"""Sealed-entry leaderboard scoring.

Ranking rule, in one sentence: rank on the pessimistic end of the estimate, not the
estimate. That single choice is what the brief means by 'remove luck from the
equation' -- a point estimate of expected value is a lottery ticket with a spreadsheet
attached, while its 95% lower bound already contains the entry's sample size, its
variance and its dependence on a handful of games.

Entries are content-addressed (code + config + data snapshot) so a result cannot be
reached by editing a strategy after the games were played. Near-duplicate entries by the
same author are merged before ranking, because otherwise the optimal contest strategy is
to clone one idea twenty times and keep the luckiest clone -- the winner's curse
smuggled back in through the contest design (gate G-13).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Sequence

from . import gates, stats


@dataclass
class Entry:
    entry_id: str
    author: str
    division: str
    bets: list = field(default_factory=list)
    code_blob: str = ""
    config_blob: str = ""
    data_blob: str = ""
    submitted_at: str | None = None
    model_card: dict = field(default_factory=dict)

    def payload(self) -> str:
        return json.dumps({
            "entry_id": self.entry_id, "author": self.author, "division": self.division,
            "code": self.code_blob, "config": self.config_blob, "data": self.data_blob,
            "bets": self.bets,
        }, sort_keys=True, separators=(",", ":"), default=str)

    def sealed_hash(self) -> str:
        """Content address of the whole entry; the thing that makes 'sealed' verifiable."""
        return hashlib.sha256(self.payload().encode("utf-8")).hexdigest()

    def bet_keys(self) -> set:
        return {b.get("game_id", "") + "|" + str(b.get("market", "")) for b in self.bets}


def _score_one(entry: Entry, cfg: gates.GateConfig) -> dict:
    rows, summary = gates.evaluate(entry.bets, cfg)
    by_id = {r.gate_id: r for r in rows}
    settled = [b for b in entry.bets if b.get("won") is not None and not b.get("abstained")]
    returns = [b.get("pnl", 0.0) / max(b.get("stake", 1.0) or 1.0, 1e-9) for b in settled]

    if len(returns) >= 20:
        roi_pt, roi_lo, roi_hi = stats.bootstrap_ci(returns, n_boot=2000)
    else:
        roi_pt = stats.mean(returns) if returns else None
        roi_lo = roi_hi = None

    hit = summary.get("hit_rate")
    n = summary.get("bets_settled", 0)
    hurdle = pricing_hurdle(settled)
    tstat = stats.z_stat(hit, hurdle, n) if (hit is not None and n > 1) else None

    failed = [r.gate_id for r in rows if r.verdict == "FAIL"]
    hard_failed = [g for g in failed if g not in ("G-11",)]  # G-11 is a soft/monitoring gate
    blocked = [r.gate_id for r in rows if r.verdict == "BLOCKED"]

    # concentration penalty (from G-8's reported shares, if computable)
    penalty = 0.0
    g8 = by_id.get("G-8")
    if g8 and g8.value is not None:
        over = max(0.0, g8.value - cfg.max_season_pnl_share)
        penalty = min(0.5, over * 2.0)     # up to a 50% haircut, documented and visible

    lcb = roi_lo
    raw = roi_pt
    score = 0.0 if (hard_failed or lcb is None) else max(lcb * (1.0 - penalty), -1.0)

    # ---- SIGNAL vs STAKING (the brief: a lucky staking run must not mask a bad
    # signal). Signal = stake-independent selection quality (equal-weight unit
    # returns + hurdle test + CLV). Staking = execution/sizing (ROI on staked
    # units, drawdown). Overall rank follows the signal; staking is reported
    # beside it and can never promote an entry whose signal fails.
    SIGNAL_GATES = ("G-2", "G-2b", "G-3", "G-4", "G-9")
    signal_failed = [g for g in failed if g in SIGNAL_GATES]
    clvs = [b.get("clv") for b in settled if b.get("clv") is not None]
    clv_lcb = None
    if len(clvs) >= 20:
        _, clv_lcb, _ = stats.bootstrap_ci(clvs, n_boot=2000)
    signal_lcb = roi_lo                     # equal-weight unit returns, LCB
    if signal_failed or signal_lcb is None:
        signal_score = 0.0 if signal_failed else None
    else:
        signal_score = max(signal_lcb, -1.0)
    staked_units = summary.get("staked_units") or 0.0
    pnl_units = summary.get("pnl_units") or 0.0
    staking_roi = (pnl_units / staked_units) if staked_units else None
    # max drawdown of the cumulative staked PnL path (sizing risk, pure staking)
    cum = peak = 0.0
    max_dd = 0.0
    for b in settled:
        cum += b.get("pnl") or 0.0
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)

    return {
        "entry_id": entry.entry_id,
        "author": entry.author,
        "division": entry.division,
        "sealed_hash": entry.sealed_hash(),
        "bets": n,
        "abstain_rate": summary.get("abstain_rate"),
        "hit_rate": None if hit is None else round(hit, 5),
        "break_even_hurdle": round(hurdle, 5),
        "t_stat": None if tstat is None else round(tstat, 3),
        "roi_point": None if raw is None else round(raw, 5),
        "lcb": None if lcb is None else round(lcb, 5),
        "ucb": None if roi_hi is None else round(roi_hi, 5),
        "pnl_units": summary.get("pnl_units"),
        "concentration_penalty": round(penalty, 4),
        "las": round(score, 5),
        # --- signal block (stake-independent) ---
        "signal_score": None if signal_score is None else round(signal_score, 5),
        "signal_lcb": None if signal_lcb is None else round(signal_lcb, 5),
        "signal_z_vs_hurdle": None if tstat is None else round(tstat, 3),
        "signal_clv_lcb": None if clv_lcb is None else round(clv_lcb, 5),
        "signal_failed_gates": signal_failed,
        # --- staking block (sizing/execution only; never used for overall rank) ---
        "staking_score": None if staking_roi is None else round(staking_roi, 5),
        "staking_pnl_units": round(pnl_units, 4),
        "staking_max_drawdown": round(max_dd, 4),
        "eligible": not hard_failed,
        "failed_hard_gates": hard_failed,
        "blocked_gates": blocked,
        "note": ("ranked on the 95% lower bound of per-unit return; a blocked gate means "
                 "an input we do not have (typically closing-line data), which is reported, "
                 "not imputed"),
    }


def pricing_hurdle(settled: Sequence[dict]) -> float:
    """Break-even at the modal price paid; falls back to -110 only when the log is empty."""
    if not settled:
        from . import pricing
        return pricing.break_even_probability(-110)
    from . import pricing
    counts: dict = {}
    for b in settled:
        counts[b.get("price", -110)] = counts.get(b.get("price", -110), 0) + 1
    modal = max(counts.items(), key=lambda kv: kv[1])[0]
    return pricing.break_even_probability(modal)


def dedupe(entries: Sequence[Entry], threshold: float = 0.8) -> list:
    """Merge same-author entries whose bet sets overlap beyond the threshold."""
    kept: list[dict] = []
    for e in entries:
        target = None
        for slot in kept:
            if slot["entry"].author != e.author:
                continue
            j = stats.jaccard(slot["keys"], e.bet_keys())
            if j > threshold:
                target = slot
                break
        if target is None:
            kept.append({"entry": e, "keys": set(e.bet_keys()), "merged_with": []})
        else:
            target["keys"] |= e.bet_keys()
            target["merged_with"].append(e.entry_id)
    return kept


def rank(entries: Sequence[Entry], cfg: gates.GateConfig | None = None,
         apply_deflator: bool = False, trial_sharpe_sd: float | None = None) -> list[dict]:
    """Produce the leaderboard: deduplicated, gated, ranked on the lower confidence bound.

    `apply_deflator` requires the measured dispersion of Sharpe ratios across every
    strategy the field tried -- including the abandoned ones. If the caller cannot supply
    it we do not apply a deflator and we say so in the row, rather than assuming a trial
    count and pretending the selection effect has been handled.
    """
    cfg = cfg or gates.GateConfig()
    slots = dedupe(entries, cfg.jaccard_merge)
    rows = []
    for slot in slots:
        row = _score_one(slot["entry"], cfg)
        if slot["merged_with"]:
            row["merged_with"] = slot["merged_with"]
        if apply_deflator and trial_sharpe_sd is not None:
            returns = [b.get("pnl", 0.0) / max(b.get("stake", 1.0) or 1.0, 1e-9)
                       for b in slot["entry"].bets if b.get("won") is not None]
            if len(returns) >= 20:
                d = stats.deflated_sharpe_ratio(returns, trials=max(2, len(entries)),
                                                 trial_sharpe_sd=trial_sharpe_sd)
                row["deflated_sharpe_probability"] = round(d["deflated_sharpe_probability"], 4)
                row["las"] = round(row["las"] * d["deflated_sharpe_probability"], 5)
        elif apply_deflator:
            row["deflator_note"] = ("deflator requested but trial_sharpe_sd was not supplied; "
                                    "score left undeflated and the omission is recorded here")
        rows.append(row)
    # per-author live-entry cap (G-13 companion rule): score everything, then keep each
    # author's strongest entries so an entrant cannot win by fielding twenty clones.
    by_author: dict = {}
    for r in rows:
        by_author.setdefault(r["author"], []).append(r)
    for author, rs in by_author.items():
        rs.sort(key=lambda r: -(r["las"] if r["las"] is not None else -1e9))
        for extra in rs[cfg.max_entries_per_author:]:
            extra["eligible"] = False
            extra["rank"] = None
            extra["excluded_reason"] = (f"over the per-author live-entry cap "
                                       f"({cfg.max_entries_per_author}); clones do not buy rank")
    rows.sort(key=lambda r: (not r["eligible"], -(r["signal_score"] if r["signal_score"] is not None else -1e9)))
    for i, r in enumerate(rows, start=1):
        r["rank"] = i if r["eligible"] else None
    # Separate signal ranking from staking ranking. The OVERALL rank is the
    # signal rank: a lucky staking run (big stakes on the winners) must not
    # lift an entry whose selection quality fails. The staking rank is
    # published beside it, and a visible note marks any row where the two
    # disagree — that disagreement is exactly where sizing luck is hiding.
    sig_sorted = sorted([r for r in rows if r["eligible"] and r.get("signal_score") is not None],
                        key=lambda r: -r["signal_score"])
    for i, r in enumerate(sig_sorted, start=1):
        r["signal_rank"] = i
    stk_sorted = sorted([r for r in rows if r["eligible"] and r.get("staking_score") is not None],
                        key=lambda r: -r["staking_score"])
    for i, r in enumerate(stk_sorted, start=1):
        r["staking_rank"] = i
    for r in rows:
        r.setdefault("signal_rank", None)
        r.setdefault("staking_rank", None)
        if (r.get("signal_rank") is not None and r.get("staking_rank") is not None
                and r["staking_rank"] < r["signal_rank"]):
            r["masking_warning"] = ("staking rank %d is better than signal rank %d — "
                                    "the gap is sizing luck until proven otherwise; "
                                    "overall rank follows the signal"
                                    % (r["staking_rank"], r["signal_rank"]))
    return rows
