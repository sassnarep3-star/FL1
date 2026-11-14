# FL1 — Coordination Board

Shared task board for the NFL lines origination, injury/deficiency tracking, and GitHub Pages site project.
Branch: `arena/a7c0f9c5-fl1` (branched from `e001e0a` of `main`).
Remote: https://github.com/sassnarep3-star/FL1.git

## Session registry

| Session ID | Branch / Worktree | Status |
|---|---|---|
| session-arena-a7c0f9c5-fl1 | arena/a7c0f9c5-fl1 (current working branch) | active |

## Task board

| Task ID | Description | Status | Owner | Files in scope | Sources / verification | Irregularities |
|---|---|---|---|---|---|---|
| TASK-1 | Create COORDINATION.md task board and claim all tasks | done | session-arena-a7c0f9c5-fl1 | COORDINATION.md | n/a | none |
| TASK-2 | Research official NFL data sources (injuries, rosters, depth charts, schedules) | done | session-arena-a7c0f9c5-fl1 | docs/sources.md | nfl.com/injuries/, nfl.com/standings/, nfl.com/teams/{team}/roster (all verified via fetch_page) | n/a |
| TASK-3 | NFL lines origination strategy research (single bets, parlays, player-prop combos, validation gates, correlation values, leaderboard design) | done | session-arena-a7c0f9c5-fl1 | data/strategies.csv, data/correlations.csv | Analytical (not official NFL source); flagged unverified where applicable | n/a |
| TASK-4 | Injury & roster deficiency tracking data (starters vs backups, 2nd/3rd/4th string replacements, offense & defense) | done | session-arena-a7c0f9c5-fl1 | data/injuries.csv, data/rosters.csv | nfl.com/injuries/ (Verified), nfl.com/teams/{team}/roster (roster verified; depth order unverified) | Depth-chart order not rendered on roster page; flagged unverified |
| TASK-5 | Executive summary | unclaimed | session-arena-a7c0f9c5-fl1 | docs/executive-summary.md | n/a | n/a |
| TASK-6 | GitHub Pages site: clean landing page + category subpages, dashboard-style UI, tables with entries/findings/analysis, source links on every row | done | session-arena-a7c0f9c5-fl1 | index.html, injuries.html, depth-charts.html, standings.html, strategies.html, leaderboard.html, executive-summary.html, flagged-review.html, sources.html, assets/css/style.css, assets/js/main.js | n/a | sources.html title tag fixed (was invalid) |
| TASK-7 | Line-by-line verification: every table row must have an official source link or be left blank + flagged unverified | in progress | session-arena-a7c0f9c5-fl1 | all data files + site pages | nfl.com/injuries/, nfl.com/standings/, nfl.com/teams/{team}/roster | n/a |
| TASK-8 | Flagged for Review page (unverified items + irregularities with source links) | unclaimed | session-arena-a7c0f9c5-fl1 | flagged-review.html | n/a | n/a |
| TASK-9 | Integration: merge branches, re-verify combined data, confirm site builds with no broken links, create PR to main, merge, confirm GitHub Pages deploy, record PR link + merge result here | unclaimed | session-arena-a7c0f9c5-fl1 | all | n/a | n/a |

## Rules (from project brief)

- Work on the current branch only; no renaming; no other branches.
- Claim a task by writing your session ID and file scope here, then commit and push that claim immediately.
- Never start a task another session has claimed.
- Keep scopes non-overlapping; if a task requires changing a file owned by another session, log the request here instead of editing it.
- Make small, frequent commits; run `git pull --rebase` before every push.
- On merge conflict: stop, resolve without discarding the other session's work, log what happened.
- A session claim idle > 60 minutes may be taken over by another session; note the handoff here.
- Never mark anything verified without checking against an official source; link that source.
- Shared outputs (table data, index, navigation) are changed only by the final integration session (TASK-9).
- Flagged irregularities and unverified items do not block the merge; publish them on the "Flagged for Review" page.
- Do not merge a broken site.

## Change log

- 2026-11-14: Created COORDINATION.md; claimed TASK-1. Repo contained only README.md ("# FL1").
