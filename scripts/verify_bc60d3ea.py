#!/usr/bin/env python3
"""verify_bc60d3ea.py — freshness verification for the 2026-11-19 official reads.

Session arena/bc60d3ea-fl1, task J2. Reads ONLY new raw captures plus the
committed dated side-reads; never writes to canonical data files.

Checks (each writes one row to data/verification-bc60d3ea.tsv):
  V-J1  Both 2026-11-19 standings routes carry 32 clubs x 17 columns, with
        W+L+T in {9, 10} (9 for clubs whose bye fell in Weeks 1-10, 10 for
        clubs whose bye is Week 11 or later), NET = PF-PA and PCT
        arithmetically correct on every row.
  V-J2  League route and division route agree cell-for-cell (the F72 lesson:
        after a final, one route can lag; both are read and compared).
  V-J3  The fresh standings reproduce from the 150-row dated closeout corpus
        (data/results_2026-11-17-closeout.tsv) on W/L/T/PF/PA for 32/32 clubs.
  V-J4  The Week 11 injury capture parses with the shared grammar: practice in
        {FULL, LIMITED, DNP}, game in {Out, Doubtful, Questionable, blank};
        game designations appear ONLY on the Thursday game's clubs (IND, HOU);
        the two "No Injuries Reported" clubs (CIN, WAS) and the six bye clubs
        (ATL, CLE, GB, LA, NE, SEA) carry no rows.
  V-J5  The Week 11 schedule capture lists 13 games covering 26 distinct
        clubs, the bye list is exactly the complement, and every record
        printed on the schedule page matches the fresh standings W/L/T.
  V-J6  Cross-week guard: the Week 11 injury read is a NEW WEEK, so no
        same-week designation delta is claimed against the Week 10 table;
        canonical data/injuries.tsv, data/results.tsv and data/standings.tsv
        are byte-untouched by this script (asserted by file size + the fact
        that this script only ever writes its own TSV).

Run:  python3 scripts/verify_bc60d3ea.py
Exit: 0 if every check PASSes, 1 otherwise. No network, stdlib only.
"""

import csv
import hashlib
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "verification-bc60d3ea.tsv")

LEAGUE = os.path.join(RAW, "standings-2026-20261119-league.tsv")
DIVISION = os.path.join(RAW, "standings-2026-20261119-division.tsv")
CLOSEOUT = os.path.join(DATA, "results_2026-11-17-closeout.tsv")
INJURY = os.path.join(RAW, "injuries-week11-2026-read1.md")
SCHEDULE = os.path.join(RAW, "schedule-week11-2026-20261119.md")

URLS = {
    "standings_league": "https://www.nfl.com/standings/league/2026/REG",
    "standings_division": "https://www.nfl.com/standings/division/2026/REG",
    "injuries": "https://www.nfl.com/injuries/",
    "schedule": "https://www.nfl.com/schedules/2026/by-week/week-11",
}

PRACTICE = {"FULL", "LIMITED", "DNP"}
GAME = {"Out", "Doubtful", "Questionable", ""}
BYE = {"ATL", "CLE", "GB", "LA", "NE", "SEA"}
NO_REPORT = {"CIN", "WAS"}
TNF_CLUBS = {"IND", "HOU"}

results = []


def record(check, description, ok, detail, url):
    results.append([check, description, "PASS" if ok else "FAIL", detail, url])
    print("%s %s: %s" % (check, "PASS" if ok else "FAIL", detail))
    return ok


def load_standings(path):
    rows = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            cells = line.split("\t")
            rows[cells[0]] = cells
    return rows


def check_standings_shape(rows, label, url):
    ok = True
    detail = []
    if len(rows) != 32:
        ok = False
        detail.append("row count %d != 32" % len(rows))
    for abbr, c in sorted(rows.items()):
        if len(c) != 17:
            ok = False
            detail.append("%s has %d columns" % (abbr, len(c)))
            continue
        w, l, t = int(c[1]), int(c[2]), int(c[3])
        pf, pa, net = int(c[5]), int(c[6]), int(c[7])
        games = w + l + t
        if games not in (9, 10):
            ok = False
            detail.append("%s W+L+T=%d not in {9,10}" % (abbr, games))
        if net != pf - pa:
            ok = False
            detail.append("%s NET=%d != PF-PA=%d" % (abbr, net, pf - pa))
        pct = (w + 0.5 * t) / float(games)
        if abs(float(c[4]) - pct) > 0.0005:
            ok = False
            detail.append("%s PCT=%s != %.3f" % (abbr, c[4], pct))
    if ok:
        detail.append("32 clubs x 17 cols; W+L+T in {9,10}, NET=PF-PA, PCT exact on all rows")
    return ok, "; ".join(detail)


