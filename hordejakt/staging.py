"""Where to wait: pick the staging town that minimises expected travel time to
the box under the current posterior, and how much probability each town can
reach within 30/60/90 min. Being first after a decisive weekend hint is
mostly a function of where you are when it drops.

Travel time model (no routing offline): road distance ≈ 1.35 × great-circle,
average 65 km/h on the way plus the cell's walk (~10 min). Replace with OSRM
(`router.project-osrm.org`) when network access is available.

    .venv/bin/python -m hordejakt.staging [--posterior output/posterior_bma.npz]
"""
import argparse
import json

import numpy as np

from . import OUTPUT
from .geo import haversine
from .grid import GRID

TOWNS = {
    "Elverum": (60.881, 11.562), "Rena": (61.133, 11.367), "Koppang": (61.572, 11.041),
    "Evenstad": (61.420, 11.078), "Løten": (60.817, 11.338), "Hamar": (60.795, 11.068),
    "Brumunddal": (60.881, 10.940), "Moelv": (60.931, 10.700), "Sjusjøen": (61.036, 10.730),
    "Lillehammer": (61.115, 10.466), "Atna": (61.740, 10.822), "Tynset": (62.276, 10.781),
    "Rendalen (Bergset)": (61.868, 11.071), "Trysil": (61.314, 12.263), "Kongsvinger": (60.190, 11.998),
    "Flisa": (60.614, 12.013), "Stange": (60.715, 11.190), "Ringebu": (61.529, 10.140),
    "Otta": (61.772, 9.537), "Gjøvik": (60.795, 10.692), "Oslo": (59.914, 10.752),
}
DETOUR, SPEED_KMH, WALK_H = 1.35, 65.0, 10 / 60


def travel_h(lat, lon, L, O):
    return haversine(lat, lon, L, O) * DETOUR / SPEED_KMH + WALK_H


def evaluate(post, top_mass=0.995):
    # restrict to the cells holding most of the mass for speed
    flat = np.argsort(post, axis=None)[::-1]
    c = np.cumsum(post.ravel()[flat])
    k = int(np.searchsorted(c, top_mass)) + 1
    idx = np.unravel_index(flat[:k], post.shape)
    p = post[idx] / post[idx].sum()
    L, O = GRID.lats[idx[0]], GRID.lons[idx[1]]
    rows = []
    for name, (la, lo) in TOWNS.items():
        t = travel_h(la, lo, L, O)
        rows.append({"town": name, "lat": la, "lon": lo, "expected_h": round(float((p * t).sum()), 2),
                     "p_within_30min": round(float(p[t <= 0.5].sum()), 3),
                     "p_within_60min": round(float(p[t <= 1.0].sum()), 3),
                     "p_within_90min": round(float(p[t <= 1.5].sum()), 3)})
    rows.sort(key=lambda r: r["expected_h"])
    # continuous optimum (weighted geometric median of travel time ~ distance)
    x = np.array([np.average(L, weights=p), np.average(O, weights=p)])
    for _ in range(100):
        d = np.maximum(haversine(x[0], x[1], L, O), 0.05)
        w = p / d
        x = np.array([np.sum(w * L) / w.sum(), np.sum(w * O) / w.sum()])
    t = travel_h(x[0], x[1], L, O)
    best = {"lat": round(float(x[0]), 4), "lon": round(float(x[1]), 4), "expected_h": round(float((p * t).sum()), 2),
            "p_within_60min": round(float(p[t <= 1.0].sum()), 3)}
    return rows, best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posterior", default=str(OUTPUT / "posterior_bma.npz"))
    a = ap.parse_args()
    post = np.load(a.posterior)["post"].astype(float)
    rows, best = evaluate(post / post.sum())
    (OUTPUT / "staging.json").write_text(json.dumps({"towns": rows, "optimum": best}, indent=1, ensure_ascii=False))
    print("optimum (geometric median):", best)
    for r in rows[:10]:
        print(f"{r['town']:20s} E[t]={r['expected_h']:.2f} h  P(<=30m)={r['p_within_30min']:.2f}  "
              f"P(<=60m)={r['p_within_60min']:.2f}  P(<=90m)={r['p_within_90min']:.2f}")


if __name__ == "__main__":
    main()
