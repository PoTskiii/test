"""SDR uplink survey: sweep the mobile UPLINK bands and find a streaming modem.

A 4G/5G router streaming the forest feed transmits a **continuous, high
duty-cycle uplink carrier** (~3-8 Mbit/s up, 24/7). Ordinary phones nearby
transmit in short bursts (keep-alives, the odd upload) at low duty cycle. So if
the box is on cellular, standing near it you should see, in the operator UPLINK
sub-bands, a narrow-ish carrier that is *on almost all the time and steady*,
sitting above the bursty ambient uplink noise. That is the fingerprint this
module hunts for. (If instead the box is on Starlink, its uplink is Ku-band
~14 GHz, a steered phased-array beam pointed at the sky - not detectable with
the cheap ground gear here; see ``coverage.py`` and ``docs/RF_FIELD_KIT.md``.)

This module:
* wraps whichever power-sweep tool is installed (``hackrf_sweep``, ``rtl_power``
  or ``soapy_power``) to sweep the Norwegian uplink bands and write CSV;
* parses that CSV (all three emit the same rtl_power-style rows) into a
  time x frequency power matrix;
* runs :func:`detect_persistent_carriers` to flag steady high-duty carriers and
  classify them by band;
* gives RSSI-gradient foxhunt guidance so you can walk up the carrier.

**Passive, receive-only.** Sweeping just measures received power; nothing is
transmitted. Ekomloven: receiving is allowed; do not decode or disclose content
and do not interfere. Note the RTL-SDR v4 tunes only to ~1.766 GHz, so it covers
the B28/B20/B8 uplinks (700-915 MHz) but *not* B3/B1/B7/n78 - use a HackRF/
bladeRF for those (see the doc).

Failure modes: segment/bin granularity blurs narrow carriers; a duplexer/TDD
pattern makes a real uplink look bursty (n78 is TDD - uplink only in some
slots); strong downlink spillover or an FM/DAB image can masquerade as a
"steady carrier", so always sanity-check the frequency against the band plan and
confirm by walking the gradient. Nothing here needs the network.
"""
from __future__ import annotations

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

import numpy as np

log = logging.getLogger("hordewatch.rf.sdr")
UTC = timezone.utc


# --------------------------------------------------------------------------- Norwegian uplink band plan
@dataclass(frozen=True)
class Band:
    name: str
    ul_lo_hz: float
    ul_hi_hz: float
    tech: str
    note: str = ""

    @property
    def center_hz(self):
        return 0.5 * (self.ul_lo_hz + self.ul_hi_hz)


# UPLINK ranges (device -> tower), where a streaming router radiates.
BANDS: List[Band] = [
    Band("B28", 703e6, 733e6, "LTE/NR", "700 MHz; good rural range; RTL-SDR OK"),
    Band("B20", 832e6, 862e6, "LTE", "800 MHz; primary rural coverage; RTL-SDR OK"),
    Band("B8", 880e6, 915e6, "LTE/GSM", "900 MHz; RTL-SDR OK"),
    Band("B3", 1710e6, 1785e6, "LTE", "1800 MHz; needs HackRF/bladeRF"),
    Band("B1", 1920e6, 1980e6, "LTE/NR", "2100 MHz; needs HackRF/bladeRF"),
    Band("B7", 2500e6, 2570e6, "LTE", "2600 MHz FDD uplink; needs HackRF/bladeRF"),
    Band("n78", 3400e6, 3800e6, "NR TDD", "3.5 GHz 5G; TDD so uplink is bursty by design"),
]
BAND_BY_NAME = {b.name: b for b in BANDS}
RTLSDR_MAX_HZ = 1.766e9   # RTL-SDR v4 upper tuning limit


def band_of(freq_hz: float) -> Optional[Band]:
    for b in BANDS:
        if b.ul_lo_hz <= freq_hz <= b.ul_hi_hz:
            return b
    return None


# --------------------------------------------------------------------------- CSV parsing
@dataclass
class SweepRow:
    ts: float            # unix seconds
    f_lo: float
    f_hi: float
    bin_hz: float
    n_samples: int
    power_db: np.ndarray  # one value per bin, low->high


def _parse_ts(date_s: str, time_s: str) -> float:
    date_s, time_s = date_s.strip(), time_s.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(f"{date_s} {time_s}", fmt).replace(tzinfo=UTC).timestamp()
        except ValueError:
            continue
    return 0.0


