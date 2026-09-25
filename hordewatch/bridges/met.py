"""Weather bridge: weather seen/heard on the stream vs. MET Norway products -> consistency grids.

Idea
----
Weather is a location fingerprint. If the stream shows rain at 14:10 while
the MET Nordic analysis is dry over Hedmark but wet over Oppland, Oppland
gains. A single frame says little, but hours of observations (rain, cloud
cover, direct sun, fog, condensation, temperature) are compared with the
gridded analysis/radar at every cell and accumulate into a per-day layer.

Products (all fail soft, all cached under data/hordewatch/met/)
* MET Nordic analysis 1 km (thredds.met.no metpplatest / metpparchive,
  ``met_analysis_1_0km_nordic_YYYYMMDDTHHZ.nc``): hourly precipitation_amount (mm
  over the previous hour = mm/h), cloud_area_fraction, air_temperature_2m,
  relative_humidity_2m. Fetched through the THREDDS NetCDF Subset Service as
  netCDF-3 (readable with scipy, no netCDF4 dependency), bbox-limited, with an
  OPeNDAP ASCII fallback. Located through the THREDDS catalog, so file-name
  changes do not break it.
* Radar composite (thredds remotesensing/reflectivity-nordic, the 'yr'
  composite): 5-min reflectivity -> rain rate with Marshall-Palmer Z = 200 R^1.6.
  Found through the monthly catalog; any variable holding dBZ or a rain rate is used.
* Frost station observations (optional ``frost_client_id``): hourly precipitation,
  temperature, cloud cover (octas), humidity, interpolated with a Gaussian kernel.
* Fixture: default.no met.json (points [lat, lon, T C, cloud %, precip mm, RH %]).

Scoring (pure functions below, unit-tested on synthetic grids)
* rain (rain_visual, audio_rain): p_wet(R) = logistic((ln(R + 0.02) - ln r50) / 0.8)
  with r50 = 0.1 / 0.5 / 1.5 mm/h for light / moderate / heavy observed intensity;
  P(detect) = hit p_wet + fa (1 - p_wet). Timing tolerance +-15 min: for "rain"
  the wettest product valid within the tolerance is used, for "dry" the
  driest; spatial tolerance of ~2 km (max/min filter) absorbs displaced showers.
* cloud_fraction: robust Gaussian eps + (1-eps) exp(-(f_obs - c)^2 / 2 0.3^2); the camera
  sees a small, low sky patch, hence the wide sigma.
* direct_sun: P(sun disc clear | c) = (1 - c)^1.5. "sun" -> hit 0.85 / fa 0.03; "no sun"
  is weak (canopy/terrain shade: an unlit scene under clear sky is common). Cells
  where the sun is below 3 deg are NaN (that is the astro bridge's job).
* fog: P(fog | RH) = logistic((RH - 97) / 1.5).
* condensation: needs near-saturation (T - Td < 2 C) or cold walls (T < 3 C); low weight.
* temperature: outside N(0, 3 C); inside the box (a person, closed walls) the
  offset is 0..+10 C with 3 C soft edges.
Soft (fractional) hourly observations are used as virtual evidence:
log(f P(yes | x) + (1-f) P(no | x)), so f = 0.5 carries no information.
Hours are summed within a local date and scaled by n_eff/n for weather errors
that persist for ~3 h (AR(1) with tau = 3 h -> factor ~1/6 for many hours).

Output: data/hordewatch/layers/weather_<kind>_<YYYYMMDD>.npz with conservative
reliabilities (0.2-0.5); layers of one weather family and day (rain_visual +
audio_rain, cloud_fraction + direct_sun, fog + condensation) share an
independence group, because they are compared against the same model errors.

Operation: the bridge rebuilds a (kind, day) layer when that day's observation count
changes; the lookback starts at a local midnight so a day is always scored from all
of its rows; downloads and scoring run in a worker thread (``async``), because a slow
THREDDS server must not stall the runner's frame/audio loop. Model units come from
the CF ``units`` attribute when present (value-range guesses are only a fallback).

Failure modes: the analysis smooths convective showers (the tolerances and the
floors handle it); the box interior differs from the air outside (temperature
weight low); looped audio (audio_rain near an audio_loop is ignored); overlap
with any manual weather layer in hordejakt.layers.weather is possible -- keep
hand-entered weather facts out of hordewatch or vice versa.
"""
from __future__ import annotations

import io
import json
import logging
import re
import time
import warnings
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from scipy.ndimage import maximum_filter, minimum_filter

from hordejakt import DEFAULTNO
from hordejakt.grid import Grid

from ..analyzers.base import Analyzer
from ..types import UTC, Observation
from .common import (OSLO, RateLimitedLog, cache_dir, from_unix, layers_dir, load_state, local_date, save_state,
                     setting, sub_grid, to_unix, upsample, write_layer)

log = logging.getLogger("hordewatch.bridges.met")
warn_once = RateLimitedLog(900)

MET_GRID = Grid(dlat=0.01, dlon=0.02)   # ~1.1 km, every second hordejakt cell (aligned)

KINDS = ("rain_visual", "audio_rain", "cloud_fraction", "direct_sun", "fog", "condensation", "temperature")
FAMILY = {"rain_visual": "rain", "audio_rain": "rain", "cloud_fraction": "cloud", "direct_sun": "cloud",
          "fog": "humidity", "condensation": "humidity", "temperature": "temperature"}
NEEDS = {"rain_visual": ("precip_rate_mmh",), "audio_rain": ("precip_rate_mmh",), "cloud_fraction": ("cloud_fraction",),
         "direct_sun": ("cloud_fraction",), "fog": ("relative_humidity",),
         "condensation": ("air_temperature_c", "relative_humidity"), "temperature": ("air_temperature_c",)}
RELIABILITY = {"rain_visual": 0.5, "audio_rain": 0.3, "cloud_fraction": 0.35, "direct_sun": 0.45, "fog": 0.35,
               "condensation": 0.2, "temperature": 0.3}
SPATIAL_TOL_KM = {"precip_rate_mmh": 2.0}
TIME_TOL_S = 900.0


# =========================================================================== pure scoring functions
def logistic(x):
    return 1.0 / (1.0 + np.exp(-np.asarray(x, float)))


def intensity_r50(intensity):
    """Observed intensity -> rain rate (mm/h) at which p_wet = 0.5."""
    if intensity is None:
        return 0.1
    if isinstance(intensity, str):
        return {"light": 0.1, "drizzle": 0.05, "moderate": 0.5, "heavy": 1.5}.get(intensity.lower(), 0.1)
    x = float(intensity)
    return 0.1 if x < 0.4 else (0.5 if x < 0.7 else 1.5)


