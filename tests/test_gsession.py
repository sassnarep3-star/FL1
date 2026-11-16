"""Tests for the 2026-11-16 decision layer (session arena-fc0ed6e8-fl1).

Covers: engine/luck.py arithmetic, engine/ablation.py least-squares + leakage-free
feature construction + deterministic bootstrap, and the drift-alarm pin integrity.
"""
import csv
import json
import os
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.luck import build_panel, familywise, strategy_luck_rows  # noqa: E402
from engine.ablation import (  # noqa: E402
    ablate, build_rows, features, load_team_week_qb, paired_mae_diff_ci,
    predict, rolling_prior_margin, solve_normal_equations,
)


class LuckPanelTests(unittest.TestCase):
    SIG = [
        {"strategy_id": "A", "market": "spread",
         "signal": {"settled": 1000, "hit_rate": 0.55, "hit_ci_low": 0.52,
                    "reference_hurdle": 0.52381}},
        {"strategy_id": "B", "market": "total",
         "signal": {"settled": 500, "hit_rate": 0.50, "hit_ci_low": 0.46,
                    "reference_hurdle": 0.52381}},
    ]

    def test_below_hurdle_has_no_certification_target(self):
        rows = strategy_luck_rows(self.SIG, trials=2)
        self.assertEqual(rows[0]["strategy_id"], "A")
        self.assertIsNotNone(rows[0]["n_to_certify_if_real"])
        self.assertIsNone(rows[1]["n_to_certify_if_real"])

    def test_familywise_bar_is_bonferroni(self):
        rows = strategy_luck_rows(self.SIG, trials=2)
        fw = familywise(rows, trials=2, alpha=0.05)
        self.assertAlmostEqual(fw["bonferroni_p_bar"], 0.025, places=6)
        self.assertAlmostEqual(fw["sidak_p_bar"], 1 - 0.95 ** 0.5, places=4)
        self.assertFalse(fw["clears_familywise_bar"])

    def test_p_value_is_monotone_in_sample_size_direction(self):
        # a 55% hit over 4000 bets is far less luck-plausible than over 1000
        sig = [
            {"strategy_id": "small", "signal": {"settled": 1000, "hit_rate": 0.55,
                                                "reference_hurdle": 0.52381}},
            {"strategy_id": "large", "signal": {"settled": 4000, "hit_rate": 0.55,
                                                "reference_hurdle": 0.52381}},
        ]
        rows = strategy_luck_rows(sig, trials=2)
        self.assertLess(rows[1]["p_luck_alone_this_hot"], rows[0]["p_luck_alone_this_hot"])

    def test_panel_shape(self):
        panel = build_panel(self.SIG, trials=2, controls=[])
        self.assertEqual(len(panel["rows"]), 2)
        self.assertIn("familywise", panel)
        self.assertIn("A p-value is", panel["method"])


