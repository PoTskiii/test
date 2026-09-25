"""Acoustic event detector for the stream's microphone (analyzer name: ``audio_events``).

Input: 16 kHz mono float32 chunks (default 10 s; other rates are resampled). Every
detector uses interpretable DSP features computed once per chunk:

* long STFT (4096 / hop 1024 = 256 ms window, 3.9 Hz bins): band energies, tonal peaks,
  harmonic combs, bell partials;
* short STFT (512 / hop 160 = 32 ms window, 10 ms hop): envelopes, roughness, modulation;
* 2 ms frame energies on the raw ring buffer: impulses (gunshots, echoes, rain drops).

Levels are in dBFS (a full-scale sine is 0 dBFS). Power spectra are scaled so that the sum
over bins is the mean-square of the frame (Parseval). Background: for each band, a *floor
tracker* follows the per-chunk 10th percentile of the 0.5 s block energies. It follows a
quieter background at once and rises by at most ``floor_rise_db_per_min`` (0.6 dB/min), so
a 3-minute aircraft pass raises it by < 2 dB while a new steady background (a generator,
rain for an hour) is absorbed in ~20 min. SNRs are "event level minus that floor".

History and ring buffer
-----------------------
A 0.5 s feature history covering ``history_s`` (420 s) is kept on the analyzer. It holds band
energies, air-band level, roughness, AM periodicity, dominant tone, and floors. Long events
(aircraft, trains) are found in it. The last ``ring_s`` (180 s) of raw audio is published in
``ctx.state['audio_ring']`` (``{'sr', 't_end', 'cap_off', 'data'}``; t_end = real unix time
after the last sample) for other analyzers. Gaps of up to ``gap_fill_max_s`` are NaN-filled.
Longer gaps, or time running backwards, reset the history.

Detectors (all conservative: confidence <= 0.75, most <= 0.55)
-------------------------------------------------------------
audio_aircraft
    A source passing at slant distance d with speed v gives received power
    P(t) = P_floor + A / (1 + ((t - t0) / tau)^2)^gamma, with tau = d / v. gamma = 1 is pure
    spherical spreading. gamma > 1 means steeper tails, from ground effect and absorption at
    grazing angles and from jets radiating aft. Tau differs before and after t0 (tau_rise,
    tau_fall) because passes are asymmetric. The model is fitted by robust least squares in dB,
    with the floor held within +-3 dB of the tracker, to the 1 s-smoothed band level. Distant
    aircraft are low-mid dominated, since absorption above 2 kHz is ~10 dB/km. Events are
    hysteresis segments of the 2 s-smoothed excess over the floor (on 4 dB / off 1.5 dB). They
    are reported once, when closed and settled (10 s). Two band variants run: 'air'
    50-1500 Hz and 'mid' 150-1500 Hz. 'mid' stays usable when microphone wind noise fills
    < 150 Hz. An event reported by one variant is not repeated by the other. Every pass-by
    class requires broadband character (median 50-1500 Hz spectral flatness >= 0.15 at the
    peak; bells and engines are tonal). Aircraft also need a fitted -3 dB width (FWHM)
    of 10-240 s, a duration >= 20 s, >= 60 % of the excess energy in the band, smoothness
    (50 ms roughness <= 2.5 dB, unless periodic 8-30 Hz blade AM => 'helicopter?'),
    fit RMS <= 3 dB, rise/fall asymmetry <= 6, and both flanks observed.
    ``peak_ts`` = fitted t0 = time of peak loudness (for ADS-B matching). ``peak_sigma_s`` is
    its measurement uncertainty: the Gauss-Newton covariance from the raw residuals, inflated
    by the AR(1) factor sqrt((1+rho)/(1-rho)) of the residuals, plus 0.5 s block
    quantisation. Acoustic travel time s/c and directivity are left to the ADS-B bridge.
    Doppler: the dominant tonal line (blade-pass or fan tone, prominence >= 8 dB) is tracked
    over the event and fitted with f(t) = fc - D tanh((t - tc) / w). A falling line gives
    beta = v/c >= D / fc (a lower bound if the asymptotes are not reached) and the
    inflection tc (Doppler zero = CPA reception, geometric and free of directivity bias).
    ``features`` holds everything for later review.
audio_vehicle
    Same segment and fit, but the pass is short (FWHM 2-16 s, since tau = d/v with d ~ 20-300 m)
    and has tyre/road noise (>= 25 % of the excess in 500-4000 Hz). If both aircraft and
    vehicle fit (FWHM 10-16 s), the one with more high frequencies is taken as the vehicle.
audio_train
    Long (>= 30 s) with a plateau (a train is a line source: level within 4 dB of the peak
    for >= 15 s) and periodic wheel/joint clacks (autocorrelation >= 0.3 of the 1-5 kHz
    onset-strength envelope at 0.15-2 s lags).
audio_wind
    Turbulence at the microphone: 20-150 Hz energy >= 50 % of the total, >= 6 dB above its
    floor, and non-stationary. The detrended 64 ms-frame level std over 1 s windows is
    >= 2.5 dB (stationary noise gives ~1 dB). Emitted every ``wind_emit_interval_s`` while
    present. ``level_db`` is the mean dBFS of the wind band.
audio_rain
    Drops hitting the box roof are dense, random broadband impulses. In the 2-8 kHz band
    (Butterworth high-pass), 2 ms frames >= 9 dB above a 200 ms running median are impacts.
    Gaussian noise almost never does this, since 24 degrees of freedom give P < 1e-12. Rain =
    >= 8 impacts/s in >= 70 % of the 1 s windows (continuous, unlike birds), noise-like 2-7 kHz
    spectrum (flatness >= 0.2), in 2 consecutive chunks. ``intensity`` (0-1; < 0.4 light,
    < 0.7 moderate, else heavy, as in bridges/met.py) rises with the log impact rate and the
    HF level above floor.
audio_gunshot
    Impulse >= 25 dB above the 1 s running median, rising >= 18 dB within ~16 ms. It must be
    broadband (>= 15 dB above the background in 200-1000 Hz, >= 8 dB in 1-5 kHz, flatness
    >= 0.15) and decay 20 dB within 0.03-2 s (a click is shorter, a shout longer). Echoes
    are later sharp peaks >= 6 dB above the local decay trend. Each echo gives the distance
    to the reflecting slope or treeline (c * delay / 2), which describes the terrain. Analysed
    on the ring buffer with a 3 s look-ahead, so impulses near chunk edges are complete.
    Failure mode: a tap or clap near the microphone looks the same, so confidence is <= 0.55.
audio_chainsaw
    Harmonic comb salience on the long STFT: H(f0) = mean_k L(k f0) - mean_k L((k+0.5) f0),
    k = 1..8, with the same 3-bin max operator on both, so noise is unbiased. A two-stroke saw
    at 9-14 krpm has f0 80-270 Hz, many strong harmonics (>= 5 of 8), a very stable f0
    (median frame-to-frame |d log2 f0| <= 0.008 octave; throttle glides are smooth), a high
    level (>= 12 dB SNR), and no syllabic modulation. f0 25-80 Hz sustained over the whole
    chunk => type 'machine' (diesel harvester, generator). This is rate-limited, since a
    generator on site would otherwise repeat every chunk.
audio_voice
    Voiced frames (harmonic, f0 70-400 Hz, persistent >= 3 frames) plus syllabic modulation.
    The 300-3400 Hz envelope has >= 4 dB depth and >= 30 % of its 0.5-20 Hz modulation power
    in 2-8 Hz. f0 must vary (intonation, std >= 0.03 octave), which rejects engines.
    ``speaker_hint``: median f0 < 150 Hz 'male', > 175 Hz 'female'. The value also carries
    voiced segments and ``onsets_ts`` (speech onsets after >= 0.5 s silence), which
    audio_loop uses for A/V offset estimation.
audio_bells
    Church bells: struck, slowly decaying, *inharmonic* partials (hum 0.5, prime 1, minor-third
    tierce 1.2, quint 1.5, nominal 2 ...). Tonal peaks (>= 12 dB above the 120 Hz median) are
    tracked across frames and split at re-strikes (+6 dB jumps). A strike = >= 3 partials with
    a common onset (+-130 ms), each lasting >= 0.8 s with a linear dB decay of 1.5-60 dB/s
    (R^2 >= 0.6), and at least one partial >= 0.15 away from the harmonic positions of the
    best f0. Strikes are gathered across chunks into a sequence, which is reported when it
    ends (8 s quiet) and has >= 2 strikes. Clock strikes on the hour give ``clock_hint``: the
    count vs the local (Europe/Oslo) hour and the audio time offset from hh:00:00. That is a
    free absolute timing reference for the audio path.

Failure modes: the stream's AAC encoder may remove < 30 Hz and smear transients. Automatic
gain control changes levels, which the floor tracker partly absorbs. Replayed audio
(audio_loop) makes every audio observation's time meaningless: values carry
``loop_suspect`` when audio_loop flagged the recent audio. Aircraft vs distant road traffic
overlaps at FWHM 10-16 s. Bird song can occasionally look voice-like (wood pigeon coos).
"""
from __future__ import annotations

import logging
import math
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter1d, median_filter, uniform_filter1d

from ..types import Observation, iso
from .base import Analyzer, Context

log = logging.getLogger("hordewatch.audio")

UTC = timezone.utc
SR = 16000
EPS = 1e-14
BLOCK_S = 0.5
N_LONG, HOP_LONG = 4096, 1024
N_SHORT, HOP_SHORT = 512, 160
BANDS = ((20.0, 50.0), (50.0, 150.0), (150.0, 500.0), (500.0, 1500.0), (1500.0, 4000.0), (4000.0, 8000.0))
BAND_NAMES = ("20-50", "50-150", "150-500", "500-1500", "1500-4000", "4000-8000")
AIR_BANDS = (1, 2, 3)      # 50-1500 Hz: propagated aircraft / traffic noise
SOUND_SPEED = 340.0

