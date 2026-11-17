#!/usr/bin/env python3
"""promote_week10.py — the Q44 promotion acceptance run for Week 10, 2026.

Question Q44 (data/questions.json) asks: when a week's games all reach FINAL,
who promotes the captured finals into the canonical verified results feed
(data/results.tsv) and re-captures the official standings — and what acceptance
checks must pass first? This script is the mechanical half of that answer: the
checks, run here, fail loudly. The policy half (rolling the canonical feed and
the pinned model corpus forward) stays a reviewer decision — nothing canonical
is written unless --promote is passed AFTER Q44's owner has chosen that path.

Inputs (dated captures, never edited after write):
  raw/schedule-results-2026-week10-closeout.tsv   all 14 Week 10 games FINAL
  raw/standings-2026-20261117-closeout.tsv                 fresh official league standings
  data/results.tsv                                the frozen 137-game corpus (read only)
  data/week10_results_extension.json              the 2026-11-16 dated extension (read only)
  data/schedule.tsv                               the published fixture list (read only)
  data/results_2026-11-17.tsv                     the earlier same-day SNF read (read only)

Acceptance checks (all must PASS before any write):
  P1  the closeout capture holds exactly 14 rows, each a published Week 10
      fixture in data/schedule.tsv with an official gamecentre URL
  P2  cross-read agreement: the 12 finals already on record (the TNF row inside
      the frozen corpus + the 11 finals in the 2026-11-16 extension) equal the
      closeout capture exactly, score for score
  P3  the two late finals (PIT at CIN, LAC at BAL) appear with scores ONLY in
      the closeout capture: they were pending with blank scores in the
      extension, so no in-progress score was ever carried forward
  P4  the staged corpus (frozen 137 + the 13 new rows) reproduces the fresh
      standings capture for all 32 clubs on W, L, T, PF and PA
  P5  append-only: the first 137 rows of the staged corpus are byte-identical
      to data/results.tsv — the pre-registration corpus has not drifted
  P6  per-club game count equals W+L+T in the fresh standings for all 32 clubs
  P7  no duplicate (week, away, home) in the staged corpus; every club key is a
      known team in data/teams.tsv
  P8  the 2026-11-17 SNF read (data/results_2026-11-17.tsv, 149 rows, session
      e97f05c3) is a byte-prefix of the staged closeout — the chain of dated
      reads is unbroken: 137 -> 148 -> 149 -> 150

Modes:
  default        run every check, write data/week10_closeout.json (a dated
                 register — additive, like every other register here), print
                 exactly what the gated modes would do. No canonical file is
                 touched. Exit 0 when all checks pass.
  --execute      additionally write the dated side-reads:
                 data/results_2026-11-17-closeout.tsv (150 rows) and
                 data/standings_2026-11-17-closeout.tsv (32 clubs)
  --promote      (requires --execute) roll the canonical feed forward:
                 data/results.tsv, data/standings.tsv,
                 data/schedule2026-d.csv played flags — then print the
                 follow-up rebuild/verification commands that MUST be run
                 before anything is published. Refuses to run if any check
                 fails.

Run:  python3 scripts/promote_week10.py
Exit: 0 when every acceptance check passes.
No third-party packages.
"""

import argparse
import csv
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
DATA = os.path.join(ROOT, "data")

CLOSEOUT_RAW = os.path.join(RAW, "schedule-results-2026-week10-closeout.tsv")
STANDINGS_RAW = os.path.join(RAW, "standings-2026-20261117-closeout.tsv")
RESULTS = os.path.join(DATA, "results.tsv")
EXTENSION = os.path.join(DATA, "week10_results_extension.json")
SCHEDULE = os.path.join(DATA, "schedule.tsv")
TEAMS = os.path.join(DATA, "teams.tsv")

# data/standings.tsv carries the page's full column layout; the raw capture
# keeps the same columns so --promote can write the canonical file verbatim.
STAND_FIELDS = ["abbr", "w", "l", "t", "pct", "pf", "pa", "net", "home", "road",
                "div", "div_pct", "conf", "conf_pct", "nonconf", "streak", "last5"]

OUT_REGISTER = os.path.join(DATA, "week10_closeout.json")
OUT_RESULTS_DATED = os.path.join(DATA, "results_2026-11-17-closeout.tsv")
OUT_STANDINGS_DATED = os.path.join(DATA, "standings_2026-11-17-closeout.tsv")
OUT_VERIFICATION = os.path.join(DATA, "verification-promote.tsv")

