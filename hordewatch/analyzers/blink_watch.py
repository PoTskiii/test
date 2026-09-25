"""Periodic full-frame-rate bursts to catch blinking lights (Morse, digit groups, LEDs).

The main pipeline samples one frame every few seconds, which cannot resolve a
blink. This analyzer records a short burst (default 60 s) of the live stream at
full frame rate every `interval_min` minutes (by default only at night, when
point lights are visible in IR mode), runs hordewatch.blink auto-detection, and
emits a `blinking_light` observation per detected point. A new Morse decode or
digit group raises a dashboard event.

Config (analyzer_config.blink_watch): interval_min (15), seconds (60),
night_only (True), url (defaults to the source URL), keep_clips (True).
"""
from __future__ import annotations

import threading
import time
from datetime import timedelta
from pathlib import Path

from ..types import Observation, utcnow
from .base import Analyzer


class BlinkWatchAnalyzer(Analyzer):
    name = "blink_watch"
    wants_frames = False
    tick_interval_s = 30.0

    def __init__(self, config=None):
        super().__init__(config)
        self.interval_s = float(self.config.get("interval_min", 15)) * 60
        self.seconds = int(self.config.get("seconds", 60))
        self.night_only = bool(self.config.get("night_only", True))
        g = self.config.get("_global", {})
        self.url = self.config.get("url") or g.get("source", {}).get("url")
        self.out_dir = Path(g.get("archive_dir", "data/hordewatch/archive")) / "bursts"
        self._last = 0.0
        self._worker = None
        self._results = []
        self._lock = threading.Lock()

    def available(self):
        if not self.url:
            return False
        try:
            import yt_dlp  # noqa: F401
            return True
        except ImportError:
            return False

    def _is_night(self, ctx):
        # the sky analyzer records IR mode; fall back to the clock (18:30-07:30 Europe/Oslo ~ 16:30-05:30 UTC)
        ir = ctx.state.get("ir_mode")
        if ir is not None:
            return bool(ir)
        h = utcnow().hour
        return h >= 17 or h < 5

    def _run_burst(self, started):
        from .. import blink
        try:
            self.out_dir.mkdir(parents=True, exist_ok=True)
            clip = self.out_dir / f"burst_{started.strftime('%Y%m%dT%H%M%SZ')}.mp4"
            blink.record(self.url, self.seconds, clip)
            res = blink.analyze(clip, auto=True, top=6)
            with self._lock:
                self._results.append((started, clip, res))
        except Exception as e:  # network / decoding problems must not kill the monitor
            with self._lock:
                self._results.append((started, None, {"error": str(e)}))

    def on_tick(self, ctx):
        out = []
        with self._lock:
            done, self._results = self._results, []
        for started, clip, res in done:
            if "error" in res:
                ctx.log.warning("blink burst failed: %s", res["error"])
                continue
            real = started - timedelta(seconds=ctx.clock.latency_s)
            for t in res.get("targets", []):
                v = {"x": t["x"], "y": t["y"], "frame_size": res.get("frame_size"), "verdict": t["verdict"],
                     "morse_text": t["morse"].get("text") if t["morse"].get("plausible") else None,
                     "groups": t["groups"].get("groups") if t["groups"].get("ok") else None,
                     "period_s": t["periodicity"].get("period_s"), "duty": t["periodicity"].get("duty"),
                     "n_flashes": t["n_flashes"], "clip": str(clip)}
                conf = 0.7 if (v["morse_text"] or v["groups"]) else 0.4
                out.append(Observation("blinking_light", real, v, self.name, confidence=conf, ts_capture=started))
                if v["morse_text"] or (v["groups"] and len(set(v["groups"])) > 1):
                    ctx.db.add_event(real, "blinking_light", f"Blinking light at ({t['x']},{t['y']}): {t['verdict']}", v)
        now = time.monotonic()
        busy = self._worker is not None and self._worker.is_alive()
        if not busy and now - self._last >= self.interval_s and (not self.night_only or self._is_night(ctx)):
            self._last = now
            self._worker = threading.Thread(target=self._run_burst, args=(utcnow(),), daemon=True)
            self._worker.start()
        return out
