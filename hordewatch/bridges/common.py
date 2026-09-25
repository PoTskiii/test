"""Shared plumbing for the hordewatch bridges.

A *bridge* turns hordewatch observations (things seen/heard on the stream)
into location evidence for the hordejakt engine. The hand-over format is the
one ``hordejakt.layers.live`` reads (see CONTRACT.md "Bridges"):

    data/hordewatch/layers/<name>.npz
        loglik  float32 array on hordejakt.grid.GRID (NaN = no information), or on
                a sub-grid with the same cell size whose lower-left centre is
                given by lat_min/lon_min (dlat/dlon are stored for checking)
        meta    JSON string {name, reliability, independence_group, description, sources, ...}

This module holds what every bridge needs: where files go (overridable per
bridge for tests), an atomic layer writer, coarse-grid helpers, small
persistent bridge state in the DB calibration table, and time helpers.

Design rules shared by all bridges
* Never emit -inf: a bridge is never certain enough to exclude a cell
  outright (only hordejakt's own hard layers do that). Log-likelihoods are
  clipped to ``LOGLIK_FLOOR`` below their maximum.
* Reliability is the probability that the evidence *model* is right (see
  hordejakt.layers.base). Bridges clip it to [0.05, 0.9] and use conservative
  defaults; fusion then bounds the damage a wrong layer can do (L >= 1 - r).
* Writes are atomic (tmp file + os.replace) because the engine may read the
  directory while a bridge writes.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates

from hordejakt.grid import GRID, Grid

from ..types import UTC, parse_iso

log = logging.getLogger("hordewatch.bridges")

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "hordewatch"
DEFAULT_LAYERS_DIR = DATA / "layers"
OUTPUT = ROOT / "output"

LOGLIK_FLOOR = -30.0          # loglik is clipped to max - 30 (likelihood ratio 1e-13)
REL_MIN, REL_MAX = 0.05, 0.9

try:  # Europe/Oslo for "dates" in file names; fixed CEST fallback when tzdata is missing
    from zoneinfo import ZoneInfo
    OSLO = ZoneInfo("Europe/Oslo")
except Exception:  # pragma: no cover
    OSLO = timezone(timedelta(hours=2))


# --------------------------------------------------------------------------- config / paths
def setting(config: dict | None, key: str, default=None):
    """Look a bridge setting up in its own analyzer_config, then in the global
    ``bridges:`` section of hordewatch.yaml, then fall back to ``default``."""
    config = config or {}
    if key in config:
        return config[key]
    g = (config.get("_global") or {}).get("bridges") or {}
    return g.get(key, default)


def resolve_path(p, base: Path = ROOT) -> Path:
    p = Path(p)
    return p if p.is_absolute() else base / p


def layers_dir(config) -> Path:
    return resolve_path(setting(config, "layers_dir", DEFAULT_LAYERS_DIR))


def cache_dir(config, sub: str) -> Path:
    d = resolve_path(setting(config, "cache_dir", DATA)) / sub
    d.mkdir(parents=True, exist_ok=True)
    return d


# --------------------------------------------------------------------------- time
def to_unix(ts) -> float:
    if isinstance(ts, (int, float, np.floating)):
        return float(ts)
    if isinstance(ts, str):
        ts = parse_iso(ts)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts.timestamp()


def from_unix(t: float) -> datetime:
    return datetime.fromtimestamp(float(t), UTC)


def local_date(ts) -> str:
    """YYYYMMDD of a UTC timestamp in Norwegian local time."""
    return from_unix(to_unix(ts)).astimezone(OSLO).strftime("%Y%m%d")


def stamp(ts) -> str:
    return from_unix(to_unix(ts)).strftime("%Y%m%dT%H%M%SZ")


def capture_time(obs: dict, clock=None, default_latency_s: float = 30.0, latency: float | None = None) -> float:
    """Unix capture (stream) time of the *phenomenon* of an observation row from DB.observations().

    Observation.ts is the estimated real time of the phenomenon = its capture time
    minus the latency the analyzer used, so capture = ts + latency_used. Pass
    ``latency`` (from :func:`observation_latencies`) whenever a DB is available.

    ``ts_capture`` is NOT a safe substitute in general: it is the capture time of
    the frame the observation was *emitted* on, which for some analyzers is not
    the frame of the phenomenon (gesture 'summary' rows carry the onset ts but the
    end-of-episode frame; aircraft_light carries the first track point's ts but
    the frame that closed the track, tens of seconds later). Without ``latency``
    the order is: value['latency_s'] (analyzer-reported), ts_capture, clock.
    """
    if latency is not None:
        return to_unix(obs["ts"]) + float(latency)
    v = obs.get("value") if isinstance(obs.get("value"), dict) else {}
    if isinstance(v.get("latency_s"), (int, float)) and np.isfinite(v["latency_s"]):
        return to_unix(obs["ts"]) + float(v["latency_s"])
    if obs.get("ts_capture") is not None:
        return to_unix(obs["ts_capture"])
    lat = getattr(clock, "latency_s", None)
    return to_unix(obs["ts"]) + float(default_latency_s if lat is None else lat)


def observation_latencies(db, rows, clock=None, default_latency_s: float = 30.0) -> list:
    """Stream latency (s) the producing analyzer used for each observation row,
    i.e. capture - real of the frame / audio chunk the row references.

    Order of preference per row: the referenced frame (``frame_id``) or audio chunk
    (``audio_id``) in the DB (capture_ts - real_ts: exactly what the analyzer's
    real times were derived from, also after a later re-calibration of the clock);
    ``value['latency_s']``; ``ts_capture - ts`` (rows without a frame/audio
    reference, e.g. manual entries); the clock's current latency; the default.
    """
    fmap, amap = {}, {}
    con = getattr(db, "con", None)
    for table, key, out in (("frames", "frame_id", fmap), ("audio", "audio_id", amap)):
        ids = sorted({int(r[key]) for r in rows if r.get(key) is not None})
        if con is None or not ids:
            continue
        try:
            for k in range(0, len(ids), 500):
                chunk = ids[k:k + 500]
                q = f"SELECT id, capture_ts, real_ts FROM {table} WHERE id IN ({','.join('?' * len(chunk))})"
                for i, c, r in con.execute(q, chunk):
                    if c and r:
                        out[int(i)] = to_unix(c) - to_unix(r)
        except Exception as e:  # never let a lookup failure stop a bridge
            log.debug("latency lookup in %s failed: %s", table, e)
    clat = getattr(clock, "latency_s", None)
    res = []
    for r in rows:
        v = r.get("value") if isinstance(r.get("value"), dict) else {}
        if r.get("frame_id") is not None and int(r["frame_id"]) in fmap:
            res.append(fmap[int(r["frame_id"])])
        elif r.get("audio_id") is not None and int(r["audio_id"]) in amap:
            res.append(amap[int(r["audio_id"])])
        elif isinstance(v.get("latency_s"), (int, float)) and np.isfinite(v["latency_s"]):
            res.append(float(v["latency_s"]))
        elif r.get("ts_capture") is not None:
            res.append(to_unix(r["ts_capture"]) - to_unix(r["ts"]))
        else:
            res.append(float(default_latency_s if clat is None else clat))
    return res


# --------------------------------------------------------------------------- grids
def coarse_axes(box=(58.0, 64.5, 4.5, 13.5), dlat=0.02, dlon=0.04):
    la0, la1, lo0, lo1 = box
    return np.arange(la0, la1 + 1e-9, dlat), np.arange(lo0, lo1 + 1e-9, dlon)


def upsample(coarse: np.ndarray, clats: np.ndarray, clons: np.ndarray, grid: Grid = GRID, order: int = 1):
    """Bilinear interpolation of a regular coarse lat/lon field onto ``grid``
    (edge values are extended; NaN propagates to the neighbouring cells)."""
    fi = (grid.lats - clats[0]) / (clats[1] - clats[0])
    fj = (grid.lons - clons[0]) / (clons[1] - clons[0])
    I, J = np.meshgrid(fi, fj, indexing="ij")
    return map_coordinates(np.asarray(coarse, float), [I, J], order=order, mode="nearest")


def sub_grid(lat_min, lat_max, lon_min, lon_max, base: Grid = GRID) -> Grid:
    """A Grid with ``base``'s cell size whose centres are aligned with ``base``."""
    i0, j0 = base.index(lat_min, lon_min)
    i1, j1 = base.index(lat_max, lon_max)
    i0, j0 = max(int(i0), 0), max(int(j0), 0)
    i1 = base.nlat - 1 if i1 < 0 else int(i1)
    j1 = base.nlon - 1 if j1 < 0 else int(j1)
    return Grid(lat_min=float(base.lats[i0]), lat_max=float(base.lats[i1]),
                lon_min=float(base.lons[j0]), lon_max=float(base.lons[j1]), dlat=base.dlat, dlon=base.dlon)


