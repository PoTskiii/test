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
    # the re-ping runs on a background thread (on_frame never waits on the network); wait for it
    an.on_frame(mk_frame(1, noisy(forest(), np.random.default_rng(1))), ctx)
    for _ in range(200):
        if an._connected:
            break
        time.sleep(0.02)
    assert an._connected
    ctx.trigger("whiteboard")
    an.on_frame(mk_frame(2, noisy(forest(), np.random.default_rng(2))), ctx)
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


# =================================================================================== adversarial review tests
# Each test below pins a defect found in review (it failed on the original implementation).

def _read(text, conf=0.9):
    lines = [wb.OcrLine(text=t, conf=conf, y=(k + 0.5) / 3, raw=t) for k, t in enumerate(text.split("\n"))]
    return wb.BoardRead(lines=lines, conf=conf, engine="rapidocr", variant="clahe")


def _scripted_ocr(monkeypatch, reads):
    """Replace the OCR engine by a script of reads (None = nothing legible); returns the call log."""
    calls = []
    it = iter(reads)

    def fake_read_board(crop, rapid=None, tess=None, good_conf=0.85):
        calls.append(crop.shape)
        return next(it, None)

    monkeypatch.setattr(wb, "read_board", fake_read_board)
    monkeypatch.setattr(wb, "get_rapidocr", lambda threads=2: object())
    monkeypatch.setattr(wb, "get_tesseract", lambda: None)
    return calls


FULL = "INGEN STIER\nKAMERA 41 ØST"


@pytest.mark.parametrize("script, expect_texts", [
    # a hand covers the lower line for one frame: the partial read must not start a new board
    ([FULL, FULL, "INGEN", FULL, FULL], [FULL]),
    # a single garbage read (glare) in the middle is discarded, not announced
    ([FULL, FULL, "XQZW PLMK", FULL, FULL], [FULL]),
    # a garbage FIRST read followed by the real board: the abandoned single-read instance is dropped
    (["XQZW PLMK", FULL, FULL, FULL, FULL], [FULL]),
    # she really flips the board (two agreeing reads of new text): two boards, two events
    ([FULL, FULL, "SOL I SØR\nKL 14:30", "SOL I SØR\nKL 14:30", "SOL I SØR\nKL 14:30"],
     [FULL, "SOL I SØR\nKL 14:30"]),
])
def test_whiteboard_odd_read_does_not_split_board(monkeypatch, tmp_path, script, expect_texts):
    _scripted_ocr(monkeypatch, [_read(t) for t in script])
    db = DB(tmp_path / "w.sqlite")
    ctx = mk_ctx(db)
    an = wb.WhiteboardAnalyzer({"thumb_change": -1})             # read every frame
    rng = np.random.default_rng(21)
    base = forest(6)
    imgs = [place_board(noisy(base, rng), board_img())[0] for _ in range(len(script))] + [noisy(base, rng)] * 3
    frames = [mk_frame(i, im, db) for i, im in enumerate(imgs)]
    obs = run_frames(an, ctx, frames, db)
    texts = [o.value["text"] for _, o in obs if o.kind == "whiteboard_text"]
    assert texts == expect_texts
    assert [e[0] for e in events(db)] == ["whiteboard_text"] * len(expect_texts)
    if len(expect_texts) == 2:          # the new board is stamped with the first frame showing its text
        second = [o for _, o in obs if o.kind == "whiteboard_text"][1]
        assert second.ts == frames[2].real_ts and second.ts_capture == frames[2].capture_ts


def test_whiteboard_ocr_gate_ignores_light_change_but_rereads_new_writing(monkeypatch):
    """The re-read gate compared raw thumbnails: a 40 % exposure drop forced a re-OCR (~1 s CPU) while new
    writing on the held board (mean change ~9 grey levels < 12) was not re-read."""
    calls = _scripted_ocr(monkeypatch, [_read(FULL) for _ in range(20)])
    an = wb.WhiteboardAnalyzer({})
    ctx = mk_ctx(None)
    rng = np.random.default_rng(22)
    base = forest(6)
    a = lambda: place_board(noisy(base, rng), board_img())[0]                                     # noqa: E731
    dark = lambda: np.clip(a().astype(np.float32) * 0.6, 0, 255).astype(np.uint8)                 # noqa: E731
    b = lambda: place_board(noisy(base, rng), board_img(("SOL I SOR", "KL 14:30")))[0]            # noqa: E731
    seq = [a(), a(), dark(), dark(), a(), b()]
    n_calls = []
    for i, im in enumerate(seq):
        an.on_frame(mk_frame(i, im), ctx)
        n_calls.append(len(calls))
    assert n_calls[1] == 2                      # read until two reads agree (emitted)
    assert n_calls[4] == 2, n_calls             # exposure change / same board: no re-read
    assert n_calls[5] == 3, n_calls             # new writing on the held board: re-read at once


