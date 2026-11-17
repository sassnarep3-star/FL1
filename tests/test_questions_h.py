#!/usr/bin/env python3
"""H4 — answer-layer tests for data/questions.json (2026-11-17).

The answers layer must be complete, internally consistent and cross-linked:
every row answered, states counted, every register id an answer cites must
exist, and the Q35/Q45 duplication the pass discovered must be on record.
"""

import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-11-17"
STATES = {"answered", "partial", "open"}
# every answer must cite something checkable: a register id or a committed path
CITE = re.compile(r"\b(?:D-\d\d|S\d\d|F\d\d|Q\d\d|SG\d\d)\b|\.\./|"
                  r"[\w/]+\.(?:json|tsv|csv|py|html|md)\b")


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


class TestQuestionAnswers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q = load("questions.json")
        if isinstance(cls.q, dict):
            cls.q = cls.q.get("questions") or cls.q["rows"]
        cls.flags = load("flags.json")
        if isinstance(cls.flags, dict):
            cls.flags = cls.flags.get("flags") or cls.flags["rows"]
        cls.flag_ids = {f["id"] for f in cls.flags}
        cls.q_ids = {r["id"] for r in cls.q}

    def test_all_45_rows_answered(self):
        self.assertEqual(len(self.q), 45)
        for r in self.q:
            self.assertIn("answer_state", r, r["id"])
            self.assertIn(r["answer_state"], STATES, r["id"])
            self.assertTrue(r.get("answer", "").strip(), r["id"])
            self.assertEqual(r.get("answer_date"), DATE, r["id"])

    def test_state_counts(self):
        from collections import Counter
        c = Counter(r["answer_state"] for r in self.q)
        self.assertEqual(c["answered"], 12)
        self.assertEqual(c["partial"], 15)
        self.assertEqual(c["open"], 18)

    def test_every_answer_cites_something_checkable(self):
        for r in self.q:
            self.assertRegex(r["answer"], CITE, r["id"])

    def test_cited_ids_resolve(self):
        for r in self.q:
            for ref in re.findall(r"\b(?:Q|F|SG)\d\d\b", r["answer"]):
                if ref.startswith("Q"):
                    self.assertIn(ref, self.q_ids, "%s cites missing %s" % (r["id"], ref))
                elif ref.startswith("F"):
                    self.assertIn(ref, self.flag_ids, "%s cites missing %s" % (r["id"], ref))
                else:
                    sugg = load("suggestions.json")
                    if isinstance(sugg, dict):
                        sugg = sugg.get("suggestions") or sugg["rows"]
                    self.assertIn(ref, {s["id"] for s in sugg},
                                  "%s cites missing %s" % (r["id"], ref))

    def test_open_answers_name_the_blocker(self):
        """Every open/partial answer must state what would settle it — a
        decision, a source, or a named missing dataset — not just assert
        ignorance."""
        MUST_MENTION = ("open", "decision", "owner", "source", "blocked",
                        "missing", "until", "pending", "ratify", "chooses",
                        "chosen", "decided", "clears", "clearing")
        for r in self.q:
            if r["answer_state"] == "answered":
                continue
            low = r["answer"].lower()
            self.assertTrue(any(w in low for w in MUST_MENTION),
                            "%s (%s) names no clearing path" % (r["id"],
                                                                r["answer_state"]))

    def test_q45_duplication_on_record(self):
        d = {r["id"]: r for r in self.q}
        self.assertEqual(d["Q35"]["question"], d["Q45"]["question"])
        f67 = [f for f in self.flags if f["id"] == "F67"]
        self.assertEqual(len(f67), 1)
        self.assertIn("Q45", f67[0]["item"])
        self.assertIn("F67", d["Q45"]["answer"])
        self.assertIn("Q35", d["Q45"]["answer"])

    def test_suggestions_sg48_sg49_exist(self):
        sugg = load("suggestions.json")
        if isinstance(sugg, dict):
            sugg = sugg.get("suggestions") or sugg["rows"]
        ids = {s["id"] for s in sugg}
        self.assertIn("SG48", ids)
        self.assertIn("SG49", ids)


if __name__ == "__main__":
    unittest.main()
