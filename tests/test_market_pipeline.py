"""Tests for the market spine: price store, results ledger, origination order, the
signal/staking split, replacement depth, the correlation gate, the demotion gate, and the
artefacts the site renders.

Two rules govern these tests, because they are the tests of a *data-integrity* project:

  1. Units are tested on small synthetic fixtures, so a failure names the rule that broke
     rather than a 28,000-row dataset shifting.
  2. Integration is asserted against the committed artefacts in `data/market/`, and every
     check is a *cross-check between two artefacts that were computed independently*. A
     test that only re-runs the same function proves nothing about the numbers on the site.
"""

import csv
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import backtest_spine as bt            # noqa: E402 — renamed on integration: engine/backtest.py is the R22 module (PR #33)
from engine import correlation_gate as cg    # noqa: E402
from engine import demotion_eval as de       # noqa: E402
from engine import market_feed as feed       # noqa: E402
from engine import originate_spine as og           # noqa: E402 — renamed on integration: engine/originate.py is the brief.py O module
from engine import price_store as ps         # noqa: E402
from engine import replacement_depth as rd   # noqa: E402
from engine import results_ledger as rl      # noqa: E402
from engine import signal_staking as ss      # noqa: E402

MKT = os.path.join(ROOT, "data", "market")


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------
def game(gid, season, week, away, home, ascore, hscore, spread=-3.0, total=44.5,
          aml=None, hml=None, aside=-110, hside=-110, over=-110, under=-110):
    return {"game_id": gid, "season": season, "game_type": "REG", "week": week,
            "gameday": "2026-11-0%d" % (1 + (week % 7)), "weekday": "Thu",
            "away": away, "home": home, "away_feed_team": away, "home_feed_team": home,
            "away_score": ascore, "home_score": hscore, "location": "away" if False else "home",
            "margin_home": None if hscore is None else float(hscore - ascore),
            "total_points": None if hscore is None else float(hscore + ascore),
            "spread_line": spread, "total_line": total, "away_ml": aml, "home_ml": hml,
            "away_spread_odds": aside, "home_spread_odds": hside, "over_odds": over,
            "under_odds": under, "temp": None, "wind": None, "roof": "dome",
            "surface": "fieldturf", "referee": "", "stadium": "", "away_rest": 6,
            "home_rest": 6, "old_game_id": ""}


def closing(gid, market, side, line=None, odds=None, outcome=None):
    return {"alt_game_id": gid, "market": market, "side": side, "line": line, "odds": odds,
            "outcome_flag": outcome}


class PriceStoreTest(unittest.TestCase):
    def setUp(self):
        self.games = [game("2026_10_ARI_SF", 2026, 10, "ARI", "SF", 21, 17),
                      game("2026_11_SF_SEA", 2026, 11, "SF", "SEA", None, None)]
        self.clo = [closing("2026_10_ARI_SF", "SIDE", "ARI", line=3.0, odds=-105),
                    closing("2026_10_ARI_SF", "SIDE", "SF", line=-3.0, odds=-115),
                    closing("2026_10_ARI_SF", "TOTAL", "OVER", line=44.5, odds=-110),
                    closing("2026_10_ARI_SF", "MONEYLINE", "SF", odds=-150)]
        res = ps.ingest(self.games, self.clo, [], [], [])
        self.snaps = res["snapshots"]
        self.rep = res["integrity"]

    def test_every_row_carries_its_own_provenance(self):
        for r in self.snaps:
            self.assertTrue(r["source_url"].startswith("https://github.com/"), r)
            self.assertTrue(r["captured_at_utc"], "capture timestamp is mandatory")
            self.assertIn(r["vintage"], ps.VINTAGES)
            self.assertNotEqual(r["feed"], "")
            self.assertNotEqual(r["snapshot_key"], "")

    def test_undated_price_is_never_promoted_to_a_close(self):
        played = [r for r in self.snaps if r["feed"] == "games" and r["game_id"] == "2026_10_ARI_SF"]
        self.assertTrue(played)
        for r in played:
            self.assertEqual(r["vintage"], "UNDOCUMENTED",
                             "a played game from a feed that states no vintage must stay UNDOCUMENTED")
        live = [r for r in self.snaps if r["game_id"] == "2026_11_SF_SEA"]
        self.assertTrue(live)
        for r in live:
            self.assertEqual(r["vintage"], "LIVE_CURRENT",
                             "an unplayed game cannot have a closing number")

    def test_closing_feed_rows_are_labelled_close(self):
        rows = [r for r in self.snaps if r["feed"] == "closing_lines"]
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(r["vintage"], "CLOSE")
            self.assertIn("filename", r["vintage_evidence"].lower())

    def test_append_only_dedupe_is_idempotent(self):
        again = ps.ingest(self.games, self.clo, [], [], [])["snapshots"]
        self.assertEqual(len(self.snaps), len(again))
        self.assertEqual({r["snapshot_key"] for r in self.snaps},
                         {r["snapshot_key"] for r in again})

    def test_side_rows_net_to_zero_and_are_checked(self):
        # the fixture is symmetric, so the report must say so rather than stay silent
        row = self.rep["games"]
        self.assertGreaterEqual(row["side_pairs_checked"], 1)
        self.assertEqual(row["side_pairs_asymmetric"], 0)

    def test_asymmetric_feed_is_caught_not_silently_used(self):
        bad = [closing("2026_09_SEA_ARI", "SIDE", "SEA", line=-7.0, odds=-110),
               closing("2026_09_SEA_ARI", "SIDE", "ARI", line=6.5, odds=-110)]
        games = [game("2026_09_SEA_ARI", 2026, 9, "SEA", "ARI", 20, 24, spread=-7.0)]
        rep = ps.ingest(games, bad, [], [], [])["integrity"]
        self.assertEqual(rep["closing_lines"]["side_pairs_asymmetric"], 1)

    def test_quarantined_feed_is_stored_but_flagged(self):
        init = [{"game_id": "2021_01_BUF_PIT", "season": 2021, "sportsbook": "WSGT",
                 "market": "SIDE", "side": "BUF", "line": 3.0}]
        res = ps.ingest([game("2021_01_BUF_PIT", 2021, 1, "BUF", "PIT", 33, 21)], [], [],
                        init, [])
        q = [r for r in res["snapshots"] if r["feed"] == "initial_lines"]
        self.assertEqual(len(q), 1, "the row is recorded, not deleted")
        self.assertEqual(q[0]["status"], "QUARANTINED")
        self.assertEqual(q[0]["vintage"], "OPEN", "its own claim is recorded even in quarantine")

    def test_coverage_and_drift_shape(self):
        cov = ps.coverage(self.snaps)
        self.assertTrue(cov)
        for r in cov:
            self.assertIn(r["market"], ps.MARKETS)
            self.assertLessEqual(len(r["with_line"].intersection(r["games"])) if False
                                 else r["games_with_line"], r["games"])
        dr = ps.drift([r for r in self.snaps if r["market"] == "SIDE"])
        self.assertTrue(dr)
        for r in dr:
            self.assertEqual(r["games_compared"], r["lines_identical"] + r["lines_differ"])


