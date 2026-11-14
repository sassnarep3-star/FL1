#!/usr/bin/env python3
"""
build_prop_correlations_d.py — empirical PLAYER-LEVEL correlation estimates for
same-game prop combinations. Closes open question Q-PROP-01 from the computed
research layer (scripts/build_correlations.py measures team-level proxies only
because player data was not available to that session).

Input (NOT committed; workspace-only mirror of the nflverse release):
  /home/user/datawork/player_stats_weekly_archive.parquet
    nflverse `player_stats` weekly format, seasons 1999-2024
    (Beexly/Sports data/nflverse/player_stats_weekly_archive.parquet,
     file commit 2026-11-07T21:48:26Z; nflverse provenance, third-party mirror).

QA gates before any coefficient is published:
  QA1 schema: required columns present.
  QA2 coverage: seasons 1999-2024 present; 2002-2020 seasons >= 250 team-games.
  QA3 join integrity: >= 99% of team-games join to a played row in
      data/raw/games.csv (nflverse games.csv, committed at data/raw).
  QA4 distribution sanity: 2015-2024 league mean team passing yards in
      [200, 300] y/g and mean team points in [15, 30] p/g.
If any gate fails the script exits non-zero and writes nothing.

Statistics: Pearson r (Fisher-z 95% CI), Spearman rho, p-value, n; binary combo
proxies get lift = P(A and B) / (P(A)P(B)) with bootstrap 95% CI
(seed 42, 2000 resamples).

Output: data/prop-correlations-d.csv — all values are labelled computed.
None of them is an official NFL statistic; they are model inputs estimated
from nflverse-derived data, published for review, never as verified facts.
"""
import os
import sys
import numpy as np
import pandas as pd
from scipy import stats as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_GAMES = os.path.join(ROOT, "data", "raw", "games.csv")
OUT = os.path.join(ROOT, "data", "prop-correlations-d.csv")
PARQUET = "/home/user/datawork/player_stats_weekly_archive.parquet"

SOURCE = ("nflverse player_stats 1999-2024 (nflverse-data releases) via Beexly/Sports "
          "mirror, commit 2026-11-07; reconciled vs data/raw/games.csv (QA3)")

SEED = 42
BOOT = 2000


def fisher_ci(r, n):
    z = np.arctanh(r)
    se = 1.0 / np.sqrt(n - 3)
    return float(np.tanh(z - 1.96 * se)), float(np.tanh(z + 1.96 * se))


def pearson_with_ci(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m], b[m]
    n = len(a)
    if n < 30 or a.std() == 0 or b.std() == 0:
        return dict(n=n, r="", lo="", hi="", p="")
    r, p = st.pearsonr(a, b)
    lo, hi = fisher_ci(float(r), n)
    return dict(n=n, r=round(float(r), 4), lo=round(lo, 4), hi=round(hi, 4), p=float(p))


def binary_lift(a, b):
    pA, pB, pAB = a.mean(), b.mean(), (a & b).mean()
    if pA == 0 or pB == 0:
        return None
    rng = np.random.default_rng(SEED)
    draws = []
    n = len(a)
    for _ in range(BOOT):
        s = rng.integers(0, n, n)
        pa, pb, pab = a[s].mean(), b[s].mean(), (a[s] & b[s]).mean()
        draws.append(pab / (pa * pb) if pa > 0 and pb > 0 else np.nan)
    lo, hi = np.nanpercentile(draws, [2.5, 97.5])
    return dict(p_a=pA, p_b=pB, p_ab=pAB, lift=pAB / (pA * pB), lo=lo, hi=hi)


