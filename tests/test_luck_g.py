#!/usr/bin/env python3
"""
test_luck_g.py — unit tests for engine/luck.py (session arena/dbf11de0-fl1).

Every expected value here is either a textbook constant or a figure that can be
checked with a calculator, so the tests are hand-verifiable rather than
"whatever the code happens to produce".

Run:  python3 -m unittest discover -s tests -q
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import luck  # noqa: E402


class TestNormal(unittest.TestCase):
    def test_cdf_at_zero(self):
        self.assertAlmostEqual(luck.norm_cdf(0.0), 0.5, places=9)

    def test_cdf_at_196(self):
        self.assertAlmostEqual(luck.norm_cdf(1.96), 0.9750, places=4)

    def test_cdf_at_neg_inf_is_zero(self):
        self.assertLess(luck.norm_cdf(-8), 1e-12)

    def test_z_crit_95(self):
        self.assertAlmostEqual(luck.z_crit(0.05), 1.959964, places=5)

    def test_z_crit_99(self):
        self.assertAlmostEqual(luck.z_crit(0.01), 2.575829, places=5)


class TestIntervals(unittest.TestCase):
    def test_wilson_50_of_100(self):
        lo, hi = luck.wilson_interval(50, 100)
        self.assertAlmostEqual(lo, 0.4038, places=3)
        self.assertAlmostEqual(hi, 0.5962, places=3)

    def test_wilson_is_inside_zero_one(self):
        lo, hi = luck.wilson_interval(0, 10)
        self.assertGreaterEqual(lo, 0.0)
        self.assertLessEqual(hi, 1.0)

    def test_wilson_empty(self):
        self.assertEqual(luck.wilson_interval(0, 0), (None, None))

    def test_luck_band_half_width_matches_hand_calc(self):
        lo, hi = luck.luck_band(100, 0.5)
        # 1.959964 * sqrt(.25/100) = 1.959964 * 0.05 = 0.0979982
        self.assertAlmostEqual(0.5 - lo, 0.0979982, places=6)
        self.assertAlmostEqual(hi - 0.5, 0.0979982, places=6)

    def test_luck_band_narrows_with_n(self):
        a = luck.luck_band(100, 0.5)
        b = luck.luck_band(400, 0.5)
        self.assertGreater(a[1] - a[0], b[1] - b[0])
        self.assertAlmostEqual((a[1] - a[0]) / (b[1] - b[0]), 2.0, places=6)

    def test_home_rate_of_137_games_is_inside_the_band(self):
        # 67 home wins in 137 official 2026 games (data/results.tsv)
        lo, hi = luck.luck_band(137, 0.5)
        self.assertLess(lo, 67 / 137)
        self.assertGreater(hi, 67 / 137)


class TestSizing(unittest.TestCase):
    def test_required_n_for_five_point_edge(self):
        # (1.959964 + 0.841621)^2 * .25 / .05^2 = 7.848932 * .25 / .0025
        self.assertEqual(luck.required_n(0.5, 0.05), 785)

    def test_required_n_scales_with_the_square_of_the_edge(self):
        self.assertEqual(luck.required_n(0.5, 0.10),
                         luck.required_n(0.5, 0.05) // 4 + 1)

    def test_required_n_rejects_a_zero_edge(self):
        self.assertIsNone(luck.required_n(0.5, 0.0))

    def test_a_season_is_not_enough(self):
        # 272 regular-season games; a 5pp edge needs far more than one season
        self.assertGreater(luck.required_n(0.5, 0.05), 272)

    def test_design_effect(self):
        self.assertAlmostEqual(luck.cluster_design_effect(2, 0.30), 1.30, places=9)
        self.assertAlmostEqual(luck.cluster_design_effect(1, 0.30), 1.00, places=9)

    def test_effective_n_halves_when_legs_are_perfectly_correlated(self):
        self.assertEqual(luck.effective_n(100, 2, 1.0), 50)

    def test_bonferroni(self):
        self.assertAlmostEqual(luck.bonferroni_alpha(0.05, 6), 0.05 / 6, places=12)

    def test_multiplicity_raises_the_sample(self):
        plain = luck.required_n(0.5, 0.05)
        adj = luck.required_n(0.5, 0.05, alpha=luck.bonferroni_alpha(0.05, 6))
        self.assertGreater(adj, plain)


class TestScoring(unittest.TestCase):
    def test_brier_of_a_coin_forecast(self):
        self.assertAlmostEqual(luck.brier([0.5, 0.5], [1, 0]), 0.25, places=12)

    def test_brier_zero_for_a_perfect_forecast(self):
        self.assertAlmostEqual(luck.brier([1.0, 0.0], [1, 0]), 0.0, places=12)

    def test_constant_brier_is_p_times_one_minus_p(self):
        outcomes = [1] * 67 + [0] * 70
        p = 67 / 137
        self.assertAlmostEqual(luck.constant_brier(p, outcomes),
                               p * (1 - p), places=12)

    def test_skill_score_of_the_benchmark_against_itself_is_zero(self):
        outcomes = [1, 0, 1, 0]
        f = [0.5] * 4
        self.assertAlmostEqual(luck.brier_skill_score(f, outcomes, f), 0.0,
                               places=12)

    def test_worse_than_the_benchmark_is_negative(self):
        self.assertLess(luck.brier_skill_score([0.1, 0.9], [1, 0], [0.5, 0.5]), 0)

    def test_binomial_two_sided(self):
        # 50 heads in 100 flips is utterly unremarkable
        self.assertGreater(luck.binomial_p_two_sided(50, 100, 0.5), 0.9)
        # 100 heads in 100 flips is not
        self.assertLess(luck.binomial_p_two_sided(100, 100, 0.5), 1e-25)
        # the observed 67 of 137 is unremarkable too
        self.assertGreater(luck.binomial_p_two_sided(67, 137, 0.5), 0.5)


if __name__ == "__main__":
    unittest.main()
