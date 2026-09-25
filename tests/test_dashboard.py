"""Tests for hordewatch.dashboard: API, filters, media, timeline/sun, SSE, ntfy push, CLI, launcher.

Offline: a temp SQLite DB seeded with frames/audio/observations/events/calibration, synthetic engine
outputs and a live layer; the only socket used is a loopback uvicorn server (skipped if binding fails).
"""
import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.error
import wave
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

cv2 = pytest.importorskip("cv2")
from fastapi.testclient import TestClient  # noqa: E402

from hordewatch.dashboard import app as A  # noqa: E402
from hordewatch.dashboard.notify import CURSOR_KEY, NtfyNotifier  # noqa: E402
from hordewatch.db import DB  # noqa: E402
from hordewatch.types import AudioChunk, Frame, Observation, iso  # noqa: E402

UTC = timezone.utc
T0 = datetime(2026, 9, 21, 17, 0, tzinfo=UTC)          # 19:00 CEST, the evening of day 1
BOARD_BBOX = (500, 200, 700, 330)
REF = (61.245, 10.87)                                   # #1 hotspot in the synthetic hotspots.json
TRUE_ATT = (219.6, 1.0, 0.5)                             # heading, pitch, roll used to build astro_camera.G


# =============================================================================== fixtures
def _board_image():
    img = np.full((720, 1280, 3), 40, np.uint8)
    x0, y0, x1, y1 = BOARD_BBOX
    img[y0:y1 + 1, x0:x1 + 1] = 245
    img[y0 + 40:y0 + 50, x0 + 30:x1 - 30] = 10            # a line of "ink"
    return img


