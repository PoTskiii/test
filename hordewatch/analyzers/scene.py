"""Persistent scene-change / new-object detector (analyzer name: ``scene``).

Goal: notice when something *new* appears (or disappears) in the static forest
scene around the box - the wooden HORDE arrow sign, a hand in the heather, a
balloon, a crew bag, a person - and timestamp it, while ignoring what
constantly changes: sun/cloud illumination, auto-exposure, Anja moving inside
the box, branches in the wind, compression noise.

Background model (per illumination regime)
  Work at ~320 px width. Per pixel, four *illumination-normalised* features:
    * E   - gradient magnitude of the log-luminance (Sobel on blurred log1p(Y)).
            A global gain change (cloud, exposure) is an additive constant in
            log space and disappears in the gradient.
    * LCN - local-contrast-normalised log-luminance ((L - mu9x9) / sd9x9):
            invariant to local gain and offset.
    * r, g - normalised chromaticity R/(R+G+B), G/(R+G+B) (x10), invariant to
            intensity; disabled in IR/night mode (monochrome).
  The background is an exponential running mean and variance of these
  features (``alpha`` ~0.03 per sampled frame = a few minutes). Pixels that
  currently differ are updated 10x slower (selective update) so a new object
  is not absorbed before it has been confirmed. Deviations are z-scores with
  per-feature noise floors; the structure score (E, LCN) and the colour score
  (r, g) are combined by max so a brown sign on green heather and a grey
  object on grey rock are both caught.

Persistence and gating
  * A pixel must deviate in >= ``persist_frames`` (3) consecutive frames;
    components of such pixels (area >= ``min_area_frac``) become candidates.
  * If more than ``global_frac`` of the valid image changes at once it is a
    global event (sun burst, rain on the lens, exposure/IR switch): no object
    events, fast re-adaptation, one rate-limited ``scene_change`` {global}.
  * Camera wobble is removed by phase-correlation registration of the current
    edge map to the background (sub-pixel translation); a large shift re-seeds
    the model and emits ``scene_change`` {camera_shift} - someone touched the
    camera, which itself is news.
  * Areas excluded: configured rectangles (``exclude_norm``), the whiteboard
    bbox, the person bbox published by the gesture analyzer (sticky for
    ``person_hold_s``: a person who sits still is absorbed into the gesture
    analyzer's background and stops being published; person areas are learnt
    at the normal rate meanwhile), pixels with a
    high long-term *activity* rate (the box interior where Anja moves, trees
    swaying) and learnt "hot zones" (the same place reported repeatedly).
  * Day and IR-night have separate reference models (the IR illuminator gives a
    completely different image); the regime is detected from saturation and
    channel equality with hysteresis, and each switch is reported as
    ``ir_mode_switch`` (a dusk/dawn light-level timing that the astro side
    can use).

Classification of a confirmed component (on the full-resolution crop)
  * ``horde_sign``: mostly wood-brown (HSV hue 5-28, saturation >= 70) and
    elongated (minAreaRect aspect >= 2.2); an *arrow score* from the width
    profile along the principal axis (a head wider than the shaft that tapers
    to a tip, or a board that tapers to a point) raises confidence and gives
    ``points_to_deg_image`` (0 = image right, 90 = image up).
  * ``hand`` / ``hand_in_heather``: mostly skin-coloured (YCrCb), small, lower
    half of the image = in the heather/foreground.
  * otherwise ``<colour>_object`` (white, dark, red, blue, ...), and in IR
    ``bright_object`` / ``dark_object``.
  * ``appeared`` vs removed: if the region returns to what it looked like before
    a previously reported object appeared, it is reported as that object
    *removed* (``appeared: False``, ``ref_label``). Without history, an
    increase in structure/colour contrast means appeared.
  After reporting, the region is absorbed into the background so it is not
  reported again, and the frame is archived (``ctx.state['archive_next']``).

Timestamps: ``Observation.ts`` is the real time of the first frame in which the
change was seen (onset), ``value.onset_window`` brackets it with the previous
frame, ``value.detected_ts`` is when persistence confirmed it. ``ts_capture``
always belongs to the same (onset) frame as ``ts`` so bridges that undo the
latency from ``ts_capture`` get the onset, not the confirmation frame.

Resolution changes: every frame is resized to a fixed working width (up or
down), so a stream that drops to 144p and back keeps its model; a change of the
source size only triggers a few frames of fast re-adaptation (no event).
Grey (2-D), RGBA and float frames are coerced to RGB uint8.

Failure modes: moving sun flecks under the canopy (slow; mostly absorbed),
snow/frost changing the ground (global), heavy rain on the lens, objects that
appear during an IR/day switch, objects placed inside an excluded/active zone,
and camouflaged (green/grey) objects with little texture.
"""
from __future__ import annotations

