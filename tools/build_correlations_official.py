#!/usr/bin/env python3
"""build_correlations_official.py — correlation values computed ONLY from
officially sourced numbers, with n published beside every value.

The brief: "Compute correlations only from officially sourced numbers and
publish n with each value." So this script computes exclusively from captures
whose source record is Official (league): the Week 10 injury report (S01),
the 2026 standings (S02/S03), and the results reconciled against them.
Everything else — market-leg correlations from third-party prices, player-prop
correlations from third-party player stats — is a BLANK row with its n set to
the number of usable joint observations (0 here) and a note explaining what
would unblock it. The third-party estimates that exist elsewhere in the repo
are deliberately NOT promoted into this register (open item F11).

Every value carries:
    n        joint observations actually used
    ci95     paired bootstrap interval (seed 20261114, 2000 resamples)
    method   Pearson on raw values, or Spearman on mid-ranks (ties averaged)
    sources  the official source record ids behind the two input columns

Run:  python3 tools/build_correlations_official.py
"""

import csv
import os
import random
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "correlations_official.csv")

SEED = 20261114
N_BOOT = 2000

PRACTICE_ORD = {"DNP": 2, "LIMITED": 1, "FULL": 0}
GAME_ORD = {"Out": 3, "Doubtful": 2, "Questionable": 1}


# ---------------------------------------------------------------- statistics
def _mean(xs):
    return sum(xs) / len(xs)


def _pearson(xs, ys):
    mx, my = _mean(xs), _mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _spearman(xs, ys):
    return _pearson(_ranks(xs), _ranks(ys))


def _boot_ci(xs, ys, fn, seed=SEED, n_boot=N_BOOT):
    rng = random.Random(seed)
    n = len(xs)
    stats = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        v = fn([xs[i] for i in idx], [ys[i] for i in idx])
        if v is not None:
            stats.append(v)
    if not stats:
        return None, None
    stats.sort()
    lo = stats[int(0.025 * len(stats))]
    hi = stats[min(int(0.975 * len(stats)), len(stats) - 1)]
    return round(lo, 5), round(hi, 5)


def measure(label, xs, ys, fn, method, inputs, source_ids, source_urls, note=""):
    n = len(xs)
    if n == 0:
        return {"id": "", "label": label, "inputs": inputs, "method": method,
                "n": 0, "value": "", "ci95_low": "", "ci95_high": "",
                "status": "BLOCKED", "sources": source_ids,
                "source_urls": source_urls,
                "note": note or "no officially sourced joint observations"}
    v = fn(xs, ys)
    lo, hi = _boot_ci(xs, ys, fn) if n >= 2 else (None, None)
    return {"id": "", "label": label, "inputs": inputs, "method": method,
            "n": n,
            "value": "" if v is None else round(v, 5),
            "ci95_low": "" if lo is None else lo,
            "ci95_high": "" if hi is None else hi,
            "status": "MEASURED" if v is not None else "BLOCKED",
            "sources": source_ids, "source_urls": source_urls, "note": note}


def load_tsv(name):
    out = []
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        for raw in csv.reader(fh, delimiter="\t"):
            if raw and not all(c.strip() == "" for c in raw):
                out.append(raw)
    return out


