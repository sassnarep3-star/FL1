#!/usr/bin/env python3
"""
build_fair_lines_m.py — session M: publish the model's fair line, the market
line, and the difference as three SEPARATE columns, for every market we
originate in 2026, in the mandated origination order: SIDE first, then TOTAL,
then MONEYLINE.

Model
-----
The same causal Elo engine the Computed Research Layer documents
(docs/computed/lines.html), constants fixed before any backtest:

  K = 20, home field = 48 Elo, between-season regression 0.75 toward 1505,
  MOV multiplier  ln(mov+1) * 2.2 / (|elo_gap_incl_hfa|*0.001 + 2.2),
  spread = 10.8 * log10(p / (1-p))   (p clipped to [0.02, 0.98]),
  American moneyline from the same p (clipped), standard conversion.

This script REUSES scripts/strategy_lab.py's loaders and asserts its per-game
pre-game Elo matches this script's own loop exactly before publishing anything.

Conventions
-----------
* Spread columns are in the away-posted unit of the pinned snapshot
  (spread_line: positive = away underdog / home favoured).
* side_difference = fair - market, in away points. Negative = the market gives
  the away side more points than the model says is fair (value on the away
  side at the market number); positive = value on the home side.
* ml difference columns are in implied-probability percentage points vs the
  market's RAW implied probability (vig included, not de-vigged).
* total_fair is BLANK: the totals model (stage S2) has unfitted parameters and
  the rule of this repo is to leave a cell blank rather than invent one.

Provenance
----------
Fair lines are MODEL OUTPUT (labelled, versioned). Market lines come from the
pinned third-party snapshot data/raw/games.csv (nflverse/nfldata), flagged as
third-party — no official NFL price source exists (see flagged.html).

Run:  python3 scripts/build_fair_lines_m.py
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "games.csv")
OUT_CSV = os.path.join(ROOT, "data", "fair_lines.csv")
OUT_CAL = os.path.join(ROOT, "data", "fair_lines_calibration.json")

MODEL_VERSION = (
    "fl1-elo-v1 (K=20, HFA=48, inter-season regress x0.75 toward 1505, "
    "MOV multiplier ln(mov+1)*2.2/(|elo_gap_hfa|*0.001+2.2), "
    "spread=10.8*log10(p/(1-p)), p clipped [0.02,0.98])"
)
AS_OF = "2026-11-14"
ELO_PTS_PER_100 = 2.7


def load_strategy_lab():
    spec = importlib.util.spec_from_file_location(
        "fl1_strategy_lab", os.path.join(ROOT, "scripts", "strategy_lab.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fl1_strategy_lab"] = mod
    spec.loader.exec_module(mod)
    return mod


def elo_to_spread(p: float) -> float:
    p = min(max(float(p), 0.02), 0.98)
    return (ELO_PTS_PER_100 * 4.0) * math.log10(p / (1.0 - p))


def p_to_american(p: float) -> float:
    p = min(max(float(p), 0.02), 0.98)
    return -100.0 * p / (1.0 - p) if p >= 0.5 else 100.0 * (1.0 - p) / p


def american_to_prob(o: float) -> float:
    return -o / (100.0 - o) if o < 0 else 100.0 / (100.0 + o)


def own_elo_loop(g: pd.DataFrame):
    """Mirror of strategy_lab.elo_and_form, plus the closing Elo state."""
    K, HFA = 20.0, 48.0
    elo: dict[str, float] = {}
    rows = {}
    for season, wk_block in g.groupby("season", sort=True):
        for t in list(elo):
            elo[t] = 1505.0 + 0.75 * (elo[t] - 1505.0)
        for _, r in wk_block.iterrows():
            h, a = r.home_team, r.away_team
            eh, ea = elo.get(h, 1505.0), elo.get(a, 1505.0)
            ph = 1.0 / (1.0 + 10 ** (-((eh + HFA) - ea) / 400.0))
            rows[r.game_id] = (round(eh, 2), round(ea, 2), round(ph, 6))
            res = 1.0 if r.margin > 0 else (0.5 if r.margin == 0 else 0.0)
            mov = abs(r.margin)
            mult = math.log(mov + 1.0) * (2.2 / ((abs(eh + HFA - ea) * 0.001) + 2.2))
            delta = K * mult * (res - ph)
            elo[h] = eh + delta
            elo[a] = ea - delta
    return rows, elo


def main() -> int:
    lab = load_strategy_lab()
    g_played = lab.load_games()                     # REG games with scores, any season
    g06 = g_played[g_played.season >= lab.TRAIN_START].copy()

    # 1. equivalence proof against the published engine --------------------
    theirs = lab.elo_and_form(g06)
    mine, final_elo = own_elo_loop(g06)
    mism = 0
    for _, r in theirs.iterrows():
        m = mine.get(r.game_id)
        if m is None or m[0] != r.home_elo or m[1] != r.away_elo:
            mism += 1
    if mism:
        print("FATAL: %d games differ from strategy_lab.elo_and_form" % mism,
              file=sys.stderr)
        return 1
    print("elo equivalence: %d games identical to strategy_lab.elo_and_form"
          % len(theirs))

    g06 = g06.merge(theirs, on="game_id", how="left")
    g06["elo_spread"] = g06.home_winprob_elo.apply(elo_to_spread)
    g06["elo_vs_market"] = g06.elo_spread - g06.spread_line

    # 2. calibration vs the published stats (docs/computed/lines.html) ------
    cal_rows = g06[g06.spread_line.notna()]
    err = cal_rows.elo_vs_market
    cal = {
        "model_version": MODEL_VERSION,
        "n_games": int(len(cal_rows)),
        "mean_signed_error_points": round(float(err.mean()), 3),
        "mean_absolute_error_points": round(float(err.abs().mean()), 3),
        "corr_with_close": round(float(cal_rows.elo_spread.corr(cal_rows.spread_line)), 4),
        "published_reference": {
            "note": "docs/computed/lines.html, same constants",
            "mean_signed_error_points": -0.77,
            "mean_absolute_error_points": 2.89,
            "corr_with_close": 0.828,
            "n_games": 5336,
        },
        "as_of": AS_OF,
    }
    with open(OUT_CAL, "w", encoding="utf-8") as fh:
        json.dump(cal, fh, indent=1)
    print("calibration:", {k: cal[k] for k in
                           ("n_games", "mean_signed_error_points",
                            "mean_absolute_error_points", "corr_with_close")})

    # 3. the 2026 origination table ---------------------------------------
    allg = pd.read_csv(RAW)
    allg = allg[allg.game_type == "REG"].copy()
    allg = allg[allg.season == 2026].copy()
    alias = {"SD": "LAC", "STL": "LAR", "LA": "LAR", "OAK": "LV"}
    for c in ("home_team", "away_team"):
        allg[c] = allg[c].replace(alias)
    allg = allg.sort_values(["week", "gameday"]).reset_index(drop=True)

    played_elo = {r.game_id: (r.home_elo, r.away_elo, r.home_winprob_elo)
                  for _, r in g06.iterrows()}

    rows = []
    for _, r in allg.iterrows():
        gid = r.game_id
        if gid in played_elo:
            _, _, ph = played_elo[gid]
            basis = "pre-game Elo (causal)"
        else:
            eh = final_elo.get(r.home_team, 1505.0)
            ea = final_elo.get(r.away_team, 1505.0)
            ph = 1.0 / (1.0 + 10 ** (-((eh + 48.0) - ea) / 400.0))
            basis = "Elo snapshot through W10 TNF (%s)" % AS_OF

        fair_away = elo_to_spread(ph)                  # away-posted unit
        fair_ml_home = p_to_american(ph)
        fair_ml_away = p_to_american(1.0 - ph)

        mkt_spread = r.spread_line if pd.notna(r.spread_line) else None
        mkt_total = r.total_line if pd.notna(r.total_line) else None
        mkt_ml_h = r.home_moneyline if pd.notna(r.home_moneyline) else None
        mkt_ml_a = r.away_moneyline if pd.notna(r.away_moneyline) else None

        rows.append({
            "game_id": gid,
            "season": 2026,
            "week": int(r.week),
            "gameday": str(r.gameday)[:10],
            "away_team": r.away_team,
            "home_team": r.home_team,
            "played": "yes" if pd.notna(r.home_score) else "no",
            "side_fair_spread_away": round(fair_away, 1),
            "side_market_spread_away": mkt_spread,
            "side_difference": (round(fair_away - mkt_spread, 1)
                                if mkt_spread is not None else None),
            "total_fair": None,                        # S2 unfitted — never invented
            "total_market": mkt_total,
            "total_difference": None,
            "ml_fair_home_american": round(fair_ml_home),
            "ml_fair_away_american": round(fair_ml_away),
            "ml_market_home_american": (round(mkt_ml_h)
                                        if mkt_ml_h is not None else None),
            "ml_market_away_american": (round(mkt_ml_a)
                                        if mkt_ml_a is not None else None),
            "ml_diff_home_prob_pts": (
                round((ph - american_to_prob(mkt_ml_h)) * 100, 2)
                if mkt_ml_h is not None else None),
            "ml_diff_away_prob_pts": (
                round(((1 - ph) - american_to_prob(mkt_ml_a)) * 100, 2)
                if mkt_ml_a is not None else None),
            "fair_basis": basis,
            "model_version": MODEL_VERSION,
            "market_provenance": "third-party (nflverse/nfldata games.csv), flagged",
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)
    print("wrote data/fair_lines.csv (%d rows; played %d / upcoming %d)"
          % (len(out), (out.played == "yes").sum(), (out.played == "no").sum()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
