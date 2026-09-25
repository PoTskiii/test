"""HLS for precise timing: playlist parsing, MPEG-TS PTS scanning, PTS->PDT
mapping, stall/gap bookkeeping, and a segment fetcher.

Why fetch segments ourselves instead of letting ffmpeg read the URL?
--------------------------------------------------------------------
* ``#EXT-X-PROGRAM-DATE-TIME`` (PDT) stamps the first sample of every media
  segment with an absolute wall-clock time, from the encoder or the YouTube
  ingest clock. That is the best latency reference there is, and it is
  consistent with ADS-B and astronomy. To use it per frame we must know which
  segment a decoded frame came from. We download each segment, read the
  earliest PTS inside it (``ts_scan``), and feed the bytes to one persistent
  ffmpeg over stdin with ``-copyts``. ffmpeg's frame PTS (from ``showinfo``)
  then maps exactly to PDT + offset (``PtsTimeMap``). The 33-bit 90 kHz PTS
  wraps every 26.5 h, and the stream has run for days, so all PTS arithmetic
  is modulo 2**33.
* Segment arrival times are the best stall sensor we have. If the playlist
  stops advancing while our fetches succeed, the problem is upstream: the
  on-site uplink or YouTube. A PDT jump between consecutive segments means
  media is missing: the uplink dropped out. Slow or failed downloads are our
  own network. See ``SegmentTimeline`` and ``stats.py``.
* ffmpeg (the static imageio-ffmpeg 7.0.2 build) segfaults while parsing the
  MPEG-TS SDT table: static glibc iconv cannot load gconv modules. ``ts_scan``
  strips PID 0x11 (SDT/BAT) before the data reaches ffmpeg, which removes the
  problem whichever ffmpeg build is used.

Failure modes: fMP4 (``EXT-X-MAP``) playlists are not parsed for PTS, so the
caller falls back to ffmpeg-direct mode. Encrypted segments (``EXT-X-KEY``
other than NONE) are refused the same way. PDT may be absent. Then frames are
timed by receive time and ``StreamClock``.
"""
from __future__ import annotations

import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional
from urllib.parse import urljoin, urlparse

import numpy as np

from ..types import UTC

log = logging.getLogger("hordewatch.ingest.hls")

PTS_WRAP = 1 << 33          # MPEG-TS PTS is 33 bits @ 90 kHz -> wraps every 95443.7 s (26.5 h)
PTS_HZ = 90000
TS_PACKET = 188
STRIP_PIDS = (0x11,)        # SDT/BAT: crashes static ffmpeg builds, useless to us


# ============================================================================ playlist parsing
def parse_pdt(s: str) -> datetime:
    """Parse an EXT-X-PROGRAM-DATE-TIME value (ISO 8601) into an aware UTC datetime.

    Accepts 'Z', '+00:00', '+0000', lowercase 'z', any number of fractional
    digits, and a missing offset (interpreted as UTC, as players do)."""
    s = s.strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})[Tt ](\d{2}):(\d{2}):(\d{2})(?:[.,](\d+))?\s*(Z|z|[+-]\d{2}(?::?\d{2})?)?$", s)
    if not m:
        raise ValueError(f"bad PROGRAM-DATE-TIME {s!r}")
    y, mo, d, hh, mi, ss, frac, tz = m.groups()
    us = int((frac or "0")[:6].ljust(6, "0"))
    dt = datetime(int(y), int(mo), int(d), int(hh), int(mi), int(ss), us, tzinfo=UTC)
    if tz and tz not in ("Z", "z"):
        sign = 1 if tz[0] == "+" else -1
        digits = tz[1:].replace(":", "")
        off = timedelta(hours=int(digits[:2]), minutes=int(digits[2:4] or 0))
        dt = dt - sign * off
    return dt


