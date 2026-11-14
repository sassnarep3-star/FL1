"""Hand-checkable tests for the requirements sprint (R21-R28).

Every expectation is arithmetic a reviewer can do on paper, or a rule the
requirement states in words. The tests exist to prove the RULES hold —
blank means blank, order is side/total/moneyline, rank cannot be moved by
stakes, non-official sources cannot enter the correlation register — not to
fit any data.
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine import backtest, corr_official, demotion, fairline, snapshots  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestPriceSnapshotStore(unittest.TestCase):
    """R21: opening and closing numbers, provenance required, order mandated."""

    def test_market_order_is_side_total_moneyline(self):
        self.assertEqual(snapshots.MARKET_ORDER["SIDE"], 0)
        self.assertEqual(snapshots.MARKET_ORDER["TOTAL"], 1)
        self.assertEqual(snapshots.MARKET_ORDER["MONEYLINE"], 2)
        self.assertEqual(fairline.origination_order(), ("SIDE", "TOTAL", "MONEYLINE"))

    def test_price_without_provenance_fails_validation(self):
        row = snapshots.record(2026, 10, "g", "A", "H", "SIDE", "H", "HOME",
                               close_price=-3.0, close_source="S47",
                               close_provenance=snapshots.PROVENANCE_NONE)
        errors = snapshots.validate([row])
        self.assertTrue(any("no provenance" in e for e in errors))

    def test_price_without_source_fails_validation(self):
        row = snapshots.record(2026, 10, "g", "A", "H", "TOTAL", "GAME", "GAME",
                               close_price=44.0,
                               close_provenance=snapshots.PROVENANCE_THIRD_PARTY)
        errors = snapshots.validate([row])
        self.assertTrue(any("no source id" in e for e in errors))

    def test_official_pricing_claim_is_rejected(self):
        row = snapshots.record(2026, 10, "g", "A", "H", "SIDE", "H", "HOME",
                               close_price=-3.0, close_source="S01",
                               close_provenance=snapshots.PROVENANCE_OFFICIAL)
        errors = snapshots.validate([row])
        self.assertTrue(any("OFFICIAL" in e for e in errors))

    def test_blank_price_with_provenance_is_invalid(self):
        row = snapshots.record(2026, 10, "g", "A", "H", "MONEYLINE", "H", "HOME",
                               open_provenance=snapshots.PROVENANCE_THIRD_PARTY)
        errors = snapshots.validate([row])
        self.assertTrue(any("without a price" in e for e in errors))

    def test_settle_close_refuses_overwrite(self):
        row = snapshots.record(2026, 10, "g", "A", "H", "SIDE", "H", "HOME")
        snapshots.settle_close(row, -3.0, "2026-11-15", "S47",
                               snapshots.PROVENANCE_THIRD_PARTY)
        with self.assertRaises(ValueError):
            snapshots.settle_close(row, -3.5, "2026-11-15", "S47",
                                   snapshots.PROVENANCE_THIRD_PARTY)

    def test_store_file_passes_its_own_validation(self):
        with open(os.path.join(ROOT, "data", "price_snapshots.json"),
                  encoding="utf-8") as fh:
            store = json.load(fh)
        self.assertEqual(snapshots.validate(store["rows"]), [])
        # order: SIDE, TOTAL, MONEYLINE, MONEYLINE within each game
        per_game = {}
        for r in store["rows"]:
            per_game.setdefault(r["game_id"], []).append(r["market_type"])
        for gid, types in per_game.items():
            self.assertEqual(types, ["SIDE", "TOTAL", "MONEYLINE", "MONEYLINE"], gid)


class TestBacktest(unittest.TestCase):
    """R22/R25: settlement against the verified feed; signal split from staking."""

    FEED = [
        {"week": 1, "date": "2026-09-10", "away": "SF", "awayPts": 27,
         "home": "LAR", "homePts": 7},
        {"week": 1, "date": "2026-09-13", "away": "ARI", "awayPts": 26,
         "home": "LAC", "homePts": 14},
    ]

    def test_side_settlement_push_and_win(self):
        # SF 27 @ LAR 7: SF won by 20, so SF +3 wins comfortably.
        b = backtest.settle_bet({"week": 1, "away": "SF", "home": "LAR",
                                 "market_type": "SIDE", "side": "SF", "line": 3.0,
                                 "price": -110, "stake": 1.0}, 
                                backtest.index_results(self.FEED))
        self.assertIs(b["won"], True)
        self.assertAlmostEqual(b["pnl"], 0.909091, places=5)
        # LAR +3 at home loses by 20 -> LAR +3 loses.
        b = backtest.settle_bet({"week": 1, "away": "SF", "home": "LAR",
                                 "market_type": "SIDE", "side": "LAR", "line": 3.0,
                                 "price": -110, "stake": 1.0},
                                backtest.index_results(self.FEED))
        self.assertIs(b["won"], False)
        # ARI @ LAC won by exactly 12; ARI -12 pushes.
        b = backtest.settle_bet({"week": 1, "away": "ARI", "home": "LAC",
                                 "market_type": "SIDE", "side": "ARI", "line": -12.0,
                                 "price": -110, "stake": 1.0},
                                backtest.index_results(self.FEED))
        self.assertIsNone(b["won"])
        self.assertEqual(b["pnl"], 0.0)

    def test_total_and_moneyline_settlement(self):
        feed = backtest.index_results(self.FEED)
        # SF 27 @ LAR 7 -> 34 total: OVER 40.5 loses, UNDER 40.5 wins.
        over = backtest.settle_bet({"week": 1, "away": "SF", "home": "LAR",
                                    "market_type": "TOTAL", "side": "OVER",
                                    "line": 40.5, "price": -110, "stake": 1.0}, feed)
        self.assertIs(over["won"], False)
        under = backtest.settle_bet({"week": 1, "away": "SF", "home": "LAR",
                                     "market_type": "TOTAL", "side": "UNDER",
                                     "line": 40.5, "price": -110, "stake": 1.0}, feed)
        self.assertIs(under["won"], True)
        b = backtest.settle_bet({"week": 1, "away": "SF", "home": "LAR",
                                 "market_type": "MONEYLINE", "side": "LAR",
                                 "price": 150, "stake": 1.0}, feed)
        self.assertIs(b["won"], False)
        self.assertAlmostEqual(b["pnl"], -1.0)

    def test_unmatched_game_stays_unsettled_with_reason(self):
        b = backtest.settle_bet({"week": 9, "away": "XX", "home": "YY",
                                 "market_type": "SIDE", "side": "XX", "line": 0,
                                 "price": -110, "stake": 1.0},
                                backtest.index_results(self.FEED))
        self.assertIsNone(b["won"])
        self.assertIn("no verified result", b["settle_note"])

    def test_signal_split_ignores_stakes(self):
        # Two logs with IDENTICAL outcomes but wildly different stakes must
        # produce identical SIGNAL blocks and different STAKING blocks.
        base = [{"week": 1, "away": "SF", "home": "LAR", "market_type": "SIDE",
                 "side": "SF", "line": 3.0, "price": -110, "stake": s}
                for s in (1.0, 1.0, 1.0, 1.0)]
        big = [dict(b, stake=50.0) for b in base]
        feed = backtest.index_results(self.FEED)
        s1 = backtest.split_signal_staking([backtest.settle_bet(b, feed) for b in base])
        s2 = backtest.split_signal_staking([backtest.settle_bet(b, feed) for b in big])
        self.assertEqual(s1["signal"], s2["signal"])
        self.assertNotEqual(s1["staking"]["staked_units"],
                            s2["staking"]["staked_units"])

    def test_signal_hurdle_is_price_based(self):
        # flat ROI on -110 losses: -1 per bet
        settled = [{"won": False, "price": -110, "stake": 1.0, "pnl": -1.0}] * 10
        out = backtest.split_signal_staking(settled)
        self.assertAlmostEqual(out["signal"]["hit_rate"], 0.0)
        self.assertAlmostEqual(out["signal"]["breakeven_hit"], 110 / 210, places=5)

    def test_results_feed_reconciles_with_standings(self):
        with open(os.path.join(ROOT, "data", "results_feed.json"),
                  encoding="utf-8") as fh:
            feed = json.load(fh)
        self.assertEqual(feed["coverage"]["games"], 137)
        rec = {}
        for g in feed["rows"]:
            for team, pf, pa in ((g["home"], g["homePts"], g["awayPts"]),
                                 (g["away"], g["awayPts"], g["homePts"])):
                w, l, t, gpf, gpa = rec.get(team, (0, 0, 0, 0, 0))
                rec[team] = (w + (pf > pa), l + (pf < pa), t + (pf == pa),
                             gpf + pf, gpa + pa)
        path = os.path.join(ROOT, "data", "standings.tsv")
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 8:
                    continue
                abbr = parts[0]
                got = rec.get(abbr)
                if got is None:
                    continue
                self.assertEqual(got, (int(parts[1]), int(parts[2]), int(parts[3]),
                                       int(parts[5]), int(parts[6])), abbr)


class TestFairline(unittest.TestCase):
    """R23/R24: order mandated; difference = fair - market; blanks stay blank."""

    def test_difference_blank_never_zero(self):
        self.assertIsNone(fairline.difference(None, 3.0))
        self.assertIsNone(fairline.difference(-3.0, None))
        self.assertAlmostEqual(fairline.difference(-3.0, -2.5), -0.5)

    def test_fair_game_arithmetic(self):
        strength = {
            "H": {"games": 8, "pf": 200, "pa": 160, "ppg": 25.0, "oppg": 20.0,
                  "strength": 5.0},
            "A": {"games": 8, "pf": 160, "pa": 200, "ppg": 20.0, "oppg": 25.0,
                  "strength": -5.0},
        }
        fg = fairline.fair_game(strength, "H", "A", hfa=0.0, sd_margin=13.0,
                                season_games=8)
        # margin = 0 + (5 - -5)/2 = 5 -> home-view spread = -5.0
        self.assertAlmostEqual(fg["SIDE"]["fair"], -5.0)
        self.assertAlmostEqual(fg["TOTAL"]["fair"], 45.0)
        self.assertGreater(fg["MONEYLINE"]["fair"], 0.5)
        self.assertEqual([fg[m]["order"] for m in fairline.origination_order()],
                         [1, 2, 3])

    def test_line_board_columns_are_separate_and_ordered(self):
        with open(os.path.join(ROOT, "data", "line_board.json"),
                  encoding="utf-8") as fh:
            board = json.load(fh)
        for r in board["rows"]:
            self.assertIn("model_fair_line", r)
            self.assertIn("market_line", r)
            self.assertIn("difference", r)
        types = [r["market_type"] for r in board["rows"][:3]]
        self.assertEqual(types, ["SIDE", "TOTAL", "MONEYLINE"])
        # difference = fair - market wherever both exist
        for r in board["rows"]:
            if r["market_line"] is not None:
                self.assertAlmostEqual(
                    r["difference"],
                    round(r["model_fair_line"] - r["market_line"], 2))


class TestDemotion(unittest.TestCase):
    """R28: any trigger demotes; re-promotion needs a fresh qualifying sample."""

    @staticmethod
    def _log(wins_pattern, price=-110, stake=1.0, clv=None):
        out = []
        for i, win in enumerate(wins_pattern):
            pnl = (0.909091 if win else -1.0) * stake
            b = {"game_id": str(i), "season": 2026, "price": price,
                 "stake": stake, "won": win, "pnl": pnl}
            if clv is not None:
                b["clv"] = clv
            out.append(b)
        return out

    def test_signal_decay_demotes(self):
        # 100 bets at -110, 40% hit rate -> decisively below break-even
        log = self._log([i % 5 < 2 for i in range(100)])
        out = demotion.demotion_status(log)
        self.assertEqual(out["verdict"], demotion.VERDICT_DEMOTE)
        self.assertEqual(out["state"], demotion.STATE_PAPER)
        self.assertTrue(any(r.startswith("D1") for r in out["reasons"]))

    def test_drawdown_demotes(self):
        # alternating streak: 60 losses in a row then wins -> drawdown 60u
        log = self._log([False] * 60 + [True] * 60)
        out = demotion.demotion_status(log)
        self.assertEqual(out["verdict"], demotion.VERDICT_DEMOTE)
        self.assertTrue(any(r.startswith("D2") for r in out["reasons"]))

    def test_healthy_log_holds(self):
        # 60% hit rate at -110 over 120 bets: no trigger
        log = self._log([i % 5 < 3 for i in range(120)])
        out = demotion.demotion_status(log)
        self.assertEqual(out["verdict"], demotion.VERDICT_HOLD)
        self.assertEqual(out["state"], demotion.STATE_LIVE)

    def test_small_sample_blocks_verdict(self):
        out = demotion.demotion_status(self._log([False] * 20))
        self.assertEqual(out["rules"]["D1"]["status"], "BLOCKED")

    def test_clv_rot_demotes(self):
        log = self._log([i % 5 < 3 for i in range(120)], clv=-0.05)
        out = demotion.demotion_status(log)
        self.assertEqual(out["verdict"], demotion.VERDICT_DEMOTE)
        self.assertTrue(any(r.startswith("D3") for r in out["reasons"]))

    def test_repromotion_needs_fresh_sample_and_edge(self):
        small = demotion.repromotion_status(self._log([True] * 10))
        self.assertEqual(small["verdict"], demotion.VERDICT_HOLD)
        big = demotion.repromotion_status(self._log([True] * 300))
        self.assertEqual(big["verdict"], demotion.VERDICT_PROMOTE)
        weak = demotion.repromotion_status(self._log([i % 2 == 0 for i in range(300)]))
        self.assertEqual(weak["verdict"], demotion.VERDICT_HOLD)


class TestCorrOfficial(unittest.TestCase):
    """R27: official sources only, n published with every value."""

    def test_non_official_source_is_refused(self):
        with self.assertRaises(ValueError):
            corr_official.CorrRecord.build(
                "X", "x", "a", "b", [1, 2, 3], [2, 4, 6],
                ["S47"], {"S01", "S03", "S50"})

    def test_pearson_and_ci_arithmetic(self):
        r = corr_official.pearson([1, 2, 3, 4], [2, 4, 6, 8])
        self.assertAlmostEqual(r, 1.0)
        lo, hi = corr_official.fisher_ci(0.5, 32)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)

    def test_n_is_always_published(self):
        with open(os.path.join(ROOT, "data", "correlations_official.json"),
                  encoding="utf-8") as fh:
            reg = json.load(fh)
        for row in reg["rows"]:
            self.assertIn("n", row)
            self.assertGreaterEqual(row["n"], 1)
            if row["r"] is not None:
                self.assertIsNotNone(row["ci_low"], row["id"])
                self.assertGreaterEqual(row["n"], 3, row["id"])

    def test_every_row_official_only(self):
        with open(os.path.join(ROOT, "data", "correlations_official.json"),
                  encoding="utf-8") as fh:
            reg = json.load(fh)
        for row in reg["rows"]:
            self.assertTrue(set(row["sources"]) <= {"S01", "S02", "S03", "S04",
                                                    "S05", "S06", "S09", "S10",
                                                    "S49", "S50"}, row["id"])


class TestReplacementDepth(unittest.TestCase):
    """R26: the DEPTH of the replacement is tracked, not just the fact."""

    def test_rows_carry_replacement_depth(self):
        path = os.path.join(ROOT, "data", "replacement_depth.tsv")
        with open(path, encoding="utf-8") as fh:
            lines = [l.rstrip("\n").split("\t") for l in fh if l.strip()]
        head, body = lines[0], lines[1:]
        self.assertIn("replacement_depth", head)
        i = head.index("replacement_depth")
        self.assertTrue(body, "no replacement rows produced")
        for row in body:
            d = row[i]
            self.assertTrue(d == "" or d.isdigit(), row[:4])
            if d.isdigit():
                self.assertGreaterEqual(int(d), 1)


if __name__ == "__main__":
    unittest.main()
