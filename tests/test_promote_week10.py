"""Tests for the Q44 week-10 closeout artefacts (C1, 2026-11-17).

These tests pin BOTH halves of the staged state:

  * the closeout run itself — 14 finals, gates P1-P7 all PASS, dated
    side-reads present and arithmetically consistent; and
  * the decision NOT to roll the canonical feed forward — data/results.tsv,
    data/standings.tsv and data/schedule2026-d.csv must still be in their
    pre-promotion state until the Q44 owner chooses the canonical path.

If a future session executes the promotion (scripts/promote_week10.py
--execute --promote), these tests fail on purpose: the corpus contract moved,
so the pins (DR-03/DR-05, brief V6, N04, luck panels) and this file must all
be updated in the same commit, exactly as the runner's follow-up list says.
"""
import csv
import hashlib
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


def rows(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as fh:
        return [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]


class TestCloseoutRegister(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = load("week10_closeout.json")

    def test_all_14_finals_present(self):
        self.assertEqual(len(self.reg["finals"]), 14)
        self.assertEqual(len(self.reg["new_since_frozen_corpus"]), 13)
        for f in self.reg["finals"]:
            self.assertEqual(f["week"], 10)
            self.assertTrue(f["game_url"].startswith("https://www.nfl.com/games/"))
            self.assertEqual(f["source_id"], "S90")

    def test_every_gate_passed(self):
        self.assertEqual(len(self.reg["checks"]), 7)
        for c in self.reg["checks"]:
            self.assertEqual(c["result"], "PASS", c)

    def test_register_says_canonical_not_promoted(self):
        self.assertFalse(self.reg["canonical_promoted"])
        self.assertEqual(self.reg["frozen_corpus"]["rows"], 137)

    def test_frozen_corpus_hash_matches_file(self):
        with open(os.path.join(ROOT, "data", "results.tsv"), "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        # canonical must still be the pre-promotion corpus (see module docstring)
        self.assertEqual(self.reg["frozen_corpus"]["sha256"], digest)

    def test_late_finals_scores_match_capture(self):
        by = {(f["away"], f["home"]): f for f in self.reg["finals"]}
        self.assertEqual((by[("PIT", "CIN")]["awayPts"],
                          by[("PIT", "CIN")]["homePts"]), (18, 38))
        lac, bal = by[("LAC", "BAL")]["awayPts"], by[("LAC", "BAL")]["homePts"]
        self.assertGreaterEqual(lac + bal, 1)  # a played game, captured final


class TestDatedSideRead(unittest.TestCase):
    def test_results_read_is_150_and_append_only(self):
        staged = rows("results_2026-11-17.tsv")
        frozen = rows("results.tsv")
        self.assertEqual(len(frozen), 137)
        self.assertEqual(len(staged), 150)
        self.assertEqual(staged[:137], frozen)

    def test_week10_rows_complete(self):
        staged = rows("results_2026-11-17.tsv")
        w10 = [r for r in staged if r[0] == "10"]
        self.assertEqual(len(w10), 14)
        tnf = [r for r in w10 if r[2] == "WAS" and r[4] == "NYG"]
        self.assertEqual((tnf[0][3], tnf[0][4], tnf[0][5]), ("24", "NYG", "21"))
        pit = [r for r in w10 if r[2] == "PIT" and r[4] == "CIN"]
        self.assertEqual((pit[0][3], pit[0][5]), ("18", "38"))

    def test_standings_read_reproduces_from_results(self):
        stand = {r[0]: r for r in rows("standings_2026-11-17.tsv")}
        self.assertEqual(len(stand), 32)
        derived = {k: [0, 0, 0, 0, 0] for k in stand}  # w l t pf pa
        for r in rows("results_2026-11-17.tsv"):
            ap, hp = int(r[3]), int(r[5])
            for team, pf, pa in ((r[2], ap, hp), (r[4], hp, ap)):
                d = derived[team]
                d[3] += pf
                d[4] += pa
                d[0] += pf > pa
                d[1] += pf < pa
                d[2] += pf == pa
        for ab, s in stand.items():
            self.assertEqual(
                derived[ab], [int(s[1]), int(s[2]), int(s[3]), int(s[5]), int(s[6])],
                ab)


class TestCanonicalUntouched(unittest.TestCase):
    """The staged decision: canonical feed still the 137-game corpus."""

    def test_canonical_results_still_137(self):
        self.assertEqual(len(rows("results.tsv")), 137)

    def test_canonical_standings_untouched(self):
        std = rows("standings.tsv")
        self.assertEqual(len(std), 32)
        self.assertEqual(len(std[0]), 17)

    def test_schedule_feed_not_flipped(self):
        with open(os.path.join(ROOT, "data", "schedule2026-d.csv"),
                  newline="", encoding="utf-8") as fh:
            sched = list(csv.DictReader(fh))
        played = [r for r in sched if r["played"] == "yes"]
        self.assertEqual(len(played), 137)
        w10 = [r for r in sched if r["week"] == "10"]
        w10_played = [r for r in w10 if r["played"] == "yes"]
        self.assertEqual(len(w10), 14)
        self.assertEqual(len(w10_played), 1)  # TNF only, until --promote


if __name__ == "__main__":
    unittest.main()
