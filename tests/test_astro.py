"""Tests for hordewatch.astro (ephemeris, camera, sun track, twilight, stars, bridge).

Synthetic observations are generated with skyfield's *own* topocentric alt/az (and its
refraction), independently of hordewatch.astro.ephem, then projected through a simulated
camera: heading 220 deg, pitch 2 deg, roll -1 deg, f = 1000 px, 1280x720 at 61.30 N 10.95 E.

Accuracies achieved (and asserted) - see solver.py / camera.py for why:
* sun track, no level reference: the likelihood is flat (< 2 nats over 500 x 350 km) - the
  exact rotation degeneracy - while the camera's Earth-fixed orientation is recovered to 0.05 deg
  and f to 0.5 %.
* sun track + level calibration good to 0.15 deg (offset ~0.5 sigma): MAP 11 km from truth (< 30 asserted).
* sun track + 30 tree trunks (1 deg lean each): ridge along the viewing azimuth, sigma ~70 x 22 km;
  across-track error < 30 km, truth within 2 nats of the maximum.
* moon track (23/24 Sept, 23 points, 2 px) + the same calibration: 14 km; ignoring parallax: ~96 km off.
* twilight, h0 = -3 deg, 2-min noise, 3 days: MAP longitude within 0.25 deg (< 0.3 asserted); posterior
  longitude sigma ~1.4 deg because a dusk/dawn asymmetry is allowed; latitude essentially unconstrained.
* 40 catalogue stars at 2026-09-22 23:00 UTC + 5 spurious points: all identified, rms < 1 px;
  with a level calibration good to 0.1 deg the MAP is ~3 km from the truth (< 0.2 deg asserted).

Adversarial review tests (bottom of the file) - none of them gives the solver the truth:
* level bias +0.5 deg pitch / roll -> fix moves 58 km towards 218 deg / 53 km towards 307 deg (sign conventions);
* a cloudy day (7 sun points) on a static camera is not a pose jump (was: 12/12 false jumps), a real 0.8 deg
  bump seen in 8 points is, and a < 6-point session after a bump joins the bumped pose;
* camera bumped 1 deg, calibration measured after the bump: 10 km (was: 59 km off with sigma 11 km);
* live twilight extraction in 10-min ticks: one dusk marker per threshold (was: two, 17:13 and 19:39), none
  for an ambiguous evening, no evening 'dawn' from a flapping IR switch;
* sun track + 3 simulated hanging cords + 2 families of box edges (box tilted 0.15 deg), through the bridge:
  8-14 km, sigma ~20 x 12 km; a NaN sun pixel no longer kills the layer; recomputes do not re-post alerts;
* 60 automatic lines are capped at a combined 1.0 deg level reference (would claim 0.32 deg = 35 km).
"""
import json
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from hordejakt.geo import bearing, haversine
from hordewatch.astro import ephem
from hordewatch.astro import stars as st
from hordewatch.astro import twilight as tw
from hordewatch.astro.camera import (CameraModel, attitude_from_rotation, detect_vertical_segments,
                                     horizontal_family_residuals, rotation_matrix, vertical_residuals)
from hordewatch.astro.solver import (AstroBridge, CelestialPoints, FitOptions, LevelReference, coarse_grid,
                                     solve_celestial, summarize)

UTC = timezone.utc
LAT, LON = 61.30, 10.95
CAM = CameraModel(220.0, 2.0, -1.0, 1000.0, 1280, 720)
DOMAIN = (59.0, 63.5, 7.0, 14.0)
LATS, LONS = coarse_grid(DOMAIN, 0.1, 0.2)
MET = dict(temperature_C=8.0, pressure_mbar=955.0)          # = FitOptions defaults
STAR_TIME = datetime(2026, 9, 22, 23, 0, tzinfo=UTC)


def sky_altaz(target, times, lat=LAT, lon=LON):
    """Independent reference: skyfield topocentric apparent alt/az with refraction."""
    from skyfield.api import wgs84
    ts, eph = ephem._skyfield()
    obs = eph["earth"] + wgs84.latlon(lat, lon, 500.0)
    t = ts.from_datetimes(times) if isinstance(times, list) else ts.from_datetime(times)
    body = eph[target] if isinstance(target, str) else target
    alt, az, _ = obs.at(t).observe(body).apparent().altaz(**MET)
    return az.degrees, alt.degrees


@pytest.fixture(scope="module")
def sun_obs():
    """Sun pixels every 5 min whenever the sun is in view, 21-23 Sept, 2 px noise."""
    times = [datetime(2026, 9, 21, 4, tzinfo=UTC) + timedelta(minutes=5 * k) for k in range(12 * 24 * 3)]
    az, alt = sky_altaz("sun", times)
    x, y, ins = CAM.project_altaz(az, alt)
    ok = np.nonzero(ins & (alt > 1.0))[0]
    rng = np.random.default_rng(1)
    return [times[i] for i in ok], x[ok] + rng.normal(0, 2, len(ok)), y[ok] + rng.normal(0, 2, len(ok))


def sun_points(sun_obs):
    t, x, y = sun_obs
    return CelestialPoints.from_places(ephem.body_places("sun", t), x, y, 1280, 720, "sun")


def map_error(ll, lats=LATS, lons=LONS):
    i, j = np.unravel_index(np.nanargmax(ll), ll.shape)
    return float(haversine(lats[i], lons[j], LAT, LON)), float(lats[i]), float(lons[j])


def ll_drop_at_truth(ll):
    return float(np.nanmax(ll) - ll[np.argmin(abs(LATS - LAT)), np.argmin(abs(LONS - LON))])


# ----------------------------------------------------------------------------- ephemeris / camera
def test_ephemeris_matches_skyfield_topocentric():
    times = [datetime(2026, 9, 21, 12, tzinfo=UTC) + timedelta(hours=1.7 * k) for k in range(15)]
    from skyfield.api import wgs84
    ts, eph = ephem._skyfield()
    for body, tol in (("sun", 2e-4), ("moon", 5e-4)):
        pl = ephem.body_places(body, times)
        az, alt = ephem.altaz_grid(pl, [LAT, 58.2], [LON, 5.0], height_m=500.0)
        for k, (la, lo) in enumerate([(LAT, LON), (58.2, 5.0)]):
            a, z, _ = (eph["earth"] + wgs84.latlon(la, lo, 500.0)).at(ephem.sf_time(times)).observe(eph[body]).apparent().altaz()
            d = np.hypot(a.degrees - alt[k], ((z.degrees - az[k] + 180) % 360 - 180) * np.cos(np.radians(alt[k])))
            assert d.max() < tol, (body, d.max())
    # the Moon's parallax is ~1 deg: geocentric and topocentric directions must differ that much
    pl = ephem.body_places("moon", times[:1])
    r, T = ephem.observer_frame(np.array([LAT]), np.array([LON]))
    geo = np.einsum("cij,nj->cni", T, pl.e_ef())[0, 0]
    topo = ephem.topocentric_enu(pl.e_ef(), pl.dist_km, r, T)[0, 0]
    assert 0.3 < np.degrees(np.arccos(np.clip(geo @ topo, -1, 1))) < 1.1
    # refraction agrees with skyfield's (Bennett) within 0.1' above 3 deg
    from skyfield.earthlib import refract
    h = np.array([3.0, 5.0, 10.0, 30.0])
    assert np.all(np.abs(ephem.refraction_deg(h, 1010, 10) - (refract(h, 10.0, 1010.0) - h)) * 60 < 0.1)


