"""Verified results feed: the thing that makes a backtest, and an ROI number, possible.

WHAT A "RESULT" HAS TO CLEAR BEFORE IT IS TRUSTED
    A result that comes from the same file as the price is not a verification, it is a
    tautology. This module therefore admits a game only with an explicit status:

        MATCHED_TWO_FEEDS            scores agree between an independent feed and the
                                     official nfl.com transcription (game-level check)
        SINGLE_FEED_SEASON_RECONCILED feed scores roll up to the official published
                                     standings table for that season (aggregate check)
        SINGLE_FEED                  feed only; usable for method development, never for
                                     a published claim of skill
        QUARANTINE_MISMATCH          the feeds disagree - the game settles nothing
        NO_RESULT                    the game has not been played (or is not in the feed)

    A quarantined game is stored, rendered, and excluded from settlement. It is never
    silently dropped, because "we found 3 contradictions" is a fact a reader is owed.

SETTLEMENT RULES (the ones the market uses, stated so a reviewer can object to them)
    SIDE      the side you bet covers if  (its own margin) + (its own line) > 0; equal => push
              so an away dog of +3.0 covers iff the home margin is below 3.0
    TOTAL     over wins if  total > line; under wins if total < line; equal => push
    MONEYLINE winner wins; a tied game => push for both sides (NFL rules: a wager on a
              tied game is a push unless the market is 3-way)

    Overtime counts as part of the game for all three markets, which is what the
    "result"/"total" columns of the upstream feed represent (documented: result = home -
    away, total = sum, both NA before the game is played).

Reproduce:  python3 -m engine.results_ledger
"""

from __future__ import annotations

from collections import OrderedDict, defaultdict
from typing import Iterable, Sequence

from . import market_feed as feed

LEDGER_FIELDS = [
    "game_id", "season", "game_type", "week", "gameday", "away", "home",
    "away_score", "home_score", "margin_home", "total_points", "result_source",
    "verify_status", "settle_eligible", "official_week", "official_date", "join_basis",
]

SETTLE_FIELDS = [
    "trade_key", "game_id", "market", "side_key", "team", "line", "price_american",
    "price_basis", "margin_home", "total_points", "outcome", "pnl_units", "stake_units",
]

WIN, LOSE, PUSH = "WIN", "LOSE", "PUSH"


# ---------------------------------------------------------------------------
# settlement
# ---------------------------------------------------------------------------
def settle_side(line: float, margin_home: float, side_key: str = "home") -> str:
    """Grade one side of a spread.

    `line` is the number posted *for the side being bet*, in that side's own perspective
    (negative = that side is the favourite). The side covers when its own margin plus its
    own line is positive, so the away side's margin is the negated home margin. Getting
    this sign wrong is the classic off-by-a-whole-side error: it turns "away +3 lost by 4"
    into a win, and it is why `settle_total` takes `side_key` too.
    """
    own = float(margin_home) if side_key == "home" else -float(margin_home)
    adj = own + float(line)
    if adj > 0:
        return WIN
    if adj < 0:
        return LOSE
    return PUSH


def settle_total(line: float, total_points: float, side_key: str = "over") -> str:
    """`over` wins when the total exceeds the number; `under` wins when it falls short."""
    diff = float(total_points) - float(line)
    if side_key == "under":
        diff = -diff
    if diff > 0:
        return WIN
    if diff < 0:
        return LOSE
    return PUSH


def settle_moneyline(margin_home: float, side_key: str) -> str:
    if margin_home == 0:
        return PUSH
    home_won = margin_home > 0
    won = home_won if side_key == "home" else (not home_won)
    return WIN if won else LOSE


def settle(market: str, *, side_key: str, line, margin_home, total_points) -> str:
    if margin_home is None or total_points is None:
        raise ValueError("cannot settle without a result")
    if market == "SIDE":
        if line is None:
            raise ValueError("cannot settle a spread without a number")
        return settle_side(float(line), float(margin_home), side_key)
    if market == "TOTAL":
        if line is None:
            raise ValueError("cannot settle a total without a number")
        return settle_total(float(line), float(total_points), side_key)
    if market == "MONEYLINE":
        return settle_moneyline(float(margin_home), side_key)
    raise ValueError("no settlement rule for market %r" % market)


def pnl(outcome: str, price_american: int, stake: float = 1.0) -> float:
    """Profit in units of stake. Push and void return exactly zero."""
    if outcome in (PUSH, "VOID"):
        return 0.0
    if outcome == WIN:
        return stake * (price_american / 100.0 if price_american > 0 else 100.0 / -price_american)
    return -stake


