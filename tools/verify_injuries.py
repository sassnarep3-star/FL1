#!/usr/bin/env python3
"""
verify_injuries.py — re-verifies data/injuries.tsv line by line against the
raw page capture stored in raw/injuries-week10-2026.md.

This is the "verify line by line" artefact. It does not trust the TSV and it
does not trust the capture: it parses the capture independently, rebuilds the
player table, and diffs it against the TSV. Any row present in one and missing
in the other, or any field that differs, is reported.

Run:  python3 tools/verify_injuries.py
"""

import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "injuries-week10-2026.md")
TSV = os.path.join(ROOT, "data", "injuries.tsv")

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
    "Out": "Out",
    "Doubtful": "Doubtful",
    "Questionable": "Questionable",
    "": "",
}


def parse_raw():
    with open(RAW, encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    rows = []
    current_team = None
    for line in lines:
        s = line.strip()
        # club heading line, e.g. "Commanders" alone on a line
        if s in CLUBS:
            current_team = ABBR.get("__" + s, None)
            # map short name -> abbr
            for full, ab in ABBR.items():
                if full.endswith(" " + s) or full == s:
                    current_team = ab
                    break
            continue
        m = ROW.match(s)
        if m and current_team:
            rows.append((
                current_team,
                m.group("player").strip(),
                m.group("pos").strip(),
                m.group("injury").strip(),
                PRACTICE_MAP.get(m.group("practice").strip(), "?" + m.group("practice").strip()),
                GAME_MAP.get(m.group("game").strip(), "?" + m.group("game").strip()),
            ))
    return rows


def parse_tsv():
    rows = []
    with open(TSV, newline="", encoding="utf-8") as fh:
        for r in csv.reader(fh, delimiter="\t"):
            if not r or all(c.strip() == "" for c in r):
                continue
            r = r + [""] * (6 - len(r))
            rows.append((r[0].strip(), r[1].strip(), r[2].strip(), r[3].strip(),
                         r[4].strip(), r[5].strip()))
    return rows


def main():
    raw = parse_raw()
    tsv = parse_tsv()

    print("rows parsed from raw capture : %d" % len(raw))
    print("rows in data/injuries.tsv    : %d" % len(tsv))

    problems = []

    # exact ordered comparison, because the TSV is meant to preserve page order
    if raw != tsv:
        n = max(len(raw), len(tsv))
        for i in range(n):
            a = raw[i] if i < len(raw) else None
            b = tsv[i] if i < len(tsv) else None
            if a != b:
                problems.append("line %d:\n    raw=%r\n    tsv=%r" % (i + 1, a, b))

    bad = [r for r in raw if r[4].startswith("?") or r[5].startswith("?")]
    for r in bad:
        problems.append("unmapped practice/game value: %r" % (r,))

    if problems:
        print("\n%d PROBLEM(S):" % len(problems), file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        return 1

    # independent recount of the headline figures
    out = sum(1 for r in raw if r[5] == "Out")
    doubt = sum(1 for r in raw if r[5] == "Doubtful")
    q = sum(1 for r in raw if r[5] == "Questionable")
    dnp = sum(1 for r in raw if r[4] == "DNP")
    clubs = len({r[0] for r in raw})
    noninj = sum(1 for r in raw if r[3].lower().startswith("not injury related"))
    print("\nrecount from the raw capture (independent of build.py):")
    print("  rows=%d clubs=%d out=%d doubtful=%d questionable=%d dnp=%d non_injury=%d"
          % (len(raw), clubs, out, doubt, q, dnp, noninj))
    print("\nOK: every row in data/injuries.tsv matches the raw capture exactly, "
          "in the same order, field for field.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
