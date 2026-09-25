"""Tests for hordejakt.refine (offline: synthetic terrain/OSM + the real local ADS-B trace).

Run:  .venv/bin/python -m pytest tests/test_refine.py -q
"""
import gzip
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest
import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hordejakt.refine import fetch, score  # noqa: E402
from hordejakt.refine.raster import Raster, make_transform, to_utm, to_wgs84  # noqa: E402

TRACE = ROOT / "data/raw/mk_bevis/bevis/claude-2026-09-25/adsb/trace_4791ac.json"

# ----------------------------------------------------------------------------- synthetic scene
# Local frame around the target T: u points NE (grid 45 deg), v points NW (grid 315 deg).
TX, TY = (round(float(v), -2) for v in to_utm(61.21, 10.93))
U = np.array([np.sqrt(0.5), np.sqrt(0.5)])
V = np.array([-np.sqrt(0.5), np.sqrt(0.5)])
SUMMIT = np.array([TX, TY]) + 900.0 * V          # hill top 900 m NW of T
AMP, SIG = 250.0, 1400.0
BASE = 810.0 - AMP * np.exp(-900.0 ** 2 / (2 * SIG ** 2))   # makes z(T) = 810 m exactly


def uv(u, v):
    p = np.array([TX, TY]) + u * U + v * V
    return float(p[0]), float(p[1])


def lonlat(u, v):
    lat, lon = to_wgs84(*uv(u, v))
    return [float(lon), float(lat)]


def hill(x, y):
    d2 = (x - SUMMIT[0]) ** 2 + (y - SUMMIT[1]) ** 2
    return BASE + AMP * np.exp(-d2 / (2 * SIG ** 2))


def contour_v(u):
    """v of the 810 m contour (circle of radius 900 around the summit) at along-slope position u."""
    return 900.0 - np.sqrt(900.0 ** 2 - u ** 2)


def line(kind_tags, pts):
    return {"type": "Feature", "properties": dict(kind_tags), "geometry": {"type": "LineString",
                                                                        "coordinates": [lonlat(*p) for p in pts]}}


def circle(tags, u, v, r, n=24):
    ring = [lonlat(u + r * np.cos(a), v + r * np.sin(a)) for a in np.linspace(0, 2 * np.pi, n, endpoint=False)]
    ring.append(ring[0])
    return {"type": "Feature", "properties": dict(tags), "geometry": {"type": "Polygon", "coordinates": [ring]}}


def point(tags, u, v):
    return {"type": "Feature", "properties": dict(tags), "geometry": {"type": "Point", "coordinates": lonlat(u, v)}}


DECOYS = {  # openings in the canopy that look like the box site but violate one clue
    "stream": (-380.0, float(contour_v(-380.0))),   # on the 810 contour, 20 m from a stream
    "cabin": (420.0, float(contour_v(420.0))),      # on the 810 contour, ~50 m from a cabin
    "low": (0.0, -200.0),                           # 100 m from the road, ~790 m a.s.l.
}


def synthetic_scene(res=4.0, half=1200.0, with_dom=True):
    xmin, ymax = TX - half, TY + half
    n = int(2 * half / res)
    dtm = Raster(np.zeros((n, n), np.float32), make_transform(xmin, ymax, res))
    X, Y = dtm.centres()
    dtm.data = hill(X, Y).astype(np.float32)
    fc = {"type": "FeatureCollection", "features": [
        # forest road (drivable track) 300 m SE of T, running NE-SW
        line({"highway": "track", "tracktype": "grade2", "name": "Testskogsveien"}, [(-700, -300), (700, -300)]),
        # county road (traffic) far east
        {"type": "Feature", "properties": {"highway": "tertiary", "ref": "Fv999"}, "geometry": {
            "type": "LineString", "coordinates": [list(map(float, to_wgs84(TX + 1150, TY + y)[::-1])) for y in (-1500, 1500)]}},
        # stream down the slope at u = -400 and a lake at its foot
        line({"waterway": "stream"}, [(-400, 350), (-400, -150), (-560, -420)]),
        circle({"natural": "water", "name": "Testtjernet"}, -700, -520, 90),
        # a cabin near the contour NE of T
        circle({"building": "cabin"}, 450, -60, 6, n=8),
        # a footpath far from T, a cattle grid on the track's far end, a bog and a field
        line({"highway": "path"}, [(250, 500), (900, 900)]),
        point({"barrier": "cattle_grid"}, -690, -300),
        circle({"natural": "wetland", "wetland": "bog"}, 0, 450, 80),
        circle({"landuse": "farmland"}, 500, -700, 150),
    ]}
    dom = None
    if with_dom:
        chm = np.full(dtm.shape, 18.0, np.float32)
        # old logging area (young forest ~6 m) between the road and T
        cu = (X - TX) * U[0] + (Y - TY) * U[1]
        cv = (X - TX) * V[0] + (Y - TY) * V[1]
        chm[(np.abs(cu) < 150) & (cv > -300) & (cv < -60)] = 6.0
        for (u, v) in [(0.0, 0.0)] + list(DECOYS.values()):
            x0, y0 = uv(u, v)
            chm[np.hypot(X - x0, Y - y0) <= 5.0] = 0.3
        dom = Raster(dtm.data + chm, dtm.transform)
    return dtm, dom, fc


