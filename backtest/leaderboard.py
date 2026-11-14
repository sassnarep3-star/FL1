"""Skill-based strategy leaderboard: scored on closeness, not on luck.

Why CLV-anchored and not PnL-anchored: over a football-sized sample, realised PnL is dominated
by variance — a zero-edge strategy can finish a season up 8 units. Closing line value is the
least-noisy available proxy for "the model knew something the market did not yet know", so the
score is weighted toward CLV and toward the *lower bound* of a bootstrapped CI rather than the
point estimate. Luck is made explicit as `realised - expected_from_close` and reported, not
hidden.

Run:  python3 -m backtest.leaderboard
"""

from __future__ import annotations

import csv
import io
import json
import math
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "backtest" / "fixtures" / "bets_synthetic.psv"
OUT = ROOT / "data" / "model" / "leaderboard.json"

BANKROLL = 100.0  # units at the start of each season for the drawdown rule

WEIGHTS = {
    "mean_clv_pct": 0.30,
    "ci_low_per_100_staked": 0.25,
    "ev_per_100_staked_from_close": 0.20,
    "neg_max_drawdown_pct": 0.10,
    "neg_brier": 0.15,
}

REWARD_TIERS = [
    {"tier": 1, "name": "Fundable", "requires": "all 10 gates PASS",
     "reward": "bankroll allocation, up to 2.0% of roll per bet, monthly operating budget, "
               "and first claim on paid data sources"},
    {"tier": 2, "name": "Contender", "requires": "G0,G2,G3,G4,G5,G8 PASS; G1,G7,G9 may HOLD",
     "reward": "paper-money allocation at 0.5% of roll, shared GPU/backtest queue priority, "
               "and a named slot in the weekly review"},
    {"tier": 3, "name": "Watchlist", "requires": "G0 PASS and mean CLV > 0",
     "reward": "tracked on the board, no allocation; gets a data-request slot"},
    {"tier": 4, "name": "Bench", "requires": "anything else",
     "reward": "no allocation; must re-derive the thesis before re-entering"},
]


def load(path: Path = FIXTURE) -> list[dict]:
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines()
             if not ln.startswith("#") and ln.strip()]
    rows = list(csv.DictReader(io.StringIO("\n".join(lines)), delimiter="|"))
    for r in rows:
        for k in ("p_model", "p_bet_novig", "p_close_novig", "stake_units", "payout_units",
                  "leg_rho"):
            r[k] = float(r[k]) if r[k] not in ("", None) else None
        for k in ("season", "week", "legs", "limit_usd", "fetched_before_kickoff"):
            r[k] = int(float(r[k]))
        raw_result = r["result"].strip()
        r["result"] = 1 if raw_result == "1" else (0 if raw_result == "0" else "push")
        r["line_bet"] = float(r["line_bet"]) if r["line_bet"] else None
        r["line_close"] = float(r["line_close"]) if r["line_close"] else None
    return rows


