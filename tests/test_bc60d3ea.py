#!/usr/bin/env python3
"""J4 — tests for session arena/bc60d3ea-fl1 (2026-11-19 freshness reads).

Covers: the V-J1..V-J6 verifier (all PASS, TSV shape), the raw captures'
internal consistency, the audit document's register coverage (every Q and
SG id present), and the guard that the verifier never touches canonical
Week 10 files. Stdlib only, no network.
"""

import csv
import hashlib
import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def p(*parts):
    return os.path.join(ROOT, *parts)


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load_standings(path):
    rows = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.strip():
                cells = line.split("\t")
                rows[cells[0]] = cells
    return rows


class TestVerifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = {n: sha(p("data", n)) for n in
                      ("injuries.tsv", "results.tsv", "standings.tsv")}
        cls.proc = subprocess.run(
            [sys.executable, p("scripts", "verify_bc60d3ea.py")],
            capture_output=True, text=True, cwd=ROOT)
        cls.after = {n: sha(p("data", n)) for n in
                     ("injuries.tsv", "results.tsv", "standings.tsv")}
        with open(p("data", "verification-bc60d3ea.tsv"),
                  encoding="utf-8", newline="") as fh:
            cls.rows = list(csv.DictReader(fh, delimiter="\t"))

    def test_verifier_exits_zero(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stdout + self.proc.stderr)

    def test_seven_checks_all_pass(self):
        self.assertEqual([r["check"] for r in self.rows],
                         ["V-J1a", "V-J1b", "V-J2", "V-J3", "V-J4", "V-J5", "V-J6"])
        self.assertTrue(all(r["result"] == "PASS" for r in self.rows),
                        [r for r in self.rows if r["result"] != "PASS"])

    def test_every_check_has_official_url(self):
        for r in self.rows:
            self.assertTrue(r["source_url"].startswith("https://www.nfl.com/"),
                            r["check"])

    def test_canonical_files_untouched(self):
        self.assertEqual(self.before, self.after)


class TestStandingsCaptures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.league = load_standings(p("raw", "standings-2026-20261119-league.tsv"))
        cls.division = load_standings(p("raw", "standings-2026-20261119-division.tsv"))

    def test_32_clubs_both_routes(self):
        self.assertEqual(len(self.league), 32)
        self.assertEqual(len(self.division), 32)
        self.assertEqual(set(self.league), set(self.division))

    def test_routes_identical(self):
        self.assertEqual(self.league, self.division)

    def test_arithmetic(self):
        for abbr, c in self.league.items():
            self.assertEqual(len(c), 17, abbr)
            w, l, t = int(c[1]), int(c[2]), int(c[3])
            self.assertIn(w + l + t, (9, 10), abbr)
            self.assertEqual(int(c[7]), int(c[5]) - int(c[6]), abbr)
            pct = (w + 0.5 * t) / (w + l + t)
            self.assertAlmostEqual(float(c[4]), pct, places=3, msg=abbr)

    def test_week11_bye_clubs_played_10(self):
        for abbr in ("ATL", "CLE", "GB", "LA", "NE", "SEA"):
            c = self.league[abbr]
            self.assertEqual(int(c[1]) + int(c[2]) + int(c[3]), 10, abbr)


class TestInjuryCapture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = []
        with open(p("raw", "injuries-week11-2026-read1.md"), encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                cells = line.split("\t")
                if len(cells) == 6:
                    cls.rows.append(cells)

    def test_row_count_and_grammar(self):
        self.assertEqual(len(self.rows), 253)
        for r in self.rows:
            self.assertIn(r[4], ("FULL", "LIMITED", "DNP"), r)
            self.assertIn(r[5], ("Out", "Doubtful", "Questionable", ""), r)

    def test_designations_only_on_thursday_clubs(self):
        designated = {r[0] for r in self.rows if r[5] != ""}
        self.assertEqual(designated, {"IND", "HOU"})
        outs = [r for r in self.rows if r[5] == "Out"]
        self.assertEqual(len(outs), 9)

    def test_bye_and_no_report_clubs_absent(self):
        clubs = {r[0] for r in self.rows}
        self.assertEqual(len(clubs), 24)
        self.assertFalse(clubs & {"ATL", "CLE", "GB", "LA", "NE", "SEA"})
        self.assertFalse(clubs & {"CIN", "WAS"})


class TestAuditDoc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(p("docs", "DECISION-AUDIT-bc60d3ea.md"), encoding="utf-8") as fh:
            cls.doc = fh.read()
        with open(p("data", "questions.json"), encoding="utf-8") as fh:
            cls.questions = json.load(fh)
        with open(p("data", "suggestions.json"), encoding="utf-8") as fh:
            cls.suggestions = json.load(fh)

    def test_every_question_in_doc(self):
        for q in self.questions:
            self.assertIn("| %s |" % q["id"], self.doc, q["id"])

    def test_every_suggestion_in_doc(self):
        for s in self.suggestions:
            self.assertIn("| %s |" % s["id"], self.doc, s["id"])

    def test_doc_states_counts(self):
        self.assertIn("12 answered", self.doc)
        self.assertIn("16 partial", self.doc)
        self.assertIn("18 open", self.doc)

    def test_exec_summary_exists_and_names_gates(self):
        with open(p("docs", "EXECUTIVE_SUMMARY-bc60d3ea.md"),
                  encoding="utf-8") as fh:
            text = fh.read()
        for token in ("Q21", "Q44", "Q05", "V-J1", "253 rows", "32/32"):
            self.assertIn(token, text, token)


if __name__ == "__main__":
    unittest.main()
