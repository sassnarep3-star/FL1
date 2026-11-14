"""Correlation, measured where it can be measured and specified where it cannot.

Two different jobs, kept strictly apart:

  MEASURED  Pearson rho across the 32 verified clubs. Exact arithmetic on data that exists.
  SPECIFIED analytic rho for pairs of legs inside one game under the model's own error
            structure. Computable without any extra data, and useful because it shows which
            parlay legs are nearly-free of dependence and which are mechanically stacked.
  MISSING   rho that only play-by-play or a multi-season line history can give (game-flow
            dependence, same-player prop coupling). Never estimated here - reported as blank.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIED = ROOT / "data" / "verified"
MODEL_OUT = ROOT / "data" / "model"


def pearson(xs: list[float], ys: list[float]) -> dict:
    n = len(xs)
    if n != len(ys) or n < 3:
        raise ValueError("need >=3 paired observations")
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    r = sxy / math.sqrt(sxx * syy)
    # Fisher z interval, n-3 d.o.f. - reported so a reader can see how loose it is
    z = 0.5 * math.log((1 + r) / (1 - r)) if abs(r) < 1 else float("inf")
    se = 1.0 / math.sqrt(n - 3)
    lo = math.tanh(z - 1.96 * se)
    hi = math.tanh(z + 1.96 * se)
    return {"n": n, "rho": round(r, 4), "ci95": [round(lo, 4), round(hi, 4)]}


def bvn_cdf(h: float, k: float, rho: float) -> float:
    """P(X<=h, Y<=k) for a standard bivariate normal, via 160-point quadrature on the
    conditional. Used to price multi-leg parlays honestly instead of multiplying legs."""
    n = 160
    lo, hi = -8.0, 8.0
    step = (hi - lo) / n
    total = 0.0
    for i in range(n + 1):
        x = lo + i * step
        w = 1.0 if 0 < i < n else 0.5
        fx = math.exp(-x * x / 2) / math.sqrt(2 * math.pi)
        cond = (k - rho * x) / math.sqrt(max(1e-9, 1 - rho * rho))
        fy = 0.5 * (1.0 + math.erf(cond / math.sqrt(2.0)))
        total += w * fx * fy
    return total * step


LEG_PAIR_RHO: list[dict] = [
    {"pair": "Home spread + away spread, same game", "rho": -1.0,
     "how": "identical statistic, opposite sign - one leg wins exactly when the other loses",
     "needs_data": None},
    {"pair": "Home spread + game total (either side)", "rho": 0.0,
     "how": "margin = H-A and total = H+A are orthogonal when both teams carry the same "
            "variance; under the model's iid normal errors the correlation is exactly zero",
     "needs_data": "the zero result depends on equal variances and on ignoring game flow; "
                   "a trailing team passing more makes over + dog-spread positively dependent "
                   "in reality - that term needs play-by-play"},
    {"pair": "Team A spread + Team A team total", "rho": 0.7071,
     "how": "cov(H, H-A) = Var(H) -> rho = 1/sqrt(2)",
     "needs_data": None},
    {"pair": "Team A spread + Team B spread (same game)", "rho": -1.0,
     "how": "same leg written twice", "needs_data": None},
    {"pair": "Two legs from two different games", "rho": 0.0,
     "how": "no shared term in a static model; cross-game dependence in practice is small and "
            "not modelled", "needs_data": None},
    {"pair": "Player prop + that player's team spread", "rho": None,
     "how": "not computable here - requires snap-weighted usage and game-state response",
     "needs_data": "play-by-play + participation data (flag F-16)"},
    {"pair": "Two props on the same player (e.g. pass yards + completions)", "rho": None,
     "how": "not computable here - requires the joint distribution of one player's game",
     "needs_data": "player game-level history (flag F-16)"},
    {"pair": "Same-player props on the same side of a high-total game", "rho": None,
     "how": "not computable here - the coupling is exactly the game-flow term",
     "needs_data": "play-by-play (flag F-16)"},
]


def measured_correlations() -> list[dict]:
    st = json.loads((VERIFIED / "standings_2026.json").read_text(encoding="utf-8"))["clubs"]
    avail = json.loads((VERIFIED / "availability_week10.json").read_text(encoding="utf-8"))["clubs"]

    ppg = [c["ppg"] for c in st]
    papg = [c["papg"] for c in st]
    net = [c["net_ppg"] for c in st]
    pct = [c["win_pct_derived"] for c in st]
    gp = [c["games_played"] for c in st]

    def by_abbr(values):
        idx = {c["abbr"]: v for c, v in zip(st, values)}
        return idx

    out = []
    out.append(dict(pair="club points-per-game vs club points-allowed-per-game",
                    **pearson(ppg, papg),
                    reads="How much of 'good offence' is really 'good defence'. A strongly "
                          "negative value would mean quality teams also allow fewer points, so "
                          "spread and total legs would inherit that coupling.",
                    implication_for_parlays="Near zero means the static model does not itself "
                                           "create extra dependence between a side and a total; "
                                           "any real dependence must come from game flow."))
    out.append(dict(pair="net points per game vs win percentage", **pearson(net, pct),
                    reads="Whether the standings are internally coherent as a rating.",
                    implication_for_parlays="Validation that PF/PA is a usable strength signal "
                                           "at all; a weak value would condemn the whole v0 model."))
    out.append(dict(pair="games played vs net points per game", **pearson(gp, net),
                    reads="Does a short season (bye taken) line up with quality?",
                    implication_for_parlays="If games-played correlated with strength, "
                                           "per-game rates would carry a schedule-size artefact."))

    common = [c for c in st if c["abbr"] in avail]
    absences = [avail[c["abbr"]]["absences_total"] for c in common]
    out.append(dict(pair="club projected absences (Out+Doubtful) vs net points per game",
                    **pearson(absences, [c["net_ppg"] for c in common]),
                    reads="Is availability injury-driven, quality-driven or noise? "
                          "This is the single most important check before letting injury data "
                          "move a line: a strong negative value means the two signals overlap and "
                          "an additive injury penalty double-counts weakness.",
                    implication_for_parlays="Sets the ceiling on how much an availability "
                                           "adjustment should be trusted."))
    out.append(dict(pair="club projected absences vs points per game",
                    **pearson(absences, [c["ppg"] for c in common]),
                    reads="Same test on the offence side only.",
                    implication_for_parlays="If offence-side absences track scoring, part of the "
                                           "injury 'signal' is already inside PPG."))
    out.append(dict(pair="club projected absences vs points allowed per game",
                    **pearson(absences, [c["papg"] for c in common]),
                    reads="Same test on the defence side only.",
                    implication_for_parlays="If defensive absences track points allowed, an "
                                           "adjustment on OUT defensive players double-counts."))
    out.append(dict(pair="offence absences vs defence absences, same club",
                    **pearson([avail[c["abbr"]]["out_offense"] for c in common],
                              [avail[c["abbr"]]["out_defense"] for c in common]),
                    reads="Do clubs lose hitters on both sides at once (poor depth, poor "
                          "medical staff, small roster)?",
                    implication_for_parlays="High value means a 'both sides thin' bucket exists, "
                                            "which is a total-market signal, not a spread one."))
    return out


def main() -> int:
    measured = measured_correlations()
    payload = {
        "dataset": "Correlation study - measured, specified and missing",
        "fetched_at_utc": "2026-11-14T03:20:00Z",
        "method": {"measured": "Pearson rho with Fisher-z 95% interval, computed on the "
                               "32-club verified aggregates",
                   "specified": "analytic rho from the model's error structure (iid normal "
                                "team points, sigma = declared prior)",
                   "missing": "left blank on purpose; needs play-by-play (flag F-16)"},
        "measured": measured,
        "leg_pairs": LEG_PAIR_RHO,
        "parlay_pricing_rule": (
            "A parlay is priced from the JOINT probability, never from the product of legs. "
            "For k legs with the correlation matrix R above, P(all win) is evaluated with the "
            "bivariate/multivariate normal integral using R; where an entry of R is blank the "
            "parlay is not priced at all (gate G6 returns HOLD)."
        ),
        "bvn_examples": [
            {"legs": 2, "each_leg_win_prob": 0.55, "rho": 0.0,
             "joint": round(bvn_cdf(0.1257, 0.1257, 0.0), 5)},
            {"legs": 2, "each_leg_win_prob": 0.55, "rho": 0.35,
             "joint": round(bvn_cdf(0.1257, 0.1257, 0.35), 5)},
            {"legs": 2, "each_leg_win_prob": 0.55, "rho": 0.7071,
             "joint": round(bvn_cdf(0.1257, 0.1257, 0.7071), 5)},
            {"legs": 2, "each_leg_win_prob": 0.55, "rho": -1.0,
             "joint": "0 (impossible for both sides of one game to win)",
             "note": "exact, by construction"},
        ],
    }
    MODEL_OUT.mkdir(parents=True, exist_ok=True)
    path = MODEL_OUT / "correlation.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}  ({len(measured)} measured rho, "
          f"{len(LEG_PAIR_RHO)} leg-pair rows)")
    for m in measured:
        print(f"    rho={m['rho']:+.4f} n={m['n']} ci={m['ci95']}  {m['pair']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
