"""Defensive fetchers for the fine-scale refinement.

Every network call goes through ``http()``:
  * on-disk cache under data/cache/http/<host>/<sha256>.{bin,json} (re-runs and
    offline runs are free; set HORDEJAKT_OFFLINE=1 to forbid the network),
  * retries with exponential back-off on timeouts, 429 and 5xx (Retry-After is
    honoured),
  * fail-fast ``FetchBlocked`` when the sandbox/proxy refuses the host (HTTP 403
    on CONNECT, DNS failure); the host is remembered so later calls fail at once.
Processed products (DTM/DOM rasters, OSM GeoJSON, SR16) have a second cache
under data/cache/{rasters,osm,sr16,adsb}/ keyed by bbox/resolution.

Endpoints (see ``HOSTS``; all EPSG:25833 unless stated):
  DTM   https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833   (WCS 1.0.0, coverage discovered)
  DOM   https://wcs.geonorge.no/skwms1/wcs.hoyde-dom-nhm-25833
  pts   https://ws.geonorge.no/hoydedata/v1/punkter             (<=50 points per call)
  OSM   https://overpass-api.de/api/interpreter  (fallback https://overpass.kumi.systems/api/interpreter)
  SR16  https://wms.nibio.no/cgi-bin/sr16                        (WMS GetFeatureInfo / WCS if offered)
  ADS-B https://globe.adsb.lol/globe_history/YYYY/MM/DD/traces/xx/trace_full_<hex>.json

Known uncertainties (verify with ``python -m hordejakt.refine.fetch --probe`` once
the hosts are allowed): the coverage ids (expected ``nhm_dtm_topo_25833`` /
``nhm_dom_topo_25833``; discovered from GetCapabilities, the constants are only
a fallback), the accepted FORMAT string (GeoTIFF / GTiff / image/tiff), the
server's max request size (we tile at <= 2000 px), SR16 layer names and class
codes (1 = spruce, 2 = pine, 3 = deciduous assumed) and how long adsb.lol keeps
globe_history on the live server.
"""
import gzip
import hashlib
import io
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date as _date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse

import numpy as np
import requests

from .. import ROOT
from .raster import Raster, bbox_to_wgs84, make_transform, snap_bbox, to_utm, to_wgs84

CACHE = Path(os.environ.get("HORDEJAKT_CACHE", ROOT / "data" / "cache"))
USER_AGENT = "hordejakt-refine/0.1 (hobby treasure-hunt research; python-requests)"

DTM_WCS = "https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833"
DOM_WCS = "https://wcs.geonorge.no/skwms1/wcs.hoyde-dom-nhm-25833"
HOYDEDATA_POINTS = "https://ws.geonorge.no/hoydedata/v1/punkter"
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
SR16_ENDPOINTS = ["https://wms.nibio.no/cgi-bin/sr16"]
ADSB_HISTORY = "https://globe.adsb.lol/globe_history/{y:04d}/{m:02d}/{d:02d}/traces/{xx}/trace_full_{hex}.json"

# Fallback coverage ids if GetCapabilities cannot be parsed (best knowledge, unverified here).
DEFAULT_COVERAGE = {"dtm": "nhm_dtm_topo_25833", "dom": "nhm_dom_topo_25833"}
MAX_PX = 2000          # per WCS request side
POINTS_PER_CALL = 50   # høydedata API limit

HOSTS = {
    "wcs.geonorge.no": "Kartverket DTM + DOM (WCS) - required for 1 m terrain/canopy",
    "ws.geonorge.no": "Kartverket høydedata point API - DTM fallback and spot checks",
    "overpass-api.de": "OpenStreetMap Overpass API - roads, water, buildings, rail, landuse",
    "overpass.kumi.systems": "Overpass mirror - fallback for OSM",
    "wms.nibio.no": "NIBIO SR16 forest resource map - optional species/height check",
    "globe.adsb.lol": "adsb.lol globe_history traces - optional aircraft tracks",
}


class FetchError(RuntimeError):
    """The service answered but not with usable data (exception report, bad format, ...)."""


class FetchBlocked(FetchError):
    """The network (sandbox proxy / DNS) does not let us reach the host(s)."""

    def __init__(self, hosts, detail=""):
        self.hosts = sorted(set([hosts] if isinstance(hosts, str) else hosts))
        super().__init__(f"blocked host(s): {', '.join(self.hosts)}" + (f" ({detail})" if detail else ""))


_BLOCKED = {}
_OFFLINE = os.environ.get("HORDEJAKT_OFFLINE", "") not in ("", "0", "false")
_SESSION = None


def set_offline(flag=True):
    global _OFFLINE
    _OFFLINE = bool(flag)


def blocked_hosts():
    return sorted(_BLOCKED)


def reset_blocked():
    _BLOCKED.clear()


def _session():
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers.update({"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"})
    return _SESSION


def _send(method, url, params=None, data=None, headers=None, timeout=60):
    """Single raw request (monkeypatched in tests)."""
    return _session().request(method, url, params=params, data=data, headers=headers, timeout=timeout)


class Response:
    def __init__(self, content, status=200, headers=None, url="", from_cache=False):
        self.content = content
        self.status_code = status
        self.headers = headers or {}
        self.url = url
        self.from_cache = from_cache

    @property
    def text(self):
        return self.content.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.content)

    @property
    def content_type(self):
        return (self.headers.get("Content-Type") or self.headers.get("content-type") or "").lower()


def _is_blocked_exc(exc):
    s = repr(exc)
    return (isinstance(exc, requests.exceptions.ProxyError) or "Tunnel connection failed" in s
            or "NameResolutionError" in s or "Failed to resolve" in s or "Name or service not known" in s
            or "Temporary failure in name resolution" in s or "nodename nor servname" in s)


def _cache_paths(method, url, params, data):
    key = json.dumps([method.upper(), url, sorted((params or {}).items()),
                      data if isinstance(data, str) else (data.decode() if isinstance(data, bytes) else data)],
                     sort_keys=True, default=str)
    h = hashlib.sha256(key.encode()).hexdigest()[:40]
    d = CACHE / "http" / (urlparse(url).hostname or "unknown")
    return d / f"{h}.bin", d / f"{h}.json"


