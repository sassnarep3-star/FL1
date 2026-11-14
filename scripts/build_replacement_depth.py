#!/usr/bin/env python3
"""Build data/replacement_depth.tsv (requirement R26).

"Track the depth of the replacement, not just the fact of a replacement."

For every (club, unit, position slot) on a published depth chart where the
first string carries an official OUT game status, this walks the club's own
chart downward — rank 2, then 3, then 4 — and records WHICH STRING the next
actually available player is. A club missing its starter AND its backup is not
the same problem as a club missing only its starter, and this file is what
makes that difference visible.

Observed facts only:
  * the chart order and string numbers (club-published, S07/S08/S16..S46)
  * the game status (official injury report, S01)
Nothing about who WILL play is asserted: no snap-count source is verified.
A string is "unavailable" only on an official OUT designation; Doubtful and
Questionable are carried as notes, never treated as absent.

Output columns:
  team, unit, slot, line, missing_players (strings forced out),
  replacement, replacement_depth (string number of the replacement),
  replacement_status (the official report says nothing about this player ->
  'not listed'), note, source_chart, source_injury

Run:  python3 scripts/build_replacement_depth.py
"""

import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build  # noqa: E402

DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "replacement_depth.tsv")
HEADER = ("team\tunit\tslot\tline\tmissing_strings\tmissing_players\t"
          "replacement\treplacement_depth\treplacement_game_status\tnote\t"
          "source_chart\tsource_injury\n")


def main() -> int:
    teams = build.load("teams.tsv")
    injuries = build.load("injuries.tsv")
    aliases = build.load("depth-aliases.tsv")
    depth_league = build.analyse_depth_league(
        build.load("depth.tsv"), build.load("depth-sources.tsv"),
        injuries, teams, aliases,
        extra=[("KC", build.analyse_depth(build.load("depth-kc.tsv"),
                                          injuries, aliases))])
    rows = depth_league["rows"]

    groups = defaultdict(list)
    for r in rows:
        groups[(r["team"], r["unit"], r["slot"], r["line"])].append(r)

    out_lines = [HEADER]
    summary = defaultdict(lambda: {"rows": 0, "deepest": 1})
    for key in sorted(groups):
        team, unit, slot, line = key
        ordered = sorted(groups[key], key=lambda r: r["rank"])
        out_ranks = []
        uncertain = []
        for r in ordered:
            gs = (r["gameStatus"] or "").strip().lower()
            if gs == "out" and r["player"]:
                out_ranks.append(r)
            elif gs in ("doubtful", "questionable") and r["player"]:
                uncertain.append(r)
        if not out_ranks:
            continue          # nothing missing at this slot
        unavailable = {r["rank"] for r in out_ranks}
        replacement = None
        for r in ordered:
            if r["rank"] not in unavailable and r["player"]:
                replacement = r
                break
        missing_strings = ",".join(str(r["rank"]) for r in out_ranks)
        missing_players = "; ".join("%s (%s)" % (r["player"], r["rank"])
                                    for r in out_ranks)
        note = ""
        if uncertain:
            note = "also uncertain: " + "; ".join(
                "%s (%s, %s)" % (r["player"], r["rank"], r["gameStatus"])
                for r in uncertain)
        starter = ordered[0] if ordered and ordered[0]["rank"] == 1 else None
        starter_out = bool(starter and (starter["gameStatus"] or "").strip().lower() == "out")
        if not starter_out and replacement is not None and replacement["rank"] == 1:
            note = ("contingent: starter healthy; if lost, the next available "
                    "is string %s" % replacement["rank"]) + (" | " + note if note else "")
        if replacement is None:
            rep, depth, gs = "", "", "no charted player left"
            note = (note + " | " if note else "") + \
                "every charted string at this slot carries an OUT designation"
        else:
            rep, depth, gs = replacement["player"], str(replacement["rank"]), \
                (replacement["gameStatus"] or "").strip() or "not listed"
        src_chart = next((r.get("source", "") for r in ordered if r.get("source")), "")
        out_lines.append("\t".join([
            team, unit, slot, line, missing_strings, missing_players,
            rep, depth, gs, note, src_chart, "S01"]) + "\n")
        summary[team]["rows"] += 1
        if depth and depth.isdigit():
            summary[team]["deepest"] = max(summary[team]["deepest"], int(depth))

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.writelines(out_lines)

    n = len(out_lines) - 1
    deep = sum(1 for l in out_lines[1:] if l.split("\t")[7] in ("3", "4"))
    print("wrote %s: %d affected slots (%d whose next available player is "
          "string 3 or deeper)" % (OUT, n, deep))
    for team in sorted(summary):
        s = summary[team]
        if s["deepest"] >= 3:
            print("  %s: %d affected slots, deepest available string %d"
                  % (team, s["rows"], s["deepest"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
