"""Joint pricing of parlay and prop-combo legs.

Why this module exists: the value of a multi-leg bet is not the product of the values
of its legs, and the size of that error is the size of the correlation. The brief asks
for correlation *values*; the honest deliverable today is (a) the estimator, (b) the
handling rules, and (c) blanks where a measurement is owed. This module produces a
number only from data or an explicit simulation you pass in.
"""

from __future__ import annotations

import math
import random
from typing import Sequence

from . import pricing


# ---------------------------------------------------------------------------
# Bernoulli algebra: exact for two binary legs
# ---------------------------------------------------------------------------


def joint_prob_from_rho(p_a: float, p_b: float, rho: float) -> float:
    """P(A and B) for two binary events given their correlation.

    P(AB) = pA pB + rho * sqrt(pA qA pB qB). Clipped to the Frechet bounds, because a
    rho inconsistent with the marginals otherwise returns an impossible probability --
    and an impossible probability in a pricing path is a silent, expensive bug.
    """
    lo = max(0.0, p_a + p_b - 1.0)
    hi = min(p_a, p_b)
    cov = rho * math.sqrt(p_a * (1 - p_a) * p_b * (1 - p_b))
    return min(hi, max(lo, p_a * p_b + cov))


def rho_from_joint(p_a: float, p_b: float, p_ab: float) -> float:
    """The correlation implied by an observed joint frequency (the inverse map)."""
    denom = math.sqrt(p_a * (1 - p_a) * p_b * (1 - p_b))
    if denom <= 0:
        raise ValueError("a degenerate marginal carries no correlation information")
    return (p_ab - p_a * p_b) / denom


def conditional(p_ab: float, p_b: float) -> float:
    if p_b <= 0:
        raise ValueError("conditioning event has zero probability")
    return p_ab / p_b


def correlation_premium(p_a: float, p_b: float, rho: float) -> float:
    """How much the true joint probability exceeds the product of marginals.

    This is the quantity a bettor's eye should be on: if the operator's combined price
    already embeds it, there is no 'extra value from correlation' to collect.
    """
    return joint_prob_from_rho(p_a, p_b, rho) - p_a * p_b


def two_leg_ev(american_a: float, american_b: float, p_a: float, p_b: float,
               rho: float | None) -> dict:
    """Compare the naive and the joint-aware valuation of a two-leg parlay.

    With `rho=None` the joint number is reported as unavailable rather than assumed
    independent: the difference between 'we do not know' and 'we assume zero', which
    is the difference between an honest tool and one that manufactures confidence.
    """
    dec = pricing.parlay_decimal([american_a, american_b])
    naive_p = p_a * p_b
    out = {
        "combined_decimal": dec,
        "break_even_joint_prob": 1.0 / dec,
        "naive": {
            "joint_prob": naive_p,
            "ev_per_unit": naive_p * dec - 1.0,
            "validity": "exact only if the legs are independent, which same-game legs are not",
        },
        "joint": None,
    }
    if rho is not None:
        jp = joint_prob_from_rho(p_a, p_b, rho)
        out["joint"] = {"rho": rho, "joint_prob": jp, "ev_per_unit": jp * dec - 1.0,
                        "delta_vs_naive": (jp - naive_p) * dec}
    else:
        out["joint"] = {"rho": None, "joint_prob": None, "ev_per_unit": None,
                        "delta_vs_naive": None,
                        "blocking_reason": "rho not measured (GAP-01: joint price history)"}
    return out


def sensitivity_to_rho(p_a: float, p_b: float, dec: float, rho: float,
                       perturbation: float = 0.05) -> dict:
    """EV at rho and at rho +/- the perturbation, per unit staked.

    The required practice for any multi-leg bet: if a plausible error in the
    correlation flips the sign of the EV, the bet is a model artefact and must be
    refused rather than sized down.
    """
    out = {}
    for label, r in (("low", rho - perturbation), ("central", rho), ("high", rho + perturbation)):
        jp = joint_prob_from_rho(p_a, p_b, r)
        out[label] = {"rho": r, "joint_prob": jp, "ev_per_unit": jp * dec - 1.0}
    sign_flip = (out["low"]["ev_per_unit"] <= 0 <= out["high"]["ev_per_unit"]) or \
                (out["low"]["ev_per_unit"] >= 0 >= out["high"]["ev_per_unit"])
    out["decision"] = "REFUSE: EV is inside the noise of the correlation assumption" if sign_flip \
        else "robust to the assumed perturbation"
    return out


