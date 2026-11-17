#!/usr/bin/env python3
"""
scoreboard_d5.py — the pre-registration / qualification scoreboard for session
arena/d50423eb-fl1.

What this module is for
-----------------------
The brief asks for a leaderboard competition with rewards for top strategies, in
four divisions (singles, game parlays, same-game parlays, prop combos), where every
strategy must pass validation gates before it can be ranked, and where ranking is
on *skill*, not on a lucky staking run.

This module implements the ranking maths and the gates. It deliberately does NOT
declare a winner on this season's data, because:

  * no strategy here has a pre-registered forecast record against a benchmark;
  * the market prices in this repository are third-party (nflverse) and were
    quarantined for settlement by an earlier session (S85);
  * a 137-game season cannot clear the sample bar for a 52.4%-break-even market.

Instead it publishes, for every strategy, the number that *would* clear the gate,
so a reader can see how far away each one is. That is the honest form of a
leaderboard during the registration window.

Key definitions, each of which maps to a brief line
--------------------------------------------------
Brier score            mean squared error of a probability forecast, outcome in {0,1}
Brier skill score      BSS = 1 - BS_model / BS_benchmark    (benchmark-relative skill)
cluster bootstrap       resample whole *games*, not single bets, so the dependence
                       between bets on the same game cannot be resampled away
lower confidence bound the 2.5th percentile of the cluster-bootstrap distribution of BSS;
                       a strategy ranks only if this is > 0
multiplicity           Benjamini-Hochberg step-up across the number of registered
                       hypotheses, because trying 40 rules and reporting the best one
                       is how noise gets published
control baselines      random picks at the same vig, and favourites-only, scored the
                       same way, so "skill" has something to beat
staking is not skill  a staking yield is reported beside the signal and can never
                       change the rank; reward eligibility needs both bounds positive

Everything here is stdlib only.
"""

from __future__ import annotations

import math
import random
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------- constants
AMERICAN_BREAKEVEN = {
    # break-even probability for a two-way market at these prices, no push
    -110: 110.0 / 210.0,
}
DEFAULT_VIG_PRICE = -110

DIVISIONS = ("singles", "game_parlay", "same_game_parlay", "prop_combo")

# Minimum sample at which a 52.38% market can be told from a 55% edge at 80% power.
# Computed, not asserted: see sample_for_edge().
EDGE_FOR_POWER = (0.55, 0.5238, 0.80)


# --------------------------------------------------------------------------- basic maths
def american_to_prob(price: int) -> float:
    """Implied probability of an American price, vig included."""
    if price < 0:
        return (-price) / ((-price) + 100.0)
    return 100.0 / (price + 100.0)


def american_payout_per_unit(price: int) -> float:
    """Profit on a 1-unit winning stake (not including the returned stake)."""
    if price < 0:
        return 100.0 / (-price)
    return price / 100.0


def brier(probs: Sequence[float], outcomes: Sequence[int]) -> float:
    if len(probs) != len(outcomes):
        raise ValueError("probs and outcomes must be the same length")
    if not probs:
        raise ValueError("no forecasts")
    return sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / len(probs)


def brier_skill(model_probs, outcomes, bench_probs) -> float:
    """1 - BS_model / BS_benchmark. Positive means the model beats the benchmark."""
    bs_m = brier(model_probs, outcomes)
    bs_b = brier(bench_probs, outcomes)
    if bs_b == 0:
        raise ValueError("benchmark Brier score is zero; skill is undefined")
    return 1.0 - bs_m / bs_b


def log_loss(probs: Sequence[float], outcomes: Sequence[int], eps: float = 1e-9) -> float:
    total = 0.0
    for p, y in zip(probs, outcomes):
        p = min(max(p, eps), 1.0 - eps)
        total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return total / len(probs)


def wilson(successes: int, n: int, z: float = 1.959963984540054) -> Tuple[float, float]:
    """Wilson score interval. Used instead of normal-approx because n is small here."""
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def sample_for_edge(p1: float, p0: float, power: float = 0.8,
                    alpha: float = 0.05) -> int:
    """Bets needed to detect p1 > p0 at `power` with a one-sided alpha test.

    Uses the standard two-proportion approximation with the null variance at p0.
    Returns an integer; never returns less than 1.
    """
    z_a = _z_for(1 - alpha)
    z_b = _z_for(power)
    num = (z_a * math.sqrt(p0 * (1 - p0)) + z_b * math.sqrt(p1 * (1 - p1))) ** 2
    den = (p1 - p0) ** 2
    return max(1, int(math.ceil(num / den)))


