"""Tests for the audio analyzers (audio_events, audio_loop, birds) on synthetic signals.

Offline and deterministic. Signals are synthesised with numpy at 16 kHz and fed as 10 s
AudioChunks with explicit real/capture timestamps, as the ingest layer would.
"""
from __future__ import annotations

import json
import sys
import types
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from hordewatch.analyzers.audio_events import AudioEventAnalyzer, find_bell_strikes, fit_passby
from hordewatch.analyzers.audio_loop import (AudioLoopAnalyzer, FingerprintStore, estimate_av_offset,
                                             match_offsets)
from hordewatch.analyzers.base import Context
from hordewatch.analyzers.birds import BirdAnalyzer
from hordewatch.db import DB
from hordewatch.types import KINDS, AudioChunk, Observation, iso, parse_iso

SR = 16000
UTC = timezone.utc
T0 = datetime(2026, 9, 22, 10, 0, 0, tzinfo=UTC)
LATENCY = 30.0


# ============================================================================ synthesis
def pink(n, rng, lo=20.0, hi=8000.0):
    """Unit-variance 1/f noise band-limited to [lo, hi] Hz."""
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.zeros_like(f)
    m = (f >= lo) & (f <= hi)
    g[m] = 1 / np.sqrt(f[m])
    y = np.fft.irfft(X * g, n)
    return y / (np.std(y) + 1e-12)


def background(dur, rng, level=0.003):
    return level * pink(int(dur * SR), rng)


def aircraft_pass(dur=300.0, t_peak=143.7, width=90.0, amp=10.0, seed=1):
    """Pink noise 50-1500 Hz under a 90 s rise/fall (sin^2) envelope + a 300 Hz tone drifting
    315 -> 285 Hz (Doppler-like tanh) centred on the peak, over a quiet broadband background."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    u = (t - (t_peak - width / 2)) / width
    env = np.where((u >= 0) & (u <= 1), np.sin(np.pi * np.clip(u, 0, 1)) ** 2, 0.0)
    y = background(dur, rng) + env * 0.003 * amp * pink(n, rng, 50, 1500)
    f = 300.0 - 15.0 * np.tanh((t - t_peak) / 15.0)
    y += env * 0.003 * amp * 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR)
    return y.astype(np.float32)


def lorentz_pass(dur=300.0, t_peak=151.3, tau=20.0, snr_db=12.0, seed=8, lo=50, hi=1500):
    """Physical pass-by: intensity 1 / (1 + ((t - t0) / tau)^2), tau = d / v."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    inten = 1.0 / (1 + ((t - t_peak) / tau) ** 2)
    frac = np.log(hi / lo) / np.log(8000 / 20)
    a = 0.003 * np.sqrt(frac) * 10 ** (snr_db / 20)
    return (background(dur, rng) + a * np.sqrt(inten) * pink(n, rng, lo, hi)).astype(np.float32)


def rain(dur=60.0, rate=150.0, amp=0.05, seed=2):
    """Dense Poisson impulses (drops on the roof): 3 ms broadband clicks, log-normal amplitudes."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    y = background(dur, rng, 0.002)
    k = rng.poisson(rate * dur)
    pos = rng.integers(0, n - 100, k)
    amps = amp * np.exp(rng.normal(0, 0.7, k))
    L = 48
    decay = np.exp(-np.arange(L) / SR / 0.0006)
    for p, a in zip(pos, amps):
        y[p:p + L] += a * rng.standard_normal(L) * decay
    return y.astype(np.float32)


def gunshot(dur=40.0, t_shot=19.6, echo_delay=0.62, seed=3):
    """Broadband impulse (0.5 ms rise, 40 ms decay) across a chunk boundary + an echo at -14 dB."""
    rng = np.random.default_rng(seed)
    y = background(dur, rng)
    L = SR
    tt = np.arange(L) / SR
    burst = pink(L, rng, 100, 7000) * np.exp(-tt / 0.04) * np.minimum(tt / 0.0005, 1)
    burst = 0.6 * burst / np.max(np.abs(burst))
    i = int(t_shot * SR)
    y[i:i + L] += burst
    j = int((t_shot + echo_delay) * SR)
    y[j:j + L] += 0.2 * burst
    return y.astype(np.float32)


def chainsaw(dur=30.0, t_on=5.0, t_off=25.0, f0=180.0, amp=0.08, seed=4):
    """Two-stroke buzz: 24-harmonic series at ~180 Hz (slow +-3 % rpm drift, 0.3 % jitter) + noise."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    jit = 1 + 0.06 * np.convolve(rng.standard_normal(n), np.ones(800) / 800, "same")
    f = f0 * (1 + 0.03 * np.sin(2 * np.pi * 0.1 * t)) * jit
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum((1 / k ** 0.7) * np.sin(k * ph + rng.uniform(0, 6.28)) for k in range(1, 25))
    s = s / np.std(s)
    env = np.convolve(((t >= t_on) & (t < t_off)).astype(float), np.ones(1600) / 1600, "same")
    y = background(dur, rng) + amp * env * (s + 0.3 * pink(n, rng, 500, 6000))
    return y.astype(np.float32)