def http(url, params=None, data=None, method="GET", headers=None, retries=4, backoff=2.0, timeout=90,
         cache=True, validate=None):
    """GET/POST with cache + retries. Returns ``Response``.

    validate(resp) -> None or raises FetchError; invalid answers are never cached.
    Raises FetchBlocked when the host is unreachable because of network policy.
    """
    host = urlparse(url).hostname or url
    binp, metap = _cache_paths(method, url, params, data)
    if cache and binp.exists() and metap.exists():
        meta = json.loads(metap.read_text())
        return Response(binp.read_bytes(), meta.get("status", 200), meta.get("headers", {}), meta.get("url", url), True)
    if _OFFLINE:
        raise FetchBlocked(host, "offline mode (HORDEJAKT_OFFLINE=1) and not cached")
    if host in _BLOCKED:
        raise FetchBlocked(host, _BLOCKED[host])
    last = None
    for attempt in range(retries + 1):
        try:
            r = _send(method, url, params=params, data=data, headers=headers, timeout=timeout)
        except Exception as exc:  # noqa: BLE001 - classify below
            if _is_blocked_exc(exc):
                _BLOCKED[host] = type(exc).__name__
                raise FetchBlocked(host, str(exc)[:160]) from exc
            last = exc
            if attempt < retries:
                time.sleep(backoff * 2 ** attempt)
                continue
            raise FetchError(f"{host}: {type(exc).__name__}: {str(exc)[:200]}") from exc
        status = r.status_code
        if status == 403 and re.search(rb"proxy|policy|egress|not allowed", r.content[:2000] or b"", re.I):
            _BLOCKED[host] = "HTTP 403 from proxy"
            raise FetchBlocked(host, "HTTP 403 from proxy")
        if status in (429, 500, 502, 503, 504) and attempt < retries:
            ra = r.headers.get("Retry-After")
            wait = float(ra) if ra and str(ra).isdigit() else backoff * 2 ** attempt
            time.sleep(min(wait, 120))
            last = FetchError(f"{host}: HTTP {status}")
            continue
        if status >= 400:
            raise FetchError(f"{host}: HTTP {status} for {r.url if hasattr(r, 'url') else url}: "
                             f"{r.content[:300]!r}")
        resp = Response(r.content, status, dict(r.headers), getattr(r, "url", url))
        if validate is not None:
            validate(resp)
        if cache:
            binp.parent.mkdir(parents=True, exist_ok=True)
            binp.write_bytes(resp.content)
            metap.write_text(json.dumps({"url": resp.url, "status": status, "fetched": datetime.now(timezone.utc).isoformat(),
                                         "headers": {k: v for k, v in resp.headers.items()
                                                     if k.lower() in ("content-type", "content-encoding", "date")}}))
        return resp
    raise FetchError(f"{host}: giving up after {retries + 1} attempts ({last})")


def check_hosts(hosts=None, timeout=8):
    """{host: 'ok' | 'blocked' | 'error: ...'} - any HTTP answer counts as reachable."""
    out = {}
    for h in hosts or HOSTS:
        if _OFFLINE:
            out[h] = "blocked"
            continue
        try:
            _send("GET", f"https://{h}/", timeout=timeout)
            out[h] = "ok"
        except Exception as exc:  # noqa: BLE001
            if _is_blocked_exc(exc):
                _BLOCKED[h] = type(exc).__name__
                out[h] = "blocked"
            else:
                out[h] = f"error: {type(exc).__name__}"
    return out


def blocked_message(hosts):
    lines = ["Network access is blocked for the data hosts this step needs. Allow these hosts",
             "(Claude Code on the web: environment settings -> network access -> allowed domains):"]
    for h in sorted(set(hosts)):
        lines.append(f"  - {h:24s} {HOSTS.get(h, '')}")
    lines.append("Everything fetched is cached in data/cache/, so a later offline run reuses it.")
    return "\n".join(lines)


# ----------------------------------------------------------------------------- XML helpers
def _local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _iter_local(root, name):
    for el in root.iter():
        if _local(el.tag) == name:
            yield el


def _child_text(el, name):
    for c in el.iter():
        if _local(c.tag) == name and c.text:
            return c.text.strip()
    return None


def ows_exception(content):
    """Return the exception text if content is an OGC ServiceException/ExceptionReport, else None."""
    head = content[:4000].lstrip()
    if not head.startswith(b"<"):
        return None
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return None
    if "Exception" in _local(root.tag):
        texts = [(e.text or "").strip() for e in root.iter() if (e.text or "").strip()]
        return " | ".join(texts)[:500] or _local(root.tag)
    return None


# ----------------------------------------------------------------------------- WCS
def parse_wcs_capabilities(content):
    """Coverage ids from WCS 1.0.0 / 1.1 / 2.0 capabilities: [{'name', 'label', 'version'}]."""
    root = ET.fromstring(content)
    out = []
    for el in _iter_local(root, "CoverageOfferingBrief"):  # 1.0.0
        n = _child_text(el, "name")
        if n:
            out.append({"name": n, "label": _child_text(el, "label") or "", "version": "1.0.0"})
    for el in _iter_local(root, "CoverageSummary"):  # 1.1 / 2.0
        n = _child_text(el, "CoverageId") or _child_text(el, "Identifier")
        if n:
            out.append({"name": n, "label": _child_text(el, "Title") or "", "version": "2.0.1"})
    formats = [(e.text or "").strip() for e in _iter_local(root, "formatSupported")]
    for o in out:
        o["formats"] = formats
    return out


def parse_wcs_describe(content):
    """Supported formats and CRSs from a WCS 1.0.0 DescribeCoverage."""
    root = ET.fromstring(content)
    fmts, crss = [], []
    for el in _iter_local(root, "supportedFormats"):
        fmts += [(c.text or "").strip() for c in el if _local(c.tag) == "formats"]
    for el in _iter_local(root, "supportedCRSs"):
        crss += [(c.text or "").strip() for c in el if (c.text or "").strip()]
    return {"formats": [f for f in fmts if f], "crs": crss}