def parse_power_csv(text: str) -> List[SweepRow]:
    """Parse hackrf_sweep / rtl_power / soapy_power CSV.

    Row layout (shared by all three)::

        date, time, hz_low, hz_high, hz_bin_width, num_samples, dB, dB, ...

    Lines starting with '#' and blank lines are ignored. Malformed rows are
    skipped with a debug log rather than raising.
    """
    rows: List[SweepRow] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 7:
            continue
        try:
            ts = _parse_ts(parts[0], parts[1])
            f_lo, f_hi, bin_hz = float(parts[2]), float(parts[3]), float(parts[4])
            n = int(float(parts[5]))
            pw = np.array([float(x) for x in parts[6:] if x != ""], dtype=float)
        except ValueError:
            log.debug("skipping malformed sweep row: %.60s", line)
            continue
        if pw.size == 0:
            continue
        rows.append(SweepRow(ts, f_lo, f_hi, bin_hz, n, pw))
    return rows


# --------------------------------------------------------------------------- spectrogram assembly
@dataclass
class Spectrogram:
    freqs_hz: np.ndarray            # (F,) bin centre frequencies
    times: np.ndarray               # (T,) unix seconds, one per sweep
    power_db: np.ndarray            # (T, F), NaN where a sweep did not cover a bin
    bin_hz: float

    @property
    def n_sweeps(self):
        return self.power_db.shape[0]


def build_spectrogram(rows: List[SweepRow]) -> Optional[Spectrogram]:
    """Assemble sweep rows into a (time x frequency) power matrix.

    A full sweep is a set of consecutive rows whose ``f_lo`` ascends; a new
    sweep starts whenever ``f_lo`` drops back to (near) the minimum. Each sweep's
    bins are placed on a common frequency axis by nearest bin; bins a sweep did
    not measure are NaN.
    """
    if not rows:
        return None
    bin_hz = float(np.median([r.bin_hz for r in rows]))
    f_min = min(r.f_lo for r in rows)
    f_max = max(r.f_hi for r in rows)
    nfreq = int(round((f_max - f_min) / bin_hz))
    nfreq = max(nfreq, 1)
    freqs = f_min + (np.arange(nfreq) + 0.5) * bin_hz

    # group rows into sweeps
    sweeps: List[List[SweepRow]] = []
    cur: List[SweepRow] = []
    prev_lo = None
    for r in rows:
        if prev_lo is not None and r.f_lo <= prev_lo + 0.5 * bin_hz:
            if cur:
                sweeps.append(cur)
            cur = []
        cur.append(r)
        prev_lo = r.f_lo
    if cur:
        sweeps.append(cur)

    T = len(sweeps)
    P = np.full((T, nfreq), np.nan)
    times = np.zeros(T)
    for ti, sw in enumerate(sweeps):
        times[ti] = np.mean([r.ts for r in sw]) if sw else 0.0
        for r in sw:
            centres = r.f_lo + (np.arange(r.power_db.size) + 0.5) * r.bin_hz
            idx = np.round((centres - f_min) / bin_hz - 0.5).astype(int)
            ok = (idx >= 0) & (idx < nfreq)
            P[ti, idx[ok]] = r.power_db[ok]
    return Spectrogram(freqs, times, P, bin_hz)


# --------------------------------------------------------------------------- persistent carrier detection
@dataclass
class Carrier:
    center_hz: float
    bw_hz: float
    mean_over_floor_db: float       # how far the carrier sits above the local noise floor
    duty_cycle: float               # fraction of sweeps the carrier is present
    steady_db: float                # temporal std of power when present (low = steady/streaming)
    peak_db: float
    band: Optional[str]
    is_uplink_band: bool
    verdict: str                    # streaming_uplink_like | intermittent | weak
    n_bins: int = 1

    def describe(self) -> str:
        return (f"{self.center_hz/1e6:8.3f} MHz  bw {self.bw_hz/1e6:.2f} MHz  "
                f"+{self.mean_over_floor_db:4.1f} dB  duty {self.duty_cycle:.2f}  "
                f"steady {self.steady_db:.1f} dB  [{self.band or 'out-of-band'}]  {self.verdict}")


