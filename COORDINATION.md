# COORDINATION — Shared Task Board

Repo: `sassnix321/FL1` · Purpose: collect, organize, and analyze the requirements for an
NFL line-origination / signal-generation decision system, published as a GitHub Pages dashboard.

**Rules of the board (read before touching anything):**

1. Claim a task by writing your session ID + file scope in the row, then commit and push that claim
   **immediately** (before any other work).
2. Never start a task another session has claimed. Work only inside your claimed scope.
3. Work on a branch named `session-<id>/<task>`. Keep scopes non-overlapping.
4. If a task needs a file owned by another session, log a request in **Change Requests** below —
   do not edit the file.
5. Small, frequent commits. `git pull --rebase` before every push.
6. A status of `needs review` = the item is published on the **Flagged for Review** page and does
   **not** block anything.
7. Stale claims (no commit for > 60 min) may be taken over by another session; record the handoff
   in **Log**.
8. Shared outputs (`data/*.json`, `docs/index.html`, `docs/assets/nav.js`, this file's board rows)
   are integrated by the **final integration session only**.
9. Nothing is marked `verified` unless it was checked against an official source and the source URL
   is recorded in the row or in `sources.json`. Values that cannot be confirmed are left **blank**
   and flagged, never inferred.

**Status vocabulary:** `unclaimed` · `in progress` · `done` · `needs review`

---

## Board

| # | Task | Status | Owner (session ID) | File scope | Notes |
|---|------|--------|--------------------|------------|-------|
| 0 | Repo audit (line-by-line review of what exists) | in progress | `sess-c80caab4` | `COORDINATION.md`, `REPO_AUDIT.md` | HEAD `e001e0a24c2ca5a432f6bd39cea3b5e6fcc035a2` ("Initial commit"). Repo contained exactly 1 tracked file: `README.md` (6 bytes, text `# FL1`). No code, no data, no CI, no Pages config. Nothing to verify ⇒ all data work is greenfield. See `REPO_AUDIT.md`. |
| 1 | Sources register (official-source allowlist + verification ledger) | in progress | `sess-c80caab4` | `data/sources.json` | 30+ primary sources, each with access date and what it proves. |
| 2 | Requirements register + full requirements list | in progress | `sess-c80caab4` | `data/requirements.json` | R-01…R-40 derived verbatim from the brief; each with owner, status, evidence. |
| 3 | Open-questions / known-unknowns / missing-information register | in progress | `sess-c80caab4` | `data/questions.json` | Q-01…Q-24: question, why it blocks, what we know, what we lack, where to get it, default if unanswered. |
| 4 | Suggestions register (review before implementing) | in progress | `sess-c80caab4` | `data/suggestions.json` | S-01…S-24 with impact/effort/risk/dependency + decision field left open for the owner. |
| 5 | Line-origination model spec (totals-first, market-neutral) | in progress | `sess-c80caab4` | `docs/methodology.html`, `data/models.json` | Equations, priors, inputs, release cadence, no fabricated coefficients. |
| 6 | Validation gates (anti-luck / skill isolation) | in progress | `sess-c80caab4` | `docs/validation.html` | G-1…G-12 with pass thresholds; multiple-comparison controls; CLV; bootstrap. |
| 7 | Correlation & parlay math | in progress | `sess-c80caab4` | `docs/correlation.html` | ρ definitions, pay-table correction, prop-combo rules, limits. |
| 8 | Injury / availability / depth-chart deficiency tracking spec | in progress | `sess-c80caab4` | `docs/injuries.html`, `data/injury_model.json` | Official NFL injury-report cadence + WR-DB/QB availability tiers, backup-deficiency scoring, snap-share proxy. |
| 9 | Leaderboard competition + rewards design | in progress | `sess-c80caab4` | `docs/leaderboard.html` | Scoring that ranks on luck-adjusted metrics; anti-gaming rules; prize governance & legal caveats. |
| 10 | Executive summary | in progress | `sess-c80caab4` | `docs/summary.html`, `EXECUTIVE_SUMMARY.md` | One page for the owner: what exists, what's missing, first 5 moves, hard risks. |
| 11 | GitHub Pages static site (landing + category subpages + tables) | in progress | `sess-c80caab4` | `docs/**` (except `docs/index.html` nav wiring, owned here), `site/build.py`, `site/styles.css` | Built from `data/*.json`; every table row carries a source column. |
| 12 | Build + link-integrity verification (no broken links, no dead tables) | in progress | `sess-c80caab4` | `site/verify.py` | Local build → crawl every `href` → fail on any missing target or missing source link. |
| 13 | Final integration + PR to `main` + Pages deploy confirmation | in progress | `sess-c80caab4` | `docs/index.html`, this file | Then publish. |

## Change Requests

| # | Requested by | Needs | Owner of target | Status |
|---|--------------|-------|-----------------|--------|
| CR-1 | `sess-c80caab4` | Repo settings: enable GitHub Pages, source = `main` / `/docs`. Not a file change; done via `gh api` in T13. | repo owner | pending → see Log |

## Irregularities & Flags (published on the "Flagged for Review" page)

| # | Flag | Severity | Evidence |
|---|------|----------|----------|
| F-1 | Repo was empty at claim time (single 6-byte README) although the brief reads as if a populated data project existed. No prior ingestion, no schema, no tests. | High — scope assumption wrong | `git show e001e0a --stat` |
| F-2 | No `LICENSE` file. Default copyright applies; blocks any reuse or open collaboration. | Medium | `ls /home/user/FL1` |
| F-3 | No `.gitignore`; build output would otherwise be committed by accident. | Low | — |
| F-4 | GitHub Pages not configured (`GET /repos/…/pages` → 404 at claim time). | Medium | `gh api repos/sassnix321/FL1/pages` |
| F-5 | Zero live NFL data exists in-repo. Any number a future session writes without a source URL must be flagged unverified, per rule 9. | High — hallucination risk | brief |
| F-6 | Repo owner identity `sassnix321/FL1` vs. git author `sassnix321-star <sassnix321@gmail.com>` — cosmetic mismatch, worth confirming no stray fork. | Low | `git log -1 --format='%an %ae'` |

## Log

| Time (UTC) | Session | Action |
|------------|---------|--------|
| 2026-11-13 | `sess-c80caab4` | Board created (did not exist). Claimed T0–T13; no other sessions present (`git branch -a` showed only `main` + this branch). |
| 2026-11-13 | `sess-c80caab4` | T0 repo audit complete → `REPO_AUDIT.md`. Findings F-1…F-6 logged. |
