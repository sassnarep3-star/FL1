import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import source_audit


class SourceAuditTests(unittest.TestCase):
    def test_official_verified_registry_citation(self):
        row = {
            "text": ["ARI", "12", "S01"],
            "links": ["sources.html#S01"],
            "cells": [{"text": "ARI", "classes": set()}, {"text": "12", "classes": set()},
                      {"text": "S01", "classes": set()}],
        }
        registry = {"S01": {"status": "VERIFIED", "tier": "Official (league)",
                             "url": "https://www.nfl.com/injuries/"}}
        status, ids, urls = source_audit.classify(row, registry)
        self.assertEqual(status, "OFFICIAL_REGISTERED")
        self.assertEqual(ids, ["S01"])
        self.assertEqual(urls, ["https://www.nfl.com/injuries/"])

    def test_direct_link_is_registered_only_on_exact_url_match(self):
        registry = {"S01": {"status": "VERIFIED", "tier": "Official (league)",
                             "url": "https://www.nfl.com/injuries/"}}
        row = {"text": ["injury report", "listed"],
               "links": ["https://www.nfl.com/injuries/"],
               "cells": [{"text": "injury report", "classes": set()},
                         {"text": "listed", "classes": set()}]}
        self.assertEqual(source_audit.classify(row, registry)[0], "OFFICIAL_REGISTERED")
        row["links"] = ["https://www.nfl.com/some-other-page/"]
        self.assertEqual(source_audit.classify(row, registry)[0], "DIRECT_LINK_UNREGISTERED")

    def test_repository_generator_link_is_not_official_evidence(self):
        row = {"text": ["Seattle", "4"],
               "links": ["https://github.com/sassnarep3-star/FL1/blob/main/tools/site.py"],
               "cells": [{"text": "Seattle", "classes": set()},
                         {"text": "4", "classes": set()}]}
        status, _, _ = source_audit.classify(row, {})
        self.assertEqual(status, "REPOSITORY_LINK_ONLY")

    def test_unverified_or_third_party_registry_is_not_upgraded(self):
        row = {"text": ["line", "S02"], "links": ["sources.html#S02"],
               "cells": [{"text": "line", "classes": set()},
                         {"text": "S02", "classes": set()}]}
        status, _, _ = source_audit.classify(row, {
            "S02": {"status": "PARTIAL", "tier": "Third-party", "url": "https://example.org/data"}
        })
        self.assertEqual(status, "REGISTERED_NOT_VERIFIED")

    def test_blank_values_are_classified_as_blank_not_missing_source(self):
        row = {"text": ["—"], "links": [],
               "cells": [{"text": "—", "classes": {"blank"}}]}
        self.assertEqual(source_audit.classify(row, {})[0], "BLANK_NO_VALUE")

    def test_row_scanner_ignores_headers_and_classifies_body_rows(self):
        html = """<table><thead><tr><th>Team</th><th>Source</th></tr></thead>
        <tbody><tr><td>ARI</td><td><a href='sources.html#S01'>S01</a></td></tr>
        <tr><td class='blank'>—</td><td>—</td></tr></tbody></table>"""
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "page.html"), "w", encoding="utf-8") as f:
                f.write(html)
            registry = {"S01": {"status": "VERIFIED", "tier": "Official (league)",
                                 "url": "https://www.nfl.com/injuries/"}}
            rows = source_audit.audit_pages(root=root, sources=registry)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["status"], "OFFICIAL_REGISTERED")
        self.assertEqual(rows[1]["status"], "BLANK_NO_VALUE")


if __name__ == "__main__":
    unittest.main()
