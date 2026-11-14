# FL1 — Executive Summary

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

## Second pass — the eight bolded requirements (session `arena/5a8baf03-fl1`, 2026-11-14)

The brief's eight bolded items now each have a concrete, re-runnable artefact. Every number below is
regenerated by a committed script from committed inputs; nothing is typed in by hand.

| Requirement | Delivered | Verified numbers | Where |
|---|---|---|---|
| Price-snapshot store (open **and** close for every market originated) | Append-only, source-bound SQLite store + Week 10 export | 14 slate games x 4 market rows = 56 rows; **0 opening prices** (no verified opener source exists — F23); 56 closing/latest values recorded in the store with third-party provenance; blank on the site display per the no-unverified-values rule (F25) | `engine/price_snapshots.py`, `data/price_snapshots.csv`, `price-snapshots.html` |
| Verified results feed (backtests/ROI computable) | Settled markets from scores reconciled 32/32 against official standings | 137 verified games, 548 settled market rows (audit layer: 282W/262L/4P, flat-bet ROI -0.71%/unit from labelled third-party prices — recorded in the data file, withheld from site display, F25) | `engine/settlement.py`, `data/results_feed.csv`, `results-feed.html` |
| Origination order: side, then total, then moneyline | Executable queue that raises on anything else | `ORIGINATION_ORDER = ("side","total","moneyline")`; board order asserted at build | `engine/origination.py`, `line-origination.html` |
| Fair line / market line / difference as separate columns | Origination board with the three columns and a fixed difference convention | 56 board rows; fair **blank** (model coefficients unfitted — F24); difference **blank** with it; market blank — third-party values recorded in data/line_board.csv only (F25) | `data/line_board.csv`, `line-board.html` |
| Signal separated from staking in the leaderboard | Two scores, two ranks; overall rank follows signal; masking warning where staking outranks signal | Unit-tested: a 50%-hit-rate entry with stakes piled on winners shows a better staking score yet cannot outrank a 55% signal | `engine/leaderboard.py`, `strategies.html` |
| Depth of replacement tracked, not just the fact | String of the club's own next man up, per affected slot | 112 affected players; 91 name a replacement — 48 second-string, 17 third, **11 fourth**, 13 fifth, 2 sixth; 21 publish no further name; Houston blank (F26) | `data/replacement_depth.csv`, `replacement-depth.html` |
| Correlations only from officially sourced numbers, n published | Register computed exclusively from official captures | CO-01 rho 0.723 (n=160), CO-02 -0.087 (n=32), CO-03 0.653 (n=32), CO-04 -0.161 (n=137); CO-05..07 **blocked, n=0, blank** | `data/correlations_official.csv`, `correlations-official.html` |
| Demotion gate: live back to paper | D1 decay / D2 calibration drift / D3 concentration, implemented and tested; promotion requires G1-G6 all PASS | Too-small windows return INSUFFICIENT_DATA, never a pass | `engine/demotion.py`, `validation.html` |

### Irregularities found and fixed in this pass

1. **A hand-edited page was being silently destroyed by the build.** The demotion-gate section had been
   added directly to `validation.html`; `tools/site.py` regenerates that file, so the section vanished on
   the next build. Found by re-running the build and diffing; fixed by porting the section into the
   generator (flag F28). The pattern is the finding: edit the generator, never the artefact.
2. **Row-level sourcing was prose, not links, on five tables.** The new `tools/checkrows.py` gate (every
   data row must carry a source link or publish nothing) initially failed 519 rows; all genuine gaps were
   fixed at the generators — including the computed layer's schedule and prop-correlation tables — and the
   gate now passes 3,724 rows on 21 pages.

### What is still blocked (all on Flagged for Review)

Opening prices (F23), fair lines (F24), anything needing an official odds source (F25), replacement depth
where clubs publish no further name (F26), the week-10 availability-vs-outcome correlation until the week
settles (F27). Four questions (Q21-Q25) and five suggestions (SG16-SG20) were added for your decision;
none of them is answered unilaterally.
