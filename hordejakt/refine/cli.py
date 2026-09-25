"""Refine the coarse hotspots to 1-10 m candidate spots and write a field plan.

    .venv/bin/python -m hordejakt.refine.cli --hotspots output/hotspots.json --top 15 --radius-km 1.5

For each of the top hotspots: fetch (cached) DTM, DOM, OSM and optionally SR16
around the cell, score every pixel (hordejakt/refine/score.py), pick candidate
box positions with their best parking spot, and combine

    p_i = P(hotspot region)  x  P(spot i | region)

where P(region) is the coarse engine's ``p_within_1.5km`` and P(spot | region)
the refined pixel posterior mass of a 25 m search disc around the spot.

Outputs (in --out-dir, default output/):
  refined_candidates.json / .csv   every candidate with lat/lon, parking, walk, reasons
  field_plan.md                    stops ordered greedily by p * P(detect) / (drive + walk + search)

If data hosts are blocked the command prints which hosts must be allowed and
exits with status 2 (tiles already in data/cache/ are still processed).
"""
import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .. import OUTPUT
from ..geo import haversine
from . import fetch, score
from .raster import bbox_around, to_utm

CSV_COLS = ["rank", "p_abs", "p_share_pct", "p_in_tile", "score", "lat", "lon", "elevation_m", "road_distance_m",
            "nearest_road", "parking_lat", "parking_lon", "parking_road", "walk_distance_m", "walk_time_min", "climb_m",
            "bearing_car_to_box_true", "bearing_car_to_box_magnetic", "bearing_box_to_car_true", "direction_hypothesis",
            "dist_water_osm_m", "dist_stream_dtm_m", "dist_building_m", "dist_trafficked_road_m", "dist_path_m",
            "slope_deg", "canopy_at_spot_m", "canopy_ring_m", "terrain_sunrise_local", "hotspot_rank", "hotspot_lat",
            "hotspot_lon", "data", "google_maps", "google_directions_parking", "norgeskart", "reasons"]


def links(lat, lon, plat=None, plon=None):
    x, y = (float(v) for v in to_utm(lat, lon))
    out = {"google_maps": f"https://www.google.com/maps/search/?api=1&query={lat:.6f},{lon:.6f}",
           # norgeskart.no takes EPSG:25833 northing/easting in its lat/lon parameters
           "norgeskart": (f"https://norgeskart.no/#!?project=norgeskart&layers=1002&zoom=16&lat={y:.2f}&lon={x:.2f}"
                          f"&markerLat={y:.2f}&markerLon={x:.2f}"),
           "geo": f"geo:{lat:.6f},{lon:.6f}"}
    if plat is not None:
        out["google_directions_parking"] = (f"https://www.google.com/maps/dir/?api=1&destination={plat:.6f},{plon:.6f}"
                                            f"&travelmode=driving")
    return out


def load_hotspots(path, top):
    d = json.load(open(path))
    spots = d["hotspots"] if isinstance(d, dict) else d
    out = []
    for k, s in enumerate(spots[:top], 1):
        p = s.get("p_within_1.5km", s.get("p_cell", 1.0))
        out.append({"rank": k, "lat": float(s["lat"]), "lon": float(s["lon"]), "p_region": float(p)})
    return out


