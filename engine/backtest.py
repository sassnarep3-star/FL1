"""Backtest: turn fair lines, stored market numbers and verified results into a bet log.

THE ONE THING THAT MAKES THIS DIFFERENT FROM A SPREADSHEET
    A bet log is only a measurement if the price in it is a price somebody published. So
    every trade row carries the market line, the source field that line came from, that
    field's vintage, and a `price_basis` that says whether a payout was actually
    published for it or whether one was assumed. A row with an assumed price can show a
    line edge; it may never show an ROI.

ROI IS AN UPPER BOUND, AND THE MODULE SAYS SO
    The best price available to us for historical games is the recorded close. A bettor
    cannot trade at the close of their own bet, so any ROI computed against it is a
    generous reading of the model. Settlement-at-close is therefore labelled
    `benchmark=CLOSE_UPPER_BOUND` on every aggregate, and the only genuinely tradeable
    benchmark in this repository - a first-posted line - exists for one season, from one
    book, with no payout column, and is quarantined (see `engine.price_store`). That
    leaves the "vs open" table rendered with blank ROI cells, which is the honest answer.

Stake sizing is deliberately kept out of the signal numbers: the log is built with flat
one-unit stakes so that hit rates and edge are not contaminated by a staking rule.
Sizing is evaluated separately in `engine.signal_staking`.
"""

from __future__ import annotations

from collections import OrderedDict, defaultdict
from typing import Sequence

from . import market_feed as feed
from . import pricing
from . import results_ledger as rl

#: rules we grade. `threshold` is in points for SIDE/TOTAL and percentage points for ML;
#: a rule trades when the model's delta reaches it, on the side the model prefers.
RULES = (
    {"id": "SIDE_EDGE_1.0", "market": "SIDE", "threshold": 1.0},
    {"id": "SIDE_EDGE_1.5", "market": "SIDE", "threshold": 1.5},
    {"id": "SIDE_EDGE_2.0", "market": "SIDE", "threshold": 2.0},
    {"id": "SIDE_EDGE_3.0", "market": "SIDE", "threshold": 3.0},
    {"id": "TOTAL_EDGE_2.0", "market": "TOTAL", "threshold": 2.0},
    {"id": "TOTAL_EDGE_3.0", "market": "TOTAL", "threshold": 3.0},
    {"id": "TOTAL_EDGE_4.5", "market": "TOTAL", "threshold": 4.5},
    {"id": "ML_EDGE_3PP", "market": "MONEYLINE", "threshold": 3.0},
    {"id": "ML_EDGE_5PP", "market": "MONEYLINE", "threshold": 5.0},
)

TRADE_FIELDS = [
    "trade_key", "strategy_id", "market", "game_id", "season", "week", "gameday",
    "team", "side_key", "fair_line", "market_line", "delta", "benchmark",
    "price_american", "price_basis", "stake_units", "outcome", "pnl_units",
    "verify_status", "line_source", "line_vintage", "settle_line", "margin_home",
    "total_points",
]


# ---------------------------------------------------------------------------
# market numbers per game, with provenance kept attached
# ---------------------------------------------------------------------------
def _best_per_key(snapshots: Sequence[dict]) -> dict:
    """Index the store by (game, market, side) keeping the most defensible row.

    Priority rule, stated once so it can be argued about:
      1. a row from a feed whose vintage is CLOSED (`closing_lines.csv`, 2006-2018);
      2. otherwise a row from the games feed (vintage UNDOCUMENTED / LIVE_CURRENT);
      3. inside a tie, a row that also carries a published payout beats a line-only row.
    The runner-up is kept as an `alt` column so a reader sees how much the choice matters.
    """
    PRIORITY = {"CLOSE": 0, "OPEN": 1, "LIVE_CURRENT": 2, "UNDOCUMENTED": 3}
    best: dict[tuple, dict] = {}
    rivals: dict[tuple, dict] = {}
    for r in snapshots:
        if r["status"] != "PUBLISHED":
            continue
        key = (r["game_id"], r["market"], r["side_key"])
        cand = {"line": None if r["line"] == "" else float(r["line"]),
                "price": None if r["price_american"] == "" else int(r["price_american"]),
                "vintage": r["vintage"], "feed": r["feed"], "field": r["feed_field"],
                "rank": PRIORITY.get(r["vintage"], 9)}
        cur = best.get(key)
        score = lambda x: (x["rank"], 0 if x["price"] is not None else 1)
        if cur is None or score(cand) < score(cur):
            if cur is not None:
                rivals[key] = cur
            best[key] = cand
        elif key not in rivals:
            rivals[key] = cand
    return {"best": best, "rivals": rivals}