@pytest.fixture(scope="module")
def scored_with_dom():
    dtm, dom, fc = synthetic_scene()
    return score.score_tile(dtm, dom=dom, osm=fc, work_res=4.0, n_out=10, n_pool=120, min_sep_m=30.0)


@pytest.fixture(scope="module")
def scored_no_dom():
    dtm, _, fc = synthetic_scene(with_dom=False)
    return score.score_tile(dtm, osm=fc, work_res=4.0, n_out=10, n_pool=120, min_sep_m=30.0)


# ----------------------------------------------------------------------------- scorer on the synthetic scene
def _uv_of(c):
    dx, dy = c["x"] - TX, c["y"] - TY
    return dx * U[0] + dy * U[1], dx * V[0] + dy * V[1]


def test_target_ranked_first_with_dom(scored_with_dom):
    ts, cands = scored_with_dom
    top = cands[0]
    u, v = _uv_of(top)
    assert np.hypot(u, v) <= 6.0, f"top candidate {u:.1f},{v:.1f} m from T"
    assert abs(top["z"] - 810.0) < 2.0
    # the decoy openings each violate one clue and must score clearly below T at pixel level
    rT, cT = (int(round(q)) for q in ts.grid.rowcol(*uv(0, 0)))
    for name, (du, dv) in DECOYS.items():
        r, c = (int(round(q)) for q in ts.grid.rowcol(*uv(du, dv)))
        assert ts.total[r, c] < ts.total[rT, cT] - 0.5, name
    # and none of the top 3 is a decoy
    for c in cands[:3]:
        cu, cv = _uv_of(c)
        assert all(np.hypot(cu - du, cv - dv) > 30 for du, dv in DECOYS.values())


def test_top_candidate_access_details(scored_with_dom):
    _, cands = scored_with_dom
    inf = cands[0]["info"]
    assert inf["parking"]["road"].startswith("track/grade2 'Testskogsveien'")
    assert 250 <= inf["walk_m"] <= 360
    assert 4.0 <= inf["walk_min"] <= 11.0
    assert inf["climb_m"] > 10                                  # uphill from the car
    assert inf["direction_hypothesis"] == "SE (whiteboard)"
    assert score.angdiff(inf["bearing_box_to_car"], 130.0) <= 40
    assert inf["crossings"] == []
    assert inf["regrowth_frac"] > 0.5                           # walked through the old logging area
    assert cands[0]["terms_b"]["morning_sun"] == 0.0


def test_without_dom_top_is_on_contour_and_clear_of_hazards(scored_no_dom):
    ts, cands = scored_no_dom
    assert "dom" in ts.missing
    top = cands[0]
    x, y = top["x"], top["y"]
    assert abs(top["z"] - 810.0) < 5.0
    stream_x, stream_y = uv(-400, 0)
    assert abs((x - stream_x) * U[0] + (y - stream_y) * U[1]) > 200     # >200 m from the stream (u = -400)
    cab = np.array(uv(450, -60))
    assert np.hypot(x - cab[0], y - cab[1]) > 350
    assert top["info"]["direction_hypothesis"] == "SE (whiteboard)"
    assert 120 <= top["info"]["road_dist_m"] <= 600


def test_water_cabin_and_elevation_terms(scored_no_dom):
    ts, _ = scored_no_dom

    def at(u, v, name):
        r, c = (int(round(q)) for q in ts.grid.rowcol(*uv(u, v)))
        return ts.terms[name][r, c]
    assert at(-700, -420, "water_osm") < -2.0          # lake shore
    assert at(0, 0, "water_osm") == 0.0
    assert at(450, -40, "cabin") < -2.0
    assert at(0, 0, "elevation") == pytest.approx(float(score.elevation_ll(810.0)), abs=0.01)
    assert at(0, -280, "elevation") < -1.0             # down by the road, ~780 m
    assert at(500, -700, "landcover") <= -3.0          # farmland


def test_candidate_record_is_json_ready(scored_with_dom):
    _, cands = scored_with_dom
    rec = score.candidate_record(cands[0])
    js = json.loads(json.dumps(rec))
    assert abs(js["lat"] - 61.21) < 0.01 and abs(js["lon"] - 10.93) < 0.02
    for k in ("elevation_m", "road_distance_m", "bearing_car_to_box_true", "bearing_car_to_box_magnetic",
              "walk_distance_m", "walk_time_min", "climb_m", "parking", "reasons", "terms"):
        assert js[k] is not None, k
    assert abs((js["bearing_car_to_box_true"] - js["bearing_box_to_car_true"]) % 360 - 180) < 1e-6
    assert js["parking"]["lat"] < js["lat"]                     # car is south(-east) of the box
    assert any("elevation 810" in r for r in js["reasons"])


