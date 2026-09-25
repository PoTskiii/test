"""Weather evidence: what Anja saw on the sky / felt outside vs. what the weather
was across Norway at the same moments.

Every layer returns ``loglik = log s(x)`` with s(x) ∝ P(her weather report | box
in cell x) (additive constant irrelevant, NaN = no information here). Mappings
are stated as probabilities P(...) below; the layer value is ``log P``.

Layers produced (name -> independence_group, reliability r)
===========================================================

Always included (community polygons + our own computations on raw data):

1. ``weather_clear_sky_2109_evening`` -> ``sky_2109_evening``, r = 0.45
   Tavla 21.09 19:00 «INGEN SKYER NÅ», 19:50 «KLAR HIMMEL» (also 19:32 «FINT
   VÆR»). Data: SKYDEKKE (innhold.ts) = areas blue (cloud/precip) on a Windy
   screenshot for the same period, hand-digitised by the community (±10 km).
   ring 0 (Vestlandet, Sørlandskysten, Trøndelag): P = 0.135 (= e^-2);
   ring 1 (band Lillehammer -> Sweden, "most uncertain"):   P = 0.37 (= e^-1);
   elsewhere P = 1. Ring membership is softened with a Gaussian (sigma 8 km),
   P = 1 - q * (1 - P_in).

2. ``weather_sun_2309_clear_areas`` -> ``sky_2309``, r = 0.40
   Anja had sun 23.09 (forenoon; tavla 17:49 «SOL») while the satellite showed
   cloud over most of Norway. Two community products of the *same* satellite
   observation are merged into one surface (mean of the two log P where both
   have information, otherwise whichever has it - see "Why merged" below):
   a) SOL_I_DAG (innhold.ts): clear areas drawn from a *description* of the
      image. ring 0 Kongsvinger-Rena-Sweden P = 1; ring 1 (parts of Vestfold,
      unclear which) P = 0.5; ring 2 (Trondheim-Ålesund, uncertain) P = 0.5;
      outside all rings P = 0.25; soft edges sigma 10 km.
   b) utelukket.json (community exclusion map 23.09, located from a picture,
      ±10 km). Decode: ``celler = [[lat, lon, code], ...]`` on 0.05° x 0.1°
      cells (cell centres, same keying as MagnusPladsen's utelukkNokkel);
      code 'R' = excluded, 'C' = mountain birch. Mapping: R -> P = 0.135 (soft
      edges sigma 8 km); unlisted cells inside the picture -> P = 1;
      'C' -> NaN (excluded for vegetation, says nothing about clouds);
      west of 8.35° E -> NaN (MagnusPladsen filled that in as 'R' because the
      picture did not cover it - not community evidence); outside the file's
      extent (lat 57.975-63.325, lon 8.35-12.65) -> NaN.

3. ``weather_no_fog_2309_morning`` -> ``fog_2309_morning``, r = 0.40
   Local in chat: thick fog 23.09 morning Nord-Odal -> Sør-Odal -> Jessheim,
   while Anja had none. TAAKE polygon (innhold.ts, "grovt tegnet"): inside
   P = 0.2, outside P = 1, soft edges sigma 4 km. (Valley fog: a hill-top at
   800 m above Odal could have been above it - one reason r is only 0.4.)

4. ``weather_calm_2309_1749`` -> ``wind_2309_1749``, r = 0.45
   Tavla 23.09 17:49 «LYDTETT · SOL · VINDSTILLE». Data: vind.json =
   open-meteo historical forecast (MET Nordic), 10 m wind at 17:49.
   Decode: ``celler = [[lat, lon, speed_ms, gust_ms], ...]``, cell centres of a
   0.2° x 0.4° grid (~22 km), land cells only (MagnusPladsen vind.ts).
   Speed is interpolated (Gaussian kernel, sigma 10 km; NaN > 25 km from any
   cell centre) and mapped with P = 0.15 + 0.85 / (1 + exp((v - 4) / 0.8)):
   v = 2 -> 0.93, 3 -> 0.79, 4 -> 0.58, 5 -> 0.33, >= 7 -> ~0.15. In-forest
   wind is weaker than the 10 m model wind, hence the soft 2-4 m/s shoulder.

5. ``weather_overcast_2409`` -> ``overcast_2409``, r = 0.40
   Tavla 24.09 «GRÅVÆR HELE DAGEN» (posted by 18:36). Up to three components,
   merged per cell as the mean of the available log P:
   a) met.json (MET "now", 24.09 18:07, fetched by default.no; raw values).
      Decode: ``punkter = [[lat, lon, temp_C, cloud_pct, rain, rh_pct], ...]``
      (order from defaultno.ts dn_met). Cloud % interpolated (kernel sigma
      10 km, NaN > 25 km from a point) and mapped
      P = 0.4 + 0.6 * sigmoid((cloud - 45) / 12): 5 % -> 0.42, 45 % -> 0.70,
      80 % -> 0.96.
   b) vaer.json station field ``stigning`` = temperature rise dawn -> 11:00
      on 24.09 (Frost/MET). An overcast morning warms little:
      P = 0.3 + 0.7 * sigmoid((2.5 - rise) / 0.6): 0 °C -> 0.99,
      2.5 -> 0.65, 3.5 -> 0.43, 5 -> 0.31. Kernel sigma 20 km, NaN > 50 km.
   c) radar.png (MET radar composite 24.09 16:35Z = 18:35 local, via
      default.no; ``cfg['weather_use_radar']``, default True). Decode: 720 x 720
      RGBA over bounds ``b = [[58, 7], [63, 13]]`` (radar.json), treated as
      linear in lat/lon (checked against the burnt-in place labels, error
      < ~0.07°). Exactly 5 opaque colours: (150,220,120) very light,
      (60,170,60) light, (255,230,0) moderate, (255,140,0) heavy,
      (220,20,20) very heavy; alpha 0 = no echo (also label holes).
      P(she writes «gråvær», not «regn») = 1 / 0.85 / 0.7 / 0.45 / 0.35 / 0.3,
      smoothed in P-space with sigma 8 km (advection + unknown writing time);
      NaN outside the bounds. It is not double counting with default.no: every
      fusjon/*.json variant was computed before 18:35 (utenfly at 13:21).
   Sanity: at 18:07 Hamar-Løten had 0-16 % cloud, Rena 23-40 %, Evenstad
   35-44 %, Koppang ~60 %; stations there warmed < 1.3 °C (all consistent).

6. ``weather_rain_2409_morning`` -> ``rain_2409_1105``, r = 0.25
   «(kl. 11:05) Anja sa at det regnet» 24.09 - relayed by others, stills show
   dewy glass rather than certain rain; community: it rained in Rena then.
   Data: vaer.json ``regn`` = station precipitation 07-12 on 24.09 (mm).
   P = 0.4 + 0.6 * (1 - exp(-r / 0.3)): 0 mm -> 0.4, 0.2 mm -> 0.71,
   0.5 mm -> 0.89. Kernel sigma 20 km, NaN > 50 km from a station. (Rena's two
   stations had 0.2 mm, so the community Rena claim adds nothing separate.)

7. ``weather_no_rain_2309_evening_froland`` -> ``rain_2309_evening``, r = 0.35
   Community weather check: rain in Froland 23.09 evening, no rain on stream.
   Froland = TEORIER 'froland' pos (58.53, 8.63).
   P = 1 - 0.8 * exp(-0.5 * (d / 25 km)^2).

8. ``weather_skyanalyse_2209`` -> ``skyanalyse_2209``, r = 0.10
   Community "skyanalyse" map (cloudy times 22.09 + aircraft) meeting point
   SKYANALYSE.senter (58.7, 8.27), outer ring 45 km. Status «usikker»/teori,
   contradicted by the Froland rain and the ~7 h drive, hence r = 0.1:
   P = 0.3 + 0.7 * exp(-0.5 * (d / 35 km)^2) (same 35 km as MagnusPladsen).

Only when ``cfg['weather_include_defaultno_derived']`` is true (default
False = module flag INCLUDE_DEFAULTNO_DERIVED; "auto" = true iff a
``defaultno_fusion*`` layer is listed in ``cfg['skip_layers']`` or
``cfg['skip']``):

9. ``weather_dn_rain_since_2109`` -> ``defaultno_model``, r = 0.55
   Camera glass dry 21.-23.09, tavla «NULL REGN» 22./23.09; one reported
   shower 24.09 ~11:05. Data: default.no regn.json (updated 24.09 18:25;
   accumulation since 21.09 04:50Z from 831 Frost stations + 76 radar frames).
   Decode (same as defaultno.ts tegnGrid / defaultno_fusion.decode_rle):
   ``lop`` is a flat list with stride 4: [i, j, len, k, i, j, len, k, ...]
   = row i, first column j, run length len, class k; cells (i, j..j+len-1)
   have centre (lat0 + i*dlat, lon0 + jj*dlon) and extent ±dlat/2, ±dlon/2
   (lat0 57.8, dlat 0.05, lon0 4.3, dlon 0.1). Verified: 8712 values = 2178
   runs, i non-decreasing, no overlapping cells, k in {1, 2, 3}. Unlisted
   cells = class 0 (driest; 5 % of Norwegian land, around Hamar-Elverum-
   Kongsvinger). Classes (renderer opacities .22/.42/.65, legend «0,3-6 mm»
   and «over 6 mm»): 3 = over 6 mm (65 % of land: west, south, north),
   1-2 = the 0.3-6 mm band (thresholds inside the band unpublished).
   Mapping P: class 0 -> 1, 1 -> 1, 2 -> 0.6 (log -0.5), 3 -> 0.22 (log -1.5).
   Group ``defaultno_model`` on purpose: if someone enables it while the
   default.no fusion layer is still on, fusion averages instead of summing.

Why merged layers: fusion averages robust log-likelihoods inside a group and
a NaN cell counts as a neutral vote there, so two separate layers with
different coverage would halve the evidence wherever only one of them has
information. Components of one observation are therefore merged per cell with
a NaN-aware mean before they become a LayerResult.

Not encoded (no matching data offline, or not weather):
* «CA 12 °C (DAGEN) · NÅ CA 8-11 °C» (21.09 19:35), «ISH 16°» (23.09
  evening), «SIKKERT 5°, TROR DET ER VARMERE» (25.09 09:58): no temperature
  field for those times is mirrored (met.json/vegkamera temps are 24.09 18:xx).
* «OVERSKYET», «INGEN TÅKE» 09:49 (25.09): the mirror ends 24.09 18:36.
* Dew on the roof 07:00-09:40 (dried by ~10:11), «SER VELDIG MANGE STJERNER»,
  «det har ikke vært frost»: the only dew field (vaer.json ``dugg`` = dewpoint
  depression at dawn) is for 24.09, when default.no's camera read "no dew".
* vaer.json ``score`` (default.no similarity to the camera): same raw fields
  as components 5b/6, and it ranks northern Norway best - not used.
* vegkamera.json (road weather 24.09 18:30): 6 of 313 gauges wet, all
  Østfold/Romerike/west coast - corroborates the radar, no own layer.
* baer.json (berries), sjelden.json (aircraft rarity): not weather.
"""
import json
import math
import re
import warnings

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from shapely import contains_xy
from shapely.geometry import Polygon