def test_camera_model_roundtrips_and_level_constraints():
    R = rotation_matrix([220, 10, 359], [2, -30, 5], [-1, 20, 0.3])
    h, p, r = attitude_from_rotation(R)
    assert np.allclose(h, [220, 10, 359]) and np.allclose(p, [2, -30, 5]) and np.allclose(r, [-1, 20, 0.3])
    x, y, ins = CAM.project_altaz(220.0, 2.0)
    assert ins and abs(x - 640) < 1e-9 and abs(y - 360) < 1e-9
    az, alt = CAM.unproject(np.array([100.0, 900.0]), np.array([50.0, 600.0]))
    x2, y2, _ = CAM.project_altaz(az, alt)
    assert np.allclose(x2, [100, 900]) and np.allclose(y2, [50, 600])
    # positive roll lifts the camera's right side: the horizon slopes down to the right
    tilted = CameraModel(220, 0, 5, 1000)
    assert tilted.project_altaz(250, 0)[1] > tilted.project_altaz(190, 0)[1]
    # a plumb line seen by the true camera: zero residual; with a 1 deg roll error: ~1 deg
    base = np.array([np.sin(np.radians(230)), np.cos(np.radians(230)), -0.3]) * 5
    p1, p2 = CAM.project_enu(base), CAM.project_enu(base + [0, 0, 3])
    seg = np.array([[p1[0], p1[1], p2[0], p2[1]]])
    assert abs(vertical_residuals(seg, CAM.R, 1000, 640, 360)[0]) < 1e-9
    assert abs(np.degrees(vertical_residuals(seg, rotation_matrix(220, 2, 0), 1000, 640, 360)[0])) == pytest.approx(1.0, abs=0.1)
    # level-line families: a family along the view axis measures pitch, across it roll, neither heading
    def family(direction_az, centre_az):
        # (edges must not lie in a plane through the camera centre: then the vanishing direction is undefined)
        d = np.array([np.sin(np.radians(direction_az)), np.cos(np.radians(direction_az)), 0.0])
        c = np.array([np.sin(np.radians(centre_az)), np.cos(np.radians(centre_az)), 0]) * 4
        out = []
        for hgt in (-1.2, 0.3):
            a, b = CAM.project_enu(c + [0, 0, hgt] - 0.75 * d), CAM.project_enu(c + [0, 0, hgt] + 0.75 * d)
            out.append([a[0], a[1], b[0], b[1]])
        return np.array(out)
    along, across = family(40, 232), family(130, 220)
    res = lambda fam, att: float(np.degrees(horizontal_family_residuals(fam, rotation_matrix(*att), 1000, 640, 360)))
    assert res(along, (220, 2, -1)) < 1e-6 and res(across, (220, 2, -1)) < 1e-6
    assert res(along, (220, 3, -1)) == pytest.approx(1.0, abs=0.02) and res(across, (220, 3, -1)) < 0.02
    assert res(across, (220, 2, 0)) == pytest.approx(1.0, abs=0.02) and res(along, (200, 2, -1)) < 1e-6


def test_detect_vertical_segments_on_synthetic_trunks():
    import cv2
    img = np.full((720, 1280, 3), 200, np.uint8)
    for x in (200, 500, 900):
        cv2.line(img, (x, 50), (x + 20, 650), (30, 30, 30), 9)          # trunks leaning 1.9 deg in the image
    cv2.line(img, (100, 300), (1100, 420), (30, 30, 30), 5)             # a branch: not vertical
    segs = detect_vertical_segments(img)
    assert len(segs) == 3
    tilt = np.degrees(np.arctan2(segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1]))
    assert np.all(np.abs(tilt - 1.9) < 0.5)


# ----------------------------------------------------------------------------- sun track
def test_sun_track_without_level_reference_is_degenerate(sun_obs):
    """Heading, pitch and roll free: any site fits equally well (exact rotation degeneracy)."""
    sol = solve_celestial(sun_points(sun_obs), LevelReference(pitch=None, roll=None, source="none"), FitOptions(),
                          LATS, LONS, 61.25, 9.0)
    ref, ll = sol["ref"], sol["ll"]
    assert ref.n >= 60 and ref.n_rejected == 0 and ref.rms_px < 3.5
    assert abs(np.exp(ref.p[ref.lay.lnf]) * 1280 - 1000.0) < 5.0            # focal length to 0.5 %
    # the Earth-fixed orientation G is exact: seen from the true site it is the true attitude
    _, T = ephem.observer_frame(LAT, LON)
    h, p, r = attitude_from_rotation(ref.G[0] @ T.T)
    assert abs(h - 220) < 0.05 and abs(p - 2) < 0.05 and abs(r + 1) < 0.05
    assert np.nanmax(ll) - np.nanmin(ll) < 2.0                              # ... but no location information
    assert summarize(LATS, LONS, ll)["info_bits"] < 0.1


def test_sun_track_with_level_calibration_within_30km(sun_obs):
    lev = LevelReference(pitch=(2.08, 0.15), roll=(-1.07, 0.15), source="config calibration")
    ll = solve_celestial(sun_points(sun_obs), lev, FitOptions(), LATS, LONS, 61.25, 9.0)["ll"]
    err, _, _ = map_error(ll)
    assert err < 30.0                                                        # achieved: ~11 km
    assert ll_drop_at_truth(ll) < 3.0
    assert summarize(LATS, LONS, ll)["sigma_km"] < 40.0


