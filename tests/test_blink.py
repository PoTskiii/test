import numpy as np
import pytest

from hordewatch import blink

FPS = 25.0


def morse_states(text, unit_s, fps=FPS, lead_s=1.0):
    """Frame-wise ON/OFF sequence for `text` in Morse with a given unit."""
    seq = [(False, lead_s)]
    words = text.split(" ")
    for wi, w in enumerate(words):
        for ci, ch in enumerate(w):
            code = blink.REVERSE[ch]
            for si, s in enumerate(code):
                seq.append((True, unit_s * (3 if s == "-" else 1)))
                if si < len(code) - 1:
                    seq.append((False, unit_s))
            if ci < len(w) - 1:
                seq.append((False, 3 * unit_s))
        if wi < len(words) - 1:
            seq.append((False, 7 * unit_s))
    seq.append((False, lead_s))
    frames = []
    for on, dur in seq:
        frames += [on] * int(round(dur * fps))
    return np.array(frames, bool)


def make_clip(states_by_point, shape=(240, 320), seed=0):
    rng = np.random.default_rng(seed)
    n = max(len(s) for s in states_by_point.values())
    base = rng.normal(60, 8, shape).astype(np.float32)
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    frames = np.empty((n,) + shape, np.float32)
    gain = 1 + 0.05 * np.sin(np.arange(n) / 40.0)  # camera auto-gain drift
    for k in range(n):
        f = base + rng.normal(0, 4, shape)
        for (x, y), st in states_by_point.items():
            on = st[k] if k < len(st) else False
            if isinstance(on, (float, np.floating)):
                amp = on
            else:
                amp = 150.0 if on else 0.0
            f += amp * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * 1.8 ** 2))
        frames[k] = np.clip(f * gain[k], 0, 255)
    times = np.arange(n) / FPS
    return frames.astype(np.uint8), times


def run_point(frames, times, x, y):
    sig = blink.point_signal(frames, x, y, radius=3)
    _, runs, contrast = blink.binarize(sig, times)
    return blink.classify(runs, contrast)


def test_morse_digits_and_letters():
    st = morse_states("HORDE 5008", unit_s=0.2)
    frames, times = make_clip({(100, 120): st})
    res = run_point(frames, times, 100, 120)
    assert res["morse"]["ok"] and res["morse"]["plausible"], res
    assert res["morse"]["text"] == "HORDE 5008"
    assert "Morse" in res["verdict"]


def test_norwegian_letters():
    st = morse_states("ØST", unit_s=0.24)
    frames, times = make_clip({(60, 60): st})
    assert run_point(frames, times, 60, 60)["morse"]["text"] == "ØST"


def test_regular_led_is_not_morse():
    n = int(60 * FPS)
    st = (np.arange(n) % 50) < 5      # 0.2 s on every 2 s
    frames, times = make_clip({(200, 80): st})
    res = run_point(frames, times, 200, 80)
    assert res["periodicity"]["regular"]
    assert abs(res["periodicity"]["period_s"] - 2.0) < 0.1
    assert "status LED" in res["verdict"]


def test_irregular_twinkle_is_flagged_as_reflection():
    rng = np.random.default_rng(3)
    n = int(60 * FPS)
    amp = np.clip(rng.gamma(0.6, 60, n), 0, 160)  # random glints of varying strength
    st = np.convolve(amp, np.ones(3) / 3, mode="same").astype(np.float32)
    frames, times = make_clip({(150, 150): list(st)})
    res = run_point(frames, times, 150, 150)
    assert not res["periodicity"].get("regular")
    assert not res["morse"].get("plausible")


def test_blink_groups_as_digits():
    fps = FPS
    seq = [False] * 25
    for g in [5, 1, 3]:
        for _ in range(g):
            seq += [True] * 6 + [False] * 6
        seq += [False] * 50
    frames, times = make_clip({(80, 180): np.array(seq)})
    res = run_point(frames, times, 80, 180)
    assert res["groups"]["ok"]
    assert res["groups"]["groups"] == [5, 1, 3]


def test_auto_finds_the_blinkers_and_video_roundtrip(tmp_path):
    cv2 = pytest.importorskip("cv2")
    st_morse = morse_states("SOS", unit_s=0.2, lead_s=2.0)
    n = len(st_morse)
    st_led = (np.arange(n) % 40) < 8
    frames, times = make_clip({(70, 90): st_morse, (250, 170): st_led})
    path = tmp_path / "clip.mp4"
    vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (frames.shape[2], frames.shape[1]))
    for f in frames:
        vw.write(cv2.cvtColor(f, cv2.COLOR_GRAY2BGR))
    vw.release()
    out = blink.analyze(path, auto=True, top=4, plot=False)
    pts = [(t["x"], t["y"]) for t in out["targets"]]
    assert any(abs(x - 70) <= 3 and abs(y - 90) <= 3 for x, y in pts), pts
    assert any(abs(x - 250) <= 3 and abs(y - 170) <= 3 for x, y in pts), pts
    morse_hit = [t for t in out["targets"] if abs(t["x"] - 70) <= 3 and abs(t["y"] - 90) <= 3][0]
    assert morse_hit["morse"]["text"] == "SOS"
