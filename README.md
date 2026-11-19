# FL1 — NFL Line Lab

A static, evidence-oriented project for NFL line origination research. It separates sourced observations, model outputs, evaluation, and review decisions; a blank means the project has not established a value and must not be read as zero or as availability.

**Published site:** <https://sassnarep3-star.github.io/FL1/>\
**Start here:** [Dashboard](index.html) · [Executive summary](executive-summary.html) · [Review guide](REVIEW.md)

## What the project can and cannot establish

This repository contains a substantial requirements register, data/evidence pages, model and evaluation code, and governance proposals. It is a research and audit workspace, not a currently qualified betting product. A repository artifact or generated table is not, by itself, independent verification of the underlying NFL fact. Check the evidence and verification status shown on the relevant page before relying on any row.

The [row-level source audit](source-audit.html) distinguishes official-source references from repository build artifacts, unregistered links, non-official sources, and missing citations. It audits citation metadata; it does **not** fetch every external URL or independently re-check every claim. The [Flagged for Review page](flagged.html) records unresolved discrepancies and unverified items. Do not treat a value marked unverified, stale, partial, or flagged as confirmed.

The project has code and ledgers for line origination, prices/results, strategy evaluation, injuries, availability, depth, correlations, and model outputs. Their presence does not mean that a strategy passed its gates, that all-market opening/closing prices are complete, or that a feature is ready for wagering. Read the [readiness table](readiness.html), [validation gates](validation.html), [strategy scorecard](strategy-scorecard.html), and [suggestions](suggestions.html) for the current state and blockers. In particular, backtest, paper, and prospective evidence must not be conflated; consult each strategy's registration and evidence window.

No user action is required to reproduce the local static build, but not every data source is automatically refreshed. The scheduled workflow documents its limited scope; it is not a guarantee of daily collection for every feed. Freshness and coverage should be checked on the relevant ledger before use.

## Decision-making paths

| Need | Start here | How to use it |
|---|---|---|
| Understand the project and immediate blockers | [Executive Summary](executive-summary.html), [Readiness](readiness.html) | Review the status and gate for each requirement. Treat blanks and partial states literally. |
| See what is known, what remains unknown, and what would resolve it | [Questions](questions.html) | Each question includes an answer state; open or partial entries name the unresolved decision or missing evidence. |
| Review options before implementation | [Suggestions](suggestions.html), [Suggestions pipeline](suggestions-pipeline.html), [Decision desk](decision-desk.html) | Compare the proposed paths, trade-offs, dependencies, and linked questions. A suggestion is not an approved change. |
| Inspect problems that need human attention | [Flagged for Review](flagged.html) | Review the cited source, discrepancy, and stated limitation before promoting a value or method. |
| Trace provenance | [Sources](sources.html), [Source audit](source-audit.html), [Verification](verification.html) | Check each source's declared status and each verifier's actual scope; an internal link checker is not an external fact check. |
| Review lines, prices, outcomes, and strategy skill | [Origination](line-origination.html), [Price snapshots](price-snapshots.html), [Results feed](verified-results-feed.html), [Strategies](strategies.html), [Removal of luck](removal-of-luck.html) | Separate fair estimate, market observation, settlement, signal quality, and staking results. Confirm sample size and evidence stage. |
| Examine injury and lineup evidence | [Availability ledger](availability-ledger.html), [Injuries](injuries.html), [Team availability](team-availability.html), [Depth](depth.html), [Matchup matrix](availability-matrix-d5.html) | Distinguish dated official evidence from derived or unavailable depth; do not infer a replacement from a blank. |
| Inspect model and statistical inputs | [Model lines](model-lines.html), [Ablations](ablations.html), [Correlations](correlation-register.html) | Check provenance, input definitions, sample size, and validation status before interpreting an estimate. |

The site has additional category pages; navigation is available from each page. The registers and data files under `data/` are the durable inputs for generated views. Historical session notes in `EXECUTIVE_SUMMARY.md` and `COORDINATION.md` document how artifacts were produced, but later dated reads and flags supersede earlier statements where they conflict.

## Repository layout

```
index.html and other root HTML     committed static pages served by GitHub Pages
assets/                            styles and browser-side helpers
data/                              source registers, normalized records, and derived ledgers
raw/                               captured source material and dated reads
engine/                            pricing, settlement, scoring, gates, and statistical code
scripts/                           dataset-specific builders and verifiers
tools/                             site generation, link/row checks, and audits
tests/                             unit and repository regression tests
COORDINATION.md                    shared task board and integration history
EXECUTIVE_SUMMARY.md               dated session summaries and verification records
```

## Rebuild and check locally

Run from the repository root with Python 3:

```bash
python3 -m unittest discover -s tests -v
python3 tools/build.py
python3 tools/site.py
python3 tools/checklinks.py
python3 tools/checkrows.py
python3 tools/verify_drift.py
python3 tools/verify_injuries.py
python3 tools/verify_results.py
python3 tools/verify_replacement.py
```

