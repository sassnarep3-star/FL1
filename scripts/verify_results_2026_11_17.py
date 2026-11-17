#!/usr/bin/env python3
"""
verify_results_2026_11_17.py — session `arena/e97f05c3-fl1` (task H1).

Adds ONE newly official final to the Week 10 2026 results read and proves it
against the official standings page read on the same day:

  NEW FINAL  Week 10, 2026-11-15, Steelers (PIT) 18 at Bengals (CIN) 38
             Source: https://www.nfl.com/games/steelers-at-bengals-2026-reg-10
             (status "Final", quarter scores 0-3-0-15 / 3-21-7-7, sum 18 / 38)

NOT ADDED  Monday night, LAC at BAL. Read 2026-11-17 as "Q2 01:56, Chargers 17,
           Ravens 7, Live" at https://www.nfl.com/games/chargers-at-ravens-2026-reg-10?tab=live
           A live score is not a final result and is not recorded.

Checks (all must pass; any failure makes the script exit 1):

  H-R1  the new results file = the 2026-11-16 results file + exactly one row.
  H-R2  the new results file reproduces the new official standings for all 32
        clubs on W, L, T, PF and PA (derived from the games, not copied).
  H-R3  games played per club = W + L + T in the new official standings.
  H-R4  the change between the 2026-11-16 and 2026-11-17 official standings is
        EXACTLY the new game: only CIN and PIT move, by the amounts the score implies.
  H-R5  the frozen 137-game corpus data/results.tsv is still a prefix of the file.

Run:  python3 scripts/verify_results_2026_11_17.py
No third-party packages.
"""

import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(ROOT, "raw")

GAME_SRC = "https://www.nfl.com/games/steelers-at-bengals-2026-reg-10"
STAND_SRC = "https://www.nfl.com/standings/league/2026/REG"
SCHED_SRC = "https://www.nfl.com/schedules/2026/REG10/"
MNF_SRC = "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10?tab=live"

NEW_GAME = ("10", "2026-11-15", "PIT", 18, "CIN", 38)