def speech(dur=30.0, t_on=5.0, t_off=25.0, amp=0.05, f0=210.0, seed=5):
    """Speech-like: harmonic source with intonation (f0 +-12 %), formant weighting, syllabic
    gating at ~4-5 Hz with occasional pauses."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 0.12 * np.sin(2 * np.pi * 0.4 * t) + 0.05 * np.sin(2 * np.pi * 1.3 * t + 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.zeros(n)
    for k in range(1, 20):
        fk = k * f0
        form = 1 + 3 * np.exp(-((fk - 700) / 200) ** 2) + 2 * np.exp(-((fk - 1200) / 250) ** 2) \
            + np.exp(-((fk - 2500) / 300) ** 2)
        s += form / k * np.sin(k * ph)
    s /= np.std(s)
    env = np.zeros(n)
    tt = t_on
    while tt < t_off:
        L = rng.uniform(0.12, 0.25)
        i0, i1 = int(tt * SR), int(min(tt + L, t_off) * SR)
        env[i0:i1] = np.sin(np.pi * np.linspace(0, 1, i1 - i0)) ** 2
        tt += L + rng.uniform(0.05, 0.12)
        if rng.random() < 0.12:
            tt += rng.uniform(0.3, 0.6)
    return (background(dur, rng) + amp * env * s).astype(np.float32)


def bells(dur=40.0, t_first=6.3, n_strikes=4, interval=2.5, f=440.0, amp=0.03, seed=6):
    """Church bell: hum 0.5, prime 1, tierce 1.2, quint 1.5, nominal 2, 2.51, 3 with T60 8..1.5 s."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = background(dur, rng)
    for k in range(n_strikes):
        ts = t_first + k * interval
        m = t >= ts
        tt = t[m] - ts
        for r, a, T in zip([0.5, 1.0, 1.2, 1.5, 2.0, 2.51, 3.0], [0.5, 0.6, 0.5, 0.3, 0.7, 0.3, 0.2],
                           [8, 5, 4, 3, 3, 2, 1.5]):
            y[m] += amp * a * np.exp(-6.9 * tt / T) * np.sin(2 * np.pi * f * r * tt)
    return y.astype(np.float32)


def wind(dur=60.0, amp=0.05, seed=7):
    """Microphone wind noise: 15-150 Hz noise with 6 dB (std) gusts on a ~0.2 s time scale."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    g = np.convolve(rng.standard_normal(n // 160 + 10), np.ones(20) / 20, "same")[:n // 160 + 1]
    g = np.repeat(g / np.std(g), 160)[:n]
    gust = 10 ** (np.clip(g * 6, -20, 12) / 20)
    return (background(dur, rng) + amp * pink(n, rng, 15, 150) * gust).astype(np.float32)


def vehicle(dur=120.0, t_peak=61.7, tau=4.0, snr_db=15.0, seed=9):
    """Road vehicle at ~50 m: short pass (tau 4 s), tyre noise peaking near 1 kHz + engine harmonics."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    inten = 1.0 / (1 + ((t - t_peak) / tau) ** 2)
    tyre = pink(n, rng, 300, 4000)
    X = np.fft.rfft(tyre)
    f = np.fft.rfftfreq(n, 1 / SR)
    tyre = np.fft.irfft(X * (1 + 3 * np.exp(-((f - 1000) / 400) ** 2)), n)
    tyre /= np.std(tyre)
    ph = 2 * np.pi * np.cumsum(70 * (1 + 0.02 * np.tanh((t - t_peak) / tau))) / SR
    eng = sum(np.sin(k * ph) / k for k in range(1, 6))
    eng /= np.std(eng)
    a = 0.003 * 10 ** (snr_db / 20)
    return (background(dur, rng) + a * np.sqrt(inten) * (tyre + 0.5 * eng)).astype(np.float32)