def test_sun_track_with_tree_trunks_gives_ridge_along_view_azimuth(sun_obs):
    rng = np.random.default_rng(100)
    segs = []
    for _ in range(30):                          # trunks 4-15 m away, 1 deg random lean each
        az0, dist = 220 + rng.uniform(-30, 30), rng.uniform(4, 15)
        lean_az, lean = rng.uniform(0, 360), rng.normal(0, 1.0)
        base = np.array([np.sin(np.radians(az0)), np.cos(np.radians(az0)), 0.0]) * dist + [0, 0, -1.5]
        d = np.array([np.sin(np.radians(lean)) * np.sin(np.radians(lean_az)),
                      np.sin(np.radians(lean)) * np.cos(np.radians(lean_az)), np.cos(np.radians(lean))])
        (x1, y1, _), (x2, y2, _) = CAM.project_enu(base), CAM.project_enu(base + 4 * d)
        segs.append([x1 / 1280 - 0.5, (y1 - 360) / 1280, x2 / 1280 - 0.5, (y2 - 360) / 1280])
    pts = sun_points(sun_obs)
    lev = LevelReference(segments=np.array(segs), seg_sigma=np.full(30, np.radians(1.0)), seg_t=np.full(30, pts.t[0]),
                         seg_pose=np.zeros(30, int), source="30 trunks")
    ll = solve_celestial(pts, lev, FitOptions(), LATS, LONS, 61.25, 9.0)["ll"]
    s = summarize(LATS, LONS, ll)
    err, la, lo = map_error(ll)
    across = err * np.sin(np.radians(bearing(LAT, LON, la, lo) - 220.0))
    assert abs(across) < 30.0                                   # roll from plumb lines is good ...
    assert s["sigma_major_km"] > 2 * s["sigma_minor_km"]        # ... pitch (along the view axis) is not
    assert abs(((s["major_axis_bearing_deg"] - 40.0) + 90) % 180 - 90) < 20
    assert ll_drop_at_truth(ll) < 2.0


def test_camera_jump_is_detected(sun_obs):
    t, x, y = sun_obs
    bumped = CameraModel(221.0, 2.0, -1.0, 1000.0)              # camera panned 1 deg on 23 Sept
    late = np.array([tt.day == 23 for tt in t])
    az, alt = sky_altaz("sun", [tt for tt, m in zip(t, late) if m])
    xb, yb, ins = bumped.project_altaz(az, alt)
    keep = np.r_[np.ones((~late).sum(), bool), ins]
    xs = np.r_[x[~late], xb][keep]
    ys = np.r_[y[~late], yb][keep]
    ts = [tt for tt, m in zip(t, late) if not m] + [tt for tt, m in zip(t, late) if m]
    ts = [tt for tt, k in zip(ts, keep) if k]
    pts = CelestialPoints.from_places(ephem.body_places("sun", ts), xs, ys, 1280, 720, "sun")
    lev = LevelReference(pitch=(2.0, 0.15), roll=(-1.0, 0.15), source="config")
    sol = solve_celestial(pts, lev, FitOptions(), LATS, LONS, 61.25, 9.0)
    assert sol["fitter"].S == 2 and len(sol["ref"].jumps) == 1
    assert sol["ref"].rms_px < 3.5
    assert map_error(sol["ll"])[0] < 30.0


def test_moon_track_with_parallax(sun_obs):
    """Moon in the SW sky on the nights of 23/24 Sept; parallax (~0.5-1 deg) must be modelled."""
    times = [datetime(2026, 9, 23, 21, tzinfo=UTC) + timedelta(minutes=10 * k) for k in range(6 * 5)]
    az, alt = sky_altaz("moon", times)
    x, y, ins = CAM.project_altaz(az, alt)
    ok = np.nonzero(ins & (alt > 1.0))[0]
    rng = np.random.default_rng(5)
    pl = ephem.body_places("moon", [times[i] for i in ok])
    pts = CelestialPoints.from_places(pl, x[ok] + rng.normal(0, 2, len(ok)), y[ok] + rng.normal(0, 2, len(ok)),
                                      1280, 720, "moon")
    assert len(pts) >= 15
    lev = LevelReference(pitch=(2.05, 0.15), roll=(-1.05, 0.15), source="config calibration")
    sol = solve_celestial(pts, lev, FitOptions(), LATS, LONS, 61.25, 9.0)
    assert sol["ref"].rms_px < 3.5 and map_error(sol["ll"])[0] < 30.0
    # treating the Moon like a star (no parallax) is a *silent* error: the camera rotation absorbs most
    # of it (rms 2.5 vs 2.4 px) but the site moves by ~100 km
    far = CelestialPoints(**{**pts.__dict__, "dist_km": np.full(len(pts), np.inf)})
    bad = solve_celestial(far, lev, FitOptions(), LATS, LONS, 61.25, 9.0)
    assert map_error(bad["ll"])[0] > 60.0


def test_shadow_helper_recovers_sun_azimuth_geometry():
    from hordewatch.astro.camera import ground_direction_azimuth
    from hordewatch.astro.solver import shadow_loglik
    times = [datetime(2026, 9, 22, 11, tzinfo=UTC) + timedelta(minutes=40 * k) for k in range(6)]
    az, alt = sky_altaz("sun", times)
    shadows = []
    for t, a in zip(times, az):
        p0 = np.array([np.sin(np.radians(225)), np.cos(np.radians(225)), 0.0]) * 5 + [0, 0, -1.5]
        d = np.array([np.sin(np.radians(a + 180)), np.cos(np.radians(a + 180)), 0.0])
        (x0, y0, _), (x1, y1, _) = CAM.project_enu(p0), CAM.project_enu(p0 + 0.6 * d)
        ang = np.degrees(np.arctan2(y1 - y0, x1 - x0))
        got, ok = ground_direction_azimuth(np.array([x0]), np.array([y0]), ang, CAM.R, 1000.0, 640.0, 360.0)
        assert ok[0] and abs(((got[0] - (a + 180)) + 180) % 360 - 180) < 0.01
        shadows.append({"t": t.timestamp(), "x": x0 / 1280 - 0.5, "y": (y0 - 360) / 1280, "angle_deg_image": ang})
    # per-cell camera attitude from the Earth-fixed orientation (as the sun track provides it)
    _, T0 = ephem.observer_frame(LAT, LON)
    G = CAM.R @ T0
    L, O = np.meshgrid(LATS, LONS, indexing="ij")
    _, T = ephem.observer_frame(L.ravel(), O.ravel())
    R_cells = np.einsum("ij,ckj->cik", G, T)
    ll = shadow_loglik(shadows, L.ravel(), O.ravel(), R_cells, 1000.0 / 1280, sigma_deg=3.0).reshape(L.shape)
    assert ll_drop_at_truth(ll) < 1.0


# ----------------------------------------------------------------------------- twilight
def crossing_times(h0, lat=LAT, lon=LON, start=datetime(2026, 9, 21, 12, tzinfo=UTC), days=3):
    """Times when the sun's geometric (unrefracted) altitude crosses h0, from skyfield."""
    times = [start + timedelta(minutes=k) for k in range(days * 1440)]
    from skyfield.api import wgs84
    ts, eph = ephem._skyfield()
    a, _, _ = (eph["earth"] + wgs84.latlon(lat, lon, 0.0)).at(ts.from_datetimes(times)).observe(eph["sun"]).apparent().altaz()
    h = a.degrees - h0
    out = []
    for i in np.nonzero(np.sign(h[:-1]) != np.sign(h[1:]))[0]:
        f = h[i] / (h[i] - h[i + 1])
        out.append((times[i] + timedelta(seconds=60 * f), "dusk" if h[i] > 0 else "dawn"))
    return out


