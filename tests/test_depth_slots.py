#!/usr/bin/env python3
"""
test_depth_slots.py — unit tests for engine/depth_slots.py (session arena/143300b4).

The point of this module is that it must NOT invent a starter. These tests
therefore check the two failure modes the brief names:

    * a slot the club published with two names at the first string must not be
      resolved to one of them;
    * a slot the club published with no name at the first string must not be
      resolved to the second string.

and one more that the previous implementation had:

    * a replacement must come from the SAME published slot group, never from a
      different line of the same slot label.

Run:  python3 -m unittest discover -s tests -q
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import depth_slots as ds  # noqa: E402


def group(unit="Offense", slot="TE", line=1, names=()):
    g = ds.SlotGroup(team="TST", unit=unit, slot=slot, line=line)
    g.names = [{"player": p, "rank": str(r), "note": ""} for p, r in names]
    return g


class TestSlotStates(unittest.TestCase):
    def test_single_slot_names_one_starter(self):
        g = group(names=[("A Player", 1), ("B Player", 2)])
        self.assertEqual(g.state, "single")
        self.assertEqual(g.starter_named, "yes")
        self.assertEqual([n["player"] for n in g.first_string], ["A Player"])

    def test_shared_slot_is_ambiguous_not_single(self):
        g = group(names=[("A Player", 1), ("B Player", 1), ("C Player", 2)])
        self.assertEqual(g.state, "shared")
        self.assertTrue(g.starter_named.startswith("ambiguous"))
        self.assertIn("2 names", g.starter_named)
        self.assertEqual(len(g.first_string), 2)

    def test_three_names_at_the_first_string_is_still_ambiguous(self):
        g = group(names=[("A", 1), ("B", 1), ("C", 1)])
        self.assertEqual(g.state, "shared")
        self.assertIn("3 names", g.starter_named)

    def test_empty_slot_names_no_starter(self):
        g = group(names=[("", 1), ("B Player", 2)])
        self.assertEqual(g.state, "empty")
        self.assertEqual(g.first_string, [])
        self.assertTrue(g.first_string_blank)
        self.assertTrue(g.starter_named.startswith("no -"))

    def test_slot_with_no_first_string_entry_at_all_is_empty(self):
        g = group(names=[("B Player", 2)])
        self.assertEqual(g.state, "empty")
        self.assertFalse(g.first_string_blank)


class TestReplacement(unittest.TestCase):
    def test_shared_slot_replacement_is_the_other_first_string(self):
        g = group(names=[("A Player", 1), ("B Player", 1), ("C Player", 2)])
        res = ds.resolve_replacement(g, "A Player", set())
        self.assertEqual(res["replacement"], "B Player")
        self.assertEqual(res["strings_lost"], 0)

    def test_second_string_costs_one_string(self):
        g = group(names=[("A Player", 1), ("B Player", 2)])
        res = ds.resolve_replacement(g, "A Player", set())
        self.assertEqual(res["replacement"], "B Player")
        self.assertEqual(res["strings_lost"], 1)

    def test_replacement_never_leaves_the_slot_group(self):
        """Two published lines of the same slot label are different positions."""
        line1 = group(line=1, names=[("A Player", 1), ("B Player", 2)])
        line2 = group(line=2, names=[("C Player", 1)])
        # the walker is handed the line-1 group only; C Player lives in line 2
        res = ds.resolve_replacement(line1, "A Player", set())
        self.assertEqual(res["replacement"], "B Player")
        self.assertNotEqual(res["replacement"], "C Player")

    def test_unavailable_names_are_skipped(self):
        g = group(names=[("A Player", 1), ("B Player", 2), ("C Player", 3)])
        res = ds.resolve_replacement(g, "A Player", {"B Player"})
        self.assertEqual(res["replacement"], "C Player")
        self.assertEqual(res["strings_lost"], 2)

    def test_no_further_name_is_reported_as_no_replacement(self):
        g = group(names=[("A Player", 1)])
        res = ds.resolve_replacement(g, "A Player", set())
        self.assertEqual(res["replacement"], "")
        self.assertIn("no further name", res["reason"])

    def test_absent_player_outside_the_group_is_reported(self):
        g = group(names=[("A Player", 1)])
        res = ds.resolve_replacement(g, "Someone Else", set())
        self.assertEqual(res["replacement"], "")
        self.assertIn("not in this slot group", res["reason"])


class TestCommittedCapture(unittest.TestCase):
    """Checks against the committed official capture, not against the code."""

    def setUp(self):
        self.groups = ds.build_groups(ds.load_depth_rows(ROOT))

    def test_group_count_is_stable(self):
        self.assertEqual(len(self.groups), 737)

    def test_every_group_has_a_state(self):
        for g in self.groups.values():
            self.assertIn(g.state, ("single", "shared", "empty"))

    def test_shared_and_empty_counts_are_stable(self):
        s = ds.summarise(self.groups)
        self.assertEqual(s["shared"], 19)
        self.assertEqual(s["empty"], 4)
        self.assertEqual(s["single"], 714)

    def test_kansas_city_lb_slot_carries_three_first_string_names(self):
        g = self.groups[("KC", "Defense", "LB", "1")]
        self.assertEqual(g.state, "shared")
        self.assertEqual(len(g.first_string), 3)

    def test_seattle_wr_slot_is_shared(self):
        g = self.groups[("SEA", "Offense", "WR", "1")]
        self.assertEqual(g.state, "shared")
        self.assertEqual([n["player"] for n in g.first_string],
                         ["Cooper Kupp", "Rashid Shaheed"])

    def test_no_group_promotes_a_second_string_to_the_first(self):
        for g in self.groups.values():
            if g.state == "empty":
                self.assertEqual(g.first_string, [])
                self.assertTrue(g.starter_named.startswith("no -"))

    def test_houston_is_absent_because_its_chart_is_an_image(self):
        self.assertNotIn("HOU", {g.team for g in self.groups.values()})


class TestPublishedFile(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(ROOT, "data", "depth_slots.tsv")

    def test_published_file_matches_the_committed_capture(self):
        import csv
        with open(self.path, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh, delimiter="\t"))
        groups = ds.build_groups(ds.load_depth_rows(ROOT))
        self.assertEqual(len(rows), len(groups))
        by_id = {r["slot_id"]: r for r in rows}
        for key, g in groups.items():
            r = by_id.get(g.slot_id)
            self.assertIsNotNone(r, "missing published row for %s" % (key,))
            self.assertEqual(r["state"], g.state)
            self.assertEqual(int(r["n_at_first_string"]), len(g.first_string))

    def test_every_published_row_carries_a_source_url_or_is_flagged(self):
        import csv
        with open(self.path, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh, delimiter="\t"))
        for r in rows:
            if not r["source_url"]:
                self.fail("published row %s has no source url" % r["slot_id"])


if __name__ == "__main__":
    unittest.main()