def test_whiteboard_long_hold_bounded_cpu(monkeypatch):
    """A board (or white fixture) visible for hours with OCR re-reads: reads per instance are capped, so the
    quadratic merge stays cheap (200 reads took 3.6 s per frame before)."""
    rng_t = np.random.default_rng(23)

    def noisy_read(k):
        t = list(FULL)
        for _ in range(int(rng_t.integers(0, 3))):
            t[int(rng_t.integers(0, len(t)))] = "ABCDEFGH0123"[int(rng_t.integers(0, 12))]
        return _read("".join(t), conf=float(rng_t.uniform(0.6, 0.95)))

    _scripted_ocr(monkeypatch, [noisy_read(k) for k in range(400)])
    an = wb.WhiteboardAnalyzer({"thumb_change": -1, "max_reads": 16})
    ctx = mk_ctx(None)
    rng = np.random.default_rng(24)
    img = place_board(noisy(forest(6), rng), board_img())[0]
    small = cv2.resize(img, (640, 360), interpolation=cv2.INTER_AREA)       # fast detection
    worst = 0.0
    for i in range(36):
        t = time.perf_counter()
        an.on_frame(mk_frame(i, small), ctx)
        worst = max(worst, time.perf_counter() - t)
    assert len(an._track.inst.reads) <= 16
    assert worst < 1.0, worst
    m = wb.merge_reads(an._track.inst.reads)
    assert wb.board_similarity(m["text"], FULL) > 0.85


@pytest.mark.parametrize("gains", [(1.0, 0.86, 0.66), (1.0, 0.75, 0.50)])     # ~3500 K and ~2500 K sun
def test_whiteboard_detected_in_warm_low_sun_without_false_positives(gains):
    """Late-September sun at 60 N is low most of the day: a white board lit by it is orange (HSV S 86-127)
    and was rejected by the fixed s_max=75 test."""
    rng = np.random.default_rng(25)
    g = np.array(gains, np.float32) * 1.08
    img, corners = place_board(noisy(forest(3), rng), board_img(), width=220, tilt_deg=-12)
    img = np.clip(img.astype(np.float32) * g, 0, 255).astype(np.uint8)
    c = wb.detect_boards(img)
    assert c, "warm-lit board not detected"
    xs, ys = corners[:, 0], corners[:, 1]
    assert wb.bbox_iou(c[0].bbox, (xs.min(), ys.min(), xs.max(), ys.max())) > 0.7
    # the balance must not turn a sunlit yellow patch (the brightest thing in view) into a 'board'
    for seed in range(4):
        f = noisy(forest(seed), rng).astype(np.float32)
        cv2.ellipse(f, (400 + 60 * seed, 560), (90, 40), 10, 0, 360, (220, 200, 120), -1)
        cv2.rectangle(f, (900, 500), (1060, 580), (225, 205, 110), -1)          # sunlit straw bale side
        f = np.clip(f * g, 0, 255).astype(np.uint8)
        assert wb.detect_boards(f) == []


class _HangingServer:
    """Accepts TCP connections (kernel backlog) but never answers: a hung/overloaded Ollama."""

    def __enter__(self):
        import socket
        self.s = socket.socket()
        self.s.bind(("127.0.0.1", 0))
        self.s.listen(16)
        return f"http://127.0.0.1:{self.s.getsockname()[1]}"

    def __exit__(self, *a):
        self.s.close()


