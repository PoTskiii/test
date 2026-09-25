"""One ffmpeg process per stream: raw RGB frames plus 16 kHz mono PCM.

Process layout (``DecodeSession``)
----------------------------------
::

    input (URL | file | stdin <- HLS segment feeder)
      |- map 0:v -> select(one frame per frame_interval_s grid cell) -> scale -> showinfo -> rawvideo rgb24 -> stdout
      |- map 0:a -> aresample(async=1, 16 kHz) -> mono s16 -> asetnsamples(1 s) -> ashowinfo -> s16le -> AUDIO PIPE
      '- stderr: showinfo/ashowinfo lines (per-frame PTS and size), -stats lines (speed, drops), stream headers

Why one process with two outputs (not two processes): both outputs share one
demuxer and one clock, so audio and video PTS are directly comparable. The
network is read once, and a single failure restarts both. The audio goes to
a second pipe:

* POSIX: an ``os.pipe()`` whose write end is inherited by ffmpeg via
  ``pass_fds`` and addressed as ``pipe:<fd>``. This is the default.
* Windows (no ``pass_fds``): ffmpeg connects to a loopback TCP listener that
  we open (``tcp://127.0.0.1:<port>``). It is also selectable on POSIX
  (``audio_transport: tcp``).

Both pipes are drained by dedicated threads, so ffmpeg can never deadlock
writing one output while we block on the other. The same goes for stderr.

Timestamps: raw pipes carry no timestamps, so ``showinfo`` logs each emitted
frame's ``n``, ``pts_time`` and size ``s:WxH``. The video reader waits for
that line before reading frame ``n``, so it always knows the exact byte size,
even if the resolution changes mid-stream. ``aresample=async=1`` fills gaps
with silence and trims overlaps, keeping audio sample count linear in PTS.
``asetnsamples`` makes 1 s audio frames whose PTS ``ashowinfo`` logs once per
second, so ``audio_pts_at(sample_index)`` is exact. Lines from the video and
audio filter threads can interleave inside one stderr line, so the parser
splits every line at ``n:`` fragments.

Frame selection: ``select`` keeps the first frame of each
``floor(t / frame_interval_s)`` cell (``not(eq(...))``), so the grid is aligned
to absolute PTS, does not drift, and survives backwards PTS jumps. This is
unlike ``gte(t - prev_selected_t, I)``, which never fires again after a jump
backwards.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

log = logging.getLogger("hordewatch.ingest.ffmpeg")

_VERSION_CACHE: dict = {}


def ffmpeg_exe(preferred: Optional[str] = None) -> str:
    """Pick the ffmpeg binary.

    Order: explicit config path, the ``HORDEWATCH_FFMPEG`` env var, then the
    imageio-ffmpeg static binary (a known, recent build), then ``ffmpeg`` on
    PATH."""
    for cand in (preferred, os.environ.get("HORDEWATCH_FFMPEG")):
        if cand and (os.path.exists(cand) or shutil.which(cand)):
            return shutil.which(cand) or cand
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    p = shutil.which("ffmpeg")
    if p:
        return p
    raise RuntimeError("ffmpeg not found: pip install imageio-ffmpeg or install ffmpeg, or set source.ffmpeg")


def ffmpeg_version(exe: str) -> tuple:
    if exe in _VERSION_CACHE:
        return _VERSION_CACHE[exe]
    ver = (0, 0)
    try:
        out = subprocess.run([exe, "-hide_banner", "-version"], capture_output=True, timeout=10).stdout.decode(
            "utf-8", "replace")
        m = re.search(r"ffmpeg version n?(\d+)\.(\d+)", out)
        if m:
            ver = (int(m.group(1)), int(m.group(2)))
    except Exception:
        pass
    _VERSION_CACHE[exe] = ver
    return ver


@dataclass
class ProbeInfo:
    duration_s: Optional[float] = None
    start_s: Optional[float] = None
    bitrate_kbps: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    has_video: bool = False
    has_audio: bool = False
    audio_sr: Optional[int] = None
    audio_channels: Optional[str] = None
    raw: str = ""


_DUR_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
_START_RE = re.compile(r"start:\s*(-?\d+(?:\.\d+)?)")
_BR_RE = re.compile(r"bitrate:\s*(\d+)\s*kb/s")
_VSTREAM_RE = re.compile(r"Stream #\d+:\d+.*?: Video: .*?, (\d{2,5})x(\d{2,5})[ ,\[]")
_FPS_RE = re.compile(r"(\d+(?:\.\d+)?) fps")
_ASTREAM_RE = re.compile(r"Stream #\d+:\d+.*?: Audio: .*?, (\d+) Hz, ([^,]+)")


def parse_input_header(text: str) -> ProbeInfo:
    """Parse the 'Input #0' part of ffmpeg's stderr."""
    info = ProbeInfo(raw=text[-4000:])
    head = text.split("Output #", 1)[0] if "Output #" in text else text
    head = head.split("Stream mapping:", 1)[0]
    m = _DUR_RE.search(head)
    if m:
        info.duration_s = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    m = _START_RE.search(head)
    if m:
        info.start_s = float(m.group(1))
    m = _BR_RE.search(head)
    if m:
        info.bitrate_kbps = float(m.group(1))
    for line in head.splitlines():
        if ": Video:" in line and not info.has_video and "attached pic" not in line:
            mv = _VSTREAM_RE.search(line)
            if mv:
                info.has_video = True
                info.width, info.height = int(mv.group(1)), int(mv.group(2))
                mf = _FPS_RE.search(line)
                info.fps = float(mf.group(1)) if mf else None
        elif ": Audio:" in line and not info.has_audio:
            ma = _ASTREAM_RE.search(line)
            info.has_audio = True
            if ma:
                info.audio_sr = int(ma.group(1))
                info.audio_channels = ma.group(2).strip()
    return info


