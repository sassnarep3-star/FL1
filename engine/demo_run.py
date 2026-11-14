#!/usr/bin/env python3
"""Run the whole engine over one fixture and emit data/demo_results.json.

WHAT THIS IS. A reproducible exercise of the machinery: the gates, the leaderboard
scoring, the correlation correction, the availability diff and the compliance veto, run
over (a) the one real dataset in the repository -- the captured official NFL injury
report sample -- and (b) *synthetic* bet logs whose hit rates we choose, so the
arithmetic can be checked by hand.

WHAT THIS IS NOT. It is not a backtest, not a result, and not evidence that any
strategy works. The bet logs are constructed, so every ROI figure in the output is a
property of the construction. The point of publishing them is to prove the *evaluator*
behaves correctly -- that it fails a small-sample lucky log, blocks on missing line
data, and refuses a prohibited market -- and a reviewer can re-run it in one command.

    python3 engine/demo_run.py            # regenerate data/demo_results.json
    python3 engine/demo_run.py --check    # exit 1 if the committed file differs
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import compliance, correlation, gates, injuries, leaderboard, pricing, stats  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "demo_results.json")
HURDLE = pricing.break_even_probability(-110)


def _synthetic_log(n: int, hit_percent: int, price: int = -110, seasons=(2022, 2023, 2024, 2025),
                   teams=32, clv: float | None = None, edge: float = 0.03) -> list[dict]:
    """A log with exactly round(n x hit_percent/100) wins, spread evenly across the sequence.

    The win indices are chosen by even spacing rather than `i % 100 < hit_percent`, which
    silently produces a 100% hit rate whenever n is smaller than the win count -- and a demo
    whose numbers are wrong is worse than no demo, because it gets quoted. Deterministic and
    hand-countable: wins = round(n*p), so any reviewer can verify the rate with a calculator.
    """
    target = round(n * hit_percent / 100.0)
    winners = {(i * n) // target for i in range(target)} if target else set()
    bets = []
    for i in range(n):
        won = i in winners
        bets.append({
            "game_id": f"SYN-{i:05d}", "season": seasons[i % len(seasons)],
            "team": f"T{i % teams}", "price": price, "stake": 1.0, "won": won,
            "pnl": (100.0 / abs(price)) if won else -1.0, "clv": clv,
            "modelled_edge": edge, "eval": "oos",
        })
    return bets


def _strategy_grid() -> list[leaderboard.Entry]:
    return [
        leaderboard.Entry(
            entry_id="DEMO-A", author="demo", division="D2 — game total",
            bets=_synthetic_log(180, 57), code_blob="totals_v1", data_blob="snapshot-2026w10",
            model_card={"thesis": "totals mispriced after a public injury downgrade",
                        "market": "game total", "inputs": "official report only",
                        "kill_rule": "G-2b fails for two consecutive reviews"}),
        leaderboard.Entry(
            entry_id="DEMO-B", author="demo", division="D2 — game total",
            bets=_synthetic_log(1400, 54, clv=0.004), code_blob="totals_v2",
            data_blob="snapshot-2026w10",
            model_card={"thesis": "shrinkage priors plus rest asymmetry", "market": "game total",
                        "inputs": "schedule + availability",
                        "kill_rule": "rolling 250-bet CLV lower bound below zero"}),
        leaderboard.Entry(
            entry_id="DEMO-C", author="demo", division="D1 — game spread",
            bets=_synthetic_log(60, 62), code_blob="spread_home_underdog",
            data_blob="snapshot-2026w10",
            model_card={"thesis": "home underdog after a failed cover (SIG-01)",
                        "market": "spread", "inputs": "schedule + prior",
                        "kill_rule": "n/a — pre-registration example"}),
        leaderboard.Entry(
            entry_id="DEMO-D", author="rival", division="D6 — prop combos",
            bets=_synthetic_log(700, 56), code_blob="sgp_qb_wr", data_blob="snapshot-2026w10",
            model_card={"thesis": "QB-and-WR1 props under a backfield absence",
                        "market": "SGP (3 legs max)", "inputs": "availability + joint simulation",
                        "kill_rule": "EV flips sign under +/-0.05 rho perturbation"}),
    ]


def main(write: bool = True) -> dict:
    src = json.load(open(os.path.join(ROOT, "data", "injury_snapshot.json"), encoding="utf-8"))
    rows = injuries.load_rows(src)

    # 1. arithmetic the owner can check with a calculator
    arithmetic = {
        "break_even_minus110": HURDLE,
        "break_even_formula": "risk / (risk + payout) = 110 / 210",
        "two_way_margin_minus110_both_sides": pricing.two_way_margin(-110, -110),
        "kelly_full_at_55pct": pricing.kelly_fraction(0.55, -110),
        "kelly_quarter_at_55pct": pricing.fractional_kelly(0.55, -110, 0.25, cap=1.0),
        "parlay_break_even_2_legs": pricing.break_even_parlay([-110, -110]),
        "parlay_break_even_3_legs": pricing.break_even_parlay([-110, -110, -110]),
        "sample_for_55pct": stats.required_sample(HURDLE, 0.55),
        "sample_for_57pct": stats.required_sample(HURDLE, 0.57),
        "sample_for_60pct": stats.required_sample(HURDLE, 0.60),
    }

    # 2. the detectable-edge curve, which is the real answer to 'be selective'
    curve = gates.detectable_edge_table(HURDLE, [100, 200, 400, 800, 1600, 3200])

    # 3. gate evaluation over each synthetic strategy
    cfg = gates.GateConfig(trials=1)
    gate_tables = {}
    for e in _strategy_grid():
        g_rows, g_sum = gates.evaluate(e.bets, cfg)
        gate_tables[e.entry_id] = {"summary": g_sum,
                                   "gates": [g.as_row() for g in g_rows]}

    # 4. the leaderboard itself
    lb = leaderboard.rank(_strategy_grid(), cfg)

    # 5. correlation, on a real-shaped example rather than an invented coefficient
    dec2 = pricing.parlay_decimal([-110, -110])
    dec3 = pricing.parlay_decimal([-110, -110, -110])
    corr = {
        "two_leg_55_55": {
            "independent": correlation.joint_prob_from_rho(0.55, 0.55, 0.0),
            "rho_0_15": correlation.joint_prob_from_rho(0.55, 0.55, 0.15),
            "rho_0_30": correlation.joint_prob_from_rho(0.55, 0.55, 0.30),
            "combined_decimal": dec2,
            "break_even_joint_prob": 1.0 / dec2,
        },
        "three_leg_sensitivity_at_rho_0_20": correlation.sensitivity_to_rho(
            0.55, 0.55, dec3, rho=0.20, perturbation=0.05),
        "note": ("the rho values above are inputs to demonstrate the estimator's response, "
                 "not measurements of any real market pair; the measured values live in "
                 "data/correlations.json, where every rho cell is blank by design"),
    }

    # 6. the one real dataset: availability mechanics
    diff_demo = {
        "counts": injuries.deficiency_counts(rows),
        "nmu": injuries.nmu_index(rows),
        "scenarios": injuries.scenario_range(rows),
        "certain_to_play_by_omission": sorted(
            {f"{r['club']}::{r['player']}" for r in rows if injuries.certain_to_play(r)}),
        "rows_in_capture": len(rows),
        "capture_is_partial": True,
    }

    # 7. the compliance veto, run over a realistic candidate slate
    slate = [
        {"market": "Patriots -2.5", "family": "game spread"},
        {"market": "Over 43.5", "family": "game total"},
        {"market": "Stevenson to be ruled Out on Sunday", "family": "player prop"},
        {"market": "Most penalties by either team", "family": "team total"},
        {"market": "Will Mahomes start this week?", "family": "special"},
        {"market": "Baringer to miss the game-winning field goal", "family": "special"},
        {"market": "Goff over 279.5 passing yards", "family": "passing yards"},
    ]
    allowed, refused = compliance.filter_offers(slate)
    compliance_demo = {
        "slate_size": len(slate),
        "allowed": [o["market"] for o in allowed],
        "refused": [{"market": o["market"], "classes": o["refusal"]["classes"]} for o in refused],
    }

    return {
        "id": "demo_results",
        "generated_by": "engine/demo_run.py",
        "warning": ("SYNTHETIC STRATEGY LOGS. The bet logs below are constructed to have an exact "
                    "hit rate so the evaluator can be checked by hand. No figure derived from them "
                    "is a backtest result, and none may be quoted as evidence that a strategy works. "
                    "The only real data in this file is the injury-report capture in section 6, "
                    "which is itself explicitly partial."),
        "updated": src.get("updated"),
        "arithmetic": arithmetic,
        "detectable_edge_curve": curve,
        "gate_tables": gate_tables,
        "leaderboard": lb,
        "correlation": corr,
        "availability": diff_demo,
        "compliance": compliance_demo,
        "source_ids": ["SRC-001", "SRC-002", "SRC-014", "SRC-015", "SRC-016", "SRC-019"],
    }


if __name__ == "__main__":
    check = "--check" in sys.argv
    payload = main(write=not check)
    text = json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    if check:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if current != text:
            print("data/demo_results.json is stale: run `python3 engine/demo_run.py`", file=sys.stderr)
            sys.exit(1)
        print("data/demo_results.json is current")
    else:
        with open(OUT, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote data/demo_results.json ({len(text)} bytes)")
