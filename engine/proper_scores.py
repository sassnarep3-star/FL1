"""
Proper scores, uncertainty and controls - the leaderboard this repository wants.

THE PROBLEM WITH A LEADERBOARD BUILT ON HIT RATE
    A strategy that went 9-1 has a 90% hit rate and has told you nothing: with
    ten bets, a coin flip lands at 90% or better about 1.8% of the time. Worse,
    the 9-1 strategy and the 1-9 strategy are the same strategy seen from two
    ends of the same coin, and a leaderboard that cannot tell them apart is not
    measuring skill, it is measuring luck.

    The brief says it directly: rank by proper scores and uncertainty, not win
    rate, and separate signal from staking so that a lucky staking run cannot
    mask a bad signal.

WHAT THIS MODULE DOES
    For every settled backtest trade it produces three numbers:

        o          the outcome, 1 win / 0 loss / 0.5 push
        p_model    the probability the STRATEGY's line assigns to the win
        p_bench    the MARKET's probability of the same win, from the two
                   posted prices with the vig removed

    and scores them with the Brier score, which is a proper scoring rule: it is
    minimised by the true probability, so it rewards a forecast for being both
    sharp and honest. A hit rate is not a scoring rule.

THE SIGN CONVENTION, SPELLED OUT
    A spread is quoted in the HOME club's perspective: -6.0 means the home club
    is given six points. The betting side's own margin is therefore

        own = margin_home    for a home bet
        own = -margin_home   for an away bet

    and a spread bet wins when own + settle_line > 0, because the settle line is
    the points the side RECEIVES. Both the model's line (`fair_line`) and the
    market's line (`settle_line`) are home-perspective spreads, so both convert
    to the betting side's own forecast with the same transform:

        model_own  = -fair_line    for a home bet, +fair_line for an away bet
        market_own = -settle_line  for a home bet, +settle_line for an away bet

    Getting one of those signs wrong flips the comparison, so both are pinned by
    tests against hand-worked book-style examples rather than assumed.

THE SKILL MEASURE
        BSS = 1 - Brier(model) / Brier(benchmark)

    Zero means the strategy's line is no sharper than the price it bet against;
    positive means it was sharper. A line is not a probability, so the model's
    line is turned into one with ONE shared residual scale - the standard
    deviation of the market line's own error, measured over every settled game.
    The same scale is used for the model and for the market, deliberately: it
    isolates the comparison onto the LINE, which is what is being originated,
    and stops a flatter forecast from winning on calibration alone.

THE UNCERTAINTY
    1. A GAME-CLUSTER LOWER BOUND. Bets inside one game are not independent: a
       model that is wrong about one club is usually wrong about its opponent,
       and one bad weather read hits both. The interval is a cluster bootstrap
       that resamples GAMES, not bets. The published bound is the 5th percentile
       - the pessimistic end.
    2. A MULTIPLICITY ADJUSTMENT. If K strategies are ranked on the same data,
       the best is partly luck. The one-sided probability that each strategy's
       skill exceeds zero is adjusted across the K with the Holm step-down
       procedure, so the leaderboard cannot hand a prize to the luckiest of many.

THE CONTROLS
    RANDOM     picks drawn at random from the same games
    FAVOURITE  always takes the side the market priced shorter

    A strategy that cannot beat both has not demonstrated skill, it has
    demonstrated a run. Both controls are scored with the same metric.

THE DIVISIONS
    singles, game parlays, same-game parlays, prop combos. A combo is only
    ranked when a DIRECTLY VALIDATED JOINT PROBABILITY exists and the operator's
    void/push rules are documented. Multiplying marginal probabilities is invalid
    under dependence, so this module contains no code path that prices or ranks a
    combo from marginals: it reports the gate and stops.

WHAT IT NEVER DOES
    It never reads realised return into the ranking, and it never labels a
    backtest number skill. Return belongs to the staking ledger, a separate file
    and a separate page.
"""

from __future__ import annotations

import csv
import math
import random
from collections import defaultdict

# Divisions, in the order the brief names them.
DIVISIONS = ["singles", "game parlays", "same-game parlays", "prop combos"]

# A combo needs a validated joint probability to be ranked at all.
JOINT_EVIDENCE_REQUIRED = {"game parlays", "same-game parlays", "prop combos"}