def probe(path: str, exe: Optional[str] = None, timeout: float = 30.0, input_args=()) -> ProbeInfo:
    """Probe a local file/URL with ``ffmpeg -i`` (there is no ffprobe in imageio-ffmpeg)."""
    exe = exe or ffmpeg_exe()
    try:
        r = subprocess.run([exe, "-hide_banner", "-nostdin", *input_args, "-i", path], capture_output=True,
                           timeout=timeout)
        return parse_input_header(r.stderr.decode("utf-8", "replace"))
    except subprocess.TimeoutExpired:
        return ProbeInfo()


_TS_SAFE_CACHE: dict = {}


def mpegts_safe(exe: str) -> bool:
    """Can this ffmpeg demux an MPEG-TS stream that carries an SDT table?

    The imageio-ffmpeg 7.0.2 static build segfaults in the SDT parser
    (static glibc iconv). Only ffmpeg-direct HLS mode needs this; segment mode
    strips the SDT. Cached per binary."""
    if exe in _TS_SAFE_CACHE:
        return _TS_SAFE_CACHE[exe]
    ok = True
    try:
        gen = subprocess.run([exe, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                              "testsrc=size=64x48:rate=5:duration=0.4", "-c:v", "mpeg2video", "-f", "mpegts",
                              "pipe:1"], capture_output=True, timeout=30)
        if gen.returncode == 0 and gen.stdout:
            r = subprocess.run([exe, "-hide_banner", "-loglevel", "error", "-f", "mpegts", "-i", "pipe:0",
                                "-f", "null", "-"], input=gen.stdout, capture_output=True, timeout=30)
            ok = r.returncode == 0
    except Exception:
        ok = True   # cannot tell; do not block
    _TS_SAFE_CACHE[exe] = ok
    return ok


def fmt_seconds(x: float) -> str:
    return f"{x:.6f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------------------- stderr parsing
# no \b: interleaved log output can glue a fragment onto a hex dump ("...3136n:1 pts:16000 ...")
_FRAG_SPLIT = re.compile(r"(?=n:\s*\d+\s+pts:)")
_FRAG_RE = re.compile(r"^n:\s*(\d+)\s+pts:\s*(-?\d+|NOPTS)\s+pts_time:\s*(-?[\d.eE+-]+|NOPTS)")
_SIZE_RE = re.compile(r"\bs:(\d+)x(\d+)")
_OUT_VID_RE = re.compile(r"Video: rawvideo.*?, (\d{2,5})x(\d{2,5})[ ,\[]")
_STATS_RE = {k: re.compile(p) for k, p in {
    "speed": r"speed=\s*([\d.]+)x", "drop": r"drop=\s*(\d+)", "dup": r"dup=\s*(\d+)",
    "frame": r"frame=\s*(\d+)", "time": r"time=\s*(-?[\d:.]+)"}.items()}


