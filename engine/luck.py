#!/usr/bin/env python3
"""
engine/luck.py — the "removal of luck" arithmetic.

Standard library only. Every function here answers one question: how much of an
observed result could chance alone produce, and how many decisions would it take
before chance stops being a plausible explanation?

The point of the panel is not to flatter a strategy. It is to publish, before
any result exists, the size of the sample at which a result would mean anything.
A leaderboard that ranks on a number nobody has earned is a lottery with a
scoreboard; this module supplies the yardstick.

Definitions used (all conventional, all stated on the page):

  luck band        the 95% interval within which the hit rate of a strategy with
                   NO skill would fall, at a given number of decisions n.
  Wilson interval  score interval for a proportion; used instead of the normal
                   approximation because hit rates near 0 and 1 are common in
                   small samples and the normal interval misbehaves there.
  required n       number of independent decisions needed to detect an edge of
                   d over a base rate p, two-sided alpha, power 1-beta:

                       n = (z_{1-a/2} + z_{1-b})^2 * p(1-p) / d^2

  cluster inflation  when several decisions sit inside one game (a same-game
                   parlay, a prop combo), the decisions are not independent.
                   The effective sample is n_eff = n / (1 + (m-1) * ICC), where
                   m is decisions per game and ICC the intra-cluster
                   correlation. ICC is NOT measured in this repository, so the
                   panel publishes a sensitivity grid over ICC and marks the
                   measured value blank (flag: no joint-outcome source).
  multiplicity     trying k strategies and ranking the best inflates false
                   positives. The panel reports the Bonferroni-adjusted alpha
                   and the n it implies.
"""

import math
from math import comb


# ------------------------------------------------------------------ utilities
def norm_cdf(x):
    """Standard normal CDF. math.erf is exact to machine precision, so no
    series approximation is needed here."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def z_crit(alpha_two_sided):
    """Two-sided critical value, e.g. alpha=0.05 -> 1.959964."""
    target = 1.0 - alpha_two_sided / 2.0
    lo, hi = 0.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if norm_cdf(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ------------------------------------------------------------- intervals
def wilson_interval(k, n, alpha=0.05):
    """Wilson score interval for a proportion. Returns (lo, hi) or (None, None)."""
    if n <= 0:
        return (None, None)
    z = z_crit(alpha)
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    spread = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def luck_band(n, p=0.5, alpha=0.05):
    """95% interval for the OBSERVED hit rate of a skill-free strategy.

    This is the number that answers 'could that be luck?'. A strategy whose hit
    rate sits inside its own band has not demonstrated anything.
    """
    if n <= 0:
        return (None, None)
    z = z_crit(alpha)
    half = z * math.sqrt(p * (1 - p) / n)
    return (max(0.0, p - half), min(1.0, p + half))


# -------------------------------------------------------------------- sizing
def required_n(p, edge, alpha=0.05, power=0.80):
    """Independent decisions needed to detect `edge` (a proportion, e.g. 0.05)
    above base rate p, two-sided alpha, given power."""
    if edge <= 0 or p <= 0 or p >= 1:
        return None
    za = z_crit(alpha)
    zb = z_crit(2 * (1 - power))  # one-sided tail converted to two-sided input
    return math.ceil((za + zb) ** 2 * p * (1 - p) / (edge * edge))


def cluster_design_effect(m, icc):
    """Variance inflation for m correlated decisions per cluster."""
    if m is None or icc is None or m < 1:
        return None
    return 1.0 + (m - 1.0) * icc


def effective_n(n, m, icc):
    """Independent-decision equivalent of n clustered decisions."""
    if n is None:
        return None
    de = cluster_design_effect(m, icc)
    if not de:
        return n
    return int(math.floor(n / de))


def bonferroni_alpha(alpha, k):
    """Per-comparison alpha that holds the family-wise rate at `alpha` over k
    independent comparisons."""
    if k is None or k < 1:
        return alpha
    return alpha / k


# ----------------------------------------------------------------- scoring
def brier(forecasts, outcomes):
    """Mean squared error of probability forecasts against 0/1 outcomes."""
    if not forecasts:
        return None
    return sum((f - o) ** 2 for f, o in zip(forecasts, outcomes)) / len(forecasts)


def brier_skill_score(forecasts, outcomes, benchmark_forecasts):
    """BSS = 1 - BS_model / BS_benchmark. 0 means no improvement on the
    benchmark; negative means worse than the benchmark."""
    bs = brier(forecasts, outcomes)
    bs_ref = brier(benchmark_forecasts, outcomes)
    if bs is None or bs_ref in (None, 0):
        return None
    return 1.0 - bs / bs_ref


def constant_brier(p, outcomes):
    """Brier score of forecasting the same probability every time."""
    if not outcomes:
        return None
    return sum((p - o) ** 2 for o in outcomes) / len(outcomes)


def binomial_p_two_sided(k, n, p=0.5):
    """Exact two-sided binomial test p-value. Pure python; fine for the sample
    sizes this project will see for a long while."""
    if n <= 0:
        return None
    pk = [comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(n + 1)]
    obs = pk[k]
    return min(1.0, sum(q for q in pk if q <= obs * (1 + 1e-12)))
