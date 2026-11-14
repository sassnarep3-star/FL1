# COORDINATION.md — Shared Task Board

Repo: `sassnarep3-star/FL1`
Purpose: NFL requirements / decision-support / line-generation research site.

## Branch policy for this session (read first)

This session runs on the Arena-managed branch **`arena/3f677e8a-fl1`** (branched from
`main` @ `e001e0a24c2ca5a432f6bd39cea3b5e6fcc035a2`). Arena tracks this session by that
branch, so **this session will not create or push any other branch**, including
`session-<id>/<task>` worktrees. Instead of branch-per-task isolation, this session uses
**file-scope isolation**: every task below claims an explicit, non-overlapping set of files,
and no task may edit files outside its claimed scope. If another session is live, claim an
unclaimed task (or a sub-scope) below, commit and push the claim immediately, and respect
the file scopes already claimed here.

If a second session is running concurrently and wants branch-per-task isolation, it may
create `session-<id>/<task>` branches; in that case it must do the final integration merge
itself, because this session can only push `arena/3f677e8a-fl1`.

## Session registry

| Session ID | Branch | Started | Status | Notes |
|---|---|---|---|---|
| `session-3f677e8a` | `arena/3f677e8a-fl1` | 2026-11-14 | active | Single session observed. Performing all tasks incl. final integration. |

## Task board

Status values: `unclaimed` · `in progress` · `done` · `needs review` · `blocked`
(`needs review` = published on the Flagged for Review page; does **not** block anything.)

| # | Task | Status | Owner | File scope (claimed) |
|---|---|---|---|---|
| T01 | Repo audit — line-by-line review of existing repo contents | done | `session-3f677e8a` | `REPO_AUDIT.md`, `README.md` |
| T02 | Coordination board + branch/scope protocol | done | `session-3f677e8a` | `COORDINATION.md` |
| T03 | Source registry (official-only, tiered, with retrieval dates) | in progress | `session-3f677e8a` | `data/sources.json` |
| T04 | Official NFL standings + schedule scrape (2026 season) | in progress | `session-3f677e8a` | `data/standings.json`, `data/schedule.json` |
| T05 | Official NFL injury report (Week 10, 2026) | in progress | `session-3f677e8a` | `data/injuries.json` |
| T06 | Official team depth charts — starter / 2nd / 3rd / 4th string | in progress | `session-3f677e8a` | `data/depth_charts.json` |
| T07 | Market/consensus lines capture (external book pages) | in progress | `session-3f677e8a` | `data/market_lines.json` |
| T08 | Historical dataset acquisition for backtesting (nflverse via GitHub) | in progress | `session-3f677e8a` | `tools/fetch_data.py`, `data_raw/` (git-ignored) |
| T09 | Requirements register (full list of requirements) | unclaimed→in progress | `session-3f677e8a` | `data/requirements.json` |
| T10 | Suggestions / decision register (reviewable, choose-before-implement) | unclaimed→in progress | `session-3f677e8a` | `data/suggestions.json` |
| T11 | Open questions: info we have / don't have / how to discover | unclaimed→in progress | `session-3f677e8a` | `data/open_questions.json` |
| T12 | Own-line generation model spec + current-week model output | unclaimed→in progress | `session-3f677e8a` | `data/model_lines.json`, `MODEL.md` |
| T13 | Strategy leaderboard: single bets, parlays, prop combos | unclaimed→in progress | `session-3f677e8a` | `data/strategies.json` |
| T14 | Validation gates + correlation values + skill-vs-luck statistics | unclaimed→in progress | `session-3f677e8a` | `data/validation.json`, `data/correlations.json`, `VALIDATION.md` |
| T15 | Executive summary | unclaimed→in progress | `session-3f677e8a` | `data/exec_summary.json`, `EXECUTIVE_SUMMARY.md` |
| T16 | Site build (landing + category subpages, dashboard UI, tables) | unclaimed→in progress | `session-3f677e8a` | `assets/`, `tools/build_site.py`, `*.html` |
| T17 | Verification pass — every row link-checked; unconfirmed → blank + flagged | unclaimed | `session-3f677e8a` | `VERIFICATION.md`, `tools/verify.py` |
| T18 | Flagged-for-Review page (irregularities + unverified items w/ source links) | unclaimed | `session-3f677e8a` | `flagged.html` |
| T19 | Final integration: merge, re-verify, link check, publish Pages | unclaimed | `session-3f677e8a` | `*` (integration only after T01–T18 done) |
| T20 | PR → main, merge without waiting, confirm Pages deploy | unclaimed | `session-3f677e8a` | PR only |

## Integration rules (from the task brief)

* Shared outputs — the table data in `data/` and the site's `index.html` + navigation —
  are merged/changed only by the final integration task (T19), after T01–T18 are done.
* Small, frequent commits; `git pull --rebase` before every push.
* On merge conflict: stop, resolve without discarding the other session's work, log it below.
* Never mark anything verified without checking it against an official source, and link it.
* Stale-claim rule: a claim older than 60 minutes with no commits may be taken over; note
  the handoff in the log.

## Change log

| Timestamp (UTC) | Session | Entry |
|---|---|---|
| 2026-11-14T00:00Z | `session-3f677e8a` | Board created. Repo found empty (single 5-byte `README.md`, commit `e001e0a`). Branch-per-task isolation replaced by file-scope isolation due to Arena single-branch policy. |
