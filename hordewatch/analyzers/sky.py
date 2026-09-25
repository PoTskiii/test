"""Sky / light / weather photometry (analyzer name: ``sky``).

What it measures (per sampled frame, ~256 px wide working copy, a few ms of CPU)
-----------------------------------------------------------------------------
* A learned **sky mask**. A pixel counts as sky if it is (a) bright relative to the
  ground (the bottom 40 % of the frame), (b) smooth (5x5 local std of luma), (c) blue or
  grey, meaning not green foliage (G > (R+B)/2) and not brown bark (R > B), and (d) in the
  upper part of the frame (full weight above 40 % of the height, zero below
  ``sky_max_y`` = 70 %). The product of these soft scores is averaged over time. The
  memory is 1/n for the first frames and then an exponential average over
  ``mask_memory_frames`` (~1000 frames, about 1.5 h at 5 s). So the mask sharpens over a
  day, and swaying branches and passing clouds wash out to ~0.5 and are dropped. It is
  only updated in colour (day) mode with the sun above 3 deg at the approximate site,
  because twilight and IR images would corrupt it. The mask goes into
  ``ctx.state['sky']['mask']`` for the sun / rain / night analyzers (see
  ``sky_mask_for``). It is saved as PNG under ``<archive_dir>/sky/`` (binary mask plus the
  8-bit accumulator) and reloaded on restart. Until ``mask_min_frames`` updates exist,
  the current frame's thresholded score is used (``mask_state='bootstrap'``).
* ``sky_photometry``: sky-pixel mean luma (8-bit, gamma encoded as delivered), median,
  mean R/G/B, saturation, B/R ratio of linearised means, clipped fraction, sky-to-scene
  luma ratio, and the correlated colour temperature. CCT is computed as sRGB ->
  linear -> XYZ -> CIE 1960 (u, v), then the nearest point on the Planckian locus
  (Krystek 1985 approximation). ``duv`` is the signed distance from the locus; |duv| > 0.02
  means the colour is not blackbody-like (saturated blue sky) and cct_k is only indicative.
  The camera's auto white balance makes CCT relative, not absolute.
* ``scene_photometry``: whole-frame luma statistics, clipped / dark fractions, an
  exposure hint, ground luma and the IR-mode flag. IR mode = monochrome image (median HSV
  saturation < 14 and mean channel difference < 4), switched with a 2-frame hysteresis.
  ``noise_sigma`` is Immerkaer's (1996) fast noise estimate on a full-resolution centre
  crop; it rises with sensor gain, so it is a light-level proxy after the exposure time
  has saturated at dusk. Stream compression flattens it.
* ``cloud_fraction``: sky pixels (not clipped, not dark, away from the last detected sun)
  classified by the red/blue ratio. Clear sky has R/B ~0.4-0.7 because Rayleigh scattering
  is ~lambda^-4. Cloud droplets scatter neutrally, giving R/B ~0.85-1 (Long et al. 2006,
  Heinle et al. 2010). The soft membership is sigmoid((R/B - 0.78) / 0.04). Local texture
  (broken cumulus edges) and the sky brightness relative to a learned clear-sky reference
  for the same solar altitude (5-deg bins at the approximate site) are reported alongside.
  When the clear-sky reference exists and the sky is much brighter than clear, clipped
  pixels are counted as bright cloud. Skipped when the sun is < 3 deg (reddened sky looks
  like cloud), in IR, or when > 60 % of the sky is clipped.
* ``direct_sun``: hard shadows on the ground (below 45 % height, outside the sky). Three
  signs of direct sun, all scale-free:
  (1) linear-luminance dynamic range p95/p10;
  (2) bimodality. An Otsu split of the ground log-luminance gives two classes. If their
  means differ by >= 3x (the direct/diffuse ratio; overcast albedo contrast between heather,
  lichen and bark stays ~2x), the bright class is "sunlit" (``sunlit_fraction``,
  ``class_ratio``). This works whether sunflecks are a minority under the canopy or most
  of the ground is in sun;
  (3) the sunlit class is warmer (lit by sun + sky) than the shade, which is lit by the blue
  sky alone (``warm_shift`` = difference of mean log(R/B)).
* ``fog``: contrast of a "far" band (35-55 % height, looking deep into the forest) against
  a "near" band (bottom 25 %). By Koschmieder, C(d) = C0 exp(-beta d), so fog kills
  distant contrast first while near contrast survives. The far/near ratio is compared with
  a slowly learned clear baseline. Two more cues: airlight (far-band luma approaches sky
  luma) and the dark-channel prior (He et al. 2009). Haze lifts min(R,G,B) over a patch,
  giving a haze estimate of 1 - t = 0.95 * darkchannel / A. Daytime only.
* **Twilight markers** (the key astro input). A 1-min-binned, 5-bin running-median
  light curve of sky luma is kept per camera mode (day/IR series are separate, because the
  IR switch changes the spectral response). A marker is emitted when a threshold
  (``twilight_thresholds``, default 100/50/25/12) is crossed *and held*: 10 min on the old
  side before, 10 min on the new side after, no gap > 3 min, and the right slope sign.
  The crossing time is the zero of a local linear fit of log luma against time (+-10 min),
  which is robust to single-bin wiggles. The approximate-site solar altitude at the
  crossing must lie in [-18, +12] deg and fall at dusk (descending) or rise at dawn
  (ascending). Midday cloud dips are therefore not markers. A marker is emitted as
  ``sky_photometry`` with ``ts`` = crossing time, ``region='twilight_marker'``,
  ``luma`` = threshold and ``value.twilight_marker = {event, threshold, series, t_cross,
  slope_per_min, mode, sun_alt_approx_deg, method}``. The distinct region keeps markers
  out of the per-frame light curve that astro/solver.py builds from region 'sky'.
  Physics: sky brightness at twilight depends (to first order) only on the sun's depression
  below the local horizon. Auto-exposure normalises luma until the exposure/gain limit is
  reached, so crossings are only meaningful late in twilight. The IR-switch time
  (scene_photometry ir_mode) is the camera's own photometer.

Failure modes: the whole sky clipped (forest exposure) gives no colour, so no cloud
fraction; the auto white balance shifts R/B; a camera move invalidates the mask until it
re-learns; snow on branches, white signs and the box roof reflecting the sky can enter the
mask if they are high in the frame; fog and rain on the lens look alike to the contrast
measures; clouds shift twilight crossings by minutes (the solver's Student-t loss
absorbs this).

Shared helpers used by sun.py / rain.py / night.py live here: ``solar_altaz``,
``is_ir_raw``, ``frame_ir_mode``, ``sky_mask_for``, ``downscale``, ``luma``, ``clean``,
``site_from_config``, ``focal_px``.
"""
from __future__ import annotations

