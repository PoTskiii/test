"""Sun disk / glare position and cast-shadow direction (analyzer name: ``sun``).

Both outputs feed the camera-model / site solver in ``hordewatch.astro``. A time series of
sun pixels fixes the camera's Earth-fixed orientation, and together with a level reference
it fixes latitude/longitude. Shadow directions on level ground point to the anti-solar
azimuth.

sun_pixel
---------
1. Work at ~640 px. Candidate cores are connected components of *all-channel* saturated
   pixels (min(R,G,B) >= ``sat_level``). If nothing is saturated (sun behind thin cloud),
   the brightest plateau (Y >= max - 6, max >= 200) is used instead.
2. Each candidate is scored on four things:
   * compactness: circularity 4 pi A / P^2;
   * a monotonic radial falloff of luma in four annuli outside the core (the glare/aureole
     of the sun decreases roughly like theta^-2; a white sign, the whiteboard or clipped
     overcast sky has a flat surround);
   * isotropy of the first annuli over 8 sectors (branches crossing the glare break it,
     so this term is soft);
   * a size prior and a sky context (the ring lies in the learned sky mask from the sky
     analyzer, else the upper 60 % of the frame).
3. Refinement at full resolution in a crop around the winner. A round core (circularity
   >= 0.6) gives the moment centroid (``method='core'``). An occluded, irregular core gives
   the peak of the glare, blurred at the core scale, with a quadratic subpixel fit
   (``method='glare'``).
4. Lens-flare ghosts are internal reflections that lie on the line from the sun through
   the optical centre, at p = S + k (C - S). Residual peaks (luma minus 31-px median) within
   1.2 % of the width of that line are counted. They slightly raise the confidence and are
   reported (``ghosts``: [[x, y, k], ...]); ``line_angle_deg`` is the sun-to-centre line
   direction.
5. Physical gates:
   * the solar altitude at the approximate site must be > ``min_sun_alt`` (-3 deg, which
     covers the whole domain), and nothing is reported in IR mode;
   * the solar azimuth should lie within the configured camera heading +- (hfov/2 + 25
     deg), otherwise confidence x0.4 (the heading is only approximately known);
   * a "sun" that stays within 4 px for more than 15 min is a static glare (lamp, sign,
     reflection). The real sun moves ~0.25 deg/min, i.e. ~60 px in 15 min at 1280 px/70 deg,
     so static glares are suppressed;
   * a position consistent with the previous detection at the solar angular rate earns a
     small bonus.
   Emitted every ``interval_s`` with value = {x, y (full-res px), xn, yn (x/w, y/h), radius,
   saturated, w, h, method, score, ghosts, n_ghosts, line_angle_deg, sun_alt_approx_deg,
   sun_az_approx_deg, az_prior_ok}.

shadow_direction
----------------
The structure tensor of log-luminance gradients on sunlit ground (default ROI: bottom 45 %,
outside the sky mask). Only *shadow edges* should count. Crossing from shade into sun, luma
rises by the direct/diffuse ratio, while log(B/R) falls, because the shade is lit only by the
blue sky. So a per-pixel weight wc = clip(-(grad logY . grad log(B/R)) / |grad logY|^2 / 0.15,
0, 1) keeps edges where colour and luma change in the "shadow" way and suppresses albedo and
material edges. In IR mode wc = 1. The weighted orientation histogram (line direction =
gradient direction + 90 deg) gives the dominant mode. Within +-15 deg of it, the structure
tensor sum_w [gx^2, gx gy; gx gy, gy^2] gives the refined orientation and the coherence
(lambda1 - lambda2) / (lambda1 + lambda2).
``angle_deg_image`` is measured from +x towards +y (clockwise on screen, 0-180, axial: a
line has a 180 deg ambiguity), the convention of ``astro.camera.ground_direction_azimuth``.
x, y is the weighted centroid of the contributing edges, at full resolution. strength =
coherence x the share of edge weight in the dominant mode. Only reported when the sky
analyzer does not say "no direct sun", the sun is > 5 deg up, and the coherence >= 0.25.

Failure modes: tree trunks (vertical edges) and the box frame dominate if the colour cue
fails (e.g. auto white balance on a grey day); dappled sunflecks give incoherent
orientations (low strength); uneven ground (hummocks) bends shadows; the sun disk is often
occluded by crowns, and forest exposures clip the whole sky around it, in which case no
detection is possible. Reflections of the sun in the box walls are specular and can mimic a
second sun; the sky-context term and the azimuth gate reduce them.
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
from .sky import (clean, downscale, focal_px, frame_ir_mode, luma, rect_mask, site_from_config, sky_mask_for,
                  solar_altaz)

log = logging.getLogger("hordewatch.sun")


# ============================================================================ sun disk / glare
def _circularity(comp_u8: np.ndarray, area: float) -> float:
    if area < 15:
        return 0.85                       # tiny blobs: perimeter estimate is meaningless
    cnts, _ = cv2.findContours(comp_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cnts:
        return 0.0
    P = max(cv2.arcLength(max(cnts, key=cv2.contourArea), True), 1e-6)
    return float(min(1.0, 4 * math.pi * area / (P * P)))


def _radial_profile(Y, core, cx, cy, r_eq, n_ann=4):
    h, w = Y.shape
    d = max(2.0, 0.6 * r_eq)
    R = r_eq + 1 + n_ann * d
    x0, x1 = max(0, int(cx - R - 1)), min(w, int(cx + R + 2))
    y0, y1 = max(0, int(cy - R - 1)), min(h, int(cy + R + 2))
    yy, xx = np.mgrid[y0:y1, x0:x1]
    rr = np.hypot(xx - cx, yy - cy)
    ang = np.arctan2(yy - cy, xx - cx)
    Yw, cw = Y[y0:y1, x0:x1], core[y0:y1, x0:x1]
    prof, sectors = [], []
    for i in range(n_ann):
        m = (rr >= r_eq + 1 + i * d) & (rr < r_eq + 1 + (i + 1) * d) & ~cw
        prof.append(float(Yw[m].mean()) if m.sum() >= 4 else np.nan)
        if i < 2:
            sec = ((ang[m] + math.pi) / (2 * math.pi) * 8).astype(int) % 8
            vals = Yw[m]
            sectors.append([float(vals[sec == s].mean()) if np.any(sec == s) else np.nan for s in range(8)])
    return np.array(prof), np.array(sectors, float), (x0, y0, x1, y1), rr


def find_sun(rgb: np.ndarray, work_width: int = 640, sat_level: int = 235, sky_mask: Optional[np.ndarray] = None,
             min_score: float = 0.3, max_candidates: int = 8) -> Optional[dict]:
    """Locate the sun disk / glare. Returns dict (full-res coordinates) or None."""
    H, W = rgb.shape[:2]
    small, s = downscale(rgb, work_width)
    h, w = small.shape[:2]
    Y = luma(small)
    ymax = float(Y.max())
    if ymax < 200:
        return None
    mn = small.min(axis=2)
    if int((mn >= sat_level).sum()) >= 2:
        core, saturated = mn >= sat_level, True
    else:
        core, saturated = Y >= max(200.0, ymax - 6.0), False
    core = cv2.morphologyEx(core.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, lab, stats, cents = cv2.connectedComponentsWithStats(core, connectivity=8)
    if n <= 1:
        return None
    core_b = core > 0
    if sky_mask is not None and sky_mask.shape != (h, w):
        sky_mask = cv2.resize(sky_mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0
    order = 1 + np.argsort(-stats[1:, cv2.CC_STAT_AREA])[:max_candidates]
    best = None
    for k in order:
        A = float(stats[k, cv2.CC_STAT_AREA])
        if A < 2:
            continue
        cx, cy = cents[k]
        r_eq = math.sqrt(A / math.pi)
        bx, by, bw, bh = stats[k, :4]
        comp = (lab[by:by + bh, bx:bx + bw] == k).astype(np.uint8)
        circ = _circularity(np.pad(comp, 1), A)
        prof, sectors, (x0, y0, x1, y1), rr = _radial_profile(Y, core_b, cx, cy, r_eq)
        pv = prof[np.isfinite(prof)]
        if len(pv) < 3:
            continue
        dec = float(np.mean(np.diff(pv) < 0))
        drop = float(pv[0] - pv[-1])
        f_score = dec * float(np.clip(drop / 40.0, 0, 1))
        sec = sectors[np.isfinite(sectors)]
        iso = float(np.clip(1 - (sec.std() / max(sec.mean(), 1.0)) / 0.35, 0.2, 1.0)) if sec.size >= 4 else 0.5
        r_full = r_eq / s
        size_w = 1.0 if 1.5 <= r_full <= 90 else 0.3
        if sky_mask is not None:
            ring = (rr >= r_eq + 2) & (rr < 2.5 * r_eq + 6)
            sm = sky_mask[y0:y1, x0:x1][ring]
            ctx_w = 0.5 + 0.5 * float(sm.mean()) if sm.size else 0.5
        else:
            ctx_w = 1.0 if cy / h < 0.6 else 0.5
        score = math.sqrt(circ) * f_score * math.sqrt(iso) * size_w * ctx_w
        if best is None or score > best["score"]:
            best = {"score": score, "cx": cx, "cy": cy, "r_eq": r_eq, "circ": circ, "falloff": f_score,
                    "iso": iso, "ctx": ctx_w, "profile": prof.tolist()}
    if best is None or best["score"] < min_score:
        return None
    # ---- full-resolution refinement
    X0, Y0 = best["cx"] / s, best["cy"] / s
    r_full = best["r_eq"] / s
    R = int(max(3 * r_full, 24))
    x0, x1 = max(0, int(X0 - R)), min(W, int(X0 + R + 1))
    y0, y1 = max(0, int(Y0 - R)), min(H, int(Y0 + R + 1))
    crop = rgb[y0:y1, x0:x1]
    Yc = luma(crop)
    cc = (crop.min(axis=2) >= sat_level) if saturated else (Yc >= max(200.0, float(Yc.max()) - 6.0))
    n2, lab2, st2, ce2 = cv2.connectedComponentsWithStats(cc.astype(np.uint8), connectivity=8)
    method, x, y, radius, circ2 = "glare", None, None, r_full, 0.0
    if n2 > 1:
        lx, ly = X0 - x0, Y0 - y0
        d2 = [(math.hypot(ce2[j][0] - lx, ce2[j][1] - ly) - math.sqrt(st2[j, cv2.CC_STAT_AREA] / math.pi), j)
              for j in range(1, n2)]
        j = min(d2)[1]
        comp = (lab2 == j).astype(np.uint8)
        A2 = float(st2[j, cv2.CC_STAT_AREA])
        circ2 = _circularity(np.pad(comp, 1), A2)
        radius = math.sqrt(A2 / math.pi)
        if circ2 >= 0.6:
            M = cv2.moments(comp, binaryImage=True)
            x, y, method = x0 + M["m10"] / M["m00"], y0 + M["m01"] / M["m00"], "core"
    if x is None:
        sig = max(2.0, r_full)
        B = cv2.GaussianBlur(Yc, (0, 0), sig)
        iy, ix = np.unravel_index(int(np.argmax(B)), B.shape)
        dx = dy = 0.0
        if 0 < ix < B.shape[1] - 1:
            den = B[iy, ix - 1] - 2 * B[iy, ix] + B[iy, ix + 1]
            dx = 0.5 * (B[iy, ix - 1] - B[iy, ix + 1]) / den if den < 0 else 0.0
        if 0 < iy < B.shape[0] - 1:
            den = B[iy - 1, ix] - 2 * B[iy, ix] + B[iy + 1, ix]
            dy = 0.5 * (B[iy - 1, ix] - B[iy + 1, ix]) / den if den < 0 else 0.0
        x, y = x0 + ix + float(np.clip(dx, -1, 1)), y0 + iy + float(np.clip(dy, -1, 1))
    ghosts = find_ghosts(Y, (x * s, y * s), best["r_eq"])
    ghosts_full = [[g[0] / s, g[1] / s, g[2]] for g in ghosts]
    cxw, cyw = 0.5 * W, 0.5 * H
    line_angle = math.degrees(math.atan2(cyw - y, cxw - x)) % 360.0
    return {"x": float(x), "y": float(y), "xn": float(x / W), "yn": float(y / H), "radius": float(radius),
            "saturated": bool(saturated), "w": W, "h": H, "method": method, "score": float(best["score"]),
            "circularity": float(max(best["circ"], circ2)), "falloff": best["falloff"], "isotropy": best["iso"],
            "ghosts": ghosts_full, "n_ghosts": len(ghosts_full), "line_angle_deg": line_angle}


def find_ghosts(Y: np.ndarray, sun_xy, r_core: float, max_n: int = 6) -> list:
    """Lens-flare ghost candidates on the line sun -> image centre: [(x, y, k), ...] in the given (working) scale."""
    h, w = Y.shape
    sx, sy = sun_xy
    vx, vy = 0.5 * w - sx, 0.5 * h - sy
    L = math.hypot(vx, vy)
    if L < 0.08 * w:
        return []
    y8 = np.clip(Y, 0, 255).astype(np.uint8)
    res = Y - cv2.medianBlur(y8, 31).astype(np.float32)
    sm = cv2.GaussianBlur(res, (0, 0), 2.0)
    yy, xx = np.mgrid[0:h, 0:w]
    far = (xx - sx) ** 2 + (yy - sy) ** 2 > (3 * r_core + 0.05 * w) ** 2
    vals = sm[far]
    sigma = 1.4826 * float(np.median(np.abs(vals - np.median(vals)))) + 1e-3
    thr = max(6.0, 5.0 * sigma)
    peaks = (sm >= cv2.dilate(sm, np.ones((9, 9), np.uint8))) & (sm > thr) & far
    py, px = np.nonzero(peaks)
    out = []
    tol = max(4.0, 0.012 * w)
    for x, y in zip(px, py):
        dist = abs(vx * (y - sy) - vy * (x - sx)) / L
        k = ((x - sx) * vx + (y - sy) * vy) / (L * L)
        if dist < tol and k > 0.25:
            out.append((float(x), float(y), float(k), float(sm[y, x])))
    out.sort(key=lambda g: -g[3])
    return [g[:3] for g in out[:max_n]]


# ============================================================================ shadow orientation
def shadow_orientation(rgb: np.ndarray, work_width: int = 320, roi_norm=(0.0, 0.55, 1.0, 1.0),
                       sky_mask: Optional[np.ndarray] = None, ir: bool = False, exclude=(),
                       min_grad: float = 0.06) -> Optional[dict]:
    """Dominant cast-shadow edge orientation on the ground (see module docstring)."""
    H, W = rgb.shape[:2]
    small, s = downscale(rgb, work_width)
    h, w = small.shape[:2]
    f = small.astype(np.float32)
    L = cv2.GaussianBlur(np.log(luma(small) + 4.0), (0, 0), 1.0)
    gx = cv2.Sobel(L, cv2.CV_32F, 1, 0, ksize=3) / 8.0
    gy = cv2.Sobel(L, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    mag2 = gx * gx + gy * gy
    roi = rect_mask(h, w, [roi_norm]) & ~rect_mask(h, w, exclude)
    if sky_mask is not None:
        sm = sky_mask if sky_mask.shape == (h, w) else cv2.resize(sky_mask.astype(np.uint8), (w, h),
                                                                   interpolation=cv2.INTER_NEAREST) > 0
        roi &= ~sm
    roi[:2], roi[-2:], roi[:, :2], roi[:, -2:] = False, False, False, False
    if ir:
        wc = np.ones_like(L)
    else:
        C = cv2.GaussianBlur(np.log((f[..., 2] + 4.0) / (f[..., 0] + 4.0)), (0, 0), 1.0)
        cx = cv2.Sobel(C, cv2.CV_32F, 1, 0, ksize=3) / 8.0
        cy = cv2.Sobel(C, cv2.CV_32F, 0, 1, ksize=3) / 8.0
        k = -(gx * cx + gy * cy) / (mag2 + 1e-4)
        wc = np.clip(k / 0.15, 0, 1)
    wgt = mag2 * wc * roi * (mag2 > min_grad ** 2)
    tot = float(wgt.sum())
    if tot <= 1e-6 or int((wgt > 0).sum()) < 20:
        return None
    th = (np.degrees(np.arctan2(gy, gx)) + 90.0) % 180.0          # line direction, clockwise from +x
    hist, _ = np.histogram(th[wgt > 0], bins=36, range=(0, 180), weights=wgt[wgt > 0])
    hs = hist + 0.5 * (np.roll(hist, 1) + np.roll(hist, -1))
    pk = (int(np.argmax(hs)) + 0.5) * 5.0
    dth = (th - pk + 90.0) % 180.0 - 90.0
    sel = (np.abs(dth) <= 15.0) & (wgt > 0)
    ws = wgt * sel
    # structure tensor of the cluster: the gradient orientation is perpendicular to the shadow line
    Jxx, Jyy, Jxy = float((ws * gx * gx).sum()), float((ws * gy * gy).sum()), float((ws * gx * gy).sum())
    Jxx_a, Jyy_a, Jxy_a = float((wgt * gx * gx).sum()), float((wgt * gy * gy).sum()), float((wgt * gx * gy).sum())
    if Jxx + Jyy <= 0:
        return None
    theta_g = 0.5 * math.degrees(math.atan2(2 * Jxy, Jxx - Jyy))
    angle = (theta_g + 90.0) % 180.0
    coh = math.sqrt((Jxx_a - Jyy_a) ** 2 + 4 * Jxy_a ** 2) / max(Jxx_a + Jyy_a, 1e-12)
    share = float(ws.sum() / tot)
    yy, xx = np.mgrid[0:h, 0:w]
    xc, yc = float((ws * xx).sum() / ws.sum()), float((ws * yy).sum() / ws.sum())
    hs2 = hs.copy()
    bins = (np.arange(36) + 0.5) * 5.0
    hs2[np.abs((bins - pk + 90) % 180 - 90) <= 20] = 0
    second = float((int(np.argmax(hs2)) + 0.5) * 5.0) if hs2.max() > 0.3 * hs.max() else None
    return {"angle_deg_image": angle, "coherence": coh, "peak_share": share, "strength": coh * share,
            "x": (xc + 0.5) / s - 0.5, "y": (yc + 0.5) / s - 0.5, "w": W, "h": H, "n_px": int(sel.sum()),
            "second_peak_deg": second, "colour_cue": not ir}


# ============================================================================ analyzer
DEFAULTS = {
    "work_width": 640,
    "interval_s": 10.0,
    "shadow_interval_s": 60.0,
    "sat_level": 235,
    "min_score": 0.3,
    "min_sun_alt": -3.0,
    "az_margin_deg": 25.0,
    "static_px": 4.0,
    "static_after_s": 900.0,
    "shadow_roi_norm": [0.0, 0.55, 1.0, 1.0],
    "shadow_work_width": 320,
    "shadow_min_coherence": 0.25,
    "shadow_min_sun_alt": 5.0,
    "exclude_norm": [],
    "approx_site": None,
}


class SunAnalyzer(Analyzer):
    name = "sun"
    wants_frames = True
    min_interval_s = 0.0

    def __init__(self, config=None):
        super().__init__(config)
        cfg = config or {}
        self.p = {**DEFAULTS, **{k: v for k, v in cfg.items() if k != "_global"}}
        self.site = site_from_config(cfg)
        cam = (cfg.get("_global") or {}).get("camera") or {}
        self.heading = float(cam.get("heading_deg", 220.0))
        self.hfov = float(cam.get("hfov_deg", 70.0))
        self.history = deque()           # (t, x, y, w)
        self._last = None
        self._last_shadow = None
        self.n_static = 0

    def _obs(self, kind, frame, value, conf):
        return Observation(kind=kind, ts=frame.real_ts, value=clean(value), analyzer=self.name, confidence=float(conf),
                           frame_id=frame.id, ts_capture=frame.capture_ts)

    @staticmethod
    def _due(last, t, interval):
        return last is None or t - last >= interval - 1e-6 or t < last

    def on_frame(self, frame, ctx: Context):
        t = frame.real_ts.timestamp()
        st = ctx.state.setdefault("sun", {})
        alt, az = solar_altaz(t, *self.site)
        if alt < self.p["min_sun_alt"] or frame_ir_mode(frame, ctx):
            st["last"] = None
            return []
        out = []
        H, W = frame.image.shape[:2]
        if self._due(self._last, t, self.p["interval_s"]):
            self._last = t
            wk = int(self.p["work_width"])
            hk = int(round(H * min(1.0, wk / W)))
            det = find_sun(frame.image, wk, int(self.p["sat_level"]), sky_mask_for(ctx, hk, min(wk, W)),
                           float(self.p["min_score"]))
            st["last"] = None
            if det is not None:
                o = self._accept(det, t, alt, az, W, frame)
                if o is not None:
                    out.append(o)
                    st["last"] = {**det, "t": t}
        sky = ctx.state.get("sky") or {}
        if (self._due(self._last_shadow, t, self.p["shadow_interval_s"]) and alt >= self.p["shadow_min_sun_alt"]
                and sky.get("direct_sun") is not False):
            self._last_shadow = t
            wk = int(self.p["shadow_work_width"])
            sh = shadow_orientation(frame.image, wk, self.p["shadow_roi_norm"],
                                    sky_mask_for(ctx, int(round(H * min(1.0, wk / W))), min(wk, W)),
                                    False, self.p["exclude_norm"])
            if sh is not None and sh["coherence"] >= self.p["shadow_min_coherence"]:
                conf = min(0.5, 0.15 + 0.4 * sh["strength"]) * (1.0 if sky.get("direct_sun") else 0.7)
                out.append(self._obs("shadow_direction", frame, {**sh, "sun_alt_approx_deg": alt,
                                                                 "sun_az_approx_deg": az,
                                                                 "direct_sun": sky.get("direct_sun")}, conf))
        return out

    def _accept(self, det, t, alt, az, W, frame):
        while self.history and self.history[0][0] < t - 3 * 3600:
            self.history.popleft()
        x, y = det["x"], det["y"]
        static = any(t - th >= self.p["static_after_s"] and math.hypot(x - xh * W / wh, y - yh * W / wh) < self.p["static_px"]
                     for th, xh, yh, wh in self.history)
        self.history.append((t, x, y, W))
        if static:
            self.n_static += 1
            log.debug("sun: static glare at (%.0f, %.0f) ignored", x, y)
            return None
        f = focal_px(self.config, W)
        px_per_deg = f * math.pi / 180.0
        consistent = False
        for th, xh, yh, wh in reversed(self.history):
            dt = t - th
            if 0 < dt <= 900:
                d = math.hypot(x - xh * W / wh, y - yh * W / wh)
                consistent = d <= 6.0 + 0.3 * px_per_deg * dt / 60.0
                break
        daz = (az - self.heading + 180.0) % 360.0 - 180.0
        az_ok = abs(daz) <= self.hfov / 2.0 + self.p["az_margin_deg"]
        conf = 0.25 + 0.45 * min(det["score"], 1.0) + 0.05 * min(det["n_ghosts"], 2) + (0.1 if consistent else 0.0)
        if not az_ok:
            conf *= 0.4
        if alt < 0:
            conf *= 0.6
        det = {**det, "sun_alt_approx_deg": alt, "sun_az_approx_deg": az, "az_prior_ok": az_ok,
               "track_consistent": consistent}
        return self._obs("sun_pixel", frame, det, min(conf, 0.85))