def test_twilight_recovers_longitude():
    rng = np.random.default_rng(7)
    mk = [{"t": t + timedelta(seconds=rng.normal(0, 120)), "event": e, "series": "sky_luma_20"}
          for t, e in crossing_times(-3.0)]
    assert len(mk) == 6
    lons = np.arange(7.0, 14.0 + 1e-9, 0.05)                                  # twilight is cheap: finer longitudes
    L, O = np.meshgrid(LATS, lons, indexing="ij")
    r = tw.twilight_loglik(mk, L.ravel(), O.ravel(), latency_sigma_s=15.0)
    ll = r.loglik.reshape(L.shape)
    _, la, lo = map_error(ll, LATS, lons)
    assert abs(lo - LON) < 0.3                                                # achieved: 0.20 deg (this seed)
    assert abs(r.best["h0"]["sky_luma_20"] + 3.0) < 1.0
    s = summarize(LATS, lons, ll)
    assert abs(s["lon"] - LON) < 1.0                                          # posterior mean
    assert s["major_axis_bearing_deg"] < 20 or s["major_axis_bearing_deg"] > 160   # latitude: weak (N-S ridge)


def test_twilight_marker_extraction_from_luma_series():
    start = datetime(2026, 9, 21, 12, tzinfo=UTC)
    times = [start + timedelta(minutes=k) for k in range(36 * 60)]
    from skyfield.api import wgs84
    ts, eph = ephem._skyfield()
    a, _, _ = (eph["earth"] + wgs84.latlon(LAT, LON, 0.0)).at(ts.from_datetimes(times)).observe(eph["sun"]).apparent().altaz()
    h = a.degrees
    rng = np.random.default_rng(3)
    luma = np.clip(200 * 10 ** (0.35 * (h - 2.0)), 1.0, 230) * rng.lognormal(0, 0.03, len(h))   # auto-exposure plateau
    samples = [(t + timedelta(seconds=s), float(v)) for t, v in zip(times, luma) for s in (0, 20, 40)]
    mk = tw.extract_markers(samples, [50.0, 12.0], approx=(61.25, 9.0))
    assert {(m["series"], m["event"]) for m in mk} == {("sky_luma_50", "dusk"), ("sky_luma_50", "dawn"),
                                                       ("sky_luma_12", "dusk"), ("sky_luma_12", "dawn")}
    truth = {50.0: crossing_times(2.0 + np.log10(50 / 200) / 0.35, days=2),
             12.0: crossing_times(2.0 + np.log10(12 / 200) / 0.35, days=2)}
    for m in mk:
        best = min(abs(m["t"] - t.timestamp()) for t, e in truth[m["threshold"]] if e == m["event"])
        assert best < 120, (m, best)
    # IR switches -> markers
    ir = [(t, bool(hh < -2.0)) for t, hh in zip(times, h)]
    irm = tw.ir_switch_markers(ir, approx=(61.25, 9.0))
    assert [m["event"] for m in irm] == ["dusk", "dawn", "dusk"]          # 36 h: two evenings, one morning


# ----------------------------------------------------------------------------- stars
@pytest.fixture(scope="module")
def star_field():
    """40 brightest catalogue stars in view at 2026-09-22 23:00 UTC (0.5 px noise) + 5 spurious points."""
    from skyfield.api import Star
    cat = st.load_catalogue()
    star = Star(ra_hours=cat.ra / 15, dec_degrees=cat.dec, ra_mas_per_year=cat.pmra, dec_mas_per_year=cat.pmdec)
    az, alt = sky_altaz(star, STAR_TIME)
    x, y, ins = CAM.project_altaz(az, alt)
    ok = np.nonzero(ins & (alt > 0.5))[0]
    ok = ok[np.argsort(cat.vmag[ok])][:40]
    rng = np.random.default_rng(3)
    flux = 10 ** (-0.4 * cat.vmag[ok]) * rng.lognormal(0, 0.2, len(ok))
    P = np.c_[x[ok] + rng.normal(0, 0.5, 40), y[ok] + rng.normal(0, 0.5, 40), flux]
    spur = np.c_[rng.uniform(0, 1280, 5), rng.uniform(0, 720, 5), np.median(flux) * rng.uniform(0.3, 2, 5)]
    perm = rng.permutation(45)
    return np.r_[P, spur][perm], np.r_[cat.hip[ok], -np.ones(5, int)][perm]


def test_catalogue_is_real_hipparcos_data():
    cat = st.load_catalogue()
    assert len(cat) > 1500 and len(st.load_catalogue(3.55)) >= 300
    vega = int(np.nonzero(cat.name == "Vega")[0][0])
    assert cat.hip[vega] == 91262 and abs(cat.ra[vega] - 279.2347) < 0.001 and abs(cat.dec[vega] - 38.7837) < 0.001
    assert cat.name[0] == "Sirius" and np.all(np.diff(cat.vmag) >= 0)


def test_star_matcher_identifies_field_and_recovers_site(star_field):
    P, truth_hip = star_field
    approx = st.ApproxCamera.from_attitude(220, 0, 0, 0.5 / np.tan(np.radians(35)), 61.25, 9.0)   # config guess
    fm = st.match_frame(np.c_[P[:, 0] / 1280, P[:, 1] / 1280, P[:, 2]], STAR_TIME, approx)
    assert fm is not None and fm.method == "triangles"
    hip = st.load_catalogue().hip
    correct = sum(truth_hip[d] == hip[c] for d, c in fm.pairs)
    assert correct >= 38 and correct == len(fm.pairs)                         # no false identifications
    assert fm.rms * 1280 < 1.0 and abs(fm.f * 1280 - 1000) < 5
    plate = st.plate_summary(fm, 1280, 720 / 1280)
    assert plate["n_matched"] == len(fm.pairs) and 190 < plate["scale_arcsec_px"] < 220
    pts = CelestialPoints.from_places(fm.places, fm.X * 1280, fm.Y * 1280, 1280, 720, "star")
    lev = LevelReference(pitch=(2.05, 0.1), roll=(-1.05, 0.1), source="config calibration")
    ll = solve_celestial(pts, lev, FitOptions(pixel_sigma_prior=1.0), LATS, LONS, 61.25, 9.0)["ll"]
    err, la, lo = map_error(ll)
    assert abs(la - LAT) < 0.2 and abs(lo - LON) < 0.2                        # achieved: ~3 km
    # the same field with only the default (weak) level prior must not claim a tight fix at a wrong place
    ll0 = solve_celestial(pts, LevelReference(), FitOptions(pixel_sigma_prior=1.0), LATS, LONS, 61.25, 9.0)["ll"]
    assert ll_drop_at_truth(ll0) < 3.0


def test_star_matcher_rejects_random_fields():
    approx = st.ApproxCamera.from_attitude(220, 0, 0, 0.5 / np.tan(np.radians(35)), 61.25, 9.0)
    for seed in range(3):
        r = np.random.default_rng(seed)
        P = np.c_[r.uniform(0, 1, 40), r.uniform(0, 0.5625, 40), r.lognormal(0, 1, 40)]
        assert st.match_frame(P, STAR_TIME, approx) is None