class _PtsBook:
    """n -> (pts_s, w, h) with blocking lookup."""

    def __init__(self):
        self._d: dict = {}
        self._cv = threading.Condition()
        self.closed = False
        self.max_n = -1

    def put(self, n, val):
        with self._cv:
            self._d[n] = val
            self.max_n = max(self.max_n, n)
            if len(self._d) > 4096:
                for k in sorted(self._d)[:1024]:
                    del self._d[k]
            self._cv.notify_all()

    def get(self, n, timeout: float):
        """Wait for entry n. Lines arrive strictly in order, so once a later n is present a missing
        entry was lost to log interleaving: return None at once instead of waiting."""
        end = time.monotonic() + timeout
        with self._cv:
            while n not in self._d and not self.closed and self.max_n < n:
                rem = end - time.monotonic()
                if rem <= 0:
                    break
                self._cv.wait(min(rem, 0.25))
            return self._d.get(n)

    def peek(self, n):
        with self._cv:
            return self._d.get(n)

    def nearest(self, n):
        with self._cv:
            if not self._d:
                return None, None
            k = min(self._d, key=lambda k: abs(k - n))
            return k, self._d[k]

    def close(self):
        with self._cv:
            self.closed = True
            self._cv.notify_all()


def _read_exact(f, n: int) -> Optional[bytearray]:
    """Read exactly n bytes into a bytearray (so numpy views on it are writable); None on EOF."""
    buf = bytearray(n)
    view = memoryview(buf)
    got = 0
    while got < n:
        k = f.readinto(view[got:])
        if not k:
            return None
        got += k
    return buf


