"""'Pointing up / at the sky' detector (analyzer name: ``gesture``).

Anja has several times pointed at aircraft. Matched against ADS-B tracks, the
*time* of such a gesture (and roughly the direction) constrains where the box
is: an aircraft that is overhead at that moment passes over a known ground
track. The emphasis here is therefore on precise, honestly-bounded timestamps.

Two detectors
  1. MediaPipe PoseLandmarker (if ``pose_model_path`` points to a
     ``pose_landmarker_{lite,full}.task`` file and MediaPipe can create the
     task). mediapipe 1.0.x ships only the Tasks API and *no* model files; the
     model must be downloaded once on the monitoring machine, e.g.
     https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task
     (in this dev container googleapis is blocked and the Tasks runtime also
     needs libEGL, so the fallback is what the tests exercise). Pointing =
     wrist above the shoulder, shoulder->wrist angle from vertical <=
     ``max_angle_deg``; a straight elbow (> 130 deg) raises confidence.
  2. Fallback, no model: classical silhouette analysis.
       * Person mask = |frame - background| where the background is the per-pixel
         median of a ring of past frames (gain-compensated, so exposure changes
         do not light up the whole frame).
       * Largest person-sized blob. Its torso width is the median row width of
         the middle band; a morphological opening with a disk of ~0.5 x torso
         width removes thin limbs and keeps the trunk ("core").
       * Limbs = blob minus core. A limb whose top reaches well above the
         shoulder line (the top of the wide part of the core) by >= 0.9 torso
         widths is a raised arm; its angle from vertical is measured from the
         attachment point (limb pixel nearest the core) to the tip. The head
         (compact, centred, short) never reaches that high.
       * Hand cue: skin colour (day, YCrCb) or bright IR skin near the tip.
       * Arm-only path: if she sat still long enough to become background, only
         the moving arm differs; a very elongated (>= 4.5:1), near-vertical blob
         with a hand cue at its top end is accepted with lower confidence.
       * Both arms up = stretching/waving -> lower confidence.

Output
  ``gesture_point_up`` on the *onset* frame of each episode (phase 'onset'):
    arm_angle_deg_from_vertical (image plane, 0 = straight up), side ('left' /
    'right' in the image), bbox (person, full-res px), method, onset_window
    [real time of the last frame without the gesture, real time of this frame],
    ts_uncertainty_s (half the sampling gap + latency sigma), latency_s used,
    world_hint {az_deg, elev_deg} from the camera heading assuming the arm lies
    in the image plane (rough!). ``ctx.trigger('aircraft_check')`` is fired and
    a request is appended to ``ctx.state['aircraft_check_requests']``.
  A second observation (phase 'summary') when a multi-frame episode ends,
  with the angle track - the arm follows the aircraft, so the track gives the
  direction of motion.
  ``person_count`` (MediaPipe path only) when the number of people changes.
  ``ctx.state['person_bbox']`` is published for the scene analyzer to exclude.

Timing caveats: frames are sampled every ``frame_interval_s`` (5 s), so a brief
point can be missed and the onset is only known within the sampling gap; the
real-time estimate inherits the stream latency uncertainty (StreamClock). For
aircraft matching use onset_window widened by ts_uncertainty_s. ``latency_s`` in
the value is the latency actually applied to *this* frame (capture_ts -
real_ts: PDT-measured or StreamClock), and ``timing`` is the ingest's timing
method when known. Both observations of an episode carry the onset frame's
(ts, ts_capture) pair - the ADS-B bridge clusters on ts_capture, so a summary
stamped at the end of a long episode would become a second, wrong sighting.

Robustness: the background buffer is reset when the source size changes
(adaptive bitrate: 720p -> 144p) or the camera switches day <-> IR (2-frame
hysteresis), since a median over mixed frames is meaningless; grey/RGBA/float
frames are coerced to RGB uint8; the per-episode angle track is capped.
``aircraft_check`` is a pulse withdrawn after ``trigger_ttl_s`` of stream time.

Failure modes (fallback): a person who has been motionless for minutes becomes
part of the background median (only the moving arm then shows - handled by the
arm-only path, which needs a visible hand); reflections on the transparent
walls; two people overlapping; an arm raised in front of the body (no
silhouette protrusion); long sleeves in IR (no hand cue).
"""
from __future__ import annotations

import logging
import os
from collections import deque
from typing import Optional

