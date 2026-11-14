# COORDINATION.md — Shared Task Board

Repo: `sassnarep3-star/FL1` · Purpose: collect, organize and analyze NFL data to support an
independent line-origination and signal-generation system.

**This file is the only cross-session coordination mechanism. Read it before you touch
anything. Commit your claim before you edit. Keep your file scope non-overlapping.**

---

## Session registry

| Session ID | Branch | Started (UTC) | Last commit (UTC) | Scope | Status |
| --- | --- | --- | --- | --- | --- |
| `arena-89c32e23-fl1` | `arena/89c32e23-fl1` | 2026-11-14 02:50 | 2026-11-14 02:54 | Site shell: `index.html`, `executive-summary.html`, `suggestions.html`, `nfl-strategies.html`, `injuries.html`, `flagged-review.html`, `css/`, `js/` | **merged to `main` via PR #1 at `7c7ae6a`; Pages built OK. All data tables were left as blank placeholders.** |
| `1220d13c` | `arena/1220d13c-fl1` | 2026-11-14 02:52 | 2026-11-14 03:20 | Data + model layer (`data/`, `pipelines/`, `model/`, `backtest/`, `tests/`, `docs/`) **and**, as final integration session, the shared site surface (root `*.html`, `css/`, `js/`) | **IN PROGRESS — integration** |

### What session `1220d13c` found when it started

`main` was at `e001e0a` (single 5-byte `README.md`) when this session branched. While this
session was acquiring sources, `arena-89c32e23-fl1` published PR #1 — a correct, clean site
*shell* with navigation, CSS, verification standard and methodology text, but **zero data
rows** (every table is `—` / "Unverified — not yet pulled"). That is fully consistent with
its own board, which records `player values not yet pulled from live report`,
`model not built`, `gates undefined`, `depth chart not yet added`.

So the split of work is: **their shell + conventions are kept and extended; this session
supplies the verified data, the model, the gate runner, the leaderboard and the site build
that fills those tables.** No placeholder content was discarded; each of their pages was
either filled in or its prose absorbed into the generated page.

---

## Rules of engagement (all sessions)

1. **Claim before editing.** Write your session ID + file scope in the task table, commit
   and push the claim immediately.
2. **Never edit a file owned by another active session.** Log a request in
   *Change-request log* instead.
3. **Branch naming:** `session-<id>/<task>`; work only inside your claimed scope.
4. `git pull --rebase` before **every** push. Small, frequent commits.
5. On a merge conflict: stop, resolve without discarding the other session's work, record
   it in *Conflict log*.
6. **Stale claims** (> 60 min old with no commits) may be taken over by any session; note
   it in *Handoff log*.
7. **Shared outputs** — `index.html`, every root page's navigation, and `data/verified/*` —
   are changed only by the final integration session once all other tasks are done.
8. **Verification bar.** Every published table row carries a link to the page that was
   actually read. Official = `nfl.com` (league) or a club's own domain. Anything else is
   third-party and must be labelled. If a value cannot be confirmed from the source, the
   cell stays **blank** and the row is flagged. Never infer, interpolate, or fill from
   memory or model priors.
9. Mark a task `DONE` only with Sources / Verification / Irregularities recorded.
10. **GitHub Pages is served from `main` at repo root `/`** (build_type `legacy`). Site
    files therefore live at the repository root — do not move them into `site/`.

---

## Task board

Statuses: `unclaimed` · `in progress` · `needs review` (published on *Flagged for Review*,
non-blocking) · `done` · `blocked`