from .. import DEFAULTNO, MAGNUS
from ..geo import haversine
from .base import LayerResult
from .defaultno_fusion import decode_rle

INCLUDE_DEFAULTNO_DERIVED = False

INNHOLD = MAGNUS / "src" / "data" / "innhold.ts"
PUBLIC = MAGNUS / "public" / "data"

# --- likelihood parameters (see module docstring) --------------------------
SKYDEKKE_P = (np.exp(-2.0), np.exp(-1.0))       # ring 0, ring 1
SKYDEKKE_SIGMA_KM = 8.0
SOL_P_RINGS = (1.0, 0.5, 0.5)                   # Kongsvinger-Rena, Vestfold, Trondheim-Ålesund
SOL_P_OUT = 0.25
SOL_SIGMA_KM = 10.0
UTELUKKET_P_R = np.exp(-2.0)
UTELUKKET_SIGMA_KM = 8.0
UTELUKKET_WEST_FILL_LON = 8.35                  # west of this MagnusPladsen filled in 'R'
FOG_P_IN = 0.2
FOG_SIGMA_KM = 4.0
RADAR_P = {0: 1.0, 1: 0.85, 2: 0.7, 3: 0.45, 4: 0.35, 5: 0.3}
RADAR_COLOURS = {(150, 220, 120): 1, (60, 170, 60): 2, (255, 230, 0): 3, (255, 140, 0): 4, (220, 20, 20): 5}
RADAR_SIGMA_KM = 8.0
FROLAND = (58.53, 8.63)
RAIN_CLASS_LL = {0: 0.0, 1: 0.0, 2: -0.5, 3: -1.5}

