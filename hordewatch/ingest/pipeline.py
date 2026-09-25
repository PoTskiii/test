"""Shared plumbing between live and replay sources.

* ``ReceiveClock``: estimates "when did this media reach us" from noisy
  arrival times. ffmpeg emits frames in bursts: a whole HLS segment is
  downloaded and decoded at once. So ``capture = pts + min(wall - pts)`` over
  a sliding window. The running minimum tracks the earliest-arrival envelope,
  which removes the burst and decode-buffer jitter. After a real stall the
  offset grows once the pre-stall samples have left the window, which is
  correct: we are then further behind the live edge.
* ``AudioChunker``: int16 blocks become float32 [-1, 1] chunks of
  ``audio_chunk_s``.
* Timing policies map (pts, wall) to (capture_unix, real_unix, method):
    - ``LiveTiming``: HLS PDT through ``PtsTimeMap`` when available
      (real = PDT + offset - pdt_offset_s), else receive time and
      ``StreamClock``.
    - ``FileTiming``: file-derived start + pts * stretch (replay).
    - ``PdtFileTiming``: replay of a recorded HLS playlist (real = PDT).
* ``DecoderHost``: owns the current ffmpeg ``DecodeSession``: restarts,
  draining, audio chunking, and turning callbacks into timed items.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import Callable, Optional

import numpy as np

from .ffmpeg import DecodeSession

log = logging.getLogger("hordewatch.ingest")


class ReceiveClock:
    def __init__(self, window_s: float = 60.0):
        self.window_s = window_s
        self._obs: deque = deque()
        self._lock = threading.Lock()
        self.offset: Optional[float] = None

    def observe(self, pts: Optional[float], wall: float) -> float:
        if pts is None:
            return wall
        with self._lock:
            self._obs.append((wall, wall - pts))
            while self._obs and wall - self._obs[0][0] > self.window_s:
                self._obs.popleft()
            self.offset = min(o for _, o in self._obs)
            return pts + self.offset

    def estimate(self, pts: Optional[float], wall: float) -> float:
        if pts is None or self.offset is None:
            return wall
        return pts + self.offset


class AudioChunker:
    """Accumulate int16 sample blocks into float32 chunks (start_index, samples)."""

    def __init__(self, sr: int, chunk_s: float, min_partial_s: float = 1.0):
        self.sr = int(sr)
        self.n = max(1, int(round(chunk_s * sr)))
        self.min_partial = int(round(min_partial_s * sr))
        self._buf: list = []
        self._len = 0
        self._start: Optional[int] = None

    def push(self, samples: np.ndarray, first_index: int) -> list:
        out = []
        if self._start is not None and first_index != self._start + self._len:
            # non-contiguous input (should not happen inside a session): flush what we have
            p = self.flush()
            if p:
                out.append(p)
        if self._start is None:
            self._start = first_index
        pos = 0
        while pos < len(samples):
            take = min(self.n - self._len, len(samples) - pos)
            self._buf.append(samples[pos:pos + take])
            self._len += take
            pos += take
            if self._len >= self.n:
                out.append(self._emit())
                self._start = first_index + pos
        return out

    def _emit(self):
        arr = np.concatenate(self._buf).astype(np.float32) / 32768.0
        start = self._start
        self._buf, self._len, self._start = [], 0, None
        return start, arr

    def flush(self):
        if self._len >= max(1, self.min_partial):
            return self._emit()
        self._buf, self._len, self._start = [], 0, None
        return None


# ---------------------------------------------------------------------------- timing policies
class LiveTiming:
    """Live timing: PDT when the frame's segment is known, else receive clock + StreamClock latency."""

    def __init__(self, clock, time_map=None, pdt_offset_s: float = 0.0, real_from_pdt: bool = True,
                 stats=None, window_s: float = 60.0):
        self.clock = clock
        self.time_map = time_map
        self.pdt_offset_s = float(pdt_offset_s or 0.0)
        self.real_from_pdt = real_from_pdt
        self.stats = stats
        self.rclock = ReceiveClock(window_s)
        self._lat: deque = deque(maxlen=24)

    def reset_session(self):
        self.rclock = ReceiveClock(self.rclock.window_s)

    def _times(self, pts, wall, observe=True):
        e, d = (self.time_map.lookup(pts) if self.time_map is not None else (None, None))
        if e is not None:
            cap = e.recv + d
            if e.pdt is not None and self.real_from_pdt:
                real = e.pdt + d - self.pdt_offset_s
                self._lat.append(cap - real)
                if self.stats is not None:
                    self.stats.update(latency_pdt_s=round(float(np.median(self._lat)), 3), timing="pdt")
                return cap, real, "pdt"
            return cap, cap - self.clock.latency_s, "segment_recv"
        cap = self.rclock.observe(pts, wall) if observe else self.rclock.estimate(pts, wall)
        if self.stats is not None:
            self.stats.update(timing="receive_clock")
        return cap, cap - self.clock.latency_s, "receive_clock"

    def frame_times(self, pts, wall, n=None):
        return self._times(pts, wall)

    def audio_times(self, pts, wall):
        cap, real, m = self._times(pts, wall, observe=False)
        return cap, real + float(getattr(self.clock, "audio_offset_s", 0.0) or 0.0), m

    def observe_audio_block(self, pts, wall):
        if pts is not None and (self.time_map is None or self.time_map.lookup(pts)[0] is None):
            self.rclock.observe(pts, wall)


