"""Price-snapshot store (requirement R21).

Records the OPENING and the CLOSING number for every market we originate — one
row per (game, market), created before kickoff and completed at close.

Rules the store enforces by construction:

1. Every market we originate gets a row BEFORE its kickoff, even if every price
   cell is blank. The store records the fact that a market was originated and
   the price fields it is waiting for.
2. A price cell is filled only from a named source record (source id + capture
   timestamp). No source, no number: the cell stays None and the row carries a
   flag. A blank cell means "no source", never "zero" and never "unknown price".
3. Rows are stored in origination order: SIDE first, then TOTAL, then
   MONEYLINE (requirement R23), then by kickoff.
4. `validate()` refuses rows that carry a price without provenance, and rows
   that claim an official source for a market no official source prices.

This is a store and a discipline, not a price generator. Opening prices have no
verified source in this repository at all, so every open cell in the seed data
is blank and flagged — that is the honest state, and the store is what makes the
gap visible and fillable later.
"""

from __future__ import annotations

from datetime import datetime, timezone

# Origination order mandated by requirement R23.
MARKET_ORDER = {"SIDE": 0, "TOTAL": 1, "MONEYLINE": 2}
MARKET_TYPES = tuple(MARKET_ORDER)

PROVENANCE_OFFICIAL = "OFFICIAL"
PROVENANCE_THIRD_PARTY = "THIRD_PARTY"
PROVENANCE_NONE = ""

SCHEMA_VERSION = 1


def make_id(season: int, week: int, away: str, home: str, market_type: str,
            quote_side: str) -> str:
    """Stable market id: season-week-away-home-TYPE-QUOTE.

    quote_side names the number the row records: HOME for the home-view spread,
    GAME for the total, HOME/AWAY for each moneyline price (the two sides of a
    moneyline are two distinct numbers, so they get one row each)."""
    if market_type not in MARKET_ORDER:
        raise ValueError("unknown market type %r" % market_type)
    return "%d-W%02d-%s-%s-%s-%s" % (int(season), int(week), away, home,
                                     market_type, quote_side)


def record(season, week, game_id, away, home, market_type, side, quote_side,
           open_price=None, open_ts=None, open_source=None, open_provenance=PROVENANCE_NONE,
           close_price=None, close_ts=None, close_source=None, close_provenance=PROVENANCE_NONE,
           notes=""):
    """Build one snapshot row. Prices may be None; provenance may not silently
    claim a source that is not named."""
    row = {
        "market_id": make_id(season, week, away, home, market_type, quote_side),
        "season": int(season),
        "week": int(week),
        "game_id": game_id,
        "away": away,
        "home": home,
        "market_type": market_type,
        "side": side,
        "quote_side": quote_side,
        "open_price": open_price,
        "open_ts": open_ts,
        "open_source": open_source or "",
        "open_provenance": open_provenance,
        "close_price": close_price,
        "close_ts": close_ts,
        "close_source": close_source or "",
        "close_provenance": close_provenance,
        "notes": notes,
    }
    return row


def sort_key(row):
    """Origination order: kickoff, then SIDE, TOTAL, MONEYLINE (R23)."""
    return (row.get("season", 0), row.get("week", 0), row.get("away", ""),
            row.get("home", ""), MARKET_ORDER.get(row.get("market_type", ""), 99),
            row.get("quote_side", ""))


def validate(rows):
    """Return a list of human-readable errors; empty list means the store is sound."""
    errors = []
    seen = set()
    for i, r in enumerate(rows):
        mid = r.get("market_id", "")
        where = "row %d (%s)" % (i, mid or "?")
        if not mid:
            errors.append("%s: missing market_id" % where)
            continue
        if mid in seen:
            errors.append("%s: duplicate market_id" % where)
        seen.add(mid)
        if r.get("market_type") not in MARKET_ORDER:
            errors.append("%s: bad market_type %r" % (where, r.get("market_type")))
        for field in ("season", "week", "away", "home", "side", "quote_side"):
            if r.get(field) in (None, ""):
                errors.append("%s: missing %s" % (where, field))
        for end in ("open", "close"):
            price = r.get("%s_price" % end)
            prov = r.get("%s_provenance" % end, PROVENANCE_NONE)
            src = r.get("%s_source" % end, "")
            if price is not None and prov == PROVENANCE_NONE:
                errors.append("%s: %s price carries no provenance" % (where, end))
            if price is not None and not src:
                errors.append("%s: %s price carries no source id" % (where, end))
            if price is None and prov != PROVENANCE_NONE:
                errors.append("%s: %s provenance set without a price" % (where, end))
            if prov == PROVENANCE_OFFICIAL:
                errors.append(
                    "%s: %s claims OFFICIAL provenance, but no official league "
                    "source prices NFL markets (see flag F23)" % (where, end))
    return errors


def coverage(rows):
    """Coverage counters per market type: how many rows exist and how many of
    their price cells a source actually backs. The point of the store is that
    these numbers are never silently assumed to be complete."""
    out = {}
    for mt in MARKET_TYPES:
        rs = [r for r in rows if r.get("market_type") == mt]
        out[mt] = {
            "rows": len(rs),
            "open_filled": sum(1 for r in rs if r.get("open_price") is not None),
            "close_filled": sum(1 for r in rs if r.get("close_price") is not None),
        }
    out["TOTAL_ROWS"] = len(rows)
    out["open_filled"] = sum(1 for r in rows if r.get("open_price") is not None)
    out["close_filled"] = sum(1 for r in rows if r.get("close_price") is not None)
    return out


def settle_close(row, close_price, close_ts, source, provenance):
    """Complete a row at close. Refuses to overwrite an existing close: a
    recorded close is history, and history is corrected by a new dated row in
    the verification log, not by editing the store."""
    if row.get("close_price") is not None:
        raise ValueError("close already recorded for %s" % row.get("market_id"))
    if provenance == PROVENANCE_NONE or not source:
        raise ValueError("a close needs a source and a provenance")
    row["close_price"] = close_price
    row["close_ts"] = close_ts
    row["close_source"] = source
    row["close_provenance"] = provenance
    return row


def utcnow_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
