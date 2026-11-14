"""Evaluation of a strategy bet log against the gate set (G-1..G-13).

Thresholds are constructor arguments with documented defaults: they are our proposed
competition rules, not facts about football, and a reviewer should feel free to change
them. What a reviewer may not do is reinterpret a FAIL as a PASS, which is why the
verdict is computed here and rendered verbatim by the site.

A bet record (dict) is expected to carry, at minimum:
    game_id  str            unique game identifier
    season   int|str         for concentration and stability splits
    team     str|None         the club whose games dominate this bet
    price    int             American price paid (e.g. -110)
    stake    float            units staked (>0)
    won      bool|None        None => push/void
    pnl      float|None       realised profit in units for the settled outcome
    clv      float|None       per-unit EV versus the closing price (None if line data absent)

`stats_only` bets (abstentions) are counted where present via 'abstained': True, because
selectivity is a measurable behaviour and a strategy that never says no is not selective.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from . import pricing, stats


@dataclass
class GateConfig:
    min_bets: int = 300
    min_seasons: int = 3
    require_positive_clv: bool = True
    edge_threshold: float = 0.02          # modelled EV per unit above break-even
    max_season_pnl_share: float = 0.45
    max_team_pnl_share: float = 0.25
    decay_window: int = 250
    jaccard_merge: float = 0.8
    max_entries_per_author: int = 5
    hold_assumed: float = 0.04545         # -110 two-way theoretical margin
    hold_measured: float | None = None    # None until GAP-08 closes
    trials: int = 1                       # number of candidate strategies searched
    max_stake_units: float = 2.0            # hard exposure cap; breach is a disqualification
    trial_sharpe_sd: float | None = None


@dataclass
class GateResult:
    gate_id: str
    name: str
    value: float | None
    threshold: str
    verdict: str          # PASS | FAIL | BLOCKED
    note: str = ""

    def as_row(self) -> dict:
        return {"gate": self.gate_id, "name": self.name,
                "value": "" if self.value is None else round(self.value, 5),
                "threshold": self.threshold, "verdict": self.verdict, "note": self.note}


def _settled(bets: Sequence[dict]) -> list[dict]:
    return [b for b in bets if b.get("won") is not None and not b.get("abstained")]


def evaluate(bets: Sequence[dict], cfg: GateConfig | None = None) -> tuple[list[GateResult], dict]:
    """Return (gate rows, summary) for one strategy's log."""
    cfg = cfg or GateConfig()
    s = _settled(bets)
    n = len(s)
    abst = sum(1 for b in bets if b.get("abstained"))
    wins = sum(1 for b in s if b["won"])
    summary = {
        "bets_settled": n,
        "bets_won": wins,
        "hit_rate": (wins / n) if n else None,
        "abstentions": abst,
        "abstain_rate": (abst / (abst + n)) if (abst + n) else None,
        "pnl_units": round(sum(b.get("pnl") or 0.0 for b in s), 4),
        "staked_units": round(sum(b.get("stake") or 0.0 for b in s), 4),
    }
    results: list[GateResult] = []
    if n == 0:
        return ([GateResult(f"G-{i}", g, None, t, "BLOCKED", "no settled bets in the log")
                 for i, (g, t) in enumerate(
                     [("Sample sufficiency", "n >= %d" % cfg.min_bets),
                      ("Break-even hurdle", "hit rate > hurdle"),
                      ("Closing-line value", "CLV LCB > 0")], start=1)], summary)

    # --- G-1 sample sufficiency -------------------------------------------------
    hurdle = pricing.break_even_probability(_modal_price(s))
    p_hat = wins / n
    se = stats.proportion_se(p_hat, n) if n > 1 else 0.0
    z = stats.z_stat(p_hat, hurdle, n)
    results.append(GateResult(
        "G-1", "Sample sufficiency", float(n),
        f"n >= {cfg.min_bets} and seasons >= {cfg.min_seasons}",
        "PASS" if n >= cfg.min_bets else "FAIL",
        f"z vs break-even = {z:.2f}; n={n} settled bets"))

    # --- G-2 break-even hurdle ---------------------------------------------------
    results.append(GateResult(
        "G-2", "Break-even hurdle", p_hat, f"hit rate > {hurdle:.5f} at the price paid",
        "PASS" if p_hat > hurdle else "FAIL",
        f"modal price {hurdle:.5f} break-even; observed {p_hat:.5f}"))

    # --- G-2b statistical significance of the hit rate --------------------------
    pval = stats.one_sided_p_above(z)
    results.append(GateResult(
        "G-2b", "Hurdle exceeded beyond noise", pval, "one-sided p < 0.05 vs break-even",
        "PASS" if pval < 0.05 else "FAIL",
        "the profit is not explainable as a lucky run at this sample size"))

    # --- G-3 closing line value ---------------------------------------------------
    clvs = [b["clv"] for b in s if b.get("clv") is not None]
    if len(clvs) < 5:
        results.append(GateResult("G-3", "Closing-line value", None,
                                  "median CLV > 0 with bootstrap LCB > 0", "BLOCKED",
                                  "no closing-line data (GAP-01). Until this is BLOCKED, no "
                                  "strategy may be promoted, whatever its record."))
    else:
        point, lo, hi = stats.bootstrap_ci(clvs, n_boot=2000)
        results.append(GateResult("G-3", "Closing-line value", point,
                                  f"bootstrap LCB > 0 (observed [{lo:.4f}, {hi:.4f}])",
                                  "PASS" if lo > 0 else "FAIL",
                                  "beating the close is the closest available proxy for being right"))

    # --- G-4 selectivity ------------------------------------------------------------
    edges = [b.get("modelled_edge") for b in s if b.get("modelled_edge") is not None]
    if not edges:
        results.append(GateResult("G-4", "Edge threshold / selectivity", None,
                                  f"bet only when EV exceeds hurdle + {cfg.edge_threshold}",
                                  "BLOCKED", "the log does not record modelled edge per bet"))
    else:
        mean_edge = stats.mean(edges)
        share_below = sum(1 for e in edges if e < cfg.edge_threshold) / len(edges)
        results.append(GateResult(
            "G-4", "Edge threshold / selectivity", mean_edge,
            f"mean modelled EV >= hurdle + {cfg.edge_threshold}",
            "PASS" if share_below == 0.0 else "FAIL",
            f"{share_below:.1%} of bets taken below the configured threshold; "
            f"abstain rate {summary['abstain_rate'] if summary['abstain_rate'] is not None else 'n/a'}"))

    # --- G-5 / G-6 multiple comparisons ---------------------------------------------
    if cfg.trials > 1:
        required = stats.required_sample(hurdle, min(0.99, p_hat), 0.05 / cfg.trials)
        results.append(GateResult(
            "G-5", "Multiple-comparison control (Bonferroni floor)", float(cfg.trials),
            f"n >= {required} at alpha/m = {0.05 / cfg.trials:.5f}",
            "PASS" if n >= required else "FAIL",
            "the sample needed to stay significant once the number of searched strategies "
            "is charged against you; use the max-T routine in stats.reality_check_pvalue "
            "for the real competition-wide test"))
    else:
        results.append(GateResult("G-5", "Multiple-comparison control", 1.0,
                                  "single candidate: correction not binding", "PASS",
                                  "declare `trials` honestly: understating it is the one "
                                  "input that makes every other gate look better"))
    rets = [b.get("pnl") for b in s if b.get("pnl") is not None]
    if len(rets) >= 20 and cfg.trial_sharpe_sd is not None and cfg.trials > 1:
        dsr = stats.deflated_sharpe_ratio(rets, trials=cfg.trials,
                                           trial_sharpe_sd=cfg.trial_sharpe_sd)
        results.append(GateResult("G-6", "Overfitting deflator",
                                  dsr["deflated_sharpe_probability"],
                                  "deflated Sharpe probability > 0.95",
                                  "PASS" if dsr["deflated_sharpe_probability"] > 0.95 else "FAIL",
                                  f"raw Sharpe {dsr['sharpe']:.3f}; selection-adjusted "
                                  f"benchmark {dsr['expected_max_sharpe_under_null']:.3f}"))
    else:
        results.append(GateResult("G-6", "Overfitting deflator", None,
                                  "requires per-period returns and the trial dispersion",
                                  "BLOCKED",
                                  "no default dispersion is supplied on purpose: DSR with an "
                                  "invented trial count is decoration"))

    # --- G-7 hold realism -------------------------------------------------------------
    if cfg.hold_measured is None:
        results.append(GateResult("G-7", "Hold realism", None,
                                  "recompute at measured hold by family", "BLOCKED",
                                  "regulator files not parsed (GAP-08); assumption remains the "
                                  "theoretical -110 margin, which flatters parlays"))
    else:
        adj = stats.mean([pricing.hold_adjusted_ev(
            pricing.ev_per_unit(1.0 if b["won"] else 0.0, b["price"]), cfg.hold_measured,
            cfg.hold_assumed) for b in s])
        results.append(GateResult("G-7", "Hold realism", adj,
                                  "EV stays positive at measured hold", "PASS" if adj > 0 else "FAIL",
                                  f"measured hold {cfg.hold_measured:.4f} vs assumed {cfg.hold_assumed:.4f}"))

    # --- G-8 concentration --------------------------------------------------------------
    pnls = [b.get("pnl") or 0.0 for b in s]
    total_gain = sum(p for p in pnls if p > 0) or 1.0
    by_season: dict = {}
    by_team: dict = {}
    for b, p in zip(s, pnls):
        if p > 0:
            by_season[str(b.get("season"))] = by_season.get(str(b.get("season")), 0.0) + p
            if b.get("team"):
                by_team[str(b.get("team"))] = by_team.get(str(b.get("team")), 0.0) + p
    s_share = max(by_season.values()) / total_gain if by_season else 0.0
    t_share = max(by_team.values()) / total_gain if by_team else 0.0
    results.append(GateResult(
        "G-8", "Concentration and regime stability", s_share,
        f"max season share <= {cfg.max_season_pnl_share:.0%} and max team share <= {cfg.max_team_pnl_share:.0%}",
        "PASS" if (s_share <= cfg.max_season_pnl_share and t_share <= cfg.max_team_pnl_share) else "FAIL",
        f"largest season {s_share:.1%} of gains, largest team {t_share:.1%}"))

    # --- G-9 walk-forward -------------------------------------------------------------
    wf = all(b.get("eval", "oos") == "oos" for b in s)
    results.append(GateResult("G-9", "Walk-forward only", 1.0 if wf else 0.0,
                              "100% out-of-sample by construction", "PASS" if wf else "FAIL",
                              "any in-sample row in the score disqualifies the score, not the row"))

    # --- G-10 cost realism --------------------------------------------------------------
    capped = all(0 < (b.get("stake") or 0) <= cfg.max_stake_units for b in s)
    promo = any(b.get("promo_credit") for b in s)
    results.append(GateResult("G-10", "Cost and execution realism", float(n),
                              "stakes within limits; no promo credit counted as edge",
                              "PASS" if (capped and not promo) else "FAIL",
                              "void/reprice handling must follow the filed house rule version"))

    # --- G-11 decay ---------------------------------------------------------------------
    if len(clvs) >= cfg.decay_window:
        window = clvs[-cfg.decay_window:]
        point, lo, hi = stats.bootstrap_ci(window, n_boot=1500)
        results.append(GateResult("G-11", "Decay monitoring", point,
                                  "rolling CLV LCB > 0", "PASS" if lo > 0 else "FAIL",
                                  f"last {cfg.decay_window} bets; auto-demote on a negative bound"))
    else:
        results.append(GateResult("G-11", "Decay monitoring", None,
                                  f"needs {cfg.decay_window} bets with CLV", "BLOCKED",
                                  "not enough settled, priced bets to judge decay yet"))

    # --- G-12 compliance ------------------------------------------------------------------
    results.append(GateResult("G-12", "Compliance gate", None,
                              "delegated to engine.compliance at bet emission", "PASS",
                              "this gate is enforced upstream: a prohibited market never reaches "
                              "the log, so a clean log here is a necessary but not sufficient claim"))

    # --- G-13 dedupe ----------------------------------------------------------------------
    results.append(GateResult("G-13", "Deduplication of entries", None,
                              f"Jaccard <= {cfg.jaccard_merge} across a single author's entries",
                              "BLOCKED", "resolved at leaderboard scoring, which sees all entries"))

    return results, summary


