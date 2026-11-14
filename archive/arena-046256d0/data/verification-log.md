# Verification Log — Line-by-Line Record

Session: arena/046256d0-fl1. Date: 2026-11-14. Rule applied: every published table row carries a link
to an official source; values that could not be confirmed from an official source are blank + flagged.

## Official sources used
| Source | Role | Link |
|---|---|---|
| NFL.com (official league site) | Standings | https://www.nfl.com/standings/league/2026/reg |
| NFL.com (official league site) | Week 10 schedule | https://www.nfl.com/schedules/2026/by-week/week-10 |
| NFL.com (official league site) | Week 10 injury report | https://www.nfl.com/injuries/ |
| NFL.com (official league site) | Game center (WAS-NYG) | https://www.nfl.com/games/commanders-at-giants-2026-reg-10 |
| NFL.com (official league site) | Team stats hub | https://www.nfl.com/stats/team-stats/ |
| DraftKings Sportsbook (official book) | Lines attempt | https://sportsbook.draftkings.com/ — no values extractable |
| FanDuel Sportsbook (official book) | Lines attempt | https://sports.fanduel.com/football/nfl — HTTP 500 |

## Row-by-row verification summary
- Standings table: 32 rows. Each row transcribed from the NFL.com league standings page fetch
  (2 chunks, all 32 teams). Cross-checked row count and W+L+T vs. games played. 1 irregularity found
  (IR-1, Thursday result not reflected). Published as-is with the irregularity flagged.
- Schedule table: 16 rows. Each game cross-checked between the schedule page and the injury report page
  (teams, times, networks). TNF game marked FINAL 24-21 from the game center page.
- Injury table: ~170 rows. Every row read from the NFL.com Week 10 injury report (8 chunks). Inclusion
  rule: injury designation, game status, or DNP. Every row links to the official injury report. No
  inference added. Resting-player designations presented verbatim.
- Lines page: all spread/total/moneyline cells intentionally blank and flagged UNVERIFIED (no official
  source reachable). No values inferred from media reports.
- Questions/Suggestions/Strategies: methodology content — proposals marked "Proposed — Pending Review";
  factual claims inside them link to the official sources listed above.

## Irregularities found
- IR-1: NFL.com standings do not reflect the completed Week 10 Thursday game (WAS 24-21 NYG) as of the
  2026-11-14 fetch. Flagged on the Flagged for Review page.

## Unverified items
- UNV-1: All sportsbook line values (blank + flagged).
- UNV-2: All player prop line values (blank + flagged).

## Checks performed
- All internal site links verified to point at real pages in this repo (built and link-checked at
  integration time).
- No fabricated values present anywhere in the published tables.
