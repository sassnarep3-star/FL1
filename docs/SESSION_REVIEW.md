# Decision-readiness review (2026-11-19)

## Executive finding

The repository is a substantial, reproducible static research dashboard, not a live betting or automated data-ingestion service. The current checkout contains dedicated pages and data/gates for line origination, prices, results, availability, replacement depth, correlations, strategy validation, demotion, luck removal, suggestions and flagged items. Repository test/build consistency does **not** establish that the underlying external fact is true or current: the source audit explicitly classifies many rows as code-only, unregistered, non-verified, or missing a source, and `checklinks.py` does not fetch external links. No live market prices or official NFL results should be implied from the presence of the pages alone.

**Decision now:** retain an explicit shadow/paper-only posture. Do not recommend a wager, publish a performance claim, or promote a strategy to live staking until a complete provenance-linked forecast, benchmark price, official outcome, and pre-registered chronological evaluation exist. The repo itself states in `README.md` that no line has been originated and no strategy has a result; check this claim against the current generated model/result datasets before each release.

## What this checkout demonstrates

- The current tree has a static site and a sizable set of deterministic data, validators, and tests. The local test suite passed: 356 tests (`python3 -m unittest discover -s tests -q`). Internal site links and registered source IDs passed for 57 pages; the row audit checked 7,019 rows. These are software/data-structure checks, not external-source verification.
- Questions and suggestions are maintained as distinct records (`data/questions.json`, 46 rows; `data/suggestions.json`, 51 rows). Requirements and flags are also registered (`data/requirements.json`, 29; `data/flags.json`, 72). These counts describe this checkout only.
- Existing standalone pages cover side/total/moneyline origination, market price snapshots, official-results feed, line decomposition, correlation gates, injury/depth availability, strategy scorecards, demotion, validation, luck removal and decision readiness. That means this session recommends improving the evidence and workflow behind the existing sections rather than duplicating them in another dashboard.
- The existing site source-row audit (see `source-audit.html` and `docs/SOURCE_ROW_AUDIT.md`) is explicit that it classifies citation syntax/registry metadata and does not freshly open external sources or validate every claim.

## Decision-readiness table

| Decision | Known from this repo | Missing / must be established before decision | Gate to clear |
|---|---|---|---|
| Whether a strategy has signal | Pre-registration, proper-score and validation concepts exist; a leaderboard is not by itself evidence of skill. | Frozen prospective forecasts with timestamped inputs; adequate out-of-sample games; baseline comparisons; uncertainty and multiplicity correction. | Rebuild scores only from pre-kickoff predictions and verified final outcomes; separately report benchmark-relative skill and uncertainty. |
| Whether a bet has value | Fair/market/residual decomposition and price storage are represented. | A licensed/approved, reproducible price feed with exact quote time, market, operator, rules, odds and open/close identity; vig removal method. | Price provenance, policy, freshness and settlement rules all pass; otherwise market/residual fields stay blank. |
| Whether injuries affect a line | Injury, availability and ablation areas exist. | Immutable report history (fetch time, raw hash), official active/inactive evidence, and actual participation/snap counts linked to the correct game and roster state. | Chronological, paired ablation with verified records and uncertainty; never convert a designation directly into a fixed points penalty. |
| Whether a replacement is truly a backup | Depth and announced-starter pages exist. | A verified dated club depth source per club/position, or a verified official snap-count route; shared/empty slots, roster turnover and source conflicts retained. | Coverage and parsing QA for all 32 clubs; confirmed starter/replacement event, not jersey number, salary, tenure or inferred rank. |
| Whether a player/prop combo can be ranked | Correlation pages and combo gates exist. | Joint outcome samples with linked game/player IDs, market settlement/void/push rules, sample counts and time-aware holdouts. | Directly validated joint probability; marginal multiplication alone is disallowed. Publish n and uncertainty with every correlation. |
| Whether a strategy should go live or be demoted | Validation and demotion-gate sections exist. | Concrete numeric gates, monitoring cadence, prospective evidence window, and a tested automatic transition to paper. | Freeze gate values before the evaluation interval; fail closed on stale/missing inputs, calibration drift or insufficient sample. |
| Whether site facts are current and official | Source registry and row-level audit exist. | Routine URL/status/content checks, archived source snapshots, current source-of-record approval, and explicit data terms/licensing review. | Per-row source ID and capture time; show unverified/absent values blank, with a visible review flag. |

## Highest-priority information requests (machine-discoverable, no user hand-entry)

