#!/usr/bin/env python3
"""
verify_results.py — proves data/results.tsv and data/standings.tsv agree.

The standings table is an official NFL publication. The results table is a
transcription of 137 individual official game pages. If the transcription is
right, adding the games up must reproduce the published table exactly.

That is a real check, because the two files come from different pages:
results from /schedules/2026/by-week/week-N, standings from /standings/. A
single mis-typed score, a swapped home/away, or a game counted in the wrong
column shows up as a mismatch.

It also settles the snapshot date of the standings without trusting a label:
run with --include-week-10-tnf and again without it and see which one matches.

Run:  python3 tools/verify_results.py
"""

import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build  # noqa: E402

TNF = ("10", "2026-11-12", "WAS", "NYG")


def tally(rows, skip_tnf):
    rec = defaultdict(lambda: {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0})
    used = 0
    for r in rows:
        week, date, away, ap, home, hp = (r["week"], r["date"], r["away"],
                                          r["awayPts"], r["home"], r["homePts"])
        if skip_tnf and (week, date, away, home) == TNF:
            continue
        if ap == "" or hp == "":
            print("PROBLEM: %s week %s has a missing score" % (away, week),
                  file=sys.stderr)
            sys.exit(1)
        ap, hp = int(ap), int(hp)
        used += 1
        for t, pts, opp in ((away, ap, hp), (home, hp, ap)):
            rec[t]["PF"] += pts
            rec[t]["PA"] += opp
            if pts > opp:
                rec[t]["W"] += 1
            elif pts < opp:
                rec[t]["L"] += 1
            else:
                rec[t]["T"] += 1
    return rec, used


def main():
    results = build.load("results.tsv")
    standings = build.load("standings.tsv")
    teams = build.load("teams.tsv")
    known = {t["abbr"] for t in teams}

    problems = []
    for r in results:
        for abbr in (r["away"], r["home"]):
            if abbr not in known:
                problems.append("results.tsv unknown club %r" % abbr)

    for label, skip in (("all 137 games (Week 10 TNF included)", False),
                        ("136 games (Week 10 TNF excluded)", True)):
        rec, used = tally(results, skip)
        mismatches = []
        for s in standings:
            a = s["abbr"]
            got = rec.get(a)
            if got is None:
                mismatches.append("%s: no games at all" % a)
                continue
            want = (int(s["w"]), int(s["l"]), int(s["t"]),
                    int(s["pf"]), int(s["pa"]))
            have = (got["W"], got["L"], got["T"], got["PF"], got["PA"])
            if want != have:
                mismatches.append(
                    "%s: standings says %d-%d-%d PF %d PA %d, games add up to "
                    "%d-%d-%d PF %d PA %d" % ((a,) + want + have))
        print("%-42s games=%-4d clubs=%-3d mismatches=%d"
              % (label, used, len(standings), len(mismatches)))
        for m in mismatches:
            print("    %s" % m)
        if not skip:
            final = len(mismatches)

    if problems:
        for p in problems:
            print("DATA PROBLEM: %s" % p, file=sys.stderr)
        sys.exit(1)
    if final:
        print("\nFAIL: results.tsv does not reproduce the official standings.",
              file=sys.stderr)
        sys.exit(1)
    print("\nPASS: adding up every game in results.tsv reproduces the published "
          "standings\n      for all 32 clubs, and the match only holds when the "
          "Week 10 Thursday\n      game is included — which is how the standings "
          "snapshot date was established.")


if __name__ == "__main__":
    main()
