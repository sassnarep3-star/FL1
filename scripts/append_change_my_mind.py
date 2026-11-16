#!/usr/bin/env python3
"""Append the two-sided "what would change our mind" field to every strategy
entry in data/strategies.json (brief requirement N02).

Two-sided: each entry gains
  raises_confidence  — evidence that would make us MORE confident in the hypothesis
  lowers_confidence  — evidence that would make us LESS confident
Both reference data that exists today, or name the missing data and the open
question that owns obtaining it. Nothing is asserted as measured that is not.

The script refuses to run twice (idempotence guard) and fails if any strategy
id is missing from the curated dict.

Run:  python3 scripts/append_change_my_mind.py
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "strategies.json")

FIELDS = {
    "ST01": {
        "raises_confidence":
            "Using the official results feed (S52, 137 settled games, extended weekly), "
            "backtest both predictors walk-forward: if margin-based picks beat "
            "record-based picks at equal sample with a confidence interval excluding "
            "zero, the baseline earns its place.",
        "lowers_confidence":
            "If the walk-forward gap between the two estimators stays inside its "
            "confidence interval across the whole 2026 season, margin adds no usable "
            "information at this sample size and the baseline is downgraded to the "
            "record model.",
    },
    "ST02": {
        "raises_confidence":
            "A price source (Q21/Q30) letting us compare the market move on games with "
            "an official Out designation against the same games' fair line, with the "
            "replacement string published per slot (replacement-depth register); a "
            "persistent, correctly-signed residual would support the hypothesis.",
        "lowers_confidence":
            "If games with and without an Out starter show no residual difference once "
            "opponent quality is controlled for, or if the derived depth rank layer "
            "(flagged unofficial, F10) proves unstable week to week, the signal has no "
            "evidence beyond the level effect already public.",
    },
    "ST03": {
        "raises_confidence":
            "The official-register correlation C-A3 (rest edge vs home margin, n=121, "
            "r=0.426, CI 0.268..0.562) holding or strengthening as weekly official "
            "captures grow n, with the travel component separable from rest.",
        "lowers_confidence":
            "If C-A3's interval widens to include zero as n grows, or if adding the "
            "international/short-week fixtures reverses the sign, the asymmetry is a "
            "small-sample artefact and the strategy is dropped.",
    },
    "ST04": {
        "raises_confidence":
            "An official roof/surface registry (the brief's stadium-overlay requirement) "
            "joined to NWS point forecasts and to official game totals: a wind-conditioned "
            "total estimator that beats the unconditioned one out-of-sample on the "
            "official feed.",
        "lowers_confidence":
            "If the roof registry cannot be verified officially (determinations are "
            "published 90 minutes before kickoff, S-note pending), the outdoor "
            "determination stays inferred and the feature is dropped rather than "
            "guessed; a fitted model that only helps in-sample would also sink it.",
    },
    "ST05": {
        "raises_confidence":
            "A directly validated joint probability for a specific two-leg pairing "
            "(the joint-evidence gate) plus the operator's void/push rules, both "
            "available before any combo is ranked.",
        "lowers_confidence":
            "If the joint dataset cannot be built (pairing observed too rarely), the "
            "gate stays closed permanently for that combo; multiplying marginals "
            "remains invalid under dependence and no workaround is permitted.",
    },
    "ST06": {
        "raises_confidence":
            "A player-level official or licensed log (snap share, target/carry share — "
            "Q17) large enough to estimate the same-script joint frequency for at "
            "least one pairing with usable uncertainty.",
        "lowers_confidence":
            "If only third-party estimates exist (F17), the strategy stays BLOCKED "
            "behind the joint-evidence gate; a marginal-only build would fail G-12 "
            "provenance and is not attempted.",
    },
}


def main():
    with open(PATH, encoding="utf-8") as fh:
        strategies = json.load(fh)
    for s in strategies:
        if "raises_confidence" in s or "lowers_confidence" in s:
            raise SystemExit("FAIL: %s already carries the field — refusing to "
                             "double-apply" % s.get("id"))
    missing = [s["id"] for s in strategies if s["id"] not in FIELDS]
    if missing:
        raise SystemExit("FAIL: no curated field for %s" % missing)
    for s in strategies:
        s["raises_confidence"] = FIELDS[s["id"]]["raises_confidence"]
        s["lowers_confidence"] = FIELDS[s["id"]]["lowers_confidence"]
    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump(strategies, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("change-our-mind fields appended to %d strategy entries" % len(strategies))
    return 0


if __name__ == "__main__":
    sys.exit(main())