class DecodeSession:
    """Run one ffmpeg decode process; deliver frames/audio through callbacks.

    Callbacks (called from reader threads):
      ``on_frame(n, pts_s | None, rgb_uint8_HxWx3, wall_unix)``
      ``on_audio(int16_samples, first_sample_index, wall_unix)``: use
      ``audio_pts_at(first_sample_index)`` for its PTS
      ``on_end(session)`` once, when every reader has finished.
    """

    def __init__(self, input_url: str, *, exe: Optional[str] = None, input_args=(), audio_input: Optional[str] = None,
                 audio_input_args=(), frame_interval_s: float = 5.0, max_width: int = 1280, want_video: bool = True,
                 want_audio: bool = True, audio_sr: int = 16000, copyts: bool = False, realtime: bool = False,
                 keyframes_only: bool = False, audio_transport: str = "auto", feed_stdin: bool = False,
                 on_frame: Optional[Callable] = None, on_audio: Optional[Callable] = None,
                 on_end: Optional[Callable] = None, label: str = "", info_timeout_s: float = 20.0,
                 threads: int = 2):
        self.exe = exe or ffmpeg_exe()
        self.input_url = input_url
        self.input_args = list(input_args)
        self.audio_input = audio_input
        self.audio_input_args = list(audio_input_args)
        self.frame_interval_s = float(frame_interval_s)
        self.max_width = int(max_width)
        self.want_video = want_video
        self.want_audio = want_audio
        self.audio_sr = int(audio_sr)
        self.copyts = copyts
        self.realtime = realtime
        self.keyframes_only = keyframes_only
        self.feed_stdin = feed_stdin
        self.on_frame = on_frame
        self.on_audio = on_audio
        self.on_end = on_end
        self.label = label
        self.info_timeout_s = info_timeout_s
        self.threads = int(threads or 0)          # decoder threads (0 = ffmpeg auto = all cores)
        if audio_transport == "auto":
            audio_transport = "fd" if os.name == "posix" else "tcp"
        self.audio_transport = audio_transport
        self.proc: Optional[subprocess.Popen] = None
        self.vbook = _PtsBook()
        self.abook = _PtsBook()
        self.stderr_tail: deque = deque(maxlen=80)
        self.header_text = []
        self.input_info: Optional[ProbeInfo] = None
        self.stats: dict = {}
        self.frames = 0
        self.audio_samples = 0
        self.last_output_wall: Optional[float] = None
        self.started_wall: Optional[float] = None
        self._threads: list = []
        self._audio_fd = None
        self._audio_sock = None
        self._stopping = False
        self._end_lock = threading.Lock()
        self._ended = False
        self._done_event = threading.Event()
        self._audio_close_lock = threading.Lock()
        self._readers_left = 0
        self.out_dims: Optional[tuple] = None
        self._dims_event = threading.Event()

    # ------------------------------------------------------------------ command
    def _vf(self) -> str:
        i = fmt_seconds(self.frame_interval_s)
        sel = f"select='if(isnan(prev_selected_t),1,not(eq(floor(t/{i}),floor(prev_selected_t/{i}))))'"
        mw = self.max_width - (self.max_width % 2)
        scale = f"scale=w='min({mw},iw)':h=-2:flags=area"
        return f"{sel},{scale},showinfo=checksum=0"

    def _af(self) -> str:
        sr = self.audio_sr
        return (f"aresample=async=1:osr={sr},aformat=sample_fmts=s16:channel_layouts=mono,"
                f"asetnsamples=n={sr}:p=0,ashowinfo")

    def build_cmd(self, audio_target: str) -> list:
        ver = ffmpeg_version(self.exe)
        cmd = [self.exe, "-hide_banner", "-nostdin", "-loglevel", "info", "-stats", "-stats_period", "5"]
        if self.copyts:
            cmd += ["-copyts"]
        if self.keyframes_only and self.want_video:
            cmd += ["-skip_frame", "nokey"]
        if self.realtime:
            cmd += ["-re"]
        if self.threads > 0:
            cmd += ["-threads", str(self.threads)]     # leave CPU for the analyzers (OCR, VLM, ...)
        cmd += [*self.input_args, "-i", "pipe:0" if self.feed_stdin else self.input_url]
        audio_src = "0:a:0"
        if self.audio_input and self.want_audio:
            cmd += [*self.audio_input_args, "-i", self.audio_input]
            audio_src = "1:a:0"
        if self.want_video:
            passthrough = ["-fps_mode", "passthrough"] if ver >= (5, 1) or ver == (0, 0) else ["-vsync", "passthrough"]
            cmd += ["-map", "0:v:0", "-filter:v", self._vf(), *passthrough, "-an", "-sn", "-dn",
                    "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]
        if self.want_audio:
            cmd += ["-map", audio_src, "-filter:a", self._af(), "-vn", "-sn", "-dn",
                    "-f", "s16le", "-flush_packets", "1", audio_target]
        return cmd

    # ------------------------------------------------------------------ lifecycle
    def start(self):
        if not (self.want_video or self.want_audio):
            raise ValueError("DecodeSession needs video or audio")
        pass_fds = ()
        audio_target = None
        rfd = None
        if self.want_audio:
            if self.audio_transport == "fd":
                rfd, wfd = os.pipe()
                pass_fds = (wfd,)
                audio_target = f"pipe:{wfd}"
            else:
                srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                srv.bind(("127.0.0.1", 0))
                srv.listen(1)
                srv.settimeout(1.0)
                self._audio_sock = srv
                audio_target = f"tcp://127.0.0.1:{srv.getsockname()[1]}"
        cmd = self.build_cmd(audio_target)
        log.debug("ffmpeg %s: %s", self.label, " ".join(cmd))
        kw = {}
        if os.name == "nt":
            kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE if self.feed_stdin else subprocess.DEVNULL,
                                         stdout=subprocess.PIPE if self.want_video else subprocess.DEVNULL,
                                         stderr=subprocess.PIPE, pass_fds=pass_fds, bufsize=0, **kw)
        except Exception:
            for fd in (*pass_fds, rfd):
                if fd is not None:
                    os.close(fd)
            self._close_audio()
            raise
        self.started_wall = time.time()
        if pass_fds:
            os.close(pass_fds[0])       # the child holds the write end now; EOF propagates when it exits
            self._audio_fd = rfd
        self._spawn(self._stderr_loop, "stderr", count=False)
        if self.want_video:
            self._spawn(self._video_loop, "video")
        if self.want_audio:
            self._spawn(self._audio_loop, "audio")
        return self

    def _spawn(self, fn, name, count=True):
        if count:
            self._readers_left += 1
        t = threading.Thread(target=self._guard, args=(fn, count), name=f"ffmpeg-{name}-{self.label}", daemon=True)
        self._threads.append(t)
        t.start()

    def _guard(self, fn, count):
        try:
            fn()
        except Exception as e:  # pragma: no cover - defensive
            if not self._stopping:
                log.exception("ffmpeg reader %s failed: %s", fn.__name__, e)
        finally:
            if count:
                with self._end_lock:
                    self._readers_left -= 1
                    done = self._readers_left == 0 and not self._ended
                    if done:
                        self._ended = True
                if done:
                    self.vbook.close()
                    self.abook.close()
                    if self.on_end:
                        try:
                            self.on_end(self)
                        except Exception:
                            log.exception("on_end callback failed")
                    self._done_event.set()

    def write(self, data: bytes):
        """Feed input bytes (feed_stdin mode). Raises BrokenPipeError if ffmpeg died."""
        if self.proc is None or self.proc.stdin is None:
            raise BrokenPipeError("ffmpeg stdin not open")
        self.proc.stdin.write(data)

    def close_stdin(self):
        if self.proc is not None and self.proc.stdin is not None:
            try:
                self.proc.stdin.close()
            except Exception:
                pass

    @property
    def alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    @property
    def finished(self) -> bool:
        """True once every reader finished and on_end (final partial audio chunk) has run."""
        return self._done_event.is_set()

    def wait_finished(self, timeout: Optional[float] = None) -> bool:
        return self._done_event.wait(timeout)

    def wait(self, timeout: Optional[float] = None) -> bool:
        """Wait for ffmpeg exit and reader completion. Returns True if finished."""
        end = None if timeout is None else time.monotonic() + timeout
        for t in self._threads:
            rem = None if end is None else max(0.0, end - time.monotonic())
            t.join(rem)
        if self.proc is not None:
            try:
                self.proc.wait(None if end is None else max(0.01, end - time.monotonic()))
            except subprocess.TimeoutExpired:
                return False
        return all(not t.is_alive() for t in self._threads)

    def terminate(self, grace_s: float = 3.0):
        self._stopping = True
        self.close_stdin()
        p = self.proc
        if p is not None and p.poll() is None:
            try:
                p.terminate()
                p.wait(grace_s)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        for t in self._threads:
            t.join(2.0)
        self._close_audio()
        self.vbook.close()
        self.abook.close()

    def _close_audio(self):
        # locked: the reader thread and terminate() may both get here; a double os.close could hit a reused fd
        with self._audio_close_lock:
            fd, self._audio_fd = self._audio_fd, None
            sock, self._audio_sock = self._audio_sock, None
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

    @property
    def returncode(self):
        return None if self.proc is None else self.proc.poll()

    # ------------------------------------------------------------------ PTS helpers
    def audio_pts_at(self, sample_index: int, timeout: float = 2.0) -> Optional[float]:
        """PTS (s) of audio sample ``sample_index`` of this session."""
        j = sample_index // self.audio_sr
        v = self.abook.get(j, timeout)
        if v is None:
            k, v = self.abook.nearest(j)
            if v is None:
                return None
            return v[0] + (sample_index - k * self.audio_sr) / self.audio_sr
        return v[0] + (sample_index - j * self.audio_sr) / self.audio_sr

    # ------------------------------------------------------------------ readers
    def _stderr_loop(self):
        f = self.proc.stderr
        buf = b""
        in_header = True
        header = []
        seen_output0 = False
        while True:
            chunk = f.read(65536)   # raw FileIO (bufsize=0): returns what is available
            if not chunk:
                break
            buf += chunk
            parts = re.split(rb"[\r\n]", buf)
            buf = parts.pop()
            for raw in parts:
                if not raw:
                    continue
                line = raw.decode("utf-8", "replace")
                self.stderr_tail.append(line)
                if in_header:
                    header.append(line)
                    if line.startswith("Output #0"):
                        seen_output0 = True
                    if seen_output0 and self.out_dims is None:
                        m = _OUT_VID_RE.search(line)
                        if m:
                            self.out_dims = (int(m.group(1)), int(m.group(2)))
                            self._dims_event.set()
                    if line.startswith("Stream mapping:") and self.input_info is None:
                        self.input_info = parse_input_header("\n".join(header))
                    if len(header) > 400 or line.startswith(("frame=", "size=")):
                        in_header = False
                        if self.input_info is None:
                            self.input_info = parse_input_header("\n".join(header))
                self._parse_line(line)
        if buf:
            self._parse_line(buf.decode("utf-8", "replace"))
        f.close()
        # stderr EOF: ffmpeg is exiting, every showinfo line has been parsed
        self.vbook.close()
        self.abook.close()

    def _parse_line(self, line: str):
        if "showinfo" in line or " pts_time:" in line:
            for frag in _FRAG_SPLIT.split(line):
                m = _FRAG_RE.match(frag.strip())
                if not m:
                    continue
                n = int(m.group(1))
                pts = None if m.group(3) == "NOPTS" else float(m.group(3))
                if "nb_samples:" in frag or "rate:" in frag or "chlayout:" in frag:
                    self.abook.put(n, (pts, 0, 0))
                else:
                    ms = _SIZE_RE.search(frag)
                    if ms:
                        self.vbook.put(n, (pts, int(ms.group(1)), int(ms.group(2))))
            return
        if "speed=" in line or "frame=" in line:
            for k, rx in _STATS_RE.items():
                m = rx.search(line)
                if m:
                    try:
                        self.stats[k] = float(m.group(1)) if k != "time" else m.group(1)
                    except ValueError:
                        pass

    def _video_loop(self):
        out = self.proc.stdout
        n = 0
        dims = None
        while True:
            info = self.vbook.get(n, self.info_timeout_s if dims is None else 3.0)
            if info is not None:
                pts, w, h = info
                dims = (w, h)
            else:
                # showinfo line missing (stderr closed = process ending, or a garbled log line):
                # keep the stream in sync with the last known / declared frame size
                pts = None
                dims = dims or self.out_dims
                if dims is None:
                    if self.vbook.closed or self.proc.poll() is not None:
                        break
                    continue
                w, h = dims
            data = _read_exact(out, w * h * 3)
            if data is None:
                break
            now = time.time()
            self.last_output_wall = now
            img = np.frombuffer(data, dtype=np.uint8).reshape(h, w, 3)
            self.frames += 1
            if self.on_frame:
                self.on_frame(n, pts, img, now)
            n += 1
        try:
            out.close()
        except Exception:
            pass

    def _audio_loop(self):
        if self.audio_transport == "fd":
            fd = self._audio_fd

            def rd(k):
                return os.read(fd, k)
        else:
            conn = None
            while conn is None:
                try:
                    conn, _ = self._audio_sock.accept()
                except socket.timeout:
                    if self.proc.poll() is not None or self._stopping:
                        return
                except OSError:
                    return
            conn.settimeout(None)
            self._audio_conn = conn

            def rd(k):
                return conn.recv(k)
        idx = 0
        carry = b""
        chunk_bytes = max(2, (self.audio_sr // 4) * 2)   # ~0.25 s reads
        while True:
            try:
                b = rd(chunk_bytes)
            except OSError:
                break
            if not b:
                break
            b = carry + b
            if len(b) % 2:
                carry, b = b[-1:], b[:-1]
            else:
                carry = b""
            if not b:
                continue
            s = np.frombuffer(b, dtype="<i2")
            now = time.time()
            self.last_output_wall = now
            if self.on_audio:
                self.on_audio(s, idx, now)
            idx += len(s)
            self.audio_samples = idx
        if self.audio_transport == "tcp":
            try:
                self._audio_conn.close()
            except Exception:
                pass
        self._close_audio()

    def error_summary(self) -> str:
        lines = [l for l in self.stderr_tail if not l.startswith(("[Parsed_", "frame=", "  ", "size="))]
        return " | ".join(lines[-6:])[-600:]
