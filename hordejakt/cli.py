"""Run the engine:  .venv/bin/python -m hordejakt.cli [--config cfg.json] [--top 40]

Writes output/posterior.npz, output/hotspots.json/.csv, output/layers.json and
output/map.html.
"""
import argparse
import csv
import json
import time

import numpy as np

from . import OUTPUT
from .fusion import build_layers, credible_area_km2, fuse, hotspots, posterior
from .grid import GRID

_TO_UTM33 = None


def map_links(lat, lon):
    """Norgeskart takes EPSG:25833 northing/easting in its lat/lon URL parameters."""
    global _TO_UTM33
    if _TO_UTM33 is None:
        from pyproj import Transformer
        _TO_UTM33 = Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True)
    e, n = _TO_UTM33.transform(lon, lat)
    nk = (f"https://norgeskart.no/#!?project=norgeskart&layers=1002&zoom=14&lat={n:.0f}&lon={e:.0f}"
          f"&markerLat={n:.0f}&markerLon={e:.0f}")
    gm = f"https://www.google.com/maps/search/?api=1&query={lat:.5f},{lon:.5f}"
    return nk, gm


DEFAULT_CFG = {"p_monday_pickup": 0.5, "defaultno_variant": "utenfly"}


def run(cfg, top=40, min_sep_km=2.0, skip=(), quiet=False, write=True):
    t = time.time()
    layers = build_layers(GRID, cfg, skip=skip)
    lp, contrib = fuse(layers)
    post = posterior(lp)
    spots = hotspots(GRID, post, n=top, min_sep_km=min_sep_km)
    for s in spots:
        i, j = GRID.index(s["lat"], s["lon"])
        s["groups"] = {g: round(float(v[i, j]), 2) for g, v in contrib.items()}
        s["norgeskart"], s["google_maps"] = map_links(s["lat"], s["lon"])
    summary = {
        "credible_km2": {str(q): round(credible_area_km2(GRID, post, q), 1) for q in (0.5, 0.8, 0.9)},
        "layers": [{"name": L.name, "group": L.independence_group, "reliability": L.reliability,
                    "description": L.description, "sources": L.sources} for L in layers],
        "cfg": cfg, "seconds": round(time.time() - t, 1),
    }
    if write:
        OUTPUT.mkdir(exist_ok=True)
        np.savez_compressed(OUTPUT / "posterior.npz", post=post.astype(np.float32), lat_min=GRID.lat_min,
                            lon_min=GRID.lon_min, dlat=GRID.dlat, dlon=GRID.dlon)
        (OUTPUT / "hotspots.json").write_text(json.dumps({"summary": summary, "hotspots": spots}, indent=1, ensure_ascii=False))
        with open(OUTPUT / "hotspots.csv", "w", newline="") as f:
            w = csv.writer(f)
            groups = sorted(contrib)
            w.writerow(["rank", "lat", "lon", "p_cell", "p_within_1.5km"] + groups + ["norgeskart"])
            for k, s in enumerate(spots, 1):
                w.writerow([k, f"{s['lat']:.4f}", f"{s['lon']:.4f}", f"{s['p_cell']:.3e}", f"{s['p_within_1.5km']:.4f}"]
                           + [s["groups"][g] for g in groups] + [s["norgeskart"]])
        from .report import write_map
        write_map(GRID, post, spots, OUTPUT / "map.html", summary)
    if not quiet:
        print(json.dumps(summary["credible_km2"]), f"{summary['seconds']} s")
        for k, s in enumerate(spots[:15], 1):
            worst = sorted(s["groups"].items(), key=lambda kv: kv[1])[:3]
            print(f"{k:2d} {s['lat']:.4f},{s['lon']:.4f} p1.5km={s['p_within_1.5km']:.4f}  weakest: {worst}")
    return post, spots, summary, layers, contrib


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--skip", nargs="*", default=[])
    a = ap.parse_args()
    cfg = dict(DEFAULT_CFG)
    if a.config:
        cfg.update(json.load(open(a.config)))
    cfg["skip"] = a.skip
    run(cfg, top=a.top, skip=a.skip)


if __name__ == "__main__":
    main()