# Official standings, read 2026-11-17 from https://www.nfl.com/standings/league/2026/REG
# Columns: abbr, W, L, T, PCT, PF, PA, NET, HOME, ROAD, DIV, DIV_PCT, CONF, CONF_PCT,
#          NONCONF, STREAK, LAST5
STANDINGS_2026_11_17 = [
    ("BUF", 8, 1, 0, "0.889", 287, 199, 88, "3-1-0", "5-0-0", "1-1-0", "0.500", "5-1-0", "0.833", "3-0-0", "5W", "5-0-0"),
    ("SF", 8, 1, 0, "0.889", 281, 196, 85, "5-0-0", "3-1-0", "3-0-0", "1.000", "5-1-0", "0.833", "3-0-0", "2W", "4-1-0"),
    ("CHI", 7, 2, 0, "0.778", 241, 184, 57, "4-1-0", "3-1-0", "0-2-0", "0.000", "5-2-0", "0.714", "2-0-0", "4W", "4-1-0"),
    ("CIN", 7, 2, 0, "0.778", 278, 193, 85, "3-1-0", "4-1-0", "2-1-0", "0.667", "5-2-0", "0.714", "2-0-0", "5W", "5-0-0"),
    ("DEN", 7, 2, 0, "0.778", 198, 186, 12, "4-0-0", "3-2-0", "2-1-0", "0.667", "3-1-0", "0.750", "4-1-0", "5W", "5-0-0"),
    ("DET", 7, 2, 0, "0.778", 257, 199, 58, "5-0-0", "2-2-0", "2-0-0", "1.000", "4-1-0", "0.800", "3-1-0", "5W", "5-0-0"),
    ("JAX", 7, 2, 0, "0.778", 269, 144, 125, "4-1-0", "3-1-0", "2-1-0", "0.667", "6-2-0", "0.750", "1-0-0", "3W", "4-1-0"),
    ("KC", 7, 2, 0, "0.778", 237, 156, 81, "4-0-0", "3-2-0", "3-1-0", "0.750", "6-1-0", "0.857", "1-1-0", "2W", "3-2-0"),
    ("MIN", 7, 2, 0, "0.778", 176, 126, 50, "3-1-0", "4-1-0", "3-1-0", "0.750", "5-1-0", "0.833", "2-1-0", "1W", "3-2-0"),
    ("PIT", 6, 3, 0, "0.667", 198, 182, 16, "4-0-0", "2-3-0", "2-2-0", "0.500", "3-3-0", "0.500", "3-0-0", "1L", "4-1-0"),
    ("NYG", 5, 3, 1, "0.611", 203, 196, 7, "3-2-0", "2-1-1", "2-1-1", "0.625", "3-3-1", "0.500", "2-0-0", "1L", "2-2-1"),
    ("CLE", 6, 4, 0, "0.600", 188, 220, -32, "4-0-0", "2-4-0", "2-1-0", "0.667", "4-3-0", "0.571", "2-1-0", "1W", "3-2-0"),
    ("GB", 6, 4, 0, "0.600", 226, 221, 5, "3-2-0", "3-2-0", "1-3-0", "0.250", "4-4-0", "0.500", "2-0-0", "1L", "3-2-0"),
    ("LAR", 6, 4, 0, "0.600", 248, 187, 61, "2-3-0", "4-1-0", "1-2-0", "0.333", "4-2-0", "0.667", "2-2-0", "4W", "4-1-0"),
    ("SEA", 6, 4, 0, "0.600", 223, 175, 48, "4-2-0", "2-2-0", "2-1-0", "0.667", "2-3-0", "0.400", "4-1-0", "2W", "3-2-0"),
    ("NE", 5, 5, 0, "0.500", 221, 242, -21, "3-1-0", "2-4-0", "3-0-0", "1.000", "5-1-0", "0.833", "0-4-0", "2L", "2-3-0"),
    ("BAL", 4, 5, 0, "0.444", 189, 236, -47, "1-3-0", "3-2-0", "0-2-0", "0.000", "2-4-0", "0.333", "2-1-0", "4L", "1-4-0"),
    ("CAR", 4, 5, 0, "0.444", 219, 236, -17, "1-3-0", "3-2-0", "2-1-0", "0.667", "4-3-0", "0.571", "0-2-0", "1W", "2-3-0"),
    ("DAL", 4, 6, 0, "0.400", 286, 282, 4, "1-4-0", "3-2-0", "2-1-0", "0.667", "2-5-0", "0.286", "2-1-0", "1L", "2-3-0"),
    ("LV", 4, 6, 0, "0.400", 251, 289, -38, "1-4-0", "3-2-0", "1-1-0", "0.500", "3-3-0", "0.500", "1-3-0", "2L", "1-4-0"),
    ("WAS", 3, 5, 1, "0.389", 196, 223, -27, "2-2-1", "1-3-0", "2-2-1", "0.500", "3-4-1", "0.438", "0-1-0", "1W", "2-2-1"),
    ("HOU", 3, 6, 0, "0.333", 233, 219, 14, "0-4-0", "3-2-0", "2-1-0", "0.667", "3-4-0", "0.429", "0-2-0", "1L", "3-2-0"),
    ("NO", 3, 6, 0, "0.333", 202, 236, -34, "1-5-0", "2-1-0", "0-2-0", "0.000", "1-4-0", "0.200", "2-2-0", "1L", "2-3-0"),
    ("TB", 3, 6, 0, "0.333", 202, 178, 24, "1-4-0", "2-2-0", "2-0-0", "1.000", "3-3-0", "0.500", "0-3-0", "1L", "3-2-0"),
    ("ARI", 3, 7, 0, "0.300", 184, 289, -105, "0-4-0", "3-3-0", "1-4-0", "0.200", "2-6-0", "0.250", "1-1-0", "2L", "2-3-0"),
    ("ATL", 3, 7, 0, "0.300", 201, 258, -57, "1-5-0", "2-2-0", "1-2-0", "0.333", "3-3-0", "0.500", "0-4-0", "3L", "1-4-0"),
    ("IND", 3, 7, 0, "0.300", 208, 271, -63, "2-3-0", "1-4-0", "1-2-0", "0.333", "2-5-0", "0.286", "1-2-0", "1W", "1-4-0"),
    ("PHI", 2, 7, 0, "0.222", 148, 221, -73, "1-4-0", "1-3-0", "1-3-0", "0.250", "1-6-0", "0.143", "1-1-0", "7L", "0-5-0"),
    ("NYJ", 2, 8, 0, "0.200", 194, 254, -60, "1-4-0", "1-4-0", "0-3-0", "0.000", "2-5-0", "0.286", "0-3-0", "5L", "0-5-0"),
    ("MIA", 1, 8, 0, "0.111", 148, 224, -76, "0-4-0", "1-4-0", "1-1-0", "0.500", "1-5-0", "0.167", "0-3-0", "3L", "1-4-0"),
    ("TEN", 1, 8, 0, "0.111", 167, 239, -72, "0-5-0", "1-3-0", "1-2-0", "0.333", "1-6-0", "0.143", "0-2-0", "3L", "1-4-0"),
    ("LAC", 0, 8, 0, "0.000", 121, 219, -98, "0-4-0", "0-4-0", "0-3-0", "0.000", "0-5-0", "0.000", "0-3-0", "8L", "0-5-0"),
]

