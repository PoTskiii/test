"""Night sky: stars, aircraft lights, the moon and artificial lights (analyzer name: ``night``).

Active in IR/night mode. Also active in colour mode when the sun is > 4 deg below the
horizon at the approximate site and the sky region is dark. Everything runs on the sky
region: the learned day-time sky mask from the sky analyzer, eroded by 4 px so that
canopy edges do not count. Without a mask, the top ``fallback_sky_frac`` of the frame is
used. Only the rows that contain the region are processed, at full resolution, because
stars are 1-3 px.

Point sources
-------------
Background = 11x11 median (removes point sources, keeps skyglow gradients and canopy
silhouettes). The residual is matched-filtered with a Gaussian of the PSF scale. Peaks are
5x5 local maxima above max(5 robust sigma, ``min_amp``). For each peak: centroid and
second moments are taken in a 7x7 window of the residual (clipped at 2 sigma), with flux =
sum of the residual. Extended sources (PSF sigma > 3 px: glow, lamps, the moon) are not
stars.

Stars vs. everything else
-------------------------
* Stars are static between frames. The sidereal rate is 15 deg/h x cos(dec), about 0.3 px
  per 5 s at 1280 px / 70 deg. So the star field is detected on the *median* of the last
  ``stack_frames`` frames within ``stack_max_span_s`` (15 s), which removes moving lights, single-frame speckle and
  compression flicker and gains ~sqrt(N) SNR.
* Stars are not static over tens of minutes (~60 px in 20 min near the celestial
  equator). A source still within 1 px of a position seen > ``hot_px_after_s`` (20 min)
  ago is a hot pixel, a lamp or a sky hole in the canopy, and is dropped from
  ``star_field`` (``n_static_rejected``). The camera faces SW, so the celestial pole,
  where real stars barely move, is out of view.
* Coherent drift: between star-field epochs (1-60 min apart) the common displacement is
  found by voting over all pair displacements (2 px bins) and refined with a RANSAC
  similarity transform. ``drift`` = {dx, dy, rate_px_per_min, rot_deg, n_matched}. Stars
  move together; a field that does not move over > 20 min is flagged ``static_field``.
``star_field`` value = {n_stars, points: [[x, y, flux], ...] (full-res px, brightest
first), w, h, noise_sigma, threshold, stack_n, fwhm_px, sky_region, drift, static_field,
ir_mode}. The points feed the plate solver in hordewatch/astro. Emitted every
``star_field_interval_s`` when >= ``min_stars`` sources are found. The star count relative
to the best count seen (decaying reference, >= 15 stars) is also reported as weak
``cloud_fraction`` evidence (method 'star_count', confidence 0.2). Only fractions <= 0.5
are reported, because few stars can also mean haze, dew or compression.

Aircraft lights (multi-frame tracker, ``ctx.state['night']['tracks']``)
------------------------------------------------------------------------------
Aircraft move 0.1-2 deg/s, i.e. 1.6-32 px/s at f ~ 914 px. "Movers" are single-frame
detections (>= 6 sigma, compact) with no counterpart within 1.5 px in the detections of a
frame >= ``static_lag_s`` earlier. Tracks are predicted with constant velocity (gate 4 px
+ 25 % of the predicted motion; one-point tracks accept anything within v_max x dt) and
assigned greedily by distance. A missed detection where the light should be counts as
"off" (strobe or beacon blinking), and a gap longer than ``track_max_gap_s`` (default:
3.5 frame intervals, clamped to 1-20 s) closes the track. A closed track with >= 3
detections, a straight-line fit rms <= 2.5 px and a speed between ``v_min_deg_s`` and
``v_max_deg_s`` is an ``aircraft_light``: {track: [[iso_ts, x, y], ...], speed_px_s,
speed_deg_s, direction_deg_image, duty, blink_hz, colour, ...}. The duty cycle is counted
between the first and last detection only.
``blink_hz`` = (onsets - 1) / (t_last_onset - t_first_onset). It is only reported when
the sampling interval is <= 0.5 s: anti-collision strobes flash at ~0.7-1.7 Hz, so 5-s
sampling aliases completely, and only the duty cycle is meaningful there. In colour mode
the light's colour is red / green / white (red port and green starboard navigation lights
give the flight direction). A steady light (duty >= 0.95) at < 1 deg/s is flagged
``satellite_hint``. Long passes are cut into ``track_max_s`` segments.

Moon
----
A large saturated (Y >= 245), round (circularity >= 0.6) component in the upper frame, or a
strong broad glow (sigma-6 blurred peak >= 60 above the median). The value holds centroid,
radius, fill ratio (area / enclosing circle, a crude phase proxy) and, when skyfield
(bundled DE421) is available, the moon altitude and illuminated fraction at the
approximate site. With the moon > 3 deg below the horizon, the disk is a lamp and is not
reported (``moon_ephemeris_gate``). A disk that has not moved for 20 min is a lamp too
(the moon moves ~0.25 deg/min).

Artificial lights (night_light_event)
--------------------------------------
A 160-px thumbnail is compared with an exponential background (alpha 0.1 per frame).
Connected regions brighter by > ``light_thr`` (or darker: a light switched off) with area
> 0.2 % of the frame are events: {luma_delta, bbox (full-res px), colour, area_frac,
elongation (beams are elongated), in_sky, switched: 'on'|'off'}. A change over > 50 % of
the frame is global (IR illuminator, exposure): the background is re-seeded and nothing is
reported. The same region is not reported again within ``light_repeat_s``, and a
persistent light is absorbed into the background after ~20 frames.

Failure modes: YouTube compression erases all but the brightest stars and planets; the IR
illuminator's glare and insects near the lens make fast "movers" (the speed limits and the
straightness test reject most); clouds hide stars (the star count is itself weak cloud
evidence); a bumped camera shifts every star at once (the drift check reports it as a
jump); tracks through branch gaps are fragmented.
"""
from __future__ import annotations