import logging
import math
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from ..types import Observation, iso
from .base import Analyzer, Context

log = logging.getLogger("hordewatch.sky")
UTC = timezone.utc
DEFAULT_SITE = (61.25, 9.0)          # centre of the hordejakt search domain (lat, lon)


# ============================================================================ shared helpers
def _round_float(f: float):
    """4 decimals, but at least 4 significant digits for small magnitudes (noise sigmas, duv, rates);
    never fewer decimals than 4, so unix times and pixel coordinates keep their precision."""
    if not math.isfinite(f):
        return None
    a = abs(f)
    if a == 0.0 or a >= 1e-2:
        return round(f, 4)
    return float(f"{f:.4g}")


def clean(v):
    """Recursively convert numpy scalars / arrays / bools / datetimes into JSON-friendly values."""
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [clean(x) for x in v]
    if isinstance(v, np.ndarray):
        return clean(v.tolist())
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return _round_float(float(v))
    if isinstance(v, datetime):
        return iso(v)
    return v


def as_rgb(img) -> np.ndarray:
    """Coerce a frame image to contiguous H x W x 3 uint8 RGB.

    The ingest contract is H x W x 3 uint8, but a grey IR frame decoded as 2-D / H x W x 1,
    an RGBA PNG from an image-folder replay, or float / 16-bit arrays must not crash the
    analyzers. Float images with max <= 1 are scaled by 255; 16-bit images are divided by 257.
    """
    a = np.asarray(img)
    if a.ndim == 3 and a.shape[2] == 3 and a.dtype == np.uint8:
        return a
    if a.dtype != np.uint8:
        if np.issubdtype(a.dtype, np.floating):
            a = np.nan_to_num(a.astype(np.float32))
            if a.size and float(a.max()) <= 1.0 + 1e-6:
                a = a * 255.0
        elif a.dtype in (np.uint16, np.int32, np.uint32, np.int64, np.uint64) and a.size and a.max() > 255:
            a = a.astype(np.float32) / 257.0
        a = np.clip(a, 0, 255).astype(np.uint8)
    if a.ndim == 2:
        a = a[..., None]
    if a.ndim != 3:
        raise ValueError(f"unsupported frame image shape {a.shape}")
    if a.shape[2] == 1 or a.shape[2] == 2:
        a = np.repeat(a[..., :1], 3, axis=2)
    elif a.shape[2] > 3:
        a = a[..., :3]
    return np.ascontiguousarray(a)


def rgb_frame(frame):
    """The frame itself when its image already is H x W x 3 uint8, else a copy with a coerced image."""
    img = frame.image
    if isinstance(img, np.ndarray) and img.ndim == 3 and img.shape[2] == 3 and img.dtype == np.uint8:
        return frame
    import dataclasses
    return dataclasses.replace(frame, image=as_rgb(img))


def downscale(img: np.ndarray, width: int):
    """Area-downscale to ``width`` px (never upscale). Returns (image, scale = new/old)."""
    h, w = img.shape[:2]
    if w <= width:
        return img, 1.0
    s = width / float(w)
    return cv2.resize(img, (int(width), max(1, int(round(h * s)))), interpolation=cv2.INTER_AREA), s


def luma(rgb: np.ndarray) -> np.ndarray:
    """Rec.601 luma (float32, 0-255) of an RGB image (gamma-encoded, as delivered)."""
    f = rgb.astype(np.float32)
    return f[..., 0] * 0.299 + f[..., 1] * 0.587 + f[..., 2] * 0.114