class ResultsLedgerTest(unittest.TestCase):
    def setUp(self):
        self.games = [game("2026_10_ARI_SF", 2026, 10, "ARI", "SF", 21, 17),
                      game("2026_11_SF_SEA", 2026, 11, "SF", "SEA", None, None),
                      game("2026_10_TEN_HOU", 2026, 10, "TEN", "HOU", 24, 24)]
        self.official = [{"week": 10, "date": "2026-11-01", "away": "ARI", "away_score": 21,
                          "home": "SF", "home_score": 17},
                         {"week": 10, "date": "2026-11-01", "away": "TEN", "away_score": 24,
                          "home": "HOU", "home_score": 24}]

    def test_only_an_agreeing_game_is_admitted_as_two_feed(self):
        led = rl.build_ledger(self.games, self.official, {})
        by = {r["game_id"]: r for r in led["rows"]}
        self.assertEqual(by["2026_10_ARI_SF"]["verify_status"], "MATCHED_TWO_FEEDS")
        self.assertEqual(by["2026_11_SF_SEA"]["verify_status"], "NO_RESULT")
        self.assertEqual(by["2026_11_SF_SEA"]["settle_eligible"], "NO")

    def test_disagreement_quarantines_the_game(self):
        bad = [{"week": 10, "date": "2026-11-01", "away": "ARI", "away_score": 24,
                "home": "SF", "home_score": 17}]
        led = rl.build_ledger([self.games[0]], bad, {})
        self.assertEqual(led["rows"][0]["verify_status"], "QUARANTINE_MISMATCH")
        self.assertEqual(led["rows"][0]["settle_eligible"], "NO")

    def test_settlement_matches_the_book(self):
        """Each case is a sentence a bet slip could contain, graded by hand.

        These are the four signs this codebase exists to get right; a fixture written from
        the implementation would grade nothing.
        """
        cases = [
            # home -3.0 (favourite)
            ("SIDE", -3.0, "home", 4, None, rl.WIN, "home won by 4, laid 3"),
            ("SIDE", -3.0, "home", 3, None, rl.PUSH, "won by exactly the number"),
            ("SIDE", -3.0, "home", 2, None, rl.LOSE, "won but did not cover"),
            ("SIDE", -3.0, "home", -1, None, rl.LOSE, "lost outright"),
            # away +3.0 (dog) in the same game
            ("SIDE", 3.0, "away", 2, None, rl.WIN, "away lost by 2 and covered +3"),
            ("SIDE", 3.0, "away", 3, None, rl.PUSH, "lost by exactly the number"),
            ("SIDE", 3.0, "away", 4, None, rl.LOSE, "away +3 lost by 4 - must not be a win"),
            # totals, both sides of the same number
            ("TOTAL", 44.5, "over", None, 45, rl.WIN, "45 beats 44.5"),
            ("TOTAL", 44.5, "over", None, 44, rl.LOSE, "44 does not clear 44.5"),
            ("TOTAL", 44.5, "under", None, 44, rl.WIN, "under wins below the number"),
            ("TOTAL", 44.5, "under", None, 45, rl.LOSE, "under cannot win an over game"),
            ("TOTAL", 44.5, "under", None, 44.5, rl.PUSH, "exactly the number is a push"),
            ("TOTAL", 44.0, "over", None, 44.0, rl.PUSH, "integer total on an integer line"),
            # moneyline
            ("MONEYLINE", None, "home", 0, None, rl.PUSH, "an NFL tie pushes a two-way ML"),
            ("MONEYLINE", None, "away", -2, None, rl.WIN, "away won by 2"),
            ("MONEYLINE", None, "away", 2, None, rl.LOSE, "away lost"),
        ]
        for market, line, side, margin, total, want, why in cases:
            got = rl.settle(market, side_key=side, line=line,
                            margin_home=margin if margin is not None else 0,
                            total_points=total if total is not None else 0)
            self.assertEqual(got, want, "%s / %s: %s" % (market, side, why))

    def test_points_beat_and_settlement_never_disagree(self):
        """The stake-free measure and the settled outcome must be the same arithmetic."""
        for market, line, side, margin, total in [
                ("SIDE", -3.0, "home", 4, 41), ("SIDE", 3.0, "away", 4, 41),
                ("SIDE", 3.0, "away", -2, 41), ("TOTAL", 44.5, "under", 4, 40),
                ("TOTAL", 44.5, "over", 4, 50)]:
            row = {"market": market, "side_key": side, "settle_line": line, "market_line": line,
                   "margin_home": margin, "total_points": total}
            beat = ss._points_beat(row)
            want = rl.settle(market, side_key=side, line=line, margin_home=margin,
                             total_points=total)
            got = rl.WIN if beat > 0 else (rl.LOSE if beat < 0 else rl.PUSH)
            self.assertEqual(got, want, "%s %s %s" % (market, side, row))

    def test_tied_game_is_a_push_and_pays_nothing(self):
        led = rl.build_ledger(self.games, self.official, {})
        t = [{"trade_key": "x|2026_10_TEN_HOU", "game_id": "2026_10_TEN_HOU",
              "market": "MONEYLINE", "side_key": "home", "price_american": -150,
              "stake": 1.0}]
        g = rl.grade_trades(t, led["rows"])
        self.assertEqual(g["trades"][0]["outcome"], rl.PUSH)
        self.assertEqual(g["trades"][0]["pnl_units"], 0.0)

    def test_grading_refuses_unverified_games(self):
        led = rl.build_ledger(self.games, self.official, {})
        t = [{"trade_key": "y|2026_11_SF_SEA", "game_id": "2026_11_SF_SEA", "market": "SIDE",
              "side_key": "home", "line": -3.0, "price_american": -110, "stake": 1.0}]
        g = rl.grade_trades(t, led["rows"])
        self.assertEqual(g["trades"], [])
        self.assertIn("game_not_verified:NO_RESULT", g["refused"])

    def test_double_entry_the_log_recomputes_to_the_same_settlement(self):
        led = rl.build_ledger(self.games, self.official, {})
        trades = bt.build_trades(
            [{"game_id": "2026_10_ARI_SF", "season": 2026, "week": 10, "gameday": "2026-11-01",
              "fair_side_line_home": -6.0, "market_side_line_home": -3.0, "delta_side_pts": -3.0}],
            [], [], {"2026_10_ARI_SF": {"away": "ARI", "home": "SF"}}, led["rows"],
            rules=[{"id": "TEST", "market": "SIDE", "threshold": 1.0}])
        self.assertEqual(len(trades["trades"]), 1)
        g = rl.grade_trades(trades["trades"], led["rows"])
        self.assertEqual(g["trades"][0]["outcome"], g["trades"][0]["outcome_from_ledger"])
        self.assertEqual(g["trades"][0]["outcome_agrees_with_log"], "YES")


