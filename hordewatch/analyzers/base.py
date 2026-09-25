"""Analyzer plugin contract.

Subclass Analyzer, set `name`, and override any of:
  on_frame(frame, ctx)  -> list[Observation]   every sampled video frame
  on_audio(chunk, ctx)  -> list[Observation]   every audio chunk (default 10 s, 16 kHz mono)
  on_tick(ctx)          -> list[Observation]   periodically (derived analyses over the DB)
Heavy analyzers declare `min_interval_s` (runner skips calls that come
sooner) and may request triggers: ctx.trigger("whiteboard") lets e.g. the
VLM analyzer run immediately when a board is detected.

Analyzers must be CPU-only by default, never block for more than a few
seconds per call (spawn their own worker thread for slow models), and degrade
gracefully when an optional dependency (tesseract, ollama, mediapipe,
birdnet, astrometry.net) is missing: log once and return [].
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..types import AudioChunk, Frame, Observation


@dataclass
class Context:
    db: Any
    config: dict
    clock: Any                      # types.StreamClock
    state: dict = field(default_factory=dict)   # per-run scratch shared between analyzers
    triggers: set = field(default_factory=set)
    log: logging.Logger = field(default_factory=lambda: logging.getLogger("hordewatch"))

    def trigger(self, name: str):
        self.triggers.add(name)

    def consume(self, name: str) -> bool:
        if name in self.triggers:
            self.triggers.discard(name)
            return True
        return False


class Analyzer:
    name = "base"
    min_interval_s = 0.0
    wants_frames = False
    wants_audio = False
    tick_interval_s = None

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def available(self) -> bool:
        """Return False (and log why) when a required dependency is missing."""
        return True

    def on_frame(self, frame: Frame, ctx: Context) -> list[Observation]:
        return []

    def on_audio(self, chunk: AudioChunk, ctx: Context) -> list[Observation]:
        return []

    def on_tick(self, ctx: Context) -> list[Observation]:
        return []