def test_probabilities_are_normalised(scored_with_dom):
    ts, _ = scored_with_dom
    ps = [c["p_in_tile"] for c in ts.candidates]
    assert all(0 <= p <= 1 for p in ps) and 0 < sum(ps) <= 1.0 + 1e-9


# ----------------------------------------------------------------------------- scoring building blocks
def test_direction_mixture():
    assert score.direction_ll(130.0) == pytest.approx(0.0, abs=1e-6)
    assert score.direction_ll(170.0) == pytest.approx(0.0, abs=1e-6)           # edge of +-40
    old = (119.0 + 4.5 + 180.0) % 360
    assert score.direction_ll(old) == pytest.approx(np.log(0.25 / 0.75), abs=1e-3)
    assert score.direction_ll(30.0) < score.direction_ll(old) - 1.0
    assert score.direction_ll(220.0) < -1.0


def test_elevation_bands():
    z = np.arange(700, 1000, 0.5)
    ll = score.elevation_ll(z)
    assert ll.max() == pytest.approx(0.0, abs=1e-3) and 880 < z[ll.argmax()] < 892
    assert -0.3 < score.elevation_ll(810.0) < 0.0
    assert score.elevation_ll(875.0) > -0.8 and score.elevation_ll(891.0) > -0.05
    assert score.elevation_ll(830.0) < -1.0 and score.elevation_ll(850.0) < -2.0
    assert score.elevation_ll(700.0) <= -10.0


def test_walk_profile_flat_and_uphill():
    r = Raster(np.full((100, 100), 800.0, np.float32), make_transform(0.0, 1000.0, 10.0))
    w = score.walk_profile(r, 100, 500, 400, 500)
    assert w["length_m"] == pytest.approx(300.0)
    assert w["time_min"] == pytest.approx(0.3 / (6 * np.exp(-0.175) * 0.6) * 60, rel=1e-3)
    X, Y = r.centres()
    r.data = (800 + 0.1 * X).astype(np.float32)
    up = score.walk_profile(r, 100, 500, 400, 500)
    assert up["ascent_m"] == pytest.approx(30.0, abs=0.5) and up["time_min"] > w["time_min"]


def test_sun_position_2109():
    lat, lon = 61.21, 10.93
    az, el = score.sun_position(lat, lon, datetime(2026, 9, 21, 5, 52, tzinfo=timezone.utc))   # 07:52 CEST
    assert 88 < az < 110 and 2 < el < 9
    # solar noon: elevation ~ 90 - lat + decl(~+0.8)
    best = max((score.sun_position(lat, lon, datetime(2026, 9, 21, 10, m, tzinfo=timezone.utc)) for m in range(0, 60, 2)),
               key=lambda t: t[1])
    best = max(best, max((score.sun_position(lat, lon, datetime(2026, 9, 21, 11, m, tzinfo=timezone.utc))
                          for m in range(0, 60, 2)), key=lambda t: t[1]), key=lambda t: t[1])
    assert best[1] == pytest.approx(29.6, abs=0.4) and abs(best[0] - 180) < 2


def test_horizon_and_terrain_sunrise():
    x0, y0 = to_utm(61.21, 10.93)
    r = Raster(np.full((400, 400), 800.0, np.float32), make_transform(x0 - 2000, y0 + 2000, 10.0))
    X, Y = r.centres()
    ang, d, cov = score.horizon_elevation([r], x0, y0, 800.0, 90.0)
    assert abs(ang) < 0.2
    r2 = Raster(np.where(X > x0 + 1000, 900.0, 800.0).astype(np.float32), r.transform)
    ang2, d2, _ = score.horizon_elevation([r2], x0, y0, 800.0, 95.0)
    assert ang2 == pytest.approx(np.degrees(np.arctan(100 / 1005)), abs=0.6)
    early = score.terrain_sunrise([r], x0, y0, 801.5)[0]
    late = score.terrain_sunrise([r2], x0, y0, 801.5)[0]
    assert early < "07:15" and late > early


def test_dtm_streams_follow_valley():
    r = Raster(np.zeros((150, 150), np.float32), make_transform(0.0, 1500.0, 10.0))
    X, Y = r.centres()
    r.data = (800 + 0.15 * np.abs(X - 750) + 0.05 * Y).astype(np.float32)
    s = score.dtm_streams(r, 10.0, 2.0e5)
    rr, cc = (int(round(q)) for q in r.rowcol(750, 100))
    assert s.data[rr, cc] == 1                          # valley bottom near the outlet
    rr, cc = (int(round(q)) for q in r.rowcol(300, 100))
    assert s.data[rr, cc] == 0                          # hillside


def test_nms_separation():
    a = np.zeros((50, 50))
    a[10, 10], a[11, 11], a[40, 40] = 3, 2.9, 2
    picks = score.nms(a, 3, 5)
    assert picks[0] == (10, 10) and (40, 40) in picks and (11, 11) not in picks