def train(dur=240.0, t_on=60.0, t_off=150.0, snr_db=15.0, clack_hz=1.6, seed=10):
    """Train: plateau (line source) with bogie clack pairs every 1/clack_hz s."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    ramp = 15.0
    inten = np.clip(np.minimum((t - (t_on - ramp)) / ramp, ((t_off + ramp) - t) / ramp), 0, 1) ** 2
    a = 0.003 * 10 ** (snr_db / 20)
    y = background(dur, rng) + a * np.sqrt(inten) * pink(n, rng, 50, 3000)
    L = 800
    dec = np.exp(-np.arange(L) / SR / 0.008)
    for tc in np.arange(t_on - ramp, t_off + ramp, 1 / clack_hz):
        for d in (0.0, 0.12):
            i = int((tc + d) * SR)
            if 0 <= i < n - L:
                y[i:i + L] += 4 * a * np.sqrt(inten[i]) * rng.standard_normal(L) * dec
    return y.astype(np.float32)


def forest(dur=300.0, seed=12):
    """Quiet forest: background + bird chirps (FM 2-6 kHz) + occasional twig snaps. Expect nothing."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    y = background(dur, rng)
    for _ in range(rng.poisson(0.8 * dur)):
        L = int(rng.uniform(0.08, 0.35) * SR)
        i = rng.integers(0, n - L)
        tt = np.arange(L) / SR
        f0 = rng.uniform(2000, 6000)
        f = f0 + (f0 * rng.uniform(0.7, 1.4) - f0) * tt / tt[-1]
        y[i:i + L] += rng.uniform(0.005, 0.05) * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / tt[-1]) ** 2
    for _ in range(rng.poisson(0.05 * dur)):
        i = rng.integers(0, n - 200)
        y[i:i + 200] += rng.uniform(0.01, 0.05) * rng.standard_normal(200) * np.exp(-np.arange(200) / 30)
    return y.astype(np.float32)


def make_chunks(y, t_start=0.0, chunk_s=10.0, sr=SR):
    n = int(chunk_s * sr)
    out = []
    for k, i in enumerate(range(0, len(y) - n + 1, n)):
        rt = T0 + timedelta(seconds=t_start + i / sr)
        out.append(AudioChunk(index=k, capture_ts=rt + timedelta(seconds=LATENCY), real_ts=rt,
                              samples=np.asarray(y[i:i + n], dtype=np.float32), sr=sr))
    return out


def run_events(y, analyzer=None, ctx=None, t_start=0.0, sr=SR):
    a = analyzer or AudioEventAnalyzer({})
    ctx = ctx or Context(db=None, config={}, clock=None)
    obs = []
    for c in make_chunks(y, t_start, sr=sr):
        obs += a.on_audio(c, ctx)
    return obs


def secs(o, ref=0.0):
    return (o.ts - T0).total_seconds() - ref


def kinds(obs):
    return sorted({o.kind for o in obs})


_CACHE: dict = {}


def cached(name, fn):
    """Run each synthetic scenario once per test session."""
    if name not in _CACHE:
        _CACHE[name] = run_events(fn())
    return _CACHE[name]


# ============================================================================ audio_events
def test_background_only_is_quiet():
    obs = run_events(background(120, np.random.default_rng(11)).astype(np.float32))
    assert obs == []


def test_forest_birds_and_snaps_no_false_events():
    assert cached("forest", forest) == []


