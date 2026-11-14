"""Own-line origination: side first, then total, then moneyline. Standard library only.

Scope and honesty rules (read before using any number this module prints):

* INPUTS. Every game result used here comes from data/results.tsv, which holds the 2026
  regular-season scores that were reconciled to the official nfl.com standings. The
  13 unplayed games in the slate come from data/slate-w10-2026.tsv, which was checked
  line by line against the official Week 10 schedule page. No betting price is an input.
  No market line is read, estimated, or imputed anywhere in this module.

* ORDER. `originate_game` runs three steps in a fixed order and records that order:
    step 1  SIDE       the home-side margin from team ratings (fit on prior results);
    step 2  TOTAL      expected points from season-to-date scoring rates;
    step 3  MONEYLINE  the win probability implied by the step-1 margin (never by a
                       market price, which this module does not have).
  Each step receives only what the earlier steps produced, so a moneyline cannot
  feed back into a side.

* FAIR vs MARKET. Output is a fair (model) value only. Market and difference columns
  are produced by the caller as blanks, because no official price source exists.

* ESTIMATOR. Ridge with an essentially zero penalty (1e-6) only to make the normal
  equations solvable: margins are invariant to a common shift of every rating, so the
  system is rank-deficient without it. The penalty is a numerical device, not a prior.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

RIDGE_EPS = 1e-6
ROUND_TO = 0.5


# ---------------------------------------------------------------- linear algebra ---

def solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting. Raises on a singular system."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ValueError("singular system")
        m[col], m[piv] = m[piv], m[col]
        for r in range(n):
            if r != col and m[r][col] != 0.0:
                f = m[r][col] / m[col][col]
                for c in range(col, n + 1):
                    m[r][c] -= f * m[col][c]
    return [m[i][n] / m[i][i] for i in range(n)]


# ------------------------------------------------------------------- data types ---

@dataclass(frozen=True)
class Game:
    week: int
    away: str
    home: str
    away_pts: int
    home_pts: int
    neutral: bool = False

    @property
    def margin_home(self) -> int:
        return self.home_pts - self.away_pts


@dataclass
class Model:
    ratings: dict
    hfa: float
    n_fit: int
    sigma: float | None = None           # residual SD of home margin, from backtest
    rates: dict = field(default_factory=dict)   # team -> (pf_per_g, pa_per_g, games)


# --------------------------------------------------------------------- fitting ---

def fit(games: Sequence[Game]) -> Model:
    """Least squares of home margin on team ratings (+1 home, -1 away) and a home-field
    term that applies only to non-neutral games."""
    teams = sorted({g.home for g in games} | {g.away for g in games})
    idx = {t: i for i, t in enumerate(teams)}
    k = len(teams) + 1                   # + home-field column
    xtx = [[0.0] * k for _ in range(k)]
    xty = [0.0] * k
    for g in games:
        x = [0.0] * k
        x[idx[g.home]] += 1.0
        x[idx[g.away]] -= 1.0
        x[-1] = 0.0 if g.neutral else 1.0
        y = float(g.margin_home)
        for i in range(k):
            if x[i] == 0.0:
                continue
            xty[i] += x[i] * y
            for j in range(k):
                xtx[i][j] += x[i] * x[j]
    for i in range(k):
        xtx[i][i] += RIDGE_EPS
    beta = solve(xtx, xty)
    ratings = {t: beta[idx[t]] for t in teams}
    mean = sum(ratings.values()) / len(ratings)
    ratings = {t: r - mean for t, r in ratings.items()}   # centre on zero (display only)
    model = Model(ratings=ratings, hfa=beta[-1], n_fit=len(games))
    model.rates = scoring_rates(games)
    return model


def scoring_rates(games: Sequence[Game]) -> dict:
    acc: dict = {}
    for g in games:
        for team, pf, pa in ((g.home, g.home_pts, g.away_pts), (g.away, g.away_pts, g.home_pts)):
            a = acc.setdefault(team, [0, 0, 0])
            a[0] += pf
            a[1] += pa
            a[2] += 1
    return {t: (v[0] / v[2], v[1] / v[2], v[2]) for t, v in acc.items()}


# ------------------------------------------------------------------ the steps ---

def _norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def round_line(x: float) -> float:
    return round(x / ROUND_TO) * ROUND_TO


def american(p: float) -> int:
    """Fair American price for win probability p (no vig: a fair price, not a market)."""
    p = min(max(p, 1e-6), 1 - 1e-6)
    if p >= 0.5:
        return -int(round(100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def originate_game(model: Model, away: str, home: str, neutral: bool) -> dict:
    """Run the three steps in the mandated order and return the record for one game."""
    if model.sigma is None:
        raise ValueError("sigma must come from the walk-forward backtest before origination")
    steps = []

    # step 1 -- SIDE
    hfa = 0.0 if neutral else model.hfa
    margin = model.ratings[home] - model.ratings[away] + hfa
    side_raw = -margin                                  # spread convention: home line
    steps.append("1 SIDE: margin = rating(home) - rating(away) + home-field"
                 + (" (neutral: 0)" if neutral else ""))

    # step 2 -- TOTAL (independent of the side; recorded after it by design)
    h_pf, h_pa, h_g = model.rates[home]
    a_pf, a_pa, a_g = model.rates[away]
    exp_home = (h_pf + a_pa) / 2.0
    exp_away = (a_pf + h_pa) / 2.0
    total_raw = exp_home + exp_away
    steps.append("2 TOTAL: (home PF/g + away PA/g)/2 + (away PF/g + home PA/g)/2")

    # step 3 -- MONEYLINE (uses only the step-1 margin and the backtest sigma)
    p_home = _norm_cdf(margin / model.sigma)
    steps.append("3 MONEYLINE: P(home) = Phi(margin / sigma), sigma from backtest")

    return {
        "order": steps,
        "fair_home_spread_raw": side_raw,
        "fair_home_spread": round_line(side_raw),
        "fair_total_raw": total_raw,
        "fair_total": round_line(total_raw),
        "p_home": p_home,
        "fair_ml_home": american(p_home),
        "fair_ml_away": american(1.0 - p_home),
        "home_margin_expected": margin,
        "games_home": h_g, "games_away": a_g,
    }


# ----------------------------------------------------------------- backtest ---

def walk_forward(games: Sequence[Game], first_week: int = 4) -> list[dict]:
    """Predict each game in week w using only games from weeks < w. Strictly out of sample.

    Three predictions are scored, in the same order the origination uses them:
    side (home margin), total (points), and moneyline (win probability via Phi(margin/sigma)).
    Sigma is fixed inside the loop from the training games only, so no future error leaks in.
    """
    out = []
    weeks = sorted({g.week for g in games})
    for w in weeks:
        if w < first_week:
            continue
        train = [g for g in games if g.week < w]
        test = [g for g in games if g.week == w]
        if not test or len(train) < 20:
            continue
        m = fit(train)
        # training residual sigma (in-sample) gives the moneyline scale for this window
        res = [(g.margin_home - (m.ratings[g.home] - m.ratings[g.away] + (0.0 if g.neutral else m.hfa)))
               for g in train]
        sigma_w = math.sqrt(sum(e * e for e in res) / len(res))
        bench_margin = sum(g.margin_home for g in train) / len(train)
        bench_total = sum(g.home_pts + g.away_pts for g in train) / len(train)
        for g in test:
            hfa = 0.0 if g.neutral else m.hfa
            pred = m.ratings[g.home] - m.ratings[g.away] + hfa
            h_pf, h_pa, _ = m.rates[g.home]
            a_pf, a_pa, _ = m.rates[g.away]
            pred_total = (h_pf + a_pa) / 2.0 + (a_pf + h_pa) / 2.0
            p_home = _norm_cdf(pred / sigma_w)
            home_won = 1.0 if g.margin_home > 0 else (0.0 if g.margin_home < 0 else 0.5)
            out.append({"week": w, "game": g, "pred": pred, "bench": bench_margin,
                        "actual": g.margin_home, "pred_total": pred_total,
                        "bench_total": bench_total, "actual_total": g.home_pts + g.away_pts,
                        "p_home": p_home, "home_won": home_won, "sigma": sigma_w,
                        "n_train": len(train)})
    return out


def wilson(k: int, n: int, z: float = 1.96):
    """Wilson score interval for a proportion k/n."""
    if n == 0:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def summarise_backtest(rows: Sequence[dict]) -> dict:
    """Out-of-sample statistics for side, total and moneyline. n is published with every value."""
    n = len(rows)
    if n == 0:
        return {"n": 0}
    err = [r["actual"] - r["pred"] for r in rows]
    err_b = [r["actual"] - r["bench"] for r in rows]
    mae = sum(abs(e) for e in err) / n
    mae_b = sum(abs(e) for e in err_b) / n
    rmse = math.sqrt(sum(e * e for e in err) / n)
    bias = sum(err) / n
    t_err = [r["actual_total"] - r["pred_total"] for r in rows]
    t_err_b = [r["actual_total"] - r["bench_total"] for r in rows]
    nz = [r for r in rows if r["pred"] != 0 and r["actual"] != 0]
    sign_hit = sum(1 for r in nz if (r["pred"] > 0) == (r["actual"] > 0))
    lo, hi = wilson(sign_hit, len(nz))
    brier = sum((r["p_home"] - r["home_won"]) ** 2 for r in rows) / n
    brier_c = sum((0.5 - r["home_won"]) ** 2 for r in rows) / n
    return {"n": n, "mae": mae, "mae_benchmark": mae_b, "rmse": rmse, "bias": bias,
            "sign_n": len(nz), "sign_hits": sign_hit,
            "sign_rate": (sign_hit / len(nz)) if nz else None,
            "sign_ci": (lo, hi),
            "total_mae": sum(abs(e) for e in t_err) / n,
            "total_mae_benchmark": sum(abs(e) for e in t_err_b) / n,
            "total_bias": sum(t_err) / n,
            "brier_model": brier, "brier_coinflip": brier_c}


def weekly_backtest(rows: Sequence[dict]) -> list[dict]:
    out = []
    for w in sorted({r["week"] for r in rows}):
        s = summarise_backtest([r for r in rows if r["week"] == w])
        s["week"] = w
        out.append(s)
    return out
