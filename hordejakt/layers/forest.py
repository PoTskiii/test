"""Forest composition: «KANSKJE 35% BJØRK, 25% GRAN, 40% FURU. AKKURAT RUNDT MEG» (tavla 25.09 18:13)
and mature pine on blueberry heath (stream image).

Source: MagnusPladsen treslag.json — NIBIO SR16 dominant-species shares per
0.02° x 0.04° cell with a similarity score 0.55-0.98 to (pine .40, spruce .25,
deciduous .35). Cells in the covered rectangle but absent from the file scored
below 0.55 (or are not forest).
"""
import json

import numpy as np

from .. import MAGNUS
from .base import LayerResult

K = 5.0  # log-likelihood per unit similarity
ABSENT_SCORE = 0.45


def build(grid, cfg):
    d = json.load(open(MAGNUS / "public" / "data" / "treslag.json"))
    a = np.array(d["celler"], float)
    lat, lon, score = a[:, 0], a[:, 1], a[:, 2]
    ll_cells = K * (score - 1.0)
    ll = grid.paint_blocks(lat, lon, d["dlat"], d["dlon"], ll_cells, fill=np.nan)
    L, O = grid.mesh()
    rect = (L >= lat.min() - d["dlat"] / 2) & (L <= lat.max() + d["dlat"] / 2) & \
           (O >= lon.min() - d["dlon"] / 2) & (O <= lon.max() + d["dlon"] / 2)
    ll = np.where(np.isnan(ll) & rect, K * (ABSENT_SCORE - 1.0), ll)
    covered = rect
    fill = np.log(np.mean(np.exp(ll[covered]))) if covered.any() else 0.0
    ll = np.where(np.isnan(ll), fill, ll)
    return [LayerResult("forest_species_mix", ll, reliability=0.55, independence_group="forest_species",
                        description="SR16 species-share similarity to 40% pine / 25% spruce / 35% birch (her estimate 'right around me')",
                        sources=["tavla 25.09 18:13", "NIBIO SR16 via MagnusPladsen treslag.json"])]
