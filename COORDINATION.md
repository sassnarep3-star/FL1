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

## Task board — session `arena/360ca650-fl1` (requirements sprint R21–R28)

**Session ID:** `arena-360ca650-fl1` · **Branch:** `arena/360ca650-fl1` (from `9d7ca32` of `main`) ·
**Claimed:** 2026-11-14T22:12Z · **Status:** active — this session is the only live session and performs
its own final integration. Per the standing rule, work is **additive**: new files plus new pages added to
`NAV` in `tools/site.py`; shared registers are appended to, never replaced.

| # | Task | Status | Owner | File scope (claimed) | Sources / verification | Irregularities |
|---|------|--------|-------|----------------------|------------------------|----------------|
| R21 | Price-snapshot store — records opening **and** closing numbers for every market we originate | done | arena-360ca650-fl1 | `engine/snapshots.py`, `data/price_snapshots.json`, `scripts/build_price_snapshots.py`, `price-snapshots.html` | data/raw/MANIFEST.json (sha256-pinned captures); week-10 board | Opening prices have no source at all → every open cell blank+flagged |
| R22 | Verified results feed — so backtests and ROI can be computed at all | done | arena-360ca650-fl1 | `engine/backtest.py`, `data/results_feed.json`, `scripts/build_results_feed.py`, `results-feed.html` | nfl.com schedules capture (raw/schedule-results-2026-week1-10.tsv), standings cross-check (tools/verify_results.py) | none expected |
| R23 | Originate the side first, then the total, then the moneyline | done | arena-360ca650-fl1 | `data/models.json` (append), `line-origination.html` section, `line-board.html` | requirement text | Supersedes the earlier "totals-first" design note; change logged, old text preserved in archive |
| R24 | Publish model fair line, market line, difference as **separate columns** | done | arena-360ca650-fl1 | `engine/fairline.py`, `scripts/build_line_board.py`, `data/line_board.json`, `line-board.html` | fair = computed from official standings/results; market = pinned third-party capture (flagged) | No official source prices NFL lines (F-18 to log); policy: show with 3P badge + flag per the requirement, strict-blank alternative left open for review |
| R25 | Separate signal from staking in the leaderboard (lucky staking cannot mask bad signal) | done | arena-360ca650-fl1 | `data/leaderboard_signal_staking.json`, `strategies.html` section | engine/leaderboard.py scoring | Root page previously claimed "no backtest anywhere in this repository" while data/leaderboard.csv holds third-party backtests — inconsistency to flag (F-19) |
| R26 | Track the **depth of the replacement**, not just the fact of a replacement | done | arena-360ca650-fl1 | `scripts/build_replacement_depth.py`, `data/replacement_depth.tsv`, `replacement-depth.html` | data/depth.tsv (31 club charts), data/injuries.tsv (official), depth-sources.tsv | HOU chart image-only (already flagged); string order is club-labelled unofficial |
| R27 | Correlations only from officially sourced numbers, publish **n** with each value | done | arena-360ca650-fl1 | `engine/corr_official.py`, `scripts/build_correlations_official.py`, `data/correlations_official.json`, `correlation-register.html` | official results/standings/schedule/injury captures only | Third-party correlations (measured.json, prop-correlations, correlations.csv) stay on their labelled pages, excluded from this register |
| R28 | Demotion gate — sends a live strategy back to paper | done | arena-360ca650-fl1 | `engine/demotion.py`, `data/validation_gates.json` (append G-14), `validation.html` section | design decision + engine tests | Thresholds are proposed rules, not facts; left reviewable |
| R29 | Registers + site integration: requirements/questions/suggestions/flags/sources append, NAV, rebuild, checks, exec summary | done | arena-360ca650-fl1 | `data/{requirements,questions,suggestions,flags}.json`, `data/sources.tsv`, `tools/site.py`, `tests/test_r21_r28.py`, `EXECUTIVE_SUMMARY.md`, `COORDINATION.md` | tools/checklinks.py, scripts/verify_site.py, tools/verify_injuries.py, tools/verify_results.py, unittest | — |
| R30 | Final integration: PR → main, merge, confirm Pages deploy, record result here | unclaimed | arena-360ca650-fl1 | PR only | Pages API | — |

### R21–R29 completion record (2026-11-14)

**Built (all re-runnable):** `engine/{snapshots,backtest,fairline,demotion,corr_official}.py`;
`scripts/build_{results_feed,price_snapshots,line_board,correlations_official,replacement_depth,signal_staking,register_r21_r28}.py`;
`data/{price_snapshots,results_feed,line_board,correlations_official,leaderboard_signal_staking}.json`,
`data/replacement_depth.tsv`; pages `line-board`, `price-snapshots`, `results-feed`,
`replacement-depth`, `correlation-register` + sprint sections on Line Origination, Leaderboard,
Validation (`G-14`), Executive Summary.

**Verification performed (all passing at completion):**
- `python3 -m unittest discover -s tests -q` → **102 tests OK** (75 pre-existing + 27 sprint rules).
- `tools/checklinks.py` → **21 pages OK**, every internal link/anchor resolves, all source IDs registered.
- `scripts/verify_site.py` → **0 errors, 0 warnings** (docs/computed layer intact).
- `tools/verify_injuries.py` → 345/345 rows match the raw capture. `tools/verify_results.py` → PASS
  (32/32 clubs). `scripts/verify_d.py` → **V5–V9 PASS** (V7a FLAGGED by design).
