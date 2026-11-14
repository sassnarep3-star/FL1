"""The demotion gate: what sends a live strategy back to paper, and what keeps it there.

WHY A PROMOTION RULE IS HALF A RULE
    Promotion gates answer "may this strategy run money?". Nothing in the repository answered
    "when does it stop?". The three rules published on `validation.html` (D1 live-decay,
    D2 calibration drift, D3 concentration breach) were defined there and left inactive,
    because D1 needs a benchmark price and no price existed in the repo. The price store now
    supplies a recorded market number per game, so D1 can be *evaluated* - with one caveat
    this module states instead of hiding:

        the recorded number is a close or an undocumented-vintage price, not a timestamped
        quote taken before the pick was made. A decay monitor built on it measures
        "did our edge against the closing number shrink", which is strictly weaker than
        "is our closing-line value negative". It is reported as `D1-SUBSTITUTE`, not as D1.

WHAT THE GATE DOES WHEN IT FIRES
    Demotion is automatic and non-discretionary, it moves the strategy to PAPER (picks are
    still logged, no capital), and the strategy cannot come back on profit alone: it must
    clear a fresh paper window (`reprobe_min_bets`) with a positive lower bound on points
    beat *and* re-clear the promotion gates. Two demotions in one season escalate to a
    season suspension, because a third chance is how a contest ends up funding noise.

A fourth rule (D4) is the one every leaderboard in this genre forgets: an integrity breach
in the data the strategy is scored on demotes it immediately, because a strategy cannot be
judged on numbers we do not trust. D4 is fail-closed: missing coverage is a breach, not an
absence of evidence in the strategy's favour.
"""

from __future__ import annotations

from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from typing import Sequence

from . import results_ledger as rl
from . import stats as st

RULE_FIELDS = ["strategy_id", "rule", "name", "measured", "threshold", "verdict", "why",
               "window_bets", "first_breach", "action"]


@dataclass
class DemotionConfig:
    """Thresholds are ours to propose and a reviewer's to change; the arithmetic is not."""
    min_window: int = 60
    window: int = 200
    d1_lb_fail: float = 0.0
    d1_negative_streak: int = 60
    d2_slope_band: tuple = (0.40, 1.60)
    d2_hit_band_pp: float = 6.0
    d3_season_cap: float = 0.35
    d3_team_cap: float = 0.30
    d3_venue_cap: float = 0.35
    d4_price_gap_pct_max: float = 5.0
    d4_quarantine_pct_max: float = 0.5
    d4_verification_pct_min: float = 0.0
    max_demotions_per_season: int = 2
    reprobe_min_bets: int = 150
    states: tuple = ("PAPER", "LIVE", "DEMOTE", "SUSPENDED")


@dataclass
class StrategyState:
    strategy_id: str
    state: str = "PAPER"
    demotions_this_season: int = 0
    season: object = None
    paper_bets_since_demotion: int = 0
    notes: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# the four monitors
# ---------------------------------------------------------------------------
def _points_beat(t: dict) -> float:
    """Same definition as `engine.signal_staking._points_beat`, on the same struck number."""
    line = t.get("settle_line")
    if line is None:
        line = t.get("market_line")
    if t["market"] == "SIDE":
        home_line = float(line)
        return float(t["margin_home"]) + (home_line if t["side_key"] == "home" else -home_line)
    if t["market"] == "TOTAL":
        line = float(line)
        return (float(t["total_points"]) - line) if t["side_key"] == "over" \
            else (line - float(t["total_points"]))
    return float(t["margin_home"])


