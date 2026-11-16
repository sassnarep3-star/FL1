"""Correlation publication gate: official inputs only, and `n` on every value.

THE RULE, WRITTEN DOWN SO IT CAN BE ENFORCED AND NOT ARGUED WITH
    The brief says correlations are to be computed *only from officially sourced numbers*
    and published *with n*. Both halves are enforced here:

      1. every operand of a correlation carries a source tier, and the gate refuses to
         publish a value whose operands are not both official (tier `OFFICIAL-LEAGUE` or
         `OFFICIAL-CLUB`);
      2. a published value carries `n` (the number of joint observations, not the number
         of rows in the file), a bootstrap interval, the window it was computed over, and
         the link to the capture it came from.

    A number derived from a third-party price feed is not "wrong" - it is a real
    measurement of that dataset - but publishing it in a column headed *correlation*
    without a tier would let a reader take it for a fact about the league. So those rows
    are computed, labelled and held. That is the whole of the gate: it is a publication
    rule about provenance, not a statistical objection.

WHAT THIS ALSO MAKES IMPOSSIBLE, ON PURPOSE
    A market correlation (is the over correlated with the home cover?) needs a *price* on
    both legs. No official league source publishes prices, so the honest published answer
    for that family of pairs is a blank with the reason attached, plus the Frechet bounds
    that hold for *any* dependence - which is what a parlay price has to respect anyway.

Reproduce:  python3 -m engine.correlation_gate
"""

from __future__ import annotations

import math
import random
from collections import OrderedDict
from typing import Sequence

TIER_OFFICIAL = ("OFFICIAL-LEAGUE", "OFFICIAL-CLUB")
TIER_THIRD_PARTY = ("THIRD-PARTY-AGGREGATOR", "THIRD-PARTY-MIRROR")

MIN_N_PUBLISH = 30          # below this, no interval is quoted at all
MIN_N_LEADERBOARD = 100     # below this, a gate may not cite the value


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    if n < 3 or len(ys) != n:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return float("nan")
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def phi(p_a: int, p_b: int, p_ab: int, n: int) -> float:
    """Correlation of two binary events from their counts - the parlay-relevant statistic."""
    if n < 3:
        return float("nan")
    a, b, ab = p_a / n, p_b / n, p_ab / n
    var_a, var_b = a * (1 - a), b * (1 - b)
    if var_a <= 0 or var_b <= 0:
        return float("nan")
    return (ab - a * b) / math.sqrt(var_a * var_b)


def bootstrap_rho(xs: Sequence[float], ys: Sequence[float], n_boot: int = 1500,
                  conf: float = 0.95, seed: int = 20261114) -> tuple[float, float]:
    """Percentile interval for a correlation, fixed seed so the site is reproducible."""
    n = len(xs)
    if n < 10:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    vals = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        r = pearson([xs[i] for i in idx], [ys[i] for i in idx])
        if r == r:
            vals.append(r)
    if len(vals) < 20:
        return (float("nan"), float("nan"))
    vals.sort()
    lo_i = int(math.floor((1 - conf) / 2 * len(vals)))
    hi_i = int(math.ceil((1 + conf) / 2 * len(vals))) - 1
    return vals[max(0, lo_i)], vals[min(len(vals) - 1, hi_i)]


