"""Naive baseline fair-line model (requirements R23 and R24).

Purpose: produce the MODEL'S FAIR LINE for every market we originate, as a
number that can sit in its own column next to the market line and the
difference. This is the baseline estimator the line-origination spec already
mandates ("the first, mandatory estimator is the naive baseline: season points
differential per game"), formalised so it is reproducible.

Origination order (requirement R23): SIDE first, then TOTAL, then MONEYLINE.
The moneyline is derived from the side model's margin distribution, so it is
produced last — that ordering is a requirement, and `origination_order()` is
what the build scripts iterate.

Every coefficient is computed from an OFFICIAL input passed by the caller —
never hard-coded, never tuned on market prices:

    strength_t = (PF_t - PA_t) / G_t          official standings
    fair margin (home view) = HFA + (strength_h - strength_a)/2
    fair total              = (PPG_h + OPPG_h + PPG_a + OPPG_a) / 2
    fair home win prob      = Phi(fair margin / sd_margin)
    HFA, sd_margin          = computed over the official results feed

The /2 is a bookkeeping convention (each point of scoring differential is
produced by one side and consumed by the other) and is labelled as such on the
site. Uncertainty bands come from the sampling error of the margin estimate
(1/sqrt(G)) so a wide band is shown rather than implied precision.

Difference column (R24): difference = model fair − market. Positive means the
model makes the side/total higher than the market. The sign convention is part
of the published schema so it cannot be redefined after seeing results.
"""

from __future__ import annotations

import math
from typing import Mapping, Sequence

from . import stats


def origination_order():
    """R23: side first, then total, then moneyline."""
    return ("SIDE", "TOTAL", "MONEYLINE")


def team_strength(standings_rows: Sequence[Mapping]) -> dict:
    """strength = (PF-PA)/G, ppg = PF/G, oppg = PA/G — all from official rows."""
    out = {}
    for r in standings_rows:
        g = int(r["w"]) + int(r["l"]) + int(r["t"])
        if g <= 0:
            continue
        pf, pa = float(r["pf"]), float(r["pa"])
        out[r["abbr"]] = {
            "games": g, "pf": pf, "pa": pa,
            "ppg": pf / g, "oppg": pa / g,
            "strength": (pf - pa) / g,
        }
    return out


def home_field_advantage(results_rows: Sequence[Mapping]) -> dict:
    """Mean home margin over the official results feed. A computed coefficient,
    with its n, so the site can publish where it came from."""
    margins = [float(r["homePts"]) - float(r["awayPts"]) for r in results_rows]
    n = len(margins)
    mean = sum(margins) / n if n else None
    return {"hfa": mean, "n": n,
            "tier": "COMPUTED" if n else "BLANK"}


def margin_sd(results_rows: Sequence[Mapping]) -> dict:
    """SD of game margins over the official results feed — the scale that turns
    a fair margin into a fair win probability."""
    margins = [float(r["homePts"]) - float(r["awayPts"]) for r in results_rows]
    n = len(margins)
    if n < 2:
        return {"sd": None, "n": n, "tier": "BLANK"}
    mu = sum(margins) / n
    var = sum((m - mu) ** 2 for m in margins) / (n - 1)
    return {"sd": math.sqrt(var), "n": n, "tier": "COMPUTED"}


def fair_game(strength: Mapping, home: str, away: str,
              hfa: float, sd_margin: float, season_games: int) -> dict:
    """Fair SIDE (home-view spread), fair TOTAL, and fair MONEYLINE probability.
    Produced in requirement order; moneyline last because it is derived."""
    h, a = strength[home], strength[away]
    margin = hfa + (h["strength"] - a["strength"]) / 2.0
    total = (h["ppg"] + h["oppg"] + a["ppg"] + a["oppg"]) / 2.0
    # Sampling error of a per-game margin estimate grows as 1/sqrt(G); the
    # band is reported so nobody reads the point estimate as precision.
    band = 1.96 * (sd_margin / math.sqrt(max(season_games, 1))) if sd_margin else None
    out = {
        "order": 1,
        "market_type": "SIDE",
        "fair": round(-margin, 1),   # home-view spread: negative = home favourite
        "band": round(band, 1) if band is not None else None,
    }
    total_row = {
        "order": 2,
        "market_type": "TOTAL",
        "fair": round(total, 1),
        "band": round(band, 1) if band is not None else None,
    }
    p_home = stats.norm_cdf(margin / sd_margin) if sd_margin else None
    ml_row = {
        "order": 3,
        "market_type": "MONEYLINE",
        "fair": round(p_home, 4) if p_home is not None else None,
        "band": None,
    }
    return {"SIDE": out, "TOTAL": total_row, "MONEYLINE": ml_row,
            "fair_margin_home": round(margin, 2)}


def difference(fair, market):
    """R24: difference = model fair − market. None when either side is missing.
    A blank difference is a blank, never a zero."""
    if fair is None or market is None:
        return None
    return round(float(fair) - float(market), 2)