# ---------------------------------------------------------------------------
# the ledger
# ---------------------------------------------------------------------------
def build_ledger(games: Sequence[dict], official_results: Sequence[dict],
                 official_standings_by_season: "OrderedDict[str, list[dict]]",
                 official_season: int | None = None) -> dict:
    """`official_season` restricts the game-level join to the season the transcription
    covers. Without it a 2024 game could be matched to a 2026 row of the same matchup and
    week, which would look exactly like a score contradiction and be nothing of the sort."""
    """One row per game, with its verification status attached.

    `official_standings_by_season` maps season -> rows of the official table
    (abbr/w/l/t/pf/pa). Reconciliation is a recount from game rows, not a comparison of
    two tables that were copied from each other.
    """
    off_by_key: dict[tuple, dict] = {}
    for r in official_results:
        off_by_key[(r["date"], r["away"], r["home"])] = r
    # Fallback join for a game whose listed date differs from the page's date column (a
    # Monday-night game listed on the Sunday of its week, for instance). It is only allowed
    # for the season the transcription actually covers, and only when the (week, matchup)
    # key is unique on both sides - otherwise it can pair eras that merely share a fixture.
    off_by_sched: dict[tuple, list] = {}
    for r in official_results:
        off_by_sched.setdefault((r["week"], r["away"], r["home"]), []).append(r)
    off_by_sched = {k: v[0] for k, v in off_by_sched.items() if len(v) == 1}

    season_tally: "OrderedDict[int, dict]" = OrderedDict()
    for g in games:
        season_tally.setdefault(g["season"], []).append(g)

    rows = []
    stats = Counter()
    for g in games:
        played = g["away_score"] is not None and g["home_score"] is not None
        margin = None if not played else g["home_score"] - g["away_score"]
        total = None if not played else g["home_score"] + g["away_score"]
        # internal consistency of the feed's own derived columns
        if played:
            if g["margin_home"] is not None and int(g["margin_home"]) != margin:
                stats["feed_result_column_disagrees"] += 1
            if g["total_points"] is not None and int(g["total_points"]) != total:
                stats["feed_total_column_disagrees"] += 1
            else:
                stats["feed_total_column_agrees"] += 1
        off = off_by_key.get((g["gameday"], g["away"], g["home"]))
        join = "date" if off is not None else ""
        if off is None and (official_season is None or g["season"] == official_season):
            off = off_by_sched.get((g["week"], g["away"], g["home"]))
            join = "week" if off is not None else ""
        if off is not None and played:
            same = (off["away_score"] == g["away_score"] and off["home_score"] == g["home_score"])
            status = "MATCHED_TWO_FEEDS" if same else "QUARANTINE_MISMATCH"
            stats["official_game_matches" if same else "official_game_mismatches"] += 1
            stats["official_game_checked"] += 1
            stats["join_by_date" if join == "date" else "join_by_week"] += 1
        elif played:
            status = _season_status(g["season"], season_tally, official_standings_by_season, stats)
        else:
            status = "NO_RESULT"
            stats["unplayed"] += 1
        rows.append(OrderedDict([
            ("game_id", g["game_id"]), ("season", g["season"]), ("game_type", g["game_type"]),
            ("week", g["week"]), ("gameday", g["gameday"]), ("away", g["away"]),
            ("home", g["home"]),
            ("away_score", "" if g["away_score"] is None else str(g["away_score"])),
            ("home_score", "" if g["home_score"] is None else str(g["home_score"])),
            ("margin_home", "" if margin is None else str(margin)),
            ("total_points", "" if total is None else str(total)),
            ("result_source", "nflverse games feed + official nfl.com transcription" if off
             else ("nflverse games feed" if played else "no result published yet")),
            ("verify_status", status),
            ("settle_eligible", "YES" if status in ("MATCHED_TWO_FEEDS", "SINGLE_FEED",
                                                    "SINGLE_FEED_SEASON_RECONCILED") else "NO"),
            ("official_week", "" if not off else str(off["week"])),
            ("official_date", "" if not off else str(off["date"])),
            ("join_basis", join),
        ]))
    rows.sort(key=lambda r: (r["gameday"], r["game_id"]))
    return {"rows": rows, "stats": stats.as_dict(), "season_reconciliation": _reconcile(
        games, official_standings_by_season)}


def _season_status(season, season_tally, standings_by_season, stats) -> str:
    recon = _reconcile_one(season, season_tally.get(season, []), standings_by_season.get(str(season)))
    if recon is None:
        stats["single_feed_games"] += 1
        return "SINGLE_FEED"
    if recon["mismatch_clubs"] == 0:
        stats["season_reconciled_games"] += 1
        return "SINGLE_FEED_SEASON_RECONCILED"
    stats["single_feed_games"] += 1
    return "SINGLE_FEED"


