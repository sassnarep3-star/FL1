"""Regression tests for the 2026-11-17 Week 10 results read (session arena/e97f05c3-fl1, task H1).

Reads only the committed files. The reconciliation itself is re-run by
scripts/verify_results_2026_11_17.py; here we check that the committed artefacts
still say what the official reads said.
"""
import csv
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, *p)


def lines(path):
    with open(path, encoding="utf-8") as fh:
        return [ln.rstrip("\n") for ln in fh if ln.strip()]


class ResultsRead20261117(unittest.TestCase):
    def test_new_read_is_old_read_plus_exactly_one_game(self):
        old = lines(D("data", "results_2026-11-16.tsv"))
        new = lines(D("data", "results_2026-11-17.tsv"))
        self.assertEqual(len(old), 148)
        self.assertEqual(len(new), 149)
        self.assertEqual(new[:-1], old)
        self.assertEqual(new[-1], "10\t2026-11-15\tPIT\t18\tCIN\t38")

    def test_monday_night_game_is_not_recorded(self):
        for name in ("results_2026-11-16.tsv", "results_2026-11-17.tsv"):
            for ln in lines(D("data", name)):
                f = ln.split("\t")
                self.assertFalse({f[2], f[4]} == {"LAC", "BAL"} and f[1] == "2026-11-16",
                                 "Monday night LAC@BAL must not be recorded while it is live")

    def test_frozen_corpus_is_still_a_prefix(self):
        corpus = lines(D("data", "results.tsv"))
        new = lines(D("data", "results_2026-11-17.tsv"))
        self.assertEqual(len(corpus), 137)
        self.assertEqual(new[:137], corpus)

    def test_standings_have_32_clubs_and_match_the_games(self):
        rows = [ln.split("\t") for ln in lines(D("data", "standings_2026-11-17.tsv"))]
        self.assertEqual(len(rows), 32)
        games = [ln.split("\t") for ln in lines(D("data", "results_2026-11-17.tsv"))]
        w = {r[0]: 0 for r in rows}; l = dict(w); t = dict(w); pf = dict(w); pa = dict(w)
        for _, _, a, ap, h, hp in games:
            ap, hp = int(ap), int(hp)
            pf[a] += ap; pa[a] += hp; pf[h] += hp; pa[h] += ap
            if ap > hp: w[a] += 1; l[h] += 1
            elif hp > ap: w[h] += 1; l[a] += 1
            else: t[a] += 1; t[h] += 1
        for r in rows:
            a = r[0]
            self.assertEqual((w[a], l[a], t[a], pf[a], pa[a]),
                             (int(r[1]), int(r[2]), int(r[3]), int(r[5]), int(r[6])), a)

    def test_recorded_verification_is_all_pass_and_open_item_is_open(self):
        with open(D("data", "verification-2026-11-17.tsv"), encoding="utf-8") as fh:
            rows = list(csv.reader(fh, delimiter="\t"))
        body = rows[1:]
        res = {r[0]: r[2] for r in body}
        for cid in ("H-R1", "H-R2", "H-R3", "H-R4", "H-R5"):
            self.assertEqual(res[cid], "PASS", cid)
        self.assertEqual(res["H-N1"], "OPEN")

    def test_flag_and_sources_registered(self):
        flags = {f["id"]: f for f in json.load(open(D("data", "flags.json"), encoding="utf-8"))}
        self.assertIn("F67", flags)
        src_ids = {ln.split("\t")[0] for ln in lines(D("data", "sources.tsv"))}
        for sid in ("S89", "S90", "S91"):
            self.assertIn(sid, src_ids)


if __name__ == "__main__":
    unittest.main()