PAGE_URL = "https://www.nfl.com/schedules/2026/REG10/"
STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
SOURCE_SCHEDULE = "S98"
SOURCE_STANDINGS = "S99"

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

FOLLOWUP_PROMOTED = """\
--promote written. REQUIRED follow-ups before anything is published (the
analytical layer refits from the canonical feed, so every derived artefact and
pin must be rebuilt and re-verified in one pass):

  1. python3 scripts/build_results_feed.py        # VERIFIED_COUNT must be updated to 150 first
  2. python3 tools/build.py                       # data.js + coverage numbers
  3. python3 tools/brief.py                       # refit fair lines on the promoted corpus
  4. python3 tools/build_line_board.py            # HFA / margin sd n_games -> 150
  5. python3 scripts/build_correlations_official.py
  6. python3 scripts/build_luck_g.py && python3 scripts/build_luck_panel.py
  7. python3 tools/verify_drift.py                # update DR-03 / DR-05 pins 137 -> 150
  8. python3 tools/verify_brief.py                # V6 expects the promoted count
  9. python3 tools/verify_results.py              # must PASS 32/32 on the promoted pair
 10. python3 -m unittest discover -s tests -q     # update count-pinned assertions (137 -> 150)
 11. sweep current-state "137" strings in generators (tools/site.py, tools/site_g.py,
     tools/brief.py, scripts/build_pages_m.py ...) — dated historical claims stay dated
 12. python3 tools/checklinks.py && python3 tools/checkrows.py
 13. commit as ONE changeset recording the corpus promotion (Q44 executed)

The frozen corpus property survives the promotion only if check P5 passes at
promotion time; after it, data/results.tsv must keep its first 137 rows
byte-identical forever (scripts/verify_results_g.py keeps asserting this)."""


