"""Star fields: bundled bright-star catalogue, pattern matching and plate solving.

Catalogue
---------
``data/bright_stars.csv`` holds every Hipparcos star with V <= 5.0 (1625 stars;
the 300 brightest reach V = 3.54) taken from the HYG database v4.1
(astronexus, CC BY-SA 4.0; a merge of Hipparcos, the Yale Bright Star Catalog
and Gliese): ICRS/J2000 positions at epoch J2000, proper motions (mas/yr,
mu_alpha* = mu_alpha cos dec) and V magnitudes.  ``build_catalogue_from_hyg``
regenerates it from ``hygdata_v41.csv``; nothing is typed in by hand.  The cut is
deeper than the ~300 naked-eye showpieces because a 65 x 40 deg field at night
only holds ~7 stars brighter than V = 3.5: the matcher needs the fainter ones
when the camera (IR night mode, dark forest) reaches V ~ 4.5-5.

Matching (built-in, no astrometry.net needed)
---------------------------------------------
1. Predict where catalogue stars should appear with an *approximate* camera:
   either the Earth-fixed camera orientation G found from the sun track
   (location independent, so the prediction is good to the pose accuracy) or the
   configured heading/pitch/roll/HFOV at the domain centre.
2. Triangle voting: side-length-ratio invariants (a/c, b/c) of triangles of the
   brightest ~12 detections are looked up (KD-tree) among triangles of the
   brightest ~30 predicted stars; every hit proposes a 2-D similarity (complex
   least squares, vectorised); the similarity with most inliers wins (scale and
   rotation must stay plausible).  A pure camera rotation maps one image onto
   another by a homography; for pointing errors of a few degrees a similarity is
   good to ~2 % of the width, enough to seed step 3.
3. Refine: homography from the inliers, re-match all detections, then a full
   pinhole fit (attitude + focal length) and mutual-nearest-neighbour matching
   against the whole catalogue.

The matched stars (pixel, apparent RA/Dec of date) feed the same location solver
as the sun track (``solver.CelestialFitter``).  Remember the degeneracy explained
in camera.py: a star field fixes the camera orientation relative to the Earth
to arcseconds, the *site* only as well as the level reference (pitch/roll).

astrometry.net
--------------
If ``solve-field`` is installed (with index files) ``astrometry_solve`` writes an
xylist FITS table, runs it blind within the plausible plate-scale range and
parses the ``.corr`` file (matched pixel <-> catalogue RA/Dec).  It fails soft
(returns None) when the tool is missing, times out, or finds no solution.
"""
from __future__ import annotations

import csv
import functools
import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

from . import ephem
from .camera import project, rotation_matrix

log = logging.getLogger("hordewatch.astro")

DATA = Path(__file__).resolve().parent / "data"
CATALOGUE = DATA / "bright_stars.csv"
HYG_URL = "https://raw.githubusercontent.com/astronexus/HYG-Database/main/hyg/CURRENT/hygdata_v41.csv"


# ----------------------------------------------------------------------------- catalogue
@dataclass
class Catalogue:
    name: np.ndarray
    hip: np.ndarray
    ra: np.ndarray
    dec: np.ndarray
    pmra: np.ndarray
    pmdec: np.ndarray
    vmag: np.ndarray

    def __len__(self):
        return len(self.ra)

    def subset(self, m):
        return Catalogue(*(getattr(self, k)[m] for k in ("name", "hip", "ra", "dec", "pmra", "pmdec", "vmag")))


@functools.lru_cache(maxsize=4)
def load_catalogue(vmax: float | None = None, path: str | None = None) -> Catalogue:
    rows = []
    with open(path or CATALOGUE) as f:
        for r in csv.DictReader(line for line in f if not line.startswith("#")):
            rows.append(r)
    cat = Catalogue(np.array([r["name"] for r in rows]), np.array([int(r["hip"]) for r in rows]),
                    np.array([float(r["ra_deg"]) for r in rows]), np.array([float(r["dec_deg"]) for r in rows]),
                    np.array([float(r["pmra_mas_yr"] or 0) for r in rows]),
                    np.array([float(r["pmdec_mas_yr"] or 0) for r in rows]),
                    np.array([float(r["vmag"]) for r in rows]))
    if vmax is not None:
        cat = cat.subset(cat.vmag <= vmax)
    return cat