def p_rain_given_rate(rate_mmh, r50=0.1, width=0.8, r_min=0.02):
    """Probability that it rains (noticeably) at a point whose analysed/radar rate is R.
    Logistic in ln R; R = 0 still gives ~0.1 (missed light showers)."""
    r = np.maximum(np.asarray(rate_mmh, float), 0.0)
    return logistic((np.log(r + r_min) - np.log(r50)) / width)


def rain_loglik(present, rate_mmh, intensity=None, hit=0.85, false_alarm=0.05):
    """log P(rain detector says ``present`` | model rate at x)."""
    pw = p_rain_given_rate(rate_mmh, r50=intensity_r50(intensity) if present else 0.1)
    p = hit * pw + false_alarm * (1.0 - pw)
    return np.log(p if present else 1.0 - p)


def cloud_loglik(frac_obs, cloud, sigma=0.3, eps=0.05):
    """log P(observed cloud fraction | model cloud_area_fraction), robust Gaussian."""
    d = float(frac_obs) - np.asarray(cloud, float)
    return np.log(eps + (1.0 - eps) * np.exp(-0.5 * (d / sigma) ** 2))


def sun_loglik(present, cloud, sun_elev_deg, gamma=1.5, hit=0.85, false_alarm=0.03, shade_hit=0.6, min_elev=3.0):
    """log P(direct-sun detector | cloud fraction, sun elevation). NaN where the sun is down.
    ``shade_hit`` = P(detector sees sun | sun disc clear) used for the 'no sun' case
    (canopy/terrain shading makes 'no sun' weak evidence)."""
    c = np.clip(np.asarray(cloud, float), 0.0, 1.0)
    clear = (1.0 - c) ** gamma
    if present:
        ll = np.log(hit * clear + false_alarm * (1.0 - clear))
    else:
        ll = np.log(1.0 - (shade_hit * clear + false_alarm * (1.0 - clear)))
    return np.where(np.asarray(sun_elev_deg) >= min_elev, ll, np.nan)


def fog_loglik(present, rh_pct, rh50=97.0, width=1.5, hit=0.8, false_alarm=0.05):
    pf = logistic((np.asarray(rh_pct, float) - rh50) / width)
    p = hit * pf + false_alarm * (1.0 - pf)
    return np.log(p if present else 1.0 - p)


def dewpoint_c(t_c, rh_pct):
    """Magnus formula (Alduchov & Eskridge 1996)."""
    a, b = 17.625, 243.04
    rh = np.clip(np.asarray(rh_pct, float), 1.0, 100.0)
    g = np.log(rh / 100.0) + a * np.asarray(t_c, float) / (b + np.asarray(t_c, float))
    return b * g / (a - g)


def condensation_loglik(present, t_c, rh_pct, hit=0.7, false_alarm=0.1):
    """Condensation/frost on the box walls: outside near saturation (dew/frost on the
    outer surface) or walls colder than the occupied interior's dew point (T < ~3 C)."""
    dd = np.asarray(t_c, float) - dewpoint_c(t_c, rh_pct)
    pc = np.maximum(logistic((2.0 - dd) / 1.0), logistic((3.0 - np.asarray(t_c, float)) / 1.5))
    p = hit * pc + false_alarm * (1.0 - pc)
    return np.log(p if present else 1.0 - p)


def temperature_loglik(t_obs_c, t_model_c, where="outside", sigma=3.0, inside=(0.0, 10.0)):
    """Outside: N(t_obs - t_model; 0, sigma). Inside the box: offset uniform on
    ``inside`` with Gaussian edges of width sigma."""
    d = float(t_obs_c) - np.asarray(t_model_c, float)
    if where == "inside":
        lo, hi = inside
        e = np.where(d < lo, lo - d, np.where(d > hi, d - hi, 0.0))
        return -0.5 * (e / sigma) ** 2
    return -0.5 * (d / sigma) ** 2


def soft_loglik(frac_yes, ll_yes, ll_no):
    """Virtual evidence: log(f P(yes|x) + (1-f) P(no|x))."""
    f = float(np.clip(frac_yes, 0.0, 1.0))
    with np.errstate(invalid="ignore"):   # NaN (no model data) stays NaN
        return np.logaddexp(np.log(max(f, 1e-12)) + ll_yes, np.log(max(1.0 - f, 1e-12)) + ll_no)


def decorrelation_factor(n_hours, tau_h=3.0):
    """n_eff / n for an AR(1) error with correlation exp(-lag / tau) at hourly lags."""
    if n_hours <= 1:
        return 1.0
    rho = np.exp(-1.0 / tau_h)
    n = float(n_hours)
    s = sum((1 - k / n) * rho ** k for k in range(1, int(n)))
    return 1.0 / (1.0 + 2.0 * s)


def solar_elevation(lat, lon, t_unix):
    """Sun elevation (deg, no refraction), Astronomical Almanac low-precision formulas (~0.05 deg)."""
    n = float(t_unix) / 86400.0 + 2440587.5 - 2451545.0
    L = np.radians((280.460 + 0.9856474 * n) % 360.0)
    g = np.radians((357.528 + 0.9856003 * n) % 360.0)
    lam = L + np.radians(1.915) * np.sin(g) + np.radians(0.020) * np.sin(2 * g)
    eps = np.radians(23.439 - 4e-7 * n)
    ra = np.arctan2(np.cos(eps) * np.sin(lam), np.cos(lam))
    dec = np.arcsin(np.sin(eps) * np.sin(lam))
    gmst_h = (18.697374558 + 24.06570982441908 * n) % 24.0
    ha = np.radians(gmst_h * 15.0 + np.asarray(lon, float)) - ra
    la = np.radians(np.asarray(lat, float))
    return np.degrees(np.arcsin(np.sin(la) * np.sin(dec) + np.cos(la) * np.cos(dec) * np.cos(ha)))


def spatial_tolerance(field, radius_cells, mode):
    """Max (mode 'max') or min filter over a (2r+1)^2 window, NaN-aware."""
    if radius_cells <= 0:
        return field
    f = np.asarray(field, float)
    nan = np.isnan(f)
    size = 2 * int(radius_cells) + 1
    if mode == "max":
        out = maximum_filter(np.where(nan, -np.inf, f), size=size, mode="nearest")
    else:
        out = minimum_filter(np.where(nan, np.inf, f), size=size, mode="nearest")
    return np.where(np.isfinite(out), out, np.nan)