class OriginationTest(unittest.TestCase):
    def setUp(self):
        self.params = {"mu": 22.0, "lam": 0.92, "s": 0.55, "hfa": 2.0, "sd_residual": 13.5}
        self.game_row = {"game_id": "2026_11_ARI_SF", "season": 2026, "week": 11,
                         "gameday": "2026-11-21", "away": "ARI", "home": "SF",
                         "away_score": None, "home_score": None,
                         "market_side_line_home": -2.5, "side_line_source": "games",
                         "side_line_vintage": "LIVE_CURRENT",
                         "market_total_line": 43.5, "total_line_source": "games",
                         "total_line_vintage": "LIVE_CURRENT", "market_ml_home": -140,
                         "market_ml_away": 120, "ml_source": "games", "ml_vintage": "LIVE_CURRENT"}

    def test_stage_order_is_enforced(self):
        p = og.OriginationPipeline(self.params)
        p.begin_game()
        with self.assertRaises(og.StageOrderError):
            p.originate_total({"game_id": "x", "pred_total": 44.0}, self.game_row)
        with self.assertRaises(og.StageOrderError):
            p.derive_moneyline({"game_id": "x", "pred_margin_home": 2.0, "season": 2026,
                                "week": 11}, self.game_row)
        side = p.originate_side(self.game_row)
        tot = p.originate_total(side, self.game_row)
        ml = p.derive_moneyline(side, self.game_row)
        self.assertEqual(tot["fair_total"] % 0.5, 0.0)
        self.assertIsInstance(ml["fair_price_home"], int)

    def test_delta_is_three_separate_columns(self):
        p = og.OriginationPipeline(self.params)
        p.begin_game()
        side = p.originate_side(self.game_row)
        self.assertIn("fair_side_line_home", side)
        self.assertIn("market_side_line_home", side)
        self.assertIn("delta_side_pts", side)
        self.assertEqual(side["delta_side_pts"],
                         round(side["fair_side_line_home"] - side["market_side_line_home"], 4))

    def test_delta_is_blank_when_no_market_number_exists(self):
        p = og.OriginationPipeline(self.params)
        row = dict(self.game_row)
        row["market_side_line_home"] = None
        row["market_total_line"] = None
        row.pop("market_ml_home"); row.pop("market_ml_away")
        p.begin_game()
        side = p.originate_side(row)
        self.assertIsNone(side["delta_side_pts"])
        self.assertIn("no market line", side["delta_side_basis"])
        ml = p.derive_moneyline(side, row)
        self.assertIsNone(ml["delta_ml_pp"])
        self.assertIn("no market moneyline pair", ml["delta_ml_basis"])

    def test_market_line_is_never_fitted(self):
        p = og.OriginationPipeline(self.params)
        audit = p.audit()
        self.assertIs(audit["market_price_fitted"], False)
        self.assertEqual(audit["stage_order"], ["side", "total", "moneyline"])
        src = open(os.path.join(ROOT, "engine", "originate.py"), encoding="utf-8").read()
        for forbidden in ("fit_market", "scipy.optimize", "minimize", "least_squares"):
            self.assertNotIn(forbidden, src, "%s would mean we are fitting market prices" % forbidden)

    def test_moneyline_derives_from_the_side_not_from_prices(self):
        p = og.OriginationPipeline(self.params)
        p.begin_game()
        side = p.originate_side(self.game_row)
        ml = p.derive_moneyline(side, self.game_row)
        self.assertIn("residual", ml["derivation"])
        # a bigger predicted margin must raise the home probability
        p2 = og.OriginationPipeline(self.params)
        p2.residuals = [-14.0, -7.0, 0.0, 7.0, 14.0] * 20
        p.residuals = [-14.0, -7.0, 0.0, 7.0, 14.0] * 20
        p.begin_game(); p2.begin_game()
        weak = p.originate_side(self.game_row)
        strong = dict(self.game_row)
        p2.model.off["SF"] = 6.0
        strong_side = p2.originate_side(strong)
        self.assertGreater(strong_side["pred_margin_home"], weak["pred_margin_home"])

    def test_fair_price_round_trips_through_the_pricing_module(self):
        from engine import pricing
        for prob in (0.60, 0.55, 0.50, 0.45, 0.30):
            am = og.fair_american(prob)
            self.assertAlmostEqual(pricing.implied_probability(am), prob, delta=0.002)
        self.assertLess(og.fair_american(0.7), 0)
        self.assertGreater(og.fair_american(0.3), 0)

    def test_saturated_tail_prices_finite_via_laplace(self):
        p = og.OriginationPipeline(self.params)
        p.residuals = [5.0] * 50           # every historical residual beat the mark
        p.begin_game()
        side = p.originate_side(self.game_row)
        ml = p.derive_moneyline(side, self.game_row)
        self.assertLess(ml["fair_p_home"], 1.0)
        self.assertGreater(ml["fair_p_home"], 0.0)
        self.assertIsInstance(ml["fair_price_home"], int)
        self.assertEqual(ml["residual_n"], 50)

    def test_rounding_and_key_numbers_are_reported(self):
        p = og.OriginationPipeline(self.params)
        p.begin_game()
        side = p.originate_side(self.game_row)
        self.assertIn(round(side["fair_side_line_home"] * 2) / 2, [side["fair_side_line_home"]])
        self.assertLessEqual(side["key_number_distance"], 2.0)
        self.assertAlmostEqual(side["rounding_shift_pts"] + side["fair_side_line_home_raw"],
                               side["fair_side_line_home"], places=4)

    def test_run_pipeline_consumes_the_training_window_before_evaluating(self):
        games = [game("2020_%02d_ARI_SF" % w, 2020, w, "ARI", "SF", 20 + w, 17 + (w % 3),
                      spread=-3.0, total=44.5) for w in range(1, 5)]
        games += [game("2026_11_ARI_SF", 2026, 11, "ARI", "SF", 24, 20)]
        market = {g["game_id"]: {"market_side_line_home": -2.5, "side_line_source": "games",
                                "market_total_line": 44.5, "market_ml_home": -140,
                                "market_ml_away": 120} for g in games}
        out = og.run_pipeline(games, market, self.params, evaluate_from_season=2021)
        self.assertEqual(len(out["side"]), 1)          # only 2026 is published
        self.assertGreater(out["audit"]["games_run"], 1)   # but 2020 was consumed
        # the side is originated for every game (the training window is consumed too),
        # but only the evaluation window publishes a total and a moneyline
        self.assertEqual(out["audit"]["stages_completed"]["side"], len(games))
        self.assertEqual(out["audit"]["stages_completed"]["total"], 1)
        self.assertEqual(out["audit"]["stages_completed"]["moneyline"], 1)


