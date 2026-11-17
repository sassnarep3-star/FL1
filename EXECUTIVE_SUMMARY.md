# FL1 — Executive Summary

**Status date:** 2026-11-17 UTC<br>
**Site:** <https://sassnarep3-star.github.io/FL1/>

FL1 is a static research and decision-support site, not an NFL publication and not a validated betting system. This summary separates dated official evidence from derived analyses and user-provided project specifications. A link to an official page is evidence for what that page showed at its recorded read; it does not make a model output an NFL fact.

## Verified official evidence

| Evidence item | Published record and limitation | Official source for manual review |
|---|---|---|
| Latest dated 2026 results read | The 2026-11-17 results set contains **149 finals** and reconciles the league's W/L/T/PF/PA standings for all 32 clubs. | [Steelers at Bengals Game Center — Final](https://www.nfl.com/games/steelers-at-bengals-2026-reg-10) · [NFL 2026 league standings](https://www.nfl.com/standings/league/2026/REG) · [S89](sources.html#S89) · [S90](sources.html#S90) |
| Frozen evaluation corpus | The separate `data/results.tsv` corpus remains at **137 games**. It was not silently extended by the later dated results capture. | [NFL 2026 schedule/results pages](https://www.nfl.com/schedules/2026/by-week/week-10) · [S52](sources.html#S52) |
| Week 10 injury evidence | Two dated snapshots are retained: **345 rows (2026-11-14)** and **347 rows (2026-11-16)**. They are point-in-time captures, not a statement of today's live injury status. | [NFL Injury Report](https://www.nfl.com/injuries/) · [S01](sources.html#S01) · [S80](sources.html#S80) · [Snapshot Ledger](availability-ledger.html) |
| LAC at BAL | **No result is recorded.** F67 remains open because the official Game Center was still marked Live on the audit's re-read. A live score is not a final result. | [Chargers at Ravens Game Center](https://www.nfl.com/games/chargers-at-ravens-2026-reg-10?tab=live) · [S91](sources.html#S91) · [F67](flagged.html#F67) |
| Official-results luck panel | The separate frozen-sample panel uses **137 games** and reports 67 home wins, 69 away wins and one tie: a 48.9% home-win rate, with a 95% Wilson interval of 40.7%–57.2%. This is a computed statistic for that sample, not a 149-game update or a league-published estimate. | [NFL 2026 schedule/results pages](https://www.nfl.com/schedules/2026/by-week/week-10) · [S52](sources.html#S52) · [Removal of Luck](removal-of-luck.html) |

The official results and injury evidence are dated and separately preserved. The latest 149-result set and the 137-game evaluation corpus answer different questions; they must not be conflated. F67 should be resolved only after a fresh official Final check and the existing standings reconciliation passes.

## Analyses and limits

The repository has multiple analysis implementations and source tiers. A signal panel based on the computed research layer reports **no strategy clearing its family-wise threshold**, but its inputs include third-party market data; this is a model result, not an NFL statement. Other official-results-only and readiness views use different inputs or criteria. F66 records that these overlapping pages remain published pending owner review under SG47. Keep their methods and conclusions separate; no canonical view is declared here.

The project still does not establish a validated, prospective edge or a deployable betting system. Market-data provenance/policy, source coverage, calibration, prospective records, uncertainty and governance gates remain material. Values unsupported at the required source tier remain blank and flagged; third-party inputs remain labelled as such.

## Project specifications, not NFL requirements

The two requirement registers contain **28 core rows and 59 backlog rows**. These are transcriptions of user-provided project specifications and repository planning criteria—not NFL rules, NFL policy or facts about the league. The statuses and blockers describe repository work. “Numbers that clear” are measurable project targets, not NFL-published thresholds; see [F65](flagged.html#F65).

- [Requirements](requirements.html) — core register.
- [Requirement Backlog](requirements-backlog.html) — full specification backlog with an explicit provenance notice.
- [Decision Readiness](readiness.html) — readiness and gate view.
- [Open Questions](questions.html) and [Suggestions](suggestions.html) — missing information and possible acquisition or policy paths.

## Citation issue to keep visible

The announcement block on [Schedule 2026](schedule.html) currently links to `sources.html#S86`. In the current source register S86 identifies an nflverse win-totals feed, not the schedule announcement. The [official NFL announcement](https://www.nfl.com/news/2026-nfl-schedule-powered-by-aws-to-be-released-thursday-may-14) was fetched and read on 2026-11-17. The source-register ID, generated references and page builder need to be corrected together; the follow-up is recorded in [COORDINATION.md](COORDINATION.md). Until then, the S86 chip is not valid evidence for that announcement.

## Where to go next

- [Dashboard](index.html) for topic-grouped navigation and the retained alternate analyses.
- [Sources](sources.html), [Verification](verification.html) and [Flagged for Review](flagged.html) for provenance, checks and open issues.
- [Review guide](REVIEW.md) for manual source checks, current caveats and reproducible commands.

Nothing here is a bet, an offer to wager, betting advice, or a statement about legality in any jurisdiction. No regulator or tax source has been verified.