def build_catalogue_from_hyg(hyg_csv, out=CATALOGUE, vmax=5.0):
    """Regenerate data/bright_stars.csv from HYG v4.1 (download HYG_URL first)."""
    import pandas as pd

    d = pd.read_csv(hyg_csv, low_memory=False)
    d = d[(d["id"] > 0) & d["hip"].notna() & (d["mag"] <= vmax)].sort_values("mag")

    def name(r):
        if isinstance(r["proper"], str) and r["proper"].strip():
            return r["proper"].strip()
        if isinstance(r["bf"], str) and r["bf"].strip():
            return " ".join(r["bf"].split())
        return f"HIP {int(r['hip'])}"

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        f.write(f"# Bright-star catalogue for hordewatch.astro: all Hipparcos stars with V <= {vmax} ({len(d)} stars)\n")
        f.write(f"# Source: HYG database v4.1 (astronexus), {HYG_URL}\n")
        f.write("# HYG = Hipparcos + Yale Bright Star Catalog + Gliese; licence CC BY-SA 4.0 (http://creativecommons.org/licenses/by-sa/4.0/)\n")
        f.write("# ra_deg/dec_deg: ICRS/J2000, epoch J2000 (HYG ra hours x 15); pmra = mu_alpha* (mas/yr, x cos dec); vmag = V\n")
        f.write("# Generated by hordewatch.astro.stars.build_catalogue_from_hyg; sorted by vmag (row k = k-th brightest)\n")
        w = csv.writer(f)
        w.writerow(["name", "hip", "ra_deg", "dec_deg", "pmra_mas_yr", "pmdec_mas_yr", "vmag"])
        for _, r in d.iterrows():
            w.writerow([name(r), int(r["hip"]), f"{r['ra'] * 15.0:.6f}", f"{r['dec']:.6f}",
                        f"{r['pmra']:.2f}", f"{r['pmdec']:.2f}", f"{r['mag']:.2f}"])
    return out


# ----------------------------------------------------------------------------- prediction
@dataclass
class ApproxCamera:
    """Approximate pose for prediction: Earth-fixed->camera rotation G plus intrinsics (width units)."""
    G: np.ndarray
    f: float
    cx: float = 0.5
    cy: float = 0.28125
    k1: float = 0.0
    lat: float = 61.25
    lon: float = 9.0

    @classmethod
    def from_attitude(cls, heading, pitch, roll, f, lat, lon, aspect=720 / 1280, k1=0.0):
        _, T = ephem.observer_frame(lat, lon)
        return cls(rotation_matrix(heading, pitch, roll) @ T, f, 0.5, 0.5 * aspect, k1, lat, lon)


def predict_catalogue(cat: Catalogue, when, cam: ApproxCamera, refraction=True, margin=0.25, aspect=720 / 1280):
    """Pixel positions (width units) of catalogue stars at `when` for an approximate camera.

    Returns (index array into cat, X, Y, places) for stars above the horizon and within
    the image extended by `margin` (fraction of the width) on every side.
    """
    pl = ephem.star_places(cat.ra, cat.dec, cat.pmra, cat.pmdec, when)
    e = pl.e_ef()
    r, T = ephem.observer_frame(np.array([cam.lat]), np.array([cam.lon]))
    enu = ephem.topocentric_enu(e, pl.dist_km, r, T)[0]
    up = enu[:, 2] > np.sin(np.radians(-0.5))
    if refraction:
        enu = ephem.apply_refraction(enu)
    # camera orientation in ENU at the approximate site: R = G T^T
    R = cam.G @ T[0].T
    c = enu @ R.T
    X, Y, front = project(c, cam.f, cam.cx, cam.cy, cam.k1)
    ok = up & front & (X > -margin) & (X < 1 + margin) & (Y > -margin) & (Y < aspect + margin)
    idx = np.nonzero(ok)[0]
    return idx, X[idx], Y[idx], pl