def test_astrometry_wrapper_fails_soft(tmp_path, monkeypatch):
    from astropy.io import fits
    p = st.write_xyls(tmp_path / "f.xyls", np.array([[10.0, 20.0], [30.0, 40.0]]), [5.0, 3.0], 1280, 720)
    with fits.open(p) as h:
        assert list(h[1].data["X"]) == [11.0, 31.0] and h[1].header["IMAGEW"] == 1280
    monkeypatch.setattr(st.shutil, "which", lambda name: None)
    assert st.astrometry_solve(np.zeros((5, 2)), np.ones(5), 1280, 720) is None


# ----------------------------------------------------------------------------- bridge end to end
def test_bridge_end_to_end(tmp_path, monkeypatch, sun_obs, star_field):
    from hordejakt.grid import GRID
    from hordejakt.layers import live
    from hordewatch.analyzers.base import Context
    from hordewatch.db import DB
    from hordewatch.types import Observation, StreamClock

    db = DB(tmp_path / "hw.sqlite")
    t, x, y = sun_obs
    for tt, xx, yy in zip(t, x, y):
        if tt.day == 21:
            db.add_observation(Observation("sun_pixel", tt, {"x": xx, "y": yy, "radius": 8, "saturated": True,
                                                              "w": 1280, "h": 720}, "sun"))
    rng = np.random.default_rng(11)
    for tt, e in crossing_times(-3.0):
        db.add_observation(Observation("twilight_marker", tt + timedelta(seconds=rng.normal(0, 60)),
                                       {"event": e, "series": "ir_switch", "method": "ir_mode"}, "test"))
    P, _ = star_field
    db.add_observation(Observation("star_field", STAR_TIME, {"n_stars": len(P), "points": P.tolist(), "w": 1280,
                                                             "h": 720}, "night"))
    db.set_calibration("camera_attitude", {"pitch_deg": 2.05, "pitch_sigma_deg": 0.15, "roll_deg": -1.05,
                                           "roll_sigma_deg": 0.15, "method": "test plumb calibration"})
    cfg = {"layers_dir": str(tmp_path / "layers"), "domain": [59.8, 62.8, 8.0, 14.0], "coarse_dlat": 0.2,
           "coarse_dlon": 0.4, "threaded": False, "auto_verticals": False,
           "_global": {"camera": {"heading_deg": 220.0, "pitch_deg": 0.0, "roll_deg": 0.0, "hfov_deg": 70.0}}}
    bridge = AstroBridge(cfg)
    assert bridge.available()
    ctx = Context(db=db, config={}, clock=StreamClock())
    out = bridge.on_tick(ctx)
    for o in out:
        db.add_observation(o)
    fixes = {o.value["method"]: o for o in out if o.kind == "astro_fix"}
    assert set(fixes) == {"sun_track", "stars", "twilight"}
    assert any(o.kind == "plate_solution" and o.value["n_matched"] >= 38 for o in out)
    assert haversine(fixes["sun_track"].value["lat_map"], fixes["sun_track"].value["lon_map"], LAT, LON) < 40
    assert haversine(fixes["stars"].value["lat_map"], fixes["stars"].value["lon_map"], LAT, LON) < 30
    assert abs(fixes["twilight"].value["lon_map"] - LON) < 0.5
    cam = db.calibration("astro_camera")
    assert cam and len(cam["G"]) == 1
    assert db.con.execute("SELECT COUNT(*) FROM events").fetchone()[0] >= 3
    assert bridge.on_tick(ctx) == []                          # nothing new -> nothing recomputed
    # the engine's live layer loader picks the files up unchanged
    monkeypatch.setattr(live, "LIVE_DIR", tmp_path / "layers")
    layers = {L.name: L for L in live.build(GRID, {})}
    assert set(layers) == {"astro_sun_track", "astro_stars", "astro_twilight"}
    assert layers["astro_stars"].independence_group == layers["astro_sun_track"].independence_group == "astro_attitude"
    assert layers["astro_twilight"].independence_group == "astro_twilight"
    assert layers["astro_stars"].reliability == pytest.approx(0.8)
    assert 0.3 <= layers["astro_twilight"].reliability <= 0.4 and 0.5 <= layers["astro_sun_track"].reliability <= 0.7
    for L in layers.values():
        assert L.loglik.shape == GRID.shape
        i, j = GRID.index(LAT, LON)
        assert np.isfinite(L.loglik[i, j]) and np.isnan(L.loglik[0, 0])
        assert np.isfinite(L.robust()).any()
    meta = json.loads(str(np.load(tmp_path / "layers" / "astro_stars.npz")["meta"]))
    assert "level reference" in meta["description"] and meta["fix"]["sigma_km"] > 0


def test_bridge_threaded_and_marker_extraction(tmp_path):
    from hordewatch.analyzers.base import Context
    from hordewatch.db import DB
    from hordewatch.types import StreamClock

    db = DB(tmp_path / "hw.sqlite")
    start = datetime(2026, 9, 21, 15, tzinfo=UTC)
    times = [start + timedelta(minutes=k) for k in range(17 * 60)]
    from skyfield.api import wgs84
    ts, eph = ephem._skyfield()
    a, _, _ = (eph["earth"] + wgs84.latlon(LAT, LON, 0.0)).at(ts.from_datetimes(times)).observe(eph["sun"]).apparent().altaz()
    luma = np.clip(200 * 10 ** (0.35 * (a.degrees - 2.0)), 1.0, 230)
    with db._lock:
        db.con.executemany("INSERT INTO observations(ts, kind, analyzer, confidence, value) VALUES (?,?,?,?,?)",
                           [(tt.isoformat(), "sky_photometry", "sky", 1.0, json.dumps({"luma": float(v), "region": "sky"}))
                            for tt, v in zip(times, luma)])
        db.con.commit()
    bridge = AstroBridge({"layers_dir": str(tmp_path / "layers"), "domain": [59.8, 62.8, 8.0, 14.0], "coarse_dlat": 0.2,
                          "coarse_dlon": 0.4, "auto_verticals": False, "min_total": {"twilight": 2},
                          "twilight": {"thresholds": [40.0]}})
    ctx = Context(db=db, config={}, clock=StreamClock())
    out = bridge.on_tick(ctx)                                  # markers now, solving in the background
    markers = [o for o in out if o.kind == "twilight_marker"]
    assert [m.value["event"] for m in markers] == ["dusk", "dawn"]
    for o in out:
        db.add_observation(o)
    bridge._worker.join(timeout=60)
    out2 = bridge.on_tick(ctx)
    assert [o.value["method"] for o in out2 if o.kind == "astro_fix"] == ["twilight"]
    assert (tmp_path / "layers" / "astro_twilight.npz").exists()


