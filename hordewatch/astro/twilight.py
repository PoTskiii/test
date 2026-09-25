"""Twilight timing: location from *when* the sky gets dark and light again.

Why it works without any camera geometry
----------------------------------------
Sky (and scene) brightness during twilight is, to first order, a function of the
Sun's depression below the *local* horizon only.  A fixed luminance threshold
(or the camera's own day/night IR switch, a built-in photometer) is therefore
crossed at a fixed solar altitude h0 every evening and morning.  The solar
altitude is gravity-referenced by definition, so - unlike sun tracks or star
fields (see camera.py) - no level reference is needed.

Model (per candidate site x, per marker series s = one threshold / detector)
    h_sun(x, t_i + dt) = h0_s + e_i * a_s + noise,     e_i = +1 dusk, -1 dawn
  * h0_s   unknown threshold altitude (nuisance, weak prior N(-4, 6) deg);
  * a_s    dusk/dawn asymmetry (nuisance, prior N(0, sigma_a)): the camera looks
           SW, so the evening glow is *in* the view and the morning glow behind
           it; a sky-ROI threshold is then reached at a deeper depression at dusk
           than at dawn.  For sky thresholds sigma_a ~ 0.5-1 deg; for the IR
           switch (hysteresis between on/off lux levels) ~1.5 deg;
  * dt     common timing error (stream latency, prior N(0, latency sigma)).
Linearising with the solar altitude rate hdot_i (deg/min, from the ephemeris at
the site) gives a time residual
    r_i = (h_i - h0_s - e_i a_s) / hdot_i + dt       (minutes)
which is linear in (h0_s, a_s, dt): per cell a tiny weighted least-squares
problem, solved for thousands of cells at once.  Clouds shift individual
crossings by minutes (overcast = darker = earlier dusk / later dawn), so the
residuals use a Student-t (nu = 4) loss with a noise scale learned from the
data (shrunk towards a 4-min prior, floored at 1 min).

What it constrains
------------------
* Longitude: dusk and dawn at the same depression straddle local solar midnight
  symmetrically, so their midpoint (after the equation of time, which the
  ephemeris handles) is a clock reading of longitude: 1 min = 0.25 deg.  The
  asymmetry nuisance a_s and the latency dt are the systematic floor
  (a = 0.5 deg at 61 N, where the Sun sinks ~0.12 deg/min near the equinox,
  moves the midpoint by ~4 min = 1 deg of longitude!), which is why the layer
  is broad in longitude unless several series / many days agree.
* Latitude: only through the *duration* of twilight/night and its change from
  day to day.  Duration alone is degenerate with h0 (a deeper h0 at a lower
  latitude gives the same night length); the day-to-day change of night length
  near the equinox scales with tan(latitude) (~7 min/day at 61 N vs ~5.5 at
  55 N), so a latitude constraint only builds up over a week or more, and is
  weak for the few days of the hunt.

Marker extraction from photometry
---------------------------------
``extract_markers`` turns the per-frame ``sky_photometry`` luma series (and
``scene_photometry.ir_mode`` flags) into crossing times: 1-min medians, a
5-min running median, then the downward crossing of each threshold in the
evening window that stays below it for 20 min (hysteresis) and the sustained
upward crossing in the morning.  Crossings next to data gaps (> 3 min, stream
outages) are rejected, since a reconnect after a gap would otherwise look like a
crossing.

Two rules make the markers safe for a *live* monitor that re-runs the extraction
every tick over a sliding look-back:
* a window (dusk: sunset - 2 h .. + 3 h, dawn: sunrise - 3 h .. + 2 h at the
  approximate site) is only decided once the data covers all of it - otherwise a
  crossing picked from a half-seen evening could be followed by a second, different
  one an hour later (moonrise, lit clouds, headlights on the sky ROI);
* a window with more than one sustained crossing of the same threshold is
  *ambiguous* and gives no marker.  Which one is "the" twilight crossing is then a
  guess, and a wrong guess (a crossing at 15 deg depression) is worth far less than
  a missing marker.
The same logic applies to IR switches (camera flapping between modes under clouds),
which must in addition go the right way (to IR while the Sun sinks).
"""
from __future__ import annotations

import functools
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import numpy as np

from . import ephem

UTC = timezone.utc


# ----------------------------------------------------------------------------- solving
@dataclass
class TwilightResult:
    loglik: np.ndarray             # (C,)
    chi2: np.ndarray
    sigma_min: float               # noise scale used (minutes)
    n: int
    series: list
    best: dict = field(default_factory=dict)


