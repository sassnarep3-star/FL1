#!/usr/bin/env python3
"""verify_brief.py — line-by-line checks for the arena/685f958d-fl1 outputs.

Checks (each writes one row to data/verification-brief.tsv):
  V1  official capture: all 13 pending games match raw/nfl-week10-2026-capture.md (URL, date, time, network, teams)
  V2  slate equals the repo's own unplayed Week 10 games (data/schedule2026-d.csv)
  V3  model lines: every fair value reproduces when the model is re-run from data/results.tsv
  V4  model lines: every market and difference cell is blank, and every row carries an official game URL
  V5  price store: 13 games x 3 markets = 39 rows, every price field blank, every row carries an official URL
  V6  results feed: 137 rows equal the played rows of the repo schedule feed, scores included
  V7  backtest: n is present on every row; every ROI cell is blank
  V8  correlations: no withheld coefficient appears on any published page
  V9  flagged page: F18-F22 anchors exist
  V10 existing standings check still passes (tools/verify_results.py)

Exit code is non-zero if any check fails. No network access is used.
"""

import csv
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import brief  # noqa: E402

RESULTS = []


def check(cid, name, ok, detail):
    RESULTS.append((cid, name, "PASS" if ok else "FAIL", detail))


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as fh:
        return fh.read()


