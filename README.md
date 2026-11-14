# FL1 — NFL Line Lab

A verified, auditable base for originating NFL lines: official injury data, a decision register,
and a strategy leaderboard that refuses to guess.

**Live site:** https://sassnarep3-star.github.io/FL1/

---

## What this is

The site is a static dashboard. It separates three things that are usually blurred together:

1. **What an official source actually says** — every value links to the live page it came from.
2. **What we do not know yet** — twenty open questions, each with the missing data named.
3. **What we propose to do about it** — fifteen suggestions with options, costs, risks and one
   recommended path, for review before anything is implemented.

Where a number could not be confirmed from an official source, the cell is left **blank** and listed
on the *Flagged for Review* page. Nothing is estimated to fill a gap.

**No line has been originated and no strategy has a result.** That is deliberate: a line needs a
fitted model *and* a benchmark price, and the second does not exist in this repository.

## Pages

| Page | Contents |
|---|---|
| `index.html` | Dashboard and headline figures |
| `executive-summary.html` | One-page brief |
| `requirements.html` | Full requirement decomposition with evidence |
| `injuries.html` | Official Week 10 2026 injury report, 345 rows |
| `depth.html` | Backup depth, observed vs derived, one club worked |
| `standings.html` | Official 2026 standings, schedule, tiebreakers |
| `line-origination.html` | How a line would be produced, and where it stops |
| `strategies.html` | Leaderboard and ranking rule |
| `validation.html` | The eight validation gates and luck controls |
| `questions.html` | Twenty open questions |
| `suggestions.html` | Fifteen suggestions with options and recommendations |
| `sources.html` | Source registry with verification status |
| `flagged.html` | Fifteen flagged items |
| `verification.html` | Every check performed, and how to re-run it |

## Repository layout

```
index.html … flagged.html     the published site (generated, committed)
assets/css/site.css           one stylesheet, no framework, no CDN
assets/js/site.js             optional filter/highlight helpers
assets/js/data.js             generated data bundle
data/*.tsv                    normalised source data, one row per fact
data/*.json                   registers (questions, suggestions, requirements, strategies, flags)
raw/                          verbatim page captures used for verification
tools/build.py                data -> assets/js/data.js, and all derived arithmetic
tools/site.py                 data -> the HTML pages
tools/checklinks.py           internal link + anchor + reachability check
tools/verify_injuries.py      line-by-line diff of the TSV against the raw capture
docs/                         markdown copies of the executive summary and methodology
COORDINATION.md               shared task board for concurrent sessions
```

## Reproduce and verify

```bash
python3 tools/build.py           # regenerate data bundle + derived counts
python3 tools/site.py            # regenerate all HTML pages
python3 tools/checklinks.py      # fail if any internal link or anchor is broken
python3 tools/verify_injuries.py # diff every injury row against the raw capture
```

`checklinks.py` and `verify_injuries.py` both exit non-zero on failure, so they can gate a merge.
No third-party Python packages are required.

## Why there is no build step

`index.html` and its siblings are committed, fully rendered HTML. GitHub Pages serves the repository
root directly, so there is no pipeline that can fail and no possibility of the live site lagging the
committed data. Re-run the tools when the data changes and commit the output.

## Method notes

- **Blanks are load-bearing.** An em dash means no official source publishes that value. A cell reading
  *not listed* means the player does not appear on the club's injury report at all — also an official fact.
  These are visually distinct on purpose.
- **Provenance is per row.** Every fact carries the ID of the source record it came from.
- **Derived arithmetic is computed, never typed.** Every count on the site comes out of `tools/build.py`.
- **Name joins use an explicit alias table** (`data/depth-aliases.tsv`), never fuzzy matching, because two
  different players named Marcus Harris appear in this dataset (flag F11).

## Where to start

See [`REVIEW.md`](REVIEW.md) for a short reading guide, the checks to run, and the judgement calls
worth disagreeing with.

## Limitations

Single season, single snapshot, no price data, no snap counts, no official league-wide depth chart.
See `flagged.html` for all fifteen items, with links.

## Not advice

Nothing here is a bet, an offer to wager, betting advice, or a statement about the legality of any
activity in any jurisdiction. No regulator or tax source was verified.

---

## Session D additions (2026-11-14)