def _solar_alt_and_rate(t_unix, lats, lons, height_m=0.0):
    pl = ephem.body_places("sun", list(t_unix))
    pl2 = ephem.body_places("sun", list(np.asarray(t_unix) + 60.0))
    _, h = ephem.altaz_grid(pl, lats, lons, height_m)
    _, h2 = ephem.altaz_grid(pl2, lats, lons, height_m)
    return h, h2 - h                                  # deg, deg/min


def _solve(h, hdot, ev, sid, S, sig_t, asym_sig, dt_sig_min, h0_prior, nu=4.0, irls=4):
    """Vectorised robust linear solve per cell.  Returns (objective (C,), params (C,P), residuals (C,n))."""
    C, n = h.shape
    P = 2 * S + 1
    hd = np.where(np.abs(hdot) < 1e-3, np.sign(hdot + 1e-12) * 1e-3, hdot)
    y = h / hd                                        # r = y - A p
    A = np.zeros((C, n, P))
    A[:, np.arange(n), sid] = 1.0 / hd
    A[:, np.arange(n), S + sid] = ev[None, :] / hd
    A[:, :, 2 * S] = -1.0
    # prior rows (same for every cell)
    pr_A, pr_y, pr_w = [], [], []
    for s in range(S):
        row = np.zeros(P); row[s] = 1.0
        pr_A.append(row); pr_y.append(h0_prior[0]); pr_w.append(1.0 / h0_prior[1] ** 2)
        row = np.zeros(P); row[S + s] = 1.0
        pr_A.append(row); pr_y.append(0.0); pr_w.append(1.0 / asym_sig[s] ** 2)
    row = np.zeros(P); row[2 * S] = 1.0
    pr_A.append(row); pr_y.append(0.0); pr_w.append(1.0 / dt_sig_min ** 2)
    pr_A, pr_y, pr_w = np.array(pr_A), np.array(pr_y), np.array(pr_w)
    w = np.ones((C, n))
    for _ in range(irls):
        W = w / sig_t ** 2
        N = np.einsum("cni,cn,cnj->cij", A, W, A) + np.einsum("ki,k,kj->ij", pr_A, pr_w, pr_A)[None]
        b = np.einsum("cni,cn,cn->ci", A, W, y) + (pr_A.T @ (pr_w * pr_y))[None]
        p = np.linalg.solve(N + 1e-9 * np.eye(P)[None], b[..., None])[..., 0]
        r = y - np.einsum("cni,ci->cn", A, p)
        z2 = (r / sig_t) ** 2
        w = (nu + 1.0) / (nu + z2)                     # Student-t IRLS weights
    obj = np.sum((nu + 1.0) * np.log1p(z2 / nu), axis=1)          # = -2 log t-likelihood (+const)
    obj = obj + np.sum(pr_w[None] * (pr_y[None] - p @ pr_A.T) ** 2, axis=1)
    return obj, p, r


def twilight_loglik(markers, lats, lons, sigma_prior_min=4.0, sigma_floor_min=1.0, asym_sigma_deg=0.75,
                    series_asym=None, latency_sigma_s=15.0, h0_prior=(-4.0, 6.0), height_m=0.0) -> TwilightResult:
    """Log-likelihood over candidate sites (1-D arrays lats, lons of equal length).

    markers: iterable of dicts {t (datetime or unix), event: 'dusk'|'dawn', series: str}.
    series_asym: optional {series: asymmetry sigma (deg)} overriding asym_sigma_deg.
    """
    mk = [m for m in markers if m.get("event") in ("dusk", "dawn")]
    if not mk:
        raise ValueError("no twilight markers")
    t = np.array([m["t"].timestamp() if isinstance(m["t"], datetime) else float(m["t"]) for m in mk])
    ev = np.array([1.0 if m["event"] == "dusk" else -1.0 for m in mk])
    names = sorted({m.get("series", "default") for m in mk})
    sid = np.array([names.index(m.get("series", "default")) for m in mk])
    S = len(names)
    asym = np.array([(series_asym or {}).get(s, asym_sigma_deg) for s in names], float)
    h, hdot = _solar_alt_and_rate(t, lats, lons, height_m)
    dt_sig = max(latency_sigma_s, 1.0) / 60.0
    # pass 1 with the prior noise scale -> learn the scatter at the best cell
    obj, p, r = _solve(h, hdot, ev, sid, S, sigma_prior_min, asym, dt_sig, h0_prior)
    k = int(np.argmin(np.where(np.isfinite(obj), obj, np.inf)))
    n = len(t)
    dof = max(n - (2 * S + 1) * 0.5, 1.0)             # asymmetry / dt are prior-constrained: count half
    s2 = float(np.sum(r[k] ** 2) / dof)
    nu0 = 4.0
    sig = float(np.sqrt((dof * s2 + nu0 * sigma_prior_min ** 2) / (dof + nu0)))
    sig = max(sig, sigma_floor_min)
    obj, p, r = _solve(h, hdot, ev, sid, S, sig, asym, dt_sig, h0_prior)
    k = int(np.argmin(np.where(np.isfinite(obj), obj, np.inf)))
    best = {"cell": k, "h0": {s: float(p[k, i]) for i, s in enumerate(names)},
            "asym": {s: float(p[k, S + i]) for i, s in enumerate(names)}, "dt_s": float(p[k, 2 * S] * 60.0),
            "rms_min": float(np.sqrt(np.mean(r[k] ** 2)))}
    return TwilightResult(loglik=-0.5 * obj, chi2=obj, sigma_min=sig, n=n, series=names, best=best)


