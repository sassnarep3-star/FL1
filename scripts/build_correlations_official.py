#!/usr/bin/env python3
"""Build data/correlations_official.json (requirement R27).

Rule enforced here and in engine/corr_official.py: ONLY officially sourced
numbers enter this register, and EVERY published value carries its n. Rows
computed from third-party captures (measured.json, prop-correlations-d.csv,
correlations.csv) are deliberately excluded — they live on their own labelled
pages and are listed below as excluded, so a reader can see the boundary.

Official inputs only:
    data/standings.tsv   (S03, official standings capture)
    data/results.tsv     (S52, official schedule/results capture)
    data/injuries.tsv + data/week10_2026_official.csv (S01, official injury report)

Run:  python3 scripts/build_correlations_official.py
"""

import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from engine import corr_official  # noqa: E402
import build  # noqa: E402

DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "correlations_official.json")

OFFICIAL = {"S01", "S02", "S03", "S04", "S05", "S06", "S09", "S10", "S49", "S52"}


def rest_asymmetry(results):
    """rest days for each club per game from the official result dates;
    a game counts only when BOTH clubs have a prior game in the feed."""
    from datetime import date
    last = {}
    pairs = []
    for r in sorted(results, key=lambda x: x["date"]):
        d = date.fromisoformat(r["date"])
        rh = ra = None
        if r["home"] in last:
            rh = (d - last[r["home"]]).days
        if r["away"] in last:
            ra = (d - last[r["away"]]).days
        last[r["home"]] = last[r["away"]] = d
        if rh is not None and ra is not None:
            pairs.append((rh - ra, float(r["homePts"]) - float(r["awayPts"])))
    return pairs


def main() -> int:
    standings = build.load("standings.tsv")
    results = build.load("results.tsv")

    recs = []

    # C-A1: season point differential per game vs win percentage, 32 clubs.
    xs = [(float(s["pf"]) - float(s["pa"])) / max(1, int(s["w"]) + int(s["l"]) + int(s["t"]))
          for s in standings]
    ys = [float(s["pct"]) for s in standings]
    recs.append(corr_official.CorrRecord.build(
        "C-A1", "Season point differential per game vs win percentage",
        "(PF-PA)/G", "Win pct",
        xs, ys, ["S03"], OFFICIAL,
        "32 official standing rows (S03); one row per club").as_row())

    # C-A2: home margin vs game total, 137 games.
    xs = [float(r["homePts"]) - float(r["awayPts"]) for r in results]
    ys = [float(r["homePts"]) + float(r["awayPts"]) for r in results]
    recs.append(corr_official.CorrRecord.build(
        "C-A2", "Home margin vs game total (blowouts push totals up)",
        "Home margin", "Game total",
        xs, ys, ["S52"], OFFICIAL,
        "137 official result rows (S52)").as_row())

    # C-A3: rest-days asymmetry vs home margin.
    pairs = rest_asymmetry(results)
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    recs.append(corr_official.CorrRecord.build(
        "C-A3", "Rest-days asymmetry (home minus away) vs home margin",
        "Rest edge (days)", "Home margin",
        xs, ys, ["S52"], OFFICIAL,
        "official result dates (S52); games where either club had no prior "
        "game in the feed are excluded, n counts the rest").as_row())

    # C-A4: paired availability vs margin — BLOCKED at n=1, published as such.
    recs.append({
        "id": "C-A4",
        "label": "Availability disadvantage (official report) vs game margin",
        "x": "avail edge (home)", "y": "Home margin",
        "n": 1,
        "r": None, "ci_low": None, "ci_high": None,
        "method": corr_official.CorrRecord.method,
        "sources": ["S01", "S52"],
        "inputs": "Only one week of official injury captures exists (Week 10) "
                  "and only the TNF game is settled with paired inputs — n=1 "
                  "cannot support a correlation. Published blank with its n, "
                  "as the requirement demands, instead of estimated.",
        "tier": "BLANK",
    })

    # C-A5: points for vs points against, 32 clubs (schedule-strength probe).
    xs = [float(s["pf"]) for s in standings]
    ys = [float(s["pa"]) for s in standings]
    recs.append(corr_official.CorrRecord.build(
        "C-A5", "Points for vs points against (schedule-strength probe)",
        "PF", "PA",
        xs, ys, ["S03"], OFFICIAL,
        "32 official standing rows (S03)").as_row())

    payload = {
        "id": "correlations_official",
        "title": "Correlation register — officially sourced numbers only",
        "updated": "2026-11-14",
        "requirement": "R27",
        "description": (
            "Every value in this register is computed from rows transcribed "
            "from official league sources (S01/S03/S52), and every value "
            "publishes its n alongside it. Correlations computed from "
            "third-party captures are excluded by rule (engine/corr_official.py "
            "refuses non-official source ids) and remain on their own labelled "
            "pages."),
        "excluded_registers": [
            {"path": "data/measured.json",
             "why": "computed from the third-party nflverse games capture (S47)"},
            {"path": "data/prop-correlations-d.csv",
             "why": "computed from a third-party player_stats mirror (S48, flag F17)"},
            {"path": "data/correlations.csv",
             "why": "computed from third-party closing prices; self-labelled unverified"},
        ],
        "method": "Pearson r; Fisher-z 95% CI; n published with every value",
        "rows": recs,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
        fh.write("\n")
    for r in recs:
        print("%s  n=%-4s r=%s" % (r["id"], r["n"], r["r"]))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