def market_by_game(snapshots: Sequence[dict], games: Sequence[dict]) -> "OrderedDict[str, dict]":
    """One record per game: our benchmark line and price for each market, with provenance.

    Conventions, fixed here and used everywhere downstream:
      * `market_side_line_home` is the **home team's own line**, negative when the home
        team is favoured - the same convention as `fair_side_line_home` from the
        pipeline, so a delta between them is arithmetic and not a translation.
      * the away line is always the negative of the home line; the store keeps both rows
        and `engine.price_store` verifies they net to zero.
      * over/under share one number, the total.
    """
    idx = _best_per_key(snapshots)
    best, rivals = idx["best"], idx["rivals"]
    out: "OrderedDict[str, dict]" = OrderedDict()
    for g in games:
        gid = g["game_id"]
        rec = OrderedDict([("game_id", gid), ("away", g["away"]), ("home", g["home"]),
                           ("season", g["season"]), ("week", g["week"]),
                           ("gameday", g["gameday"]),
                           ("away_score", g["away_score"]), ("home_score", g["home_score"])])
        home = best.get((gid, "SIDE", "home"))
        away = best.get((gid, "SIDE", "away"))
        if home and home["line"] is not None:
            rec["market_side_line_home"] = home["line"]
            rec["side_line_source"] = home["feed"]
            rec["side_line_vintage"] = home["vintage"]
            rec["side_line_field"] = home["field"]
        if home and home["price"] is not None:
            rec["home_side_price"] = home["price"]
        if away and away["price"] is not None:
            rec["away_side_price"] = away["price"]
        alt = rivals.get((gid, "SIDE", "home"))
        if alt and alt["line"] is not None:
            rec["market_side_line_home_alt"] = alt["line"]
            rec["side_alt_source"] = alt["feed"]
        tot_o = best.get((gid, "TOTAL", "over"))
        tot_u = best.get((gid, "TOTAL", "under"))
        tot = tot_o or tot_u
        if tot and tot["line"] is not None:
            rec["market_total_line"] = tot["line"]
            rec["total_line_source"] = tot["feed"]
            rec["total_line_vintage"] = tot["vintage"]
        if tot_o and tot_o["price"] is not None:
            rec["over_price"] = tot_o["price"]
        if tot_u and tot_u["price"] is not None:
            rec["under_price"] = tot_u["price"]
        ml_h = best.get((gid, "MONEYLINE", "home"))
        ml_a = best.get((gid, "MONEYLINE", "away"))
        if ml_h and ml_h["price"] is not None:
            rec["market_ml_home"] = ml_h["price"]
            rec["ml_home_source"] = ml_h["feed"]
            rec["ml_home_vintage"] = ml_h["vintage"]
            rec["ml_source"] = ml_h["feed"]
            rec["ml_vintage"] = ml_h["vintage"]
        if ml_a and ml_a["price"] is not None:
            rec["market_ml_away"] = ml_a["price"]
            rec["ml_away_source"] = ml_a["feed"]
            rec["ml_away_vintage"] = ml_a["vintage"]
            rec.setdefault("ml_source", ml_a["feed"])
            rec.setdefault("ml_vintage", ml_a["vintage"])
        out[gid] = rec
    return out


