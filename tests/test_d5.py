import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from engine import scoreboard_d5 as sb


class ScoreboardD5Tests(unittest.TestCase):
    def test_proper_scores(self):
        self.assertAlmostEqual(sb.brier([0.9, 0.1], [1, 0]), 0.01)
        self.assertAlmostEqual(sb.brier_skill([0.9, 0.1], [1, 0], [0.5, 0.5]), 0.96)

    def test_empty_and_invalid_inputs(self):
        with self.assertRaises(ValueError):
            sb.brier([], [])
        self.assertTrue(sb.log_loss([1.1], [1]) >= 0)  # probabilities are clipped at epsilon

    def test_sample_bar_is_reproducible_and_above_existing_corpus(self):
        n = sb.sample_for_edge(*sb.EDGE_FOR_POWER)
        self.assertGreater(n, 137)
        self.assertEqual(n, sb.sample_bars()["singles"])

    def test_cluster_bootstrap_reproducible(self):
        p = [0.8, 0.2, 0.7, 0.3]
        y = [1, 0, 1, 0]
        a = sb.cluster_bootstrap_skill(p, y, [0.5] * 4, ["a", "a", "b", "b"], reps=100, seed=7)
        b = sb.cluster_bootstrap_skill(p, y, [0.5] * 4, ["a", "a", "b", "b"], reps=100, seed=7)
        self.assertEqual(a, b)

    def test_unconfirmed_strategy_cannot_rank_or_qualify(self):
        registry = json.load(open(os.path.join(ROOT, "data", "strategy_registry_d5.json"), encoding="utf-8"))
        score = json.load(open(os.path.join(ROOT, "data", "scorecard_d5.json"), encoding="utf-8"))
        self.assertEqual(len(registry), 11)
        self.assertTrue(all(not x["registration"]["committed"] for x in registry))
        self.assertEqual(score["qualified_count"], 0)
        self.assertTrue(all(not e["qualified"] for e in score["registry"]))
        self.assertTrue(all(e["signal"]["n"] == 0 for e in score["registry"] if e["id"] != "D5S04"))

    def test_live_gate_hashes_and_results_reconciliation(self):
        result = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "verify_live_d5.py")],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_scorecard_keeps_signal_and_staking_distinct(self):
        score = json.load(open(os.path.join(ROOT, "data", "scorecard_d5.json"), encoding="utf-8"))
        for e in score["registry"]:
            self.assertIn("signal", e)
            self.assertIn("staking", e)
            self.assertIsNot(e["signal"], e["staking"])


if __name__ == "__main__":
    unittest.main()
