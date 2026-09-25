"""Replayed-audio (loop) detector and audio/video offset estimator (analyzer name: ``audio_loop``).

default.no found stretches of the stream's audio that repeat 22-48 h apart: the "live" audio is at
times a replay. When that happens, every audio-derived time (aircraft peaks, rain, voices) is
unrelated to the picture and to the real time on site. This analyzer finds such repeats against
*all* retained history and tags them, so the bridges can drop audio evidence near an ``audio_loop``
observation (bridges/adsb.py: +-30 s, bridges/met.py: +-60 s).

Landmark fingerprint (Wang 2003, "Shazam")
------------------------------------------
* Audio is resampled to 8 kHz. Log power spectrogram: 512-point Hann window, hop 128 (16 ms
  frames, 15.6 Hz bins, bins 1-255 = 16 Hz-4 kHz). Each frequency row is whitened by its median
  over the buffer, so stationary hum and noise colour do not create peaks.
* Peaks are local maxima in a 7 x 9 (112 ms x 140 Hz) neighbourhood that are >= ``peak_min_db``
  above the row median. Only the ``peaks_per_s`` strongest within +-0.5 s are kept. This
  selection is shift-invariant: it does not depend on where the chunk boundaries fall, so
  a replay with a different chunk alignment yields the same landmarks.
* Each anchor peak is paired with the ``fanout`` nearest peaks in its target zone
  (2-48 frames = 32-770 ms later, within +-40 bins). A pair gives the 22-bit hash
  (f1 << 14 | f2 << 6 | dt), stored with the anchor's *absolute* frame index round(t / 16 ms).
  t is the chunk's *capture* time, the stable local reception clock. Real time moves whenever
  the latency calibration is updated, and would leak into the measured lag. Outputs are
  converted back to real time with the current capture-real offset.
  Level and gain changes, AAC re-encoding and moderate added noise leave most hashes intact.
* Chunk edges: a 2 s tail of the previous chunk is prepended. Anchors are taken only from
  [end of the last processed region, buffer end - 0.9 s], so every anchor is hashed exactly
  once, with its complete target zone.

Index: one SQLite table per UTC day (``fp_YYYYMMDD(h, t) PRIMARY KEY (h, t) WITHOUT ROWID``),
clustered by hash, in ``<db dir>/fp/audio_fp.sqlite`` (config ``fp_path``). A separate file keeps
the main DB small and free of lock contention with the dashboard. Pruning after ``retention_h``
(168 h, covering the 22-48 h repeats with margin) is a DROP TABLE. At ~40 hashes/s that is
~3.5 M rows (~60 MB) per day. A query is ~500 B-tree seeks, ~5 ms per chunk.

Matching: for every new chunk, all hashes are looked up in all retained days with lag >=
``min_lag_s`` (600 s; repetitive nature sounds and quasi-stationary noise at short lags are
excluded). Hashes seen more than ``max_hash_hits`` times (e.g. hum/tones) are ignored. The time
offsets (t_query - t_ref) are histogrammed with +-1 frame merging. A loop is declared when the
best offset has
  * >= ``min_matches`` (12) distinct matching query hashes, >= ``min_frac`` (2 %) of the
    chunk's hashes, spread over >= ``min_span_s`` (2 s) of the chunk;
  * >= ``noise_ratio`` (3x) the count of any unrelated offset, and at most ``max_multi`` (3)
    strong offsets (>= 50 % of the best), at least 10 min apart. A segment replayed twice is
    allowed; a periodic sound (a comb of many offsets) is not.
Random coincidences are Poisson with a mean of ~1e-3 per offset bin, so 12 aligned hashes
cannot happen by chance. Consecutive hits at the same lag (+-0.2 s) form a *run*. Confidence
rises with the number of matches and the run length. A new run also creates a human-facing
row in ``events``.

``audio_loop`` value: ref_ts (start of the matched stretch at the earlier time), lag_s, lag_h,
corr (fraction of this chunk's landmark hashes that recur at this lag, 0-1), n_matched,
n_hashes, span_s, seg_start/seg_end (matched stretch now), run_chunks, run_start, other_lags_s.
``ts`` is the middle of the matched stretch. ``ctx.state['audio_loop_active']`` =
{'since', 'until', 'lag_s'} (real unix times of the current run) lets audio_events and birds
flag their observations ``loop_suspect`` (confidence capped at 0.3).

A/V offset (``av_offset``, on_tick every ``tick_interval_s``)
------------------------------------------------------------
Visual events with an onset window come from the DB: ``whiteboard_visible``
([first_seen_ts - frame_interval, first_seen_ts]) and ``gesture_point_up`` onsets
(value.onset_window). Audio events are strong broadband onsets from the fingerprint
spectrogram (spectral-flux z >= 8, with a >= 6 dB level jump: a clap, a tap on the board, the
box door) and speech onsets (``audio_voice.value.onsets_ts``). Audio inside looped stretches is
excluded. For each candidate lag tau (+-20 s, 0.1 s steps), count the visual windows
[a - tol, b + tol] that contain an audio event at t - tau. Significance: the same statistic
for 200 circular shifts of the audio train within the observed span (the null keeps the audio
event rate and clustering). It is emitted only if >= 4 visual events, >= 4 matched, >= 50 % matched, and
permutation p <= 0.01. The estimate is the centre of the tau interval that reaches the maximum.
Its sigma is that interval's half-width / sqrt(3), plus 0.25 s.
Convention (as in ingest.pipeline / StreamClock.audio_offset_s, which is *added* to the audio
real time): ``residual_s`` = audio time - video time as currently stamped; ``offset_s`` =
current audio_offset_s - residual_s, the value that would align them; ``audio_lag_s`` =
-offset_s, the physical audio delay behind the picture. Nothing is written to calibration.
Frames are sampled every 5 s, so one event constrains the offset only to ~5 s, and the
intersection over many events narrows it. Confidence <= 0.5.

Failure modes: heavily re-mixed replays (music added) lower the match fraction. Very quiet
audio (digital silence) has no landmarks. Two chunks that both contain the same broadcast
jingle would match, but the 10-minute minimum lag and the multi-offset guard limit that. A/V:
her speech need not coincide with the board appearing, so this is a weak, statistical estimate.
"""
from __future__ import annotations

