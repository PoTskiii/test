"""Tests for hordewatch.bridges (aircraft, weather, engine, default.no poller). Offline only."""
import gzip
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hordejakt.geo import FT, destination, haversine  # noqa: E402
from hordejakt.grid import GRID, Grid  # noqa: E402
from hordewatch.analyzers.base import Context  # noqa: E402
from hordewatch.bridges import adsb as A  # noqa: E402
from hordewatch.bridges import defaultno as DN  # noqa: E402
from hordewatch.bridges import engine as E  # noqa: E402
from hordewatch.bridges import met as M  # noqa: E402
from hordewatch.bridges.common import from_unix, read_layer, to_unix, write_layer  # noqa: E402
from hordewatch.db import DB  # noqa: E402
from hordewatch.types import Observation, StreamClock, parse_iso  # noqa: E402

UTC = timezone.utc
TRACE = A.MK_BEVIS_ADSB / "trace_4791ac.json"
BERGEN = (60.39, 5.32)
UNDER_NOZ9EG = (61.33, 10.905)   # NOZ9EG passed overhead southbound ~21:29 CEST 21.09
NO_NET = {"live_record": False, "calibrate": False, "async": False, "settle_s": 0.0, "lookback_h": 1e6}


def ctx_for(tmp_path, **clock):
    return Context(db=DB(tmp_path / "hw.sqlite"), config={}, clock=StreamClock(**clock))


def ll_at(ll, lat, lon, grid=GRID):
    i, j = grid.index(lat, lon)
    return float(ll[i, j])


# =========================================================================== ADS-B parsing
def test_parse_real_adsblol_trace():
    tr = A.parse_trace(TRACE)
    assert tr.hex == "4791ac" and tr.callsign == "NOZ9EG" and tr.reg == "LN-NIQ" and tr.type == "B738"
    assert len(tr.t) == 1643
    assert np.all(np.diff(tr.t) >= 0)
    assert np.isnan(tr.alt_m).sum() >= 70           # 'ground' rows -> NaN altitude
    # mk_bevis fly_2109_resultat.txt: at stream 21:29:38 - 22 s NOZ9EG was at 61.317 N 10.904 E, 25920 ft geom
    t = to_unix("2026-09-21T21:29:16+02:00")
    la, lo, al, ok = tr.at(t)
    assert ok[0]
    assert abs(la[0] - 61.317) < 0.003 and abs(lo[0] - 10.904) < 0.003
    assert abs(al[0] / FT - 25920) < 120
    # no interpolation on the ground / outside the trace
    assert not tr.at(tr.t[0] - 10)[3][0]
    assert not tr.at(tr.t[-1] - 1)[3][0]             # last rows are 'ground' at OSL


def test_parse_gzip_bytes_and_snapshots():
    raw = TRACE.read_bytes()
    assert raw[:2] == b"\x1f\x8b"
    tr = A.parse_trace(gzip.decompress(raw))           # plain JSON bytes work too
    assert tr.hex == "4791ac"
    snap = {"now": 1790018979000, "ac": [
        {"hex": "4791ac", "flight": "NOZ9EG  ", "lat": 61.3, "lon": 10.9, "alt_baro": 25000, "alt_geom": 25800,
         "gs": 490, "track": 182, "seen_pos": 1.0},
        {"hex": "abc123", "lat": 60.2, "lon": 11.1, "alt_baro": "ground", "seen_pos": 0},
        {"hex": "nopos"}]}
    now, pts = A.parse_readsb_snapshot(snap)
    assert now == pytest.approx(1790018979.0)
    assert len(pts) == 2 and pts[0]["flight"] == "NOZ9EG" and pts[0]["t"] == pytest.approx(1790018978.0)
    assert pts[0]["alt_m"] == pytest.approx(25800 * FT) and pts[1]["alt_m"] is None
    osk = {"time": 1790018979, "states": [["4791ac", "NOZ9EG  ", "Norway", 1790018978, 1790018979, 10.9, 61.3, 7600.0,
                                            False, 250.0, 182.0, -10.0, None, 7860.0, "1262", False, 0]]}
    p = A.parse_opensky_states(osk)[0]
    assert p["alt_m"] == 7860.0 and p["gs"] == pytest.approx(250 / A.KT)


def test_fixture_fly2130_timing_offset_matches_real_trace():
    """fly_2130.json timestamps are ~45 s early vs the adsb.lol trace; the provider corrects it."""
    real = A.parse_trace(TRACE)

    def mean_err(offset):
        fp = A.FixtureProvider(fly2130_offset_s=offset, trace_paths=[])
        blocks, _ = fp._load()
        noz = next(t for b in blocks for t in b[2] if t.callsign == "NOZ9EG" and "fly_2130" in t.source)
        ts = np.linspace(noz.t[0] + 5, noz.t[-1] - 5, 8)
        la1, lo1, _, ok1 = noz.at(ts)
        la2, lo2, _, ok2 = real.at(ts)
        ok = ok1 & ok2
        return float(np.mean(haversine(la1[ok], lo1[ok], la2[ok], lo2[ok])))
    assert mean_err(45.0) < 1.5
    assert mean_err(0.0) > 8.0


def test_merge_prefers_real_trace_and_dedupes_unnamed():
    ts = A.FixtureProvider().tracks(to_unix("2026-09-21T21:27:00+02:00"), to_unix("2026-09-21T21:30:00+02:00"))
    labels = [t.label for t in ts.tracks]
    assert labels.count("NOZ9EG") == 1 and not any(l.startswith("@") for l in labels)
    noz = next(t for t in ts.tracks if t.label == "NOZ9EG")
    assert noz.hex == "4791ac" and not noz.approx


# =========================================================================== geometry
def test_image_tilt_reproduces_mk_bevis_table():
    # tilt_2129_resultat.txt (heading 219.6 deg): Myklebysaeter 15 s: h 29 A 212 -> -13; Madsskardveien 30 s: h 24 A 224 -> +10
    assert A.image_tilt(212, 29, 219.6) == pytest.approx(-13, abs=1.0)
    assert A.image_tilt(224, 24, 219.6) == pytest.approx(10, abs=1.0)
    assert A.image_tilt(168, 21, 219.6) == pytest.approx(-63, abs=1.5)


def test_pixel_to_azel_camera_model():
    az, el = A.pixel_to_azel([639.5, 639.5, 0.0], [359.5, 0.0, 359.5], 1280, 720, 1068.0, 219.6)
    assert az[0] == pytest.approx(219.6, abs=1e-6) and el[0] == pytest.approx(0.0, abs=1e-6)
    assert el[1] == pytest.approx(np.degrees(np.arctan(359.5 / 1068.0)), abs=1e-6)
    assert az[2] == pytest.approx(219.6 - np.degrees(np.arctan(639.5 / 1068.0)), abs=1e-6)


