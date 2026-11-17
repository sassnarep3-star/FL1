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
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "schedule-results-2026-week10-finals.tsv")
RAW_COMPLETE = os.path.join(ROOT, "raw", "schedule-results-2026-week10-complete.md")
STANDINGS_1117 = os.path.join(ROOT, "raw", "standings-2026-20261117.tsv")
STANDINGS_1116 = os.path.join(ROOT, "raw", "standings-2026-20261116.tsv")
SCHED = os.path.join(ROOT, "data", "schedule.tsv")
RESULTS = os.path.join(ROOT, "data", "results.tsv")
OUT = os.path.join(ROOT, "data", "week10_results_extension.json")

PAGE_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
READ_WINDOW = "after 2026-11-16T01:14:56Z, before 2026-11-16T01:25:00Z"
SOURCE_ID = "S81"

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

    # ------------------------------------------------- close-out read (2026-11-17)
    # Second dated read of the same official page plus a fresh standings read.
    # C1  every game bullet on the fresh capture parses; exactly 13 FINAL and one
    #     live card (LAC at BAL, Q2) — a partial score is never a result;
    # C2  the 12 rows of the original extension reappear verbatim on the fresh
    #     read, and the one extra FINAL is exactly SNF (PIT 18, CIN 38);
    # C3  feed + extension + the new SNF final reproduces the fresh official
    #     standings for all 32 clubs (W/L/T AND PF/PA);
    # C4  the live MNF clubs' standings rows are byte-identical to the 2026-11-16
    #     capture (the in-progress game is not counted anywhere);
    # C5  the four bye-club records printed on the fresh page equal the recompute.
    with open(RAW_COMPLETE, encoding="utf-8") as fh:
        comp_text = fh.read()

    NAME2ABBR = {
        "Commanders": "WAS", "Giants": "NYG", "Patriots": "NE", "Lions": "DET",
        "Chiefs": "KC", "Falcons": "ATL", "Texans": "HOU", "Browns": "CLE",
        "Vikings": "MIN", "Packers": "GB", "Dolphins": "MIA", "Colts": "IND",
        "Panthers": "CAR", "Saints": "NO", "Bills": "BUF", "Jets": "NYJ",
        "Jaguars": "JAX", "Titans": "TEN", "Rams": "LAR", "Cardinals": "ARI",
        "Seahawks": "SEA", "Raiders": "LV", "49ers": "SF", "Cowboys": "DAL",
        "Steelers": "PIT", "Bengals": "CIN", "Chargers": "LAC", "Ravens": "BAL",
    }
    BULLET = re.compile(
        r"^- \[([A-Za-z0-9.]+) (\d+), ([A-Za-z0-9.]+) (\d+), (FINAL|Q\d), "
        r"([^\]]+)\]\((https://www\.nfl\.com/games/[^)]+)\)$")

    page_finals, live_cards = [], []
    for ln in comp_text.splitlines():
        m = BULLET.match(ln)
        if not m:
            continue
        away_n, ap, home_n, hp, status, tail, url = m.groups()
        row = {"away": NAME2ABBR[away_n], "awayPts": int(ap),
               "home": NAME2ABBR[home_n], "homePts": int(hp),
               "game_url": url}
        if status == "FINAL":
            day = re.search(r"November (\d+)(?:st|nd|rd|th)", tail)
            if not day:
                raise SystemExit("FAIL C1: FINAL bullet has no date: %r" % ln)
            row["date"] = "2026-11-%02d" % int(day.group(1))
            page_finals.append(row)
        else:
            row["status"] = "%s (%s)" % (status, tail)
            live_cards.append(row)
    if len(page_finals) != 13:
        raise SystemExit("FAIL C1: expected 13 FINAL bullets, parsed %d"
                         % len(page_finals))
    if len(live_cards) != 1 or live_cards[0]["away"] != "LAC" \
            or live_cards[0]["home"] != "BAL" or not live_cards[0]["status"].startswith("Q2"):
        raise SystemExit("FAIL C1: expected exactly one live card (LAC at BAL, Q2), got %r"
                         % live_cards)
    for r in page_finals + live_cards:
        k = (r["away"], r["home"])
        if k not in GAME_URLS:
            raise SystemExit("FAIL C1: %s @ %s has no gamecentre URL" % k)
        if r["game_url"] != GAME_URLS[k]:
            raise SystemExit("FAIL C1: bullet URL %s != registered gamecentre %s"
                             % (r["game_url"], GAME_URLS[k]))

    # C1b: the TSV rows in the same capture agree with the bullet lines.
    comp_tsv = [r for r in read_tsv(RAW_COMPLETE,
                                    ["week", "date", "away", "away_pts", "home",
                                     "home_pts", "note"])
                if r["week"] == "10"]
    b_key = sorted((r["away"], r["awayPts"], r["home"], r["homePts"])
                   for r in page_finals)
    t_key = sorted((r["away"], int(r["away_pts"]), r["home"], int(r["home_pts"]))
                   for r in comp_tsv)
    if b_key != t_key:
        raise SystemExit("FAIL C1b: bullet lines and TSV rows disagree:\n bullets=%r\n tsv=%r"
                         % (b_key, t_key))

    # C2: the original extension reappears verbatim; the extra final is SNF.
    ext_key = sorted((r["away"], int(r["away_pts"]), r["home"], int(r["home_pts"]))
                     for r in raw)
    missing = [k for k in ext_key if k not in b_key]
    extra = [k for k in b_key if k not in ext_key]
    if missing:
        raise SystemExit("FAIL C2: extension rows missing from the fresh read: %r" % missing)
    if extra != [("PIT", 18, "CIN", 38)]:
        raise SystemExit("FAIL C2: expected exactly [PIT 18, CIN 38] as the new final, got %r"
                         % extra)
    snf = [r for r in page_finals if (r["away"], r["home"]) == ("PIT", "CIN")][0]

    # C3: recompute WITH the SNF final and compare to the fresh standings read.
    rec2, pf_pa2 = dict(rec), dict(pf_pa)
    for team, pf, pa in (("PIT", 18, 38), ("CIN", 38, 18)):
        w, l, t = rec2[team]
        rec2[team] = (w + (1 if pf > pa else 0),
                      l + (1 if pf < pa else 0),
                      t + (1 if pf == pa else 0))
        p, q = pf_pa2[team]
        pf_pa2[team] = (p + pf, q + pa)
    stand3 = read_tsv(STANDINGS_1117, ["abbr", "w", "l", "t", "pf", "pa"])
    if len(stand3) != 32:
        raise SystemExit("FAIL C3: standings capture has %d rows, expected 32" % len(stand3))
    c3_mismatch = []
    for s in stand3:
        ab = s["abbr"]
        got = (rec2.get(ab), pf_pa2.get(ab, (0, 0)))
        want = ((int(s["w"]), int(s["l"]), int(s["t"])),
                (int(s["pf"]), int(s["pa"])))
        if got != want:
            c3_mismatch.append((ab, got, want))
    if c3_mismatch:
        for ab, got, want in c3_mismatch:
            print("FAIL C3: %s computed %s vs standings %s" % (ab, got, want),
                  file=sys.stderr)
        return 1

    # C4: the live MNF clubs' rows are unchanged between the two standings reads.
    stand2 = {r["abbr"]: r for r in read_tsv(STANDINGS_1116,
                                             ["abbr", "w", "l", "t", "pf", "pa"])}
    stand3d = {r["abbr"]: r for r in stand3}
    for ab in ("LAC", "BAL"):
        if stand2.get(ab) != stand3d.get(ab):
            raise SystemExit("FAIL C4: %s standings row moved between reads although the "
                             "game was live: %r -> %r"
                             % (ab, stand2.get(ab), stand3d.get(ab)))

    # C5: bye records printed on the fresh page equal the recompute.
    # The page glues record and wins text into one line:
    #   "7-27 wins, 2 losses, 0 ties" == record "7-2" + "7 wins, 2 losses, 0 ties".
    # Parse the words first (unambiguous), then rebuild the whole line from the
    # parsed numbers and require an exact match before trusting the parse.
    BYE_LINES = re.compile(
        # non-greedy abbr + lookahead so "TBTampa Bay" yields TB, not TBT
        r"^- ([A-Z]{2,3}?)(?=[A-Z][a-z])([A-Za-z .]+)\n"
        r"(\d+(?:-\d+)+(?: wins, \d+ losses, \d+ ties)+)\s*$", flags=re.M)
    # Full-line parse with the glued structure enforced: record "w-l" is
    # immediately followed by the wins word "w wins", so every occurrence of the
    # number must agree — that is what disambiguates "7-2" + "7 wins" from 27.
    GLUED = re.compile(r"^(\d+)-(\d+)(\d+) wins, (\d+) losses, (\d+) ties$")
    byes_found = 0
    for m in BYE_LINES.finditer(comp_text):
        ab, _name, line3 = m.groups()
        gm = GLUED.match(line3)
        if not gm:
            raise SystemExit("FAIL C5: cannot parse bye line for %s: %r" % (ab, line3))
        rec_w, rec_l, word_w, word_l, ti = (int(x) for x in gm.groups())
        if ti != 0:
            raise SystemExit("FAIL C5: bye line with a tie not handled: %r" % line3)
        if (rec_w, rec_l) != (word_w, word_l):
            raise SystemExit("FAIL C5: %s line %r is internally inconsistent "
                             "(record %d-%d vs words %d-%d)"
                             % (ab, line3, rec_w, rec_l, word_w, word_l))
        if rec2.get(ab) != (rec_w, rec_l, ti):
            raise SystemExit("FAIL C5: bye %s printed %d-%d-%d, recompute says %r"
                             % (ab, rec_w, rec_l, ti, rec2.get(ab)))
        byes_found += 1
    if byes_found != 4:
        raise SystemExit("FAIL C5: expected 4 bye records on the page, parsed %d"
                         % byes_found)

    completion = {
        "read": "2026-11-17",
        "read_window_utc": "after 2026-11-17T02:45:45Z, before 2026-11-17T02:46:39Z",
        "schedule_capture": "raw/schedule-results-2026-week10-complete.md",
        "standings_capture": "raw/standings-2026-20261117.tsv",
        "source_ids": ["S95", "S96"],
        "finals_on_page": len(page_finals),
        "page_finals": [
            {**r, "week": 10, "page_url": PAGE_URL, "source_id": "S95",
             "tier": "OFFICIAL"}
            for r in sorted(page_finals, key=lambda r: (r["date"], r["away"]))
        ],
        "new_final": {
            "week": 10, "date": snf["date"], "away": "PIT", "awayPts": 18,
            "home": "CIN", "homePts": 38,
            "result": "PIT 18, CIN 38",
            "margin_home": 20, "total": 56,
            "note": "Sunday Night Football — final at the 2026-11-17 read; "
                    "in progress at the 2026-11-16 read",
            "game_url": GAME_URLS[("PIT", "CIN")],
            "page_url": PAGE_URL, "source_id": "S95", "tier": "OFFICIAL",
        },
        "still_live": {
            "week": 10, "date": "2026-11-16", "away": "LAC", "home": "BAL",
            "status": "LIVE at read time — card printed Q2, Chargers 17, Ravens 7 "
                      "(partial score, not a result)",
            "game_url": GAME_URLS[("LAC", "BAL")], "page_url": PAGE_URL,
            "source_id": "S95",
        },
        "checks": {
            "C1_13_finals_and_one_live_card": True,
            "C1b_bullets_match_tsv_rows": True,
            "C2_original_rows_reappear_plus_snf": True,
            "C3_records_and_points_vs_fresh_standings_32_of_32": True,
            "C4_live_mnf_clubs_unchanged_between_standings_reads": True,
            "C5_bye_records_match_recompute": True,
        },
        "note": "data/results.tsv and data/standings.tsv remain untouched; promoting "
                "these finals into the canonical feed is the owner decision Q44 "
                "(tracked by F61/SG37).",
    }

    payload = {
        "id": "week10_results_extension",
        "title": "Week 10 finals captured after the 2026-11-14 read",
        "updated": "2026-11-17",
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
                                    "reproduces raw/standings-2026-20261116.tsv (S82, the official "
                                    "league-standings page at the same read time) exactly; "
                                    "that capture is corroborating evidence and does not "
                                    "replace data/standings.tsv",
        },
        "provenance": {"tier": "OFFICIAL", "source_id": SOURCE_ID,
                       "capture": "raw/schedule-results-2026-week10-finals.tsv"},
        "completion": completion,
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print("finals=%d (1 corroborated TNF + 11 new)  pending=%d" %
          (len(payload["finals"]), len(payload["pending"])))
    print("V3 record arithmetic: all 32 clubs reproduce the page-printed records")
    print("V4 points arithmetic: feed + finals reproduce the fresh standings capture (32/32)")
    print("completion read 2026-11-17: %d finals on page, new final %s, still live %s"
          % (len(page_finals), completion["new_final"]["result"],
             completion["still_live"]["status"]))
    print("C1-C5 all pass (fresh standings 32/32 W/L/T + PF/PA, bye records, "
          "live MNF excluded)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
