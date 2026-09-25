"""Tests for hordejakt.layers.weather.

Run:  .venv/bin/python -m pytest -q tests/test_weather.py
  or  .venv/bin/python tests/test_weather.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hordejakt import DEFAULTNO  # noqa: E402
from hordejakt.grid import GRID  # noqa: E402
from hordejakt.layers import weather  # noqa: E402
from hordejakt.layers.base import LayerResult  # noqa: E402
from hordejakt.layers.defaultno_fusion import decode_rle  # noqa: E402

PLACES = {
    "rena": (61.13, 11.37), "elverum": (60.88, 11.56), "kongsvinger": (60.19, 12.00), "koppang": (61.57, 11.04),
    "nord_odal": (60.39, 11.56), "bergen": (60.39, 5.33), "trondheim": (63.43, 10.39), "oslo": (59.91, 10.75),
    "froland": (58.53, 8.63), "larvik": (59.05, 10.03),
}
ALWAYS = {"weather_clear_sky_2109_evening", "weather_sun_2309_clear_areas", "weather_no_fog_2309_morning",
          "weather_calm_2309_1749", "weather_overcast_2409", "weather_rain_2409_morning",
          "weather_no_rain_2309_evening_froland", "weather_skyanalyse_2209"}
FULL_COVERAGE = {"weather_clear_sky_2109_evening", "weather_sun_2309_clear_areas", "weather_no_fog_2309_morning",
                 "weather_no_rain_2309_evening_froland", "weather_skyanalyse_2209", "weather_dn_rain_since_2109"}

_CACHE = {}


def layers(include_dn=False):
    if include_dn not in _CACHE:
        res = weather.build(GRID, {"weather_include_defaultno_derived": include_dn})
        _CACHE[include_dn] = {L.name: L for L in res}
    return _CACHE[include_dn]


def at(layer, place):
    la, lo = PLACES[place]
    return float(GRID.sample(layer.loglik, la, lo))


def test_contract_default():
    ls = layers(False)
    assert set(ls) == ALWAYS
    groups = [L.independence_group for L in ls.values()]
    assert len(set(groups)) == len(groups), "each weather observation should have its own group"
    for L in ls.values():
        assert isinstance(L, LayerResult)
        assert L.loglik.shape == GRID.shape, L.name
        assert 0.0 < L.reliability < 1.0 and not L.hard
        assert L.independence_group != "defaultno_model", "default.no-derived layer leaked into default cfg"
        ll = L.loglik
        assert not np.isinf(ll).any(), L.name
        assert np.nanmax(ll) <= 1e-9, f"{L.name}: log P must be <= 0"
        assert np.isfinite(ll).mean() > 0.5, L.name
        assert L.description and L.sources


def test_gate():
    ls = layers(True)
    assert set(ls) == ALWAYS | {"weather_dn_rain_since_2109"}
    assert ls["weather_dn_rain_since_2109"].independence_group == "defaultno_model"
    assert weather._include_defaultno({}) is False
    assert weather._include_defaultno({"weather_include_defaultno_derived": "auto",
                                       "skip_layers": ["defaultno_fusion_utenfly"]}) is True
    assert weather._include_defaultno({"weather_include_defaultno_derived": "auto", "skip": ["defaultno_fusion"]})
    assert weather._include_defaultno({"weather_include_defaultno_derived": "auto"}) is False


def test_finite_where_expected():
    ls = layers(True)
    L, O = GRID.mesh()
    core = (L >= 60.0) & (L <= 62.0) & (O >= 10.0) & (O <= 12.5)  # Østlandet interior: every product covers it
    for name, lay in ls.items():
        if name in FULL_COVERAGE:
            assert np.isfinite(lay.loglik).all(), name
        assert np.isfinite(lay.loglik[core]).all(), name
        for p in ("rena", "elverum", "koppang", "nord_odal"):
            assert np.isfinite(at(lay, p)), (name, p)


def test_robust_mixture_finite():
    for lay in layers(True).values():
        r = lay.robust()
        assert np.isfinite(r).all(), lay.name
        assert r.min() >= np.log(1 - lay.reliability) - 1e-9, lay.name


def test_sanity_fog():
    fog = layers()["weather_no_fog_2309_morning"]
    assert at(fog, "nord_odal") < at(fog, "elverum") - 1.0
    assert abs(at(fog, "elverum")) < 1e-6


def test_sanity_sky_and_sun():
    ls = layers()
    sky = ls["weather_clear_sky_2109_evening"]
    assert at(sky, "bergen") < at(sky, "rena") - 1.0
    assert at(sky, "trondheim") < at(sky, "elverum") - 1.0
    sun = ls["weather_sun_2309_clear_areas"]
    for inside in ("kongsvinger", "elverum", "rena"):
        for outside in ("oslo", "bergen"):
            assert at(sun, inside) > at(sun, outside) + 0.5, (inside, outside)


def test_sanity_wind_overcast_rain():
    ls = layers()
    calm = ls["weather_calm_2309_1749"]
    assert at(calm, "bergen") < at(calm, "rena") - 0.5          # windy west coast at 17:49
    over = ls["weather_overcast_2409"]
    assert at(over, "bergen") < at(over, "koppang")             # sunnier west on 24.09
    fro = ls["weather_no_rain_2309_evening_froland"]
    assert at(fro, "froland") < at(fro, "rena") - 1.0
    sky = ls["weather_skyanalyse_2209"]
    assert at(sky, "froland") > at(sky, "rena")


def test_radar_decode():
    ll, w, tid = weather._radar_ll(GRID, GRID.mesh())
    assert tid == "20260924T163500Z"
    L, O = GRID.mesh()
    oslofjord = (L >= 59.0) & (L <= 60.0) & (O >= 10.0) & (O <= 11.5)   # heavy echoes at 18:35
    hedmark = (L >= 60.8) & (L <= 61.6) & (O >= 10.8) & (O <= 11.6)     # dry at 18:35
    assert np.nanmin(ll[oslofjord]) < -0.6
    assert np.nanmin(ll[hedmark]) > -0.3
    assert np.isnan(GRID.sample(ll, 60.39, 5.33))  # Bergen is west of the image (7°E)
    assert 0.0 <= np.nanmin(w) and np.nanmax(w) <= 1.0


def test_regn_decode():
    d = json.load(open(DEFAULTNO / "regn.json"))
    lop = np.array(d["lop"]).reshape(-1, 4)
    assert len(d["lop"]) % 4 == 0
    assert np.all(np.diff(lop[:, 0]) >= 0) and set(np.unique(lop[:, 3])) <= {1, 2, 3}
    cls = decode_rle(d, GRID)
    assert cls[GRID.index(60.39, 5.33)] == 3        # Bergen: over 6 mm since Sunday
    assert cls[GRID.index(60.88, 11.56)] <= 1       # Elverum: (nearly) dry
    dn = layers(True)["weather_dn_rain_since_2109"]
    assert at(dn, "bergen") < at(dn, "elverum") - 1.0


def test_innhold_parsing_matches_copy():
    src = weather._innhold_text()
    for name in ("SOL_I_DAG", "TAAKE", "SKYDEKKE"):
        parsed = weather._rings(src, name)
        assert parsed == weather._FALLBACK[name], name
    (la, lo), outer = weather._skyanalyse(src)
    assert (la, lo, outer) == (58.7, 8.27, 45.0)
    assert weather._froland(src) == (58.53, 8.63)


if __name__ == "__main__":
    fails = 0
    for k, f in list(globals().items()):
        if k.startswith("test_") and callable(f):
            try:
                f()
                print("ok  ", k)
            except AssertionError as e:
                fails += 1
                print("FAIL", k, e)
    sys.exit(1 if fails else 0)
