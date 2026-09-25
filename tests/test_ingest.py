"""Offline tests for hordewatch.ingest (replay, live-from-local-HLS, parsers) and analyzers.stream_health.

All media is synthesised: a 20 s clip whose white square moves 14 px/s (so each decoded frame
encodes its own content time) with a 440 Hz tone, encoded with the imageio-ffmpeg binary.
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

from hordewatch import ingest
from hordewatch.analyzers.base import Context
from hordewatch.analyzers.stream_health import (StreamHealthAnalyzer, classify_uplink, interval_multiple_test,
                                                rayleigh)
from hordewatch.ingest.ffmpeg import ffmpeg_exe
from hordewatch.ingest.hls import (PTS_HZ, PTS_WRAP, MapEntry, PtsTimeMap, SegmentTimeline, choose_variant,
                                   parse_master_playlist, parse_media_playlist, parse_pdt, ts_scan)
from hordewatch.ingest.live import (ItemQueue, expiry_from_url, redact_url, resolve_stream,
                                    stream_from_ytdlp_info, ResolveError)
from hordewatch.ingest.pipeline import AudioChunker, ReceiveClock
from hordewatch.ingest.replay import parse_defaultno_name, parse_filename_time
from hordewatch.ingest.stats import StreamStats
from hordewatch.types import KINDS, UTC, StreamClock

FF = ffmpeg_exe()
FPS, W, H = 10, 320, 96
X0, SPEED = 8.0, 14.0           # square left edge = X0 + SPEED * t  (px)
CLIP_S = 20.0


# ============================================================================ fixtures / helpers
def _encode_clip(path: Path, seconds=CLIP_S, tone_hz=440.0):
    n = int(round(seconds * FPS))
    frames = bytearray()
    for i in range(n):
        t = i / FPS
        img = np.full((H, W, 3), 30, np.uint8)
        x = int(round(X0 + SPEED * t))
        img[40:56, x:x + 16] = 255
        img[0:8, :, 0] = 220            # red stripe on top: checks RGB channel order
        frames += img.tobytes()
    cmd = [FF, "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
           "-f", "lavfi", "-i", f"sine=frequency={tone_hz}:sample_rate=44100:duration={seconds}",
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
           "-g", str(FPS), "-c:a", "aac", "-b:a", "96k", "-shortest", str(path)]
    subprocess.run(cmd, input=bytes(frames), check=True, capture_output=True, timeout=120)
    return path


def _encode_hls(src: Path, out_dir: Path, seg_s=2, ts_offset=None):
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [FF, "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-c", "copy"]
    if ts_offset is not None:
        cmd += ["-output_ts_offset", str(ts_offset)]
    cmd += ["-f", "hls", "-hls_time", str(seg_s), "-hls_list_size", "0", "-hls_flags", "program_date_time",
            "-hls_segment_type", "mpegts", "-hls_segment_filename", str(out_dir / "seg%03d.ts"),
            str(out_dir / "index.m3u8")]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    return out_dir / "index.m3u8"


def _content_time(img: np.ndarray) -> float:
    """Content time encoded by the square's position."""
    band = img[40:56, :, :].mean(axis=(0, 2))
    xs = np.nonzero(band > 128)[0]
    assert len(xs) > 4, "square not found"
    left = xs.mean() - 7.5
    return (left - X0) / SPEED


@pytest.fixture(scope="module")
def media(tmp_path_factory):
    d = tmp_path_factory.mktemp("ingest_media")
    clip = _encode_clip(d / "202609251620_202609251621.mp4")
    return {"dir": d, "clip": clip}


def _collect(src):
    items = list(src)
    frames = [it for k, it in items if k == "frame"]
    audio = [it for k, it in items if k == "audio"]
    return items, frames, audio


@pytest.fixture(autouse=True)
def _clean_bus():
    yield
    ingest._BOUND.clear()
    ingest._LATEST.clear()


# ============================================================================ timestamp rules
def test_defaultno_name_to_utc():
    nt = parse_defaultno_name("202609251620_202609251703.mp4")
    assert nt.start == datetime(2026, 9, 25, 14, 20, tzinfo=UTC)      # CEST = UTC+2
    assert nt.end == datetime(2026, 9, 25, 15, 3, tzinfo=UTC)
    winter = parse_defaultno_name("cuts/202612011200_202612011300.mp4")
    assert winter.start == datetime(2026, 12, 1, 11, 0, tzinfo=UTC)   # CET = UTC+1
    assert parse_defaultno_name("202609251620_202609251603.mp4") is None   # end before start
    assert parse_defaultno_name("clip.mp4") is None