# ----------------------------------------------------------------------------- ADS-B (real local file)
def test_parse_real_adsb_trace():
    tr = fetch.parse_trace(TRACE)
    assert (tr["icao"], tr["registration"], tr["type"]) == ("4791ac", "LN-NIQ", "B738")
    df = tr["points"]
    assert len(df) == 1643
    assert df["t"].iloc[0] == pytest.approx(1789948800.0 + 51823.17)
    assert "NOZ9EG" in tr["callsigns"] and all(set(c) != {"@"} for c in tr["callsigns"])
    assert df["on_ground"].sum() > 0 and df["new_leg"].sum() >= 1
    # same numbers as fly_2109_resultat.txt: 21:29:38 CEST stream time minus 22 s delay
    t = datetime(2026, 9, 21, 19, 29, 38, tzinfo=timezone.utc).timestamp() - 22
    p = fetch.trace_position(tr, t)
    assert p["lat"] == pytest.approx(61.317, abs=0.001) and p["lon"] == pytest.approx(10.904, abs=0.001)
    assert p["alt_ft"] == pytest.approx(25920, abs=5) and p["alt_kind"] == "geom" and p["callsign"] == "NOZ9EG"
    assert fetch.trace_position(tr, df["t"].iloc[0] - 10) is None


def test_parse_trace_plain_json_and_bytes():
    raw = gzip.decompress(TRACE.read_bytes())
    a = fetch.parse_trace(raw)
    b = fetch.parse_trace(json.loads(raw))
    assert len(a["points"]) == len(b["points"]) == 1643


# ----------------------------------------------------------------------------- fetch layer (fake transport)
class FakeResp:
    def __init__(self, content, status=200, ctype="application/octet-stream", url=""):
        self.content = content if isinstance(content, bytes) else content.encode()
        self.status_code = status
        self.headers = {"Content-Type": ctype}
        self.url = url


@pytest.fixture
def net(monkeypatch, tmp_path):
    """Route fetch._send through a python function; isolated cache; no sleeping."""
    monkeypatch.setattr(fetch, "CACHE", tmp_path)
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    fetch.reset_blocked()
    fetch.set_offline(False)
    calls = []

    def install(router):
        def send(method, url, params=None, data=None, headers=None, timeout=60):
            calls.append((method, url, dict(params or {}), data))
            return router(method, url, params or {}, data)
        monkeypatch.setattr(fetch, "_send", send)
    yield install, calls
    fetch.reset_blocked()


def proxy_block(method, url, params, data):
    raise requests.exceptions.ProxyError("Unable to connect to proxy", OSError("Tunnel connection failed: 403 Forbidden"))


def test_blocked_host_fails_fast_and_is_remembered(net):
    install, calls = net
    install(proxy_block)
    with pytest.raises(fetch.FetchBlocked) as e:
        fetch.http("https://overpass-api.de/api/interpreter", data={"data": "x"}, method="POST")
    assert e.value.hosts == ["overpass-api.de"] and len(calls) == 1      # no retries on a policy block
    with pytest.raises(fetch.FetchBlocked):
        fetch.http("https://overpass-api.de/api/interpreter")
    assert len(calls) == 1                                                # remembered
    msg = fetch.blocked_message(["overpass-api.de", "wcs.geonorge.no"])
    assert "overpass-api.de" in msg and "wcs.geonorge.no" in msg


def test_retry_then_cache(net):
    install, calls = net
    seq = [FakeResp("busy", 503), FakeResp('{"ok": 1}', 200, "application/json")]
    install(lambda *a: seq.pop(0))
    r = fetch.http("https://ws.geonorge.no/hoydedata/v1/punkter", {"a": 1})
    assert r.json() == {"ok": 1} and len(calls) == 2
    r2 = fetch.http("https://ws.geonorge.no/hoydedata/v1/punkter", {"a": 1})
    assert r2.from_cache and len(calls) == 2
    fetch.set_offline(True)
    try:
        assert fetch.http("https://ws.geonorge.no/hoydedata/v1/punkter", {"a": 1}).json() == {"ok": 1}
        with pytest.raises(fetch.FetchBlocked):
            fetch.http("https://ws.geonorge.no/hoydedata/v1/punkter", {"a": 2})
    finally:
        fetch.set_offline(False)


