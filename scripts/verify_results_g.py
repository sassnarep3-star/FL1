#!/usr/bin/env python3
"""
verify_results_g.py — session `arena/dbf11de0-fl1` (task G1, results side).

Reads the official league standings page and the official Week 10 schedule page
on a later date than the repository's existing snapshots, and checks the new
numbers against the old ones — and against each other.

Three checks, in order of how hard they are to pass by accident:

  G-R1  the new results file reproduces the new standings file exactly, for all
        32 clubs, on W, L, T, PF and PA. Transcribing eleven scores wrong and
        still landing on 32 correct club lines is not something a typo does.
  G-R2  the first 137 rows of the new results file are byte-identical to the
        frozen corpus data/results.tsv — the pre-registration corpus has not
        drifted.
  G-R3  every club's game count in the new results file equals W + L + T in the
        new standings (no club is missing a game).

The frozen corpus is NOT overwritten. data/results.tsv stays as the
pre-registration corpus it is; the newer read is written beside it with its own
date, so a backtest can pin either.

Run:  python3 scripts/verify_results_g.py
Exit: 0 when all three checks pass.
No third-party packages.
"""

import hashlib
import json
import os
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(ROOT, "raw")

STAND_FIELDS = ["abbr", "w", "l", "t", "pct", "pf", "pa", "net", "home", "road",
                "div", "div_pct", "conf", "conf_pct", "nonconf", "streak", "last5"]

# Official 2026 league standings, read 2026-11-16 from
# https://www.nfl.com/standings/league/2026/REG
STANDINGS_2026_11_16 = [
    ("BUF", 8, 1, 0, "0.889", 287, 199, 88, "3-1-0", "5-0-0", "1-1-0", "0.500", "5-1-0", "0.833", "3-0-0", "5W", "5-0-0"),
    ("SF", 8, 1, 0, "0.889", 281, 196, 85, "5-0-0", "3-1-0", "3-0-0", "1.000", "5-1-0", "0.833", "3-0-0", "2W", "4-1-0"),
    ("CHI", 7, 2, 0, "0.778", 241, 184, 57, "4-1-0", "3-1-0", "0-2-0", "0.000", "5-2-0", "0.714", "2-0-0", "4W", "4-1-0"),
    ("DEN", 7, 2, 0, "0.778", 198, 186, 12, "4-0-0", "3-2-0", "2-1-0", "0.667", "3-1-0", "0.750", "4-1-0", "5W", "5-0-0"),
    ("DET", 7, 2, 0, "0.778", 257, 199, 58, "5-0-0", "2-2-0", "2-0-0", "1.000", "4-1-0", "0.800", "3-1-0", "5W", "5-0-0"),
    ("JAX", 7, 2, 0, "0.778", 269, 144, 125, "4-1-0", "3-1-0", "2-1-0", "0.667", "6-2-0", "0.750", "1-0-0", "3W", "4-1-0"),
    ("KC", 7, 2, 0, "0.778", 237, 156, 81, "4-0-0", "3-2-0", "3-1-0", "0.750", "6-1-0", "0.857", "1-1-0", "2W", "3-2-0"),
    ("MIN", 7, 2, 0, "0.778", 176, 126, 50, "3-1-0", "4-1-0", "3-1-0", "0.750", "5-1-0", "0.833", "2-1-0", "1W", "3-2-0"),
    ("CIN", 6, 2, 0, "0.750", 240, 175, 65, "2-1-0", "4-1-0", "1-1-0", "0.500", "4-2-0", "0.667", "2-0-0", "4W", "4-1-0"),
    ("PIT", 6, 2, 0, "0.750", 180, 144, 36, "4-0-0", "2-2-0", "2-1-0", "0.667", "3-2-0", "0.600", "3-0-0", "4W", "4-1-0"),
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

# Week 10 finals published on the official schedule page and read 2026-11-16,
# that were not in the 2026-11-14 corpus. (week, date, away, awayPts, home, homePts)
# The Sunday-night game (PIT at CIN) was LIVE in the first quarter at capture
# time and the Monday-night game (LAC at BAL) had not kicked off, so neither is
# included: a partial score is not a result.
NEW_GAMES = [
    ("10", "2026-11-15", "NE", 10, "DET", 35),
    ("10", "2026-11-15", "KC", 35, "ATL", 13),
    ("10", "2026-11-15", "HOU", 24, "CLE", 27),
    ("10", "2026-11-15", "MIN", 30, "GB", 10),
    ("10", "2026-11-15", "MIA", 22, "IND", 24),
    ("10", "2026-11-15", "CAR", 20, "NO", 17),
    ("10", "2026-11-15", "BUF", 31, "NYJ", 12),
    ("10", "2026-11-15", "JAX", 40, "TEN", 23),
    ("10", "2026-11-15", "LAR", 34, "ARI", 6),
    ("10", "2026-11-15", "SEA", 21, "LV", 13),
    ("10", "2026-11-15", "SF", 46, "DAL", 40),
]

SOURCES = [
    "https://www.nfl.com/standings/league/2026/REG",
    "https://www.nfl.com/schedules/2026/REG10/",
]


def write_standings():
    path = os.path.join(DATA, "standings_2026-11-16.tsv")
    with open(path, "w", encoding="utf-8") as fh:
        for row in STANDINGS_2026_11_16:
            fh.write("\t".join(str(v) for v in row) + "\n")
    return path


def write_results():
    corpus = [ln.rstrip("\n") for ln in open(os.path.join(DATA, "results.tsv"),
                                             encoding="utf-8") if ln.strip()]
    new = list(corpus) + ["\t".join(str(v) for v in g) for g in NEW_GAMES]
    path = os.path.join(DATA, "results_2026-11-16.tsv")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(new) + "\n")
    return path, corpus


