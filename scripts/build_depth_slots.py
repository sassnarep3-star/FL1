#!/usr/bin/env python3
"""
build_depth_slots.py — publish the club depth charts as SLOT GROUPS.

WHAT IT DOES
    Reads the committed official depth-chart capture (data/depth.tsv for the 30
    clubs captured from their own pages, data/depth-kc.tsv for Kansas City) and
    writes one row per published *slot group*:

        data/depth_slots.tsv        one row per (club, unit, slot, occurrence)
        data/depth_slot_summary.json the counts the page and the tests read

WHY A SEPARATE FILE
    data/depth.tsv is a flat list of names, one per line. It cannot express
    "this slot has two names at the first string" or "this slot has no name at
    the first string" as anything other than two rows that look like two
    different slots. The slot-group file says so explicitly, and the
    replacement-depth logic is built on top of it.

Run:  python3 scripts/build_depth_slots.py
"""

from __future__ import annotations

import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import depth_slots as ds   # noqa: E402


def load_teams() -> dict:
    out = {}
    path = os.path.join(ROOT, "data", "teams.tsv")
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.reader(fh, delimiter="\t"):
            if len(r) >= 2:
                out[r[0].strip()] = r[1].strip()
    return out


def main() -> int:
    rows = ds.load_depth_rows(ROOT)
    groups = ds.build_groups(rows)
    sources = ds.load_depth_sources(ROOT)
    teams = load_teams()
    out_rows = ds.publishable_rows(groups, teams, sources)
    ds.write_tsv(os.path.join(ROOT, "data", "depth_slots.tsv"), ds.SLOT_FIELDS, out_rows)

    summary = ds.summarise(groups)
    summary["clubs"] = sorted({g.team for g in groups.values()})
    summary["n_clubs"] = len(summary["clubs"])
    summary["clubs_with_no_chart"] = sorted(set(teams) - set(summary["clubs"]))
    summary["empty_slots"] = {
        g.slot_id: [n["player"] for n in g.names]
        for g in groups.values() if g.state == "empty"
    }
    summary["source_capture"] = {
        abbr: {"source": s.get("source", ""), "url": s.get("url", ""),
               "chart_date": s.get("chart_date", "")}
        for abbr, s in sorted(sources.items())
    }
    with open(os.path.join(ROOT, "data", "depth_slot_summary.json"), "w",
              encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)

    print("wrote data/depth_slots.tsv: %d slot groups" % len(out_rows))
    print("  single  %d" % summary["single"])
    print("  shared  %d" % summary["shared"])
    print("  empty   %d" % summary["empty"])
    print("  clubs captured: %d of %d" % (summary["n_clubs"], len(teams)))
    if summary["clubs_with_no_chart"]:
        print("  clubs with no official chart captured: %s"
              % " ".join(summary["clubs_with_no_chart"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
