"""Astronomical location evidence: camera observations -> lat/lon likelihood grids.

Methods (each written as data/hordewatch/layers/astro_<method>.npz for
hordejakt.layers.live, plus an ``astro_fix`` Observation):

* sun_track - ``sun_pixel`` positions over hours/days;
* moon      - ``moon_pixel`` positions (topocentric: parallax up to ~1 deg);
* stars     - ``star_field`` point sources identified with catalogue stars
              (stars.py: built-in triangle matcher or astrometry.net);
* twilight  - dusk/dawn brightness threshold crossings (twilight.py);
* shadow    - cast-shadow directions on level ground (optional helper).

Celestial fits (sun / moon / stars): profile likelihood with a batched Levenberg-Marquardt
---------------------------------------------------------------------------------------------
For every candidate site x (a coarse grid, default 0.1 deg x 0.2 deg over the
engine domain) we minimise over the camera parameters

    chi2(x) = sum_i |pix_i - P(cam, dt; body_i(t_i + dt) seen from x)|^2 / sigma_px^2
            + level-reference terms (pitch/roll priors, plumb lines)
            + (dt / sigma_latency)^2 + weak intrinsic priors

where cam = heading, pitch, roll per pose segment, focal length f (and optional
principal point / radial k1), and dt is the stream-latency error.  The body's
apparent place comes from ephem.py (refraction included), so the model is exact
up to detection noise.  log L(x) = -chi2(x)/2 is the profile likelihood; the
pixel noise sigma_px is learned from the residuals of the best fit (shrunk
towards a 2-px prior, floored at 0.5 px) and outliers (flares, reflections,
mis-detections) beyond ~4 sigma are rejected at the global fit.

Efficiency: all cells are solved *simultaneously* (numpy arrays of shape
cells x points, finite-difference Jacobians, per-cell damping), in chunks.
They are warm-started exactly: a reference fit at one site gives the camera's
Earth-fixed orientation G = R_cam T(x0); at any other site the attitude that
reproduces the same pixels is R_cam(x) = G T(x)^T (see camera.py), so LM only
has to trade the latency and the level reference against each other.

Degeneracies (the important part - read camera.py):
* heading <-> longitude through time: a clock error dt, a longitude change and
  a camera pan are all rotations; over a short arc they are indistinguishable.
* pitch <-> latitude: tilting the camera moves the zenith in the image exactly
  like moving the site along the viewing azimuth.
* In fact with heading, pitch *and* roll free the degeneracy is exact for any
  amount of data: sun/star/moon positions only fix G (3 numbers).  Multi-day
  and long-window data make G, f and distortion extremely precise, separate the
  latency (the Sun's RA advance of ~1 deg/day is *not* a rotation of the
  sky about the pole) and expose camera bumps, but the site comes out of the
  level reference: 1 deg of pitch/roll error = 111 km.  Hence the layers
  report the reference they used, and sun_track / moon / stars share the
  independence group ``astro_attitude`` (they all lean on the same level
  reference; summing them would count it three times).  Twilight does not need
  a level reference and is independent (``astro_twilight``).
* The default reference is weak (roll 0 +- 3 deg, pitch 0 +- 15 deg: cameras
  are usually installed with a level horizon, pitch arbitrary), so without
  plumb lines (``camera_vertical``) or a configured calibration the celestial
  layers are broad ridges along the viewing azimuth - which is the truth.

Camera jumps: points are grouped into sessions (gaps > 3 h) and each session's
orientation is fitted with the intrinsics held at the global fit (a per-session
focal length lets a short cloudy-day arc fake a 1-deg 'jump').  A change larger
than ``jump_deg`` (0.3 deg) that is also significant given both sessions'
covariances (Mahalanobis d^2 > ``jump_chi2``), or a timestamp in ``camera_moves``,
starts a new pose segment with its own attitude (shared intrinsics).  Detection
runs on all input points, before the single-pose outlier rejection that would
otherwise discard a briefly seen bumped pose as 'outliers'.  A level calibration
(``camera_attitude``) constrains only the pose in force when it was stored (or
at its ``ts``); the other poses keep the weak default prior.

Input hygiene: non-finite pixels / angles / luma are dropped; manually or
automatically marked lines of one kind are capped in their *combined* level
information (``vertical_floor_deg``: correlated tree leans, detector bias and
lens distortion do not average down like sqrt(N)); degenerate families of level
edges (all in one plane through the camera) are ignored.
"""
from __future__ import annotations

import json
import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from ..analyzers.base import Analyzer
from ..types import Observation, parse_iso
from . import ephem
from .camera import (attitude_from_rotation, ground_direction_azimuth, horizontal_family_residuals, project,
                     rotation_angle_deg, rotation_matrix, vertical_residuals)

log = logging.getLogger("hordewatch.astro")
UTC = timezone.utc

DOMAIN = (58.0, 64.5, 4.5, 13.5)
KM_PER_DEG_LAT = 110.57
WEAK_PITCH = (0.0, 15.0)        # default level prior: cameras are mounted with a level horizon, pitch arbitrary
WEAK_ROLL = (0.0, 3.0)


# ============================================================================ data containers
@dataclass
class CelestialPoints:
    """Pixel observations of bodies with known apparent places.

    X, Y: pixel coordinates relative to the image centre, divided by the image width
    (resolution independent).  scale: image width in px (to express residuals in px).
    e_ef: Earth-fixed unit vectors at the observation time; dist_km: inf for stars;
    rate: dGHA/dt (deg/s) for the latency nuisance; seg: pose segment index.
    """
    X: np.ndarray
    Y: np.ndarray
    scale: np.ndarray
    e_ef: np.ndarray
    dist_km: np.ndarray
    rate: np.ndarray
    t: np.ndarray
    seg: np.ndarray
    body: np.ndarray
    weight: np.ndarray

    def __len__(self):
        return len(self.X)

    def subset(self, m):
        return CelestialPoints(*(getattr(self, k)[m] for k in self.__dataclass_fields__))

    @classmethod
    def concat(cls, items):
        items = [i for i in items if i is not None and len(i)]
        return cls(*(np.concatenate([getattr(i, k) for i in items]) for k in cls.__dataclass_fields__))

    @classmethod
    def from_places(cls, places, x_px, y_px, width, height, body, weight=None):
        x_px, y_px = np.asarray(x_px, float), np.asarray(y_px, float)
        w = np.broadcast_to(np.asarray(width, float), x_px.shape).astype(float)
        h = np.broadcast_to(np.asarray(height, float), x_px.shape).astype(float)
        n = len(x_px)
        return cls(X=x_px / w - 0.5, Y=(y_px - 0.5 * h) / w, scale=w, e_ef=places.e_ef(), dist_km=places.dist_km,
                   rate=places.gha_rate, t=places.t_unix, seg=np.zeros(n, int), body=np.array([body] * n),
                   weight=np.ones(n) if weight is None else np.asarray(weight, float))


@dataclass
class LevelReference:
    """What ties the camera to gravity.  (mean, sigma) tuples in degrees or None.

    segments: plumb lines in centred width units [x1, y1, x2, y2] (see CelestialPoints),
    seg_sigma: per-line lean sigma (radians), seg_t: unix time of the frame (-> pose segment).
    """
    pitch: tuple | None = (0.0, 15.0)
    roll: tuple | None = (0.0, 3.0)
    heading: tuple | None = None
    segments: np.ndarray = field(default_factory=lambda: np.zeros((0, 4)))
    seg_sigma: np.ndarray = field(default_factory=lambda: np.zeros(0))
    seg_t: np.ndarray = field(default_factory=lambda: np.zeros(0))
    seg_pose: np.ndarray = field(default_factory=lambda: np.zeros(0, int))
    source: str = "default level prior (roll 0+-3, pitch 0+-15 deg)"
    # families of world-horizontal parallel segments: list of (segments (k,4), sigma_rad, unix t)
    families: list = field(default_factory=list)
    # unix time at which the pitch/roll/heading priors were measured (e.g. when a camera_attitude calibration
    # was stored).  With several pose segments (camera bumped) the priors then apply only to the segment
    # in force at that time; the others get the weak default prior.  None: the priors hold for every segment.
    att_t: float | None = None

    @property
    def n_lines(self):
        return len(self.segments)

    @property
    def n_terms(self):
        return len(self.segments) + len(self.families)

    def strength_deg(self):
        """Rough 1-sigma of the zenith direction implied by the reference (deg), reported in the layer
        metadata / astro_fix as ``level_sigma_deg`` (x 111 km = the expected size of the fix)."""
        sp = self.pitch[1] if self.pitch else 90.0
        sr = self.roll[1] if self.roll else 90.0
        if len(self.families) >= 2:
            s_f = float(np.degrees(np.sqrt(1.0 / np.sum([1.0 / fam[1] ** 2 for fam in self.families]))))
            sp = 1.0 / np.sqrt(1.0 / sp ** 2 + 1.0 / s_f ** 2)
            sr = 1.0 / np.sqrt(1.0 / sr ** 2 + 1.0 / s_f ** 2)
        if self.n_lines:
            s_line = float(np.degrees(np.sqrt(1.0 / np.sum(1.0 / self.seg_sigma ** 2))))
            sr = 1.0 / np.sqrt(1.0 / sr ** 2 + 1.0 / s_line ** 2)
            sp = 1.0 / np.sqrt(1.0 / sp ** 2 + 1.0 / (3.0 * s_line) ** 2)   # pitch from convergence: weaker
        return float(np.hypot(sp, sr))