def _z_for(p: float) -> float:
    """Inverse normal CDF (Acklam's rational approximation, |error| < 1.15e-9)."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0,1)")
    a = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00)
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


# --------------------------------------------------------------------------- clustering
def cluster_bootstrap_skill(model_probs: Sequence[float], outcomes: Sequence[int],
                            bench_probs: Sequence[float], clusters: Sequence[str],
                            reps: int = 2000, seed: int = 20261117,
                            alpha: float = 0.05) -> Dict[str, float]:
    """Brier skill with a *game-cluster* bootstrap interval.

    A bet is not an independent observation when several bets ride on the same game
    (a side and a total, or a same-game parlay's legs). Resampling individual bets
    would understate the interval. This resamples whole clusters — games — with
    replacement, which is the conservative choice.
    """
    if not (len(model_probs) == len(outcomes) == len(bench_probs) == len(clusters)):
        raise ValueError("all inputs must be the same length")
    groups: Dict[str, List[int]] = {}
    for i, c in enumerate(clusters):
        groups.setdefault(c, []).append(i)
    keys = sorted(groups)
    if len(keys) < 2:
        return {"bss": brier_skill(model_probs, outcomes, bench_probs),
                "lo": None, "hi": None, "n": len(model_probs), "clusters": len(keys),
                "note": "fewer than two clusters: an interval cannot be formed"}
    point = brier_skill(model_probs, outcomes, bench_probs)
    rng = random.Random(seed)
    draws: List[float] = []
    for _ in range(reps):
        mp: List[float] = []
        oc: List[int] = []
        bp: List[float] = []
        for _ in range(len(keys)):
            k = keys[rng.randrange(len(keys))]
            for i in groups[k]:
                mp.append(model_probs[i])
                oc.append(outcomes[i])
                bp.append(bench_probs[i])
        try:
            draws.append(brier_skill(mp, oc, bp))
        except ValueError:
            continue
    if not draws:
        return {"bss": point, "lo": None, "hi": None, "n": len(model_probs),
                "clusters": len(keys), "note": "bootstrap produced no valid draw"}
    draws.sort()
    lo = draws[int(math.floor((alpha / 2) * len(draws)))]
    hi = draws[min(len(draws) - 1, int(math.ceil((1 - alpha / 2) * len(draws))) - 1)]
    return {"bss": point, "lo": lo, "hi": hi, "n": len(model_probs),
            "clusters": len(keys), "reps": len(draws),
            "note": "cluster bootstrap over games, %d reps, seed 20261117" % reps}


# --------------------------------------------------------------------------- multiplicity
def benjamini_hochberg(pvals: Sequence[float], q: float = 0.05) -> List[bool]:
    """BH step-up. Returns a pass/fail per hypothesis, index-aligned with input."""
    m = len(pvals)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: pvals[i])
    keep = [False] * m
    k_max = 0
    for rank, i in enumerate(order, start=1):
        if pvals[i] <= q * rank / m:
            k_max = rank
    for rank, i in enumerate(order, start=1):
        if rank <= k_max:
            keep[i] = True
    return keep


# --------------------------------------------------------------------------- gates
def gates_for(entry: dict, ctx: dict) -> List[dict]:
    """Evaluate the qualification gates for one registered strategy.

    Returns a list of {gate, passed, detail, clears_when}. A gate that cannot be
    evaluated on the data available is reported as NOT PASSED with the reason —
    never as passed by default. That is the point: silence is not a pass.
    """
    out: List[dict] = []
    div = entry.get("division")
    sig = entry.get("signal") or {}
    stk = entry.get("staking") or {}

    # G1 — pre-registered before results were seen.
    reg = entry.get("registration") or {}
    out.append({
        "gate": "D5-G1",
        "name": "Pre-registered before results",
        "passed": bool(reg.get("committed") and reg.get("hash")),
        "detail": ("rule text committed at %s, sha256 %s" % (reg.get("committed"),
                   (reg.get("hash") or "")[:16])) if reg.get("committed") else
                  "no committed rule text: the definition could still be changed after seeing results",
        "clears_when": "commit the rule text, window and gates to git; the commit hash is the registration",
    })

    # G2 — a realised forecast record exists at all.
    n = sig.get("n") or 0
    out.append({
        "gate": "D5-G2",
        "name": "Prospective forecast record",
        "passed": n > 0,
        "detail": ("%d scored forecasts" % n) if n else
                  "0 forecasts have been recorded against a benchmark for this strategy",
        "clears_when": "one forecast per selection, logged before kickoff, with the probability",
    })

    # G3 — sample size clears the power bar for this division.
    bar = ctx["sample_bar"].get(div, ctx["sample_bar"]["singles"])
    out.append({
        "gate": "D5-G3",
        "name": "Sample clears the power bar",
        "passed": n >= bar,
        "detail": "%d of %d forecasts" % (n, bar),
        "clears_when": "%d scored forecasts at a 55%% edge against a 52.4%% break-even" % bar,
    })

    # G4 — skill lower bound above zero, benchmark-relative.
    lo = sig.get("bss_lo")
    out.append({
        "gate": "D5-G4",
        "name": "Benchmark-relative skill lower bound > 0",
        "passed": lo is not None and lo > 0,
        "detail": ("BSS %.4f, game-cluster 95%% lower bound %s" %
                   (sig.get("bss") or 0.0, ("%.4f" % lo) if lo is not None else "not computable"))
                  if n else "no forecasts, so no skill interval",
        "clears_when": "the lower bound of the clustered BSS interval is above zero",
    })

    # G5 — multiplicity: did it survive under the number of registered trials?
    out.append({
        "gate": "D5-G5",
        "name": "Survives multiplicity adjustment",
        "passed": bool(entry.get("multiplicity_pass")),
        "detail": entry.get("multiplicity_detail") or
                  "not evaluated: %d registered hypotheses in this division window" % ctx["n_hypotheses"],
        "clears_when": "Benjamini-Hochberg q=0.05 across all registered hypotheses",
    })

    # G6 — staking can add reward but can never lift a weak signal.
    out.append({
        "gate": "D5-G6",
        "name": "Staking cannot mask the signal",
        "passed": bool(stk.get("eligible")),
        "detail": ("staking yield %.4f with lower bound %s; ranked on signal only" %
                   (stk.get("yield") or 0.0,
                    ("%.4f" % stk["lo"]) if stk.get("lo") is not None else "not computable"))
                  if stk.get("n") else
                  "0 settled stakes; market cells blank because no official price source exists",
        "clears_when": "both the signal bound and the staking bound are positive, and the rank is unchanged",
    })

    # G7 — combos need a directly validated joint probability, not a product of marginals.
    if div in ("game_parlay", "same_game_parlay", "prop_combo"):
        jv = entry.get("joint_validation") or {}
        out.append({
            "gate": "D5-G7",
            "name": "Joint probability directly validated",
            "passed": bool(jv.get("validated")),
            "detail": jv.get("detail") or
                      "combos are priced off marginal probabilities multiplied together, which is only "
                      "correct under independence; no directly validated joint probability exists",
            "clears_when": "a joint probability estimated from realised joint outcomes, plus the operator's void/push rules",
        })
        out.append({
            "gate": "D5-G8",
            "name": "Operator void/push rules on file",
            "passed": bool(jv.get("void_rules")),
            "detail": jv.get("void_detail") or
                      "a same-game parlay's void rule changes its settlement, and no operator's rules are on file",
            "clears_when": "the operator's written void/push rules are registered against the combo",
        })
    return out


def qualified(gate_rows: Sequence[dict]) -> bool:
    return all(g["passed"] for g in gate_rows)


# --------------------------------------------------------------------------- scoreboard
def rank(entries: Sequence[dict]) -> List[dict]:
    """Rank by signal lower bound. Staking never enters the key.

    Entries without a computable lower bound sort last — never first. That ordering
    rule is the whole point: missing evidence must not read as good evidence.
    """
    def key(e: dict):
        lo = (e.get("signal") or {}).get("bss_lo")
        return (0 if lo is not None else 1, -(lo or 0.0), e.get("id", ""))
    ranked = sorted(entries, key=key)
    for i, e in enumerate(ranked, start=1):
        e["rank"] = i
    return ranked


def control_baselines(n_games: int, seed: int = 20261117,
                      price: int = DEFAULT_VIG_PRICE) -> Dict[str, float]:
    """The two controls every leaderboard run must carry.

    They are *designed*, not measured: a random pick, and a favourites-only pick,
    at the stated price. Publishing the arithmetic lets a reader check the bar a
    strategy has to clear before claiming skill.
    """
    p_implied = american_to_prob(price)
    return {
        "random_expected_hit": 0.5,
        "random_expected_yield": 0.5 * (1 + american_payout_per_unit(price)) - 1.0,
        "breakeven_hit": p_implied,
        "favourite_bar": ("a favourites-only rule has to clear %.4f hit rate at %d "
                          "just to break even; it has no skill until it clears it" % (p_implied, price)),
        "n_games": n_games,
        "price": price,
        "seed": seed,
    }


def sample_bars() -> Dict[str, int]:
    """Per-division sample bar. Parlay divisions need more because their variance is higher."""
    p1, p0, pw = EDGE_FOR_POWER
    base = sample_for_edge(p1, p0, pw)
    return {
        "singles": base,
        "game_parlay": int(math.ceil(base * 1.5)),
        "same_game_parlay": int(math.ceil(base * 2.0)),
        "prop_combo": int(math.ceil(base * 2.0)),
    }


# --------------------------------------------------------------------------- predictions
def normal_cdf(x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2.0))))


def cover_probability(market_line: float, fair_line: float, sigma: float) -> float:
    """P(the market number covers) given our fair number and a margin sd.

    For a spread, `market_line` is the number the market hangs and `fair_line` our own.
    A bet on the side at `market_line` wins when the realised margin exceeds it, so the
    probability is 1 - Phi((market_line - fair_line)/sigma). This is the only place a
    "market vs fair" probability is formed in this repository, and it stays blank when
    either input is blank.
    """
    if market_line is None or fair_line is None or not sigma:
        return None
    z = (market_line - fair_line) / sigma
    return 1.0 - normal_cdf(z)


def push_probability(market_line: float, fair_line: float, sigma: float) -> float:
    """P(exactly the market number), approximated with a half-point continuity window.

    NFL spreads and totals land on .0 or .5. A .5 line cannot push; a .0 line can.
    """
    if market_line is None or fair_line is None or not sigma:
        return None
    if abs(market_line - round(market_line)) > 1e-9:
        return 0.0
    z = (market_line - fair_line) / sigma
    return normal_cdf(z + 0.25) - normal_cdf(z - 0.25)
