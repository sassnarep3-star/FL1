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
| 9 | Integration: merge branches, re-verify combined data line-by-line, confirm site builds with no broken links | in progress | arena-89c32e23-fl1 | all site files | official sources per row | none yet |
| 10 | GitHub Pages: publish, confirm deploy succeeds (do not merge a broken site), create PR from integration branch to main, merge, record PR link + merge result here | in progress | arena-89c32e23-fl1 | repo / GitHub Pages | n/a | Pages pinned to main branch / root (cannot retarget via API: 403) |

## Notes
- Official NFL source = nfl.com (and official NFL subdomains). Betting lines have no official NFL source; mark as unverified/not-from-official-source.
- Every table row must carry a source link to an official site. If a value cannot be confirmed from an official source, leave it blank and flag it "unverified".
- Do not infer or fill in values.
