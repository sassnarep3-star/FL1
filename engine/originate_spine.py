"""Line origination, in the order the brief demands: side, then total, then moneyline.

THE ORDER IS NOT COSMETIC
    The spread is the market's statement about *relative strength*; the total is its
    statement about *pace*; the moneyline is a re-statement of relative strength in a
    different payout shape. Once a margin distribution exists, the moneyline is arithmetic
    - it is not a third thing to be fitted. Fitting the moneyline separately to prices
    would produce three models that disagree with each other and could not be reconciled,
    so this module enforces the order in code:

        originate_total()      raises until originate_side() has run
        derive_moneyline()     raises until originate_side() has run

    There is no function in this module that estimates a market price. The market line is
    read from the price store and copied through; a test asserts that this file contains no
    optimiser import, because a fitted "market line" would be our guess wearing someone
    else's name.

WHAT IS ESTIMATED, AND HOW
    Everything is fitted from the verified results ledger by walk-forward update, and
    every parameter is published with the objective it was chosen for and the window it
    was chosen on. No folklore constants: no "home field is 2.5 points", no
    "Questionable means 50%".

    Stage 1/2 model - exponentially weighted attack/defense scoring levels:
        o_i = EWMA(points scored by i - league mean)      (offence, in points)
        d_i = EWMA(points allowed by i - league mean)     (defence, in points)
        expected_away = mu + s*(o_a + d_h)
        expected_home = mu + s*(o_h + d_a) + hfa
        margin_pred   = expected_home - expected_away
        total_pred    = expected_home + expected_away
    (mu is a trailing league mean, computed from the same ledger; s and hfa are fitted.)

    Stage 3 - the win probability is the empirical CDF of the model's own margin
    residuals, evaluated at -margin_pred. That is deliberately non-parametric: a normal
    approximation is also computed and published next to it, because assuming normality
    in a distribution with ties and blowouts is exactly the kind of assumption this
    repository exists to make visible rather than to make silently.
"""

from __future__ import annotations

import bisect
import math
from collections import OrderedDict
from typing import Sequence

from . import pricing

KEY_NUMBERS = (3.0, 7.0, 10.0, 14.0)
ROUND_TO = 0.5


def fair_american(prob: float) -> int:
    """Zero-vig American price for a two-way market.

    p >= 0.5 -> a lay price (negative); p < 0.5 -> a dog price (positive). This is the
    inverse of `engine.pricing.implied_probability`, so a reviewer can check it by
    converting the answer back. It is deliberately not written anywhere as a quote we
    could have traded at: it is the fair value our model implies, at zero hold.

    A moneyline is a two-way market; an NFL tie is a push on both sides, so the tie
    probability is removed by renormalising the two win probabilities (see
    `OriginationPipeline.derive_moneyline`), not by splitting it half to each side.
    """
    if not 0.0 < prob < 1.0:
        raise ValueError("probability must be strictly between 0 and 1, got %r" % prob)
    if prob >= 0.5:
        return int(round(-100.0 * prob / (1.0 - prob)))
    return int(round(100.0 * (1.0 - prob) / prob))


def laplace_win_prob(above: int, n: int) -> float:
    """(above + 1) / (n + 2): keeps a saturated empirical tail finite and honest.

    The residual distribution is a window, not a law. With n residuals all on one side of
    a handicap, the raw empirical probability is 1.0, which prices as an infinite payout.
    The +1/+2 correction gives 1 - 1/(n+2): still extreme, still finite, and the row
    carries `residual_n` so the reader can see how thin the tail was.
    """
    if n <= 0:
        return 0.5
    return (above + 1.0) / (n + 2.0)


class StageOrderError(RuntimeError):
    """Raised when the pipeline is asked to do a stage out of order."""


class NoMarketLine(Exception):
    """Raised when a delta is requested but no market number exists for that game."""


def round_half(v: float, direction: str = "nearest") -> float:
    step = ROUND_TO
    if direction == "up":
        return math.ceil(v / step) * step
    if direction == "down":
        return math.floor(v / step) * step
    return round(v / step) * step


