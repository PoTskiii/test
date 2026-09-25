"""Stream health and uplink fingerprinting (analyzer name: ``stream_health``).

Every ``interval_s`` (default 60 s) this reads the ingest statistics that the
source publishes into ``ctx.state['ingest_stats']`` (see
``hordewatch.ingest.StreamStats``; the analyzer subscribes the state dict on
its first call) and writes:

* ``stream_health``: bitrate, input and output fps, drops, stall seconds in the
  window, resolution, reconnects, PDT latency, edge lag, decoder speed. It
  also carries the raw per-segment series of the window
  (``lag_series`` = [[pdt_unix, arrival_lag_s, download_s, kB], ...]) so the
  uplink can be analysed offline later from the DB alone.
* ``stream_stall``: one per new disruption. ``ts`` is the estimated on-site
  start: exact PDT for ``gap`` events and for upstream stalls that have a
  PDT, else capture time minus latency. The value holds
  ``phase_mod_period_s`` (on-site UTC seconds modulo 15).
* ``stream_latency``: the measured HLS PDT latency (capture minus
  PROGRAM-DATE-TIME) with its spread.
* ``uplink_signature``: every ``signature_every_s`` once enough events have
  accumulated, a verdict on how the box is connected.

Why the uplink matters for finding the box
-------------------------------------------
The stream leaves the forest over Starlink or a 4G/5G modem. Each has a
timing fingerprint:

* Starlink reallocates satellites on a global 15 s schedule. Measurement
  studies report latency and throughput changes, and brief outages, at
  seconds ~12, 27, 42 and 57 of every UTC minute, i.e. (unix_time mod 15) ~ 12
  (configurable: ``starlink_phase_s``). A dish partly obstructed by trees
  loses whole 15 s slots whenever the scheduled satellite sits behind a
  branch. The result is many short outages (<= 15 s) that start at the slot
  boundary. So: a Rayleigh test on the on-site event times folded at 15 s,
  plus a test that inter-event intervals cluster at multiples of 15 s, plus a
  Lomb-Scargle periodogram of the per-segment arrival lag at 1/15 Hz.
  Starlink rain fade also correlates outages with the rain analyzers.
* Cellular: congestion and handover stalls are longer (tens of seconds),
  aperiodic, and more frequent in the evening busy hour (see ``hour_hist``,
  Europe/Oslo). If the link is cellular, the box is inside a mast's coverage,
  so coverage maps become a location prior (and a manual RF search target).
  If it is Starlink, the site probably has poor coverage.

Failure modes, and why confidences stay conservative (at most 0.75):
our own network hiccups look like upstream stalls unless downloads fail
(``local`` events are excluded). YouTube's own ingest and transcode add
jitter. Segment granularity (2-5 s) and latency jitter blur the phase. An
encoder that buffers and back-fills hides outages, which then show only as
arrival-lag spikes. And none of this works without disruptions to observe.
"""
from __future__ import annotations

import logging
import math
import time
from collections import deque
from datetime import datetime
from typing import Optional

import numpy as np

from ..types import UTC, Observation
from .base import Analyzer

log = logging.getLogger("hordewatch.analyzers.stream_health")

DISRUPTIVE = ("upstream", "gap", "decoder")
STALL_CONF = {"gap": 0.8, "upstream": 0.6, "decoder": 0.4, "local": 0.5, "reconnect": 0.5, "skip": 0.4}


# ============================================================================ statistics
def rayleigh(times, period: float) -> dict:
    """Rayleigh test for phase concentration of event times folded at ``period``.

    Returns R (mean resultant length), z = nR^2, p (Zar's approximation) and
    the mean phase in seconds within the period."""
    t = np.asarray(times, dtype=float)
    n = len(t)
    if n == 0:
        return {"n": 0, "R": 0.0, "z": 0.0, "p": 1.0, "phase_s": None}
    ph = 2 * np.pi * np.mod(t, period) / period
    C, S = np.cos(ph).mean(), np.sin(ph).mean()
    R = float(math.hypot(C, S))
    z = n * R * R
    p = math.exp(math.sqrt(1 + 4 * n + 4 * (n * n - (n * R) ** 2)) - (1 + 2 * n))
    phase = (math.atan2(S, C) % (2 * np.pi)) * period / (2 * np.pi)
    return {"n": n, "R": round(R, 4), "z": round(z, 3), "p": float(min(1.0, max(p, 1e-300))), "phase_s": round(phase, 2)}


