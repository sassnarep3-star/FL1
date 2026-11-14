"""
FL1 Strategy Lab — line generation, validation gates, luck removal.

WHAT THIS DOES
--------------
Builds a walk-forward backtest of a set of candidate betting strategies over
real closing prices, then pushes every strategy through the same 7 validation
gates. A strategy that fails any gate is reported as REJECTED, not hidden.

ECONOMICS
---------
Every bet is settled at the *closing* price recorded in nflverse/nfldata
games.csv (spread odds / total odds / moneyline). Pushes are removed from both
the numerator and denominator. ROI is stake-normalised at 1 unit per bet.

METHOD NOTES (stated so they can be attacked)
---------------------------------------------
* Signals only use information available BEFORE kickoff of the week being
  predicted: rolling team form from prior weeks, rest days, roof/surface,
  divisional flag, and market-implied ratings built from *prior* weeks' closing
  lines. No in-week leakage.
* `market_devig` strategies compare our model number to the closing number.
  Because we can only observe closing lines (not openers) for the full sample,
  a strategy that "beats the close" is measured against the same close it must
  beat in reality. That is the honest, conservative test: half of any edge
  claimed against a close you cannot bet into is fiction, so we do not use a
  close-minus-model-epsilon trick anywhere.
* Multiple-testing is handled in gate G6 (deflated significance), not by
  cherry-picking.

Run: python3 scripts/strategy_lab.py
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np
import pandas as pd
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data"

# --- tuning constants. These are FIXED before looking at results. -----------
TRAIN_START = 2006          # first season with reliable moneylines in the source
OOS_FRACTION = 0.30         # last 30% of seasons = strict out-of-sample
MIN_BETS = 150              # gate G1: minimum settled bets
MIN_OOS_BETS = 60           # gate G1: minimum settled bets in the OOS window
WILSON_Z = 1.96
ALPHA = 0.05                # gate G3 nominal level, one-sided
N_TRIALS_CONSIDERED = 15    # gate G6: number of strategy variants actually searched


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def load_games() -> pd.DataFrame:
    g = pd.read_csv(RAW / "games.csv")
    g = g[g.game_type == "REG"].copy()
    g["gameday"] = pd.to_datetime(g["gameday"], errors="coerce")
    g = g.sort_values(["season", "week", "gameday"]).reset_index(drop=True)

    # margin / total from home perspective
    g = g[g.home_score.notna() & g.away_score.notna()]
    g["margin"] = g.home_score - g.away_score
    g["gametotal"] = g.home_score + g.away_score

    alias = {"SD": "LAC", "STL": "LAR", "LA": "LAR", "OAK": "LV"}
    for c in ("home_team", "away_team"):
        g[c] = g[c].replace(alias)

    g["ats_margin"] = g.margin + g.spread_line      # home covers if > 0
    g["ats_margin_away"] = -g.ats_margin
    g["total_delta"] = g.gametotal - g.total_line   # over if > 0
    return g


def load_availability() -> pd.DataFrame:
    """2025 weekly availability disadvantage per team, from the official-derived
    nflverse injury release (see data/availability_2025.csv).

    Only 2025 is populated because the nflverse release CDN is blocked in this
    sandbox (irregularity #1). Strategies that use this signal are therefore
    restricted to 2025 and will FAIL gate G1 (sample size). They are reported
    as REJECTED-BY-GATE rather than quietly dropped.
    """
    p = OUT / "availability_2025.csv"
    if not p.exists():
        return pd.DataFrame(columns=["season", "week", "team", "out_w", "q_w", "d_w", "avail_disadv"])
    a = pd.read_csv(p)
    return a


def attach_availability(g: pd.DataFrame) -> pd.DataFrame:
    a = load_availability()
    if a.empty:
        g["home_avail_disadv"] = np.nan
        g["away_avail_disadv"] = np.nan
    else:
        h = a.rename(columns={"team": "home_team", "avail_disadv": "home_avail_disadv"})
        aw = a.rename(columns={"team": "away_team", "avail_disadv": "away_avail_disadv"})
        g = g.merge(h[["season", "week", "home_team", "home_avail_disadv"]],
                    on=["season", "week", "home_team"], how="left")
        g = g.merge(aw[["season", "week", "away_team", "away_avail_disadv"]],
                    on=["season", "week", "away_team"], how="left")
    g["avail_edge_home"] = g.home_avail_disadv - g.away_avail_disadv
    return g


def elo_and_form(g: pd.DataFrame) -> pd.DataFrame:
    """Pre-game Elo + rolling form. Strictly causal: updated after each game."""
    K = 20.0
    HFA = 48.0
    elo: dict[str, float] = {}
    rows = []
    for season, wk_block in g.groupby("season", sort=True):
        # regress to mean between seasons (documented choice)
        for t in list(elo):
            elo[t] = 1505.0 + 0.75 * (elo[t] - 1505.0)

        # running per-team form accumulators reset each season
        form = {t: {"pf": 0.0, "pa": 0.0, "n": 0, "w": 0} for t in elo}

        for _, r in wk_block.iterrows():
            h, a = r.home_team, r.away_team
            eh, ea = elo.get(h, 1505.0), elo.get(a, 1505.0)
            ph = 1.0 / (1.0 + 10 ** (-((eh + HFA) - ea) / 400.0))
            fh, fa = form.get(h), form.get(a)
            rows.append({
                "game_id": r.game_id,
                "home_elo": round(eh, 2),
                "away_elo": round(ea, 2),
                "home_winprob_elo": round(ph, 6),
                "home_net_form": round((fh["pf"] - fh["pa"]) / fh["n"], 3) if fh and fh["n"] else None,
                "away_net_form": round((fa["pf"] - fa["pa"]) / fa["n"], 3) if fa and fa["n"] else None,
                "home_winpct_form": round(fh["w"] / fh["n"], 4) if fh and fh["n"] else None,
                "away_winpct_form": round(fa["w"] / fa["n"], 4) if fa and fa["n"] else None,
            })
            # update
            res = 1.0 if r.margin > 0 else (0.5 if r.margin == 0 else 0.0)
            mov = abs(r.margin)
            mult = math.log(mov + 1.0) * (2.2 / ((abs(eh + HFA - ea) * 0.001) + 2.2))
            delta = K * mult * (res - ph)
            elo[h] = eh + delta
            elo[a] = ea - delta
            for t, pf, pa, w in ((h, r.home_score, r.away_score, int(res == 1.0)),
                                 (a, r.away_score, r.home_score, int(res == 0.0))):
                d = form.setdefault(t, {"pf": 0.0, "pa": 0.0, "n": 0, "w": 0})
                d["pf"] += pf; d["pa"] += pa; d["n"] += 1; d["w"] += w
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Evaluation primitives
# ---------------------------------------------------------------------------
def settle(margin: float, line: float, side: str) -> str:
    """Return 'win' | 'loss' | 'push' for a spread/total bet."""
    if side == "home" or side == "over":
        d = margin - line
    else:
        d = line - margin
    if abs(d) < 1e-9:
        return "push"
    return "win" if d > 0 else "loss"


def american_profit(odds: float) -> float:
    return 100.0 / -odds if odds < 0 else odds / 100.0


def evaluate(bets: pd.DataFrame) -> dict:
    """bets: columns [season, win(bool), push(bool), profit(float), stake(float)]"""
    settled = bets[~bets.push]
    n = len(settled)
    out = {"bets": int(len(bets)), "settled": int(n)}
    if n == 0:
        return out
    wins = int(settled.win.sum())
    out["wins"] = wins
    out["losses"] = n - wins
    out["push_rate"] = round(float(bets.push.mean()), 4) if len(bets) else None
    out["hit_rate"] = round(wins / n, 4)
    out["staked"] = round(float(settled.stake.sum()), 3)
    out["profit"] = round(float(settled.profit.sum()), 3)
    out["roi"] = round(out["profit"] / out["staked"], 4) if out["staked"] else None
    # Wilson CI on hit rate
    p, z = out["hit_rate"], WILSON_Z
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    out["hit_ci_low"] = round(max(0.0, ctr - half), 4)
    out["hit_ci_high"] = round(min(1.0, ctr + half), 4)
    # breakeven hit rate given average odds (vig included, exact)
    avg_dec = float(((settled.profit / settled.stake) + 1).mean())
    out["avg_decimal"] = round(avg_dec, 4)
    out["breakeven_hit"] = round(1.0 / avg_dec, 4)
    out["edge_vs_breakeven"] = round(out["hit_rate"] - out["breakeven_hit"], 4)
    # per-bet ROI t-test (one-sided > 0)
    r = (settled.profit / settled.stake).to_numpy()
    if n > 2 and r.std(ddof=1) > 0:
        t, pv = stats.ttest_1samp(r, 0.0, alternative="greater")
        out["t_stat"] = round(float(t), 3)
        out["p_value"] = round(float(pv), 5)
    out["roi_se"] = round(float(r.std(ddof=1) / math.sqrt(n)), 4) if n > 2 else None
    # max drawdown on cumulative profit
    cum = settled.sort_values(["season"]).profit.cumsum().to_numpy()
    if len(cum):
        peak = np.maximum.accumulate(cum)
        out["max_drawdown"] = round(float((cum - peak).min()), 3)
    return out


def build_bets(df: pd.DataFrame, mask: pd.Series, kind: str, side_fn) -> pd.DataFrame:
    """Turn a signal mask into a settled bet ledger."""
    sub = df[mask].copy()
    if kind == "spread":
        sub["line"] = sub.spread_line
    elif kind == "total":
        sub["line"] = sub.total_line
    else:
        raise ValueError(kind)
    sub["side"] = side_fn(sub)
    rows = []
    for _, r in sub.iterrows():
        if kind == "spread":
            ref = r.margin
            odds = r.home_spread_odds if r.side == "home" else r.away_spread_odds
        else:
            ref = r.gametotal
            odds = r.over_odds if r.side == "over" else r.under_odds
        if pd.isna(odds) or pd.isna(r.line):
            continue
        res = settle(ref, r.line, r.side)
        rows.append({
            "season": int(r.season), "week": int(r.week),
            "game_id": r.game_id, "side": r.side, "line": float(r.line),
            "odds": float(odds),
            "win": res == "win", "push": res == "push",
            "stake": 1.0,
            "profit": (american_profit(float(odds)) if res == "win"
                       else (-1.0 if res == "loss" else 0.0)),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------
def spread_to_prob(spread: float) -> float:
    """Standard logistic mapping of an NFL point spread to a home win probability.

    Fixed a priori (1 point ~ 0.028 logit). Not fitted to outcomes.
    """
    if spread is None or (isinstance(spread, float) and math.isnan(spread)):
        return float("nan")
    return 1.0 / (1.0 + math.exp(-0.028 * float(spread) * 10.0 / 10.0 * 1.0))


def signals(g: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return name -> (mask, kind, side_fn, description, rationale)."""
    S: dict[str, dict] = {}

    # 1. Elo vs market  -----------------------------------------------------
    # Conversion: Elo diff D points -> win prob p = 1/(1+10^(-D/400)).
    # Therefore D = 400 * log10(p/(1-p)). Empirically 1 point of spread ~= 25 Elo,
    # so spread_points = D / 25 = 16 * log10(p/(1-p)). We use the standard
    # 2.7 pts per 100 Elo => 2.7 * (D/100) = 10.8 * log10(p/(1-p)).
    # The constant is FIXED here, before any evaluation, and is not fitted to ROI.
    ELO_PTS_PER_100 = 2.7
    def elo_to_spread(p):
        p = min(max(float(p), 0.02), 0.98)
        return (ELO_PTS_PER_100 * 4.0) * math.log10(p / (1.0 - p))

    g["elo_spread"] = g.home_winprob_elo.apply(elo_to_spread)

    g["elo_vs_market"] = g.elo_spread - g.spread_line

    m = g.elo_vs_market.abs() >= 1.5
    S["ELO_MKT_1.5"] = {
        "mask": m,
        "kind": "spread",
        "side": lambda s: np.where(s.elo_vs_market > 0, "home", "away"),
        "desc": "Bet the side where a causal pre-game Elo number disagrees with the closing spread by >= 1.5 points.",
        "family": "market_devig",
    }

    m = g.elo_vs_market.abs() >= 2.5
    S["ELO_MKT_2.5"] = {
        "mask": m,
        "kind": "spread",
        "side": lambda s: np.where(s.elo_vs_market > 0, "home", "away"),
        "desc": "Same Elo-vs-close signal at a >= 2.5 point disagreement threshold.",
        "family": "market_devig",
    }

    # 2. rest advantage -----------------------------------------------------
    rest = g.home_rest - g.away_rest
    m = (rest >= 3) & g.spread_line.notna()
    S["REST_ADV"] = {
        "mask": m, "kind": "spread",
        "side": lambda s: np.full(len(s), "home"),
        "desc": "Home team with >= 3 more rest days than the visitor; bet the rested home side.",
        "family": "situational",
    }

    m = (g.away_rest - g.home_rest >= 3) & g.spread_line.notna()
    S["REST_ADV_AWAY"] = {
        "mask": m, "kind": "spread",
        "side": lambda s: np.full(len(s), "away"),
        "desc": "Visitor with >= 3 more rest days than the home team.",
        "family": "situational",
    }

    # 3. divisional underdogs (fade the public) -----------------------------
    dog_home = (g.spread_line < 0) & (g.div_game == 1)
    S["DIV_HOME_DOG"] = {
        "mask": dog_home, "kind": "spread",
        "side": lambda s: np.full(len(s), "home"),
        "desc": "Divisional games: take the home underdog.",
        "family": "situational",
    }

    dog_away = (g.spread_line > 0) & (g.div_game == 1)
    S["DIV_AWAY_DOG"] = {
        "mask": dog_away, "kind": "spread",
        "side": lambda s: np.full(len(s), "away"),
        "desc": "Divisional games: take the road underdog.",
        "family": "situational",
    }

    # 4. big favourites / underdog regression -----------------------------
    m = g.spread_line >= 10.0
    S["BIG_FAV_FADE"] = {
        "mask": m, "kind": "spread",
        "side": lambda s: np.full(len(s), "away"),
        "desc": "Fade a home favourite of 10+ with the road underdog.",
        "family": "situational",
    }

    # 5. totals: dome effect ------------------------------------------------
    m = (g.roof.isin(["dome", "closed"])) & g.total_line.notna()
    S["DOME_OVER"] = {
        "mask": m, "kind": "total",
        "side": lambda s: np.full(len(s), "over"),
        "desc": "Indoor games: bet the over (no weather variance).",
        "family": "situational",
    }

    m = (g.roof.isin(["dome", "closed"])) & g.total_line.notna()
    S["DOME_UNDER"] = {
        "mask": m, "kind": "total",
        "side": lambda s: np.full(len(s), "under"),
        "desc": "Indoor games: bet the under. (Paired with DOME_OVER to show the search is symmetric.)",
        "family": "situational",
    }

    # 6. wind fade ----------------------------------------------------------
    m = (g.wind.fillna(0) >= 15) & g.total_line.notna()
    S["WIND15_UNDER"] = {
        "mask": m, "kind": "total",
        "side": lambda s: np.full(len(s), "under"),
        "desc": "Games with wind >= 15 mph: bet the under.",
        "family": "weather",
    }

    # 7. sharp-side / steam proxy: large spread but short price ------------
    # (documented as UNTESTABLE with closing-only data; kept as a control)
    # 8. ratio of market-implied win prob to Elo win prob (probability space) --
    mk_p = g.spread_line.apply(spread_to_prob)
    g["prob_gap"] = g.home_winprob_elo - mk_p
    m = g.prob_gap.abs() >= 0.06
    S["PROB_GAP_6PT"] = {
        "mask": m, "kind": "spread",
        "side": lambda s: np.where(s.prob_gap > 0, "home", "away"),
        "desc": "Win-probability gap: model win prob vs the win prob implied by the closing spread, >= 6 pts.",
        "family": "market_devig",
    }

    # 9. rest-advantage + Elo agreement (conjunction) ------------------------
    m = ((g.home_rest - g.away_rest) >= 3) & (g.elo_vs_market >= 1.0)
    S["REST_AND_ELO"] = {
        "mask": m, "kind": "spread",
        "side": lambda s: np.full(len(s), "home"),
        "desc": "Conjunction: home rested 3+ days more AND Elo also likes the home side by 1+.",
        "family": "conjunction",
    }

    # 10. divisional underdog + Elo agreement -------------------------------
    m = (g.div_game == 1) & (g.spread_line > 0) & (g.elo_vs_market <= 0)
    S["DIV_DOG_AND_ELO"] = {
        "mask": m, "kind": "spread",
        "side": lambda s: np.full(len(s), "away"),
        "desc": "Divisional road dog where Elo also rates the home side no better than the market.",
        "family": "conjunction",
    }

    # 11. weather conjunction: wind + cold ---------------------------------
    m = (g.wind.fillna(0) >= 12) & (g.temp.fillna(100) <= 40) & g.total_line.notna()
    S["WIND_COLD_UNDER"] = {
        "mask": m, "kind": "total",
        "side": lambda s: np.full(len(s), "under"),
        "desc": "Cold AND windy (temp <= 40F, wind >= 12 mph): bet the under.",
        "family": "weather",
    }

    # 12. availability disadvantage (2025 only -> expected to fail G1) ------
    m = (g.avail_edge_home.notna()) & (g.avail_edge_home.abs() >= 1.5)
    S["AVAIL_EDGE_1.5"] = {
        "mask": m, "kind": "spread",
        "side": lambda s: np.where(s.avail_edge_home > 0, "away", "home"),
        "desc": ("Bet AGAINST the more depleted team (weighted Out/Doubtful/Questionable starter loss). "
                 "2025 only - fails G1 by design; included to show the pipeline works, not to claim edge."),
        "family": "availability",
    }

    S["__CONTROL_MARKET"] = {
        "mask": g.spread_line.notna(),
        "kind": "spread",
        "side": lambda s: np.full(len(s), "home"),
        "desc": "CONTROL: bet every home team at the close. Not a strategy — it measures house vig.",
        "family": "control",
    }

    return S


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------
def gates(all_bets: pd.DataFrame, split_season: int) -> tuple[dict, list[dict]]:
    full = evaluate(all_bets)
    oos = evaluate(all_bets[all_bets.season >= split_season])
    ins = evaluate(all_bets[all_bets.season < split_season])

    G = {}

    # G1 sample size
    G["G1_sample_size"] = bool(full.get("settled", 0) >= MIN_BETS
                               and oos.get("settled", 0) >= MIN_OOS_BETS)

    # G2 positive ROI in-sample AND out-of-sample
    G["G2_roi_both_periods"] = bool(
        (ins.get("roi") or -1) > 0 and (oos.get("roi") or -1) > 0
    )

    # G3 statistical significance, one-sided, with significance tested on ROI
    p = full.get("p_value")
    G["G3_roi_significance"] = bool(p is not None and p < ALPHA)

    # G4 hit rate must clear the vig breakeven with a positive lower bound
    G["G4_beats_vig"] = bool(
        full.get("hit_ci_low") is not None and
        full["hit_ci_low"] > full.get("breakeven_hit", 1.0)
    )

    # G5 stability: no single season contributes more than 40% of total profit
    if "season" in all_bets and all_bets[~all_bets.push].shape[0]:
        s = all_bets[~all_bets.push].groupby("season").profit.sum()
        tot = s.sum()
        share = (s.max() / tot) if tot and tot != 0 else 0
        G["G5_no_single_season_dependency"] = bool(tot > 0 and share <= 0.40)
        G["G5_max_season_share"] = round(float(share), 3) if tot else None
    else:
        G["G5_no_single_season_dependency"] = False
        G["G5_max_season_share"] = None

    # G6 deflated significance (Bonferroni over the searched variants)
    adj = ALPHA / N_TRIALS_CONSIDERED
    G["G6_multiplicity_adjusted"] = bool(
        full.get("p_value") is not None and full["p_value"] < adj
    )
    G["G6_adjusted_alpha"] = round(adj, 5)

    # G7 drawdown control: expected max drawdown must be smaller than total profit
    G["G7_drawdown_bounded"] = bool(
        full.get("max_drawdown") is not None and full.get("profit") is not None
        and abs(full["max_drawdown"]) < abs(full["profit"])
    )

    passed = sum(1 for k, v in G.items() if k.startswith("G") and isinstance(v, bool) and v)
    G["gates_passed"] = passed
    G["verdict"] = ("APPROVED" if passed == 7 else
                    "REJECTED")
    return G, [full, ins, oos]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    g = load_games()
    g = g[g.season >= TRAIN_START].copy()
    g = g.merge(elo_and_form(g), on="game_id", how="left")
    g = attach_availability(g)

    seasons = sorted(g.season.unique())
    split_season = seasons[int(len(seasons) * (1 - OOS_FRACTION))]
    print(f"seasons={seasons[0]}..{seasons[-1]}  split={split_season}")

    sig = signals(g)
    summary, leaderboard = [], []

    for name, s in sig.items():
        bets = build_bets(g, s["mask"], s["kind"], s["side"])
        if bets.empty:
            continue
        G, periods = gates(bets, split_season)
        full, ins, oos = periods
        row = {
            "strategy_id": name,
            "family": s["family"],
            "market": s["kind"],
            "description": s["desc"],
            "seasons_tested": f"{seasons[0]}-{seasons[-1]}",
            "oos_from": split_season,
            "bets": full.get("bets"), "settled": full.get("settled"),
            "hit_rate": full.get("hit_rate"),
            "hit_ci_low": full.get("hit_ci_low"),
            "hit_ci_high": full.get("hit_ci_high"),
            "breakeven_hit": full.get("breakeven_hit"),
            "roi": full.get("roi"),
            "roi_se": full.get("roi_se"),
            "profit_units": full.get("profit"),
            "max_drawdown": full.get("max_drawdown"),
            "is_roi": ins.get("roi"),
            "oos_roi": oos.get("roi"),
            "oos_settled": oos.get("settled"),
            "p_value": full.get("p_value"),
            **{k: v for k, v in G.items()},
        }
        summary.append(row)

        # per-season ledger for charts / audit
        bs = bets[~bets.push].groupby("season").agg(
            settled=("profit", "size"), profit=("profit", "sum"),
            wins=("win", "sum"), roi=("profit", lambda x: x.sum() / len(x)),
        ).reset_index()
        for _, r in bs.iterrows():
            leaderboard.append({
                "strategy_id": name, "season": int(r.season),
                "settled": int(r.settled), "wins": int(r.wins),
                "profit_units": round(float(r.profit), 3),
                "roi": round(float(r.roi), 4),
            })

    df = pd.DataFrame(summary)
    order = {"APPROVED": 0, "REJECTED": 1}
    df["_o"] = df.verdict.map(order)
    df = df.sort_values(["_o", "roi"], ascending=[True, False]).drop(columns="_o")
    df.to_csv(OUT / "strategies.csv", index=False)
    pd.DataFrame(leaderboard).sort_values(["strategy_id", "season"]).to_csv(
        OUT / "leaderboard_by_season.csv", index=False)

    # Leaderboard = rank by gates passed then OOS ROI. Only APPROVED items are
    # eligible for rewards; REJECTED items are listed with zero reward.
    lb = df.copy()
    lb["rank"] = lb.index + 1
    lb["reward_eligible"] = lb.verdict.eq("APPROVED")
    lb["reward_units"] = np.where(lb.reward_eligible, 10.0, 0.0)
    lb.to_csv(OUT / "leaderboard.csv", index=False)

    print(df[["strategy_id", "settled", "hit_rate", "roi", "oos_roi",
              "p_value", "gates_passed", "verdict"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
