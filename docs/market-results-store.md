# Price snapshots and verified results: storage contract

This repository now has two standard-library SQLite storage primitives:

- `engine.snapshot_store.SnapshotStore` writes an opening snapshot when a market is originated and permits one later closing snapshot. `fair_value`, `market_value`, and the signed `difference = fair_value - market_value` are separate fields; American odds are separate from line values. Markets lacking a verified opening or closing quote are returned by `incomplete_markets()`.
- `engine.results_feed.ResultsFeed` accepts only explicitly verified `FINAL` scores with an HTTPS `nfl.com` source URL, checked-at timestamp, and exact captured source bytes whose SHA-256 matches the supplied digest. Re-importing the same game/payload is idempotent. A corrected official result is retained as another event; `latest()` selects the newest imported revision.

## Deliberate verification boundary

The libraries do **not** fetch a sportsbook or NFL page and do not themselves prove that a transcription matches the source. A collector must capture and independently verify source content before setting `verified=True`. The snapshot API verifies that the supplied digest matches the provided bytes; the results API does the same. They persist the digest and source URL/check time, not the raw payload, so an upstream collector must retain the payload in its evidence archive. Merely using an `nfl.com` URL is not proof that its contents were transcribed correctly.

Unverified market snapshots may be retained as events for completeness, but all numeric cells are forcibly blank. No values from the repository's historical third-party odds feed are imported into this new store. No strategy performance or ROI is asserted by these modules.

## Minimal use

```python
from engine.snapshot_store import SnapshotStore, sha256_bytes

store = SnapshotStore("state/market-snapshots.sqlite")
payload = b"exact captured sportsbook response bytes"
store.originate(
    market_id="game-123:spread:home", game_id="game-123",
    market_type="spread", selection="home", value_unit="points",
    captured_at="2026-11-14T15:00:00Z", source_name="book/feed name",
    source_url=verified_book_url, verified=True,  # actual checked HTTPS source, supplied by the collector
    source_payload=payload, source_sha256=sha256_bytes(payload),
    source_checked_at="2026-11-14T15:00:00Z",
    fair_value=-2.0, market_value=-1.5, american_odds=-110,
)
```

Results use `VerifiedResult` and `ResultsFeed.ingest()`. The exact payload must be passed as `evidence_payload`; only its digest is stored. The API intentionally has no sample real-game record.

## Official source check performed for this task

The NFL's 2026 regular-season schedule page was fetched and showed the Week 10 Washington–New York Giants result as **Commanders 24, Giants 21, FINAL**: [NFL 2026 Week 10 schedule](https://www.nfl.com/schedules/2026/REG10/). This validates that the official schedule source is available and illustrates the source type the results importer accepts; it is **not** a feed ingestion, a complete season dataset, or ROI evidence. The API does not claim results are loaded.