# ----------------------------------------------------------------------------- marker extraction
def _minute_series(ts, vals):
    """1-min medians. ts unix seconds (sorted), returns (t_min_centres, values)."""
    m = np.floor(np.asarray(ts) / 60.0).astype(np.int64)
    uniq, start = np.unique(m, return_index=True)
    out = np.array([np.median(v) for v in np.split(np.asarray(vals, float), start[1:])])
    return uniq * 60.0 + 30.0, out


def _running_median(v, k=5):
    if len(v) < k:
        return v.copy()
    pad = k // 2
    vp = np.pad(v, pad, mode="edge")
    return np.median(np.lib.stride_tricks.sliding_window_view(vp, k), axis=1)


@functools.lru_cache(maxsize=64)
def _approx_sun_events(day, lat, lon):
    """(sunset, sunrise-next-morning) unix times at the approximate site for a UTC date.

    Memoised: the bridge re-extracts markers every tick over a 40-h look-back, and 2 x 576 IAU2000A
    apparent places per day would otherwise cost ~0.15 s per day and tick in the main thread.
    (Callers must not modify the returned arrays.)"""
    t0 = datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp()
    ts = t0 + np.arange(0, 48 * 3600, 300.0)
    _, h = ephem.altaz_grid(ephem.body_places("sun", list(ts)), [lat], [lon])
    h = h[0]
    down = np.nonzero((h[:-1] > 0) & (h[1:] <= 0))[0]
    up = np.nonzero((h[:-1] <= 0) & (h[1:] > 0))[0]
    return ts, h, down, up


def extract_markers(samples, thresholds, approx=(61.25, 9.0), hold_min=20.0, max_gap_min=3.0, series_prefix="sky_luma",
                    min_points=30, require_complete=True):
    """Threshold crossings of a brightness series.

    samples: iterable of (datetime|unix, luma) - one per frame; non-positive luma ignored.
    thresholds: luma levels (same units as the samples).
    require_complete: decide a twilight window only when the data reaches its end (see module docstring);
    set False for a finished recording whose last window is cut short.
    Returns list of dicts {t, event, series, threshold, method, slope_per_min}.
    """
    data = [(s[0].timestamp() if isinstance(s[0], datetime) else float(s[0]), float(s[1])) for s in samples
            if s[1] is not None and float(s[1]) > 0]
    if len(data) < min_points:
        return []
    data.sort()
    ts, v = _minute_series([d[0] for d in data], [d[1] for d in data])
    lv = _running_median(np.log(np.maximum(v, 1e-3)), 5)
    gaps = np.diff(ts) > max_gap_min * 60.0 + 1
    out = []
    lat, lon = approx
    days = sorted({datetime.fromtimestamp(t, UTC).date() for t in ts})
    for day in [days[0] - timedelta(days=1)] + days:
        grid_t, h, down, up = _approx_sun_events(day, lat, lon)
        windows = []
        for i in down[:1]:
            windows.append(("dusk", grid_t[i] - 2 * 3600, grid_t[i] + 3 * 3600))
        for i in up:
            if grid_t[i] > (grid_t[down[0]] if len(down) else 0):
                windows.append(("dawn", grid_t[i] - 3 * 3600, grid_t[i] + 2 * 3600))
                break
        for event, w0, w1 in windows:
            if require_complete and ts[-1] < w1:
                continue                                   # window not fully seen yet: decide later
            sel = np.nonzero((ts >= w0) & (ts <= w1))[0]
            if len(sel) < 30:
                continue
            for T in thresholds:
                lt = np.log(T)
                cands = _crossings(ts[sel], lv[sel], lt, event, hold_min, gaps[sel[:-1]] if len(sel) > 1 else None,
                                   max_gap_min)
                if len(cands) != 1:
                    continue                               # none, or ambiguous (several sustained crossings)
                tc, slope = cands[0]
                if any(abs(tc - m["t"]) < 60 and m["series"] == f"{series_prefix}_{T:g}" for m in out):
                    continue
                out.append({"t": tc, "event": event, "series": f"{series_prefix}_{T:g}", "threshold": float(T),
                            "method": "luma_crossing", "slope_per_min": slope})
    return out