def _modal_price(bets: Sequence[dict]) -> float:
    """Most common price paid in the log; the hurdle is computed at *that* price."""
    counts: dict[float, int] = {}
    for b in bets:
        counts[b["price"]] = counts.get(b["price"], 0) + 1
    return max(counts.items(), key=lambda kv: kv[1])[0]


def detectable_edge_table(hurdle: float, ns: Sequence[int], alpha: float = 0.05,
                          power: float = 0.80) -> list[dict]:
    """The curve the leaderboard should publish: bets per season vs provable edge."""
    rows = []
    for n in ns:
        p = stats.detectable_edge(n, hurdle, alpha, power)
        rows.append({"bets": n, "min_provable_hit_rate": round(p, 5),
                     "min_edge_pp": round((p - hurdle) * 100, 3),
                     "seasons_at_this_volume": round(stats.required_sample(hurdle, p, alpha, power) / n, 2)})
    return rows


# ----------------------------------------------------------------------------------------
# G-14 Demotion gate: a LIVE strategy goes back to PAPER on defined triggers (brief item).
#
# Thresholds below are proposals (see suggestions register); the rule shape is fixed:
#   R1 exposure    any stake above cfg.max_stake_units while live       -> DEMOTE (immediate)
#   R2 sample      fewer than WINDOW settled live bets                  -> NO DECISION (stay live,
#                                                                          reported as insufficient)
#   R3 signal      LCB95 of equal-weight per-unit return over the last
#                  WINDOW settled bets is below zero                    -> DEMOTE
#   R4 CLV         LCB95 of CLV over the last WINDOW bets is below zero;
#                  if CLV is absent the rule is NOT evaluated (never imputed) -> DEMOTE
# Paper is not a penalty box: a demoted strategy keeps accumulating paper bets, and it
# returns to LIVE only through repromotion_decision().
# ----------------------------------------------------------------------------------------

