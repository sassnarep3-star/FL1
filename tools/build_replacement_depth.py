#!/usr/bin/env python3
"""build_replacement_depth.py — track the DEPTH of the replacement, not just
the fact that a replacement is needed.

Inputs, both already in the repo and already verified:
    data/depth.tsv + data/depth-kc.tsv   club-published depth charts (30+1 clubs)
    data/injuries.tsv                    official Week 10 2026 injury report (S01)

Method (fully mechanical, nothing inferred):
    1. Order each (club, unit, slot) by the club's own published ordering
       (line, rank) — or rank alone for the Kansas City file. A player's
       STRING is his 1-based position in that ordering: 1st string, 2nd, 3rd...
    2. For every charted player carrying an official game status
       (Out / Doubtful / Questionable), the replacement is the next name the
       CLUB ITSELF lists at that slot who is not himself designated Out. A
       Doubtful or Questionable next man is still the listed replacement — his
       own status is recorded in a separate column, never silently skipped.
    3. depth_of_replacement = the replacement's string number. That single
       number is what the brief asks for: a 4th-string replacement is a
       different event from a 2nd-string one, and a flat 'someone is out'
       hides the difference.

Rows where the club publishes no machine-readable chart (Houston, F16) are
emitted with blank fields and a flag — never guessed.

Run:  python3 tools/build_replacement_depth.py
"""

import csv
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build  # noqa: E402

DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "replacement_depth_out.csv")

INJURY_SOURCE_ID = "S01"
INJURY_SOURCE_URL = "https://www.nfl.com/injuries/"
STATUS_TRIGGER = {"Out", "Doubtful", "Questionable"}
UNAVAILABLE_FOR_SKIP = {"Out"}   # Doubtful is recorded, not skipped: the club lists him


def norm(s):
    out = s.lower().replace(".", "").replace("'", "").replace("-", " ")
    return " ".join(out.split())


def main():
    depth = build.load("depth.tsv")
    aliases = build.load("depth-aliases.tsv")
    injuries = build.load("injuries.tsv")
    depth_sources = build.load("depth-sources.tsv")
    teams = build.load("teams.tsv")
    alias = {norm(a["depthName"]): a["reportName"] for a in aliases}
    src_of = {r["abbr"]: r for r in depth_sources}
    name_of = {t["abbr"]: t["name"] for t in teams}

    # injury index by club + normalised name
    by_club = defaultdict(dict)
    for r in injuries:
        by_club[r["team"].strip()][norm(r["player"].strip())] = r

    # group charted players
    groups = defaultdict(list)
    for d in depth:
        if not d["player"].strip():
            continue
        groups[(d["team"].strip(), d["unit"].strip(), d["slot"].strip())].append({
            "player": d["player"].strip(),
            "order": (int(d["line"] or 0), int(d["rank"] or 0)),
            "src": src_of.get(d["team"].strip(), {}),
        })
    # Kansas City's chart lives in its own file (rank = ordering)
    kc = build.load("depth-kc.tsv")
    for d in kc:
        groups[("KC", d["unit"].strip(), d["slot"].strip())].append({
            "player": d["player"].strip(),
            "order": (0, int(d["rank"] or 0)),
            "src": {"source": "S08", "url": "https://www.chiefs.com/team/depth-chart"},
        })

    rows = []
    for (team, unit, slot), plist in sorted(groups.items()):
        plist.sort(key=lambda p: p["order"])
        status = {}
        for i, p in enumerate(plist, start=1):
            p["string"] = i
            key = norm(alias.get(norm(p["player"]), p["player"]))
            st = by_club.get(team, {}).get(key)
            status[p["player"]] = st
        for i, p in enumerate(plist, start=1):
            st = status[p["player"]]
            game = (st["game"].strip() if st else "")
            if game not in STATUS_TRIGGER:
                continue
            # the replacement: the next name the club lists who is not Out
            rep = None
            for q in plist[i:]:
                qst = status[q["player"]]
                qgame = qst["game"].strip() if qst else ""
                if qgame in UNAVAILABLE_FOR_SKIP:
                    continue
                rep = q
                break
            rep_st = status[rep["player"]] if rep else None
            rows.append({
                "team": team,
                "team_name": name_of.get(team, ""),
                "unit": unit,
                "slot": slot,
                "absent_player": p["player"],
                "absent_string": p["string"],
                "absent_game_status": game,
                "absent_practice_status": st["practice"].strip() if st else "",
                "replacement_player": rep["player"] if rep else "",
                "replacement_string": rep["string"] if rep else "",
                "depth_of_replacement": rep["string"] if rep else "",
                "replacement_game_status": (rep_st["game"].strip() if rep_st else ""),
                "replacement_on_report": ("yes" if (rep_st and any(
                    (rep_st[k] or "").strip() for k in ("game", "practice", "injury"))) else
                    ("no" if rep_st is not None else "")),
                "note": ("" if rep else
                         "no further player published at this slot — replacement unknown"),
                "depth_source_id": p["src"].get("source", ""),
                "depth_source_url": p["src"].get("url", ""),
                "injury_source_id": INJURY_SOURCE_ID,
                "injury_source_url": INJURY_SOURCE_URL,
            })

    # Houston: no machine-readable chart (F16) — emit one honest blank row
    rows.append({
        "team": "HOU", "team_name": name_of.get("HOU", ""),
        "unit": "", "slot": "",
        "absent_player": "", "absent_string": "", "absent_game_status": "",
        "absent_practice_status": "",
        "replacement_player": "", "replacement_string": "",
        "depth_of_replacement": "", "replacement_game_status": "",
        "replacement_on_report": "",
        "note": "Houston publishes its depth chart as an image (F16): replacement "
                "depth cannot be derived without inference, so every field is blank",
        "depth_source_id": "S46", "depth_source_url": "https://www.houstontexans.com/team/depth-chart",
        "injury_source_id": INJURY_SOURCE_ID, "injury_source_url": INJURY_SOURCE_URL,
    })

    fields = ["team", "team_name", "unit", "slot",
              "absent_player", "absent_string", "absent_game_status",
              "absent_practice_status",
              "replacement_player", "replacement_string", "depth_of_replacement",
              "replacement_game_status", "replacement_on_report", "note",
              "depth_source_id", "depth_source_url",
              "injury_source_id", "injury_source_url"]
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

    from collections import Counter
    dist = Counter(r["depth_of_replacement"] for r in rows if r["depth_of_replacement"] != "")
    print(f"wrote {OUT}")
    print(f"  rows={len(rows)} (1 blank HOU row included)")
    print(f"  depth-of-replacement distribution (string of the next man up): {dict(sorted(dist.items()))}")


if __name__ == "__main__":
    main()