# ----------------------------------------------------------------------------- triangle matching
def _triangles(xy, max_pts):
    n = min(len(xy), max_pts)
    if n < 3:
        return np.zeros((0, 3), int), np.zeros((0, 2))
    comb = np.array([(a, b, c) for a in range(n) for b in range(a + 1, n) for c in range(b + 1, n)], int)
    P = xy[comb]                                       # (T, 3, 2)
    # side opposite vertex v
    s = np.stack([np.linalg.norm(P[:, 1] - P[:, 2], axis=1), np.linalg.norm(P[:, 0] - P[:, 2], axis=1),
                  np.linalg.norm(P[:, 0] - P[:, 1], axis=1)], axis=1)
    order = np.argsort(s, axis=1)                      # vertex opposite shortest, middle, longest
    ss = np.take_along_axis(s, order, 1)
    verts = np.take_along_axis(comb, order, 1)
    inv = np.stack([ss[:, 0] / ss[:, 2], ss[:, 1] / ss[:, 2]], axis=1)
    Q = xy[verts]
    orient = np.sign((Q[:, 1, 0] - Q[:, 0, 0]) * (Q[:, 2, 1] - Q[:, 0, 1]) - (Q[:, 1, 1] - Q[:, 0, 1]) * (Q[:, 2, 0] - Q[:, 0, 0]))
    # ambiguous vertex order (near-equal sides) and slivers are useless
    good = (ss[:, 2] > 1e-6) & (inv[:, 0] > 0.12) & (np.diff(ss, axis=1).min(axis=1) > 0.03 * ss[:, 2])
    return verts[good], np.c_[inv[good], orient[good]]


def _similarity(src, dst):
    """Complex least-squares similarity dst ~ a*src + b for (..., n) complex arrays."""
    ms, md = src.mean(-1, keepdims=True), dst.mean(-1, keepdims=True)
    a = np.sum((dst - md) * np.conj(src - ms), -1) / np.maximum(np.sum(np.abs(src - ms) ** 2, -1), 1e-18)
    b = md[..., 0] - a * ms[..., 0]
    return a, b


def _homography(src, dst):
    import cv2
    H, _ = cv2.findHomography(src.astype(np.float64), dst.astype(np.float64), 0)
    return H


def _apply_h(H, xy):
    p = np.c_[xy, np.ones(len(xy))] @ H.T
    return p[:, :2] / p[:, 2:3]


def _mutual_nn(a, b, radius):
    """Mutual nearest neighbours between point sets a (n,2) and b (m,2) within radius."""
    if len(a) == 0 or len(b) == 0:
        return np.zeros((0, 2), int)
    ta, tb = cKDTree(a), cKDTree(b)
    d_ab, j = tb.query(a)
    _, i_back = ta.query(b)
    pairs = [(i, jj) for i, (jj, d) in enumerate(zip(j, d_ab)) if d <= radius and i_back[jj] == i]
    return np.array(pairs, int).reshape(-1, 2)