# Copies of the innhold.ts constants (25.09) used only if parsing fails.
_FALLBACK = {
    "SOL_I_DAG": [
        [[60.1, 11.85], [60.5, 11.6], [60.88, 11.35], [61.15, 11.2], [61.3, 11.35], [61.3, 12.1], [61.0, 12.45],
         [60.6, 12.6], [60.2, 12.55], [60.0, 12.2]],
        [[59.05, 9.95], [59.1, 10.55], [59.6, 10.45], [59.65, 10.0], [59.35, 9.8]],
        [[62.3, 5.9], [62.8, 6.2], [63.2, 8.0], [63.55, 10.0], [63.5, 10.7], [63.2, 10.6], [62.9, 9.0], [62.5, 7.2],
         [62.2, 6.3]],
    ],
    "TAAKE": [[[60.1, 11.05], [60.08, 11.4], [60.18, 11.75], [60.3, 11.85], [60.48, 11.75], [60.5, 11.4],
               [60.35, 11.15], [60.2, 11.0]]],
    "SKYDEKKE": [
        [[63.685, 7.743], [63.766, 9.107], [63.966, 10.32], [64.119, 11.305], [63.953, 11.835], [63.618, 11.532],
         [63.347, 10.926], [63.074, 10.244], [62.833, 9.789], [62.449, 9.531], [62.061, 9.486], [61.704, 9.41],
         [61.379, 9.183], [61.087, 9.259], [60.867, 9.107], [60.607, 8.652], [60.533, 8.046], [60.346, 7.516],
         [60.044, 7.212], [59.664, 6.985], [59.279, 6.864], [58.889, 6.833], [58.574, 7.137], [58.336, 7.591],
         [58.177, 7.819], [58.017, 7.288], [58.257, 6.379], [58.653, 5.621], [59.356, 4.863], [60.421, 4.56],
         [61.452, 4.636], [62.309, 5.166], [63.074, 6.227], [63.483, 7.137]],
        [[60.94, 10.092], [61.014, 10.547], [61.596, 11.229], [62.168, 11.835], [62.729, 12.366], [63.347, 12.82],
         [63.719, 12.896], [63.739, 12.563], [63.005, 12.108], [62.379, 11.608], [61.812, 11.002], [61.233, 10.32],
         [61.051, 9.941]],
    ],
    "SKYANALYSE": {"senter": [58.7, 8.27], "indreKm": 12, "ytreKm": 45},
}


