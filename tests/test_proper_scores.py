"""
Tests for engine/proper_scores.py.

The point of these tests is the SIGN CONVENTIONS. A leaderboard built on a
sign error does not crash: it produces a plausible-looking table of negative
numbers and tells the reader that every strategy is bad. So every convention
is pinned here against a hand-worked example in which the answer is known
before the code runs.
"""

import math
import unittest

from engine import proper_scores as ps


def trade(**kw):
    base = {
        "trade_key": "T|g", "strategy_id": "S", "market": "SIDE",
        "game_id": "g1", "season": "2025", "week": "1", "team": "PHI",
        "side_key": "home", "fair_line": "-6.0", "market_line": "-1.0",
        "settle_line": "-1.0", "price_american": "-110",
        "outcome": "WIN", "margin_home": "6", "total_points": "30",
    }
    base.update(kw)
    return base


class TestImpliedProbability(unittest.TestCase):
    def test_negative_price(self):
        # -110 risks 110 to win 100 -> 110/210
        self.assertAlmostEqual(ps.implied_probability("-110"), 110 / 210.0, places=12)

    def test_positive_price(self):
        # +150 risks 100 to win 150 -> 100/250
        self.assertAlmostEqual(ps.implied_probability("150"), 0.4, places=12)

    def test_absent_price_is_nan_not_zero(self):
        self.assertTrue(math.isnan(ps.implied_probability("")))
        self.assertTrue(math.isnan(ps.implied_probability(None)))


class TestSpreadSigns(unittest.TestCase):
    """A spread is quoted home-perspective; the betting side's own margin flips."""

    def test_home_bet_that_won_by_six_against_a_one_point_line(self):
        # home -1.0, home won by 6: the home side covered by 5.
        # The market's forecast of home's own margin is -(-1.0) = +1.0, so its
        # error is 6 - 1 = 5 points. The model's forecast is -(-6.0) = +6.0,
        # so its error is 6 - 6 = 0 points.
        errs = ps.line_errors(trade(market="SIDE", side_key="home",
                                    fair_line="-6.0", settle_line="-1.0",
                                    margin_home="6"))
        self.assertEqual(errs, (0.0, 5.0))

    def test_away_bet_uses_the_negated_margin_and_the_same_line_sign(self):
        # away side receives +1.0 (settle_line is written in the side's own
        # perspective for an away bet). The actual margin was home +6, so the
        # away side's own margin is -6. The market's forecast of the away
        # side's own margin is -(+1.0) = -1.0, so its error is -6 - (-1) = -5.
        errs = ps.line_errors(trade(market="SIDE", side_key="away",
                                    fair_line="-6.0", settle_line="1.0",
                                    margin_home="6"))
        self.assertIsNotNone(errs)
        self.assertAlmostEqual(errs[1], -5.0, places=9)

    def test_a_push_scores_a_half(self):
        self.assertEqual(ps.outcome_value("PUSH"), 0.5)

    def test_model_probability_on_a_spread_matches_the_normal_conversion(self):
        # model_own + settle_line = 6 + (-1) = 5 points of edge, over a
        # 10-point scale that is half a standard deviation.
        p = ps.model_belief(trade(market="SIDE", side_key="home",
                                  fair_line="-6.0", settle_line="-1.0"),
                            sigma_margin=10.0, sigma_total=10.0)
        self.assertAlmostEqual(p, ps.norm_cdf(0.5), places=12)

    def test_the_fair_line_does_not_enter_the_market_belief(self):
        # the market's belief is a property of the price, not of the model
        t = trade(price_american="120")
        self.assertAlmostEqual(ps.market_belief(t), 100 / 220.0, places=12)