import logging
import math
import sqlite3
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.ndimage import maximum_filter

from ..types import Observation, iso, parse_iso
from .audio_events import dbfs, from_unix, prepare_samples, resample, stft_power, to_unix
from .base import Analyzer, Context

log = logging.getLogger("hordewatch.audio_loop")

UTC = timezone.utc
FP_SR = 8000
FP_NFFT = 512
FP_HOP = 128
HOP_S = FP_HOP / FP_SR          # 16 ms
F_LO, F_HI = 1, 256             # bins used (1..255)
PEAK_T, PEAK_F = 7, 9           # neighbourhood (frames, bins)
DT_MIN, DT_MAX = 2, 48          # target zone (frames)
DF_MAX = 40                     # target zone (bins)
TAIL_S = 2.0
FP_VERSION = "lm1-8k-512-128-7x9-2..48-40"

DEFAULTS = {
    "fp_path": None,
    "retention_h": 168.0,
    "min_lag_s": 600.0,
    "max_lag_s": None,
    "peaks_per_s": 15,
    "fanout": 5,
    "peak_min_db": 6.0,
    "min_matches": 12,
    "min_frac": 0.02,
    "min_span_s": 2.0,
    "max_hash_hits": 200,
    "noise_ratio": 3.0,
    "max_multi": 3,
    "multi_min_sep_s": 600.0,
    "run_tol_s": 0.2,
    "prune_every_s": 3600.0,
    # A/V offset
    "av_lookback_h": 6.0,
    "av_max_offset_s": 20.0,
    "av_step_s": 0.1,
    "av_tol_s": 0.5,
    "av_min_visual": 4,
    "av_min_matches": 4,
    "av_min_match_frac": 0.5,
    "av_p_max": 0.01,
    "av_n_null": 200,
    "av_onset_z": 8.0,
    "av_emit_every_s": 3600.0,
    "av_frame_interval_s": None,     # default: _global.source.frame_interval_s or 5 s
}


def _day_of_frame(t_frame: int) -> str:
    return datetime.fromtimestamp(float(t_frame) * HOP_S, UTC).strftime("%Y%m%d")


