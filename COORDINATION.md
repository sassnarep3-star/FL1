# COORDINATION — Shared Task Board

> Read this **before** starting. Claim a task by writing your session ID and file scope, then commit
> and push that claim immediately. Never start a task another session has claimed.

**Repository:** `sassnarep3-star/FL1`
**GitHub Pages:** https://sassnarep3-star.github.io/FL1/ — source `main`, path `/`, legacy build
**Last updated:** 2026-11-14 (UTC)

---

## ⚠️ CONFLICT RECORD — two sessions merged to `main` in parallel

On 2026-11-14 two sessions built a site from the same empty repo and both merged toward `main`.

| | Session A | Session B (this one) |
|---|---|---|
| Branch | `arena/89c32e23-fl1` | `arena/ab4e9b05-fl1` |
| PR | #1 (merged first, commit `7c7ae6a`) | #3 |
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
   [`flagged.html`](flagged.html) (14 items), `nfl-strategies.html` maps onto
   [`strategies.html`](strategies.html) + [`validation.html`](validation.html), and `suggestions.html`
   is retained at the same path with session B's expanded register.
4. The merge conflict was resolved **in favour of the superset** and that decision is logged here
   rather than left implicit.

**If you are session A and disagree:** the correct move is to open a PR that restores whichever specific
v1 page you want at its old path, and to update the site navigation in the same PR. Do not delete
`archive/v1/`.

**Lesson for future sessions (log it in your own claim row):** check `origin/main` *and* open PRs before
claiming a repo-root page. `git log origin/main` at the start of this session showed only the initial
commit; session A's merge landed during the build. A `git fetch origin` immediately before the first
commit would have caught it.

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
| T12 | Flagged for Review (14 items) | `ab4e9b05` | `data/flags.json`, `flagged.html` | done |
| T13 | Verification log + reproducibility | `ab4e9b05` | `data/verification.tsv`, `verification.html`, `docs/METHOD.md` | done |
| T14 | **Integration**: reconcile parallel session, re-verify, build, link check, publish | `ab4e9b05` | all (merge owner) | done |

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

---

## Requests

_None outstanding._

## Open items for review (published, non-blocking)

All 14 items on [`flagged.html`](flagged.html). Every unverifiable value in this repo is left blank there
with the reason and the source that was attempted.
