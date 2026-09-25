"""Rain, drops, streaks, wet surfaces, condensation and frost on the box (analyzer name: ``rain``).

Geometry sets the limits. A 3 mm drop on the box wall 5 m away is ~0.5 px wide at 1280 px
and 70 deg HFOV. Drops on the box are therefore only visible as sparkles (specular
highlights, often bright and sub-pixel) or as coalesced drops and rivulets of 1-3 px. That
is why the drop search runs at up to ``work_width`` = 960 px inside ``box_roi_norm``. Drops
on the camera lens or housing are large blurry blobs (10-60 px) and are searched over the
whole frame at a coarse scale.

rain_visual
-----------
* Drops: difference-of-Gaussians (DoG) blobs, fine (sigma 0.8/2.4 px, box ROI) and coarse
  (sigma 3/9 px on a 320-px copy, anywhere: lens drops). Both polarities count, because a
  drop acts as a small lens showing an inverted, often brighter sky. Drops stick, so the
  test works on DoG *changes*:
  - a new drop is a peak of D_t - g D_{t-2} above max(5 robust sigma, 6 levels), where g is
    the least-squares gain, so a global light or exposure change cancels;
  - it must already be present at t-1 (D_{t-1} - g' D_{t-2} > 0.6 thr);
  - it must be unchanged between t-1 and t (|D_t - g'' D_{t-1}| < 0.5 of the t-2 -> t change):
    swaying twigs and grass behind the transparent walls move a little every frame and fail this;
  - edge-like responses are rejected by the Hessian ratio test (tr^2/det < (r+1)^2/r, r = 5).
  Static texture of any strength cancels in the difference, so near-threshold bark or heather
  blobs cannot flicker into "new drops". Blobs inside large changed regions are ignored
  (frame difference, blurred, > 20 levels, components > 1 % of the ROI: Anja moving, a hand,
  the whiteboard). The count per 1e5 ROI pixels, minus a learned dry-weather base rate,
  gives the drop term (``drops_heavy_per_1e5`` = 20, i.e. ~55 new drops per frame in the
  default ROI at 960 px, saturates it).
* Streaks: falling drops are motion-blurred into short near-vertical lines (very visible
  under the IR illuminator at night). They are transient: positive frame difference >
  max(5 sigma, 10), components with aspect >= 3, length 4-60 px and orientation within
  25 deg of vertical, and without a negative-difference partner within 5 px (a moved twig).
* Wet-surface darkening: wet ground has a lower albedo. The ground-band luma relative to
  sky luma (roughly exposure-invariant) is compared with a dry baseline. It is only a
  supporting cue (weight 0.2), because clouds change it too.
The combined intensity is in [0, 1] (< 0.4 light, < 0.7 moderate, else heavy, the
convention of bridges/met.py). ``present`` requires the raw score above ``present_thr`` in
at least 2 of the last 3 frames. The analyzer emits every ``emit_interval_s`` and on
every state change. Confidences are conservative: <= 0.6 for rain, 0.3 for "no rain".

condensation
------------
The box ROI is split into tiles (8 x 6 at ~320 px). Per tile it measures the local contrast
(RMS of the high-pass / mean), the dark channel (min over RGB and 5x5; a white veil lifts
it) and the rim brightening (ROI border band vs interior; frost and condensation start at
the edges and corners). Each has a per-mode baseline that adapts quickly towards "clear"
and slowly away from it. Tile contrast is normalised by the contrast change *outside* the
ROI, so fog, low light or exposure changes that affect everything do not count. A tile is
"fogged" when its relative contrast < 0.5. ``present`` requires > 30 % fogged tiles plus a
veil, a rim, or > 60 % fogged tiles, for ``cond_persist`` consecutive evaluations, after
>= 5 baseline frames. ``type_hint`` is 'frost?' for a bright veil with a rim, else
'condensation'.

Failure modes: drops on the box are sub-pixel in 720p streams, so only heavy rain or lens
drops are seen; stream compression erases sparkles; snowflakes also make streaks; moving
branch tips can make persistent blobs; direct sun on the walls reduces contrast like
condensation (the global normalisation only partly helps); the box ROI is a fixed
configuration (``box_roi_norm``, normalised [x0, y0, x1, y1]).
"""
from __future__ import annotations

