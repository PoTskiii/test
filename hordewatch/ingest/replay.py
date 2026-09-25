"""Replay source: local recordings -> ("frame", Frame) / ("audio", AudioChunk) in timestamp order.

Inputs (``files`` / ``paths`` / ``path``: a list of files and/or directories, searched recursively):
  * video: .mp4 .mkv .ts .m2ts .webm .mov .m4v .flv .avi. Decoded by ffmpeg
    (``ffmpeg.DecodeSession``). MPEG-TS is fed through stdin with the SDT
    table stripped (see hls.py).
  * audio: .wav .flac .ogg .mp3 .m4a .aac .opus. Resampled by ffmpeg to
    ``audio_sr`` mono.
  * images: every image file of one directory becomes one input (a frame per
    image).
  * HLS: ``index.m3u8``, e.g. hordewatch's own segment archive
    (archive_segments). Timed exactly by EXT-X-PROGRAM-DATE-TIME. Its .ts
    files are not also added as videos.

Timestamp rules (first match wins; the result is always UTC):
  1. ``start_utc`` as a dict ``{basename_or_path: ISO time}``: an explicit
     per-file start. It overrides the file name.
  2. default.no cuts ``YYYYMMDDHHMM_YYYYMMDDHHMM.<ext>``: start and end in
     Norwegian local time (Europe/Oslo, i.e. CEST = UTC+2 in September),
     converted to UTC. The names have minute resolution, so the true start is
     uncertain by up to 60 s. ``defaultno_align``: ``start`` (default) puts
     t=0 at the named start; ``end`` puts the last sample at the named end;
     ``stretch`` maps [0, duration] onto [start, end] (useful only if the cut
     is a time-lapse). A duration/name mismatch over max(5 s, 2 %) is logged.
     These cuts were recorded from the YouTube player, so they carry YouTube
     latency. Set ``latency_s`` (e.g. 20-40) or ``use_clock_latency: true``
     to shift real_ts to on-site time.
  3. hordewatch archive files ``YYYYMMDD/HHMMSS_<idx>.jpg`` (UTC).
  4. a generic date-time in the name (``20260925_162000``,
     ``2026-09-25T16-20-00Z``, ``IMG_20260925_162000``, ...). Local time in
     ``filename_tz`` (default Europe/Oslo) unless it has a 'Z'/'UTC'/offset
     suffix.
  5. sidecar ``<file>.json`` with ``{"start_utc": ...}``.
  6. ``start_utc`` as a string: used for inputs that matched nothing above;
     several such inputs are chained back to back in the given order.
  7. last resort: file mtime minus duration, logged as a warning.
  Image folders whose names do not all parse use ``start_utc`` (or the first
  parseable / mtime) plus a fixed ``image_interval_s`` (default
  frame_interval_s).

Timing: capture_ts = file-derived time; real_ts = capture_ts - latency_s
(default 0, or StreamClock.latency_s when ``use_clock_latency``). Audio also
gets ``StreamClock.audio_offset_s``.

Other keys: frame_interval_s (5), audio_chunk_s (10), audio_sr (16000),
audio (true), video (true), max_width (1280), speed (0 = as fast as
possible, 1 = real time, 10 = 10x). Gaps between recordings are never slept
through. Also filename_tz, min_partial_audio_s (1.0), keyframes_only,
decoder_threads (2), audio_transport, ffmpeg, and the archive keys: archive (true), archive_dir,
archive_every_n_frames, jpeg_quality, archive_audio.
"""
from __future__ import annotations

import heapq
import json
import logging
import os
import queue
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import numpy as np

from ..types import UTC, AudioChunk, Frame, parse_iso
from . import pop_archive_request, publish_stats, register_stats
from .archive import Archiver
from .ffmpeg import ProbeInfo, ffmpeg_exe, parse_input_header, probe
from .hls import HLSFetcher, PtsTimeMap, SegmentTimeline, parse_media_playlist, ts_scan, PTS_HZ, PTS_WRAP
from .pipeline import DecoderHost, FileTiming, PdtFileTiming
from .stats import StreamStats

log = logging.getLogger("hordewatch.ingest.replay")