# --- parsing -----------------------------------------------------------------
def _innhold_text():
    try:
        return INNHOLD.read_text()
    except OSError:
        return ""


def _rings(src, name):
    """`export const NAME: LatLon[][] = [ [[lat, lon], ...], ... ]` -> list of rings."""
    m = re.search(rf"export const {name}\s*:\s*LatLon\[\]\[\]\s*=\s*(\[.*?\n\])", src, re.S)
    if m:
        try:
            rings = json.loads(re.sub(r",\s*\]", "]", m.group(1)))
            if rings and all(len(r) >= 3 for r in rings):
                return rings
        except ValueError:
            pass
    warnings.warn(f"weather: could not parse {name} from innhold.ts, using the 25.09 copy")
    return _FALLBACK[name]


def _skyanalyse(src):
    m = re.search(r"SKYANALYSE\s*=\s*\{\s*senter:\s*\[([\d.]+),\s*([\d.]+)\][^}]*?ytreKm:\s*([\d.]+)", src)
    if m:
        return (float(m.group(1)), float(m.group(2))), float(m.group(3))
    d = _FALLBACK["SKYANALYSE"]
    return tuple(d["senter"]), float(d["ytreKm"])


def _froland(src):
    m = re.search(r"id:\s*'froland'[^}]*?pos:\s*\[([\d.]+),\s*([\d.]+)\]", src)
    return (float(m.group(1)), float(m.group(2))) if m else FROLAND


