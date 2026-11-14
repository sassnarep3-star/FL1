#!/usr/bin/env python3
"""
build_replacement_depth_m.py — session M: track the DEPTH of the replacement,
not just the fact of a replacement.

For every club-slot group whose published first string carries an official
Week 10 game status (Out / Doubtful / Questionable), walk the club's OWN
published depth order and name the first player not carrying an "Out"
designation. The published output is the replacement's STRING (2nd, 3rd, 4th)
and how many listed players are out above him — the depth of the replacement.

Rule (derived, published with every row):
  * inputs = official Week 10 injury report (data/injuries.tsv, S01) and the
    clubs' own published depth charts (data/depth.tsv + data/depth-kc.tsv,
    per-club sources in data/depth-sources.tsv);
  * name matching uses only the explicit alias table data/depth-aliases.tsv
    (never fuzzy matching);
  * players whose official game status is "Out" are skipped; the first listed
    player remaining is the replacement; his string = his published rank;
  * a player absent from the club's injury report is labelled "not listed"
    (an official fact — and per league policy, absence is NOT evidence of
    availability, so the row carries that caveat);
  * if every listed player at the spot is Out, the replacement cell stays
    BLANK and the row is flagged.

Output: data/replacement_depth.csv

Run:  python3 scripts/build_replacement_depth_m.py
"""
from __future__ import annotations

import csv
import importlib.util
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "replacement_depth.csv")

FIELDS = [
    "team", "club", "unit", "slot", "line", "starter", "starter_status",
    "starter_injury", "starter_practice", "out_above", "replacement",
    "replacement_rank", "replacement_depth", "replacement_own_status",
    "replacement_note", "depth_source", "injury_source", "rule", "flag",
]

RULE = ("derived: first player in the club's own published depth order at the "
        "same spot whose official game status is not Out; string = published "
        "rank; alias table data/depth-aliases.tsv only")


def load_build():
    spec = importlib.util.spec_from_file_location(
        "fl1_build", os.path.join(ROOT, "tools", "build.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fl1_build"] = mod
    spec.loader.exec_module(mod)
    return mod


def ordinal(n: int) -> str:
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return "%d%s string" % (n, suf)


def main() -> int:
    build = load_build()
    teams = build.load("teams.tsv")
    injuries = build.load("injuries.tsv")
    aliases = build.load("depth-aliases.tsv")
    depth_all = build.load("depth.tsv")
    depth_kc = build.load("depth-kc.tsv")
    depth_sources = build.load("depth-sources.tsv")

    name_of = {t["abbr"]: t["name"] for t in teams}
    src_of = {r["abbr"]: r for r in depth_sources}

    alias = {build._norm_name(a["depthName"]): build._norm_name(a["reportName"])
             for a in aliases}
    by_club = defaultdict(dict)
    for r in injuries:
        by_club[r["team"]][build._norm_name(r["player"])] = r

    def status_of(team, player):
        key = build._norm_name(alias.get(build._norm_name(player), player))
        st = by_club.get(team, {}).get(key)
        return st

    # group players: key = (team, unit, slot, line)
    groups = defaultdict(list)
    for d in depth_all:
        if not d["player"].strip():
            continue
        groups[(d["team"], d["unit"], d["slot"], d["line"])].append(
            (int(d["rank"]), d["player"]))
    for d in depth_kc:                       # Kansas City: own capture, no line
        if not d["player"].strip():
            continue
        groups[("KC", d["unit"], d["slot"], "")].append(
            (int(d["rank"]), d["player"]))

    rows = []
    for key in sorted(groups):
        team, unit, slot, line = key
        members = sorted(groups[key])
        first_rank, first_player = members[0]
        if first_rank != 1:
            continue                          # not a starter spot
        st = status_of(team, first_player)
        if st is None:
            continue                          # starter not on the report at all
        gs = st["game"].strip().lower()
        if gs not in ("out", "doubtful", "questionable"):
            continue

        replacement = None
        out_above = 0
        for rank, player in members[1:]:
            rst = status_of(team, player)
            rgs = (rst["game"].strip().lower() if rst else "")
            if rgs == "out":
                out_above += 1
                continue
            replacement = (rank, player, rst)
            break

        src = src_of.get(team, {})
        src_id = "S08" if team == "KC" else src.get("source", "")
        row = {
            "team": team,
            "club": name_of.get(team, team),
            "unit": unit,
            "slot": slot,
            "line": line,
            "starter": first_player,
            "starter_status": st["game"].strip(),
            "starter_injury": st["injury"].strip(),
            "starter_practice": st["practice"].strip(),
            "out_above": out_above if replacement else "",
            "replacement": "",
            "replacement_rank": "",
            "replacement_depth": "",
            "replacement_own_status": "",
            "replacement_note": "",
            "depth_source": src_id,
            "injury_source": "S01",
            "rule": RULE,
            "flag": "",
        }
        if replacement is None:
            row["flag"] = ("no listed player remains at this spot "
                           "(all listed players Out)")
        else:
            rank, player, rst = replacement
            row["replacement"] = player
            row["replacement_rank"] = rank
            row["replacement_depth"] = ordinal(rank)
            if rst is None:
                row["replacement_own_status"] = "not listed"
                row["replacement_note"] = (
                    "not on the club's Week 10 injury report; per league policy "
                    "absence is not evidence of availability")
            else:
                row["replacement_own_status"] = rst["game"].strip() or "not listed"
                if not rst["game"].strip():
                    row["replacement_note"] = (
                        "listed on the report with no game status; per league "
                        "policy absence of a status is not evidence of availability")
            if rank >= 3:
                row["flag"] = ("replacement deeper than 2nd string "
                               "(%s listed Out above him)" % out_above)
        rows.append(row)

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    by_unit = defaultdict(int)
    deep = 0
    for r in rows:
        by_unit[r["unit"]] += 1
        if r["replacement_rank"] and int(r["replacement_rank"]) >= 3:
            deep += 1
    print("wrote data/replacement_depth.csv (%d affected spots)" % len(rows))
    print("  by unit:", dict(by_unit))
    print("  replacements at 3rd string or deeper:", deep)
    print("  blank replacement (all listed Out):",
          sum(1 for r in rows if not r["replacement"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
