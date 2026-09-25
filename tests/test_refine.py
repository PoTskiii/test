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
from hordejakt.refine.raster import Raster, make_transform, to_utm, to_wgs84, true_bearing_xy  # noqa: E402

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
        circle({"landuse": "farmland"}, 900, -900, 150),
    ]}
    dom = None
    if with_dom:
        chm = np.full(dtm.shape, 18.0, np.float32)
        # old logging (regrowth ~4 m) between the road and T
        cu = (X - TX) * U[0] + (Y - TY) * U[1]
        cv = (X - TX) * V[0] + (Y - TY) * V[1]
        chm[(np.abs(cu) < 150) & (cv > -300) & (cv < -60)] = 4.0
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