import logging
import math
from collections import deque
from datetime import datetime, timezone
from typing import Optional

import cv2
import numpy as np

from ..types import Observation, iso
from .base import Analyzer, Context
from .sky import clean, downscale, focal_px, frame_ir_mode, luma, site_from_config, sky_mask_for, solar_altaz

try:
    from scipy.spatial import cKDTree
except Exception:  # pragma: no cover
    cKDTree = None

log = logging.getLogger("hordewatch.night")
UTC = timezone.utc


# ============================================================================ point sources
def detect_points(Y: np.ndarray, roi: np.ndarray, bg_ksize: int = 11, psf_sigma: float = 1.2, k_sigma: float = 5.0,
                  min_amp: float = 3.0, max_points: int = 600, sat_level: float = 250.0):
    """Point sources in ``Y`` (float, 0-255) inside ``roi``.

    Returns (points, noise_sigma, threshold): points is an (N, 7) float array
    [x, y, flux, peak, snr, saturated, psf_sigma], brightest (matched-filter) first.
    """
    empty = np.zeros((0, 7), np.float32)
    m = int(bg_ksize) // 2 + 2               # median / Gaussian border artefacts
    roi = roi.copy()
    roi[:m], roi[-m:], roi[:, :m], roi[:, -m:] = False, False, False, False
    if roi.sum() < 100:
        return empty, 0.0, 0.0
    y8 = np.clip(Y, 0, 255).astype(np.uint8)
    bg = cv2.medianBlur(y8, int(bg_ksize) | 1).astype(np.float32)
    res = Y.astype(np.float32) - bg
    sm = cv2.GaussianBlur(res, (0, 0), 0.8 * psf_sigma)
    vals = sm[roi]
    med = float(np.median(vals))
    sigma = 1.4826 * float(np.median(np.abs(vals - med))) + 1e-3
    rv = res[roi]
    sig_res = 1.4826 * float(np.median(np.abs(rv - np.median(rv)))) + 1e-3
    thr = max(k_sigma * sigma, min_amp)
    pk = (sm >= cv2.dilate(sm, np.ones((5, 5), np.uint8))) & (sm > med + thr) & roi
    ys, xs = np.nonzero(pk)
    if len(xs) == 0:
        return empty, sigma, thr
    o = np.argsort(-sm[ys, xs])[:max_points]
    ys, xs = ys[o], xs[o]
    h, w = Y.shape
    out = np.zeros((len(xs), 7), np.float32)
    yy, xx = np.mgrid[-3:4, -3:4]
    for i, (x, y) in enumerate(zip(xs, ys)):
        x0, x1, y0, y1 = max(0, x - 3), min(w, x + 4), max(0, y - 3), min(h, y + 4)
        win = res[y0:y1, x0:x1]
        wx = xx[(y0 - y + 3):(y1 - y + 3), (x0 - x + 3):(x1 - x + 3)]
        wy = yy[(y0 - y + 3):(y1 - y + 3), (x0 - x + 3):(x1 - x + 3)]
        wt = np.clip(win - 2.0 * sig_res, 0, None)
        s = float(wt.sum())
        if s <= 0:
            cx, cy, ps = float(x), float(y), 0.0
        else:
            mx, my = float((wt * wx).sum() / s), float((wt * wy).sum() / s)
            cx, cy = x + mx, y + my
            vxx = float((wt * (wx - mx) ** 2).sum() / s)
            vyy = float((wt * (wy - my) ** 2).sum() / s)
            ps = math.sqrt(max(0.5 * (vxx + vyy), 0.0))
        out[i] = (cx, cy, float(win.sum()), float(Y[y, x]), float(sm[y, x] - med) / sigma,
                  float(Y[y, x] >= sat_level), ps)
    return out, sigma, thr


def _nn_match(a: np.ndarray, b: np.ndarray, r: float) -> np.ndarray:
    """bool per row of a: some row of b within r px (xy in the first two columns)."""
    if len(a) == 0 or b is None or len(b) == 0:
        return np.zeros(len(a), bool)
    if cKDTree is not None:
        d, _ = cKDTree(b[:, :2]).query(a[:, :2], k=1, distance_upper_bound=r + 1e-6)
        return d <= r
    d2 = ((a[:, None, :2] - b[None, :, :2]) ** 2).sum(-1)
    return d2.min(axis=1) <= r * r