import logging
import math
from collections import deque
from typing import Optional

import cv2
import numpy as np

from ..types import Observation
from .base import Analyzer, Context
from .sky import clean, downscale, frame_ir_mode, luma, rect_mask, rgb_frame, sky_mask_for

log = logging.getLogger("hordewatch.rain")


# ============================================================================ blob / streak primitives
def dog(Y: np.ndarray, s1: float, s2: float):
    """(difference-of-Gaussians map, the sigma-s1 smoothed image)."""
    g1 = cv2.GaussianBlur(Y, (0, 0), s1)
    return g1 - cv2.GaussianBlur(Y, (0, 0), s2), g1


def _gain(a: np.ndarray, b: np.ndarray, roi: np.ndarray) -> float:
    """Least-squares gain g with a ~ g b over roi (global illumination / exposure change of the texture)."""
    bb = float((b[roi] ** 2).sum())
    return float(np.clip((a[roi] * b[roi]).sum() / bb, 0.5, 2.0)) if bb > 1e-6 else 1.0


def new_persistent_blobs(d0: np.ndarray, d1: np.ndarray, d2: np.ndarray, g1: np.ndarray, roi: np.ndarray,
                         s2: float, k_sigma: float = 5.0, min_amp: float = 6.0, ignore: Optional[np.ndarray] = None,
                         edge_r: float = 5.0, max_blobs: int = 3000, stable_frac: float = 0.5):
    """Blobs that are present at t (d0) and t-1 (d1) but were absent at t-2 (d2): drops that landed and stuck.

    Works on DoG *changes* (d0 - g d2, d1 - g' d2 with least-squares gains), so static texture -
    however strong - cancels, and near-threshold texture cannot flicker into a "new" blob.
    A stuck drop is also *unchanged* between t-1 and t: the change d0 - g'' d1 at the peak must be
    below ``stable_frac`` of the t-2 -> t change. This rejects swaying twig tips and grass seen
    through the transparent box (each frame at a slightly different place: present at t and t-1
    in a 3x3 neighbourhood, but never the same), the dominant false alarm in wind.
    Returns ((N, 3) [x, y, polarity], noise sigma, threshold).
    """
    dd = d0 - _gain(d0, d2, roi) * d2
    dd1 = d1 - _gain(d1, d2, roi) * d2
    dd01 = np.abs(d0 - _gain(d0, d1, roi) * d1)
    vals = dd[roi]
    if vals.size < 50:
        return np.zeros((0, 3), np.float32), 0.0, 0.0
    sigma = 1.4826 * float(np.median(np.abs(vals - np.median(vals)))) + 1e-3
    thr = max(k_sigma * sigma, min_amp)
    k = max(3, int(2 * round(s2) + 1))
    ker = np.ones((k, k), np.uint8)
    dxx = cv2.Sobel(g1, cv2.CV_32F, 2, 0, ksize=3)
    dyy = cv2.Sobel(g1, cv2.CV_32F, 0, 2, ksize=3)
    dxy = cv2.Sobel(g1, cv2.CV_32F, 1, 1, ksize=3)
    tr = dxx + dyy
    det = dxx * dyy - dxy * dxy
    blobby = (det > 0) & (tr * tr < det * (edge_r + 1) ** 2 / edge_r)
    valid = roi & blobby if ignore is None else roi & blobby & ~ignore
    out = []
    for pol in (1.0, -1.0):
        a = pol * dd
        pk = ((a >= cv2.dilate(a, ker)) & (a > thr) & valid & (cv2.dilate(pol * dd1, np.ones((3, 3), np.uint8)) > 0.6 * thr)
              & (dd01 < stable_frac * a))
        ys, xs = np.nonzero(pk)
        if len(xs) > max_blobs:
            o = np.argsort(-a[ys, xs])[:max_blobs]
            ys, xs = ys[o], xs[o]
        out.append(np.stack([xs, ys, np.full(len(xs), pol)], 1).astype(np.float32))
    return np.concatenate(out, 0), sigma, thr


