# Review guide — how to make a decision from FL1

**Live site:** <https://sassnarep3-star.github.io/FL1/>\
**Dashboard:** [index.html](index.html) · **Decision summary:** [executive-summary.html](executive-summary.html)

This guide is a route through the repository, not a substitute for the row-level evidence. The current registers and linked source pages take precedence over dated prose in historical session notes.

## Read in this order

1. [Executive Summary](executive-summary.html) — current project posture and named blockers.
2. [Decision readiness](readiness.html) and [requirements backlog](requirements-backlog.html) — requirement-by-requirement gate and clearance criteria.
3. [Questions](questions.html) — evidence-backed answers where available, and explicit open/partial states where not.
4. [Suggestions](suggestions.html), [suggestion pipeline](suggestions-pipeline.html), and [decision desk](decision-desk.html) — options and trade-offs to review before implementation.
5. [Flagged for Review](flagged.html) — unresolved provenance, data, or interpretation issues.
6. [Sources](sources.html), [row-level source audit](source-audit.html), and [Verification](verification.html) — what was cited and what each check actually tested.

## Questions that must be answered before relying on an output

| Decision question | Evidence to inspect | What is still needed if unresolved |
|---|---|---|
| Is this input official, current, and available at the forecast cutoff? | Row citation, source registry, dated snapshot, and relevant flag | A source record with its publication/read time, captured content/hash where applicable, and a passing dataset-specific verification. |
| Is the player's status or lineup role established rather than inferred? | [Injuries](injuries.html), [availability ledger](availability-ledger.html), [announced starters](announced-starters.html), and [depth](depth.html) | Official point-in-time inactive/starter evidence and a verified replacement/playing-time basis; a blank or absent name does not establish availability. |
| Is there a comparable market price and a verified result? | [Price snapshots](price-snapshots.html), [price store](price-store.html), and [verified results feed](verified-results-feed.html) | Provenance, market/phase, timestamp, coverage, and independently verified settlement for the exact event/market. |
| Has this strategy shown skill rather than variance or staking effects? | [Strategies](strategies.html), [signal vs. staking](signal-vs-staking.html), [removal of luck](removal-of-luck.html), and [validation](validation.html) | Frozen pre-registration, chronological holdout/prospective evidence, benchmark-relative proper scores, uncertainty, multiplicity handling, and a sample that clears its stated gate. |
| Are correlation or combined-bet probabilities directly supported? | [Correlation register](correlation-register.html), [official correlations](official-correlations.html), and [prop correlations](prop-correlations.html) | Officially sourced inputs, published `n`, uncertainty, and direct joint-probability validation plus applicable settlement rules. Marginal probabilities alone are not enough. |
| Which implementation path should be chosen? | Related question in [Questions](questions.html) and proposal in [Suggestions](suggestions.html) | Resolve the named dependency, compare costs/risks, and record an explicit decision before implementation. |

A question marked **answered** is answered only within its stated evidence and date. **Partial** means a material gap remains; **open** means no decision should be inferred. Follow the page's source links and answer notes rather than treating a status label as universal validation.

## Review proposals before choosing a path

The Suggestions pages are the dedicated review section. For each item, check its linked question(s), what evidence it assumes, alternatives, cost/risk, and the proposed validation gate. Do not interpret a recommendation as approval or silently implement a suggested source/model feature. Record the selected path and its reason in the project's decision register before changing the model or publishing a leaderboard result.

## Data and scoring cautions

- The [source audit](source-audit.html) is a metadata audit, not a live fetch of every source or a full line-by-line fact re-verification. It explicitly classifies non-official, unregistered, repository-only, and missing-citation rows.
- The [readiness table](readiness.html) and [flagged page](flagged.html) are essential: a requirement can be represented in the site while still blocked or unverified.
- Keep historical snapshots immutable and use only information available by the forecast timestamp. Never use post-kickoff or later status/results as pregame inputs.
- Treat official designations, club depth labels, announced starters, actual participation, and snap share as distinct evidence. Do not convert one into another without a validated rule.
- Evaluate models with chronological out-of-sample data and proper scores; report uncertainty and benchmark-relative skill. Keep signal quality separate from staking and realized ROI.
- Keep singles, parlays, same-game parlays, and player-prop combinations in separate validation divisions. Do not multiply marginal probabilities and call the result a validated joint price.
- The site and repository may contain dated examples or partially populated research outputs. Their existence does not mean a strategy is qualified, a data feed is complete, or the market price is executable.

## Reproduce the local checks

From the repository root:

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

A successful check only supports the claims within that check's scope. The site-level link checker does not fetch or validate external facts. Review the exact verification notes and warnings before relying on any result.
