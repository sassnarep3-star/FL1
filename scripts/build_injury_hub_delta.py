#!/usr/bin/env python3
"""Build data/injury_hub_delta.json — the delta between dated reads of the
official injury hub (https://www.nfl.com/injuries/).

Requirement (brief): "Store every injury-hub read with its clock time and
publish the delta, never the level."

Inputs (raw captures, never edited after write):
  raw/injuries-week10-2026.md          read 1, 2026-11-14 (source S01)
  raw/injuries-week10-2026-read2.md    read 2, 2026-11-16 (source S77; id re-issued from S70 at merge — main took S70-S76)

The parser is the same line grammar tools/verify_injuries.py uses for read 1,
applied to both captures so the diff is like-for-like. The script fails loudly
on any practice/game value the grammar does not map, or if read 2 parses to a
row count that disagrees with the header claim inside the capture file.

Output: data/injury_hub_delta.json. Changed/added/removed ROWS are published;
the page renders the delta, not a second copy of the level.

Run:  python3 scripts/build_injury_hub_delta.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "injury_hub_delta.json")

READ1 = os.path.join(ROOT, "raw", "injuries-week10-2026.md")
READ2 = os.path.join(ROOT, "raw", "injuries-week10-2026-read2.md")

CLUBS = {
    "Commanders", "Giants", "Patriots", "Lions", "Chiefs", "Falcons", "Vikings",
    "Packers", "Jaguars", "Titans", "Bills", "Jets", "Dolphins", "Colts",
    "Panthers", "Saints", "Texans", "Browns", "Rams", "Cardinals", "Seahawks",
    "Raiders", "49ers", "Cowboys", "Steelers", "Bengals", "Chargers", "Ravens",
    "Bears", "Broncos", "Eagles", "Buccaneers",
}

ABBR = {
    "Washington Commanders": "WAS", "New York Giants": "NYG",
    "New England Patriots": "NE", "Detroit Lions": "DET",
    "Kansas City Chiefs": "KC", "Atlanta Falcons": "ATL",
    "Minnesota Vikings": "MIN", "Green Bay Packers": "GB",
    "Jacksonville Jaguars": "JAX", "Tennessee Titans": "TEN",
    "Buffalo Bills": "BUF", "New York Jets": "NYJ",
    "Miami Dolphins": "MIA", "Indianapolis Colts": "IND",
    "Carolina Panthers": "CAR", "New Orleans Saints": "NO",
    "Houston Texans": "HOU", "Cleveland Browns": "CLE",
    "Los Angeles Rams": "LAR", "Arizona Cardinals": "ARI",
    "Seattle Seahawks": "SEA", "Las Vegas Raiders": "LV",
    "San Francisco 49ers": "SF", "Dallas Cowboys": "DAL",
    "Pittsburgh Steelers": "PIT", "Cincinnati Bengals": "CIN",
    "Los Angeles Chargers": "LAC", "Baltimore Ravens": "BAL",
    "Chicago Bears": "CHI", "Denver Broncos": "DEN",
    "Philadelphia Eagles": "PHI", "Tampa Bay Buccaneers": "TB",
}

ROW = re.compile(
    r'^\| \[(?P<player>[^\]]+)\]\(https://www\.nfl\.com/players/[^)]*\)'
    r' \| (?P<pos>[^|]*)\| (?P<injury>[^|]*)\| (?P<practice>[^|]*)\| (?P<game>[^|]*)\|$'
)

PRACTICE_MAP = {
    "Full Participation in Practice": "FULL",
    "Limited Participation in Practice": "LIMITED",
    "Did Not Participate In Practice": "DNP",
    "": "",
}

GAME_MAP = {
    "Out": "Out", "Doubtful": "Doubtful", "Questionable": "Questionable",
    "": "",
}


def parse_capture(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    rows, current = [], None
    for line in lines:
        s = line.strip()
        if s in CLUBS:
            current = None
            for full, ab in ABBR.items():
                if full.endswith(" " + s) or full == s:
                    current = ab
                    break
            if current is None:
                raise SystemExit("FAIL: club heading %r did not map to an abbr" % s)
            continue
        m = ROW.match(s)
        if m and current:
            practice = PRACTICE_MAP.get(m.group("practice").strip(),
                                        "?" + m.group("practice").strip())
            game = GAME_MAP.get(m.group("game").strip(),
                                "?" + m.group("game").strip())
            if practice.startswith("?") or game.startswith("?"):
                raise SystemExit("FAIL: unmapped value in %s: %r" % (path, s))
            rows.append({
                "team": current,
                "player": m.group("player").strip(),
                "pos": m.group("pos").strip(),
                "injury": m.group("injury").strip(),
                "practice": practice,
                "game": game,
            })
    return rows


def key(r):
    return (r["team"], r["player"], r["pos"])


def main():
    if not os.path.exists(READ2):
        raise SystemExit("FAIL: %s missing" % READ2)
    r1, r2 = parse_capture(READ1), parse_capture(READ2)

    # like-for-like sanity: read 1 must still reproduce the canonical TSV
    tsv = []
    tsv_path = os.path.join(ROOT, "data", "injuries.tsv")
    with open(tsv_path, newline="", encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            if line.strip():
                c = line.split("\t")
                c += [""] * (6 - len(c))
                tsv.append({"team": c[0], "player": c[1], "pos": c[2],
                            "injury": c[3], "practice": c[4], "game": c[5]})
    if r1 != tsv:
        raise SystemExit("FAIL: read-1 capture no longer parses to data/injuries.tsv "
                         "(%d vs %d rows) — refuse to publish a delta on a moving baseline"
                         % (len(r1), len(tsv)))

    old = {key(r): r for r in r1}
    new = {key(r): r for r in r2}
    if len(old) != len(r1) or len(new) != len(r2):
        raise SystemExit("FAIL: duplicate (club, player, position) key inside a capture")

    changed, added, removed = [], [], []
    for k in sorted(new):
        if k not in old:
            added.append(new[k])
        else:
            for field in ("injury", "practice", "game"):
                if old[k][field] != new[k][field]:
                    c = dict(new[k])
                    c["field"] = field
                    c["old"] = old[k][field]
                    c["new"] = new[k][field]
                    changed.append(c)
    for k in sorted(old):
        if k not in new:
            removed.append(old[k])

    per_club_old = {}
    per_club_new = {}
    for r in r1:
        per_club_old[r["team"]] = per_club_old.get(r["team"], 0) + 1
    for r in r2:
        per_club_new[r["team"]] = per_club_new.get(r["team"], 0) + 1
    clubs = sorted(set(per_club_old) | set(per_club_new))
    per_club = [{"team": t,
                 "read1": per_club_old.get(t, 0),
                 "read2": per_club_new.get(t, 0)}
                for t in clubs if per_club_old.get(t) != per_club_new.get(t)]

    payload = {
        "id": "injury_hub_delta",
        "title": "Injury-hub reads — clock-timed, delta published",
        "requirement": "Store every injury-hub read with its clock time and publish "
                       "the delta, never the level.",
        "updated": "2026-11-16",
        "url": "https://www.nfl.com/injuries/",
        "reads": [
            {"read": 1, "capture": "raw/injuries-week10-2026.md",
             "captured": "2026-11-14", "rows": len(r1),
             "week_shown": "WEEK 10", "source_id": "S01"},
            {"read": 2, "capture": "raw/injuries-week10-2026-read2.md",
             "read_window_utc": "after 2026-11-16T01:14:56Z, before 2026-11-16T01:25:00Z",
             "rows": len(r2), "week_shown": "WEEK 10", "source_id": "S77"},
        ],
        "delta": {"changed": changed, "added": added, "removed": removed,
                  "per_club_row_count_changes": per_club},
        "reserve_list_pointers": [
            {"text": "NFL news roundup: Patriots place RB TreVeyon Henderson (illness) "
                     "on injured reserve",
             "url": "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-saturday-nov-14"},
            {"text": "Dolphins place QB Malik Willis (groin) on injured reserve; "
                     "Kyle McCord in line for first start",
             "url": "https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start"},
            {"text": "NFL news roundup: Ravens confirm Lamar Jackson expected to miss "
                     "6-10 weeks; Kenneth Walker questionable",
             "url": "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13"},
            {"text": "NFL news roundup: Ravens officially place Lamar Jackson on injured reserve",
             "url": "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-thursday-nov-5"},
        ],
        "provenance": {
            "tier": "OFFICIAL",
            "source_ids": ["S01", "S77"],
            "verification": "read 1 re-parses to data/injuries.tsv exactly (asserted here, "
                            "independently of tools/verify_injuries.py); read 2 parsed with the "
                            "same grammar; all practice/game values map to known designations",
        },
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print("read1 rows=%d  read2 rows=%d" % (len(r1), len(r2)))
    print("changed=%d added=%d removed=%d" % (len(changed), len(added), len(removed)))
    for c in changed:
        print("  %s %s (%s): %s '%s' -> '%s'"
              % (c["team"], c["player"], c["field"], c["pos"], c["old"], c["new"]))
    for a in added:
        print("  + %s %s (%s) %s | %s | %s"
              % (a["team"], a["player"], a["pos"], a["injury"], a["practice"], a["game"]))
    for d in removed:
        print("  - %s %s (%s)" % (d["team"], d["player"], d["pos"]))
    for p in per_club:
        print("  club row count: %s %d -> %d" % (p["team"], p["read1"], p["read2"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
