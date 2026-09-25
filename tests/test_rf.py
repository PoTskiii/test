"""Tests for the hordewatch RF + field-search kit (offline, synthetic fixtures)."""
import math

import numpy as np
import pytest

from hordewatch.rf import coverage, foxhunt, sdr_survey, wifi_scan


# =========================================================================== WiFi parsers & flagging
NMCLI = (
    # SSID:BSSID(escaped colons):CHAN:FREQ:SIGNAL:SECURITY
    r"STARLINK:F8\:0C\:F3\:11\:22\:33:6:2437 MHz:82:WPA2" "\n"
    r"RUT240_9F2A:00\:1E\:42\:AA\:BB\:CC:36:5180 MHz:47:WPA2" "\n"
    r"Get-home-5G:AA\:BB\:CC\:DD\:EE\:FF:11:2462 MHz:71:WPA2 WPA3" "\n"
    r":DE\:AD\:BE\:EF\:00\:01:1:2412 MHz:33:--" "\n"      # hidden SSID
)

NETSH = """Interface name : Wi-Fi
There are 3 networks currently visible.

SSID 1 : STARLINK
    Network type            : Infrastructure
    Authentication          : WPA2-Personal
    Encryption              : CCMP
    BSSID 1                 : f8:0c:f3:11:22:33
         Signal             : 90%
         Radio type         : 802.11ac
         Channel            : 6
    BSSID 2                 : f8:0c:f3:11:22:34
         Signal             : 55%
         Channel            : 149

SSID 2 : Pepwave_1234
    Authentication          : WPA2-Personal
    BSSID 1                 : 00:1a:dd:11:22:33
         Signal             : 40%
         Channel            : 11
"""

TERMUX = """[
  {"bssid": "f8:0c:f3:11:22:33", "frequency_mhz": 2437, "rssi": -48, "ssid": "STARLINK", "channel": 6},
  {"bssid": "34:6f:24:aa:bb:cc", "frequency_mhz": 5180, "rssi": -71, "ssid": "Teltonika-XY", "channel": 36},
  {"bssid": "de:ad:be:ef:00:02", "frequency_mhz": 2412, "rssi": -83, "ssid": "someone_iPhone", "channel": 1}
]"""


def test_parse_nmcli():
    aps = wifi_scan.parse_nmcli(NMCLI)
    assert len(aps) == 4
    star = aps[0]
    assert star.ssid == "STARLINK"
    assert star.bssid == "F8:0C:F3:11:22:33"
    assert star.channel == 6
    assert star.freq_mhz == 2437
    assert star.band == "2.4GHz"
    # 82% -> approx dBm
    assert star.rssi_dbm == pytest.approx(-59.0, abs=0.1)
    assert "starlink" in star.tags
    # hidden ssid row
    assert "hidden_ssid" in aps[3].tags


def test_parse_netsh():
    aps = wifi_scan.parse_netsh(NETSH)
    # two BSSIDs for STARLINK + one for Pepwave
    assert len(aps) == 3
    ssids = {a.bssid: a.ssid for a in aps}
    assert ssids["F8:0C:F3:11:22:33"] == "STARLINK"
    star = [a for a in aps if a.bssid == "F8:0C:F3:11:22:33"][0]
    assert star.channel == 6
    assert star.rssi_dbm == pytest.approx(-55.0, abs=0.1)   # 90% -> -55
    assert "starlink" in star.tags
    pep = [a for a in aps if a.ssid == "Pepwave_1234"][0]
    assert any(t.startswith("cellular_router:peplink") for t in pep.tags)


def test_parse_termux():
    aps = wifi_scan.parse_termux(TERMUX)
    assert len(aps) == 3
    star = aps[0]
    assert star.ssid == "STARLINK"
    assert star.rssi_dbm == -48
    assert "starlink" in star.tags
    telt = aps[1]
    assert any(t.startswith("cellular_router:teltonika") for t in telt.tags)
    # OUI tag for DJI/Teltonika BSSID recognised
    assert any("oui:" in t for t in telt.tags)


def test_flag_starlink_variants():
    for s in ["STARLINK", "Starlink", "STARLINK-1A2B", "Starlink_Forest", "my starlink dish"]:
        assert "starlink" in wifi_scan.flag_ssid(s), s
    assert wifi_scan.flag_ssid("HomeNet_2G") == []
    # OUI-only detection (hidden or renamed SSID but SpaceX radio)
    assert "oui:starlink" in wifi_scan.flag_ssid("Renamed", "F8:0C:F3:00:00:01")


def test_rssi_trend():
    warming = wifi_scan.rssi_trend([-80, -78, -74, -70, -66])
    assert warming["trend"] == "warmer" and warming["slope_db"] > 0
    cooling = wifi_scan.rssi_trend([-60, -65, -70, -78])
    assert cooling["trend"] == "colder"
    flat = wifi_scan.rssi_trend([-70, -70.2, -69.8, -70.1])
    assert flat["trend"] == "steady"