# history row layout
C_T, C_CAP = 0, 1
C_B0 = 2                   # 6 band energies (linear mean-square)
C_AIR = C_B0 + 6           # air-band level dBFS
C_ROUGH = C_AIR + 1        # 50 ms roughness of air band (dB)
C_AM = C_ROUGH + 1         # 8-30 Hz AM periodicity (helicopter blades)
C_AMF = C_AM + 1           # AM frequency (Hz)
C_TONEF = C_AMF + 1        # dominant tone (Hz)
C_TONEP = C_TONEF + 1      # its prominence (dB)
C_CLACK = C_TONEP + 1      # periodic clack score of the chunk
C_F0 = C_CLACK + 1         # 6 band floors (dB)
C_FAIR = C_F0 + 6          # air-band floor (dB)
C_FLAT = C_FAIR + 1        # spectral flatness 50-1500 Hz (broadband ~0.3-0.7, tonal/bells < 0.1)
C_MID = C_FLAT + 1         # 150-1500 Hz level dBFS (above most wind noise)
C_FMID = C_MID + 1         # its floor
C_RMID = C_FMID + 1        # its 50 ms roughness
N_COLS = C_RMID + 1
MID_BANDS = (2, 3)
# pass-by detection variants: (name, level col, floor col, roughness col, source bands, reference bands)
VARIANTS = (("air", C_AIR, C_FAIR, C_ROUGH, AIR_BANDS, (0, 1, 2, 3, 4, 5)),
            ("mid", C_MID, C_FMID, C_RMID, MID_BANDS, (2, 3, 4, 5)))

DEFAULTS = {
    "history_s": 420.0,
    "ring_s": 180.0,
    "gap_tol_s": 1.0,
    "gap_fill_max_s": 30.0,
    "floor_percentile": 10.0,
    "floor_rise_db_per_min": 0.6,
    "silence_dbfs": -95.0,
    # pass-by events
    "evt_on_db": 4.0, "evt_off_db": 1.5, "evt_merge_gap_s": 4.0, "evt_settle_s": 10.0, "evt_pad_s": 30.0,
    "evt_min_snr_db": 5.0, "evt_max_open_s": 400.0, "evt_min_flatness": 0.15, "evt_max_asym": 6.0,
    "aircraft_fwhm_s": [10.0, 240.0], "aircraft_min_dur_s": 20.0, "aircraft_max_dur_s": 360.0,
    "aircraft_min_air_frac": 0.6, "aircraft_max_rough_db": 2.5, "aircraft_max_fit_rms_db": 3.0,
    "vehicle_fwhm_s": [2.0, 16.0], "vehicle_min_dur_s": 4.0, "vehicle_max_dur_s": 90.0,
    "vehicle_min_mid_frac": 0.25, "vehicle_max_rough_db": 3.0,
    "train_min_dur_s": 30.0, "train_min_clack": 0.3, "train_plateau_s": 15.0,
    # wind
    "wind_min_rough_db": 2.5, "wind_min_lf_frac": 0.5, "wind_min_excess_db": 6.0, "wind_emit_interval_s": 60.0,
    # rain
    "rain_min_rate_hz": 8.0, "rain_min_continuity": 0.7, "rain_min_flatness": 0.2, "rain_confirm_chunks": 2,
    "rain_emit_interval_s": 120.0, "rain_impulse_db": 9.0,
    # harmonic sources
    "harm_min_db": 9.0, "harm_min_n": 3,
    "chainsaw_f0_hz": [80.0, 270.0], "chainsaw_min_frac": 0.4, "chainsaw_min_snr_db": 12.0,
    "chainsaw_min_nharm": 5.0, "chainsaw_max_jitter_oct": 0.008, "chainsaw_max_depth_db": 6.0,
    "chainsaw_emit_interval_s": 60.0,
    "machine_f0_hz": [25.0, 80.0], "machine_min_frac": 0.8, "machine_min_snr_db": 10.0, "machine_emit_interval_s": 600.0,
    "voice_f0_hz": [70.0, 400.0], "voice_min_voiced_frac": 0.08, "voice_min_mod_frac": 0.3,
    "voice_min_depth_db": 4.0, "voice_min_snr_db": 6.0, "voice_min_f0_std_oct": 0.03, "voice_emit_interval_s": 30.0,
    # impulses
    "gun_min_db": 25.0, "gun_min_rise_db": 18.0, "gun_decay_s": [0.03, 2.0], "gun_min_flatness": 0.15,
    "gun_lo_band_db": 15.0, "gun_hi_band_db": 8.0, "imp_pre_s": 1.0, "imp_post_s": 3.0,
    # bells
    "bell_min_prom_db": 12.0, "bell_min_partials": 3, "bell_min_dur_s": 0.8, "bell_seq_gap_s": 8.0,
    "bell_min_strikes": 2, "bell_fmax_hz": 4000.0,
}


# ============================================================================ small helpers
def to_unix(ts: datetime) -> float:
    return ts.timestamp()


def from_unix(t: float) -> datetime:
    return datetime.fromtimestamp(float(t), UTC)


def dbfs(p):
    """Mean-square power -> dBFS (full-scale sine = 0 dBFS)."""
    return 10.0 * np.log10(np.asarray(p, dtype=np.float64) + EPS) + 3.0103


def prepare_samples(samples, sr) -> Optional[np.ndarray]:
    """float64 mono at 16 kHz, NaN-free, DC removed. None when empty."""
    x = np.asarray(samples, dtype=np.float64).ravel()
    if x.size == 0:
        return None
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    np.clip(x, -2.0, 2.0, out=x)
    sr = int(sr or SR)
    if sr != SR:
        g = math.gcd(sr, SR)
        x = signal.resample_poly(x, SR // g, sr // g)
    return x - float(np.mean(x))


def resample(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    if sr_in == sr_out:
        return np.asarray(x, dtype=np.float64)
    g = math.gcd(int(sr_in), int(sr_out))
    return signal.resample_poly(np.asarray(x, dtype=np.float64), sr_out // g, sr_in // g)


_WINDOWS: dict = {}


def _hann(n):
    w = _WINDOWS.get(n)
    if w is None:
        w = _WINDOWS[n] = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n) / n))
    return w


def stft_power(x: np.ndarray, sr: int, n_fft: int, hop: int, center: bool = True):
    """Power spectrogram (frames x bins), Parseval-scaled: sum over bins = frame mean-square.
    Returns (P, frame_times_s, freqs). With center=True frame i is centred on sample i*hop."""
    x = np.asarray(x, dtype=np.float64)
    if center:
        pad = n_fft // 2
        x = np.pad(x, pad, mode="reflect" if len(x) > pad else "constant")
    if len(x) < n_fft:
        x = np.pad(x, (0, n_fft - len(x)))
    w = _hann(n_fft)
    fr = np.lib.stride_tricks.sliding_window_view(x, n_fft)[::hop]
    X = np.fft.rfft(fr * w, axis=1)
    P = (X.real ** 2 + X.imag ** 2) / (n_fft * float(np.sum(w * w)))
    P[:, 1:-1] *= 2.0
    t = np.arange(P.shape[0]) * hop / float(sr) + (0.0 if center else n_fft / (2.0 * sr))
    f = np.fft.rfftfreq(n_fft, 1.0 / sr)
    return P, t, f


def local_background_db(L: np.ndarray, width: int = 31, axis: int = -1, clip_db: float = 6.0) -> np.ndarray:
    """Robust local spectral background (dB): moving mean, then the mean again with values
    clipped at +clip_db above it. Tonal peaks barely raise it, and it is ~20x cheaper than a
    median filter."""
    m = uniform_filter1d(L, width, axis=axis, mode="nearest")
    return uniform_filter1d(np.minimum(L, m + clip_db), width, axis=axis, mode="nearest")


def band_slice(freqs, lo, hi):
    i0 = int(np.searchsorted(freqs, lo, side="left"))
    i1 = int(np.searchsorted(freqs, hi, side="left"))
    return slice(max(i0, 1), max(i1, i0 + 1))


def smooth_db(L: np.ndarray, w: int) -> np.ndarray:
    """NaN-aware moving average in the power domain, back to dB."""
    L = np.asarray(L, dtype=np.float64)
    if w <= 1:
        return L.copy()
    m = np.isfinite(L)
    P = np.where(m, 10.0 ** (np.where(m, L, 0.0) / 10.0), 0.0)
    num = uniform_filter1d(P, w, mode="nearest")
    den = uniform_filter1d(m.astype(np.float64), w, mode="nearest")
    out = np.full_like(L, np.nan)
    ok = den > 0.3
    out[ok] = 10.0 * np.log10(num[ok] / den[ok] + EPS)
    return out


def hysteresis_segments(E: np.ndarray, on: float, off: float, merge_gap: int = 0):
    """[(i0, i1)] (i1 exclusive) runs with E > off containing at least one E > on; NaN breaks runs."""
    above = np.isfinite(E) & (E > off)
    runs, i, n = [], 0, len(E)
    while i < n:
        if above[i]:
            j = i
            while j < n and above[j]:
                j += 1
            runs.append([i, j])
            i = j
        else:
            i += 1
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] <= merge_gap and np.all(np.isfinite(E[merged[-1][1]:r[0]])):
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [(a, b) for a, b in merged if np.nanmax(E[a:b]) > on]


def parabolic_peak(y: np.ndarray, i: int):
    """Sub-sample peak offset (and value) around index i by a parabola through 3 points."""
    if i <= 0 or i >= len(y) - 1:
        return 0.0, float(y[i])
    a, b, c = float(y[i - 1]), float(y[i]), float(y[i + 1])
    d = a - 2 * b + c
    if not np.isfinite(d) or d >= 0:
        return 0.0, b
    off = 0.5 * (a - c) / d
    return float(np.clip(off, -0.5, 0.5)), b - 0.25 * (a - c) * off


def spectral_flatness(P: np.ndarray, axis=-1):
    P = np.asarray(P, dtype=np.float64) + EPS
    return np.exp(np.mean(np.log(P), axis=axis)) / np.mean(P, axis=axis)


