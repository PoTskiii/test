"""Aircraft sighting geometry.

For each event where Anja pointed at / reacted to an aircraft we ask: if the
box stood in cell x, how likely is it that *some* aircraft was high enough in
her sky at that moment for her to point at it?  Through a forest canopy only
the upper sky is visible, so we use a soft elevation-angle threshold.

    P(event | x) = b + (1 - b) * [1 - prod_a (1 - q * vis(max_t elev_a(x, t)))]

a runs over every tracked aircraft in the event (unknown identity is handled by
the union), t over the timing window (stream delay is uncertain), q is the
chance she notices a visible aircraft and b a floor for unmodelled causes
(satellite, untracked aircraft, gesture misread).

Computed on a coarse 0.02° x 0.04° grid (~2 km; elevation angles vary slowly)
and interpolated to the analysis grid.
"""
import json
from datetime import datetime, timedelta

import numpy as np
from scipy.ndimage import map_coordinates

from .. import DEFAULTNO, MAGNUS
from ..geo import FT, destination, elevation_angle, haversine
from .base import LayerResult

COARSE_DLAT, COARSE_DLON = 0.02, 0.04
BOX = (58.0, 64.5, 4.5, 13.5)
OBSERVER_M = 600.0  # rough terrain height of the box (m a.s.l.); altitudes are ft AMSL


FLY_2130_LABEL_LAG_S = 45
RAW_TRACES = {"NOZ9EG": "trace_4791ac.json", "NOZ56U": "trace_47a3b0.json"}
MIN_FT = 8000  # airliner-class traffic; low GA/helicopter traffic near airfields is not what she described


def vis(elev_deg, mid=25.0, scale=3.0):
    return 1.0 / (1.0 + np.exp(-(elev_deg - mid) / scale))


def _hms(s):
    h, m, sec = map(int, s.split(":"))
    return h * 3600 + m * 60 + sec


def _interp_track(track, t):
    """track: [[hms, lat, lon, ft], ...]; t seconds of day -> (lat, lon, ft) or None."""
    ts = np.array([_hms(p[0]) for p in track], float)
    if t < ts[0] or t > ts[-1]:
        return None
    k = np.searchsorted(ts, t, side="right") - 1
    k = min(k, len(ts) - 2)
    f = 0.0 if ts[k + 1] == ts[k] else (t - ts[k]) / (ts[k + 1] - ts[k])
    a, b = track[k], track[k + 1]
    return (a[1] + f * (b[1] - a[1]), a[2] + f * (b[2] - a[2]), a[3] + f * (b[3] - a[3]))


def _densify(poly, step_km=1.0):
    pts = []
    for (la1, lo1), (la2, lo2) in zip(poly[:-1], poly[1:]):
        d = float(haversine(la1, lo1, la2, lo2))
        n = max(1, int(np.ceil(d / step_km)))
        for k in range(n):
            f = k / n
            pts.append((la1 + f * (la2 - la1), lo1 + f * (lo2 - lo1)))
    pts.append(tuple(poly[-1]))
    return pts


def events(cfg):
    """Returns list of dicts: name, positions [(lat, lon, alt_m)...] grouped per aircraft, params."""
    ev = []
    # --- 21.09: pointed up at 21:29:38 stream time; stream delay ~15-60 s -> real ~21:28:38-21:29:23
    # fly_2130.json labels are 45 s EARLY: the position labelled t happened at real t + 45 s
    # (verified against the raw adsb.lol traces: 0.23 km mean error at +45 s vs 10.8 km at 0 s).
    d = json.load(open(MAGNUS / "public" / "data" / "fly_2130.json"))
    t0, t1 = _hms("21:28:30"), _hms("21:29:30")  # real (CEST) window
    ac = {}
    for f in d["fly"]:
        pos = []
        for t in range(t0, t1 + 1, 10):
            p = _interp_track(f["spor"], t - FLY_2130_LABEL_LAG_S)
            if p and p[2] > MIN_FT:
                pos.append((p[0], p[1], p[2] * FT))
        if pos:
            ac[f["kallesignal"]] = pos
    # exact raw traces for the two candidate aircraft, when the evidence branch is present
    for callsign, pos in _raw_trace_positions(t0, t1).items():
        ac[callsign] = pos
    ev.append({"name": "2109_2129_point", "aircraft": ac, "reliability": 0.75,
               "desc": "21.09 21:29:38 (stream) Anja points up, writes «FLY» 21:30:12; ADS-B fly_2130.json, delay 15-60 s"})

    # --- 22.09 20:32 and 20:34 (overcast 90-96 %: only aircraft under ~28 000 ft visible)
    e = json.load(open(DEFAULTNO / "flyhendelser.json"))
    for key, name, rel, courses, desc in [
        ("22.09 20:32", "2209_2032_flyy", 0.45, None, "22.09 20:32:40 chat «FLYY» (weaker; SAS39A candidate)"),
        ("22.09 20:34", "2209_2034_follow", 0.7, (110, 250),
         "22.09 20:34:40 she points, sits up and follows a plane southward (NOZ55J candidate)"),
    ]:
        ac = {}
        for f in e["fly"]:
            if f["h"] != key or not f.get("pek"):
                continue
            ft = f["pek"][2]
            if ft is None or ft < MIN_FT or ft > 28000:
                continue
            if courses and not (courses[0] <= (f.get("kurs") or -1) <= courses[1]):
                continue
            path = _densify(f["spor"], 1.5) if len(f["spor"]) >= 2 else [tuple(f["pek"][:2])]
            ac[f["k"]] = [(la, lo, ft * FT) for la, lo in path]
        ev.append({"name": name, "aircraft": ac, "reliability": rel, "desc": desc})

    # --- 25.09 17:22 stream: pointed up; SAS50J over east Stange (only track we have; SAS364 over Rena untracked)
    track = _read_fly_2509()
    ac = {}
    if track:
        pos = []
        for t in range(_hms("17:21:00"), _hms("17:22:20") + 1, 10):
            p = _interp_track(track, t)
            if p:
                pos.append((p[0], p[1], p[2] * FT))
        ac["SAS50J"] = pos
    ev.append({"name": "2509_1722_point", "aircraft": ac, "reliability": 0.45, "floor": 0.15,
               "desc": "25.09 17:22 (stream) pointed up; SAS50J track only (SAS364 over Rena untracked), overcast day"})
    return ev