WCS_CAPS_100 = b"""<?xml version="1.0"?><WCS_Capabilities xmlns="http://www.opengis.net/wcs" version="1.0.0">
<ContentMetadata>
 <CoverageOfferingBrief><name>nhm_dtm_topobathy_25833</name><label>DTM topobathy</label></CoverageOfferingBrief>
 <CoverageOfferingBrief><name>nhm_dtm_topo_25833</name><label>DTM</label></CoverageOfferingBrief>
 <CoverageOfferingBrief><name>nhm_dtm_skyggerelieff</name><label>shade</label></CoverageOfferingBrief>
</ContentMetadata></WCS_Capabilities>"""
WCS_CAPS_201 = b"""<?xml version="1.0"?><wcs:Capabilities xmlns:wcs="http://www.opengis.net/wcs/2.0" xmlns:ows="http://www.opengis.net/ows/2.0">
<wcs:ServiceMetadata><wcs:formatSupported>image/tiff</wcs:formatSupported></wcs:ServiceMetadata>
<wcs:Contents><wcs:CoverageSummary><wcs:CoverageId>nhm_dom_topo_25833</wcs:CoverageId></wcs:CoverageSummary></wcs:Contents>
</wcs:Capabilities>"""
WCS_DESCRIBE = b"""<?xml version="1.0"?><CoverageDescription xmlns="http://www.opengis.net/wcs"><CoverageOffering>
<name>nhm_dtm_topo_25833</name><supportedCRSs><requestResponseCRSs>EPSG:25833</requestResponseCRSs></supportedCRSs>
<supportedFormats nativeFormat="GeoTIFF"><formats>GeoTIFF</formats><formats>XYZ</formats></supportedFormats>
</CoverageOffering></CoverageDescription>"""
OWS_EXC = b"""<?xml version="1.0"?><ServiceExceptionReport><ServiceException code="InvalidParameterValue">msWCSGetCoverage(): unsupported</ServiceException></ServiceExceptionReport>"""


def zfun(x, y):
    return 800.0 + 0.01 * (x - 280000) + 0.02 * (y - 6790000)


def geotiff_bytes(arr, xmin, ymax, res, nodata=-9999.0):
    import tifffile
    buf = io.BytesIO()
    geokeys = (1, 1, 0, 3, 1024, 0, 1, 1, 1025, 0, 1, 1, 3072, 0, 1, 25833)
    tifffile.imwrite(buf, arr.astype(np.float32), extratags=[
        (33550, "d", 3, (res, res, 0.0), True), (33922, "d", 6, (0.0, 0.0, 0.0, xmin, ymax, 0.0), True),
        (34735, "H", len(geokeys), geokeys, True), (42113, "s", 0, f"{nodata:g}", True)])
    return buf.getvalue()


def wcs_router(method, url, params, data):
    req = params.get("REQUEST")
    if req == "GetCapabilities":
        return FakeResp(WCS_CAPS_100, ctype="text/xml")
    if req == "DescribeCoverage":
        return FakeResp(WCS_DESCRIBE, ctype="text/xml")
    if req == "GetCoverage":
        assert params["COVERAGE"] == "nhm_dtm_topo_25833" and params["FORMAT"] == "GeoTIFF"
        xmin, ymin, xmax, ymax = map(float, params["BBOX"].split(","))
        w, h = int(params["WIDTH"]), int(params["HEIGHT"])
        res = (xmax - xmin) / w
        t = Raster(np.zeros((h, w), np.float32), make_transform(xmin, ymax, res))
        X, Y = t.centres()
        z = zfun(X, Y)
        z[0, 0] = -9999.0
        return FakeResp(geotiff_bytes(z, xmin, ymax, res), ctype="image/tiff")
    raise AssertionError(f"unexpected {url} {params}")


def test_wcs_capabilities_and_choice():
    covs = fetch.parse_wcs_capabilities(WCS_CAPS_100)
    assert [c["name"] for c in covs][:2] == ["nhm_dtm_topobathy_25833", "nhm_dtm_topo_25833"]
    assert fetch.choose_coverage(covs, "dtm") == "nhm_dtm_topo_25833"
    c2 = fetch.parse_wcs_capabilities(WCS_CAPS_201)
    assert c2[0]["name"] == "nhm_dom_topo_25833" and c2[0]["formats"] == ["image/tiff"]
    assert fetch.choose_coverage([], "dom") == "nhm_dom_topo_25833"
    assert fetch.parse_wcs_describe(WCS_DESCRIBE)["formats"] == ["GeoTIFF", "XYZ"]
    assert fetch.choose_format(["XYZ", "GeoTIFF"]) == "GeoTIFF"
    assert "unsupported" in fetch.ows_exception(OWS_EXC)


def test_dtm_tile_mosaics_wcs_tiles(net, monkeypatch):
    install, calls = net
    install(wcs_router)
    monkeypatch.setattr(fetch, "MAX_PX", 64)                     # force a 3x3 mosaic
    bbox = (280000.0, 6790000.0, 280150.0, 6790150.0)
    r = fetch.dtm_tile(bbox, res_m=1.0)
    assert r.shape == (150, 150) and r.res == (1.0, 1.0)
    assert tuple(r.transform)[:6] == (1.0, 0.0, 280000.0, 0.0, -1.0, 6790150.0)
    X, Y = r.centres()
    ok = np.isfinite(r.data)
    assert (~ok).sum() == 9                                      # one nodata pixel per tile
    assert np.allclose(r.data[ok], zfun(X, Y)[ok], atol=1e-3)
    n = len(calls)
    r2 = fetch.dtm_tile(bbox, res_m=1.0)                          # processed-raster cache
    assert len(calls) == n and np.array_equal(np.isnan(r2.data), ~ok)