# --- geometry helpers --------------------------------------------------------
def _cell_km(grid):
    mid = math.radians(0.5 * (grid.lat_min + grid.lat_max))
    return 111.2 * grid.dlat, 111.32 * math.cos(mid) * grid.dlon


def _inside(grid, ring, mesh):
    L, O = mesh
    poly = Polygon([(p[1], p[0]) for p in ring])
    if not poly.is_valid:
        poly = poly.buffer(0)
    minx, miny, maxx, maxy = poly.bounds
    m = np.zeros(grid.shape, bool)
    sel = (O >= minx) & (O <= maxx) & (L >= miny) & (L <= maxy)
    if sel.any():
        m[sel] = contains_xy(poly, O[sel], L[sel])
    return m


def _soften(grid, mask, sigma_km):
    """Membership in [0, 1]: mask blurred with a Gaussian of sigma_km."""
    ky, kx = _cell_km(grid)
    return np.clip(gaussian_filter(mask.astype(np.float32), sigma=(sigma_km / ky, sigma_km / kx),
                                   mode="nearest", truncate=3.0).astype(float), 0.0, 1.0)


def _kernel_field(grid, lat, lon, val, sigma_km, cutoff_km, step=(0.05, 0.1)):
    """Gaussian-kernel (Nadaraya-Watson) interpolation of point values onto the
    grid, computed on a coarse step grid and upsampled bilinearly. NaN where the
    nearest point is farther than about cutoff_km."""
    lat, lon, val = (np.asarray(a, float) for a in (lat, lon, val))
    ok = np.isfinite(lat) & np.isfinite(lon) & np.isfinite(val)
    ok &= (lat > grid.lat_min - 1) & (lat < grid.lat_max + 1) & (lon > grid.lon_min - 2) & (lon < grid.lon_max + 2)
    lat, lon, val = lat[ok], lon[ok], val[ok]
    if not len(val):
        return grid.empty()
    clat = np.arange(grid.lat_min, grid.lat_max + step[0] + 1e-9, step[0])
    clon = np.arange(grid.lon_min, grid.lon_max + step[1] + 1e-9, step[1])
    CL, CO = np.meshgrid(clat, clon, indexing="ij")
    W = np.zeros(CL.shape)
    WV = np.zeros(CL.shape)
    for la, lo, v in zip(lat, lon, val):
        w = np.exp(-0.5 * (haversine(CL, CO, la, lo) / sigma_km) ** 2)
        W += w
        WV += w * v
    V = np.where(W > 1e-12, WV / np.maximum(W, 1e-300), float(np.mean(val)))
    fi = (grid.lats - grid.lat_min) / step[0]
    fj = (grid.lons - grid.lon_min) / step[1]
    I, J = np.meshgrid(fi, fj, indexing="ij")
    Vu = map_coordinates(V, [I, J], order=1, mode="nearest")
    Wu = map_coordinates(W, [I, J], order=1, mode="nearest")
    return np.where(Wu >= np.exp(-0.5 * (cutoff_km / sigma_km) ** 2), Vu, np.nan)


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.asarray(x, float)))


def _log(p):
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.log(np.asarray(p, float))


def _nanmean(*arrs):
    stack = np.stack(arrs)
    n = np.isfinite(stack).sum(axis=0)
    s = np.where(np.isfinite(stack), stack, 0.0).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, s / np.maximum(n, 1), np.nan)


