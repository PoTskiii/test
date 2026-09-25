"""Offline ephemerides and vectorised topocentric geometry.

Design
------
skyfield (with the DE421 kernel and timescale data bundled by ``skyfield-data``;
nothing is ever downloaded) is used only for what is *observer independent*:
the apparent geocentric right ascension / declination of the Sun, the Moon or a
star (true equator and equinox of date: precession, nutation, annual
aberration, light time and gravitational deflection included) and the Greenwich
apparent sidereal time GAST.  Everything that depends on the observer is done
here with plain numpy so that one call handles thousands of candidate
locations x hundreds of epochs at once:

    GHA  = GAST - RA                     Greenwich hour angle (deg, westward)
    e_EF = (cos d cos GHA, -cos d sin GHA, sin d)
                                          unit vector in the Earth-fixed,
                                          true-of-date frame (x: Greenwich
                                          meridian, y: 90 E, z: north pole)
    v    = dist * e_EF - r_obs           topocentric vector (km); r_obs is the
                                          WGS84 geocentric position of the site
    (E, N, U) = T(lat, lon) . v          local east/north/up
    alt  = atan2(U, hypot(E, N)),  az = atan2(E, N)

The parallax term matters for the Moon (up to ~1 deg), is 8.8 arcsec for the
Sun and zero for stars (dist = inf).  Polar motion (< 0.5 arcsec) and diurnal
aberration (0.3 arcsec) are neglected.  Accuracy against skyfield's own
topocentric ``altaz`` is better than 0.001 deg for the Sun and ~0.002 deg for
the Moon (see tests/test_astro.py).

Refraction: Saemundsson's (1986) formula for the *true* (airless) altitude,
the inverse of Bennett's formula used by skyfield, scaled by pressure and
temperature.  It is accurate to ~0.1 arcmin above 5 deg; below ~3 deg real
refraction varies by +-10-20 % with the temperature profile, which is one of
the reasons the solvers down-weight very low sun positions.

A time offset dt (stream-latency error) is a rotation about the Earth's axis by
``gha_rate * dt``: that is exactly equivalent to a longitude shift of the
same angle (0.25 deg of longitude per minute of time), which is why the
latency prior directly limits every astronomical longitude.
"""
from __future__ import annotations

import functools
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np

log = logging.getLogger("hordewatch.astro")

UTC = timezone.utc
AU_KM = 149597870.7
WGS84_A_KM = 6378.137
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)
SIDEREAL_RATE_DEG_S = 360.98564736629 / 86400.0


# ----------------------------------------------------------------------------- skyfield access
@functools.lru_cache(maxsize=1)
def _skyfield():
    """(timescale, ephemeris) from the bundled skyfield-data directory (no network)."""
    import skyfield_data
    from skyfield.api import Loader

    loader = Loader(skyfield_data.get_skyfield_data_path(), verbose=False)
    ts = loader.timescale(builtin=True)
    eph = loader("de421.bsp")
    return ts, eph


def available() -> bool:
    try:
        _skyfield()
        return True
    except Exception as e:  # pragma: no cover - only when the bundle is missing
        log.warning("astro: skyfield / skyfield-data not usable (%s)", e)
        return False


def _as_datetimes(times):
    if isinstance(times, datetime):
        times = [times]
    out = []
    for t in times:
        if isinstance(t, (int, float, np.floating, np.integer)):
            t = datetime.fromtimestamp(float(t), UTC)
        elif t.tzinfo is None:
            t = t.replace(tzinfo=UTC)
        out.append(t)
    return out


def sf_time(times):
    """skyfield Time (vector) for datetimes or unix seconds."""
    ts, _ = _skyfield()
    return ts.from_datetimes(_as_datetimes(times))


def unix(times) -> np.ndarray:
    return np.array([t.timestamp() for t in _as_datetimes(times)], float)