@dataclass
class FitOptions:
    f0: float = 0.78                  # focal length / width (HFOV ~65 deg); prior centre + init
    lnf_sigma: float = 0.7
    fit_center: bool = False
    center_sigma: float = 0.03
    fit_k1: bool = False
    k1_sigma: float = 0.15
    dt_sigma_s: float = 15.0
    pixel_sigma_prior: float = 2.0
    pixel_sigma_floor: float = 0.5
    height_m: float = 500.0
    pressure_mbar: float = 955.0
    temp_c: float = 8.0
    refraction: bool = True
    max_iter: int = 10
    chunk: int = 256
    jump_deg: float = 0.3              # a pose jump must rotate the camera by more than this ...
    jump_chi2: float = 30.0            # ... AND be significant: Mahalanobis d^2 (3 dof; 30 ~ p 1e-6)
    session_gap_h: float = 3.0
    reject_k: float = 4.0
    refraction_sigma: float = 0.10     # prior on the refraction scale factor (nuisance, fitted per site)
    refraction_model_err: float = 0.05 # uncorrelated refraction error per point (fraction of R) high up ...
    refraction_horizon_err: float = 0.25  # ... growing to +0.25 at the horizon (e-folding 2 deg): night inversions


class Layout:
    """Parameter vector layout: [psi, theta, phi] per pose segment, ln f, dt, (dcx, dcy), (k1), (refraction scale)."""

    def __init__(self, S, fit_dt=True, fit_center=False, fit_k1=False, fit_kr=False):
        self.S = S
        i = 3 * S
        self.lnf = i
        i += 1
        self.dt = i if fit_dt else None
        i += int(fit_dt)
        self.cx = i if fit_center else None
        self.cy = i + 1 if fit_center else None
        i += 2 * int(fit_center)
        self.k1 = i if fit_k1 else None
        i += int(fit_k1)
        self.kr = i if fit_kr else None
        i += int(fit_kr)
        self.P = i
        st = np.full(i, 1e-4)
        st[self.lnf] = 1e-6
        if self.dt is not None:
            st[self.dt] = 0.05
        for k in (self.cx, self.cy):
            if k is not None:
                st[k] = 1e-6
        if self.k1 is not None:
            st[self.k1] = 1e-5
        if self.kr is not None:
            st[self.kr] = 1e-4
        self.steps = st


def batched_lm(fun, p0, steps, n_iter=10, lam0=1e-3):
    """Levenberg-Marquardt on many independent problems at once. fun: (C,P) -> (C,M) residuals."""
    p = np.array(p0, float)
    r = fun(p)
    cost = np.sum(r * r, axis=1)
    C, P = p.shape
    lam = np.full(C, lam0)
    eye = np.eye(P)[None]
    for it in range(n_iter):
        J = np.empty((C, r.shape[1], P))
        for j in range(P):
            q = p.copy()
            q[:, j] += steps[j]
            J[:, :, j] = (fun(q) - r) / steps[j]
        A = np.einsum("cmi,cmj->cij", J, J)
        g = np.einsum("cmi,cm->ci", J, r)
        D = np.maximum(np.einsum("cii->ci", A), 1e-12)
        M = A + lam[:, None, None] * D[:, :, None] * eye
        try:
            dp = -np.linalg.solve(M, g[..., None])[..., 0]
        except np.linalg.LinAlgError:
            dp = -np.linalg.lstsq(M.reshape(-1, P), g.reshape(-1), rcond=None)[0].reshape(C, P)
        q = p + dp
        rq = fun(q)
        cq = np.sum(rq * rq, axis=1)
        acc = np.isfinite(cq) & (cq < cost)
        gain = np.where(acc, (cost - cq) / np.maximum(cost, 1e-12), 0.0)
        p[acc], r[acc], cost[acc] = q[acc], rq[acc], cq[acc]
        lam = np.clip(np.where(acc, lam * 0.3, lam * 8.0), 1e-9, 1e9)
        if it >= 2 and np.all(gain < 1e-8):
            break
    return p, cost, r


@dataclass
class RefFit:
    p: np.ndarray
    lay: Layout
    G: list
    sigma_px: float
    rms_px: float
    n: int
    n_rejected: int
    lat0: float
    lon0: float
    jumps: list = field(default_factory=list)


