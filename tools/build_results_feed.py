#!/usr/bin/env python3
"""build_results_feed.py — the verified results feed.

Joins the OFFICIALLY VERIFIED 2026 scores (data/results.tsv, reconciled 32/32
against the league standings) to the committed third-party price snapshot
(data/raw/games.csv) and settles every originated market (side, total,
moneyline) in the mandated origination order.

Output: data/results_feed.csv — one row per (game, market, selection) with:
    result_source_url  official site the SCORE was reconciled against
    line_source_url    third-party snapshot the PRICE came from (clearly labelled)
    outcome            win | loss | push  (push-aware; no pushes are dropped)
    pnl_unit           per-unit PnL at the stated American price (blank if no price)

Nothing is imputed. A price the snapshot does not hold becomes a blank odds
cell and is counted in the printed summary. Any score disagreement between the
two inputs is a hard failure — the script refuses to write.

Run:  python3 tools/build_results_feed.py
"""

import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from engine import settlement as rf  # noqa: E402

DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "results_feed.csv")

RESULT_SOURCE_URL = "https://www.nfl.com/standings/league/2026/REG"
RESULT_SOURCE_ID = "S03"
LINE_SOURCE_URL = "https://github.com/nflverse/nfldata/blob/master/data/games.csv"
LINE_SOURCE_ID = "S47"

# Official code vs the third-party feed's older code (flag F07). The mapping is
# explicit and evidence-based: same club, same season, same week, same score.
CANON = {"LA": "LAR"}


def canon(t):
    return CANON.get(t, t)


def load_results():
    rows = []
    with open(os.path.join(DATA, "results.tsv"), newline="", encoding="utf-8") as fh:
        for raw in csv.reader(fh, delimiter="\t"):
            if not raw or all(c.strip() == "" for c in raw):
                continue
            raw += [""] * (6 - len(raw))
            week, date, away, apts, home, hpts = raw[:6]
            rows.append({"week": int(week), "date": date,
                         "away": away, "home": home,
                         "away_score": int(apts), "home_score": int(hpts)})
    return rows


def load_prices():
    idx = {}
    with open(os.path.join(DATA, "raw", "games.csv"), newline="", encoding="utf-8") as fh:
        for g in csv.DictReader(fh):
            if g.get("season") != "2026":
                continue
            key = (g["gameday"], canon(g["away_team"]), canon(g["home_team"]))
            idx[key] = g
    return idx


def num(v):
    return None if v is None or str(v).strip() == "" else float(v)


def main():
    results = load_results()
    prices = load_prices()
    games = []
    for r in results:
        g = prices.get((r["date"], canon(r["away"]), canon(r["home"])))
        if g is None:
            raise SystemExit(f"no price row for {r['date']} {r['away']}@{r['home']}")
        if (g["away_score"] != str(r["away_score"])
                or g["home_score"] != str(r["home_score"])):
            raise SystemExit(
                f"score disagreement for {r['date']} {r['away']}@{r['home']}: "
                f"official {r['away_score']}-{r['home_score']} vs feed "
                f"{g['away_score']}-{g['home_score']}")
        games.append({
            "game_id": g["game_id"], "gameday": r["date"], "week": r["week"],
            "away": r["away"], "home": r["home"],
            "away_score": r["away_score"], "home_score": r["home_score"],
            "spread_home": num(g["spread_line"]),
            "total_line": num(g["total_line"]),
            "ml_home": num(g["home_moneyline"]), "ml_away": num(g["away_moneyline"]),
            "home_spread_odds": num(g["home_spread_odds"]),
            "over_odds": num(g["over_odds"]),
            "result_source_url": RESULT_SOURCE_URL,
            "line_source_url": LINE_SOURCE_URL,
            "line_source_id": LINE_SOURCE_ID,
        })

    rows, summary = rf.feed_rows(games)
    fields = ["game_id", "gameday", "week", "away", "home", "away_score", "home_score",
              "market", "selection", "line", "odds_american", "outcome", "pnl_unit",
              "result_source_id", "result_source_url", "line_source_id", "line_source_url"]
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            r["result_source_id"] = RESULT_SOURCE_ID
            r["line_source_id"] = LINE_SOURCE_ID
            w.writerow({k: r.get(k, "") for k in fields})

    roi = rf.roi(rows)
    print(f"wrote {OUT}")
    print(f"  games={summary['games']} market_rows={summary['market_rows']} "
          f"wins={summary['settled_wins']} losses={summary['settled_losses']} "
          f"pushes={summary['pushes']}")
    print(f"  unpriced: {summary['missing_prices']}")
    print(f"  ROI on priced rows: {roi}")


if __name__ == "__main__":
    main()
