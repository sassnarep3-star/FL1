"""Signal and staking, computed apart, published apart, ranked on signal only.

WHY THE LEADERBOARD IS SPLIT IN TWO
    A single "ROI" column rewards two unrelated achievements: knowing something, and
    sizing it well. A strategy with no information can beat a strategy with real
    information by betting more often at the same edge, and - worse for a competition -
    a strategy with an inverted signal can finish first after a two-month run of
    coin-flips on half-point wagers. The brief's requirement is that this must not be
    able to happen, so:

      * the **signal** block never sees a stake. It measures points beat the line, hit
        rate against the break-even implied by the log's own prices, calibration of the
        edge against realised outcomes, and Brier score against the market's no-vig
        probabilities. Its ranking statistic is the 95% lower bound of mean points beat.
      * the **staking** block measures what a bankroll experienced: units at risk, ROI,
        drawdown, realised-vs-fractional-Kelly. It is published, never ranked on.
      * a **divergence** column names, in words, any entry whose staking rank is well
        above its signal rank. That entry is not a good strategy that made money; it is
        a small sample or a lucky run, and the competition treats it as such.

Nothing here converts a good staking block into a promotion: `engine.demotion_eval`
reads the signal block, and so do the rewards.
"""

from __future__ import annotations

import math
from collections import OrderedDict, defaultdict
from typing import Sequence

from . import pricing
from . import stats as st
from . import results_ledger as rl

SIGNAL_FIELDS = [
    "strategy_id", "market", "signal_bets", "signal_pushes", "signal_n_eligible",
    "selectivity_pct", "hit_rate", "hit_ci_low", "hit_ci_high", "breakeven_hit",
    "mean_abs_edge", "mean_edge_signed", "points_beat_mean", "points_beat_lb",
    "points_beat_ci", "calibration_slope", "calibration_ci", "brier_vs_market_pp",
    "z_vs_breakeven", "p_one_sided", "detectable_edge_pp", "signal_grade",
]

STAKING_FIELDS = [
    "strategy_id", "stake_units", "profit_units", "roi", "roi_ci_low", "roi_ci_high",
    "max_drawdown_units", "bets_at_posted_price", "price_basis_pct_posted",
    "mean_stake", "kelly_suggested_mean", "over_bet_flag", "roi_is_upper_bound",
    "staking_note",
]