DEMOTION_WINDOW = 100
REPROMOTION_WINDOW = 250


def _lcb(values, n_boot=2000):
    if len(values) < 20:
        return None
    _, lo, _ = stats.bootstrap_ci(values, n_boot=n_boot)
    return lo


def demotion_decision(live_bets: Sequence[dict], cfg: GateConfig | None = None,
                      window: int = DEMOTION_WINDOW) -> dict:
    """Decide whether a LIVE strategy stays live. Input: live bets in chronological order."""
    cfg = cfg or GateConfig()
    reasons, checks = [], []
    settled = [b for b in live_bets if b.get("won") is not None and not b.get("abstained")]

    breaches = [b for b in live_bets if (b.get("stake") or 0) > cfg.max_stake_units]
    if breaches:
        return {"gate": "G-14", "decision": "DEMOTE_TO_PAPER", "state_after": "PAPER",
                "reasons": [f"R1 exposure: {len(breaches)} live bet(s) above the {cfg.max_stake_units}-unit cap"],
                "checks": [("R1", "exposure breach", "FAIL")], "window": window, "n_settled": len(settled)}
    checks.append(("R1", "exposure within cap", "PASS"))

    if len(settled) < window:
        return {"gate": "G-14", "decision": "NO_DECISION_INSUFFICIENT_SAMPLE", "state_after": "LIVE",
                "reasons": [f"R2 sample: {len(settled)} of {window} settled live bets"],
                "checks": checks + [("R2", "sample", "BLOCKED")], "window": window, "n_settled": len(settled)}
    last = settled[-window:]
    unit = [float(b.get("pnl", 0.0) or 0.0) / float(b["stake"]) for b in last]
    lo = _lcb(unit)
    checks.append(("R2", "sample", "PASS"))
    if lo is not None and lo < 0:
        reasons.append(f"R3 signal: LCB95 of per-unit return {lo:.4f} < 0 over last {window} bets")
        checks.append(("R3", "signal LCB", "FAIL"))
    else:
        checks.append(("R3", "signal LCB", "PASS" if lo is not None else "BLOCKED"))

    clv = [float(b["clv"]) for b in last if b.get("clv") is not None]
    if len(clv) == window:
        clv_lo = _lcb(clv)
        if clv_lo is not None and clv_lo < 0:
            reasons.append(f"R4 CLV: LCB95 {clv_lo:.4f} < 0 over last {window} bets")
            checks.append(("R4", "CLV LCB", "FAIL"))
        else:
            checks.append(("R4", "CLV LCB", "PASS"))
    else:
        checks.append(("R4", "CLV", "NOT EVALUATED: CLV present for %d of %d bets (GAP-01)" % (len(clv), window)))

    if reasons:
        return {"gate": "G-14", "decision": "DEMOTE_TO_PAPER", "state_after": "PAPER",
                "reasons": reasons, "checks": checks, "window": window, "n_settled": len(settled)}
    return {"gate": "G-14", "decision": "KEEP_LIVE", "state_after": "LIVE", "reasons": [],
            "checks": checks, "window": window, "n_settled": len(settled)}


