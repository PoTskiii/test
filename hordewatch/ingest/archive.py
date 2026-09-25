"""Archiving: JPEG frames, optional WAV chunks, optional raw HLS segments.

Layout (all times UTC, from the item's *real* timestamp)::

    archive_dir/YYYYMMDD/HHMMSS_<idx>.jpg        every archive_every_n_frames-th frame, plus forced ones
    archive_dir/YYYYMMDD/HHMMSS_<idx>.wav        every audio chunk if archive_audio: true (16-bit PCM)
    archive_dir/segments/YYYYMMDD/<seq>.ts       raw HLS segments if archive_segments: true
    archive_dir/segments/YYYYMMDD/index.m3u8     playlist of that day's segments with PROGRAM-DATE-TIME
    archive_dir/segments/YYYYMMDD/segments.jsonl {seq, pdt, dur, recv, file, bytes} per segment

Recording the raw segments makes it possible to re-run new analyzers over
the full-quality stream later. ``replay`` accepts ``index.m3u8`` and times
it exactly by PDT. At about 2.5 Mbit/s a 720p stream is about 1.1 GB/h, so
``archive_segments_max_gb`` deletes the oldest days first.

Forced archiving: an analyzer sets ``ctx.state['archive_next'] = True``. The
source then saves the frame the analyzer just saw, retroactively: the file is
written and ``frame.path`` is set on the object, though the DB row was
already inserted. It also saves the next frame, which is stored with its
path.
"""
from __future__ import annotations

import json
import logging
import math
import shutil
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

from ..types import UTC

log = logging.getLogger("hordewatch.ingest.archive")


def _stamp(ts: datetime) -> tuple:
    t = ts.astimezone(UTC)
    return t.strftime("%Y%m%d"), t.strftime("%H%M%S")


class Archiver:
    def __init__(self, archive_dir, every_n_frames: int = 12, jpeg_quality: int = 90, audio: bool = False,
                 enabled: bool = True):
        self.dir = Path(archive_dir) if archive_dir else None
        self.every_n = int(every_n_frames or 0)
        self.quality = int(jpeg_quality)
        self.audio = bool(audio)
        self.enabled = bool(enabled) and self.dir is not None
        self._warned = False
        self.saved_frames = 0
        self.saved_audio = 0

    def path_for(self, ts: datetime, idx: int, ext: str) -> Path:
        day, hms = _stamp(ts)
        return self.dir / day / f"{hms}_{idx}{ext}"

    def maybe_save_frame(self, frame, force: bool = False) -> Optional[str]:
        if not self.enabled or frame.path:
            return frame.path
        if force or (self.every_n > 0 and frame.index % self.every_n == 0):
            return self.save_frame(frame)
        return None

    def save_frame(self, frame) -> Optional[str]:
        if not self.enabled:
            return None
        p = self.path_for(frame.real_ts, frame.index, ".jpg")
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            if not write_jpeg(p, frame.image, self.quality):
                return None
        except Exception as e:
            if not self._warned:
                log.warning("frame archive failed (%s): %s", p, e)
                self._warned = True
            return None
        frame.path = str(p)
        self.saved_frames += 1
        return frame.path

    def maybe_save_audio(self, chunk) -> Optional[str]:
        if not (self.enabled and self.audio) or chunk.path:
            return chunk.path
        p = self.path_for(chunk.real_ts, chunk.index, ".wav")
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            write_wav(p, chunk.samples, chunk.sr)
        except Exception as e:
            log.warning("audio archive failed (%s): %s", p, e)
            return None
        chunk.path = str(p)
        self.saved_audio += 1
        return chunk.path


def write_jpeg(path, rgb: np.ndarray, quality: int = 90) -> bool:
    try:
        import cv2
        return bool(cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, quality]))
    except ImportError:
        pass
    try:
        from PIL import Image
        Image.fromarray(rgb).save(str(path), quality=quality)
        return True
    except ImportError:
        log.warning("neither opencv nor Pillow installed: cannot archive JPEGs")
        return False


def write_wav(path, samples: np.ndarray, sr: int):
    pcm = np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sr))
        w.writeframes(pcm.tobytes())


class SegmentArchiver:
    """Record raw HLS segments with a PDT-tagged playlist per UTC day (see module docstring)."""

    def __init__(self, root, max_gb: float = 20.0, prune_every: int = 50):
        self.root = Path(root)
        self.max_bytes = float(max_gb) * 1e9 if max_gb else None
        self.prune_every = prune_every
        self._n = 0
        self._last_seq: dict = {}

    def write(self, seg, data: bytes, recv: float):
        ts = seg.pdt or datetime.fromtimestamp(recv, UTC)
        day = ts.astimezone(UTC).strftime("%Y%m%d")
        d = self.root / day
        d.mkdir(parents=True, exist_ok=True)
        name = f"{seg.seq:010d}.ts"
        (d / name).write_bytes(data)
        idx = d / "index.m3u8"
        lines = []
        if not idx.exists():
            lines += ["#EXTM3U", "#EXT-X-VERSION:3", f"#EXT-X-TARGETDURATION:{max(10, math.ceil(seg.duration))}",
                      f"#EXT-X-MEDIA-SEQUENCE:{seg.seq}"]
        last = self._last_seq.get(day)
        if last is not None and seg.seq != last + 1:
            lines.append("#EXT-X-DISCONTINUITY")
        if seg.pdt is not None:
            lines.append("#EXT-X-PROGRAM-DATE-TIME:" + seg.pdt.astimezone(UTC).isoformat(timespec="milliseconds"))
        lines += [f"#EXTINF:{seg.duration:.3f},", name]
        with open(idx, "a") as f:
            f.write("\n".join(lines) + "\n")
        with open(d / "segments.jsonl", "a") as f:
            f.write(json.dumps({"seq": seg.seq, "pdt": seg.pdt.timestamp() if seg.pdt else None,
                                "dur": seg.duration, "recv": recv, "file": name, "bytes": len(data)}) + "\n")
        self._last_seq[day] = seg.seq
        self._n += 1
        if self.max_bytes and self._n % self.prune_every == 0:
            self.prune()

    def prune(self):
        days = sorted(p for p in self.root.iterdir() if p.is_dir())
        sizes = {p: sum(f.stat().st_size for f in p.iterdir() if f.is_file()) for p in days}
        total = sum(sizes.values())
        while days[:-1] and total > self.max_bytes:     # never delete the current day
            victim = days.pop(0)
            log.warning("segment archive over %.1f GB: deleting %s", self.max_bytes / 1e9, victim)
            shutil.rmtree(victim, ignore_errors=True)
            total -= sizes[victim]
