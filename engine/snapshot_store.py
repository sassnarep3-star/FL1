"""Append-only, provenance-aware storage for originated-market price snapshots.

A market must be opened with an opening snapshot and closed with exactly one closing
snapshot. The fair value, observed market value and their signed difference are stored
separately. No sportsbook feed is bundled: the caller must provide a source URL and a
content digest for every verified quote. Unverified quotes may be logged, but their
numeric cells are forced blank.

This is a storage primitive, not a claim that any existing repository prices are
official or verified. SQLite uses a local file and the standard library only.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import math
import sqlite3
from typing import Optional
from urllib.parse import urlparse

_PHASES = {"opening", "closing"}
_MARKET_TYPES = {"spread", "total", "moneyline", "player_prop", "parlay", "other"}


def _utc(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("timestamp must be ISO-8601 with a timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _url(value: str) -> str:
    parsed = urlparse(value or "")
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("source_url must be an absolute HTTPS URL")
    return value


def _digest(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.lower()
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("source_sha256 must be a 64-character SHA-256 hex digest")
    return value


class SnapshotStore:
    """SQLite ledger; the caller owns lifecycle and source verification."""

    def __init__(self, path: str):
        self.path = path
        with self._connect() as db:
            db.execute("PRAGMA foreign_keys=ON")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS markets (
                    market_id TEXT PRIMARY KEY,
                    game_id TEXT NOT NULL,
                    market_type TEXT NOT NULL,
                    selection TEXT NOT NULL,
                    value_unit TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_id TEXT NOT NULL REFERENCES markets(market_id),
                    phase TEXT NOT NULL CHECK (phase IN ('opening','closing')),
                    captured_at TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    verified INTEGER NOT NULL CHECK (verified IN (0,1)),
                    fair_value REAL,
                    market_value REAL,
                    difference REAL,
                    american_odds INTEGER,
                    source_sha256 TEXT,
                    source_checked_at TEXT,
                    UNIQUE(market_id, phase)
                );
            """)

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def originate(self, *, market_id: str, game_id: str, market_type: str,
                  selection: str, value_unit: str, captured_at: str,
                  source_name: str, source_url: str, verified: bool,
                  source_sha256: Optional[str] = None,
                  source_checked_at: Optional[str] = None,
                  source_payload: Optional[bytes] = None,
                  fair_value: Optional[float] = None,
                  market_value: Optional[float] = None,
                  american_odds: Optional[int] = None) -> None:
        """Create a market and its required opening record atomically."""
        if market_type not in _MARKET_TYPES:
            raise ValueError(f"market_type must be one of {sorted(_MARKET_TYPES)}")
        if not all((market_id, game_id, selection, value_unit, source_name)):
            raise ValueError("market identifiers, selection, unit and source name are required")
        self._insert_snapshot(
            market_id=market_id, phase="opening", captured_at=captured_at,
            source_name=source_name, source_url=source_url, verified=verified,
            value_unit=value_unit, fair_value=fair_value, market_value=market_value,
            american_odds=american_odds, source_sha256=source_sha256,
            source_checked_at=source_checked_at, source_payload=source_payload,
            create=(market_id, game_id, market_type, selection, value_unit, _utc(captured_at)),
        )

    def close(self, *, market_id: str, captured_at: str, source_name: str,
              source_url: str, verified: bool, source_sha256: Optional[str] = None,
              source_checked_at: Optional[str] = None,
              source_payload: Optional[bytes] = None,
              fair_value: Optional[float] = None,
              market_value: Optional[float] = None,
              american_odds: Optional[int] = None) -> None:
        """Record the single closing snapshot; opening must already exist."""
        with self._connect() as db:
            row = db.execute("SELECT value_unit FROM markets WHERE market_id=?", (market_id,)).fetchone()
        if row is None:
            raise ValueError("cannot close an unknown market")
        self._insert_snapshot(
            market_id=market_id, phase="closing", captured_at=captured_at,
            source_name=source_name, source_url=source_url, verified=verified,
            value_unit=row["value_unit"], fair_value=fair_value,
            market_value=market_value, american_odds=american_odds,
            source_sha256=source_sha256, source_checked_at=source_checked_at,
            source_payload=source_payload,
        )

    def _insert_snapshot(self, *, market_id: str, phase: str, captured_at: str,
                         source_name: str, source_url: str, verified: bool,
                         value_unit: str, fair_value: Optional[float],
                         market_value: Optional[float], american_odds: Optional[int],
                         source_sha256: Optional[str], source_checked_at: Optional[str],
                         source_payload: Optional[bytes], create=None) -> None:
        if phase not in _PHASES:
            raise ValueError("phase must be opening or closing")
        if not isinstance(verified, bool):
            raise ValueError("verified must be an explicit boolean")
        captured_at = _utc(captured_at)
        source_url = _url(source_url)
        if not source_name:
            raise ValueError("source_name is required")
        source_sha256 = _digest(source_sha256)
        checked = _utc(source_checked_at) if source_checked_at else None
        values = (fair_value, market_value, american_odds)
        if verified:
            if source_sha256 is None or checked is None or source_payload is None:
                raise ValueError(
                    "verified values require source_sha256, source_checked_at and source_payload")
            if hashlib.sha256(source_payload).hexdigest() != source_sha256:
                raise ValueError("source_sha256 does not match the exact source_payload bytes")
        elif any(v is not None for v in values):
            # The brief's rule: unsupported values stay blank, not guessed or inferred.
            fair_value = market_value = american_odds = None
        for value in (fair_value, market_value):
            if value is not None:
                if isinstance(value, bool):
                    raise ValueError("snapshot values must be finite numbers")
                try:
                    valid = math.isfinite(float(value))
                except (TypeError, ValueError):
                    valid = False
                if not valid:
                    raise ValueError("snapshot values must be finite numbers")
        if american_odds is not None and (isinstance(american_odds, bool)
                                          or not isinstance(american_odds, int)):
            raise ValueError("American odds must be an integer")
        if american_odds == 0:
            raise ValueError("American odds cannot be zero")
        difference = (float(fair_value) - float(market_value)
                      if fair_value is not None and market_value is not None else None)
        with self._connect() as db:
            if create:
                db.execute("INSERT INTO markets VALUES (?,?,?,?,?,?)", create)
            elif db.execute("SELECT 1 FROM markets WHERE market_id=?", (market_id,)).fetchone() is None:
                raise ValueError("cannot snapshot an unknown market")
            if phase == "closing":
                opening = db.execute(
                    "SELECT captured_at FROM snapshots WHERE market_id=? AND phase='opening'",
                    (market_id,)).fetchone()
                if opening is None:
                    raise ValueError("closing snapshot requires an opening snapshot")
                if captured_at < opening["captured_at"]:
                    raise ValueError("closing snapshot cannot predate its opening snapshot")
            db.execute("""INSERT INTO snapshots
                (market_id,phase,captured_at,source_name,source_url,verified,
                 fair_value,market_value,difference,american_odds,source_sha256,source_checked_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (market_id, phase, captured_at, source_name, source_url, int(bool(verified)),
                 fair_value, market_value, difference, american_odds, source_sha256, checked))

    def rows(self):
        with self._connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM snapshots ORDER BY snapshot_id")]

    def incomplete_markets(self):
        """Return originated markets without a verified closing snapshot."""
        with self._connect() as db:
            return [row[0] for row in db.execute("""
                SELECT m.market_id FROM markets m
                LEFT JOIN snapshots s ON s.market_id=m.market_id AND s.phase='closing'
                WHERE s.snapshot_id IS NULL OR s.verified=0 OR EXISTS (
                    SELECT 1 FROM snapshots o
                    WHERE o.market_id=m.market_id AND o.phase='opening' AND o.verified=0
                ) ORDER BY m.market_id
            """)]


def sha256_bytes(payload: bytes) -> str:
    """Utility for callers to bind a record to the exact source payload captured."""
    return hashlib.sha256(payload).hexdigest()