def test_bridge_level_reference_and_auto_verticals(tmp_path):
    import cv2

    from hordewatch.analyzers.base import Context
    from hordewatch.db import DB
    from hordewatch.types import Frame, Observation, StreamClock

    db = DB(tmp_path / "hw.sqlite")
    img = np.full((720, 1280, 3), 190, np.uint8)
    for x in (150, 420, 760, 1100):
        cv2.line(img, (x, 40), (x + 8, 680), (25, 25, 25), 7)
    path = tmp_path / "frame.jpg"
    cv2.imwrite(str(path), img)
    noon = datetime(2026, 9, 22, 10, 30, tzinfo=UTC)
    db.add_frame(Frame(1, noon, noon, img, path=str(path)))
    bridge = AstroBridge({"layers_dir": str(tmp_path / "layers"), "threaded": False})
    ctx = Context(db=db, config={}, clock=StreamClock())
    (obs,) = bridge._auto_verticals(ctx)
    assert obs.kind == "camera_vertical" and obs.value["kind"] == "auto_lines" and len(obs.value["segments"]) == 4
    assert bridge._auto_verticals(ctx) == []                           # once per day
    db.add_observation(obs)
    db.add_observation(Observation("camera_vertical", noon + timedelta(days=1), dict(obs.value), "astro_bridge"))
    fam = [[500, 600, 700, 590], [500, 400, 700, 395]]
    db.add_observation(Observation("camera_vertical", noon, {"segments": [[640, 100, 641, 600, 0.2]], "kind": "plumb",
                                                             "horizontal_families": [fam], "w": 1280, "h": 720}, "human"))
    lev = bridge._level(db)
    assert lev.n_lines == 4 + 1                                         # latest auto set only + the manual plumb line
    # manual lines first (own sigma), then the latest automatic set (auto_vertical_sigma_deg)
    assert np.isclose(lev.seg_sigma[0], np.radians(0.2)) and np.isclose(lev.seg_sigma[-1], np.radians(2.5))
    assert len(lev.families) == 1 and "plumb lines" in lev.source and "families" in lev.source
    assert np.allclose(lev.segments[0], [0.0, (100 - 360) / 1280, 1 / 1280, (600 - 360) / 1280])


# ============================================================================= adversarial review tests
# (independent of the builder's own set-ups: nothing below hands the solver the truth it must recover)
def _bumped_points(sun_obs, bumped, day_mask_fn, keep_fn=None, seed=4):
    """Sun points where the camera had attitude `bumped` on the days selected by day_mask_fn."""
    t, x, y = sun_obs
    late = np.array([day_mask_fn(tt) for tt in t])
    az, alt = sky_altaz("sun", [tt for tt, m in zip(t, late) if m])
    xb, yb, ins = bumped.project_altaz(az, alt)
    rng = np.random.default_rng(seed)
    xb, yb = xb + rng.normal(0, 2, len(xb)), yb + rng.normal(0, 2, len(yb))
    ts = [tt for tt, m in zip(t, late) if not m] + [tt for tt, m in zip(t, late) if m]
    keep = np.r_[np.ones((~late).sum(), bool), ins]
    if keep_fn is not None:
        keep &= np.array([keep_fn(k, tt) for k, tt in enumerate(ts)])
    xs, ys = np.r_[x[~late], xb][keep], np.r_[y[~late], yb][keep]
    ts = [tt for tt, k in zip(ts, keep) if k]
    return CelestialPoints.from_places(ephem.body_places("sun", ts), xs, ys, 1280, 720, "sun"), ts


def test_level_bias_moves_fix_along_the_predicted_axis(sun_obs):
    """Sign conventions end to end: a level reference that is wrong by +0.5 deg of *pitch* must move the fix
    ~55 km towards the viewing azimuth (the sun looks higher -> closer to the sub-solar point), +0.5 deg of
    *roll* (right side up) ~55 km towards the camera's right (azimuth 310).  Catches flipped azimuth/heading,
    pixel-y or roll signs anywhere in camera.py / ephem.py / solver.py."""
    lats, lons = np.arange(60.2, 62.4, 0.05), np.arange(8.6, 13.4, 0.1)
    pts = sun_points(sun_obs)
    got = {}
    for name, lev in (("pitch", LevelReference(pitch=(2.5, 0.03), roll=(-1.0, 0.03), source="config")),
                      ("roll", LevelReference(pitch=(2.0, 0.03), roll=(-0.5, 0.03), source="config"))):
        s = summarize(lats, lons, solve_celestial(pts, lev, FitOptions(), lats, lons, 61.25, 9.0)["ll"])
        got[name] = (float(haversine(LAT, LON, s["lat"], s["lon"])), float(bearing(LAT, LON, s["lat"], s["lon"])))
    for name, az in (("pitch", 220.0), ("roll", 310.0)):
        dist, brg = got[name]
        assert 0.5 * 111 * 0.75 < dist < 0.5 * 111 * 1.25, (name, got)           # 1 deg = 111 km
        assert abs((brg - az + 180) % 360 - 180) < 15, (name, got)


def test_short_cloudy_session_is_not_a_camera_jump(sun_obs):
    """A static camera with one cloudy day (35 min of sun) must stay ONE pose segment (the builder's per-session
    refit with a free focal length split it in 12/12 seeds, 0.4-1.6 deg 'jumps').  Positive controls: a real
    0.8 deg pitch bump seen only in a short session is still detected, and a session too short to fit
    (< 6 points) after a bump joins the pose in force at its time, not the first one."""
    from hordewatch.astro.solver import CelestialFitter
    t, x, y = sun_obs
    idx22 = [k for k, tt in enumerate(t) if tt.day == 22]
    for seed in range(4):
        rng = np.random.default_rng(seed)
        s0 = int(rng.integers(0, len(idx22) - 7))
        keep = np.array([tt.day != 22 for tt in t])
        keep[idx22[s0:s0 + 7]] = True
        sel = np.nonzero(keep)[0]
        pts = CelestialPoints.from_places(ephem.body_places("sun", [t[i] for i in sel]), x[sel], y[sel], 1280, 720, "sun")
        fitter = CelestialFitter(pts, LevelReference(), FitOptions())
        seg, jumps = fitter.detect_jumps(fitter.fit_reference(61.25, 9.0))
        assert seg.max() == 0 and jumps == [], (seed, jumps)
    # real bump (pitch +0.8 deg) on 23 Sept, of which only 8 points are seen
    day23 = [k for k, tt in enumerate(t) if tt.day == 23]
    pts, ts = _bumped_points(sun_obs, CameraModel(220.0, 2.8, -1.0, 1000.0), lambda tt: tt.day == 23,
                             keep_fn=lambda k, tt: tt.day != 23 or len(t) - len(day23) + 6 <= k < len(t) - len(day23) + 14)
    assert sum(tt.day == 23 for tt in ts) == 8
    fitter = CelestialFitter(pts, LevelReference(), FitOptions())
    seg, jumps = fitter.detect_jumps(fitter.fit_reference(61.25, 9.0))
    assert seg.max() == 1 and len(jumps) == 1
    # bump on 22 Sept (full day), 23 Sept only 4 points with the bumped camera: they belong to segment 1
    pts, ts = _bumped_points(sun_obs, CameraModel(220.0, 2.8, -1.0, 1000.0), lambda tt: tt.day >= 22,
                             keep_fn=lambda k, tt: tt.day != 23 or k % 7 == 0)
    n23 = sum(tt.day == 23 for tt in ts)
    assert 2 <= n23 < 6
    fitter = CelestialFitter(pts, LevelReference(), FitOptions())
    seg, _ = fitter.detect_jumps(fitter.fit_reference(61.25, 9.0))
    day = np.array([tt.day for tt in ts])
    assert set(seg[day == 21]) == {0} and set(seg[day == 22]) == {1} and set(seg[day == 23]) == {1}