def key_number_distance(line: float) -> float:
    """Distance from the nearest key number - a spread is only as good as its keys."""
    return min(abs(abs(float(line)) - k) for k in KEY_NUMBERS)


# ---------------------------------------------------------------------------
# scoring model (shared by stages 1 and 2)
# ---------------------------------------------------------------------------
class ScoringModel:
    """Online EWMA attack/defence ratings. Update after each settled game only."""

    def __init__(self, mu: float, lam: float, s: float, hfa: float):
        self.mu = float(mu)
        self.lam = float(lam)
        self.s = float(s)
        self.hfa = float(hfa)
        self.off: dict[str, float] = {}
        self.defn: dict[str, float] = {}
        self.seen: set[str] = set()

    def _o(self, team: str) -> float:
        return self.off.get(team, 0.0)

    def _d(self, team: str) -> float:
        return self.defn.get(team, 0.0)

    def predict(self, away: str, home: str) -> tuple[float, float]:
        exp_away = self.mu + self.s * (self._o(away) + self._d(home))
        exp_home = self.mu + self.s * (self._o(home) + self._d(away)) + self.hfa
        return exp_home - exp_away, exp_home + exp_away

    def update(self, away: str, home: str, away_pts: float, home_pts: float) -> None:
        for team, pts, opp in ((away, away_pts, home_pts), (home, home_pts, away_pts)):
            w = 1.0 - self.lam
            self.off[team] = self.lam * self._o(team) + w * (pts - self.mu)
            self.defn[team] = self.lam * self._d(team) + w * (opp - self.mu)
            self.seen.add(team)


def league_mean_points(games: Sequence[dict], upto_season: int) -> float:
    tot = n = 0
    for g in games:
        if g["season"] >= upto_season or g["game_type"] not in ("REG", "WC", "DIV", "CON", "SB"):
            continue
        if g["away_score"] is None or g["home_score"] is None:
            continue
        tot += g["away_score"] + g["home_score"]
        n += 2
    return (tot / n) if n else 0.0


def trailing_mu(games: Sequence[dict], season: int, back: int = 3) -> float:
    """League average points per team over the `back` seasons before `season`.

    Recomputed at every season boundary, because a scoring environment that drifts (rule
    changes, pace changes) must not be priced off a decade-old constant. This is a window,
    not a fitted parameter, and the window length is published with the model card.
    """
    tot = n = 0
    for g in games:
        if not (season - back <= g["season"] < season):
            continue
        if g["away_score"] is None or g["home_score"] is None:
            continue
        tot += g["away_score"] + g["home_score"]
        n += 2
    return (tot / n) if n else 0.0


def _run(games: Sequence[dict], upto_season: int, params: tuple[float, float, float],
         want_predictions: bool = False, mu_window: int = 3) -> dict:
    """Single chronological pass. Returns error stats and (optionally) per-game rows."""
    lam, s, hfa = params
    mu = trailing_mu(games, upto_season, mu_window) or league_mean_points(games, upto_season)
    model = ScoringModel(mu, lam, s, hfa)
    margin_err, total_err = [], []
    residual_cdf: list[float] = []
    rows: list[dict] = []
    seen_season = None
    for g in games:
        if g["season"] >= upto_season:
            continue
        if g["season"] != seen_season:
            seen_season = g["season"]
            fresh = trailing_mu(games, seen_season, mu_window)
            if fresh:
                model.mu = mu = fresh
        played = g["away_score"] is not None and g["home_score"] is not None
        if played:
            margin_act = float(g["home_score"] - g["away_score"])
            total_act = float(g["home_score"] + g["away_score"])
        else:
            margin_act = total_act = None
        pred_margin = pred_total = None
        if len(model.seen) >= 2 and (g["away"] in model.seen or g["home"] in model.seen):
            pred_margin, pred_total = model.predict(g["away"], g["home"])
        if want_predictions:
            rows.append({"game": g, "pred_margin": pred_margin, "pred_total": pred_total,
                         "actual_margin": margin_act, "actual_total": total_act,
                         "mu": mu})
        if margin_act is not None:
            if pred_margin is not None:
                margin_err.append(abs(margin_act - pred_margin))
                total_err.append(abs(total_act - pred_total))
                bisect.insort(residual_cdf, margin_act - pred_margin)
            model.update(g["away"], g["home"], float(g["away_score"]), float(g["home_score"]))
    return {"mae_margin": (sum(margin_err) / len(margin_err)) if margin_err else float("nan"),
            "mae_total": (sum(total_err) / len(total_err)) if total_err else float("nan"),
            "sd_residual": _sd(residual_cdf), "n_pred": len(margin_err), "mu": mu,
            "rows": rows, "residuals": residual_cdf}


