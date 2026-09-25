"""Combine layers into a posterior and extract ranked search areas."""
import importlib
from collections import defaultdict

import numpy as np

from .geo import haversine
from .layers import LAYER_MODULES
from .layers.base import LayerResult


def build_layers(grid, cfg, only=None, skip=()):
    """Build every layer module; cfg['reliability'] = {layer_name: r} overrides
    reliabilities and cfg['skip_layers'] drops individual layers by name."""
    layers = []
    for mod in LAYER_MODULES:
        short = mod.rsplit(".", 1)[1]
        if (only and short not in only) or short in skip:
            continue
        m = importlib.import_module(mod)
        res = m.build(grid, cfg)
        layers.extend(res if isinstance(res, list) else [res])
    return apply_overrides(layers, cfg)


def apply_overrides(layers, cfg):
    rel = cfg.get("reliability", {})
    drop = set(cfg.get("skip_layers", ()))
    out = []
    for L in layers:
        if L.name in drop:
            continue
        if L.name in rel:
            L = LayerResult(**{**L.__dict__, "reliability": rel[L.name]})
        out.append(L)
    return out


def fuse(layers, weights=None):
    """Sum robust log-likelihoods across independence groups; average inside a group.

    weights: optional {layer_name: multiplier} for sensitivity analysis.
    Returns (log_posterior, per-group contributions).
    """
    weights = weights or {}
    groups = defaultdict(list)
    for L in layers:
        groups[L.independence_group].append(L)
    # search domain = cells allowed by every hard layer (Norwegian land)
    domain = None
    for L in layers:
        if L.hard:
            ok = ~np.isneginf(np.asarray(L.loglik, float))
            domain = ok if domain is None else (domain & ok)
    total = None
    contrib = {}
    for g, ls in groups.items():
        w = np.array([max(L.reliability, 1e-3) for L in ls])
        stack = np.stack([L.robust(domain) * weights.get(L.name, 1.0) for L in ls])
        # hard exclusions survive the averaging
        hard = np.isneginf(stack).any(axis=0)
        s = np.where(np.isneginf(stack), 0.0, stack)
        g_ll = np.tensordot(w / w.sum(), s, axes=1)
        g_ll = np.where(hard, -np.inf, g_ll)
        contrib[g] = g_ll
        total = g_ll if total is None else total + g_ll
    return total, contrib


def posterior(logpost):
    lp = np.where(np.isfinite(logpost), logpost, -np.inf)
    m = np.max(lp)
    p = np.exp(lp - m)
    return p / p.sum()


def hotspots(grid, post, n=40, min_sep_km=2.0, mass_radius_km=1.5):
    """Greedy non-maximum suppression over cells; mass within radius per spot."""
    flat = np.argsort(post, axis=None)[::-1]
    lats, lons = grid.lats, grid.lons
    picks = []
    for idx in flat[: 200000]:
        i, j = np.unravel_index(idx, post.shape)
        la, lo = lats[i], lons[j]
        if any(haversine(la, lo, p["lat"], p["lon"]) < min_sep_km for p in picks):
            continue
        picks.append({"lat": float(la), "lon": float(lo), "p_cell": float(post[i, j])})
        if len(picks) >= n:
            break
    L, O = grid.mesh()
    for p in picks:
        # local window for speed
        di = int(mass_radius_km / 111 / grid.dlat) + 2
        dj = int(mass_radius_km / (111 * np.cos(np.radians(p["lat"]))) / grid.dlon) + 2
        i, j = grid.index(p["lat"], p["lon"])
        sl = (slice(max(i - di, 0), i + di + 1), slice(max(j - dj, 0), j + dj + 1))
        d = haversine(p["lat"], p["lon"], L[sl], O[sl])
        p["p_within_%gkm" % mass_radius_km] = float(post[sl][d <= mass_radius_km].sum())
    return picks


def credible_area_km2(grid, post, q):
    """Area of the smallest set of cells holding probability mass q."""
    s = np.sort(post, axis=None)[::-1]
    k = int(np.searchsorted(np.cumsum(s), q)) + 1
    lat_c = np.radians(np.mean(grid.lats))
    cell_km2 = (grid.dlat * 111.2) * (grid.dlon * 111.2 * np.cos(lat_c))
    return k * cell_km2
