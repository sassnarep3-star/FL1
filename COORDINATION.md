# COORDINATION.md — Shared Task Board

Repo: `sassnarep3-star/FL1` · Purpose: collect, organize and analyze NFL data for an
independent line-origination and signal-generation system.

**This file is the only cross-session coordination mechanism. Read it before you touch
anything. Commit your claim before you edit. Keep your file scope non-overlapping.**

---

## Session registry

| Session ID | Branch | Started (UTC) | Last commit (UTC) | Scope summary | Status |
| --- | --- | --- | --- | --- | --- |
| `1220d13c` | `arena/1220d13c-fl1` | 2026-11-14 02:52 | 2026-11-14 03:05 | Full greenfield build: repo review, official-source ingestion + verified data snapshot, origination model, strategy/gate/correlation docs, GitHub Pages site, integration + PR + merge | **IN PROGRESS — also acting as the final integration session** |

> Session `1220d13c` claimed **every** task below on an empty repo (only `README.md`,
> 5 bytes, existed at start). There was no other work in the repository to avoid. If you
> are a new session and your scope overlaps a `DONE` row, do not re-implement it —
> re-verify it and open a request in the Change-request log instead.

---

## Rules of engagement (all sessions)

1. **Claim before editing.** Write your session ID + file scope in the task table, commit
   and push the claim immediately.
2. **Never edit a file owned by another active session.** Log a request in
   *Change-request log* instead.
3. **Branch naming:** `session-<id>/<task>`. Work only inside your claimed scope.
4. `git pull --rebase` before **every** push. Small, frequent commits.
5. On a merge conflict: stop, resolve without discarding the other session's work, and
   record the resolution in *Conflict log*.
6. **Stale claims** (> 60 min old with no commit) may be taken over by any session; note
   the handoff in *Handoff log*.
7. **Shared outputs** — `site/index.html`, `site/**` navigation, `site/data/*`,
   `data/verified/*` — are written only by the final integration session once all other
   tasks are done.
8. **Verification bar:** every published table row carries a link to the source that was
   actually read. Official = `nfl.com` (league) or the club's own domain. Anything else is
   Tier-2/third-party and must be labelled. If a value cannot be confirmed from the
   source, the cell is left **blank** and the row is flagged. Never infer, interpolate, or
   fill from memory.
9. Mark a task `DONE` only with Sources / Verification / Irregularities recorded.

---

## Task board

Statuses: `unclaimed` · `in progress` · `needs review` (published on *Flagged for Review*,
non-blocking) · `done` · `blocked`