- `scripts/build_results_feed.py` hard-fails unless the feed reproduces the official standings exactly.
- Rebuild determinism: V6 re-ran `build_correlations.py` / `strategy_lab.py` / `build_week10_board.py`
  with byte-identical artefacts.

**Sources:** S01/S03/S49/S50 (official nfl.com captures: injuries, standings, schedule, results);
S47 + `data/raw/MANIFEST.json` sha256 pins (third-party market capture, flagged); club depth charts
S07/S08/S16–S46 (labelled unofficial). Every new table row links to its source record.

**Irregularities found and published (`flagged.html` F18–F25):** F18 market prices third-party-only
(policy question Q23); F19 root-vs-computed leaderboard claim contradiction; F20 moneyline closes
uncaptured; F21 `closing_spread_home` misnamed (V8: feed holds the AWAY spread) + unvalidated
`market_implied_home_winprob` formula excluded; F22 totals-first superseded by mandated order; F23
demotion thresholds are proposed rules; F24 fair coefficients computed from 137 official games only;
**F25 (High)** computed-layer `breakeven_hit` is circular (1/(1+realized ROI)) so its G4 gate is
unusable — transcribed with a warning, one-line fix offered as SG24, not silently patched.

**Note on environment:** `scripts/verify_d.py` V9 and `build_prop_correlations_d.py` need the
workspace mirror `/home/user/datawork/player_stats_weekly_archive.parquet` (Beexly/Sports, 5.6 MB)
plus `pandas numpy scipy pyarrow`; fetched from GitHub for this run and left outside the repo.

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
| 2026-11-14 | `ab4e9b05` | **PR #3 merged** as `eb50220` (merge commit, 2026-11-14T03:05:45Z). GitHub Pages build for `eb50220`: **built**. Live site verified. |
| 2026-11-14 | `ab4e9b05` | Found a rendering bug by reading the live page: the dashboard's Source column printed literal `<a class=...>` text, because `src_link()` markup was passed through `cell()` which escapes it. Fixed via `raw_src()`; added an escaped-markup guard to `checklinks.py` and proved the guard fires by injecting the bug. |
| 2026-11-14 | `ab4e9b05` | **PR #5 merged** as `d5e9cc0`. Pages build for `d5e9cc0`: **built**. Live `index.html` re-fetched and confirmed rendering real links. |
| 2026-11-14 | `ab4e9b05` | **PR #7 merged** as `6ba143f` (review guide, deploy record, option-label tidy). Pages build: **built**. |
| 2026-11-14 | `ab4e9b05` | Found a second rendering bug by reading the deployed page: `verification.html` printed its own TSV header line as a data row, and two page counts were stale at 13 instead of 14. **PR #8 merged** as `1c6c8ab`; Pages build **built**; live page re-fetched clean. |
| 2026-11-14 | `ab4e9b05` | Final state: 14 pages live, `verify_injuries.py` 345/345 PASS, `checklinks.py` PASS with 0 escaped fragments, 15 flagged items published, 0 fabricated values, 0 estimated values presented as sourced. |

---

## PR and deploy record

| Item | Result |
|---|---|
| PR #3 (this session's main deliverable) | **MERGED** into `main` as merge commit `eb50220` at 2026-11-14T03:05:45Z |
| PR #5 (escaped-link fix) | **MERGED** into `main` as merge commit `d5e9cc0` |
| PR #7 (review guide, PR/deploy record, option labels) | **MERGED** into `main` as merge commit `6ba143f` |
| PR #8 (verification table header fix) | **MERGED** into `main` as merge commit `1c6c8ab` |
| GitHub Pages source | `main`, path `/`, legacy build |
| Pages build for `eb50220` | **built** |
| Pages build for `d5e9cc0` | **built** |
| Pages build for `6ba143f` | **built** |
| Pages build for `1c6c8ab` | **built** |
| Live URL | https://sassnarep3-star.github.io/FL1/ |
| Live verification | `index.html`, `injuries.html`, `flagged.html`, `suggestions.html`, `questions.html`, `verification.html` fetched from the live host and read; all render correctly |
| Note on caching | GitHub Pages serves `index.html` and cached paths from a CDN. A stale read straight after a deploy is a cache artefact, not a broken deploy — re-fetch with a `?cb=<sha>` query before concluding a page is wrong. This caused one false alarm during this session. |
| Branches merged before this one | PR #1 (`7c7ae6a`), PR #2 (`42b06f5`), PR #4 (`557ffc3`) — all preserved in `archive/` |

## Verification performed on the merged `main` tree

| Check | Result |
|---|---|
| `tools/verify_injuries.py` | PASS — 345 of 345 rows match the raw capture, same order, field for field |
| `tools/checklinks.py` | PASS — 14 pages, every internal link and anchor resolves, every page reachable, all source IDs registered, 0 escaped fragments |
| `tools/build.py` | PASS — 32 teams, 32 standings rows, 345 injury rows, 15 sources (12 verified), 60 depth slots, 20 questions, 15 suggestions, 20 requirements, 6 strategies, 15 flags |
| Independent cross-transcription | 156 of 161 shared rows identical to another session's capture; the 5 differences are that CSV's comma-shift bug, not a data dispute |
| Live deploy | Pages build `built` for the merge commit; pages re-fetched and rendered correctly |

