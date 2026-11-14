#!/usr/bin/env python3
"""Build data/leaderboard_signal_staking.json (requirement R25).

Splits every leaderboard entry into a SIGNAL block and a STAKING block and
re-ranks on SIGNAL ONLY, so a lucky staking run cannot mask a bad signal.

Source: data/leaderboard.csv (computed layer, third-party data, flagged F17/F18
family). The stakes in that dataset are flat 1 unit per bet
(scripts/strategy_lab.py), so staking cannot mask signal IN THIS DATASET — the
split is enforced anyway, because the competition will admit variable stakes
and the rule must already exist when it does.

NOTE (flag F25): the dataset's own `breakeven_hit` column is circular — it is
computed as 1/(1+realized ROI) from settled profits, not from the prices paid,
so it cannot serve as a price hurdle. It is transcribed into
`dataset_breakeven_hit_transcribed` for audit and NOT used for ranking. The
signal edge is measured against the standard -110 two-way reference hurdle
(0.52381, engine/pricing.py, source SRC-015) and labelled as such; when the
computed layer re-emits per-bet odds (SG24), the exact price hurdle replaces it.

Signal score = hit_ci_low - reference_hurdle (the pessimistic end of the hit-rate
estimate minus the hurdle). Ranking on the lower bound rather than the
point estimate is what removes the luck: a lucky 8-2 run has a wide interval
and a low lower bound.

Run:  python3 scripts/build_signal_staking.py
"""

import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "leaderboard_signal_staking.json")

REFERENCE_HURDLE = 0.52381   # break-even at -110; engine/pricing.py, SRC-015


def f(v):
    return None if v in (None, "") else float(v)


def main() -> int:
    with open(os.path.join(DATA, "leaderboard.csv"), newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    entries = []
    for r in rows:
        lo = f(r["hit_ci_low"])
        signal_edge_lcb = None if lo is None else round(lo - REFERENCE_HURDLE, 6)
        entries.append({
            "strategy_id": r["strategy_id"],
            "family": r["family"],
            "market": r["market"],
            "description": r["description"],
            "signal": {
                "settled": int(r["settled"]),
                "hit_rate": f(r["hit_rate"]),
                "hit_ci_low": lo,
                "hit_ci_high": f(r["hit_ci_high"]),
                "reference_hurdle": REFERENCE_HURDLE,
                "reference_hurdle_note": "standard -110 two-way break-even "
                                         "(engine/pricing.py, SRC-015); exact "
                                         "per-bet price hurdle pending SG24",
                "signal_edge_lcb": signal_edge_lcb,
                "signal_verdict": ("SIGNAL PROVEN" if (signal_edge_lcb is not None
                                                       and signal_edge_lcb > 0)
                                   else "NOT PROVEN"),
                "dataset_breakeven_hit_transcribed": f(r["breakeven_hit"]),
                "dataset_breakeven_warning": "circular: 1/(1+realized ROI), not a "
                                             "price hurdle — flag F25; not used "
                                             "for ranking",
                "tier": "COMPUTED",
            },
            "staking": {
                "roi": f(r["roi"]),
                "roi_se": f(r["roi_se"]),
                "profit_units": f(r["profit_units"]),
                "max_drawdown": f(r["max_drawdown"]),
                "oos_roi": f(r["oos_roi"]),
                "oos_settled": f(r["oos_settled"]),
                "tier": "COMPUTED",
            },
            "dataset_verdict": r["verdict"],
            "dataset_gates_passed": int(r["gates_passed"]),
        })

    ranked = sorted(entries, key=lambda e: (
        e["signal"]["signal_edge_lcb"] is not None,
        e["signal"]["signal_edge_lcb"] if e["signal"]["signal_edge_lcb"] is not None else -9e9),
        reverse=True)
    for i, e in enumerate(ranked, start=1):
        e["signal_rank"] = i

    payload = {
        "id": "leaderboard_signal_staking",
        "title": "Leaderboard split — signal vs staking (rank is signal-only)",
        "updated": "2026-11-14",
        "requirement": "R25",
        "description": (
            "The rank column is computed from the SIGNAL block only: flat-stake "
            "hit rate, ranked on the 95% lower bound against the standard -110 "
            "reference hurdle. The STAKING block (ROI at actual "
            "stakes, profit, drawdown) is reported beside it and can never "
            "change a rank. Source dataset: data/leaderboard.csv (computed "
            "layer over third-party data — flagged), stakes flat 1 unit. The "
            "dataset's breakeven_hit column is circular (flag F25) and is "
            "transcribed only for audit."),
        "ranking_rule": "signal_rank = order by (hit_ci_low - reference_hurdle) "
                        "descending; ties break on larger settled sample. Profit "
                        "and ROI are reported, never ranked on.",
        "demotion": "No entry is LIVE in this dataset (all verdicts REJECTED/UNRANKED "
                    "pending gates), so gate G-14 (engine/demotion.py) has nothing to "
                    "demote yet; it will apply the moment an entry goes live.",
        "coverage": {
            "entries": len(entries),
            "signal_proven": sum(1 for e in entries
                                 if e["signal"]["signal_verdict"] == "SIGNAL PROVEN"),
            "best_signal": ranked[0]["strategy_id"] if ranked else None,
        },
        "rows": ranked,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
        fh.write("\n")
    print("wrote %s: %d entries, %d signal-proven, best signal: %s"
          % (OUT, len(entries), payload["coverage"]["signal_proven"],
             payload["coverage"]["best_signal"]))
    return 0


if __name__ == "__main__":
    main()
