"""Ingest diagnostics: check a live stream or recording without running the analyzers.

    .venv/bin/python -m hordewatch.ingest --url https://www.youtube.com/watch?v=EQHgfmZicc8 --seconds 120
    .venv/bin/python -m hordewatch.ingest --replay data/cuts/202609251620_202609251703.mp4 --max-items 20
    .venv/bin/python -m hordewatch.ingest --url ... --archive-segments --archive-dir data/hordewatch/archive

Prints one line per frame/audio chunk (capture/real time, timing method) and
a final summary: decoder mode, PDT latency, edge lag, bitrate, stalls by
kind, and media deficit. Run it first on the monitoring machine to confirm
that yt-dlp resolves the stream and PROGRAM-DATE-TIME timing is active.
"""
from __future__ import annotations

import argparse
import json
import logging
import threading
import time
from collections import Counter

from ..types import StreamClock
from . import make_source


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m hordewatch.ingest", description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", help="live page URL or direct HLS/media URL")
    g.add_argument("--replay", nargs="+", help="files/directories to replay")
    ap.add_argument("--seconds", type=float, default=90.0, help="stop after this many wall seconds")
    ap.add_argument("--max-items", type=int, default=0)
    ap.add_argument("--frame-interval", type=float, default=5.0)
    ap.add_argument("--mode", default="auto", choices=["auto", "segments", "direct"])
    ap.add_argument("--latency", type=float, default=30.0, help="StreamClock latency prior (s)")
    ap.add_argument("--archive-dir", default=None, help="archive JPEGs (and --archive-segments) here")
    ap.add_argument("--archive-segments", action="store_true")
    ap.add_argument("--speed", type=float, default=0.0, help="replay speed (0 = max)")
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if a.v else logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    if a.url:
        scfg = {"type": "live", "url": a.url, "frame_interval_s": a.frame_interval, "mode": a.mode,
                "archive": bool(a.archive_dir), "archive_segments": a.archive_segments}
    else:
        scfg = {"type": "replay", "files": a.replay, "frame_interval_s": a.frame_interval, "speed": a.speed,
                "archive": bool(a.archive_dir)}
    cfg = {"archive_dir": a.archive_dir}
    src = make_source(scfg, StreamClock(latency_s=a.latency), cfg)
    timer = threading.Timer(a.seconds, src.close)      # also fires while waiting in reconnect backoff
    timer.daemon = True
    timer.start()
    t0 = time.monotonic()
    n = 0
    try:
        for kind, it in src:
            n += 1
            extra = f"{it.w}x{it.h}" if kind == "frame" else f"{it.duration_s:.2f}s rms={float((it.samples ** 2).mean() ** 0.5):.4f}"
            lat = (it.capture_ts - it.real_ts).total_seconds()
            print(f"{kind:5s} #{it.index:<5d} capture={it.capture_ts.isoformat()} real={it.real_ts.isoformat()} "
                  f"lat={lat:6.2f}s {extra} {it.path or ''}", flush=True)
            if (a.max_items and n >= a.max_items) or time.monotonic() - t0 > a.seconds:
                break
    except KeyboardInterrupt:
        pass
    finally:
        timer.cancel()
        src.close()
    s = src.stats.snapshot()
    kinds = Counter(e["kind"] for e in s["stall_events"])
    summary = {k: s.get(k) for k in ("mode", "decoder", "timing", "resolver", "format_id", "resolution", "fps_in",
                                     "bitrate_kbps", "latency_pdt_s", "edge_lag_s", "edge_lag_min_s", "segments",
                                     "segments_skipped", "reconnects", "stalls", "stall_s_total", "media_deficit_s",
                                     "speed", "frames_out", "audio_s_out", "last_error")}
    summary["stall_kinds"] = dict(kinds)
    print(json.dumps(summary, indent=1, default=str))


if __name__ == "__main__":
    main()