def estimate_drift(p0: np.ndarray, p1: np.ndarray, max_disp: float, bin_px: float = 2.0, min_pairs: int = 4):
    """Common displacement of a point set (p0 -> p1) by pair-displacement voting + RANSAC similarity."""
    if len(p0) < min_pairs or len(p1) < min_pairs:
        return None
    a, b = p0[:200, :2].astype(np.float64), p1[:200, :2].astype(np.float64)
    d = b[None, :, :] - a[:, None, :]
    ok = np.hypot(d[..., 0], d[..., 1]) <= max_disp
    if ok.sum() < min_pairs:
        return None
    dv = d[ok]
    nb = int(2 * max_disp / bin_px) + 1
    H, xe, ye = np.histogram2d(dv[:, 0], dv[:, 1], bins=nb, range=[[-max_disp, max_disp], [-max_disp, max_disp]])
    H = H + 0.5 * (np.roll(H, 1, 0) + np.roll(H, -1, 0) + np.roll(H, 1, 1) + np.roll(H, -1, 1))
    i, j = np.unravel_index(int(np.argmax(H)), H.shape)
    sx, sy = 0.5 * (xe[i] + xe[i + 1]), 0.5 * (ye[j] + ye[j + 1])
    near = ok & (np.abs(d[..., 0] - sx) <= 1.5 * bin_px) & (np.abs(d[..., 1] - sy) <= 1.5 * bin_px)
    ia, ib = np.nonzero(near)
    if len(ia) < max(min_pairs, int(0.25 * min(len(a), len(b)))):
        return None
    # one-to-one: keep the closest pair per source point
    best = {}
    for u, v in zip(ia, ib):
        e = np.hypot(d[u, v, 0] - sx, d[u, v, 1] - sy)
        if u not in best or e < best[u][1]:
            best[u] = (v, e)
    src = np.array([a[u] for u in best], np.float32)
    dst = np.array([b[v] for v, _ in best.values()], np.float32)
    rot = 0.0
    tx, ty = float(np.median(dst[:, 0] - src[:, 0])), float(np.median(dst[:, 1] - src[:, 1]))
    if len(src) >= 3:
        M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=2.0)
        if M is not None:
            rot = math.degrees(math.atan2(M[1, 0], M[0, 0]))
    return {"dx": tx, "dy": ty, "n_matched": int(len(src)), "rot_deg": rot}


# ============================================================================ moon
_EPH = None


def moon_altaz_illum(t_unix: float, lat: float, lon: float):
    """(alt_deg, az_deg, illuminated_fraction) from skyfield + bundled DE421, or None if unavailable."""
    global _EPH
    if _EPH is False:
        return None
    try:
        from skyfield import almanac
        from skyfield.api import wgs84
        if _EPH is None:
            import skyfield_data
            from skyfield.api import Loader
            ld = Loader(skyfield_data.get_skyfield_data_path(), verbose=False)
            _EPH = (ld.timescale(), ld("de421.bsp"))
        ts, eph = _EPH
        t = ts.from_datetime(datetime.fromtimestamp(float(t_unix), UTC))
        alt, az, _ = (eph["earth"] + wgs84.latlon(lat, lon)).at(t).observe(eph["moon"]).apparent().altaz()
        return float(alt.degrees), float(az.degrees), float(almanac.fraction_illuminated(eph, "moon", t))
    except Exception as e:  # never fatal
        log.warning("night: moon ephemeris unavailable (%s); moon gating disabled", e)
        _EPH = False
        return None


def find_moon(Y: np.ndarray, region: np.ndarray, min_radius: float = 4.0, sat_level: float = 245.0) -> Optional[dict]:
    """Moon disk (saturated, round) or glow within ``region`` (bool mask of Y's shape)."""
    sat = ((Y >= sat_level) & region).astype(np.uint8)
    n, lab, stats, cents = cv2.connectedComponentsWithStats(sat, connectivity=8)
    best = None
    for k in range(1, n):
        A = float(stats[k, cv2.CC_STAT_AREA])
        if A < math.pi * min_radius ** 2:
            continue
        bx, by, bw, bh = stats[k, :4]
        comp = np.pad((lab[by:by + bh, bx:bx + bw] == k).astype(np.uint8), 1)
        cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cnts, key=cv2.contourArea)
        P = max(cv2.arcLength(c, True), 1e-6)
        circ = min(1.0, 4 * math.pi * A / (P * P))
        (_, _), rc = cv2.minEnclosingCircle(c)
        fill = A / max(math.pi * rc * rc, 1e-6)
        if circ < 0.6 and fill < 0.5:
            continue
        M = cv2.moments(comp[1:-1, 1:-1], binaryImage=True)
        cand = {"x": bx + M["m10"] / M["m00"], "y": by + M["m01"] / M["m00"], "radius": math.sqrt(A / math.pi),
                "fill": fill, "circularity": circ, "saturated": True, "method": "disk", "area": A}
        if best is None or A > best["area"]:
            best = cand
    if best is not None:
        return best
    if region.sum() < 100:
        return None
    B = cv2.GaussianBlur(Y, (0, 0), 6.0)
    Bm = np.where(region, B, -1)
    iy, ix = np.unravel_index(int(np.argmax(Bm)), Bm.shape)
    if Bm[iy, ix] - float(np.median(B[region])) >= 60.0:
        return {"x": float(ix), "y": float(iy), "radius": None, "fill": None, "circularity": None,
                "saturated": bool(Y[iy, ix] >= sat_level), "method": "glow", "area": 0.0}
    return None