LEADERBOARD_FIELDS = [
    "rank_signal", "strategy_id", "market", "signal_bets", "points_beat_mean",
    "points_beat_lb", "hit_rate", "breakeven_hit", "calibration_slope", "selectivity_pct",
    "p_one_sided", "signal_grade", "rank_staking", "profit_units", "roi",
    "max_drawdown_units", "divergence", "reward_units", "status",
]


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _ols_slope(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = _mean(xs), _mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den


# ---------------------------------------------------------------------------
# the two scorecards
# ---------------------------------------------------------------------------
def signal_card(trades: Sequence[dict], n_eligible: int | None = None,
                strategy_id: str | None = None, market: str | None = None) -> dict:
    """Stake-free quality of the picks in this log."""
    settled = [t for t in trades if t["outcome"] in (rl.WIN, rl.LOSE)]
    pushes = sum(1 for t in trades if t["outcome"] == rl.PUSH)
    n = len(settled)
    out = OrderedDict((k, "") for k in SIGNAL_FIELDS)
    sid = strategy_id or (trades[0]["strategy_id"] if trades else "UNKNOWN")
    mkt = market or (trades[0]["market"] if trades else "UNKNOWN")
    out["strategy_id"], out["market"] = sid, mkt
    out["signal_bets"], out["signal_pushes"] = n, pushes
    if n_eligible:
        out["signal_n_eligible"] = n_eligible
        out["selectivity_pct"] = round(100.0 * n / n_eligible, 3)
    if not n:
        out["signal_grade"] = "NO SETTLED BETS - the rule never triggered on a verified game"
        return out
    wins = sum(1 for t in settled if t["outcome"] == rl.WIN)
    hit = wins / n
    lo, hi = st.wilson_interval(wins, n)
    out["hit_rate"] = round(hit, 5)
    out["hit_ci_low"], out["hit_ci_high"] = round(lo, 5), round(hi, 5)
    modal_price = _modal(settled)
    be = pricing.break_even_probability(modal_price)
    out["breakeven_hit"] = round(be, 5)
    edges = [abs(float(t["delta"])) for t in settled]
    out["mean_abs_edge"] = round(_mean(edges), 5)
    out["mean_edge_signed"] = round(_mean([float(t["delta"]) for t in settled]), 5)
    # points beat the line: the stake-free outcome measure (for ML bets, the margin itself
    # is not meaningful, so the block falls back to the probability-implied measure below)
    if mkt in ("SIDE", "TOTAL"):
        pts = [_points_beat(t) for t in settled]
        out["points_beat_mean"] = round(_mean(pts), 5)
        if len(pts) >= 30:
            pt, plo, phi = st.bootstrap_ci(pts)
            out["points_beat_lb"] = round(plo, 5)
            out["points_beat_ci"] = "%.5f to %.5f" % (plo, phi)
        slope = _ols_slope([float(t["delta"]) for t in settled], pts)
        out["calibration_slope"] = "" if slope != slope else round(slope, 4)
        if len(pts) >= 100:
            sl = _boot_slope([float(t["delta"]) for t in settled], pts)
            out["calibration_ci"] = "%.3f to %.3f" % sl if sl else ""
    else:
        # moneyline: Brier against the market's own no-vig probability is the fair
        # stake-free comparison, and "points beat" is reported in probability points
        prob = [_prob_beat(t) for t in settled]
        out["points_beat_mean"] = round(_mean(prob), 6)
        if len(prob) >= 30:
            _, plo, phi = st.bootstrap_ci(prob)
            out["points_beat_lb"] = round(plo, 6)
            out["points_beat_ci"] = "%.6f to %.6f" % (plo, phi)
        out["brier_vs_market_pp"] = _brier_gap(settled)
        out["calibration_slope"] = "n/a for a two-way price market"
    z = st.z_stat(hit, be, n)
    out["z_vs_breakeven"] = round(z, 4)
    out["p_one_sided"] = "%.5g" % st.one_sided_p_above(z)
    out["detectable_edge_pp"] = round(100.0 * st.detectable_edge(n, be), 3)
    out["signal_grade"] = _grade(out)
    return out


def staking_card(trades: Sequence[dict], strategy_id: str | None = None) -> dict:
    """What the bankroll experienced. Published, never ranked on."""
    out = OrderedDict((k, "") for k in STAKING_FIELDS)
    sid = strategy_id or (trades[0]["strategy_id"] if trades else "UNKNOWN")
    out["strategy_id"] = sid
    if not trades:
        out["staking_note"] = "no trades - nothing to size, nothing to grade"
        return out
    settled = [t for t in trades if t["outcome"] in (rl.WIN, rl.LOSE, rl.PUSH)]
    stakes = [float(t["stake_units"]) for t in settled]
    pnls = [float(t["pnl_units"]) for t in settled]
    staked = sum(stakes)
    profit = sum(pnls)
    out["stake_units"] = round(staked, 4)
    out["profit_units"] = round(profit, 4)
    roi = profit / staked if staked else 0.0
    out["roi"] = round(roi, 5)
    if len(pnls) >= 30:
        _, lo, hi = st.bootstrap_ci([p / s if s else 0.0 for p, s in zip(pnls, stakes)])
        out["roi_ci_low"], out["roi_ci_high"] = round(lo, 5), round(hi, 5)
    out["max_drawdown_units"] = round(_drawdown(pnls), 4)
    posted = sum(1 for t in settled if t["price_basis"] == "POSTED_IN_STORE")
    out["bets_at_posted_price"] = posted
    out["price_basis_pct_posted"] = round(100.0 * posted / len(settled), 2)
    out["mean_stake"] = round(staked / len(settled), 4)
    kelly = []
    for t in settled:
        p = float(t.get("fair_p_home") or 0.0)
        if t["market"] == "MONEYLINE" and t["side_key"] == "away":
            p = 1.0 - p
        if p:
            kelly.append(pricing.kelly_fraction(p, float(t["price_american"])))
    out["kelly_suggested_mean"] = round(_mean(kelly), 5) if kelly else ""
    out["over_bet_flag"] = ("n/a (flat one-unit log)" if not kelly else
                            ("OVER-BET vs full Kelly" if _mean(kelly) < 0 and roi < 0 else
                             "within bounds"))
    out["roi_is_upper_bound"] = "YES"
    out["staking_note"] = ("priced at the store's recorded market number; no feed here is "
                           "time-stamped to the moment the pick was made, so ROI is an "
                           "upper bound on a real book")
    return out


def _points_beat(t: dict) -> float:
    """Signed points by which the pick beat the line. Stake-free and unit-free.

    Side-aware, on the number the bet was actually struck at (`settle_line`), so a push is
    a push here and in `engine.results_ledger` at the same time. Duplicated deliberately in
    `engine.demotion_eval`: the two must agree, and the agreement is asserted by a test
    against book-style truths rather than assumed.
    """
    margin = float(t["margin_home"])
    total = float(t["total_points"])
    line = t.get("settle_line")
    if line is None or line == "":
        line = t.get("market_line")
    if line is None or line == "":
        return float("nan")
    line = float(line)
    if t["market"] == "SIDE":
        own = margin if t["side_key"] == "home" else -margin
        return own + line
    if t["market"] == "TOTAL":
        diff = total - line
        return diff if t["side_key"] == "over" else -diff
    return margin


def _prob_beat(t: dict) -> float:
    """Probability points beat the no-vig market: our estimate minus the outcome, less the
    market's estimate minus the outcome. Positive = we were closer than the market."""
    outcome = 1.0 if t["outcome"] == rl.WIN else 0.0
    side = t["side_key"]
    fair = t.get("fair_line")
    mkt = t.get("market_line")
    if side == "away" and fair is not None and mkt is not None:
        fair, mkt = 1.0 - float(fair), 1.0 - float(mkt)
    if fair is None or mkt is None:
        return float("nan")
    return ((float(mkt) - outcome) ** 2 - (float(fair) - outcome) ** 2)


def _brier_gap(settled: Sequence[dict]) -> str:
    vals = [_prob_beat(t) for t in settled]
    vals = [v for v in vals if v == v]
    if not vals:
        return ""
    return "%+.3f" % (1000.0 * _mean(vals))  # milli-Brier, market-relative


def _modal(trades: Sequence[dict]) -> int:
    counts: dict[int, int] = defaultdict(int)
    for t in trades:
        counts[int(t["price_american"])] += 1
    return max(sorted(counts), key=lambda k: counts[k])


def _drawdown(pnls: Sequence[float]) -> float:
    cum = peak = 0.0
    worst = 0.0
    for p in pnls:
        cum += p
        peak = max(peak, cum)
        worst = min(worst, cum - peak)
    return worst


def _boot_slope(xs: Sequence[float], ys: Sequence[float], n_boot: int = 600,
                seed: int = 20261114) -> tuple[float, float] | None:
    import random
    n = len(xs)
    if n < 100:
        return None
    rng = random.Random(seed)
    slopes = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        sx = [xs[i] for i in idx]
        sy = [ys[i] for i in idx]
        s = _ols_slope(sx, sy)
        if s == s:
            slopes.append(s)
    if len(slopes) < 50:
        return None
    slopes.sort()
    return slopes[int(0.025 * len(slopes))], slopes[int(0.975 * len(slopes))]


def _grade(row: dict) -> str:
    """Coarse, rule-based, and recomputable - not a verdict of skill.

    The order is the point. Inversion is a measured fact about the mean points beat, so it is
    read off that mean and nothing else; the calibration slope is a separate observation about
    whether a bigger claimed edge buys a bigger beat. Reporting a negative slope as an
    "inverted signal" would let a column about *scaling* decide a verdict about *direction*,
    which is exactly the sort of overstatement this site is built to avoid.
    """
    lb = row.get("points_beat_lb")
    n = row.get("signal_bets") or 0
    slope = row.get("calibration_slope")
    mean = row.get("points_beat_mean")
    if not isinstance(lb, float):
        return "INSUFFICIENT SAMPLE (<30 settled bets)"
    if isinstance(mean, float) and mean < 0:
        return "INVERTED - the side this rule picks loses points against the line on average"
    if lb > 0:
        return "SIGNAL CLEARS ZERO at 95%% (n=%d)" % n
    if isinstance(mean, float) and mean > 0:
        return "POSITIVE MEAN, NOT PROVABLE at n=%d" % n
    if isinstance(slope, float) and slope <= 0:
        return "FLAT CALIBRATION - a bigger claimed edge does not buy a bigger beat"
    return "NEGATIVE OR ZERO"


# ---------------------------------------------------------------------------
# ranking
# ---------------------------------------------------------------------------
def rank(cards_signal: Sequence[dict], cards_staking: Sequence[dict]) -> list[dict]:
    """Rank on the signal lower bound. Attach the staking rank; never mix the two."""
    by_id = {c["strategy_id"]: c for c in cards_signal}
    stak = {c["strategy_id"]: c for c in cards_staking}

    def key(item):
        lb = item[1].get("points_beat_lb")
        return (-(lb if isinstance(lb, float) else -1e9), item[0])

    order = sorted(by_id.items(), key=key)
    roi_order = sorted(stak.items(),
                       key=lambda kv: -(kv[1].get("roi") if isinstance(kv[1].get("roi"), float)
                                        else -1e9))
    staking_rank = {sid: i + 1 for i, (sid, _c) in enumerate(roi_order)}
    rows = []
    for i, (sid, sig) in enumerate(order):
        stk = stak.get(sid, {})
        sr = staking_rank.get(sid, "")
        lb = sig.get("points_beat_lb")
        roi = stk.get("roi")
        edge = isinstance(lb, float) and lb > 0
        profit = isinstance(roi, float) and roi > 0
        if not edge and profit:
            # the exact failure the split exists to expose: money made on a signal that
            # cannot clear its own break-even
            # this string is not %-formatted, so a doubled percent would reach the artefact
            diverge = ("STAKING OUTPERFORMS SIGNAL - a profitable run on a signal with no "
                       "edge at 95%. No promotion, no reward.")
        elif edge and not profit:
            diverge = "SIGNAL OUTPERFORMS STAKING - sizing is throwing away a real edge"
        elif not edge and not profit:
            diverge = ("NO DIVERGENCE OF SUBSTANCE - both blocks are negative; the rank order "
                       "says who is least wrong, not who has an edge")
        else:
            diverge = "signal and staking agree"
        rows.append(OrderedDict([
            ("rank_signal", i + 1), ("strategy_id", sid), ("market", sig.get("market", "")),
            ("signal_bets", sig.get("signal_bets", "")),
            ("points_beat_mean", sig.get("points_beat_mean", "")),
            ("points_beat_lb", sig.get("points_beat_lb", "")),
            ("hit_rate", sig.get("hit_rate", "")),
            ("breakeven_hit", sig.get("breakeven_hit", "")),
            ("calibration_slope", sig.get("calibration_slope", "")),
            ("selectivity_pct", sig.get("selectivity_pct", "")),
            ("p_one_sided", sig.get("p_one_sided", "")),
            ("signal_grade", sig.get("signal_grade", "")),
            ("rank_staking", sr), ("profit_units", stk.get("profit_units", "")),
            ("roi", stk.get("roi", "")), ("max_drawdown_units", stk.get("max_drawdown_units", "")),
            ("divergence", diverge),
            ("reward_units", _reward(i + 1, sig)),
            ("status", "PAPER - not fundable from a price vintage nobody published"
             if not str(sig.get("signal_grade", "")).startswith("SIGNAL CLEARS")
             else "PAPER - signal clears zero; still not fundable without a tradable price"),
        ]))
    return rows


REWARD_TABLE = {1: 40, 2: 25, 3: 15}


def _reward(rank_no: int, sig: dict) -> int:
    """Rewards follow the signal bound only. Profit cannot buy a reward."""
    lb = sig.get("points_beat_lb")
    if not isinstance(lb, float) or lb <= 0:
        return 0
    return REWARD_TABLE.get(rank_no, 0)


def legacy_leaderboard_rows(path: str) -> list[dict]:
    """What the pre-existing leaderboard can and cannot support after the split.

    Its columns are all staking-side (bets, ROI, drawdown) plus a hit-rate; there is no
    bet log in the repository, so points-beat, calibration and selectivity cannot be
    recomputed from it. Those cells stay blank and the row is marked, per the site rule.
    """
    import csv
    import os
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        out.append(OrderedDict([
            ("strategy_id", r.get("strategy_id", "")),
            ("legacy_bets", r.get("bets", "")),
            ("legacy_hit_rate", r.get("hit_rate", "")),
            ("legacy_roi", r.get("roi", "")),
            ("legacy_verdict", r.get("verdict", "")),
            ("points_beat_mean", ""), ("points_beat_lb", ""), ("calibration_slope", ""),
            ("selectivity_pct", ""), ("mean_abs_edge", ""),
            ("blockable", "SIGNAL BLOCK UNPOPULATED - no sealed bet log in the repository"),
        ]))
    return out
