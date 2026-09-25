"""Layer contract.

A layer turns one piece of evidence into a log-likelihood surface
``loglik[i, j] = log P(evidence | box in cell) - log P(evidence | box elsewhere)``
up to an additive constant (only differences between cells matter).

* NaN means "no information here" and is treated as the layer's neutral value
  (the median over covered cells), so gaps in coverage neither reward nor
  punish a cell.
* ``reliability`` is the probability that the evidence itself is valid (the
  hint is read correctly, the flight match is right, ...). Fusion uses the
  robust mixture  L' = r * L + (1 - r) * 1, so an unreliable hint can at most
  cost a cell log(1 - r) - it can never zero it out.
* Layers that come from the same underlying observation share an
  ``independence_group``; fusion takes the reliability-weighted mean inside a
  group instead of summing, to avoid double counting.
"""
from dataclasses import dataclass, field

import numpy as np


@dataclass
class LayerResult:
    name: str
    loglik: np.ndarray
    reliability: float
    independence_group: str
    description: str = ""
    sources: list = field(default_factory=list)
    hard: bool = False  # hard=True: cells with loglik == -inf are excluded outright

    def normalised(self):
        """Neutral-filled log-likelihood with max 0 (finite except hard -inf)."""
        ll = np.array(self.loglik, dtype=float)
        covered = np.isfinite(ll)
        if not covered.any():
            return np.zeros_like(ll)
        neutral = np.median(ll[covered])
        out = np.where(np.isnan(ll), neutral, ll)
        return out - np.max(out[np.isfinite(out)])

    def robust(self):
        """log( r * L + (1 - r) ), L = exp(normalised loglik)."""
        ll = self.normalised()
        if self.hard:
            return ll
        r = float(np.clip(self.reliability, 0.0, 0.999))
        with np.errstate(over="ignore", under="ignore"):
            return np.log(r * np.exp(ll) + (1.0 - r))


def gaussian_ll(x, mu, sigma):
    return -0.5 * ((np.asarray(x) - mu) / sigma) ** 2


def band_ll(x, lo, hi, soft):
    """0 inside [lo, hi], Gaussian fall-off with scale `soft` outside."""
    x = np.asarray(x, float)
    d = np.where(x < lo, lo - x, np.where(x > hi, x - hi, 0.0))
    return -0.5 * (d / soft) ** 2