| # | Task | Status | Owner | File scope | Sources / verification / irregularities |
| --- | --- | --- | --- | --- | --- |
| T1 | Repo review, line by line, with links | **done** | `1220d13c` | `docs/REPO_REVIEW.md` | Repo at base commit `e001e0a` contained exactly one file, `README.md`, containing only `# FL1`. No code, no data, no CI, no LICENSE, no `.gitignore`, no GitHub Pages config. Verified with `git ls-tree -r` + `gh api`. Irregularities: 3 (see `docs/REPO_REVIEW.md`). |
| T2 | Official-source ingestion pipeline (reproducible refresh) | **done** | `1220d13c` | `pipelines/fetch_nfl_sources.py`, `data/raw/sources.json` | Targets: `nfl.com/injuries`, `nfl.com/standings`, `nfl.com/schedules`, `nfl.com/teams/*/stats`, `nfl.com/teams/*/roster`, `nfl.com/news`. Manual read of every one of these endpoints confirmed reachable 2026-11-14. Sandbox blocks direct egress to `nfl.com`, so the committed snapshot was captured through the agent's HTTP fetch tool; the script performs the same fetches when run from a networked host. |
| T3 | Verified Week 10 injury + availability dataset (all 28 playing teams) | **done** | `1220d13c` | `data/verified/injury_report_week10.json`, `data/verified/availability_week10.json` | Transcribed line by line from `https://www.nfl.com/injuries/` (title: "Official Latest NFL Injury Report … Week 10 of the 2026 Season"), 8 chunks, 2026-11-14 02:52 UTC. 281 reported rows across 28 clubs. Cross-checks run in `pipelines/validate.py`. Irregularities: 6 flagged → `needs review`. |
| T4 | Verified standings / scoring baseline through Week 9 | **done** | `1220d13c` | `data/verified/standings_2026.json` | `https://www.nfl.com/standings/?season=2026&week=10&sort=division`. Integrity check: ΣPF = ΣPA = 6291 exactly across 32 clubs (passed in `validate.py`). Implied 137 games vs 136 in third-party weekly counts → flagged. |
| T5 | Verified team-performance snapshot (offense + opponent splits) | **needs review** | `1220d13c` | `data/verified/team_stats_snapshot.json` | Read from 7 official club stats pages (`nfl.com/teams/<slug>/stats`). Only single-value fields published (yards, first downs, 3rd/4th down, sacks, FG, TD, turnover ratio). Composite runs (`OFFENSE Plays/Avg`, `PASSING Comp-Att-Int-Avg`, `TOUCHDOWNS Rush/Pass/Ret/Def`) render as concatenated digits in the extracted text and are **deliberately not published** — needs the structured API. 25 clubs still `unavailable` → coverage row on site. |
| T6 | Line-origination model + signals (single, parlay, prop combos) | **done** | `1220d13c` | `model/config.py`, `model/originate.py`, `model/availability.py`, `data/model/*` | Inputs are only verified rows (T3, T4, T5). 4 of 14 games fully sourced → published; 10 games output `BLANK — inputs missing`. Every constant is declared in `model/config.py` with `verified=False` and is listed in the Assumptions register. Fixture backtest included to prove the code runs; it is synthetic and labelled as such. |
| T7 | Correlation study + parlay leg-correlation model | **done** | `1220d13c` | `model/correlation.py`, `data/model/correlation.json` | Cross-sectional ρ computed from verified 32-club aggregates (Pearson, exact, reproducible). Same-game leg ρ is a **specification, not a measurement** — needs play-by-play, which no official free endpoint exposes → flagged. |
| T8 | Validation gates (definition + executable gate runner) | **done** | `1220d13c` | `model/gates.py`, `backtest/leaderboard.py` | 9 gates, each with a numeric threshold, a pass/fail implementation and a data-requirement line. Gates that cannot be evaluated yet return `HOLD`, never `PASS`. |
| T9 | Strategy leaderboard with rewards | **done** | `1220d13c` | `backtest/leaderboard.py`, `backtest/fixtures/*` | Scoring = CLV-anchored, not PnL-anchored (luck removal): units EV, 1-edge Kelly sizing, block-bootstrap CI, Winkler score, Brier, mean-CLV, skill-vs-luck split. Rewards defined in `docs/STRATEGY_PLAYBOOK.md`. Synthetic fixtures only — **no claim of live accuracy is made anywhere**. |
| T10 | Suggestions for site/system improvement | **done** | `1220d13c` | `docs/SUGGESTIONS.md` | 18 suggestions, each with rationale, effort, dependency, and the decision it unblocks, so a human can pick a path before implementation. |
| T11 | Open questions / known-unknowns register | **done** | `1220d13c` | `docs/OPEN_QUESTIONS.md` | 34 questions grouped by what is known, what is missing, and what answer is required before a decision is defensible. |
| T12 | Executive summary | **done** | `1220d13c` | `docs/EXECUTIVE_SUMMARY.md` | Condensed from T1–T11 only; no new facts. |
| T13 | GitHub Pages site (landing + category subpages + Flagged for Review) | **done** | `1220d13c` | `site/**`, `pipelines/build_site.py` | Dependency-free static HTML generated from `data/verified/*` + `data/model/*`. `pipelines/build_site.py --check` asserts no broken internal links and no orphan rows. |
| T14 | Integration: re-verify combined data, confirm build, PR → main, merge, Pages | **in progress** | `1220d13c` | all (integration only) | Runs `pipelines/validate.py` + `pytest` + `build_site.py --check` on the merged tree, then opens and merges the PR and polls the Pages build. Result recorded in *Integration log*. |

---

## Change-request log

| Date (UTC) | Requester | File / owner | Request | Reason |
| --- | --- | --- | --- | --- |
| — | — | — | (none yet) | — |

## Conflict log

| Date (UTC) | Files | Between sessions | Resolution |
| --- | --- | --- | --- |
| 2026-11-14 | `COORDINATION.md` | none — repo had a single active session | no conflict; created file |

## Handoff log

| Date (UTC) | Task | From → To | Reason |
| --- | --- | --- | --- |
| — | — | — | (no stale claims observed) |

## Integration log

| Step | Result |
| --- | --- |
| `pipelines/validate.py` | see *Verification log* below |
| `pytest -q` | see *Verification log* below |
| `build_site.py --check` | see *Verification log* below |
| PR | pending |
| Merge | pending |
| Pages deploy | pending |

## Verification log

Populated by the final integration run (T14). Every published row traces to a fetched
official page; the fetch timestamp, URL and chunk used are stored per dataset in
`data/raw/sources.json`.

## Flagged for review (mirrors `site/flagged.html`)

See `data/verified/flags.json` — 6 data irregularities + 8 structural gaps, each with the
official link to re-check, what was observed, and the decision it blocks.
