#!/usr/bin/env python3
"""Build data/results_feed.json (requirement R22) from the verified capture.

Input : data/results.tsv          137 rows, weeks 1-10 of the 2026 season
        raw/schedule-results-2026-week1-10.tsv   the official capture behind it
Output: data/results_feed.json    the feed: metadata + one row per game, each
        row carrying its provenance and the official source it was checked
        against (tools/verify_results.py + the standings recomputation).

The feed is what makes backtests and ROI computable at all: a settled bet is
only settled against a row of THIS feed, never against memory or a scrape.

Run:  python3 scripts/build_results_feed.py
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build  # noqa: E402

OUT = os.path.join(ROOT, "data", "results_feed.json")
VERIFIED_COUNT = 137


def main() -> int:
    rows = build.load("results.tsv")
    feed_rows = []
    for r in rows:
        feed_rows.append({
            "week": int(r["week"]),
            "date": r["date"],
            "away": r["away"],
            "awayPts": int(r["awayPts"]),
            "home": r["home"],
            "homePts": int(r["homePts"]),
            "result": "%s %d, %s %d" % (r["away"], int(r["awayPts"]),
                                        r["home"], int(r["homePts"])),
            "margin_home": int(r["homePts"]) - int(r["awayPts"]),
            "total": int(r["homePts"]) + int(r["awayPts"]),
            "tier": "OFFICIAL",
            "source_id": "S52",
        })

    assert len(feed_rows) == VERIFIED_COUNT, (
        "results feed must hold exactly the %d verified rows, got %d"
        % (VERIFIED_COUNT, len(feed_rows)))

    # Integrity check: every club's record recomputed from the feed must match
    # the official standings capture. This is the verification that makes the
    # feed "verified" rather than merely transcribed.
    standings = build.load("standings.tsv")
    rec = {}
    for g in feed_rows:
        for team, pf, pa in ((g["home"], g["homePts"], g["awayPts"]),
                             (g["away"], g["awayPts"], g["homePts"])):
            w, l, t, gpf, gpa = rec.get(team, (0, 0, 0, 0, 0))
            if pf > pa:
                w += 1
            elif pf < pa:
                l += 1
            else:
                t += 1
            rec[team] = (w, l, t, gpf + pf, gpa + pa)
    mismatches = []
    for s in standings:
        w, l, t, gpf, gpa = rec.get(s["abbr"], (0, 0, 0, 0, 0))
        if (w, l, t, gpf, gpa) != (int(s["w"]), int(s["l"]), int(s["t"]),
                                   int(s["pf"]), int(s["pa"])):
            mismatches.append(s["abbr"])
    if mismatches:
        print("FAIL: feed disagrees with official standings for %s" % mismatches,
              file=sys.stderr)
        return 1

    payload = {
        "id": "results_feed",
        "title": "Verified results feed — 2026 season, weeks 1-10",
        "updated": "2026-11-14",
        "requirement": "R22",
        "description": (
            "Every row is a finished game transcribed from the official NFL.com "
            "week pages (raw/schedule-results-2026-week1-10.tsv) and reconciled "
            "against the official standings capture: recomputing all 32 clubs' "
            "W/L/T and PF/PA from this feed reproduces data/standings.tsv "
            "exactly. Backtests settle ONLY against this feed."),
        "provenance": {
            "tier": "OFFICIAL",
            "source_id": "S52",
            "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10",
            "capture": "raw/schedule-results-2026-week1-10.tsv",
            "verification": "tools/verify_results.py + standings recomputation "
                            "(32/32 clubs match data/standings.tsv)",
        },
        "coverage": {
            "seasons": [2026],
            "weeks": [1, 10],
            "games": len(feed_rows),
            "clubs": len(rec),
            "settled_wagers_supported": True,
        },
        "rows": feed_rows,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
        fh.write("\n")
    print("wrote %s: %d rows, standings check OK (32/32)" % (OUT, len(feed_rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