def test_vlm_nonblocking_reping_and_aircraft_pulse_expires():
    with _HangingServer() as url:
        an = vlm.VLMAnalyzer({"_global": {"vlm": {"url": url, "backend": "auto"}}, "lazy_connect": True,
                              "reping_s": 0.0, "ping_timeout_s": 0.5, "scene_every_s": -1})
        assert an.available() is True
        ctx = mk_ctx(None)
        img = noisy(forest(), np.random.default_rng(0))
        worst = 0.0
        for i in range(3):
            t = time.perf_counter()
            an.on_frame(mk_frame(i, img), ctx)
            worst = max(worst, time.perf_counter() - t)
        assert worst < 0.1, f"on_frame blocked {worst:.2f}s on a hung server (re-ping was synchronous)"
    # a VLM 'pointing_up' answer raises aircraft_check; nothing consumes it, so it must be a pulse
    an._connected = True
    job = {"kind": "scene", "ts": T0, "ts_capture": T0 + timedelta(seconds=30), "frame_id": 1, "answer": "",
           "parsed": {"sky": "clear", "pointing_up": True}}
    kinds = [o.kind for o in an._to_observations(job, ctx)]
    assert "gesture_point_up" in kinds and "aircraft_check" in ctx.triggers
    for i in range(3, 20):                                     # 5 s frames: 85 s later
        an.on_frame(mk_frame(i, img), ctx)
    assert "aircraft_check" not in ctx.triggers, "trigger never expires -> runner forces every analyzer forever"
    an.close()


def test_vlm_board_answers_that_must_not_be_announced(tmp_path):
    db = DB(tmp_path / "v.sqlite")
    ctx = mk_ctx(db)
    an = vlm.VLMAnalyzer({"_global": {"vlm": {"url": "http://127.0.0.1:9"}}})
    f = mk_frame(0, np.zeros((72, 128, 3), np.uint8), db)

    def board(answer, parsed):
        return an._to_observations({"kind": "whiteboard", "ts": f.real_ts, "ts_capture": f.capture_ts,
                                    "frame_id": f.id, "track_id": 7, "answer": answer, "parsed": parsed}, ctx)

    # prose refusal (OpenAI-compatible backends do not enforce JSON)
    out = board("I'm sorry, I cannot read the text in this image.", None)
    assert not [o for o in out if o.kind == "whiteboard_text"]
    # unreadable transcription
    out = board('{"lines": ["???", "? ?"], "legible": true}', {"lines": ["???", "? ?"], "legible": True})
    assert [o.value["is_new"] for o in out if o.kind == "whiteboard_text"] == [None]
    # prose that is a plausible transcription: recorded with low confidence, never announced
    out = board("INGEN STIER", None)
    wt = [o for o in out if o.kind == "whiteboard_text"]
    assert wt and wt[0].confidence <= 0.2 and wt[0].value["is_new"] is None
    assert events(db) == []
    # the OCR analyzer announced this board earlier in THIS run -> the VLM must not announce it again
    from hordewatch.types import Observation
    db.add_observation(Observation(kind="whiteboard_text", ts=f.real_ts, analyzer="whiteboard",
                                   value={"text": FULL, "lines": FULL.split("\n")}))
    out = board("", {"lines": ["INGEN STIER", "KAMERA 41 ØST"], "legible": True, "confidence": 0.9})
    assert [o.value["is_new"] for o in out if o.kind == "whiteboard_text"] == [False]
    assert events(db) == []
    # bounded state over a multi-day run
    for k in range(200):
        ctx.state.setdefault("vlm_whiteboard", {})[1000 + k] = {"text": "x"}
    board("", {"lines": ["NY TAVLE 7"], "legible": True, "confidence": 0.9})
    assert len(ctx.state["vlm_whiteboard"]) <= 50


def test_gesture_timestamps_pdt_latency_and_summary_pair():
    """The summary row carried ts = onset but ts_capture = END frame (ADS-B bridge clusters on ts_capture:
    a > 60 s episode became a second, wrong sighting), and latency_s was the clock's value instead of the
    latency actually applied to the frame (PDT-measured)."""
    an = gesture.GestureAnalyzer({})
    ctx = mk_ctx(None)                                        # StreamClock says 30 s
    rng = np.random.default_rng(26)
    base = forest()
    seq = ["bg"] * 6 + ["down"] * 2 + [("up", 30.0, "right")] * 16 + ["down"] * 3
    obs = []
    for i, what in enumerate(seq):
        img = noisy(base, rng)
        if what == "down":
            stick_figure(img)
        elif what != "bg":
            stick_figure(img, arm="up", angle=what[1], side=what[2])
        obs += an.on_frame(mk_frame(i, img, latency=12.0), ctx)       # ingest measured 12 s via HLS PDT
    g = [o for o in obs if o.kind == "gesture_point_up"]
    assert [o.value["phase"] for o in g] == ["onset", "summary"]
    onset, summary = g
    for o in g:
        assert (o.ts_capture - o.ts).total_seconds() == pytest.approx(12.0)
        assert o.value["latency_s"] == pytest.approx(12.0)
    assert summary.ts == onset.ts and summary.ts_capture == onset.ts_capture
    assert summary.value["duration_s"] >= 30


