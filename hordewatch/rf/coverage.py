"""Cellular-coverage evidence layer + Starlink-vs-cellular discriminator.

*Conditional* location evidence: **if** the forest box uplinks over 4G/5G (rather
than Starlink), then it must sit inside a mobile mast's coverage, so cells with
good coverage become more likely and dead zones less likely. Because Starlink is
equally plausible (and a Starlink site is *chosen* for poor coverage, if
anything), this layer is emitted with a deliberately **low reliability (0.3)** so
it can only nudge the posterior, never dominate it (see the robust mixture in
``hordejakt.layers.base``: L(x) >= 1 - r, so a wrong cellular hypothesis costs at
most ~0.7 of a likelihood ratio).

What produces the coverage field
--------------------------------
Ideally, a real coverage map:
* **Nkom** publishes mobile coverage ("dekningskart") and a transmitter register
  ("Finnsenderen", https://finnsenderen.no) with base-station sites and bands.
* Operators publish coverage tiles/APIs (Telenor, Telia, Ice "dekningskart").
Candidate endpoints are listed in :data:`COVERAGE_ENDPOINTS`. **All network
access fails soft** (this dev container blocks everything but GitHub/PyPI/npm;
the live fetch runs on the user's machine). When no coverage data is available
this module logs and emits nothing rather than inventing a prior.

When only base-station *sites* are known (e.g. from Finnsenderen), we synthesise
a coverage footprint with a rural log-distance propagation model
(:func:`coverage_field_from_masts`). This is a coarse footprint, not a
propagation simulation - terrain, clutter and real antenna patterns are ignored,
hence the low reliability.

Stream-health discriminator (which uplink is it?)
-------------------------------------------------
Independent of coverage, the *timing* of stream stalls tells the two apart, and
``hordewatch.analyzers.stream_health`` already emits an ``uplink_signature``
verdict from it. In short (see :func:`discriminator_note`): Starlink shows short,
~15 s-periodic micro-stalls and canopy-obstruction outages on a global slot
clock; cellular shows congestion-driven bitrate dips concentrated in the evening
busy hour and aperiodic handover stalls. Consult that verdict before trusting
this layer: raise the reliability toward it if ``cellular_like``, drop the layer
entirely if ``starlink_like``.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

from hordejakt.geo import haversine
from hordejakt.grid import GRID, Grid

from ..bridges.common import (DEFAULT_LAYERS_DIR, coarse_axes, sub_grid, upsample,
                              write_layer)

log = logging.getLogger("hordewatch.rf.coverage")

# --------------------------------------------------------------------------- candidate live endpoints (documentation)
COVERAGE_ENDPOINTS = {
    "nkom_finnsenderen": "https://finnsenderen.no/  (base-station sites & bands; scrape/API)",
    "nkom_dekningskart": "https://www.nkom.no/  Nkom mobile coverage ('dekningskart') datasets",
    "telenor_coverage": "https://www.telenor.no/dekning/  (operator coverage map tiles)",
    "telia_coverage": "https://www.telia.no/dekningskart/  (operator coverage map tiles)",
    "ice_coverage": "https://www.ice.no/dekning/  (operator coverage map)",
    # Generic WMS/tile note: many are XYZ raster tiles keyed to a strength colour ramp;
    # a proper import samples the raster on GRID cell centres.
}


@dataclass
class Mast:
    lat: float
    lon: float
    eirp_dbm: float = 63.0      # typical macro-cell EIRP per sector (~2 kW ERP)
    band: str = "B20"
    freq_mhz: float = 811.0     # downlink centre; used for the propagation model


# --------------------------------------------------------------------------- propagation / coverage model
def _pathloss_db(dist_km, freq_mhz, n=3.5, ref_km=1.0):
    """Log-distance path loss (dB): free-space reference at ``ref_km`` plus a
    ``10 n log10(d/ref)`` slope. ``n`` ~3.5 is a rural/suburban macro exponent.
    Distances below 50 m are clamped to avoid a singularity."""
    d = np.maximum(np.asarray(dist_km, float), 0.05)
    fspl_ref = 32.44 + 20 * np.log10(ref_km) + 20 * np.log10(freq_mhz)   # dB at ref_km
    return fspl_ref + 10.0 * n * np.log10(d / ref_km)


def coverage_prob_from_rx(rx_dbm, sensitivity_dbm=-110.0, spread_db=8.0):
    """Map received power to a served-probability with a logistic link centred on
    the receiver sensitivity. ``spread_db`` is the shadow-fading scale."""
    return 1.0 / (1.0 + np.exp(-(np.asarray(rx_dbm, float) - sensitivity_dbm) / spread_db))


def coverage_field_from_masts(masts: Sequence[Mast], grid: Grid = GRID, *, n: float = 3.5,
                              sensitivity_dbm: float = -110.0, spread_db: float = 8.0,
                              coarse: bool = True):
    """Coverage probability on ``grid`` from mast sites (max over masts).

    Returns (coverage_prob, best_rx_dbm) as full-grid arrays. Computed on a
    coarse 0.02x0.04 deg lattice then bilinearly upsampled (coverage varies
    slowly), because a per-cell all-masts loop over the full grid is wasteful.
    """
    if not masts:
        return None, None
    if coarse:
        clats, clons = coarse_axes(box=(grid.lat_min, grid.lat_max, grid.lon_min, grid.lon_max))
        LA, LO = np.meshgrid(clats, clons, indexing="ij")
    else:
        LA, LO = grid.mesh()
        clats, clons = grid.lats, grid.lons
    best_rx = np.full(LA.shape, -300.0)
    for m in masts:
        d = haversine(LA, LO, m.lat, m.lon)             # km
        rx = m.eirp_dbm - _pathloss_db(d, m.freq_mhz, n=n)
        best_rx = np.maximum(best_rx, rx)
    prob = coverage_prob_from_rx(best_rx, sensitivity_dbm, spread_db)
    if coarse:
        prob = np.clip(upsample(prob, clats, clons, grid), 0.0, 1.0)
        best_rx = upsample(best_rx, clats, clons, grid)
    return prob, best_rx


def coverage_loglik(coverage_prob, floor_prob=1e-3):
    """Log-likelihood shape for the 'cellular uplink' hypothesis: s(x) ∝ P(served
    | x). NaN where coverage is unknown; a small floor keeps dead zones from
    going to -inf (the box could be served by an unlisted mast)."""
    p = np.asarray(coverage_prob, float)
    p = np.where(np.isnan(p), np.nan, np.clip(p, floor_prob, 1.0))
    return np.log(p)


# --------------------------------------------------------------------------- live fetch (fails soft)
def fetch_nkom_masts(bbox=(58.0, 64.5, 4.5, 13.5), *, timeout=20.0) -> Optional[List[Mast]]:
    """Attempt to fetch base-station sites from a live source (Finnsenderen / Nkom).

    Returns None on any failure (no network in this container, endpoint down,
    schema change). The caller then skips the layer. Runs on the user's machine.
    """
    try:
        import requests
    except Exception:
        log.warning("requests not available for coverage fetch")
        return None
    try:  # pragma: no cover - network path, never exercised in tests
        # NOTE: Finnsenderen has no stable open JSON API; a real implementation
        # scrapes its map backend or imports the Nkom open dataset. We only
        # attempt a HEAD/GET and fail soft, documenting the endpoints instead.
        r = requests.get("https://finnsenderen.no/", timeout=timeout)
        r.raise_for_status()
        log.warning("coverage: reached finnsenderen.no but no parser implemented; "
                    "download the Nkom dataset and pass masts= explicitly. Endpoints: %s",
                    COVERAGE_ENDPOINTS)
        return None
    except Exception as e:  # pragma: no cover
        log.warning("coverage fetch failed (expected offline): %s. Endpoints: %s",
                    e, list(COVERAGE_ENDPOINTS))
        return None


# --------------------------------------------------------------------------- layer emission
def build_layer(masts: Optional[Sequence[Mast]] = None, coverage_prob=None, *,
                grid: Grid = GRID, out_dir=None, name: str = "coverage_4g",
                reliability: float = 0.3, region=None, cfg: Optional[dict] = None):
    """Write ``data/hordewatch/layers/coverage_4g.npz`` for the cellular-uplink
    hypothesis, or return None (and log) when there is no coverage information.

    Provide either ``coverage_prob`` (a full-grid probability field) or
    ``masts`` (sites, from which a footprint is synthesised). ``region`` = (lat_min,
    lat_max, lon_min, lon_max) restricts output to a sub-grid.
    """
    out_dir = out_dir or DEFAULT_LAYERS_DIR
    if coverage_prob is None:
        if masts is None:
            masts = fetch_nkom_masts()
        if not masts:
            log.warning("coverage: no mast/coverage data available -> not emitting %s "
                        "(this is correct fail-soft behaviour; supply masts= on the user's machine)", name)
            return None
        coverage_prob, _ = coverage_field_from_masts(masts, grid)
    ll = coverage_loglik(coverage_prob)

    g = grid
    if region is not None:
        g = sub_grid(*region, base=grid)
        i0, j0 = grid.index(g.lat_min, g.lon_min)
        ll = ll[i0:i0 + g.nlat, j0:j0 + g.nlon]

    desc = ("Cellular-uplink hypothesis only: box likely inside 4G/5G coverage. "
            "Low reliability (0.3) because Starlink is equally plausible. "
            "Coverage footprint synthesised from base-station sites (rural log-distance model) "
            "unless a real coverage raster was supplied.")
    path = write_layer(out_dir / f"{name}.npz", ll, name=name, reliability=reliability,
                       independence_group="uplink_cellular", description=desc,
                       sources=[COVERAGE_ENDPOINTS["nkom_finnsenderen"]], grid=g,
                       extra={"hypothesis": "cellular_uplink", "n_masts": len(masts) if masts else None})
    log.info("wrote coverage layer %s (reliability %.2f)", path, reliability)
    return path


# --------------------------------------------------------------------------- discriminator note
def discriminator_note() -> str:
    return (
        "Starlink vs cellular from stream health (see analyzers/stream_health.uplink_signature):\n"
        "  Starlink : short (<=15 s) micro-stalls whose on-site start times cluster on the global\n"
        "             15 s satellite-reallocation clock (unix_time mod 15 ~ 12 s); extra whole-slot\n"
        "             outages when a branch obstructs the scheduled satellite; outages correlate with\n"
        "             rain fade. A Rayleigh test on stall phase (period 15 s), an inter-interval\n"
        "             multiple-of-15 test, and a Lomb-Scargle line at 1/15 Hz all fire -> starlink_like.\n"
        "  Cellular : longer, aperiodic congestion/handover stalls and bitrate dips concentrated in the\n"
        "             evening busy hour (Europe/Oslo); no 15 s periodicity -> cellular_like.\n"
        "Use the verdict to gate THIS layer: keep/raise it only if cellular_like; drop it if starlink_like."
    )


def apply_verdict(reliability: float, uplink_verdict: Optional[str], confidence: float = 0.5) -> Optional[float]:
    """Adjust the coverage-layer reliability given a stream_health uplink verdict.

    Returns a new reliability, or None meaning 'do not emit the layer' when the
    uplink looks like Starlink. ``confidence`` is the verdict's own confidence."""
    if uplink_verdict == "starlink_like" and confidence >= 0.5:
        return None
    if uplink_verdict == "cellular_like":
        return float(min(0.6, reliability + 0.25 * confidence))
    return float(reliability)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Cellular coverage evidence layer (fails soft offline).")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--reliability", type=float, default=0.3)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print(discriminator_note())
    p = build_layer(out_dir=a.out_dir, reliability=a.reliability)
    print("wrote" if p else "no coverage data (fail-soft); see COVERAGE_ENDPOINTS", p or "")
