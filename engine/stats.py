"""Estimation and multiple-testing machinery: the tools that remove luck.

Deliberately dependency-free. The bootstrap and max-T implementations are standard
procedures written plainly rather than borrowed, so a reviewer can read the ten lines
that decide whether a strategy is funded. Where a well-known method is approximated,
the approximation is named in the docstring; the code never claims more than it does.
"""

from __future__ import annotations

import math
import random
from typing import Callable, Sequence

SQRT2 = math.sqrt(2.0)


# ---------------------------------------------------------------------------
# normal distribution helpers
# ---------------------------------------------------------------------------


def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / SQRT2))


def norm_ppf(p: float) -> float:
    """Inverse standard normal CDF (Acklam's rational approximation).

    Absolute error is about 1e-9 in the central region, which is far tighter than
    anything in this project needs; documented so nobody mistakes it for a table
    lookup of record.
    """
    if not 0.0 < p < 1.0:
        raise ValueError("p must be strictly between 0 and 1")
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155043206e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00]
    plow, phigh = 0.02425, 1.0 - 0.02425
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    if p > phigh:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)


# ---------------------------------------------------------------------------
# proportions
# ---------------------------------------------------------------------------


def mean(xs: Sequence[float]) -> float:
    if not xs:
        raise ValueError("empty sample")
    return sum(xs) / len(xs)


