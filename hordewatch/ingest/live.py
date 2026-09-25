"""Live source: YouTube livestream -> timed frames and audio chunks, with reconnects.

Pipeline::

    resolve (yt-dlp -> streamlink -> direct URL)
       |- HLS (the normal case for YouTube live) -> "segments" mode:
       |     HLSFetcher polls the media playlist, downloads each new .ts segment, reads its first PTS,
       |     records PDT / arrival time / download time -> PtsTimeMap + StreamStats,
       |     strips SDT, writes the bytes to ONE persistent ffmpeg (stdin, -copyts).
       |     frame real_ts = EXT-X-PROGRAM-DATE-TIME of its segment + PTS offset - pdt_offset_s
       |     frame capture_ts = segment download time + PTS offset
       '- anything else (DASH, separate audio URL, fMP4 HLS, plain files) -> "direct" mode:
             ffmpeg reads the URL itself (with -reconnect), and a playlist monitor (for HLS) still
             records PDT/stall statistics. capture_ts = receive clock (running-min of wall - pts),
             real_ts = StreamClock.real_ts(capture_ts).

Latency. HLS PDT is the encoder or ingest wall clock, so ``capture_ts -
real_ts`` (published as ``stats.latency_pdt_s``) is the measured
glass-to-glass latency, apart from encoder buffering before the PDT stamp
(``pdt_offset_s``, which ADS-B or aircraft calibration can pin down).
Without PDT, real_ts falls back to the StreamClock latency (DB calibration or
config).

Stalls and reconnects. Playlist fetch errors, 403/404 (expired signed URLs,
about 6 h on googlevideo) and ENDLIST end the session. The supervisor then
re-resolves with exponential backoff and jitter. Before a signed URL expires
it re-resolves proactively without backoff. In segment mode the decoder and
PTS map survive re-resolution of the same video id, so no frames are lost.
All disruptions go into ``stats.stall_events`` (see stats.py).

Config keys (``source:`` section, all optional except url):
  url, frame_interval_s (5), audio_chunk_s (10), audio_sr (16000), audio (true),
  max_width (1280), max_height (720), mode (auto|segments|direct), ffmpeg (path),
  audio_transport (auto|fd|tcp), keyframes_only (false: true decodes only I-frames, roughly 10x less CPU,
  frame times then snap to the keyframe grid of about 2 s), realtime (false: -re for local test files),
  reconnect (true), max_reconnects (0 = unlimited), backoff_initial_s (2), backoff_max_s (300),
  live_start_segments (3), playlist_poll_s (auto = target/2), http_timeout_s (15),
  stall_factor (2.0), min_stall_s (6), gap_tolerance_s (0.75), stall_timeout_s (20, direct mode),
  restart_after_stall_s (120, direct mode), pdt_offset_s (0), real_ts_from_pdt (true),
  clock_from_pdt (false: if true, StreamClock.latency_s follows the measured PDT latency),
  pdt_monitor (true), queue_max (32), min_partial_audio_s (1.0), decoder_threads (2; 0 = all cores),
  archive (true), archive_dir (default: top-level archive_dir), archive_every_n_frames (12),
  jpeg_quality (90), archive_audio (false), archive_segments (false), archive_segments_max_gb (20),
  resolvers ([yt-dlp, streamlink]), ytdlp_format, cookies (cookie file for yt-dlp), direct (false).
"""
from __future__ import annotations

import logging
import random
import re
import shutil
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from ..types import UTC, AudioChunk, Frame
from . import pop_archive_request, publish_stats
from .archive import Archiver, SegmentArchiver
from .ffmpeg import ffmpeg_exe, mpegts_safe
from .hls import HLSFetcher, PlaylistGone, PtsTimeMap, SegmentTimeline, UnsupportedPlaylist
from .pipeline import DecoderHost, LiveTiming
from .stats import StreamStats

log = logging.getLogger("hordewatch.ingest.live")

_END = object()


# ============================================================================ resolution
class ResolveError(RuntimeError):
    pass


