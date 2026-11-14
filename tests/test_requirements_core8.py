"""Tests for the eight bolded brief requirements implemented in this session:

    price snapshots (store), verified results feed, origination order,
    fair/market/difference columns, signal-vs-staking leaderboard split,
    replacement depth (in tools/build_replacement_depth.py, tested via data),
    official correlations (tools/build_correlations_official.py),
    demotion gate (engine/paper_gate.py).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import gates, leaderboard, origination, paper_gate, pricing, settlement  # noqa: E402


# ---------------------------------------------------------------- origination
class TestOrigination(unittest.TestCase):
    def test_order_is_side_total_moneyline(self):
        self.assertEqual(origination.ORIGINATION_ORDER, ("side", "total", "moneyline"))
        q = origination.origination_queue(["moneyline", "total", "side"])
        self.assertEqual(q, ["side", "total", "moneyline"])

    def test_unknown_market_raises_not_appends(self):
        with self.assertRaises(ValueError):
            origination.origination_queue(["side", "player_prop"])

    def test_aliases_map_but_exotics_do_not(self):
        self.assertEqual(origination.canonical_market("Spread"), "side")
        self.assertEqual(origination.canonical_market("ML"), "moneyline")
        with self.assertRaises(ValueError):
            origination.canonical_market("first touchdown scorer")

    def test_three_columns_stay_separate(self):
        rows = origination.originate([
            {"game_id": "g1", "market": "total", "selection": "over",
             "fair_line": None, "market_line": 44.5},
            {"game_id": "g1", "market": "side", "selection": "home",
             "fair_line": -3.0, "market_line": -3.5},
        ])
        # side originates first even though it was listed second
        self.assertEqual([r["market"] for r in rows], ["side", "total"])
        self.assertEqual(rows[0]["origination"], 1)
        side = rows[0]
        self.assertEqual(side["fair_line"], -3.0)     # published separately
        self.assertEqual(side["market_line"], -3.5)   # published separately
        self.assertEqual(side["difference"], -0.5)    # market - fair, line points
        total = rows[1]
        self.assertIsNone(total["difference"])        # never imputed

    def test_moneyline_difference_is_probability_points(self):
        rows = origination.originate([
            {"game_id": "g1", "market": "moneyline", "selection": "home",
             "fair_line": -150, "market_line": -120},
        ])
        d = rows[0]["difference"]
        expect = (pricing.implied_probability(-120) - pricing.implied_probability(-150))
        self.assertAlmostEqual(d, round(expect, 5), places=5)
        self.assertEqual(rows[0]["difference_unit"], "implied-probability points")


# ---------------------------------------------------------------- results feed
class TestResultsFeed(unittest.TestCase):
    def test_settlements_and_pushes(self):
        self.assertEqual(settlement.settle_side(24, 21, 1.5), "away")   # WAS 24 @ NYG 21, NYG +1.5: -3+1.5 < 0
        self.assertEqual(settlement.settle_side(21, 24, -3.0), "push")  # margin +3, spread -3
        self.assertEqual(settlement.settle_total(24, 21, 40.5), "over")
        self.assertEqual(settlement.settle_total(24, 21, 45.0), "push")
        self.assertEqual(settlement.settle_moneyline(24, 21), "away")
        self.assertEqual(settlement.settle_moneyline(20, 20), "push")

    def test_pnl_at_american_prices(self):
        self.assertAlmostEqual(settlement.settle_result("win", -110), 100 / 110, places=5)
        self.assertAlmostEqual(settlement.settle_result("win", 140), 1.4, places=5)
        self.assertEqual(settlement.settle_result("loss", -110), -1.0)
        self.assertEqual(settlement.settle_result("push", -110), 0.0)
        self.assertIsNone(settlement.settle_result("win", None))  # no price, no number

    def test_feed_rows_and_roi(self):
        games = [{
            "game_id": "2026_10_WAS_NYG", "gameday": "2026-11-12", "week": "10",
            "away": "WAS", "home": "NYG", "away_score": 24, "home_score": 21,
            "spread_home": 1.5, "total_line": 40.5,
            "ml_home": 120, "ml_away": -140,
            "home_spread_odds": -110, "over_odds": -110,
            "result_source_url": "https://www.nfl.com/standings/",
            "line_source_url": "https://github.com/nflverse/nfldata",
            "line_source_id": "S47",
        }]
        rows, summary = settlement.feed_rows(games)
        self.assertEqual([r["market"] for r in rows],
                         ["side", "total", "moneyline", "moneyline"])
        by = {(r["market"], r["selection"]): r for r in rows}
        self.assertEqual(by[("side", "home")]["outcome"], "loss")  # NYG +1.5: 21-24+1.5 = -1.5 < 0
        self.assertEqual(by[("total", "over")]["outcome"], "win")  # 45 > 40.5
        self.assertEqual(by[("moneyline", "home")]["outcome"], "loss")
        self.assertEqual(by[("moneyline", "away")]["outcome"], "win")
        r = settlement.roi(rows)
        self.assertEqual(r["n_priced"], 4)
        self.assertIsNotNone(r["roi_per_unit"])
        self.assertEqual(summary["pushes"], 0)

    def test_missing_price_is_reported_not_imputed(self):
        games = [{"game_id": "g", "gameday": "d", "week": "1", "away": "A", "home": "H",
                  "away_score": 10, "home_score": 10,
                  "spread_home": None, "total_line": None, "ml_home": None, "ml_away": None}]
        rows, summary = settlement.feed_rows(games)
        self.assertEqual(len(rows), 0)
        self.assertEqual(summary["missing_prices"]["side"], 2)
        self.assertEqual(settlement.roi(rows)["roi_per_unit"], None)


# ---------------------------------------------------------------- demotion gate
def _live_bets(n=300, clv=-0.02, stake=1.0, quoted=None, won_mod=2):
    out = []
    for i in range(n):
        won = (i % won_mod) == 0
        out.append({"game_id": f"g{i}", "season": 2024 + (i % 3), "team": f"t{i % 32}",
                    "price": -110, "stake": stake, "won": won,
                    "pnl": (100 / 110) if won else -1.0,
                    "clv": clv, "quoted_prob": quoted, "eval": "oos"})
    return out


class TestDemotion(unittest.TestCase):
    def test_negative_clv_window_demotes_d1(self):
        bets = _live_bets(300, clv=-0.02)
        d = paper_gate.evaluate_live(bets, paper_gate.DemotionConfig(decay_window=250))
        self.assertEqual(d.action, paper_gate.DEMOTE_TO_PAPER)
        self.assertTrue(any(r.startswith("D1") for r in d.reasons))

    def test_positive_clv_window_keeps_live(self):
        bets = _live_bets(300, clv=0.02)
        d = paper_gate.evaluate_live(bets, paper_gate.DemotionConfig(decay_window=250))
        self.assertEqual(d.action, paper_gate.KEEP_LIVE)

    def test_calibration_drift_demotes_d2(self):
        # quoted 80% but wins only half the time -> drift 0.30 > band 0.05
        bets = _live_bets(200, clv=0.02, quoted=0.8)
        d = paper_gate.evaluate_live(bets, paper_gate.DemotionConfig(decay_window=250))
        self.assertEqual(d.action, paper_gate.DEMOTE_TO_PAPER)
        self.assertTrue(any(r.startswith("D2") for r in d.reasons))

    def test_concentration_breach_demotes_d3(self):
        bets = _live_bets(300, clv=0.02)
        for b in bets:
            b["season"] = 2026
        d = paper_gate.evaluate_live(bets, paper_gate.DemotionConfig(decay_window=250))
        self.assertEqual(d.action, paper_gate.DEMOTE_TO_PAPER)
        self.assertTrue(any(r.startswith("D3") for r in d.reasons))

    def test_small_window_is_insufficient_not_pass(self):
        d = paper_gate.evaluate_live(_live_bets(10), paper_gate.DemotionConfig())
        self.assertEqual(d.action, paper_gate.INSUFFICIENT_DATA)

    def test_promotion_requires_all_pass(self):
        gates_order = ("G-1", "G-2", "G-2b", "G-3", "G-4", "G-5", "G-6")
        all_pass = [{"gate": g, "verdict": "PASS"} for g in gates_order]
        self.assertEqual(paper_gate.promotion_check(all_pass)["action"], "PROMOTE_TO_LIVE")
        with_blocked = all_pass[:-1] + [{"gate": "G-6", "verdict": "BLOCKED"}]
        self.assertEqual(paper_gate.promotion_check(with_blocked)["action"], "REMAIN_ON_PAPER")
        with_fail = [{"gate": g, "verdict": "FAIL" if g == "G-1" else "PASS"}
                     for g in gates_order]
        self.assertEqual(paper_gate.promotion_check(with_fail)["action"], "REMAIN_ON_PAPER")


# ------------------------------------------------- signal vs staking separation
class TestSignalStakingSplit(unittest.TestCase):
    def _entry(self, eid, bets, author="a"):
        return leaderboard.Entry(entry_id=eid, author=author, division="D1",
                                 bets=bets, code_blob=eid)

    def test_lucky_staking_cannot_mask_bad_signal(self):
        # 50% hit rate (below the 52.38% hurdle) but stakes concentrated on the
        # winners: staking ROI is spectacular, signal is bad.
        bets = []
        for i in range(200):
            won = (i % 2) == 0
            stake = 10.0 if won else 0.1
            bets.append({"game_id": f"g{i}", "season": 2026, "team": f"t{i % 32}",
                         "price": -110, "stake": stake, "won": won,
                         "pnl": (100 / 110) * stake if won else -stake,
                         "clv": -0.01, "modelled_edge": 0.03, "eval": "oos"})
        lucky = self._entry("lucky", bets, author="x")
        # honest entry: 55% hit rate, flat stakes
        honest_bets = []
        for i in range(1200):
            won = (i % 100) < 55
            honest_bets.append({"game_id": f"h{i}", "season": 2020 + (i % 5),
                                "team": f"t{i % 32}", "price": -110, "stake": 1.0,
                                "won": won, "pnl": (100 / 110) if won else -1.0,
                                "clv": 0.02, "modelled_edge": 0.03, "eval": "oos"})
        honest = self._entry("honest", honest_bets, author="y")
        table = leaderboard.rank([lucky, honest], gates.GateConfig())
        rows = {r["entry_id"]: r for r in table}
        # the lucky staking run LOOKS better on staking — that is the mask...
        self.assertGreater(rows["lucky"]["staking_score"], rows["honest"]["staking_score"])
        self.assertGreater(rows["honest"]["staking_score"], 0)
        # ...but the overall rank follows the signal, so it cannot win
        self.assertEqual(table[0]["entry_id"], "honest")
        self.assertFalse(rows["lucky"]["eligible"])
        self.assertIn("G-2", rows["lucky"]["failed_hard_gates"])
        self.assertEqual(rows["lucky"]["signal_score"], 0.0)

    def test_staking_and_signal_ranks_are_separate_columns(self):
        bets = []
        for i in range(1200):
            won = (i % 100) < 55
            bets.append({"game_id": f"g{i}", "season": 2020 + (i % 5), "team": f"t{i % 32}",
                         "price": -110, "stake": 1.0 + (i % 3), "won": won,
                         "pnl": (100 / 110) * (1.0 + (i % 3)) if won else -(1.0 + (i % 3)),
                         "clv": 0.02, "modelled_edge": 0.03, "eval": "oos"})
        table = leaderboard.rank([self._entry("e", bets)], gates.GateConfig())
        row = table[0]
        for key in ("signal_score", "staking_score", "signal_rank", "staking_rank",
                    "signal_lcb", "signal_clv_lcb", "staking_max_drawdown"):
            self.assertIn(key, row)


if __name__ == "__main__":
    unittest.main()