# =========================================================================== model fields
@dataclass
class Field:
    """A model/observation field on a target grid, valid over [t_start, t_end] (unix)."""
    var: str               # precip_rate_mmh | cloud_fraction | air_temperature_c | relative_humidity
    t_start: float
    t_end: float
    values: np.ndarray
    product: str


def tolerant_field(fields, t0, t1, mode, tol_s=TIME_TOL_S):
    """Combine the fields valid within [t0 - tol, t1 + tol]: pointwise max ('max'),
    min ('min') or mean ('mean'). None if no field overlaps."""
    sel = [f for f in fields if f.t_end >= t0 - tol_s and f.t_start <= t1 + tol_s]
    if not sel:
        return None, []
    st = np.stack([f.values for f in sel]).astype(float)
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)   # all-NaN cells (outside product coverage)
        if mode == "max":
            v = np.nanmax(np.where(np.isnan(st), -np.inf, st), axis=0)
        elif mode == "min":
            v = np.nanmin(np.where(np.isnan(st), np.inf, st), axis=0)
        else:
            v = np.nanmean(st, axis=0)
    v = np.where(np.isfinite(v), v, np.nan)
    return v, sorted({f.product for f in sel})


class Regridder:
    """Nearest-neighbour map from a regular projected grid (1-D x, y + CRS) or from
    2-D lat/lon arrays onto a hordejakt-style lat/lon Grid."""

    def __init__(self, grid: Grid, x=None, y=None, crs=None, lat2d=None, lon2d=None):
        L, O = grid.mesh()
        self.shape = L.shape
        if crs is not None and x is not None:
            from pyproj import Transformer
            tr = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
            X, Y = tr.transform(O, L)
            x, y = np.asarray(x, float), np.asarray(y, float)
            dx, dy = x[1] - x[0], y[1] - y[0]
            j = np.rint((X - x[0]) / dx).astype(int)
            i = np.rint((Y - y[0]) / dy).astype(int)
            self.ok = (i >= 0) & (i < len(y)) & (j >= 0) & (j < len(x))
            self.i, self.j = np.where(self.ok, i, 0), np.where(self.ok, j, 0)
            self.max_d = None
        else:
            from scipy.spatial import cKDTree

            def xyz(la, lo):
                la, lo = np.radians(la), np.radians(lo)
                return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)
            src = xyz(np.asarray(lat2d, float), np.asarray(lon2d, float))
            tree = cKDTree(src.reshape(-1, 3))
            d, k = tree.query(xyz(L, O).reshape(-1, 3))
            spacing = np.nanmedian(np.abs(np.diff(np.asarray(lat2d, float), axis=0))) * 111.2
            self.ok = (d * 6371.0 <= max(1.5 * spacing, 0.8)).reshape(self.shape)
            self.i, self.j = np.unravel_index(k.reshape(self.shape), np.shape(lat2d))

    def __call__(self, values):
        v = np.asarray(values, float)[self.i, self.j]
        return np.where(self.ok, v, np.nan)


def stations_to_field(lats, lons, vals, grid: Grid, length_km=15.0, max_km=40.0, k=8, d0_km=3.0):
    """Interpolate station values to ``grid`` with weights exp(-d^2 / 2 L^2) / (d^2 + d0^2):
    inverse-distance near a station (the field reproduces the station within ~d0),
    Gaussian-limited far away (length scale L per variable), NaN beyond max_km."""
    from scipy.spatial import cKDTree
    lats, lons, vals = (np.asarray(a, float) for a in (lats, lons, vals))
    ok = np.isfinite(lats) & np.isfinite(lons) & np.isfinite(vals)
    L, O = grid.mesh()
    if not ok.any():
        return np.full(L.shape, np.nan)
    c = np.cos(np.radians(61.0))
    tree = cKDTree(np.c_[lats[ok] * 111.2, lons[ok] * 111.2 * c])
    kk = min(k, int(ok.sum()))
    d, idx = tree.query(np.c_[L.ravel() * 111.2, O.ravel() * 111.2 * c], k=kk)
    d, idx = d.reshape(len(d), -1), idx.reshape(len(idx), -1)
    w = np.exp(-0.5 * (d / length_km) ** 2) / (d ** 2 + d0_km ** 2)
    w = np.where(d <= max_km, w, 0.0)
    v = vals[ok][idx]
    s = w.sum(1)
    out = np.where(s > 1e-9, (w * v).sum(1) / np.maximum(s, 1e-12), np.nan)
    return out.reshape(L.shape)


# =========================================================================== providers
class MetProvider:
    name = "base"

    def fields(self, var, t0, t1, grid: Grid) -> list:
        raise NotImplementedError


class ArrayProvider(MetProvider):
    """In-memory fields (tests, or anything precomputed)."""
    name = "array"

    def __init__(self, fields):
        self._f = list(fields)

    def fields(self, var, t0, t1, grid):
        return [f for f in self._f if f.var == var and f.t_end >= t0 and f.t_start <= t1 and f.values.shape == grid.shape]


class DefaultNoMetFixture(MetProvider):
    """default.no met.json: {"tid": ISO, "punkter": [[lat, lon, T C, cloud %, precip mm, RH %], ...]} (0.2 deg points)."""
    name = "defaultno_met"
    COLS = {"air_temperature_c": 2, "cloud_fraction": 3, "precip_rate_mmh": 4, "relative_humidity": 5}

    def __init__(self, path=None, half_window_s=1800.0):
        self.path = Path(path or DEFAULTNO / "met.json")
        self.half = half_window_s

    def fields(self, var, t0, t1, grid):
        if var not in self.COLS or not self.path.exists():
            return []
        d = json.loads(self.path.read_text())
        t = to_unix(d["tid"])
        if not (t + self.half >= t0 and t - self.half <= t1):
            return []
        a = np.array([[np.nan if v is None else v for v in p] for p in d["punkter"]], float)
        v = a[:, self.COLS[var]]
        if var == "cloud_fraction":
            v = v / 100.0
        f = stations_to_field(a[:, 0], a[:, 1], v, grid, length_km=8.0, max_km=14.0)
        return [Field(var, t - self.half, t + self.half, f, "default.no met.json")]


def _session():
    import requests
    s = requests.Session()
    s.headers["User-Agent"] = "hordewatch/1.0 (hordejakten monitoring)"
    return s


def _read_netcdf3(data: bytes):
    from scipy.io import netcdf_file
    return netcdf_file(io.BytesIO(data), mode="r", mmap=False, maskandscale=True)