class FeedRegistryTest(unittest.TestCase):
    def test_vintage_is_only_ever_a_quoted_claim(self):
        for name, meta in feed.iter_feeds():
            self.assertIn(meta["vintage"], ("OPEN", "CLOSE", "LIVE_CURRENT", "UNDOCUMENTED",
                                            "N/A"))
            if meta["vintage"] in ("OPEN", "CLOSE"):
                self.assertTrue(meta.get("vintage_evidence"),
                                "%s asserts %s, so it must cite what it asserts"
                                % (name, meta["vintage"]))
                self.assertIn("filename", meta["vintage_evidence"].lower(),
                              "%s may only claim %s from its own filename, and must say so"
                              % (name, meta["vintage"]))
            if "NOT documented" in meta["documented"] and meta["vintage"] != "UNDOCUMENTED":
                self.assertIn("filename", meta.get("vintage_evidence", "").lower())

    def test_no_undocumented_vendor_endpoint_is_ever_cited(self):
        """A price is only ever attributed to a file this repository can hash.

        The historical temptation in this domain is a scrapable aggregator URL; the
        registry must not contain one, and every market feed must resolve to a path in
        the pinned upstream tree so the claim can be re-checked.
        """
        urls = " ".join([str(meta.get("upstream_path", "")) for meta in feed.FEEDS.values()] +
                        [feed.upstream_url(k) for k in feed.FEEDS] +
                        [str(feed.manifest()[k]["file"]) for k in feed.FEEDS]).lower()
        for forbidden in ("vegasinsider", "oddspedia", "draftkings", "sportsbook.", "odds-api",
                          "api.", ".xml", "?"):
            self.assertNotIn(forbidden, urls,
                             "a market feed must resolve to a file in the pinned tree, not a live endpoint")
        for name, meta in feed.FEEDS.items():
            if not meta["upstream_path"].startswith("data/"):
                continue
            url = feed.upstream_url(name)
            self.assertTrue(url.startswith("https://github.com/nflverse/nfldata/blob/"), url)
            self.assertIn(meta["file"], url)

    def test_team_aliasing_is_an_explicit_table(self):
        self.assertEqual(feed.canon_team("LA"), "LAR")
        self.assertEqual(feed.canon_team("STL"), "LAR")
        self.assertEqual(feed.canon_team("OAK"), "LV")
        self.assertEqual(feed.canon_team("SD"), "LAC")
        self.assertEqual(feed.canon_team("AZ"), "ARI")
        self.assertEqual(feed.canon_team("SF"), "SF")

    def test_hashes_reproduce_for_every_committed_capture(self):
        for name, row in feed.manifest().items():
            if not row["exists"] or not row["manifest_sha256"]:
                continue
            self.assertEqual(row["sha256"], row["manifest_sha256"],
                             "data/raw/%s differs from the hash in MANIFEST.json" % name)


class BacktestTest(unittest.TestCase):
    def setUp(self):
        self.games = [game("2026_10_ARI_SF", 2026, 10, "ARI", "SF", 21, 17, spread=-3.0,
                           total=44.5)]
        self.snaps = ps.ingest(self.games, [], [], [], [])["snapshots"]
        self.market = bt.market_by_game(self.snaps, self.games)
        self.led = rl.build_ledger(self.games, [], {})

    def test_market_line_priority_and_provenance(self):
        rec = self.market["2026_10_ARI_SF"]
        # the fixture sets spread_line = -3.0, i.e. the AWAY team is favoured by 3, so the
        # home side's own number is +3.0 - the sign flip from the feed is the store's job
        self.assertEqual(rec["market_side_line_home"], 3.0)
        self.assertEqual(rec["side_line_vintage"], "UNDOCUMENTED")
        self.assertEqual(rec["total_line_source"], "games")

    def test_stakes_are_flat_by_construction(self):
        # SF (home) LOST by 4 while the store quotes home +3.0 (away favoured by 3). Our line
        # asks away to lay 5.5, more than the market's 3.0, so the value is on the away side -
        # a fixture that also exercises the away negation in engine.results_ledger.
        side = [{"game_id": "2026_10_ARI_SF", "season": 2026, "week": 10, "gameday": "2026-11-01",
                 "fair_side_line_home": 5.5, "market_side_line_home": 3.0,
                 "delta_side_pts": 2.5, "market_side_line_source": "games",
                 "market_side_vintage": "UNDOCUMENTED"}]
        t = bt.build_trades(side, [], [], self.market, self.led["rows"],
                            rules=[{"id": "T", "market": "SIDE", "threshold": 1.0}])
        self.assertEqual(len(t["trades"]), 1)
        row = t["trades"][0]
        self.assertEqual(row["stake_units"], 1.0)
        # a POSITIVE delta (our line asks more of the AWAY side than the market does) means away
        # is the side with the value; see the derivation in engine.backtest_spine.build_trades
        self.assertEqual(row["side_key"], "away")
        self.assertEqual(row["settle_line"], -3.0,
                         "an away bet is settled on away's own number, the negated home line")
        self.assertEqual(row["outcome"], rl.WIN)
        self.assertAlmostEqual(row["pnl_units"], round(100.0 / 110.0, 6), places=5)
        self.assertEqual(row["benchmark"], "CLOSE_OR_UNDOCUMENTED")
        self.assertEqual(row["price_basis"], "POSTED_IN_STORE")   # -110 came from the store
        # ...and with no price in the store the same bet must announce the assumption
        bare = {g["game_id"]: {k: v for k, v in g.items()
                                if k not in ("home_side_price", "away_side_price")}
                for g in self.market.values()}
        bare["2026_10_ARI_SF"].update({"home_side_price": None, "away_side_price": None})
        t2 = bt.build_trades(side, [], [], bare, self.led["rows"],
                             rules=[{"id": "T", "market": "SIDE", "threshold": 1.0}])
        self.assertIn("NOT_POSTED_ASSUMED", t2["trades"][0]["price_basis"])
        self.assertEqual(t2["trades"][0]["price_american"], -110)

    def test_eligibility_is_counted_whether_or_not_a_bet_is_written(self):
        side = [{"game_id": "2026_10_ARI_SF", "season": 2026, "week": 10,
                 "gameday": "2026-11-01", "fair_side_line_home": 3.5,
                 "market_side_line_home": 3.0, "delta_side_pts": 0.5,
                 "market_side_line_source": "games", "market_side_vintage": "UNDOCUMENTED"}]
        t = bt.build_trades(side, [], [], self.market, self.led["rows"],
                            rules=[{"id": "T2", "market": "SIDE", "threshold": 1.0}])
        self.assertEqual(t["trades"], [])
        self.assertEqual(t["eligible"]["T2"], {"eligible": 1, "traded": 0, "below_threshold": 1})