def period_scan(times, periods=None) -> dict:
    """Rayleigh z over candidate periods; returns the best one (for context / sanity)."""
    if periods is None:
        periods = np.arange(4.0, 90.0, 0.05)
    t = np.asarray(times, dtype=float)
    if len(t) < 3:
        return {"best_period_s": None, "best_z": 0.0}
    t = t - t.min()
    ph = 2 * np.pi * t[None, :] / np.asarray(periods)[:, None]
    z = len(t) * (np.cos(ph).mean(1) ** 2 + np.sin(ph).mean(1) ** 2)
    k = int(np.argmax(z))
    return {"best_period_s": round(float(periods[k]), 2), "best_z": round(float(z[k]), 3)}


def interval_multiple_test(times, period: float, tol: float = 1.5, max_gap: float = 600.0) -> dict:
    """Fraction of consecutive inter-event intervals within ``tol`` of a multiple of ``period``.

    For random (Poisson) timing the chance rate is ~2*tol/period; a one-sided
    binomial test gives p."""
    t = np.sort(np.asarray(times, dtype=float))
    d = np.diff(t)
    d = d[(d > tol) & (d < max_gap)]
    n = len(d)
    if n == 0:
        return {"n_intervals": 0, "frac": None, "p": 1.0}
    r = np.abs(d - period * np.round(d / period))
    k = int((r <= tol).sum())
    p0 = min(1.0, 2 * tol / period)
    try:
        from scipy.stats import binom
        p = float(binom.sf(k - 1, n, p0))
    except Exception:  # normal approximation
        mu, sd = n * p0, math.sqrt(max(n * p0 * (1 - p0), 1e-9))
        p = 0.5 * math.erfc((k - 0.5 - mu) / sd / math.sqrt(2))
    return {"n_intervals": n, "frac": round(k / n, 3), "chance": round(p0, 3), "p": p}


def circ_dist(a: float, b: float, period: float) -> float:
    d = abs((a - b) % period)
    return min(d, period - d)


def lag_periodicity(t, lag, period: float = 15.0) -> Optional[dict]:
    """Lomb-Scargle power of the arrival-lag series at 1/period relative to the rest of the band."""
    t = np.asarray(t, dtype=float)
    y = np.asarray(lag, dtype=float)
    ok = np.isfinite(t) & np.isfinite(y)
    t, y = t[ok], y[ok]
    if len(t) < 30 or np.ptp(t) < 10 * period:
        return None
    y = y - np.median(y)
    if np.allclose(y, 0):
        return None
    dt = float(np.median(np.diff(np.sort(t))))
    fmax = 0.95 * 0.5 / max(dt, 1e-3)       # stay below Nyquist: LS is degenerate there for regular sampling
    fmin = 1.0 / min(np.ptp(t) / 3, 600.0)
    if 1.0 / period > fmax or 1.0 / period < fmin:
        return None
    freqs = np.linspace(fmin, fmax, 400)
    try:
        from scipy.signal import lombscargle
        pw = lombscargle(t - t.min(), y, 2 * np.pi * freqs, normalize=True)
        p15 = float(np.atleast_1d(lombscargle(t - t.min(), y, np.array([2 * np.pi / period]), normalize=True))[0])
    except Exception as e:
        log.debug("lombscargle failed: %s", e)
        return None
    med = float(np.median(pw)) or 1e-9
    near = (np.abs(freqs - 1 / period) < 0.1 / period)
    is_peak = bool(p15 >= 0.95 * float(pw[near].max())) if near.any() else False
    m = len(freqs) / 4.0     # rough number of independent frequencies
    fap = float(min(1.0, m * (1 - p15) ** ((len(t) - 3) / 2.0)))
    return {"power": round(p15, 4), "ratio": round(p15 / med, 2), "is_local_peak": is_peak, "fap": fap,
            "n": int(len(t))}


