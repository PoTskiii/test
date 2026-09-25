"""Main loop:  .venv/bin/python -m hordewatch.runner --config hordewatch.yaml

Sources yield ("frame", Frame) / ("audio", AudioChunk) items (see
hordewatch/ingest). Every item is stored, dispatched to the enabled analyzers
(respecting their min_interval_s), and resulting observations are written to
the DB. Tick analyzers run on their own interval.
"""
from __future__ import annotations

import argparse
import importlib
import logging
import time

import yaml

from .analyzers.base import Context
from .db import DB
from .types import StreamClock

# name -> "module:Class". Modules are imported lazily so missing optional deps only disable one analyzer.
ANALYZERS = {
    "whiteboard": "hordewatch.analyzers.whiteboard:WhiteboardAnalyzer",
    "vlm": "hordewatch.analyzers.vlm:VLMAnalyzer",
    "scene": "hordewatch.analyzers.scene:SceneChangeAnalyzer",
    "gesture": "hordewatch.analyzers.gesture:GestureAnalyzer",
    "sky": "hordewatch.analyzers.sky:SkyAnalyzer",
    "sun": "hordewatch.analyzers.sun:SunAnalyzer",
    "rain": "hordewatch.analyzers.rain:RainAnalyzer",
    "night": "hordewatch.analyzers.night:NightSkyAnalyzer",
    "audio_events": "hordewatch.analyzers.audio_events:AudioEventAnalyzer",
    "audio_loop": "hordewatch.analyzers.audio_loop:AudioLoopAnalyzer",
    "birds": "hordewatch.analyzers.birds:BirdAnalyzer",
    "stream_health": "hordewatch.analyzers.stream_health:StreamHealthAnalyzer",
    "aircraft_bridge": "hordewatch.bridges.adsb:AircraftBridge",
    "weather_bridge": "hordewatch.bridges.met:WeatherBridge",
    "astro_bridge": "hordewatch.astro.solver:AstroBridge",
    "engine_bridge": "hordewatch.bridges.engine:EngineBridge",
}

DEFAULT_CONFIG = {
    "db": "data/hordewatch/hordewatch.sqlite",
    "archive_dir": "data/hordewatch/archive",
    "source": {"type": "live", "url": "https://www.youtube.com/watch?v=EQHgfmZicc8",
               "frame_interval_s": 5.0, "audio_chunk_s": 10.0, "audio_sr": 16000, "archive_every_n_frames": 12},
    "clock": {"latency_s": 30.0, "latency_sigma_s": 15.0},
    "analyzers": ["whiteboard", "vlm", "scene", "gesture", "sky", "sun", "rain", "night",
                  "audio_events", "audio_loop", "stream_health",
                  "aircraft_bridge", "weather_bridge", "astro_bridge", "engine_bridge"],
    "analyzer_config": {},
    "camera": {"heading_deg": 220.0, "pitch_deg": 0.0, "roll_deg": 0.0, "hfov_deg": 70.0},
    "vlm": {"backend": "ollama", "url": "http://localhost:11434", "model": "llava:7b"},
}


def load_config(path=None):
    cfg = {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULT_CONFIG.items()}
    if path:
        with open(path) as f:
            user = yaml.safe_load(f) or {}
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg


def load_analyzers(cfg, log):
    out = []
    for name in cfg["analyzers"]:
        spec = ANALYZERS.get(name)
        if not spec:
            log.warning("unknown analyzer %s", name)
            continue
        mod, cls = spec.split(":")
        try:
            A = getattr(importlib.import_module(mod), cls)
            a = A({**cfg.get("analyzer_config", {}).get(name, {}), "_global": cfg})
            if a.available():
                out.append(a)
            else:
                log.warning("analyzer %s unavailable (missing dependency)", name)
        except Exception as e:  # never let one analyzer kill the monitor
            log.exception("analyzer %s failed to load: %s", name, e)
    return out


def make_source(cfg, clock):
    from .ingest import make_source as _make
    return _make(cfg["source"], clock, cfg)


def run(cfg, max_items=None):
    log = logging.getLogger("hordewatch")
    db = DB(cfg["db"])
    clock = StreamClock(**cfg["clock"])
    stored = db.calibration("latency_s")
    if stored is not None:
        clock.latency_s = float(stored)
    ctx = Context(db=db, config=cfg, clock=clock)
    analyzers = load_analyzers(cfg, log)
    log.info("analyzers: %s", [a.name for a in analyzers])
    last_call = {a.name: 0.0 for a in analyzers}
    last_tick = {a.name: 0.0 for a in analyzers}
    src = make_source(cfg, clock)
    n = 0
    try:
        for kind, item in src:
            if kind == "frame":
                db.add_frame(item)
            else:
                db.add_audio(item)
            now = time.monotonic()
            for a in analyzers:
                try:
                    obs = []
                    forced = bool(ctx.triggers) and kind == "frame"
                    if kind == "frame" and a.wants_frames and (forced or now - last_call[a.name] >= a.min_interval_s):
                        obs = a.on_frame(item, ctx)
                        last_call[a.name] = now
                    elif kind == "audio" and a.wants_audio and now - last_call[a.name] >= a.min_interval_s:
                        obs = a.on_audio(item, ctx)
                        last_call[a.name] = now
                    if a.tick_interval_s and now - last_tick[a.name] >= a.tick_interval_s:
                        obs = list(obs) + list(a.on_tick(ctx))
                        last_tick[a.name] = now
                    for o in obs or []:
                        db.add_observation(o)
                except Exception as e:
                    log.exception("analyzer %s error: %s", a.name, e)
            n += 1
            if max_items and n >= max_items:
                break
    finally:
        close = getattr(src, "close", None)
        if close:
            close()
    return db


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--max-items", type=int)
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if a.v else logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    run(load_config(a.config), max_items=a.max_items)


if __name__ == "__main__":
    main()
