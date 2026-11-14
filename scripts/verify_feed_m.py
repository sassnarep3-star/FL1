#!/usr/bin/env python3
"""
verify_feed_m.py — session M: line-by-line verification of the verified results feed.

Compares THREE independent captures of the 2026 season's finals:

  1. raw/official-finals-2026.tsv   row-level official (nfl.com weekly schedule
     pages, fetched 2026-11-14) — 137 rows, this session's transcription.
  2. data/results.tsv               session 3f677e8a's capture (137 rows),
     previously proven against the official standings (records + PF + PA).
  3. data/schedule2026-d.csv        session D's 272-row slate; the played rows
     carry scores reconciled V1/V2/V4 to official sources.

Every game must appear in all three with identical scores and identical
team pairs. Any mismatch fails the check (exit 1). Nothing is inferred.

Run:  python3 scripts/verify_feed_m.py
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "official-finals-2026.tsv")
RESULTS = os.path.join(ROOT, "data", "results.tsv")
SCHED = os.path.join(ROOT, "data", "schedule2026-d.csv")


def load_official():
    rows = []
    with open(RAW, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            week, date, away, ap, home, hp, url, verified = line.rstrip("\n").split("\t")
            rows.append({
                "week": int(week), "date": date, "away": away, "ap": int(ap),
                "home": home, "hp": int(hp), "url": url, "verified": verified,
            })
    return rows


def load_results():
    rows = []
    with open(RESULTS, encoding="utf-8") as fh:
        for raw in csv.reader(fh, delimiter="\t"):
            if not raw or all(c.strip() == "" for c in raw):
                continue
            week, date, away, ap, home, hp = (raw + [""] * 6)[:6]
            rows.append({
                "week": int(week), "date": date, "away": away, "ap": int(ap),
                "home": home, "hp": int(hp),
            })
    return rows


def load_schedule():
    rows = []
    with open(SCHED, newline="", encoding="utf-8") as fh:
        for g in csv.DictReader(fh):
            if g["played"] != "yes":
                continue
            rows.append({
                "week": int(g["week"]), "date": g["date"],
                "away": g["away_team"], "ap": int(g["away_score"]),
                "home": g["home_team"], "hp": int(g["home_score"]),
            })
    return rows


def key(r):
    return (r["week"], r["away"], r["home"])


def main() -> int:
    off = load_official()
    res = load_results()
    sch = load_schedule()
    problems = []

    print("rows: official=%d results.tsv=%d schedule2026-d(played)=%d"
          % (len(off), len(res), len(sch)))

    maps = {}
    for name, rows in (("official", off), ("results.tsv", res), ("schedule2026-d", sch)):
        m = {}
        for r in rows:
            k = key(r)
            if k in m:
                problems.append("%s: duplicate game %s" % (name, k))
            m[k] = r
        maps[name] = m

    keys = set().union(*[set(m) for m in maps.values()])
    for k in sorted(keys):
        present = {n: maps[n].get(k) for n in maps}
        missing = [n for n, r in present.items() if r is None]
        if missing:
            problems.append("game %s missing from: %s" % (k, ", ".join(missing)))
            continue
        scores = {n: (present[n]["ap"], present[n]["hp"]) for n in present}
        if len(set(scores.values())) != 1:
            problems.append("game %s score mismatch: %s" % (k, scores))
        dates = {present[n]["date"] for n in present if present[n].get("date")}
        if len(dates) > 1:
            problems.append("game %s date mismatch: %s" % (k, sorted(dates)))

    if problems:
        for p in problems:
            print("FAIL:", p)
        print("verify_feed_m: %d problem(s)" % len(problems))
        return 1
    print("verify_feed_m: PASS — %d games, all three captures agree field for field"
          % len(keys))
    return 0


if __name__ == "__main__":
    sys.exit(main())