def parse_dap_ascii(text: str) -> dict:
    """Parse an OPeNDAP (DAP2) ``.ascii`` response into {name: ndarray}.
    Handles 1-D arrays ("x[3]" then "1, 2, 3") and grids
    ("v.v[1][2][3]" then rows "[0][0], 1, 2, 3")."""
    body = text.split("---------------------------------------------", 1)[-1]
    out, name, dims, vals = {}, None, None, []

    def flush():
        if name is not None:
            a = np.array(vals, float)
            out[name] = a.reshape(dims) if dims and np.prod(dims) == a.size else a
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^([A-Za-z_][\w.]*)((?:\[\d+\])+)$", line)
        if m:
            flush()
            name = m.group(1).split(".")[-1]
            dims = [int(x) for x in re.findall(r"\[(\d+)\]", m.group(2))]
            vals = []
            continue
        if name is None:
            continue
        line = re.sub(r"^(\[\d+\])+,\s*", "", line)
        for tok in line.split(","):
            tok = tok.strip()
            if tok:
                try:
                    vals.append(float(tok))
                except ValueError:
                    vals.append(np.nan)
    flush()
    return out


def parse_das(text: str) -> dict:
    """OPeNDAP DAS -> {var: {attr: value}} (numbers and strings)."""
    out, cur, depth = {}, None, 0
    for raw in text.splitlines():
        line = raw.strip()
        if line.endswith("{"):
            depth += 1
            if depth == 2:
                cur = line[:-1].strip()
                out[cur] = {}
            continue
        if line.startswith("}"):
            depth -= 1
            continue
        if cur and depth == 2:
            m = re.match(r'^(\w+)\s+(\w+)\s+(.*);$', line)
            if m:
                typ, key, val = m.groups()
                if typ.lower() == "string":
                    out[cur][key] = val.strip().strip('"')
                else:
                    try:
                        nums = [float(v) for v in val.split(",")]
                        out[cur][key] = nums[0] if len(nums) == 1 else nums
                    except ValueError:
                        out[cur][key] = val
    return out


def crs_from_attrs(attrs: dict):
    from pyproj import CRS
    for k in ("proj4", "proj4_string", "proj4string", "crs_wkt", "spatial_ref"):
        if attrs.get(k):
            try:
                return CRS.from_user_input(attrs[k])
            except Exception:
                pass
    try:
        return CRS.from_cf({k: v for k, v in attrs.items() if not isinstance(v, bytes)})
    except Exception:
        return None


class Thredds:
    """Minimal THREDDS client for thredds.met.no: catalog listing, NCSS netCDF-3
    subsets (scipy-readable) and OPeNDAP ASCII."""
    BASE = "https://thredds.met.no/thredds"

    def __init__(self, base=None, timeout=90.0):
        self.base = base or self.BASE
        self.timeout = timeout
        self._s = None

    def get(self, url, **kw):
        self._s = self._s or _session()
        try:
            r = self._s.get(url, timeout=self.timeout, **kw)
        except Exception as e:
            raise IOError(f"{url}: {e.__class__.__name__}: {e}") from e
        if r.status_code != 200:
            raise IOError(f"{url}: HTTP {r.status_code}")
        return r

    def catalog(self, path):
        """[(name, urlPath)] of the datasets in catalog/<path>/catalog.xml."""
        r = self.get(f"{self.base}/catalog/{path}/catalog.xml")
        root = ET.fromstring(r.content)
        out = []
        for el in root.iter():
            if el.tag.endswith("dataset") and el.get("urlPath"):
                out.append((el.get("name") or "", el.get("urlPath")))
        return out

    def ncss(self, url_path, variables, bbox, stride=1, **time_kw):
        la0, la1, lo0, lo1 = bbox
        params = [("var", v) for v in variables] + [("north", la1), ("south", la0), ("west", lo0), ("east", lo1),
                                                     ("horizStride", int(stride)), ("accept", "netcdf3")]
        params += list(time_kw.items())
        last = None
        for svc in ("ncss/grid", "ncss"):
            try:
                return self.get(f"{self.base}/{svc}/{url_path}", params=params).content
            except IOError as e:
                last = e
        raise last

    def dap_ascii(self, url_path, constraint):
        return self.get(f"{self.base}/dodsC/{url_path}.ascii?{constraint}").text

    def dap_das(self, url_path):
        return self.get(f"{self.base}/dodsC/{url_path}.das").text


def cf_times(values, units):
    """CF 'seconds|minutes|hours|days since YYYY-MM-DD[ T]hh:mm:ss[ +hh:mm|Z]' -> unix seconds."""
    units = units.decode() if isinstance(units, bytes) else str(units)
    m = re.match(r"\s*(\w+)\s+since\s+(\d{4}-\d{1,2}-\d{1,2})(?:[ T](\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?))?\s*(Z|UTC|[+-]\d{1,2}(?::?\d{2})?)?",
                 units)
    if not m:
        raise ValueError(f"unparseable time units {units!r}")
    scale = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}[m.group(1).lower().rstrip("s")]
    y, mo, d = (int(x) for x in m.group(2).split("-"))
    hh, mm, ss = 0, 0, 0.0
    if m.group(3):
        parts = m.group(3).split(":")
        hh, mm = int(parts[0]), int(parts[1])
        ss = float(parts[2]) if len(parts) > 2 else 0.0
    off = 0.0
    tz = m.group(4)
    if tz and tz not in ("Z", "UTC"):
        sign = -1 if tz.startswith("-") else 1
        t = tz[1:].replace(":", "")
        off = sign * (int(t[:2]) * 3600 + (int(t[2:4]) * 60 if len(t) > 2 else 0))
    from ..types import UTC
    ref = datetime(y, mo, d, hh, mm, tzinfo=UTC).timestamp() + ss - off
    return ref + np.asarray(values, float) * scale


def to_standard_units(ours, arr, units):
    """Convert a model field to the bridge's units (mm/h, fraction 0-1, deg C, % RH) using the
    CF ``units`` attribute. Returns ``arr`` unchanged when the units are missing or already
    standard, so the converters in var_map (value-range heuristics) only act as a fallback --
    a heuristic alone cannot tell a clear hour in % (max <= 1.5) from an overcast one in 0-1."""
    u = (units.decode() if isinstance(units, bytes) else str(units or "")).strip().lower()
    if not u:
        return arr
    if ours == "cloud_fraction" and u in ("%", "percent"):
        return arr / 100.0
    if ours == "relative_humidity" and u in ("1", "fraction", "0-1"):
        return arr * 100.0
    if ours == "air_temperature_c" and u in ("k", "kelvin"):
        return arr - 273.15
    return arr


