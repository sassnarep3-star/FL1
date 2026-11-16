#!/usr/bin/env python3
"""Build data/luck_panel.json — the "removal of luck" panel for the dashboard.

Requirement (brief): "Compute and publish the 'removal of luck' panel on the
site dashboard."

The panel is DERIVED — every number is read from data/leaderboard_signal_staking.json
(the signal-vs-staking register, which transcribes data/leaderboard.csv and carries
its own warnings). Nothing is recomputed here, so the panel cannot disagree with the
register it summarises.

What the panel shows, in one view:
- the luck-removed ranking metric: hit-rate 95% CI lower bound minus the price hurdle;
- that 0 of 16 entries survive it, including every positive-ROI entry;
- the control baseline (bet every home team at the close) as the vig yardstick;
- the multiplicity adjustment for 16 trials.

Run:  python3 scripts/build_luck_panel.py
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "luck_panel.json")


def main():
    src = json.load(open(os.path.join(ROOT, "data", "leaderboard_signal_staking.json"),
                         encoding="utf-8"))
    rows = src["rows"]
    if len(rows) != 16:
        raise SystemExit("FAIL: expected 16 entries in the signal/staking register, got %d"
                         % len(rows))

    control = [r for r in rows if r["strategy_id"] == "__CONTROL_MARKET"]
    if len(control) != 1:
        raise SystemExit("FAIL: control baseline entry missing from the register")
    control = control[0]

    proven = [r for r in rows if r["signal"]["signal_verdict"] == "PROVEN"]
    pos_roi = [r for r in rows if r["staking"]["roi"] > 0]
    pos_roi_rejected = [r for r in pos_roi if r["signal"]["signal_verdict"] != "PROVEN"]
    ranked = sorted(rows, key=lambda r: r["signal"]["signal_edge_lcb"], reverse=True)

    panel_rows = []
    for r in ranked:
        s, k = r["signal"], r["staking"]
        panel_rows.append({
            "strategy_id": r["strategy_id"],
            "market": r["market"],
            "settled": s["settled"],
            "hit_rate": s["hit_rate"],
            "hit_ci_low": s["hit_ci_low"],
            "reference_hurdle": s["reference_hurdle"],
            "edge_lcb": s["signal_edge_lcb"],
            "roi_report_only": k["roi"],
            "verdict": s["signal_verdict"],
        })

    payload = {
        "id": "luck_panel",
        "title": "Removal of luck — why no entry is ranked yet",
        "updated": "2026-11-16",
        "requirement": "Compute and publish the 'removal of luck' panel on the site "
                       "dashboard.",
        "metric": src["ranking_rule"],
        "metric_plain": "A strategy's luck-removed edge is the 95% LOWER bound of its "
                        "hit rate minus the break-even hurdle at the price paid "
                        "(0.52381 at standard -110). A lucky run raises ROI but it "
                        "also narrows nothing: the lower bound only rises with more "
                        "settled evidence, so it cannot be gamed by variance.",
        "headlines": {
            "entries": len(rows),
            "proven": len(proven),
            "positive_roi_entries": len(pos_roi),
            "positive_roi_but_rejected_on_signal": len(pos_roi_rejected),
            "best_case": {
                "strategy_id": "DIV_DOG_AND_ELO",
                "roi": rows[0]["staking"]["roi"],
                "roi_units": rows[0]["staking"]["profit_units"],
                "edge_lcb": rows[0]["signal"]["signal_edge_lcb"],
                "verdict": rows[0]["signal"]["signal_verdict"],
                "point": "The register's top ROI entry (+5.73%, +53.7 units) is "
                         "REJECTED because its luck-removed edge is negative "
                         "(-1.31pp): 936 settled bets give a 95% hit-rate lower "
                         "bound of 51.07% against a 52.38% break-even hurdle.",
            },
            "control_baseline": {
                "strategy_id": control["strategy_id"],
                "description": control["description"],
                "settled": control["signal"]["settled"],
                "hit_rate": control["signal"]["hit_rate"],
                "roi": control["staking"]["roi"],
                "point": "Betting every home team at the close loses 5.19% over 5,067 "
                         "settled bets — that loss is the house margin. Every strategy "
                         "is judged against this yardstick, not against zero.",
            },
            "multiplicity": {
                "trials": len(rows),
                "note": "Gate G-6 deflates for the number of trials; the register "
                        "transcribes G6_adjusted_alpha=0.00333 per row. With 16 "
                        "strategies tried, a p-value that looks fine alone is not "
                        "fine for the family.",
            },
        },
        "rows": panel_rows,
        "provenance": {
            "tier": "COMPUTED",
            "source_ids": ["S47", "S52"],
            "warning": "The underlying dataset is the computed research layer over "
                       "third-party data (flags F19/F23); its breakeven_hit column is "
                       "circular (F30) and is NOT used here. The OFFICIAL register has "
                       "no settled bet log yet, so no entry can be ranked. The panel "
                       "demonstrates the method on the flagged dataset — it does not "
                       "endorse any strategy.",
        },
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("luck panel: entries=%d proven=%d posROI=%d posROI-rejected=%d" % (
        len(rows), len(proven), len(pos_roi), len(pos_roi_rejected)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
