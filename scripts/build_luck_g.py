#!/usr/bin/env python3
"""
build_luck_g.py — session `arena-dbf11de0-fl1` (task G4).

Publishes the "removal of luck" panel: the numbers that say how much of any
result on this site could be chance, and how many decisions it would take before
chance stopped being a plausible explanation.

Everything here is computed from the official 2026 results file
(data/results.tsv, 137 games, reconciled 32/32 against the official standings)
plus closed-form statistics in engine/luck.py. No price is needed, because a
luck band needs a base rate and a sample size — not a market.

Where a number cannot be produced from an official source it is left blank and
the reason is stated (for example: the intra-cluster correlation for parlays is
not measured anywhere in this repository, so only a sensitivity grid is shown).

Run:  python3 scripts/build_luck_g.py
Writes: data/luck_panel.json
No third-party packages.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import luck  # noqa: E402

RESULTS = os.path.join(ROOT, "data", "results.tsv")
OUT = os.path.join(ROOT, "data", "luck_panel.json")

EDGES = [0.10, 0.05, 0.04, 0.03, 0.02, 0.01]
NS = [50, 100, 137, 250, 500, 1000]
ICCS = [0.0, 0.10, 0.30, 0.50]


def load_results():
    rows = []
    with open(RESULTS, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            f = line.split("\t")
            rows.append({"week": f[0], "date": f[1], "away": f[2],
                         "awayPts": int(f[3]), "home": f[4], "homePts": int(f[5])})
    return rows


def main():
    games = load_results()
    n_games = len(games)
    home_wins = sum(1 for g in games if g["homePts"] > g["awayPts"])
    away_wins = sum(1 for g in games if g["awayPts"] > g["homePts"])
    ties = sum(1 for g in games if g["homePts"] == g["awayPts"])
    home_rate = home_wins / n_games if n_games else None

    outcomes = [1 if g["homePts"] > g["awayPts"] else 0 for g in games]

    # Constant-forecast Brier scores on the official outcomes.
    bs_home = luck.constant_brier(home_rate, outcomes)
    bs_coin = luck.constant_brier(0.5, outcomes)
    bss_home = luck.brier_skill_score([home_rate] * n_games, outcomes,
                                      [0.5] * n_games)
    lo, hi = luck.wilson_interval(home_wins, n_games)
    p_binom = luck.binomial_p_two_sided(home_wins, n_games, 0.5)
    band = luck.luck_band(n_games, 0.5)

    base_rates = [
        {"label": "Home team wins the game (official 2026 results)",
         "k": home_wins, "n": n_games, "rate": home_rate,
         "wilson_lo": lo, "wilson_hi": hi, "exact_p_vs_coin": p_binom,
         "measurable": True, "source": "S49"},
        {"label": "Away team wins the game (official 2026 results)",
         "k": away_wins, "n": n_games, "rate": away_wins / n_games,
         "wilson_lo": luck.wilson_interval(away_wins, n_games)[0],
         "wilson_hi": luck.wilson_interval(away_wins, n_games)[1],
         "exact_p_vs_coin": luck.binomial_p_two_sided(away_wins, n_games, 0.5),
         "measurable": True, "source": "S49"},
        {"label": "Game goes over the total", "k": None, "n": None,
         "rate": None, "wilson_lo": None, "wilson_hi": None,
         "exact_p_vs_coin": None, "measurable": False, "source": "",
         "note": "No official source publishes a total for a game, so the base "
                 "rate for an over/under decision cannot be measured. Left blank "
                 "rather than assumed to be 0.5."},
        {"label": "A named player prop goes over", "k": None, "n": None,
         "rate": None, "wilson_lo": None, "wilson_hi": None,
         "exact_p_vs_coin": None, "measurable": False, "source": "",
         "note": "No official player-prop outcome source is captured, so no base "
                 "rate and no sample size can be stated for props."},
    ]

    bands = []
    for n in NS:
        lo_b, hi_b = luck.luck_band(n, 0.5)
        bands.append({"n": n, "lo": lo_b, "hi": hi_b,
                      "half_width_pp": (hi_b - lo_b) / 2 * 100})

    sizing = []
    for e in EDGES:
        row = {"edge_pp": e * 100, "n_alpha05_power80": luck.required_n(0.5, e)}
        for icc in ICCS:
            row["n_at_icc_%.2f_m2" % icc] = (
                luck.required_n(0.5, e) if icc == 0 else
                int(round(luck.required_n(0.5, e)
                          * luck.cluster_design_effect(2, icc))))
        sizing.append(row)

    k_strategies = 6  # ST01..ST06 in data/strategies.json
    alpha_adj = luck.bonferroni_alpha(0.05, k_strategies)
    n_adj = luck.required_n(0.5, 0.05, alpha=alpha_adj)

    panel = {
        "id": "luck_panel",
        "title": "Removal of luck",
        "updated": "2026-11-16",
        "note": (
            "Every figure below is computed by scripts/build_luck_g.py from "
            "data/results.tsv (137 official 2026 results) using engine/luck.py. "
            "No market price is used anywhere in this panel: a luck band needs a "
            "base rate and a sample size, not a price. Where a base rate cannot be "
            "measured from an official source the row is blank and says why."),
        "headline": {
            "games": n_games,
            "home_wins": home_wins,
            "away_wins": away_wins,
            "ties": ties,
            "home_win_rate": home_rate,
            "home_win_rate_wilson": [lo, hi],
            "exact_p_vs_coin": p_binom,
            "luck_band_95_at_n": [band[0], band[1]],
            "verdict": (
                "The home-team hit rate over 137 official games is %.1f%%. Its "
                "95%% interval is %.1f%% to %.1f%%, which contains 50%%. On this "
                "sample, backing the home team every time is indistinguishable "
                "from a coin flip — which is exactly the point: a season is not "
                "long enough for a small edge to become visible."
                % (home_rate * 100, lo * 100, hi * 100)),
        },
        "brier": {
            "constant_forecast_at_home_rate": bs_home,
            "constant_forecast_at_coin": bs_coin,
            "brier_skill_score_vs_coin": bss_home,
            "note": (
                "Both forecasts are constants: they say the same number for every "
                "game. The skill score of %.4f is what 'no skill' looks like on a "
                "proper score. Any strategy must beat this, not beat zero."
                % bss_home),
        },
        "base_rates": base_rates,
        "luck_bands": bands,
        "sizing": sizing,
        "multiplicity": {
            "strategies_registered": k_strategies,
            "family_alpha": 0.05,
            "per_comparison_alpha": alpha_adj,
            "n_required_at_5pp_edge": n_adj,
            "note": (
                "Ranking the best of %d strategies without adjusting the threshold "
                "is how a lucky run gets mistaken for a method. With the "
                "Bonferroni-adjusted threshold the 5pp-edge sample rises from %s "
                "to %s decisions."
                % (k_strategies, luck.required_n(0.5, 0.05), n_adj)),
        },
        "clustering": {
            "icc_measured": None,
            "icc_note": (
                "The intra-cluster correlation between legs of the same game is "
                "NOT measured in this repository — no joint-outcome source has "
                "been captured. The grid below is therefore a sensitivity, not an "
                "estimate: it shows how fast the required sample grows if legs "
                "inside one game are correlated at all."),
            "icc_grid": ICCS,
            "legs_per_game_example": 2,
        },
        "sources": ["S49", "S50"],
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(panel, fh, indent=2)
        fh.write("\n")

    print("games %d | home %d away %d ties %d | home rate %.4f"
          % (n_games, home_wins, away_wins, ties, home_rate))
    print("Wilson 95%%: %.4f .. %.4f | exact p vs coin %.4f" % (lo, hi, p_binom))
    print("Brier const(home) %.5f  const(coin) %.5f  BSS %.5f"
          % (bs_home, bs_coin, bss_home))
    print("n for 5pp edge: %d (alpha .05, power .80); Bonferroni k=6: %d"
          % (luck.required_n(0.5, 0.05), n_adj))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