1. **Market data policy and provider:** choose an authorized feed; define allowed storage/display, market coverage, timestamp semantics, book/consensus policy, opening/closing definition, push/void grading, and retention. Until this exists, do not fill market-price or CLV fields.
2. **Official outcomes and identities:** establish the canonical NFL game identifier and official final score/result source; preserve corrections and postponements as dated versions. Make result ingestion idempotent and reconcile against a second official NFL record before scoring.
3. **Availability snapshots:** automated scheduled capture from official NFL injury reports and club pages plus official inactives; raw response/file hash, fetch clock, source URL, parser version, player identity, conflict state and immutable retention. A later revision must not overwrite what was known before kickoff.
4. **Replacement evidence:** assess every club source independently. Track position groups/slots (including shared or blank slots), validity dates, transactions and named announced starters. Do not label a replacement from jersey order or roster-only clues. If club charts are incomplete, verify whether official snap counts offer a complete alternative before using the feature.
5. **Prospective model pipeline:** start with a single market and simple frozen baseline; log probability, inputs, model/version hash, source snapshot IDs and kickoff cutoff before game start. Keep train, validation and final holdout seasons disjoint. Add parlays/props only after direct joint-outcome validation.
6. **Statistics and leaderboard:** use proper scores, benchmark-relative skill, game-clustered uncertainty, multiple-trial correction and randomized/favorites controls. Keep signal skill separate from staking and realized ROI. Publish the denominator, eligible sample, exclusions and n.
7. **Operational controls:** freshness alarms, schema/row-count drift checks, failed-source quarantine, source terms review, privacy boundary for raw data, and a tested paper demotion path. A static GitHub Pages site cannot provide durable private capture storage or a secure ingestion scheduler by itself.

## Strategy discovery plan

1. Pre-register a transparent team-strength baseline and side market only; freeze feature definitions, sample window, scoring, benchmark and gates in version control before evaluation.
2. Generate pre-kickoff probabilities from data available at that timestamp. Never include a backtest-only result on the prospective leaderboard.
3. Compare against published controls (random and favorites) and a market benchmark only when price provenance is licensed and verified. Score Brier/log loss and calibration; show confidence intervals and game-clustered lower bounds.
4. Add total and moneyline in that order only after side pipeline and verification pass. Run availability/depth features as paired ablations rather than fixed injury penalties.
5. Allow parlays and prop combos only with directly validated joint probabilities and documented settlement rules. Publish correlation estimates with sample size, uncertainty and source eligibility.
6. Keep paper/live status explicit. Promote only after prospective gates pass; demote automatically when pre-registered triggers fire. Do not rank by raw win rate or season ROI.

## Review flags / irregularities

- A green unit-test, link-check, or registered source ID is not proof that an official source currently resolves or that a displayed value matches it. The local checker says external links are not fetched; manual/current source verification remains a separate gate.
- Counted rows in JSON registries are not unique verified findings. Requirements marked `done` may represent earlier sessions or historical evidence; inspect the cited source records and dates before treating those statuses as current.
- Public static pages are appropriate for derived summaries and official links, but immutable raw captures, restricted/vendor prices and licensing-sensitive records need a durable controlled data store outside the public Pages tree.
- No new NFL factual values were introduced by this review. Official-source citations and current values remain those already in the repository's source registry; unverified claims should remain flagged rather than elevated.

## Verification performed

From the repository root on 2026-11-19 UTC:

- `python3 -m unittest discover -s tests -q` — 356 passed; existing `ResourceWarning` messages from test file handles were emitted, not failures.
- `python3 tools/checklinks.py` — 57 pages, internal links/anchors and registered source IDs passed; reports 263 external links were **not fetched**.
- `python3 tools/checkrows.py` — 57 pages and 7,019 rows audited; output states 310 register/spec rows and 6,709 data rows satisfied its configured rules. This is a structural/citation-rule audit, not line-by-line external fact validation.

## Official source review links

These are the official locations already relevant to the project; linking them here is for human review and does not assert that each underlying record was freshly re-fetched in this session:

- NFL schedule: https://www.nfl.com/schedules/
- NFL injury report: https://www.nfl.com/injuries/
- NFL transactions: https://www.nfl.com/transactions/
- NFL game center: https://www.nfl.com/scores/
- NFL Football Operations (rules and league operations): https://operations.nfl.com/

Use the repository's `sources.html` and `source-audit.html` for row-specific source IDs and their recorded verification status. External URLs were not fetched by this session's local checkers.