def sample_sd(xs: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        raise ValueError("need at least two observations")
    mu = mean(xs)
    return math.sqrt(sum((x - mu) ** 2 for x in xs) / (n - 1))


def wilson_interval(k: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Preferred over the normal 'plus or minus' interval because a hit rate near the
    boundary (a small-sample prop strategy) must not be reported with an interval
    that runs past 0 or 1.
    """
    if n == 0:
        return (0.0, 1.0)
    z = norm_ppf(0.5 + conf / 2.0)
    phat = k / n
    denom = 1.0 + z * z / n
    centre = (phat + z * z / (2.0 * n)) / denom
    half = (z / denom) * math.sqrt(phat * (1.0 - phat) / n + z * z / (4.0 * n * n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def proportion_se(p: float, n: int) -> float:
    return math.sqrt(max(p, 1e-12) * (1.0 - p) / n)


def z_stat(p_hat: float, p0: float, n: int) -> float:
    """One-sample z statistic of an observed hit rate against a hurdle."""
    return (p_hat - p0) / proportion_se(p0, n)


def one_sided_p_above(z: float) -> float:
    """P(Z >= z) under the standard normal."""
    return 1.0 - norm_cdf(z)


# ---------------------------------------------------------------------------
# power analysis: the honest answer to 'how many bets do we need'
# ---------------------------------------------------------------------------


def required_sample(p_hurdle: float, p_true: float, alpha: float = 0.05,
                    power: float = 0.80, one_sided: bool = True) -> int:
    """Bets needed to detect `p_true` against `p_hurdle` with the given power.

    Normal approximation to the two-proportion test with unpooled variance, the
    standard textbook form:

        n = ( z_(1-alpha) * sqrt(p0 q0) + z_(1-beta) * sqrt(p1 q1) )^2 / (p1 - p0)^2

    For -110 singles (hurdle 0.52381) and a 55% true hit rate at 80% power this is
    about 2,240 bets -- which is the number that decides whether 'selective' can
    afford to mean many small edges or must mean few large ones.
    """
    if not (0 < p_hurdle < 1 and 0 < p_true < 1):
        raise ValueError("probabilities must be in (0,1)")
    if p_true <= p_hurdle:
        raise ValueError("p_true must exceed the hurdle; there is nothing to detect")
    za = norm_ppf(1.0 - alpha if one_sided else 1.0 - alpha / 2.0)
    zb = norm_ppf(power)
    num = za * math.sqrt(p_hurdle * (1 - p_hurdle)) + zb * math.sqrt(p_true * (1 - p_true))
    return int(math.ceil((num / (p_true - p_hurdle)) ** 2))


def detectable_edge(n: int, p_hurdle: float, alpha: float = 0.05,
                    power: float = 0.80) -> float:
    """Smallest true hit rate distinguishable from the hurdle with n bets (bisection).

    The inverse question, and the one a leaderboard should publish: given the bets an
    entrant will realistically accumulate, what edge size could we even prove?
    """
    if n < 10:
        raise ValueError("n too small for the normal approximation")
    lo, hi = p_hurdle + 1e-4, 0.999
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if required_sample(p_hurdle, mid, alpha, power) > n:
            lo = mid
        else:
            hi = mid
    return hi


# ---------------------------------------------------------------------------
# bootstrap
# ---------------------------------------------------------------------------


def bootstrap_ci(values: Sequence[float], statistic: Callable[[Sequence[float]], float] = mean,
                 n_boot: int = 4000, conf: float = 0.95, seed: int = 20261114) -> tuple[float, float, float]:
    """Percentile bootstrap: returns (point, lower, upper).

    Percentile method, not BCa: with a few hundred bets the difference is a rounding
    argument we are not making. `lower` is the pessimistic bound the leaderboard ranks
    on, which is the entire point of the exercise.
    """
    if len(values) < 5:
        raise ValueError("need at least five observations to bootstrap meaningfully")
    rng = random.Random(seed)
    n = len(values)
    stats = []
    for _ in range(n_boot):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        stats.append(statistic(sample))
    stats.sort()
    lo_i = int(math.floor((1.0 - conf) / 2.0 * n_boot))
    hi_i = int(math.ceil((1.0 + conf) / 2.0 * n_boot)) - 1
    lo_i = max(0, min(lo_i, n_boot - 1))
    hi_i = max(0, min(hi_i, n_boot - 1))
    return statistic(values), stats[lo_i], stats[hi_i]


def paired_bootstrap_diff(a: Sequence[float], b: Sequence[float], n_boot: int = 4000,
                          conf: float = 0.95, seed: int = 20261114) -> tuple[float, float, float]:
    """Ledoit-Wolf-flavoured paired stationary bootstrap of mean(a) - mean(b).

    Fixed block length 8 (a geometric draw is the original's refinement; the block
    structure is what matters for serial dependence in a bet sequence, and it is
    stated here rather than hidden). Used to compare two strategies on the same games
    and to compare a strategy against its own benchmark.
    """
    if len(a) != len(b) or len(a) < 20:
        raise ValueError("paired comparison needs aligned samples of at least 20 bets")
    rng = random.Random(seed)
    n = len(a)
    block = 8
    diffs = []
    for _ in range(n_boot):
        da = 0.0
        i = 0
        count = 0
        while count < n:
            start = rng.randrange(n)
            for j in range(block):
                if count >= n:
                    break
                idx = (start + j) % n
                da += a[idx] - b[idx]
                count += 1
        diffs.append(da / n)
    diffs.sort()
    point = mean([x - y for x, y in zip(a, b)])
    lo = diffs[int(math.floor((1 - conf) / 2 * n_boot))]
    hi = diffs[int(math.ceil((1 + conf) / 2 * n_boot)) - 1]
    return point, lo, hi


# ---------------------------------------------------------------------------
# multiple comparisons: is the winner better, or just the luckiest of many?
# ---------------------------------------------------------------------------


def reality_check_pvalue(loss_matrix: Sequence[Sequence[float]], n_boot: int = 2000,
                         seed: int = 20261114, block: int = 10) -> tuple[float, int, float]:
    """White's Reality Check (simplified, documented) for a field of candidate models.

    `loss_matrix[t][k]` is the per-period loss difference of strategy k against the
    benchmark (positive = strategy is worse). H0: no strategy beats the benchmark.
    We take the max of the mean losses, and compare it against a block-bootstrap
    distribution of that same max-T statistic resampled from the *centred* matrix, so
    that the null imposes 'nobody has an edge'.

    Returns (p_value, index_of_best_strategy, observed_stat). This is the max-T of
    White (2000) with a stationary-block flavour and Hansen's studentisation *not*
    applied: it is therefore conservative relative to the SPA of Hansen (2005), which
    is the right direction of error for a funding decision but must not be described
    as the SPA itself.
    """
    t = len(loss_matrix)
    if t < 30:
        raise ValueError("need at least 30 periods for a meaningful max-T bootstrap")
    k = len(loss_matrix[0])
    means = [mean([loss_matrix[i][j] for i in range(t)]) for j in range(k)]
    # best strategy minimises mean loss
    best = min(range(k), key=lambda j: means[j])
    observed = means[best]
    centred = [[loss_matrix[i][j] - means[j] for j in range(k)] for i in range(t)]
    rng = random.Random(seed)
    count = 0
    for _ in range(n_boot):
        idxs = []
        while len(idxs) < t:
            start = rng.randrange(t)
            for j in range(block):
                if len(idxs) < t:
                    idxs.append((start + j) % t)
        bmeans = [mean([centred[i][j] for i in idxs]) for j in range(k)]
        if min(bmeans) <= observed:
            count += 1
    return (count + 1.0) / (n_boot + 1.0), best, observed


def deflated_sharpe_ratio(returns: Sequence[float], trials: int,
                          trial_sharpe_sd: float | None = None) -> dict:
    """Deflated Sharpe ratio, following Bailey & Lopez de Prado's construction.

    `trial_sharpe_sd` is the dispersion of Sharpe ratios across *all* strategies
    considered (including the abandoned ones). If the caller does not supply it we
    cannot invent it, so we raise: a DSR computed with a made-up dispersion is
    precisely the kind of confident number this repository forbids.

    Returns the deflated statistic and the expected maximum Sharpe under the null of
    `trials` independent searches, so a reviewer can see the haircut that was applied.
    """
    if trials < 1:
        raise ValueError("trials must be >= 1")
    if trial_sharpe_sd is None:
        raise ValueError("trial_sharpe_sd required: pass the measured dispersion across all trials")
    n = len(returns)
    if n < 20:
        raise ValueError("need at least 20 observations")
    mu = mean(returns)
    sd = sample_sd(returns)
    sr = mu / sd
    m2 = sum((x - mu) ** 3 for x in returns) / n / sd ** 3      # skewness
    m3 = sum((x - mu) ** 4 for x in returns) / n / sd ** 4       # kurtosis
    gamma = 0.5772156649015329  # Euler-Mascheroni, the constant the DSR correction uses
    e_max = trial_sharpe_sd * ((1 - gamma) * norm_ppf(1 - 1.0 / trials)
                               + gamma * norm_ppf(1 - 1.0 / (math.e * trials)))
    denom = math.sqrt(max(1e-12, 1.0 - m2 * sr + (m3 - 1.0) / 4.0 * sr * sr))
    dsr = norm_cdf((sr - e_max) * math.sqrt(n - 1.0) / denom)
    return {"sharpe": sr, "expected_max_sharpe_under_null": e_max,
            "deflated_sharpe_probability": dsr, "n": n, "trials": trials,
            "note": "DSR is a probability that the Sharpe exceeds the selection-adjusted "
                    "benchmark; near 0.5 means the result is indistinguishable from the best "
                    "of `trials` coin flips."}


def jaccard(a: set, b: set) -> float:
    """Overlap of two bet sets; used to catch duplicated leaderboard entries (G-13)."""
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0
