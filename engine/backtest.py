"""Verified results feed + backtest arithmetic (requirement R22).

A backtest and an ROI number are only as good as two things: a results feed
whose every row is checked against an official source, and a price snapshot for
the market that was actually played. This module wires those together and
reports, alongside every computed number, which provenance tier produced it.

Tier vocabulary (same as the site):
    OFFICIAL      value transcribed from an official league source
    COMPUTED      value computed here from OFFICIAL inputs only
    THIRD_PARTY   value transcribed from a pinned third-party capture
    BLANK         no source exists; the field is left empty and flagged

Requirement R25 is implemented here too: `split_signal_staking` computes the
SIGNAL block (flat stake only, so staking cannot flatter it) and the STAKING
block (the declared stake plan) separately, and the caller ranks on signal only.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

from . import pricing, stats

TIER_OFFICIAL = "OFFICIAL"
TIER_COMPUTED = "COMPUTED"
TIER_THIRD_PARTY = "THIRD_PARTY"
TIER_BLANK = "BLANK"


def _modal_price(prices: Sequence[int]) -> float:
    """Modal (most common) price; the break-even benchmark for the log."""
    counts = {}
    for p in prices:
        counts[p] = counts.get(p, 0) + 1
    return float(max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0])


def index_results(rows: Sequence[Mapping]) -> dict:
    """Index the results feed by (week, away, home) and by game_id when present.
    Feed rows are dicts with week/date/away/awayPts/home/homePts (+ provenance)."""
    by_key = {}
    by_id = {}
    for r in rows:
        key = (int(r["week"]), r["away"], r["home"])
        by_key[key] = r
        if r.get("game_id"):
            by_id[str(r["game_id"])] = r
    return {"by_key": by_key, "by_id": by_id}


def settle_bet(bet: Mapping, feed: Mapping) -> dict:
    """Settle one bet against the results feed. Returns a NEW dict; never edits
    the input, never guesses a result.

    A bet carries: game (week, away, home) or game_id, market_type
    (SIDE|TOTAL|MONEYLINE), side, line (optional), price (American), stake.
    `won` is decided only from the official score; if the feed has no row the
    bet stays unsettled with a reason, it is not dropped silently.
    """
    out = dict(bet)
    row = None
    if bet.get("game_id"):
        row = feed["by_id"].get(str(bet["game_id"]))
    if row is None and bet.get("week") is not None:
        row = feed["by_key"].get((int(bet["week"]), bet["away"], bet["home"]))
    if row is None:
        out["won"] = None
        out["settle_note"] = "no verified result row for this game"
        return out

    ap, hp = int(row["awayPts"]), int(row["homePts"])
    mt = bet.get("market_type")
    line = bet.get("line")
    if mt == "MONEYLINE":
        if bet["side"] == bet["home"]:
            out["won"] = hp > ap
        elif bet["side"] == bet["away"]:
            out["won"] = ap > hp
        else:
            out["won"] = None
            out["settle_note"] = "side %r is neither club in this game" % bet["side"]
            return out
    elif mt == "TOTAL":
        total = ap + hp
        if line is None:
            out["won"] = None
            out["settle_note"] = "total bet without a line cannot be settled"
            return out
        if total == float(line):
            out["won"] = None
            out["settle_note"] = "push on the total"
        else:
            out["won"] = (total > float(line)) if bet["side"] == "OVER" else (total < float(line))
    elif mt == "SIDE":
        if line is None:
            out["won"] = None
            out["settle_note"] = "side bet without a line cannot be settled"
            return out
        # Convention: `line` is the spread attached to bet["side"] itself
        # (e.g. -3 means the side is the 3-point favourite). A bet wins when
        # side's margin + its own line > 0, pushes at exactly 0.
        if bet["side"] == bet["home"]:
            margin = float(hp - ap) + float(line)
        elif bet["side"] == bet["away"]:
            margin = float(ap - hp) + float(line)
        else:
            out["won"] = None
            out["settle_note"] = "side %r is neither club in this game" % bet["side"]
            return out
        if abs(margin) < 1e-9:
            out["won"] = None
            out["settle_note"] = "push against the spread"
        else:
            out["won"] = margin > 0
    else:
        out["won"] = None
        out["settle_note"] = "unknown market_type %r" % mt
        return out

    price = bet.get("price")
    stake = float(bet.get("stake") or 1.0)
    if out["won"] is None:
        out["pnl"] = 0.0
    elif price is None:
        out["pnl"] = None
        out["settle_note"] = "settled win/loss but no price recorded; pnl left blank"
    else:
        out["pnl"] = round(stake * pricing.net_odds(int(price)) if out["won"] else -stake, 6)
    return out


def settle_all(bets: Iterable[Mapping], feed_rows: Sequence[Mapping]) -> list:
    feed = index_results(feed_rows)
    return [settle_bet(b, feed) for b in bets]


def flat_stake_returns(settled: Sequence[Mapping]) -> list:
    """Per-bet return at a flat one-unit stake. This is the SIGNAL series:
    it contains no staking choice, so no staking choice can flatter it."""
    out = []
    for b in settled:
        if b.get("won") is None or b.get("price") is None:
            continue
        out.append(pricing.net_odds(int(b["price"])) if b["won"] else -1.0)
    return out


def split_signal_staking(settled: Sequence[Mapping]) -> dict:
    """Requirement R25: report signal and staking as separate blocks.

    SIGNAL  — flat one-unit stake on every settled bet: hit rate, break-even at
              the prices paid, Wilson interval, one-sided z/p vs break-even,
              flat ROI. Nothing here depends on how much was staked.
    STAKING — the declared stake plan: ROI at actual stakes, profit units,
              max drawdown in units, largest single-bet share of profit.
    The rank must be computed from the SIGNAL block only; this function returns
    both so a caller cannot accidentally mix them.
    """
    settled = [b for b in settled if b.get("won") is not None]
    n = len(settled)
    wins = sum(1 for b in settled if b["won"])
    prices = [int(b["price"]) for b in settled if b.get("price") is not None]
    hurdle = pricing.break_even_probability(_modal_price(prices)) if prices else None

    signal = {
        "settled": n,
        "won": wins,
        "hit_rate": round(wins / n, 6) if n else None,
        "breakeven_hit": round(hurdle, 6) if hurdle is not None else None,
        "hit_ci_low": None, "hit_ci_high": None,
        "z_vs_breakeven": None, "p_one_sided": None,
        "flat_roi": None, "tier": TIER_COMPUTED,
    }
    if n:
        lo, hi = stats.wilson_interval(wins, n)
        signal["hit_ci_low"] = round(lo, 6)
        signal["hit_ci_high"] = round(hi, 6)
    if n and hurdle is not None:
        z = stats.z_stat(wins / n, hurdle, n)
        signal["z_vs_breakeven"] = round(z, 4)
        signal["p_one_sided"] = round(stats.one_sided_p_above(z), 6)
    flat = flat_stake_returns(settled)
    if flat:
        signal["flat_roi"] = round(sum(flat) / len(flat), 6)

    staked = [b for b in settled if b.get("stake") and b.get("pnl") is not None]
    staking = {
        "staked_bets": len(staked),
        "staked_units": round(sum(float(b["stake"]) for b in staked), 4),
        "profit_units": round(sum(float(b["pnl"]) for b in staked), 4),
        "roi_at_stakes": None, "max_drawdown_units": None,
        "largest_bet_share_of_profit": None, "tier": TIER_COMPUTED,
    }
    if staked:
        total_stake = sum(float(b["stake"]) for b in staked)
        staking["roi_at_stakes"] = round(
            sum(float(b["pnl"]) for b in staked) / total_stake, 6) if total_stake else None
        equity, peak, max_dd = 0.0, 0.0, 0.0
        biggest = 0.0
        for b in staked:
            equity += float(b["pnl"])
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
            biggest = max(biggest, abs(float(b["pnl"])))
        staking["max_drawdown_units"] = round(max_dd, 4)
        prof = staking["profit_units"]
        staking["largest_bet_share_of_profit"] = (
            round(biggest / abs(prof), 4) if prof else None)

    return {"signal": signal, "staking": staking}


def provenance_report(price_tier: str, results_tier: str = TIER_OFFICIAL) -> dict:
    """The honesty wrapper: what a computed backtest number is allowed to be
    called, given the tiers of its inputs. Official results + third-party prices
    = a THIRD_PARTY-backed statistic, publishable only with its flag."""
    order = {TIER_OFFICIAL: 0, TIER_COMPUTED: 1, TIER_THIRD_PARTY: 2, TIER_BLANK: 3}
    worst = max((price_tier, results_tier), key=lambda t: order.get(t, 3))
    return {
        "results_tier": results_tier,
        "price_tier": price_tier,
        "statistic_tier": worst,
        "publishable_on_official_layer": worst in (TIER_OFFICIAL, TIER_COMPUTED),
        "flag": None if worst in (TIER_OFFICIAL, TIER_COMPUTED) else
                "computed from %s prices — not an official league fact" % price_tier.lower(),
    }