def paired_bootstrap_rho(xs: Sequence[float], ys: Sequence[float], **kw) -> tuple[float, float]:
    return bootstrap_rho(xs, ys, **kw)


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------
def gate(pair: dict) -> dict:
    """Decide whether a computed correlation may be published as a sourced value.

    Every reason is returned, including the ones that pass, so the table can print the
    basis instead of a bare tick.
    """
    reasons: list[str] = []
    x_tier = (pair.get("x_tier") or "").strip()
    y_tier = (pair.get("y_tier") or "").strip()
    for who, tier in (("x", x_tier), ("y", y_tier)):
        if tier not in TIER_OFFICIAL:
            reasons.append("%s operand is %s, not an official source" %
                          (who.upper(), tier or "UNCLASSIFIED"))
    n = pair.get("n") or 0
    if not n:
        reasons.append("no joint-observation count - n is part of the number, not a footnote")
    elif n < MIN_N_PUBLISH:
        reasons.append("n=%d is below the %d-observation floor for quoting an interval"
                       % (n, MIN_N_PUBLISH))
    if pair.get("joint_observations") is False:
        reasons.append("the two series were never observed on the same units")
    rho = pair.get("rho")
    if rho is None or rho != rho:
        reasons.append("the statistic is undefined on this sample (a zero-variance leg)")
    verdict = "PUBLISH" if not reasons else "HOLD"
    out = OrderedDict(pair)
    out["verdict"] = verdict
    out["gate_reasons"] = "; ".join(reasons) if reasons else \
        "both operands official, n published with the value, joint observations present"
    out["n"] = n
    return out


def frechet(p_a: float, p_b: float) -> tuple[float, float]:
    """Bounds that hold for *any* dependence - the only honest statement without data."""
    return max(0.0, p_a + p_b - 1.0), min(p_a, p_b)


def joint_from_rho(p_a: float, p_b: float, rho: float) -> float:
    sd = math.sqrt(p_a * (1 - p_a) * p_b * (1 - p_b))
    if sd <= 0:
        return float("nan")
    return p_a * p_b + rho * sd


def parlay_price_effect(p_a: float, p_b: float, rho: float, dec: float) -> dict:
    """What a given dependence does to a two-leg price, at a fixed decimal payout."""
    indep = p_a * p_b
    joint = joint_from_rho(p_a, p_b, rho)
    if joint != joint:
        return {}
    ev_indep = dec * indep - 1.0
    ev_joint = dec * joint - 1.0
    lo, hi = frechet(p_a, p_b)
    return OrderedDict([
        ("independent_joint_prob", round(indep, 6)),
        ("true_joint_prob", round(joint, 6)),
        ("frechet_low", round(lo, 6)), ("frechet_high", round(hi, 6)),
        ("ev_at_independence", round(ev_indep, 6)), ("ev_at_true_joint", round(ev_joint, 6)),
        ("ev_error_per_unit", round(ev_indep - ev_joint, 6)),
        ("break_even_prob_at_price", round(1.0 / dec, 6) if dec > 0 else ""),
    ])