def process_hotspot(h, a, status):
    """Fetch + score one hotspot. Returns (candidate records, tile info)."""
    bbox = bbox_around(h["lat"], h["lon"], a.radius_km * 1000.0)
    tile = {"hotspot_rank": h["rank"], "lat": h["lat"], "lon": h["lon"], "bbox_25833": [round(v) for v in bbox],
            "data": {}, "notes": []}

    def get(name, fn, *args, required=False, **kw):
        try:
            v = fn(*args, **kw)
            tile["data"][name] = getattr(v, "source", None) or (v.get("source") if isinstance(v, dict) else "ok") or "ok"
            return v
        except fetch.FetchBlocked as exc:
            status["blocked"].update(exc.hosts)
            tile["data"][name] = "blocked: " + ", ".join(exc.hosts)
        except fetch.FetchError as exc:
            tile["data"][name] = f"error: {str(exc)[:200]}"
        if required:
            raise _Skip(name)
        return None

    try:
        dtm = get("dtm", fetch.dtm_tile, bbox, a.res, required=True)
    except _Skip:
        tile["status"] = "skipped (no DTM)"
        return [], tile
    dom = None if a.no_dom else get("dom", fetch.dom_tile, bbox, a.res)
    osm = get("osm", fetch.osm_features, bbox)
    if osm is None:
        tile["notes"].append("no OSM: roads/water/buildings unknown - parking, walk and distance clues are missing")
    hz = None
    if a.horizon_km and a.horizon_km * 1000 > a.radius_km * 1000:
        hz = get("horizon_dtm", fetch.dtm_tile, bbox_around(h["lat"], h["lon"], a.horizon_km * 1000.0), 10.0,
                 points_fallback=False)
    t0 = time.time()
    ts, cands = score.score_tile(dtm, dom=dom, osm=osm, work_res=a.work_res, n_out=a.per_tile, n_pool=a.pool,
                                 min_sep_m=a.min_sep, horizon_rasters=[hz] if hz is not None else None)
    tile["score_seconds"] = round(time.time() - t0, 1)
    tile["missing"] = ts.missing
    if not a.no_sr16 and cands:
        pts = [(c["x"], c["y"]) for c in cands]
        sr = get("sr16", fetch.sr16, bbox, points=pts)
        if sr and sr.get("points"):
            vals = []
            for c, rec in zip(cands, sr["points"]):
                v, sp = score.sr16_point_ll(rec)
                vals.append(v if (rec.get("species") is not None or rec.get("height") is not None) else None)
                c["info"]["sr16_species"], c["info"]["sr16_height"] = sp, rec.get("height")
            score.apply_point_term(cands, "sr16_point", vals)
            for c in cands:
                c["reasons"] = score.reasons(c, ts.missing, ts.meta["params"])
            tile["notes"] += sr.get("notes", [])[:5]
    recs = []
    for c in cands:
        r = score.candidate_record(c)
        r.update({"hotspot_rank": h["rank"], "hotspot_lat": h["lat"], "hotspot_lon": h["lon"], "p_region": h["p_region"],
                  "p_abs": h["p_region"] * (c.get("p_in_tile") or 0.0), "data": dict(tile["data"])})
        pk = r.get("parking") or {}
        r["links"] = links(r["lat"], r["lon"], pk.get("lat"), pk.get("lon"))
        recs.append(r)
    tile["status"] = "ok"
    tile["n_candidates"] = len(recs)
    return recs, tile


class _Skip(Exception):
    pass


def dedupe(recs, min_m=50.0):
    """Drop candidates within min_m of a better one (tiles overlap)."""
    keep = []
    for r in sorted(recs, key=lambda r: r["p_abs"], reverse=True):
        if all(haversine(r["lat"], r["lon"], k["lat"], k["lon"]) * 1000 >= min_m for k in keep):
            keep.append(r)
    return keep


def plan(recs, start=None, search_min=10.0, drive_kmh=45.0, pd=0.9, hours=10.0, max_stops=40):
    """Greedy search-theory order: maximise p * pd / (drive + round-trip walk + search) at each step."""
    remaining = list(recs[: max(max_stops * 3, max_stops)])
    pos = start
    t_used, p_cum, stops = 0.0, 0.0, []
    while remaining and len(stops) < max_stops and t_used < hours * 60:
        best, best_rate, best_t = None, -1.0, None
        for r in remaining:
            pk = r.get("parking")
            tgt = (pk["lat"], pk["lon"]) if pk else (r["lat"], r["lon"])
            if pos is None:
                drive = 0.0
            else:
                km = float(haversine(pos[0], pos[1], tgt[0], tgt[1]))
                drive = 0.0 if km < 0.15 else km * 1.4 / drive_kmh * 60 + 3.0
            walk = 2 * (r.get("walk_time_min") or ((r.get("road_distance_m") or 1000) / 50.0))
            t = drive + walk + search_min
            rate = r["p_abs"] * pd / t
            if rate > best_rate:
                best, best_rate, best_t = r, rate, (drive, walk, t)
        remaining.remove(best)
        pk = best.get("parking")
        pos = (pk["lat"], pk["lon"]) if pk else (best["lat"], best["lon"])
        t_used += best_t[2]
        p_cum += best["p_abs"] * pd
        stops.append({"rec": best, "drive_min": best_t[0], "walk_rt_min": best_t[1], "total_min": best_t[2],
                      "p_per_hour": best_rate * 60, "t_cum_min": t_used, "p_cum": p_cum})
    return stops


