"""default.no's own fused probability grid, used as ONE low-reliability input.

default.no publishes several variants under fusjon/*.json; each is a
run-length-encoded class grid: lop = [i, j, len, k, ...] meaning cells
(lat0 + i*dlat, lon0 + (j..j+len-1)*dlon) have class k (3 = best 2 %,
2 = top 15 %, 1 = top 40 %; unlisted = rest). We use the 'utenfly' variant
(everything except the aircraft evidence) so it does not double count our own
aircraft layer; its weather/satellite/rain evidence is otherwise not
reproducible offline.
"""
import json

import numpy as np

from .. import DEFAULTNO
from .base import LayerResult

CLASS_LL = {3: 0.0, 2: -0.8, 1: -1.8, 0: -3.0}


def decode_rle(d, grid, fill=0):
    """Return an int class array on `grid` from a default.no lop grid."""
    cls = np.full(grid.shape, fill, dtype=int)
    lop = d["lop"]
    lat0, dlat, lon0, dlon = d["lat0"], d["dlat"], d["lon0"], d["dlon"]
    L, O = grid.mesh()
    ci = np.rint((L - lat0) / dlat).astype(int)
    cj = np.rint((O - lon0) / dlon).astype(int)
    coarse = {}
    for n in range(0, len(lop) - 3, 4):
        i, j, ln, k = lop[n:n + 4]
        for jj in range(j, j + ln):
            coarse[(i, jj)] = k
    if not coarse:
        return cls
    imax = max(i for i, _ in coarse) + 2
    jmax = max(j for _, j in coarse) + 2
    lut = np.full((imax, jmax), fill, dtype=int)
    for (i, j), k in coarse.items():
        lut[i, j] = k
    ok = (ci >= 0) & (ci < imax) & (cj >= 0) & (cj < jmax)
    cls[ok] = lut[ci[ok], cj[ok]]
    return cls


def build(grid, cfg):
    variant = cfg.get("defaultno_variant", "utenfly")
    d = json.load(open(DEFAULTNO / "fusjon" / f"{variant}.json"))
    cls = decode_rle(d, grid)
    ll = np.vectorize(CLASS_LL.get)(cls).astype(float)
    return [LayerResult(f"defaultno_fusion_{variant}", ll, reliability=0.4, independence_group="defaultno_model",
                        description=f"default.no fused model '{variant}' ({d.get('oppdatert')}); evidence: {', '.join(d.get('bevis') or [])}",
                        sources=["default.no fusjon (mirror 24.09 18:36)"])]