@dataclass
class ResolvedStream:
    url: str
    protocol: str = "http"              # hls | dash | http | file
    audio_url: Optional[str] = None
    headers: dict = field(default_factory=dict)
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    is_live: Optional[bool] = None
    release_ts: Optional[float] = None  # broadcast start (unix)
    expires_at: Optional[float] = None  # signed URL expiry (unix)
    format_id: Optional[str] = None
    resolver: str = "direct"
    key: str = ""                       # stream identity (video id) to keep state across re-resolves
    title: str = ""


def redact_url(u: str) -> str:
    """Keep YouTube page URLs; reduce signed CDN URLs to host + short path (they embed IP and signature)."""
    if not u.startswith(("http://", "https://")):
        return u
    p = urlparse(u)
    host = p.hostname or ""
    if host.endswith(("youtube.com", "youtu.be")):
        return u
    return f"{p.scheme}://{host}{p.path[:40]}{'...' if len(p.path) > 40 else ''}"


def video_key(url: str) -> str:
    """Stable identity of a stream across resolvers: the YouTube video id when recognisable, else the URL."""
    m = re.search(r"(?:[?&]v=|youtu\.be/|/live/|/embed/|/shorts/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else (url or "")


def expiry_from_url(u: str) -> Optional[float]:
    m = re.search(r"[/?&]expire[/=](\d{9,11})", u or "")
    return float(m.group(1)) if m else None


def _looks_direct(url: str, scfg: dict) -> bool:
    if scfg.get("direct"):
        return True
    if not url.startswith(("http://", "https://")):
        return True
    path = urlparse(url).path.lower()
    return path.endswith((".m3u8", ".mpd", ".mp4", ".ts", ".mkv", ".flv", ".webm", ".mov")) or "/hls_playlist/" in path


def _direct(url: str) -> ResolvedStream:
    path = urlparse(url).path.lower() if url.startswith(("http", "file:")) else url.lower()
    if path.endswith(".m3u8"):
        proto = "hls"
    elif path.endswith(".mpd"):
        proto = "dash"
    elif url.startswith(("http://", "https://")):
        proto = "hls" if "/hls_playlist/" in path else "http"
    else:
        proto = "file"
    return ResolvedStream(url=url, protocol=proto, resolver="direct", key=url, expires_at=expiry_from_url(url))


def stream_from_ytdlp_info(info: dict, page_url: str = "") -> ResolvedStream:
    """Turn a yt-dlp info dict (format already selected) into a ResolvedStream."""
    fmts = info.get("requested_formats") or []
    audio_url = None
    if len(fmts) >= 2:
        v = next((f for f in fmts if f.get("vcodec") not in (None, "none")), fmts[0])
        a = next((f for f in fmts if f is not v and f.get("acodec") not in (None, "none")), None)
        src, audio_url = v, (a or {}).get("url")
    else:
        src = info
    url = src.get("url")
    if not url:
        raise ResolveError("yt-dlp returned no stream URL")
    proto = str(src.get("protocol") or "")
    if "dash_segments" in proto or "f4m" in proto:
        raise ResolveError(f"yt-dlp picked protocol {proto!r} which ffmpeg cannot read directly")
    protocol = "hls" if "m3u8" in proto else ("dash" if "dash" in proto else "http")
    headers = src.get("http_headers") or info.get("http_headers") or {}
    return ResolvedStream(url=url, audio_url=audio_url, protocol=protocol, headers=dict(headers),
                          width=src.get("width"), height=src.get("height"), fps=src.get("fps"),
                          is_live=info.get("is_live"),
                          release_ts=info.get("release_timestamp") or (info.get("timestamp") if info.get("is_live") else None),
                          expires_at=expiry_from_url(url), format_id=str(info.get("format_id") or src.get("format_id")),
                          resolver="yt-dlp", key=str(info.get("id") or video_key(page_url)),
                          title=info.get("title") or "")


class _QuietYdlLogger:
    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        log.debug("yt-dlp: %s", msg)

    def error(self, msg):
        log.debug("yt-dlp: %s", msg)      # the raised DownloadError is logged by resolve_stream


def _resolve_ytdlp(url: str, max_h: int, scfg: dict) -> ResolvedStream:
    import yt_dlp
    fmt = scfg.get("ytdlp_format") or (
        f"best[height<={max_h}][protocol^=m3u8][vcodec!=none][acodec!=none]/"
        f"best[height<={max_h}][vcodec!=none][acodec!=none]/bestvideo[height<={max_h}]+bestaudio/best")
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True, "format": fmt,
            "socket_timeout": float(scfg.get("http_timeout_s", 15)), "logger": _QuietYdlLogger()}
    if scfg.get("cookies"):
        opts["cookiefile"] = scfg["cookies"]
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("live_status") in ("was_live", "post_live", "not_live") and scfg.get("require_live", False):
        raise ResolveError(f"stream is not live ({info.get('live_status')})")
    return stream_from_ytdlp_info(info, url)