def _crossings(t, lv, lt, event, hold_min, gap_mask, max_gap_min):
    """All sustained crossings of log-level lt in the right direction: list of (time, dlog/dmin)."""
    below = lv < lt
    if event == "dusk":
        cand = np.nonzero(~below[:-1] & below[1:])[0]      # downward crossings
    else:
        cand = np.nonzero(below[:-1] & ~below[1:])[0]      # upward crossings
    out = []
    for i in cand:
        after = (t > t[i + 1]) & (t <= t[i + 1] + hold_min * 60)
        before = (t < t[i]) & (t >= t[i] - 10 * 60)
        if after.sum() < hold_min * 0.6 or before.sum() < 5:
            continue
        if event == "dusk" and (np.any(lv[after] > lt + 0.1) or np.any(lv[before] < lt - 0.1)):
            continue
        if event == "dawn" and (np.any(lv[after] < lt - 0.1) or np.any(lv[before] > lt + 0.1)):
            continue
        if gap_mask is not None:
            near = np.nonzero(np.abs(t[:-1] - t[i]) < max_gap_min * 60 * 2)[0]
            if np.any(gap_mask[near[near < len(gap_mask)]]):
                continue
        f = (lt - lv[i]) / (lv[i + 1] - lv[i])
        tc = t[i] + f * (t[i + 1] - t[i])
        slope = (lv[i + 1] - lv[i]) / ((t[i + 1] - t[i]) / 60.0)
        out.append((float(tc), float(slope)))
    return out


def ir_switch_markers(samples, approx=(61.25, 9.0), stable_min=10.0, settle_min=90.0, group_h=4.0):
    """Day/night (IR) mode switches -> markers. samples: iterable of (datetime|unix, ir_mode bool).

    A switch counts when the mode is stable for ``stable_min`` on both sides, the Sun at the approximate
    site is between -15 and +8 deg *and moving the right way* (to IR while it sinks = dusk, to day while
    it rises = dawn; a flap back to day mode in the evening is not a 'dawn'), and it is the only such
    switch within ``group_h`` hours (a camera flapping at the threshold under clouds gives no marker).
    Switches less than ``settle_min`` before the end of the data are left for a later call, when it is
    known whether more switches follow.
    """
    data = sorted((s[0].timestamp() if isinstance(s[0], datetime) else float(s[0]), bool(s[1])) for s in samples
                  if s[1] is not None)
    if len(data) < 10:
        return []
    t = np.array([d[0] for d in data])
    ir = np.array([d[1] for d in data])
    cand = []
    for i in np.nonzero(ir[1:] != ir[:-1])[0]:
        pre = (t >= t[i] - stable_min * 60) & (t <= t[i])
        post = (t > t[i + 1] - 1e-6) & (t <= t[i + 1] + stable_min * 60)
        if pre.sum() < 3 or post.sum() < 3 or np.any(ir[pre] != ir[i]) or np.any(ir[post] != ir[i + 1]):
            continue
        if t[i + 1] - t[i] > 180:
            continue
        cand.append((0.5 * (t[i] + t[i + 1]), "dusk" if ir[i + 1] else "dawn"))
    if not cand:
        return []
    tc = np.array([c[0] for c in cand])
    _, h = ephem.altaz_grid(ephem.body_places("sun", list(tc)), [approx[0]], [approx[1]])
    _, h2 = ephem.altaz_grid(ephem.body_places("sun", list(tc + 300.0)), [approx[0]], [approx[1]])
    h, rising = h[0], (h2 - h)[0] > 0
    ok = [(-15.0 < h[k] < 8.0) and (rising[k] == (cand[k][1] == "dawn")) for k in range(len(cand))]
    out = []
    for k, (tk, event) in enumerate(cand):
        if not ok[k] or t[-1] - tk < settle_min * 60:
            continue
        rivals = [j for j in range(len(cand)) if j != k and ok[j] and cand[j][1] == event
                  and abs(cand[j][0] - tk) < group_h * 3600]
        if rivals:
            continue
        out.append({"t": float(tk), "event": event, "series": "ir_switch", "threshold": None, "method": "ir_mode"})
    return out