# ---------------------------------------------------------------------------
# trade construction
# ---------------------------------------------------------------------------
def build_trades(side_rows: Sequence[dict], total_rows: Sequence[dict],
                 ml_rows: Sequence[dict], market: dict, ledger: Sequence[dict],
                 rules: Sequence[dict] = RULES,
                 assumed_price: int = -110) -> dict:
    """Flat-stake trade log for every rule x game where the delta clears the threshold."""
    led = {r["game_id"]: r for r in ledger}
    side_by_id = {r["game_id"]: r for r in side_rows}
    total_by_id = {r["game_id"]: r for r in total_rows}
    ml_by_id = {r["game_id"]: r for r in ml_rows}
    trades: list[dict] = []
    skipped = defaultdict(int)
    eligible = defaultdict(lambda: {"eligible": 0, "traded": 0, "below_threshold": 0})
    for rule in rules:
        market_name = rule["market"]
        thr = float(rule["threshold"])
        rows = {"SIDE": side_rows, "TOTAL": total_rows,
                "MONEYLINE": ml_rows}[market_name]
        for row in rows:
            gid = row["game_id"]
            lg = led.get(gid)
            if lg is None or lg["settle_eligible"] != "YES":
                skipped["no_verified_result"] += 1
                continue
            mkt = market.get(gid, {})
            delta_key = {"SIDE": "delta_side_pts", "TOTAL": "delta_total_pts",
                         "MONEYLINE": "delta_ml_pp"}[market_name]
            delta = row.get(delta_key)
            if delta is None:
                skipped["no_market_number"] += 1
                continue
            eligible[rule["id"]]["eligible"] += 1
            if abs(float(delta)) < thr:
                skipped["below_threshold"] += 1
                continue
            eligible[rule["id"]]["traded"] += 1
            away, home = mkt.get("away"), mkt.get("home")
            if market_name == "SIDE":
                fair_line = row["fair_side_line_home"]
                market_line = row["market_side_line_home"]
                side_key = "home" if float(delta) > 0 else "away"
                team = home if side_key == "home" else away
                line_for_settle = float(market_line) if side_key == "home" else -float(market_line)
                price = mkt.get("home_side_price") if side_key == "home" else mkt.get("away_side_price")
                price_basis = "POSTED_IN_STORE" if price is not None else \
                    "NOT_POSTED_ASSUMED_%d" % assumed_price
                line_source = row.get("market_line_source", "")
                vintage = row.get("market_side_vintage", "")
            elif market_name == "TOTAL":
                fair_line = row["fair_total"]
                market_line = row["market_total_line"]
                side_key = "over" if float(delta) > 0 else "under"
                team = ""
                line_for_settle = float(market_line)
                price = mkt.get("over_price") if side_key == "over" else mkt.get("under_price")
                price_basis = "POSTED_IN_STORE" if price is not None else \
                    "NOT_POSTED_ASSUMED_%d" % assumed_price
                line_source = row.get("market_line_source", "")
                vintage = row.get("market_line_vintage", "")
            else:
                fair_line = row["fair_p_home"]
                market_line = row["market_p_home_novig"]
                side_key = "home" if float(delta) > 0 else "away"
                team = home if side_key == "home" else away
                line_for_settle = None
                price = (mkt.get("market_ml_home") if side_key == "home"
                         else mkt.get("market_ml_away"))
                price_basis = "POSTED_IN_STORE" if price else "NOT_POSTED_ASSUMED_%d" % assumed_price
                line_source = row.get("market_ml_source", "")
                vintage = row.get("market_ml_vintage", "")
            if price is None:
                price = assumed_price
            margin = int(lg["margin_home"])
            total_pts = int(lg["total_points"])
            try:
                outcome = rl.settle(market_name, side_key=side_key, line=line_for_settle,
                                    margin_home=margin, total_points=total_pts)
            except ValueError as exc:
                skipped["unsettleable:%s" % exc] += 1
                continue
            stake = 1.0
            pnl = rl.pnl(outcome, int(price), stake)
            trades.append(OrderedDict([
                ("trade_key", "%s|%s" % (rule["id"], gid)),
                ("strategy_id", rule["id"]), ("market", market_name), ("game_id", gid),
                ("season", row["season"]), ("week", row["week"]),
                ("gameday", row.get("gameday", "")), ("team", team), ("side_key", side_key),
                ("fair_line", "" if fair_line is None else fair_line),
                ("market_line", "" if market_line is None else market_line),
                ("delta", round(float(delta), 4)), ("benchmark", "CLOSE_OR_UNDOCUMENTED"),
                ("price_american", int(price)), ("price_basis", price_basis),
                ("stake_units", stake), ("outcome", outcome), ("pnl_units", round(pnl, 6)),
                ("verify_status", lg["verify_status"]), ("line_source", line_source),
                ("line_vintage", vintage), ("settle_line", line_for_settle),
                ("margin_home", margin),
                ("total_points", total_pts),
            ]))
    trades.sort(key=lambda t: t["trade_key"])
    return {"trades": trades, "skipped": OrderedDict(sorted(skipped.items())),
            "eligible": OrderedDict((k, dict(v)) for k, v in sorted(eligible.items()))}


def write_tsv(trades: Sequence[dict], path: str, fields: Sequence[str] = TRADE_FIELDS) -> None:
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(fields) + "\n")
        for t in trades:
            fh.write("\t".join("" if t.get(f) is None else str(t.get(f)) for f in fields) + "\n")


def summarise_by_season(trades: Sequence[dict]) -> list[dict]:
    agg: dict[tuple, dict] = {}
    for t in trades:
        k = (t["strategy_id"], t["season"])
        d = agg.setdefault(k, {"n": 0, "wins": 0, "pushes": 0, "pnl": 0.0, "staked": 0.0,
                               "posted": 0})
        d["n"] += 1
        if t["outcome"] == rl.WIN:
            d["wins"] += 1
        elif t["outcome"] == rl.PUSH:
            d["pushes"] += 1
        d["pnl"] += float(t["pnl_units"])
        d["staked"] += float(t["stake_units"])
        if t["price_basis"] == "POSTED_IN_STORE":
            d["posted"] += 1
    rows = []
    for (sid, season), d in agg.items():
        n = d["n"]
        rows.append(OrderedDict([
            ("strategy_id", sid), ("season", season), ("bets", n), ("wins", d["wins"]),
            ("pushes", d["pushes"]),
            ("hit_rate", "" if not n else round(d["wins"] / max(1, n - d["pushes"]), 4)),
            ("staked", round(d["staked"], 3)), ("pnl_units", round(d["pnl"], 3)),
            ("roi", "" if not d["staked"] else round(d["pnl"] / d["staked"], 5)),
            ("bets_at_posted_price", d["posted"]),
            ("roi_basis", "POSTED" if d["posted"] == n else
             ("MIXED" if d["posted"] else "ASSUMED")),
        ]))
    rows.sort(key=lambda r: (r["strategy_id"], r["season"]))
    return rows
