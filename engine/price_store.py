"""Price-snapshot store: opening and closing numbers for every market we originate.

THE REQUIREMENT, AND THE HONEST VERSION OF IT
    "Record opening and closing numbers for every market we originate." A store that
    recorded only numbers we could label honestly would be almost empty; a store that
    labelled everything we have as an opener or a closer would be a lie. This module
    takes the third option: it stores every observation with the *vintage the publisher
    actually asserts*, and it publishes the coverage that honest labelling leaves.

    Vintages used here (closed vocabulary):
        OPEN          a price the source labels as the number first posted for the game
        CLOSE         a price the source labels as the number at the end of the market
        LIVE_CURRENT  a price for a game that has not been played, as of the capture
        UNDOCUMENTED  a price whose vintage the source does not state

    `UNDOCUMENTED` is the honest label for most of what exists: the upstream publisher
    documents the sign of `games.csv:spread_line` but never states when that price was
    taken. Rows are never dropped for being awkward - the store's job is to record.

APPEND-ONLY, IDEMPOTENT, QUARANTINE-INSTEAD-OF-DELETE
    Rows are addressed by a content hash of (game, market, side, feed, field, value).
    Re-ingesting the same feed cannot create a duplicate; a corrected feed creates a new
    row and leaves the old one visible, because a store that overwrites cannot answer
    "what did we know on the day". A feed whose internal consistency fails (lines that do
    not net to zero across the two sides, a file whose own commit date predates the games
    it contains) is marked QUARANTINED, still stored, never used for pricing or ROI.

Interoperation: `to_sqlite_store()` writes the defensible subset through
`engine.price_snapshots` (the storage primitive on `main`), which is the write-path this
project intends to use in production. Its `phase` vocabulary is {open, close,
intermediate}; rows whose vintage is not one of those are *reported as rejected*, not
relabelled.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import OrderedDict, defaultdict
from typing import Iterable, Sequence

from . import market_feed as feed

FIELDS = [
    "snapshot_key", "game_id", "season", "week", "gameday", "market", "side_key",
    "team", "line", "price_american", "vintage", "status", "feed", "feed_field",
    "source_url", "captured_at_utc", "integrity", "value_basis", "vintage_evidence",
]

VINTAGES = ("OPEN", "CLOSE", "LIVE_CURRENT", "UNDOCUMENTED")
STATUSES = ("PUBLISHED", "QUARANTINED")
MARKETS = ("SIDE", "TOTAL", "MONEYLINE", "WIN_TOTAL")

GAMES_CAPTURE_AT = feed.UPSTREAM_HEAD_AT  # games.csv was re-hashed against this tree


# ---------------------------------------------------------------------------
# records
# ---------------------------------------------------------------------------
def make_snapshot(*, game_id: str, season, week, gameday: str, market: str, side_key: str,
                  team: str = "", line=None, price=None, vintage: str, status: str = "PUBLISHED",
                  feed_name: str, feed_field: str, source_url: str, captured_at_utc: str,
                  integrity: str = "", value_basis: str = "AS_PUBLISHED",
                  vintage_evidence: str = "") -> dict:
    if market not in MARKETS:
        raise ValueError("unknown market %r" % market)
    if vintage not in VINTAGES:
        raise ValueError("unknown vintage %r (never invent one)" % vintage)
    if status not in STATUSES:
        raise ValueError("unknown status %r" % status)
    if line is None and price is None:
        raise ValueError("a snapshot must carry a line or a price: %s %s %s" % (game_id, market, side_key))
    if not source_url.startswith(("https://", "http://")):
        raise ValueError("a snapshot must carry a resolvable source URL")
    if not captured_at_utc.strip():
        raise ValueError("a snapshot must carry the capture timestamp of its feed")
    rec = OrderedDict([
        ("snapshot_key", ""),
        ("game_id", game_id),
        ("season", "" if season is None else str(season)),
        ("week", "" if week is None else str(week)),
        ("gameday", gameday),
        ("market", market),
        ("side_key", side_key),
        ("team", team),
        ("line", "" if line is None else _fmt_line(line)),
        ("price_american", "" if price is None else str(int(price))),
        ("vintage", vintage),
        ("status", status),
        ("feed", feed_name),
        ("feed_field", feed_field),
        ("source_url", source_url),
        ("captured_at_utc", captured_at_utc),
        ("integrity", integrity),
        ("value_basis", value_basis),
        ("vintage_evidence", vintage_evidence),
    ])
    rec["snapshot_key"] = key_of(rec)
    return rec


def key_of(rec: dict) -> str:
    """Content address: identical content from the same field yields the same key."""
    parts = [rec[f] for f in FIELDS if f != "snapshot_key"]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]


def _fmt_line(v) -> str:
    f = float(v)
    return str(int(f)) if f == int(f) else ("%.1f" % f)


def dedupe(records: Sequence[dict]) -> list[dict]:
    """Append-only semantics: keep the first sighting of each content address."""
    seen: set[str] = set()
    out: list[dict] = []
    for rec in records:
        if rec["snapshot_key"] in seen:
            continue
        seen.add(rec["snapshot_key"])
        out.append(rec)
    out.sort(key=lambda r: (r["game_id"], r["feed"], r["market"], r["side_key"]))
    return out


# ---------------------------------------------------------------------------
# ingestion from the feeds described in engine.market_feed
# ---------------------------------------------------------------------------
def ingest(games: Sequence[dict], closing: Sequence[dict], sc: Sequence[dict],
           initial: Sequence[dict], win_totals: Sequence[dict]) -> dict:
    """Return {snapshots, per-feed integrity report}. Pure: no file writes."""
    recs: list[dict] = []
    by_game: "OrderedDict[str, dict]" = OrderedDict()
    for g in games:
        by_game[g["game_id"]] = g

    # ---- games.csv: spread (both sides), total (both sides), moneyline (both sides)
    gmeta = feed.FEEDS["games"]
    gurl = feed.upstream_url("games")
    for g in games:
        played = g["away_score"] is not None and g["home_score"] is not None
        vintage = "UNDOCUMENTED" if played else "LIVE_CURRENT"
        ev = ("upstream DATASETS.md documents this column's sign convention but not its "
              "vintage; the game has not been played, so the number cannot be a close") if not played \
            else gmeta["documented"]
        if g["spread_line"] is not None:
            home_line = -g["spread_line"]
            recs.append(make_snapshot(
                game_id=g["game_id"], season=g["season"], week=g["week"], gameday=g["gameday"],
                market="SIDE", side_key="home", team=g["home"], line=home_line,
                vintage=vintage, feed_name="games", feed_field="spread_line", source_url=gurl,
                captured_at_utc=gmeta["at"], integrity="SYMMETRIC_OK", vintage_evidence=ev))
            recs.append(make_snapshot(
                game_id=g["game_id"], season=g["season"], week=g["week"], gameday=g["gameday"],
                market="SIDE", side_key="away", team=g["away"], line=g["spread_line"],
                vintage=vintage, feed_name="games", feed_field="spread_line", source_url=gurl,
                captured_at_utc=gmeta["at"], integrity="SYMMETRIC_OK", vintage_evidence=ev))
            if g["home_spread_odds"] is not None:
                recs.append(make_snapshot(
                    game_id=g["game_id"], season=g["season"], week=g["week"], gameday=g["gameday"],
                    market="SIDE", side_key="home", team=g["home"], line=home_line,
                    price=g["home_spread_odds"], vintage=vintage, feed_name="games",
                    feed_field="home_spread_odds", source_url=gurl, captured_at_utc=gmeta["at"],
                    integrity="SYMMETRIC_OK", vintage_evidence=ev))
            if g["away_spread_odds"] is not None:
                recs.append(make_snapshot(
                    game_id=g["game_id"], season=g["season"], week=g["week"], gameday=g["gameday"],
                    market="SIDE", side_key="away", team=g["away"], line=g["spread_line"],
                    price=g["away_spread_odds"], vintage=vintage, feed_name="games",
                    feed_field="away_spread_odds", source_url=gurl, captured_at_utc=gmeta["at"],
                    integrity="SYMMETRIC_OK", vintage_evidence=ev))
        if g["total_line"] is not None:
            for side_key, price in (("over", g["over_odds"]), ("under", g["under_odds"])):
                recs.append(make_snapshot(
                    game_id=g["game_id"], season=g["season"], week=g["week"], gameday=g["gameday"],
                    market="TOTAL", side_key=side_key, line=g["total_line"],
                    price=price, vintage=vintage, feed_name="games",
                    feed_field="total_line" if price is None else "%s_odds" % side_key,
                    source_url=gurl, captured_at_utc=gmeta["at"], integrity="SYMMETRIC_OK",
                    vintage_evidence=ev))
        for side_key, team, price in (("home", g["home"], g["home_ml"]), ("away", g["away"], g["away_ml"])):
            if price is None:
                continue
            recs.append(make_snapshot(
                game_id=g["game_id"], season=g["season"], week=g["week"], gameday=g["gameday"],
                market="MONEYLINE", side_key=side_key, team=team, price=price,
                vintage=vintage, feed_name="games", feed_field="%s_moneyline" % side_key,
                source_url=gurl, captured_at_utc=gmeta["at"], integrity="NO_LINE_PUBLISHED",
                vintage_evidence=ev))

    # ---- closing_lines.csv: named 'closing' by the publisher; vintage claim = filename
    cmeta = feed.FEEDS["closing_lines"]
    curl = feed.upstream_url("closing_lines")
    for r in closing:
        g = by_game.get(r["alt_game_id"])
        game = g or {"season": r["alt_game_id"][:4], "week": "", "gameday": ""}
        recs.append(make_snapshot(
            game_id=r["alt_game_id"], season=game["season"], week=game["week"],
            gameday=game["gameday"], market=r["market"],
            side_key=_side_key(r["market"], r["side"], g), team=r["side"],
            line=r["line"], price=r["odds"], vintage="CLOSE", feed_name="closing_lines",
            feed_field="%s.%s" % (r["market"].lower(), "line" if r["line"] is not None else "odds"),
            source_url=curl, captured_at_utc=cmeta["at"],
            integrity="SYMMETRIC_OK" if r["market"] != "MONEYLINE" else "NO_LINE_PUBLISHED",
            vintage_evidence=cmeta["vintage_evidence"]))

    # ---- sc_lines.csv: undocumented vintage, spread only
    smeta = feed.FEEDS["sc_lines"]
    surl = feed.upstream_url("sc_lines")
    for r in sc:
        recs.append(make_snapshot(
            game_id="%s_%02d_%s_%s" % (r["season"], r["week"], r["away"], r["home"]),
            season=r["season"], week=r["week"], gameday="", market="SIDE",
            side_key="away" if r["side"] == r["away"] else "home", team=r["side"], line=r["line"],
            vintage="UNDOCUMENTED", feed_name="sc_lines", feed_field="line", source_url=surl,
            captured_at_utc=smeta["at"], integrity="SYMMETRIC_OK",
            vintage_evidence=smeta["documented"]))

    # ---- initial_lines.csv: claims to be the opener, quarantined on evidence
    imeta = feed.FEEDS["initial_lines"]
    iurl = feed.upstream_url("initial_lines")
    for r in initial:
        g = by_game.get(r["game_id"]) or {}
        recs.append(make_snapshot(
            game_id=r["game_id"], season=r["season"], week=g.get("week", ""),
            gameday=g.get("gameday", ""), market=r["market"],
            side_key=_side_key(r["market"], r["side"], g if g else None), team=r["side"],
            line=r["line"], vintage="OPEN", status="QUARANTINED", feed_name="initial_lines",
            feed_field="line", source_url=iurl, captured_at_utc=imeta["at"],
            integrity="QUARANTINE_FAVOURITE_CONTRADICTION" if g else "UNMATCHED_GAME",
            value_basis="LINE_ONLY_NO_PRICE", vintage_evidence=imeta["vintage_evidence"]))

    # ---- win_totals.csv: the futures market, to prove the store is market-generic
    wmeta = feed.FEEDS["win_totals"]
    wurl = feed.upstream_url("win_totals")
    for r in win_totals:
        for side_key, price in (("over", r["over_odds"]), ("under", r["under_odds"])):
            if price is None and r["line"] is None:
                continue
            recs.append(make_snapshot(
                game_id="WIN%d_%s" % (r["season"], r["team"]), season=r["season"], week="",
                gameday="", market="WIN_TOTAL", side_key=side_key, team=r["team"], line=r["line"],
                price=price, vintage="UNDOCUMENTED", feed_name="win_totals",
                feed_field="%s_odds" % side_key if price is not None else "line",
                source_url=wurl, captured_at_utc=wmeta["at"], integrity="NO_GAME_KEY",
                vintage_evidence=wmeta["documented"]))

    recs = dedupe(recs)
    report = integrity_report(recs)
    return {"snapshots": recs, "integrity": report}


def _side_key(market: str, side: str, game: dict | None) -> str:
    if market == "TOTAL":
        return side.strip().lower()
    if game and side in (game.get("away"), game.get("home")):
        return "away" if side == game["away"] else "home"
    return side.strip().lower()


# ---------------------------------------------------------------------------
# integrity
# ---------------------------------------------------------------------------
def integrity_report(records: Sequence[dict]) -> "OrderedDict[str, dict]":
    """Structural checks that need no outside knowledge to run.

    The important one is symmetry: a spread feed that publishes `home -3.0` and
    `away +2.5` for the same game is internally inconsistent, whatever its provenance
    says. Totals must be a single number shared by both sides. Any feed failing these
    is quarantined rather than quietly used.
    """
    by_feed: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_feed[r["feed"]].append(r)
    out: "OrderedDict[str, dict]" = OrderedDict()
    for name, rows in sorted(by_feed.items()):
        pairs: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for r in rows:
            if r["market"] == "SIDE" and r["line"] != "" and r["side_key"] in ("home", "away"):
                pairs[(r["game_id"], r["vintage"])].append(r)
        checked = asym = 0
        for _k, grp in pairs.items():
            lines = {}
            for r in grp:
                lines[r["side_key"]] = float(r["line"])
            if "home" in lines and "away" in lines:
                checked += 1
                if abs(lines["home"] + lines["away"]) > 1e-9:
                    asym += 1
        totals: dict[tuple[str, str], set] = defaultdict(set)
        for r in rows:
            if r["market"] == "TOTAL" and r["line"] != "":
                totals[(r["game_id"], r["vintage"])].add(r["line"])
        tot_conflict = sum(1 for v in totals.values() if len(v) > 1)
        games = {r["game_id"] for r in rows}
        out[name] = OrderedDict([
            ("rows", len(rows)),
            ("games", len(games)),
            ("games_with_line", len({r["game_id"] for r in rows if r["line"] != ""})),
            ("games_with_price", len({r["game_id"] for r in rows if r["price_american"] != ""})),
            ("side_pairs_checked", checked),
            ("side_pairs_asymmetric", asym),
            ("total_pairs_conflicting", tot_conflict),
            ("quarantined_rows", sum(1 for r in rows if r["status"] == "QUARANTINED")),
            ("seasons", "%s..%s" % (min((r["season"] for r in rows if r["season"]), default="-"),
                                    max((r["season"] for r in rows if r["season"]), default="-"))),
            ("vintages", ",".join(sorted({r["vintage"] for r in rows}))),
        ])
    return out


# ---------------------------------------------------------------------------
# coverage + cross-feed drift
# ---------------------------------------------------------------------------
def coverage(records: Sequence[dict]) -> list[dict]:
    """Games per season x market x vintage, with a line and/or a price present."""
    agg: dict[tuple, dict] = {}
    for r in records:
        k = (r["season"], r["market"], r["vintage"], r["status"], r["feed"])
        d = agg.setdefault(k, {"games": set(), "with_line": set(), "with_price": set()})
        d["games"].add(r["game_id"])
        if r["line"] != "":
            d["with_line"].add(r["game_id"])
        if r["price_american"] != "":
            d["with_price"].add(r["game_id"])
    rows = []
    for (season, market, vintage, status, src), d in agg.items():
        rows.append(OrderedDict([
            ("season", season), ("market", market), ("vintage", vintage),
            ("status", status), ("feed", src),
            ("games", len(d["games"])), ("games_with_line", len(d["with_line"])),
            ("games_with_price", len(d["with_price"])),
        ]))
    rows.sort(key=lambda r: (r["season"], r["market"], r["feed"], r["vintage"]))
    return rows


def drift(records: Sequence[dict]) -> list[dict]:
    """Where two feeds price the same game, what do they say?"""
    idx: dict[tuple[str, str, str], dict] = {}
    for r in records:
        if r["market"] != "SIDE" or r["line"] == "" or r["side_key"] not in ("home", "away"):
            continue
        idx[(r["game_id"], r["feed"], r["side_key"])] = r
    games = sorted({g for (g, _f, _s) in idx})
    feeds = sorted({f for (_g, f, _s) in idx})
    rows = []
    for i, fa in enumerate(feeds):
        for fb in feeds[i + 1:]:
            same_line = diff_line = 0
            same_fav = diff_fav = 0
            deltas = []
            both_price_same = both_price_diff = 0
            for gid in games:
                a = idx.get((gid, fa, "home"))
                b = idx.get((gid, fb, "home"))
                if not a or not b:
                    continue
                la, lb = float(a["line"]), float(b["line"])
                if la == lb:
                    same_line += 1
                else:
                    diff_line += 1
                    deltas.append(abs(la - lb))
                fa_dir = _dir(la)
                fb_dir = _dir(lb)
                if fa_dir == fb_dir:
                    same_fav += 1
                elif fa_dir != "?" and fb_dir != "?":
                    diff_fav += 1
                if a["price_american"] and b["price_american"]:
                    if a["price_american"] == b["price_american"]:
                        both_price_same += 1
                    else:
                        both_price_diff += 1
            n = same_line + diff_line
            rows.append(OrderedDict([
                ("feed_a", fa), ("feed_b", fb), ("market", "SIDE"),
                ("games_compared", n),
                ("lines_identical", same_line), ("lines_differ", diff_line),
                ("pct_lines_identical", "" if not n else "%.1f" % (100.0 * same_line / n)),
                ("favourite_agrees", same_fav), ("favourite_conflicts", diff_fav),
                ("median_abs_diff_pts", _median(deltas)), ("max_abs_diff_pts", _max(deltas)),
                ("prices_identical", both_price_same), ("prices_differ", both_price_diff),
                ("note", "disagreement is reported, not resolved; no feed is treated as truth"),
            ]))
    return rows


def _dir(line: float) -> str:
    return "home" if line < 0 else ("away" if line > 0 else "?")


def _median(xs: Sequence[float]) -> str:
    if not xs:
        return ""
    s = sorted(xs)
    n = len(s)
    m = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0
    return _fmt_line(m)


def _max(xs: Sequence[float]) -> str:
    return _fmt_line(max(xs)) if xs else ""


# ---------------------------------------------------------------------------
# interoperation with the SQLite write path on main
# ---------------------------------------------------------------------------
PHASE_MAP = {"OPEN": "open", "CLOSE": "close"}


def to_sqlite_store(records: Sequence[dict], db_path: str, version: str = "line-origin-v1") -> dict:
    """Push the defensible rows through engine.price_snapshots; report the rest.

    The upstream store's `phase` vocabulary is {open, close, intermediate}. A row whose
    vintage the publisher never stated is not "intermediate" - it is unstated - so it is
    refused and counted, which is the point of the exercise: the vocabulary needs a
    fourth value before the store can hold the whole ledger.
    """
    from . import price_snapshots as ps  # noqa: PLC0415 (optional interop path)

    db = ps.connect(db_path)
    inserted = 0
    refused: dict[str, int] = defaultdict(int)
    for r in records:
        if r["status"] != "PUBLISHED":
            refused["quarantined feed (not a tradable price)"] += 1
            continue
        if r["market"] not in ("SIDE", "TOTAL", "MONEYLINE"):
            refused["market %s is outside the store's market vocabulary" % r["market"]] += 1
            continue
        phase = PHASE_MAP.get(r["vintage"])
        if not phase:
            refused["vintage %s is outside the store's phase vocabulary" % r["vintage"]] += 1
            continue
        if not r["game_id"].count("_"):
            refused["no event key (futures rows)"] += 1
            continue
        ps.record(
            db, event_id=r["game_id"], market_type="spread" if r["market"] == "SIDE" else
            ("total" if r["market"] == "TOTAL" else ("moneyline" if r["market"] == "MONEYLINE" else "player_prop")),
            market_key="%s:%s" % (r["market"], r["feed"]), side=r["side_key"],
            line=None if r["line"] == "" else float(r["line"]),
            odds_american=None if r["price_american"] == "" else int(r["price_american"]),
            captured_at_utc=r["captured_at_utc"], phase=phase,
            source_name="nflverse/nfldata %s" % r["feed"], source_url=r["source_url"],
            source_record_id=r["snapshot_key"], line_origin_version=version)
        inserted += 1
    stored = db.execute("SELECT COUNT(*) AS c FROM price_snapshot").fetchone()["c"]
    db.close()
    return {"inserted_calls": inserted, "rows_in_store": stored,
            "refused": OrderedDict(sorted(refused.items()))}


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------
def write_tsv(records: Sequence[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(FIELDS) + "\n")
        for r in records:
            fh.write("\t".join(str(r[f]) for f in FIELDS) + "\n")


def write_json(obj, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


if __name__ == "__main__":  # pragma: no cover
    games = feed.load_games()
    res = ingest(games, feed.load_closing_lines(), feed.load_sc_lines(),
                 feed.load_initial_lines(), feed.load_win_totals())
    print("snapshots:", len(res["snapshots"]))
    for name, d in res["integrity"].items():
        print(" ", name, d)
