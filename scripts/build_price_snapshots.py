#!/usr/bin/env python3
"""Build data/price_snapshots.json (requirement R21).

The store records OPENING and CLOSING numbers for every market we originate.
The seed slate is the Week 10, 2026 board — the 14 games this repository
publishes lines for. Per game the store holds four rows in the mandated
origination order (R23): SIDE-HOME, TOTAL-GAME, MONEYLINE-HOME, MONEYLINE-AWAY.

What fills in, and what does not:
  * Closing spread and closing total: transcribed from the pinned third-party
    capture behind data/week10_signal_board.csv (nflverse/nfldata games.csv,
    sha256 in data/raw/MANIFEST.json). Provenance THIRD_PARTY, flagged F23.
  * Opening prices: NO source exists anywhere in this repository. Every open
    cell is left blank (None) and the row carries the flag. Never inferred.
  * Moneyline closes: not captured in the Week 10 board. Blank + flagged.

Run:  python3 scripts/build_price_snapshots.py
"""

import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from engine import snapshots  # noqa: E402

DATA = os.path.join(ROOT, "data")
BOARD = os.path.join(DATA, "week10_signal_board.csv")
OUT = os.path.join(DATA, "price_snapshots.json")

TP = snapshots.PROVENANCE_THIRD_PARTY
NONE = snapshots.PROVENANCE_NONE


def main() -> int:
    with open(BOARD, newline="", encoding="utf-8") as fh:
        board = list(csv.DictReader(fh))

    rows = []
    for g in board:
        away, home = g["away_team"], g["home_team"]
        gameday = g["gameday"]
        game_id = "2026-W10-%s-%s" % (away, home)
        close_spread = float(g["closing_spread_home"])
        close_total = float(g["closing_total"])

        common = dict(season=2026, week=10, game_id=game_id,
                      away=away, home=home)
        # 1) SIDE first (R23). The pinned feed records the AWAY team's spread
        #    (V8: 13/13 games verified against moneyline direction), so the
        #    verbatim value is stored as the AWAY quote.
        rows.append(snapshots.record(
            **common, market_type="SIDE", side=away, quote_side="AWAY",
            close_price=close_spread, close_ts=gameday,
            close_source="S47", close_provenance=TP,
            notes="closing spread recorded VERBATIM as the away club's line (%+.1f); "
                  "feed convention verified by check V8 (data/verification-d.tsv)"
                  % close_spread))
        # 2) TOTAL second.
        rows.append(snapshots.record(
            **common, market_type="TOTAL", side="GAME", quote_side="GAME",
            close_price=close_total, close_ts=gameday,
            close_source="S47", close_provenance=TP,
            notes="closing game total"))
        # 3) MONEYLINE last: two quotes, neither captured. Blank + flagged.
        rows.append(snapshots.record(
            **common, market_type="MONEYLINE", side=home, quote_side="HOME",
            notes="no moneyline price captured for this game — blank and flagged (F25)"))
        rows.append(snapshots.record(
            **common, market_type="MONEYLINE", side=away, quote_side="AWAY",
            notes="no moneyline price captured for this game — blank and flagged (F25)"))

    rows.sort(key=snapshots.sort_key)
    errors = snapshots.validate(rows)
    if errors:
        print("FAIL: store invalid:", *errors, sep="\n  ", file=sys.stderr)
        return 1

    cov = snapshots.coverage(rows)
    payload = {
        "id": "price_snapshots",
        "title": "Price-snapshot store — opening and closing numbers per originated market",
        "updated": "2026-11-14",
        "requirement": "R21",
        "description": (
            "One row per (game, market, quote side) for every market this "
            "repository originates, created before kickoff and completed at "
            "close. A price cell is filled only when a named source record "
            "backs it. Opening prices have no source in this repository, so "
            "every open cell is blank and flagged — recorded absence, not "
            "guesswork. Rows are stored in origination order: SIDE, then "
            "TOTAL, then MONEYLINE (requirement R23)."),
        "policy": {
            "order": ["SIDE", "TOTAL", "MONEYLINE"],
            "open_rule": "record at first publication of our own line; blank "
                         "until a licensed opening-price source is approved (GAP-01)",
            "close_rule": "record once at close; never overwritten (history is "
                          "corrected only by a dated verification-log entry)",
            "provenance_rule": "OFFICIAL | THIRD_PARTY | blank; a price without "
                               "provenance fails validation",
        },
        "coverage": cov,
        "flags": ["F23", "F25"],
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
        fh.write("\n")
    print("wrote %s: %d rows (open filled %d/%d, close filled %d/%d)"
          % (OUT, len(rows), cov["open_filled"], cov["TOTAL_ROWS"],
             cov["close_filled"], cov["TOTAL_ROWS"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