def _dedupe(times_durs, window: float = 3.0):
    """Merge events closer than ``window`` s (a gap and the stall it causes are one outage)."""
    out = []
    for t, d, m in sorted(times_durs):
        if out and t - out[-1][0] < window:
            out[-1] = (out[-1][0], max(out[-1][1], d), out[-1][2] or m)
            continue
        out.append((t, d, m))
    return out


def classify_uplink(events, lags=None, *, period: float = 15.0, starlink_phase: float = 12.0, min_events: int = 6,
                    long_stall_s: float = 20.0, short_max_s: float = 15.0, p_thresh: float = 0.01,
                    tz: str = "Europe/Oslo") -> dict:
    """Infer Starlink-like vs cellular-like uplink from disruption timing.

    ``events``: [(onsite_unix, duration_s, pdt_based: bool)]; ``lags``: [(pdt_unix, lag_s)].
    """
    ev = _dedupe(events)
    times = np.array([e[0] for e in ev], dtype=float)
    durs = np.array([e[1] for e in ev], dtype=float)
    n = len(ev)
    res = {"verdict": "unknown", "confidence": 0.15, "n_events": n, "period_s": period,
           "starlink_phase_s": starlink_phase}
    if n:
        res.update(n_short=int((durs <= short_max_s).sum()), n_long=int((durs >= long_stall_s).sum()),
                   median_duration_s=round(float(np.median(durs)), 2), total_stall_s=round(float(durs.sum()), 1),
                   span_h=round(float(np.ptp(times)) / 3600.0, 2),
                   pdt_based_frac=round(float(np.mean([bool(e[2]) for e in ev])), 2))
        try:
            from zoneinfo import ZoneInfo
            hours = [datetime.fromtimestamp(t, ZoneInfo(tz)).hour for t in times]
            res["hour_hist"] = np.bincount(hours, minlength=24).astype(int).tolist()
        except Exception:
            pass
    periodic, p_best, phase_dist = False, 1.0, None
    if n >= min_events:
        ray = rayleigh(times, period)
        scan = period_scan(times)
        imt = interval_multiple_test(times, period)
        phase_dist = circ_dist(ray["phase_s"], starlink_phase, period) if ray["phase_s"] is not None else None
        res.update(rayleigh_R=ray["R"], rayleigh_z=ray["z"], rayleigh_p=ray["p"], phase_s=ray["phase_s"],
                   phase_dist_s=None if phase_dist is None else round(phase_dist, 2), **scan,
                   interval_multiple_frac=imt["frac"], interval_multiple_chance=imt.get("chance"),
                   interval_multiple_p=imt["p"], n_intervals=imt["n_intervals"])
        p_best = min(ray["p"], imt["p"])
        periodic = p_best < p_thresh
    lagres = None
    if lags is not None and len(lags) >= 30:
        la = np.asarray(lags, dtype=float)
        lagres = lag_periodicity(la[:, 0], la[:, 1], period)
        if lagres:
            res.update(lag_ls_power=lagres["power"], lag_ls_ratio=lagres["ratio"], lag_ls_fap=lagres["fap"],
                       lag_ls_peak=lagres["is_local_peak"], lag_n=lagres["n"])
    lag_periodic = bool(lagres and lagres["fap"] < p_thresh and lagres["is_local_peak"] and lagres["ratio"] > 5)
    if periodic or lag_periodic:
        conf = 0.35 + 0.1 * min(3.0, -math.log10(max(p_best if periodic else lagres["fap"], 1e-12)) - 1.0)
        if n and float(np.median(durs)) <= short_max_s:
            conf += 0.05
        if phase_dist is not None and phase_dist <= 3.0 and res.get("pdt_based_frac", 0) >= 0.5:
            conf += 0.1   # phase-locked to the Starlink slot boundary, measured on the PDT clock
        res["verdict"] = "starlink_like"
        res["confidence"] = round(min(0.75, conf), 3)
    elif n >= 3 and res.get("n_long", 0) >= 3 and res["n_long"] >= 0.5 * n:
        res["verdict"] = "cellular_like"
        res["confidence"] = round(min(0.45, 0.25 + 0.03 * res["n_long"]), 3)
    return res


# ============================================================================ analyzer
def _dt(unix: float) -> datetime:
    return datetime.fromtimestamp(float(unix), UTC)


