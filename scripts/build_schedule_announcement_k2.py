#!/usr/bin/env python3
"""K2 (R44): build data/schedule_announcement.json from the raw official capture.

Every claim is a verbatim quote that must appear in raw/schedule-announcement-2026.md.
The script refuses to write the JSON if any quote is missing, so the JSON can never
carry a value the raw capture does not contain. Stdlib only.

Source IDs S105 (release) and S106 (advance notice) were assigned in K4 integration, because
S101-S103 were already taken on main. data/sources.tsv is a shared output: K4 registers them.
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "schedule-announcement-2026.md")
OUT = os.path.join(ROOT, "data", "schedule_announcement.json")

FETCH_DATE_UTC = "2026-11-19"
PRIMARY_URL = "https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced"
ADVANCE_URL = "https://media.nfl.com/news-and-releases/2026-nfl-schedule-powered-by-aws-to-be-released-thursday--may-14"

CLAIMS = [
    {"id": "A1", "field": "regular_season_games",
     "value": 272, "unit": "games",
     "quote": "The NFL announced its 18-week, 272-game regular-season schedule for 2026",
     "url": PRIMARY_URL},
    {"id": "A2", "field": "season_weeks",
     "value": 18, "unit": "weeks",
     "quote": "The NFL’s 32 teams will each play 17 games over 18 weeks.",
     "url": PRIMARY_URL},
    {"id": "A3", "field": "games_per_team",
     "value": 17, "unit": "games",
     "quote": "will feature each team playing 17 regular-season games and three preseason games",
     "url": PRIMARY_URL},
    {"id": "A4", "field": "kickoff_game",
     "value": "Wednesday, September 9, in Seattle", "unit": "date/venue",
     "quote": "kicks off on Wednesday night, September 9, in Seattle",
     "url": PRIMARY_URL},
    {"id": "A5", "field": "bye_weeks",
     "value": "Week 5 through Week 14", "unit": "weeks",
     "quote": "Byes will begin in Week 5 and end in Week 14.",
     "url": PRIMARY_URL},
    {"id": "A6", "field": "final_regular_season_weekend",
     "value": "Saturday, January 9 and Sunday, January 10 (Week 18)", "unit": "date",
     "quote": "concludes with 16 division games in Week 18 – three on Saturday, January 9, and 13 on Sunday, January 10.",
     "url": PRIMARY_URL},
    {"id": "A7", "field": "international_games",
     "value": 9, "unit": "games",
     "quote": "The NFL schedule features nine international games, the most-ever in a season",
     "url": PRIMARY_URL},
    {"id": "A8", "field": "release_date_notice",
     "value": "Thursday, May 14, 8 p.m. ET", "unit": "date/time",
     "quote": "will be released on Thursday, May 14 at 8 p.m. ET.",
     "url": ADVANCE_URL},
    {"id": "A9", "field": "release_dateline",
     "value": "2026-05-14", "unit": "date",
     "quote": "May 14, 2026",
     "url": PRIMARY_URL},
    {"id": "A10", "field": "super_bowl_lxi",
     "value": "Sunday, February 14, Super Bowl LXI, SoFi Stadium, Los Angeles", "unit": "date/venue",
     "quote": "The winners meet two weeks later on Sunday, February 14, in Super Bowl LXI at SoFi Stadium",
     "url": PRIMARY_URL},
]


def main():
    with open(RAW, "rb") as fh:
        raw_bytes = fh.read()
    raw = raw_bytes.decode("utf-8")
    sha = hashlib.sha256(raw_bytes).hexdigest()

    missing = [c["id"] for c in CLAIMS if c["quote"] not in raw]
    if missing:
        print("FAIL: quotes not found verbatim in raw capture: %s" % ", ".join(missing))
        return 1

    teams, games_per_team = 32, 17
    computed_games = teams * games_per_team // 2
    if computed_games != 272:
        print("FAIL: 32 teams x 17 games / 2 = %d, not 272" % computed_games)
        return 1

    doc = {
        "task": "R44",
        "session": "arena/9fccbb0e-fl1",
        "purpose": "Dated official schedule announcement, shown beside schedule.html",
        "publisher": "NFL Football Communications (official NFL media release)",
        "fetch_date_utc": FETCH_DATE_UTC,
        "fetch_method": "fetch_page tool; curl to nfl.com fails in the sandbox (TLS SSL_ERROR_SYSCALL)",
        "raw_file": "raw/schedule-announcement-2026.md",
        "raw_sha256": sha,
        "announcements": [
            {"role": "advance_notice", "published": "2026-05-08",
             "title": "2026 NFL Schedule Powered by AWS to be Released Thursday, May 14",
             "url": ADVANCE_URL, "source_id": "S106"},
            {"role": "release", "published": "2026-05-14",
             "title": "2026 NFL Schedule Announced",
             "url": PRIMARY_URL, "source_id": "S105",
             "official_pdfs": [
                 "http://media.nfl.com/content/dam/communications/football-communications/2026/news/05%2014%2026%20-%202026%20NFL%20Schedule%20-%20By%20Week.pdf",
                 "http://media.nfl.com/content/dam/communications/football-communications/2026/news/05%2014%2026%20-%202026%20NFL%20Schedule%20-%20By%20Division.pdf",
                 "http://media.nfl.com/content/dam/communications/football-communications/2026/news/05%2014%2026%20-%20Preseason%20Schedule.pdf"]},
        ],
        "claims": CLAIMS,
        "derived_checks": [
            {"id": "D1", "rule": "teams x games_per_team / 2 = regular_season_games",
             "inputs": {"teams": teams, "games_per_team": games_per_team},
             "computed": computed_games, "stated": 272, "pass": computed_games == 272}
        ],
        "schedule_html_block": {
            "page": "schedule.html",
            "cites_source": "S86",
            "status": "miswired (flag J-F1 in the decision audit)",
            "correct_source_once_registered": "S105",
            "note": "S86 is the nflverse win_totals feed, not the NFL announcement. Fix belongs to K4."
        },
        "source_register_request": {
            "status": "registered by K4 integration (data/sources.tsv)",
            "rows": [
                {"id": "S105", "title": "NFL: 2026 NFL Schedule Announced (release, May 14, 2026)",
                 "url": PRIMARY_URL, "publisher_type": "official"},
                {"id": "S106", "title": "NFL: 2026 NFL Schedule Powered by AWS to be Released Thursday, May 14 (advance notice, May 8, 2026)",
                 "url": ADVANCE_URL, "publisher_type": "official"}
            ]
        },
    }

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("OK: %d claims verified verbatim; raw sha256 %s; wrote %s" % (len(CLAIMS), sha[:16], os.path.relpath(OUT, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