STAND_FIELDS = ["abbr", "w", "l", "t", "pct", "pf", "pa", "net", "home", "road",
                "div", "div_pct", "conf", "conf_pct", "nonconf", "streak", "last5"]


def read_lines(path):
    with open(path, encoding="utf-8") as fh:
        return [ln.rstrip("\n") for ln in fh if ln.strip()]


def read_standings(path):
    out = {}
    for ln in read_lines(path):
        f = ln.split("\t")
        out[f[0]] = dict(zip(STAND_FIELDS, f))
    return out


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def derive(games, clubs):
    d = {a: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "gp": 0} for a in clubs}
    for wk, date, away, ap, home, hp in games:
        ap, hp = int(ap), int(hp)
        d[away]["pf"] += ap; d[away]["pa"] += hp
        d[home]["pf"] += hp; d[home]["pa"] += ap
        d[away]["gp"] += 1; d[home]["gp"] += 1
        if ap > hp:
            d[away]["w"] += 1; d[home]["l"] += 1
        elif hp > ap:
            d[home]["w"] += 1; d[away]["l"] += 1
        else:
            d[away]["t"] += 1; d[home]["t"] += 1
    return d


def parse_games(path):
    out = []
    for ln in read_lines(path):
        wk, date, away, ap, home, hp = ln.split("\t")
        out.append((wk, date, away, int(ap), home, int(hp)))
    return out