# ============================================================================ tracker
class _Track:
    __slots__ = ("id", "pts", "samples", "v", "continued_from")

    def __init__(self, tid, t, x, y, flux, colour, continued_from=None):
        self.id = tid
        self.pts = [(t, x, y, flux, colour)]
        self.samples = [(t, True)]
        self.v = None
        self.continued_from = continued_from

    @property
    def last(self):
        return self.pts[-1]

    def add(self, t, x, y, flux, colour):
        self.pts.append((t, x, y, flux, colour))
        self.samples.append((t, True))
        p = np.array([(q[0], q[1], q[2]) for q in self.pts[-6:]], np.float64)
        tt = p[:, 0] - p[:, 0].mean()
        den = float((tt * tt).sum())
        if den > 0:
            self.v = (float((tt * (p[:, 1] - p[:, 1].mean())).sum() / den),
                      float((tt * (p[:, 2] - p[:, 2].mean())).sum() / den))

    def predict(self, t):
        t0, x0, y0 = self.last[:3]
        if self.v is None:
            return x0, y0
        return x0 + self.v[0] * (t - t0), y0 + self.v[1] * (t - t0)


def track_summary(tr: _Track, f_px: float) -> Optional[dict]:
    """Straight-line constant-velocity fit of a track; None if fewer than 2 points."""
    if len(tr.pts) < 2:
        return None
    p = np.array([(q[0], q[1], q[2]) for q in tr.pts], np.float64)
    t = p[:, 0]
    A = np.vstack([t - t[0], np.ones(len(t))]).T
    (vx, x0), *_ = np.linalg.lstsq(A, p[:, 1], rcond=None)
    (vy, y0), *_ = np.linalg.lstsq(A, p[:, 2], rcond=None)
    rx = p[:, 1] - (x0 + vx * (t - t[0]))
    ry = p[:, 2] - (y0 + vy * (t - t[0]))
    rms = float(np.sqrt(np.mean(rx * rx + ry * ry)))
    speed = float(math.hypot(vx, vy))
    samples = sorted(s for s in tr.samples if t[0] <= s[0] <= t[-1])   # trailing "off" after the light left: not blinking
    on = [s for s in samples if s[1]]
    duty = len(on) / max(len(samples), 1)
    st = np.array([s[0] for s in samples])
    dt_med = float(np.median(np.diff(st))) if len(st) > 1 else None
    onsets = [s[0] for i, s in enumerate(samples) if s[1] and (i == 0 or not samples[i - 1][1])]
    blink = None
    if dt_med is not None and dt_med <= 0.5 and len(onsets) >= 3 and duty < 0.95:
        blink = (len(onsets) - 1) / max(onsets[-1] - onsets[0], 1e-6)
    cols = [q[4] for q in tr.pts if q[4]]
    colour = max(set(cols), key=cols.count) if cols else None
    return {"speed_px_s": speed, "speed_deg_s": math.degrees(speed / f_px), "vx": float(vx), "vy": float(vy),
            "direction_deg_image": math.degrees(math.atan2(vy, vx)) % 360.0, "rms_px": rms, "duty": duty,
            "blink_hz": blink, "sample_dt_s": dt_med, "colour": colour, "mean_flux": float(np.mean([q[3] for q in tr.pts])),
            "duration_s": float(t[-1] - t[0]), "n_points": len(tr.pts), "n_samples": len(samples)}


def _colour_name(rgb) -> Optional[str]:
    r, g, b = [float(c) for c in rgb]
    mx, mn = max(r, g, b), min(r, g, b)
    if mx < 20:
        return None
    if (mx - mn) / mx < 0.25:
        return "white"
    if r == mx and r > 1.4 * g:
        return "red"
    if g == mx and g > 1.2 * r:
        return "green"
    if b == mx:
        return "blue"
    return "warm" if r >= g else "white"


