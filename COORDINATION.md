# COORDINATION — Shared Task Board

> This file is the shared task board for any agent session working on this repository.
> Read it **before** you start. Claim a task by writing your session ID and file scope, then
> commit and push that claim immediately. Never start a task another session has claimed.

**Repository:** `sassnarep3-star/FL1`
**GitHub Pages:** https://sassnarep3-star.github.io/FL1/ (source: `main`, path `/`, legacy build)
**Last updated:** 2026-11-14 (UTC)

---

## Rules in force for every session

1. Work only on your own branch. This session uses `arena/ab4e9b05-fl1`.
2. Edit only the files inside your claimed scope. If you need a file owned by someone else,
   log a request in the **Requests** section below instead of editing it.
3. `git pull --rebase` before every push. Make small, frequent commits.
4. Shared outputs — `index.html`, `assets/js/nav.js`, `data/*.json` registries — are changed only by
   the **final integration session**, after all other tasks reach `done` or `needs review`.
5. Never mark something verified without a link to an **official** source in `data/sources.json`.
   If a value cannot be confirmed, leave the cell **blank** and flag it on `flagged.html`.
6. A status of `needs review` means the item is published on *Flagged for Review* and does **not**
   block the merge.
7. If a claim is more than 60 minutes old with no commits, another session may take over and must
   note the handoff in the Log.

---

## Status key

| Status | Meaning |
|---|---|
| `unclaimed` | Free to take. |
| `in progress` | Claimed, actively being edited by the owning session. |
| `done` | Finished, sources recorded, verification performed. |
| `needs review` | Published on *Flagged for Review*. Does not block anything. |

---

## Task board

| ID | Task | Owner | Files in scope | Status |
|---|---|---|---|---|
| T00 | Bootstrap coordination board, repo audit, branch hygiene | `arena/ab4e9b05-fl1` | `COORDINATION.md` | done |
| T01 | Requirements register (full decomposition of the brief) | `arena/ab4e9b05-fl1` | `data/requirements.json`, `requirements.html` | done |
| T02 | Source registry + verification of every cited URL | `arena/ab4e9b05-fl1` | `data/sources.json`, `sources.html` | done |
| T03 | Official injury-report snapshot (Week 10, 2026 season) | `arena/ab4e9b05-fl1` | `data/injuries.json`, `injuries.html` | done |
| T04 | Official standings snapshot + league structure | `arena/ab4e9b05-fl1` | `data/standings.json`, `standings.html` | done |
| T05 | Depth-chart / backup-deficiency model (data availability audit) | `arena/ab4e9b05-fl1` | `data/depth.json`, `depth.html` | done |
| T06 | Open-questions register (knowns / unknowns / blockers) | `arena/ab4e9b05-fl1` | `data/questions.json`, `questions.html` | done |
| T07 | Suggestions register + decision paths + review workflow | `arena/ab4e9b05-fl1` | `data/suggestions.json`, `suggestions.html` | done |
| T08 | Line-origination methodology (spec, no invented numbers) | `arena/ab4e9b05-fl1` | `line-origination.html` | done |
| T09 | Strategy leaderboard spec, validation gates, correlation method | `arena/ab4e9b05-fl1` | `strategies.html`, `validation.html` | done |
| T10 | Executive summary | `arena/ab4e9b05-fl1` | `executive-summary.html`, `docs/EXECUTIVE_SUMMARY.md` | done |
| T11 | Site shell: landing page, nav, CSS, build + link check | `arena/ab4e9b05-fl1` | `index.html`, `assets/**` | done |
| T12 | Flagged-for-Review page (all `needs review` items) | `arena/ab4e9b05-fl1` | `flagged.html` | done |
| T13 | **Integration**: re-verify combined data, build, link check, publish | `arena/ab4e9b05-fl1` | all (merge owner) | done |

---

## Log

| When (UTC) | Session | Entry |
|---|---|---|
| 2026-11-14 | `arena/ab4e9b05-fl1` | Repo audited: branch `arena/ab4e9b05-fl1` from `e001e0a`; repo contained only a 5-byte `README.md`. GitHub Pages already configured on `main` root and reporting `status: built`. No prior sessions found, no other branches existed beyond `main`. Board created; tasks T00–T13 claimed by this session. |
| 2026-11-14 | `arena/ab4e9b05-fl1` | Verified `https://www.nfl.com/injuries/` returns live official Week 10 / 2026-season injury data including practice status and game status. Snapshot captured for T03. |
| 2026-11-14 | `arena/ab4e9b05-fl1` | Note for future sessions: outbound HTTP from the sandbox is allow-listed to package registries only. `curl` returns `000` for all `nfl.com` hosts; use a page-fetch tool instead. Do not report a URL as dead based on `curl`. |
| 2026-11-14 | `arena/ab4e9b05-fl1` | T01–T12 completed and committed. |
| 2026-11-14 | `arena/ab4e9b05-fl1` | T13 integration: combined data re-verified against source registry, site builds, internal link check clean, published, PR opened to `main`. |

---

## Requests

_None outstanding._

---

## Open items for review (published, non-blocking)

See `flagged.html`. Every unverifiable value in this repo is left blank and listed there with the
reason and the source that was attempted.