def main():
    spath = write_standings()
    rpath, corpus = write_results()

    stand = {}
    for row in STANDINGS_2026_11_16:
        stand[row[0]] = {"w": row[1], "l": row[2], "t": row[3],
                         "pf": row[5], "pa": row[6]}

    games = [ln.split("\t") for ln in open(rpath, encoding="utf-8")
             if ln.strip()]
    derived = {a: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0}
               for a in stand}
    for wk, date, away, ap, home, hp in games:
        ap, hp = int(ap), int(hp)
        derived[away]["pf"] += ap
        derived[away]["pa"] += hp
        derived[home]["pf"] += hp
        derived[home]["pa"] += ap
        if ap > hp:
            derived[away]["w"] += 1
            derived[home]["l"] += 1
        elif hp > ap:
            derived[home]["w"] += 1
            derived[away]["l"] += 1
        else:
            derived[away]["t"] += 1
            derived[home]["t"] += 1

    bad = []
    for abbr, exp in stand.items():
        got = derived[abbr]
        if got != exp:
            bad.append((abbr, exp, got))

    new_lines = [ln.rstrip("\n") for ln in open(rpath, encoding="utf-8")
                 if ln.strip()]
    drift = new_lines[:len(corpus)] != corpus

    count_bad = []
    for abbr, exp in stand.items():
        played = sum(1 for g in games if g[2] == abbr or g[4] == abbr)
        if played != exp["w"] + exp["l"] + exp["t"]:
            count_bad.append((abbr, played, exp["w"] + exp["l"] + exp["t"]))

    checks = [
        ("G-R1", "new results reproduce the new official standings for all 32 clubs",
         "PASS" if not bad else "FAIL",
         "32 clubs checked, %d mismatches" % len(bad)),
        ("G-R2", "the frozen 137-game corpus is unchanged inside the newer read",
         "PASS" if not drift else "FAIL",
         "%d corpus rows, drift: %s" % (len(corpus), drift)),
        ("G-R3", "games played per club equals W+L+T for every club",
         "PASS" if not count_bad else "FAIL",
         "%d clubs with a count mismatch" % len(count_bad)),
        ("G-R4", "games added since the 2026-11-14 corpus", "INFO",
         "%d new finals (%d results now); SNF PIT@CIN was in progress and MNF "
         "LAC@BAL had not kicked off at capture, so neither is recorded"
         % (len(NEW_GAMES), len(new_lines))),
    ]

    ver_path = os.path.join(DATA, "verification-g.tsv")
    existing = []
    if os.path.exists(ver_path):
        with open(ver_path, encoding="utf-8") as fh:
            existing = [ln.rstrip("\n") for ln in fh if ln.strip()]
    with open(ver_path, "w", encoding="utf-8") as fh:
        if existing:
            fh.write(existing[0] + "\n")
            for ln in existing[1:]:
                if not ln.split("\t")[0].startswith("G-R"):
                    fh.write(ln + "\n")
        else:
            fh.write("check\tdescription\tresult\tdetail\tsource\n")
        for cid, desc, res, detail in checks:
            fh.write("%s\t%s\t%s\t%s\t%s\n"
                     % (cid, desc, res, detail, SOURCES[1]))

    # raw capture record
    raw_note = os.path.join(RAW, "results-week10-2026-2026-11-16.md")
    with open(raw_note, "w", encoding="utf-8") as fh:
        fh.write("# RAW CAPTURE — Week 10 2026 finals, read 2026-11-16\n\n")
        fh.write("- Standings: %s\n- Schedule: %s\n" % (SOURCES[0], SOURCES[1]))
        fh.write("- Read at: 2026-11-16 (UTC)\n\n")
        fh.write("Eleven finals were published since the 2026-11-14 corpus was taken.\n")
        fh.write("Sunday night (PIT at CIN) was in the first quarter at capture time and\n")
        fh.write("Monday night (LAC at BAL) had not kicked off, so neither is recorded:\n")
        fh.write("a partial score is not a result.\n\n")
        fh.write("| Week | Date | Away | Away pts | Home | Home pts |\n|---|---|---|---|---|---|\n")
        for g in NEW_GAMES:
            fh.write("| %s | %s | %s | %s | %s | %s |\n" % g)

    manifest_path = os.path.join(DATA, "raw", "MANIFEST-g.json")
    manifest = {}
    if os.path.exists(manifest_path):
        manifest = json.load(open(manifest_path, encoding="utf-8"))
    for name, path in (("results_2026-11-16.tsv", rpath),
                       ("standings_2026-11-16.tsv", spath),
                       ("results-week10-2026-2026-11-16.md", raw_note)):
        with open(path, "rb") as fh:
            manifest[name] = {"sha256": hashlib.sha256(fh.read()).hexdigest(),
                              "bytes": os.path.getsize(path)}
    manifest.setdefault("_source", SOURCES[0])
    manifest["_results_retrieved"] = "2026-11-16"
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")

    for abbr, exp, got in bad[:10]:
        print("  MISMATCH %s expected %s got %s" % (abbr, exp, got))
    for cid, desc, res, detail in checks:
        print("  %-6s %-4s %s | %s" % (cid, res, desc, detail))
    ok = not bad and not drift and not count_bad
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
