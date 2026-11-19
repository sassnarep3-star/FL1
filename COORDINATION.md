## Task board — session `arena/7ac4e12e-fl1` (2026-11-17 — dated re-reads + answers layer + Week-10 close-out)

**Session ID:** `arena-7ac4e12e-fl1` · **Branch:** `arena/7ac4e12e-fl1` (from `5a076a0` of `main`, PR #48 merged) ·
**Claimed:** 2026-11-17T02:34Z · **Status:** active.
**Pre-claim sweep:** `gh pr list --state open` → none; `origin/main` = `5a076a0` = branch base; no session has
work in flight, so every scope below is free. Shared files (`tools/site.py`, `data/sources.tsv`,
`data/flags.json`, `data/questions.json`, `EXECUTIVE_SUMMARY.md`, `COORDINATION.md`) are touched only as
logged here, per the standing additive rule.

| # | Task | Status | Owner | File scope (claimed) |
|---|------|--------|-------|----------------------|
| H1 | Coordination claim + immediate push | done (30da5d7) | `arena-7ac4e12e-fl1` | `COORDINATION.md` |
| H2 | Dated read 3 of the official injury hub (2026-11-17, clock-bracketed) parsed with the shared grammar; publish the **read-3 delta** (added / changed / removed) against the 2026-11-16 read — delta, never the level | done (e5ef4af) | `arena-7ac4e12e-fl1` | `raw/injuries-week10-2026-read3.md` (new), `scripts/build_injury_hub_delta.py` (extend to read 3), `data/injury_hub_delta.json`, `data/sources.tsv` (next S id), generated `injuries.html`, `tests/test_injury_delta_h.py` (new) |
| H3 | Week 10 close-out: official re-read of the week-10 schedule page (are all 13 games FINAL?) plus a fresh standings read to corroborate; extend the published finals extension with SNF/MNF now that they are final; publish the delta and update flag F61's detail. Canonical `data/results.tsv` / `data/standings.tsv` **not** touched (promotion remains Q44's owner decision) | done (1ad7387) | `arena-7ac4e12e-fl1` | `raw/schedule-results-2026-week10-complete.md` (new), `raw/standings-2026-20261117.tsv` (new), `scripts/build_week10_extension.py` (extend), `data/week10_results_extension.json`, `data/flags.json` (F61 detail append), `data/sources.tsv` (next S ids), generated `verified-results-feed.html` |
| H4 | **Answers layer on the open-questions register**: every Q row gains an evidence-backed answer state — either an answer now (citing the verified evidence that settles it) or an explicit OPEN state naming the exact decision/data that would answer it and who must supply it; rendered as a new column on `questions.html` with a per-page answered/open count | done (0620bff) | `arena-7ac4e12e-fl1` | `data/questions.json` (append `answer` + `answer_state` fields to all 45 rows), `tools/site.py` (questions section only), generated `questions.html`, `tests/test_questions_h.py` (new) |
| H5 | Registers append, exec-summary/README addendum, full verification battery, coordination completion record, PR → `main`, merge without waiting, confirm GitHub Pages deploy | done (PR #55) | `arena-7ac4e12e-fl1` | `data/{flags,suggestions}.json`, `data/sources.tsv`, `EXECUTIVE_SUMMARY.md`, `README.md`, `COORDINATION.md`, PR |

**First push = this claim, per the brief.**

### Integration record — H5 (2026-11-17, UTC)

- **PR:** https://github.com/sassnarep3-star/FL1/pull/55 (`arena/7ac4e12e-fl1` → `main`), titled
  "H1-H5: dated injury read 3 (delta), Week-10 close-out (13 finals + live MNF, C1-C5), answers for
  all 46 questions, reconciliation over PRs #49/#51-54".
- **Merge:** `gh pr merge 55 --merge` — state `MERGED` at 2026-11-17T03:26:52Z, merge commit
  `c592121cad9dc360293b18d4ab8e0463e98789d6` on `main`.
- **GitHub Pages:** status went `building` → **`built`** after the merge. Live verification:
  `questions.html` prints "46 questions … answers dated 2026-11-17: 12 answered, 16 partial, 18 open"
  with the dated Answer column; `verified-results-feed.html` prints the Close-out read (13 finals,
  PIT 18–CIN 38 with S95, live MNF row with blank scores); `injuries.html` prints Read 3 (2026-11-17)
  with S94 and the single-change delta; `flagged.html` carries F61's dated correction and F70;
  `suggestions.html` carries SG50/SG51; `sources.html` lists S94–S96.
- **Battery at merge:** 344 tests OK · 57 pages · checkrows 6,976 rows, 0 unsourced · checklinks OK ·
  drift 19/19 · verify_results / verify_injuries OK · verify_site 0 errors, 0 warnings.
- **Still open (non-blocking):** MNF LAC at BAL pending its Final re-read (their F67); Q44 promotion
  rule (SG51); Q42 cadence/terms (SG50); all other `open`/`partial` answers as listed on
  `questions.html`. Nothing was marked verified without an official source link.

**Reconciliation note (2026-11-17, after H4).** While this session worked, `main` advanced through PRs
#49 (session `arena/e97f05c3-fl1` — Week-10 SNF final ingested as dated results files, MNF kept out and
registered as F67) and #51–#54 (sessions `arena/2493a657-fl1`, `arena/d50423eb-fl1` — Q&A exports, Q46,
row-citation audit, Week-11 schedule). This branch was rebased onto `origin/main` with conflicts resolved
keeping **both** sides: their `S89–S93 / F67–F69 / SG48–SG49 / Q46` were already on `main`, so this
session's ids shifted to **`S94–S96` (injury read 3, schedule close-out, standings close-out), `F70`
(Q45 duplication), `SG50`/`SG51` (cadence automation, frozen promotion rule)**; every reference, pin and
drift row was rewritten to match and the full battery re-ran green afterwards (344 tests, 57 pages,
19/19 drift pins). The answers layer covers all 46 questions (45 original + their Q46).

## Task board — session `arena/e97f05c3-fl1` (2026-11-17) — COMPLETE

**Session ID:** `arena-e97f05c3` · **Branch:** `arena/e97f05c3-fl1` (from `5a076a0` of `main`) ·
**Claimed:** 2026-11-17 (UTC). **Branch note:** this session is bound to the single branch named above, so the
per-task `session-<id>/<task>` branches in the brief are not used; claims are recorded here on that branch instead.

| ID | Task | Status | Owner | File scope |
|----|------|--------|-------|------------|
| H0 | Claim + push this block | done | `arena-e97f05c3` | `COORDINATION.md` |
| H1 | Week 10 Sunday-night final (PIT 18 at CIN 38) ingested from the official Game Center; reconciled against the live official standings; Monday-night game (LAC at BAL) kept **unrecorded** because it was still live (Q2, 17–7) at read time | done (MNF open → F67) | `arena-e97f05c3` | `data/results_2026-11-17.tsv`, `data/standings_2026-11-17.tsv`, `data/verification-2026-11-17.tsv`, `raw/results-week10-2026-2026-11-17.md`, `scripts/verify_results_2026_11_17.py`, `tests/test_results_2026_11_17.py`, `data/sources.tsv` (append S89–S91 only), `data/flags.json` (append F67 only), `data/raw/MANIFEST-h.json`, `tools/site_g.py` (one additive row in the Snapshot Ledger results table), `data/verification-2026-11-17.tsv` |
| H2 | Integration: build, tests, link check, PR to `main`, merge, Pages check | done | `arena-e97f05c3` | PR + this record |

### Integration record — H2 (2026-11-17, UTC)

- **PR:** https://github.com/sassnarep3-star/FL1/pull/49 (`arena/e97f05c3-fl1` → `main`), CI check `verify` = pass
  (run 44004284596), mergeability `MERGEABLE / CLEAN`.
- **Merge:** `gh pr merge 49 --merge` at merge commit `09c5257` on 2026-11-17T02:37:43Z.
- **GitHub Pages:** source `main` / path `/`, legacy build → status **`built`** (build 1376553096, no error).
  Live check: https://sassnarep3-star.github.io/FL1/flagged.html shows **67 items** including F67;
  https://sassnarep3-star.github.io/FL1/availability-ledger.html shows the 2026-11-17 results row (149 results, S89).
- **Still open, not blocking (Flagged for Review, F67):** Monday night LAC at BAL. Re-read the official Game Center
  page after it shows Final, then add it in a new dated results file.
- **Scope honesty:** the rest of the brief (for example the 32-team sweep, the depth-source routes, the ablations)
  was **not** re-verified in this session; those rows keep the status earlier sessions published. Nothing in this
  session marks them verified.

### Completion record — H1 (2026-11-17, UTC)

**What was added.** One official final: **Steelers (PIT) 18 at Bengals (CIN) 38**, Week 10, Sunday 2026-11-15,
Paycor Stadium. Recorded in `data/results_2026-11-17.tsv` (149 rows; the 2026-11-16 read had 148). Every other
row is byte-identical to the 2026-11-16 read.

**What was not added, and why.** Monday night **LAC at BAL** was *Live* at read time (Q2 01:56, Chargers 17, Ravens 7).
A live score is not a result, so it is not in any results file. It is registered as open item **F67** with
source **S91**, and it must be re-read after it shows Final.

**Sources (each links to the official page):**
- S89 Game Center, PIT at CIN, status Final: https://www.nfl.com/games/steelers-at-bengals-2026-reg-10 (quarter scores PIT 0-3-0-15, CIN 3-21-7-7; each sums to the total)
- S90 Official standings, read 2026-11-17, all 32 clubs: https://www.nfl.com/standings/league/2026/REG
- S49/S81 Official Week 10 schedule page (shows "Steelers 18, Bengals 38, FINAL"): https://www.nfl.com/schedules/2026/REG10/
- S91 Game Center, LAC at BAL, Live (not recorded): https://www.nfl.com/games/chargers-at-ravens-2026-reg-10?tab=live

**Verification performed (all re-runnable):**
- `python3 scripts/verify_results_2026_11_17.py` → GATE PASS: H-R1 (new = old + one row), H-R2 (results reproduce the
  new official standings for 32/32 clubs on W/L/T/PF/PA), H-R3 (games = W+L+T for every club), H-R4 (the change between
  the 2026-11-16 and 2026-11-17 standings is exactly this game; only CIN and PIT move, by 38/18 points and one win/loss),
  H-R5 (frozen 137-game corpus still a prefix).
- `python3 -m unittest discover -s tests -q` → 315 OK (6 new in `tests/test_results_2026_11_17.py`).
- `python3 tools/build.py && python3 tools/site.py && python3 tools/checklinks.py` → every internal link and anchor resolves.
- `/tmp/ci-venv/bin/python scripts/verify_site.py` (pandas venv, as CI does) → errors 0, warnings 0.
- `python3 tools/checkrows.py` → 43 pages, 6,293 rows audited, every data row sourced.
- `python3 tools/verify_drift.py` → 19 pins, 19 PASS. DR-10 (flags 66→67) and DR-14 (sources 80→83) were re-pinned on purpose.

**Irregularities found (published on Flagged for Review as F67, and below):**
1. **Monday night LAC at BAL is unrecorded and open** (F67). It is the only Week 10 game without a result.
2. **Source-ID collision avoided.** The brief's next free IDs were S87/S88, but both were already taken on `main`
   (S87 = repo capture manifest, S88 = 2025 standings). This session used S89–S91 instead.
3. **Branch-naming conflict.** The brief asks each task to go on its own `session-<id>/<task>` branch. The session
   branch note allows only `arena/e97f05c3-fl1`, so all work is on that single branch, and claims are logged here.
4. **Pinned-count tests changed on purpose.** `tests/test_n01_n05.py` (sources 80→83) and the drift pin for
   `data/flags.json` (66→67) were updated. This is the drift alarm working, not a silent change.
5. **Scope not re-verified.** This session did not re-verify the rest of the brief (for example the 32-team depth
   sweep, or the availability ledger). Those items keep the status their earlier sessions published.

**Files changed:** `data/results_2026-11-17.tsv`, `data/standings_2026-11-17.tsv`, `data/verification-2026-11-17.tsv`,
`data/raw/MANIFEST-h.json`, `raw/results-week10-2026-2026-11-17.md`, `scripts/verify_results_2026_11_17.py`,
`tests/test_results_2026_11_17.py`, `tests/test_n01_n05.py` (count pin), `tools/verify_drift.py` (pin),
`tools/site_g.py` (one row in the Snapshot Ledger), `data/sources.tsv` (S89–S91), `data/flags.json` (F67),
regenerated site pages and `assets/js/data.js`.
## Task board — session `arena/a502c4e0-fl1` (2026-11-17) — Week-10 promotion (Q44) + freshness sweep

**Session ID:** `arena-a502c4e0` · **Branch:** `arena/a502c4e0-fl1` (from `5a076a0` of `main`) ·
**Claimed:** 2026-11-17T02:35Z · **Status:** active. Work is additive; registers appended, never
replaced; shared/generated files rebuilt through the standard builders after my scoped edits.