@dataclass
class Segment:
    seq: int
    uri: str
    duration: float
    pdt: Optional[datetime] = None
    pdt_explicit: bool = False
    discontinuity: bool = False
    gap: bool = False
    byterange: Optional[tuple] = None     # (length, offset)
    title: str = ""

    @property
    def pdt_end(self) -> Optional[datetime]:
        return self.pdt + timedelta(seconds=self.duration) if self.pdt else None


@dataclass
class MediaPlaylist:
    target_duration: float = 0.0
    media_sequence: int = 0
    segments: list = field(default_factory=list)
    endlist: bool = False
    has_map: bool = False
    map_uri: Optional[str] = None
    encrypted: bool = False
    version: int = 0
    discontinuity_sequence: int = 0
    playlist_type: Optional[str] = None
    part_target: Optional[float] = None

    @property
    def last_seq(self) -> Optional[int]:
        return self.segments[-1].seq if self.segments else None


@dataclass
class Variant:
    uri: str
    bandwidth: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    codecs: str = ""
    frame_rate: Optional[float] = None


_ATTR_RE = re.compile(r'([A-Z0-9-]+)=("[^"]*"|[^,]*)')


def _attrs(s: str) -> dict:
    return {k: v.strip('"') for k, v in _ATTR_RE.findall(s)}


def resolve_uri(base: str, uri: str) -> str:
    """Resolve a playlist URI against its playlist URL or local path."""
    if re.match(r"^[a-z][a-z0-9+.-]*://", uri, re.I):
        return uri
    if base.startswith(("http://", "https://")):
        return urljoin(base, uri)
    if base.startswith("file://"):
        base = urlparse(base).path
    if os.path.isabs(uri):
        return uri
    return os.path.join(os.path.dirname(base), uri)


def is_master_playlist(text: str) -> bool:
    return "#EXT-X-STREAM-INF" in text


def parse_master_playlist(text: str, base_url: str = "") -> list:
    out, pending = [], None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#EXT-X-STREAM-INF:"):
            pending = _attrs(line.split(":", 1)[1])
        elif line and not line.startswith("#") and pending is not None:
            w = h = None
            if "RESOLUTION" in pending and "x" in pending["RESOLUTION"]:
                w, h = (int(x) for x in pending["RESOLUTION"].lower().split("x")[:2])
            fr = pending.get("FRAME-RATE")
            out.append(Variant(uri=resolve_uri(base_url, line), bandwidth=int(float(pending.get("BANDWIDTH", 0) or 0)),
                               width=w, height=h, codecs=pending.get("CODECS", ""),
                               frame_rate=float(fr) if fr else None))
            pending = None
    return out


def choose_variant(variants: list, max_height: int = 720) -> Optional[Variant]:
    """Highest-bandwidth variant whose height is <= max_height (else the smallest)."""
    if not variants:
        return None
    ok = [v for v in variants if v.height is None or v.height <= max_height]
    if ok:
        return max(ok, key=lambda v: ((v.height or 0), v.bandwidth))
    return min(variants, key=lambda v: (v.height or 1e9, v.bandwidth))


