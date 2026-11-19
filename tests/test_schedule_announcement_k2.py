"""K2 (R44): the dated schedule announcement is captured, hashed and quote-verified."""
import datetime
import hashlib
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def p(*parts):
    return os.path.join(ROOT, *parts)


class ScheduleAnnouncementK2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(p("data", "schedule_announcement.json"), encoding="utf-8") as fh:
            cls.doc = json.load(fh)
        with open(p("raw", "schedule-announcement-2026.md"), "rb") as fh:
            cls.raw_bytes = fh.read()
        cls.raw = cls.raw_bytes.decode("utf-8")

    def test_task_and_session(self):
        self.assertEqual(self.doc["task"], "R44")
        self.assertEqual(self.doc["session"], "arena/9fccbb0e-fl1")

    def test_raw_hash_matches_capture(self):
        self.assertEqual(self.doc["raw_sha256"], hashlib.sha256(self.raw_bytes).hexdigest())

    def test_fetch_date_is_valid_and_not_future(self):
        d = datetime.date.fromisoformat(self.doc["fetch_date_utc"])
        self.assertLessEqual(d, datetime.date(2026, 11, 19))
        self.assertGreaterEqual(d, datetime.date(2026, 5, 14))

    def test_every_claim_quote_is_verbatim_in_raw(self):
        self.assertGreaterEqual(len(self.doc["claims"]), 8)
        for c in self.doc["claims"]:
            self.assertIn(c["quote"], self.raw, c["id"])

    def test_claim_urls_are_official_nfl_hosts(self):
        for c in self.doc["claims"]:
            self.assertTrue(c["url"].startswith("https://media.nfl.com/"), c["id"])
        for a in self.doc["announcements"]:
            self.assertTrue(a["url"].startswith("https://media.nfl.com/"), a["role"])

    def test_release_and_advance_dates(self):
        by_role = {a["role"]: a for a in self.doc["announcements"]}
        self.assertEqual(by_role["advance_notice"]["published"], "2026-05-08")
        self.assertEqual(by_role["release"]["published"], "2026-05-14")

    def test_derived_game_count(self):
        (check,) = self.doc["derived_checks"]
        self.assertEqual(check["computed"], 32 * 17 // 2)
        self.assertEqual(check["stated"], 272)
        self.assertTrue(check["pass"])

    def test_headline_values(self):
        byid = {c["id"]: c for c in self.doc["claims"]}
        self.assertEqual(byid["A1"]["value"], 272)
        self.assertEqual(byid["A2"]["value"], 18)
        self.assertEqual(byid["A3"]["value"], 17)
        self.assertEqual(byid["A7"]["value"], 9)

    def test_source_requests_registered_with_matching_urls(self):
        # K4 (integration) registers the request rows in data/sources.tsv. Each row must
        # exist once, with the URL from the K2 request, and with the official NFL host.
        with open(p("data", "sources.tsv"), encoding="utf-8") as fh:
            table = {}
            for line in fh:
                if line.strip():
                    cols = line.rstrip("\n").split("\t")
                    table.setdefault(cols[0], []).append(cols)
        req = self.doc["source_register_request"]
        self.assertEqual(req["status"], "registered by K4 integration (data/sources.tsv)")
        for row in req["rows"]:
            hits = table.get(row["id"], [])
            self.assertEqual(len(hits), 1, row["id"])
            self.assertEqual(hits[0][3], row["url"], row["id"])
            self.assertEqual(hits[0][6], "VERIFIED", row["id"])
            self.assertTrue(row["url"].startswith("https://media.nfl.com/"), row["id"])

    def test_schedule_block_miswire_is_recorded(self):
        blk = self.doc["schedule_html_block"]
        self.assertEqual(blk["cites_source"], "S86")
        self.assertIn("J-F1", blk["status"])


if __name__ == "__main__":
    unittest.main()