def d1_live_decay(trades: Sequence[dict], cfg: DemotionConfig) -> dict:
    """Trailing mean points beat, and its 95% lower bound, on the monitor window."""
    tail = list(trades)[-cfg.window:]
    vals = [_points_beat(t) for t in tail]
    n = len(vals)
    if n < cfg.min_window:
        return {"rule": "D1-SUBSTITUTE", "verdict": "NOT_EVALUABLE",
                "measured": "n=%d" % n, "threshold": ">=%d settled bets" % cfg.min_window,
                "why": "the monitor needs a window before it can call anything decay",
                "values": []}
    mean = sum(vals) / n
    if n >= 30:
        _, lb, _ub = st.bootstrap_ci(vals)
    else:
        lb = mean
    # negative streak, as the rule is written: consecutive settled bets with a losing run
    streak = 0
    for v in reversed(vals):
        if v < 0:
            streak += 1
        else:
            break
    trig = (lb <= cfg.d1_lb_fail) or (streak >= cfg.d1_negative_streak)
    return {"rule": "D1-SUBSTITUTE",
            "verdict": "TRIGGERED" if trig else "OK",
            "measured": "trailing mean %+.4f pts, 95%% LB %+.4f, losing run %d bets" % (mean, lb, streak),
            "threshold": "LB <= %.2f pts or negative run >= %d bets" % (cfg.d1_lb_fail, cfg.d1_negative_streak),
            "why": ("edge against the recorded market number has decayed to nothing on the "
                    "monitor window" if trig else
                    "edge against the recorded market number is still positive at 95%"),
            "values": [round(v, 4) for v in vals]}


def d2_calibration(trades: Sequence[dict], cfg: DemotionConfig) -> dict:
    """Stated probabilities must keep earning their keep: slope and hit-rate band."""
    tail = [t for t in trades][-cfg.window:]
    xs, ys = [], []
    stated = []
    for t in tail:
        if t["market"] == "MONEYLINE":
            continue
        try:
            xs.append(float(t["delta"]))
            ys.append(_points_beat(t))
        except (TypeError, ValueError):
            continue
    if len(xs) < cfg.min_window:
        return {"rule": "D2", "verdict": "NOT_EVALUABLE", "measured": "n=%d" % len(xs),
                "threshold": ">=%d" % cfg.min_window,
                "why": "slope on this few bets is noise dressed as a diagnostic", "values": []}
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    den = sum((x - mx) ** 2 for x in xs)
    slope = float("nan") if den <= 0 else sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
    wins = sum(1 for t in tail if t["outcome"] == rl.WIN)
    live = sum(1 for t in tail if t["outcome"] in (rl.WIN, rl.LOSE))
    hit = wins / live if live else 0.0
    implied = [abs(float(t["delta"])) for t in tail]
    lo, hi = cfg.d2_slope_band
    trig = not (lo <= slope <= hi) if slope == slope else True
    why = ("slope of realised points beat on stated edge is %s, outside [%s, %s]"
           % (("%.3f" % slope) if slope == slope else "undefined", lo, hi))
    return {"rule": "D2", "verdict": "TRIGGERED" if trig else "OK",
            "measured": "slope %s, realised hit %.1f%% over %d settled bets (mean stated edge "
                        "%.2f pts)" % (("%.3f" % slope) if slope == slope else "undefined",
                                       100 * hit, live, (sum(implied) / len(implied)) if implied else 0),
            "threshold": "slope in [%s, %s]; hit rate within %.1f pp of the stated band"
                         % (lo, hi, cfg.d2_hit_band_pp),
            "why": why, "values": [round(s, 4) for s in slope and [slope] or []]}