def _raw_trace_positions(t0, t1, day="2026-09-21"):
    """Positions every 10 s in the real CEST window [t0, t1] (seconds of day) from adsb.lol traces."""
    import gzip
    from datetime import datetime, timedelta, timezone
    from .. import RAW
    out = {}
    base_day = datetime.fromisoformat(day).replace(tzinfo=timezone(timedelta(hours=2))).timestamp()
    for callsign, fn in RAW_TRACES.items():
        path = RAW / "mk_bevis" / "bevis" / "claude-2026-09-25" / "adsb" / fn
        if not path.exists():
            continue
        tr = json.loads(gzip.open(path).read())
        pts = [(tr["timestamp"] + p[0], p[1], p[2], p[3]) for p in tr["trace"]
               if p[1] is not None and isinstance(p[3], (int, float))]
        if not pts:
            continue
        T, La, Lo, Al = (np.array(c, float) for c in zip(*pts))
        pos = []
        for t in range(t0, t1 + 1, 10):
            ts = base_day + t
            if T[0] <= ts <= T[-1]:
                alt = float(np.interp(ts, T, Al))
                if alt > MIN_FT:
                    pos.append((float(np.interp(ts, T, La)), float(np.interp(ts, T, Lo)), alt * FT))
        if pos:
            out[callsign] = pos
    return out


def _read_fly_2509():
    import re
    src = (MAGNUS / "src" / "data" / "innhold.ts").read_text()
    m = re.search(r"FLY_2509[^=]*=\s*\{[^}]*spor:\s*(\[\[.*?\]\])\s*,?\s*\}", src, re.S)
    if not m:
        return None
    return json.loads(m.group(1))


def event_prob(lat, lon, aircraft, q=0.85, floor=0.03, mid=25.0, scale=3.0):
    miss = np.ones_like(lat)
    for positions in aircraft.values():
        best = np.full_like(lat, -90.0)
        for la, lo, alt in positions:
            g = haversine(lat, lon, la, lo)
            best = np.maximum(best, elevation_angle(g, alt - OBSERVER_M))
        miss *= 1.0 - q * vis(best, mid, scale)
    return floor + (1.0 - floor) * (1.0 - miss)


def _upsample(coarse, grid):
    la0, la1, lo0, lo1 = BOX
    fi = (grid.lats - la0) / COARSE_DLAT
    fj = (grid.lons - lo0) / COARSE_DLON
    I, J = np.meshgrid(fi, fj, indexing="ij")
    return map_coordinates(coarse, [I, J], order=1, mode="nearest")


def build(grid, cfg):
    la0, la1, lo0, lo1 = BOX
    clats = np.arange(la0, la1 + 1e-9, COARSE_DLAT)
    clons = np.arange(lo0, lo1 + 1e-9, COARSE_DLON)
    CL, CO = np.meshgrid(clats, clons, indexing="ij")
    out = []
    for ev in events(cfg):
        if not ev["aircraft"]:
            continue
        p = event_prob(CL, CO, ev["aircraft"], floor=ev.get("floor", 0.03))
        ll = _upsample(np.log(p), grid)
        out.append(LayerResult(
            name=f"aircraft_{ev['name']}", loglik=ll, reliability=ev["reliability"],
            independence_group=f"aircraft_{ev['name']}", description=ev["desc"],
            sources=["default.no flyhendelser.json / fly_2130.json (adsb.lol)", "MagnusPladsen innhold.ts FLY_2509"]))
    return out