class AblationTests(unittest.TestCase):
    def test_solve_normal_equations_recovers_exact_line(self):
        X = [[1.0, 0.0], [1.0, 1.0], [1.0, 2.0], [1.0, 3.0]]
        y = [2.0, 4.0, 6.0, 8.0]  # y = 2 + 2x exactly
        beta = solve_normal_equations(X, y)
        self.assertAlmostEqual(beta[0], 2.0, places=8)
        self.assertAlmostEqual(beta[1], 2.0, places=8)

    def test_predict_and_features_shapes(self):
        row = {"prior_margin_diff": 3.0, "home_qb_class": 1, "away_qb_class": 0}
        self.assertEqual(len(features(row, False)), 2)
        self.assertEqual(len(features(row, True)), 6)
        self.assertEqual(features(row, True)[2], 1.0)
        self.assertEqual(features(row, True)[5], 0.0)

    def test_rolling_prior_margin_uses_only_past_games(self):
        games = [
            {"game_id": "g1", "season": "2024", "week": "1", "game_type": "REG",
             "home_team": "AAA", "away_team": "BBB", "home_score": "10", "away_score": "10"},
            {"game_id": "g2", "season": "2024", "week": "2", "game_type": "REG",
             "home_team": "AAA", "away_team": "CCC", "home_score": "20", "away_score": "10"},
        ]
        games.append({"game_id": "g3", "season": "2024", "week": "3", "game_type": "REG",
                      "home_team": "AAA", "away_team": "DDD", "home_score": "30", "away_score": "10"})
        games.append({"game_id": "g4", "season": "2024", "week": "4", "game_type": "REG",
                      "home_team": "AAA", "away_team": "EEE", "home_score": "40", "away_score": "10"})
        prior = rolling_prior_margin(games)
        by_team = {k: dict(v) for k, v in prior.items()}
        # the first three games have no prior-3 history (documented rule)
        self.assertIsNone(by_team[("2024", "AAA")]["g1"])
        self.assertIsNone(by_team[("2024", "AAA")]["g2"])
        # g4 prior = mean of margins from g1..g3 (0, +10, +20) = 10.0 - g4's own margin (+30) must NOT leak
        self.assertEqual(by_team[("2024", "AAA")]["g4"], 10.0)

    def test_paired_bootstrap_is_deterministic(self):
        a = [1.0, 2.0, 3.0, 4.0]
        b = [2.0, 2.0, 2.0, 2.0]
        r1 = paired_mae_diff_ci(a, b, n_boot=200, seed=7)
        r2 = paired_mae_diff_ci(a, b, n_boot=200, seed=7)
        self.assertEqual(r1, r2)
        self.assertEqual(r1["mae_diff"], 0.5)  # mean(a-b) = 0.5

    def test_ablate_runs_and_reports_both_shapes(self):
        # synthetic world where the availability feature has a true effect
        rows = []
        for i in range(600):
            season = "1999" if i < 400 else "2000"
            pm = (i % 7) - 3
            hq = i % 3
            aq = (i // 2 + 2) % 3  # not a deterministic function of hq (avoids collinearity)
            y = 2.0 + 0.5 * pm - 3.0 * (hq == 1) + 3.0 * (aq == 1)
            rows.append({"game_id": str(i), "season": season, "week": "1",
                         "y": y, "prior_margin_diff": pm,
                         "home_qb_class": hq, "away_qb_class": aq})
        res = ablate(rows, {"1999"}, {"1999"}, {"2000"}, "margin", seed=1)
        self.assertIn("with_availability", res)
        self.assertIn("holdout_difference", res)
        self.assertEqual(res["n_holdout"], 200)

    def test_load_team_week_qb_maps_classes(self):
        qb = load_team_week_qb([
            {"season": "2024", "week": "1", "team": "AAA", "qb_deficiency": "primary starter"},
            {"season": "2024", "week": "2", "team": "AAA", "qb_deficiency": "2nd different starter"},
            {"season": "2024", "week": "3", "team": "AAA", "qb_deficiency": "3rd-or-later different starter"},
            {"season": "2024", "week": "4", "team": "AAA", "qb_deficiency": "weird label"},
        ])
        self.assertEqual(qb[("2024", "1", "AAA")], 0)
        self.assertEqual(qb[("2024", "2", "AAA")], 1)
        self.assertEqual(qb[("2024", "3", "AAA")], 2)
        self.assertNotIn(("2024", "4", "AAA"), qb)


class DriftAlarmPinTests(unittest.TestCase):
    PINS_PATH = ROOT / "tools" / "verify_drift.py"

    def test_all_pinned_files_exist(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import verify_drift
        for pin in verify_drift.PINS:
            self.assertTrue((ROOT / pin[1]).exists(), pin[1])

    def test_drift_output_written_and_green(self):
        import subprocess
        proc = subprocess.run([sys.executable, str(ROOT / "tools" / "verify_drift.py")],
                              capture_output=True, text=True, cwd=str(ROOT))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        out = ROOT / "data" / "verification-drift.tsv"
        rows = list(csv.DictReader(open(out, encoding="utf-8"), delimiter="\t"))
        self.assertTrue(rows)
        self.assertTrue(all(r["status"] in ("PASS", "WARN") for r in rows),
                        [r for r in rows if r["status"] == "FAIL"])


class RegisterIntegrityTests(unittest.TestCase):
    """The new registers must be valid, complete and cross-referenced."""

    def test_readiness_has_a_row_for_every_requirement(self):
        reqs = json.load(open(ROOT / "data" / "requirements.json", encoding="utf-8"))
        readiness = json.load(open(ROOT / "data" / "readiness.json", encoding="utf-8"))
        landing_ids = {r["r_id"] for r in readiness["landing"]}
        self.assertEqual(landing_ids, {r["id"] for r in reqs})

    def test_every_strategy_has_two_sided_change_of_mind(self):
        strategies = json.load(open(ROOT / "data" / "strategies.json", encoding="utf-8"))
        for s in strategies:
            com = s.get("change_of_mind")
            self.assertTrue(com and com.get("upgrade") and com.get("downgrade"),
                            s["id"] + " missing two-sided change_of_mind")

    def test_announced_starters_never_publishes_an_unverified_start(self):
        doc = json.load(open(ROOT / "data" / "announced_starters.json", encoding="utf-8"))
        for r in doc["rows"]:
            if r.get("verified") is not True or "yes" not in (r.get("announced_start") or ""):
                self.assertEqual(r.get("announced_start"), "", r["id"])

    def test_luck_panel_matches_signal_register(self):
        sig = json.load(open(ROOT / "data" / "leaderboard_signal_staking.json", encoding="utf-8"))
        panel = json.load(open(ROOT / "data" / "luck_panel.json", encoding="utf-8"))
        self.assertEqual(len(panel["rows"]), len(sig["rows"]))

    def test_reserve_list_row_count_matches_raw_capture(self):
        tsv = list(csv.DictReader(open(ROOT / "data" / "reserve_list_2026-11.tsv",
                                       encoding="utf-8"), delimiter="\t"))
        raw = (ROOT / "raw" / "nfl-reserve-list-2026-11.md").read_text(encoding="utf-8")
        data_rows = [ln for ln in raw.splitlines()
                     if ln.startswith("| ") and "Reserve/Injured |" in ln]
        self.assertEqual(len(tsv), len(data_rows))

    def test_g18_registered(self):
        gates = json.load(open(ROOT / "data" / "validation_gates.json", encoding="utf-8"))
        self.assertIn("G-18", [r["g_id"] for r in gates["rows"]])


if __name__ == "__main__":
    unittest.main()
