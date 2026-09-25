"""Elevation band (HORDEMINUS -> «2,7 eiffeltårn» -> 810 / 875 / 891 m) and
road access (5-10 min walk, car to the south-east).

Source: MagnusPladsen hoyde891.json — cells of 0.005° x 0.01° whose Kartverket
elevation is 790-911 m and that lie within 900 m of a road; fields
[lat, lon, z_m, dist_to_road_m, road_to_SE(0/1)]. Coverage rectangle is the
bounding box of the file. Outside it elevation is unknown and the layer is
filled with the covered-area expectation (neither rewarded nor punished).
"""
import json

import numpy as np

from .. import MAGNUS
from .base import LayerResult

# 2.7 x Eiffel: 300 m (no antenna) = 810, 324 m (2000-2022) = 875, 330 m = 891
CENTRES = [(810.0, 0.4), (875.0, 0.2), (891.0, 0.4)]
SIGMA_M = 20.0
OUT_OF_BAND_LL = -6.0


def _load():
    d = json.load(open(MAGNUS / "public" / "data" / "hoyde891.json"))
    a = np.array(d["punkter"], float)
    return a, d["dlat"], d["dlon"]


def _fill_outside(ll, inside_rect):
    """Cells outside the surveyed rectangle get log E[L] of the surveyed area."""
    vals = ll[inside_rect]
    fill = np.log(np.mean(np.exp(vals - vals.max()))) + vals.max()
    return np.where(inside_rect, ll, fill)


def build(grid, cfg):
    a, dlat, dlon = _load()
    lat, lon, z, dist, se = a.T
    L, O = grid.mesh()
    rect = (L >= lat.min() - dlat / 2) & (L <= lat.max() + dlat / 2) & (O >= lon.min() - dlon / 2) & (O <= lon.max() + dlon / 2)

    # --- elevation band
    mix = sum(w * np.exp(-0.5 * ((z - c) / SIGMA_M) ** 2) for c, w in CENTRES)
    ll_pts = np.log(mix / max(w for _, w in CENTRES) + 1e-9)
    ll_elev = grid.paint_points(lat, lon, ll_pts, fill=np.nan)
    ll_elev = np.where(np.isnan(ll_elev), OUT_OF_BAND_LL, ll_elev)
    ll_elev = _fill_outside(ll_elev, rect)

    # --- walking distance from the car: 5-10 min through untracked forest, uphill
    # ~ 250-700 m at 3-4 km/h; accept 120-900 m with soft edges
    d = np.asarray(dist)
    ll_road_pts = np.where(d < 120, -0.5 * ((120 - d) / 60) ** 2,
                           np.where(d > 700, -0.5 * ((d - 700) / 150) ** 2, 0.0))
    ll_road = grid.paint_points(lat, lon, ll_road_pts, fill=np.nan)  # NaN = unknown distance

    # --- car / road lies to the SE of the box («KOM FRA DEN VEIEN ←»; left in image ≈ 130°)
    ll_se_pts = np.where(se > 0.5, 0.0, -1.2)
    ll_se = grid.paint_points(lat, lon, ll_se_pts, fill=np.nan)

    return [
        LayerResult("elevation_band_810_891", ll_elev, reliability=0.65, independence_group="elevation_hint",
                    description="HORDEMINUS -> 2.7 Eiffel towers -> 810/875/891 m a.s.l. (Horde AI in app, 24.09); hoyde891.json cells",
                    sources=["Horde AI «2,7 eiffeltårn stablet oppå hverandre»", "MagnusPladsen hoyde891.json (Kartverket DTM)"]),
        LayerResult("walk_distance_from_road", ll_road, reliability=0.55, independence_group="road_access",
                    description="5-10 min walk from car, no paths; distance to nearest road 120-900 m (only known inside the band cells)",
                    sources=["tavla: «INGEN STIER», walk 5-10 min (community reading)"]),
        LayerResult("road_to_southeast", ll_se, reliability=0.45, independence_group="approach_direction",
                    description="Road lies SE of the box: «KOM FRA DEN VEIEN ←» with camera facing ~221°; sign pointed 118-120°",
                    sources=["tavla 24.09 «KOM FRA DEN VEIEN» + arrow", "tavla «KAMERA 41 ØST»"]),
    ]