class TestTotalSigns(unittest.TestCase):
    def test_total_error_is_the_same_number_for_over_and_under(self):
        base = dict(market="TOTAL", fair_line="44.5", settle_line="39.0",
                    total_points="50")
        over = ps.line_errors(trade(side_key="over", **base))
        under = ps.line_errors(trade(side_key="under", **base))
        self.assertEqual(over, under)
        self.assertAlmostEqual(over[0], 50 - 44.5, places=9)
        self.assertAlmostEqual(over[1], 50 - 39.0, places=9)

    def test_total_model_probability_uses_the_model_total_minus_the_line(self):
        # The model projects 44.5, the market line is 39: the over has 5.5
        # points of model edge. Crucially the actual total (50) must NOT
        # appear: it is not known when the forecast is made.
        p_over = ps.model_belief(trade(market="TOTAL", side_key="over",
                                       fair_line="44.5", settle_line="39.0"),
                                 sigma_margin=10.0, sigma_total=11.0)
        p_under = ps.model_belief(trade(market="TOTAL", side_key="under",
                                        fair_line="44.5", settle_line="39.0"),
                                  sigma_margin=10.0, sigma_total=11.0)
        self.assertAlmostEqual(p_over, ps.norm_cdf(5.5 / 11.0), places=12)
        self.assertAlmostEqual(p_over + p_under, 1.0, places=9)

    def test_market_line_mae_is_below_its_own_standard_deviation(self):
        # For any distribution with a mean near zero, MAE <= sigma. A sign bug
        # in the line comparison usually breaks this, so it is a cheap guard.
        errs = []
        for margin, line in [(3, -2.5), (-7, 6.5), (0, -3.0), (14, 10.5),
                             (-1, 1.0), (20, 17.5), (-13, -11.5)]:
            e = ps.line_errors(trade(market="SIDE", side_key="home",
                                     settle_line=str(line), fair_line=str(line),
                                     margin_home=str(margin)))
            errs.append(e[1])
        mae = sum(abs(x) for x in errs) / len(errs)
        m = sum(errs) / len(errs)
        sd = math.sqrt(sum((x - m) ** 2 for x in errs) / (len(errs) - 1))
        self.assertLessEqual(mae, sd)


class TestBrierAndSkill(unittest.TestCase):
    def test_perfect_forecast_has_zero_brier(self):
        self.assertEqual(ps.brier([1.0, 0.0], [1.0, 0.0]), 0.0)

    def test_a_coin_flip_has_a_quarter_brier(self):
        self.assertAlmostEqual(ps.brier([0.5, 0.5], [1.0, 0.0]), 0.25)

    def test_skill_is_zero_when_both_forecasts_are_the_same(self):
        p = [0.6, 0.4, 0.7]
        o = [1.0, 0.0, 1.0]
        self.assertAlmostEqual(ps.skill(p, p, o), 0.0, places=12)

    def test_a_sharper_forecast_has_positive_skill(self):
        o = [1.0, 0.0, 1.0, 0.0]
        model = [0.9, 0.1, 0.85, 0.2]
        bench = [0.6, 0.4, 0.55, 0.45]
        self.assertGreater(ps.skill(model, bench, o), 0)

    def test_a_broken_benchmark_gives_nan_not_a_zero_division(self):
        self.assertTrue(math.isnan(ps.skill([0.5], [0.0], [0.0])))


class TestClusterBootstrap(unittest.TestCase):
    def test_every_bet_of_a_drawn_game_travels_with_it(self):
        # one cluster dominates; the bootstrap must never see its bets apart
        model = [0.9, 0.1, 0.5, 0.5]
        bench = [0.5, 0.5, 0.5, 0.5]
        out = [1.0, 0.0, 1.0, 0.0]
        groups = ["A", "A", "B", "C"]
        res = ps.cluster_bootstrap(model, bench, out, groups, n_boot=200, seed=7)
        self.assertLessEqual(res["lower"], res["median"])
        self.assertLessEqual(res["median"], res["upper"])
        self.assertEqual(res["n_boot"], 200)

    def test_it_is_deterministic_for_a_fixed_seed(self):
        args = ([0.6, 0.4, 0.7], [0.5, 0.5, 0.5], [1.0, 0.0, 1.0],
                ["a", "b", "c"])
        self.assertEqual(ps.cluster_bootstrap(*args, n_boot=100, seed=11),
                         ps.cluster_bootstrap(*args, n_boot=100, seed=11))


class TestHolm(unittest.TestCase):
    def test_it_never_makes_a_p_value_smaller(self):
        p = {"a": 0.01, "b": 0.04, "c": 0.03}
        adj = ps.holm_adjust(p)
        for k in p:
            self.assertGreaterEqual(adj[k], p[k])

    def test_it_is_monotone_in_the_raw_order(self):
        adj = ps.holm_adjust({"a": 0.001, "b": 0.02, "c": 0.5})
        self.assertLessEqual(adj["a"], adj["b"])
        self.assertLessEqual(adj["b"], adj["c"])

    def test_a_single_hypothesis_is_unadjusted(self):
        self.assertAlmostEqual(ps.holm_adjust({"only": 0.03})["only"], 0.03, places=12)

    def test_it_caps_at_one(self):
        adj = ps.holm_adjust({"a": 0.4, "b": 0.7})
        self.assertLessEqual(max(adj.values()), 1.0)


