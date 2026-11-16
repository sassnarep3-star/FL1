# FL1 — Executive Summary

**Session:** `arena-dbf11de0-fl1` · **Branch:** `arena/dbf11de0-fl1` (from `ebf20eb` of `main`) · **Built:** 2026-11-16
**Site:** https://sassnarep3-star.github.io/FL1/

> **Reading note.** This file carries more than one session's summary. The block immediately
> below is the current one (2026-11-16). Earlier blocks are preserved verbatim further down
> because they record work that is still in the repository; where they conflict with a later
> re-verification, the later one is marked as superseding.

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