# ---------------------------------------------------------------------------
# small numerical helpers (standard library only)
# ---------------------------------------------------------------------------
def norm_cdf(x: float) -> float:
    """Standard normal CDF (Abramowitz & Stegun 26.2.17, |error| < 7.5e-8)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def mean(xs) -> float:
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    return sum(xs) / len(xs) if xs else float("nan")


def stdev(xs) -> float:
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    if len(xs) < 2:
        return float("nan")
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def brier(probabilities, outcomes) -> float:
    """Mean squared error of a probability forecast. Lower is better."""
    if not probabilities:
        return float("nan")
    return sum((p - o) ** 2 for p, o in zip(probabilities, outcomes)) / len(probabilities)


def skill(model_probs, bench_probs, outcomes) -> float:
    """Benchmark-relative Brier skill: 1 - Brier(model) / Brier(benchmark)."""
    bm = brier(model_probs, outcomes)
    bb = brier(bench_probs, outcomes)
    if bb == 0 or not math.isfinite(bm) or not math.isfinite(bb):
        return float("nan")
    return 1.0 - bm / bb


def implied_probability(price_american) -> float:
    """Probability implied by a posted American price, before the vig is removed."""
    try:
        price = float(price_american)
    except (TypeError, ValueError):
        return float("nan")
    if price > 0:
        return 100.0 / (price + 100.0)
    if price < 0:
        return -price / (-price + 100.0)
    return float("nan")


# ---------------------------------------------------------------------------
# the two beliefs about the same event
# ---------------------------------------------------------------------------
def outcome_value(outcome: str) -> float:
    """1 win, 0 loss, 0.5 push. A push is half a win and half a refund."""
    return {"WIN": 1.0, "LOSE": 0.0, "PUSH": 0.5}.get((outcome or "").upper(),
                                                      float("nan"))


def market_belief(trade: dict, benchmark_row: dict = None) -> float:
    """The market's probability of the betting side winning, vig removed.

    The vig is removed because the model's own probability has no vig in it.
    Comparing a vig-free forecast against a vig-inflated price would make the
    market look worse than it is and would flatter the strategy for a reason
    that has nothing to do with skill.

    When both sides' prices are on the record the belief is the de-vigged price.
    When only one side is on the record the belief falls back to the single
    price as quoted, and the caller counts how often that happened so the
    fallback is visible rather than silent.
    """
    market = (trade.get("market") or "").upper()
    side = (trade.get("side_key") or "").lower()
    b = benchmark_row or {}
    pairs = {
        "SIDE": ("home_side_price", "away_side_price", "home"),
        "TOTAL": ("over_price", "under_price", "over"),
        "MONEYLINE": ("market_ml_home", "market_ml_away", "home"),
    }
    if market in pairs:
        first, second, first_side = pairs[market]
        p1 = implied_probability(b.get(first))
        p2 = implied_probability(b.get(second))
        if math.isfinite(p1) and math.isfinite(p2) and (p1 + p2) > 0:
            belief_first = p1 / (p1 + p2)
            return belief_first if side == first_side else 1.0 - belief_first
    return implied_probability(trade.get("price_american"))


def model_belief(trade: dict, sigma_margin: float, sigma_total: float) -> float:
    """The model's probability of the betting side winning.

    MONEYLINE is already a probability (fair_line is the model's own P(home)).
    SIDE and TOTAL are lines, and are converted with the shared residual scale:

        SIDE   own + settle_line > 0, so P(win) = Phi((model_own + settle_line)/sigma)
        TOTAL  own > 0, so P(win) = Phi(model_own / sigma)
    """
    market = (trade.get("market") or "").upper()
    side = (trade.get("side_key") or "").lower()
    try:
        fair = float(trade.get("fair_line"))
    except (TypeError, ValueError):
        return float("nan")
    if market == "MONEYLINE":
        return fair if side == "home" else 1.0 - fair
    try:
        strike = float(trade.get("settle_line"))
    except (TypeError, ValueError):
        return float("nan")
    if market == "SIDE":
        model_own = -fair if side == "home" else fair
        return norm_cdf((model_own + strike) / sigma_margin)
    if market == "TOTAL":
        # `fair` and `strike` are both game totals, so the comparison is the
        # model's total minus the line, NOT model minus actual. Using the
        # model's absolute level here would score a sharp forecast as if it
        # were a guess of "over" every time.
        diff = (fair - strike) if side == "over" else (strike - fair)
        return norm_cdf(diff / sigma_total)
    return float("nan")


def line_errors(trade: dict):
    """(model error, market error) in POINTS, or None if the market has no line.

    Both are measured against the actual outcome of the same thing the bet was
    about: the betting side's own margin for a spread, the game total for a
    total. Moneyline is a probability market and has no line to be accurate
    about, so it is skipped.
    """
    market = (trade.get("market") or "").upper()
    side = (trade.get("side_key") or "").lower()
    if market not in ("SIDE", "TOTAL"):
        return None
    try:
        fair = float(trade.get("fair_line"))
        strike = float(trade.get("settle_line"))
    except (TypeError, ValueError):
        return None
    try:
        if market == "SIDE":
            # `settle_line` is already in the betting side's own perspective:
            # the backtest writes market_line for a home bet and -market_line
            # for an away bet. The market's forecast of the side's own margin
            # is therefore -settle_line for BOTH sides. Subtracting the line
            # instead of adding it for away bets would double the sign flip.
            margin = float(trade.get("margin_home"))
            actual = margin if side == "home" else -margin
            model_own = -fair if side == "home" else fair
            market_own = -strike
        else:
            # a total is the same number for both sides: the over wins on the
            # high side of the line, the under on the low side, and the line's
            # error is the same error either way. Flipping the sign for an
            # under would turn a well-lined game into a miss.
            actual = float(trade.get("total_points"))
            model_own = fair
            market_own = strike
    except (TypeError, ValueError):
        return None
    return actual - model_own, actual - market_own


def estimate_sigmas(trades) -> dict:
    """The residual scale of the market line, estimated from settled games.

    A line and a probability are different things, so the spread of the market
    line's own error has to be known before a line can be turned into one. It is
    estimated from the settled trades themselves: the standard deviation of the
    market's error on spreads, and on totals.

    This is a property of the MARKET's line, not of any strategy, and it is
    published with the result so a reader can check it.
    """
    side_res, tot_res = [], []
    for t in trades:
        errs = line_errors(t)
        if not errs:
            continue
        market_err = errs[1]
        if (t.get("market") or "").upper() == "SIDE":
            side_res.append(market_err)
        else:
            tot_res.append(market_err)
    return {
        "sigma_margin": stdev(side_res),
        "sigma_total": stdev(tot_res),
        "n_margin": len(side_res),
        "n_total": len(tot_res),
        "mae_margin": mean([abs(x) for x in side_res]),
        "mae_total": mean([abs(x) for x in tot_res]),
    }


# ---------------------------------------------------------------------------
# clustering and the interval
# ---------------------------------------------------------------------------
def cluster_bootstrap(model_probs, bench_probs, outcomes, groups,
                      n_boot: int = 2000, seed: int = 20261117) -> dict:
    """Skill distribution from a bootstrap that resamples GAMES, not bets."""
    by_cluster = defaultdict(list)
    for i, g in enumerate(groups):
        by_cluster[g].append(i)
    cluster_ids = sorted(by_cluster)
    if not cluster_ids:
        return {"lower": float("nan"), "median": float("nan"),
                "upper": float("nan"), "n_boot": 0, "p_skill_gt_zero": float("nan")}
    rng = random.Random(seed)
    values = []
    for _ in range(n_boot):
        idx = []
        for _ in cluster_ids:
            idx.extend(by_cluster[cluster_ids[rng.randrange(len(cluster_ids))]])
        s = skill([model_probs[i] for i in idx],
                  [bench_probs[i] for i in idx],
                  [outcomes[i] for i in idx])
        if math.isfinite(s):
            values.append(s)
    values.sort()
    if not values:
        return {"lower": float("nan"), "median": float("nan"),
                "upper": float("nan"), "n_boot": 0, "p_skill_gt_zero": float("nan")}
    lo = max(0, int(round(0.05 * (len(values) - 1))))
    hi = min(len(values) - 1, int(round(0.95 * (len(values) - 1))))
    return {
        "lower": values[lo],
        "median": values[len(values) // 2],
        "upper": values[hi],
        "n_boot": len(values),
        "p_skill_gt_zero": sum(1 for v in values if v > 0) / len(values),
    }


def holm_adjust(pvalues: dict) -> dict:
    """Holm step-down adjustment for a family of K one-sided p-values."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    k = len(items)
    out = {}
    running = 0.0
    for i, (key, p) in enumerate(items):
        running = max(running, min(1.0, (k - i) * p))
        out[key] = running
    return out


# ---------------------------------------------------------------------------
# controls
# ---------------------------------------------------------------------------
def control_random(model_probs, bench_probs, outcomes, seed: int = 20261118) -> float:
    """Random picks: as many bets as the strategy made, drawn at random."""
    n = len(outcomes)
    if n == 0:
        return float("nan")
    rng = random.Random(seed)
    picks = [rng.randrange(n) for _ in range(n)]
    return skill([model_probs[i] for i in picks],
                 [bench_probs[i] for i in picks],
                 [outcomes[i] for i in picks])


def control_favourite(bench_probs, outcomes) -> float:
    """Favourites only: always take the side the market priced shorter.

    The market's favourite is the side with the higher de-vigged probability, so
    this control's forecast is simply max(p, 1-p) against p. It is a demanding
    control on a sharp market, which is the point: it shows how much of a
    strategy's apparent skill is just siding with the crowd.
    """
    mp, bp, oc = [], [], []
    for q, o in zip(bench_probs, outcomes):
        if not math.isfinite(q):
            continue
        mp.append(max(q, 1.0 - q))
        bp.append(q)
        oc.append(o)
    return skill(mp, bp, oc)


# ---------------------------------------------------------------------------
# scoring one strategy
# ---------------------------------------------------------------------------
def score_strategy(trades, sigma_margin: float, sigma_total: float,
                   benchmarks: dict = None, n_boot: int = 2000,
                   seed: int = 20261117) -> dict:
    """Score one strategy's trades with every measure the brief asks for."""
    benchmarks = benchmarks or {}
    model_probs, bench_probs, outcomes, groups = [], [], [], []
    model_errs, market_errs = [], []
    fallback = 0
    for t in trades:
        p_model = model_belief(t, sigma_margin, sigma_total)
        p_bench = market_belief(t, benchmarks.get(t.get("game_id")))
        o = outcome_value(t.get("outcome"))
        if not (math.isfinite(p_model) and math.isfinite(p_bench) and math.isfinite(o)):
            continue
        if math.isfinite(implied_probability(t.get("price_american"))) and \
                abs(p_bench - implied_probability(t.get("price_american"))) < 1e-12:
            fallback += 1
        model_probs.append(p_model)
        bench_probs.append(p_bench)
        outcomes.append(o)
        groups.append(t.get("game_id") or t.get("trade_key"))
        errs = line_errors(t)
        if errs:
            model_errs.append(errs[0])
            market_errs.append(errs[1])
    n = len(outcomes)
    if n == 0:
        return {"n_bets": 0}

    boot = cluster_bootstrap(model_probs, bench_probs, outcomes, groups,
                             n_boot=n_boot, seed=seed)
    mae_model = mean([abs(x) for x in model_errs])
    mae_market = mean([abs(x) for x in market_errs])
    return {
        "n_bets": n,
        "n_games": len(set(groups)),
        "n_price_fallback": fallback,
        "brier_model": brier(model_probs, outcomes),
        "brier_benchmark": brier(bench_probs, outcomes),
        "brier_skill": skill(model_probs, bench_probs, outcomes),
        "skill_lower_95": boot["lower"],
        "skill_median": boot["median"],
        "skill_upper_95": boot["upper"],
        "p_skill_gt_zero": boot["p_skill_gt_zero"],
        "control_random": control_random(model_probs, bench_probs, outcomes),
        "control_favourite": control_favourite(bench_probs, outcomes),
        "hit_rate": mean([1.0 if o == 1.0 else 0.0 for o in outcomes
                          if o != 0.5]) if any(o != 0.5 for o in outcomes)
                    else float("nan"),
        "mean_model_prob": mean(model_probs),
        "mean_bench_prob": mean(bench_probs),
        "model_line_mae": mae_model,
        "market_line_mae": mae_market,
        "line_skill_vs_market_line": (1.0 - mae_model / mae_market
                                      if math.isfinite(mae_market) and mae_market
                                      else float("nan")),
    }


# ---------------------------------------------------------------------------
# the combo gate
# ---------------------------------------------------------------------------
def joint_evidence_gate(entry: dict) -> dict:
    """The gate a combo must pass before it can be ranked at all.

    Multiplying marginal probabilities is invalid under dependence, so a combo is
    ranked only when a directly validated joint probability exists AND the
    operator's void/push rules are documented. A combo missing either is GATED
    and is not scored.
    """
    joint = entry.get("joint_probability_validated")
    void = entry.get("void_push_rules_documented")
    if joint and void:
        return {"gated": False,
                "reason": "joint probability validated and void/push rules documented"}
    missing = []
    if not joint:
        missing.append("no directly validated joint probability")
    if not void:
        missing.append("no documented void/push rules")
    return {"gated": True, "reason": "; ".join(missing)}


def load_trades(path: str) -> list:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))