def main():
    if not os.path.exists(PARQUET):
        print(f"FATAL: {PARQUET} missing (workspace mirror only)", file=sys.stderr)
        sys.exit(1)
    df = pd.read_parquet(PARQUET)
    problems = []

    # ---- QA1 schema ----
    need = {"season", "week", "season_type", "recent_team", "position",
            "player_id", "passing_yards", "receiving_yards", "rushing_yards",
            "passing_tds", "receiving_tds"}
    missing = need - set(df.columns)
    if missing:
        print(f"FATAL QA1: missing columns {sorted(missing)}", file=sys.stderr)
        sys.exit(1)

    df = df[df.season_type == "REG"].copy()
    df = df[df.recent_team.notna()]
    df["recent_team"] = df["recent_team"].replace(
        {"LA": "LAR", "WSH": "WAS", "SD": "LAC", "STL": "LAR", "OAK": "LV"})

    # ---- QA2 coverage ----
    seasons = sorted(df.season.unique())
    if seasons[0] != 1999 or seasons[-1] != 2024:
        problems.append(f"QA2: season range {seasons[0]}-{seasons[-1]}")
    for s in range(2002, 2021):
        n_tg = df[df.season == s].groupby(["week", "recent_team"]).ngroups
        if n_tg < 250:
            problems.append(f"QA2: season {s} has {n_tg} team-games < 250")

    # ---- aggregates per team-game ----
    is_wr = df.position.isin(["WR"])
    is_te = df.position.isin(["TE"])
    is_rb = df.position.isin(["RB", "FB"])

    key = ["season", "week", "recent_team"]
    qb_yds = df.groupby(key).passing_yards.sum()
    qb_tds = df.groupby(key).passing_tds.sum()
    wr_yds = df[is_wr].groupby(key).receiving_yards.sum()
    wr_tds = df[is_wr].groupby(key).receiving_tds.sum()
    te_yds = df[is_te].groupby(key).receiving_yards.sum()
    rb_rrecv = df[is_rb].groupby(key).receiving_yards.sum()
    rb_rush = df[is_rb].groupby(key).rushing_yards.sum()

    # ---- QA3 join integrity + team points from data/raw/games.csv ----
    g = pd.read_csv(RAW_GAMES)
    g = g[(g.game_type == "REG") & g.home_score.notna()].copy()
    # Canonicalize both sides to current abbreviations (teams.tsv set):
    # games.csv keeps historical ones (SD, STL, OAK, LA-era Rams); the
    # player_stats archive uses LA for every Rams era and no STL/SD/OAK.
    CANON = {"LA": "LAR", "WSH": "WAS", "SD": "LAC", "STL": "LAR", "OAK": "LV"}
    for c in ("home_team", "away_team"):
        g[c] = g[c].replace(CANON)
    gkey = set(zip(g.season, g.week, g.home_team, g.away_team))
    score_map = {(r.season, r.week, r.home_team): r.home_score
                 for r in g.itertuples()}
    score_map.update({(r.season, r.week, r.away_team): r.away_score
                      for r in g.itertuples()})

    tg_keys = list(qb_yds.index)
    joined = [k for k in tg_keys if (k[0], k[1], k[2]) in score_map]
    join_rate = len(joined) / max(len(tg_keys), 1)
    if join_rate < 0.99:
        problems.append(f"QA3: join rate {join_rate:.4f} < 0.99")

    points = pd.Series({k: float(score_map[(k[0], k[1], k[2])]) for k in joined})

    # ---- QA4 sanity ----
    tp = df[(df.season >= 2015) & (df.season <= 2024)].groupby(key).passing_yards.sum()
    pts15 = points[[k for k in points.index if 2015 <= k[0] <= 2024]]
    if not (200 <= tp.mean() <= 300):
        problems.append(f"QA4: mean team passing yards {tp.mean():.1f}")
    if not (15 <= pts15.mean() <= 30):
        problems.append(f"QA4: mean team points {pts15.mean():.1f}")

    if problems:
        print("FATAL QA failures: " + "; ".join(problems), file=sys.stderr)
        sys.exit(1)

    rows = [["pair_id", "scope", "unit", "window", "n", "pearson_r", "ci95_low",
             "ci95_high", "spearman_rho", "p_value", "p_a", "p_b", "p_joint",
             "lift", "lift_ci95", "source", "status", "notes"]]

    def cont(name, s_a, s_b, scope, unit, window, note=""):
        if window == "2015-2024":
            sel = [k for k in s_a.index if 2015 <= k[0] <= 2024 and k in s_b.index]
        elif window == "2022-2024":
            sel = [k for k in s_a.index if 2022 <= k[0] <= 2024 and k in s_b.index]
        else:
            sel = [k for k in s_a.index if k in s_b.index]
        a = s_a.loc[sel].astype(float)
        b = s_b.loc[sel].astype(float)
        m = a.notna() & b.notna()
        s = pearson_with_ci(a[m].to_numpy(), b[m].to_numpy())
        rho = st.spearmanr(a[m], b[m]).statistic if s["n"] else None
        rows.append([name, scope, unit, window, s["n"], s["r"], s["lo"], s["hi"],
                     round(float(rho), 4) if rho is not None else "", s["p"],
                     "", "", "", "", "", SOURCE, "computed (QA gates passed)", note])

    cont("QB_pass_yds__WR_recv_yds", qb_yds, wr_yds, "same team-game", "yards",
         "2015-2024", "unbiased aggregates, no ex-post WR1 conditioning")
    cont("QB_pass_yds__WR_recv_yds", qb_yds, wr_yds, "same team-game", "yards",
         "2022-2024", "recent-era check")
    cont("QB_pass_yds__TE_recv_yds", qb_yds, te_yds, "same team-game", "yards", "2015-2024")
    cont("QB_pass_yds__RB_recv_yds", qb_yds, rb_rrecv, "same team-game", "yards", "2015-2024")
    cont("QB_pass_tds__WR_recv_tds", qb_tds, wr_tds, "same team-game", "TD counts", "2015-2024")
    cont("RB_rush_yds__RB_recv_yds", rb_rush, rb_rrecv, "same team-game (RB group)", "yards", "2015-2024")
    cont("QB_pass_yds__team_points", qb_yds, points, "same team-game vs team score",
         "yards vs points", "2015-2024", "score join QA3 >= 99%")
    cont("WR_recv_yds__team_points", wr_yds, points, "same team-game vs team score",
         "yards vs points", "2015-2024")
    cont("RB_rush_yds__team_points", rb_rush, points, "same team-game vs team score",
         "yards vs points", "2015-2024")

    for name, sa_thr, sb_thr, s_a, s_b in [
        ("QB_pass_yds>=250__WR_recv_yds>=80", 250, 80, qb_yds, wr_yds),
        ("QB_pass_tds>=1__WR_recv_tds>=1", 1, 1, qb_tds, wr_tds),
        ("QB_pass_yds>=250__TE_recv_yds>=50", 250, 50, qb_yds, te_yds),
    ]:
        sel = [k for k in s_a.index if 2015 <= k[0] <= 2024 and k in s_b.index]
        a = (s_a.loc[sel].astype(float) >= sa_thr)
        b = (s_b.loc[sel].astype(float) >= sb_thr)
        m = s_a.loc[sel].astype(float).notna() & s_b.loc[sel].astype(float).notna()
        r = binary_lift(a[m].to_numpy(), b[m].to_numpy())
        if r:
            rows.append([name, "same team-game (binary)",
                         f"thresholds {sa_thr}/{sb_thr}", "2015-2024", int(m.sum()),
                         "", "", "", "", "", round(r["p_a"], 4), round(r["p_b"], 4),
                         round(r["p_ab"], 4), round(r["lift"], 4),
                         f"[{r['lo']:.4f}, {r['hi']:.4f}]", SOURCE,
                         "computed (bootstrap 2000, seed 42)",
                         "lift>1 => positively correlated legs"])

    pd.DataFrame(rows[1:], columns=rows[0]).to_csv(OUT, index=False)
    print(f"written {OUT}: {len(rows) - 1} rows; QA gates passed "
          f"(join rate {join_rate:.4f}; {len(tg_keys)} team-games)")


if __name__ == "__main__":
    main()
