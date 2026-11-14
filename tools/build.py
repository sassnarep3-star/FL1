#!/usr/bin/env python3
"""
build.py — regenerates assets/js/data.js from the committed data files.

Design notes
------------
* No runtime build step is required by the site: assets/js/data.js is generated
  here and committed. The published site is plain static files.
* Every number this script computes is derived from a source-marked TSV/JSON in
  data/. Nothing is typed in by hand, so the arithmetic in the site is auditable
  by re-running this script.
* The script refuses to write a value it cannot compute. Missing stays missing.

Run:  python3 tools/build.py
"""

import csv
import json
import os
import sys
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "assets", "js", "data.js")

OFF_POS = {
    "QB", "RB", "FB", "WR", "TE", "T", "G", "C", "OT", "OG", "LS_OFF",
}
DEF_POS = {
    "DE", "DT", "NT", "LB", "ILB", "OLB", "CB", "S", "DB", "SAF", "FS", "SS",
}
SPEC_POS = {"K", "P", "LS"}

POS_GROUP = {}
for p in ("QB", "RB", "FB", "WR", "TE"):
    POS_GROUP[p] = "Offense — skill"
for p in ("T", "G", "C", "OT", "OG"):
    POS_GROUP[p] = "Offense — line"
for p in ("DE", "DT", "NT"):
    POS_GROUP[p] = "Defense — line"
for p in ("LB", "ILB", "OLB"):
    POS_GROUP[p] = "Defense — linebacker"
for p in ("CB", "DB"):
    POS_GROUP[p] = "Defense — corner"
for p in ("S", "SAF", "FS", "SS"):
    POS_GROUP[p] = "Defense — safety"
for p in ("K", "P", "LS"):
    POS_GROUP[p] = "Special teams"


def read_tsv(name, fields):
    path = os.path.join(DATA, name)
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for raw in csv.reader(fh, delimiter="\t"):
            if not raw or all(c.strip() == "" for c in raw):
                continue
            # pad so short rows keep their blanks
            raw = raw + [""] * (fields - len(raw))
            rows.append(OrderedDict(zip(_names(name), raw[:fields])))
    return rows


SCHEMAS = {
    "teams.tsv": ["abbr", "name", "slug", "conference", "division"],
    "standings.tsv": [
        "abbr", "w", "l", "t", "pct", "pf", "pa", "net",
        "home", "road", "div", "div_pct", "conf", "conf_pct",
        "nonconf", "streak", "last5",
    ],
    "injuries.tsv": ["team", "player", "position", "injury", "practice", "game"],
    "sources.tsv": ["id", "title", "publisher", "url", "tier", "checked", "status", "note"],
    "schedule.tsv": ["date", "time_et", "broadcast", "away", "home", "venue", "note"],
    "depth-kc.tsv": ["unit", "slot", "player", "rank"],
    "depth-aliases.tsv": ["depthName", "reportName", "evidence"],
}


def _names(name):
    return SCHEMAS[name]


def load(name):
    return read_tsv(name, len(SCHEMAS[name]))