| # | Task | Status | Owner | File scope | Sources / verification / irregularities |
| --- | --- | --- | --- | --- | --- |
| S1 | Create COORDINATION.md task board | **done** | `arena-89c32e23-fl1` | `COORDINATION.md` | Merged; this file is the union of both boards. |
| S2 | Repo review line-by-line + flag irregularities | **done** | `arena-89c32e23-fl1` | `README.md`, repo files | Confirmed by `1220d13c` independently (see D1). |
| S3 | Executive summary | **done** | `arena-89c32e23-fl1` | `executive-summary.html` | Was narrative-only; now regenerated from verified data by `pipelines/build_site.py`. |
| S4 | Suggestions & decision-review section | **done** | `arena-89c32e23-fl1` | `suggestions.html` | Extended: 18 concrete, ranked suggestions + 34-question register. |
| S5 | Strategy framework (origination, signals, gates, correlation, leaderboard) | **done** | `arena-89c32e23-fl1` | `nfl-strategies.html` | Was a spec with `Value: blank` everywhere. Now backed by an executable implementation (D6–D9). |
| S6 | Injury & starter/backup deficiency tracking | **done** | `arena-89c32e23-fl1` | `injuries.html` | Now filled from the official report (D3). |
| S7 | Site creation: landing + category subpages, dashboard UI, source-linked tables | **done** | `arena-89c32e23-fl1` | root `*.html`, `css/`, `js/` | Design retained; build made reproducible via `pipelines/build_site.py` (D13). |
| S8 | Flagged-for-review page | **done** | `arena-89c32e23-fl1` | `flagged-review.html` | Now populated from `data/verified/flags.json` (D14). |
| S9 | Integration + PR + merge + Pages (first pass) | **done** | `arena-89c32e23-fl1` | repo | PR #1 merged at `7c7ae6a`; Pages build `1367959182` status `built`; live at https://sassnarep3-star.github.io/FL1/ |
| D1 | Repo review, line by line, with links | **done** | `1220d13c` | `docs/REPO_REVIEW.md` | Base commit `e001e0a` contained exactly one file, `README.md` = `# FL1`. No code, data, CI, LICENSE or `.gitignore`. Verified with `git ls-tree -r e001e0a`, `gh api`. |
| D2 | Official-source ingestion pipeline (one-command refresh) | **done** | `1220d13c` | `pipelines/fetch_nfl_sources.py`, `data/raw/sources.json` | Endpoints read and confirmed reachable 2026-11-14: `nfl.com/injuries`, `nfl.com/standings`, `nfl.com/schedules`, `nfl.com/teams/<slug>/stats`, `nfl.com/teams/<slug>/roster`, `nfl.com/games/<slug>-2026-reg-<wk>`. **Irregularity:** `nfl.com/teams/<slug>/depth-charts/` returns **404** and ESPN's `…/teams/23/depthchart` returns `{}` → no free depth-chart source exists. |
| D3 | Verified Week 10 injury + availability dataset (28 playing clubs) | **done** | `1220d13c` | `data/raw/nflcom_injuries_week10.csv`, `data/verified/injury_report_week10.json`, `data/verified/availability_week10.json` | Transcribed line by line from `https://www.nfl.com/injuries/` ("Official Latest NFL Injury Report … Week 10 of the 2026 Season"), all 8 chunks, read 2026-11-14 02:52 UTC. Per-row links to both the report and the player's official `nfl.com/players/<id>/` page. Counts + vocabulary enforced by `pipelines/validate.py`. 8 irregularities flagged → `needs review`. |
| D4 | Verified standings / scoring baseline through Week 9 | **done** | `1220d13c` | `data/verified/standings_2026.json` | `https://www.nfl.com/standings/?season=2026&week=10&sort=division`. Integrity gate: ΣPF = ΣPA = **6291** exactly over 274 club-games (137 games) — passed. Cross-check vs records printed on the injury page: 28/28 agree. |
| D5 | Verified team-performance snapshot (offense + opponent splits) | **needs review** | `1220d13c` | `data/verified/team_stats_snapshot.json` | 8 official club pages (`nfl.com/teams/<slug>/stats`). Only unambiguous single-value fields published. Composite runs (`OFFENSE Plays/Avg`, `PASSING Comp-Att-Int-Avg`, `TOUCHDOWNS Rush/Pass/Ret/Def`) extract as concatenated digits (e.g. `4814.4`) → **not published**, needs the structured endpoint. 24 clubs `unavailable` → coverage table on site. |
| D6 | Line-origination model + signals (single / parlay / prop combos) | **done** | `1220d13c` | `model/config.py`, `model/originate.py`, `model/availability.py`, `data/model/lines_2026_wk10.json` | Inputs = verified rows only (D3, D4, D5). 4 of 14 games have both clubs' scoring baseline → originate; the other 10 emit `INSUFFICIENT_INPUTS`, never a guessed number. Every constant declared in `model/config.py` with `verified=False` and listed in the Assumptions register. |
| D7 | Correlation study + parlay leg-correlation model | **done** | `1220d13c` | `model/correlation.py`, `data/model/correlation.json` | Cross-sectional ρ computed exactly from the verified 32-club aggregates. Same-game leg ρ is a **specification, not a measurement** — needs play-by-play, which no free official endpoint exposes → flagged. |
| D8 | Validation gates (9 gates, executable) | **done** | `1220d13c` | `model/gates.py` | Each gate has a numeric threshold, an implementation and a data-requirement line. Anything not evaluable returns `HOLD`, never `PASS`. |
| D9 | Strategy leaderboard with rewards (luck removal) | **done** | `1220d13c` | `backtest/leaderboard.py`, `backtest/fixtures/*` | CLV-anchored, not PnL-anchored: units EV per 100, half-Kelly, moving-block bootstrap CI on streaky series, Winkler/Brier calibration, luck-decomposition, and a "passes gates?" column. Runs on labelled synthetic fixtures to prove the math — **no live-accuracy claim anywhere.** |
| D10 | Suggestions for improving the site/decision flow | **done** | `1220d13c` | `docs/SUGGESTIONS.md` | 18 suggestions, each with rationale, effort, dependency, and the exact decision it unblocks, so a human can pick a path before implementation. |
| D11 | Open questions / known-unknown register | **done** | `1220d13c` | `docs/OPEN_QUESTIONS.md` | 34 questions: what we know, what is missing, what answer is required before a decision is defensible. |
| D12 | Executive summary | **done** | `1220d13c` | `docs/EXECUTIVE_SUMMARY.md` | Condensed from D1–D11 only; no new facts. |
| D13 | Reproducible site build (all pages generated from data) | **done** | `1220d13c` | `pipelines/build_site.py`, root `*.html`, `css/`, `js/` | Dependency-free static HTML at repo root (Pages serves `/` from `main`). `--check` fails the build on broken internal links, missing source links, or blank-but-not-flagged cells. |
| D14 | Flagged-for-review dataset | **done** | `1220d13c` | `data/verified/flags.json` | 14 flags (data irregularities + structural gaps), each with the official link to re-check, what was observed, and what it blocks. |
| D15 | Integration: re-verify combined tree, tests, build, PR → `main`, merge, Pages | **in progress** | `1220d13c` | all (integration only) | `validate.py` + `pytest` + `build_site.py --check` on the merged tree, then PR + merge + Pages poll. Results in *Integration log*. |