def test_sighting_prob_agrees_with_hordejakt_event_prob():
    from hordejakt.layers.aircraft import event_prob
    clats, clons = A.coarse_axes((60.5, 62.0, 10.0, 12.0))
    CL, CO = np.meshgrid(clats, clons, indexing="ij")
    real = A.parse_trace(TRACE)
    t = to_unix("2026-09-21T21:29:16+02:00")
    la, lo, al, _ = real.at(t)
    mine = A.sighting_prob(CL, CO, [real], t + 22.0, np.array([22.0]), np.array([1.0]), q=0.85, floor=0.03)
    ref = event_prob(CL, CO, {"NOZ9EG": [(la[0], lo[0], al[0])]}, q=0.85, floor=0.03)
    assert np.max(np.abs(mine - ref)) < 2e-3


def test_sound_speed_and_audibility():
    c = A.sound_speed_eff(np.array([600.0, 10600.0]))
    assert c[0] == pytest.approx(337.0, abs=2.0) and 305 < c[1] < 325
    assert A.sound_speed_eff(10600.0, mode=343.0) == pytest.approx(343.0)
    p = A.audible_prob(np.array([5.0, 16.0, 30.0]))
    assert p[0] > 0.95 and p[1] == pytest.approx(0.5) and p[2] < 0.01


def test_latency_prior_shapes():
    v, w = A.latency_prior()
    assert w.sum() == pytest.approx(1.0)
    inside = (v >= 15) & (v <= 60)
    assert w[inside].sum() > 0.6 and np.ptp(w[inside]) < 1e-12   # 10 s shoulders hold the rest
    v2, w2 = A.latency_prior(calib={"well_determined": True, "latency_s": 25.0, "latency_sigma_s": 4.0})
    assert np.sum(v2 * w2) == pytest.approx(25.0, abs=0.5)
    v3, w3 = A.with_reaction(v2, w2, 8.0)
    assert np.sum(v3 * w3) == pytest.approx(29.0, abs=0.6)


# =========================================================================== sighting event end-to-end
def test_sighting_event_2109_layer(tmp_path, monkeypatch):
    ctx = ctx_for(tmp_path)
    tc = parse_iso("2026-09-21T21:29:38+02:00")
    ctx.db.add_observation(Observation("gesture_point_up", from_unix(to_unix(tc) - 30), {"arm_angle_deg_from_vertical": 5},
                                       analyzer="gesture", confidence=0.8, ts_capture=tc))
    b = A.AircraftBridge({**NO_NET, "providers": ["fixture"], "layers_dir": str(tmp_path / "layers"),
                          "cache_dir": str(tmp_path / "cache")})
    obs = b.on_tick(ctx)
    files = list((tmp_path / "layers").glob("aircraft_*.npz"))
    assert len(files) == 1 and files[0].name == "aircraft_20260921T192938Z.npz"
    ll, meta = read_layer(files[0])
    assert ll.shape == GRID.shape and np.isfinite(ll).all()
    assert 0.5 <= meta["reliability"] <= 0.75
    assert meta["independence_group"] == "aircraft_2109_2129_point"   # dedup with hordejakt's hand-made layer
    under, bergen = ll_at(ll, *UNDER_NOZ9EG), ll_at(ll, *BERGEN)
    assert under > bergen + 2.0
    assert ll_at(ll, 61.3995, 11.0316) > bergen + 2.0                # candidate 1 (Myklebysaeter) saw it at ~33 deg
    assert obs and obs[0].kind == "aircraft_match"
    ev = ctx.db.con.execute("SELECT kind FROM events").fetchall()
    assert ("aircraft_layer",) in ev
    # processed once only
    assert b.on_tick(ctx) == []
    # hordejakt.layers.live picks it up unchanged
    from hordejakt.layers import live
    monkeypatch.setattr(live, "LIVE_DIR", tmp_path / "layers")
    layers = live.build(GRID, {})
    assert len(layers) == 1 and layers[0].name == meta["name"]
    assert np.allclose(layers[0].loglik, ll, equal_nan=True)


def test_async_worker_path(tmp_path):
    import time as _t
    ctx = ctx_for(tmp_path)
    tc = parse_iso("2026-09-21T21:29:38+02:00")
    ctx.db.add_observation(Observation("gesture_point_up", from_unix(to_unix(tc) - 30), {}, analyzer="g", ts_capture=tc))
    b = A.AircraftBridge({**NO_NET, "async": True, "providers": ["fixture"], "layers_dir": str(tmp_path / "layers"),
                          "cache_dir": str(tmp_path / "cache")})
    assert b.on_tick(ctx) == []                       # submitted, not blocking
    out, t0 = [], _t.time()
    while not out and _t.time() - t0 < 60:
        _t.sleep(0.2)
        out = b.on_tick(ctx)
    assert out and out[0].kind == "aircraft_match" and out[0].value["callsign"] == "NOZ9EG"
    assert (tmp_path / "layers" / "aircraft_20260921T192938Z.npz").exists()


def test_arm_tilt_sharpens_sighting(tmp_path):
    """A tilt of -13 deg (mk_bevis: Myklebysaeter at 15 s delay) must favour cells SW-of-track views."""
    real = A.parse_trace(TRACE)
    clats, clons = A.coarse_axes((61.0, 61.8, 10.4, 11.6))
    CL, CO = np.meshgrid(clats, clons, indexing="ij")
    tc = to_unix("2026-09-21T21:29:38+02:00")
    D, W = np.array([15.0]), np.array([1.0])
    p_no = A.sighting_prob(CL, CO, [real], tc, D, W)
    p_tl = A.sighting_prob(CL, CO, [real], tc, D, W, tilt_obs=-13.0, tilt_weight=0.9)
    i, j = np.argmin(np.abs(clats - 61.40)), np.argmin(np.abs(clons - 11.04))   # Myklebysaeter
    k, m = np.argmin(np.abs(clats - 61.46)), np.argmin(np.abs(clons - 10.84))   # S-Messelt (tilt -63)
    ratio_myk = p_tl[i, j] / p_no[i, j]
    ratio_mes = p_tl[k, m] / p_no[k, m]
    assert ratio_myk > 0.9 and ratio_mes < 0.6