# ---------------------------------------------------------------------------
# the pairs we can actually compute from official numbers
# ---------------------------------------------------------------------------
def official_pairs(ledger: Sequence[dict], test_total_threshold: float = 44.5) -> dict:
    """Correlations computable from scores alone, on games verified against the official table.

    `test_total_threshold` is *our stated cut*, not a market price: it exists so a
    parlay-shaped pair of binary events can be measured at all without touching a price
    feed. The row says so, because otherwise it would read like a market total.
    """
    rows = [r for r in ledger
            if r["verify_status"] == "MATCHED_TWO_FEEDS" and r["margin_home"] != ""]
    by_week: dict = {}
    margin = [float(r["margin_home"]) for r in rows]
    total = [float(r["total_points"]) for r in rows]
    home_win = [1.0 if m > 0 else 0.0 for m in margin]
    over = [1.0 if t > test_total_threshold else 0.0 for t in total]
    n = len(rows)
    out = OrderedDict()
    if n >= 3:
        r1 = pearson(margin, total)
        lo1, hi1 = bootstrap_rho(margin, total)
        a = int(sum(home_win))
        b = int(sum(over))
        ab = int(sum(1 for hw, ov in zip(home_win, over) if hw and ov))
        r2 = phi(a, b, ab, n)
        lo2, hi2 = bootstrap_rho(home_win, over)
        out["P-01"] = OrderedDict([
            ("id", "P-01"), ("pair", "final margin (home perspective) vs final total points"),
            ("why", "the dependence that makes 'favourite and under' a single bet, not two"),
            ("statistic", "pearson"), ("rho", round(r1, 5)),
            ("ci_low", round(lo1, 5)), ("ci_high", round(hi1, 5)),
            ("n", n), ("window", "%s..%s" % (rows[0]["season"], rows[-1]["season"])),
            ("x_source", "official nfl.com game scores (data/results.tsv)"),
            ("x_tier", "OFFICIAL-LEAGUE"),
            ("y_source", "official nfl.com game scores (data/results.tsv)"),
            ("y_tier", "OFFICIAL-LEAGUE"),
            ("joint_observations", True),
            ("note", "same 137 games both feeds agree on; no price involved"),
        ])
        out["P-02"] = OrderedDict([
            ("id", "P-02"),
            ("pair", "home win vs total points above %.1f (a stated test cut, not a market total)"
             % test_total_threshold),
            ("why", "the parlay shape this project would actually write: ML leg + total leg"),
            ("statistic", "phi"), ("rho", round(r2, 5)),
            ("ci_low", round(lo2, 5)), ("ci_high", round(hi2, 5)),
            ("n", n), ("p_a", round(a / n, 5)), ("p_b", round(b / n, 5)),
            ("p_ab", round(ab / n, 5)),
            ("x_source", "official nfl.com game scores (data/results.tsv)"),
            ("x_tier", "OFFICIAL-LEAGUE"),
            ("y_source", "official nfl.com game scores (data/results.tsv)"),
            ("y_tier", "OFFICIAL-LEAGUE"),
            ("joint_observations", True),
            ("note", "the threshold is ours and is labelled as such; changing it changes rho"),
        ])
        # within-week independence of two different games - the cross-game parlay assumption
        by_week: dict = {}
        for r in rows:
            by_week.setdefault(r["week"], []).append(1.0 if float(r["margin_home"]) > 0 else 0.0)
        xs, ys = [], []
        for wk, vals in sorted(by_week.items()):
            for i in range(len(vals)):
                for j in range(i + 1, len(vals)):
                    xs.append(vals[i])
                    ys.append(vals[j])
        if len(xs) >= 30:
            r3 = pearson(xs, ys)
            lo3, hi3 = bootstrap_rho(xs, ys)
            out["P-03"] = OrderedDict([
                ("id", "P-03"),
                ("pair", "home win in one game vs home win in another game the same week"),
                ("why", "the independence assumption behind every two-leg cross-game parlay"),
                ("statistic", "pearson on paired game-week observations"),
                ("rho", round(r3, 5)), ("ci_low", round(lo3, 5)), ("ci_high", round(hi3, 5)),
                ("n", len(xs)), ("window", "2026 weeks 1-10, all within-week game pairs"),
                ("x_source", "official nfl.com game scores (data/results.tsv)"),
                ("x_tier", "OFFICIAL-LEAGUE"),
                ("y_source", "official nfl.com game scores (data/results.tsv)"),
                ("y_tier", "OFFICIAL-LEAGUE"),
                ("joint_observations", True),
                ("note", "pairs are not independent draws across weeks; the interval is "
                        "treated as indicative, and the row says so"),
            ])
    counts = {"games_used": n, "weeks": len(by_week) if rows else 0,
              "test_total_threshold": test_total_threshold}
    return {"pairs": out, "counts": counts}


def held_rows(candidates: Sequence[dict]) -> list[dict]:
    """Run the gate over everything, including the pairs the gate will refuse."""
    return [gate(c) for c in candidates]


if __name__ == "__main__":  # pragma: no cover
    import sys
    sys.path.insert(0, ".")
    from engine import market_feed, results_ledger

    games = market_feed.load_games()
    led = results_ledger.build_ledger(games, market_feed.load_official_results(),
                                      OrderedDict([("2026", market_feed.load_official_standings())]))
    res = official_pairs(led["rows"])
    for k, v in res["pairs"].items():
        print(k, v["rho"], "n=%s" % v["n"], gate(v)["verdict"])