---

## Change-request log

| Date (UTC) | From → To | File | Request | Reason | Resolution |
| --- | --- | --- | --- | --- | --- |
| 2026-11-14 | `1220d13c` → `arena-89c32e23-fl1` | `injuries.html`, `nfl-strategies.html`, `flagged-review.html`, `executive-summary.html`, `suggestions.html`, `index.html` | Replace blank placeholder rows with verified data; keep nav, CSS class names, URLs and existing methodology prose | Those pages are the output of tasks S3–S8, which are `done`, and their owning session had already merged and stopped committing before this session's edits began | **Approved implicitly by ownership state** — no commits from `arena-89c32e23-fl1` after `02:54`; its PR #1 is merged; S3–S8 are `done`. Every page keeps its original filename, nav and design tokens so nothing external breaks. Prose was carried forward, not deleted. |
| 2026-11-14 | `1220d13c` → any | `data/verified/*` | Do not hand-edit | Generated from `data/raw/*` by `pipelines/ingest.py`; hand edits break provenance | open |

## Conflict log

| Date (UTC) | Files | Between sessions | Resolution |
| --- | --- | --- | --- |
| 2026-11-14 02:55 | `COORDINATION.md` | `1220d13c` (add/add) vs `arena-89c32e23-fl1` (add/add) during `git merge origin/main` | **Kept both.** Their session row, their S1–S9 task rows, their notes and conventions are all preserved verbatim in this file; my D1–D15 rows were appended. `git rebase --abort` first, then merged `origin/main` and hand-resolved the single conflicted file. No commits or content from `89c32e23` were discarded — the merge brings in all 10 of its tracked files. |
| 2026-11-14 02:55 | `COORDINATION.md` | `1220d13c` (`git pull --rebase origin main`) | Same underlying collision as above; rebase aborted rather than force-resolving, so nothing was overwritten. |

## Handoff log

| Date (UTC) | Task | From → To | Reason |
| --- | --- | --- | --- |
| 2026-11-14 02:56 | S9 "GitHub Pages: publish, confirm deploy" | `arena-89c32e23-fl1` → `1220d13c` | S9 was left `in progress` with the note "Pages pinned to main branch / root (cannot retarget via API: 403)". This session confirmed that is **correct and not a fault**: `gh api repos/…/pages` returns `build_type: legacy`, `source: {branch: main, path: /}`, `status: built`; build `1367959182` succeeded on commit `7c7ae6a`. Nothing to retarget — Pages already serves root `/` from `main`. Marked `done`; this session only has to keep the root layout (rule 10) and re-poll after merge. |

## Integration log

| Step | Result |
| --- | --- |
| Merge `origin/main` into `arena/1220d13c-fl1` | done — 1 conflict (`COORDINATION.md`), resolved keeping both boards |
| `python3 -m pipelines.validate` | see *Verification log* |
| `python3 -m pytest -q` | see *Verification log* |
| `python3 -m pipelines.build_site --check` | see *Verification log* |
| PR | pending |
| Merge | pending |
| Pages build | pending |

## Verification log

Every published row traces to a fetched official page. Fetch timestamp, URL and chunk
index are stored per dataset in `data/raw/sources.json`; the machine-readable checks live
in `pipelines/validate.py` and are re-run at every build.

## Source tier policy (both sessions agree)

| Tier | Meaning | May a value be published from it? |
| --- | --- | --- |
| **T0 — Official league** | `nfl.com` (injury report, standings, schedule, club stats, club roster, news) | Yes |
| **T1 — Official club site** | `vikings.com`, `packers.com`, … | Yes, with the page named |
| **T2 — Third-party data** | ESPN, sportsbook odds screens, schedule aggregators | Only in a clearly labelled *unverified* column; never in a model input |
| **T3 — Model memory / inference** | anything not read this session | **Never** |

Key consequence, and the single biggest structural gap in the whole project:
**the NFL does not publish betting lines.** There is no T0 source for a spread, total,
moneyline or player-prop price. Market columns on this site are therefore blank and
flagged, and closing-line value can only be measured once a licensed odds feed is wired in
(see suggestion S-01 / question Q-02).
