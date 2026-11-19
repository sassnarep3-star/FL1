#!/usr/bin/env python3
"""Parse the Week 11 official NFL injury-hub read (read 5) into a TSV and summary.

Input : raw/injuries-week11-2026-read5.md   (verbatim capture of https://www.nfl.com/injuries/)
Output: data/injuries_2026-11-19.tsv        one row per published player row
        data/injury_hub_delta_w11.json      read metadata, counts, flags; delta = null
                                            (no earlier Week 11 read exists -> nothing like-for-like)

Rules:
  * Every value is copied from the capture. Nothing is inferred.
  * Club is taken from the team header line that precedes each table, mapped to
    the official abbreviation shown in the same game header.
  * Practice/game cells are kept raw; mapped codes are added only for the 3 published
    practice strings and the 3 published game strings. Unknown strings fail loudly.
  * Irregularities (name/link mismatch, blank game status on a player the earlier
    brief says is Out, etc.) are recorded, not corrected.

Run: python3 scripts/build_week11_read.py
"""
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "injuries-week11-2026-read5.md")
TSV = os.path.join(ROOT, "data", "injuries_2026-11-19.tsv")
OUT = os.path.join(ROOT, "data", "injury_hub_delta_w11.json")
HUB = "https://www.nfl.com/injuries/"
SOURCE_ID = "S100"

# Team header (nickname as published) -> official abbreviation shown in game header.
TEAM = {
    "Colts": "IND", "Texans": "HOU", "Steelers": "PIT", "Eagles": "PHI",
    "Cardinals": "AZ", "Chiefs": "KC", "Ravens": "BAL", "Panthers": "CAR",
    "Buccaneers": "TB", "Lions": "DET", "Dolphins": "MIA", "Bills": "BUF",
    "Titans": "TEN", "Cowboys": "DAL", "Saints": "NO", "Bears": "CHI",
    "Jets": "NYJ", "Chargers": "LAC", "Jaguars": "JAX", "Giants": "NYG",
    "Raiders": "LV", "Broncos": "DEN", "Vikings": "MIN", "49ers": "SF",
    "Bengals": "CIN", "Commanders": "WAS",
}
PRACTICE = {
    "Full Participation in Practice": "FULL",
    "Limited Participation in Practice": "LIMITED",
    "Did Not Participate In Practice": "DNP",
}
GAME = {"": "", "Questionable": "Questionable", "Out": "Out", "Doubtful": "Doubtful"}

ROW = re.compile(
    r"^\| \[(?P<player>[^\]]+)\]\((?P<url>https://www\.nfl\.com/players/[^)]*)\) \|"
    r" (?P<pos>[^|]*)\|(?P<injury>[^|]*)\|(?P<practice>[^|]*)\|(?P<game>[^|]*)\|$"
)


