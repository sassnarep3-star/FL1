"""Tests for the N01-N05 sprint (2026-11-16, session arena-38a78804-fl1).

N01 decision-readiness table   data/decision_readiness.json
N02 change-our-mind fields     data/strategies.json
N03 injury-hub delta register  data/injury_hub_delta.json
N04 week-10 finals extension   data/week10_results_extension.json
N05 luck panel                 data/luck_panel.json
plus the S70-S72 source rows backing them.
"""

import csv
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


class TestN01DecisionReadiness(unittest.TestCase):
    def setUp(self):
        self.dec = load("decision_readiness.json")
        self.req = load("requirements.json")

    def test_one_row_per_requirement(self):
        self.assertEqual(len(self.dec["rows"]), len(self.req))
        self.assertEqual([r["id"] for r in self.dec["rows"]],
                         [r["id"] for r in self.req])

    def test_status_matches_register(self):
        status = {r["id"]: r["status"] for r in self.req}
        for row in self.dec["rows"]:
            self.assertEqual(row["status"], status[row["id"]])

    def test_blockers_cite_only_published_ids(self):
        q_ids = {q["id"] for q in load("questions.json")}
        f_ids = {f["id"] for f in load("flags.json")}
        for row in self.dec["rows"]:
            for ref in row["blocker_refs"]:
                self.assertTrue(ref in q_ids or ref in f_ids,
                                "%s cites unknown %s" % (row["id"], ref))

    def test_done_rows_have_no_blocker(self):
        for row in self.dec["rows"]:
            if row["status"] == "done":
                self.assertIsNone(row["blocker"], row["id"])
            else:
                self.assertTrue(row["blocker"], row["id"])
                self.assertTrue(row["clears"], row["id"])

    def test_status_counts_match_register(self):
        reg = {"done": 0, "other": 0}
        for r in self.req:
            reg["done" if r["status"] == "done" else "other"] += 1
        dec_done = sum(1 for r in self.dec["rows"] if r["status"] == "done")
        self.assertEqual(dec_done, reg["done"])
        self.assertEqual(len(self.dec["rows"]), len(self.req))


class TestN02ChangeOurMind(unittest.TestCase):
    def test_every_strategy_has_both_sides(self):
        strategies = load("strategies.json")
        self.assertEqual(len(strategies), 6)
        for s in strategies:
            self.assertTrue(s.get("raises_confidence", "").strip(), s["id"])
            self.assertTrue(s.get("lowers_confidence", "").strip(), s["id"])

    def test_blocked_strategies_state_the_gate(self):
        strategies = {s["id"]: s for s in load("strategies.json")}
        for sid in ("ST05", "ST06"):
            self.assertIn("joint", strategies[sid]["raises_confidence"].lower()
                          + strategies[sid]["lowers_confidence"].lower(), sid)


class TestN03InjuryHubDelta(unittest.TestCase):
    def setUp(self):
        self.delta = load("injury_hub_delta.json")

    def test_two_dated_reads(self):
        reads = self.delta["reads"]
        self.assertEqual(len(reads), 2)
        self.assertEqual(reads[0]["captured"], "2026-11-14")
        self.assertIn("2026-11-16", reads[1]["read_window_utc"])
        self.assertEqual(reads[0]["rows"], 345)
        self.assertEqual(reads[1]["rows"], 347)

    def test_delta_totals_consistent(self):
        d = self.delta["delta"]
        self.assertEqual(len(d["changed"]), 32)
        self.assertEqual(len(d["added"]), 2)
        self.assertEqual(len(d["removed"]), 0)
        self.assertEqual(sum(p["read2"] - p["read1"] for p in d["per_club_row_count_changes"]),
                         len(d["added"]) - len(d["removed"]))

    def test_changes_carry_old_and_new(self):
        designations = {"", "Out", "Doubtful", "Questionable"}
        practices = {"", "FULL", "LIMITED", "DNP"}
        for c in self.delta["delta"]["changed"]:
            self.assertIn(c["field"], ("injury", "practice", "game"))
            self.assertNotEqual(c["old"], c["new"])
            if c["field"] == "game":
                self.assertIn(c["old"], designations)
                self.assertIn(c["new"], designations)
            if c["field"] == "practice":
                self.assertIn(c["old"], practices)
                self.assertIn(c["new"], practices)

    def test_added_rows_are_baltimore(self):
        for a in self.delta["delta"]["added"]:
            self.assertEqual(a["team"], "BAL")

    def test_reserve_pointers_are_nfl_news(self):
        for p in self.delta["reserve_list_pointers"]:
            self.assertTrue(p["url"].startswith("https://www.nfl.com/news/"))