def test_calibration_applies_only_to_its_pose_segment(sun_obs):
    """Camera pitched up by 1 deg on 23 Sept; the level calibration (pitch 3.0) was measured on 23 Sept.
    Applying it to the pre-bump pose too (builder's behaviour) biased the fix by ~55 km while claiming
    sigma ~11 km; restricted to its own segment (att_t) the fix stays within 25 km."""
    pts, _ = _bumped_points(sun_obs, CameraModel(220.0, 3.0, -1.0, 1000.0), lambda tt: tt.day == 23)
    t_cal = datetime(2026, 9, 23, 15, tzinfo=UTC).timestamp()
    lev = LevelReference(pitch=(3.0, 0.1), roll=(-1.0, 0.1), source="calibration camera_attitude (test)", att_t=t_cal)
    sol = solve_celestial(pts, lev, FitOptions(), LATS, LONS, 61.25, 9.0)
    assert sol["fitter"].S == 2
    s = summarize(LATS, LONS, sol["ll"])
    assert haversine(s["lat"], s["lon"], LAT, LON) < 25.0                        # achieved ~10 km
    # the bridge takes att_t from the calibration row's time (or an explicit 'ts')
    from hordewatch.db import DB
    from hordewatch.astro.solver import _calibration_time
    import tempfile
    db = DB(tempfile.mkdtemp() + "/c.sqlite")
    db.set_calibration("camera_attitude", {"pitch_deg": 3.0, "pitch_sigma_deg": 0.1, "ts": "2026-09-23T15:00:00+00:00"})
    assert _calibration_time(db, "camera_attitude", db.calibration("camera_attitude")) == pytest.approx(t_cal)
    assert AstroBridge({"auto_verticals": False})._level(db).att_t == pytest.approx(t_cal)


def test_live_twilight_markers_one_per_evening_and_ambiguity(tmp_path):
    """The bridge re-extracts markers every tick from a growing series.  (a) A clean evening fed in 20-min
    ticks gives exactly ONE dusk marker per threshold, at the true crossing; (b) an evening where the sky ROI
    brightens again (moonrise / lit cloud, 19:00-19:40 UTC) is ambiguous and gives none - the builder emitted
    a first marker at 17:13 and a second one at 19:39 (15 deg depression); (c) an IR camera flapping at dusk
    gives no marker and never an evening 'dawn'."""
    from hordewatch.analyzers.base import Context
    from hordewatch.db import DB
    from hordewatch.types import StreamClock
    from skyfield.api import wgs84

    start = datetime(2026, 9, 21, 14, tzinfo=UTC)
    times = [start + timedelta(minutes=k) for k in range(10 * 60)]
    ts_, eph = ephem._skyfield()
    h = (eph["earth"] + wgs84.latlon(LAT, LON, 0.0)).at(ts_.from_datetimes(times)).observe(eph["sun"]).apparent().altaz()[0].degrees
    clean = np.clip(200 * 10 ** (0.35 * (h - 2.0)), 1.0, 230)
    tt = np.array([t.timestamp() for t in times])
    rebound = clean.copy()
    rebound[(tt >= datetime(2026, 9, 21, 19, tzinfo=UTC).timestamp()) & (tt < datetime(2026, 9, 21, 19, 40, tzinfo=UTC).timestamp())] = 60.0

    def run(luma, name):
        db = DB(tmp_path / f"{name}.sqlite")
        bridge = AstroBridge({"layers_dir": str(tmp_path / name), "threaded": False, "auto_verticals": False,
                              "min_total": {"twilight": 99}, "twilight": {"thresholds": [40.0]}})
        ctx = Context(db=db, config={}, clock=StreamClock())
        got, i0 = [], 0
        for stop in range(60, len(times) + 1, 20):                # live: 20 new minutes per tick
            with db._lock:
                db.con.executemany("INSERT INTO observations(ts, kind, analyzer, confidence, value) VALUES (?,?,?,?,?)",
                                   [(times[k].isoformat(), "sky_photometry", "sky", 1.0,
                                     json.dumps({"luma": float(luma[k]), "region": "sky"})) for k in range(i0, stop)])
                db.con.commit()
            i0 = stop
            for o in bridge.on_tick(ctx):
                db.add_observation(o)
                got += [o] if o.kind == "twilight_marker" else []
        return got

    got = run(clean, "clean")
    assert [(o.value["event"], o.value["series"]) for o in got] == [("dusk", "sky_luma_40")]
    truth = [t for t, e in crossing_times(2.0 + np.log10(40 / 200) / 0.35, start=start, days=1) if e == "dusk"][0]
    assert abs((got[0].ts - truth).total_seconds()) < 120
    assert run(rebound, "rebound") == []
    # (c) IR flapping at dusk on 21 Sept (on 17:40, off 17:55, on 18:10), clean switch to day at dawn 22 Sept
    t_ir = [datetime(2026, 9, 21, 15, tzinfo=UTC) + timedelta(minutes=k) for k in range(17 * 60)]

    def ir_at(t):
        hm = t.hour * 60 + t.minute + (0 if t.day == 21 else 1440)
        return (17 * 60 + 40 <= hm < 17 * 60 + 55) or (18 * 60 + 10 <= hm < 1440 + 4 * 60 + 30)
    mk = tw.ir_switch_markers([(t, ir_at(t)) for t in t_ir], approx=(61.25, 9.0))
    assert [m["event"] for m in mk] == ["dawn"]