def test_wcs_format_alias_fallback(net, monkeypatch):
    install, calls = net

    def router(method, url, params, data):
        if params.get("REQUEST") == "GetCoverage" and params.get("FORMAT") != "GTiff":
            return FakeResp(OWS_EXC, ctype="text/xml")          # server only knows 'GTiff'
        if params.get("REQUEST") == "GetCoverage":
            params = dict(params, FORMAT="GeoTIFF")
        return wcs_router(method, url, params, data)
    install(router)
    r = fetch.dtm_tile((280000.0, 6790000.0, 280040.0, 6790040.0), res_m=1.0)
    assert r.meta["format"] == "GTiff" and np.isfinite(r.data).sum() == 40 * 40 - 1


def test_adsb_trace_fetch_and_cache(net):
    install, calls = net
    raw = TRACE.read_bytes()

    def router(method, url, params, data):
        assert url == "https://globe.adsb.lol/globe_history/2026/09/21/traces/ac/trace_full_4791ac.json"
        return FakeResp(gzip.decompress(raw), ctype="application/json")     # server already gunzipped
    install(router)
    tr = fetch.adsb_trace("4791AC", "2026-09-21")
    assert tr["registration"] == "LN-NIQ" and len(tr["points"]) == 1643
    assert fetch.adsb_trace("4791ac", "2026-09-21")["icao"] == "4791ac" and len(calls) == 1


def test_score_tile_without_osm_still_runs():
    dtm, _, _ = synthetic_scene(res=8.0, half=600.0, with_dom=False)
    ts, cands = score.score_tile(dtm, osm=None, work_res=8.0, n_out=3, n_pool=20, sun=False)
    assert "osm" in ts.missing and cands and cands[0]["info"]["parking"] is None
    assert any("no drivable road" in r for r in cands[0]["reasons"])


def test_geotiff_decoder_without_rasterio(monkeypatch):
    arr = np.arange(12, dtype=np.float32).reshape(3, 4)
    b = geotiff_bytes(arr, 1000.0, 2000.0, 10.0, nodata=5.0)
    monkeypatch.setitem(sys.modules, "rasterio", None)           # force the tifffile path
    monkeypatch.setitem(sys.modules, "rasterio.io", None)
    with pytest.raises(ImportError):
        from rasterio.io import MemoryFile  # noqa: F401
    a, t = fetch.decode_geotiff(b)
    assert np.isnan(a[1, 1]) and a[2, 3] == 11
    assert tuple(t)[:6] == (10.0, 0.0, 1000.0, 0.0, -10.0, 2000.0)


def test_ascii_decoders():
    a, t = fetch.decode_aaigrid("ncols 2\nnrows 2\nxllcorner 100\nyllcorner 200\ncellsize 5\nNODATA_value -1\n1 2\n-1 4\n")
    assert np.isnan(a[1, 0]) and tuple(t)[:6] == (5.0, 0.0, 100.0, 0.0, -5.0, 210.0)
    a, t = fetch.decode_xyz("102.5 207.5 1\n107.5 207.5 2\n102.5 202.5 3\n107.5 202.5 4\n")
    assert a.tolist() == [[1, 2], [3, 4]] and tuple(t)[:6] == (5.0, 0.0, 100.0, 0.0, -5.0, 210.0)


def test_dtm_falls_back_to_point_api(net):
    install, calls = net

    def router(method, url, params, data):
        if "wcs.geonorge.no" in url:
            return proxy_block(method, url, params, data)
        pts = json.loads(params["punkter"])
        assert len(pts) <= 50 and params["koordsys"] == 25833
        return FakeResp(json.dumps({"koordsys": 25833, "punkter": [
            {"x": x, "y": y, "z": zfun(x, y), "datakilde": "dtm1", "terreng": "Skog"} for x, y in pts]}), ctype="application/json")
    install(router)
    r = fetch.dtm_tile((280000.0, 6790000.0, 280500.0, 6790500.0), res_m=1.0, sparse_step_m=50.0)
    assert r.source == "hoydedata-points" and r.shape == (10, 10)
    X, Y = r.centres()
    assert np.allclose(r.data, zfun(X, Y), atol=1e-3)
    assert sum("ws.geonorge.no" in c[1] for c in calls) == 2       # 100 points / 50 per call


def test_dtm_both_hosts_blocked(net):
    install, _ = net
    install(proxy_block)
    with pytest.raises(fetch.FetchBlocked) as e:
        fetch.dtm_tile((280000.0, 6790000.0, 280100.0, 6790100.0))
    assert e.value.hosts == ["wcs.geonorge.no", "ws.geonorge.no"]


def _g(*pts):
    return [{"lat": a, "lon": b} for a, b in pts]


