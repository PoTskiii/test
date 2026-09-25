"""Raster container and coordinate helpers (EPSG:25833 = ETRS89 / UTM 33N).

A ``Raster`` is a 2-D float array (row 0 = north) plus a GDAL/rasterio-style
affine transform ``(a, b, c, d, e, f)``:  x = c + a*col + b*row,
y = f + d*col + e*row  for pixel *edges*; pixel centres sit at +0.5.
``affine.Affine`` (shipped with rasterio) is used when importable, otherwise a
plain tuple with the same order - both index identically.
"""
from dataclasses import dataclass, field

import numpy as np
from pyproj import Transformer
from scipy.ndimage import map_coordinates

try:  # optional, ships with rasterio
    from affine import Affine as _Affine
except Exception:  # pragma: no cover - exercised only without rasterio
    _Affine = None

CRS = "EPSG:25833"
_TO_UTM = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
_TO_WGS = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True)


def make_transform(xmin, ymax, res_x, res_y=None):
    res_y = res_x if res_y is None else res_y
    t = (float(res_x), 0.0, float(xmin), 0.0, -float(res_y), float(ymax))
    return _Affine(*t) if _Affine is not None else t


def to_utm(lat, lon):
    """WGS84 lat/lon (scalars or arrays) -> EPSG:25833 x (east), y (north)."""
    x, y = _TO_UTM.transform(np.asarray(lon, float), np.asarray(lat, float))
    return x, y


def to_wgs84(x, y):
    """EPSG:25833 x, y -> WGS84 (lat, lon)."""
    lon, lat = _TO_WGS.transform(np.asarray(x, float), np.asarray(y, float))
    return lat, lon


def bbox_around(lat, lon, radius_m):
    """Square EPSG:25833 bbox (xmin, ymin, xmax, ymax) centred on lat/lon."""
    x, y = to_utm(lat, lon)
    x, y = float(x), float(y)
    return (x - radius_m, y - radius_m, x + radius_m, y + radius_m)


def snap_bbox(bbox, res):
    """Expand a bbox outward so its edges are multiples of res."""
    xmin, ymin, xmax, ymax = bbox
    return (np.floor(xmin / res) * res, np.floor(ymin / res) * res,
            np.ceil(xmax / res) * res, np.ceil(ymax / res) * res)


def bbox_to_wgs84(bbox):
    """(south, west, north, east) in degrees covering an EPSG:25833 bbox."""
    xmin, ymin, xmax, ymax = bbox
    xs = np.array([xmin, xmax, xmax, xmin, (xmin + xmax) / 2, (xmin + xmax) / 2])
    ys = np.array([ymin, ymin, ymax, ymax, ymin, ymax])
    lat, lon = to_wgs84(xs, ys)
    return float(lat.min()), float(lon.min()), float(lat.max()), float(lon.max())


def bearing_xy(x0, y0, x1, y1):
    """Grid bearing (deg, clockwise from grid north) from point 0 to point 1.

    In UTM 33 grid north differs from true north by the meridian convergence
    (about -3.5 deg at 11 E, 61 N: a true-SE line has grid bearing ~138.5);
    use ``true_bearing_xy`` for compass/whiteboard directions."""
    return (np.degrees(np.arctan2(np.asarray(x1) - x0, np.asarray(y1) - y0)) + 360.0) % 360.0


def convergence_deg(x, y):
    """gamma (deg) such that true_bearing = grid_bearing + gamma (computed numerically)."""
    lat, lon = to_wgs84(x, y)
    x0, y0 = to_utm(lat, lon)
    x1, y1 = to_utm(np.asarray(lat) + 0.001, lon)
    return -((bearing_xy(x0, y0, x1, y1) + 180.0) % 360.0 - 180.0)


def true_bearing_xy(x0, y0, x1, y1):
    return (bearing_xy(x0, y0, x1, y1) + convergence_deg(x0, y0)) % 360.0


def angdiff(a, b):
    return np.abs((np.asarray(a) - np.asarray(b) + 180.0) % 360.0 - 180.0)