def _reconcile_one(season, games_for_season, standings_rows):
    if not standings_rows:
        return None
    tally = feed.tally_from_games(games_for_season, season=None)
    mism = []
    for s in standings_rows:
        abbr = feed.canon_team(s["abbr"])
        t = tally.get(abbr)
        if t is None:
            mism.append((abbr, "no games in feed"))
            continue
        want = (int(s["w"]), int(s["l"]), int(s["t"]), int(s["pf"]), int(s["pa"]))
        got = (t["W"], t["L"], t["T"], t["PF"], t["PA"])
        if want != got:
            mism.append((abbr, "official %s vs feed %s" % (want, got)))
    return {"season": season, "clubs": len(standings_rows), "mismatch_clubs": len(mism),
            "games_counted": sum(t["G"] for t in tally.values()), "detail": mism}


def _reconcile(games, standings_by_season) -> list[dict]:
    out = []
    grouped: dict[int, list] = defaultdict(list)
    for g in games:
        grouped[g["season"]].append(g)
    for season_label, rows in standings_by_season.items():
        season = int(season_label)
        rec = _reconcile_one(season, grouped.get(season, []), rows)
        if rec is None:
            continue
        out.append(OrderedDict([
            ("season", season), ("official_clubs_checked", rec["clubs"]),
            ("clubs_reconciled", rec["clubs"] - rec["mismatch_clubs"]),
            ("mismatch_clubs", rec["mismatch_clubs"]),
            ("games_counted", rec["games_counted"]),
            ("detail", "; ".join("%s: %s" % m for m in rec["detail"][:6])),
        ]))
    out.sort(key=lambda r: r["season"])
    return out


class Counter:
    def __init__(self):
        self.d: dict[str, int] = defaultdict(int)

    def __getitem__(self, k):
        return self.d[k]

    def __setitem__(self, k, v):
        self.d[k] = v

    def inc(self, k, n=1):
        self.d[k] += n

    def as_dict(self) -> dict:
        return OrderedDict(sorted(self.d.items()))


# ---------------------------------------------------------------------------
# grading a bet log against the ledger
# ---------------------------------------------------------------------------
def grade_trades(trades: Iterable[dict], ledger_rows: Sequence[dict]) -> dict:
    """Attach margin/total/outcome/pnl to each trade. Refuses unverifiable games."""
    by_id = {r["game_id"]: r for r in ledger_rows}
    graded, refused = [], Counter()
    for t in trades:
        row = by_id.get(t["game_id"])
        if row is None:
            refused["game_not_in_ledger"] += 1
            continue
        if row["settle_eligible"] != "YES":
            refused["game_not_verified:%s" % row["verify_status"]] += 1
            continue
        margin = int(row["margin_home"])
        total = int(row["total_points"])
        market = t.get("market")
        line = t.get("settle_line")
        if line is None:
            # fall back to the published market number the bet was struck against
            ml = t.get("market_line")
            if market == "SIDE" and ml not in (None, ""):
                line = float(ml) if t["side_key"] == "home" else -float(ml)
            elif market == "TOTAL" and ml not in (None, ""):
                line = float(ml)
        try:
            outcome = settle(market, side_key=t["side_key"], line=line,
                             margin_home=margin, total_points=total)
        except ValueError as exc:
            refused["unsettleable:%s" % exc] += 1
            continue
        price = int(t["price_american"])
        stake = float(t.get("stake", 1.0))
        rec = OrderedDict(t)
        rec["margin_home"] = margin
        rec["total_points"] = total
        rec["verify_status"] = row["verify_status"]
        rec["outcome_from_ledger"] = outcome
        rec["outcome_agrees_with_log"] = ("" if "outcome" not in t else
                                          ("YES" if outcome == t["outcome"] else "NO"))
        rec["outcome"] = outcome
        rec["pnl_units"] = round(pnl(outcome, price, stake), 6)
        rec["stake_units"] = stake
        graded.append(rec)
        if outcome == PUSH:
            refused["push"] += 1
    graded.sort(key=lambda r: r["trade_key"])
    return {"trades": graded, "refused": refused.as_dict()}


if __name__ == "__main__":  # pragma: no cover
    games = feed.load_games()
    led = build_ledger(games, feed.load_official_results(),
                       OrderedDict([("2026", feed.load_official_standings())]))
    print("ledger rows:", len(led["rows"]))
    print("stats:", json.dumps(led["stats"], indent=1) if (json := __import__("json")) else "")