def test_gesture_survives_stream_dropping_to_144p():
    """The background ring buffer mixed frame sizes after an adaptive-bitrate drop: np.stack raised on every
    frame and the detector stayed dead as long as the stream stayed at 144p."""
    an = gesture.GestureAnalyzer({})
    ctx = mk_ctx(None)
    rng = np.random.default_rng(27)
    base = forest()
    for i in range(8):
        an.on_frame(mk_frame(i, noisy(base, rng)), ctx)
    got = []
    for k, what in enumerate(["bg"] * 6 + ["down"] * 3 + ["up"] * 2):
        img = noisy(base, rng)
        if what == "down":
            stick_figure(img)
        elif what == "up":
            stick_figure(img, arm="up", angle=30.0, side="right")
        lo = cv2.resize(img, (256, 144), interpolation=cv2.INTER_AREA)
        got += [(8 + k, o) for o in an.on_frame(mk_frame(8 + k, lo), ctx)]
    on = [(i, o) for i, o in got if o.kind == "gesture_point_up"]
    assert len(on) == 1 and on[0][0] == 17 and on[0][1].value["side"] == "right"
    assert on[0][1].value["bbox"][2] <= 256                  # bbox in the 144p frame's own pixels


def test_scene_timestamp_pairs_and_odd_frames():
    """scene_change / ir_mode_switch had ts = onset but ts_capture = detection frame; grey 2-D frames crashed."""
    an = scene.SceneChangeAnalyzer({})
    ctx = mk_ctx(None)
    rng = np.random.default_rng(28)
    base = forest()
    obs = []
    for i in range(20):
        img = noisy(base, rng)
        if 6 <= i:
            cv2.fillPoly(img, [arrow_poly(200, 560)], (125, 80, 40))
        if i >= 12:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)          # 2-D grey frame (IR, some decoders)
        obs += [o for o in an.on_frame(mk_frame(i, img, latency=17.0), ctx)]
    kinds = [o.kind for o in obs]
    assert "object_appeared" in kinds and "scene_change" in kinds and "ir_mode_switch" in kinds
    for o in obs:
        assert (o.ts_capture - o.ts).total_seconds() == pytest.approx(17.0), (o.kind, o.ts, o.ts_capture)


@pytest.mark.parametrize("img", [
    np.full((720, 1280), 90, np.uint8),                                   # grey 2-D
    np.full((720, 1280, 4), 90, np.uint8),                                # RGBA
    np.random.default_rng(0).random((144, 256, 3)).astype(np.float32),   # float [0, 1]
    np.zeros((5, 7, 3), np.uint8),                                        # degenerate
    np.zeros((1, 1, 3), np.uint8),
])
def test_frame_analyzers_never_raise_on_odd_frames(img):
    ctx = mk_ctx(None)
    for an in (wb.WhiteboardAnalyzer({"ocr": False}), scene.SceneChangeAnalyzer({}), gesture.GestureAnalyzer({})):
        for i in range(6):
            assert isinstance(an.on_frame(mk_frame(i, img), ctx), list)


def test_mediapipe_landmark_geometry_with_fake_landmarker():
    """The MediaPipe path cannot run here (no model, no libEGL): exercise its landmark geometry with a fake
    PoseLandmarker so a pointing arm / a resting arm are classified correctly."""
    from types import SimpleNamespace as NS

    def pose(wrist_r, elbow_r, vis=0.9):
        pts = [(0.5, 0.2)] * 33                                  # everything at the head by default
        pts = list(pts)
        pts[11], pts[12] = (0.44, 0.35), (0.56, 0.35)            # shoulders (image left / right)
        pts[13], pts[15] = (0.42, 0.5), (0.42, 0.62)             # left arm resting
        pts[14], pts[16] = elbow_r, wrist_r
        pts[23], pts[24] = (0.46, 0.7), (0.54, 0.7)
        return [NS(x=x, y=y, visibility=vis) for x, y in pts]

    class FakeLM:
        def __init__(self, poses):
            self.poses = poses

        def detect(self, img):
            return NS(pose_landmarks=self.poses)

    mp_stub = NS(Image=lambda image_format, data: data, ImageFormat=NS(SRGB=1))
    det = object.__new__(gesture.MediaPipePose)
    det.mp, det.max_angle = mp_stub, 65.0
    small = np.zeros((225, 400, 3), np.uint8)
    # right arm straight up and 20 deg outwards
    a = np.deg2rad(20)
    sx, sy = 0.56 * 400, 0.35 * 225
    wx, wy = sx + 100 * np.sin(a), sy - 100 * np.cos(a)
    ex, ey = sx + 50 * np.sin(a), sy - 50 * np.cos(a)
    det.lm = FakeLM([pose((wx / 400, wy / 225), (ex / 400, ey / 225))])
    r = det.analyze(small, False)
    assert r["pointing"] and r["side"] == "right" and abs(r["angle"] - 20) < 2 and r["hand_cue"]
    assert r["n_persons"] == 1
    det.lm = FakeLM([pose((0.58, 0.62), (0.58, 0.5))])          # right arm resting
    assert det.analyze(small, False)["pointing"] is False
    det.lm = FakeLM([pose((wx / 400, wy / 225), (ex / 400, ey / 225), vis=0.2)])   # occluded landmarks
    assert det.analyze(small, False)["pointing"] is False
    det.lm = FakeLM([])
    r = det.analyze(small, False)
    assert r["person"] is False and r["pointing"] is False


