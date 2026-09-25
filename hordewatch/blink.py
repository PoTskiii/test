"""Blinking-light analysis: is it Morse, a digit code, an equipment LED, or a twinkling reflection?

A blink can only be judged from its timing, so this works on a short clip at the
stream's full frame rate (25/30 fps), not on the monitor's sparse frame samples.

    # 1) record 3 minutes of the live stream (on a machine that can reach YouTube)
    .venv/bin/python -m hordewatch.blink record --url https://www.youtube.com/watch?v=EQHgfmZicc8 --seconds 180 --out clip.mp4
    # 2a) you know where the light is (pixel coords in the clip; see --preview)
    .venv/bin/python -m hordewatch.blink analyze clip.mp4 --point 580,540 --radius 6
    # 2b) or let it find every blinking spot in the frame
    .venv/bin/python -m hordewatch.blink analyze clip.mp4 --auto
    # screen recordings / phone videos of the screen work too (use --auto or --point)

Method
  1. brightness(t) = mean of a small disc around the point minus the median of a
     surrounding ring (cancels camera auto-gain and global light changes);
  2. two-level quantisation (Otsu threshold with hysteresis, runs shorter than
     1.5 frames merged) -> alternating ON/OFF runs with durations;
  3. classify:
     - equipment LED: ON and OFF durations each nearly constant (CV < 0.15),
       strong autocorrelation peak -> period + duty cycle;
     - Morse: ON runs split into two clusters with ratio ~2.3-4 (dot/dash),
       OFF runs into 1/3/7-unit gaps -> decoded text incl. Æ Ø Å and digits;
     - blink groups: bursts of equal short flashes separated by long pauses ->
       counts per group (common way to signal digits, e.g. 5-0-0-8);
     - irregular: no stable timing -> most likely a reflection flickering as
       vegetation moves (check whether nearby leaves move at the same time).
  4. writes <clip>_blink.json and <clip>_blink.png (signal + decoded runs).

Caveats: YouTube re-encodes at 25-30 fps, so flashes shorter than ~80 ms can be
missed or aliased; the IR camera's own exposure can merge short gaps. Unit times
of 100-400 ms (typical for LED/Morse beacons) are resolved fine.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

MORSE = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F", "--.": "G", "....": "H",
    "..": "I", ".---": "J", "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O", ".--.": "P",
    "--.-": "Q", ".-.": "R", "...": "S", "-": "T", "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z", ".-.-": "Æ", "---.": "Ø", ".--.-": "Å",
    "-----": "0", ".----": "1", "..---": "2", "...--": "3", "....-": "4", ".....": "5",
    "-....": "6", "--...": "7", "---..": "8", "----.": "9",
    ".-.-.-": ".", "--..--": ",", "..--..": "?", "-..-.": "/", "-...-": "=", ".-.-.": "+",
}
REVERSE = {v: k for k, v in MORSE.items()}


# ----------------------------------------------------------------------------- signal
def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def read_video_gray(path, max_width=960, max_seconds=None):
    """Decode a video to (frames uint8 [N,H,W], times_s [N], fps)."""
    import cv2
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frames, times = [], []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        if g.shape[1] > max_width:
            s = max_width / g.shape[1]
            g = cv2.resize(g, (max_width, int(round(g.shape[0] * s))), interpolation=cv2.INTER_AREA)
        frames.append(g)
        times.append(t if t > 0 or not times else times[-1] + 1.0 / fps)
        if max_seconds and times[-1] >= max_seconds:
            break
    cap.release()
    if not frames:
        raise RuntimeError("no frames decoded")
    times = np.array(times, float)
    if not np.all(np.diff(times) > 0):  # some containers report 0 -> use nominal fps
        times = np.arange(len(frames)) / fps
    return np.stack(frames), times, float(fps)


def point_signal(frames, x, y, radius=5, ring=(10, 18)):
    """Disc mean minus ring median around (x, y) for every frame."""
    n, h, w = frames.shape
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.hypot(xx - x, yy - y)
    disc = d <= radius
    ringm = (d >= ring[0]) & (d <= ring[1])
    if not disc.any():
        raise ValueError("point outside frame")
    f = frames.reshape(n, -1).astype(np.float32)
    s_disc = f[:, disc.ravel()].max(axis=1) * 0.5 + f[:, disc.ravel()].mean(axis=1) * 0.5
    s_ring = np.median(f[:, ringm.ravel()], axis=1) if ringm.any() else 0.0
    return s_disc - s_ring


def find_blinkers(frames, top=8, min_sep=12):
    """Rank pixels whose brightness toggles between two levels (bimodal, many transitions)."""
    import cv2
    n, h, w = frames.shape
    f = frames.astype(np.float32)
    # local contrast vs. a blurred version, per frame -> small bright features only
    hp = np.stack([fr - cv2.GaussianBlur(fr, (0, 0), 6) for fr in f])
    hi = np.percentile(hp, 95, axis=0)
    lo = np.percentile(hp, 20, axis=0)
    swing = hi - lo
    mid = (hi + lo) / 2
    on = hp > mid[None]
    trans = np.abs(np.diff(on.astype(np.int8), axis=0)).sum(axis=0)
    # blinkers: large swing, several transitions, but not flickering every frame (noise)
    score = swing * np.clip(trans, 0, None) * (trans >= 4) * (trans <= 0.6 * n)
    score = cv2.GaussianBlur(score, (0, 0), 1.5)
    picks = []
    flat = np.argsort(score, axis=None)[::-1]
    for idx in flat[:20000]:
        y, x = divmod(int(idx), w)
        if score[y, x] <= 0:
            break
        if any((x - px) ** 2 + (y - py) ** 2 < min_sep ** 2 for px, py, _ in picks):
            continue
        picks.append((x, y, float(score[y, x])))
        if len(picks) >= top:
            break
    return picks


# ----------------------------------------------------------------------------- runs
def otsu_threshold(x):
    x = np.asarray(x, float)
    hist, edges = np.histogram(x, bins=128)
    c = (edges[:-1] + edges[1:]) / 2
    w0 = np.cumsum(hist)
    w1 = w0[-1] - w0
    m0 = np.cumsum(hist * c) / np.maximum(w0, 1)
    m1 = (np.sum(hist * c) - np.cumsum(hist * c)) / np.maximum(w1, 1)
    between = w0 * w1 * (m0 - m1) ** 2
    return float(c[np.argmax(between)])


def binarize(sig, times, min_frames=1.5):
    """-> (states bool[N], runs [(state, t_start, duration_s), ...], contrast)."""
    sig = np.asarray(sig, float)
    th0 = otsu_threshold(sig)
    lo_m = sig[sig <= th0].mean()
    hi_m = sig[sig > th0].mean() if (sig > th0).any() else th0
    # Otsu's between-class variance is flat across an empty gap and picks its
    # lower edge; use the midpoint of the two class means instead.
    th = (lo_m + hi_m) / 2
    spread = hi_m - lo_m
    noise = np.median(np.abs(sig - np.median(sig))) + 1e-6
    hyst = 0.15 * spread
    state = sig[0] > th
    states = np.zeros(len(sig), bool)
    for i, v in enumerate(sig):
        if state and v < th - hyst:
            state = False
        elif not state and v > th + hyst:
            state = True
        states[i] = state
    dt = np.median(np.diff(times)) if len(times) > 1 else 0.04
    runs = _runs(states, times, dt)
    # merge runs shorter than min_frames into neighbours (compression / exposure glitches)
    changed = True
    while changed and len(runs) > 2:
        changed = False
        for k in range(1, len(runs) - 1):
            if runs[k][2] < min_frames * dt:
                a, b, c = runs[k - 1], runs[k], runs[k + 1]
                runs[k - 1:k + 2] = [(a[0], a[1], a[2] + b[2] + c[2])]
                changed = True
                break
    return states, runs, float(spread / noise)


def _runs(states, times, dt):
    runs = []
    start = 0
    for i in range(1, len(states) + 1):
        if i == len(states) or states[i] != states[start]:
            t0 = times[start]
            t1 = times[i] if i < len(states) else times[-1] + dt
            runs.append((bool(states[start]), float(t0), float(t1 - t0)))
            start = i
    return runs


# ----------------------------------------------------------------------------- classifiers
def _cv(x):
    x = np.asarray(x, float)
    return float(np.std(x) / np.mean(x)) if len(x) and np.mean(x) > 0 else np.inf


def _two_clusters(x):
    """1-D 2-means; returns (low_centre, high_centre, labels) or None if not separable."""
    x = np.sort(np.asarray(x, float))
    if len(x) < 2:
        return None
    best = None
    for k in range(1, len(x)):
        a, b = x[:k], x[k:]
        sse = ((a - a.mean()) ** 2).sum() + ((b - b.mean()) ** 2).sum()
        if best is None or sse < best[0]:
            best = (sse, a.mean(), b.mean(), x[k - 1], x[k])
    _, m0, m1, left, right = best
    return m0, m1, (left + right) / 2


def decode_morse(runs):
    """Decode ON/OFF runs as Morse. Returns dict with text, unit_s, fit quality."""
    inner = runs[1:-1] if len(runs) > 2 else runs  # first/last runs are truncated by the clip
    on = [d for s, _, d in inner if s]
    off = [d for s, _, d in inner if not s]
    if len(on) < 3:
        return {"ok": False, "why": "too few flashes"}
    cl = _two_clusters(on)
    if cl is None:
        return {"ok": False, "why": "too few flashes"}
    dot, dash, cut = cl
    ratio = dash / dot if dot > 0 else np.inf
    if not (2.0 <= ratio <= 4.5):
        # all flashes the same length -> only dots or only dashes; unit from shortest cluster
        dot, cut, ratio = min(on), max(on) * 1.01, float("nan")
    unit = dot
    text, sym, word = "", "", ""
    errors = 0
    for s, _, d in inner:
        if s:
            sym += "-" if d > cut else "."
        else:
            u = d / unit
            if u >= 5.0:          # word gap (7 units)
                ch = MORSE.get(sym, "?") if sym else ""
                errors += ch == "?"
                text += ch + " "
                sym = ""
            elif u >= 2.0:        # letter gap (3 units)
                ch = MORSE.get(sym, "?") if sym else ""
                errors += ch == "?"
                text += ch
                sym = ""
    if sym:
        ch = MORSE.get(sym, "?")
        errors += ch == "?"
        text += ch
    n_chars = max(1, len(text.replace(" ", "")))
    # timing fit: how well OFF gaps sit on 1/3/7 unit multiples
    offs_u = np.array(off) / unit if off else np.array([])
    gap_fit = float(np.mean(np.min(np.abs(offs_u[:, None] - np.array([1, 3, 7])[None]), axis=1))) if len(offs_u) else np.nan
    return {"ok": True, "text": text.strip(), "unit_s": round(unit, 3), "dash_dot_ratio": round(float(ratio), 2) if ratio == ratio else None,
            "unknown_symbols": errors, "gap_fit_units": round(gap_fit, 2) if gap_fit == gap_fit else None,
            "plausible": bool(errors / n_chars < 0.25 and (gap_fit != gap_fit or gap_fit < 0.6) and n_chars >= 2)}


def blink_groups(runs, pause_factor=3.0):
    """Counts of flashes per group separated by pauses much longer than the normal gap."""
    inner = runs[1:-1] if len(runs) > 2 else runs
    off = [d for s, _, d in inner if not s]
    if len(off) < 2:
        return {"ok": False}
    base = np.median(off)
    groups, n = [], 0
    for s, _, d in inner:
        if s:
            n += 1
        elif d > pause_factor * base and n:
            groups.append(n)
            n = 0
    if n:
        groups.append(n)
    return {"ok": len(groups) >= 2, "groups": groups, "as_digits": "".join(str(g % 10) for g in groups),
            "gap_s": round(float(base), 3)}


def periodicity(runs):
    inner = runs[1:-1] if len(runs) > 2 else runs
    on = [d for s, _, d in inner if s]
    off = [d for s, _, d in inner if not s]
    if len(on) < 3 or len(off) < 3:
        return {"ok": False}
    period = float(np.mean(on) + np.mean(off))
    return {"ok": True, "period_s": round(period, 3), "duty": round(float(np.mean(on) / period), 3),
            "cv_on": round(_cv(on), 3), "cv_off": round(_cv(off), 3),
            "regular": bool(_cv(on) < 0.15 and _cv(off) < 0.15)}


def classify(runs, contrast):
    per = periodicity(runs)
    morse = decode_morse(runs)
    groups = blink_groups(runs)
    n_on = sum(1 for s, _, _ in runs if s)
    if contrast < 4 or n_on < 3:
        verdict = "no clear blinking (contrast or flash count too low)"
    elif per.get("regular"):
        verdict = f"regular blink: period {per['period_s']} s, duty {per['duty']} -> most likely an equipment status LED"
    elif morse.get("plausible"):
        verdict = f"Morse-like timing -> decoded «{morse['text']}» (unit {morse['unit_s']} s)"
    elif groups.get("ok") and len(set(groups["groups"])) > 1:
        verdict = f"grouped flashes {groups['groups']} -> possible digit code {groups['as_digits']}"
    else:
        verdict = "irregular flicker -> most likely a reflection twinkling as vegetation/insects move (or a noisy LED)"
    return {"verdict": verdict, "periodicity": per, "morse": morse, "groups": groups,
            "n_flashes": n_on, "contrast_snr": round(contrast, 1)}


# ----------------------------------------------------------------------------- CLI
def analyze(path, point=None, radius=5, auto=False, top=6, max_seconds=None, plot=True):
    frames, times, fps = read_video_gray(path, max_seconds=max_seconds)
    targets = []
    if point:
        targets.append((point[0], point[1], None))
    if auto or not point:
        targets += find_blinkers(frames, top=top)
    results = []
    for x, y, score in targets:
        sig = point_signal(frames, x, y, radius=radius)
        states, runs, contrast = binarize(sig, times)
        res = {"x": int(x), "y": int(y), "auto_score": score, **classify(runs, contrast),
               "runs": [(int(s), round(t0, 3), round(d, 3)) for s, t0, d in runs]}
        res["_sig"] = sig
        res["_states"] = states
        results.append(res)
    out = {"file": str(path), "fps": fps, "frames": int(len(times)), "duration_s": round(float(times[-1] - times[0]), 2),
           "frame_size": [int(frames.shape[2]), int(frames.shape[1])],
           "targets": [{k: v for k, v in r.items() if not k.startswith("_")} for r in results]}
    p = Path(path)
    Path(str(p.with_suffix("")) + "_blink.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    if plot and results:
        _plot(p, frames, times, results)
    return out


def _plot(p, frames, times, results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(results)
    fig, axes = plt.subplots(n + 1, 1, figsize=(12, 2.2 * (n + 1)))
    axes = np.atleast_1d(axes)
    axes[0].imshow(frames[len(frames) // 2], cmap="gray")
    for k, r in enumerate(results):
        axes[0].scatter([r["x"]], [r["y"]], s=80, facecolors="none", edgecolors="r")
        axes[0].text(r["x"] + 8, r["y"], str(k + 1), color="r")
        ax = axes[k + 1]
        ax.plot(times, r["_sig"], lw=0.7)
        ax.fill_between(times, r["_sig"].min(), r["_sig"].max(), where=r["_states"], alpha=0.2, color="orange")
        ax.set_title(f"#{k + 1} ({r['x']},{r['y']}): {r['verdict']}", fontsize=8)
    axes[0].set_axis_off()
    fig.tight_layout()
    fig.savefig(str(p.with_suffix("")) + "_blink.png", dpi=110)
    plt.close(fig)


def record(url, seconds, out):
    """Record `seconds` of the live stream at full frame rate (needs yt-dlp + network)."""
    import yt_dlp
    with yt_dlp.YoutubeDL({"quiet": True, "format": "best[height<=1080]/best"}) as ydl:
        info = ydl.extract_info(url, download=False)
    src = info.get("url") or info["formats"][-1]["url"]
    cmd = [_ffmpeg(), "-y", "-loglevel", "error", "-i", src, "-t", str(seconds), "-an", "-c:v", "libx264",
           "-preset", "veryfast", "-crf", "18", str(out)]
    subprocess.run(cmd, check=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--url", default="https://www.youtube.com/watch?v=EQHgfmZicc8")
    r.add_argument("--seconds", type=int, default=180)
    r.add_argument("--out", default="clip.mp4")
    a = sub.add_parser("analyze")
    a.add_argument("clip")
    a.add_argument("--point", help="x,y pixel in the clip")
    a.add_argument("--radius", type=int, default=5)
    a.add_argument("--auto", action="store_true")
    a.add_argument("--top", type=int, default=6)
    a.add_argument("--max-seconds", type=float)
    pv = sub.add_parser("preview", help="save a middle frame with a pixel grid to pick --point")
    pv.add_argument("clip")
    args = ap.parse_args()
    if args.cmd == "record":
        print(record(args.url, args.seconds, args.out))
    elif args.cmd == "preview":
        import cv2
        frames, _, _ = read_video_gray(args.clip, max_seconds=5)
        img = cv2.cvtColor(frames[len(frames) // 2], cv2.COLOR_GRAY2BGR)
        for x in range(0, img.shape[1], 50):
            cv2.line(img, (x, 0), (x, img.shape[0]), (0, 0, 255) if x % 250 == 0 else (0, 80, 0), 1)
            if x % 100 == 0:
                cv2.putText(img, str(x), (x + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
        for y in range(0, img.shape[0], 50):
            cv2.line(img, (0, y), (img.shape[1], y), (0, 0, 255) if y % 250 == 0 else (0, 80, 0), 1)
            if y % 100 == 0:
                cv2.putText(img, str(y), (2, y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
        out = str(Path(args.clip).with_suffix("")) + "_grid.png"
        cv2.imwrite(out, img)
        print(out)
    else:
        pt = tuple(int(v) for v in args.point.split(",")) if args.point else None
        out = analyze(args.clip, point=pt, radius=args.radius, auto=args.auto, top=args.top, max_seconds=args.max_seconds)
        for k, t in enumerate(out["targets"], 1):
            print(f"#{k} ({t['x']},{t['y']}) flashes={t['n_flashes']} snr={t['contrast_snr']}: {t['verdict']}")
            if t["morse"].get("ok"):
                print(f"    morse: «{t['morse']['text']}» unit={t['morse']['unit_s']}s ratio={t['morse']['dash_dot_ratio']} "
                      f"unknown={t['morse']['unknown_symbols']} gapfit={t['morse']['gap_fit_units']}")
            if t["groups"].get("ok"):
                print(f"    groups: {t['groups']['groups']} -> {t['groups']['as_digits']}")
            if t["periodicity"].get("ok"):
                print(f"    period={t['periodicity']['period_s']}s duty={t['periodicity']['duty']} "
                      f"cv_on={t['periodicity']['cv_on']} cv_off={t['periodicity']['cv_off']}")


if __name__ == "__main__":
    main()
