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
    """Four dated reads of the official hub; the register publishes the LATEST
    delta (read 3 -> read 4) and keeps read 1 -> read 2 and read 2 -> read 3
    under `history`. Every delta row is re-checked here against the verbatim
    raw captures."""

    READS = {
        1: "injuries-week10-2026.md",
        2: "injuries-week10-2026-read2.md",
        3: "injuries-week10-2026-read3.md",
        4: "injuries-week10-2026-read4.md",
    }
    PRACTICE_TEXT = {
        "FULL": "Full Participation in Practice",
        "LIMITED": "Limited Participation in Practice",
        "DNP": "Did Not Participate In Practice",
        "": "",
    }
    CELL = {"injury": 2, "practice": 3, "game": 4}

    def setUp(self):
        self.delta = load("injury_hub_delta.json")

    def _row_cells(self, read_no, team, player, pos):
        """Return the 5 cells of that player's row in a raw capture, or None."""
        path = os.path.join(ROOT, "raw", self.READS[read_no])
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                if not ln.startswith("| ["):
                    continue
                if ("| [" + player + "](") not in ln:
                    continue
                cells = [c.strip() for c in ln.strip().strip("|").split("|")]
                self.assertEqual(len(cells), 5, ln.strip())
                if cells[1] == pos:
                    return cells
        return None

    def test_four_dated_reads(self):
        reads = self.delta["reads"]
        self.assertEqual(len(reads), 4)
        self.assertEqual(reads[0]["captured"], "2026-11-14")
        self.assertIn("2026-11-16", reads[1]["read_window_utc"])
        self.assertIn("2026-11-17", reads[2]["read_window_utc"])
        self.assertIn("2026-11-17", reads[3]["read_window_utc"])
        self.assertEqual(reads[0]["rows"], 345)
        self.assertEqual(reads[1]["rows"], 347)
        self.assertEqual(reads[2]["rows"], 347)
        self.assertEqual(reads[3]["rows"], 347)
        self.assertEqual(reads[2]["source_id"], "S94")
        self.assertEqual(reads[3]["source_id"], "S97")

    def test_history_preserves_the_earlier_deltas(self):
        h = self.delta["history"]
        self.assertEqual(len(h), 2)
        d = h[0]
        self.assertEqual(d["older_label"], "read 1 (2026-11-14)")
        self.assertEqual(d["newer_label"], "read 2 (2026-11-16)")
        self.assertEqual(len(d["changed"]), 32)
        self.assertEqual(len(d["added"]), 2)
        self.assertEqual(len(d["removed"]), 0)
        d2 = h[1]
        self.assertEqual(d2["older_label"], "read 2 (2026-11-16)")
        self.assertEqual(len(d2["changed"]), 1)
        c2 = d2["changed"][0]
        self.assertEqual((c2["team"], c2["player"], c2["field"]),
                         ("NO", "Travis Etienne", "practice"))
        self.assertEqual((c2["old"], c2["new"]), ("FULL", "LIMITED"))

    def test_published_delta_is_read3_to_read4(self):
        d = self.delta["delta"]
        self.assertEqual(d["older_label"], "read 3 (2026-11-17 02:36Z)")
        self.assertEqual(d["newer_label"], "read 4 (2026-11-17 02:43Z)")
        self.assertEqual(len(d["changed"]), 2)
        self.assertEqual(len(d["added"]), 0)
        self.assertEqual(len(d["removed"]), 0)
        got = {(c["team"], c["player"], c["field"], c["old"], c["new"])
               for c in d["changed"]}
        self.assertEqual(got, {
            ("BUF", "Tyrell Shavers", "practice", "FULL", "LIMITED"),
            ("CIN", "Brian Parker II", "practice", "FULL", "DNP"),
        })

    def _check_pair(self, d, older_read, newer_read):
        for c in d["changed"]:
            self.assertIn(c["field"], ("injury", "practice", "game"))
            self.assertNotEqual(c["old"], c["new"])
            old_cells = self._row_cells(older_read, c["team"], c["player"], c["pos"])
            new_cells = self._row_cells(newer_read, c["team"], c["player"], c["pos"])
            self.assertIsNotNone(old_cells, c)
            self.assertIsNotNone(new_cells, c)
            idx = self.CELL[c["field"]]
            exp_old = self.PRACTICE_TEXT.get(c["old"], c["old"])
            exp_new = self.PRACTICE_TEXT.get(c["new"], c["new"])
            self.assertEqual(old_cells[idx], exp_old, c)
            self.assertEqual(new_cells[idx], exp_new, c)
        for a in d["added"]:
            self.assertIsNotNone(self._row_cells(newer_read, a["team"], a["player"], a["pos"]), a)
            self.assertIsNone(self._row_cells(older_read, a["team"], a["player"], a["pos"]), a)
        for r in d["removed"]:
            self.assertIsNotNone(self._row_cells(older_read, r["team"], r["player"], r["pos"]), r)
            self.assertIsNone(self._row_cells(newer_read, r["team"], r["player"], r["pos"]), r)

    def test_every_delta_row_ties_back_to_the_raw_captures(self):
        self._check_pair(self.delta["delta"], 3, 4)
        self._check_pair(self.delta["history"][0], 1, 2)
        self._check_pair(self.delta["history"][1], 2, 3)

    def test_per_club_counts_arithmetic(self):
        for d in [self.delta["delta"]] + self.delta["history"]:
            self.assertEqual(
                sum(p["newer"] - p["older"] for p in d["per_club_row_count_changes"]),
                len(d["added"]) - len(d["removed"]), d["between"])

    def test_added_rows_are_baltimore(self):
        for a in self.delta["history"][0]["added"]:
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
        self.assertEqual(self.ext["source_id"], "S81")  # re-issued twice: S71->S78->S81 at merges

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
        self.panel = load("luck_panel_signal.json")  # renamed at 2nd merge; main session owns luck_panel.json
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
        for sid in ("S80", "S81", "S82"):
            self.assertIn(sid, rows)
            self.assertEqual(rows[sid][6], "VERIFIED", sid)
            self.assertNotIn("nflverse", rows[sid][2], sid)
            self.assertTrue(rows[sid][3].startswith("https://www.nfl.com/"), sid)

    def test_counts(self):
        with open(os.path.join(ROOT, "data", "sources.tsv"), encoding="utf-8") as fh:
            rows = [ln for ln in fh.read().splitlines()
                    if ln.strip() and not ln.startswith("#")]
        # main (S01-S79, S53-S60 unused) + S80-S82 (session 38a78804)
        # + S83-S88 (session fc0ed6e8: renumbered second wave after both
        #   sessions independently claimed S70-S82 for different sources)
        # + S89-S91 (session arena/e97f05c3-fl1: Week 10 Sunday-night final and
        #   the 2026-11-17 standings read; S91 is the live, not-yet-final MNF game)
        # + S92 (row-level citation audit; repository-only, not an NFL source)
        # + S93 (Week 11 by-week schedule; arena/d50423eb)
        # + S94 (session 7ac4e12e: third dated injury-hub read, 2026-11-17)
        # + S95-S96 (session 7ac4e12e: Week 10 close-out schedule + standings
        #   reads, 2026-11-17)
        # + S97-S99 (session arena/a502c4e0-fl1: injury-hub read 4, week-10
        #   closeout schedule, post-MNF standings closeout)
        # + S100-S103 (session arena-58ccea26-fl1: 2026-11-19 Week 11 injury,
        #   standings/schedule reads and official schedule-release article)
        self.assertEqual(len(rows), 95)
if __name__ == "__main__":
    unittest.main()
