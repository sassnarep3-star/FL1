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

## Session F additions (2026-11-14) — the eight requirement items

Branch `arena/5a8baf03-fl1`. This pass implements the brief's eight bolded requirements as tested
code plus generated tables, and adds the row-level source audit. New engine modules are standard
library only, per the dependency policy above:

- `engine/origination.py` — the mandated origination order (side, total, moneyline) as an executable
  queue, and fair/market/difference as three separate columns with the difference convention fixed
  before any result.
- `engine/results_feed.py` — push-aware settlement of side/total/moneyline from verified scores and
  per-unit PnL at American prices; missing prices are reported, never imputed.
- `engine/demotion.py` — the live-to-paper demotion gate (D1 decay, D2 calibration drift, D3
  concentration) plus the paper-to-live promotion check. INSUFFICIENT_DATA is a first-class outcome.
- `engine/leaderboard.py` (extended) — signal score and staking score computed separately; overall
  rank follows the signal, so a lucky staking run cannot mask a bad signal (unit-tested).
- `tools/build_{results_feed,snapshots,line_board,replacement_depth,correlations_official}.py` —
  deterministic builders for `data/results_feed.csv` (548 settled rows), `data/price_snapshots.csv`
  (56 rows, opens blank — F18), `data/line_board.csv` (56 rows, fair blank — F19),
  `data/replacement_depth.csv` (112 affected players; 4th-string-or-deeper replacements: 26),
  `data/correlations_official.csv` (4 measured values with n; 3 blocked rows kept blank).
- `tools/checkrows.py` — the row-level verification gate: every data row on every page either carries
  a source link or publishes nothing (3,724 rows audited).
- Registers: flags F18-F23, questions Q21-Q25, suggestions SG16-SG20. Five new site pages:
  `results-feed.html`, `price-snapshots.html`, `line-board.html`, `replacement-depth.html`,
  `correlations-official.html`.

All checks green at hand-off: 95 unit tests, `tools/{build,site,checklinks,checkrows,verify_injuries,
verify_results}.py`, `engine/demo_run.py --check`, `python3 -m engine.measure`,
`scripts/verify_site.py` (0 errors), `scripts/verify_d.py` (V5-V9 PASS), `site/build.py` +
`site/verify.py`. See `COORDINATION.md` for the full sources/verification/irregularities record.