class CelestialFitter:
    """Fits camera + site to CelestialPoints; see module docstring."""

    def __init__(self, pts: CelestialPoints, level: LevelReference | None = None, opts: FitOptions | None = None):
        import dataclasses
        self.pts = pts
        self.pts_input = pts                          # before any outlier rejection (jump detection uses it)
        # private copy: the pose-segment assignment of plumb lines is fitter specific
        self.level = dataclasses.replace(level) if level is not None else LevelReference()
        self.o = opts or FitOptions()
        self.sigma_px = self.o.pixel_sigma_prior
        self.model_var = np.zeros(len(pts))           # extra per-point variance (px^2), e.g. refraction
        self._update_segments()

    def _update_segments(self):
        self.S = int(self.pts.seg.max()) + 1 if len(self.pts) else 1
        lev = self.level
        if lev.n_lines:
            lev.seg_pose = self._pose_of_time(lev.seg_t)

    def _pose_of_time(self, t):
        """Pose segment of arbitrary times: segment of the nearest earlier point (or first)."""
        order = np.argsort(self.pts.t)
        ts, segs = self.pts.t[order], self.pts.seg[order]
        k = np.clip(np.searchsorted(ts, np.asarray(t, float), side="right") - 1, 0, len(ts) - 1)
        return segs[k].astype(int)

    def layout(self, fit_dt=True, fit_kr=None):
        fit_kr = (self.o.refraction and self.o.refraction_sigma > 0) if fit_kr is None else fit_kr
        return Layout(self.S, fit_dt, self.o.fit_center, self.o.fit_k1, fit_kr)

    # ------------------------------------------------------------------ model
    def _intr(self, p, lay):
        C = p.shape[0]
        f = np.exp(p[:, lay.lnf])
        cx = p[:, lay.cx] if lay.cx is not None else np.zeros(C)
        cy = p[:, lay.cy] if lay.cy is not None else np.zeros(C)
        k1 = p[:, lay.k1] if lay.k1 is not None else np.zeros(C)
        return f, cx, cy, k1

    def predict(self, p, lay, r_obs, T, pts=None):
        pts = self.pts if pts is None else pts
        e = pts.e_ef[None]
        if lay.dt is not None:
            e = ephem.rotate_gha(e, pts.rate[None] * p[:, lay.dt, None])
        enu = ephem.topocentric_enu(e, pts.dist_km, r_obs, T)
        if self.o.refraction:
            kr = p[:, lay.kr, None] if lay.kr is not None else 1.0
            enu = ephem.apply_refraction(enu, self.o.pressure_mbar, self.o.temp_c, kr)
        f, cx, cy, k1 = self._intr(p, lay)
        C, N = p.shape[0], len(pts)
        X = np.empty((C, N))
        Y = np.empty((C, N))
        front = np.empty((C, N), bool)
        for s in range(lay.S):
            m = pts.seg == s
            if not m.any():
                continue
            R = rotation_matrix(p[:, 3 * s], p[:, 3 * s + 1], p[:, 3 * s + 2])
            c = np.einsum("cij,cnj->cni", R, enu[:, m])
            X[:, m], Y[:, m], front[:, m] = project(c, f[:, None], cx[:, None], cy[:, None], k1[:, None])
        return X, Y, front

    def residuals(self, p, lay, r_obs, T, attitude_priors=True, verticals=True):
        pts = self.pts
        X, Y, front = self.predict(p, lay, r_obs, T)
        w = pts.scale * np.sqrt(pts.weight) / np.sqrt(self.sigma_px ** 2 + self.model_var)
        rx = np.where(front, (X - pts.X) * w, 1e3)
        ry = np.where(front, (Y - pts.Y) * w, 1e3)
        parts = [rx, ry, self._prior_res(p, lay, attitude_priors)]
        if verticals and self.level.n_terms:
            parts.append(self._vert_res(p, lay))
        return np.concatenate(parts, axis=1)

    def _prior_res(self, p, lay, attitude_priors):
        o, lev = self.o, self.level
        cols = [(p[:, lay.lnf] - np.log(o.f0)) / o.lnf_sigma]
        if lay.dt is not None:
            cols.append(p[:, lay.dt] / max(o.dt_sigma_s, 0.5))
        for k in (lay.cx, lay.cy):
            if k is not None:
                cols.append(p[:, k] / o.center_sigma)
        if lay.k1 is not None:
            cols.append(p[:, lay.k1] / o.k1_sigma)
        if lay.kr is not None:
            cols.append((p[:, lay.kr] - 1.0) / o.refraction_sigma)
        if attitude_priors:
            s_meas = None
            if lev.att_t is not None and lay.S > 1 and len(self.pts):
                s_meas = int(self._pose_of_time(np.array([lev.att_t]))[0])
            for s in range(lay.S):
                if s_meas is None or s == s_meas:
                    pitch, roll, heading = lev.pitch, lev.roll, lev.heading
                else:
                    # the calibration describes another pose of the camera: only the weak default applies
                    pitch, roll, heading = WEAK_PITCH, WEAK_ROLL, None
                if pitch:
                    cols.append((p[:, 3 * s + 1] - pitch[0]) / pitch[1])
                if roll:
                    cols.append((p[:, 3 * s + 2] - roll[0]) / roll[1])
                if heading:
                    cols.append(((p[:, 3 * s] - heading[0] + 180.0) % 360.0 - 180.0) / heading[1])
        return np.stack(cols, axis=1)

    def _vert_res(self, p, lay):
        """Level-reference residuals: plumb lines, then horizontal families (pose by time)."""
        lev = self.level
        f, cx, cy, k1 = self._intr(p, lay)
        out = np.zeros((p.shape[0], lev.n_terms))
        Rs = [rotation_matrix(p[:, 3 * s], p[:, 3 * s + 1], p[:, 3 * s + 2]) for s in range(lay.S)]
        for s in range(lay.S):
            m = lev.seg_pose == s
            if m.any():
                out[:, :lev.n_lines][:, m] = vertical_residuals(lev.segments[m], Rs[s], f, cx, cy, k1) / lev.seg_sigma[m]
        if lev.families:
            poses = self._pose_of_time(np.array([fam[2] for fam in lev.families], float))
            for k, (segs, sig, _) in enumerate(lev.families):
                out[:, lev.n_lines + k] = horizontal_family_residuals(segs, Rs[min(int(poses[k]), lay.S - 1)], f, cx, cy, k1) / sig
        return out

    # ------------------------------------------------------------------ reference fit
    def _starts(self, lat0, lon0, init=None):
        pts, o = self.pts, self.o
        r, T = ephem.observer_frame(np.array([lat0]), np.array([lon0]), o.height_m)
        enu = ephem.apply_refraction(ephem.topocentric_enu(pts.e_ef, pts.dist_km, r, T)[0])
        lay = self.layout(fit_dt=False, fit_kr=False)
        starts = []
        fmuls = (0.6, 0.8, 1.0, 1.3, 1.8)
        for fm in fmuls:
            f = o.f0 * fm
            for roll in (-6.0, 0.0, 6.0):
                p = np.zeros(lay.P)
                p[lay.lnf] = np.log(f)
                for s in range(self.S):
                    m = pts.seg == s
                    if not m.any():
                        continue
                    # least-squares boresight: rotate the mean ray so the mean pixel lands right
                    az = np.degrees(np.arctan2(enu[m, 0], enu[m, 1]))
                    alt = np.degrees(np.arcsin(np.clip(enu[m, 2], -1, 1)))
                    az_m = np.degrees(np.arctan2(np.mean(np.sin(np.radians(az))), np.mean(np.cos(np.radians(az)))))
                    p[3 * s] = (az_m - np.degrees(np.arctan(np.mean(pts.X[m]) / f))) % 360.0
                    p[3 * s + 1] = np.mean(alt) + np.degrees(np.arctan(np.mean(pts.Y[m]) / f))
                    p[3 * s + 2] = roll
                starts.append(p)
        if init is not None:
            for p in init:
                starts.append(np.asarray(p, float)[: lay.P])
        return np.array(starts), lay, r, T

    def fit_reference(self, lat0, lon0, init=None, reject=True) -> RefFit:
        """Data-only fit at one site: the camera's Earth-fixed orientation G and intrinsics."""
        o = self.o
        n0 = len(self.pts)
        p_best = None
        self.model_var = 0.0                                     # set from the fitted geometry below
        for rnd in range(4):
            P0, lay, r, T = self._starts(lat0, lon0, init if p_best is None else [p_best])
            C = len(P0)
            rr, TT = np.repeat(r, C, 0), np.repeat(T, C, 0)
            self.sigma_px = o.pixel_sigma_prior

            def fun(p):
                return self.residuals(p, lay, rr, TT, attitude_priors=False, verticals=False)

            P, cost, res = batched_lm(fun, P0, lay.steps, n_iter=30 if rnd == 0 else 15)
            k = int(np.argmin(cost))
            p_best = P[k]
            N = len(self.pts)
            rx, ry = res[k, :N] * o.pixel_sigma_prior, res[k, N:2 * N] * o.pixel_sigma_prior
            if not reject or N < 8 or rnd == 3:
                break
            norm = np.hypot(rx, ry)
            sig_r = max(np.median(norm) / 1.1774, 0.3)            # Rayleigh median -> sigma
            bad = norm > max(o.reject_k * sig_r, 3.0 * o.pixel_sigma_floor)
            if not bad.any() or bad.sum() > 0.4 * N:
                break
            self.pts = self.pts.subset(~bad)                     # refit without the outliers
            self._update_segments()
        N = len(self.pts)
        rss = float(np.sum(rx ** 2 + ry ** 2))
        dof = max(2 * N - lay.P, 1)
        s2 = rss / dof
        nu0 = 6.0
        sig = float(np.sqrt((dof * s2 + nu0 * o.pixel_sigma_prior ** 2) / (dof + nu0)))
        self.sigma_px = max(sig, o.pixel_sigma_floor)
        G = [rotation_matrix(p_best[3 * s], p_best[3 * s + 1], p_best[3 * s + 2]) @ T[0] for s in range(self.S)]
        self.model_var = self._model_var(self.pts, p_best[lay.lnf], r, T)
        return RefFit(p=p_best, lay=lay, G=G, sigma_px=self.sigma_px, rms_px=float(np.sqrt(rss / max(N, 1))),
                      n=N, n_rejected=n0 - N, lat0=lat0, lon0=lon0)

    def _model_var(self, pts, lnf, r, T):
        """Extra per-point variance (px^2) for uncorrelated refraction error (anomalous refraction near the
        horizon: refraction_model_err of R high up, growing by refraction_horizon_err with e-folding 2 deg)."""
        o = self.o
        if not o.refraction or not len(pts):
            return np.zeros(len(pts))
        enu = ephem.topocentric_enu(pts.e_ef, pts.dist_km, r, T)[0]
        alt = np.degrees(np.arcsin(np.clip(enu[:, 2], -1, 1)))
        frac = o.refraction_model_err + o.refraction_horizon_err * np.exp(-np.maximum(alt, 0.0) / 2.0)
        err_rad = np.radians(frac * ephem.refraction_deg(alt, o.pressure_mbar, o.temp_c))
        return (err_rad * np.exp(lnf) * pts.scale) ** 2

    def _session_attitude(self, ref: RefFit, sub: CelestialPoints):
        """Attitude-only fit of one session's points at the reference site, intrinsics held at the global fit.

        Returns (angles (3,) deg [heading, pitch, roll], covariance (3, 3) deg^2, reduced chi2) or None.
        The covariance comes from the Gauss-Newton normal matrix with the globally learned pixel sigma
        and is inflated by the session's reduced chi2 when that exceeds 1 (a session with correlated
        errors - flare, partial occlusion - must not look more precise than it is).  Points beyond
        reject_k sigma of the session's own fit (flares) are dropped once and the fit repeated.

        Why the intrinsics are fixed: refitting f per session lets a short arc (a cloudy day with 30 min
        of sun) trade focal length against roll and pointing, which fakes 0.5-1.5 deg 'jumps' of a camera
        that never moved.  A real bump changes the attitude, not the lens.
        """
        o = self.o
        sub = sub.subset(np.ones(len(sub), bool))            # private copy
        if len(sub) < 6:
            return None
        lay1 = Layout(1, fit_dt=False, fit_center=o.fit_center, fit_k1=o.fit_k1, fit_kr=False)
        s = int(np.bincount(np.clip(sub.seg.astype(int), 0, ref.lay.S - 1)).argmax())
        base = np.r_[ref.p[3 * s:3 * s + 3], ref.p[ref.lay.lnf:ref.lay.P]]
        if len(base) != lay1.P:
            return None
        sub.seg = np.zeros(len(sub), int)
        r, T = ephem.observer_frame(np.array([ref.lat0]), np.array([ref.lon0]), o.height_m)
        q = base[None, :3].copy()
        for rnd in range(2):
            N = len(sub)
            w = sub.scale * np.sqrt(sub.weight) / np.sqrt(self.sigma_px ** 2 + self._model_var(sub, base[3], r, T))

            def fun(qq, sub=sub, w=w):
                p = np.repeat(base[None], len(qq), 0)
                p[:, :3] = qq
                X, Y, front = self.predict(p, lay1, np.repeat(r, len(qq), 0), np.repeat(T, len(qq), 0), pts=sub)
                return np.concatenate([np.where(front, (X - sub.X) * w, 1e3), np.where(front, (Y - sub.Y) * w, 1e3)], 1)

            q, cost, res = batched_lm(fun, q, np.full(3, 1e-4), n_iter=30)
            norm = np.hypot(res[0, :N], res[0, N:])
            bad = norm > o.reject_k
            if rnd == 1 or not bad.any() or bad.sum() > 0.4 * N or N - bad.sum() < 6:
                break
            sub = sub.subset(~bad)
        h = 1e-4
        r0 = fun(q)[0]
        J = np.stack([(fun(q + h * np.eye(3)[k][None])[0] - r0) / h for k in range(3)], axis=1)
        cov = np.linalg.pinv(J.T @ J)
        red = float(cost[0]) / max(2 * len(sub) - 3, 1)
        return q[0], cov * max(red, 1.0), red

    def detect_jumps(self, ref: RefFit, moves=(), pts=None):
        """Split into pose segments at known moves and at significant orientation changes between sessions.

        Sessions = runs of points without gaps > session_gap_h.  Each session's attitude is fitted with
        the intrinsics fixed (see _session_attitude) and compared with the previous fitted session: a new
        pose segment starts only when the rotation exceeds ``jump_deg`` *and* its Mahalanobis distance
        (both sessions' covariances) exceeds ``jump_chi2``.  Sessions too short to fit (< 6 points) join
        the pose in force at their time.

        pts: the points to segment; default *all* input points, including those the single-pose reference
        fit rejected: after a bump seen only briefly (a short cloudy session) the bumped points look like
        outliers to a one-pose fit and would otherwise vanish before the jump could be seen.  The returned
        segment array refers to these points.
        """
        o = self.o
        pts = self.pts_input if pts is None else pts
        order = np.argsort(pts.t)
        t = pts.t[order]
        session = np.concatenate([[0], np.cumsum(np.diff(t) > o.session_gap_h * 3600)])
        sess = np.empty(len(t), int)
        sess[order] = session
        mv = sorted(float(m) for m in moves)
        seg = np.searchsorted(np.array(mv), pts.t, side="right") if mv else np.zeros(len(pts), int)
        jumps = [{"t": m, "why": "configured camera move"} for m in mv]
        cur = None
        extra = 0
        seg_auto = np.zeros(len(pts), int)
        for s in range(session.max() + 1):                 # sessions are numbered in time order
            m = sess == s
            fit = self._session_attitude(ref, pts.subset(m))
            if fit is not None:
                ang, cov, _ = fit
                if cur is not None:
                    d = ang - cur[0]
                    d[0] = (d[0] + 180.0) % 360.0 - 180.0
                    d2 = float(d @ np.linalg.pinv(cov + cur[1]) @ d)
                    rot = float(rotation_angle_deg(rotation_matrix(*ang), rotation_matrix(*cur[0])))
                    if rot > o.jump_deg and d2 > o.jump_chi2:
                        extra += 1
                        jumps.append({"t": float(pts.t[m].min()),
                                      "why": f"orientation changed by {rot:.2f} deg (d2 {d2:.0f})"})
                cur = (ang, cov)
            seg_auto[m] = extra
        seg = seg + seg_auto
        _, seg = np.unique(seg, return_inverse=True)
        return seg, jumps

    # ------------------------------------------------------------------ profile over sites
    def profile(self, ref: RefFit, lats, lons):
        """chi2 (C,), fitted params (C,P), data-only chi2 (C,) at candidate sites."""
        o = self.o
        lats, lons = np.ravel(lats), np.ravel(lons)
        lay = self.layout(fit_dt=True)
        r, T = ephem.observer_frame(lats, lons, o.height_m)
        C = len(lats)
        p0 = np.zeros((C, lay.P))
        for s in range(self.S):
            R = np.einsum("ij,ckj->cik", ref.G[s], T)            # G T^T
            h, pt, rl = attitude_from_rotation(R)
            p0[:, 3 * s], p0[:, 3 * s + 1], p0[:, 3 * s + 2] = h, pt, rl
        p0[:, lay.lnf] = ref.p[ref.lay.lnf]
        for k_new, k_old in ((lay.cx, ref.lay.cx), (lay.cy, ref.lay.cy), (lay.k1, ref.lay.k1)):
            if k_new is not None:
                p0[:, k_new] = ref.p[k_old]
        if lay.kr is not None:
            p0[:, lay.kr] = 1.0
        chi2 = np.empty(C)
        chi2_data = np.empty(C)
        P = np.empty_like(p0)
        N = len(self.pts)
        for a in range(0, C, o.chunk):
            sl = slice(a, min(a + o.chunk, C))

            def fun(p, sl=sl):
                return self.residuals(p, lay, r[sl], T[sl])

            p, cost, res = batched_lm(fun, p0[sl], lay.steps, n_iter=o.max_iter)
            P[sl], chi2[sl] = p, cost
            chi2_data[sl] = np.sum(res[:, :2 * N] ** 2, axis=1)
        return chi2, P, chi2_data, lay