class TestN04Week10Extension(unittest.TestCase):
    def setUp(self):
        self.ext = load("week10_results_extension.json")

    def test_shape(self):
        self.assertEqual(len(self.ext["finals"]), 12)
        self.assertEqual(len(self.ext["pending"]), 2)
        self.assertEqual(self.ext["source_id"], "S78")  # re-issued from S71 at merge

    def test_tnf_corroborates_feed(self):
        tnf = [f for f in self.ext["finals"] if f["away"] == "WAS"]
        self.assertEqual(len(tnf), 1)
        self.assertEqual((tnf[0]["awayPts"], tnf[0]["homePts"]), (24, 21))
        results = list(csv.reader(
            open(os.path.join(ROOT, "data", "results.tsv"), encoding="utf-8"),
            delimiter="\t"))
        week10 = [r for r in results if r[0] == "10"]
        self.assertEqual([(r[2], r[3], r[4], r[5]) for r in week10],
                         [("WAS", "24", "NYG", "21")])

    def test_scores_are_integers_and_totals_match(self):
        for f in self.ext["finals"]:
            self.assertIsInstance(f["awayPts"], int)
            self.assertIsInstance(f["homePts"], int)
            self.assertEqual(f["total"], f["awayPts"] + f["homePts"])
            self.assertEqual(f["margin_home"], f["homePts"] - f["awayPts"])

    def test_pending_have_blank_scores_and_a_reason(self):
        for p in self.ext["pending"]:
            self.assertNotIn("awayPts", p)
            self.assertNotIn("homePts", p)
            self.assertTrue(p["status"], p["away"])
        self.assertEqual({p["away"] for p in self.ext["pending"]}, {"PIT", "LAC"})

    def test_every_row_links_official_pages(self):
        for f in self.ext["finals"] + self.ext["pending"]:
            self.assertTrue(f["game_url"].startswith("https://www.nfl.com/games/"))
            self.assertTrue(f["page_url"].startswith("https://www.nfl.com/schedules/"))


class TestN05LuckPanel(unittest.TestCase):
    def setUp(self):
        self.panel = load("luck_panel.json")
        self.src = load("leaderboard_signal_staking.json")

    def test_rows_match_register(self):
        self.assertEqual(len(self.panel["rows"]), 16)
        self.assertEqual([r["strategy_id"] for r in self.panel["rows"]],
                         [r["strategy_id"] for r in
                          sorted(self.src["rows"],
                                 key=lambda r: r["signal"]["signal_edge_lcb"],
                                 reverse=True)])

    def test_edge_lcb_is_ci_low_minus_hurdle(self):
        for r in self.panel["rows"]:
            self.assertAlmostEqual(r["edge_lcb"],
                                   r["hit_ci_low"] - r["reference_hurdle"],
                                   places=6)

    def test_headline_nothing_proven(self):
        h = self.panel["headlines"]
        self.assertEqual(h["proven"], 0)
        self.assertEqual(h["positive_roi_but_rejected_on_signal"],
                         h["positive_roi_entries"])

    def test_control_baseline_present(self):
        h = self.panel["headlines"]["control_baseline"]
        self.assertEqual(h["strategy_id"], "__CONTROL_MARKET")
        self.assertEqual(h["settled"], 5067)

    def test_carries_third_party_warning(self):
        self.assertIn("F19", self.panel["provenance"]["warning"])


class TestSourcesS70S72(unittest.TestCase):
    def test_new_source_rows_registered(self):
        with open(os.path.join(ROOT, "data", "sources.tsv"), encoding="utf-8") as fh:
            rows = {ln.split("\t")[0]: ln.split("\t")
                    for ln in fh.read().splitlines() if ln.strip() and not ln.startswith("#")}
        for sid in ("S77", "S78", "S79"):
            self.assertIn(sid, rows)
            self.assertEqual(rows[sid][6], "VERIFIED", sid)
            self.assertNotIn("nflverse", rows[sid][2], sid)
            self.assertTrue(rows[sid][3].startswith("https://www.nfl.com/"), sid)

    def test_counts(self):
        with open(os.path.join(ROOT, "data", "sources.tsv"), encoding="utf-8") as fh:
            rows = [ln for ln in fh.read().splitlines()
                    if ln.strip() and not ln.startswith("#")]
        # 68 rows from main (S01-S76) + this session's S77-S79
        self.assertEqual(len(rows), 71)


if __name__ == "__main__":
    unittest.main()