def d3_concentration(trades: Sequence[dict], cfg: DemotionConfig) -> dict:
    """One season, one team or one venue must not be carrying the whole PnL."""
    if len(trades) < cfg.min_window:
        return {"rule": "D3", "verdict": "NOT_EVALUABLE", "measured": "n=%d" % len(trades),
                "threshold": ">=%d" % cfg.min_window, "why": "no concentration claim without a window",
                "values": []}
    pos = [t for t in trades if float(t["pnl_units"]) > 0]
    total_pos = sum(float(t["pnl_units"]) for t in pos) or 1.0
    def share(key):
        agg = defaultdict(float)
        for t in pos:
            agg[str(t.get(key) or "")] += float(t["pnl_units"])
        top = max(agg.items(), key=lambda kv: kv[1]) if agg else ("", 0.0)
        return top[0], top[1] / total_pos
    s_season, sh_season = share("season")
    s_team, sh_team = share("team")
    worst = max(((sh_season, "season", s_season, cfg.d3_season_cap),
                 (sh_team, "club", s_team, cfg.d3_team_cap)), key=lambda x: x[0] / max(1e-9, x[3]))
    trig = worst[0] > worst[3]
    return {"rule": "D3", "verdict": "TRIGGERED" if trig else "OK",
            "measured": "largest share of net profit: %s %s at %.1f%%" % (worst[1], worst[2], 100 * worst[0]),
            "threshold": "season <= %.0f%%, club <= %.0f%% of net PnL"
                         % (100 * cfg.d3_season_cap, 100 * cfg.d3_team_cap),
            "why": ("a single %s is carrying the result" % worst[1]) if trig
                   else "profit is spread across seasons and clubs", "values": []}


def d4_integrity(store_stats: dict, ledger_stats: dict, cfg: DemotionConfig) -> dict:
    """Fail closed if the data the strategy is scored on has holes in it."""
    gap = float(store_stats.get("price_gap_pct", 100.0))
    quar = float(ledger_stats.get("official_game_mismatches", 0))
    total_games = float(ledger_stats.get("official_game_checked", 0)) or 1.0
    quar_pct = 100.0 * quar / total_games
    reasons = []
    if gap > cfg.d4_price_gap_pct_max:
        reasons.append("market number missing for %.1f%% of settled bets (cap %.1f%%)"
                       % (gap, cfg.d4_price_gap_pct_max))
    if quar_pct > cfg.d4_quarantine_pct_max:
        reasons.append("%.1f%% of officially checked games disagree between feeds (cap %.1f%%)"
                       % (quar_pct, cfg.d4_quarantine_pct_max))
    return {"rule": "D4", "verdict": "TRIGGERED" if reasons else "OK",
            "measured": "price gap %.1f%%; feed contradictions %d of %d"
                        % (gap, int(quar), int(total_games)),
            "threshold": "gap <= %.1f%%; contradictions <= %.1f%%"
                         % (cfg.d4_price_gap_pct_max, cfg.d4_quarantine_pct_max),
            "why": "; ".join(reasons) if reasons else
            "the window is priced and the feeds agree, so the score means something",
            "values": []}


# ---------------------------------------------------------------------------
# evaluation and the state machine
# ---------------------------------------------------------------------------
def first_breach(trades: Sequence[dict], cfg: DemotionConfig, step: int = 50) -> dict:
    """Walk the log in windows and report the earliest point any monitor fires.

    Returns the breach's season/week/game so a reviewer can go and look at that slate,
    which is the difference between a rule and a decoration.
    """
    ordered = list(trades)
    for end in range(cfg.min_window, len(ordered) + 1, step):
        window = ordered[:end]
        r = d1_live_decay(window, cfg)
        if r["verdict"] == "TRIGGERED":
            at = ordered[end - 1]
            return {"rule": r["rule"], "at_index": end, "season": at["season"],
                    "week": at["week"], "game_id": at["game_id"], "measured": r["measured"]}
    return {"rule": "", "at_index": "", "season": "", "week": "", "game_id": "",
            "measured": "no breach at any window boundary from n=%d to n=%d"
                        % (cfg.min_window, len(ordered))}


