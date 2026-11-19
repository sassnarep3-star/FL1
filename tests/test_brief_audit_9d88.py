"""Tests for session arena-9d880d91-fl1 (2026-11-19): brief re-audit + fresh reads.

No network, no pandas. Every assertion recomputes from committed files.
"""

import csv
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def D(*parts):
    return os.path.join(ROOT, *parts)


def load_json(name):
    with open(D("data", name), encoding="utf-8") as fh:
        return json.load(fh)


class BriefAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_json("brief_audit_9d88.json")
        cls.rows = {r["id"]: r for r in cls.audit["rows"]}
        cls.ev = cls.audit["evidence"]

    def test_row_count(self):
        self.assertEqual(len(self.audit["rows"]), 59)

    def test_six_stale_corrected(self):
        stale = [r for r in self.audit["rows"] if r["verdict"] == "stale-corrected"]
        self.assertEqual(len(stale), 6)
        self.assertEqual({r["id"] for r in stale},
                         {"R37", "R47", "R55", "R83", "R44", "R76"})

    def test_r37_change_of_mind_exists(self):
        strat = load_json("strategies.json")
        n = sum(1 for s in strat
                if isinstance(s.get("change_of_mind"), dict)
                and s["change_of_mind"].get("upgrade")
                and s["change_of_mind"].get("downgrade"))
        self.assertEqual(n, 6)
        self.assertEqual(self.rows["R37"]["audited_status"], "done")
        self.assertEqual(self.ev["strategies_with_two_sided_change_of_mind"], "6 of 6")

    def test_r47_ablations_run_ci_contains_zero(self):
        ab = load_json("ablations.json")
        for target in ("margin", "total"):
            d = ab["ablations"][target]["holdout_difference"]
            self.assertTrue(d["ci_contains_zero"])
            self.assertEqual(d["n_holdout"], 895)
        self.assertEqual(self.rows["R47"]["audited_status"], "done")

    def test_r55_gate_enforced(self):
        with open(D("data", "market", "correlations_published.tsv"), encoding="utf-8") as fh:
            pub = [l for l in fh if l.strip()]
        with open(D("data", "market", "correlations_held.tsv"), encoding="utf-8") as fh:
            held = [l for l in fh if l.strip()]
        self.assertEqual(len(pub) - 1, 3)
        self.assertEqual(len(held) - 1, 4)
        self.assertEqual(self.rows["R55"]["audited_status"], "done")

    def test_r83_reserve_list_partial(self):
        with open(D("data", "reserve_list_2026-11.tsv"), encoding="utf-8") as fh:
            n = sum(1 for l in fh if l.strip()) - 1
        self.assertEqual(n, 25)
        self.assertEqual(self.rows["R83"]["audited_status"], "partial")

    def test_r44_block_present_but_chip_miswired(self):
        html = open(D("schedule.html"), encoding="utf-8").read()
        self.assertIn("league's schedule-release announcement", html.lower())
        self.assertIn('href="sources.html#s103"', html.lower())
        self.assertEqual(self.rows["R44"]["audited_status"], "done")
        self.assertEqual(self.ev["S86_title"],
                         "nflverse/nfldata win_totals feed (season win totals, both sides)")
        ids = {x["id"] for x in self.audit["irregularities"]}
        self.assertIn("J-F1", ids)

    def test_r76_control_partial(self):
        with open(D("data", "leaderboard.csv"), encoding="utf-8", newline="") as fh:
            lb = list(csv.DictReader(fh))
        # K1 (arena/9fccbb0e-fl1) added the random and favourites-only controls: 3 control rows now.
        self.assertEqual(sum(1 for r in lb if r["strategy_id"].startswith("__CONTROL")), 3)
        self.assertEqual(sum(1 for r in lb if "RANDOM" in r["strategy_id"].upper()), 1)
        self.assertEqual(self.rows["R76"]["audited_status"], "partial")

    def test_confirmed_rows_unchanged(self):
        for rid in ("R40", "R39", "R29", "R33", "R52", "R67", "R60", "R61"):
            self.assertEqual(self.rows[rid]["verdict"], "confirmed", rid)
            self.assertEqual(self.rows[rid]["audited_status"],
                             self.rows[rid]["published_status"], rid)

    def test_irregularities_present(self):
        ids = {x["id"] for x in self.audit["irregularities"]}
        self.assertEqual(ids, {"J-F1", "J-F2", "J-F3", "J-F4", "J-F5"})

    def test_page_rendered(self):
        html = open(D("brief-audit.html"), encoding="utf-8").read()
        self.assertIn("Brief Audit", html)
        self.assertIn("stale-corrected", html)
        idx = open(D("index.html"), encoding="utf-8").read()
        self.assertIn("brief-audit.html", idx)


class FreshReadsTest(unittest.TestCase):
    def test_standings_live_matches_closeout(self):
        def load(path):
            rows = []
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("#") or not line.strip():
                        continue
                    rows.append(line.rstrip("\n").split("\t"))
            return {r[0]: r for r in rows}
        live = load(D("raw", "live", "2026-11-19-standings-league-reg.tsv"))
        close = load(D("data", "standings_2026-11-17-closeout.tsv"))
        self.assertEqual(len(live), 32)
        self.assertEqual(live, close)

    def test_slate_identical(self):
        def slate(path):
            with open(path, encoding="utf-8") as fh:
                return [l.rstrip("\n") for l in fh if not l.startswith("#") and l.strip()]
        a = slate(D("raw", "live", "2026-11-19-week11-slate.tsv"))
        b = slate(D("raw", "live", "2026-11-17-week11-slate.tsv"))
        self.assertEqual(len(a), 13)
        self.assertEqual(a, b)

    def test_week11_injury_read_parses(self):
        # reuse the verifier's parser by importing the script as a module
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "verify_9d88", D("scripts", "verify_9d88.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        rows = mod.parse_injuries(D("raw", "injuries-week11-2026-read1-9d88.md"))
        self.assertEqual(len(rows), 253)
        self.assertEqual(len({r["team"] for r in rows}), 24)
        self.assertEqual({r["team"] for r in rows if r["game"]}, {"IND", "HOU"})
        keys = [(r["team"], r["player"], r["pos"]) for r in rows]
        self.assertEqual(len(set(keys)), len(keys))
        # main's independent capture (PR #63, TSV shape) must agree row-for-row
        theirs = []
        with open(D("raw", "injuries-week11-2026-read1.md"), encoding="utf-8") as fh:
            for line in fh:
                p = line.rstrip("\n").split("\t")
                if len(p) == 6 and p[0].isupper() and len(p[0]) in (2, 3):
                    theirs.append(("ARI" if p[0] == "AZ" else p[0], p[1], p[2], p[3], p[4], p[5]))
        mine = [(r["team"], r["player"], r["pos"], r["injury"], r["practice"], r["game"]) for r in rows]
        self.assertEqual(len(theirs), 253)
        self.assertEqual(set(theirs), set(mine))

    def test_verification_tsv_all_pass(self):
        with open(D("data", "verification-9d88.tsv"), encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh, delimiter="\t"))
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r["status"] == "PASS" for r in rows))


if __name__ == "__main__":
    unittest.main()
