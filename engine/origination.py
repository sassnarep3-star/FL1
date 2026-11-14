"""Market origination: order, and the three-column output (fair / market / difference).

The brief fixes the origination order: the SIDE first, then the TOTAL, then the
MONEYLINE. That order is not cosmetic — the side (spread) is where the model's
scoring differential is hardest to hide behind, the total comes second because it
shares the same scoring engine, and the moneyline last because it is a derivative
of the first two. This module makes the order executable so a pipeline cannot
quietly originate whatever it finds easiest first.

Every emitted row carries three SEPARATE columns, never a pre-computed blend:

    fair_line      the model's own number (None until a fitted model exists —
                   a fabricated fair line would be exactly the hallucination the
                   brief forbids)
    market_line    the observed market number, with its source id attached
    difference     market_line - fair_line, computed only when BOTH are present

Difference convention (fixed here, before any result exists):
    side / total : difference in LINE POINTS  (market_line - fair_line)
    moneyline    : difference in IMPLIED PROBABILITY POINTS
                   (market implied prob - model implied prob), because American
                   moneyline numbers are not on a linear scale.

For moneyline rows the fair/market columns hold American prices and the
difference column holds the probability-point gap, which is the only linear
scale available for that market.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from . import pricing

# The mandated origination order. Nothing else may be originated.
ORIGINATION_ORDER: tuple[str, ...] = ("side", "total", "moneyline")

_ALIASES = {
    "side": "side", "spread": "side", "ats": "side",
    "total": "total", "totals": "total", "over/under": "total",
    "moneyline": "moneyline", "ml": "moneyline", "money_line": "moneyline",
}


def canonical_market(name: str) -> str:
    """Map a market label to one of the three originated markets.

    Raises ValueError for anything else (player props and exotics are not
    originated here and must never slip through a lenient normalisation).
    """
    key = str(name).strip().lower()
    if key not in _ALIASES:
        raise ValueError(f"not an originated market: {name!r}")
    return _ALIASES[key]


def origination_queue(markets: Iterable[str]) -> list[str]:
    """Return market names sorted into the mandated origination order.

    Unknown markets raise instead of being appended, so the queue cannot be
    widened by accident. Duplicates collapse to one entry: a market is
    originated once per slate, not once per row.
    """
    seen: dict[str, None] = {}
    for m in markets:
        seen[canonical_market(m)] = None
    return [m for m in ORIGINATION_ORDER if m in seen]


def market_rank(market: str) -> int:
    return ORIGINATION_ORDER.index(canonical_market(market))


def difference_points(fair_line: float | None, market_line: float | None,
                      market: str) -> float | None:
    """market_line - fair_line in line points (side/total), or None if either is
    missing. Never imputes: a missing side stays missing."""
    if fair_line is None or market_line is None:
        return None
    canonical_market(market)  # validate
    return round(float(market_line) - float(fair_line), 4)


def difference_prob(fair_american: float | None, market_american: float | None) -> float | None:
    """Moneyline difference in implied-probability points (market minus fair)."""
    if fair_american is None or market_american is None:
        return None
    return round(pricing.implied_probability(float(market_american))
                 - pricing.implied_probability(float(fair_american)), 5)


def originate(rows: Sequence[dict]) -> list[dict]:
    """Order board rows into the origination queue and fill the difference column.

    Each input row is a dict with at least:
        game_id    str
        market     str  (side | total | moneyline | aliases)
        selection  str  (the taken side of the market: home/away/over/under)
        fair_line  float|None   model number (American price for moneyline)
        market_line float|None  market number (American price for moneyline)
        source_id  str          source record for market_line (may be "" when blank)

    Output rows are copies with:
        market        canonicalised
        origination   1-based position in the mandated order for this slate
        fair_line, market_line   passed through unchanged (never filled in)
        difference    computed only when both inputs exist
    """
    out: list[dict] = []
    for r in rows:
        market = canonical_market(r.get("market", ""))
        row = dict(r)
        row["market"] = market
        fair = r.get("fair_line")
        mkt = r.get("market_line")
        if market == "moneyline":
            row["difference"] = difference_prob(fair, mkt)
            row["difference_unit"] = "implied-probability points"
        else:
            row["difference"] = difference_points(fair, mkt, market)
            row["difference_unit"] = "line points"
        out.append(row)
    # stable order: by origination rank, then game, then selection
    order = {m: i for i, m in enumerate(ORIGINATION_ORDER)}
    out.sort(key=lambda r: (order[r["market"]], str(r.get("game_id", "")),
                            str(r.get("selection", ""))))
    for r in out:
        r["origination"] = order[r["market"]] + 1
    return out
