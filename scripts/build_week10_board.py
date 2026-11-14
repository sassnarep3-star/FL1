"""
Week 10 2026 signal board.

Joins three sources that were each independently verified:
  * data/week10_2026_official.csv  - official NFL.com game statuses (S01)
  * data/raw/games.csv             - closing spread/total + kickoff time (D01)
  * data/depth_deficiency.csv      - which QB actually started (computed, D01)

The output is NOT a betting recommendation. It is a table of the observable
inputs that any line-origination model would need for this week, with the
disagreement between the availability signal and the closing line shown
side by side. No projection is invented: where the model cannot produce a
number, the cell is blank.
"""
from __future__ import annotations

import math
import pathlib

import pandas as pd

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib import norm_team  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = ROOT / "data" / "raw"

W = {"Out": 1.0, "Doubtful": 0.5, "Questionable": 0.25}


def main() -> int:
    inj = pd.read_csv(DATA / "week10_2026_official.csv")
    # NFL.com uses LAR; nfldata uses LA. Normalise both sides before joining (FLAG-07).
    inj["team"] = inj.team.map(norm_team)
    inj["opponent"] = inj.opponent.map(norm_team)
    inj["score"] = inj.game_status.map(W).fillna(0.0)

    # availability disadvantage per team for this week, keyed on QB-inclusive weight
    team = (inj.groupby("team")
               .agg(listed=("player", "count"),
                    out=("game_status", lambda s: int((s == "Out").sum())),
                    doubtful=("game_status", lambda s: int((s == "Doubtful").sum())),
                    questionable=("game_status", lambda s: int((s == "Questionable").sum())),
                    avail_disadv=("score", "sum"))
               .reset_index())

    # QB-specific flag straight from the official report
    qb = inj[(inj.position == "QB") & inj.game_status.isin(["Out", "Doubtful", "Questionable"])]
    qb_flag = (qb.groupby("team")
                 .apply(lambda d: "; ".join(f"{r.player} ({r.injury or 'no injury listed'}) - {r.game_status}"
                                            for _, r in d.iterrows()), include_groups=False)
                 .rename("qb_status")
                 .reset_index())

    g = pd.read_csv(RAW / "games.csv")
    w = g[(g.season == 2026) & (g.week == 10)].copy()
    w["gameday"] = pd.to_datetime(w.gameday)
    for c in ("home_team", "away_team"):
        w[c] = w[c].map(norm_team)

    rows = []
    for _, r in w.iterrows():
        home, away = r.home_team, r.away_team
        h = team[team.team == home]
        a = team[team.team == away]
        hq = qb_flag[qb_flag.team == home]
        aq = qb_flag[qb_flag.team == away]
        rows.append({
            "gameday": r.gameday.strftime("%Y-%m-%d"),
            "away_team": away,
            "home_team": home,
            "closing_spread_home": r.spread_line,
            "closing_total": r.total_line,
            "market_implied_home_winprob": round(1 / (1 + math.exp(-0.028 * 10 * r.spread_line)), 4)
            if pd.notna(r.spread_line) else None,
            "away_listed": int(a.listed.iloc[0]) if len(a) else None,
            "away_out": int(a.out.iloc[0]) if len(a) else None,
            "away_doubtful": int(a.doubtful.iloc[0]) if len(a) else None,
            "away_questionable": int(a.questionable.iloc[0]) if len(a) else None,
            "away_avail_disadv": round(float(a.avail_disadv.iloc[0]), 2) if len(a) else None,
            "home_listed": int(h.listed.iloc[0]) if len(h) else None,
            "home_out": int(h.out.iloc[0]) if len(h) else None,
            "home_doubtful": int(h.doubtful.iloc[0]) if len(h) else None,
            "home_questionable": int(h.questionable.iloc[0]) if len(h) else None,
            "home_avail_disadv": round(float(h.avail_disadv.iloc[0]), 2) if len(h) else None,
            "avail_edge_home": (round(float(h.avail_disadv.iloc[0]) - float(a.avail_disadv.iloc[0]), 2)
                                if len(h) and len(a) else None),
            "home_qb_status": (hq.qb_status.iloc[0] if len(hq) else ""),
            "away_qb_status": (aq.qb_status.iloc[0] if len(aq) else ""),
            "away_score": r.away_score,
            "home_score": r.home_score,
            "source_url": "https://www.nfl.com/injuries/",
            "line_source_url": "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
        })

    B = pd.DataFrame(rows).sort_values(["gameday", "away_team"])

    # every game must have both teams' official report joined, or the build fails
    missing = B[B.away_listed.isna() | B.home_listed.isna()]
    if len(missing):
        raise SystemExit("JOIN FAILED for: " + ", ".join(
            f"{r.away_team}@{r.home_team}" for _, r in missing.iterrows()))

    # availability vs market: rank the games by |availability edge| so a reader
    # can see which games the injury signal separates most, without inventing a
    # point value per unit of availability disadvantage.
    B["avail_rank"] = B.avail_edge_home.abs().rank(ascending=False, method="min")
    B.to_csv(DATA / "week10_signal_board.csv", index=False)

    print(B[["gameday", "away_team", "home_team", "closing_spread_home",
             "away_out", "home_out", "avail_edge_home", "avail_rank"]].to_string(index=False))
    print()
    print("teams covered:", len(team), "| games:", len(B),
          "| teams with a QB on the report:", len(qb_flag))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