def _resolve_streamlink(url: str, max_h: int, scfg: dict) -> ResolvedStream:
    # streamlink renames the global logging level names to lowercase on import; keep ours intact
    saved = (dict(logging._levelToName), dict(logging._nameToLevel))
    try:
        import streamlink
        sess = streamlink.Streamlink()
    finally:
        logging._levelToName.clear()
        logging._levelToName.update(saved[0])
        logging._nameToLevel.update(saved[1])
    streams = sess.streams(url)
    if not streams:
        raise ResolveError("streamlink: no streams (offline?)")

    def height(name):
        m = re.match(r"(\d+)p", name)
        return int(m.group(1)) if m else None

    cands = sorted((height(n), n) for n in streams if height(n) is not None and height(n) <= max_h)
    name = cands[-1][1] if cands else ("best" if "best" in streams else next(iter(streams)))
    st = streams[name]
    surl = getattr(st, "url", None)
    if not surl:
        raise ResolveError(f"streamlink stream {name} has no URL")
    try:
        ua = sess.http.headers.get("User-Agent")
    except Exception:
        ua = None
    proto = "hls" if (type(st).__name__.upper().startswith("HLS") or ".m3u8" in surl) else "http"
    return ResolvedStream(url=surl, protocol=proto, headers={"User-Agent": ua} if ua else {}, height=height(name),
                          resolver="streamlink", key=video_key(url), expires_at=expiry_from_url(surl))


def resolve_stream(url: str, scfg: Optional[dict] = None) -> ResolvedStream:
    """Resolve a page URL to a playable media URL (yt-dlp, then streamlink); direct URLs pass through."""
    scfg = scfg or {}
    if _looks_direct(url, scfg):
        return _direct(url)
    max_h = int(scfg.get("max_height", 720))
    errors = []
    for r in scfg.get("resolvers", ["yt-dlp", "streamlink"]):
        try:
            if r == "yt-dlp":
                return _resolve_ytdlp(url, max_h, scfg)
            if r == "streamlink":
                return _resolve_streamlink(url, max_h, scfg)
            errors.append(f"unknown resolver {r}")
        except ImportError as e:
            errors.append(f"{r} not installed ({e})")
        except Exception as e:
            errors.append(f"{r}: {type(e).__name__}: {str(e)[:200]}")
            log.warning("resolver %s failed: %s", r, e)
    raise ResolveError("; ".join(errors) or "no resolver")


# ============================================================================ queue
class ItemQueue:
    """Bounded queue that never blocks producers.

    When the consumer (runner plus analyzers, e.g. a slow VLM) falls behind
    live, the oldest *frame* is dropped (audio is kept: it is small and
    continuous) and ``stats.dropped_consumer`` is incremented."""

    def __init__(self, maxsize: int, stats: StreamStats):
        self.maxsize = max(2, int(maxsize))
        self.stats = stats
        self._d: deque = deque()
        self._cv = threading.Condition()

    def put(self, item):
        with self._cv:
            if len(self._d) >= self.maxsize:
                for i, it in enumerate(self._d):
                    if it is not _END and it[0] == "frame":
                        del self._d[i]
                        break
                else:
                    self._d.popleft()
                self.stats.incr("dropped_consumer")
            self._d.append(item)
            self._cv.notify()

    def put_end(self):
        with self._cv:
            self._d.append(_END)
            self._cv.notify_all()

    def get(self, timeout: float):
        with self._cv:
            if not self._d:
                self._cv.wait(timeout)
            return self._d.popleft() if self._d else None

    def __len__(self):
        return len(self._d)


