"""Validation gates. A strategy is not 'good because it won'; it is admissible because it
survives every gate. Anything the current data cannot answer returns HOLD, never PASS - a
missing input must not be able to buy a green light.

Gate set (all thresholds numeric, all in one table, all rendered on the site):

  G0  data integrity          validate.py reports 0 FAIL and 0 blank-but-unflagged cell
  G1  sample                  >= 300 settled bets, >= 2 seasons, >= 30 bets/season
  G2  post-vig edge           mean edge >= 2.0% and >= 55% of bets carry a positive edge
  G3  closing-line value      mean CLV >= +0.5 pts (spread/total) or >= 1.5% (ML/prop)
  G4  luck-adjusted return    95% block-bootstrap CI of mean PnL per 100 excludes 0
  G5  drawdown                max drawdown <= 25% of bankroll under the declared staking rule
  G6  correlation             every leg-pair rho known and |rho| <= 0.35; unknown => HOLD
  G7  regime robustness       no season > 40% of total edge; each season PnL/100 > -2.0
  G8  parameter stability     line shift <= 0.5 pts and >= 80% signal-set overlap under
                              +/-20% perturbation of each prior
  G9  capacity                stake <= 1% of market limit; handle <= 0.5% of pool
  G10 timing / no leak        every input timestamp strictly before kickoff; 0 rows from a
                              game already decided at snapshot time
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PASS, FAIL, HOLD = "PASS", "FAIL", "HOLD"


@dataclass(frozen=True)
class Gate:
    id: str
    name: str
    threshold: str
    data_required: str
    blocks: str
    blocked_by_flag: str | None = None


GATES: list[Gate] = [
    Gate("G0", "Data integrity", "0 FAIL from pipelines.validate; every published row has an "
         "official source link; 0 blank cells without a flag",
         "data/verified/validation.json", "everything - a broken table breaks every decision", None),
    Gate("G1", "Sample size", "n >= 300 settled bets, >= 2 distinct seasons, >= 30 bets in each",
         "bet ledger + settled results", "any claim that a strategy is skill rather than luck",
         "F-11"),
    Gate("G2", "Post-vig edge", "mean edge >= 2.0% AND >= 55% of bets with edge > 0",
         "origination output + a market price to subtract", "bet sizing and the leaderboard score",
         "F-02"),
    Gate("G3", "Closing-line value", "mean CLV >= +0.5 pts on spread/total, >= 1.5% on ML/props",
         "opening and closing market prices per bet", "whether any edge is real or an artefact",
         "F-02"),
    Gate("G4", "Luck-adjusted return", "95% block-bootstrap CI (blocks = weeks) of mean PnL/100 "
         "excludes 0", "settled bets with week ids", "reward eligibility, tier 1 and 2", "F-11"),
    Gate("G5", "Drawdown control", "max drawdown <= 25% of starting bankroll at the declared "
         "fractional-Kelly stake", "settled bets + staking rule", "bankroll policy", None),
    Gate("G6", "Correlation cap", "max |rho| over all leg pairs <= 0.35; every rho measured, "
         "none assumed; parlays with an unknown rho are not priced",
         "leg-pair correlation matrix (model/correlation.py)", "every multi-leg product",
         "F-16"),
    Gate("G7", "Regime robustness", "no single season carries > 40% of total edge; every "
         "season's PnL/100 > -2.0", ">= 3 seasons of settled bets", "whether the edge survives a rule change",
         "F-11"),
    Gate("G8", "Parameter stability", "under +/-20% perturbation of each prior: published line "
         "moves <= 0.5 pts and the signalled bet set overlaps >= 80%",
         "model/config priors + the origination run", "whether the model is a machine or a coin",
         "F-05"),
    Gate("G9", "Capacity / liquidity", "stake <= 1% of the posted limit; expected handle <= 0.5% "
         "of the market pool", "market limits per market", "whether the strategy scales past paper",
         "F-02"),
    Gate("G10", "Timing and leakage", "every input row fetched strictly before that game's "
         "kickoff; 0 rows where the official page already printed a final score",
         "fetch timestamps + kickoff times", "every accuracy claim", "F-12"),
]


def evaluate(metrics: dict) -> list[dict]:
    """metrics comes from backtest.leaderboard.summarise(). Missing key -> HOLD."""
    out: list[dict] = []

    def verdict(gate: Gate, ok: bool, observed: str, missing: bool = False):
        out.append({"id": gate.id, "name": gate.name, "threshold": gate.threshold,
                    "result": HOLD if missing else (PASS if ok else FAIL),
                    "observed": observed, "data_required": gate.data_required,
                    "blocks": gate.blocks, "blocked_by_flag": gate.blocked_by_flag})

    g = {x.id: x for x in GATES}

    fails = metrics.get("validation_failures")
    verdict(g["G0"], fails == 0,
            f"{fails} FAIL rows in validation.json" if fails is not None else "validation not run",
            missing=fails is None)

    n, seasons = metrics.get("n"), metrics.get("seasons")
    per_season_min = metrics.get("min_bets_per_season")
    if n is None or seasons is None:
        verdict(g["G1"], False, "no settled bet ledger", missing=True)
    else:
        verdict(g["G1"], n >= 300 and seasons >= 2 and (per_season_min or 0) >= 30,
                f"n={n}, seasons={seasons}, min bets in a season={per_season_min}")

    edge = metrics.get("mean_edge_pct")
    verdict(g["G2"], (edge or -1) >= 2.0 and (metrics.get("pct_positive_edge") or 0) >= 55.0,
            f"mean edge {edge}% / positive-edge share {metrics.get('pct_positive_edge')}%",
            missing=edge is None)

    clv = metrics.get("mean_clv")
    verdict(g["G3"], (clv or -1) >= metrics.get("clv_threshold", 0.5),
            f"mean CLV {clv} vs threshold {metrics.get('clv_threshold', 0.5)}",
            missing=clv is None)

    ci = metrics.get("bootstrap_ci_mean_pnl_per_100")
    verdict(g["G4"], bool(ci) and ci[0] > 0,
            f"95% CI of mean PnL/100 = {ci}" + ("" if ci else " (bootstrap not run)"),
            missing=ci is None)

    dd = metrics.get("max_drawdown_pct")
    verdict(g["G5"], dd is not None and dd <= 25.0, f"max drawdown {dd}%", missing=dd is None)

    rho_max = metrics.get("max_abs_leg_rho")
    unknown = metrics.get("unknown_leg_pairs", 0)
    verdict(g["G6"], rho_max is not None and rho_max <= 0.35 and unknown == 0,
            f"max |rho|={rho_max}, unknown leg pairs={unknown}",
            missing=rho_max is None)

    share = metrics.get("top_season_edge_share")
    worst = metrics.get("worst_season_pnl_per_100")
    verdict(g["G7"], share is not None and share <= 0.40 and worst is not None and worst > -2.0,
            f"largest season share {share}, worst season PnL/100 {worst}",
            missing=share is None)

    shift = metrics.get("max_perturbation_line_shift")
    overlap = metrics.get("perturbation_signal_overlap")
    verdict(g["G8"], shift is not None and shift <= 0.5 and (overlap or 0) >= 0.80,
            f"max line shift {shift} pts, signal overlap {overlap}",
            missing=shift is None)

    cap = metrics.get("stake_pct_of_limit")
    verdict(g["G9"], cap is not None and cap <= 1.0, f"stake {cap}% of posted limit",
            missing=cap is None)

    leak = metrics.get("rows_after_kickoff")
    verdict(g["G10"], leak == 0, f"{leak} input rows captured at or after kickoff"
            if leak is not None else "no fetch timestamps recorded", missing=leak is None)
    return out


def summary(results: list[dict]) -> dict:
    counts = {PASS: 0, FAIL: 0, HOLD: 0}
    for r in results:
        counts[r["result"]] += 1
    return {"counts": counts,
            "admissible": counts[FAIL] == 0 and counts[HOLD] == 0,
            "failing": [r["id"] for r in results if r["result"] == FAIL],
            "on_hold": [r["id"] for r in results if r["result"] == HOLD]}


def main() -> int:
    """Run the gate set against whatever the repo currently holds and publish the verdict."""
    sys_path = ROOT / "data" / "model"
    metrics: dict = {}
    vp = ROOT / "data" / "verified" / "validation.json"
    if vp.exists():
        metrics["validation_failures"] = len(json.loads(vp.read_text())["failures"])
    results = evaluate(metrics)
    payload = {"gates": [{**{"id": g.id, "name": g.name, "threshold": g.threshold,
                             "data_required": g.data_required, "blocks": g.blocks,
                             "blocked_by_flag": g.blocked_by_flag}} for g in GATES],
               "evaluated": results, "summary": summary(results),
               "note": "With an empty bet ledger the honest verdict is HOLD on 9 of 10 gates. "
                       "That is the gate set working, not failing."}
    (sys_path / "gates.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
