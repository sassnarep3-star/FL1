#!/usr/bin/env python3
"""build_line_board.py — the origination board: fair / market / difference as
THREE SEPARATE COLUMNS, markets originated side first, then total, then
moneyline (engine/origination.ORIGINATION_ORDER, enforced at import).

    fair_line    BLANK. The model specification (data/models.json) deliberately
                 leaves every coefficient unfitted; a number here would be a
                 fabricated fair line. Flagged F19. The engine pipeline
                 (engine/origination.originate) computes the difference the
                 moment a fitted model emits a fair line.
    market_line  the observed market number from the committed third-party
                 snapshot (S47), clearly labelled non-official (F20).
    difference   BLANK while fair_line is blank — never computed from one arm.

Run:  python3 tools/build_line_board.py
"""

import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from engine import origination  # noqa: E402

DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "line_board.csv")

SNAPSHOT_AT = "2026-11-14"
LINE_SOURCE_URL = "https://github.com/nflverse/nfldata/blob/master/data/games.csv"
LINE_SOURCE_ID = "S47"
SLATE_SOURCE_URL = "https://www.nfl.com/schedules/2026/REG10/"
SLATE_SOURCE_ID = "S49"

CANON = {"LA": "LAR"}


def load_slate():
    slate = []
    with open(os.path.join(DATA, "schedule.tsv"), newline="", encoding="utf-8") as fh:
        for raw in csv.reader(fh, delimiter="\t"):
            if not raw or all(c.strip() == "" for c in raw):
                continue
            raw += [""] * (7 - len(raw))
            slate.append({"date": raw[0], "away": raw[3], "home": raw[4]})
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
    rows = []
    for game in sorted(slate, key=lambda g: (g["date"], g["away"], g["home"])):
        g = prices.get((game["date"], game["away"], game["home"]))
        if g is None:
            raise SystemExit(f"no price row for slate game {game['date']} "
                             f"{game['away']}@{game['home']}")
        played = bool(g["away_score"] and g["home_score"])
        base = {"game_id": g["game_id"], "gameday": game["date"],
                "away": game["away"], "home": game["home"],
                "fair_line": None, "source_id": LINE_SOURCE_ID,
                "source_url": LINE_SOURCE_URL,
                "slate_source_id": SLATE_SOURCE_ID,
                "slate_source_url": SLATE_SOURCE_URL,
                "phase": "close" if played else "intermediate"}
        rows.append(dict(base, market="side", selection="home",
                         market_line=float(g["spread_line"]) if g["spread_line"] else None))
        rows.append(dict(base, market="total", selection="over",
                         market_line=float(g["total_line"]) if g["total_line"] else None))
        rows.append(dict(base, market="moneyline", selection="home",
                         market_line=float(g["home_moneyline"]) if g["home_moneyline"] else None))
        rows.append(dict(base, market="moneyline", selection="away",
                         market_line=float(g["away_moneyline"]) if g["away_moneyline"] else None))

    board = origination.originate(rows)   # enforces side -> total -> moneyline
    fields = ["origination", "game_id", "gameday", "away", "home",
              "market", "selection", "fair_line", "market_line", "difference",
              "difference_unit", "phase",
              "source_id", "source_url", "slate_source_id", "slate_source_url"]
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in board:
            out = {k: r.get(k, "") for k in fields}
            out["fair_line"] = "" if r.get("fair_line") is None else r["fair_line"]
            out["market_line"] = "" if r.get("market_line") is None else r["market_line"]
            out["difference"] = "" if r.get("difference") is None else r["difference"]
            w.writerow(out)

    ords = [r["origination"] for r in board]
    assert ords == sorted(ords), "board is not in origination order"
    markets_in_order = []
    for r in board:
        if not markets_in_order or markets_in_order[-1] != r["market"]:
            markets_in_order.append(r["market"])
    print(f"wrote {OUT}")
    print(f"  rows={len(board)} market order seen: {markets_in_order}")
    print(f"  fair_line populated: {sum(1 for r in board if r.get('fair_line') is not None)} "
          "(0 until a model is fitted — F19)")
    print(f"  difference populated: {sum(1 for r in board if r.get('difference') is not None)} "
          "(0 while fair_line is blank — never from one arm)")


if __name__ == "__main__":
    main()