def test_aircraft_light_direction(tmp_path):
    """A light seen at a known pixel pins the box to where that aircraft had that az/el."""
    real = A.parse_trace(TRACE)
    X = (61.60, 11.40)
    tc = to_unix("2026-09-21T21:29:40+02:00")
    D = 25.0
    la, lo, al, _ = real.at(tc - D)
    from hordejakt.geo import bearing, elevation_angle
    az = float(bearing(X[0], X[1], la[0], lo[0]))
    el = float(elevation_angle(haversine(X[0], X[1], la[0], lo[0]), al[0] - A.OBSERVER_M))
    clats, clons = A.coarse_axes((61.0, 62.2, 10.4, 12.2))
    CL, CO = np.meshgrid(clats, clons, indexing="ij")
    P = A.light_prob(CL, CO, [real], [(tc, az, el)], np.array([D]), np.array([1.0]))
    i, j = np.argmin(np.abs(clats - X[0])), np.argmin(np.abs(clons - X[1]))
    assert P[i, j] > 0.7
    far = np.argmin(np.abs(clats - 61.1)), np.argmin(np.abs(clons - 10.5))
    assert P[far] < 0.2


# =========================================================================== audio + latency calibration
X_TRUE = (61.40, 11.03)
T0 = 1790000000.0


def straight(hexid, lat, lon, heading, alt_m, gs_kt, t_cpa, offset_km, dur=1200, dt=5):
    cla, clo = destination(lat, lon, (heading + 90) % 360, offset_km)
    ts = np.arange(t_cpa - dur / 2, t_cpa + dur / 2 + 1, dt)
    d = (ts - t_cpa) * gs_kt * A.KT / 1000.0
    la, lo = destination(cla, clo, np.where(d >= 0, heading, (heading + 180) % 360), np.abs(d))
    return A.Track(hexid, hexid.upper(), ts, la, lo, np.full(len(ts), alt_m), np.full(len(ts), gs_kt), source="synthetic")


class StubProvider(A.AdsbProvider):
    name = "stub"

    def __init__(self, tracks):
        self._t = tracks

    def tracks(self, t0, t1, bbox=A.FETCH_BBOX):
        return A.TrackSet([t.window(t0, t1) for t in self._t if t.window(t0, t1) is not None], True, ["stub"])


def synthetic_audio(latency=25.0, noise=2.0, seed=3):
    rng = np.random.default_rng(seed)
    specs = [(0, 2.0, 11000), (40, 6.0, 10500), (95, 4.0, 11500), (160, 9.0, 10000), (220, 3.0, 9000),
             (300, 7.0, 11800), (20, 5.0, 10600)]
    tracks, events = [], []
    for k, (hdg, off, alt) in enumerate(specs):
        tc = T0 + 1800 * k
        tr = straight(f"a{k:05x}", *X_TRUE, hdg, alt, 450, tc, off)
        tracks.append(tr)
        tracks.append(straight(f"d{k:05x}", 60.5, 9.5, (hdg + 90) % 360, 11000, 450, tc + 60, 1.0))  # far distractor
        c = A.audio_cpa(tr, np.array([X_TRUE[0]]), np.array([X_TRUE[1]]), tc - 600, tc + 600)
        events.append({"id": f"e{k}", "t_obs": float(c.t_peak[0] + latency + rng.normal(0, noise))})
    events.append({"id": "clutter", "t_obs": T0 + 1800 * 7 + 400})     # e.g. a car: explained by the floor
    return tracks, events


CANDS = (np.array([X_TRUE[0], 61.2, 61.6, 61.0, 60.8, 61.45]), np.array([X_TRUE[1], 10.7, 11.4, 11.2, 11.0, 10.6]),
         np.array([0.3, 0.15, 0.15, 0.15, 0.1, 0.15]))


def test_audio_event_layer_geometry():
    tracks, events = synthetic_audio()
    tr = tracks[0]                                # heading 0, passes 2 km E of X at T0
    ev = events[0]
    clats, clons = A.coarse_axes((60.6, 62.2, 10.0, 12.2))
    CL, CO = np.meshgrid(clats, clons, indexing="ij")
    Lv, Lw = A.latency_prior()
    cpas = [c for c in (A.audio_cpa(t, CL, CO, ev["t_obs"] - 300, ev["t_obs"] + 30) for t in tracks) if c is not None]
    P = A.audio_prob_from_cpas(cpas, ev["t_obs"], Lv, Lw)
    at = lambda la, lo: P[np.argmin(np.abs(clats - la)), np.argmin(np.abs(clons - lo))]
    # one peak under a flat 15-60 s latency prior matches ~half of the prior mass (sigma_t ~ 14 s)
    assert at(*X_TRUE) > 0.4
    assert at(X_TRUE[0], X_TRUE[1] + 1.2) < 0.15         # ~65 km east: inaudible -> floor 0.1
    assert at(X_TRUE[0] + 0.6, X_TRUE[1]) < 0.15         # under the track 67 km north: CPA ~4.8 min earlier
    # a calibrated latency sharpens the same event
    Lc, Wc = A.latency_prior(calib={"well_determined": True, "latency_s": 25.0, "latency_sigma_s": 3.0})
    P2 = A.audio_prob_from_cpas(cpas, ev["t_obs"], Lc, Wc)
    assert P2[np.argmin(np.abs(clats - X_TRUE[0])), np.argmin(np.abs(clons - X_TRUE[1]))] > 0.7


def test_latency_calibration_recovers_synthetic_latency():
    tracks, events = synthetic_audio(latency=25.0)
    tf = lambda ev: [t for t in tracks if t.t[0] <= ev["t_obs"] + 30 and t.t[-1] >= ev["t_obs"] - 330]
    res = A.calibrate_latency(events, *CANDS, tf)
    assert abs(res["latency_s"] - 25.0) <= 5.0
    assert res["well_determined"] and res["n_matched"] >= 5 and "clutter" not in res["matched"]
    one = A.calibrate_latency(events[:1], *CANDS, tf)
    assert not one["well_determined"]


def test_latency_calibration_through_bridge_skips_loops(tmp_path):
    tracks, events = synthetic_audio(latency=25.0)
    ctx = ctx_for(tmp_path, latency_s=30.0)
    for ev in events[:-1]:
        cap = from_unix(ev["t_obs"])
        ctx.db.add_observation(Observation("audio_aircraft", from_unix(ev["t_obs"] - 30), {"peak_ts": from_unix(ev["t_obs"] - 30).isoformat(), "snr_db": 12},
                                           analyzer="audio", confidence=0.7, ts_capture=cap))
    # a looped (replayed) jet sound at a time that would bias the fit: must be ignored
    bad = events[0]["t_obs"] + 900.0
    ctx.db.add_observation(Observation("audio_aircraft", from_unix(bad - 30), {"snr_db": 30}, analyzer="audio",
                                       ts_capture=from_unix(bad)))
    ctx.db.add_observation(Observation("audio_loop", from_unix(bad - 35), {"ref_ts": "x", "lag_s": 86400, "corr": 0.97},
                                       analyzer="audio_loop"))
    b = A.AircraftBridge({**NO_NET, "providers": [StubProvider(tracks)], "layers_dir": str(tmp_path / "layers"),
                          "cache_dir": str(tmp_path / "cache")})
    res = b.run_calibration(ctx.db, ctx.clock, candidates=CANDS, now=T0 + 86400)
    assert res["n_events"] == 7
    assert abs(res["latency_s"] - 25.0) <= 5.0 and res["well_determined"]
    b.apply_calibration(ctx, res)
    assert abs(ctx.db.calibration("latency_s") - 25.0) <= 5.0
    assert isinstance(ctx.db.calibration("latency_s"), float)              # runner does float(stored)
    assert ctx.clock.latency_s == pytest.approx(ctx.db.calibration("latency_s"))
    assert ctx.db.calibration("latency_calibration")["well_determined"]
    # the calibrated prior is now used for event layers
    v, w = b._latency(ctx)
    assert abs(np.sum(v * w) - res["latency_s"]) < 1.0


