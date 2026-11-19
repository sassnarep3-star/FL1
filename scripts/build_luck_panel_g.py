#!/usr/bin/env python3
"""Build data/luck_panel.json - the "removal of luck" panel (brief: G4).

Reads the signal-vs-staking register (R25) and the computed layer's control rows,
computes the luck decomposition with engine/luck.py + engine/stats.py, and writes
the panel dataset. Deterministic: no sampling involved, so re-runs are byte-stable.

Inputs (all committed, provenance stated in the output):
  data/leaderboard_signal_staking.json  - signal blocks (from data/leaderboard.csv)
  data/leaderboard.csv                  - control rows (__CONTROL_*)
Output:
  data/luck_panel.json
"""
from __future__ import annotations

import csv
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.luck_signals import build_panel  # noqa: E402


def main() -> None:
    sig_doc = json.load(open(ROOT / "data" / "leaderboard_signal_staking.json"))
    # K1 (arena/9fccbb0e-fl1): controls are yardsticks, not trials. The family-wise bar is
    # computed over the strategies only (N_TRIALS_CONSIDERED = 15 in scripts/strategy_lab.py);
    # the three control rows are carried separately in the panel's "controls" list.
    signal_rows = [r for r in sig_doc["rows"] if not r["strategy_id"].startswith("__CONTROL")]
    trials = len(signal_rows)
    if trials != 15:
        raise SystemExit("FAIL: expected 15 strategy trials, got %d" % trials)

    controls = []
    with open(ROOT / "data" / "leaderboard.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("strategy_id", "").startswith("__CONTROL"):
                controls.append({
                    "strategy_id": r["strategy_id"],
                    "description": r.get("description", ""),
                    "market": r.get("market", ""),
                    "settled": int(r["settled"]) if r.get("settled") else None,
                    "hit_rate": float(r["hit_rate"]) if r.get("hit_rate") else None,
                    "hit_ci_low": float(r["hit_ci_low"]) if r.get("hit_ci_low") else None,
                    "roi": float(r["roi"]) if r.get("roi") else None,
                    "p_value": float(r["p_value"]) if r.get("p_value") else None,
                    "note": ("The control is not a strategy: it measures what the vig costs a "
                             "no-information bettor. Its ROI is the house margin, its p-value is "
                             "the probability a zero-edge process runs at least this well - a "
                             "calibration anchor for the panel, not an entrant."),
                    "provenance": "computed research layer ledger (third-party data, flagged F39/F34)",
                })

    if trials == 0:
        raise SystemExit("no signal rows found - nothing to compute")

    panel = build_panel(signal_rows, trials=trials, controls=controls)
    out = ROOT / "data" / "luck_panel_signals.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(panel, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s: %d strategy rows, %d control(s), verdict=%s"
          % (out.name, len(panel["rows"]), len(controls),
             panel["familywise"]["verdict"]))


if __name__ == "__main__":
    main()