# ----------------------------------------------------------------------------- apparent places
@dataclass
class Places:
    """Apparent geocentric places of one body (or of many stars at one epoch).

    All arrays have the same length.  ``gha_rate`` is dGHA/dt in deg/s (15.04 for
    stars, ~15.00 for the Sun, ~14.5 for the Moon), used for the latency nuisance.
    """
    t_unix: np.ndarray
    ra_deg: np.ndarray
    dec_deg: np.ndarray
    dist_km: np.ndarray
    gast_deg: np.ndarray
    gha_rate: np.ndarray

    @property
    def gha_deg(self):
        return (self.gast_deg - self.ra_deg) % 360.0

    def e_ef(self):
        return earth_fixed_unit(self.gha_deg, self.dec_deg)

    def __len__(self):
        return len(self.ra_deg)


def _radec(body, t):
    _, eph = _skyfield()
    ra, dec, dist = eph["earth"].at(t).observe(body).apparent().radec(epoch="date")
    return np.atleast_1d(ra._degrees), np.atleast_1d(dec.degrees), np.atleast_1d(dist.km)


def body_places(body: str, times) -> Places:
    """Apparent places of 'sun' or 'moon' at a list of datetimes / unix seconds."""
    _, eph = _skyfield()
    target = eph[{"sun": "sun", "moon": "moon"}[body]]
    dts = _as_datetimes(times)
    t = sf_time(dts)
    ra, dec, dist = _radec(target, t)
    gast = np.atleast_1d(t.gast) * 15.0
    t2 = sf_time([d + timedelta(seconds=60) for d in dts])
    ra2, _, _ = _radec(target, t2)
    gast2 = np.atleast_1d(t2.gast) * 15.0
    rate = (((gast2 - ra2) - (gast - ra) + 180.0) % 360.0 - 180.0) / 60.0
    return Places(unix(dts), ra, dec, dist, gast, rate)


def star_places(ra_deg, dec_deg, pm_ra_mas=None, pm_dec_mas=None, when=None) -> Places:
    """Apparent places (of date) of catalogue stars (ICRS/J2000, epoch J2000) at one epoch.

    pm_ra_mas is mu_alpha* (already multiplied by cos dec), as in Hipparcos/HYG.
    """
    from skyfield.api import Star

    ra_deg = np.asarray(ra_deg, float)
    dec_deg = np.asarray(dec_deg, float)
    kw = {}
    if pm_ra_mas is not None:
        kw["ra_mas_per_year"] = np.nan_to_num(np.asarray(pm_ra_mas, float))
        kw["dec_mas_per_year"] = np.nan_to_num(np.asarray(pm_dec_mas, float))
    star = Star(ra_hours=ra_deg / 15.0, dec_degrees=dec_deg, **kw)
    (dt,) = _as_datetimes([when])
    ts, eph = _skyfield()
    t = ts.from_datetime(dt)
    ra, dec, _ = eph["earth"].at(t).observe(star).apparent().radec(epoch="date")
    n = len(ra_deg)
    return Places(np.full(n, dt.timestamp()), np.atleast_1d(ra._degrees), np.atleast_1d(dec.degrees),
                  np.full(n, np.inf), np.full(n, float(t.gast) * 15.0), np.full(n, SIDEREAL_RATE_DEG_S))


def gast_deg(times) -> np.ndarray:
    return np.atleast_1d(sf_time(times).gast) * 15.0


# ----------------------------------------------------------------------------- geometry
def earth_fixed_unit(gha_deg, dec_deg):
    g = np.radians(np.asarray(gha_deg, float))
    d = np.radians(np.asarray(dec_deg, float))
    return np.stack([np.cos(d) * np.cos(g), -np.cos(d) * np.sin(g), np.sin(d)], axis=-1)


def rotate_gha(e_ef, delta_deg):
    """Advance the Greenwich hour angle of Earth-fixed unit vectors by delta (deg)."""
    a = np.radians(delta_deg)
    c, s = np.cos(a), np.sin(a)
    x, y, z = e_ef[..., 0], e_ef[..., 1], e_ef[..., 2]
    xr, yr = x * c + y * s, y * c - x * s
    return np.stack([xr, yr, np.broadcast_to(z, xr.shape)], axis=-1)


