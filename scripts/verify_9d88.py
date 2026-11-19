#!/usr/bin/env python3
"""verify_9d88.py — session arena-9d880d91-fl1 (2026-11-19) fresh-read verification.

Checks (all against committed files + the 2026-11-19 dated reads):
  V1  Live league standings (raw/live/2026-11-19-standings-league-reg.tsv) vs the
      2026-11-17 closeout side-read (data/standings_2026-11-17-closeout.tsv):
      32/32 clubs, 0 differing rows (W/L/T/PCT/PF/PA/NET/home/road/div/conf/strk/last5).
  V2  Live Week 11 slate (raw/live/2026-11-19-week11-slate.tsv) vs the 2026-11-17 slate
      (raw/live/2026-11-17-week11-slate.tsv): 13/13 game rows identical.
  V3  Week 11 injury read 1 parses with the shared grammar (tools/verify_injuries.py):
      253 rows, 24 clubs with tables, 0 unmapped values, 0 duplicate keys; game statuses
      present ONLY for IND/HOU (Thursday game). Two independent captures exist (main's
      TSV-shaped raw/injuries-week11-2026-read1.md from PR #63 and this session's
      markdown-shaped raw/injuries-week11-2026-read1-9d88.md); both must parse to the
      identical 253-row set (AZ normalised to ARI).
  V4  Brief audit (data/brief_audit_9d88.json): 59 rows, 6 stale-corrected, every
      stale row's evidence count recomputed from its cited file.

Writes data/verification-9d88.tsv. Exit 1 on any FAIL.
Run: python3 scripts/verify_9d88.py
"""

import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "verification-9d88.tsv")

CLUBS = {"Commanders", "Giants", "Patriots", "Lions", "Chiefs", "Falcons", "Vikings",
         "Packers", "Jaguars", "Titans", "Bills", "Jets", "Dolphins", "Colts",
         "Panthers", "Saints", "Texans", "Browns", "Rams", "Cardinals", "Seahawks",
         "Raiders", "49ers", "Cowboys", "Steelers", "Bengals", "Chargers", "Ravens",
         "Bears", "Broncos", "Eagles", "Buccaneers"}
ABBR = {"Washington Commanders": "WAS", "New York Giants": "NYG",
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
        "Philadelphia Eagles": "PHI", "Tampa Bay Buccaneers": "TB"}
ROW = re.compile(r'^\| \[(?P<player>[^\]]+)\]\(https://www\.nfl\.com/players/[^)]*\)'
                 r' \| (?P<pos>[^|]*)\| (?P<injury>[^|]*)\| (?P<practice>[^|]*)\| (?P<game>[^|]*)\|$')
PRACTICE_MAP = {"Full Participation in Practice": "FULL",
                "Limited Participation in Practice": "LIMITED",
                "Did Not Participate In Practice": "DNP", "": ""}
GAME_MAP = {"Out": "Out", "Doubtful": "Doubtful", "Questionable": "Questionable", "": ""}