# ============================================================================ grids / layers
def _nanarg(a, fn=np.argmax):
    """argmax/argmin ignoring non-finite cells (np.argmax returns the first NaN)."""
    a = np.asarray(a, float)
    fill = -np.inf if fn is np.argmax else np.inf
    return int(fn(np.where(np.isfinite(a), a, fill)))


def coarse_grid(domain=DOMAIN, dlat=0.1, dlon=0.2):
    lats = np.arange(domain[0], domain[1] + 1e-9, dlat)
    lons = np.arange(domain[2], domain[3] + 1e-9, dlon)
    return lats, lons


def summarize(lats, lons, ll):
    """Location summary of a coarse log-likelihood grid (uniform prior per unit area)."""
    L, O = np.meshgrid(lats, lons, indexing="ij")
    fin = np.isfinite(ll)
    w = np.where(fin, np.exp(np.where(fin, ll, -np.inf) - np.nanmax(ll)), 0.0) * np.cos(np.radians(L))
    w = w / w.sum()
    i, j = np.unravel_index(np.nanargmax(np.where(fin, ll, -np.inf)), ll.shape)
    mlat, mlon = float((w * L).sum()), float((w * O).sum())
    y = (L - mlat) * KM_PER_DEG_LAT
    x = (O - mlon) * 111.32 * np.cos(np.radians(mlat))
    cov = np.array([[(w * x * x).sum(), (w * x * y).sum()], [(w * x * y).sum(), (w * y * y).sum()]])
    ev, evec = np.linalg.eigh(cov)
    ev = np.maximum(ev, 0.0)
    major = evec[:, 1]
    n = fin.sum()
    ent = -np.sum(w[w > 0] * np.log2(w[w > 0]))
    return {"lat": mlat, "lon": mlon, "lat_map": float(lats[i]), "lon_map": float(lons[j]),
            "sigma_km": float(np.sqrt(ev.sum() / 2.0)), "sigma_major_km": float(np.sqrt(ev[1])),
            "sigma_minor_km": float(np.sqrt(ev[0])),
            "major_axis_bearing_deg": float(np.degrees(np.arctan2(major[0], major[1])) % 180.0),
            "info_bits": float(np.log2(max(n, 1)) - ent)}


def write_layer(path, lats, lons, ll, meta):
    """Upsample a coarse loglik (len(lats) x len(lons)) to the hordejakt analysis grid and save.

    The file holds the sub-grid covering the coarse extent (full grid when the extent is the
    whole engine domain) with lat_min/lon_min/dlat/dlon, as hordejakt.layers.live expects.
    """
    from scipy.interpolate import RegularGridInterpolator

    from hordejakt.grid import GRID

    i0 = max(int(np.ceil((lats[0] - GRID.lat_min) / GRID.dlat - 1e-9)), 0)
    i1 = min(int(np.floor((lats[-1] - GRID.lat_min) / GRID.dlat + 1e-9)), GRID.nlat - 1)
    j0 = max(int(np.ceil((lons[0] - GRID.lon_min) / GRID.dlon - 1e-9)), 0)
    j1 = min(int(np.floor((lons[-1] - GRID.lon_min) / GRID.dlon + 1e-9)), GRID.nlon - 1)
    flats = GRID.lat_min + np.arange(i0, i1 + 1) * GRID.dlat
    flons = GRID.lon_min + np.arange(j0, j1 + 1) * GRID.dlon
    ll = np.asarray(ll, float)
    ll = ll - np.nanmax(ll)
    interp = RegularGridInterpolator((lats, lons), ll, bounds_error=False, fill_value=np.nan)
    FL, FO = np.meshgrid(flats, flons, indexing="ij")
    fine = interp(np.stack([FL, FO], -1)).astype(np.float32)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".partial")       # not matched by the engine's *.npz glob
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, loglik=fine, lat_min=float(flats[0]), lon_min=float(flons[0]), dlat=GRID.dlat,
                            dlon=GRID.dlon, meta=json.dumps(meta, ensure_ascii=False, default=float))
    tmp.replace(path)                                         # atomic: the engine never reads half a file
    return path


# ============================================================================ method runners
def solve_celestial(pts, level, opts, lats, lons, lat0, lon0, moves=(), init=None):
    """Full celestial pipeline on a coarse grid. Returns dict with ll (grid), ref, fitter, extras."""
    fitter = CelestialFitter(pts, level, opts)
    ref = fitter.fit_reference(lat0, lon0, init=init)
    seg, jumps = fitter.detect_jumps(ref, moves)               # over all input points: see detect_jumps
    if seg.max() > 0:
        allp = pts.subset(np.ones(len(pts), bool))
        allp.seg = seg
        fitter.pts = allp
        fitter._update_segments()
        ref = fitter.fit_reference(lat0, lon0)                  # per-pose fit, outliers judged per pose
    ref.jumps = jumps
    L, O = np.meshgrid(lats, lons, indexing="ij")
    chi2, P, chi2_data, lay = fitter.profile(ref, L.ravel(), O.ravel())
    # plumb-line outliers (branches, leaning trees): drop > 3.5 sigma at the best site and redo
    if fitter.level.n_lines >= 4 and np.isfinite(chi2).any():
        k = _nanarg(chi2, np.argmin)
        vr = fitter._vert_res(P[k:k + 1], lay)[0][:fitter.level.n_lines]
        bad = np.abs(vr) > 3.5
        if bad.any() and (~bad).sum() >= 3:
            import dataclasses
            lev = fitter.level
            fitter.level = dataclasses.replace(
                lev, segments=lev.segments[~bad], seg_sigma=lev.seg_sigma[~bad], seg_t=lev.seg_t[~bad],
                seg_pose=lev.seg_pose[~bad], source=lev.source + f"; {int(bad.sum())} lines rejected")
            chi2, P, chi2_data, lay = fitter.profile(ref, L.ravel(), O.ravel())
    ll = (-0.5 * chi2).reshape(L.shape)
    return {"ll": ll, "ref": ref, "fitter": fitter, "params": P.reshape(L.shape + (lay.P,)), "lay": lay,
            "chi2_data": chi2_data.reshape(L.shape)}