class StreamHealthAnalyzer(Analyzer):
    name = "stream_health"
    wants_frames = True
    wants_audio = True
    min_interval_s = 0.0
    tick_interval_s = 60.0

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        c = self.config
        self.interval_s = float(c.get("interval_s", 60.0))
        self.tick_interval_s = self.interval_s
        self.signature_every_s = float(c.get("signature_every_s", 600.0))
        self.min_events = int(c.get("min_events", 6))
        self.history_s = float(c.get("history_h", 24.0)) * 3600.0
        self.period_s = float(c.get("period_s", 15.0))
        self.starlink_phase_s = float(c.get("starlink_phase_s", 12.0))
        self.max_series = int(c.get("max_series_points", 400))
        self._bound = False
        self._last_event_id = 0
        self._last_seg_id = 0
        self._events: deque = deque()     # (onsite_unix, duration_s, pdt_based)
        self._lags: deque = deque()       # (pdt_unix, lag_s)
        self._last_signature: Optional[float] = None
        self._last_obs_ts: Optional[float] = None

    def _bind(self, ctx):
        if self._bound:
            return
        self._bound = True
        try:
            from ..ingest import bind_state
            bind_state(ctx.state)
        except Exception as e:  # ingest package missing/broken: still read ctx.state if someone fills it
            log.info("stream_health: cannot subscribe to ingest stats (%s)", e)

    def on_frame(self, frame, ctx):
        self._bind(ctx)
        return []

    def on_audio(self, chunk, ctx):
        self._bind(ctx)
        return []

    def on_tick(self, ctx):
        self._bind(ctx)
        snap = ctx.state.get("ingest_stats") or ctx.state.get("ingest")
        if not snap:
            try:
                from ..ingest import latest_stats
                snap = latest_stats()
            except Exception:
                snap = None
        if not snap:
            return []
        return self.process(snap, ctx.clock)

    # ------------------------------------------------------------------ core (pure: testable with synthetic snapshots)
    def process(self, snap: dict, clock=None, now: Optional[float] = None) -> list:
        now = float(now if now is not None else snap.get("snapshot_ts") or time.time())
        pdt_timing = snap.get("timing") == "pdt" and snap.get("latency_pdt_s") is not None
        if pdt_timing:
            lat = float(snap["latency_pdt_s"])      # = capture - real_ts (pdt_offset_s already applied)
        else:
            lat = float(getattr(clock, "latency_s", 30.0) if clock is not None else 30.0)
        ts_real = _dt(now - lat)
        ts_cap = _dt(now)
        obs = []

        # --- new disruption events
        events = snap.get("stall_events") or []
        if events and max(e.get("id", 0) for e in events) < self._last_event_id:
            self._last_event_id = 0          # source restarted: ids start again
        new_events = [e for e in events if e.get("id", 0) > self._last_event_id]
        window_stall_s = 0.0
        for e in new_events:
            self._last_event_id = max(self._last_event_id, int(e.get("id", 0)))
            onsite = e.get("onsite_start")
            method = e.get("onsite_method")
            if onsite is None:
                onsite, method = float(e["start"]) - lat, "capture_minus_latency"
            dur = float(e.get("duration_s") or 0.0)
            if e.get("kind") in DISRUPTIVE:
                window_stall_s += dur
                self._events.append((float(onsite), dur, method == "pdt"))
            value = {"kind": e.get("kind"), "start": e.get("start"), "end": e.get("end"), "duration_s": dur,
                     "onsite_start": round(float(onsite), 3), "onsite_method": method,
                     "phase_mod_period_s": round(float(onsite) % self.period_s, 2), "period_s": self.period_s,
                     "seq": e.get("seq"), "detail": e.get("detail", "")}
            obs.append(Observation(kind="stream_stall", ts=_dt(onsite), value=value, analyzer=self.name,
                                   confidence=STALL_CONF.get(e.get("kind"), 0.4), ts_capture=_dt(e.get("end") or now),
                                   notes="local = our network, not the site" if e.get("kind") == "local" else ""))

        # --- new segment records (arrival lag series)
        segs = snap.get("segment_series") or []
        if segs and max(s.get("id", 0) for s in segs) < self._last_seg_id:
            self._last_seg_id = 0
        new_segs = [s for s in segs if s.get("id", 0) > self._last_seg_id]
        series = []
        for s in new_segs:
            self._last_seg_id = max(self._last_seg_id, int(s.get("id", 0)))
            if s.get("pdt") is not None and s.get("lag_s") is not None:
                self._lags.append((float(s["pdt"]), float(s["lag_s"])))
            series.append([s.get("pdt"), s.get("lag_s"), s.get("dl_s"),
                           None if s.get("bytes") is None else round(s["bytes"] / 1000.0, 1)])
        if len(series) > self.max_series:
            series = series[-self.max_series:]

        # --- trim history
        horizon = now - self.history_s
        while self._events and self._events[0][0] < horizon:
            self._events.popleft()
        while self._lags and self._lags[0][0] < horizon:
            self._lags.popleft()

        # --- stream_health
        cur = float(snap.get("current_stall_s") or 0.0)
        health = {
            "bitrate_kbps": snap.get("bitrate_kbps"), "fps": snap.get("fps_in"), "fps_out": snap.get("fps_out"),
            "dropped": snap.get("dropped"), "stall_s": round(window_stall_s + cur, 3),
            "current_stall_s": cur, "resolution": snap.get("resolution"), "reconnects": snap.get("reconnects"),
            "stalls_total": snap.get("stalls"), "stall_s_total": snap.get("stall_s_total"),
            "state": snap.get("state"), "mode": snap.get("mode"), "decoder": snap.get("decoder"),
            "timing": snap.get("timing"), "latency_pdt_s": snap.get("latency_pdt_s"),
            "edge_lag_s": snap.get("edge_lag_s"), "edge_lag_min_s": snap.get("edge_lag_min_s"),
            "speed": snap.get("speed"), "segments": snap.get("segments"),
            "segments_skipped": snap.get("segments_skipped"), "discontinuities": snap.get("discontinuities"),
            "media_deficit_s": snap.get("media_deficit_s"), "target_duration": snap.get("target_duration"),
            "frames_out": snap.get("frames_out"), "audio_s_out": snap.get("audio_s_out"),
            "last_error": snap.get("last_error"), "window_s": self.interval_s, "new_stalls": len(new_events),
            "lag_series": series,
        }
        obs.append(Observation(kind="stream_health", ts=ts_real, value=health, analyzer=self.name, confidence=0.9,
                               ts_capture=ts_cap))

        # --- stream_latency (measured from PDT)
        if pdt_timing:
            lags = [s[1] for s in series if s[1] is not None]
            sigma = float(1.4826 * np.median(np.abs(np.asarray(lags) - np.median(lags)))) if len(lags) >= 3 else None
            obs.append(Observation(
                kind="stream_latency", ts=ts_real, analyzer=self.name, confidence=0.7, ts_capture=ts_cap,
                value={"latency_s": round(lat, 3), "method": "hls_program_date_time",
                       "sigma_s": None if sigma is None else round(sigma, 3), "n": len(lags),
                       "pdt_offset_s": snap.get("pdt_offset_s"), "edge_lag_s": snap.get("edge_lag_s"),
                       "edge_lag_min_s": snap.get("edge_lag_min_s")},
                notes="capture - PROGRAM-DATE-TIME; excludes encoder buffering before the PDT stamp (pdt_offset_s)"))

        # --- uplink signature (periodically, when there is something to say)
        due = self._last_signature is None or now - self._last_signature >= self.signature_every_s
        if due and (len(self._events) >= self.min_events or len(self._lags) >= 60):
            self._last_signature = now
            sig = classify_uplink(list(self._events), list(self._lags), period=self.period_s,
                                  starlink_phase=self.starlink_phase_s, min_events=self.min_events)
            sig["history_h"] = round(self.history_s / 3600.0, 1)
            obs.append(Observation(kind="uplink_signature", ts=ts_real, value=sig, analyzer=self.name,
                                   confidence=float(sig["confidence"]), ts_capture=ts_cap,
                                   notes="Starlink slots: 15 s, boundaries ~:12/:27/:42/:57 UTC (literature); "
                                         "cellular => site within mast coverage"))
        self._last_obs_ts = now
        return obs