def evaluate(strategy_id: str, trades: Sequence[dict], store_stats: dict,
             ledger_stats: dict, cfg: DemotionConfig | None = None,
             state: StrategyState | None = None) -> dict:
    cfg = cfg or DemotionConfig()
    state = state or StrategyState(strategy_id=strategy_id)
    rows = [d1_live_decay(trades, cfg), d2_calibration(trades, cfg),
            d3_concentration(trades, cfg), d4_integrity(store_stats, ledger_stats, cfg)]
    breach = first_breach(trades, cfg)
    triggered = [r for r in rows if r["verdict"] == "TRIGGERED"]
    new_state = state.state
    if state.state == "LIVE" and triggered:
        new_state = "DEMOTE"
    elif state.state == "LIVE" and not triggered:
        new_state = "LIVE"
    elif state.state == "DEMOTE":
        new_state = "DEMOTE"
    elif state.state == "PAPER" and not triggered:
        new_state = "PAPER"
    elif state.state == "PAPER":
        new_state = "PAPER"
    demotions = state.demotions_this_season + (1 if new_state == "DEMOTE" and state.state != "DEMOTE" else 0)
    if demotions >= cfg.max_demotions_per_season:
        new_state = "SUSPENDED"
    out = []
    for r in rows:
        out.append(OrderedDict([
            ("strategy_id", strategy_id), ("rule", r["rule"]),
            ("name", {"D1-SUBSTITUTE": "live-decay monitor, measured on the recorded market number",
                      "D2": "calibration drift", "D3": "concentration breach",
                      "D4": "data-integrity breach (fail closed)"}[r["rule"]]),
            ("measured", r["measured"]), ("threshold", r["threshold"]),
            ("verdict", r["verdict"]), ("why", r["why"]),
            ("window_bets", len(trades[-cfg.window:])),
            ("first_breach", "%s" % ("season %s week %s %s" % (breach["season"], breach["week"],
                                                               breach["game_id"])
                                     if breach["rule"] and breach["rule"] == r["rule"] else
                                     ("none" if not breach["rule"] else "not this rule"))),
            ("action", "auto-demote to PAPER; no discretionary rescue"
             if r["verdict"] == "TRIGGERED" else "none"),
        ]))
    return {"rows": out, "triggered": [r["rule"] for r in triggered],
            "decision": new_state, "first_breach": breach,
            "state": StrategyState(strategy_id=strategy_id, state=new_state,
                                   demotions_this_season=demotions,
                                   notes=[r["why"] for r in triggered]),
            "repromotion": reprpromotion(state, new_state, trades, cfg)}


def reprpromotion(prev: StrategyState, now: str, trades: Sequence[dict],
                  cfg: DemotionConfig) -> dict:
    """The hysteresis: what it takes to come back, and why profit alone is not enough."""
    settled = [t for t in trades if t["outcome"] in (rl.WIN, rl.LOSE)]
    n = len(settled)
    if now not in ("DEMOTE", "SUSPENDED"):
        return {"eligible": None, "why": "not demoted; the paper window rule does not apply"}
    vals = [_points_beat(t) for t in settled]
    lb = None
    if n >= 30:
        _, lb, _ = st.bootstrap_ci(vals)
    enough = n >= cfg.reprobe_min_bets
    positive = lb is not None and lb > 0
    return OrderedDict([
        ("eligible", bool(enough and positive)),
        ("paper_bets_after_demotion", n),
        ("required", cfg.reprobe_min_bets),
        ("lower_bound_points_beat", "" if lb is None else round(lb, 5)),
        ("why", ("needs %d settled paper bets with a positive 95%% lower bound before a "
                 "re-promotion vote, and must re-clear the promotion gates; profit alone "
                 "cannot reopen a fund" % cfg.reprobe_min_bets)
                if not (enough and positive) else
                "paper window cleared on both counts; re-promotion still requires the "
                "promotion gates to pass again"),
    ])


def price_gap_pct(trades: Sequence[dict]) -> float:
    """Share of settled bets with no market number in the store (the D4 input)."""
    if not trades:
        return 100.0
    missing = sum(1 for t in trades if str(t.get("price_basis", "")).startswith("NOT_POSTED"))
    return 100.0 * missing / len(trades)