def celestial_reliability(method, n, rms_px, level: LevelReference, n_days=1, n_rejected=0, jumps=0):
    """Conservative reliabilities: P(the evidence model is right).

    sun_track 0.5-0.7 (n, span, fit quality); stars 0.8 with >= 8 identified stars; moon 0.5.
    A layer driven only by the default level prior is broad anyway, but its assumption
    (camera roughly level) can be wrong outright, so it gets x0.8.
    """
    if method == "sun_track":
        r = 0.5 + 0.1 * (n >= 30 and n_days >= 2) + 0.1 * (rms_px <= 3.0 and n_rejected <= 0.1 * max(n, 1))
        if rms_px > 8.0:
            r = 0.3
    elif method == "stars":
        r = 0.8 if n >= 8 else (0.6 if n >= 5 else 0.4)
        if rms_px > 3.0:
            r -= 0.2
    else:
        r = 0.5 if n >= 5 else 0.35
    if jumps:
        r -= 0.1
    if level.n_terms == 0 and "calibration" not in level.source and "config" not in level.source:
        r *= 0.8
    return float(np.clip(r, 0.1, 0.9))


def shadow_loglik(shadows, lats, lons, R_cells, f, width_units=True, sigma_deg=10.0, directed=False):
    """Cast-shadow directions on level ground -> sun azimuth -> site.

    shadows: list of dicts {t, x, y, angle_deg_image} in centred width units (see CelestialPoints).
    R_cells: (C, 3, 3) camera attitude per cell (e.g. from the sun-track profile, which ties the camera
    to the Earth) or (3, 3) fixed.  The shadow of a vertical object on level ground points to the
    anti-solar azimuth; with 'directed' False the 180-deg ambiguity of a line is kept.
    """
    lats, lons = np.ravel(lats), np.ravel(lons)
    C = len(lats)
    R_cells = np.broadcast_to(R_cells, (C, 3, 3))
    t = np.array([s["t"] for s in shadows], float)
    pl = ephem.body_places("sun", list(t))
    az, alt = ephem.altaz_grid(pl, lats, lons)
    obj = np.zeros(C)
    for i, s in enumerate(shadows):
        a_img, ok = ground_direction_azimuth(np.full(C, s["x"]), np.full(C, s["y"]), s["angle_deg_image"], R_cells,
                                             np.broadcast_to(f, (C,)), 0.0, 0.0)
        d = (a_img - (az[:, i] + 180.0) + 180.0) % 360.0 - 180.0
        if not directed:
            d = (d + 90.0) % 180.0 - 90.0
        z = d / (sigma_deg / max(s.get("strength", 1.0), 0.3) ** 0.5)
        z = np.where(ok & (alt[:, i] > 2.0), z, 3.0)            # sun down or ray above horizon: no support
        obj += 5.0 * np.log1p(z ** 2 / 4.0)                      # Student-t (nu = 4)
    return -0.5 * obj


# ============================================================================ the bridge
DEFAULTS = {
    "layers_dir": None,                 # -> hordejakt.layers.live.LIVE_DIR
    "domain": list(DOMAIN),
    "coarse_dlat": 0.1,
    "coarse_dlon": 0.2,
    "approx_site": [61.25, 9.0],
    "threaded": True,
    "tick_interval_s": 600,
    "min_new": {"sun_track": 6, "moon": 4, "stars": 1, "twilight": 1, "shadow": 3},
    "min_total": {"sun_track": 12, "moon": 6, "stars": 1, "twilight": 3, "shadow": 3},   # stars: frames
    "sun_bin_s": 120,
    "max_points": 400,                  # per celestial fit (cost ~ cells x points)
    "moon_bin_s": 300,
    "attitude": {"pitch_deg": 0.0, "pitch_sigma_deg": 15.0, "roll_deg": 0.0, "roll_sigma_deg": 3.0,
                 "heading_deg": None, "heading_sigma_deg": None},
    "vertical_sigma_deg": {"trunk": 1.5, "post": 0.5, "plumb": 0.15, "default": 1.5},
    # floor on the *combined* level information of all lines of one kind (correlated errors, see _level)
    "vertical_floor_deg": {"trunk": 0.5, "post": 0.25, "plumb": 0.05, "auto_lines": 1.0, "default": 0.5},
    "fit": {},
    "twilight": {"thresholds": [100.0, 50.0, 25.0, 12.0], "sigma_prior_min": 4.0, "sigma_floor_min": 1.0,
                 "asym_sigma_deg": 0.75, "ir_asym_sigma_deg": 1.5, "lookback_h": 40},
    "stars": {"vmax": 5.0, "max_frames": 12, "min_points": 5, "min_matched": 5},
    "shadow": {"sigma_deg": 10.0},
    "camera_moves": [],
    "auto_verticals": True,             # daily Hough plumb-line candidates from an archived daylight frame
    "auto_vertical_sigma_deg": 2.5,
}


def _finite(*vals):
    """True when every value is a finite number (JSON NaN / None / strings from a buggy analyzer are dropped)."""
    try:
        return all(v is not None and np.isfinite(float(v)) for v in vals)
    except (TypeError, ValueError):
        return False


def _family_degenerate(segs, f, min_ratio=1e-3):
    """True when the interpretation planes of a family of parallel edges (centred width units) are (nearly)
    one plane: the vanishing direction is then only confined to a plane and the level residual is arbitrary
    (e.g. two pieces of the same edge, or edges whose planes through the camera coincide).  Criterion: the
    middle eigenvalue of sum n n^T must exceed min_ratio x the largest (~2 deg between the planes)."""
    from .camera import pixel_rays
    seg = np.asarray(segs, float)
    d1 = pixel_rays(seg[:, 0], seg[:, 1], f, 0.0, 0.0)
    d2 = pixel_rays(seg[:, 2], seg[:, 3], f, 0.0, 0.0)
    n = np.cross(d1, d2)
    nn = np.linalg.norm(n, axis=-1, keepdims=True)
    if np.any(nn < 1e-9):
        return True
    ev = np.linalg.eigvalsh(np.einsum("ki,kj->ij", n / nn, n / nn))
    return bool(ev[1] < min_ratio * ev[2])


def _calibration_time(db, key, value):
    """Unix time a calibration describes: value['ts'|'valid_at'] if given, else when the row was stored."""
    for k in ("ts", "valid_at"):
        if isinstance(value, dict) and value.get(k):
            try:
                return parse_iso(value[k]).timestamp() if isinstance(value[k], str) else float(value[k])
            except Exception:
                pass
    try:
        r = db.con.execute("SELECT updated FROM calibration WHERE key=?", (key,)).fetchone()
        return parse_iso(r[0]).timestamp() if r and r[0] else None
    except Exception:
        return None


def _merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = _merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