def test_generic_filename_times(tmp_path):
    a = parse_filename_time(tmp_path / "20260925" / "142000_17.jpg")                  # hordewatch archive: UTC
    assert a.start == datetime(2026, 9, 25, 14, 20, tzinfo=UTC) and a.rule == "hordewatch_archive_utc"
    b = parse_filename_time("IMG_20260925_162005.jpg")                                 # local Oslo
    assert b.start == datetime(2026, 9, 25, 14, 20, 5, tzinfo=UTC)
    c = parse_filename_time("snap_2026-09-25T14-20-05.250Z.png")
    assert c.start == datetime(2026, 9, 25, 14, 20, 5, 250000, tzinfo=UTC)
    assert parse_filename_time("board.jpg") is None


# ============================================================================ replay
@pytest.mark.parametrize("transport", ["fd", "tcp"])
def test_replay_defaultno_cut(media, tmp_path, transport):
    arch = tmp_path / "archive"
    src = ingest.make_source({"type": "replay", "files": [str(media["clip"])], "frame_interval_s": 5.0,
                              "audio_chunk_s": 10.0, "archive_every_n_frames": 2, "audio_transport": transport},
                             StreamClock(latency_s=30.0), {"archive_dir": str(arch)})
    items, frames, audio = _collect(src)
    src.close()
    start = datetime(2026, 9, 25, 14, 20, tzinfo=UTC)          # 16:20 CEST
    # --- frames: one per 5 s grid cell of a 20 s clip -> t = 0, 5, 10, 15
    assert len(frames) == 4
    for i, f in enumerate(frames):
        assert f.index == i
        assert abs((f.capture_ts - start).total_seconds() - 5.0 * i) < 0.15
        assert f.real_ts == f.capture_ts                        # replay latency defaults to 0
        assert f.image.shape == (H, W, 3) and f.image.dtype == np.uint8
        assert abs(_content_time(f.image) - 5.0 * i) < 0.12     # decoded content matches the timestamp
        assert f.image[2, W // 2, 0] > 150 and f.image[2, W // 2, 2] < 90    # RGB (not BGR)
        assert f.source == "replay:202609251620_202609251621.mp4"
    # --- audio: 16 kHz mono float32, 20 s total, 440 Hz
    assert [a.index for a in audio] == list(range(len(audio)))
    total = sum(a.duration_s for a in audio)
    assert abs(total - CLIP_S) < 0.1
    assert audio[0].sr == 16000 and audio[0].samples.dtype == np.float32
    assert abs(audio[0].duration_s - 10.0) < 1e-6
    assert abs((audio[0].capture_ts - start).total_seconds()) < 0.05
    assert abs((audio[1].capture_ts - start).total_seconds() - 10.0) < 0.05
    spec = np.abs(np.fft.rfft(audio[0].samples * np.hanning(len(audio[0].samples))))
    peak_hz = np.argmax(spec) * 16000 / len(audio[0].samples)
    assert abs(peak_hz - 440.0) < 2.0
    assert 0.08 < np.abs(audio[0].samples).max() <= 1.0          # lavfi sine amplitude is 1/8
    # --- strictly in timestamp order
    ts = [it.capture_ts for _, it in items]
    assert ts == sorted(ts)
    # --- archive: every 2nd frame as archive/YYYYMMDD/HHMMSS_<idx>.jpg (UTC)
    assert frames[0].path == str(arch / "20260925" / "142000_0.jpg") and os.path.isfile(frames[0].path)
    assert frames[2].path == str(arch / "20260925" / "142010_2.jpg") and os.path.isfile(frames[2].path)
    assert frames[1].path is None
    snap = src.stats.snapshot()
    assert snap["frames_out"] == 4 and snap["state"] == "ended" and snap["resolution"] == f"{W}x{H}"


def test_replay_latency_speed_and_align(media):
    t0 = time.monotonic()
    src = ingest.make_source({"type": "replay", "files": [str(media["clip"])], "latency_s": 30.0, "speed": 10.0,
                              "defaultno_align": "end", "archive": False}, StreamClock(), {})
    _, frames, audio = _collect(src)
    wall = time.monotonic() - t0
    assert wall > 1.3                         # last item at t=15 s -> >= 1.5 s at 10x
    end = datetime(2026, 9, 25, 15, 21, tzinfo=UTC) - timedelta(hours=1)    # 16:21 CEST = 14:21Z
    # align=end: the clip's last sample sits at the named end time
    assert abs((frames[0].capture_ts - (end - timedelta(seconds=CLIP_S))).total_seconds()) < 0.1
    for f in frames:
        assert abs((f.capture_ts - f.real_ts).total_seconds() - 30.0) < 1e-6


def test_replay_images_and_wav(tmp_path):
    import cv2
    import wave
    d = tmp_path / "shots"
    d.mkdir()
    for i in range(3):
        img = np.zeros((60, 2000, 3), np.uint8)
        img[:, :, 1] = 40 * (i + 1)
        cv2.imwrite(str(d / f"board_{i}.png"), img)
    wav = tmp_path / "20260925_162003.wav"                      # local 16:20:03 -> 14:20:03Z
    sr = 8000
    x = (0.5 * np.sin(2 * np.pi * 1000 * np.arange(int(2.5 * sr)) / sr) * 32767).astype("<i2")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(x.tobytes())
    src = ingest.make_source({"type": "replay", "files": [str(d), str(wav)], "start_utc": "2026-09-25T14:20:00Z",
                              "image_interval_s": 2.0, "audio_chunk_s": 1.0, "min_partial_audio_s": 0.25,
                              "max_width": 1000}, StreamClock(), {})
    items, frames, audio = _collect(src)
    t0 = datetime(2026, 9, 25, 14, 20, tzinfo=UTC)
    assert [round((f.capture_ts - t0).total_seconds(), 3) for f in frames] == [0.0, 2.0, 4.0]
    assert frames[0].image.shape == (30, 1000, 3)               # downscaled to max_width, aspect kept
    assert frames[1].image[..., 1].mean() > frames[0].image[..., 1].mean()
    assert frames[0].path.endswith("board_0.png")               # replayed images are not re-archived
    assert [round(a.duration_s, 2) for a in audio] == [1.0, 1.0, 0.5]           # last partial chunk kept
    assert abs((audio[0].capture_ts - t0).total_seconds() - 3.0) < 0.05
    ts = [it.capture_ts for _, it in items]
    assert ts == sorted(ts)                                     # images and audio merged in time order


def test_forced_archive_via_state(media, tmp_path):
    state = {}
    src = ingest.make_source({"type": "replay", "files": [str(media["clip"])], "archive_every_n_frames": 0},
                             StreamClock(), {"archive_dir": str(tmp_path)}, state=state)
    frames = []
    for kind, it in src:
        if kind == "frame":
            frames.append(it)
            if it.index == 1:
                state["archive_next"] = True           # an analyzer asks for this frame to be kept
    assert frames[0].path is None
    assert frames[1].path and os.path.isfile(frames[1].path)      # retroactively saved
    assert frames[2].path and os.path.isfile(frames[2].path)      # and the next one
    assert frames[3].path is None
    assert state["ingest_stats"]["frames_out"] == 4               # stats published into bound state


def test_make_source_errors():
    with pytest.raises(ValueError):
        ingest.make_source({"type": "carrier-pigeon"}, StreamClock(), {})
    with pytest.raises(ValueError):
        ingest.make_source({"type": "replay"}, StreamClock(), {})
    with pytest.raises(ValueError):
        ingest.make_source({"type": "live"}, StreamClock(), {})


# ============================================================================ HLS parsing / TS
SAMPLE_PLAYLIST = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:5
#EXT-X-MEDIA-SEQUENCE:81234
#EXT-X-DISCONTINUITY-SEQUENCE:2
#EXT-X-PROGRAM-DATE-TIME:2026-09-25T14:20:00.000+00:00
#EXTINF:5.0,
https://rr1---sn-example.googlevideo.com/videoplayback/id/EQHg.1/sq/81234/goap/seg.ts
#EXTINF:5.0,
https://rr1---sn-example.googlevideo.com/videoplayback/id/EQHg.1/sq/81235/goap/seg.ts
#EXT-X-PROGRAM-DATE-TIME:2026-09-25T16:20:10.500+02:00
#EXTINF:5.005,
81236.ts
#EXT-X-DISCONTINUITY
#EXTINF:5.0,
81237.ts
#EXTINF:4.0,
#EXT-X-PROGRAM-DATE-TIME:2026-09-25T14:20:40.25Z
81238.ts
"""


def test_hls_pdt_parser():
    pl = parse_media_playlist(SAMPLE_PLAYLIST, "https://manifest.example/api/hls_playlist/index.m3u8")
    assert pl.target_duration == 5 and pl.media_sequence == 81234 and not pl.endlist and not pl.has_map
    assert [s.seq for s in pl.segments] == [81234, 81235, 81236, 81237, 81238]
    s = pl.segments
    assert s[0].pdt == datetime(2026, 9, 25, 14, 20, tzinfo=UTC) and s[0].pdt_explicit
    assert s[1].pdt == datetime(2026, 9, 25, 14, 20, 5, tzinfo=UTC) and not s[1].pdt_explicit    # extrapolated
    assert s[2].pdt == datetime(2026, 9, 25, 14, 20, 10, 500000, tzinfo=UTC)                   # +02:00 -> UTC
    assert s[2].uri == "https://manifest.example/api/hls_playlist/81236.ts"
    assert s[3].discontinuity and s[3].pdt is None               # never extrapolate across a discontinuity
    assert s[4].pdt == datetime(2026, 9, 25, 14, 20, 40, 250000, tzinfo=UTC)                   # PDT after EXTINF
    assert s[4].duration == 4.0 and s[4].pdt_end == datetime(2026, 9, 25, 14, 20, 44, 250000, tzinfo=UTC)
    assert parse_pdt("2026-09-25T20:46:35.029+0000") == datetime(2026, 9, 25, 20, 46, 35, 29000, tzinfo=UTC)
    assert parse_pdt("2026-09-25t20:46:35.123456789z").microsecond == 123456
    assert parse_pdt("2026-09-25T20:46:35") == datetime(2026, 9, 25, 20, 46, 35, tzinfo=UTC)
    with pytest.raises(ValueError):
        parse_pdt("yesterday")


def test_master_playlist_variant_choice():
    master = """#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=4500000,CODECS="avc1.4d401f,mp4a.40.2",RESOLUTION=1920x1080,FRAME-RATE=30
hls/1080.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2500000,CODECS="avc1.4d401f,mp4a.40.2",RESOLUTION=1280x720,FRAME-RATE=30
hls/720.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1200000,RESOLUTION=854x480
hls/480.m3u8
"""
    vs = parse_master_playlist(master, "https://x.example/live/master.m3u8")
    assert [v.height for v in vs] == [1080, 720, 480]
    v = choose_variant(vs, 720)
    assert v.height == 720 and v.uri == "https://x.example/live/hls/720.m3u8" and v.frame_rate == 30


def test_ts_scan_strips_sdt_and_finds_pts(tmp_path):
    ts = tmp_path / "wrap.ts"
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                    "testsrc=size=64x48:rate=10:duration=1", "-c:v", "mpeg2video", "-output_ts_offset", "95443",
                    "-f", "mpegts", str(ts)], check=True, capture_output=True, timeout=60)
    data = ts.read_bytes()
    info, payload = ts_scan(data)
    assert info.stripped > 0 and len(payload) == len(data) - 188 * info.stripped
    assert info.first_video90 is not None
    # 95443 s + 1.4 s mux preload = 95444.4 s -> past the 2**33 wrap (95443.717 s)
    expected = int(round((95443 + 1.4) * PTS_HZ)) % PTS_WRAP
    assert abs(((info.anchor90 - expected + PTS_WRAP // 2) % PTS_WRAP) - PTS_WRAP // 2) < 0.2 * PTS_HZ
    # stripped stream still decodes (the imageio build segfaults on the SDT otherwise)
    r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-f", "mpegts", "-i", "pipe:0", "-f", "null", "-"],
                       input=payload, capture_output=True, timeout=60)
    assert r.returncode == 0


def test_pts_time_map_wrap_representations():
    m = PtsTimeMap()
    anchor = PTS_WRAP - 90000 * 3            # 3 s before the wrap
    m.add(MapEntry(seq=1, anchor90=anchor, dur=5.0, pdt=1000.0, recv=2000.0, seen=1999.0))
    m.add(MapEntry(seq=2, anchor90=(anchor + 5 * 90000) % PTS_WRAP, dur=5.0, pdt=1005.0, recv=2005.0, seen=2004.0))
    raw = anchor / 90000 + 1.0                             # raw 33-bit seconds
    for rep in (raw, raw - PTS_WRAP / 90000):              # ffmpeg may report either (shifted by -2**33)
        e, d = m.lookup(rep)
        assert e.seq == 1 and abs(d - 1.0) < 1e-4
    e, d = m.lookup((anchor + 6.5 * 90000) % PTS_WRAP / 90000)    # after the wrap -> segment 2
    assert e.seq == 2 and abs(d - 1.5) < 1e-4 and abs(e.pdt + d - 1006.5) < 1e-4
    e, d = m.lookup(anchor / 90000 - 0.02)                 # leading audio just before the first anchor
    assert e.seq == 1 and -0.03 < d < 0
    assert m.lookup(None) == (None, None)


# ============================================================================ live pipeline (offline)
def test_live_segments_local_hls_pdt_timing(media, tmp_path):
    # PTS offset puts the 33-bit wrap ~5 s into the stream
    m3u8 = _encode_hls(media["clip"], tmp_path / "hls", seg_s=2, ts_offset=95437)
    pl = parse_media_playlist(m3u8.read_text(), str(m3u8))
    assert pl.endlist and pl.segments[0].pdt is not None
    pdt0 = pl.segments[0].pdt
    src = ingest.make_source({"type": "live", "url": str(m3u8), "reconnect": False, "archive": False,
                              "frame_interval_s": 5.0}, StreamClock(latency_s=99.0), {})
    items, frames, audio = _collect(src)
    src.close()
    assert len(frames) >= 4
    for f in frames:
        t_content = _content_time(f.image)
        assert abs((f.real_ts - pdt0).total_seconds() - t_content) < 0.12, (f.index, f.real_ts, t_content)
    # (the muxer stamped PDTs faster than real time, so only the first segment is surely "in the past")
    assert frames[0].capture_ts > frames[0].real_ts
    assert abs(sum(a.duration_s for a in audio) - CLIP_S) < 0.3
    assert abs((audio[0].real_ts - pdt0).total_seconds()) < 0.1
    snap = src.stats.snapshot()
    assert snap["decoder"] == "segments" and snap["timing"] == "pdt"
    assert snap["segments"] == len(pl.segments) and snap["latency_pdt_s"] is not None
    assert snap["bitrate_kbps"] > 0 and snap["segment_series"][0]["pdt"] == pdt0.timestamp()


def test_live_direct_mode_local_file(media):
    src = ingest.make_source({"type": "live", "url": str(media["clip"]), "mode": "direct", "reconnect": False,
                              "archive": False}, StreamClock(latency_s=20.0), {})
    items, frames, audio = _collect(src)
    src.close()
    assert len(frames) == 4 and abs(sum(a.duration_s for a in audio) - CLIP_S) < 0.1
    for f in frames:
        assert abs((f.capture_ts - f.real_ts).total_seconds() - 20.0) < 1e-6    # StreamClock latency
    d = [(frames[i].capture_ts - frames[0].capture_ts).total_seconds() for i in range(4)]
    assert d == sorted(d) and d[-1] < 5.0     # faster-than-real-time input: capture ~ arrival (no invented delay)
    assert src.stats.snapshot()["decoder"] == "direct"


def test_live_growing_playlist_detects_upstream_stall(media, tmp_path):
    """A writer publishes 1 s segments progressively with one 1.5 s pause -> 'upstream' stall, no data loss."""
    full = _encode_hls(media["clip"], tmp_path / "src", seg_s=1)
    pl = parse_media_playlist(full.read_text(), str(full))
    header, blocks = [], []
    lines = full.read_text().splitlines()
    cur = []
    for ln in lines:
        if ln.startswith("#EXT-X-ENDLIST"):
            continue
        if not blocks and not cur and not ln.startswith(("#EXTINF", "#EXT-X-PROGRAM-DATE-TIME")) and ln.startswith("#"):
            header.append(ln)
            continue
        cur.append(ln)
        if not ln.startswith("#"):
            blocks.append(cur)
            cur = []
    live = tmp_path / "src" / "live.m3u8"

    def publish(n, end=False):
        tmp = live.with_suffix(".tmp")
        tmp.write_text("\n".join(header + sum(blocks[:n], []) + (["#EXT-X-ENDLIST"] if end else [])) + "\n")
        os.replace(tmp, live)

    publish(3)
    pause_after = 8

    def writer():
        for n in range(4, len(blocks) + 1):
            time.sleep(1.6 if n == pause_after + 1 else 0.12)
            publish(n, end=(n == len(blocks)))

    th = threading.Thread(target=writer, daemon=True)
    th.start()
    src = ingest.make_source({"type": "live", "url": str(live), "reconnect": False, "archive": False,
                              "playlist_poll_s": 0.05, "stall_factor": 0.5, "min_stall_s": 0.6,
                              "live_start_segments": 3}, StreamClock(), {})
    items, frames, audio = _collect(src)
    th.join()
    src.close()
    snap = src.stats.snapshot()
    stalls = [e for e in snap["stall_events"] if e["kind"] == "upstream"]
    assert len(stalls) == 1, snap["stall_events"]
    ev = stalls[0]
    assert 0.6 < ev["duration_s"] < 2.0
    assert abs(ev["onsite_start"] - pl.segments[pause_after - 1].pdt_end.timestamp()) < 1e-3   # on the PDT clock
    assert snap["segments"] == len(pl.segments)
    assert abs(sum(a.duration_s for a in audio) - CLIP_S) < 0.3        # nothing lost
    lags = [s["lag_s"] for s in snap["segment_series"] if s.get("lag_s") is not None]
    assert lags and all(np.isfinite(lags))


# ============================================================================ stall bookkeeping (synthetic)
def _pl(first_seq, n, pdt0, dur=5.0, gap_at=None, gap_s=0.0):
    lines = ["#EXTM3U", "#EXT-X-TARGETDURATION:5", f"#EXT-X-MEDIA-SEQUENCE:{first_seq}"]
    t = pdt0
    for k in range(n):
        seq = first_seq + k
        if gap_at is not None and seq == gap_at:
            t += timedelta(seconds=gap_s)
        lines += [f"#EXT-X-PROGRAM-DATE-TIME:{t.isoformat()}", f"#EXTINF:{dur},", f"{seq}.ts"]
        t += timedelta(seconds=dur)
    return parse_media_playlist("\n".join(lines))


def test_segment_timeline_classifies_stalls_gaps_and_skips():
    st = StreamStats()
    pdt0 = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)
    T = pdt0.timestamp() + 45.0                  # newest segment (104, PDT end +25 s) seen 20 s later
    tl = SegmentTimeline(st, start_segments=3, stream_start=pdt0.timestamp() - 100 * 5.0 - 7.0)
    new = tl.on_playlist(_pl(100, 5, pdt0), T)
    assert [s.seq for s in new] == [102, 103, 104]            # live start: last 3 segments
    assert abs(st.edge_lag_s - (T - (pdt0.timestamp() + 25))) < 1e-6
    assert abs(st.media_deficit_s - 7.0) < 0.2                # 7 s of wall time never became media
    # normal cadence
    assert [s.seq for s in tl.on_playlist(_pl(101, 5, pdt0 + timedelta(seconds=5)), T + 5)] == [105]
    # playlist unchanged for 20 s while fetches succeed -> upstream stall
    for k in range(1, 8):
        tl.on_playlist(_pl(101, 5, pdt0 + timedelta(seconds=5)), T + 5 + 2.5 * k)
    assert st.state == "stalled" and st.current_stall_since == pytest.approx(T + 10)
    tl.on_playlist(_pl(103, 5, pdt0 + timedelta(seconds=15)), T + 25)
    ev = st.stall_events[-1]
    assert ev["kind"] == "upstream" and ev["duration_s"] == pytest.approx(15.0)
    assert ev["onsite_start"] == pytest.approx(pdt0.timestamp() + 30.0)          # end of seq 105 on PDT clock
    assert st.state == "streaming"
    # fetch errors during a pause -> local
    tl.on_fetch_error(T + 30, "timeout")
    tl.on_fetch_error(T + 33, "timeout")
    tl.on_playlist(_pl(105, 4, pdt0 + timedelta(seconds=25)), T + 40)
    assert st.stall_events[-1]["kind"] == "local"
    # PDT jumps 12 s between consecutive segments -> gap (media missing on site)
    new = tl.on_playlist(_pl(106, 4, pdt0 + timedelta(seconds=30), gap_at=109, gap_s=12.0), T + 45)
    assert [s.seq for s in new] == [109]
    gap = st.stall_events[-1]
    assert gap["kind"] == "gap" and gap["duration_s"] == pytest.approx(12.0)
    assert gap["onsite_start"] == pytest.approx(pdt0.timestamp() + 45.0) and gap["onsite_method"] == "pdt"
    # we fell behind: the playlist window moved past seq 110 -> skipped segments
    tl.on_playlist(_pl(115, 3, pdt0 + timedelta(seconds=87)), T + 60)
    assert st.segments_skipped == 5
    assert {e["kind"] for e in list(st.stall_events)[-2:]} == {"skip", "upstream"}   # 15 s without advance, too


# ============================================================================ small units
def test_item_queue_drops_oldest_frame_not_audio():
    st = StreamStats()
    q = ItemQueue(3, st)
    q.put(("frame", 1))
    q.put(("audio", 2))
    q.put(("frame", 3))
    q.put(("frame", 4))
    assert [q.get(0.1) for _ in range(3)] == [("audio", 2), ("frame", 3), ("frame", 4)]
    assert st.dropped_consumer == 1


def test_audio_chunker_and_receive_clock():
    ch = AudioChunker(16000, 1.0, min_partial_s=0.25)
    out = ch.push(np.full(10000, 16384, np.int16), 0) + ch.push(np.full(10000, -16384, np.int16), 10000)
    assert [(s, len(a)) for s, a in out] == [(0, 16000)]
    assert out[0][1][0] == pytest.approx(0.5) and out[0][1][-1] == pytest.approx(-0.5)
    s, a = ch.flush()
    assert s == 16000 and len(a) == 4000
    rc = ReceiveClock(window_s=60)
    # a burst: 3 frames of one segment arrive together 2 s late; the first arrived on time
    assert rc.observe(0.0, 100.0) == 100.0
    assert rc.observe(1.0, 103.0) == pytest.approx(101.0)
    assert rc.observe(2.0, 103.0) == pytest.approx(102.0)


def test_ytdlp_info_and_url_helpers():
    info = {"id": "EQHgfmZicc8", "is_live": True, "release_timestamp": 1790059800, "format_id": "95",
            "url": "https://manifest.googlevideo.com/api/manifest/hls_playlist/expire/1790100000/ei/x/index.m3u8",
            "protocol": "m3u8_native", "width": 1280, "height": 720, "fps": 30,
            "http_headers": {"User-Agent": "Mozilla/5.0"}}
    r = stream_from_ytdlp_info(info, "https://www.youtube.com/watch?v=EQHgfmZicc8")
    assert r.protocol == "hls" and r.key == "EQHgfmZicc8" and r.expires_at == 1790100000
    assert r.release_ts == 1790059800 and r.height == 720 and r.audio_url is None
    split = {"id": "v", "requested_formats": [
        {"url": "https://a/v.m3u8", "protocol": "m3u8_native", "vcodec": "avc1", "acodec": "none", "height": 720},
        {"url": "https://a/a.m3u8", "protocol": "m3u8_native", "vcodec": "none", "acodec": "mp4a"}]}
    r2 = stream_from_ytdlp_info(split)
    assert r2.url.endswith("v.m3u8") and r2.audio_url.endswith("a.m3u8")
    with pytest.raises(ResolveError):
        stream_from_ytdlp_info({"url": "https://a/b", "protocol": "http_dash_segments_generator"})
    assert expiry_from_url("https://x/videoplayback?expire=1790000000&sig=1") == 1790000000
    assert "sig" not in redact_url("https://rr1.googlevideo.com/videoplayback?expire=1&sig=SECRET")
    assert redact_url("https://www.youtube.com/watch?v=EQHgfmZicc8").endswith("EQHgfmZicc8")
    loc = resolve_stream("/data/cuts/x.m3u8")
    assert loc.resolver == "direct" and loc.protocol == "hls"


# ============================================================================ stream_health analyzer
T_BASE = 1790059800.0      # 2026-09-22 06:50 UTC-ish; a multiple of 60


def _starlink_stats(n=24, seed=3):
    rng = np.random.default_rng(seed)
    st = StreamStats()
    st.update(timing="pdt", latency_pdt_s=18.0, bitrate_kbps=2500.0, fps_in=30.0, resolution="1280x720",
              decoder="segments", pdt_offset_s=0.0)
    slots = np.sort(rng.choice(np.arange(0, 2 * 3600 // 15), n, replace=False))
    for k in slots:
        onsite = T_BASE + 15.0 * k + 12.0 + rng.normal(0, 0.7)       # slot boundaries :12 :27 :42 :57
        dur = float(rng.uniform(1.0, 8.0))
        st.add_stall("gap", start=onsite, end=onsite + dur, onsite_start=onsite, onsite_method="pdt", seq=int(k))
    for i in range(30):
        st.add_segment(seq=i, pdt=T_BASE + 5.0 * i, dur=5.0, seen=T_BASE + 5.0 * i + 20.0, recv=T_BASE + 5 * i + 20.5,
                       dl_s=0.4, bytes=1_500_000, lag_s=15.0 + 0.1 * (i % 3))
    return st


def test_stream_health_detects_starlink_like_periodic_stalls():
    st = _starlink_stats()
    a = StreamHealthAnalyzer({})
    assert a.name == "stream_health" and a.tick_interval_s == 60.0
    now = T_BASE + 7300.0
    obs = a.process(st.snapshot(), StreamClock(), now=now)
    kinds = [o.kind for o in obs]
    assert all(k in KINDS for k in kinds)
    assert kinds.count("stream_stall") == 24 and "stream_health" in kinds and "stream_latency" in kinds
    stall = next(o for o in obs if o.kind == "stream_stall")
    assert abs(stall.value["phase_mod_period_s"] - 12.0) < 3.0 and stall.value["onsite_method"] == "pdt"
    assert abs(stall.ts.timestamp() - stall.value["onsite_start"]) < 1e-3
    health = next(o for o in obs if o.kind == "stream_health").value
    assert health["resolution"] == "1280x720" and health["new_stalls"] == 24 and health["stall_s"] > 24
    assert len(health["lag_series"]) == 30
    lat = next(o for o in obs if o.kind == "stream_latency").value
    assert lat["latency_s"] == 18.0 and lat["method"] == "hls_program_date_time"
    sig = next(o for o in obs if o.kind == "uplink_signature")
    assert sig.value["verdict"] == "starlink_like", sig.value
    assert sig.value["rayleigh_p"] < 1e-4 and sig.value["phase_dist_s"] < 2.0
    assert abs(sig.value["best_period_s"] - 15.0) < 0.3 or sig.value["interval_multiple_frac"] > 0.8
    assert 0.5 <= sig.confidence <= 0.75
    # incremental: a second tick 60 s later without new events emits no duplicate stalls / signature
    obs2 = a.process(st.snapshot(), StreamClock(), now=now + 60)
    assert [o.kind for o in obs2 if o.kind == "stream_stall"] == []
    assert "uplink_signature" not in [o.kind for o in obs2]
    assert next(o for o in obs2 if o.kind == "stream_health").value["stall_s"] == 0.0


def test_stream_health_cellular_and_random_are_not_starlink():
    rng = np.random.default_rng(7)
    st = StreamStats()
    t = T_BASE + np.cumsum(rng.exponential(1200.0, 8))
    for x in t:
        d = float(rng.uniform(25, 120))
        st.add_stall("upstream", start=x + 25.0, end=x + 25.0 + d, onsite_start=float(x), onsite_method="pdt")
    a = StreamHealthAnalyzer({"min_events": 6})
    sig = next(o for o in a.process(st.snapshot(), StreamClock(), now=float(t[-1]) + 600) if o.kind == "uplink_signature")
    assert sig.value["verdict"] == "cellular_like" and sig.confidence <= 0.45
    # random short stalls: no verdict
    tr = T_BASE + np.sort(rng.uniform(0, 7200, 25))
    ev = [(float(x), float(rng.uniform(1, 6)), True) for x in tr]
    assert classify_uplink(ev)["verdict"] == "unknown"
    # stats helpers
    r = rayleigh([T_BASE + 15 * k + 12 for k in range(10)], 15.0)
    assert r["R"] > 0.99 and r["p"] < 1e-3 and abs(r["phase_s"] - 12.0) < 0.01
    imt = interval_multiple_test([T_BASE + 15 * k for k in (0, 2, 3, 7, 11, 12, 20)], 15.0)
    assert imt["frac"] == 1.0 and imt["p"] < 0.01


def test_stream_health_reads_published_stats_from_ctx_state():
    ctx = Context(db=None, config={}, clock=StreamClock(latency_s=25.0))
    a = StreamHealthAnalyzer({})
    assert a.on_frame(None, ctx) == []              # first call subscribes ctx.state to the ingest bus
    st = StreamStats(mode="live")
    st.add_callback(ingest.publish_stats)
    st.update(bitrate_kbps=900.0, resolution="1280x720", fps_in=25.0)
    st.add_stall("upstream", start=time.time() - 30, end=time.time() - 20)
    st.publish()
    assert ctx.state["ingest_stats"]["bitrate_kbps"] == 900.0 and ctx.state["ingest"] is ctx.state["ingest_stats"]
    obs = a.on_tick(ctx)
    h = next(o for o in obs if o.kind == "stream_health")
    assert h.value["bitrate_kbps"] == 900.0 and h.value["new_stalls"] == 1
    s = next(o for o in obs if o.kind == "stream_stall")
    assert s.value["onsite_method"] == "capture_minus_latency"       # no PDT: capture - clock latency
    assert abs(s.value["onsite_start"] - (st.stall_events[0]["start"] - 25.0)) < 2e-3


def test_runner_end_to_end_with_replay(media, tmp_path):
    from hordewatch.runner import load_config, run
    cfg = load_config(None)
    cfg.update(db=str(tmp_path / "hw.sqlite"), archive_dir=str(tmp_path / "arch"), analyzers=["stream_health"],
               source={"type": "replay", "files": [str(media["clip"])], "frame_interval_s": 5.0,
                       "audio_chunk_s": 10.0, "archive_every_n_frames": 12})
    db = run(cfg)
    n_frames = db.con.execute("SELECT COUNT(*) FROM frames").fetchone()[0]
    n_audio = db.con.execute("SELECT COUNT(*) FROM audio").fetchone()[0]
    assert n_frames == 4 and n_audio == 2
    first = db.con.execute("SELECT real_ts, path FROM frames ORDER BY id LIMIT 1").fetchone()
    assert first[0].startswith("2026-09-25T14:20:00") and first[1].endswith("142000_0.jpg")
    kinds = {o["kind"] for o in db.observations()}
    assert "stream_health" in kinds


def test_live_adapts_to_stream_without_audio(media, tmp_path):
    silent = tmp_path / "silent.mp4"
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", "-i", str(media["clip"]), "-an", "-c", "copy",
                    str(silent)], check=True, capture_output=True, timeout=60)
    src = ingest.make_source({"type": "live", "url": str(silent), "mode": "direct", "reconnect": True,
                              "max_reconnects": 1, "backoff_initial_s": 0.05, "archive": False}, StreamClock(), {})
    items, frames, audio = _collect(src)
    src.close()
    assert len(frames) == 4 and audio == []           # 1st session fails (no audio stream), 2nd runs video-only
    snap = src.stats.snapshot()
    assert snap["reconnects"] == 1 and "matches no streams" in (snap["last_error"] or "")
