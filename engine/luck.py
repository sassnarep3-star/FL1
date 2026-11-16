"""Removal-of-luck arithmetic: how much of a run is explainable by chance alone.

PURPOSE
-------
The brief asks for a "removal of luck" panel published on the dashboard. This module
holds the arithmetic, using only the machinery in engine/stats.py:

1.  For each strategy's signal block (settled bets, hit rate, break-even hurdle):
      - the Wilson lower bound on the true hit rate,
      - the one-sided p-value that a ZERO-edge process would run at least this hot
        over the same number of settled bets (this is "the probability that luck
        alone explains the run" - it is a p-value, not a posterior),
      - the sample size that would be needed to certify the observed hit rate as a
        real edge at 80% power (engine.stats.required_sample),
      - the smallest true edge this sample could certify at 80% power
        (engine.stats.detectable_edge).
2.  The family-wise significance bar for the number of strategies searched
    (Bonferroni alpha/n and the Sidak equivalent), so a reader can see how far the
    best raw p-value is from the bar a multi-strategy search has to clear.

HONESTY NOTES (published with the panel)
----------------------------------------
- A p-value is the probability of the evidence given no edge; it is NOT the
  probability that the strategy has no edge. The panel wording keeps this distinction.
- The input dataset is the computed research layer's third-party ledger
  (data/leaderboard.csv -> data/leaderboard_signal_staking.json), flagged F39/F34.
  The panel ranks on NOTHING; it publishes uncertainty so the owner can judge.
- Where the inputs disagree with the register (e.g. the circular breakeven_hit
  column, flag F30) the panel recomputes the hurdle from the price-implied
  reference (0.52381 for standard -110) and labels the recomputation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from engine.stats import (
    detectable_edge,
    one_sided_p_above,
    proportion_se,
    required_sample,
    z_stat,
)


def strategy_luck_rows(signal_rows: Sequence[Dict[str, Any]],
                       trials: int,
                       alpha: float = 0.05,
                       power: float = 0.80) -> List[Dict[str, Any]]:
    """One luck-decomposition row per strategy signal block.

    signal_rows: entries carrying a "signal" dict with settled / hit_rate /
    hit_ci_low / reference_hurdle, as produced by the R25 signal-vs-staking build.
    """
    out: List[Dict[str, Any]] = []
    for r in signal_rows:
        sig = r.get("signal", {})
        n = sig.get("settled")
        hit = sig.get("hit_rate")
        hurdle = sig.get("reference_hurdle")
        if not (isinstance(n, (int, float)) and n > 0 and hit is not None and hurdle is not None):
            out.append({
                "strategy_id": r.get("strategy_id"),
                "status": "NO_EVALUABLE_SIGNAL",
            })
            continue
        n_i = int(n)
        se = proportion_se(float(hit), n_i)
        z = z_stat(float(hit), float(hurdle), n_i)
        p = one_sided_p_above(z)
        if float(hit) > float(hurdle):
            n_needed = required_sample(float(hurdle), float(hit), alpha=alpha, power=power)
            n_needed_out = int(n_needed) if n_needed else None
            n_ratio = round(n_needed / n_i, 1) if n_needed and n_i else None
        else:
            # the observed rate does not clear the hurdle at all - there is no edge to certify
            n_needed_out = None
            n_ratio = None
        edge_cert = detectable_edge(n_i, float(hurdle), alpha=alpha, power=power)
        out.append({
            "strategy_id": r.get("strategy_id"),
            "market": r.get("market", ""),
            "settled": n_i,
            "hit_rate": round(float(hit), 4),
            "reference_hurdle": round(float(hurdle), 5),
            "se": round(se, 4),
            "z_vs_hurdle": round(z, 3),
            "p_luck_alone_this_hot": round(p, 5),
            "n_to_certify_if_real": n_needed_out,
            "n_needed_vs_have": n_ratio,
            "certifiable_edge_at_80pct": round(edge_cert, 4),
            "status": "LUCK_NOT_EXCLUDED",
        })
    return out


def familywise(rows: Sequence[Dict[str, Any]], trials: int, alpha: float = 0.05) -> Dict[str, Any]:
    """The bar a multi-strategy search must clear, published before results are read."""
    evaluated = [r for r in rows if "p_luck_alone_this_hot" in r]
    ps = [r["p_luck_alone_this_hot"] for r in evaluated]
    bonf = alpha / trials
    sidak = 1.0 - (1.0 - alpha) ** (1.0 / trials)
    best = min(ps) if ps else None
    best_id = None
    if ps:
        best_id = min(evaluated, key=lambda r: r["p_luck_alone_this_hot"])["strategy_id"]
    return {
        "trials": trials,
        "alpha": alpha,
        "bonferroni_p_bar": round(bonf, 5),
        "sidak_p_bar": round(sidak, 5),
        "strategies_evaluated": len(evaluated),
        "best_raw_p": best,
        "best_raw_p_strategy": best_id,
        "clears_familywise_bar": bool(best is not None and best < bonf),
        "verdict": ("NO STRATEGY CLEARING" if best is None or best >= bonf
                    else "SKILL CANDIDATE - REQUIRES PRICE-SOURCED REPLAY"),
    }


def build_panel(signal_rows: Sequence[Dict[str, Any]],
                trials: int,
                controls: Sequence[Dict[str, Any]],
                alpha: float = 0.05,
                power: float = 0.80) -> Dict[str, Any]:
    """Assemble the full luck panel: per-strategy rows, the family-wise bar, controls."""
    rows = strategy_luck_rows(signal_rows, trials, alpha=alpha, power=power)
    fw = familywise(rows, trials, alpha=alpha)
    return {
        "id": "luck_panel",
        "title": "Removal of luck - what the runs look like once chance is priced in",
        "updated": "2026-11-16",
        "method": ("p_luck_alone_this_hot is the one-sided p-value that a zero-edge process "
                   "over the same number of settled bets runs at least this hot. "
                   "n_to_certify_if_real is engine.stats.required_sample at 80% power against "
                   "the -110 reference hurdle. certifiable_edge_at_80pct is "
                   "engine.stats.detectable_edge - the smallest TRUE edge this sample could "
                   "certify. A p-value is P(evidence | no edge), never P(no edge | evidence)."),
        "input_provenance": ("data/leaderboard_signal_staking.json, built from the computed "
                             "research layer's third-party ledger (data/leaderboard.csv) - "
                             "flagged F39/F34. The panel publishes uncertainty; it ranks on nothing."),
        "hurdle_note": ("Hurdle recomputed from the standard -110 break-even (0.52381); the "
                        "dataset's own breakeven_hit column is circular (flag F30) and is not used."),
        "familywise": fw,
        "rows": rows,
        "controls": list(controls),
        "headline": {
            "strategies_evaluated": fw["strategies_evaluated"],
            "proven": sum(1 for r in rows if r.get("clears_familywise_bar")),
            "verdict": fw["verdict"],
        },
    }