import logging
from collections import deque
from datetime import timedelta
from typing import Optional

import cv2
import numpy as np

from ..types import Observation, iso
from .base import Analyzer, Context
from .whiteboard import as_rgb_u8

log = logging.getLogger("hordewatch.scene")

_NOISE_FLOOR = np.array([0.06, 0.45, 0.10, 0.10], np.float32)   # E, LCN, r*10, g*10


def is_ir_frame(rgb_small: np.ndarray, sat_thr: float = 14.0, chan_thr: float = 4.0) -> bool:
    """Night/IR mode: the IR-cut filter is out and the camera outputs a grey image."""
    x = rgb_small.astype(np.int16)
    chan = (np.abs(x[..., 0] - x[..., 1]).mean() + np.abs(x[..., 1] - x[..., 2]).mean()) / 2.0
    hsv = cv2.cvtColor(rgb_small, cv2.COLOR_RGB2HSV)
    return bool(np.median(hsv[..., 1]) < sat_thr and chan < chan_thr)


def compute_features(small_rgb: np.ndarray, ir: bool) -> np.ndarray:
    """H x W x 4 float32 feature stack (E, LCN, r, g); chroma channels are constant in IR."""
    f = small_rgb.astype(np.float32)
    y = f[..., 0] * 0.299 + f[..., 1] * 0.587 + f[..., 2] * 0.114
    L = cv2.GaussianBlur(np.log1p(y), (0, 0), 1.0)
    gx = cv2.Sobel(L, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(L, cv2.CV_32F, 0, 1, ksize=3)
    E = np.sqrt(gx * gx + gy * gy) * 0.25
    mu = cv2.boxFilter(L, -1, (9, 9))
    mu2 = cv2.boxFilter(L * L, -1, (9, 9))
    sd = np.sqrt(np.maximum(mu2 - mu * mu, 0))
    lcn = np.clip((L - mu) / (sd + 0.03), -3, 3)
    if ir:
        r = np.full_like(E, 10 / 3.0)
        g = r
    else:
        s = f.sum(axis=2) + 3.0
        r = f[..., 0] / s * 10.0
        g = f[..., 1] / s * 10.0
        dark = y < 20                       # chroma is meaningless in the noise floor
        r = np.where(dark, 10 / 3.0, r)
        g = np.where(dark, 10 / 3.0, g)
        r = cv2.GaussianBlur(r, (0, 0), 1.0)
        g = cv2.GaussianBlur(g, (0, 0), 1.0)
    return np.dstack([E, lcn, r, g]).astype(np.float32)


def colour_name(hsv_mean) -> str:
    h, s, v = [float(x) for x in hsv_mean]
    if s < 40:
        return "white" if v > 170 else ("dark" if v < 60 else "grey")
    if v < 45:
        return "dark"
    if h < 5 or h >= 170:
        return "red"
    if h < 25:
        return "brown" if v < 170 else "orange"
    if h < 35:
        return "yellow"
    if h < 85:
        return "green"
    if h < 130:
        return "blue"
    return "purple"


def arrow_shape(mask: np.ndarray) -> dict:
    """Elongation, arrow score and pointing direction of a binary blob.

    The blob is projected on its principal axis; the width profile along the axis is
    examined for an arrow head (an end region clearly wider than the shaft that narrows
    to a tip) or a pointed board (one end tapering to a point, the other blunt).
    """
    ys, xs = np.nonzero(mask)
    if len(xs) < 20:
        return {"elongation": 1.0, "arrow_score": 0.0, "points_to_deg_image": None}
    pts = np.stack([xs, ys], 1).astype(np.float32)
    mean = pts.mean(0)
    cov = np.cov((pts - mean).T)
    evals, evecs = np.linalg.eigh(cov)
    e1 = evecs[:, 1]
    e2 = evecs[:, 0]
    u = (pts - mean) @ e1
    v = (pts - mean) @ e2
    length = u.max() - u.min()
    width_all = v.max() - v.min()
    elong = float(length / max(width_all, 1.0))
    nb = 20
    bins = np.clip(((u - u.min()) / max(length, 1e-6) * nb).astype(int), 0, nb - 1)
    prof = np.zeros(nb)
    for b in range(nb):
        vb = v[bins == b]
        prof[b] = (vb.max() - vb.min() + 1) if len(vb) else 0
    shaft = float(np.median(prof[5:15])) if prof[5:15].any() else float(np.median(prof))
    best, end_sign = 0.0, 0
    for sign, region in ((-1, prof[:7]), (1, prof[::-1][:7])):
        head = float(region.max())
        tip = float(region[0])
        # arrow head: wider than shaft, narrowing to a tip
        s_head = np.clip((head / max(shaft, 1) - 1.2) / 0.6, 0, 1) * np.clip((head - tip) / max(head, 1) / 0.5, 0, 1)
        # pointed board: this end tapers to a point, the other end is blunt
        other = prof[::-1][:7] if sign == -1 else prof[:7]
        s_taper = 0.8 * np.clip((1 - tip / max(shaft, 1) - 0.3) / 0.4, 0, 1) * \
            np.clip((float(other[0]) / max(shaft, 1) - 0.5) / 0.3, 0, 1)
        sc = float(max(s_head, s_taper))
        if sc > best:
            best, end_sign = sc, sign
    direction = None
    if best > 0.2:
        vec = e1 * end_sign                  # towards the head end (image coords, y down)
        direction = float(np.degrees(np.arctan2(-vec[1], vec[0])) % 360)
    return {"elongation": round(elong, 2), "arrow_score": round(best, 3), "points_to_deg_image": direction}


def _bbox_iou(a, b):
    ix0, iy0, ix1, iy1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix1 - ix0) * max(0, iy1 - iy0)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


