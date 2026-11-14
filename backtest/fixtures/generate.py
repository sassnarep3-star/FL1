"""Generate the SYNTHETIC fixture bet ledger the leaderboard code is tested against.

Run:  python3 -m backtest.fixtures.generate

Nothing in backtest/fixtures/ is real betting activity. Its only job is to prove the scoring
math, the bootstrap, the drawdown rule and the gate runner behave correctly on a ledger whose
truth is known by construction - so that when real bets are recorded, the same code is already
audited. The fixture encodes four strategies: two with a genuine built-in edge, one noisy
zero-edge control, and one multi-leg SGP whose leg correlation is deliberately left unknown so
gate G6 has something to refuse.
"""

from __future__ import annotations

import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "bets_synthetic.psv"

HEADER = ("bet_id|strategy|season|week|game|market|legs|p_model|p_bet_novig|p_close_novig|"
          "line_bet|line_close|leg_rho|stake_units|payout_units|result|limit_usd|"
          "fetched_before_kickoff")

STRATEGIES = {
    "S-A spread-value": {"edge": 0.045, "n_per_season": 120, "rho": 0.0, "legs": 1, "kelly": 0.5},
    "S-B total-value": {"edge": 0.020, "n_per_season": 90, "rho": 0.0, "legs": 1, "kelly": 0.5},
    "S-C coinflip-control": {"edge": 0.0, "n_per_season": 150, "rho": 0.0, "legs": 1, "kelly": 0.5},
    "S-D sgp-props": {"edge": 0.030, "n_per_season": 60, "rho": None, "legs": 3, "kelly": 0.25},
}
MARKETS = {"S-A spread-value": "spread", "S-B total-value": "total",
           "S-C coinflip-control": "spread", "S-D sgp-props": "player-prop-parlay"}


def main() -> None:
    rng = random.Random(1220)
    rows: list[str] = []
    bid = 0
    for name, cfg in STRATEGIES.items():
        for season in (2024, 2025, 2026):
            for _ in range(cfg["n_per_season"]):
                bid += 1
                week = rng.randint(1, 18)
                p_true = rng.uniform(0.40, 0.60)
                p_close = min(0.95, max(0.05, p_true + rng.gauss(0, 0.012)))
                p_model = min(0.97, max(0.03, p_true + cfg["edge"] + rng.gauss(0, 0.02)))
                p_bet = min(0.97, max(0.03, p_model))
                dec = 1.0 / p_close + rng.uniform(0.0, 0.03)
                outcome = 1 if rng.random() < p_true + cfg["edge"] * 0.85 else 0
                kelly = max(0.02, min(0.12, cfg["kelly"] * (p_model - (1 - p_model) / (dec - 1))))
                stake = round(kelly * 100 / 100, 4)
                payout = round(stake * (dec - 1), 4) if outcome else round(-stake, 4)
                if rng.random() < 0.02:
                    payout, outcome = 0.0, "push"
                line_bet = round(rng.choice([-7.0, -3.5, -3.0, 3.5, 6.5, 10.0]), 1)
                line_close = round(line_bet - rng.choice([-0.5, 0.0, 0.0, 0.5]), 1)
                rows.append("|".join(str(x) for x in [
                    f"B{bid:05d}", name, season, week, f"g{season}w{week:02d}_{rng.randint(1, 16)}",
                    MARKETS[name], cfg["legs"], f"{p_model:.4f}", f"{p_bet:.4f}", f"{p_close:.4f}",
                    line_bet, line_close,
                    "" if cfg["rho"] is None else cfg["rho"],
                    stake, payout, outcome, rng.choice([2000, 5000, 10000, 25000]), 1]))
    OUT.write_text(
        "# SYNTHETIC FIXTURE - generated, not observed. No real wager is represented by any row.\n"
        "# Regenerate with: python3 -m backtest.fixtures.generate  (seed 1220, fully deterministic)\n"
        + HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"  wrote {OUT.relative_to(OUT.parents[2])}: {len(rows)} synthetic bets")


if __name__ == "__main__":
    main()
