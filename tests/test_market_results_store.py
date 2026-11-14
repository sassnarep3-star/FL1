import os
import sqlite3
import tempfile
import unittest

from engine.snapshot_store import SnapshotStore, sha256_bytes as snapshot_sha
from engine.results_feed import ResultsFeed, VerifiedResult, sha256_bytes as result_sha

NOW = "2026-11-14T12:00:00Z"
URL = "https://sportsbook.example/markets/event-123"
NFL_URL = "https://www.nfl.com/games/example-game"
OPEN_PAYLOAD = b"quote capture"
CLOSE_PAYLOAD = b"closing quote capture"
RESULT_PAYLOAD = b"official result capture"
DIGEST = snapshot_sha(OPEN_PAYLOAD)


class SnapshotStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = SnapshotStore(os.path.join(self.tmp.name, "prices.sqlite"))

    def tearDown(self):
        self.tmp.cleanup()

    def open_market(self, **overrides):
        values = dict(market_id="g1:spread:home", game_id="g1", market_type="spread",
                      selection="HOME", value_unit="points", captured_at=NOW,
                      source_name="book source", source_url=URL, verified=True,
                      source_sha256=DIGEST, source_checked_at=NOW,
                      source_payload=OPEN_PAYLOAD, fair_value=-2.0,
                      market_value=-1.5, american_odds=-110)
        values.update(overrides)
        self.store.originate(**values)

    def test_open_and_close_are_separate_rows_with_calculated_difference(self):
        self.open_market()
        self.store.close(market_id="g1:spread:home", captured_at="2026-11-14T17:00:00+00:00",
                         source_name="book source", source_url=URL, verified=True,
                         source_sha256=snapshot_sha(CLOSE_PAYLOAD), source_checked_at=NOW,
                         source_payload=CLOSE_PAYLOAD, fair_value=-2.5,
                         market_value=-3.0, american_odds=-105)
        rows = self.store.rows()
        self.assertEqual([r["phase"] for r in rows], ["opening", "closing"])
        self.assertEqual(rows[0]["difference"], -0.5)
        self.assertEqual(rows[1]["difference"], 0.5)
        self.assertEqual(rows[1]["market_value"], -3.0)
        self.assertEqual(self.store.incomplete_markets(), [])

    def test_unverified_snapshot_numeric_fields_are_blank_and_market_incomplete(self):
        self.open_market(verified=False, fair_value=3, market_value=2,
                         american_odds=110, source_sha256=None, source_checked_at=None)
        row = self.store.rows()[0]
        self.assertIsNone(row["fair_value"])
        self.assertIsNone(row["market_value"])
        self.assertIsNone(row["difference"])
        self.assertIsNone(row["american_odds"])
        self.assertEqual(self.store.incomplete_markets(), ["g1:spread:home"])

    def test_verified_values_need_matching_payload_digest_and_checked_timestamp(self):
        with self.assertRaisesRegex(ValueError, "source_sha256"):
            self.open_market(source_sha256=None)
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.open_market(source_payload=b"different payload")
        self.assertEqual(self.store.rows(), [])

    def test_closing_requires_opening_and_only_one_closing_is_allowed(self):
        with self.assertRaisesRegex(ValueError, "unknown market"):
            self.store.close(market_id="missing", captured_at=NOW, source_name="x",
                             source_url=URL, verified=False)
        self.open_market()
        closing = dict(market_id="g1:spread:home", captured_at=NOW, source_name="x",
                       source_url=URL, verified=False)
        self.store.close(**closing)
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.close(**closing)

    def test_close_cannot_predate_open_and_incomplete_flags_unverified_open(self):
        self.open_market(verified=False, fair_value=1, market_value=2, american_odds=-105,
                         source_sha256=None, source_checked_at=None)
        with self.assertRaisesRegex(ValueError, "predate"):
            self.store.close(market_id="g1:spread:home", captured_at="2026-11-13T12:00:00Z",
                             source_name="book source", source_url=URL, verified=True,
                             source_sha256=snapshot_sha(CLOSE_PAYLOAD), source_checked_at=NOW,
                             source_payload=CLOSE_PAYLOAD)
        self.store.close(market_id="g1:spread:home", captured_at="2026-11-14T13:00:00Z",
                         source_name="book source", source_url=URL, verified=True,
                         source_sha256=snapshot_sha(CLOSE_PAYLOAD), source_checked_at=NOW,
                         source_payload=CLOSE_PAYLOAD, fair_value=-2,
                         market_value=-1.5, american_odds=-110)
        self.assertEqual(self.store.incomplete_markets(), ["g1:spread:home"])

    def test_bad_url_nonfinite_value_and_invalid_market_type_rejected(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            self.open_market(source_url="http://sportsbook.example/market")
        with self.assertRaisesRegex(ValueError, "finite"):
            self.open_market(fair_value=float("nan"))
        with self.assertRaisesRegex(ValueError, "market_type"):
            self.open_market(market_type="unknown")
        self.assertEqual(self.store.rows(), [])

    def test_digest_utility(self):
        self.assertEqual(snapshot_sha(b"quote capture"),
                         "ce41d43f0e1749968ae091f9a358e50565a3ae84bd1b5968e7ef0684481eae16")


class ResultsFeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.feed = ResultsFeed(os.path.join(self.tmp.name, "results.sqlite"))

    def tearDown(self):
        self.tmp.cleanup()

    def result(self, **overrides):
        data = dict(game_id="2026_10_A_B", season=2026, week=10,
                    away_team="A", home_team="B", away_score=17, home_score=20,
                    status="FINAL", source_url=NFL_URL, source_checked_at=NOW,
                    evidence_sha256=result_sha(RESULT_PAYLOAD),
                    evidence_payload=RESULT_PAYLOAD, verified=True)
        data.update(overrides)
        return VerifiedResult(**data)

    def test_ingests_only_verified_final_and_retains_source_provenance(self):
        self.assertEqual(self.feed.ingest([self.result()]), 1)
        row = self.feed.latest()[0]
        self.assertEqual(row["away_score"], 17)
        self.assertEqual(row["source_url"], NFL_URL)
        self.assertEqual(row["evidence_sha256"], result_sha(RESULT_PAYLOAD))
        self.assertEqual(row["verified"], 1)

    def test_repeat_payload_is_idempotent_but_correction_is_retained(self):
        first = self.result()
        self.assertEqual(self.feed.ingest([first]), 1)
        self.assertEqual(self.feed.ingest([first]), 0)
        corrected_payload = b"official corrected result capture"
        corrected = self.result(home_score=21,
                                evidence_sha256=result_sha(corrected_payload),
                                evidence_payload=corrected_payload)
        self.assertEqual(self.feed.ingest([corrected]), 1)
        self.assertEqual(len(self.feed.history(first.game_id)), 2)
        self.assertEqual(self.feed.latest()[0]["home_score"], 21)

    def test_unverified_nonfinal_and_non_nfl_sources_are_rejected_atomically(self):
        good = self.result()
        for bad in (self.result(verified=False), self.result(status="SCHEDULED"),
                    self.result(source_url="https://nfl.com.evil.example/game")):
            with self.assertRaises(ValueError):
                self.feed.ingest([good, bad])
            self.assertEqual(self.feed.latest(), [])

    def test_bad_score_timestamp_or_digest_rejected(self):
        for bad in (self.result(home_score=-1), self.result(away_score=True),
                    self.result(source_checked_at="2026-11-14T12:00:00"),
                    self.result(evidence_sha256="not-a-digest"),
                    self.result(evidence_payload=b"payload with wrong matching digest")):
            with self.assertRaises(ValueError):
                self.feed.ingest([bad])
        self.assertEqual(self.feed.latest(), [])

    def test_results_digest_utility(self):
        self.assertEqual(result_sha(b"result capture"),
                         "3005952c8dcb6ee0d0540e3467b3669720966bdb83fce8d488b6d090f9f5a99f")


if __name__ == "__main__":
    unittest.main()
