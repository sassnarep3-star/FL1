"""Ablations instead of fixed penalties: does a personnel feature earn its place?

PURPOSE
-------
The brief rejects "subtract a fixed number of points for a missing starter" and asks
for the same model to be tested with and without the personnel features, with the
difference reported and an uncertainty attached. This module is that harness.

DESIGN
------
- Identical model shapes, trained on identical rows, differing ONLY in whether the
  availability/personnel features are included.
- Chronological splits, never random: train seasons, validation seasons (for
  stability reading), and a final holdout that is scored exactly once.
- Difference = MAE(with feature) - MAE(without) on the holdout, reported with a
  paired bootstrap 95% CI over per-game absolute errors (seeded, deterministic).
- The fitted coefficient of the personnel feature is published with its own
  bootstrap CI, so the "effect of a non-primary QB starter" is an ESTIMATE with
  uncertainty, not an assumed constant.

DEPENDENCIES
------------
None. engine/ stays stdlib-only: the least-squares fit is a small normal-equations
solve via Gaussian elimination, which is exact for these feature counts and lets
the panel re-run in CI without optional packages.

PROVENANCE (published with every output row)
--------------------------------------------
games.csv and the QB-start identity behind depth_deficiency.csv come from the
nflverse combined feed (source S47, third-party snapshot committed at
data/raw/games.csv). The QB-deficiency classes come from data/depth_deficiency.csv
(built by scripts/build_availability.py from that same feed's recorded starters).
No value here is an official NFL publication; every output row carries that label.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Sequence, Tuple

Matrix = List[List[float]]
Vector = List[float]


# ---------------------------------------------------------------------------
# tiny linear algebra (stdlib only)
# ---------------------------------------------------------------------------

def solve_normal_equations(X: Matrix, y: Vector) -> Vector:
    """Solve (X'X) b = X'y by Gaussian elimination with partial pivoting."""
    p = len(X[0])
    ata = [[sum(X[i][a] * X[i][b] for i in range(len(X))) for b in range(p)] for a in range(p)]
    aty = [sum(X[i][a] * y[i] for i in range(len(X))) for a in range(p)]
    # augment
    for a in range(p):
        ata[a].append(aty[a])
    for col in range(p):
        piv = max(range(col, p), key=lambda r: abs(ata[r][col]))
        if abs(ata[piv][col]) < 1e-10:
            raise ValueError("singular normal equations - duplicate/constant features?")
        ata[col], ata[piv] = ata[piv], ata[col]
        pv = ata[col][col]
        for j in range(col, p + 1):
            ata[col][j] /= pv
        for r in range(p):
            if r == col:
                continue
            f = ata[r][col]
            if f:
                for j in range(col, p + 1):
                    ata[r][j] -= f * ata[col][j]
    return [ata[i][p] for i in range(p)]


def predict(X: Matrix, beta: Vector) -> Vector:
    return [sum(x[i] * beta[i] for i in range(len(beta))) for x in X]


# ---------------------------------------------------------------------------
# paired bootstrap on per-game absolute errors
# ---------------------------------------------------------------------------

def paired_mae_diff_ci(err_with: Sequence[float], err_without: Sequence[float],
                       n_boot: int = 4000, seed: int = 20261116,
                       conf: float = 0.95) -> Dict[str, float]:
    """CI for mean(err_with) - mean(err_without), paired by game, seeded and deterministic."""
    if len(err_with) != len(err_without):
        raise ValueError("paired errors must have equal length")
    diffs = [w - o for w, o in zip(err_with, err_without)]
    n = len(diffs)
    mean_diff = sum(diffs) / n
    rng = random.Random(seed)
    boots: List[float] = []
    for _ in range(n_boot):
        s = 0.0
        for _i in range(n):
            s += diffs[rng.randrange(n)]
        boots.append(s / n)
    boots.sort()
    lo_idx = int((1 - conf) / 2 * n_boot)
    hi_idx = min(n_boot - 1, int((1 + conf) / 2 * n_boot) - 1)
    return {
        "mae_diff": round(mean_diff, 4),
        "ci_low": round(boots[lo_idx], 4),
        "ci_high": round(boots[hi_idx], 4),
        "ci_contains_zero": bool(boots[lo_idx] <= 0 <= boots[hi_idx]),
        "n_holdout": n,
        "seed": seed,
        "n_boot": n_boot,
    }


# ---------------------------------------------------------------------------
# dataset assembly
# ---------------------------------------------------------------------------

QB_CLASSES = {"primary starter": 0, "2nd different starter": 1,
              "3rd-or-later different starter": 2}


def load_team_week_qb(depth_rows: Sequence[Dict[str, str]]) -> Dict[Tuple[str, str, str], int]:
    """(season, week, team) -> 0/1/2 QB-deficiency class. Blank 'starters_not_primary' with a
    primary-starter label stays 0; unknown labels are skipped and counted by the caller."""
    out: Dict[Tuple[str, str, str], int] = {}
    for r in depth_rows:
        cls = QB_CLASSES.get(r.get("qb_deficiency", ""))
        if cls is None:
            continue
        out[(r["season"], r["week"], r["team"])] = cls
    return out


def rolling_prior_margin(games: Sequence[Dict[str, str]], by_season: bool = True) \
        -> Dict[Tuple[str, str], List[Tuple[str, float]]]:
    """Per (season, team): chronological list of (game_id, prior mean margin over last 3 games).

    A game's prior margin uses ONLY that team's earlier games in the same season, so no
    future information leaks. First three games of a season have no feature (None).
    """
    per_team: Dict[Tuple[str, str], List[Tuple[str, float]]] = {}
    for g in games:
        if g.get("game_type") != "REG":
            continue
        hs = g.get("home_score", "")
        as_ = g.get("away_score", "")
        if hs == "" or as_ == "":
            continue
        m = float(hs) - float(as_)
        key = (g["season"], g["home_team"])
        per_team.setdefault(key, []).append((g["game_id"], m))
        key = (g["season"], g["away_team"])
        per_team.setdefault(key, []).append((g["game_id"], -m))
    out: Dict[Tuple[str, str], List[Tuple[str, float]]] = {}
    for key, seq in per_team.items():
        hist: List[float] = []
        row: List[Tuple[str, float]] = []
        for gid, m in seq:
            row.append((gid, sum(hist[-3:]) / len(hist[-3:]) if len(hist) >= 3 else None))
            hist.append(m)
        out[key] = row
    return out


def build_rows(games: Sequence[Dict[str, str]], qb: Dict[Tuple[str, str, str], int],
               prior: Dict[Tuple[str, str], List[Tuple[str, float]]],
               target: str) -> List[Dict[str, object]]:
    """One modelling row per game with both teams' features.

    target: "margin" (home points - away points) or "total".
    A row keeps None features where the game has no prior history or the feed lacks
    a QB class; the fitter drops those rows identically for both model shapes, so
    the comparison stays like-for-like.
    """
    rows: List[Dict[str, object]] = []
    prior_index = {k: {gid: v for gid, v in lst} for k, lst in prior.items()}
    for g in games:
        if g.get("game_type") != "REG":
            continue
        hs = g.get("home_score", "")
        as_ = g.get("away_score", "")
        if hs == "" or as_ == "":
            continue
        if target == "margin":
            y = float(hs) - float(as_)
        elif target == "total":
            y = float(hs) + float(as_)
        else:
            raise ValueError(target)
        hm = prior_index.get((g["season"], g["home_team"]), {}).get(g["game_id"])
        am = prior_index.get((g["season"], g["away_team"]), {}).get(g["game_id"])
        hq = qb.get((g["season"], g["week"], g["home_team"]))
        aq = qb.get((g["season"], g["week"], g["away_team"]))
        if hm is None or am is None or hq is None or aq is None:
            continue
        rows.append({
            "game_id": g["game_id"], "season": g["season"], "week": g["week"],
            "y": y, "prior_margin_diff": hm - am,
            "home_qb_class": hq, "away_qb_class": aq,
        })
    return rows


# ---------------------------------------------------------------------------
# the ablation itself
# ---------------------------------------------------------------------------

def features(row: Dict[str, object], with_availability: bool) -> Vector:
    """Base features: intercept + prior-3-game margin difference.
    Availability features (added only in the WITH model): home and away QB-deficiency
    indicators for '2nd different starter' and '3rd-or-later', encoded as 0/1 each.
    This is an indicator design, NOT a fixed points penalty: the model fits the size
    of the effect from training data, and the harness reports it with a CI."""
    x = [1.0, float(row["prior_margin_diff"])]
    if with_availability:
        x += [1.0 if row["home_qb_class"] == 1 else 0.0,
              1.0 if row["home_qb_class"] == 2 else 0.0,
              1.0 if row["away_qb_class"] == 1 else 0.0,
              1.0 if row["away_qb_class"] == 2 else 0.0]
    return x


def ablate(rows: Sequence[Dict[str, object]], train_seasons: set, val_seasons: set,
           holdout_seasons: set, target_name: str, seed: int = 20261116) -> Dict[str, object]:
    """Full ablation for one target: both shapes, holdout difference + paired CI."""
    tr = [r for r in rows if r["season"] in train_seasons]
    va = [r for r in rows if r["season"] in val_seasons]
    ho = [r for r in rows if r["season"] in holdout_seasons]
    if not tr or not ho:
        raise ValueError("empty train or holdout split")
    fits: Dict[str, Dict[str, object]] = {}
    for shape, with_flag in (("without_availability", False), ("with_availability", True)):
        Xtr = [features(r, with_flag) for r in tr]
        ytr = [float(r["y"]) for r in tr]
        beta = solve_normal_equations(Xtr, ytr)
        Xho = [features(r, with_flag) for r in ho]
        yho = [float(r["y"]) for r in ho]
        pho = predict(Xho, beta)
        err_ho = [abs(p - t) for p, t in zip(pho, yho)]
        mae_ho = sum(err_ho) / len(err_ho)
        Xva = [features(r, with_flag) for r in va]
        yva = [float(r["y"]) for r in va]
        pva = predict(Xva, beta)
        mae_va = sum(abs(p - t) for p, t in zip(pva, yva)) / len(yva) if yva else None
        coef_ci: List[Dict[str, object]] | None = None
        if with_flag:
            rng = random.Random(seed + 1)
            boots: List[List[float]] = []
            n = len(tr)
            for _b in range(2000):
                idx = [rng.randrange(n) for _i in range(n)]
                Xb = [features(tr[i], True) for i in idx]
                yb = [float(tr[i]["y"]) for i in idx]
                try:
                    boots.append(solve_normal_equations(Xb, yb))
                except ValueError:
                    continue
            coef_ci = []
            for j, name in ((2, "home_qb_2nd"), (3, "home_qb_3rd_or_later"),
                            (4, "away_qb_2nd"), (5, "away_qb_3rd_or_later")):
                vals = sorted(b[j] for b in boots if len(b) > j)
                if vals:
                    coef_ci.append({
                        "feature": name,
                        "coef": round(beta[j], 4),
                        "ci_low": round(vals[int(0.025 * len(vals))], 4),
                        "ci_high": round(vals[min(len(vals) - 1, int(0.975 * len(vals)) - 1)], 4),
                    })
        fits[shape] = {
            "beta": [round(b, 4) for b in beta],
            "mae_holdout": round(mae_ho, 4),
            "mae_validation": round(mae_va, 4) if mae_va is not None else None,
            "availability_coefficients_ci": coef_ci,
        }
    err_w = [abs(p - t) for p, t in zip(
        predict([features(r, True) for r in ho], fits["with_availability"]["beta"]),  # type: ignore[arg-type]
        [float(r["y"]) for r in ho])]
    err_o = [abs(p - t) for p, t in zip(
        predict([features(r, False) for r in ho], fits["without_availability"]["beta"]),  # type: ignore[arg-type]
        [float(r["y"]) for r in ho])]
    diff = paired_mae_diff_ci(err_w, err_o, seed=seed)
    return {
        "target": target_name,
        "splits": {"train": sorted(train_seasons), "validation": sorted(val_seasons),
                   "holdout": sorted(holdout_seasons)},
        "n_train": len(tr), "n_validation": len(va), "n_holdout": len(ho),
        "without_availability": fits["without_availability"],
        "with_availability": fits["with_availability"],
        "holdout_difference": diff,
    }