def srgb_to_linear(c):
    c = np.asarray(c, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def is_ir_raw(rgb_small: np.ndarray, sat_thr: float = 14.0, chan_thr: float = 4.0) -> bool:
    """Night/IR mode: the IR-cut filter is out and the camera outputs a (near) grey image."""
    x = rgb_small.astype(np.int16)
    chan = (np.abs(x[..., 0] - x[..., 1]).mean() + np.abs(x[..., 1] - x[..., 2]).mean()) / 2.0
    hsv = cv2.cvtColor(np.ascontiguousarray(rgb_small), cv2.COLOR_RGB2HSV)
    return bool(np.median(hsv[..., 1]) < sat_thr and chan < chan_thr)


def solar_altaz(t, lat, lon, refraction: bool = True):
    """Sun altitude / azimuth (deg, azimuth from north through east) - NOAA algorithm.

    t: datetime (aware) or unix seconds; lat/lon scalars or arrays. Accuracy ~0.01 deg
    (1900-2100) before refraction; Bennett refraction (standard atmosphere) is added for
    altitudes above -1 deg. No dependencies, so every analyzer can gate on it cheaply.
    """
    ts = t.timestamp() if isinstance(t, datetime) else float(t)
    lat = np.asarray(lat, np.float64)
    lon = np.asarray(lon, np.float64)
    jd = ts / 86400.0 + 2440587.5
    jc = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360.0
    M = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    Mr = np.radians(M)
    C = (np.sin(Mr) * (1.914602 - jc * (0.004817 + 0.000014 * jc)) + np.sin(2 * Mr) * (0.019993 - 0.000101 * jc)
         + np.sin(3 * Mr) * 0.000289)
    true_long = L0 + C
    omega = 125.04 - 1934.136 * jc
    app_long = true_long - 0.00569 - 0.00478 * np.sin(np.radians(omega))
    mean_obl = 23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60.0) / 60.0
    obl = np.radians(mean_obl + 0.00256 * np.cos(np.radians(omega)))
    decl = np.arcsin(np.sin(obl) * np.sin(np.radians(app_long)))
    y = np.tan(obl / 2) ** 2
    L0r = np.radians(L0)
    eot = 4 * np.degrees(y * np.sin(2 * L0r) - 2 * e * np.sin(Mr) + 4 * e * y * np.sin(Mr) * np.cos(2 * L0r)
                         - 0.5 * y * y * np.sin(4 * L0r) - 1.25 * e * e * np.sin(2 * Mr))
    minutes = (ts % 86400.0) / 60.0
    tst = (minutes + eot + 4.0 * lon) % 1440.0
    ha = np.radians(tst / 4.0 - 180.0)
    latr = np.radians(lat)
    cz = np.clip(np.sin(latr) * np.sin(decl) + np.cos(latr) * np.cos(decl) * np.cos(ha), -1, 1)
    alt = 90.0 - np.degrees(np.arccos(cz))
    az = (np.degrees(np.arctan2(np.sin(ha), np.cos(ha) * np.sin(latr) - np.tan(decl) * np.cos(latr))) + 180.0) % 360.0
    if refraction:
        h = np.maximum(alt, -1.0)
        R = 1.02 / np.tan(np.radians(h + 10.3 / (h + 5.11))) / 60.0      # Saemundsson / Bennett, deg
        alt = np.where(alt > -1.0, alt + R, alt)
    if alt.ndim == 0:
        return float(alt), float(az)
    return alt, az


def site_from_config(cfg: dict) -> tuple:
    """Approximate site (lat, lon): analyzer config ``approx_site``, else the astro bridge's, else the domain centre."""
    if cfg.get("approx_site"):
        return tuple(float(x) for x in cfg["approx_site"])
    g = cfg.get("_global") or {}
    a = (g.get("analyzer_config") or {}).get("astro_bridge") or {}
    if a.get("approx_site"):
        return tuple(float(x) for x in a["approx_site"])
    return DEFAULT_SITE


def focal_px(cfg: dict, width: int) -> float:
    """Focal length in px for an image ``width`` px wide, from camera.focal_px (at 1280) or camera.hfov_deg."""
    cam = (cfg.get("_global") or {}).get("camera") or {}
    if cam.get("focal_px"):
        return float(cam["focal_px"]) * width / 1280.0
    hf = float(cfg.get("hfov_deg") or cam.get("hfov_deg") or 70.0)
    return 0.5 * width / math.tan(math.radians(hf) / 2.0)


def shared(ctx: Context) -> dict:
    return ctx.state.setdefault("sky", {})


def frame_ir_mode(frame, ctx: Context, small: Optional[np.ndarray] = None) -> bool:
    """IR mode for this frame: the sky analyzer's hysteresis decision when it already ran on this
    frame, else a raw decision from a thumbnail."""
    st = ctx.state.get("sky") or {}
    # index AND time: frame indices restart when the ingest reconnects or a replay chain starts over
    if st.get("frame_index") == frame.index and st.get("ts") == frame.real_ts and "ir_mode" in st:
        return bool(st["ir_mode"])
    if small is None:
        small, _ = downscale(as_rgb(frame.image), 160)
    return is_ir_raw(small)


def sky_mask_for(ctx: Context, h: int, w: int) -> Optional[np.ndarray]:
    """Learned sky mask resized to (h, w) (bool), or None if the sky analyzer has none yet."""
    st = ctx.state.get("sky") or {}
    m = st.get("mask")
    if m is None or not np.any(m):
        return None
    if m.shape != (h, w):
        m = cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0
    return m


def rect_mask(h, w, rects) -> np.ndarray:
    """Union of normalised rectangles [x0, y0, x1, y1] as a bool mask."""
    m = np.zeros((h, w), bool)
    for r in rects or []:
        x0, y0, x1, y1 = r
        m[int(round(y0 * h)):int(round(y1 * h)), int(round(x0 * w)):int(round(x1 * w))] = True
    return m


# ============================================================================ colour temperature
_M_RGB2XYZ = np.array([[0.4124564, 0.3575761, 0.1804375],
                       [0.2126729, 0.7151522, 0.0721750],
                       [0.0193339, 0.1191920, 0.9503041]])
_T_GRID = np.logspace(np.log10(1000.0), np.log10(30000.0), 800)


def _planck_uv(T):
    """Krystek (1985) rational approximation of the Planckian locus in CIE 1960 (u, v)."""
    T = np.asarray(T, np.float64)
    u = (0.860117757 + 1.54118254e-4 * T + 1.28641212e-7 * T * T) / (1 + 8.42420235e-4 * T + 7.08145163e-7 * T * T)
    v = (0.317398726 + 4.22806245e-5 * T + 4.20481691e-8 * T * T) / (1 - 2.89741816e-5 * T + 1.61456053e-7 * T * T)
    return u, v


_LOCUS_U, _LOCUS_V = _planck_uv(_T_GRID)