def test_aircraft_pass_peak_time_and_doppler():
    obs = cached("aircraft", aircraft_pass)
    assert kinds(obs) == ["audio_aircraft"], [(o.kind, o.value) for o in obs]
    o = obs[0]
    v = o.value
    # peak loudness (closest approach) within +-5 s -- in practice ~0.3 s
    assert abs(secs(o, 143.7)) <= 5.0
    assert abs((parse_iso(v["peak_ts"]) - T0).total_seconds() - 143.7) <= 5.0
    assert 0 < v["peak_sigma_s"] <= 5.0
    assert v["snr_db"] >= 15
    assert o.ts_capture == o.ts + timedelta(seconds=LATENCY)
    # Doppler: tone falls 315 -> 285 Hz, midpoint at the peak
    d = v["doppler"]
    assert d is not None and d["consistent"]
    assert d["drift_hz"] < -20 and 305 <= d["f_start_hz"] <= 325 and 275 <= d["f_end_hz"] <= 295
    assert abs((parse_iso(d["t_mid_ts"]) - T0).total_seconds() - 143.7) <= 3.0
    assert "Hz" in v["doppler_hint"]
    assert 0.2 <= o.confidence <= 0.75
    json.loads(o.value_json())


@pytest.mark.parametrize("tau,snr,t_peak,gamma_hint", [(20.0, 12.0, 151.3, 1.0), (30.0, 8.0, 148.2, 1.0)])
def test_lorentzian_pass_physics(tau, snr, t_peak, gamma_hint):
    obs = run_events(lorentz_pass(tau=tau, snr_db=snr, t_peak=t_peak))
    air = [o for o in obs if o.kind == "audio_aircraft"]
    assert len(air) == 1 and kinds(obs) == ["audio_aircraft"]
    o = air[0]
    assert abs(secs(o, t_peak)) <= 2.0
    f = o.value["features"]
    assert abs(f["fwhm_s"] - 2 * tau) <= 0.25 * 2 * tau        # FWHM of 1/(1+(t/tau)^2) is 2 tau
    assert 0.6 <= f["gamma"] <= 1.6
    assert abs(o.value["snr_db"] - snr) <= 3.0


def test_aircraft_under_wind_uses_mid_band():
    y = lorentz_pass(snr_db=14) + wind(300, amp=0.01)
    obs = run_events(y)
    air = [o for o in obs if o.kind == "audio_aircraft"]
    assert len(air) == 1 and abs(secs(air[0], 151.3)) <= 5.0
    assert air[0].value["features"]["variant"] == "mid"
    assert "audio_wind" in kinds(obs)


def test_fit_passby_recovers_asymmetric_peak():
    t = np.arange(-120, 120, 0.5)
    rng = np.random.default_rng(0)
    tr, tf, t0 = 12.0, 25.0, 7.3
    tau = np.where(t < t0, tr, tf)
    P = 1e-5 + 1e-4 / (1 + ((t - t0) / tau) ** 2)
    L = 10 * np.log10(P) + rng.normal(0, 0.4, len(t))
    fit = fit_passby(t, L, -50.0)
    assert abs(fit["t0"] - t0) < 1.0 and fit["sigma_t0"] < 2.0
    assert abs(fit["tau_r"] - tr) / tr < 0.3 and abs(fit["tau_f"] - tf) / tf < 0.3


def test_rain_hiss():
    obs = cached("rain", rain)
    assert kinds(obs) == ["audio_rain"]
    v = obs[0].value
    assert 0.0 <= v["intensity"] <= 1.0 and v["intensity_label"] in ("light", "moderate", "heavy")
    assert v["impact_rate_hz"] >= 20 and v["continuity"] >= 0.7
    assert obs[0].confidence <= 0.6


def test_gunshot_with_echo_across_chunk_boundary():
    obs = cached("gunshot", gunshot)
    assert kinds(obs) == ["audio_gunshot"] and len(obs) == 1   # the echo is not a second shot
    o = obs[0]
    assert abs(secs(o, 19.6)) <= 0.05
    v = o.value
    assert v["snr_db"] >= 25 and 0.03 <= v["decay20_s"] <= 1.0
    assert any(abs(e["delay_s"] - 0.62) <= 0.03 for e in v["echoes"])
    assert all(abs(e["reflector_m"] - 340 * e["delay_s"] / 2) <= 2 for e in v["echoes"])
    assert o.confidence <= 0.55


