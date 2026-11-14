"""Demotion gate: when a LIVE strategy goes back to PAPER.

The validation page defines three demotion rules (D1–D3). This module makes them
executable, so 'auto-demote' is a function call rather than a policy sentence.
The lifecycle is explicit and one-directional under failure:

    PAPER  --(promotion gates G-1..G-6 clear)-->  LIVE
    LIVE   --(any D-rule fires)---------------->  PAPER

D1  Live-decay monitor    rolling closing-line value (CLV) lower confidence
                          bound stays below zero across the monitoring window.
D2  Calibration drift    realised hit rate falls outside the declared
                          probability band around the quoted probabilities.
D3  Concentration breach one season / team / cluster exceeds its allowed share
                          of net gains.

Design rules carried over from the rest of the engine:
    * thresholds are constructor arguments with documented defaults, never
      hidden constants — a reviewer changes them in one place;
    * INSUFFICIENT_DATA is a first-class outcome, not a pass. A window too
      small to judge decay keeps the strategy where it is and says why;
    * a demotion decision carries its reasons, so the site can print them
      verbatim and nobody has to trust a bare verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from . import stats

KEEP_LIVE = "KEEP_LIVE"
DEMOTE_TO_PAPER = "DEMOTE_TO_PAPER"
INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class DemotionConfig:
    # D1
    decay_window: int = 250          # settled bets per monitoring window
    clv_lcb_floor: float = 0.0       # demote when the window's CLV LCB < floor
    # D2
    prob_band: float = 0.05          # allowed |realised - quoted| on mean quoted prob
    min_bets_calibration: int = 100
    # D3
    max_season_gain_share: float = 0.45
    max_team_gain_share: float = 0.25
    # lifecycle
    min_settled_to_judge: int = 50   # below this, INSUFFICIENT_DATA


@dataclass
class DemotionDecision:
    action: str
    reasons: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    @property
    def demoted(self) -> bool:
        return self.action == DEMOTE_TO_PAPER

    def as_row(self) -> dict:
        return {"action": self.action,
                "reasons": "; ".join(self.reasons) if self.reasons else "",
                **{k: v for k, v in self.metrics.items()}}


def _settled(bets: Sequence[dict]) -> list[dict]:
    return [b for b in bets if b.get("won") is not None and not b.get("abstained")]


def evaluate_live(bets: Sequence[dict], cfg: DemotionConfig | None = None,
                  state: str = "LIVE") -> DemotionDecision:
    """Evaluate a live strategy's bet log against D1–D3.

    `bets` uses the same record shape as engine.gates (see its docstring):
    won, price, stake, pnl, clv, season, team, and optionally `quoted_prob`
    for D2. `state` is the strategy's current lifecycle state; a strategy
    already on paper is never 'demoted' again — the call is a no-op KEEP-free
    INSUFFICIENT_DATA-free record. For simplicity we evaluate logs regardless
    of state and let the caller persist transitions; `state` is echoed into
    metrics so the decision log is self-describing.
    """
    cfg = cfg or DemotionConfig()
    s = _settled(bets)
    decision = DemotionDecision(action=KEEP_LIVE, metrics={"state_in": state,
                                                           "settled": len(s)})
    if len(s) < cfg.min_settled_to_judge:
        decision.action = INSUFFICIENT_DATA
        decision.reasons.append(
            f"only {len(s)} settled bets; {cfg.min_settled_to_judge} required "
            f"to judge a live strategy at all")
        return decision

    # ---- D1: rolling CLV decay -------------------------------------------------
    clvs = [b["clv"] for b in s if b.get("clv") is not None]
    decision.metrics["clvs"] = len(clvs)
    if len(clvs) >= cfg.decay_window:
        window = clvs[-cfg.decay_window:]
        point, lo, hi = stats.bootstrap_ci(window, n_boot=1500)
        decision.metrics["clv_window_lcb"] = round(lo, 5)
        decision.metrics["clv_window_mean"] = round(point, 5)
        if lo < cfg.clv_lcb_floor:
            decision.reasons.append(
                f"D1 live-decay: rolling {cfg.decay_window}-bet CLV lower bound "
                f"{lo:.4f} < {cfg.clv_lcb_floor}")
            decision.action = DEMOTE_TO_PAPER
    else:
        decision.reasons.append(
            f"D1 not judgeable yet: {len(clvs)} CLV observations, "
            f"{cfg.decay_window} needed for the monitoring window")

    # ---- D2: calibration drift -------------------------------------------------
    quoted = [(b.get("quoted_prob"), b["won"]) for b in s if b.get("quoted_prob") is not None]
    if len(quoted) >= cfg.min_bets_calibration:
        mean_quoted = stats.mean([q for q, _ in quoted])
        realised = stats.mean([1.0 if w else 0.0 for _, w in quoted])
        drift = abs(realised - mean_quoted)
        decision.metrics["calibration_drift"] = round(drift, 5)
        if drift > cfg.prob_band:
            decision.reasons.append(
                f"D2 calibration drift: |realised {realised:.3f} - quoted "
                f"{mean_quoted:.3f}| = {drift:.4f} > {cfg.prob_band}")
            decision.action = DEMOTE_TO_PAPER
    else:
        decision.reasons.append(
            f"D2 not judgeable yet: {len(quoted)} bets carry quoted_prob")

    # ---- D3: concentration breach ---------------------------------------------
    pnls = [b.get("pnl") or 0.0 for b in s]
    gains = sum(p for p in pnls if p > 0)
    if gains > 0:
        by_season: dict = {}
        by_team: dict = {}
        for b, p in zip(s, pnls):
            if p > 0:
                by_season[str(b.get("season"))] = by_season.get(str(b.get("season")), 0.0) + p
                if b.get("team"):
                    by_team[str(b.get("team"))] = by_team.get(str(b.get("team")), 0.0) + p
        s_share = max(by_season.values()) / gains if by_season else 0.0
        t_share = max(by_team.values()) / gains if by_team else 0.0
        decision.metrics["max_season_gain_share"] = round(s_share, 5)
        decision.metrics["max_team_gain_share"] = round(t_share, 5)
        if s_share > cfg.max_season_gain_share or t_share > cfg.max_team_gain_share:
            decision.reasons.append(
                f"D3 concentration breach: season share {s_share:.1%} / team share "
                f"{t_share:.1%} above {cfg.max_season_gain_share:.0%} / "
                f"{cfg.max_team_gain_share:.0%}")
            decision.action = DEMOTE_TO_PAPER
    else:
        decision.reasons.append(
            "D3 not judgeable: the window contains no positive PnL to concentrate")

    return decision


def promotion_check(gate_rows: Sequence[dict]) -> dict:
    """The other half of the lifecycle: PAPER -> LIVE requires the promotion
    gates to clear. `gate_rows` are rows from engine.gates.evaluate().

    A strategy may go live only when every promotion gate (G-1..G-6) is PASS —
    a BLOCKED gate means an input we do not hold, and live capital does not run
    on missing inputs. Returns a dict the site can render verbatim.
    """
    promote_gates = ("G-1", "G-2", "G-2b", "G-3", "G-4", "G-5", "G-6")
    by_id = {r.get("gate"): r for r in gate_rows}
    verdicts = {g: (by_id.get(g, {}).get("verdict", "MISSING")) for g in promote_gates}
    ready = all(v == "PASS" for v in verdicts.values())
    return {"action": "PROMOTE_TO_LIVE" if ready else "REMAIN_ON_PAPER",
            "gate_verdicts": verdicts,
            "reason": ("every promotion gate PASS" if ready else
                       "promotion requires PASS on G-1..G-6; any FAIL or BLOCKED "
                       "keeps the strategy on paper")}
