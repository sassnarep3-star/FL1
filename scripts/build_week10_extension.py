#!/usr/bin/env python3
"""Build data/week10_results_extension.json — the Week 10 finals captured from
the official week-10 schedule page AFTER the 2026-11-14 capture, plus the two
games that were not final at read time.

Requirement (brief): the verified results feed must keep extending so backtests
and ROI can be computed; every row must link to its official source; values not
confirmed by an official source stay blank.

Inputs:
  raw/schedule-results-2026-week10-finals.tsv   the new dated capture (read 2026-11-16)
  data/results.tsv                              the existing verified feed (weeks 1-10 TNF)

Verification performed here (fails loudly):
  V1  the TNF row in the new capture equals the week-10 row already in data/results.tsv
      (two independent captures of the same fact must agree);
  V2  every new final is a Week 10 fixture that appears on data/schedule.tsv with the
      same home/away keys (the league's own published fixture list);
  V3  recomputing every club's W/L/T from results.tsv + the new finals reproduces the
      records the OFFICIAL page printed on its game cards at read time for all 32 clubs
      (pre-game records for the two games not yet played, and the four bye clubs).
      A single mistyped score would break this arithmetic for the clubs involved.

Output rows carry the official page URL and the per-game gamecentre URL printed on it.
The standings reconciliation of the main feed stays pinned to its capture state; this
extension is labelled per-row and does not touch data/results.tsv or data/standings.tsv.

Run:  python3 scripts/build_week10_extension.py
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "schedule-results-2026-week10-finals.tsv")
SCHED = os.path.join(ROOT, "data", "schedule.tsv")
RESULTS = os.path.join(ROOT, "data", "results.tsv")
OUT = os.path.join(ROOT, "data", "week10_results_extension.json")

PAGE_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
READ_WINDOW = "after 2026-11-16T01:14:56Z, before 2026-11-16T01:25:00Z"
SOURCE_ID = "S78"

# Records printed on the official page's game cards at read time (all 32 clubs).
# Post-game for the 12 finals; pre-game for PIT/CIN (in progress) and LAC/BAL
# (not yet played); the four bye clubs as printed on the "Teams on Bye" section.
PAGE_RECORDS = {
    "WAS": (3, 5, 1), "NYG": (5, 3, 1),
    "NE": (5, 5, 0), "DET": (7, 2, 0),
    "KC": (7, 2, 0), "ATL": (3, 7, 0),
    "HOU": (3, 6, 0), "CLE": (6, 4, 0),
    "MIN": (7, 2, 0), "GB": (6, 4, 0),
    "MIA": (1, 8, 0), "IND": (3, 7, 0),
    "CAR": (4, 5, 0), "NO": (3, 6, 0),
    "BUF": (8, 1, 0), "NYJ": (2, 8, 0),
    "JAX": (7, 2, 0), "TEN": (1, 8, 0),
    "LAR": (6, 4, 0), "ARI": (3, 7, 0),
    "SEA": (6, 4, 0), "LV": (4, 6, 0),
    "SF": (8, 1, 0), "DAL": (4, 6, 0),
    "PIT": (6, 2, 0), "CIN": (6, 2, 0),
    "LAC": (0, 8, 0), "BAL": (4, 5, 0),
    "CHI": (7, 2, 0), "DEN": (7, 2, 0),
    "PHI": (2, 7, 0), "TB": (3, 6, 0),
}

GAME_URLS = {
    ("WAS", "NYG"): "https://www.nfl.com/games/commanders-at-giants-2026-reg-10",
    ("NE", "DET"): "https://www.nfl.com/games/patriots-at-lions-2026-reg-10",
    ("KC", "ATL"): "https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10",
    ("HOU", "CLE"): "https://www.nfl.com/games/texans-at-browns-2026-reg-10",
    ("MIN", "GB"): "https://www.nfl.com/games/vikings-at-packers-2026-reg-10",
    ("MIA", "IND"): "https://www.nfl.com/games/dolphins-at-colts-2026-reg-10",
    ("CAR", "NO"): "https://www.nfl.com/games/panthers-at-saints-2026-reg-10",
    ("BUF", "NYJ"): "https://www.nfl.com/games/bills-at-jets-2026-reg-10",
    ("JAX", "TEN"): "https://www.nfl.com/games/jaguars-at-titans-2026-reg-10",
    ("LAR", "ARI"): "https://www.nfl.com/games/rams-at-cardinals-2026-reg-10",
    ("SEA", "LV"): "https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10",
    ("SF", "DAL"): "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10",
    ("PIT", "CIN"): "https://www.nfl.com/games/steelers-at-bengals-2026-reg-10",
    ("LAC", "BAL"): "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10",
}


def read_tsv(path, fields):
    with open(path, newline="", encoding="utf-8") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    rows = []
    for ln in lines:
        if ln.startswith("#"):
            continue
        c = ln.rstrip("\t").split("\t")
        c += [""] * (len(fields) - len(c))
        if len(c) > len(fields):
            raise SystemExit("FAIL: %s row has %d fields, expected %d: %r"
                             % (path, len(c), len(fields), ln))
        rows.append(dict(zip(fields, c)))
    return rows


def read_headered_tsv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    header = None
    rows = []
    for ln in lines:
        if ln.startswith("#"):
            continue
        c = ln.rstrip("\t").split("\t")
        if header is None:
            header = c
            continue
        rows.append(dict(zip(header, c + [""] * (len(header) - len(c)))))
    return rows


def main():
    raw = read_tsv(RAW, ["week", "date", "away", "away_pts", "home", "home_pts", "note"])
    if len(raw) != 12:
        raise SystemExit("FAIL: expected 12 FINAL rows in the capture, got %d" % len(raw))
    tnf = [r for r in raw if r["away"] == "WAS" and r["home"] == "NYG"]
    if len(tnf) != 1:
        raise SystemExit("FAIL: exactly one WAS@NYG row expected")
    tnf = tnf[0]

    results = read_tsv(RESULTS, ["week", "date", "away", "awayPts", "home", "homePts"])
    tnf_feed = [r for r in results if r["week"] == "10" and r["away"] == "WAS"
                and r["home"] == "NYG"]
    if len(tnf_feed) != 1:
        raise SystemExit("FAIL: week-10 TNF row missing from results.tsv")
    if (tnf_feed[0]["awayPts"], tnf_feed[0]["homePts"]) != (tnf["away_pts"], tnf["home_pts"]):
        raise SystemExit("FAIL: V1 — new TNF capture %s/%s disagrees with results.tsv %s/%s"
                         % (tnf["away_pts"], tnf["home_pts"],
                            tnf_feed[0]["awayPts"], tnf_feed[0]["homePts"]))

    sched = read_tsv(SCHED, ["date", "time_et", "network", "away", "home", "note", "result"])
    sched_keys = {(s["away"], s["home"]) for s in sched}
    new_finals = [r for r in raw if r is not tnf]
    for r in new_finals:
        k = (r["away"], r["home"])
        if k not in sched_keys:
            raise SystemExit("FAIL: V2 — %s @ %s is not a published Week 10 fixture in "
                             "data/schedule.tsv" % (r["away"], r["home"]))
        if k not in GAME_URLS:
            raise SystemExit("FAIL: %s @ %s has no gamecentre URL" % (r["away"], r["home"]))

    # V3: record arithmetic across all 32 clubs
    rec = {}
    pf_pa = {}
    for r in results:
        a, h = r["away"], r["home"]
        ap, hp = int(r["awayPts"]), int(r["homePts"])
        for team, pf, pa in ((a, ap, hp), (h, hp, ap)):
            w, l, t = rec.get(team, (0, 0, 0))
            w, l, t = (w + (1 if pf > pa else 0),
                       l + (1 if pf < pa else 0),
                       t + (1 if pf == pa else 0))
            rec[team] = (w, l, t)
            p, q = pf_pa.get(team, (0, 0))
            pf_pa[team] = (p + pf, q + pa)
    for r in new_finals:
        ap, hp = int(r["away_pts"]), int(r["home_pts"])
        for team, pf, pa in ((r["away"], ap, hp), (r["home"], hp, ap)):
            w, l, t = rec.get(team, (0, 0, 0))
            w, l, t = (w + (1 if pf > pa else 0),
                       l + (1 if pf < pa else 0),
                       t + (1 if pf == pa else 0))
            rec[team] = (w, l, t)
            p, q = pf_pa.get(team, (0, 0))
            pf_pa[team] = (p + pf, q + pa)
    all_abbrs = sorted(set(rec) | set(PAGE_RECORDS))
    mismatches = []
    for ab in all_abbrs:
        got = rec.get(ab, None)
        want = PAGE_RECORDS.get(ab, None)
        if got != want:
            mismatches.append((ab, got, want))
    if mismatches:
        for ab, got, want in mismatches:
            print("FAIL V3: %s computed %s vs page-printed %s" % (ab, got, want),
                  file=sys.stderr)
        return 1

    # V4: the feed + the new finals must reproduce the fresh official standings
    # capture (W/L/T AND PF/PA for all 32 clubs). raw/standings-2026-20261116.tsv
    # is corroborating evidence only; data/standings.tsv stays the canonical
    # capture behind the already-published registers and is not replaced.
    stand2 = read_tsv(os.path.join(ROOT, "raw", "standings-2026-20261116.tsv"),
                      ["abbr", "w", "l", "t", "pf", "pa"])
    if len(stand2) != 32:
        raise SystemExit("FAIL: V4 standings capture has %d rows, expected 32" % len(stand2))
    v4_mismatch = []
    for s in stand2:
        ab = s["abbr"]
        got = (rec.get(ab), pf_pa.get(ab, (0, 0)))
        want = ((int(s["w"]), int(s["l"]), int(s["t"])),
                (int(s["pf"]), int(s["pa"])))
        if got != want:
            v4_mismatch.append((ab, got, want))
    if v4_mismatch:
        for ab, got, want in v4_mismatch:
            print("FAIL V4: %s computed %s vs standings capture %s" % (ab, got, want),
                  file=sys.stderr)
        return 1

    payload = {
        "id": "week10_results_extension",
        "title": "Week 10 finals captured after the 2026-11-14 read",
        "updated": "2026-11-16",
        "read_window_utc": READ_WINDOW,
        "page_url": PAGE_URL,
        "source_id": SOURCE_ID,
        "finals": [
            {"week": 10, "date": r["date"], "away": r["away"], "awayPts": int(r["away_pts"]),
             "home": r["home"], "homePts": int(r["home_pts"]),
             "result": "%s %d, %s %d" % (r["away"], int(r["away_pts"]),
                                         r["home"], int(r["home_pts"])),
             "margin_home": int(r["home_pts"]) - int(r["away_pts"]),
             "total": int(r["home_pts"]) + int(r["away_pts"]),
             "note": r.get("note", "").strip(),
             "game_url": GAME_URLS[(r["away"], r["home"])],
             "page_url": PAGE_URL, "source_id": SOURCE_ID,
             "tier": "OFFICIAL"}
            for r in raw
        ],
        "pending": [
            {"week": 10, "date": "2026-11-15", "away": "PIT", "home": "CIN",
             "status": "IN PROGRESS at read time (8:20 PM ET Sunday; card printed no score, "
                       "pre-game records 6-2 / 6-2)",
             "game_url": GAME_URLS[("PIT", "CIN")], "page_url": PAGE_URL,
             "source_id": SOURCE_ID},
            {"week": 10, "date": "2026-11-16", "away": "LAC", "home": "BAL",
             "status": "SCHEDULED at read time (8:15 PM ET Monday, not yet played; "
                       "pre-game records 0-8 / 4-5)",
             "game_url": GAME_URLS[("LAC", "BAL")], "page_url": PAGE_URL,
             "source_id": SOURCE_ID},
        ],
        "verification": {
            "V1_tnf_matches_existing_feed": True,
            "V2_all_finals_are_published_week10_fixtures": True,
            "V3_record_arithmetic": "recomputing W/L/T for all 32 clubs from data/results.tsv "
                                    "+ the 11 new finals reproduces the records the official "
                                    "page printed on its game cards at read time, exactly "
                                    "(pre-game records for PIT/CIN and LAC/BAL; bye clubs "
                                    "CHI 7-2, DEN 7-2, PHI 2-7, TB 3-6)",
            "V4_points_arithmetic_vs_fresh_standings": "recomputing W/L/T AND PF/PA for all "
                                    "32 clubs from data/results.tsv + the 11 new finals "
                                    "reproduces raw/standings-2026-20261116.tsv (S79, the official "
                                    "league-standings page at the same read time) exactly; "
                                    "that capture is corroborating evidence and does not "
                                    "replace data/standings.tsv",
        },
        "provenance": {"tier": "OFFICIAL", "source_id": SOURCE_ID,
                       "capture": "raw/schedule-results-2026-week10-finals.tsv"},
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print("finals=%d (1 corroborated TNF + 11 new)  pending=%d" %
          (len(payload["finals"]), len(payload["pending"])))
    print("V3 record arithmetic: all 32 clubs reproduce the page-printed records")
    print("V4 points arithmetic: feed + finals reproduce the fresh standings capture (32/32)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