def test_chainsaw_harmonic_buzz():
    obs = cached("chainsaw", chainsaw)
    assert kinds(obs) == ["audio_chainsaw"], [(o.kind, o.value) for o in obs]
    v = obs[0].value
    assert v["type"] == "chainsaw" and 165 <= v["f0_hz"] <= 195
    assert v["n_harmonics"] >= 5 and v["snr_db"] >= 12
    assert 9000 <= v["rpm_est"] <= 12000


def test_speech_like_signal():
    obs = cached("speech", speech)
    assert kinds(obs) == ["audio_voice"], [(o.kind, o.value) for o in obs]
    v = obs[0].value
    assert v["speaker_hint"] == "female" and 180 <= v["f0_median_hz"] <= 240
    assert v["mod_frac_2_8hz"] >= 0.3 and v["snr_db"] >= 6
    assert v["onsets_ts"] and abs((parse_iso(v["onsets_ts"][0]) - T0).total_seconds() - 5.0) <= 0.6
    assert abs(secs(obs[0], 5.0)) <= 0.6


def test_bells_strikes_and_clock_hint():
    obs = cached("bells", bells)
    assert kinds(obs) == ["audio_bells"], [(o.kind, o.value) for o in obs]
    v = obs[0].value
    assert v["n_strikes"] == 4 and abs(v["strike_interval_s"] - 2.5) <= 0.2
    assert any(abs(f - 528) < 8 for f in v["partials_hz"])          # the minor-third tierce
    assert v["inharmonicity"] > 0
    assert abs(secs(obs[0], 6.3)) <= 0.3
    ch = v["clock_hint"]      # 10:00:06 UTC = 12:00:06 CEST -> expects 12 strikes, got 4
    assert ch["nearest_local_hour"] == "12:00" and ch["expected_strikes"] == 12 and not ch["matches"]


def test_bell_strike_finder_direct():
    y = bells(dur=20).astype(np.float64)
    st = find_bell_strikes(y, 0.0)
    assert len(st) == 4
    assert np.allclose([s["t"] for s in st], [6.3, 8.8, 11.3, 13.8], atol=0.3)


def test_wind_gusts():
    obs = cached("wind", wind)
    assert kinds(obs) == ["audio_wind"]
    v = obs[0].value
    assert v["roughness_db"] >= 2.5 and v["lf_frac"] >= 0.5 and v["level_db"] < 0


def test_vehicle_short_pass():
    obs = run_events(vehicle())
    assert kinds(obs) == ["audio_vehicle"], [(o.kind, o.value) for o in obs]
    assert abs(secs(obs[0], 61.7)) <= 2.0


def test_train_plateau_with_clacks():
    obs = run_events(train())
    assert kinds(obs) == ["audio_train"], [(o.kind, o.value) for o in obs]
    assert 60 <= secs(obs[0]) <= 150 and obs[0].value["features"]["clack"] >= 0.3


def test_cross_class_exclusivity():
    """Each synthetic class fires only its own detector."""
    for name, fn, want in (("chainsaw", chainsaw, "audio_chainsaw"), ("speech", speech, "audio_voice"),
                           ("bells", bells, "audio_bells"), ("rain", rain, "audio_rain"),
                           ("gunshot", gunshot, "audio_gunshot")):
        assert kinds(cached(name, fn)) == [want], name


def test_timeline_gaps_silence_and_resampling():
    a = AudioEventAnalyzer({})
    ctx = Context(db=None, config={}, clock=None)
    y = background(40, np.random.default_rng(3)).astype(np.float32)
    ch = make_chunks(y)
    assert a.on_audio(ch[0], ctx) == [] and a.on_audio(ch[1], ctx) == []
    # 20 s gap (NaN-filled), then a 2 h jump (history reset), then digital silence
    for c, dt in ((ch[2], 20.0), (ch[3], 7200.0)):
        c.real_ts += timedelta(seconds=dt)
        c.capture_ts += timedelta(seconds=dt)
        assert a.on_audio(c, ctx) == []
    silent = AudioChunk(index=9, capture_ts=ch[3].capture_ts + timedelta(seconds=10),
                        real_ts=ch[3].real_ts + timedelta(seconds=10), samples=np.zeros(SR * 10, np.float32))
    assert a.on_audio(silent, ctx) == [] and ctx.state["audio_silent"] is True
    ring = ctx.state["audio_ring"]
    assert ring["sr"] == SR and ring["data"].dtype == np.float32
    # 48 kHz input is resampled: the gunshot is still found
    y48 = np.repeat(gunshot(), 3)                     # crude x3 upsampling, content < 8 kHz
    obs = run_events(y48, sr=48000)
    assert "audio_gunshot" in kinds(obs)