def cct_from_linear_rgb(rl, gl, bl):
    """(cct_k, duv) from *linear* sRGB means; None if too dark. Nearest point on the Planckian locus
    (1000-30000 K grid, parabolic refinement); duv > 0 above the locus (greenish), < 0 below (purplish)."""
    X, Y, Z = _M_RGB2XYZ @ np.array([rl, gl, bl], np.float64)
    d = X + 15 * Y + 3 * Z
    if Y <= 1e-5 or d <= 1e-9:
        return None, None
    u, v = 4 * X / d, 6 * Y / d
    dist = np.hypot(_LOCUS_U - u, _LOCUS_V - v)
    i = int(np.argmin(dist))
    T = _T_GRID[i]
    if 0 < i < len(_T_GRID) - 1:
        y0, y1, y2 = dist[i - 1], dist[i], dist[i + 1]
        den = y0 - 2 * y1 + y2
        if den > 1e-12:
            off = 0.5 * (y0 - y2) / den
            T = float(np.exp(np.log(_T_GRID[i]) + off * (np.log(_T_GRID[i + 1]) - np.log(_T_GRID[i]))))
    lu, lv = _planck_uv(T)
    tu, tv = _planck_uv(T * 1.01)
    # sign of duv: positive when the point is on the "green" side (above the locus in the uv plane)
    nx, ny = -(tv - lv), (tu - lu)
    sign = 1.0 if (u - lu) * nx + (v - lv) * ny > 0 else -1.0
    if ny < 0:
        sign = -sign
    return float(T), float(sign * np.hypot(u - lu, v - lv))


def otsu_threshold(v: np.ndarray, bins: int = 64) -> float:
    """Otsu's threshold of a 1-D sample (maximises the between-class variance)."""
    v = np.asarray(v, np.float64).ravel()
    lo, hi = float(v.min()), float(v.max())
    if hi - lo < 1e-9:
        return hi
    hist, edges = np.histogram(v, bins=bins, range=(lo, hi))
    p = hist / hist.sum()
    c = 0.5 * (edges[:-1] + edges[1:])
    w0 = np.cumsum(p)
    m0 = np.cumsum(p * c)
    mt = m0[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        sb = (mt * w0 - m0) ** 2 / (w0 * (1 - w0))
    sb[~np.isfinite(sb)] = 0
    return float(edges[int(np.argmax(sb)) + 1])


def immerkaer_noise(gray: np.ndarray) -> float:
    """Fast noise std estimate (Immerkaer 1996): sqrt(pi/2) / (6 (W-2)(H-2)) * sum |I * N|."""
    g = gray.astype(np.float32)
    if g.shape[0] < 3 or g.shape[1] < 3:
        return 0.0
    k = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], np.float32)
    r = cv2.filter2D(g, -1, k)[1:-1, 1:-1]
    return float(np.sqrt(np.pi / 2.0) * np.abs(r).mean() / 6.0)


