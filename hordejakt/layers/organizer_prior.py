"""Organizer-behaviour prior from Horde's earlier hunts (evidence/sources/prior_years_early.md).

2023: Tokke, Vest-Telemark (found day 6). 2024: near the Kongsberg silver
mines, Buskerud (found day 6). Both: forest, 1.5-4 h by car from Oslo, 5-7 h
from Bergen, walkable off-trail within earshot of a road; no 2025 hunt.
Elicited regional prior (research agent, judgement from two data points):
  Innlandet 0.35 · Buskerud/Telemark/Vestfold/inland Agder 0.30 ·
  Akershus/Østfold 0.07 · Vestland/Rogaland 0.10 · Trøndelag/Møre 0.13 · north 0.05
Regions are approximated with coarse polygons (Innlandet exact from
innlandet.json, the rest as lat/lon boxes); the layer converts regional mass
to a per-area density so large regions are not favoured for their size.
"""
import json

import numpy as np
from shapely import contains_xy
from shapely.geometry import box, shape

from .. import MAGNUS
from .base import LayerResult

REGION_MASS = {
    "innlandet": 0.35,
    "south_east_inland": 0.30,   # Buskerud, Telemark, Vestfold, inland Agder
    "akershus_ostfold": 0.07,
    "west": 0.10,                # Vestland, Rogaland, coastal Agder west
    "mid": 0.13,                 # Trøndelag, Møre og Romsdal
}


def region_masks(grid):
    L, O = grid.mesh()
    inn = shape(json.load(open(MAGNUS / "public" / "data" / "innlandet.json"))["geometry"])
    m_inn = contains_xy(inn, O, L)
    rest = ~m_inn
    mid = rest & (L >= 62.0)
    west = rest & ~mid & (O < 7.3)
    ak_os = rest & ~mid & ~west & (L < 60.45) & (O >= 10.45)
    se_in = rest & ~mid & ~west & ~ak_os & (L < 62.0)
    return {"innlandet": m_inn, "south_east_inland": se_in, "akershus_ostfold": ak_os, "west": west, "mid": mid}


def build(grid, cfg):
    masks = region_masks(grid)
    ll = grid.empty(np.nan)
    for name, m in masks.items():
        n = int(m.sum())
        if n:
            ll[m] = np.log(REGION_MASS[name] / n)  # per-cell density
    return [LayerResult("organizer_region_prior", ll, reliability=float(cfg.get("organizer_prior_reliability", 0.6)),
                        independence_group="organizer_prior",
                        description="Regional prior from Horde's 2023 (Tokke) and 2024 (Kongsberg) hunts; eastern/inland Norway favoured",
                        sources=["evidence/sources/prior_years_early.md"])]