def choose_coverage(coverages, kind):
    """Pick the coverage id for kind 'dtm'/'dom': prefer names mentioning kind and 25833, avoid bathymetry."""
    names = [c["name"] if isinstance(c, dict) else c for c in coverages]
    if not names:
        return DEFAULT_COVERAGE[kind]

    def rank(n):
        s = n.lower()
        return ((kind in s) * 4 + ("25833" in s) * 2 + ("topo" in s) * 1 - ("bathy" in s or "sjo" in s) * 3
                - ("skygge" in s or "shade" in s or "hillshade" in s) * 5)
    return max(names, key=rank)


def choose_format(formats):
    order = [lambda f: "geotiff" in f, lambda f: f in ("gtiff", "image/tiff"), lambda f: "tif" in f,
             lambda f: "aaigrid" in f or "ascii" in f, lambda f: "xyz" in f]
    low = [f.lower() for f in formats]
    for test in order:
        for f, lf in zip(formats, low):
            if test(lf):
                return f
    return "GeoTIFF"


def decode_geotiff(content):
    """(array float32 with NaN nodata, transform) from GeoTIFF bytes (rasterio, else tifffile)."""
    try:
        import rasterio
        from rasterio.io import MemoryFile
        with MemoryFile(content) as mf, mf.open() as src:
            arr = src.read(1).astype(np.float32)
            nod = src.nodata
            if nod is not None:
                arr[arr == nod] = np.nan
            return arr, src.transform
    except ImportError:
        pass
    import tifffile
    with tifffile.TiffFile(io.BytesIO(content)) as tf:
        page = tf.pages[0]
        arr = page.asarray().astype(np.float32)
        if arr.ndim == 3:
            arr = arr[..., 0] if arr.shape[-1] < arr.shape[0] else arr[0]
        tags = {t.name: t.value for t in page.tags.values()}
        nod = tags.get("GDAL_NODATA")
        if nod is not None:
            try:
                arr[arr == float(str(nod).strip().strip("\x00"))] = np.nan
            except ValueError:
                pass
        point = False
        gk = tags.get("GeoKeyDirectoryTag")
        if gk is not None:
            g = list(gk)
            for k in range(4, len(g) - 3, 4):
                if g[k] == 1025 and g[k + 3] == 2:  # GTRasterTypeGeoKey = RasterPixelIsPoint
                    point = True
        if "ModelTransformationTag" in tags:
            m = list(tags["ModelTransformationTag"])
            t = (m[0], m[1], m[3], m[4], m[5], m[7])
        elif "ModelPixelScaleTag" in tags and "ModelTiepointTag" in tags:
            sx, sy = tags["ModelPixelScaleTag"][:2]
            i, j, _, x, y, _ = tags["ModelTiepointTag"][:6]
            t = (sx, 0.0, x - i * sx, 0.0, -sy, y + j * sy)
        else:
            raise FetchError("GeoTIFF without georeferencing tags")
        if point:
            t = (t[0], t[1], t[2] - t[0] / 2, t[3], t[4], t[5] - t[4] / 2)
        return arr, make_transform(t[2], t[5], t[0], -t[4])


def decode_aaigrid(text):
    lines = text.strip().splitlines()
    hdr, k = {}, 0
    while k < len(lines) and re.match(r"^[A-Za-z_]+\s", lines[k]):
        key, val = lines[k].split()[:2]
        hdr[key.lower()] = float(val)
        k += 1
    arr = np.array(" ".join(lines[k:]).split(), float).reshape(int(hdr["nrows"]), int(hdr["ncols"]))
    cs = hdr["cellsize"]
    x0 = hdr.get("xllcorner", hdr.get("xllcenter", 0) - cs / 2)
    y0 = hdr.get("yllcorner", hdr.get("yllcenter", 0) - cs / 2)
    if "nodata_value" in hdr:
        arr[arr == hdr["nodata_value"]] = np.nan
    return arr.astype(np.float32), make_transform(x0, y0 + cs * arr.shape[0], cs)


def decode_xyz(text):
    a = np.loadtxt(io.StringIO(text), ndmin=2)
    xs, ys = np.unique(a[:, 0]), np.unique(a[:, 1])[::-1]
    res = float(np.median(np.diff(xs))) if len(xs) > 1 else 1.0
    arr = np.full((len(ys), len(xs)), np.nan, np.float32)
    arr[np.searchsorted(-ys, -a[:, 1]), np.searchsorted(xs, a[:, 0])] = a[:, 2]
    return arr, make_transform(xs[0] - res / 2, ys[0] + res / 2, res)


def decode_coverage(resp):
    exc = ows_exception(resp.content)
    if exc:
        raise FetchError(f"WCS exception: {exc}")
    c = resp.content
    if c[:4] in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
        return decode_geotiff(c)
    if c[:2] == b"\x1f\x8b":
        c = gzip.decompress(c)
    head = c[:200].decode("ascii", errors="replace").lower()
    if head.startswith("ncols") or "ncols" in head[:40]:
        return decode_aaigrid(c.decode())
    if re.match(r"^\s*-?\d", head):
        return decode_xyz(c.decode())
    raise FetchError(f"unrecognised coverage payload (content-type {resp.content_type!r}, starts {c[:16]!r})")


def _validate_coverage(resp):
    exc = ows_exception(resp.content)
    if exc:
        raise FetchError(f"WCS exception: {exc}")
    if len(resp.content) < 64:
        raise FetchError("WCS returned an empty payload")


def wcs_discover(service_url):
    """(coverage list, formats) for a WCS; tries 1.0.0 then 2.0.1 capabilities."""
    last = None
    for ver in ("1.0.0", "2.0.1"):
        try:
            r = http(service_url, {"SERVICE": "WCS", "REQUEST": "GetCapabilities", "VERSION": ver},
                     validate=lambda rr: _raise_if_exception(rr, "GetCapabilities"))
            cov = parse_wcs_capabilities(r.content)
            if cov:
                return cov
        except FetchBlocked:
            raise
        except (FetchError, ET.ParseError) as exc:
            last = exc
    if last:
        print(f"[fetch] WCS capabilities unusable for {service_url}: {last}", file=sys.stderr)
    return []


def _raise_if_exception(resp, what):
    exc = ows_exception(resp.content)
    if exc:
        raise FetchError(f"{what}: {exc}")