| # | Task | Status | Owner | File scope (claimed) | Sources / verification | Irregularities |
|---|------|--------|-------|----------------------|------------------------|----------------|
| C0 | Coordination claim + immediate push | done | arena-a502c4e0 | `COORDINATION.md` | — | — |
| C1 | Week 10 closeout + Q44 promotion **acceptance run**: fresh official read of the week-10 page and league standings once all games reach FINAL; closeout gates P1–P8 (`scripts/promote_week10.py`, new) run against the captures; dated side-reads published (`data/results_2026-11-17-closeout.tsv`, `data/standings_2026-11-17-closeout.tsv`) byte-chained after session e97f05c3's same-day 149-row SNF read; **canonical `data/results.tsv`/`data/standings.tsv` roll-forward deliberately NOT executed** — that half of Q44 is the owner's policy choice (refit would move every published model coefficient; the runner's `--promote` prints the full rebuild/verify sequence). Resolves open flag F67 (the prescribed re-read of the Monday-night game after Final). Scope note recorded here per the claim rule. | done | arena-a502c4e0 | `raw/schedule-results-2026-week10-closeout.tsv` (new), `raw/standings-2026-20261117.tsv` (new), `data/week10_closeout.json` (new), `scripts/promote_week10.py` (new), `data/results_2026-11-17-closeout.tsv` (new), `data/standings_2026-11-17-closeout.tsv` (new), generated `verified-results-feed.html`; **not** `data/results.tsv`/`data/standings.tsv`/`data/week10_results_extension.json`/`data/results_2026-11-17.tsv`/`data/standings_2026-11-17.tsv` | official https://www.nfl.com/schedules/2026/REG10/ and https://www.nfl.com/standings/league/2026/REG, fetched this session; P1–P8 in the runner | scope deviation vs original claim: staged closeout instead of canonical promotion — Q44 policy half left open; register-slip flag is F70 (renumbered after main took F67–F69) |
| C2 | Fresh injury-hub read with clock time (2026-11-17) + published delta vs the 2026-11-16 read; never the level | done | arena-a502c4e0 | `raw/injuries-week10-2026-read4.md` (new), `data/injury_hub_delta.json`, `scripts/build_injury_hub_delta.py` (read-only + new read arg), generated `injuries.html` | official https://www.nfl.com/injuries/ | — |
| C3 | Full verification sweep on the final tree: unit tests, build, link check, row-sourcing check, injury/result verifiers | done | arena-a502c4e0 | none (read-only runs; results recorded in this board) | repo tooling | — |
| C4 | Registers append (new sources, any new flags, Q44 answer/resolution), executive-summary touch, coordination completion record | done | arena-a502c4e0 | `data/{sources.tsv,flags.json,questions.json,suggestions.json}`, `EXECUTIVE_SUMMARY.md`, `COORDINATION.md` | each appended row carries its official URL | — |
| C5 | Final integration: PR → `main`, merge without waiting for review, confirm GitHub Pages deploy, record PR link + merge result here | claimed | arena-a502c4e0 | PR + this record | gh + Pages API | — |

**Notes:** MNF (LAC at BAL) was live in Q2 at claim time (2026-11-17T02:33Z official read) — a live
score is not a result, so C1 waits for the official FINAL before any promotion, exactly as Q44
prescribes. No other session has an open PR or an un-stale claim on these files (latest merged tip
`5a076a0`, PR list empty as of claim time).

**Shared-file notice:** this session appends to `tools/site.py` (new closeout + read-3 injury
sections; the file's own header already requires appending sections rather than rewriting), to
`data/sources.tsv` (**S97–S99** — renumbered twice: main took S89–S93 mid-session, session 7ac4e12e then took S94–S96),
`data/flags.json` (**F71–F72** — renumbered after main took F67–F69 and 7ac4e12e took F70), `data/questions.json`
(Q44 fields only), and `tools/verify_drift.py` (DR-10 pin → 72). `data/results.tsv`,
`data/standings.tsv`, `data/week10_results_extension.json`, `data/results_2026-11-17.tsv` and
`data/standings_2026-11-17.tsv` (session e97f05c3) stay untouched (C1 scope note above).
`tools/site_g.py` gets one additive Snapshot-Ledger row for the closeout read (mirrors the
row session e97f05c3 added for the 149-row read).
Mid-session rebase onto `22482a9` (PRs #49–#54) completed with conflicts resolved in
`COORDINATION.md`, `data/sources.tsv`, `data/flags.json`, `tools/verify_drift.py`.

### Completion record — C0–C4 (2026-11-17, UTC)

- **C0** claim `c9a1493` pushed at claim time (main was `5a076a0`, PR list empty).
- **C1 closeout + Q44 acceptance run.** Monday-night final confirmed on the official Game
  Center (LAC 23 BAL 20, "Final", quarter scores 10-7-3-3 / 0-10-3-7). Clock-bracketed
  reads → `raw/schedule-results-2026-week10-closeout.tsv` (S98, 14/14 FINAL) and
  `raw/standings-2026-20261117-closeout.tsv` (S99, post-MNF 32 clubs; league route stale at four
  post-final reads — see F72, division route fresh). `scripts/promote_week10.py` gates
  **P1–P8 ALL PASS** (`data/verification-promote.tsv`); `--execute` published
  `data/results_2026-11-17-closeout.tsv` (150 rows, byte-chained after e97f05c3's 149-row
  read) + `data/standings_2026-11-17-closeout.tsv`; register `data/week10_closeout.json`.
  **Canonical `data/results.tsv`/`data/standings.tsv` NOT promoted** (scope note above; Q44
  policy half). Open flag **F67 resolved** by the prescribed re-read (annotation appended;
  their 149-row read and gate files untouched — their H-gate still GATE PASS).
- **C2 injury read 4** — `raw/injuries-week10-2026-read3.md` (window 02:33:27Z–02:43:50Z,
  347 rows/28 clubs), `delta` (read 3 → read 4) = 2 practice changes / 0 added / 0 removed, source S97,
  N03 tests updated (3 reads), site section renders both deltas.
- **C3 verification sweep (final tree):** 342 tests OK; build+site+checklinks (57 pages)
  + checkrows (7,046 rows) green; verify_results 32/32; verify_results_g PASS;
  verify_results_2026_11_17 GATE PASS (untouched); verify_injuries OK; verify_drift 19/19
  (DR-10 → 71, DR-08 → 46); verify_brief 10/10; verify_site 0/0 (CI pandas venv);
  CI six-builder rebuild byte-identical.
- **C4 registers:** sources **S97** (injury read 4), **S98** (closeout schedule), **S99**
  (post-MNF standings) — 91 rows; flags **F71** (Q44/SG43/F59 cross-reference slip;
  Q44 recommended_path corrected to SG43), **F72** (league-route staleness), F67 annotated
  RESOLVED; Q44 what_we_know/missing_data updated with the delivered acceptance run;
  DR pins re-pinned on purpose (flags 67→71 as entries landed, questions 45→46 by main);
  EXECUTIVE_SUMMARY new current block; README promote_week10 entry; Snapshot-Ledger row
  for the 150-row read; tests/test_promote_week10.py guards the staged state (150 closeout,
  149-prefix chain, canonical untouched at 137/137 played).

---

## Task board — session `arena/dbf11de0-fl1` (2026-11-16) — COMPLETE

**Session ID:** `arena-dbf11de0` · **Branch:** `arena/dbf11de0-fl1` (from `ebf20eb` of `main`) ·
**Claimed:** 2026-11-16 (UTC) · **Status:** complete — merged to `main`, Pages deploy confirmed
(record at the end of this block).

| ID | Task | Status | Owner | File scope |
|----|------|--------|-------|------------|
| G0 | Coordination claim + immediate push | done | `arena-dbf11de0` | `COORDINATION.md` |
| G1 | Live official re-capture of the Week 10 2026 injury report, line-by-line diff, plus a dated results/standings read | done | `arena-dbf11de0` | `raw/injuries-week10-2026-recapture-2026-11-16.md`, `raw/results-week10-2026-2026-11-16.md`, `data/injuries_2026-11-16.tsv`, `data/results_2026-11-16.tsv`, `data/standings_2026-11-16.tsv`, `data/injury_diff_g.tsv`, `data/verification-g.tsv`, `scripts/verify_recapture_g.py`, `scripts/verify_results_g.py` |
| G2 | Requirement backlog: every brief line registered with the gate that blocks it and the number that clears it | done | `arena-dbf11de0` | `data/requirements_backlog.{csv,json}`, `scripts/build_backlog_g.py`, `requirements-backlog.html` |
| G3 | Decision-readiness table on the landing page (one row per requirement) | done | `arena-dbf11de0` | `tools/site_g.py`, `index.html` (section `#decision`) |
| G4 | Removal-of-luck panel | done | `arena-dbf11de0` | `engine/luck.py`, `tests/test_luck_g.py`, `scripts/build_luck_g.py`, `data/luck_panel.json`, `removal-of-luck.html` |
| G5 | Per-team availability view: starters out, replacement named, net injury count | done | `arena-dbf11de0` | `scripts/build_availability_g.py`, `data/team_availability.csv`, `data/starters_out_detail.csv`, `team-availability.html` |
| G6 | Announced-starter evidence field + registers | done | `arena-dbf11de0` | `data/announced_starters.{csv,json}`, `announced-starters.html`, `availability-ledger.html`, `scripts/register_g.py`, `data/{flags,questions,suggestions}.json`, `data/sources.tsv` |
| G7 | Final integration: PR → `main`, merge, Pages confirmed | done | `arena-dbf11de0` | PR + this record |

### What the official sources said (each claim links to the page)

| Check | Result | Source |
|---|---|---|
| Injury report re-read two days later | 345 rows (2026-11-14) → 347 rows (2026-11-16); 2 rows added, 32 fields moved | https://www.nfl.com/injuries/ |
| No published row missing from the later read | 0 missing (so the published table holds no invented row) | https://www.nfl.com/injuries/ |
| Kerby Joseph / Cade Mays / D.J. Reed game status | all three published **Out** on the official page | https://www.nfl.com/injuries/ |
| Results and standings re-read | 137 → 148 results; the new read reproduces the new official standings for 32/32 clubs on W, L, T, PF, PA | https://www.nfl.com/schedules/2026/REG10/ , https://www.nfl.com/standings/league/2026/REG |
| Announced starters (quoted, dated, linked) | 11 rows from 3 official pages | S77, S78, S79 (`sources.html`) |

Two games were deliberately **not** recorded: the Sunday-night game (PIT at CIN) was in the first
quarter at capture time and the Monday-night game (LAC at BAL) had not kicked off. A partial score
is not a result.

### Verification performed at completion (all re-runnable, all green)

`python3 -m unittest discover -s tests -q` → **267 OK** · `tools/build.py` clean ·
`tools/verify_injuries.py` → 345/345 · `tools/verify_results.py` → PASS 32/32 ·
`tools/checklinks.py` → **41 pages**, every link and anchor resolves ·
`tools/checkrows.py` → **41 pages, 5,963 rows**, every row sourced ·
`scripts/verify_recapture_g.py` → GATE PASS (G-V1..G-V7) ·
`scripts/verify_results_g.py` → PASS (G-R1..G-R4).

### Irregularities this session found (published on Flagged for Review)

F53 injury row-count discrepancy (254/279 claimed; 345 and 347 measured) · F54 Brissett
announced-starter evidence not found · F55 the official report moved between two dated reads ·
F56 depth-chart register carries no capture date on 31/31 rows · F57 venue/roof/surface only from a
third-party feed · F58 model outputs store a line, not a probability with inputs · F59 published
standings/results predate eleven finals · F60 two source registers share the S-number space with
different meanings.

### Merge reconciliation with `origin/main` (140 commits, PRs up to #42)

`main` had moved 140 commits ahead while this session worked. The merge conflicted in 27 files.
Nothing from either side was discarded:

- **Generated pages (23 HTML files + `assets/js/data.js`)** — resolved to `main`'s version and then
  regenerated from the merged sources, because they are build artefacts, not hand-edited content.
- **`tools/site.py`** — auto-merged cleanly; this session's five NAV entries and its `site_g`
  wiring are intact.
- **Registers (`flags`, `questions`, `suggestions`, `sources.tsv`)** — `main` had independently
  allocated ids that collided with this session's (`F43`–`F50`, `Q35`–`Q38`, `SG36`–`SG38`,
  `S70`–`S72`). Rather than overwrite either side, this session's rows were **renumbered** to
  `F53`–`F60`, `Q40`–`Q43`, `SG39`–`SG42`, `S77`–`S79` and appended. Their content is unrelated to
  mine (theirs concern price feeds and line vintages; mine concern official availability data), so
  both sets stand. Cross-references inside my rows were updated to the new ids.
- **`COORDINATION.md`** — `main`'s version taken as the base and this block prepended, so no other
  session's record was lost.

### Integration record (G7)

**PR:** https://github.com/sassnarep3-star/FL1/pull/44 (`arena/dbf11de0-fl1` → `main`) —
**merged** with `gh pr merge 44 --merge` at merge commit
`4f6ee975b6534f17c230a5b1afb35e0bd3ff7e36` on 2026-11-16T01:49:46Z, after both
`verify-research-build` checks reported SUCCESS and GitHub reported `MERGEABLE / CLEAN`.

**GitHub Pages:** build triggered 2026-11-16T01:49:47Z → status **`built`**
(`gh api repos/sassnarep3-star/FL1/pages`; source `main`, path `/`). The site is live at
https://sassnarep3-star.github.io/FL1/ .

**Live re-fetch after deploy (page fetch, not curl):** `removal-of-luck.html` and
`availability-ledger.html` were re-read from the live origin and render correctly — headline
numbers, the luck bands by sample size, the sizing grid, the two dated captures with the 347-row
sha256, the 35-row diff, and every check row with its own official source link.

**Post-merge follow-up:** one small PR corrected the verification table so each check row links to
its own official URL rather than a shared one (the G-R* checks now point at the schedule/standings
page instead of the injury page).

**Final state on `main`:** 41 pages; 267 unit tests OK; `tools/build.py` clean;
`tools/verify_injuries.py` 345/345; `tools/verify_results.py` PASS 32/32; `tools/checklinks.py`
41 pages; `tools/checkrows.py` 41 pages / 5,963 rows; `scripts/verify_recapture_g.py` GATE PASS;
`scripts/verify_results_g.py` PASS (G-R1..G-R4). 60 flags, 43 questions, 42 suggestions,
71 sources, 87 requirement rows.

**Open items, all published on Flagged for Review and none blocking:** F53–F60 as listed above.
The decisions that would unblock the most work are **Q40** (which dated read a backtest may pin),
**Q43** (the leaderboard's sample-size bar) and **Q42** (whether the injury report may be captured
at the Wednesday/Thursday/Friday cadence the brief asks for, before the terms question is
answered).

## Task board — session `arena/d50423eb-fl1` (2026-11-17) — LIVE, IN PROGRESS

**Session ID:** `arena-d50423eb` · **Branch:** `arena/d50423eb-fl1` (from `5a076a0` of `main`) ·
**Claimed:** 2026-11-17T02:34Z (UTC) · **Status:** active. Standing rule restated here and followed:
**additive only**. New files added; existing shared files (`tools/site.py`, `data/sources.tsv`,
`data/flags.json`, `data/questions.json`, `data/suggestions.json`, `data/requirements.json`,
`COORDINATION.md`, `README.md`, `EXECUTIVE_SUMMARY.md`, `data/verification*.tsv`) are **appended to**,
never replaced. Registers are deduped on their id key at every append.

| ID | Task | Status | Owner | File scope (claimed) | Sources / verification | Irregularities |
|---|------|--------|-------|----------------------|------------------------|----------------|
| T1 | Element-level verification of live official pages and dated captures | done | arena-d50423eb-fl1 | `raw/live/2026-11-17-*`, `scripts/verify_live_d5.py`, `data/verification-live.tsv` | NFL injury report, standings, Week 10 schedule, Week 11 by-week page; hashes + 11 checks pass | injury delta preserved; F69/Q46 |
| T2 | Decision ledger: questions/flags with known, unknown, gate, clearing number, owner action | done | arena-d50423eb-fl1 | `data/decision_ledger_d5.{csv,json}`, `scripts/build_d5_registers.py`, `tools/pages_d5.py`, `decision-ledger.html` | derived from registers; 113 rows; checkrows passes | clearing criteria blank where unavailable |
| T3 | Reviewable suggestions pipeline | done | arena-d50423eb-fl1 | `data/suggestion_pipeline_d5.{csv,json}`, `tools/pages_d5.py`, `suggestions-pipeline.html` | 49 rows from suggestion register | all remain proposed; no manual approval assumed |
| T4 | Availability and depth evidence matrix | needs review | arena-d50423eb-fl1 | `data/depth_matrix_d5.{csv,json}`, `data/availability_d5.json`, `tools/pages_d5.py`, `availability-matrix-d5.html` | official injury hub + captured club depth sources; exact-name join only | 30/32 chart clubs; charts do not prove actual starters or participation |
| T5 | Strategy scorecard, proper-score engine, controls and qualification gates | done | arena-d50423eb-fl1 | `engine/scoreboard_d5.py`, `tests/test_d5.py`, `data/strategy_scorecard_d5.csv`, `data/scorecard_d5.json`, `scripts/build_d5.py`, `strategy-scorecard.html` | 11 candidate entries; 0 qualified; tests pass | Elo measurement retrospective only; candidate registry hashes not all committed/frozen |
| T6 | Complete questions-and-answers register | done | arena-d50423eb-fl1 | `data/qa_register_d5.{csv,json}`, `tools/pages_d5.py`, `qa-d5.html` | 46 questions; checkrows passes | unresolved decisions explicitly listed |
| T7 | Integration and PR | done | arena-d50423eb-fl1 | PR #53, all site outputs, this record | PR #53 merged; CI verify passed; Pages build 1376581755 / deploy run 44006171014 succeeded | Pending final live URL check |

**Shared files this session will touch (logged before touching):** `tools/site.py` (NAV entries +
index cards + one import call, additive), `data/sources.tsv` (append S93+), `data/flags.json`
(append F69+), `data/questions.json` (append Q46+), `data/suggestions.json` (append SG48+),
`data/requirements.json` (append R29+), `README.md` / `EXECUTIVE_SUMMARY.md` (append a dated block),
`data/verification.tsv` (append rows). **No existing row in any register will be edited or
renumbered.** If a later session needs one of these files mid-run, take `main`'s version and
re-append this block — that is the board's own rule.

### D5 progress — 2026-11-17T02:40Z onward

**Live capture and verification.** Added `raw/live/2026-11-17-{standings-league-reg,week10-finals,week11-slate}.tsv`, the official injury report text `raw/live/2026-11-17-injury-report-week10.md`, and `raw/live/MANIFEST-2026-11-17.json` with SHA-256 and byte counts for all four. `scripts/verify_live_d5.py` independently verifies the hashes, 32 standings rows, 13 Week-10 finals (excludes LAC–BAL, still partial), 13 Week-11 fixtures/six byes, the 347-row injury capture, 0 committed injury rows missing, 2 live-only BAL additions, 16 changed injury rows, SEA/CIN row counts, and results-vs-live-standings reconciliation. It also caught and prevented double-counting the already-committed Thursday game. All checks pass. Sources: `https://www.nfl.com/injuries/`, `https://www.nfl.com/standings/league/2026/REG`, `https://www.nfl.com/schedules/2026/REG10/`, `https://www.nfl.com/schedules/2026/by-week/week-11`.

**D5 scorecard and pages.** Added `engine/scoreboard_d5.py`, frozen candidate registry `data/strategy_registry_d5.json`, `scripts/build_d5.py`, `tools/pages_d5.py`, and generated live-state, availability, scorecard, forecast-ledger and org-health files. The historical Elo output scores n=137 with BSS 0.1021 vs constant-0.5 baseline, 95% game-cluster interval [-0.0120, 0.2215]; it is explicitly retrospective, not prospective, and is not leaderboard eligible. No one of 11 registered entries qualifies. Market spread is not translated into win probability because no validated margin distribution exists. The captured depth data has 30/32 clubs; 108 injury rows have a game designation, 86 have a next listed player in the parsed depth slot (this is not proof of actual entry or starter status). 2,241 singles are the computed 80%-power planning bar for 55% vs 52.38% break-even. No season-long ROI or raw win-rate ranking is used.

**Review registers.** Appended S93 (official Week-11 by-week schedule page), F69 (injury snapshot delta), Q46 (promotion policy), SG48 (immutable snapshot recommendation), and R29 (availability snapshot requirement); no existing register row replaced. The live vs committed injury discrepancy is preserved as a dated snapshot, not silently overwritten.

**Site integration.** Added D5 navigation and dashboard section additively in `tools/site.py`; ten D5 generated pages cover captures, live standings, finals, slate, strategy scorecard, readiness, availability matrix, decision questions, suggestions, and flags. Site now generates 53 pages. `python3 tools/build.py`, `python3 scripts/build_d5.py`, `python3 tools/site.py`, `python3 scripts/verify_live_d5.py`, `python3 -m unittest discover -s tests -q` (316 OK), `python3 tools/checklinks.py` (all internal links/anchors resolve) and `python3 tools/checkrows.py` (56 pages; 6,861 rows audited) pass. The full append-only decision ledger (113 questions/flags), suggestion pipeline (48 rows), Q&A register (46 questions), 252-row exact-join depth matrix, 11-row scorecard, and 4-row capture verification export were generated by `scripts/build_d5_registers.py`; corresponding pages are live in the checked-in site output. R29 is also included in the landing readiness register. Warnings: pre-existing ResourceWarnings from test code; external links are not fetched by checklinks. `scripts/verify_site.py` could not run in this sandbox because pandas is not installed (`ModuleNotFoundError`); no claim of that check passing. No external verification of all 259 outbound links is claimed here.

**PR / CI / deployment:** [PR #53](https://github.com/sassnarep3-star/FL1/pull/53) from `arena/d50423eb-fl1` to `main` merged at `2026-11-17T02:52:48Z`, merge commit `8b8b7b807068d4ee70e9f578a7cb488f03241ded`. `main` advanced with PR #49 during this run; the clean merge in commit `b6abb62` preserved that work, unioned non-conflicting register entries, and re-keyed this session's colliding live source/flag/suggestion additions to S93/F69/SG49 (main's S89–S92 and F67–F68 remain intact). Fresh CI run 44006084490 passed (full rebuild, verification, clean-artifact check). Local full rebuild, 328 tests, live checks, drift pins, links and row audits passed. Local `scripts/verify_site.py` could not run because pandas is absent, but CI verification passed. GitHub Pages build 1376581755 and deployment workflow 44006171014 both succeeded. Final live URL check pending.

### What this session will NOT do

* Not re-derive or overwrite another session's numbers. Where a live page contradicts a committed
  value, the contradiction is published as a flag with both readings and neither is overwritten.
* Not quote a betting price, an odds feed or a "market line" as official. No official NFL price
  source exists (F18 / GAP-01 on `main`); every market cell stays blank and labelled.
* Not transcribe a depth chart by eye. Image-only charts (Texans) stay blank and flagged.
* Not fill a blank to make a table look complete.


# COORDINATION — Shared Task Board

> Read this **before** starting. Claim a task by writing your session ID and file scope, then commit
> and push that claim immediately. Never start a task another session has claimed.

**Repository:** `sassnarep3-star/FL1`
**GitHub Pages:** https://sassnarep3-star.github.io/FL1/ — source `main`, path `/`, legacy build
**Last updated:** 2026-11-16 (UTC) — session `arena-38a78804-fl1` claim added below

## Task board — session `arena/38a78804-fl1` (Week-10 live refresh + brief-gap sprint N01–N06)

**Session ID:** `arena-38a78804-fl1` · **Branch:** `arena/38a78804-fl1` (from `ebf20eb` of `main`) ·
**Claimed:** 2026-11-16T01:20Z · **Status:** active. Work is additive per the standing rule: new files +
appended sections rendered by the shared generator; registers appended to, never replaced. Shared files
touched (`tools/site.py`, `data/sources.tsv`, `EXECUTIVE_SUMMARY.md`, `COORDINATION.md`) are logged here.

| # | Task | Status | Owner | File scope (claimed) | Sources / verification | Irregularities |
|---|------|--------|-------|----------------------|------------------------|----------------|
| N01 | Decision-readiness table on the landing page — one row per requirement R01–R28, the gate that blocks it, the number that would clear it | done | arena-38a78804-fl1 | `data/decision_readiness.json`, `scripts/build_decision_readiness.py`, `tools/site.py` (index section only), generated `index.html` | derived from `data/requirements.json`, `data/questions.json`, `data/flags.json`, `data/sources.tsv`; builder asserts 28/28 coverage and register-id validity | none found |
| N02 | Two-sided "what would change our mind" field on every strategy entry | done | arena-38a78804-fl1 | `data/strategies.json` (field appended to all 6 entries), `scripts/append_change_my_mind.py`, `tools/site.py` (strategies section), generated `strategies.html` | idempotent appender; blocked entries must name the gate | none found |
| N03 | Fresh injury-hub read with clock time + published delta vs the 2026-11-14 read (delta, never the level) | done | arena-38a78804-fl1 | `raw/injuries-week10-2026-read2.md`, `data/injury_hub_delta.json`, `scripts/build_injury_hub_delta.py`, `data/sources.tsv` (S77), generated `injuries.html` | read 1 still re-parses to data/injuries.tsv 345/345 (asserted in the builder AND tools/verify_injuries.py); hub still showed WEEK 10; delta = 32 changed, 2 added (both BAL), 0 removed | Colts Arden Key row cleared between reads (published as a removal-free delta: it is a field change, not a removed row) |
| N04 | Week 10 finals capture — the games FINAL at read time (SNF live / MNF pending left blank and flagged) | done | arena-38a78804-fl1 | `raw/schedule-results-2026-week10-finals.tsv`, `raw/standings-2026-20261116.tsv` (corroborating evidence), `data/week10_results_extension.json`, `scripts/build_week10_extension.py`, `data/sources.tsv` (S78, S79), generated `verified-results-feed.html` | V1 TNF corroborates the feed; V2 fixture match vs published schedule; V3 record arithmetic 32/32 vs page cards; V4 W/L/T **and** PF/PA 32/32 vs fresh official standings. Scope note: the section landed on `verified-results-feed.html`, not `schedule.html` (schedule.html is generated by session D's builder; no overlap) | none found; standings capture is labelled corroborating evidence, does not replace data/standings.tsv |
| N05 | "Removal of luck" panel on the site dashboard | done | arena-38a78804-fl1 | `data/luck_panel.json`, `scripts/build_luck_panel.py`, `tools/site.py` (index section), generated `index.html` | derived read-only from data/leaderboard_signal_staking.json; edge = CI-low − hurdle asserted in tests | dataset is the flagged computed layer (F19/F23/F30 warnings carried verbatim onto the panel) |
| N06 | Registers append, tests, link checks, rebuild, exec-summary update, coordination completion record, PR → main, merge, confirm Pages | done | arena-38a78804-fl1 | `data/{questions,suggestions}.json` (Q40, SG39), `data/sources.tsv` (S77–S79), `tests/test_n01_n05.py` (24 tests), `EXECUTIVE_SUMMARY.md`, `COORDINATION.md`, PR | 192 tests OK; checklinks 28 pages OK; verify_site 0/0; injuries 345/345; results PASS; verify_d V5–V8 PASS + V9 PASS (mirror fetched to /home/user/datawork, outside the repo); demo_run --check current; docs sub-site 18 pages 0 unsourced | V9 required fetching the parquet mirror again — recorded for future sessions |


**Last updated:** 2026-11-16 (UTC) — session `arena-a4c5a1de-fl1` claimed below (stale-PR integration + partial-requirements close-out + final integration)

## Task board — session `arena/a4c5a1de-fl1` (final integration, 2026-11-16)

**Session ID:** `arena-a4c5a1de-fl1` · **Branch:** `arena/a4c5a1de-fl1` (from `ebf20eb` = main tip) ·
**Claimed:** 2026-11-16T00:00Z · **Status:** active.

Handoff basis: open PRs **#38** (market spine, `arena/08fef9e9-fl1`, last activity 2026-11-14T23:06Z) and
**#39** (replacement-depth cross-check, `arena/2fa09442-fl1`, last activity 2026-11-14T23:09Z) have no
commits for >60 minutes and their sessions show no activity — takeover permitted by the stale-claim rule.
Both pass CI (`verify` SUCCESS). Nothing below starts work claimed by a live session.

| # | Task | Status | Owner | File scope (claimed) | Sources / verification | Irregularities |
|---|------|--------|-------|----------------------|------------------------|----------------|
| I1 | Integrate stale open PRs #38 and #39 into main (verify combined tree, resolve conflicts preserving both sides, merge, confirm Pages) | done | arena-a4c5a1de-fl1 | PR operations + `COORDINATION.md` records + conflict resolutions (engine renames, registers, tools/site.py, pages_market.py, test page list) + regenerated pages | see completion record below | see completion record below |
| P1 | Close out partial requirements R11/R12/R16/R19 where merged evidence now exists; where evidence does not exist, leave status `partial` and make the exact blocking gap + clearing number explicit (decision-readiness contract) | done | arena-a4c5a1de-fl1 | `data/requirements.json`, `requirements.html` (generated), `data/suggestions.json` (SG32 stale-page fix), `EXECUTIVE_SUMMARY.md`, `README.md` (stray-marker fix + addendum) | per-requirement evidence text cites the published pages/files; every number quoted was re-checked against committed data (summary.json, signal_cards.tsv, correlations_official.json, depth.html) | see completion record below |
| I2 | Final integration: PR → main, merge without waiting for review, confirm GitHub Pages deploy, record PR link + merge result here | done | arena-a4c5a1de-fl1 | PR + `COORDINATION.md` + requirements-page lead fix | Pages API + live fetch | — |

### Integration record — I2 (2026-11-16)

- **PR:** https://github.com/sassnarep3-star/FL1/pull/42 (`arena/a4c5a1de-fl1` → `main`),
  **MERGED** as `bec36881fa3ec01e40852870a6473b352698131c` via `gh pr merge 42 --merge` after the
  `verify` check passed. **PRs #38 and #39 now show state MERGED** — their head commits
  (`c09098c`, `372793a`) became ancestors of `main` through this integration, which is the intended
  takeover outcome: their work is on main under their own authorship history.
- **GitHub Pages:** latest build for `bec3688` → status **`built`**, `error: null`
  (pages-build-deployment run 43787989062, success). Source `main` `/`,
  https://sassnarep3-star.github.io/FL1/ live.
- **Live verification (page fetch, cache-busted):** `requirements.html` renders all 28 requirements
  with the new page-anchored evidence (R11/R12/R16/R19 rows confirmed); `flagged.html` publishes
  **52 items (F01–F52)** including the re-issued F43–F52; `results-feed-market.html` (the renamed
  spine page) renders with per-row source chips and the retagged F48 link; NAV/cards show both builds.
- **Follow-up fix shipped with this record:** the requirements-page lead said "The rest are marked
  partial on purpose" even at 28/28 — now conditional in the generator (`tools/site.py`), rebuilt,
  gates re-run (242 tests, checklinks 36 pages, checkrows 5,604 rows, verify_site 0/0).

**Session state: complete.** All three claimed tasks (I1, P1, I2) done and recorded. No open claims
remain on this session's board. The owner's decision list stays on the live pages: Q35–Q39 and
SG35–SG38 (spine decisions), Q23/Q37 (benchmark policy), Q29/Q32 (canonical build + official-only
rule), plus the long-standing flags (F34/F39 prices, F43 opening prices, F49 CLV collector).

### Completion record — I1 (2026-11-16)

**Merges performed on `arena/a4c5a1de-fl1` (takeover basis: both PRs' last commits 2026-11-14T23:0xZ,
>60 min stale; both CI-green; no live session activity):**
- PR #39 (`arena/2fa09442-fl1`, head `372793a`) merged first — one COORDINATION.md append/append
  conflict, both records kept. `tools/verify_replacement.py` cross-check passes after merge.
- PR #38 (`arena/08fef9e9-fl1`, head `c09098c`) merged second — resolutions, nothing discarded:
  - **engine add/add:** main keeps `engine/backtest.py` (R22 module, PR #33) and `engine/originate.py`
    (tools/brief.py `O` module); the spine's implementations renamed to `engine/backtest_spine.py` /
    `engine/originate_spine.py`; importers (`scripts/build_market_spine.py`, `tests/test_market_pipeline.py`)
    repointed; prose references in `tools/pages_market.py` updated.
  - **Register id re-issue (repo convention):** spine flags F18–F27 → **F43–F52**, questions Q21–Q25 →
    **Q35–Q39**, suggestions SG16–SG19 → **SG35–SG38**, sources S50–S56 → **S77–S76**. Retagging applied
    only inside the spine's own files (pages_market.py, its register rows, its COORDINATION record,
    its generated pages) — main-side references to same-numbered ids (685f958d's F18–F22 etc.) untouched.
  - **Page-name collisions:** spine outputs re-issued as `results-feed-market.html`,
    `signal-vs-staking-market.html`, `replacement-depth-market.html`; NAV + index cards retargeted;
    `tests/test_market_pipeline.py` PAGES list repointed.
  - **Generated artefacts** (`assets/js/data.js`, root pages) resolved to main then regenerated once
    from the merged generators — no hand-merged HTML.
  - **Capture refresh taken from the spine** per its own change record (F52): `data/raw/games.csv`,
    `data/raw/MANIFEST.json`, `data/raw/initial_lines.csv`; derived `docs/computed/week10.html` and
    `data/week10_signal_board.csv` match the spine's regenerated versions.
- **Post-merge gate battery (all green):** 242 unit tests OK · `tools/checklinks.py` 36 pages OK ·
  `tools/checkrows.py` 36 pages / 5,604 rows OK · `tools/verify_injuries.py` 345/345 ·
  `tools/verify_results.py` PASS · `tools/verify_replacement.py` OK (with cross-check) ·
  `tools/verify_brief.py` 10/10 · `scripts/build_market_spine.py --check` **byte-identical** ·
  `scripts/verify_feed_m.py` PASS 137/137 · `engine/demo_run.py --check` current ·
  `scripts/verify_d.py` V5/V7/V7a/V8 PASS (V6, V9 BLOCKED — optional deps/parquet absent in this
  sandbox, the recorded limitation) · `scripts/verify_site.py` 0 errors / 0 warnings ·
  `site/build.py` + `site/verify.py` publishable · no broken page references across root + docs pages.

**Irregularities found during I1 (all fixed here, all logged):**
1. README.md carried a committed, unresolved conflict-marker pair (`=======` / `>>>>>>> origin/main`
   around the 685f958d record) — a prior session removed the `<<<<<<<` line but left the other two.
   Fixed; both records preserved verbatim.
2. Generated `suggestions.html` (SG32's evidence text) referenced `correlations-official.html`, a page
   removed at a previous integration — invisible to `checklinks` because it is plain text, not an href.
   Repointed to the live `correlation-register.html` / `official-correlations.html` in the register row.
3. The shallow clone (depth 1) made `git merge-base` report "unrelated histories" until
   `git fetch --unshallow`; noted for future sessions.

### Completion record — P1 (2026-11-16)

All four remaining partials closed with published evidence; **all 28 tracked requirements now render
`done`** on `requirements.html`. Every number in the new evidence text was re-checked against committed
data before writing it (`data/market/summary.json` 23,219/13,310; `data/market/signal_cards.tsv`
5×INVERTED + 4×POSITIVE-MEAN-NOT-PROVABLE; `data/correlations_official.json` C-A1..C-A5 with n;
`depth.html` 71 ladders). Status → `done`, evidence → page-anchored:

- **R11** — numeric fair | market | difference published on `line-board.html` (official-only fair
  side/total; moneyline market cell BLANK by rule) and `origination.html` (spine: fitted µ/EWMA/HFA
  from the verbatim 2025 official standings capture S75, all 272 games, model card + tuning grid).
  The benchmark-provenance decision stays open (Q37) but is no longer a blocker of origination itself.
- **R12** — signals fitted and measured walk-forward (13,310 published bets, 2011–2026, sealed tail);
  SIGNAL/STAKING split live on both leaderboard implementations; headline finding F50 published
  (model signal negative vs recorded market on all three markets); 0 rewards payable (F49); control
  baselines ranked in the same table.
- **R16** — official-operand correlation register with n + Fisher CIs (C-A1..C-A5); correlation gate
  publishes its refused pairs with reasons (joint-evidence rule); availability-edge value blank at n=1
  (C-A4) as a published hold.
- **R19** — 71 verified replacement-depth ladders (per-club coverage, ruled-Out trails, named
  replacements by string), independently re-derived and cross-checked against the second
  implementation (31/35 exact, 4 enumerated definitional divergences, negative-tested); HOU image-only
  limit (F16) and the Dallas dual-first-string decision stay published.

Requests to future sessions: none open. The decision list for the owner remains Q35–Q39 (+ Q23/Q37
benchmark policy) and SG35–SG38 (+ SG24 breakeven fix) on the live pages.

Requests to other sessions: none currently. This session does not edit `tools/site.py` NAV regions or
other sessions' engine files; if I1 reveals a conflict, both sides are preserved and logged.

---

**Last updated:** 2026-11-16 (UTC) — claim of session `arena/fc0ed6e8-fl1` added at the top of this board

## Task board — session `arena/fc0ed6e8-fl1` (decision layer: readiness, change-of-mind, luck panel, ablations, drift alarm)

**Session ID:** `arena-fc0ed6e8-fl1` · **Branch:** `arena/fc0ed6e8-fl1` (from `ebf20eb` of `main`, PR #41 merged) ·
**Claimed:** 2026-11-16T00:00Z · **Status:** active.
**Pre-claim sweep:** `origin/main` = `ebf20eb`; two open PRs inspected — **#38** (`arena/08fef9e9-fl1`, market
spine: touches `tools/site.py`, most root pages, `data/market/*`, several engine files) and **#39**
(`arena/2fa09442-fl1`, touches only `tools/verify_replacement.py`, `data/verification-replacement.tsv`,
`COORDINATION.md`). This session avoids every file in those scopes except minimal, additive edits to
`tools/site.py` (new NAV entries + one new index section + one strategies-page column), logged here as
required by the shared-file rule.

| # | Task | Status | Owner | File scope (claimed) | Sources / verification | Irregularities |
|---|------|--------|-------|----------------------|------------------------|----------------|
| G1 | Coordination claim | done | `arena/fc0ed6e8-fl1` | `COORDINATION.md` | open-PR sweep via `gh pr list` | — |
| G2 | **Decision-readiness table on the landing page** — one row per brief requirement, with the gate that blocks it and the number that would clear it; full table on a new `readiness.html` | in progress | `arena/fc0ed6e8-fl1` | `data/readiness.json` (new), `readiness.html` (new), `tools/site.py` (additive: NAV + index section), `assets/js/data.js` (generated) | brief text + existing registers/gates | — |
| G3 | **Two-sided "what would change our mind" field on every strategy entry** (upgrade side + downgrade side) | in progress | `arena/fc0ed6e8-fl1` | `data/strategies.json` (add field), `tools/site.py` (strategies page render) | requirement text | — |
| G4 | **"Removal of luck" panel on the dashboard** — signal score vs luck decomposition, control baselines, uncertainty, sample floors; computed from committed official-reconciled data | in progress | `arena/fc0ed6e8-fl1` | `engine/luck.py` (new), `data/luck_panel.json` (new), `tools/site.py` (index section + validation.html section) | `engine/stats.py`, `data/results_feed.csv` (official-reconciled), `data/leaderboard_signal_staking.json` | — |
| G5 | **Injury/personnel ablations instead of fixed penalties** — same model with and without availability features, chronological holdouts, difference with uncertainty | in progress | `arena/fc0ed6e8-fl1` | `engine/ablation.py` (new), `data/ablations.json` (new), `ablations.html` (new) | `data/availability_2025.csv`, `data/depth_deficiency.csv`, `data/raw/games.csv` (third-party, labelled) | — |
| G6 | **Drift alarm gate** — pin every register/scraper output to expected row counts and required fields; fail loudly | in progress | `arena/fc0ed6e8-fl1` | `tools/verify_drift.py` (new), `data/validation_gates.json` (append G-18) | repo data files | — |
| G7 | **Venue transcription of 2026 fixtures** + published source label per row | in progress | `arena/fc0ed6e8-fl1` | `data/venue_2026.csv` (new), schedule page section via `tools/site.py` | `raw/games-nfldata.csv` (labelled third-party) + official game-centre spot checks | — |
| G8 | Registers append (flags/questions/suggestions/sources), README + EXEC_SUMMARY appends — **done only after merging `origin/main` into this branch** | pending | `arena/fc0ed6e8-fl1` | `data/flags.json`, `data/questions.json`, `data/suggestions.json`, `data/sources.tsv`, `README.md`, `EXECUTIVE_SUMMARY.md` | append-only | — |
| G9 | Integration: full verification battery, PR → main, merge, confirm Pages deploy, record here | pending | `arena/fc0ed6e8-fl1` | PR + `COORDINATION.md` | CI + Pages API | — |



> **Which board is authoritative?** This file. The board below is maintained by the session that owns the
> consolidating build at the repo root (`arena/ab4e9b05-fl1`). Earlier boards from the other two sessions are
> kept verbatim further down so their records are not lost. If your session's board is not the one at the top,
> **add your tasks to the top board** rather than replacing it.

### Session `arena-38a78804-fl1` — completion record (2026-11-16)

**Sources used (all appended to `data/sources.tsv`, all VERIFIED in this session):**
- **S77** — https://www.nfl.com/injuries/ — second dated read, 2026-11-16, window bracketed by
  sandbox clock readings (after 01:14:56Z, before 01:25:00Z), 8 content chunks. Page still showed
  *WEEK 10*; captured verbatim to `raw/injuries-week10-2026-read2.md`.
- **S78** — https://www.nfl.com/schedules/2026/by-week/week-10 — finals read, same window, 2 chunks.
  12 of 13 games printed FINAL; SNF in progress (no score printed; pre-game records 6-2/6-2);
  MNF unplayed. Captured to `raw/schedule-results-2026-week10-finals.tsv`.
- **S79** — https://www.nfl.com/standings/league/2026/REG — corroborating standings read (W/L/T
  and PF/PA for all 32 clubs), captured to `raw/standings-2026-20261116.tsv`. Explicitly NOT a
  replacement for `data/standings.tsv`.

**Verification performed (all passing at completion):**
- `python3 -m unittest discover -s tests -q` → **192 tests OK** (24 new in `tests/test_n01_n05.py`).
- `tools/checklinks.py` → **28 pages OK** (every internal link/anchor resolves; per-question anchors
  added to the questions page so Q-deep links work).
- `scripts/verify_site.py` → **0 errors / 0 warnings**. `tools/verify_injuries.py` → 345/345.
- `tools/verify_results.py` → PASS. `scripts/verify_d.py` → V5–V8 PASS, V7a FLAGGED by design,
  **V9 PASS** (Beexly/Sports parquet mirror fetched to `/home/user/datawork`, outside the repo —
  same procedure as the R21–R28 session; the file is not committed).
- `engine/demo_run.py --check` → current. `site/build.py` + `site/verify.py` → 18 pages, 0 rows
  without a source, "publishable".
- Rebuild determinism: `verify_d.py` V6 re-ran the computed-layer builds with identical artefacts.

**What was delivered:** landing-page **decision-readiness table** (28 rows: blocker + clearing
number per requirement); landing-page **removal-of-luck panel** (0 of 16 proven; all 7 positive-ROI
entries rejected on signal; control baseline −5.19%/5,067 bets; 16-trial multiplicity);
**two-sided change-our-mind field** on all 6 strategy entries; **dated injury-hub read 2 + delta
register** (32 changed / 2 added / 0 removed — all on clubs whose report was still evolving);
**Week 10 finals extension** (11 new finals, V1–V4 verified; SNF/MNF published as pending with
blank scores); **Q40 + SG39** (feed-promotion policy, owner decision pending); footer timestamp
updated to include the 2026-11-16 reads.

**Irregularities:** none new. Two operational notes recorded instead: (1) the live hub still showed
Week 10 on Monday — expected, logged in the capture header; (2) V9 needed the external parquet
mirror refetched in this checkout (file lives outside the repo by design).

**Integration:** PR from `arena/38a78804-fl1` → `main`, merged without waiting for approval, Pages
deploy confirmed — record appended below after the merge.

### ⚠️ Reconciliation record — merge with `origin/main` mid-session (2026-11-16)

While this session worked, PRs #38/#39/#42/#43 (market-data spine, stale-PR takeovers, partials
close-out, final integration) landed on `main` (base `ebf20eb` → `fef303b`, 142 commits). Per the
brief, `origin/main` was merged **in**; nothing from either side was discarded. What collided:

| Area | Theirs (merged first) | Mine (this session) | Resolution |
|---|---|---|---|
| Register ids | their integration re-issued `S70–S76`, `Q35–Q39`, `SG35–SG38`, flags `F43–F52` | mine had independently issued `S70–S72`, `Q35`, `SG35` | **Mine re-issued**: `S70→S77`, `S71→S78`, `S72→S79`, `Q35→Q40`, `SG35→SG39`; every reference in my builders, JSON registers, tests, exec-summary and this record retagged. Their ids untouched. |
| Requirements | R11/R12/R16/R19 closed as `done` with published evidence | my decision-readiness rows treated them as partial with blockers | My four curated rows rewritten to match the register (done, no blocker), citing their close-out evidence (spine boards, 23,219 graded trades, correlation gate, 71 verified ladders); builder asserts row↔register agreement, so the table cannot drift |
| `tools/site.py` | 8 spine pages in NAV, `pages_market` import, 8 new index cards, conditional requirements lead | my sprint sections, index cards + anchors, per-question anchors, page appends, footer date | Auto-merged (different regions); verified both feature sets render; 36 pages regenerate cleanly |
| Generated `*.html` / `data.js` | regenerated by their build | regenerated by mine | Resolved to their side at merge, then regenerated **once** from the merged generator — no hand-merged HTML |
| `data/questions.json` / `suggestions.json` / `sources.tsv` | their appends | my appends | Union by id with re-issue; dedupe asserted; 40 questions / 39 suggestions / 71 sources |

Post-merge verification: **266 tests OK** · checklinks **36 pages OK** · `verify_site.py` 0/0 ·
injuries 345/345 · results PASS · `verify_d.py` V5–V9 + V10 PASS · `verify_brief.py` 10/10 ·
`verify_replacement.py` OK · `demo_run --check` current · docs sub-site publishable.

### Session `arena-fc0ed6e8-fl1` — completion record (2026-11-16)

**Claim table above (G1–G9) is now done.** Delivered on branch `arena/fc0ed6e8-fl1`, merged into the
consolidating build after reconciling three parallel sessions (PRs #42–#46; conflicts logged below).

| Task | Result | Verification |
|---|---|---|
| G2 decision readiness | `data/readiness.json` (28 requirement rows + 69 brief-audit rows), `readiness.html`, compact table on the landing page | unit-tested (a row per requirement), rendered, link-checked |
| G3 change of mind | two-sided pre-registered upgrade/downgrade on all 6 strategies, rendered as a Leaderboard column | unit-tested (every entry carries both sides) |
| G4 luck panel | `engine/luck_signals.py` + `data/luck_panel_signals.json`; dashboard section + full table; verdict NO STRATEGY CLEARING (best raw p 0.1236 vs α/16 = 0.00313; best candidate needs n=4,315, has 936) | unit-tested; companion cross-link to the parallel session's official-results panel |
| G5 ablations | `engine/ablation.py` (stdlib OLS + seeded paired bootstrap), `data/ablations.json`, `ablations.html`; margin diff −0.11 [−0.24, +0.02], total −0.08 [−0.19, +0.03] — CIs include zero → feature stays OUT | unit-tested (exact-line OLS, leakage-free prior margins, determinism) |
| G6 drift alarm | `tools/verify_drift.py` (19 pins), gate G-18 appended to `data/validation_gates.json`, `data/verification-drift.tsv` | 19/19 PASS after re-committing pins for register growth |
| G7 venue | official Game Center spot-checks 2/272 both matching (S81/S82), Game Book PDF links confirmed; Stadium column stays labelled third-party (F63) | fetched live 2026-11-16 |
| G8 registers + reserve list | flags F61–F65, question Q44, suggestions SG43–SG45, sources S80–S85 (renumbered after PR #42–#44 collisions, cross-referenced); reserve-list capture 25 rows (S80) incl. Malik Willis 11/10 | `checkrows` 6,176 rows sourced; `checklinks` all anchors resolve |
| G9 integration | merged `origin/main` (nothing discarded; their `site_g` pages + my pages both live and cross-linked); full battery re-run | see below |

**Post-merge battery (all green):** 285 unit tests OK (18 new) · `checklinks` 43 pages OK (255 external
links) · `checkrows` 43 pages / 6,176 rows, 0 unsourced · `verify_drift` 19/19 PASS ·
`verify_injuries` 345/345 · `verify_results` 32/32 · `verify_brief` 10/10 · `verify_feed_m` 137/137 ·
`verify_d` V5–V9 (V7a FLAGGED by design, V9 BLOCKED by design — workspace parquet mirror absent) ·
`scripts/verify_site.py` 0 errors / 0 warnings · computed-layer CI rebuild byte-identical ·
`site/build.py` + `site/verify.py` publishable · `engine/demo_run.py --check` current.

**Official sources fetched and read this session:** S80 reserve-list transactions page (both chunks);
S81 KC@ATL Game Center; S82 NE@DET Game Center (Munich); S83 schedule-release announcement (May 8,
2026); S84 Brissett trade article (full text); S85 Lock start announcement; plus the official REG10
schedule page re-read (S49) which confirmed the 13 Week 10 finals behind flag F61.

**Irregularities published this session (Flagged for Review):** F61 (13 Week 10 finals now official
but feed snapshot stale — refresh task SG45), F62 (ablation inputs third-party, labelled),
F63 (venue third-party 272/272, spot-checks 2/272 — automation SG44), F64 (announced-starter
evidence boundary: Brissett start is reporter wording, McCord start not officially read),
F65 (readiness "numbers that clear" are design targets).

**Conflict log (merge with `origin/main` at PRs #43/#44):** `engine/luck.py`,
`data/luck_panel.json`, `data/announced_starters.json` existed on both sides — theirs kept at the
canonical paths (their `scripts/build_luck_g.py` + `tools/site_g.py` build), ours renamed to
`engine/luck_signals.py`, `data/luck_panel_signals.json`, `data/announced_starters_g.json` with the
builders, pins and tests re-pointed. Registers were unioned; our new rows renumbered
(F43–F47→F61–F65, Q35→Q44, SG35–SG37→SG43–SG45, S70–S75→S80–S85) with cross-references to the
overlapping rows we did not duplicate (F57/F59/F54). `tools/site.py` merged both sessions' blocks
(NAV, index sections, `written.extend(g_pages)` + our `session_sections`); all generated pages were
regenerated once from the merged generators. `COORDINATION.md` unioned (their board then ours).

**Silent-loss incident (caught in post-merge verification):** the wave-2 merge auto-took the
parallel sessions' rewritten `tools/site.py` wholesale, quietly dropping every
`session_sections` block (readiness/ablations pages, luck dashboard, strategies change-of-mind
column, validation G-18 section) even though the generated artifacts from the wave-1 commit
stayed committed — the pages were live but no generator rebuilt them. Found because the
rendered label `(F47)` no longer matched any generator source; recovered the blocks from the
wave-1 commit, re-applied them to the merged generator with final ids, and re-ran the battery.
Lesson for the board: after ANY merge touching `tools/site.py`, grep the generator for every
session's function names — a clean `git status` does not mean the merge kept both halves.

**Second reconciliation (PR #46, session `arena/38a78804-fl1`):** that session had ALSO claimed
S80–S82, Q44 and SG43 for different rows, and renamed the signal luck panel to
`data/luck_panel_signal.json`. Re-issued again: our sources are now **S83–S88**, our question **Q45**,
our suggestions **SG44–SG46** (+SG47 consolidation proposal, flag **F66** records the three-way
duplication). `scripts/build_luck_panel.py` (ours) renamed to `scripts/build_luck_panel_g.py`;
`data/strategies.json` now carries BOTH change-of-mind vocabularies (our `change_of_mind`
upgrade/downgrade objects and their `raises_confidence`/`lowers_confidence` strings) — the site
renders ours; the test pin for sources.tsv updated 74→80. All three parallel views stay live and
cross-linked; consolidation is registered as SG47 for owner review.

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
| R30 | Final integration: PR → main, merge, confirm Pages deploy, record result here | done | arena-360ca650-fl1 | PR only | Pages API + live fetch | PR #33 merged as `f5b6922`; Pages `built`; live pages re-fetched clean |

### Integration completion record — R30 (2026-11-14T22:55Z)

- **PR:** https://github.com/sassnarep3-star/FL1/pull/33 (`arena/360ca650-fl1` → `main`), **merged**
  as `f5b6922` via `gh pr merge 33 --merge` after CI (`verify-research-build` / `verify`) passed and
  GitHub reported `MERGEABLE CLEAN`.
- **GitHub Pages:** build for `f5b6922` → status **`built`** (`gh api repos/.../pages`; source `main` `/`).
- **Live verification (page-fetch, not curl):** `index.html` and `line-board.html` re-fetched from
  https://sassnarep3-star.github.io/FL1/ and read — the three separate columns (fair | market |
  difference) render with per-cell provenance badges, coefficients with n, retagged flag links
  (F23/F25/F26/F29), S52 source chips, and the F31 cross-links to the parallel build. Dashboard cards
  from both sessions render; KPI wording fix confirmed.
- **Post-merge incident (logged, no damage):** `git pull --rebase` on a branch containing the
  reconciliation merge commit attempted to flatten it and replay `arena/685f958d-fl1`'s commits on top
  of my line — exactly the discarding-work scenario the brief forbids. The rebase stopped on conflicts
  before writing anything, `git rebase --abort` restored `0969c58`, and the remote was already correct.
  **Lesson for future sessions: after a merge-conflict resolution, use `git pull --ff-only` — never
  `--rebase` across a merge commit.**
- **Final state:** 22 pages live; 134 unit tests OK; `tools/checklinks.py` 22 pages OK;
  `scripts/verify_site.py` 0 errors / 0 warnings; `tools/verify_brief.py` 10/10; injuries 345/345;
  results 32/32; `verify_d.py` V5–V9 PASS. 31 flagged items published (F01–F31), 29 questions,
  29 suggestions — the owner's decision list is Q21–Q29 on the live Open Questions page.

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

### ⚠️ Reconciliation record — parallel duplicate implementation (`arena/685f958d-fl1`)

While this session was building R21–R28, session `arena/685f958d-fl1` independently implemented the
**same eight requirements** and merged first (PRs #22–#32, main at `c3d5e8c`). PR #33 conflicted. Per the
brief, `origin/main` was merged **in**; nothing from either side was discarded. What happened, item by item:

| Area | Theirs (merged first) | Mine (this merge) | Resolution |
|---|---|---|---|
| Price store | `engine/price_snapshots.py` + `engine/snapshot_store.py`, `data/price_snapshots.tsv` | `engine/snapshots.py`, `data/price_snapshots.json` | **Both kept.** Two stores, cross-flagged as F31 |
| Results feed / backtest | `engine/results_feed.py`, `results-feed.html` ("Results Feed & Backtest") | `engine/backtest.py`, `verified-results-feed.html` | **Both kept**, renamed mine to avoid clobbering; mutual cross-links added |
| Line model | `engine/originate.py`, `model-lines.html` (market/difference cells **blank** — strict source policy) | `engine/fairline.py`, `line-board.html` (market published with THIRD_PARTY badge) | **Both kept.** The policy divergence is the substance of Q23 |
| Signal/staking + demotion | `governance.html`, D1–D3 gate (CLV decay, calibration drift, concentration) in `engine/gates.py` | `strategies.html` split + G-14 gate (`engine/demotion.py`: signal decay, drawdown, CLV rot) | **Both kept.** Both gate sets render on `validation.html`; Q24 chooses |
| Registers | their flags **F18–F22**, suggestions **SG16–SG19**, sources **S50–S51** | mine used the same id ranges | **Mine re-issued** per repo convention: F18–F25 → **F23–F30**, SG16–SG24 → **SG20–SG28**, S50 → **S52**. Their ids untouched; every internal reference in my files retagged (single-pass mapping — a first sequential-replace attempt chained F18→F23→F28 and was rebuilt from git) |
| New reconciliation items | — | **F31** (High, integration divergence), **Q29** (which build is canonical?), **SG29** (review pair-by-pair, archive-with-cross-links) | Published for owner review |
| `tools/site.py` | NAV + 3 cards + `brief.render()` hook + exec banner + D1–D3 section | NAV + 2 cards + `sprint_sections()` + 5 pages + 4 section appends + footer policy | **Both features re-applied on their base**; all 22 pages regenerated from the merged generator |
| `COORDINATION.md` | their board + integration records | my board + records | Auto-merged cleanly (different regions); this record appended |
| Generated pages (`*.html`, `assets/js/data.js`) | regenerated by their build | regenerated by mine | Regenerated **once** from the merged `tools/site.py` / `tools/build.py` — no hand-merged HTML |

**Verification after the reconciliation (all green):** `python3 -m unittest discover -s tests -q` →
**134 tests OK** (both suites) · `tools/checklinks.py` → 22 pages OK · `scripts/verify_site.py` → 0/0 ·
`tools/verify_brief.py` → **10/10 PASS** (their verifier confirms F18–F22 anchors preserved) ·
`tools/verify_injuries.py` 345/345 · `tools/verify_results.py` PASS · `scripts/verify_d.py` V5–V9 PASS ·
`engine/demo_run.py --check` current.

**Lesson logged (per the board's own rule):** `git fetch origin && git log origin/main` was run before my
first push, but not re-run before opening the PR — a second fetch would have caught the parallel session
mid-build. The 60-minute stale-claim rule did not help because both claims were fresh. The fix for future
sessions: re-check `origin/main` and open PRs **immediately before** creating a PR, not only before the
first push.

### Current task claim — `arena/725adbd2-fl1` (2026-11-14)

| Task | Status | Owner | File scope | Sources / verification | Irregularities |
|---|---|---|---|---|---|
| Make verification results truthful when inputs/dependencies are unavailable; expose blocked prop-correlation rebuild on the review page | done | arena/725adbd2-fl1 | `scripts/verify_d.py`, `scripts/build_schedule_d.py`, `scripts/build_pages_d.py`, `tools/site.py`, `data/verification-d.tsv`, `data/flags.json`, generated `assets/js/data.js`, `schedule.html`, `prop-correlations.html`, `flagged.html`, and `validation.html`, this claim/completion note in `COORDINATION.md` | `scripts/verify_d.py` with workflow-equivalent NumPy/Pandas/SciPy installed in an ignored venv: V6 PASS and V9 BLOCKED; `scripts/verify_site.py` 0 errors/0 warnings; root and docs site verifiers pass; 78 tests pass; internal links and injury/results checks pass | Parquet mirror is not committed and is unavailable in this checkout; V9 correctly remains BLOCKED. V9 now links the actual third-party mirror, not the nflverse games feed. |

**Completion note (2026-11-14):** V6 checks dependencies before attempting a fresh rebuild; V9 separately checks the external parquet input, required libraries, and parquet reader. Missing prerequisites are recorded as `BLOCKED`, never as a false pass/fail. Both status rows render visibly on `schedule.html`; F17 states the reproducibility limitation on `flagged.html`. TSV writers use LF endings for clean diffs. The root generator now also emits the D1–D3 live-to-paper demotion section, preserving the separate gate added on `main`. Verified with `.venv/bin/python -m unittest discover -s tests -q` (78 tests on rebased integration), `python3 engine/demo_run.py --check`, `python3 -m engine.measure`, `python3 tools/checklinks.py`, `python3 tools/verify_injuries.py`, `python3 tools/verify_results.py`, `python3 site/build.py && python3 site/verify.py`, and `.venv/bin/python scripts/verify_site.py` (0 errors/0 warnings).

**Integration record:** PR [#27](https://github.com/sassnarep3-star/FL1/pull/27) merged to `main` at `d495ba844414565f29f2a4d67b4afad3707d5d1e` on 2026-11-14 22:10:36 UTC. Verification workflow [43646645547](https://github.com/sassnarep3-star/FL1/actions/runs/43646645547) passed. GitHub Pages deploy [43646691589](https://github.com/sassnarep3-star/FL1/actions/runs/43646691589) passed; Pages API reports `built` from `main` `/` at https://sassnarep3-star.github.io/FL1/. V9 remains visibly BLOCKED because the uncommitted parquet input is absent; this is an explicit limitation, not a failed site build.

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
| 2026-11-14 | `arena/4a9893e6-fl1` | Verified official sources (nfl.com/injuries/, nfl.com/standings/, nfl.com/schedules/2026/REG10/, nfl.com/teams/kansas-city-chiefs/roster) against the live pages; injury spot-checks (8 players) and repo standings.tsv match the live official pages exactly. tools/build.py, verify_injuries.py (345/345) and checklinks.py (16 pages, 0 broken) all PASS. Added the demotion gate (D1-D3) to validation.html, defined but not active pending a benchmark price (flag F08). **PR #24 merged** into `main` as merge commit `f079743`. GitHub Pages build for `f079743`: **built**. Live validation.html re-fetched and confirmed rendering the demotion gate. |

---

## PR and deploy record

| Item | Result |
|---|---|
| PR #3 (this session's main deliverable) | **MERGED** into `main` as merge commit `eb50220` at 2026-11-14T03:05:45Z |
| PR #5 (escaped-link fix) | **MERGED** into `main` as merge commit `d5e9cc0` |
| PR #7 (review guide, PR/deploy record, option labels) | **MERGED** into `main` as merge commit `6ba143f` |
| PR #8 (verification table header fix) | **MERGED** into `main` as merge commit `1c6c8ab` |
| PR #24 (demotion gate, source verification) | **MERGED** into `main` as merge commit `f079743` |
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

## Current Arena session claim — `arena/0669d4cf-fl1` (2026-11-14)

| ID | Task | Status | Owner | File scope |
|---|---|---|---|---|
| T21 | Add fair-vs-market opening/closing snapshots and a fail-closed verified final-results import interface; complement the raw quote ledger; do not populate unverified facts | done — library only; no records imported | `arena/0669d4cf-fl1` | `engine/snapshot_store.py`, `engine/results_feed.py`, `tests/test_market_results_store.py`, `docs/market-results-store.md`, this claim/verification record only |

Existing price/results datasets remain third-party or capture-specific; this task adds a persistence and provenance boundary, not a claim that those inputs are official NFL data. The existing active claim at T03–T16 is not touched.

### T21 completion / verification record

- `SnapshotStore` requires an opening event, allows one closing event, stores fair value, market value and signed difference separately, verifies the caller-supplied source digest against the exact captured bytes, and keeps numeric fields blank on unverified events. It reports markets without both verified snapshots. This is an analytical paired-value ledger complementing (not replacing) the simpler raw quote-event store `engine/price_snapshots.py`, merged to main in PR #22.
- `ResultsFeed` accepts only explicit `FINAL` records with an HTTPS `nfl.com` host URL, timestamp and captured bytes whose SHA-256 matches. It is append-only, idempotent for the same game/payload, and retains corrections as new events. It validates provenance shape; it does not fetch pages or independently validate transcription, so callers must check every score against the cited source before setting `verified=True`. Evidence payload archival remains the collector's responsibility.
- Official-source check: fetched [NFL 2026 Week 10 schedule](https://www.nfl.com/schedules/2026/REG10/) and observed “Commanders 24, Giants 21, FINAL”. This verifies the cited source page and an example official result only; **no result was imported**, and this is not a complete results feed or ROI dataset.
- Checks: after integrating the concurrent main branch, `python3 -m unittest discover -s tests -q` — 90 tests passed; `python3 tools/verify_results.py` — 137 captured games reconcile to all 32 standings records (excluding Week 10 Thursday gives 2 mismatches); `python3 tools/verify_injuries.py` — 345/345 captured rows match; `python3 tools/checklinks.py` — 16 pages / 0 broken internal links; `python3 engine/demo_run.py --check`, `python3 -m engine.measure`, `python3 site/build.py`, and `python3 site/verify.py` all passed; `git diff --check` clean.
- Limitation: the new libraries are not yet wired to an automated bookmaker collector or linked into the published site navigation. This requires a selected/licensed quote feed and integration-scope site changes. No unverified prices or unverified results were added.
- **Concurrent merge reconciliation:** PR #25 initially could not merge because `main` advanced (including PR #22's raw quote ledger and PR #24's demotion gate). Merged that `origin/main` into this branch; the only content conflict was this coordination log and both session records were retained. Before the next push, `git pull --rebase` tried to replay already-merged main history and conflicted in the same log; aborted that rebase, then merged the newer `origin/main` (PR #26) cleanly. README and validation-page additions from main were retained; no other session files were edited or discarded. This branch's fair-value/results extension remains separate by design.
- **Integration record:** [PR #25](https://github.com/sassnarep3-star/FL1/pull/25) merged on 2026-11-14T22:12:08Z as `3d669fc3a0654d9b28ea1a7430524a111b054d0f`; CI verification run 43646755208 passed. GitHub Pages run 43646837225 succeeded and API reports `status: built`, source `main` `/`. Live spot checks: [dashboard](https://sassnarep3-star.github.io/FL1/) and [validation/demotion gates](https://sassnarep3-star.github.io/FL1/validation.html). A transient earlier Pages build attempt errored during overlapping deploy triggers; the latest build completed successfully. The new SQLite modules are not wired into the public site or an automated quote collector; the site records this as blocked pending a selected/licensed feed.
---

## Additive follow-up — price snapshot storage

- **Session/branch:** `arena/f1e4deb7-fl1` (active current branch; repository branch is Arena-managed, so no alternate session branch was created).
- **Scope:** `engine/price_snapshots.py`, `tests/test_price_snapshots.py`, README documentation, this log.
- **Status:** done; implementation is a local append-only SQLite schema/API, not a populated feed.
- **Verification:** run `python3 -m unittest discover -s tests -q`, `python3 engine/demo_run.py --check`, `python3 -m engine.measure`, and `python3 site/build.py && python3 site/verify.py`. Tests cover open/close persistence, model-version capture, idempotency, and fail-closed validation of missing source / unsupported market and phase.
- **Sources / irregularities:** no provider was selected and no quote was inserted. NFL official sources do not publish sportsbook prices; price values stay unverified/blank until an authorized source is acquired. The store requires explicit source URL, source record identifier, phase, timestamp and originating model version, and deliberately performs no inference.
- **Integration record:** PR https://github.com/sassnarep3-star/FL1/pull/22 merged on 2026-11-14T22:06:18Z. CI run 43646254061 passed; GitHub Pages deployment run 43646303860 passed. Pages source remains `main` / `/`.

---

## Session `arena/685f958d-fl1` — task claims (brief: price store, results feed, origination, leaderboard split, demotion gate, official-only correlations)

**Session ID:** `arena-685f958d-fl1` · **Branch:** `arena/685f958d-fl1` (from `main` @ `9d7ca32`, PR #21 merged) · **Status:** active
**Protocol note:** this session works only on `arena/685f958d-fl1` (Arena single-branch policy), so file-scope isolation is used, as in earlier sessions. Checked 2026-11-14 with `gh pr list --state open`: no other PR is open on the repository. The top board's per-task statuses were not re-audited in this session.

| ID | Task | Status | Owner | File scope (claimed) |
|---|---|---|---|---|
| B1 | Price-snapshot store: opening and closing numbers for each market we originate (side, total, moneyline) | done (store built, no prices: F18) | `arena-685f958d-fl1` | `data/price_snapshots.tsv`, `tools/brief.py` |
| B2 | Origination order (side → total → moneyline); fair line, market line and difference as separate columns | done (market blank: F18) | `arena-685f958d-fl1` | `data/model_lines.tsv`, `tools/brief.py`, `engine/originate.py` |
| B3 | Verified results feed + walk-forward calibration backtest (ROI stays blank until prices exist) | done (Weeks 1–9 aggregate only: F22) | `arena-685f958d-fl1` | `data/results.tsv` (read only), `data/backtest_calibration.tsv`, `tools/brief.py` |
| B4 | Leaderboard: separate signal score from staking score; staking cannot mask a bad signal | done | `arena-685f958d-fl1` | `engine/leaderboard.py`, `tests/test_engine.py` |
| B5 | Demotion gate G-14: live strategy returns to paper on defined triggers | done (thresholds need owner: SG17) | `arena-685f958d-fl1` | `engine/gates.py`, `data/validation_gates.json`, `tests/test_engine.py` |
| B6 | Correlations from officially sourced numbers only, with n published; third-party rho withdrawn from publication and flagged | done (F19; rule decision: SG19) | `arena-685f958d-fl1` | `data/correlations.json` (read), `tools/brief.py`, `data/flags.json` (append only) |
| B7 | Verification of every new row (official source links, fetch-checked), verifier script | done (10/10 checks) | `arena-685f958d-fl1` | `tools/verify_brief.py`, `data/verification-brief.tsv` |
| B8 | Integration: site nav + new pages, executive summary, suggestions, requirements status, PR, merge, Pages check | in progress | `arena-685f958d-fl1` | `tools/site.py` (NAV + page calls only), `README.md` (append), `COORDINATION.md` |

**Official sources used this session (fetched and read 2026-11-14):**
- https://www.nfl.com/schedules/2026/REG10/ — Week 10 slate (1 final, 13 upcoming; 14 games = 28 clubs playing).
- https://www.nfl.com/schedules/2026/by-week/week-11 — Week 11 begins Thursday 19 Nov 2026 (not in the current slate).
- Existing verified sources in `data/sources.tsv` (S01–S04, S49) remain the anchors for injuries, standings and schedule.

**Known limits, recorded up front:** no official NFL source publishes betting prices (GAP-01 / Q-02 remain open), so every market line, closing price and ROI cell stays blank, and no correlation coefficient can be computed from official joint observations yet.

### Session `arena/685f958d-fl1` — completion record (task board B1–B8)

**Sources (all official sources fetched and read 2026-11-14; links kept per row in the data files):**
- Week 10 2026 official schedule, all 13 pending games: https://www.nfl.com/schedules/2026/REG10/ (S51; capture in `raw/nfl-week10-2026-capture.md`).
- Week 10 official page (1 final, 13 pending, 4 byes CHI/DEN/PHI/TB), and the Week 11 page (first game Thu 19 Nov): https://www.nfl.com/schedules/2026/by-week/week-10 and https://www.nfl.com/schedules/2026/by-week/week-11 (S50).
- Existing verified anchors reused: S01 (injury report), S02/S03 (standings), S49 (REG10), S48 (third-party, withheld).

**Verification performed:**
- `tools/verify_brief.py`: 10/10 PASS — V1 13 games match the official capture (URL, teams, date, kickoff, network); V2 the slate equals the repo's own unplayed Week 10 games; V3 every fair value reproduces from a fresh re-run; V4 0 market cells filled, official URL on every row; V5 39 price rows, 0 prices; V6 137 results equal the played rows of the schedule feed; V7 n on every backtest row, ROI blank; V8 no withheld coefficient on any published page; V9 F18–F22 anchors; V10 standings reconciliation still passes.
- `python3 -m unittest discover -s tests -q`: 92 tests pass (17 new in `tests/test_brief.py`).
- `tools/build.py`, `tools/site.py`, `tools/checklinks.py` (19 pages, all reachable, all source IDs registered), `tools/verify_injuries.py` (345/345), `site/build.py` + `site/verify.py` (all checks passed).
- CI rebuild sequence run locally in a throwaway venv: `build_availability`, `build_correlations`, `strategy_lab`, `build_week10_board`, `build_registers`, `build_site`, then `verify_site.py` (exit 0).

**Results of the work (stated plainly):**
- Fair lines are published for the 13 pending games, in order side → total → moneyline. Market and difference cells are blank.
- Out-of-sample backtest (weeks 4–10, n = 89): side sign accuracy 67.0% (95% CI 56.7–76.0%), but side MAE 10.49 vs a constant benchmark of 10.33, and total MAE 11.07 vs 10.96. The model does not show an advantage on margin or total. ML Brier 0.2181 vs 0.2472 for 50/50. No ROI.
- No official price source exists, so the price store holds 39 blank rows.
- Correlations are withheld everywhere they appeared (F19); n is kept.

**Irregularities flagged (Flagged for Review, F18–F22):** no official price source (F18); third-party correlations withheld (F19); the model does not beat a constant benchmark (F20); Munich home-field assumption (F21); Weeks 1–9 results only reconciled in aggregate (F22).

**Owner decisions requested (suggestions register, SG16–SG19):** price source (SG16); G-14 thresholds (SG17); line-by-line check of Weeks 1–9 (SG18); the correlation rule (SG19).

**Pages changed on the root site:** `schedule.html` and `prop-correlations.html` (values withheld), `index.html` (three new cards), every page (new navigation entries), `executive-summary.html` (update banner), `suggestions.html`, `flagged.html`, `sources.html`. New pages: `model-lines.html`, `results-feed.html`, `governance.html`. Sub-site `docs/pages/measured.html` carries a withdrawal banner.

**Known limits:** the requirement status changes in `data/specs/requirements.json` apply to the sub-site register only; the root `requirements.html` still reads the earlier `data/requirements.json`. Weeks 1–9 per-game verification is still open (SG18).

### Integration record — `arena/685f958d-fl1` (2026-11-14, merge with `main` at `d3b4f4d`)

- **Concurrent work reconciled:** `main` had advanced by PRs #22–#29 (price snapshot ledger `engine/price_snapshots.py`, `engine/snapshot_store.py`, the fail-closed results feed `engine/results_feed.py`, the Week 10 `schedule.html` and `flagged.html` regenerations, and `verify_d.py` dependency checks). These overlap by topic with B1/B3, not by file. Nothing from `main` was removed. Both sides of each conflict were kept: `COORDINATION.md` (both records), `data/flags.json` (main's F01–F17 plus this session's F18–F22; no ID collision), `flagged.html` and `assets/js/data.js` (generated, regenerated from the merged data).
- **Checks on the merged tree:** `python3 -m unittest discover -s tests -q` OK; `tools/checklinks.py` OK; `tools/verify_brief.py` PASS 10/10; `tools/verify_injuries.py` exact; `tools/verify_results.py` ran clean; `site/build.py` + `site/verify.py` all passed; `engine/demo_run.py --check` current; `engine.measure` SIG-01 n=1302. CI rebuild sequence (`verify.yml`) reproduces with no diff in `data/` or `docs/`.
- **Refresh workflow note:** `scripts/build_prop_correlations_d.py` exits non-zero in the sandbox because `/home/user/datawork/player_stats_weekly_archive.parquet` is a workspace-only mirror. `refresh.yml` already tolerates this with `|| echo skipped`; no change made.
- **Left open:** the price store has no official source (F18, SG16); the correlation rule (F19, SG19); Weeks 1–9 per-game verification (F22, SG18).

### Post-merge correction — `arena/685f958d-fl1` (2026-11-14)

- **Defect found after PR #30 merged (`cd994ed`):** a live check of `model-lines.html` on Pages showed (a) the pending-game table rows had 13 cells under 16 headers, so the fair total and fair moneyline values sat under the wrong columns; (b) the origination prose printed the literal `σ = %.2f`. The merge gate did not catch either because it checked the data and links, not the table shape or the rendered text.
- **Fix:** `tools/brief.py` now emits the three missing difference cells per row and substitutes the fitted σ (13.63) into the prose. Every table on every root page was checked against its header: 53 tables, 3,407 rows, 0 mismatches. A sweep for unformatted placeholders across the root and sub-site pages found none; the one `%s` on `audit.html` is a literal `git log --format` example in a documentation cell (present on `main` before this session).
- **Gates re-run on the fix:** unit tests OK; `tools/checklinks.py` OK; `tools/verify_brief.py` PASS 10/10; `site/build.py` + `site/verify.py` pass; CI rebuild sequence and `scripts/verify_site.py` pass; `git diff --exit-code -- data docs` clean.
- **Process note:** the cell-count and placeholder checks are now run on the built pages before any future merge in this session.

### Merge and deployment record — `arena/685f958d-fl1` (2026-11-14, final)

| PR | Head | Merge commit | Merged (UTC) | CI | Pages build |
|---|---|---|---|---|---|
| [#30](https://github.com/sassnarep3-star/FL1/pull/30) — session integration (B1–B8) | `d89a9cb` | `cd994ed` | 2026-11-14 22:18:54 | `verify` pass (run 43647366078) | `built` for `cd994ed` (22:19:23) |
| [#31](https://github.com/sassnarep3-star/FL1/pull/31) — post-merge correction to `model-lines.html` | `25783de` | `32e2bc9` | 2026-11-14 22:22:07 | `verify` pass (run 43647656802) | `built` for `32e2bc9` (22:22:27) |

- **Live check after #31:** `https://sassnarep3-star.github.io/FL1/model-lines.html` shows σ = 13.63 and the pending-game table with 16 cells per row, each value under its own header. The first fetch returned the pre-fix copy, which was CDN caching; a cache-busting query returned the corrected page.
- **Defect shipped in #30 and corrected in #31:** misaligned table cells and an unformatted σ placeholder on `model-lines.html` (see the post-merge correction record above).
- **Open items carried forward (not blocking):** F18 no official price source (SG16); F19 correlations withheld (SG19); F20 model does not beat a constant benchmark; F21 Munich home-field assumption; F22 Weeks 1–9 per-game verification (SG18); G-14 thresholds (SG17).
- **Workflow note:** `refresh.yml` step `build_prop_correlations_d.py` cannot run in the sandbox (workspace-only parquet mirror), and is tolerated by its `|| echo skipped`.
---

## Session `arena/5876146b-fl1` — claim and scope (2026-11-14)

- **Session/branch:** `arena/5876146b-fl1` (Arena-managed single branch; claim pushed at first commit).
- **Coordination check before claiming:** `origin/main` = `9d7ca32` (PR #21 merged). One open PR
  inspected: [#22](https://github.com/sassnarep3-star/FL1/pull/22) (`arena/f1e4deb7-fl1`,
  "Add sourced NFL price snapshot storage", files `engine/price_snapshots.py`,
  `tests/test_price_snapshots.py`, `README.md`, `COORDINATION.md`). That session owns the
  **price-snapshot store**; this session will not touch those files and will merge their PR at
  integration only if it is complete and green.
- **Claimed tasks (unclaimed at claim time; non-overlapping with PR #22):**

| ID | Task | Files (owned by this session) | Status |
|---|---|---|---|
| M1 | Verified results feed (official-sourced, settlement-ready) + ROI/backtest computation, fail-closed | `data/results_feed.csv`, `engine/results_feed.py`, `tests/test_results_feed.py` | in progress |
| M2 | Market origination order **side → total → moneyline**, and publish **fair line / market line / difference** as three separate columns | `data/fair_lines.csv`, `data/origination_order.json`, `engine/fair_lines.py` | in progress |
| M3 | Leaderboard: separate **signal** from **staking** (rank on signal only) | `data/signal_vs_staking.csv`, `engine/signal_vs_staking.py` | in progress |
| M4 | Replacement-**depth** tracking (which string replaces a missing starter), Week 10 2026 | `data/replacement_depth.csv`, `tools/build_replacement_depth.py` | in progress |
| M5 | Correlations computed **only** from officially sourced numbers, each published **with n** | `data/correlations-official.csv` | in progress |
| M6 | **Demotion gate**: live strategy → paper, with triggers and re-entry rules (G-14) | `data/governance_gates.json` | in progress |
| M7 | Root-site integration pages + NAV + executive-summary/README addenda + flags | `originations.html`, `signal-vs-staking.html`, `results-feed.html`, `governance.html` (new pages), `tools/site.py` (NAV + page builders, additive), `data/flags.json` (append-only), `EXECUTIVE_SUMMARY.md`, `README.md` (append-only) | in progress |
| M8 | Integration: verify line-by-line, merge PR #22 if complete, PR → main, confirm Pages, record here | `COORDINATION.md` | unclaimed→in progress |

- **Shared-file etiquette:** `tools/site.py` gets additive NAV/page-builder edits only (session D
  precedent); `data/flags.json`, `README.md`, `EXECUTIVE_SUMMARY.md`, `COORDINATION.md` are
  append-only. No file owned by `arena/f1e4deb7-fl1` will be edited. If PR #22 lands first, this
  session rebases and keeps both sides' appends.
- **Sources policy:** official-sourced values only in M1/M4/M5 tables (per-row source IDs from
  `data/sources.tsv`); model outputs (fair lines) are labelled MODEL OUTPUT with a pinned model
  version; third-party market prices are labelled third-party and flagged (F-17 lineage). Blank +
  flagged wherever unverified. Nothing inferred.

---

## Session `arena/5876146b-fl1` — integration & completion record (2026-11-14)

### What was delivered (all committed on this branch, merged in the record below)

| ID | Deliverable | Artefacts | Verification |
|---|---|---|---|
| M1 | Verified results feed + fail-closed settlement/ROI | `data/results_feed.csv` (137), `raw/official-finals-2026.tsv`, `engine/results_settlement.py` (renamed at integration; see below), `tests/test_results_feed.py`, `results-feed.html` | `scripts/verify_feed_m.py` 137/137 three-way PASS; `python3 -m engine.results_settlement --check` OK; 17 unit tests |
| M2 | Origination order **side → total → ML**; fair line \| market line \| difference as separate columns | `data/fair_lines.csv` (272 rows), `data/origination_order.json`, `scripts/build_fair_lines_m.py`, `originations.html` | engine equivalence vs Computed Research Layer 5,336/5,336; published calibration reproduced (MAE 2.89, corr 0.828) |
| M3 | Signal vs staking split | `data/signal_vs_staking.csv` (16 strategies), `signal-vs-staking.html` | rank on signal only; 3 masked (positive staking over non-positive signal); G-15 signal-only promotion |
| M4 | Replacement **depth** | `data/replacement_depth.csv` (69 spots), `replacement-depth.html` | string = published rank within spot; 6 blanks (all Out above) flagged; NE RB cascade to 3rd string flagged |
| M5 | Official-only correlations with n | `data/correlations-official.csv` (C-O1..C-O3), `official-correlations.html` | r=+0.076 n=137; \|r\|<0.09 n=242; every value publishes its n |
| M6 | Demotion gate live→paper | `data/governance_gates.json` (G-14, G-15), `signal-vs-staking.html` | trigger A signal decay / B risk breach / C compliance; automatic; staking can never promote but can demote |
| M7/M8 | Site pages + integration | NAV/cards, S52–S60 sources, F23–F27 flags, EXECUTIVE_SUMMARY/README addenda | post-merge matrix below |

### Conflict resolution at merge with `origin/main` (PRs #22–#32) — nothing discarded

1. **`engine/results_feed.py` (add/add):** main's module is the verified-ingestion boundary
   (SQLite, provenance-shaped; `arena/0669d4cf-fl1`) and **keeps the name**. This branch's
   settlement/ROI engine is now `engine/results_settlement.py`; its 17 tests follow. Both are
   cited on `results-feed.html`.
2. **`data/flags.json` id collision (F18–F22, both sides):** main's F18–F22 kept as registered.
   This branch's five flags re-issued **F23–F27** (session-D S47–S49 re-issue precedent) and all
   in-page references updated. Registry status updates, entries kept: their **F19** marked
   RESOLVED-IN-PART (official-only correlations now published with n); their **F22** marked
   RESOLVED (row-level official capture of all 137 finals supersedes the aggregate-only
   reconciliation of weeks 1–9).
3. **`data/sources.tsv` id collision (S50/S51):** main's S50/S51 kept (by-week overview; week-10
   game pages). This branch's nine per-week sources re-issued **S52–S60**; `results_feed.csv`
   rebuilt with the new ids and re-verified 137/137.
4. **`results-feed.html` (add/add):** one merged page — main's walk-forward backtest table
   (values preserved from `data/backtest_calibration.tsv`) + this branch's row-level official
   feed + the settlement contract. `tools/brief.py` no longer writes the page (printed pointer)
   and continues to compute the data tables; its other pages unchanged.
5. **`tools/site.py`:** union NAV (23 entries: + model-lines, results-feed, governance from main;
   + replacement-depth, official-correlations, originations, signal-vs-staking from this branch)
   and union index cards (one results-feed card).
6. Generated HTML and `assets/js/data.js` re-rendered from the merged data by the merged
   generators (tools/site.py, scripts/build_pages_d.py, tools/brief.py, scripts/build_pages_m.py).

### Post-merge verification matrix (2026-11-14)

- `python3 -m unittest discover -s tests -q` — **124 tests OK** (incl. this branch's 17,
  the price-store and market-results-store suites, and the brief suite).
- `python3 tools/verify_brief.py` — **10/10 PASS** (its V6 confirms the 137 results equal the
  played rows of the schedule feed).
- `python3 scripts/verify_feed_m.py` — PASS 137/137 three-way field-for-field.
- `python3 scripts/verify_d.py` — V5–V9 PASS (V9 upgraded BLOCKED→PASS by
  `scripts/fetch_prop_mirror_m.py`, pinned git blob `adc42c07…`, rebuild byte-identical).
- `python3 scripts/verify_site.py` — 0 errors, 0 warnings. `python3 tools/checklinks.py` — 23
  pages, every internal link and anchor resolves, every source id registered.
- `python3 site/build.py && python3 site/verify.py` — publishable.
  `python3 engine/demo_run.py --check` — current.

### Sources added this session (registries)

S52–S60 (official nfl.com by-week pages, weeks 1–9, row-level finals transcribed and verified;
`raw/official-finals-2026.tsv`). Market prices remain third-party (S47; F18/F25) — no official
NFL price source exists; nothing inferred.

### Irregularities flagged this session

F23 (leaderboard note says "totals-first" vs mandated side-first), F24 (fair total blank —
unfitted S2), F25 (market prices third-party; see also F18), F26 (replacement values derived;
6 blanks; HOU absent per F16), F27 (requirements.txt understates scripts-layer deps: pandas/
numpy/scipy/pyarrow — pre-existing; `scripts/` layer only).

---

## Session `arena/5876146b-fl1` — second merge & final id mapping (2026-11-14)

PR #33 (`arena/360ca650-fl1`, R21–R28) landed while this session's PR #34 was open — a
**third** parallel implementation of the same eight requirements. Resolved exactly like the
first merge: preserve everything, re-issue colliding ids, cross-link duplicate pages
(their F31 updated to record all three).

### Final id map (supersedes the ids in the completion record above)

| This session's artefact | Earlier id | **Final id** | Note |
|---|---|---|---|
| Week 1–9 official schedule pages | S50–S58, then S52–S60 | **S61–S69** | S50–S52 now held by the R21–R28/685f958d registers |
| Leaderboard "totals-first" wording discrepancy | F18, then F23 | **F32** | cross-ref their F27 (mandated order) |
| Fair total blank (unfitted S2) | F19, then F24 | **F33** | cross-ref their F29 |
| Market prices third-party only | F20, then F25 | **F34** | cross-ref their F23 |
| Replacement values derived / 6 blanks / HOU absent | F21, then F26 | **F35** | — |
| requirements.txt understates scripts deps | F22, then F27 | **F36** | — |
| Demotion gate (session M proposal) | G-14 | **G-16** | their G-14 (validation_gates.json) kept; two proposals, both live |
| Signal-only promotion rule | G-15 | **G-17** | — |

`data/results_feed.csv` rebuilt against S61–S69/S49 and re-verified 137/137; all page text
and `data/origination_order.json` / `data/governance_gates.json` re-mapped.

### Duplicate-page map (all preserved)

| Page | Status |
|---|---|
| `results-feed.html` | merged superset (685f958d backtest table + this session's row-level official feed + settlement contract) |
| `verified-results-feed.html` | R21–R28's feed page, kept as-is |
| `replacement-depth.html` | merged (this session's 69-spot week-10 analysis + the R26 52-slot register section) |
| `replacement-depth-r21r28.html` | R26 register standalone copy (their generator output, preserved) |
| `originations.html` / `line-board.html` / `model-lines.html` | all three fair\|market\|difference views kept, cross-linked |
| `signal-vs-staking.html` / `governance.html` / strategies sprint sections | all kept |
| `official-correlations.html` / `correlation-register.html` | both kept |

### Post-second-merge verification matrix

`unittest discover` **151 OK** · `verify_brief` **10/10** · `verify_feed_m` **PASS 137/137** ·
`verify_d` V5–V9 **PASS** · `verify_site` **0 errors** · `checklinks` **28 pages OK** ·
`site/verify` **publishable** · `register_r21_r28` idempotent · `engine.results_settlement
--check` OK · `demo_run --check` current.

---

---

## Session `arena/2fa09442-fl1` — task claims (2026-11-14)

**Session ID:** `arena-2fa09442-fl1` · **Branch:** `arena/2fa09442-fl1` (from `main` @ `9d7ca328`, fast-forwarded to `82555e0`) · **Status:** active
**Protocol:** Arena single-branch policy → file-scope isolation, as in earlier sessions. Claim written and pushed before any task work began.

**Pre-claim sweep (all refs fetched, open PRs checked):** active concurrent claims read first —
`arena/0669d4cf-fl1` T21 (`engine/snapshot_store.py`, `engine/results_feed.py`, `tests/test_market_results_store.py`);
`arena/685f958d-fl1` B1–B8 (price-snapshot store, verified results feed, origination order + fair/market/difference columns, leaderboard signal-vs-staking split, demotion gate G-14, official-only correlations, verifier, integration incl. `tools/site.py` NAV + page calls + `README.md`);
`arena/725adbd2-fl1` V9 verifier availability (`scripts/verify_d.py`, `data/verification-d.tsv`);
`arena/f1e4deb7-fl1` price-snapshot store — **merged as PR #22**. The bolded brief items those sessions cover are deliberately NOT claimed here.

| ID | Task | Status | Owner | File scope |
|---|---|---|---|---|
| D1 | **Replacement-depth tracking** — the one bolded brief item ("track the depth of the replacement, not just the fact of a replacement") with no claim on the board: measure how deep each club's own published chart must be read to reach the first player the league has **not** ruled Out (stacked rule-outs included), per slot, Offense/Defense split, league depth distribution; published on `depth.html` with per-row source links; blank + reason where the chart cannot resolve it | in progress | `arena-2fa09442-fl1` | `tools/build.py` (new analysis function only), `tools/site.py` (depth page body region only), `depth.html` (generated), `tools/verify_replacement.py` (new), `data/verification-replacement.tsv` (new) |
| D2 | Line-by-line verification of this session's output; PR → `main`; merge; GitHub Pages deploy confirmation; record here | in progress | `arena-2fa09442-fl1` | PR + this file (append only) |

**Co-ownership note (logged, not edited):** `tools/site.py` is claimed by `arena/685f958d-fl1` for "NAV + page calls only". D1 edits only the depth-page body region (the `depth_html` template and its row builders) and adds no NAV entry. If a merge conflict occurs, both regions are preserved.

**Why D1 was free:** `COORDINATION.md` contains no prior claim mentioning replacement depth; `data/requirements.json` R19 (2nd/3rd/4th-string deficiency) is still `partial`. Existing `nextUp` in `tools/build.py` reports the *next listed* player without skipping strings that are also ruled Out — i.e. it records the fact of a replacement but not its depth. D1 fixes exactly that gap.

**Requests to the integration session (logged per rules, not edited here):** when D1 is verified, R19 in `data/requirements.json` can move `partial → done`; the dashboard/executive-summary wording can cite the new depth-distribution section on `depth.html`.

---

## Session `arena/2fa09442-fl1` — D1 completion record (2026-11-14)

**Status:** D1 **done** on this branch; D2 (PR → main → Pages) follows. Task D1 = the bolded brief item
"track the depth of the replacement, not just the fact of a replacement", claimed above at 22:14:58Z.

### What was built (all re-runnable)

| Deliverable | Path | What it computes |
|---|---|---|
| Replacement-depth analysis | `tools/build.py` → `replacement_depth()` | Per chart ladder (club, unit, slot, line): the string number of the first charted name whose official game status is **not Out** (`depthOut`), the stricter string number of the first name with **no game status at all** (`depthClear`), the full ruled-Out trail, and a separate "thin" list (deeper string ruled Out behind an available first string). Blank + hover reason whenever the club's own chart cannot resolve it — never a guessed number. |
| KC ladder-fold correction | `tools/build.py` → `analyse_depth_league()` | `data/depth-kc.tsv` is a flat capture with no line column; the old fold gave every KC row a globally unique `line`, which (a) split every KC ladder into single-row groups so `nextUp` could never show KC's next listed player, and (b) counted KC's 60 rows as 60 "charted slots" while every other club counts ladders. Ladders are now rebuilt from where the club's own string numbering restarts (documented rule; no player reordered). KC slots 60 → 28; KC `nextUp` now shows Fulton/Johnson/Ezeudu; league totals unchanged (startersWithStatus stays 71). |
| Backup Depth page section | `depth.html` (via `tools/site.py`) | "Replacement depth" section: 71-ladder detail table (first string, ruled-Out trail, depth, first-not-ruled-out name, no-designation depth, sources), by-unit distribution (Offense/Defense/Special Teams + all), and 18 thin ladders. Every row carries the club's chart source chip (S08, S16–S45) **and** S01. |
| Independent verifier | `tools/verify_replacement.py` | A separate walker re-derives every published cell from the committed inputs and diffs it against the rendered HTML: population, cell-by-cell, distribution recount, thin table, source chips (club chip must equal `data/depth-sources.tsv`), blank-reason titles. **Negative-tested**: corrupting one depth cell and removing one source chip both fail the gate. |
| Verification log | `data/verification-replacement.tsv` | 10 checks, all PASS (see below). |

### Sources / verification (every value traceable)

- Inputs: `data/depth.tsv` (31 club charts, S08/S16–S45), `data/depth-kc.tsv` (S08), `data/injuries.tsv` (S01),
  `data/depth-aliases.tsv` (documented name equivalences only).
- `tools/verify_replacement.py` → OK (population 71 = the first-string-status table's population; 0 cell diffs;
  18 thin ladders; 0 missing source chips; 0 missing blank reasons).
- `tools/verify_injuries.py` → 345/345 · `tools/verify_results.py` → 32/32 · `tools/checklinks.py` → OK ·
  `tools/verify_brief.py` → 10/10 (session 685f958d's verifier, run against this branch's merged tree) ·
  `python3 -m unittest discover -s tests` → **107 OK** · full `scripts/` CI sequence locally (6 rebuilds +
  `scripts/verify_site.py` 0 errors) with `git diff --exit-code -- data docs` **CLEAN**.
- **Live spot-checks (fetched this session):** [Titans depth chart](https://www.tennesseetitans.com/team/depth-chart)
  confirms the capture exactly — including that the club publishes **no second string at LG (Skoronski)** and
  **none on the Cody Barton LB row**, which is why those two depths are blank with a reason rather than a guess;
  [nfl.com Week 10 injury report](https://www.nfl.com/injuries/) confirms the game statuses behind the new tables
  for 15 of 15 players checked (Barton, Skoronski, Hill, Moore, Woods, Delane, Walker, Branch, Whyle, Wallace,
  Wayne, Alie-Cox, Benford, Brown, CJ Allen).

### Irregularities found by this session (both fixed here, both logged)

1. **KC ladder-fold bug** (above) — published `nextUp` for KC was blank and the KC charted-slot count was
   inconsistent with every other club. Fixed in `tools/build.py`; effect visible in `depth.html` and `data.js`.
2. **Dashboard overclaim** — the landing-page schedule card said "All 272 regular-season games **with results**";
   only 137 of 272 results exist (`data/results.tsv`). The count is now computed (`len(results)`), not typed.
3. **Claim race on R26 / D1 (needs-review, not blocking):** session `arena/360ca650-fl1` claimed R21–R28
   including replacement depth at **22:12Z**, this session claimed D1 at **22:14:58Z** — ~3 minutes apart, both
   claims pushed to separate branches, neither visible to the other at claim time (verified: their branch did not
   exist at this session's pre-claim `git fetch`; this session's claim commit postdates their claim timestamp).
   File scopes are largely disjoint (theirs: `scripts/build_replacement_depth.py`, `data/replacement_depth.tsv`,
   `replacement-depth.html`; this session: `tools/build.py`, `tools/site.py` depth body, `depth.html`,
   `tools/verify_replacement.py`), so both implementations can ship. **Recommendation for the integration
   session:** cross-check `data/replacement_depth.tsv` (PR #33) against the Backup Depth section row for row —
   two independent implementations agreeing is the strongest verification this requirement can get; if they
   disagree, publish the diff on Flagged for Review rather than picking a winner.

### Regeneration

```
python3 tools/build.py && python3 tools/site.py        # root pages incl. depth.html
python3 tools/verify_replacement.py                    # gate, rewrites the TSV
python3 tools/checklinks.py
python3 -m unittest discover -s tests -q
```

---

## Session `arena/5876146b-fl1` — PR, merge & deployment record (2026-11-14)

- **PR:** [#34 — Verified results feed, own-line origination (side→total→ML), signal/staking
  split, replacement depth, official-only correlations, demotion
  gate](https://github.com/sassnarep3-star/FL1/pull/34)
- **Merge result:** MERGED to `main` (`gh pr merge 34 --merge`), CI `verify-research-build`
  green on the branch at merge time (151 unit tests, verify_brief 10/10, verify_feed_m 137/137,
  verify_d V5–V9, verify_replacement, verify_site 0 errors, checklinks 28 pages).
- **GitHub Pages:** `pages-build-deployment` completed; `https://sassnarep3-star.github.io/FL1/`
  live — `results-feed.html` fetched from the live site and checked end-to-end (row-level feed,
  S61–S69 source chips, walk-forward backtest, cross-links to the parallel registers).
- **Integration summary:** three parallel implementations of the eight brief requirements
  (685f958d, 360ca650/R21–R28, this session M1–M8) preserved in full and cross-linked
  (F31); colliding ids re-issued twice for this session — final ids: sources **S61–S69**,
  flags **F32–F36**, gates **G-16/G-17** (see the final id map above). PRs #22–#33, #35–#36 all
  respected (nothing overwritten; `engine/price_snapshots.py` etc. untouched).

## Task board — session F (`arena/5a8baf03-fl1`) — ACTIVE

**Branch policy (Arena constraint):** this session runs on the Arena-managed branch
`arena/5a8baf03-fl1` and cannot push any other branch. File-scope isolation applies, exactly as
session `arena-3f677e8a-fl1` adopted. No other session is currently active; all tasks below are
claimed by `arena/5a8baf03-fl1` at 2026-11-14. Scopes are additive — no existing register row or
page content is deleted.

| ID | Task | Status | Owner | File scope (claimed) |
|----|------|--------|-------|----------------------|
| F-T1 | Coordination claim (this row) | done | `arena/5a8baf03` | `COORDINATION.md` |
| F-T2 | **Price-snapshot store** — opening + closing numbers for every market originated | done | `arena/5a8baf03` | `data/price_snapshots.csv`, `engine/price_snapshots.py`, `tools/build_snapshots.py`, `price-snapshots.html` |
| F-T3 | **Verified results feed** — settled markets so backtests/ROI are computable | done | `arena/5a8baf03` | `data/settled_markets.csv`, `engine/settlement.py`, `tools/build_results_feed.py`, `results-feed.html` |
| F-T4 | **Origination order** — side first, then total, then moneyline (enforced) | done | `arena/5a8baf03` | `engine/origination.py`, `data/models.json`, `line-origination.html` |
| F-T5 | **Fair line / market line / difference** as separate columns | done | `arena/5a8baf03` | `data/line_board.csv`, `tools/build_line_board.py`, `line-board.html` |
| F-T6 | **Leaderboard: signal score separated from staking score** | done | `arena/5a8baf03` | `engine/leaderboard.py`, `strategies.html` |
| F-T7 | **Depth of replacement** tracked (2nd/3rd/4th string), not just the fact | done | `arena/5a8baf03` | `data/replacement_depth.csv`, `tools/build_replacement_depth.py`, `replacement-depth.html` |
| F-T8 | **Correlations from officially sourced numbers only, n published** | done | `arena/5a8baf03` | `data/correlations_official.csv`, `tools/build_correlations_official.py`, `correlations-official.html` |
| F-T9 | **Demotion gate** — live strategy back to paper, implemented + tested | done | `arena/5a8baf03` | `engine/demotion.py`, `tests/test_requirements_core8.py`, `validation.html` |
| F-T10 | Registers: questions, suggestions, flags, sources; executive summary; README | done | `arena/5a8baf03` | `data/{questions,suggestions,flags}.json`, `data/sources.tsv`, `executive-summary.html`, `README.md` |
| F-T11 | Verification pass: every suite green, every table row sourced, unverified blank + flagged | done | `arena/5a8baf03` | `tools/site.py` (NAV + pages), `tools/checklinks.py` run |
| F-T12 | Integration: PR → main, merge without waiting, confirm Pages, record here | done | `arena/5a8baf03` | PR + `COORDINATION.md` log |

### Completion record — session `arena/5a8baf03-fl1` (F-T2..F-T12)

**Delivered (all re-runnable; engine additions are stdlib-only):**

| Task | Artefacts | Sources / verification | Irregularities |
|------|-----------|------------------------|----------------|
| F-T2 price snapshots | `engine/price_snapshots.py` (store, merged PR #22), `tools/build_snapshots.py`, `data/price_snapshots.csv` (56 rows), `price-snapshots.html` | slate from `data/schedule.tsv` = S04/S49 (official); prices from `data/raw/games.csv` = S47 (third-party, labelled on every row); opens blank (0/56) | **F37** no verified opener source anywhere; the third-party feed records no capture timestamp for closes |
| F-T3 results feed | `engine/settlement.py`, `tools/build_results_feed.py`, `data/settled_markets.csv` (548 rows), `results-feed.html` | 137/137 score join verified vs `data/results.tsv` (reconciled 32/32 vs official standings S02/S03); hard-fail on any score disagreement; 282 W / 262 L / 4 push; flat-bet ROI -0.71%/unit | prices third-party (F39); verified scope is 2026 only (Q34) |
| F-T4 origination order | `engine/origination.py`, `line-origination.html` | order asserted in the build and unit-tested; queue raises on non-originated markets | prior copy described a totals-first architecture; the mandated ORDER (side, total, moneyline) is now executable and tested |
| F-T5 fair/market/difference | `tools/build_line_board.py`, `data/line_board.csv` (56 rows), `line-board.html` | three separate columns; difference convention fixed pre-result (line points; implied-probability points for ML); unit tests | **F38** fair blank (model unfitted); difference blank with it; **F39** market third-party |
| F-T6 signal vs staking | `engine/leaderboard.py` (extended), `strategies.html` | unit test: lucky staking (stakes piled on winners, 50% hit) shows a better staking score yet cannot outrank a 55% signal; masking warning emitted | ranking key is now signal_score; LAS retained in each row; change documented in-page |
| F-T7 replacement depth | `tools/build_replacement_depth.py`, `data/replacement_depth_out.csv` (113 rows), `replacement-depth.html` | 112 affected players on club charts; 91 named replacements (48x2nd, 17x3rd, 11x4th, 13x5th, 2x6th); skip rule uses the club's own chart, Out only | **F40** 21 slots publish no further name; Houston image-only (F16/S46) |
| F-T8 official correlations | `tools/build_correlations_official.py`, `data/correlations_official.csv`, `correlations-official.html` | CO-01 Spearman 0.72299 n=160 (S01); CO-02 -0.08693 n=32; CO-03 0.65280 n=32 (S02/S03); CO-04 -0.16065 n=137 (official-reconciled results); paired bootstrap 95% CI (seed 20261114, 2000) | CO-05 blocked, n=0 until Week 10 settles (**F41**); CO-06/CO-07 blocked by the official-only rule (Q32) |
| F-T9 demotion gate | `engine/demotion.py`, `tests/test_requirements_core8.py`, `validation.html` | D1/D2/D3 + `promotion_check()` unit-tested; INSUFFICIENT_DATA never a pass | the prior session's hand-edited validation.html section was **wiped by regeneration**; found by diffing after `tools/site.py`, ported into the generator (**F42**) |
| F-T10 registers | `data/flags.json` F37-F42, `data/questions.json` Q30-Q34, `data/suggestions.json` SG16-SG30, `README.md`, `EXECUTIVE_SUMMARY.md`, `executive-summary.html` | every new row states its basis; suggestions remain `decision: OPEN` for your review | — |
| F-T11 verification | `tools/checkrows.py` (new row gate), all suites re-run | 95 unit tests · `tools/build.py` · `tools/checklinks.py` 21 pages · `tools/checkrows.py` 3,724 rows (3,624 data rows sourced / 100 register rows) · `tools/verify_injuries.py` 345/345 · `tools/verify_results.py` · `engine/demo_run.py --check` · `python3 -m engine.measure` · `scripts/verify_site.py` 0 errors · `scripts/verify_d.py` V5-V9 PASS · `site/build.py` + `site/verify.py` publishable | checkrows initially failed 519 rows; genuine gaps fixed at the generators (incl. `scripts/build_pages_d.py` schedule + prop tables now per-row sourced) |

**Environment notes (recorded honestly):**
- `scripts/verify_site.py` needs `pandas numpy scipy` (CI installs them in `verify.yml`); the sandbox needed
  `pip install --break-system-packages` to mirror CI. The repo's engine remains stdlib-only.
- `scripts/build_prop_correlations_d.py` needs the workspace mirror parquet (`PROP_PARQUET`); fetched from
  the recorded source (Beexly/Sports `data/nflverse/player_stats_weekly_archive.parquet`) and the rebuild
  was **byte-identical** to `data/prop-correlations-d.csv` (12 rows, join rate 1.0000, 13,384 team-games) —
  exactly what V9 verifies.
- `data/demo_results.json` was regenerated after the leaderboard extension (new score columns);
  `engine/demo_run.py --check` passes and `site/verify.py` no longer reports V7.

**Sources used this pass:** S01 (nfl.com/injuries), S02/S03 (nfl.com/standings), S04/S49 (nfl.com
schedules), S06 (tiebreaking procedures), S46 (Houston depth chart), S47 (nflverse games feed —
third-party, labelled), S48 (Beexly mirror — third-party, labelled), plus the club depth-chart records
already registered. No source was promoted to official in this pass.

**Integration record (F-T12):** appended below after the merge and the Pages check.

**Integration record (F-T12), complete:** PR
[#40](https://github.com/sassnarep3-star/FL1/pull/40) (“Second pass: the eight bolded requirements …
(+ full reconciliation of three parallel sessions)”) merged to `main` with `gh pr merge 40 --merge` at
merge commit `c377bf1a20bac31c37a3438c5b1dc0a60d96dba8` on 2026-11-14. `verify-research-build` workflow
[43652594682](https://github.com/sassnarep3-star/FL1/actions/runs/43652594682) passed. GitHub Pages build
[43652603953](https://github.com/sassnarep3-star/FL1/actions/runs/43652603953) completed successfully
(`status: built`, error: none) and the site is live at https://sassnarep3-star.github.io/FL1/ serving from
`main` `/` (plus `/docs/pages/`, `/docs/computed/`). This completion record is merged to `main` via the
follow-up record PR logged immediately below.

**Merge reconciliation (this branch vs origin/main PRs #25–#32 — sessions 725adbd2, 0669d4cf,
685f958d):** three sessions built overlapping second-pass deliverables. Nothing was discarded:

- `engine/settlement.py` collided (add/add). Theirs (685f958d) is a provenance-checked verified-results
  *store* and keeps the path; this session's market settlement arithmetic moved to `engine/settlement.py`
  (tests and `tools/build_results_feed.py` re-pointed). Both implementations live on.
- Register IDs collided (both sides numbered F18+/SG16+). Theirs keep F18–F22 / SG16–SG19 (merged
  first); this session's entries renumbered F37–F42 / SG30–SG34 with cross-references updated
  (SG31 cites SG17: same demotion-threshold decision family). Questions did not collide (Q30–Q34 stand).
- `results-feed.html` collided (both generated it). Merged into ONE page: their backtest table + 137-row
  results feed (with per-week official page links) are folded into this session's settled-feed page via
  `brief.RESULTS_BODY`; `tools/brief.py` no longer writes that filename (their doubled-`<tr>` row bug fixed
  in the fold). Their `model-lines.html` and `governance.html` pages are kept, generated by `tools/brief.py`.
- **Display-policy conflict, resolved in favour of the user's explicit constraint** ("if a value cannot be
  confirmed from an official source, leave it blank and flag it unverified"): this session had shown
  third-party prices *labelled*; session 685f958d withheld them (their B6 reading). Resolution: the store and
  audit files keep every captured value with provenance (S47/S48 labels), but every published table blanks
  price-derived cells (prices, odds, cover/ROI/PnL, W/L/P counts, prop-correlation estimates) with the reason
  in the cell (F39). Official-source values (scores, standings, injuries, depth, CO-01..04) display normally.
- `tools/site.py` and `scripts/build_pages_d.py` merged both sides: their NAV/cards/banner + B6 withholding
  hunks re-applied onto this session's generators; this session's per-row Source/Record columns kept.
- This session's audit-layer numbers (548 settled rows; 282W/262L/4P; flat-bet ROI −0.71%/unit — from
  labelled third-party prices) remain in `data/settled_markets.csv` and in this record only, each with its
  provenance; the site shows the rows with blank price-derived cells and the reason (F39).


**Second merge reconciliation (this branch vs origin/main PRs #33–#37 — session `arena-5876146b-fl1`,
the "M" pass):** a third session independently implemented the same eight requirements and landed first.
Nothing discarded; the integration rule this time is: **main keeps the canonical site and stores; this
session's audit layer stands beside them.**

- Theirs (canonical): `data/results_feed.csv` (137 games, row-level official verification — per-game
  nfl.com game links, three-way capture agreement via `scripts/verify_feed_m.py` PASS), `engine/demotion.py`
  (`demotion_status`, G-14), `data/replacement_depth.csv` (alias rules + `tools/verify_replacement.py` PASS),
  `engine/snapshots.py`, `data/{price_snapshots,line_board,results_feed,leaderboard_signal_staking,
  origination_order,governance_gates}.json`, fair lines with model coefficients (`data/fair_lines.csv`),
  `tools/site.py` + `scripts/build_pages_m.py` page sets, registers F01–F36 / Q01–Q29 / SG01–SG29,
  tests `test_r21_r28.py` + `test_results_feed.py`.
- Kept from this session (paths renamed to avoid clobbering their generators): `engine/settlement.py`
  + `tools/build_results_feed.py` + `data/settled_markets.csv` (548 market-level settled rows, audit),
  `engine/paper_gate.py` (this session's D1–D3 + `promotion_check`; their `engine/demotion.py` keeps the
  path and its own API — both tested: 168 tests green), `engine/origination.py`, `engine/price_snapshots.py`
  (PR #22 store), `tools/build_{snapshots,line_board,correlations_official,replacement_depth}.py` +
  audit CSVs `data/{price_snapshots,line_board,correlations_official,replacement_depth_out}.csv`,
  `tools/checkrows.py` (the row-source gate — after the merge it audits 29 pages / 4,654 rows and forced
  per-row source cells into every generator table via a `table()`/`page()` sweep in `tools/site.py`).
- Register entries from this session renumbered again: F37–F42 / Q30–Q34 / SG30–SG34, each carrying a
  cross-reference to the overlapping entry from the other sessions (e.g. SG31 cites SG17/Q33; Q32 cites SG19).
  All earlier ids preserved verbatim; total registers now 42 flags / 34 questions / 34 suggestions.
- Display policy (F39) unchanged from the first reconciliation: stores keep labelled third-party values;
  published tables blank price-derived cells with the reason.
- Stale page `correlations-official.html` from this session's generator removed (superseded by their
  `official-correlations.html` + `correlation-register.html`; the data `data/correlations_official.csv`
  and its builder remain — note their separate `data/correlations-official.csv` also exists, hyphen vs
  underscore: both files kept).
- Full gate battery after the merge: 168 tests · `tools/{build,site,checklinks,checkrows}.py`
  (29 pages, 4,654 rows) · `tools/verify_injuries.py` 345/345 · `tools/verify_results.py` ·
  `tools/verify_replacement.py` PASS · `scripts/verify_feed_m.py` PASS (137 games) ·
  `engine/demo_run.py --check` · `site/build.py` + `site/verify.py` publishable ·
  `scripts/verify_site.py` 0 errors · `scripts/verify_d.py` V5–V9 PASS.

---

## Session `arena/2fa09442-fl1` — D2 completion record (PR, merge, Pages)

| Item | Result |
|---|---|
| PR | https://github.com/sassnarep3-star/FL1/pull/36 (branch `arena/2fa09442-fl1` → `main`) |
| CI before merge | `verify-research-build` run 43650935714 → **pass** (31s) |
| Merge | **MERGED** as `20bb8d0` (`gh pr merge 36 --merge`), 2026-11-14 |
| Pages | `gh api repos/sassnarep3-star/FL1/pages` → **status: built**, source `main` / `/` |
| Live verification | `depth.html` re-fetched from the live host: replacement-depth section present (71 ladders, KC row = 28 slots after the fold fix, TEN blanks with reasons). `index.html?cb=20bb8d0` re-fetched with a cache-buster: corrected schedule card **"All 272 regular-season games, 137 results in so far"** is live. (A first read without the cache-buster showed the pre-merge card — the documented CDN cache artefact, not a broken deploy.) |
| Merges in-session | `origin/main` merged twice (PRs #22–#32, then #33); `COORDINATION.md` conflict resolved by keeping both sides' records; no work discarded |
| Post-merge follow-up | cross-check of the two replacement-depth implementations, committed as `3afdcb2` and shipped in the follow-up PR below |

### Cross-check of the two replacement-depth implementations (R26 / D1)

Session `arena/360ca650-fl1` shipped `data/replacement_depth.tsv` (PR #33) from an independent code path.
`tools/verify_replacement.py` now compares it against this session's ladder walk on every run:

- **35 core rows: 31 agree exactly** — including the two Titans ladders (Barton LB, Skoronski LG) where *both*
  implementations return blank (the club publishes no deeper name: confirmed against the live
  [Titans chart](https://www.tennesseetitans.com/team/depth-chart)).
- **17 contingent rows == 17 non-KC thin ladders**, set-equal.
- **4 accepted divergences, enumerated in the code and failing the gate if they grow:**
  1. *Definitional (flagged for review, not an error):* Dallas S and Dallas TE publish **two names at first
     string**. This site reports ladder-level depth (a not-ruled-out name exists at string 1 → depth 1, with the
     ruled-Out name still shown in the trail); their file reports per-missing-starter depth (Locke Out → Thomas,
     depth 2). **Decision needed: which definition is canonical?** Both are published today, on different pages.
  2. *Superseded:* their two KC rows were built from the **pre-fix fold** (each KC row its own ladder), so they
     read "no charted player left"; the fold fix shipped in PR #36 resolves KC RT to depth 2 (Ezeudu) and KC DT to
     a thin ladder. Their file should be regenerated from the fixed fold by whoever owns it next.
- Negative-tested: corrupting one cell in their TSV fails the gate.

### Status

- **D1: done** — replacement-depth tracking published on `depth.html`, verified cell-by-cell by an independent
  walker, cross-checked against a second independent implementation, spot-checked against two live official pages.
- **D2: done** — PR #36 merged, CI green, Pages built, live site verified.
- Open items for the integration session (non-blocking, logged above): the R26/D1 claim race, the Dallas
  dual-first-string definition choice, and regenerating `data/replacement_depth.tsv` from the fixed KC fold.
- Open PRs from other sessions at time of writing: #34 (`arena/5876146b-fl1`), #35 (already merged), #37+ as they appear.

---


## Session `arena/08fef9e9-fl1` — market-data spine, origination run, and the eight brief items

**Session ID:** `sess-08fef9e9` · **Branch:** `arena/08fef9e9-fl1` (from `main` @ `9d7ca328`) · **Started:** 2026-11-14T22:10Z
**Role:** this session also acts as **integrator** (checked `gh pr list --state open` → no open PRs; `git ls-remote --heads origin` → every
other `arena/*` branch already merged or abandoned; `origin/main` == this branch's base). If a new session appears mid-flight it should
claim from the **Unclaimed** list at the bottom of this section, not from the scopes below.

### Scopes claimed (do not edit these files from another session)

| ID | Task | Status | File scope |
|---|---|---|---|
| F01 | Price-snapshot store: opening + closing, every market we originate, append-only, per-feed provenance | in progress | `engine/price_snapshot.py`, `data/market/price_*.tsv`, `data/market/price_manifest.json`, `price-store.html` |
| F02 | Verified results feed: multi-feed reconciliation + settlement engine so backtests and ROI exist | in progress | `engine/results_feed.py`, `data/market/results_feed.tsv`, `results-feed.html` |
| F03 | Origination order enforced: side → total → derived moneyline; fair / market / delta as separate columns | in progress | `engine/originate.py`, `data/market/fair_lines.tsv`, `origination.html` |
| F04 | Leaderboard: signal score and staking score computed and published separately | in progress | `engine/signal_staking.py`, `data/market/leaderboard_split.tsv`, `signal-vs-staking.html` |
| F05 | Depth of the replacement (levels lost, who fills in, what they bring), not just "X is out" | in progress | `engine/replacement_depth.py`, `data/market/replacement_depth.tsv`, `replacement-depth.html` |
| F06 | Correlation publication gate: official-sourced inputs only, `n` published with every value | in progress | `engine/correlation_gate.py`, `data/market/correlations_gated.tsv`, `correlation-gate.html` |
| F07 | Demotion gate: rules that send a live strategy back to paper, with hysteresis | in progress | `engine/demotion.py`, `data/market/demotion_eval.tsv`, `demotion-gate.html` |
| F08 | Decision desk: suggestions + the questions each one hinges on, reviewable before anything is implemented | in progress | `data/market/decisions.json`, `data/market/questions.json`, `decision-desk.html` |
| F09 | Site integration: shared nav module, 8 new pages in the root build, README/exec-summary addenda | in progress | `tools/site.py` (**NAV block + import only**), `tools/site_shell.py`, `tools/pages_market.py`, `index.html` (+1 card), `README.md` (append-only), `EXECUTIVE_SUMMARY.md` (append-only) |
| F10 | Verification pass, flags, tests, PR → main → merge → confirm Pages | in progress | `tests/test_market.py`, `data/flags.json` (append), `data/sources.tsv` (append S70+), `docs/MARKET_SPINE.md`, PR |

**Unclaimed after this session starts (free for another session):** `docs/computed/**`, `archive/**`, `docs/pages/**`,
`scripts/strategy_lab.py`, `scripts/build_week10_board.py`, `schedule.html`, `standings.html`, `injuries.html`, `depth.html`.

### Upstream verification performed before claiming (no other session's data trusted)

- Re-cloned `nflverse/nfldata` (HEAD `69a1fa550eac8edfb6782cac4f92f2350ddd5b9a`, pushed 2026-11-14T22:05Z) and re-hashed every
  file the repo carries under `data/raw/`: `closing_lines.csv`, `sc_lines.csv`, `rosters.csv`, `win_totals.csv` are **byte-identical
  to upstream**; `games.csv` differs from upstream HEAD in **26 fields, all of them moneyline columns of games not yet played**
  (weeks 10–11 of 2026). Score, spread and total columns are unchanged. Recorded as a price-store drift finding, not as an error.
- Measured the disagreement between the two feeds that both claim to price the same games: `closing_lines.csv` vs `games.csv`
  `spread_line` agree on **2,267 / 3,368** game-sides; totals **2,078 / 3,368**; moneyline prices **394 / 3,232**.
- `data/initial_lines.csv` (the only upstream file that claims to be an **opening** price): 2021 regular season only, one sportsbook
  (`WSGT`), no odds, undocumented in upstream `DATASETS.md`, added by a single upstream commit dated 2021-05-22 — before the games
  it contains — and it names the **opposite** favoured team from `games.csv` in **61 of 272** games. Quarantined, not used for ROI.

### Log

| When (UTC) | Entry |
|---|---|
| 2026-11-14T22:10Z | Read board. `main` @ `9d7ca328` (PR #21 merge). All prior session boards/records preserved. No open PRs. |
| 2026-11-14T22:12Z | Upstream re-verification of `data/raw/*` against `nflverse/nfldata` HEAD completed (results above). Baseline checks on this tree: `unittest` 75 OK, `tools/build.py` OK, `tools/site.py` OK (16 pages), `tools/checklinks.py` OK, `tools/verify_injuries.py` 345/345 OK. |

| 2026-11-14T22:14Z | **Conflict, resolved without discarding work.** `git pull --rebase origin main` hit a `COORDINATION.md` conflict: `main` had advanced through PRs #22–#27 while this claim was being written (sessions `4a9893e6`, `f1e4deb7`, `725adbd2` merged, including `d872543` "retain demotion gate in regenerated validation page"). Resolution = take `main`'s board verbatim and re-append this section, per the board's own rule. **Re-scope noted:** `725adbd2` touched the validation-page demotion-gate rendering; this session's F07 therefore ships as a *new* page + engine module and will not edit `validation.html`'s generator output — if `main`'s validation page already carries a demotion gate, both are published and reconciled at integration. |
| 2026-11-14T22:15Z | `git ls-remote` re-checked: branches `arena/4a9893e6-fl1`, `arena/f1e4deb7-fl1`, `arena/725adbd2-fl1` all merged into `main` at `d495ba8`. No open PRs at claim time. |

### Re-scope after live contention (same minute as the claim)

Two sessions are active in parallel, so the claim above is narrowed to what they do not cover:

| Other session | What they own | What this session will NOT do |
|---|---|---|
| `arena/0669d4cf-fl1` (PR #25, open) | `engine/snapshot_store.py`, `engine/results_feed.py`, `tests/test_market_results_store.py`, `docs/market-results-store.md` — the **write-path storage primitives** (fair/market/difference ledger, FINAL-only results importer with hash check) | Write a competing store. `engine/price_snapshots.py` (already on `main`) is reused as-is and imported; no edits to that file or to #25's files |
| `arena/4a9893e6-fl1` (PR #24, merged) | `validation.html` D1–D3 demotion gate, "defined but not active pending a benchmark price (flag F08)" | Re-define D1–D3 or edit their rendering. F07 ships as **activation + evaluation** of those three rules over a real bet log, on a new page, and reports the numbers that F08 says were missing |
| `arena/725adbd2-fl1` (PR #27 merged, #28 open) | `scripts/verify_d.py`, `schedule.html`, `prop-correlations.html`, `validation.html`, `tools/site.py` D1–D3 emitter | Touch `scripts/*_d.py`, `schedule.html`, `prop-correlations.html`, or the D1–D3 emitter block |

**This session's scope after re-scope (F01–F10, updated):** ingestion + published exports into `data/market/*` (a deterministic TSV/JSON export *of* the store, so a reviewer can read the ledger without opening SQLite); `engine/price_snapshot_pipeline.py`, `engine/backtest.py`, `engine/signal_staking.py`, `engine/replacement_depth.py`, `engine/correlation_gate.py`, `engine/demotion_eval.py`; new pages `price-store.html`, `results-feed.html`, `origination.html`, `signal-vs-staking.html`, `replacement-depth.html`, `correlation-gate.html`, `demotion-gate.html`, `decision-desk.html`; `tools/pages_market.py`; two additive edits inside `tools/site.py` (NAV entries + one index card block); `tests/test_market_pipeline.py`; append-only additions to `data/sources.tsv` (S70+) and `data/flags.json`; `README.md` / `EXECUTIVE_SUMMARY.md` append-only addenda; integration PR.

### Follow-up — unit tests, four engine bugs, and the eight pages actually built

| When (UTC) | Entry |
|---|---|
| 2026-11-14T23:45Z | Added `tests/test_market_pipeline.py` (74 tests). Deliberately split: unit tests on synthetic fixtures, plus one class that cross-checks the committed files in `data/market/` against **each other** — never by re-running the function that wrote them, which would only prove the code agrees with itself. |
| 2026-11-14T23:58Z | First run was red: 15 failures, 6 errors. Four were defects in **published numbers**, not test bugs. Fixed in `engine/` and the spine rebuilt (committed `5eea570`). |
| 2026-11-15T00:05Z | Built the eight pages for real (`tools/pages_market.py`, wired into `tools/site.py`), removed the stale "Not built yet" stamp and reworded the four `data/verification.tsv` rows that asserted the pages were unbuilt. Regenerated the six session-D artefacts with the CI toolchain so `verify.yml`'s final `git diff --exit-code -- data docs` cannot fail on the refreshed capture. |

**The four bugs, in the order they were found.** Anyone reading `main` after this merge should know these were live before the tests existed:

1. `results_ledger.settle_side` / `settle_total` took no side argument. An away bet was graded on the **home** margin and an **under** on the over's difference. Both now take `side_key`; the away margin is the negated home margin, the under flips the total difference, and an NFL tie is a push on a two-way moneyline.
2. `backtest` mapped a TOTAL bet's side onto `home`/`away`. `settle_total` reads any side that is not `over` as an under, so every published over bet was graded as an under while being priced at the over. Each market now names its own side, with the derivation written out per market.
3. `signal_staking._points_beat` ignored the side on a spread bet, so the stake-free measure could carry the opposite sign to the settled outcome. It now reads the number the bet was actually struck at, and a test requires the two to agree.
4. `replacement_depth.load_aliases()` read the headerless positional `data/depth-aliases.tsv` with `csv.DictReader`. The first alias was consumed as the header, no `depthName` field was found, and the map came back **empty** — the page advertised "an exact join after alias mapping" while no alias had ever applied.

A fifth, smaller one: `backtest` counted a game as `eligible` only when a bet was written, so "games meeting the condition" and "bets placed" could never differ. The counters are separate now, and selectivity is stated as a share of eligible games.

**Numbers that moved.** The spine is deterministic and `--check` is byte-identical, but the published figures are **not** the ones earlier rows of this log quoted: 23,219 trades, 13,310 published, and every ROI now sits between −1.6% and −6.9% with hit rates 48–51% against a 52.38% break-even. Five rules grade `INVERTED` (mean points beat below zero) and four `POSITIVE MEAN, NOT PROVABLE`. That is the finding: on this capture no rule beats the recorded market number, and the model's 67%-ROI-shaped story does not survive its own settlement arithmetic. Demotion triggers: 28 (D1-SUBSTITUTE 9, D2 7, D3 3, D4 9).

**Files this session touched that another session also owns — please read before rebasing.**

* `tools/site.py` — three additive edits (8 NAV tuples with `flagged.html` last, 8 index cards fed from `pages_market.summary_counts()`, and `import pages_market` inside `main()`). PR #28 (`arena/725adbd2-fl1`) edits the same file's D1–D3 emitter; expect a conflict and keep **both** halves. Nothing in the D1–D3 table was changed here.
* `data/verification.tsv`, `data/flags.json`, `data/questions.json`, `data/suggestions.json`, `data/sources.tsv` — appended only, deduped on the `check`/`id` key. Row counts now: sources 56, questions 25, suggestions 19, flags 27. `data/verification.tsv` is 36 rows and this branch's diff against `main` for it is **17 insertions, 0 deletions** (`git diff origin/main...HEAD -- data/verification.tsv`), so no other session's check row is lost at merge; the per-game file `data/market/results_verification.tsv` (13 rows) is written by the spine and is not the register.
* `docs/computed/week10.html` and `data/week10_signal_board.csv` — regenerated by the **session-D scripts** (`build_week10_board.py` etc.), not by this session's code, because those scripts read `data/raw/games.csv`, whose sha256 changed when the capture was refreshed (`6766de0`). Row counts unchanged at 7,548; the 26 changed fields are moneylines of unplayed games. Run with pandas 3.1.1/numpy/scipy to match `verify.yml`.
* `engine/price_snapshots.py` — **not edited**, as claimed.

### Request against `engine/price_snapshots.py` (F47, restated for the storage owner)

The store's `phase` CHECK accepts `OPEN`, `CLOSE`, `LIVE`. It has no legal value for "a price whose vintage the publisher never stated", which is the true state of 56,624 of the 78,410 ledger rows this session loaded (`vintage_counts` in `data/market/summary.json`): 20,490 were accepted as `CLOSE` on a filename's word, and 1,088 were quarantined. Two shapes, storage owner's choice:

* add a fourth value (`UNDOCUMENTED`) to the CHECK and keep the strict provenance columns (`source_url`, `source_record_id`, `line_origin_version`) mandatory, so widening the enum does not widen the trust boundary; or
* leave the store close-only and treat the exported ledger under `data/market/` as the record of undated prices, which is what ships today.

This session took the second option and published the refusals rather than hiding them. Q35 is the open question for the board; SG36 is the suggestion. Nothing here was patched into that file, and no test in this session asserts its current behaviour — the tests assert this session's loader and ledger only.

### Build / check commands (this follow-up)

```
python3 -m unittest discover -s tests                    # 152 tests, no network, no pandas
python3 scripts/build_market_spine.py                    # ~78 s
python3 scripts/build_market_spine.py --check            # "rebuild is byte-identical"
python3 tools/build.py && python3 tools/site.py && python3 tools/checklinks.py
/home/user/.ci-venv/bin/python scripts/verify_site.py    # errors 0, warnings 0
```

## Current integration task — `arena/2493a657-fl1` (2026-11-17 UTC)

**Role:** final integration and audit follow-up on the current Arena branch. The checkout is fixed to
`arena/2493a657-fl1`; this session will not create or switch branches. Existing completed task records
above are historical evidence and are not reopened.

| ID | Task | Status | Owner | File scope |
|---|---|---|---|---|
| I01 | Audit row-level source strength and surface repository-generator placeholders separately from official evidence | done | `arena/2493a657-fl1` | `tools/source_audit.py`, `tools/checklinks.py` (correct external-fetch claim), `tools/verify_drift.py` (refresh register row-count pins), `data/verification-drift.tsv`, `tools/site.py` (NAV + generated audit page only), `source-audit.html`, `data/source_row_audit.tsv`, `data/sources.tsv` (append S92), `data/flags.json` (append F68), `data/suggestions.json` (append SG48), `tests/test_source_audit.py`, `tests/test_n01_n05.py` (source-count expectation updated for S92 after preserving S89-S91 from upstream), `docs/SOURCE_ROW_AUDIT.md`, this section of `COORDINATION.md` |

This is an additive integration audit. It will not rewrite other session-owned market or injury data,
will not promote third-party sources to official, and will classify unresolvable provenance as a review
finding rather than inferring a source. No other session-owned file is being edited.

### I01 completion record — 2026-11-17 UTC

**Delivered:** `source-audit.html` (in the shared navigation), the deterministic full-row ledger at
`data/source_row_audit.tsv`, the generator `tools/source_audit.py`, and the method note
`docs/SOURCE_ROW_AUDIT.md`. `tools/checklinks.py` no longer refers to the absent
`tools/verify_sources.py`; it explicitly says external URLs are not fetched by that checker. A linked
repository generator is classified as build provenance, not as proof of an NFL fact. Exact URLs already
present in the source registry can be matched to that registry; no trust is inferred merely from a familiar
hostname. `F68` and `SG48` publish the issue and a reviewable path. `S92` identifies the audit itself as a
non-official repository artifact, not an NFL source.

**Current row classification (6,296 rendered table body rows; row counts, not unique claims):** 3,596
point only to sources whose registry entries are marked Official + VERIFIED; 1,244 link only to repository
code/artifacts; 178 have no detected source link; 94 have a direct link not registered by exact URL; 135
cite a source not marked VERIFIED; 434 cite non-official registered sources; 615 combine official with
non-official or unresolved registry references. The buckets are mutually exclusive in the audit ledger.
The report classifies metadata; it does **not** open web pages, confirm their current availability, or verify
the underlying values line by line. Values in unverified/nonofficial classes are not promoted to official.

**Sources and verification:** S92 is the generated audit ledger (repository-only evidence). No NFL source
was newly fetched for this audit. The older official source records are linked in `sources.html`; their
historical registry status is not a fresh re-verification. `python3 tools/site.py` generated the page and
ledger; `python3 tools/checklinks.py` → 44 pages, all internal links/anchors/source IDs resolve;
`python3 tools/checkrows.py` → 44 pages, 6,419 table rows audited; `python3 tools/verify_drift.py` →
19/19 PASS; `python3 tools/verify_injuries.py` → 345/345 exact rows; `python3 scripts/verify_recapture_g.py`
→ PASS (no published injury row absent from the later read; 2 additions and 32 changes reported);
`python3 scripts/verify_results_g.py` → PASS (32/32 standings reconciliation);
`python3 -m unittest discover -s tests -q` → 315 OK. The first full test pass exposed the expected
source-register count assertion; it was updated for S89 and the full suite passed afterward. Existing
ResourceWarnings in older tests remain non-fatal.

**Irregularities surfaced for review:** F67 is High severity because many rendered rows cite code or have
no usable/registered citation. The audit is syntax/registry based and intentionally does not claim those
values are wrong. `scripts/verify_site.py` could not be run in this environment because pandas is absent;
that script requires pandas although the repo's runtime dependency note says no third-party packages are
required. `checklinks.py` does not fetch external URLs. Both constraints are explicitly retained rather
than reported as successful source verification.

### Rebase reconciliation with upstream main (2026-11-17 UTC)

`git pull --rebase origin main` found `origin/main` had advanced from the branch base at `5a076a0` to
`8d41cbe` (PR #50). The incoming work added the official PIT@CIN final, the 2026-11-17 standings read,
source records S89-S91 and F67 for the not-yet-final LAC@BAL game. The audit's original S89/F67 ids
collided. Resolution preserved the incoming records and appended the audit as S92/F68; SG48 was unique.
The source-count regression test now expects 84 rows, and the G-18 drift pins are 48 suggestions / 68
flags. Generated HTML and `assets/js/data.js` were regenerated from the combined data; no upstream
results, flags, sources, or site changes were discarded.

### Final integration — PR #51 and Pages deployment

**PR:** https://github.com/sassnarep3-star/FL1/pull/51 (`arena/2493a657-fl1` → `main`). Merged at
2026-11-17T02:45:20Z with merge commit `00700fdb6d021abc05aef2113ffcbd63dfce5f64` after both
`verify-research-build` checks completed SUCCESS. GitHub Pages is configured for `main` `/`; API build
`1376567311` reports **built** for that merge commit (`https://sassnarep3-star.github.io/FL1/`). The site
includes the Row-Level Source Audit in the global navigation. F68 remains a visible review item; it does
not block publication.

---

## Session `arena/0a100872-fl1` (2026-11-19 — Week-11 fresh reads + brief-coverage audit)

**Session ID:** `arena-0a100872-fl1` · **Branch:** `arena/0a100872-fl1` (from `addeb0a` of `main`, PR #58 merged) ·
**Claimed:** 2026-11-19T~07:00Z · **Status:** active.
**Pre-claim sweep:** `gh pr list --state open` → #57 (`arena/3f12fa46-fl1`, CONFLICTING, another session's branch — not touched) and #59 (`arena/a502c4e0-fl1`, coordination record only, MERGEABLE — left for its owner). `origin/main` = `addeb0a` = branch base. Shared files (`tools/site.py`, `data/sources.tsv`, `data/flags.json`, `data/questions.json`, `data/suggestions.json`, `EXECUTIVE_SUMMARY.md`, `COORDINATION.md`) are touched only as logged here, per the standing additive rule. Canonical frozen corpora (`data/injuries.tsv`, `data/results.tsv`, `data/standings.tsv`, `data/injury_hub_delta.json`) are **not** modified by this session; Week-11 work lands as dated side-reads.

| # | Task | Status | Owner | File scope (claimed) |
|---|------|--------|-------|----------------------|
| J1 | Coordination claim + immediate push | in progress | `arena-0a100872-fl1` | `COORDINATION.md` |
| J2 | Week-11 injury-hub read (clock-bracketed, verbatim capture, shared-grammar parse, delta vs read 4 labelled cross-week; stored level + published delta) | **done** (0a100872, see log below) | `arena-0a100872-fl1` | `raw/injuries-week11-2026-read5.md` (new), `scripts/build_week11_read.py` (new), `data/injuries_2026-11-19.tsv` (new), `data/injury_hub_delta_w11.json` (new), `data/sources.tsv` (append S100), `data/flags.json` (append only if irregularity found), `tests/test_week11_read.py` (new) |
| J3 | Week-11 schedule + standings fresh reads (dated side-reads; canonical corpora untouched) | claimed | `arena-0a100872-fl1` | `raw/schedule-week11-2026.md` (new), `raw/standings-2026-20261119.tsv` (new), `data/slate-w11-2026.tsv` (new), `data/standings_2026-11-19.tsv` (new), `data/sources.tsv` (append S101–S102) |
| J4 | Brief-coverage audit (every brief line → evidence page/file or explicit gap) + Week-11 site page + exec-summary block | claimed | `arena-0a100872-fl1` | `docs/BRIEF_COVERAGE.md` (new), `tools/pages_week11.py` (new), `tools/site.py` (NAV + import + render call + index card only), `week11-read.html` (generated), `EXECUTIVE_SUMMARY.md` (prepend session block only), `data/verification-drift.tsv` (pin refresh if counts move) |
| J5 | Full verification battery, PR → `main`, merge without waiting, confirm GitHub Pages deploy, record in this file | claimed | `arena-0a100872-fl1` | PR + `COORDINATION.md` completion record |

**First push = this claim, per the brief.**

### Session arena-0a100872-fl1 — log (branch `arena/0a100872-fl1`)

- **J1 claim** commit `9569059`. **J2 done** (this log).
- **J2 sources:** `https://www.nfl.com/injuries/` read 5, Week 11 of 2026 (source **S100**, `data/sources.tsv`). Fetched via fetch_page in 7 chunks (chunkIndex 0–6, totalChunks 7); staged in `raw/.chunks-w11/`; assembled verbatim into `raw/injuries-week11-2026-read5.md`. One chunk-boundary newline (Riley Moss row, DEN) was rejoined; the capture header says so. News pointers are condensed to headline + link and are not injury rows.
- **J2 output:** `scripts/build_week11_read.py` → `data/injuries_2026-11-19.tsv` (253 player rows, 24 clubs with tables; CIN and WAS show "No Injuries Reported"; hub header shows WEEK 11; 13 games). Every row carries the hub URL and its official `nfl.com/players/` link. Mapped codes only from the published strings (FULL 83 / LIMITED 87 / DNP 83; Out 9 / Questionable 7 / blank 237). `data/injury_hub_delta_w11.json`. `tests/test_week11_read.py` (6 gates, pass).
- **Delta:** `delta: null`. No earlier Week 11 read exists, so no like-for-like delta is published. Week 10 reads are not compared. The first Week 11 delta lands with the next read.
- **Verification performed:** row count equals the count of player-link lines in the raw capture; every raw line reproduces its row; unmapped practice/game strings fail loudly; 362 unit tests run, all green after pinning the S-register count 91→92 in `tests/test_n01_n05.py` (S100 added); `tools/checkrows.py` OK 58 pages / 7359 rows; `tools/verify_drift.py` 19/19 PASS.
- **Irregularities (flagged, not corrected; 78 flags in the JSON):**
  1. Surname/first-name vs link slug: Jacob Hummel (HOU) links to `jake-hummel`; Dee Alford (BUF) links to `deaundre-ford` (surname not in slug); LeQuint Allen Jr. (JAX) links to `lequint-allen`.
  2. Lions Kerby Joseph, Cade Mays, D.J. Reed: game status blank in this read. The earlier brief cites these as Out (VR-08, VR-12); this read does not confirm that, so it stays blank and unverified.
  3. 72 DNP-in-practice players with blank game status (publish blank, unverified).
- **Request to integration session (not edited by me):** `week11-read.html` is not linked from `index.html`. The site's link checker reports it as orphan. Add a card or nav entry in the integration session. The page exists; `tools/checklinks.py` will stay at 1 finding until that happens.
- **Still open in this session:** J3 (schedule + standings Week 11 side-reads) and J4 (brief-coverage audit, exec-summary block, the NAV wiring) are not started. J5 (PR → merge → Pages) waits until the integration session confirms the claims. The brief has about 100 requirement lines; `docs/BRIEF_COVERAGE.md` will list each one as covered or as an explicit gap. Many items (price-snapshot policy, availability graph, depth register, 32-team sweep, parlay gate, etc.) remain gaps in this session.