def test_audio_event_through_bridge_writes_layer(tmp_path):
    tracks, events = synthetic_audio(latency=25.0)
    ctx = ctx_for(tmp_path)
    ev = events[2]
    ctx.db.add_observation(Observation("audio_aircraft", from_unix(ev["t_obs"] - 30), {"snr_db": 15}, analyzer="audio",
                                       ts_capture=from_unix(ev["t_obs"])))
    b = A.AircraftBridge({**NO_NET, "providers": [StubProvider(tracks)], "layers_dir": str(tmp_path / "layers"),
                          "cache_dir": str(tmp_path / "cache")})
    b.on_tick(ctx)
    (f,) = list((tmp_path / "layers").glob("aircraft_*.npz"))
    ll, meta = read_layer(f)
    assert 0.5 <= meta["reliability"] <= 0.75 and meta["independence_group"].startswith("hw_aircraft_")
    assert ll_at(ll, *X_TRUE) > ll_at(ll, *BERGEN) + 1.0


def test_audio_events_merge_into_daily_joint_layer(tmp_path):
    tracks, events = synthetic_audio(latency=25.0)
    ctx = ctx_for(tmp_path)
    for ev in events[:-1]:
        ctx.db.add_observation(Observation("audio_aircraft", from_unix(ev["t_obs"] - 30), {"snr_db": 15}, analyzer="audio",
                                           ts_capture=from_unix(ev["t_obs"])))
    b = A.AircraftBridge({**NO_NET, "providers": [StubProvider(tracks)], "layers_dir": str(tmp_path / "layers"),
                          "cache_dir": str(tmp_path / "cache"), "audio_daily_threshold": 3})
    b.on_tick(ctx)
    files = sorted(p.name for p in (tmp_path / "layers").glob("*.npz"))
    assert files == ["aircraft_audio_20260921.npz"]                 # 7 events > 3: per-event layers replaced
    ll, meta = read_layer(tmp_path / "layers" / files[0])
    assert meta["n_events"] == 7 and meta["reliability"] == 0.5
    assert meta["independence_group"] == "hw_aircraft_audio_20260921"
    # the joint (shared-latency) layer is far sharper than one event: X beats cells 30 km away
    x = ll_at(ll, *X_TRUE)
    assert x > ll_at(ll, X_TRUE[0] + 0.27, X_TRUE[1]) + 3.0 and x > ll_at(ll, *BERGEN) + 5.0
    i, j = np.unravel_index(np.nanargmax(ll), ll.shape)
    assert haversine(GRID.lats[i], GRID.lons[j], *X_TRUE) < 6.0


# =========================================================================== providers: offline / fail-soft
class FakeResp:
    def __init__(self, obj=None, status=200, content=b""):
        self._o, self.status_code, self.content = obj, status, content
        self.text = content.decode() if content else json.dumps(obj)

    def json(self):
        return self._o


class FakeSession:
    def __init__(self, handler):
        self.h = handler
        self.headers = {}

    def get(self, url, **kw):
        return self.h(url, **kw)


def test_live_recorder_and_record_provider(tmp_path):
    t = 1790018900.0
    calls = {"n": 0}

    def handler(url, **kw):
        calls["n"] += 1
        k = calls["n"]
        return FakeResp({"now": (t + 10 * k) * 1000, "ac": [
            {"hex": "4791ac", "flight": "NOZ9EG", "lat": 61.4 - 0.02 * k, "lon": 10.9, "alt_geom": 26000, "gs": 490,
             "track": 182, "seen_pos": 0.0},
            {"hex": "zzzzzz", "lat": 40.0, "lon": 0.0, "alt_baro": 30000}]})     # outside bbox: dropped
    rec = A.LiveRecorder(tmp_path / "live", sources=["adsb.lol"], centres=[(61.0, 10.0, 250)])
    s = FakeSession(handler)
    for _ in range(12):
        assert rec.poll_once(s)
    prov = A.LiveRecordProvider(tmp_path / "live")
    ts = prov.tracks(t + 20, t + 100)
    assert ts.complete and len(ts.tracks) == 1 and ts.tracks[0].hex == "4791ac"
    assert ts.tracks[0].at(t + 55)[3][0]
    assert prov.hexes(t, t + 100) == ["4791ac"]
    assert not prov.tracks(t + 500, t + 900).complete


def test_network_providers_fail_soft(tmp_path):
    def boom(url, **kw):
        raise ConnectionError("blocked by proxy")
    h = A.AdsbLolHistoryProvider(tmp_path, hexes=["4791ac"])
    h._s = FakeSession(boom)
    ts = h.tracks(T0, T0 + 60)
    assert ts.tracks == [] and not ts.complete
    o = A.OpenSkyProvider(tmp_path)
    o._s = FakeSession(boom)
    assert o.tracks(T0, T0 + 60).tracks == []
    ts = A.resolve_tracks([h, o], T0, T0 + 60)
    assert ts.tracks == [] and not ts.complete
    # trace cache round trip
    day = from_unix(to_unix("2026-09-21T12:00:00Z")).strftime("%Y%m%d")
    (tmp_path / "traces" / day).mkdir(parents=True)
    (tmp_path / "traces" / day / "trace_full_4791ac.json.gz").write_bytes(TRACE.read_bytes())
    tc = A.TraceCacheProvider(tmp_path / "traces").tracks(to_unix("2026-09-21T21:28:00+02:00"), to_unix("2026-09-21T21:30:00+02:00"))
    assert [t.hex for t in tc.tracks] == ["4791ac"]
    # no data at all -> event deferred, not a layer
    b = A.AircraftBridge({**NO_NET, "providers": [h], "layers_dir": str(tmp_path / "L"), "cache_dir": str(tmp_path)})
    ev = {"t_first": T0, "t_last": T0, "id": "x", "kinds": ["gesture_point_up"],
          "obs": [(T0, {"kind": "gesture_point_up", "ts": from_unix(T0), "value": {}, "confidence": 0.5})]}
    assert b.process_event(ev, A.latency_prior())["status"] == "no_data"