def parse_media_playlist(text: str, base_url: str = "") -> MediaPlaylist:
    """Parse an HLS media playlist (RFC 8216).

    Tags that precede a URI (EXTINF, PROGRAM-DATE-TIME, DISCONTINUITY,
    BYTERANGE, GAP) apply to that URI, in any order; ffmpeg writes EXTINF
    before PDT and YouTube writes PDT first. PDT is carried forward (prev.pdt +
    prev.duration) to segments without an explicit tag, but never across a
    discontinuity. That follows RFC 8216 section 6.2.1."""
    pl = MediaPlaylist()
    seq = None
    cur: dict = {}
    prev: Optional[Segment] = None
    last_byterange_end = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            tag, _, val = line.partition(":")
            if tag == "#EXT-X-TARGETDURATION":
                pl.target_duration = float(val)
            elif tag == "#EXT-X-MEDIA-SEQUENCE":
                pl.media_sequence = int(val)
            elif tag == "#EXT-X-DISCONTINUITY-SEQUENCE":
                pl.discontinuity_sequence = int(val)
            elif tag == "#EXT-X-VERSION":
                pl.version = int(val)
            elif tag == "#EXT-X-PLAYLIST-TYPE":
                pl.playlist_type = val.strip()
            elif tag == "#EXT-X-ENDLIST":
                pl.endlist = True
            elif tag == "#EXT-X-MAP":
                pl.has_map = True
                u = _attrs(val).get("URI")
                pl.map_uri = resolve_uri(base_url, u) if u else None
            elif tag == "#EXT-X-KEY":
                if _attrs(val).get("METHOD", "NONE").upper() != "NONE":
                    pl.encrypted = True
            elif tag == "#EXT-X-PART-INF":
                a = _attrs(val)
                if "PART-TARGET" in a:
                    pl.part_target = float(a["PART-TARGET"])
            elif tag == "#EXTINF":
                d, _, title = val.partition(",")
                cur["duration"] = float(d)
                cur["title"] = title
            elif tag == "#EXT-X-PROGRAM-DATE-TIME":
                try:
                    cur["pdt"] = parse_pdt(val)
                except ValueError as e:
                    log.warning("%s", e)
            elif tag == "#EXT-X-DISCONTINUITY":
                cur["discontinuity"] = True
            elif tag == "#EXT-X-GAP":
                cur["gap"] = True
            elif tag == "#EXT-X-BYTERANGE":
                n, _, o = val.partition("@")
                off = int(o) if o else last_byterange_end
                cur["byterange"] = (int(n), off)
                last_byterange_end = off + int(n)
            continue
        # a URI line closes the segment
        if seq is None:
            seq = pl.media_sequence
        pdt = cur.get("pdt")
        explicit = pdt is not None
        if pdt is None and prev is not None and prev.pdt is not None and not cur.get("discontinuity"):
            pdt = prev.pdt + timedelta(seconds=prev.duration)
        seg = Segment(seq=seq, uri=resolve_uri(base_url, line), duration=float(cur.get("duration", pl.target_duration)),
                      pdt=pdt, pdt_explicit=explicit, discontinuity=bool(cur.get("discontinuity")),
                      gap=bool(cur.get("gap")), byterange=cur.get("byterange"), title=cur.get("title", ""))
        pl.segments.append(seg)
        prev = seg
        seq += 1
        cur = {}
    if not pl.target_duration and pl.segments:
        pl.target_duration = max(s.duration for s in pl.segments)
    return pl


# ============================================================================ MPEG-TS scanning
@dataclass
class TsInfo:
    anchor90: Optional[int] = None       # earliest PTS in the segment (wrap-aware), 90 kHz, mod 2**33
    first_video90: Optional[int] = None
    first_audio90: Optional[int] = None
    n_packets: int = 0
    n_pes: int = 0
    stripped: int = 0
    sync_offset: int = 0


def _pes_pts(payload: np.ndarray) -> Optional[int]:
    """PTS of a PES header (payload starting at 00 00 01), or None."""
    if len(payload) < 14 or payload[0] != 0 or payload[1] != 0 or payload[2] != 1:
        return None
    sid = int(payload[3])
    if sid in (0xBC, 0xBE, 0xBF, 0xF0, 0xF1, 0xFF, 0xF2, 0xF8):   # streams without the optional header
        return None
    if (payload[7] >> 6) & 0x2 == 0:                               # PTS_DTS_flags: PTS absent
        return None
    p = payload[9:14].astype(np.int64)
    return int(((p[0] >> 1) & 0x7) << 30 | p[1] << 22 | (p[2] >> 1) << 15 | p[3] << 7 | (p[4] >> 1))