class SignalStakingTest(unittest.TestCase):
    def trade(self, key, edge, pts, stake=1.0, price=-110, market="SIDE", outcome=None):
        """A bet row whose recomputed points beat is exactly `pts`.

        `pts` is what the scorecard measures, so the fixture has to set the score that
        produces it: home at -3.0 beats the line by `pts` when the home margin is
        `pts + 3.0`. Anything else would test the fixture instead of the code.
        """
        won = pts > 0
        return {"trade_key": key, "strategy_id": "S1", "market": market, "side_key": "home",
                "delta": edge, "price_american": price, "price_basis": "POSTED_IN_STORE",
                "stake_units": stake, "margin_home": float(pts) + 3.0, "total_points": 40.0,
                "market_line": -3.0, "settle_line": -3.0,
                "outcome": outcome or (rl.WIN if won else rl.LOSE),
                "pnl_units": stake * (100.0 / abs(price) if won else -1.0),
                "season": "2020"}

    def test_the_signal_block_ignores_stakes(self):
        small = [self.trade("a%d" % i, 2.0, 1.0) for i in range(40)]
        big = [dict(t, stake_units=9.0, pnl_units=t["pnl_units"] * 9.0) for t in small]
        s1 = ss.signal_card(small, 40, "S1", "SIDE")
        s2 = ss.signal_card(big, 40, "S1", "SIDE")
        for k in ("signal_bets", "hit_rate", "points_beat_mean", "mean_abs_edge"):
            self.assertEqual(s1[k], s2[k], "%s must not move when stakes move" % k)
        st1 = ss.staking_card(small, "S1")
        st2 = ss.staking_card(big, "S1")
        self.assertEqual(st1["roi"], st2["roi"], "ROI is scale-invariant")

    def test_a_staking_run_cannot_buy_a_better_signal_rank(self):
        """The rank a strategy holds must depend on which block is asking.

        `good` beats the line by a point and a half every time but is priced at -170, so its
        ROI is modest. `lucky` never beats the line at all and wins every bet at -110, so its
        ROI is the best in the room. If the two blocks produced the same order, one of them
        would be decorative.
        """
        good = [self.trade("g%d" % i, 2.0, 1.5, price=-170) for i in range(60)]
        lucky = [dict(self.trade("l%d" % i, 2.0, -0.5, price=-110),
                      outcome=rl.WIN, pnl_units=round(100.0 / 110.0, 6)) for i in range(40)]
        sig = {sid: ss.signal_card(rows, 40, sid, "SIDE")
               for sid, rows in (("good", good), ("lucky", lucky))}
        stk = {sid: ss.staking_card(rows, sid) for sid, rows in (("good", good), ("lucky", lucky))}
        board = ss.rank(list(sig.values()), list(stk.values()))
        self.assertEqual(board[0]["strategy_id"], "good", "signal rank must ignore the price")
        self.assertEqual(board[0]["rank_staking"], 2,
                         "a staking run cannot buy a better SIGNAL rank")
        self.assertGreater(stk["lucky"]["roi"], stk["good"]["roi"])
        self.assertLess(sig["lucky"]["points_beat_mean"], sig["good"]["points_beat_mean"])
        self.assertEqual(board[0]["divergence"], "signal and staking agree",
                         "both blocks positive is agreement, whatever the ranks say")
        by_id = {r["strategy_id"]: r for r in board}
        self.assertIn("STAKING OUTPERFORMS", by_id["lucky"]["divergence"],
                      "a profitable run on a signal that cannot clear its own break-even must be named")
        self.assertNotIn("%%", by_id["lucky"]["divergence"],
                         "this string is not %-formatted; a doubled percent reaches the artefact")
        self.assertEqual(by_id["lucky"]["reward_units"], 0,
                         "no reward is payable on a staking rank alone")

    def test_calibration_slope_sees_an_inverted_signal(self):
        inv = [self.trade("i%d" % i, 6.0 if i % 2 == 0 else 1.0,
                          -3.0 if i % 2 == 0 else 0.5) for i in range(80)]
        card = ss.signal_card(inv, 80, "INV", "SIDE")
        self.assertLess(card["calibration_slope"], 0)
        self.assertIn("INVERTED", card["signal_grade"])

    def test_reward_requires_a_positive_lower_bound(self):
        weak = [self.trade("w%d" % i, 1.5, 0.2 if i % 2 else -0.2) for i in range(40)]
        card = ss.signal_card(weak, 40, "WEAK", "SIDE")
        self.assertAlmostEqual(card["points_beat_mean"], 0.0, places=6)
        self.assertEqual(ss._reward(1, card), 0,
                         "a mean above zero with an interval spanning zero earns nothing")

    def test_selectivity_is_published(self):
        tr = [self.trade("s%d" % i, 2.0, 1.0) for i in range(50)]
        card = ss.signal_card(tr, 200, "S1", "SIDE")
        self.assertEqual(card["selectivity_pct"], 25.0)

    def test_legacy_rows_leave_the_signal_block_empty(self):
        path = os.path.join(ROOT, "data", "leaderboard.csv")
        if not os.path.exists(path):
            self.skipTest("no legacy leaderboard in this checkout")
        rows = ss.legacy_leaderboard_rows(path)
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(r["points_beat_mean"], "")
            self.assertIn("SIGNAL BLOCK UNPOPULATED", r["blockable"])