# =========================================================================== foxhunt: RSSI multilateration
def test_rssi_multilateration_within_30m():
    rng = np.random.default_rng(1234)
    tx_lat, tx_lon = 61.1000, 11.2000
    n_true, p0_true = 2.7, -35.0
    noise_db = 3.0
    # 20 samples walked around the transmitter with good angular spread
    # (radii 40-220 m), as the field procedure recommends
    samples = []
    for k in range(20):
        ang = math.radians(k * (360.0 / 20) + rng.uniform(-8, 8))
        r = rng.uniform(40, 220)
        east, north = r * math.sin(ang), r * math.cos(ang)
        lat, lon = foxhunt.to_wgs84(east, north, tx_lat, tx_lon)
        rssi = p0_true - 10 * n_true * math.log10(r) + rng.normal(0, noise_db)
        samples.append((float(lat), float(lon), rssi))
    fix = foxhunt.rssi_multilaterate(samples, n=n_true)
    from hordejakt.geo import haversine
    err_m = float(haversine(fix.lat, fix.lon, tx_lat, tx_lon)) * 1000.0
    assert err_m < 30.0, f"error {err_m:.1f} m"
    assert fix.extra["rms_db"] < 2 * noise_db
    assert fix.sigma_m > 0


def test_rssi_multilateration_fit_n():
    rng = np.random.default_rng(7)
    tx_lat, tx_lon = 60.5, 10.5
    n_true, p0 = 3.2, -30.0
    samples = []
    for _ in range(30):
        e, nn = rng.uniform(-250, 250), rng.uniform(-250, 250)
        lat, lon = foxhunt.to_wgs84(e, nn, tx_lat, tx_lon)
        d = max(15.0, math.hypot(e, nn))
        rssi = p0 - 10 * n_true * math.log10(d) + rng.normal(0, 2.0)
        samples.append((float(lat), float(lon), rssi))
    fix = foxhunt.rssi_multilaterate(samples, n=2.5, fit_n=True)
    from hordejakt.geo import haversine
    err = float(haversine(fix.lat, fix.lon, tx_lat, tx_lon)) * 1000
    assert err < 50.0
    assert 2.3 < fix.extra["n"] < 4.2


# =========================================================================== foxhunt: bearing intersection
def test_bearing_intersection():
    from hordejakt.geo import bearing, destination, haversine
    tx_lat, tx_lon = 61.05, 11.30
    rng = np.random.default_rng(99)
    obs = [(61.04, 11.28), (61.06, 11.28), (61.05, 11.33), (61.03, 11.31)]
    fixes = []
    for (la, lo) in obs:
        b = float(bearing(la, lo, tx_lat, tx_lon)) + rng.normal(0, 1.5)
        fixes.append((la, lo, b))
    fix = foxhunt.bearing_intersection(fixes)
    err = float(haversine(fix.lat, fix.lon, tx_lat, tx_lon)) * 1000
    assert err < 80.0, f"error {err:.1f} m"
    assert not fix.extra["near_parallel"]


def test_bearing_intersection_near_parallel_flagged():
    # all observers on one road looking the same way -> ill-conditioned
    fixes = [(61.00, 11.00, 45.0), (61.001, 11.002, 45.2), (61.002, 11.004, 44.8)]
    fix = foxhunt.bearing_intersection(fixes)
    assert fix.extra["cond"] > 50.0
    assert fix.extra["near_parallel"]


def test_estimate_dispatch():
    ms = [{"lat": 61.04, "lon": 11.28, "bearing": 60.0},
          {"lat": 61.06, "lon": 11.33, "bearing": 300.0}]
    fix = foxhunt.estimate(ms)
    assert fix.method == "bearing_intersection"
    assert "google.com/maps" in fix.google_maps


# =========================================================================== SDR sweep parser + carrier detector
def _make_hackrf_csv(*, n_sweeps=30, f_lo=832e6, f_hi=862e6, bin_hz=100e3,
                     carrier_hz=845.0e6, carrier_bw_hz=300e3, carrier_db=-75.0,
                     burst_hz=855.0e6, burst_db=-58.0, burst_duty=0.3,
                     floor_db=-95.0, seed=0):
    """Synthetic hackrf_sweep CSV: an always-on narrow carrier + a bursty
    interferer + noise floor. Each sweep is split into two chunk rows."""
    rng = np.random.default_rng(seed)
    edges = np.arange(f_lo, f_hi + 1, bin_hz)
    n_bins = len(edges) - 1
    centres = f_lo + (np.arange(n_bins) + 0.5) * bin_hz
    lines = []
    t0 = 1_700_000_000
    for s in range(n_sweeps):
        power = floor_db + rng.normal(0, 2.0, n_bins)
        # persistent carrier (present every sweep, steady)
        cmask = np.abs(centres - carrier_hz) <= carrier_bw_hz / 2
        power[cmask] = carrier_db + rng.normal(0, 1.0, cmask.sum())
        # bursty interferer (present only some sweeps, strong when on)
        if rng.random() < burst_duty:
            bmask = np.abs(centres - burst_hz) <= 150e3
            power[bmask] = burst_db + rng.normal(0, 4.0, bmask.sum())
        # split into two chunk-rows to exercise sweep grouping
        mid = n_bins // 2
        ts = t0 + s * 5
        import datetime as _dt
        d = _dt.datetime.utcfromtimestamp(ts)
        date_s, time_s = d.strftime("%Y-%m-%d"), d.strftime("%H:%M:%S.%f")
        for (lo_i, hi_i) in [(0, mid), (mid, n_bins)]:
            row_lo = edges[lo_i]
            row_hi = edges[hi_i]
            vals = ", ".join(f"{v:.2f}" for v in power[lo_i:hi_i])
            lines.append(f"{date_s}, {time_s}, {int(row_lo)}, {int(row_hi)}, {bin_hz:.2f}, 1024, {vals}")
    return "\n".join(lines)


