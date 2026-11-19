# FL1 — Executive Summary

**Session:** `arena/a502c4e0-fl1` · **Branch:** `arena/a502c4e0-fl1` (from `5a076a0` of `main`; rebased onto `22482a9` and `970f0ac`) · **Built:** 2026-11-17
**Site:** https://sassnarep3-star.github.io/FL1/

> **Reading note.** This file carries more than one session's summary. The block immediately
> below is the current one (2026-11-19). Earlier blocks are preserved verbatim further down
> because they record work that is still in the repository; where they conflict with a later
> re-verification, the later one is marked as superseding.

---

## Session `arena/9d880d91-fl1` — 2026-11-19 (brief re-audit, fresh Week 11 reads, integration)

### What this session set out to do

Re-check the whole project brief line by line against the committed files (the backlog was last
written 2026-11-16 and predates later sessions' work), take fresh dated reads of the official pages
now that Week 11 is live, refresh this summary, and land it through a PR to `main` with the site
verified end to end. No canonical table was replaced; no register owned by another session was
rewritten.

### What it found

1. **Six backlog rows were stale; the files were right.** `data/requirements_backlog.json`
   (2026-11-16) contradicts committed files on R37 (two-sided change-of-mind fields exist on 6 of 6
   strategies), R47 (margin + total ablations run; holdout CIs contain zero), R55 (the joint-evidence
   gate is implemented: 3 pairs published, 4 held with reasons, 0 combos ranked), R83 (reserve list
   captured, 25 rows), R44 (dated schedule announcement published beside the live schedule), and R76
   (a `__CONTROL_MARKET` control exists in the computed leaderboard, though not in the plan register
   and with no random-picks control anywhere). Readiness D-rows were correct in each case. The
   corrections are published with computed evidence on the new **Brief Audit** page
   (`brief-audit.html`, `data/brief_audit_9d88.json`); the backlog file itself was not rewritten.

2. **One provenance error found, not fixed here.** The schedule announcement block cites source S86,
   but S86 in `data/sources.tsv` is the nflverse win-totals feed — the announcement article has no
   source record. Published as irregularity J-F1; the register fix belongs to the sources owner
   (logged in COORDINATION.md).

3. **Week 10 is closed and verified again from the live page.** A fresh read of
   `nfl.com/standings/league/2026/REG` (2026-11-19) matches the 2026-11-17 closeout side-read on
   32 of 32 clubs, 0 differing rows (V1). The Week 11 slate matches the 2026-11-17 capture 13 of 13
   (V2). The canonical `data/results.tsv` (137 rows) was deliberately not promoted — Q44 is still
   the owner's decision.

4. **First Week 11 injury read captured.** `nfl.com/injuries/` now shows WEEK 11 (Thursday game
   IND at HOU tonight). Read 1 parses at 253 rows across 24 clubs with tables, plus CIN/WAS
   "No Injuries Reported" (V3). Game statuses exist only for the Thursday clubs (9 Out, 7
   Questionable); every Sunday/Monday club is a practice-only read with blank game status, and the
   Injuries column is blank on 237 of 253 rows — both preserved as blank, never interpreted.

5. **PR #57 ID collision logged.** PR #57 (`arena/3f12fa46-fl1`) reuses source IDs S89–S90 and flag
   IDs F67–F68, which `main` already holds (S89–S99, F67–F72). It must re-key to S100+/F73+ on
   rebase. Its Game Book / matchup-matrix / weather claims remain unmerged; on `main` those
   requirements (R45, R64, R77) are still not-started/blocked, as the audit confirms.

### What it built

| Artefact | File | Re-runnable |
|---|---|---|
| Brief re-audit (59 rows, 6 corrections, 5 irregularities) | `data/brief_audit_9d88.json`, `brief-audit.html` | `python3 tools/build_brief_audit_9d88.py` + `python3 tools/site.py` |
| Fresh-read verification (V1–V4, all PASS) | `scripts/verify_9d88.py`, `data/verification-9d88.tsv` | `python3 scripts/verify_9d88.py` |
| Week 11 injury read 1 (253 rows, dated, hash-pinned in git) | `raw/injuries-week11-2026-read1.md` | page-fetch of `nfl.com/injuries/` (2026-11-19) |
| Live standings + slate side-reads | `raw/live/2026-11-19-standings-league-reg.tsv`, `raw/live/2026-11-19-week11-slate.tsv` | page-fetch (2026-11-19) |
| Tests (15 new) | `tests/test_brief_audit_9d88.py` | `python3 -m unittest discover -s tests` |

### Verification (2026-11-19)

371 unit tests OK · `tools/build.py` + `tools/site.py` (58 pages) + checklinks (all resolve) +
checkrows (7,089 rows) · verify_drift 19/19 · verify_injuries 345/345 · verify_results PASS (32/32) ·
verify_9d88 4/4 PASS.

### Decisions left open (unchanged, by design)

- **Q44** (canonical promotion of the 150-row closeout), **Q23/Q37** (price-data policy),
  **Q21/Q30** (opening-price source), **Q40** (canonical pre-kickoff snapshot), **Q42**
  (Wed/Thu/Fri capture cadence). The site's honest state is unchanged: fair lines are originated,
  market cells stay blank where no official price exists, and the leaderboard has no eligible winner.

---

## Session `arena/a502c4e0-fl1` — 2026-11-17 (Week-10 closeout, Q44 acceptance run, freshness sweep)

### What this session set out to do

Close Week 10 against official sources with no manual input: run the Q44 promotion
acceptance checks the moment the last game reached FINAL, take a fresh dated injury-hub read,
publish every register the brief requires, and land it all through a PR to `main` with the
site verified end to end.

### What it found

1. **The week closed exactly as Q44 prescribed — and the acceptance run now exists.**
   The Monday-night final (Chargers 23, Ravens 20; Game Center "Final", quarter scores
   10-7-3-3 / 0-10-3-7 summing to the total) landed at ~04:29 UTC on 2026-11-17. A
   clock-bracketed read of the official schedule page captured all 14 Week-10 games FINAL
   (S98), and eight acceptance gates in `scripts/promote_week10.py` all PASS
   (`data/verification-promote.tsv`): fixture membership, cross-read agreement with the
   12 finals already on record, late-final provenance (no in-progress score was ever
   carried forward), 32-of-32 W/L/T/PF/PA points arithmetic against a fresh standings read,
   append-only prefix of the frozen corpus, per-club game counts, no duplicates, and the
   byte-prefix chain **137 → 148 → 149 → 150** across four dated reads.

2. **The canonical feed was deliberately NOT promoted.** Q44's policy half — rolling
   `data/results.tsv` forward — would refit every published model coefficient computed from
   it, and F59's doctrine ("a backtest corpus that silently grows is not a corpus") plus the
   pre-registration requirements argue for a reviewer decision instead of a silent append.
   The closeout is published as dated side-reads (`data/results_2026-11-17-closeout.tsv`,
   150 rows; `data/standings_2026-11-17-closeout.tsv`), and the runner's `--promote` mode
   prints the exact 13-step rebuild-and-re-verify sequence the owner would execute. The
   earlier same-day 149-row SNF read (session e97f05c3) is preserved byte-identically as
   its prefix; their gate files were never touched.

3. **Parallel sessions merged mid-run — IDs were re-keyed, not overwritten.** Main advanced
   from `5a076a0` to `22482a9` (PRs #49–#54) while this session worked, taking sources
   S89–S93 and flags F67–F69. This session's additions were renumbered to **S97–S99 /
   F71** in a clean rebase (conflicts resolved in COORDINATION.md, sources, flags,
   verify_drift; the sources prefix S01–S88 restored intact). The new F67 (MNF open) was
   resolved by exactly the re-read it asks for.

4. **The league-standings route went stale after the final; the division route did not.**
   Four reads of `nfl.com/standings/league/2026/REG` after the whistle still printed the
   pre-game state (LAC 0-8/121/219, BAL 4-5/189/236), byte-identical to the pre-game
   arithmetic — while `nfl.com/standings/division/2026/REG` already carried the settled
   rows (LAC 1-8/144/239/1W, BAL 4-6/209/259/5L). The closeout capture takes the fresh
   route, documents the stale reads with their clocks, and flags the divergence (F72).
   Nothing was inferred: a stale row would have failed the points-arithmetic gate, and did.

5. **Register cross-references were mis-wired (F71).** Q44 paired "SG35" (the prices
   collector), F59 pointed at SG36 (undated-vintage labels), and SG43 — the actual
   promotion suggestion — paired Q35 (the storage question). The three records describe one
   decision family and were wired to three others. Q44's recommended_path now names SG43
   with a pointer to F71; the other two remain as published history under the flag.

6. **Injury hub read 4 is a delta, not a snapshot.** A clock-bracketed read
   (2026-11-17T02:33:27Z–02:43:50Z, 8 chunks, 347 rows/28 clubs) against reads 1–2 moved
   exactly two practice designations (BUF Shavers FULL→LIMITED, CIN Parker FULL→DNP), zero rows added or removed — each change re-checked line by
   line against all three captures before publishing (S97; `delta (r3→r4) in
   `data/injury_hub_delta.json`).

### What it built

| Artefact | File | Re-runnable |
|---|---|---|
| Week-10 closeout captures | `raw/schedule-results-2026-week10-closeout.tsv`, `raw/standings-2026-20261117.tsv` | clock-bracketed reads, verbatim |
| Acceptance gates P1–P8 | `scripts/promote_week10.py` | `python3 scripts/promote_week10.py` (idempotent; `--execute` gated; `--promote` prints the owner sequence) |
| Dated side-reads | `data/results_2026-11-17-closeout.tsv` (150), `data/standings_2026-11-17-closeout.tsv` (32) | produced by `--execute` |
| Closeout register + gate table | `data/week10_closeout.json`, `data/verification-promote.tsv` | rebuilt by the runner |
| Injury read 4 + delta | `raw/injuries-week10-2026-read4.md`, `data/injury_hub_delta.json` | `python3 scripts/build_injury_hub_delta.py` |
| Site sections | verified-results-feed (closeout + gates), injuries (read-3 delta), Snapshot-Ledger row | `python3 tools/site.py` |
| Registers | sources S97–S99, flags F71–F72, Q44 acceptance record, DR-10 pin 72 | appended, drift-checked |

### Verification (2026-11-17, final sweep)

342 unit tests OK · `tools/build.py` + `tools/site.py` + checklinks (57 pages) +
checkrows (7,046 rows, every data row sourced) · verify_results PASS (32/32) ·
verify_results_g PASS (G-R1–R4) · verify_results_2026_11_17 GATE PASS (their gates intact)
· verify_injuries OK · verify_drift 19/19 · verify_brief 10/10 · verify_site (CI pandas
venv) 0 errors / 0 warnings · CI-equivalent six-builder rebuild byte-identical (clean
`data/`+`docs/` diff) · CI `verify` check green on every push.

### Decisions left open (unchanged, by design)

- **Q44 policy half:** execute `scripts/promote_week10.py --execute --promote` (canonical
  roll-forward + 13-step refit sweep) or keep extending by dated reads. Acceptance checks
  are done; the choice is the owner's, exactly as the registers require.
- **Q46** (main's new question): whether the 2026-11-17 live injury capture joins the
  current table — this session's read 3 stays a delta beside it, consistent with either
  answer.

---

## Session `arena/7ac4e12e-fl1` — 2026-11-17

### What this session did

1. **Dated injury read 3, published as a delta only.** The official hub was re-read inside a
   clock-bracketed window (02:35:39Z–02:36:52Z), captured verbatim (8 chunks, 63 KB), and parsed with
   the shared grammar: 347 rows, matching read 2's claim. One field moved — **NO Travis Etienne,
   practice FULL → LIMITED** — and that single change is what the site publishes under
   `data/injury_hub_delta.json` (read 1 → read 2 kept as history). The canonical 345-row table was
   not rewritten. Sources: S94.

2. **Week 10 close-out, with the live game left alone.** A second official read
   (02:45:45Z–02:46:39Z) shows **13 of 14 games FINAL** — the new one being Sunday Night Football,
   **PIT 18, CIN 38** — while Monday Night Football (LAC at BAL) was live (Q2, 17–7). A partial score
   is not a result: the extension publishes the final as `completion.new_final`, keeps the live game
   as a status row with blank scores, and checks **C1–C5** pass, including a 32-of-32 recomputation of
   records *and* points/allowed against a fresh official standings capture. The pre-existing F61
   claimed "all 14 FINAL on 2026-11-16" — impossible on any 11-16 UTC read — and carries a dated
   correction. Canonical `data/results.tsv` untouched (promotion stays Q44). Sources: S95, S96.

3. **Every open question now has an answer.** All 46 rows of `data/questions.json` gained
   `answer_state` + `answer` + `answer_date`: **12 answered** from evidence already in the repo,
   **16 partial** (facts stated, named gap remains), **18 open** (owner decision or missing dataset,
   with the exact clearing item). `questions.html` renders the dated Answer column with counts. The
   pass also caught **Q45 duplicating Q35 verbatim** — recorded as F70 rather than answered twice.

4. **Rebased over four parallel PRs without losing either side.** `main` advanced mid-session (#49,
   #51–#54). After the rebase, this session's register ids were shifted to `S94–S96 / F70 /
   SG50–SG51` because the earlier-merged sessions already held `S89–S93 / F67–F69 / SG48–SG49`;
   Q46 (theirs) was answered alongside the original 45; every pin and drift row was repaired and the
   battery re-run: **344 tests, 57 pages, 0 unsourced rows, 19/19 drift pins**.

### What this session did not do

No canonical feed was promoted (Q44 open), no new official page types were captured (terms question
Q18/Q42 open), and no previously published status was upgraded — scope not re-verified here keeps
the status its earlier sessions gave it.

---

## Session `arena/dbf11de0-fl1` — 2026-11-16

### What this session set out to do

Take the project brief line by line, check each line against an official source, and publish —
for every requirement — **the gate that blocks it** and **the number that would clear it**.

### What it found

1. **The official injury report is a series, not a snapshot.** Reading `nfl.com/injuries` on
   2026-11-14 gave 345 rows across 28 clubs. Reading the same URL on 2026-11-16 gave 347 rows:
   two Baltimore rows appeared (Calais Campbell, Ronnie Stanley) and 32 fields moved. **22 of the
   32 are Chargers rows** — Los Angeles played on Monday night, so its game-day designations did
   not exist when the earlier read was taken. Indianapolis's Arden Key moved the other way, from
   Questionable to no designation at all. Both reads are now committed with sha256 hashes and the
   diff between them is published. The earlier read is never overwritten: doing so would inject
   lookahead into any backtest. (`raw/injuries-week10-2026-recapture-2026-11-16.md`,
   `data/injury_diff_g.tsv`.)

2. **Three Lions designations the review flagged as blank are in fact published.** Kerby Joseph,
   Cade Mays and D.J. Reed all carry **Out** on the official page, and the published table already
   showed Out. Re-verified on 2026-11-16 (check G-V5 in `data/verification-g.tsv`).

3. **A row-count claim in an earlier review could not be reproduced.** The review recorded 254
   published rows against 279 live. Both of this session's reads parse to 345 and 347. The
   discrepancy is flagged (F43) rather than reconciled by picking a number.

4. **The requirement register tracked 28 of the brief's roughly seventy lines.** The remaining
   lines are now registered (R29–R87), each with a status, the gate that blocks it, and the number
   that would clear it. 12 of the 87 rows are blocked or waiting on a decision.

5. **"Remove luck" is now a number, not a slogan.** Over 137 official 2026 results the home team
   won 48.9% of games; the 95% interval is 40.7% to 57.2%, which contains 50%. The exact two-sided
   p-value against a coin flip is 0.864. Detecting a 5-point edge at conventional significance
   needs **785 independent decisions**, or **1,211** once six strategies are tried — more than
   three NFL seasons of every game.

6. **NFL.com publishes dated starter announcements.** The daily roundup carries a "DEPTH CHART
   NEWS" section. Eleven announced-starter rows are now published, each **quoted** with its date
   and link (Carson Beck ARI, Deshaun Watson CLE, Harrison Butker KC, Kirk Cousins MIN, Drew Lock
   SEA, Jalen Milroe SEA, Sam Darnold SEA, Kyle McCord MIA, Malik Willis MIA, TreVeyon Henderson
   NE, Lamar Jackson BAL). One name from the brief — Brissett, Arizona — appears on no official
   page this session read, so that row is **blank and flagged**, not filled in (F44).

### What it built

| Artefact | File | Re-runnable |
|---|---|---|
| Dated re-capture + row-by-row diff | `raw/injuries-week10-2026-recapture-2026-11-16.md`, `data/injury_diff_g.tsv`, `scripts/verify_recapture_g.py` | yes — exits non-zero if a published row is missing from the later read |
| Requirement backlog (R29–R87) | `data/requirements_backlog.csv`, `scripts/build_backlog_g.py`, `requirements-backlog.html` | yes |
| Decision-readiness table on the landing page | `index.html` (section `#decision`), `tools/site_g.py` | yes |
| Removal-of-luck panel | `engine/luck.py`, `scripts/build_luck_g.py`, `data/luck_panel.json`, `removal-of-luck.html` | yes — 25 new unit tests |
| Per-team availability view | `scripts/build_availability_g.py`, `data/team_availability.csv`, `team-availability.html` | yes |
| Announced-starter evidence | `data/announced_starters.csv`, `announced-starters.html` | yes |
| Point-in-time snapshot ledger | `availability-ledger.html` | yes |
| Registers: 3 sources, 6 flags, 4 questions, 4 suggestions | `scripts/register_g.py` | yes |

### Verification run at completion

`python3 -m unittest discover -s tests -q` → **193 tests OK** (168 pre-existing + 25 new).
`tools/build.py` → clean. `tools/verify_injuries.py` → 345/345 rows match the raw capture.
`tools/verify_results.py` → PASS, 32/32 clubs. `tools/checklinks.py` → 33 pages, every link and
anchor resolves. `tools/checkrows.py` → 33 pages, 4,998 rows, every row sourced.
`scripts/verify_recapture_g.py` → GATE PASS.

### Irregularities published, not hidden

F43 row-count discrepancy · F44 Brissett not evidenced · F45 the report moved between reads ·
F46 depth-chart register has no capture date · F47 venue/roof/surface only from a third-party feed
· F48 model outputs store a line, not a probability with inputs.

---

## Earlier session summary — `arena-ab82c93f` (2026-11-14, preserved)

**Session:** `arena-ab82c93f` · **Branch:** `arena/ab82c93f-fl1` · **Built:** 2026-11-14
**Site:** https://sassnarep3-star.github.io/FL1/

---

## The one-paragraph version

Sixteen pre-registered betting strategies were tested against real closing prices on 5,336 NFL
games from 2006 to 2026. **None passed all seven validation gates, so the leaderboard pays out
zero reward.** A control that bets every home team lost 5.2%, which is exactly what the bookmaker's
vig should cost — and that control sits closer to zero than almost every real candidate. The
measured correlation between an against-the-spread cover and the game total is −0.0001, so pars
and same-game builds are not underpriced either. The honest state of the project is: **the
infrastructure is built and trustworthy, the edge is not yet found, and the two things blocking
progress are a data-access problem and a set of unanswered questions that only you can answer.**

---

## What is actually deliverable today

| Delivered | Evidence | Status |
|---|---|---|
| Reproducible line-origination engine (causal Elo → spread/total), priced against real closes | `scripts/strategy_lab.py`, calibration error 2.89 pts MAE, r = 0.828 | Works; not yet *better* than the market |
| 16 strategies × 7 pre-registered gates, walk-forward 2006–2026 with 2020+ held out | `data/strategies.csv` | Done; 0 approved |
| Correlation engine (same-game, cross-game, parlay economics) | `data/correlations.csv`, `data/parlay_economics.csv` | Done; props blocked |
| Availability model from official-derived injury reports | `data/availability_2025.csv` (388 team-weeks) | 2025 only |
| Official Week 10 2026 injury report, hand-verified | `data/week10_2026_official.csv`, 345 rows, per-row official link + verbatim quote | Done |
| Quarterback availability tracking by actual starter | `data/depth_deficiency.csv` | Done; QB only |
| 9 irregularities, 9 unverified items, 16 open questions, 12 ranked suggestions | `data/` registers | Done |
| Static GitHub Pages site, 14 pages, build gate that fails on any unsourced row | `docs/`, `scripts/verify_site.py` | Done |

---

## The five numbers that matter

1. **0 of 16** strategies approved. Gate G6 (multiple-testing) was the killed-at-the-line gate for
   the best candidates; the effective significance bar is p < 0.00313.
2. **−5.2%** ROI for betting every home team over 5,067 bets. That is the vig, and it is the
   baseline any "edge" has to clear.
3. **+7.2%** ROI for the best raw candidate (`WIND15_UNDER`, 425 bets, p = 0.063). It fails
   significance, fails the multiple-testing bar, and is not even implementable as written because it
   uses **post-game measured wind** — information that does not exist before kickoff.
4. **−0.0001** correlation between home cover and over (95% CI −0.028 to 0.029). A 4-leg parlay of
   −110 legs is **−17.0% EV**. Correlation does not rescue it.
5. **345 rows / 28 clubs / 14 games** of official Week 10 2026 injury data, joined to closing
   prices, with **zero** unsourced cells.

---

## What I could not do, and why (this is the part to read)

| Gap | Root cause | What it needs |
|---|---|---|
| No 2nd/3rd/4th-string depth model | No reachable source publishes depth order. NFL.com roster pages list status and jersey number only; the nflverse `depth_charts` release is unreachable. | **OQ-07** — a timestamped depth-chart feed |
| No player-prop combo pricing | No prop line/outcome dataset obtainable | **OQ-08** |
| Injury history is one season | The nflverse release CDN is outside this environment's network allowlist | **OQ-05 / SG-01** — one allowlist entry unblocks four items |
| No independent line yet | Result-history Elo contains only information the market already has | **SG-08** — pace/EPA/pressure inputs, and an opening-line feed |
| No 2026 out-of-sample result | `games.csv` has one completed Week 10 game | Re-run after Week 18 |

I did not fill any of these gaps with an estimate. Every affected cell is blank and every affected
item is on the Flagged for Review page.

---

## Decisions now waiting on you

Ranked by how much they unblock:

1. **Can the release CDN be reached?** (OQ-05) One infra change; unblocks injuries backfill, depth
   charts and snap counts at once. This is the highest-leverage item in the entire project.
2. **Where does an authoritative depth chart come from?** (OQ-07) Without it, one of your core
   requirements — knowing when a defence is on its 3rd string — cannot be built at all.
3. **What number counts as "luck removed"?** (OQ-10) The gates are numbers. Right now the
   thresholds are my defaults, not your decision, which means any "approved" strategy would be
   approved against a bar you never set.
4. **What price can you actually get?** (OQ-01) Every ROI here is measured against the close. If you
   can only get the close, roughly half of any model-vs-close gap is fictional.
5. **Who signs off on a live test, and with what stake?** (OQ-14) Rewards need accountability.

The full list is on the **Open questions** page, and the ranked paths are on **Suggestions**.

---

## Suggested next session

1. Land **SG-01** (CDN access) and **SG-02** (freeze the gate config in a signed file).
2. Commission a depth-chart source (**SG-05**) — this is the only route to your stated requirement.
3. Re-run `strategy_lab.py` after Week 18 with a 2026 holdout, and re-test `DIV_DOG_AND_ELO`
   specifically: it is the only candidate with a plausible shape (5 of 7 gates, +8.1% out-of-sample)
   that died on deflation rather than on being wrong.
4. Do **not** promote the weather strategy. p = 0.063 across 16 searches, using an input that is not
   available pre-game, is the textbook picture of noise.

---

## How to audit any number on the site

Every figure names its source file. Every source file names its URL and SHA-256 in
`data/raw/MANIFEST.json`. Re-run:

```
python3 scripts/fetch_data.py && python3 scripts/build_availability.py \
  && python3 scripts/build_correlations.py && python3 scripts/strategy_lab.py \
  && python3 scripts/build_week10_board.py && python3 scripts/build_registers.py \
  && python3 scripts/build_site.py && python3 scripts/verify_site.py
```

The last command exits non-zero if any table row lacks a source link, any internal link is broken,
any gate column is malformed, or any reward is paid to an unapproved strategy.

---

## Requirements sprint — R21–R28 (session `arena-360ca650-fl1`, 2026-11-14)

Eight system requirements were implemented on top of the layers above, each with its engine code,
tests, data artefact and page:

| # | Requirement | Where it landed | State |
|---|---|---|---|
| R21 | Price-snapshot store: opening **and** closing numbers for every market we originate | `engine/snapshots.py`, `data/price_snapshots.json`, `price-snapshots.html` | 56 rows (Week 10 slate, SIDE→TOTAL→MONEYLINE order). 28 closes sourced (third-party capture); **0 opens** — no opening-price source exists, every open cell blank and flagged |
| R22 | Verified results feed so backtests and ROI can be computed at all | `engine/backtest.py`, `data/results_feed.json`, `results-feed.html` | 137 official rows; recomputing all 32 clubs' records reproduces the official standings exactly |
| R23 | Originate the side first, then the total, then the moneyline | `engine/fairline.py`, `line-origination.html` | Order fixed in code and enforced in the store; supersedes the earlier "totals-first" note (F27) |
| R24 | Model fair line, market line, difference as **separate columns** | `data/line_board.json`, `line-board.html` | 42 rows; fair = computed from official numbers with coefficients published (HFA −0.02 pts, n=137; margin sd 13.23, n=137); market = pinned third-party capture (F23); difference blank when either side blank |
| R25 | Separate **signal** from **staking** in the leaderboard | `engine/backtest.py`, `data/leaderboard_signal_staking.json`, `strategies.html` | Rank computed from the flat-stake signal block only; staking reported beside it and structurally unable to move a rank |
| R26 | Track the **depth of the replacement**, not just the fact | `data/replacement_depth.tsv`, `replacement-depth.html` | 52 affected slots, each naming the next available player's string (2nd/3rd/4th); contingent depth recorded before it hurts |
| R27 | Correlations **only** from officially sourced numbers, **n** published with each | `engine/corr_official.py`, `data/correlations_official.json`, `correlation-register.html` | 5 rows (r = 0.88 n=32; −0.16 n=137; 0.43 n=121; blank n=1; −0.09 n=32). Non-official registers excluded by code |
| R28 | Demotion gate: a live strategy goes back to paper | `engine/demotion.py`, G-14 in `data/validation_gates.json`, `validation.html#G-14` | D1 signal decay / D2 drawdown / D3 CLV rot; re-promotion needs 300 fresh settled bets |

### Decisions only the owner can make (each is a question + options on the site)

1. **Q21/Q22 — price sources.** Opening and moneyline prices have no source at all. Approve a licensed
   line history (SG21) or start recording opens prospectively (SG20). Until then the cells stay blank.
2. **Q23 / F-11 — market-price policy.** The brief demands the market column; the verification rule
   demands blanks for unconfirmed values. Provisional answer: publish with a THIRD_PARTY badge + flag
   (F23). Strict blanks are one review away.
3. **Q24/Q25 — competition rules.** Demotion thresholds (F28) and allowed staking plans need a signature.
4. **F30 (severity High) — computed-layer break-even is circular.** `strategy_lab.py` computes
   `breakeven_hit = 1/(1+realized ROI)` instead of the price hurdle, which makes its G4 "beats_vig" gate
   unusable and fails every strategy by construction. Not silently fixed: transcribed with a warning
   (SG28 is the one-line fix + rebuild).

### Audit trail for the sprint

```
python3 scripts/build_results_feed.py && python3 scripts/build_price_snapshots.py \
  && python3 scripts/build_line_board.py && python3 scripts/build_correlations_official.py \
  && python3 scripts/build_replacement_depth.py && python3 scripts/build_signal_staking.py \
  && python3 tools/site.py && python3 tools/checklinks.py
python3 -m unittest discover -s tests -q      # 102 tests, includes the sprint rules
python3 scripts/verify_site.py                # 0 errors, 0 warnings
python3 tools/verify_injuries.py && python3 tools/verify_results.py
```

All of the above pass as of the merge. Verification records: `COORDINATION.md`, `data/verification-d.tsv`.
## Executive summary addendum — session `arena-5876146b-fl1` (2026-11-14)

This session closed the eight structural gaps the brief calls out. Everything below is built,
verified and live on the site; every number is reproducible from the committed scripts.

### What now exists (with where to look)

1. **Price-snapshot store** — an append-only, provenance-requiring observation store for opening
   and closing numbers of every market we originate (`engine/price_snapshots.py`, PR #22). Storage
   capability is real; publishable prices remain blocked on an authorized feed (Q-02, flag F34) —
   no official NFL source prices betting lines.
2. **Verified results feed** ([results-feed.html](results-feed.html)) — 137 games of 2026, every
   final verified row-by-row against official nfl.com week pages (S49, S61–S69) and cross-checked
   three ways (137/137 PASS). Settlement and ROI are computed by `engine/results_feed.py`, which
   fails closed on undeclared price provenance. Backtests can now be computed at all — against
   verified scores only.
3. **Origination order** ([originations.html](originations.html)) — side first, then total, then
   moneyline, as mandated. For all 272 markets of 2026 the page publishes the **model's fair
   line, the market line and the difference as three separate columns**. The fair-line engine is
   proved identical to the Computed Research Layer's engine (5,336/5,336 pre-game Elo values)
   and reproduces its calibration (MAE 2.89, corr 0.828, n=5,336). The fair TOTAL is deliberately
   blank (flag F33) because its model has no fitted parameter.
4. **Signal vs staking** ([signal-vs-staking.html](signal-vs-staking.html)) — the leaderboard
   ranks, rewards and promotes on the SIGNAL ledger (flat stakes) only; staking is risk
   telemetry. The split immediately earned its keep: **three candidate entries show a positive
   staking run over a non-positive signal** (DOME_OVER, DOME_UNDER, __CONTROL_MARKET) — masked,
   unranked by it.
5. **Replacement depth** ([replacement-depth.html](replacement-depth.html)) — 69 affected Week-10
   lineup spots, each with the replacement's string and the cascade count; one NE RB case runs to
   3rd string with a player Out above him; six spots have no listed replacement left (blank and
   flagged, never filled).
6. **Official-only correlations with n** ([official-correlations.html](official-correlations.html))
   — C-O1 same-game scoring r=+0.076 (n=137); C-O2/C-O3 form persistence |r|<0.09 (n=242). All
   near zero: on official numbers alone, scoring "form" in 2026 to date is noise, and game-level
   parlay legs priced as independent are close to the truth.
7. **Demotion gate** (G-14 on the signal-vs-staking page) — a live strategy returns to PAPER on
   signal decay, risk breach or compliance breach; automatic execution, documented re-entry, and
   the asymmetry rule: staking can never promote but a staking risk breach can demote.
8. **Suggestions & questions** — unchanged and unblocked: 15 suggestions with options and one
   recommended path each ([suggestions.html](suggestions.html)), 20 open questions stating what we
   know, lack and how to obtain it ([questions.html](questions.html)).

### The decisions that still unblock the most

| # | Decision | Unblocks | Question |
|---|----------|----------|----------|
| 1 | Authorize a price feed behind the price-snapshot store | CLV, hold realism (G-7), live origination comparison | Q-02 |
| 2 | Fit the totals model (S2) on official drive data | the blank fair-total column (F33), total origination | GAP-05 |
| 3 | Rule on third-party-derived values (F-11) | promoting measured correlation/edge values into the registers | F-11 |
| 4 | Confirm cash-reward legality review | reward structure beyond compute/capital promotion | Q-13 |
| 5 | Acquire machine-readable depth charts (Houston) | 32/32 replacement-depth coverage (F16) | — |

### Verification performed this session (all green)

`verify_feed_m.py` 137/137 PASS · `checklinks.py` 21 pages PASS · `verify_site.py` 0 errors 0
warnings · `unittest discover` 92 tests OK · `engine.demo_run.py --check` current ·
`engine.measure` reproducible · `verify_d.py` V5–V9 PASS (V7a flagged by design) ·
`site/build.py + site/verify.py` 18 pages publishable. Session D's V9 was restored in a fresh
workspace by `scripts/fetch_prop_mirror_m.py` (pinned git blob sha) and the rebuild is
byte-identical to the committed artefact.

---

## Second pass — the eight bolded requirements (session `arena/5a8baf03-fl1`, 2026-11-14)

The brief's eight bolded items now each have a concrete, re-runnable artefact. Every number below is
regenerated by a committed script from committed inputs; nothing is typed in by hand.

| Requirement | Delivered | Verified numbers | Where |
|---|---|---|---|
| Price-snapshot store (open **and** close for every market originated) | Append-only, source-bound SQLite store + Week 10 export | 14 slate games x 4 market rows = 56 rows; **0 opening prices** (no verified opener source exists — F37); 56 closing/latest values recorded in the store with third-party provenance; blank on the site display per the no-unverified-values rule (F39) | `engine/price_snapshots.py`, `data/price_snapshots.csv`, `price-snapshots.html` |
| Verified results feed (backtests/ROI computable) | Settled markets from scores reconciled 32/32 against official standings | 137 verified games, 548 settled market rows (audit layer: 282W/262L/4P, flat-bet ROI -0.71%/unit from labelled third-party prices — recorded in the data file, withheld from site display, F39) | `engine/settlement.py`, `data/settled_markets.csv`, `results-feed.html` |
| Origination order: side, then total, then moneyline | Executable queue that raises on anything else | `ORIGINATION_ORDER = ("side","total","moneyline")`; board order asserted at build | `engine/origination.py`, `line-origination.html` |
| Fair line / market line / difference as separate columns | Origination board with the three columns and a fixed difference convention | 56 board rows; fair **blank** (model coefficients unfitted — F38); difference **blank** with it; market blank — third-party values recorded in data/line_board.csv only (F39) | `data/line_board.csv`, `line-board.html` |
| Signal separated from staking in the leaderboard | Two scores, two ranks; overall rank follows signal; masking warning where staking outranks signal | Unit-tested: a 50%-hit-rate entry with stakes piled on winners shows a better staking score yet cannot outrank a 55% signal | `engine/leaderboard.py`, `strategies.html` |
| Depth of replacement tracked, not just the fact | String of the club's own next man up, per affected slot | 112 affected players; 91 name a replacement — 48 second-string, 17 third, **11 fourth**, 13 fifth, 2 sixth; 21 publish no further name; Houston blank (F40) | `data/replacement_depth_out.csv`, `replacement-depth.html` |
| Correlations only from officially sourced numbers, n published | Register computed exclusively from official captures | CO-01 rho 0.723 (n=160), CO-02 -0.087 (n=32), CO-03 0.653 (n=32), CO-04 -0.161 (n=137); CO-05..07 **blocked, n=0, blank** | `data/correlations_official.csv`, `correlations-official.html` |
| Demotion gate: live back to paper | D1 decay / D2 calibration drift / D3 concentration, implemented and tested; promotion requires G1-G6 all PASS | Too-small windows return INSUFFICIENT_DATA, never a pass | `engine/demotion.py`, `validation.html` |

### Irregularities found and fixed in this pass

1. **A hand-edited page was being silently destroyed by the build.** The demotion-gate section had been
   added directly to `validation.html`; `tools/site.py` regenerates that file, so the section vanished on
   the next build. Found by re-running the build and diffing; fixed by porting the section into the
   generator (flag F42). The pattern is the finding: edit the generator, never the artefact.
2. **Row-level sourcing was prose, not links, on five tables.** The new `tools/checkrows.py` gate (every
   data row must carry a source link or publish nothing) initially failed 519 rows; all genuine gaps were
   fixed at the generators — including the computed layer's schedule and prop-correlation tables — and the
   gate now passes 3,724 rows on 21 pages.

### What is still blocked (all on Flagged for Review)

Opening prices (F37), fair lines (F38), anything needing an official odds source (F39), replacement depth
where clubs publish no further name (F40), the week-10 availability-vs-outcome correlation until the week
settles (F41). Four questions (Q30-Q34) and five suggestions (SG16-SG30) were added for your decision;
none of them is answered unilaterally.

---

## Final integration addendum — session `arena-a4c5a1de-fl1` (2026-11-16)

**Stale-PR takeover (coordination rule: claim >60 min stale).** Two complete, CI-green PRs whose
sessions went inactive were integrated: **#38** (`arena/08fef9e9-fl1`, the market-data spine: 9 engine
modules, 8 pages, 74 unit tests, four settlement bugs it found in its own first pass) and **#39**
(`arena/2fa09442-fl1`, the cross-check gate between the two independent replacement-depth
implementations). Nothing discarded: colliding engine paths renamed with importers repointed
(`engine/backtest_spine.py`, `engine/originate_spine.py`), colliding page outputs re-issued
(`results-feed-market.html`, `signal-vs-staking-market.html`, `replacement-depth-market.html`),
register ids re-issued per repo convention (flags F43–F52, questions Q35–Q39, suggestions SG35–SG38,
sources S77–S76) with every in-file reference retagged inside the spine's own files only.

**All 28 tracked requirements now show `done` on [Requirements](requirements.html).** The last four
partials were closed with published evidence: R11 (numeric fair | market | difference boards on
`line-board.html` and `origination.html`), R12 (fitted signals, walk-forward 13,310 published bets,
headline finding F50: the model's own signal is negative against the recorded market number on all
three markets), R16 (official-operand correlation register with n + Fisher CIs, plus the correlation
gate that publishes its refusals with reasons), R19 (71 verified replacement-depth ladders,
cross-checked by two independent implementations). Status changes cite their evidence on the
requirements page itself.

**Known-open items are unchanged and stay on [Flagged for Review](flagged.html)**: no official price
source exists (F34/F39), opening prices for 2026 are uncapturable from official channels (F43), CLV
is unmeasurable until a dated snapshot collector runs (F49, SG35), the undated-vintage vocabulary
decision (Q35), and the benchmark-policy decision (Q37). These do not block the merge; they are the
owner's decision list.

## Session `arena-38a78804-fl1` — live refresh + brief-gap sprint N01–N06 (2026-11-16)

Fresh official captures (both clock-timed, transcribed verbatim, all re-runnable) plus five brief
requirements that no prior session had built. Nothing already published was overwritten.

**New verified data (official NFL.com, read 2026-11-16 ~01:15–01:25 UTC):**

1. **Second dated read of the injury hub (S77).** The hub still showed *WEEK 10*. Delta vs the
   2026-11-14 read: **32 field changes + 2 added rows + 0 removed** — every change belongs to a
   report still evolving (both Monday-night clubs; Baltimore grew 8→10 rows; one Colts row cleared).
   The three Lions designations flagged earlier were already populated in the 2026-11-14 re-capture.
   Published as a delta register (`data/injury_hub_delta.json` + new section on `injuries.html`);
   the level is never re-published. Reserve-list events referenced on the hub (TreVeyon Henderson
   IR, Malik Willis IR, Lamar Jackson IR roundups) are recorded as pointers, never as table rows.
2. **Week 10 finals (S78).** 12 of 13 games printed FINAL at read time: 11 new finals captured.
   The two non-final games (SNF in progress, MNF unplayed) are published as **pending with blank
   scores** — nothing inferred. Verification V1–V4 in `scripts/build_week10_extension.py`:
   TNF corroborates the existing feed; every final is a published fixture; record arithmetic for
   all 32 clubs reproduces the page's game-card records; and the feed + new finals reproduce the
   fresh official standings (S79) **including PF/PA, 32/32**.

**Brief requirements closed:**

- **Decision-readiness table on the landing page (N01)** — one row per requirement R01–R28 with
  the gate that blocks it and the number that would clear it; blockers cite published question and
  flag records only (`scripts/build_decision_readiness.py`, fails if the register drifts).
- **Two-sided "what would change our mind" field on every strategy entry (N02)** — both directions
  populated for ST01–ST06, each naming the data it needs or the open question that owns it.
- **Removal-of-luck panel on the dashboard (N05)** — the luck-removed edge (95% CI lower bound vs
  break-even hurdle) for all 16 computed entries: **0 proven; all 7 positive-ROI entries rejected
  on signal**; control baseline (home teams at the close, −5.19% over 5,067 bets) and the 16-trial
  multiplicity adjustment shown beside.
- **Open question Q35 + suggestion SG35** — the promotion policy for moving verified finals into
  the canonical feed after a week completes (owner decision; pairs with the V1–V4 machinery).

**Verification this session:** 192 unit tests OK (24 new); `tools/checklinks.py` 28 pages OK;
`scripts/verify_site.py` 0 errors/0 warnings; `tools/verify_injuries.py` 345/345;
`tools/verify_results.py` PASS; `scripts/verify_d.py` V5–V8 PASS (V9 BLOCKED by design — uncommitted
parquet input); `engine/demo_run.py --check` current; docs sub-site builds 18 pages, 0 unsourced rows.

---

## Session `arena/dbf11de0-fl1` — 2026-11-16

### What this session set out to do

Take the project brief line by line, check each line against an official source, and publish —
for every requirement — **the gate that blocks it** and **the number that would clear it**.

### What it found

1. **The official injury report is a series, not a snapshot.** Reading `nfl.com/injuries` on
   2026-11-14 gave 345 rows across 28 clubs. Reading the same URL on 2026-11-16 gave 347 rows:
   two Baltimore rows appeared (Calais Campbell, Ronnie Stanley) and 32 fields moved. **22 of the
   32 are Chargers rows** — Los Angeles played on Monday night, so its game-day designations did
   not exist when the earlier read was taken. Indianapolis's Arden Key moved the other way, from
   Questionable to no designation at all. Both reads are now committed with sha256 hashes and the
   diff between them is published. The earlier read is never overwritten: doing so would inject
   lookahead into any backtest. (`raw/injuries-week10-2026-recapture-2026-11-16.md`,
   `data/injury_diff_g.tsv`.)

2. **Three Lions designations the review flagged as blank are in fact published.** Kerby Joseph,
   Cade Mays and D.J. Reed all carry **Out** on the official page, and the published table already
   showed Out. Re-verified on 2026-11-16 (check G-V5 in `data/verification-g.tsv`).

3. **A row-count claim in an earlier review could not be reproduced.** The review recorded 254
   published rows against 279 live. Both of this session's reads parse to 345 and 347. The
   discrepancy is flagged (F43) rather than reconciled by picking a number.

4. **The requirement register tracked 28 of the brief's roughly seventy lines.** The remaining
   lines are now registered (R29–R87), each with a status, the gate that blocks it, and the number
   that would clear it. 12 of the 87 rows are blocked or waiting on a decision.

5. **"Remove luck" is now a number, not a slogan.** Over 137 official 2026 results the home team
   won 48.9% of games; the 95% interval is 40.7% to 57.2%, which contains 50%. The exact two-sided
   p-value against a coin flip is 0.864. Detecting a 5-point edge at conventional significance
   needs **785 independent decisions**, or **1,211** once six strategies are tried — more than
   three NFL seasons of every game.

6. **NFL.com publishes dated starter announcements.** The daily roundup carries a "DEPTH CHART
   NEWS" section. Eleven announced-starter rows are now published, each **quoted** with its date
   and link (Carson Beck ARI, Deshaun Watson CLE, Harrison Butker KC, Kirk Cousins MIN, Drew Lock
   SEA, Jalen Milroe SEA, Sam Darnold SEA, Kyle McCord MIA, Malik Willis MIA, TreVeyon Henderson
   NE, Lamar Jackson BAL). One name from the brief — Brissett, Arizona — appears on no official
   page this session read, so that row is **blank and flagged**, not filled in (F44).

### What it built

| Artefact | File | Re-runnable |
|---|---|---|
| Dated re-capture + row-by-row diff | `raw/injuries-week10-2026-recapture-2026-11-16.md`, `data/injury_diff_g.tsv`, `scripts/verify_recapture_g.py` | yes — exits non-zero if a published row is missing from the later read |
| Requirement backlog (R29–R87) | `data/requirements_backlog.csv`, `scripts/build_backlog_g.py`, `requirements-backlog.html` | yes |
| Decision-readiness table on the landing page | `index.html` (section `#decision`), `tools/site_g.py` | yes |
| Removal-of-luck panel | `engine/luck.py`, `scripts/build_luck_g.py`, `data/luck_panel.json`, `removal-of-luck.html` | yes — 25 new unit tests |
| Per-team availability view | `scripts/build_availability_g.py`, `data/team_availability.csv`, `team-availability.html` | yes |
| Announced-starter evidence | `data/announced_starters.csv`, `announced-starters.html` | yes |
| Point-in-time snapshot ledger | `availability-ledger.html` | yes |
| Registers: 3 sources, 6 flags, 4 questions, 4 suggestions | `scripts/register_g.py` | yes |

### Verification run at completion

`python3 -m unittest discover -s tests -q` → **193 tests OK** (168 pre-existing + 25 new).
`tools/build.py` → clean. `tools/verify_injuries.py` → 345/345 rows match the raw capture.
`tools/verify_results.py` → PASS, 32/32 clubs. `tools/checklinks.py` → 33 pages, every link and
anchor resolves. `tools/checkrows.py` → 33 pages, 4,998 rows, every row sourced.
`scripts/verify_recapture_g.py` → GATE PASS.

### Irregularities published, not hidden

F43 row-count discrepancy · F44 Brissett not evidenced · F45 the report moved between reads ·
F46 depth-chart register has no capture date · F47 venue/roof/surface only from a third-party feed
· F48 model outputs store a line, not a probability with inputs.

---

## Earlier session summary — `arena-ab82c93f` (2026-11-14, preserved)

**Session:** `arena-ab82c93f` · **Branch:** `arena/ab82c93f-fl1` · **Built:** 2026-11-14
**Site:** https://sassnarep3-star.github.io/FL1/

---

## The one-paragraph version

Sixteen pre-registered betting strategies were tested against real closing prices on 5,336 NFL
games from 2006 to 2026. **None passed all seven validation gates, so the leaderboard pays out
zero reward.** A control that bets every home team lost 5.2%, which is exactly what the bookmaker's
vig should cost — and that control sits closer to zero than almost every real candidate. The
measured correlation between an against-the-spread cover and the game total is −0.0001, so pars
and same-game builds are not underpriced either. The honest state of the project is: **the
infrastructure is built and trustworthy, the edge is not yet found, and the two things blocking
progress are a data-access problem and a set of unanswered questions that only you can answer.**

---

## What is actually deliverable today

| Delivered | Evidence | Status |
|---|---|---|
| Reproducible line-origination engine (causal Elo → spread/total), priced against real closes | `scripts/strategy_lab.py`, calibration error 2.89 pts MAE, r = 0.828 | Works; not yet *better* than the market |
| 16 strategies × 7 pre-registered gates, walk-forward 2006–2026 with 2020+ held out | `data/strategies.csv` | Done; 0 approved |
| Correlation engine (same-game, cross-game, parlay economics) | `data/correlations.csv`, `data/parlay_economics.csv` | Done; props blocked |
| Availability model from official-derived injury reports | `data/availability_2025.csv` (388 team-weeks) | 2025 only |
| Official Week 10 2026 injury report, hand-verified | `data/week10_2026_official.csv`, 345 rows, per-row official link + verbatim quote | Done |
| Quarterback availability tracking by actual starter | `data/depth_deficiency.csv` | Done; QB only |
| 9 irregularities, 9 unverified items, 16 open questions, 12 ranked suggestions | `data/` registers | Done |
| Static GitHub Pages site, 14 pages, build gate that fails on any unsourced row | `docs/`, `scripts/verify_site.py` | Done |

---

## The five numbers that matter

1. **0 of 16** strategies approved. Gate G6 (multiple-testing) was the killed-at-the-line gate for
   the best candidates; the effective significance bar is p < 0.00313.
2. **−5.2%** ROI for betting every home team over 5,067 bets. That is the vig, and it is the
   baseline any "edge" has to clear.
3. **+7.2%** ROI for the best raw candidate (`WIND15_UNDER`, 425 bets, p = 0.063). It fails
   significance, fails the multiple-testing bar, and is not even implementable as written because it
   uses **post-game measured wind** — information that does not exist before kickoff.
4. **−0.0001** correlation between home cover and over (95% CI −0.028 to 0.029). A 4-leg parlay of
   −110 legs is **−17.0% EV**. Correlation does not rescue it.
5. **345 rows / 28 clubs / 14 games** of official Week 10 2026 injury data, joined to closing
   prices, with **zero** unsourced cells.

---

## What I could not do, and why (this is the part to read)

| Gap | Root cause | What it needs |
|---|---|---|
| No 2nd/3rd/4th-string depth model | No reachable source publishes depth order. NFL.com roster pages list status and jersey number only; the nflverse `depth_charts` release is unreachable. | **OQ-07** — a timestamped depth-chart feed |
| No player-prop combo pricing | No prop line/outcome dataset obtainable | **OQ-08** |
| Injury history is one season | The nflverse release CDN is outside this environment's network allowlist | **OQ-05 / SG-01** — one allowlist entry unblocks four items |
| No independent line yet | Result-history Elo contains only information the market already has | **SG-08** — pace/EPA/pressure inputs, and an opening-line feed |
| No 2026 out-of-sample result | `games.csv` has one completed Week 10 game | Re-run after Week 18 |

I did not fill any of these gaps with an estimate. Every affected cell is blank and every affected
item is on the Flagged for Review page.

---

## Decisions now waiting on you

Ranked by how much they unblock:

1. **Can the release CDN be reached?** (OQ-05) One infra change; unblocks injuries backfill, depth
   charts and snap counts at once. This is the highest-leverage item in the entire project.
2. **Where does an authoritative depth chart come from?** (OQ-07) Without it, one of your core
   requirements — knowing when a defence is on its 3rd string — cannot be built at all.
3. **What number counts as "luck removed"?** (OQ-10) The gates are numbers. Right now the
   thresholds are my defaults, not your decision, which means any "approved" strategy would be
   approved against a bar you never set.
4. **What price can you actually get?** (OQ-01) Every ROI here is measured against the close. If you
   can only get the close, roughly half of any model-vs-close gap is fictional.
5. **Who signs off on a live test, and with what stake?** (OQ-14) Rewards need accountability.

The full list is on the **Open questions** page, and the ranked paths are on **Suggestions**.

---

## Suggested next session

1. Land **SG-01** (CDN access) and **SG-02** (freeze the gate config in a signed file).
2. Commission a depth-chart source (**SG-05**) — this is the only route to your stated requirement.
3. Re-run `strategy_lab.py` after Week 18 with a 2026 holdout, and re-test `DIV_DOG_AND_ELO`
   specifically: it is the only candidate with a plausible shape (5 of 7 gates, +8.1% out-of-sample)
   that died on deflation rather than on being wrong.
4. Do **not** promote the weather strategy. p = 0.063 across 16 searches, using an input that is not
   available pre-game, is the textbook picture of noise.

---

## How to audit any number on the site

Every figure names its source file. Every source file names its URL and SHA-256 in
`data/raw/MANIFEST.json`. Re-run:

```
python3 scripts/fetch_data.py && python3 scripts/build_availability.py \
  && python3 scripts/build_correlations.py && python3 scripts/strategy_lab.py \
  && python3 scripts/build_week10_board.py && python3 scripts/build_registers.py \
  && python3 scripts/build_site.py && python3 scripts/verify_site.py
```

The last command exits non-zero if any table row lacks a source link, any internal link is broken,
any gate column is malformed, or any reward is paid to an unapproved strategy.

---

## Requirements sprint — R21–R28 (session `arena-360ca650-fl1`, 2026-11-14)

Eight system requirements were implemented on top of the layers above, each with its engine code,
tests, data artefact and page:

| # | Requirement | Where it landed | State |
|---|---|---|---|
| R21 | Price-snapshot store: opening **and** closing numbers for every market we originate | `engine/snapshots.py`, `data/price_snapshots.json`, `price-snapshots.html` | 56 rows (Week 10 slate, SIDE→TOTAL→MONEYLINE order). 28 closes sourced (third-party capture); **0 opens** — no opening-price source exists, every open cell blank and flagged |
| R22 | Verified results feed so backtests and ROI can be computed at all | `engine/backtest.py`, `data/results_feed.json`, `results-feed.html` | 137 official rows; recomputing all 32 clubs' records reproduces the official standings exactly |
| R23 | Originate the side first, then the total, then the moneyline | `engine/fairline.py`, `line-origination.html` | Order fixed in code and enforced in the store; supersedes the earlier "totals-first" note (F27) |
| R24 | Model fair line, market line, difference as **separate columns** | `data/line_board.json`, `line-board.html` | 42 rows; fair = computed from official numbers with coefficients published (HFA −0.02 pts, n=137; margin sd 13.23, n=137); market = pinned third-party capture (F23); difference blank when either side blank |
| R25 | Separate **signal** from **staking** in the leaderboard | `engine/backtest.py`, `data/leaderboard_signal_staking.json`, `strategies.html` | Rank computed from the flat-stake signal block only; staking reported beside it and structurally unable to move a rank |
| R26 | Track the **depth of the replacement**, not just the fact | `data/replacement_depth.tsv`, `replacement-depth.html` | 52 affected slots, each naming the next available player's string (2nd/3rd/4th); contingent depth recorded before it hurts |
| R27 | Correlations **only** from officially sourced numbers, **n** published with each | `engine/corr_official.py`, `data/correlations_official.json`, `correlation-register.html` | 5 rows (r = 0.88 n=32; −0.16 n=137; 0.43 n=121; blank n=1; −0.09 n=32). Non-official registers excluded by code |
| R28 | Demotion gate: a live strategy goes back to paper | `engine/demotion.py`, G-14 in `data/validation_gates.json`, `validation.html#G-14` | D1 signal decay / D2 drawdown / D3 CLV rot; re-promotion needs 300 fresh settled bets |

### Decisions only the owner can make (each is a question + options on the site)

1. **Q21/Q22 — price sources.** Opening and moneyline prices have no source at all. Approve a licensed
   line history (SG21) or start recording opens prospectively (SG20). Until then the cells stay blank.
2. **Q23 / F-11 — market-price policy.** The brief demands the market column; the verification rule
   demands blanks for unconfirmed values. Provisional answer: publish with a THIRD_PARTY badge + flag
   (F23). Strict blanks are one review away.
3. **Q24/Q25 — competition rules.** Demotion thresholds (F28) and allowed staking plans need a signature.
4. **F30 (severity High) — computed-layer break-even is circular.** `strategy_lab.py` computes
   `breakeven_hit = 1/(1+realized ROI)` instead of the price hurdle, which makes its G4 "beats_vig" gate
   unusable and fails every strategy by construction. Not silently fixed: transcribed with a warning
   (SG28 is the one-line fix + rebuild).

### Audit trail for the sprint

```
python3 scripts/build_results_feed.py && python3 scripts/build_price_snapshots.py \
  && python3 scripts/build_line_board.py && python3 scripts/build_correlations_official.py \
  && python3 scripts/build_replacement_depth.py && python3 scripts/build_signal_staking.py \
  && python3 tools/site.py && python3 tools/checklinks.py
python3 -m unittest discover -s tests -q      # 102 tests, includes the sprint rules
python3 scripts/verify_site.py                # 0 errors, 0 warnings
python3 tools/verify_injuries.py && python3 tools/verify_results.py
```

All of the above pass as of the merge. Verification records: `COORDINATION.md`, `data/verification-d.tsv`.
## Executive summary addendum — session `arena-5876146b-fl1` (2026-11-14)

This session closed the eight structural gaps the brief calls out. Everything below is built,
verified and live on the site; every number is reproducible from the committed scripts.

### What now exists (with where to look)

1. **Price-snapshot store** — an append-only, provenance-requiring observation store for opening
   and closing numbers of every market we originate (`engine/price_snapshots.py`, PR #22). Storage
   capability is real; publishable prices remain blocked on an authorized feed (Q-02, flag F34) —
   no official NFL source prices betting lines.
2. **Verified results feed** ([results-feed.html](results-feed.html)) — 137 games of 2026, every
   final verified row-by-row against official nfl.com week pages (S49, S61–S69) and cross-checked
   three ways (137/137 PASS). Settlement and ROI are computed by `engine/results_feed.py`, which
   fails closed on undeclared price provenance. Backtests can now be computed at all — against
   verified scores only.
3. **Origination order** ([originations.html](originations.html)) — side first, then total, then
   moneyline, as mandated. For all 272 markets of 2026 the page publishes the **model's fair
   line, the market line and the difference as three separate columns**. The fair-line engine is
   proved identical to the Computed Research Layer's engine (5,336/5,336 pre-game Elo values)
   and reproduces its calibration (MAE 2.89, corr 0.828, n=5,336). The fair TOTAL is deliberately
   blank (flag F33) because its model has no fitted parameter.
4. **Signal vs staking** ([signal-vs-staking.html](signal-vs-staking.html)) — the leaderboard
   ranks, rewards and promotes on the SIGNAL ledger (flat stakes) only; staking is risk
   telemetry. The split immediately earned its keep: **three candidate entries show a positive
   staking run over a non-positive signal** (DOME_OVER, DOME_UNDER, __CONTROL_MARKET) — masked,
   unranked by it.
5. **Replacement depth** ([replacement-depth.html](replacement-depth.html)) — 69 affected Week-10
   lineup spots, each with the replacement's string and the cascade count; one NE RB case runs to
   3rd string with a player Out above him; six spots have no listed replacement left (blank and
   flagged, never filled).
6. **Official-only correlations with n** ([official-correlations.html](official-correlations.html))
   — C-O1 same-game scoring r=+0.076 (n=137); C-O2/C-O3 form persistence |r|<0.09 (n=242). All
   near zero: on official numbers alone, scoring "form" in 2026 to date is noise, and game-level
   parlay legs priced as independent are close to the truth.
7. **Demotion gate** (G-14 on the signal-vs-staking page) — a live strategy returns to PAPER on
   signal decay, risk breach or compliance breach; automatic execution, documented re-entry, and
   the asymmetry rule: staking can never promote but a staking risk breach can demote.
8. **Suggestions & questions** — unchanged and unblocked: 15 suggestions with options and one
   recommended path each ([suggestions.html](suggestions.html)), 20 open questions stating what we
   know, lack and how to obtain it ([questions.html](questions.html)).

### The decisions that still unblock the most

| # | Decision | Unblocks | Question |
|---|----------|----------|----------|
| 1 | Authorize a price feed behind the price-snapshot store | CLV, hold realism (G-7), live origination comparison | Q-02 |
| 2 | Fit the totals model (S2) on official drive data | the blank fair-total column (F33), total origination | GAP-05 |
| 3 | Rule on third-party-derived values (F-11) | promoting measured correlation/edge values into the registers | F-11 |
| 4 | Confirm cash-reward legality review | reward structure beyond compute/capital promotion | Q-13 |
| 5 | Acquire machine-readable depth charts (Houston) | 32/32 replacement-depth coverage (F16) | — |

### Verification performed this session (all green)

`verify_feed_m.py` 137/137 PASS · `checklinks.py` 21 pages PASS · `verify_site.py` 0 errors 0
warnings · `unittest discover` 92 tests OK · `engine.demo_run.py --check` current ·
`engine.measure` reproducible · `verify_d.py` V5–V9 PASS (V7a flagged by design) ·
`site/build.py + site/verify.py` 18 pages publishable. Session D's V9 was restored in a fresh
workspace by `scripts/fetch_prop_mirror_m.py` (pinned git blob sha) and the rebuild is
byte-identical to the committed artefact.

---

## Second pass — the eight bolded requirements (session `arena/5a8baf03-fl1`, 2026-11-14)

The brief's eight bolded items now each have a concrete, re-runnable artefact. Every number below is
regenerated by a committed script from committed inputs; nothing is typed in by hand.

| Requirement | Delivered | Verified numbers | Where |
|---|---|---|---|
| Price-snapshot store (open **and** close for every market originated) | Append-only, source-bound SQLite store + Week 10 export | 14 slate games x 4 market rows = 56 rows; **0 opening prices** (no verified opener source exists — F37); 56 closing/latest values recorded in the store with third-party provenance; blank on the site display per the no-unverified-values rule (F39) | `engine/price_snapshots.py`, `data/price_snapshots.csv`, `price-snapshots.html` |
| Verified results feed (backtests/ROI computable) | Settled markets from scores reconciled 32/32 against official standings | 137 verified games, 548 settled market rows (audit layer: 282W/262L/4P, flat-bet ROI -0.71%/unit from labelled third-party prices — recorded in the data file, withheld from site display, F39) | `engine/settlement.py`, `data/settled_markets.csv`, `results-feed.html` |
| Origination order: side, then total, then moneyline | Executable queue that raises on anything else | `ORIGINATION_ORDER = ("side","total","moneyline")`; board order asserted at build | `engine/origination.py`, `line-origination.html` |
| Fair line / market line / difference as separate columns | Origination board with the three columns and a fixed difference convention | 56 board rows; fair **blank** (model coefficients unfitted — F38); difference **blank** with it; market blank — third-party values recorded in data/line_board.csv only (F39) | `data/line_board.csv`, `line-board.html` |
| Signal separated from staking in the leaderboard | Two scores, two ranks; overall rank follows signal; masking warning where staking outranks signal | Unit-tested: a 50%-hit-rate entry with stakes piled on winners shows a better staking score yet cannot outrank a 55% signal | `engine/leaderboard.py`, `strategies.html` |
| Depth of replacement tracked, not just the fact | String of the club's own next man up, per affected slot | 112 affected players; 91 name a replacement — 48 second-string, 17 third, **11 fourth**, 13 fifth, 2 sixth; 21 publish no further name; Houston blank (F40) | `data/replacement_depth_out.csv`, `replacement-depth.html` |
| Correlations only from officially sourced numbers, n published | Register computed exclusively from official captures | CO-01 rho 0.723 (n=160), CO-02 -0.087 (n=32), CO-03 0.653 (n=32), CO-04 -0.161 (n=137); CO-05..07 **blocked, n=0, blank** | `data/correlations_official.csv`, `correlations-official.html` |
| Demotion gate: live back to paper | D1 decay / D2 calibration drift / D3 concentration, implemented and tested; promotion requires G1-G6 all PASS | Too-small windows return INSUFFICIENT_DATA, never a pass | `engine/demotion.py`, `validation.html` |

### Irregularities found and fixed in this pass

1. **A hand-edited page was being silently destroyed by the build.** The demotion-gate section had been
   added directly to `validation.html`; `tools/site.py` regenerates that file, so the section vanished on
   the next build. Found by re-running the build and diffing; fixed by porting the section into the
   generator (flag F42). The pattern is the finding: edit the generator, never the artefact.
2. **Row-level sourcing was prose, not links, on five tables.** The new `tools/checkrows.py` gate (every
   data row must carry a source link or publish nothing) initially failed 519 rows; all genuine gaps were
   fixed at the generators — including the computed layer's schedule and prop-correlation tables — and the
   gate now passes 3,724 rows on 21 pages.

### What is still blocked (all on Flagged for Review)

Opening prices (F37), fair lines (F38), anything needing an official odds source (F39), replacement depth
where clubs publish no further name (F40), the week-10 availability-vs-outcome correlation until the week
settles (F41). Four questions (Q30-Q34) and five suggestions (SG16-SG30) were added for your decision;
none of them is answered unilaterally.

---

## Final integration addendum — session `arena-a4c5a1de-fl1` (2026-11-16)

**Stale-PR takeover (coordination rule: claim >60 min stale).** Two complete, CI-green PRs whose
sessions went inactive were integrated: **#38** (`arena/08fef9e9-fl1`, the market-data spine: 9 engine
modules, 8 pages, 74 unit tests, four settlement bugs it found in its own first pass) and **#39**
(`arena/2fa09442-fl1`, the cross-check gate between the two independent replacement-depth
implementations). Nothing discarded: colliding engine paths renamed with importers repointed
(`engine/backtest_spine.py`, `engine/originate_spine.py`), colliding page outputs re-issued
(`results-feed-market.html`, `signal-vs-staking-market.html`, `replacement-depth-market.html`),
register ids re-issued per repo convention (flags F43–F52, questions Q35–Q39, suggestions SG35–SG38,
sources S70–S76) with every in-file reference retagged inside the spine's own files only.

**All 28 tracked requirements now show `done` on [Requirements](requirements.html).** The last four
partials were closed with published evidence: R11 (numeric fair | market | difference boards on
`line-board.html` and `origination.html`), R12 (fitted signals, walk-forward 13,310 published bets,
headline finding F50: the model's own signal is negative against the recorded market number on all
three markets), R16 (official-operand correlation register with n + Fisher CIs, plus the correlation
gate that publishes its refusals with reasons), R19 (71 verified replacement-depth ladders,
cross-checked by two independent implementations). Status changes cite their evidence on the
requirements page itself.

**Known-open items are unchanged and stay on [Flagged for Review](flagged.html)**: no official price
source exists (F34/F39), opening prices for 2026 are uncapturable from official channels (F43), CLV
is unmeasurable until a dated snapshot collector runs (F49, SG35), the undated-vintage vocabulary
decision (Q35), and the benchmark-policy decision (Q37). These do not block the merge; they are the
owner's decision list.

---

## Session `arena-fc0ed6e8-fl1` — decision layer (2026-11-16)

The eight remaining brief items that no prior session had built are now built and verified:

1. **Decision readiness** — the landing page now carries one row per requirement with the gate that
   blocks it and the number that would clear it (`readiness.html` holds the full register plus a
   69-row audit of every brief bullet; 28/28 requirements covered).
2. **Change of mind** — every strategy entry now carries two-sided, pre-registered
   "what would change our mind" conditions (upgrade / downgrade).
3. **Removal of luck, published** — the dashboard panel decomposes each signal run: the probability
   luck alone ran that hot, the family-wise bar (α/16 = 0.00313), the sample each strategy would need
   to certify its observed rate if real (best candidate: 4,315 bets vs 936 held), and the smallest
   edge each sample could certify at 80% power. Verdict unchanged: **no strategy clearing**; the
   every-home-team control (−5.2%, the vig) anchors the panel.
4. **Ablations instead of fixed penalties** — a real one, run on 5,657 games: identical models with
   and without QB-deficiency features, chronological splits, holdout scored once. Result: margin MAE
   −0.11 pts [−0.24, +0.02], total MAE −0.08 [−0.19, +0.03] — **both CIs include zero, so the feature
   stays OUT of every published model**. The fitted coefficients (home 2nd-string QB ≈ −3.5 pts
   [−4.6, −2.4]) are published with intervals: the estimate a fixed penalty would have guessed.
5. **Drift alarm (G-18)** — 19 datasets pinned; shrink/missing/emptied fields fail the build loudly.
6. **Reserve list captured** (25 official rows, S80) — "not listed" no longer silently means available.
7. **Announced-starter evidence** (S84/S85) — official dated announcements recorded with a strict
   verified/unverified boundary.
8. **Venue + schedule announcement** (S81–S83) — official Game Center spot-checks (2/272, both
   matching, Game Books confirmed reachable) and the league's dated May 8, 2026 schedule announcement
   published beside the live schedule page.

Parallel-session note: sessions `arena/a4c5a1de-fl1` and `arena/dbf11de0-fl1` shipped overlapping
deliverables in PRs #42–#44 (their removal-of-luck panel, backlog, availability pages, snapshot
ledger). Nothing was discarded: both builds are live and cross-linked; register IDs from this
session were renumbered (F61–F65, Q44, SG43–SG45, S80–S85) and the collisions cross-referenced.