- **`schedule.html`** — all 272 games of the 2026 regular season with results, reconciled strictly
  (32/32 clubs' records, PF and PA) against the official standings capture and the official Week 10
  schedule page; raw feed snapshot at `raw/games-nfldata.csv`.
- **`prop-correlations.html`** — empirical player-level correlations (QB↔WR r≈0.79, QB↔TE r≈0.37,
  RB rush↔receive r≈−0.07, binary lifts) computed from nflverse player_stats 1999–2024; closes
  open question **Q-PROP-01** from the computed research layer; QA-gated and reproducible.
- **`.github/workflows/refresh.yml`** — scheduled weekly refresh: re-fetches the games feed,
  rebuilds and re-verifies every session-D artefact, commits only when all checks pass.
- **Independent verification (V1–V9)** — recorded in `data/verification-d.tsv` and on the schedule
  page: record reconciliation, deterministic rebuild of the merged computed layer, 18/18 injury
  transcription fidelity, spread-sign convention (13/13 vs moneylines), bye-club completeness.

---

## Price-snapshot store (2026-11-14)

`engine/price_snapshots.py` provides an append-only SQLite store for point-in-time quotes attached to an originated model version. It records explicit `open`, `close`, or `intermediate` phase, market/side/line/odds, UTC capture time, source URL and vendor record ID; duplicate deliveries are idempotent. The store does not fetch quotes or manufacture missing values. Use only a licensed feed and preserve its terms. The repository contains no verified official NFL betting-price feed; therefore this is an implementation capability, not evidence that price history is currently populated. Run `python3 -m unittest tests.test_price_snapshots -v` for its checks.

## Session E additions (2026-11-14) — registers, engine, and a measured result

Branch `arena/c80caab4-fl1`, integrated into the published site rather than replacing it. Everything here is
additive: `data/*.json` registers already on `main` were left byte-for-byte untouched, and this session's
parallel registers live under `data/specs/`.

- **`docs/pages/`** — 18 pages generated entirely from the registers (`site/build.py`), covering requirements
  (R-01…R-40), questions (Q-01…Q-24), suggestions (S-01…S-24, all `decision: OPEN`), the line-origination
  specification, validation gates G-1…G-13, the correlation register, injury/depth modelling, the leaderboard
  design, the missing-information register (GAP-01…GAP-19), a source register with per-source verification
  levels, the repo audit, two independent captures of the official injury report, and a flagged-for-review page.
- **`engine/`** — stdlib-only implementation with 75 tests: pricing and staking, statistics (Wilson intervals,
  power analysis, bootstrap, max-T multiple-testing control, deflated Sharpe), joint parlay pricing with
  Frechet-bounded correlation, injury capture reconciliation, a fail-closed compliance gate for the league's
  prohibited wager classes, the gate evaluator, and sealed-entry leaderboard scoring that ranks on the 95%
  lower bound of per-unit return.
- **`data/measured.json` + `docs/pages/measured.html`** — the brief's correlation ask, actually computed:
  over-the-total versus home-covering has rho **+0.00696** (95% CI [-0.03324, +0.04831], n=6,813) in the
  in-repo third-party dataset, i.e. marginal dependence indistinguishable from zero. The cost is not
  correlation, it is price: that pair's joint hit rate is 24.35% against a 26.42% break-even implied by its own
  legs. The peer-reviewed home-underdog hypothesis, run through the same gates, fails (45.8% over 1,302 bets,
  ROI -11.6%). The register's `rho` cell stays blank pending one decision: whether third-party-derived values
  may be published as sourced (flag **F-11**).
- **Two findings worth reading before trusting any table here.** (1) The official injury report renders a
  different number of rows per fetch: two captures an hour apart agree on every shared player but differ by 44
  rows, four of them confirmed `Out` designations — so ingestion reconciles renders instead of trusting one.
  (2) A plausibility check caught a contested sign convention in the third-party spread column; it was settled
  by a sibling session's moneyline cross-check (`data/verification-d.tsv` V8), and the wrong reading is
  published alongside the right one as the audit trail.
- **Reproduce:** `python3 -m unittest discover -s tests -q` · `python3 engine/demo_run.py --check` ·
  `python3 -m engine.measure` · `python3 site/build.py && python3 site/verify.py`.

---

## Session arena/685f958d-fl1 additions (2026-11-14) — origination, price store, results feed, signal vs staking, demotion

- **`model-lines.html`** — own fair lines for the 13 pending Week 10 games, in the order side → total → moneyline.
  Fair, market and difference are separate columns. Every market and difference cell is blank: no official NFL
  source publishes prices (F18). Source: `data/model_lines.tsv`, `engine/originate.py`.
- **`data/price_snapshots.tsv`** — the opening/closing store, one row per game and market (39 rows), all blank.
- **`results-feed.html`** — the 137 final 2026 results used as inputs, and a strictly out-of-sample walk-forward
  backtest (weeks 4–10, n = 89). The side model's sign accuracy is above 50%, but its margin and total errors do
  not beat a constant benchmark (F20). ROI is blank (no prices).
- **`governance.html`** — signal ranks the leaderboard, staking is reported beside it (`engine/leaderboard.py`
  `split_scores`); the G-14 demotion gate sends a live strategy back to paper (`engine/gates.py`
  `demotion_decision`); correlation values are withheld, with n shown (F19).
- **Verification** — `tools/verify_brief.py` writes `data/verification-brief.tsv` (10 checks, incl. the 13-game slate
  against `raw/nfl-week10-2026-capture.md`, and a fresh re-run of every fair value). `tests/test_brief.py` holds 17
  hand-checkable tests.
- **Withheld on purpose (brief B6):** market columns on `schedule.html`; coefficients on `prop-correlations.html`
  (n kept); a withdrawal banner on the sub-site `docs/pages/measured.html`.
- **Rebuild:** `python3 tools/brief.py && python3 tools/site.py && python3 tools/checklinks.py && python3 tools/verify_brief.py`.
  `scripts/build_pages_d.py` regenerates `schedule.html` and `prop-correlations.html`.
## Session M additions (2026-11-14)

- **`results-feed.html`** — the verified results feed: all 137 played 2026 games, finals verified
  row-by-row against official nfl.com week pages (`raw/official-finals-2026.tsv`, sources
  S49–S67) and cross-checked three ways (`scripts/verify_feed_m.py`, 137/137 PASS).
  `engine/results_settlement.py` settles side/total/ML and computes ROI **fail-closed** on price
  provenance (17 unit tests); the verified-ingestion boundary is `engine/results_feed.py`.
- **`originations.html`** — origination in the mandated order (**side → total → moneyline**), and
  for all 272 markets of 2026 the three separate columns: model fair line | market line |
  difference. Fair-line engine proved identical to the Computed Research Layer's engine
  (5,336/5,336 Elo values) and reproduces its published calibration. Fair TOTAL deliberately
  blank (S2 unfitted, flag F33).
- **`signal-vs-staking.html`** — leaderboard split: signal (flat-stake) ranks and rewards;
  staking is risk telemetry only. Three entries found where a positive staking run would mask a
  non-positive signal (MASKED flag). Also the **demotion gate G-16** (live → paper: signal decay,
  risk breach or compliance breach; automatic; staking can never promote but can demote) and
  G-17 (signal-only promotion rule).
- **`replacement-depth.html`** — the depth of the replacement, not just the fact: 69 Week-10
  spots, each replacement's string and cascade count; 6 spots with no listed replacement left
  (blank + flagged).
- **`official-correlations.html`** — correlations computed **only** from officially sourced
  numbers, each published **with its n** (C-O1 r=+0.076 n=137; C-O2/C-O3 |r|<0.09 n=242).
- **`data/governance_gates.json`** — G-16/G-17 register; **`data/origination_order.json`** —
  the order register; **`scripts/fetch_prop_mirror_m.py`** — pinned-blob fetch (sha-verified)
  that restores session D's V9 input in a fresh workspace.
- Sources S50–S67 (official week pages) and flags F32–F36 added to the registries.

## Session F additions (2026-11-14) — the eight requirement items

Branch `arena/5a8baf03-fl1`. This pass implements the brief's eight bolded requirements as tested
code plus generated tables, and adds the row-level source audit. New engine modules are standard
library only, per the dependency policy above:

- `engine/origination.py` — the mandated origination order (side, total, moneyline) as an executable
  queue, and fair/market/difference as three separate columns with the difference convention fixed
  before any result.
- `engine/settlement.py` — push-aware settlement of side/total/moneyline from verified scores and
  per-unit PnL at American prices; missing prices are reported, never imputed.
- `engine/demotion.py` — the live-to-paper demotion gate (D1 decay, D2 calibration drift, D3
  concentration) plus the paper-to-live promotion check. INSUFFICIENT_DATA is a first-class outcome.
- `engine/leaderboard.py` (extended) — signal score and staking score computed separately; overall
  rank follows the signal, so a lucky staking run cannot mask a bad signal (unit-tested).
- `tools/build_{results_feed,snapshots,line_board,replacement_depth,correlations_official}.py` —
  deterministic builders for `data/settled_markets.csv` (548 settled rows), `data/price_snapshots.csv`
  (56 rows, opens blank — F37), `data/line_board.csv` (56 rows, fair blank — F38),
  `data/replacement_depth_out.csv` (112 affected players; 4th-string-or-deeper replacements: 26),
  `data/correlations_official.csv` (4 measured values with n; 3 blocked rows kept blank).
- `tools/checkrows.py` — the row-level verification gate: every data row on every page either carries
  a source link or publishes nothing (3,724 rows audited).
- Registers: flags F37-F42, questions Q30-Q34, suggestions SG16-SG30. Five new site pages:
  `results-feed.html`, `price-snapshots.html`, `line-board.html`, `replacement-depth.html`,
  `correlations-official.html`.

All checks green at hand-off: 95 unit tests, `tools/{build,site,checklinks,checkrows,verify_injuries,
verify_results}.py`, `engine/demo_run.py --check`, `python3 -m engine.measure`,
`scripts/verify_site.py` (0 errors), `scripts/verify_d.py` (V5-V9 PASS), `site/build.py` +
`site/verify.py`. See `COORDINATION.md` for the full sources/verification/irregularities record.

=======
---

## Session arena/685f958d-fl1 additions (2026-11-14) — origination, price store, results feed, signal vs staking, demotion

- **`model-lines.html`** — own fair lines for the 13 pending Week 10 games, in the order side → total → moneyline.
  Fair, market and difference are separate columns. Every market and difference cell is blank: no official NFL
  source publishes prices (F37). Source: `data/model_lines.tsv`, `engine/originate.py`.
- **`data/price_snapshots.tsv`** — the opening/closing store, one row per game and market (39 rows), all blank.
- **`results-feed.html`** — the 137 final 2026 results used as inputs, and a strictly out-of-sample walk-forward
  backtest (weeks 4–10, n = 89). The side model's sign accuracy is above 50%, but its margin and total errors do
  not beat a constant benchmark (F39). ROI is blank (no prices).
- **`governance.html`** — signal ranks the leaderboard, staking is reported beside it (`engine/leaderboard.py`
  `split_scores`); the G-14 demotion gate sends a live strategy back to paper (`engine/gates.py`
  `demotion_decision`); correlation values are withheld, with n shown (F38).
- **Verification** — `tools/verify_brief.py` writes `data/verification-brief.tsv` (10 checks, incl. the 13-game slate
  against `raw/nfl-week10-2026-capture.md`, and a fresh re-run of every fair value). `tests/test_brief.py` holds 17
  hand-checkable tests.
- **Withheld on purpose (brief B6):** market columns on `schedule.html`; coefficients on `prop-correlations.html`
  (n kept); a withdrawal banner on the sub-site `docs/pages/measured.html`.
- **Rebuild:** `python3 tools/brief.py && python3 tools/site.py && python3 tools/checklinks.py && python3 tools/verify_brief.py`.
  `scripts/build_pages_d.py` regenerates `schedule.html` and `prop-correlations.html`.
>>>>>>> origin/main

**Merge note (same day):** sessions `arena-685f958d-fl1` and `arena-5876146b-fl1` independently built
parallel second-pass deliverables and both landed on `main` first. The integration keeps main's canonical
site pages and data stores (verified results feed with row-level official game links, fair lines with
model coefficients, replacement depth with alias rules, registers to F36/Q29/SG29) and keeps this
session's audit layer alongside: `tools/checkrows.py` (every table row sourced or blank — now 29 pages,
4,654 rows), `engine/settlement.py` + `tools/build_results_feed.py` + `data/settled_markets.csv` (market
settlement audit), `engine/origination.py`, `engine/paper_gate.py` (D1–D3 + promotion check),
`tools/build_{snapshots,line_board,correlations_official,replacement_depth}.py` and the audit CSVs they
regenerate. This session's register entries are numbered F37–F42 / Q30–Q34 / SG30–SG34 with
cross-references to the overlapping entries from the other sessions. Full log in `COORDINATION.md`.

