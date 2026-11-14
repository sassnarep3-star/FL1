#!/usr/bin/env python3
"""
build_results_feed_m.py — session M: build the verified results feed.

Inputs  raw/official-finals-2026.tsv   row-level official transcription (137 rows)
        data/schedule2026-d.csv        slate metadata (game_id, venue, kickoff)
        data/results.tsv               independent capture (cross-checked)
Output  data/results_feed.csv          settlement-ready feed, one row per played
                                       game, every row carries its official game
                                       URL and the week-page source id.

Verification: scripts/verify_feed_m.py must PASS before this script writes
anything (it re-runs the three-way comparison itself).

Run:  python3 scripts/build_results_feed_m.py
"""
import csv
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "official-finals-2026.tsv")
SCHED = os.path.join(ROOT, "data", "schedule2026-d.csv")
OUT = os.path.join(ROOT, "data", "results_feed.csv")

# week -> source id in data/sources.tsv (weeks 1-9 = S61..S69, week 10 = S49)
WEEK_SOURCE = {w: "S%02d" % (60 + w) for w in range(1, 10)}
WEEK_SOURCE[10] = "S49"
WEEK_URL = {w: "https://www.nfl.com/schedules/2026/by-week/week-%d" % w
            for w in range(1, 11)}

FIELDS = [
    "game_id", "season", "week", "game_date", "kickoff_et",
    "away_team", "away_score", "home_team", "home_score",
    "overtime", "stadium", "roof",
    "verified", "verification_basis", "official_game_url",
    "official_week_url", "source_ids",
]


def main() -> int:
    rc = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "verify_feed_m.py")])
    if rc.returncode != 0:
        print("build aborted: verify_feed_m.py failed", file=sys.stderr)
        return 1

    sched = {}
    with open(SCHED, newline="", encoding="utf-8") as fh:
        for g in csv.DictReader(fh):
            sched[(int(g["week"]), g["away_team"], g["home_team"])] = g

    rows = []
    with open(RAW, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            week, date, away, ap, home, hp, url, verified = line.rstrip("\n").split("\t")
            week = int(week)
            meta = sched[(week, away, home)]
            rows.append({
                "game_id": meta["game_id"],
                "season": "2026",
                "week": str(week),
                "game_date": date,
                "kickoff_et": meta["kickoff_et"],
                "away_team": away,
                "away_score": ap,
                "home_team": home,
                "home_score": hp,
                "overtime": "yes" if meta["overtime"] == "yes" else "",
                "stadium": meta["stadium"],
                "roof": meta["roof"],
                "verified": verified,
                "verification_basis": (
                    "official nfl.com week-page FINAL line, transcribed to "
                    "raw/official-finals-2026.tsv; three-way field-for-field "
                    "agreement with data/results.tsv and data/schedule2026-d.csv "
                    "(scripts/verify_feed_m.py PASS)"),
                "official_game_url": url,
                "official_week_url": WEEK_URL[week],
                "source_ids": WEEK_SOURCE[week],
            })

    rows.sort(key=lambda r: (int(r["week"]), r["game_date"], r["away_team"]))
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print("wrote data/results_feed.csv (%d rows)" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