def test_loop_suspect_flag_lowers_confidence():
    a = AudioEventAnalyzer({})
    ctx = Context(db=None, config={}, clock=None)
    ctx.state["audio_loop_active"] = {"until": (T0 + timedelta(hours=1)).timestamp(), "lag_s": 86400.0,
                                      "since": T0.timestamp()}
    obs = run_events(chainsaw(), a, ctx)
    assert obs and all(o.value.get("loop_suspect") and o.confidence <= 0.3 for o in obs)


def test_observations_roundtrip_db(tmp_path):
    db = DB(tmp_path / "hw.sqlite")
    obs = cached("aircraft", aircraft_pass) + cached("gunshot", gunshot) + cached("speech", speech)
    for o in obs:
        assert o.kind in KINDS
        db.add_observation(o)
    rows = db.observations(kind="audio_aircraft")
    assert len(rows) == 1 and parse_iso(rows[0]["value"]["peak_ts"]) == parse_iso(obs[0].value["peak_ts"])
    assert rows[0]["ts_capture"] - rows[0]["ts"] == timedelta(seconds=LATENCY)


# ============================================================================ audio_loop
def loop_clip(seed, dur=20.0):
    """Random noise + 30 random tone bursts."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = 0.02 * pink(n, rng, 50, 7000)
    for _ in range(30):
        f, t0, L = rng.uniform(200, 3500), rng.uniform(0, dur - 1), rng.uniform(0.2, 1.5)
        m = (t >= t0) & (t < t0 + L)
        y[m] += rng.uniform(0.01, 0.05) * np.sin(2 * np.pi * f * (t[m] - t0)) * np.hanning(m.sum())
    return y


def feed_loop(a, ctx, y, t_start):
    out = []
    for c in make_chunks(y, t_start):
        out += a.on_audio(c, ctx)
    return out


def _bg(rng, d):
    return 0.004 * pink(int(d * SR), rng)


def test_audio_loop_detects_replay_two_hours_later(tmp_path):
    db = DB(tmp_path / "hw.sqlite")
    a = AudioLoopAnalyzer({})
    ctx = Context(db=db, config={}, clock=None)
    rng = np.random.default_rng(7)
    A = loop_clip(42)
    first = np.concatenate([_bg(rng, 10), A + _bg(rng, 20), _bg(rng, 10)])
    assert feed_loop(a, ctx, first, 0.0) == []
    assert feed_loop(a, ctx, _bg(rng, 60), 3600.0) == []                  # unrelated audio in between
    # replay 2 h later, 3.37 s off the chunk grid, with extra noise (re-encoding stand-in)
    second = np.concatenate([_bg(rng, 3.37), A + 0.5 * _bg(rng, 20), _bg(rng, 16.63)])
    t2 = 7200.0 + 10.0 - 3.37
    out = feed_loop(a, ctx, second, t2)
    assert out and all(o.kind == "audio_loop" for o in out)
    for o in out:
        assert abs(o.value["lag_s"] - 7200.0) <= 0.05
        assert o.value["n_matched"] >= 12 and 0 < o.value["corr"] <= 1
        # the matched stretch lies inside the replayed clip, and ref_ts maps it back to the original
        s0 = (parse_iso(o.value["seg_start"]) - T0).total_seconds()
        assert t2 + 3.37 - 1.0 <= s0 <= t2 + 3.37 + 20.0
        assert abs((parse_iso(o.value["ref_ts"]) - T0).total_seconds() - (s0 - 7200.0)) <= 0.05
    assert max(o.value["run_chunks"] for o in out) >= 2
    assert max(o.confidence for o in out) >= 0.8
    # stored in its own index next to the DB, a human-facing event, and the shared state flag
    assert (tmp_path / "fp" / "audio_fp.sqlite").exists() and a.store.count() > 1000
    ev = db.con.execute("SELECT kind, summary FROM events").fetchall()
    assert len(ev) == 1 and ev[0][0] == "audio_loop" and "2.00 h" in ev[0][1]
    assert ctx.state["audio_loop_active"]["lag_s"] == pytest.approx(7200.0, abs=0.05)
    for o in out:
        db.add_observation(o)
    assert len(db.observations(kind="audio_loop")) == len(out)


def test_audio_loop_no_false_match_between_different_clips():
    a = AudioLoopAnalyzer({"fp_path": ":memory:"})
    ctx = Context(db=None, config={}, clock=None)
    rng = np.random.default_rng(8)
    feed_loop(a, ctx, np.concatenate([_bg(rng, 10), loop_clip(42) + _bg(rng, 20), _bg(rng, 10)]), 0.0)
    out = feed_loop(a, ctx, np.concatenate([_bg(rng, 10), loop_clip(43) + _bg(rng, 20), _bg(rng, 10)]), 7200.0)
    assert out == []
    # a repeat within min_lag_s (10 min) is not reported either (repetitive nature sounds)
    out = feed_loop(a, ctx, np.concatenate([_bg(rng, 10), loop_clip(43) + _bg(rng, 20), _bg(rng, 10)]), 7400.0)
    assert out == []


def test_fingerprint_store_prune_and_version(tmp_path):
    p = tmp_path / "fp.sqlite"
    st = FingerprintStore(p)
    day = 86400.0 / 0.016
    t_old = int(1790000000 / 0.016)
    st.add(np.array([1, 2, 3], np.int64), np.array([t_old, t_old, t_old], np.int64))
    st.add(np.array([1, 5], np.int64), np.array([t_old + int(3 * day), t_old + int(3 * day) + 7], np.int64))
    assert len(st.tables()) == 2
    h, t = st.query(np.array([1, 5]), t_old + int(4 * day))
    assert sorted(h.tolist()) == [1, 1, 5]
    st.prune(t_old + int(3 * day), 36 * 3600.0)
    assert len(st.tables()) == 1
    st.close()
    st2 = FingerprintStore(p)
    assert st2.count() == 2


def test_match_offsets_rejects_periodic_comb():
    # a periodic sound: the same hashes recur every 5 s -> many equally strong offsets
    rng = np.random.default_rng(1)
    q_h = rng.integers(0, 1 << 22, 200)
    q_t = 10_000_000 + np.sort(rng.integers(0, 600, 200))
    r_h = np.concatenate([q_h] * 6)
    r_t = np.concatenate([q_t - 100_000 - k * 312 for k in range(6)])
    m = match_offsets(q_h, q_t, r_h, r_t, 1000, 10 ** 9, 200)
    assert m["n_strong"] == 6          # > max_multi -> the analyzer refuses to call it a loop


# ============================================================================ A/V offset
def test_av_offset_event_alignment(tmp_path):
    """Claps at visual event time + 2.0 s; visual onsets known only within 5 s frame gaps."""
    db = DB(tmp_path / "hw.sqlite")
    a = AudioLoopAnalyzer({"fp_path": ":memory:", "_global": {"source": {"frame_interval_s": 5.0}}})
    ctx = Context(db=db, config={}, clock=types.SimpleNamespace(audio_offset_s=0.0))
    rng = np.random.default_rng(5)
    dur = 700.0
    ev = np.sort(rng.uniform(30, dur - 30, 10))
    ev = ev[np.concatenate([[True], np.diff(ev) > 20])]
    y = _bg(rng, dur)
    L = 1600
    dec = np.exp(-np.arange(L) / SR / 0.01)
    residual = 2.0
    distractors = rng.uniform(10, dur - 10, 12)
    for t in list(ev + residual) + list(distractors):
        i = int(t * SR)
        y[i:i + L] += 0.3 * rng.standard_normal(L) * dec
    for t in ev:                          # frames every 5 s: first frame showing the board
        first_seen = T0 + timedelta(seconds=float(np.ceil(t / 5.0) * 5.0))
        db.add_observation(Observation(kind="whiteboard_visible", ts=first_seen + timedelta(seconds=5),
                                       value={"bbox": [0, 0, 1, 1], "first_seen_ts": iso(first_seen)},
                                       analyzer="whiteboard", confidence=0.7))
    feed_loop(a, ctx, y, 0.0)
    assert len(a._onsets) >= len(ev)
    out = a.on_tick(ctx)
    assert len(out) == 1 and out[0].kind == "av_offset"
    v = out[0].value
    assert abs(v["residual_s"] - residual) <= 1.0
    assert v["offset_s"] == pytest.approx(-v["residual_s"]) and v["audio_lag_s"] == pytest.approx(v["residual_s"])
    assert v["p_value"] <= 0.01 and v["n_matched"] >= 4 and out[0].confidence <= 0.5
    # the same estimate is not repeated on the next tick
    assert a.on_tick(ctx) == []


def test_av_offset_null_when_unrelated():
    rng = np.random.default_rng(9)
    vis = [(t - 5.0, t, "whiteboard_visible") for t in np.sort(rng.uniform(0, 3000, 8))]
    aud = np.sort(rng.uniform(0, 3000, 30))
    res = estimate_av_offset(vis, aud)
    assert res is None or res["p_value"] > 0.01 or res["match_frac"] < 0.5


# ============================================================================ birds
def test_birds_unavailable_without_birdnet(monkeypatch):
    monkeypatch.setitem(sys.modules, "birdnetlib", None)      # import fails
    b = BirdAnalyzer({})
    assert b.available() is False and "birdnetlib" in b.reason
    c = make_chunks(background(10, np.random.default_rng(0)).astype(np.float32))[0]
    assert b.on_audio(c, Context(db=None, config={}, clock=None)) == []


def test_birds_with_fake_birdnet(monkeypatch):
    calls = {}

    class FakeAnalyzer:
        def __init__(self):
            print("loading model")          # birdnetlib prints; must be silenced

    class FakeRecordingBuffer:
        def __init__(self, analyzer, buffer, rate, **kw):
            calls.update(rate=rate, n=len(buffer), kw=kw)

        def analyze(self):
            print("analyze_recording buffer")

        @property
        def detections(self):
            return [
                {"common_name": "Eurasian Wren", "scientific_name": "Troglodytes troglodytes", "start_time": 0.0,
                 "end_time": 3.0, "confidence": 0.62, "label": "Troglodytes troglodytes_Eurasian Wren"},
                {"common_name": "Eurasian Wren", "scientific_name": "Troglodytes troglodytes", "start_time": 3.0,
                 "end_time": 6.0, "confidence": 0.81, "label": "Troglodytes troglodytes_Eurasian Wren"},
                {"common_name": "Coal Tit", "scientific_name": "Periparus ater", "start_time": 6.0,
                 "end_time": 9.0, "confidence": 0.31, "label": "Periparus ater_Coal Tit"},
            ]

    mod = types.ModuleType("birdnetlib")
    mod.RecordingBuffer = FakeRecordingBuffer
    sub = types.ModuleType("birdnetlib.analyzer")
    sub.Analyzer = FakeAnalyzer
    mod.analyzer = sub
    monkeypatch.setitem(sys.modules, "birdnetlib", mod)
    monkeypatch.setitem(sys.modules, "birdnetlib.analyzer", sub)
    b = BirdAnalyzer({})
    assert b.available() is True
    c = make_chunks(background(10, np.random.default_rng(0)).astype(np.float32))[0]
    out = b.on_audio(c, Context(db=None, config={}, clock=None))
    assert calls["rate"] == 48000 and calls["n"] == 480000 and "lat" not in calls["kw"]
    assert len(out) == 1                               # coal tit < 0.5 dropped, wren de-duplicated
    o = out[0]
    assert o.kind == "audio_bird" and o.value["species"] == "Eurasian Wren" and o.value["conf"] == 0.81
    assert o.ts == c.real_ts + timedelta(seconds=3.0) and o.confidence == pytest.approx(0.81 * 0.8, abs=1e-3)


# ============================================================================ runner integration
def test_runner_loads_audio_analyzers(monkeypatch):
    import logging

    from hordewatch.runner import load_analyzers, load_config
    monkeypatch.setitem(sys.modules, "birdnetlib", None)
    cfg = load_config()
    cfg["analyzers"] = ["audio_events", "audio_loop", "birds"]
    names = [a.name for a in load_analyzers(cfg, logging.getLogger("test"))]
    assert names == ["audio_events", "audio_loop"]
