"""StreamStats: thread-safe ingest statistics, published to analyzers.

Every source owns one ``StreamStats`` (``source.stats``). Reader threads,
the HLS fetcher and the supervisor update it; ``snapshot()`` returns a
JSON-friendly dict that is published (throttled, via callbacks) into
``ctx.state['ingest_stats']`` / ``ctx.state['ingest']`` by
``hordewatch.ingest.publish_stats`` so that analyzers, in particular
``analyzers.stream_health``, can read it without touching the source.

Two bounded series are kept for later analysis. Their times are unix epoch
seconds (floats), not ISO strings, so they can be analysed numerically.

``stall_events``  one dict per disruption::

    {id, kind, start, end, duration_s, onsite_start, onsite_method, seq, detail}

  kind:
    ``upstream``   the HLS playlist stopped advancing although our playlist
                   fetches succeeded. Nothing new reached YouTube, so the
                   on-site encoder or uplink (Starlink/4G) stalled, or YouTube
                   ingest did.
    ``gap``        media time is missing: consecutive segments'
                   EXT-X-PROGRAM-DATE-TIME are not contiguous. The on-site
                   uplink dropped out and the encoder did not back-fill.
                   ``onsite_start`` is exact to the PDT clock.
    ``local``      our own downloads failed or were slow, so it is our
                   network and says nothing about the site.
    ``decoder``    ffmpeg produced no output for too long (direct mode, where
                   the cause is unknown).
    ``reconnect``  the time between a session dying and the next one producing
                   data.
    ``skip``       segments fell out of the playlist window before we fetched
                   them (we were too slow).

``segment_series``  one dict per HLS media segment::

    {id, seq, pdt, dur, seen, recv, dl_s, bytes, lag_s, disc, hdr}

  ``lag_s = seen - (pdt + dur)``: how long after the encoder or ingest clock
  finished the segment it appeared in the playlist. Spikes are uplink or
  processing delays.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from datetime import datetime
from typing import Any, Callable, Optional

from ..types import UTC, iso


def _iso_or_none(ts):
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return iso(datetime.fromtimestamp(float(ts), UTC))
    return iso(ts)


class StreamStats:
    """Mutable, lock-protected counters and series; see module docstring."""

    SCALARS = (
        "mode", "state", "source", "started_utc", "bitrate_kbps", "fps_in", "fps_out", "resolution",
        "frames_out", "audio_chunks_out", "audio_s_out", "dropped_consumer", "dropped_decoder",
        "segments", "segments_skipped", "discontinuities", "stalls", "stall_s_total", "current_stall_since",
        "reconnects", "sessions", "last_error", "last_pdt", "latency_pdt_s", "edge_lag_s", "edge_lag_min_s",
        "target_duration", "media_deficit_s", "speed", "last_capture_ts", "last_real_ts", "timing",
        "stream_start", "format_id", "resolver", "pdt_offset_s", "decoder", "ffmpeg",
    )

    def __init__(self, mode: str = "live", source: str = "", series_len: int = 4000, publish_every_s: float = 1.0):
        self._lock = threading.RLock()
        self._callbacks: list[Callable[[dict], Any]] = []
        self._publish_every_s = publish_every_s
        self._last_publish = 0.0
        self._event_id = 0
        self._seg_id = 0
        for k in self.SCALARS:
            setattr(self, k, None)
        self.mode = mode
        self.source = source
        self.state = "init"
        self.started_utc = time.time()
        for k in ("frames_out", "audio_chunks_out", "dropped_consumer", "dropped_decoder", "segments",
                  "segments_skipped", "discontinuities", "stalls", "reconnects", "sessions"):
            setattr(self, k, 0)
        self.audio_s_out = 0.0
        self.stall_s_total = 0.0
        self.stall_events: deque = deque(maxlen=series_len)
        self.segment_series: deque = deque(maxlen=series_len)
        self._frame_walls: deque = deque(maxlen=64)

    # ------------------------------------------------------------------ updates
    def update(self, **kw):
        with self._lock:
            for k, v in kw.items():
                setattr(self, k, v)
        self._maybe_publish()

    def incr(self, key: str, n=1):
        with self._lock:
            setattr(self, key, (getattr(self, key, 0) or 0) + n)

    def note_frame(self, capture_ts: datetime, real_ts: datetime):
        now = time.time()
        with self._lock:
            self.frames_out += 1
            self.last_capture_ts = capture_ts.timestamp()
            self.last_real_ts = real_ts.timestamp()
            self._frame_walls.append(now)
            if len(self._frame_walls) >= 3:
                span = self._frame_walls[-1] - self._frame_walls[0]
                self.fps_out = (len(self._frame_walls) - 1) / span if span > 0 else None
        self._maybe_publish()

    def note_audio(self, duration_s: float):
        with self._lock:
            self.audio_chunks_out += 1
            self.audio_s_out += float(duration_s)
        self._maybe_publish()

    def add_stall(self, kind: str, start: float, end: float, onsite_start: Optional[float] = None,
                  onsite_method: Optional[str] = None, seq: Optional[int] = None, detail: str = "") -> dict:
        """Record a finished disruption (times: unix seconds)."""
        with self._lock:
            self._event_id += 1
            ev = {"id": self._event_id, "kind": kind, "start": float(start), "end": float(end),
                  "duration_s": round(max(0.0, float(end) - float(start)), 3),
                  "onsite_start": None if onsite_start is None else float(onsite_start),
                  "onsite_method": onsite_method, "seq": seq, "detail": detail}
            self.stall_events.append(ev)
            if kind in ("upstream", "gap", "decoder", "local", "reconnect"):
                self.stalls += 1
                self.stall_s_total += ev["duration_s"]
        self._maybe_publish(force=True)
        return ev

    def add_segment(self, **rec) -> dict:
        with self._lock:
            self._seg_id += 1
            rec = {"id": self._seg_id, **rec}
            self.segment_series.append(rec)
            self.segments += 1
        return rec

    # ------------------------------------------------------------------ output
    def snapshot(self) -> dict:
        with self._lock:
            d = {k: getattr(self, k) for k in self.SCALARS}
            d["started_utc"] = _iso_or_none(self.started_utc)
            d["current_stall_since"] = self.current_stall_since
            d["current_stall_s"] = (round(time.time() - self.current_stall_since, 3)
                                    if self.current_stall_since else 0.0)
            d["dropped"] = int(self.dropped_consumer + self.dropped_decoder + self.segments_skipped)
            d["stall_events"] = [dict(e) for e in self.stall_events]
            d["segment_series"] = [dict(s) for s in self.segment_series]
            d["snapshot_ts"] = time.time()
            return d

    def add_callback(self, cb: Callable[[dict], Any]):
        self._callbacks.append(cb)

    def publish(self):
        self._maybe_publish(force=True)

    def _maybe_publish(self, force: bool = False):
        if not self._callbacks:
            return
        now = time.monotonic()
        if not force and now - self._last_publish < self._publish_every_s:
            return
        self._last_publish = now
        snap = self.snapshot()
        for cb in list(self._callbacks):
            try:
                cb(snap)
            except Exception:  # a broken consumer must never kill ingest
                pass