def fields_from_netcdf3(data, var_map, grid, product, validity, regrid_cache=None):
    """Read a netCDF-3 subset: var_map {nc_var: (our_var, converter)}; validity(t_unix, our_var) -> (t0, t1)."""
    nc = _read_netcdf3(data)
    try:
        v = nc.variables
        out = []
        tname = next((n for n in ("time",) if n in v), None)
        times = np.atleast_1d(np.array(v[tname][:], float)) if tname else np.array([np.nan])
        if tname:
            times = cf_times(times, v[tname].units)
        for ncv, (ours, conv) in var_map.items():
            if ncv not in v:
                continue
            var = v[ncv]
            arr = np.ma.filled(np.ma.asarray(var[:], dtype=float), np.nan)
            arr = to_standard_units(ours, arr, getattr(var, "units", None))
            dims = var.dimensions
            gm = getattr(var, "grid_mapping", b"")
            gm = gm.decode() if isinstance(gm, bytes) else gm
            attrs = {k: (a.decode() if isinstance(a, bytes) else a) for k, a in v[gm]._attributes.items()} if gm in v else {}
            key = (product, gm, arr.shape[-2:])
            rg = (regrid_cache or {}).get(key)
            if rg is None:
                xn = next((d for d in dims if d in ("x", "X", "xc", "Xc")), dims[-1])
                yn = next((d for d in dims if d in ("y", "Y", "yc", "Yc")), dims[-2])
                crs = crs_from_attrs(attrs) if attrs else None
                if crs is not None and xn in v and yn in v:
                    x, y = np.array(v[xn][:], float), np.array(v[yn][:], float)
                    u = getattr(v[xn], "units", b"m")
                    if (u.decode() if isinstance(u, bytes) else u) == "km":
                        x, y = x * 1000.0, y * 1000.0
                    rg = Regridder(grid, x=x, y=y, crs=crs)
                else:
                    la = next((n for n in ("latitude", "lat") if n in v), None)
                    lo = next((n for n in ("longitude", "lon") if n in v), None)
                    if la is None:
                        raise IOError(f"{product}: no usable coordinates")
                    rg = Regridder(grid, lat2d=np.array(v[la][:], float), lon2d=np.array(v[lo][:], float))
                if regrid_cache is not None:
                    regrid_cache[key] = rg
            arr = arr.reshape((-1,) + arr.shape[-2:])
            for k in range(arr.shape[0]):
                t = times[min(k, len(times) - 1)]
                a0, a1 = validity(t, ours)
                out.append(Field(ours, a0, a1, conv(rg(arr[k])), product))
        return out
    finally:
        nc.close()


class MetNordicProvider(MetProvider):
    """MET Nordic analysis (1 km, hourly) from thredds.met.no; see module docstring."""
    name = "met_nordic"
    # converters run after to_standard_units (CF units attribute); the value-range tests only
    # matter when a subset arrives without units
    VARS = {"precipitation_amount": ("precip_rate_mmh", lambda a: np.maximum(a, 0.0)),
            "cloud_area_fraction": ("cloud_fraction", lambda a: np.clip(a / (100.0 if np.nanmax(a) > 1.5 else 1.0), 0, 1)),
            "air_temperature_2m": ("air_temperature_c", lambda a: a - 273.15 if np.nanmean(a) > 150 else a),
            "relative_humidity_2m": ("relative_humidity", lambda a: np.clip(a * 100.0 if np.nanmax(a) <= 1.5 else a, 0, 100))}
    FILE = "met_analysis_1_0km_nordic_{Y}{m}{d}T{H}Z.nc"

    def __init__(self, cache_root, thredds=None, stride=1, bbox=(57.9, 64.6, 4.4, 13.6)):
        self.cache = Path(cache_root)
        self.th = thredds or Thredds()
        self.stride = stride
        self.bbox = bbox
        self._rg = {}
        self._mem = {}

    @staticmethod
    def validity(t, var):
        if var == "precip_rate_mmh":
            return t - 3600.0, t        # accumulated over the previous hour
        return t - 1800.0, t + 1800.0

    def _candidates(self, hour: datetime):
        f = self.FILE.format(Y=hour.year, m=f"{hour.month:02d}", d=f"{hour.day:02d}", H=f"{hour.hour:02d}")
        return [f"metpplatest/{f}", f"metpparchive/{hour:%Y/%m/%d}/{f}"]

    def _hour(self, hour: datetime, grid):
        key = (hour, grid)
        if key in self._mem:
            return self._mem[key]
        dest = self.cache / "nordic" / f"{hour:%Y%m%dT%H}_{grid.lat_min:.2f}_{grid.lon_min:.2f}_{grid.nlat}x{grid.nlon}.npz"
        fields = []
        if dest.exists():
            d = np.load(dest)
            meta = json.loads(str(d["meta"]))
            for m in meta:
                fields.append(Field(m["var"], m["t0"], m["t1"], d[m["var"]].astype(float), m["product"]))
        else:
            data, last = None, None
            for path in self._candidates(hour):
                try:
                    data = self.th.ncss(path, list(self.VARS), self.bbox, self.stride)
                    break
                except IOError as e:
                    last = e
            if data is None:
                raise IOError(f"MET Nordic {hour:%Y-%m-%dT%H}Z unavailable: {last}")
            fields = fields_from_netcdf3(data, self.VARS, grid, "MET Nordic analysis", self.validity, self._rg)
            dest.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(dest, meta=np.array(json.dumps([{"var": f.var, "t0": f.t_start, "t1": f.t_end,
                                                                  "product": f.product} for f in fields])),
                                **{f.var: f.values.astype(np.float16) for f in fields})
        if len(self._mem) > 64:
            self._mem.clear()
        self._mem[key] = fields
        return fields

    def fields(self, var, t0, t1, grid):
        out = []
        h = from_unix(np.floor((t0 - TIME_TOL_S) / 3600.0) * 3600.0)
        end = from_unix(t1 + TIME_TOL_S + 3600.0)
        while h <= end:
            if (datetime.now(h.tzinfo) - h).total_seconds() > 20 * 60:  # analysis appears ~15 min after the hour
                try:
                    out += [f for f in self._hour(h, grid) if f.var == var]
                except Exception as e:
                    warn_once(f"nordic:{h:%Y%m%d%H}", "MET Nordic analysis not available (%s); weather layer skips this hour", e)
            h += timedelta(hours=1)
        return out