def test_runner_end_to_end_replay_all_vision_analyzers(tmp_path):
    """Replay an image sequence through runner.run with whiteboard + vlm (server absent) + scene + gesture:
    DB serialisation of every value, consistent (ts, ts_capture) pairs, one announcement, and no false
    'object' for the person (the gesture blob used to be the held-up board, and a person absorbed into the
    gesture background used to lose her exclusion and be reported as a new blue object)."""
    from hordewatch.runner import load_config, run
    shots = tmp_path / "shots"
    shots.mkdir()
    rng = np.random.default_rng(0)
    base = forest(2)
    seq = ["bg"] * 5 + ["down"] * 3 + ["board"] * 3 + ["down"] * 2 + ["up"] * 3 + ["down"] * 3 + ["arrow"] * 6
    for i, what in enumerate(seq):
        img = noisy(base, rng)
        if what == "up":
            stick_figure(img, cx=900, arm="up", angle=25.0, side="left")
        elif what != "bg":
            stick_figure(img, cx=900)
        if what == "board":
            img = place_board(img, board_img(), center=(560, 380), width=360)[0]
        if what == "arrow":
            cv2.fillPoly(img, [arrow_poly(150, 600)], (125, 80, 40))
        cv2.imwrite(str(shots / f"f_{i:03d}.png"), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    cfg = load_config(None)
    cfg.update(db=str(tmp_path / "hw.sqlite"), archive_dir=str(tmp_path / "arch"),
               analyzers=["whiteboard", "vlm", "scene", "gesture"],
               vlm={"backend": "ollama", "url": f"http://127.0.0.1:{socket_free_port()}", "model": "llava:7b"},
               source={"type": "replay", "files": [str(shots)], "start_utc": "2026-09-22T18:00:00Z",
                       "image_interval_s": 5.0, "frame_interval_s": 5.0, "latency_s": 25.0,
                       "archive_every_n_frames": 0})
    db = run(cfg)
    obs = db.observations()
    assert obs
    for o in obs:
        assert (o["ts_capture"] - o["ts"]).total_seconds() == pytest.approx(25.0), o
    by = {}
    for o in obs:
        by.setdefault(o["kind"], []).append(o)
    assert [o["value"]["is_new"] for o in by["whiteboard_text"]] == [True]
    assert "KAMERA" in by["whiteboard_text"][0]["value"]["text"]
    onset = [o for o in by["gesture_point_up"] if o["value"]["phase"] == "onset"]
    assert len(onset) == 1 and onset[0]["value"]["side"] == "left"
    assert abs(onset[0]["value"]["arm_angle_deg_from_vertical"] - 25) < 8
    assert onset[0]["ts"] == datetime(2026, 9, 22, 18, 1, 5, tzinfo=timezone.utc) - timedelta(seconds=25)
    assert [o["value"]["label"] for o in by.get("object_appeared", [])] == ["horde_sign"]
    assert [e[0] for e in events(db)] == ["whiteboard_text"]


def test_vlm_scene_objects_not_rereported_every_scene_prompt():
    """LLaVA lists the same persistent things every 10 min: each listing used to become a new
    object_appeared row (and hands_or_signs_near_box on every report while true)."""
    an = vlm.VLMAnalyzer({"_global": {"vlm": {"url": "http://127.0.0.1:9"}}})
    ctx = mk_ctx(None)

    def scene_job(k, objects, near):
        t = T0 + timedelta(minutes=10 * k)
        return an._to_observations({"kind": "scene", "ts": t, "ts_capture": t + timedelta(seconds=30), "frame_id": k,
                                    "answer": "", "parsed": {"sky": "overcast", "objects_new": objects,
                                                             "hands_or_signs_near_box": near}}, ctx)

    labels = lambda out: [o.value["label"] for o in out if o.kind == "object_appeared"]   # noqa: E731
    assert labels(scene_job(0, ["wooden sign", "the box"], False)) == ["wooden sign", "the box"]
    assert labels(scene_job(1, ["Wooden sign.", "the box"], True)) == ["hands_or_signs_near_box"]
    assert labels(scene_job(2, ["wooden sign", "drone"], True)) == ["drone"]
    assert labels(scene_job(3, [], False)) == []
    assert labels(scene_job(4, [], True)) == ["hands_or_signs_near_box"]          # a new transition
    assert labels(scene_job(30, ["wooden sign"], False)) == ["wooden sign"]      # 5 h later: re-reported


def test_clock_seen_without_tz_database_after_dst_end(monkeypatch):
    """Without a tz database (Windows without tzdata) the Oslo fallback was a fixed +2 h: after the last
    Sunday of October a board saying 'KL 14:30' was mapped an hour wrong (capture_minus_shown_s ~3640 s)."""
    import zoneinfo

    def no_tz(key):
        raise zoneinfo.ZoneInfoNotFoundError(key)

    monkeypatch.setattr(zoneinfo, "ZoneInfo", no_tz)
    an = wb.WhiteboardAnalyzer({"ocr": False})
    for cap, expect in ((datetime(2026, 10, 26, 13, 30, 40, tzinfo=timezone.utc), 40.0),     # CET  (UTC+1)
                        (datetime(2026, 10, 24, 12, 30, 40, tzinfo=timezone.utc), 40.0)):    # CEST (UTC+2)
        obs = an._clock_obs("SOL I SØR\nKL 14:30", cap - timedelta(seconds=30), cap, None)
        assert len(obs) == 1 and obs[0].value["capture_minus_shown_s"] == pytest.approx(expect)


def test_pulse_triggers_expire_even_with_frozen_timestamps():
    """A source that repeats one timestamp (image folder without times, stalled clock) must not leave a
    pulse trigger set forever (the runner would force every analyzer on every frame)."""
    ctx = mk_ctx(None)
    wb.pulse_trigger(ctx, "aircraft_check", T0, 60.0, index=10)
    ctx.trigger("unrelated")                                     # someone else's trigger: never touched
    for i in range(11, 80):
        wb.expire_pulses(ctx, T0, i)
    assert ctx.triggers == {"unrelated"}
    wb.pulse_trigger(ctx, "whiteboard", T0, 12.0, index=5)
    wb.expire_pulses(ctx, T0 - timedelta(seconds=1), 6)           # replay restarted: time went backwards
    assert "whiteboard" not in ctx.triggers


def test_whiteboard_flip_confirmed_promptly_with_default_ocr_gate(monkeypatch, tmp_path):
    """With the (default) appearance gate, the frame after a divergent read looks unchanged; the confirming
    read must still happen at once, not ocr_stable_every_s (60 s) later."""
    B = "SOL I SØR\nKL 14:30"
    calls = _scripted_ocr(monkeypatch, [_read(FULL), _read(FULL), _read(B), _read(B), _read(B)])
    db = DB(tmp_path / "f.sqlite")
    ctx = mk_ctx(db)
    an = wb.WhiteboardAnalyzer({})
    rng = np.random.default_rng(29)
    base = forest(6)
    a = lambda: place_board(noisy(base, rng), board_img())[0]                                     # noqa: E731
    b = lambda: place_board(noisy(base, rng), board_img(("SOL I SOR", "KL 14:30")))[0]            # noqa: E731
    frames = [mk_frame(i, im, db) for i, im in enumerate([a(), a(), b(), b(), noisy(base, rng), noisy(base, rng)])]
    out = run_frames(an, ctx, frames, db)
    texts = [(i, o.value["text"]) for i, o in out if o.kind == "whiteboard_text"]
    assert [t for _, t in texts] == [FULL, B]
    assert texts[1][0] == 3, texts                     # confirmed on the 2nd frame of the flipped board
    assert len(calls) == 4
    assert len(events(db)) == 2
