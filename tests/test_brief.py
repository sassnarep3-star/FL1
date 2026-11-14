"""Hand-checkable tests for the session arena/685f958d-fl1 additions: origination order,
signal-versus-staking split, and the G-14 demotion gate. Every expectation is worked out by
hand in its comment, so a failure can be checked without running the code."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine import gates, leaderboard, originate as O  # noqa: E402


def _synthetic_games():
    # Ratings A=+6, B=0, C=-3, D=-3 with home-field +2 (non-neutral). Margins are exact,
    # so least squares must recover the rating differences and the home-field term.
    r = {"A": 6.0, "B": 0.0, "C": -3.0, "D": -3.0}
    hfa = 2.0
    pairs = [("A", "B"), ("B", "C"), ("C", "A"), ("D", "B"), ("A", "D"), ("B", "C"),
             ("C", "D"), ("D", "A"), ("B", "A"), ("C", "B"), ("A", "C"), ("D", "C")]
    games = []
    for i, (h, a) in enumerate(pairs, start=1):
        margin = r[h] - r[a] + hfa
        games.append(O.Game(i, a, h, 20, int(round(20 + margin))))
    return games


class TestOriginationOrder(unittest.TestCase):
    def test_fit_recovers_exact_ratings_and_home_field(self):
        m = O.fit(_synthetic_games())
        self.assertAlmostEqual(m.hfa, 2.0, places=3)
        self.assertAlmostEqual(m.ratings["A"] - m.ratings["B"], 6.0, places=3)
        self.assertAlmostEqual(m.ratings["B"] - m.ratings["C"], 3.0, places=3)

    def test_neutral_game_drops_home_field(self):
        m = O.fit(_synthetic_games())
        m.sigma = 10.0
        m.rates = O.scoring_rates(_synthetic_games())
        home = O.originate_game(m, "B", "A", neutral=False)
        neutral = O.originate_game(m, "B", "A", neutral=True)
        # margin = rating(A) - rating(B) + hfa = 6 + 2 = 8 ; neutral removes the 2
        self.assertAlmostEqual(home["home_margin_expected"], 8.0, places=2)
        self.assertAlmostEqual(neutral["home_margin_expected"], 6.0, places=2)

    def test_steps_are_recorded_in_the_mandated_order(self):
        m = O.fit(_synthetic_games())
        m.sigma = 10.0
        m.rates = O.scoring_rates(_synthetic_games())
        rec = O.originate_game(m, "C", "A", neutral=False)
        labels = [s.split(":")[0] for s in rec["order"]]
        self.assertEqual(labels, ["1 SIDE", "2 TOTAL", "3 MONEYLINE"])

    def test_moneyline_refuses_to_run_before_sigma_exists(self):
        m = O.fit(_synthetic_games())
        m.rates = O.scoring_rates(_synthetic_games())
        with self.assertRaises(ValueError):
            O.originate_game(m, "C", "A", neutral=False)

    def test_american_prices_and_rounding(self):
        self.assertEqual(O.american(0.5), -100)           # even money, favourite side by convention
        self.assertEqual(O.american(0.25), 300)           # 0.75/0.25 * 100
        self.assertEqual(O.american(0.75), -300)
        self.assertEqual(O.round_line(5.6), 5.5)          # 5.6/0.5 = 11.2 -> 11 -> 5.5
        self.assertEqual(O.round_line(5.8), 6.0)          # 11.6 -> 12 -> 6.0

    def test_wilson_interval_known_value(self):
        lo, hi = O.wilson(50, 100)
        self.assertAlmostEqual(lo, 0.4038, places=3)
        self.assertAlmostEqual(hi, 0.5962, places=3)
        self.assertEqual(O.wilson(0, 0), (None, None))

    def test_walk_forward_is_out_of_sample(self):
        # 36 games over 12 weeks (3 per week) so that weeks 8-12 can be scored with >= 20 training games.
        base = _synthetic_games()
        games = []
        for i, g in enumerate(base * 3):   # re-numbered: 3 games per week, weeks 1..12
            games.append(O.Game(1 + (i // 3), g.away, g.home, g.away_pts, g.home_pts, g.neutral))
        bt = O.walk_forward(games, first_week=8)
        self.assertTrue(bt, "expected scored rows once 20+ training games exist")
        for row in bt:
            train_n = sum(1 for g in games if g.week < row["week"])
            self.assertEqual(row["n_train"], train_n)          # trained on earlier weeks only
            self.assertLess(row["game"].week, row["week"] + 1)
            self.assertEqual(row["game"].week, row["week"])


class TestSignalVersusStaking(unittest.TestCase):
    def _entry(self, bets):
        return leaderboard.Entry(entry_id="E", author="x", division="d", bets=bets)

    def test_lucky_staking_cannot_mask_a_bad_signal(self):
        # 35 losses at 1 unit (-1 each) and 5 wins at 10 units (+9.1 each, price -110).
        # Signal (equal weight per bet): (5*0.91 - 35) / 40 = -0.76  -> negative.
        # Staking (dollar-weighted): (5*9.1 - 35) / (35*1 + 5*10) = 10.5 / 85 = +0.1235 -> positive.
        bets = [{"game_id": f"g{i}", "won": False, "pnl": -1.0, "stake": 1.0} for i in range(35)]
        bets += [{"game_id": f"w{i}", "won": True, "pnl": 9.1, "stake": 10.0} for i in range(5)]
        s = leaderboard.split_scores(self._entry(bets), n_boot=500)
        self.assertLess(s["signal_mean"], 0)
        self.assertAlmostEqual(s["staking_yield"], 10.5 / 85, places=4)
        self.assertTrue(s["masking_flag"])
        self.assertFalse(s["staking_reward_eligible"])

    def test_staking_reward_needs_both_signal_and_staking(self):
        bets = [{"game_id": f"g{i}", "won": (i % 10 < 7), "pnl": (0.91 if i % 10 < 7 else -1.0),
                 "stake": 1.0} for i in range(100)]
        s = leaderboard.split_scores(self._entry(bets), n_boot=500)
        # 70% wins at +0.91 and 30% losses at -1: mean +0.337 per unit, a clear positive signal
        self.assertGreater(s["signal_mean"], 0.3)
        self.assertFalse(s["masking_flag"])

    def test_signal_order_sorts_missing_bounds_last(self):
        rows = [{"entry_id": "a", "signal_lcb": None}, {"entry_id": "b", "signal_lcb": -0.2},
                {"entry_id": "c", "signal_lcb": 0.1}]
        ordered = leaderboard.signal_order(rows)
        self.assertEqual([r["entry_id"] for r in ordered], ["c", "b", "a"])
        self.assertIsNone(ordered[-1]["signal_rank"])


class TestDemotionGate(unittest.TestCase):
    def _bets(self, n, pnl_win, pnl_loss, p_win_idx, clv=None):
        out = []
        for i in range(n):
            won = i % 10 < p_win_idx
            b = {"game_id": f"g{i}", "won": won, "pnl": pnl_win if won else pnl_loss, "stake": 1.0}
            if clv is not None:
                b["clv"] = clv
            out.append(b)
        return out

    def test_negative_signal_over_window_demotes_to_paper(self):
        # 100 bets, every one -1 unit: LCB95 = -1 < 0
        bets = [{"game_id": f"g{i}", "won": False, "pnl": -1.0, "stake": 1.0} for i in range(100)]
        d = gates.demotion_decision(bets)
        self.assertEqual(d["decision"], "DEMOTE_TO_PAPER")
        self.assertEqual(d["state_after"], "PAPER")

    def test_fewer_than_window_bets_is_no_decision_not_a_demotion(self):
        bets = [{"game_id": f"g{i}", "won": False, "pnl": -1.0, "stake": 1.0} for i in range(99)]
        d = gates.demotion_decision(bets)
        self.assertEqual(d["decision"], "NO_DECISION_INSUFFICIENT_SAMPLE")
        self.assertEqual(d["state_after"], "LIVE")

    def test_positive_signal_keeps_live(self):
        bets = self._bets(100, 0.91, -1.0, 7)   # mean +0.337; LCB95 comfortably above 0
        d = gates.demotion_decision(bets)
        self.assertEqual(d["decision"], "KEEP_LIVE")

    def test_exposure_breach_demotes_immediately(self):
        bets = self._bets(100, 0.91, -1.0, 7)
        bets[50]["stake"] = 5.0                  # above the 2-unit cap
        d = gates.demotion_decision(bets)
        self.assertEqual(d["decision"], "DEMOTE_TO_PAPER")
        self.assertIn("R1", d["reasons"][0])

    def test_negative_clv_demotes_even_with_positive_signal(self):
        bets = self._bets(100, 0.91, -1.0, 7, clv=-0.02)
        d = gates.demotion_decision(bets)
        self.assertEqual(d["decision"], "DEMOTE_TO_PAPER")
        self.assertTrue(any(c[0] == "R4" and c[2] == "FAIL" for c in d["checks"]))

    def test_missing_clv_is_reported_not_imputed(self):
        bets = self._bets(100, 0.91, -1.0, 7)   # no clv key at all
        d = gates.demotion_decision(bets)
        r4 = [c for c in d["checks"] if c[0] == "R4"][0]
        self.assertTrue(r4[2].startswith("NOT EVALUATED"))

    def test_repromotion_needs_a_full_paper_window_with_positive_signal(self):
        short = self._bets(249, 0.91, -1.0, 7)
        self.assertEqual(gates.repromotion_decision(short)["decision"], "STAY_PAPER")
        full = self._bets(250, 0.91, -1.0, 7)
        self.assertEqual(gates.repromotion_decision(full)["decision"], "ELIGIBLE_TO_REPROMOTE")


if __name__ == "__main__":
    unittest.main()