import cv2
import numpy as np

from ..types import Observation, iso
from .base import Analyzer, Context
from .whiteboard import as_rgb_u8, expire_pulses, pulse_trigger

log = logging.getLogger("hordewatch.gesture")


def _angle_from_vertical(vx: float, vy: float) -> float:
    """Angle (deg) between image vector (vx, vy) (y down) and straight up; 0 = up, 180 = down."""
    n = float(np.hypot(vx, vy))
    if n < 1e-6:
        return 180.0
    return float(np.degrees(np.arccos(np.clip(-vy / n, -1, 1))))


def _inside_frac(a, b) -> float:
    """Fraction of box a's area inside box b (boxes x0, y0, x1, y1)."""
    iw = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    return iw * ih / max((a[2] - a[0]) * (a[3] - a[1]), 1e-6)


def _is_ir(small: np.ndarray) -> bool:
    x = small.astype(np.int16)
    chan = (np.abs(x[..., 0] - x[..., 1]).mean() + np.abs(x[..., 1] - x[..., 2]).mean()) / 2.0
    return bool(chan < 4.0)


# ------------------------------------------------------------------------------------ fallback
class SilhouettePose:
    """Model-free raised-arm detector on a motion/background silhouette."""

    def __init__(self, bg_len=30, bg_every=2, bg_min=4, fg_thr=26.0, min_person_h_frac=0.12,
                 max_angle_deg=65.0, min_excursion=0.9):
        self.buf = deque(maxlen=int(bg_len))
        self.bg_every = max(1, int(bg_every))
        self.bg_min = int(bg_min)
        self.fg_thr = float(fg_thr)
        self.min_person_h_frac = float(min_person_h_frac)
        self.max_angle = float(max_angle_deg)
        self.min_excursion = float(min_excursion)
        self._count = 0
        self._pushes = 0
        self._bg = None
        self._bg_dirty = True

    def _background(self):
        if self._bg_dirty or self._bg is None:
            self._bg = np.median(np.stack(self.buf, 0), axis=0).astype(np.float32)
            self._bg_dirty = False
        return self._bg

    def foreground(self, small: np.ndarray) -> Optional[np.ndarray]:
        if self.buf and self.buf[-1].shape != small.shape:
            self.reset()                     # stream resolution changed: the old background is useless
        if len(self.buf) < self.bg_min:
            return None
        bg = self._background()
        cur = small.astype(np.float32)
        gb = float(np.median(bg.mean(axis=2))) + 1.0
        gc = float(np.median(cur.mean(axis=2))) + 1.0
        diff = np.abs(cur - bg * (gc / gb)).max(axis=2)
        mad = float(np.median(diff))
        thr = max(self.fg_thr, 4.0 * 1.4826 * mad)
        fg = (diff > thr).astype(np.uint8)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
        cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filled = np.zeros_like(fg)
        cv2.drawContours(filled, cnts, -1, 1, -1)
        return filled.astype(bool)

    def reset(self):
        self.buf.clear()
        self._bg = None
        self._bg_dirty = True
        self._pushes = 0

    def push(self, small: np.ndarray):
        self._count += 1
        if self.buf and self.buf[-1].shape != small.shape:
            self.reset()
        if len(self.buf) < self.bg_min or self._count % self.bg_every == 0:
            self.buf.append(small.copy())
            self._pushes += 1
            # the median is the expensive part (~40 ms for 24 x 400 px frames): refresh every 3rd push
            # once the buffer is warm
            if len(self.buf) <= self.bg_min + 1 or self._pushes % 3 == 0 or self._bg is None:
                self._bg_dirty = True

    def analyze(self, small: np.ndarray, ir: bool, not_person=()) -> Optional[dict]:
        """``not_person``: boxes (working px) of known non-person foreground - the held-up whiteboard.
        A blob lying >= 70 % inside one is not taken as the person (a big bright board otherwise wins
        the largest-blob vote and person_bbox points at the board, not at her)."""
        fg = self.foreground(small)
        self.push(small)
        if fg is None:
            return None
        h, w = fg.shape
        n, lab, st, _ = cv2.connectedComponentsWithStats(fg.astype(np.uint8), connectivity=8)
        best = None
        for i in range(1, n):
            x, y, bw, bh, area = st[i]
            if bh < self.min_person_h_frac * h or area < 0.002 * h * w:
                continue
            if any(_inside_frac((x, y, x + bw, y + bh), b) >= 0.7 for b in not_person):
                continue
            if best is None or area > st[best][4]:
                best = i
        if best is None:
            return {"person": False}
        x, y, bw, bh, _ = st[best]
        blob = (lab[y:y + bh, x:x + bw] == best)
        res = self._pose_from_blob(blob, small[y:y + bh, x:x + bw], ir)
        res.update({"person": True, "bbox_small": [int(x), int(y), int(x + bw), int(y + bh)]})
        if res.get("tip") is not None:
            res["tip"] = [res["tip"][0] + x, res["tip"][1] + y]
            res["attach"] = [res["attach"][0] + x, res["attach"][1] + y]
        if not res.get("pointing"):
            arm = self._arm_only(lab, st, n, small, ir)
            if arm is not None:
                res.update(arm)
        return res

    def _arm_only(self, lab, st, n, small, ir) -> Optional[dict]:
        """A person who sat still for minutes is part of the median background; then only the moving
        arm shows up. Accept an isolated, very elongated blob (a straight arm, length/width >= 4.5)
        tilted <= max_angle from vertical with a hand (skin / bright IR skin) at its upper end."""
        h, w = lab.shape
        best = None
        for i in range(1, n):
            x, y, bw, bh, area = st[i]
            if area < 30 or max(bw, bh) < 0.06 * h or max(bw, bh) > 0.45 * h:
                continue
            py, px = np.nonzero(lab[y:y + bh, x:x + bw] == i)
            pts = np.stack([px + x, py + y], 1).astype(np.float32)
            ev, evec = np.linalg.eigh(np.cov((pts - pts.mean(0)).T))
            elong = float(np.sqrt(max(ev[-1], 1e-6) / max(ev[0], 1e-6)))
            if elong < 4.5:
                continue
            axis = evec[:, -1] * (1 if evec[1, -1] < 0 else -1)        # oriented upwards (y down)
            ang = _angle_from_vertical(float(axis[0]), float(axis[1]))
            if ang > self.max_angle:
                continue
            u = (pts - pts.mean(0)) @ axis
            tip = pts[int(np.argmax(u))]
            base = pts[int(np.argmin(u))]
            width = max(1.0, 4.0 * float(np.sqrt(max(ev[0], 1e-6))))
            if not self._hand_cue(small, tip, 1.5 * width, ir):
                continue
            cand = {"pointing": True, "angle": ang, "side": "left" if tip[0] < base[0] else "right",
                    "tip": tip.tolist(), "attach": base.tolist(), "elong": elong, "hand_cue": True,
                    "arm_only": True, "n_arms_up": 1, "bbox_small": [int(x), int(y), int(x + bw), int(y + bh)]}
            if best is None or elong > best["elong"]:
                best = cand
        return best

    def _pose_from_blob(self, blob: np.ndarray, rgb: np.ndarray, ir: bool) -> dict:
        Hb, Wb = blob.shape
        rows = blob.sum(axis=1).astype(float)
        band = rows[int(0.35 * Hb):max(int(0.7 * Hb), int(0.35 * Hb) + 1)]
        band = band[band > 0]
        if band.size == 0:
            return {"pointing": False}
        torso_w = float(np.median(band))
        k = int(max(3, round(0.5 * torso_w))) | 1
        core = cv2.morphologyEx(blob.astype(np.uint8), cv2.MORPH_OPEN,
                                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        nc, clab, cst, _ = cv2.connectedComponentsWithStats(core, connectivity=8)
        if nc < 2:
            return {"pointing": False, "torso_w": torso_w}
        ci = 1 + int(np.argmax(cst[1:, cv2.CC_STAT_AREA]))
        core = clab == ci
        crow = core.sum(axis=1)
        ys = np.nonzero(crow)[0]
        core_top = int(ys[0])
        # shoulder line: first core row that is at least 70 % of the torso width (skips a surviving head)
        wide = np.nonzero(crow >= 0.7 * torso_w)[0]
        shoulder_y = int(wide[0]) if wide.size else core_top
        cxs = np.nonzero(core[min(shoulder_y + int(0.3 * torso_w), Hb - 1)])[0]
        core_cx = float(cxs.mean()) if cxs.size else Wb / 2.0
        limbs = blob & ~cv2.dilate(core.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        nl, llab, lst, _ = cv2.connectedComponentsWithStats(limbs.astype(np.uint8), connectivity=8)
        dist_core = cv2.distanceTransform((~core).astype(np.uint8), cv2.DIST_L2, 3)
        arms = []
        for i in range(1, nl):
            if lst[i][4] < max(6, 0.05 * torso_w * torso_w):
                continue
            py, px = np.nonzero(llab == i)
            top_y = int(py.min())
            excursion = (shoulder_y - top_y) / max(torso_w, 1.0)
            j = int(np.argmin(dist_core[py, px]))
            ax, ay = float(px[j]), float(py[j])
            if excursion > 0:
                # raised limb: the tip is its highest point (mean x of the top rows)
                top_rows = py <= top_y + max(1, int(0.1 * torso_w))
                tx, ty = float(px[top_rows].mean()), float(top_y)
            else:
                d = np.hypot(px - ax, py - ay)
                tx, ty = float(px[int(np.argmax(d))]), float(py[int(np.argmax(d))])
            length = float(np.hypot(tx - ax, ty - ay)) / max(torso_w, 1.0)
            pts = np.stack([px, py], 1).astype(np.float32)
            if len(pts) > 3:
                ev, evec = np.linalg.eigh(np.cov((pts - pts.mean(0)).T))
            else:
                ev, evec = np.array([1.0, 1.0]), np.eye(2)
            elong = float(np.sqrt(max(ev[-1], 1e-6) / max(ev[0], 1e-6)))
            ang = _angle_from_vertical(tx - ax, ty - ay)
            if elong >= 2.5:
                # straight arm: its principal axis (oriented attach -> tip) is a better direction estimate
                # than the two endpoints, which are biased by the arm thickness
                axis = evec[:, -1] * (1 if np.dot(evec[:, -1], [tx - ax, ty - ay]) >= 0 else -1)
                ang = _angle_from_vertical(float(axis[0]), float(axis[1]))
            arms.append({"tip": [tx, ty], "attach": [ax, ay], "angle": ang, "excursion": excursion,
                         "length": length, "elong": elong, "side": "left" if tx < core_cx else "right"})
        up = [a for a in arms if a["excursion"] >= self.min_excursion and a["angle"] <= self.max_angle
              and a["length"] >= 0.6]
        res = {"pointing": bool(up), "torso_w": torso_w, "shoulder_y": shoulder_y, "arms": arms,
               "n_arms_up": len(up)}
        if up:
            a = max(up, key=lambda a: a["excursion"])
            res.update({"angle": a["angle"], "side": a["side"], "tip": a["tip"], "attach": a["attach"],
                        "elong": a["elong"], "excursion": a["excursion"],
                        "hand_cue": self._hand_cue(rgb, a["tip"], torso_w, ir)})
        return res

    @staticmethod
    def _hand_cue(rgb, tip, torso_w, ir) -> bool:
        r = int(max(3, 0.45 * torso_w))
        x, y = int(tip[0]), int(tip[1])
        patch = rgb[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1]
        if patch.size == 0:
            return False
        if ir:
            g = patch.mean(axis=2)
            return bool((g > np.percentile(rgb.mean(axis=2), 90)).mean() > 0.15)
        ycc = cv2.cvtColor(np.ascontiguousarray(patch), cv2.COLOR_RGB2YCrCb)
        skin = (ycc[..., 1] >= 138) & (ycc[..., 1] <= 178) & (ycc[..., 2] >= 80) & (ycc[..., 2] <= 128) & (ycc[..., 0] > 60)
        return bool(skin.mean() > 0.1)


# ------------------------------------------------------------------------------------ mediapipe
class MediaPipePose:
    """Thin wrapper over mediapipe.tasks PoseLandmarker (IMAGE mode, CPU delegate)."""

    def __init__(self, model_path: str, num_poses: int = 3, max_angle_deg: float = 65.0):
        import mediapipe as mp
        from mediapipe.tasks.python import vision
        from mediapipe.tasks.python.core.base_options import BaseOptions
        self.mp = mp
        opts = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path, delegate=BaseOptions.Delegate.CPU),
            running_mode=vision.RunningMode.IMAGE, num_poses=int(num_poses), min_pose_detection_confidence=0.5)
        self.lm = vision.PoseLandmarker.create_from_options(opts)
        self.max_angle = float(max_angle_deg)

    def analyze(self, small: np.ndarray, ir: bool) -> dict:
        h, w = small.shape[:2]
        img = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=np.ascontiguousarray(small))
        res = self.lm.detect(img)
        poses = res.pose_landmarks or []
        out = {"person": bool(poses), "n_persons": len(poses), "pointing": False}
        best = None
        for lms in poses:
            P = np.array([[l.x * w, l.y * h, getattr(l, "visibility", 1.0) or 0.0] for l in lms])
            xs, ys = P[:, 0], P[:, 1]
            bbox = [float(np.clip(xs.min(), 0, w)), float(np.clip(ys.min(), 0, h)),
                    float(np.clip(xs.max(), 0, w)), float(np.clip(ys.max(), 0, h))]
            sh_w = float(np.hypot(*(P[11, :2] - P[12, :2])))
            mid_x = float((P[11, 0] + P[12, 0]) / 2)
            for person_side, (s, e, wr) in (("person_left", (11, 13, 15)), ("person_right", (12, 14, 16))):
                if min(P[s, 2], P[wr, 2]) < 0.5:
                    continue
                v = P[wr, :2] - P[s, :2]
                ang = _angle_from_vertical(v[0], v[1])
                u1, u2 = P[s, :2] - P[e, :2], P[wr, :2] - P[e, :2]
                elbow = float(np.degrees(np.arccos(np.clip(np.dot(u1, u2) / (np.linalg.norm(u1) * np.linalg.norm(u2) + 1e-6), -1, 1))))
                raised = P[wr, 1] < P[s, 1] - 0.3 * max(sh_w, 1.0)
                if raised and ang <= self.max_angle and np.linalg.norm(v) > 0.5 * max(sh_w, 1.0):
                    cand = {"angle": ang, "side": "left" if P[wr, 0] < mid_x else "right", "person_side": person_side,
                            "tip": P[wr, :2].tolist(), "attach": P[s, :2].tolist(), "elbow_deg": elbow,
                            "bbox_small": bbox, "visibility": float(min(P[s, 2], P[wr, 2]))}
                    if best is None or cand["visibility"] > best["visibility"]:
                        best = cand
            if "bbox_small" not in out:
                out["bbox_small"] = bbox
        if best is not None:
            out.update(best)
            out["pointing"] = True
            out["hand_cue"] = best["elbow_deg"] > 130
        return out


