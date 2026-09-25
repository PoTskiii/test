"""Areas the box is very unlikely to be in.

* Active military ranges (Forsvaret skyte- og øvingsfelt): «INGEN SKYTING», and
  the organiser would not put a public treasure hunt there.
* Norway only (land): outside the Norway polygon is excluded.
"""
import json

import numpy as np
from shapely import contains_xy
from shapely.geometry import shape, Polygon

from .. import DEFAULTNO, MAGNUS
from .base import LayerResult


def _mask_polygon(grid, geom):
    L, O = grid.mesh()
    minx, miny, maxx, maxy = geom.bounds
    m = np.zeros(grid.shape, bool)
    sel = (O >= minx) & (O <= maxx) & (L >= miny) & (L <= maxy)
    if sel.any():
        m[sel] = contains_xy(geom, O[sel], L[sel])
    return m


def build(grid, cfg):
    out = []
    sk = json.load(open(DEFAULTNO / "skytefelt.json"))
    mil = np.zeros(grid.shape, bool)
    for f in sk["felt"]:
        if f.get("status") not in (None, "brukes"):
            continue
        for ring in f["ringer"]:
            # rings are [[lat, lon], ...]
            poly = Polygon([(p[1], p[0]) for p in ring])
            if poly.is_valid and poly.area > 0:
                mil |= _mask_polygon(grid, poly)
    out.append(LayerResult("exclude_military_ranges", np.where(mil, -5.0, 0.0), reliability=0.85,
                           independence_group="military", description="Active Forsvaret firing/training ranges (default.no skytefelt.json)",
                           sources=["default.no skytefelt.json", "tavla «INGEN SKYTING»"]))

    no = json.load(open(MAGNUS / "public" / "data" / "norge.json"))
    norway = shape(no["geometry"])
    land = _mask_polygon(grid, norway)
    out.append(LayerResult("norway_land", np.where(land, 0.0, -np.inf), reliability=1.0,
                           independence_group="norway", hard=True,
                           description="Box is in Norway, reachable by car without ferry", sources=["Horde rules"]))
    return out