def _dt(unix: float) -> datetime:
    return datetime.fromtimestamp(float(unix), UTC)


# ============================================================================ source
class LiveSource:
    """Iterable of ("frame", Frame) / ("audio", AudioChunk) from a live stream. See module docstring."""

    def __init__(self, source_cfg: dict, clock, cfg: Optional[dict] = None):
        s = dict(source_cfg or {})
        self.scfg = s
        self.cfg = cfg or {}
        self.clock = clock
        self.url = s.get("url")
        if not self.url:
            raise ValueError("live source needs 'url'")
        g = lambda k, d: s.get(k, d) if s.get(k) is not None else d  # noqa: E731
        self.frame_interval_s = float(g("frame_interval_s", 5.0))
        self.audio_chunk_s = float(g("audio_chunk_s", 10.0))
        self.audio_sr = int(g("audio_sr", 16000))
        self.want_audio = bool(g("audio", True))
        self.max_width = int(g("max_width", 1280))
        self.max_height = int(g("max_height", 720))
        self.mode = g("mode", "auto")
        self.reconnect = bool(g("reconnect", True))
        self.max_reconnects = int(g("max_reconnects", 0))
        self.backoff_initial_s = float(g("backoff_initial_s", 2.0))
        self.backoff_max_s = float(g("backoff_max_s", 300.0))
        self.live_start_segments = int(g("live_start_segments", 3))
        self.http_timeout_s = float(g("http_timeout_s", 15.0))
        self.stall_timeout_s = float(g("stall_timeout_s", 20.0))
        self.restart_after_stall_s = float(g("restart_after_stall_s", 120.0))
        self.pdt_offset_s = float(g("pdt_offset_s", 0.0))
        self.real_ts_from_pdt = bool(g("real_ts_from_pdt", True))
        self.clock_from_pdt = bool(g("clock_from_pdt", False))
        self.min_partial_s = float(g("min_partial_audio_s", 1.0))
        self._exe = ffmpeg_exe(s.get("ffmpeg"))
        self.stats = StreamStats(mode="live", source=redact_url(self.url))
        self.stats.update(ffmpeg=self._exe, pdt_offset_s=self.pdt_offset_s)
        self.stats.add_callback(publish_stats)
        if self.clock_from_pdt:
            self.stats.add_callback(self._clock_follow_pdt)
        archive_dir = s.get("archive_dir") or self.cfg.get("archive_dir")
        self.archiver = Archiver(archive_dir, g("archive_every_n_frames", 12), g("jpeg_quality", 90),
                                 g("archive_audio", False), enabled=g("archive", True))
        self.seg_archiver = (SegmentArchiver(Path(archive_dir) / "segments", g("archive_segments_max_gb", 20.0))
                             if s.get("archive_segments") and archive_dir else None)
        self._q = ItemQueue(int(g("queue_max", 32)), self.stats)
        self._stop = threading.Event()
        self._sup: Optional[threading.Thread] = None
        self._idx_lock = threading.Lock()
        self._fidx = 0
        self._aidx = 0
        self._items = 0
        self._host: Optional[DecoderHost] = None
        self._seg_state = None
        self._gap_since: Optional[float] = None

    # ------------------------------------------------------------------ public
    def __iter__(self):
        if self._sup is None:
            self._sup = threading.Thread(target=self._supervise, name="hordewatch-live", daemon=True)
            self._sup.start()
        last_frame = None
        force_next = False
        while True:
            if pop_archive_request():
                if last_frame is not None and last_frame.path is None:
                    self.archiver.save_frame(last_frame)
                force_next = True
            item = self._q.get(timeout=1.0)
            if item is None:
                if self._stop.is_set():
                    return
                continue
            if item is _END:
                self.stats.publish()
                return
            kind, obj = item
            if kind == "frame":
                self.archiver.maybe_save_frame(obj, force=force_next)
                force_next = False
                last_frame = obj
            else:
                self.archiver.maybe_save_audio(obj)
            yield kind, obj

    def close(self):
        self._stop.set()
        host = self._host
        if host is not None:
            host.terminate()
        if self._sup is not None and self._sup is not threading.current_thread():
            self._sup.join(10.0)
        self._q.put_end()
        self.stats.update(state="closed")
        self.stats.publish()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    # ------------------------------------------------------------------ items
    def _emit(self, kind, cap, real, payload, meta):
        if self._stop.is_set():
            return
        cap_dt, real_dt = _dt(cap), _dt(real)
        with self._idx_lock:
            if kind == "frame":
                idx, self._fidx = self._fidx, self._fidx + 1
            else:
                idx, self._aidx = self._aidx, self._aidx + 1
            self._items += 1
        if self._gap_since is not None:
            self.stats.add_stall("reconnect", start=self._gap_since, end=time.time(),
                                 detail="no data between sessions")
            self._gap_since = None
        if kind == "frame":
            item = Frame(index=idx, capture_ts=cap_dt, real_ts=real_dt, image=payload, source="live")
            res = f"{item.w}x{item.h}"
            if self.stats.resolution != res:
                self.stats.update(resolution=res)
            self.stats.note_frame(cap_dt, real_dt)
        else:
            item = AudioChunk(index=idx, capture_ts=cap_dt, real_ts=real_dt, samples=payload, sr=self.audio_sr,
                              source="live")
            self.stats.note_audio(item.duration_s)
        self._q.put((kind, item))

    def _sync_session_stats(self, sess):
        """Copy ffmpeg's -stats (speed, dropped frames) and input header (fps, bitrate) into StreamStats."""
        st = sess.stats
        upd = {}
        if st.get("drop") is not None:
            upd["dropped_decoder"] = int(st["drop"])
        if st.get("speed") is not None:
            upd["speed"] = st["speed"]
        info = sess.input_info
        if info is not None:
            if info.fps and not self.stats.fps_in:
                upd["fps_in"] = info.fps
            if info.bitrate_kbps and self.stats.bitrate_kbps is None:
                upd["bitrate_kbps"] = info.bitrate_kbps
        if upd:
            self.stats.update(**upd)

    def _clock_follow_pdt(self, snap):
        lat = snap.get("latency_pdt_s")
        if lat is not None and snap.get("timing") == "pdt":
            self.clock.latency_s = float(lat)      # capture - real; real already includes pdt_offset_s

    # ------------------------------------------------------------------ supervisor
    def _supervise(self):
        attempt = 0
        n_retries = 0
        try:
            while not self._stop.is_set():
                before = self._items
                outcome = "error"
                try:
                    self.stats.update(state="resolving")
                    res = resolve_stream(self.url, self.scfg)
                    log.info("resolved %s via %s: %s %s (live=%s)", redact_url(self.url), res.resolver,
                             res.protocol, redact_url(res.url), res.is_live)
                    self.stats.update(resolver=res.resolver, format_id=res.format_id, stream_start=res.release_ts)
                    if res.width and res.height:
                        self.stats.update(resolution=f"{res.width}x{res.height}")
                    if res.fps:
                        self.stats.update(fps_in=res.fps)
                    self.stats.incr("sessions")
                    outcome = self._run(res)
                except Exception as e:
                    log.warning("live session failed: %s: %s", type(e).__name__, e)
                    self.stats.update(last_error=f"{type(e).__name__}: {e}"[:300], state="error")
                if self._stop.is_set():
                    break
                if self._gap_since is None:
                    self._gap_since = time.time()
                if outcome == "expiring":
                    attempt = 0
                    continue
                if self._items > before:
                    attempt = 0
                if not self.reconnect:
                    break
                n_retries += 1
                if self.max_reconnects and n_retries > self.max_reconnects:
                    log.warning("giving up after %d reconnects", self.max_reconnects)
                    break
                delay = min(self.backoff_max_s, self.backoff_initial_s * (2 ** attempt)) * random.uniform(0.8, 1.2)
                attempt += 1
                self.stats.incr("reconnects")
                self.stats.update(state="backoff")
                log.info("reconnecting in %.1f s (outcome=%s)", delay, outcome)
                self._stop.wait(delay)
        finally:
            host = self._host
            if host is not None:
                host.finish(timeout=2.0 if self._stop.is_set() else 15.0)
                self._host = None
            if not self._stop.is_set():
                self.stats.update(state="ended")
            self._q.put_end()

    def _run(self, res: ResolvedStream) -> str:
        mode = self.mode
        if mode == "auto":
            mode = "segments" if (res.protocol == "hls" and not res.audio_url) else "direct"
        if mode == "segments" and res.protocol != "hls":
            mode = "direct"
        self.stats.update(decoder=mode)
        if mode == "segments":
            try:
                return self._run_segments(res)
            except UnsupportedPlaylist as e:
                log.warning("segment mode not possible (%s): falling back to ffmpeg-direct", e)
                self.stats.update(decoder="direct")
        return self._run_direct(res)

    def _session_kwargs(self, **kw) -> dict:
        s = self.scfg
        base = dict(exe=self._exe, frame_interval_s=self.frame_interval_s, max_width=self.max_width,
                    want_audio=self.want_audio, audio_transport=s.get("audio_transport", "auto"),
                    keyframes_only=bool(s.get("keyframes_only", False)),
                    threads=int(s.get("decoder_threads", 2) or 0))
        base.update(kw)
        return base

    def _timeline(self, res) -> SegmentTimeline:
        s = self.scfg
        return SegmentTimeline(self.stats, stall_factor=float(s.get("stall_factor", 2.0)),
                               min_stall_s=float(s.get("min_stall_s", 6.0)),
                               gap_tolerance_s=float(s.get("gap_tolerance_s", 0.75)),
                               start_segments=self.live_start_segments, stream_start=res.release_ts)

    def _run_segments(self, res: ResolvedStream) -> str:
        if self._seg_state is None or self._seg_state[0] != res.key:
            if self._host is not None:
                self._host.finish(timeout=5.0)
                self._host = None
            self._seg_state = (res.key, self._timeline(res), PtsTimeMap())
        _, timeline, tmap = self._seg_state
        if self._host is None:
            timing = LiveTiming(self.clock, tmap, self.pdt_offset_s, self.real_ts_from_pdt, self.stats)
            self._host = DecoderHost(self._session_kwargs(input_url="pipe:0", input_args=["-f", "mpegts"],
                                                          feed_stdin=True, copyts=True),
                                     timing, self._emit, self.audio_sr, self.audio_chunk_s, self.min_partial_s,
                                     label="live-seg")
        host = self._host

        def on_segment(seg, payload, entry, restart):
            host.write(payload, restart=restart)
            if host.session is not None:
                self._sync_session_stats(host.session)

        fetcher = HLSFetcher(res.url, self.stats, timeline, tmap, on_segment=on_segment, stop=self._stop,
                             headers=res.headers, poll_s=self.scfg.get("playlist_poll_s"),
                             timeout=self.http_timeout_s, expires_at=res.expires_at, max_height=self.max_height,
                             segment_archiver=self.seg_archiver)
        try:
            fetcher.run()
        except PlaylistGone as e:
            log.warning("playlist gone: %s", e)
            self.stats.update(last_error=str(e)[:300])
            return "gone"
        finally:
            if fetcher.ended or self._stop.is_set():
                self._host = None
                host.finish(timeout=2.0 if self._stop.is_set() else 20.0)
        if fetcher.ended:
            return "ended"
        return "expiring" if fetcher.expiring else "stopped"

    def _http_args(self, url: str, headers: dict) -> list:
        if not url.startswith(("http://", "https://")):
            return []
        a = ["-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "10",
             "-rw_timeout", str(int(self.http_timeout_s * 1e6))]
        h = dict(headers or {})
        ua = h.pop("User-Agent", None) or h.pop("user-agent", None)
        if ua:
            a += ["-user_agent", ua]
        extra = "".join(f"{k}: {v}\r\n" for k, v in h.items() if k.lower() not in ("accept-encoding",))
        if extra:
            a += ["-headers", extra]
        return a

    def _run_direct(self, res: ResolvedStream) -> str:
        exe = self._exe
        if res.protocol == "hls" and not mpegts_safe(exe):
            alt = shutil.which("ffmpeg")
            if alt and alt != exe and mpegts_safe(alt):
                exe = alt
            else:
                log.error("this ffmpeg build crashes on MPEG-TS SDT tables and HLS-direct needs it; use mode: segments "
                          "or set source.ffmpeg to a system ffmpeg")
        input_args = self._http_args(res.url, res.headers)
        if res.protocol == "hls" and res.is_live is not False and not Path(res.url).exists():
            input_args += ["-live_start_index", str(-self.live_start_segments)]
        audio_args = self._http_args(res.audio_url, res.headers) if res.audio_url else []
        timing = LiveTiming(self.clock, None, self.pdt_offset_s, False, self.stats)
        host = DecoderHost(self._session_kwargs(exe=exe, input_url=res.url, input_args=input_args,
                                                audio_input=res.audio_url, audio_input_args=audio_args,
                                                copyts=False, realtime=bool(self.scfg.get("realtime", False))),
                           timing, self._emit, self.audio_sr, self.audio_chunk_s, self.min_partial_s,
                           label="live-direct")
        self._host = host
        mon_stop = threading.Event()
        mon_thread = None
        if res.protocol == "hls" and self.scfg.get("pdt_monitor", True):
            mon = HLSFetcher(res.url, self.stats, self._timeline(res), download=False, stop=mon_stop,
                             headers=res.headers, poll_s=self.scfg.get("playlist_poll_s"), timeout=self.http_timeout_s,
                             max_height=self.max_height)

            def _mon():
                try:
                    mon.run()
                except Exception as e:
                    log.info("playlist monitor stopped: %s", e)

            mon_thread = threading.Thread(target=_mon, name="hordewatch-pdt-monitor", daemon=True)
            mon_thread.start()
        sess = host.start()
        stall_since = None
        outcome = "eof"
        try:
            while not self._stop.is_set():
                if sess.wait_finished(0.5):
                    break
                now = time.time()
                last = sess.last_output_wall or sess.started_wall
                gap = now - last
                if stall_since is None and gap > self.stall_timeout_s:
                    stall_since = last
                    self.stats.update(state="stalled", current_stall_since=last)
                elif stall_since is not None and gap < self.stall_timeout_s:
                    self.stats.add_stall("decoder", start=stall_since, end=sess.last_output_wall or now,
                                         detail="no ffmpeg output")
                    self.stats.update(state="streaming", current_stall_since=None)
                    stall_since = None
                if gap > self.restart_after_stall_s:
                    log.warning("no output for %.0f s: restarting ffmpeg", gap)
                    outcome = "stalled"
                    break
                if res.expires_at and now > res.expires_at - 600:
                    outcome = "expiring"
                    break
                self._sync_session_stats(sess)
            if sess.finished and sess.returncode not in (0, None):
                msg = f"ffmpeg exit {sess.returncode}: {sess.error_summary()}"
                log.warning(msg)
                self.stats.update(last_error=msg[:300])
                if host.adapt_to_error(sess):
                    self.want_audio = host.session_kwargs.get("want_audio", self.want_audio)
            self._sync_session_stats(sess)
        finally:
            if stall_since is not None:
                self.stats.add_stall("decoder", start=stall_since, end=time.time(), detail="session ended while stalled")
            if sess.finished:
                host.finish(timeout=2.0)
            else:
                host.terminate()
            self._host = None
            mon_stop.set()
            if mon_thread is not None:
                mon_thread.join(2.0)
        return outcome