def wcs_formats(service_url, coverage):
    try:
        r = http(service_url, {"SERVICE": "WCS", "REQUEST": "DescribeCoverage", "VERSION": "1.0.0", "COVERAGE": coverage},
                 validate=lambda rr: _raise_if_exception(rr, "DescribeCoverage"))
        return parse_wcs_describe(r.content)["formats"]
    except FetchBlocked:
        raise
    except (FetchError, ET.ParseError):
        return []


def _wcs_request(service_url, coverage, bbox, w, h, fmt, version="1.0.0"):
    xmin, ymin, xmax, ymax = bbox
    if version == "1.0.0":
        params = {"SERVICE": "WCS", "VERSION": "1.0.0", "REQUEST": "GetCoverage", "COVERAGE": coverage,
                  "CRS": "EPSG:25833", "RESPONSE_CRS": "EPSG:25833",
                  "BBOX": f"{xmin:.3f},{ymin:.3f},{xmax:.3f},{ymax:.3f}", "WIDTH": w, "HEIGHT": h, "FORMAT": fmt}
        return http(service_url, params, validate=_validate_coverage, timeout=180)
    last = None
    for ax, ay in (("x", "y"), ("E", "N"), ("X", "Y")):
        q = [("SERVICE", "WCS"), ("VERSION", "2.0.1"), ("REQUEST", "GetCoverage"), ("COVERAGEID", coverage),
             ("FORMAT", "image/tiff"), ("SUBSET", f"{ax}({xmin:.3f},{xmax:.3f})"), ("SUBSET", f"{ay}({ymin:.3f},{ymax:.3f})"),
             ("SCALESIZE", f"{ax}({w}),{ay}({h})")]
        try:
            return http(service_url + "?" + urlencode(q), validate=_validate_coverage, timeout=180)
        except FetchBlocked:
            raise
        except FetchError as exc:
            last = exc
    raise last


def wcs_raster(service_url, kind, bbox, res_m=1.0, coverage=None, fmt=None):
    """Mosaic of WCS GetCoverage tiles (<= MAX_PX per side) over bbox at res_m, EPSG:25833."""
    bbox = snap_bbox(bbox, res_m)
    covs = [] if coverage else wcs_discover(service_url)
    coverage = coverage or choose_coverage(covs, kind)
    fmt = fmt or choose_format(wcs_formats(service_url, coverage) or (covs[0].get("formats") if covs else []) or [])
    xmin, ymin, xmax, ymax = bbox
    W = int(round((xmax - xmin) / res_m))
    H = int(round((ymax - ymin) / res_m))
    out = np.full((H, W), np.nan, np.float32)
    step = MAX_PX
    for r0 in range(0, H, step):
        for c0 in range(0, W, step):
            h, w = min(step, H - r0), min(step, W - c0)
            tb = (xmin + c0 * res_m, ymax - (r0 + h) * res_m, xmin + (c0 + w) * res_m, ymax - r0 * res_m)
            try:
                resp = _wcs_request(service_url, coverage, tb, w, h, fmt)
            except FetchBlocked:
                raise
            except FetchError:
                resp = _wcs_request(service_url, coverage, tb, w, h, fmt, version="2.0.1")
            arr, tr = decode_coverage(resp)
            # place by the returned georeference (robust to half-pixel conventions)
            rr = int(round((ymax - tr[5]) / res_m))
            cc = int(round((tr[2] - xmin) / res_m))
            if abs(abs(tr[0]) - res_m) > 1e-6 * max(1.0, res_m):
                tmp = Raster(arr, tr).resample(res_m, tb)
                arr, rr, cc = tmp.data, r0, c0
            rr0, cc0 = max(rr, 0), max(cc, 0)
            rr1, cc1 = min(rr + arr.shape[0], H), min(cc + arr.shape[1], W)
            if rr1 > rr0 and cc1 > cc0:
                out[rr0:rr1, cc0:cc1] = arr[rr0 - rr:rr1 - rr, cc0 - cc:cc1 - cc]
    if np.isnan(out).all():
        raise FetchError(f"{kind}: WCS returned only nodata for {bbox}")
    return Raster(out, make_transform(xmin, ymax, res_m), source=f"wcs:{service_url.rsplit('/', 1)[-1]}:{coverage}",
                  meta={"coverage": coverage, "format": fmt, "res": res_m, "bbox": list(bbox)})


def _raster_cache(kind, bbox, res):
    b = "_".join(f"{v:.0f}" for v in bbox)
    return CACHE / "rasters" / f"{kind}_{b}_{res:g}m.npz"


# ----------------------------------------------------------------------------- høydedata points
def hoydedata_points(xs, ys, koordsys=25833, pause=0.15):
    """Terrain height (DTM, m) for EPSG:25833 points via the høydedata API (<= 50 per call).

    Returns (z array with NaN where missing, list of raw point dicts)."""
    xs, ys = np.atleast_1d(np.asarray(xs, float)), np.atleast_1d(np.asarray(ys, float))
    z = np.full(xs.shape, np.nan)
    raw = []
    for k in range(0, len(xs), POINTS_PER_CALL):
        pts = [[round(float(x), 2), round(float(y), 2)] for x, y in zip(xs[k:k + POINTS_PER_CALL], ys[k:k + POINTS_PER_CALL])]
        r = http(HOYDEDATA_POINTS, {"koordsys": koordsys, "punkter": json.dumps(pts, separators=(",", ":")),
                                    "geojson": "false"}, validate=_validate_json)
        items = r.json().get("punkter", [])
        for n, it in enumerate(items[:len(pts)]):
            v = it.get("z", it.get("hoyde"))
            z[k + n] = np.nan if v is None else float(v)
            raw.append(it)
        if not r.from_cache:
            time.sleep(pause)
    return z, raw


def _validate_json(resp):
    try:
        json.loads(resp.content)
    except ValueError as exc:
        raise FetchError(f"expected JSON, got {resp.content[:120]!r}") from exc