# ---------------------------------------------------------------------------
# score-driven joint simulation (works for any number of legs)
# ---------------------------------------------------------------------------


def simulate_game_outcomes(mu_total: float, sd_total: float, mu_margin: float,
                            sd_margin: float, rho_mt: float, n_sims: int = 20000,
                            seed: int = 20261114) -> list[tuple[float, float]]:
    """Simulate (total, margin) pairs from a bivariate normal with given parameters.

    A deliberate simplification: real scoring is discrete, bounded and has an
    overtime tail, and a 5-point total line is settled in half-point steps. It is used
    here to *bound the size of the correlation effect*, not to price a specific book.
    All five parameters must come from your own fitted distribution: they are
    arguments, never constants, because a hard-coded rho here would propagate into
    every parlay decision in the system while looking like code rather than like a guess.
    """
    rng = random.Random(seed)
    if not -0.999 <= rho_mt <= 0.999:
        raise ValueError("rho_mt must be in (-1, 1)")
    out = []
    for _ in range(n_sims):
        z1 = rng.gauss(0.0, 1.0)
        z2 = rng.gauss(0.0, 1.0)
        total = mu_total + sd_total * z1
        margin = mu_margin + sd_margin * (rho_mt * z1 + math.sqrt(1 - rho_mt ** 2) * z2)
        out.append((total, margin))
    return out


def leg_event_probabilities(outcomes: Sequence[tuple[float, float]], total_line: float,
                            spread_line: float) -> dict:
    """Empirical joint probabilities of the classic correlated pair: total Over and
    home side of the spread. Computed from a simulated or historical sample."""
    if not outcomes:
        raise ValueError("no outcomes supplied")
    n = len(outcomes)
    over = sum(1 for t, _ in outcomes if t > total_line)
    cover = sum(1 for _, m in outcomes if m > spread_line)
    both = sum(1 for t, m in outcomes if t > total_line and m > spread_line)
    p_over, p_cover = over / n, cover / n
    p_both = both / n
    return {
        "n": n,
        "p_over": p_over,
        "p_cover": p_cover,
        "p_both": p_both,
        "rho": rho_from_joint(p_over, p_cover, p_both) if p_over not in (0.0, 1.0) and p_cover not in (0.0, 1.0) else None,
        "product_of_marginals": p_over * p_cover,
        "dependence_excess": p_both - p_over * p_cover,
    }


def implied_rho_from_market(p_a: float, p_b: float, american_combined: float,
                            hold_assumption: float = 0.0) -> dict:
    """Back out the correlation a combined price implies, given the leg prices.

    If the operator's SGP price is 'fair' after removing its margin, the joint
    probability it prices is 1/decimal, so the correlation it embeds follows from the
    marginals. `hold_assumption` must be the measured combined-market hold, not zero --
    leaving it at zero attributes every cent of margin to correlation, which is the
    most flattering possible reading of our own model and the least defensible one.
    """
    dec = pricing.parlay_decimal([american_combined])
    # A price's break-even probability overstates the true probability by exactly the
    # margin the book keeps, so the margin is divided out (never multiplied).
    p_joint_market = (1.0 / dec) / (1.0 + hold_assumption)
    naive = p_a * p_b
    try:
        rho = rho_from_joint(p_a, p_b, p_joint_market)
    except ValueError:
        rho = None
    return {"p_joint_implied": p_joint_market, "p_joint_naive": naive,
            "implied_rho": rho,
            "caveat": "single-number inversion; the operator's margin is not observable per-market and may be allocated arbitrarily across legs"}
