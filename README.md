# FL1 — NFL Line Lab

A static NFL research and decision-support site. It preserves the distinction between official records, third-party inputs, derived analyses, project decisions, and values that remain unknown. It is **not** an NFL publication or a validated betting system.

**Live site:** <https://sassnarep3-star.github.io/FL1/><br>
**Documentation status:** reconciled against the committed registers and dated official reads through 2026-11-17 UTC.

## Current state

- The latest dated official results set contains **149 completed games** and reproduces the official standings for all 32 clubs. It is a separate dated extension; `data/results.tsv` remains the frozen **137-game** evaluation corpus and was not silently extended. See the [official Steelers–Bengals Game Center](https://www.nfl.com/games/steelers-at-bengals-2026-reg-10), the [2026 league standings](https://www.nfl.com/standings/league/2026/REG), and source records [S89](sources.html#S89), [S90](sources.html#S90).
- **LAC at BAL remains open in F67.** The official Game Center was still marked Live when re-read for this audit; no final score is recorded here. Recheck the [official Game Center](https://www.nfl.com/games/chargers-at-ravens-2026-reg-10?tab=live) after it explicitly shows Final before adding a result.
- Injury evidence consists of separate, dated Week 10 captures: **345 rows on 2026-11-14** and **347 rows on 2026-11-16**. They are point-in-time records, not a claim about the live report today. See the [snapshot ledger](availability-ledger.html), source records [S01](sources.html#S01) and [S80](sources.html#S80), and the [official NFL injury report](https://www.nfl.com/injuries/).
- The official-results luck panel still evaluates the **137-game frozen sample**: home wins were 48.9% (67 of 137; one tie), with a 95% Wilson interval of 40.7%–57.2%. This is a computed sample result, not an NFL-published estimate or a 149-game update. See [Removal of Luck](removal-of-luck.html) and the official schedule source [S52](sources.html#S52).
- Separate market/model views use third-party inputs and must not be mistaken for official NFL facts. The repository retains competing readiness and luck analyses pending owner review under **F66 / SG47**; see [Flagged for Review](flagged.html#F66) and [Suggestions](suggestions.html#SG47). No view is designated canonical by this documentation.

## Requirements are project specifications

The requirement registers and backlog transcribe **user-provided project specifications**. They are planning and acceptance criteria for this repository—not NFL rules, NFL policy, or facts about the league. Their statuses, blockers and “number that would clear it” values are project records or proposed targets; see [Flagged for Review F65](flagged.html#F65). The current registers contain 28 core rows and 59 backlog rows; inspect each view separately:

- [Requirements](requirements.html) — core register.
- [Requirement Backlog](requirements-backlog.html) — line-by-line project-spec backlog.
- [Decision Readiness](readiness.html) — gate and readiness view.

## Where to start

- [Dashboard](index.html) — current evidence boundary and topic navigation.
- [Executive Summary](executive-summary.html) — dated official evidence, analysis boundaries, and open review items.
- [Open Questions](questions.html) and [Suggestions](suggestions.html) — missing information, ways to obtain it, and proposals for review.
- [Sources](sources.html), [Verification](verification.html), and [Flagged for Review](flagged.html) — provenance, reproducibility checks, and unresolved items.

The navigation groups every root page by topic. The Dashboard also links to alternate pages and explicitly retains overlapping analyses while F66/SG47 remains open.

## Evidence and interpretation

- Official source citations identify what a dated NFL or club page said at the recorded read. Live pages can change; the dated captures and their hashes are the audit record.
- Derived metrics should be read with their sample, inputs, date and source tier. Third-party inputs are labelled and are not NFL publications.
- A blank means the value was not confirmed for that field; it is not an estimate. A flag or open question remains visible until supported by evidence or a recorded decision.
- The requirement backlog is user-provided specification text, not a factual data table. Its criteria do not acquire NFL authority by appearing on this site.

## Rebuild and checks

From the repository root:

```bash
python3 tools/build.py
python3 tools/site.py
python3 tools/checklinks.py
python3 tools/checkrows.py
python3 -m unittest discover -s tests -q
python3 scripts/verify_results_2026_11_17.py
```

The static HTML is committed for GitHub Pages; these commands regenerate and check it locally. The main build and the commands above use the Python standard library. Some additional research/CI scripts import optional scientific packages; for example, `scripts/verify_site.py` requires pandas, so do not treat it as passed when pandas is unavailable.

**Caution:** do not add `scripts/verify_recapture_g.py` to this routine on the current branch. Its current implementation rewrites `data/verification-g.tsv` and `data/raw/MANIFEST-g.json`; during this audit it removed upstream Week 10 result/standings entries from those files. The generated changes were restored, and a coordinated fix is logged in `COORDINATION.md`.

## Repository map

- `data/` — registers, dated transcriptions and derived data stores. Do not collapse dated snapshots into a single “current” value.
- `raw/` and `data/raw/` — source captures and manifests used by the verification scripts.
- `tools/site.py`, `tools/site_g.py` — root-page generation and shared navigation.
- `tools/checklinks.py`, `tools/checkrows.py` — link/reachability and row-source audit gates.
- `tests/` — unit and regression checks.
- `COORDINATION.md` — task ownership, source decisions, and unresolved cross-session issues.
- `archive/*-legacy-2026-11-17.md` — preserved pre-audit documents; historical, not current guidance.

## Known source-citation issue

The dated schedule-announcement callout on `schedule.html` currently links to source ID S86, but S86 in the current source register identifies an nflverse win-totals feed, not the announcement. The official announcement itself is available at [NFL.com](https://www.nfl.com/news/2026-nfl-schedule-powered-by-aws-to-be-released-thursday-may-14). The source-register/generator correction is logged in [COORDINATION.md](COORDINATION.md); until that correction is made, do not use the S86 chip as evidence for the announcement. This finding is also detailed in [REVIEW.md](REVIEW.md).

## Not advice

Nothing here is a bet, an offer to wager, betting advice, or a statement about legality in any jurisdiction. No regulator or tax source has been verified.
