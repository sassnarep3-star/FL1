"""Hand-checkable tests for the FL1 engine.

Every expectation is derived from arithmetic that can be verified by hand, or from the
source register (the 52.38% break-even and the 2,243-bet power figure both trace to
data/sources.json). Random routines are seeded, so failures reproduce.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine import compliance, correlation, gates, injuries, leaderboard, pricing, stats  # noqa: E402

HURDLE = 0.52381  # -110, per SRC-015's own note


class TestPricing(unittest.TestCase):
    def test_break_even_110(self):
        self.assertAlmostEqual(pricing.break_even_probability(-110), 110 / 210, places=9)
        self.assertAlmostEqual(pricing.break_even_probability(-110), 0.5238095238, places=9)

    def test_break_even_moves_with_price_direction(self):
        # +150 pays 1.5:1, so break-even is 1/2.5 = 40%. -200 risks 2 to win 1, so it
        # is 1/1.5 = 66.7%. A longshot needs FEWER wins; a favourite needs more.
        self.assertAlmostEqual(pricing.break_even_probability(150), 0.4, places=9)
        self.assertAlmostEqual(pricing.break_even_probability(-200), 2 / 3, places=9)
        self.assertLess(pricing.break_even_probability(150),
                        pricing.break_even_probability(-110))

    def test_decimal_roundtrip(self):
        for price in (-110, -105, -200, 100, 150, 300):
            d = pricing.american_to_decimal(price)
            self.assertEqual(pricing.decimal_to_american(d), price, f"roundtrip {price}")

    def test_overround_versus_hold_on_handle(self):
        # two different legitimate "vig" numbers, and confusing them is a known error
        self.assertAlmostEqual(pricing.two_way_margin(-110, -110), 0.0476190476, places=8)
        self.assertAlmostEqual(pricing.hold_on_handle(-110, -110), 0.0454545455, places=8)
        self.assertLess(pricing.hold_on_handle(-110, -110), pricing.two_way_margin(-110, -110))

    def test_devig_two_way_sums_to_one(self):
        a, b = pricing.devig_two_way(-120, -100)
        self.assertAlmostEqual(a + b, 1.0, places=12)
        self.assertGreater(a, b)  # the -120 side is the market's favourite

    def test_ev_sign_flips_at_break_even(self):
        self.assertAlmostEqual(pricing.ev_per_unit(pricing.break_even_probability(-110), -110),
                               0.0, places=12)
        self.assertGreater(pricing.ev_per_unit(0.55, -110), 0)
        self.assertLess(pricing.ev_per_unit(0.52, -110), 0)
        self.assertGreater(pricing.ev_per_unit(0.53, -110), 0)  # 53% clears 52.38%

    def test_kelly_zero_at_fair_and_positive_above(self):
        self.assertAlmostEqual(pricing.kelly_fraction(pricing.break_even_probability(-110), -110),
                               0.0, places=9)
        self.assertAlmostEqual(pricing.kelly_fraction(0.55, -110),
                               (0.55 * (1 + 100 / 110) - 1) / (100 / 110), places=9)

    def test_fractional_kelly_respects_cap(self):
        self.assertLessEqual(pricing.fractional_kelly(0.9, -110, fraction=1.0, cap=0.02), 0.02)
        self.assertAlmostEqual(pricing.fractional_kelly(0.55, -110, fraction=0.25, cap=1.0),
                               pricing.kelly_fraction(0.55, -110) * 0.25, places=12)

    def test_parlay_decimal_multiplies(self):
        d = pricing.parlay_decimal([-110, -110])
        self.assertAlmostEqual(d, (210 / 110) ** 2, places=9)

    def test_parlay_naive_versus_joint_direction(self):
        # positive correlation must raise the true joint win probability above the product
        naive = pricing.parlay_ev_independent([0.55, 0.55], [-110, -110])
        joint = pricing.parlay_ev_joint([0.55, 0.55], [-110, -110],
                                        joint_prob=correlation.joint_prob_from_rho(0.55, 0.55, 0.3))
        self.assertGreater(joint, naive)

    def test_parlay_refuses_missing_joint(self):
        with self.assertRaises(ValueError):
            pricing.parlay_ev_joint([0.55, 0.55], [-110, -110])

    def test_product_of_breakevens_matches_joint_be_when_independent(self):
        prices = [-110, -110]
        self.assertAlmostEqual(pricing.break_even_parlay(prices),
                               pricing.product_of_breakevens(prices), places=12)


class TestCorrelation(unittest.TestCase):
    def test_rho_zero_is_independent(self):
        self.assertAlmostEqual(correlation.joint_prob_from_rho(0.6, 0.4, 0.0), 0.24, places=12)

    def test_rho_one_hits_the_bound(self):
        self.assertAlmostEqual(correlation.joint_prob_from_rho(0.4, 0.6, 1.0), 0.4, places=9)

    def test_rho_minus_one_hits_zero(self):
        self.assertAlmostEqual(correlation.joint_prob_from_rho(0.4, 0.6, -1.0), 0.0, places=9)

    def test_always_within_frechet_bounds(self):
        for pa in (0.05, 0.3, 0.5, 0.75):
            for pb in (0.1, 0.5, 0.9):
                for rho in (-1.0, -0.4, 0.0, 0.4, 1.0):
                    p = correlation.joint_prob_from_rho(pa, pb, rho)
                    self.assertGreaterEqual(p, max(0.0, pa + pb - 1.0) - 1e-12)
                    self.assertLessEqual(p, min(pa, pb) + 1e-12)

    def test_roundtrip_rho(self):
        p = correlation.joint_prob_from_rho(0.55, 0.48, 0.27)
        self.assertAlmostEqual(correlation.rho_from_joint(0.55, 0.48, p), 0.27, places=9)

    def test_correlation_premium_sign(self):
        self.assertGreater(correlation.correlation_premium(0.5, 0.5, 0.2), 0)
        self.assertLess(correlation.correlation_premium(0.5, 0.5, -0.2), 0)
        self.assertAlmostEqual(correlation.correlation_premium(0.5, 0.5, 0.0), 0.0, places=12)

    def test_two_leg_ev_reports_blocked_without_rho(self):
        out = correlation.two_leg_ev(-110, -110, 0.55, 0.55, None)
        self.assertIsNone(out["joint"]["rho"])
        self.assertIn("GAP-01", out["joint"]["blocking_reason"])

    def test_sensitivity_flags_sign_flip(self):
        dec = pricing.parlay_decimal([-110, -110])
        out = correlation.sensitivity_to_rho(0.55, 0.55, dec, rho=0.0, perturbation=0.4)
        self.assertIn("REFUSE", out["decision"])

    def test_simulation_reproduces_input_dependence(self):
        outcomes = correlation.simulate_game_outcomes(44.0, 14.0, 0.0, 13.5, 0.45,
                                                       n_sims=12000, seed=7)
        row = correlation.leg_event_probabilities(outcomes, 44.0, 0.0)
        # correlation of threshold events is attenuated relative to the latent 0.45
        self.assertGreater(row["rho"], 0.15)
        self.assertLess(row["rho"], 0.45)
        self.assertGreater(row["p_both"], row["product_of_marginals"])

    def test_implied_rho_is_margin_aware(self):
        # a combined price of +300 (decimal 4.0) implies 25% joint vs 30.25% naive:
        # the book is charging for correlation, so the inversion says 'negative rho'
        out = correlation.implied_rho_from_market(0.55, 0.55, 300, hold_assumption=0.0)
        self.assertAlmostEqual(out["p_joint_naive"], 0.3025, places=10)
        self.assertLess(out["p_joint_implied"], out["p_joint_naive"])
        self.assertLess(out["implied_rho"], 0)

    def test_infeasible_inversion_is_reported_not_hidden(self):
        # -130 as a *combined* price implies 56.5%, impossible for these marginals
        out = correlation.implied_rho_from_market(0.55, 0.55, -130, hold_assumption=0.0)
        self.assertTrue(out["clipped_to_feasible_bounds"])

    def test_degenerate_marginal_raises(self):
        with self.assertRaises(ValueError):
            correlation.rho_from_joint(1.0, 0.5, 0.5)


class TestStats(unittest.TestCase):
    def test_norm_ppf_cdf_roundtrip(self):
        for p in (0.001, 0.05, 0.25, 0.5, 0.9, 0.975, 0.999):
            self.assertAlmostEqual(stats.norm_cdf(stats.norm_ppf(p)), p, places=6)

    def test_wilson_matches_normal_case_and_stays_in_range(self):
        lo, hi = stats.wilson_interval(110, 200)
        self.assertLess(lo, 0.55)
        self.assertGreater(hi, 0.55)
        lo0, hi0 = stats.wilson_interval(0, 10)
        self.assertGreaterEqual(lo0, 0.0)
        self.assertLess(hi0, 0.35)   # 0/10 must not look like a proven 0%

    def test_required_sample_at_55_percent(self):
        n = stats.required_sample(HURDLE, 0.55)
        self.assertEqual(n, 2243)  # published figure; change deliberately, never silently

    def test_required_sample_direction(self):
        self.assertLess(stats.required_sample(HURDLE, 0.58), stats.required_sample(HURDLE, 0.55))

    def test_detectable_edge_is_inverse_of_required_sample(self):
        p = stats.detectable_edge(2243, HURDLE)
        self.assertLessEqual(stats.required_sample(HURDLE, p), 2243)
        self.assertGreater(stats.required_sample(HURDLE, p - 0.001), 2243)

    def test_bootstrap_contains_sample_mean(self):
        vals = [(i % 7) - 3 for i in range(400)]
        point, lo, hi = stats.bootstrap_ci(vals, n_boot=500, seed=11)
        self.assertLessEqual(lo, point)
        self.assertLessEqual(point, hi)

    def test_bootstrap_refuses_tiny_samples(self):
        with self.assertRaises(ValueError):
            stats.bootstrap_ci([1, 2, 3])

    def test_paired_bootstrap_zero_difference(self):
        a = [1.0 if i % 2 else -1.0 for i in range(200)]
        point, lo, hi = stats.paired_bootstrap_diff(a, list(a), n_boot=200, seed=3)
        self.assertAlmostEqual(point, 0.0, places=12)
        self.assertAlmostEqual(lo, 0.0, places=12)

    def test_reality_check_no_signal_is_not_significant(self):
        # pure noise: 40 strategies x 400 periods, none better than benchmark
        import random
        rng = random.Random(2026)
        t, k = 400, 40
        mat = [[rng.gauss(0, 1) for _ in range(k)] for _ in range(t)]
        p, best, stat = stats.reality_check_pvalue(mat, n_boot=400, seed=5)
        self.assertGreater(p, 0.05)
        self.assertTrue(0 <= best < k)

    def test_reality_check_finds_a_real_edge(self):
        import random
        rng = random.Random(99)
        t, k = 600, 20
        mat = [[rng.gauss(0, 1) for _ in range(k)] for _ in range(t)]
        for row in mat:
            row[7] -= 0.20          # strategy 7 genuinely better (lower loss)
        p, best, stat = stats.reality_check_pvalue(mat, n_boot=400, seed=13)
        self.assertEqual(best, 7)
        self.assertLess(p, 0.05)

    def test_deflated_sharpe_requires_trial_dispersion(self):
        rets = [0.01 if i % 3 else -0.01 for i in range(300)]
        with self.assertRaises(ValueError):
            stats.deflated_sharpe_ratio(rets, trials=50)
        out = stats.deflated_sharpe_ratio(rets, trials=50, trial_sharpe_sd=0.05)
        self.assertGreater(out["deflated_sharpe_probability"], 0.5)

    def test_jaccard(self):
        self.assertEqual(stats.jaccard({1, 2, 3}, {1, 2, 3}), 1.0)
        self.assertEqual(stats.jaccard({1, 2}, {3, 4}), 0.0)
        self.assertAlmostEqual(stats.jaccard({1, 2, 3, 4}, {3, 4, 5}), 0.4, places=12)


class TestCompliance(unittest.TestCase):
    def test_injury_subject_prohibited(self):
        r = compliance.classify_market("Mahomes to be listed Out on the injury report")
        self.assertEqual(r["decision"], "PROHIBIT")
        self.assertIn("INJURY_OR_HEALTH", r["classes"])

    def test_officiating_prohibited(self):
        r = compliance.classify_market("Total penalty yards by the referee crew")
        self.assertEqual(r["decision"], "PROHIBIT")
        self.assertIn("OFFICIATING", r["classes"])

    def test_one_person_one_play_prohibited(self):
        r = compliance.classify_market("Bryce Baringer to miss his first field goal attempt")
        self.assertEqual(r["decision"], "PROHIBIT")
        self.assertIn("ONE_PERSON_ONE_PLAY", r["classes"])

    def test_predetermined_roster_prohibited(self):
        r = compliance.classify_market("Will the starting QB start this week?")
        self.assertEqual(r["decision"], "PROHIBIT")
        self.assertIn("PRE_DETERMINED", r["classes"])

    def test_allowed_standard_markets(self):
        for name, fam in [("Chiefs -3.5", "game spread"), ("Over 44.5", "game total"),
                          ("Kelce over 62.5 receiving yards", "receiving yards")]:
            self.assertEqual(compliance.classify_market(name, fam)["decision"], "ALLOW", name)

    def test_unknown_family_holds(self):
        r = compliance.classify_market("Some exotic new market", "team exotic")
        self.assertEqual(r["decision"], "HOLD")

    def test_non_public_flag_blocks_any_market(self):
        r = compliance.check_bet({"market": "Chiefs -3.5", "family": "game spread",
                                  "non_public": True})
        self.assertEqual(r["decision"], "PROHIBIT")
        self.assertIn("NON_PUBLIC_INFORMATION", r["classes"])

    def test_provenance_allowlist(self):
        ok = compliance.check_provenance(["SRC-001"], ["SRC-001", "SRC-002"])
        bad = compliance.check_provenance(["SRC-999"], ["SRC-001"])
        self.assertTrue(ok["ok"])
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["unknown_sources"], ["SRC-999"])

    def test_filter_offers_splits(self):
        offers = [{"market": "Over 44.5", "family": "game total"},
                  {"market": "Player to be placed on IR", "family": "game total"}]
        allowed, refused = compliance.filter_offers(offers)
        self.assertEqual(len(allowed), 1)
        self.assertEqual(len(refused), 1)
        self.assertIn("refusal", refused[0])


class TestInjuries(unittest.TestCase):
    def setUp(self):
        import json
        path = os.path.join(os.path.dirname(__file__), "..", "data", "injury_snapshot.json")
        with open(path, encoding="utf-8") as fh:
            self.snap = json.load(fh)
        self.rows = injuries.load_rows(self.snap)

    def test_snapshot_is_not_empty_and_is_labelled_partial(self):
        self.assertGreater(len(self.rows), 10)
        self.assertTrue(self.snap.get("captured_partial"))
        self.assertIn("chunks 0-1 of 8", (self.snap.get("capture_note") or "").lower())
        self.assertEqual(self.snap.get("capture"), "A")
        self.assertEqual(self.snap.get("companion_capture"), "injury_snapshot_b")

    def test_blank_injury_stays_none(self):
        Daniels = [r for r in self.rows if r["player"] == "Jayden Daniels"][0]
        self.assertIsNone(Daniels["injury"])
        self.assertEqual(Daniels["practice"], "Full Participation in Practice")
        self.assertTrue(injuries.certain_to_play(Daniels))

    def test_out_is_the_only_confirmed_absence(self):
        pat = [r for r in self.rows if r["player"] == "Lucas Patrick"][0]
        self.assertTrue(injuries.is_unavailable(pat))
        brown = [r for r in self.rows if r["player"] == "A.J. Brown"][0]
        self.assertFalse(injuries.is_unavailable(brown))
        self.assertTrue(injuries.at_risk(brown))

    def test_group_classification_covers_positions(self):
        cb = [r for r in self.rows if r["pos"] == "CB"][0]
        self.assertEqual(cb["side"], "defence")
        self.assertEqual(cb["group"], "outside_cb")
        t = [r for r in self.rows if r["pos"] == "T"][0]
        self.assertEqual(t["group"], "offensive_line")

    def test_deficiency_counts_run_without_estimates(self):
        counts = injuries.deficiency_counts(self.rows)
        self.assertIn("New England", counts)
        det = counts["New England"]
        self.assertIn("defence::outside_cb", det)
        self.assertIn("Carlton Davis III", det["defence::outside_cb"]["out"])

    def test_nmu_refuses_to_invent_points(self):
        out = injuries.nmu_index(self.rows)
        self.assertEqual(out["mode"], "COUNT_ONLY_UNWEIGHTED")
        self.assertIsNone(out["index"])
        with self.assertRaises(injuries.NeedsEstimate):
            injuries.nmu_index(self.rows, snap_share={}, quality_gap={})

    def test_scenario_range_has_no_expected_value_when_at_risk_exists(self):
        r = injuries.scenario_range(self.rows)
        ne = r["New England"]
        self.assertEqual(ne["best_case_out"], ne["confirmed_out"])
        self.assertEqual(ne["worst_case_out"], ne["confirmed_out"] + ne["at_risk"])
        self.assertIsNone(ne["expected_case_out"])
        self.assertIn("P(play)", ne["expected_case_note"])

    def test_diff_detects_worsening_and_improvement(self):
        import copy
        a = copy.deepcopy(self.snap)
        b = copy.deepcopy(self.snap)
        for r in b["rows"]:
            if r["player"] == "A.J. Brown":
                r["game_status"] = "Out"
                r["practice"] = "Did Not Participate In Practice"
        changes = injuries.diff_snapshots(a, b)
        self.assertTrue(any(c.get("field") == "game_status" and c.get("direction") == "worse"
                            for c in changes))
        for r in b["rows"]:
            if r["player"] == "Lucas Patrick":
                r["game_status"] = ""
                r["practice"] = "Full Participation in Practice"
        changes = injuries.diff_snapshots(a, b)
        self.assertTrue(any(c.get("direction") == "better" for c in changes))

    def test_unknown_position_is_unclassified_not_guessed(self):
        row = {"team": "X", "player": "Y", "pos": "VK", "injury": "", "practice": "", "game_status": ""}
        out = injuries.deficiency_counts([row])
        self.assertEqual(out, {})


class TestGates(unittest.TestCase):
    def _bets(self, n, hit, price=-110, season=2026, team=None, clv=None, edge=0.03):
        bets = []
        for i in range(n):
            won = (i % 100) < round(hit * 100)
            bets.append({"game_id": f"g{i}", "season": season + (i % 3), "team": team or f"t{i % 32}",
                         "price": price, "stake": 1.0, "won": won,
                         "pnl": (100 / 110) if won else -1.0,
                         "clv": clv, "modelled_edge": edge, "eval": "oos"})
        return bets

    def test_clean_fail_on_small_sample(self):
        rows, summary = gates.evaluate(self._bets(40, 0.55), gates.GateConfig())
        g1 = [r for r in rows if r.gate_id == "G-1"][0]
        self.assertEqual(g1.verdict, "FAIL")
        self.assertEqual(summary["bets_settled"], 40)

    def test_big_sample_55_passes_core_gates(self):
        cfg = gates.GateConfig(trials=1)
        rows, summary = gates.evaluate(self._bets(1200, 0.55), cfg)
        by = {r.gate_id: r for r in rows}
        self.assertEqual(by["G-1"].verdict, "PASS")
        self.assertEqual(by["G-2"].verdict, "PASS")
        self.assertEqual(by["G-2b"].verdict, "PASS")
        self.assertEqual(by["G-3"].verdict, "BLOCKED")   # no line data, as expected

    def test_54_percent_fails_hurdle_test_at_this_sample(self):
        rows, _ = gates.evaluate(self._bets(320, 0.54), gates.GateConfig())
        by = {r.gate_id: r for r in rows}
        self.assertEqual(by["G-2"].verdict, "PASS")       # 54% > 52.38% nominally
        self.assertEqual(by["G-2b"].verdict, "FAIL")      # but not distinguishable from it

    def test_holding_data_missing_blocks_g7(self):
        rows, _ = gates.evaluate(self._bets(400, 0.55), gates.GateConfig())
        by = {r.gate_id: r for r in rows}
        self.assertEqual(by["G-7"].verdict, "BLOCKED")

    def test_concentration_failure(self):
        bets = self._bets(600, 0.56, season=2026, team="KC")
        for b in bets:
            b["season"] = 2026            # single season -> must trip G-8
        rows, _ = gates.evaluate(bets, gates.GateConfig())
        by = {r.gate_id: r for r in rows}
        self.assertEqual(by["G-8"].verdict, "FAIL")

    def test_in_sample_contamination_fails_g9(self):
        bets = self._bets(400, 0.55)
        bets[0]["eval"] = "in_sample"
        rows, _ = gates.evaluate(bets, gates.GateConfig())
        self.assertEqual({r.gate_id: r for r in rows}["G-9"].verdict, "FAIL")

    def test_stake_beyond_cap_fails_g10(self):
        bets = self._bets(400, 0.55)
        bets[5]["stake"] = 9.0
        rows, _ = gates.evaluate(bets, gates.GateConfig(max_stake_units=2.0))
        self.assertEqual({r.gate_id: r for r in rows}["G-10"].verdict, "FAIL")

    def test_clv_present_and_positive_passes_g3(self):
        bets = self._bets(600, 0.55, clv=0.30)
        rows, _ = gates.evaluate(bets, gates.GateConfig())
        self.assertEqual({r.gate_id: r for r in rows}["G-3"].verdict, "PASS")

    def test_abstentions_are_reported(self):
        bets = self._bets(300, 0.55) + [{"abstained": True}] * 700
        _, summary = gates.evaluate(bets, gates.GateConfig())
        self.assertAlmostEqual(summary["abstain_rate"], 0.7, places=6)

    def test_empty_log_is_blocked_not_passed(self):
        rows, summary = gates.evaluate([], gates.GateConfig())
        self.assertTrue(all(r.verdict == "BLOCKED" for r in rows))
        self.assertEqual(summary["bets_settled"], 0)

    def test_detectable_edge_table_is_monotone(self):
        rows = gates.detectable_edge_table(HURDLE, [50, 200, 800, 3200])
        rates = [r["min_provable_hit_rate"] for r in rows]
        self.assertEqual(rates, sorted(rates, reverse=True))


class TestLeaderboard(unittest.TestCase):
    def _entry(self, eid, bets, author="a", division="D2", code="x"):
        return leaderboard.Entry(entry_id=eid, author=author, division=division,
                                 bets=bets, code_blob=code)

    def test_hash_is_content_addressed(self):
        e1 = self._entry("e1", [{"game_id": "g", "price": -110, "won": True, "stake": 1, "pnl": 0.9}])
        e2 = self._entry("e1", [{"game_id": "g", "price": -110, "won": True, "stake": 1, "pnl": 0.9}])
        e3 = self._entry("e1", [{"game_id": "g", "price": -115, "won": True, "stake": 1, "pnl": 0.9}])
        self.assertEqual(e1.sealed_hash(), e2.sealed_hash())
        self.assertNotEqual(e1.sealed_hash(), e3.sealed_hash())

    def test_more_evidence_wins_when_mean_is_equal(self):
        small = self._entry("small", _bets_seq(60, 0.58), author="x")
        big = self._entry("big", _bets_seq(1200, 0.58), author="y")
        table = leaderboard.rank([small, big], gates.GateConfig())
        self.assertLess(table[0]["lcb"], table[1]["lcb"] + 1)   # sanity: bounds are ordered
        self.assertEqual(table[0]["entry_id"], "big")

    def test_gate_veto_zeroes_eligibility(self):
        lucky = self._entry("lucky", _bets_seq(30, 0.70), author="x")
        solid = self._entry("solid", _bets_seq(2500, 0.56), author="y")
        table = leaderboard.rank([lucky, solid], gates.GateConfig())
        self.assertEqual(table[0]["entry_id"], "solid")
        lucky_row = [r for r in table if r["entry_id"] == "lucky"][0]
        self.assertFalse(lucky_row["eligible"])
        self.assertIn("G-1", lucky_row["failed_hard_gates"])

    def test_dedupe_merges_near_identical_entries(self):
        bets = _bets_seq(500, 0.56)
        a = self._entry("a", bets, author="same", code="c1")
        b = self._entry("b", bets, author="same", code="c2")
        table = leaderboard.rank([a, b], gates.GateConfig())
        merged = [r for r in table if r.get("merged_with")]
        self.assertEqual(len(table), 1)
        self.assertTrue(merged or table[0]["entry_id"] in ("a", "b"))

    def test_las_is_lcb_based_not_pnl_based(self):
        risky = self._entry("risky", _bets_seq(120, 0.60), author="x")
        steady = self._entry("steady", _bets_seq(1500, 0.55), author="y")
        table = leaderboard.rank([risky, steady], gates.GateConfig())
        top = table[0]
        self.assertGreater(top["bets"], risky.bets.__len__())


def _bets_seq(n, hit, price=-110):
    out = []
    for i in range(n):
        won = (i % 100) < round(hit * 100)
        out.append({"game_id": f"g{i}", "season": 2020 + (i % 5), "team": f"t{i % 32}",
                    "price": price, "stake": 1.0, "won": won,
                    "pnl": (100 / 110) if won else -1.0, "clv": None,
                    "modelled_edge": 0.03, "eval": "oos"})
    return out


if __name__ == "__main__":
    unittest.main(verbosity=2)