class FileTiming:
    """Replay of a file: capture = start + (pts - pts0) * stretch; real = capture - latency_s."""

    def __init__(self, start_unix: float, stretch: float = 1.0, latency_s: float = 0.0, frame_interval_s: float = 5.0,
                 audio_offset_s: float = 0.0, pts0: float = 0.0):
        self.start = start_unix
        self.stretch = stretch
        self.latency_s = latency_s
        self.frame_interval_s = frame_interval_s
        self.audio_offset_s = audio_offset_s
        self.pts0 = pts0

    def frame_times(self, pts, wall, n=None):
        t = (pts if pts is not None else (n or 0) * self.frame_interval_s) - self.pts0
        cap = self.start + t * self.stretch
        return cap, cap - self.latency_s, "file"

    def audio_times(self, pts, wall):
        cap = self.start + ((pts or 0.0) - self.pts0) * self.stretch
        return cap, cap - self.latency_s + self.audio_offset_s, "file"

    def observe_audio_block(self, pts, wall):
        pass


class PdtFileTiming:
    """Replay of a recorded HLS playlist: capture = PDT + offset; real = capture - latency_s."""

    def __init__(self, time_map, latency_s: float = 0.0, audio_offset_s: float = 0.0):
        self.time_map = time_map
        self.latency_s = latency_s
        self.audio_offset_s = audio_offset_s
        self._last = None

    def _t(self, pts):
        e, d = self.time_map.lookup(pts)
        if e is None or e.pdt is None:
            if self._last is None:
                return None
            return self._last
        self._last = e.pdt + d
        return self._last

    def frame_times(self, pts, wall, n=None):
        t = self._t(pts)
        t = wall if t is None else t
        return t, t - self.latency_s, "pdt"

    def audio_times(self, pts, wall):
        t = self._t(pts)
        t = wall if t is None else t
        return t, t - self.latency_s + self.audio_offset_s, "pdt"

    def observe_audio_block(self, pts, wall):
        pass


# ---------------------------------------------------------------------------- decoder host
class DecoderHost:
    """Manage DecodeSession lifetimes and convert their output to timed items.

    ``emit(kind, capture_unix, real_unix, payload, meta)`` receives
    ``payload`` = HxWx3 uint8 RGB for frames and float32 samples for audio.
    """

    def __init__(self, session_kwargs: dict, timing, emit: Callable, audio_sr: int = 16000,
                 audio_chunk_s: float = 10.0, min_partial_s: float = 1.0, label: str = "", on_session_end=None):
        self.session_kwargs = dict(session_kwargs)
        self.timing = timing
        self.emit = emit
        self.audio_sr = audio_sr
        self.audio_chunk_s = audio_chunk_s
        self.min_partial_s = min_partial_s
        self.label = label
        self.on_session_end = on_session_end
        self.session: Optional[DecodeSession] = None
        self.sessions = 0
        self._lock = threading.RLock()

    def start(self, **overrides) -> DecodeSession:
        with self._lock:
            kw = {**self.session_kwargs, **overrides}
            chunker = AudioChunker(self.audio_sr, self.audio_chunk_s, self.min_partial_s)
            holder = {}
            if hasattr(self.timing, "reset_session"):
                self.timing.reset_session()
            timing = self.timing

            def on_frame(n, pts, img, wall):
                cap, real, method = timing.frame_times(pts, wall, n)
                self.emit("frame", cap, real, img, {"pts": pts, "n": n, "timing": method})

            def on_audio(samples, idx0, wall):
                s = holder["s"]
                pts_block = s.audio_pts_at(idx0)
                timing.observe_audio_block(pts_block, wall - len(samples) / float(self.audio_sr))
                for start, arr in chunker.push(samples, idx0):
                    pts = s.audio_pts_at(start)
                    cap, real, method = timing.audio_times(pts, wall)
                    self.emit("audio", cap, real, arr, {"pts": pts, "timing": method})

            def on_end(sess):
                p = chunker.flush()
                if p is not None:
                    start, arr = p
                    pts = sess.audio_pts_at(start, timeout=0.2)
                    cap, real, method = timing.audio_times(pts, time.time())
                    self.emit("audio", cap, real, arr, {"pts": pts, "timing": method, "partial": True})
                if self.on_session_end:
                    self.on_session_end(sess)

            s = DecodeSession(**kw, on_frame=on_frame, on_audio=on_audio, on_end=on_end,
                              audio_sr=self.audio_sr, label=self.label)
            holder["s"] = s
            s.start()
            self.session = s
            self.sessions += 1
            return s

    def write(self, data: bytes, restart: bool = False):
        """Feed bytes to the current stdin session, (re)starting it when needed."""
        with self._lock:
            if restart and self.session is not None:
                self.finish()
            if self.session is None or not self.session.alive:
                if self.session is not None:
                    log.warning("%s: ffmpeg exited (%s): %s - restarting", self.label, self.session.returncode,
                                self.session.error_summary())
                    self.finish(timeout=2.0)
                self.start()
            try:
                self.session.write(data)
            except (BrokenPipeError, OSError, ValueError) as e:
                log.warning("%s: ffmpeg input broke (%s): %s - restarting", self.label, e, self.session.error_summary())
                self.finish(timeout=2.0)
                self.start()
                self.session.write(data)

    def finish(self, timeout: float = 15.0):
        """Close input, let ffmpeg drain, wait for readers."""
        with self._lock:
            s = self.session
            self.session = None
        if s is None:
            return
        s.close_stdin()
        if not s.wait(timeout):
            s.terminate()

    def terminate(self):
        with self._lock:
            s = self.session
            self.session = None
        if s is not None:
            s.terminate()