# --------------------------------------------------------------------------- layer files
def clean_loglik(loglik: np.ndarray) -> np.ndarray:
    """float32 copy with +-inf removed and values clipped to max + LOGLIK_FLOOR."""
    ll = np.array(loglik, dtype=float)
    fin = np.isfinite(ll)
    if not fin.any():
        return ll.astype(np.float32)
    top = float(np.max(ll[fin]))
    ll = np.where(np.isposinf(ll), top, ll)
    ll = np.where(np.isneginf(ll), top + LOGLIK_FLOOR, ll)
    ll = np.where(np.isnan(ll), np.nan, np.maximum(ll, top + LOGLIK_FLOOR))
    return (ll - top).astype(np.float32)


def write_layer(path, loglik, *, name, reliability, independence_group, description="", sources=(),
                grid: Grid = GRID, extra: dict | None = None) -> Path:
    """Atomically write a hordejakt live layer (see module docstring).

    ``grid`` may be a sub-grid of GRID with identical cell size; its lower-left
    centre is stored so hordejakt.layers.live can paste it in place.
    """
    path = Path(path)
    ll = clean_loglik(loglik)
    if ll.shape != grid.shape:
        raise ValueError(f"loglik shape {ll.shape} != grid shape {grid.shape}")
    if abs(grid.dlat - GRID.dlat) > 1e-9 or abs(grid.dlon - GRID.dlon) > 1e-9:
        raise ValueError("live layers must use the hordejakt GRID cell size")
    meta = {"name": name, "reliability": float(np.clip(reliability, REL_MIN, REL_MAX)),
            "independence_group": independence_group, "description": description,
            "sources": list(sources), "created": datetime.now(UTC).isoformat(timespec="seconds")}
    if extra:
        meta.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    arrays = {"loglik": ll, "meta": np.array(json.dumps(meta, ensure_ascii=False, default=_json_default))}
    if grid.shape != GRID.shape or grid.lat_min != GRID.lat_min or grid.lon_min != GRID.lon_min:
        arrays.update(lat_min=np.float64(grid.lat_min), lon_min=np.float64(grid.lon_min),
                      dlat=np.float64(grid.dlat), dlon=np.float64(grid.dlon))
    with open(tmp, "wb") as f:
        np.savez_compressed(f, **arrays)
    os.replace(tmp, path)
    return path