def ts_scan(data: bytes, strip_pids=STRIP_PIDS) -> tuple:
    """Scan an MPEG-TS buffer, returning ``(TsInfo, payload_bytes)``.

    Finds the earliest presentation timestamp (wrap-aware), the first video
    PTS (stream_id 0xE0-0xEF) and the first audio PTS (0xC0-0xDF or 0xBD).
    It also drops the packets of ``strip_pids``. Vectorised with numpy: a 5 s
    720p segment (~1.5 MB, 8k packets) takes a few ms."""
    info = TsInfo()
    n_total = len(data)
    off = -1
    mv = memoryview(data)
    for i in range(min(TS_PACKET, n_total)):
        if data[i] == 0x47 and (i + TS_PACKET >= n_total or data[i + TS_PACKET] == 0x47):
            off = i
            break
    if off < 0:
        return info, bytes(data)
    info.sync_offset = off
    n = (n_total - off) // TS_PACKET
    if n == 0:
        return info, bytes(data)
    arr = np.frombuffer(mv[off:off + n * TS_PACKET], dtype=np.uint8).reshape(n, TS_PACKET)
    info.n_packets = n
    pid = ((arr[:, 1].astype(np.int32) & 0x1F) << 8) | arr[:, 2]
    good = arr[:, 0] == 0x47
    pusi = (arr[:, 1] & 0x40) != 0
    afc = (arr[:, 3] >> 4) & 0x3
    has_payload = (afc & 1) == 1
    start = np.full(n, 4, dtype=np.int32)
    adapt = (afc & 2) == 2
    start[adapt] += 1 + arr[adapt, 4].astype(np.int32)
    cand = np.nonzero(good & pusi & has_payload & (start < TS_PACKET - 14) & (pid > 0x1F) & (pid != 0x1FFF))[0]
    ptss = []
    for k in cand:
        pl = arr[k, start[k]:]
        if pl[0] != 0 or pl[1] != 0 or pl[2] != 1:
            continue
        pts = _pes_pts(pl)
        if pts is None:
            continue
        info.n_pes += 1
        sid = int(pl[3])
        if 0xE0 <= sid <= 0xEF and info.first_video90 is None:
            info.first_video90 = pts
        elif (0xC0 <= sid <= 0xDF or sid == 0xBD) and info.first_audio90 is None:
            info.first_audio90 = pts
        ptss.append(pts)
    if ptss:
        ref = ptss[0]
        d = [((p - ref + (PTS_WRAP >> 1)) % PTS_WRAP) - (PTS_WRAP >> 1) for p in ptss]
        info.anchor90 = (ref + min(d)) % PTS_WRAP
    strip = np.isin(pid, np.asarray(strip_pids, dtype=np.int32)) if strip_pids else np.zeros(n, bool)
    info.stripped = int(strip.sum())
    if info.stripped == 0 and off == 0 and n * TS_PACKET == n_total:
        return info, bytes(data)
    return info, arr[~strip].tobytes()


# ============================================================================ PTS -> wall clock
@dataclass
class MapEntry:
    seq: int
    anchor90: int
    dur: float
    pdt: Optional[float]        # unix seconds of the segment's first sample (PDT) or None
    recv: float                 # unix seconds: download complete
    seen: float                 # unix seconds: first seen in the playlist


class PtsTimeMap:
    """Map decoded-frame PTS back to the segment it came from.

    ``lookup(pts_s)`` returns ``(entry, offset_s)`` with
    ``offset_s = (pts - anchor) / 90 kHz`` computed modulo 2**33. ffmpeg may
    report PTS unwrapped, shifted by -2**33 (it does so near a wrap) or raw.
    The modulo makes all three identical. Newest segments are tried first, so
    a small overshoot slack (``slack_s``, for audio frames extending past the
    last video frame) never steals frames from the next segment.
    """

    def __init__(self, maxlen: int = 2048, slack_s: float = 1.0):
        self._entries: list = []
        self._lock = threading.Lock()
        self.maxlen = maxlen
        self.slack_s = slack_s

    def add(self, e: MapEntry):
        with self._lock:
            self._entries.append(e)
            if len(self._entries) > self.maxlen:
                del self._entries[: len(self._entries) - self.maxlen]

    def __len__(self):
        return len(self._entries)

    def lookup(self, pts_s: Optional[float]):
        if pts_s is None:
            return None, None
        p90 = int(round(pts_s * PTS_HZ)) % PTS_WRAP
        with self._lock:
            entries = list(reversed(self._entries[-256:]))
        for e in entries:
            d = (p90 - e.anchor90) % PTS_WRAP
            if d <= (e.dur + self.slack_s) * PTS_HZ:
                return e, d / PTS_HZ
        # small negative offsets: leading audio or B-frames before the anchor of the oldest candidate
        for e in entries:
            d = ((p90 - e.anchor90 + (PTS_WRAP >> 1)) % PTS_WRAP) - (PTS_WRAP >> 1)
            if -self.slack_s * PTS_HZ <= d < 0:
                return e, d / PTS_HZ
        return None, None


