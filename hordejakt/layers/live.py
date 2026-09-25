"""Evidence produced continuously by hordewatch (astro fixes, aircraft matches,
weather matches ...). Each file data/hordewatch/layers/<name>.npz holds
`loglik` on the analysis grid (or on a sub-grid given by lat_min/lon_min/dlat/dlon)
and `meta` (JSON: name, reliability, independence_group, description, sources).
"""
import json

import numpy as np

from .. import ROOT
from .base import LayerResult

LIVE_DIR = ROOT / "data" / "hordewatch" / "layers"


def build(grid, cfg):
    out = []
    if not LIVE_DIR.exists():
        return out
    for p in sorted(LIVE_DIR.glob("*.npz")):
        d = np.load(p, allow_pickle=False)
        meta = json.loads(str(d["meta"]))
        ll = d["loglik"].astype(float)
        if ll.shape != grid.shape:
            # sub-grid: paste into a full NaN grid
            full = grid.empty()
            i0, j0 = grid.index(float(d["lat_min"]), float(d["lon_min"]))
            if i0 < 0 or j0 < 0:
                continue
            h = min(ll.shape[0], grid.nlat - i0)
            w = min(ll.shape[1], grid.nlon - j0)
            full[i0:i0 + h, j0:j0 + w] = ll[:h, :w]
            ll = full
        out.append(LayerResult(meta["name"], ll, float(meta.get("reliability", 0.5)),
                               meta.get("independence_group", meta["name"]), meta.get("description", ""),
                               meta.get("sources", [])))
    return out
