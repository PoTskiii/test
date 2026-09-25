"""Aircraft bridge: ADS-B truth x stream events -> location likelihood grids + stream latency.

Why this works
--------------
An aircraft is a moving, precisely known object (ADS-B gives position every
1-10 s with ~10 m accuracy). Whenever the stream shows a reaction to an
aircraft -- Anja points up (``gesture_point_up``), a blinking light crosses the
frame at night (``aircraft_light``) or jet noise peaks on the audio
(``audio_aircraft``) -- only the places from where *some* tracked aircraft
could have caused that reaction at that moment remain plausible. Several such
events intersect quickly. The unknown stream latency (encoder + Starlink/4G +
YouTube, ~15-60 s) is the main nuisance parameter: it is marginalised in every
event and estimated jointly from audio peaks (``calibrate_latency``).

Event models (all evaluated on a 0.02 deg x 0.04 deg (~2.2 km) coarse grid, then
bilinearly upsampled to hordejakt.grid.GRID like hordejakt.layers.aircraft)

* Sighting (gesture_point_up). Same geometry as hordejakt.layers.aircraft.event_prob:
      P(event | x, D) = b + (1-b) [1 - prod_a (1 - q vis(elev_a(x, t_c - D)) g_a)]
  vis() is the soft canopy elevation threshold (logistic, mid 25 deg, scale 3 deg),
  elevations use the 4/3-earth refraction model of hordejakt.geo, the observer
  stands at OBSERVER_M = 600 m a.s.l. t_c is the capture time of the onset frame
  and D = L + u with u in [-dwell, reaction + sampling gap]: she saw the aircraft
  up to reaction_s (8 s) plus one frame gap before the onset frame, and kept
  pointing at it (following it) for the episode duration ``dwell`` after it
  (from the gesture 'summary' row, capped at 60 s). P(event | x) = sum_D w(D)
  P(event | x, D) with w from the latency prior (calibrated N(mu, sigma) or
  uniform 15-60 s with 10 s Gaussian shoulders).
  g_a is an optional pointing-direction factor: with the camera heading psi and
  an aircraft at azimuth A / elevation h, her arm appears tilted from vertical
  in the image by tau = atan2(cos h sin(A - psi), sin h) (negative = image left;
  this reproduces the mk_bevis tilt_2129 table).
      g_a = (1-w) + w [p N(tau; tau_obs, 12 deg) + (1-p) N(tau; -tau_obs, 12 deg)]
  p is the probability that the *sign* of the observed tilt is right: the gesture
  analyzer reports an unsigned angle plus a 'side' that, depending on the detector
  path, is the tilt direction (arm-only path: tip vs. base, p = 0.9) or only the
  side of the body the raised arm is on (MediaPipe / limb paths, p = 0.75); a
  manually entered signed tilt gets p = 0.95.

* Light in frame (aircraft_light, night). The pixel track is turned into
  azimuth/elevation with the fitted camera (heading 219.6 deg, pitch 0, f = 1068 px
  at 1280 px width) and compared with each aircraft's direction seen from x:
      match_a(x, D) = exp(-mean_i delta_i^2 / (2 sigma^2)),  sigma = 3 deg
  (delta_i = great-circle angle between observed and predicted direction at the
  track point i). P(x) = b + (1-b)[1 - prod_a (1 - q match_a)], marginalised over D.
  This is very location-specific: a light at 12 deg elevation towards SW pins the
  box to a ~5 km wide strip NE of the aircraft.

* Sound (audio_aircraft). For a source moving past x, received intensity ~ 1/s(t)^2
  peaks for emission at the closest point of approach (CPA); the peak is received
  s_cpa / c later (c = harmonic-mean ISA speed of sound along the ray, ~318 m/s
  for a cruising jet; config ``sound_speed: 343`` forces the textbook value).
  The observed stream peak is t_obs = t_cpa + s_cpa / c + L_audio. The peak of an
  intensity bump of width s_cpa / v is only defined to a fraction of that width
  (and jet noise radiates aft, delaying the perceived peak), so
      sigma_t = sqrt(4^2 + (0.3 s_cpa / v)^2) s.
  Audibility decreases with slant distance: P_aud(s) = 1 / (1 + exp((s - 16 km) / 2.5 km))
  (airliners at cruise are plausibly audible at 5-25 km slant in a quiet forest).
  Detected peaks at x form a Poisson process in stream time with rate
      lambda(t | x, L) = b + sum_a P_aud(s_a) N(t; t_peak_a + L, sigma_a)      (per s)
  (b = background rate of detections not caused by a tracked aircraft: untracked
  aircraft, vehicles, wind; default 4 / h). The evidence of one peak is the
  *conditional* density of its time given one detection in the window
  W = [t_obs - 180 s, t_obs + 180 s], scaled so that "no information" = 1:
      r(x, L) = 2|W| lambda(t_obs | x, L) / integral_W lambda(t | x, L) dt
      P(peak | x) = sum_L w(L) r(x, L)
  The normalisation is essential: an unnormalised "some aircraft explains the
  peak" score (1 - prod_a (1 - p_a)) saturates wherever audible traffic is dense
  (airport approaches, airway crossings), so every peak would favour busy
  airspace over the quiet forest the box stands in. Under r(x, L) a place where
  aircraft pass all the time is uninformative (r ~ 1), a place where one aircraft
  passes exactly at the right time scores high, and a place where aircraft pass
  at the wrong times scores < 1. Missed detections are not modelled (the
  analyzer's detection efficiency is unknown), so no expected-count penalty.

Latency calibration
-------------------
Given >= 3 non-looped audio peaks, candidate box locations x_k with weights w_k
from the current posterior (output/posterior.npz pooled to ~5 km blocks), and the
tracks around each peak:
      J(L) = sum_k w_k prod_e r_e(x_k, L)
The posterior over L (flat prior on 0-120 s) is well determined when at least
3 peaks are explained by aircraft (r >= 3 at the MAP and best candidate), the MAP
is sharply peaked (posterior sd <= 8 s, >= 70 % mass within +-10 s) and log J(MAP)
exceeds the median by >= 3. Only then are ``latency_s`` / ``latency_sigma_s`` written
to the calibration table (the runner reads ``latency_s`` as a float at start-up) and
the live StreamClock updated. A systematic floor of 3 s (wind, directivity) is
added in quadrature to the statistical sd. One peak alone cannot calibrate:
latency trades off against position along the track. Candidate positions are
~5 km block centroids, so a few km of along-track position error (~10 s at
airliner speed) enters the fit; it averages out over peaks from aircraft on
different headings but is one reason for the systematic floor.

Reliability and independence groups
-----------------------------------
Per event r = r_kind x f(detection confidence), clipped to 0.5-0.75 for confident
detections (and x 0.8 before clipping when the ADS-B coverage may be incomplete).
Gesture-only events whose detections are all below ``gesture_strong_conf`` (0.5;
e.g. the arm-only fallback detector) get r 0.2-0.5 and share one daily group
hw_aircraft_lowconf_<YYYYMMDD>: fusion averages them instead of multiplying, so a
noisy detector that fires on stretching or hair-fixing cannot compound many
"some aircraft was overhead then" layers (which favour busy airspace).

Daily audio layers: many per-event audio layers (a live microphone hears dozens of
overflights a day) would each carry their own reliability and compound if the
audio is replayed. In ``audio_mode: auto`` (default) audio-only events get
per-event layers until more than ``audio_daily_threshold`` (6) occur in a local
day; then they are replaced by one joint layer aircraft_audio_<YYYYMMDD>.npz with a
*shared* latency, log sum_L w(L) prod_e P_e(x | L) (statistically right, since the
latency is common, and bounded by a single reliability of 0.5).

Looped audio: default.no found audio repeating 22-48 h later. Audio events within
``loop_margin_s`` of an ``audio_loop`` observation are skipped entirely; if loops
are frequent around an event its layer reliability drops to the minimum.

ADS-B sources (``providers`` config, tried in order until one covers the window)
* ``fixture``     local fixtures: magnus fly_2130.json (all aircraft 21.09 ~21:28-21:35),
                  default.no flyhendelser.json (tracks for 21.09 21:29, 22.09 20:32/20:34;
                  timing synthesised from course/speed, approximate), and the real adsb.lol
                  trace_full files of mk_bevis. NOTE: fly_2130.json timestamps are ~45 s
                  EARLY relative to the adsb.lol traces (measured on NOZ9EG/4791ac and
                  NOZ56U/47a3b0: +43..+51 s); the provider corrects by ``fly2130_offset_s``.
* ``trace_cache`` every trace_full_*.json(.gz) under data/hordewatch/adsb/traces/.
* ``live_record`` snapshots recorded by LiveRecorder (adsb.lol /v2 point API, fallback
                  airplanes.live) under data/hordewatch/adsb/live/ -- the only complete live
                  source, since the point APIs have no history: run the recorder continuously.
* ``adsblol_history`` globe.adsb.lol globe_history trace_full per hex (hexes from recorded
                  snapshots or ``hexes`` config). Incomplete by construction.
* ``opensky``     OpenSky /api/states/all?time= (OAuth2 client credentials or legacy basic
                  auth). Step 15 s, bbox-limited. The REST API serves state vectors at most
                  1 h back even to registered users (older ``time`` -> HTTP 400) and ignores
                  ``time`` for anonymous users, so this is a near-real-time fallback for
                  events processed within the hour, never a history source; older or
                  anonymous windows are refused without a request.
* ``adsblol_release`` daily globe_history tarballs on GitHub (adsblol/globe_history_YYYY,
                  multi-GB; streamed and filtered to the bbox). Off by default; asset naming
                  not verified from this container.
Every network call fails soft (rate-limited warning) and results are cached
under data/hordewatch/adsb/.

Failure modes / caveats
* An aircraft missing from ADS-B (military, GA without ADS-B, satellites) can
  explain an event the model cannot -> floor b and reliability <= 0.75.
* Gesture misreads and non-aircraft sounds (vehicles, wind, chainsaws) -> floor.
* Replayed (looped) audio carries no location information -> skipped.
* fly_2130/flyhendelser fixture timing is approximate (+-15 s); real traces win.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import logging
import tarfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.special import ndtr

from hordejakt import DEFAULTNO, MAGNUS, RAW
from hordejakt.geo import FT, R_EARTH, bearing, elevation_angle, haversine
from hordejakt.grid import GRID
from hordejakt.layers.aircraft import BOX, COARSE_DLAT, COARSE_DLON, OBSERVER_M, vis

from ..analyzers.base import Analyzer
from ..types import UTC, Observation, parse_iso
from .common import (RateLimitedLog, cache_dir, coarse_axes, dumps, from_unix, layers_dir, load_state, local_date,
                     observation_latencies, posterior_candidates, save_state, setting, stamp, to_unix, upsample,
                     write_layer)

log = logging.getLogger("hordewatch.bridges.adsb")
warn_once = RateLimitedLog(600)

KT = 0.514444  # m/s per knot
TRIGGERS = ("gesture_point_up", "audio_aircraft", "aircraft_light")
FETCH_BBOX = (BOX[0] - 0.7, BOX[1] + 0.7, BOX[2] - 1.5, BOX[3] + 1.5)  # aircraft just outside the domain matter
MK_BEVIS_ADSB = RAW / "mk_bevis" / "bevis" / "claude-2026-09-25" / "adsb"

# Hand-curated events already modelled by hordejakt.layers.aircraft. A hordewatch
# event within DEDUP_S of one of these reuses its independence group, so fusion
# averages the two layers instead of counting the same pointing twice.
BUILTIN_EVENTS = {
    "aircraft_2109_2129_point": "2026-09-21T21:29:38+02:00",
    "aircraft_2209_2032_flyy": "2026-09-22T20:32:40+02:00",
    "aircraft_2209_2034_follow": "2026-09-22T20:34:40+02:00",
    "aircraft_2509_1722_point": "2026-09-25T17:22:00+02:00",
}
DEDUP_S = 60.0

# stream time of the reaction that each flyhendelser.json block belongs to
FLYHENDELSER_STREAM = {"21.09 21:29": "2026-09-21T21:29:38+02:00",
                       "22.09 20:32": "2026-09-22T20:32:40+02:00",
                       "22.09 20:34": "2026-09-22T20:34:40+02:00"}

DEFAULTS = {
    "providers": ["live_record", "trace_cache", "adsblol_history", "opensky"],
    "latency_range_s": [15.0, 60.0], "latency_margin_s": 10.0, "latency_step_s": 2.5,
    "reaction_s": 8.0, "max_dwell_s": 60.0,
    "q": 0.85, "floor": 0.05, "vis_mid": 25.0, "vis_scale": 3.0, "min_alt_ft": 3000.0,
    "tilt_sigma_deg": 12.0, "tilt_weight": 0.6,
    "light_sigma_deg": 3.0, "light_floor": 0.1,
    "audible_s50_km": 16.0, "audible_width_km": 2.5, "sound_speed": "isa",
    "audio_bg_rate_per_h": 4.0, "audio_window_s": 180.0, "audio_cpa_dt_s": 4.0,
    "audio_sigma_det_s": 4.0, "audio_width_frac": 0.3,
    "cluster_s": 60.0, "max_cluster_s": 300.0, "settle_s": 180.0, "retry_s": 300.0, "max_tries": 12,
    "lookback_h": 24 * 14,
    "loop_margin_s": 30.0, "calibrate": True, "calib_min_events": 3, "calib_every_s": 900.0,
    "reliability": {"gesture_point_up": 0.65, "aircraft_light": 0.7, "audio_aircraft": 0.55},
    "gesture_strong_conf": 0.5,
    "camera_heading_deg": 219.6, "camera_pitch_deg": 0.0, "camera_roll_deg": 0.0,
    "camera_focal_px_1280": 1068.0, "image_w": 1280, "image_h": 720,
    "async": True, "live_record": None, "poll_s": 10.0,
    "audio_mode": "auto", "audio_daily_threshold": 6,
}
AUDIO_L_GRID = np.arange(0.0, 120.0 + 1e-9, 2.5)   # fixed audio-latency grid of the daily accumulators


def cfg_get(config, key):
    v = setting(config, key, None)
    return DEFAULTS.get(key) if v is None else v


# =========================================================================== tracks
@dataclass
class Track:
    """One aircraft's positions. Times are unix seconds (UTC), alt_m is geometric
    (GNSS) altitude when available, else barometric (both ~ m a.s.l.; the
    geoid/ISA errors of a few hundred ft do not matter at the elevation-angle
    precision used here). NaN altitude = on ground or unknown."""
    hex: str | None
    callsign: str | None
    t: np.ndarray
    lat: np.ndarray
    lon: np.ndarray
    alt_m: np.ndarray
    gs_kt: np.ndarray | None = None
    track_deg: np.ndarray | None = None
    leg_start: np.ndarray | None = None      # True where readsb flags a new leg (no interpolation across)
    source: str = ""
    type: str | None = None
    reg: str | None = None
    max_gap_s: float = 120.0
    approx: bool = False                      # synthetic timing (fixtures)

    def __post_init__(self):
        o = np.argsort(self.t, kind="stable")
        for k in ("t", "lat", "lon", "alt_m", "gs_kt", "track_deg", "leg_start"):
            v = getattr(self, k)
            if v is not None:
                setattr(self, k, np.asarray(v)[o])
        self.t = self.t.astype(float)
        if self.leg_start is None:
            self.leg_start = np.zeros(len(self.t), bool)

    @property
    def key(self):
        return (self.hex or "").lower() or f"cs:{(self.callsign or '').strip()}"

    @property
    def label(self):
        return (self.callsign or "").strip() or (self.hex or "?")

    def span(self):
        return (float(self.t[0]), float(self.t[-1])) if len(self.t) else (np.nan, np.nan)

    def at(self, times):
        """Linear interpolation -> (lat, lon, alt_m, ok). ok is False outside the
        track, across gaps > max_gap_s, across a new leg, or on the ground."""
        times = np.atleast_1d(np.asarray(times, float))
        n = len(self.t)
        nan = np.full(times.shape, np.nan)
        if n < 2:
            return nan, nan.copy(), nan.copy(), np.zeros(times.shape, bool)
        k = np.searchsorted(self.t, times, side="right") - 1
        k = np.where(times == self.t[-1], n - 2, k)
        inside = (k >= 0) & (k < n - 1)
        kc = np.clip(k, 0, n - 2)
        t0, t1 = self.t[kc], self.t[kc + 1]
        dt = t1 - t0
        f = np.where(dt > 0, (times - t0) / np.where(dt > 0, dt, 1), 0.0)
        a0, a1 = self.alt_m[kc], self.alt_m[kc + 1]
        ok = inside & (dt <= self.max_gap_s) & ~self.leg_start[kc + 1] & np.isfinite(a0) & np.isfinite(a1)
        lat = self.lat[kc] + f * (self.lat[kc + 1] - self.lat[kc])
        lon = self.lon[kc] + f * (self.lon[kc + 1] - self.lon[kc])
        alt = a0 + f * (a1 - a0)
        return (np.where(ok, lat, np.nan), np.where(ok, lon, np.nan), np.where(ok, alt, np.nan), ok)

    def speed_at(self, times):
        """Ground speed (m/s) from the reported gs, or from finite differences."""
        times = np.atleast_1d(np.asarray(times, float))
        if self.gs_kt is not None and np.isfinite(self.gs_kt).any():
            ok = np.isfinite(self.gs_kt)
            return np.interp(times, self.t[ok], self.gs_kt[ok]) * KT
        if len(self.t) < 2:
            return np.full(times.shape, 230.0)
        d = haversine(self.lat[:-1], self.lon[:-1], self.lat[1:], self.lon[1:]) * 1000.0
        v = d / np.maximum(np.diff(self.t), 1e-3)
        tm = 0.5 * (self.t[:-1] + self.t[1:])
        return np.interp(times, tm, v)

    def window(self, t0, t1, pad=120.0):
        m = (self.t >= t0 - pad) & (self.t <= t1 + pad)
        if m.sum() < 2:
            return None
        sl = {k: (getattr(self, k)[m] if getattr(self, k) is not None else None)
              for k in ("t", "lat", "lon", "alt_m", "gs_kt", "track_deg", "leg_start")}
        return Track(self.hex, self.callsign, source=self.source, type=self.type, reg=self.reg,
                     max_gap_s=self.max_gap_s, approx=self.approx, **sl)

    def in_bbox(self, bbox, t0=None, t1=None):
        m = np.ones(len(self.t), bool)
        if t0 is not None:
            m &= (self.t >= t0 - 300) & (self.t <= t1 + 300)
        la0, la1, lo0, lo1 = bbox
        return bool(np.any(m & (self.lat >= la0) & (self.lat <= la1) & (self.lon >= lo0) & (self.lon <= lo1)))


def _load_json_any(src):
    """dict from a dict / bytes / path; transparently gunzips (adsb.lol serves
    trace files gzip-compressed even though they are named .json)."""
    if isinstance(src, dict):
        return src
    if isinstance(src, (str, Path)):
        src = Path(src).read_bytes()
    if src[:2] == b"\x1f\x8b":
        src = gzip.decompress(src)
    return json.loads(src)


def parse_trace(src, source="adsb.lol trace_full") -> Track:
    """Parse a readsb/tar1090 ``trace_full_<hex>.json`` (globe_history or live).

    Row layout (readsb globe_index.c / tar1090 README):
      [0] seconds after ``timestamp``   [1] lat   [2] lon
      [3] altitude ft (baro; geometric if flags&8) | "ground" | null
      [4] ground speed kt  [5] track deg  [6] flags (1 stale, 2 new leg, 4 geom vrate, 8 geom alt)
      [7] vertical rate    [8] details dict or null (has "flight" = callsign)
      [9] source type      [10] geometric altitude ft  [11] geom vrate  [12] IAS  [13] roll
    """
    obj = _load_json_any(src)
    base = float(obj["timestamp"])
    rows = obj.get("trace") or []
    n = len(rows)
    t = np.empty(n)
    lat = np.empty(n)
    lon = np.empty(n)
    alt = np.full(n, np.nan)
    gs = np.full(n, np.nan)
    trk = np.full(n, np.nan)
    leg = np.zeros(n, bool)
    callsign = None
    for i, r in enumerate(rows):
        t[i] = base + float(r[0])
        lat[i], lon[i] = float(r[1]), float(r[2])
        a = r[3]
        flags = int(r[6] or 0) if len(r) > 6 else 0
        geom = r[10] if len(r) > 10 else None
        if a == "ground":
            alt[i] = np.nan
        elif isinstance(geom, (int, float)):
            alt[i] = float(geom) * FT
        elif isinstance(a, (int, float)):
            alt[i] = float(a) * FT
        if len(r) > 4 and isinstance(r[4], (int, float)):
            gs[i] = float(r[4])
        if len(r) > 5 and isinstance(r[5], (int, float)):
            trk[i] = float(r[5])
        leg[i] = bool(flags & 2)
        det = r[8] if len(r) > 8 else None
        if isinstance(det, dict) and det.get("flight") and det["flight"].strip() and "@" not in det["flight"]:
            callsign = det["flight"].strip()
    hexid = str(obj.get("icao", "")).lower() or None
    return Track(hexid, callsign, t, lat, lon, alt, gs, trk, leg, source=source, type=obj.get("t"), reg=obj.get("r"),
                 max_gap_s=120.0)


def parse_readsb_snapshot(obj, source="adsb.lol /v2"):
    """readsb JSON (adsb.lol /v2/..., airplanes.live /v2/point, aircraft.json) ->
    list of point dicts {hex, flight, t, lat, lon, alt_m, gs, track}."""
    now = float(obj.get("now", time.time()))
    if now > 1e11:  # ms
        now /= 1000.0
    out = []
    for a in obj.get("ac") or obj.get("aircraft") or []:
        if a.get("lat") is None or a.get("lon") is None:
            continue
        ab, ag = a.get("alt_baro"), a.get("alt_geom")
        if ab == "ground":
            alt = None
        elif isinstance(ag, (int, float)):
            alt = float(ag) * FT
        elif isinstance(ab, (int, float)):
            alt = float(ab) * FT
        else:
            alt = None
        out.append({"hex": str(a.get("hex", "")).lower().lstrip("~"), "flight": (a.get("flight") or "").strip(),
                    "t": round(now - float(a.get("seen_pos", a.get("seen", 0)) or 0), 1), "lat": a["lat"], "lon": a["lon"],
                    "alt_m": alt, "gs": a.get("gs"), "track": a.get("track"), "type": a.get("t"), "src": source})
    return now, out


def parse_opensky_states(obj):
    """OpenSky /api/states/all -> list of point dicts (see parse_readsb_snapshot)."""
    out = []
    for s in obj.get("states") or []:
        if s[5] is None or s[6] is None:
            continue
        on_ground = bool(s[8])
        alt = s[13] if s[13] is not None else s[7]
        out.append({"hex": str(s[0]).lower(), "flight": (s[1] or "").strip(), "t": float(s[3] or s[4] or obj.get("time", 0)),
                    "lat": float(s[6]), "lon": float(s[5]), "alt_m": None if on_ground or alt is None else float(alt),
                    "gs": None if s[9] is None else float(s[9]) / KT, "track": s[10], "type": None, "src": "opensky"})
    return out


def points_to_tracks(points, source, max_gap_s=60.0):
    """Group point dicts by hex into Tracks (deduplicating identical times)."""
    by = {}
    for p in points:
        by.setdefault(p["hex"] or f"cs:{p['flight']}", []).append(p)
    out = []
    for key, ps in by.items():
        ps = sorted({p["t"]: p for p in ps}.values(), key=lambda p: p["t"])
        if len(ps) < 2:
            continue
        cs = next((p["flight"] for p in reversed(ps) if p.get("flight")), None)
        out.append(Track(None if key.startswith("cs:") else key, cs, np.array([p["t"] for p in ps]),
                         np.array([p["lat"] for p in ps], float), np.array([p["lon"] for p in ps], float),
                         np.array([np.nan if p["alt_m"] is None else p["alt_m"] for p in ps], float),
                         np.array([np.nan if p.get("gs") is None else p["gs"] for p in ps], float),
                         np.array([np.nan if p.get("track") is None else p["track"] for p in ps], float),
                         source=source, type=next((p.get("type") for p in ps if p.get("type")), None), max_gap_s=max_gap_s))
    return out


def merge_tracks(tracks):
    """Merge per aircraft. Same hex -> concatenated. A hex-less track (fixtures)
    whose callsign matches a hex track overlapping in time is dropped in favour
    of the (denser, real) hex track."""
    by_hex = {}
    rest = []
    for tr in tracks:
        if tr is None or len(tr.t) < 2:
            continue
        if tr.hex:
            by_hex.setdefault(tr.hex, []).append(tr)
        else:
            rest.append(tr)
    merged = []
    for hx, trs in by_hex.items():
        if len(trs) == 1:
            merged.append(trs[0])
            continue
        cat = {k: np.concatenate([getattr(t, k) for t in trs]) for k in ("t", "lat", "lon", "alt_m")}
        for k in ("gs_kt", "track_deg"):
            cat[k] = np.concatenate([getattr(t, k) if getattr(t, k) is not None else np.full(len(t.t), np.nan) for t in trs])
        cat["leg_start"] = np.concatenate([t.leg_start for t in trs])
        _, idx = np.unique(cat["t"], return_index=True)
        cat = {k: v[idx] for k, v in cat.items()}
        cs = next((t.callsign for t in trs if t.callsign), None)
        merged.append(Track(hx, cs, source="+".join(sorted({t.source for t in trs})), type=trs[0].type, reg=trs[0].reg,
                            max_gap_s=max(t.max_gap_s for t in trs), approx=all(t.approx for t in trs), **cat))
    names = {}
    for tr in merged:
        if tr.callsign:
            names.setdefault(tr.callsign.strip().upper(), []).append(tr.span())
    # hex-less tracks: first come first served per callsign (providers list their
    # best-timed source first, e.g. fly_2130 before the synthetic flyhendelser timing)
    for tr in rest:
        cs = (tr.callsign or "").strip().upper()
        a, b = tr.span()
        if cs and not cs.startswith("@") and any(s0 <= b and a <= s1 for s0, s1 in names.get(cs, [])):
            continue
        if any(_same_aircraft(tr, m) for m in merged):
            continue
        merged.append(tr)
        if cs:
            names.setdefault(cs, []).append((a, b))
    return merged


def _same_aircraft(a: Track, b: Track, km=6.0, alt_m=600.0):
    """True when two tracks fly together (same aircraft from two sources, e.g. an
    unnamed '@@@@@@@@' fixture entry and the real trace): mean separation over
    their common time span < km and altitude difference < alt_m."""
    s0, s1 = max(a.span()[0], b.span()[0]), min(a.span()[1], b.span()[1])
    if s1 - s0 < 20.0:
        return False
    ts = np.linspace(s0, s1, 5)
    la1, lo1, al1, ok1 = a.at(ts)
    la2, lo2, al2, ok2 = b.at(ts)
    ok = ok1 & ok2
    if ok.sum() < 2:
        return False
    d = haversine(la1[ok], lo1[ok], la2[ok], lo2[ok])
    lo_alt = min(np.nanmin(al1[ok]), np.nanmin(al2[ok])) < 3000.0
    if lo_alt and (a.approx or b.approx):
        return False  # airport traffic: many aircraft close together, fixture timing too coarse to tell
    if a.approx or b.approx:  # synthetic fixture timing/altitude (constant alt, +-15 s)
        km, alt_m = km * 1.5, alt_m * 4
    i0, i1 = np.nonzero(ok)[0][[0, -1]]
    if haversine(la1[i0], lo1[i0], la1[i1], lo1[i1]) > 2.0 and haversine(la2[i0], lo2[i0], la2[i1], lo2[i1]) > 2.0:
        c1 = bearing(la1[i0], lo1[i0], la1[i1], lo1[i1])
        c2 = bearing(la2[i0], lo2[i0], la2[i1], lo2[i1])
        if abs((c1 - c2 + 180.0) % 360.0 - 180.0) > 25.0:
            return False
    return bool(np.mean(d) < km and np.mean(np.abs(al1[ok] - al2[ok])) < alt_m)


# =========================================================================== providers
class ProviderError(Exception):
    pass


@dataclass
class TrackSet:
    tracks: list
    complete: bool            # believed to contain *all* aircraft in bbox during the window
    sources: list = field(default_factory=list)


class AdsbProvider:
    name = "base"

    def tracks(self, t0: float, t1: float, bbox=FETCH_BBOX) -> TrackSet:
        raise NotImplementedError


def _session():
    import requests
    s = requests.Session()
    s.headers["User-Agent"] = "hordewatch/1.0 (hordejakten monitoring; polite; contact via github)"
    return s


def _http_get(session, url, timeout=15.0, **kw):
    try:
        r = session.get(url, timeout=timeout, **kw)
    except Exception as e:
        raise ProviderError(f"{url}: {e.__class__.__name__}: {e}") from e
    if r.status_code != 200:
        raise ProviderError(f"{url}: HTTP {r.status_code}")
    return r


class FixtureProvider(AdsbProvider):
    """Offline provider from local fixture data (see module docstring).

    fly_2130.json ("ekte tid 21.09, CEST", hh:mm:ss) -> +fly2130_offset_s (default 45 s,
    measured against the adsb.lol traces). flyhendelser.json has no timestamps:
    each aircraft's polyline is timed by projecting the points on its course
    (``kurs``) through ``pek`` (position when she reacted = stream time - 22 s,
    default.no's delay estimate) at ground speed ``fart``; altitude = pek altitude.
    """
    name = "fixture"

    def __init__(self, fly2130=None, fly2130_date="2026-09-21", fly2130_offset_s=45.0, flyhendelser=None,
                 flyhendelser_delay_s=22.0, trace_paths=None):
        self.fly2130 = Path(fly2130 or MAGNUS / "public" / "data" / "fly_2130.json")
        self.fly2130_date = fly2130_date
        self.fly2130_offset_s = float(fly2130_offset_s)
        self.flyhendelser = Path(flyhendelser or DEFAULTNO / "flyhendelser.json")
        self.flyhendelser_delay_s = float(flyhendelser_delay_s)
        self.trace_paths = [Path(p) for p in (trace_paths if trace_paths is not None
                                              else sorted(MK_BEVIS_ADSB.glob("trace_*.json")))]
        self._cache = None

    def _load(self):
        if self._cache is not None:
            return self._cache
        blocks = []  # (coverage t0, t1, tracks)
        if self.fly2130.exists():
            d = json.loads(self.fly2130.read_text())
            trs = []
            for f in d["fly"]:
                ts = np.array([to_unix(datetime.fromisoformat(f"{self.fly2130_date}T{p[0]}+02:00")) for p in f["spor"]])
                ts = ts + self.fly2130_offset_s
                a = np.array(f["spor"], dtype=object)
                trs.append(Track(None, f["kallesignal"], ts, a[:, 1].astype(float), a[:, 2].astype(float),
                                 a[:, 3].astype(float) * FT, source="fixture:fly_2130", type=f.get("type"),
                                 max_gap_s=200.0, approx=True))
            if trs:
                t0 = min(t.span()[0] for t in trs)
                t1 = max(t.span()[1] for t in trs)
                blocks.append((t0, t1, trs))
        if self.flyhendelser.exists():
            e = json.loads(self.flyhendelser.read_text())
            cov = {h["navn"]: (to_unix(h["fra"]), to_unix(h["til"])) for h in e.get("hendelser", [])}
            per = {}
            for i, f in enumerate(e["fly"]):
                tr = self._flyhendelse_track(f, i)
                if tr is not None:
                    per.setdefault(f["h"], []).append(tr)
            for h, trs in per.items():
                if h in cov:
                    blocks.append((cov[h][0], cov[h][1], trs))
        traces = []
        for p in self.trace_paths:
            try:
                traces.append(parse_trace(p, source=f"fixture:{p.name}"))
            except Exception as ex:
                log.warning("fixture trace %s unreadable: %s", p, ex)
        self._cache = (blocks, traces)
        return self._cache

    def _flyhendelse_track(self, f, idx):
        if not f.get("pek") or f.get("kurs") is None or not f.get("fart") or f["h"] not in FLYHENDELSER_STREAM:
            return None
        t_react = to_unix(FLYHENDELSER_STREAM[f["h"]]) - self.flyhendelser_delay_s
        la0, lo0, ft = f["pek"]
        if ft is None:
            return None
        pts = [(la0, lo0)] + [tuple(p) for p in f.get("spor") or []]
        cos0 = np.cos(np.radians(la0))
        ux, uy = np.sin(np.radians(f["kurs"])), np.cos(np.radians(f["kurs"]))
        v = f["fart"] * KT
        ts, las, los = [], [], []
        for la, lo in pts:
            along_m = ((lo - lo0) * 111320.0 * cos0 * ux + (la - la0) * 110570.0 * uy)
            ts.append(t_react + along_m / v)
            las.append(la)
            los.append(lo)
        if len(pts) < 3:  # extrapolate +-120 s along the course so a lone pek point is usable
            for s in (-120.0, 120.0):
                d = v * s
                las.append(la0 + d * uy / 110570.0)
                los.append(lo0 + d * ux / (111320.0 * cos0))
                ts.append(t_react + s)
        ts = np.array(ts)
        o = np.argsort(ts)
        ts, las, los = ts[o], np.array(las)[o], np.array(los)[o]
        keep = np.concatenate([[True], np.diff(ts) > 1.0])
        k = f["k"] if f["k"] and "@" not in f["k"] else f"@{idx}"
        return Track(None, k, ts[keep], las[keep], los[keep], np.full(keep.sum(), ft * FT),
                     gs_kt=np.full(keep.sum(), float(f["fart"])), source="fixture:flyhendelser", type=f.get("t"),
                     max_gap_s=400.0, approx=True)

    def tracks(self, t0, t1, bbox=FETCH_BBOX):
        blocks, traces = self._load()
        out, complete, srcs = [], False, []
        for c0, c1, trs in blocks:
            overlap = max(0.0, min(t1, c1) - max(t0, c0))
            if overlap <= 0:
                continue
            if overlap >= 0.8 * (t1 - t0):
                complete = True
            out += [t for t in trs if t.in_bbox(bbox, t0, t1)]
            srcs.append(trs[0].source)
        for tr in traces:
            s0, s1 = tr.span()
            if s0 <= t1 and t0 <= s1 and tr.in_bbox(bbox, t0, t1):
                w = tr.window(t0, t1, pad=300)
                if w is not None:
                    out.append(w)
                    srcs.append(tr.source)
        return TrackSet(merge_tracks(out), complete, sorted(set(srcs)))


class TraceCacheProvider(AdsbProvider):
    """Every trace_full / trace_recent file under a directory tree (downloads by
    AdsbLolHistoryProvider / release provider, or files dropped in by hand)."""
    name = "trace_cache"

    def __init__(self, root):
        self.root = Path(root)
        self._parsed = {}

    def tracks(self, t0, t1, bbox=FETCH_BBOX):
        out = []
        days = {from_unix(t).strftime("%Y%m%d") for t in (t0, t1)}
        files = []
        for d in days:
            files += list((self.root / d).glob("trace_*.json*"))
        files += list(self.root.glob("trace_*.json*"))
        for p in files:
            key = (str(p), p.stat().st_mtime)
            if key not in self._parsed:
                try:
                    self._parsed[key] = parse_trace(p, source=f"trace:{p.name}")
                except Exception as e:
                    log.warning("bad trace file %s: %s", p, e)
                    self._parsed[key] = None
            tr = self._parsed[key]
            if tr is not None and tr.in_bbox(bbox, t0, t1):
                w = tr.window(t0, t1, pad=300)
                if w is not None:
                    out.append(w)
        return TrackSet(merge_tracks(out), False, ["trace_cache"] if out else [])


class LiveRecordProvider(AdsbProvider):
    """Reads snapshots written by LiveRecorder (hourly gzip JSONL files). Complete
    when successful polls cover the window without gaps > max_poll_gap_s."""
    name = "live_record"

    def __init__(self, root, max_poll_gap_s=45.0):
        self.root = Path(root)
        self.max_poll_gap_s = max_poll_gap_s

    def _files(self, t0, t1):
        h = int(t0 // 3600) * 3600
        while h <= t1:
            dt = from_unix(h)
            p = self.root / dt.strftime("%Y%m%d") / f"{dt:%H}.jsonl.gz"
            if p.exists():
                yield p
            h += 3600

    def tracks(self, t0, t1, bbox=FETCH_BBOX):
        pts, polls = [], []
        for p in self._files(t0 - 300, t1 + 300):
            try:
                with gzip.open(p, "rt") as f:
                    for line in f:
                        try:
                            rec = json.loads(line)
                        except ValueError:
                            continue  # truncated line from a crash
                        if not (t0 - 300 <= rec["now"] <= t1 + 300):
                            continue
                        polls.append(rec["now"])
                        pts += [dict(zip(("hex", "flight", "t", "lat", "lon", "alt_m", "gs", "track"), a), type=None)
                                for a in rec["ac"]]
            except (OSError, EOFError) as e:
                log.warning("live record %s unreadable: %s", p, e)
        polls = np.sort(np.array(polls + [], float))
        complete = False
        if len(polls) >= 2:
            inwin = np.concatenate([[t0], polls[(polls > t0) & (polls < t1)], [t1]])
            complete = polls[0] <= t0 + self.max_poll_gap_s and polls[-1] >= t1 - self.max_poll_gap_s and \
                np.max(np.diff(inwin)) <= self.max_poll_gap_s * 2
        return TrackSet(points_to_tracks(pts, "live_record"), complete, ["live_record"] if pts else [])

    def hexes(self, t0, t1):
        ts = self.tracks(t0, t1)
        return sorted({t.hex for t in ts.tracks if t.hex})


class AdsbLolHistoryProvider(AdsbProvider):
    """globe.adsb.lol globe_history trace_full per hex (ODbL). Needs the hexes
    (from recorded snapshots or config ``hexes``); ~50-500 kB gzip per aircraft-day.
    Downloads are cached under <cache>/traces/YYYYMMDD/."""
    name = "adsblol_history"
    URL = "https://globe.adsb.lol/globe_history/{Y}/{m}/{d}/traces/{h2}/trace_full_{hex}.json"
    LIVE_URL = "https://globe.adsb.lol/data/traces/{h2}/trace_full_{hex}.json"

    def __init__(self, cache_root, hex_sources=(), hexes=(), timeout=20.0):
        self.cache_root = Path(cache_root)
        self.hex_sources = list(hex_sources)
        self.static_hexes = [h.lower() for h in hexes]
        self.timeout = timeout
        self._s = None

    def _get_trace(self, hx, day: datetime):
        dest = self.cache_root / day.strftime("%Y%m%d") / f"trace_full_{hx}.json.gz"
        if dest.exists():
            return parse_trace(dest, source=f"adsb.lol:{hx}")
        self._s = self._s or _session()
        urls = [self.URL.format(Y=day.year, m=f"{day.month:02d}", d=f"{day.day:02d}", h2=hx[-2:], hex=hx)]
        if (datetime.now(UTC) - day).total_seconds() < 36 * 3600:
            urls.append(self.LIVE_URL.format(h2=hx[-2:], hex=hx))
        last = None
        for url in urls:
            try:
                r = _http_get(self._s, url, timeout=self.timeout)
                raw = r.content
                data = raw if raw[:2] == b"\x1f\x8b" else gzip.compress(raw)
                tr = parse_trace(data, source=f"adsb.lol:{hx}")
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                return tr
            except Exception as e:
                last = e
        raise ProviderError(str(last))

    def tracks(self, t0, t1, bbox=FETCH_BBOX):
        hexes = set(self.static_hexes)
        for src in self.hex_sources:
            try:
                hexes |= set(src.hexes(t0, t1))
            except Exception:
                pass
        out = []
        days = sorted({from_unix(t).replace(hour=0, minute=0, second=0, microsecond=0) for t in (t0, t1)})
        for hx in sorted(hexes):
            for day in days:
                try:
                    tr = self._get_trace(hx, day)
                except ProviderError as e:
                    warn_once(f"adsblol:{hx}", "adsb.lol globe_history unavailable for %s (%s); continuing without it", hx, e)
                    continue
                w = tr.window(t0, t1, pad=300)
                if w is not None and w.in_bbox(bbox, t0, t1):
                    out.append(w)
        return TrackSet(merge_tracks(out), False, ["adsb.lol globe_history"] if out else [])


class OpenSkyProvider(AdsbProvider):
    """OpenSky Network state vectors at regular times inside the window.

    Auth: OAuth2 client credentials (``client_id``/``client_secret``, current API)
    or legacy basic auth (``username``/``password``). Anonymous users only get the
    present state, so historical windows need an account. Responses are cached
    as JSON per request under <cache>/opensky/.
    """
    name = "opensky"
    API = "https://opensky-network.org/api/states/all"
    TOKEN = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

    def __init__(self, cache_root, client_id=None, client_secret=None, username=None, password=None,
                 step_s=15.0, max_calls=60, timeout=20.0):
        self.cache_root = Path(cache_root)
        self.cid, self.csecret, self.user, self.pw = client_id, client_secret, username, password
        self.step_s, self.max_calls, self.timeout = step_s, max_calls, timeout
        self._s = None
        self._token = (None, 0.0)

    def _auth(self):
        if self.cid and self.csecret:
            tok, exp = self._token
            if tok is None or time.time() > exp - 60:
                r = self._s.post(self.TOKEN, data={"grant_type": "client_credentials", "client_id": self.cid,
                                                   "client_secret": self.csecret}, timeout=self.timeout)
                if r.status_code != 200:
                    raise ProviderError(f"OpenSky token HTTP {r.status_code}")
                j = r.json()
                self._token = (j["access_token"], time.time() + float(j.get("expires_in", 1800)))
            return {"headers": {"Authorization": f"Bearer {self._token[0]}"}}
        if self.user and self.pw:
            return {"auth": (self.user, self.pw)}
        return {}

    MAX_AGE_S = 3600.0 - 120.0     # REST state vectors: registered users <= 1 h back (older -> HTTP 400)
    TIME_TOL_S = 20.0              # a response whose "time" differs more was not served for the asked time

    def tracks(self, t0, t1, bbox=FETCH_BBOX):
        la0, la1, lo0, lo1 = bbox
        times = np.arange(np.floor(t0), t1 + 1, self.step_s)
        covered = len(times) <= self.max_calls
        times = times[: self.max_calls]
        pts, ok_calls = [], 0
        for t in times:
            dest = self.cache_root / from_unix(t).strftime("%Y%m%d") / f"states_{int(t)}_{la0:.1f}_{lo0:.1f}.json"
            try:
                if dest.exists():
                    obj = json.loads(dest.read_text())
                else:
                    if not ((self.cid and self.csecret) or (self.user and self.pw)):
                        raise ProviderError("anonymous OpenSky access only serves the present state (time is ignored); "
                                            "set opensky client_id/client_secret")
                    if time.time() - t > self.MAX_AGE_S:
                        raise ProviderError("OpenSky /states/all serves at most 1 h of history; window is older "
                                            "(use the live recorder or adsb.lol history)")
                    self._s = self._s or _session()
                    auth = self._auth()
                    r = _http_get(self._s, self.API, timeout=self.timeout,
                                  params={"time": int(t), "lamin": la0, "lamax": la1, "lomin": lo0, "lomax": lo1}, **auth)
                    obj = r.json()
                    if abs(float(obj.get("time") or 0.0) - t) > self.TIME_TOL_S:
                        raise ProviderError(f"OpenSky answered for time {obj.get('time')} instead of {int(t)}")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(json.dumps(obj))
                pts += parse_opensky_states(obj)
                ok_calls += 1
            except Exception as e:
                warn_once("opensky", "OpenSky unavailable (%s); continuing without it", e)
                break
        # complete only when every requested time was served and the requests covered the whole window
        complete = covered and ok_calls == len(times) and ok_calls > 0
        return TrackSet(points_to_tracks(pts, "opensky", max_gap_s=3 * self.step_s), complete,
                        ["opensky"] if pts else [])


class AdsbLolReleaseProvider(AdsbProvider):
    """Full-day history from adsb.lol's GitHub releases (repo adsblol/globe_history_<YYYY>,
    one release per day whose tag contains YYYY.MM.DD, split tar parts .tar.aa, .tar.ab, ...).

    The parts are streamed back-to-back into ``tarfile`` (mode 'r|'), and only
    ``traces/**/trace_full_*.json`` members with a point inside the bbox are
    kept (written to <cache>/traces/YYYYMMDD/). A marker file records that the day
    was scanned, after which the trace cache is *complete* for that day.
    Multi-GB per day: enable only on a machine with bandwidth (``providers``
    entry ``adsblol_release``). Release naming was not verifiable from the dev
    container; failures are logged and ignored.
    """
    name = "adsblol_release"
    API = "https://api.github.com/repos/adsblol/globe_history_{Y}/releases"

    def __init__(self, cache_root, timeout=60.0, token=None):
        self.cache_root = Path(cache_root)
        self.timeout = timeout
        self.token = token

    class _Concat(io.RawIOBase):
        def __init__(self, responses):
            self.it = iter(responses)
            self.cur = None

        def readable(self):
            return True

        def readinto(self, b):
            while True:
                if self.cur is None:
                    try:
                        self.cur = next(self.it)
                    except StopIteration:
                        return 0
                n = self.cur.raw.readinto(b)
                if n:
                    return n
                self.cur = None

    def _scan_day(self, day: datetime, bbox):
        outdir = self.cache_root / day.strftime("%Y%m%d")
        marker = outdir / ".release_scanned"
        if marker.exists():
            return
        s = _session()
        if self.token:
            s.headers["Authorization"] = f"Bearer {self.token}"
        tag = day.strftime("%Y.%m.%d")
        rel = None
        for page in range(1, 6):
            r = _http_get(s, self.API.format(Y=day.year), params={"per_page": 100, "page": page}, timeout=self.timeout)
            rels = r.json()
            hits = [x for x in rels if tag in x.get("tag_name", "")]
            # several releases per day are possible (prod / staging, re-uploads): prefer prod, then the newest
            hits.sort(key=lambda x: x.get("published_at") or "", reverse=True)
            hits.sort(key=lambda x: "prod" not in x.get("tag_name", ""))          # stable: prod first, newest first
            rel = hits[0] if hits else None
            if rel or not rels:
                break
        if not rel:
            raise ProviderError(f"no adsblol release for {tag}")
        assets = sorted((a for a in rel.get("assets", []) if ".tar" in a["name"]), key=lambda a: a["name"])
        if not assets:
            raise ProviderError(f"release {rel.get('tag_name')} has no tar parts")

        def resps():
            for a in assets:
                r = s.get(a["browser_download_url"], stream=True, timeout=self.timeout)
                if r.status_code != 200:
                    raise ProviderError(f"{a['name']}: HTTP {r.status_code}")
                yield r
        outdir.mkdir(parents=True, exist_ok=True)
        la0, la1, lo0, lo1 = bbox
        n = 0
        with tarfile.open(fileobj=io.BufferedReader(self._Concat(resps()), 1 << 20), mode="r|") as tar:
            for m in tar:
                if not m.isfile() or "trace_full_" not in m.name:
                    continue
                raw = tar.extractfile(m).read()
                try:
                    tr = parse_trace(raw)
                except Exception:
                    continue
                if tr.in_bbox(bbox):
                    (outdir / (Path(m.name).name + ".gz")).write_bytes(raw if raw[:2] == b"\x1f\x8b" else gzip.compress(raw))
                    n += 1
        marker.write_text(json.dumps({"release": rel.get("tag_name"), "traces": n}))

    def tracks(self, t0, t1, bbox=FETCH_BBOX):
        days = sorted({from_unix(t).replace(hour=0, minute=0, second=0, microsecond=0) for t in (t0, t1)})
        try:
            for d in days:
                self._scan_day(d, FETCH_BBOX)
        except Exception as e:
            warn_once("adsblol_release", "adsb.lol GitHub release history unavailable (%s)", e)
            return TrackSet([], False, [])
        ts = TraceCacheProvider(self.cache_root).tracks(t0, t1, bbox)
        return TrackSet(ts.tracks, True, ["adsb.lol github release"])


def resolve_tracks(providers, t0, t1, bbox=FETCH_BBOX) -> TrackSet:
    """Query providers in order, merging tracks, until one declares the window complete."""
    allt, srcs, complete = [], [], False
    for p in providers:
        try:
            ts = p.tracks(t0, t1, bbox)
        except Exception as e:  # a provider bug must not stop the monitor
            warn_once(f"provider:{getattr(p, 'name', p)}", "ADS-B provider %s failed: %s", getattr(p, "name", p), e)
            continue
        allt += ts.tracks
        srcs += ts.sources
        if ts.complete:
            complete = True
            break
    return TrackSet(merge_tracks(allt), complete, srcs)


# =========================================================================== live recorder
class LiveRecorder(threading.Thread):
    """Polls readsb-style point APIs and appends compact snapshots to
    <root>/YYYYMMDD/HH.jsonl.gz: {"now": t, "src": ..., "ac": [[hex, flight, t, lat, lon, alt_m, gs, track], ...]}.

    Point APIs return only the present, so continuous recording is what makes
    the live path work (an event is evaluated minutes later against the
    recording). Default: adsb.lol then airplanes.live, both /v2 radius 250 nm
    around two centres covering southern Norway. ~20-40 MB/day at 10 s.
    """
    SOURCES = {"adsb.lol": "https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{nm}",
               "airplanes.live": "https://api.airplanes.live/v2/point/{lat}/{lon}/{nm}"}
    CENTRES = [(59.9, 8.6, 250), (62.6, 9.8, 250)]

    def __init__(self, root, poll_s=10.0, sources=("adsb.lol", "airplanes.live"), centres=None, bbox=FETCH_BBOX):
        super().__init__(daemon=True, name="adsb-live-recorder")
        self.root = Path(root)
        self.poll_s = poll_s
        self.sources = list(sources)
        self.centres = centres or self.CENTRES
        self.bbox = bbox
        self.stop_event = threading.Event()
        self.ok_polls = 0

    def poll_once(self, session):
        la0, la1, lo0, lo1 = self.bbox
        acs, now_all, used = {}, None, None
        for src in self.sources:
            try:
                for lat, lon, nm in self.centres:
                    r = _http_get(session, self.SOURCES[src].format(lat=lat, lon=lon, nm=nm), timeout=10)
                    now, pts = parse_readsb_snapshot(r.json(), source=src)
                    now_all = now
                    for p in pts:
                        if la0 <= p["lat"] <= la1 and lo0 <= p["lon"] <= lo1:
                            acs[p["hex"]] = [p["hex"], p["flight"], p["t"], round(p["lat"], 5), round(p["lon"], 5),
                                             None if p["alt_m"] is None else round(p["alt_m"]), p["gs"], p["track"]]
                used = src
                break
            except (ProviderError, ValueError, KeyError, TypeError) as e:   # unreachable, or not readsb JSON
                warn_once(f"live:{src}", "live ADS-B source %s unusable (%s); trying next", src, e)
                acs = {}
        if used is None:
            return False
        dt = from_unix(now_all)
        p = self.root / dt.strftime("%Y%m%d") / f"{dt:%H}.jsonl.gz"
        p.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(p, "at") as f:
            f.write(json.dumps({"now": now_all, "src": used, "ac": list(acs.values())}) + "\n")
        self.ok_polls += 1
        return True

    def run(self):
        s = _session()
        while not self.stop_event.is_set():
            t = time.monotonic()
            try:
                self.poll_once(s)
            except Exception as e:  # never die
                warn_once("live:loop", "live ADS-B recorder error: %s", e)
            self.stop_event.wait(max(0.5, self.poll_s - (time.monotonic() - t)))

    def stop(self):
        self.stop_event.set()


# =========================================================================== geometry
def isa_sound_speed(z_m):
    T = np.where(np.asarray(z_m) < 11000.0, 288.15 - 0.0065 * np.asarray(z_m), 216.65)
    return np.sqrt(1.4 * 287.05 * T)


def sound_speed_eff(alt_m, z_obs=OBSERVER_M, mode="isa"):
    """Effective speed of sound along a straight ray observer -> aircraft:
    harmonic mean of the ISA profile (travel time = s * mean(1/c) because z is
    linear along the ray). ~318 m/s for 10 km, 337 m/s near the ground.
    ``mode`` may be a number to force a constant (e.g. 343)."""
    if not isinstance(mode, str):
        return np.full(np.shape(alt_m), float(mode))
    fr = np.linspace(0.0, 1.0, 9)
    z = z_obs + (np.asarray(alt_m, float)[..., None] - z_obs) * fr
    return 1.0 / np.mean(1.0 / isa_sound_speed(z), axis=-1)


def image_tilt(az_deg, elev_deg, heading_deg):
    """Tilt from vertical (deg, negative = image left) of a pointing arm aimed at
    (az, elev), seen by a level camera looking along ``heading_deg``."""
    h = np.radians(elev_deg)
    d = np.radians(np.asarray(az_deg) - heading_deg)
    return np.degrees(np.arctan2(np.cos(h) * np.sin(d), np.sin(h)))


def pixel_to_azel(u, v, w, h, focal_px, heading_deg, pitch_deg=0.0, roll_deg=0.0):
    """Pinhole camera: pixel (u right, v down) -> (azimuth, elevation) in degrees.
    Pitch positive = camera tilted up; roll positive = clockwise image rotation."""
    x = (np.asarray(u, float) - (w - 1) / 2.0) / focal_px
    y = ((h - 1) / 2.0 - np.asarray(v, float)) / focal_px
    ps, th, ph = np.radians(heading_deg), np.radians(pitch_deg), np.radians(roll_deg)
    fwd = np.array([np.sin(ps), np.cos(ps), 0.0])
    right = np.array([np.cos(ps), -np.sin(ps), 0.0])
    up = np.array([0.0, 0.0, 1.0])
    fwd, up = np.cos(th) * fwd + np.sin(th) * up, -np.sin(th) * fwd + np.cos(th) * up
    right, up = np.cos(ph) * right - np.sin(ph) * up, np.sin(ph) * right + np.cos(ph) * up
    d = fwd[:, None] * 1.0 + right[:, None] * np.atleast_1d(x)[None, :] + up[:, None] * np.atleast_1d(y)[None, :]
    az = (np.degrees(np.arctan2(d[0], d[1])) + 360.0) % 360.0
    el = np.degrees(np.arctan2(d[2], np.hypot(d[0], d[1])))
    return az, el


def angular_sep(az1, el1, az2, el2):
    a1, e1, a2, e2 = map(np.radians, (az1, el1, az2, el2))
    c = np.sin(e1) * np.sin(e2) + np.cos(e1) * np.cos(e2) * np.cos(a1 - a2)
    return np.degrees(np.arccos(np.clip(c, -1.0, 1.0)))


def _window(clats, clons, lat, lon, rkm):
    """Index slices of a regular lat/lon grid within +-rkm of a point."""
    dla = rkm / 111.2
    dlo = rkm / (111.2 * max(np.cos(np.radians(lat)), 0.1))
    i0 = max(int(np.floor((lat - dla - clats[0]) / (clats[1] - clats[0]))), 0)
    i1 = min(int(np.ceil((lat + dla - clats[0]) / (clats[1] - clats[0]))) + 1, len(clats))
    j0 = max(int(np.floor((lon - dlo - clons[0]) / (clons[1] - clons[0]))), 0)
    j1 = min(int(np.ceil((lon + dlo - clons[0]) / (clons[1] - clons[0]))) + 1, len(clons))
    return slice(i0, i1), slice(j0, j1)


def audible_prob(slant_km, s50_km=16.0, width_km=2.5):
    return 1.0 / (1.0 + np.exp((np.asarray(slant_km) - s50_km) / width_km))


# =========================================================================== delay priors
def latency_prior(clock=None, calib=None, rng=(15.0, 60.0), margin=10.0, step=2.5):
    """Discrete prior over stream latency L (s): calibrated N(mu, sigma) when the
    calibration is flagged well determined, else uniform on ``rng`` with Gaussian
    shoulders of width ``margin``. Returns (values, weights) with sum(w) = 1."""
    if calib and calib.get("well_determined") and calib.get("latency_s") is not None:
        mu, sd = float(calib["latency_s"]), max(float(calib.get("latency_sigma_s", 5.0)), 1.5)
        v = np.arange(max(0.0, mu - 4 * sd), mu + 4 * sd + 1e-9, min(step, sd / 2))
        w = np.exp(-0.5 * ((v - mu) / sd) ** 2)
    else:
        lo, hi = rng
        v = np.arange(max(0.0, lo - 3 * margin), hi + 3 * margin + 1e-9, step)
        d = np.where(v < lo, lo - v, np.where(v > hi, v - hi, 0.0))
        w = np.exp(-0.5 * (d / margin) ** 2)
    return v, w / w.sum()


def with_reaction(vals, w, reaction_s, step=2.5):
    """Convolve a delay prior with a uniform reaction delay [0, reaction_s]."""
    if reaction_s <= 0:
        return vals, w
    r = np.arange(0.0, reaction_s + 1e-9, step)
    D = (vals[:, None] + r[None, :]).ravel()
    W = np.repeat(w, len(r)) / len(r)
    grid = np.round(D / step) * step
    u, inv = np.unique(grid, return_inverse=True)
    ww = np.zeros(len(u))
    np.add.at(ww, inv, W)
    return u, ww / ww.sum()


# =========================================================================== event likelihoods
def positions_at(tracks, t, min_alt_m):
    """[(track, lat, lon, alt_m)] for airborne aircraft at time t."""
    out = []
    for tr in tracks:
        la, lo, al, ok = tr.at(t)
        if ok[0] and al[0] >= min_alt_m:
            out.append((tr, float(la[0]), float(lo[0]), float(al[0])))
    return out


def sighting_prob(CL, CO, tracks, t_capture, delays, dweights, q=0.85, floor=0.05, mid=25.0, scale=3.0,
                  min_alt_m=900.0, tilt_obs=None, tilt_sigma=12.0, tilt_weight=0.6, heading=219.6, tilt_sign_p=1.0):
    """P(she points up at t_capture | box at (CL, CO)) marginalised over delay D.

    Identical geometry to hordejakt.layers.aircraft.event_prob (4/3-earth
    elevation angle, observer at OBSERVER_M, logistic canopy visibility), but
    evaluated only where vis() is non-negligible and with an optional arm-tilt
    factor (see module docstring); ``tilt_sign_p`` is the probability that the
    sign of ``tilt_obs`` is right (1 = signed tilt known exactly)."""
    clats, clons = CL[:, 0], CO[0, :]
    emin = max(mid - 7 * scale, 2.0)
    P = np.zeros(CL.shape)
    for D, w in zip(delays, dweights):
        miss = np.ones(CL.shape)
        for tr, la, lo, al in positions_at(tracks, t_capture - D, min_alt_m):
            h = al - OBSERVER_M
            if h <= 0:
                continue
            rkm = h / 1000.0 / np.tan(np.radians(emin)) + 3.0
            si, sj = _window(clats, clons, la, lo, rkm)
            cl, co = CL[si, sj], CO[si, sj]
            g = haversine(cl, co, la, lo)
            el = elevation_angle(g, h)
            p = q * vis(el, mid, scale)
            if tilt_obs is not None:
                tau = image_tilt(bearing(cl, co, la, lo), el, heading)
                g = tilt_sign_p * np.exp(-0.5 * ((tau - tilt_obs) / tilt_sigma) ** 2)
                if tilt_sign_p < 1.0:
                    g = g + (1.0 - tilt_sign_p) * np.exp(-0.5 * ((tau + tilt_obs) / tilt_sigma) ** 2)
                p = p * ((1 - tilt_weight) + tilt_weight * g)
            miss[si, sj] *= 1.0 - p
        P += w * (floor + (1.0 - floor) * (1.0 - miss))
    return P / np.sum(dweights)


def light_prob(CL, CO, tracks, pts, delays, dweights, q=0.85, floor=0.1, sigma=3.0, min_alt_m=300.0):
    """P(light track seen | x). ``pts`` = [(t_capture, az_obs, el_obs), ...]."""
    P = np.zeros(CL.shape)
    for D, w in zip(delays, dweights):
        miss = np.ones(CL.shape)
        by_track = {}
        for tc, az_o, el_o in pts:
            for tr, la, lo, al in positions_at(tracks, tc - D, min_alt_m):
                by_track.setdefault(tr.key, []).append((la, lo, al, az_o, el_o))
        for key, obs in by_track.items():
            if len(obs) < len(pts):
                continue  # aircraft not present for the whole track
            sq = np.zeros(CL.shape)
            for la, lo, al, az_o, el_o in obs:
                g = haversine(CL, CO, la, lo)
                el = elevation_angle(g, al - OBSERVER_M)
                az = bearing(CL, CO, la, lo)
                sq += angular_sep(az, el, az_o, el_o) ** 2
            miss *= 1.0 - q * np.exp(-0.5 * (sq / len(obs)) / sigma ** 2)
        P += w * (floor + (1.0 - floor) * (1.0 - miss))
    return P / np.sum(dweights)


@dataclass
class CPA:
    slant_km: np.ndarray      # slant distance at closest approach
    t_peak: np.ndarray        # unix time the loudness peak arrives at x (real time)
    sigma_t: np.ndarray       # timing sd (s)
    idx: tuple = None         # (si, sj) window into the coarse grid, or None for point lists


def audio_cpa(track, lats, lons, t0, t1, dt=2.0, max_km=40.0, sound_speed="isa", sigma_det=4.0, width_frac=0.3,
              min_alt_m=300.0):
    """Closest approach of ``track`` to every location (lats/lons arrays, any shape)
    inside [t0, t1]. CPAs at the window edges (approach/recession only) are NaN."""
    ts = np.arange(t0, t1 + 1e-9, dt)
    la, lo, al, ok = track.at(ts)
    ok &= al >= min_alt_m
    if ok.sum() < 3:
        return None
    ts, la, lo, al = ts[ok], la[ok], lo[ok], al[ok]
    lats = np.asarray(lats, float)
    lons = np.asarray(lons, float)
    shape = lats.shape
    flat_la, flat_lo = lats.ravel(), lons.ravel()
    near = (flat_la > la.min() - max_km / 111.2) & (flat_la < la.max() + max_km / 111.2)
    cosl = np.cos(np.radians(np.mean(la)))
    near &= (flat_lo > lo.min() - max_km / (111.2 * cosl)) & (flat_lo < lo.max() + max_km / (111.2 * cosl))
    s_out = np.full(flat_la.shape, np.nan)
    t_out = np.full(flat_la.shape, np.nan)
    sd_out = np.full(flat_la.shape, np.nan)
    idx = np.nonzero(near)[0]
    if len(idx):
        for c0 in range(0, len(idx), 4096):
            ii = idx[c0:c0 + 4096]
            g = haversine(flat_la[ii, None], flat_lo[ii, None], la[None, :], lo[None, :]) * 1000.0
            dz = (al[None, :] - OBSERVER_M) - g ** 2 / (2 * R_EARTH * 1000.0)
            s2 = g ** 2 + dz ** 2
            k = np.argmin(s2, axis=1)
            interior = (k > 0) & (k < len(ts) - 1)
            kk = np.clip(k, 1, len(ts) - 2)
            r = np.arange(len(ii))
            y0, y1, y2 = s2[r, kk - 1], s2[r, kk], s2[r, kk + 1]
            den = y0 - 2 * y1 + y2
            # parabolic refinement (exact for straight flight: s^2 is quadratic in t) -- only
            # across evenly spaced neighbours (samples dropped below min_alt / in gaps break that)
            even = np.isclose(ts[kk + 1] - ts[kk], dt) & np.isclose(ts[kk] - ts[kk - 1], dt)
            off = np.where((den > 0) & even, 0.5 * (y0 - y2) / np.where(den > 0, den, 1), 0.0)
            off = np.clip(off, -1, 1)
            tc = ts[kk] + off * dt
            smin = np.sqrt(np.maximum(y1 - 0.25 * (y0 - y2) * off, 0.0))
            c = sound_speed_eff(al[kk], mode=sound_speed)
            v = np.maximum(track.speed_at(tc), 50.0)
            s_out[ii] = np.where(interior, smin / 1000.0, np.nan)
            t_out[ii] = np.where(interior, tc + smin / c, np.nan)
            sd_out[ii] = np.where(interior, np.sqrt(sigma_det ** 2 + (width_frac * smin / v) ** 2), np.nan)
    return CPA(s_out.reshape(shape), t_out.reshape(shape), sd_out.reshape(shape))


SQRT2PI = np.sqrt(2.0 * np.pi)


def audio_prob_per_latency(cpas, t_obs, lat_vals, bg_rate=4.0 / 3600.0, window_s=180.0, s50=16.0, width=2.5):
    """Timing likelihood ratio r(x, L) of one audio peak at stream time ``t_obs`` for every
    audio latency L -> array (len(L), *shape); 1 = uninformative (see module docstring):

        lambda(t | x, L) = b + sum_a P_aud(s_a) N(t; t_peak_a + L, sigma_a)
        r(x, L) = 2 W lambda(t_obs | x, L) / integral_{t_obs-W}^{t_obs+W} lambda(t | x, L) dt

    ``bg_rate`` b is per second. CPAs outside their computation window are NaN and
    contribute to neither term, so the CPA window must cover t_obs - L -+ W for all L."""
    shape = cpas[0].slant_km.shape
    W = float(window_s)
    b = max(float(bg_rate), 1e-9)
    out = np.full((len(lat_vals),) + shape, 2.0 * W * b)       # numerator 2W lambda, background part
    den = np.full((len(lat_vals),) + shape, 2.0 * W * b)       # expected detections in the window
    flat_out = out.reshape(len(lat_vals), -1)
    flat_den = den.reshape(len(lat_vals), -1)
    L = np.asarray(lat_vals, float)[:, None]
    for c in cpas:
        s = c.slant_km.ravel()
        idx = np.nonzero(np.isfinite(s) & np.isfinite(c.t_peak.ravel()))[0]
        if not len(idx):
            continue
        pa = audible_prob(s[idx], s50, width)
        keep = pa > 1e-4
        idx, pa = idx[keep], pa[keep]
        if not len(idx):
            continue
        mu = c.t_peak.ravel()[idx][None, :] + L            # stream time of this aircraft's peak at x
        sd = np.maximum(c.sigma_t.ravel()[idx], 0.5)[None, :]
        z = (t_obs - mu) / sd
        flat_out[:, idx] += 2.0 * W * pa * np.exp(-0.5 * z * z) / (sd * SQRT2PI)
        flat_den[:, idx] += pa * (ndtr((t_obs + W - mu) / sd) - ndtr((t_obs - W - mu) / sd))
    return out / den


def audio_prob_from_cpas(cpas, t_obs, lat_vals, lat_w, bg_rate=4.0 / 3600.0, window_s=180.0, s50=16.0, width=2.5):
    """Evidence of one peak marginalised over the audio latency: sum_L w(L) r(x, L)
    (1 = uninformative) for a list of CPA arrays (same shape). ``lat_vals`` are *audio* latencies."""
    if not cpas:
        return None
    PL = audio_prob_per_latency(cpas, t_obs, lat_vals, bg_rate, window_s, s50, width)
    w = np.asarray(lat_w, float)
    return np.tensordot(w / w.sum(), PL, axes=1)


def audio_track_window(t_obs, lat_vals, window_s=180.0):
    """Track time span [t0, t1] (unix) that audio_cpa needs so that every aircraft whose
    peak can fall inside t_obs - L -+ W (any L in ``lat_vals``) has an interior CPA:
    the CPA precedes the peak by s/c <= ~110 s at audible ranges."""
    lv = np.asarray(lat_vals, float)
    return t_obs - float(lv.max()) - window_s - 140.0, t_obs - float(lv.min()) + window_s + 30.0


def prior_on(grid_vals, Lv, Lw):
    """Re-express a discrete latency prior (Lv, Lw) on another grid (linear interpolation, renormalised)."""
    w = np.interp(grid_vals, Lv, Lw, left=0.0, right=0.0)
    if w.sum() <= 0:
        w = np.ones_like(grid_vals)
    return w / w.sum()


# =========================================================================== latency calibration
def calibrate_latency(events, cand_lats, cand_lons, cand_w, tracks_for, grid=None, bg_rate=4.0 / 3600.0,
                      window_s=180.0, s50=16.0, width=2.5, sound_speed="isa", sys_floor_s=3.0, min_events=3,
                      match_ratio=3.0, sigma_det=4.0, width_frac=0.3, dt=4.0):
    """Joint stream-latency estimate from audio peaks (see module docstring).

    events: [{"id", "t_obs" (unix capture time of the peak)}]; tracks_for(event)
    -> list[Track] covering audio_track_window(t_obs, grid, window_s). Returns a dict
    with latency_s, latency_sigma_s, posterior grid, n_matched and well_determined.
    """
    grid = np.arange(0.0, 120.0 + 1e-9, 0.5) if grid is None else np.asarray(grid)
    cand_lats, cand_lons = np.asarray(cand_lats, float), np.asarray(cand_lons, float)
    cand_w = np.asarray(cand_w, float) / np.sum(cand_w)
    K = len(cand_lats)
    loglik = np.zeros((K, len(grid)))  # sum_e log r_e(x_k, L)
    per_event = []
    for ev in events:
        t_obs = ev["t_obs"]
        w0, w1 = audio_track_window(t_obs, grid, window_s)
        cpas = []
        for tr in tracks_for(ev):
            c = audio_cpa(tr, cand_lats, cand_lons, w0, w1, dt=dt, sound_speed=sound_speed, sigma_det=sigma_det,
                          width_frac=width_frac)
            if c is not None and np.isfinite(c.slant_km).any():
                cpas.append(c)
        if cpas:
            p_ev = audio_prob_per_latency(cpas, t_obs, grid, bg_rate, window_s, s50, width).T   # (K, len(grid))
        else:
            p_ev = np.ones((K, len(grid)))
        loglik += np.log(p_ev)
        per_event.append((ev, p_ev))
    # J(L) = sum_k w_k exp(loglik_k(L))
    m = loglik.max()
    J = np.log(np.maximum(np.tensordot(cand_w, np.exp(loglik - m), axes=1), 1e-300)) + m
    post = np.exp(J - J.max())
    post /= post.sum()
    i = int(np.argmax(post))
    L_map = float(grid[i])
    near = np.abs(grid - L_map) <= 30.0
    pn = post[near] / post[near].sum()
    sd_stat = float(np.sqrt(np.sum(pn * (grid[near] - L_map) ** 2)))
    mass10 = float(post[np.abs(grid - L_map) <= 10.0].sum())
    # which events are explained by an aircraft (not the floor) at the MAP latency and best candidate
    with np.errstate(divide="ignore"):
        k_best = int(np.argmax(loglik[:, i] + np.log(cand_w)))
    matched = [ev["id"] for ev, p in per_event if p[k_best, i] >= match_ratio]
    contrast = float(J[i] - np.median(J))
    sd = float(np.hypot(max(sd_stat, 0.5), sys_floor_s))
    well = (len(events) >= min_events and len(matched) >= min_events and sd_stat <= 8.0 and mass10 >= 0.7
            and contrast >= 3.0)
    return {"latency_s": L_map, "latency_sigma_s": sd, "sd_stat_s": sd_stat, "mass_within_10s": mass10,
            "contrast": contrast, "n_events": len(events), "n_matched": len(matched), "matched": matched,
            "best_candidate": [float(cand_lats[k_best]), float(cand_lons[k_best])], "well_determined": bool(well),
            "grid_s": grid.tolist()[:: 4], "posterior": post.tolist()[:: 4]}


# =========================================================================== bridge
def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


class AircraftBridge(Analyzer):
    """Turns gesture/audio/light observations into aircraft_<event>.npz layers and calibrates latency.

    Config (analyzer_config.aircraft_bridge, or the global ``bridges:`` section):
      providers   list of names (see module docstring) or provider objects; add "fixture" for offline tests
      live_record start the LiveRecorder thread (default: when source.type == live)
      async       process events in a worker thread (default True; tests use False)
      opensky     {client_id, client_secret} / {username, password}
      hexes       extra ICAO hexes to pull from adsb.lol globe_history
      plus the model constants in DEFAULTS.
    """
    name = "aircraft_bridge"
    tick_interval_s = 20.0

    def __init__(self, config=None):
        super().__init__(config)
        self.providers = None
        self._recorder = None
        self._pool = None
        self._futures = {}
        self._calib_future = None
        self._last_calib = 0.0

    # ----------------------------------------------------------- setup
    def get(self, key):
        return cfg_get(self.config, key)

    def build_providers(self):
        if self.providers is not None:
            return self.providers
        names = [p for p in self.get("providers") if isinstance(p, str)]
        root = cache_dir(self.config, "adsb") if set(names) - {"fixture"} else None
        out = []
        live = LiveRecordProvider(root / "live") if root is not None else None
        for p in self.get("providers"):
            if not isinstance(p, str):
                out.append(p)
            elif p == "fixture":
                out.append(FixtureProvider(**(setting(self.config, "fixture", {}) or {})))
            elif p == "trace_cache":
                out.append(TraceCacheProvider(root / "traces"))
            elif p == "live_record":
                out.append(live)
            elif p == "adsblol_history":
                out.append(AdsbLolHistoryProvider(root / "traces", hex_sources=[live], hexes=self.get("hexes") or []))
            elif p == "opensky":
                out.append(OpenSkyProvider(root / "opensky", **(setting(self.config, "opensky", {}) or {})))
            elif p == "adsblol_release":
                out.append(AdsbLolReleaseProvider(root / "traces", token=setting(self.config, "github_token")))
            else:
                log.warning("unknown ADS-B provider %s", p)
        self.providers = out
        return out

    def _ensure_recorder(self, ctx):
        want = self.get("live_record")
        if want is None:
            want = ((self.config.get("_global") or {}).get("source") or {}).get("type") == "live"
        if want and self._recorder is None:
            self._recorder = LiveRecorder(cache_dir(self.config, "adsb") / "live", poll_s=float(self.get("poll_s")))
            self._recorder.start()
            log.info("ADS-B live recorder started -> %s", self._recorder.root)

    # ----------------------------------------------------------- events
    def _loops(self, db, t0, t1):
        return [r for r in db.observations(kind="audio_loop", since=from_unix(t0 - 3600), until=from_unix(t1 + 3600))]

    @staticmethod
    def _loop_intervals(rows):
        """audio_loop rows -> [(t_start, t_end)] real times of the repeated segments. The
        contract only guarantees ts (start); a duration_s / len_s / end field widens it."""
        out = []
        for r in rows:
            t0 = to_unix(r["ts"])
            v = r.get("value") or {}
            dur = _num(v.get("duration_s"), None) or _num(v.get("len_s"), None) or 0.0
            t1 = t0 + max(dur, 0.0)
            if isinstance(v.get("end"), str):
                try:
                    t1 = max(t1, to_unix(parse_iso(v["end"])))
                except ValueError:
                    pass
            out.append((t0, t1))
        return out

    def _is_looped(self, t_real, intervals):
        m = float(self.get("loop_margin_s"))
        return any(a - m <= t_real <= b + m for a, b in intervals)

    def collect_events(self, db, clock, now=None):
        """Cluster trigger observations into events (list of dicts, oldest first).

        Each row's phenomenon capture time is ts + the latency its analyzer used
        (see common.observation_latencies): ts_capture is the capture of the frame the
        row was *emitted* on, which for gesture 'summary' rows is the end of the
        pointing episode and for aircraft_light the frame that closed the track. The
        latency is kept in row['_lat'] to convert other real times in the value
        (track points, peak_ts). A cluster ends after a gap > cluster_s or when it
        spans max_cluster_s (a detector firing continuously must not hold one event
        open forever)."""
        now = time.time() if now is None else now
        since = from_unix(now - float(self.get("lookback_h")) * 3600)
        rows = db.observations(kind=list(TRIGGERS), since=since)
        lats = observation_latencies(db, rows, clock)
        items = []
        for r, lat in zip(rows, lats):
            r = dict(r, _lat=float(lat))
            tc = to_unix(r["ts"]) + lat
            if r["kind"] == "audio_aircraft":
                pk = r["value"].get("peak_ts")
                if isinstance(pk, str):
                    try:
                        tc = to_unix(parse_iso(pk)) + lat
                    except ValueError:
                        pass
                elif isinstance(pk, (int, float)):
                    tc = (float(pk) + lat) if pk > 1e9 else (to_unix(r["ts"]) + float(pk) + lat)
            items.append((tc, r))
        items.sort(key=lambda x: x[0])
        events, cur = [], None
        gap, span = float(self.get("cluster_s")), float(self.get("max_cluster_s"))
        for tc, r in items:
            if cur is None or tc - cur["t_last"] > gap or tc - cur["t_first"] > span:
                cur = {"t_first": tc, "t_last": tc, "obs": []}
                events.append(cur)
            cur["obs"].append((tc, r))
            cur["t_last"] = tc
        for ev in events:
            ev["id"] = stamp(ev["t_first"])
            ev["kinds"] = sorted({r["kind"] for _, r in ev["obs"]})
        return events

    def is_weak(self, ev):
        """Gesture-only event whose detections are all low-confidence (see module docstring)."""
        kinds = {r["kind"] for _, r in ev["obs"]}
        if kinds != {"gesture_point_up"}:
            return False
        return max(float(r.get("confidence") or 0.0) for _, r in ev["obs"]) < float(self.get("gesture_strong_conf"))

    def event_group(self, ev):
        for g, ts in BUILTIN_EVENTS.items():
            if abs(ev["t_first"] - to_unix(ts)) <= DEDUP_S:
                return g
        if self.is_weak(ev):
            return f"hw_aircraft_lowconf_{local_date(ev['t_first'])}"
        return f"hw_aircraft_{ev['id']}"

    def _latency(self, ctx):
        calib = None
        try:
            calib = ctx.db.calibration("latency_calibration")
        except Exception:
            pass
        return latency_prior(ctx.clock, calib, tuple(self.get("latency_range_s")), float(self.get("latency_margin_s")),
                             float(self.get("latency_step_s")))

    def _camera(self, value):
        g = (self.config.get("_global") or {}).get("camera") or {}
        w = float(value.get("w") or value.get("image_w") or self.get("image_w"))
        h = float(value.get("h") or value.get("image_h") or self.get("image_h"))
        f = value.get("focal_px") or g.get("focal_px")
        f = float(f) if f else float(self.get("camera_focal_px_1280")) * w / 1280.0
        heading = float(setting(self.config, "camera_heading_deg", None) or g.get("heading_deg")
                        or DEFAULTS["camera_heading_deg"])
        return w, h, f, heading, float(self.get("camera_pitch_deg")), float(self.get("camera_roll_deg"))

    def _tilt(self, value):
        """(signed image tilt of the arm in deg, P(sign right)) or (None, 0).
        The gesture analyzer's angle is unsigned; its 'side' is the tilt direction only
        for the arm-only path (tip vs. base), otherwise the side of the body the raised
        arm is on (MediaPipe wrist vs. shoulder midpoint, limb tip vs. core centre)."""
        if value.get("tilt_deg_image") is not None:
            t = _num(value["tilt_deg_image"])
            return (t, 0.95) if t is not None else (None, 0.0)
        a = _num(value.get("arm_angle_deg_from_vertical"))
        if a is None:
            return None, 0.0
        side = str(value.get("side", "")).lower()
        p = 0.9 if value.get("arm_only") else 0.75
        if "left" in side:
            return -abs(a), p
        if "right" in side:
            return abs(a), p
        return None, 0.0

    def process_event(self, ev, lat_prior, loops=(), audio_offset=0.0, write=True):
        """Compute the event layer. Returns {status, loglik, meta, path, matches}.
        Pure w.r.t. the DB (safe in a worker thread)."""
        clats, clons = coarse_axes(BOX, COARSE_DLAT, COARSE_DLON)
        CL, CO = np.meshgrid(clats, clons, indexing="ij")
        Lv, Lw = lat_prior
        rel_cfg = {**DEFAULTS["reliability"], **(self.get("reliability") or {})}   # partial overrides allowed
        by_kind = {}
        for tc, r in ev["obs"]:
            by_kind.setdefault(r["kind"], []).append((tc, r))
        # audio: drop looped segments
        loop_iv = self._loop_intervals(loops)
        if "audio_aircraft" in by_kind:
            keep = [(tc, r) for tc, r in by_kind["audio_aircraft"] if not self._is_looped(to_unix(r["ts"]), loop_iv)]
            if keep:
                by_kind["audio_aircraft"] = keep
            else:
                by_kind.pop("audio_aircraft")
        if not by_kind:
            return {"status": "skipped", "reason": "looped audio only"}
        # gesture timing: positions at t_c - D, D = L + u, u in [-dwell, reaction + sampling gap]
        # (she saw it just before the onset frame and follows it while pointing)
        if "gesture_point_up" in by_kind:
            gobs = by_kind["gesture_point_up"]
            g_tc = gobs[0][0]
            durs = [_num(r["value"].get("duration_s"), 0.0) or 0.0 for _, r in gobs]
            dwell = float(np.clip(max(durs + [gobs[-1][0] - g_tc]), 0.0, float(self.get("max_dwell_s"))))
            gaps = [_num(r["value"].get("sampling_gap_s"), 0.0) or 0.0 for _, r in gobs
                    if r["value"].get("phase", "onset") == "onset"]
            gap = float(np.clip(max(gaps) if gaps else 0.0, 0.0, 30.0))
            gD, gW = with_reaction(Lv - dwell, Lw, float(self.get("reaction_s")) + gap + dwell)
        # ADS-B window: sightings need t_capture - D for every D; audio needs every aircraft
        # whose peak can fall into the conditional window (see audio_track_window)
        wins = []
        if "gesture_point_up" in by_kind:
            wins.append((g_tc - float(gD.max()) - 30.0, g_tc - float(gD.min()) + 30.0))
        if "aircraft_light" in by_kind:
            wins.append((ev["t_first"] - float(Lv.max()) - 30.0, ev["t_last"] - float(Lv.min()) + 120.0))
        W_a = float(self.get("audio_window_s"))
        if "audio_aircraft" in by_kind:
            a0, a1 = audio_track_window(0.0, AUDIO_L_GRID, W_a)
            wins.append((ev["t_first"] + a0, ev["t_last"] + a1))
        t0, t1 = min(w[0] for w in wins), max(w[1] for w in wins)
        ts = resolve_tracks(self.build_providers(), t0, t1)
        if not ts.tracks and not ts.complete:
            return {"status": "no_data", "reason": "no ADS-B source covers the window"}
        logP = np.zeros(CL.shape)
        audio_logPL = None
        rels, descs, matches = [], [], []
        min_alt = float(self.get("min_alt_ft")) * FT
        q, floor = float(self.get("q")), float(self.get("floor"))
        mid, scale = float(self.get("vis_mid")), float(self.get("vis_scale"))
        if "gesture_point_up" in by_kind:
            tilt, sign_p = None, 0.0
            for _, r in sorted(gobs, key=lambda x: x[1]["value"].get("phase") == "summary"):   # onset rows first
                tilt, sign_p = self._tilt(r["value"])
                if tilt is not None:
                    break
            heading = self._camera({})[3]
            P = sighting_prob(CL, CO, ts.tracks, g_tc, gD, gW, q=q, floor=floor, mid=mid, scale=scale,
                              min_alt_m=min_alt, tilt_obs=tilt, tilt_sigma=float(self.get("tilt_sigma_deg")),
                              tilt_weight=float(self.get("tilt_weight")), heading=heading, tilt_sign_p=sign_p)
            logP += np.log(P)
            conf = max(float(r["confidence"] if r.get("confidence") is not None else 0.5) for _, r in gobs)
            # detection confidence scales the reliability: 0.6 -> r_kind, 0.25 (arm-only fallback) -> 0.42 r_kind
            rels.append(rel_cfg["gesture_point_up"] * float(np.clip(conf / 0.6, 0.3, 1.15)))
            descs.append(f"points up at {from_unix(g_tc):%Y-%m-%d %H:%M:%S}Z stream (conf {conf:.2f}"
                         + (f", {dwell:.0f} s" if dwell > 0 else "")
                         + (f", arm tilt {tilt:+.0f} deg p_sign {sign_p:.2f})" if tilt is not None else ")"))
        if "aircraft_light" in by_kind:
            pts = []
            for tc, r in by_kind["aircraft_light"]:
                w, h, f, heading, pitch, roll = self._camera(r["value"])
                lat_used = float(r.get("_lat", tc - to_unix(r["ts"])))   # real -> capture for track times
                trk = r["value"].get("track") or []
                sel = trk if len(trk) <= 3 else [trk[0], trk[len(trk) // 2], trk[-1]]
                for p in sel:
                    tt, x, y = p[0], float(p[1]), float(p[2])
                    if isinstance(tt, str):
                        tcp = to_unix(parse_iso(tt)) + lat_used
                    elif tt is not None and float(tt) > 1e9:
                        tcp = float(tt) + lat_used
                    else:
                        tcp = tc + float(tt or 0.0)
                    az, el = pixel_to_azel(x, y, w, h, f, heading, pitch, roll)
                    pts.append((tcp, float(az[0]), float(el[0])))
            if pts:
                Lv2, Lw2 = Lv[::2], Lw[::2] / Lw[::2].sum()
                P = light_prob(CL, CO, ts.tracks, pts, Lv2, Lw2, q=q, floor=float(self.get("light_floor")),
                               sigma=float(self.get("light_sigma_deg")))
                logP += np.log(P)
                rels.append(rel_cfg["aircraft_light"])
                descs.append(f"light in frame {len(pts)} pts first az {pts[0][1]:.0f} el {pts[0][2]:.1f}")
        if "audio_aircraft" in by_kind:
            best = max(by_kind["audio_aircraft"], key=lambda x: _num(x[1]["value"].get("snr_db"), 0.0))
            t_obs = best[0]
            w0, w1 = audio_track_window(t_obs, AUDIO_L_GRID, W_a)
            cpas = []
            for tr in ts.tracks:
                c = audio_cpa(tr, CL, CO, w0, w1, dt=float(self.get("audio_cpa_dt_s")),
                              sound_speed=self.get("sound_speed"), sigma_det=float(self.get("audio_sigma_det_s")),
                              width_frac=float(self.get("audio_width_frac")))
                if c is not None and np.isfinite(c.slant_km).any():
                    cpas.append(c)
            if cpas:
                PL = audio_prob_per_latency(cpas, t_obs, AUDIO_L_GRID, bg_rate=float(self.get("audio_bg_rate_per_h")) / 3600.0,
                                            window_s=W_a, s50=float(self.get("audible_s50_km")),
                                            width=float(self.get("audible_width_km")))
            else:
                PL = np.ones((len(AUDIO_L_GRID),) + CL.shape)    # no audible aircraft anywhere: no information
            P = np.tensordot(prior_on(AUDIO_L_GRID + audio_offset, Lv, Lw), PL, axes=1)
            logP += np.log(P)
            if set(by_kind) == {"audio_aircraft"}:
                audio_logPL = np.log(PL).astype(np.float32)
            t_real_best = to_unix(best[1]["ts"])
            n_loops = sum(1 for a, _ in loop_iv if abs(a - t_real_best) < 6 * 3600)   # loops passed in: +-1 h
            rels.append(0.5 if n_loops >= 3 else rel_cfg["audio_aircraft"])
            descs.append(f"jet noise peak {from_unix(t_obs):%H:%M:%S}Z stream (snr {best[1]['value'].get('snr_db')})")
        if not ts.complete:
            # we may be missing aircraft: only the positive part is trustworthy
            rels = [r * 0.8 for r in rels]
        ll = upsample(logP, clats, clons, GRID)
        weak = self.is_weak(ev)
        rel = float(np.clip(max(rels), 0.2, 0.5) if weak else np.clip(max(rels), 0.5, 0.75))
        group = self.event_group(ev)
        name = f"hw_aircraft_{ev['id']}"
        meta = dict(name=name, reliability=rel, independence_group=group,
                    description="hordewatch: " + "; ".join(descs) + f"; {len(ts.tracks)} aircraft"
                                + ("" if ts.complete else " (ADS-B coverage incomplete)"),
                    sources=ts.sources or ["ADS-B"])
        path = None
        daily = None
        # a flat layer (no aircraft visible/audible anywhere) is exactly neutral in the robust
        # mixture (s = 1 -> L = 1): do not write a multi-MB file or report a spurious match
        flat = float(np.ptp(logP)) < 1e-3
        if flat:
            meta["description"] += " -- no informative geometry, no layer written"
        if write and audio_logPL is not None:
            daily = self._accumulate_audio_day(ev, audio_logPL, (Lv, Lw), audio_offset)
            if daily is not None:
                path, meta = daily
        if write and daily is None and not flat:
            path = write_layer(layers_dir(self.config) / f"aircraft_{ev['id']}.npz", ll, grid=GRID,
                               extra={"event_id": ev["id"], "kinds": sorted(by_kind), "t_capture": from_unix(ev["t_first"]),
                                      "complete": ts.complete, "n_aircraft": len(ts.tracks)}, **meta)
            if audio_logPL is not None:
                self._accumulate_audio_day(ev, None, (Lv, Lw), audio_offset, per_event_path=path)
        # which aircraft explains the event best at the layer's maximum
        if not flat:
            i, j = np.unravel_index(np.nanargmax(logP), logP.shape)
            audio_only = set(by_kind) == {"audio_aircraft"}
            matches.append(self.explain(ts.tracks, ev["t_first"], float(CL[i, j]), float(CO[i, j]), Lv, Lw,
                                        extra_delay=35.0 - 0.5 * float(self.get("reaction_s")) if audio_only else 0.0))
        return {"status": "ok", "loglik": ll, "coarse": logP, "meta": meta, "path": str(path) if path else None,
                "matches": [m for m in matches if m], "n_tracks": len(ts.tracks), "complete": ts.complete}

    def _accumulate_audio_day(self, ev, logPL, prior, audio_offset, per_event_path=None):
        """Daily joint layer for audio-only events with a *shared* latency:
            log J_day(x) = log sum_L w(L) prod_e P_e(x | L)
        The running sum S(x, L) = sum_e log P_e(x | L) lives in <cache>/adsb/audio_daily/<date>.npz.
        audio_mode 'event': never merge; 'daily': always; 'auto' (default): per-event layers
        until more than audio_daily_threshold audio events in a day, then one daily layer
        replaces them (bounding the damage if the day's audio turns out to be replayed).
        Returns (path, meta) when the daily layer was (re)written, else None.
        With logPL None only records ``per_event_path`` for a later merge."""
        date = local_date(ev["t_first"])
        acc_path = cache_dir(self.config, "adsb") / "audio_daily" / f"{date}.npz"
        acc_path.parent.mkdir(parents=True, exist_ok=True)
        S, info = None, {"events": [], "per_event": {}}
        if acc_path.exists():
            d = np.load(acc_path)
            S, info = d["S"].astype(np.float32), json.loads(str(d["info"]))
        if logPL is None:
            info["per_event"][ev["id"]] = str(per_event_path)
        elif ev["id"] not in info["events"]:
            S = logPL if S is None else S + logPL
            info["events"].append(ev["id"])
        mode = self.get("audio_mode")
        n = len(info["events"])
        merge = S is not None and (mode == "daily" or (mode == "auto" and n > int(self.get("audio_daily_threshold"))))
        tmp = acc_path.with_name(acc_path.name + ".tmp")
        with open(tmp, "wb") as f:
            np.savez_compressed(f, S=S if S is not None else np.zeros((0,), np.float32), info=np.array(json.dumps(info)))
        tmp.replace(acc_path)
        if not merge or logPL is None:
            return None
        Lv, Lw = prior
        w = prior_on(AUDIO_L_GRID + audio_offset, Lv, Lw)
        with np.errstate(divide="ignore"):
            lw = np.log(w)[:, None, None]
        m = np.max(S + lw, axis=0)
        logJ = m + np.log(np.sum(np.exp(S + lw - m), axis=0))
        clats, clons = coarse_axes(BOX, COARSE_DLAT, COARSE_DLON)
        ll = upsample(logJ, clats, clons, GRID)
        meta = dict(name=f"hw_aircraft_audio_{date}", reliability=0.5, independence_group=f"hw_aircraft_audio_{date}",
                    description=f"hordewatch: {n} aircraft sounds on {date} with a shared stream latency",
                    sources=["ADS-B", "stream audio"])
        path = write_layer(layers_dir(self.config) / f"aircraft_audio_{date}.npz", ll, grid=GRID,
                           extra={"events": info["events"], "n_events": n}, **meta)
        for eid, pth in list(info["per_event"].items()):
            try:
                Path(pth).unlink()
            except OSError:
                pass
            info["per_event"].pop(eid)
        with open(tmp, "wb") as f:
            np.savez_compressed(f, S=S, info=np.array(json.dumps(info)))
        tmp.replace(acc_path)
        return str(path), meta

    def explain(self, tracks, t_capture, lat, lon, Lv, Lw, extra_delay=0.0):
        """Highest-elevation aircraft seen from (lat, lon) at the prior-mean delay (for sounds
        ``extra_delay`` ~ s/c moves the look-up back to the closest approach)."""
        D = float(np.sum(Lv * Lw)) + 0.5 * float(self.get("reaction_s")) + extra_delay
        best = None
        for tr, la, lo, al in positions_at(tracks, t_capture - D, 300.0):
            g = float(haversine(lat, lon, la, lo))
            el = float(elevation_angle(g, al - OBSERVER_M))
            if best is None or el > best["elev_deg"]:
                best = {"callsign": tr.label, "icao": tr.hex, "alt_ft": round(al / FT), "elev_deg": round(el, 1),
                        "az_deg": round(float(bearing(lat, lon, la, lo)), 1), "ground_km": round(g, 1),
                        "at": [round(lat, 4), round(lon, 4)], "delay_s": round(D, 1), "approx_timing": tr.approx}
        return best

    # ----------------------------------------------------------- calibration
    def audio_events_for_calibration(self, db, clock, now=None):
        evs = []
        loops = None
        for ev in self.collect_events(db, clock, now):
            aud = [(tc, r) for tc, r in ev["obs"] if r["kind"] == "audio_aircraft"]
            if not aud:
                continue
            if loops is None:
                loops = self._loop_intervals(db.observations(kind="audio_loop"))
            aud = [(tc, r) for tc, r in aud if not self._is_looped(to_unix(r["ts"]), loops)]
            if not aud:
                continue
            tc, r = max(aud, key=lambda x: _num(x[1]["value"].get("snr_db"), 0.0))
            evs.append({"id": ev["id"], "t_obs": tc})
        return evs

    def run_calibration(self, db, clock, candidates=None, now=None, events=None, audio_offset=None):
        """Joint latency fit (see calibrate_latency). ``events``/``audio_offset`` may be
        passed pre-read so this can run in the worker thread without touching the DB."""
        evs = events if events is not None else self.audio_events_for_calibration(db, clock, now)
        if len(evs) < int(self.get("calib_min_events")):
            return {"status": "insufficient", "n_events": len(evs)}
        if candidates is None:
            candidates = posterior_candidates(setting(self.config, "posterior_path"), setting(self.config, "hotspots_path"))
        if candidates is None:
            return {"status": "no_candidates"}
        la, lo, w = candidates
        provs = self.build_providers()
        if audio_offset is None:
            audio_offset = float((db.calibration("audio_offset_s") if db else 0.0) or 0.0)

        W_a = float(self.get("audio_window_s"))
        grid = np.arange(0.0, 120.0 + 1e-9, 0.5)

        def tracks_for(ev):
            return resolve_tracks(provs, *audio_track_window(ev["t_obs"], grid, W_a)).tracks

        res = calibrate_latency(evs, la, lo, w, tracks_for, grid=grid,
                                bg_rate=float(self.get("audio_bg_rate_per_h")) / 3600.0, window_s=W_a,
                                s50=float(self.get("audible_s50_km")), width=float(self.get("audible_width_km")),
                                sound_speed=self.get("sound_speed"), min_events=int(self.get("calib_min_events")),
                                sigma_det=float(self.get("audio_sigma_det_s")),
                                width_frac=float(self.get("audio_width_frac")), dt=float(self.get("audio_cpa_dt_s")))
        res["audio_offset_s"] = audio_offset
        res["latency_audio_s"] = res["latency_s"]
        res["latency_s"] = res["latency_s"] + audio_offset   # video latency = audio latency + audio offset
        res["updated"] = from_unix(time.time()).isoformat()
        res["status"] = "ok"
        return res

    def apply_calibration(self, ctx, res):
        db = ctx.db
        db.set_calibration("latency_calibration", json.loads(dumps(res)))
        if res.get("well_determined"):
            db.set_calibration("latency_s", float(res["latency_s"]))
            db.set_calibration("latency_sigma_s", float(res["latency_sigma_s"]))
            if ctx.clock is not None:
                ctx.clock.latency_s = float(res["latency_s"])
                ctx.clock.latency_sigma_s = float(res["latency_sigma_s"])
            db.add_event(from_unix(time.time()), "latency_calibrated",
                         f"stream latency {res['latency_s']:.1f} +- {res['latency_sigma_s']:.1f} s from "
                         f"{res['n_matched']}/{res['n_events']} aircraft sounds", {k: res[k] for k in
                                                                                   ("latency_s", "latency_sigma_s", "n_matched", "n_events", "matched")})

    # ----------------------------------------------------------- tick
    def on_tick(self, ctx):
        self._ensure_recorder(ctx)
        db = ctx.db
        now = time.time()
        state = load_state(db, self.name, {"done": {}, "pending": {}})
        out = []
        # collect finished async jobs
        for eid, fut in list(self._futures.items()):
            if fut.done():
                self._futures.pop(eid)
                try:
                    out += self._finish(ctx, state, eid, fut.result(), now, getattr(fut, "event", None))
                except Exception as e:
                    log.exception("aircraft event %s failed: %s", eid, e)
        events = self.collect_events(db, ctx.clock, now)
        prior = self._latency(ctx)
        audio_offset = float(db.calibration("audio_offset_s", 0.0) or 0.0)
        for ev in events:
            eid = ev["id"]
            if eid in state["done"] or eid in self._futures:
                continue
            if now < ev["t_last"] + float(self.get("settle_s")):
                continue
            pend = state["pending"].get(eid)
            if pend and now - pend["last"] < float(self.get("retry_s")):
                continue
            loops = self._loops(db, ev["t_first"], ev["t_last"]) if "audio_aircraft" in ev["kinds"] else []
            if self.get("async"):
                self._futures[eid] = self._pool_get().submit(self._safe_process, ev, prior, loops, audio_offset)
                self._futures[eid].event = ev
            else:
                out += self._finish(ctx, state, eid, self._safe_process(ev, prior, loops, audio_offset), now, ev)
        if self._calib_future is not None and self._calib_future.done():
            fut, self._calib_future = self._calib_future, None
            try:
                res = fut.result()
                if res.get("status") == "ok":
                    self.apply_calibration(ctx, res)
            except Exception as e:
                log.exception("latency calibration failed: %s", e)
        if self.get("calibrate") and self._calib_future is None and now - self._last_calib >= float(self.get("calib_every_s")):
            self._last_calib = now
            n_audio = sum(1 for e in events if "audio_aircraft" in e["kinds"])
            if n_audio >= int(self.get("calib_min_events")) and n_audio != state.get("calib_n_audio"):
                state["calib_n_audio"] = n_audio
                if self.get("async"):
                    # same single worker as the events: providers are never used from two threads
                    evs = self.audio_events_for_calibration(db, ctx.clock, now)
                    off = float(db.calibration("audio_offset_s", 0.0) or 0.0)
                    self._calib_future = self._pool_get().submit(self.run_calibration, None, None, None, now, evs, off)
                else:
                    try:
                        res = self.run_calibration(db, ctx.clock, now=now)
                        if res.get("status") == "ok":
                            self.apply_calibration(ctx, res)
                    except Exception as e:
                        log.exception("latency calibration failed: %s", e)
        self._prune_state(state, now)
        save_state(db, self.name, state)
        return out

    def _prune_state(self, state, now):
        """Forget events older than the lookback (they can no longer be collected) so the
        state blob in the calibration table does not grow without bound."""
        cutoff = now - float(self.get("lookback_h")) * 3600.0 - 86400.0
        for key in ("done", "pending"):
            for eid in list(state.get(key, {})):
                try:
                    t = datetime.strptime(eid, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC).timestamp()
                except ValueError:
                    continue
                if t < cutoff:
                    state[key].pop(eid, None)

    def _pool_get(self):
        if self._pool is None:
            self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="aircraft-bridge")
        return self._pool

    def _safe_process(self, ev, prior, loops, audio_offset):
        try:
            return self.process_event(ev, prior, loops, audio_offset)
        except Exception as e:
            log.exception("aircraft event %s: %s", ev["id"], e)
            return {"status": "error", "reason": str(e)}

    def _finish(self, ctx, state, eid, res, now, ev=None):
        st = res.get("status")
        if st in ("ok", "skipped"):
            state["done"][eid] = {"status": st, "path": res.get("path"), "t": now}
            state["pending"].pop(eid, None)
        elif st in ("no_data", "error"):
            p = state["pending"].setdefault(eid, {"tries": 0, "last": now})
            p["tries"] += 1
            p["last"] = now
            if p["tries"] >= int(self.get("max_tries")):
                state["done"][eid] = {"status": st, "reason": res.get("reason"), "t": now}
                state["pending"].pop(eid, None)
        if st != "ok":
            return []
        obs = []
        lat_s = float(getattr(ctx.clock, "latency_s", 30.0) or 30.0)
        t_ev = from_unix((ev["t_first"] if ev else now) - lat_s)   # estimated real time of the reaction
        for m in res["matches"]:
            obs.append(Observation("aircraft_match", t_ev, {**m, "event_id": eid, "layer": res["path"]},
                                   analyzer=self.name, confidence=float(res["meta"]["reliability"]),
                                   notes=res["meta"]["description"][:500]))
        if res.get("path"):   # no dashboard alert for a flat (uninformative) event
            ctx.db.add_event(t_ev, "aircraft_layer", f"aircraft evidence {eid}: {res['meta']['description'][:200]}",
                             {"event_id": eid, "path": res["path"], "matches": res["matches"],
                              "reliability": res["meta"]["reliability"], "group": res["meta"]["independence_group"]})
        return obs


# =========================================================================== CLI
def main(argv=None):
    """Manual use:
        python -m hordewatch.bridges.adsb event --kind gesture_point_up --stream-time 2026-09-21T21:29:38+02:00 --provider fixture
        python -m hordewatch.bridges.adsb record          # run the live recorder in the foreground
    """
    ap = argparse.ArgumentParser(prog="hordewatch.bridges.adsb")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("event", help="build a layer for one manual event")
    e.add_argument("--kind", default="gesture_point_up", choices=TRIGGERS)
    e.add_argument("--stream-time", required=True, help="ISO time the reaction was seen on the stream")
    e.add_argument("--provider", nargs="*", default=["fixture", "trace_cache", "live_record", "adsblol_history", "opensky"])
    e.add_argument("--tilt", type=float, help="arm tilt in image, deg from vertical (negative = image left)")
    e.add_argument("--layers-dir")
    e.add_argument("--cache-dir", help="ADS-B cache / daily audio accumulator root (default data/hordewatch)")
    r = sub.add_parser("record", help="record live ADS-B snapshots")
    r.add_argument("--poll", type=float, default=10.0)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    if a.cmd == "record":
        rec = LiveRecorder(cache_dir({}, "adsb") / "live", poll_s=a.poll)
        rec.run()
        return
    cfg = {"providers": a.provider, "async": False}
    if a.layers_dir:
        cfg["layers_dir"] = a.layers_dir
    if a.cache_dir:
        cfg["cache_dir"] = a.cache_dir
    b = AircraftBridge(cfg)
    tc = to_unix(parse_iso(a.stream_time))
    val = {} if a.tilt is None else {"tilt_deg_image": a.tilt}
    row = {"id": 0, "ts": from_unix(tc - 30), "ts_capture": from_unix(tc), "kind": a.kind, "analyzer": "manual",
           "confidence": 0.8, "value": val}
    ev = {"t_first": tc, "t_last": tc, "obs": [(tc, row)], "id": stamp(tc), "kinds": [a.kind]}
    res = b.process_event(ev, latency_prior(rng=tuple(DEFAULTS["latency_range_s"])))
    print(json.dumps({k: v for k, v in res.items() if k not in ("loglik", "coarse")}, indent=1, default=str))


if __name__ == "__main__":
    main()