def pts_jump(prev: MapEntry, anchor90: int) -> float:
    """Seconds by which ``anchor90`` deviates from the continuation of ``prev`` (signed, wrap-aware)."""
    expected = (prev.anchor90 + int(round(prev.dur * PTS_HZ))) % PTS_WRAP
    d = ((anchor90 - expected + (PTS_WRAP >> 1)) % PTS_WRAP) - (PTS_WRAP >> 1)
    return d / PTS_HZ


# ============================================================================ stall / gap bookkeeping
class SegmentTimeline:
    """Track playlist progress, returning new segments and classifying stalls.

    Pure bookkeeping with an injected clock (``now``), so it can be unit
    tested with synthetic arrival times.

    * A *stall* is an interval with no new segment for longer than
      ``stall_factor * target_duration`` (at least ``min_stall_s``). Its
      duration counts from when the next segment was due (last advance +
      target). It is ``upstream`` if our playlist fetches kept succeeding and
      ``local`` if they failed.
    * A *gap* is missing media time between consecutive segments:
      ``pdt[k] - (pdt[k-1] + dur[k-1]) > gap_tolerance_s``. The event's
      ``onsite_start`` is the PDT at which the media stopped: the time of the
      outage on site.
    * ``edge_lag`` = now - (pdt + dur) of the newest segment when it appears.
      Its running minimum is the floor of uplink plus YouTube processing
      delay.
    * ``media_deficit_s`` (YouTube only, where sequence numbers count from 0 at
      broadcast start) = wall time since ``stream_start`` minus the media time
      produced, (last_seq + 1) * target. It grows with every uplink outage.
    """

    def __init__(self, stats, stall_factor: float = 2.0, min_stall_s: float = 6.0, gap_tolerance_s: float = 0.75,
                 start_segments: Optional[int] = 3, stream_start: Optional[float] = None):
        self.stats = stats
        self.stall_factor = stall_factor
        self.min_stall_s = min_stall_s
        self.gap_tolerance_s = gap_tolerance_s
        self.start_segments = start_segments
        self.stream_start = stream_start
        self.last_seq: Optional[int] = None
        self.last_seg: Optional[Segment] = None
        self.last_advance: Optional[float] = None
        self.last_poll: Optional[float] = None
        self.target: float = 0.0
        self.fetch_errors_since_advance = 0
        self.in_stall = False

    def stall_threshold(self) -> float:
        return max(self.min_stall_s, self.stall_factor * (self.target or 2.0))

    def on_fetch_error(self, now: float, err: str = ""):
        self.fetch_errors_since_advance += 1
        self.stats.update(last_error=f"playlist: {err}"[:300])
        self.check(now)

    def check(self, now: float):
        """Update the ongoing-stall state (call on every poll)."""
        if self.last_advance is None:
            return
        if now - self.last_advance > self.stall_threshold():
            if not self.in_stall:
                self.in_stall = True
                self.stats.update(state="stalled", current_stall_since=self.last_advance + (self.target or 0))

    def on_playlist(self, pl: MediaPlaylist, now: float) -> list:
        """Register a freshly fetched playlist; return the segments we have not seen yet."""
        prev_poll = self.last_poll
        self.last_poll = now
        if pl.target_duration:
            self.target = pl.target_duration
            self.stats.update(target_duration=pl.target_duration)
        if not pl.segments:
            self.check(now)
            return []
        if self.last_seq is None:
            if pl.endlist or self.start_segments is None:
                new = list(pl.segments)
            else:
                new = list(pl.segments[-max(1, self.start_segments):])
        else:
            if pl.last_seq is not None and pl.last_seq < self.last_seq - 5:
                # sequence numbers restarted: a new broadcast/encoder session
                log.warning("media sequence went backwards (%s -> %s): treating as a new stream", self.last_seq,
                            pl.last_seq)
                self.stats.incr("discontinuities")
                self.last_seq, self.last_seg = None, None
                return self.on_playlist(pl, now)
            new = [s for s in pl.segments if s.seq > self.last_seq]
            first_avail = pl.segments[0].seq
            if first_avail > self.last_seq + 1:
                skipped = first_avail - self.last_seq - 1
                self.stats.incr("segments_skipped", skipped)
                self.stats.add_stall("skip", start=prev_poll or now, end=now, seq=self.last_seq + 1,
                                     detail=f"{skipped} segment(s) left the playlist window before fetch")
        if not new:
            self.check(now)
            return []
        # --- the playlist advanced
        if self.last_advance is not None:
            waited = now - self.last_advance
            if waited > self.stall_threshold():
                kind = "local" if self.fetch_errors_since_advance > 0 else "upstream"
                start = self.last_advance + (self.target or 0.0)
                onsite = self.last_seg.pdt_end.timestamp() if (self.last_seg and self.last_seg.pdt) else None
                self.stats.add_stall(kind, start=start, end=now, onsite_start=onsite,
                                     onsite_method="pdt" if onsite else None, seq=new[0].seq,
                                     detail=f"playlist did not advance for {waited:.1f}s "
                                            f"({self.fetch_errors_since_advance} fetch errors)")
        self.in_stall = False
        self.fetch_errors_since_advance = 0
        self.last_advance = now
        for s in new:
            if self.last_seg is not None and s.pdt is not None and self.last_seg.pdt is not None \
                    and s.seq == self.last_seg.seq + 1:
                gap = (s.pdt - self.last_seg.pdt_end).total_seconds()
                if gap > self.gap_tolerance_s:
                    t0 = self.last_seg.pdt_end.timestamp()
                    self.stats.add_stall("gap", start=t0, end=s.pdt.timestamp(), onsite_start=t0,
                                         onsite_method="pdt", seq=s.seq,
                                         detail=f"PROGRAM-DATE-TIME jumps {gap:.2f}s: media missing")
            if s.discontinuity:
                self.stats.incr("discontinuities")
            self.last_seg = s
            self.last_seq = s.seq
        newest = new[-1]
        upd = {"state": "streaming", "current_stall_since": None}
        if newest.pdt is not None:
            lag = now - newest.pdt_end.timestamp()
            prev_min = self.stats.edge_lag_min_s
            upd.update(edge_lag_s=round(lag, 3), last_pdt=newest.pdt.timestamp(),
                       edge_lag_min_s=round(lag if prev_min is None else min(prev_min, lag), 3))
        if self.stream_start and self.target:
            produced = (newest.seq + 1) * self.target
            upd["media_deficit_s"] = round((now - self.stream_start) - produced, 1)
        self.stats.update(**upd)
        return new