def _sd(xs: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


GRID_LAM = (0.88, 0.92, 0.96)
GRID_S = (0.40, 0.55, 0.70, 0.85)
GRID_HFA = (0.5, 1.5, 2.5, 3.5)


def tune(games: Sequence[dict], dev_until: int, objective: str = "mae_margin") -> dict:
    """Grid search on the development window only. Returns best params + the whole grid."""
    grid = []
    for lam in GRID_LAM:
        for s in GRID_S:
            for hfa in GRID_HFA:
                res = _run(games, dev_until, (lam, s, hfa))
                grid.append({"lam": lam, "s": s, "hfa": hfa, "mae_margin": res["mae_margin"],
                             "mae_total": res["mae_total"], "n_pred": res["n_pred"]})
    key = "mae_margin" if objective.startswith("mae") else objective
    grid_ok = [g for g in grid if g[key] == g[key]]  # drop NaN
    best = min(grid_ok, key=lambda g: g[key]) if grid_ok else None
    return {"best": best, "grid": sorted(grid, key=lambda g: g[key]),
            "objective": key, "dev_window": "1999-%d" % (dev_until - 1), "grid_size": len(grid)}


# ---------------------------------------------------------------------------
# the pipeline
# ---------------------------------------------------------------------------
class OriginationPipeline:
    """Enforced stage order: side -> total -> moneyline. The market line is never fitted.

    One game at a time, in chronological order:

        pipe.begin_game()
        side = pipe.originate_side(game_with_market_lines)
        tot  = pipe.originate_total(side, game_with_market_lines)
        ml   = pipe.derive_moneyline(side, game_with_market_lines)
        pipe.finish_game(game)          # folds the result into model + residuals

    Calling `originate_total` or `derive_moneyline` before `originate_side` raises
    `StageOrderError`; that is the requirement, written as code.
    """

    def __init__(self, params: dict, residual_window: int = 6000):
        self.params = dict(params)
        self.model = ScoringModel(self.params.get("mu", 0.0), self.params.get("lam", 0.92),
                                  self.params.get("s", 0.55), self.params.get("hfa", 2.0))
        self.residuals: list[float] = []
        self.residual_window = int(residual_window)
        self.stages_completed: "OrderedDict[str, int]" = OrderedDict(
            [("side", 0), ("total", 0), ("moneyline", 0)])
        self.games = 0
        self.current: set[str] = set()
        self.market = {}
        # set by originate_side(); a stage that runs before the side stage must be able to
        # name the game it is refusing, so the attribute exists from construction
        self._gid = "(no game opened yet)"

    # -- plumbing ----------------------------------------------------------
    def begin_game(self) -> None:
        self.current = set()

    def _require(self, stage: str, after: str) -> None:
        if after not in self.current:
            raise StageOrderError(
                "%s cannot run before %s for game %s: the moneyline is a re-statement of "
                "the margin distribution and the total is scored on the same levels"
                % (stage, after, self._gid))
        self.current.add(stage)
        self.stages_completed[stage] += 1

    def attach_market_lines(self, market_by_game: dict) -> None:
        """Market numbers come from the price store. There is no fit here and there never will be."""
        self.market = market_by_game

    # -- stage 1: the side --------------------------------------------------
    def originate_side(self, game: dict) -> dict:
        """Fair spread from the fitted scoring levels, plus the delta to the market line."""
        self._gid = game["game_id"]
        if "side" in self.current:
            raise StageOrderError("side already originated for %s - begin_game() first" % self._gid)
        self.current.add("side")
        self.stages_completed["side"] += 1
        away, home = game["away"], game["home"]
        pred_margin, pred_total = self.model.predict(away, home)
        fair_raw = -pred_margin
        fair = round_half(fair_raw)
        mkt = game.get("market_side_line_home")
        return OrderedDict([
            ("game_id", self._gid), ("season", game["season"]), ("week", game["week"]),
            ("gameday", game.get("gameday", "")), ("away", away), ("home", home),
            ("pred_margin_home", _r4(pred_margin)),
            ("fair_side_line_home_raw", _r4(fair_raw)),
            ("fair_side_line_home", fair),
            ("fair_side_line_away", round_half(-fair_raw)),
            ("market_side_line_home", mkt),
            ("market_line_source", game.get("side_line_source", "")),
            ("market_line_vintage", game.get("side_line_vintage", "")),
            ("delta_side_pts", None if mkt is None else _r4(fair - float(mkt))),
            ("delta_side_basis", "fair minus market, home perspective, after 0.5 rounding"
             if mkt is not None else "no market line in the store for this game"),
            ("key_number_distance", round(key_number_distance(fair), 4)),
            ("rounding_shift_pts", _r4(fair - fair_raw)),
            ("residual_n", len(self.residuals)),
            ("pred_total", _r4(pred_total)),
        ])

    # -- stage 2: the total --------------------------------------------------
    def originate_total(self, side_row: dict, game: dict) -> dict:
        self._require("total", "side")
        fair = round_half(side_row["pred_total"])
        mkt = game.get("market_total_line")
        return OrderedDict([
            ("game_id", side_row["game_id"]), ("season", side_row["season"]),
            ("week", side_row["week"]),
            ("fair_total_raw", side_row["pred_total"]), ("fair_total", fair),
            ("market_total_line", mkt),
            ("market_total_source", game.get("total_line_source", "")),
            ("market_total_vintage", game.get("total_line_vintage", "")),
            ("delta_total_pts", None if mkt is None else _r4(fair - float(mkt))),
            ("over_price", game.get("over_price")),
            ("under_price", game.get("under_price")),
            ("price_basis", "posted in store" if game.get("over_price") is not None
             else "no posted price in store"),
            ("residual_n", len(self.residuals)),
        ])

    # -- stage 3: the moneyline, derived ------------------------------------
    def derive_moneyline(self, side_row: dict, game: dict) -> dict:
        self._require("moneyline", "side")
        mu = side_row["pred_margin_home"]
        p_home, p_away, tie = self._probs(mu)
        mkt_home, mkt_away = game.get("market_ml_home"), game.get("market_ml_away")
        dev = pricing.devig_two_way(mkt_home, mkt_away) if (mkt_home and mkt_away) else None
        sd = self.params.get("sd_residual")
        p_norm = 0.5 if not sd or sd != sd else 0.5 * (
            1.0 + math.erf(mu / (sd * math.sqrt(2.0))))
        return OrderedDict([
            ("game_id", side_row["game_id"]), ("season", side_row["season"]),
            ("week", side_row["week"]),
            ("fair_p_home", _r6(p_home)), ("fair_p_away", _r6(p_away)),
            ("tie_share", _r6(tie)),
            ("fair_p_home_normal_approx", _r6(p_norm)),
            ("fair_price_home", fair_american(p_home)),
            ("fair_price_away", fair_american(p_away)),
            ("derivation", "P(margin residual > -pred_margin) on the model residual window; "
                           "normal approximation shown for comparison only"),
            ("market_ml_home", mkt_home), ("market_ml_away", mkt_away),
            ("market_price_source", game.get("ml_source", "")),
            ("market_price_vintage", game.get("ml_vintage", "")),
            ("market_p_home_novig", None if not dev else _r6(dev[0])),
            ("market_hold_pct", None if not dev else _r6(100.0 * pricing.two_way_margin(
                mkt_home, mkt_away))),
            ("delta_ml_pp", None if not dev else _r4(100.0 * (p_home - dev[0]))),
            ("delta_ml_basis", "fair minus no-vig market probability, percentage points"
             if dev else "no market moneyline pair in the store - delta left blank"),
            ("residual_n", len(self.residuals)),
        ])

    # -- after settlement ----------------------------------------------------
    def finish_game(self, game: dict, side_row: dict) -> None:
        """Fold the settled result into the ratings and the residual window."""
        self.games += 1
        a, h = game.get("away_score"), game.get("home_score")
        if a is None or h is None:
            return
        margin = float(h) - float(a)
        self.model.update(game["away"], game["home"], float(a), float(h))
        pred = side_row.get("pred_margin_home")
        if pred is not None:
            bisect.insort(self.residuals, margin - float(pred))
            if len(self.residuals) > self.residual_window:
                del self.residuals[0]

    def _probs(self, mu: float) -> tuple[float, float, float]:
        """Empirical win/tie/loss shares of the predicted margin, Laplace-corrected."""
        r = self.residuals
        n = len(r)
        cut = -mu
        lo = bisect.bisect_left(r, cut)
        hi = bisect.bisect_right(r, cut)
        below, tie, above = lo, hi - lo, n - hi
        p_home = laplace_win_prob(above, n)
        p_away = laplace_win_prob(below, n)
        s = p_home + p_away
        if s <= 0:
            return 0.5, 0.5, 0.0
        tie_share = tie / n if n else 0.0
        return p_home / s, p_away / s, tie_share

    def audit(self) -> dict:
        return OrderedDict([
            ("stage_order", ["side", "total", "moneyline"]),
            ("stages_completed", dict(self.stages_completed)),
            ("games_run", self.games),
            ("depends_on", {"side": ["fitted scoring levels"],
                            "total": ["side (same scoring levels)"],
                            "moneyline": ["side (margin residual distribution)"]}),
            ("fitted_parameters", {k: self.params[k] for k in
                                   ("mu", "lam", "s", "hfa", "sd_residual") if k in self.params}),
            ("market_price_fitted", False),
            ("residual_window", self.residual_window),
            ("note", "the moneyline is derived, never fitted to prices; market lines are "
                     "read from the price store and this module never writes to it"),
        ])


def _r4(v) -> float | None:
    return None if v is None else round(float(v), 4)


def _r6(v) -> float | None:
    return None if v is None else round(float(v), 6)


# ---------------------------------------------------------------------------
# driver used by scripts/build_market_spine.py
# ---------------------------------------------------------------------------
def run_pipeline(games: Sequence[dict], market_by_game: dict, params: dict,
                 evaluate_from_season: int, progress: bool = False) -> dict:
    """Walk the schedule once, in order, and return the three published tables.

    Rows are produced for every game from `evaluate_from_season` onward. Seasons before
    that are still consumed, so the model a game is priced with has only ever seen
    earlier games - which is the whole point of a walk-forward run.
    """
    pipe = OriginationPipeline(params)
    side_rows, total_rows, ml_rows = [], [], []
    seen_season = None
    for g in games:
        game = dict(g)
        game.update(market_by_game.get(g["game_id"], {}))
        if g["season"] != seen_season:
            seen_season = g["season"]
            fresh = trailing_mu(games, seen_season)
            if fresh:
                pipe.model.mu = fresh
        pipe.begin_game()
        side = pipe.originate_side(game)
        if g["season"] < evaluate_from_season:
            pipe.finish_game(game, side)
            continue
        total = pipe.originate_total(side, game)
        ml = pipe.derive_moneyline(side, game)
        pipe.finish_game(game, side)
        side_rows.append(side)
        total_rows.append(total)
        ml_rows.append(ml)
    return {"side": side_rows, "total": total_rows, "moneyline": ml_rows,
            "audit": pipe.audit()}