def main():
    rows = []

    # ---- CO-01: practice participation vs game status (official report) ----
    inj = load_tsv("injuries.tsv")
    xs, ys = [], []
    for r in inj:
        r += [""] * (6 - len(r))
        practice, game = r[4].strip(), r[5].strip()
        if practice in PRACTICE_ORD and game in GAME_ORD:
            xs.append(PRACTICE_ORD[practice])
            ys.append(GAME_ORD[game])
    rows.append(measure(
        "CO-01 practice severity vs game-status severity (official injury report)",
        xs, ys, _spearman, "Spearman (mid-ranks)",
        "practice participation ordinal (DNP>Limited>Full) vs game-status ordinal "
        "(Out>Doubtful>Questionable) on the same player row",
        "S01", "https://www.nfl.com/injuries/",
        "computed only from the 2026-11-14 official report capture; a single week, "
        "so it is a within-snapshot association, not a season-long parameter"))

    # ---- CO-02 / CO-03: official standings ----
    std = load_tsv("standings.tsv")
    pf, pa, pct = [], [], []
    for r in std:
        r += [""] * (17 - len(r))
        pf.append(float(r[5])); pa.append(float(r[6])); pct.append(float(r[4]))
    rows.append(measure(
        "CO-02 points for vs points against (official standings, 32 clubs)",
        pf, pa, _pearson, "Pearson",
        "PF vs PA across all 32 clubs at the Week 10 standings snapshot",
        "S02;S03", "https://www.nfl.com/standings/league/2026/REG", ""))
    rows.append(measure(
        "CO-03 points for vs win percentage (official standings, 32 clubs)",
        pf, pct, _pearson, "Pearson",
        "PF vs winning pct across all 32 clubs",
        "S02;S03", "https://www.nfl.com/standings/league/2026/REG",
        "sanity-level association; published because the brief says every "
        "correlation value carries its n and its source"))

    # ---- CO-04: margin vs total in verified results ----
    res = load_tsv("results.tsv")
    margin, total = [], []
    for r in res:
        r += [""] * (6 - len(r))
        a, h = int(r[3]), int(r[5])
        margin.append(h - a)
        total.append(h + a)
    rows.append(measure(
        "CO-04 home margin vs total points (verified 2026 results)",
        margin, total, _pearson, "Pearson",
        "(home-away) margin vs combined points across every verified 2026 game",
        "S03;S04", "https://www.nfl.com/standings/league/2026/REG",
        "scores reconciled 32/32 against the official standings (see "
        "verification.html); this is a scoring-context correlation, NOT a "
        "betting-market leg correlation"))

    # ---- CO-05: week-10 availability vs week-10 outcome — BLOCKED ----
    rows.append(measure(
        "CO-05 team unavailable count vs scoring margin (Week 10 2026)",
        [], [], _pearson, "Pearson (planned)",
        "per-club count of Out/Doubtful/Questionable (official report) vs that "
        "club's scoring margin in the same week",
        "S01;S04", "https://www.nfl.com/injuries/",
        "BLOCKED: only the Thursday game of Week 10 is settled at capture time; "
        "n=0 joint observations exist. The estimate becomes computable the week "
        "settles — it is NOT estimated from other weeks and presented as Week 10"))

    # ---- CO-06: same-game cover vs over — BLOCKED by the official-only rule ----
    rows.append(measure(
        "CO-06 home cover vs over (same-game parlay leg correlation)",
        [], [], _pearson, "phi coefficient (planned)",
        "joint outcome of (home covers spread) and (game goes over) across games",
        "", "",
        "BLOCKED: computing this requires spread and total prices, and no "
        "official source publishes NFL betting lines (flag F20). Third-party "
        "estimates exist in docs/computed/ but are excluded here by rule "
        "'correlations only from officially sourced numbers' (open item F11)"))

    # ---- CO-07: player-prop pairs — BLOCKED by the same rule ----
    rows.append(measure(
        "CO-07 player-prop pair correlations (e.g. QB pass yds x WR rec yds)",
        [], [], _pearson, "Pearson (planned)",
        "player-level joint game logs",
        "", "",
        "BLOCKED: player-level game logs are third-party (nflverse), not "
        "official. Published-with-n third-party estimates live on "
        "prop-correlations.html and are deliberately not promoted here (F11)"))

    fields = ["id", "label", "inputs", "method", "n", "value",
              "ci95_low", "ci95_high", "status", "sources", "source_urls", "note"]
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for i, r in enumerate(rows, start=1):
            r["id"] = "CO-%02d" % i
            w.writerow({k: r.get(k, "") for k in fields})

    for r in rows:
        print(f"  {r['id']}  n={r['n']:<5} value={r['value']!s:<9} {r['label'][:60]}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
