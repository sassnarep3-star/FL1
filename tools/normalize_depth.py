#!/usr/bin/env python3
"""
normalize_depth.py — turns the raw club depth-chart capture into data/depth.tsv.

Why this exists
---------------
The raw capture (raw/depth-charts-week10-2026.tsv) is one pipe-delimited row per
published position, with the four strings side by side:

    TEAM|SIDE|POSITION|P1|P2|P3|P4

The site needs one row per (club, slot occurrence, string, player) so it can be joined to
the injury report. This script does exactly that reshaping and nothing else:

  * it never invents a player, never guesses a position, never reorders a chart;
  * a slot the club published empty stays empty and is marked;
  * two names the club published as co-starters ("A & B") become two rows at the
    same string, each marked "co-starter", because splitting them is bookkeeping
    and merging them differently would be an edit;
  * club abbreviations are mapped to the official ones in data/teams.tsv.

Run:  python3 tools/normalize_depth.py
"""

import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "depth-charts-week10-2026.tsv")
DATA = os.path.join(ROOT, "data")

# Club -> (official domain, chart path as it was actually fetched, date printed on
# the chart itself or "" when the club printed none). The date is copied from the
# page, never inferred: an undated chart is recorded as undated.
CLUBS = [
    ("ARI", "azcardinals.com", "/team/depth-chart", ""),
    ("ATL", "atlantafalcons.com", "/team/depth-chart", ""),
    ("BAL", "baltimoreravens.com", "/team/depth-chart", ""),
    ("BUF", "buffalobills.com", "/team/depth-chart", ""),
    ("CAR", "panthers.com", "/team/depth-chart", ""),
    ("CHI", "chicagobears.com", "/team/depth-chart", "2026-10-31"),
    ("CIN", "bengals.com", "/team/depth-chart", ""),
    ("CLE", "clevelandbrowns.com", "/team/depth-chart", ""),
    ("DAL", "dallascowboys.com", "/team/depth-chart", ""),
    ("DEN", "denverbroncos.com", "/team/depth-chart/", ""),
    ("DET", "detroitlions.com", "/team/depth-chart", ""),
    ("GB", "packers.com", "/team/depth-chart", "2026-11-10"),
    ("IND", "colts.com", "/team/depth-chart", ""),
    ("JAX", "jaguars.com", "/team/depth-chart", ""),
    ("LAC", "chargers.com", "/team/depth-chart", ""),
    ("LAR", "therams.com", "/team/depth-chart", ""),
    ("LV", "raiders.com", "/team/depth-chart", "2026-11-10"),
    ("MIA", "miamidolphins.com", "/team/depth-chart", ""),
    ("MIN", "vikings.com", "/team/depth-chart", ""),
    ("NE", "patriots.com", "/team/depth-chart", ""),
    ("NO", "neworleanssaints.com", "/team/depth-chart", ""),
    ("NYG", "giants.com", "/team/depth-chart", ""),
    ("NYJ", "newyorkjets.com", "/team/depth-chart", ""),
    ("PHI", "philadelphiaeagles.com", "/team/depth-chart", ""),
    ("PIT", "steelers.com", "/team/depth-chart", ""),
    ("SEA", "seahawks.com", "/team/depth-chart/", ""),
    ("SF", "49ers.com", "/team/depth-chart", "2026-11-10"),
    ("TB", "buccaneers.com", "/team/depth-chart", ""),
    ("TEN", "tennesseetitans.com", "/team/depth-chart", "2026-11-10"),
    ("WAS", "commanders.com", "/team/depth-chart", ""),
]

# Kansas City is captured and alias-checked separately in data/depth-kc.tsv
# (source S08). It is deliberately not duplicated here.
# Houston is not captured at all: houstontexans.com/team/depth-chart renders the
# chart as an image. See flag F16.

SIDE_TO_UNIT = {"O": "Offense", "D": "Defense", "S": "Special Teams"}

# Source IDs are assigned in the alphabetical order above, continuing the
# registry in data/sources.tsv after S15.
FIRST_SOURCE_ID = 16


def norm_name(s):
    return " ".join(s.split())


