#!/usr/bin/env python3
"""Build data/ablations.json - injury/personnel ablations instead of fixed penalties.

DESIGN (fixed before the holdout was scored - see the brief item and G-18)
------
Identical model shapes differing only in the availability features:
  WITHOUT: intercept + prior-3-game point-margin difference (a naive strength proxy)
  WITH:    the same, plus four 0/1 indicators for each side's QB-deficiency class
           (2nd different starter / 3rd-or-later different starter, per
           data/depth_deficiency.csv, derived from the recorded starting QB identity)
Splits are chronological, never random:
  train      1999-2019
  validation 2020-2021  (stability reading only - nothing is chosen on it)
  holdout    2022-2025  (scored exactly once, after both models were frozen)
2026 games are excluded from every split: the season is in progress, so any use of
it would be neither train nor clean holdout.
The holdout difference (MAE with - MAE without) is reported with a paired bootstrap
95% CI over per-game absolute errors, and each fitted availability coefficient is
published with its own train-only bootstrap CI. No fixed penalty is assumed anywhere.

PROVENANCE: data/raw/games.csv (nflverse feed, source S47, third-party snapshot) and
data/depth_deficiency.csv (derived from the same feed's recorded starters). No output
here is an official NFL publication; every row carries that label. Deterministic seeds.
"""
from __future__ import annotations

import csv
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.ablation import ablate, build_rows, load_team_week_qb, rolling_prior_margin  # noqa: E402

TRAIN = {str(s) for s in range(1999, 2020)}
VALIDATION = {"2020", "2021"}
HOLDOUT = {"2022", "2023", "2024", "2025"}
TARGETS = ("margin", "total")


def main() -> None:
    games = list(csv.DictReader(open(ROOT / "data" / "raw" / "games.csv", encoding="utf-8")))
    qb = load_team_week_qb(csv.DictReader(
        open(ROOT / "data" / "depth_deficiency.csv", encoding="utf-8")))
    prior = rolling_prior_margin(games)

    played = [g for g in games
              if g.get("game_type") == "REG" and g.get("home_score") and g.get("away_score")]
    ablations = {}
    for target in TARGETS:
        rows = build_rows(games, qb, prior, target)
        seasons_used = {r["season"] for r in rows}
        res = ablate(rows, TRAIN, VALIDATION, HOLDOUT, target)
        # rows outside all three windows (2026) are held out of the study entirely
        res["rows_available"] = len(rows)
        res["rows_in_study"] = (res["n_train"] + res["n_validation"] + res["n_holdout"])
        res["seasons_with_feature"] = sorted(seasons_used)
        ablations[target] = res

    doc = {
        "id": "ablations",
        "title": "Injury/personnel ablations instead of fixed penalties",
        "updated": "2026-11-16",
        "requirement": ("Add injury and personnel ablations instead of fixed penalties; compare "
                        "identical models with and without verified availability features using "
                        "chronological holdouts (brief, R-series sprint)."),
        "design": {
            "without": "intercept + prior-3-game scoring-margin difference",
            "with": "the same features + four 0/1 QB-deficiency indicators (home/away x "
                    "2nd-starter / 3rd-or-later-starter classes)",
            "splits": {"train": "1999-2019", "validation": "2020-2021 (stability reading only)",
                       "holdout": "2022-2025 (scored once, after freezing)",
                       "excluded": "2026 (season in progress; no split may absorb it)"},
            "difference_statistic": ("MAE(with) - MAE(without) on the holdout, paired by game; "
                                     "95% CI by paired bootstrap over per-game absolute errors "
                                     "(seed 20261116, 4000 resamples)"),
            "coefficient_ci": "train-only case bootstrap (1000 resamples, seed 20261117)",
            "why_not_a_fixed_penalty": ("The adjustment's SIZE is fitted from training data and "
                                        "published with an interval; whether the feature helps at "
                                        "all is decided on the holdout. A fixed penalty would "
                                        "assert the size with no uncertainty and no test."),
        },
        "provenance": {
            "games": "data/raw/games.csv - nflverse combined feed snapshot (source S47, THIRD-PARTY)",
            "qb_deficiency": "data/depth_deficiency.csv - derived from the same feed's recorded "
                             "starting QB identity vs each team's most-used starter that season "
                             "(scripts/build_availability.py); classes: primary starter / 2nd "
                             "different starter / 3rd-or-later different starter",
            "official_status": ("No output on this page is an official NFL publication. The "
                                "feature is built from recorded starters, which is evidence of "
                                "who STARTED, not of injury designations; the official-only "
                                "correlation register (correlation-register.html) is separate "
                                "and unaffected."),
        },
        "reading_guide": ("mae_diff < 0 means the availability feature REDUCED holdout error. "
                          "ci_contains_zero = true means the data cannot distinguish the two "
                          "shapes - the feature stays OUT of any published model rather than "
                          "being waved in."),
        "ablations": ablations,
    }
    out = ROOT / "data" / "ablations.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    for t, r in ablations.items():
        d = r["holdout_difference"]
        print("%s: n_holdout=%d  MAE %.3f -> %.3f  diff %.3f [%.3f, %.3f] contains0=%s"
              % (t, d["n_holdout"],
                 r["without_availability"]["mae_holdout"],
                 r["with_availability"]["mae_holdout"],
                 d["mae_diff"], d["ci_low"], d["ci_high"], d["ci_contains_zero"]))


if __name__ == "__main__":
    main()
