"""Pinhole camera model shared by the sun / moon / star solvers.

Conventions
-----------
* World frame: local East-North-Up (ENU) at the camera.
* Camera frame (OpenCV): x right, y down, z forward (optical axis).
* Attitude = (heading psi, pitch theta, roll phi), all in degrees:
    forward  f = (sin psi cos theta, cos psi cos theta, sin theta)
    right_0  r0 = (cos psi, -sin psi, 0)           (horizontal)
    up_0     u0 = r0 x f = (-sin psi sin theta, -cos psi sin theta, cos theta)
    roll:    r = cos phi r0 + sin phi u0 ,  u = -sin phi r0 + cos phi u0
  i.e. positive roll lifts the right-hand side of the camera, so the horizon
  appears to slope *down* towards the right edge of the image.
  The rotation R (world -> camera) has rows (r, -u, f).
* Pixels: x = cx + f * X (1 + k1 rho^2),  y = cy + f * Y (1 + k1 rho^2),
  X = c_x / c_z, Y = c_y / c_z, rho^2 = X^2 + Y^2.  The principal point
  defaults to the image centre; k1 is a one-term radial distortion (barrel < 0).
  Every function works in any consistent pixel unit; the solvers use pixels
  divided by the image width so that 720p and 1080p frames of the same stream
  share one model (YouTube renditions are scaled copies of one sensor image).

The fundamental degeneracy (why a camera alone cannot find its latitude)
-------------------------------------------------------------------------
The direction of a celestial body in *Earth-fixed* coordinates at time t does
not depend on the observer (apart from parallax: 8.8" for the Sun, ~1 deg for
the Moon).  An observer at (lat, lon) sees it in camera coordinates as

    c = R_cam(psi, theta, phi) . T(lat, lon) . e_EF(t)

and only the product G = R_cam . T enters: a pure 3-D rotation.  Any (lat, lon)
is reproduced exactly by another camera attitude R_cam' = G . T(lat', lon')^T.
Sun tracks, star fields and moon tracks therefore determine G - the camera's
orientation relative to the rotating Earth - to hundredths of a degree, but
they say *nothing* about the site until the camera's attitude relative to
gravity (pitch and roll = where the zenith is in the image) is known.  This is
celestial navigation with a sextant: the sea horizon supplies the vertical, and
an altitude error of 1' is a position error of 1 NM.  Here:

    1 deg of pitch error = 111 km along the camera's viewing azimuth,
    1 deg of roll error  = 111 km perpendicular to it (both through the zenith).

Refraction (it depends on the true altitude) breaks the degeneracy only very
weakly (sub-pixel curvature for a sun track); Moon parallax by ~0.3 px per
100 km.  A level reference is therefore an explicit input of the solvers:
vertical structures in the image (tree trunks +-1-2 deg each, box posts,
anything *hanging*, which is a plumb line to 0.1 deg) and/or configured
priors.  ``vertical_residuals`` implements the plumb-line constraint.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


# ----------------------------------------------------------------------------- rotations
def rotation_matrix(heading_deg, pitch_deg, roll_deg):
    """World(ENU) -> camera rotation(s); broadcasts over the inputs, returns (..., 3, 3)."""
    psi, th, ph = (np.radians(np.asarray(a, float)) for a in (heading_deg, pitch_deg, roll_deg))
    psi, th, ph = np.broadcast_arrays(psi, th, ph)
    sp, cp, st, ct, sr, cr = np.sin(psi), np.cos(psi), np.sin(th), np.cos(th), np.sin(ph), np.cos(ph)
    fwd = np.stack([sp * ct, cp * ct, st], axis=-1)
    r0 = np.stack([cp, -sp, np.zeros_like(sp)], axis=-1)
    u0 = np.stack([-sp * st, -cp * st, ct], axis=-1)
    r = cr[..., None] * r0 + sr[..., None] * u0
    u = -sr[..., None] * r0 + cr[..., None] * u0
    return np.stack([r, -u, fwd], axis=-2)


def attitude_from_rotation(R):
    """Inverse of rotation_matrix: (heading, pitch, roll) in degrees from (..., 3, 3)."""
    R = np.asarray(R, float)
    fwd = R[..., 2, :]
    psi = np.arctan2(fwd[..., 0], fwd[..., 1])
    th = np.arcsin(np.clip(fwd[..., 2], -1.0, 1.0))
    sp, cp, st, ct = np.sin(psi), np.cos(psi), np.sin(th), np.cos(th)
    r = R[..., 0, :]
    r0 = np.stack([cp, -sp, np.zeros_like(sp)], axis=-1)
    u0 = np.stack([-sp * st, -cp * st, ct], axis=-1)
    ph = np.arctan2(np.sum(r * u0, -1), np.sum(r * r0, -1))
    return np.degrees(psi) % 360.0, np.degrees(th), np.degrees(ph)


def rotation_angle_deg(Ra, Rb):
    """Angle of the rotation Ra Rb^T (deg): how far apart two orientations are."""
    M = np.einsum("...ij,...kj->...ik", Ra, Rb)
    tr = np.clip((np.trace(M, axis1=-2, axis2=-1) - 1.0) / 2.0, -1.0, 1.0)
    return np.degrees(np.arccos(tr))


# ----------------------------------------------------------------------------- projection
def project(cam_vec, f, cx, cy, k1=0.0):
    """Camera-frame vectors (..., 3) -> pixel (x, y, in_front). f, cx, cy, k1 broadcast."""
    z = cam_vec[..., 2]
    front = z > 1e-9
    zs = np.where(front, z, 1e-9)
    X = cam_vec[..., 0] / zs
    Y = cam_vec[..., 1] / zs
    d = 1.0 + k1 * (X * X + Y * Y)
    return cx + f * X * d, cy + f * Y * d, front


def undistort_normalised(xd, yd, k1, n_iter=8):
    """Invert X (1 + k1 rho^2) by fixed-point iteration (|k1| < ~0.3)."""
    X, Y = xd, yd
    if np.all(np.asarray(k1) == 0):
        return X, Y
    for _ in range(n_iter):
        d = 1.0 + k1 * (X * X + Y * Y)
        X, Y = xd / d, yd / d
    return X, Y


def pixel_rays(x, y, f, cx, cy, k1=0.0):
    """Pixels -> unit rays in the camera frame (..., 3)."""
    X, Y = undistort_normalised((np.asarray(x) - cx) / f, (np.asarray(y) - cy) / f, k1)
    v = np.stack(np.broadcast_arrays(X, Y, np.ones_like(X)), axis=-1)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def vertical_residuals(segments, R, f, cx, cy, k1=0.0):
    """Plumb-line residuals (radians) of image segments that are vertical in the world.

    segments: (K, 4) [x1, y1, x2, y2] in the same units as f/cx/cy.
    R: (..., 3, 3) world->camera.  The 3-D line is vertical iff the plane through
    the camera centre and the image line contains the world 'up' vector:
    residual = asin(n . up_cam), n = unit normal of that plane.  A lean *towards*
    the camera is unobservable and correctly gives 0.  Returns (..., K).
    """
    seg = np.asarray(segments, float)
    f = np.asarray(f, float)[..., None]
    cx = np.asarray(cx, float)[..., None]
    cy = np.asarray(cy, float)[..., None]
    k1 = np.asarray(k1, float)[..., None]
    d1 = pixel_rays(seg[:, 0], seg[:, 1], f, cx, cy, k1)
    d2 = pixel_rays(seg[:, 2], seg[:, 3], f, cx, cy, k1)
    n = np.cross(d1, d2)
    n = n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-12)
    up = R[..., :, 2]                          # camera coords of world up = column 3 of R
    return np.arcsin(np.clip(np.sum(n * up[..., None, :], -1), -1.0, 1.0))


def ground_direction_azimuth(x, y, angle_deg_image, R, f, cx, cy, k1=0.0, step=0.02):
    """World azimuth (deg) of a line on *horizontal ground* seen at pixel (x, y) with image angle.

    angle_deg_image: direction of the line in the image, measured from the +x axis
    towards +y (i.e. clockwise on screen).  Two nearby image points are back-projected
    onto the plane z = -1 (camera height cancels out of the direction).  Used for shadow
    directions: a vertical object's shadow on level ground points to sun azimuth + 180.
    """
    a = np.radians(angle_deg_image)
    s = step * f
    xs = np.stack([x, x + s * np.cos(a)])
    ys = np.stack([y, y + s * np.sin(a)])
    rays_c = pixel_rays(xs, ys, f, cx, cy, k1)                     # (2, ..., 3)
    Rt = np.swapaxes(R, -1, -2)
    rays_w = np.einsum("...ij,k...j->k...i", Rt, rays_c)
    t = -1.0 / np.minimum(rays_w[..., 2], -1e-6)                   # hits ground only if looking down
    p = rays_w * t[..., None]
    d = p[1] - p[0]
    return np.degrees(np.arctan2(d[..., 0], d[..., 1])) % 360.0, rays_w[..., 2].max(axis=0) < 0


# ----------------------------------------------------------------------------- convenience model
@dataclass
class CameraModel:
    heading_deg: float = 220.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    f_px: float = 1000.0
    width: int = 1280
    height: int = 720
    cx: float | None = None
    cy: float | None = None
    k1: float = 0.0
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_hfov(cls, hfov_deg, width=1280, height=720, **kw):
        return cls(f_px=(width / 2.0) / np.tan(np.radians(hfov_deg) / 2.0), width=width, height=height, **kw)

    @property
    def principal(self):
        return (self.width / 2.0 if self.cx is None else self.cx, self.height / 2.0 if self.cy is None else self.cy)

    @property
    def R(self):
        return rotation_matrix(self.heading_deg, self.pitch_deg, self.roll_deg)

    @property
    def hfov_deg(self):
        return float(np.degrees(2 * np.arctan(self.width / 2.0 / self.f_px)))

    def project_enu(self, enu):
        cx, cy = self.principal
        c = np.einsum("ij,...j->...i", self.R, np.asarray(enu, float))
        x, y, front = project(c, self.f_px, cx, cy, self.k1)
        inside = front & (x >= 0) & (x < self.width) & (y >= 0) & (y < self.height)
        return x, y, inside

    def project_altaz(self, az_deg, alt_deg):
        az, alt = np.radians(az_deg), np.radians(alt_deg)
        enu = np.stack([np.cos(alt) * np.sin(az), np.cos(alt) * np.cos(az), np.sin(alt)], axis=-1)
        return self.project_enu(enu)

    def unproject(self, x, y):
        """Pixels -> (az, alt) in degrees."""
        cx, cy = self.principal
        rays = pixel_rays(x, y, self.f_px, cx, cy, self.k1)
        enu = np.einsum("ji,...j->...i", self.R, rays)
        az = np.degrees(np.arctan2(enu[..., 0], enu[..., 1])) % 360.0
        alt = np.degrees(np.arcsin(np.clip(enu[..., 2], -1, 1)))
        return az, alt

    def to_dict(self):
        return {"heading_deg": self.heading_deg, "pitch_deg": self.pitch_deg, "roll_deg": self.roll_deg,
                "f_px": self.f_px, "width": self.width, "height": self.height, "cx": self.cx, "cy": self.cy,
                "k1": self.k1}