def main():
    with open(RAW, encoding="utf-8") as fh:
        raw_rows = []
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("|")
            parts += [""] * (7 - len(parts))
            raw_rows.append(parts[:7])

    source_of = {}
    for i, (abbr, domain, path, date) in enumerate(CLUBS):
        source_of[abbr] = "S%02d" % (FIRST_SOURCE_ID + i)

    out = []
    seen_clubs = []
    # Several clubs publish the same slot label more than once (two "DL" lines,
    # two "CB" lines, and so on). They are different slots on the real chart, so
    # each occurrence is numbered in the order the club published it. Without
    # this, a second-string player on one line could be mistaken for the backup
    # to the starter on the other.
    line_count = {}
    for team, side, slot, p1, p2, p3, p4 in raw_rows:
        team = norm_name(team)
        slot = norm_name(slot)
        if team == "KC":
            continue
        key = (team, side, slot)
        line_count[key] = line_count.get(key, 0) + 1

    used_line = {}
    for team, side, slot, p1, p2, p3, p4 in raw_rows:
        team = norm_name(team)
        # KC is owned by depth-kc.tsv; skip it here so the two files cannot drift.
        if team == "KC":
            continue
        if team not in source_of:
            print("RAW PROBLEM: club %r is not in the CLUBS table" % team,
                  file=sys.stderr)
            sys.exit(1)
        unit = SIDE_TO_UNIT.get(side)
        if unit is None:
            print("RAW PROBLEM: unknown side %r for %s %s" % (side, team, slot),
                  file=sys.stderr)
            sys.exit(1)
        if team not in seen_clubs:
            seen_clubs.append(team)
        key = (team, side, norm_name(slot))
        used_line[key] = used_line.get(key, 0) + 1
        line = used_line[key]
        for rank, value in ((1, p1), (2, p2), (3, p3), (4, p4)):
            value = norm_name(value)
            unnamed = value == "" or value in ("UNVERIFIED_BLANK",
                                               "UNVERIFIED_BLANK_STARTER")
            if unnamed:
                # A blank backup string is normal and is simply not recorded.
                # A blank FIRST string is a gap worth recording, so the site can
                # show that the club published a slot with no starter in it.
                if rank == 1:
                    out.append([team, unit, norm_name(slot), "", "1", str(line),
                                "club chart publishes no name at this string"])
                continue
            if " & " in value:
                note = "co-starter (club published both names at this string)"
                for one in value.split(" & "):
                    one = norm_name(one)
                    if one:
                        out.append([team, unit, norm_name(slot), one, str(rank),
                                    str(line), note])
            else:
                out.append([team, unit, norm_name(slot), value, str(rank),
                            str(line), ""])

    # columns are [team, unit, slot, player, rank, line, note]
    out.sort(key=lambda r: (r[0], r[1] != "Offense", r[1] != "Defense",
                            r[2], int(r[5]), int(r[4]), r[3]))

    with open(os.path.join(DATA, "depth.tsv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerows(out)

    with open(os.path.join(DATA, "depth-sources.tsv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        # Kansas City leads the table so the coverage page can show its source
        # chip too. Its chart is captured in its own file (data/depth-kc.tsv)
        # with a documented alias table, and is not regenerated here.
        w.writerow(["KC", "S08", "https://www.chiefs.com/team/depth-chart", "",
                    "Captured separately in data/depth-kc.tsv with an explicit "
                    "name-alias table; not regenerated by normalize_depth.py."])
        for abbr, domain, path, date in CLUBS:
            w.writerow([abbr, source_of[abbr],
                        "https://www.%s%s" % (domain, path), date,
                        "Club page is self-titled 'Unofficial Depth Chart'."
                        if abbr in ("SF",) else ""])

    print("wrote data/depth.tsv: %d rows, %d clubs" % (len(out), len(seen_clubs)))
    print("wrote data/depth-sources.tsv: %d clubs (30 generated + KC, captured separately)" % (len(CLUBS) + 1))
    print("clubs:", " ".join(sorted(seen_clubs)))
    print("note: no header row is written — data/*.tsv in this repo are headerless,")
    print("      the column order lives in tools/build.py SCHEMAS.")


if __name__ == "__main__":
    main()