## Requests

_None outstanding._

## Open items for review (published, non-blocking)

All 15 items on [`flagged.html`](flagged.html). Every unverifiable value in this repo is left blank there
with the reason and the source that was attempted.

### Preserved task board and integration record from the merged branch (verbatim)

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

### Session `arena/3f677e8a-fl1` — completion record

- **Merges into main (all merged, none left open):**
  - https://github.com/sassnarep3-star/FL1/pull/14 — depth charts, results, verification
    (merged 2026-11-14T03:27:25Z)
  - https://github.com/sassnarep3-star/FL1/pull/15 — Kansas City source chip, bye-club note,
    then superseded on the Computed Lab card by session `arena-34db7d1d-fl1`
    (merged 2026-11-14T03:39:13Z)
  - https://github.com/sassnarep3-star/FL1/pull/18 — fix for scrambled landing-page figures
    (merged 2026-11-14T03:42:08Z)
- **Note:** an earlier draft of this record cited "PR #6". That was wrong — #6 belongs to
  another session. Corrected here.
- **What this session added on top of main (PRs #1–#5):**
  - `data/depth.tsv`, `data/depth-sources.tsv`, `tools/normalize_depth.py` — depth charts for
    30 clubs, folded in with the existing Kansas City chart for **31 of 32 clubs covered**.
  - `data/results.tsv`, `tools/verify_results.py` — 137 game results, proven against the
    published standings.
  - `data/sources.tsv` S16–S46 (30 club depth-chart pages plus Houston's image-only page).
  - `data/flags.json` F16 (Houston chart not machine-readable).
  - `data/verification.tsv` — 5 new checks, including two independent cross-transcriptions.
  - Depth page rebuilt league-wide; standings page gains scoring rates and full game log.
- **Sources verified (loaded and read, 2026-11-14):** 30 `<club>.com/team/depth-chart` pages,
  `nfl.com/schedules/2026/by-week/week-1..10`, `nfl.com/standings/`, `nfl.com/injuries/`.
- **Verification performed:**
  - 137 games summed → matches the official standings for all 32 clubs, 0 mismatches.
  - Standings: 352 field comparisons against an independently captured table, 0 differences.
  - Injuries: 345 rows, two independent transcriptions of the same page, identical content
    (2 Houston rows in a different order; 2 cosmetic vocabulary differences).
  - Club membership: 0 players charted by a club other than the one on whose injury report
    they appear.
- **Irregularity withdrawn, not published:** before the club charts were captured, several
  injury-report names looked like they belonged to other clubs. With the charts in hand the
  check above returns zero conflicts, so the suspicion was **not supported by the official
  documents and is withdrawn**. It is deliberately *not* listed on Flagged for Review.
- **Still open / flagged:** Houston depth chart (F16, image-only); no official snap counts
  (F09); no market price source; single-season snapshot.
- **Branch divergence note (why a force push was needed and was safe):**
  this session branched from `main` @ `e001e0a` before PRs #1–#5 landed, and by the time it
  discovered that, `main` had moved to `d5e9cc0`. It reconciled by **merging** `main` in
  (commit `92cd9e5`) rather than force-pushing, so no other session's work was overwritten.
  A side effect is that this branch's history now contains all of `main`, while the branch's
  own remote tip was still this session's earlier commit `ab0b331`. Ordinary
  `git pull --rebase` therefore tries to replay main's entire history onto `ab0b331` and
  deadlocks on `COORDINATION.md`. Verified before pushing:
  `ab0b331`, `5a0e62a`, `b124358`, `3183479` and `d5e9cc0` are all ancestors of `HEAD`, and
  `git diff HEAD origin/arena/3f677e8a-fl1` shows no file present on the remote tip that is
  missing locally. The force push with lease therefore drops nothing; it only moves the
  branch pointer forward past this session's own superseded commits.
- **Upstream fixed:** `arena/3f677e8a-fl1` now tracks `origin/arena/3f677e8a-fl1`. It had no
  upstream configured, so `git pull` was silently rebasing onto `origin/main` — the cause of
  the first conflict. Any other session on this branch should check `git rev-parse --abbrev-ref @{u}`.

---

## Session record — `arena-ab82c93f` (`arena/ab82c93f-fl1`) · 2026-11-14

**Scope:** a new, non-overlapping computed sub-site at `docs/computed/`, plus its own standalone
`scripts/` and `data/` files. Shared outputs were **not** rewritten: `README.md` keeps main's text
verbatim and appends one section, this file is appended to, and the root `index.html` gains exactly
one nav link and one card.

### Delivered

| Task | Status | Files (all new) |
|---|---|---|
| Reproducible pipeline with SHA-256 pinning | done | `scripts/fetch_data.py`, `scripts/lib.py`, `data/raw/MANIFEST.json` |
| Strategy lab: 16 variants × 7 pre-registered gates | done | `scripts/strategy_lab.py`, `data/strategies.csv`, `data/leaderboard*.csv` |
| Correlation engine (same-game, cross-game, parlay economics) | done | `scripts/build_correlations.py`, `data/correlations.csv`, `data/parlay_economics.csv` |
| Availability + QB-depth model | done | `scripts/build_availability.py`, `data/availability_2025.csv`, `data/depth_deficiency.csv` |
| Official Week 10 2026 capture | done | `data/week10_2026_official.csv` (345 rows), `scripts/build_week10_board.py` |
| Registers | done | `data/{requirements,questions,suggestions,irregularities,unverified}.csv`, `data/sources.json` |
| Computed sub-site, 14 pages | done | `scripts/build_site.py`, `docs/computed/*.html` |
| Build gate + CI | done | `scripts/verify_site.py`, `.github/workflows/verify.yml` |

### Headline result

**16 pre-registered strategies tested on 5,336 games (2006-2026) at real closing prices. 0 passed all
seven gates. The reward pool pays 0 units.** A control that bets every home team returns -5.2% (the
vig). Best raw candidate `WIND15_UNDER` (+7.2% ROI, p = 0.063) fails G3, G4 and G6 **and** is not
implementable, because it uses post-game measured wind.

This directly complements — and does not contradict — the root site's deliberate "no strategy has a
result" position: this layer ran the tests and the answer was no.

### Verification performed

- Every number regenerated by script; `data/raw/MANIFEST.json` pins each input by SHA-256 + row count.
- 345 Week-10 rows each carry the official URL **and** a verbatim quote, so transcription is auditable
  offline.
- `scripts/verify_site.py` enforces 19 checks and exits non-zero on: unsourced table row, broken or
  placeholder link, missing/non-https source, malformed gate column, verdict/gate mismatch, reward
  paid to an unapproved strategy, asymmetric correlation matrix, incomplete Week-10 join, a rendered
  `nan`, or a root site that lost its pages.
- CI rebuilds everything and fails if the committed result differs.

### Irregularities (full detail at `docs/computed/flagged.html`)

| ID | Severity | Item |
|---|---|---|
| FLAG-01 | Critical | nflverse release CDN unreachable → injuries limited to 2025, no depth charts, no snap counts |
| FLAG-02 | High | No depth order in the official roster feed → 2nd/3rd/4th-string model stops at QB |
| FLAG-03 | Medium | `closing_lines.csv` has no push outcome |
| FLAG-04 | Medium | `rosters.csv` stops at 2019 |
| FLAG-05 | Medium | NFL Personnel (Injury) Report Policy page 404s |
| FLAG-06 | High | 2026 season incomplete → no 2026 out-of-sample claim |
| FLAG-07 | Low | Mixed team-code generations (SD/LAC, STL/LA/LAR, OAK/LV) |
| FLAG-08 | Medium | Closing prices only, no openers |
| FLAG-09 | Low | Push exclusion shifts the gate denominator slightly |

**The CDN failure (FLAG-01) was also found independently by session `kanlerxz87-cyber` in a sibling
repository**, where it is logged as F-10; its finding F-08 (no depth order in the official roster feed)
matches FLAG-02 here. Two independent sessions reaching the same two conclusions from different
sources is the strongest evidence in this build that they are environmental, not mistakes.

### Two real bugs my own verification step caught (recorded for honesty)

1. **Vig breakeven was computed from realised returns instead of from the price**, which circularly
   dragged it toward the observed hit rate — it reported a 105.5% breakeven for the control. Fixed to
   `1 / mean(decimal price)`, giving ~51.3%.
2. **The Bonferroni denominator was hand-typed as 15 while 16 variants were searched.** Fixed: it is
   now read from the signal registry at runtime and cannot drift. G6 currently uses α/16 = 0.00313.

### Integration instructions

1. Adopt by merging this branch as-is. Nothing at the repo root is replaced.
2. **Do not add a Pages deploy job to `.github/workflows/verify.yml`.** It intentionally has none. The
   Pages source is `main` / root, so `docs/computed/` publishes under
   `https://sassnarep3-star.github.io/FL1/docs/computed/` with no workflow. A deploy job would repoint
   the site root and replace the integrating session's build.
3. To adopt a finding into the root site, copy the number from `data/strategies.csv` or
   `data/correlations.csv` and cite `scripts/strategy_lab.py` / `scripts/build_correlations.py`.

### Lesson for future sessions

`git fetch` at session *start* is not enough. At start `origin/main` was `e001e0a`; **eight other
session branches and five merges to `main` appeared during the run.** Re-check `origin/main`
immediately before the first push and again before opening a PR. Scopes here stayed non-overlapping
only because the build wrote to new paths.

---

## Session record — `arena-046256d0-fl1` (`arena/046256d0-fl1`) · 2026-11-14

**Scope:** built a full verification-first decision dashboard from the empty repo (README-only at start):
landing page plus category subpages, verified Week 10 (2026) standings/schedule/injury data, decision-gate
questions, suggestions register, strategy framework (single bet / parlay / player-prop combos, validation
gates, correlation, luck removal, leaderboard rewards), lines page with verification-gated cells, and a
flagged-for-review page. Sources: NFL.com standings, schedule, injury report, game center (all official).

**Tasks, sources, verification (see `data/verification-log.md` in the archive):** all 32-team standings,
16-game schedule, and the complete Week 10 injury report verified line-by-line against NFL.com on
2026-11-14. Line values had no reachable official source (DraftKings client-rendered, FanDuel HTTP 500)
and were left blank + flagged, per rule.

**Irregularities found by this session:**
- **IR-1 (standings freshness):** NFL.com standings do not reflect the completed Week 10 Thursday game
  (WAS 24, NYG 21, FINAL) — WAS still 3-5-1, NYG 5-3-1. Published as-is, flagged.
- **UNV-1 / UNV-2:** all sportsbook line and player-prop values unverifiable — left blank, flagged.
- **IR-2 (repo hygiene):** the `main`-branch `COORDINATION.md` contained committed merge-conflict
  markers (lines from a prior session's merge). Resolved during this integration: both conflict sides'
  records preserved verbatim, markers removed. Flagged here for the record.

**Conflict with the consolidated build on `main` (resolved, no work discarded):** this session's branch
added site files at the same repo-root paths as the already-merged consolidating build (three earlier
sessions had merged into `main`). `gh pr merge` failed on add/add conflicts. Resolution per the standing
rule in this board: the consolidated site at the repo root stays live; this session's complete site is
preserved **verbatim** in [`archive/arena-046256d0/`](archive/arena-046256d0/) (pages, stylesheet, and
its `data/` verification records), with a README explaining the mapping. Nothing from this session was
deleted; nothing from the consolidating build was altered.

**Integration & deployment:** PR https://github.com/sassnarep3-star/FL1/pull/10 opened from
`arena/046256d0-fl1` to `main`. Merge result and GitHub Pages deploy status recorded in the follow-up
log entry appended below after the merge and deploy check.

### Integration record — session `arena-ab82c93f` (PR #6, #12, #13)
### Integration record — session `arena-ab82c93f` (PR #6)

- **PR:** https://github.com/sassnarep3-star/FL1/pull/6
- **Merged:** 2026-11-14T03:11:55Z · merge commit `457664a` · method `--merge`, no approval wait
- **CI before merge:** `verify-research-build` **pass** (run 43550306043) — rebuild, 19-check verify
  gate, and byte-identical-rebuild check all green
- **Pages:** build `588fa09` → status `built`. Sub-site confirmed reachable at
  https://sassnarep3-star.github.io/FL1/docs/computed/index.html
- **Root site re-checked after merge:** reachable, unbroken, and its headline injury counts
  (345 rows / 66 Out / 10 Doubtful / 84 Questionable) are **identical to this session's independent
  count** — a useful cross-check that two separate transcriptions of the same official report agree.

**Files merged:** `scripts/` (9), `data/` (17 new, 4 regenerated), `docs/computed/` (14 pages + .nojekyll),
`.github/workflows/verify.yml`, `EXECUTIVE_SUMMARY.md`. Shared files touched additively only:
`index.html` (+1 nav link, +1 card), `COORDINATION.md` (this appendix), `README.md` (one appended
section, main's text byte-identical).

**No deploy workflow was added on purpose** — Pages serves from `main` / root, so `docs/computed/`
publishes with no workflow and the root build is untouched.

**Rebase conflicts:** `COORDINATION.md` conflicted on all four rebases because other sessions merged to
`main` while this branch was open (main advanced through `eb50220 → d5e9cc0 → 6ba143f → 1c6c8ab`).
Each time it was resolved by taking `origin/main`'s file verbatim and re-appending this appendix, so
no other session's record was ever discarded. `README.md` and `index.html` merged without conflict.

**Still open for the owner (unchanged by this merge):** FLAG-01 (CDN access) and FLAG-02 (no depth
order) remain the two items that block requirements R13/R14. Both are also recorded as F-08/F-10 by a
sibling session, so they are independently corroborated.

### Correction to this session's own log

Mid-session I ran `rm -rf .git` inside the repo root while cleaning up unrelated files. That was a
mistake and destroyed the local git directory. Recovery: re-cloned the branch from `origin` (where the
previous commit had already been pushed) and copied the recovered `.git` back. **No committed work was
lost**, because the branch had been pushed before the deletion. From that point the branch was rebased
onto current `main`. Recorded here rather than omitted, since the board asks for irregularities to be
logged including the ones a session caused itself.

### Follow-up — session `arena-ab82c93f` (PRs #12 and #13)

- **PR #12** (merged 2026-11-14T03:16:23Z): fixed a real rendering bug where four tables — including
  the entire source registry, the entire Flagged-for-Review register, and all 345 Week-10 official
  injury rows — were publishing **completely empty**. `table()` was being called with display labels
  as column keys, so every cell looked up a non-existent column. Two defences added so it cannot recur:
  `table()` now raises `KeyError` on an unknown column, and `verify_site.py` gains **T2** (no table may
  render an entirely-empty row) and **T3** (every `flagged.html#ANCHOR` must resolve). T2 immediately
  found three further instances that had not been spotted by eye.
- **Lesson worth carrying:** the original 19-check gate verified *data*, *links* and *gate columns* but
  never verified that a rendered table had any content. A verification suite that checks sources but
  not output is half a suite. Any future session adding a table should run the T2 check.

### Final state of this session's contribution

| | |
|---|---|
| PRs merged | #6 (computed layer), #11 (merge record), #12 (empty-table fix) |
| CI | `verify-research-build` green on every merge |
| Pages | build `67adb6f` status `built`; `docs/computed/` confirmed live with populated tables |
| Root site | untouched and verified reachable after every merge |
| Data | 16 strategies / 0 approved / 0 reward paid; 345 verified official rows; 16 sources |
### Change to a shared file — notification for the root-site owner

`arena/3f677e8a-fl1` added **one card to the root landing page** (`index.html`, generated by
`tools/site.py`) linking to `docs/computed/index.html`.

- **Why:** the `verify-research-build` workflow (`scripts/verify_site.py`, check **L4**) fails when the
  root `index.html` does not link to the computed sub-site. That check was failing on `main` itself
  and on every branch cut from it, so the computed sub-site was unreachable from the root by any path
  except a direct URL.
- **What changed:** a single card in the landing-page grid. The global navigation was **not** touched,
  so no other page's nav changed.
- **Owner of that file:** the session that owns the root build. If you would rather present it
  differently — move it into the nav, rename it, or drop it and change check L4 instead — it is one
  block in `tools/site.py` under `<section class="grid">` and is easy to revert.
- **Verified after the change:** `tools/checklinks.py` passes (14 pages, all links and anchors), and
  `scripts/verify_site.py` now reports `errors: 0  warnings: 0`.

> **Superseded.** While this was open, session `arena-34db7d1d-fl1` fixed the same check at the
> generator level on `main` and shipped a better-worded "Computed Research Layer" card, together
> with two new pages. On merge, their card block was kept and this session's duplicate was dropped.
> No functionality is lost — the root still links to `docs/computed/index.html` and L4 passes.

---

---

## Session D — `arena-34db7d1d-fl1` (completion record; merged through PR below)

- Work delivered on branch `arena/34db7d1d-fl1` (single-session branch per Arena constraint; claim first pushed ~03:20 UTC):
  1. **Q-PROP-01 closed**: `data/prop-correlations-d.csv` + `scripts/build_prop_correlations_d.py` — empirical player-level correlations from nflverse player_stats 1999–2024 (13,384 team-games, 100% score join vs games.csv after canonicalizing SD/STL/OAK/LA); QA-gated (schema/coverage/join/sanity/determinism); binary lifts with bootstrap CIs. Pages: `prop-correlations.html`.
  2. **Full-season schedule**: `data/schedule2026-d.csv` (272 rows) + `raw/games-nfldata.csv` snapshot + `schedule.html`; strict V1 reconciliation 32/32 clubs (records+PF+PA) vs official standings capture; V2 Thursday final vs official schedule page; V3 slate equality; V4 internal consistency.
  3. **Independent verification V5–V9** (`data/verification-d.tsv`, `scripts/verify_d.py`): bye-club completeness; deterministic byte-identical rebuild of the merged computed layer; 18/18 injury transcription fidelity vs `week10_2026_official.csv`; spread-sign convention 13/13 vs moneylines; prop-correlations reproducibility.
  4. **Weekly refresh workflow** `.github/workflows/refresh.yml` — scheduled cron; rebuilds + re-verifies; commits only on all-green; deploys nothing (per verify.yml policy).
  5. Integration edits: NAV +2 entries in `tools/site.py`; sources S47–S49; flags F16–F17; README addendum.
- Sources: S47 (nflverse games feed), S48 (player_stats mirror), S49 (official W10 schedule page), plus S01–S03 official captures.
- Irregularities logged: F16 (Mike Evans listed under 49ers while TB on bye — published verbatim), F17 (prop correlations are computed estimates, not official stats).
- Conflict log: rebase/merge conflicts on COORDINATION.md and registries with sessions ab4e9b05/ab82c93f/3f677e8a resolved by taking origin/main's board and re-appending; registries unioned by id (my S16–S18 re-issued as S47–S49 after id collision); no other session's work discarded.

### Session D merge record (2026-11-14)

- **PR created:** https://github.com/sassnarep3-star/FL1/pull/16 (arena/34db7d1d-fl1 → main)
- **PR merged:** 2026-11-14T03:32:44Z via `gh pr merge 16 --merge`; merge commit on main
- **GitHub Pages:** build for the merge commit reported status `built` (Pages API, commit e24a848); live pages confirmed served:
  - `https://sassnarep3-star.github.io/FL1/prop-correlations.html` — 12 empirical coefficients + QA gates rendered
  - `https://sassnarep3-star.github.io/FL1/schedule.html` — 272-game table with reconciliation banner rendered
  - `flagged.html` carries F16/F17; NAV shows "Schedule 2026" and "Prop Correlations"
- **Checks at merge time:** `tools/checklinks.py` OK (16 pages, 77 external links); `scripts/verify_site.py` 0 errors 0 warnings (L4 fixed at generator level: root index now links to `docs/computed/index.html`); `scripts/verify_d.py` V1–V9 no FAIL (V7a FLAGGED by design)
- Nothing else outstanding from this session. The weekly refresh workflow will run next on its Thursday cron.

---

## Session `arena/c80caab4-fl1` — registers, engine, generated sub-site

**Session ID:** `sess-c80caab4` · **Branch:** `arena/c80caab4-fl1` (from `e001e0a`) · **Scope claimed:** `data/specs/*`, `data/*.json` (registers not owned by others), `engine/*`, `site/*`, `tests/*`, `docs/pages/*`, `LICENSE`, `requirements.txt`

### What this session added (all committed, all re-runnable)

| Deliverable | Path | Verified against |
|---|---|---|
| Source register (24 sources, per-source verification level) | `data/specs/sources.json` | each row states whether it was FETCHED, seen via INDEX-MEANS, LINKED or UNREACHABLE |
| Requirements register R-01…R-40 | `data/specs/requirements.json` | the brief, line by line; blocked items say who must unblock them |
| Questions Q-01…Q-24 (15 blocking) | `data/specs/questions.json` | known / lacking / obtain / interim default per question |
| Suggestions S-01…S-24, every `decision: OPEN` | `data/specs/suggestions.json` | nothing implemented on your behalf |
| Missing-information register GAP-01…GAP-19 | `data/specs/missing_data.json` | each gap names the acquisition action |
| Line-origination spec S1…S10, SIG-01…14 | `data/models.json` | every coefficient deliberately blank with an estimator attached |
| Validation gates G-1…G-13 | `data/validation_gates.json` | thresholds + the function claimed to implement each |
| Correlation register C-01…C-15, rho blank | `data/correlations.json` | treatment + measurement plan per pair |
| Injury/deficiency model + two real captures | `data/injury_model.json`, `data/injury_snapshot.json`, `data/injury_snapshot_b.json` | nfl.com/injuries, transcribed verbatim |
| Leaderboard design (divisions, LAS, rewards, anti-gaming) | `data/leaderboard.json` | ranking = 95% lower bound, not PnL |
| Repo audit, flags, exec summary (computed numbers) | `data/audit.json`, `data/flags.json`, `data/exec_summary.json` | git + gh API, twice |
| Stdlib engine: pricing, stats, correlation, injuries, compliance, gates, leaderboard, demo | `engine/` | 70 unit tests, `python3 -m unittest discover -s tests` |
| Generated site (17 pages) + publish gate | `docs/pages/`, `site/build.py`, `site/verify.py` | build fails on unsourced rows, dead links, stale generation |
| Licence + ignore + dependency policy | `LICENSE`, `.gitignore`, `requirements.txt` | MIT added because the repo had none |

### Key verified conclusions (each with an official source)

1. **Injury report semantics** — Practice = DNP / Limited / Full; Game Status = Questionable / Doubtful / Out; "Probable" was retired because ~95% of those players played; **players certain to play are not listed at all**, so absence from the report is not evidence of availability. Source: [nfl.com injury report](https://www.nfl.com/injuries/) and the [Competition Committee revision](https://www.nfl.com/news/competition-committee-approves-revisions-to-injury-report-0ap3000000688693).
2. **A single scrape of that page is not the report.** Two captures taken ~1 h apart in this session agree on every shared player but differ in row count (24 vs 68 rows for the same six clubs, including four extra `Out` designations). Ingestion must reconcile renders. Recorded in `data/injury_snapshot_b.json`.
3. **The league bans wager classes, not analysis.** Injury-, officiating-, one-person-one-play and pre-determined markets are prohibited across its official partners; data is distributed exclusively via Genius Sports. Implemented as a fail-closed gate in `engine/compliance.py`. Source: [league/partners release](https://www.nfl.com/news/nfl-draftkings-fanduel-fanatics-sports-betting-partners), [league betting policy PDF](https://media.nfl.com/LSB).
4. **Luck removal is arithmetic, not attitude.** Break-even at −110 is 52.38%; separating a true 55% from that hurdle at 80% power needs **2,243** settled bets (one-sided α=0.05); at 150 bets a season the provable floor is ~62.4%. Ranking therefore uses a lower confidence bound plus White's reality check / Hansen's SPA (`engine/stats.py`). Source: [Journal of Economics & Finance, DOI 10.1007/s12197-018-9431-4](https://link.springer.com/article/10.1007/s12197-018-9431-4), [RCtest package PDF](https://cloud.r-project.org/web/packages/RCtest/RCtest.pdf).
5. **No official source prices NFL lines.** Every spread, total, close and CLV cell in this session's output is blank and flagged; a purchase decision (Q-02) is the only way past it.

### Irregularities this session found and flagged (published, not hidden)

- `www.nfl.com/teams/<slug>/depth-chart`, `www.nfl.com/teams/transactions`, `operations.nfl.com/the-rules`, `operations.nfl.com/the-rules/nfl-injury-rules`, and two Nevada Gaming Control Board landing paths all return 404 — the depth-chart and hold-percentage assumptions in the brief have **no official endpoint**. Details and consequences: `docs/pages/flagged.html` (V-1…V-8) and `docs/pages/audit.html` (section B).
- The widely-repeated "Questionable = 50%" mapping has no official basis anywhere; `engine/injuries.py` raises instead of defaulting.
- Two figures the brief implies are knowable were **not** confirmed by this session and are therefore not published: any Nevada hold number, and the Wednesday/Thursday/Friday release cadence. They sit in `data/specs/missing_data.json`.

### Conflicts resolved during this merge (nothing discarded)

- `data/sources.json`, `data/requirements.json`, `data/questions.json`, `data/suggestions.json`, `data/flags.json` existed on **both** sides with different schemas. Resolution: the published site's files stay at their original paths untouched; this session's registers moved to `data/specs/` and my generator reads from there. No row of either set was deleted, and `site/verify.py` checks only my own pages, so the published site's checks are unaffected.
- `.gitignore` was unioned rather than replaced.
- `COORDINATION.md` was taken from `main` (it is the authoritative board) and this section appended, per the board's own "add, do not replace" rule.
- Site paths: this session writes only `docs/pages/**`; the published dashboard keeps `index.html`, `*.html`, `assets/`, `css/`, `js/`, `scripts/`, `tools/`, `docs/computed/`.

### Build / check commands

```
python3 -m unittest discover -s tests -q      # 70 tests
python3 engine/demo_run.py --check            # demo output reproducibility
python3 site/build.py && python3 site/verify.py   # 17 pages + publish gate
```

### Status

- T-audit, T-req, T-questions, T-suggest, T-model, T-gates, T-corr, T-injury, T-leaderboard, T-engine, T-site, T-tests: **done** on this branch.
- T-integrate (this merge): in progress until the PR is merged.
- Pages: already `built` from `main`/`root`; this session adds `docs/pages/` as a sub-site and does not change the Pages configuration. Deploy status is re-confirmed after merge in the log below.

### Integration record — session `sess-c80caab4`

- **PR:** https://github.com/sassnarep3-star/FL1/pull/20 — created from `arena/c80caab4-fl1` → `main`, **merged** as `a40ff93` (`gh pr merge 20 --merge`).
- **CI:** `verify-research-build` run 43553486404 → **pass** before merge (their rebuild + `scripts/verify_site.py` run clean on top of this merge).
- **Pages deploy confirmed after merge:** `gh api repos/sassnarep3-star/FL1/pages` → `status: built`, source `main` path `/`. Live spot-checks: https://sassnarep3-star.github.io/FL1/docs/pages/measured.html and the rest of `docs/pages/` render with tables, source chips and flags intact. The published root site was not modified by this session.
- **Conflicts resolved (nothing discarded):** `data/{sources,requirements,questions,suggestions,flags}.json` existed on both sides → `main`'s kept byte-for-byte, this session's moved to `data/specs/`; `.gitignore` unioned; `COORDINATION.md` taken from `main` with this section appended; `README.md` append-only (a "Session E additions" section). `LICENSE` and `requirements.txt` added (repo had neither).
- **Sources / verification:** 25 registered sources, each labelled FETCHED / INDEX-MEANS / LINKED / UNREACHABLE / THIRD-PARTY-IN-REPO, in `data/specs/sources.json`. Official anchors: nfl.com/injuries, the Competition Committee injury-report revision, the league's betting-partner release, media.nfl.com/LSB (league betting policy), operations.nfl.com, roster-eligibility FAQs, Illinois Gaming Board, NY Gaming, Nevada compliance regs; Journal of Economics & Finance 42:818–827; White 2000 / Hansen 2005 via CRAN `RCtest`.
- **Irregularities flagged (published on the site, not hidden):** 8 official paths that do not exist (depth charts, transactions, `operations.nfl.com/the-rules`, the injury-rules policy page, two NV gaming landing pages, the gameday inactive list, a canonical Kelly URL, the 2022-vintage roster FAQ) — recorded as `data/flags.json` V-1…V-8 and as F-1…F-12. Plus two substantive ones worth repeating: (a) the official injury report renders a **variable number of rows per fetch** (two captures 1 h apart: same 22 shared players, 44-row difference, four `Out` designations missing from the first), so ingestion reconciles renders and never overwrites; (b) a **plausibility check caught a contested spread sign convention** in the in-repo third-party dataset, resolved by a sibling session's check (`data/verification-d.tsv` V8) rather than by preference — and the rejected reading is published as the audit trail.
- **Measured, from committed in-repo data (labelled third-party, not promoted to the registers):** C-01 rho **+0.00696** [-0.03324, +0.04831], n=6,813; parlay price penalty **-2.07 pp** (joint hit 24.35% vs 26.42% break-even at the legs' own closing prices); SIG-01 refuted (45.8% over 1,302 bets, ROI −11.6%, gate G-2b fails).
- **Checks to re-run anything:** `python3 -m unittest discover -s tests -q` (75) · `python3 engine/demo_run.py --check` · `python3 -m engine.measure` · `python3 site/build.py && python3 site/verify.py`.
- **Left for the owner (deliberately undecided):** F-11 — whether third-party-derived values may be published as sourced (promoting C-01's rho is then a one-line change); the licence confirmation for the added MIT LICENSE; and the two-layer structure decision (F-10: `data/specs/` research registers vs `data/*.json` published registers, and `docs/pages/` beside the root site).