# =========================================================================== MET scoring (pure, synthetic grids)
SG = Grid(lat_min=60.0, lat_max=60.5, lon_min=10.0, lon_max=11.0, dlat=0.01, dlon=0.02)   # 51 x 51 met cells
H = to_unix("2026-09-24T12:00:00Z")


def halves(left, right, grid=SG):
    a = np.full(grid.shape, float(right))
    a[:, : grid.nlon // 2] = left
    return a


def test_rain_scoring():
    rate = halves(3.0, 0.0)                         # raining in the west half
    ll_y = M.rain_loglik(True, rate)
    ll_n = M.rain_loglik(False, rate)
    assert ll_y[0, 0] > ll_y[0, -1] + 1.5
    assert ll_n[0, -1] > ll_n[0, 0] + 1.0
    soft = M.soft_loglik(0.5, ll_y, ll_n)
    assert np.ptp(soft) < 0.2                       # undecided observation ~ no information
    # heavy rain needs a real rate: 0.3 mm/h is much less consistent with 'heavy' than with 'light'
    assert M.rain_loglik(True, 0.3, "heavy") < M.rain_loglik(True, 0.3, "light") - 0.5
    assert M.p_rain_given_rate(0.0) < 0.15 and M.p_rain_given_rate(5.0) > 0.95


def test_rain_timing_and_spatial_tolerance():
    wet = np.zeros(SG.shape)
    wet[20, 20] = 4.0
    f = [M.Field("precip_rate_mmh", H - 3600, H, wet, "test")]
    v, _ = M.tolerant_field(f, H + 600, H + 600, "max")         # 10 min after the analysis hour: within +-15 min
    assert v is not None and v[20, 20] == 4.0
    v2, _ = M.tolerant_field(f, H + 2400, H + 2400, "max")      # 40 min after: no product
    assert v2 is None
    sp = M.spatial_tolerance(wet, 1, "max")
    assert sp[21, 21] == 4.0 and sp[23, 23] == 0.0
    both = [f[0], M.Field("precip_rate_mmh", H - 300, H + 300, np.zeros(SG.shape), "radar")]
    lo, _ = M.tolerant_field(both, H, H, "min")
    hi, _ = M.tolerant_field(both, H, H, "max")
    assert lo[20, 20] == 0.0 and hi[20, 20] == 4.0


def test_cloud_sun_fog_condensation_temperature_scoring():
    cloud = halves(0.05, 0.95)
    ll = M.cloud_loglik(0.1, cloud)
    assert ll[0, 0] > ll[0, -1] + 2.0
    noon = to_unix("2026-09-24T11:00:00Z")
    L, O = SG.mesh()
    el = M.solar_elevation(L, O, noon)
    assert 25 < el.mean() < 35
    s_y = M.sun_loglik(True, cloud, el)
    s_n = M.sun_loglik(False, cloud, el)
    assert s_y[0, 0] > s_y[0, -1] + 2.0
    assert (s_n[0, -1] - s_n[0, 0]) < (s_y[0, 0] - s_y[0, -1])   # 'no sun' is weaker evidence (shade)
    night = M.solar_elevation(L, O, to_unix("2026-09-24T22:00:00Z"))
    assert np.isnan(M.sun_loglik(True, cloud, night)).all()
    rh = halves(99.5, 70.0)
    assert M.fog_loglik(True, rh)[0, 0] > M.fog_loglik(True, rh)[0, -1] + 2.0
    assert M.dewpoint_c(10.0, 100.0) == pytest.approx(10.0, abs=0.05)
    assert M.dewpoint_c(20.0, 50.0) == pytest.approx(9.3, abs=0.3)
    c = M.condensation_loglik(True, halves(8.0, 15.0), halves(99.0, 60.0))
    assert c[0, 0] > c[0, -1] + 1.0
    t = halves(8.0, 16.0)
    out = M.temperature_loglik(8.5, t, "outside")
    assert out[0, 0] > out[0, -1] + 2.0
    ins = M.temperature_loglik(14.0, t, "inside")       # 14 inside: 8 outside (+6) fits, 16 outside (-2) less
    assert ins[0, 0] == 0.0 and ins[0, -1] < -0.1
    assert M.decorrelation_factor(1) == 1.0 and M.decorrelation_factor(24) < M.decorrelation_factor(4) < 1.0


def test_weather_bridge_day_layer(tmp_path):
    wet = halves(2.0, 0.0)
    fields = [M.Field("precip_rate_mmh", H - 3600 * (k + 1), H - 3600 * k, wet, "synthetic analysis") for k in range(4)]
    ctx = ctx_for(tmp_path)
    for k in range(12):   # rain seen for ~2 h (10 min steps)
        ctx.db.add_observation(Observation("rain_visual", from_unix(H - 3 * 3600 + 600 * k), {"present": True, "intensity": 0.5},
                                           analyzer="rain", confidence=0.8))
    ctx.db.add_observation(Observation("temperature", from_unix(H - 3600), {"temp_c": 9.0, "where": "outside"}, analyzer="wb"))
    wb = M.WeatherBridge({"providers": [M.ArrayProvider(fields)], "met_grid": SG, "layers_dir": str(tmp_path / "layers"),
                          "lookback_days": 1e5})
    obs = wb.on_tick(ctx)
    f = tmp_path / "layers" / "weather_rain_visual_20260924.npz"
    assert f.exists()
    assert not (tmp_path / "layers" / "weather_temperature_20260924.npz").exists()   # no temperature field -> no layer
    ll, meta = read_layer(f)
    d = np.load(f)
    assert meta["independence_group"] == "hw_weather_rain_20260924" and meta["reliability"] == 0.5
    sub = Grid(lat_min=float(d["lat_min"]), lat_max=float(d["lat_min"]) + (ll.shape[0] - 1) * GRID.dlat,
               lon_min=float(d["lon_min"]), lon_max=float(d["lon_min"]) + (ll.shape[1] - 1) * GRID.dlon)
    assert ll_at(ll, 60.25, 10.1, sub) > ll_at(ll, 60.25, 10.9, sub) + 1.0
    assert [o.kind for o in obs] == ["weather_match"] and obs[0].value["hours"] == 2   # 12 obs span two UTC hours
    assert wb.on_tick(ctx) == []                                     # unchanged -> not rebuilt
    # hordejakt.layers.live pastes the sub-grid at the right place
    from hordejakt.layers import live
    lj = live.build.__globals__
    old = lj["LIVE_DIR"]
    try:
        lj["LIVE_DIR"] = tmp_path / "layers"
        (L,) = live.build(GRID, {})
    finally:
        lj["LIVE_DIR"] = old
    assert ll_at(L.loglik, 60.25, 10.1) > ll_at(L.loglik, 60.25, 10.9) + 1.0
    assert np.isnan(ll_at(L.loglik, *BERGEN))


def test_defaultno_met_fixture_provider():
    p = M.DefaultNoMetFixture()
    g = Grid(lat_min=60.0, lat_max=61.5, lon_min=10.5, lon_max=12.0, dlat=0.01, dlon=0.02)
    t = to_unix(json.loads(p.path.read_text())["tid"])
    (c,) = p.fields("cloud_fraction", t - 60, t + 60, g)
    assert np.nanmax(c.values) <= 1.0 and np.isfinite(c.values).any()
    assert p.fields("cloud_fraction", t + 86400, t + 86500, g) == []


def test_dap_ascii_das_and_netcdf3_regridding():
    txt = ("Dataset {\n Float32 x[x = 3];\n} a;\n---------------------------------------------\n"
           "x[3]\n1.0, 2.0, 3.0\n\nprecipitation_amount.precipitation_amount[1][2][3]\n[0][0], 0.0, 0.5, 1.0\n[0][1], 2.0, NaN, 3.0\n")
    d = M.parse_dap_ascii(txt)
    assert d["x"].tolist() == [1.0, 2.0, 3.0] and d["precipitation_amount"].shape == (1, 2, 3)
    das = 'Attributes {\n precipitation_amount {\n  Float32 scale_factor 0.1;\n  String units "kg/m^2";\n }\n}\n'
    assert M.parse_das(das)["precipitation_amount"] == {"scale_factor": 0.1, "units": "kg/m^2"}
    assert M.RadarProvider.dbz_to_rate(np.array([0.0, 23.0]))[1] == pytest.approx(1.0, rel=0.1)
    # synthetic netCDF-3 in the MET Nordic LCC projection: a wet 1 km cell must land at its lat/lon
    from pyproj import Transformer
    from scipy.io import netcdf_file
    proj = "+proj=lcc +lat_0=63 +lon_0=15 +lat_1=63 +lat_2=63 +R=6371000 +units=m +no_defs"
    tr = Transformer.from_crs("EPSG:4326", proj, always_xy=True)
    x0, y0 = tr.transform(10.0, 60.0)
    x = x0 - 20000 + 1000.0 * np.arange(80)
    y = y0 - 20000 + 1000.0 * np.arange(80)
    wx, wy = tr.transform(10.5, 60.25)
    arr = np.zeros((1, 80, 80), np.float32)
    arr[0, int(round((wy - y[0]) / 1000)), int(round((wx - x[0]) / 1000))] = 5.0
    buf = io.BytesIO()
    f = netcdf_file(buf, "w")
    f.createDimension("time", 1)
    f.createDimension("y", 80)
    f.createDimension("x", 80)
    tv = f.createVariable("time", "f8", ("time",))
    tv[:] = [H]
    tv.units = "seconds since 1970-01-01 00:00:00 +00:00"
    for n, a in (("x", x), ("y", y)):
        v = f.createVariable(n, "f8", (n,))
        v[:] = a
        v.units = "m"
    pl = f.createVariable("projection_lcc", "i4", ())
    pl.proj4 = proj
    pv = f.createVariable("precipitation_amount", "f4", ("time", "y", "x"))
    pv[:] = arr
    pv.grid_mapping = "projection_lcc"
    f.flush()
    data = buf.getvalue()
    f.close()
    (fld,) = M.fields_from_netcdf3(data, {"precipitation_amount": ("precip_rate_mmh", lambda a: a)}, SG, "t",
                                   M.MetNordicProvider.validity)
    assert fld.t_end == H and fld.t_start == H - 3600
    i, j = SG.index(60.25, 10.5)
    assert fld.values[i, j] == 5.0 and np.nansum(fld.values) <= 5.0 * 2


def synthetic_nordic_nc(t_valid, wet_lat=60.25, wet_lon=10.5):
    from pyproj import Transformer
    from scipy.io import netcdf_file
    proj = "+proj=lcc +lat_0=63 +lon_0=15 +lat_1=63 +lat_2=63 +R=6371000 +units=m +no_defs"
    tr = Transformer.from_crs("EPSG:4326", proj, always_xy=True)
    x0, y0 = tr.transform(10.0, 60.0)
    x = x0 - 20000 + 1000.0 * np.arange(80)
    y = y0 - 20000 + 1000.0 * np.arange(80)
    wx, wy = tr.transform(wet_lon, wet_lat)
    buf = io.BytesIO()
    f = netcdf_file(buf, "w")
    for n, k in (("time", 1), ("y", 80), ("x", 80)):
        f.createDimension(n, k)
    tv = f.createVariable("time", "f8", ("time",))
    tv[:] = [t_valid]
    tv.units = "seconds since 1970-01-01 00:00:00 +00:00"
    for n, a in (("x", x), ("y", y)):
        v = f.createVariable(n, "f8", (n,))
        v[:] = a
    pl = f.createVariable("projection_lcc", "i4", ())
    pl.proj4 = proj
    pr = np.zeros((1, 80, 80), np.float32)
    pr[0, int(round((wy - y[0]) / 1000)), int(round((wx - x[0]) / 1000))] = 3.0
    for name, arr in (("precipitation_amount", pr), ("air_temperature_2m", np.full((1, 80, 80), 283.15, np.float32)),
                      ("cloud_area_fraction", np.full((1, 80, 80), 0.25, np.float32)),
                      ("relative_humidity_2m", np.full((1, 80, 80), 0.8, np.float32))):
        v = f.createVariable(name, "f4", ("time", "y", "x"))
        v[:] = arr
        v.grid_mapping = "projection_lcc"
    f.flush()
    data = buf.getvalue()
    f.close()
    return data


def test_met_nordic_provider_with_fake_thredds(tmp_path):
    p = M.MetNordicProvider(tmp_path)
    calls = []

    def fake_ncss(path, variables, bbox, stride, **kw):
        calls.append(path)
        hour = to_unix(datetime.strptime(path.split("_")[-1][:12], "%Y%m%dT%HZ").replace(tzinfo=UTC))
        if path.startswith("metpplatest"):
            raise IOError("HTTP 404")                        # old hours are only in the archive
        return synthetic_nordic_nc(hour)
    p.th.ncss = fake_ncss
    fs = p.fields("precip_rate_mmh", H - 600, H - 300, SG)
    assert fs and all(f.var == "precip_rate_mmh" for f in fs)
    assert any(c.startswith("metpparchive/2026/09/24/met_analysis_1_0km_nordic_20260924T12Z") for c in calls)
    f12 = next(f for f in fs if f.t_end == H)
    i, j = SG.index(60.25, 10.5)
    assert f12.values[i, j] == pytest.approx(3.0)
    t = p.fields("air_temperature_c", H - 600, H - 300, SG)
    assert t[0].values[0, 0] == pytest.approx(10.0, abs=0.01)
    assert p.fields("relative_humidity", H - 600, H - 300, SG)[0].values[0, 0] == pytest.approx(80.0, abs=0.1)
    n = len(calls)
    p2 = M.MetNordicProvider(tmp_path)                       # disk cache: no new requests
    p2.th.ncss = fake_ncss
    assert p2.fields("cloud_fraction", H - 600, H - 300, SG)[0].values[0, 0] == pytest.approx(0.25, abs=1e-3)
    assert len(calls) == n


def test_frost_provider_with_fake_api(tmp_path):
    fp = M.FrostProvider(tmp_path, "client-id")

    def handler(url, params=None, **kw):
        if "sources" in url:
            return FakeResp({"data": [{"id": "SN1", "geometry": {"coordinates": [10.2, 60.2]}},
                                      {"id": "SN2", "geometry": {"coordinates": [10.8, 60.3]}}]})
        return FakeResp({"data": [
            {"sourceId": "SN1:0", "referenceTime": "2026-09-24T12:00:00.000Z", "observations": [{"value": 2.5}]},
            {"sourceId": "SN2:0", "referenceTime": "2026-09-24T12:00:00.000Z", "observations": [{"value": 0.0}]}]})
    fp._s = FakeSession(handler)
    (f,) = fp.fields("precip_rate_mmh", H - 600, H - 300, SG)
    assert f.t_end == H and f.product == "Frost stations"
    assert f.values[SG.index(60.2, 10.2)] == pytest.approx(2.5, abs=0.05)
    assert f.values[SG.index(60.3, 10.8)] == pytest.approx(0.0, abs=0.05)


def test_met_providers_fail_soft(tmp_path):
    p = M.MetNordicProvider(tmp_path)

    def boom(url, **kw):
        raise IOError("blocked")
    p.th.get = boom
    assert p.fields("precip_rate_mmh", H, H + 60, SG) == []
    r = M.RadarProvider(tmp_path)
    r.th.get = boom
    assert r.fields("precip_rate_mmh", H, H + 60, SG) == []
    assert M.FrostProvider(tmp_path, None).fields("precip_rate_mmh", H, H + 60, SG) == []


# =========================================================================== engine bridge
def spots(*pts):
    return [{"lat": a, "lon": b, "p_within_1.5km": 0.01} for a, b in pts]


BASE = [(61.245, 10.87), (61.39, 10.89), (61.155, 10.86), (61.335, 10.95), (61.21, 10.93),
        (61.315, 10.97), (61.34, 11.09), (61.42, 10.98), (61.295, 10.81), (61.375, 10.98)]


def test_compare_rankings():
    same = spots(*BASE)
    assert compare(same, same) == (False, [])
    swapped = spots(BASE[1], BASE[0], *BASE[2:])
    mat, ch = compare(same, swapped)
    assert mat and ch[0]["type"] == "top_moved"          # #1 and #2 are 16 km apart
    promoted = spots(BASE[0], BASE[1], BASE[7], *BASE[2:7], *BASE[8:])
    mat, ch = compare(same, promoted)
    assert mat and ch == [{"type": "new_top_area", "rank": 3, "lat": BASE[7][0], "lon": BASE[7][1],
                           "km_to_prev_top": ch[0]["km_to_prev_top"], "prev_rank": 8, "p_within_1.5km": 0.01}]
    jitter = spots(*[(a + 0.005, b) for a, b in BASE])   # 0.55 km moves: not material
    assert compare(same, jitter)[0] is False
    far = spots(*[(a - 1.0, b) for a, b in BASE])
    mat, ch = compare(same, far)
    assert mat and {c["type"] for c in ch} == {"top_moved", "new_top_area", "reshuffle"}


def compare(a, b):
    return E.compare_rankings(a, b)


def test_engine_bridge_detects_ranking_change(tmp_path):
    ctx = ctx_for(tmp_path)
    runs = [spots(*BASE), spots(*BASE), spots((62.1, 9.5), *BASE[:9]), None]

    def fake_run():
        r = runs.pop(0)
        if r is None:
            raise RuntimeError("engine crashed")
        return {"hotspots": r, "summary": {"credible_km2": {"0.5": 1000.0},
                                           "layers": [{"name": "hw_aircraft_x"}, {"name": "elevation_band_810_891"}]}}
    eb = E.EngineBridge({"run_fn": fake_run, "every_min": 0.0, "history_dir": str(tmp_path / "history"),
                         "layers_dir": str(tmp_path / "layers"), "only_if_changed": False})
    for _ in range(4):
        eb.on_tick(ctx)
    hist = sorted((tmp_path / "history").glob("*_hotspots.json"))
    assert len(hist) == 3
    last = json.loads(hist[-1].read_text())
    assert last["material"] and last["live_layers"] == ["hw_aircraft_x"]
    ev = ctx.db.con.execute("SELECT kind, summary FROM events ORDER BY id").fetchall()
    kinds = [k for k, _ in ev]
    assert kinds == ["engine_ranking_change", "engine_run_failed"]
    assert "62.1000,9.5000" in ev[0][1]
    # restart: previous ranking is reloaded from history
    eb2 = E.EngineBridge({"history_dir": str(tmp_path / "history")})
    assert eb2.load_previous()[0]["lat"] == 62.1


def test_engine_subprocess_path(tmp_path):
    import time as _t
    hot = tmp_path / "hot.json"
    fake = tmp_path / "fakepy"
    payload = {"hotspots": spots(*BASE), "summary": {"credible_km2": {"0.5": 1.0}}}
    fake.write_text(f"#!{sys.executable}\nimport json, sys\nassert sys.argv[1:3] == ['-m', 'hordejakt.cli']\n"
                    f"open({str(hot)!r}, 'w').write(json.dumps({payload!r}))\n")
    fake.chmod(0o755)
    ctx = ctx_for(tmp_path)
    eb = E.EngineBridge({"python": str(fake), "hotspots_path": str(hot), "every_min": 0.0,
                         "history_dir": str(tmp_path / "h"), "layers_dir": str(tmp_path / "layers")})
    eb.on_tick(ctx)
    t0 = _t.time()
    while eb._proc is not None and _t.time() - t0 < 30:
        _t.sleep(0.1)
        eb.on_tick(ctx)
    (h,) = list((tmp_path / "h").glob("*_hotspots.json"))
    assert json.loads(h.read_text())["hotspots"][0]["lat"] == BASE[0][0]
    bad = tmp_path / "badpy"
    bad.write_text(f"#!{sys.executable}\nimport sys\nprint('boom'); sys.exit(3)\n")
    bad.chmod(0o755)
    eb2 = E.EngineBridge({"python": str(bad), "hotspots_path": str(hot), "every_min": 0.0,
                          "history_dir": str(tmp_path / "h2"), "layers_dir": str(tmp_path / "layers")})
    eb2.on_tick(ctx)
    t0 = _t.time()
    while eb2._proc is not None and _t.time() - t0 < 30:
        _t.sleep(0.1)
        eb2.on_tick(ctx)
    row = ctx.db.con.execute("SELECT kind, summary FROM events").fetchone()
    assert row[0] == "engine_run_failed" and "exited with 3" in row[1] and "boom" in row[1]


def test_engine_skips_when_layers_unchanged(tmp_path):
    ctx = ctx_for(tmp_path)
    n = {"runs": 0}

    def fake_run():
        n["runs"] += 1
        return {"hotspots": spots(*BASE), "summary": {}}
    (tmp_path / "layers").mkdir()
    eb = E.EngineBridge({"run_fn": fake_run, "every_min": 0.0, "force_every_min": 60.0,
                         "history_dir": str(tmp_path / "h"), "layers_dir": str(tmp_path / "layers")})
    eb.on_tick(ctx)
    eb.on_tick(ctx)
    assert n["runs"] == 1
    write_layer(tmp_path / "layers" / "x.npz", np.zeros(GRID.shape), name="x", reliability=0.5, independence_group="x")
    eb.on_tick(ctx)
    assert n["runs"] == 2


# =========================================================================== default.no poller
def make_snapshot(root, stamp, files, links=()):
    d = root / stamp
    man = []
    for url, obj in files.items():
        rel = url.split("default.no/")[1] or "index.html"
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        data = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        p.write_bytes(data)
        import hashlib
        man.append({"url": url, "path": rel, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "content_type": ""})
    d.mkdir(parents=True, exist_ok=True)
    (d / "manifest.json").write_text(json.dumps(man))
    (d / "links.txt").write_text("\n".join(sorted(set(links) | set(files))))
    return d


OLD_FILES = {"https://default.no/": b"<html>v1</html>",
             "https://default.no/data/steder.json": {"steder": [{"navn": "Ormsetra", "lat": 61.4, "lon": 11.0},
                                                                {"navn": "Loten", "lat": 60.82, "lon": 11.35}]},
             "https://default.no/data/met.json": {"tid": "a", "punkter": [[60.0, 10.0, 1]]}}
NEW_FILES = {"https://default.no/": b"<html>v1</html>",
             "https://default.no/data/steder.json": {"steder": [{"navn": "Ormsetra", "lat": 61.4, "lon": 11.0},
                                                                {"navn": "Skramstad", "lat": 61.2, "lon": 10.9}]},
             "https://default.no/data/met.json": {"tid": "b", "punkter": [[60.0, 10.0, 1]]},
             "https://default.no/data/fly3.json": {"fly": []}}


def test_defaultno_diff_and_events(tmp_path):
    old = make_snapshot(tmp_path, "20260925T100000Z", OLD_FILES, ["https://default.no/cuts/202609251000_202609251001.mp4"])
    new = make_snapshot(tmp_path, "20260925T103000Z", NEW_FILES,
                        ["https://default.no/cuts/202609251000_202609251001.mp4",
                         "https://default.no/cuts/202609251029_202609251030.mp4"])
    d = DN.diff_snapshots(old, new)
    assert d["ok"] and d["new_files"] == ["https://default.no/data/fly3.json"]
    assert sorted(d["changed_files"]) == ["https://default.no/data/met.json", "https://default.no/data/steder.json"]
    (cut,) = d["new_cuts"]
    assert cut["start_utc"].startswith("2026-09-25T08:29") and cut["end_local"].startswith("2026-09-25T10:30")
    st = d["json_changes"]["https://default.no/data/steder.json"]["lists"]["steder"]
    assert [DN._label(x) for x in st["added"]] == ["Skramstad"] and [DN._label(x) for x in st["removed"]] == ["Loten"]
    evs = DN.diff_events(d)
    kinds = [k for k, _, _ in evs]
    assert kinds.count("defaultno_new_cuts") == 1 and "defaultno_new_files" in kinds
    txt = " | ".join(s for _, s, _ in evs)
    assert "+1 (Skramstad)" in txt and "-1 (Loten)" in txt and "keys changed: tid" in txt
    empty = make_snapshot(tmp_path, "20260925T110000Z", {})
    bad = DN.diff_snapshots(new, empty)
    assert not bad["ok"] and DN.diff_events(bad)[0][0] == "defaultno_fetch_failed"


def test_defaultno_poller_cycle(tmp_path):
    snaps = tmp_path / "snaps"
    make_snapshot(snaps, "20260925T100000Z", OLD_FILES)
    script = tmp_path / "fake_fetch.py"
    script.write_text(
        "import json, sys, hashlib, pathlib\n"
        f"d = pathlib.Path({str(snaps)!r}) / '20260925T103000Z'\n"
        "(d / 'data').mkdir(parents=True, exist_ok=True)\n"
        "data = json.dumps({'steder': [{'navn': 'Skramstad', 'lat': 61.2, 'lon': 10.9}]}).encode()\n"
        "(d / 'data/steder.json').write_bytes(data)\n"
        "(d / 'index.html').write_bytes(b'<html>v1</html>')\n"
        "m = [{'url': 'https://default.no/data/steder.json', 'path': 'data/steder.json', 'sha256': hashlib.sha256(data).hexdigest()},\n"
        "     {'url': 'https://default.no/', 'path': 'index.html', 'sha256': hashlib.sha256(b'<html>v1</html>').hexdigest()}]\n"
        "(d / 'manifest.json').write_text(json.dumps(m))\n"
        "(d / 'links.txt').write_text('https://default.no/cuts/202609251029_202609251030.mp4')\n")
    ctx = ctx_for(tmp_path)
    p = DN.DefaultNoPoller({"cmd": [sys.executable, str(script)], "snapshots_dir": str(snaps), "async": False, "every_min": 0})
    # establish the baseline from the existing snapshot first
    evs = p.process_new(ctx)
    assert evs[0][0] == "defaultno_snapshot"
    p.on_tick(ctx)
    kinds = [k for (k,) in ctx.db.con.execute("SELECT kind FROM events ORDER BY id")]
    assert kinds[0] == "defaultno_snapshot" and "defaultno_new_cuts" in kinds and "defaultno_data_changed" in kinds
    assert ctx.db.calibration("bridge_state:defaultno_poller")["baseline"] == "20260925T103000Z"
    # a run that produces nothing new -> fetch_failed, baseline kept
    p2 = DN.DefaultNoPoller({"cmd": [sys.executable, "-c", "pass"], "snapshots_dir": str(snaps), "async": False, "every_min": 0})
    p2.on_tick(ctx)
    assert ctx.db.con.execute("SELECT kind FROM events ORDER BY id DESC LIMIT 1").fetchone()[0] == "defaultno_fetch_failed"
