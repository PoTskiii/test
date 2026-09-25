"""Model averaging over competing readings of the uncertain evidence.

Several hints admit different readings (pickup Sunday or Monday? is «2,7
eiffeltårn» an elevation? did the car come from the SE?). Instead of betting
on one, we build the posterior under each scenario and average them with
scenario weights (Bayesian model averaging). Spots that stay high across
scenarios are robust; spots that only win under one reading are fragile.

    .venv/bin/python -m hordejakt.scenarios
"""
import copy
import json

import numpy as np

from . import OUTPUT
from .fusion import apply_overrides, build_layers, credible_area_km2, fuse, hotspots, posterior
from .grid import GRID
from .layers import travel

BASE = {"p_monday_pickup": 0.5, "defaultno_variant": "utenfly"}

# (name, weight, cfg-delta). 'reliability' deltas override layer reliabilities.
SCENARIOS = [
    ("base", 3.0, {}),
    ("elevation_literal", 1.5, {"reliability": {"elevation_band_810_891": 0.9}}),
    ("elevation_not_elevation", 1.5, {"reliability": {"elevation_band_810_891": 0.05}}),
    ("monday_pickup", 1.0, {"p_monday_pickup": 0.95, "reliability": {"drive_time_from_oslo": 0.6}}),
    ("sunday_pickup", 1.0, {"p_monday_pickup": 0.05}),
    ("no_organizer_prior", 0.75, {"reliability": {"organizer_region_prior": 0.05}}),
    ("no_se_approach", 1.0, {"reliability": {"road_to_southeast": 0.05}}),
    ("aircraft_strong", 1.0, {"reliability": {"aircraft_2109_2129_point": 0.9, "aircraft_2209_2034_follow": 0.85,
                                              "aircraft_2209_2032_flyy": 0.6, "aircraft_2509_1722_point": 0.6}}),
    ("aircraft_weak", 1.0, {"reliability": {"aircraft_2109_2129_point": 0.4, "aircraft_2209_2034_follow": 0.35,
                                            "aircraft_2209_2032_flyy": 0.2, "aircraft_2509_1722_point": 0.2}}),
    ("no_defaultno", 1.0, {"skip_layers": ["defaultno_fusion_utenfly"]}),
    ("forest_strong", 0.75, {"reliability": {"forest_species_mix": 0.85}}),
]


def run(top=40, write=True):
    base_layers = build_layers(GRID, BASE)
    travel_cache = {}
    posts, meta = [], []
    for name, w, delta in SCENARIOS:
        cfg = {**copy.deepcopy(BASE), **{k: v for k, v in delta.items() if k not in ("reliability", "skip_layers")}}
        layers = list(base_layers)
        if cfg.get("p_monday_pickup") != BASE["p_monday_pickup"]:
            key = cfg["p_monday_pickup"]
            if key not in travel_cache:
                travel_cache[key] = travel.build(GRID, cfg)
            layers = [L for L in layers if L.independence_group != "travel"] + travel_cache[key]
        layers = apply_overrides(layers, delta)
        lp, _ = fuse(layers)
        p = posterior(lp)
        posts.append(p)
        meta.append({"name": name, "weight": w, "credible_km2_50": round(credible_area_km2(GRID, p, 0.5), 1)})
    W = np.array([m["weight"] for m in meta])
    avg = np.tensordot(W / W.sum(), np.stack(posts), axes=1)
    spots = hotspots(GRID, avg, n=top)
    # stability: rank of each averaged spot's 1.5 km mass under every scenario
    for s in spots:
        i, j = GRID.index(s["lat"], s["lon"])
        s["scenario_p_cell_ratio"] = {m["name"]: round(float(p[i, j] / avg[i, j]), 2) for m, p in zip(meta, posts)}
        s["fragility"] = round(float(np.std(np.log([max(v, 1e-6) for v in s["scenario_p_cell_ratio"].values()]))), 2)
    out = {"scenarios": meta, "credible_km2": {str(q): round(credible_area_km2(GRID, avg, q), 1) for q in (0.5, 0.8, 0.9)},
           "hotspots": spots}
    if write:
        OUTPUT.mkdir(exist_ok=True)
        (OUTPUT / "scenario_hotspots.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
        np.savez_compressed(OUTPUT / "posterior_bma.npz", post=avg.astype(np.float32))
    return avg, out


if __name__ == "__main__":
    avg, out = run()
    print(json.dumps(out["scenarios"]), json.dumps(out["credible_km2"]))
    for k, s in enumerate(out["hotspots"][:20], 1):
        print(f"{k:2d} {s['lat']:.4f},{s['lon']:.4f} p1.5km={s['p_within_1.5km']:.4f} fragility={s['fragility']}")