class AstroBridge(Analyzer):
    """Periodic astro solver over the observation table (``astro_bridge`` in runner.ANALYZERS).

    on_tick (every 10 min): derive twilight markers from the photometry series, collect sun/moon
    pixels, star fields, plumb lines and shadows, and recompute a method's layer when enough new
    data arrived.  Heavy work runs in one background thread (analyzers must not block); results
    (astro_fix / plate_solution / twilight_marker Observations, calibration 'astro_camera',
    events) are handed back on the next tick.  Set ``threaded: false`` to compute inline.
    """
    name = "astro_bridge"
    tick_interval_s = 600

    def __init__(self, config=None):
        super().__init__(config)
        glob = (config or {}).get("_global", {})
        self.cfg = _merge(DEFAULTS, {k: v for k, v in (config or {}).items() if k != "_global"})
        self.tick_interval_s = self.cfg["tick_interval_s"]
        self.camera_cfg = glob.get("camera", {"heading_deg": 220.0, "pitch_deg": 0.0, "roll_deg": 0.0, "hfov_deg": 70.0})
        src = glob.get("source", {})
        self.default_wh = (src.get("width", 1280), src.get("height", 720))
        self._done_counts = {}
        self._results = queue.Queue()
        self._worker = None
        self._star_cache = {}
        self._last_state = {}
        self._reported = set()             # (method, jump half-hour) / mismatch keys already posted as events

    def available(self):
        return ephem.available()

    # ------------------------------------------------------------------ helpers
    @property
    def layers_dir(self):
        if self.cfg["layers_dir"]:
            return Path(self.cfg["layers_dir"])
        from hordejakt.layers.live import LIVE_DIR
        return LIVE_DIR

    def _frame_sizes(self, db, ids):
        ids = sorted({int(i) for i in ids if i is not None})
        out = {}
        for a in range(0, len(ids), 500):
            chunk = ids[a:a + 500]
            q = "SELECT id, w, h FROM frames WHERE id IN (%s)" % ",".join("?" * len(chunk))
            for i, w, h in db.con.execute(q, chunk):
                if w and h:
                    out[i] = (int(w), int(h))
        return out

    def _wh(self, o, sizes):
        v = o["value"]
        if v.get("w") and v.get("h"):
            return int(v["w"]), int(v["h"])
        return sizes.get(o.get("frame_id"), self.default_wh)

    def _level(self, db, pts_times=None):
        """Level reference from config ``attitude``, DB calibration ``camera_attitude`` and camera_vertical rows.

        camera_attitude = {pitch_deg, pitch_sigma_deg, roll_deg, roll_sigma_deg, heading_deg?, heading_sigma_deg?,
        method, ts?}: ``ts`` (ISO or unix) is when the attitude was measured; without it the time the row was
        stored is used.  It only matters after a camera bump (several pose segments): the priors then bind the
        pose in force at that time.  Missing sigmas fall back to the config / weak defaults.
        """
        a = self.cfg["attitude"]
        cal = db.calibration("camera_attitude") if db is not None else None
        src = "config level prior"
        if a == DEFAULTS["attitude"]:
            src = DEFAULTS_LEVEL_SOURCE
        att_t = None
        if cal:
            a = _merge(a, cal)
            src = f"calibration camera_attitude ({cal.get('method', 'manual')})"
            att_t = _calibration_time(db, "camera_attitude", cal)
        lev = LevelReference(
            pitch=(float(a["pitch_deg"]), float(a["pitch_sigma_deg"])) if a.get("pitch_sigma_deg") else None,
            roll=(float(a["roll_deg"]), float(a["roll_sigma_deg"])) if a.get("roll_sigma_deg") else None,
            heading=(float(a["heading_deg"]), float(a["heading_sigma_deg"])) if a.get("heading_sigma_deg") else None,
            source=src, att_t=att_t)
        segs, sig, ts, kinds = [], [], [], []
        f_nom = 0.5 / np.tan(np.radians(float(self.camera_cfg.get("hfov_deg", 70.0))) / 2.0)
        if db is not None:
            cv = db.observations(kind="camera_vertical")
            auto = [o for o in cv if o["value"].get("kind") == "auto_lines"]
            # the same trees are re-detected every day: only the latest automatic set counts
            cv = [o for o in cv if o["value"].get("kind") != "auto_lines"] + auto[-1:]
            for o in cv:
                v = o["value"]
                for fam in v.get("horizontal_families", []) or []:
                    fam = [q for q in fam if len(q) >= 4 and _finite(*q[:4])]
                    if len(fam) >= 2:
                        wv, hv = v.get("w", self.default_wh[0]), v.get("h", self.default_wh[1])
                        segs_f = np.array([[q[0] / wv - 0.5, (q[1] - 0.5 * hv) / wv, q[2] / wv - 0.5, (q[3] - 0.5 * hv) / wv]
                                           for q in fam])
                        if _family_degenerate(segs_f, f_nom):
                            log.warning("astro: horizontal family ignored - its edges lie (almost) in one plane through "
                                        "the camera, so their common direction is undefined (%s)", fam)
                            continue
                        lev.families.append((segs_f, np.radians(v.get("family_sigma_deg", 0.5)), o["ts"].timestamp()))
                w, h = v.get("w", self.default_wh[0]), v.get("h", self.default_wh[1])
                s_deg = v.get("sigma_deg") or self.cfg["vertical_sigma_deg"].get(v.get("kind", "default"),
                                                                                   self.cfg["vertical_sigma_deg"]["default"])
                for sgm in v.get("segments", []):
                    if len(sgm) < 4 or not np.all(np.isfinite(np.asarray(sgm, float))):
                        continue
                    x1, y1, x2, y2 = sgm[:4]
                    if np.hypot(x2 - x1, y2 - y1) < 1e-3 * w:
                        continue
                    segs.append([x1 / w - 0.5, (y1 - 0.5 * h) / w, x2 / w - 0.5, (y2 - 0.5 * h) / w])
                    sig.append(np.radians(sgm[4] if len(sgm) > 4 else s_deg))
                    ts.append(o["ts"].timestamp())
                    kinds.append(v.get("kind", "default"))
        if segs:
            sig = np.array(sig)
            kinds = np.array(kinds)
            floors = self.cfg["vertical_floor_deg"]
            capped = []
            # Leans of trees in one stand (slope, prevailing wind), detector biases of automatic lines and
            # uncorrected lens distortion are *correlated*: N lines do not beat that floor by sqrt(N).
            for k in np.unique(kinds):
                m = kinds == k
                comb = 1.0 / np.sqrt(np.sum(1.0 / sig[m] ** 2))
                floor = np.radians(floors.get(str(k), floors["default"]))
                if comb < floor:
                    sig[m] *= floor / comb
                    capped.append(f"{k} {np.degrees(floor):.2f} deg")
            lev.segments, lev.seg_sigma, lev.seg_t = np.array(segs), sig, np.array(ts)
            lev.seg_pose = np.zeros(len(segs), int)
            lev.source += f" + {len(segs)} plumb lines (camera_vertical)"
            if capped:
                lev.source += " (correlated-lean floor: " + ", ".join(capped) + ")"
        if lev.families:
            lev.source += f" + {len(lev.families)} level-line families"
        return lev

    def _auto_verticals(self, ctx):
        """Once per UTC day: Hough plumb-line candidates on the latest archived daylight frame."""
        if not self.cfg["auto_verticals"]:
            return []
        rows = ctx.db.con.execute("SELECT id, real_ts, path, w, h FROM frames WHERE path IS NOT NULL "
                                  "ORDER BY real_ts DESC LIMIT 300").fetchall()
        if not rows:
            return []
        # stream (not wall-clock) day, so replays spanning several days also get one set per day
        day = parse_iso(rows[0][1]).date().isoformat()
        if self._last_state.get("verticals_day") == day:
            return []
        self._last_state["verticals_day"] = day
        la0, lo0 = self.cfg["approx_site"]
        t = [parse_iso(r[1]) for r in rows]
        _, alt = ephem.altaz_grid(ephem.body_places("sun", t), [la0], [lo0])
        from .camera import detect_vertical_segments
        for k in np.argsort(-alt[0])[:5]:
            if alt[0, k] < 10.0:
                break
            fid, _, path, w, h = rows[k]
            try:
                import cv2
                img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)      # (imread's colour order is BGR)
            except Exception:
                img = None
            if img is None:
                continue
            segs = detect_vertical_segments(img)
            if len(segs) < 3:
                continue
            h_img, w_img = img.shape[:2]
            return [Observation("camera_vertical", t[k], {"segments": np.round(segs, 1).tolist(), "kind": "auto_lines",
                                                          "sigma_deg": self.cfg["auto_vertical_sigma_deg"], "w": w_img,
                                                          "h": h_img, "method": "canny+hough"}, self.name, 0.4,
                                frame_id=fid)]
        return []

    def _opts(self, ctx):
        fit = dict(self.cfg["fit"])
        hf = float(self.camera_cfg.get("hfov_deg", 70.0))
        fit.setdefault("f0", 0.5 / np.tan(np.radians(hf) / 2.0))
        fit.setdefault("dt_sigma_s", float(getattr(ctx.clock, "latency_sigma_s", 15.0)) if ctx else 15.0)
        return FitOptions(**{k: v for k, v in fit.items() if k in FitOptions.__dataclass_fields__})

    def _grid(self):
        return coarse_grid(self.cfg["domain"], self.cfg["coarse_dlat"], self.cfg["coarse_dlon"])

    # ------------------------------------------------------------------ data collection (main thread)
    def _binned_points(self, db, kind, body, bin_s):
        """Median pixel per time bin (per resolution); the bin widens until <= max_points remain."""
        obs = [o for o in db.observations(kind=kind) if _finite(o["value"].get("x"), o["value"].get("y"))]
        if not obs:
            return None, 0, None
        sizes = self._frame_sizes(db, [o.get("frame_id") for o in obs])
        while True:
            rows = {}
            for o in obs:
                w, h = self._wh(o, sizes)
                key = (int(o["ts"].timestamp() // bin_s), w, h)
                rows.setdefault(key, []).append((o["ts"].timestamp(), float(o["value"]["x"]), float(o["value"]["y"])))
            if len(rows) <= self.cfg["max_points"]:
                break
            bin_s *= 2
        t, x, y, W, H, wt = [], [], [], [], [], []
        for (_, w, h), r in sorted(rows.items()):
            a = np.array(r)
            t.append(np.median(a[:, 0]))
            x.append(np.median(a[:, 1]))
            y.append(np.median(a[:, 2]))
            W.append(w)
            H.append(h)
            wt.append(min(len(r), 4) / 4.0 * 0.5 + 0.5)
        return {"t": np.array(t), "x": np.array(x), "y": np.array(y), "w": np.array(W), "h": np.array(H),
                "wt": np.array(wt), "body": body}, len(obs), max(o["ts"] for o in obs)

    def _collect(self, ctx):
        db = ctx.db
        d = {"level": self._level(db), "opts": self._opts(ctx)}
        d["sun_track"], d["n_sun_track"], d["ts_sun_track"] = self._binned_points(db, "sun_pixel", "sun", self.cfg["sun_bin_s"])
        d["moon"], d["n_moon"], d["ts_moon"] = self._binned_points(db, "moon_pixel", "moon", self.cfg["moon_bin_s"])
        stars = []
        for o in db.observations(kind="star_field"):
            pts = [q for q in (o["value"].get("points") or []) if len(q) >= 2 and _finite(*q[:3])]
            if len(pts) >= self.cfg["stars"]["min_points"]:
                stars.append((o, pts))
        sizes = self._frame_sizes(db, [o.get("frame_id") for o, _ in stars])
        d["stars"] = [{"id": o["id"], "t": o["ts"], "points": pts, "wh": self._wh(o, sizes)} for o, pts in stars]
        stars = [o for o, _ in stars]
        d["n_stars"], d["ts_stars"] = len(stars), (max(o["ts"] for o in stars) if stars else None)
        mk = db.observations(kind="twilight_marker")
        d["twilight"] = [{"t": o["ts"], **o["value"]} for o in mk]
        d["n_twilight"], d["ts_twilight"] = len(mk), (max(o["ts"] for o in mk) if mk else None)
        sh = db.observations(kind="shadow_direction")
        sizes = self._frame_sizes(db, [o.get("frame_id") for o in sh])
        d["shadow"] = []
        for o in sh:
            v = o["value"]
            if not _finite(v.get("angle_deg_image"), v.get("x", 0.0), v.get("y", 0.0)):
                continue
            w, h = self._wh(o, sizes)
            d["shadow"].append({"t": o["ts"].timestamp(), "x": v.get("x", 0.5 * w) / w - 0.5,
                                "y": (v.get("y", 0.8 * h) - 0.5 * h) / w, "angle_deg_image": float(v["angle_deg_image"]),
                                "strength": float(v.get("strength", 1.0) or 1.0)})
        d["n_shadow"], d["ts_shadow"] = len(d["shadow"]), (max(o["ts"] for o in sh) if sh else None)
        d["camera_cal"] = db.calibration("astro_camera")
        moves = list(self.cfg["camera_moves"]) + list(db.calibration("camera_moves", []) or [])
        d["moves"] = [parse_iso(m).timestamp() if isinstance(m, str) else float(m) for m in moves]
        return d

    def _twilight_markers(self, ctx):
        """Derive new twilight_marker observations from sky/scene photometry (cheap, main thread)."""
        from . import twilight as tw
        db = ctx.db
        cfg = self.cfg["twilight"]
        last = db.con.execute("SELECT MAX(ts) FROM observations WHERE kind IN ('sky_photometry','scene_photometry')").fetchone()[0]
        if not last:
            return []
        until = parse_iso(last)
        since = datetime.fromtimestamp(until.timestamp() - cfg["lookback_h"] * 3600, UTC)
        if self._last_state.get("photometry_until") == last:
            return []
        self._last_state["photometry_until"] = last
        sky = db.observations(kind="sky_photometry", since=since)
        scene = db.observations(kind="scene_photometry", since=since)
        ir_by_frame = {o["frame_id"]: bool(o["value"].get("ir_mode")) for o in scene if o.get("frame_id") is not None}
        samples = [(o["ts"], o["value"].get("luma")) for o in sky
                   if not (o["value"].get("ir_mode") or ir_by_frame.get(o.get("frame_id"), False))
                   and "sky" in str(o["value"].get("region") or "sky") and _finite(o["value"].get("luma"))]
        approx = tuple(self.cfg["approx_site"])
        thresholds = list(cfg["thresholds"])
        vals = [v for _, v in samples if v is not None]
        if vals and max(vals) <= 1.5:                  # analyzer reports luma in 0..1 instead of 0..255
            thresholds = [t / 255.0 for t in thresholds]
        markers = tw.extract_markers(samples, thresholds, approx=approx)
        markers += tw.ir_switch_markers([(o["ts"], o["value"].get("ir_mode")) for o in scene], approx=approx)
        existing = db.observations(kind="twilight_marker", since=datetime.fromtimestamp(since.timestamp() - 6 * 3600, UTC))
        out = []
        for m in markers:
            # one marker per series and twilight: the extraction is re-run every tick over a sliding look-back,
            # so a later, different crossing of the same evening must not be added as a second measurement
            if any(e["value"].get("series") == m["series"] and e["value"].get("event") == m["event"]
                   and abs(e["ts"].timestamp() - m["t"]) < 4 * 3600 for e in existing):
                continue
            val = {k: v for k, v in m.items() if k != "t"}
            o = Observation("twilight_marker", datetime.fromtimestamp(m["t"], UTC), val, self.name, 0.6)
            out.append(o)
            existing.append({"ts": o.ts, "value": val})
        return out

    def _due(self, d):
        due = []
        for m in ("sun_track", "moon", "stars", "twilight", "shadow"):
            n = d.get(f"n_{m}", 0)
            if n < self.cfg["min_total"][m]:
                continue
            if n - self._done_counts.get(m, 0) >= self.cfg["min_new"][m]:
                due.append(m)
        return due

    # ------------------------------------------------------------------ tick
    def on_tick(self, ctx):
        out = self._drain(ctx)
        try:
            new_markers = self._twilight_markers(ctx)
        except Exception as e:
            log.exception("astro: twilight marker extraction failed: %s", e)
            new_markers = []
        out += new_markers
        try:
            for o in self._auto_verticals(ctx):
                ctx.db.add_observation(o)       # needed by this tick's level reference
        except Exception as e:
            log.warning("astro: automatic plumb-line detection failed: %s", e)
        d = self._collect(ctx)
        if new_markers:
            d["twilight"] += [{"t": o.ts, **o.value} for o in new_markers]
            d["n_twilight"] += len(new_markers)
            d["ts_twilight"] = max([d["ts_twilight"]] + [o.ts for o in new_markers] if d["ts_twilight"] else [o.ts for o in new_markers])
        due = self._due(d)
        if not due:
            return out
        if self._worker is not None and self._worker.is_alive():
            return out
        for m in due:
            self._done_counts[m] = d.get(f"n_{m}", 0)
        job = {"due": due, "data": d}
        if self.cfg["threaded"]:
            self._worker = threading.Thread(target=self._run_job, args=(job,), daemon=True, name="astro_bridge")
            self._worker.start()
        else:
            self._run_job(job)
            out += self._drain(ctx)
        return out

    def _drain(self, ctx):
        out = []
        while True:
            try:
                res = self._results.get_nowait()
            except queue.Empty:
                break
            for key, val in res.get("calibration", {}).items():
                ctx.db.set_calibration(key, val)
            for ev in res.get("events", []):
                ctx.db.add_event(ev["ts"], "astro", ev["summary"], ev.get("value"))
            out += res.get("observations", [])
        return out

    def _run_job(self, job):
        for method in job["due"]:
            t0 = time.time()
            try:
                res = getattr(self, f"_run_{method}")(job["data"])
            except Exception as e:  # never kill the monitor
                log.exception("astro: %s failed: %s", method, e)
                continue
            if res:
                log.info("astro: %s done in %.1f s", method, time.time() - t0)
                self._results.put(res)

    # ------------------------------------------------------------------ methods (worker thread)
    def _points(self, b):
        pl = ephem.body_places(b["body"], list(b["t"]))
        return CelestialPoints.from_places(pl, b["x"], b["y"], b["w"], b["h"], b["body"], weight=b["wt"])

    def _celestial_result(self, method, d, pts, extra_desc="", ts=None, init=None):
        lats, lons = self._grid()
        la0, lo0 = self.cfg["approx_site"]
        sol = solve_celestial(pts, d["level"], d["opts"], lats, lons, la0, lo0, moves=d["moves"], init=init)
        ref, fitter = sol["ref"], sol["fitter"]
        if not np.isfinite(sol["ll"]).any():
            log.warning("astro: %s produced no finite likelihood (%d points); layer not written", method, len(pts))
            return None
        summ = summarize(lats, lons, sol["ll"])
        n_days = len({int(t // 86400) for t in fitter.pts.t})
        rel = celestial_reliability(method, ref.n, ref.rms_px, fitter.level, n_days, ref.n_rejected, len(ref.jumps))
        k = np.unravel_index(_nanarg(sol["ll"]), sol["ll"].shape)
        pbest = sol["params"][k]
        level_sigma = fitter.level.strength_deg()
        meta = {"name": f"astro_{method}", "reliability": rel, "independence_group": "astro_attitude",
                "description": (f"{method}: {ref.n} points ({ref.n_rejected} rejected) over {n_days} day(s), fit rms "
                                f"{ref.rms_px:.2f} px, sigma {ref.sigma_px:.2f} px; level reference: {fitter.level.source} "
                                f"(zenith ~{level_sigma:.2f} deg). Location information comes from the level reference "
                                f"(1 deg = 111 km along the viewing azimuth / across it). {extra_desc}"),
                "sources": ["hordewatch observations (%s)" % method, "skyfield DE421 (skyfield-data)"],
                "fix": summ, "camera_at_best": {"heading_deg": float(pbest[0]), "pitch_deg": float(pbest[1]),
                                                "roll_deg": float(pbest[2]),
                                                "f_px_at_1280": float(np.exp(pbest[sol['lay'].lnf]) * 1280)},
                "pose_segments": int(fitter.S), "jumps": ref.jumps, "level_sigma_deg": level_sigma,
                "updated": datetime.now(UTC).isoformat()}
        path = write_layer(self.layers_dir / f"astro_{method}.npz", lats, lons, sol["ll"], meta)
        fix = {"method": method, "lat": summ["lat"], "lon": summ["lon"], "sigma_km": summ["sigma_km"],
               "grid_path": str(path), **{k2: summ[k2] for k2 in ("lat_map", "lon_map", "sigma_major_km",
                                                                   "sigma_minor_km", "major_axis_bearing_deg",
                                                                   "info_bits")},
               "reliability": rel, "n_points": ref.n, "rms_px": ref.rms_px, "level_reference": fitter.level.source,
               "level_sigma_deg": level_sigma}
        ts = ts or datetime.fromtimestamp(float(fitter.pts.t.max()), UTC)
        obs = [Observation("astro_fix", ts, fix, self.name, rel)]
        cal = {}
        if method in ("sun_track", "stars"):
            cal["astro_camera"] = {"method": method, "G": [g.tolist() for g in ref.G], "f": float(np.exp(ref.p[ref.lay.lnf])),
                                   "rms_px": ref.rms_px, "n": ref.n, "pose_segments": int(fitter.S),
                                   "updated": datetime.now(UTC).isoformat(), "last_t": float(fitter.pts.t.max())}
        events = [{"ts": ts, "summary": f"astro {method}: {summ['lat']:.2f}N {summ['lon']:.2f}E +-{summ['sigma_km']:.0f} km "
                                        f"(r={rel:.2f}, {summ['info_bits']:.1f} bits)", "value": fix}]
        # human-facing alerts only for what is new: every recompute sees the same historic jumps again
        for j in ref.jumps:
            key = (method, int(round(j["t"] / 1800.0)))
            if key in self._reported:
                continue
            self._reported.add(key)
            events.append({"ts": datetime.fromtimestamp(j["t"], UTC), "summary": f"astro: camera pose jump ({j['why']})",
                           "value": j})
        other = d.get("camera_cal")
        if other and other.get("method") != method and method in ("sun_track", "stars") and other.get("G"):
            ang = float(rotation_angle_deg(np.array(other["G"][-1]), ref.G[-1]))   # latest pose of both
            key = ("mismatch", method, other.get("method"))
            if ang > 0.5 and key not in self._reported:
                self._reported.add(key)
                events.append({"ts": ts, "summary": f"astro: camera orientation from {method} differs from "
                                                    f"{other['method']} by {ang:.2f} deg (camera moved?)", "value": {"deg": ang}})
            elif ang <= 0.5:
                self._reported.discard(key)
        return {"observations": obs, "calibration": cal, "events": events}

    def _run_sun_track(self, d):
        if d["sun_track"] is None:
            return None
        return self._celestial_result("sun_track", d, self._points(d["sun_track"]), ts=d["ts_sun_track"])

    def _run_moon(self, d):
        if d["moon"] is None:
            return None
        return self._celestial_result("moon", d, self._points(d["moon"]), ts=d["ts_moon"],
                                      extra_desc="Moon topocentric (parallax) modelled.")

    def _approx_camera(self, d, aspect):
        from .stars import ApproxCamera
        la0, lo0 = self.cfg["approx_site"]
        cal = d.get("camera_cal")
        if cal and cal.get("G"):
            return ApproxCamera(np.array(cal["G"][-1]), float(cal["f"]), 0.5, 0.5 * aspect, 0.0, la0, lo0)
        c = self.camera_cfg
        f = 0.5 / np.tan(np.radians(float(c.get("hfov_deg", 70.0))) / 2.0)
        return ApproxCamera.from_attitude(float(c.get("heading_deg", 220.0)), float(c.get("pitch_deg", 0.0)),
                                          float(c.get("roll_deg", 0.0)), f, la0, lo0, aspect=aspect)

    def match_star_fields(self, d):
        """Identify stars in (up to max_frames) star_field observations -> CelestialPoints, plate solutions."""
        from . import stars as st
        fields = sorted(d["stars"], key=lambda s: -len(s["points"]))
        # spread over time: best field per 20-min bin
        chosen, bins = [], set()
        for s in fields:
            b = int(s["t"].timestamp() // 1200)
            if b in bins:
                continue
            bins.add(b)
            chosen.append(s)
            if len(chosen) >= self.cfg["stars"]["max_frames"]:
                break
        pts_list, plates = [], []
        for s in chosen:
            w, h = s["wh"]
            aspect = h / w
            # a failed identification is retried once a better approximate camera (astro_camera) exists
            cam_key = (s["id"], (d.get("camera_cal") or {}).get("updated"))
            if s["id"] in self._star_cache:
                fm = self._star_cache[s["id"]]
            elif cam_key in self._star_cache:
                fm = None
            else:
                P = np.asarray(s["points"], float)
                if P.shape[1] < 3:
                    P = np.c_[P[:, :2], np.ones(len(P))]
                fm = None
                if st.solve_field_available():
                    sol = st.astrometry_solve(P[:, :2], P[:, 2], w, h)
                    if sol and len(sol["pairs"]) >= 5:
                        pr = np.array(sol["pairs"])
                        pl = ephem.star_places(pr[:, 2], pr[:, 3], when=s["t"])
                        fm = st.FrameMatch(np.c_[np.arange(len(pr)), -np.ones(len(pr), int)], pr[:, 0] / w,
                                           pr[:, 1] / w, pl, ["astrometry.net"] * len(pr), np.full(len(pr), np.nan),
                                           np.nan, np.eye(3), np.nan, "astrometry.net")
                if fm is None:
                    cam = self._approx_camera(d, aspect)
                    Pn = np.c_[P[:, 0] / w, P[:, 1] / w, P[:, 2]]
                    fm = st.match_frame(Pn, s["t"], cam, aspect=aspect, vmax=self.cfg["stars"]["vmax"])
                self._star_cache[s["id"] if fm is not None else cam_key] = fm
            if fm is None:
                continue
            pts_list.append(CelestialPoints.from_places(fm.places, fm.X * w, fm.Y * w, w, h, "star"))
            if fm.method != "astrometry.net":
                plates.append((s, st.plate_summary(fm, w, aspect)))
        return (CelestialPoints.concat(pts_list) if pts_list else None), plates

    def _run_stars(self, d):
        pts, plates = self.match_star_fields(d)
        if pts is None or len(pts) < self.cfg["stars"]["min_matched"]:
            return None
        o = d["opts"]
        d = dict(d, opts=FitOptions(**{**o.__dict__, "pixel_sigma_prior": min(o.pixel_sigma_prior, 1.0)}))
        res = self._celestial_result("stars", d, pts, ts=d["ts_stars"],
                                     extra_desc=f"{len(plates)} frame(s) matched with the bright-star catalogue.")
        for s, val in plates:
            res["observations"].append(Observation("plate_solution", s["t"], val, self.name, 0.8))
        return res

    def _run_twilight(self, d):
        from . import twilight as tw
        cfg = self.cfg["twilight"]
        lats, lons = self._grid()
        L, O = np.meshgrid(lats, lons, indexing="ij")
        series_asym = {m["series"]: cfg["ir_asym_sigma_deg"] for m in d["twilight"] if m.get("series") == "ir_switch"}
        r = tw.twilight_loglik(d["twilight"], L.ravel(), O.ravel(), cfg["sigma_prior_min"], cfg["sigma_floor_min"],
                               cfg["asym_sigma_deg"], series_asym, d["opts"].dt_sigma_s)
        ll = r.loglik.reshape(L.shape)
        summ = summarize(lats, lons, ll)
        def _days(ev):
            return {int((m["t"].timestamp() if isinstance(m["t"], datetime) else float(m["t"])) // 86400)
                    for m in d["twilight"] if m["event"] == ev}
        both = min(len(_days("dusk")), len(_days("dawn")))
        rel = 0.4 if (both >= 3 and r.best["rms_min"] <= 5.0) else 0.3
        meta = {"name": "astro_twilight", "reliability": rel, "independence_group": "astro_twilight",
                "description": (f"Twilight timing: {r.n} markers in series {r.series}, noise {r.sigma_min:.1f} min, "
                                f"best h0 {r.best['h0']}, asymmetry {r.best['asym']}. Longitude from the dusk/dawn "
                                f"midpoint (limited by dusk/dawn asymmetry), latitude only weakly from night length."),
                "sources": ["hordewatch sky_photometry / scene_photometry (IR switch)", "skyfield DE421"],
                "fix": summ, "updated": datetime.now(UTC).isoformat()}
        path = write_layer(self.layers_dir / "astro_twilight.npz", lats, lons, ll, meta)
        fix = {"method": "twilight", "lat": summ["lat"], "lon": summ["lon"], "sigma_km": summ["sigma_km"],
               "grid_path": str(path), "lat_map": summ["lat_map"], "lon_map": summ["lon_map"],
               "sigma_major_km": summ["sigma_major_km"], "sigma_minor_km": summ["sigma_minor_km"],
               "major_axis_bearing_deg": summ["major_axis_bearing_deg"], "info_bits": summ["info_bits"],
               "reliability": rel, "n_points": r.n, "sigma_min": r.sigma_min}
        ts = d["ts_twilight"] or datetime.now(UTC)
        return {"observations": [Observation("astro_fix", ts, fix, self.name, rel)],
                "events": [{"ts": ts, "summary": f"astro twilight: lon {summ['lon']:.2f}E +-{summ['sigma_major_km']:.0f} km", "value": fix}]}

    def _run_shadow(self, d):
        if len(d["shadow"]) < self.cfg["min_total"]["shadow"]:
            return None
        lats, lons = self._grid()
        L, O = np.meshgrid(lats, lons, indexing="ij")
        cal = d.get("camera_cal")
        if cal and cal.get("G"):
            # per-cell attitude that reproduces the Earth-fixed orientation found from the sun/stars
            _, T = ephem.observer_frame(L.ravel(), O.ravel())
            R = np.einsum("ij,ckj->cik", np.array(cal["G"][-1]), T)
            f = float(cal["f"])
            how = "camera orientation from " + cal.get("method", "astro")
        else:
            c = self.camera_cfg
            R = rotation_matrix(c.get("heading_deg", 220.0), c.get("pitch_deg", 0.0), c.get("roll_deg", 0.0))
            f = 0.5 / np.tan(np.radians(float(c.get("hfov_deg", 70.0))) / 2.0)
            how = "configured camera pose"
        ll = shadow_loglik(d["shadow"], L.ravel(), O.ravel(), R, f, sigma_deg=self.cfg["shadow"]["sigma_deg"]).reshape(L.shape)
        summ = summarize(lats, lons, ll)
        rel = 0.3
        meta = {"name": "astro_shadow", "reliability": rel, "independence_group": "astro_shadow",
                "description": f"{len(d['shadow'])} cast-shadow directions on level ground vs sun azimuth ({how})",
                "sources": ["hordewatch shadow_direction", "skyfield DE421"], "fix": summ}
        path = write_layer(self.layers_dir / "astro_shadow.npz", lats, lons, ll, meta)
        fix = {"method": "shadow", "lat": summ["lat"], "lon": summ["lon"], "sigma_km": summ["sigma_km"],
               "grid_path": str(path), "reliability": rel, "n_points": len(d["shadow"])}
        return {"observations": [Observation("astro_fix", d["ts_shadow"], fix, self.name, rel)]}


DEFAULTS_LEVEL_SOURCE = "default level prior (roll 0+-3, pitch 0+-15 deg)"