def _write_jpeg(path, img):
    path.parent.mkdir(parents=True, exist_ok=True)
    assert cv2.imwrite(str(path), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    return str(path)


def _write_wav(path, sr=16000, s=1.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    x = (0.1 * np.sin(2 * np.pi * 440 * np.arange(int(sr * s)) / sr) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(x.tobytes())
    return str(path)


def _obs(db, kind, t, value, analyzer="test", conf=0.5, **kw):
    return db.add_observation(Observation(kind=kind, ts=t, value=value, analyzer=analyzer, confidence=conf,
                                          ts_capture=t + timedelta(seconds=30), **kw))


@pytest.fixture()
def env(tmp_path):
    db_path = tmp_path / "hw.sqlite"
    archive = tmp_path / "archive"
    out = tmp_path / "output"
    layers = tmp_path / "layers"
    db = DB(db_path)
    ids = {}
    img = _board_image()

    # frames: A archived with DB path, B archived retroactively (DB path NULL), C not archived
    tA = T0 + timedelta(minutes=10)
    fA = Frame(12, tA + timedelta(seconds=30), tA, img, "live")
    fA.path = _write_jpeg(archive / "20260921" / f"{tA:%H%M%S}_12.jpg", img)
    ids["fA"] = db.add_frame(fA)
    tB = tA + timedelta(seconds=5)
    fB = Frame(13, tB + timedelta(seconds=30), tB, img, "live")
    ids["fB"] = db.add_frame(fB)
    _write_jpeg(archive / "20260921" / f"{tB:%H%M%S}_13.jpg", img)
    tC = T0 + timedelta(hours=2)
    ids["fC"] = db.add_frame(Frame(14, tC + timedelta(seconds=30), tC, img, "live"))

    au = AudioChunk(3, T0 + timedelta(minutes=29, seconds=40), T0 + timedelta(minutes=29, seconds=10),
                    np.zeros(16000, np.float32))
    au.path = _write_wav(archive / "20260921" / "172910_3.wav")
    ids["audio"] = db.add_audio(au)

    # continuous series: 2 h of sky/scene photometry (1/min), cloud every 10 min
    for k in range(121):
        t = T0 + timedelta(minutes=k)
        _obs(db, "sky_photometry", t, {"luma": 100.0 + k, "r": 1, "g": 1, "b": 1, "cct_k": 6000, "sat": 0.1, "region": "sky"},
             "sky", 0.6)
        _obs(db, "scene_photometry", t, {"luma": 80.0, "exposure_hint": 0, "ir_mode": False}, "sky", 0.6)
    for k in range(0, 121, 10):
        _obs(db, "cloud_fraction", T0 + timedelta(minutes=k), {"fraction": 0.8, "method": "sky_seg"}, "sky", 0.5)
    _obs(db, "rain_visual", T0 + timedelta(minutes=30), {"present": True, "intensity": 0.6}, "rain", 0.4)
    _obs(db, "rain_visual", T0 + timedelta(minutes=31), {"present": False}, "rain", 0.4)
    ids["aircraft"] = _obs(db, "audio_aircraft", T0 + timedelta(minutes=29, seconds=38),
                           {"peak_ts": iso(T0), "snr_db": 12.5, "duration_s": 40, "doppler_hint": "falling"},
                           "audio_events", 0.7, audio_id=ids["audio"])
    ids["gesture"] = _obs(db, "gesture_point_up", T0 + timedelta(minutes=29, seconds=40),
                          {"arm_angle_deg_from_vertical": 20, "side": "left", "bbox": [1, 2, 3, 4]}, "gesture", 0.8,
                          frame_id=ids["fA"])
    ids["stars"] = _obs(db, "star_field", T0 + timedelta(minutes=90),
                        {"n_stars": 50, "points": [[i, i, 1.0] for i in range(50)]}, "night", 0.3)
    _obs(db, "stream_health", T0 + timedelta(minutes=100),
         {"bitrate_kbps": 2500, "fps": 30, "dropped": 0, "stall_s": 0, "resolution": "1280x720"}, "stream_health", 0.9)
    _obs(db, "stream_latency", T0 + timedelta(minutes=100), {"latency_s": 31.0, "method": "live_edge"}, "stream_health", 0.5)
    _obs(db, "clock_seen", T0 + timedelta(minutes=10),
         {"shown_time": "19:10", "capture_minus_shown_s": 35.0, "source": "whiteboard"}, "whiteboard", 0.4)

    # whiteboard: board 1 (track 1) = OCR first read + OCR revision + VLM; board 2 (older, repeat, no frame)
    v1 = {"text": "KAMERA 41 0ST", "lines": ["KAMERA 41 0ST"], "ocr_conf": 0.8, "track_id": 1, "bbox": list(BOARD_BBOX),
          "first_seen_ts": iso(tA), "last_seen_ts": iso(tA + timedelta(seconds=20)), "is_new": True, "n_reads": 2}
    ids["wb1"] = _obs(db, "whiteboard_text", tA, v1, "whiteboard", 0.7, frame_id=ids["fB"])
    ids["wb1rev"] = _obs(db, "whiteboard_text", tA, {**v1, "text": "KAMERA 41 ØST", "revision_of": ids["wb1"], "n_reads": 5},
                         "whiteboard", 0.75, frame_id=ids["fB"], notes="revision")
    ids["wb1vlm"] = _obs(db, "whiteboard_text", tA + timedelta(seconds=5),
                         {"text": "KAMERA 41 ØST", "source": "vlm", "model": "llava:7b", "track_id": 1,
                          "bbox": list(BOARD_BBOX), "is_new": True, "legible": True}, "vlm", 0.5, frame_id=ids["fB"])
    tW = T0 + timedelta(minutes=5)
    ids["wb2"] = _obs(db, "whiteboard_text", tW, {"text": "HEI", "track_id": 7, "bbox": list(BOARD_BBOX), "is_new": False,
                                                 "repeat_of": 99, "first_seen_ts": iso(tW),
                                                 "last_seen_ts": iso(tW + timedelta(seconds=20))},
                      "whiteboard", 0.6, frame_id=ids["fC"])

    # events
    ids["ev_wb"] = db.add_event(tA, "whiteboard_text", "New whiteboard text: KAMERA 41 ØST", {"text": "KAMERA 41 ØST"})
    ids["ev_eng"] = db.add_event(T0 + timedelta(minutes=60), "engine_ranking_change", "top spot moved 7 km", {"changes": []})
    ids["ev_lat"] = db.add_event(T0 + timedelta(minutes=61), "latency_calibrated", "latency 32.5 s", {})
    db.con.execute("UPDATE events SET status='ack' WHERE id=?", (ids["ev_lat"],))
    db.con.commit()

    # calibration (astro_camera.G built from a known attitude at the reference point)
    from hordewatch.astro.camera import rotation_matrix
    from hordewatch.astro.ephem import observer_frame
    _, T = observer_frame(*REF)
    G = rotation_matrix(*TRUE_ATT) @ T
    db.set_calibration("latency_s", 32.5)
    db.set_calibration("latency_sigma_s", 6.0)
    db.set_calibration("audio_offset_s", 0.4)
    db.set_calibration("astro_camera", {"method": "sun_track", "G": [G.tolist()], "f": 1068.0 / 1280.0, "rms_px": 0.001,
                                        "n": 40, "pose_segments": 1, "updated": iso(T0)})
    db.set_calibration("bridge_state:adsb", {"done": {}})

    # engine outputs
    out.mkdir()
    (out / "hotspots.json").write_text(json.dumps({
        "summary": {"credible_km2": {"0.5": 817.8, "0.8": 5328.2, "0.9": 16610.0}, "layers": [{"name": "x"}]},
        "hotspots": [
            {"lat": REF[0], "lon": REF[1], "p_cell": 1.7e-3, "p_within_1.5km": 0.012,
             "groups": {"elevation_hint": 2.41, "forest_species": -0.33, "aircraft": 1.59, "travel": 0.1}},
            {"lat": 61.335, "lon": 10.95, "p_cell": 1.69e-3, "p_within_1.5km": 0.0089, "groups": {"a": 0.5},
             "norgeskart": "https://norgeskart.no/#!given", "google_maps": "https://maps.example/given"},
            {"lat": 61.315, "lon": 10.97, "p_cell": 1.68e-3, "p_within_1.5km": 0.0112, "groups": {}},
        ]}))
    (out / "scenario_hotspots.json").write_text(json.dumps({
        "scenarios": [{"name": "base", "weight": 3.0, "credible_km2_50": 817.8}],
        "credible_km2": {"0.5": 860.3, "0.8": 6159.7, "0.9": 19866.3},
        "hotspots": [{"lat": 61.14, "lon": 10.86, "p_cell": 1.6e-3, "p_within_1.5km": 0.014,
                      "scenario_p_cell_ratio": {"base": 0.98, "elevation_literal": 1.98}, "fragility": 0.64}]}))
    (out / "map.html").write_text("<html><body>engine map</body></html>")
    (out / "posterior.npz").write_bytes(b"not served")
    hist = out / "history"
    hist.mkdir()
    for k, (lat, stamp) in enumerate([(61.1, "20260925T180000000Z"), (61.2, "20260925T190000000Z")]):
        (hist / f"{stamp}_hotspots.json").write_text(json.dumps({
            "ts": f"2026-09-25T{18 + k}:00:00+00:00", "material": bool(k), "changes": [{"type": "top_moved", "km": 7.1}] if k else [],
            "credible_km2": {"0.5": 800 + k}, "live_layers": ["hw_aircraft"], "hotspots": [{"lat": lat, "lon": 10.9, "p_within_1.5km": 0.01}]}))

    # a live layer on a sub-grid with a known peak
    layers.mkdir()
    ll = np.full((20, 30), -5.0, np.float32)
    ll[:3, :] = np.nan
    ll[7, 11] = 2.5
    np.savez(layers / "hw_test.npz", loglik=ll, lat_min=61.0, lon_min=10.5, dlat=0.005, dlon=0.01,
             meta=json.dumps({"name": "hw_test", "reliability": 0.4, "independence_group": "aircraft_x",
                              "description": "synthetic", "sources": ["test"]}))

    cfg = {"camera": {"heading_deg": 220.0, "pitch_deg": 0.0, "roll_deg": 0.0, "hfov_deg": 70.0},
           "clock": {"latency_s": 30.0, "latency_sigma_s": 15.0}}
    app = A.create_app(db_path, out, archive_dir=archive, layers_dir=layers, config=cfg, notifier=None)
    client = TestClient(app)
    return {"db": db, "db_path": db_path, "archive": archive, "out": out, "app": app, "client": client, "ids": ids,
            "tmp": tmp_path}


def parse_sse(text):
    events = []
    for block in text.split("\n\n"):
        ev = {"event": "message", "data": None, "id": None}
        lines = [l for l in block.split("\n") if l and not l.startswith(":")]
        if not lines:
            continue
        for l in lines:
            k, _, v = l.partition(": ")
            if k == "event":
                ev["event"] = v
            elif k == "data":
                ev["data"] = json.loads(v)
            elif k == "id":
                ev["id"] = v
            elif k == "retry":
                ev["event"] = "retry"
        events.append(ev)
    return events


# =============================================================================== page + helpers
def test_index_and_static_served(env):
    c = env["client"]
    r = c.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    assert "hordewatch" in r.text and "api/stream" in r.text and "EventSource" in r.text
    assert c.get("/static/index.html").status_code == 200
    assert c.get("/static/nope.js").status_code == 404
    assert c.get("/api/health").json()["ok"] is True


def test_parse_time_param_and_summaries():
    now = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)
    assert A.parse_time_param("6h", now) == iso(now - timedelta(hours=6))
    assert A.parse_time_param("90m", now) == iso(now - timedelta(minutes=90))
    assert A.parse_time_param("2026-09-21T19:29:38Z") == "2026-09-21T19:29:38.000+00:00"
    assert A.parse_time_param("2026-09-21T21:29:38+02:00") == "2026-09-21T19:29:38.000+00:00"
    assert A.parse_time_param("2026-09-21T19:29:38") == "2026-09-21T19:29:38.000+00:00"   # naive = UTC
    assert A.parse_time_param("") is None and A.parse_time_param(None) is None
    with pytest.raises(ValueError):
        A.parse_time_param("yesterday-ish")
    assert A.to_oslo("2026-09-21T19:29:38.000+00:00") == "2026-09-21T21:29:38+02:00"     # CEST
    assert A.to_oslo("2026-12-21T12:00:00+00:00") == "2026-12-21T13:00:00+01:00"         # CET (DST-aware)
    assert "luma 123.5" in A.summarize_value("sky_photometry", {"luma": 123.45, "cct_k": 5400, "sat": 0.2})
    assert A.summarize_value("whiteboard_text", {"text": "A\nB", "is_new": True}) == "NEW «A / B»"
    assert "80 % cloud" in A.summarize_value("cloud_fraction", {"fraction": 0.8, "method": "vlm"})
    assert "NOZ9EG" in A.summarize_value("aircraft_match", {"callsign": "NOZ9EG", "alt_ft": 25920, "elev_deg": 70.2, "az_deg": 12})
    # malformed values never raise; unknown kinds get the generic summary
    assert isinstance(A.summarize_value("cloud_fraction", {"fraction": "x"}), str)
    assert A.summarize_value("brand_new_kind", {"a": 1, "b": "text", "c": [1, 2]}) == "a=1, b=text, c=[2]"
    assert A.summarize_value("sky_photometry", "not a dict") == "not a dict"


def test_bucketize_mean_and_max():
    t = np.array([0.0, 10, 20, 70, 80])
    v = np.array([1.0, 3, np.nan, 5, 9])
    mean = A._bucketize(t, v, 0.0, 60.0, "mean")
    assert mean == [[30000, 2.0, 2], [90000, 7.0, 2]]
    mx = A._bucketize(t, v, 0.0, 60.0, "max")
    assert [p[1] for p in mx] == [3.0, 9.0]
    # clipped to a 75 s window: the sample at t1 joins the last (partial) bucket, centred inside the window
    clip = A._bucketize(np.array([0.0, 60, 75, 90]), np.array([1.0, 2, 4, 100]), 0.0, 60.0, "mean", t1=75.0)
    assert clip == [[30000, 1.0, 1], [67500, 3.0, 2]]


# =============================================================================== observations
def test_observations_list_and_filters(env):
    c, ids = env["client"], env["ids"]
    r = c.get("/api/observations").json()
    rows = r["rows"]
    assert len(rows) == 100 and r["next"] == {"before_id": rows[-1]["id"]}
    assert [o["id"] for o in rows] == sorted((o["id"] for o in rows), reverse=True)
    o = rows[0]
    for k in ("id", "ts", "ts_oslo", "ts_capture", "delay_s", "kind", "analyzer", "confidence", "summary", "value"):
        assert k in o
    assert o["ts_oslo"].endswith("+02:00") and o["delay_s"] == 30.0
    # paging
    page2 = c.get("/api/observations", params={"before_id": r["next"]["before_id"], "limit": 10}).json()["rows"]
    assert len(page2) == 10 and max(x["id"] for x in page2) < rows[-1]["id"]
    # kind filter (single, multiple)
    sky = c.get("/api/observations", params={"kind": "sky_photometry", "limit": 1000}).json()["rows"]
    assert len(sky) == 121 and {x["kind"] for x in sky} == {"sky_photometry"}
    two = c.get("/api/observations", params={"kind": "cloud_fraction,rain_visual", "limit": 1000}).json()["rows"]
    assert {x["kind"] for x in two} == {"cloud_fraction", "rain_visual"} and len(two) == 13 + 2
    # confidence, analyzer, text search, time window
    hi = c.get("/api/observations", params={"min_conf": 0.65, "limit": 1000}).json()["rows"]
    assert hi and all(x["confidence"] >= 0.65 for x in hi)
    assert {x["kind"] for x in hi} >= {"audio_aircraft", "gesture_point_up", "stream_health"}
    vlm = c.get("/api/observations", params={"analyzer": "vlm"}).json()["rows"]
    assert [x["id"] for x in vlm] == [ids["wb1vlm"]]
    q = c.get("/api/observations", params={"q": "KAMERA"}).json()["rows"]
    assert {x["id"] for x in q} == {ids["wb1"], ids["wb1rev"], ids["wb1vlm"]}
    win = c.get("/api/observations", params={"since": "2026-09-21T17:29:00Z", "until": "2026-09-21T19:30:00+02:00",
                                             "limit": 1000}).json()["rows"]
    assert win and all("2026-09-21T17:29:00" <= x["ts"] <= "2026-09-21T17:30:00.000+00:00" for x in win)
    assert {ids["aircraft"], ids["gesture"]} <= {x["id"] for x in win}
    # phenomenon-time ordering
    by_ts = c.get("/api/observations", params={"order": "ts", "limit": 50}).json()
    ts = [x["ts"] for x in by_ts["rows"]]
    assert ts == sorted(ts, reverse=True) and "before_ts" in by_ts["next"]
    more = c.get("/api/observations", params={"order": "ts", "limit": 50, **by_ts["next"]}).json()["rows"]
    assert more and more[0]["ts"] <= ts[-1] and not ({x["id"] for x in more} & {x["id"] for x in by_ts["rows"]})
    # errors
    assert c.get("/api/observations", params={"since": "garbage"}).status_code == 400
    assert c.get("/api/observations", params={"min_conf": 2}).status_code == 422


def test_observation_media_links_and_truncation(env):
    c, ids = env["client"], env["ids"]
    by_id = {o["id"]: o for o in c.get("/api/observations", params={"limit": 1000}).json()["rows"]}
    # star list truncated in lists, complete in the detail view
    s = by_id[ids["stars"]]
    assert s["value_truncated"] is True and len(s["value"]["points"]) == 13 and "50 star-like" in s["summary"]
    full = c.get(f"/api/observations/{ids['stars']}").json()
    assert len(full["value"]["points"]) == 50 and full["value_truncated"] is False
    assert c.get("/api/observations/999999").status_code == 404
    # frame A has a DB path; whiteboard rows point at frame B (archived retroactively, NULL path)
    g = by_id[ids["gesture"]]
    assert g["frame_url"] == f"api/frames/{ids['fA']}/image" and g["near_frame_url"] is None
    assert by_id[ids["wb1"]]["frame_url"] == f"api/frames/{ids['fB']}/image"
    assert by_id[ids["wb2"]]["frame_url"] is None                # frame C was never archived
    # audio observation: WAV link + nearest archived frame by time (URL-encoded '+')
    a = by_id[ids["aircraft"]]
    assert a["audio_url"] == f"api/audio/{ids['audio']}"
    assert "%2B00%3A00" in a["near_frame_url"]
    r = c.get("/" + a["near_frame_url"] + "&max_s=3600&info=true")
    assert r.status_code == 200 and r.json()["id"] in (ids["fA"], ids["fB"])
    wav = c.get("/" + a["audio_url"])
    assert wav.status_code == 200 and wav.content[:4] == b"RIFF"


def test_kinds_endpoint(env):
    d = env["client"].get("/api/kinds").json()
    k = {x["kind"]: x for x in d["kinds"]}
    assert k["sky_photometry"]["n"] == 121 and k["whiteboard_text"]["n"] == 4 and k["audio_bells"]["n"] == 0
    assert k["sky_photometry"]["description"]
    an = {x["analyzer"]: x["n"] for x in d["analyzers"]}
    assert an["vlm"] == 1 and an["sky"] == 121 * 2 + 13


# =============================================================================== events
def test_events_list_ack_reopen_ack_all(env):
    c, ids = env["client"], env["ids"]
    d = c.get("/api/events", params={"status": "new"}).json()
    assert [e["id"] for e in d["rows"]] == [ids["ev_eng"], ids["ev_wb"]]
    assert d["counts"] == {"new": 2, "ack": 1}
    assert d["rows"][0]["ts_oslo"].endswith("+02:00")
    e = c.post(f"/api/events/{ids['ev_wb']}/ack").json()
    assert e["status"] == "ack" and e["id"] == ids["ev_wb"]
    assert [x["id"] for x in c.get("/api/events", params={"status": "new"}).json()["rows"]] == [ids["ev_eng"]]
    assert c.post(f"/api/events/{ids['ev_wb']}/ack", json={"status": "new"}).json()["status"] == "new"
    assert c.post(f"/api/events/{ids['ev_wb']}/ack", json={"status": "bogus"}).status_code == 400
    assert c.post("/api/events/99999/ack").status_code == 404
    # ack_all only up to the id the page has seen: a newer alert stays new
    late = env["db"].add_event(T0 + timedelta(hours=3), "whiteboard_text", "late", {})
    r = c.post("/api/events/ack_all", params={"up_to_id": ids["ev_lat"]}).json()
    assert sorted(r["ids"]) == sorted([ids["ev_wb"], ids["ev_eng"]])
    assert [x["id"] for x in c.get("/api/events", params={"status": "new"}).json()["rows"]] == [late]
    assert len(c.get("/api/events", params={"status": "all"}).json()["rows"]) == 4


# =============================================================================== whiteboard + frames
def test_whiteboard_grouping_and_crop(env):
    c, ids = env["client"], env["ids"]
    boards = c.get("/api/whiteboard").json()["boards"]
    assert len(boards) == 2
    b1, b2 = boards                                              # newest first
    assert b1["obs_ids"] == sorted([ids["wb1"], ids["wb1rev"], ids["wb1vlm"]])
    assert b1["ocr"]["text"] == "KAMERA 41 ØST" and b1["ocr"]["revision"] is True     # latest OCR revision wins
    assert b1["vlm"]["text"] == "KAMERA 41 ØST" and b1["vlm"]["model"] == "llava:7b"
    assert b1["is_new"] is True and b1["ts_oslo"] == "2026-09-21T19:10:00+02:00"
    assert b1["crop_url"] == f"api/whiteboard/{ids['wb1rev']}/crop.jpg"
    assert b2["is_new"] is False and b2["repeat_of"] == 99 and b2["crop_url"] is None
    assert [b["id"] for b in c.get("/api/whiteboard", params={"only_new": True}).json()["boards"]] == [b1["id"]]
    r = c.get("/" + b1["crop_url"])
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    im = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_GRAYSCALE)
    x0, y0, x1, y1 = BOARD_BBOX
    pad = 0.15 * max(x1 - x0, y1 - y0)
    assert abs(im.shape[1] - (x1 - x0 + 2 * pad)) <= 3 and abs(im.shape[0] - (y1 - y0 + 2 * pad)) <= 3
    h, w = im.shape
    assert im[h // 2 + 20, w // 2] > 200 and im[2, 2] < 80       # bright board in the middle, dark margin
    assert c.get(f"/api/whiteboard/{ids['wb2']}/crop.jpg").status_code == 404


def test_frames_latest_near_image_and_path_safety(env, tmp_path_factory):
    c, ids, db = env["client"], env["ids"], env["db"]
    lf = c.get("/api/frames/latest").json()
    assert lf["id"] == ids["fC"] and lf["image"]["id"] == ids["fB"] and lf["latency_applied_s"] == 30.0
    r = c.get(f"/api/frames/{ids['fA']}/image")
    assert r.status_code == 200 and r.content[:2] == b"\xff\xd8"
    small = c.get(f"/api/frames/{ids['fA']}/image", params={"max_w": 320})
    assert cv2.imdecode(np.frombuffer(small.content, np.uint8), cv2.IMREAD_COLOR).shape[1] == 320
    assert c.get(f"/api/frames/{ids['fC']}/image").status_code == 404
    near = c.get("/api/frames/near", params={"ts": "2026-09-21T17:10:04Z", "info": True}).json()
    assert near["id"] == ids["fB"] and near["offset_s"] == 1.0
    assert c.get("/api/frames/near", params={"ts": "2026-09-21T17:10:04Z"}).content[:2] == b"\xff\xd8"
    assert c.get("/api/frames/near", params={"ts": "2026-09-22T12:00:00Z"}).status_code == 404
    # a DB row pointing outside the allowed roots (or at a non-image) is never served
    outside = tmp_path_factory.mktemp("elsewhere") / "secret.jpg"
    outside.write_bytes(open(db.frame_path(ids["fA"]), "rb").read())
    f1 = Frame(20, T0, T0, np.zeros((4, 4, 3), np.uint8), path=str(outside))
    f2 = Frame(21, T0, T0, np.zeros((4, 4, 3), np.uint8), path=str(env["db_path"]))
    for f in (f1, f2):
        fid = db.add_frame(f)
        assert c.get(f"/api/frames/{fid}/image").status_code == 404


# =============================================================================== timeline / sun
def test_timeline_series_markers_and_sun(env):
    c = env["client"]
    d = c.get("/api/timeline", params={"since": "2026-09-21T17:00:00Z", "until": "2026-09-21T19:00:00Z",
                                       "bucket_s": 600}).json()
    assert d["bucket_s"] == 600 and d["since_oslo"] == "2026-09-21T19:00:00+02:00"
    sky = d["series"]["sky_luma"]["points"]
    assert len(sky) == 12
    # first bucket: minutes 0..9 -> luma 100..109, mean 104.5, centred at +5 min
    assert sky[0] == [int((T0 + timedelta(minutes=5)).timestamp() * 1000), 104.5, 10]
    assert sky[-1] == [int((T0 + timedelta(minutes=115)).timestamp() * 1000), 215.0, 11]   # sample at 'until' included
    assert d["series"]["scene_luma"]["points"][3][1] == 80.0
    rain = {p[0]: p[1] for p in d["series"]["rain_visual"]["points"]}
    assert rain[int((T0 + timedelta(minutes=35)).timestamp() * 1000)] == 0.6     # max of 0.6 and present=False -> 0
    lanes = {l["key"]: l for l in d["lanes"]}
    assert {m["kind"] for m in lanes["aircraft"]["markers"]} == {"audio_aircraft", "gesture_point_up"}
    assert lanes["board"]["n"] == 5 and lanes["alerts"]["n"] == 3
    assert all(m["label"] for m in lanes["aircraft"]["markers"])
    sun = d["sun"]
    assert (sun["lat"], sun["lon"]) == REF and "hotspots.json" in sun["source"]
    assert sun["points"][0][0] == int(T0.timestamp() * 1000)
    ev = [x["event"] for x in sun["crossings"]]
    assert ev[:2] == ["sunset", "civil dusk"]                   # 21.09 at 61 N: ~19:20 and ~20:05 CEST
    # default window ends at the newest observation; window= sets its length
    d2 = c.get("/api/timeline", params={"window": "1h"}).json()
    assert d2["until"] == d2["data_max"]
    assert A.unix_of(d2["until"]) - A.unix_of(d2["since"]) == 3600
    assert c.get("/api/timeline", params={"window": "soon"}).status_code == 400
    assert c.get("/api/timeline", params={"since": "2026-09-22T00:00:00Z", "until": "2026-09-21T00:00:00Z"}).status_code == 400


def test_sun_position_matches_skyfield():
    from hordewatch.astro import ephem
    if not ephem.available():
        pytest.skip("skyfield data not available")
    times = [datetime(2026, 9, 21, h, 17, tzinfo=UTC) for h in (4, 8, 11, 15, 17, 19, 23)]
    for lat, lon in [(61.245, 10.87), (58.5, 5.9), (64.0, 13.0)]:
        az_ref, alt_ref = ephem.altaz_grid(ephem.body_places("sun", times), [lat], [lon], refraction=False)
        alt, az = A.sun_position([t.timestamp() for t in times], lat, lon)
        assert np.max(np.abs(alt - alt_ref[0])) < 0.03
        up = alt_ref[0] > -5
        dz = (az[up] - az_ref[0][up] + 180) % 360 - 180
        assert np.max(np.abs(dz)) < 0.1


def test_sun_crossings_are_on_threshold():
    t0 = datetime(2026, 9, 21, 12, 0, tzinfo=UTC).timestamp()
    cr = A.sun_crossings(t0, t0 + 86400, *REF)
    names = [c["event"] for c in cr]
    assert names == ["sunset", "civil dusk", "nautical dusk", "nautical dawn", "civil dawn", "sunrise"]
    for c in cr:
        alt, _ = A.sun_position([c["t"] / 1000.0], *REF)
        assert abs(alt[0] - c["elev_deg"]) < 0.02
    # independent check against skyfield's almanac (DE421, -0.8333 deg horizon)
    from hordewatch.astro import ephem
    if not ephem.available():
        pytest.skip("skyfield data not available")
    from skyfield import almanac
    from skyfield.api import wgs84
    ts, eph = ephem._skyfield()
    f = almanac.sunrise_sunset(eph, wgs84.latlon(*REF))
    times, ups = almanac.find_discrete(ts.from_datetime(datetime.fromtimestamp(t0, UTC)),
                                       ts.from_datetime(datetime.fromtimestamp(t0 + 86400, UTC)), f)
    ref = {("sunrise" if up else "sunset"): tt.utc_datetime().timestamp() for tt, up in zip(times, ups)}
    ours = {c["event"]: c["t"] / 1000.0 for c in cr if c["event"] in ("sunrise", "sunset")}
    assert abs(ours["sunset"] - ref["sunset"]) < 60 and abs(ours["sunrise"] - ref["sunrise"]) < 60
    assert datetime.fromtimestamp(ours["sunset"], UTC).strftime("%H:%M") in ("17:19", "17:20", "17:21")   # 19:20 CEST


# =============================================================================== map / engine outputs
def test_hotspots_layers_history_and_output_files(env):
    c = env["client"]
    h = c.get("/api/hotspots").json()
    assert h["available"] and h["credible_km2"]["0.5"] == 817.8 and len(h["hotspots"]) == 3
    s1, s2 = h["hotspots"][0], h["hotspots"][1]
    # computed link matches hordejakt.cli.map_links (EPSG:25833 northing/easting) for the known cell
    assert "lat=6797082&lon=278451" in s1["norgeskart"] and s1["google_maps"].endswith("query=61.24500,10.87000")
    assert s2["norgeskart"] == "https://norgeskart.no/#!given"                    # links from the file are kept
    assert [g["group"] for g in s1["support"]] == ["elevation_hint", "aircraft", "travel"]
    assert s1["against"] == [{"group": "forest_species", "loglik": -0.33}]
    assert h["map_url"].startswith("output/map.html?v=")
    sc = c.get("/api/hotspots", params={"source": "scenarios"}).json()
    assert sc["hotspots"][0]["fragility"] == 0.64 and sc["hotspots"][0]["norgeskart"].startswith("https://norgeskart.no/")
    assert sc["scenarios"][0]["name"] == "base" and sc["credible_km2"]["0.5"] == 860.3
    runs = c.get("/api/engine/history").json()["runs"]
    assert [r["top"]["lat"] for r in runs] == [61.2, 61.1] and runs[0]["material"] is True
    L = c.get("/api/layers").json()["layers"]
    assert len(L) == 1 and L[0]["name"] == "hw_test" and L[0]["reliability"] == 0.4
    assert L[0]["n_cells"] == 17 * 30 and L[0]["peak"]["lat"] == pytest.approx(61.035) and L[0]["peak"]["lon"] == pytest.approx(10.61)
    assert c.get("/output/map.html").text.startswith("<html>")
    assert c.get("/output/hotspots.json").status_code == 200
    assert c.get("/output/posterior.npz").status_code == 404
    assert c.get("/output/missing.html").status_code == 404
    assert c.get("/output/..%2Fhw.sqlite").status_code == 404


def test_hotspots_missing_files_fail_soft(tmp_path):
    app = A.create_app(tmp_path / "empty.sqlite", tmp_path / "no_output", layers_dir=tmp_path / "no_layers", notifier=None)
    c = TestClient(app)
    assert c.get("/api/hotspots").json() == {"source": "base", "file": "hotspots.json", "available": False, "hotspots": []}
    assert c.get("/api/layers").json()["layers"] == []
    assert c.get("/api/engine/history").json()["runs"] == []
    assert c.get("/api/observations").json() == {"rows": [], "next": None}
    assert c.get("/api/frames/latest").json() == {}
    st = c.get("/api/status").json()
    assert st["runner_alive"] is False and st["max_ids"]["observations"] == 0
    tl = c.get("/api/timeline").json()
    assert tl["series"]["sky_luma"]["points"] == [] and tl["sun"]["source"] == "default reference point"


# =============================================================================== calibration / status
def test_calibration_get_and_manual_overrides(env):
    c = env["client"]
    d = c.get("/api/calibration").json()
    assert d["latency"]["latency_s"] == 32.5 and d["latency"]["latency_sigma_s"] == 6.0 and d["latency"]["audio_offset_s"] == 0.4
    assert d["latency"]["config_latency_s"] == 30.0
    ac = d["camera"]["astro_camera"]
    assert ac["focal_px"] == pytest.approx(1068.0) and ac["hfov_deg"] == pytest.approx(61.87, abs=0.02)
    att = ac["implied_attitude"]                          # G -> attitude at the #1 hotspot round-trips exactly
    assert (att["heading_deg"], att["pitch_deg"], att["roll_deg"]) == pytest.approx(TRUE_ATT, abs=0.01)
    assert d["camera"]["prior"]["heading_deg"] == 219.6 and d["camera"]["config"]["heading_deg"] == 220.0
    keys = {r["key"] for r in d["rows"]}
    assert "latency_s" in keys and "bridge_state:adsb" not in keys and d["internal_keys"] == ["bridge_state:adsb"]
    assert {e["kind"] for e in d["evidence"]} == {"stream_latency", "clock_seen"}
    # manual overrides: allow-listed, range-checked, audited as an already-acknowledged event
    assert c.post("/api/calibration", json={"key": "latency_s", "value": 41}).json() == {"key": "latency_s", "value": 41.0}
    assert c.get("/api/calibration").json()["latency"]["latency_s"] == 41.0
    audit = c.get("/api/events", params={"kind": "calibration_manual"}).json()["rows"][0]
    assert audit["status"] == "ack" and audit["value"] == {"key": "latency_s", "old": 32.5, "new": 41.0}
    assert c.post("/api/calibration", json={"key": "latency_s", "value": 5000}).status_code == 400
    assert c.post("/api/calibration", json={"key": "latency_s", "value": "abc"}).status_code == 400
    assert c.post("/api/calibration", json={"key": "astro_camera", "value": {}}).status_code == 400
    r = c.post("/api/calibration", json={"key": "camera_attitude", "value": {"pitch_deg": 1.2, "pitch_sigma_deg": 0.3}}).json()
    assert r["value"] == {"pitch_deg": 1.2, "pitch_sigma_deg": 0.3, "method": "manual (dashboard)"}
    assert env["db"].calibration("camera_attitude")["method"] == "manual (dashboard)"
    assert c.post("/api/calibration", json={"key": "camera_attitude", "value": {"bogus": 1}}).status_code == 400
    assert c.post("/api/calibration", json={"key": "camera_attitude", "value": {"roll_deg": 80}}).status_code == 400


def test_status(env):
    s = env["client"].get("/api/status").json()
    ids = env["ids"]
    assert s["max_ids"]["frames"] == ids["fC"] and s["events_new"] == 2
    assert s["runner_alive"] is True and s["last_write_age_s"] < 60
    assert s["stream_health"]["value"]["bitrate_kbps"] == 2500
    assert s["latency_s"] == 32.5 and s["latest_frame"]["image"]["id"] == ids["fB"]


# =============================================================================== SSE
def _insert_later(db, delay, fn):
    def run():
        time.sleep(delay)
        fn()
    th = threading.Thread(target=run, daemon=True)
    th.start()
    return th


def test_sse_yields_row_inserted_after_connect(env):
    c, db = env["client"], env["db"]
    store = env["app"].state.store
    mo, me = store.max_ids()
    new_id = {}

    def when_connected():
        t_end = time.time() + 5
        while store.sse_clients == 0 and time.time() < t_end:
            time.sleep(0.01)
        time.sleep(0.1)
        new_id["o"] = _obs(db, "audio_aircraft", T0 + timedelta(hours=3), {"snr_db": 9.0}, "audio_events", 0.6)

    th = threading.Thread(target=when_connected, daemon=True)
    th.start()
    t = time.time()
    r = c.get("/api/stream", params={"max_events": 1, "timeout": 10, "poll_s": 0.05})   # default cursor = "now"
    th.join()
    assert time.time() - t < 8
    assert r.headers["content-type"].startswith("text/event-stream")
    evs = parse_sse(r.text)
    assert evs[0]["event"] == "retry"
    assert evs[1]["event"] == "hello" and evs[1]["data"]["obs_cursor"] == mo and evs[1]["id"] == f"o{mo}.e{me}"
    obs = [e for e in evs if e["event"] == "observation"]
    assert len(obs) == 1 and obs[0]["data"]["id"] == new_id["o"] and obs[0]["data"]["kind"] == "audio_aircraft"
    assert obs[0]["data"]["summary"].startswith("aircraft noise SNR 9.0 dB")
    assert obs[0]["id"] == f"o{new_id['o']}.e{me}"


def test_sse_explicit_cursor_events_and_resume(env):
    c, db, ids = env["client"], env["db"], env["ids"]
    mo, me = env["app"].state.store.max_ids()
    _insert_later(db, 0.2, lambda: db.add_event(T0 + timedelta(hours=4), "whiteboard_text", "NY TAVLE", {"text": "NY"}))
    r = c.get("/api/stream", params={"since_obs": mo, "since_event": me, "max_events": 1, "timeout": 10, "poll_s": 0.05})
    ev = [e for e in parse_sse(r.text) if e["event"] == "event"]
    assert len(ev) == 1 and ev[0]["data"]["summary"] == "NY TAVLE" and ev[0]["data"]["status"] == "new"
    assert ev[0]["id"] == f"o{mo}.e{me + 1}"
    # Last-Event-ID wins over query cursors: resume right after the gesture observation
    r = c.get("/api/stream", params={"since_obs": mo, "max_events": 3, "timeout": 5, "poll_s": 0.05},
              headers={"Last-Event-ID": f"o{ids['gesture']}.e{me + 1}"})
    got = [e["data"]["id"] for e in parse_sse(r.text) if e["event"] == "observation"]
    assert got == [ids["gesture"] + 1, ids["gesture"] + 2, ids["gesture"] + 3]


def test_sse_kind_filter_and_event_update(env):
    c, db, ids = env["client"], env["db"], env["ids"]
    mo, me = env["app"].state.store.max_ids()

    def later():
        _obs(db, "sky_photometry", T0 + timedelta(hours=5), {"luma": 1.0}, "sky", 0.5)        # filtered out
        time.sleep(0.15)
        c.post(f"/api/events/{ids['ev_eng']}/ack")                                          # broadcast on the bus
        time.sleep(0.15)
        _obs(db, "whiteboard_text", T0 + timedelta(hours=5), {"text": "TEST"}, "whiteboard", 0.9)

    _insert_later(db, 0.2, later)
    r = c.get("/api/stream", params={"kinds": "whiteboard_text", "since_obs": mo, "since_event": me, "max_events": 2,
                                     "timeout": 10, "poll_s": 0.05})
    evs = parse_sse(r.text)
    names = [e["event"] for e in evs if e["event"] in ("observation", "event_update")]
    assert names == ["event_update", "observation"]
    upd = next(e for e in evs if e["event"] == "event_update")["data"]
    assert upd == {"id": ids["ev_eng"], "status": "ack"}
    ob = next(e for e in evs if e["event"] == "observation")["data"]
    assert ob["kind"] == "whiteboard_text" and ob["value"]["text"] == "TEST"


def test_sse_timeout_heartbeat_and_calibration_change(env):
    c, db = env["client"], env["db"]
    _insert_later(db, 0.3, lambda: db.set_calibration("latency_s", 28.0))
    r = c.get("/api/stream", params={"timeout": 1.2, "poll_s": 0.05, "heartbeat_s": 0.5})
    assert r.status_code == 200
    assert ": ping" in r.text
    cal = [e for e in parse_sse(r.text) if e["event"] == "calibration"]
    assert cal and cal[0]["data"]["latency_s"] == 28.0


def _free_port():
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
    finally:
        s.close()


def test_sse_live_uvicorn_server(env):
    """End to end over a real socket: the browser-like client sees a row the 'runner' inserts."""
    import httpx
    import uvicorn
    try:
        port = _free_port()
    except OSError as e:
        pytest.skip(f"cannot bind loopback: {e}")
    server = uvicorn.Server(uvicorn.Config(env["app"], host="127.0.0.1", port=port, log_level="warning",
                                           timeout_graceful_shutdown=1))
    th = threading.Thread(target=server.run, daemon=True)
    th.start()
    t_end = time.time() + 10
    while not server.started and time.time() < t_end:
        time.sleep(0.05)
    if not server.started:
        pytest.skip("uvicorn did not start")
    got = None
    try:
        with httpx.Client(trust_env=False, timeout=10) as cl:
            assert cl.get(f"http://127.0.0.1:{port}/api/health").json()["ok"]
            with cl.stream("GET", f"http://127.0.0.1:{port}/api/stream", params={"poll_s": 0.05}) as r:
                buf, inserted = "", False
                for chunk in r.iter_text():
                    buf += chunk
                    if not inserted and "event: hello" in buf:
                        _obs(env["db"], "gesture_point_up", T0 + timedelta(hours=6), {"side": "right"}, "gesture", 0.8)
                        inserted = True
                    m = re.search(r"event: observation\ndata: (.*)\n", buf)
                    if m:
                        got = json.loads(m.group(1))
                        break
                    if time.time() > t_end:
                        break
    finally:
        server.should_exit = True
        th.join(5)
    assert got is not None and got["kind"] == "gesture_point_up" and got["value"]["side"] == "right"


# =============================================================================== ntfy notifier
def test_ntfy_notifier_cursor_filters_rate_limit_and_fail_soft(env):
    db, db_path = env["db"], env["db_path"]
    posts = []
    n = NtfyNotifier(db_path, topic="hw-test", click_url="http://localhost:8787/", post=posts.append, max_per_minute=100)
    assert n.step() == 0 and posts == []                               # first start: backlog is not pushed
    assert db.calibration(CURSOR_KEY) == env["ids"]["ev_lat"]
    now = datetime.now(UTC)
    e1 = db.add_event(now, "whiteboard_text", "Ny tavle: SØR FOR VEIEN", {})
    db.add_event(now, "calibration_manual", "manual", {})                  # excluded by default
    e3 = db.add_event(now, "engine_ranking_change", "top moved", {})
    db.con.execute("UPDATE events SET created=? WHERE id=?", (iso(now - timedelta(hours=2)), e3))   # stale
    db.con.commit()
    assert n.step() == 1
    p = posts[0]
    assert p["topic"] == "hw-test" and p["priority"] == 5 and "whiteboard_text" in p["title"]
    assert p["message"] == "Ny tavle: SØR FOR VEIEN" and p["click"] == "http://localhost:8787/"
    assert db.calibration(CURSOR_KEY) == e3
    # network failure: exception, cursor unchanged; the next successful step delivers
    e4 = db.add_event(datetime.now(UTC), "astro", "astro fix", {})

    def boom(_):
        raise urllib.error.URLError("no route to host")
    n._post = boom
    with pytest.raises(urllib.error.URLError):
        n.step()
    assert db.calibration(CURSOR_KEY) == e3
    n._post = posts.append
    assert n.step() == 1 and posts[-1]["message"] == "astro fix" and db.calibration(CURSOR_KEY) == e4
    # burst beyond the per-minute budget: newest go out individually, the rest folded into one summary
    n2 = NtfyNotifier(db_path, topic="hw-test", post=posts.append, max_per_minute=3)
    for k in range(6):
        db.add_event(datetime.now(UTC), "aircraft_layer", f"layer {k}", {})
    posts.clear()
    assert n2.step() == 3
    assert "4 more alerts" in posts[0]["title"] and [x["message"] for x in posts[1:]] == ["layer 4", "layer 5"]
    db.add_event(datetime.now(UTC), "aircraft_layer", "layer 6", {})
    assert n2.step() == 0                                             # budget used up: cursor waits
    # background thread survives a dead network and records the error
    n3 = NtfyNotifier(db_path, topic="hw-test", post=boom, poll_s=0.05, warn_every_s=0)
    db.add_event(datetime.now(UTC), "astro", "x", {})
    n3.start()
    time.sleep(0.4)
    n3.stop()
    assert n3.last_error and "no route" in n3.last_error


def test_create_app_builds_ntfy_notifier_from_config(tmp_path):
    cfg = {"dashboard": {"ntfy": {"topic": "hw-abc", "server": "http://127.0.0.1:9", "priority": {"astro": 5}}}}
    app = A.create_app(tmp_path / "x.sqlite", tmp_path, config=cfg)
    n = app.state.notifier
    assert isinstance(n, NtfyNotifier) and n.topic == "hw-abc" and n.priority["astro"] == 5
    assert A.create_app(tmp_path / "y.sqlite", tmp_path).state.notifier is None


# =============================================================================== CLI + launcher
def test_main_resolve_settings(tmp_path, monkeypatch):
    from hordewatch.dashboard import __main__ as M
    monkeypatch.delenv("HORDEWATCH_NTFY_TOPIC", raising=False)
    cfgf = tmp_path / "hw.yaml"
    cfgf.write_text(f"db: {tmp_path / 'cfg.sqlite'}\ndashboard:\n  port: 9001\n  sun_ref: [61.0, 10.0]\n")
    a = M.build_parser().parse_args(["--config", str(cfgf), "--ntfy-topic", "hw-xyz"])
    s = M.resolve_settings(a)
    assert s["port"] == 9001 and s["host"] == "127.0.0.1" and str(s["db_path"]) == str(tmp_path / "cfg.sqlite")
    assert s["config"]["dashboard"]["ntfy"] == {"topic": "hw-xyz", "click_url": "http://localhost:9001/"}
    assert s["config"]["dashboard"]["sun_ref"] == [61.0, 10.0]
    s2 = M.resolve_settings(M.build_parser().parse_args(["--db", str(tmp_path / "cli.sqlite"), "--port", "8899"]))
    assert s2["port"] == 8899 and str(s2["db_path"]) == str(tmp_path / "cli.sqlite")


def test_launcher_script_dry_run(tmp_path):
    sh = ROOT / "scripts" / "hordewatch_all.sh"
    assert os.access(sh, os.X_OK)
    assert subprocess.run(["bash", "-n", str(sh)], capture_output=True).returncode == 0
    envv = {**os.environ, "PYTHON": sys.executable, "HORDEWATCH_LOG_DIR": str(tmp_path / "logs")}
    envv.pop("HORDEWATCH_CONFIG", None)
    r = subprocess.run([str(sh), "--dry-run", "--port", "8799"], capture_output=True, text=True, env=envv, timeout=60)
    assert r.returncode == 0, r.stderr
    assert "runner: " in r.stdout and "-m hordewatch.runner" in r.stdout
    assert "-m hordewatch.dashboard --db data/hordewatch/hordewatch.sqlite --host 127.0.0.1 --port 8799" in r.stdout
    assert "http://127.0.0.1:8799/" in r.stdout
    r2 = subprocess.run([str(sh), "--dry-run", "--no-runner"], capture_output=True, text=True, env=envv, timeout=60)
    assert r2.returncode == 0 and "runner: " not in r2.stdout and "dashboard: " in r2.stdout
    r3 = subprocess.run([str(sh), "--bogus"], capture_output=True, text=True, env=envv, timeout=60)
    assert r3.returncode == 2
    assert not (tmp_path / "logs").exists()                           # dry run writes nothing


# =============================================================================== adversarial review tests
def test_layer_peaks_match_engine_live_build(env, tmp_path, monkeypatch):
    """The layers tab must report where hordejakt.layers.live.build (the engine) actually puts each grid.
    Files are written with the real producer (bridges.common.write_layer) plus hand-made edge cases."""
    from hordejakt.grid import GRID, Grid
    from hordejakt.layers import live
    from hordewatch.bridges.common import write_layer
    d = tmp_path / "live_layers"
    # (a) full-GRID layer, peak at a known cell
    full = np.full(GRID.shape, -3.0)
    full[GRID.index(61.3, 10.95)] = 4.0
    write_layer(d / "hw_full.npz", full, name="hw_full", reliability=0.4, independence_group="t_full")
    # (b) sub-grid written by write_layer (stores lat_min/lon_min/dlat/dlon)
    sub_g = Grid(lat_min=61.1, lat_max=61.2, lon_min=10.6, lon_max=10.8)
    sub = np.full(sub_g.shape, -2.0)
    sub[5, 7] = 3.0
    write_layer(d / "hw_sub.npz", sub, name="hw_sub", reliability=0.3, independence_group="t_sub", grid=sub_g)
    # (c) hand-made sub-grid with a *different* cell size: the engine ignores dlat/dlon and pastes it with
    #     GRID cells, so the evidence lands elsewhere than the file claims
    ll = np.full((10, 10), -1.0)
    ll[6, 4] = 2.0
    np.savez(d / "hw_coarse.npz", loglik=ll, lat_min=61.0, lon_min=10.5, dlat=0.01, dlon=0.02,
             meta=json.dumps({"name": "hw_coarse", "reliability": 0.2}))
    # (d) sub-grid whose origin lies outside GRID: the engine skips it
    np.savez(d / "hw_out.npz", loglik=np.zeros((4, 4)), lat_min=70.0, lon_min=10.0, dlat=0.005, dlon=0.01,
             meta=json.dumps({"name": "hw_out", "reliability": 0.2}))
    monkeypatch.setattr(live, "LIVE_DIR", d)
    engine = {L.name: L for L in live.build(GRID, {})}
    assert set(engine) == {"hw_full", "hw_sub", "hw_coarse"}                # hw_out skipped by the engine

    app = A.create_app(env["db_path"], env["out"], archive_dir=env["archive"], layers_dir=d, notifier=None)
    r = TestClient(app).get("/api/layers").json()
    assert r["engine_dir"] == str(d) and r["engine_reads_this_dir"] is True and r["warning"] is None
    info = {x["name"]: x for x in r["layers"]}
    lats, lons = GRID.lats, GRID.lons
    for name, L in engine.items():
        i, j = np.unravel_index(np.nanargmax(L.loglik), L.loglik.shape)
        assert info[name]["peak"]["lat"] == pytest.approx(lats[i], abs=1e-6), name
        assert info[name]["peak"]["lon"] == pytest.approx(lons[j], abs=1e-6), name
        assert info[name]["n_cells"] == int(np.isfinite(L.loglik).sum()), name
        assert info[name]["reliability"] == pytest.approx(L.reliability) and info[name]["used_by_engine"] is True
    # the coarse file: the naive reading (file's own dlat) would claim 61.06 N 10.58 E - the engine uses 61.03 / 10.54
    assert info["hw_coarse"]["peak"]["lat"] == pytest.approx(61.03) and info["hw_coarse"]["peak"]["lon"] == pytest.approx(10.54)
    assert any("cell size" in p for p in info["hw_coarse"]["problems"])
    assert info["hw_out"]["used_by_engine"] is False and info["hw_out"]["peak"] is None
    assert info["hw_full"]["problems"] == [] and info["hw_sub"]["problems"] == []
    # (e) a file without meta makes live.build raise (whole engine run fails): flagged, not shown as fine
    np.savez(d / "hw_nometa.npz", loglik=np.zeros(GRID.shape))
    with pytest.raises(KeyError):
        live.build(GRID, {})
    bad = {x["file"]: x for x in TestClient(app).get("/api/layers").json()["layers"]}["hw_nometa.npz"]
    assert bad["engine_ok"] is False and any("engine run fails" in p for p in bad["problems"])
    # a dashboard pointed at another dir than the engine reads says so
    monkeypatch.setattr(live, "LIVE_DIR", tmp_path / "elsewhere")
    assert "do not reach the posterior" in TestClient(app).get("/api/layers").json()["warning"]


def test_manual_camera_attitude_reaches_astro_solver_as_entered(env):
    """The level override must mean to the astro solver exactly what the user typed. The solver merges
    camera_attitude over {pitch 0+-15, roll 0+-3, heading None} and uses an axis only with its sigma."""
    from hordewatch.astro.solver import AstroBridge
    c, db = env["client"], env["db"]
    # a sigma without its value would silently become 'pitch = 0 +- 0.3 deg' (~33 km of astro-fix bias)
    r = c.post("/api/calibration", json={"key": "camera_attitude", "value": {"pitch_sigma_deg": 0.3, "roll_deg": 0.2,
                                                                             "roll_sigma_deg": 0.5}})
    assert r.status_code == 400 and "pitch" in r.json()["detail"]
    # a heading without sigma is ignored by the solver: refuse instead of pretending it was applied
    assert c.post("/api/calibration", json={"key": "camera_attitude", "value": {"heading_deg": 219.6}}).status_code == 400
    assert db.calibration("camera_attitude") is None
    assert c.post("/api/calibration", json={"key": "camera_attitude", "value": {
        "pitch_deg": 1.2, "pitch_sigma_deg": 0.3, "valid_at": "2099-01-01T00:00:00Z"}}).status_code == 400   # future
    r = c.post("/api/calibration", json={"key": "camera_attitude", "value": {
        "heading_deg": 219.6, "heading_sigma_deg": 1.5, "pitch_deg": 1.2, "pitch_sigma_deg": 0.3,
        "valid_at": "2026-09-22T12:00:00+02:00"}})
    assert r.status_code == 200
    lev = AstroBridge({"_global": {"camera": {"heading_deg": 220.0, "hfov_deg": 70.0}}})._level(db)
    assert lev.pitch == (1.2, 0.3) and lev.heading == (219.6, 1.5)
    assert lev.roll == (0.0, 3.0)                                        # untouched axis keeps the weak default
    assert lev.att_t == datetime(2026, 9, 22, 10, 0, tzinfo=UTC).timestamp()   # tied to the pose of that time
    assert "manual (dashboard)" in lev.source


def test_implied_attitude_uses_the_solvers_own_camera_convention(env):
    """astro_camera.G produced by the solver's own ApproxCamera (not re-built with the test's formula)
    must invert to the attitude it was made from at the reference point."""
    from hordewatch.astro.stars import ApproxCamera
    cam = ApproxCamera.from_attitude(221.0, -0.7, 1.3, 0.83, *REF)
    env["db"].set_calibration("astro_camera", {"method": "stars", "G": [np.asarray(cam.G).tolist()], "f": 0.83})
    att = env["client"].get("/api/calibration").json()["camera"]["astro_camera"]["implied_attitude"]
    assert (att["heading_deg"], att["pitch_deg"], att["roll_deg"]) == pytest.approx((221.0, -0.7, 1.3), abs=0.01)


def test_timeline_all_window_and_long_range_sun_crossings(env):
    c = env["client"]
    d = c.get("/api/timeline", params={"window": "all"}).json()
    # 'All' = oldest..newest observation (the page used to ask for since=3650d: a 10-year axis)
    assert d["since"] == d["data_min"] and d["until"] == d["data_max"]
    assert A.unix_of(d["until"]) - A.unix_of(d["since"]) < 86400
    assert c.get("/api/timeline", params={"window": "0h"}).status_code == 400
    # crossings stay exact over years (the old fixed 20000-point grid sampled every ~53 min over 2 years)
    t0 = datetime(2026, 1, 1, tzinfo=UTC).timestamp()
    t1 = t0 + 2 * 365 * 86400
    cr = A.sun_crossings(t0, t1, *REF)
    sunsets = [x for x in cr if x["event"] == "sunset"]
    assert abs(len(sunsets) - 730) <= 1
    alt, _ = A.sun_position(np.array([x["t"] / 1000.0 for x in cr]), *REF)
    assert np.max(np.abs(alt - np.array([x["elev_deg"] for x in cr]))) < 0.005
    # summer at 61.2 N: the sun never reaches -12 deg around the June solstice -> no nautical events then
    june = [x for x in cr if datetime.fromtimestamp(x["t"] / 1000, UTC).strftime("%m-%d") == "06-21"]
    assert june and not any("nautical" in x["event"] for x in june)


def test_series_sql_matches_python_and_ignores_twilight_markers(env):
    store = env["app"].state.store
    db = env["db"]
    # twilight markers are stored as sky_photometry with the *threshold* as luma: not a measurement
    for k in range(3):
        _obs(db, "sky_photometry", T0 + timedelta(minutes=12, seconds=20 * k),
             {"luma": 1.0, "region": "twilight_marker", "twilight_marker": {"event": "dusk"}}, "sky", 0.55)
    _obs(db, "cloud_fraction", T0 + timedelta(minutes=13), {"fraction": "n/a"}, "sky", 0.5)        # non-numeric
    _obs(db, "cloud_fraction", T0 + timedelta(minutes=14), {"method": "x"}, "sky", 0.5)            # missing
    _obs(db, "scene_photometry", T0 + timedelta(minutes=15, seconds=5), {"luma": float("inf")}, "sky", 0.5)  # 'Infinity'
    _obs(db, "scene_photometry", T0 + timedelta(minutes=15, seconds=9), {"luma": float("nan")}, "sky", 0.5)  # 'NaN'
    q = {"since": "2026-09-21T17:00:00Z", "until": "2026-09-21T19:00:00Z"}
    rng = np.random.default_rng(3)
    for b in [60, 600, 437.5, float(rng.uniform(5, 3000))]:
        sql = env["client"].get("/api/timeline", params={**q, "bucket_s": b}).json()
        store.json1 = False                                                   # force the Python fallback
        try:
            py = env["client"].get("/api/timeline", params={**q, "bucket_s": b}).json()
        finally:
            store.json1 = True
        for key in sql["series"]:
            assert sql["series"][key]["points"] == py["series"][key]["points"], (key, b)
            assert sql["series"][key]["n"] == py["series"][key]["n"], (key, b)
    d = env["client"].get("/api/timeline", params={**q, "bucket_s": 600}).json()
    first = d["series"]["sky_luma"]["points"][1]                              # minutes 10..19: luma 110..119
    assert first[1] == 114.5 and first[2] == 10                               # markers (luma 1.0) not averaged in
    scene = d["series"]["scene_luma"]["points"][1]
    assert scene == [int((T0 + timedelta(minutes=15)).timestamp() * 1000), 80.0, 10]   # inf/NaN dropped, bucket kept


def test_sse_resume_after_long_disconnect_is_capped(env):
    c, db = env["client"], env["db"]
    mo, me = env["app"].state.store.max_ids()
    for k in range(40):
        _obs(db, "audio_voice", T0 + timedelta(hours=7, seconds=k), {"snr_db": float(k)}, "audio_events", 0.5)
    r = c.get("/api/stream", params={"max_replay": 10, "max_events": 10, "timeout": 5, "poll_s": 0.05},
              headers={"Last-Event-ID": f"o{mo}.e{me}"})
    evs = parse_sse(r.text)
    gap = [e for e in evs if e["event"] == "gap"]
    assert len(gap) == 1 and gap[0]["data"]["skipped_obs"] == 30 and gap[0]["data"]["from_id"] == mo
    got = [e["data"]["id"] for e in evs if e["event"] == "observation"]
    assert got == list(range(mo + 31, mo + 41))                               # exactly the 10 newest, in order
    # a cursor from a replaced (smaller) DB would hide every new row: it is reset and announced
    r = c.get("/api/stream", params={"timeout": 0.5, "poll_s": 0.05}, headers={"Last-Event-ID": "o999999.e999999"})
    hello = [e for e in parse_sse(r.text) if e["event"] == "hello"][0]["data"]
    assert hello["obs_cursor"] == mo + 40 and hello["gap"]["reason"].startswith("cursor ahead")


def test_sse_calibration_message_only_for_real_calibrations(env):
    c, db = env["client"], env["db"]

    def later():
        db.set_calibration("bridge_state:adsb", {"done": {"x": 1}})          # bridges persist state often
        db.set_calibration(CURSOR_KEY, 12345)                                 # ntfy cursor
        time.sleep(0.4)
        db.set_calibration("audio_offset_s", -1.5)

    _insert_later(db, 0.2, later)
    r = c.get("/api/stream", params={"timeout": 1.4, "poll_s": 0.05})
    cal = [e["data"] for e in parse_sse(r.text) if e["event"] == "calibration"]
    assert len(cal) == 1 and cal[0]["audio_offset_s"] == -1.5 and cal[0]["latency_s"] == 32.5


def test_kinds_counts_are_incremental_and_exact(env):
    c, db = env["client"], env["db"]
    k0 = {x["kind"]: x["n"] for x in c.get("/api/kinds").json()["kinds"]}
    _obs(db, "audio_bells", T0 + timedelta(hours=9), {"snr_db": 3.0}, "audio_events", 0.4)
    _obs(db, "sky_photometry", T0 - timedelta(days=2), {"luma": 5.0}, "sky", 0.4)       # older than all data
    d = c.get("/api/kinds").json()
    k1 = {x["kind"]: x for x in d["kinds"]}
    assert k1["audio_bells"]["n"] == k0["audio_bells"] + 1 and k1["sky_photometry"]["n"] == k0["sky_photometry"] + 1
    with sqlite3.connect(env["db_path"]) as con:
        truth = dict(con.execute("SELECT kind, COUNT(*) FROM observations GROUP BY kind").fetchall())
        tmin, tmax = con.execute("SELECT MIN(ts), MAX(ts) FROM observations").fetchone()
    assert {k: v["n"] for k, v in k1.items() if v["n"]} == truth
    assert env["app"].state.store.data_range() == (tmin, tmax)


def test_search_is_literal_and_ack_all_scales(env):
    c, db = env["client"], env["db"]
    pct = _obs(db, "vlm_description", T0, {"text": "100% overcast"}, "vlm", 0.3)
    und = _obs(db, "vlm_description", T0, {"text": "snake_case"}, "vlm", 0.3)
    _obs(db, "vlm_description", T0, {"text": "snakeXcase"}, "vlm", 0.3)    # matched only if '_' were a wildcard
    assert {x["id"] for x in c.get("/api/observations", params={"q": "%"}).json()["rows"]} == {pct}
    assert {x["id"] for x in c.get("/api/observations", params={"q": "snake_c"}).json()["rows"]} == {und}
    rows = [(iso(T0), "aircraft_layer", f"x{k}", "{}", "new", iso(T0)) for k in range(1500)]
    db.con.executemany("INSERT INTO events(ts, kind, summary, value, status, created) VALUES (?,?,?,?,?,?)", rows)
    db.con.commit()
    r = c.post("/api/events/ack_all").json()
    assert r["acked"] == 1500 + 2 and c.get("/api/events", params={"status": "new"}).json()["rows"] == []
    assert c.get("/api/frames/near", params={"ts": ""}).status_code == 400


def test_ntfy_bad_config_fails_soft_and_priorities_are_ntfy_integers(tmp_path):
    posts = []
    n = NtfyNotifier(_empty_db(tmp_path), topic="hw-ok", post=posts.append,
                     priority={"whiteboard_text": "urgent", "astro": "high", "aircraft_layer": 9})
    assert n.priority["whiteboard_text"] == 5 and n.priority["astro"] == 4 and n.priority["aircraft_layer"] == 5
    with pytest.raises(ValueError):
        NtfyNotifier(_empty_db(tmp_path), topic="has space/and slash")
    # a broken push section must not keep the dashboard from starting
    app = A.create_app(tmp_path / "z.sqlite", tmp_path, config={"dashboard": {"ntfy": {"topic": "bad topic!"}}})
    assert app.state.notifier is None and TestClient(app).get("/api/health").json()["ok"] is True


def _empty_db(tmp_path):
    p = tmp_path / "ntfy.sqlite"
    DB(p)
    return p
