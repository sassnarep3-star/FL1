"""Gate tests for the Week 11 injury-hub read (read 5). Every check re-reads the raw capture."""
import csv
import json
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "injuries-week11-2026-read5.md")
TSV = os.path.join(ROOT, "data", "injuries_2026-11-19.tsv")
JSN = os.path.join(ROOT, "data", "injury_hub_delta_w11.json")


class Week11Read(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_week11_read.py")],
                       check=True, capture_output=True)
        with open(TSV, encoding="utf-8") as f:
            cls.rows = list(csv.DictReader(f, delimiter="\t"))
        with open(JSN, encoding="utf-8") as f:
            cls.doc = json.load(f)
        with open(RAW, encoding="utf-8") as f:
            cls.raw = f.read()

    def test_row_count_matches_capture(self):
        raw_rows = [l for l in self.raw.splitlines() if re.match(r"^\| \[[^\]]+\]\(https://www\.nfl\.com/players/", l)]
        self.assertEqual(len(raw_rows), len(self.rows))
        self.assertEqual(len(self.rows), 253)

    def test_every_row_has_official_links(self):
        for r in self.rows:
            self.assertTrue(r["source_url"].startswith("https://www.nfl.com/"), r["player"])
            self.assertTrue(r["player_url"].startswith("https://www.nfl.com/players/"), r["player"])
            self.assertEqual(r["source_id"], "S100")

    def test_mapped_codes_only_from_published_strings(self):
        for r in self.rows:
            self.assertIn(r["practice_code"], {"FULL", "LIMITED", "DNP"})
            self.assertIn(r["game_code"], {"", "Questionable", "Out", "Doubtful"})

    def test_raw_line_reproduces_row(self):
        lines = self.raw.splitlines()
        for r in self.rows:
            line = lines[int(r["raw_line"]) - 1]
            self.assertIn(r["player"], line)
            self.assertIn(r["practice_raw"], line)

    def test_no_injury_clubs_recorded(self):
        self.assertEqual(sorted(self.doc["reads"][0]["clubs_no_injuries_reported"]), ["Bengals", "Commanders"])

    def test_delta_null_and_flags_recorded(self):
        self.assertIsNone(self.doc["delta"])
        self.assertEqual(self.doc["flag_count"], len(self.doc["flags"]))
        self.assertTrue(any(f["player"] == "Kerby Joseph" for f in self.doc["flags"]))


if __name__ == "__main__":
    unittest.main()