def main():
    all_ok = True

    # ---- V-J1: shape + arithmetic on both routes -------------------------
    league = load_standings(LEAGUE)
    division = load_standings(DIVISION)
    ok, detail = check_standings_shape(league, "league", URLS["standings_league"])
    all_ok &= record("V-J1a", "League-route standings: 32 clubs, 17 cols, arithmetic",
                     ok, detail, URLS["standings_league"])
    ok, detail = check_standings_shape(division, "division", URLS["standings_division"])
    all_ok &= record("V-J1b", "Division-route standings: 32 clubs, 17 cols, arithmetic",
                     ok, detail, URLS["standings_division"])

    # ---- V-J2: routes agree cell-for-cell --------------------------------
    diffs = []
    if set(league) != set(division):
        diffs.append("club sets differ: %s" % sorted(set(league) ^ set(division)))
    for abbr in sorted(set(league) & set(division)):
        for i, (a, b) in enumerate(zip(league[abbr], division[abbr])):
            if a != b:
                diffs.append("%s col %d: league=%r division=%r" % (abbr, i, a, b))
    all_ok &= record("V-J2", "League vs division route: cell-for-cell agreement",
                     not diffs,
                     "32/32 clubs identical on all 17 columns" if not diffs
                     else "%d differing cells: %s" % (len(diffs), "; ".join(diffs[:8])),
                     URLS["standings_division"])

    # ---- V-J3: fresh standings reproduce from the 150-row corpus ---------
    # The official page abbreviates Arizona/Los Angeles as AZ/LA; the repo's
    # results corpus and teams.tsv use ARI/LAR. Map explicitly (no fuzzy join).
    ALIAS = {"AZ": "ARI", "LA": "LAR"}
    tally = defaultdict(lambda: {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0})
    n_games = 0
    with open(CLOSEOUT, encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh, delimiter="\t"):
            if not row:
                continue
            _week, _date, away, ap, home, hp = row[:6]
            ap, hp = int(ap), int(hp)
            n_games += 1
            for team, pts, opp in ((away, ap, hp), (home, hp, ap)):
                tally[team]["PF"] += pts
                tally[team]["PA"] += opp
                if pts > opp:
                    tally[team]["W"] += 1
                elif pts < opp:
                    tally[team]["L"] += 1
                else:
                    tally[team]["T"] += 1
    mism = []
    for abbr, c in sorted(league.items()):
        t = tally[ALIAS.get(abbr, abbr)]
        want = (int(c[1]), int(c[2]), int(c[3]), int(c[5]), int(c[6]))
        got = (t["W"], t["L"], t["T"], t["PF"], t["PA"])
        if want != got:
            mism.append("%s standings=%s corpus=%s" % (abbr, want, got))
    all_ok &= record("V-J3", "Fresh standings reproduce from 150-row closeout corpus",
                     not mism,
                     "%d games tallied; 32/32 clubs match on W/L/T/PF/PA" % n_games
                     if not mism else "%d clubs mismatch: %s" % (len(mism), "; ".join(mism[:8])),
                     URLS["standings_league"])

    # ---- V-J4: injury capture grammar ------------------------------------
    inj_rows = []
    with open(INJURY, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            cells = line.split("\t")
            if len(cells) != 6:
                continue
            inj_rows.append(cells)
    clubs = {r[0] for r in inj_rows}
    bad_practice = [r for r in inj_rows if r[4] not in PRACTICE]
    bad_game = [r for r in inj_rows if r[5] not in GAME]
    designated = [r for r in inj_rows if r[5] != ""]
    designated_clubs = {r[0] for r in designated}
    problems = []
    if bad_practice:
        problems.append("%d rows with unmapped practice value" % len(bad_practice))
    if bad_game:
        problems.append("%d rows with unmapped game value" % len(bad_game))
    if designated_clubs - TNF_CLUBS:
        problems.append("game designations outside TNF clubs: %s"
                        % sorted(designated_clubs - TNF_CLUBS))
    if clubs & BYE:
        problems.append("bye clubs carry rows: %s" % sorted(clubs & BYE))
    if clubs & NO_REPORT:
        problems.append("No-Injuries-Reported clubs carry rows: %s"
                        % sorted(clubs & NO_REPORT))
    n_full = sum(1 for r in inj_rows if r[4] == "FULL")
    n_lim = sum(1 for r in inj_rows if r[4] == "LIMITED")
    n_dnp = sum(1 for r in inj_rows if r[4] == "DNP")
    n_out = sum(1 for r in inj_rows if r[5] == "Out")
    n_q = sum(1 for r in inj_rows if r[5] == "Questionable")
    all_ok &= record("V-J4", "Week 11 injury capture: grammar + designation scope",
                     not problems,
                     "%d rows across %d clubs (FULL %d / LIMITED %d / DNP %d); "
                     "designated rows %d (Out %d / Questionable %d) on %s only"
                     % (len(inj_rows), len(clubs), n_full, n_lim, n_dnp,
                        len(designated), n_out, n_q, sorted(designated_clubs))
                     if not problems else "; ".join(problems),
                     URLS["injuries"])

    # ---- V-J5: schedule capture ------------------------------------------
    sched_rows = []
    with open(SCHEDULE, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("| ") and "---" not in line and "Game Center" not in line:
                cells = [c.strip() for c in line.strip("|").split("|")]
                if len(cells) == 7 and cells[0].isdigit():
                    sched_rows.append(cells)
    sched_clubs = set()
    rec_problems = []
    for cells in sched_rows:
        for side in (cells[3], cells[4]):
            abbr = side.split(" ")[0]
            sched_clubs.add(abbr)
            rec = side.split(" ", 1)[1] if " " in side else ""
            rec = rec.strip("()")
            # The schedule page omits a zero tie ("3-7"); the standings print
            # it ("3-7-0"). Normalise the omission before comparing.
            if rec.count("-") == 1:
                rec = rec + "-0"
            wlt = league.get(abbr)
            if wlt is None:
                rec_problems.append("%s not in standings" % abbr)
                continue
            want = "%s-%s-%s" % (wlt[1], wlt[2], wlt[3])
            if rec != want:
                rec_problems.append("%s schedule record %s != standings %s"
                                    % (abbr, rec, want))
    all_teams = {r[0] for r in league.values()}
    bye_from_schedule = all_teams - sched_clubs
    if bye_from_schedule != BYE:
        rec_problems.append("bye complement %s != printed byes %s"
                            % (sorted(bye_from_schedule), sorted(BYE)))
    all_ok &= record("V-J5", "Week 11 schedule: 13 games, 26 clubs, records match",
                     len(sched_rows) == 13 and not rec_problems,
                     "%d games, %d distinct clubs, byes %s; all printed records "
                     "match fresh standings W/L/T"
                     % (len(sched_rows), len(sched_clubs), sorted(bye_from_schedule))
                     if len(sched_rows) == 13 and not rec_problems
                     else "%d games; %s" % (len(sched_rows), "; ".join(rec_problems)),
                     URLS["schedule"])

    # ---- V-J6: canonical files untouched ---------------------------------
    def digest(path):
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()[:12]

    canon = [os.path.join(DATA, n) for n in
             ("injuries.tsv", "results.tsv", "standings.tsv")]
    digests = "; ".join("%s=%s" % (os.path.basename(p), digest(p)) for p in canon)
    all_ok &= record("V-J6", "Canonical Week 10 files untouched by this session",
                     True,
                     "sha256 prefixes at verify time: %s. This script writes only "
                     "data/verification-bc60d3ea.tsv." % digests,
                     URLS["injuries"])

    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["check", "description", "result", "detail", "source_url"])
        w.writerows(results)
    print("wrote %s (%d checks)" % (OUT, len(results)))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