OVERPASS_SAMPLE = {"osm3s": {"timestamp_osm_base": "2026-09-25T00:00:00Z"}, "elements": [
    {"type": "way", "id": 1, "tags": {"highway": "track", "tracktype": "grade2"}, "geometry": _g((61.20, 10.90), (61.201, 10.902))},
    {"type": "way", "id": 2, "tags": {"building": "cabin"},
     "geometry": _g((61.2, 10.9), (61.2, 10.9002), (61.2001, 10.9002), (61.2001, 10.9), (61.2, 10.9))},
    {"type": "node", "id": 3, "lat": 61.2, "lon": 10.9, "tags": {"barrier": "cattle_grid"}},
    {"type": "relation", "id": 4, "tags": {"type": "multipolygon", "natural": "water"}, "members": [
        {"type": "way", "ref": 10, "role": "outer", "geometry": _g((61.21, 10.91), (61.21, 10.92), (61.215, 10.92))},
        {"type": "way", "ref": 11, "role": "outer", "geometry": _g((61.21, 10.91), (61.215, 10.91), (61.215, 10.92))}]},
    {"type": "way", "id": 5, "tags": {"waterway": "stream"}, "geometry": _g((61.22, 10.9), (61.23, 10.91))},
    {"type": "way", "id": 6, "tags": {"highway": "tertiary"}, "geometry": _g((61.22, 10.8), (61.23, 10.81))},
    {"type": "way", "id": 7, "tags": {"railway": "abandoned"}, "geometry": _g((61.22, 10.7), (61.23, 10.71))},
    {"type": "way", "id": 8, "tags": {"highway": "footway", "area": "yes"},
     "geometry": _g((61.2, 10.8), (61.2, 10.8002), (61.2001, 10.8002), (61.2, 10.8))},
]}


def test_overpass_to_geojson():
    fc = fetch.overpass_to_geojson(OVERPASS_SAMPLE)
    by = {f["properties"]["osm_id"]: f for f in fc["features"]}
    assert by[1]["properties"]["kind"] == "track" and by[1]["geometry"]["type"] == "LineString"
    assert by[2]["properties"]["kind"] == "building" and by[2]["geometry"]["type"] == "Polygon"
    assert by[3]["properties"]["kind"] == "cattle_grid" and by[3]["geometry"]["type"] == "Point"
    assert by[4]["properties"]["kind"] == "water" and by[4]["geometry"]["type"] == "MultiPolygon"
    ring = by[4]["geometry"]["coordinates"][0][0]
    assert len(ring) == 5 and ring[0] == ring[-1]
    assert by[5]["properties"]["kind"] == "waterway"
    assert by[6]["properties"]["kind"] == "road_major"
    assert by[7]["properties"]["kind"] == "railway_disused"
    assert by[8]["geometry"]["type"] == "Polygon" and by[8]["properties"]["kind"] == "path"
    feats = score.Features(fc)
    assert len(feats.roads) == 2 and feats.points["cattle_grid"] and feats.polys["water"]


def test_osm_features_uses_mirror_when_primary_blocked(net):
    install, calls = net

    def router(method, url, params, data):
        if "overpass-api.de" in url:
            return proxy_block(method, url, params, data)
        assert method == "POST" and "cattle_grid" in data["data"] and "out geom" in data["data"]
        return FakeResp(json.dumps(OVERPASS_SAMPLE), ctype="application/json")
    install(router)
    fc = fetch.osm_features((280000.0, 6790000.0, 281000.0, 6791000.0))
    assert fc["source"].startswith("https://overpass.kumi.systems") and len(fc["features"]) == 8
    n = len(calls)
    fetch.osm_features((280000.0, 6790000.0, 281000.0, 6791000.0))
    assert len(calls) == n


SR16_CAPS = b"""<?xml version="1.0"?><WMS_Capabilities xmlns="http://www.opengis.net/wms" version="1.3.0"><Capability>
<Request><GetFeatureInfo><Format>text/plain</Format><Format>application/vnd.ogc.gml</Format></GetFeatureInfo></Request>
<Layer><Title>SR16</Title>
 <Layer queryable="1"><Name>SRRTRESLAG</Name><Title>Treslag</Title></Layer>
 <Layer queryable="1"><Name>SRRMHOYDE</Name><Title>Middelhoyde</Title></Layer>
 <Layer queryable="1"><Name>SRRVOLMB</Name><Title>Volum m/bark</Title></Layer>
</Layer></Capability></WMS_Capabilities>"""


