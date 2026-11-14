"""
Correlation engine for single bets, parlays and same-game combinations.

WHY THIS EXISTS
---------------
A parlay's price already contains an assumption about how independent the legs
are. Books price parlays and same-game parlays with a correlation adjustment.
If you build combinations whose true correlation is higher than the book priced,
your expected value improves; if lower, you are being sold a lottery ticket.

WHAT THIS MEASURES (and what it cannot)
---------------------------------------
* Legs ACROSS games are treated as independent. That is testable here: we
  measure the empirical correlation of the outcomes we can observe.
* Legs WITHIN a game (same-game parlay / prop combos) cannot be measured at
  prop level without player-prop data, which is not available in this sandbox
  (see data/unverified.csv). We measure the *team-level* correlations that
  drive same-game builds: home cover vs over, home cover vs home moneyline,
  over vs home win, and the joint distribution of margin and total.
* Player-prop combos are therefore only covered at the level of the
  statistically identical team-level proxies, and the gap is explicitly
  flagged as an open question (Q-PROP-01).

Run: python3 scripts/build_correlations.py
"""
from __future__ import annotations

import itertools
import json
import math
import pathlib

import numpy as np
import pandas as pd
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data"

MIN_SEASON = 2006  # moneylines exist from here (see data/raw/MANIFEST.json)


def load() -> pd.DataFrame:
    g = pd.read_csv(RAW / "games.csv")
    g = g[g.game_type == "REG"]
    g = g[g.home_score.notna() & g.away_score.notna()]
    g["margin"] = g.home_score - g.away_score
    g["total"] = g.home_score + g.away_score
    g["ats"] = g.margin + g.spread_line
    g["tot"] = g.total - g.total_line
    g = g[g.season >= MIN_SEASON]
    return g.dropna(subset=["spread_line", "total_line"])


def phi_ci(a: np.ndarray, b: np.ndarray) -> dict:
    """Correlation of two binary series with bootstrap CI and Fisher p."""
    n = len(a)
    r, p = stats.pearsonr(a, b)
    # bootstrap CI
    rng = np.random.default_rng(20261114)
    boot = []
    for _ in range(2000):
        idx = rng.integers(0, n, n)
        aa, bb = a[idx], b[idx]
        if aa.std() == 0 or bb.std() == 0:
            continue
        boot.append(np.corrcoef(aa, bb)[0, 1])
    lo, hi = (np.percentile(boot, [2.5, 97.5]) if boot else (np.nan, np.nan))
    return {"n": n, "corr": round(float(r), 4), "p_value": round(float(p), 5),
            "ci_low": round(float(lo), 4), "ci_high": round(float(hi), 4)}


