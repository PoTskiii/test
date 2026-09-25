"""Sources: live YouTube stream or replayed files -> ("frame", Frame) / ("audio", AudioChunk).

    src = make_source(cfg["source"], clock, cfg)
    for kind, item in src: ...
    src.close()
    src.stats            # StreamStats (live: bitrate, fps, stalls, reconnects, PDT latency, ...)

``type: live`` -> ``live.LiveSource``; ``type: replay`` -> ``replay.ReplaySource``.
See those modules for the config keys.

Stats bus
---------
The runner builds its ``Context`` before the source and does not pass it in,
so sources cannot write to ``ctx.state`` directly. Stats reach it through a
small process-wide bus instead:

* every source registers ``publish_stats`` as a ``StreamStats`` callback
  (throttled to about 1/s, plus on every stall event);
* ``bind_state(ctx.state)`` subscribes a state dict. ``StreamHealthAnalyzer``
  does this on its first call, and ``make_source(..., state=...)`` accepts
  one. After that each publish sets ``state['ingest_stats']`` (and
  ``state['ingest']``, the name used in CONTRACT.md) to the latest snapshot;
* ``pop_archive_request()`` lets a source see ``state['archive_next'] = True``
  set by any analyzer. It then force-archives the current frame.
"""
from __future__ import annotations

import threading
from typing import Optional

_BUS_LOCK = threading.Lock()
_BOUND: list = []
_LATEST: dict = {}


def bind_state(state: dict) -> None:
    """Subscribe a ctx.state dict to ingest stats (idempotent)."""
    if state is None:
        return
    with _BUS_LOCK:
        if not any(s is state for s in _BOUND):
            _BOUND.append(state)
        snap = _LATEST.get("snap")
    if snap is not None:
        state["ingest_stats"] = snap
        state["ingest"] = snap


def unbind_state(state: dict) -> None:
    with _BUS_LOCK:
        _BOUND[:] = [s for s in _BOUND if s is not state]


def publish_stats(snapshot: dict) -> None:
    """StreamStats callback: store the snapshot in every bound state dict."""
    with _BUS_LOCK:
        _LATEST["snap"] = snapshot
        targets = list(_BOUND)
    for st in targets:
        st["ingest_stats"] = snapshot
        st["ingest"] = snapshot


def latest_stats() -> Optional[dict]:
    with _BUS_LOCK:
        return _LATEST.get("snap")


def pop_archive_request() -> bool:
    """True (once) if an analyzer set ``state['archive_next'] = True`` in a bound state."""
    hit = False
    with _BUS_LOCK:
        targets = list(_BOUND)
    for st in targets:
        if st.get("archive_next"):
            st["archive_next"] = False
            hit = True
    return hit


def make_source(source_cfg: dict, clock, cfg: Optional[dict] = None, state: Optional[dict] = None):
    """Build the configured source. ``cfg`` is the full runner config (for archive_dir etc.)."""
    cfg = cfg or {}
    typ = (source_cfg or {}).get("type", "live")
    if typ == "live":
        from .live import LiveSource
        src = LiveSource(source_cfg, clock, cfg)
    elif typ == "replay":
        from .replay import ReplaySource
        src = ReplaySource(source_cfg, clock, cfg)
    else:
        raise ValueError(f"unknown source type {typ!r} (expected 'live' or 'replay')")
    if state is not None:
        bind_state(state)
    return src


__all__ = ["make_source", "bind_state", "unbind_state", "publish_stats", "latest_stats", "pop_archive_request"]
