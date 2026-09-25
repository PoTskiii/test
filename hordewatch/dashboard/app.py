"""hordewatch dashboard: FastAPI app factory, JSON API and Server-Sent Events for the single-page UI.

Run it with ``.venv/bin/python -m hordewatch.dashboard --db data/hordewatch/hordewatch.sqlite --port 8787``
(or ``scripts/hordewatch_all.sh``, which also starts the runner). The UI is ``static/index.html``.

What the page shows
-------------------
1. Live observation table (``/api/observations`` + SSE): kind / analyzer / confidence / time / text
   filters, a one-line value summary per kind (:func:`summarize_value`), both UTC and Europe/Oslo times,
   and links to the archived frame (or the nearest archived frame in time for audio/tick observations)
   and to the archived audio chunk.
2. Whiteboard transcripts (``/api/whiteboard``): OCR and VLM readings of the same physical board
   hold are merged into one card (same ``track_id`` within 20 min, or ``revision_of``), newest first,
   with a crop of the board cut from the archived full frame (``/api/whiteboard/{id}/crop.jpg``).
3. Alerts (``/api/events``): the ``events`` table with acknowledge / reopen, pushed live over SSE and
   optionally to a phone via ntfy (:mod:`hordewatch.dashboard.notify`).
4. Timeline (``/api/timeline``): bucketed sky/scene luma, cloud fraction, visual and audio rain,
   event swim-lanes (aircraft cues, sounds, light/IR switches, boards, stream stalls, alerts) and the
   geometric solar elevation at a reference point (the current #1 hotspot) with sunrise/sunset and
   civil/nautical twilight crossings, so a dusk IR switch or luma drop can be compared with the sun
   at a glance.
5. Map (``/api/hotspots``, ``/api/layers``, ``/api/engine/history``, ``/output/map.html``).
6. Calibration (``/api/calibration``): stream latency, audio offset, camera model (config, priors,
   astro-solver fit and its implied attitude at the reference point) plus the timing evidence rows.

Design and assumptions
----------------------
* Read-mostly. The runner is another process writing the SQLite "data table" in WAL mode; the
  dashboard opens one short-lived connection per request (cheap, and WAL readers never block the
  writer). The only writes are event status (ack), manual calibration overrides (allow-listed,
  range-checked, and audited as an already-acknowledged ``calibration_manual`` event) and the ntfy
  cursor (calibration key ``dashboard_state:ntfy_cursor``).
* Live updates. There is no cross-process notification from the runner, so ``/api/stream`` *polls*
  the integer primary keys (``id > cursor``) every ``poll_s`` (default 1 s): the cost is O(new rows),
  independent of table size. The SSE ``id:`` field carries both cursors (``o<obs>.e<event>``); a
  browser that reconnects (EventSource does this by itself and sends ``Last-Event-ID``) resumes with
  no gaps or duplicates. Event status changes made through this process are broadcast over an
  in-process bus (single uvicorn worker assumed).
* Time. Every stored timestamp is UTC ISO-8601 (CONTRACT.md). ``Observation.ts`` is the *estimated
  on-site* time (capture time - latency). The API returns ISO UTC plus ``ts_oslo`` (Europe/Oslo,
  DST-aware; fixed UTC+2 if tzdata is missing). ``delay_s`` = ts_capture - ts is the latency the
  analyzer assumed. Relative filters (``since=6h``) are relative to *now*, the timeline default window
  ends at the newest observation (so replays of old recordings also show up).
* Frames. The ingest archives every n-th frame and forced frames as JPEG. Forced frames are archived
  *after* their DB row was inserted, so ``frames.path`` can be NULL for a frame whose file exists; the
  dashboard falls back to the archive naming convention ``archive_dir/YYYYMMDD/HHMMSS_<idx>.jpg``
  (UTC of the frame's real_ts). Only image/audio files inside allowed roots (archive dir, repo data
  dir, DB dir) are served, so a tampered DB row cannot expose arbitrary files.

Failure modes
-------------
* A DB that the runner has not created yet is created empty (schema only) - the page simply shows
  no data. SQLite "database is locked" under heavy writes is retried by the 10 s busy timeout.
* Missing output files (no engine run yet), missing layers dir, missing cv2 (crops fall back to the
  full frame), missing pyproj (only Google links) and missing Leaflet (offline browser) all degrade
  to "not available" instead of errors.
* The solar elevation is a low-precision analytic ephemeris (NOAA / Meeus, ~0.01 deg, geometric, no
  refraction) at a *reference* point - a visual aid, not an astrometric solution (hordewatch.astro
  does that).
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import re
import sqlite3
import threading
import time
from collections import deque
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from starlette.concurrency import run_in_threadpool

from .. import ROOT
from ..db import DB
from ..types import KINDS, UTC, iso, parse_iso, utcnow

log = logging.getLogger("hordewatch.dashboard")

try:
    from zoneinfo import ZoneInfo

    OSLO = ZoneInfo("Europe/Oslo")
except Exception:  # pragma: no cover - tzdata missing: CEST is right for the whole hunt
    OSLO = timezone(timedelta(hours=2), "CEST")

STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_OUTPUT = ROOT / "output"
DEFAULT_ARCHIVE = ROOT / "data" / "hordewatch" / "archive"
DEFAULT_LAYERS = ROOT / "data" / "hordewatch" / "layers"
DEFAULT_SUN_REF = (61.245, 10.87)          # #1 hotspot of the 25.09 engine run; replaced by the live #1
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_EXT = {".wav", ".flac", ".ogg", ".mp3", ".opus"}
OUTPUT_FILE_RE = re.compile(r"^[A-Za-z0-9_.-]+\.(html|json|csv|png|jpg|jpeg|svg|geojson|txt)$")
EVENT_STATUSES = ("new", "ack", "dismissed")

# Priors about the camera that are *not* calibrations of this system (shown for comparison).
CAMERA_PRIORS = {
    "heading_deg": 219.6, "pitch_deg": 0.0, "focal_px": 1068.0,
    "source": "default.no sun-track fit (focal for their frame size)",
    "box_bearing_from_camera_deg": 221.0,
    "note": "whiteboard «KAMERA 41 ØST»: the camera stands ~41° (NE) of the box, so it looks ~221° "
            "towards her - consistent with the fitted 219.6° heading",
}

# Manual calibration overrides accepted by POST /api/calibration: key -> (min, max).
CAL_NUMERIC = {"latency_s": (0.0, 900.0), "latency_sigma_s": (0.1, 900.0), "audio_offset_s": (-900.0, 900.0)}
CAL_ATTITUDE = {"heading_deg": (0.0, 360.0), "pitch_deg": (-60.0, 60.0), "roll_deg": (-30.0, 30.0),
                "heading_sigma_deg": (0.01, 180.0), "pitch_sigma_deg": (0.01, 45.0), "roll_sigma_deg": (0.01, 45.0)}

# Timeline: continuous series (key, label, kind, SQL expression on `value`, python fallback, aggregate, lane)
SERIES = [
    ("sky_luma", "Sky luma", "sky_photometry", "json_extract(value,'$.luma')", lambda v: v.get("luma"), "mean", "luma"),
    ("scene_luma", "Scene luma", "scene_photometry", "json_extract(value,'$.luma')", lambda v: v.get("luma"), "mean", "luma"),
    ("cloud_fraction", "Cloud fraction", "cloud_fraction", "json_extract(value,'$.fraction')",
     lambda v: v.get("fraction"), "mean", "wx"),
    ("rain_visual", "Rain (visual)", "rain_visual",
     "COALESCE(json_extract(value,'$.intensity'), CASE WHEN json_extract(value,'$.present') THEN 1.0 ELSE 0.0 END)",
     lambda v: v.get("intensity") if v.get("intensity") is not None else (1.0 if v.get("present") else 0.0), "max", "wx"),
    ("audio_rain", "Rain (audio)", "audio_rain", "json_extract(value,'$.intensity')", lambda v: v.get("intensity"), "max", "wx"),
    ("wind_db", "Wind noise (dB)", "audio_wind", "json_extract(value,'$.level_db')", lambda v: v.get("level_db"), "mean", None),
    ("sunlit_fraction", "Sunlit fraction", "direct_sun", "json_extract(value,'$.sunlit_fraction')",
     lambda v: v.get("sunlit_fraction"), "mean", None),
]
# Timeline: discrete event swim-lanes (key, label, kinds)
EVENT_LANES = [
    ("aircraft", "Aircraft cues", ["gesture_point_up", "audio_aircraft", "aircraft_light", "aircraft_match"]),
    ("sounds", "Sounds", ["audio_vehicle", "audio_train", "audio_gunshot", "audio_chainsaw", "audio_bells",
                          "audio_voice", "audio_loop"]),
    ("light", "Light / IR", ["ir_mode_switch", "twilight_marker", "night_light_event"]),
    ("board", "Whiteboard", ["whiteboard_text", "clock_seen"]),
    ("stream", "Stream", ["stream_stall"]),
]
SUN_THRESHOLDS = [(-0.833, "sunrise", "sunset"), (-6.0, "civil dawn", "civil dusk"),
                  (-12.0, "nautical dawn", "nautical dusk")]
NICE_BUCKETS = [5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600, 7200, 10800, 21600]


# =============================================================================== small helpers
def to_oslo(ts: Optional[str]) -> Optional[str]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts).astimezone(OSLO).isoformat(timespec="seconds")
    except (TypeError, ValueError):
        return None


def unix_of(ts: str) -> float:
    return parse_iso(ts).timestamp()


_REL = re.compile(r"^\s*-?(\d+(?:\.\d+)?)\s*([smhd])\s*$", re.I)


def parse_time_param(s: Optional[str], now: Optional[datetime] = None) -> Optional[str]:
    """``None``/'' -> None; '6h' / '30m' / '2d' / '90s' -> now minus that; ISO (naive = UTC) -> ISO UTC.

    Returned in the DB's own ISO format so that string comparison in SQL is chronological.
    Raises ValueError on garbage (the route turns it into HTTP 400)."""
    if s is None or not str(s).strip():
        return None
    s = str(s).strip()
    m = _REL.match(s)
    if m:
        mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}[m.group(2).lower()]
        return iso((now or utcnow()) - timedelta(seconds=float(m.group(1)) * mult))
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    d = datetime.fromisoformat(s)
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return iso(d)


def _loads(s):
    if s is None:
        return None
    try:
        return json.loads(s)
    except (TypeError, ValueError):
        return s


def _num(x, nd=2, unit=""):
    if x is None:
        return "–"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, int):
        return f"{x}{unit}"
    try:
        f = float(x)
    except (TypeError, ValueError):
        return str(x)[:40]
    if not math.isfinite(f):
        return "–"
    return f"{f:.{nd}f}{unit}"


def _txt(x, n=160):
    s = " / ".join(l.strip() for l in str(x or "").splitlines() if l.strip())
    return s if len(s) <= n else s[: n - 1] + "…"


def compact(v, max_list=12, max_str=1500, depth=0):
    """Truncate long lists/strings (star lists, segments, tracks) for list views. Returns (value, truncated)."""
    if depth > 6:
        return "…", True
    if isinstance(v, dict):
        out, tr = {}, False
        for k, x in v.items():
            out[k], t = compact(x, max_list, max_str, depth + 1)
            tr |= t
        return out, tr
    if isinstance(v, list):
        items, tr = [], len(v) > max_list
        for x in v[:max_list]:
            c, t = compact(x, max_list, max_str, depth + 1)
            items.append(c)
            tr |= t
        if len(v) > max_list:
            items.append(f"… ({len(v)} items)")
        return items, tr
    if isinstance(v, str) and len(v) > max_str:
        return v[:max_str] + "…", True
    return v, False


def _generic_summary(v) -> str:
    if not isinstance(v, dict):
        return _txt(v, 120)
    parts = []
    for k, x in v.items():
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            parts.append(f"{k}={_num(x, 3) if isinstance(x, float) else x}")
        elif isinstance(x, (str, bool)) or x is None:
            if x is None:
                continue
            parts.append(f"{k}={_txt(x, 40) if isinstance(x, str) else _num(x)}")
        elif isinstance(x, list):
            parts.append(f"{k}=[{len(x)}]")
        if len(parts) >= 5:
            break
    return ", ".join(parts)


def _wb(v):
    tag = "NEW " if v.get("is_new") is True else ("repeat " if v.get("is_new") is False else "")
    src = " (VLM)" if v.get("source") == "vlm" else ""
    return f"{tag}«{_txt(v.get('text'), 150)}»{src}"


_SUMMARY = {
    "whiteboard_text": _wb,
    "whiteboard_visible": lambda v: f"board at {v.get('bbox')}",
    "vlm_description": lambda v: _txt(v.get("text"), 160),
    "scene_change": lambda v: f"score {_num(v.get('score'))}, {len(v.get('bbox_list') or [])} regions",
    "object_appeared": lambda v: f"{v.get('label')} {'appeared' if v.get('appeared', True) else 'removed'}",
    "gesture_point_up": lambda v: f"arm {_num(v.get('arm_angle_deg_from_vertical'), 0, '°')} from vertical, {v.get('side') or '?'} side",
    "person_count": lambda v: f"{v.get('n')} person(s)",
    "ir_mode_switch": lambda v: ("→ IR / night" if v.get("to_ir") else "→ day / colour") + f" ({v.get('from')}→{v.get('to')})",
    "sky_photometry": lambda v: f"luma {_num(v.get('luma'), 1)} · CCT {_num(v.get('cct_k'), 0, ' K')} · sat {_num(v.get('sat'))}",
    "scene_photometry": lambda v: f"luma {_num(v.get('luma'), 1)}" + (" · IR" if v.get("ir_mode") else ""),
    "cloud_fraction": lambda v: f"{_num(100 * float(v['fraction']), 0, ' %') if v.get('fraction') is not None else '–'} cloud ({v.get('method') or '?'})",
    "direct_sun": lambda v: f"sun {'on' if v.get('present') else 'off'} · sunlit {_num(v.get('sunlit_fraction'))}",
    "sun_pixel": lambda v: f"sun at ({_num(v.get('x'), 0)}, {_num(v.get('y'), 0)}) r {_num(v.get('radius'), 0)}" + (" saturated" if v.get("saturated") else ""),
    "shadow_direction": lambda v: f"shadow {_num(v.get('angle_deg_image'), 1, '°')} (strength {_num(v.get('strength'))})",
    "rain_visual": lambda v: f"rain {'yes' if v.get('present') else 'no'} · intensity {_num(v.get('intensity'))}",
    "condensation": lambda v: f"condensation {'yes' if v.get('present') else 'no'} · {_num(v.get('fraction'))}",
    "fog": lambda v: f"fog {'yes' if v.get('present') else 'no'} · contrast drop {_num(v.get('contrast_drop'))}",
    "temperature": lambda v: f"{_num(v.get('temp_c'), 1, ' °C')} {v.get('where') or ''} ({v.get('source') or '?'})",
    "night_light_event": lambda v: f"light Δluma {_num(v.get('luma_delta'), 1)} {v.get('colour') or ''}",
    "aircraft_light": lambda v: f"moving light, {len(v.get('track') or [])} pts, blink {_num(v.get('blink_hz'), 2, ' Hz')}",
    "star_field": lambda v: f"{v.get('n_stars')} star-like points",
    "moon_pixel": lambda v: f"moon at ({_num(v.get('x'), 0)}, {_num(v.get('y'), 0)}) illum {_num(v.get('illum'))}",
    "plate_solution": lambda v: f"RA {_num(v.get('ra_deg'), 2)} Dec {_num(v.get('dec_deg'), 2)} · {_num(v.get('scale_arcsec_px'), 1)}\"/px",
    "audio_aircraft": lambda v: f"aircraft noise SNR {_num(v.get('snr_db'), 1, ' dB')} · {_num(v.get('duration_s'), 0, ' s')}"
                                + (f" · {v.get('doppler_hint')}" if v.get("doppler_hint") else ""),
    "audio_rain": lambda v: f"rain sound intensity {_num(v.get('intensity'))}",
    "audio_wind": lambda v: f"wind {_num(v.get('level_db'), 1, ' dB')}",
    "audio_vehicle": lambda v: f"vehicle SNR {_num(v.get('snr_db'), 1, ' dB')}",
    "audio_train": lambda v: f"train SNR {_num(v.get('snr_db'), 1, ' dB')}",
    "audio_gunshot": lambda v: f"impulse peak {_num(v.get('peak_db'), 1, ' dB')}",
    "audio_chainsaw": lambda v: f"chainsaw/machine SNR {_num(v.get('snr_db'), 1, ' dB')}",
    "audio_bird": lambda v: f"{v.get('species') or 'bird'} ({_num(v.get('conf'))})",
    "audio_voice": lambda v: f"speech SNR {_num(v.get('snr_db'), 1, ' dB')} {v.get('speaker_hint') or ''}",
    "audio_bells": lambda v: f"bells SNR {_num(v.get('snr_db'), 1, ' dB')}",
    "audio_loop": lambda v: f"repeat of {v.get('ref_ts')} (lag {_num(v.get('lag_s'), 0, ' s')}, r={_num(v.get('corr'))})",
    "av_offset": lambda v: f"A/V offset {_num(v.get('offset_s'), 2, ' s')} ({v.get('method') or '?'})",
    "stream_health": lambda v: f"{_num(v.get('bitrate_kbps'), 0, ' kbit/s')} · {_num(v.get('fps'), 1, ' fps')} · "
                               f"dropped {v.get('dropped', '–')} · stall {_num(v.get('stall_s'), 1, ' s')} · {v.get('resolution') or ''}",
    "stream_latency": lambda v: f"latency {_num(v.get('latency_s'), 1, ' s')} ({v.get('method') or '?'})",
    "stream_stall": lambda v: f"{v.get('kind') or 'stall'} {_num(v.get('duration_s'), 1, ' s')}",
    "uplink_signature": lambda v: f"{v.get('verdict')} ({v.get('n_events')} stalls, p={_num(v.get('rayleigh_p'), 3)})",
    "clock_seen": lambda v: f"clock {v.get('shown_time')} · capture−shown {_num(v.get('capture_minus_shown_s'), 0, ' s')}",
    "aircraft_match": lambda v: f"{v.get('callsign') or v.get('icao') or '?'} {_num(v.get('alt_ft'), 0, ' ft')} · "
                                f"elev {_num(v.get('elev_deg'), 1, '°')} · az {_num(v.get('az_deg'), 0, '°')}",
    "weather_match": lambda v: f"{v.get('product')} · {v.get('cells')} cells",
    "astro_fix": lambda v: f"{v.get('method')}: {_num(v.get('lat'), 3)} N {_num(v.get('lon'), 3)} E ±{_num(v.get('sigma_km'), 0, ' km')}",
    "twilight_marker": lambda v: f"{v.get('event')} · {v.get('series')} @ {_num(v.get('threshold'), 1)} ({v.get('method') or '?'})",
    "camera_vertical": lambda v: f"{len(v.get('segments') or [])} vertical segments ({v.get('kind')})",
}


def summarize_value(kind: str, value: Any) -> str:
    """One-line human summary of an observation value (kind-specific, generic fallback, never raises)."""
    try:
        if isinstance(value, dict) and kind in _SUMMARY:
            return _SUMMARY[kind](value)
    except Exception:
        pass
    try:
        return _generic_summary(value)
    except Exception:  # pragma: no cover
        return ""


def map_links(lat: float, lon: float):
    """(norgeskart, google) URLs. Norgeskart takes EPSG:25833 northing/easting in its lat/lon parameters
    (same as hordejakt.cli.map_links; replicated so the dashboard never imports the engine)."""
    gm = f"https://www.google.com/maps/search/?api=1&query={lat:.5f},{lon:.5f}"
    try:
        tr = _utm33()
        e, n = tr.transform(lon, lat)
        nk = (f"https://norgeskart.no/#!?project=norgeskart&layers=1002&zoom=14&lat={n:.0f}&lon={e:.0f}"
              f"&markerLat={n:.0f}&markerLon={e:.0f}")
    except Exception:
        nk = None
    return nk, gm


_TR = None


def _utm33():
    global _TR
    if _TR is None:
        from pyproj import Transformer
        _TR = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True)
    return _TR


# =============================================================================== sun
def sun_position(unix_s, lat_deg: float, lon_deg: float):
    """Geometric solar elevation and azimuth (deg, azimuth from north through east).

    NOAA / Meeus (Astronomical Algorithms ch. 25) low-precision series: mean longitude and anomaly,
    equation of centre, nutation-in-longitude and aberration (the -0.00569 - 0.00478 sin(Omega)
    term), true obliquity, then the hour angle from GMST (GMST vs GAST differs by < 1.2 s = 0.005 deg).
    Accuracy ~0.01 deg for 1950-2050, no refraction (add ~0.5 deg near the horizon for the apparent
    sun). Vectorised over time."""
    t = np.asarray(unix_s, float)
    jd = t / 86400.0 + 2440587.5
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360.0
    M = np.radians(357.52911 + T * (35999.05029 - 0.0001537 * T))
    C = (np.sin(M) * (1.914602 - T * (0.004817 + 0.000014 * T)) + np.sin(2 * M) * (0.019993 - 0.000101 * T)
         + np.sin(3 * M) * 0.000289)
    om = np.radians(125.04 - 1934.136 * T)
    lam = np.radians(L0 + C - 0.00569 - 0.00478 * np.sin(om))
    eps0 = 23.0 + (26.0 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60.0) / 60.0
    eps = np.radians(eps0 + 0.00256 * np.cos(om))
    dec = np.arcsin(np.sin(eps) * np.sin(lam))
    ra = np.arctan2(np.cos(eps) * np.sin(lam), np.cos(lam))
    gmst = np.radians((280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T * T
                       - T ** 3 / 38710000.0) % 360.0)
    H = gmst + np.radians(lon_deg) - ra
    phi = np.radians(lat_deg)
    s_alt = np.sin(phi) * np.sin(dec) + np.cos(phi) * np.cos(dec) * np.cos(H)
    alt = np.degrees(np.arcsin(np.clip(s_alt, -1.0, 1.0)))
    az = np.degrees(np.arctan2(-np.cos(dec) * np.sin(H), np.sin(dec) * np.cos(phi) - np.cos(dec) * np.sin(phi) * np.cos(H)))
    return alt, az % 360.0


def sun_crossings(t0: float, t1: float, lat: float, lon: float, step_s: float = 60.0):
    """Times the sun crosses the sunrise/sunset (-0.833 deg: refraction + semi-diameter), civil (-6)
    and nautical (-12) thresholds in [t0, t1], linearly interpolated on a 1-min grid (error < 1 s)."""
    if t1 <= t0:
        return []
    n = int(min(20000, max(2, (t1 - t0) / step_s + 1)))
    ts = np.linspace(t0, t1, n)
    alt, _ = sun_position(ts, lat, lon)
    out = []
    for h0, rising, setting in SUN_THRESHOLDS:
        d = alt - h0
        idx = np.nonzero(np.sign(d[:-1]) * np.sign(d[1:]) < 0)[0]
        for i in idx:
            f = d[i] / (d[i] - d[i + 1])
            t = ts[i] + f * (ts[i + 1] - ts[i])
            out.append({"t": int(round(t * 1000)), "event": rising if d[i + 1] > d[i] else setting, "elev_deg": h0})
    return sorted(out, key=lambda e: e["t"])


def _nice_bucket(span_s: float, target: int = 1200) -> float:
    raw = max(span_s / max(target, 1), 1.0)
    for b in NICE_BUCKETS:
        if b >= raw:
            return float(b)
    return float(NICE_BUCKETS[-1])


def _bucketize(t: np.ndarray, v: np.ndarray, t0: float, bucket_s: float, agg: str):
    ok = np.isfinite(t) & np.isfinite(v)
    t, v = t[ok], v[ok]
    if t.size == 0:
        return []
    b = np.floor((t - t0) / bucket_s).astype(np.int64)
    b -= b.min() if b.min() < 0 else 0
    nb = int(b.max()) + 1
    cnt = np.bincount(b, minlength=nb)
    if agg == "max":
        val = np.full(nb, -np.inf)
        np.maximum.at(val, b, v)
    else:
        val = np.bincount(b, weights=v, minlength=nb) / np.maximum(cnt, 1)
    keep = np.nonzero(cnt > 0)[0]
    base = t0 + (np.floor((t.min() - t0) / bucket_s) if t.min() < t0 else 0) * bucket_s
    return [[int(round((base + (k + 0.5) * bucket_s) * 1000)), round(float(val[k]), 4), int(cnt[k])] for k in keep]


# =============================================================================== in-process bus
class Bus:
    """Tiny broadcast log for changes made *by this process* (event acks, manual calibration)."""

    def __init__(self, maxlen=2000):
        self._lock = threading.Lock()
        self._items = deque(maxlen=maxlen)
        self.seq = 0

    def publish(self, name: str, data: dict):
        with self._lock:
            self.seq += 1
            self._items.append((self.seq, name, data))

    def since(self, seq: int):
        with self._lock:
            return [it for it in self._items if it[0] > seq]


# =============================================================================== data access
class Store:
    """All DB / file access of the dashboard (sync; FastAPI runs sync routes in a threadpool)."""

    def __init__(self, db_path, output_dir=None, archive_dir=None, layers_dir=None, config=None):
        self.config = config or {}
        self.db_path = str(Path(db_path).expanduser())
        self.db = DB(self.db_path)                    # creates schema/WAL if the runner has not yet
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT
        dash = self.config.get("dashboard") or {}
        if archive_dir is None:
            if self.config.get("archive_dir"):
                archive_dir = _resolve(self.config["archive_dir"])
            elif (Path(self.db_path).parent / "archive").exists():
                archive_dir = Path(self.db_path).parent / "archive"
            else:
                archive_dir = DEFAULT_ARCHIVE
        self.archive_dir = Path(archive_dir)
        self.layers_dir = Path(layers_dir) if layers_dir else _resolve(
            (self.config.get("bridges") or {}).get("layers_dir") or DEFAULT_LAYERS)
        self.allowed_roots = [p.resolve() for p in
                              [self.archive_dir, ROOT / "data", Path(self.db_path).parent,
                               *[_resolve(x) for x in dash.get("media_roots", [])]]]
        self.sun_ref_cfg = dash.get("sun_ref")
        self.bus = Bus()
        self._frame_samples = deque(maxlen=400)
        self._layer_cache: dict = {}
        self._kinds_cache = (0.0, None)
        self.sse_clients = 0
        try:
            with self.connect() as con:
                con.execute("SELECT json_extract('{\"a\":1}', '$.a')").fetchone()
            self.json1 = True
        except sqlite3.Error:  # pragma: no cover
            self.json1 = False

    # ------------------------------------------------------------------ plumbing
    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.db_path, timeout=10.0)
        con.row_factory = sqlite3.Row
        try:
            yield con
        finally:
            con.close()

    def _write(self, sql, args=()):
        with self.db._lock:
            cur = self.db.con.execute(sql, args)
            self.db.con.commit()
            return cur

    # ------------------------------------------------------------------ media files
    def _allowed(self, p: Path, exts) -> bool:
        try:
            rp = p.resolve()
        except OSError:
            return False
        if rp.suffix.lower() not in exts or not rp.is_file():
            return False
        return any(rp == r or r in rp.parents for r in self.allowed_roots)

    def media_file(self, path: Optional[str], exts=IMG_EXT) -> Optional[Path]:
        if not path:
            return None
        p = Path(path)
        for c in ([p] if p.is_absolute() else [ROOT / p, Path.cwd() / p, Path(self.db_path).parent / p]):
            if self._allowed(c, exts):
                return c.resolve()
        return None

    def frame_file(self, path, idx, real_ts) -> Optional[Path]:
        f = self.media_file(path)
        if f is not None:
            return f
        if real_ts and idx is not None:           # retroactively archived frame: path not in DB
            try:
                t = parse_iso(real_ts)
            except ValueError:
                return None
            c = self.archive_dir / t.strftime("%Y%m%d") / f"{t:%H%M%S}_{idx}.jpg"
            if self._allowed(c, IMG_EXT):
                return c.resolve()
        return None

    def frame_row(self, con, frame_id):
        return con.execute("SELECT id, idx, capture_ts, real_ts, source, path, w, h FROM frames WHERE id=?",
                           (frame_id,)).fetchone()

    def frame_by_id(self, frame_id):
        with self.connect() as con:
            r = self.frame_row(con, frame_id)
        if r is None:
            return None, None
        return r, self.frame_file(r["path"], r["idx"], r["real_ts"])

    def nearest_frame(self, ts: str, max_s: float = 120.0):
        """Nearest *archived* frame to ``ts`` (real time) within +-max_s: (row, file) or (None, None)."""
        t = parse_iso(ts)
        lo, hi = iso(t - timedelta(seconds=max_s)), iso(t + timedelta(seconds=max_s))
        with self.connect() as con:
            rows = con.execute("SELECT id, idx, capture_ts, real_ts, source, path, w, h FROM frames "
                               "WHERE real_ts BETWEEN ? AND ? LIMIT 2000", (lo, hi)).fetchall()
        rows = sorted(rows, key=lambda r: (r["path"] is None, abs(unix_of(r["real_ts"]) - t.timestamp())))
        best = None
        for r in rows:
            f = self.frame_file(r["path"], r["idx"], r["real_ts"])
            if f is not None:
                d = abs(unix_of(r["real_ts"]) - t.timestamp())
                if best is None or d < best[0]:
                    best = (d, r, f)
        return (best[1], best[2]) if best else (None, None)

    def latest_frame(self):
        with self.connect() as con:
            rows = con.execute("SELECT id, idx, capture_ts, real_ts, source, path, w, h FROM frames "
                               "ORDER BY id DESC LIMIT 60").fetchall()
        if not rows:
            return None
        newest = rows[0]
        img = None
        for r in rows:
            f = self.frame_file(r["path"], r["idx"], r["real_ts"])
            if f is not None:
                img = r
                break
        out = {"id": newest["id"], "real_ts": newest["real_ts"], "real_ts_oslo": to_oslo(newest["real_ts"]),
               "capture_ts": newest["capture_ts"], "source": newest["source"], "w": newest["w"], "h": newest["h"],
               "latency_applied_s": _delta(newest["capture_ts"], newest["real_ts"]), "image": None}
        if img is not None:
            out["image"] = {"id": img["id"], "real_ts": img["real_ts"], "real_ts_oslo": to_oslo(img["real_ts"]),
                            "url": f"api/frames/{img['id']}/image"}
        return out

    # ------------------------------------------------------------------ observations
    OBS_SQL = ("SELECT o.id, o.ts, o.ts_capture, o.kind, o.analyzer, o.confidence, o.value, o.frame_id, o.audio_id, "
               "o.notes, o.created, f.path AS f_path, f.idx AS f_idx, f.real_ts AS f_real_ts, a.path AS a_path "
               "FROM observations o LEFT JOIN frames f ON f.id = o.frame_id LEFT JOIN audio a ON a.id = o.audio_id")

    def obs_dict(self, r, full=False) -> dict:
        value = _loads(r["value"])
        v_out, trunc = (value, False) if full else compact(value)
        frame_url = None
        if r["frame_id"] is not None and self.frame_file(r["f_path"], r["f_idx"], r["f_real_ts"]) is not None:
            frame_url = f"api/frames/{r['frame_id']}/image"
        audio_url = None
        if r["audio_id"] is not None and self.media_file(r["a_path"], AUDIO_EXT) is not None:
            audio_url = f"api/audio/{r['audio_id']}"
        return {"id": r["id"], "ts": r["ts"], "ts_oslo": to_oslo(r["ts"]), "ts_capture": r["ts_capture"],
                "delay_s": _delta(r["ts_capture"], r["ts"]), "created": r["created"], "kind": r["kind"],
                "analyzer": r["analyzer"], "confidence": r["confidence"], "summary": summarize_value(r["kind"], value),
                "value": v_out, "value_truncated": trunc, "frame_id": r["frame_id"], "audio_id": r["audio_id"],
                "notes": r["notes"], "frame_url": frame_url, "audio_url": audio_url,
                "near_frame_url": None if frame_url else f"api/frames/near?ts={r['ts']}"}

    def observations(self, kinds=None, analyzer=None, min_conf=None, since=None, until=None, q=None,
                     limit=100, order="id", before_id=None, before_ts=None):
        where, args = [], []
        if kinds:
            where.append("o.kind IN (%s)" % ",".join("?" * len(kinds)))
            args += list(kinds)
        if analyzer:
            where.append("o.analyzer = ?")
            args.append(analyzer)
        if min_conf is not None and min_conf > 0:
            where.append("o.confidence >= ?")
            args.append(float(min_conf))
        if since:
            where.append("o.ts >= ?")
            args.append(since)
        if until:
            where.append("o.ts <= ?")
            args.append(until)
        if q:
            where.append("(o.value LIKE ? OR o.notes LIKE ? OR o.kind LIKE ? OR o.analyzer LIKE ?)")
            args += [f"%{q}%"] * 4
        if order == "ts":
            if before_ts:
                where.append("(o.ts < ? OR (o.ts = ? AND o.id < ?))")
                args += [before_ts, before_ts, int(before_id if before_id is not None else 2 ** 62)]
            ob = "o.ts DESC, o.id DESC"
        else:
            if before_id is not None:
                where.append("o.id < ?")
                args.append(int(before_id))
            ob = "o.id DESC"
        sql = self.OBS_SQL + (" WHERE " + " AND ".join(where) if where else "") + f" ORDER BY {ob} LIMIT ?"
        args.append(int(limit) + 1)
        with self.connect() as con:
            rows = con.execute(sql, args).fetchall()
        more = len(rows) > limit
        rows = rows[:limit]
        out = [self.obs_dict(r) for r in rows]
        nxt = None
        if more and out:
            nxt = {"before_id": out[-1]["id"]} if order != "ts" else {"before_ts": out[-1]["ts"], "before_id": out[-1]["id"]}
        return {"rows": out, "next": nxt}

    def observation(self, obs_id):
        with self.connect() as con:
            r = con.execute(self.OBS_SQL + " WHERE o.id = ?", (obs_id,)).fetchone()
        return self.obs_dict(r, full=True) if r else None

    def kinds(self):
        now = time.monotonic()
        if self._kinds_cache[1] is not None and now - self._kinds_cache[0] < 5.0:
            return self._kinds_cache[1]
        with self.connect() as con:
            rows = con.execute("SELECT kind, COUNT(*) AS n, MAX(ts) AS last_ts, MAX(created) AS last_created "
                               "FROM observations GROUP BY kind").fetchall()
            an = con.execute("SELECT analyzer, COUNT(*) AS n, MAX(created) AS last_created FROM observations "
                             "GROUP BY analyzer ORDER BY analyzer").fetchall()
        seen = {r["kind"]: r for r in rows}
        kinds = []
        for k, desc in KINDS.items():
            r = seen.get(k)
            kinds.append({"kind": k, "description": desc, "n": r["n"] if r else 0,
                          "last_ts": r["last_ts"] if r else None, "last_created": r["last_created"] if r else None})
        for k, r in seen.items():
            if k not in KINDS:
                kinds.append({"kind": k, "description": "(not in types.KINDS)", "n": r["n"], "last_ts": r["last_ts"],
                              "last_created": r["last_created"]})
        res = {"kinds": kinds, "analyzers": [{"analyzer": r["analyzer"], "n": r["n"], "last_created": r["last_created"]}
                                             for r in an]}
        self._kinds_cache = (now, res)
        return res

    # ------------------------------------------------------------------ events
    @staticmethod
    def event_dict(r) -> dict:
        return {"id": r["id"], "ts": r["ts"], "ts_oslo": to_oslo(r["ts"]), "kind": r["kind"], "summary": r["summary"],
                "value": _loads(r["value"]), "status": r["status"] or "new", "created": r["created"]}

    def events(self, status=None, kind=None, limit=100, before_id=None):
        where, args = [], []
        if status and status != "all":
            where.append("COALESCE(status,'new') = ?")
            args.append(status)
        if kind:
            where.append("kind = ?")
            args.append(kind)
        if before_id is not None:
            where.append("id < ?")
            args.append(int(before_id))
        sql = "SELECT * FROM events" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY id DESC LIMIT ?"
        with self.connect() as con:
            rows = con.execute(sql, args + [int(limit)]).fetchall()
            counts = {r[0] or "new": r[1] for r in con.execute(
                "SELECT COALESCE(status,'new'), COUNT(*) FROM events GROUP BY COALESCE(status,'new')")}
        return {"rows": [self.event_dict(r) for r in rows], "counts": counts}

    def set_event_status(self, event_id: int, status: str):
        cur = self._write("UPDATE events SET status=? WHERE id=?", (status, int(event_id)))
        if cur.rowcount == 0:
            return None
        with self.connect() as con:
            r = con.execute("SELECT * FROM events WHERE id=?", (int(event_id),)).fetchone()
        d = self.event_dict(r)
        self.bus.publish("event_update", {"id": d["id"], "status": d["status"]})
        return d

    def ack_all(self, up_to_id=None, kind=None):
        where, args = ["COALESCE(status,'new') = 'new'"], []
        if up_to_id is not None:
            where.append("id <= ?")
            args.append(int(up_to_id))
        if kind:
            where.append("kind = ?")
            args.append(kind)
        with self.connect() as con:
            ids = [r[0] for r in con.execute("SELECT id FROM events WHERE " + " AND ".join(where), args)]
        if ids:
            self._write("UPDATE events SET status='ack' WHERE id IN (%s)" % ",".join("?" * len(ids)), ids)
            for i in ids:
                self.bus.publish("event_update", {"id": i, "status": "ack"})
        return ids

    # ------------------------------------------------------------------ whiteboard
    def whiteboard(self, limit=40, only_new=False):
        with self.connect() as con:
            rows = con.execute(self.OBS_SQL + " WHERE o.kind='whiteboard_text' ORDER BY o.ts DESC, o.id DESC LIMIT ?",
                               (int(limit) * 4,)).fetchall()
        groups: list = []
        by_obs: dict = {}
        for r in rows:
            v = _loads(r["value"]) or {}
            if not isinstance(v, dict):
                v = {"text": str(v)}
            t = unix_of(r["ts"])
            g = by_obs.get(v.get("revision_of"))
            if g is None:
                for h in groups:   # the later revision of an earlier emission links back via revision_of
                    if r["id"] in h["revision_links"]:
                        g = h
                        break
            tid = v.get("track_id")
            if g is None and tid is not None:
                for h in groups:
                    if h["track_id"] == tid and abs(h["t"] - t) <= 1200.0:
                        g = h
                        break
            if g is None:
                g = {"track_id": tid, "t": t, "members": [], "revision_links": set()}
                groups.append(g)
            g["members"].append((r, v))
            g["t"] = min(g["t"], t)
            if v.get("revision_of") is not None:
                g["revision_links"].add(v["revision_of"])
            by_obs[r["id"]] = g
        out = []
        for g in groups:
            card = self._wb_card(g)
            if only_new and card["is_new"] is False:
                continue
            out.append(card)
        out.sort(key=lambda c: c["ts"], reverse=True)
        return out[: int(limit)]

    def _wb_card(self, g) -> dict:
        ocr = [(r, v) for r, v in g["members"] if v.get("source") != "vlm" and r["analyzer"] != "vlm"]
        vlm = [(r, v) for r, v in g["members"] if (r, v) not in ocr]
        best_ocr = max(ocr, key=lambda rv: rv[0]["id"]) if ocr else None      # latest revision wins
        best_vlm = max(vlm, key=lambda rv: (rv[0]["confidence"] or 0, rv[0]["id"])) if vlm else None
        ref = best_ocr or best_vlm
        r0, v0 = ref
        news = [v.get("is_new") for _, v in g["members"] if v.get("is_new") is not None]
        is_new = (True if any(news) else False) if news else None
        ts = min(r["ts"] for r, _ in g["members"])
        img = self.whiteboard_image(r0["id"])
        card = {"id": r0["id"], "ts": ts, "ts_oslo": to_oslo(ts), "track_id": g["track_id"],
                "obs_ids": sorted(r["id"] for r, _ in g["members"]), "is_new": is_new,
                "repeat_of": next((v.get("repeat_of") for _, v in g["members"] if v.get("repeat_of")), None),
                "confidence": max((r["confidence"] or 0.0) for r, _ in g["members"]),
                "text": v0.get("text") or "", "first_seen_ts": v0.get("first_seen_ts"), "last_seen_ts": v0.get("last_seen_ts"),
                "bbox": v0.get("bbox"), "crop_url": f"api/whiteboard/{r0['id']}/crop.jpg" if img else None,
                "frame_url": f"api/frames/{img[1]['id']}/image" if img and img[1] is not None else None,
                "ocr": None, "vlm": None}
        if best_ocr:
            r, v = best_ocr
            card["ocr"] = {"obs_id": r["id"], "text": v.get("text") or "", "lines": v.get("lines"), "raw_text": v.get("raw_text"),
                           "ocr_conf": v.get("ocr_conf"), "confidence": r["confidence"], "n_reads": v.get("n_reads"),
                           "engines": v.get("engines"), "revision": bool(v.get("revision_of")), "ts": r["ts"]}
        if best_vlm:
            r, v = best_vlm
            card["vlm"] = {"obs_id": r["id"], "text": v.get("text") or "", "model": v.get("model"), "legible": v.get("legible"),
                           "confidence": r["confidence"], "drawings": v.get("drawings"), "ts": r["ts"]}
        return card

    def whiteboard_image(self, obs_id):
        """(file, frame_row, bbox) for a whiteboard_text observation: its own frame, the frame of the
        whiteboard_visible detection, else the archived frame nearest in time within the board hold."""
        with self.connect() as con:
            r = con.execute("SELECT id, ts, kind, value, frame_id FROM observations WHERE id=?", (obs_id,)).fetchone()
            if r is None:
                return None
            v = _loads(r["value"]) or {}
            if not isinstance(v, dict):
                v = {}
            cand = []
            if r["frame_id"] is not None:
                cand.append(r["frame_id"])
            if v.get("visible_obs_id"):
                vis = con.execute("SELECT frame_id FROM observations WHERE id=?", (v["visible_obs_id"],)).fetchone()
                if vis and vis[0] is not None:
                    cand.append(vis[0])
            rows = [self.frame_row(con, fid) for fid in cand]
            t0 = v.get("first_seen_ts") or r["ts"]
            t1 = v.get("last_seen_ts") or r["ts"]
            try:
                lo = iso(parse_iso(t0) - timedelta(seconds=5))
                hi = iso(parse_iso(t1) + timedelta(seconds=5))
                more = con.execute("SELECT id, idx, capture_ts, real_ts, source, path, w, h FROM frames "
                                   "WHERE real_ts BETWEEN ? AND ? LIMIT 400", (lo, hi)).fetchall()
                tt = unix_of(r["ts"])
                rows += sorted(more, key=lambda f: abs(unix_of(f["real_ts"]) - tt))
            except ValueError:
                pass
        for fr in rows:
            if fr is None:
                continue
            f = self.frame_file(fr["path"], fr["idx"], fr["real_ts"])
            if f is not None:
                return f, fr, v.get("bbox")
        return None

    # ------------------------------------------------------------------ timeline
    def data_range(self):
        with self.connect() as con:
            r = con.execute("SELECT MIN(ts), MAX(ts) FROM observations").fetchone()
        return r[0], r[1]

    def sun_ref(self):
        if self.sun_ref_cfg and len(self.sun_ref_cfg) == 2:
            return float(self.sun_ref_cfg[0]), float(self.sun_ref_cfg[1]), "config dashboard.sun_ref"
        for name in ("hotspots.json", "scenario_hotspots.json"):
            d = _read_json(self.output_dir / name)
            try:
                s = d["hotspots"][0]
                return float(s["lat"]), float(s["lon"]), f"#1 hotspot ({name})"
            except (TypeError, KeyError, IndexError, ValueError):
                continue
        return DEFAULT_SUN_REF[0], DEFAULT_SUN_REF[1], "default reference point"

    def _series(self, con, kind, expr, fn, lo, hi):
        if self.json1:
            try:
                rows = con.execute(f"SELECT ts, {expr} FROM observations WHERE kind=? AND ts BETWEEN ? AND ?",
                                   (kind, lo, hi)).fetchall()
                t = np.array([unix_of(a) for a, _ in rows], float)
                v = np.array([_float(b) for _, b in rows], float)
                return t, v
            except sqlite3.Error:
                pass
        rows = con.execute("SELECT ts, value FROM observations WHERE kind=? AND ts BETWEEN ? AND ?", (kind, lo, hi)).fetchall()
        t, v = [], []
        for a, b in rows:
            d = _loads(b)
            try:
                v.append(_float(fn(d)) if isinstance(d, dict) else np.nan)
            except Exception:
                v.append(np.nan)
            t.append(unix_of(a))
        return np.array(t, float), np.array(v, float)

    def timeline(self, since=None, until=None, bucket_s=None, sun_lat=None, sun_lon=None, max_markers=1500):
        dmin, dmax = self.data_range()
        now = utcnow()
        hi = until or dmax or iso(now)
        lo = since or iso(parse_iso(hi) - timedelta(hours=24))
        t0, t1 = unix_of(lo), unix_of(hi)
        if t1 <= t0:
            raise ValueError("until must be after since")
        span = t1 - t0
        b = float(bucket_s) if bucket_s else _nice_bucket(span)
        b = max(b, 1.0)
        series = {}
        with self.connect() as con:
            for key, label, kind, expr, fn, agg, lane in SERIES:
                t, v = self._series(con, kind, expr, fn, lo, hi)
                series[key] = {"label": label, "kind": kind, "agg": agg, "lane": lane, "n": int(np.isfinite(v).sum()),
                               "points": _bucketize(t, v, t0, b, agg)}
            lanes = []
            for key, label, kinds in EVENT_LANES:
                rows = con.execute("SELECT id, ts, kind, confidence, value FROM observations WHERE kind IN (%s) "
                                   "AND ts BETWEEN ? AND ? ORDER BY ts LIMIT 50000" % ",".join("?" * len(kinds)),
                                   (*kinds, lo, hi)).fetchall()
                marks = [{"t": int(round(unix_of(r["ts"]) * 1000)), "id": r["id"], "kind": r["kind"],
                          "conf": r["confidence"], "label": summarize_value(r["kind"], _loads(r["value"]))} for r in rows]
                lanes.append({"key": key, "label": label, "kinds": kinds, "n": len(marks),
                              "markers": _thin(marks, max_markers, span)})
            ev = con.execute("SELECT id, ts, kind, summary, status FROM events WHERE ts BETWEEN ? AND ? ORDER BY ts LIMIT 20000",
                             (lo, hi)).fetchall()
            lanes.append({"key": "alerts", "label": "Alerts", "kinds": ["events"], "n": len(ev),
                          "markers": _thin([{"t": int(round(unix_of(r["ts"]) * 1000)), "event_id": r["id"], "kind": r["kind"],
                                             "conf": 1.0, "label": r["summary"], "status": r["status"]} for r in ev],
                                           max_markers, span)})
        if sun_lat is None or sun_lon is None:
            sun_lat, sun_lon, ref_src = self.sun_ref()
        else:
            ref_src = "query"
        n = int(min(1500, max(50, span / 60.0 + 1)))
        ts = np.linspace(t0, t1, n)
        alt, az = sun_position(ts, sun_lat, sun_lon)
        sun = {"lat": sun_lat, "lon": sun_lon, "source": ref_src, "model": "NOAA/Meeus geometric (no refraction), ~0.01°",
               "points": [[int(round(a * 1000)), round(float(e), 3), round(float(z), 2)] for a, e, z in zip(ts, alt, az)],
               "crossings": sun_crossings(t0, t1, sun_lat, sun_lon)}
        return {"since": lo, "until": hi, "since_oslo": to_oslo(lo), "until_oslo": to_oslo(hi), "bucket_s": b,
                "data_min": dmin, "data_max": dmax, "series": series, "lanes": lanes, "sun": sun}

    # ------------------------------------------------------------------ engine outputs
    def hotspots(self, source="base", top=30):
        name = "scenario_hotspots.json" if source == "scenarios" else "hotspots.json"
        p = self.output_dir / name
        d = _read_json(p)
        if not isinstance(d, dict):
            return {"source": source, "file": name, "available": False, "hotspots": []}
        spots = []
        for k, s in enumerate((d.get("hotspots") or [])[: int(top)], 1):
            try:
                lat, lon = float(s["lat"]), float(s["lon"])
            except (KeyError, TypeError, ValueError):
                continue
            nk, gm = s.get("norgeskart"), s.get("google_maps")
            if not nk or not gm:
                nk2, gm2 = map_links(lat, lon)
                nk, gm = nk or nk2, gm or gm2
            groups = s.get("groups") or {}
            ranked = sorted(((g, float(x)) for g, x in groups.items() if isinstance(x, (int, float))), key=lambda gx: -gx[1])
            ratios = s.get("scenario_p_cell_ratio") or {}
            spots.append({"rank": k, "lat": round(lat, 5), "lon": round(lon, 5), "p_cell": s.get("p_cell"),
                          "p_within_1_5km": s.get("p_within_1.5km"), "fragility": s.get("fragility"),
                          "support": [{"group": g, "loglik": x} for g, x in ranked[:3] if x > 0],
                          "against": [{"group": g, "loglik": x} for g, x in ranked[::-1][:2] if x < 0],
                          "scenario_ratio": ratios, "norgeskart": nk, "google_maps": gm})
        summ = d.get("summary") or {}
        return {"source": source, "file": name, "available": True, "mtime": _mtime_iso(p), "mtime_oslo": to_oslo(_mtime_iso(p)),
                "credible_km2": summ.get("credible_km2") or d.get("credible_km2"), "scenarios": d.get("scenarios"),
                "layers": summ.get("layers"), "hotspots": spots,
                "map_url": (f"output/map.html?v={int((self.output_dir / 'map.html').stat().st_mtime)}"
                            if (self.output_dir / "map.html").is_file() else None)}

    def engine_history(self, limit=20):
        d = self.output_dir / "history"
        if not d.is_dir():
            return []
        out = []
        for p in sorted(d.glob("*_hotspots.json"), reverse=True)[: int(limit)]:
            rec = _read_json(p)
            if not isinstance(rec, dict):
                continue
            hs = rec.get("hotspots") or []
            top = hs[0] if hs else None
            out.append({"file": p.name, "ts": rec.get("ts"), "ts_oslo": to_oslo(rec.get("ts")), "material": rec.get("material"),
                        "changes": rec.get("changes"), "credible_km2": rec.get("credible_km2"),
                        "live_layers": rec.get("live_layers"),
                        "top": ({"lat": top.get("lat"), "lon": top.get("lon"), "p_within_1_5km": top.get("p_within_1.5km")}
                                if isinstance(top, dict) else None)})
        return out

    def layers(self):
        """Live evidence grids in the layers dir: metadata + where each one peaks (cached by mtime)."""
        if not self.layers_dir.is_dir():
            return []
        from hordejakt.grid import GRID
        out = []
        for p in sorted(self.layers_dir.glob("*.npz")):
            try:
                st = p.stat()
                key = (str(p), st.st_mtime, st.st_size)
                if key not in self._layer_cache:
                    self._layer_cache[key] = _layer_info(p, GRID)
                info = dict(self._layer_cache[key])
                info["mtime"] = datetime.fromtimestamp(st.st_mtime, UTC).isoformat(timespec="seconds")
                info["mtime_oslo"] = to_oslo(info["mtime"])
                out.append(info)
            except Exception as e:
                out.append({"file": p.name, "error": str(e)[:200]})
        return out

    # ------------------------------------------------------------------ calibration / status
    def calibration(self):
        with self.connect() as con:
            rows = con.execute("SELECT key, value, updated FROM calibration ORDER BY key").fetchall()
            ev = con.execute(self.OBS_SQL + " WHERE o.kind IN ('stream_latency','av_offset','clock_seen','uplink_signature') "
                                            "ORDER BY o.id DESC LIMIT 40").fetchall()
        cal = {r["key"]: {"value": _loads(r["value"]), "updated": r["updated"]} for r in rows}
        gcfg = self.config
        clock = gcfg.get("clock") or {}

        def val(k, default=None):
            return cal[k]["value"] if k in cal else default

        lc = val("latency_calibration")
        latency = {"latency_s": val("latency_s"), "latency_sigma_s": val("latency_sigma_s"),
                   "audio_offset_s": val("audio_offset_s"),
                   "updated": (cal.get("latency_s") or {}).get("updated"),
                   "audio_offset_updated": (cal.get("audio_offset_s") or {}).get("updated"),
                   "config_latency_s": clock.get("latency_s", 30.0), "config_latency_sigma_s": clock.get("latency_sigma_s", 15.0),
                   "method": (lc or {}).get("method") if isinstance(lc, dict) else None, "details": lc}
        lf = self.latest_frame()
        camera = {"config": gcfg.get("camera"), "prior": CAMERA_PRIORS, "camera_attitude": val("camera_attitude"),
                  "camera_moves": val("camera_moves"), "astro_camera": None}
        ac = val("astro_camera")
        if isinstance(ac, dict):
            camera["astro_camera"] = self._astro_camera_summary(ac, (lf or {}).get("w"))
        internal = [k for k in cal if k.startswith(("bridge_state:", "dashboard_state:"))]
        return {"latency": latency, "camera": camera, "latest_frame": lf,
                "evidence": [self.obs_dict(r) for r in ev],
                "rows": [{"key": k, "value": v["value"], "updated": v["updated"], "updated_oslo": to_oslo(v["updated"])}
                         for k, v in cal.items() if k not in internal],
                "internal_keys": internal,
                "writable": {"numeric": {k: list(v) for k, v in CAL_NUMERIC.items()},
                             "camera_attitude": {k: list(v) for k, v in CAL_ATTITUDE.items()}}}

    def _astro_camera_summary(self, ac, width):
        out = {k: ac.get(k) for k in ("method", "f", "rms_px", "n", "pose_segments", "updated")}
        f = _float(ac.get("f"))
        if math.isfinite(f) and f > 0:
            out["hfov_deg"] = round(math.degrees(2 * math.atan(0.5 / f)), 2)
            if width:
                out["focal_px"] = round(f * float(width), 1)
                out["focal_px_at_width"] = width
        try:
            G = np.array(ac["G"][-1], float)
            from ..astro.camera import attitude_from_rotation
            from ..astro.ephem import observer_frame
            lat, lon, src = self.sun_ref()
            _, T = observer_frame(lat, lon)
            h, p, r = attitude_from_rotation(G @ T.T)
            out["implied_attitude"] = {"heading_deg": round(float(h), 2), "pitch_deg": round(float(p), 2),
                                       "roll_deg": round(float(r), 2), "at": [lat, lon], "at_source": src,
                                       "note": "G = R_cam·T(lat,lon) fixes the camera only relative to the rotating "
                                               "Earth; this attitude is what G implies *if* the camera stood at the "
                                               "reference point"}
        except Exception:
            pass
        return out

    def set_calibration(self, key, value):
        old = self.db.calibration(key)
        self.db.set_calibration(key, value)
        now = utcnow()
        self._write("INSERT INTO events(ts, kind, summary, value, status, created) VALUES (?,?,?,?,?,?)",
                    (iso(now), "calibration_manual", f"manual calibration {key}: {json.dumps(old)} → {json.dumps(value)}",
                     json.dumps({"key": key, "old": old, "new": value}, ensure_ascii=False), "ack", iso(now)))
        self.bus.publish("calibration", {"key": key, "value": value})

    def status(self):
        now = utcnow()
        with self.connect() as con:
            n_obs = con.execute("SELECT MAX(id) FROM observations").fetchone()[0] or 0
            n_frames = con.execute("SELECT MAX(id) FROM frames").fetchone()[0] or 0
            n_audio = con.execute("SELECT MAX(id) FROM audio").fetchone()[0] or 0
            ev_new = con.execute("SELECT COUNT(*) FROM events WHERE COALESCE(status,'new')='new'").fetchone()[0]
            last_created = con.execute("SELECT created FROM observations ORDER BY id DESC LIMIT 1").fetchone()
            last = {}
            for k in ("stream_health", "uplink_signature", "stream_latency"):
                r = con.execute(self.OBS_SQL + " WHERE o.kind=? ORDER BY o.id DESC LIMIT 1", (k,)).fetchone()
                last[k] = self.obs_dict(r) if r else None
            stalls = con.execute("SELECT COUNT(*) FROM observations WHERE kind='stream_stall' AND created >= ?",
                                 (iso(now - timedelta(hours=1)),)).fetchone()[0]
        self._sample_frames(n_frames)
        lc = last_created[0] if last_created else None
        age = (now - parse_iso(lc)).total_seconds() if lc else None
        try:
            size_mb = round(Path(self.db_path).stat().st_size / 1e6, 1)
        except OSError:
            size_mb = None
        cal_lat = self.db.calibration("latency_s")
        return {"server_time": iso(now), "server_time_oslo": to_oslo(iso(now)), "db": self.db_path, "db_size_mb": size_mb,
                "max_ids": {"observations": n_obs, "frames": n_frames, "audio": n_audio}, "events_new": ev_new,
                "last_observation_created": lc, "last_write_age_s": round(age, 1) if age is not None else None,
                "runner_alive": bool(age is not None and age < 300), "frames_per_min": self.frames_per_min(),
                "latest_frame": self.latest_frame(), "stream_health": last["stream_health"],
                "uplink": last["uplink_signature"], "stream_latency": last["stream_latency"], "stalls_last_hour": stalls,
                "latency_s": cal_lat, "latency_sigma_s": self.db.calibration("latency_sigma_s"),
                "audio_offset_s": self.db.calibration("audio_offset_s"), "sse_clients": self.sse_clients}

    def _sample_frames(self, max_id):
        self._frame_samples.append((time.monotonic(), int(max_id or 0)))

    def frames_per_min(self, window_s=300.0):
        if len(self._frame_samples) < 2:
            return None
        t1, n1 = self._frame_samples[-1]
        old = [s for s in self._frame_samples if t1 - s[0] <= window_s]
        t0, n0 = old[0]
        if t1 - t0 < 20.0:
            return None
        return round((n1 - n0) / ((t1 - t0) / 60.0), 2)

    # ------------------------------------------------------------------ SSE polling
    def max_ids(self):
        with self.connect() as con:
            o = con.execute("SELECT MAX(id) FROM observations").fetchone()[0] or 0
            e = con.execute("SELECT MAX(id) FROM events").fetchone()[0] or 0
        return int(o), int(e)

    def poll(self, cur_obs, cur_ev, kinds=None, limit=200):
        """New observations/events after the cursors -> (obs_rows, event_rows, new_cur_obs, new_cur_ev, frame_max,
        cal_stamp). The cursor advances over rows filtered out by ``kinds`` too."""
        with self.connect() as con:
            mo = con.execute("SELECT MAX(id) FROM observations").fetchone()[0] or 0
            me = con.execute("SELECT MAX(id) FROM events").fetchone()[0] or 0
            where, args = ["o.id > ?", "o.id <= ?"], [cur_obs, mo]
            if kinds:
                where.append("o.kind IN (%s)" % ",".join("?" * len(kinds)))
                args += list(kinds)
            orows = con.execute(self.OBS_SQL + " WHERE " + " AND ".join(where) + " ORDER BY o.id LIMIT ?",
                                args + [limit]).fetchall() if mo > cur_obs else []
            erows = con.execute("SELECT * FROM events WHERE id > ? AND id <= ? ORDER BY id LIMIT ?",
                                (cur_ev, me, limit)).fetchall() if me > cur_ev else []
            fmax = con.execute("SELECT MAX(id) FROM frames").fetchone()[0] or 0
            cal = tuple(con.execute("SELECT MAX(updated), COUNT(*) FROM calibration").fetchone())
        new_o = orows[-1]["id"] if len(orows) == limit else max(cur_obs, mo)
        new_e = erows[-1]["id"] if len(erows) == limit else max(cur_ev, me)
        self._sample_frames(fmax)
        return ([self.obs_dict(r) for r in orows], [self.event_dict(r) for r in erows], new_o, new_e, fmax, cal,
                len(orows) == limit or len(erows) == limit)


# =============================================================================== module helpers
def _resolve(p) -> Path:
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def _float(x) -> float:
    try:
        return float(x) if x is not None and not isinstance(x, bool) else (float(x) if isinstance(x, bool) else np.nan)
    except (TypeError, ValueError):
        return np.nan


def _delta(a: Optional[str], b: Optional[str]) -> Optional[float]:
    if not a or not b:
        return None
    try:
        return round(unix_of(a) - unix_of(b), 3)
    except ValueError:
        return None


def _read_json(p: Path):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


def _mtime_iso(p: Path) -> Optional[str]:
    try:
        return datetime.fromtimestamp(Path(p).stat().st_mtime, UTC).isoformat(timespec="seconds")
    except OSError:
        return None


def _thin(marks: list, max_n: int, span_s: float) -> list:
    """Keep at most ~max_n markers: the most confident per time bin (so a burst never hides a rare cue)."""
    if len(marks) <= max_n:
        return marks
    bin_ms = max(span_s * 1000.0 / max_n, 1.0)
    best: dict = {}
    for m in marks:
        k = int(m["t"] // bin_ms)
        if k not in best or (m.get("conf") or 0) > (best[k].get("conf") or 0):
            best[k] = m
    return [best[k] for k in sorted(best)]


def _layer_info(p: Path, grid) -> dict:
    with np.load(p, allow_pickle=False) as d:
        meta = json.loads(str(d["meta"])) if "meta" in d.files else {}
        ll = np.asarray(d["loglik"], float)
        lat0 = float(d["lat_min"]) if "lat_min" in d.files else grid.lat_min
        lon0 = float(d["lon_min"]) if "lon_min" in d.files else grid.lon_min
        dlat = float(d["dlat"]) if "dlat" in d.files else grid.dlat
        dlon = float(d["dlon"]) if "dlon" in d.files else grid.dlon
    fin = np.isfinite(ll)
    info = {"file": p.name, "name": meta.get("name", p.stem), "reliability": meta.get("reliability"),
            "independence_group": meta.get("independence_group"), "description": meta.get("description", ""),
            "sources": meta.get("sources", []), "shape": list(ll.shape), "n_cells": int(fin.sum()), "peak": None,
            "range": None}
    if fin.any():
        i, j = np.unravel_index(np.nanargmax(np.where(fin, ll, -np.inf)), ll.shape)
        lat, lon = lat0 + i * dlat, lon0 + j * dlon
        nk, gm = map_links(lat, lon)
        info["peak"] = {"lat": round(lat, 4), "lon": round(lon, 4), "loglik": round(float(ll[i, j]), 3),
                        "norgeskart": nk, "google_maps": gm}
        info["range"] = round(float(np.nanmax(ll) - np.nanmin(ll)), 3)
    return info


# =============================================================================== app factory
def create_app(db_path, output_dir=None, archive_dir=None, layers_dir=None, config: Optional[dict] = None,
               notifier: Any = "auto") -> FastAPI:
    """Build the dashboard app.

    db_path     SQLite file written by the runner (created empty if missing)
    output_dir  hordejakt engine output (map.html, hotspots.json, scenario_hotspots.json, history/)
    archive_dir frame archive (default: config archive_dir, <db dir>/archive, data/hordewatch/archive)
    layers_dir  live evidence grids (default data/hordewatch/layers)
    config      full hordewatch config (runner.load_config); uses ``camera``, ``clock``, ``archive_dir``
                and the optional ``dashboard`` section {sun_ref: [lat, lon], media_roots: [...],
                ntfy: {topic, server, ...}}
    notifier    "auto" starts :class:`notify.NtfyNotifier` when ``dashboard.ntfy.topic`` is set;
                None disables; or pass a ready (unstarted) notifier object with start()/stop().
    """
    store = Store(db_path, output_dir, archive_dir, layers_dir, config)
    ntfy = None
    if notifier == "auto":
        ncfg = ((config or {}).get("dashboard") or {}).get("ntfy") or {}
        if ncfg.get("topic"):
            from .notify import NtfyNotifier
            ntfy = NtfyNotifier(store.db_path, **{k: v for k, v in ncfg.items() if k in NtfyNotifier.CONFIG_KEYS})
    elif notifier is not None:
        ntfy = notifier

    @asynccontextmanager
    async def lifespan(app):
        if ntfy is not None:
            try:
                ntfy.start()
            except Exception as e:  # pragma: no cover
                log.warning("ntfy notifier failed to start: %s", e)
        yield
        if ntfy is not None:
            try:
                ntfy.stop()
            except Exception:  # pragma: no cover
                pass

    app = FastAPI(title="hordewatch dashboard", version="1.0", lifespan=lifespan)
    app.state.store = store
    app.state.notifier = ntfy

    def _bad(e):
        raise HTTPException(status_code=400, detail=str(e))

    def _times(since, until):
        try:
            return parse_time_param(since), parse_time_param(until)
        except ValueError as e:
            _bad(f"bad time: {e}")

    # ------------------------------------------------------------------ page + files
    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html", media_type="text/html",
                            headers={"Cache-Control": "no-cache"})

    @app.get("/static/{name}", include_in_schema=False)
    def static_file(name: str):
        p = (STATIC_DIR / name).resolve()
        if STATIC_DIR.resolve() not in p.parents or not p.is_file():
            raise HTTPException(404, "not found")
        return FileResponse(p)

    @app.get("/output/{name}", include_in_schema=False)
    def output_file(name: str):
        if not OUTPUT_FILE_RE.match(name):
            raise HTTPException(404, "not an output file")
        p = (store.output_dir / name)
        if not p.is_file():
            raise HTTPException(404, f"{name} not found in {store.output_dir} (run the engine: python -m hordejakt.cli)")
        return FileResponse(p, headers={"Cache-Control": "no-cache"})

    @app.get("/api/health")
    def health():
        return {"ok": True, "time": iso(utcnow())}

    @app.get("/api/status")
    def status():
        return store.status()

    # ------------------------------------------------------------------ observations
    @app.get("/api/kinds")
    def kinds():
        return store.kinds()

    @app.get("/api/observations")
    def observations(kind: Optional[str] = None, analyzer: Optional[str] = None,
                     min_conf: float = Query(0.0, ge=0.0, le=1.0), since: Optional[str] = None, until: Optional[str] = None,
                     q: Optional[str] = None, limit: int = Query(100, ge=1, le=1000), order: str = Query("id", pattern="^(id|ts)$"),
                     before_id: Optional[int] = None, before_ts: Optional[str] = None):
        s, u = _times(since, until)
        kinds_ = [k.strip() for k in kind.split(",") if k.strip()] if kind else None
        return store.observations(kinds_, analyzer or None, min_conf, s, u, (q or "").strip() or None, limit, order,
                                  before_id, before_ts)

    @app.get("/api/observations/{obs_id}")
    def observation(obs_id: int):
        o = store.observation(obs_id)
        if o is None:
            raise HTTPException(404, "no such observation")
        return o

    # ------------------------------------------------------------------ events
    @app.get("/api/events")
    def events(status: str = Query("all", pattern="^(all|new|ack|dismissed)$"), kind: Optional[str] = None,
               limit: int = Query(100, ge=1, le=1000), before_id: Optional[int] = None):
        return store.events(status, kind, limit, before_id)

    @app.post("/api/events/{event_id}/ack")
    def ack(event_id: int, body: Optional[dict] = Body(None)):
        st = (body or {}).get("status", "ack")
        if st not in EVENT_STATUSES:
            _bad(f"status must be one of {EVENT_STATUSES}")
        d = store.set_event_status(event_id, st)
        if d is None:
            raise HTTPException(404, "no such event")
        return d

    @app.post("/api/events/ack_all")
    def ack_all(up_to_id: Optional[int] = None, kind: Optional[str] = None):
        ids = store.ack_all(up_to_id, kind)
        return {"acked": len(ids), "ids": ids}

    # ------------------------------------------------------------------ whiteboard + media
    @app.get("/api/whiteboard")
    def whiteboard(limit: int = Query(40, ge=1, le=500), only_new: bool = False):
        return {"boards": store.whiteboard(limit, only_new)}

    @app.get("/api/whiteboard/{obs_id}/crop.jpg")
    def whiteboard_crop(obs_id: int, pad: float = Query(0.15, ge=0.0, le=2.0), max_w: int = Query(900, ge=64, le=4000)):
        res = store.whiteboard_image(obs_id)
        if res is None:
            raise HTTPException(404, "no archived frame for this board")
        f, fr, bbox = res
        data = crop_jpeg(f, bbox, (fr["w"], fr["h"]), pad=pad, max_w=max_w)
        if data is None:
            return FileResponse(f)
        return Response(data, media_type="image/jpeg", headers={"Cache-Control": "max-age=3600"})

    @app.get("/api/frames/latest")
    def frames_latest():
        return store.latest_frame() or {}

    @app.get("/api/frames/near")
    def frames_near(ts: str, max_s: float = Query(120.0, gt=0, le=3600), redirect: bool = True):
        try:
            t = parse_time_param(ts)
        except ValueError as e:
            _bad(e)
        r, f = store.nearest_frame(t, max_s)
        if r is None:
            raise HTTPException(404, f"no archived frame within ±{max_s:.0f} s")
        d = {"id": r["id"], "real_ts": r["real_ts"], "real_ts_oslo": to_oslo(r["real_ts"]),
             "offset_s": round(unix_of(r["real_ts"]) - unix_of(t), 2), "url": f"api/frames/{r['id']}/image"}
        if redirect:
            return FileResponse(f, headers={"X-Frame-Id": str(r["id"]), "X-Frame-Offset-S": str(d["offset_s"])})
        return d

    @app.get("/api/frames/{frame_id}/image")
    def frame_image(frame_id: int, max_w: Optional[int] = Query(None, ge=32, le=8000)):
        r, f = store.frame_by_id(frame_id)
        if f is None:
            raise HTTPException(404, "frame not archived")
        if max_w:
            data = crop_jpeg(f, None, (r["w"], r["h"]), max_w=max_w)
            if data is not None:
                return Response(data, media_type="image/jpeg", headers={"Cache-Control": "max-age=86400"})
        return FileResponse(f, headers={"Cache-Control": "max-age=86400"})

    @app.get("/api/audio/{audio_id}")
    def audio_file(audio_id: int):
        with store.connect() as con:
            r = con.execute("SELECT path FROM audio WHERE id=?", (audio_id,)).fetchone()
        f = store.media_file(r["path"], AUDIO_EXT) if r else None
        if f is None:
            raise HTTPException(404, "audio chunk not archived (set source.archive_audio: true)")
        return FileResponse(f)

    # ------------------------------------------------------------------ timeline / map / calibration
    @app.get("/api/timeline")
    def timeline(since: Optional[str] = None, until: Optional[str] = None, bucket_s: Optional[float] = Query(None, gt=0),
                 sun_lat: Optional[float] = Query(None, ge=-90, le=90), sun_lon: Optional[float] = Query(None, ge=-180, le=180),
                 max_markers: int = Query(1500, ge=10, le=20000)):
        s, u = _times(since, until)
        try:
            return store.timeline(s, u, bucket_s, sun_lat, sun_lon, max_markers)
        except ValueError as e:
            _bad(e)

    @app.get("/api/hotspots")
    def hotspots(source: str = Query("base", pattern="^(base|scenarios)$"), top: int = Query(30, ge=1, le=200)):
        return store.hotspots(source, top)

    @app.get("/api/engine/history")
    def engine_history(limit: int = Query(20, ge=1, le=500)):
        return {"runs": store.engine_history(limit)}

    @app.get("/api/layers")
    def layers():
        return {"dir": str(store.layers_dir), "layers": store.layers()}

    @app.get("/api/calibration")
    def calibration():
        return store.calibration()

    @app.post("/api/calibration")
    def set_calibration(body: dict = Body(...)):
        key, value = body.get("key"), body.get("value")
        if key in CAL_NUMERIC:
            lo, hi = CAL_NUMERIC[key]
            v = _float(value)
            if not math.isfinite(v) or not lo <= v <= hi:
                _bad(f"{key} must be a number in [{lo}, {hi}]")
            value = v
        elif key == "camera_attitude":
            if not isinstance(value, dict) or not {"heading_deg", "pitch_deg", "roll_deg"} & set(value):
                _bad("camera_attitude needs a dict with heading_deg / pitch_deg / roll_deg (+ *_sigma_deg)")
            clean = {}
            for k, x in value.items():
                if k not in CAL_ATTITUDE:
                    _bad(f"unknown camera_attitude field {k}")
                lo, hi = CAL_ATTITUDE[k]
                v = _float(x)
                if not math.isfinite(v) or not lo <= v <= hi:
                    _bad(f"{k} must be in [{lo}, {hi}]")
                clean[k] = v
            clean["method"] = "manual (dashboard)"
            value = clean
        else:
            _bad(f"key must be one of {sorted(CAL_NUMERIC) + ['camera_attitude']}")
        store.set_calibration(key, value)
        return {"key": key, "value": value}

    # ------------------------------------------------------------------ SSE
    @app.get("/api/stream")
    async def stream(request: Request, since_obs: Optional[int] = None, since_event: Optional[int] = None,
                     kinds: Optional[str] = None, max_events: Optional[int] = Query(None, ge=1),
                     timeout: Optional[float] = Query(None, gt=0), poll_s: float = Query(1.0, ge=0.05, le=10.0),
                     heartbeat_s: float = Query(15.0, ge=0.5, le=300.0), frame_every_s: float = Query(5.0, ge=0.0, le=600.0)):
        """Server-Sent Events: ``hello``, ``observation``, ``event``, ``event_update``, ``frame``,
        ``calibration`` (+ ``: ping`` comments). Cursors: Last-Event-ID header ("o<obs>.e<event>") >
        since_obs/since_event > current maxima (only rows that arrive after connecting).
        ``max_events`` / ``timeout`` end the stream (tests, scripts); a browser keeps it open."""
        kinds_ = [k.strip() for k in kinds.split(",") if k.strip()] if kinds else None
        mo, me = await run_in_threadpool(store.max_ids)
        cur_o = since_obs if since_obs is not None else mo
        cur_e = since_event if since_event is not None else me
        m = re.match(r"^o(\d+)\.e(\d+)$", request.headers.get("last-event-id", "").strip())
        if m:
            cur_o, cur_e = int(m.group(1)), int(m.group(2))

        async def gen():
            nonlocal cur_o, cur_e
            store.sse_clients += 1
            try:
                t_start = time.monotonic()
                sent = 0
                bus_seq = store.bus.seq
                last_frame, last_frame_sent, cal_stamp = None, 0.0, None
                last_beat = time.monotonic()
                yield "retry: 3000\n\n"
                yield _sse("hello", {"obs_cursor": cur_o, "event_cursor": cur_e, "server_time": iso(utcnow()),
                                     "kinds": kinds_}, f"o{cur_o}.e{cur_e}")
                while True:
                    if await request.is_disconnected():
                        break
                    obs, evs, cur_o, cur_e, fmax, cal, backlog = await run_in_threadpool(store.poll, cur_o, cur_e, kinds_)
                    cid = f"o{cur_o}.e{cur_e}"
                    for o in obs:
                        yield _sse("observation", o, f"o{o['id']}.e{cur_e}" if o is not obs[-1] else cid)
                        sent += 1
                    for e in evs:
                        yield _sse("event", e, cid)
                        sent += 1
                    for seq, name, data in store.bus.since(bus_seq):
                        bus_seq = seq
                        yield _sse(name, data, cid)
                        if name == "event_update":
                            sent += 1
                    now = time.monotonic()
                    if cal_stamp is None:
                        cal_stamp = cal
                    elif cal != cal_stamp:
                        cal_stamp = cal
                        yield _sse("calibration", {"latency_s": store.db.calibration("latency_s"),
                                                   "latency_sigma_s": store.db.calibration("latency_sigma_s"),
                                                   "audio_offset_s": store.db.calibration("audio_offset_s"),
                                                   "updated": cal[0]}, cid)
                    if fmax != last_frame and now - last_frame_sent >= frame_every_s:
                        first = last_frame is None
                        last_frame, last_frame_sent = fmax, now
                        if not first and fmax:
                            lf = await run_in_threadpool(store.latest_frame)
                            if lf:
                                yield _sse("frame", lf, cid)
                    if max_events is not None and sent >= max_events:
                        break
                    if timeout is not None and now - t_start >= timeout:
                        break
                    if now - last_beat >= heartbeat_s:
                        last_beat = now
                        yield f": ping {iso(utcnow())}\n\n"
                    if not backlog:
                        await asyncio.sleep(poll_s)
            finally:
                store.sse_clients -= 1

        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"})

    return app


def _sse(event: str, data: Any, id_: Optional[str] = None) -> str:
    s = f"id: {id_}\n" if id_ else ""
    return s + f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


def crop_jpeg(path: Path, bbox, frame_wh=(None, None), pad: float = 0.15, max_w: int = 900, quality: int = 85):
    """Cut ``bbox`` (x0,y0,x1,y1 in the *frame's* pixel grid, e.g. a whiteboard) out of an archived JPEG,
    padded by ``pad`` x the larger box side, and downscale to ``max_w``. The bbox is rescaled when the
    archived JPEG size differs from the frame size recorded in the DB. Returns JPEG bytes, or None when
    OpenCV is unavailable / the image is unreadable (caller serves the full file)."""
    try:
        import cv2
    except Exception:  # pragma: no cover
        return None
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        return None
    H, W = img.shape[:2]
    if bbox is not None and len(bbox) == 4:
        fw, fh = frame_wh
        sx = W / float(fw) if fw else 1.0
        sy = H / float(fh) if fh else 1.0
        x0, y0, x1, y1 = (float(bbox[0]) * sx, float(bbox[1]) * sy, float(bbox[2]) * sx, float(bbox[3]) * sy)
        p = pad * max(x1 - x0, y1 - y0)
        xa, ya = int(max(0, math.floor(x0 - p))), int(max(0, math.floor(y0 - p)))
        xb, yb = int(min(W, math.ceil(x1 + p) + 1)), int(min(H, math.ceil(y1 + p) + 1))
        if xb - xa >= 4 and yb - ya >= 4:
            img = img[ya:yb, xa:xb]
    h, w = img.shape[:2]
    if w > max_w:
        img = cv2.resize(img, (max_w, max(1, int(round(h * max_w / w)))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    return buf.tobytes() if ok else None