class RadarProvider(MetProvider):
    """MET radar composite (thredds remotesensing/reflectivity-nordic) -> rain rate fields.
    Datasets are found through the monthly THREDDS catalog; any variable with
    dBZ ('reflectivity' in the name) is converted with Z = 200 R^1.6, a rain-rate
    variable is used directly. Each 5-min scan is valid +-2.5 min."""
    name = "radar"
    CATALOG = "remotesensing/reflectivity-nordic/{Y}/{m}"

    def __init__(self, cache_root, thredds=None, stride=1, bbox=(57.9, 64.6, 4.4, 13.6), catalog=None):
        self.cache = Path(cache_root)
        self.th = thredds or Thredds()
        self.stride, self.bbox = stride, bbox
        self.catalog_tpl = catalog or self.CATALOG
        self._rg = {}

    @staticmethod
    def dbz_to_rate(dbz, min_dbz=7.0):
        z = np.asarray(dbz, float)
        r = (10.0 ** (z / 10.0) / 200.0) ** (1.0 / 1.6)
        return np.where(z >= min_dbz, r, 0.0)

    def fields(self, var, t0, t1, grid):
        if var != "precip_rate_mmh":
            return []
        day = from_unix(t0)
        dest = self.cache / "radar" / f"{day:%Y%m%dT%H%M}_{int(t1 - t0)}_{grid.nlat}x{grid.nlon}.npz"
        if dest.exists():
            d = np.load(dest)
            ts = d["t"]
            return [Field(var, t - 150, t + 150, d["rate"][k].astype(float), "MET radar") for k, t in enumerate(ts)]
        try:
            cat = self.th.catalog(self.catalog_tpl.format(Y=day.year, m=f"{day.month:02d}"))
            ymd = day.strftime("%Y%m%d")
            paths = [p for n, p in cat if ymd in n or ymd in p] or [p for n, p in cat if "dbz" in (n + p).lower()][:1]
            if not paths:
                raise IOError("no radar dataset in catalog")
            ts0 = from_unix(t0 - TIME_TOL_S).strftime("%Y-%m-%dT%H:%M:%SZ")
            ts1 = from_unix(t1 + TIME_TOL_S).strftime("%Y-%m-%dT%H:%M:%SZ")
            data = self.th.ncss(paths[0], ["equivalent_reflectivity_factor", "lwe_precipitation_rate"], self.bbox,
                                self.stride, time_start=ts0, time_end=ts1)
            conv = {"equivalent_reflectivity_factor": ("precip_rate_mmh", self.dbz_to_rate),
                    "lwe_precipitation_rate": ("precip_rate_mmh", lambda a: np.maximum(a, 0.0))}
            fields = fields_from_netcdf3(data, conv, grid, "MET radar", lambda t, v: (t - 150.0, t + 150.0), self._rg)
        except Exception as e:
            warn_once("radar", "MET radar composite unavailable (%s); rain layers use the analysis only", e)
            return []
        if fields:
            dest.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(dest, t=np.array([f.t_start + 150 for f in fields]),
                                rate=np.stack([f.values for f in fields]).astype(np.float16))
        return fields


class FrostProvider(MetProvider):
    """frost.met.no station observations (needs a free client id: frost.met.no/auth/requestCredentials.html)."""
    name = "frost"
    SRC = "https://frost.met.no/sources/v0.jsonld"
    OBS = "https://frost.met.no/observations/v0.jsonld"
    ELEMENTS = {"precip_rate_mmh": ("sum(precipitation_amount PT1H)", 1.0, 15.0),
                "air_temperature_c": ("air_temperature", 1.0, 30.0),
                "cloud_fraction": ("cloud_area_fraction", 1.0 / 8.0, 40.0),
                "relative_humidity": ("relative_humidity", 1.0, 30.0)}

    def __init__(self, cache_root, client_id, timeout=60.0, bbox=(58.0, 64.5, 4.5, 13.5)):
        self.cache = Path(cache_root)
        self.cid = client_id
        self.timeout = timeout
        self.bbox = bbox
        self._s = None
        self._stations = None

    def _get(self, url, params):
        self._s = self._s or _session()
        r = self._s.get(url, params=params, auth=(self.cid, ""), timeout=self.timeout)
        if r.status_code == 404:
            return {"data": []}
        if r.status_code != 200:
            raise IOError(f"frost HTTP {r.status_code}: {r.text[:200]}")
        return r.json()

    def stations(self):
        if self._stations is None:
            p = self.cache / "frost" / "stations.json"
            if p.exists() and time.time() - p.stat().st_mtime < 7 * 86400:
                self._stations = json.loads(p.read_text())
            else:
                la0, la1, lo0, lo1 = self.bbox
                poly = f"POLYGON(({lo0} {la0}, {lo1} {la0}, {lo1} {la1}, {lo0} {la1}, {lo0} {la0}))"
                j = self._get(self.SRC, {"types": "SensorSystem", "geometry": poly, "fields": "id,geometry,masl"})
                self._stations = {s["id"]: s["geometry"]["coordinates"][::-1] for s in j.get("data", []) if s.get("geometry")}
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(self._stations))
        return self._stations

    def fields(self, var, t0, t1, grid):
        if not self.cid or var not in self.ELEMENTS:
            return []
        elem, scale, length = self.ELEMENTS[var]
        try:
            st = self.stations()
            ids = sorted(st)
            ref = f"{from_unix(t0 - 3600):%Y-%m-%dT%H:00:00Z}/{from_unix(t1 + 3600):%Y-%m-%dT%H:00:00Z}"
            by_hour = {}
            for k in range(0, len(ids), 50):
                j = self._get(self.OBS, {"sources": ",".join(ids[k:k + 50]), "referencetime": ref, "elements": elem})
                for d in j.get("data", []):
                    sid = d["sourceId"].split(":")[0]
                    if sid not in st:
                        continue
                    t = to_unix(d["referenceTime"])
                    for o in d.get("observations", []):
                        if o.get("value") is not None:
                            by_hour.setdefault(round(t / 3600) * 3600, []).append((*st[sid], float(o["value"]) * scale))
        except Exception as e:
            warn_once("frost", "Frost unavailable (%s); continuing without station data", e)
            return []
        out = []
        for t, rows in sorted(by_hour.items()):
            a = np.array(rows)
            f = stations_to_field(a[:, 0], a[:, 1], a[:, 2], grid, length_km=length, max_km=2.5 * length)
            a0, a1 = (t - 3600, t) if var == "precip_rate_mmh" else (t - 1800, t + 1800)
            out.append(Field(var, a0, a1, f, "Frost stations"))
        return out