def test_parse_power_csv_and_spectrogram():
    csv = _make_hackrf_csv(n_sweeps=10)
    rows = sdr_survey.parse_power_csv(csv)
    assert len(rows) == 20                       # 10 sweeps x 2 chunks
    spec = sdr_survey.build_spectrogram(rows)
    assert spec is not None
    assert spec.n_sweeps == 10                   # chunks regrouped into sweeps
    assert spec.power_db.shape[1] == 300
    assert spec.freqs_hz[0] == pytest.approx(832.05e6, abs=1e3)


def test_persistent_carrier_detected():
    csv = _make_hackrf_csv(n_sweeps=40, seed=3)
    spec = sdr_survey.build_spectrogram(sdr_survey.parse_power_csv(csv))
    carriers = sdr_survey.detect_persistent_carriers(spec)
    assert carriers, "should detect at least one carrier"
    # the persistent 845 MHz carrier is found, in band B20, steady, high duty
    near = [c for c in carriers if abs(c.center_hz - 845.0e6) < 4e5]
    assert near, [round(c.center_hz / 1e6, 3) for c in carriers]
    c = near[0]
    assert c.band == "B20"
    assert c.is_uplink_band and c.verdict == "streaming_uplink_like"
    assert c.duty_cycle > 0.9
    assert c.mean_over_floor_db > 12.0
    assert c.steady_db < 6.0
    # the bursty 855 MHz interferer is NOT reported as a persistent carrier
    bursty = [c for c in carriers if abs(c.center_hz - 855.0e6) < 3e5 and c.duty_cycle >= 0.7]
    assert not bursty


def test_carrier_gradient_guidance():
    # rising carrier power across positions -> "warmer"
    g = sdr_survey.gradient_guidance([-90, -85, -80, -74, -68])
    assert g["trend"] == "warmer"


def test_sweep_command_and_rtlsdr_limit(caplog):
    b7 = sdr_survey.BAND_BY_NAME["B7"]
    cmd = sdr_survey.sweep_command("hackrf_sweep", b7, "out.csv", bin_hz=100e3, one_shot=True)
    assert cmd[0] == "hackrf_sweep" and "-1" in cmd
    # B7 (2.5 GHz) is above the RTL-SDR limit
    assert b7.ul_hi_hz > sdr_survey.RTLSDR_MAX_HZ
    assert sdr_survey.band_of(845e6).name == "B20"


# =========================================================================== coverage layer
def test_coverage_field_higher_near_masts():
    masts = [coverage.Mast(61.10, 11.30), coverage.Mast(60.90, 11.00)]
    prob, rx = coverage.coverage_field_from_masts(masts)
    assert prob.shape == coverage.GRID.shape
    g = coverage.GRID
    # coverage right at a mast >> coverage far away
    p_near = float(g.sample(prob, 61.10, 11.30))
    p_far = float(g.sample(prob, 58.2, 5.0))
    assert p_near > 0.8
    assert p_far < p_near
    assert 0.0 <= prob[np.isfinite(prob)].min() <= prob[np.isfinite(prob)].max() <= 1.0


def test_coverage_layer_emitted_and_loads(tmp_path):
    masts = [coverage.Mast(61.10, 11.30, eirp_dbm=63.0)]
    path = coverage.build_layer(masts=masts, out_dir=tmp_path, reliability=0.3)
    assert path is not None and path.exists()
    ll, meta = _read_layer(path)
    assert ll.shape == coverage.GRID.shape
    assert meta["reliability"] == pytest.approx(0.3)
    assert meta["independence_group"] == "uplink_cellular"
    assert meta["hypothesis"] == "cellular_uplink"


def test_coverage_fail_soft_without_data(tmp_path, monkeypatch):
    # no masts + fetch returns None -> no layer written, no crash
    monkeypatch.setattr(coverage, "fetch_nkom_masts", lambda *a, **k: None)
    path = coverage.build_layer(masts=None, out_dir=tmp_path)
    assert path is None
    assert not list(tmp_path.glob("*.npz"))


def test_apply_verdict():
    assert coverage.apply_verdict(0.3, "starlink_like", 0.7) is None      # drop layer
    assert coverage.apply_verdict(0.3, "cellular_like", 0.8) > 0.3        # strengthen
    assert coverage.apply_verdict(0.3, "unknown", 0.5) == 0.3


def _read_layer(path):
    from hordewatch.bridges.common import read_layer
    return read_layer(path)