def dtm_from_points(bbox, step_m=50.0, max_points=4000):
    """Sparse DTM on a step_m lattice from the point API (fallback when WCS is unavailable)."""
    xmin, ymin, xmax, ymax = bbox
    while ((xmax - xmin) / step_m) * ((ymax - ymin) / step_m) > max_points:
        step_m *= 1.5
    W = max(1, int(np.ceil((xmax - xmin) / step_m)))
    H = max(1, int(np.ceil((ymax - ymin) / step_m)))
    r = Raster(np.zeros((H, W), np.float32), make_transform(xmin, ymin + H * step_m, step_m), source="hoydedata-points")
    X, Y = r.centres()
    z, _ = hoydedata_points(X.ravel(), Y.ravel())
    r.data = z.reshape(H, W).astype(np.float32)
    r.meta = {"res": step_m, "note": "sparse point-API samples; slope/canopy terms are coarse"}
    return r


# ----------------------------------------------------------------------------- DTM / DOM
def dtm_tile(bbox, res_m=1.0, points_fallback=True, sparse_step_m=50.0):
    """Kartverket DTM (terrain) over an EPSG:25833 bbox -> Raster (array + affine, NaN = nodata).

    WCS first; if the WCS host is blocked or errors, falls back to the høydedata
    point API on a sparse lattice (sparse_step_m). Cached in data/cache/rasters/."""
    bbox = snap_bbox(bbox, res_m)
    cp = _raster_cache("dtm", bbox, res_m)
    if cp.exists():
        return Raster.load(cp)
    errors, blocked = [], []
    try:
        r = wcs_raster(DTM_WCS, "dtm", bbox, res_m)
        cp.parent.mkdir(parents=True, exist_ok=True)
        r.save(cp)
        return r
    except FetchBlocked as exc:
        blocked += exc.hosts
    except FetchError as exc:
        errors.append(str(exc))
    if points_fallback:
        step = max(res_m, sparse_step_m)
        cpp = _raster_cache("dtmpts", bbox, step)
        if cpp.exists():
            return Raster.load(cpp)
        try:
            r = dtm_from_points(bbox, step)
            cpp.parent.mkdir(parents=True, exist_ok=True)
            r.save(cpp)
            print(f"[fetch] DTM via point API at {r.res[0]:.0f} m (WCS unavailable: {errors or blocked})", file=sys.stderr)
            return r
        except FetchBlocked as exc:
            blocked += exc.hosts
        except FetchError as exc:
            errors.append(str(exc))
    if blocked and not errors:
        raise FetchBlocked(blocked, "DTM")
    raise FetchError("DTM unavailable: " + "; ".join(errors + [f"blocked {h}" for h in blocked]))


def dom_tile(bbox, res_m=1.0):
    """Kartverket DOM (surface incl. canopy) over bbox -> Raster. Canopy height = DOM - DTM."""
    bbox = snap_bbox(bbox, res_m)
    cp = _raster_cache("dom", bbox, res_m)
    if cp.exists():
        return Raster.load(cp)
    r = wcs_raster(DOM_WCS, "dom", bbox, res_m)
    cp.parent.mkdir(parents=True, exist_ok=True)
    r.save(cp)
    return r


def canopy_height(dtm, dom):
    """Canopy height model (m) on the DTM grid: clip(DOM - DTM, 0, 60)."""
    d = dom.like(dtm)
    chm = np.clip(d.data.astype(float) - dtm.data.astype(float), 0.0, 60.0)
    return Raster(chm.astype(np.float32), dtm.transform, source="chm=dom-dtm")


# ----------------------------------------------------------------------------- OSM / Overpass
OSM_QUERY = """[out:json][timeout:{timeout}];
(
  way["highway"]({bb});
  way["waterway"]({bb});
  way["natural"~"^(water|wetland|wood|heath|scrub|bare_rock)$"]({bb});
  relation["natural"~"^(water|wetland)$"]({bb});
  node["natural"="spring"]({bb});
  way["water"]({bb});
  way["building"]({bb});
  node["building"]({bb});
  relation["building"]({bb});
  node["tourism"~"^(alpine_hut|wilderness_hut|chalet|camp_site)$"]({bb});
  node["amenity"="shelter"]({bb});
  way["amenity"="shelter"]({bb});
  node["barrier"~"^(cattle_grid|gate|lift_gate)$"]({bb});
  way["barrier"="cattle_grid"]({bb});
  way["railway"]({bb});
  way["landuse"]({bb});
  relation["landuse"]({bb});
  node["man_made"]({bb});
  way["man_made"]({bb});
);
out geom;
"""

MAJOR_ROADS = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary",
               "secondary_link", "tertiary", "tertiary_link"}
MINOR_ROADS = {"unclassified", "residential", "living_street", "road"}
PATHS = {"path", "footway", "bridleway", "cycleway", "steps", "pedestrian", "via_ferrata"}
AREA_KEYS = {"building", "landuse", "water", "amenity", "leisure", "man_made", "tourism"}
AREA_NATURAL = {"water", "wetland", "wood", "heath", "scrub", "bare_rock", "grassland"}


def osm_kind(tags):
    """Coarse class used by the scorer."""
    hw = tags.get("highway")
    if hw:
        if hw in MAJOR_ROADS:
            return "road_major"
        if hw in MINOR_ROADS:
            return "road_minor"
        if hw == "service":
            return "road_service"
        if hw == "track":
            return "track"
        if hw in PATHS:
            return "path"
        return "highway_other"
    ww = tags.get("waterway")
    if ww in ("riverbank",) or tags.get("natural") == "water" or "water" in tags or tags.get("landuse") in ("reservoir", "basin"):
        return "water"
    if ww in ("river", "stream", "brook", "canal", "waterfall", "rapids", "tidal_channel"):
        return "waterway"
    if ww in ("ditch", "drain"):
        return "ditch"
    if tags.get("natural") == "spring":
        return "spring"
    if tags.get("natural") == "wetland":
        return "wetland"
    if "building" in tags or tags.get("tourism") in ("alpine_hut", "wilderness_hut", "chalet") or tags.get("amenity") == "shelter":
        return "building"
    if tags.get("barrier") == "cattle_grid":
        return "cattle_grid"
    if tags.get("barrier") in ("gate", "lift_gate"):
        return "gate"
    rw = tags.get("railway")
    if rw:
        return "railway" if rw in ("rail", "light_rail", "narrow_gauge", "subway", "tram", "preserved") else "railway_disused"
    if "landuse" in tags:
        return "landuse"
    if tags.get("natural") in AREA_NATURAL:
        return "landcover"
    if "man_made" in tags:
        return "man_made"
    return "other"