def _include_defaultno(cfg):
    v = cfg.get("weather_include_defaultno_derived", INCLUDE_DEFAULTNO_DERIVED)
    if isinstance(v, str) and v.lower() == "auto":
        skipped = list(cfg.get("skip_layers", ())) + list(cfg.get("skip", ()))
        return any(str(s).startswith("defaultno_fusion") for s in skipped)
    return bool(v)


# --- layers ------------------------------------------------------------------
def clear_sky_2109(grid, src, mesh):
    rings = _rings(src, "SKYDEKKE")
    p = np.ones(grid.shape)
    for ring, p_in in zip(rings, SKYDEKKE_P):
        q = _soften(grid, _inside(grid, ring, mesh), SKYDEKKE_SIGMA_KM)
        p *= 1.0 - q * (1.0 - p_in)
    return LayerResult(
        "weather_clear_sky_2109_evening", _log(p), reliability=0.45, independence_group="sky_2109_evening",
        description="21.09 19:00 «INGEN SKYER NÅ» / 19:50 «KLAR HIMMEL» vs. areas blue on Windy then "
                    "(SKYDEKKE, hand-digitised ±10 km): coast/west/Trøndelag P=0.14, Lillehammer-Sweden band P=0.37",
        sources=["tavla 21.09 19:00, 19:50", "MagnusPladsen innhold.ts SKYDEKKE (Windy screenshot)"])


def _utelukket_ll(grid, mesh):
    d = json.load(open(PUBLIC / "utelukket.json"))
    cells = d["celler"]
    dlat, dlon = d["dlat"], d["dlon"]
    lat = np.array([c[0] for c in cells], float)
    lon = np.array([c[1] for c in cells], float)
    code = np.array([c[2] for c in cells])
    r = grid.paint_blocks(lat[code == "R"], lon[code == "R"], dlat, dlon, np.ones((code == "R").sum()), fill=0.0)
    c = grid.paint_blocks(lat[code == "C"], lon[code == "C"], dlat, dlon, np.ones((code == "C").sum()), fill=0.0)
    q = _soften(grid, r > 0.5, UTELUKKET_SIGMA_KM)
    ll = _log(1.0 - q * (1.0 - UTELUKKET_P_R))
    L, O = mesh
    extent = (L >= lat.min() - dlat / 2) & (L <= lat.max() + dlat / 2) & (O <= lon.max() + dlon / 2) \
        & (O >= max(lon.min() - dlon / 2, UTELUKKET_WEST_FILL_LON))
    return np.where(extent & (c < 0.5), ll, np.nan)


def sun_2309(grid, src, mesh):
    rings = _rings(src, "SOL_I_DAG")
    p = np.full(grid.shape, SOL_P_OUT)
    for ring, p_in in zip(rings, SOL_P_RINGS):
        q = _soften(grid, _inside(grid, ring, mesh), SOL_SIGMA_KM)
        p += q * (p_in - SOL_P_OUT)
    ll_sol = _log(np.clip(p, SOL_P_OUT, 1.0))
    ll = _nanmean(ll_sol, _utelukket_ll(grid, mesh))
    return LayerResult(
        "weather_sun_2309_clear_areas", ll, reliability=0.40, independence_group="sky_2309",
        description="Sun at the box 23.09 while the satellite showed cloud over most of Norway: mean of "
                    "SOL_I_DAG clear areas (Kongsvinger-Rena P=1, Vestfold/Trondheim-Ålesund 0.5, elsewhere 0.25) "
                    "and the community exclusion map utelukket.json (R P=0.14; birch cells and MagnusPladsen's "
                    "west fill = no info)",
        sources=["satellite 23.09 via community (innhold.ts SOL_I_DAG)", "utelukket.json (community map 23.09)",
                 "tavla 23.09 17:49 «SOL»"])