@dataclass
class Raster:
    data: np.ndarray
    transform: tuple
    crs: str = CRS
    source: str = ""
    meta: dict = field(default_factory=dict)

    # --- geometry -----------------------------------------------------
    @property
    def shape(self):
        return self.data.shape

    @property
    def res(self):
        return float(abs(self.transform[0])), float(abs(self.transform[4]))

    @property
    def bounds(self):
        a, b, c, d, e, f = tuple(self.transform)[:6]
        h, w = self.data.shape
        xs = (c, c + a * w)
        ys = (f, f + e * h)
        return (min(xs), min(ys), max(xs), max(ys))

    def xy(self, row, col):
        """Pixel-centre coordinates for (fractional) row/col arrays."""
        a, b, c, d, e, f = tuple(self.transform)[:6]
        row = np.asarray(row, float) + 0.5
        col = np.asarray(col, float) + 0.5
        return c + a * col + b * row, f + d * col + e * row

    def rowcol(self, x, y):
        """Fractional (row, col) of pixel centres for coordinates (inverse of xy)."""
        a, b, c, d, e, f = tuple(self.transform)[:6]
        det = a * e - b * d
        dx, dy = np.asarray(x, float) - c, np.asarray(y, float) - f
        col = (e * dx - b * dy) / det
        row = (-d * dx + a * dy) / det
        return row - 0.5, col - 0.5

    def centres(self):
        h, w = self.shape
        rr, cc = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
        return self.xy(rr, cc)

    def axes(self):
        """1-D x (per column) and y (per row) pixel-centre coordinates (north-up only)."""
        h, w = self.shape
        x, _ = self.xy(np.zeros(w), np.arange(w))
        _, y = self.xy(np.arange(h), np.zeros(h))
        return x, y

    def sample(self, x, y, order=1, fill=np.nan):
        r, c = self.rowcol(x, y)
        r, c = np.atleast_1d(r), np.atleast_1d(c)
        data = np.asarray(self.data, float)
        nan = np.isnan(data)
        if nan.any():
            data = np.where(nan, np.nanmean(data) if (~nan).any() else 0.0, data)
        out = map_coordinates(data, [r.ravel(), c.ravel()], order=order, mode="nearest").reshape(r.shape)
        h, w = self.shape
        outside = (r < -0.5) | (r > h - 0.5) | (c < -0.5) | (c > w - 0.5)
        if nan.any():
            nn = map_coordinates(nan.astype(float), [r.ravel(), c.ravel()], order=0, mode="nearest").reshape(r.shape)
            outside |= nn > 0.5
        return np.where(outside, fill, out)

    def contains(self, x, y):
        xmin, ymin, xmax, ymax = self.bounds
        return (np.asarray(x) >= xmin) & (np.asarray(x) <= xmax) & (np.asarray(y) >= ymin) & (np.asarray(y) <= ymax)

    # --- resampling ---------------------------------------------------
    def resample(self, res, bbox=None, order=1):
        """Resample onto a north-up grid with pixel size `res` covering bbox
        (default: own bounds). Integer down-sampling uses block means."""
        xmin, ymin, xmax, ymax = bbox or self.bounds
        own = self.res[0]
        k = res / own
        if bbox is None and abs(k - round(k)) < 1e-6 and round(k) >= 2 and abs(self.transform[1]) < 1e-12:
            k = int(round(k))
            h, w = (self.shape[0] // k) * k, (self.shape[1] // k) * k
            blk = self.data[:h, :w].astype(float).reshape(h // k, k, w // k, k)
            with np.errstate(all="ignore"):
                data = np.nanmean(blk, axis=(1, 3))
            a, b, c, d, e, f = tuple(self.transform)[:6]
            return Raster(data.astype(np.float32), make_transform(c, f, res), self.crs, self.source, dict(self.meta))
        w = max(1, int(round((xmax - xmin) / res)))
        h = max(1, int(round((ymax - ymin) / res)))
        out = Raster(np.zeros((h, w), np.float32), make_transform(xmin, ymax, res), self.crs, self.source, dict(self.meta))
        X, Y = out.centres()
        out.data = self.sample(X, Y, order=order).astype(np.float32)
        return out

    def like(self, other, order=1):
        """This raster resampled onto `other`'s grid."""
        if other.shape == self.shape and np.allclose(tuple(other.transform)[:6], tuple(self.transform)[:6]):
            return self
        X, Y = other.centres()
        return Raster(self.sample(X, Y, order=order).astype(np.float32), other.transform, self.crs, self.source,
                      dict(self.meta))

    # --- persistence --------------------------------------------------
    def save(self, path):
        np.savez_compressed(path, data=self.data, transform=np.array(tuple(self.transform)[:6], float),
                            crs=self.crs, source=self.source)

    @classmethod
    def load(cls, path):
        z = np.load(path, allow_pickle=False)
        t = tuple(float(v) for v in z["transform"])
        return cls(z["data"], _Affine(*t) if _Affine is not None else t, str(z["crs"]), str(z["source"]))
