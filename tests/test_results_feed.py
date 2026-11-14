"""Tests for engine.results_settlement — the verified results feed and ROI contract."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.results_settlement import (  # noqa: E402
    Bet, FeedError, ProvenanceError, american_profit, load_feed, roi, settle,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = os.path.join(ROOT, "data", "results_feed.csv")

GOOD_HEADER = (
    "game_id,season,week,game_date,away_team,away_score,home_team,home_score,"
    "verified,verification_basis,official_game_url,source_ids"
)
GOOD_ROW = (
    "X1,2026,1,2026-01-01,AAA,10,BBB,20,row-level official,unit-test,"
    "https://www.nfl.com/games/x,S01"
)


class TestRealFeed(unittest.TestCase):
    def test_real_feed_loads(self):
        if not os.path.exists(FEED):
            self.skipTest("data/results_feed.csv not built")
        games = load_feed(FEED)
        self.assertGreaterEqual(len(games), 137)
        for g in games:
            self.assertEqual(g.verified, "row-level official")
            self.assertTrue(g.official_game_url.startswith("https://www.nfl.com/"))
            self.assertTrue(g.source_ids)

    def test_real_feed_unique_ids(self):
        if not os.path.exists(FEED):
            self.skipTest("data/results_feed.csv not built")
        games = load_feed(FEED)
        ids = [g.game_id for g in games]
        self.assertEqual(len(ids), len(set(ids)))


class TestLoaderContracts(unittest.TestCase):
    def _write(self, text):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        self.addCleanup(os.remove, path)
        return path

    def test_missing_column_rejected(self):
        path = self._write("game_id,season\nX,2026\n")
        with self.assertRaises(FeedError):
            load_feed(path)

    def test_empty_required_rejected(self):
        path = self._write(GOOD_HEADER + "\nX1,2026,1,2026-01-01,AAA,10,BBB,20,"
                           "row-level official,,https://www.nfl.com/games/x,S01\n")
        with self.assertRaises(FeedError):
            load_feed(path)

    def test_duplicate_rejected(self):
        path = self._write(GOOD_HEADER + "\n" + GOOD_ROW + "\n" + GOOD_ROW + "\n")
        with self.assertRaises(FeedError):
            load_feed(path)

    def test_unverified_rejected(self):
        bad = GOOD_ROW.replace("row-level official", "reconciled-only")
        path = self._write(GOOD_HEADER + "\n" + bad + "\n")
        with self.assertRaises(FeedError):
            load_feed(path)


class TestSettlement(unittest.TestCase):
    def setUp(self):
        path_fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(path_fd, "w", encoding="utf-8") as fh:
            fh.write(GOOD_HEADER + "\n" + GOOD_ROW + "\n")
        self.game = load_feed(path)[0]
        os.remove(path)

    def bet(self, **kw):
        base = dict(game_id="X1", market="side", selection="home",
                    price_american=-110, line=-3.0,
                    market_provenance="price-snapshot-store",
                    price_source_id="S99")
        base.update(kw)
        return Bet(**base)

    def test_side_home_cover(self):
        g = self.game  # home 20 - 10 = margin 10
        b = self.bet(line=-3.0)
        self.assertEqual(settle(b, g), "win")

    def test_side_push(self):
        b = self.bet(line=10.0)  # margin exactly 10
        self.assertEqual(settle(b, self.game), "push")

    def test_side_away(self):
        b = self.bet(selection="away", line=13.0)  # away +13 loses by 10 -> win
        self.assertEqual(settle(b, self.game), "win")

    def test_total(self):
        b = self.bet(market="total", selection="over", line=29.5)
        self.assertEqual(settle(b, self.game), "win")
        b2 = self.bet(market="total", selection="under", line=29.5)
        self.assertEqual(settle(b2, self.game), "loss")

    def test_ml(self):
        b = self.bet(market="ml", selection="home", line=None)
        self.assertEqual(settle(b, self.game), "win")

    def test_ml_tie_raises(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(GOOD_HEADER + "\n" +
                     GOOD_ROW.replace(",10,BBB,20,", ",10,BBB,10,") + "\n")
        g = load_feed(path)[0]
        os.remove(path)
        b = self.bet(market="ml", selection="home", line=None)
        with self.assertRaises(FeedError):
            settle(b, g)

    def test_missing_provenance_raises(self):
        b = self.bet(market_provenance="")
        with self.assertRaises(ProvenanceError):
            settle(b, self.game)

    def test_unknown_provenance_raises(self):
        b = self.bet(market_provenance="guesswork")
        with self.assertRaises(ProvenanceError):
            settle(b, self.game)

    def test_missing_price_source_raises(self):
        b = self.bet(price_source_id="")
        with self.assertRaises(ProvenanceError):
            settle(b, self.game)

    def test_roi_fail_closed(self):
        bets = [self.bet(), self.bet(market_provenance="")]
        with self.assertRaises(ProvenanceError):
            roi(bets, {"X1": self.game})

    def test_roi_math(self):
        win = self.bet(line=-3.0, price_american=-110)
        push = self.bet(line=10.0, price_american=-110)
        out = roi([win, push], {"X1": self.game})
        self.assertEqual(out["bets"], 2)
        self.assertEqual(out["settled"], 1)
        self.assertEqual(out["wins"], 1)
        self.assertAlmostEqual(out["profit"], round(american_profit(-110), 4))
        self.assertAlmostEqual(out["roi"], round(american_profit(-110), 4))
        self.assertEqual(out["provenance"], ["price-snapshot-store"])


if __name__ == "__main__":
    unittest.main()
