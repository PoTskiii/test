"""Offline tests for the vision analyzers (whiteboard, vlm, scene, gesture) on synthetic data."""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import numpy as np
import pytest

from hordewatch.analyzers.base import Context
from hordewatch.db import DB
from hordewatch.types import Frame, StreamClock

T0 = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
W, H = 1280, 720


# ----------------------------------------------------------------------------------- synthetic scenes
def forest(seed=0, w=W, h=H):
    """Forest-ish background: low-frequency green/brown blotches + fine texture + hazy sky strip."""
    rng = np.random.default_rng(seed)
    low = cv2.resize(rng.normal(0, 1, (h // 16 + 1, w // 16 + 1, 3)).astype(np.float32), (w, h),
                     interpolation=cv2.INTER_CUBIC)
    hi = rng.normal(0, 1, (h, w, 3)).astype(np.float32)
    img = np.array([70, 95, 55], np.float32) + 25 * low + 14 * cv2.GaussianBlur(hi, (0, 0), 1.2)
    img[:100] = np.array([150, 160, 170], np.float32) + 10 * low[:100]
    return np.clip(img, 0, 255)


def noisy(base, rng, gain=1.0, sigma=3.0):
    return np.clip(base * gain + rng.normal(0, sigma, base.shape), 0, 255).astype(np.uint8)


def board_img(lines=("INGEN STIER", "KAMERA 41 OST")):
    b = np.full((400, 600, 3), 238, np.uint8)
    y = 150
    for t in lines:
        cv2.putText(b, t, (30, y), cv2.FONT_HERSHEY_SIMPLEX, 1.9, (25, 25, 30), 5, cv2.LINE_AA)
        y += 140
    return b


def place_board(frame, board, center=(700, 420), width=420, tilt_deg=9.0, persp=0.06):
    bh, bw = board.shape[:2]
    hh = width * bh / bw
    pts = np.array([[-width / 2, -hh / 2], [width / 2, -hh / 2 * (1 - persp)],
                    [width / 2, hh / 2 * (1 - persp)], [-width / 2, hh / 2]])
    a = np.deg2rad(tilt_deg)
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    dst = (pts @ R.T + np.array(center, float)).astype(np.float32)
    src = np.array([[0, 0], [bw, 0], [bw, bh], [0, bh]], np.float32)
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(board, M, (frame.shape[1], frame.shape[0]))
    mask = cv2.warpPerspective(np.full((bh, bw), 255, np.uint8), M, (frame.shape[1], frame.shape[0]))
    out = frame.copy()
    out[mask > 128] = warped[mask > 128]
    return out, dst


def arrow_poly(x, y, L=300, T=40, head=80, headlen=70):
    return np.array([[x, y - T // 2], [x + L - headlen, y - T // 2], [x + L - headlen, y - head // 2], [x + L, y],
                     [x + L - headlen, y + head // 2], [x + L - headlen, y + T // 2], [x, y + T // 2]], np.int32)


JACKET, SKIN, PANTS = (40, 50, 120), (215, 160, 130), (30, 30, 35)


def stick_figure(img, cx=640, top=200, arm="down", angle=30.0, side="right", L=160):
    """Human-proportioned 'stick figure': skin head, jacket torso, thick limbs, skin hands."""
    head_r = 24
    cv2.circle(img, (cx, top + head_r), head_r, SKIN, -1)
    t0 = top + 2 * head_r + 4
    tw, th = 84, 160
    cv2.ellipse(img, (cx, t0 + th // 2), (tw // 2, th // 2), 0, 0, 360, JACKET, -1)
    cv2.rectangle(img, (cx - tw // 2, t0 + 10), (cx + tw // 2, t0 + th - 20), JACKET, -1)
    for dx in (-22, 22):
        cv2.line(img, (cx + dx, t0 + th - 10), (cx + dx * 2, t0 + th + 170), PANTS, 26)
    shoulders = {"left": (cx - tw // 2 + 6, t0 + 14), "right": (cx + tw // 2 - 6, t0 + 14)}
    for s, (x0, y0) in shoulders.items():
        sg = -1 if s == "left" else 1
        if arm == "up" and s == side:
            a = np.deg2rad(angle)
            x1, y1 = int(x0 + sg * L * np.sin(a)), int(y0 - L * np.cos(a))
        elif arm == "horizontal" and s == side:
            x1, y1 = x0 + sg * L, y0
        else:
            x1, y1 = x0 + sg * 30, y0 + L - 10
        cv2.line(img, (x0, y0), (x1, y1), JACKET, 20)
        cv2.circle(img, (x1, y1), 12, SKIN, -1)
    return img


def mk_frame(i, img, db=None, dt=5.0, latency=30.0):
    cap = T0 + timedelta(seconds=dt * i)
    f = Frame(index=i, capture_ts=cap, real_ts=cap - timedelta(seconds=latency), image=img, source="test")
    if db is not None:
        db.add_frame(f)
    else:
        f.id = i + 1
    return f


def mk_ctx(db=None, **cfg):
    return Context(db=db, config={"camera": {"heading_deg": 220.0}, **cfg}, clock=StreamClock())


def run_frames(an, ctx, frames, db=None):
    """Mini runner: call on_frame, persist observations, collect them."""
    out = []
    for f in frames:
        obs = an.on_frame(f, ctx)
        for o in obs:
            if db is not None:
                db.add_observation(o)
            out.append((f.index, o))
    return out


def events(db):
    return db.con.execute("SELECT kind, summary, value FROM events ORDER BY id").fetchall()


# ----------------------------------------------------------------------------------- whiteboard
wb = pytest.importorskip("hordewatch.analyzers.whiteboard")


def test_fix_norwegian_restores_letters():
    assert wb.fix_norwegian("KAMERA 41 0ST")[0] == "KAMERA 41 ØST"
    assert wb.fix_norwegian("KAMERA410ST")[0] == "KAMERA 41 ØST"
    assert wb.fix_norwegian("NAR SOLA ER I S0R")[0] == "NÅR SOLA ER I SØR"
    assert wb.fix_norwegian("HOYDE 4O0 M")[0] == "HØYDE 400 M"
    assert wb.fix_norwegian("Gå 300 m mot OST")[0] == "Gå 300 m mot ØST"
    # ambiguous real words without directional context are left alone
    assert wb.fix_norwegian("OST OG BROD")[0] == "OST OG BROD"
    assert wb.fix_norwegian("HΦYSPENT")[0] == "HØYSPENT"
    assert wb.fix_norwegian("E6 NORD")[0] == "E6 NORD"


def test_text_similarity_and_clock():
    assert wb.board_similarity("INGEN STIER\nKAMERA 41 ØST", "INGENSTIER KAMERA410ST") > 0.9
    assert wb.board_similarity("INGEN STIER", "SOL I SØR") < 0.5
    assert wb.find_clock("KL 14.30 VED BEKKEN") == ["14:30"]
    assert wb.find_clock("60.123 N 10:05") == ["10:05"]


def test_detect_rectify_and_ocr_board():
    rng = np.random.default_rng(1)
    frame, corners = place_board(noisy(forest(), rng), board_img())
    cands = wb.detect_boards(frame)
    assert cands, "board not detected"
    c = cands[0]
    xs, ys = corners[:, 0], corners[:, 1]
    true_bbox = (xs.min(), ys.min(), xs.max(), ys.max())
    assert wb.bbox_iou(c.bbox, true_bbox) > 0.8
    crop = wb.rectify(frame, c.corners)
    assert crop.shape[1] > crop.shape[0]            # landscape board stays landscape
    read = wb.read_board(crop, rapid=wb.get_rapidocr())
    assert read is not None
    text = read.text.upper()
    for word in ("INGEN", "STIER", "KAMERA", "41"):
        assert word in text.replace(" ", "") or word in text, text
    assert "ØST" in text or "OST" in text, text
    assert read.conf > 0.7


def test_no_board_in_plain_forest():
    rng = np.random.default_rng(2)
    for seed in range(3):
        assert wb.detect_boards(noisy(forest(seed), rng)) == []


def test_small_board_realistic_size():
    rng = np.random.default_rng(3)
    frame, _ = place_board(noisy(forest(4), rng), board_img(), center=(600, 400), width=140, tilt_deg=-6)
    cands = wb.detect_boards(frame)
    assert cands and 100 <= cands[0].bbox[2] - cands[0].bbox[0] <= 200


def test_whiteboard_analyzer_merge_dedup_events(tmp_path):
    db = DB(tmp_path / "hw.sqlite")
    ctx = mk_ctx(db)
    an = wb.WhiteboardAnalyzer({})
    assert an.available()
    rng = np.random.default_rng(5)
    base = forest(7)
    bg = lambda: noisy(base, rng)                                         # noqa: E731
    shown = lambda **kw: place_board(noisy(base, rng), board_img(), **kw)[0]   # noqa: E731
    seq = [bg(), bg(), shown(), shown(center=(705, 418)), shown(center=(710, 425), tilt_deg=7), bg(), bg(), bg()]
    frames = [mk_frame(i, img, db) for i, img in enumerate(seq)]
    obs = []
    triggered_at = []
    for f in frames:
        for o in an.on_frame(f, ctx):
            db.add_observation(o)
            obs.append((f.index, o))
        if "whiteboard" in ctx.triggers:
            triggered_at.append(f.index)
            assert isinstance(ctx.state["whiteboard"]["crop"], np.ndarray)
            assert ctx.state.get("archive_next") is True
    vis = [o for _, o in obs if o.kind == "whiteboard_visible"]
    txt = [o for _, o in obs if o.kind == "whiteboard_text"]
    assert len(vis) == 1 and vis[0].ts == frames[3].real_ts          # confirmed on the 2nd board frame
    assert triggered_at and triggered_at[0] == 3
    assert len(txt) == 1, [o.value["text"] for o in txt]
    v = txt[0].value
    assert v["is_new"] is True and v["n_reads"] >= 2
    assert txt[0].ts == frames[2].real_ts                              # stamped with the first sighting
    flat = v["text"].replace(" ", "").upper()
    assert "INGENSTIER" in flat and "KAMERA" in flat and "41" in flat
    assert "ØST" in v["text"] or "OST" in v["text"]
    assert len(events(db)) == 1

    # same board held up again later -> recorded as a repeat, not re-announced
    seq2 = [shown(center=(650, 400), tilt_deg=-5), shown(center=(655, 402), tilt_deg=-4), shown(center=(652, 398)),
            bg(), bg(), bg()]
    frames2 = [mk_frame(10 + i, img, db) for i, img in enumerate(seq2)]
    obs2 = run_frames(an, ctx, frames2, db)
    txt2 = [o for _, o in obs2 if o.kind == "whiteboard_text"]
    assert len(txt2) == 1
    assert txt2[0].value["is_new"] is False and txt2[0].value["repeat_of"] == txt[0].id
    assert len(events(db)) == 1

    # a restarted analyzer knows the board from the DB
    an2 = wb.WhiteboardAnalyzer({})
    frames3 = [mk_frame(20 + i, img, db) for i, img in enumerate([shown(), shown(), shown(), bg(), bg(), bg()])]
    obs3 = run_frames(an2, mk_ctx(db), frames3, db)
    assert [o.value["is_new"] for _, o in obs3 if o.kind == "whiteboard_text"] == [False]
    assert len(events(db)) == 1

    # genuinely new text -> new event
    new_board = lambda: place_board(noisy(base, rng), board_img(("SOL I SOR", "KL 14:30")))[0]  # noqa: E731
    frames4 = [mk_frame(30 + i, img, db) for i, img in enumerate([new_board(), new_board(), new_board(), bg(), bg()])]
    obs4 = run_frames(an2, mk_ctx(db), frames4, db)
    t4 = [o for _, o in obs4 if o.kind == "whiteboard_text"]
    assert len(t4) == 1 and t4[0].value["is_new"] is True
    assert "SØR" in t4[0].value["text"] or "SOR" in t4[0].value["text"]
    ev = events(db)
    assert len(ev) == 2 and ev[-1][0] == "whiteboard_text"
    clocks = [o for _, o in obs4 if o.kind == "clock_seen"]
    assert clocks and clocks[0].value["shown_time"] == "14:30"


def test_whiteboard_transient_not_announced_and_trigger_expires():
    ctx = mk_ctx(None)
    an = wb.WhiteboardAnalyzer({"ocr": False})
    rng = np.random.default_rng(9)
    base = forest(3)
    seq = [noisy(base, rng), place_board(noisy(base, rng), board_img())[0], noisy(base, rng), noisy(base, rng)]
    obs = run_frames(an, ctx, [mk_frame(i, im) for i, im in enumerate(seq)])
    assert not obs                                              # one-frame flash: no board
    # confirmed board: trigger fires, and expires if no VLM consumes it
    seq = [place_board(noisy(base, rng), board_img())[0] for _ in range(2)] + [noisy(base, rng)] * 4
    frames = [mk_frame(10 + i, im) for i, im in enumerate(seq)]
    seen = []
    for f in frames:
        an.on_frame(f, ctx)
        seen.append("whiteboard" in ctx.triggers)
    assert seen[1] is True and seen[-1] is False


def test_whiteboard_survives_h264_roundtrip(tmp_path):
    """Encode a tiny clip with the bundled ffmpeg (YouTube-like compression) and analyse the decoded frames."""
    imageio_ffmpeg = pytest.importorskip("imageio_ffmpeg")
    rng = np.random.default_rng(11)
    base = forest(8)
    imgs = [noisy(base, rng)] + [place_board(noisy(base, rng), board_img())[0] for _ in range(3)] + \
        [noisy(base, rng)] * 3
    path = str(tmp_path / "clip.mp4")
    w = imageio_ffmpeg.write_frames(path, (W, H), fps=1, codec="libx264", quality=6, macro_block_size=16,
                                    pix_fmt_out="yuv420p", ffmpeg_log_level="error")
    w.send(None)
    for im in imgs:
        w.send(np.ascontiguousarray(im))
    w.close()
    rd = imageio_ffmpeg.read_frames(path)
    meta = rd.__next__()
    decoded = [np.frombuffer(b, np.uint8).reshape(meta["size"][1], meta["size"][0], 3).copy() for b in rd]
    assert len(decoded) == len(imgs)
    an = wb.WhiteboardAnalyzer({})
    obs = run_frames(an, mk_ctx(None), [mk_frame(i, im) for i, im in enumerate(decoded)])
    txt = [o for _, o in obs if o.kind == "whiteboard_text"]
    assert txt and "KAMERA" in txt[0].value["text"].replace(" ", "")


# ----------------------------------------------------------------------------------- VLM
vlm = pytest.importorskip("hordewatch.analyzers.vlm")

BOARD_ANSWER = ('Sure! Here is the transcription:\n```json\n{"lines": ["INGEN STIER", "KAMERA 41 ØST"], '
                '"text": "INGEN STIER\\nKAMERA 41 ØST", "language": "no", "legible": true, "confidence": 0.8, '
                '"drawings": "arrow pointing left"}\n```')
SCENE_ANSWER = ('{"sky": "overcast", "precipitation": "drizzle", "sunlight_direct": false, '
                '"shadows_direction": "none", "anja_activity": "pointing at the sky", "pointing_up": true, '
                '"objects_new": ["wooden sign"], "signs_text": ["HORDE"], "hands_or_signs_near_box": false, '
                '"notable": "",}')


class _MockVLM(BaseHTTPRequestHandler):
    requests = []
    models = ["llava:7b"]

    def log_message(self, *a):
        pass

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/tags":
            self._send({"models": [{"name": m, "model": m} for m in self.models]})
        elif self.path == "/v1/models":
            self._send({"data": [{"id": "local"}]})
        else:
            self._send({"error": "nf"}, 404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).requests.append((self.path, body))
        time.sleep(0.05)
        if self.path == "/api/chat":
            msg = body["messages"][0]
            assert msg["images"] and isinstance(msg["images"][0], str)
            prompt = msg["content"]
            self._send({"message": {"role": "assistant",
                                    "content": BOARD_ANSWER if "whiteboard" in prompt.lower() else SCENE_ANSWER}})
        elif self.path == "/v1/chat/completions":
            parts = body["messages"][0]["content"]
            assert parts[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
            prompt = parts[0]["text"]
            self._send({"choices": [{"message": {"content": BOARD_ANSWER if "whiteboard" in prompt.lower()
                                                 else SCENE_ANSWER}}]})
        else:
            self._send({"error": "nf"}, 404)


@pytest.fixture
def mock_vlm_server():
    _MockVLM.requests = []
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _MockVLM)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def test_extract_json_robust():
    assert vlm.extract_json(BOARD_ANSWER)["lines"][1] == "KAMERA 41 ØST"
    assert vlm.extract_json(SCENE_ANSWER)["sky"] == "overcast"            # trailing comma repaired
    assert vlm.extract_json("Answer: {'sky': 'clear', 'pointing_up': True}") == {"sky": "clear", "pointing_up": True}
    assert vlm.extract_json('prefix {"a": "x}y", "b": {"c": 1}} suffix') == {"a": "x}y", "b": {"c": 1}}
    assert vlm.extract_json('{"a": 1, "b": [1, 2]') == {"a": 1, "b": [1, 2]}  # unterminated
    assert vlm.extract_json("no json here") is None


def _vlm_run(an, ctx, db, crop_frame):
    f0 = mk_frame(0, crop_frame, db)
    ctx.state["whiteboard"] = {"crop": crop_frame[300:560, 480:900].copy(), "track_id": 1, "ts": f0.real_ts,
                               "frame_id": f0.id, "bbox": [480, 300, 900, 560]}
    ctx.trigger("whiteboard")
    t = time.perf_counter()
    first = an.on_frame(f0, ctx)
    dt = time.perf_counter() - t
    assert "whiteboard" not in ctx.triggers                  # consumed
    assert an.flush(10)
    out = list(first) + an.on_tick(ctx)
    f1 = mk_frame(1, crop_frame, db)
    out += an.on_frame(f1, ctx)
    assert an.flush(10)
    out += an.on_tick(ctx)
    return f0, out, dt


def test_vlm_ollama_mock(mock_vlm_server, tmp_path):
    db = DB(tmp_path / "v.sqlite")
    ctx = mk_ctx(db)
    an = vlm.VLMAnalyzer({"_global": {"vlm": {"backend": "ollama", "url": mock_vlm_server, "model": "llava:7b"}},
                          "scene_every_s": 0})
    assert an.available()
    img = place_board(noisy(forest(), np.random.default_rng(0)), board_img())[0]
    f0, out, dt = _vlm_run(an, ctx, db, img)
    assert dt < 0.2, f"on_frame blocked for {dt:.3f}s"
    kinds = [o.kind for o in out]
    board = [o for o in out if o.kind == "whiteboard_text"]
    assert len(board) == 1
    assert board[0].value["text"] == "INGEN STIER\nKAMERA 41 ØST" and board[0].value["source"] == "vlm"
    assert board[0].ts == f0.real_ts and board[0].analyzer == "vlm" and board[0].confidence <= 0.6
    assert ctx.state["vlm_whiteboard"][1]["text"].startswith("INGEN")
    assert kinds.count("vlm_description") == 2
    cf = [o for o in out if o.kind == "cloud_fraction"]
    assert cf and cf[0].value["fraction"] > 0.9 and cf[0].value["method"] == "vlm"
    rain = [o for o in out if o.kind == "rain_visual"]
    assert rain and rain[0].value["present"] is True and rain[0].value["type"] == "drizzle"
    assert any(o.kind == "gesture_point_up" for o in out) and "aircraft_check" in ctx.triggers
    assert any(o.kind == "object_appeared" and o.value["label"] == "wooden sign" for o in out)
    assert any(o.kind == "direct_sun" and o.value["present"] is False for o in out)
    for o in out:
        db.add_observation(o)
    ev = events(db)
    assert len(ev) == 1 and ev[0][0] == "whiteboard_text_vlm"
    paths = [p for p, _ in _MockVLM.requests]
    assert paths.count("/api/chat") == 2
    assert _MockVLM.requests[0][1]["format"] == "json"
    an.close()


def test_vlm_openai_compatible_mock(mock_vlm_server):
    ctx = mk_ctx(None)
    an = vlm.VLMAnalyzer({"_global": {"vlm": {"backend": "openai", "url": mock_vlm_server + "/v1", "model": "local"}},
                          "scene_every_s": -1})
    assert an.available()
    img = noisy(forest(), np.random.default_rng(0))
    _, out, _ = _vlm_run(an, ctx, None, img)
    assert [o.kind for o in out].count("whiteboard_text") == 1
    assert all(p == "/v1/chat/completions" for p, _ in _MockVLM.requests)
    assert len(_MockVLM.requests) == 1                     # scene prompts disabled with scene_every_s < 0
    an.close()


def test_vlm_unavailable_fails_fast_and_model_missing(mock_vlm_server):
    s = socket_free_port()
    an = vlm.VLMAnalyzer({"_global": {"vlm": {"url": f"http://127.0.0.1:{s}"}}, "ping_timeout_s": 1.0})
    t = time.perf_counter()
    assert an.available() is False
    assert time.perf_counter() - t < 3.0
    assert "unreachable" in an.client.reason
    an2 = vlm.VLMAnalyzer({"_global": {"vlm": {"url": mock_vlm_server, "model": "qwen2.5vl:7b"}}})
    assert an2.available() is False and "ollama pull" in an2.client.reason


def socket_free_port():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# ----------------------------------------------------------------------------------- scene
scene = pytest.importorskip("hordewatch.analyzers.scene")


def test_arrow_shape_direction():
    m = np.zeros((200, 400), np.uint8)
    cv2.fillPoly(m, [arrow_poly(40, 100)], 1)
    s = scene.arrow_shape(m.astype(bool))
    assert s["arrow_score"] > 0.6 and s["elongation"] > 3
    assert min(s["points_to_deg_image"], 360 - s["points_to_deg_image"]) < 10     # points right
    m2 = np.zeros((200, 400), np.uint8)
    cv2.rectangle(m2, (40, 80), (340, 120), 1, -1)
    assert scene.arrow_shape(m2.astype(bool))["arrow_score"] < 0.2


def test_scene_brown_arrow_appears_and_is_removed():
    an = scene.SceneChangeAnalyzer({})
    ctx = mk_ctx(None)
    rng = np.random.default_rng(5)
    base = forest()
    frames = []
    for i in range(16):
        img = noisy(base, rng, gain=1.0 + 0.08 * np.sin(i))
        if 6 <= i < 12:
            cv2.fillPoly(img, [arrow_poly(200, 560)], (125, 80, 40))
        if i == 9:
            img = np.clip(img.astype(np.float32) * 0.55, 0, 255).astype(np.uint8)   # cloud / exposure drop
        frames.append(mk_frame(i, img))
    obs = run_frames(an, ctx, frames)
    objs = [(i, o) for i, o in obs if o.kind == "object_appeared"]
    assert len(objs) == 2, [(i, o.value) for i, o in objs]
    (i1, o1), (i2, o2) = objs
    assert i1 == 8 and o1.value["label"] == "horde_sign" and o1.value["appeared"] is True
    assert o1.ts == frames[6].real_ts                        # onset = first frame with the sign
    assert o1.value["onset_window"][0] == frames[5].real_ts.isoformat(timespec="milliseconds")
    assert wb.bbox_iou(o1.value["bbox"], (200, 520, 500, 600)) > 0.6
    assert o1.value["shape"]["arrow_score"] > 0.5
    pd = o1.value["shape"]["points_to_deg_image"]
    assert min(pd, 360 - pd) < 15
    assert i2 == 14 and o2.value["appeared"] is False and o2.value["label"] == "horde_sign"
    assert sum(o.kind == "scene_change" for _, o in obs) == 2
    assert not any(o.kind == "scene_change" and o.value.get("global") for _, o in obs)


def test_scene_ir_switch_and_camera_wobble_are_not_objects():
    an = scene.SceneChangeAnalyzer({})
    ctx = mk_ctx(None)
    rng = np.random.default_rng(6)
    base = forest(2)
    imgs = [noisy(base, rng) for _ in range(6)]
    # camera wobble by 2 px
    M = np.float32([[1, 0, 2], [0, 1, 1]])
    imgs += [cv2.warpAffine(noisy(base, rng), M, (W, H), borderMode=cv2.BORDER_REFLECT) for _ in range(4)]
    # night: IR mode (grey, different illumination)
    grey = cv2.cvtColor(noisy(base * 0.7, rng), cv2.COLOR_RGB2GRAY)
    imgs += [np.dstack([np.clip(grey + rng.normal(0, 2, grey.shape), 0, 255).astype(np.uint8)] * 3) for _ in range(8)]
    frames = [mk_frame(i, im) for i, im in enumerate(imgs)]
    obs = run_frames(an, ctx, frames)
    assert not [o for _, o in obs if o.kind == "object_appeared"], [o.value for _, o in obs]
    sw = [(i, o) for i, o in obs if o.kind == "ir_mode_switch"]
    assert len(sw) == 1 and sw[0][1].value["to_ir"] is True and sw[0][1].ts == frames[10].real_ts


def test_scene_excludes_person_bbox_and_detects_hand_in_heather():
    an = scene.SceneChangeAnalyzer({})
    ctx = mk_ctx(None)
    rng = np.random.default_rng(8)
    base = forest(5)
    obs = []
    for i in range(12):
        img = noisy(base, rng)
        if i >= 5:
            cv2.rectangle(img, (560, 200), (720, 520), (40, 50, 120), -1)          # person-sized blob, excluded
            cv2.ellipse(img, (300, 620), (28, 18), 20, 0, 360, SKIN, -1)           # hand in the heather
        ctx.state["person_bbox"] = {"bbox": [560, 200, 720, 520], "frame_index": i}
        obs += run_frames(an, ctx, [mk_frame(i, img)])
    objs = [o for _, o in obs if o.kind == "object_appeared"]
    assert len(objs) == 1, [o.value for o in objs]
    assert objs[0].value["label"] == "hand_in_heather"


# ----------------------------------------------------------------------------------- gesture
gesture = pytest.importorskip("hordewatch.analyzers.gesture")


def _gesture_seq(an, ctx, pose, n_bg=6, seed=3):
    rng = np.random.default_rng(seed)
    base = forest()
    seq = ["bg"] * n_bg + ["down"] * 2 + [pose] * 2 + ["down"] * 2
    frames, obs = [], []
    for i, what in enumerate(seq):
        img = noisy(base, rng)
        if what == "down":
            stick_figure(img)
        elif what != "bg":
            stick_figure(img, arm=what[0], angle=what[1], side=what[2])
        f = mk_frame(i, img)
        frames.append(f)
        obs += [(i, o) for o in an.on_frame(f, ctx)]
    return frames, obs


def test_gesture_fallback_distinguishes_arm_up_from_down():
    an = gesture.GestureAnalyzer({"_global": {"camera": {"heading_deg": 220.0}}})
    assert an.method == "fallback" and an.available()
    ctx = mk_ctx(None)
    frames, obs = _gesture_seq(an, ctx, ("up", 30.0, "right"))
    onset = [(i, o) for i, o in obs if o.kind == "gesture_point_up" and o.value["phase"] == "onset"]
    assert len(onset) == 1
    i, o = onset[0]
    assert i == 8                                                  # first arm-up frame, none before
    assert abs(o.value["arm_angle_deg_from_vertical"] - 30) < 8
    assert o.value["side"] == "right"
    assert o.ts == frames[8].real_ts and o.ts_capture == frames[8].capture_ts
    assert o.value["onset_window"] == [frames[7].real_ts.isoformat(timespec="milliseconds"),
                                       frames[8].real_ts.isoformat(timespec="milliseconds")]
    assert o.value["ts_uncertainty_s"] == pytest.approx(2.5 + 15.0)
    assert o.value["world_hint"]["az_deg"] == pytest.approx(310.0)   # camera-right of a 220 deg heading
    assert "aircraft_check" in ctx.triggers
    assert ctx.state["aircraft_check_requests"][-1]["side"] == "right"
    summary = [o for _, o in obs if o.kind == "gesture_point_up" and o.value["phase"] == "summary"]
    assert len(summary) == 1 and len(summary[0].value["track"]) == 2
    assert ctx.state["person_bbox"]["bbox"][0] < 640 < ctx.state["person_bbox"]["bbox"][2]


@pytest.mark.parametrize("pose", [("down", 0.0, "right"), ("horizontal", 0.0, "left")])
def test_gesture_no_false_positive(pose):
    an = gesture.GestureAnalyzer({})
    ctx = mk_ctx(None)
    _, obs = _gesture_seq(an, ctx, pose)
    assert not [o for _, o in obs if o.kind == "gesture_point_up"]
    assert "aircraft_check" not in ctx.triggers


def test_gesture_left_steep_and_pose_model_fallback():
    an = gesture.GestureAnalyzer({"pose_model_path": "/nonexistent/pose_landmarker_lite.task"})
    assert an.method == "fallback"
    _, obs = _gesture_seq(an, mk_ctx(None), ("up", 10.0, "left"))
    onset = [o for _, o in obs if o.kind == "gesture_point_up" and o.value["phase"] == "onset"]
    assert len(onset) == 1 and onset[0].value["arm_angle_deg_from_vertical"] < 20


def test_gesture_arm_only_when_person_absorbed_into_background():
    """Anja sat still long enough to become background: only the raised arm differs."""
    for pose, expect in ((("up", 30.0, "right"), True), (("down", 0.0, "right"), False)):
        an = gesture.GestureAnalyzer({"bg_len": 6, "bg_every": 1})
        ctx = mk_ctx(None)
        rng = np.random.default_rng(4)
        base = forest()
        obs = []
        for i, what in enumerate(["bg"] * 3 + ["down"] * 10 + [pose] * 2):
            img = noisy(base, rng)
            if what == "down":
                stick_figure(img)
            elif what != "bg":
                stick_figure(img, arm=what[0], angle=what[1], side=what[2])
            obs += [(i, o) for o in an.on_frame(mk_frame(i, img), ctx)]
        got = [(i, o) for i, o in obs if o.kind == "gesture_point_up"]
        if not expect:
            assert not got
            continue
        assert len(got) == 1 and got[0][0] == 13
        o = got[0][1]
        assert o.value["arm_only"] is True and o.confidence <= 0.35
        assert abs(o.value["arm_angle_deg_from_vertical"] - 30) < 8 and o.value["side"] == "right"


def test_vlm_lazy_connect_retries(mock_vlm_server):
    port = socket_free_port()
    an = vlm.VLMAnalyzer({"_global": {"vlm": {"url": f"http://127.0.0.1:{port}"}}, "lazy_connect": True,
                          "reping_s": 0.0, "scene_every_s": -1})
    assert an.available() is True                    # stays loaded
    ctx = mk_ctx(None)
    ctx.trigger("whiteboard")
    assert an.on_frame(mk_frame(0, noisy(forest(), np.random.default_rng(0))), ctx) == []
    assert "whiteboard" not in ctx.triggers and _MockVLM.requests == []
    an.client.url = mock_vlm_server                  # server comes up
    ctx.trigger("whiteboard")
    an.on_frame(mk_frame(1, noisy(forest(), np.random.default_rng(1))), ctx)
    assert an.flush(10)
    assert [o.kind for o in an.on_tick(ctx)].count("whiteboard_text") == 1
    an.close()


def test_runner_loads_vision_analyzers(caplog):
    from hordewatch.runner import DEFAULT_CONFIG, load_analyzers
    import logging
    cfg = {**DEFAULT_CONFIG, "analyzers": ["whiteboard", "scene", "gesture", "vlm"],
           "vlm": {"backend": "ollama", "url": f"http://127.0.0.1:{socket_free_port()}", "model": "llava:7b"}}
    got = load_analyzers(cfg, logging.getLogger("test"))
    assert [a.name for a in got] == ["whiteboard", "scene", "gesture"]      # VLM server absent -> disabled