# ============================================================================ analyzer
DEFAULTS = {
    "fallback_sky_frac": 0.5,
    "roi_erode_px": 4,
    "dark_p95": 70.0,
    "night_sun_alt": -4.0,
    "bg_ksize": 11,
    "psf_sigma": 1.2,
    "k_sigma": 5.0,
    "min_amp": 3.0,
    "max_psf_sigma": 3.0,
    "mover_k_sigma": 6.0,
    "stack_frames": 3,
    "stack_max_span_s": 15.0,
    "star_field_interval_s": 60.0,
    "min_stars": 5,
    "max_points": 300,
    "static_lag_s": 3.0,
    "static_match_px": 1.5,
    "v_min_deg_s": 0.05,
    "v_max_deg_s": 3.0,
    "track_max_gap_s": None,             # None: auto = clip(3.5 x frame interval, 1, 20) s
    "track_min_points": 3,
    "track_max_rms_px": 2.5,
    "track_max_s": 120.0,
    "hot_px_after_s": 1200.0,
    "drift_min_dt_s": 60.0,
    "drift_max_dt_s": 3600.0,
    "cloud_min_ref_stars": 15,
    "moon_min_radius_px": 4.0,
    "moon_interval_s": 60.0,
    "moon_ephemeris_gate": True,
    "light_work_width": 160,
    "light_thr": 25.0,
    "light_min_frac": 0.002,
    "light_bg_alpha": 0.1,
    "light_repeat_s": 60.0,
    "approx_site": None,
}