def detect_persistent_carriers(spec: Spectrogram, *, floor_margin_db: float = 8.0,
                               min_duty: float = 0.7, max_steady_db: float = 6.0,
                               merge_gap_bins: int = 1, min_bw_hz: float = 0.0,
                               max_bw_hz: float = 12e6) -> List[Carrier]:
    """Find steady, high duty-cycle carriers standing above the noise floor.

    For every frequency bin we compute a robust per-bin noise floor (temporal
    median), the *duty cycle* (fraction of sweeps whose power exceeds
    floor + ``floor_margin_db``), and the temporal std of the power while the
    carrier is present. A streaming-router uplink is *persistent* (duty >=
    ``min_duty``) and *steady* (std <= ``max_steady_db``); a bursty phone fails
    one or both. Contiguous qualifying bins (allowing ``merge_gap_bins`` gaps)
    are merged into one carrier and its band is looked up.

    ``max_bw_hz`` rejects wide, whole-band elevations (a raised noise floor,
    downlink spillover) that are not a single carrier.
    """
    P = spec.power_db
    F = P.shape[1]
    if spec.n_sweeps < 2:
        return []
    # per-bin robust floor over time (10th percentile ~ noise between bursts)
    with np.errstate(invalid="ignore"):
        floor = np.nanpercentile(P, 10, axis=0)
        floor = np.where(np.isfinite(floor), floor, np.nanmin(P))
    thresh = floor + floor_margin_db

    present = P >= thresh[None, :]           # (T, F) bool, NaN -> False
    present = np.where(np.isfinite(P), present, False)
    covered = np.isfinite(P).sum(axis=0)
    covered = np.maximum(covered, 1)
    duty = present.sum(axis=0) / covered

    # power above floor and its temporal steadiness while present
    over = P - floor[None, :]
    mean_over = np.array([np.nanmean(over[present[:, k], k]) if present[:, k].any() else 0.0
                          for k in range(F)])
    steady = np.array([np.nanstd(P[present[:, k], k]) if present[:, k].sum() >= 2 else 0.0
                       for k in range(F)])
    peak = np.nan_to_num(np.nanmax(P, axis=0), nan=-999.0)

    qualifies = (duty >= min_duty) & (steady <= max_steady_db) & (mean_over >= floor_margin_db)

    # merge contiguous qualifying bins (bridge small gaps)
    carriers: List[Carrier] = []
    k = 0
    while k < F:
        if not qualifies[k]:
            k += 1
            continue
        j = k
        gap = 0
        last = k
        while j + 1 < F:
            if qualifies[j + 1]:
                last = j + 1
                gap = 0
            else:
                gap += 1
                if gap > merge_gap_bins:
                    break
            j += 1
        lo, hi = k, last
        bins = np.arange(lo, hi + 1)
        w = np.clip(mean_over[bins], 0.1, None)
        center = float(np.sum(spec.freqs_hz[bins] * w) / np.sum(w))
        bw = float((hi - lo + 1) * spec.bin_hz)
        c_mean_over = float(np.mean(mean_over[bins]))
        c_duty = float(np.mean(duty[bins]))
        c_steady = float(np.mean(steady[bins]))
        c_peak = float(np.max(peak[bins]))
        b = band_of(center)
        if min_bw_hz <= bw <= max_bw_hz:
            verdict = "streaming_uplink_like" if (b is not None) else "steady_carrier_out_of_band"
            carriers.append(Carrier(center, bw, c_mean_over, c_duty, c_steady, c_peak,
                                    b.name if b else None, b is not None, verdict, len(bins)))
        k = hi + 1

    carriers.sort(key=lambda c: (c.is_uplink_band, c.duty_cycle, c.mean_over_floor_db), reverse=True)
    return carriers


def carrier_power_timeseries(spec: Spectrogram, center_hz: float, bw_hz: float = 2e6) -> np.ndarray:
    """Mean power (dB) in a window around ``center_hz`` per sweep -- feed this to
    the RSSI-gradient guidance while walking."""
    half = 0.5 * bw_hz
    sel = np.abs(spec.freqs_hz - center_hz) <= half
    if not sel.any():
        sel = np.argmin(np.abs(spec.freqs_hz - center_hz))[None]
    return np.nanmean(spec.power_db[:, sel], axis=1)


# --------------------------------------------------------------------------- foxhunt guidance
def gradient_guidance(power_series, min_slope_db: float = 0.5) -> dict:
    """Warmer/colder guidance from a per-position carrier-power series (delegates
    to the WiFi RSSI-trend logic)."""
    from .wifi_scan import rssi_trend
    return rssi_trend([float(x) for x in power_series if np.isfinite(x)], min_slope_db=min_slope_db)


def locate_carrier(samples, n: float = 2.5, fit_n: bool = False):
    """Multilaterate a carrier from (lat, lon, carrier_power_db) samples.
    ``carrier_power_db`` behaves like RSSI for the log-distance model."""
    from . import foxhunt
    return foxhunt.rssi_multilaterate(samples, n=n, fit_n=fit_n)


# --------------------------------------------------------------------------- driving the SDR
def which_tool() -> Optional[str]:
    for t in ("hackrf_sweep", "rtl_power", "soapy_power"):
        if shutil.which(t):
            return t
    return None