def triangle_match(det_xy, cat_xy, n_det=12, n_cat=30, tol=0.012, radius=0.025, scale_range=(0.6, 1.6),
                   max_rot_deg=40.0, min_inliers=4):
    """Match detections (brightest first) to predicted catalogue positions (brightest first).

    Coordinates in image-width units.  Returns (pairs (k,2) [det_idx, cat_idx], similarity (a, b)) or
    (empty, None) when no convincing match exists.
    """
    det_xy, cat_xy = np.asarray(det_xy, float), np.asarray(cat_xy, float)
    vd, invd = _triangles(det_xy, n_det)
    vc, invc = _triangles(cat_xy, n_cat)
    if len(vd) == 0 or len(vc) == 0:
        return np.zeros((0, 2), int), None
    tree = cKDTree(invc[:, :2])
    hits = tree.query_ball_point(invd[:, :2], tol)
    di, ci = [], []
    for k, h in enumerate(hits):
        for m in h:
            if invc[m, 2] == invd[k, 2]:
                di.append(k)
                ci.append(m)
    if not di:
        return np.zeros((0, 2), int), None
    di, ci = np.array(di), np.array(ci)
    zd = det_xy[vd[di]] @ np.array([1, 1j])            # (H, 3) complex
    zc = cat_xy[vc[ci]] @ np.array([1, 1j])
    a, b = _similarity(zd, zc)
    sc, rot = np.abs(a), np.degrees(np.angle(a))
    ok = (sc > scale_range[0]) & (sc < scale_range[1]) & (np.abs(rot) < max_rot_deg)
    if not ok.any():
        return np.zeros((0, 2), int), None
    a, b = a[ok], b[ok]
    nd = min(len(det_xy), n_det)
    zall = det_xy[:nd] @ np.array([1, 1j])
    zcat = cat_xy[: max(n_cat, 3)] @ np.array([1, 1j])
    best = None
    for s in range(0, len(a), 2000):                  # chunks keep memory bounded
        proj = a[s:s + 2000, None] * zall[None, :] + b[s:s + 2000, None]
        d = np.abs(proj[:, :, None] - zcat[None, None, :]).min(axis=2)
        score = (d < radius).sum(1) - 0.5 * np.minimum(d, radius).sum(1) / radius / nd
        k = int(np.argmax(score))
        if best is None or score[k] > best[0]:
            best = (score[k], a[s + k], b[s + k])
    if best is None or best[0] < min_inliers:
        return np.zeros((0, 2), int), None
    _, a_best, b_best = best
    proj = a_best * (det_xy @ np.array([1, 1j])) + b_best
    pairs = _mutual_nn(np.c_[proj.real, proj.imag], cat_xy, radius)
    return pairs, (a_best, b_best)


# ----------------------------------------------------------------------------- full frame matching
@dataclass
class FrameMatch:
    pairs: np.ndarray            # (k, 2) detection index, catalogue index
    X: np.ndarray                # matched detections (width units)
    Y: np.ndarray
    places: object               # ephem.Places of the matched stars (apparent, of date)
    names: list
    vmag: np.ndarray
    rms: float                   # width units, after the camera fit
    G: np.ndarray                # fitted Earth-fixed -> camera rotation (at the approx site)
    f: float
    method: str


def _fit_pose(Xd, Yd, e_ef, dist, cam: ApproxCamera, x0, fit_k1=False):
    """Least-squares attitude (at cam.lat/lon) + ln f (+k1) to matched points; returns (x, rms)."""
    r, T = ephem.observer_frame(np.array([cam.lat]), np.array([cam.lon]))
    enu = ephem.apply_refraction(ephem.topocentric_enu(e_ef, dist, r, T)[0])

    def res(p):
        R = rotation_matrix(p[0], p[1], p[2])
        X, Y, _ = project(enu @ R.T, np.exp(p[3]), cam.cx, cam.cy, p[4] if fit_k1 else 0.0)
        return np.r_[X - Xd, Y - Yd]

    x0 = np.r_[x0, 0.0] if fit_k1 else np.asarray(x0, float)
    sol = least_squares(res, x0, loss="soft_l1", f_scale=0.004, x_scale=np.r_[1, 1, 1, 0.01, 0.01][:len(x0)])
    rr = res(sol.x).reshape(2, -1)
    return sol.x, float(np.sqrt(np.mean(np.sum(rr ** 2, 0)))), T[0]


