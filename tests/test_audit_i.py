"""2026-11-19 official re-read and brief-to-artifact traceability audit.

This audit is intentionally explicit about its limits: the dated NFL reads are
compared row-by-row; the requirement ledger is checked for repository evidence
paths and source-registry status, not treated as fresh verification of older NFL
facts. Values without a fresh official source stay blank and flagged.
"""

import csv
import json
import os
import re
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_injury_hub_delta import diff, parse_capture  # noqa: E402


INJURY_URL = "https://www.nfl.com/injuries/"
STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
SCHEDULE_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"


def load_tsv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def markdown_table(path, prefix):
    found = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.startswith(prefix):
            continue
        found.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return found


def url_in(markdown_link):
    m = re.search(r"\((https://[^)]+)\)", markdown_link)
    if not m:
        raise AssertionError("expected an https URL in %r" % markdown_link)
    return m.group(1)


class TestOfficialRereads(unittest.TestCase):
    def test_week11_injury_capture_and_rollover_are_parser_checked(self):
        path = ROOT / "raw/injuries-week11-2026-read5.md"
        text = path.read_text(encoding="utf-8")
        claim = re.search(r"^[-\s]*Rows parsed: (\d+)", text, flags=re.M)
        self.assertIsNotNone(claim)
        read5 = parse_capture(str(path))
        self.assertEqual(int(claim.group(1)), 253)
        self.assertEqual(len(read5), 253)
        self.assertEqual(len({(r["team"], r["player"], r["pos"]) for r in read5}), 253)

        payload = json.loads((ROOT / "data/injury_hub_delta.json").read_text(encoding="utf-8"))
        self.assertEqual(len(payload["reads"]), 4)  # preserve the existing read-1..4 interface
        fifth = payload["week_rollover_read"]
        self.assertEqual((fifth["read"], fifth["rows"], fifth["week_shown"]),
                         (5, 253, "WEEK 11"))
        self.assertEqual(fifth["capture"], "raw/injuries-week11-2026-read5.md")
        self.assertEqual(fifth["source_url"], INJURY_URL)
        self.assertEqual(fifth["source_id"], "S01")
        self.assertIn("2026-11-19", fifth["read_window_utc"])
        self.assertFalse((ROOT / "data/injuries_2026-11-19.tsv").exists(),
                         "do not create a second public copy of the report level")

        read4 = parse_capture(str(ROOT / "raw/injuries-week10-2026-read4.md"))
        expected = diff(read4, read5, "read 4 (WEEK 10, 2026-11-17)",
                        "read 5 (WEEK 11, 2026-11-19)")
        self.assertEqual(payload["week_rollover"], expected)
        self.assertEqual((len(expected["changed"]), len(expected["added"]),
                          len(expected["removed"])), (228, 120, 214))
        # The same-week site delta remains read 3 -> read 4; do not mislabel the
        # week rollover as a designation change within one report week.
        self.assertEqual(payload["delta"]["newer_label"], "read 4 (2026-11-17 02:43Z)")

        by_team_status = {}
        for row in read5:
            if row["game"]:
                by_team_status.setdefault(row["team"], []).append(row["game"])
        self.assertEqual(set(by_team_status), {"IND", "HOU"})
        self.assertEqual((by_team_status["IND"].count("Out"),
                          by_team_status["IND"].count("Questionable")), (5, 4))
        self.assertEqual((by_team_status["HOU"].count("Out"),
                          by_team_status["HOU"].count("Questionable")), (4, 3))

    def test_standings_reread_matches_all_32_closeout_rows(self):
        raw_rows = markdown_table(ROOT / "raw/standings-2026-11-19.md", "| ")
        raw_rows = [r for r in raw_rows if len(r) == 9 and re.fullmatch(r"[A-Z]{2,3}", r[0])]
        prior = {}
        with open(ROOT / "data/standings_2026-11-17-closeout.tsv", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    cells = line.rstrip("\n").split("\t")
                    prior[cells[0]] = cells
        self.assertEqual(len(raw_rows), 32)
        self.assertEqual(set(r[0] for r in raw_rows), set(prior))
        for r in raw_rows:
            self.assertEqual(r[2:8], prior[r[0]][1:7], r[0])
            self.assertEqual(url_in(r[8]), STANDINGS_URL, r[0])

    def test_week11_schedule_and_game_centre_venue_reread(self):
        raw_rows = markdown_table(ROOT / "raw/schedule-week11-2026-2026-11-19.md", "| 2026-")
        self.assertEqual(len(raw_rows), 13)
        official = {}
        for r in raw_rows:
            self.assertEqual(len(r), 8)
            key = (r[0], r[2], r[3])
            self.assertNotIn(key, official)
            self.assertEqual(url_in(r[6]), SCHEDULE_URL)
            self.assertTrue(url_in(r[7]).startswith("https://www.nfl.com/games/"))
            official[key] = r

        with open(ROOT / "data/schedule2026-d.csv", encoding="utf-8", newline="") as fh:
            csv_rows = { (r["date"], r["away_team"], r["home_team"]): r
                         for r in csv.DictReader(fh) if r["week"] == "11" }
        self.assertEqual(set(official), set(csv_rows))
        self.assertEqual(len(csv_rows), 13)
        def to_24(value):
            return datetime.strptime(value, "%I:%M %p").strftime("%H:%M")
        kickoff_mismatches = []
        venue_label_mismatches = []
        for key, row in official.items():
            data = csv_rows[key]
            if to_24(row[1]) != data["kickoff_et"]:
                kickoff_mismatches.append((row[2], row[3], data["kickoff_et"], to_24(row[1])))
            if row[5] != data["stadium"]:
                venue_label_mismatches.append((row[2], row[3], data["stadium"], row[5]))
        self.assertEqual(set(kickoff_mismatches), {
            ("PIT", "PHI", "16:25", "13:00"),
            ("JAX", "NYG", "13:00", "16:25"),
        })
        self.assertEqual(venue_label_mismatches, [
            ("ARI", "KC", "GEHA Field at Arrowhead Stadium", "Arrowhead Stadium")
        ])
        text = (ROOT / "raw/schedule-week11-2026-2026-11-19.md").read_text(encoding="utf-8")
        for bye in ("Atlanta Falcons (ATL)", "Cleveland Browns (CLE)",
                    "Green Bay Packers (GB)", "Los Angeles Rams (LAR)",
                    "New England Patriots (NE)", "Seattle Seahawks (SEA)"):
            self.assertIn(bye, text)

    def test_verification_table_has_official_links_or_explicit_flags(self):
        rows = load_tsv(ROOT / "data/verification-2026-11-19.tsv")
        self.assertEqual(len(rows), 134)
        counts = {}
        for r in rows:
            counts[r["scope"]] = counts.get(r["scope"], 0) + 1
        self.assertEqual(counts["official_reverification"], 49)  # 32 standings + 13 games + 3 injury + pagination
        self.assertEqual(counts["official_game_centre_venue"], 13)
        self.assertEqual(counts["published_site_audit"], 13)
        self.assertEqual(counts["brief_to_artifact_trace"], 59)
        for r in rows:
            if r["scope"] == "brief_to_artifact_trace" and not r["official_source_url"]:
                self.assertTrue(r["source_status"].startswith("FLAG_"), r["check_id"])
            elif r["scope"] == "brief_to_artifact_trace":
                urls = r["official_source_url"].split(";")
                self.assertTrue(urls and all(u.startswith("https://") for u in urls), r["check_id"])
                self.assertEqual(r["source_status"], "REGISTERED_OFFICIAL_HISTORICAL_NOT_FRESH", r["check_id"])
            else:
                self.assertTrue(r["official_source_url"].startswith("https://www.nfl.com/"),
                                r["check_id"])
        self.assertEqual(sum(r["status"] == "SITE_FIX_REQUEST" for r in rows), 12)
        self.assertEqual(sum(r["status"] == "SCHEDULE_DATA_MISMATCH" for r in rows), 2)

    def test_new_live_capture_uses_a_registered_official_url(self):
        sources = {}
        with open(ROOT / "data/sources.tsv", encoding="utf-8", newline="") as fh:
            for row in csv.reader(fh, delimiter="\t"):
                if len(row) >= 7:
                    sources[row[0]] = row
        self.assertIn("S01", sources)
        self.assertEqual(sources["S01"][3], INJURY_URL)
        self.assertEqual(sources["S01"][4], "Official (league)")
        self.assertEqual(sources["S01"][6], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