# ============================================================================ fetching
class FetchError(RuntimeError):
    def __init__(self, msg, status=None):
        super().__init__(msg)
        self.status = status


class Fetcher:
    """Tiny HTTP/local fetcher (httpx if installed, else urllib)."""

    def __init__(self, headers: Optional[dict] = None, timeout: float = 15.0):
        self.headers = dict(headers or {})
        self.timeout = timeout
        self._client = None
        try:
            import httpx  # noqa
            self._httpx = httpx
        except Exception:
            self._httpx = None

    def get(self, url: str, byterange=None) -> tuple:
        if not url.startswith(("http://", "https://")):
            path = urlparse(url).path if url.startswith("file://") else url
            try:
                with open(path, "rb") as f:
                    if byterange:
                        f.seek(byterange[1])
                        return f.read(byterange[0]), {}
                    return f.read(), {}
            except OSError as e:
                raise FetchError(str(e), status=404) from e
        headers = dict(self.headers)
        if byterange:
            headers["Range"] = f"bytes={byterange[1]}-{byterange[1] + byterange[0] - 1}"
        if self._httpx is not None:
            if self._client is None:
                self._client = self._httpx.Client(timeout=self.timeout, follow_redirects=True)
            try:
                r = self._client.get(url, headers=headers)
            except self._httpx.HTTPError as e:
                raise FetchError(f"{type(e).__name__}: {e}") from e
            if r.status_code >= 400:
                raise FetchError(f"HTTP {r.status_code}", status=r.status_code)
            return r.content, dict(r.headers)
        import urllib.error
        import urllib.request
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            raise FetchError(f"HTTP {e.code}", status=e.code) from e
        except Exception as e:
            raise FetchError(f"{type(e).__name__}: {e}") from e

    def close(self):
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None


