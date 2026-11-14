"""Odds arithmetic, break-even hurdles, devigging, staking and parlay pricing.

Everything here is arithmetic on prices. Nothing here contains an opinion about
football: there are no effect sizes, no priors about scoring, no designation
probabilities. Those belong to a fitted model and would have to arrive with their
data. The one place a judgement is encoded is the default staking fraction, which is
documented as a default and is overridable by configuration.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

# ---------------------------------------------------------------------------
# price conversions
# ---------------------------------------------------------------------------


def american_to_decimal(american: float) -> float:
    """Convert an American price to decimal (total return per 1 unit staked).

    -110 -> 1.909090...   +100 -> 2.0   +150 -> 2.5
    """
    if american == 0:
        raise ValueError("american price cannot be 0")
    if american > 0:
        return 1.0 + american / 100.0
    return 1.0 + 100.0 / abs(american)


def decimal_to_american(dec: float) -> int:
    """Inverse of american_to_decimal, rounded to the cent-ish integer prices books use."""
    if dec <= 1.0:
        raise ValueError("decimal price must exceed 1.0")
    net = dec - 1.0
    if net >= 1.0:
        return int(round(net * 100))
    return int(round(-100.0 / net))


def net_odds(american: float) -> float:
    """Profit per 1 unit staked, i.e. the multiplier `m` used in Kelly's notation."""
    return american_to_decimal(american) - 1.0


def implied_probability(american: float) -> float:
    """Bookmaker's implied probability, including the vig. Not a true probability."""
    return 1.0 / american_to_decimal(american)


def break_even_probability(american: float) -> float:
    """Hit rate required to be flat at this price.

    -110 -> 110 / 210 = 0.52381 (the figure the academic literature uses as the
    standard hurdle, and the one our G-2 gate compares against). +150 -> 1.5/2.5 =
    0.6, which is why 'we hit 55% on longshots' can still be a losing book.
    """
    m = net_odds(american)
    return 1.0 / (1.0 + m)


def two_way_margin(american_a: float, american_b: float) -> float:
    """Overround (the theoretical hold) of a two-sided market, as a fraction.

    Both sides at -110 -> 1/1.90909*2 - 1 = 0.04545, the familiar 4.55%.
    """
    return implied_probability(american_a) + implied_probability(american_b) - 1.0


def devig_two_way(american_a: float, american_b: float) -> tuple[float, float]:
    """Proportionally-normalised 'no-vig' probabilities for a two-way market.

    This is the simplest fair-price estimator and it carries a known bias: it assumes
    the vig is spread proportionally, which sportsbooks demonstrably do not do
    (longshot-heavy prices keep more margin on the dog side). It is used for
    consistency checks and for the market-implied prior, never as a final probability.
    """
    pa = implied_probability(american_a)
    pb = implied_probability(american_b)
    s = pa + pb
    return pa / s, pb / s


# ---------------------------------------------------------------------------
# expected value
# ---------------------------------------------------------------------------


def ev_per_unit(p_win: float, american: float) -> float:
    """Expected profit per 1 unit staked at this price, given our probability.

    Positive means the price is better than our model says. A `p_win` derived from a
    fitted model must be accompanied by its uncertainty -- EV on a point probability
    is how a coin flip looks like an edge.
    """
    if not 0.0 <= p_win <= 1.0:
        raise ValueError("p_win must be in [0, 1]")
    return p_win * net_odds(american) - (1.0 - p_win)


def edge_in_points(our_total: float, market_total: float) -> float:
    """Signed gap between our number and the market's, in points (our - market)."""
    return our_total - market_total


def fair_price_for_edge(edge_points: float, sd_points: float) -> float:
    """Win probability a bettor gets from an edge, assuming margin noise ~ Normal.

    P(cover) = Phi(edge / sd_of_margin). The sd is a *model input the owner must
    supply from data*; there is no default here on purpose. Returns a probability for
    the side we are on, ignoring the vig.
    """
    if sd_points <= 0:
        raise ValueError("sd_points must be positive; supply it from your own residual variance")
    return 0.5 * (1.0 + math.erf((edge_points / sd_points) / math.sqrt(2.0)))


def hold_adjusted_ev(ev: float, measured_hold: float, assumed_hold: float) -> float:
    """Re-base an EV computed under one hold assumption onto a measured one.

    Until the regulator filings are parsed (gap GAP-08) the caller should pass the
    conservative family floor, not the 4.55% theoretical number, for parlays.
    """
    return ev - (measured_hold - assumed_hold)


# ---------------------------------------------------------------------------
# staking
# ---------------------------------------------------------------------------


def kelly_fraction(p_win: float, american: float) -> float:
    """Full Kelly fraction: (p*(1+m) - 1) / m.

    Kelly maximises the expected log of terminal wealth on a *repeated* bet with
    *known* p. Our p is an estimate with error, and the fraction is far more
    sensitive to p's error than to m, so full Kelly is never the operating number.
    See `fractional_kelly`.
    """
    m = net_odds(american)
    if m <= 0:
        raise ValueError("no positive payout available")
    return max(0.0, (p_win * (1.0 + m) - 1.0) / m)


def fractional_kelly(p_win: float, american: float, fraction: float = 0.25,
                     cap: float = 0.02) -> float:
    """Fraction of bankroll to stake, defaulting to a quarter of full Kelly capped
    at 2% of bankroll.

    The defaults are a risk posture, not a validated result: `fraction` and `cap`
    must come from the owner's mandate (open question Q-05). A cap is applied because
    an unbounded fraction on a confidently-wrong probability is how a model with a
    positive backtest bankrupts an operator.
    """
    if not 0.0 < fraction <= 1.0:
        raise ValueError("fraction must be in (0, 1]")
    return min(kelly_fraction(p_win, american) * fraction, cap)


# ---------------------------------------------------------------------------
# parlays
# ---------------------------------------------------------------------------


def parlay_decimal(prices: Sequence[float]) -> float:
    """Combined decimal price of a parlay, from American leg prices."""
    d = 1.0
    for a in prices:
        d *= american_to_decimal(a)
    return d


def parlay_ev_independent(our_probs: Sequence[float], prices: Sequence[float]) -> float:
    """Parlay EV under the independence assumption -- the naive calculation.

    Provided so it can be *contrasted* with `parlay_ev_joint`, not for use in
    production. Multiplying leg probabilities is only correct when the legs are
    independent, which same-game legs are not.
    """
    if len(our_probs) != len(prices):
        raise ValueError("probs and prices must align")
    p = 1.0
    for q in our_probs:
        p *= q
    return p * parlay_decimal(prices) - 1.0


def parlay_ev_joint(our_probs: Sequence[float], prices: Sequence[float],
                    joint_prob: float | None = None) -> float:
    """Parlay EV when we have a joint probability (from simulation or measurement).

    `joint_prob` must come from a model that prices the legs together, or from a
    measured empirical co-occurrence. If it is None the caller has not done the work
    and we refuse to guess, raising instead of silently falling back to independence.
    """
    if joint_prob is None:
        raise ValueError(
            "joint_prob required: refusing to price a parlay by multiplying singles"
        )
    return joint_prob * parlay_decimal(prices) - 1.0


def break_even_parlay(prices: Sequence[float]) -> float:
    """Joint probability needed to break even on this parlay at its combined price."""
    d = parlay_decimal(prices)
    return 1.0 / d


def product_of_breakevens(prices: Sequence[float]) -> float:
    """What the naive independent calculation would claim you need."""
    acc = 1.0
    for a in prices:
        acc *= break_even_probability(a)
    return acc
