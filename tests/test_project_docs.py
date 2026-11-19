"""Regression checks for the repository's human-facing review entry points."""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProjectDocsTests(unittest.TestCase):
    def test_markdown_relative_links_resolve(self):
        for filename in ("README.md", "REVIEW.md"):
            text = (ROOT / filename).read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if target.startswith(("https://", "http://", "mailto:")):
                    continue
                path = target.split("#", 1)[0]
                if not path:
                    continue
                with self.subTest(document=filename, target=target):
                    self.assertTrue((ROOT / path).is_file(), f"broken relative link: {target}")

    def test_review_guide_links_required_decision_surfaces(self):
        text = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        required = (
            "readiness.html",
            "requirements-backlog.html",
            "questions.html",
            "suggestions.html",
            "decision-desk.html",
            "flagged.html",
            "source-audit.html",
            "validation.html",
            "removal-of-luck.html",
        )
        for page in required:
            with self.subTest(page=page):
                self.assertIn(f"]({page})", text)
        self.assertIn("What is still needed if unresolved", text)
        self.assertIn("not a live fetch of every source", text)

    def test_readme_no_longer_claims_old_inventory_as_current(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        stale_claims = (
            "Single season, single snapshot, no price data",
            "twenty open questions",
            "fifteen suggestions",
            "all 14 pages",
        )
        for claim in stale_claims:
            with self.subTest(claim=claim):
                self.assertNotIn(claim, text)
        self.assertIn("not every data source is automatically refreshed", text)
        self.assertIn("repository artifact or generated table is not, by itself, independent verification", text)


if __name__ == "__main__":
    unittest.main()
