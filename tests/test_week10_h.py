#!/usr/bin/env python3
"""H3 — Week 10 close-out (2026-11-17) tests.

Every published number in data/week10_results_extension.json["completion"] is
re-derived here from the raw captures and the canonical feed, independently of
the builder that produced it:

  * the 13 page finals vs the original 12-row extension + the one new final;
  * the live Monday-night card carries no scores anywhere it is published;
  * the record/point arithmetic (feed + extension + new final) vs BOTH dated
    standings captures, club by club;
  * the raw captures themselves (verbatim bullet lines, TSV rows);
  * flag F61 carries the dated correction (its original count/date claim did
    not match the official reads on record).
"""

import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


def read_tsv(rel, fields):
    path = os.path.join(ROOT, rel)
    rows = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh.read().splitlines():
            if not ln.strip() or ln.startswith("#"):
                continue
            c = ln.rstrip("\t").split("\t")
            c += [""] * (len(fields) - len(c))
            rows.append(dict(zip(fields, c)))
    return rows


class TestWeek10Completion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ext = load("week10_results_extension.json")
        cls.comp = cls.ext["completion"]

    def test_shape(self):
        self.assertEqual(self.comp["read"], "2026-11-17")
        self.assertIn("2026-11-17T02:45:45Z", self.comp["read_window_utc"])
        self.assertIn("2026-11-17T02:46:39Z", self.comp["read_window_utc"])
        self.assertEqual(self.comp["source_ids"], ["S90", "S91"])
        self.assertEqual(self.comp["finals_on_page"], 13)
        self.assertEqual(len(self.comp["page_finals"]), 13)
        self.assertTrue(all(c for c in self.comp["checks"].values()))
        self.assertGreaterEqual(len(self.comp["checks"]), 6)

    def test_page_finals_vs_original_extension(self):
        ext = {(f["away"], f["awayPts"], f["home"], f["homePts"])
               for f in self.ext["finals"]}
        page = {(f["away"], f["awayPts"], f["home"], f["homePts"])
                for f in self.comp["page_finals"]}
        self.assertEqual(page - ext, {("PIT", 18, "CIN", 38)})
        self.assertEqual(ext - page, set())

    def test_new_final_row(self):
        nf = self.comp["new_final"]
        self.assertEqual((nf["away"], nf["awayPts"]), ("PIT", 18))
        self.assertEqual((nf["home"], nf["homePts"]), ("CIN", 38))
        self.assertEqual(nf["total"], 56)
        self.assertEqual(nf["margin_home"], 20)
        self.assertEqual(nf["source_id"], "S90")
        self.assertEqual(nf["date"], "2026-11-15")
        self.assertIn("steelers-at-bengals-2026-reg-10", nf["game_url"])

    def test_live_game_has_no_scores_anywhere(self):
        sl = self.comp["still_live"]
        self.assertEqual((sl["away"], sl["home"]), ("LAC", "BAL"))
        self.assertNotIn("awayPts", sl)
        self.assertNotIn("homePts", sl)
        self.assertIn("Q2", sl["status"])
        # and it is not a row of any results table in the repo's raw captures
        cap = open(os.path.join(ROOT, "raw",
                                "schedule-results-2026-week10-complete.md"),
                   encoding="utf-8").read()
        self.assertIn("- [Chargers 17, Ravens 7, Q2, ESPN]", cap)
        tsv = read_tsv("raw/schedule-results-2026-week10-complete.md",
                       ["week", "date", "away", "away_pts", "home", "home_pts", "note"])
        self.assertFalse([r for r in tsv if r["away"] == "LAC" or r["home"] == "LAC"])

    def test_record_and_points_arithmetic_vs_both_standings_reads(self):
        results = read_tsv("data/results.tsv",
                           ["week", "date", "away", "awayPts", "home", "homePts"])
        rec, pf_pa = {}, {}
        games = [(r["away"], int(r["awayPts"]), r["home"], int(r["homePts"]))
                 for r in results]
        # extension finals except the TNF duplicate already in the feed
        for f in self.ext["finals"]:
            if (f["away"], f["home"]) == ("WAS", "NYG"):
                continue
            games.append((f["away"], f["awayPts"], f["home"], f["homePts"]))
        nf = self.comp["new_final"]
        games.append((nf["away"], nf["awayPts"], nf["home"], nf["homePts"]))
        for a, ap, h, hp in games:
            for team, pf, pa in ((a, ap, hp), (h, hp, ap)):
                w, l, t = rec.get(team, (0, 0, 0))
                rec[team] = (w + (pf > pa), l + (pf < pa), t + (pf == pa))
                p, q = pf_pa.get(team, (0, 0))
                pf_pa[team] = (p + pf, q + pa)

        stand3 = {r["abbr"]: r for r in read_tsv(
            "raw/standings-2026-20261117.tsv", ["abbr", "w", "l", "t", "pf", "pa"])}
        self.assertEqual(len(stand3), 32)
        for ab, r in stand3.items():
            got = (rec[ab], pf_pa[ab])
            want = ((int(r["w"]), int(r["l"]), int(r["t"])),
                    (int(r["pf"]), int(r["pa"])))
            self.assertEqual(got, want, ab)

        # the pre-SNF read must differ ONLY for PIT and CIN (the new final)
        stand2 = {r["abbr"]: r for r in read_tsv(
            "raw/standings-2026-20261116.tsv", ["abbr", "w", "l", "t", "pf", "pa"])}
        self.assertEqual(len(stand2), 32)
        moved = {ab for ab in stand3
                 if (stand2[ab]["w"], stand2[ab]["l"], stand2[ab]["t"],
                     stand2[ab]["pf"], stand2[ab]["pa"]) !=
                    (stand3[ab]["w"], stand3[ab]["l"], stand3[ab]["t"],
                     stand3[ab]["pf"], stand3[ab]["pa"])}
        self.assertEqual(moved, {"PIT", "CIN"})
        self.assertEqual((stand3["PIT"]["w"], stand3["PIT"]["l"]), ("6", "3"))
        self.assertEqual((stand3["CIN"]["w"], stand3["CIN"]["l"]), ("7", "2"))

    def test_verbatim_bullet_lines_present_and_counted(self):
        cap = open(os.path.join(ROOT, "raw",
                                "schedule-results-2026-week10-complete.md"),
                   encoding="utf-8").read()
        bullets = re.findall(r"^- \[[^\]]+\]\(https://www\.nfl\.com/games/[^)]+\)$",
                             cap, flags=re.M)
        self.assertEqual(len(bullets), 14)
        finals = [b for b in bullets if ", FINAL, " in b]
        self.assertEqual(len(finals), 13)
        self.assertTrue(any("Steelers 18, Bengals 38, FINAL" in b for b in finals))

    def test_f61_carries_the_dated_correction(self):
        flags = load("flags.json")
        rows = flags if isinstance(flags, list) else flags.get("flags")
        f61 = [r for r in rows if r["id"] == "F61"]
        self.assertEqual(len(f61), 1)
        self.assertIn("UPDATE 2026-11-17", f61[0]["detail"])
        self.assertIn("13 finals + 1 live", f61[0]["detail"])
        self.assertIn("S90", f61[0]["sourceIds"])


if __name__ == "__main__":
    unittest.main()
