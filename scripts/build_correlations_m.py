#!/usr/bin/env python3
"""
build_correlations_m.py — session M: correlations computed ONLY from officially
sourced numbers, every value published WITH its n.

Inputs: data/results_feed.csv — 137 games of 2026 regular-season final scores,
each row-level verified against official nfl.com week pages (S49-S58) and
cross-checked three ways (scripts/verify_feed_m.py).

The brief's rule: "Compute correlations only from officially sourced numbers
and publish n with each value." Nothing from third-party feeds enters this
table. The register values in data/correlations.json (C-01..C-15) stay blank
under the same rule (flag F-11 pending); player-prop correlations
(prop-correlations.html) are computed from a third-party archive and are
published separately, flagged (F17).

Method: Pearson product-moment correlation. Each row carries n explicitly.

Output: data/correlations-official.csv

Run:  python3 scripts/build_correlations_m.py
"""
from __future__ import annotations

import csv
import math
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = os.path.join(ROOT, "data", "results_feed.csv")
OUT = os.path.join(ROOT, "data", "correlations-official.csv")

FIELDS = ["corr_id", "x", "y", "method", "n", "r", "se_r", "window",
          "source_ids", "inputs", "note"]


def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        raise ValueError("zero variance")
    r = sxy / math.sqrt(sxx * syy)
    se = math.sqrt((1 - r * r) / (n - 2)) if n > 2 else None
    return r, se


def main() -> int:
    games = []
    with open(FEED, newline="", encoding="utf-8") as fh:
        for g in csv.DictReader(fh):
            games.append({
                "week": int(g["week"]), "date": g["game_date"],
                "away": g["away_team"], "ap": int(g["away_score"]),
                "home": g["home_team"], "hp": int(g["home_score"]),
                "src": g["source_ids"],
            })
    games.sort(key=lambda g: (g["week"], g["date"], g["away"]))
    all_src = sorted({g["src"] for g in games}, key=lambda s: int(s[1:]))
    src_ids = ",".join(all_src)

    rows = []

    # C-O1: same-game scoring co-movement (home points vs away points).
    xs = [g["ap"] for g in games]
    ys = [g["hp"] for g in games]
    r, se = pearson(xs, ys)
    rows.append({
        "corr_id": "C-O1", "x": "away points, game", "y": "home points, game",
        "method": "Pearson", "n": len(games), "r": round(r, 4),
        "se_r": round(se, 4), "window": "2026 W1-W10 (played games)",
        "source_ids": src_ids,
        "inputs": "data/results_feed.csv (row-level official)",
        "note": "game-level scoring co-movement; input for single-game parlay "
                "leg dependence once prices exist",
    })

    # C-O2 / C-O3: week-to-week autocorrelation per club (consecutive team games).
    seq = defaultdict(list)
    for g in games:
        seq[g["away"]].append((g["week"], g["ap"], g["hp"]))
        seq[g["home"]].append((g["week"], g["hp"], g["ap"]))
    for t in seq:
        seq[t].sort()

    xp, yp = [], []
    xd, yd = [], []
    for t, lst in seq.items():
        for i in range(1, len(lst)):
            xp.append(lst[i - 1][1])      # points scored, previous game
            yp.append(lst[i][1])          # points scored, this game
            xd.append(lst[i - 1][2])      # points allowed, previous game
            yd.append(lst[i][2])          # points allowed, this game

    r2, se2 = pearson(xp, yp)
    rows.append({
        "corr_id": "C-O2", "x": "team points scored, game N-1",
        "y": "team points scored, game N", "method": "Pearson", "n": len(xp),
        "r": round(r2, 4), "se_r": round(se2, 4),
        "window": "2026 W1-W10 (consecutive club games, bye weeks skipped)",
        "source_ids": src_ids,
        "inputs": "data/results_feed.csv (row-level official)",
        "note": "scoring form persistence; the reversion question for totals "
                "and team-total markets",
    })

    r3, se3 = pearson(xd, yd)
    rows.append({
        "corr_id": "C-O3", "x": "team points allowed, game N-1",
        "y": "team points allowed, game N", "method": "Pearson", "n": len(xd),
        "r": round(r3, 4), "se_r": round(se3, 4),
        "window": "2026 W1-W10 (consecutive club games, bye weeks skipped)",
        "source_ids": src_ids,
        "inputs": "data/results_feed.csv (row-level official)",
        "note": "defensive form persistence; input for opponent-prop and "
                "team-total signals (SIG-05 family)",
    })

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print("%s  r=%+.4f  n=%d  (%s)" % (r["corr_id"], r["r"], r["n"], r["y"]))
    print("wrote data/correlations-official.csv (%d rows)" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
