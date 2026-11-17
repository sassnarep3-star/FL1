#!/usr/bin/env python3
"""H6 — backlog re-audit: correct every brief line's status against committed evidence.

Reads data/requirements_backlog.json and updates the status + evidence of the
lines this session's H2-H5 work (and earlier committed work) now satisfies,
using only evidence that exists in the committed tree. A line is moved to
`done` only when a committed artefact proves it; otherwise it stays as-is or
moves to `partial` with the exact remaining gap named.

The update is idempotent: re-running produces the same file.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
PATH = os.path.join(DATA, "requirements_backlog.json")

# row id -> (new_status, evidence)
UPDATES = {
    "R45": (
        "done",
        "Official NFL Game Books for all 13 completed Week 10 games captured "
        "(data/gamebooks_{games,rosters,snaps}.tsv): actual starters, "
        "substitutions, DNP, inactives, game-day weather/roof/surface and "
        "playtime, transcribed from the official PDFs (S90). Verified by "
        "tools/verify_gamebooks.py (GB-1..GB-8).",
    ),
    "R50": (
        "done",
        "Official inactive lists and the Game Book Playtime Percentage table "
        "captured for all 13 games (data/gamebooks_rosters.tsv role "
        "inactive/dnp; data/gamebooks_snaps.tsv). Caveat: the Playtime "
        "Percentage is the Game Book's playtime measure, and 4 of 13 books "
        "label it '(Unofficial)' (flag F67); it is not an official snap-count "
        "table.",
    ),
    "R77": (
        "partial",
        "Stadium roof/surface overlay built from the Game Book venue line "
        "(data/weather_overlay.tsv); NWS forecast grids resolved for 11 of 13 "
        "Week 11 venues (data/venue_spotchecks.json). Remaining gap: the NWS "
        "hourly wind/precipitation VALUES are not retained in this capture "
        "(left blank, not inferred); a refresh re-reads each grid. Estadio "
        "Azteca and FedExField have no resolved NWS grid yet.",
    ),
    "R75": (
        "partial",
        "Game Book Playtime Percentage captured as the starter/playing-time "
        "proxy for 13 games (data/gamebooks_snaps.tsv). Remaining gap: 4 of "
        "13 books label the table '(Unofficial)' (F67), so it is a strong "
        "proxy but not a certified official snap count on those games.",
    ),
    "R37": (
        "done",
        "Two-sided 'what would change our mind' field added to every strategy "
        "entry (data/strategies.json change_of_mind upgrade/downgrade), "
        "rendered on the Leaderboard (committed by session fc0ed6e8; carried "
        "on main).",
    ),
    "R76": (
        "done",
        "Control baseline (random picks / favourites-only) ranked in the same "
        "table as the model strategies on the removal-of-luck panel "
        "(data/luck_panel.json; committed by session 38a78804).",
    ),
}


def main():
    with open(PATH, encoding="utf-8") as fh:
        doc = json.load(fh)
    rows = doc.get("rows", [])
    changed = 0
    for r in rows:
        rid = r.get("id")
        if rid in UPDATES:
            status, evidence = UPDATES[rid]
            r["status"] = status
            r["evidence"] = evidence
            r["updated_by"] = "arena/3f12fa46-fl1 (H6 re-audit)"
            changed += 1
    doc["updated"] = "2026-11-17"
    doc["reaudited_by"] = "arena/3f12fa46-fl1"
    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    # recompute counts
    counts = {}
    for r in rows:
        counts[r.get("status", "?")] = counts.get(r.get("status", "?"), 0) + 1
    doc["counts"] = counts
    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    print("backlog: updated %d rows; counts=%s" % (changed, counts))


if __name__ == "__main__":
    main()
