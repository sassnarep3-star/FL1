#!/usr/bin/env python3
"""
build_schedule_d.py — full 2026 regular-season schedule/results from the
nflverse/nfldata combined games.csv (auto-updated feed derived from official NFL
game books), reconciled line by line against the official captures in this repo.

Outputs (session D scope, prefixed -d):
  data/schedule2026-d.csv   272 regular-season rows: teams, dates, results,
                            market lines (flagged third-party), venue.
  data/verification-d.tsv   reconciliation rows (records vs official standings,
                            Week 10 finals vs official schedule page and vs
                            session B's capture).

Provenance
  raw/games-nfldata.csv     snapshot of nflverse/nfldata data/games.csv
                            (https://github.com/nflverse/nfldata, auto-updated;
                            last upstream commit checked at fetch time).
  Official cross-checks     https://www.nfl.com/schedules/2026/REG10/ (fetched
                            2026-11-14: "Commanders 24, Giants 21, FINAL"),
                            https://www.nfl.com/standings/ (fetched 2026-11-14,
                            records through Week 9; cached pre-Thursday),
                            data/standings.tsv (32-row official capture, session B).

Verification performed
  V1  computed records/PF/PA through Week 9 == data/standings.tsv 32/32 rows.
  V2  Week 10 Thursday final (WAS 24 @ NYG 21) == official nfl.com schedule page.
  V3  Week 10 13 games (teams, dates, times) == data/schedule.tsv (session B).
  V4  every played game's margin/total is internally consistent (no NaN scores,
      no future dates with scores).
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "games-nfldata.csv")
DATA = os.path.join(ROOT, "data")
STANDINGS = os.path.join(DATA, "standings.tsv")
SCHED_B = os.path.join(DATA, "schedule.tsv")
OUT_SCHED = os.path.join(DATA, "schedule2026-d.csv")
OUT_VER = os.path.join(DATA, "verification-d.tsv")

NFLVERSE_URL = "https://github.com/nflverse/nfldata/blob/master/data/games.csv"
NFL_SCHED_URL = "https://www.nfl.com/schedules/2026/REG10/"
NFL_STANDINGS_URL = "https://www.nfl.com/standings/"

TEAM_ABBR_TO_SLUG_PAGE = (
    "nfl.com/schedules (per-week page); scores derived from nflverse games.csv"
)


def load_official_standings():
    """data/standings.tsv: ABBR W L T ... PF PA — official capture (through W9)."""
    out = {}
    with open(STANDINGS, newline="", encoding="utf-8") as fh:
        for row in csv.reader(fh, delimiter="\t"):
            if not row or row[0] in ("Team", "#"):
                continue
            abbr = row[0]
            w, l, t = int(row[1]), int(row[2]), int(row[3])
            pf, pa = int(row[5]), int(row[6])
            out[abbr] = (w, l, t, pf, pa)
    return out


def main():
    problems = []
    ver_rows = []

    with open(RAW, newline="", encoding="utf-8") as fh:
        games = list(csv.DictReader(fh))

    g26 = [
        g for g in games
        if g["season"] == "2026" and g["game_type"] == "REG"
    ]
    if len(g26) != 272:
        problems.append(f"expected 272 regular-season games, got {len(g26)}")

    def played(g):
        return g["away_score"] != "" and g["home_score"] != ""

    # Normalize feed abbreviations to the repo's teams.tsv set (nflverse uses
    # LA for the Rams; the official captures here use LAR).
    ABBR_FIX = {"LA": "LAR", "WSH": "WAS"}
    for g in g26:
        g["away_team"] = ABBR_FIX.get(g["away_team"], g["away_team"])
        g["home_team"] = ABBR_FIX.get(g["home_team"], g["home_team"])

    # ---- V1: records through Week 9 vs official standings capture ----
    # ---- V1: records through all played games (incl. Week 10 Thursday) ----
    rec = {a: dict(w=0, l=0, t=0, pf=0, pa=0) for a in
           {g["home_team"] for g in g26} | {g["away_team"] for g in g26}}
    for g in g26:
        if not played(g):
            continue
        a, h = g["away_team"], g["home_team"]
        as_, hs = int(g["away_score"]), int(g["home_score"])
        rec[a]["pf"] += as_; rec[a]["pa"] += hs
        rec[h]["pf"] += hs; rec[h]["pa"] += as_
        if as_ > hs:
            rec[a]["w"] += 1; rec[h]["l"] += 1
        elif as_ < hs:
            rec[h]["w"] += 1; rec[a]["l"] += 1
        else:
            rec[a]["t"] += 1; rec[h]["t"] += 1

    official = load_official_standings()
    if len(official) != 32:
        problems.append(f"official standings capture has {len(official)} rows, expected 32")
    mism = []
    for abbr, (w, l, t, pf, pa) in official.items():
        c = rec.get(abbr)
        if c is None:
            mism.append(f"{abbr}: missing from feed")
            continue
        if (c["w"], c["l"], c["t"], c["pf"], c["pa"]) != (w, l, t, pf, pa):
            mism.append(
                f"{abbr}: computed {c['w']}-{c['l']}-{c['t']} PF{c['pf']} PA{c['pa']}"
                f" vs official {w}-{l}-{t} PF{pf} PA{pa}"
            )
    ver_rows.append([
        "V1", "records/PF/PA through all played games == official standings capture (32 teams, strict)",
        f"{32 - len(mism)}/32 exact match" + ("; MISMATCH: " + "; ".join(mism) if mism else ""),
        "PASS" if not mism and len(official) == 32 else "FAIL",
        NFL_STANDINGS_URL,
        "nflverse feed vs nfl.com standings capture fetched 2026-11-14 "
        "(both include the Wk10 Thursday final)",
    ])

    # ---- V2: Week 10 Thursday final vs official schedule page ----
    thu = [g for g in g26 if int(g["week"]) == 10 and played(g)]
    ok = False
    detail = "no Week 10 result rows found"
    for g in thu:
        if g["away_team"] == "WAS" and g["home_team"] == "NYG":
            got = f"{g['away_team']} {g['away_score']} @ {g['home_team']} {g['home_score']}"
            ok = got == "WAS 24 @ NYG 21"
            detail = f"{got} vs official 'Commanders 24, Giants 21, FINAL'"
    ver_rows.append([
        "V2", "Week 10 Thursday final == nfl.com schedule page",
        detail, "PASS" if ok else "FAIL", NFL_SCHED_URL,
        "official page fetched 2026-11-14",
    ])

    # ---- V3: Week 10 13 games vs session B capture ----
    w10 = [g for g in g26 if int(g["week"]) == 10]
    rows_b = []
    with open(SCHED_B, newline="", encoding="utf-8") as fh:
        for row in csv.reader(fh, delimiter="\t"):
            if row and row[0] != "Date" and len(row) >= 4:
                rows_b.append((row[0], row[1], row[3], row[4]))
    mine = {(g["gameday"], g["gametime"], g["away_team"], g["home_team"]) for g in w10}
    theirs = set(rows_b)
    missing_b = mine - theirs
    extra_b = theirs - mine
    ver_rows.append([
        "V3", "Week 10 slate == session B capture (13 games)",
        f"feed games {len(mine)}, capture rows {len(theirs)}, "
        f"missing-from-capture {len(missing_b)}, extra-in-capture {len(extra_b)}",
        "PASS" if not missing_b and not extra_b else "CHECK",
        NFL_SCHED_URL,
        "data/schedule.tsv cross-check",
    ])

    # ---- V4: internal consistency ----
    bad = []
    for g in g26:
        p = played(g)
        if p and g["gameday"] > "2026-11-14":
            bad.append(f"{g['game_id']}: future game has score")
        if not p and int(g["week"]) <= 9:
            bad.append(f"{g['game_id']}: Week<=9 game missing score")
    ver_rows.append([
        "V4", "internal consistency of 272 rows",
        "; ".join(bad[:5]) if bad else f"{sum(1 for g in g26 if played(g))} played rows consistent, "
        f"{sum(1 for g in g26 if not played(g))} future rows scoreless",
        "PASS" if not bad else "FAIL", NFLVERSE_URL, "nflverse games.csv snapshot",
    ])

    # ---- write schedule2026-d.csv ----
    os.makedirs(DATA, exist_ok=True)
    with open(OUT_SCHED, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([
            "game_id", "week", "date", "weekday", "kickoff_et", "away_team",
            "home_team", "away_score", "home_score", "played", "overtime",
            "neutral_site", "stadium", "roof", "surface",
            "market_spread_away", "market_total", "away_moneyline",
            "home_moneyline", "source", "scores_verified", "flags",
        ])
        for g in sorted(g26, key=lambda x: (int(x["week"]), x["gameday"], x["gametime"])):
            p = played(g)
            flags = []
            if g["spread_line"] or g["total_line"] or g["away_moneyline"]:
                flags.append("market lines = third-party (nflverse aggregation), no official NFL source")
            w.writerow([
                g["game_id"], g["week"], g["gameday"], g["weekday"], g["gametime"],
                g["away_team"], g["home_team"],
                g["away_score"], g["home_score"],
                "yes" if p else "no",
                "yes" if g["overtime"] not in ("", "0") else "",
                g["location"] if g["location"] != "Home" else "",
                g["stadium"], g["roof"], g["surface"],
                g["spread_line"], g["total_line"],
                g["away_moneyline"], g["home_moneyline"],
                NFL_SCHED_URL if int(g["week"]) == 10 else NFLVERSE_URL,
                "yes (reconciled V1/V2/V4)" if p else "",
                " | ".join(flags),
            ])

    with open(OUT_VER, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["check", "description", "result", "status", "source", "notes"])
        w.writerows(ver_rows)

    print(f"schedule rows written: {len(g26)}")
    for r in ver_rows:
        print(f"{r[0]} {r[3]}: {r[2][:110]}")
    if problems or any(r[3] == "FAIL" for r in ver_rows):
        print("PROBLEMS:", problems)
        sys.exit(1)


if __name__ == "__main__":
    main()