def main():
    old_res_path = os.path.join(DATA, "results_2026-11-16.tsv")
    old_stand_path = os.path.join(DATA, "standings_2026-11-16.tsv")
    corpus_path = os.path.join(DATA, "results.tsv")
    new_res_path = os.path.join(DATA, "results_2026-11-17.tsv")
    new_stand_path = os.path.join(DATA, "standings_2026-11-17.tsv")

    old_lines = read_lines(old_res_path)
    new_lines = old_lines + ["\t".join(str(v) for v in NEW_GAME)]
    with open(new_res_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(new_lines) + "\n")
    with open(new_stand_path, "w", encoding="utf-8") as fh:
        for row in STANDINGS_2026_11_17:
            fh.write("\t".join(str(v) for v in row) + "\n")

    clubs = [r[0] for r in STANDINGS_2026_11_17]
    live = {r[0]: dict(zip(STAND_FIELDS, [str(v) for v in r])) for r in STANDINGS_2026_11_17}
    old_stand = read_standings(old_stand_path)
    games_new = parse_games(new_res_path)
    games_old = parse_games(old_res_path)
    corpus = read_lines(corpus_path)

    checks = []

    # H-R1
    r1 = (len(new_lines) == len(old_lines) + 1 and new_lines[:-1] == old_lines
          and new_lines[-1] == "\t".join(str(v) for v in NEW_GAME))
    checks.append(("H-R1", "new results = 2026-11-16 results + exactly one row (the PIT@CIN final)",
                   "PASS" if r1 else "FAIL", "%d rows (was %d)" % (len(new_lines), len(old_lines))))

    # H-R2
    d = derive(games_new, clubs)
    bad2 = []
    for a in clubs:
        L = live[a]
        got = (d[a]["w"], d[a]["l"], d[a]["t"], d[a]["pf"], d[a]["pa"])
        exp = (int(L["w"]), int(L["l"]), int(L["t"]), int(L["pf"]), int(L["pa"]))
        if got != exp:
            bad2.append((a, exp, got))
    checks.append(("H-R2", "new results reproduce the 2026-11-17 official standings, 32 clubs, W/L/T/PF/PA",
                   "PASS" if not bad2 else "FAIL", "32 clubs, %d mismatches" % len(bad2)))

    # H-R3
    bad3 = [a for a in clubs if d[a]["gp"] != int(live[a]["w"]) + int(live[a]["l"]) + int(live[a]["t"])]
    checks.append(("H-R3", "games played per club = W+L+T (official)",
                   "PASS" if not bad3 else "FAIL", "%d clubs with a count mismatch" % len(bad3)))

    # H-R4: the standings change is exactly the new game
    moved = []
    exp_moved = {}
    _, _, a_, ap_, h_, hp_ = NEW_GAME
    exp_moved[a_] = (ap_, hp_, 0 if ap_ > hp_ else 1 if ap_ < hp_ else 0)
    exp_moved[h_] = (hp_, ap_, 0 if hp_ > ap_ else 1 if hp_ < ap_ else 0)
    bad4 = []
    for a in clubs:
        o, n = old_stand[a], live[a]
        dpf = int(n["pf"]) - int(o["pf"])
        dpa = int(n["pa"]) - int(o["pa"])
        dw = int(n["w"]) - int(o["w"])
        dl = int(n["l"]) - int(o["l"])
        dt = int(n["t"]) - int(o["t"])
        if a in exp_moved:
            pf_add, pa_add, _ = exp_moved[a]
            ok = (dpf == pf_add and dpa == pa_add and dt == 0 and
                  ((dw, dl) == (1, 0) if pf_add > pa_add else (dw, dl) == (0, 1)))
            moved.append(a)
        else:
            ok = (dpf, dpa, dw, dl, dt) == (0, 0, 0, 0, 0)
        if not ok:
            bad4.append((a, (dpf, dpa, dw, dl, dt)))
    checks.append(("H-R4", "standings change between the two reads = exactly the new game (only %s move)"
                   % " and ".join(sorted(moved)),
                   "PASS" if not bad4 else "FAIL", "32 clubs, %d unexplained changes" % len(bad4)))

    # H-R5
    prefix = old_lines[:len(corpus)] == corpus
    checks.append(("H-R5", "frozen 137-game corpus data/results.tsv is still a prefix of the results",
                   "PASS" if prefix else "FAIL", "%d corpus rows; prefix intact: %s" % (len(corpus), prefix)))

    # Verification register (own file; does not touch other sessions' registers)
    ver_path = os.path.join(DATA, "verification-2026-11-17.tsv")
    with open(ver_path, "w", encoding="utf-8") as fh:
        fh.write("check\tdescription\tresult\tdetail\tsource\n")
        for cid, desc, res, detail in checks:
            src = GAME_SRC if cid in ("H-R1", "H-R2", "H-R3", "H-R5") else STAND_SRC
            fh.write("%s\t%s\t%s\t%s\t%s\n" % (cid, desc, res, detail, src))
        fh.write("H-N1\tMonday night LAC@BAL NOT recorded: live at read time (Q2 01:56, LAC 17, BAL 7)"
                 "\tOPEN\tnot final; re-read required before it can enter any results file\t%s\n" % MNF_SRC)

    # Raw capture note
    raw_note = os.path.join(RAW, "results-week10-2026-2026-11-17.md")
    with open(raw_note, "w", encoding="utf-8") as fh:
        fh.write("# RAW CAPTURE — Week 10 2026 finals, read 2026-11-17\n\n")
        fh.write("- Game Center (Sunday night): %s — status Final, \"PIT 18 / CIN 38\", quarter scores PIT 0-3-0-15, CIN 3-21-7-7\n" % GAME_SRC)
        fh.write("- Schedule: %s — printed \"Steelers 18, Bengals 38, FINAL, Sunday, November 15th\"\n" % SCHED_SRC)
        fh.write("- Standings: %s (all 32 clubs; transcribed to data/standings_2026-11-17.tsv)\n" % STAND_SRC)
        fh.write("- Monday night: %s — read as Q2 01:56, Chargers 17, Ravens 7, status Live. NOT recorded.\n\n" % MNF_SRC)
        fh.write("| Week | Date | Away | Away pts | Home | Home pts |\n|---|---|---|---|---|---|\n")
        fh.write("| %s | %s | %s | %s | %s | %s |\n" % NEW_GAME)

    # Manifest (hashes), same convention as MANIFEST-g.json
    manifest_path = os.path.join(DATA, "raw", "MANIFEST-h.json")
    manifest = {}
    for name, path in (("results_2026-11-17.tsv", new_res_path),
                       ("standings_2026-11-17.tsv", new_stand_path),
                       ("results-week10-2026-2026-11-17.md", raw_note),
                       ("verification-2026-11-17.tsv", ver_path)):
        manifest[name] = {"sha256": sha256(path), "bytes": os.path.getsize(path)}
    manifest["_retrieved"] = "2026-11-17"
    manifest["_sources"] = [GAME_SRC, STAND_SRC, SCHED_SRC, MNF_SRC]
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")

    for a, exp, got in bad2[:10]:
        print("  MISMATCH(H-R2) %s expected %s got %s" % (a, exp, got))
    for a, dd in bad4[:10]:
        print("  UNEXPLAINED(H-R4) %s delta %s" % (a, dd))
    for cid, desc, res, detail in checks:
        print("  %-5s %-4s %s | %s" % (cid, res, desc, detail))
    ok = all(c[2] == "PASS" for c in checks)
    print("GATE", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
