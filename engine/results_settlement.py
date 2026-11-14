#!/usr/bin/env python3
"""
results_feed.py — the verified results feed: settlement and ROI primitives.

Purpose
-------
Backtests and ROI cannot be computed at all without (a) verified final scores
and (b) an explicit price provenance. This module provides (a) as a strict
loader over data/results_feed.csv and provides (b) as fail-closed contracts:
settlement and ROI functions REFUSE to run on a price whose provenance is not
declared. Nothing is inferred; a missing value raises.

Feed contract (data/results_feed.csv)
-------------------------------------
game_id, season, week, game_date, kickoff_et, away_team, away_score,
home_team, home_score, overtime, stadium, roof, verified,
verification_basis, official_game_url, official_week_url, source_ids

The feed carries only official facts (scores and their verification). Market
prices are NOT part of the feed: they live behind the price-snapshot store
(engine/price_snapshots.py) or a declared third-party snapshot, and every bet
submitted to roi() must name which one it used.

Standard library only. Run:  python3 -m engine.results_feed --check
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = os.path.join(ROOT, "data", "results_feed.csv")

REQUIRED_FIELDS = (
    "game_id", "season", "week", "game_date", "away_team", "away_score",
    "home_team", "home_score", "verified", "verification_basis",
    "official_game_url", "source_ids",
)

ALLOWED_MARKET_PROVENANCE = (
    "official",            # an official league source (none exists for prices)
    "price-snapshot-store",  # engine/price_snapshots.py with source record
    "third-party",         # e.g. the pinned nflverse snapshot (flagged)
)


class FeedError(ValueError):
    """Raised when the feed is malformed or a contract is violated."""


class ProvenanceError(ValueError):
    """Raised when ROI/settlement is attempted without declared price provenance."""


@dataclass
class Game:
    game_id: str
    season: int
    week: int
    game_date: str
    away_team: str
    away_score: int
    home_team: str
    home_score: int
    verified: str
    verification_basis: str
    official_game_url: str
    source_ids: str
    overtime: str = ""
    stadium: str = ""
    roof: str = ""
    kickoff_et: str = ""
    official_week_url: str = ""

    @property
    def margin(self) -> int:
        """home_score - away_score"""
        return self.home_score - self.away_score

    @property
    def total(self) -> int:
        return self.home_score + self.away_score


@dataclass
class Bet:
    game_id: str
    market: str            # "side" | "total" | "ml"
    selection: str         # "home" | "away" | "over" | "under"
    price_american: float
    stake: float = 1.0
    line: float | None = None      # required for side/total
    market_provenance: str = ""    # must be one of ALLOWED_MARKET_PROVENANCE
    price_source_id: str = ""      # source record for the price
    result: str = field(default="")  # win | loss | push (filled by settle)

    def _check_provenance(self) -> None:
        if self.market_provenance not in ALLOWED_MARKET_PROVENANCE:
            raise ProvenanceError(
                "bet %s/%s: market_provenance %r is not declared; allowed: %s"
                % (self.game_id, self.market, self.market_provenance,
                   ", ".join(ALLOWED_MARKET_PROVENANCE)))
        if not self.price_source_id:
            raise ProvenanceError(
                "bet %s/%s: price_source_id is required"
                % (self.game_id, self.market))


def load_feed(path: str = FEED) -> list[Game]:
    if not os.path.exists(path):
        raise FeedError("feed not found: %s" % path)
    games = []
    seen = set()
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [f for f in REQUIRED_FIELDS if f not in (reader.fieldnames or [])]
        if missing:
            raise FeedError("feed missing columns: %s" % ", ".join(missing))
        for row in reader:
            for f in REQUIRED_FIELDS:
                if not (row.get(f) or "").strip():
                    raise FeedError("feed row %s: empty required field %s"
                                    % (row.get("game_id"), f))
            gid = row["game_id"]
            if gid in seen:
                raise FeedError("feed duplicate game_id %s" % gid)
            seen.add(gid)
            if row["verified"] != "row-level official":
                raise FeedError("feed row %s: not row-level official" % gid)
            games.append(Game(
                game_id=gid,
                season=int(row["season"]), week=int(row["week"]),
                game_date=row["game_date"],
                away_team=row["away_team"], away_score=int(row["away_score"]),
                home_team=row["home_team"], home_score=int(row["home_score"]),
                verified=row["verified"],
                verification_basis=row["verification_basis"],
                official_game_url=row["official_game_url"],
                source_ids=row["source_ids"],
                overtime=row.get("overtime", ""),
                stadium=row.get("stadium", ""),
                roof=row.get("roof", ""),
                kickoff_et=row.get("kickoff_et", ""),
                official_week_url=row.get("official_week_url", ""),
            ))
    return games


def settle(bet: Bet, game: Game) -> str:
    """Settle one bet against a verified game. Returns 'win'|'loss'|'push'."""
    bet._check_provenance()
    if bet.market == "ml":
        if bet.line is not None:
            raise FeedError("ml bet carries a line")
        if bet.selection not in ("home", "away"):
            raise FeedError("ml selection must be home|away")
        if game.margin == 0:
            raise FeedError("ml cannot settle: game %s tied" % game.game_id)
        win = (game.margin > 0) == (bet.selection == "home")
        bet.result = "win" if win else "loss"
        return bet.result
    if bet.line is None:
        raise FeedError("%s bet requires a line" % bet.market)
    if bet.market == "side":
        if bet.selection not in ("home", "away"):
            raise FeedError("side selection must be home|away")
        d = (game.margin - bet.line) if bet.selection == "home" else (bet.line - game.margin)
    elif bet.market == "total":
        if bet.selection not in ("over", "under"):
            raise FeedError("total selection must be over|under")
        d = (game.total - bet.line) if bet.selection == "over" else (bet.line - game.total)
    else:
        raise FeedError("unknown market %r" % bet.market)
    if abs(d) < 1e-9:
        bet.result = "push"
    else:
        bet.result = "win" if d > 0 else "loss"
    return bet.result


def american_profit(odds: float) -> float:
    return 100.0 / -odds if odds < 0 else odds / 100.0


def roi(bets: list[Bet], games: dict[str, Game]) -> dict:
    """Settle every bet and compute stake-normalised ROI.

    Fail-closed: any bet without declared price provenance raises before any
    number is produced. Pushes leave both numerator and denominator.
    """
    for b in bets:
        b._check_provenance()
        if b.game_id not in games:
            raise FeedError("no verified game %s in feed" % b.game_id)
        if not b.result:
            settle(b, games[b.game_id])
    settled = [b for b in bets if b.result != "push"]
    staked = sum(b.stake for b in settled)
    profit = sum(b.stake * (american_profit(b.price_american) if b.result == "win"
                            else -1.0) for b in settled)
    wins = sum(1 for b in settled if b.result == "win")
    out = {
        "bets": len(bets),
        "settled": len(settled),
        "wins": wins,
        "losses": len(settled) - wins,
        "staked": round(staked, 4),
        "profit": round(profit, 4),
        "roi": round(profit / staked, 4) if staked else None,
        "provenance": sorted({b.market_provenance for b in bets}),
        "price_sources": sorted({b.price_source_id for b in bets}),
    }
    return out


def check(path: str = FEED) -> int:
    games = load_feed(path)
    weeks = sorted({g.week for g in games})
    print("results feed OK: %d games, weeks %d-%d, all row-level official"
          % (len(games), weeks[0], weeks[-1]))
    return 0


if __name__ == "__main__":
    import sys
    try:
        sys.exit(check())
    except FeedError as e:
        print("FEED ERROR:", e, file=sys.stderr)
        sys.exit(1)