class NightSkyAnalyzer(Analyzer):
    name = "night"
    wants_frames = True
    min_interval_s = 0.0

    def __init__(self, config=None):
        super().__init__(config)
        cfg = config or {}
        self.p = {**DEFAULTS, **{k: v for k, v in cfg.items() if k != "_global"}}
        self.site = site_from_config(cfg)
        self.tracks: list = []
        self._next_id = 1
        self.det_hist = deque()           # (t, points (N, 7)) single-frame detections
        self.stack = deque(maxlen=int(self.p["stack_frames"]))
        self.epochs = deque()             # (t, star points) for static rejection / drift
        self._last_sf = None
        self._last_moon = None
        self.moon_hist = deque()
        self.light_bg = None
        self.light_recent = []            # (t, bbox_small)
        self.was_night = False
        self._dt = None                   # EMA of the frame interval (s)
        self._pending = []
        self._n_ref = 0.0
        self._t_prev = None

    # ------------------------------------------------------------------ helpers
    @property
    def max_gap_s(self):
        if self.p["track_max_gap_s"]:
            return float(self.p["track_max_gap_s"])
        return float(np.clip(3.5 * (self._dt or 5.0), 1.0, 20.0))

    def _obs(self, kind, frame, value, conf, ts=None):
        return Observation(kind=kind, ts=ts or frame.real_ts, value=clean(value), analyzer=self.name,
                           confidence=float(conf), frame_id=frame.id, ts_capture=frame.capture_ts)

    def _roi(self, ctx, H, W):
        m = sky_mask_for(ctx, H, W)
        src = "mask"
        if m is None:
            m = np.zeros((H, W), bool)
            m[: int(self.p["fallback_sky_frac"] * H)] = True
            src = "fallback"
        e = int(self.p["roi_erode_px"])
        if e > 0:
            m = cv2.erode(m.astype(np.uint8), np.ones((2 * e + 1, 2 * e + 1), np.uint8)) > 0
        return m, src

    def _is_night(self, frame, ctx, thumb, alt):
        if frame_ir_mode(frame, ctx, thumb):
            return True, True
        if alt > self.p["night_sun_alt"]:
            return False, False
        Yt = luma(thumb)
        top = Yt[: max(1, int(0.4 * Yt.shape[0]))]
        return bool(np.percentile(top, 95) < self.p["dark_p95"]), False

    def flush(self, frame=None, ctx=None) -> list:
        """Close all open tracks (end of night / end of stream) and return their observations."""
        out = []
        for tr in self.tracks:
            o = self._finish(tr, frame, "ended")
            if o is not None:
                out.append(o)
        self.tracks = []
        return out

    # ------------------------------------------------------------------ main
    def on_frame(self, frame, ctx: Context):
        img = frame.image
        H, W = img.shape[:2]
        t = frame.real_ts.timestamp()
        thumb, _ = downscale(img, int(self.p["light_work_width"]))
        alt, _ = solar_altaz(t, *self.site)
        night, ir = self._is_night(frame, ctx, thumb, alt)
        if self._t_prev is not None and t > self._t_prev:
            d = t - self._t_prev
            self._dt = d if self._dt is None else self._dt + 0.2 * (d - self._dt)
        self._t_prev = t
        st = ctx.state.setdefault("night", {})
        st["active"] = night
        if not night:
            out = self.flush(frame, ctx) if self.was_night else []
            self.was_night = False
            self.light_bg = None
            self.stack.clear()
            self.det_hist.clear()
            return out
        self.was_night = True
        self._f = focal_px(self.config, W)
        self._pending = []
        out = []
        roi, roi_src = self._roi(ctx, H, W)
        rows = np.nonzero(roi.any(axis=1))[0]
        Yfull = None
        if len(rows):
            r0, r1 = int(rows[0]), int(rows[-1]) + 1
            Yfull = luma(img[r0:r1])
            roi_s = roi[r0:r1]
            moon_region = cv2.dilate(roi_s.astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
            moon = self._moon(frame, ctx, Yfull, moon_region, r0, W, H, t, out)
            if moon is not None:                 # keep the moon and its glow out of the point lists
                yy, xx = np.mgrid[0:roi_s.shape[0], 0:W]
                rad = 6 * (moon.get("radius") or 10.0) + 10
                roi_s = roi_s & ((xx - moon["x"]) ** 2 + (yy - (moon["y"] - r0)) ** 2 > rad * rad)
            pts, sigma, thr = detect_points(Yfull, roi_s, self.p["bg_ksize"], self.p["psf_sigma"], self.p["k_sigma"],
                                            self.p["min_amp"], max_points=600)
            pts = pts[pts[:, 6] <= 1.7 * self.p["max_psf_sigma"]] if len(pts) else pts   # bright lights bloom
            if len(pts):
                pts[:, 1] += r0
            out += self._track(frame, t, pts, img, ir, W, H, roi)
            while self.stack and not (0 <= t - self.stack[0][0] <= self.p["stack_max_span_s"]):
                self.stack.popleft()          # stars drift ~4 px/min: stack only a short span
            self.stack.append((t, Yfull, r0, roi_s))
            if self._last_sf is None or t - self._last_sf >= self.p["star_field_interval_s"] - 1e-6 or t < self._last_sf:
                sf = self._star_field(frame, t, W, H, ir, roi_src)
                if sf is not None:
                    self._last_sf = t
                    out.append(sf)
        out += self._lights(frame, thumb, ir, W, H, ctx, t)
        out += self._pending
        st["tracks"] = [{"id": tr.id, "n": len(tr.pts), "last": tr.last[:3]} for tr in self.tracks]
        return out

    # ------------------------------------------------------------------ tracker
    def _track(self, frame, t, pts, img, ir, W, H, roi):
        out = []
        while self.det_hist and self.det_hist[0][0] < t - max(30.0, 4 * self.p["static_lag_s"]):
            self.det_hist.popleft()
        ref = None
        for th, ph in reversed(self.det_hist):
            if th <= t - self.p["static_lag_s"]:
                ref = ph
                break
        if ref is None and self.det_hist and self.det_hist[0][0] < t:
            ref = self.det_hist[0][1]
        self.det_hist.append((t, pts))
        if ref is None:
            return out
        cand = pts[(pts[:, 4] >= self.p["mover_k_sigma"])] if len(pts) else pts
        movers = cand[~_nn_match(cand, ref, self.p["static_match_px"])] if len(cand) else cand
        f = self._f
        vmin = math.radians(self.p["v_min_deg_s"]) * f
        vmax = math.radians(self.p["v_max_deg_s"]) * f
        pairs = []
        for i, tr in enumerate(self.tracks):
            dt = t - tr.last[0]
            if dt <= 0:
                continue
            px, py = tr.predict(t)
            if tr.v is not None:
                gate = 4.0 + 0.25 * math.hypot(*tr.v) * dt
            else:
                gate = vmax * dt + 3.0
            for j, m in enumerate(movers):
                d = math.hypot(m[0] - px, m[1] - py)
                if d > gate:
                    continue
                if tr.v is None and math.hypot(m[0] - tr.last[1], m[1] - tr.last[2]) < vmin * dt:
                    continue
                pairs.append((d, i, j))
        pairs.sort()
        used_t, used_m = set(), set()
        for d, i, j in pairs:
            if i in used_t or j in used_m:
                continue
            used_t.add(i)
            used_m.add(j)
            m = movers[j]
            self.tracks[i].add(t, float(m[0]), float(m[1]), float(m[2]), None if ir else self._colour(img, m))
        keep = []
        for i, tr in enumerate(self.tracks):
            if i not in used_t:
                px, py = tr.predict(t)
                if 0 <= px < W and 0 <= py < H and roi[int(py), int(px)]:
                    tr.samples.append((t, False))
                if t - tr.last[0] > self.max_gap_s:
                    o = self._finish(tr, frame, "ended")
                    if o is not None:
                        out.append(o)
                    continue
            elif tr.pts[-1][0] - tr.pts[0][0] >= self.p["track_max_s"]:
                o = self._finish(tr, frame, "segment")
                if o is not None:
                    out.append(o)
                    last = tr.last
                    nt = _Track(self._next_id, *last, continued_from=tr.id)
                    nt.v = tr.v
                    self._next_id += 1
                    keep.append(nt)
                continue
            keep.append(tr)
        for j, m in enumerate(movers):
            if j not in used_m:
                keep.append(_Track(self._next_id, t, float(m[0]), float(m[1]), float(m[2]),
                                   None if ir else self._colour(img, m)))
                self._next_id += 1
        self.tracks = keep[-200:]
        return out

    @staticmethod
    def _colour(img, m):
        x, y = int(round(m[0])), int(round(m[1]))
        h, w = img.shape[:2]
        win = img[max(0, y - 1):min(h, y + 2), max(0, x - 1):min(w, x + 2)].reshape(-1, 3).astype(np.float32)
        return _colour_name(win.max(axis=0)) if len(win) else None

    def _finish(self, tr: _Track, frame, status):
        if len(tr.pts) < self.p["track_min_points"]:
            return None
        s = track_summary(tr, self._f if hasattr(self, "_f") else 914.0)
        if s is None or s["rms_px"] > self.p["track_max_rms_px"]:
            return None
        if not (self.p["v_min_deg_s"] <= s["speed_deg_s"] <= self.p["v_max_deg_s"]):
            return None
        H, W = (frame.image.shape[:2] if frame is not None else (None, None))
        track = [[iso(datetime.fromtimestamp(q[0], UTC)), q[1], q[2]] for q in tr.pts]
        sat_hint = s["duty"] >= 0.95 and s["blink_hz"] is None and s["speed_deg_s"] < 1.0
        conf = min(0.7, 0.3 + 0.08 * min(len(tr.pts) - 3, 5) + (0.1 if s["duty"] < 0.95 else 0.0))
        if sat_hint:
            conf *= 0.8
        val = {"track": track, "track_id": tr.id, "status": status, "continued_from": tr.continued_from,
               "w": W, "h": H, "focal_px_assumed": self._f if hasattr(self, "_f") else None,
               "satellite_hint": sat_hint, **s}
        ts = datetime.fromtimestamp(tr.pts[0][0], UTC)
        if frame is None:
            return Observation(kind="aircraft_light", ts=ts, value=clean(val), analyzer=self.name, confidence=conf)
        return self._obs("aircraft_light", frame, val, conf, ts=ts)

    # ------------------------------------------------------------------ star field
    def _star_field(self, frame, t, W, H, ir, roi_src):
        shapes = {(y.shape, r0) for _, y, r0, _ in self.stack}
        if len(shapes) != 1:
            last = self.stack[-1]
            self.stack.clear()
            self.stack.append(last)
        Ys = [y for _, y, _, _ in self.stack]
        r0 = self.stack[-1][2]
        roi = self.stack[-1][3]
        Ym = Ys[0] if len(Ys) == 1 else np.median(np.stack(Ys, 0), axis=0).astype(np.float32)
        pts, sigma, thr = detect_points(Ym, roi, self.p["bg_ksize"], self.p["psf_sigma"], self.p["k_sigma"],
                                        self.p["min_amp"], max_points=int(self.p["max_points"]) * 2)
        if len(pts):
            pts = pts[(pts[:, 6] <= self.p["max_psf_sigma"]) & (pts[:, 5] < 0.5)]
            pts[:, 1] += r0
        pts = pts[np.argsort(-pts[:, 2])] if len(pts) else pts
        # static sources (hot pixels, lamps, sky holes): same place as >= hot_px_after_s ago
        while self.epochs and self.epochs[0][0] < t - self.p["hot_px_after_s"] - self.p["drift_max_dt_s"]:
            self.epochs.popleft()
        old = [p for te, p in self.epochs if t - te >= self.p["hot_px_after_s"]]
        n_static = 0
        if old and len(pts):
            st = np.zeros(len(pts), bool)
            for p in old:
                st |= _nn_match(pts, p, 1.0)
            n_static = int(st.sum())
            pts = pts[~st]
        drift, static_field = None, False
        prev = [(te, p) for te, p in self.epochs if self.p["drift_min_dt_s"] <= t - te <= self.p["drift_max_dt_s"]]
        if prev and len(pts) >= self.p["min_stars"]:
            te, p = prev[-1]
            dt = t - te
            max_disp = max(10.0, 6.0 * dt / 60.0 * self._f / 914.0)
            dr = estimate_drift(p, pts, max_disp)
            if dr is not None:
                dr["dt_s"] = dt
                dr["rate_px_per_min"] = math.hypot(dr["dx"], dr["dy"]) / (dt / 60.0)
                drift = dr
                static_field = dt >= self.p["hot_px_after_s"] and math.hypot(dr["dx"], dr["dy"]) < 1.0
        self.epochs.append((t, pts.copy()))
        if len(pts) < self.p["min_stars"]:
            return None
        pts = pts[: int(self.p["max_points"])]
        self._cloud_from_stars(frame, len(pts), static_field)
        fwhm = float(np.median(pts[:, 6])) * 2.3548
        conf = min(0.7, 0.3 + 0.02 * len(pts)) * (0.4 if static_field else 1.0)
        val = {"n_stars": int(len(pts)), "points": [[float(p[0]), float(p[1]), float(p[2])] for p in pts],
               "snr": [float(p[4]) for p in pts], "w": W, "h": H, "noise_sigma": sigma, "threshold": thr,
               "stack_n": len(Ys), "fwhm_px": fwhm, "sky_region": roi_src, "n_static_rejected": n_static,
               "drift": drift, "static_field": static_field, "ir_mode": ir}
        return self._obs("star_field", frame, val, conf)

    def _cloud_from_stars(self, frame, n, static_field):
        """Clear-sky evidence at night: many stars relative to the best count seen = little cloud.

        Few stars can also mean haze, dew on the lens or compression, so only fractions below 0.5 (at
        least half of the reference count visible) are reported, with low confidence."""
        if static_field:
            return
        self._n_ref = max(getattr(self, "_n_ref", 0.0) * 0.999, float(n))
        if self._n_ref < self.p["cloud_min_ref_stars"] or n < 0.5 * self._n_ref:
            return
        frac = float(np.clip(1.0 - n / self._n_ref, 0.0, 1.0))
        self._pending.append(self._obs("cloud_fraction", frame, {"fraction": frac, "method": "star_count", "n_stars": n,
                                                                 "n_ref": self._n_ref}, 0.2))

    # ------------------------------------------------------------------ moon
    def _moon(self, frame, ctx, Y, region, r0, W, H, t, out):
        m = find_moon(Y, region, self.p["moon_min_radius_px"])
        if m is None:
            return None
        m["y"] += r0
        if self._last_moon is not None and 0 <= t - self._last_moon < self.p["moon_interval_s"]:
            return m
        eph = moon_altaz_illum(t, *self.site) if self.p["moon_ephemeris_gate"] else None
        if eph is not None and eph[0] < -3.0:
            return m                      # disk while the moon is down: a lamp (handled as a light)
        while self.moon_hist and self.moon_hist[0][0] < t - 3 * 3600:
            self.moon_hist.popleft()
        static = any(t - th >= 1200 and math.hypot(m["x"] - xh, m["y"] - yh) < 2.0 for th, xh, yh in self.moon_hist)
        self.moon_hist.append((t, m["x"], m["y"]))
        if static:
            return m
        self._last_moon = t
        val = {"x": m["x"], "y": m["y"], "radius": m["radius"], "illum": eph[2] if eph else None,
               "fill": m["fill"], "circularity": m["circularity"], "saturated": m["saturated"], "method": m["method"],
               "w": W, "h": H, "xn": m["x"] / W, "yn": m["y"] / H,
               "moon_alt_approx_deg": eph[0] if eph else None, "moon_az_approx_deg": eph[1] if eph else None}
        conf = 0.55 if m["method"] == "disk" else 0.3
        if eph is None:
            conf *= 0.7
        out.append(self._obs("moon_pixel", frame, val, conf))
        return m

    # ------------------------------------------------------------------ artificial lights
    def _lights(self, frame, thumb, ir, W, H, ctx, t):
        out = []
        Y = cv2.GaussianBlur(luma(thumb), (0, 0), 1.0)
        h, w = Y.shape
        if self.light_bg is None or self.light_bg.shape != Y.shape:
            self.light_bg = Y.copy()
            return out
        D = Y - self.light_bg
        thr = self.p["light_thr"]
        on = D > thr
        off = D < -thr
        if (on | off).mean() > 0.5:          # global change: IR illuminator / exposure / mode switch
            self.light_bg = Y.copy()
            return out
        sky = sky_mask_for(ctx, h, w)
        if sky is None:
            sky = np.zeros((h, w), bool)
            sky[: int(self.p["fallback_sky_frac"] * h)] = True
        self.light_recent = [(tt, bb) for tt, bb in self.light_recent if t - tt < self.p["light_repeat_s"]]
        sx, sy = W / float(w), H / float(h)
        for switched, m in (("on", on), ("off", off)):
            m8 = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
            n, lab, stats, _ = cv2.connectedComponentsWithStats(m8, connectivity=8)
            for k in range(1, n):
                A = stats[k, cv2.CC_STAT_AREA]
                if A < self.p["light_min_frac"] * h * w:
                    continue
                bx, by, bw, bh = [int(v) for v in stats[k, :4]]
                bb = (bx, by, bx + bw, by + bh)
                if any(_iou(bb, b2) > 0.3 for _, b2 in self.light_recent):
                    continue
                comp = lab == k
                ys, xs = np.nonzero(comp)
                elong = 1.0
                if len(xs) >= 5:
                    ev = np.linalg.eigvalsh(np.cov(xs.astype(np.float64), ys.astype(np.float64)))
                    elong = float(math.sqrt(max(ev[1], 1e-6) / max(ev[0], 1e-6)))
                colour = "ir" if ir else (_colour_name(thumb[comp].astype(np.float32).mean(axis=0)) or "dark")
                self.light_recent.append((t, bb))
                val = {"luma_delta": float(D[comp].mean()), "bbox": [bx * sx, by * sy, (bx + bw) * sx, (by + bh) * sy],
                       "colour": colour, "area_frac": float(A / (h * w)), "elongation": elong,
                       "in_sky": bool(sky[comp].mean() > 0.5), "switched": switched, "ir_mode": ir, "w": W, "h": H}
                conf = min(0.6, 0.3 + 0.01 * abs(val["luma_delta"])) * (1.0 if switched == "on" else 0.7)
                out.append(self._obs("night_light_event", frame, val, conf))
        self.light_bg += self.p["light_bg_alpha"] * (Y - self.light_bg)
        return out


def _iou(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0
