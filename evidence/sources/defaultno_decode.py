"""Decoders for the default.no map-layer mirror (MagnusPladsen/hordejakten-2026, fetched 24.09 18:36).

Recipes are taken from src/lib/defaultno.ts (tegnGrid, fugl, imageOverlay calls) and
src/components/Kart.tsx (eiffel_*, plan, rejected, pins). See defaultno_mirror.md for semantics.

Usage:
    from defaultno_decode import load_grid, grid_value, overlay_pixel_to_latlon, SITE_PNG_TRUE_CENTRE
    g = load_grid('fusjon/alle.json')          # dict with level array + geometry
    grid_value(g, 61.45, 11.10)                 # -> 3 (best 2 %)
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

MIRROR = '/home/user/test/data/raw/magnus/public/data/defaultno'
RECOVERED = '/home/user/test/evidence/sources/defaultno_recovered'  # pre-edit plan/steder/pins (git e431102^)


def _p(rel: str) -> str:
    return rel if os.path.isabs(rel) else os.path.join(MIRROR, rel)


def load_grid(rel: str) -> dict:
    """Decode a run-length grid {lat0, dlat, lon0, dlon, lop}.

    lop is a flat int list of 4-tuples [i, j, length, level]. Row i, columns j .. j+length-1 all have
    `level`. Cell centre: lat = lat0 + i*dlat, lon = lon0 + j*dlon. Cell extent: centre +/- dlat/2,
    +/- dlon/2 (tegnGrid draws [lat-dlat/2, lon0+(j-0.5)dlon] .. [lat+dlat/2, lon0+(j+len-0.5)dlon]).
    Cells not covered by any run are level 0 (= not in the top 40 % / not drawn).
    """
    d = json.load(open(_p(rel)))
    lop = d['lop']
    assert len(lop) % 4 == 0
    runs = np.asarray(lop, dtype=np.int64).reshape(-1, 4)
    ni = int(runs[:, 0].max()) + 1
    nj = int((runs[:, 1] + runs[:, 2]).max())
    lev = np.zeros((ni, nj), dtype=np.int8)
    for i, j, L, k in runs:
        lev[i, j:j + L] = k
    return {
        'level': lev,
        'lat0': d['lat0'], 'dlat': d['dlat'], 'lon0': d['lon0'], 'dlon': d['dlon'],
        'meta': {k: v for k, v in d.items() if k not in ('lop', 'lat0', 'dlat', 'lon0', 'dlon')},
    }


def grid_value(g: dict, lat: float, lon: float) -> int:
    i = int(round((lat - g['lat0']) / g['dlat']))
    j = int(round((lon - g['lon0']) / g['dlon']))
    lev = g['level']
    if 0 <= i < lev.shape[0] and 0 <= j < lev.shape[1]:
        return int(lev[i, j])
    return 0


def grid_cells(g: dict):
    """Yield (lat_centre, lon_centre, level) for every non-zero cell."""
    ii, jj = np.nonzero(g['level'])
    for i, j in zip(ii, jj):
        yield g['lat0'] + i * g['dlat'], g['lon0'] + j * g['dlon'], int(g['level'][i, j])


def fugl_cells(species: str = 'orr'):
    """fugl.json: {steg: 0.02, orr: [[lat, lon, n]], stor: [...]}. [lat, lon] is the SW corner;
    cell spans lat..lat+steg, lon..lon+steg (see fugl() in defaultno.ts)."""
    d = json.load(open(_p('fugl.json')))
    s = d['steg']
    return [(la, lo, la + s, lo + s, n) for la, lo, n in d[species]]


def overlay_pixel_to_latlon(x: float, y: float, bounds, width: int, height: int, mercator: bool = False):
    """Map a PNG pixel (x right, y down, pixel-centre = +0.5) to lat/lon for an overlay with
    Leaflet bounds [[south, west], [north, east]]. default.no PNGs appear lat-linear (radar.png
    verified via airport icons); Leaflet itself stretches in Web-Mercator. For <=0.25 deg boxes the
    difference is < 1 px."""
    (s, w), (n, e) = bounds
    lon = w + (x + 0.5) / width * (e - w)
    if not mercator:
        lat = n - (y + 0.5) / height * (n - s)
    else:
        m = lambda l: math.log(math.tan(math.pi / 4 + math.radians(l) / 2))
        my = m(n) - (y + 0.5) / height * (m(n) - m(s))
        lat = math.degrees(2 * math.atan(math.exp(my)) - math.pi / 2)
    return lat, lon


# steder/sites_NN.png and hogst/logging_NN.png for NN in 01..14, 61, 62 are NOT registered to the
# steder.json/omrader.json bounds of the same rank. Cross-correlation (clear-cut mosaic) and
# site-on-red-pixel tests give these true centres (box size unchanged: 0.2162 deg lat):
SITE_PNG_TRUE_CENTRE = {
    1: (61.45, 11.00),   # rail-distance test: median error 11 m vs tog_m; 47/54 sites on red px
    2: (61.10, 11.00),   # hogst dice 0.86; 11/13 sites on red px
    10: (60.90, 11.00),  # hogst dice 0.63
    11: (60.82, 10.85),  # hogst dice 0.58 (= centre of rank 13)
    # 3-9, 12-14, 61, 62: unresolved (no match inside the registered-PNG mosaic) -> do not use.
}
REGISTERED_PNG_RANKS = [21, 22, 31, 32, 41, 71, 72, 73, 74, 81, 82, 83, 91, 101, 102, 111, 112, 121]

SITE_COLOURS = {  # steder/sites_*.png RGBA
    (230, 40, 40, 200): 'strong',      # "Sterkt treff"
    (250, 200, 40, 140): 'possible',   # "Mulig treff"
    (40, 110, 230, 60): 'road_band',   # "Riktig avstand fra vei"
}
HOGST_COLOURS = {  # hogst/logging_*.png RGBA (Global Forest Watch loss year)
    (255, 210, 60, 90): 'cut_2016plus',
    (255, 120, 20, 150): 'cut_2022plus',
    (230, 20, 20, 200): 'cut_2024_25',
    (40, 40, 40, 255): 'railway',
}


def load_sites(recovered: bool = True):
    """steder.json sites; recovered=True uses the pre-edit default.no copy (126 sites) rather than the
    magnus-edited mirror (117 sites, Birkebeinerveien removed 25.09 14:12)."""
    path = os.path.join(RECOVERED, 'steder.json') if recovered else _p('steder.json')
    return json.load(open(path))


if __name__ == '__main__':
    g = load_grid('fusjon/alle.json')
    assert grid_value(g, 61.45, 11.10) == 3
    counts = {k: int((g['level'] == k).sum()) for k in (1, 2, 3)}
    assert counts == {1: 1096, 2: 556, 3: 86}, counts
    s = load_grid('sjelden.json')
    assert s['meta']['grad'] == 40.0
    st = load_sites(True)
    assert len(st['steder']) == 126 and st['steder'][0]['veinavn'] == 'Birkebeinerveien'
    assert len(load_sites(False)['steder']) == 117
    print('ok', counts, g['level'].shape)