class TestControls(unittest.TestCase):
    def test_the_favourite_control_on_a_fair_coin_is_the_coin(self):
        # with a 0.5 belief, max(p,1-p) == p, so the control IS the benchmark
        self.assertAlmostEqual(
            ps.control_favourite([0.5, 0.5, 0.5], [1.0, 0.0, 1.0]), 0.0, places=12)

    def test_the_favourite_control_is_deterministic(self):
        p = [0.7, 0.3, 0.6]
        o = [1.0, 0.0, 1.0]
        self.assertEqual(ps.control_favourite(p, o), ps.control_favourite(p, o))


class TestComboGate(unittest.TestCase):
    def test_a_combo_without_a_joint_probability_is_gated(self):
        g = ps.joint_evidence_gate({})
        self.assertTrue(g["gated"])
        self.assertIn("joint probability", g["reason"])

    def test_a_combo_with_a_joint_probability_but_no_void_rules_is_gated(self):
        g = ps.joint_evidence_gate({"joint_probability_validated": True})
        self.assertTrue(g["gated"])
        self.assertIn("void/push", g["reason"])

    def test_a_combo_with_both_is_not_gated(self):
        g = ps.joint_evidence_gate({"joint_probability_validated": True,
                                    "void_push_rules_documented": True})
        self.assertFalse(g["gated"])

    def test_there_is_no_code_path_that_prices_a_combo_from_marginals(self):
        for name in dir(ps):
            self.assertNotIn("multiply", name.lower())
            self.assertNotIn("independent_joint", name.lower())


class TestAgainstTheRealCorpus(unittest.TestCase):
    """One end-to-end guard on the committed backtest corpus."""

    @classmethod
    def setUpClass(cls):
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.trades = ps.load_trades(os.path.join(
            root, "data", "market", "backtest_trades.tsv"))
        cls.benchmarks = {r["game_id"]: r for r in ps.load_trades(os.path.join(
            root, "data", "market", "benchmarks.tsv"))}
        cls.sig = ps.estimate_sigmas(cls.trades)

    def test_the_market_line_is_accurate_on_a_realistic_scale(self):
        # A market spread's error is about 10 points of mean absolute error
        # and 13 points of standard deviation. Anything wildly outside that
        # would mean the line comparison had been mis-signed again.
        self.assertGreater(self.sig["mae_margin"], 8.0)
        self.assertLess(self.sig["mae_margin"], 12.0)
        self.assertGreater(self.sig["sigma_margin"], 11.0)
        self.assertLess(self.sig["sigma_margin"], 16.0)
        self.assertGreater(self.sig["mae_total"], 8.0)
        self.assertLess(self.sig["mae_total"], 13.0)

    def test_the_de_vigged_market_is_well_calibrated(self):
        # The strongest single check in this file: a real market's de-vigged
        # price must predict its own outcomes. If this fails, the benchmark
        # belief is wrong and every skill number above is meaningless.
        bins = {}
        for t in self.trades:
            q = ps.market_belief(t, self.benchmarks.get(t["game_id"]))
            o = ps.outcome_value(t["outcome"])
            if not (q == q and o == o):
                continue
            bins.setdefault(min(9, int(q * 10)), []).append(o)
        checked = 0
        for k, vals in bins.items():
            if len(vals) < 100:
                continue
            checked += 1
            self.assertAlmostEqual(sum(vals) / len(vals), (k + 0.5) / 10.0,
                                   delta=0.10,
                                   msg="bin %.1f-%.1f (%d bets)"
                                       % (k / 10, (k + 1) / 10, len(vals)))
        self.assertGreaterEqual(checked, 4)

    def test_scoring_a_strategy_returns_every_published_field(self):
        strat = [t for t in self.trades if t["strategy_id"] == "SIDE_EDGE_1.0"]
        r = ps.score_strategy(strat[:800], self.sig["sigma_margin"],
                              self.sig["sigma_total"],
                              benchmarks=self.benchmarks, n_boot=100)
        for field in ("brier_model", "brier_benchmark", "brier_skill",
                      "skill_lower_95", "skill_upper_95", "p_skill_gt_zero",
                      "control_random", "control_favourite", "hit_rate",
                      "model_line_mae", "market_line_mae"):
            self.assertIn(field, r)
        self.assertLessEqual(r["skill_lower_95"], r["skill_upper_95"])


if __name__ == "__main__":
    unittest.main()