def match_frame(points, when, cam: ApproxCamera, aspect=720 / 1280, vmax=5.0, n_det=12, n_cat=30,
                min_matches=5, max_rms=0.004) -> FrameMatch | None:
    """Identify detected point sources [[X, Y, flux], ...] (width units) with catalogue stars.

    Returns None when fewer than min_matches stars are identified or the final pinhole fit is
    worse than max_rms (width units; 0.004 = 5 px at 1280) - the guard against false matches.
    """
    pts = np.asarray(points, float)
    if len(pts) < 4:
        return None
    det_order = np.argsort(-pts[:, 2], kind="stable") if pts.shape[1] > 2 else np.arange(len(pts))
    pts = pts[det_order]
    det = pts[:, :2]
    cat = load_catalogue(vmax)
    idx, Xc, Yc, pl = predict_catalogue(cat, when, cam, aspect=aspect)
    if len(idx) < 4:
        return None
    order = np.argsort(cat.vmag[idx])
    idx, Xc, Yc = idx[order], Xc[order], Yc[order]
    cxy = np.c_[Xc, Yc]
    method = "predict"
    # (a) direct nearest-neighbour match when the prediction is already good (camera G known)
    pairs = _mutual_nn(det, cxy, 0.006)
    if len(pairs) < max(min_matches, 0.5 * min(len(det), len(cxy))):
        method = "triangles"
        pairs, sim = triangle_match(det, cxy, n_det=n_det, n_cat=n_cat)
        if len(pairs) < 4:
            return None
        # homography refinement with all detections
        for radius in (0.02, 0.01):
            if len(pairs) < 4:
                return None
            H = _homography(det[pairs[:, 0]], cxy[pairs[:, 1]])
            if H is None:
                return None
            pairs = _mutual_nn(_apply_h(H, det), cxy, radius)
    if len(pairs) < 4:
        return None
    # (b) full camera fit at the approximate site, then deep mutual-NN re-match
    e_all = pl.e_ef()[idx]
    dist_all = pl.dist_km[idx]
    R0 = cam.G @ ephem.observer_frame(cam.lat, cam.lon)[1].T
    from .camera import attitude_from_rotation
    h0, p0, r0 = attitude_from_rotation(R0)
    x = np.array([h0, p0, r0, np.log(cam.f)])
    rms = np.inf
    for radius in (0.012, 0.005, 0.003):
        x, rms, T = _fit_pose(det[pairs[:, 0], 0], det[pairs[:, 0], 1], e_all[pairs[:, 1]], dist_all[pairs[:, 1]], cam, x[:4])
        r_, T_ = ephem.observer_frame(np.array([cam.lat]), np.array([cam.lon]))
        enu = ephem.apply_refraction(ephem.topocentric_enu(e_all, dist_all, r_, T_)[0])
        Xp, Yp, front = project(enu @ rotation_matrix(x[0], x[1], x[2]).T, np.exp(x[3]), cam.cx, cam.cy)
        new = _mutual_nn(det, np.c_[np.where(front, Xp, 9.0), np.where(front, Yp, 9.0)], max(radius, 4 * rms))
        if len(new) >= 4:
            pairs = new
    if len(pairs) < min_matches:
        return None
    x, rms, T = _fit_pose(det[pairs[:, 0], 0], det[pairs[:, 0], 1], e_all[pairs[:, 1]], dist_all[pairs[:, 1]], cam, x[:4])
    if rms > max_rms:                     # a wrong identification cannot be fitted by any real camera
        log.info("astro: star match rejected (rms %.4f width units, %d pairs)", rms, len(pairs))
        return None
    ci = idx[pairs[:, 1]]
    sub = ephem.Places(pl.t_unix[ci], pl.ra_deg[ci], pl.dec_deg[ci], pl.dist_km[ci], pl.gast_deg[ci], pl.gha_rate[ci])
    G = rotation_matrix(x[0], x[1], x[2]) @ T
    # detection indices refer to the caller's order (we sorted by flux internally)
    return FrameMatch(pairs=np.c_[det_order[pairs[:, 0]], ci], X=det[pairs[:, 0], 0], Y=det[pairs[:, 0], 1], places=sub,
                      names=list(cat.name[ci]), vmag=cat.vmag[ci], rms=rms, G=G, f=float(np.exp(x[3])), method=method)


