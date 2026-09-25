"""Fine-scale site score for the box (1-10 m) inside one coarse hotspot tile.

Every clue is a *soft* log-likelihood term ``ll <= 0`` (0 = fully consistent).
Each term has a reliability r (probability that the clue is valid and read
correctly) and enters the total through the same robust mixture as the coarse
engine (hordejakt/layers/base.py):

    contribution = weight * log(r * exp(ll) + (1 - r))      in [weight*log(1-r), 0]

so no single clue can veto a spot. Nothing is a hard filter except pixels
without terrain data.

Stage A (per pixel, work grid ~2 m)                                  r
  elevation      2.7 Eiffel towers: 810 / 875 / 891 m (w .4/.2/.4), sigma 12 m     0.85
  flat_ground    blueberry/heather on flat ground: slope 0-8 deg, soft 6 deg        0.60
  water_osm      «INGEN VANN ELLER VANNLYDER»: OSM lake/river/stream/spring
                 within 250 m penalised (soft 90 m)                                0.80
  water_dtm      same, streams derived from the DTM (D8, catchment >= 0.2 km2),
                 within 150 m (OSM misses small brooks; lower reliability)         0.40
  cabin          «INGEN HYTTE I NÆRHETEN»: any building within 400 m (soft 150)     0.75
  traffic        no traffic noise in 8 h: motorway..tertiary within 500 m (s 200)  0.70
  minor_road     unclassified/residential within 150 m (soft 80)                   0.30
  railway        active railway within 1000 m (soft 400)                           0.70
  path_nearby    «INGEN STIER»: footpath within 40 m (soft 25)                     0.40
  road_access    5-10 min walk: drivable road 120-600 m (soft 60/200). Pre-
                 selection proxy only: replaced by Stage B walk_time.              0.70
  landcover      military -4, farmland/residential/quarry.. -3, bog -1.5,
                 bare rock -1 (OSM landuse/natural polygons)                       0.75
  opening  (DOM) small opening at the box: canopy within ~3 m <= 4 m (soft 3)     0.65
  mature   (DOM) mature pine/spruce/birch around: canopy 8-30 m ring 13-24 m
                 (soft 4) and >= 70 % of the ring closed (>= 10 m; soft 15 %)      0.60
  sr16           (if SR16 rasters) pine/deciduous/spruce prior, mean height       0.30

Stage B (per candidate, best parking spot = argmax over drivable road points)
  direction      «KOM FRA DEN VEIEN ←»: true bearing box->car 130 +-40 deg
                 (weight .75) OR old sign reading: sign WNW of box pointing
                 118-120 deg magnetic -> car ~303 +-40 deg true (weight .25)       0.60
  walk_time      Tobler off-trail (x0.6) along the straight line, 4-11 min (s 3)  0.70
  uphill         climb car->box 3-150 m (downhill soft 8 m, steep soft 50 m)       0.60
  crossing       straight walk crosses stream (-3) / lake (-4) / >30 deg (-2)      0.60
  logging        «DET HAR VÆRT HOGD»: regrowth (canopy 0.5-8 m) >= 15 % of walk    0.35
  road_type      parking on track/service road preferred; primary -1, grade4/5 -0.7 0.50
  cattle_grid    «INGEN FERIST SOM JEG MERKA»: cattle grid within 1 km of parking  0.20
  morning_sun    first terrain sun (21.09) must be <= ~08:10 CEST                  0.35
  sr16_point     (if SR16 GetFeatureInfo samples) species prior                   0.30

The candidate's final score is  A_total - A_road_access + B_total.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, uniform_filter
from scipy.spatial import cKDTree
from shapely import STRtree, contains_xy, prepare
from shapely.geometry import LineString, Point, Polygon

from .raster import Raster, angdiff, convergence_deg, make_transform, to_utm, to_wgs84, true_bearing_xy

# --------------------------------------------------------------------------- parameters
PARAMS = {
    "elev_centres": [(810.0, 0.4), (875.0, 0.2), (891.0, 0.4)],
    "elev_sigma_m": 12.0,
    "slope_ok_deg": 8.0, "slope_soft_deg": 6.0,
    "water_radius_m": 250.0, "water_soft_m": 90.0,
    "dtm_stream_radius_m": 150.0, "dtm_stream_soft_m": 60.0, "dtm_stream_min_area_m2": 2.0e5, "dtm_stream_res_m": 10.0,
    "cabin_radius_m": 400.0, "cabin_soft_m": 150.0,
    "traffic_radius_m": 500.0, "traffic_soft_m": 200.0,
    "minor_radius_m": 150.0, "minor_soft_m": 80.0,
    "rail_radius_m": 1000.0, "rail_soft_m": 400.0,
    "path_radius_m": 40.0, "path_soft_m": 25.0,
    "road_lo_m": 120.0, "road_hi_m": 600.0, "road_soft_lo_m": 60.0, "road_soft_hi_m": 200.0,
    "opening_max_m": 4.0, "opening_soft_m": 3.0, "opening_radius_m": 3.0,
    "ring_inner_m": 8.0, "ring_outer_m": 30.0, "ring_lo_m": 13.0, "ring_hi_m": 24.0, "ring_soft_m": 4.0,
    "ring_closed_frac": 0.7, "ring_closed_soft": 0.15,
    # Stage B
    "dir_new_deg": 130.0, "dir_new_w": 0.75,
    "sign_magnetic_deg": 119.0, "declination_deg": 4.5, "dir_old_w": 0.25,  # sign WNW of box, pointing to box
    "dir_tol_deg": 40.0, "dir_soft_deg": 25.0,
    "walk_lo_min": 4.0, "walk_hi_min": 11.0, "walk_soft_min": 3.0, "offtrail_factor": 0.6,
    "climb_lo_m": 3.0, "climb_hi_m": 150.0, "climb_soft_lo_m": 8.0, "climb_soft_hi_m": 50.0,
    "parking_search_m": 1200.0, "road_point_step_m": 10.0,
    "regrowth_lo_m": 0.5, "regrowth_hi_m": 8.0, "regrowth_frac": 0.15,
    "cattle_grid_m": 1000.0,
    "sun_date": "2026-09-21", "sun_deadline_local": "08:10", "utc_offset_h": 2.0,
    "mass_radius_m": 25.0,
}

TERMS = {  # name: (reliability, weight, stage)
    "elevation": (0.85, 1.0, "A"), "flat_ground": (0.60, 1.0, "A"), "water_osm": (0.80, 1.0, "A"),
    "water_dtm": (0.40, 1.0, "A"), "cabin": (0.75, 1.0, "A"), "traffic": (0.70, 1.0, "A"),
    "minor_road": (0.30, 1.0, "A"), "railway": (0.70, 1.0, "A"), "path_nearby": (0.40, 1.0, "A"),
    "road_access": (0.70, 1.0, "A"), "landcover": (0.75, 1.0, "A"), "opening": (0.65, 1.0, "A"),
    "mature": (0.60, 1.0, "A"), "sr16": (0.30, 1.0, "A"),
    "direction": (0.60, 1.0, "B"), "walk_time": (0.70, 1.0, "B"), "uphill": (0.60, 1.0, "B"),
    "crossing": (0.60, 1.0, "B"), "logging": (0.35, 1.0, "B"), "road_type": (0.50, 1.0, "B"),
    "cattle_grid": (0.20, 1.0, "B"), "morning_sun": (0.35, 1.0, "B"), "sr16_point": (0.30, 1.0, "B"),
}

WATER_KINDS = ("water", "waterway", "spring")
DRIVABLE = ("road_major", "road_minor", "road_service", "track")
NONFOREST_LANDUSE = {"farmland", "meadow", "residential", "industrial", "commercial", "retail", "quarry", "cemetery",
                     "allotments", "farmyard", "construction", "landfill", "recreation_ground", "grass", "orchard",
                     "garages", "railway", "brownfield", "greenfield", "village_green", "plant_nursery", "religious",
                     "education", "winter_sports"}


# --------------------------------------------------------------------------- small helpers
def band_ll(x, lo, hi, soft_lo, soft_hi=None):
    """0 inside [lo, hi], Gaussian fall-off (scale soft_lo below, soft_hi above)."""
    soft_hi = soft_lo if soft_hi is None else soft_hi
    x = np.asarray(x, float)
    return np.where(x < lo, -0.5 * ((lo - x) / soft_lo) ** 2, np.where(x > hi, -0.5 * ((x - hi) / soft_hi) ** 2, 0.0))


def near_ll(d, radius, soft):
    """Penalty for being closer than `radius` to something: -0.5*((radius-d)/soft)^2."""
    d = np.asarray(d, float)
    return -0.5 * (np.maximum(0.0, radius - d) / soft) ** 2


def robust(ll, name, weights=None):
    r, w, _ = TERMS[name]
    w = (weights or {}).get(name, w)
    with np.errstate(over="ignore", under="ignore"):
        return w * np.log(r * np.exp(np.minimum(ll, 0.0)) + (1.0 - r))


def elevation_ll(z, p=PARAMS):
    z = np.asarray(z, float)
    wmax = max(w for _, w in p["elev_centres"])
    mix = sum(w * np.exp(-0.5 * ((z - c) / p["elev_sigma_m"]) ** 2) for c, w in p["elev_centres"])
    return np.maximum(np.log(mix / wmax + 1e-12), -12.0)


def direction_ll(brg_box_to_car_true, p=PARAMS):
    """Mixture of the two approach hypotheses; 0 when the preferred one fits exactly."""
    old_axis = (p["sign_magnetic_deg"] + p["declination_deg"] + 180.0) % 360.0

    def g(delta):
        return np.where(delta <= p["dir_tol_deg"], 1.0, np.exp(-0.5 * ((delta - p["dir_tol_deg"]) / p["dir_soft_deg"]) ** 2))
    f = p["dir_new_w"] * g(angdiff(brg_box_to_car_true, p["dir_new_deg"])) + p["dir_old_w"] * g(angdiff(brg_box_to_car_true, old_axis))
    return np.log(np.maximum(f, 1e-4) / max(p["dir_new_w"], p["dir_old_w"]))


def tobler_kmh(slope, factor=1.0):
    return 6.0 * np.exp(-3.5 * np.abs(np.asarray(slope) + 0.05)) * factor


def _fill_nan_1d(z):
    z = np.array(z, float)
    ok = np.isfinite(z)
    if ok.all() or not ok.any():
        return z if ok.any() else np.zeros_like(z)
    idx = np.arange(len(z))
    return np.interp(idx, idx[ok], z[ok])


# --------------------------------------------------------------------------- sun
def sun_position(lat, lon, when_utc):
    """NOAA solar position: (azimuth deg true, apparent elevation deg). ~0.1 deg accuracy."""
    jd = when_utc.timestamp() / 86400.0 + 2440587.5
    jc = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360
    M = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    Mr = np.radians(M)
    C = np.sin(Mr) * (1.914602 - jc * (0.004817 + 0.000014 * jc)) + np.sin(2 * Mr) * (0.019993 - 0.000101 * jc) \
        + np.sin(3 * Mr) * 0.000289
    app = L0 + C - 0.00569 - 0.00478 * np.sin(np.radians(125.04 - 1934.136 * jc))
    obl = 23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60) / 60
    oblc = obl + 0.00256 * np.cos(np.radians(125.04 - 1934.136 * jc))
    decl = np.degrees(np.arcsin(np.sin(np.radians(oblc)) * np.sin(np.radians(app))))
    y = np.tan(np.radians(oblc / 2)) ** 2
    L0r = np.radians(L0)
    eqt = 4 * np.degrees(y * np.sin(2 * L0r) - 2 * e * np.sin(Mr) + 4 * e * y * np.sin(Mr) * np.cos(2 * L0r)
                         - 0.5 * y * y * np.sin(4 * L0r) - 1.25 * e * e * np.sin(2 * Mr))
    minutes = when_utc.hour * 60 + when_utc.minute + when_utc.second / 60
    tst = (minutes + eqt + 4 * lon) % 1440
    ha = tst / 4 - 180
    la, de, har = np.radians(lat), np.radians(decl), np.radians(ha)
    cz = np.clip(np.sin(la) * np.sin(de) + np.cos(la) * np.cos(de) * np.cos(har), -1, 1)
    elev = 90 - np.degrees(np.arccos(cz))
    az = (np.degrees(np.arctan2(np.sin(har), np.cos(har) * np.sin(la) - np.tan(de) * np.cos(la))) + 180) % 360
    if elev > -0.575:  # refraction (Saemundsson-like, degrees)
        elev = elev + 1.02 / np.tan(np.radians(elev + 10.3 / (elev + 5.11))) / 60
    return float(az), float(elev)


def horizon_elevation(rasters, x, y, z_eye, az_true, min_d=30.0, max_d=None, step=None):
    """Max terrain elevation angle (deg) along a ray; rasters are tried in order per sample.

    Returns (angle, distance of the max, covered distance)."""
    gamma = float(convergence_deg(x, y))
    azg = np.radians(az_true - gamma)
    if max_d is None:
        max_d = 0.0
        for r in rasters:
            xmin, ymin, xmax, ymax = r.bounds
            max_d = max(max_d, np.hypot(max(xmax - x, x - xmin), max(ymax - y, y - ymin)))
    step = step or max(2.0, min(r.res[0] for r in rasters))
    d = np.arange(min_d, max_d, step)
    xs, ys = x + d * np.sin(azg), y + d * np.cos(azg)
    z = np.full(d.shape, np.nan)
    for r in rasters:
        need = np.isnan(z)
        if need.any():
            z[need] = r.sample(xs[need], ys[need])
    ok = np.isfinite(z)
    if not ok.any():
        return np.nan, np.nan, 0.0
    drop = d ** 2 / (2 * 6371000.0) * (1 - 0.13)
    ang = np.degrees(np.arctan2(z - z_eye - drop, d))
    ang[~ok] = -90
    k = int(np.argmax(ang))
    return float(ang[k]), float(d[k]), float(d[ok].max())


def terrain_sunrise(rasters, x, y, z_eye, date="2026-09-21", utc_offset_h=2.0, start="06:30", end="10:30", step_min=5):
    """First local time the sun is above the terrain horizon (trees ignored)."""
    lat, lon = to_wgs84(x, y)
    lat, lon = float(lat), float(lon)
    h0, m0 = map(int, start.split(":"))
    h1, m1 = map(int, end.split(":"))
    base = datetime.fromisoformat(date).replace(tzinfo=timezone.utc) - timedelta(hours=utc_offset_h)
    t = base + timedelta(hours=h0, minutes=m0)
    tend = base + timedelta(hours=h1, minutes=m1)
    last = None
    while t <= tend:
        az, el = sun_position(lat, lon, t)
        if el > -1.0:
            hz, _, cov = horizon_elevation(rasters, x, y, z_eye, az)
            last = (az, el, hz, cov)
            if np.isfinite(hz) and el > hz:
                return (t + timedelta(hours=utc_offset_h)).strftime("%H:%M"), az, el, hz, cov
        t += timedelta(minutes=step_min)
    return None, *(last or (np.nan, np.nan, np.nan, 0.0))


# --------------------------------------------------------------------------- features
class Features:
    """OSM GeoJSON-like FeatureCollection (WGS84) converted to EPSG:25833 geometry by kind."""

    def __init__(self, fc=None):
        from .fetch import osm_kind
        self.lines, self.polys, self.points = {}, {}, {}
        self.areas = []          # (props, polygon) for landuse/natural polygons
        self.roads = []          # dict(xy, kind, props)
        for f in (fc or {}).get("features", []):
            g, props = f.get("geometry"), f.get("properties", {}) or {}
            if not g:
                continue
            kind = props.get("kind") or osm_kind(props)
            t, cs = g["type"], g["coordinates"]
            if t == "Point":
                x, y = to_utm(cs[1], cs[0])
                self.points.setdefault(kind, []).append((float(x), float(y)))
            elif t in ("LineString", "MultiLineString"):
                for part in ([cs] if t == "LineString" else cs):
                    xy = self._xy(part)
                    if len(xy) >= 2:
                        self.lines.setdefault(kind, []).append(xy)
                        if kind in DRIVABLE:
                            self.roads.append({"xy": xy, "kind": kind, "props": props})
            elif t in ("Polygon", "MultiPolygon"):
                for poly in ([cs] if t == "Polygon" else cs):
                    rings = [self._xy(r) for r in poly]
                    if len(rings[0]) < 4:
                        continue
                    P = Polygon(rings[0], rings[1:]).buffer(0)
                    if P.is_empty:
                        continue
                    self.polys.setdefault(kind, []).append(P)
                    self.lines.setdefault(kind, []).append(rings[0])  # outline counts for distances
                    if kind in ("landuse", "landcover", "wetland", "water"):
                        self.areas.append((props, P))
        self._water_tree = None

    @staticmethod
    def _xy(coords):
        a = np.asarray(coords, float)
        x, y = to_utm(a[:, 1], a[:, 0])
        return np.column_stack([x, y])

    def has(self, *kinds):
        return any(self.lines.get(k) or self.polys.get(k) or self.points.get(k) for k in kinds)

    def road_points(self, step=10.0):
        """Densified drivable-road points: (xy array, list of per-point road dicts)."""
        pts, meta = [], []
        for r in self.roads:
            xy = r["xy"]
            seg = np.hypot(*np.diff(xy, axis=0).T)
            s = np.concatenate([[0], np.cumsum(seg)])
            if s[-1] <= 0:
                continue
            u = np.arange(0, s[-1] + 1e-9, step)
            px = np.interp(u, s, xy[:, 0])
            py = np.interp(u, s, xy[:, 1])
            pts.append(np.column_stack([px, py]))
            meta += [r] * len(u)
        if not pts:
            return np.zeros((0, 2)), []
        return np.vstack(pts), meta

    def obstacle_tree(self):
        """STRtree over water geometries for walk-line crossing tests."""
        if self._water_tree is None:
            geoms, kinds = [], []
            for k in ("waterway", "ditch"):
                for xy in self.lines.get(k, []):
                    geoms.append(LineString(xy))
                    kinds.append(k)
            for P in self.polys.get("water", []):
                geoms.append(P)
                kinds.append("water")
            self._water_tree = (STRtree(geoms) if geoms else None, geoms, kinds)
        return self._water_tree


def _feature_grid(bounds, res, pad):
    xmin, ymin, xmax, ymax = bounds
    xmin, ymin, xmax, ymax = xmin - pad, ymin - pad, xmax + pad, ymax + pad
    W, H = int(np.ceil((xmax - xmin) / res)), int(np.ceil((ymax - ymin) / res))
    return Raster(np.zeros((H, W), np.float32), make_transform(xmin, ymin + H * res, res))


def rasterize(grid, feats, kinds, fill_polys=True):
    """Boolean mask on `grid` of lines/points/polygons of the given kinds."""
    m = np.zeros(grid.shape, bool)
    res = grid.res[0]
    H, W = grid.shape

    def mark(x, y):
        r, c = grid.rowcol(x, y)
        r, c = np.rint(r).astype(int), np.rint(c).astype(int)
        ok = (r >= 0) & (r < H) & (c >= 0) & (c < W)
        m[r[ok], c[ok]] = True
    for k in kinds:
        for xy in feats.lines.get(k, []):
            seg = np.hypot(*np.diff(xy, axis=0).T)
            s = np.concatenate([[0], np.cumsum(seg)])
            u = np.arange(0, s[-1] + 1e-9, res / 2)
            mark(np.interp(u, s, xy[:, 0]), np.interp(u, s, xy[:, 1]))
        if feats.points.get(k):
            p = np.asarray(feats.points[k])
            mark(p[:, 0], p[:, 1])
        if fill_polys:
            for P in feats.polys.get(k, []):
                _fill_poly(grid, m, P)
    return m


def _fill_poly(grid, m, P, value=True, out=None):
    xmin, ymin, xmax, ymax = P.bounds
    r0, c0 = grid.rowcol(xmin, ymax)
    r1, c1 = grid.rowcol(xmax, ymin)
    H, W = grid.shape
    r0, r1 = max(int(np.floor(r0)), 0), min(int(np.ceil(r1)) + 1, H)
    c0, c1 = max(int(np.floor(c0)), 0), min(int(np.ceil(c1)) + 1, W)
    if r1 <= r0 or c1 <= c0:
        return
    rr, cc = np.meshgrid(np.arange(r0, r1), np.arange(c0, c1), indexing="ij")
    X, Y = grid.xy(rr, cc)
    prepare(P)
    inside = contains_xy(P, X, Y)
    tgt = m if out is None else out
    sub = tgt[r0:r1, c0:c1]
    sub[inside] = value


def distance_to(grid, feats, kinds):
    """Distance (m) raster on `grid` to the nearest feature of `kinds` (inf when none)."""
    m = rasterize(grid, feats, kinds)
    if not m.any():
        return Raster(np.full(grid.shape, np.inf, np.float32), grid.transform)
    return Raster(distance_transform_edt(~m, sampling=grid.res[0]).astype(np.float32), grid.transform)


def landcover_ll(grid, feats):
    ll = np.zeros(grid.shape, np.float32)
    for props, P in feats.areas:
        lu, nat = props.get("landuse"), props.get("natural")
        if lu == "military" or props.get("military"):
            v = -4.0
        elif lu in NONFOREST_LANDUSE:
            v = -3.0
        elif nat == "wetland":
            v = -0.8 if props.get("wetland") in ("swamp", "wet_meadow") else -1.5
        elif nat == "bare_rock":
            v = -1.0
        else:
            continue
        tmp = np.zeros(grid.shape, bool)
        _fill_poly(grid, None, P, True, out=tmp)
        ll = np.minimum(ll, np.where(tmp, v, 0.0))
    return ll


# --------------------------------------------------------------------------- DTM derived
def slope_deg(dtm, smooth_m=3.0):
    z = np.asarray(dtm.data, float)
    if np.isnan(z).any():
        z = np.where(np.isnan(z), np.nanmean(z), z)
    res = dtm.res[0]
    if smooth_m / res >= 0.5:
        z = gaussian_filter(z, smooth_m / res)
    gy, gx = np.gradient(z, res)
    return np.degrees(np.arctan(np.hypot(gx, gy)))


def dtm_streams(dtm, res=10.0, min_area_m2=2.0e5):
    """D8 flow accumulation -> boolean stream mask Raster (catchment >= min_area_m2)."""
    d = dtm if dtm.res[0] >= res else dtm.resample(res)
    z = np.asarray(d.data, float)
    if np.isnan(z).any():
        z = np.where(np.isnan(z), np.nanmax(z), z)
    H, W = z.shape
    r = d.res[0]
    zp = np.pad(z, 1, constant_values=np.inf)
    idx = np.arange(H * W).reshape(H, W)
    best = np.zeros((H, W))
    rcv = np.full((H, W), -1)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            zn = zp[1 + di:1 + di + H, 1 + dj:1 + dj + W]
            drop = (z - zn) / (np.hypot(di, dj) * r)
            better = drop > best
            best = np.where(better, drop, best)
            rcv = np.where(better, idx + di * W + dj, rcv)
    acc = np.ones(H * W)
    rv = rcv.ravel()
    for i in np.argsort(z.ravel(), kind="stable")[::-1]:
        j = rv[i]
        if j >= 0:
            acc[j] += acc[i]
    area = acc.reshape(H, W) * r * r
    return Raster((area >= min_area_m2).astype(np.float32), d.transform, source="d8-streams",
                  meta={"max_area_m2": float(area.max())})


def canopy_terms(chm, p=PARAMS):
    """(opening canopy height, ring mean canopy height, ring closed-canopy fraction) on the chm grid.

    open_h: mean canopy within ~opening_radius_m of the pixel (box-filter);
    ring:   mean canopy in the ring_inner..ring_outer square annulus;
    closed: fraction of that annulus with canopy >= 10 m (separates a small
            opening in mature forest from the edge of a clear-cut)."""
    res = chm.res[0]
    c = np.where(np.isnan(chm.data), 0.0, chm.data).astype(float)
    k0 = max(1, int(2 * p["opening_radius_m"] / res) | 1)
    k1 = max(3, int(round(2 * p["ring_inner_m"] / res)) | 1)
    k2 = max(k1 + 2, int(round(2 * p["ring_outer_m"] / res)) | 1)
    open_h = uniform_filter(c, k0, mode="nearest")

    def ring_mean(a):
        m1, m2 = uniform_filter(a, k1, mode="nearest"), uniform_filter(a, k2, mode="nearest")
        return (m2 * k2 * k2 - m1 * k1 * k1) / (k2 * k2 - k1 * k1)
    return open_h, ring_mean(c), ring_mean((c >= 10.0).astype(float))


# --------------------------------------------------------------------------- stage A
@dataclass
class TileScore:
    grid: Raster                 # work-grid DTM
    total: np.ndarray            # Stage A robust total (-inf where no DTM)
    terms: dict                  # name -> raw ll array
    contrib: dict                # name -> robust contribution array
    dist: dict                   # name -> distance array (m) on work grid
    extra: dict                  # slope, open_h, ring, ...
    missing: list
    feats: Features
    chm: Raster = None
    sr16: dict = None
    candidates: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)


def stage_a(dtm, chm=None, feats=None, sr16=None, p=PARAMS, weights=None, work_res=2.0, feat_res=None, pad=800.0):
    """Per-pixel Stage A terms on a work grid (DTM resampled to work_res if finer)."""
    grid = dtm if dtm.res[0] >= work_res - 1e-9 else dtm.resample(work_res)
    if chm is not None and chm.shape != grid.shape:
        chm = chm.resample(grid.res[0]) if chm.res[0] < grid.res[0] - 1e-9 else chm
        chm = chm.like(grid)
    feats = feats if isinstance(feats, Features) else Features(feats)
    z = np.asarray(grid.data, float)
    valid = np.isfinite(z)
    X, Y = grid.centres()
    terms, dist, extra, missing = {}, {}, {}, []

    terms["elevation"] = elevation_ll(np.where(valid, z, -999), p)
    sl = slope_deg(grid)
    extra["slope"] = sl
    terms["flat_ground"] = band_ll(sl, 0, p["slope_ok_deg"], p["slope_soft_deg"])

    fres = feat_res or max(grid.res[0], 4.0)
    fg = _feature_grid(grid.bounds, fres, pad)

    def dist_on_grid(kinds):
        d = distance_to(fg, feats, kinds)
        return d.sample(X, Y, order=1, fill=np.inf) if np.isfinite(d.data).any() else np.full(z.shape, np.inf)

    osm_ok = bool(feats.lines or feats.polys or feats.points)
    if not osm_ok:
        missing.append("osm")
    groups = {"water_osm": WATER_KINDS, "cabin": ("building",), "traffic": ("road_major",), "minor_road": ("road_minor",),
              "railway": ("railway",), "path_nearby": ("path",), "road_access": DRIVABLE}
    for name, kinds in groups.items():
        if osm_ok:
            dist[name] = dist_on_grid(kinds)
    if osm_ok:
        terms["water_osm"] = near_ll(dist["water_osm"], p["water_radius_m"], p["water_soft_m"])
        terms["cabin"] = near_ll(dist["cabin"], p["cabin_radius_m"], p["cabin_soft_m"])
        terms["traffic"] = near_ll(dist["traffic"], p["traffic_radius_m"], p["traffic_soft_m"])
        terms["minor_road"] = near_ll(dist["minor_road"], p["minor_radius_m"], p["minor_soft_m"])
        terms["railway"] = near_ll(dist["railway"], p["rail_radius_m"], p["rail_soft_m"])
        terms["path_nearby"] = near_ll(dist["path_nearby"], p["path_radius_m"], p["path_soft_m"])
        if feats.roads:
            terms["road_access"] = band_ll(dist["road_access"], p["road_lo_m"], p["road_hi_m"], p["road_soft_lo_m"],
                                           p["road_soft_hi_m"])
        else:
            missing.append("roads")
        lc = landcover_ll(fg, feats)
        terms["landcover"] = Raster(lc, fg.transform).sample(X, Y, order=0, fill=0.0)

    try:
        st = dtm_streams(dtm, p["dtm_stream_res_m"], p["dtm_stream_min_area_m2"])
        if st.data.any():
            dst = Raster(distance_transform_edt(st.data < 0.5, sampling=st.res[0]).astype(np.float32), st.transform)
            dist["water_dtm"] = dst.sample(X, Y, order=1, fill=np.inf)
        else:
            dist["water_dtm"] = np.full(z.shape, np.inf)
        terms["water_dtm"] = near_ll(dist["water_dtm"], p["dtm_stream_radius_m"], p["dtm_stream_soft_m"])
    except Exception as exc:  # noqa: BLE001 - optional
        missing.append(f"water_dtm ({exc})")

    if chm is not None:
        oh, ring, closed = canopy_terms(chm, p)
        extra["open_h"], extra["ring"], extra["closed"] = oh, ring, closed
        terms["opening"] = band_ll(oh, 0.0, p["opening_max_m"], p["opening_soft_m"])
        terms["mature"] = (band_ll(ring, p["ring_lo_m"], p["ring_hi_m"], p["ring_soft_m"])
                           + band_ll(closed, p["ring_closed_frac"], 1.0, p["ring_closed_soft"]))
    else:
        missing.append("dom")

    if sr16 and sr16.get("rasters"):
        ll = np.zeros(z.shape)
        sp = sr16["rasters"].get("species")
        if sp is not None:
            from .fetch import sr16_species_name
            v = sp.sample(X, Y, order=0)
            names = np.vectorize(lambda a: sr16_species_name(a) or "none", otypes=[object])(v)
            ll += np.select([names == "pine", names == "deciduous", names == "spruce"], [0.0, -0.15, -0.5], -1.0)
        hg = sr16["rasters"].get("height")
        if hg is not None:
            ll += band_ll(hg.sample(X, Y, order=1), 12.0, 24.0, 5.0)
        terms["sr16"] = ll

    contrib = {k: robust(v, k, weights) for k, v in terms.items()}
    total = sum(contrib.values())
    total = np.where(valid, total, -np.inf)
    return TileScore(grid, total, terms, contrib, dist, extra, missing, feats, chm, sr16)


def nms(score, n, min_sep_px):
    """Greedy non-maximum suppression on a 2-D score -> list of (row, col)."""
    order = np.argsort(np.where(np.isfinite(score), score, -np.inf), axis=None)[::-1]
    sup = np.zeros(score.shape, bool)
    H, W = score.shape
    rr = int(np.ceil(min_sep_px))
    yy, xx = np.mgrid[-rr:rr + 1, -rr:rr + 1]
    disc = (yy ** 2 + xx ** 2) <= min_sep_px ** 2
    picks = []
    for k in order:
        i, j = divmod(int(k), W)
        if not np.isfinite(score[i, j]):
            break
        if sup[i, j]:
            continue
        picks.append((i, j))
        if len(picks) >= n:
            break
        i0, i1, j0, j1 = max(i - rr, 0), min(i + rr + 1, H), max(j - rr, 0), min(j + rr + 1, W)
        sup[i0:i1, j0:j1] |= disc[i0 - i + rr:i1 - i + rr, j0 - j + rr:j1 - j + rr]
    return picks


# --------------------------------------------------------------------------- stage B
def walk_profile(dtm, x_car, y_car, x_box, y_box, step=2.0, offtrail=0.6):
    L = float(np.hypot(x_box - x_car, y_box - y_car))
    n = max(2, int(np.ceil(L / step)) + 1)
    xs, ys = np.linspace(x_car, x_box, n), np.linspace(y_car, y_box, n)
    z = _fill_nan_1d(dtm.sample(xs, ys))
    dx = L / (n - 1) if n > 1 else 0.0
    dz = np.diff(z)
    s = dz / dx if dx > 0 else np.zeros_like(dz)
    t_h = np.sum((dx / 1000.0) / tobler_kmh(s, offtrail)) if dx > 0 else 0.0
    k = max(1, int(round(10.0 / max(dx, 1e-9)))) if dx > 0 else 1
    s10 = (z[k:] - z[:-k]) / (k * dx) if dx > 0 and len(z) > k else np.array([0.0])
    return {"length_m": L, "time_min": float(t_h * 60), "ascent_m": float(dz[dz > 0].sum()),
            "descent_m": float(-dz[dz < 0].sum()), "max_slope_deg": float(np.degrees(np.arctan(np.abs(s10).max()))) if len(s10) else 0.0,
            "xs": xs, "ys": ys}


def road_type_ll(props, kind):
    hw, tt = props.get("highway"), props.get("tracktype")
    if kind == "road_major":
        v = -1.0
    elif kind == "road_minor":
        v = -0.2 if hw != "residential" else -0.4
    elif kind == "track" and tt in ("grade4", "grade5"):
        v = -0.7
    else:
        v = 0.0
    if props.get("motor_vehicle") in ("no",) or props.get("access") in ("no",):
        v -= 0.2
    return v


def stage_b(ts, cand_rc, p=PARAMS, weights=None, horizon_rasters=None, sun=True):
    """Evaluate candidates (list of (row, col) on ts.grid) -> list of candidate dicts."""
    grid, feats = ts.grid, ts.feats
    road_xy, road_meta = feats.road_points(p["road_point_step_m"])
    tree = cKDTree(road_xy) if len(road_xy) else None
    road_z = grid.sample(road_xy[:, 0], road_xy[:, 1]) if len(road_xy) else np.zeros(0)
    wt, wgeoms, wkinds = feats.obstacle_tree()
    cattle = np.asarray(feats.points.get("cattle_grid", []), float).reshape(-1, 2)
    chm = ts.chm
    rasters = [grid] + list(horizon_rasters or [])
    out = []
    for (i, j) in cand_rc:
        x, y = (float(v) for v in grid.xy(i, j))
        zb = float(grid.data[i, j])
        c = {"row": int(i), "col": int(j), "x": x, "y": y, "z": zb, "terms_b": {}, "info": {}}
        terms = c["terms_b"]
        info = c["info"]
        best = None
        if tree is not None:
            dmin, kmin = tree.query([x, y])
            info["road_dist_m"] = float(dmin)
            info["nearest_road"] = _road_label(road_meta[kmin])
            idx = tree.query_ball_point([x, y], p["parking_search_m"])
            if idx:
                idx = np.asarray(idx)
                P = road_xy[idx]
                d = np.hypot(P[:, 0] - x, P[:, 1] - y)
                brg = true_bearing_xy(x, y, P[:, 0], P[:, 1])  # box -> car
                zc = road_z[idx]
                climb = np.where(np.isfinite(zc), zb - zc, np.nan)
                t_flat = d / 1000.0 / tobler_kmh(np.nan_to_num((zb - np.nan_to_num(zc, nan=zb)) / np.maximum(d, 1)),
                                                  p["offtrail_factor"]) * 60
                cheap = (robust(direction_ll(brg, p), "direction", weights)
                         + robust(band_ll(t_flat, p["walk_lo_min"], p["walk_hi_min"], p["walk_soft_min"]), "walk_time", weights)
                         + robust(np.where(np.isfinite(climb), band_ll(climb, p["climb_lo_m"], p["climb_hi_m"],
                                                                       p["climb_soft_lo_m"], p["climb_soft_hi_m"]), 0.0), "uphill", weights)
                         + np.array([robust(road_type_ll(road_meta[k]["props"], road_meta[k]["kind"]), "road_type", weights)
                                     for k in idx]))
                for q in np.argsort(cheap)[::-1][:12]:
                    k = int(idx[q])
                    res = _eval_parking(grid, chm, x, y, zb, road_xy[k], road_z[k], road_meta[k], wt, wgeoms, wkinds, cattle,
                                        p, weights)
                    if best is None or res["score"] > best["score"]:
                        best = res
        if best is None:
            dmin = info.get("road_dist_m", np.inf)
            terms["walk_time"] = float(band_ll(dmin / 50.0, p["walk_lo_min"], p["walk_hi_min"], p["walk_soft_min"])) if np.isfinite(dmin) else -8.0
            terms["direction"] = float(np.log(0.5))
            info["parking"] = None
        else:
            terms.update(best["terms"])
            info.update(best["info"])
        if sun:
            t_sr, az, el, hz, cov = terrain_sunrise(rasters, x, y, zb + 1.5, p["sun_date"], p["utc_offset_h"])
            info.update({"terrain_sunrise_local": t_sr, "sun_az_deg": az, "sun_el_deg": el, "horizon_deg": hz,
                         "horizon_covered_m": cov})
            dl_h, dl_m = map(int, p["sun_deadline_local"].split(":"))
            if t_sr is None:
                terms["morning_sun"] = -4.0
            else:
                hh, mm = map(int, t_sr.split(":"))
                late = (hh * 60 + mm) - (dl_h * 60 + dl_m)
                terms["morning_sun"] = float(-0.5 * (max(0, late) / 15.0) ** 2)
        if ts.sr16 and ts.sr16.get("points"):
            rec = min(ts.sr16["points"], key=lambda r: np.hypot(r["x"] - x, r["y"] - y))
            if np.hypot(rec["x"] - x, rec["y"] - y) < 30:
                terms["sr16_point"], sp = sr16_point_ll(rec)
                info["sr16_species"], info["sr16_height"] = sp, rec.get("height")
        c["contrib_b"] = {k: float(robust(v, k, weights)) for k, v in terms.items()}
        c["score_b"] = float(sum(c["contrib_b"].values()))
        out.append(c)
    return out


def sr16_point_ll(rec):
    """(ll, species name) for one SR16 GetFeatureInfo sample {'species', 'species_label', 'height'}.

    Scene: ~40 % pine, 35 % birch, 25 % spruce -> a 16 m SR16 pixel is most likely
    pine-dominated, then deciduous, then spruce; non-forest is penalised."""
    from .fetch import sr16_species_name
    sp = sr16_species_name(rec.get("species"), rec.get("species_label"))
    if sp is None:
        v = -1.0 if rec.get("species") is not None else 0.0
    else:
        v = {"pine": 0.0, "deciduous": -0.15, "spruce": -0.5}[sp]
    if rec.get("height") is not None and np.isfinite(rec["height"]):
        v += float(band_ll(rec["height"], 12.0, 24.0, 5.0))
    return v, sp


def apply_point_term(cands, name, values, weights=None):
    """Add a late Stage-B term (e.g. SR16 samples fetched for the top candidates) and
    update score / p_in_tile consistently. values: list aligned with cands (None = no data)."""
    old_total = sum(c.get("p_in_tile") or 0.0 for c in cands)
    for c, v in zip(cands, values):
        if v is None:
            continue
        c["terms_b"][name] = float(v)
        new = float(robust(v, name, weights))
        delta = new - c.get("contrib_b", {}).get(name, 0.0)
        c["contrib_b"][name] = new
        c["score_b"] += delta
        c["score"] += delta
        if c.get("p_in_tile") is not None:
            c["p_in_tile"] *= float(np.exp(delta))
    new_total = sum(c.get("p_in_tile") or 0.0 for c in cands)
    if new_total > 0 and old_total > 0:
        for c in cands:
            if c.get("p_in_tile") is not None:
                c["p_in_tile"] *= old_total / new_total
    cands.sort(key=lambda c: c["score"], reverse=True)
    return cands


def _road_label(meta):
    pr = meta["props"]
    s = pr.get("highway", meta["kind"])
    if pr.get("tracktype"):
        s += f"/{pr['tracktype']}"
    if pr.get("name") or pr.get("ref"):
        s += f" '{pr.get('name') or pr.get('ref')}'"
    return s


def _eval_parking(grid, chm, x, y, zb, pxy, pz, meta, wt, wgeoms, wkinds, cattle, p, weights):
    prof = walk_profile(grid, pxy[0], pxy[1], x, y, step=max(grid.res[0], 2.0), offtrail=p["offtrail_factor"])
    brg = float(true_bearing_xy(x, y, pxy[0], pxy[1]))
    climb = zb - pz if np.isfinite(pz) else np.nan
    terms = {"direction": float(direction_ll(brg, p)),
             "walk_time": float(band_ll(prof["time_min"], p["walk_lo_min"], p["walk_hi_min"], p["walk_soft_min"])),
             "uphill": float(band_ll(climb, p["climb_lo_m"], p["climb_hi_m"], p["climb_soft_lo_m"], p["climb_soft_hi_m"]))
             if np.isfinite(climb) else 0.0,
             "road_type": road_type_ll(meta["props"], meta["kind"])}
    cross = []
    if wt is not None:
        line = LineString([(pxy[0], pxy[1]), (x, y)])
        for gi in wt.query(line):
            if wgeoms[gi].intersects(line):
                cross.append(wkinds[gi])
    ll_cross = 0.0
    if "water" in cross:
        ll_cross -= 4.0
    if "waterway" in cross:
        ll_cross -= 3.0
    if "ditch" in cross:
        ll_cross -= 0.5
    if prof["max_slope_deg"] > 30:
        ll_cross -= 2.0
    terms["crossing"] = ll_cross
    regrowth = None
    if chm is not None:
        h = chm.sample(prof["xs"], prof["ys"])
        h = h[np.isfinite(h)]
        if len(h):
            regrowth = float(np.mean((h >= p["regrowth_lo_m"]) & (h <= p["regrowth_hi_m"])))
            terms["logging"] = float(-0.5 * (max(0.0, p["regrowth_frac"] - regrowth) / 0.08) ** 2)
    cg = None
    if len(cattle):
        cg = float(np.min(np.hypot(cattle[:, 0] - pxy[0], cattle[:, 1] - pxy[1])))
        terms["cattle_grid"] = -1.0 if cg < p["cattle_grid_m"] else 0.0
    # the cattle-grid clue concerns the (unknown) drive route: it is reported, not used to pick the spot
    score = sum(float(robust(v, k, weights)) for k, v in terms.items() if k != "cattle_grid")
    gamma = float(convergence_deg(x, y))
    brg_cb = (brg + 180.0) % 360.0
    info = {"parking": {"x": float(pxy[0]), "y": float(pxy[1]), "z": float(pz) if np.isfinite(pz) else None,
                        "road": _road_label(meta), "osm_id": meta["props"].get("osm_id")},
            "walk_m": prof["length_m"], "walk_min": prof["time_min"], "climb_m": float(climb) if np.isfinite(climb) else None,
            "ascent_m": prof["ascent_m"], "descent_m": prof["descent_m"], "max_slope_deg": prof["max_slope_deg"],
            "bearing_box_to_car": brg, "bearing_car_to_box": brg_cb,
            "bearing_car_to_box_magnetic": (brg_cb - p["declination_deg"]) % 360.0, "grid_convergence_deg": gamma,
            "crossings": sorted(set(cross)), "regrowth_frac": regrowth, "cattle_grid_m": cg,
            "direction_hypothesis": ("SE (whiteboard)" if angdiff(brg, p["dir_new_deg"]) <= p["dir_tol_deg"] else
                                     "WNW (old sign)" if angdiff(brg, (p["sign_magnetic_deg"] + p["declination_deg"] + 180) % 360)
                                     <= p["dir_tol_deg"] else "neither")}
    return {"score": score, "terms": terms, "info": info}


# --------------------------------------------------------------------------- driver
def score_tile(dtm, dom=None, osm=None, sr16=None, p=None, weights=None, work_res=2.0, n_out=10, n_pool=150,
               min_sep_m=40.0, horizon_rasters=None, sun=True, chm=None):
    """Score one tile and return (TileScore, candidates sorted by final score).

    dtm/dom: Raster in EPSG:25833; osm: GeoJSON-like dict (WGS84) or Features;
    sr16: dict from fetch.sr16 (rasters and/or point samples)."""
    p = {**PARAMS, **(p or {})}
    if chm is None and dom is not None:
        from .fetch import canopy_height
        chm = canopy_height(dtm, dom)
    ts = stage_a(dtm, chm, osm, sr16, p, weights, work_res)
    res = ts.grid.res[0]
    picks = nms(ts.total, n_pool, max(1.0, min_sep_m / res))
    cands = stage_b(ts, picks, p, weights, horizon_rasters, sun)
    # Stage-A posterior mass of the search disc (radius mass_radius_m) around each candidate;
    # pixels are assigned to their nearest candidate (Voronoi) so discs never double count.
    lp = np.where(np.isfinite(ts.total), ts.total - np.nanmax(ts.total[np.isfinite(ts.total)]), -np.inf)
    px = np.exp(lp)
    px /= px.sum()
    mass = np.zeros(len(cands))
    if cands:
        seed = np.zeros(px.shape, bool)
        lab = np.full(px.shape, -1, int)
        for n, c in enumerate(cands):
            seed[c["row"], c["col"]] = True
            lab[c["row"], c["col"]] = n
        dd, (ii, jj) = distance_transform_edt(~seed, sampling=res, return_indices=True)
        owner = lab[ii, jj]
        inside = dd <= p["mass_radius_m"]
        mass = np.bincount(owner[inside], weights=px[inside], minlength=len(cands))
    for n, c in enumerate(cands):
        i, j = c["row"], c["col"]
        c["mass_a"] = float(mass[n])
        c["terms_a"] = {k: float(v[i, j]) for k, v in ts.terms.items()}
        c["contrib_a"] = {k: float(v[i, j]) for k, v in ts.contrib.items()}
        c["score_a"] = float(ts.total[i, j])
        road_a = c["contrib_a"].get("road_access", 0.0)
        c["score"] = c["score_a"] - road_a + c["score_b"]
        c["adj"] = c["score_b"] - road_a
        c["info"].update({k: float(v[i, j]) for k, v in ts.dist.items()})
        for k in ("slope", "open_h", "ring", "closed"):
            if k in ts.extra:
                c["info"][k] = float(ts.extra[k][i, j])
    if cands:
        m = max(c["adj"] for c in cands)
        w = np.array([c["mass_a"] * np.exp(c["adj"] - m) for c in cands])
        resid = max(0.0, 1.0 - sum(c["mass_a"] for c in cands)) * float(np.mean([np.exp(c["adj"] - m) for c in cands]))
        tot = w.sum() + resid
        for c, wi in zip(cands, w):
            c["p_in_tile"] = float(wi / tot) if tot > 0 else 0.0
    cands.sort(key=lambda c: c["score"], reverse=True)
    ts.candidates = cands
    ts.meta = {"work_res_m": res, "n_pool": len(picks), "missing": ts.missing, "params": p}
    for c in cands:
        c["reasons"] = reasons(c, ts.missing, p)
    return ts, cands[:n_out]


def _flag(v):
    return "ok" if v > -0.3 else ("weak" if v > -1.5 else "BAD")


def reasons(c, missing, p=PARAMS):
    """Human-readable justification per term."""
    ta, tb, inf = c["terms_a"], c["terms_b"], c["info"]
    target = min((cc for cc, _ in p["elev_centres"]), key=lambda cc: abs(cc - c["z"]))
    out = [f"[{_flag(ta['elevation'])}] elevation {c['z']:.0f} m (target {target:.0f}, {c['z'] - target:+.0f} m)",
           f"[{_flag(ta['flat_ground'])}] slope {inf.get('slope', float('nan')):.0f} deg"]
    if "water_osm" in ta:
        out.append(f"[{_flag(ta['water_osm'])}] nearest OSM water {_m(inf.get('water_osm'))}")
    if "water_dtm" in ta:
        out.append(f"[{_flag(ta['water_dtm'])}] nearest DTM-derived stream {_m(inf.get('water_dtm'))}")
    if "cabin" in ta:
        out.append(f"[{_flag(ta['cabin'])}] nearest building {_m(inf.get('cabin'))}")
    if "traffic" in ta:
        out.append(f"[{_flag(ta['traffic'])}] trafficked road (tertiary+) {_m(inf.get('traffic'))}; "
                   f"railway {_m(inf.get('railway'))}; path {_m(inf.get('path_nearby'))}")
    if "landcover" in ta and ta["landcover"] < 0:
        out.append(f"[{_flag(ta['landcover'])}] OSM landcover not forest (ll {ta['landcover']:.1f})")
    if "opening" in ta:
        out.append(f"[{_flag(ta['opening'] + ta['mature'])}] canopy {inf.get('open_h', 0):.1f} m at spot, "
                   f"{inf.get('ring', 0):.0f} m mean in 8-30 m ring ({inf.get('closed', 0) * 100:.0f}% >= 10 m)")
    pk = inf.get("parking")
    if pk:
        out.append(f"[{_flag(tb.get('direction', 0))}] car {inf['bearing_box_to_car']:.0f} deg true from box "
                   f"({inf['direction_hypothesis']}); park on {pk['road']}")
        out.append(f"[{_flag(tb.get('walk_time', 0) + tb.get('uphill', 0))}] walk {inf['walk_m']:.0f} m "
                   f"~{inf['walk_min']:.1f} min, climb {inf['climb_m'] if inf['climb_m'] is None else round(inf['climb_m'])} m, "
                   f"max slope {inf['max_slope_deg']:.0f} deg")
        if inf.get("crossings") or tb.get("crossing", 0) < 0:
            out.append(f"[{_flag(tb.get('crossing', 0))}] straight walk crosses: {', '.join(inf['crossings']) or 'steep ground'}")
        if inf.get("regrowth_frac") is not None:
            out.append(f"[{_flag(tb.get('logging', 0))}] regrowth/old logging along walk {inf['regrowth_frac'] * 100:.0f}%")
        if inf.get("cattle_grid_m") is not None and inf["cattle_grid_m"] < p["cattle_grid_m"]:
            out.append(f"[weak] cattle grid {inf['cattle_grid_m']:.0f} m from parking")
    else:
        out.append(f"[BAD] no drivable road within {p['parking_search_m']:.0f} m")
    if "morning_sun" in tb:
        out.append(f"[{_flag(tb['morning_sun'])}] terrain sunrise 21.09 {inf.get('terrain_sunrise_local') or 'after 10:30'} "
                   f"(horizon {inf.get('horizon_deg', float('nan')):.1f} deg at sun az {inf.get('sun_az_deg', float('nan')):.0f}, "
                   f"checked {inf.get('horizon_covered_m', 0) / 1000:.1f} km)")
    if inf.get("sr16_species"):
        out.append(f"[{_flag(tb.get('sr16_point', 0))}] SR16 species {inf['sr16_species']}, height {inf.get('sr16_height')}")
    if missing:
        out.append("missing data: " + ", ".join(missing))
    return out


def _m(v):
    return "none nearby" if v is None or not np.isfinite(v) or v > 5000 else f"{v:.0f} m"


def candidate_record(c, ts=None):
    """JSON-ready dict with WGS84 coordinates."""
    lat, lon = (float(v) for v in to_wgs84(c["x"], c["y"]))
    inf = c["info"]
    rec = {"lat": round(lat, 6), "lon": round(lon, 6), "x_25833": round(c["x"], 1), "y_25833": round(c["y"], 1),
           "elevation_m": round(c["z"], 1), "score": round(c["score"], 3), "score_a": round(c["score_a"], 3),
           "score_b": round(c["score_b"], 3), "p_in_tile": c.get("p_in_tile"), "mass_a": c.get("mass_a"),
           "road_distance_m": _r(inf.get("road_dist_m")), "nearest_road": inf.get("nearest_road"),
           "slope_deg": _r(inf.get("slope"), 1), "canopy_at_spot_m": _r(inf.get("open_h"), 1),
           "canopy_ring_m": _r(inf.get("ring"), 1),
           "dist_water_osm_m": _r(inf.get("water_osm")), "dist_stream_dtm_m": _r(inf.get("water_dtm")),
           "dist_building_m": _r(inf.get("cabin")), "dist_trafficked_road_m": _r(inf.get("traffic")),
           "dist_railway_m": _r(inf.get("railway")), "dist_path_m": _r(inf.get("path_nearby")),
           "terms": {**{k: round(v, 3) for k, v in c["terms_a"].items()}, **{k: round(v, 3) for k, v in c["terms_b"].items()}},
           "contrib": {**{k: round(v, 3) for k, v in c["contrib_a"].items()}, **{k: round(v, 3) for k, v in c["contrib_b"].items()}},
           "reasons": c.get("reasons", [])}
    pk = inf.get("parking")
    if pk:
        plat, plon = (float(v) for v in to_wgs84(pk["x"], pk["y"]))
        rec["parking"] = {"lat": round(plat, 6), "lon": round(plon, 6), "x_25833": round(pk["x"], 1),
                          "y_25833": round(pk["y"], 1), "elevation_m": _r(pk["z"], 1), "road": pk["road"],
                          "osm_id": pk.get("osm_id")}
        rec.update({"walk_distance_m": _r(inf["walk_m"]), "walk_time_min": _r(inf["walk_min"], 1),
                    "climb_m": _r(inf["climb_m"], 1), "ascent_m": _r(inf["ascent_m"], 1),
                    "max_slope_deg": _r(inf["max_slope_deg"], 1),
                    "bearing_box_to_car_true": _r(inf["bearing_box_to_car"], 1),
                    "bearing_car_to_box_true": _r(inf["bearing_car_to_box"], 1),
                    "bearing_car_to_box_magnetic": _r(inf["bearing_car_to_box_magnetic"], 1),
                    "direction_hypothesis": inf["direction_hypothesis"], "walk_crossings": inf["crossings"],
                    "regrowth_frac": _r(inf.get("regrowth_frac"), 2)})
    else:
        rec["parking"] = None
    for k in ("terrain_sunrise_local", "sun_az_deg", "sun_el_deg", "horizon_deg", "horizon_covered_m"):
        if k in inf:
            rec[k] = inf[k] if isinstance(inf[k], str) or inf[k] is None else _r(inf[k], 2)
    return rec


def _r(v, nd=0):
    if v is None:
        return None
    v = float(v)
    if not np.isfinite(v):
        return None
    return round(v, nd) if nd else int(round(v))
