"""Append-only import boundary for source-checked NFL final scores.

The module accepts only records explicitly marked verified, with a cited HTTPS URL on
an nfl.com host, a retrieval/check timestamp, and the SHA-256 of the exact captured
source payload and stores its digest (the caller remains responsible for archiving the
payload). It checks provenance shape and arithmetic inputs; it does not fetch NFL pages
or prove that a human/collector transcribed the page correctly. Callers must run
an independent line-by-line verifier before asserting `verified=True`.

No synthetic or unverified results are shipped in this module. Corrections are retained
as later events; `latest()` returns the most recently recorded verified revision.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import sqlite3
from typing import Iterable
from urllib.parse import urlparse


def _utc(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("timestamp must be ISO-8601 with a timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _official_nfl_url(url: str) -> str:
    parsed = urlparse(url or "")
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme != "https" or not (host == "nfl.com" or host.endswith(".nfl.com")):
        raise ValueError("verified results require an HTTPS source URL on nfl.com")
    return url


def _sha256(value: str) -> str:
    value = (value or "").lower()
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("evidence_sha256 must be a 64-character SHA-256 hex digest")
    return value


@dataclass(frozen=True)
class VerifiedResult:
    game_id: str
    season: int
    week: int
    away_team: str
    home_team: str
    away_score: int
    home_score: int
    status: str
    source_url: str
    source_checked_at: str
    evidence_sha256: str
    evidence_payload: bytes
    verified: bool = True


class ResultsFeed:
    """Minimal append-only SQLite feed for officially sourced final results."""

    def __init__(self, path: str):
        self.path = path
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS result_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                season INTEGER NOT NULL,
                week INTEGER NOT NULL,
                away_team TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_score INTEGER NOT NULL,
                home_score INTEGER NOT NULL,
                status TEXT NOT NULL CHECK (status='FINAL'),
                source_url TEXT NOT NULL,
                source_checked_at TEXT NOT NULL,
                evidence_sha256 TEXT NOT NULL,
                verified INTEGER NOT NULL CHECK (verified=1),
                UNIQUE(game_id, evidence_sha256)
            )""")

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _validate(record: VerifiedResult) -> VerifiedResult:
        if record.verified is not True:
            raise ValueError("unverified results cannot enter the verified feed")
        if not record.game_id or not record.away_team or not record.home_team:
            raise ValueError("game id and both team identifiers are required")
        if record.away_team == record.home_team:
            raise ValueError("away and home teams must differ")
        if record.season < 1920 or record.week < 1:
            raise ValueError("season and week are outside supported NFL game ranges")
        if (isinstance(record.away_score, bool) or isinstance(record.home_score, bool)
                or not isinstance(record.away_score, int) or not isinstance(record.home_score, int)
                or record.away_score < 0 or record.home_score < 0):
            raise ValueError("final scores must be non-negative integers")
        if record.status != "FINAL":
            raise ValueError("only explicitly final results may be imported")
        if not isinstance(record.evidence_payload, bytes):
            raise ValueError("evidence_payload must contain exact captured source bytes")
        digest = _sha256(record.evidence_sha256)
        if hashlib.sha256(record.evidence_payload).hexdigest() != digest:
            raise ValueError("evidence_sha256 does not match the exact evidence_payload bytes")
        return VerifiedResult(
            game_id=record.game_id, season=record.season, week=record.week,
            away_team=record.away_team, home_team=record.home_team,
            away_score=record.away_score, home_score=record.home_score,
            status=record.status, source_url=_official_nfl_url(record.source_url),
            source_checked_at=_utc(record.source_checked_at),
            evidence_sha256=digest,
            evidence_payload=record.evidence_payload, verified=True)

    def ingest(self, records: Iterable[VerifiedResult]) -> int:
        """Validate then append a batch atomically; returns number newly inserted."""
        validated = [self._validate(r) for r in records]
        if len({(r.game_id, r.evidence_sha256) for r in validated}) != len(validated):
            raise ValueError("duplicate game/payload records in batch")
        inserted = 0
        with self._connect() as db:
            for r in validated:
                cur = db.execute("""INSERT OR IGNORE INTO result_events
                    (game_id,season,week,away_team,home_team,away_score,home_score,status,
                     source_url,source_checked_at,evidence_sha256,verified)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,1)""",
                    (r.game_id, r.season, r.week, r.away_team, r.home_team,
                     r.away_score, r.home_score, r.status, r.source_url,
                     r.source_checked_at, r.evidence_sha256))
                inserted += cur.rowcount
        return inserted

    def latest(self) -> list[dict]:
        """Return latest recorded verified revision per game, including provenance."""
        with self._connect() as db:
            return [dict(row) for row in db.execute("""
                SELECT e.* FROM result_events e
                JOIN (SELECT game_id, MAX(event_id) AS event_id FROM result_events GROUP BY game_id) x
                  ON x.event_id=e.event_id
                ORDER BY e.season, e.week, e.game_id
            """)]

    def history(self, game_id: str) -> list[dict]:
        with self._connect() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM result_events WHERE game_id=? ORDER BY event_id", (game_id,))]


def sha256_bytes(payload: bytes) -> str:
    """Digest the exact captured source bytes referenced by a result record."""
    return hashlib.sha256(payload).hexdigest()
