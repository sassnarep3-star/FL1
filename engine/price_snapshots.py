"""Append-only store for point-in-time prices on markets we originate.

This module deliberately stores observations only; it does not invent prices or
identify a sportsbook as authoritative. Callers must supply a source URL and a
source-record identifier. OPEN/CLOSE are explicit labels, not inferred from time.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

MARKETS = {"spread", "total", "moneyline", "player_prop"}
PHASES = {"open", "close", "intermediate"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS price_snapshot (
  snapshot_id INTEGER PRIMARY KEY,
  event_id TEXT NOT NULL,
  market_type TEXT NOT NULL CHECK (market_type IN ('spread','total','moneyline','player_prop')),
  market_key TEXT NOT NULL,
  side TEXT NOT NULL,
  line REAL,
  odds_american INTEGER,
  captured_at_utc TEXT NOT NULL,
  phase TEXT NOT NULL CHECK (phase IN ('open','close','intermediate')),
  source_name TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_record_id TEXT NOT NULL,
  line_origin_version TEXT NOT NULL,
  created_at_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE(event_id, market_type, market_key, side, captured_at_utc, source_name, source_record_id)
);
CREATE INDEX IF NOT EXISTS price_snapshot_lookup
  ON price_snapshot(event_id, market_type, market_key, phase, captured_at_utc);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    """Open or create a local SQLite store and ensure its schema exists."""
    db = sqlite3.connect(str(path))
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def record(db: sqlite3.Connection, *, event_id: str, market_type: str,
           market_key: str, side: str, line: float | None,
           odds_american: int | None, captured_at_utc: str, phase: str,
           source_name: str, source_url: str, source_record_id: str,
           line_origin_version: str) -> int:
    """Record a sourced quote; duplicate delivery is idempotent.

    A quote without a source URL/record id or originating model version is
    rejected. Prices should be stored in the vendor's original representation.
    """
    if market_type not in MARKETS:
        raise ValueError(f"unsupported market_type: {market_type}")
    if phase not in PHASES:
        raise ValueError(f"unsupported phase: {phase}")
    required = (event_id, market_key, side, captured_at_utc, source_name,
                source_url, source_record_id, line_origin_version)
    if not all(isinstance(v, str) and v.strip() for v in required):
        raise ValueError("all identifiers, timestamps, source fields, and version are required")
    if not source_url.startswith(("https://", "http://")):
        raise ValueError("source_url must be an explicit http(s) URL")
    cur = db.execute("""INSERT OR IGNORE INTO price_snapshot
      (event_id,market_type,market_key,side,line,odds_american,captured_at_utc,
       phase,source_name,source_url,source_record_id,line_origin_version)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
      (event_id,market_type,market_key,side,line,odds_american,captured_at_utc,
       phase,source_name,source_url,source_record_id,line_origin_version))
    db.commit()
    row = db.execute("""SELECT snapshot_id FROM price_snapshot WHERE event_id=?
      AND market_type=? AND market_key=? AND side=? AND captured_at_utc=?
      AND source_name=? AND source_record_id=?""",
      (event_id,market_type,market_key,side,captured_at_utc,source_name,source_record_id)).fetchone()
    return int(row["snapshot_id"])


def snapshots(db: sqlite3.Connection, event_id: str | None = None) -> Iterable[sqlite3.Row]:
    """Return immutable observations in event/time order, optionally filtered."""
    if event_id is None:
        return db.execute("SELECT * FROM price_snapshot ORDER BY event_id,captured_at_utc,snapshot_id")
    return db.execute("SELECT * FROM price_snapshot WHERE event_id=? ORDER BY captured_at_utc,snapshot_id", (event_id,))
