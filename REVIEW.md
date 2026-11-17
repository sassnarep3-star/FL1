# REVIEW — what to read, what is established, and what remains open

This guide is reconciled to the committed registers and official reads through **2026-11-17 UTC**. The site contains NFL evidence, model outputs, third-party inputs and user-provided project specifications; these are different kinds of information and should not be merged.

## Start here

1. [Executive Summary](executive-summary.html) — the dated evidence boundary and the current review issues.
2. [Dashboard](index.html) — browse every root page by topic and open alternate analyses without treating them as one canonical result.
3. [Flagged for Review](flagged.html) — unresolved evidence and provenance issues, including F66 and F67.
4. [Open Questions](questions.html) and [Suggestions](suggestions.html) — what is missing, possible ways to obtain it, and proposals that still need a decision.

## Current claims to check

| Claim | Where it comes from | How to review |
|---|---|---|
| The 2026-11-17 dated result set has 149 finals and reconciles W/L/T/PF/PA for 32 clubs. The 137-game evaluation corpus remains a separate frozen input. | Official Game Center S89, league standings S90, and the dated verifier. | Open the [PIT–CIN Game Center](https://www.nfl.com/games/steelers-at-bengals-2026-reg-10), [official standings](https://www.nfl.com/standings/league/2026/REG), [S89](sources.html#S89), [S90](sources.html#S90), and run `python3 scripts/verify_results_2026_11_17.py`. |
| LAC–BAL has no result row because F67 records the game as not Final. A fresh official-page read for this audit still showed it Live. | F67 / S91 and the official Game Center. | Re-read the [LAC–BAL Game Center](https://www.nfl.com/games/chargers-at-ravens-2026-reg-10?tab=live). Do not record a score until the page says Final and the quarter-score arithmetic is checked. |
| Week 10 injury data is two dated snapshots (345 rows on 2026-11-14; 347 on 2026-11-16), not a real-time report. | S01 and S80; the [Snapshot Ledger](availability-ledger.html) preserves both reads and the diff. | Compare the [official injury report](https://www.nfl.com/injuries/) with the dated source records [S01](sources.html#S01) and [S80](sources.html#S80); run `python3 scripts/verify_recapture_g.py`. |
| The official-results luck panel describes 137 games, not the later 149-result capture. It reports a 48.9% home-win rate (67/137; one tie), with a 40.7%–57.2% Wilson interval. | The frozen results corpus, official schedule record S52, and `data/luck_panel.json`. | Read [Removal of Luck](removal-of-luck.html) and [S52](sources.html#S52); keep its sample vintage visible. |
| Third-party market/model summaries are separate from official-only results analyses; multiple implementations remain live. | Source tier S47 and F66; consolidation is an owner decision in SG47. | Open [Flagged F66](flagged.html#F66), [Suggestions SG47](suggestions.html#SG47), [Price Store](price-store.html), and the alternate readiness/luck pages linked from the Dashboard. Do not average or silently replace their results. |
| The requirements/backlog rows are user-provided project specifications, not NFL requirements or facts. | The project brief and the repository’s two requirement registers. | Read the provenance notice on [Requirement Backlog](requirements-backlog.html) and the design-target note [F65](flagged.html#F65). |

## Citation issue discovered in this audit

The schedule-announcement paragraph on [Schedule 2026](schedule.html) links to `sources.html#S86`. In the current `data/sources.tsv`, **S86 is the third-party nflverse win-totals feed**, so that source chip does not support the schedule-announcement claim. The official NFL announcement was fetched and read on 2026-11-17 at <https://www.nfl.com/news/2026-nfl-schedule-powered-by-aws-to-be-released-thursday-may-14>. The correction needs to update the source registry, its generated references and the page builder together; it is logged as an out-of-scope follow-up in [COORDINATION.md](COORDINATION.md). Until that correction lands, use the direct NFL URL, not the S86 chip.

## How to review key pages

- **Official availability evidence:** [Injuries](injuries.html), [Snapshot Ledger](availability-ledger.html), [Announced Starters](announced-starters.html), [Team Availability](team-availability.html), [Backup Depth](depth.html), and [Replacement Depth](replacement-depth.html). These pages distinguish official injury-report fields from club-published, unofficial depth order and derived joins.
- **Schedule and results:** [Schedule](schedule.html), [Standings](standings.html), [Results Feed](results-feed.html), and [Verified Results Feed](verified-results-feed.html). Dated captures and competing feeds remain separate; F67 remains open.
- **Lines and prices:** [Line Origination](line-origination.html), [Model Lines](model-lines.html), [Line Board](line-board.html), [Price Snapshots](price-snapshots.html), and [Price Store](price-store.html). Fair values, market values, and differences are separate; missing or unsupported cells remain blank and price provenance remains reviewable.
- **Strategy evaluation:** [Leaderboard](strategies.html), [Signal vs Staking](signal-vs-staking.html), [Validation Gates](validation.html), [Ablations](ablations.html), [Official Correlations](official-correlations.html), and [Removal of Luck](removal-of-luck.html). Read each result with its input tier, sample and method.
- **Decision and audit views:** [Requirements](requirements.html), [Requirement Backlog](requirements-backlog.html), [Decision Readiness](readiness.html), [Questions](questions.html), [Suggestions](suggestions.html), [Sources](sources.html), and [Verification](verification.html).

## Historic copy and stale claims

Pre-audit README, review and executive-summary documents are preserved in `archive/*-legacy-2026-11-17.md`. They contain superseded counts and claims such as “no strategy has been run,” a single 345-row injury snapshot, and older question/suggestion totals. The archive headers mark them historical; use the root-level documentation for current guidance.

## Reproduce the main checks

```bash
python3 tools/build.py
python3 tools/site.py
python3 tools/checklinks.py
python3 tools/checkrows.py
python3 -m unittest discover -s tests -q
python3 scripts/verify_results_2026_11_17.py
```

The above verification commands use the standard library. `scripts/verify_site.py` is a separate check that imports pandas; it has **not** passed in environments where pandas is unavailable. Report the outcome of each verifier independently rather than describing the whole suite as green.

**Do not run `scripts/verify_recapture_g.py` as a routine check on this branch.** It rewrites `data/verification-g.tsv` and `data/raw/MANIFEST-g.json`; its current version removed upstream Week 10 result/standings manifest entries during this audit. The generated changes were restored immediately, and the generator follow-up is logged in [COORDINATION.md](COORDINATION.md).

## Reading rule

A blank is not a value to estimate. An official source citation is evidence for what that source said at a dated read; a third-party feed, a model output, and a user-provided specification are not official NFL facts. If a row cannot be verified at the required source tier, leave the value blank and keep its review flag visible.
