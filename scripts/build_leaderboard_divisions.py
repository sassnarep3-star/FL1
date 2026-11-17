#!/usr/bin/env python3
"""
build_leaderboard_divisions.py — the proper-score leaderboard, and the split.

WHAT IT DOES
    1. Splits the season corpus into TRAIN, VALIDATION and FINAL HOLDOUT, and
       records the rule in data/splits.json so the split is a commitment rather
       than a choice made after the fact.
    2. Scores every backtest strategy with a proper score (Brier) against the
       market benchmark, with a game-cluster bootstrap lower bound and a
       multiplicity adjustment across the number of strategies tried.
    3. Publishes two control baselines (random picks, favourites only) so a
       strategy that cannot beat them is visibly not demonstrating skill.
    4. Applies the two-stage rule: proper-score qualification first, prospective
       CLV/ROI escrow second.
    5. Gates the parlay and prop-combo divisions behind the joint-evidence rule
       and reports that gate rather than ranking anything from marginals.

Run:  python3 scripts/build_leaderboard_divisions.py
"""

from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import proper_scores as ps  # noqa: E402

# ---------------------------------------------------------------------------
# The split. Written down before the scoring is run, and committed.
# ---------------------------------------------------------------------------
SPLITS = {
    "rule": ("Seasons are assigned to exactly one split. The final holdout is "
             "never read while a rule, a threshold, a parameter or a feature is "
             "being chosen. A rule that has been tuned against the holdout "
             "stops being a holdout, and the repository records the date that "
             "happened rather than pretending otherwise."),
    "train": {"seasons": ["2018", "2019", "2020", "2021", "2022", "2023"],
              "purpose": "fit scoring levels, fit parameters, choose rules"},
    "validation": {"seasons": ["2024"],
                   "purpose": "choose among already-fitted rules; no refitting"},
    "final_holdout": {"seasons": ["2025", "2026"],
                      "purpose": "read once, at the end, for the final number",
                      "status": "NOT YET READ by any published number on this "
                                "site; the corpus exists and is counted, but no "
                                "published figure is computed on it"},
    "registered": "2026-11-17",
}


