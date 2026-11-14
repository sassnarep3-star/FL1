"""Demotion gate (requirement R28): sends a LIVE strategy back to PAPER.

The gate set decides who gets promoted; this module decides who gets sent back.
A strategy that passed the gates once can decay — the market can catch up, the
edge can be a regime that ended, the author can drift. Without a demotion rule
a bad live run keeps its badge until the next scheduled re-validation, and that
is exactly how a leaderboard turns into a graveyard of former winners.

Thresholds below are PROPOSED COMPETITION RULES (a design decision, reviewable
in data/flags.json / the Suggestions page), not facts about football. They are
constructor arguments so a reviewer can change them without touching logic.
What a reviewer may not do is reinterpret DEMOTE as HOLD.

Trigger rules — any ONE of these demotes:

    D1  SIGNAL DECAY   over the trailing window of settled bets, the flat-stake
                       hit rate is below break-even at the prices paid and the
                       one-sided test of inferiority gives p < 0.10.
    D2  DRAWDOWN       the flat-stake equity curve's maximum drawdown exceeds
                       `max_drawdown_units` at any point in the log.
    D3  CLV ROT        (only when CLV values exist) the trailing window's mean
                       CLV is below zero and its bootstrap 95% upper bound is
                       also below zero.

Re-promotion (PAPER -> LIVE) needs a FRESH sealed sample of `repromote_bets`
settled bets that passes G-1..G-3 again. Old bets never re-qualify an entry:
the point of the gate is that the burden of proof resets.

States: LIVE -> DEMOTE (transient verdict) -> PAPER (holding state) -> LIVE.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from . import pricing, stats

STATE_LIVE = "LIVE"
STATE_PAPER = "PAPER"
VERDICT_DEMOTE = "DEMOTE"
VERDICT_HOLD = "HOLD"
VERDICT_PROMOTE = "PROMOTE"


@dataclass
class DemotionConfig:
    window: int = 100                # trailing settled bets evaluated
    min_window: int = 50             # below this, no decay verdict is issued
    inferiority_alpha: float = 0.10  # one-sided p for "worse than break-even"
    max_drawdown_units: float = 25.0 # flat-stake units
    clv_window: int = 100
    repromote_bets: int = 300        # fresh settled bets required to return


def _settled(bets: Sequence[dict]) -> list:
    return [b for b in bets if b.get("won") is not None and not b.get("abstained")]


def _modal_price(bets: Sequence[dict]) -> float:
    counts = {}
    for b in bets:
        p = b.get("price")
        if p is not None:
            counts[p] = counts.get(p, 0) + 1
    return float(max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]) if counts else -110.0


def _flat_return(b: dict) -> float:
    won = b["won"]
    price = b.get("price")
    if won is None or price is None:
        return 0.0
    return pricing.net_odds(int(price)) if won else -1.0


def demotion_status(bets: Sequence[dict], cfg: DemotionConfig | None = None) -> dict:
    """Evaluate a LIVE strategy's bet log. Returns verdict + per-rule detail."""
    cfg = cfg or DemotionConfig()
    s = _settled(bets)
    out = {
        "verdict": VERDICT_HOLD,
        "state": STATE_LIVE,
        "reasons": [],
        "rules": {},
        "window_size": 0,
    }
    if len(s) < cfg.min_window:
        out["rules"]["D1"] = {"status": "BLOCKED",
                              "detail": "only %d settled bets; %d required for a "
                                        "decay verdict" % (len(s), cfg.min_window)}
        return out

    tail = s[-cfg.window:]
    out["window_size"] = len(tail)

    # --- D1 signal decay -----------------------------------------------------
    wins = sum(1 for b in tail if b["won"])
    hurdle = pricing.break_even_probability(_modal_price(tail))
    p_hat = wins / len(tail)
    z = stats.z_stat(p_hat, hurdle, len(tail))
    p_inferior = 1.0 - stats.one_sided_p_above(z)   # P(data | true rate = hurdle)
    d1 = p_hat < hurdle and p_inferior < cfg.inferiority_alpha
    out["rules"]["D1"] = {
        "status": "DEMOTE" if d1 else "HOLD",
        "hit_rate": round(p_hat, 4),
        "breakeven": round(hurdle, 4),
        "p_inferiority": round(p_inferior, 4),
        "detail": "flat-stake hit rate %s break-even %s with p=%s"
                  % ("<" if p_hat < hurdle else ">=", round(hurdle, 4),
                     round(p_inferior, 4)),
    }
    if d1:
        out["reasons"].append("D1 signal decay: hit rate below break-even beyond noise "
                              "(p=%.4f < %.2f)" % (p_inferior, cfg.inferiority_alpha))

    # --- D2 drawdown ---------------------------------------------------------
    equity = peak = max_dd = 0.0
    for b in s:
        equity += _flat_return(b)
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    d2 = max_dd > cfg.max_drawdown_units
    out["rules"]["D2"] = {
        "status": "DEMOTE" if d2 else "HOLD",
        "max_drawdown_units": round(max_dd, 3),
        "limit_units": cfg.max_drawdown_units,
        "detail": "flat-stake drawdown %.3f vs limit %.3f" % (max_dd, cfg.max_drawdown_units),
    }
    if d2:
        out["reasons"].append("D2 drawdown: %.3f units > %.3f limit"
                              % (max_dd, cfg.max_drawdown_units))

    # --- D3 CLV rot ----------------------------------------------------------
    clvs = [b["clv"] for b in tail if b.get("clv") is not None]
    if len(clvs) >= 10:
        mean_clv = sum(clvs) / len(clvs)
        _, _, hi = stats.bootstrap_ci(clvs, n_boot=1000)
        d3 = mean_clv < 0 and hi < 0
        out["rules"]["D3"] = {
            "status": "DEMOTE" if d3 else "HOLD",
            "mean_clv": round(mean_clv, 4),
            "clv_ci_high": round(hi, 4) if hi is not None else None,
            "detail": "mean CLV %.4f, bootstrap upper bound %s"
                      % (mean_clv, round(hi, 4) if hi is not None else "None"),
        }
        if d3:
            out["reasons"].append("D3 CLV rot: mean CLV and its upper bound both below zero")
    else:
        out["rules"]["D3"] = {"status": "BLOCKED",
                              "detail": "no closing-line values in the window (GAP-01)"}

    if out["reasons"]:
        out["verdict"] = VERDICT_DEMOTE
        out["state"] = STATE_PAPER
    return out