VIDEO_EXT = {".mp4", ".mkv", ".ts", ".m2ts", ".mts", ".webm", ".mov", ".m4v", ".flv", ".avi"}
AUDIO_EXT = {".wav", ".flac", ".ogg", ".oga", ".mp3", ".m4a", ".aac", ".opus"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
TS_EXT = {".ts", ".m2ts", ".mts"}
OSLO = "Europe/Oslo"
_END = object()


# ============================================================================ filename time parsing
@dataclass
class NameTime:
    start: datetime
    end: Optional[datetime] = None
    rule: str = ""


_DEFAULTNO_RE = re.compile(r"(?<!\d)(\d{12})_(\d{12})(?!\d)")
_ARCHIVE_RE = re.compile(r"^(\d{6})_(\d+)$")
_GEN_S_RE = re.compile(r"(?<!\d)(20\d{2})[-_.]?(\d{2})[-_.]?(\d{2})[T _-]?(\d{2})[-:_.h]?(\d{2})[-:_.m]?(\d{2})"
                       r"(?:[.,](\d{1,6}))?(Z|z|UTC|utc|[+-]\d{2}:?\d{2})?(?!\d)")
_GEN_M_RE = re.compile(r"(?<!\d)(20\d{2})[-_.]?(\d{2})[-_.]?(\d{2})[T _-]?(\d{2})[-:_.h]?(\d{2})(Z|z|UTC|utc)?(?!\d)")


def _mk(y, mo, d, hh, mi, ss=0, us=0, tz=None) -> Optional[datetime]:
    try:
        return datetime(int(y), int(mo), int(d), int(hh), int(mi), int(ss), int(us), tzinfo=tz)
    except ValueError:
        return None


def local_to_utc(naive_fields: tuple, tz_name: str = OSLO) -> Optional[datetime]:
    dt = _mk(*naive_fields, tz=ZoneInfo(tz_name))
    return dt.astimezone(UTC) if dt else None


def parse_defaultno_name(name: str, tz_name: str = OSLO) -> Optional[NameTime]:
    """'202609251620_202609251703.mp4' -> 14:20Z..15:03Z (Europe/Oslo local -> UTC)."""
    m = _DEFAULTNO_RE.search(Path(name).name)
    if not m:
        return None
    a, b = m.groups()
    f = lambda s: (s[0:4], s[4:6], s[6:8], s[8:10], s[10:12])  # noqa: E731
    start, end = local_to_utc(f(a), tz_name), local_to_utc(f(b), tz_name)
    if start is None or end is None or end < start:
        return None
    return NameTime(start, end, "defaultno_local")


def _tz_from_suffix(sfx: Optional[str], default_tz: str):
    if not sfx:
        return ZoneInfo(default_tz), "local"
    if sfx in ("Z", "z", "UTC", "utc"):
        return UTC, "utc"
    sign = 1 if sfx[0] == "+" else -1
    digits = sfx[1:].replace(":", "")
    from datetime import timezone
    return timezone(sign * timedelta(hours=int(digits[:2]), minutes=int(digits[2:4] or 0))), "offset"


def parse_filename_time(path, tz_name: str = OSLO) -> Optional[NameTime]:
    """Derive a UTC start time from a file name (rules 2-4 of the module docstring)."""
    p = Path(path)
    nt = parse_defaultno_name(p.name, tz_name)
    if nt:
        return nt
    m = _ARCHIVE_RE.match(p.stem)
    if m and re.fullmatch(r"\d{8}", p.parent.name or ""):
        d, t = p.parent.name, m.group(1)
        dt = _mk(d[:4], d[4:6], d[6:8], t[:2], t[2:4], t[4:6], tz=UTC)
        if dt:
            return NameTime(dt, None, "hordewatch_archive_utc")
    m = _GEN_S_RE.search(p.stem)
    if m:
        y, mo, d, hh, mi, ss, frac, sfx = m.groups()
        tz, kind = _tz_from_suffix(sfx, tz_name)
        us = int((frac or "0")[:6].ljust(6, "0"))
        dt = _mk(y, mo, d, hh, mi, ss, us, tz=tz)
        if dt:
            return NameTime(dt.astimezone(UTC), None, f"name_{kind}")
    m = _GEN_M_RE.search(p.stem)
    if m:
        y, mo, d, hh, mi, sfx = m.groups()
        tz, kind = _tz_from_suffix(sfx, tz_name)
        dt = _mk(y, mo, d, hh, mi, tz=tz)
        if dt:
            return NameTime(dt.astimezone(UTC), None, f"name_min_{kind}")
    return None


# ============================================================================ inputs
@dataclass
class ReplayInput:
    kind: str                       # video | audio | images | hls
    path: str
    start: float = 0.0              # unix seconds (UTC) of t=0
    duration: Optional[float] = None
    stretch: float = 1.0
    rule: str = ""
    images: list = field(default_factory=list)   # [(unix, path)]
    probe: Optional[ProbeInfo] = None
    has_pdt: bool = False

    @property
    def end(self) -> float:
        return self.start + (self.duration or 0.0) * self.stretch

    @property
    def label(self) -> str:
        return os.path.basename(self.path.rstrip("/\\")) or self.path


def discover(paths) -> list:
    """Expand files/dirs to [(kind, path)] and [('images', dir, [files])] entries (stable order)."""
    out = []
    img_dirs: dict = {}
    hls_dirs = set()

    def add_file(f: Path):
        ext = f.suffix.lower()
        if ext == ".m3u8":
            out.append(("hls", str(f)))
            hls_dirs.add(str(f.parent.resolve()))
        elif ext in VIDEO_EXT:
            out.append(("video", str(f)))
        elif ext in AUDIO_EXT:
            out.append(("audio", str(f)))
        elif ext in IMAGE_EXT:
            key = str(f.parent)
            if key not in img_dirs:
                img_dirs[key] = []
                out.append(("images", key))
            img_dirs[key].append(str(f))

    for p in paths:
        p = Path(p).expanduser()
        if p.is_dir():
            for root, dirs, files in os.walk(p):
                dirs.sort()
                for name in sorted(files):
                    add_file(Path(root) / name)
        elif p.exists():
            add_file(p)
        else:
            log.warning("replay input not found: %s", p)
    res = []
    for kind, path in out:
        if kind == "video" and Path(path).suffix.lower() in TS_EXT and str(Path(path).parent.resolve()) in hls_dirs:
            continue   # segment of a playlist we replay as HLS
        if kind == "images":
            res.append(("images", path, sorted(img_dirs[path])))
        else:
            res.append((kind, path))
    return res


def probe_ts(path: str, exe: str, head_bytes: int = 4 << 20) -> ProbeInfo:
    """Probe an MPEG-TS file without letting ffmpeg see its SDT: header from a stripped head, duration from PTS."""
    import subprocess
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        head = f.read(head_bytes)
        f.seek(max(0, size - head_bytes))
        tail = f.read(head_bytes)
    hi, payload = ts_scan(head)
    try:
        r = subprocess.run([exe, "-hide_banner", "-nostdin", "-f", "mpegts", "-i", "pipe:0"], input=payload,
                           capture_output=True, timeout=30)
        info = parse_input_header(r.stderr.decode("utf-8", "replace"))
    except Exception:
        info = ProbeInfo()
    # duration from first/last PTS of the video (or audio) stream, wrap-aware
    last = _last_pts(tail)
    if hi.anchor90 is not None and last is not None:
        info.duration_s = (((last - hi.anchor90) % PTS_WRAP) / PTS_HZ) + (1.0 / (info.fps or 25.0))
    return info


def _last_pts(data: bytes) -> Optional[int]:
    """Largest (latest) PTS in a TS buffer, wrap-aware relative to the first one found."""
    from .hls import _pes_pts
    off = next((i for i in range(min(188, len(data))) if data[i] == 0x47), None)
    if off is None:
        return None
    n = (len(data) - off) // 188
    arr = np.frombuffer(data, dtype=np.uint8, count=n * 188, offset=off).reshape(n, 188)
    ref, best = None, None
    for k in np.nonzero((arr[:, 0] == 0x47) & ((arr[:, 1] & 0x40) != 0))[0]:
        afc = (arr[k, 3] >> 4) & 3
        st = 4 + ((1 + int(arr[k, 4])) if afc & 2 else 0)
        if not afc & 1 or st > 188 - 14:
            continue
        p = _pes_pts(arr[k, st:])
        if p is None:
            continue
        if ref is None:
            ref, best = p, 0
        d = ((p - ref + (PTS_WRAP >> 1)) % PTS_WRAP) - (PTS_WRAP >> 1)
        best = max(best, d)
    return None if ref is None else (ref + best) % PTS_WRAP


class _AnyEvent:
    """Read-only OR of several threading.Events (is_set/wait), e.g. global close + generator close."""

    def __init__(self, *events):
        self.events = events

    def is_set(self) -> bool:
        return any(e.is_set() for e in self.events)

    def wait(self, timeout: float) -> bool:
        end = time.monotonic() + timeout
        while not self.is_set():
            rem = end - time.monotonic()
            if rem <= 0:
                break
            time.sleep(min(0.05, rem))
        return self.is_set()


def _put(q: queue.Queue, item, *stops: threading.Event) -> bool:
    """Blocking put that gives up as soon as any stop event is set (backpressure without deadlock)."""
    while not any(e.is_set() for e in stops):
        try:
            q.put(item, timeout=0.2)
            return True
        except queue.Full:
            continue
    return False


# ============================================================================ source
class ReplaySource:
    """Offline source over recordings; see module docstring for inputs, timestamp rules and keys."""

    def __init__(self, source_cfg: dict, clock, cfg: Optional[dict] = None):
        s = dict(source_cfg or {})
        self.scfg = s
        self.cfg = cfg or {}
        self.clock = clock
        paths = s.get("files") or s.get("paths") or s.get("path") or s.get("url")
        if not paths:
            raise ValueError("replay source needs 'files' (list of files/dirs)")
        if isinstance(paths, (str, Path)):
            paths = [paths]
        g = lambda k, d: s.get(k) if s.get(k) is not None else d  # noqa: E731
        self.frame_interval_s = float(g("frame_interval_s", 5.0))
        self.audio_chunk_s = float(g("audio_chunk_s", 10.0))
        self.audio_sr = int(g("audio_sr", 16000))
        self.want_audio = bool(g("audio", True))
        self.want_video = bool(g("video", True))
        self.max_width = int(g("max_width", 1280))
        self.speed = float(g("speed", 0.0))
        self.max_pace_sleep_s = float(g("max_pace_sleep_s", 60.0))
        self.filename_tz = g("filename_tz", OSLO)
        self.image_interval_s = float(g("image_interval_s", self.frame_interval_s))
        self.align = g("defaultno_align", "start")
        self.min_partial_s = float(g("min_partial_audio_s", 1.0))
        self.use_clock_latency = bool(g("use_clock_latency", False))
        self._latency_cfg = float(g("latency_s", 0.0))
        self._exe = ffmpeg_exe(s.get("ffmpeg"))
        self.stats = StreamStats(mode="replay", source=", ".join(str(p) for p in paths)[:200])
        self.stats.update(ffmpeg=self._exe, decoder="replay", timing="file")
        self.stats.add_callback(publish_stats)
        register_stats(self.stats)
        archive_dir = s.get("archive_dir") or self.cfg.get("archive_dir")
        self.archiver = Archiver(archive_dir, g("archive_every_n_frames", 12), g("jpeg_quality", 90),
                                 g("archive_audio", False), enabled=g("archive", True))
        self._stop = threading.Event()
        self._hosts: set = set()
        self._hosts_lock = threading.Lock()
        self._pace_anchor = None
        self.inputs = self._build_inputs(paths)
        if not self.inputs:
            raise ValueError(f"replay: no usable inputs in {paths}")

    # ------------------------------------------------------------------ timing helpers
    @property
    def latency_s(self) -> float:
        return float(self.clock.latency_s) if self.use_clock_latency else self._latency_cfg

    def _explicit(self, path: str) -> Optional[datetime]:
        su = self.scfg.get("start_utc")
        if isinstance(su, dict):
            for k in (path, os.path.basename(path.rstrip("/\\")), str(Path(path).resolve())):
                if k in su:
                    return parse_iso(str(su[k]).replace("Z", "+00:00"))
        return None

    @staticmethod
    def _sidecar(path: str) -> Optional[datetime]:
        for sc in (path + ".json", str(Path(path).with_suffix(".json"))):
            if os.path.isfile(sc):
                try:
                    v = json.load(open(sc)).get("start_utc")
                    if v:
                        return parse_iso(str(v).replace("Z", "+00:00"))
                except Exception as e:
                    log.warning("bad sidecar %s: %s", sc, e)
        return None

    def _build_inputs(self, paths) -> list:
        chain_start = None
        su = self.scfg.get("start_utc")
        if isinstance(su, (str, datetime)):
            chain_start = (su if isinstance(su, datetime) else parse_iso(su.replace("Z", "+00:00"))).timestamp()
        inputs = []
        for entry in discover(paths):
            kind, path = entry[0], entry[1]
            try:
                if kind == "images":
                    inp, chain_start = self._images_input(path, entry[2], chain_start)
                elif kind == "hls":
                    inp, chain_start = self._hls_input(path, chain_start)
                else:
                    inp, chain_start = self._media_input(kind, path, chain_start)
            except Exception as e:
                log.warning("replay: skipping %s (%s: %s)", path, type(e).__name__, e)
                continue
            if inp is not None:
                log.info("replay input %s %s start=%s dur=%s rule=%s", inp.kind, inp.label,
                         datetime.fromtimestamp(inp.start, UTC).isoformat(), inp.duration, inp.rule)
                inputs.append(inp)
        inputs.sort(key=lambda i: i.start)
        return inputs

    def _media_input(self, kind, path, chain_start):
        ext = Path(path).suffix.lower()
        info = probe_ts(path, self._exe) if ext in TS_EXT else probe(path, self._exe)
        if not (info.has_video or info.has_audio):
            raise ValueError("no audio/video streams (" + info.raw[-200:].replace("\n", " ") + ")")
        if kind == "audio" or not info.has_video:
            kind = "audio" if info.has_audio else kind
        dur = info.duration_s
        stretch, rule = 1.0, ""
        start = self._explicit(path)
        if start is not None:
            rule = "explicit"
        else:
            nt = parse_filename_time(path, self.filename_tz)
            if nt is not None:
                start, rule = nt.start, nt.rule
                if nt.end is not None:
                    span = (nt.end - nt.start).total_seconds()
                    if dur and abs(dur - span) > max(5.0, 0.02 * span):
                        log.warning("%s: media duration %.1fs differs from name span %.0fs (align=%s)",
                                    os.path.basename(path), dur, span, self.align)
                    if self.align == "end" and dur:
                        start = nt.end - timedelta(seconds=dur)
                        rule += "_align_end"
                    elif self.align == "stretch" and dur:
                        stretch = span / dur
                        rule += "_stretch"
            else:
                start = self._sidecar(path)
                rule = "sidecar" if start else ""
        if start is None and chain_start is not None:
            start, rule = datetime.fromtimestamp(chain_start, UTC), "start_utc"
            chain_start += (dur or 0.0)
        if start is None:
            start = datetime.fromtimestamp(os.path.getmtime(path) - (dur or 0.0), UTC)
            rule = "mtime"
            log.warning("%s: no timestamp rule matched; using file mtime - duration (%s)", path, start.isoformat())
        return ReplayInput(kind=kind, path=path, start=start.timestamp(), duration=dur, stretch=stretch, rule=rule,
                           probe=info), chain_start

    def _images_input(self, d, files, chain_start):
        times = [parse_filename_time(f, self.filename_tz) for f in files]
        explicit = self._explicit(d)
        if explicit is None and all(t is not None for t in times):
            imgs = sorted((t.start.timestamp(), f) for t, f in zip(times, files))
            rule = times[0].rule
        else:
            if explicit is not None:
                base, rule = explicit.timestamp(), "explicit+interval"
            elif chain_start is not None:
                base, rule = chain_start, "start_utc+interval"
            elif any(times):
                i0 = next(i for i, t in enumerate(times) if t)
                base, rule = times[i0].start.timestamp() - i0 * self.image_interval_s, "name+interval"
            else:
                base, rule = os.path.getmtime(files[0]), "mtime+interval"
                log.warning("%s: image names carry no time; using mtime + %.1fs interval", d, self.image_interval_s)
            imgs = [(base + i * self.image_interval_s, f) for i, f in enumerate(files)]
            if rule.startswith("start_utc"):
                chain_start = base + len(files) * self.image_interval_s
        dur = (imgs[-1][0] - imgs[0][0]) + self.image_interval_s if imgs else 0.0
        return ReplayInput(kind="images", path=d, start=imgs[0][0], duration=dur, rule=rule, images=imgs), chain_start

    def _hls_input(self, path, chain_start):
        pl = parse_media_playlist(open(path, encoding="utf-8", errors="replace").read(), path)
        if not pl.segments:
            raise ValueError("empty playlist")
        dur = sum(s.duration for s in pl.segments)
        has_pdt = pl.segments[0].pdt is not None
        explicit = self._explicit(path)
        if has_pdt and explicit is None:
            start, rule = pl.segments[0].pdt.timestamp(), "hls_pdt"
        elif explicit is not None:
            start, rule, has_pdt = explicit.timestamp(), "explicit", False
        elif chain_start is not None:
            start, rule = chain_start, "start_utc"
            chain_start += dur
        else:
            start, rule = os.path.getmtime(path) - dur, "mtime"
        return ReplayInput(kind="hls", path=path, start=start, duration=dur, rule=rule, has_pdt=has_pdt), chain_start

    # ------------------------------------------------------------------ iteration
    def _clusters(self) -> list:
        clusters, cur, cur_end = [], [], None
        for inp in self.inputs:
            if cur and inp.start < cur_end - 1e-6:
                cur.append(inp)
                cur_end = max(cur_end, inp.end)
            else:
                if cur:
                    clusters.append(cur)
                cur, cur_end = [inp], inp.end
        if cur:
            clusters.append(cur)
        return clusters

    def __iter__(self):
        fidx = aidx = 0
        last_frame = None
        force_next = False
        self.stats.update(state="replaying")
        try:
            for cluster in self._clusters():
                self._pace_anchor = None
                gens = [self._iter_input(inp) for inp in cluster]
                merged = gens[0] if len(gens) == 1 else heapq.merge(*gens, key=lambda x: (x[0], x[1]))
                try:
                    for cap, _order, kind, payload, meta, inp in merged:
                        if self._stop.is_set():
                            return
                        if pop_archive_request():
                            if last_frame is not None and last_frame.path is None:
                                self.archiver.save_frame(last_frame)
                            force_next = True
                        self._pace(cap)
                        cap_dt = datetime.fromtimestamp(cap, UTC)
                        src = f"replay:{inp.label}"
                        if kind == "frame":
                            real_dt = cap_dt - timedelta(seconds=self.latency_s)
                            item = Frame(index=fidx, capture_ts=cap_dt, real_ts=real_dt, image=payload, source=src,
                                         path=meta.get("path"))
                            fidx += 1
                            self.archiver.maybe_save_frame(item, force=force_next)
                            force_next = False
                            last_frame = item
                            if self.stats.resolution != f"{item.w}x{item.h}":
                                self.stats.update(resolution=f"{item.w}x{item.h}")
                            self.stats.note_frame(cap_dt, real_dt)
                        else:
                            off = float(getattr(self.clock, "audio_offset_s", 0.0) or 0.0)
                            real_dt = cap_dt - timedelta(seconds=self.latency_s - off)
                            item = AudioChunk(index=aidx, capture_ts=cap_dt, real_ts=real_dt, samples=payload,
                                              sr=self.audio_sr, source=src)
                            aidx += 1
                            self.archiver.maybe_save_audio(item)
                            self.stats.note_audio(item.duration_s)
                        yield kind, item
                finally:
                    for gen in gens:
                        gen.close()
        finally:
            self.stats.update(state="closed" if self._stop.is_set() else "ended")
            self.stats.publish()

    def _pace(self, ts: float):
        if self.speed <= 0:
            return
        now = time.monotonic()
        if self._pace_anchor is None:
            self._pace_anchor = (now, ts)
            return
        w0, t0 = self._pace_anchor
        delay = w0 + (ts - t0) / self.speed - now
        if delay > self.max_pace_sleep_s:          # gap between recordings: jump, don't sleep
            self._pace_anchor = (now, ts)
            return
        if delay > 0:
            self._stop.wait(delay)

    def _iter_input(self, inp: ReplayInput):
        if inp.kind == "images":
            yield from self._iter_images(inp)
        else:
            yield from self._iter_decoded(inp)

    def _iter_images(self, inp: ReplayInput):
        import cv2
        for t, f in inp.images:
            if self._stop.is_set():
                return
            bgr = cv2.imread(f, cv2.IMREAD_COLOR)
            if bgr is None:
                log.warning("cannot read image %s", f)
                continue
            h, w = bgr.shape[:2]
            if w > self.max_width:
                nh = int(round(h * self.max_width / w / 2) * 2)
                bgr = cv2.resize(bgr, (self.max_width, nh), interpolation=cv2.INTER_AREA)
            yield t, 0, "frame", cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), {"path": f}, inp

    def _iter_decoded(self, inp: ReplayInput):
        q: queue.Queue = queue.Queue(maxsize=16)
        stop = self._stop
        lstop = threading.Event()        # set when this generator is closed early
        info = inp.probe
        is_hls = inp.kind == "hls"
        want_video = self.want_video and inp.kind != "audio" and (is_hls or bool(info and info.has_video))
        want_audio = self.want_audio and (is_hls or bool(info and info.has_audio))
        if not (want_video or want_audio):
            return
        ext = Path(inp.path).suffix.lower()
        tmap = PtsTimeMap() if is_hls else None
        if is_hls and inp.has_pdt:
            timing = PdtFileTiming(tmap)
        else:
            timing = FileTiming(inp.start, inp.stretch, 0.0, self.frame_interval_s)

        def emit(kind, cap, real, payload, meta):
            _put(q, (kind, cap, payload, meta), stop, lstop)

        feed = is_hls or ext in TS_EXT
        kw = dict(exe=self._exe, frame_interval_s=self.frame_interval_s, max_width=self.max_width,
                  want_video=want_video, want_audio=want_audio,
                  audio_transport=self.scfg.get("audio_transport", "auto"),
                  keyframes_only=bool(self.scfg.get("keyframes_only", False)),
                  threads=int(self.scfg.get("decoder_threads", 2) or 0),
                  copyts=bool(is_hls and inp.has_pdt))
        if feed:
            kw.update(input_url="pipe:0", input_args=["-f", "mpegts"], feed_stdin=True)
        else:
            kw.update(input_url=inp.path)
        done = threading.Event()
        host = DecoderHost(kw, timing, emit, self.audio_sr, self.audio_chunk_s, self.min_partial_s,
                           label=f"replay-{inp.label}",
                           on_session_end=None if feed else (lambda s: (_put(q, _END, stop, lstop), done.set())))
        with self._hosts_lock:
            self._hosts.add(host)
        feeder = None
        if feed:
            def run_feed():
                try:
                    if is_hls:
                        # recorded playlist: one pass; PDT gaps in the recording still land in stats.stall_events
                        tl = SegmentTimeline(self.stats, start_segments=None)
                        HLSFetcher(inp.path, self.stats, tl, tmap,
                                   on_segment=lambda seg, payload, entry, restart: host.write(payload, restart),
                                   stop=_AnyEvent(stop, lstop), poll_s=0.01, vod=True).run()
                    else:
                        host.start()
                        with open(inp.path, "rb") as f:
                            # align to the first sync byte once, so every 188*4096 read stays packet-aligned
                            head = f.read(188 * 3)
                            off = next((i for i in range(min(188, len(head)))
                                        if head[i] == 0x47 and (i + 188 >= len(head) or head[i + 188] == 0x47)), 0)
                            f.seek(off)
                            while not (stop.is_set() or lstop.is_set()):
                                buf = f.read(188 * 4096)
                                if not buf:
                                    break
                                _, payload = ts_scan(buf)
                                try:
                                    host.session.write(payload)
                                except (BrokenPipeError, OSError, ValueError, AttributeError):
                                    break
                except Exception as e:
                    log.warning("replay feed %s failed: %s", inp.label, e)
                finally:
                    if not lstop.is_set():
                        host.finish(timeout=120.0)
                    _put(q, _END, stop, lstop)
                    done.set()

            feeder = threading.Thread(target=run_feed, name=f"replay-feed-{inp.label}", daemon=True)
            feeder.start()
        else:
            host.start()
        heap: list = []
        seq = 0
        vw = -np.inf if want_video else np.inf
        aw = -np.inf if want_audio else np.inf
        try:
            while True:
                try:
                    item = q.get(timeout=0.5)
                except queue.Empty:
                    if stop.is_set():
                        return
                    continue
                if item is _END:
                    break
                kind, cap, payload, meta = item
                heapq.heappush(heap, (cap, 0 if kind == "frame" else 1, seq, kind, payload, meta))
                seq += 1
                if kind == "frame":
                    vw = cap
                else:
                    aw = cap + len(payload) / float(self.audio_sr)
                lim = min(vw, aw)
                while heap and (heap[0][0] <= lim or len(heap) > 64):
                    c, o, _, k, p, m = heapq.heappop(heap)
                    yield c, o, k, p, m, inp
            while heap:
                c, o, _, k, p, m = heapq.heappop(heap)
                yield c, o, k, p, m, inp
        finally:
            if not done.is_set():
                lstop.set()
                host.terminate()
            else:
                host.finish(timeout=5.0)
            if feeder is not None:
                feeder.join(5.0)
            with self._hosts_lock:
                self._hosts.discard(host)

    def close(self):
        self._stop.set()
        with self._hosts_lock:
            hosts = list(self._hosts)
        for h in hosts:
            h.terminate()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