def test_bridge_with_measured_level_reference_and_bad_inputs(tmp_path, monkeypatch, sun_obs):
    """End to end without any truth in the level reference: three hanging cords (plumb lines, 0.1 deg swing)
    and the box's two families of level edges (box itself tilted 0.15 deg), all projected through the true
    camera with 0.5 px noise, stored as a camera_vertical observation in pixels; plus a sun_pixel with
    x = NaN from a buggy analyzer (the builder's median binning turned the whole layer into NaN).
    Achieved: 8-14 km from the truth with sigma ~20 x 12 km; asserted < 30 km and truth inside 3 sigma."""
    from hordejakt.grid import GRID
    from hordejakt.layers import live
    from hordewatch.analyzers.base import Context
    from hordewatch.db import DB
    from hordewatch.types import Observation, StreamClock

    rng = np.random.default_rng(0)

    def unit(az):
        return np.array([np.sin(np.radians(az)), np.cos(np.radians(az)), 0.0])

    def seg_px(p, q):
        (x1, y1, _), (x2, y2, _) = CAM.project_enu(p), CAM.project_enu(q)
        return [float(v) for v in np.r_[x1, y1, x2, y2] + rng.normal(0, 0.5, 4)]

    cords = []
    for az0, dist in ((205, 3.0), (228, 4.5), (241, 6.0)):
        top = unit(az0) * dist + [0, 0, 1.2]
        lean, la = np.radians(rng.normal(0, 0.1)), rng.uniform(0, 2 * np.pi)
        cords.append(seg_px(top, top + 1.5 * np.array([np.sin(lean) * np.sin(la), np.sin(lean) * np.cos(la), -np.cos(lean)])))
    k_ax, th = unit(rng.uniform(0, 360)), np.radians(0.15)

    def tilted(v):                                   # Rodrigues rotation: the box is not perfectly level
        return v * np.cos(th) + np.cross(k_ax, v) * np.sin(th) + k_ax * (k_ax @ v) * (1 - np.cos(th))
    c = unit(221) * 5.0 + [0, 0, -0.8]
    fams = []
    for edge_az, half, off_az, off in ((20, 1.0, 110, 0.6), (110, 0.6, 20, 1.0)):
        fam = []
        for hgt in (0.0, 1.1):
            for side in (-1, 1):
                mid = c + tilted(unit(off_az) * side * off + [0, 0, hgt])
                fam.append(seg_px(mid - tilted(unit(edge_az)) * half, mid + tilted(unit(edge_az)) * half))
        fams.append(fam)

    db = DB(tmp_path / "hw.sqlite")
    t, x, y = sun_obs
    for tt, xx, yy in zip(t, x, y):
        db.add_observation(Observation("sun_pixel", tt, {"x": xx, "y": yy, "w": 1280, "h": 720}, "sun"))
    db.add_observation(Observation("sun_pixel", t[5] + timedelta(seconds=20),
                                   {"x": float("nan"), "y": 300.0, "w": 1280, "h": 720}, "sun"))
    db.add_observation(Observation("camera_vertical", datetime(2026, 9, 22, 10, tzinfo=UTC),
                                   {"segments": cords, "kind": "plumb", "w": 1280, "h": 720,
                                    "horizontal_families": fams, "family_sigma_deg": 0.2}, "human"))
    bridge = AstroBridge({"layers_dir": str(tmp_path / "layers"), "domain": [59.3, 63.3, 7.0, 14.0],
                          "coarse_dlat": 0.1, "coarse_dlon": 0.2, "threaded": False, "auto_verticals": False})
    out = bridge.on_tick(Context(db=db, config={}, clock=StreamClock()))
    (fix,) = [o.value for o in out if o.kind == "astro_fix"]
    assert fix["n_points"] == len(t) and np.isfinite([fix["lat"], fix["lon"], fix["sigma_km"]]).all()
    err = haversine(fix["lat"], fix["lon"], LAT, LON)
    assert err < 30.0 and err < 3 * fix["sigma_major_km"]
    assert "3 plumb lines" in fix["level_reference"] and "2 level-line families" in fix["level_reference"]
    assert 0.1 < fix["level_sigma_deg"] < 0.3
    monkeypatch.setattr(live, "LIVE_DIR", tmp_path / "layers")
    (L,) = live.build(GRID, {})
    i, j = GRID.index(LAT, LON)
    assert L.name == "astro_sun_track" and L.loglik.shape == GRID.shape and np.isfinite(L.loglik[i, j])
    assert np.nanmax(L.loglik) - L.loglik[i, j] < 6.0                             # truth well inside the layer
    # recomputing with the same data must not re-post events (jumps / mismatches are reported once)
    n_ev = db.con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    bridge._done_counts.clear()
    bridge.on_tick(Context(db=db, config={}, clock=StreamClock()))
    assert db.con.execute("SELECT COUNT(*) FROM events WHERE summary LIKE '%jump%'").fetchone()[0] == 0
    assert db.con.execute("SELECT COUNT(*) FROM events").fetchone()[0] == n_ev + 1   # only the new fix summary


def test_correlated_lean_floor_for_line_sets(tmp_path):
    """60 automatic Hough lines at 2.5 deg each would claim a 0.32 deg (35 km) level reference; tree leans and
    detector/distortion biases are correlated, so the combined information per kind is floored
    (auto_lines 1.0 deg, trunk 0.5 deg).  Few precise plumb lines are untouched."""
    from hordewatch.db import DB
    from hordewatch.types import Observation

    db = DB(tmp_path / "hw.sqlite")
    t0 = datetime(2026, 9, 22, 10, tzinfo=UTC)
    rng = np.random.default_rng(1)
    auto = [[x, 50.0, x + 3, 650.0] for x in rng.uniform(20, 1260, 60)]
    trunks = [[x, 100.0, x + 2, 600.0] for x in rng.uniform(20, 1260, 30)]
    db.add_observation(Observation("camera_vertical", t0, {"segments": auto, "kind": "auto_lines", "sigma_deg": 2.5,
                                                           "w": 1280, "h": 720}, "astro_bridge"))
    db.add_observation(Observation("camera_vertical", t0, {"segments": trunks, "kind": "trunk", "w": 1280, "h": 720}, "human"))
    db.add_observation(Observation("camera_vertical", t0, {"segments": [[600, 100, 600.5, 500], [700, 80, 700.4, 400]],
                                                           "kind": "plumb", "w": 1280, "h": 720}, "human"))
    # two pieces of the same straight edge: no defined vanishing direction -> the family is ignored
    db.add_observation(Observation("camera_vertical", t0, {"segments": [], "kind": "post", "w": 1280, "h": 720,
                                                           "horizontal_families": [[[400, 500, 600, 490], [650, 487.5, 850, 477.5]]],
                                                           "family_sigma_deg": 0.1}, "human"))
    lev = AstroBridge({"auto_verticals": False})._level(db)
    assert lev.n_lines == 92 and lev.families == []
    comb = lambda s: float(np.degrees(1.0 / np.sqrt(np.sum(1.0 / s ** 2))))
    assert comb(lev.seg_sigma[:30]) == pytest.approx(0.5, abs=1e-6)                 # trunks (manual first)
    assert comb(lev.seg_sigma[30:32]) == pytest.approx(0.15 / np.sqrt(2), rel=1e-6)   # plumb: unchanged
    assert comb(lev.seg_sigma[32:]) == pytest.approx(1.0, abs=1e-6)                 # automatic lines
    assert "correlated-lean floor" in lev.source
