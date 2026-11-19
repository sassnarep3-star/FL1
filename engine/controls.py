"""Control baselines for every leaderboard run (requirement R76, session arena/9fccbb0e-fl1, task K1).

WHY CONTROLS
------------
A candidate strategy only means something if it beats the rules that need no insight at all:
  * RANDOM   - pick a side of every game with a fixed, pre-registered seed (no information);
  * FAVOURITE - always back the market favourite (the simplest informed rule anyone can run).
Both are scored with the same proper score (the Brier score) as a probability forecast, so
that a candidate can later be placed on the same scale. A candidate must beat both.

SIGN CONVENTION (verified in this session, not assumed)
-------------------------------------------------------
In the nflverse games feed used by this repository, `spread_line` is POSITIVE when the HOME
team is the favourite and negative when the AWAY team is the favourite. Evidence, reproduced by
tests/test_controls_k1.py directly from data/raw/games.csv:
  * the home team is the moneyline favourite (lower home moneyline) in 99.4% of 5,198 regular-
    season games that have both a spread and both moneylines; the disagreeing rows are counted,
    not hidden;
  * the correlation of the home margin with +spread_line is +0.43 (with -spread_line, -0.43).
Note: data/line_board.json and scripts/build_line_board.py label the same column "negative =
home favourite". That label contradicts this evidence and is logged as an irregularity (F73).

This module is standard-library only (the engine policy in requirements.txt); the pandas
layer that feeds it lives in scripts/strategy_lab.py.
"""
from __future__ import annotations

import math
import random

CONTROL_SEED = 20261119          # pre-registered 2026-11-19 (K1). Changing it = a new control.
COINFLIP_BRIER = 0.25            # Brier score of the uninformed forecast p = 0.5 on a binary outcome.
Z95 = 1.959963984540054


def random_sides(n: int, seed: int = CONTROL_SEED) -> list[str]:
    """One side per game, in the order given. 'home' or 'away'.

    Uses random.Random (Mersenne Twister), whose stream is stable across Python releases, so the
    random control does not move when numpy or pandas is upgraded.
    """
    rng = random.Random(seed)
    return ["home" if rng.random() < 0.5 else "away" for _ in range(n)]


def favourite_side(spread_line: float) -> str:
    """The side the market favours, using the verified convention above.

    Callers must exclude pick'em games (spread_line == 0): there is no favourite to back.
    """
    if spread_line is None or (isinstance(spread_line, float) and math.isnan(spread_line)):
        raise ValueError("no spread: a favourite cannot be defined")
    if spread_line == 0:
        raise ValueError("pick'em: no favourite (exclude the game)")
    return "home" if spread_line > 0 else "away"


def brier(forecasts: list[float], outcomes: list[int]) -> dict:
    """Mean Brier score with a normal-approximation 95% interval.

    The bets here are one per game, so the game is the unit and no further clustering exists.
    Returns n=0 and None values for an empty sample rather than inventing a number.
    """
    if len(forecasts) != len(outcomes):
        raise ValueError("forecasts and outcomes differ in length")
    n = len(forecasts)
    if n == 0:
        return {"n": 0, "brier": None, "se": None, "ci_low": None, "ci_high": None}
    for p in forecasts:
        if not (0.0 <= p <= 1.0):
            raise ValueError("forecast outside [0, 1]")
    for y in outcomes:
        if y not in (0, 1):
            raise ValueError("outcome must be 0 or 1")
    d = [(p - y) ** 2 for p, y in zip(forecasts, outcomes)]
    mean = sum(d) / n
    if n > 1:
        var = sum((x - mean) ** 2 for x in d) / (n - 1)
        se = math.sqrt(var / n)
    else:
        se = None
    ci_low = mean - Z95 * se if se is not None else None
    ci_high = mean + Z95 * se if se is not None else None
    return {
        "n": n,
        "brier": round(mean, 6),
        "se": round(se, 6) if se is not None else None,
        "ci_low": round(ci_low, 6) if ci_low is not None else None,
        "ci_high": round(ci_high, 6) if ci_high is not None else None,
    }


def train_cover_rate(outcomes: list[int]) -> float:
    """Forecast for the favourite-control: the favourite's cover rate on TRAINING seasons only.

    Fixed before any out-of-sample game is scored, so the control never sees its own test data.
    """
    if not outcomes:
        raise ValueError("no training outcomes: the favourite forecast is undefined")
    return sum(outcomes) / len(outcomes)