def _block_bootstrap_ci(payouts: list[float], weeks: list[int], reps: int = 2000,
                        seed: int = 7) -> list[float]:
    """Mean per-100 with a moving block over weeks: bets inside one week share a slate, so an
    iid bootstrap would understate the interval and hand out false confidence."""
    rng = random.Random(seed)
    by_week: dict[int, list[float]] = defaultdict(list)
    for p, w in zip(payouts, weeks):
        by_week[w].append(p)
    keys = sorted(by_week)
    n_blocks = max(2, len(keys) // 3)
    means = []
    for _ in range(reps):
        sample = []
        for _ in range(n_blocks):
            start = rng.randrange(len(keys))
            for k in keys[start:start + 3]:
                sample.extend(by_week[k])
        if sample:
            means.append(sum(sample) / len(sample) * 100.0)
    means.sort()
    if not means:
        return [0.0, 0.0]
    return [round(means[int(0.025 * (len(means) - 1))], 3),
            round(means[int(0.975 * (len(means) - 1))], 3)]


def summarise(rows: list[dict]) -> dict:
    n = len(rows)
    staked = sum(r["stake_units"] for r in rows)
    realised = sum(r["payout_units"] for r in rows)
    ev_close = 0.0
    clv_pts, clv_pct, briers = [], [], []
    for r in rows:
        dec = 1.0 / r["p_close_novig"]
        p = r["p_close_novig"]
        ev_close += r["stake_units"] * ((dec - 1.0) * p - (1.0 - p))
        briers.append((r["p_model"] - (1 if r["result"] == 1 else 0)) ** 2)
        if r["p_bet_novig"] and r["p_close_novig"]:
            clv_pct.append((r["p_bet_novig"] - r["p_close_novig"]) / r["p_close_novig"] * 100.0)
        if r["line_bet"] is not None and r["line_close"] is not None:
            clv_pts.append(r["line_bet"] - r["line_close"])

    by_season = defaultdict(list)
    for r in rows:
        by_season[r["season"]].append(r["payout_units"])
    season_pnl = {s: sum(v) for s, v in by_season.items()}
    per100 = {s: sum(v) / len(v) * 100.0 for s, v in by_season.items()}
    total_edge = sum(abs(v) for v in season_pnl.values()) or 1.0
    top_share = max(abs(v) for v in season_pnl.values()) / total_edge

    roi_per_bet = [r["payout_units"] / r["stake_units"] for r in rows if r["stake_units"]]
    cum, peak, max_dd = 0.0, BANKROLL, 0.0
    for r in rows:
        cum += r["payout_units"]
        peak = max(peak, BANKROLL + cum)
        max_dd = max(max_dd, (peak - (BANKROLL + cum)) / peak * 100.0)

    rho_vals = [abs(r["leg_rho"]) for r in rows if r["leg_rho"] is not None]
    unknown_leg_pairs = sum(1 for r in rows if r["leg_rho"] is None and r["legs"] > 1)
    limits = [r["limit_usd"] for r in rows] or [1]
    stake_usd_assumed = 100.0
    # Normalise by stake before bootstrapping: a per-bet PnL metric lets a small-staking
    # strategy beat a sharper one purely by having a tighter interval. Per unit staked, the
    # comparison is between edges, not between bet sizes.
    ci = _block_bootstrap_ci(roi_per_bet, [r["week"] for r in rows])

    return {
        "n": n,
        "seasons": len(by_season),
        "min_bets_per_season": min((len(v) for v in by_season.values()), default=0),
        "win_rate": round(sum(1 for r in rows if r["result"] == 1) / n, 4),
        "units_staked": round(staked, 3),
        "units_realised": round(realised, 3),
        "roi_pct": round(realised / staked * 100.0, 3) if staked else 0.0,
        "pnl_per_100": round(realised / n * 100.0, 3),
        "pnl_per_100_staked": round(sum(roi_per_bet) / len(roi_per_bet) * 100.0, 3),
        "ev_per_100_staked_from_close": round(ev_close / staked * 100.0, 3) if staked else 0.0,
        "luck_units": round(realised - ev_close, 3),
        "bootstrap_ci_mean_pnl_per_100": ci,
        "ci_low_per_100_staked": ci[0],
        "ci_high_per_100_staked": ci[1],
        "ci_low_pnl_per_100": ci[0],
        "ci_high_pnl_per_100": ci[1],
        "mean_clv_points": round(sum(clv_pts) / len(clv_pts), 4) if clv_pts else None,
        "mean_clv_pct": round(sum(clv_pct) / len(clv_pct), 4) if clv_pct else None,
        "pct_clv_positive": round(100.0 * sum(1 for c in clv_pct if c > 0) / len(clv_pct), 2) if clv_pct else None,
        "brier": round(sum(briers) / len(briers), 5),
        "max_drawdown_pct": round(max_dd, 3),
        "season_pnl": {str(k): round(v, 3) for k, v in season_pnl.items()},
        "season_pnl_per_100": {str(k): round(v, 3) for k, v in per100.items()},
        "top_season_edge_share": round(top_share, 4),
        "worst_season_pnl_per_100": round(min(per100.values()), 3),
        "max_abs_leg_rho": round(max(rho_vals), 4) if rho_vals else None,
        "unknown_leg_pairs": unknown_leg_pairs,
        "stake_pct_of_limit": round(stake_usd_assumed / min(limits) * 100.0, 3),
        "rows_after_kickoff": sum(1 for r in rows if r["fetched_before_kickoff"] != 1),
        "mean_edge_pct": round(sum((r["p_model"] - r["p_close_novig"]) for r in rows) / n * 100.0, 3),
        "pct_positive_edge": round(100.0 * sum(1 for r in rows
                                                if r["p_model"] > r["p_close_novig"]) / n, 2),
    }


def _z(vals: list[float]) -> list[float]:
    n = len(vals)
    if n < 2:
        return [0.0] * n
    mu = sum(vals) / n
    sd = math.sqrt(sum((v - mu) ** 2 for v in vals) / (n - 1)) or 1e-9
    return [(v - mu) / sd for v in vals]


def rank(entries: list[dict]) -> list[dict]:
    comps = ["mean_clv_pct", "ci_low_per_100_staked", "ev_per_100_staked_from_close",
             "neg_max_drawdown_pct", "neg_brier"]
    for e in entries:
        m = e["metrics"]
        e["_raw"] = {
            "mean_clv_pct": m.get("mean_clv_pct") or 0.0,
            "ci_low_per_100_staked": m.get("ci_low_per_100_staked") or 0.0,
            "ev_per_100_staked_from_close": m.get("ev_per_100_staked_from_close") or 0.0,
            "neg_max_drawdown_pct": -(m.get("max_drawdown_pct") or 0.0),
            "neg_brier": -(m.get("brier") or 0.0),
        }
    for c in comps:
        zs = _z([e["_raw"][c] for e in entries])
        for e, z in zip(entries, zs):
            e["_raw"][c] = z
    for e in entries:
        e["score"] = round(sum(WEIGHTS[c] * e["_raw"][c] for c in comps), 4)
    entries.sort(key=lambda e: -e["score"])
    for i, e in enumerate(entries, 1):
        e["rank"] = i
    return entries


TIER2_ALLOWED_HOLD = {"G1", "G6", "G7", "G9", "G10"}
TIER2_MUST_PASS = {"G0", "G2", "G3", "G4", "G5", "G8"}


def tier_for(gate_summary: dict) -> dict:
    """Tier is a function of gate results only - realised PnL can never buy a tier."""
    failing, on_hold = set(gate_summary["failing"]), set(gate_summary["on_hold"])
    if not failing and not on_hold:
        tier = 1
    elif not (failing & TIER2_MUST_PASS) and on_hold <= TIER2_ALLOWED_HOLD:
        tier = 2
    elif "G0" not in failing and gate_summary.get("mean_clv_positive"):
        tier = 3
    else:
        tier = 4
    return next(t for t in REWARD_TIERS if t["tier"] == tier)


def main() -> int:
    from model.gates import evaluate, summary as gate_summary_fn

    rows = load()
    by_strategy: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_strategy[r["strategy"]].append(r)

    vp = ROOT / "data" / "verified" / "validation.json"
    vfails = len(json.loads(vp.read_text())["failures"]) if vp.exists() else None

    entries = []
    for name, rs in by_strategy.items():
        m = summarise(rs)
        m["validation_failures"] = vfails
        m["clv_threshold"] = 1.5 if rs[0]["market"] in ("player-prop-parlay", "moneyline") else 0.5
        stab = ROOT / "data" / "model" / "stability.json"
        if stab.exists():
            sweeps = json.loads(stab.read_text())["sweeps"]
            m["max_perturbation_line_shift"] = max(s["max_spread_shift_pts"] for s in sweeps)
            m["perturbation_signal_overlap"] = min(s["signal_set_overlap"] for s in sweeps)
        gates = evaluate(m)
        gs = gate_summary_fn(gates)
        gs["passing"] = [x["id"] for x in gates if x["result"] == "PASS"]
        gs["mean_clv_positive"] = (m["mean_clv_pct"] or 0) > 0
        entries.append({"strategy": name, "market": rs[0]["market"], "metrics": m,
                        "gates": gates, "gate_summary": {k: v for k, v in gs.items() if k != "passing"},
                        "tier": tier_for(gs)})
    entries = rank(entries)
    for e in entries:
        e.pop("_raw", None)

    payload = {
        "dataset": "Strategy leaderboard",
        "ledger": "backtest/fixtures/bets_synthetic.psv",
        "ledger_kind": "SYNTHETIC FIXTURE - generated by backtest.fixtures.generate (seed 1220). "
                       "No row is a real wager and no number here is evidence about the real world.",
        "scoring_weights": WEIGHTS,
        "reward_tiers": REWARD_TIERS,
        "strategies": entries,
        "reading": "score is a z-score composite, so it ranks rows against each other only; it "
                   "is not an expected return. luck_units is realised minus what the closing "
                   "probabilities already implied.",
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {OUT.relative_to(ROOT)}")
    for e in entries:
        print(f"   #{e['rank']} {e['strategy']:<24} score {e['score']:+.3f} "
              f"n={e['metrics']['n']:>4} PnL/100-staked {e['metrics']['pnl_per_100_staked']:+7.2f} "
              f"CLV% {e['metrics']['mean_clv_pct']:+.3f} "
              f"luck {e['metrics']['luck_units']:+6.2f} tier {e['tier']['tier']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