def detect_streaks(Y: np.ndarray, Yprev: np.ndarray, roi: np.ndarray, ignore: np.ndarray, k_sigma: float = 5.0,
                   min_len: float = 4.0, max_len: float = 60.0, max_tilt_deg: float = 25.0, moved_px: int = 5,
                   moved_frac: float = 0.3) -> int:
    """Count transient thin near-vertical bright streaks (falling rain) in the positive frame difference.

    A thin object that *moved* (a hanging birch twig, grass, a cord swaying in the wind) leaves a
    positive difference where it is now and a negative one where it was, a few px away. A rain
    streak has no such partner (the streaks of the previous frame are elsewhere). Components with
    >= ``moved_frac`` of their pixels within ``moved_px`` of the opposite-sign difference are
    therefore not counted. In heavy rain (~40 streaks) the negative streaks cover ~3 % of the
    ROI, so few true streaks are lost."""
    D = Y - Yprev
    vals = D[roi]
    if vals.size < 50:
        return 0
    sigma = 1.4826 * float(np.median(np.abs(vals - np.median(vals)))) + 1e-3
    lev = max(k_sigma * sigma, 10.0)
    m = ((D > lev) & roi & ~ignore).astype(np.uint8)
    k = 2 * int(moved_px) + 1
    neg_near = cv2.dilate((D < -lev).astype(np.uint8), np.ones((k, k), np.uint8)) > 0
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    cnt = 0
    for k in range(1, n):
        a = stats[k, cv2.CC_STAT_AREA]
        if a < 3 or a > 300:
            continue
        bx, by, bw, bh = stats[k, :4]
        ys, xs = np.nonzero(lab[by:by + bh, bx:bx + bw] == k)
        if len(xs) < 3:
            continue
        if float(neg_near[by + ys, bx + xs].mean()) >= moved_frac:      # a moved thin object, not a falling drop
            continue
        (cx, cy), (rw, rh), ang = cv2.minAreaRect(np.stack([xs, ys], 1).astype(np.float32))
        L, Wd = max(rw, rh), max(min(rw, rh), 1.0)
        if L < min_len or L > max_len or L / Wd < 3.0:
            continue
        cov = np.cov(xs.astype(np.float64), ys.astype(np.float64))
        ev, evec = np.linalg.eigh(cov)
        vx, vy = evec[:, 1]
        tilt = math.degrees(math.atan2(abs(vx), abs(vy)))      # 0 = vertical
        if tilt <= max_tilt_deg:
            cnt += 1
    return cnt


def _change_mask(Y, Yprev, roi_area, thr=20.0, min_frac=0.01):
    d = cv2.GaussianBlur(np.abs(Y - Yprev), (0, 0), 2.0)
    m = (d > thr).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    big = np.zeros(n, bool)
    big[1:] = stats[1:, cv2.CC_STAT_AREA] > min_frac * roi_area
    mask = big[lab].astype(np.uint8)
    return cv2.dilate(mask, np.ones((7, 7), np.uint8)) > 0