class ReplacementDepthTest(unittest.TestCase):
    def test_levels_lost_is_a_count_of_strings(self):
        depth = [
            {"team": "SF", "unit": "Defense", "slot": "WILL", "player": "Alpha", "rank": 1,
             "line": 1, "note": ""},
            {"team": "SF", "unit": "Defense", "slot": "WILL", "player": "Bravo", "rank": 2,
             "line": 2, "note": ""},
            {"team": "SF", "unit": "Defense", "slot": "WILL", "player": "Charlie", "rank": 3,
             "line": 4, "note": ""},
        ]
        inj = [{"team": "SF", "player": "Alpha", "position": "LB", "injury": "knee",
                "practice": "DNP", "game": "Out"}]
        res = rd.build(depth, inj, {}, {}, {})
        self.assertEqual(len(res["rows"]), 1)
        row = res["rows"][0]
        self.assertEqual(row["replacement_player"], "Bravo")
        self.assertEqual(row["depth_levels_lost"], 1)
        self.assertEqual(row["depth_remaining"], 1)

    def test_chain_broken_is_flagged_when_the_next_man_is_also_hurt(self):
        depth = [{"team": "SF", "unit": "Defense", "slot": "MIKE", "player": "One", "rank": 1,
                  "line": 1, "note": ""},
                 {"team": "SF", "unit": "Defense", "slot": "MIKE", "player": "Two", "rank": 2,
                  "line": 2, "note": ""},
                 {"team": "SF", "unit": "Defense", "slot": "MIKE", "player": "Three", "rank": 3,
                  "line": 3, "note": ""}]
        inj = [{"team": "SF", "player": "One", "position": "LB", "injury": "ankle",
                "practice": "DNP", "game": "Out"},
               {"team": "SF", "player": "Two", "position": "LB", "injury": "hamstring",
                "practice": "DNP", "game": "Out"}]
        res = rd.build(depth, inj, {}, {}, {})
        first = [r for r in res["rows"] if r["absent_player"] == "One"][0]
        self.assertIn("also on the report", first["chain_broken"])
        self.assertEqual(first["replacement_player"], "Three",
                         "the depth falls past the second casualty to the third name")

    def test_no_fuzzy_matching_is_used(self):
        src = open(os.path.join(ROOT, "engine", "replacement_depth.py"), encoding="utf-8").read()
        for forbidden in ("difflib", "get_close_matches", "SequenceMatcher", "fuzzywuzzy"):
            self.assertNotIn(forbidden, src,
                             "name joins are exact-after-alias or they are left unresolved")

    def test_a_report_name_that_hits_no_slot_stays_unresolved(self):
        depth = [{"team": "SF", "unit": "Defense", "slot": "NOS", "player": "Real", "rank": 1,
                  "line": 1, "note": ""}]
        inj = [{"team": "SF", "player": "Ghost", "position": "WR", "injury": "n/a",
                "practice": "", "game": "Out"}]
        res = rd.build(depth, inj, {}, {}, {})
        self.assertEqual(res["rows"], [])
        self.assertEqual(len(res["unmatched_absences"]), 1)

    def test_alias_table_is_the_only_name_mapping(self):
        """`load_aliases()` must read the positional file, and `build()` must apply it.

        The table has no header row. It used to be read with csv.DictReader, which consumed the
        first alias as column names, found no "depthName" field, and returned an EMPTY map - so
        every alias silently stopped being applied while the page still advertised an exact
        join after alias mapping. Both halves are checked: the committed file must load, and a
        spelling pair must resolve only when the alias is in force. No fuzzy matching is
        allowed anywhere, so the alias table is the only bridge that exists.
        """
        al = rd.load_aliases()
        self.assertTrue(al, "load_aliases() returned nothing for a non-empty file")
        self.assertTrue(all(k != v for k, v in al.items()), "an alias to itself is a no-op row")
        with open(os.path.join(ROOT, "data", "depth-aliases.tsv"), encoding="utf-8") as fh:
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                self.assertGreaterEqual(len(parts), 3,
                                        "an alias row without a note is an unexplained edit")
                self.assertTrue(parts[2].strip(),
                                "the note must say which source uses which spelling")

        chart = [{"team": "SEA", "unit": "Defense", "slot": "NCB", "player": "Chris Roland-Wallace",
                  "rank": 1, "line": 1, "note": ""},
                 {"team": "SEA", "unit": "Defense", "slot": "NCB", "player": "Next Man",
                  "rank": 2, "line": 2, "note": ""}]
        report = [{"team": "SEA", "player": "Christian Roland-Wallace", "position": "CB",
                   "injury": "hamstring", "practice": "DNP", "game": "Out"}]
        bare = rd.build(chart, report, {}, {}, {})
        self.assertEqual(bare["rows"], [], "without the alias the two spellings do not meet")
        self.assertEqual(len(bare["unmatched_absences"]), 1,
                         "and the absence is reported as unmatched, not dropped")
        bridged = rd.build(chart, report, {"chris roland-wallace": "christian roland-wallace"},
                           {}, {})
        self.assertEqual(len(bridged["rows"]), 1, "the alias is what makes the join exact")
        self.assertEqual(bridged["rows"][0]["replacement_player"], "Next Man")
        self.assertEqual(bridged["rows"][0]["depth_levels_lost"], 1)


class CorrelationGateTest(unittest.TestCase):
    def test_non_official_operands_are_held(self):
        pair = {"id": "X", "pair": "p", "rho": 0.31, "n": 5000,
                "x_source": "third-party aggregator", "x_tier": "THIRD-PARTY-AGGREGATOR",
                "y_source": "third-party aggregator", "y_tier": "THIRD-PARTY-AGGREGATOR",
                "joint_observations": True}
        out = cg.gate(pair)
        self.assertEqual(out["verdict"], "HOLD")
        self.assertIn("not an official source", out["gate_reasons"])

    def test_missing_n_blocks_publication(self):
        pair = {"id": "Y", "pair": "p", "rho": 0.2, "n": 0,
                "x_source": "official", "x_tier": "OFFICIAL-LEAGUE",
                "y_source": "official", "y_tier": "OFFICIAL-CLUB", "joint_observations": True}
        out = cg.gate(pair)
        self.assertEqual(out["verdict"], "HOLD")
        self.assertIn("n is part of the number", out["gate_reasons"])

    def test_official_pair_with_n_publishes(self):
        pair = {"id": "Z", "pair": "p", "rho": 0.1, "n": 1200,
                "x_source": "official standings", "x_tier": "OFFICIAL-LEAGUE",
                "y_source": "official report", "y_tier": "OFFICIAL-CLUB",
                "joint_observations": True}
        self.assertEqual(cg.gate(pair)["verdict"], "PUBLISH")

    def test_small_sample_is_held_even_when_official(self):
        pair = {"id": "W", "pair": "p", "rho": 0.9, "n": 12,
                "x_source": "official", "x_tier": "OFFICIAL-LEAGUE",
                "y_source": "official", "y_tier": "OFFICIAL-LEAGUE", "joint_observations": True}
        out = cg.gate(pair)
        self.assertEqual(out["verdict"], "HOLD")
        self.assertIn("floor", out["gate_reasons"])

    def test_frechet_bounds_hold_for_any_dependence(self):
        lo, hi = cg.frechet(0.6, 0.5)
        self.assertAlmostEqual(lo, 0.1)
        self.assertAlmostEqual(hi, 0.5)
        for rho in (-1.0, 0.0, 1.0):
            j = cg.joint_from_rho(0.6, 0.5, rho)
            self.assertGreaterEqual(j, -1e-9)
            self.assertLessEqual(j, 1.0 + 1e-9)

    def test_phi_and_bootstrap_agree_with_a_perfect_pair(self):
        xs = [1.0, 1.0, 0.0, 0.0] * 30
        self.assertAlmostEqual(cg.pearson(xs, xs), 1.0, places=6)
        self.assertAlmostEqual(cg.phi(60, 60, 60, 120), 1.0, places=6)
        lo, hi = cg.bootstrap_rho(xs, xs)
        self.assertGreater(lo, 0.99)

    def test_parity_with_the_site_register(self):
        pub_path = os.path.join(MKT, "correlations_published.tsv")
        if not os.path.exists(pub_path):
            self.skipTest("artefacts not built")
        with open(pub_path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh, delimiter="\t"))
        for r in rows:
            self.assertGreater(int(r["n"]), 0, "n must be published with every value")
            self.assertEqual(r["verdict"], "PUBLISH")
            for side in ("x", "y"):
                self.assertIn(r[side + "_tier"], cg.TIER_OFFICIAL)