def load_json(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
# Derived analysis: injury burden by club and by unit
# --------------------------------------------------------------------------
def analyse_injuries(injuries, teams):
    name_of = {t["abbr"]: t["name"] for t in teams}
    by_team = defaultdict(lambda: {
        "listed": 0, "out": 0, "doubtful": 0, "questionable": 0,
        "dnp": 0, "limited": 0, "full": 0,
        "off_out": 0, "def_out": 0, "st_out": 0,
        "non_injury_out": 0,
        "groups": defaultdict(int),
        "out_players": [],
    })

    for r in injuries:
        t = by_team[r["team"]]
        t["listed"] += 1
        game = r["game"].strip().lower()
        practice = r["practice"].strip().upper()
        injury = r["injury"].strip()

        if game == "out":
            t["out"] += 1
        elif game == "doubtful":
            t["doubtful"] += 1
        elif game == "questionable":
            t["questionable"] += 1

        if practice == "DNP":
            t["dnp"] += 1
        elif practice == "LIMITED":
            t["limited"] += 1
        elif practice == "FULL":
            t["full"] += 1

        pos = r["position"].strip().upper()
        grp = POS_GROUP.get(pos, "Unclassified")
        t["groups"][grp] += 1

        if game == "out":
            if pos in OFF_POS:
                t["off_out"] += 1
            elif pos in DEF_POS:
                t["def_out"] += 1
            elif pos in SPEC_POS:
                t["st_out"] += 1
            if injury.lower().startswith("not injury related"):
                t["non_injury_out"] += 1
            t["out_players"].append({
                "player": r["player"], "position": r["position"],
                "injury": injury or "", "nonInjury": injury.lower().startswith("not injury related"),
            })

    rows = []
    for abbr, t in by_team.items():
        rows.append({
            "abbr": abbr,
            "team": name_of.get(abbr, abbr),
            "listed": t["listed"],
            "out": t["out"],
            "doubtful": t["doubtful"],
            "questionable": t["questionable"],
            "dnp": t["dnp"],
            "limited": t["limited"],
            "full": t["full"],
            "offOut": t["off_out"],
            "defOut": t["def_out"],
            "stOut": t["st_out"],
            "nonInjuryOut": t["non_injury_out"],
            "outPlayers": t["out_players"],
            "groups": dict(t["groups"]),
        })
    rows.sort(key=lambda r: (-r["out"], -r["listed"], r["abbr"]))
    return rows


def analyse_league(injuries, teams):
    total = len(injuries)
    out = sum(1 for r in injuries if r["game"].strip().lower() == "out")
    doubtful = sum(1 for r in injuries if r["game"].strip().lower() == "doubtful")
    questionable = sum(1 for r in injuries if r["game"].strip().lower() == "questionable")
    dnp = sum(1 for r in injuries if r["practice"].strip().upper() == "DNP")
    clubs = len({r["team"] for r in injuries})
    non_injury = sum(
        1 for r in injuries
        if r["injury"].strip().lower().startswith("not injury related")
    )
    return {
        "rows": total,
        "clubs": clubs,
        "clubsTotal": len(teams),
        "clubsMissing": sorted({t["abbr"] for t in teams} - {r["team"] for r in injuries}),
        "out": out,
        "doubtful": doubtful,
        "questionable": questionable,
        "dnp": dnp,
        "nonInjury": non_injury,
        "withGameStatus": out + doubtful + questionable,
    }


def analyse_depth(depth, injuries, aliases):
    """Match the KC depth chart against KC's official injury designations.

    Only OBSERVED fact is produced: whether a listed player carries a game
    status. No replacement is asserted. Name matching uses an explicit,
    source-documented alias table (data/depth-aliases.tsv) instead of fuzzy
    matching, so a near-miss between two different people can never merge rows.
    """
    status = {}
    for r in injuries:
        if r["team"] == "KC":
            status[r["player"].strip()] = {
                "game": r["game"].strip(),
                "practice": r["practice"].strip(),
                "injury": r["injury"].strip(),
            }

    def norm(s):
        return (s.lower().replace(".", "").replace("'", "").strip())

    alias = {norm(a["depthName"]): a["reportName"] for a in aliases}
    status_norm = {norm(k): v for k, v in status.items()}
    rows = []
    for d in depth:
        key = norm(d["player"])
        official_name = alias.get(key, d["player"])
        st = status_norm.get(norm(official_name))
        rows.append({
            "unit": d["unit"],
            "slot": d["slot"],
            "rank": int(d["rank"]),
            "player": d["player"],
            "officialName": official_name if official_name != d["player"] else "",
            "matched": st is not None,
            "gameStatus": st["game"] if st else "",
            "practice": st["practice"] if st else "",
            "injury": st["injury"] if st else "",
            # blank when we have no official designation for that player
            "flagged": (st is not None and st["game"].strip() != ""),
        })
    return rows


def main():
    teams = load("teams.tsv")
    standings = load("standings.tsv")
    injuries = load("injuries.tsv")
    sources = load("sources.tsv")
    schedule = load("schedule.tsv")
    depth = load("depth-kc.tsv")
    aliases = load("depth-aliases.tsv")

    questions = load_json("questions.json")
    suggestions = load_json("suggestions.json")
    requirements = load_json("requirements.json")
    strategies = load_json("strategies.json")
    flags = load_json("flags.json")

    # sanity checks: fail loudly rather than silently shipping bad data
    problems = []
    team_abbrs = {t["abbr"] for t in teams}
    for r in injuries:
        if r["team"] not in team_abbrs:
            problems.append("injuries.tsv unknown club %r" % r["team"])
        if not r["player"].strip():
            problems.append("injuries.tsv empty player name")
    for r in standings:
        if r["abbr"] not in team_abbrs:
            problems.append("standings.tsv unknown club %r" % r["abbr"])
    if len(standings) != len(teams):
        problems.append("standings.tsv has %d rows, teams.tsv has %d"
                        % (len(standings), len(teams)))
    for r in sources:
        if not r["url"].startswith("http"):
            problems.append("sources.tsv bad url %r" % r["url"])
    if problems:
        for p in problems:
            print("DATA PROBLEM:", p, file=sys.stderr)
        sys.exit(1)

    payload = OrderedDict([
        ("generated", "2026-11-14"),
        ("teams", teams),
        ("standings", standings),
        ("injuries", injuries),
        ("injuryByTeam", analyse_injuries(injuries, teams)),
        ("injuryLeague", analyse_league(injuries, teams)),
        ("sources", sources),
        ("schedule", schedule),
        ("depthKC", analyse_depth(depth, injuries, aliases)),
        ("questions", questions),
        ("suggestions", suggestions),
        ("requirements", requirements),
        ("strategies", strategies),
        ("flags", flags),
    ])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("/* GENERATED by tools/build.py — do not edit by hand.\n")
        fh.write("   Source of truth: data/*.tsv and data/*.json */\n")
        fh.write("window.DATA = ")
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write(";\n")

    verified = sum(1 for s in sources if s["status"] == "VERIFIED")
    print("wrote %s" % os.path.relpath(OUT, ROOT))
    print("  teams=%d standings=%d injuries=%d sources=%d(verified %d) schedule=%d depth=%d"
          % (len(teams), len(standings), len(injuries), len(sources),
             verified, len(schedule), len(depth)))
    print("  questions=%d suggestions=%d requirements=%d strategies=%d flags=%d"
          % (len(questions), len(suggestions), len(requirements),
             len(strategies), len(flags)))


if __name__ == "__main__":
    main()