# ============================================================================ sky mask model
class SkyMaskModel:
    """Temporal average of the per-pixel sky score (see module docstring)."""

    def __init__(self, shape, memory_frames=1000, min_frames=3, threshold=0.5):
        self.acc = np.zeros(shape, np.float32)
        self.n = 0
        self.memory = max(int(memory_frames), 1)
        self.min_frames = int(min_frames)
        self.thr = float(threshold)

    @staticmethod
    def score(rgb_small: np.ndarray, Y: np.ndarray, ir: bool, sky_max_y: float = 0.7) -> np.ndarray:
        h, w = Y.shape
        f = rgb_small.astype(np.float32)
        ground = Y[int(0.6 * h):]
        g = float(np.median(ground)) if ground.size else float(np.median(Y))
        top = float(np.percentile(Y, 99.5))
        s_b = np.clip((Y - g) / max(0.6 * (top - g), 8.0), 0, 1)
        mu = cv2.boxFilter(Y, -1, (5, 5))
        mu2 = cv2.boxFilter(Y * Y, -1, (5, 5))
        lstd = np.sqrt(np.maximum(mu2 - mu * mu, 0))
        s_t = np.clip(1.0 - (lstd - 4.0) / 8.0, 0, 1)
        if ir:
            s_c = np.ones_like(Y)
        else:
            db = f[..., 2] - f[..., 0]
            gex = f[..., 1] - 0.5 * (f[..., 0] + f[..., 2])
            s_c = np.clip((db + 15.0) / 15.0, 0, 1) * np.clip((15.0 - gex) / 10.0, 0, 1)
        yn = (np.arange(h, dtype=np.float32) + 0.5) / h
        s_p = np.clip((sky_max_y - yn) / 0.3, 0, 1)[:, None]
        return (s_b * s_t * s_c * s_p).astype(np.float32)

    def update(self, score: np.ndarray):
        if score.shape != self.acc.shape:
            self.acc = cv2.resize(self.acc, (score.shape[1], score.shape[0]), interpolation=cv2.INTER_LINEAR)
        self.n += 1
        a = max(1.0 / self.n, 1.0 / self.memory)
        self.acc += a * (score - self.acc)

    @property
    def confident(self) -> bool:
        return self.n >= self.min_frames

    def mask(self, current_score: Optional[np.ndarray] = None):
        """(bool mask, state) - learned when confident, else the current frame's thresholded score.

        Pass ``current_score=None`` when the frame is not usable for a bootstrap (IR mode or a dark
        frame): the score is *relative* brightness, and in IR the illuminator makes the near
        foreground (box roof, whiteboard) the brightest smooth thing in the frame. A mask from such
        a frame would point every night-sky measurement at the box instead of the sky."""
        if self.confident:
            raw, state = self.acc > self.thr, "learned"
        elif current_score is not None:
            raw, state = current_score > self.thr, "bootstrap"
        else:
            return np.zeros_like(self.acc, bool), "none"
        m = cv2.morphologyEx(raw.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, lab, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        min_area = max(4, int(0.0015 * m.size))
        keep = np.zeros(n, bool)
        keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_area
        return keep[lab], state


# ============================================================================ twilight light curve
class TwilightTracker:
    """Online sustained-threshold-crossing detector on a binned log-luma light curve (per mode)."""

    def __init__(self, thresholds=(100.0, 50.0, 25.0, 12.0), bin_s=60.0, hold_s=600.0, pre_s=600.0,
                 max_gap_s=180.0, fit_half_s=600.0, dedupe_s=4 * 3600.0, margin=0.1, keep_s=3 * 3600.0,
                 alt_window=(-18.0, 12.0), site=DEFAULT_SITE, gate=True):
        self.thresholds = [float(t) for t in thresholds]
        self.bin_s, self.hold_s, self.pre_s = float(bin_s), float(hold_s), float(pre_s)
        self.max_gap_s, self.fit_half_s, self.dedupe_s = float(max_gap_s), float(fit_half_s), float(dedupe_s)
        self.margin, self.keep_s = float(margin), float(keep_s)
        self.alt_window, self.site, self.gate = tuple(alt_window), tuple(site), bool(gate)
        self.series = {}
        self.emitted = []
        self._scanned = {}

    def add(self, t: float, value: Optional[float], mode: str = "day") -> list:
        if value is None or not np.isfinite(value) or value <= 0:
            return []
        d = self.series.setdefault(mode, deque())
        d.append((float(t), math.log(float(value))))
        while d and d[0][0] < t - self.keep_s:
            d.popleft()
        b = int(t // self.bin_s)
        if self._scanned.get(mode) == b:          # scan once per completed bin (cheap at 5-s frames)
            return []
        self._scanned[mode] = b
        return self._scan(mode, float(t))

    def _binned(self, mode):
        a = np.array(self.series[mode], np.float64)
        b = np.floor(a[:, 0] / self.bin_s).astype(np.int64)
        ub, idx = np.unique(b, return_inverse=True)
        tb = np.bincount(idx, a[:, 0]) / np.bincount(idx)
        vb = np.array([np.median(a[idx == k, 1]) for k in range(len(ub))])
        n = len(vb)
        sm = np.empty(n)
        for i in range(n):
            lo, hi = max(0, i - 2), min(n, i + 3)
            sm[i] = np.median(vb[lo:hi])
        return tb, sm

    def _recent(self, mode, T, event, t):
        return any(m == mode and abs(T0 - T) < 1e-9 and e == event and abs(t - te) < self.dedupe_s
                   for m, T0, e, te in self.emitted)

    def _scan(self, mode, now):
        d = self.series[mode]
        if len(d) < 8 or d[-1][0] - d[0][0] < self.pre_s + self.hold_s:
            return []
        tb, sm = self._binned(mode)
        out = []
        for T in self.thresholds:
            lt = math.log(T)
            for event in ("dusk", "dawn"):
                if event == "dusk":
                    cand = np.nonzero((sm[:-1] >= lt) & (sm[1:] < lt))[0]
                else:
                    cand = np.nonzero((sm[:-1] < lt) & (sm[1:] >= lt))[0]
                for i in cand[::-1]:
                    m = self._check(tb, sm, i, lt, event, now)
                    if m is None:
                        continue
                    if self._recent(mode, T, event, m["t"]):
                        break
                    m.update(threshold=T, series=f"sky_luma_{T:g}" + ("" if mode == "day" else f"_{mode}"), mode=mode)
                    self.emitted.append((mode, T, event, m["t"]))
                    out.append(m)
                    break
        return out

    def _check(self, tb, sm, i, lt, event, now):
        t_int = tb[i] + (tb[i + 1] - tb[i]) * (sm[i] - lt) / (sm[i] - sm[i + 1])
        if t_int + self.hold_s > now or tb[-1] < t_int + self.hold_s:
            return None
        before = (tb < t_int) & (tb >= t_int - self.pre_s)
        after = (tb > t_int) & (tb <= t_int + self.hold_s)
        if before.sum() < 0.5 * self.pre_s / self.bin_s or after.sum() < 0.6 * self.hold_s / self.bin_s:
            return None
        sgn = 1.0 if event == "dusk" else -1.0      # dusk: before above, after below
        if np.any(sgn * (sm[before] - lt) < -self.margin) or np.any(sgn * (sm[after] - lt) > self.margin):
            return None
        win = (tb >= t_int - self.pre_s) & (tb <= t_int + self.hold_s)
        if np.any(np.diff(tb[win]) > self.max_gap_s + self.bin_s):
            return None
        fw = np.abs(tb - t_int) <= self.fit_half_s
        t_c, slope = t_int, None
        if fw.sum() >= 4:
            A = np.vstack([tb[fw] - t_int, np.ones(fw.sum())]).T
            (k, c), *_ = np.linalg.lstsq(A, sm[fw], rcond=None)
            if (event == "dusk" and k < 0) or (event == "dawn" and k > 0):
                tc = t_int + (lt - c) / k
                if abs(tc - t_int) < self.fit_half_s:
                    t_c = tc
                slope = k * 60.0
            else:
                return None
        alt, _ = solar_altaz(t_c, *self.site)
        alt2, _ = solar_altaz(t_c + 600.0, *self.site)
        if self.gate:
            if not (self.alt_window[0] <= alt <= self.alt_window[1]):
                return None
            if (event == "dusk") != (alt2 < alt):
                return None
        return {"t": float(t_c), "event": event, "slope_per_min": slope, "sun_alt_approx_deg": alt,
                "t_interp": float(t_int), "method": "luma_crossing_online"}


# ============================================================================ analyzer
DEFAULTS = {
    "work_width": 256,
    "photometry_interval_s": 15.0,       # sky/scene photometry cadence (frame time)
    "weather_interval_s": 60.0,          # cloud / direct sun / fog cadence
    "mask_memory_frames": 1000,
    "mask_min_frames": 3,
    "mask_threshold": 0.5,
    "mask_min_sun_alt": 3.0,
    "mask_save_every": 120,
    "mask_loaded_weight": 100,
    "save_mask": True,
    "sky_max_y": 0.7,
    "mode_hysteresis": 2,
    "approx_site": None,
    "twilight_thresholds": [100.0, 50.0, 25.0, 12.0],
    "twilight_bin_s": 60.0,
    "twilight_hold_s": 600.0,
    "twilight_pre_s": 600.0,
    "twilight_max_gap_s": 180.0,
    "twilight_sun_alt_window": [-18.0, 12.0],
    "twilight_gate": True,
    "cloud_rb_threshold": 0.78,
    "cloud_min_px": 30,
    "cloud_max_clipped": 0.6,
    "cloud_min_sun_alt": 3.0,
    "fog_far_band": [0.35, 0.55],
    "fog_near_band": [0.75, 1.0],
    "exclude_norm": [],                  # [[x0,y0,x1,y1], ...] excluded from ground statistics (e.g. the box)
    "archive_dir": None,
}


class SkyAnalyzer(Analyzer):
    name = "sky"
    wants_frames = True
    min_interval_s = 0.0

    def __init__(self, config=None):
        super().__init__(config)
        cfg = config or {}
        self.p = {**DEFAULTS, **{k: v for k, v in cfg.items() if k != "_global"}}
        self.site = site_from_config(cfg)
        self.model: Optional[SkyMaskModel] = None
        self.ir = None
        self._votes = 0
        self._last_phot = None
        self._last_weather = None
        self._clear_ref = {}             # sun-alt bin -> clear-sky luma reference (sky / scene ratio)
        self._fog_base = None
        self._fog_n = 0
        self._loaded = False
        self.twilight = TwilightTracker(self.p["twilight_thresholds"], self.p["twilight_bin_s"], self.p["twilight_hold_s"],
                                        self.p["twilight_pre_s"], self.p["twilight_max_gap_s"],
                                        alt_window=self.p["twilight_sun_alt_window"], site=self.site,
                                        gate=self.p["twilight_gate"])

    # ------------------------------------------------------------------ helpers
    def _archive_dir(self, ctx) -> Optional[Path]:
        a = self.p.get("archive_dir") or (self.config.get("_global") or {}).get("archive_dir") or ctx.config.get("archive_dir")
        return Path(a) / "sky" if a else None

    def _mode(self, raw_ir: bool) -> bool:
        if self.ir is None:
            self.ir = raw_ir
        elif raw_ir != self.ir:
            self._votes += 1
            if self._votes >= self.p["mode_hysteresis"]:
                self.ir, self._votes = raw_ir, 0
        else:
            self._votes = 0
        return self.ir

    def _ensure_model(self, shape, ctx):
        if self.model is not None and self.model.acc.shape == shape:
            return
        self.model = SkyMaskModel(shape, self.p["mask_memory_frames"], self.p["mask_min_frames"], self.p["mask_threshold"])
        if not self._loaded:
            self._loaded = True
            d = self._archive_dir(ctx)
            p = d / "sky_mask_acc.png" if d else None
            if p is not None and p.exists():
                try:
                    acc = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
                    if acc is not None and abs(acc.shape[1] / acc.shape[0] - shape[1] / shape[0]) < 0.02:
                        self.model.acc = cv2.resize(acc, (shape[1], shape[0])).astype(np.float32) / 255.0
                        self.model.n = int(self.p["mask_loaded_weight"])
                        log.info("sky: loaded sky mask from %s", p)
                except Exception as e:  # never fatal
                    log.warning("sky: could not load sky mask %s: %s", p, e)

    def _save_mask(self, ctx, mask):
        if not self.p["save_mask"]:
            return
        d = self._archive_dir(ctx)
        if d is None:
            return
        try:
            d.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(d / "sky_mask.png"), (mask.astype(np.uint8) * 255))
            cv2.imwrite(str(d / "sky_mask_acc.png"), np.clip(self.model.acc * 255, 0, 255).astype(np.uint8))
            shared(ctx)["mask_path"] = str(d / "sky_mask.png")
        except Exception as e:
            log.warning("sky: could not save sky mask to %s: %s", d, e)

    def _obs(self, kind, frame, value, conf, ts=None, frame_id="frame"):
        return Observation(kind=kind, ts=ts or frame.real_ts, value=clean(value), analyzer=self.name,
                           confidence=float(conf), frame_id=frame.id if frame_id == "frame" else frame_id,
                           ts_capture=frame.capture_ts)

    @staticmethod
    def _due(last, t, interval):
        return last is None or (t - last) >= interval - 1e-6 or t < last

    # ------------------------------------------------------------------ main
    def on_frame(self, frame, ctx: Context):
        out = []
        img = frame.image
        H, W = img.shape[:2]
        small, _ = downscale(img, int(self.p["work_width"]))
        h, w = small.shape[:2]
        Y = luma(small)
        ir = self._mode(is_ir_raw(small))
        t = frame.real_ts.timestamp()
        alt, az = solar_altaz(t, *self.site)
        st = shared(ctx)
        st.update(frame_index=frame.index, ts=frame.real_ts, ir_mode=ir, sun_alt_approx=alt, sun_az_approx=az)

        # ---- sky mask
        self._ensure_model((h, w), ctx)
        score = SkyMaskModel.score(small, Y, ir, self.p["sky_max_y"])
        updated = False
        if not ir and alt > self.p["mask_min_sun_alt"] and np.percentile(Y, 98) > 60:
            self.model.update(score)
            updated = True
        mask, mstate = self.model.mask(score)
        st["mask"], st["mask_state"], st["mask_n"] = mask, mstate, self.model.n
        if updated and self.model.n >= self.model.min_frames and (
                self.model.n == self.model.min_frames or self.model.n % int(self.p["mask_save_every"]) == 0):
            self._save_mask(ctx, mask)

        # ---- sky region statistics
        region = "sky"
        sky_px = mask
        if sky_px.sum() < max(10, 0.002 * h * w):
            sky_px = np.zeros((h, w), bool)
            sky_px[: max(1, int(0.12 * h))] = True
            region = "top_band"
        f = small.astype(np.float32)
        ys = Y[sky_px]
        rgb = f[sky_px]
        clipped = (rgb.max(axis=1) >= 250)
        sky_luma = float(ys.mean())
        scene_luma = float(Y.mean())
        st["luma"], st["region"] = sky_luma, region

        # ---- twilight light curve (every frame; markers only from the learned/bootstrapped sky)
        if region == "sky":
            for m in self.twilight.add(t, sky_luma, "ir" if ir else "day"):
                tc = datetime.fromtimestamp(m["t"], UTC)
                val = {"luma": m["threshold"], "region": "twilight_marker", "ir_mode": ir,
                       "twilight_marker": {**m, "t_cross": iso(tc)}}
                conf = 0.55 if m.get("slope_per_min") is not None and abs(m["slope_per_min"]) > 0.005 else 0.35
                out.append(self._obs("sky_photometry", frame, val, conf, ts=tc, frame_id=None))
                log.info("sky: twilight marker %s %s luma %g at %s", m["event"], m["mode"], m["threshold"], iso(tc))

        # ---- photometry
        if self._due(self._last_phot, t, self.p["photometry_interval_s"]):
            self._last_phot = t
            lin = srgb_to_linear(rgb[~clipped]) if (~clipped).sum() >= 5 else srgb_to_linear(rgb)
            lm = lin.mean(axis=0)
            cct, duv = (None, None) if ir else cct_from_linear_rgb(*lm)
            hsv = cv2.cvtColor(np.ascontiguousarray(small), cv2.COLOR_RGB2HSV)
            sat = hsv[..., 1][sky_px].astype(np.float32) / 255.0
            out.append(self._obs("sky_photometry", frame, {
                "luma": sky_luma, "luma_median": float(np.median(ys)), "r": float(rgb[:, 0].mean()),
                "g": float(rgb[:, 1].mean()), "b": float(rgb[:, 2].mean()), "cct_k": cct, "duv": duv,
                "sat": float(sat.mean()), "br_ratio": float(lm[2] / max(lm[0], 1e-6)),
                "clipped_frac": float(clipped.mean()), "n_px": int(sky_px.sum()), "sky_frac": float(sky_px.mean()),
                "sky_to_scene": sky_luma / max(scene_luma, 1.0), "region": region, "mask_state": mstate,
                "ir_mode": ir, "sun_alt_approx_deg": alt}, 0.7 if region == "sky" else 0.4))
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            cy0, cx0 = max(0, H // 2 - 160), max(0, W // 2 - 256)
            noise = immerkaer_noise(gray[cy0:cy0 + 320, cx0:cx0 + 512])
            clip_all = float((f.max(axis=2) >= 250).mean())
            dark = float((Y < 16).mean())
            p5, p50, p95 = np.percentile(Y, [5, 50, 95])
            hint = "over" if clip_all > 0.08 else ("under" if p95 < 50 else "ok")
            ground = ~mask & (np.arange(h)[:, None] >= 0.45 * h)
            out.append(self._obs("scene_photometry", frame, {
                "luma": scene_luma, "luma_median": float(p50), "p5": float(p5), "p95": float(p95),
                "clipped_frac": clip_all, "dark_frac": dark, "exposure_hint": hint, "noise_sigma": noise,
                "ground_luma": float(Y[ground].mean()) if ground.any() else None,
                "sat_median": float(np.median(hsv[..., 1])),
                "ir_mode": ir, "sun_alt_approx_deg": alt, "w": W, "h": H}, 0.8))

        # ---- weather-ish measures (daytime only)
        if not ir and self._due(self._last_weather, t, self.p["weather_interval_s"]):
            self._last_weather = t
            cf = self._cloud(frame, ctx, small, Y, mask, alt, sky_luma, scene_luma, region)
            if cf:
                out.append(cf)
            ds = self._direct_sun(frame, ctx, small, Y, mask, alt)
            if ds:
                out.append(ds)
            fg = self._fog(frame, small, Y, mask, sky_luma, alt)
            if fg:
                out.append(fg)
        elif ir:
            st["direct_sun"] = False
        return out

    # ------------------------------------------------------------------ cloud fraction
    def _cloud(self, frame, ctx, small, Y, mask, alt, sky_luma, scene_luma, region):
        if region != "sky" or alt < self.p["cloud_min_sun_alt"]:
            return None
        h, w = Y.shape
        f = small.astype(np.float32)
        sel = mask.copy()
        sun = (ctx.state.get("sun") or {}).get("last")
        if sun and sun.get("w"):
            sx, sy = sun["x"] * w / sun["w"], sun["y"] * h / sun["h"]
            yy, xx = np.mgrid[0:h, 0:w]
            sel &= (xx - sx) ** 2 + (yy - sy) ** 2 > (0.08 * w) ** 2
        n_all = int(sel.sum())
        if n_all < self.p["cloud_min_px"]:
            return None
        px = f[sel]
        clipped = px.max(axis=1) >= 250
        dark = Y[sel] < 20
        clip_frac = float(clipped.mean())
        if clip_frac > self.p["cloud_max_clipped"]:
            return None
        ok = ~clipped & ~dark
        if ok.sum() < self.p["cloud_min_px"]:
            return None
        rb = (px[ok, 0] + 1.0) / (px[ok, 2] + 1.0)
        pc = 1.0 / (1.0 + np.exp(-(rb - self.p["cloud_rb_threshold"]) / 0.04))
        mu = cv2.boxFilter(Y, -1, (5, 5))
        mu2 = cv2.boxFilter(Y * Y, -1, (5, 5))
        lstd = np.sqrt(np.maximum(mu2 - mu * mu, 0))[sel][ok]
        texture = float((lstd > 6.0).mean())
        ratio = sky_luma / max(scene_luma, 1.0)
        abin = int(alt // 5)
        ref = self._clear_ref.get(abin)
        b_rel = ratio / ref if ref else None
        n_eff = float(ok.sum())
        frac_cloud = float(pc.mean())
        if clip_frac > 0.05 and b_rel is not None and b_rel > 1.2:
            frac = (frac_cloud * n_eff + 0.7 * clip_frac * n_all) / (n_eff + clip_frac * n_all)
        else:
            frac = frac_cloud
        if frac < 0.15:          # learn the clear-sky brightness reference (sky/scene ratio) per sun-alt bin
            self._clear_ref[abin] = ratio if ref is None else ref + 0.1 * (ratio - ref)
        conf = (0.2 + 0.25 * min(1.0, n_eff / 400.0)) * (1.0 - clip_frac)
        if 0.3 < frac < 0.7:
            conf *= 0.8
        return self._obs("cloud_fraction", frame, {
            "fraction": frac, "method": "rb_ratio", "clear_frac": float((pc < 0.5).mean()), "clipped_frac": clip_frac,
            "texture": texture, "rb_median": float(np.median(rb)), "brightness_vs_clear": b_rel, "n_px": int(n_eff),
            "sky_frac": float(mask.mean()), "sun_alt_approx_deg": alt}, conf)

    # ------------------------------------------------------------------ direct sun
    def _direct_sun(self, frame, ctx, small, Y, mask, alt):
        if alt < -1.0:                   # sun down everywhere in the domain: nothing to say
            shared(ctx)["direct_sun"] = False
            return None
        h, w = Y.shape
        ground = ~mask & (np.arange(h)[:, None] >= 0.45 * h) & ~rect_mask(h, w, self.p["exclude_norm"])
        if ground.sum() < 50:
            return None
        f = small.astype(np.float32)
        lin = srgb_to_linear(np.clip(Y, 0, 255)).astype(np.float32) + 1e-4
        ll = np.log(lin)
        lg = ll[ground]
        p10, p95 = np.percentile(lg, [10, 95])
        dyn = float(np.exp(p95 - p10))
        thr = otsu_threshold(lg)
        hi_c, lo_c = lg >= thr, lg < thr
        class_ratio = float(np.exp(lg[hi_c].mean() - lg[lo_c].mean())) if hi_c.any() and lo_c.any() else 1.0
        bright = ground & (ll >= thr)
        bright = cv2.morphologyEx(bright.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)) > 0
        shade = ground & (ll < thr)
        sunlit_fraction = float(bright.sum() / ground.sum()) if class_ratio >= 3.0 else 0.0
        warm = None
        if bright.sum() >= 5 and shade.sum() >= 5:
            lrb = np.log((f[..., 0] + 4.0) / (f[..., 2] + 4.0))
            warm = float(lrb[bright].mean() - lrb[shade].mean())
        s_dyn = float(np.clip((np.log10(dyn) - 0.8) / 0.6, 0, 1))
        s_cls = float(np.clip((class_ratio - 2.0) / 2.0, 0, 1)) * float(np.clip(sunlit_fraction / 0.05, 0, 1))
        s_warm = 0.5 if warm is None else float(np.clip(warm / 0.15, 0, 1))
        score = 0.3 * s_dyn + 0.5 * s_cls + 0.2 * s_warm
        present = bool(score > 0.55 and alt > 2.0)
        shared(ctx)["direct_sun"] = present
        shared(ctx)["direct_sun_score"] = score
        conf = 0.25 + 0.3 * abs(score - 0.55) / 0.45 if alt > 2.0 else 0.5
        return self._obs("direct_sun", frame, {
            "present": present, "sunlit_fraction": sunlit_fraction, "dynamic_range": dyn, "class_ratio": class_ratio,
            "warm_shift": warm, "score": score, "sun_alt_approx_deg": alt}, min(conf, 0.55))

    # ------------------------------------------------------------------ fog
    @staticmethod
    def _band_contrast(Y, sel):
        if sel.sum() < 30:
            return None
        L = Y.astype(np.float32) + 2.0
        hp = cv2.GaussianBlur(L, (0, 0), 0.8) - cv2.GaussianBlur(L, (0, 0), 4.0)
        loc = cv2.GaussianBlur(L, (0, 0), 4.0)
        return float(np.sqrt(np.mean((hp[sel] / loc[sel]) ** 2)))

    def _fog(self, frame, small, Y, mask, sky_luma, alt):
        if alt < 0.0:
            return None
        h, w = Y.shape
        rows = (np.arange(h) + 0.5)[:, None] / h
        excl = rect_mask(h, w, self.p["exclude_norm"])
        fb, nb = self.p["fog_far_band"], self.p["fog_near_band"]
        far = (rows >= fb[0]) & (rows < fb[1]) & ~mask & ~excl
        near = (rows >= nb[0]) & (rows <= nb[1]) & ~mask & ~excl
        cf, cn = self._band_contrast(Y, far), self._band_contrast(Y, near)
        if cf is None or cn is None or cn < 1e-4:
            return None
        ratio = cf / cn
        far_luma = float(Y[far].mean())
        airlight = far_luma / max(sky_luma, 1.0)
        dc = cv2.erode(small.min(axis=2), np.ones((5, 5), np.uint8)).astype(np.float32)
        A = max(sky_luma, 1.0)
        haze = float(np.clip(0.95 * dc[far].mean() / A, 0, 1))
        if self._fog_base is None:
            self._fog_base = ratio
        drop = float(np.clip(1.0 - ratio / max(self._fog_base, 1e-6), 0, 1))
        if self._fog_n >= 10:
            present = drop > 0.45 and (airlight > 0.6 or haze > 0.5)
            conf = 0.3 + 0.2 * min(drop, 1.0) if present else 0.3
        else:                            # no baseline yet: absolute heuristics only, low confidence
            present = cf < 0.02 and airlight > 0.75 and haze > 0.5
            conf = 0.2
        if not present:                  # clear frames teach the baseline (fast up, slow down)
            a = 0.3 if ratio > self._fog_base else 0.02
            self._fog_base += a * (ratio - self._fog_base)
            self._fog_n += 1
        return self._obs("fog", frame, {
            "present": bool(present), "contrast_drop": drop, "far_contrast": cf, "near_contrast": cn,
            "ratio": ratio, "baseline": self._fog_base, "airlight": airlight, "haze_darkchannel": haze,
            "n_baseline": self._fog_n, "method": "far_near_contrast"}, conf)
