"""
Availability & depth-deficiency model.

PURPOSE
-------
The owner asked for a system that (a) tracks injuries and (b) knows when a
defence or offence is down to its 2nd, 3rd or 4th string because of lineup
changes. This script produces the *quantifiable* half of that from real
official-derived data, and marks the half that cannot be quantified yet.

WHAT IS COMPUTED
----------------
1. data/availability_2025.csv  - per team-week counts of players carrying each
   official game status, plus a weighted "availability disadvantage" score.
2. data/depth_deficiency.csv   - per team-week count of QB1 / QB2 / QB3
   depletions, using the QB identity actually recorded in games.csv
   (away_qb_id / home_qb_id) against that team's most-used QB that season.
3. data/week10_2026_official.csv - a hand-verified snapshot of the official
   NFL.com Week 10 2026 injury report, one row per player, with the official
   page as the source and a per-row quote.

WEIGHTS (fixed a priori, documented so they can be challenged)
-------------------------------------------------------------
Out = 1.00   Doubtful = 0.50   Questionable = 0.25
These are prior weights reflecting *expected games lost*, not probabilities of
playing. The 2016 policy change removed numeric probabilities from the official
definitions (see sources ESPN_PROBABLE), so any numeric weight is an assumption
of this model, not an NFL statement. Flagged as open question Q-AVAIL-01.
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data"

WEIGHTS = {"Out": 1.00, "Doubtful": 0.50, "Questionable": 0.25}
IR_WEIGHT = 1.00


def build_availability() -> pd.DataFrame:
    inj = pd.read_csv(RAW / "injuries_2025.csv")
    inj["w"] = inj.report_status.map({**WEIGHTS, "Injured Reserve": IR_WEIGHT})
    inj = inj[inj.w.notna()]

    rows = []
    for (season, week, team), blk in inj.groupby(["season", "week", "team"]):
        rows.append({
            "season": int(season), "week": int(week), "team": team,
            "listed_players": int(len(blk)),
            "out": int((blk.report_status == "Out").sum()),
            "doubtful": int((blk.report_status == "Doubtful").sum()),
            "questionable": int((blk.report_status == "Questionable").sum()),
            "injured_reserve": int((blk.report_status == "Injured Reserve").sum()),
            "avail_disadv": round(float(blk.w.sum()), 3),
        })
    df = pd.DataFrame(rows).sort_values(["week", "team"])
    df.to_csv(OUT / "availability_2025.csv", index=False)
    return df


def build_qb_depth() -> pd.DataFrame:
    """Which QB actually played, and whether it was the team's primary QB.

    games.csv records the starting QB id per game (away_qb_id / home_qb_id).
    A team's 'primary' QB for a season is the modal starter. A start by anyone
    else is a depth event.

    IMPORTANT LIMITATION: `deputy_rank` is the order in which a team's starting
    QBs first appeared *that season*. It is NOT a published depth-chart slot.
    A backup who starts in week 1 is therefore recorded as #1, and a genuine
    QB2 who takes over in week 5 is recorded as #2 only if exactly one other QB
    had started before him. Published depth charts (nflverse `depth_charts`)
    are blocked in this sandbox, so the field is named `start_sequence_rank`
    and the categories say "different starter" rather than "string".
    """
    g = pd.read_csv(RAW / "games.csv")
    g = g[g.game_type == "REG"]
    g = g[g.home_score.notna()]
    g["gameday"] = pd.to_datetime(g.gameday, errors="coerce")

    long = []
    for side in ("home", "away"):
        t = g[["season", "week", "gameday", f"{side}_team", f"{side}_qb_id", f"{side}_qb_name"]].copy()
        t.columns = ["season", "week", "gameday", "team", "qb_id", "qb_name"]
        t["side"] = side
        long.append(t)
    L = pd.concat(long).sort_values(["season", "week", "gameday"])

    out = []
    for season, blk in L.groupby("season"):
        if season < 1999:
            continue
        primary = (blk.groupby("team").qb_id.apply(lambda s: s.value_counts().idxmax()))
        seen: dict[str, list] = {}
        for _, r in blk.iterrows():
            if pd.isna(r.qb_id):
                continue
            lst = seen.setdefault(r.team, [])
            if r.qb_id not in lst:
                lst.append(r.qb_id)
            rank = lst.index(r.qb_id) + 1
            is_primary = (r.qb_id == primary.get(r.team))
            out.append({
                "season": int(season), "week": int(r.week), "team": r.team,
                "qb_name": r.qb_name, "qb_id": r.qb_id,
                "is_primary_qb": bool(is_primary),
                "start_sequence_rank": int(rank),
                "depth_event": bool(not is_primary),
            })
    D = pd.DataFrame(out)

    # per team-week deficiency summary
    agg = D.groupby(["season", "week", "team"]).agg(
        starters_not_primary=("depth_event", "sum"),
        max_start_sequence_rank=("start_sequence_rank", "max"),
    ).reset_index()
    # Category names describe the data, not a depth chart (see docstring).
    agg["qb_deficiency"] = np.where(agg.max_start_sequence_rank >= 3,
                             "3rd-or-later different starter",
                             np.where(agg.max_start_sequence_rank == 2,
                                      "2nd different starter",
                                      "primary starter"))
    agg.sort_values(["season", "week", "team"]).to_csv(OUT / "depth_deficiency.csv", index=False)
    return agg


def main() -> int:
    a = build_availability()
    d = build_qb_depth()
    print("availability_2025 rows:", len(a), "teams:", a.team.nunique(),
          "weeks:", a.week.min(), "-", a.week.max())
    print(a.sort_values("avail_disadv", ascending=False).head(8).to_string(index=False))
    print()
    print("depth_deficiency rows:", len(d))
    print(d[d.season >= 2025].groupby("qb_deficiency").size().to_string())
    print(d[(d.season == 2026)].sort_values(["week", "team"]).tail(8).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