def main():
    lines = open(RAW, encoding="utf-8").read().splitlines()
    rows, team_lines, club = [], [], None
    pending_team = None
    no_injury_teams = []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s in TEAM:
            pending_team = s
            continue
        m = re.match(r"^(Bengals|Commanders)$", s)
        if s == "No Injuries Reported":
            no_injury_teams.append(pending_team)
            continue
        if pending_team and s.startswith("| Player | Position"):
            club = pending_team
            team_lines.append((i, club))
            continue
        mm = ROW.match(s)
        if mm:
            if club is None:
                sys.exit(f"row before team header at line {i}")
            prac_raw = mm.group("practice").strip()
            game_raw = mm.group("game").strip()
            if prac_raw not in PRACTICE:
                sys.exit(f"unmapped practice value {prac_raw!r} at line {i}")
            if game_raw not in GAME:
                sys.exit(f"unmapped game value {game_raw!r} at line {i}")
            rows.append({
                "club_abbr": TEAM[club],
                "club": club,
                "player": mm.group("player").strip(),
                "player_url": mm.group("url"),
                "pos": mm.group("pos").strip(),
                "injury": mm.group("injury").strip(),
                "practice_raw": prac_raw,
                "game_raw": game_raw,
                "practice_code": PRACTICE[prac_raw],
                "game_code": GAME[game_raw],
                "line": i,
            })
        if s.startswith("| Player | Position"):
            pending_team = None
        if re.match(r"^## (MONDAY|THURSDAY|SUNDAY)", s):
            club = None

    # Irregularities: recorded, never corrected.
    flags = []
    alnum = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
    for r in rows:
        slug = alnum(r["player_url"].rstrip("/").split("/")[-1])
        parts = r["player"].split()
        first, last = alnum(parts[0]), alnum(parts[-1])
        if last not in slug:
            flags.append({"line": r["line"], "club": r["club_abbr"], "player": r["player"],
                          "issue": "surname not in player-link slug (review link)", "url": r["player_url"]})
        elif first not in slug:
            flags.append({"line": r["line"], "club": r["club_abbr"], "player": r["player"],
                          "issue": "first name differs from player-link slug (published as-is; review)",
                          "url": r["player_url"]})
    for r in rows:
        if r["club_abbr"] == "DET" and r["player"] in {"Kerby Joseph", "Cade Mays", "D.J. Reed"} and not r["game_code"]:
            flags.append({"line": r["line"], "club": "DET", "player": r["player"],
                          "issue": "blank game status (earlier brief lists Lions designations Out; not verifiable from this read)",
                          "url": r["player_url"]})
    for r in rows:
        if r["game_raw"] == "" and r["practice_code"] == "DNP":
            flags.append({"line": r["line"], "club": r["club_abbr"], "player": r["player"],
                          "issue": "DNP in practice with blank game status (publish blank, unverified)",
                          "url": r["player_url"]})

    os.makedirs(os.path.dirname(TSV), exist_ok=True)
    cols = ["source_id", "source_url", "club_abbr", "club", "player", "pos", "injury",
            "practice_raw", "practice_code", "game_raw", "game_code", "player_url", "raw_line"]
    with open(TSV, "w", encoding="utf-8") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            vals = [SOURCE_ID, HUB, r["club_abbr"], r["club"], r["player"], r["pos"], r["injury"],
                    r["practice_raw"], r["practice_code"], r["game_raw"], r["game_code"],
                    r["player_url"], str(r["line"])]
            f.write("\t".join(v.replace("\t", " ") for v in vals) + "\n")

    per_club = Counter(r["club_abbr"] for r in rows)
    summary = {
        "id": "injury_hub_delta_w11",
        "title": "Injury-hub read 5 (Week 11 of 2026) - clock-timed, delta published",
        "requirement": "Store every injury-hub read with its clock time and publish the delta, never the level.",
        "url": HUB,
        "source_id": SOURCE_ID,
        "week_shown": "WEEK 11",
        "reads": [{
            "read": 5,
            "capture": "raw/injuries-week11-2026-read5.md",
            "chunks": "raw/.chunks-w11/chunk0-6.txt (fetch_page chunkIndex 0-6, totalChunks 7)",
            "captured": "2026-11-19 (UTC, session 0a100872; exact per-chunk fetch clock time not recorded by the fetch tool)",
            "rows": len(rows),
            "clubs_with_table": len(per_club),
            "clubs_no_injuries_reported": no_injury_teams,
            "source_id": SOURCE_ID,
        }],
        "delta": None,
        "delta_reason": "No earlier Week 11 read exists, so no like-for-like delta is published. Week 10 reads are not compared (different week).",
        "counts": {
            "practice": dict(Counter(r["practice_code"] for r in rows)),
            "game": dict(Counter(r["game_code"] or "blank" for r in rows)),
        },
        "flags": flags,
        "flag_count": len(flags),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"rows={len(rows)} clubs={len(per_club)} no_injury={no_injury_teams} flags={len(flags)}")
    print(summary["counts"])


if __name__ == "__main__":
    main()
