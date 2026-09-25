"""Travel from Oslo: picked up in Oslo 04:00, car only (no ferry), windows covered.

The stream started Monday 21.09 ~06:50. Whiteboard says she was picked up on
*Sunday*, Børsen says she has been in the box «since Monday morning».
  * Monday pickup  -> drive + walk + setup <= ~2 h 50 min -> drive <~ 2.5 h
  * Sunday pickup  -> she guessed ~7 h but slept most of the way: broad 1-8.5 h
Mixture weighted by cfg['p_monday_pickup'] (default 0.5).
Alf (Børsen/TikTok 25.09): she was driven around for hours on purpose, then
carried into the forest -> drive time is weak evidence (reliability 0.3).

Source: MagnusPladsen drivetime.json — OSRM car time from Oslo sentrum on a
0.1° x 0.2° lattice (fields lat, lon, sek, meter, snap_m).
"""
import json

import numpy as np
from scipy.interpolate import griddata

from .. import MAGNUS
from .base import LayerResult


def build(grid, cfg):
    d = json.load(open(MAGNUS / "public" / "data" / "drivetime.json"))
    a = np.array(d["punkter"], float)
    lat, lon, sek, snap = a[:, 0], a[:, 1], a[:, 2], a[:, 4]
    ok = snap < 5000  # lattice points far from any road are unreliable
    L, O = grid.mesh()
    hours = griddata((lat[ok], lon[ok]), sek[ok] / 3600.0, (L, O), method="linear")
    p_mon = float(cfg.get("p_monday_pickup", 0.5))
    h = np.where(np.isnan(hours), 12.0, hours)
    # Monday: drive <= 2.5 h (soft edge 20 min)
    mon = 1.0 / (1.0 + np.exp((h - 2.5) / 0.33))
    # Sunday: plausible 1-8.5 h, mild preference around her ~7 h guess is not trusted (she slept)
    sun = 1.0 / (1.0 + np.exp((h - 8.5) / 0.5)) * 1.0 / (1.0 + np.exp((1.0 - h) / 0.3))
    lik = p_mon * mon / 2.5 + (1 - p_mon) * sun / 7.5  # normalise each hypothesis by its width
    ll = np.log(lik + 1e-6)
    ll = np.where(np.isnan(hours), np.nan, ll)
    return [LayerResult("drive_time_from_oslo", ll, reliability=float(cfg.get("travel_reliability", 0.3)), independence_group="travel",
                        description=f"OSRM drive time from Oslo; mixture Monday-pickup (<=2.5 h) p={p_mon} / Sunday-pickup (1-8.5 h)",
                        sources=["tavla: hentet i Oslo kl 04:00 (søndag)", "Børsen: «siden mandag morgen»", "OSRM via drivetime.json"])]