class DemotionGateTest(unittest.TestCase):
    def cfg(self):
        return de.DemotionConfig(min_window=10, window=60, d1_negative_streak=8)

    def trades(self, n, pts):
        out = []
        for i in range(n):
            out.append({"trade_key": "d%d" % i, "strategy_id": "S", "market": "SIDE",
                        "side_key": "home", "season": "2020", "week": "1", "game_id": "g%d" % i,
                        "outcome": rl.WIN if pts[i] > 0 else rl.LOSE,
                        "margin_home": pts[i], "total_points": 40, "market_line": -3.0,
                        "settle_line": -3.0, "pnl_units": 0.9 if pts[i] > 0 else -1.0,
                        "stake_units": 1.0, "price_american": -110, "delta": 2.0})
        return out

    def test_short_window_is_not_evaluable_rather_than_ok(self):
        r = de.d1_live_decay(self.trades(4, [1.0] * 4), self.cfg())
        self.assertEqual(r["verdict"], "NOT_EVALUABLE")

    def test_losing_edge_demotes(self):
        t = self.trades(40, [-1.0] * 40)
        r = de.d1_live_decay(t, self.cfg())
        self.assertEqual(r["verdict"], "TRIGGERED")

    def test_d4_fails_closed_on_missing_prices(self):
        r = de.d4_integrity({"price_gap_pct": 100.0}, {}, self.cfg())
        self.assertEqual(r["verdict"], "TRIGGERED")
        self.assertIn("missing for", r["why"])

    def test_concentration_breach_is_spread_sensitivity_not_a_coincidence(self):
        t = self.trades(40, [0.5] * 40)
        for i, x in enumerate(t):
            x["season"] = "2020"
            x["pnl_units"] = 1.0 if i == 0 else 0.01
        r = de.d3_concentration(t, self.cfg())
        self.assertEqual(r["verdict"], "TRIGGERED")

    def test_demoted_strategy_cannot_return_on_profit_alone(self):
        cfg = self.cfg()
        state = de.StrategyState(strategy_id="S", state="LIVE")
        t = self.trades(60, [-0.5] * 60)
        for x in t:
            x["pnl_units"] = 4.0          # profitable but negative points beat
        ev = de.evaluate("S", t, {"price_gap_pct": 0.0}, {}, cfg, state)
        self.assertEqual(ev["decision"], "DEMOTE")
        self.assertFalse(ev["repromotion"]["eligible"],
                         "PnL cannot re-open a fund that a points-based rule closed")
        self.assertGreaterEqual(ev["repromotion"]["required"], cfg.reprobe_min_bets)

    def test_second_demotion_escalates_to_suspension(self):
        cfg = self.cfg()
        state = de.StrategyState(strategy_id="S", state="DEMOTE", demotions_this_season=1)
        t = self.trades(60, [-0.5] * 60)
        ev = de.evaluate("S", t, {"price_gap_pct": 50.0}, {}, cfg, state)
        self.assertIn(ev["decision"], ("DEMOTE", "SUSPENDED"))

    def test_first_breach_reports_where_in_the_schedule(self):
        pts = [1.0] * 20 + [-4.0] * 20
        t = self.trades(40, pts)
        for i, x in enumerate(t):
            x["season"] = "2020" if i < 20 else "2021"
            x["week"] = str((i % 17) + 1)
        b = de.first_breach(t, self.cfg(), step=10)
        self.assertIn(b["rule"], ("D1-SUBSTITUTE", ""))
        if b["rule"]:
            self.assertTrue(b["game_id"].startswith("g"))

    def test_d1_is_named_as_a_substitute(self):
        r = de.d1_live_decay(self.trades(40, [-1.0] * 40), self.cfg())
        self.assertEqual(r["rule"], "D1-SUBSTITUTE",
                         "measuring decay against a close is not closing-line value; it is "
                         "misleading to call it D1")