def repromotion_status(bets: Sequence[dict], cfg: DemotionConfig | None = None) -> dict:
    """PAPER -> LIVE: requires a fresh sealed sample of settled bets whose
    flat-stake hit rate beats break-even with one-sided p < 0.05 (the G-2b
    standard) and at least `repromote_bets` settled bets (the G-1 standard)."""
    cfg = cfg or DemotionConfig()
    s = _settled(bets)
    out = {"verdict": VERDICT_HOLD, "state": STATE_PAPER, "reasons": [], "n": len(s)}
    if len(s) < cfg.repromote_bets:
        out["reasons"].append("fresh sample %d < %d settled bets"
                              % (len(s), cfg.repromote_bets))
        return out
    wins = sum(1 for b in s if b["won"])
    hurdle = pricing.break_even_probability(_modal_price(s))
    p_hat = wins / len(s)
    z = stats.z_stat(p_hat, hurdle, len(s))
    p = stats.one_sided_p_above(z)
    out["hit_rate"] = round(p_hat, 4)
    out["breakeven"] = round(hurdle, 4)
    out["p_one_sided"] = round(p, 6)
    if p_hat > hurdle and p < 0.05:
        out["verdict"] = VERDICT_PROMOTE
        out["state"] = STATE_LIVE
    else:
        out["reasons"].append("hit rate %s break-even at p=%s"
                              % (round(p_hat, 4), round(p, 4)))
    return out