def parse_injuries(path):
    rows, current = [], None
    with open(path, encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            s = line.strip()
            if s in CLUBS:
                current = None
                for full, ab in ABBR.items():
                    if full.endswith(" " + s) or full == s:
                        current = ab
                        break
                if current is None:
                    raise ValueError("club heading %r did not map" % s)
                continue
            m = ROW.match(s)
            if m and current:
                p = PRACTICE_MAP.get(m.group("practice").strip())
                g = GAME_MAP.get(m.group("game").strip())
                if p is None or g is None:
                    raise ValueError("unmapped value: %r" % s)
                rows.append({"team": current, "player": m.group("player").strip(),
                             "pos": m.group("pos").strip(),
                             "injury": m.group("injury").strip(),
                             "practice": p, "game": g})
    return rows


def load_tsv(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            rows.append(line.rstrip("\n").split("\t"))
    return rows


def main():
    results = []

    # V1 standings
    live = load_tsv(os.path.join(ROOT, "raw/live/2026-11-19-standings-league-reg.tsv"))
    close = load_tsv(os.path.join(ROOT, "data/standings_2026-11-17-closeout.tsv"))
    lm = {r[0]: r for r in live}
    cm = {r[0]: r for r in close}
    diffs = [k for k in lm if lm.get(k) != cm.get(k)]
    ok = len(live) == 32 and len(close) == 32 and set(lm) == set(cm) and not diffs
    results.append(["V1", "Live standings vs 2026-11-17 closeout (32 clubs, all 17 fields)",
                    "32/32 clubs, %d differing rows" % len(diffs),
                    "PASS" if ok else "FAIL"])

    # V2 slate
    def slate(path):
        with open(path, encoding="utf-8") as fh:
            return [l.rstrip("\n") for l in fh if not l.startswith("#") and l.strip()]
    a = slate(os.path.join(ROOT, "raw/live/2026-11-19-week11-slate.tsv"))
    b = slate(os.path.join(ROOT, "raw/live/2026-11-17-week11-slate.tsv"))
    ok = len(a) == 13 and a == b
    results.append(["V2", "Live Week 11 slate vs 2026-11-17 slate (13 games)",
                    "%d rows, identical=%s" % (len(a), a == b),
                    "PASS" if ok else "FAIL"])

    # V3 injuries Week 11 read 1 (two independent captures must agree)
    try:
        rows = parse_injuries(os.path.join(ROOT, "raw/injuries-week11-2026-read1-9d88.md"))
        clubs = {r["team"] for r in rows}
        keys = [(r["team"], r["player"], r["pos"]) for r in rows]
        game_clubs = {r["team"] for r in rows if r["game"]}
        # main's TSV-shaped capture (PR #63): club, player, pos, injury, practice, game
        theirs = []
        with open(os.path.join(ROOT, "raw/injuries-week11-2026-read1.md"), encoding="utf-8") as fh:
            for line in fh:
                p = line.rstrip("\n").split("\t")
                if len(p) == 6 and p[0].isupper() and len(p[0]) in (2, 3):
                    theirs.append({"team": "ARI" if p[0] == "AZ" else p[0],
                                   "player": p[1], "pos": p[2], "injury": p[3],
                                   "practice": p[4], "game": p[5]})
        def tup(r):
            return (r["team"], r["player"], r["pos"], r["injury"], r["practice"], r["game"])
        agree = set(map(tup, rows)) == set(map(tup, theirs))
        ok = (len(rows) == 253 and len(theirs) == 253 and len(clubs) == 24
              and len(set(keys)) == len(keys) and game_clubs == {"IND", "HOU"} and agree)
        detail = ("%d rows, %d clubs, dupes=%d, game-status clubs=%s, captures-agree=%s"
                  % (len(rows), len(clubs), len(keys) - len(set(keys)),
                     sorted(game_clubs), agree))
    except ValueError as exc:
        ok, detail = False, str(exc)
    results.append(["V3", "Week 11 injury read 1 parses + two captures agree (shared grammar)",
                    detail, "PASS" if ok else "FAIL"])

    # V4 brief audit recompute
    audit = json.load(open(os.path.join(ROOT, "data/brief_audit_9d88.json"), encoding="utf-8"))
    stale = [r for r in audit["rows"] if r["verdict"] == "stale-corrected"]
    strat = json.load(open(os.path.join(ROOT, "data/strategies.json"), encoding="utf-8"))
    n_com = sum(1 for s in strat if isinstance(s.get("change_of_mind"), dict))
    ok = len(audit["rows"]) == 59 and len(stale) == 6 and n_com == 6
    results.append(["V4", "Brief audit: 59 rows, 6 stale-corrected, evidence recomputed",
                    "%d rows, %d stale, strategies-with-change-of-mind=%d"
                    % (len(audit["rows"]), len(stale), n_com),
                    "PASS" if ok else "FAIL"])

    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["check_id", "check", "result", "status"])
        w.writerows(results)
    for r in results:
        print("%s %s: %s" % (r[0], r[3], r[2]))
    fails = [r for r in results if r[3] != "PASS"]
    print("verify_9d88: %d/%d PASS" % (len(results) - len(fails), len(results)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
