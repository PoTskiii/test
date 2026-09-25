"""Foxhunt geolocation: turn field measurements into a location estimate.

Two classic passive direction-finding problems are solved here, both used to
localise the forest box's *uplink transmitter* (the Starlink router's WiFi, a
4G/5G modem, a crew camp's phones/WiFi) from measurements a searcher collects
while walking or driving the forest roads:

1. **Bearing intersection** -- from several (lat, lon, bearing) fixes taken with
   a directional antenna (Yagi/log-periodic) or a body-shadowing null, find the
   point that best explains all the lines of bearing (weighted least squares of
   perpendicular offsets).

2. **RSSI multilateration** -- from several (lat, lon, RSSI) samples of the same
   transmitter, fit the log-distance path-loss model

       RSSI(d) = P0 - 10 * n * log10(d / d0)          (d0 = 1 m)

   for the transmitter position and its reference power P0 (path-loss exponent
   ``n`` fixed by default, optionally fit). This is what a phone WiFi scanner or
   an SDR power meter gives you for free while you drive.

Everything is computed in a *local east-north tangent plane* (equirectangular
about the mean measurement point) so that a compass bearing maps to the exact
plane direction ``(sin theta, cos theta)`` with no grid convergence, then
converted back to WGS84.

Assumptions / failure modes
---------------------------
* Bearings are true (geographic) bearings; correct magnetic-compass readings for
  declination (~+2..+3 deg in SE Norway, 2026) *before* passing them in.
* RSSI path loss assumes a single dominant transmitter and roughly isotropic,
  log-distance propagation. Forest canopy, terrain shadowing, multipath and
  antenna gain patterns all break this -- so the returned sigma is only a
  formal (Gauss-Newton) uncertainty and is optimistic; treat it as "walk here,
  keep sampling" guidance, not a survey fix. Reflections can pull the estimate
  toward a false peak; take samples spread widely in angle around the target.
* Near-collinear bearings (all taken from one road) give a huge along-line
  uncertainty; the condition number is reported so callers can warn.
* Nothing here transmits. This is passive DF only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np

R_EARTH_M = 6371008.8


# --------------------------------------------------------------------------- projection
def _center(lats, lons):
    return float(np.mean(lats)), float(np.mean(lons))


def to_enu(lats, lons, lat0, lon0):
    """WGS84 -> local east (x) / north (y) metres about (lat0, lon0)."""
    lats = np.asarray(lats, float)
    lons = np.asarray(lons, float)
    x = np.radians(lons - lon0) * math.cos(math.radians(lat0)) * R_EARTH_M
    y = np.radians(lats - lat0) * R_EARTH_M
    return x, y


def to_wgs84(x, y, lat0, lon0):
    """Local east/north metres -> WGS84 lat/lon."""
    lat = lat0 + np.degrees(np.asarray(y, float) / R_EARTH_M)
    lon = lon0 + np.degrees(np.asarray(x, float) / (R_EARTH_M * math.cos(math.radians(lat0))))
    return lat, lon


def map_links(lat, lon):
    """(norgeskart, google_maps) URLs for a fix. Norgeskart wants EPSG:25833
    easting/northing; if pyproj is missing we fall back to a lat/lon-only link."""
    gm = f"https://www.google.com/maps/search/?api=1&query={lat:.6f},{lon:.6f}"
    try:
        from pyproj import Transformer
        e, n = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True).transform(lon, lat)
        nk = (f"https://norgeskart.no/#!?project=norgeskart&layers=1002&zoom=15&lat={n:.0f}&lon={e:.0f}"
              f"&markerLat={n:.0f}&markerLon={e:.0f}")
    except Exception:
        nk = f"https://norgeskart.no/#!?project=norgeskart&zoom=15&lat={lat:.6f}&lon={lon:.6f}"
    return nk, gm


# --------------------------------------------------------------------------- results
@dataclass
class Fix:
    lat: float
    lon: float
    sigma_m: float                 # 1-sigma position uncertainty (formal, isotropic-equivalent)
    method: str
    n_used: int
    cov_enu: Optional[np.ndarray] = None   # 2x2 covariance in the local ENU frame (m^2)
    extra: dict = field(default_factory=dict)

    @property
    def norgeskart(self):
        return map_links(self.lat, self.lon)[0]

    @property
    def google_maps(self):
        return map_links(self.lat, self.lon)[1]

    def summary(self) -> str:
        nk, gm = map_links(self.lat, self.lon)
        return (f"{self.method}: {self.lat:.5f}, {self.lon:.5f}  +/- {self.sigma_m:.0f} m "
                f"(n={self.n_used})\n  {gm}\n  {nk}")


# --------------------------------------------------------------------------- bearing intersection
def bearing_intersection(fixes: Sequence[Sequence[float]], weights=None) -> Fix:
    """Least-squares intersection of lines of bearing.

    ``fixes`` = [(lat, lon, bearing_deg), ...], bearing_deg true (from north,
    clockwise). Minimises the sum of squared *perpendicular* distances from the
    estimate to each bearing line. Needs >= 2 non-parallel bearings.

    The bearing line through observer ``p`` with unit direction ``d`` has
    projector ``(I - d d^T)``; stacking the normal equations gives
    ``A q = b`` with ``A = sum w_i (I - d_i d_i^T)``. Covariance is
    ``s^2 A^-1`` with ``s^2`` the reduced perpendicular-residual variance.
    """
    arr = np.asarray(fixes, float)
    if arr.shape[0] < 2:
        raise ValueError("need at least two bearings")
    lats, lons, brg = arr[:, 0], arr[:, 1], arr[:, 2]
    lat0, lon0 = _center(lats, lons)
    px, py = to_enu(lats, lons, lat0, lon0)
    th = np.radians(brg)
    d = np.stack([np.sin(th), np.cos(th)], axis=1)          # (east, north) unit vectors
    p = np.stack([px, py], axis=1)
    w = np.ones(len(arr)) if weights is None else np.asarray(weights, float)

    A = np.zeros((2, 2))
    b = np.zeros(2)
    I = np.eye(2)
    for wi, di, pi in zip(w, d, p):
        M = wi * (I - np.outer(di, di))
        A += M
        b += M @ pi
    cond = float(np.linalg.cond(A))
    q = np.linalg.solve(A, b)

    # perpendicular residuals
    res = np.array([np.linalg.norm((I - np.outer(di, di)) @ (q - pi)) for di, pi in zip(d, p)])
    dof = max(len(arr) - 2, 1)
    s2 = float((w * res ** 2).sum() / dof) if len(arr) > 2 else float(np.mean(res ** 2) + 1.0)
    Ainv = np.linalg.pinv(A)
    cov = s2 * Ainv
    sigma = float(np.sqrt(max(np.trace(cov), 0.0)))
    lat, lon = to_wgs84(q[0], q[1], lat0, lon0)
    return Fix(float(lat), float(lon), sigma, "bearing_intersection", len(arr), cov,
               {"cond": cond, "residuals_m": res.tolist(),
                "near_parallel": cond > 50.0})


# --------------------------------------------------------------------------- RSSI multilateration
def _linear_power(rssi):
    return 10.0 ** (np.asarray(rssi, float) / 10.0)


def rssi_multilaterate(samples: Sequence[Sequence[float]], n: float = 2.7,
                       fit_n: bool = False, d0_m: float = 1.0,
                       n_bounds=(1.6, 4.5)) -> Fix:
    """Locate a transmitter from RSSI samples via log-distance path loss.

    ``samples`` = [(lat, lon, rssi_dbm), ...] (>= 3). Fits transmitter position
    and reference power ``P0`` (RSSI at ``d0_m``); path-loss exponent ``n`` is
    fixed unless ``fit_n`` (then it too is estimated, needs >= 4 well-spread
    samples). Uses scipy least-squares; the initial guess is the RSSI-power
    weighted centroid.

    Returns a :class:`Fix`; ``extra`` carries P0, n, rms residual (dB) and the
    per-sample residuals. Sigma is the formal Gauss-Newton position sigma and is
    optimistic in real forest multipath -- widen it in your head.
    """
    arr = np.asarray(samples, float)
    if arr.shape[0] < 3:
        raise ValueError("need at least three RSSI samples")
    lats, lons, rssi = arr[:, 0], arr[:, 1], arr[:, 2]
    lat0, lon0 = _center(lats, lons)
    px, py = to_enu(lats, lons, lat0, lon0)

    # initial guess: power-weighted centroid, biased toward strongest sample
    wl = _linear_power(rssi)
    x0 = float(np.sum(wl * px) / np.sum(wl))
    y0 = float(np.sum(wl * py) / np.sum(wl))
    k = int(np.argmax(rssi))
    x0 = 0.5 * (x0 + px[k])
    y0 = 0.5 * (y0 + py[k])
    p0_guess = float(np.max(rssi) + 10.0 * n * math.log10(max(1.0, math.hypot(px[k] - x0, py[k] - y0)) / d0_m))

    from scipy.optimize import least_squares

    def model(params):
        tx, ty, P0 = params[0], params[1], params[2]
        nn = params[3] if fit_n else n
        d = np.hypot(px - tx, py - ty)
        d = np.maximum(d, d0_m)
        return P0 - 10.0 * nn * np.log10(d / d0_m)

    def resid(params):
        return model(params) - rssi

    span = max(np.ptp(px), np.ptp(py), 100.0)
    lo = [x0 - 5 * span, y0 - 5 * span, -40.0] + ([n_bounds[0]] if fit_n else [])
    hi = [x0 + 5 * span, y0 + 5 * span, 90.0] + ([n_bounds[1]] if fit_n else [])
    guess = [x0, y0, p0_guess] + ([n] if fit_n else [])
    # keep the initial guess strictly inside the bounds
    guess = [min(max(g, l + 1e-6), h - 1e-6) for g, l, h in zip(guess, lo, hi)]
    sol = least_squares(resid, guess, bounds=(lo, hi), method="trf", max_nfev=2000)

    tx, ty, P0 = sol.x[0], sol.x[1], sol.x[2]
    n_hat = sol.x[3] if fit_n else n
    res = sol.fun
    m, kk = len(rssi), len(sol.x)
    dof = max(m - kk, 1)
    s2 = float(np.sum(res ** 2) / dof)
    # position covariance: take the 2x2 block of s2 * (J^T J)^-1
    try:
        JtJ = sol.jac.T @ sol.jac
        cov_full = s2 * np.linalg.pinv(JtJ)
        cov = cov_full[:2, :2]
        sigma = float(np.sqrt(max(np.trace(cov), 0.0)))
    except Exception:
        cov = None
        sigma = float("nan")
    lat, lon = to_wgs84(tx, ty, lat0, lon0)
    return Fix(float(lat), float(lon), sigma, "rssi_multilaterate" + ("_fitn" if fit_n else ""),
               m, cov, {"P0_dbm": float(P0), "n": float(n_hat), "rms_db": float(np.sqrt(s2)),
                        "residuals_db": res.tolist(), "cost": float(sol.cost)})


# --------------------------------------------------------------------------- dispatch
def estimate(measurements: Sequence[dict]) -> Fix:
    """Estimate a location from a list of measurement dicts.

    Each dict has ``lat``, ``lon`` and either ``bearing`` (deg) or ``rssi``
    (dBm). If any bearings are present they are used (bearing intersection);
    otherwise RSSI multilateration is used.
    """
    brg = [(m["lat"], m["lon"], m["bearing"]) for m in measurements if m.get("bearing") is not None]
    if len(brg) >= 2:
        return bearing_intersection(brg)
    rss = [(m["lat"], m["lon"], m["rssi"]) for m in measurements if m.get("rssi") is not None]
    if len(rss) >= 3:
        return rssi_multilaterate(rss)
    raise ValueError("need >=2 bearings or >=3 RSSI samples")


# --------------------------------------------------------------------------- CLI
def _read_csv(path):
    import csv
    out = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            m = {"lat": float(row["lat"]), "lon": float(row["lon"])}
            if row.get("bearing") not in (None, ""):
                m["bearing"] = float(row["bearing"])
            if row.get("rssi") not in (None, ""):
                m["rssi"] = float(row["rssi"])
            out.append(m)
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Foxhunt geolocation from bearings or RSSI.")
    ap.add_argument("csv", help="CSV with columns lat,lon and bearing and/or rssi")
    ap.add_argument("--n", type=float, default=2.7, help="path-loss exponent (RSSI mode)")
    ap.add_argument("--fit-n", action="store_true", help="also fit the path-loss exponent")
    a = ap.parse_args(argv)
    ms = _read_csv(a.csv)
    if any(m.get("bearing") is not None for m in ms):
        fix = bearing_intersection([(m["lat"], m["lon"], m["bearing"]) for m in ms if m.get("bearing") is not None])
    else:
        fix = rssi_multilaterate([(m["lat"], m["lon"], m["rssi"]) for m in ms if m.get("rssi") is not None],
                                 n=a.n, fit_n=a.fit_n)
    print(fix.summary())
    if fix.extra.get("near_parallel"):
        print("  WARNING: bearings nearly parallel (cond=%.0f) -- large along-line uncertainty." % fix.extra["cond"])


if __name__ == "__main__":
    main()