class _Model:
    def __init__(self):
        self.mean: Optional[np.ndarray] = None
        self.var: Optional[np.ndarray] = None
        self.n = 0
        self.persist = None
        self.activity = None
        self.fast = 0              # frames of fast re-adaptation left (no detection)
        self.objects = []          # reported objects (dicts)
        self.reports = []          # (bbox_w, ts) for hot-zone learning
        self.hot = []              # (bbox_w, until_ts)

    def seed(self, F):
        self.mean = F.copy()
        self.var = np.zeros_like(F)
        self.n = 1
        self.persist = np.zeros(F.shape[:2], np.int16)
        self.activity = np.zeros(F.shape[:2], np.float32) if self.activity is None or \
            self.activity.shape != F.shape[:2] else self.activity


class SceneChangeAnalyzer(Analyzer):
    name = "scene"
    wants_frames = True
    min_interval_s = 0.0

    DEFAULTS = {"work_w": 320, "alpha": 0.03, "fg_alpha_factor": 0.1, "z_thr": 4.0, "persist_frames": 3,
                "min_area_frac": 0.0012, "max_area_frac": 0.25, "global_frac": 0.3, "warmup_frames": 3,
                "exclude_norm": [], "activity_alpha": 0.03, "activity_thr": 0.3, "activity_min_frames": 30,
                "global_event_min_interval_s": 300.0, "max_shift_px": 6.0, "hot_window_s": 3600.0,
                "hot_count": 3, "hot_suppress_s": 3600.0, "mode_hysteresis": 2, "person_margin": 0.15,
                "person_hold_s": 600.0}

    def __init__(self, config=None):
        super().__init__(config)
        self.p = {**self.DEFAULTS, **{k: v for k, v in (config or {}).items() if k != "_global"}}
        self.models = {"day": _Model(), "ir": _Model()}
        self.mode: Optional[str] = None
        self._mode_votes = 0
        self._last_mode_ts = None
        self._history = deque(maxlen=64)       # (real_ts, capture_ts, frame_id) per frame
        self._last_global = None
        self._person_mem = []                  # [[bbox full-res, last_seen_real_ts], ...] sticky person areas
        self._shape = None

    # ------------------------------------------------------------------ helpers
    def _person_boxes(self, ctx, frame):
        """Person areas to exclude. Sticky: the gesture analyzer's median background absorbs a person
        who sits still for a few minutes, after which it publishes no person_bbox although she is still
        there - and this analyzer (which never learnt her, she was excluded) would then report her as a
        new object. So every area where a person was seen stays excluded for person_hold_s."""
        now = frame.real_ts
        hold = float(self.p["person_hold_s"])
        pb = ctx.state.get("person_bbox")
        if isinstance(pb, dict) and pb.get("bbox") is not None:
            idx = pb.get("frame_index")
            # fresh = published for this or one of the last 2 frames (an index that went backwards, e.g.
            # after an ingest restart, means stale)
            if idx is None or 0 <= frame.index - idx <= 2:
                try:
                    bb = [float(v) for v in pb["bbox"]]
                except (TypeError, ValueError):
                    bb = None
                if bb is not None:
                    for m in self._person_mem:
                        if _bbox_iou(m[0], bb) > 0.3:
                            m[0], m[1] = bb, now
                            break
                    else:
                        self._person_mem.append([bb, now])
        self._person_mem = [m for m in self._person_mem if 0 <= (now - m[1]).total_seconds() <= hold][-16:]
        return [m[0] for m in self._person_mem]

    def _exclusion(self, ctx, frame, h, w, sx, sy, model: _Model):
        """Returns (all excluded pixels, person pixels). Person pixels are learnt at the normal rate."""
        ex = np.zeros((h, w), bool)
        ex_person = np.zeros((h, w), bool)
        for r in self.p.get("exclude_norm") or []:
            try:
                x0, y0, x1, y1 = [min(1.0, max(0.0, float(v))) for v in r]
            except (TypeError, ValueError):
                log.warning("scene: ignoring malformed exclude_norm entry %r (want [x0, y0, x1, y1] in 0..1)", r)
                continue
            ex[int(y0 * h):int(np.ceil(y1 * h)), int(x0 * w):int(np.ceil(x1 * w))] = True
        boxes = []
        wbs = ctx.state.get("whiteboard")
        if isinstance(wbs, dict) and wbs.get("bbox") is not None:
            boxes.append((wbs["bbox"], 0.1, False))
        for bb in self._person_boxes(ctx, frame):
            boxes.append((bb, self.p["person_margin"], True))
        for bb, m, is_person in boxes:
            try:
                x0, y0, x1, y1 = [float(v) for v in bb]
            except (TypeError, ValueError):
                continue
            bw, bh = (x1 - x0) * m, (y1 - y0) * m
            sl = (slice(max(0, int((y0 - bh) * sy)), max(0, int(np.ceil((y1 + bh) * sy)))),
                  slice(max(0, int((x0 - bw) * sx)), max(0, int(np.ceil((x1 + bw) * sx)))))
            ex[sl] = True
            if is_person:
                ex_person[sl] = True
        if model.n >= self.p["activity_min_frames"]:
            ex |= model.activity > self.p["activity_thr"]
        now = frame.real_ts
        model.hot = [(b, until) for b, until in model.hot if until > now]
        for (x0, y0, x1, y1), _ in model.hot:
            ex[y0:y1, x0:x1] = True
        return ex, ex_person

    def _register(self, model: _Model, F):
        """Translation of the current edge map relative to the background (camera wobble)."""
        a = model.mean[..., 0]
        b = F[..., 0]
        if a.shape[0] < 16 or a.shape[1] < 16:
            return (0.0, 0.0), 0.0
        win = cv2.createHanningWindow((a.shape[1], a.shape[0]), cv2.CV_32F)
        (dx, dy), resp = cv2.phaseCorrelate(a.astype(np.float32), b.astype(np.float32), win)
        return (float(dx), float(dy)), float(resp)

    # ------------------------------------------------------------------ main
    def on_frame(self, frame, ctx: Context):
        # rate-limited global events come back as None; never hand those to the runner
        return [o for o in self._process(frame, ctx) if o is not None]

    def _process(self, frame, ctx: Context):
        out = []
        img = as_rgb_u8(frame.image)
        H, W = img.shape[:2]
        if H < 8 or W < 8:
            return out
        # fixed working width (also upscales 144p/240p) so adaptive-bitrate switches keep the model
        s = self.p["work_w"] / float(W)
        wsz = (int(self.p["work_w"]), max(8, int(round(H * s))))
        small = cv2.resize(img, wsz, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
        h, w = small.shape[:2]
        sx, sy = w / float(W), h / float(H)
        if self._shape is not None and self._shape != (H, W):
            log.info("scene: source size %s -> %s; fast re-adaptation", self._shape, (H, W))
            for m in self.models.values():
                m.fast = max(m.fast, int(self.p["warmup_frames"]))
        self._shape = (H, W)
        self._history.append((frame.real_ts, frame.capture_ts, frame.id))

        # ---- regime (day / IR) with hysteresis
        ir = is_ir_frame(small)
        want = "ir" if ir else "day"
        if self.mode is None:
            self.mode = want
        elif want != self.mode:
            self._mode_votes += 1
            if self._mode_votes >= self.p["mode_hysteresis"]:
                prev = self.mode
                self.mode = want
                self._mode_votes = 0
                m = self.models[want]
                m.fast = self.p["warmup_frames"]
                k = min(int(self.p["mode_hysteresis"]), len(self._history))
                prev_ts = self._history[-k - 1][0] if len(self._history) > k else None
                onset, onset_cap = self._history[-k][0], self._history[-k][1]
                out.append(Observation(kind="ir_mode_switch", ts=onset, analyzer=self.name, confidence=0.8,
                                       frame_id=frame.id, ts_capture=onset_cap,
                                       value={"to_ir": want == "ir", "from": prev, "to": want,
                                              "onset_window": [iso(prev_ts) if prev_ts else None, iso(onset)],
                                              "detected_ts": iso(frame.real_ts)}))
                log.info("scene: switched %s -> %s at %s", prev, want, onset)
        else:
            self._mode_votes = 0
        if want != self.mode:
            return out                      # frame in the minority regime during hysteresis: skip
        model = self.models[self.mode]
        F = compute_features(small, self.mode == "ir")
        if model.mean is None or model.mean.shape != F.shape:
            model.seed(F)
            return out

        # ---- camera wobble / shift
        (dx, dy), resp = self._register(model, F)
        shift = float(np.hypot(dx, dy))
        if resp > 0.1 and shift > self.p["max_shift_px"]:
            model.seed(F)
            model.objects.clear()
            out.append(self._global_obs(frame, {"global": True, "cause": "camera_shift",
                                                "camera_shift_px": [round(dx / sx, 1), round(dy / sy, 1)],
                                                "score": 1.0, "bbox_list": [], "ir_mode": self.mode == "ir"},
                                        force=True))
            return out
        if resp > 0.1 and shift > 0.4:
            M = np.float32([[1, 0, -dx], [0, 1, -dy]])
            F = cv2.warpAffine(F, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

        # ---- deviation
        std = np.sqrt(model.var + _NOISE_FLOOR ** 2)
        z = np.abs(F - model.mean) / std
        z = np.minimum(z, 20.0)
        z_struct = np.sqrt((z[..., 0] ** 2 + z[..., 1] ** 2) / 2)
        z_col = np.sqrt((z[..., 2] ** 2 + z[..., 3] ** 2) / 2) if self.mode == "day" else np.zeros_like(z_struct)
        D = np.maximum(z_struct, z_col)
        changed = (D > self.p["z_thr"]).astype(np.uint8)
        changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        changed = cv2.morphologyEx(changed, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        chg = changed.astype(bool)
        excl, excl_person = self._exclusion(ctx, frame, h, w, sx, sy, model)
        valid = ~excl
        frac = float(chg[valid].mean()) if valid.any() else 0.0

        # ---- update statistics
        warm = model.n < self.p["warmup_frames"] or model.fast > 0
        is_global = (not warm) and frac > self.p["global_frac"]
        if warm or is_global:
            a = max(0.5, 1.0 / (model.n + 1)) if warm else 0.5
            amap = np.full(chg.shape, a, np.float32)
        else:
            # selective update, except where a person is (sticky-excluded): learn her at the normal rate
            amap = np.where(chg & ~excl_person, self.p["alpha"] * self.p["fg_alpha_factor"],
                            self.p["alpha"]).astype(np.float32)
        a3 = amap[..., None]
        d = F - model.mean
        model.mean += a3 * d
        model.var = (1 - a3) * (model.var + a3 * d * d)
        model.n += 1
        model.activity += self.p["activity_alpha"] * (chg.astype(np.float32) - model.activity)
        if model.fast > 0:
            model.fast -= 1
        if warm:
            model.persist[:] = 0
            return out
        if is_global:
            model.persist[:] = 0
            out.append(self._global_obs(frame, {"global": True, "cause": "illumination_or_weather",
                                                "score": round(frac, 3), "bbox_list": [],
                                                "ir_mode": self.mode == "ir"}))
            return out

        model.persist = np.where(chg & valid, np.minimum(model.persist + 1, 1000), 0).astype(np.int16)
        pers = (model.persist >= self.p["persist_frames"]).astype(np.uint8)
        if not pers.any():
            return out
        n, lab, stats, _ = cv2.connectedComponentsWithStats(pers, connectivity=8)
        min_area = self.p["min_area_frac"] * h * w
        max_area = self.p["max_area_frac"] * h * w
        new_objs = []
        for i in range(1, n):
            x, y, bw, bh, area = stats[i]
            if area < min_area or area > max_area:
                continue
            comp = lab == i
            bbox_w = (int(x), int(y), int(x + bw), int(y + bh))
            obs = self._report(frame, img, model, F, comp, bbox_w, sx, sy)
            # absorb into the background so it is reported once
            model.mean[comp] = F[comp]
            model.var[comp] = 0
            model.persist[comp] = 0
            if obs is not None:
                new_objs.append(obs)
        if new_objs:
            out += new_objs
            first = min(new_objs, key=lambda o: o.ts)
            out.append(Observation(kind="scene_change", ts=first.ts, analyzer=self.name,
                                   confidence=float(max(o.confidence for o in new_objs)), frame_id=frame.id,
                                   ts_capture=first.ts_capture,
                                   value={"score": round(frac, 4), "bbox_list": [o.value["bbox"] for o in new_objs],
                                          "labels": [o.value["label"] for o in new_objs], "global": False,
                                          "ir_mode": self.mode == "ir", "detected_ts": iso(frame.real_ts)}))
            ctx.state["archive_next"] = True
        return out

    def _global_obs(self, frame, value, force=False):
        now = frame.real_ts
        if not force and self._last_global is not None and \
                (now - self._last_global).total_seconds() < self.p["global_event_min_interval_s"]:
            return None
        self._last_global = now
        return Observation(kind="scene_change", ts=now, analyzer=self.name, confidence=0.4, frame_id=frame.id,
                           ts_capture=frame.capture_ts, value=value)

    # ------------------------------------------------------------------ classification / report
    def _report(self, frame, img, model: _Model, F, comp, bbox_w, sx, sy):
        H, W = img.shape[:2]
        x0, y0, x1, y1 = bbox_w
        fb = [int(x0 / sx), int(y0 / sy), int(min(W, np.ceil(x1 / sx))), int(min(H, np.ceil(y1 / sy)))]
        now = frame.real_ts
        # hot zones: same place over and over -> learn to ignore
        recent = [b for b, t in model.reports if (now - t).total_seconds() < self.p["hot_window_s"] and
                  _bbox_iou(b, bbox_w) > 0.3]
        model.reports = [(b, t) for b, t in model.reports if (now - t).total_seconds() < self.p["hot_window_s"]]
        model.reports.append((bbox_w, now))
        if len(recent) + 1 >= self.p["hot_count"]:
            model.hot.append((bbox_w, now + timedelta(seconds=self.p["hot_suppress_s"])))
            log.info("scene: hot zone %s (reported %d times) suppressed", fb, len(recent) + 1)
            return None

        pers_frames = int(np.median(model.persist[comp])) if comp.any() else self.p["persist_frames"]
        k = min(len(self._history), max(1, pers_frames))
        onset = self._history[-k]
        prev = self._history[-k - 1] if len(self._history) > k else None

        # removed? compare with the look before a previously reported object appeared
        appeared, ref = True, None
        for o in model.objects:
            if o["appeared"] and _bbox_iou(o["bbox_w"], bbox_w) > 0.3:
                ox0, oy0, ox1, oy1 = o["bbox_w"]
                cur = F[oy0:oy1, ox0:ox1]
                before = o["before"]
                if cur.shape == before.shape:
                    dz = np.abs(cur - before) / _NOISE_FLOOR
                    score_before = float(np.median(np.maximum(np.sqrt((dz[..., 0] ** 2 + dz[..., 1] ** 2) / 2),
                                                              np.sqrt((dz[..., 2] ** 2 + dz[..., 3] ** 2) / 2))))
                    da = np.abs(cur - o["after"]) / _NOISE_FLOOR
                    score_after = float(np.median(np.maximum(np.sqrt((da[..., 0] ** 2 + da[..., 1] ** 2) / 2),
                                                             np.sqrt((da[..., 2] ** 2 + da[..., 3] ** 2) / 2))))
                    if score_before < score_after:
                        appeared, ref = False, o
                        break
        if appeared and ref is None:
            e_now = float(F[..., 0][comp].mean())
            e_bg = float(model.mean[..., 0][comp].mean())
            c_now = float(np.abs(F[..., 2:][comp] - 10 / 3.0).mean())
            c_bg = float(np.abs(model.mean[..., 2:][comp] - 10 / 3.0).mean())
            if e_now < 0.6 * e_bg and c_now <= c_bg:
                appeared = False            # smoother + less colourful than before: something went away

        crop = img[fb[1]:fb[3], fb[0]:fb[2]]
        cmask = cv2.resize(comp[y0:y1, x0:x1].astype(np.uint8), (crop.shape[1], crop.shape[0]),
                           interpolation=cv2.INTER_NEAREST).astype(bool) if crop.size else np.zeros(0, bool)
        label, conf, extra = self._classify(crop, cmask, fb, H, W)
        if not appeared and ref is not None:
            label, conf = ref["label"], max(0.3, ref["conf"] - 0.1)
            extra["ref_ts"] = iso(ref["ts"])
        conf = float(conf)
        value = {"label": label, "bbox": fb, "bbox_norm": [round(fb[0] / W, 4), round(fb[1] / H, 4),
                                                           round(fb[2] / W, 4), round(fb[3] / H, 4)],
                 "appeared": bool(appeared), "area_frac": round(float(comp.sum()) / comp.size, 5),
                 "ir_mode": self.mode == "ir", "persist_frames": pers_frames,
                 "onset_window": [iso(prev[0]) if prev else None, iso(onset[0])], "onset_frame_id": onset[2],
                 "detected_ts": iso(now), **extra}
        obs = Observation(kind="object_appeared", ts=onset[0], analyzer=self.name, confidence=conf, frame_id=frame.id,
                          ts_capture=onset[1], value=value)
        if appeared:
            model.objects.append({"bbox_w": bbox_w, "label": label, "conf": conf, "ts": onset[0], "appeared": True,
                                  "before": model.mean[y0:y1, x0:x1].copy(), "after": F[y0:y1, x0:x1].copy()})
            model.objects = model.objects[-50:]
        elif ref is not None:
            ref["appeared"] = False
        log.info("scene: %s %s at %s (conf %.2f)", label, "appeared" if appeared else "removed", fb, conf)
        return obs

    def _classify(self, crop, cmask, fb, H, W):
        extra = {}
        if crop.size == 0 or not cmask.any():
            return "unknown_object", 0.25, extra
        hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
        px = hsv[cmask]
        hsv_mean = [float(np.median(px[:, 0])), float(np.median(px[:, 1])), float(np.median(px[:, 2]))]
        extra["mean_hsv"] = [round(x, 1) for x in hsv_mean]
        cy_norm = (fb[1] + fb[3]) / 2.0 / H
        area_frac = (fb[2] - fb[0]) * (fb[3] - fb[1]) / float(H * W)
        if self.mode == "ir":
            gray = crop.mean(axis=2)
            inside = float(gray[cmask].mean())
            ring = float(gray[~cmask].mean()) if (~cmask).any() else inside
            extra["colour"] = "bright" if inside >= ring else "dark"
            return ("bright_object" if inside >= ring else "dark_object"), 0.25, extra
        H_, S_, V_ = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        brown = (H_ >= 5) & (H_ <= 28) & (S_ >= 70) & (V_ >= 35) & (V_ <= 210)
        brown_frac = float(brown[cmask].mean())
        ycc = cv2.cvtColor(crop, cv2.COLOR_RGB2YCrCb)
        skin = (ycc[..., 1] >= 138) & (ycc[..., 1] <= 178) & (ycc[..., 2] >= 80) & (ycc[..., 2] <= 128) & \
            (ycc[..., 0] >= 60)
        skin_frac = float(skin[cmask].mean())
        extra["colour"] = colour_name(hsv_mean)
        extra["brown_frac"] = round(brown_frac, 3)
        extra["skin_frac"] = round(skin_frac, 3)
        if brown_frac >= 0.35:
            bm = (brown & cv2.dilate(cmask.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)).astype(np.uint8)
            bm = cv2.morphologyEx(bm, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            nb, lab, st, _ = cv2.connectedComponentsWithStats(bm, connectivity=8)
            if nb > 1:
                big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
                shape = arrow_shape(lab == big)
            else:
                shape = arrow_shape(cmask)
            extra["shape"] = shape
            if shape["elongation"] >= 2.2:
                conf = 0.4 + 0.2 * min(1.0, shape["arrow_score"] / 0.6)
                return "horde_sign", conf, extra
            return "brown_object", 0.3, extra
        if skin_frac >= 0.35 and area_frac < 0.02:
            return ("hand_in_heather" if cy_norm > 0.5 else "hand"), 0.35, extra
        return f"{extra['colour']}_object", 0.3, extra


