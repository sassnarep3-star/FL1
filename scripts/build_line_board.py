#!/usr/bin/env python3
"""Build data/line_board.json (requirements R23 + R24).

Publishes the model's FAIR line, the MARKET line and the DIFFERENCE as three
separate columns for every market we originate — in the mandated origination
order: SIDE first, then TOTAL, then MONEYLINE (R23).

Conventions (fixed before results, published on the page):
  * SIDE quotes are HOME-view spreads (negative = home favourite). The pinned
    market feed records the AWAY club's spread (check V8, data/verification-d.tsv),
    so the market column is the negated verbatim capture; the verbatim number
    lives in the price-snapshot store.
  * difference = model fair - market. Positive means the model's number is
    higher than the market's in the displayed convention. Blank when either
    side is blank — never a zero.

Provenance per column:
  fair      COMPUTED  (engine/fairline.py over official standings + results)
  market    THIRD_PARTY (pinned nflverse capture S47; no official league source
            prices NFL markets — flag F23/F26)
  difference COMPUTED-OVER-THIRD-PARTY (carries the market flag)

Run:  python3 scripts/build_line_board.py
"""

import csv
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from engine import fairline  # noqa: E402
import build  # noqa: E402

DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "line_board.json")


def main() -> int:
    standings = build.load("standings.tsv")
    results = build.load("results.tsv")
    with open(os.path.join(DATA, "week10_signal_board.csv"), newline="",
              encoding="utf-8") as fh:
        board = list(csv.DictReader(fh))

    strength = fairline.team_strength(standings)
    hfa = fairline.home_field_advantage(results)
    msd = fairline.margin_sd(results)
    if hfa["hfa"] is None or msd["sd"] is None:
        print("FAIL: official feeds too small to compute coefficients",
              file=sys.stderr)
        return 1

    rows = []
    for g in sorted(board, key=lambda r: (r["gameday"], r["away_team"])):
        away, home = g["away_team"], g["home_team"]
        if home not in strength or away not in strength:
            print("FAIL: %s@%s missing from official standings" % (away, home),
                  file=sys.stderr)
            return 1
        fg = fairline.fair_game(strength, home, away,
                                hfa["hfa"], msd["sd"],
                                season_games=min(strength[home]["games"],
                                                 strength[away]["games"]))
        mkt_spread_home = -float(g["closing_spread_home"])   # V8 transform
        mkt_total = float(g["closing_total"])
        settled = g.get("home_score") not in (None, "", "nan") and \
            str(g.get("home_score")).strip() != ""
        result_str = ""
        if settled:
            result_str = "%s %d @ %s %d" % (away, int(float(g["away_score"])),
                                            home, int(float(g["home_score"])))

        for mt in fairline.origination_order():          # SIDE, TOTAL, MONEYLINE
            fr = fg[mt]
            if mt == "SIDE":
                market, market_note = mkt_spread_home, (
                    "home-view = negated verbatim away spread %.1f (V8 transform)"
                    % float(g["closing_spread_home"]))
            elif mt == "TOTAL":
                market, market_note = mkt_total, "captured closing total"
            else:
                market, market_note = None, (
                    "no moneyline price captured (flag F25)")
            diff = fairline.difference(fr["fair"], market)
            rows.append({
                "game": "%s @ %s" % (away, home),
                "gameday": g["gameday"],
                "market_type": mt,
                "model_fair_line": fr["fair"],
                "model_band": fr["band"],
                "market_line": market,
                "difference": diff,
                "fair_tier": "COMPUTED",
                "fair_sources": ["S03", "S52"],
                "market_tier": "THIRD_PARTY" if market is not None else "BLANK",
                "market_sources": ["S47"] if market is not None else [],
                "difference_tier": ("COMPUTED-OVER-THIRD-PARTY"
                                    if diff is not None else "BLANK"),
                "market_note": market_note,
                "result": result_str,
                "flags": (["F23", "F26"] if mt == "SIDE" else
                          ["F23"] if market is not None else ["F25"]),
            })

    payload = {
        "id": "line_board",
        "title": "Line board — model fair line, market line, difference (separate columns)",
        "updated": "2026-11-14",
        "requirement": "R24",
        "order_requirement": "R23 — SIDE first, then TOTAL, then MONEYLINE",
        "description": (
            "Three separate columns per originated market, in the mandated "
            "origination order. difference = model fair - market, blank when "
            "either side is blank. The model is the published naive baseline "
            "(engine/fairline.py) computed from official standings and results "
            "only; its coefficients are printed on the page with their n. The "
            "market column is a pinned third-party capture — no official league "
            "source prices NFL markets (flag F23) — and the moneyline market "
            "cell is blank because none was captured (flag F25)."),
        "conventions": {
            "side_perspective": "HOME-view spread (negative = home favourite)",
            "difference": "model_fair_line - market_line",
            "band": "1.96 * sd_margin / sqrt(min games played), sampling error of "
                    "the margin estimate; reported so the point estimate is not "
                    "read as precision",
        },
        "coefficients": {
            "home_field_advantage_points": round(hfa["hfa"], 3),
            "hfa_n_games": hfa["n"],
            "margin_sd_points": round(msd["sd"], 3),
            "margin_sd_n_games": msd["n"],
            "strength": "(PF-PA)/G per club, official standings",
            "total": "(PPG_h + OPPG_h + PPG_a + OPPG_a)/2",
            "ml_prob": "Phi(fair_margin / margin_sd)",
            "tier": "COMPUTED",
        },
        "coverage": {
            "games": len(board),
            "markets": len(rows),
            "fair_filled": sum(1 for r in rows if r["model_fair_line"] is not None),
            "market_filled": sum(1 for r in rows if r["market_line"] is not None),
            "difference_filled": sum(1 for r in rows if r["difference"] is not None),
        },
        "rows": rows,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
        fh.write("\n")
    c = payload["coverage"]
    print("wrote %s: %d rows (fair %d, market %d, difference %d)"
          % (OUT, len(rows), c["fair_filled"], c["market_filled"],
             c["difference_filled"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
