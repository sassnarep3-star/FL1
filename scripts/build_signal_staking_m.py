#!/usr/bin/env python3
"""
build_signal_staking_m.py — session M: separate SIGNAL from STAKING on the
leaderboard so a lucky staking run cannot mask a bad signal.

Two ledgers are computed from the SAME settled bet streams (rebuilt
deterministically from scripts/strategy_lab.py over the pinned snapshot):

  SIGNAL   flat 1-unit stakes: hit rate, Wilson CI, break-even, flat ROI,
           one-sided p-value, the 7 validation gates, verdict. This is the
           only ledger that ranks and rewards.

  STAKING  the S10 policy applied to the same bets: fractional Kelly at 0.25x
           with a 1-unit cap, probability = expanding-window trailing hit rate
           of the same entry (past-only; no stake above 0 until 30 settled).
           Reported as risk telemetry ONLY: profit, ROI, max drawdown.

The published rule: promotion and rewards use the SIGNAL columns exclusively.
The staking ledger can demote a live strategy (risk breach) but can never
promote one. A row is flagged "masked" when staking profit > 0 while the
signal ROI <= 0 — the exact failure mode this split exists to prevent.

Outputs: data/signal_vs_staking.csv

Run:  python3 scripts/build_signal_staking_m.py
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "signal_vs_staking.csv")

STAKE_POLICY = ("fractional Kelly 0.25x, 1-unit cap, p = expanding trailing "
                "hit rate (min 30 settled before stake > 0)")
MIN_HISTORY = 30


def load_lab():
    spec = importlib.util.spec_from_file_location(
        "fl1_strategy_lab", os.path.join(ROOT, "scripts", "strategy_lab.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fl1_strategy_lab"] = mod
    spec.loader.exec_module(mod)
    return mod


def kelly_fraction(p: float, b: float) -> float:
    """Binary Kelly fraction for net odds b>0 and probability p."""
    if b <= 0:
        return 0.0
    return (p * (b + 1.0) - 1.0) / b


def staking_ledger(bets: pd.DataFrame) -> dict:
    bets = bets.sort_values(["season", "week"]).reset_index(drop=True)
    wins = losses = 0
    bank = 0.0
    peak = 0.0
    max_dd = 0.0
    staked_total = 0.0
    n_staked = 0
    for _, r in bets.iterrows():
        if r.push:
            continue
        settled = wins + losses
        p = wins / settled if settled else 0.0
        if settled < MIN_HISTORY:
            stake = 0.0
        else:
            b = (100.0 / -r.odds) if r.odds < 0 else r.odds / 100.0
            f = kelly_fraction(p, b)
            stake = max(0.0, min(0.25 * f, 1.0))
        if r.win:
            wins += 1
            b = (100.0 / -r.odds) if r.odds < 0 else r.odds / 100.0
            bank += stake * b
        else:
            losses += 1
            bank -= stake
        staked_total += stake
        if stake > 0:
            n_staked += 1
        peak = max(peak, bank)
        max_dd = min(max_dd, bank - peak)
    return {
        "staking_settled": wins + losses,
        "staking_wins": wins,
        "staking_staked_units": round(staked_total, 3),
        "staking_bets_staked": n_staked,
        "staking_profit_units": round(bank, 3),
        "staking_roi": round(bank / staked_total, 4) if staked_total else None,
        "staking_max_drawdown_units": round(max_dd, 3),
    }


def main() -> int:
    lab = load_lab()
    g = lab.load_games()
    g = g[g.season >= lab.TRAIN_START].copy()
    g = g.merge(lab.elo_and_form(g), on="game_id", how="left")
    g = lab.attach_availability(g)

    seasons = sorted(g.season.unique())
    split_season = seasons[int(len(seasons) * (1 - lab.OOS_FRACTION))]

    sig = lab.signals(g)
    rows = []
    for name, s in sig.items():
        bets = lab.build_bets(g, s["mask"], s["kind"], s["side"])
        if bets.empty:
            continue
        G, periods = lab.gates(bets, split_season)
        full = periods[0]
        st = staking_ledger(bets)
        rows.append({
            "strategy_id": name,
            "family": s["family"],
            "market": s["kind"],
            "n_settled": full.get("settled"),
            "signal_hit_rate": full.get("hit_rate"),
            "signal_hit_ci_low": full.get("hit_ci_low"),
            "signal_breakeven_hit": full.get("breakeven_hit"),
            "signal_flat_roi": full.get("roi"),
            "signal_max_drawdown_units": full.get("max_drawdown"),
            "signal_p_value": full.get("p_value"),
            "signal_gates_passed": G.get("gates_passed"),
            "signal_verdict": G.get("verdict"),
            "staking_policy": STAKE_POLICY,
            **st,
        })

    df = pd.DataFrame(rows)
    # signal_rank: gates passed (desc), then flat ROI (desc) — staking never enters.
    df = df.sort_values(["signal_gates_passed", "signal_flat_roi"],
                        ascending=[False, False]).reset_index(drop=True)
    df["signal_rank"] = df.index + 1
    df = df.sort_values("staking_profit_units", ascending=False).reset_index(drop=True)
    df["staking_rank"] = df.index + 1
    df["staking_would_mask"] = np.where(
        (df.staking_profit_units > 0) & (df.signal_flat_roi.fillna(-1) <= 0),
        "yes", "no")
    df["promotion_rule"] = "signal columns only"
    df["reward_eligible"] = np.where(df.signal_verdict == "APPROVED", "yes", "no")
    df = df.sort_values("signal_rank").reset_index(drop=True)
    df.to_csv(OUT, index=False)

    masked = df[df.staking_would_mask == "yes"]
    print("wrote data/signal_vs_staking.csv (%d strategies)" % len(df))
    print("signal ranks 1-3:", list(df.head(3).strategy_id))
    print("staking ranks 1-3:",
          list(df.sort_values('staking_rank').head(3).strategy_id))
    print("rows where a positive staking run masks a non-positive signal: %d"
          % len(masked))
    if len(masked):
        print("  masked:", list(masked.strategy_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