def write_outputs(out_dir, recs, tiles, stops, args, host_status):
    out_dir.mkdir(parents=True, exist_ok=True)
    tot = sum(r["p_abs"] for r in recs) or 1.0
    for k, r in enumerate(recs, 1):
        r["rank"] = k
        r["p_share_pct"] = round(100 * r["p_abs"] / tot, 2)
    meta = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "args": vars(args),
            "hosts": host_status, "tiles": tiles,
            "model": "p_abs = P(hotspot region, coarse engine p_within_1.5km) x P(25 m disc | region, refined)",
            "terms": {k: {"reliability": v[0], "weight": v[1], "stage": v[2]} for k, v in score.TERMS.items()}}
    (out_dir / "refined_candidates.json").write_text(json.dumps({"meta": meta, "candidates": recs}, indent=1,
                                                                ensure_ascii=False, default=_js))
    with open(out_dir / "refined_candidates.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(CSV_COLS)
        for r in recs:
            pk = r.get("parking") or {}
            row = dict(r, parking_lat=pk.get("lat"), parking_lon=pk.get("lon"), parking_road=pk.get("road"),
                       google_maps=r["links"]["google_maps"], norgeskart=r["links"]["norgeskart"],
                       google_directions_parking=r["links"].get("google_directions_parking"),
                       data=";".join(f"{k}={v}" for k, v in r.get("data", {}).items()),
                       reasons=" | ".join(r.get("reasons", [])))
            w.writerow([_fmt(row.get(c)) for c in CSV_COLS])
    (out_dir / "field_plan.md").write_text(field_plan_md(recs, tiles, stops, args, host_status))


def _js(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, Path):
        return str(o)
    return str(o)


def _fmt(v):
    if isinstance(v, float):
        return f"{v:.3e}" if 0 < abs(v) < 1e-3 else f"{v:.6g}"
    return "" if v is None else v


def field_plan_md(recs, tiles, stops, args, host_status):
    L = ["# Field plan - Hordejakten 2026 fine-scale refinement",
         "",
         f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} from `{args.hotspots}` "
         f"(top {args.top} hotspots, radius {args.radius_km} km, DTM {args.res} m, work grid {args.work_res} m).",
         "",
         f"**How stops are ordered.** Search theory: each stop is a {_radius(recs)} search disc around a candidate spot with "
         f"probability p = P(hotspot region) x P(disc | region). Greedily pick the next stop maximising "
         f"p x P(detect)={args.pd} / (drive + round-trip walk + {args.search_min:.0f} min search). Drive time = straight "
         f"line x 1.4 at {args.drive_kmh:.0f} km/h + 3 min; walk = Tobler off-trail (x0.6) along the straight line. "
         "Absolute p values are small because the coarse posterior is diffuse; the share column is relative to all "
         "refined candidates.",
         "",
         "Bearings are true north unless marked (mag = magnetic, declination +4.5 deg E assumed). "
         "On site: the camera stands ~41 deg (NE) of the box and faces ~221 deg (SW) - approach so you see the box from the NE side.",
         ""]
    if not stops:
        L += ["**No candidates** - no tile could be scored (see data status below).", ""]
    else:
        L += ["| # | spot lat, lon | elev | p share | p/h (rel.) | park at (lat, lon) | road | walk | drive | cum. time | links |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        top_rate = max(s["p_per_hour"] for s in stops) or 1.0
        for k, s in enumerate(stops, 1):
            r = s["rec"]
            pk = r.get("parking") or {}
            park = f"{pk['lat']:.5f}, {pk['lon']:.5f}" if pk else "-"
            lk = r["links"]
            li = f"[map]({lk['google_maps']}) [nk]({lk['norgeskart']})"
            if lk.get("google_directions_parking"):
                li += f" [drive]({lk['google_directions_parking']})"
            walk = f"{r.get('walk_distance_m') or '?'} m / {r.get('walk_time_min') or '?'} min"
            L.append(f"| {k} | {r['lat']:.5f}, {r['lon']:.5f} | {r['elevation_m']:.0f} m | {r['p_share_pct']:.1f}% | "
                     f"{100 * s['p_per_hour'] / top_rate:.0f} | {park} | {(pk.get('road') or '-')} | {walk} | "
                     f"{s['drive_min']:.0f} min | {s['t_cum_min'] / 60:.1f} h | {li} |")
        L += ["", "## Stop details", ""]
        for k, s in enumerate(stops, 1):
            r = s["rec"]
            pk = r.get("parking")
            L.append(f"### {k}. {r['lat']:.6f}, {r['lon']:.6f} ({r['elevation_m']:.0f} m) - hotspot #{r['hotspot_rank']}")
            if pk:
                L.append(f"- Park: {pk['lat']:.6f}, {pk['lon']:.6f} on {pk['road']} ({pk.get('elevation_m') or '?'} m).")
                L.append(f"- Walk {r['walk_distance_m']} m on bearing {r['bearing_car_to_box_true']:.0f} deg true "
                         f"({r['bearing_car_to_box_magnetic']:.0f} deg mag), climb {r['climb_m']} m, "
                         f"~{r['walk_time_min']} min; box->car {r['bearing_box_to_car_true']:.0f} deg "
                         f"({r['direction_hypothesis']}).")
            else:
                L.append("- No drivable road found within 1.2 km in OSM - check the map before driving.")
            L.append(f"- p = {r['p_abs']:.2e} ({r['p_share_pct']:.1f}% of refined total), P(spot | region) = "
                     f"{(r.get('p_in_tile') or 0):.4f}, score {r['score']:.2f}.")
            for why in r.get("reasons", []):
                L.append(f"  - {why}")
            L.append("")
    L += ["## Data status", "", "| hotspot | lat, lon | status | DTM | DOM | OSM | SR16 | notes |", "|---|---|---|---|---|---|---|---|"]
    for t in tiles:
        d = t.get("data", {})
        L.append(f"| {t['hotspot_rank']} | {t['lat']:.4f}, {t['lon']:.4f} | {t.get('status')} | {d.get('dtm', '-')} | "
                 f"{d.get('dom', '-')} | {d.get('osm', '-')} | {d.get('sr16', '-')} | {'; '.join(t.get('notes', []))[:200]} |")
    bad = [h for h, s in (host_status or {}).items() if s != "ok"]
    if bad:
        L += ["", "Hosts not reachable during this run: " + ", ".join(f"`{h}`" for h in bad) + "."]
    L += ["", "## Caveats", "",
          "- Every clue is a soft score (see `hordejakt/refine/score.py` for weights/reliabilities); nothing but missing terrain is a hard filter.",
          "- Kartverket DOM/DTM come from laser scans that may be several years old: new clear-cuts or openings may be missing.",
          "- OSM misses some small streams and cabins; DTM-derived streams (catchment >= 0.2 km2) partly compensate.",
          "- The morning-sun check uses terrain only (not trees) and only as far as the fetched DTM reaches"
          " (use --horizon-km 8 for distant ridges).",
          "- Direction: whiteboard «KOM FRA DEN VEIEN ←» (car ~130 deg from box, weight .75) vs. the older sign reading "
          "(car ~303 deg, weight .25).", ""]
    return "\n".join(L)


def _radius(recs):
    rs = sorted({r.get("search_radius_m") for r in recs if r.get("search_radius_m")})
    return f"{rs[0]:.0f} m" if len(rs) == 1 else ("20-25 m" if not rs else f"{rs[0]:.0f}-{rs[-1]:.0f} m")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hotspots", default=str(OUTPUT / "hotspots.json"))
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--radius-km", type=float, default=1.5)
    ap.add_argument("--res", type=float, default=1.0, help="DTM/DOM request resolution in m (1 or 10)")
    ap.add_argument("--work-res", type=float, default=2.0, help="scoring grid resolution in m")
    ap.add_argument("--per-tile", type=int, default=8, help="candidates kept per hotspot")
    ap.add_argument("--pool", type=int, default=150, help="Stage-A candidates evaluated per hotspot")
    ap.add_argument("--min-sep", type=float, default=40.0, help="min separation between candidates (m)")
    ap.add_argument("--no-dom", action="store_true", help="skip the surface model (canopy terms)")
    ap.add_argument("--no-sr16", action="store_true", help="skip NIBIO SR16")
    ap.add_argument("--horizon-km", type=float, default=0.0, help="also fetch a 10 m DTM of this radius for the sun check")
    ap.add_argument("--offline", action="store_true", help="use data/cache only")
    ap.add_argument("--skip-preflight", action="store_true")
    ap.add_argument("--start", help="'lat,lon' where the team starts (drive time to the first stop)")
    ap.add_argument("--search-min", type=float, default=10.0)
    ap.add_argument("--drive-kmh", type=float, default=45.0)
    ap.add_argument("--pd", type=float, default=0.9, help="P(detect | box inside searched disc)")
    ap.add_argument("--hours", type=float, default=10.0, help="plan length")
    ap.add_argument("--out-dir", default=str(OUTPUT))
    a = ap.parse_args(argv)
    if a.offline:
        fetch.set_offline(True)
    host_status = {}
    if not a.offline and not a.skip_preflight:
        host_status = fetch.check_hosts()
        print("data hosts: " + ", ".join(f"{h}={s}" for h, s in host_status.items()), file=sys.stderr)
    hs = load_hotspots(a.hotspots, a.top)
    status = {"blocked": set()}
    recs, tiles = [], []
    for h in hs:
        print(f"[{h['rank']:2d}/{len(hs)}] {h['lat']:.4f},{h['lon']:.4f} ...", file=sys.stderr, end=" ", flush=True)
        r, t = process_hotspot(h, a, status)
        print(f"{t.get('status')} {len(r)} candidates {t.get('data')}", file=sys.stderr)
        recs += r
        tiles.append(t)
    recs = dedupe(recs, min(50.0, a.min_sep))
    recs.sort(key=lambda r: (r["p_abs"], r["score"]), reverse=True)
    start = tuple(float(v) for v in a.start.split(",")) if a.start else None
    stops = plan(recs, start, a.search_min, a.drive_kmh, a.pd, a.hours)
    out_dir = Path(a.out_dir)
    write_outputs(out_dir, recs, tiles, stops, a, host_status)
    print(f"wrote {out_dir / 'refined_candidates.json'}, .csv and {out_dir / 'field_plan.md'} "
          f"({len(recs)} candidates, {len(stops)} stops)", file=sys.stderr)
    blocked = sorted(status["blocked"] | {h for h, s in host_status.items() if s == "blocked"})
    if not recs:
        print("\n" + fetch.blocked_message(blocked or list(fetch.HOSTS)), file=sys.stderr)
        return 2
    if blocked:
        print("\nSome data was unavailable. " + fetch.blocked_message(blocked), file=sys.stderr)
    for s in stops[:10]:
        r = s["rec"]
        print(f"{r['rank']:3d} {r['lat']:.5f},{r['lon']:.5f} {r['elevation_m']:.0f} m  p={r['p_abs']:.2e} "
              f"park={(r.get('parking') or {}).get('road', '-')} walk={r.get('walk_time_min')} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