# ============================================================================ fingerprinting
class Fingerprinter:
    """Streaming landmark hasher. process() returns (hashes, abs_frames, onsets[(t, z)])."""

    def __init__(self, peaks_per_s=15, fanout=5, peak_min_db=6.0):
        self.K = int(peaks_per_s)
        self.fanout = int(fanout)
        self.peak_min_db = float(peak_min_db)
        self.tail: Optional[np.ndarray] = None
        self.tail_t0: Optional[float] = None
        self.next_t: Optional[float] = None

    def reset(self):
        self.tail = self.tail_t0 = self.next_t = None

    def process(self, x16: np.ndarray, t0: float):
        x8 = resample(x16, 16000, FP_SR)
        if self.tail is not None and abs(t0 - (self.tail_t0 + len(self.tail) / FP_SR)) <= 0.25:
            buf = np.concatenate([self.tail, x8])
            tb = self.tail_t0
        else:
            buf, tb = x8, t0
            self.next_t = t0
        t_end = tb + len(buf) / FP_SR
        keep = int(TAIL_S * FP_SR)
        self.tail = buf[-keep:].copy()
        self.tail_t0 = t_end - len(self.tail) / FP_SR
        if len(buf) < FP_NFFT * 4:
            return np.zeros(0, np.int64), np.zeros(0, np.int64), []
        P, _, _ = stft_power(buf, FP_SR, FP_NFFT, FP_HOP, center=False)
        L = 10.0 * np.log10(P[:, F_LO:F_HI] + 1e-13)
        ft = tb + np.arange(P.shape[0]) * HOP_S          # frame start times
        t_lo = self.next_t if self.next_t is not None else tb
        t_hi = t_end - (DT_MAX + PEAK_T // 2 + 1) * HOP_S - FP_NFFT / FP_SR
        if t_hi <= t_lo:
            return np.zeros(0, np.int64), np.zeros(0, np.int64), []
        self.next_t = t_hi
        # ---- peaks
        W = L - np.median(L, axis=0, keepdims=True)
        mx = maximum_filter(W, size=(PEAK_T, PEAK_F), mode="constant", cval=-np.inf)
        alive = L > -125.0
        ti, fi = np.nonzero((W >= mx) & (W >= self.peak_min_db) & alive)
        if len(ti):
            val = W[ti, fi]
            o = np.argsort(ti, kind="stable")
            ti, fi, val = ti[o], fi[o], val[o]
            half = int(round(0.5 / HOP_S))
            lo = np.searchsorted(ti, ti - half, "left")
            hi = np.searchsorted(ti, ti + half, "right")
            keepm = np.zeros(len(ti), bool)
            for i in range(len(ti)):
                keepm[i] = int(np.sum(val[lo[i]:hi[i]] > val[i])) < self.K
            ti, fi = ti[keepm], fi[keepm]
        hashes, times = self._pairs(ti, fi, ft, t_lo, t_hi)
        onsets = self._onsets(L, ft, t_lo, t_hi)
        return hashes, times, onsets

    def _pairs(self, ti, fi, ft, t_lo, t_hi):
        if len(ti) < 2:
            return np.zeros(0, np.int64), np.zeros(0, np.int64)
        hs, ts = [], []
        tf = ft[ti]
        anchors = np.nonzero((tf >= t_lo) & (tf < t_hi))[0]
        for a in anchors:
            j0 = np.searchsorted(ti, ti[a] + DT_MIN, "left")
            j1 = np.searchsorted(ti, ti[a] + DT_MAX, "right")
            if j1 <= j0:
                continue
            cand = np.arange(j0, j1)
            cand = cand[np.abs(fi[cand] - fi[a]) <= DF_MAX][: self.fanout]
            if not len(cand):
                continue
            f1 = int(fi[a]) + F_LO
            f2 = fi[cand].astype(np.int64) + F_LO
            dt = (ti[cand] - ti[a]).astype(np.int64)
            hs.append((f1 << 14) | (f2 << 6) | dt)
            ts.append(np.full(len(cand), int(round(tf[a] / HOP_S)), np.int64))
        if not hs:
            return np.zeros(0, np.int64), np.zeros(0, np.int64)
        return np.concatenate(hs), np.concatenate(ts)

    @staticmethod
    def _onsets(L, ft, t_lo, t_hi, z_min=6.0):
        """Strong broadband onsets (spectral flux z-score, with a level jump) in [t_lo, t_hi)."""
        if L.shape[0] < 20:
            return []
        d = np.maximum(L[2:, 3:] - L[:-2, 3:], 0.0).mean(1)
        flux = np.concatenate([[0.0, 0.0], d])
        med = float(np.median(flux))
        mad = 1.4826 * float(np.median(np.abs(flux - med))) + 1e-6
        z = (flux - med) / mad
        lvl = dbfs((10 ** (L / 10)).sum(1))
        out = []
        win = 15
        for i in np.nonzero(z >= z_min)[0]:
            if i < 8 or i > len(z) - 5:
                continue
            if z[i] < np.max(z[max(i - win, 0):i + win + 1]):
                continue
            jump = float(np.mean(lvl[i + 1:i + 4]) - np.mean(lvl[i - 7:i - 3]))
            if jump < 6.0:
                continue
            t = float(ft[i]) + FP_NFFT / (2.0 * FP_SR) - HOP_S
            if t_lo <= t < t_hi:
                out.append((t, float(z[i])))
        return out


# ============================================================================ storage
class FingerprintStore:
    """Hash index in SQLite, one WITHOUT ROWID table per UTC day (pruning = DROP TABLE)."""

    def __init__(self, path: str):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.con = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
        if self.path != ":memory:":
            self.con.execute("PRAGMA journal_mode=WAL")
        self.con.execute("PRAGMA synchronous=NORMAL")
        self.con.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT)")
        r = self.con.execute("SELECT value FROM meta WHERE key='version'").fetchone()
        if r is None or r[0] != FP_VERSION:
            if r is not None:
                log.warning("fingerprint parameters changed (%s -> %s): dropping old index", r[0], FP_VERSION)
            for t in self.tables():
                self.con.execute(f"DROP TABLE {t}")
            self.con.execute("INSERT OR REPLACE INTO meta(key, value) VALUES ('version', ?)", (FP_VERSION,))
        self.con.commit()
        self._known = set(self.tables())

    def tables(self):
        return sorted(r[0] for r in self.con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'fp\\_%' ESCAPE '\\'"))

    def _table(self, day: str) -> str:
        name = f"fp_{day}"
        if name not in self._known:
            self.con.execute(f"CREATE TABLE IF NOT EXISTS {name}(h INTEGER NOT NULL, t INTEGER NOT NULL, "
                             "PRIMARY KEY(h, t)) WITHOUT ROWID")
            self._known.add(name)
        return name

    def add(self, hashes: np.ndarray, times: np.ndarray):
        if not len(hashes):
            return
        with self._lock:
            days = {}
            for h, t in zip(hashes.tolist(), times.tolist()):
                days.setdefault(_day_of_frame(t), []).append((h, t))
            for day, rows in days.items():
                self.con.executemany(f"INSERT OR IGNORE INTO {self._table(day)}(h, t) VALUES (?, ?)", rows)
            self.con.commit()

    def query(self, hashes: np.ndarray, t_max: int, t_min: Optional[int] = None):
        """All stored (h, t) with h in hashes and t_min <= t <= t_max."""
        uh = np.unique(hashes).tolist()
        if not uh:
            return np.zeros(0, np.int64), np.zeros(0, np.int64)
        day_max = _day_of_frame(t_max)
        day_min = _day_of_frame(t_min) if t_min is not None else "00000000"
        hs, ts = [], []
        with self._lock:
            for tbl in self.tables():
                day = tbl[3:]
                if day > day_max or day < day_min:
                    continue
                for i in range(0, len(uh), 900):
                    part = uh[i:i + 900]
                    q = (f"SELECT h, t FROM {tbl} WHERE h IN ({','.join('?' * len(part))}) AND t <= ?"
                         + (" AND t >= ?" if t_min is not None else ""))
                    args = part + [int(t_max)] + ([int(t_min)] if t_min is not None else [])
                    rows = self.con.execute(q, args).fetchall()
                    if rows:
                        a = np.asarray(rows, dtype=np.int64)
                        hs.append(a[:, 0])
                        ts.append(a[:, 1])
        if not hs:
            return np.zeros(0, np.int64), np.zeros(0, np.int64)
        return np.concatenate(hs), np.concatenate(ts)

    def prune(self, t_now_frame: int, retention_s: float):
        cutoff = _day_of_frame(int(t_now_frame - retention_s / HOP_S))
        with self._lock:
            for tbl in self.tables():
                if tbl[3:] < cutoff:
                    self.con.execute(f"DROP TABLE {tbl}")
                    self._known.discard(tbl)
                    log.info("audio fingerprint index: dropped %s (older than retention)", tbl)
            self.con.commit()

    def count(self) -> int:
        return sum(self.con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in self.tables())

    def close(self):
        try:
            self.con.close()
        except Exception:  # pragma: no cover
            pass


def match_offsets(q_h, q_t, r_h, r_t, min_lag, max_lag, max_hits):
    """Offset histogram of query hashes vs stored ones. Returns dict or None."""
    if not len(q_h) or not len(r_h):
        return None
    uh, cnt = np.unique(r_h, return_counts=True)
    popular = uh[cnt > max_hits]
    if len(popular):
        m = ~np.isin(r_h, popular)
        r_h, r_t = r_h[m], r_t[m]
        if not len(r_h):
            return None
    o = np.argsort(r_h, kind="stable")
    rh, rt = r_h[o], r_t[o]
    lo = np.searchsorted(rh, q_h, "left")
    hi = np.searchsorted(rh, q_h, "right")
    counts = hi - lo
    tot = int(counts.sum())
    if tot == 0:
        return None
    qi = np.repeat(np.arange(len(q_h)), counts)
    starts = np.repeat(lo, counts)
    within = np.arange(tot) - np.repeat(np.cumsum(counts) - counts, counts)
    off = q_t[qi] - rt[starts + within]
    ok = (off >= min_lag) & (off <= max_lag)
    off, qi = off[ok], qi[ok]
    if not len(off):
        return None
    u, c = np.unique(off, return_counts=True)
    cm = c.copy()
    for d in (-1, 1):
        pos = np.searchsorted(u, u + d)
        pc = np.minimum(pos, len(u) - 1)
        hit = (pos < len(u)) & (u[pc] == u + d)
        cm[hit] += c[pc[hit]]
    j = int(np.argmax(cm))
    best = int(u[j])
    sel = np.abs(off - best) <= 1
    matched = np.unique(qi[sel])
    n_matched = len(matched)
    # strong offsets (>= 50 % of best) clustered within 3 frames
    strong = u[cm >= 0.5 * cm[j]]
    clusters = []
    for s in np.sort(strong):
        if clusters and s - clusters[-1][-1] <= 3:
            clusters[-1].append(int(s))
        else:
            clusters.append([int(s)])
    in_strong = np.zeros(len(u), bool)
    for cl in clusters:
        in_strong |= (u >= cl[0] - 3) & (u <= cl[-1] + 3)
    noise = int(cm[~in_strong].max()) if np.any(~in_strong) else 0
    others = [int(round(np.mean(cl))) for cl in clusters if not (cl[0] - 3 <= best <= cl[-1] + 3)]
    return {"best": best, "lag_frames": float(np.mean(off[sel])), "n_matched": int(n_matched),
            "n_hits": int(cm[j]), "noise": noise, "n_strong": len(clusters), "other_offsets": others,
            "t_first": int(q_t[matched].min()), "t_last": int(q_t[matched].max())}


# ============================================================================ analyzer
class AudioLoopAnalyzer(Analyzer):
    name = "audio_loop"
    wants_audio = True
    min_interval_s = 0.0      # every chunk must be indexed
    tick_interval_s = 300.0

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.p = dict(DEFAULTS)
        self.p.update({k: v for k, v in (config or {}).items() if k != "_global"})
        self.fp = Fingerprinter(self.p["peaks_per_s"], self.p["fanout"], self.p["peak_min_db"])
        self.store: Optional[FingerprintStore] = None
        self._run: Optional[dict] = None
        self._onsets: deque = deque()
        self._loops: deque = deque()            # (t_start, t_end) looped stretches (real time)
        self._last_t: Optional[float] = None
        self._last_prune = -1e18
        self._last_av: Optional[dict] = None
        self._cap_off = 0.0

    # ---------------------------------------------------------------- store
    def _store(self, ctx):
        if self.store is not None:
            return self.store
        path = self.p.get("fp_path")
        if not path:
            dbp = getattr(getattr(ctx, "db", None), "path", None)
            if dbp and dbp != ":memory:":
                path = str(Path(dbp).parent / "fp" / "audio_fp.sqlite")
            else:
                g = (self.config.get("_global") or {}).get("db")
                path = str(Path(g).parent / "fp" / "audio_fp.sqlite") if g else ":memory:"
        self.store = FingerprintStore(path)
        log.info("audio fingerprint index: %s", path)
        return self.store

    # ---------------------------------------------------------------- per chunk
    def on_audio(self, chunk, ctx: Context):
        x = prepare_samples(chunk.samples, chunk.sr)
        if x is None or len(x) < 8000:
            return []
        t0r = to_unix(chunk.real_ts)
        self._cap_off = (chunk.capture_ts - chunk.real_ts).total_seconds() if chunk.capture_ts else 0.0
        # fingerprint timeline = capture time (independent of later latency re-calibration)
        hashes, times, onsets = self.fp.process(x, t0r + self._cap_off)
        self._last_t = t0r + len(x) / 16000.0
        for t, z in onsets:
            if z >= float(self.p["av_onset_z"]):
                self._onsets.append((t - self._cap_off, z))       # audio real time
        horizon = self._last_t - float(self.p["av_lookback_h"]) * 3600 - 3600
        while self._onsets and self._onsets[0][0] < horizon:
            self._onsets.popleft()
        while self._loops and self._loops[0][1] < horizon:
            self._loops.popleft()
        if not len(hashes):
            return []
        store = self._store(ctx)
        out = []
        try:
            out = self._match(hashes, times, chunk, ctx, store)
        except Exception as e:  # never lose the indexing because matching failed
            log.exception("audio_loop matching failed: %s", e)
        store.add(hashes, times)
        now_f = int(times.max())
        if now_f * HOP_S - self._last_prune >= float(self.p["prune_every_s"]):
            store.prune(now_f, float(self.p["retention_h"]) * 3600.0)
            self._last_prune = now_f * HOP_S
        return out

    def _match(self, hashes, times, chunk, ctx, store):
        p = self.p
        min_lag = int(float(p["min_lag_s"]) / HOP_S)
        max_lag_s = p.get("max_lag_s") or float(p["retention_h"]) * 3600.0
        max_lag = int(float(max_lag_s) / HOP_S)
        t_max = int(times.max()) - min_lag
        t_min = int(times.min()) - max_lag
        r_h, r_t = store.query(hashes, t_max, t_min)
        m = match_offsets(hashes, times, r_h, r_t, min_lag, max_lag, int(p["max_hash_hits"]))
        if m is None:
            return []
        n_q = len(np.unique(np.stack([hashes, times], 1), axis=0))
        frac = m["n_matched"] / max(n_q, 1)
        span = (m["t_last"] - m["t_first"]) * HOP_S
        multi_ok = m["n_strong"] <= int(p["max_multi"]) and all(
            abs(o - m["best"]) * HOP_S >= float(p["multi_min_sep_s"]) for o in m["other_offsets"])
        ok = (m["n_matched"] >= int(p["min_matches"]) and frac >= float(p["min_frac"])
              and span >= float(p["min_span_s"]) and m["n_hits"] >= float(p["noise_ratio"]) * max(m["noise"], 1)
              and multi_ok)
        if not ok:
            if m["n_matched"] >= int(p["min_matches"]) // 2:
                log.debug("audio_loop near-miss: n=%d frac=%.3f span=%.1f noise=%d strong=%d",
                          m["n_matched"], frac, span, m["noise"], m["n_strong"])
            return []
        lag = m["lag_frames"] * HOP_S
        # matched stretch in real time (fingerprint frames are capture time)
        seg0 = m["t_first"] * HOP_S - self._cap_off
        seg1 = m["t_last"] * HOP_S + DT_MAX * HOP_S - self._cap_off
        run = self._run
        if run and abs(run["lag_s"] - lag) <= float(p["run_tol_s"]) and seg0 - run["last_t"] <= 30.0:
            run["n"] += 1
            run["last_t"] = seg1
        else:
            run = self._run = {"lag_s": lag, "n": 1, "start_t": seg0, "last_t": seg1}
            summary = (f"Replayed audio: stream audio at {iso(from_unix(seg0))} repeats audio from "
                       f"{iso(from_unix(seg0 - lag))} (lag {lag / 3600:.2f} h)")
            log.warning(summary)
            db = getattr(ctx, "db", None)
            if db is not None and hasattr(db, "add_event"):
                try:
                    db.add_event(from_unix(seg0), "audio_loop", summary, {"lag_s": round(lag, 3)})
                except Exception as e:  # pragma: no cover
                    log.debug("add_event failed: %s", e)
        self._loops.append((seg0, seg1))
        ctx.state["audio_loop_active"] = {"until": seg1, "lag_s": lag, "since": run["start_t"]}
        conf = 0.45 + 0.1 * math.log2(max(m["n_matched"] / float(p["min_matches"]), 1.0)) \
            + (0.15 if run["n"] >= 2 else 0.0) + (0.1 if frac >= 0.1 else 0.0)
        tmid = 0.5 * (seg0 + seg1)
        v = {"ref_ts": iso(from_unix(seg0 - lag)), "lag_s": round(lag, 3), "lag_h": round(lag / 3600.0, 4),
             "corr": round(frac, 4), "n_matched": m["n_matched"], "n_hashes": int(n_q), "span_s": round(span, 2),
             "seg_start": iso(from_unix(seg0)), "seg_end": iso(from_unix(seg1)),
             "ref_end": iso(from_unix(seg1 - lag)), "noise_hits": m["noise"], "run_chunks": run["n"],
             "run_start": iso(from_unix(run["start_t"])),
             "other_lags_s": [round(o * HOP_S, 2) for o in m["other_offsets"]], "method": "landmark_fp"}
        return [Observation(kind="audio_loop", ts=from_unix(tmid), value=v, analyzer=self.name,
                            confidence=round(float(np.clip(conf, 0.3, 0.95)), 3), audio_id=getattr(chunk, "id", None),
                            ts_capture=from_unix(tmid + self._cap_off))]

    # ---------------------------------------------------------------- A/V offset
    def _frame_interval(self):
        v = self.p.get("av_frame_interval_s")
        if v:
            return float(v)
        g = (self.config.get("_global") or {}).get("source") or {}
        return float(g.get("frame_interval_s") or 5.0)

    def visual_events(self, db, t0, t1):
        """[(a, b, kind)] onset windows (unix real time) of visual events in [t0, t1]."""
        fi = self._frame_interval()
        out = []
        try:
            rows = db.observations(kind=["whiteboard_visible", "gesture_point_up"], since=from_unix(t0),
                                   until=from_unix(t1))
        except Exception as e:
            log.debug("visual event query failed: %s", e)
            return out
        for r in rows:
            v = r.get("value") or {}
            try:
                if r["kind"] == "whiteboard_visible":
                    b = to_unix(parse_iso(v["first_seen_ts"])) if v.get("first_seen_ts") else to_unix(r["ts"])
                    out.append((b - fi, b, "whiteboard_visible"))
                elif v.get("phase", "onset") == "onset":
                    w = v.get("onset_window")
                    if w and len(w) == 2 and w[0]:
                        a, b = to_unix(parse_iso(w[0])), to_unix(parse_iso(w[1]))
                    else:
                        b = to_unix(r["ts"])
                        a = b - fi
                    out.append((min(a, b), max(a, b), "gesture_point_up"))
            except Exception:
                continue
        return out

    def audio_events(self, db, t0, t1):
        ev = [t for t, _ in self._onsets if t0 <= t <= t1]
        src = {"onset": len(ev), "voice": 0}
        if db is not None:
            try:
                for r in db.observations(kind="audio_voice", since=from_unix(t0 - 20), until=from_unix(t1)):
                    for s in (r.get("value") or {}).get("onsets_ts") or []:
                        t = to_unix(parse_iso(s))
                        if t0 <= t <= t1:
                            ev.append(t)
                            src["voice"] += 1
            except Exception as e:
                log.debug("audio_voice query failed: %s", e)
        loops = list(self._loops)
        ev = sorted(t for t in ev if not any(a - 5 <= t <= b + 5 for a, b in loops))
        return np.asarray(ev, dtype=np.float64), src

    def on_tick(self, ctx: Context):
        if self._last_t is None or getattr(ctx, "db", None) is None:
            return []
        p = self.p
        t1 = self._last_t
        t0 = t1 - float(p["av_lookback_h"]) * 3600.0
        vis = self.visual_events(ctx.db, t0, t1)
        if len(vis) < int(p["av_min_visual"]):
            return []
        aud, src = self.audio_events(ctx.db, t0 - float(p["av_max_offset_s"]), t1 + float(p["av_max_offset_s"]))
        res = estimate_av_offset(vis, aud, max_offset=float(p["av_max_offset_s"]), step=float(p["av_step_s"]),
                                 tol=float(p["av_tol_s"]), n_null=int(p["av_n_null"]))
        if res is None:
            return []
        ok = (res["n_matched"] >= int(p["av_min_matches"]) and res["match_frac"] >= float(p["av_min_match_frac"])
              and res["p_value"] <= float(p["av_p_max"]) and res["n_max_regions"] == 1)
        if not ok:
            log.debug("av_offset not significant: %s", res)
            return []
        last = self._last_av
        if last and abs(last["residual_s"] - res["residual_s"]) <= max(last["sigma_s"], 0.5) \
                and t1 - last["t"] < float(p["av_emit_every_s"]):
            return []
        cur = float(getattr(ctx.clock, "audio_offset_s", 0.0) or 0.0) if ctx.clock is not None else 0.0
        v = {"offset_s": round(cur - res["residual_s"], 2), "residual_s": round(res["residual_s"], 2),
             "audio_lag_s": round(res["residual_s"] - cur, 2), "sigma_s": round(res["sigma_s"], 2),
             "method": "event_xcorr", "n_visual": len(vis), "n_audio": int(len(aud)), "n_matched": res["n_matched"],
             "p_value": round(res["p_value"], 4), "tau_range_s": [round(x, 2) for x in res["tau_range"]],
             "visual_kinds": sorted({k for _, _, k in vis}), "audio_sources": src, "current_audio_offset_s": cur,
             "window": [iso(from_unix(t0)), iso(from_unix(t1))],
             "convention": "offset_s is StreamClock.audio_offset_s (added to audio real time) that aligns sound and picture"}
        self._last_av = {"residual_s": res["residual_s"], "sigma_s": res["sigma_s"], "t": t1}
        conf = float(np.clip(0.2 + 0.05 * res["n_matched"], 0.2, 0.5))
        return [Observation(kind="av_offset", ts=from_unix(t1), value=v, analyzer=self.name, confidence=round(conf, 3),
                            ts_capture=from_unix(t1 + self._cap_off))]


def _coverage(vis_a, vis_b, aud, taus, tol):
    """For each tau: number of visual windows [a - tol, b + tol] containing some audio event at t - tau."""
    if not len(aud):
        return np.zeros(len(taus), int)
    out = np.zeros(len(taus), int)
    for a, b in zip(vis_a, vis_b):
        lo = np.searchsorted(aud, a - tol + taus, "left")      # audio in [a - tol + tau, b + tol + tau]
        hi = np.searchsorted(aud, b + tol + taus, "right")
        out += (hi > lo)
    return out


def estimate_av_offset(vis, aud, max_offset=20.0, step=0.1, tol=0.5, n_null=200, seed=0):
    """Event-train alignment of visual onset windows and audio event times (all unix seconds).
    residual_s = audio - video; p_value from randomly shifted audio trains."""
    if not vis or len(aud) == 0:
        return None
    aud = np.sort(np.asarray(aud, dtype=np.float64))
    va = np.array([v[0] for v in vis])
    vb = np.array([v[1] for v in vis])
    taus = np.arange(-max_offset, max_offset + step / 2, step)
    cov = _coverage(va, vb, aud, taus, tol)
    best = int(cov.max())
    if best == 0:
        return None
    j = int(np.argmax(cov))
    # the contiguous tau interval at the maximum around the first argmax, and all maxima
    i0 = j
    while i0 > 0 and cov[i0 - 1] == best:
        i0 -= 1
    i1 = j
    while i1 < len(taus) - 1 and cov[i1 + 1] == best:
        i1 += 1
    # null: circularly shifted audio train within the observed span (keeps its rate and clustering)
    base = min(float(aud.min()), float(va.min())) - max_offset
    span = max(float(aud.max()), float(vb.max())) + max_offset - base
    if span < 4 * (2 * max_offset + 60.0):
        return None                                   # too short to judge significance
    rng = np.random.default_rng(seed)
    null = np.empty(n_null)
    for k in range(n_null):
        s = rng.uniform(2 * max_offset + 30.0, span - 2 * max_offset - 30.0)
        null[k] = _coverage(va, vb, np.sort((aud - base + s) % span + base), taus, tol).max()
    pval = (1.0 + float(np.sum(null >= best))) / (1.0 + n_null)
    tau_c = 0.5 * (taus[i0] + taus[i1])
    width = taus[i1] - taus[i0] + step
    n_max_regions = int(np.sum((cov[1:] == best) & (cov[:-1] != best)) + (cov[0] == best))
    return {"residual_s": float(tau_c), "sigma_s": float(width / 2 / math.sqrt(3) + 0.25), "n_matched": best,
            "match_frac": best / float(len(vis)), "p_value": pval, "tau_range": (float(taus[i0]), float(taus[i1])),
            "n_max_regions": n_max_regions, "null_median": float(np.median(null))}