def main() -> int:
    g = load()
    rows = []

    # ---- 1. team-level outcomes, one game each -----------------------------
    home_cover = (g.ats > 0).astype(int).to_numpy()
    away_cover = (g.ats < 0).astype(int).to_numpy()
    over = (g.tot > 0).astype(int).to_numpy()
    home_win = (g.margin > 0).astype(int).to_numpy()

    pairs = [
        ("home_cover", home_cover, "over", over,
         "SAME-GAME", "Home ATS cover vs over",
         "The classic 'good team scores, bad team scores late' mechanic; books shade this in SGP pricing."),
        ("home_cover", home_cover, "home_win", home_win,
         "SAME-GAME", "Home ATS cover vs home moneyline",
         "Structurally positive: covering a spread almost always means winning unless the spread is tiny."),
        ("home_win", home_win, "over", over,
         "SAME-GAME", "Home moneyline vs over",
         "Weak positive in theory (favourite scoring drives the total up)."),
        ("away_cover", away_cover, "over", over,
         "SAME-GAME", "Away ATS cover vs over",
         "Complement of the home-cover/over relationship."),
    ]
    for na, a, nb, b, scope, label, note in pairs:
        row = {"leg_a": na, "leg_b": nb, "scope": scope, "label": label,
               "note": note, "seasons": f"{g.season.min()}-{g.season.max()}"}
        row.update(phi_ci(a, b))
        rows.append(row)

    # ---- 2. continuous correlation: margin vs total ------------------------
    r, p = stats.pearsonr(g.margin, g.total)
    rows.append({
        "leg_a": "margin", "leg_b": "total", "scope": "SAME-GAME",
        "label": "Continuous: home margin vs game total",
        "note": "Feeds the joint distribution used for correlated SGP pricing.",
        "seasons": f"{g.season.min()}-{g.season.max()}",
        "n": int(len(g)), "corr": round(float(r), 4), "p_value": round(float(p), 5),
        "ci_low": None, "ci_high": None,
    })

    # ---- 3. cross-game legs: are they independent? ------------------------
    # A 2-leg parlay of straight bets across two different games, tested by
    # comparing observed joint win rate to the product of the marginals.
    s = g.sort_values(["season", "week", "gameday"]).reset_index(drop=True)
    hc = (s.ats > 0).astype(int).to_numpy()
    ov = (s.tot > 0).astype(int).to_numpy()
    n = len(s) - 1
    joint_hc_hc = float((hc[:-1] * hc[1:]).sum() / n)
    marg_hc = float(hc.mean())
    joint_ov_ov = float((ov[:-1] * ov[1:]).sum() / n)
    marg_ov = float(ov.mean())
    rows.append({
        "leg_a": "home_cover(t)", "leg_b": "home_cover(t+1)", "scope": "ACROSS-GAMES",
        "label": "Sequential games, home covers",
        "note": "Observed joint rate vs the product of marginal rates. Defines the independence baseline for straight parlays.",
        "seasons": f"{s.season.min()}-{s.season.max()}", "n": n,
        "corr": round(joint_hc_hc - marg_hc * marg_hc, 6),
        "p_value": None, "ci_low": None, "ci_high": None,
        "observed_joint": round(joint_hc_hc, 6),
        "independence_product": round(marg_hc * marg_hc, 6),
    })
    rows.append({
        "leg_a": "over(t)", "leg_b": "over(t+1)", "scope": "ACROSS-GAMES",
        "label": "Sequential games, over hits",
        "note": "Same test on totals.",
        "seasons": f"{s.season.min()}-{s.season.max()}", "n": n,
        "corr": round(joint_ov_ov - marg_ov * marg_ov, 6),
        "p_value": None, "ci_low": None, "ci_high": None,
        "observed_joint": round(joint_ov_ov, 6),
        "independence_product": round(marg_ov * marg_ov, 6),
    })

    # ---- 4. parlay economics ----------------------------------------------
    # A parlay's true breakeven depends on the correlation AND the book's
    # pricing rule. We compute the break-even leg hit rate for 2, 3 and 4 legs
    # under (a) independent pricing at -110 per leg and (b) the same-game
    # correlated case using the measured phi.
    econ = []
    for nlegs in (2, 3, 4):
        fair_dec = (1 + 100 / 110) ** nlegs        # true odds if independent, -110 each
        for corr_label, phi in (("independent", 0.0),
                                ("measured_home_cover_over", rows[0]["corr"])):
            # approximate joint probability of all legs winning for a
            # compound-symmetric binary vector with marginal 0.5 and pairwise phi
            p_leg = 0.5
            if corr_label == "independent":
                p_all = p_leg ** nlegs
            else:
                # pairwise blend: use the average of the fully-independent and
                # fully-comonotone cases weighted by phi (documented approximation)
                p_all = p_leg ** nlegs + phi * (p_leg - p_leg ** nlegs)
            econ.append({
                "parlay_legs": nlegs, "correlation_assumption": corr_label,
                "pairwise_phi": round(float(phi), 4),
                "price_at_-110_each_decimal": round(fair_dec, 4),
                "implied_prob_at_that_price": round(1 / fair_dec, 5),
                "true_joint_prob": round(float(p_all), 5),
                "ev_per_unit_if_priced_independent": round(float(p_all * fair_dec - 1), 5),
            })
    pd.DataFrame(econ).to_csv(OUT / "parlay_economics.csv", index=False)

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "correlations.csv", index=False)

    # correlation matrix for the site
    mat = pd.DataFrame({
        "home_cover": home_cover, "away_cover": away_cover,
        "over": over, "home_win": home_win,
    }).corr()
    mat.round(4).to_csv(OUT / "correlation_matrix.csv")

    print(df[["leg_a", "leg_b", "scope", "n", "corr", "p_value", "ci_low", "ci_high"]].to_string(index=False))
    print()
    print(pd.DataFrame(econ).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