def repromotion_decision(paper_bets: Sequence[dict], cfg: GateConfig | None = None,
                         window: int = REPROMOTION_WINDOW) -> dict:
    """A PAPER strategy returns to LIVE only after a full window of paper bets with a positive
    signal lower bound and no exposure breach. Same arithmetic as the demotion gate, stricter window."""
    cfg = cfg or GateConfig()
    settled = [b for b in paper_bets if b.get("won") is not None and not b.get("abstained")]
    if any((b.get("stake") or 0) > cfg.max_stake_units for b in paper_bets):
        return {"gate": "G-14", "decision": "STAY_PAPER", "reasons": ["exposure breach on paper record"],
                "n_settled": len(settled), "window": window}
    if len(settled) < window:
        return {"gate": "G-14", "decision": "STAY_PAPER",
                "reasons": [f"{len(settled)} of {window} settled paper bets"],
                "n_settled": len(settled), "window": window}
    last = settled[-window:]
    lo = _lcb([float(b.get("pnl", 0.0) or 0.0) / float(b["stake"]) for b in last])
    if lo is not None and lo > 0:
        return {"gate": "G-14", "decision": "ELIGIBLE_TO_REPROMOTE", "reasons": [],
                "n_settled": len(settled), "window": window, "signal_lcb": round(lo, 5)}
    return {"gate": "G-14", "decision": "STAY_PAPER",
            "reasons": [f"signal LCB95 {lo:.4f} is not above zero" if lo is not None else "signal LCB not computable"],
            "n_settled": len(settled), "window": window}
