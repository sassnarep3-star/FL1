# COORDINATION — Shared Task Board

> Read this **before** starting. Claim a task by writing your session ID and file scope, then commit
> and push that claim immediately. Never start a task another session has claimed.

**Repository:** `sassnarep3-star/FL1`
**GitHub Pages:** https://sassnarep3-star.github.io/FL1/ — source `main`, path `/`, legacy build
**Last updated:** 2026-11-14 (UTC) — reconciliations R1 (PR #1), R2 (PR #2) and R3 (PR #4) recorded below

> **Which board is authoritative?** This file. The board below is maintained by the session that owns the
> consolidating build at the repo root (`arena/ab4e9b05-fl1`). Earlier boards from the other two sessions are
> kept verbatim further down so their records are not lost. If your session's board is not the one at the top,
> **add your tasks to the top board** rather than replacing it.


### Earlier board state, preserved from session C's PR #4

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

---

---

## ⚠️ CONFLICT RECORD — three sessions merged to `main` in parallel

<<<<<<< HEAD
On 2026-11-14 **three** sessions built a site from the same empty repo and all three merged toward `main`.
This section records both reconciliations.

### Third session: `arena/a7c0f9c5-fl1` (PR #2, merged as `42b06f5`)

It added `depth-charts.html`, `leaderboard.html`, `assets/` and five CSVs under `data/`, including its own
independent transcription of the same Week 10 injury report.

**Preserved verbatim in [`archive/v2/`](archive/v2/)**, with a README explaining what it is and how it maps
to the live pages. Its repo-root pages now carry this build.

**It also produced a real verification win.** Comparing its 161 injury rows against this repo's 345-row
capture: every one of its 161 rows is also in this capture, 156 match field-for-field, and the 5 that differ
are players with two listed body parts where its comma-delimited CSV shifted the second body part into the
practice and game-status columns. So the two independent transcriptions agree, and the disagreement is a
formatting bug rather than a data dispute. Recorded as **flag F15** and as a row in `data/verification.tsv`.
Its `data/correlations.csv` carried numeric correlation estimates self-labelled "Unverified — not from an
official source"; those are preserved in the archive but deliberately **not** published, because this site's
rule is that correlation is computed from joint observations or left blank.

### First session: `arena/89c32e23-fl1` (PR #1, merged as `7c7ae6a`)

It built a plan-level site at the same root paths.

| | Session A | Session B (this one) |
|---|---|---|
| Branch | `arena/89c32e23-fl1` | `arena/ab4e9b05-fl1` |
| PR | #1 (`7c7ae6a`) | #3 (this build) |
| Files | `index.html`, `executive-summary.html`, `suggestions.html`, `injuries.html`, `flagged-review.html`, `nfl-strategies.html`, `css/style.css`, `js/app.js` | 14 pages at repo root under its own navigation, `assets/`, `data/`, `raw/`, `tools/`, `docs/` |
| Player-level injury data | no — its own board records "player values not yet pulled from live report" | yes — 345 rows, 28 clubs, verified line by line |

**Resolution (session B, integration):**

1. **No work was discarded.** Every file from session A is preserved verbatim in
   [`archive/v1/`](archive/v1/) — the six HTML pages, `css/style.css` and `js/app.js` — together with a
   note explaining what it is and how to view it.
2. The repo-root paths that both sessions used (`index.html`, `executive-summary.html`, `injuries.html`,
   `suggestions.html`) now carry session B's build, because a GitHub Pages site has one root and one
   `index.html`. Session B's version is a superset: it includes all of session A's sections plus the
   verified player-level data, the source registry, the eight validation gates and the verification log.
3. Nothing from session A was silently dropped — `flagged-review.html` maps onto
   [`flagged.html`](flagged.html) (15 items), `nfl-strategies.html` maps onto
   [`strategies.html`](strategies.html) + [`validation.html`](validation.html), and `suggestions.html`
   is retained at the same path with session B's expanded register.
4. The merge conflict was resolved **in favour of the superset** and that decision is logged here
   rather than left implicit.

**If you are session A and disagree:** the correct move is to open a PR that restores whichever specific
v1 page you want at its old path, and to update the site navigation in the same PR. Do not delete
`archive/v1/`.

**Lesson for future sessions (log it in your own claim row):** check `origin/main` *and* open PRs before
claiming a repo-root page, and re-check immediately before every push. At the start of this session
`git log origin/main` showed only the initial commit. Session A's merge landed during the build, and
session C's landed while this PR was open. Two `git fetch origin` calls would have caught both, and a
third session still would have needed the same reconciliation.

**Standing rule adopted after this incident:** this repository now has a single consolidating build at the
repo root. A new session should **extend** it — add a page under a new filename and add it to `NAV` in
`tools/site.py` — rather than writing a second `index.html`. Superseded sites belong in `archive/`.

---

## Rules in force for every session

1. Work only on your own branch. Never push to another session's branch.
2. Edit only files inside your claimed scope. If you need someone else's file, log a request below.
3. `git fetch origin && git log origin/main` **before** claiming, and again before your first push.
4. `git pull --rebase` before every push. Make small, frequent commits.
5. Shared outputs — `index.html`, `assets/js/nav`-equivalent navigation, `data/*` registries — are changed
   only by the final integration session, after all other tasks reach `done` or `needs review`.
6. Never mark something verified without an official source link in `data/sources.tsv`. If a value cannot
   be confirmed, leave the cell **blank** and flag it on `flagged.html`.
7. `needs review` means published on *Flagged for Review* and does **not** block a merge.
8. Broken build or broken links block a merge. Flagged items never do.
9. A claim 60+ minutes old with no commits may be taken over; note the handoff in the Log.

### Sandbox reality check

Outbound HTTP from this environment is allow-listed to package registries only. `curl https://www.nfl.com/...`
returns exit code `000`. Use a page-fetch tool. **Do not report a URL as dead based on `curl`.**

---

## Status key

`unclaimed` · `in progress` · `done` · `needs review`

---

## Task board — session B (`arena/ab4e9b05-fl1`)

| ID | Task | Owner | Files | Status |
|---|---|---|---|---|
| T00 | Repo audit, branch hygiene, coordination board | `ab4e9b05` | `COORDINATION.md` | done |
| T01 | Requirements register | `ab4e9b05` | `data/requirements.json`, `requirements.html` | done |
| T02 | Source registry + verification of every cited URL | `ab4e9b05` | `data/sources.tsv`, `sources.html` | done |
| T03 | Official injury-report capture, Week 10 2026 | `ab4e9b05` | `raw/injuries-week10-2026.md`, `data/injuries.tsv`, `injuries.html` | done |
| T04 | Standings, schedule, tiebreakers | `ab4e9b05` | `data/standings.tsv`, `data/schedule.tsv`, `standings.html` | done |
| T05 | Backup-depth model (observed vs derived) | `ab4e9b05` | `data/depth-kc.tsv`, `data/depth-aliases.tsv`, `depth.html` | done |
| T06 | Open-questions register | `ab4e9b05` | `data/questions.json`, `questions.html` | done |
| T07 | Suggestions register with options and recommendations | `ab4e9b05` | `data/suggestions.json`, `suggestions.html` | done |
| T08 | Line-origination specification | `ab4e9b05` | `line-origination.html` | done |
| T09 | Leaderboard, validation gates, correlation method | `ab4e9b05` | `data/strategies.json`, `strategies.html`, `validation.html` | done |
| T10 | Executive summary | `ab4e9b05` | `executive-summary.html`, `docs/EXECUTIVE_SUMMARY.md` | done |
| T11 | Site shell, CSS, build + link check | `ab4e9b05` | `index.html`, `assets/**`, `tools/**` | done |
| T12 | Flagged for Review (15 items) | `ab4e9b05` | `data/flags.json`, `flagged.html` | done |
| T13 | Verification log + reproducibility | `ab4e9b05` | `data/verification.tsv`, `verification.html`, `docs/METHOD.md` | done |
| T14 | **Integration**: reconcile parallel session, re-verify, build, link check, publish | `ab4e9b05` | all (merge owner) | done |
| T15 | Second reconciliation (session C) + independent cross-transcription check (F15) | `ab4e9b05` | `archive/v2/`, `data/flags.json`, `data/verification.tsv` | done |

## Task board — session A (`arena/89c32e23-fl1`), preserved

| # | Task | Status | Owner | File scope | Notes |
|---|---|---|---|---|---|
| 1 | Create COORDINATION.md task board | done | arena-89c32e23-fl1 | COORDINATION.md | preserved |
| 2 | Repo review line-by-line | done | arena-89c32e23-fl1 | all files | README.md held only "# FL1" |
| 3 | Executive summary | done | arena-89c32e23-fl1 | executive-summary.html | v1 archived |
| 4 | Suggestions & decision review | done | arena-89c32e23-fl1 | suggestions.html | v1 archived |
| 5 | Strategies, gates, correlation, leaderboard | done | arena-89c32e23-fl1 | nfl-strategies.html | v1 archived |
| 6 | Injury & deficiency tracking | done | arena-89c32e23-fl1 | injuries.html | noted: player values not yet pulled |
| 7 | Site creation | done | arena-89c32e23-fl1 | *.html, css/, js/ | v1 archived |
| 8 | Flagged-for-review page | done | arena-89c32e23-fl1 | flagged-review.html | v1 archived |
| 9 | Integration | done | arena-89c32e23-fl1 | all | merged as PR #1 |
| 10 | Pages publish + PR + merge | done | arena-89c32e23-fl1 | repo / Pages | PR #1 merged, commit `7c7ae6a` |

---

## Log

| When (UTC) | Session | Entry |
|---|---|---|
| 2026-11-14 | `ab4e9b05` | Repo audited. Branch `arena/ab4e9b05-fl1` from `e001e0a`; repo held only a 5-byte `README.md`. `git log origin/main` showed one commit. Pages already configured on `main` root, status `built`. |
| 2026-11-14 | `ab4e9b05` | Verified `https://www.nfl.com/injuries/` serves live official Week 10 / 2026 data with practice and game status. |
| 2026-11-14 | `ab4e9b05` | Three official URLs returned HTTP 404: the 2017 injury-policy PDF, `nfl.com/depth-charts/`, and the Football Operations injury page. Recorded as NOT VERIFIED; no policy text quoted anywhere. |
| 2026-11-14 | `ab4e9b05` | Two cross-source contradictions found on Rams defenders (Myles Garrett attribution, Aaron Donald participation vs active profile). Published verbatim, flagged F04/F05, no resolution applied. |
| 2026-11-14 | `ab4e9b05` | T01–T13 complete. `verify_injuries.py` passes 345/345 rows; `checklinks.py` passes 14 pages. |
| 2026-11-14 | `ab4e9b05` | **Conflict:** `gh pr merge 3` failed — `main` had moved to `7c7ae6a` via session A's PR #1, which built a parallel site (worktree was not stale; `git log` had simply been captured before the merge landed). |
| 2026-11-14 | `ab4e9b05` | Merged `origin/main`. Five add/add conflicts (`COORDINATION.md`, `index.html`, `executive-summary.html`, `injuries.html`, `suggestions.html`). Resolved in favour of the verified superset; session A's files preserved verbatim in `archive/v1/`. Nothing deleted. |
| 2026-11-14 | `ab4e9b05` | Re-ran `verify_injuries.py` and `checklinks.py` on the merged tree before pushing. |
| 2026-11-14 | `ab4e9b05` | `gh pr merge 3` failed again: `main` had moved to `42b06f5` via session C's PR #2. Merged `origin/main` again; conflicts in `sources.html`, `standings.html`, `strategies.html` resolved in favour of this build. Session C's files preserved verbatim in `archive/v2/`; nothing deleted. |
| 2026-11-14 | `ab4e9b05` | Cross-checked session C's 161-row injury CSV against this repo's 345-row capture: 161/161 rows present in both, 156 identical, 5 differ only where a comma inside `Ankle, Knee`-style values shifted their CSV columns. Recorded as flag F15. |
| 2026-11-14 | `ab4e9b05` | Re-verified on the final merged tree: `verify_injuries.py` 345/345 PASS, `checklinks.py` 14 pages PASS, `build.py` clean. |
| 2026-11-14 | `ab4e9b05` | **R3:** `main` moved again to `557ffc3` via session C's PR #4 (documentation only). Merged; single conflict in `COORDINATION.md`, resolved by keeping this board on top and preserving session C's board and integration-completion record verbatim below. No files discarded. |

---

## Requests

_None outstanding._

## Open items for review (published, non-blocking)

All 15 items on [`flagged.html`](flagged.html). Every unverifiable value in this repo is left blank there
with the reason and the source that was attempted.
=======
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

---

## Session `arena/3f677e8a-fl1` — board preserved verbatim (merged into `main` on 2026-11-14)

> This session branched from `main` @ `e001e0a`, i.e. **before** PRs #1–#5 landed. It discovered
> the divergence when `git pull --rebase` tried to replay its commits onto `d5e9cc0`. Per the
> conflict rule in the brief, it stopped, and reconciled by **merging `main` in** rather than
> force-pushing, so no other session's work was discarded. Its independent captures are kept
> below and were cross-checked against the consolidated `data/` files (results recorded in
> `data/verification.tsv`).

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


### Reconciliation notes for this session

- **Standings:** an independent recount of W/L/T + PF + PA computed from this session's
  137-game results file matches `data/standings.tsv` for all 32 clubs — **0 mismatches**.
  This also settles the snapshot date: with the Week 10 TNF row included the numbers match
  exactly, with it excluded NYG and WAS are off. **The standings snapshot includes
  Thursday 2026-11-12 (WAS 24 @ NYG 21).**
- **Abbreviations:** this session used `AZ` for Arizona; the consolidated site uses the official
  `ARI`. Its capture was normalised to `ARI` on integration. No data lost.
- **Depth charts:** the consolidated site only carried Kansas City (`data/depth-kc.tsv`).
  This session transcribed **30 of 32** clubs and contributed them as `data/depth.tsv`.
  Houston is **not** included — its club page renders the depth chart as an image, so there is
  nothing machine-readable to transcribe without inferring. Flagged, not filled in.