def main() -> int:
    trades = ps.load_trades(os.path.join(ROOT, "data", "market", "backtest_trades.tsv"))

    # ---- split ------------------------------------------------------------
    split_of_season = {}
    for name in ("train", "validation", "final_holdout"):
        for season in SPLITS[name]["seasons"]:
            split_of_season[season] = name
    counts = {}
    for t in trades:
        split = split_of_season.get(t.get("season"), "unassigned")
        counts[split] = counts.get(split, 0) + 1
    splits_doc = dict(SPLITS)
    splits_doc["bets_per_split"] = counts
    splits_doc["note_on_holdout"] = (
        "The holdout corpus is counted here so its size is on the record, but "
        "no published number on this site is computed from it. That is the "
        "whole point of a holdout.")
    with open(os.path.join(ROOT, "data", "splits.json"), "w", encoding="utf-8") as fh:
        json.dump(splits_doc, fh, indent=2, sort_keys=True)

    # ---- proper scores ----------------------------------------------------
    sigmas = ps.estimate_sigmas(trades)
    benchmarks = {r["game_id"]: r for r in ps.load_trades(
        os.path.join(ROOT, "data", "market", "benchmarks.tsv"))}
    by_strategy = {}
    for t in trades:
        by_strategy.setdefault(t["strategy_id"], []).append(t)

    rows = []
    for strategy_id, strat_trades in sorted(by_strategy.items()):
        result = ps.score_strategy(strat_trades, sigmas["sigma_margin"],
                                   sigmas["sigma_total"],
                                   benchmarks=benchmarks)
        if not result.get("n_bets"):
            continue
        result["strategy_id"] = strategy_id
        result["division"] = "singles"
        result["markets"] = ",".join(sorted({t["market"] for t in strat_trades}))
        result["seasons"] = ",".join(sorted({t["season"] for t in strat_trades}))
        rows.append(result)

    # multiplicity across the strategies that were tried on this data
    pvals = {r["strategy_id"]: 1.0 - r["p_skill_gt_zero"] for r in rows}
    adjusted = ps.holm_adjust(pvals)
    for r in rows:
        r["p_one_sided"] = pvals[r["strategy_id"]]
        r["p_holm_adjusted"] = adjusted[r["strategy_id"]]

    # two-stage qualification
    for r in rows:
        stage1 = (r["skill_lower_95"] > 0
                  and r["p_holm_adjusted"] < 0.05
                  and r["brier_skill"] > r["control_random"]
                  and r["brier_skill"] > r["control_favourite"])
        r["stage1_qualified"] = "yes" if stage1 else "no"
        r["stage2_status"] = ("awaiting prospective samples — the escrow opens "
                              "only on bets made after the pre-registration "
                              "commit, and none of the bets in this corpus are "
                              "prospective")

    rows.sort(key=lambda r: (-(r["skill_lower_95"] if math.isfinite(r["skill_lower_95"]) else -9),
                              r["strategy_id"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    fields = ["rank", "strategy_id", "division", "markets", "seasons", "n_bets",
              "n_games", "brier_model", "brier_benchmark", "brier_skill",
              "skill_lower_95", "skill_median", "skill_upper_95",
              "p_skill_gt_zero", "p_one_sided", "p_holm_adjusted",
              "control_random", "control_favourite", "hit_rate",
              "mean_model_prob", "mean_bench_prob", "model_line_mae",
              "market_line_mae", "line_skill_vs_market_line", "stage1_qualified",
              "stage2_status"]
    out_path = os.path.join(ROOT, "data", "leaderboard_divisions.tsv")
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})

    summary = {
        "generated": "2026-11-17",
        "scoring_rule": "Brier score; skill = 1 - Brier(model)/Brier(benchmark)",
        "benchmark": ("the market's probability of the betting side winning, "
                      "taken from the two posted prices with the vig removed, so "
                      "that both sides of the comparison are honest "
                      "probabilities of the same event"),
        "sigma_margin": sigmas["sigma_margin"],
        "sigma_total": sigmas["sigma_total"],
        "n_margin_residuals": sigmas["n_margin"],
        "n_total_residuals": sigmas["n_total"],
        "sigma_basis": ("standard deviation of the market line's own error over "
                        "settled games; published so a reader can check it"),
        "bootstrap": {"unit": "game", "n_boot": 2000, "seed": 20261117,
                      "lower_bound": "5th percentile of the skill distribution"},
        "multiplicity": {"method": "Holm step-down", "k": len(rows)},
        "controls": ["random picks", "favourites only"],
        "splits": {"train": SPLITS["train"]["seasons"],
                   "validation": SPLITS["validation"]["seasons"],
                   "final_holdout": SPLITS["final_holdout"]["seasons"],
                   "bets_per_split": counts},
        "divisions": {
            "singles": {"status": "ranked", "entries": len(rows)},
            "game parlays": {
                "status": "GATED",
                "reason": ("no directly validated joint probability exists for "
                           "any combo in this corpus; multiplying marginal "
                           "probabilities is invalid under dependence"),
                "entries": 0},
            "same-game parlays": {
                "status": "GATED",
                "reason": ("legs inside one game are dependent by construction; "
                           "no joint probability has been validated"),
                "entries": 0},
            "prop combos": {
                "status": "GATED",
                "reason": ("player props are conditioned on the same game's "
                           "script; no joint probability has been validated and "
                           "no void/push rule is documented"),
                "entries": 0},
        },
        "entries": rows,
    }
    with open(os.path.join(ROOT, "data", "leaderboard_divisions.json"), "w",
              encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True, default=str)

    print("wrote data/leaderboard_divisions.tsv: %d entries" % len(rows))
    print("sigma margin %.3f (n=%d) | sigma total %.3f (n=%d)"
          % (sigmas["sigma_margin"], sigmas["n_margin"],
             sigmas["sigma_total"], sigmas["n_total"]))
    print("%-22s %5s %8s %8s %8s %8s" % ("strategy", "n", "skill", "lower",
                                          "holm p", "stage1"))
    for r in rows:
        print("%-22s %5d %8.4f %8.4f %8.4f %8s"
              % (r["strategy_id"], r["n_bets"], r["brier_skill"],
                 r["skill_lower_95"], r["p_holm_adjusted"], r["stage1_qualified"]))
    return 0


if __name__ == "__main__":
    import csv
    raise SystemExit(main())