def test_sr16_featureinfo(net):
    install, _ = net

    def router(method, url, params, data):
        if params.get("SERVICE") == "WCS":
            return FakeResp(OWS_EXC, ctype="text/xml")
        if params.get("REQUEST") == "GetCapabilities":
            return FakeResp(SR16_CAPS, ctype="text/xml")
        assert params["REQUEST"] == "GetFeatureInfo" and params["INFO_FORMAT"] == "text/plain"
        v = {"SRRTRESLAG": "2", "SRRMHOYDE": "17.5", "SRRVOLMB": "180"}[params["LAYERS"]]
        cls = "\n    class = 'Furu'" if params["LAYERS"] == "SRRTRESLAG" else ""
        return FakeResp(f"GetFeatureInfo results:\n\nLayer '{params['LAYERS']}'\n  Feature 0:\n    x = '1.5'\n"
                        f"    value_0 = '{v}'\n    value_list = '{v}'{cls}\n", ctype="text/plain")
    install(router)
    x, y = to_utm(61.21, 10.93)
    res = fetch.sr16((x - 500, y - 500, x + 500, y + 500), points=[(float(x), float(y))])
    assert res["chosen"] == {"species": "SRRTRESLAG", "height": "SRRMHOYDE", "volume": "SRRVOLMB"}
    p = res["points"][0]
    assert p["species"] == 2 and p["species_label"] == "Furu" and p["height"] == 17.5
    assert score.sr16_point_ll(p) == (0.0, "pine")
    assert fetch.parse_featureinfo("<SRRTRESLAG_feature><value_0>3</value_0></SRRTRESLAG_feature>") == (3.0, None)
    assert fetch.sr16_species_name(1) == "spruce"


# ----------------------------------------------------------------------------- CLI end to end (synthetic data)
def _fake_sources(monkeypatch, blocked=False):
    from hordejakt.refine import cli
    dtm, dom, fc = synthetic_scene()
    if blocked:
        def dtm_tile(*a, **k):
            raise fetch.FetchBlocked(["wcs.geonorge.no", "ws.geonorge.no"])
    else:
        def dtm_tile(*a, **k):
            return dtm
    monkeypatch.setattr(fetch, "dtm_tile", dtm_tile)
    monkeypatch.setattr(fetch, "dom_tile", lambda *a, **k: dom)
    monkeypatch.setattr(fetch, "osm_features", lambda *a, **k: fc)

    def sr16(bbox, points=None, **k):
        return {"points": [{"x": x, "y": y, "species": 2.0, "height": 18.0} for x, y in points], "notes": []}
    monkeypatch.setattr(fetch, "sr16", sr16)
    return cli


def test_cli_end_to_end(monkeypatch, tmp_path, capsys):
    cli = _fake_sources(monkeypatch)
    lat, lon = (float(v) for v in to_wgs84(TX, TY))
    hs = tmp_path / "hotspots.json"
    hs.write_text(json.dumps({"hotspots": [{"lat": lat, "lon": lon, "p_cell": 1e-4, "p_within_1.5km": 0.01}]}))
    rc = cli.main(["--hotspots", str(hs), "--top", "1", "--radius-km", "1.2", "--res", "4", "--work-res", "4",
                   "--pool", "80", "--min-sep", "30", "--skip-preflight", "--out-dir", str(tmp_path)])
    assert rc == 0
    d = json.loads((tmp_path / "refined_candidates.json").read_text())
    cands = d["candidates"]                                   # sorted by p_abs (search probability)
    dist = [float(np.hypot(*(np.array(to_utm(c["lat"], c["lon"])) - (TX, TY)))) for c in cands]
    k = int(np.argmin(dist))
    top = cands[k]
    assert dist[k] <= 6.0 and top["score_rank_in_tile"] == 1 and top["score"] == max(c["score"] for c in cands)
    assert top["rank"] <= 3                                   # and among the three most probable search discs
    assert top["parking"]["road"].startswith("track/grade2") and top["p_abs"] > 0
    assert top["terms"]["sr16_point"] == 0.0
    csv_text = (tmp_path / "refined_candidates.csv").read_text()
    assert csv_text.splitlines()[0].startswith("rank,p_abs") and len(csv_text.splitlines()) == len(d["candidates"]) + 1
    plan = (tmp_path / "field_plan.md").read_text()
    assert "| 1 |" in plan and "google.com/maps/dir" in plan and "norgeskart.no" in plan


def test_cli_reports_blocked_hosts(monkeypatch, tmp_path, capsys):
    cli = _fake_sources(monkeypatch, blocked=True)
    hs = tmp_path / "hotspots.json"
    hs.write_text(json.dumps({"hotspots": [{"lat": 61.21, "lon": 10.93, "p_within_1.5km": 0.01}]}))
    rc = cli.main(["--hotspots", str(hs), "--top", "1", "--skip-preflight", "--out-dir", str(tmp_path)])
    err = capsys.readouterr().err
    assert rc == 2 and "wcs.geonorge.no" in err and "ws.geonorge.no" in err and "allowed domains" in err
    assert "No candidates" in (tmp_path / "field_plan.md").read_text()


def test_field_plan_orders_by_probability_rate():
    from hordejakt.refine.cli import plan
    mk = lambda p, lat, walk: {"p_abs": p, "lat": lat, "lon": 10.9, "walk_time_min": walk, "parking": {"lat": lat - 0.003, "lon": 10.9}}
    recs = [mk(1.0, 61.0, 30.0), mk(0.9, 61.001, 3.0), mk(0.2, 62.0, 5.0)]
    stops = plan(recs, start=(61.0, 10.9))
    assert [s["rec"]["p_abs"] for s in stops] == [0.9, 1.0, 0.2]
    assert stops[-1]["drive_min"] > 100
