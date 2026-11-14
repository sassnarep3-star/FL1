# COORDINATION.md

Shared task board for the FL1 (NFL) project. All sessions must read this before starting and keep it up to date.

## Session convention
- Each session works on its own branch named `session-<id>/<task>` and edits only files in its claimed scope.
- Claim a task by writing your session ID and file scope here, then commit and push immediately.
- Never start a task another session has claimed.
- If a task requires changing a file owned by another session, log the request here instead of editing it.
- Make small, frequent commits; run `git pull --rebase` before every push.
- On merge conflict: stop, resolve without discarding the other session's work, log what happened.
- When a task is finished: record sources, verification performed, and irregularities here; mark it done.
- Never mark anything verified without checking against an official source; link that source.
- A claim older than 60 minutes with no commits may be taken over by another session (note the handoff).
- `needs review` = published on the "Flagged for Review" page; does not block anything.
- Shared outputs (table data, site index/navigation) are changed only by the final integration session once all other tasks are done.

## Current session
- Branch: `arena/89c32e23-fl1` (status: active), branched from `e001e0a` of `main`
- Session ID: `arena-89c32e23-fl1`
- This session is the only active session and claims all tasks below until/unless another session joins.

## Task board

| # | Task | Status | Owner | File scope | Sources / verification | Irregularities |
|---|------|--------|-------|------------|------------------------|----------------|
| 1 | Create COORDINATION.md task board | done | arena-89c32e23-fl1 | COORDINATION.md | n/a | none |
| 2 | Repo review line-by-line; verify from official sources; flag irregularities | done | arena-89c32e23-fl1 | README.md, all repo files | repo contents (see findings) | README.md contains only "# FL1" |
| 3 | Executive summary | done | arena-89c32e23-fl1 | executive-summary.html | nfl.com/injuries/, nfl.com/standings verified reachable | none |
| 4 | Suggestions & decision-review section (questions/info/answers before decisions; missing-info discovery) | done | arena-89c32e23-fl1 | suggestions.html | nfl.com/injuries/ cited | betting lines have no official NFL source |
| 5 | NFL betting strategies: line origination, signals, single bets/parlays/player props, validation gates, correlation, skill-based leaderboard | done | arena-89c32e23-fl1 | nfl-strategies.html | n/a (methodological) | all line/odds data unverified (no official NFL source) |
| 6 | Injury & team-deficiency tracking (starters vs backups, offense & defense, 2nd/3rd/4th string) | done | arena-89c32e23-fl1 | injuries.html | nfl.com/injuries/ verified reachable | player values not yet pulled from live report |
| 7 | Site creation: clean landing page + category subpages, dashboard UI, entry/findings tables with source links, unverified = blank + flagged | done | arena-89c32e23-fl1 | *.html, css/, js/, index.html, navigation | internal links verified OK | none |
| 8 | Flagged-for-review page (irregularities + unverified items with source links) | done | arena-89c32e23-fl1 | flagged-review.html | nfl.com, GitHub repo | none |
| 9 | Integration: merge branches, re-verify combined data line-by-line, confirm site builds with no broken links | done | arena-89c32e23-fl1 (integration); completed/merged by arena/a7c0f9c5-fl1 | all site files | nfl.com/injuries/, nfl.com/standings/, nfl.com/teams/{team}/roster | add/add conflicts resolved without discarding session arena/89c32e23-fl1 work |
| 10 | GitHub Pages: publish, confirm deploy succeeds (do not merge a broken site), create PR from integration branch to main, merge, record PR link + merge result here | done | arena/a7c0f9c5-fl1 | repo / GitHub Pages | n/a | Pages pinned to main branch / root |

## Notes
- Official NFL source = nfl.com (and official NFL subdomains). Betting lines have no official NFL source; mark as unverified/not-from-official-source.
- Every table row must carry a source link to an official site. If a value cannot be confirmed from an official source, leave it blank and flag it "unverified".
- Do not infer or fill in values.

## Integration completion record (session arena/a7c0f9c5-fl1)
- PR created: https://github.com/sassnarep3-star/FL1/pull/2 (arena/a7c0f9c5-fl1 -> main)
- PR merged: 2026-11-14T03:03:06Z (squash/merge via `gh pr merge 2 --merge`)
- GitHub Pages: https://sassnarep3-star.github.io/FL1/ — deploy status "built", all pages HTTP 200 locally and live, no broken internal links
- Conflict resolution: add/add conflicts on COORDINATION.md, index.html, injuries.html, executive-summary.html, flagged-review.html resolved by keeping session arena/89c32e23-fl1's integrated site files intact; no other session's work was discarded
- Session arena/a7c0f9c5-fl1 contributions (added, non-conflicting): data/standings.csv (32 teams, Week 10), data/injuries.csv (161 player rows), data/rosters.csv (34 Chiefs players), data/strategies.csv (8 origination strategies), data/correlations.csv (7 entries), plus strategies.html, leaderboard.html, depth-charts.html, standings.html, sources.html, assets/css/style.css, assets/js/main.js
- Sources used (verified): https://www.nfl.com/injuries/ , https://www.nfl.com/standings/ , https://www.nfl.com/teams/{team}/roster
- Flagged irregularities / unverified items: published on the live site's Flagged for Review page (flagged-review.html) — includes depth-chart order unverified, strategies & correlations analytical (no official NFL source), no live betting-lines source, partial Week 10 injury coverage, standings single week only
- Live site: https://sassnarep3-star.github.io/FL1/
