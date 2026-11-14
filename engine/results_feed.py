"""Verified results feed: settlement of every originated market from verified
final scores, so backtests and ROI are computable at all.

Provenance contract (this is the whole point of the module):

    SCORES  come only from results that were reconciled against the official
            league standings (data/results.tsv, verified 32/32 clubs). A row
            whose score cannot be verified is not in the feed.
    PRICES  (spread / total / moneyline numbers and odds) come from the
            committed third-party snapshot (data/raw/games.csv, source record
            S47/S50). They are labelled third-party everywhere they surface.
            Where no price exists the market row is omitted for that game and
            counted in `missing_prices`, never imputed.

Settlement arithmetic is deterministic and push-aware:

    side      home covers if (home_score - away_score) + spread_home > 0;
              push at exactly 0. `spread_home` is the home team's spread
              (negative when the home team is favoured) — the same sign
              convention pinned by verification V8.
    total     over if away_score + home_score > total_line; push at exactly equal.
    moneyline home wins outright (overtime included); an outright tie is a push.

ROI at a given American price, per unit staked:
    win  -> +100/|price|   when price > 0 (underdog)
    win  -> +|price|/100   when price < 0 (favourite)  [i.e. 100/|price|]
    loss -> -1
    push -> 0
"""

from __future__ import annotations

from typing import Iterable, Sequence

from . import pricing

MARKET_ORDER = ("side", "total", "moneyline")  # must match engine.origination


def settle_side(away_score: int, home_score: int, spread_home: float) -> str:
    """'home' (home covers), 'away', or 'push'. Raises on missing inputs."""
    margin = (home_score - away_score) + float(spread_home)
    if margin > 0:
        return "home"
    if margin < 0:
        return "away"
    return "push"


def settle_total(away_score: int, home_score: int, total_line: float) -> str:
    """'over', 'under', or 'push'."""
    total = away_score + home_score
    line = float(total_line)
    if total > line:
        return "over"
    if total < line:
        return "under"
    return "push"


def settle_moneyline(away_score: int, home_score: int) -> str:
    """'home', 'away', or 'push' (regular-season ties settle as pushes)."""
    if home_score > away_score:
        return "home"
    if home_score < away_score:
        return "away"
    return "push"


def settle_result(result: str, american_price: float | None) -> str | None:
    """Map a selection's settlement ('win'/'loss'/'push') to a PnL in units.

    `result` is the outcome FOR THE SELECTION the row prices. Returns None
    (not zero) when the price is missing: an ROI that silently treats a
    missing price as even money is a fabricated number.
    """
    if american_price is None:
        return None
    if result == "push":
        return 0.0
    dec = pricing.american_to_decimal(float(american_price))
    if result == "win":
        return round(dec - 1.0, 6)
    if result == "loss":
        return -1.0
    raise ValueError(f"unknown settlement: {result!r}")


def outcome_for(selection: str, settlement: str) -> str | None:
    """Translate a market settlement into win/loss/push for a selection."""
    if settlement == "push":
        return "push"
    if selection == settlement:
        return "win"
    return "loss"


def feed_rows(games: Sequence[dict]) -> tuple[list[dict], dict]:
    """Build the long-format results feed from score+price rows.

    Each input dict needs:
        game_id, gameday, week, away, home, away_score, home_score   (verified)
        spread_home, total_line, ml_home, ml_away                    (price, may be None)
        result_source_url, line_source_url, line_source_id

    Output rows carry settle outcome and per-unit PnL where a price exists,
    ordered game by game, markets within a game in the origination order
    (side, total, moneyline). The summary counts what is missing so nothing
    disappears quietly.
    """
    rows: list[dict] = []
    summary = {"games": 0, "market_rows": 0, "pushes": 0,
               "missing_prices": {"side": 0, "total": 0, "moneyline": 0},
               "settled_wins": 0, "settled_losses": 0}
    for g in games:
        summary["games"] += 1
        a, h = int(g["away_score"]), int(g["home_score"])
        common = {
            "game_id": g["game_id"], "gameday": g["gameday"], "week": g["week"],
            "away": g["away"], "home": g["home"],
            "away_score": a, "home_score": h,
            "result_source_url": g.get("result_source_url", ""),
            "line_source_url": g.get("line_source_url", ""),
            "line_source_id": g.get("line_source_id", ""),
        }

        def emit(market: str, selection: str, line, odds, settlement: str) -> None:
            if settlement == "push":
                summary["pushes"] += 1
            out = outcome_for(selection, settlement)
            if out == "win":
                summary["settled_wins"] += 1
            elif out == "loss":
                summary["settled_losses"] += 1
            pnl = settle_result(out or "push", odds)
            if line is None or odds is None:
                summary["missing_prices"][market] += 1
            rows.append({**common, "market": market, "selection": selection,
                         "line": "" if line is None else line,
                         "odds_american": "" if odds is None else odds,
                         "outcome": out or "", "pnl_unit": "" if pnl is None else pnl})
            summary["market_rows"] += 1

        spread = g.get("spread_home")
        if spread is not None and a is not None and h is not None:
            s = settle_side(a, h, spread)
            emit("side", "home", spread, g.get("home_spread_odds"), s)
        else:
            summary["missing_prices"]["side"] += 2  # the game row itself is absent
        tot = g.get("total_line")
        if tot is not None:
            s = settle_total(a, h, tot)
            emit("total", "over", tot, g.get("over_odds"), s)
        else:
            summary["missing_prices"]["total"] += 2
        mlh, mla = g.get("ml_home"), g.get("ml_away")
        if mlh is not None or mla is not None:
            s = settle_moneyline(a, h)
            emit("moneyline", "home", mlh, mlh, s)
            emit("moneyline", "away", mla, mla, s)
        else:
            summary["missing_prices"]["moneyline"] += 2
    return rows, summary


def roi(rows: Iterable[dict]) -> dict:
    """Per-unit ROI over priced rows. Pushes count in n with zero return.

    Rows with a blank pnl_unit (no price) are excluded from n and reported,
    because a backtest that averages over missing prices is measuring the
    missingness.
    """
    n = wins = losses = pushes = unpriced = 0
    total = 0.0
    for r in rows:
        if r.get("pnl_unit") == "" or r.get("pnl_unit") is None:
            unpriced += 1
            continue
        n += 1
        p = float(r["pnl_unit"])
        total += p
        if p > 0:
            wins += 1
        elif p < 0:
            losses += 1
        else:
            pushes += 1
    return {"n_priced": n, "wins": wins, "losses": losses, "pushes": pushes,
            "n_unpriced": unpriced,
            "roi_per_unit": round(total / n, 6) if n else None,
            "pnl_units": round(total, 6)}