class PlaylistGone(RuntimeError):
    """The playlist URL expired / 403 / 404: re-resolve the stream."""


class UnsupportedPlaylist(RuntimeError):
    """fMP4 or encrypted: use ffmpeg-direct mode instead."""


_TIMING_HEADERS = ("x-head-seqnum", "x-head-time-millis", "x-head-time-sec", "x-walltime-ms", "x-sequence-num",
                   "x-segment-lmt", "date", "age")


class HLSFetcher:
    """Poll a media playlist; download new segments and hand them to ``on_segment``.

    ``on_segment(seg, payload_bytes, entry)`` receives SDT-stripped TS bytes
    and the ``MapEntry`` already registered in ``time_map``. With
    ``download=False`` the fetcher only monitors the playlist (timing/stall
    stats for ffmpeg-direct mode). ``run()`` blocks until stop, ENDLIST (VOD
    fully consumed), expiry, or a fatal error (raised).
    """

    def __init__(self, url: str, stats, timeline: SegmentTimeline, time_map: Optional[PtsTimeMap] = None,
                 on_segment: Optional[Callable] = None, stop: Optional[threading.Event] = None,
                 headers: Optional[dict] = None, poll_s: Optional[float] = None, timeout: float = 15.0,
                 download: bool = True, max_errors: int = 4, expires_at: Optional[float] = None,
                 max_height: int = 720, segment_archiver=None, clock=time.time):
        self.url = url
        self.stats = stats
        self.timeline = timeline
        self.time_map = time_map if time_map is not None else PtsTimeMap()
        self.on_segment = on_segment
        self.stop = stop or threading.Event()
        self.fetcher = Fetcher(headers, timeout)
        self.poll_s = poll_s
        self.download = download
        self.max_errors = max_errors
        self.expires_at = expires_at
        self.max_height = max_height
        self.segment_archiver = segment_archiver
        self.now = clock
        self.ended = False
        self.expiring = False
        self._last_entry: Optional[MapEntry] = None
        self._variant_bw = None

    def _poll_interval(self, target: float) -> float:
        if self.poll_s:
            return float(self.poll_s)
        return float(min(5.0, max(0.5, (target or 4.0) / 2.0)))

    def run(self):
        errors = 0
        try:
            while not self.stop.is_set():
                if self.expires_at and self.now() > self.expires_at - 600:
                    self.expiring = True
                    return
                t_req = self.now()
                try:
                    raw, _ = self.fetcher.get(self.url)
                    text = raw.decode("utf-8", "replace")
                except FetchError as e:
                    errors += 1
                    self.timeline.on_fetch_error(self.now(), str(e))
                    if e.status in (401, 403, 404, 410) or errors >= self.max_errors:
                        raise PlaylistGone(f"playlist fetch failed: {e}") from e
                    self.stop.wait(min(10.0, 1.0 * errors))
                    continue
                errors = 0
                if is_master_playlist(text):
                    v = choose_variant(parse_master_playlist(text, self.url), self.max_height)
                    if v is None:
                        raise UnsupportedPlaylist("master playlist without variants")
                    log.info("master playlist -> variant %sx%s %s bps", v.width, v.height, v.bandwidth)
                    self.url = v.uri
                    self._variant_bw = v.bandwidth
                    if v.width and v.height:
                        self.stats.update(resolution=f"{v.width}x{v.height}")
                    continue
                pl = parse_media_playlist(text, self.url)
                if self.download and (pl.has_map or pl.encrypted):
                    raise UnsupportedPlaylist("fMP4 (EXT-X-MAP) or encrypted playlist")
                new = self.timeline.on_playlist(pl, self.now())
                for seg in new:
                    if self.stop.is_set():
                        return
                    self._handle_segment(seg, t_req)
                if pl.endlist and not new:
                    self.ended = True
                    self.stats.update(state="ended")
                    return
                if pl.endlist:
                    continue  # VOD: drain as fast as possible
                self.stop.wait(self._poll_interval(pl.target_duration))
        finally:
            self.fetcher.close()

    def _handle_segment(self, seg: Segment, seen: float):
        rec = {"seq": seg.seq, "pdt": seg.pdt.timestamp() if seg.pdt else None, "dur": seg.duration,
               "seen": round(seen, 3), "disc": seg.discontinuity}
        if seg.pdt is not None:
            rec["lag_s"] = round(seen - seg.pdt_end.timestamp(), 3)
        if not self.download:
            self.stats.add_segment(**rec)
            if self._variant_bw:
                self.stats.update(bitrate_kbps=round(self._variant_bw / 1000.0, 1))
            return
        data, hdr, t0 = None, {}, self.now()
        for attempt in range(3):
            try:
                data, hdr = self.fetcher.get(seg.uri, seg.byterange)
                break
            except FetchError as e:
                if e.status in (403, 410):
                    raise PlaylistGone(f"segment fetch: {e}") from e
                if attempt == 2:
                    self.stats.incr("segments_skipped")
                    self.stats.add_stall("local", start=t0, end=self.now(), seq=seg.seq,
                                         detail=f"segment download failed: {e}")
                    return
                self.stop.wait(0.5 * (attempt + 1))
        recv = self.now()
        info, payload = ts_scan(data)
        rec.update(recv=round(recv, 3), dl_s=round(recv - t0, 3), bytes=len(data))
        timing_hdr = {k.lower(): v for k, v in hdr.items() if k.lower() in _TIMING_HEADERS}
        if timing_hdr:
            rec["hdr"] = timing_hdr
        self.stats.add_segment(**rec)
        if seg.duration > 0:
            kbps = len(data) * 8 / seg.duration / 1000.0
            prev = self.stats.bitrate_kbps
            self.stats.update(bitrate_kbps=round(kbps if prev is None else 0.8 * prev + 0.2 * kbps, 1))
        if self.segment_archiver is not None:
            try:
                self.segment_archiver.write(seg, data, recv)
            except Exception as e:
                log.warning("segment archive failed: %s", e)
        if info.anchor90 is None:
            log.warning("segment %s: no PTS found (%d bytes) - timing falls back to receive time", seg.seq, len(data))
            entry = None
        else:
            entry = MapEntry(seq=seg.seq, anchor90=info.anchor90, dur=seg.duration,
                             pdt=seg.pdt.timestamp() if seg.pdt else None, recv=recv, seen=seen)
        restart = False
        if entry is not None:
            if self._last_entry is not None and (seg.discontinuity or seg.seq != self._last_entry.seq + 1
                                                 or abs(pts_jump(self._last_entry, entry.anchor90)) > 2.0):
                restart = seg.discontinuity or abs(pts_jump(self._last_entry, entry.anchor90)) > 2.0
            self.time_map.add(entry)
            self._last_entry = entry
        if self.on_segment is not None:
            self.on_segment(seg, payload, entry, restart)
