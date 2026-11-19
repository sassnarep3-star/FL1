# Independent repository review — 2026-11-19

## Scope and evidence boundary

This review inspected the committed repository, ran its local build and checks, and wrote this dated verification note. It did **not** fetch NFL pages during this review. Source URLs and `VERIFIED` states below are repository records with historical check dates, not fresh confirmations. No sports fact or external value was newly promoted to verified. The top-level README and review guide were concurrently refreshed by parallel sessions merged to `main`; those upstream files are preserved unchanged here.

## Review outcome

The repo already contains a broad static dashboard and substantial engines/registers for price snapshots, game results, model origination, injury/availability, strategy gates, removal of luck, correlations, and recommendations. During this review, parallel sessions on `main` also identified and fixed stale top-level README/review-guide claims. Those updates are retained as the authoritative reader documentation; this session's separate contribution is an independent audit record of the checks, provenance limits, and unresolved review risks.

## Checks run on the resulting tree

- `python3 -m unittest discover -s tests -q` — **356 tests passed**. The suite emitted pre-existing `ResourceWarning` messages for unclosed files in several tests; they did not fail the run.
- `python3 tools/build.py && python3 tools/site.py` — completed. Core generated outputs matched the committed tree; `git status` was clean after generation. The generators report 32 teams, 345 injury rows, 91 source-register entries (82 marked `VERIFIED`), 46 questions, 51 suggestions, 29 requirements, 6 registered strategies, and 72 flags.
- `python3 tools/checklinks.py` — **57 pages**; all internal links, anchors, reachability and source IDs resolved. It reported **263 external links**, explicitly not fetched.
- `python3 tools/checkrows.py` — **57 pages; 7,019 rows audited** (310 register/spec rows plus 6,709 data rows satisfying the checker’s rules).
- `python3 tools/verify_drift.py` — **19 pins, 19 PASS**.
- `python3 tools/verify_injuries.py` — all **345 canonical injury rows** match the retained raw capture field-by-field and in order. This is a capture-to-table transcription check, not a fresh read of the NFL injury hub.
- `python3 tools/verify_results.py` — 137-game corpus (including Week 10 Thursday) reproduces the dated standings for all 32 clubs. The diagnostic 136-game view excluding that Thursday game has expected WAS/NYG discrepancies and is not the passing corpus.
- `python3 scripts/verify_site.py` — **not run successfully**: the environment lacks `pandas` (`ModuleNotFoundError`). The workflow installs it; this review does not claim that verifier passed.
- `python3 scripts/build_market_spine.py --check` — **PASS**; all listed market artefacts rebuilt byte-identically (78,410 snapshots, 23,219 trades, 13,310 published trades, 137/272 verified 2026 results, 28 demotion triggers). The rebuild verifies determinism against the committed captures, not source truth or prospective performance.

## Source and data-quality findings

The deterministic source-row audit produced **6,891 rendered table-row records**: 3,982 `OFFICIAL_REGISTERED`, 147 `REGISTERED_NOT_VERIFIED`, 467 `NONOFFICIAL_REGISTERED`, 629 `MIXED_OR_UNRESOLVED_REGISTERED`, 1,340 `REPOSITORY_LINK_ONLY`, 121 `DIRECT_LINK_UNREGISTERED`, and 205 `NO_SOURCE_LINK`. These are mutually exclusive metadata classes emitted by `tools/source_audit.py`; they are not a determination that a data value is correct or incorrect. The count differs from `checkrows.py` because the audit classifies rendered source-bearing rows while `checkrows.py` also counts register/specification rows under separate rules. See [Source Row Audit method](SOURCE_ROW_AUDIT.md) and the published [Row-Level Source Audit](../source-audit.html).

The market-spine summary at `data/market/summary.json` is dated **2026-11-14**. Its current record reports 78,410 snapshots, 56,624 undocumented-vintage events, 1,088 quarantined rows, 137 verified 2026 results, 9 evaluated variants, zero variants clearing the signal gate, zero rewards paid, and 28 demotions. Historical odds are drawn from community data with explicit provenance limitations; they are not an official NFL price feed. Do not present these figures as current live status or prospective performance. Review `data/sources.tsv` entries S70–S76 and the flagged records, especially F47.

## Specific issues to retain for review

1. **External URLs are not checked by the internal link checker.** Its 263 external links resolve only as URL text. Fresh source retrieval and claim-level comparison remain a separate task.
2. **Most rows have not received a new line-by-line official-source check in this session.** Only the canonical injury table and the aggregate result/standings arithmetic were tested locally against retained inputs. No broad claim that every rendered value is currently verified is made here.
3. **The historical market corpus is not an eligible live leaderboard.** Its vintage/provenance limitations and negative skill-gate result are published; the dated metrics should not be generalized.
4. **Full `verify_site.py` remains environment-dependent.** Install the repository workflow's pandas/numpy/scipy dependencies before relying on that rebuild verifier.
5. **Test suite warnings remain.** Several tests open files without context managers; warnings are non-fatal, but should be cleaned in a future tests-only change.

## Official source locations already in the registry

These links are listed as official sources in `data/sources.tsv` with historical read dates; they were **not fetched again on 2026-11-19**:

- NFL injury report hub: <https://www.nfl.com/injuries/>
- NFL 2026 Week 10 schedule/results: <https://www.nfl.com/schedules/2026/REG10/>
- NFL 2026 regular-season standings: <https://www.nfl.com/standings/league/2026/REG>

Open the linked source record in [Sources](../sources.html) for the recorded date and scope before relying on a claim.