def sweep_command(tool: str, band: Band, out_csv: str, *, bin_hz: float = 100e3,
                  gain: int = 40, one_shot: bool = False) -> List[str]:
    """Build a command line to sweep one band with the given tool.

    All three write rtl_power-style CSV that :func:`parse_power_csv` reads.
    ``hackrf_sweep`` -w is bin width in Hz; ``rtl_power`` -i is the integration
    interval. We add small guard margins around the band edges.
    """
    lo = int(band.ul_lo_hz - 1e6)
    hi = int(band.ul_hi_hz + 1e6)
    if tool == "hackrf_sweep":
        cmd = ["hackrf_sweep", "-f", f"{lo//1000000}:{hi//1000000}",
               "-w", str(int(bin_hz)), "-l", "24", "-g", str(gain), "-r", out_csv]
        if one_shot:
            cmd += ["-1"]
        return cmd
    if tool == "rtl_power":
        cmd = ["rtl_power", "-f", f"{lo}:{hi}:{int(bin_hz)}", "-g", str(gain), "-i", "5", out_csv]
        if one_shot:
            cmd += ["-1"]
        return cmd
    if tool == "soapy_power":
        return ["soapy_power", "-f", f"{lo}:{hi}", "-B", str(int(bin_hz)), "-O", out_csv,
                "-T" if not one_shot else "-n", "1"]
    raise ValueError(f"unknown tool {tool}")


def run_sweep(band: Band, out_csv: str, *, tool: Optional[str] = None, timeout: float = 120.0,
              **kw) -> Optional[List[SweepRow]]:
    """Run a sweep and parse the CSV. Fails soft (logs and returns None) if no
    SDR sweep tool is installed or the tool errors. Warns if the band is above
    the RTL-SDR tuning limit."""
    tool = tool or which_tool()
    if tool is None:
        log.warning("no SDR sweep tool found (install hackrf-tools / rtl-sdr / soapy_power); see docs/RF_FIELD_KIT.md")
        return None
    if tool == "rtl_power" and band.ul_hi_hz > RTLSDR_MAX_HZ:
        log.warning("%s is above RTL-SDR's %.0f MHz limit; use a HackRF/bladeRF for band %s",
                    band.name, RTLSDR_MAX_HZ / 1e6, band.name)
    cmd = sweep_command(tool, band, out_csv, one_shot=True, **kw)
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except Exception as e:  # pragma: no cover - hardware path
        log.warning("sweep tool '%s' failed: %s", tool, e)
        return None
    try:
        with open(out_csv) as f:
            return parse_power_csv(f.read())
    except OSError as e:
        log.warning("could not read sweep output %s: %s", out_csv, e)
        return None


def survey_file(csv_path: str, **detect_kw) -> List[Carrier]:
    """Parse an existing sweep CSV and return detected persistent carriers."""
    with open(csv_path) as f:
        rows = parse_power_csv(f.read())
    spec = build_spectrogram(rows)
    if spec is None:
        return []
    return detect_persistent_carriers(spec, **detect_kw)


# --------------------------------------------------------------------------- CLI
def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="SDR uplink survey / persistent-carrier detector.")
    ap.add_argument("--analyze", metavar="CSV", help="analyse an existing sweep CSV instead of sweeping")
    ap.add_argument("--band", choices=list(BAND_BY_NAME), help="band to sweep live")
    ap.add_argument("--out", default="sweep.csv", help="sweep CSV output path")
    ap.add_argument("--bin-khz", type=float, default=100.0)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if a.analyze:
        carriers = survey_file(a.analyze)
    elif a.band:
        rows = run_sweep(BAND_BY_NAME[a.band], a.out, bin_hz=a.bin_khz * 1e3)
        if rows is None:
            return
        spec = build_spectrogram(rows)
        carriers = detect_persistent_carriers(spec) if spec else []
    else:
        ap.error("give --analyze CSV or --band NAME")
        return

    if not carriers:
        print("No persistent carriers detected.")
        return
    print(f"{len(carriers)} carrier(s):")
    for c in carriers:
        print("  " + c.describe())
    up = [c for c in carriers if c.is_uplink_band and c.verdict == "streaming_uplink_like"]
    if up:
        print("\nLikely streaming-uplink carrier(s) -- walk the gradient toward rising power:")
        for c in up:
            print(f"  {c.center_hz/1e6:.3f} MHz ({c.band}), +{c.mean_over_floor_db:.1f} dB, duty {c.duty_cycle:.2f}")


if __name__ == "__main__":
    main()