def fog_2309(grid, src, mesh):
    rings = _rings(src, "TAAKE")
    p = np.ones(grid.shape)
    for ring in rings:
        q = _soften(grid, _inside(grid, ring, mesh), FOG_SIGMA_KM)
        p *= 1.0 - q * (1.0 - FOG_P_IN)
    return LayerResult(
        "weather_no_fog_2309_morning", _log(p), reliability=0.40, independence_group="fog_2309_morning",
        description="Thick fog 23.09 morning Nord-Odal/Sør-Odal/Jessheim (local in chat) while Anja had none; "
                    "TAAKE polygon P=0.2 inside, soft edge 4 km",
        sources=["chat (Nord-Odal local) 23.09", "innhold.ts TAAKE"])


def calm_2309(grid):
    d = json.load(open(PUBLIC / "vind.json"))
    a = np.array(d["celler"], float)
    v = _kernel_field(grid, a[:, 0], a[:, 1], a[:, 2], sigma_km=10.0, cutoff_km=25.0)
    p = 0.15 + 0.85 / (1.0 + np.exp((v - 4.0) / 0.8))
    return LayerResult(
        "weather_calm_2309_1749", _log(p), reliability=0.45, independence_group="wind_2309_1749",
        description="23.09 17:49 «VINDSTILLE» vs. open-meteo (MET Nordic) 10 m wind at 17:49; "
                    "P = 0.15 + 0.85/(1+exp((v-4)/0.8)), 2 m/s 0.93, 4 m/s 0.58, 6 m/s 0.2",
        sources=["tavla 23.09 17:49", f"vind.json ({d.get('kilde')}, {d.get('tid')})"])


def _radar_ll(grid, mesh):
    from PIL import Image

    meta = json.load(open(DEFAULTNO / "radar.json"))
    (la0, lo0), (la1, lo1) = meta["b"]
    img = np.array(Image.open(DEFAULTNO / "radar.png").convert("RGBA"))
    h, w = img.shape[:2]
    cls = np.zeros((h, w), int)
    for rgb, k in RADAR_COLOURS.items():
        cls[(img[..., 3] > 0) & np.all(img[..., :3] == rgb, axis=-1)] = k
    lut = np.array([RADAR_P[k] for k in range(6)])
    p_img = lut[cls]
    L, O = mesh
    inside = (L >= la0) & (L <= la1) & (O >= lo0) & (O <= lo1)
    row = (la1 - L) / (la1 - la0) * h - 0.5   # row 0 = north edge
    col = (O - lo0) / (lo1 - lo0) * w - 0.5
    p = map_coordinates(p_img, [row, col], order=1, mode="nearest")
    ky, kx = _cell_km(grid)
    p = gaussian_filter(p, sigma=(RADAR_SIGMA_KM / ky, RADAR_SIGMA_KM / kx), mode="nearest", truncate=3.0)
    return np.where(inside, _log(p), np.nan), meta["tid"]


def overcast_2409(grid, mesh, use_radar=True):
    parts, used = [], []
    m = np.array(json.load(open(DEFAULTNO / "met.json"))["punkter"], dtype=float)
    cloud = _kernel_field(grid, m[:, 0], m[:, 1], m[:, 3], sigma_km=10.0, cutoff_km=25.0)
    parts.append(_log(0.4 + 0.6 * _sigmoid((cloud - 45.0) / 12.0)))
    used.append("met.json cloud % 24.09 18:07")
    st = json.load(open(DEFAULTNO / "vaer.json"))["stasjoner"]
    rise = np.array([np.nan if s.get("stigning") is None else s["stigning"] for s in st], float)
    slat = np.array([s["lat"] for s in st], float)
    slon = np.array([s["lon"] for s in st], float)
    rise_f = _kernel_field(grid, slat, slon, rise, sigma_km=20.0, cutoff_km=50.0)
    parts.append(_log(0.3 + 0.7 * _sigmoid((2.5 - rise_f) / 0.6)))
    used.append("vaer.json station warming dawn->11:00 24.09")
    if use_radar:
        ll_radar, tid = _radar_ll(grid, mesh)
        parts.append(ll_radar)
        used.append(f"radar.png {tid}")
    return LayerResult(
        "weather_overcast_2409", _nanmean(*parts), reliability=0.40, independence_group="overcast_2409",
        description="24.09 «GRÅVÆR HELE DAGEN»: mean over components of log P - cloud at 18:07 "
                    "(P=0.4+0.6*sig((c-45)/12)), little morning warming (P=0.3+0.7*sig((2.5-dT)/0.6))"
                    + (", no heavy radar echo at 18:35" if use_radar else ""),
        sources=["tavla 24.09"] + used)