def norm_autocorr(x: np.ndarray, lags):
    """Normalised autocorrelation of a zero-mean-ised series at integer lags."""
    x = np.asarray(x, dtype=np.float64)
    x = x - np.mean(x)
    den = float(np.dot(x, x)) + EPS
    out = []
    for L in lags:
        if L >= len(x) - 2:
            out.append(0.0)
        else:
            out.append(float(np.dot(x[:-L], x[L:])) / den * len(x) / (len(x) - L))
    return np.asarray(out)


def oslo_offset(t: datetime) -> timedelta:
    try:
        from zoneinfo import ZoneInfo
        return t.astimezone(ZoneInfo("Europe/Oslo")).utcoffset()
    except Exception:  # pragma: no cover - tzdata missing: CEST during the hunt
        return timedelta(hours=2)


def pick(cfg: dict, key: str):
    v = cfg.get(key, DEFAULTS.get(key))
    return v


# ============================================================================ per-chunk features
class ChunkFeatures:
    """All spectral features of one chunk (computed once, shared by the detectors)."""

    def __init__(self, x: np.ndarray, t0: float):
        self.x = x
        self.t0 = t0
        self.n = len(x)
        self.dur = self.n / SR
        self.Pl, self.tl, self.fl = stft_power(x, SR, N_LONG, HOP_LONG)
        self.Ps, self.ts, self.fs = stft_power(x, SR, N_SHORT, HOP_SHORT)
        self.logPl = 10.0 * np.log10(self.Pl + EPS)
        self.df = float(self.fl[1])
        self._harm = None
        # band energies per long frame
        self.bands_l = np.stack([self.Pl[:, band_slice(self.fl, lo, hi)].sum(1) for lo, hi in BANDS], 1)
        self.n_blocks = int(self.dur // BLOCK_S)
        self._blocks()

    # ---------------------------------------------------------------- 0.5 s blocks
    def _blocks(self):
        nb = self.n_blocks
        self.block_t = self.t0 + np.arange(nb) * BLOCK_S
        B = np.full((nb, 6), np.nan)
        tone_f = np.full(nb, np.nan)
        tone_p = np.zeros(nb)
        flat = np.full(nb, np.nan)
        sl_air = band_slice(self.fl, 50.0, 1500.0)
        bidx = np.floor(self.tl / BLOCK_S).astype(int)
        sl_tone = band_slice(self.fl, 60.0, 2000.0)
        for b in range(nb):
            sel = bidx == b
            if not np.any(sel):
                continue
            B[b] = self.bands_l[sel].mean(0)
            mp = self.Pl[sel].mean(0)
            flat[b] = float(spectral_flatness(mp[sl_air]))
            spec = 10 * np.log10(mp + EPS)
            seg = spec[sl_tone]
            prom = seg - local_background_db(seg, 31)
            i = int(np.argmax(prom))
            off, _ = parabolic_peak(seg, i)
            tone_f[b] = (sl_tone.start + i + off) * self.df
            tone_p[b] = float(prom[i])
        self.block_bands = B
        self.block_tone_f, self.block_tone_p = tone_f, tone_p
        self.block_flat = flat
        # air-band roughness: 50 ms sub-block levels within each block, detrended std
        air = self.Ps[:, band_slice(self.fs, 50.0, 1500.0)].sum(1)
        mid = self.Ps[:, band_slice(self.fs, 150.0, 1500.0)].sum(1)
        self.env_air_db = dbfs(air)
        self.block_rough = self._roughness(air, nb)
        self.block_rough_mid = self._roughness(mid, nb)
        # helicopter-type AM (8-30 Hz) on 1 s windows of the 10 ms air envelope
        am = np.zeros(nb)
        amf = np.full(nb, np.nan)
        fps = SR / HOP_SHORT
        lags = np.arange(3, 13)
        for w0 in range(0, nb, 2):
            i0 = int(round(w0 * BLOCK_S * fps))
            seg = self.env_air_db[i0:i0 + int(fps)]
            if len(seg) < 60:
                continue
            ac = norm_autocorr(seg - uniform_filter1d(seg, 15, mode="nearest"), lags)
            j = int(np.argmax(ac))
            am[w0:w0 + 2] = ac[j]
            amf[w0:w0 + 2] = fps / lags[j]
        self.block_am, self.block_amf = am, amf
        # periodic clacks (train wheels / rail joints): 1-5 kHz onset-strength autocorrelation
        hf = dbfs(self.Ps[:, band_slice(self.fs, 1000.0, 5000.0)].sum(1))
        onset = np.maximum(np.diff(uniform_filter1d(hf, 3, mode="nearest")), 0.0)
        if len(onset) > 250:
            lags = np.arange(15, 200)
            ac = norm_autocorr(onset, lags)
            j = int(np.argmax(ac))
            self.clack, self.clack_period = float(ac[j]), float(lags[j] / fps)
        else:
            self.clack, self.clack_period = 0.0, float("nan")

    @staticmethod
    def _roughness(env: np.ndarray, nb: int, sub: int = 5) -> np.ndarray:
        """Per 0.5 s block: std (dB) of the linearly detrended 50 ms sub-block levels."""
        rough = np.full(nb, np.nan)
        n_per = int(BLOCK_S * SR / HOP_SHORT)
        for b in range(nb):
            i0 = int(round(b * BLOCK_S * SR / HOP_SHORT))
            seg = env[i0:i0 + n_per]
            k = len(seg) // sub
            if k < 4:
                continue
            lv = dbfs(seg[:k * sub].reshape(k, sub).mean(1))
            xx = np.arange(k)
            lv = lv - np.polyval(np.polyfit(xx, lv, 1), xx)
            rough[b] = float(np.std(lv))
        return rough

    # ---------------------------------------------------------------- harmonic comb
    def harmonic(self, f0_lo=25.0, f0_hi=400.0, K=8):
        """Per long frame: best f0, comb salience H (dB), number of strong harmonics, level."""
        if self._harm is not None:
            return self._harm
        grid = np.arange(f0_lo, f0_hi + 0.25, 0.5)
        L = maximum_filter1d(self.logPl, size=3, axis=1)
        F = L.shape[1]
        k = np.arange(1, K + 1)
        on = np.clip(np.rint(np.outer(grid, k) / self.df).astype(int), 0, F - 1)
        off = np.clip(np.rint(np.outer(grid, k + 0.5) / self.df).astype(int), 0, F - 1)
        T = L.shape[0]
        f0 = np.zeros(T)
        H = np.zeros(T)
        nh = np.zeros(T)
        for t in range(T):
            Lon = L[t][on]            # G x K
            Loff = L[t][off]
            Hs = (Lon - Loff).mean(1)
            g = int(np.argmax(Hs))
            o, hv = parabolic_peak(Hs, g)
            f0[t] = grid[g] + 0.5 * o
            H[t] = hv
            prev = np.concatenate([[Loff[g, 0]], Loff[g, :-1]])
            c = Lon[g] - 0.5 * (Loff[g] + prev)
            nh[t] = float(np.sum(c >= 6.0))
        lvl = dbfs(self.Pl[:, band_slice(self.fl, 60.0, 4000.0)].sum(1))
        self._harm = (f0, H, nh, lvl)
        return self._harm


# ============================================================================ floor tracker
class FloorTracker:
    """Per-band background: follows quieter levels immediately, rises at most rise_db_per_s."""

    def __init__(self, rise_db_per_s: float):
        self.rise = rise_db_per_s
        self.v: Optional[np.ndarray] = None

    def update(self, level_db: np.ndarray, dt: float):
        lv = np.asarray(level_db, dtype=np.float64)
        if self.v is None:
            self.v = lv.copy()
            return
        ok = np.isfinite(lv)
        down = ok & (lv < self.v)
        self.v[down] = self.v[down] + 0.7 * (lv[down] - self.v[down])
        up = ok & ~down
        self.v[up] = np.minimum(lv[up], self.v[up] + self.rise * dt)


# ============================================================================ pass-by fit
def _passby_model(p, tt):
    t0, lr, lf, la, lpf, lg = p
    tau = np.where(tt < t0, np.exp(lr), np.exp(lf))
    return np.exp(lpf) + np.exp(la) / (1.0 + ((tt - t0) / tau) ** 2) ** np.exp(lg)


def fit_passby(t: np.ndarray, L: np.ndarray, floor_db: float):
    """Fit the pass-by model (in dB) to the level L(t) (seconds, dBFS).

    P(t) = P_floor + A / (1 + ((t - t0) / tau)^2)^gamma, with tau = tau_rise before t0 and
    tau_fall after it. gamma = 1 is pure spherical spreading. gamma > 1 means the tails fall
    faster, from excess ground attenuation and absorption at grazing angles and from
    directivity. P_floor is held within +-3 dB of the tracked floor, so the fit cannot trade
    the floor against the tails. Returns dict(t0, sigma_t0, tau_r, tau_f, gamma, snr_db,
    rms_db, ...) or None.
    """
    from scipy.optimize import least_squares

    m = np.isfinite(L)
    t, L = t[m], L[m]
    if len(t) < 12:
        return None
    ln10 = math.log(10.0) / 10.0
    Pf0 = math.exp(ln10 * floor_db)
    Ls = smooth_db(L, 5)
    ipk = int(np.nanargmax(Ls))
    Lpk = float(Ls[ipk])
    Ppk = math.exp(ln10 * Lpk)
    half = Lpk - 3.0
    j = ipk
    while j > 0 and Ls[j] > half:
        j -= 1
    wr = max(t[ipk] - t[j], 2.0)
    j = ipk
    while j < len(Ls) - 1 and Ls[j] > half:
        j += 1
    wf = max(t[j] - t[ipk], 2.0)
    A0 = max(Ppk - Pf0, Pf0 * 0.2)
    x0 = np.array([t[ipk], math.log(wr), math.log(wf), math.log(A0), math.log(Pf0), 0.0])
    lo = np.array([t[0], math.log(0.5), math.log(0.5), math.log(A0) - 7.0, math.log(Pf0) - 0.69, math.log(0.5)])
    hi = np.array([t[-1], math.log(900.0), math.log(900.0), math.log(A0) + 4.6, math.log(Pf0) + 0.69, math.log(6.0)])
    x0 = np.clip(x0, lo + 1e-9, hi - 1e-9)

    def res(p):
        return 10.0 * np.log10(_passby_model(p, t) + EPS) - L

    best = None
    for g0 in (0.0, math.log(3.0)):      # spherical spreading and a steep-tailed start
        x0[5] = g0
        x0[1:3] = np.log(np.array([wr, wf]) / (math.sqrt(2 ** (1 / math.exp(g0)) - 1) / 1.0))
        x0 = np.clip(x0, lo + 1e-9, hi - 1e-9)
        try:
            r = least_squares(res, x0, bounds=(lo, hi), loss="soft_l1", f_scale=1.5,
                              x_scale=np.array([5.0, 0.5, 0.5, 1.0, 0.3, 0.5]), max_nfev=600)
        except Exception as e:  # pragma: no cover
            log.debug("pass-by fit failed: %s", e)
            continue
        if best is None or r.cost < best.cost:
            best = r
    if best is None:
        return None
    r = best
    p = r.x
    rr = res(p)
    n, k = len(rr), len(p)
    # numeric Jacobian of the raw residuals -> covariance (Gauss-Newton)
    J = np.zeros((n, k))
    steps = np.array([0.05, 0.01, 0.01, 0.01, 0.01, 0.01])
    for i in range(k):
        dp = np.zeros(k)
        dp[i] = steps[i]
        J[:, i] = (res(p + dp) - res(p - dp)) / (2 * steps[i])
    s2 = float(np.sum(rr ** 2) / max(n - k, 1))
    try:
        cov = np.linalg.pinv(J.T @ J) * s2
        sig = float(math.sqrt(max(cov[0, 0], 0.0)))
    except Exception:  # pragma: no cover
        sig = float("nan")
    # residuals are correlated (smoothing, slow background changes): inflate by the AR(1) factor
    rho = float(np.clip(np.corrcoef(rr[:-1], rr[1:])[0, 1], 0.0, 0.9)) if n > 4 else 0.0
    sig *= math.sqrt((1 + rho) / (1 - rho))
    sig = math.sqrt(sig ** 2 + (BLOCK_S / math.sqrt(12)) ** 2)
    A = math.exp(p[3])
    Pf = math.exp(p[4])
    gam = math.exp(p[5])
    # half-power (-3 dB) half-widths of the fitted shape: tau * sqrt(2^(1/gamma) - 1)
    hw = math.sqrt(2 ** (1 / gam) - 1)
    return {"t0": float(p[0]), "sigma_t0": sig, "tau_r": float(math.exp(p[1])), "tau_f": float(math.exp(p[2])),
            "gamma": gam, "fwhm": float((math.exp(p[1]) + math.exp(p[2])) * hw),
            "peak_db": float(10 * math.log10(A + Pf)), "floor_db": float(10 * math.log10(Pf)),
            "snr_db": float(10 * math.log10((A + Pf) / Pf)), "rms_db": float(math.sqrt(np.mean(rr ** 2))),
            "ok": bool(r.success), "argmax_t": float(t[ipk]), "n": n, "rho": rho}


def fit_doppler(t: np.ndarray, f: np.ndarray):
    """Fit f(t) = fc - D tanh((t - tc)/w) to a tonal track. Returns dict or None."""
    from scipy.optimize import least_squares

    if len(t) < 8:
        return None
    fc0 = float(np.median(f))
    n3 = max(len(f) // 3, 2)
    D0 = 0.5 * (float(np.median(f[:n3])) - float(np.median(f[-n3:])))
    x0 = np.array([fc0, D0, float(np.median(t)), max((t[-1] - t[0]) / 4, 3.0)])
    lo = np.array([fc0 * 0.8, -0.3 * fc0, t[0], 1.0])
    hi = np.array([fc0 * 1.2, 0.3 * fc0, t[-1], max(t[-1] - t[0], 2.0) * 2])
    x0 = np.clip(x0, lo + 1e-6, hi - 1e-6)

    def res(p):
        return p[0] - p[1] * np.tanh((t - p[2]) / p[3]) - f

    try:
        r = least_squares(res, x0, bounds=(lo, hi), loss="soft_l1", f_scale=max(fc0 * 0.005, 0.5))
    except Exception:  # pragma: no cover
        return None
    rr = res(r.x)
    J = r.jac
    s2 = float(np.sum(rr ** 2) / max(len(t) - 4, 1))
    try:
        cov = np.linalg.pinv(J.T @ J) * s2
        sig_tc = float(math.sqrt(max(cov[2, 2], 0.0)))
    except Exception:  # pragma: no cover
        sig_tc = float("nan")
    fc, D, tc, w = (float(v) for v in r.x)
    return {"fc": fc, "D": D, "tc": tc, "w": w, "sigma_tc": sig_tc, "rms_hz": float(np.sqrt(np.mean(rr ** 2)))}


# ============================================================================ the analyzer
class AudioEventAnalyzer(Analyzer):
    name = "audio_events"
    wants_audio = True
    min_interval_s = 0.0   # every chunk: the detectors need a continuous history

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.p = {k: v for k, v in DEFAULTS.items()}
        self.p.update({k: v for k, v in (config or {}).items() if k != "_global"})
        self._maxlen = int(float(self.p["history_s"]) / BLOCK_S)
        self._hist: deque = deque(maxlen=self._maxlen)
        self._floor = FloorTracker(float(self.p["floor_rise_db_per_min"]) / 60.0)
        self._t_next: Optional[float] = None     # expected real start of next chunk
        self._reported: dict = {}                # variant -> [(t_start, t_end)] segments already evaluated
        self._emitted: list = []                 # [(t_start, t_end)] pass-by events reported
        self._imp_done: Optional[float] = None
        self._bell_done: Optional[float] = None
        self._bell_seq: list = []
        self._rain_run = 0
        self._last_emit: dict = {}
        self._voice_last_end: Optional[float] = None
        self._voice_episode = 0

    # ---------------------------------------------------------------- plumbing
    def _obs(self, kind, t_real, value, conf, chunk, cap_off, ctx, notes=""):
        loop = ctx.state.get("audio_loop_active") if ctx is not None else None
        if (loop and isinstance(loop, dict) and t_real <= float(loop.get("until", 0)) + 30.0
                and t_real >= float(loop.get("since", loop.get("until", 0))) - 60.0):
            value["loop_suspect"] = True
            conf = min(conf, 0.3)
        return Observation(kind=kind, ts=from_unix(t_real), value=value, analyzer=self.name,
                           confidence=round(float(conf), 3), audio_id=getattr(chunk, "id", None),
                           ts_capture=from_unix(t_real + cap_off), notes=notes)

    def _due(self, key, t, interval):
        last = self._last_emit.get(key)
        if last is None or t - last >= interval:
            self._last_emit[key] = t
            return True
        return False

    def _continuity(self, t0: float, dur: float) -> str:
        if self._t_next is None:
            return "start"
        d = t0 - self._t_next
        if abs(d) <= float(self.p["gap_tol_s"]):
            return "contiguous"
        if 0 < d <= float(self.p["gap_fill_max_s"]):
            return "gap"
        return "reset"

    def _ring_update(self, ctx, x, t0, cap_off, cont):
        ring_s = float(self.p["ring_s"])
        ring = ctx.state.get("audio_ring")
        x32 = x.astype(np.float32)
        if ring is None or cont in ("start", "reset", "gap") or ring.get("sr") != SR:
            ring = {"sr": SR, "data": x32, "t_end": t0 + len(x) / SR, "cap_off": cap_off}
        else:
            data = np.concatenate([ring["data"], x32])
            keep = int(ring_s * SR)
            if len(data) > keep:
                data = data[-keep:]
            ring = {"sr": SR, "data": data, "t_end": t0 + len(x) / SR, "cap_off": cap_off}
        ctx.state["audio_ring"] = ring
        return ring

    def _hist_array(self):
        if not self._hist:
            return np.zeros((0, N_COLS))
        return np.asarray(self._hist)

    # ---------------------------------------------------------------- main entry
    def on_audio(self, chunk, ctx: Context):
        x = prepare_samples(chunk.samples, chunk.sr)
        if x is None or len(x) < int(BLOCK_S * SR) * 2:
            return []
        t0 = to_unix(chunk.real_ts)
        cap_off = (chunk.capture_ts - chunk.real_ts).total_seconds() if chunk.capture_ts else 0.0
        dur = len(x) / SR
        cont = self._continuity(t0, dur)
        if cont == "reset" or cont == "start":
            if cont == "reset":
                log.info("audio_events: timeline discontinuity at %s -> history reset", iso(chunk.real_ts))
            self._hist.clear()
            self._imp_done = None
            self._bell_done = None
            self._rain_run = 0
        elif cont == "gap":
            n_fill = int(round((t0 - self._t_next) / BLOCK_S))
            last = np.asarray(self._hist[-1]) if self._hist else None
            for i in range(n_fill):
                row = np.full(N_COLS, np.nan)
                row[C_T] = self._t_next + i * BLOCK_S
                row[C_CAP] = cap_off
                if last is not None:
                    row[C_F0:C_FAIR + 1] = last[C_F0:C_FAIR + 1]
                    row[C_FMID] = last[C_FMID]
                self._hist.append(row)
            self._imp_done = None
            self._bell_done = None
        self._t_next = t0 + int(dur // BLOCK_S) * BLOCK_S
        ring = self._ring_update(ctx, x, t0, cap_off, cont)

        rms_db = float(dbfs(np.mean(x ** 2)))
        if rms_db < float(self.p["silence_dbfs"]):
            ctx.state["audio_silent"] = True     # muted / dropped audio: keep the timeline with NaN blocks
            last = np.asarray(self._hist[-1]) if self._hist else None
            for b in range(int(dur // BLOCK_S)):
                row = np.full(N_COLS, np.nan)
                row[C_T] = t0 + b * BLOCK_S
                row[C_CAP] = cap_off
                if last is not None:
                    row[C_F0:C_FAIR + 1] = last[C_F0:C_FAIR + 1]
                    row[C_FMID] = last[C_FMID]
                self._hist.append(row)
            return []
        ctx.state["audio_silent"] = False

        F = ChunkFeatures(x, t0)
        # floor before this chunk (detectors) and update after
        pct = float(self.p["floor_percentile"])
        blk_db = dbfs(F.block_bands)
        chunk_floor = np.nanpercentile(blk_db, pct, axis=0) if F.n_blocks else np.full(6, np.nan)
        floor_prev = self._floor.v.copy() if self._floor.v is not None else chunk_floor.copy()
        self._floor.update(chunk_floor, dur)
        floor_now = self._floor.v.copy()
        air_floor = float(dbfs(np.sum(10 ** ((floor_now[list(AIR_BANDS)] - 3.0103) / 10))))
        mid_floor = float(dbfs(np.sum(10 ** ((floor_now[list(MID_BANDS)] - 3.0103) / 10))))
        for b in range(F.n_blocks):
            row = np.full(N_COLS, np.nan)
            row[C_T] = F.block_t[b]
            row[C_CAP] = cap_off
            row[C_B0:C_B0 + 6] = F.block_bands[b]
            row[C_AIR] = dbfs(np.nansum(F.block_bands[b, list(AIR_BANDS)]))
            row[C_ROUGH] = F.block_rough[b]
            row[C_AM] = F.block_am[b]
            row[C_AMF] = F.block_amf[b]
            row[C_TONEF] = F.block_tone_f[b]
            row[C_TONEP] = F.block_tone_p[b]
            row[C_CLACK] = F.clack
            row[C_F0:C_F0 + 6] = floor_now
            row[C_FAIR] = air_floor
            row[C_FLAT] = F.block_flat[b]
            row[C_MID] = dbfs(np.nansum(F.block_bands[b, list(MID_BANDS)]))
            row[C_FMID] = mid_floor
            row[C_RMID] = F.block_rough_mid[b]
            self._hist.append(row)

        out = []
        detectors = (
            ("passby", lambda: self._passby(chunk, ctx)),
            ("wind", lambda: self._wind(F, floor_prev, chunk, cap_off, ctx)),
            ("rain", lambda: self._rain(F, floor_prev, chunk, cap_off, ctx)),
            ("harmonic", lambda: self._harmonic_sources(F, floor_prev, chunk, cap_off, ctx)),
            ("impulses", lambda: self._impulses(ring, chunk, ctx)),
            ("bells", lambda: self._bells(ring, floor_prev, chunk, ctx)),
        )
        for name, fn in detectors:
            try:
                out += fn() or []
            except Exception as e:  # one broken detector must not kill the others
                log.exception("audio_events: %s detector failed: %s", name, e)
        return out

    # ================================================================ pass-by events
    def _passby(self, chunk, ctx):
        """Level events in the history, per detection variant ('air' 50-1500 Hz, 'mid' 150-1500 Hz,
        which stays usable when wind noise fills < 150 Hz). Each variant evaluates a segment once.
        An event emitted by one variant blocks overlapping emissions by the other."""
        H = self._hist_array()
        n = len(H)
        if n < 30:
            return []
        p = self.p
        t = H[:, C_T]
        settle = int(float(p["evt_settle_s"]) / BLOCK_S)
        full = n >= self._maxlen
        out = []
        for var in VARIANTS:
            vname, c_lvl, c_floor = var[0], var[1], var[2]
            L1 = smooth_db(H[:, c_lvl], 2)
            E = smooth_db(H[:, c_lvl], 4) - H[:, c_floor]
            segs = hysteresis_segments(E, float(p["evt_on_db"]), float(p["evt_off_db"]),
                                       int(float(p["evt_merge_gap_s"]) / BLOCK_S))
            done = self._reported.setdefault(vname, [])
            for i0, i1 in segs:
                if i1 > n - settle:
                    continue                      # still open (or not settled)
                if i0 == 0 and full:
                    continue                      # started before the history: duration unknown
                ts0, ts1 = float(t[i0]), float(t[i1 - 1] + BLOCK_S)
                if any(ts0 < b and ts1 > a for a, b in done):
                    continue
                done.append((ts0, ts1))
                if any(ts0 < b and ts1 > a for a, b in self._emitted):
                    continue
                try:
                    o = self._classify_passby(H, L1, E, i0, i1, var, chunk, ctx)
                except Exception as e:  # pragma: no cover
                    log.exception("pass-by classification failed: %s", e)
                    o = None
                if o is not None:
                    o.value.setdefault("features", {})["variant"] = vname
                    self._emitted.append((ts0, ts1))
                    out.append(o)
        tmin = float(t[0]) - 60.0
        for k in list(self._reported):
            self._reported[k] = [r for r in self._reported[k] if r[1] > tmin]
        self._emitted = [r for r in self._emitted if r[1] > tmin]
        return out

    def _classify_passby(self, H, L1, E, i0, i1, var, chunk, ctx):
        p = self.p
        vname, c_lvl, c_floor, c_rough, src_bands, ref_bands = var
        n = len(H)
        t = H[:, C_T]
        pad = int(float(p["evt_pad_s"]) / BLOCK_S)
        a, b = max(0, i0 - pad), min(n, i1 + pad)
        tref = float(t[i0])
        tt = t[a:b] - tref
        floor_db = float(np.nanmedian(H[i0:i1, c_floor]))
        fit = fit_passby(tt, L1[a:b], floor_db)
        dur = (i1 - i0) * BLOCK_S
        seg_E = E[i0:i1]
        snr_seg = float(np.nanmax(seg_E))
        if fit is None:
            return None
        t0 = tref + fit["t0"]
        fwhm = fit["fwhm"]
        # excess spectrum around the peak
        k0 = int(np.clip(np.searchsorted(t, t0), 0, n - 1))
        hwf = math.sqrt(2 ** (1 / fit["gamma"]) - 1)
        hw_r, hw_f = fit["tau_r"] * hwf, fit["tau_f"] * hwf      # -3 dB half-widths
        half = max(int(min(hw_r, hw_f) / BLOCK_S), 2)
        sel = slice(max(i0, k0 - half), min(i1, k0 + half + 1))
        if not np.any(np.isfinite(H[sel, C_B0])):
            return None
        Eb = np.nanmean(H[sel, C_B0:C_B0 + 6], axis=0)
        flat_pk = float(np.nanmedian(H[sel, C_FLAT]))
        Fb = 10 ** ((np.nanmedian(H[i0:i1, C_F0:C_F0 + 6], axis=0) - 3.0103) / 10)
        exc = np.clip(Eb - Fb, 0, None)
        ref = list(ref_bands)
        tot = float(np.sum(exc[ref])) + EPS
        frac = np.zeros(6)
        frac[ref] = exc[ref] / tot
        air_frac = float(np.sum(frac[list(src_bands)]))
        lf_frac = float(frac[0])
        hf_frac = float(frac[4] + frac[5])
        mid_frac = float(frac[3] + frac[4])
        rough = float(np.nanmedian(H[i0:i1, c_rough]))
        am = float(np.nanmedian(H[i0:i1, C_AM]))
        amf = float(np.nanmedian(H[i0:i1, C_AMF]))
        clack = float(np.nanmedian(H[i0:i1, C_CLACK]))
        plateau_s = float(np.sum(seg_E >= snr_seg - 4.0)) * BLOCK_S
        # both flanks observed?
        flanks = (fit["t0"] - (t[i0] - tref) >= 0.8 * hw_r) and ((t[i1 - 1] - tref) - fit["t0"] >= 0.8 * hw_f)
        helicopter = am >= 0.45 and 8.0 <= amf <= 30.0
        snr = max(fit["snr_db"], 0.0)
        feats = {"fwhm_s": round(fwhm, 1), "tau_rise_s": round(fit["tau_r"], 1), "tau_fall_s": round(fit["tau_f"], 1),
                 "gamma": round(fit["gamma"], 2),
                 "fit_rms_db": round(fit["rms_db"], 2), "src_band_frac": round(air_frac, 3), "lf_frac": round(lf_frac, 3),
                 "hf_frac": round(hf_frac, 3), "roughness_db": round(rough, 2), "am_periodicity": round(am, 2),
                 "am_hz": None if not np.isfinite(amf) else round(amf, 1), "clack": round(clack, 2),
                 "plateau_s": plateau_s, "flatness": round(flat_pk, 3), "band_excess_db": [round(float(v), 1) for v in dbfs(exc)],
                 "segment": [iso(from_unix(t[i0])), iso(from_unix(t[i1 - 1] + BLOCK_S))], "flanks_seen": bool(flanks)}
        cap_off = float(np.nanmedian(H[i0:i1, C_CAP]))
        if max(snr, snr_seg) < float(p["evt_min_snr_db"]):
            return None
        if flat_pk < float(p["evt_min_flatness"]):
            log.debug("level event %s is tonal (flatness %.3f): not a pass-by", iso(from_unix(t0)), flat_pk)
            return None

        # ---------- train: a line source (plateau) with periodic wheel/joint clacks; no point-source fit needed
        if (dur >= float(p["train_min_dur_s"]) and plateau_s >= float(p["train_plateau_s"])
                and clack >= float(p["train_min_clack"]) and lf_frac <= 0.5):
            top = np.nonzero(seg_E >= snr_seg - 4.0)[0]
            tc = float(t[i0 + int(np.median(top))]) + BLOCK_S / 2
            conf = min(0.5, 0.3 + 0.1 * min((clack - 0.3) / 0.3, 1.0) + 0.05 * min(snr_seg / 10.0, 1.0))
            v = {"snr_db": round(snr_seg, 1), "duration_s": dur, "peak_ts": iso(from_unix(tc)), "plateau_s": plateau_s,
                 "features": feats}
            return self._obs("audio_train", tc, v, conf, chunk, cap_off, ctx)

        if not fit["ok"]:
            return None
        asym = max(hw_r, hw_f) / max(min(hw_r, hw_f), 1e-3)
        feats["asymmetry"] = round(asym, 2)
        if asym > float(p["evt_max_asym"]):
            log.debug("level event %s too asymmetric (%.1f): struck/switched source, not a pass-by", iso(from_unix(t0)), asym)
            return None

        af = p["aircraft_fwhm_s"]
        vf = p["vehicle_fwhm_s"]
        is_air = (af[0] <= fwhm <= af[1] and float(p["aircraft_min_dur_s"]) <= dur <= float(p["aircraft_max_dur_s"])
                  and air_frac >= float(p["aircraft_min_air_frac"]) and lf_frac <= 0.5
                  and (rough <= float(p["aircraft_max_rough_db"]) or helicopter)
                  and fit["rms_db"] <= float(p["aircraft_max_fit_rms_db"]) and flanks)
        is_veh = (vf[0] <= fwhm <= vf[1] and float(p["vehicle_min_dur_s"]) <= dur <= float(p["vehicle_max_dur_s"])
                  and mid_frac >= float(p["vehicle_min_mid_frac"]) and lf_frac <= 0.5
                  and rough <= float(p["vehicle_max_rough_db"]) and fit["rms_db"] <= 4.0)
        if is_air and is_veh:
            if hf_frac >= 0.15:
                is_air = False
            else:
                is_veh = False

        if is_air:
            dop = self._doppler(H, i0, i1, t0, tref)
            type_hint = "helicopter?" if helicopter else ("tonal (propeller/fan?)" if dop else "broadband (jet?)")
            conf = 0.35 + 0.15 * min(snr / 15.0, 1.0) + (0.1 if dop and dop.get("consistent") else 0.0) \
                - (0.1 if fit["sigma_t0"] > 8 else 0.0)
            conf = float(np.clip(conf, 0.2, 0.75))
            hint = None
            if dop:
                hint = (f"tone {dop['f_start_hz']:.0f}->{dop['f_end_hz']:.0f} Hz"
                        + (f", v>={dop['v_min_ms']:.0f} m/s" if dop.get("consistent") else ", not Doppler-like"))
            v = {"peak_ts": iso(from_unix(t0)), "peak_sigma_s": round(fit["sigma_t0"], 2),
                 "peak_ts_argmax": iso(from_unix(tref + fit["argmax_t"])),
                 "snr_db": round(snr, 1), "duration_s": dur, "peak_dbfs": round(fit["peak_db"], 1),
                 "doppler_hint": hint, "doppler": dop, "type_hint": type_hint,
                 "tau_over_distance_hint": "tau = d / v (slant distance / ground speed)", "features": feats}
            return self._obs("audio_aircraft", t0, v, conf, chunk, cap_off, ctx)
        if is_veh:
            conf = float(np.clip(0.3 + 0.15 * min(snr / 15.0, 1.0), 0.2, 0.5))
            v = {"snr_db": round(snr, 1), "peak_ts": iso(from_unix(t0)), "peak_sigma_s": round(fit["sigma_t0"], 2),
                 "duration_s": dur, "features": feats}
            return self._obs("audio_vehicle", t0, v, conf, chunk, cap_off, ctx)
        log.debug("unclassified level event %s (fwhm %.1f s, dur %.1f s, snr %.1f dB, air %.2f, rough %.1f)",
                  iso(from_unix(t0)), fwhm, dur, snr, air_frac, rough)
        return None

    def _doppler(self, H, i0, i1, t0, tref):
        f = H[i0:i1, C_TONEF]
        pr = H[i0:i1, C_TONEP]
        tt = H[i0:i1, C_T]
        ok = np.isfinite(f) & (pr >= 8.0) & (f >= 60.0)
        if ok.sum() < 10:
            return None
        fm = float(np.median(f[ok]))
        ok &= np.abs(f - fm) <= 0.12 * fm
        if ok.sum() < 10:
            return None
        fit = fit_doppler(tt[ok] - tref, f[ok])
        if fit is None:
            return None
        fs, fe = fit["fc"] + fit["D"], fit["fc"] - fit["D"]
        beta = fit["D"] / fit["fc"]
        consistent = bool(beta > 0.002 and fit["rms_hz"] < 0.02 * fit["fc"]
                          and abs(tref + fit["tc"] - t0) < max(3 * fit["w"], 20.0))
        return {"f_start_hz": round(fs, 1), "f_end_hz": round(fe, 1), "drift_hz": round(fe - fs, 1),
                "v_over_c_min": round(beta, 4), "v_min_ms": round(beta * SOUND_SPEED, 1),
                "t_mid_ts": iso(from_unix(tref + fit["tc"])), "t_mid_sigma_s": round(fit["sigma_tc"], 2),
                "width_s": round(fit["w"], 1), "rms_hz": round(fit["rms_hz"], 2), "n_blocks": int(ok.sum()),
                "consistent": consistent}

    # ================================================================ wind
    def _wind(self, F: ChunkFeatures, floor_prev, chunk, cap_off, ctx):
        p = self.p
        sl = band_slice(F.fl, 20.0, 150.0)
        lf = F.Pl[:, sl].sum(1)
        tot = F.Pl[:, band_slice(F.fl, 20.0, 8000.0)].sum(1) + EPS
        Llf = dbfs(lf)
        w = 16
        stds = []
        for i in range(0, len(Llf) - w + 1, w // 2):
            seg = Llf[i:i + w]
            xx = np.arange(w)
            stds.append(float(np.std(seg - np.polyval(np.polyfit(xx, seg, 1), xx))))
        if not stds:
            return []
        rough = float(np.median(stds))
        lf_floor = float(dbfs(10 ** ((floor_prev[0] - 3.0103) / 10) + 10 ** ((floor_prev[1] - 3.0103) / 10)))
        level = float(dbfs(np.mean(lf)))
        excess = float(np.percentile(Llf, 90)) - lf_floor
        lf_frac = float(np.sum(lf) / np.sum(tot))
        present = (rough >= float(p["wind_min_rough_db"]) and lf_frac >= float(p["wind_min_lf_frac"])
                   and excess >= float(p["wind_min_excess_db"]))
        if not present:
            return []
        t0 = F.t0
        if not self._due("wind", t0, float(p["wind_emit_interval_s"])):
            return []
        conf = float(np.clip(0.3 + 0.05 * (rough - 2.5) + 0.1 * (lf_frac - 0.5) / 0.5, 0.25, 0.6))
        v = {"level_db": round(level, 1), "snr_db": round(excess, 1), "gust_db": round(float(np.percentile(Llf, 95) - np.percentile(Llf, 10)), 1),
             "roughness_db": round(rough, 2), "lf_frac": round(lf_frac, 3), "excess_db": round(excess, 1)}
        return [self._obs("audio_wind", t0, v, conf, chunk, cap_off, ctx)]

    # ================================================================ rain
    def _rain(self, F: ChunkFeatures, floor_prev, chunk, cap_off, ctx):
        p = self.p
        sos = _sos_highpass(2000.0)
        hp = signal.sosfilt(sos, F.x)
        fl = 32  # 2 ms
        k = len(hp) // fl
        if k < 1000:
            return []
        e = dbfs((hp[:k * fl] ** 2).reshape(k, fl).mean(1))
        bg = median_filter(e, size=101, mode="nearest")
        pk = (e - bg >= float(p["rain_impulse_db"])) & (e >= maximum_filter1d(e, 5, mode="nearest")) & (e > -90.0)
        rate = float(pk.sum()) / F.dur
        per_s = int(1.0 / 0.002)
        n_sec = k // per_s
        if n_sec < 2:
            return []
        counts = pk[:n_sec * per_s].reshape(n_sec, per_s).sum(1)
        continuity = float(np.mean(counts >= 0.5 * float(p["rain_min_rate_hz"])))
        hf = F.Ps[:, band_slice(F.fs, 2000.0, 7000.0)]
        flat = float(np.median(spectral_flatness(hf, axis=1)))
        hf_level = float(dbfs(np.mean(hf.sum(1))))
        hf_floor = float(dbfs(10 ** ((floor_prev[4] - 3.0103) / 10) + 10 ** ((floor_prev[5] - 3.0103) / 10)))
        raw = rate >= float(p["rain_min_rate_hz"]) and continuity >= float(p["rain_min_continuity"]) \
            and flat >= float(p["rain_min_flatness"])
        if not raw:
            if self._rain_run >= int(p["rain_confirm_chunks"]):
                self._last_emit.pop("rain", None)
            self._rain_run = 0
            return []
        self._rain_run += 1
        if self._rain_run < int(p["rain_confirm_chunks"]):
            return []
        if not self._due("rain", F.t0, float(p["rain_emit_interval_s"])):
            return []
        excess = max(hf_level - hf_floor, 0.0)
        # 5 impacts/s -> 0, 500/s -> 0.6; +0.4 for a 2-8 kHz level 20 dB above its floor
        inten = float(np.clip(0.6 * np.log10(max(rate, 5.0) / 5.0) / 2.0 + 0.4 * min(excess / 20.0, 1.0), 0.0, 1.0))
        label = "light" if inten < 0.4 else ("moderate" if inten < 0.7 else "heavy")
        conf = float(np.clip(0.3 + 0.1 * min(rate / 50.0, 1.0) + 0.1 * (continuity - 0.7) / 0.3, 0.25, 0.55))
        v = {"intensity": round(inten, 3), "intensity_label": label, "impact_rate_hz": round(rate, 1),
             "continuity": round(continuity, 2), "hf_flatness": round(flat, 3), "hf_level_dbfs": round(hf_level, 1),
             "snr_db": round(excess, 1), "chunks_confirmed": self._rain_run}
        return [self._obs("audio_rain", F.t0, v, conf, chunk, cap_off, ctx)]

    # ================================================================ harmonic sources
    def _harmonic_sources(self, F: ChunkFeatures, floor_prev, chunk, cap_off, ctx):
        p = self.p
        f0, Hs, nh, lvl = F.harmonic()
        T = len(f0)
        if T < 8:
            return []
        harm = (Hs >= float(p["harm_min_db"])) & (nh >= float(p["harm_min_n"]))
        # persistence: runs of >= 3 harmonic frames with continuous f0
        stable = np.zeros(T, bool)
        i = 0
        while i < T:
            if not harm[i]:
                i += 1
                continue
            j = i + 1
            while j < T and harm[j] and abs(math.log2(f0[j] / f0[j - 1])) <= 0.06:
                j += 1
            if j - i >= 3:
                stable[i:j] = True
            i = j
        out = []
        # band floor 60-4000 Hz approx from bands 1..4
        fl_lin = np.sum(10 ** ((floor_prev[1:5] - 3.0103) / 10))
        floor_db = float(dbfs(fl_lin))
        # speech-band envelope modulation
        env = dbfs(F.Ps[:, band_slice(F.fs, 300.0, 3400.0)].sum(1))
        env_s = uniform_filter1d(env, 3, mode="nearest")
        depth = float(np.std(env_s))
        fps = SR / HOP_SHORT
        m = env_s - np.mean(env_s)
        spec = np.abs(np.fft.rfft(m * np.hanning(len(m)))) ** 2
        fm = np.fft.rfftfreq(len(m), 1 / fps)
        tot = float(spec[(fm >= 0.5) & (fm <= 20.0)].sum()) + EPS
        mod_frac = float(spec[(fm >= 2.0) & (fm <= 8.0)].sum()) / tot

        # ---------- chainsaw / machine
        cf = p["chainsaw_f0_hz"]
        cs = stable & (f0 >= cf[0]) & (f0 <= cf[1])
        mf = p["machine_f0_hz"]
        ms = stable & (f0 >= mf[0]) & (f0 < mf[1])
        claimed = False
        for kind_sel, typ in ((cs, "chainsaw"), (ms, "machine")):
            frac = float(np.mean(kind_sel))
            if frac < (float(p["chainsaw_min_frac"]) if typ == "chainsaw" else float(p["machine_min_frac"])):
                continue
            idx = np.nonzero(kind_sel)[0]
            d = np.abs(np.diff(np.log2(f0[idx])))
            d = d[np.diff(idx) == 1]
            jitter = float(np.median(d)) if len(d) else 1.0
            nharm = float(np.median(nh[idx]))
            snr = float(np.median(lvl[idx])) - floor_db
            ok = (jitter <= float(p["chainsaw_max_jitter_oct"]) and nharm >= float(p["chainsaw_min_nharm"])
                  and snr >= (float(p["chainsaw_min_snr_db"]) if typ == "chainsaw" else float(p["machine_min_snr_db"]))
                  and (depth <= float(p["chainsaw_max_depth_db"]) or mod_frac < float(p["voice_min_mod_frac"])))
            if not ok:
                continue
            claimed = True                   # an engine: never also report it as voice
            interval = float(p["chainsaw_emit_interval_s"] if typ == "chainsaw" else p["machine_emit_interval_s"])
            if not self._due(typ, F.t0, interval):
                break
            f0m = float(np.median(f0[idx]))
            conf = (0.35 + 0.1 * min((snr - 12) / 12, 1) + 0.1 * min((nharm - 5) / 3, 1)) if typ == "chainsaw" else 0.3
            v = {"snr_db": round(snr, 1), "type": typ, "f0_hz": round(f0m, 1),
                 "f0_range_hz": [round(float(np.min(f0[idx])), 1), round(float(np.max(f0[idx])), 1)],
                 "rpm_est": round(f0m * 60.0) if typ == "chainsaw" else None,
                 "n_harmonics": nharm, "harmonic_db": round(float(np.median(Hs[idx])), 1),
                 "f0_jitter_oct": round(jitter, 4), "frac": round(frac, 2), "mod_depth_db": round(depth, 1),
                 "mod_frac_2_8hz": round(mod_frac, 2)}
            out.append(self._obs("audio_chainsaw", F.t0 + float(F.tl[idx[0]]), v,
                                 float(np.clip(conf, 0.2, 0.6)), chunk, cap_off, ctx))
            break
        if claimed:
            return out

        # ---------- voice
        vf = p["voice_f0_hz"]
        vs = stable & (f0 >= vf[0]) & (f0 <= vf[1])
        vfrac = float(np.mean(vs))
        if vfrac < float(p["voice_min_voiced_frac"]):
            return out
        idx = np.nonzero(vs)[0]
        lf0 = np.log2(f0[idx])
        f0_std = float(np.std(lf0))
        snr = float(np.median(lvl[idx])) - floor_db
        if not (depth >= float(p["voice_min_depth_db"]) and mod_frac >= float(p["voice_min_mod_frac"])
                and snr >= float(p["voice_min_snr_db"]) and f0_std >= float(p["voice_min_f0_std_oct"])):
            return out
        # voiced segments (merge gaps <= 0.3 s)
        half = N_LONG / 2 / SR
        segs = []
        for i in idx:
            a, b = float(F.tl[i]) - half * 0.5, float(F.tl[i]) + half * 0.5
            if segs and a - segs[-1][1] <= 0.3:
                segs[-1][1] = b
            else:
                segs.append([a, b])
        segs = [[max(a, 0.0), min(b, F.dur)] for a, b in segs if b - a >= 0.2]
        if not segs:
            return out
        onsets = []
        prev_end = self._voice_last_end
        for a, b in segs:
            ta = F.t0 + a
            if prev_end is None or ta - prev_end >= 0.5:
                onsets.append(iso(from_unix(ta)))
            prev_end = F.t0 + b
        new_episode = self._voice_last_end is None or F.t0 + segs[0][0] - self._voice_last_end > 5.0
        self._voice_last_end = prev_end
        ctx.state["audio_voice_active_until"] = prev_end
        if new_episode:
            self._voice_episode += 1
            self._last_emit.pop("voice", None)
        if not self._due("voice", F.t0, float(p["voice_emit_interval_s"])) and not onsets:
            return out
        f0m = float(2 ** np.median(lf0))
        hint = "male" if f0m < 150 else ("female" if f0m > 175 else "unknown")
        conf = float(np.clip(0.3 + 0.1 * min((snr - 6) / 12, 1) + 0.1 * min((mod_frac - 0.3) / 0.3, 1), 0.2, 0.55))
        v = {"snr_db": round(snr, 1), "speaker_hint": hint, "f0_median_hz": round(f0m, 1),
             "f0_std_oct": round(f0_std, 3), "voiced_frac": round(vfrac, 2), "mod_frac_2_8hz": round(mod_frac, 2),
             "mod_depth_db": round(depth, 1), "segments": [[round(a, 2), round(b, 2)] for a, b in segs],
             "onsets_ts": onsets, "episode": self._voice_episode}
        out.append(self._obs("audio_voice", F.t0 + segs[0][0], v, conf, chunk, cap_off, ctx))
        return out

    # ================================================================ impulses / gunshots
    def _impulses(self, ring, chunk, ctx):
        p = self.p
        data = ring["data"]
        t_end = float(ring["t_end"])
        t_start = t_end - len(data) / SR
        pre, post = float(p["imp_pre_s"]), float(p["imp_post_s"])
        r0 = self._imp_done if self._imp_done is not None else t_start + pre
        r0 = max(r0, t_start + pre)
        r1 = t_end - post
        if r1 - r0 < 0.05:
            return []
        self._imp_done = r1
        w0 = r0 - pre
        i0 = int(round((w0 - t_start) * SR))
        x = data[max(i0, 0):].astype(np.float64)
        tw0 = t_start + max(i0, 0) / SR
        hp = signal.sosfilt(_sos_highpass(150.0), x)
        fl = 32
        k = len(hp) // fl
        if k < 600:
            return []
        e = dbfs((hp[:k * fl] ** 2).reshape(k, fl).mean(1))
        bg = median_filter(e, size=501, mode="nearest")
        ft = tw0 + (np.arange(k) + 0.5) * fl / SR
        cand = np.nonzero((e - bg >= float(p["gun_min_db"])) & (e >= maximum_filter1d(e, 51, mode="nearest"))
                          & (ft >= r0) & (ft < r1))[0]
        out = []
        taken: list = []
        es = uniform_filter1d(e, 5, mode="nearest")
        cap_off = float(ring.get("cap_off", 0.0))
        for c in cand:
            tc = float(ft[c])
            if any(abs(tc - a) < 0.25 or (0 < tc - a < 3.0 and any(abs(tc - a - d) < 0.05 for d in ech))
                   for a, ech in taken):
                continue
            peak = float(e[c])
            pre_seg = e[max(c - 15, 0):max(c - 1, 1)]           # 30 ms before the loudest frame
            if len(pre_seg) == 0 or peak - float(np.min(pre_seg)) < float(p["gun_min_rise_db"]):
                continue
            j = c
            lim = min(k, c + int(2.5 / 0.002))
            while j < lim and es[j] > peak - 20.0:
                j += 1
            decay = (j - c) * 0.002
            dmin, dmax = p["gun_decay_s"]
            if j >= lim or decay < float(dmin) or decay > float(dmax):
                continue
            # broadband check: 64 ms spectrum at the impulse vs 1 s of background before it
            s0 = c * fl - 64
            seg = hp[max(s0, 0):max(s0, 0) + 1024]
            if len(seg) < 1024:
                continue
            Pi, _, fr = stft_power(seg, SR, 1024, 1024, center=False)
            b0 = max(s0 - SR, 0)
            bgx = hp[b0:max(s0, b0 + 1024)]
            Pb, _, _ = stft_power(bgx, SR, 1024, 512, center=False)
            Pb = np.median(Pb, 0)
            Pi = Pi[0]
            lo_ex = float(dbfs(Pi[band_slice(fr, 200, 1000)].sum()) - dbfs(Pb[band_slice(fr, 200, 1000)].sum()))
            hi_ex = float(dbfs(Pi[band_slice(fr, 1000, 5000)].sum()) - dbfs(Pb[band_slice(fr, 1000, 5000)].sum()))
            flat = float(spectral_flatness(Pi[band_slice(fr, 200, 5000)]))
            if lo_ex < float(p["gun_lo_band_db"]) or hi_ex < float(p["gun_hi_band_db"]) or flat < float(p["gun_min_flatness"]):
                continue
            # echoes: sharp peaks after the direct sound, above the local decay trend
            echoes = []
            a = c + int(0.08 / 0.002)
            b = min(k, c + int(3.0 / 0.002))
            if b - a > 20:
                tail = e[a:b]
                trend = median_filter(tail, size=101, mode="nearest")
                lm = tail >= maximum_filter1d(tail, 51, mode="nearest")
                prom = tail - trend
                cands = np.nonzero(lm & (prom >= 6.0) & (tail - bg[a:b] >= 10.0))[0]
                for q in cands:
                    g = a + q
                    if e[g] - float(np.min(e[max(g - 15, 0):g])) < 6.0:
                        continue
                    echoes.append((float(prom[q]), (g - c) * 0.002, float(e[g] - peak)))
                echoes.sort(reverse=True)
                echoes = sorted(echoes[:3], key=lambda z: z[1])
            clip_seg = x[max(c * fl - 80, 0):c * fl + 112]
            clipped = bool(len(clip_seg) and np.max(np.abs(clip_seg)) >= 0.98)
            conf = 0.3 + (0.1 if echoes else 0.0) + (0.05 if 0.1 <= decay <= 1.2 else 0.0) \
                + 0.05 * min((peak - float(bg[c]) - 25) / 15, 1.0)
            if ctx.state.get("audio_voice_active_until", 0) > tc:
                conf -= 0.1
            v = {"peak_db": round(peak, 1), "snr_db": round(peak - float(bg[c]), 1), "decay20_s": round(float(decay), 3),
                 "lo_band_excess_db": round(lo_ex, 1), "hi_band_excess_db": round(hi_ex, 1),
                 "flatness": round(flat, 3), "clipped": clipped,
                 "echoes": [{"delay_s": round(float(d), 3), "rel_db": round(float(r), 1),
                             "reflector_m": int(round(SOUND_SPEED * d / 2))}
                            for _, d, r in echoes],
                 "note": "tap/clap near the microphone can look identical"}
            taken.append((tc, [d for _, d, _ in echoes]))
            out.append(self._obs("audio_gunshot", tc, v, float(np.clip(conf, 0.2, 0.55)), chunk, cap_off, ctx))
        return out

    # ================================================================ bells
    def _bells(self, ring, floor_prev, chunk, ctx):
        p = self.p
        data = ring["data"]
        t_end = float(ring["t_end"])
        t_start = t_end - len(data) / SR
        look = float(p["bell_min_dur_s"]) + 0.7
        r0 = self._bell_done if self._bell_done is not None else t_start
        r0 = max(r0, t_start)
        r1 = t_end - look
        out = []
        if r1 - r0 >= 0.2:
            self._bell_done = r1
            w0 = max(r0 - 0.6, t_start)
            i0 = int(round((w0 - t_start) * SR))
            x = data[i0:].astype(np.float64)
            strikes = find_bell_strikes(x, w0, fmax=float(p["bell_fmax_hz"]), prom_db=float(p["bell_min_prom_db"]),
                                        min_dur_s=float(p["bell_min_dur_s"]), min_partials=int(p["bell_min_partials"]))
            for s in strikes:
                if r0 <= s["t"] < r1:
                    self._bell_seq.append(s)
        # close a sequence after a quiet gap
        if self._bell_seq and t_end - self._bell_seq[-1]["t"] > float(p["bell_seq_gap_s"]) + look:
            seq, self._bell_seq = self._bell_seq, []
            if len(seq) >= int(p["bell_min_strikes"]):
                out.append(self._bell_obs(seq, ring, chunk, ctx))
        return out

    def _bell_obs(self, seq, ring, chunk, ctx):
        t_first = seq[0]["t"]
        n = len(seq)
        best = max(seq, key=lambda s: s["level_db"])
        intervals = np.diff([s["t"] for s in seq])
        dt_first = from_unix(t_first)
        local = dt_first + oslo_offset(dt_first)
        # nearest full hour (local) and the expected clock-strike count
        lh = local.replace(minute=0, second=0, microsecond=0)
        if local - lh > timedelta(minutes=30):
            lh = lh + timedelta(hours=1)
        off_s = (local - lh).total_seconds()
        hour12 = lh.hour % 12 or 12
        clock = {"nearest_local_hour": lh.strftime("%H:00"), "offset_s": round(off_s, 1),
                 "expected_strikes": hour12, "n_strikes": n,
                 "matches": bool(abs(off_s) <= 120 and n in (hour12, hour12 + 1))}
        conf = float(np.clip(0.3 + 0.05 * min(n - 2, 4) + (0.1 if clock["matches"] else 0.0), 0.25, 0.6))
        v = {"snr_db": round(best["snr_db"], 1), "n_strikes": n,
             "strike_interval_s": round(float(np.median(intervals)), 2) if len(intervals) else None,
             "partials_hz": best["partials_hz"], "decay_db_s": best["decay_db_s"],
             "inharmonicity": best["inharmonicity"], "duration_s": round(seq[-1]["t"] - t_first, 1),
             "strike_ts": [iso(from_unix(s["t"])) for s in seq[:24]], "clock_hint": clock}
        return self._obs("audio_bells", t_first, v, conf, chunk, float(ring.get("cap_off", 0.0)), ctx)


_SOS: dict = {}


def _sos_highpass(fc: float):
    s = _SOS.get(fc)
    if s is None:
        s = _SOS[fc] = signal.butter(4, fc, btype="highpass", fs=SR, output="sos")
    return s


# ============================================================================ bell partials
def find_bell_strikes(x: np.ndarray, t0: float, fmax=4000.0, prom_db=12.0, min_dur_s=0.8, min_partials=3):
    """Struck, decaying, inharmonic partial groups in x (16 kHz). Returns [{t, partials_hz, ...}]."""
    P, tl, fl = stft_power(x, SR, N_LONG, HOP_LONG)
    if P.shape[0] < 10:
        return []
    L = 10 * np.log10(P + EPS)
    sl = band_slice(fl, 150.0, fmax)
    Ls = L[:, sl]
    med = local_background_db(Ls, 31, axis=1)
    prom = Ls - med
    lm = Ls >= maximum_filter1d(Ls, 5, axis=1, mode="nearest")
    pk = lm & (prom >= prom_db)
    fps = SR / HOP_LONG
    # tracking
    active: list = []
    done: list = []
    for t in range(Ls.shape[0]):
        bins = np.nonzero(pk[t])[0]
        used = set()
        still = []
        for tr in active:
            lb = tr["bins"][-1]
            best, bl = None, -1e9
            for b in bins:
                if b in used or abs(int(b) - lb) > 1:
                    continue
                if Ls[t, b] > bl:
                    best, bl = int(b), float(Ls[t, b])
            if best is None:
                tr["miss"] += 1
                if tr["miss"] > 2:
                    done.append(tr)
                else:
                    still.append(tr)
                continue
            used.add(best)
            if bl - tr["lv"][-1] >= 6.0 and len(tr["lv"]) >= 3:   # re-strike: split
                done.append(tr)
                still.append({"t0": t, "bins": [best], "lv": [bl], "tt": [t], "miss": 0})
                continue
            tr["bins"].append(best)
            tr["lv"].append(bl)
            tr["tt"].append(t)
            tr["miss"] = 0
            still.append(tr)
        for b in bins:
            if int(b) not in used:
                still.append({"t0": t, "bins": [int(b)], "lv": [float(Ls[t, b])], "tt": [t], "miss": 0})
        active = still
    done += active
    parts = []
    for tr in done:
        n = len(tr["lv"])
        if n / fps < min_dur_s:
            continue
        lv = np.asarray(tr["lv"])
        tt = np.asarray(tr["tt"]) / fps
        imax = int(np.argmax(lv))
        if imax > 4:
            continue                      # not struck: the maximum is not within 256 ms (one window) of the start
        yy, xx = lv[imax:], tt[imax:]
        if len(yy) < 6:
            continue
        a, b = np.polyfit(xx, yy, 1)
        pred = a * xx + b
        ss = float(np.sum((yy - yy.mean()) ** 2)) + EPS
        r2 = 1 - float(np.sum((yy - pred) ** 2)) / ss
        if not (-60.0 <= a <= -1.5) or r2 < 0.6 or yy[0] - yy[-1] < 4.0:
            continue
        # onset sharpness: level before the track start must be much lower
        t_on = tr["tt"][0]
        b0 = int(np.median(tr["bins"]))
        if t_on >= 2 and Ls[t_on, b0] - Ls[t_on - 2, b0] < 8.0:
            continue
        f = (sl.start + float(np.mean(tr["bins"]))) * (fl[1] - fl[0])
        parts.append({"t_on": t_on, "f": f, "decay": float(a), "level": float(lv[imax]),
                      "prom": float(prom[t_on + imax, b0] if t_on + imax < prom.shape[0] else 0.0)})
    if len(parts) < min_partials:
        return []
    parts.sort(key=lambda d: d["t_on"])
    strikes = []
    i = 0
    while i < len(parts):
        grp = [parts[i]]
        j = i + 1
        while j < len(parts) and parts[j]["t_on"] - parts[i]["t_on"] <= 3:
            grp.append(parts[j])
            j += 1
        i = j
        if len(grp) < min_partials:
            continue
        fs = np.array(sorted(g["f"] for g in grp))
        inh, n_off = inharmonicity(fs)
        if n_off < 1 or fs[0] > 1500.0:
            continue
        t_on = min(g["t_on"] for g in grp)
        strikes.append({"t": t0 + float(tl[t_on]),
                        "partials_hz": [round(float(f), 1) for f in fs[:10]],
                        "decay_db_s": [round(g["decay"], 1) for g in sorted(grp, key=lambda g: g["f"])[:10]],
                        "inharmonicity": round(inh, 3), "level_db": float(max(g["level"] for g in grp)),
                        "snr_db": float(np.median([g["prom"] for g in grp]))})
    return strikes


def inharmonicity(fs: np.ndarray):
    """(best mean deviation from a harmonic series, number of partials >= 0.15 off) for f0 >= 80 Hz."""
    best = (1.0, len(fs))
    for fi in fs[:4]:
        for n in range(1, 7):
            f0 = fi / n
            if f0 < 80.0:
                break
            r = fs / f0
            if np.max(r) > 16:
                continue
            dev = np.abs(r - np.rint(r))
            m = float(np.mean(dev))
            if m < best[0]:
                best = (m, int(np.sum(dev >= 0.15)))
    return best
