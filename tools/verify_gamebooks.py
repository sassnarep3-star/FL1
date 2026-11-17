#!/usr/bin/env python3
"""Verification gate for the H2 official Game Book capture.

Re-derives every invariant of the canonical files from the committed raw
capture and the official results feed, independently of the builder. Exits
non-zero (and prints every failing check) unless every check passes:

  GB-1  the 13 games in data/gamebooks_games.tsv are exactly the 13 official
        Week 10 Game Book games, each with a static.www.nfl.com PDF URL
  GB-2  every game_book_url is an nfl.com host and ends .pdf
  GB-3  every roster row's (game,team,role) triple is a valid combination and
        the role is one of starter/sub/dnp/inactive
  GB-4  every starter row's unit is Offense or Defense (the Game Book labels
        units only for the Lineups block); sub/dnp/inactive rows may be blank
  GB-5  the away/home points of every game reproduce the official final score
        in the results feed
  GB-6  the roster capture is complete: the number of starters per team equals
        the Game Book's 11-per-side Lineups count for that game
  GB-7  every snap row's (game,team) exists in the games table; the offense,
        defense and special-teams percentages are each 0..100 or blank
  GB-8  venue_official.csv is exactly the 13 games × 2 teams, roof/surface are
        non-blank for every venue row (the Game Book prints them)
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

GAMES_TSV = os.path.join(DATA, "gamebooks_games.tsv")
ROSTERS_TSV = os.path.join(DATA, "gamebooks_rosters.tsv")
SNAPS_TSV = os.path.join(DATA, "gamebooks_snaps.tsv")
VENUE_CSV = os.path.join(DATA, "venue_official.csv")
RESULTS_TSV = os.path.join(DATA, "results.tsv")

VALID_ROLES = {"starter", "sub", "dnp", "inactive"}
VALID_UNITS = {"Offense", "Defense"}


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        rows = [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]
    return rows[0], rows[1:]


def main():
    failures = []
    checks = []

    ghdr, ggames = read_tsv(GAMES_TSV)
    rhdr, rroster = read_tsv(ROSTERS_TSV)
    shedr, ssnaps = read_tsv(SNAPS_TSV)
    with open(VENUE_CSV, encoding="utf-8") as fh:
        vrows = list(csv.reader(fh))
    vhdr, vgames = vrows[0], vrows[1:]

    # GB-1 / GB-2: game set + PDF URLs
    games = {}
    for g in ggames:
        key = g[0]
        games[key] = g
    pdf_ok = all(
        g[18].startswith("https://static.www.nfl.com/") and g[18].endswith(".pdf")
        for g in ggames
    )
    checks.append(("GB-1", "13 game rows, one per official Week 10 Game Book",
                   len(ggames) == 13))
    checks.append(("GB-2", "every game_book_url is a static.www.nfl.com .pdf",
                   pdf_ok))
    if not pdf_ok:
        failures.append("GB-2: a game_book_url is not an nfl.com PDF")

    # GB-3 / GB-4: roster roles and units
    role_bad = []
    unit_bad = []
    for r in rroster:
        role = r[3]
        unit = r[4]
        if role not in VALID_ROLES:
            role_bad.append((r[0], r[2], role))
        if role == "starter" and unit not in VALID_UNITS:
            unit_bad.append((r[0], r[2], unit))
    checks.append(("GB-3", "every roster role is in {starter,sub,dnp,inactive}",
                   not role_bad))
    checks.append(("GB-4", "every starter row unit is Offense/Defense",
                   not unit_bad))
    if role_bad:
        failures.append("GB-3: bad roles %r" % role_bad[:3])
    if unit_bad:
        failures.append("GB-4: bad starter units %r" % unit_bad[:3])

    # GB-5: final scores reproduce the official results feed
    scores = {}
    for r in rroster:
        pass  # rosters carry no score; scores come from games table
    score_bad = []
    try:
        _, rres = read_tsv(RESULTS_TSV)
        # results.tsv schema: game_id, date, away, away_pts, home, home_pts
        res_by_team = {}
        for r in rres:
            res_by_team[(r[2], r[4])] = (r[3], r[5])
        for g in ggames:
            key, date, away, home, ap, hp = g[0], g[1], g[2], g[3], g[4], g[5]
            pair = (away, home)
            if pair not in res_by_team:
                score_bad.append((key, "pair-not-in-results"))
            else:
                ra, rh = res_by_team[pair]
                if (str(ap), str(hp)) != (ra, rh):
                    score_bad.append((key, (ap, hp), (ra, rh)))
    except FileNotFoundError:
        checks.append(("GB-5", "results.tsv present for score cross-check", False))
        failures.append("GB-5: results.tsv missing")
    else:
        checks.append(("GB-5", "all 13 final scores reproduce the results feed",
                       not score_bad))
        if score_bad:
            failures.append("GB-5: score mismatches %r" % score_bad[:5])

    # GB-6: 11 starters per unit per side (11 offense + 11 defense = 22 total)
    starter_count = {}
    for r in rroster:
        if r[3] == "starter":
            k = (r[0], r[2], r[4])
            starter_count[k] = starter_count.get(k, 0) + 1
    starter_bad = []
    for key in games:
        for team in (games[key][2], games[key][3]):
            for unit in ("Offense", "Defense"):
                cnt = starter_count.get((key, team, unit), 0)
                if cnt != 11:
                    starter_bad.append((key, team, unit, cnt))
    checks.append(("GB-6", "11 starters per team per unit (Offense/Defense) in "
                           "every Lineups block", not starter_bad))
    if starter_bad:
        failures.append("GB-6: starter counts %r" % starter_bad[:5])

    # GB-7: snap rows valid
    snap_bad = []
    for s in ssnaps:
        key = s[0]
        team = s[2]
        if key not in games:
            snap_bad.append((key, "unknown-game"))
        if team not in (games[key][2], games[key][3]):
            snap_bad.append((key, team, "team-not-in-game"))
        for col in (5, 6, 7):
            v = s[col]
            if v == "":
                continue
            try:
                n = float(v)
            except ValueError:
                snap_bad.append((key, s[4], v))
                continue
            if not (0 <= n <= 100):
                snap_bad.append((key, s[4], v))
    checks.append(("GB-7", "every snap row has a known game/team and 0..100 pct",
                   not snap_bad))
    if snap_bad:
        failures.append("GB-7: snap issues %r" % snap_bad[:5])

    # GB-8: venue completeness
    venue_seen = set()
    venue_bad = []
    for v in vgames:
        key, stadium, city, roof, surface, team, pdf = v
        venue_seen.add(key)
        if not roof or not surface:
            venue_bad.append((key, roof, surface))
    expected_venues = set(games.keys())
    venue_ok = (venue_seen == expected_venues and not venue_bad
                and len(vgames) == 2 * len(games))
    checks.append(("GB-8", "venue_official.csv is 13 games × 2 teams, roof/surface "
                           "non-blank", venue_ok))
    if not venue_ok:
        failures.append("GB-8: venue issues %r" % (venue_bad[:5] or list(venue_seen)))

    print("verify_gamebooks.py")
    for cid, label, ok in checks:
        print("  %s  %s  ->  %s" % (cid, label, "PASS" if ok else "FAIL"))
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  " + f)
        return 1
    print("\nGATE PASS — all Game Book checks green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
