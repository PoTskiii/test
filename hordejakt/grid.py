"""Common analysis grid.

Cell centres sit on multiples of (DLAT, DLON) = (0.005°, 0.01°) so they line up
with the community's 810-891 m elevation cells (hoyde891.json). At 61°N a cell
is ~556 m x ~540 m.
"""
from dataclasses import dataclass

import numpy as np

DLAT = 0.005
DLON = 0.01


@dataclass(frozen=True)
class Grid:
    lat_min: float = 58.0
    lat_max: float = 64.5
    lon_min: float = 4.5
    lon_max: float = 13.5
    dlat: float = DLAT
    dlon: float = DLON

    @property
    def nlat(self):
        return int(round((self.lat_max - self.lat_min) / self.dlat)) + 1

    @property
    def nlon(self):
        return int(round((self.lon_max - self.lon_min) / self.dlon)) + 1

    @property
    def shape(self):
        return (self.nlat, self.nlon)

    @property
    def lats(self):
        return self.lat_min + np.arange(self.nlat) * self.dlat

    @property
    def lons(self):
        return self.lon_min + np.arange(self.nlon) * self.dlon

    def mesh(self):
        return np.meshgrid(self.lats, self.lons, indexing="ij")

    def index(self, lat, lon):
        """Nearest cell index for arrays of lat/lon; -1 where outside."""
        i = np.rint((np.asarray(lat) - self.lat_min) / self.dlat).astype(int)
        j = np.rint((np.asarray(lon) - self.lon_min) / self.dlon).astype(int)
        bad = (i < 0) | (i >= self.nlat) | (j < 0) | (j >= self.nlon)
        return np.where(bad, -1, i), np.where(bad, -1, j)

    def empty(self, fill=np.nan, dtype=float):
        return np.full(self.shape, fill, dtype=dtype)

    def paint_points(self, lat, lon, values, fill=np.nan, reduce="max"):
        """Rasterise point values onto the grid (nearest cell)."""
        out = self.empty(fill)
        i, j = self.index(lat, lon)
        ok = i >= 0
        i, j, v = i[ok], j[ok], np.asarray(values, float)[ok]
        if reduce == "max":
            tmp = np.full(self.shape, -np.inf)
            np.maximum.at(tmp, (i, j), v)
            has = np.isfinite(tmp)
            out[has] = tmp[has]
        elif reduce == "mean":
            s = np.zeros(self.shape)
            n = np.zeros(self.shape)
            np.add.at(s, (i, j), v)
            np.add.at(n, (i, j), 1)
            has = n > 0
            out[has] = s[has] / n[has]
        else:
            out[i, j] = v
        return out

    def paint_blocks(self, lat, lon, dlat, dlon, values, fill=np.nan):
        """Rasterise coarse cells (centre lat/lon, size dlat x dlon) onto the grid."""
        out = self.empty(fill)
        L, O = self.mesh()
        lat = np.asarray(lat)
        lon = np.asarray(lon)
        vals = np.asarray(values, float)
        i0 = np.rint((lat - dlat / 2 - self.lat_min) / self.dlat).astype(int)
        i1 = np.rint((lat + dlat / 2 - self.lat_min) / self.dlat).astype(int)
        j0 = np.rint((lon - dlon / 2 - self.lon_min) / self.dlon).astype(int)
        j1 = np.rint((lon + dlon / 2 - self.lon_min) / self.dlon).astype(int)
        for a, b, c, d, v in zip(i0, i1, j0, j1, vals):
            a, c = max(a, 0), max(c, 0)
            b, d = min(b, self.nlat - 1), min(d, self.nlon - 1)
            if a > b or c > d:
                continue
            # half-open on the upper edge so neighbouring blocks do not overlap
            out[a:max(b, a + 1), c:max(d, c + 1)] = v
        return out

    def sample(self, arr, lat, lon, default=np.nan):
        i, j = self.index(lat, lon)
        res = np.full(np.shape(i), default, dtype=float)
        ok = i >= 0
        res[ok] = arr[i[ok], j[ok]]
        return res


GRID = Grid()