def observer_frame(lat_deg, lon_deg, height_m=0.0):
    """WGS84 geocentric position (km, shape (...,3)) and ENU basis T (...,3,3) with rows E, N, U."""
    lat = np.radians(np.asarray(lat_deg, float))
    lon = np.radians(np.asarray(lon_deg, float))
    h = np.asarray(height_m, float) / 1000.0
    sl, cl, so, co = np.sin(lat), np.cos(lat), np.sin(lon), np.cos(lon)
    n = WGS84_A_KM / np.sqrt(1.0 - WGS84_E2 * sl ** 2)
    r = np.stack([(n + h) * cl * co, (n + h) * cl * so, (n * (1 - WGS84_E2) + h) * sl], axis=-1)
    east = np.stack([-so, co, np.zeros_like(so)], axis=-1)
    north = np.stack([-sl * co, -sl * so, cl], axis=-1)
    up = np.stack([cl * co, cl * so, sl], axis=-1)
    return r, np.stack([east, north, up], axis=-2)


def refraction_deg(alt_true_deg, pressure_mbar=1010.0, temp_c=10.0):
    """Saemundsson refraction (deg) to add to a true altitude; smooth and ~0 far below the horizon."""
    h = np.maximum(np.asarray(alt_true_deg, float), -1.5)
    r_arcmin = 1.02 / np.tan(np.radians(h + 10.3 / (h + 5.11)))
    r = r_arcmin / 60.0 * (pressure_mbar / 1010.0) * (283.0 / (273.0 + temp_c))
    # fade out below -1 deg (object invisible anyway) and above 89.9 deg
    fade = np.clip((np.asarray(alt_true_deg, float) + 2.0) / 1.0, 0.0, 1.0)
    return np.where(np.asarray(alt_true_deg) > 89.9, 0.0, r * fade)


def topocentric_enu(e_ef, dist_km, r_obs, T):
    """Unit topocentric ENU vectors.

    e_ef: (..., N, 3) Earth-fixed unit vectors; dist_km: (N,) (inf for stars);
    r_obs: (C, 3); T: (C, 3, 3).  Returns (C, N, 3).
    """
    e_ef = np.asarray(e_ef, float)
    dist = np.asarray(dist_km, float)
    inv = np.where(np.isfinite(dist), 1.0 / np.where(np.isfinite(dist), dist, 1.0), 0.0)
    v = e_ef[None] if e_ef.ndim == 2 else e_ef                # (C|1, N, 3)
    v = v - r_obs[:, None, :] * inv[None, :, None]
    enu = np.einsum("cij,cnj->cni", T, v)
    return enu / np.linalg.norm(enu, axis=-1, keepdims=True)


def apply_refraction(enu, pressure_mbar=1010.0, temp_c=10.0, scale=1.0):
    """Lift unit ENU vectors by atmospheric refraction (apparent direction).

    scale multiplies the standard refraction (a nuisance parameter in the solvers: real
    refraction near the horizon deviates from any formula by 5-20 %); it broadcasts
    against enu[..., 0].
    """
    u = np.clip(enu[..., 2], -1.0, 1.0)
    alt = np.degrees(np.arcsin(u))
    alt_app = np.radians(alt + scale * refraction_deg(alt, pressure_mbar, temp_c))
    hor = np.hypot(enu[..., 0], enu[..., 1])
    k = np.cos(alt_app) / np.maximum(hor, 1e-12)
    return np.stack([enu[..., 0] * k, enu[..., 1] * k, np.sin(alt_app)], axis=-1)


def enu_to_altaz(enu):
    az = np.degrees(np.arctan2(enu[..., 0], enu[..., 1])) % 360.0
    alt = np.degrees(np.arctan2(enu[..., 2], np.hypot(enu[..., 0], enu[..., 1])))
    return az, alt


def altaz_to_enu(az_deg, alt_deg):
    az, alt = np.radians(az_deg), np.radians(alt_deg)
    return np.stack([np.cos(alt) * np.sin(az), np.cos(alt) * np.cos(az), np.sin(alt)], axis=-1)


def altaz_grid(places: Places, lats, lons, height_m=0.0, refraction=False, pressure_mbar=1010.0, temp_c=10.0):
    """(az, alt) arrays of shape (C, N) for C sites (lats/lons 1-D, same length) and N places."""
    r, T = observer_frame(np.ravel(lats), np.ravel(lons), height_m)
    enu = topocentric_enu(places.e_ef(), places.dist_km, r, T)
    if refraction:
        enu = apply_refraction(enu, pressure_mbar, temp_c)
    return enu_to_altaz(enu)
