"""Offline tests for the sky / sun / rain / night analyzers on synthetic frames."""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone

import cv2
import numpy as np
import pytest

from hordewatch.analyzers.base import Context
from hordewatch.db import DB
from hordewatch.types import Frame, StreamClock

UTC = timezone.utc


# ----------------------------------------------------------------------------------- helpers
def make_ctx(tmp_path, **cfg):
    db = DB(tmp_path / "hw.sqlite")
    return Context(db=db, config={"archive_dir": str(tmp_path / "archive"), **cfg}, clock=StreamClock())


def frame(img, ts, idx=0):
    return Frame(index=idx, capture_ts=ts + timedelta(seconds=30), real_ts=ts, image=img, source="test")


def store(ctx, obs):
    """Write through the real DB (checks that every value is JSON-serialisable)."""
    for o in obs:
        ctx.db.add_observation(o)
    return obs


def kinds(obs, kind):
    return [o for o in obs if o.kind == kind]


SKY_BLUE = np.array([95, 145, 215], np.float32)
SKY_GREY = np.array([186, 188, 192], np.float32)


def day_scene(sky="blue", w=640, h=360, seed=0, sky_frac=0.35, noise=2.0, rng=None, gradient=True):
    """Forest scene: sky strip on top (blue or overcast grey), canopy blobs and trunks crossing into it,
    textured heath below. Returns (uint8 RGB, ground-truth sky mask)."""
    g = np.random.default_rng(seed)
    low = cv2.resize(g.normal(0, 1, (h // 16 + 1, w // 16 + 1, 3)).astype(np.float32), (w, h),
                     interpolation=cv2.INTER_CUBIC)
    hi = cv2.GaussianBlur(g.normal(0, 1, (h, w, 3)).astype(np.float32), (0, 0), 1.2)
    img = np.array([62, 88, 48], np.float32) + 22 * low + 16 * hi
    hs = int(sky_frac * h)
    yy = np.arange(hs, dtype=np.float32)[:, None, None] / max(hs, 1)
    base = SKY_BLUE if sky == "blue" else SKY_GREY
    grad = (np.array([30, 25, 12], np.float32) if sky == "blue" else np.array([6, 6, 6], np.float32)) if gradient else 0.0
    sky_img = base + grad * yy
    if sky == "grey":
        sky_img = sky_img + 3 * low[:hs]
    img[:hs] = np.broadcast_to(sky_img, (hs, w, 3))
    gt = np.zeros((h, w), bool)
    gt[:hs] = True
    occ = np.zeros((h, w), np.uint8)
    for _ in range(9):                      # canopy blobs along the sky boundary
        cx, cy = int(g.uniform(0, w)), int(hs + g.uniform(-0.08, 0.02) * h)
        cv2.ellipse(occ, (cx, cy), (int(g.uniform(0.05, 0.1) * w), int(g.uniform(0.04, 0.08) * h)), 0, 0, 360, 1, -1)
    for x in (0.18, 0.47, 0.81):            # trunks from the top down
        x0 = int(x * w)
        cv2.rectangle(occ, (x0, 0), (x0 + max(3, w // 90), h), 2, -1)
    canopy = occ == 1
    img[canopy] = np.array([40, 70, 35], np.float32) + 15 * hi[canopy]
    trunk = occ == 2
    img[trunk] = np.array([85, 62, 45], np.float32) + 10 * hi[trunk]
    gt &= occ == 0
    r = rng or g
    img = img + r.normal(0, noise, img.shape)
    return np.clip(img, 0, 255).astype(np.uint8), gt


# ----------------------------------------------------------------------------------- shared helpers
def test_solar_position_matches_skyfield():
    from hordewatch.analyzers.sky import solar_altaz
    pytest.importorskip("skyfield")
    skyfield_data = pytest.importorskip("skyfield_data")
    from skyfield.api import Loader, wgs84
    ld = Loader(skyfield_data.get_skyfield_data_path(), verbose=False)
    ts, eph = ld.timescale(), ld("de421.bsp")
    for s in ("2026-09-22T05:10:00", "2026-09-22T13:30:00", "2026-12-21T11:00:00"):
        d = datetime.fromisoformat(s).replace(tzinfo=UTC)
        for lat, lon in ((61.25, 9.0), (58.2, 5.1), (64.3, 13.2)):
            a, z = solar_altaz(d, lat, lon, refraction=False)
            alt, az, _ = (eph["earth"] + wgs84.latlon(lat, lon)).at(ts.from_datetime(d)).observe(eph["sun"]).apparent().altaz()
            assert abs(a - alt.degrees) < 0.03
            assert abs((z - az.degrees + 180) % 360 - 180) < 0.03


def test_cct_grey_is_d65_and_blue_sky_is_hotter():
    from hordewatch.analyzers.sky import cct_from_linear_rgb, srgb_to_linear
    t_grey, duv = cct_from_linear_rgb(*srgb_to_linear(np.array([128.0, 128.0, 128.0])))
    assert abs(t_grey - 6504) < 60 and abs(duv) < 0.01
    t_warm, _ = cct_from_linear_rgb(*srgb_to_linear(np.array([255.0, 180.0, 120.0])))
    t_blue, _ = cct_from_linear_rgb(*srgb_to_linear(np.array([160.0, 180.0, 210.0])))
    assert t_warm < 3500 < 6500 < t_blue


# ----------------------------------------------------------------------------------- sky
def run_sky(tmp_path, sky, n=5, cfg=None, t0=datetime(2026, 9, 22, 11, 0, tzinfo=UTC), sub="a"):
    from hordewatch.analyzers.sky import SkyAnalyzer
    ctx = make_ctx(tmp_path / sub)
    a = SkyAnalyzer({"photometry_interval_s": 0, "weather_interval_s": 0, **(cfg or {})})
    rng = np.random.default_rng(5)
    obs, gt = [], None
    for i in range(n):
        img, gt = day_scene(sky, seed=1, rng=rng)
        f = frame(img, t0 + timedelta(seconds=5 * i), i)
        ctx.db.add_frame(f)
        obs += store(ctx, a.on_frame(f, ctx))
    return a, ctx, obs, gt


def test_sky_mask_learned_and_saved(tmp_path):
    a, ctx, obs, gt = run_sky(tmp_path, "blue", n=6)
    m = ctx.state["sky"]["mask"]
    assert ctx.state["sky"]["mask_state"] == "learned"
    big = cv2.resize(m.astype(np.uint8), (gt.shape[1], gt.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
    iou = (big & gt).sum() / (big | gt).sum()
    assert iou > 0.6, iou
    assert (big & ~gt).sum() / max(big.sum(), 1) < 0.1          # little ground / canopy in the mask
    assert (tmp_path / "a" / "archive" / "sky" / "sky_mask.png").exists()
    sp = [o for o in kinds(obs, "sky_photometry") if o.value["region"] == "sky"]
    assert sp and sp[-1].value["b"] > sp[-1].value["r"] + 50
    scene = kinds(obs, "scene_photometry")
    assert scene and scene[-1].value["ir_mode"] is False and scene[-1].frame_id is not None
    # a new analyzer instance reloads the saved mask
    from hordewatch.analyzers.sky import SkyAnalyzer
    b = SkyAnalyzer({"photometry_interval_s": 0})
    img, _ = day_scene("blue", seed=1)
    b.on_frame(frame(img, datetime(2026, 9, 22, 11, 1, tzinfo=UTC), 99), ctx)
    assert b.model.n >= 100 and ctx.state["sky"]["mask_state"] == "learned"


def test_cloud_fraction_blue_vs_grey(tmp_path):
    _, _, blue, _ = run_sky(tmp_path, "blue", sub="b")
    _, _, grey, _ = run_sky(tmp_path, "grey", sub="g")
    fb = kinds(blue, "cloud_fraction")[-1].value
    fg = kinds(grey, "cloud_fraction")[-1].value
    assert fb["fraction"] < 0.2, fb
    assert fg["fraction"] > 0.8, fg
    cb = [o.value["cct_k"] for o in kinds(blue, "sky_photometry") if o.value.get("cct_k")]
    cg = [o.value["cct_k"] for o in kinds(grey, "sky_photometry") if o.value.get("cct_k")]
    assert cb[-1] > cg[-1]


def test_ir_mode_flag(tmp_path):
    from hordewatch.analyzers.sky import SkyAnalyzer
    ctx = make_ctx(tmp_path)
    a = SkyAnalyzer({"photometry_interval_s": 0})
    img, _ = day_scene("grey", seed=2)
    g = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
    obs = store(ctx, a.on_frame(frame(g, datetime(2026, 9, 22, 21, 0, tzinfo=UTC)), ctx))
    assert kinds(obs, "scene_photometry")[0].value["ir_mode"] is True
    assert ctx.state["sky"]["ir_mode"] is True
    assert not kinds(obs, "cloud_fraction")                   # no colour-based weather at night


def test_twilight_marker_on_luma_ramp(tmp_path):
    """Sky luma constant, then exponential decay after sunset; the online detector must find the
    sustained crossings of 100 / 50 / 25 at the analytic times."""
    from hordewatch.analyzers.sky import SkyAnalyzer
    ctx = make_ctx(tmp_path)
    a = SkyAnalyzer({"photometry_interval_s": 600, "weather_interval_s": 1e9, "twilight_thresholds": [100, 50, 25],
                     "work_width": 160})
    t0 = datetime(2026, 9, 22, 16, 0, tzinfo=UTC)
    decay0, tau, L0 = t0 + timedelta(minutes=40), 40.0, 160.0
    base, gt = day_scene("blue", w=160, h=90, seed=3, noise=0.0, gradient=False)
    base = base.astype(np.float32)
    sky_lum = float((base[gt] @ np.array([0.299, 0.587, 0.114], np.float32)).mean())
    assert base.max() * L0 / sky_lum < 250                  # no clipping: luma is linear in the scale factor
    rng = np.random.default_rng(0)
    markers = []
    for i in range(170):
        t = t0 + timedelta(minutes=i)
        m = (t - decay0).total_seconds() / 60.0
        target = L0 * (math.exp(-m / tau) if m > 0 else 1.0)
        img = np.clip(np.round(base * (target / sky_lum) + rng.normal(0, 1.0, base.shape)), 0, 255).astype(np.uint8)
        out = store(ctx, a.on_frame(frame(img, t, i), ctx))
        markers += [o for o in kinds(out, "sky_photometry") if o.value.get("twilight_marker")]
    got = {o.value["twilight_marker"]["threshold"]: o for o in markers}
    assert set(got) == {100.0, 50.0, 25.0}, [o.value for o in markers]
    for T, o in got.items():
        truth = decay0 + timedelta(minutes=tau * math.log(L0 / T))
        err = abs((o.ts - truth).total_seconds())
        assert err < 90, (T, o.ts, truth)
        v = o.value["twilight_marker"]
        assert v["event"] == "dusk" and v["slope_per_min"] < 0 and o.value["region"] == "twilight_marker"
    # stored in the DB with the crossing time
    rows = [r for r in ctx.db.observations(kind="sky_photometry") if r["value"].get("twilight_marker")]
    assert len(rows) == 3


def test_fog_far_contrast_drop(tmp_path):
    """Koschmieder haze: distant (mid-image) forest loses contrast and tends to the sky luminance."""
    from hordewatch.analyzers.sky import SkyAnalyzer
    ctx = make_ctx(tmp_path)
    a = SkyAnalyzer({"photometry_interval_s": 1e9, "weather_interval_s": 0})
    base, gt = day_scene("grey", seed=5, noise=0.0)
    base = base.astype(np.float32)
    rows = (np.arange(base.shape[0]) + 0.5) / base.shape[0]
    trans = np.interp(rows, [0.0, 0.35, 0.55, 0.75, 1.0], [0.1, 0.12, 0.2, 0.6, 0.8])[:, None, None]
    rng = np.random.default_rng(2)
    t0 = datetime(2026, 9, 22, 11, 0, tzinfo=UTC)
    fog = []
    for i in range(20):
        img = base if i < 12 else np.where(gt[..., None], base, base * trans + SKY_GREY * (1 - trans))
        img = np.clip(img + rng.normal(0, 2, img.shape), 0, 255).astype(np.uint8)
        fog += kinds(store(ctx, a.on_frame(frame(img, t0 + timedelta(minutes=i), i), ctx)), "fog")
    assert not any(o.value["present"] for o in fog[:12])
    assert all(o.value["present"] for o in fog[12:]) and fog[-1].value["contrast_drop"] > 0.6
    assert fog[-1].confidence <= 0.5


def test_direct_sun_vs_overcast(tmp_path):
    from hordewatch.analyzers.sky import SkyAnalyzer
    t = datetime(2026, 9, 22, 11, 0, tzinfo=UTC)
    res = {}
    fleck = day_scene("blue", seed=3, noise=0.0)[0].astype(np.float32) * 0.6       # shaded forest floor ...
    g = np.random.default_rng(3)
    lit = np.zeros(fleck.shape[:2], np.uint8)
    for _ in range(14):                                                              # ... with ~10 % sunflecks
        cv2.ellipse(lit, (int(g.uniform(20, 620)), int(g.uniform(190, 350))), (int(g.uniform(12, 30)), int(g.uniform(5, 12))),
                    float(g.uniform(0, 180)), 0, 360, 1, -1)
    fleck[lit > 0] = np.clip(fleck[lit > 0] * np.array([4.2, 3.6, 2.4], np.float32), 0, 255)
    fleck = np.clip(fleck + g.normal(0, 2, fleck.shape), 0, 255).astype(np.uint8)
    for name, img in (("sun", shadow_ground(seed=3)), ("flecks", fleck), ("overcast", day_scene("grey", seed=3)[0])):
        ctx = make_ctx(tmp_path / name)
        a = SkyAnalyzer({"photometry_interval_s": 1e9, "weather_interval_s": 0})
        res[name] = kinds(store(ctx, a.on_frame(frame(img, t), ctx)), "direct_sun")[0].value
        assert ctx.state["sky"]["direct_sun"] == res[name]["present"]
    assert res["sun"]["present"] and res["sun"]["sunlit_fraction"] > 0.5 and res["sun"]["warm_shift"] > 0.2
    assert res["flecks"]["present"] and 0.03 < res["flecks"]["sunlit_fraction"] < 0.3, res["flecks"]
    assert not res["overcast"]["present"] and res["overcast"]["sunlit_fraction"] == 0.0


def test_twilight_ignores_midday_cloud_dip():
    from hordewatch.analyzers.sky import TwilightTracker
    tr = TwilightTracker([100.0])
    t0 = datetime(2026, 9, 22, 10, 0, tzinfo=UTC).timestamp()
    out = []
    for i in range(120):                         # a 40-min dark cloud at noon crosses 100 twice
        v = 60.0 if 40 <= i < 80 else 180.0
        out += tr.add(t0 + 60 * i, v)
    assert out == []


# ----------------------------------------------------------------------------------- sun
def render_sun(img, sx, sy, R=10.0, glare_w=28.0, ghosts=(1.35, 1.8, 2.4)):
    h, w = img.shape[:2]
    f = img.astype(np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot(xx - sx, yy - sy)
    g = np.exp(-np.clip(r - R, 0, None) / glare_w)[..., None]
    f = f + (255.0 - f) * g * 0.97
    core = np.clip(R + 0.5 - r, 0, 1)[..., None]            # anti-aliased disk
    f = f * (1 - core) + 255.0 * core
    cx, cy = w / 2.0, h / 2.0
    for k in ghosts:                                        # flare ghosts on the sun -> centre line
        gx, gy = sx + k * (cx - sx), sy + k * (cy - sy)
        gr = 9 + 5 * k
        m = np.exp(-((xx - gx) ** 2 + (yy - gy) ** 2) / (2 * (gr / 2) ** 2))[..., None]
        f = f + m * np.array([10, 45, 25], np.float32)
    return np.clip(f, 0, 255).astype(np.uint8)


def test_sun_pixel_disk_and_flare(tmp_path):
    from hordewatch.analyzers.sun import SunAnalyzer
    ctx = make_ctx(tmp_path)
    img, _ = day_scene("blue", w=1280, h=720, seed=4)
    sx, sy = 903.4, 141.7
    img = render_sun(img, sx, sy)
    a = SunAnalyzer({"interval_s": 0, "shadow_interval_s": 1e9})
    t = datetime(2026, 9, 22, 13, 30, tzinfo=UTC)          # sun az ~213 deg: in the SW-facing view
    obs = store(ctx, a.on_frame(frame(img, t), ctx))
    sp = kinds(obs, "sun_pixel")
    assert len(sp) == 1
    v = sp[0].value
    assert math.hypot(v["x"] - sx, v["y"] - sy) < 3.0, v
    assert v["w"] == 1280 and v["h"] == 720 and abs(v["xn"] - sx / 1280) < 0.003
    assert v["saturated"] and 7 <= v["radius"] <= 18 and v["az_prior_ok"]
    assert v["n_ghosts"] >= 1
    assert 0.3 <= sp[0].confidence <= 0.85


def test_sun_partially_occluded_uses_glare(tmp_path):
    from hordewatch.analyzers.sun import find_sun
    img, _ = day_scene("blue", w=1280, h=720, seed=6)
    sx, sy = 700.0, 160.0
    img = render_sun(img, sx, sy, ghosts=())
    cv2.line(img, (660, 150), (740, 172), (40, 60, 30), 5)      # a branch across the disk
    d = find_sun(img)
    assert d is not None and math.hypot(d["x"] - sx, d["y"] - sy) < 4.0, d


@pytest.mark.parametrize("frac", [0.2, 0.5])
def test_sun_behind_trunk_circle_fit(frac):
    """A trunk hides the left part of the disk: the centroid would be biased; the limb circle fit is not."""
    from hordewatch.analyzers.sun import find_sun
    img, _ = day_scene("blue", w=1280, h=720, seed=6)
    sx, sy, R = 700.3, 160.6, 12.0
    img = render_sun(img, sx, sy, R=R, ghosts=())
    xcut = int(sx - R + 2 * R * frac)
    cv2.rectangle(img, (xcut - 30, 0), (xcut, 400), (70, 55, 40), -1)
    d = find_sun(img)
    assert d is not None and d["method"] == "circle_fit"
    assert math.hypot(d["x"] - sx, d["y"] - sy) < 1.5, d


def test_no_sun_at_night_and_not_for_white_sign(tmp_path):
    from hordewatch.analyzers.sun import SunAnalyzer
    ctx = make_ctx(tmp_path)
    img, _ = day_scene("grey", w=1280, h=720, seed=4)
    cv2.rectangle(img, (500, 450), (760, 600), (255, 255, 255), -1)   # whiteboard-like: flat surround
    a = SunAnalyzer({"interval_s": 0, "shadow_interval_s": 1e9})
    assert kinds(a.on_frame(frame(img, datetime(2026, 9, 22, 13, 30, tzinfo=UTC)), ctx), "sun_pixel") == []
    sun_img = render_sun(img, 900, 140)
    assert a.on_frame(frame(sun_img, datetime(2026, 9, 22, 23, 0, tzinfo=UTC), 1), ctx) == []


def shadow_ground(w=640, h=360, angle_deg=30.0, seed=0):
    """Sunlit heath (warm) with parallel cast shadows (dark, bluish) at angle_deg (clockwise from +x)."""
    g = np.random.default_rng(seed)
    low = cv2.resize(g.normal(0, 1, (h // 12 + 1, w // 12 + 1)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    alb = 1.0 + 0.12 * low + 0.06 * cv2.GaussianBlur(g.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 1.0)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = math.radians(angle_deg)
    nx, ny = -math.sin(a), math.cos(a)                      # normal to the shadow lines
    d = xx * nx + yy * ny
    shadow = (np.mod(d, 55.0) < 14.0).astype(np.float32)
    shadow = cv2.GaussianBlur(shadow, (0, 0), 0.8)           # penumbra
    sun_rgb = np.array([200, 175, 120], np.float32)
    shade_rgb = np.array([45, 52, 62], np.float32)
    col = sun_rgb * (1 - shadow[..., None]) + shade_rgb * shadow[..., None]
    img = col * alb[..., None]
    img[: int(0.3 * h)] = np.array([120, 150, 200], np.float32)
    return np.clip(img + g.normal(0, 2, img.shape), 0, 255).astype(np.uint8)


@pytest.mark.parametrize("angle", [30.0, 115.0])
def test_shadow_direction(tmp_path, angle):
    from hordewatch.analyzers.sun import SunAnalyzer
    ctx = make_ctx(tmp_path)
    img = shadow_ground(angle_deg=angle, seed=int(angle))
    a = SunAnalyzer({"interval_s": 1e9, "shadow_interval_s": 0})
    obs = store(ctx, a.on_frame(frame(img, datetime(2026, 9, 22, 11, 0, tzinfo=UTC)), ctx))
    sd = kinds(obs, "shadow_direction")
    assert len(sd) == 1
    v = sd[0].value
    err = abs((v["angle_deg_image"] - angle + 90) % 180 - 90)
    assert err < 5.0, v
    assert v["coherence"] > 0.5 and v["w"] == 640 and 0 <= v["x"] < 640 and v["y"] > 0.5 * 360


# ----------------------------------------------------------------------------------- rain / condensation
def run_rain(tmp_path, drops_per_frame, n=9, start=3, cfg=None, sub="r"):
    from hordewatch.analyzers.rain import RainAnalyzer
    ctx = make_ctx(tmp_path / sub)
    a = RainAnalyzer({"emit_interval_s": 0, "cond_emit_interval_s": 1e9, **(cfg or {})})
    base, _ = day_scene("grey", w=960, h=540, seed=7, noise=0.0)
    base = base.astype(np.float32)
    rng = np.random.default_rng(11)
    drops = []
    obs = []
    yy, xx = np.mgrid[-5:6, -5:6].astype(np.float32)
    t0 = datetime(2026, 9, 22, 12, 0, tzinfo=UTC)
    for i in range(n):
        if i >= start:
            for _ in range(drops_per_frame):
                x = rng.uniform(0.25 * 960, 0.75 * 960)
                y = rng.uniform(0.15 * 540, 0.9 * 540)
                drops.append((x, y, rng.uniform(1.2, 2.2), rng.choice([-1, 1]) * rng.uniform(35, 60)))
        img = base.copy()
        for x, y, r, amp in drops:
            xi, yi = int(x), int(y)
            blob = amp * np.exp(-((xx - (x - xi)) ** 2 + (yy - (y - yi)) ** 2) / (2 * r * r))
            img[yi - 5:yi + 6, xi - 5:xi + 6] += blob[..., None]
        img = np.clip(img + rng.normal(0, 2.0, img.shape), 0, 255).astype(np.uint8)
        obs += store(ctx, a.on_frame(frame(img, t0 + timedelta(seconds=5 * i), i), ctx))
    return kinds(obs, "rain_visual")


def test_rain_drops_detected(tmp_path):
    rv = run_rain(tmp_path, 30)
    assert rv, "no rain_visual emitted"
    pres = [o for o in rv if o.value["present"]]
    assert pres, [o.value for o in rv]
    assert pres[-1].value["intensity"] > 0.2 and pres[-1].value["new_drops"] >= 15
    assert pres[-1].confidence <= 0.6


def test_no_rain_on_static_scene(tmp_path):
    rv = run_rain(tmp_path, 0, sub="dry")
    assert rv and not any(o.value["present"] for o in rv), [o.value for o in rv]


def test_rain_streaks_at_night(tmp_path):
    from hordewatch.analyzers.rain import detect_streaks
    rng = np.random.default_rng(3)
    prev = np.full((300, 400), 30.0, np.float32) + rng.normal(0, 2, (300, 400)).astype(np.float32)
    cur = np.full((300, 400), 30.0, np.float32) + rng.normal(0, 2, (300, 400)).astype(np.float32)
    for _ in range(25):
        x, y = int(rng.uniform(20, 380)), int(rng.uniform(20, 260))
        cv2.line(cur, (x, y), (x + int(rng.uniform(-3, 3)), y + int(rng.uniform(10, 25))), 120.0, 1)
    roi = np.ones_like(cur, bool)
    n = detect_streaks(cur, prev, roi, np.zeros_like(roi))
    assert n >= 18
    assert detect_streaks(prev, cur * 0 + prev, roi, np.zeros_like(roi)) == 0


def test_condensation_on_box(tmp_path):
    from hordewatch.analyzers.rain import RainAnalyzer
    ctx = make_ctx(tmp_path)
    a = RainAnalyzer({"emit_interval_s": 1e9, "cond_emit_interval_s": 0, "box_roi_norm": [0.3, 0.3, 0.7, 0.95]})
    base, _ = day_scene("grey", w=640, h=360, seed=8, noise=0.0)
    rng = np.random.default_rng(1)
    obs = []
    t0 = datetime(2026, 9, 22, 6, 0, tzinfo=UTC)
    x0, x1, y0, y1 = int(0.3 * 640), int(0.7 * 640), int(0.3 * 360), int(0.95 * 360)
    for i in range(14):
        img = base.astype(np.float32).copy()
        if i >= 7:
            roi = img[y0:y1, x0:x1]
            img[y0:y1, x0:x1] = 0.35 * cv2.GaussianBlur(roi, (0, 0), 4.0) + 0.65 * 225.0
        img = np.clip(img + rng.normal(0, 2, img.shape), 0, 255).astype(np.uint8)
        obs += store(ctx, a.on_frame(frame(img, t0 + timedelta(seconds=5 * i), i), ctx))
    cd = kinds(obs, "condensation")
    before = [o for o in cd if o.ts < t0 + timedelta(seconds=35)]
    after = [o for o in cd if o.value["present"]]
    assert before and not any(o.value["present"] for o in before)
    assert after and after[-1].value["fraction"] > 0.5 and after[-1].value["veil"] > 0.06


# ----------------------------------------------------------------------------------- night
def night_sky(w=1280, h=720, stars=None, seed=0, noise=2.0, sky_frac=0.55, rng=None):
    g = np.random.default_rng(seed)
    hs = int(sky_frac * h)
    img = np.empty((h, w), np.float32)
    img[:hs] = 14.0 + 6.0 * np.linspace(1, 0, hs)[:, None]
    tex = cv2.GaussianBlur(g.normal(0, 1, (h - hs, w)).astype(np.float32), (0, 0), 1.5)
    img[hs:] = 65.0 + 18.0 * tex
    yy, xx = np.mgrid[-6:7, -6:7].astype(np.float32)
    for (x, y, amp) in (stars or []):
        xi, yi = int(round(x)), int(round(y))
        img[yi - 6:yi + 7, xi - 6:xi + 7] += amp * np.exp(-((xx - (x - xi)) ** 2 + (yy - (y - yi)) ** 2) / (2 * 1.1 ** 2))
    r = rng or g
    img += r.normal(0, noise, img.shape)
    return img


def to_rgb(g):
    g8 = np.clip(g, 0, 255).astype(np.uint8)
    return np.dstack([g8, g8, g8])


def add_point(img, x, y, amp, sigma=1.3):
    yy, xx = np.mgrid[-6:7, -6:7].astype(np.float32)
    xi, yi = int(round(x)), int(round(y))
    img[yi - 6:yi + 7, xi - 6:xi + 7] += amp * np.exp(-((xx - (x - xi)) ** 2 + (yy - (y - yi)) ** 2) / (2 * sigma ** 2))


def test_star_field_and_aircraft_track(tmp_path):
    from hordewatch.analyzers.night import NightSkyAnalyzer
    ctx = make_ctx(tmp_path)
    g = np.random.default_rng(42)
    stars = []
    while len(stars) < 30:
        x, y = g.uniform(20, 1260), g.uniform(15, 0.55 * 720 - 20)
        if all(math.hypot(x - a, y - b) > 12 for a, b, _ in stars):
            stars.append((x, y, g.uniform(25, 120)))
    a = NightSkyAnalyzer({"star_field_interval_s": 0, "moon_ephemeris_gate": False})
    t0 = datetime(2026, 9, 22, 21, 0, tzinfo=UTC)
    dt = 0.25
    rng = np.random.default_rng(7)
    obs = []
    truth = []
    for i in range(40):
        img = night_sky(stars=stars, seed=1, rng=rng)
        x, y = 150.0 + 6.0 * i, 120.0 + 1.2 * i
        on = (i // 2) % 2 == 0 and i < 30                  # 1 Hz blink (2 frames on, 2 off); gone after 7.5 s
        if on:
            add_point(img, x, y, 150.0)
            truth.append((x, y))
        obs += store(ctx, a.on_frame(frame(to_rgb(img), t0 + timedelta(seconds=dt * i), i), ctx))
    sf = kinds(obs, "star_field")
    assert sf
    v = sf[-1].value
    assert v["n_stars"] >= 25 and v["w"] == 1280 and v["stack_n"] == 3
    pts = np.array(v["points"])
    matched = sum(np.min(np.hypot(pts[:, 0] - x, pts[:, 1] - y)) < 1.0 for x, y, _ in stars)
    assert matched >= 25
    for p in pts:                                           # the moving light is never a "star"
        assert np.min([math.hypot(p[0] - x, p[1] - y) for x, y in truth]) > 3.0
    al = kinds(obs, "aircraft_light")
    assert len(al) == 1, [o.value for o in al]
    t = al[0].value
    assert t["n_points"] >= 10 and len(t["track"]) == t["n_points"]
    assert abs(t["blink_hz"] - 1.0) < 0.2 and 0.4 < t["duty"] < 0.6
    assert abs(t["speed_px_s"] - math.hypot(6, 1.2) / dt) < 2.0
    assert abs(t["direction_deg_image"] - math.degrees(math.atan2(1.2, 6))) < 3.0
    t_first = datetime.fromisoformat(t["track"][0][0])
    assert abs((t_first - t0).total_seconds()) <= 1.1 and al[0].ts == t_first
    assert abs(t["track"][0][1] - truth[1][0]) < 1.0 or abs(t["track"][0][1] - truth[0][0]) < 1.0


def test_aircraft_track_at_5s_sampling(tmp_path):
    """Normal monitoring cadence: blinking is aliased (blink_hz None), the track is still found."""
    from hordewatch.analyzers.night import NightSkyAnalyzer
    ctx = make_ctx(tmp_path)
    a = NightSkyAnalyzer({"star_field_interval_s": 1e9, "moon_ephemeris_gate": False})
    t0 = datetime(2026, 9, 22, 21, 30, tzinfo=UTC)
    rng = np.random.default_rng(9)
    obs = []
    for i in range(13):
        img = night_sky(seed=6, rng=rng)
        if i < 8:
            add_point(img, 200.0 + 40.0 * i, 300.0 - 22.0 * i, 120.0)
        obs += store(ctx, a.on_frame(frame(to_rgb(img), t0 + timedelta(seconds=5 * i), i), ctx))
    al = kinds(obs, "aircraft_light")
    assert len(al) == 1
    v = al[0].value
    assert v["n_points"] >= 7 and v["blink_hz"] is None and v["duty"] > 0.95
    assert abs(v["speed_px_s"] - math.hypot(40, 22) / 5.0) < 0.5 and v["sample_dt_s"] == 5.0
    assert 0.3 < v["speed_deg_s"] < 0.8


def test_hot_pixels_rejected_from_star_field(tmp_path):
    from hordewatch.analyzers.night import NightSkyAnalyzer
    ctx = make_ctx(tmp_path)
    fixed = [(100.0 + 90 * k, 60.0 + 20 * (k % 5), 80.0) for k in range(12)]     # never drift
    a = NightSkyAnalyzer({"star_field_interval_s": 0, "moon_ephemeris_gate": False, "hot_px_after_s": 600})
    t0 = datetime(2026, 9, 22, 22, 0, tzinfo=UTC)
    rng = np.random.default_rng(0)
    n = {}
    for i, m in enumerate((0, 5, 11, 12)):
        img = to_rgb(night_sky(stars=fixed, seed=2, rng=rng))
        sf = kinds(a.on_frame(frame(img, t0 + timedelta(minutes=m), i), ctx), "star_field")
        n[m] = sf[0].value["n_stars"] if sf else 0
    # before hot_px_after_s they count as stars; after it they have not drifted at all: rejected
    assert n[0] == 12 and n[5] == 12 and n[11] == 0 and n[12] == 0


def test_star_field_drift_and_star_count_clouds(tmp_path):
    """A rigidly drifting field (sidereal motion) is matched between epochs; the count gives clear-sky evidence."""
    from hordewatch.analyzers.night import NightSkyAnalyzer
    ctx = make_ctx(tmp_path)
    g = np.random.default_rng(8)
    base = [(g.uniform(80, 1200), g.uniform(40, 330), g.uniform(40, 120)) for _ in range(40)]
    a = NightSkyAnalyzer({"star_field_interval_s": 0, "moon_ephemeris_gate": False})
    t0 = datetime(2026, 9, 22, 22, 0, tzinfo=UTC)
    rng = np.random.default_rng(1)
    obs = []
    for i, m in enumerate((0, 2)):
        stars = [(x + 3.1 * m, y - 1.2 * m, f) for x, y, f in base]      # 3.3 px/min
        obs += store(ctx, a.on_frame(frame(to_rgb(night_sky(stars=stars, seed=4, rng=rng)), t0 + timedelta(minutes=m), i), ctx))
    d = kinds(obs, "star_field")[-1].value["drift"]
    assert d is not None and abs(d["dx"] - 6.2) < 0.5 and abs(d["dy"] + 2.4) < 0.5 and d["n_matched"] >= 30
    assert abs(d["rate_px_per_min"] - math.hypot(3.1, 1.2)) < 0.3
    cf = kinds(obs, "cloud_fraction")
    assert cf and cf[-1].value["method"] == "star_count" and cf[-1].value["fraction"] < 0.2


def test_moon_detected(tmp_path):
    from hordewatch.analyzers.night import NightSkyAnalyzer
    ctx = make_ctx(tmp_path)
    img = night_sky(seed=3)
    yy, xx = np.mgrid[0:720, 0:1280].astype(np.float32)
    r = np.hypot(xx - 412.3, yy - 150.6)
    img += 200.0 * np.exp(-np.clip(r - 12, 0, None) / 10.0) + 255.0 * (r <= 12)
    a = NightSkyAnalyzer({"moon_ephemeris_gate": False})
    obs = store(ctx, a.on_frame(frame(to_rgb(img), datetime(2026, 9, 22, 22, 0, tzinfo=UTC)), ctx))
    mp = kinds(obs, "moon_pixel")
    assert len(mp) == 1
    v = mp[0].value
    assert math.hypot(v["x"] - 412.3, v["y"] - 150.6) < 1.5 and v["saturated"] and 10 < v["radius"] < 18


def test_moon_ephemeris_gate(tmp_path):
    """With skyfield: the same disk is the moon at 22 UTC (alt ~8 deg, SSW, 85 % lit) but a lamp at 08 UTC."""
    pytest.importorskip("skyfield")
    pytest.importorskip("skyfield_data")
    from hordewatch.analyzers.night import NightSkyAnalyzer
    img = night_sky(seed=3)
    yy, xx = np.mgrid[0:720, 0:1280].astype(np.float32)
    r = np.hypot(xx - 640.0, yy - 250.0)
    img += 255.0 * (r <= 11) + 150.0 * np.exp(-np.clip(r - 11, 0, None) / 8.0)
    res = {}
    for h in (22, 8):
        ctx = make_ctx(tmp_path / str(h))
        a = NightSkyAnalyzer({})
        res[h] = kinds(store(ctx, a.on_frame(frame(to_rgb(img), datetime(2026, 9, 22, h, 0, tzinfo=UTC)), ctx)), "moon_pixel")
    assert len(res[22]) == 1 and res[8] == []
    v = res[22][0].value
    assert abs(v["illum"] - 0.85) < 0.03 and 5 < v["moon_alt_approx_deg"] < 11 and 190 < v["moon_az_approx_deg"] < 215


def test_whiteboard_is_not_the_moon(tmp_path):
    """A saturated square (IR-lit whiteboard) below the sky region is not reported as the moon."""
    from hordewatch.analyzers.night import NightSkyAnalyzer
    ctx = make_ctx(tmp_path)
    img = night_sky(seed=3)
    img[480:560, 600:680] = 255.0
    a = NightSkyAnalyzer({"moon_ephemeris_gate": False})
    assert kinds(a.on_frame(frame(to_rgb(img), datetime(2026, 9, 22, 22, 0, tzinfo=UTC)), ctx), "moon_pixel") == []


def test_night_light_event(tmp_path):
    from hordewatch.analyzers.night import NightSkyAnalyzer
    ctx = make_ctx(tmp_path)
    a = NightSkyAnalyzer({"moon_ephemeris_gate": False, "star_field_interval_s": 1e9})
    rng = np.random.default_rng(4)
    obs = []
    t0 = datetime(2026, 9, 22, 23, 0, tzinfo=UTC)
    for i in range(8):
        img = night_sky(seed=5, rng=rng)
        if i >= 5:                                   # torch beam in the lower left
            cv2.ellipse(img, (300, 560), (160, 45), -15, 0, 360, 200.0, -1)
        obs += store(ctx, a.on_frame(frame(to_rgb(img), t0 + timedelta(seconds=5 * i), i), ctx))
    ev = kinds(obs, "night_light_event")
    assert len(ev) == 1, [o.value for o in ev]
    v = ev[0].value
    x0, y0, x1, y1 = v["bbox"]
    assert x0 < 300 < x1 and y0 < 560 < y1 and v["switched"] == "on" and v["luma_delta"] > 50
    assert v["elongation"] > 2.0 and v["colour"] == "ir" and not v["in_sky"]


def test_night_inactive_in_daylight(tmp_path):
    from hordewatch.analyzers.night import NightSkyAnalyzer
    ctx = make_ctx(tmp_path)
    img, _ = day_scene("blue", w=1280, h=720, seed=9)
    a = NightSkyAnalyzer({})
    assert a.on_frame(frame(img, datetime(2026, 9, 22, 11, 0, tzinfo=UTC)), ctx) == []


# ----------------------------------------------------------------------------------- integration
def test_runner_loads_all_four_and_pipeline_runs(tmp_path):
    import logging
    from hordewatch.runner import DEFAULT_CONFIG, load_analyzers
    cfg = {**DEFAULT_CONFIG, "analyzers": ["sky", "sun", "rain", "night"], "archive_dir": str(tmp_path / "arch"),
           "analyzer_config": {"sky": {"photometry_interval_s": 0, "weather_interval_s": 0}}}
    an = load_analyzers(cfg, logging.getLogger("test"))
    assert [x.name for x in an] == ["sky", "sun", "rain", "night"]
    ctx = make_ctx(tmp_path)
    t0 = datetime(2026, 9, 22, 13, 30, tzinfo=UTC)
    rng = np.random.default_rng(0)
    n = 0
    for i in range(4):
        img, _ = day_scene("blue", w=1280, h=720, seed=4, rng=rng)
        img = render_sun(img, 903.4, 141.7)
        f = frame(img, t0 + timedelta(seconds=5 * i), i)
        ctx.db.add_frame(f)
        for x in an:
            for o in x.on_frame(f, ctx):
                ctx.db.add_observation(o)
                json.loads(o.value_json())
                n += 1
    ks = {r["kind"] for r in ctx.db.observations()}
    assert {"sky_photometry", "scene_photometry", "cloud_fraction", "sun_pixel", "rain_visual"} <= ks
    # the sun analyzer used the sky analyzer's learned mask and the cloud fraction excluded the sun
    assert ctx.state["sun"]["last"] is not None
