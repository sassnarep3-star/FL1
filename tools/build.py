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
    "depth.tsv": ["team", "unit", "slot", "player", "rank", "line", "note"],
    "depth-sources.tsv": ["abbr", "source", "url", "chartDate", "note"],
    "results.tsv": ["week", "date", "away", "awayPts", "home", "homePts"],
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


def _norm_name(s):
    """Normalisation used ONLY to decide whether two strings are the same name.

    It is deliberately weak: lowercase, drop periods and apostrophes, collapse
    whitespace. It never tries to guess that two different strings are the same
    person. A near miss therefore shows up as "not listed" rather than as a
    wrong match, and the alias table in data/depth-aliases.tsv is the only place
    where an equivalence is asserted (with evidence).
    """
    out = s.lower().replace(".", "").replace("'", "").replace("-", " ")
    return " ".join(out.split())


def analyse_depth_league(depth, depth_sources, injuries, teams, aliases, extra=()):
    """Join every club's published depth chart to that club's official injury report.

    Three products, all observed:

    1. rows      - one per published (club, slot, string) with whatever the club's
                   own injury report says about that player this week.
    2. nextUp    - where the club's FIRST string at a slot carries an official game
                   status, the next name the club itself lists at that same slot and
                   string number. This is a statement about what the club published,
                   not about who will play: no snap-count source was verified.
    3. notOnChart- players who appear on a club's official injury report but nowhere
                   on that club's published chart. Published as a discrepancy to
                   review, never silently reconciled.
    """
    name_of = {t["abbr"]: t["name"] for t in teams}
    src_of = {r["abbr"]: r for r in depth_sources}

    # injury report, indexed by club then normalised name
    by_club = defaultdict(dict)
    for r in injuries:
        by_club[r["team"]][_norm_name(r["player"])] = {
            "player": r["player"].strip(),
            "game": r["game"].strip(),
            "practice": r["practice"].strip(),
            "injury": r["injury"].strip(),
            "position": r["position"].strip(),
        }

    alias = {_norm_name(a["depthName"]): a["reportName"] for a in aliases}

    rows = []
    # Clubs whose chart is captured in its own file (Kansas City, with a
    # source-documented alias table) are folded in so the league view is honest
    # about how many clubs it actually covers.
    for team_abbr, kc_rows in extra:
        # data/depth-kc.tsv is a FLAT capture with no line column: under one
        # slot label the club can publish more than one ladder (two DT groups,
        # three LB groups, ...), recorded as a sequence whose string numbering
        # restarts at 1. A new ladder therefore begins exactly where the
        # club's own numbering restarts (rank drops below the previous rank).
        # Nothing is reordered and no player is matched across ladders; the
        # rule is arithmetic on the published ordering only.
        ladder_no = {}
        last_rank = {}
        for r in kc_rows:
            slot_key = (r["unit"], r["slot"])
            rank = int(r["rank"])
            if slot_key not in ladder_no:
                ladder_no[slot_key] = 1
            elif rank < last_rank[slot_key]:
                ladder_no[slot_key] += 1
            last_rank[slot_key] = rank
            rows.append(OrderedDict([
                ("team", team_abbr),
                ("unit", r["unit"]),
                ("slot", r["slot"]),
                ("line", str(ladder_no[slot_key])),
                ("rank", r["rank"]),
                ("player", r["player"]),
                ("note", ("official roster spelling: %s" % r["officialName"])
                         if r["officialName"] else ""),
                ("matched", r["matched"]),
                ("practice", r["practice"]),
                ("injury", r["injury"]),
                ("gameStatus", r["gameStatus"]),
                ("source", "S08"),
            ]))
    for d in depth:
        team = d["team"].strip()
        player = d["player"].strip()
        st = None
        if player:
            key = _norm_name(alias.get(_norm_name(player), player))
            st = by_club.get(team, {}).get(key)
        rows.append(OrderedDict([
            ("team", team),
            ("unit", d["unit"]),
            ("slot", d["slot"]),
            ("line", d["line"].strip()),
            ("rank", int(d["rank"])),
            ("player", player),
            ("note", d["note"].strip()),
            ("matched", st is not None),
            ("practice", st["practice"] if st else ""),
            ("injury", st["injury"] if st else ""),
            ("gameStatus", st["game"] if st else ""),
            ("source", src_of.get(team, {}).get("source", "")),
        ]))

    # --- per club summary -------------------------------------------------
    slots_by_club = defaultdict(lambda: defaultdict(list))
    for r in rows:
        slots_by_club[r["team"]][(r["unit"], r["slot"], r["line"])].append(r)

    clubs = []
    for abbr in sorted(slots_by_club):
        grp = slots_by_club[abbr]
        named = [r for r in rows if r["team"] == abbr and r["player"]]
        matched = [r for r in named if r["matched"]]
        games = [r for r in named if r["gameStatus"].strip()]
        src = src_of.get(abbr, {})
        clubs.append(OrderedDict([
            ("abbr", abbr),
            ("team", name_of.get(abbr, abbr)),
            ("source", src.get("source", "")),
            ("url", src.get("url", "")),
            ("chartDate", src.get("chartDate", "")),
            ("note", src.get("note", "")),
            ("slots", len(grp)),
            ("named", len(named)),
            ("matched", len(matched)),
            ("withGameStatus", len(games)),
            ("out", sum(1 for r in named if r["gameStatus"].strip().lower() == "out")),
            ("doubtful", sum(1 for r in named if r["gameStatus"].strip().lower() == "doubtful")),
            ("questionable", sum(1 for r in named if r["gameStatus"].strip().lower() == "questionable")),
            ("blankSlots", sum(1 for r in rows
                               if r["team"] == abbr and not r["player"])),
        ]))

    # --- next listed at the same slot --------------------------------------
    next_up = []
    for abbr in sorted(slots_by_club):
        for (unit, slot, line), group in sorted(slots_by_club[abbr].items()):
            ordered = sorted(group, key=lambda r: r["rank"])
            first = [r for r in ordered if r["rank"] == 1]
            for f in first:
                gs = f["gameStatus"].strip()
                if gs == "" or not f["player"]:
                    continue
                deeper = [r for r in ordered if r["rank"] > 1 and r["player"]]
                deeper.sort(key=lambda r: r["rank"])
                nxt = deeper[0] if deeper else None
                next_up.append(OrderedDict([
                    ("team", abbr),
                    ("club", name_of.get(abbr, abbr)),
                    ("unit", unit),
                    ("slot", slot),
                    ("line", line),
                    ("starter", f["player"]),
                    ("starterStatus", gs),
                    ("starterPractice", f["practice"]),
                    ("starterInjury", f["injury"]),
                    ("nextPlayer", nxt["player"] if nxt else ""),
                    ("nextString", nxt["rank"] if nxt else ""),
                    ("nextGameStatus", nxt["gameStatus"] if nxt else ""),
                    ("source", f["source"]),
                ]))

    # --- on the injury report but not on the club's own chart ---------------
    not_on_chart = []
    for abbr in sorted(by_club):
        if abbr not in slots_by_club:
            continue  # club with no chart captured; not counted as a discrepancy
        charted = {_norm_name(alias.get(_norm_name(r["player"]), r["player"]))
                   for r in rows if r["team"] == abbr and r["player"]}
        for key, st in sorted(by_club[abbr].items()):
            if key not in charted:
                not_on_chart.append(OrderedDict([
                    ("team", abbr),
                    ("club", name_of.get(abbr, abbr)),
                    ("player", st["player"]),
                    ("position", st["position"]),
                    ("practice", st["practice"]),
                    ("injury", st["injury"]),
                    ("gameStatus", st["game"]),
                    ("source", src_of.get(abbr, {}).get("source", "")),
                ]))

    covered = sorted(slots_by_club)
    all_abbrs = [t["abbr"] for t in teams]
    missing = [a for a in all_abbrs if a not in slots_by_club]

    return OrderedDict([
        ("coverage", OrderedDict([
            ("covered", len(covered)),
            ("total", len(all_abbrs)),
            ("missing", missing),
            ("kcFrom", "depth-kc.tsv"),
        ("extra", [a for a, _ in extra]),
        ])),
        ("clubs", clubs),
        ("rows", rows),
        ("nextUp", next_up),
        ("notOnChart", not_on_chart),
        ("totals", OrderedDict([
            ("rows", len(rows)),
            ("named", sum(1 for r in rows if r["player"])),
            ("matched", sum(1 for r in rows if r["player"] and r["matched"])),
            ("withGameStatus", sum(1 for r in rows if r["player"] and r["gameStatus"].strip())),
            ("starters", sum(1 for r in rows if r["player"] and r["rank"] == 1)),
            ("startersWithStatus", len(next_up)),
            ("blankSlots", sum(1 for r in rows if not r["player"])),
        ])),
    ])