# =========================================================================== aggregation + scoring
def _hour_key(t):
    return int(t // 3600) * 3600


def aggregate_hourly(kind, rows):
    """Reduce raw observation rows of one kind to hourly summaries.
    Returns [{t0, t1, n, frac|value|where|intensity}] (confidence-weighted)."""
    bins = {}
    for r in rows:
        bins.setdefault(_hour_key(to_unix(r["ts"])), []).append(r)
    out = []
    for h, rs in sorted(bins.items()):
        ts = [to_unix(r["ts"]) for r in rs]
        w = np.array([max(float(r.get("confidence") or 0.5), 0.05) for r in rs])
        s = {"t0": min(ts), "t1": max(ts), "n": len(rs)}
        vals = [r["value"] for r in rs]
        if kind in ("rain_visual", "direct_sun", "fog", "condensation"):
            yes = np.array([1.0 if v.get("present", True) else 0.0 for v in vals])
            s["frac"] = float(np.sum(w * yes) / np.sum(w))
            if kind == "rain_visual":
                ints = [v.get("intensity") for v, y in zip(vals, yes) if y and v.get("intensity") is not None]
                s["intensity"] = (max(ints, key=lambda x: intensity_r50(x)) if ints else None)
        elif kind == "audio_rain":
            s["frac"] = 1.0  # only detections are reported: no negative evidence from audio
            ints = [v.get("intensity") for v in vals if v.get("intensity") is not None]
            s["intensity"] = max(ints, key=lambda x: intensity_r50(x)) if ints else None
        elif kind == "cloud_fraction":
            f = np.array([float(v.get("fraction", np.nan)) for v in vals])
            ok = np.isfinite(f)
            if not ok.any():
                continue
            s["value"] = float(np.sum(w[ok] * f[ok]) / np.sum(w[ok]))
        elif kind == "temperature":
            f = np.array([float(v.get("temp_c", v.get("value", np.nan))) for v in vals])
            ok = np.isfinite(f)
            if not ok.any():
                continue
            s["value"] = float(np.sum(w[ok] * f[ok]) / np.sum(w[ok]))
            wh = [v.get("where", "outside") for v in vals]
            s["where"] = "inside" if wh.count("inside") > len(wh) / 2 else "outside"
        out.append(s)
    return out


def score_hour(kind, summ, get_field, grid: Grid):
    """loglik for one hourly summary. get_field(var, t0, t1, mode) -> (array|None, products)."""
    t0, t1 = summ["t0"], summ["t1"]
    tol_cells = lambda var: int(round(SPATIAL_TOL_KM.get(var, 0.0) / (grid.dlat * 111.2)))
    if kind in ("rain_visual", "audio_rain"):
        wet, p1 = get_field("precip_rate_mmh", t0, t1, "max")
        dry, p2 = get_field("precip_rate_mmh", t0, t1, "min")
        if wet is None:
            return None, []
        r = tol_cells("precip_rate_mmh")
        ll_y = rain_loglik(True, spatial_tolerance(wet, r, "max"), summ.get("intensity"),
                           hit=0.85 if kind == "rain_visual" else 0.7, false_alarm=0.05 if kind == "rain_visual" else 0.1)
        ll_n = rain_loglik(False, spatial_tolerance(dry, r, "min"))
        return soft_loglik(summ["frac"], ll_y, ll_n), sorted(set(p1) | set(p2))
    if kind == "cloud_fraction":
        c, p = get_field("cloud_fraction", t0, t1, "mean")
        return (None, []) if c is None else (cloud_loglik(summ["value"], c), p)
    if kind == "direct_sun":
        c, p = get_field("cloud_fraction", t0, t1, "mean")
        if c is None:
            return None, []
        L, O = grid.mesh()
        el = solar_elevation(L, O, 0.5 * (t0 + t1))
        return soft_loglik(summ["frac"], sun_loglik(True, c, el), sun_loglik(False, c, el)), p
    if kind == "fog":
        rh, p = get_field("relative_humidity", t0, t1, "mean")
        return (None, []) if rh is None else (soft_loglik(summ["frac"], fog_loglik(True, rh), fog_loglik(False, rh)), p)
    if kind == "condensation":
        t, p1 = get_field("air_temperature_c", t0, t1, "mean")
        rh, p2 = get_field("relative_humidity", t0, t1, "mean")
        if t is None or rh is None:
            return None, []
        return soft_loglik(summ["frac"], condensation_loglik(True, t, rh), condensation_loglik(False, t, rh)), p1 + p2
    if kind == "temperature":
        t, p = get_field("air_temperature_c", t0, t1, "mean")
        return (None, []) if t is None else (temperature_loglik(summ["value"], t, summ.get("where", "outside")), p)
    raise ValueError(kind)


def score_kind_day(kind, rows, providers, grid: Grid):
    """Sum hourly logliks for one kind (rows of one local date), decorrelation-scaled.
    Returns (loglik or None, info)."""
    cache = {}

    def get_field(var, t0, t1, mode):
        k = (var, _hour_key(t0), _hour_key(t1))
        if k not in cache:
            fs = []
            for p in providers:
                try:
                    fs += p.fields(var, t0 - TIME_TOL_S, t1 + TIME_TOL_S, grid)
                except Exception as e:
                    warn_once(f"met:{getattr(p, 'name', p)}", "weather provider %s failed: %s", getattr(p, "name", p), e)
            cache[k] = fs
        return tolerant_field(cache[k], t0, t1, mode)

    total, n, prods = None, 0, set()
    for s in aggregate_hourly(kind, rows):
        ll, p = score_hour(kind, s, get_field, grid)
        if ll is None or not np.isfinite(ll).any():   # no product, or e.g. sun below 3 deg everywhere
            continue
        prods |= set(p)
        total = ll if total is None else np.where(np.isnan(total), ll, np.where(np.isnan(ll), total, total + ll))
        n += 1
    if total is None:
        return None, {"hours": 0}
    return total * decorrelation_factor(n), {"hours": n, "products": sorted(prods)}


# =========================================================================== bridge
class WeatherBridge(Analyzer):
    """Periodically rebuilds weather_<kind>_<date>.npz from weather observations.

    Config: providers (default ["met_nordic", "radar", "frost"]; "defaultno_met" fixture;
    objects allowed), frost_client_id, lookback_days (3), met_grid (Grid, default MET_GRID),
    nordic_stride (1), recompute_s (1800: re-try days whose model hours were missing),
    async (True: downloads + scoring in a worker thread; results are collected on a later tick).
    """
    name = "weather_bridge"
    tick_interval_s = 900.0

    def __init__(self, config=None):
        super().__init__(config)
        self.providers = None
        g = setting(self.config, "met_grid", None) or MET_GRID
        self.grid = Grid(**g) if isinstance(g, dict) else g   # YAML gives a dict

    def build_providers(self):
        if self.providers is not None:
            return self.providers
        root = None
        out = []
        for p in setting(self.config, "providers", ["met_nordic", "radar", "frost"]):
            if isinstance(p, str) and root is None:
                root = cache_dir(self.config, "met")
            if not isinstance(p, str):
                out.append(p)
            elif p == "met_nordic":
                out.append(MetNordicProvider(root, stride=int(setting(self.config, "nordic_stride", 1))))
            elif p == "radar":
                out.append(RadarProvider(root))
            elif p == "frost":
                cid = setting(self.config, "frost_client_id")
                if cid:
                    out.append(FrostProvider(root, cid))
            elif p == "defaultno_met":
                out.append(DefaultNoMetFixture(setting(self.config, "defaultno_met_path")))
            else:
                log.warning("unknown weather provider %s", p)
        self.providers = out
        return out

    def rows_by_day(self, db, now=None):
        """Weather rows grouped by (kind, local date). The lookback starts at a local
        midnight, so every day it returns is complete: a day that slides out of the
        window disappears entirely (its last full layer stays on disk) instead of being
        rebuilt from its remaining tail, which would silently weaken that day's layer."""
        now = time.time() if now is None else now
        days = min(float(setting(self.config, "lookback_days", 3)), 3650.0)
        start = (from_unix(now).astimezone(OSLO) - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
        since = start.astimezone(UTC)
        rows = db.observations(kind=list(KINDS), since=since)
        loops = [to_unix(r["ts"]) for r in db.observations(kind="audio_loop", since=since)]
        groups = {}
        for r in rows:
            if r["kind"] == "audio_rain" and any(abs(to_unix(r["ts"]) - lt) < 60 for lt in loops):
                continue
            groups.setdefault((r["kind"], local_date(r["ts"])), []).append(r)
        return groups

    def build_day(self, kind, date, rows, write=True):
        grid = self.grid
        ll, info = score_kind_day(kind, rows, self.build_providers(), grid)
        if ll is None:
            return None, info
        out_grid = sub_grid(grid.lat_min, grid.lat_max, grid.lon_min, grid.lon_max)
        fine = upsample(np.nan_to_num(ll, nan=0.0), grid.lats, grid.lons, out_grid, order=0)
        mask = upsample(np.isnan(ll).astype(float), grid.lats, grid.lons, out_grid, order=0) > 0.5
        fine = np.where(mask, np.nan, fine)
        info.update(kind=kind, date=date, n_obs=len(rows))
        if write:
            path = layers_dir(self.config) / f"weather_{kind}_{date}.npz"
            desc = (f"hordewatch: {kind} observed on {date} ({len(rows)} obs, {info['hours']} h) vs "
                    + ", ".join(info.get("products", [])))
            write_layer(path, fine, name=f"hw_weather_{kind}_{date}", reliability=RELIABILITY[kind],
                        independence_group=f"hw_weather_{FAMILY[kind]}_{date}", description=desc,
                        sources=info.get("products", []), grid=out_grid, extra={"hours": info["hours"], "n_obs": len(rows)})
            info["path"] = str(path)
        fin = np.isfinite(ll)
        info["consistent_cells"] = int(np.sum(ll[fin] > np.max(ll[fin]) - 1.0)) if fin.any() else 0
        info["frac_consistent"] = float(info["consistent_cells"] / max(fin.sum(), 1))
        return fine, info

    def _build_jobs(self, jobs, now):
        """Rebuild [(kind, date, rows)] -> [(kind, date, rows, info | None, error | None)].
        Pure w.r.t. the DB, so it can run in the worker thread (downloads happen here)."""
        res = []
        for kind, date, rows in jobs:
            try:
                _, info = self.build_day(kind, date, rows)
                res.append((kind, date, rows, info, None))
            except Exception as e:
                log.exception("weather layer %s:%s failed: %s", kind, date, e)
                res.append((kind, date, rows, None, str(e)))
        return res

    def _finish_jobs(self, state, results, t_done):
        out = []
        for kind, date, rows, info, err in results:
            if info is None:
                continue
            n_hours_obs = len({_hour_key(to_unix(r["ts"])) for r in rows})
            state["days"][f"{kind}:{date}"] = {"n_obs": len(rows), "t": t_done, "hours": info.get("hours", 0),
                                               "missing": info.get("hours", 0) < n_hours_obs}
            if info.get("hours"):
                ts = max(r["ts"] for r in rows)
                out.append(Observation("weather_match", ts, {"product": ",".join(info.get("products", [])),
                                                             "cells": info["consistent_cells"], "kind": kind, "date": date,
                                                             "hours": info["hours"],
                                                             "frac_consistent": round(info["frac_consistent"], 3),
                                                             "layer": info.get("path")},
                                       analyzer=self.name, confidence=RELIABILITY[kind]))
        return out

    def on_tick(self, ctx):
        """Collect a finished rebuild, then queue the (kind, date) layers whose observations
        changed (or whose model hours were missing, after recompute_s). The rebuild --
        THREDDS / Frost downloads of several hourly fields -- runs in a single worker
        thread (config ``async``, default True): the Analyzer contract forbids blocking
        the runner's frame/audio loop for more than a few seconds."""
        state = load_state(ctx.db, self.name, {"days": {}})
        now = time.time()
        out = []
        fut = getattr(self, "_future", None)
        if fut is not None and fut.done():
            self._future = None
            try:
                out += self._finish_jobs(state, fut.result(), now)
            except Exception as e:
                log.exception("weather rebuild failed: %s", e)
        if getattr(self, "_future", None) is None:
            jobs = []
            for (kind, date), rows in sorted(self.rows_by_day(ctx.db, now).items()):
                prev = state["days"].get(f"{kind}:{date}", {})
                fresh = prev.get("n_obs") == len(rows)
                retry = prev.get("missing") and now - prev.get("t", 0) > float(setting(self.config, "recompute_s", 1800))
                if not fresh or retry:
                    jobs.append((kind, date, rows))
            if jobs and setting(self.config, "async", True):
                if getattr(self, "_pool", None) is None:
                    from concurrent.futures import ThreadPoolExecutor
                    self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="weather-bridge")
                self._future = self._pool.submit(self._build_jobs, jobs, now)
            elif jobs:
                out += self._finish_jobs(state, self._build_jobs(jobs, now), now)
        save_state(ctx.db, self.name, state)
        return out
