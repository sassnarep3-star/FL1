"""Regression checks for the current-state documentation and grouped site navigation."""

import csv
import html
import json
import re
import unittest
from pathlib import Path

from tools import checkrows

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def data_row_count(path, delimiter="\t"):
    with (ROOT / path).open(encoding="utf-8", newline="") as fh:
        return sum(1 for row in csv.reader(fh, delimiter=delimiter) if row)


class CurrentStateDocsTest(unittest.TestCase):
    def test_documented_counts_match_committed_records(self):
        results_latest = data_row_count("data/results_2026-11-17.tsv")
        results_frozen = data_row_count("data/results.tsv")
        injury_old = data_row_count("data/injuries.tsv")
        injury_new = data_row_count("data/injuries_2026-11-16.tsv")
        requirements = json.loads(read("data/requirements.json"))
        backlog = json.loads(read("data/requirements_backlog.json"))

        self.assertEqual((results_latest, results_frozen), (149, 137))
        self.assertEqual((injury_old, injury_new), (345, 347))
        self.assertEqual((len(requirements), len(backlog["rows"])), (28, 59))

        readme = read("README.md")
        review = read("REVIEW.md")
        executive = read("EXECUTIVE_SUMMARY.md")
        executive_html = read("executive-summary.html")
        dashboard = read("index.html")
        for doc in (readme, review, executive, executive_html, dashboard):
            self.assertIn("149", doc)
            self.assertIn("137", doc)
        for doc in (readme, review, executive, executive_html, dashboard):
            self.assertIn("F67", doc)
        self.assertIn("28 core rows and 59 backlog rows", readme)
        self.assertIn("28 core rows and 59 backlog rows", executive)
        self.assertIn("345 rows", readme)
        self.assertIn("347 rows", readme)

    def test_legacy_claims_are_not_current_guidance(self):
        current = "\n".join(read(p) for p in (
            "README.md", "REVIEW.md", "EXECUTIVE_SUMMARY.md", "executive-summary.html", "index.html"
        )).lower()
        for stale in (
            "no line has been originated and no strategy has a result",
            "no strategy on this site has a performance figure, because no strategy has been run",
            "twenty open questions",
            "fifteen suggestions",
            "the 15 items where something could not be confirmed",
        ):
            self.assertNotIn(stale, current)

    def test_archived_documents_are_marked_historical(self):
        for name in (
            "README-legacy-2026-11-17.md",
            "REVIEW-legacy-2026-11-17.md",
            "EXECUTIVE_SUMMARY-legacy-2026-11-17.md",
        ):
            text = read("archive/" + name)
            self.assertIn("Historical snapshot — archived 2026-11-17", text)
            self.assertIn("Do not use it as current guidance", text)

    def test_all_root_pages_are_in_the_grouped_navigation(self):
        root_pages = {p.name for p in ROOT.glob("*.html")}
        self.assertEqual(len(root_pages), 43)
        for page in sorted(root_pages):
            doc = read(page)
            nav_match = re.search(r'<nav class="nav"[^>]*>(.*?)</nav>', doc, re.S)
            self.assertIsNotNone(nav_match, page + " has no grouped navigation")
            nav = nav_match.group(1)
            links = set(re.findall(r'<a href="([^\"]+)"', nav))
            self.assertEqual(links, root_pages, page + " navigation omits or invents a root page")
            groups = re.findall(r'<details class="nav-group[^\"]*"><summary>(.*?)</summary>', nav)
            self.assertEqual(len(groups), 5, page + " should have five topic groups")
            current = re.findall(r'<a href="([^\"]+)" aria-current="page">', nav)
            self.assertEqual(current, [page], page + " must mark its own route")

    def test_dashboard_keeps_alternate_readiness_and_luck_views_visible(self):
        dashboard = read("index.html")
        for target in (
            'href="requirements-backlog.html"',
            'href="readiness.html"',
            'href="#decision-readiness-view"',
            'href="removal-of-luck.html"',
            'href="#signal-variance-view"',
            'href="#familywise-luck-view"',
            'href="readiness.html#luck"',
            'href="flagged.html#F66"',
            'href="suggestions.html#SG47"',
        ):
            self.assertIn(target, dashboard)
        plain = " ".join(re.sub(r"<[^>]+>", " ", html.unescape(dashboard)).split()).lower()
        self.assertIn("retained pending review", plain)
        self.assertIn("third-party-backed research ledger", plain)
        self.assertIn("user-provided project specifications", plain)
        self.assertIn("2026-11-16 requirements-register snapshot", plain)
        self.assertIn("24/28 requirements complete", plain)
        self.assertIn("68/74 sources verified", plain)
        self.assertIn("not current repository totals", plain)
        self.assertIn("2026-11-16 signal-versus-variance view", plain)
        self.assertIn("2026-11-16 family-wise p-value and sample-floor view", plain)
        self.assertIn("not nfl facts", plain)

    def test_requirement_backlog_is_labelled_as_user_spec_not_nfl_fact(self):
        page = read("requirements-backlog.html")
        self.assertIn('class="callout warn spec-provenance"', page)
        plain = " ".join(re.sub(r"<[^>]+>", " ", page).split()).lower()
        self.assertIn("user-provided project specifications", plain)
        self.assertIn("not nfl requirements, nfl policy, or facts about the league", plain)
        self.assertIn("Register source refs (not validation of the specification)", page)
        self.assertIn("requirements-backlog.html", checkrows.SPEC_PAGES)
        n_rows, bad, n_def, n_spec = checkrows.check_page(str(ROOT / "requirements-backlog.html"))
        self.assertEqual((n_rows, bad, n_def, n_spec), (59 + 28, [], 0, 59 + 28))

    def test_executive_summary_evidence_rows_link_to_official_records(self):
        page = read("executive-summary.html")
        table_match = re.search(r'<table class="dense">(.*?)</table>', page, re.S)
        self.assertIsNotNone(table_match)
        rows = re.findall(r'<tr>(.*?)</tr>', table_match.group(1), re.S)
        self.assertEqual(len(rows), 6)  # header plus five dated evidence records
        for row in rows[1:]:
            self.assertRegex(row, r'href="sources\.html#S\d{2}"')
        for sid in ("S89", "S90", "S52", "S01", "S80", "S91"):
            self.assertIn('href="sources.html#%s"' % sid, table_match.group(1))

    def test_schedule_source_id_mismatch_is_disclosed(self):
        for path in ("README.md", "REVIEW.md", "EXECUTIVE_SUMMARY.md", "executive-summary.html", "index.html"):
            text = read(path).lower()
            self.assertIn("s86", text)
            self.assertIn("win-totals", text)
            self.assertIn("2026-nfl-schedule-powered-by-aws-to-be-released-thursday-may-14", text)


if __name__ == "__main__":
    unittest.main()