def _is_area(tags, closed):
    if not closed:
        return False
    if tags.get("area") == "no":
        return False
    if tags.get("area") == "yes":
        return True
    if "highway" in tags or "barrier" in tags or "railway" in tags:
        return False
    if tags.get("waterway") and tags.get("waterway") not in ("riverbank", "dock", "boatyard"):
        return False
    if tags.get("natural") in AREA_NATURAL:
        return True
    return bool(AREA_KEYS & set(tags))


def _merge_rings(segments):
    """Join way coordinate lists into closed rings by matching endpoints."""
    segs = [list(s) for s in segments if len(s) >= 2]
    rings = []
    while segs:
        ring = segs.pop(0)
        changed = True
        while ring[0] != ring[-1] and changed:
            changed = False
            for k, s in enumerate(segs):
                if s[0] == ring[-1]:
                    ring += s[1:]
                elif s[-1] == ring[-1]:
                    ring += s[::-1][1:]
                elif s[-1] == ring[0]:
                    ring = s[:-1] + ring
                elif s[0] == ring[0]:
                    ring = s[::-1][:-1] + ring
                else:
                    continue
                segs.pop(k)
                changed = True
                break
        if ring[0] == ring[-1] and len(ring) >= 4:
            rings.append(ring)
    return rings


def overpass_to_geojson(data):
    """Overpass JSON (``out geom``) -> GeoJSON-like FeatureCollection (WGS84 lon/lat)."""
    feats = []
    for el in data.get("elements", []):
        tags = el.get("tags", {}) or {}
        props = dict(tags)
        props.update({"osm_type": el["type"], "osm_id": el.get("id"), "kind": osm_kind(tags)})
        geom = None
        if el["type"] == "node" and "lat" in el:
            geom = {"type": "Point", "coordinates": [el["lon"], el["lat"]]}
        elif el["type"] == "way" and el.get("geometry"):
            coords = [[p["lon"], p["lat"]] for p in el["geometry"] if p]
            if len(coords) < 2:
                continue
            closed = coords[0] == coords[-1] and len(coords) >= 4
            geom = ({"type": "Polygon", "coordinates": [coords]} if _is_area(tags, closed)
                    else {"type": "LineString", "coordinates": coords})
        elif el["type"] == "relation" and el.get("members"):
            outer, inner = [], []
            for m in el["members"]:
                if m.get("type") != "way" or not m.get("geometry"):
                    continue
                cs = [[p["lon"], p["lat"]] for p in m["geometry"] if p]
                (inner if m.get("role") == "inner" else outer).append(cs)
            if tags.get("type") in ("multipolygon", "boundary") or _is_area(tags, True):
                rings_o, rings_i = _merge_rings(outer), _merge_rings(inner)
                if rings_o:
                    geom = {"type": "MultiPolygon", "coordinates": [[r] for r in rings_o]}
                    props["inner_rings"] = rings_i
            if geom is None and outer:
                geom = {"type": "MultiLineString", "coordinates": outer}
        if geom is not None:
            feats.append({"type": "Feature", "geometry": geom, "properties": props})
    return {"type": "FeatureCollection", "features": feats}


def osm_features(bbox, pad_m=800.0, timeout=120):
    """OSM features around an EPSG:25833 bbox (padded by pad_m so distances near the
    edge are right) -> GeoJSON-like dict (WGS84 lon/lat) with properties.kind."""
    xmin, ymin, xmax, ymax = bbox
    pb = (xmin - pad_m, ymin - pad_m, xmax + pad_m, ymax + pad_m)
    cp = CACHE / "osm" / ("osm_" + "_".join(f"{v:.0f}" for v in pb) + ".json")
    if cp.exists():
        return json.loads(cp.read_text())
    s, w, n, e = bbox_to_wgs84(pb)
    q = OSM_QUERY.format(timeout=timeout, bb=f"{s:.6f},{w:.6f},{n:.6f},{e:.6f}")
    errors, blocked = [], []
    for url in OVERPASS:
        try:
            r = http(url, data={"data": q}, method="POST", timeout=timeout + 30, validate=_validate_overpass)
            fc = overpass_to_geojson(r.json())
            fc["bbox_25833"] = list(pb)
            fc["source"] = url
            fc["osm_base"] = r.json().get("osm3s", {}).get("timestamp_osm_base")
            cp.parent.mkdir(parents=True, exist_ok=True)
            cp.write_text(json.dumps(fc))
            return fc
        except FetchBlocked as exc:
            blocked += exc.hosts
        except FetchError as exc:
            errors.append(str(exc))
    if blocked and not errors:
        raise FetchBlocked(blocked, "Overpass")
    raise FetchError("Overpass failed: " + "; ".join(errors + [f"blocked {h}" for h in blocked]))


def _validate_overpass(resp):
    try:
        d = json.loads(resp.content)
    except ValueError as exc:
        raise FetchError(f"Overpass returned non-JSON: {resp.content[:200]!r}") from exc
    if "remark" in d and "error" in str(d["remark"]).lower():
        raise FetchError(f"Overpass remark: {d['remark'][:200]}")


# ----------------------------------------------------------------------------- NIBIO SR16
SR16_ROLES = {
    "species": ("treslag", "species", "tsl"),
    "height": ("mhoyde", "hoyde", "høyde", "height", "hgt"),
    "volume": ("volum", "volume", "vol"),
    "age": ("alder", "age"),
    "crown": ("krone", "kronedek", "crown", "dekning"),
}
# Assumed SR16 'treslag' codes (verify against the layer legend once reachable).
SR16_SPECIES = {1: "spruce", 2: "pine", 3: "deciduous"}
SR16_LABELS = {"gran": "spruce", "furu": "pine", "lauv": "deciduous", "bjørk": "deciduous", "bjork": "deciduous"}


