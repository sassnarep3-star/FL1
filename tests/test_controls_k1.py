"""K1 / R76 — control baselines (session arena/9fccbb0e-fl1).

Standard library only. The cross-checks recompute the controls from data/raw/games.csv with
plain csv arithmetic, never by calling scripts/strategy_lab.py, so a shared bug cannot make the
test and the published numbers agree with each other by construction.
"""
import csv
import json
import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import controls as C  # noqa: E402

GAMES = os.path.join(ROOT, "data", "raw", "games.csv")
OOS_FROM = 2020   # strategy_lab: seasons[int(21 * 0.7)] = seasons[14] = 2020
TRAIN_FROM = 2006  # strategy_lab TRAIN_START


def _f(x):
    """csv cell -> float or None (empty string = missing)."""
    if x is None or str(x).strip() == "":
        return None
    return float(x)


def _regular_games():
    with open(GAMES, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["game_type"] != "REG":
                continue
            if _f(r["home_score"]) is None or _f(r["away_score"]) is None:
                continue
            yield r


class TestPrimitives(unittest.TestCase):
    def test_coinflip_brier_is_exactly_quarter(self):
        out = C.brier([0.5] * 4, [1, 0, 1, 0])
        self.assertEqual(out["brier"], 0.25)
        self.assertEqual(out["n"], 4)

    def test_perfect_and_worst_forecasts(self):
        self.assertEqual(C.brier([1.0, 0.0], [1, 0])["brier"], 0.0)
        self.assertEqual(C.brier([1.0, 0.0], [0, 1])["brier"], 1.0)

    def test_interval_is_symmetric_and_brackets_mean(self):
        out = C.brier([0.4, 0.6, 0.5, 0.7], [0, 1, 1, 0])
        self.assertLessEqual(out["ci_low"], out["brier"])
        self.assertGreaterEqual(out["ci_high"], out["brier"])
        self.assertAlmostEqual(out["brier"] - out["ci_low"], out["ci_high"] - out["brier"], places=5)

    def test_empty_sample_is_blank_not_zero(self):
        out = C.brier([], [])
        self.assertIsNone(out["brier"])
        self.assertEqual(out["n"], 0)

    def test_rejects_bad_inputs(self):
        with self.assertRaises(ValueError):
            C.brier([1.2], [1])
        with self.assertRaises(ValueError):
            C.brier([0.5], [2])
        with self.assertRaises(ValueError):
            C.brier([0.5, 0.5], [1])

    def test_favourite_side_follows_verified_convention(self):
        self.assertEqual(C.favourite_side(3.5), "home")    # positive = home favourite
        self.assertEqual(C.favourite_side(-3.5), "away")
        with self.assertRaises(ValueError):
            C.favourite_side(0.0)                          # pick'em: no favourite
        with self.assertRaises(ValueError):
            C.favourite_side(float("nan"))

    def test_random_sides_pinned_seed_is_deterministic(self):
        a = C.random_sides(500)
        b = C.random_sides(500)
        self.assertEqual(a, b)
        self.assertEqual(C.CONTROL_SEED, 20261119)
        self.assertEqual(set(a), {"home", "away"})
        # a fair draw of 500 should not be lopsided beyond 5 sigma (sanity, not a claim)
        self.assertLess(abs(a.count("home") - 250), 5 * math.sqrt(125))

    def test_train_cover_rate(self):
        self.assertEqual(C.train_cover_rate([1, 0, 1, 1]), 0.75)
        with self.assertRaises(ValueError):
            C.train_cover_rate([])


class TestSignConvention(unittest.TestCase):
    """Evidence that spread_line > 0 means the HOME side is the favourite (see engine/controls.py)."""

    @classmethod
    def setUpClass(cls):
        cls.rows = [r for r in _regular_games()
                    if _f(r["spread_line"]) not in (None, 0.0)
                    and _f(r["home_moneyline"]) is not None and _f(r["away_moneyline"]) is not None]

    def test_moneyline_favourite_agrees_with_spread_sign(self):
        agree = sum(1 for r in self.rows
                    if (_f(r["home_moneyline"]) < _f(r["away_moneyline"])) == (_f(r["spread_line"]) > 0))
        rate = agree / len(self.rows)
        self.assertGreater(len(self.rows), 5000)
        self.assertGreaterEqual(rate, 0.99)   # measured 0.9944 on 5,198 games when K1 was written

    def test_spread_predicts_margin_in_home_favourite_direction(self):
        xs, ys = [], []
        for r in self.rows:
            xs.append(_f(r["spread_line"]))
            ys.append(_f(r["home_score"]) - _f(r["away_score"]))
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        vx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        vy = math.sqrt(sum((y - my) ** 2 for y in ys))
        self.assertGreater(cov / (vx * vy), 0.3)   # measured +0.43


class TestPublishedControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "data", "controls.csv"), encoding="utf-8", newline="") as fh:
            cls.controls = {r["control_id"]: r for r in csv.DictReader(fh)}
        with open(os.path.join(ROOT, "data", "leaderboard.csv"), encoding="utf-8", newline="") as fh:
            cls.lb = {r["strategy_id"]: r for r in csv.DictReader(fh)}
        with open(os.path.join(ROOT, "data", "controls.json"), encoding="utf-8") as fh:
            cls.meta = json.load(fh)

    def test_both_controls_present_in_leaderboard_and_controls_file(self):
        for cid in ("__CONTROL_RANDOM", "__CONTROL_FAVOURITE"):
            self.assertIn(cid, self.controls)
            self.assertIn(cid, self.lb)
        self.assertIn("__CONTROL_MARKET", self.lb)

    def test_random_brier_is_quarter_by_construction(self):
        r = self.controls["__CONTROL_RANDOM"]
        self.assertEqual(float(r["brier_oos"]), 0.25)
        self.assertEqual(r["forecast_p"], "0.5")

    def test_controls_agree_with_leaderboard_row_for_row(self):
        for cid, c in self.controls.items():
            lb = self.lb[cid]
            self.assertEqual(int(c["oos_settled"]), int(lb["oos_settled"]), cid)
            self.assertAlmostEqual(float(c["oos_roi"]), float(lb["oos_roi"]), places=4, msg=cid)

    def test_candidates_are_marked_not_evaluable(self):
        self.assertEqual(self.meta["candidates_scored"], 0)
        self.assertIn("NOT EVALUABLE", self.meta["candidate_status"])

    def test_favourite_forecast_recomputed_from_raw_games(self):
        """Independent recomputation: favourite cover rate on training seasons, stdlib only."""
        wins = losses = 0
        for r in _regular_games():
            season = int(r["season"])
            if season < TRAIN_FROM or season >= OOS_FROM:
                continue
            line = _f(r["spread_line"])
            if line is None or line == 0:
                continue
            fav_home = line > 0
            odds = _f(r["home_spread_odds"] if fav_home else r["away_spread_odds"])
            if odds is None:
                continue                       # strategy_lab drops bets with no odds for the side
            margin = _f(r["home_score"]) - _f(r["away_score"])
            d = (margin - line) if fav_home else (line - margin)   # favourite's cover margin
            if abs(d) < 1e-9:
                continue                       # push
            if d > 0:
                wins += 1
            else:
                losses += 1
        p = wins / (wins + losses)
        published = float(self.controls["__CONTROL_FAVOURITE"]["forecast_p"])
        self.assertAlmostEqual(p, published, places=5)
        self.assertEqual(int(self.controls["__CONTROL_FAVOURITE"]["train_settled"]), wins + losses)


if __name__ == "__main__":
    unittest.main()