def plate_summary(fm: FrameMatch, width, aspect, cx=0.5, cy=None):
    """plate_solution Observation value: boresight RA/Dec (of date), scale, rotation, matched stars."""
    cy = 0.5 * aspect if cy is None else cy
    gast = float(fm.places.gast_deg[0])
    fwd_ef = fm.G[2]
    dec = np.degrees(np.arcsin(np.clip(fwd_ef[2], -1, 1)))
    gha = np.degrees(np.arctan2(-fwd_ef[1], fwd_ef[0]))
    ra = (gast - gha) % 360.0
    # position angle of image 'up' (-y) measured from celestial north through east
    up_ef = -fm.G[1]
    north = np.array([-np.sin(np.radians(dec)) * np.cos(np.radians(gha)), np.sin(np.radians(dec)) * np.sin(np.radians(gha)),
                      np.cos(np.radians(dec))])
    east = np.cross(north, fwd_ef)
    rot = np.degrees(np.arctan2(np.dot(up_ef, east), np.dot(up_ef, north))) % 360.0
    return {"ra_deg": float(ra), "dec_deg": float(dec), "scale_arcsec_px": float(3600 * np.degrees(1.0 / (fm.f * width))),
            "rot_deg": float(rot), "n_matched": int(len(fm.X)), "rms_px": float(fm.rms * width), "method": fm.method,
            "stars": [[round(float(x * width), 2), round(float(y * width), 2), n, float(v)]
                      for x, y, n, v in zip(fm.X, fm.Y, fm.names, fm.vmag)]}


# ----------------------------------------------------------------------------- astrometry.net
def solve_field_available() -> bool:
    return shutil.which("solve-field") is not None


def write_xyls(path, xy_px, flux, width, height):
    """astrometry.net xylist (FITS binary table X, Y, FLUX; FITS 1-based pixel convention)."""
    from astropy.io import fits

    cols = [fits.Column(name="X", format="D", array=np.asarray(xy_px)[:, 0] + 1.0),
            fits.Column(name="Y", format="D", array=np.asarray(xy_px)[:, 1] + 1.0),
            fits.Column(name="FLUX", format="D", array=np.asarray(flux, float))]
    hdu = fits.BinTableHDU.from_columns(cols)
    hdu.header["IMAGEW"] = int(width)
    hdu.header["IMAGEH"] = int(height)
    fits.HDUList([fits.PrimaryHDU(), hdu]).writeto(path, overwrite=True)
    return path


def astrometry_solve(xy_px, flux, width, height, scale_low=100.0, scale_high=600.0, timeout=90, workdir=None):
    """Plate-solve with a local astrometry.net; returns {'pairs': [[x, y, ra_icrs, dec_icrs]...], 'wcs': header} or None.

    Scale bounds are arcsec/pixel (a 1280-px frame with HFOV 50-100 deg -> ~140-280").
    Needs index files covering wide fields (4100-series 4107-4119).  Fails soft.
    """
    if not solve_field_available():
        log.info("astro: solve-field not installed; using the built-in triangle matcher")
        return None
    from astropy.io import fits

    wd = Path(workdir or tempfile.mkdtemp(prefix="hw_astrometry_"))
    xyls = write_xyls(wd / "field.xyls", xy_px, flux, width, height)
    cmd = ["solve-field", "--overwrite", "--no-plots", "--no-verify", "--width", str(int(width)), "--height",
           str(int(height)), "--x-column", "X", "--y-column", "Y", "--sort-column", "FLUX", "--scale-units",
           "arcsecperpix", "--scale-low", str(scale_low), "--scale-high", str(scale_high), "--crpix-center",
           "--dir", str(wd), "--cpulimit", str(int(timeout)), str(xyls)]
    try:
        subprocess.run(cmd, capture_output=True, timeout=timeout + 15, check=False)
    except Exception as e:
        log.warning("astro: solve-field failed: %s", e)
        return None
    corr = wd / "field.corr"
    wcs = wd / "field.wcs"
    if not corr.exists():
        log.info("astro: solve-field found no solution")
        return None
    with fits.open(corr) as h:
        t = h[1].data
        pairs = np.c_[t["field_x"] - 1.0, t["field_y"] - 1.0, t["index_ra"], t["index_dec"]]
    header = dict(fits.getheader(wcs)) if wcs.exists() else {}
    return {"pairs": pairs.tolist(), "wcs": {k: v for k, v in header.items() if isinstance(v, (int, float, str))}}