def parse_wms_layers(content):
    root = ET.fromstring(content)
    out = []
    for el in _iter_local(root, "Layer"):
        name = None
        title = abstract = ""
        for c in el:
            t = _local(c.tag)
            if t == "Name":
                name = (c.text or "").strip()
            elif t == "Title":
                title = (c.text or "").strip()
            elif t == "Abstract":
                abstract = (c.text or "").strip()
        if name:
            out.append({"name": name, "title": title, "abstract": abstract[:200], "queryable": el.get("queryable") == "1"})
    fmts = []
    for el in _iter_local(root, "GetFeatureInfo"):
        fmts += [(c.text or "").strip() for c in el if _local(c.tag) == "Format"]
    return out, fmts


def sr16_choose(layers):
    chosen = {}
    for role, keys in SR16_ROLES.items():
        best = None
        for L in layers:
            s = (L["name"] + " " + L["title"]).lower()
            if any(k in s for k in keys) and (best is None or len(L["name"]) < len(best)):
                best = L["name"]
        if best:
            chosen[role] = best
    return chosen


def parse_featureinfo(text):
    """(value, label) from a MapServer/GeoServer raster GetFeatureInfo answer."""
    m = re.search(r"(?:value_0|value_list|GRAY_INDEX|pixel|\bvalue\b)\s*(?:=|:|>)\s*['\"]?(-?\d+(?:\.\d+)?)", text, re.I)
    lab = re.search(r"\bclass\s*(?:=|:|>)\s*['\"]?([^'\"<\n]+)", text, re.I)
    return (float(m.group(1)) if m else None), (lab.group(1).strip() if lab else None)


def sr16(bbox, points=None, res_m=16.0, endpoints=None):
    """NIBIO SR16 (forest resource map) best effort.

    Returns {'endpoint', 'layers', 'chosen', 'rasters': {role: Raster}, 'points': [...], 'notes': [...]}.
    Tries WCS GetCoverage (if the MapServer also serves WCS) for species/height/volume
    rasters over bbox; otherwise WMS GetFeatureInfo at the given EPSG:25833 points.
    """
    notes, blocked, errors = [], [], []
    for ep in endpoints or SR16_ENDPOINTS:
        try:
            r = http(ep, {"SERVICE": "WMS", "REQUEST": "GetCapabilities", "VERSION": "1.3.0"},
                     validate=lambda rr: _raise_if_exception(rr, "SR16 GetCapabilities"))
            layers, gfi_formats = parse_wms_layers(r.content)
        except FetchBlocked as exc:
            blocked += exc.hosts
            continue
        except (FetchError, ET.ParseError) as exc:
            errors.append(f"{ep}: {exc}")
            continue
        chosen = sr16_choose(layers)
        out = {"endpoint": ep, "layers": [L["name"] for L in layers], "chosen": chosen, "rasters": {}, "points": [],
               "notes": notes}
        # WCS on the same MapServer endpoint (optional)
        try:
            covs = [c["name"] for c in wcs_discover(ep)]
        except FetchError:
            covs = []
        for role in ("species", "height", "volume"):
            name = chosen.get(role)
            if name and name in covs:
                try:
                    out["rasters"][role] = wcs_raster(ep, role, bbox, res_m, coverage=name)
                except FetchError as exc:
                    notes.append(f"WCS {name}: {exc}")
        if points is not None and len(points):
            fmt = next((f for f in ("text/plain", "application/vnd.ogc.gml", "text/xml", "application/json")
                        if f in gfi_formats), "text/plain")
            for x, y in points:
                rec = {"x": float(x), "y": float(y)}
                for role, name in chosen.items():
                    if role in out["rasters"]:
                        rec[role] = float(out["rasters"][role].sample(x, y, order=0)[0])
                        continue
                    params = {"SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetFeatureInfo", "LAYERS": name,
                              "QUERY_LAYERS": name, "STYLES": "", "CRS": "EPSG:25833",
                              "BBOX": f"{x - 24:.1f},{y - 24:.1f},{x + 24:.1f},{y + 24:.1f}", "WIDTH": 3, "HEIGHT": 3,
                              "I": 1, "J": 1, "INFO_FORMAT": fmt, "FORMAT": "image/png"}
                    try:
                        v, lab = parse_featureinfo(http(ep, params).text)
                    except FetchError as exc:
                        notes.append(f"GetFeatureInfo {name}: {exc}")
                        v, lab = None, None
                    rec[role] = v
                    if lab:
                        rec[role + "_label"] = lab
                out["points"].append(rec)
        if not chosen:
            notes.append("no SR16 layer matched species/height/volume keywords; layer names: "
                         + ", ".join(out["layers"][:30]))
        return out
    if blocked and not errors:
        raise FetchBlocked(blocked, "SR16")
    raise FetchError("SR16 unavailable: " + "; ".join(errors + [f"blocked {h}" for h in blocked]))


def sr16_species_name(value, label=None):
    if label:
        for k, v in SR16_LABELS.items():
            if k in label.lower():
                return v
    if value is None or not np.isfinite(value):
        return None
    return SR16_SPECIES.get(int(round(value)))


# ----------------------------------------------------------------------------- ADS-B (adsb.lol)
TRACE_FIELDS = ["dt", "lat", "lon", "alt_baro", "gs_kt", "track_deg", "flags", "vrate_fpm", "aircraft", "source",
                "alt_geom_ft", "geom_rate_fpm", "ias_kt", "roll_deg"]