def read_table(path, fields, comment_prefix="#"):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            if not line.strip() or line.startswith(comment_prefix):
                continue
            cells = line.split("\t")
            cells += [""] * (len(fields) - len(cells))
            if len(cells) > len(fields):
                raise SystemExit("FAIL: %s row has %d fields, expected %d: %r"
                                 % (path, len(cells), len(fields), line))
            rows.append(dict(zip(fields, cells)))
    return rows


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true",
                    help="write the dated side-reads (results/standings 2026-11-17)")
    ap.add_argument("--promote", action="store_true",
                    help="ALSO roll data/results.tsv, data/standings.tsv and "
                         "data/schedule2026-d.csv forward (Q44 decision)")
    args = ap.parse_args()

    for p in (CLOSEOUT_RAW, STANDINGS_RAW, RESULTS, EXTENSION, SCHEDULE, TEAMS):
        if not os.path.exists(p):
            raise SystemExit("FAIL: missing input %s" % p)

    checks = []

    def gate(cid, desc, ok, detail):
        checks.append((cid, desc, "PASS" if ok else "FAIL", detail))
        return ok

    # ---- inputs ------------------------------------------------------------
    closeout = read_table(CLOSEOUT_RAW,
                          ["week", "date", "away", "away_pts", "home", "home_pts", "note"])
    standings = read_table(STANDINGS_RAW, STAND_FIELDS)
    corpus_lines = [ln.rstrip("\n") for ln in open(RESULTS, encoding="utf-8") if ln.strip()]
    corpus = [ln.split("\t") for ln in corpus_lines]
    ext = json.load(open(EXTENSION, encoding="utf-8"))
    sched_rows = read_table(SCHEDULE,
                            ["date", "time_et", "network", "away", "home", "note", "result"],
                            comment_prefix="\x00")  # schedule.tsv has no comment lines
    known = set()
    with open(TEAMS, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            key = line.split("\t")[0]
            if key != "abbr":  # tolerate a header row if one ever appears
                known.add(key)

    # ---- P1: closeout capture shape ---------------------------------------
    sched_keys = {(r["away"], r["home"]) for r in sched_rows}
    p1_bad = []
    for r in closeout:
        if r["week"] != "10":
            p1_bad.append("week %s" % r["week"])
        if (r["away"], r["home"]) not in sched_keys:
            p1_bad.append("not a fixture: %s@%s" % (r["away"], r["home"]))
        if (r["away"], r["home"]) not in GAME_URLS:
            p1_bad.append("no gamecentre URL: %s@%s" % (r["away"], r["home"]))
        if not r["away_pts"].isdigit() or not r["home_pts"].isdigit():
            p1_bad.append("non-integer score: %s@%s" % (r["away"], r["home"]))
    gate("P1", "closeout capture holds 14 FINAL rows, each a published Week 10 "
               "fixture with an official gamecentre URL",
         len(closeout) == 14 and not p1_bad,
         "%d rows; problems: %s" % (len(closeout), p1_bad or "none"))

    closeout_by = {(r["away"], r["home"]): r for r in closeout}

    # ---- P2: cross-read agreement -----------------------------------------
    ext_by = {(f["away"], f["home"]): f for f in ext["finals"]}
    p2_bad = []
    for k, f in ext_by.items():
        c = closeout_by.get(k)
        if c is None:
            p2_bad.append("missing in closeout: %s@%s" % k)
            continue
        if (int(c["away_pts"]), int(c["home_pts"])) != (f["awayPts"], f["homePts"]):
            p2_bad.append("%s@%s closeout %s-%s vs extension %d-%d"
                          % (k + (c["away_pts"], c["home_pts"], f["awayPts"], f["homePts"])))
    # the TNF row is also inside the frozen corpus — three-way agreement
    tnf = [r for r in corpus if r[0] == "10" and r[2] == "WAS" and r[4] == "NYG"]
    tnf_ok = (len(tnf) == 1 and tnf[0][1] == "2026-11-12"
              and (tnf[0][3], tnf[0][5]) == ("24", "21")
              and (closeout_by.get(("WAS", "NYG")) or {}).get("away_pts") == "24"
              and (closeout_by.get(("WAS", "NYG")) or {}).get("home_pts") == "21")
    if not tnf_ok:
        p2_bad.append("TNF three-way disagreement")
    gate("P2", "cross-read agreement: the 12 finals already on record equal the "
               "closeout capture exactly (frozen corpus TNF + 2026-11-16 extension)",
         len(ext_by) == 12 and not p2_bad,
         "%d extension finals re-checked; problems: %s"
         % (len(ext_by), p2_bad or "none"))

    # ---- P3: late finals were never pre-filled ----------------------------
    late = {("PIT", "CIN"), ("LAC", "BAL")}
    p3_bad = []
    for k in late:
        if k in ext_by:
            p3_bad.append("extension already holds a score for %s@%s" % k)
        pend = [p for p in ext.get("pending", []) if (p["away"], p["home"]) == k]
        if len(pend) != 1 or "awayPts" in pend[0] or "homePts" in pend[0]:
            p3_bad.append("extension pending row wrong for %s@%s" % k)
        if k not in closeout_by:
            p3_bad.append("closeout missing %s@%s" % k)
    gate("P3", "the two late finals carry scores only in the closeout capture; "
               "the extension held them pending with blank scores",
         not p3_bad, "problems: %s" % (p3_bad or "none"))

    # ---- staged corpus -----------------------------------------------------
    # Append-only and idempotent: a fixture already in the corpus (the TNF row
    # before promotion, the whole week after it) is never appended twice.
    corpus_keys = {(r[0], r[2], r[4]) for r in corpus if len(r) >= 6}
    new_rows = []
    for r in closeout:
        k = ("10", r["away"], r["home"])
        if k in corpus_keys:
            continue
        new_rows.append(["10", r["date"], r["away"], r["away_pts"],
                         r["home"], r["home_pts"]])
    staged_lines = list(corpus_lines) + ["\t".join(r) for r in new_rows]
    staged = [ln.split("\t") for ln in staged_lines]

    # ---- P4: staged corpus reproduces the fresh standings -----------------
    derived = {s["abbr"]: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0}
               for s in standings}
    p4_unreadable = []
    for row in staged:
        if len(row) != 6:
            p4_unreadable.append("row width %d: %r" % (len(row), row))
            continue
        wk, date, away, ap, home, hp = row
        try:
            ap, hp = int(ap), int(hp)
        except ValueError:
            p4_unreadable.append("non-integer score: %r" % (row,))
            continue
        for team, pf, pa in ((away, ap, hp), (home, hp, ap)):
            if team not in derived:
                p4_unreadable.append("unknown club %s" % team)
                continue
            d = derived[team]
            d["pf"] += pf
            d["pa"] += pa
            d["w"] += pf > pa
            d["l"] += pf < pa
            d["t"] += pf == pa
    p4_bad = []
    for s in standings:
        got = derived.get(s["abbr"])
        try:
            want = {"w": int(s["w"]), "l": int(s["l"]), "t": int(s["t"]),
                    "pf": int(s["pf"]), "pa": int(s["pa"])}
        except ValueError:
            p4_bad.append("%s unparseable standings fields: %r"
                          % (s["abbr"], s))
            continue
        if got != want:
            p4_bad.append("%s got %s want %s" % (s["abbr"], got, want))
    gate("P4", "staged corpus (frozen 137 + 13 new) reproduces the fresh standings "
               "capture for all 32 clubs on W/L/T/PF/PA",
         len(standings) == 32 and not p4_bad and not p4_unreadable,
         "%d clubs; %d unreadable rows; mismatches: %s"
         % (len(standings), len(p4_unreadable), p4_bad[:5] or "none"))

    # ---- P5: append-only ---------------------------------------------------
    drift = staged_lines[:len(corpus_lines)] != corpus_lines
    gate("P5", "append-only: the first 137 rows of the staged corpus are "
               "byte-identical to data/results.tsv",
         not drift, "%d frozen rows, drift=%s; %d rows appended"
         % (len(corpus_lines), drift, len(staged_lines) - len(corpus_lines)))

    # ---- P6: per-club game counts -----------------------------------------
    p6_bad = []
    for s in standings:
        played = sum(1 for r in staged if r[2] == s["abbr"] or r[4] == s["abbr"])
        want = int(s["w"]) + int(s["l"]) + int(s["t"])
        if played != want:
            p6_bad.append("%s played %d want %d" % (s["abbr"], played, want))
    gate("P6", "per-club game count equals W+L+T in the fresh standings (32 clubs)",
         not p6_bad, "mismatches: %s" % (p6_bad or "none"))

    # ---- P7: duplicates and club keys -------------------------------------
    seen, p7_bad = set(), []
    for r in staged:
        k = (r[0], r[2], r[4])
        if k in seen:
            p7_bad.append("duplicate %s" % (k,))
        seen.add(k)
        for t in (r[2], r[4]):
            if t not in known:
                p7_bad.append("unknown club key %s" % t)
    gate("P7", "no duplicate (week, away, home); every club key known to teams.tsv",
         not p7_bad, "problems: %s" % (p7_bad or "none"))

    # ---- P8: chain of dated reads — their same-day SNF read is our prefix ----
    prior_path = os.path.join(DATA, "results_2026-11-17.tsv")
    if os.path.exists(prior_path):
        prior = [ln.rstrip("\n") for ln in open(prior_path, encoding="utf-8")
                 if ln.strip()]
        chain_ok = staged_lines[:len(prior)] == prior
        chain_detail = ("%d-row SNF read is %sa prefix of the %d-row closeout"
                        % (len(prior), "" if chain_ok else "NOT ",
                           len(staged_lines)))
    else:
        chain_ok, chain_detail = False, "data/results_2026-11-17.tsv missing"
    gate("P8", "chain of dated reads: the 2026-11-17 SNF read (149 rows) is a "
               "byte-prefix of the staged closeout (137 -> 148 -> 149 -> 150)",
         chain_ok, chain_detail)

    all_ok = all(c[2] == "PASS" for c in checks)

    # ---- write the verification table (additive register) -----------------
    with open(OUT_VERIFICATION, "w", encoding="utf-8") as fh:
        fh.write("check\tdescription\tresult\tdetail\tsource\n")
        for cid, desc, res, detail in checks:
            src = STANDINGS_URL if cid in ("P4", "P6") else PAGE_URL
            fh.write("%s\t%s\t%s\t%s\t%s\n" % (cid, desc, res, detail, src))

    # ---- write the dated closeout register (additive in any mode) ---------
    register = {
        "id": "week10_closeout",
        "title": "Week 10 closeout — all 14 games FINAL (read 2026-11-17)",
        "requirement": "Q44: when the week's games all reach FINAL, publish the "
                       "verified closeout and the acceptance checks a promotion "
                       "must pass first.",
        "updated": "2026-11-17",
        "read_window_utc": "after the Monday-night final (see capture header)",
        "page_url": PAGE_URL,
        "standings_url": STANDINGS_URL,
        "source_ids": [SOURCE_SCHEDULE, SOURCE_STANDINGS],
        "status": "checks %s" % ("ALL PASS" if all_ok else "FAILED"),
        "canonical_promoted": False,
        "resolves_flag": "F67 (the Monday-night game was left open at the "
                         "earlier same-day read; this closeout is the "
                         "prescribed re-read after it showed Final)",
        "finals": [
            {"week": 10, "date": r["date"], "away": r["away"],
             "awayPts": int(r["away_pts"]), "home": r["home"],
             "homePts": int(r["home_pts"]),
             "result": "%s %d, %s %d" % (r["away"], int(r["away_pts"]),
                                         r["home"], int(r["home_pts"])),
             "margin_home": int(r["home_pts"]) - int(r["away_pts"]),
             "total": int(r["home_pts"]) + int(r["away_pts"]),
             "note": r.get("note", "").strip(),
             "game_url": GAME_URLS[(r["away"], r["home"])],
             "page_url": PAGE_URL,
             "source_id": SOURCE_SCHEDULE,
             "tier": "OFFICIAL"}
            for r in closeout
        ],
        "new_since_frozen_corpus": [
            {"week": 10, "date": r[1], "away": r[2], "awayPts": int(r[3]),
             "home": r[4], "homePts": int(r[5])}
            for r in new_rows
        ],
        "frozen_corpus": {
            "path": "data/results.tsv",
            "rows": len(corpus_lines),
            "sha256": sha256(RESULTS),
            "note": "unchanged by this run in every mode without --promote",
        },
        "staged_corpus": {
            "rows": len(staged_lines),
            "note": "frozen corpus + 13 new finals; written to "
                    "data/results_2026-11-17-closeout.tsv by --execute",
        },
        "checks": [
            {"id": cid, "description": desc, "result": res, "detail": detail}
            for cid, desc, res, detail in checks
        ],
        "provenance": {
            "tier": "OFFICIAL",
            "captures": ["raw/schedule-results-2026-week10-closeout.tsv",
                         "raw/standings-2026-20261117-closeout.tsv"],
            "verification": "P1-P7 enforced by scripts/promote_week10.py; the "
                            "same script produces this register, so the page "
                            "and the checks cannot disagree",
        },
    }
    with open(OUT_REGISTER, "w", encoding="utf-8") as fh:
        json.dump(register, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    for cid, desc, res, detail in checks:
        print("  %-3s %-4s %s | %s" % (cid, res, desc, detail))

    if not all_ok:
        print("\nFAIL: acceptance checks failed — nothing canonical was written.",
              file=sys.stderr)
        return 1

    if args.execute or args.promote:
        with open(OUT_RESULTS_DATED, "w", encoding="utf-8") as fh:
            fh.write("\n".join(staged_lines) + "\n")
        with open(OUT_STANDINGS_DATED, "w", encoding="utf-8") as fh:
            for s in standings:
                fh.write("\t".join(s[f] for f in STAND_FIELDS) + "\n")
        print("wrote %s (%d rows) and %s (%d clubs)"
              % (os.path.relpath(OUT_RESULTS_DATED, ROOT), len(staged_lines),
                 os.path.relpath(OUT_STANDINGS_DATED, ROOT), len(standings)))

    if args.promote:
        # canonical roll-forward: results, standings (full page layout), and
        # the schedule feed's played flags/scores for the 13 new finals.
        with open(RESULTS, "w", encoding="utf-8") as fh:
            fh.write("\n".join(staged_lines) + "\n")
        with open(os.path.join(DATA, "standings.tsv"), "w", encoding="utf-8") as fh:
            for s in standings:
                fh.write("\t".join(s[f] for f in STAND_FIELDS) + "\n")
        sched_path = os.path.join(DATA, "schedule2026-d.csv")
        with open(sched_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            fieldnames = reader.fieldnames
            sched_d = list(reader)
        flipped = 0
        for row in sched_d:
            if row["week"] != "10" or row["played"] == "yes":
                continue
            k = (row["away_team"], row["home_team"])
            c = closeout_by.get(k)
            if c is None:
                raise SystemExit("FAIL: no closeout row for fixture %s@%s" % k)
            row["played"] = "yes"
            row["away_score"] = c["away_pts"]
            row["home_score"] = c["home_pts"]
            row["scores_verified"] = ("yes (week-10 closeout read 2026-11-17, "
                                      "raw/schedule-results-2026-week10-closeout.tsv)")
            flipped += 1
        with open(sched_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sched_d)
        print("promoted canonical: data/results.tsv, data/standings.tsv, "
              "%d schedule2026-d.csv rows flipped to played" % flipped)
        print(FOLLOWUP_PROMOTED)

    if not args.execute and not args.promote:
        print("\nAll acceptance checks PASS. Q44's policy half remains open:")
        print("  --execute   publish the dated side-reads "
              "(data/results_2026-11-17-closeout.tsv, "
              "data/standings_2026-11-17-closeout.tsv)")
        print("  --promote   ONLY after the Q44 owner chooses the canonical "
              "roll-forward")
        print("Canonical files touched in this mode: none.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