def rain_2409(grid):
    st = json.load(open(DEFAULTNO / "vaer.json"))["stasjoner"]
    r = np.array([np.nan if s.get("regn") is None else s["regn"] for s in st], float)
    slat = np.array([s["lat"] for s in st], float)
    slon = np.array([s["lon"] for s in st], float)
    rf = _kernel_field(grid, slat, slon, r, sigma_km=20.0, cutoff_km=50.0)
    p = 0.4 + 0.6 * (1.0 - np.exp(-np.maximum(rf, 0.0) / 0.3))
    return LayerResult(
        "weather_rain_2409_morning", _log(p), reliability=0.25, independence_group="rain_2409_1105",
        description="24.09 ~11:05 Anja said it rained (relayed; community: rain in Rena then) vs. station "
                    "precipitation 07-12; P = 0.4 + 0.6*(1-exp(-mm/0.3))",
        sources=["stream 24.09 11:05 (relayed)", "default.no vaer.json (Frost) regn 07-12"])


def froland_2309(grid, src, mesh):
    la, lo = _froland(src)
    L, O = mesh
    d = haversine(L, O, la, lo)
    p = 1.0 - 0.8 * np.exp(-0.5 * (d / 25.0) ** 2)
    return LayerResult(
        "weather_no_rain_2309_evening_froland", _log(p), reliability=0.35, independence_group="rain_2309_evening",
        description="Rain in Froland 23.09 evening, none on the stream; P = 1 - 0.8*exp(-(d/25 km)^2/2)",
        sources=["community weather check (innhold.ts hint 'froland')"])


def skyanalyse_2209(grid, src, mesh):
    (la, lo), _outer = _skyanalyse(src)
    L, O = mesh
    d = haversine(L, O, la, lo)
    p = 0.3 + 0.7 * np.exp(-0.5 * (d / 35.0) ** 2)
    return LayerResult(
        "weather_skyanalyse_2209", _log(p), reliability=0.10, independence_group="skyanalyse_2209",
        description="Community cloud/aircraft timing map (22.09) meeting point in inner Agder; theory, "
                    "contradicted by Froland rain and drive time",
        sources=["innhold.ts SKYANALYSE (community image, ±15 km)"])


def dn_rain_since_2109(grid):
    d = json.load(open(DEFAULTNO / "regn.json"))
    cls = np.clip(decode_rle(d, grid), 0, 3)
    ll = np.array([RAIN_CLASS_LL[k] for k in range(4)])[cls]
    return LayerResult(
        "weather_dn_rain_since_2109", ll, reliability=0.55, independence_group="defaultno_model",
        description=f"Camera dry 21.-23.09 («NULL REGN»), one shower 24.09: default.no rain since {d.get('siden')} "
                    f"({d.get('stasjoner')} stations, {d.get('radar')} radar frames); class 0/1 -> 0, 2 -> -0.5, 3 -> -1.5",
        sources=[f"default.no regn.json ({d.get('oppdatert')})", "tavla «NULL REGN»"])


def build(grid, cfg):
    src = _innhold_text()
    mesh = grid.mesh()
    out = [
        clear_sky_2109(grid, src, mesh),
        sun_2309(grid, src, mesh),
        fog_2309(grid, src, mesh),
        calm_2309(grid),
        overcast_2409(grid, mesh, use_radar=bool(cfg.get("weather_use_radar", True))),
        rain_2409(grid),
        froland_2309(grid, src, mesh),
        skyanalyse_2209(grid, src, mesh),
    ]
    if _include_defaultno(cfg):
        out.append(dn_rain_since_2109(grid))
    return out