def read_layer(path):
    d = np.load(path, allow_pickle=False)
    return d["loglik"].astype(float), json.loads(str(d["meta"]))


def _json_default(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, datetime):
        return o.isoformat()
    return str(o)


def dumps(obj, **kw) -> str:
    return json.dumps(obj, default=_json_default, ensure_ascii=False, **kw)


# --------------------------------------------------------------------------- persistent state
def load_state(db, name: str, default=None) -> dict:
    """Small per-bridge state kept in the DB calibration table (survives restarts)."""
    if db is None:
        return dict(default or {})
    try:
        v = db.calibration(f"bridge_state:{name}")
    except Exception:
        v = None
    return v if isinstance(v, dict) else dict(default or {})


def save_state(db, name: str, state: dict):
    if db is not None:
        db.set_calibration(f"bridge_state:{name}", json.loads(dumps(state)))


class RateLimitedLog:
    """Log a recurring failure (network down, ...) at most once per ``every_s``."""

    def __init__(self, every_s=600.0):
        self.every_s = every_s
        self._last = {}

    def __call__(self, key, msg, *args, level=logging.WARNING):
        now = time.monotonic()
        if now - self._last.get(key, -1e18) >= self.every_s:
            self._last[key] = now
            log.log(level, msg, *args)
            return True
        return False


# --------------------------------------------------------------------------- posterior candidates
def posterior_candidates(posterior_path=None, hotspots_path=None, k=40, block=(10, 10)):
    """Candidate box locations with weights from the current hordejakt output.

    Prefers output/posterior.npz: the posterior is pooled into blocks of
    ``block`` cells (default 10 x 10 = 0.05 deg x 0.1 deg, ~5.5 x 5.4 km), the ``k`` blocks
    with most mass are returned at their mass-weighted centroid with their mass
    (renormalised). Falls back to hotspots.json (weights p_within_1.5km).
    Returns (lats, lons, weights) or None.
    """
    posterior_path = Path(posterior_path or OUTPUT / "posterior.npz")
    hotspots_path = Path(hotspots_path or OUTPUT / "hotspots.json")
    if posterior_path.exists():
        try:
            d = np.load(posterior_path)
            post = d["post"].astype(float)
            lat0 = float(d["lat_min"]) if "lat_min" in d.files else GRID.lat_min
            lon0 = float(d["lon_min"]) if "lon_min" in d.files else GRID.lon_min
            dlat = float(d["dlat"]) if "dlat" in d.files else GRID.dlat
            dlon = float(d["dlon"]) if "dlon" in d.files else GRID.dlon
            bi, bj = block
            H = (post.shape[0] // bi) * bi
            W = (post.shape[1] // bj) * bj
            p = np.nan_to_num(post[:H, :W])
            lats = lat0 + np.arange(H) * dlat
            lons = lon0 + np.arange(W) * dlon
            mass = p.reshape(H // bi, bi, W // bj, bj).sum(axis=(1, 3))
            mlat = (p * lats[:, None]).reshape(H // bi, bi, W // bj, bj).sum(axis=(1, 3))
            mlon = (p * lons[None, :]).reshape(H // bi, bi, W // bj, bj).sum(axis=(1, 3))
            order = np.argsort(mass, axis=None)[::-1][:k]
            m = mass.ravel()[order]
            ok = m > 0
            if ok.any():
                m = m[ok]
                la = mlat.ravel()[order][ok] / m
                lo = mlon.ravel()[order][ok] / m
                return la, lo, m / m.sum()
        except Exception as e:  # corrupt/partial file: fall through
            log.warning("could not read posterior %s: %s", posterior_path, e)
    if hotspots_path.exists():
        try:
            spots = json.loads(hotspots_path.read_text())["hotspots"][:k]
            la = np.array([s["lat"] for s in spots])
            lo = np.array([s["lon"] for s in spots])
            w = np.array([s.get("p_within_1.5km", s.get("p_cell", 1.0)) for s in spots], float)
            return la, lo, w / w.sum()
        except Exception as e:
            log.warning("could not read hotspots %s: %s", hotspots_path, e)
    return None
