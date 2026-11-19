"""Checks for the dated 2026-11-19 official NFL re-read artifacts.

These tests validate the retained transcription's structure and integrity; they do not
replace manual comparison with the official source linked in each S100-S102 record.
"""
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw" / "official-reread-2026-11-19.md"
EXPECTED_SHA256 = "0ec0557cef1c06e8b98b06fc8799a7d79d02d9455ef3a9328404433bf42735cf"


class OfficialRereadJTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = RAW.read_text(encoding="utf-8")
        cls.sources = {}
        for line in (ROOT / "data" / "sources.tsv").read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                cols = line.split("\t")
                cls.sources[cols[0]] = cols

    def test_capture_hash_is_pinned(self):
        digest = hashlib.sha256(RAW.read_bytes()).hexdigest()
        self.assertEqual(digest, EXPECTED_SHA256)

    def test_official_sources_registered(self):
        for sid, url in (
            ("S100", "https://www.nfl.com/injuries/"),
            ("S101", "https://www.nfl.com/standings/league/2026/REG"),
            ("S102", "https://www.nfl.com/schedules/"),
            ("S103", "https://www.nfl.com/news/2026-nfl-schedule-powered-by-aws-to-be-released-thursday-may-14"),
        ): 
            with self.subTest(source=sid):
                self.assertIn(sid, self.sources)
                self.assertEqual(self.sources[sid][3], url)
                self.assertEqual(self.sources[sid][4], "Official (league)")
                self.assertEqual(self.sources[sid][6], "VERIFIED")

    def test_injury_rows_and_club_coverage(self):
        rows = re.findall(
            r"^([A-Z]{2,3}) \| ([^|]+) \| ([^|]+) \| ([^|]*) \| ([^|]+) \| ([^|]*)$",
            self.text, re.MULTILINE)
        clubs = {row[0] for row in rows}
        self.assertEqual(len(rows), 253)
        self.assertEqual(len(clubs), 24)
        self.assertIn("CIN", self.text)
        self.assertIn("Commanders: No Injuries Reported.", self.text)
        self.assertIn("Bengals: No Injuries Reported.", self.text)

    def test_schedule_announcement_uses_correct_official_source(self):
        schedule = (ROOT / "schedule.html").read_text(encoding="utf-8")
        generator = (ROOT / "scripts" / "build_pages_d.py").read_text(encoding="utf-8")
        self.assertIn('href="sources.html#S103">S103</a>', schedule)
        self.assertIn("https://www.nfl.com/news/2026-nfl-schedule-powered-by-aws-to-be-released-thursday-may-14", schedule)
        self.assertIn('href="sources.html#S103">S103</a>', generator)
        self.assertNotIn('source <a href="sources.html#S86">S86</a>', schedule)
        d5 = (ROOT / "decision-questions-d5.html").read_text(encoding="utf-8")
        self.assertNotIn("schedule announcement date is missing", d5)
        self.assertIn("official release announcement (S103)", d5)
        self.assertIn("venue verification still required", d5)

    def test_standings_and_schedule_coverage(self):
        standings = re.findall(r"^[A-Z]{2,3} \| \d+ \| \d+ \| \d+ \|", self.text, re.MULTILINE)
        fixtures = re.findall(r"^- (?:Thursday|Sunday|Monday), November \d+\w*[, ].*$", self.text, re.MULTILINE)
        self.assertEqual(len(standings), 32)
        self.assertEqual(len(fixtures), 13)
        self.assertIn("Teams on Bye:", self.text)

    def test_review_plan_covers_every_open_or_partial_question(self):
        questions = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
        expected = {q["id"] for q in questions if q.get("answer_state") in ("open", "partial")}
        plan = json.loads((ROOT / "data" / "discovery_plan.json").read_text(encoding="utf-8"))
        rows = plan["questions"]
        self.assertEqual({q["id"] for q in rows}, expected)
        for row in rows:
            self.assertTrue(row["numeric_clearance_from_register"])
            for src in row["official_sources"]:
                self.assertTrue(src["url"].startswith("https://"))
        by_id = {row["id"]: row for row in rows}
        for qid in ("Q03", "Q13", "Q14", "Q18"):
            self.assertEqual(by_id[qid]["official_sources"], [], qid)
            self.assertIn("UNVERIFIED", by_id[qid]["source_review"])


if __name__ == "__main__":
    unittest.main()