def replacement_depth(rows):
    """Replacement depth: how deep a club's OWN published chart must be read,
    on each ladder, to reach the first name the league has not ruled Out.

    Pure document arithmetic: a chart ladder (team, unit, slot, line) joined to
    that club's official injury-report game status. It never asserts who will
    play — no snap-count source was verified (flag F09).

    Population: ladders whose first string carries at least one official game
    status — the same population as next_up in analyse_depth_league(), so the
    two tables on the page can be read against each other.

    Two depths are reported per ladder, each walking the club's own string
    order from string 1:

    * depthOut   — string number of the first charted name whose game status is
                   not "Out". String 1 counts, so a Questionable or Doubtful
                   first string gives depth 1 (no replacement past the first
                   string is required by the documents). Blank with a reason
                   when the club publishes no name at an earlier string, or
                   when every charted name on the ladder is ruled Out.
    * depthClear — string number of the first charted name with NO game status
                   listed at all. Blank with a reason when none exists.

    A ladder where a DEEPER string is ruled Out while the first string is not
    ("thin": a deeper replacement is already unavailable) is returned
    separately, whether or not the ladder is in the population.

    Returns an OrderedDict with two lists: "ladders" (population) and "thin".
    """
    ladders = defaultdict(list)
    for r in rows:
        if r["player"]:
            ladders[(r["team"], r["unit"], r["slot"], r["line"])].append(r)

    def walk(group, excluded, excluded_label):
        """First string on the ladder that is not fully excluded.
        Returns (depth, row, reason): depth/row are None when unresolvable."""
        ranks = sorted({r["rank"] for r in group})
        if not ranks or ranks[0] != 1:
            return None, None, "the club publishes no first string on this ladder"
        for k in range(1, max(ranks) + 1):
            level = [r for r in group if r["rank"] == k]
            if not level:
                return None, None, "the club publishes no name at string %d" % k
            for r in level:
                if not excluded(r):
                    return k, r, ""
        return None, None, "every charted name on this ladder is %s" % excluded_label

    def sort_key(k):
        return (k[0], k[1], k[2], int(k[3]) if k[3].isdigit() else 99)

    def fmt(r):
        st = r["gameStatus"].strip()
        return "%s (%s)" % (r["player"], st if st else "no designation")

    population = []
    thin = []
    for key in sorted(ladders, key=sort_key):
        team, unit, slot, line = key
        # stable sort: within one string, the club's own chart order is kept
        group = sorted(ladders[key], key=lambda r: r["rank"])
        first = [r for r in group if r["rank"] == 1]
        if not first:
            continue

        is_out = lambda r: r["gameStatus"].strip().lower() == "out"
        has_status = lambda r: r["gameStatus"].strip() != ""

        # --- thin: an available first string, but a deeper string ruled Out
        deeper_out = [r for r in group if r["rank"] > 1 and is_out(r)]
        if deeper_out and any(not is_out(r) for r in first):
            thin.append(OrderedDict([
                ("team", team),
                ("unit", unit),
                ("slot", slot),
                ("line", line),
                ("firstString", "; ".join(fmt(r) for r in first)),
                ("deeperOut", "; ".join("string %d %s" % (r["rank"], r["player"])
                                        for r in deeper_out)),
                ("source", group[0]["source"]),
            ]))

        if not any(has_status(r) for r in first):
            continue  # not in the replacement-depth population

        depth_out, row_out, reason_out = walk(group, is_out, "ruled Out")
        depth_clear, row_clear, reason_clear = walk(
            group, has_status, "listed with a game status")

        population.append(OrderedDict([
            ("team", team),
            ("unit", unit),
            ("slot", slot),
            ("line", line),
            ("firstString", "; ".join(fmt(r) for r in first)),
            ("ruledOut", "; ".join("string %d %s" % (r["rank"], r["player"])
                                   for r in group if is_out(r))),
            ("depthOut", depth_out if depth_out is not None else ""),
            ("depthOutReason", reason_out),
            ("firstNotOut", fmt(row_out) if row_out else ""),
            ("depthClear", depth_clear if depth_clear is not None else ""),
            ("depthClearReason", reason_clear),
            ("firstClear", fmt(row_clear) if row_clear else ""),
            ("source", group[0]["source"]),
        ]))

    return OrderedDict([("ladders", population), ("thin", thin)])


