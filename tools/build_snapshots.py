#!/usr/bin/env python3
"""build_snapshots.py — export the price-snapshot table for the originated slate.

The canonical store is engine/price_snapshots.py (append-only SQLite, requires
phase + source + capture time + model version per quote). This script produces
the SITE EXPORT of that store for every market we originate: the Week 10 slate
(data/schedule.tsv) x {side, total, moneyline} in the mandated origination order.

Opening vs closing:
    open_*   BLANK on purpose. No verified source of opening prices exists in
             this repository, and an opener inferred from a close would be a
             fabrication. Flagged F37 on the site. The store is ready to record
             real openers the moment a licensed feed is acquired (Q21).
    close_*  filled from the committed third-party snapshot (S47). For the
             already-played game the feed records the closing line (phase=close);
             for games not yet played the value is the LATEST OBSERVED line as of
             the 2026-11-14 fetch (phase=intermediate) — it is NOT a close and
             is labelled as such.

Run:  python3 tools/build_snapshots.py
"""

import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "price_snapshots.csv")

SNAPSHOT_AT = "2026-11-14"          # fetch date of data/raw/games.csv (MANIFEST)
LINE_SOURCE_URL = "https://github.com/nflverse/nfldata/blob/master/data/games.csv"
LINE_SOURCE_ID = "S47"
SLATE_SOURCE_URL = "https://www.nfl.com/schedules/2026/REG10/"
SLATE_SOURCE_ID = "S49"

CANON = {"LA": "LAR"}


def num(v):
    return None if v is None or str(v).strip() == "" else float(v)


def load_slate():
    slate = []
    with open(os.path.join(DATA, "schedule.tsv"), newline="", encoding="utf-8") as fh:
        for raw in csv.reader(fh, delimiter="\t"):
            if not raw or all(c.strip() == "" for c in raw):
                continue
            raw += [""] * (7 - len(raw))
            date, time_et, broadcast, away, home, venue, note = raw[:7]
            slate.append({"date": date, "away": away, "home": home})
    return slate


def load_prices():
    idx = {}
    with open(os.path.join(DATA, "raw", "games.csv"), newline="", encoding="utf-8") as fh:
        for g in csv.DictReader(fh):
            if g.get("season") != "2026":
                continue
            key = (g["gameday"], CANON.get(g["away_team"], g["away_team"]),
                   CANON.get(g["home_team"], g["home_team"]))
            idx[key] = g
    return idx


def main():
    slate = load_slate()
    prices = load_prices()
    fields = ["game_id", "gameday", "away", "home", "market_type", "side",
              "open_line", "open_odds_american", "open_captured_at_utc", "open_source_id",
              "close_line", "close_odds_american", "close_captured_at_utc",
              "phase", "source_id", "source_url", "slate_source_id", "slate_source_url",
              "note"]
    rows_out = []
    for game in sorted(slate, key=lambda g: (g["date"], g["away"], g["home"])):
        g = prices.get((game["date"], game["away"], game["home"]))
        if g is None:
            raise SystemExit(f"no price row for slate game {game['date']} "
                             f"{game['away']}@{game['home']}")
        played = bool(g["away_score"] and g["home_score"])
        phase = "close" if played else "intermediate"
        phase_note = ("closing line recorded by the third-party feed; the feed "
                      "publishes no capture timestamp for the close (F37)"
                      if played else
                      f"latest observed line as of the {SNAPSHOT_AT} snapshot; "
                      "the game is not played, so this is NOT a close")
        common = {"game_id": g["game_id"], "gameday": game["date"],
                  "away": game["away"], "home": game["home"],
                  "open_line": "", "open_odds_american": "",
                  "open_captured_at_utc": "", "open_source_id": "",
                  "close_captured_at_utc": SNAPSHOT_AT if not played else "",
                  "phase": phase,
                  "source_id": LINE_SOURCE_ID, "source_url": LINE_SOURCE_URL,
                  "slate_source_id": SLATE_SOURCE_ID, "slate_source_url": SLATE_SOURCE_URL,
                  "note": phase_note}
        rows_out.append(dict(common, market_type="side", side="home",
                             close_line=g["spread_line"],
                             close_odds_american=g["home_spread_odds"]))
        rows_out.append(dict(common, market_type="total", side="over",
                             close_line=g["total_line"],
                             close_odds_american=g["over_odds"]))
        rows_out.append(dict(common, market_type="moneyline", side="home",
                             close_line=g["home_moneyline"],
                             close_odds_american=g["home_moneyline"]))
        rows_out.append(dict(common, market_type="moneyline", side="away",
                             close_line=g["away_moneyline"],
                             close_odds_american=g["away_moneyline"]))

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows_out:
            w.writerow({k: r.get(k, "") for k in fields})

    opens = sum(1 for r in rows_out if r["open_line"] != "")
    closes = sum(1 for r in rows_out if r["close_line"] != "")
    print(f"wrote {OUT}")
    print(f"  slate games={len(slate)} rows={len(rows_out)} "
          f"(open populated={opens} — expected 0 until an opener feed exists; "
          f"close/latest populated={closes})")


if __name__ == "__main__":
    main()