These checks have different coverage. Unit tests exercise code and fixtures; builders regenerate local artifacts; link/row checks inspect the committed site; dataset verifiers check only their named datasets and invariants. A passing local check does not prove every external source is live or that every displayed claim has been independently re-verified. Consult [Verification](verification.html) and [Source audit](source-audit.html) for the published scopes and findings. Some research scripts require optional scientific Python packages; install requirements from `requirements.txt` when running those scripts.

The root HTML is committed for static hosting. After changing data or a generator, regenerate the affected outputs, review the diff, and run the checks that cover the changed dataset before publishing.

## Source and interpretation rules

- **No inference to fill a blank.** Missing evidence remains missing and should be flagged.
- **Provenance is claim-specific.** Follow the source link on the row and inspect the registry status; do not assume a whole table is official because one column has an official source.
- **Time matters.** Use dated snapshots and deltas for point-in-time analysis. A later capture must not leak into an earlier forecast.
- **Observed and derived values are different.** A model output or join is not an official statement; review its inputs and transformation.
- **Skill is not realized return.** Use the registered scoring rules, uncertainty, benchmark comparisons, and sample windows. Raw win rate or ROI alone is not sufficient evidence.
- **Suggestions are review items.** They are not implementation instructions until a path is selected and its validation gates are met.

## Not betting advice

Nothing in this repository is an offer or recommendation to wager. The project does not establish the legality of betting or prizes in any jurisdiction; consult qualified legal counsel and relevant regulators before any commercial or reward program.

---

## 2026-11-19 official re-verification (session `arena/d022d49b-fl1`)

This addendum records the audit branch's state at the time of the re-reads; it is not a live read.
At that time, the checkout contained 57 HTML pages, 46 questions (12 answered / 16 partial / 18 open),
51 suggestions, 72 flags and 91 source-registry rows. These are repository counts, not NFL facts. The
official-read captures and row-level checks are linked below. The audit distinguishes fresh official data
from repository provenance and third-party data.

- **Week 11 injury hub:** first Week 11 capture, 253 player rows parsed with the same grammar as the
  prior reads; the header claim and parser agree. Read 4 was Week 10 and read 5 Week 11, so their
  difference is stored as a labelled *week rollover*, not substituted for the existing same-week delta.
  Full raw capture: [`raw/injuries-week11-2026-read5.md`](raw/injuries-week11-2026-read5.md);
  parser and delta: [`data/injury_hub_delta.json`](data/injury_hub_delta.json). Official source:
  [NFL injury report](https://www.nfl.com/injuries/). The canonical `data/injuries.tsv` was not replaced.
- **Standings:** all 32 clubs match the 2026-11-17 closeout side-read on W/L/T/PCT/PF/PA after a fresh
  2026-11-19 NFL.com read. The historical canonical standings were left unchanged under the open Q44
  promotion decision. [Dated capture](raw/standings-2026-11-19.md) ·
  [official NFL standings](https://www.nfl.com/standings/league/2026/REG).
- **Week 11 schedule and venues:** 13 official scheduled games and 13 official Game Center venues were
  re-read. The official schedule page and game centres are linked per row in
  [`raw/schedule-week11-2026-2026-11-19.md`](raw/schedule-week11-2026-2026-11-19.md). The third-party
  `data/schedule2026-d.csv` differs from the official schedule on two kickoff times (PIT@PHI and
  JAX@NYG), and its ARI@KC stadium label differs from the Game Center text; these values are not silently
  overwritten. The schedule reader also reported an inconsistent total-chunk count across calls.
- **Published-page citation gaps:** the existing `live-schedule.html` table has 12 rows with an empty
  Game Center link and blank venue. The official Game Center links and venues are captured above; a
  change request is logged in `COORDINATION.md` because the current site-generator files overlap open
  PR #57. The affected rows are therefore marked for integration, not presented as verified site output.
- **Audit artifact:** [`data/verification-2026-11-19.tsv`](data/verification-2026-11-19.tsv) contains 134
  records: 32 standings comparisons, 13 schedule comparisons, 13 venue comparisons, 13 live-page row
  checks, four injury/pagination checks, and 59 requirement-backlog trace rows. A backlog trace is only
  an artifact/source-registry audit; it does not mean every listed requirement is complete or that every
  older NFL fact was freshly re-fetched. Rows without a registered official source URL are left blank and
  carry a review flag.

**Important constraint:** read-specific source-register IDs for the 2026-11-19 injury, standings, and
schedule reads remain pending PR #57's source-ID reconciliation. Any S01/S03/S93 values in the audit
rows are historical official-URL references only; they are not the new capture records. Each fresh read
is separately evidenced by its dated raw capture and the explicit capture date in the audit status. The
injury delta also keeps the URL reference S01 alongside its distinct read date and Week 11 selector. The
site renderer and Flagged for Review register updates requested in `COORDINATION.md` remain an integration
dependency.