# ============================================================================ analyzer
DEFAULTS = {
    "work_width": 960,
    "coarse_width": 320,
    "emit_interval_s": 60.0,
    "box_roi_norm": [0.2, 0.1, 0.8, 0.98],
    "blob_k_sigma": 5.0,
    "blob_min_amp": 6.0,
    "match_px": 2.0,
    "change_thr": 20.0,
    "change_min_frac": 0.01,
    "drops_heavy_per_1e5": 20.0,
    "lens_heavy": 6.0,
    "streaks_heavy": 40.0,
    "present_thr": 0.12,
    "persist_n": 2,
    "persist_of": 3,
    "cond_work_width": 320,
    "cond_tiles": [8, 6],
    "cond_persist": 3,
    "cond_min_baseline": 5,
    "cond_emit_interval_s": 60.0,
}


class _CondState:
    def __init__(self):
        self.base_c = None
        self.base_dc = None
        self.base_out = None
        self.base_rim = None
        self.n = 0
        self.streak = 0
        self.shape = None


class RainAnalyzer(Analyzer):
    name = "rain"
    wants_frames = True
    min_interval_s = 0.0

    def __init__(self, config=None):
        super().__init__(config)
        cfg = config or {}
        self.p = {**DEFAULTS, **{k: v for k, v in cfg.items() if k != "_global"}}
        self.hist = deque(maxlen=3)       # {Y, d_f (fine DoG), d_c (coarse DoG), chg (change mask), mode}
        self.raw_hist = deque(maxlen=int(self.p["persist_of"]))
        self.base_rate = 0.0
        self.wet_base = None
        self.present = False
        self._last_emit = None
        self._last_cond_emit = None
        self._window = []
        self.cond = {"day": _CondState(), "ir": _CondState()}
        self.cond_present = False

    def _obs(self, kind, frame, value, conf):
        return Observation(kind=kind, ts=frame.real_ts, value=clean(value), analyzer=self.name, confidence=float(conf),
                           frame_id=frame.id, ts_capture=frame.capture_ts)

    def on_frame(self, frame, ctx: Context):
        out = []
        frame = rgb_frame(frame)
        ir = frame_ir_mode(frame, ctx)
        mode = "ir" if ir else "day"
        t = frame.real_ts.timestamp()
        r = self._rain(frame, ctx, mode)
        emit = self._last_emit is None or t - self._last_emit >= self.p["emit_interval_s"] - 1e-6 or t < self._last_emit
        if r is not None:
            self._window.append(r)
            changed = r["present"] != self.present
            self.present = r["present"]
            if emit or changed:
                self._last_emit = t
                w = self._window
                self._window = []
                inten = max(x["raw"] for x in w)
                val = {**r, "intensity": inten if r["present"] else 0.0,
                       "level": ("light" if inten < 0.4 else "moderate" if inten < 0.7 else "heavy") if r["present"] else "none",
                       "n_frames": len(w), "ir_mode": ir}
                conf = min(0.6, 0.3 + 0.3 * min(1.0, inten / 0.5)) if r["present"] else 0.3
                out.append(self._obs("rain_visual", frame, val, conf))
        c = self._condensation(frame, ctx, mode)
        if c is not None:
            changed = c["present"] != self.cond_present
            self.cond_present = c["present"]
            if (self._last_cond_emit is None or t - self._last_cond_emit >= self.p["cond_emit_interval_s"] - 1e-6
                    or changed or t < self._last_cond_emit):
                self._last_cond_emit = t
                conf = min(0.5, 0.25 + 0.3 * c["fraction"]) if c["present"] else 0.25
                out.append(self._obs("condensation", frame, {**c, "ir_mode": ir}, conf))
        return out

    # ------------------------------------------------------------------ rain
    def _rain(self, frame, ctx, mode):
        img = frame.image
        small, s = downscale(img, int(self.p["work_width"]))
        h, w = small.shape[:2]
        Y = luma(small)
        roi = rect_mask(h, w, [self.p["box_roi_norm"]])
        d_f, g_f = dog(Y, 0.8, 2.4)
        coarse_img, cs = downscale(img, int(self.p["coarse_width"]))
        Yc = luma(coarse_img)
        d_c, g_c = dog(Yc, 3.0, 9.0)
        prev = self.hist[-1] if self.hist else None
        if prev is not None and (prev["Y"].shape != Y.shape or prev["mode"] != mode):
            self.hist.clear()
            self.raw_hist.clear()
            prev = None
        chg = (_change_mask(Y, prev["Y"], roi.sum(), self.p["change_thr"], self.p["change_min_frac"])
               if prev is not None else np.zeros_like(roi))
        self.hist.append({"Y": Y, "d_f": d_f, "d_c": d_c, "chg": chg, "mode": mode})
        if len(self.hist) < 3:
            return None
        h2, h1, _ = self.hist
        ignore = chg | h1["chg"]
        fine, sig_f, thr_f = new_persistent_blobs(d_f, h1["d_f"], h2["d_f"], g_f, roi, 2.4, self.p["blob_k_sigma"],
                                                  self.p["blob_min_amp"], ignore)
        n_new = int(len(fine))
        rate = n_new / max(roi.sum() / 1e5, 1e-6)
        full_c = np.ones(Yc.shape, bool)
        full_c[:4], full_c[-4:], full_c[:, :4], full_c[:, -4:] = False, False, False, False
        ig_c = cv2.resize(ignore.astype(np.uint8), (Yc.shape[1], Yc.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
        lens, _, _ = new_persistent_blobs(d_c, h1["d_c"], h2["d_c"], g_c, full_c, 9.0, self.p["blob_k_sigma"],
                                          max(self.p["blob_min_amp"], 8.0), ig_c)
        n_lens = int(len(lens))
        n_streaks = detect_streaks(Y, h1["Y"], roi, ignore)
        # wet-surface darkening (daytime, needs the sky analyzer's luma)
        dark = None
        sky = ctx.state.get("sky") or {}
        if mode == "day" and sky.get("luma"):
            band = np.zeros((h, w), bool)
            band[int(0.85 * h):] = True
            sm = sky_mask_for(ctx, h, w)
            if sm is not None:
                band &= ~sm
            if band.any():
                ratio = float(Y[band].mean()) / max(float(sky["luma"]), 1.0)
                if self.wet_base is None:
                    self.wet_base = ratio
                dark = float(np.clip(1.0 - ratio / max(self.wet_base, 1e-6), -1, 1))
        drop_term = float(np.clip((rate - self.base_rate) / self.p["drops_heavy_per_1e5"], 0, 1))
        lens_term = float(np.clip(n_lens / self.p["lens_heavy"], 0, 1))
        streak_term = float(np.clip(n_streaks / self.p["streaks_heavy"], 0, 1))
        main = max(drop_term, lens_term, streak_term)
        raw = 0.8 * main + (0.2 * float(np.clip((dark or 0.0) / 0.3, 0, 1)) if main > 0.05 else 0.0)
        self.raw_hist.append(raw)
        present = sum(x > self.p["present_thr"] for x in self.raw_hist) >= self.p["persist_n"]
        if not present and raw < 0.5 * self.p["present_thr"]:
            self.base_rate += 0.05 * (rate - self.base_rate)          # dry-weather false-alarm rate
            if dark is not None:
                ratio = (1.0 - dark) * self.wet_base
                self.wet_base += 0.02 * (ratio - self.wet_base)
        return {"present": bool(present), "raw": raw, "new_drops": n_new, "drop_rate_per_1e5": rate,
                "base_rate": self.base_rate, "lens_drops_new": n_lens, "streaks": n_streaks, "wet_darkening": dark,
                "dog_sigma": sig_f, "dog_thr": thr_f, "work_w": w, "box_roi_norm": self.p["box_roi_norm"]}

    # ------------------------------------------------------------------ condensation / frost
    def _condensation(self, frame, ctx, mode):
        small, _ = downscale(frame.image, int(self.p["cond_work_width"]))
        h, w = small.shape[:2]
        Y = luma(small)
        x0n, y0n, x1n, y1n = self.p["box_roi_norm"]
        x0, x1, y0, y1 = int(x0n * w), int(x1n * w), int(y0n * h), int(y1n * h)
        if x1 - x0 < 16 or y1 - y0 < 16:
            return None
        L = Y + 2.0
        loc = cv2.GaussianBlur(L, (0, 0), 3.0)
        hp = (L - loc) / loc
        hp2 = hp * hp
        dc = cv2.erode(small.min(axis=2), np.ones((5, 5), np.uint8)).astype(np.float32) / 255.0
        nx, ny = self.p["cond_tiles"]
        xs = np.linspace(x0, x1, nx + 1).astype(int)
        ys = np.linspace(y0, y1, ny + 1).astype(int)
        c = np.array([[math.sqrt(float(hp2[ys[j]:ys[j + 1], xs[i]:xs[i + 1]].mean())) for i in range(nx)] for j in range(ny)])
        d = np.array([[float(dc[ys[j]:ys[j + 1], xs[i]:xs[i + 1]].mean()) for i in range(nx)] for j in range(ny)])
        outside = np.ones((h, w), bool)
        outside[y0:y1, x0:x1] = False
        sm = sky_mask_for(ctx, h, w)
        if sm is not None:
            outside &= ~sm
        outside[:2], outside[-2:], outside[:, :2], outside[:, -2:] = False, False, False, False
        c_out = math.sqrt(float(hp2[outside].mean())) if outside.sum() > 50 else None
        bw = max(2, int(0.06 * min(x1 - x0, y1 - y0)))
        inner = Y[y0 + bw:y1 - bw, x0 + bw:x1 - bw]
        roi_sum = float(Y[y0:y1, x0:x1].sum())
        rim_mean = (roi_sum - float(inner.sum())) / max((y1 - y0) * (x1 - x0) - inner.size, 1)
        rim = rim_mean / max(float(inner.mean()), 1.0)
        S = self.cond[mode]
        if S.base_c is None or S.base_c.shape != c.shape or S.shape != (h, w):
            S.base_c, S.base_dc, S.base_out, S.base_rim, S.n, S.streak = c.copy(), d.copy(), c_out, rim, 1, 0
            S.shape = (h, w)
            return None
        g = (c_out / S.base_out) if (c_out is not None and S.base_out) else 1.0
        rel = (c / np.maximum(S.base_c, 1e-4)) / float(np.clip(g, 0.3, 1.5))
        fogged = rel < 0.5
        frac = float(fogged.mean())
        veil = float(np.mean(d - S.base_dc))
        rim_d = float(rim - S.base_rim)
        cand = S.n >= self.p["cond_min_baseline"] and frac > 0.3 and (veil > 0.06 or rim_d > 0.08 or frac > 0.6)
        S.streak = S.streak + 1 if cand else 0
        present = S.streak >= self.p["cond_persist"]
        if not cand and frac < 0.2:        # learn "clear box" baselines: fast towards clear, slow away
            a_c = np.where(c > S.base_c, 0.3, 0.02)
            S.base_c += a_c * (c - S.base_c)
            a_d = np.where(d < S.base_dc, 0.3, 0.02)
            S.base_dc += a_d * (d - S.base_dc)
            if c_out is not None:
                S.base_out = c_out if S.base_out is None else S.base_out + 0.1 * (c_out - S.base_out)
            S.base_rim += 0.1 * (rim - S.base_rim)
            S.n += 1
        return {"present": bool(present), "fraction": frac, "veil": veil, "rim_brightening": rim_d,
                "contrast_rel_median": float(np.median(rel)), "global_contrast_factor": float(g),
                "type_hint": ("frost?" if veil > 0.15 and rim_d > 0.1 else "condensation") if present else None,
                "n_baseline": S.n, "box_roi_norm": self.p["box_roi_norm"]}