def parse_trace(src):
    """Parse a readsb/tar1090 ``trace_full_<hex>.json`` (gzip or plain; path, bytes or dict).

    Returns {'icao', 'registration', 'type', 'desc', 'timestamp', 'callsigns', 'points': DataFrame}
    DataFrame columns: t (unix s), time (UTC), lat, lon, alt_baro_ft (NaN on ground/unknown),
    on_ground, gs_kt, track_deg, flags, stale, new_leg, vrate_fpm, alt_geom_ft, geom_rate_fpm,
    ias_kt, roll_deg, source, callsign (forward-filled per leg), squawk.
    Flags: 1 stale position, 2 start of new leg, 4 vertical rate geometric, 8 altitude geometric.
    """
    import pandas as pd
    if isinstance(src, dict):
        d = src
    else:
        raw = Path(src).read_bytes() if isinstance(src, (str, Path)) else bytes(src)
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        d = json.loads(raw)
    t0 = float(d.get("timestamp", 0.0))
    rows, cs, sq = [], None, None
    for p in d.get("trace", []):
        p = list(p) + [None] * (len(TRACE_FIELDS) - len(p))
        rec = dict(zip(TRACE_FIELDS, p[:len(TRACE_FIELDS)]))
        flags = int(rec["flags"] or 0)
        if flags & 2:
            cs, sq = None, None
        ac = rec.pop("aircraft")
        if isinstance(ac, dict):
            fl = (ac.get("flight") or "").strip()
            if fl and set(fl) != {"@"}:  # '@@@@@@@@' = no valid callsign transmitted
                cs = fl
            sq = ac.get("squawk", sq)
        alt = rec.pop("alt_baro")
        rec.update({"t": t0 + float(rec.pop("dt")), "on_ground": alt == "ground",
                    "alt_baro_ft": float(alt) if isinstance(alt, (int, float)) else np.nan,
                    "stale": bool(flags & 1), "new_leg": bool(flags & 2), "flags": flags, "callsign": cs, "squawk": sq})
        rows.append(rec)
    df = pd.DataFrame(rows)
    if len(df):
        for c in ("lat", "lon", "gs_kt", "track_deg", "vrate_fpm", "alt_geom_ft", "geom_rate_fpm", "ias_kt", "roll_deg"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["time"] = pd.to_datetime(df["t"], unit="s", utc=True)
        df = df[["t", "time", "lat", "lon", "alt_baro_ft", "on_ground", "gs_kt", "track_deg", "flags", "stale",
                 "new_leg", "vrate_fpm", "alt_geom_ft", "geom_rate_fpm", "ias_kt", "roll_deg", "source", "callsign",
                 "squawk"]]
    return {"icao": d.get("icao"), "registration": d.get("r"), "type": d.get("t"), "desc": d.get("desc"),
            "timestamp": t0, "callsigns": sorted({c for c in df["callsign"] if isinstance(c, str) and c}) if len(df) else [],
            "points": df}


def trace_position(trace, t_unix, max_gap_s=60.0):
    """Linear interpolation of the trace at unix time t (None if outside or across a gap > max_gap_s).

    Altitude prefers GNSS (alt_geom) and falls back to barometric; returns
    {'lat', 'lon', 'alt_ft', 'alt_m', 'alt_kind', 'callsign'}."""
    df = trace["points"]
    t = df["t"].to_numpy()
    k = int(np.searchsorted(t, t_unix, side="right")) - 1
    if k == len(t) - 1 and len(t) >= 2 and t[k] == t_unix:
        k -= 1
    if k < 0 or k >= len(t) - 1 or t[k + 1] - t[k] > max_gap_s:
        return None
    a, b = df.iloc[k], df.iloc[k + 1]
    f = 0.0 if t[k + 1] == t[k] else (t_unix - t[k]) / (t[k + 1] - t[k])

    def alt(row):
        return row["alt_geom_ft"] if np.isfinite(row["alt_geom_ft"]) else row["alt_baro_ft"]
    kind = "geom" if np.isfinite(a["alt_geom_ft"]) and np.isfinite(b["alt_geom_ft"]) else "baro"
    alt_ft = alt(a) + f * (alt(b) - alt(a))
    return {"lat": float(a["lat"] + f * (b["lat"] - a["lat"])), "lon": float(a["lon"] + f * (b["lon"] - a["lon"])),
            "alt_ft": float(alt_ft), "alt_m": float(alt_ft) * 0.3048, "alt_kind": kind, "callsign": a["callsign"]}


def adsb_trace(icao_hex, day):
    """adsb.lol globe_history full trace for one aircraft and UTC day (date or 'YYYY-MM-DD')."""
    if isinstance(day, str):
        day = _date.fromisoformat(day)
    hx = icao_hex.lower().lstrip("~")
    cp = CACHE / "adsb" / f"{day.isoformat()}_{hx}.json.gz"
    if cp.exists():
        return parse_trace(cp)
    url = ADSB_HISTORY.format(y=day.year, m=day.month, d=day.day, xx=hx[-2:], hex=icao_hex.lower())
    r = http(url, headers={"Referer": "https://globe.adsb.lol/", "Accept": "application/json"},
             validate=_validate_trace)
    content = r.content if r.content[:2] == b"\x1f\x8b" else gzip.compress(r.content)
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_bytes(content)
    return parse_trace(content)


def _validate_trace(resp):
    c = resp.content
    try:
        d = json.loads(gzip.decompress(c) if c[:2] == b"\x1f\x8b" else c)
    except Exception as exc:  # noqa: BLE001
        raise FetchError(f"not a trace JSON: {c[:80]!r}") from exc
    if "trace" not in d:
        raise FetchError("JSON without 'trace'")


# ----------------------------------------------------------------------------- probe
def probe():
    """Print reachability and, where reachable, the discovered WCS coverages / SR16 layers."""
    st = check_hosts()
    for h, s in st.items():
        print(f"{h:24s} {s:10s} {HOSTS[h]}")
    if st.get("wcs.geonorge.no") == "ok":
        for url in (DTM_WCS, DOM_WCS):
            try:
                covs = wcs_discover(url)
                name = choose_coverage(covs, "dtm" if "dtm" in url else "dom")
                print(url, "coverages:", [c["name"] for c in covs], "-> using", name,
                      "formats:", wcs_formats(url, name))
            except FetchError as exc:
                print(url, "ERROR", exc)
    if st.get("wms.nibio.no") == "ok":
        try:
            r = http(SR16_ENDPOINTS[0], {"SERVICE": "WMS", "REQUEST": "GetCapabilities", "VERSION": "1.3.0"})
            layers, fmts = parse_wms_layers(r.content)
            print("SR16 layers:", [L["name"] for L in layers][:60], "chosen:", sr16_choose(layers), "GFI:", fmts)
        except FetchError as exc:
            print("SR16 ERROR", exc)
    bad = [h for h, s in st.items() if s != "ok"]
    if bad:
        print()
        print(blocked_message(bad))
    return st


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Probe the refinement data hosts")
    ap.add_argument("--probe", action="store_true")
    ap.parse_args()
    probe()
