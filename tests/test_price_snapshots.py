import tempfile
import unittest
from pathlib import Path

from engine.price_snapshots import connect, record, snapshots


class PriceSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tmp.name) / "prices.sqlite")
        self.quote = dict(event_id="event-1", market_type="spread", market_key="game-side",
            side="home", line=-3.5, odds_american=-110,
            captured_at_utc="2026-11-14T12:00:00Z", phase="open",
            source_name="licensed-vendor", source_url="https://vendor.example/quote/1",
            source_record_id="q-1", line_origin_version="model-a1")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_sourced_open_and_close_are_retained(self):
        first = record(self.db, **self.quote)
        close = dict(self.quote, captured_at_utc="2026-11-14T20:00:00Z", phase="close",
                     source_record_id="q-2", line=-4.0)
        record(self.db, **close)
        rows = list(snapshots(self.db, "event-1"))
        self.assertEqual([r["phase"] for r in rows], ["open", "close"])
        self.assertEqual(rows[0]["snapshot_id"], first)
        self.assertEqual(rows[1]["line"], -4.0)
        self.assertEqual(rows[0]["line_origin_version"], "model-a1")

    def test_duplicate_delivery_is_idempotent(self):
        self.assertEqual(record(self.db, **self.quote), record(self.db, **self.quote))
        self.assertEqual(len(list(snapshots(self.db))), 1)

    def test_unverified_or_invalid_market_rejected(self):
        for changes in ({"source_url": ""}, {"market_type": "unknown"}, {"phase": "guess"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                record(self.db, **(self.quote | changes))
        self.assertEqual(len(list(snapshots(self.db))), 0)


if __name__ == "__main__":
    unittest.main()