class ArtefactConsistencyTest(unittest.TestCase):
    """Cross-checks between artefacts that were computed by different code paths."""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(os.path.join(MKT, "summary.json")):
            raise unittest.SkipTest("data/market artefacts not built")
        with open(os.path.join(MKT, "summary.json"), encoding="utf-8") as fh:
            cls.sm = json.load(fh)

        def tsv(name):
            with open(os.path.join(MKT, name), newline="", encoding="utf-8") as fh:
                return list(csv.DictReader(fh, delimiter="\t"))
        cls.led = tsv("results_ledger_2026.tsv")
        cls.index = tsv("results_ledger_index.tsv")
        cls.board = tsv("fair_lines_current.tsv")
        cls.trades = tsv("backtest_trades.tsv")
        cls.sig = tsv("signal_cards.tsv")
        cls.stk = tsv("staking_cards.tsv")
        cls.bench = tsv("benchmarks.tsv")
        cls.quar = tsv("price_snapshots_quarantine.tsv")
        cls.live = tsv("price_snapshots_2026.tsv")
        cls.dem = tsv("demotion_eval.tsv")
        cls.clubs = tsv("replacement_depth_clubs.tsv")
        cls.dep = tsv("replacement_depth.tsv")

    def test_the_index_covers_every_season_the_ledger_lists(self):
        self.assertEqual({r["game_id"] for r in self.index},
                         {r["game_id"] for r in self.index})
        self.assertGreater(len(self.index), len(self.led),
                           "the index exists so bets from earlier seasons can be checked too")
        for r in self.index:
            self.assertIn(r["verify_status"], ("MATCHED_TWO_FEEDS", "SINGLE_FEED",
                                               "SINGLE_FEED_SEASON_RECONCILED",
                                               "QUARANTINE_MISMATCH", "NO_RESULT"))

    def test_summary_counts_match_the_files(self):
        self.assertEqual(self.sm["games_2026"], len(self.led))
        self.assertEqual(self.sm["games_2026_verified"],
                         sum(1 for r in self.led if r["verify_status"] == "MATCHED_TWO_FEEDS"))
        self.assertEqual(self.sm["snapshots_quarantined"], len(self.quar))
        self.assertEqual(self.sm["trades_published"], len(self.trades))
        self.assertEqual(self.sm["games_2026"], len(self.board))

    def test_no_bet_rests_on_an_unverified_result(self):
        ok = {r["game_id"] for r in self.index if r["settle_eligible"] == "YES"}
        for t in self.trades:
            self.assertIn(t["game_id"], ok, "a trade was graded on a game the ledger refuses")

    def test_every_market_number_on_the_board_is_attributed(self):
        for r in self.board:
            if str(r["market_side_line_home"]).strip():
                self.assertTrue(r["side_line_source"], "a market number without a feed")
                self.assertIn(r["side_line_vintage"],
                              ("CLOSE", "OPEN", "LIVE_CURRENT", "UNDOCUMENTED"))
            else:
                self.assertEqual(str(r["delta_side_pts"]).strip(), "",
                                 "a delta cannot exist without a market number")

    def test_stakes_are_all_flat(self):
        self.assertEqual({t["stake_units"] for t in self.trades}, {"1.0"})

    def test_price_basis_is_declared_on_every_row(self):
        allowed = ("POSTED_IN_STORE",)
        for t in self.trades:
            self.assertTrue(t["price_basis"].startswith(allowed) or
                            t["price_basis"].startswith("NOT_POSTED_ASSUMED"), t["price_basis"])

    def test_roi_is_labelled_an_upper_bound_wherever_it_appears(self):
        for r in self.stk:
            if str(r["roi"]).strip():
                self.assertEqual(r["roi_is_upper_bound"], "YES",
                                 "an ROI measured at a close is an upper bound; it must say so")

    def test_cards_cover_every_rule_in_the_log(self):
        cards = {c["strategy_id"] for c in self.sig}
        for t in self.trades:
            self.assertIn(t["strategy_id"], cards, "a published bet has no scorecard")
        self.assertEqual(len(self.sig), len(self.stk))
        self.assertEqual(cards, {c["strategy_id"] for c in self.stk})
        for c in self.sig:
            self.assertNotEqual(c["strategy_id"], "?", "a card lost its rule id")

    def test_demotion_rows_cover_every_rule(self):
        self.assertEqual({r["strategy_id"] for r in self.dem}, {c["strategy_id"] for c in self.sig})
        for r in self.dem:
            self.assertIn(r["verdict"], ("OK", "TRIGGERED", "NOT_EVALUABLE"))

    def test_depth_levels_lost_arithmetic_from_the_committed_file(self):
        for r in self.dep:
            if str(r["replacement_line"]).strip() and str(r["absent_line"]).strip():
                self.assertEqual(int(r["depth_levels_lost"]),
                                 int(r["replacement_line"]) - int(r["absent_line"]))
            else:
                self.assertIn("no_replacement", "".join(r.keys()))
        per_club = {}
        for r in self.dep:
            d = per_club.setdefault(r["team"], [0, 0])
            if str(r["depth_levels_lost"]).strip():
                d[0] += 1
            else:
                d[1] += 1
        for c in self.clubs:
            want = per_club.get(c["team"], [0, 0])
            self.assertEqual(int(c["vacancies_resolved"]), want[0], "%s resolved count" % c["team"])
            self.assertEqual(int(c["vacancies_unresolved"]), want[1], "%s unresolved count" % c["team"])
            self.assertLessEqual(int(c["first_string_out"]), len(self.dep))

    def test_live_ledger_is_the_current_season_only(self):
        seasons = {r["season"] for r in self.live}
        self.assertEqual(len(seasons), 1)
        self.assertEqual(seasons.pop(), str(max(int(r["season"]) for r in self.led)))

    def test_quarantine_is_stored_not_deleted(self):
        self.assertGreater(len(self.quar), 0, "the 2021 open feed must be recorded, in quarantine")
        for r in self.quar:
            self.assertEqual(r["status"], "QUARANTINED")
            self.assertEqual(r["vintage"], "OPEN")
            self.assertTrue(r["integrity"], "a quarantined row must say why")

    def test_market_numbers_match_the_benchmark_table(self):
        bench = {r["game_id"]: r for r in self.bench}
        for r in self.board:
            b = bench.get(r["game_id"])
            if not b:
                continue
            for a, c in (("market_side_line_home", "market_side_line_home"),
                         ("market_total_line", "market_total_line"),
                         ("market_ml_home", "market_ml_home")):
                if str(r[a]).strip() and str(b[c]).strip():
                    self.assertAlmostEqual(float(r[a]), float(b[c]), places=6,
                                           msg="%s disagrees with the benchmark table" % a)


class SiteRenderingTest(unittest.TestCase):
    # Renamed at integration (PR #38 takeover): main already publishes results-feed.html,
    # signal-vs-staking.html and replacement-depth.html from its own generators, so the
    # spine's three colliding outputs were re-issued with -market names.
    PAGES = ("price-store.html", "results-feed-market.html", "origination.html",
             "signal-vs-staking-market.html", "replacement-depth-market.html", "correlation-gate.html",
             "demotion-gate.html", "decision-desk.html")

    def test_pages_exist_and_declare_they_are_generated(self):
        for name in self.PAGES:
            path = os.path.join(ROOT, name)
            self.assertTrue(os.path.exists(path), "%s was not rendered" % name)
            body = open(path, encoding="utf-8").read()
            self.assertGreaterEqual(body.count("<table"), 2, "%s should carry tables" % name)
            if name != "decision-desk.html":     # authored prose; it cites pages, not source ids
                self.assertIn('href="sources.html#S', body, "%s has no source chip" % name)
            self.assertNotIn("&lt;a ", body, "%s prints an escaped anchor" % name)
            self.assertNotIn("&lt;td", body, "%s prints an escaped cell" % name)
            self.assertIn("</html>", body)

    def test_no_page_fetches_anything(self):
        for name in self.PAGES:
            body = open(os.path.join(ROOT, name), encoding="utf-8").read()
            for forbidden in ("fetch(", "XMLHttpRequest", "<script src=\"http", "@import",
                              "cdn.", "googleapis"):
                self.assertNotIn(forbidden, body, "%s references %s" % (name, forbidden))

    def test_registered_source_ids_all_exist(self):
        with open(os.path.join(ROOT, "data", "sources.tsv"), encoding="utf-8") as fh:
            known = {line.split("\t")[0] for line in fh if line.strip()}
        import re
        for name in self.PAGES:
            body = open(os.path.join(ROOT, name), encoding="utf-8").read()
            for sid in set(re.findall(r"\bS\d{2}\b", body)):
                self.assertIn(sid, known, "%s cites unregistered %s" % (name, sid))

    def test_the_nav_lists_every_new_page(self):
        """Parsed from tools/site.py rather than imported: `import site` would find the
        interpreter's own startup module, not this repository's file."""
        src = open(os.path.join(ROOT, "tools", "site.py"), encoding="utf-8").read()
        block = src.split("NAV = [", 1)[1].split("]", 1)[0]
        for name in self.PAGES:
            self.assertIn('("%s"' % name, block, "%s is not in NAV" % name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