def main():
    # ---------- V1: official capture ------------------------------------------------
    cap = read("raw/nfl-week10-2026-capture.md")
    pat = re.compile(r"- \[([^\]]+?), (Sunday|Monday), November \d+(?:st|nd|rd|th), (\d{1,2}:\d{2} [AP]M), (\w+)\]\((https://www\.nfl\.com/games/[^)]+)\)")
    official = {}
    for m in pat.finditer(cap):
        matchup, dow, t, net, url = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        official[url] = {"matchup": matchup, "dow": dow, "time": t, "net": net}
    slate = brief.load_slate()
    teams = {}
    for r in csv.reader(open(os.path.join(ROOT, "data", "teams.tsv"), encoding="utf-8"), delimiter="\t"):
        teams[r[1].split()[-1].lower()] = r[0]          # nickname -> abbr ("49ers", "cardinals"...)
    def hhmm(t):
        h, rest = t.split(":")
        mm, ap = rest[:2], rest[3:].strip()
        h = int(h) % 12 + (12 if ap == "PM" else 0)
        return "%02d:%s" % (h, mm)
    v1_bad = []
    for s in slate:
        o = official.get(s["official_game_url"])
        if not o:
            v1_bad.append("missing in capture: " + s["official_game_url"]); continue
        m = re.match(r"(.+) at (.+)$", o["matchup"])
        away_abbr = teams.get(m.group(1).split()[-1].lower())
        home_abbr = teams.get(m.group(2).split()[-1].lower())
        want_date = "2026-11-15" if o["dow"] == "Sunday" else "2026-11-16"
        if (away_abbr, home_abbr) != (s["away"], s["home"]):
            v1_bad.append("teams %s vs %s/%s" % (o["matchup"], s["away"], s["home"]))
        if s["date"] != want_date:
            v1_bad.append("date " + s["date"])
        if s["kickoff_et"] != hhmm(o["time"]):
            v1_bad.append("time %s vs %s" % (o["time"], s["kickoff_et"]))
        if s["network"] != o["net"]:
            v1_bad.append("network %s vs %s" % (o["net"], s["network"]))
    check("V1", "13 pending games match the official capture (URL, teams, date, time, network)",
          len(slate) == 13 and len(official) >= 13 and not v1_bad,
          "%d slate rows, %d official URLs; mismatches: %s" % (len(slate), len(official), "; ".join(v1_bad) or "none"))

    # ---------- V2: slate == repo schedule feed, unplayed Week 10 -----------------------
    sched = {}
    for r in csv.DictReader(open(os.path.join(ROOT, "data", "schedule2026-d.csv"), encoding="utf-8")):
        if r["week"] == "10" and r["played"] == "no":
            sched[(r["away_team"], r["home_team"])] = r["date"]
    slate_pairs = {(s["away"], s["home"]): s["date"] for s in slate}
    check("V2", "slate equals the unplayed Week 10 games in data/schedule2026-d.csv",
          set(sched) == set(slate_pairs) and all(sched[k] == slate_pairs[k] for k in sched),
          "schedule feed %d games, slate %d games" % (len(sched), len(slate_pairs)))

    # ---------- V3 / V4: model lines reproduce and carry blanks ------------------------
    c = brief.compute()
    ml = list(csv.DictReader(open(os.path.join(ROOT, "data", "model_lines.tsv"), encoding="utf-8"), delimiter="\t"))
    rec_by = {(r["away"], r["home"]): r for r in c["records"]}
    v3_bad = []
    for row in ml:
        r = rec_by[(row["away"], row["home"])]
        if row["side_fair_home_spread"] != ("%+.1f" % r["fair_home_spread"] if r["fair_home_spread"] else "0.0"):
            v3_bad.append("side " + row["home"])
        if row["total_fair"] != "%.1f" % r["fair_total"]:
            v3_bad.append("total " + row["home"])
        if row["ml_fair_home"] != "%+d" % r["fair_ml_home"]:
            v3_bad.append("ml " + row["home"])
    check("V3", "fair side, total and moneyline reproduce from a fresh re-run",
          len(ml) == 13 and not v3_bad, "%d rows re-run; mismatches: %s" % (len(ml), v3_bad or "none"))
    market_cols = [k for k in ml[0] if k.startswith(("side_market", "side_difference", "total_market",
                                                      "total_difference", "ml_market", "ml_difference"))]
    filled = [(row["away"], k) for row in ml for k in market_cols if row[k].strip()]
    urls_ok = all(row["source_url"].startswith("https://www.nfl.com/games/") and row["source_url"] in official
                  for row in ml)
    check("V4", "market and difference cells are blank; every row has an official game URL",
          not filled and urls_ok,
          "%d market cells filled (must be 0); official URL on %d/%d rows" % (
              len(filled), sum(1 for r in ml if r["source_url"] in official), len(ml)))

    # ---------- V5: price store ----------------------------------------------------------
    ps = list(csv.DictReader(open(os.path.join(ROOT, "data", "price_snapshots.tsv"), encoding="utf-8"), delimiter="\t"))
    price_fields = ["open_line", "open_price", "open_time_utc", "close_line", "close_price", "close_time_utc", "book"]
    filled_ps = [k for r in ps for k in price_fields if r[k].strip()]
    games_ps = {(r["away"], r["home"]) for r in ps}
    check("V5", "price store: 39 rows (13 games x 3 markets), all price fields blank, official URL on each",
          len(ps) == 39 and len(games_ps) == 13 and not filled_ps and all(r["source_url"] in official for r in ps),
          "%d rows; filled price fields: %d" % (len(ps), len(filled_ps)))

    # ---------- V6: results feed == repo schedule feed (played rows) ---------------------
    played = {}
    for r in csv.DictReader(open(os.path.join(ROOT, "data", "schedule2026-d.csv"), encoding="utf-8")):
        if r["played"] == "yes":
            played[(int(r["week"]), r["away_team"], r["home_team"])] = (int(r["away_score"]), int(r["home_score"]))
    res_bad = []
    res_rows = c["games"]
    for g in res_rows:
        key = (g.week, g.away, g.home)
        if key not in played or played[key] != (g.away_pts, g.home_pts):
            res_bad.append("%s %s@%s" % key)
    check("V6", "137 results equal the played rows of the repo schedule feed (teams, week, scores)",
          len(res_rows) == len(played) == 137 and not res_bad,
          "results %d, played in feed %d; mismatches: %s" % (len(res_rows), len(played), res_bad[:5] or "none"))

    # ---------- V7: backtest n present, ROI blank ---------------------------------------
    bt = list(csv.DictReader(open(os.path.join(ROOT, "data", "backtest_calibration.tsv"), encoding="utf-8"), delimiter="\t"))
    check("V7", "backtest: n on every row; ROI blank on every row",
          all(r["n_out_of_sample"].strip() for r in bt) and all(r["roi"] == "" for r in bt),
          "%d rows" % len(bt))

    # ---------- V8: withheld coefficients are not on published pages --------------------
    withheld = [r["pearson_r"] for r in csv.DictReader(open(os.path.join(ROOT, "data", "prop-correlations-d.csv"), encoding="utf-8")) if r["pearson_r"]]
    pages = ["prop-correlations.html", "schedule.html", "governance.html", "results-feed.html", "model-lines.html"]
    leaks = []
    for p in pages:
        txt = read(p)
        for v in withheld:
            if re.search(r"(?<![\d.])%s(?![\d])" % re.escape(v), txt):
                leaks.append("%s:%s" % (p, v))
    check("V8", "no withheld correlation coefficient appears on a published page",
          not leaks, "%d withheld values checked on %d pages; leaks: %s" % (len(withheld), len(pages), leaks[:5] or "none"))

    # ---------- V9: flag anchors exist ---------------------------------------------------
    flagged = read("flagged.html")
    missing = [f for f in ("F18", "F19", "F20", "F21", "F22") if 'id="%s"' % f not in flagged]
    check("V9", "flagged page has anchors F18-F22", not missing, "missing: %s" % (missing or "none"))

    # ---------- V10: existing standings check ---------------------------------------------
    rc = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "verify_results.py")],
                        capture_output=True, text=True, cwd=ROOT)
    check("V10", "standings reconciliation still passes (tools/verify_results.py)", rc.returncode == 0,
          "exit %d" % rc.returncode)

    out = os.path.join(ROOT, "data", "verification-brief.tsv")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["check", "description", "result", "detail", "source"])
        for cid, name, res, detail in RESULTS:
            w.writerow([cid, name, res, detail,
                        "https://www.nfl.com/schedules/2026/REG10/ ; raw/nfl-week10-2026-capture.md"])
    for cid, name, res, detail in RESULTS:
        print("%-4s %-4s %s — %s" % (cid, res, name, detail))
    failed = [r for r in RESULTS if r[2] != "PASS"]
    print("PASS %d/%d" % (len(RESULTS) - len(failed), len(RESULTS)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