# ------------------------------------------------------------------------------------ analyzer
class GestureAnalyzer(Analyzer):
    name = "gesture"
    wants_frames = True
    min_interval_s = 0.0

    DEFAULTS = {"work_w": 400, "pose_model_path": None, "num_poses": 3, "max_angle_deg": 65.0,
                "bg_len": 30, "bg_every": 2, "bg_min": 4, "fg_thr": 26.0, "min_person_h_frac": 0.12,
                "min_excursion": 0.9, "max_gap_frames": 1, "trigger_ttl_s": 60.0, "frame_interval_s": None,
                "max_track": 240, "ir_hysteresis": 2}

    def __init__(self, config=None):
        super().__init__(config)
        cfg = dict(config or {})
        self.g = cfg.pop("_global", {}) or {}
        self.p = {**self.DEFAULTS, **cfg}
        self.method = "fallback"
        self.detector = None
        path = self.p.get("pose_model_path") or os.environ.get("HORDEWATCH_POSE_MODEL")
        if path:
            if os.path.exists(path):
                try:
                    self.detector = MediaPipePose(path, self.p["num_poses"], self.p["max_angle_deg"])
                    self.method = "mediapipe"
                except Exception as e:
                    log.warning("gesture: MediaPipe PoseLandmarker unusable (%s); using silhouette fallback", e)
            else:
                log.warning("gesture: pose model %s not found; using silhouette fallback", path)
        if self.detector is None:
            self.detector = SilhouettePose(bg_len=self.p["bg_len"], bg_every=self.p["bg_every"],
                                           bg_min=self.p["bg_min"], fg_thr=self.p["fg_thr"],
                                           min_person_h_frac=self.p["min_person_h_frac"],
                                           max_angle_deg=self.p["max_angle_deg"],
                                           min_excursion=self.p["min_excursion"])
        self._episode = None
        self._prev_frame = None          # (real_ts, capture_ts) of the previous frame
        self._gap = 0
        self._last_n_persons = None
        self._ir_mode = None
        self._ir_votes = 0

    def available(self) -> bool:
        log.info("gesture: using %s detector", self.method)
        return True

    # ------------------------------------------------------------------ helpers
    def _world_hint(self, angle, side):
        cam = (self.g or {}).get("camera") or {}
        heading = float(cam.get("heading_deg", 220.0))
        if angle is None:
            return None
        if angle < 15:
            return {"az_deg": None, "elev_deg": round(90 - angle, 1), "assumption": "near-vertical arm: overhead"}
        az = (heading + (90.0 if side == "right" else -90.0)) % 360
        return {"az_deg": round(az, 1), "elev_deg": round(max(0.0, 90 - angle), 1),
                "assumption": f"arm in the image plane; camera heading {heading:.0f} deg; depth component unknown"}

    @staticmethod
    def _board_boxes(ctx, s):
        wbs = ctx.state.get("whiteboard")
        if isinstance(wbs, dict) and wbs.get("bbox") is not None:
            try:
                return [[float(v) * s for v in wbs["bbox"]]]
            except (TypeError, ValueError):
                return []
        return []

    def _regime(self, ir: bool) -> bool:
        """Day/IR with hysteresis; a confirmed switch resets the fallback background."""
        if self._ir_mode is None:
            self._ir_mode = ir
        elif ir != self._ir_mode:
            self._ir_votes += 1
            if self._ir_votes >= int(self.p["ir_hysteresis"]):
                self._ir_mode, self._ir_votes = ir, 0
                if isinstance(self.detector, SilhouettePose):
                    self.detector.reset()
                    log.info("gesture: camera switched to %s; background reset", "IR" if ir else "day")
        else:
            self._ir_votes = 0
        return ir

    # ------------------------------------------------------------------ main
    def on_frame(self, frame, ctx: Context):
        expire_pulses(ctx, frame.real_ts, frame.index)
        out = []
        img = as_rgb_u8(frame.image)
        H, W = img.shape[:2]
        if H < 8 or W < 8:
            return out
        # fixed working width (up- or down-scaled) so the background survives adaptive-bitrate switches
        s = self.p["work_w"] / float(W)
        small = cv2.resize(img, (int(self.p["work_w"]), max(8, int(round(H * s)))),
                           interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
        ir = self._regime(_is_ir(small))
        try:
            if isinstance(self.detector, SilhouettePose):
                r = self.detector.analyze(small, ir, not_person=self._board_boxes(ctx, s)) or {}
            else:
                r = self.detector.analyze(small, ir) or {}
        except Exception as e:
            log.warning("gesture detector failed: %s", e)
            r = {}
        prev = self._prev_frame
        self._prev_frame = (frame.real_ts, frame.capture_ts)
        bbox = None
        if r.get("bbox_small") is not None:
            b = r["bbox_small"]
            bbox = [int(b[0] / s), int(b[1] / s), int(np.ceil(b[2] / s)), int(np.ceil(b[3] / s))]
            ctx.state["person_bbox"] = {"bbox": bbox, "frame_index": frame.index, "ts": frame.real_ts}
        if self.method == "mediapipe" and r.get("n_persons") is not None and r["n_persons"] != self._last_n_persons:
            self._last_n_persons = r["n_persons"]
            out.append(Observation(kind="person_count", ts=frame.real_ts, analyzer=self.name, confidence=0.5,
                                   frame_id=frame.id, ts_capture=frame.capture_ts,
                                   value={"n": int(r["n_persons"]), "method": self.method}))
        pointing = bool(r.get("pointing"))
        if pointing:
            self._gap = 0
            angle, side = float(r["angle"]), r["side"]
            if self._episode is None:
                out.append(self._onset(frame, ctx, r, bbox, prev, ir))
            else:
                tr = self._episode["track"]
                tr.append([iso(frame.real_ts), round(angle, 1), side])
                if len(tr) > int(self.p["max_track"]):          # bounded: keep the start, thin the middle
                    keep = int(self.p["max_track"]) // 2
                    tr[:] = tr[:keep // 2] + tr[keep // 2:-keep // 2][::2] + tr[-keep // 2:]
                self._episode["n_frames"] = self._episode.get("n_frames", 1) + 1
                self._episode["last"] = frame.real_ts
        elif self._episode is not None:
            self._gap += 1
            if self._gap > self.p["max_gap_frames"]:
                out += self._end(frame)
        return out

    def _onset(self, frame, ctx, r, bbox, prev, ir):
        angle, side = float(r["angle"]), r["side"]
        clock = getattr(ctx, "clock", None)
        # the latency actually applied to this frame (PDT-measured or StreamClock), not the clock's current value
        lat = float((frame.capture_ts - frame.real_ts).total_seconds())
        lat_sig = float(getattr(clock, "latency_sigma_s", 0.0) or 0.0)
        ing = ctx.state.get("ingest") if isinstance(ctx.state.get("ingest"), dict) else {}
        timing = ing.get("timing")
        gap = (frame.real_ts - prev[0]).total_seconds() if prev else float(self.p["frame_interval_s"] or 5.0)
        unc = 0.5 * gap + lat_sig
        conf = (0.25 if r.get("arm_only") else 0.35) if self.method == "fallback" else 0.55
        conf += 0.1 if r.get("elong", 0) >= 2.5 or self.method == "mediapipe" else 0.0
        conf += 0.1 if r.get("hand_cue") else 0.0
        conf -= 0.1 if r.get("n_arms_up", 1) >= 2 else 0.0
        conf = round(float(np.clip(conf, 0.1, 0.35 if r.get("arm_only") else 0.8)), 3)
        value = {"arm_angle_deg_from_vertical": round(angle, 1), "side": side, "bbox": bbox, "method": self.method,
                 "phase": "onset", "onset_window": [iso(prev[0]) if prev else None, iso(frame.real_ts)],
                 "capture_ts": iso(frame.capture_ts), "ts_uncertainty_s": round(unc, 1), "latency_s": lat,
                 "latency_sigma_s": lat_sig, "timing": timing, "sampling_gap_s": round(gap, 2),
                 "both_arms": r.get("n_arms_up", 1) >= 2,
                 "hand_cue": bool(r.get("hand_cue")), "arm_only": bool(r.get("arm_only")), "ir_mode": ir,
                 "world_hint": self._world_hint(angle, side)}
        if r.get("elbow_deg") is not None:
            value["elbow_deg"] = round(float(r["elbow_deg"]), 1)
        self._episode = {"start": frame.real_ts, "start_capture": frame.capture_ts, "start_frame_id": frame.id,
                         "last": frame.real_ts, "prev": prev, "n_frames": 1,
                         "track": [[iso(frame.real_ts), round(angle, 1), side]], "value": value}
        pulse_trigger(ctx, "aircraft_check", frame.real_ts, self.p["trigger_ttl_s"], frame.index)
        req = ctx.state.setdefault("aircraft_check_requests", [])
        req.append({"ts": iso(frame.real_ts), "onset_window": value["onset_window"], "ts_uncertainty_s": unc,
                    "arm_angle_deg_from_vertical": value["arm_angle_deg_from_vertical"], "side": side,
                    "world_hint": value["world_hint"], "source": "gesture", "frame_id": frame.id})
        del req[:-50]
        ctx.state["archive_next"] = True
        log.info("gesture: pointing up (%s, %.0f deg from vertical, %s) at real %s", side, angle, self.method,
                 iso(frame.real_ts))
        return Observation(kind="gesture_point_up", ts=frame.real_ts, value=value, analyzer=self.name,
                           confidence=conf, frame_id=frame.id, ts_capture=frame.capture_ts)

    def _end(self, frame):
        ep, self._episode = self._episode, None
        self._gap = 0
        if ep is None or len(ep["track"]) < 2:
            return []
        v = dict(ep["value"])
        angles = [t[1] for t in ep["track"]]
        v.update({"phase": "summary", "track": ep["track"], "duration_s": (ep["last"] - ep["start"]).total_seconds(),
                  "n_frames": ep.get("n_frames", len(ep["track"])),
                  "end_window": [iso(ep["last"]), iso(frame.real_ts)], "end_frame_id": frame.id,
                  "arm_angle_deg_from_vertical": round(float(np.median(angles)), 1),
                  "angle_change_deg": round(angles[-1] - angles[0], 1)})
        # (ts, ts_capture) of the ONSET frame: a consistent pair, so the summary clusters with its onset
        return [Observation(kind="gesture_point_up", ts=ep["start"], value=v, analyzer=self.name, confidence=0.3,
                            frame_id=ep.get("start_frame_id", frame.id), ts_capture=ep.get("start_capture"),
                            notes="episode summary")]