def main():
    teams = load("teams.tsv")
    standings = load("standings.tsv")
    injuries = load("injuries.tsv")
    sources = load("sources.tsv")
    schedule = load("schedule.tsv")
    depth = load("depth-kc.tsv")
    aliases = load("depth-aliases.tsv")
    depth_all = load("depth.tsv")
    depth_sources = load("depth-sources.tsv")
    depth_kc_rows = analyse_depth(depth, injuries, aliases)

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
    results = load("results.tsv")
    for r in results:
        for abbr in (r["away"], r["home"]):
            if abbr not in team_abbrs:
                problems.append("results.tsv unknown club %r" % abbr)
        if r["awayPts"].strip() == "" or r["homePts"].strip() == "":
            problems.append("results.tsv missing score: %s @ %s week %s"
                            % (r["away"], r["home"], r["week"]))
    for r in sources:
        if not r["url"].startswith("http"):
            problems.append("sources.tsv bad url %r" % r["url"])
    for r in depth_all:
        if r["team"] not in team_abbrs:
            problems.append("depth.tsv unknown club %r" % r["team"])
        if r["slot"].strip() == "":
            problems.append("depth.tsv empty slot for %r" % r["team"])
        try:
            int(r["rank"])
        except ValueError:
            problems.append("depth.tsv non-numeric rank %r" % r["rank"])
    for r in depth_sources:
        if r["abbr"] not in team_abbrs:
            problems.append("depth-sources.tsv unknown club %r" % r["abbr"])
        if r["source"] not in {s2["id"] for s2 in sources}:
            problems.append("depth-sources.tsv source %r not in sources.tsv" % r["source"])
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
        ("results", results),
        ("depthKC", depth_kc_rows),
        ("depthLeague", analyse_depth_league(
            depth_all, depth_sources, injuries, teams, aliases,
            extra=[("KC", depth_kc_rows)])),
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
