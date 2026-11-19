# Decision audit — session `arena/bc60d3ea-fl1` (2026-11-19)

**Scope.** Independent line-by-line audit of the project brief against repository
evidence, plus fresh official reads dated 2026-11-19. This document is a new file;
it edits no shared register. Items that need a shared-file change are logged as
requests (RQ-J1…RQ-J5 in `COORDINATION.md`) for the integration session.

**Method.** Every count below was recomputed from the committed files on
2026-11-19 (not copied from prose). Fresh official reads were taken with a
clock-bracketed window (after 2026-11-19T05:22:37Z, before 2026-11-19T05:40:00Z)
and verified by `scripts/verify_bc60d3ea.py` (checks V-J1…V-J6, all PASS;
`data/verification-bc60d3ea.tsv`). Canonical Week 10 files were not touched.

---

## 1. What was verified fresh today (2026-11-19)

| Check | Result | Detail |
|---|---|---|
| V-J1a/b | PASS | Both standings routes: 32 clubs × 17 columns; W+L+T ∈ {9,10}; NET = PF−PA; PCT exact on all 32 rows. (10-game clubs are those whose bye is Week 11 or later; the six Week 11 bye clubs all show 10 games, as required.) |
| V-J2 | PASS | League route and division route agree cell-for-cell on all 32 clubs × 17 columns. The F72 route-lag did **not** recur on this read. |
| V-J3 | PASS | Fresh standings reproduce from the 150-row dated closeout corpus (`data/results_2026-11-17-closeout.tsv`) on W/L/T/PF/PA for 32/32 clubs. The Week 10 closeout corpus is arithmetically complete. |
| V-J4 | PASS | Week 11 injury hub: 253 rows across 24 clubs (FULL 83 / LIMITED 87 / DNP 83). Game designations on 16 rows (Out 9 / Questionable 7), **only** on the Thursday game's clubs (IND, HOU). CIN and WAS print "No Injuries Reported"; the six bye clubs (ATL, CLE, GB, LA, NE, SEA) print no section. |
| V-J5 | PASS | Week 11 schedule: 13 games, 26 distinct clubs; bye list is exactly the complement; every record printed on the schedule page matches the fresh standings W/L/T. |
| V-J6 | PASS | Canonical `data/injuries.tsv`, `data/results.tsv`, `data/standings.tsv` untouched (sha256 prefixes recorded in the verification TSV). |

**New facts established by this read (all with official URLs in the raw captures):**

- The 2026-11-19 standings are the post-Week-10 state: BUF and SF 8-1 lead;
  LAC, MIA, TEN 1-8 are last. The 150-row closeout corpus reproduces them
  exactly, so the corpus — not the frozen 137-row canonical feed — is the
  arithmetically current results record. Promotion into the canonical feed
  remains Q44's owner decision; nothing here promotes it.
- Week 11's only designated game at read time is Thursday IND at HOU
  (Nov 19, 8:15 PM ET, PRIME). Notable designations: IND Will Mallory (Out),
  Bernhard Raimann (Out), Charvarius Ward (Out); HOU Marvin Harrison Jr.
  (Out), Danielle Hunter (Out), Brevin Jordan (Out), Woody Marks (Out).
- The Week 11 injury read is a **new week**, not a same-week delta. No
  designation-change claim is made against the Week 10 table from it. The
  first same-week delta for Week 11 requires a second Week 11 read (SG50,
  gated on Q42).
- Abbreviation conventions differ by source and must be mapped explicitly:
  NFL.com prints AZ/LA; the repo's results corpus and `data/teams.tsv` use
  ARI/LAR. The verifier maps AZ→ARI, LA→LAR; no fuzzy join is used anywhere.

---

## 2. Brief coverage — every bullet mapped (D-01…D-69)

The 69-row brief audit in `data/readiness.json` was re-checked line by line:
every `where` artefact named in the 69 rows exists in the repository (bare
filenames resolve under `data/`). Status summary (recomputed 2026-11-19):

- **Done (incl. done-this-repo / rejected-by-design):** D-02, D-03, D-04, D-05,
  D-16, D-17, D-22, D-24, D-26, D-27, D-35, D-37, D-39, D-40, D-41, D-42,
  D-47, D-48, D-49 (rejected), D-62, D-64 (rejected), D-66, D-68, D-69,
  plus D-01/D-19/D-21/D-28/D-29/D-38/D-46/D-53/D-54/D-60 in their
  store/method halves.
- **Partial (first verified evidence exists; named gap remains):** D-06, D-07,
  D-08, D-09, D-10, D-12, D-13, D-14, D-15, D-18, D-20, D-23, D-25, D-31,
  D-32, D-33, D-34, D-36, D-43, D-44, D-45, D-50, D-51, D-52, D-56, D-57,
  D-58, D-59, D-61, D-63, D-67.
- **Blocked (named gate, no path without an owner decision or a new source):**
  D-11, D-30, D-55, D-65.
- **Store-done / values-blocked:** D-01 (price store built; prices blocked on
  Q21/Q30).

The single most important structural fact, unchanged: **no strategy has a
performance figure because no strategy has been run, and no market price
exists in any official source.** Every ROI/difference cell that needs a price
is blank by policy, not by omission.

---

## 3. Questions, informations and answers (46 rows)

Recomputed 2026-11-19 from `data/questions.json`: 46 rows, all carrying an
`answer`, `answer_state` and `answer_date` (2026-11-17). States: **12 answered,
16 partial, 18 open.** The table below is generated from the register; the
live rendering with full answer text is `questions.html`.

| ID | State | Question | Answer (short) |
|----|-------|----------|----------------|
| Q01 | answered | What exactly is being priced — the full-game winner, the spread, the total, or a specific prop — and for whic… | Side first — the order is pre-registered: originate the side, then the total, then the moneyline (data/origination_order.json; brief audit D-03). mod… |
| Q02 | answered | Is the objective a single published line per game, or a repeatable pipeline that regenerates lines weekly? | A repeatable pipeline. Every published line is regenerated from committed inputs on each rebuild (tools/build.py -> scripts/build_fair_lines_m.py -> … |
| Q03 | partial | What is the official source for a *market* price to measure our own line against? | No official league source publishes betting prices; the board records this as GAP-01 and leaves market cells blank with the reason (model_lines.tsv m… |
| Q04 | answered | Is there an official league-wide depth chart, or must depth come from each of the 32 club sites? | No. https://www.nfl.com/depth-charts/ returns 404 (S13). Depth comes from the clubs' own published chart pages — 30 clubs plus the special-cased Chie… |
| Q05 | open | Are official snap counts published, so a starter's replacement can be measured rather than guessed? | Not established: no official snap-count file exists in this repo, which is exactly why the snap-count starter proxy is blocked (D-55, D-30). Until an… |
| Q06 | partial | How is the injury report snapped and versioned, given that it changes several times per week? | Method settled: each read is captured verbatim under raw/ with a clock-bracketed window (three dated reads: 2026-11-14, 2026-11-16, 2026-11-17), pars… |
| Q07 | partial | What do the practice and game-status designations officially mean, and can the definitions be quoted from an … | Official text supplies labels only — Out/Doubtful/Questionable and the three practice statuses map 1:1 in the capture grammar, and no official percen… |
| Q08 | answered | How should the cross-source irregularities found in this repo be handled? | Published, never suppressed: every cross-source irregularity becomes a row on flagged.html with detail, action and source links (70 flags today; F61 … |
| Q09 | partial | What sample size would make a strategy's result distinguishable from luck, and how long is one NFL season? | Answered per strategy by the removal-of-luck panels: skill means the 95% lower bound of hit rate clears the vig-adjusted break-even hurdle after a mu… |
| Q10 | answered | How is 'luck removed' defined operationally, rather than as a slogan? | Operationally: benchmark-relative skill with uncertainty — the luck-removed edge (hit-rate lower bound minus hurdle), a game-cluster lower bound, a m… |
| Q11 | answered | How are correlation values computed for parlays and prop combos, and from what joint data? | From official rows only: data/correlations_official.json computes every value from rows transcribed from official league sources (S01/S03/S52) with n… |
| Q12 | answered | What counts as out-of-sample, and how is the holdout protected from repeated peeking? | Chronologically, frozen before scoring: the ablation corpus splits train 1999-2019 / validation 2020-2021 / final holdout 2022-2025 (scored once, aft… |
| Q13 | partial | What exactly is rewarded on the leaderboard, and is anything of value actually paid out? | What is ranked: luck-adjusted skill computed from a sealed, walk-forward bet log, gates first, with rewards conditional on passing them (data/leaderb… |
| Q14 | open | Does producing lines and publishing them raise any legal issue, and does the responsible regulator need to be… | Not answerable from data or official sources: the legal/regulator question (Q14, SG11) has had no counsel input. Before any decision: the owner's jur… |
| Q15 | answered | Which Week 10 games have no injury report in the captured snapshot, and is that because the report is not yet… | None in the current captures: the canonical table holds 345 rows across all 28 clubs that played Week 10 — every one of the 14 games has both teams' … |
| Q16 | answered | How are 'not injury related' entries handled so they do not pollute an injury signal? | Carried verbatim from the league's own text and explicitly marked: the per-team availability build publishes a nonInjury count per club and its net-i… |
| Q17 | partial | Which additional inputs are officially obtainable, and which require a licensed vendor? | Obtained official inputs are enumerated: 88 registered sources, 79 VERIFIED, each with URL and capture date (data/sources.tsv). Licensed vendors are … |
| Q18 | open | How does an automated pipeline stay within acceptable use of official sites? | No terms review exists, so no defensible yes/no. Practice so far: a handful of clock-bracketed dated reads per page with verbatim capture (raw/ heade… |
| Q19 | partial | How is a strategy's edge tested against a naive baseline, so that the model gets credit only for what it actu… | Measured against vig-adjusted break-even hurdles plus a market control: betting every home team at the close runs 5,067 settled bets at -5.19% ROI — … |
| Q20 | answered | Who owns each task when several sessions run at once, and what happens on a stale claim? | Written in COORDINATION.md: read the board first; claim by pushing session id and file scope immediately; never start a claimed task; keep scopes non… |
| Q21 | open | What approved source will supply OPENING prices for every market we originate? | No approved source. The price-snapshot store exists (D-01 store done) but opening values are blocked: no opening-price source has been chosen (D-01 '… |
| Q22 | open | Where will moneyline opening and closing prices come from? | Same gap as Q21 — no approved source for moneyline open/close. The store keeps what the labelled feed provides (close, when provided) and leaves the … |
| Q23 | open | May third-party market prices back published difference and staking numbers, or must those cells stay blank? | Interim rule in force, ratification open: third-party-derived cells publish only with explicit labels/flags (market_provenance 'third-party ... flagg… |
| Q24 | partial | Are the demotion-gate thresholds (100-bet window, 25-unit drawdown, p<0.10, 300-bet re-promotion) the rules t… | Numbers exist and are frozen, but they are not the brief's sketch: data/market/demotion_config.json (2026-11-14) fixes a 200-bet window (min 60), D1 … |
| Q25 | partial | What staking plans may entries use at all, now that rank counts signal only? | Rank-side settled: staking can never affect a rank (signal/staking split, D-05), and each entry carries two-sided change-of-mind fields (D-17). The a… |
| Q26 | partial | When do we fit the fair model's coefficients out-of-sample instead of publishing the naive baseline? | Today no fitted coefficients populate published lines: output is the frozen pre-registered baseline fl1-elo-v1 (model_version column) with its calibr… |
| Q27 | partial | What verified source will confirm WHO actually replaces a starter on the field? | Route (a) stands at 30/32 clubs: per-club chart pages registered URL-per-row (data/depth-sources.tsv) plus 11 dated, quoted announced-starter rows (d… |
| Q28 | answered | Which officially sourced correlation pairs should be captured every week to grow n? | The five published pairs in data/correlations_official.json (C-A1: season point differential vs win pct, n=32, r=0.8781; plus four more), each with i… |
| Q29 | open | Which of the two parallel implementations of R21-R28 becomes canonical for each requirement? | Not decided: three sessions built overlapping readiness and luck views, all live and cross-linked (F66), with consolidation registered as SG47. The o… |
| Q30 | open | Which licensed source will supply OPENING prices, at what capture cadence, and under what redistribution term… | No source chosen: Q21/Q22 are blocked on exactly three unknowns — source name, capture cadence, redistribution terms. Classified NOT-ATTEMPTED in the… |
| Q31 | open | What acceptance criteria must a fitted fair-line model meet before its numbers populate the Origination Board… | None frozen: the repo deliberately publishes the naive pre-registered baseline instead (Q26). Criteria for admitting a fitted model (calibration boun… |
| Q32 | open | May third-party-derived values be published as sourced on the headline registers, or must every published val… | Open by default: today's enforced rule is third-party values publish only as labelled/flagged cells, never as unsourced headline numbers (tools/check… |
| Q33 | partial | What numeric thresholds do demotion rules D1-D3 use, and when are they frozen? (pairs with SG17 and SG31) | Frozen, with a divergence to ratify: demotion_config.json (2026-11-14) fixes window=200 (min 60), D1 LB-fail < 0, D2 slope band 0.4-1.6, D3 caps 0.35… |
| Q34 | partial | Should the verified results feed backfill 1999-2025 from third-party rows (labelled) so backtests have histor… | Labelled third-party history already powers the corpus: backtests span 2011-2026 by season with provenance per row (data/market/backtest_by_season.ts… |
| Q35 | open | Should the snapshot store accept a fourth phase value for prices whose vintage the publisher never stated, or… | Open — whether the store's phase enum gains a value for prices whose vintage the publisher never stated is a schema/owner decision. Interim: such row… |
| Q36 | partial | What price basis should a published ROI use when the feed carries a line but no odds? | Interim basis implemented: ROI publishes only where a posted price exists, with basis on the row (roi_basis=POSTED, price_basis=POSTED_IN_STORE in da… |
| Q37 | open | Is the 2021 single-book opening line worth a published movement table, or should it stay quarantined? | Open — it stays quarantined: a single 2021 single-book opening line cannot support a published movement table without a vintage/source policy (Q35) a… |
| Q38 | answered | For the 38 unlined 2026 games, does the board show the fair number with an empty market column, or suppress t… | Current published behaviour: show the fair number, leave the market cell blank, print the reason — model_lines.tsv carries market_status 'no official… |
| Q39 | open | Should a D4 integrity trigger block a merge, or only block promotion? | Open — D4 (price-integrity quarantine: price gap > 5% or quarantine share > 0.5%, data/market/demotion_config.json) currently gates promotion and dem… |
| Q40 | open | Which dated read of the injury report is the canonical pre-kickoff snapshot for backtests? | Open — three dated reads now exist (2026-11-14 canonical TSV, 2026-11-16, 2026-11-17) precisely because no rule says which one a backtest may pin. Th… |
| Q41 | partial | Should designations published after the earlier read be back-filled into the published table, or kept as a se… | Implemented, awaiting ratification: later designations are never back-filled into the canonical table — injuries.tsv stays pinned to its dated captur… |
| Q42 | open | May the injury report be captured at the Wednesday/Thursday/Friday cadence the brief asks for, before the ter… | Open — three clock-bracketed reads exist (11-14, 11-16, 11-17), but the Wednesday/Thursday/Friday cadence has not started because capture cadence bum… |
| Q43 | open | Should the leaderboard adopt the removal-of-luck numbers as its qualification bar? | Open — both luck panels publish exactly the numbers such a bar would use (edge lower bound vs hurdle, multiplicity-adjusted verdicts, control baselin… |
| Q44 | open | When a week's games all reach FINAL, who promotes the captured finals into the canonical verified results fee… | Open — today nobody promotes: the Week-10 close-out (13 finals plus the live Monday game) is published in data/week10_results_extension.json ['comple… |
| Q45 | open | Should the snapshot store accept a fourth phase value for prices whose vintage the publisher never stated, or… | Duplicate of Q35 (verbatim — a merge re-issue collision, recorded as F70). Treat Q35 as the live question; Q45's disposition is pending SG47's consol… |
| Q46 | partial | Should the 2026-11-17 injury-hub capture be promoted into the current table or retained only as a dated snaps… | Implemented, awaiting ratification: the 2026-11-17 capture is retained as an immutable dated snapshot (raw/ with its manifest) and published as a del… |

**What each state means.** *Answered* = settled by evidence already in
the repo. *Partial* = facts stated, named gap remains. *Open* = owner decision
or missing dataset, with the exact clearing item in the answer text.

**The 18 open questions, grouped by what clears them:**

- **Price source (Q21, Q22, Q30):** name a licensed opening/closing price
  source, its cadence and redistribution terms. Nothing else unblocks ROI,
  difference columns, or vig decomposition.
- **Third-party policy (Q23, Q32, Q34, Q35/Q45, Q36, Q37):** whether
  labelled third-party values may back headline numbers, the store's phase
  enum, the ROI basis, and the quarantined 2021 line.
- **Promotion & cadence (Q39, Q40, Q42, Q44):** D4 merge-vs-promotion,
  which dated read a backtest pins, Wed/Thu/Fri capture cadence (terms), and
  who promotes finals into the canonical feed.
- **Model admission (Q31, Q43):** acceptance criteria for a fitted
  fair-line model, and whether the removal-of-luck numbers become the
  leaderboard qualification bar.
- **Consolidation (Q29):** which parallel readiness/luck implementation
  is canonical (SG47).
- **Legal/terms (Q14, Q18):** jurisdiction, real stakes, acceptable use.
  No counsel input exists; nothing published here is legal advice.
- **Snap counts (Q05):** no official snap-count source verified;
  starter/replacement logic rests on club charts + announced-starter evidence.

## 4. Suggestions review table (52 rows)

Recomputed 2026-11-19 from `data/suggestions.json`: 52 rows (SG52 appended on 2026-11-19 by session arena/9fccbb0e-fl1, task K1; no other row changed), every row
carrying a recommendation. The live rendering with options, effort,
risk and prerequisites is `suggestions.html`. This table is the
review checklist: one line per suggestion, in register order.

| ID | Suggestion | Recommendation (short) |
|----|------------|----------------------|
| SG01 | Publish a fair value only, never a fake market price | A. A blank, labelled column is honest and costs nothing. Option C delays all work on the strength of a data source that was never… |
| SG02 | Grade every strategy on calibration first, profit second | A, with C as a display layer. Profit-first ranking will surface a lucky strategy in week one and destroy the credibility of the b… |
| SG03 | Freeze predictions before kickoff with a cryptographic seal | A. It is nearly free, and it is the single cheapest thing that makes the leaderboard credible. |
| SG04 | Split the backup-deficiency feature into 'observed absence' and 'derived depth' | A. Option C is the trap: it would look like the most impressive feature on the site while being the least defensible. |
| SG05 | Add a Flagged for Review page as a first-class section | A. It is the mechanism that lets the rest of the site be trusted. |
| SG06 | Adopt walk-forward validation with a frozen, access-logged holdout | A. Option B leaks future information into the past in a sport with strong week-to-week drift. |
| SG07 | Start with team totals, and defer parlays until legs are individually validated | A. Option B is how projects end up with a parlay board backed by three unvalidated legs. |
| SG08 | Require every strategy to beat a published naive baseline | A. Without it the leaderboard measures effort, not edge. |
| SG09 | Timestamp and never overwrite every injury snapshot | A. Option C discards the entire within-week signal, which is the only part that is not already in the closing price. |
| SG10 | Make the site a static dashboard with no build step | A. Nothing to break, nothing to version, and Pages serves it as-is. |
| SG11 | Keep the leaderboard non-monetary until a legal review exists | A. It delivers the requested competitive structure with none of the exposure. |
| SG12 | Separate 'observed' from 'derived' in every table, visibly | A. A reader should never have to guess whether a number was read or computed. |
| SG13 | Expand depth coverage one club at a time, starting with a single worked example | A. It demonstrates the method end-to-end and keeps every published cell checkable. |
| SG14 | Reconcile contradictions by publishing them, never by choosing silently | A. Any silent choice would be an unlogged inference, which is what the brief prohibits. |
| SG15 | Add a one-page decision brief for each open question | A. It is the difference between a list of worries and a set of choices. |
| SG16 | Choose a betting-price source before any market column or ROI is computed | A. Nothing should be computed against prices until the owner has chosen a source and its terms. Option C would make the ROI and t… |
| SG17 | Confirm the demotion-gate thresholds (G-14) before any strategy goes live | A. The defaults are the smallest honest windows the code supports. A drawdown number is a policy choice and should come from the … |
| SG18 | Re-read the official Week 1-9 pages game by game before any backtest is quoted | A. The backtest is only as good as its inputs, and the brief asks for line-by-line verification. |
| SG19 | Decide whether any third-party-derived correlation may ever be shown | A. The brief is explicit. Option C is the right long-term path and needs a source that has not been found yet. |
| SG20 | Record opening prices at origination from Week 11 onward | A. It starts closing GAP-01 prospectively at zero cost and cannot make anything worse. |
| SG21 | Purchase a licensed opening + closing line history | A if budget allows; B is the honest interim and is what runs now. |
| SG22 | Adopt the signal/staking split and the demotion gate as written competition rules | A. Blending re-opens the door the requirement exists to close. |
| SG23 | Capture official injury and depth snapshots weekly | A. The correlation register's n is the decision-quality bottleneck. |
| SG24 | Decide the market-price publication policy (F-18 / F-11) | A until C is affordable, then C. B if the no-price promise must hold absolutely. |
| SG25 | Unify the leaderboard wording across the two site layers (F-19) | A. Both registers are useful; the error was the word 'anywhere'. |
| SG26 | Annotate, do not rename, the Week 10 board columns (F-21) | A. Renaming breaks consumers; leaving it silently keeps misleading readers. |
| SG27 | Extend the verified results feed through the season in the weekly workflow | A. The verification is already automated; it should simply run. |
| SG28 | Fix the computed layer's break-even to use per-bet odds, then re-run its gates (F30) | A. The odds are already in the ledger; the correct number is one line away. |
| SG29 | Choose canonical implementations of R21-R28 from the two parallel builds (F31) | A. This is the decision the Suggestions page exists for: two real options, one owner, one pass. |
| SG30 | Acquire one licensed odds feed and start open/close capture (pairs with Q30 and SG16) | A if the terms allow public display; otherwise B. Option C keeps the site honest but leaves opening-line movement unmeasurable. |
| SG31 | Pre-register the demotion and promotion thresholds in one commit before any live stake (pairs with … | A. Option B manufactures thresholds from results; option C reintroduces exactly the discretion the gates exist to remove. |
| SG32 | Extend the results feed with player-level stats from an official source once one is identified (pai… | A with B as the interim. C abandons part of the brief. |
| SG33 | Schedule a weekly append-only capture of the injury report and depth charts (weekly append captures) | A. It is the cheapest way to turn a poster into a dataset. |
| SG34 | Decide the fair-line publication policy before the first fitted line ships (pairs with Q31 and flag… | A. Option C is how invented numbers enter a site that promised never to publish them. |
| SG35 | Run a dated snapshot collector before Week 12 | A. It is the single change that unblocks the promotion gate, the reward rule and the CLV claim at once. |
| SG36 | Keep the undated vintage as a first-class label everywhere | A. The label describes what we have; the other two describe what we wish we had. |
| SG37 | Publish cross-feed drift as a standing section, not a one-off | A. Option three is the failure mode this whole site was built to avoid. |
| SG38 | Tie rewards to measured line value, not to ROI | A. It is the version of the rule that cannot be satisfied by a run of coin flips. |
| SG39 | Publish a weekly 'what changed' diff instead of a static snapshot | A. The diff is the product; the table is just the latest frame. |
| SG40 | Promote the two dated captures into a scheduled, append-only ledger | A, once Q37 is answered. Until then, option B. |
| SG41 | Adopt the removal-of-luck thresholds as the leaderboard's qualification bar | A. Option C is how a lottery gets mistaken for a method. |
| SG42 | Add random-pick and favourites-only controls to every leaderboard run | A. A control costs nothing and is the cheapest lie detector available. |
| SG43 | Automate the weekly results promotion (extension register -> canonical feed) (pairs with Q35) | A. The two existing builders already compose into the promotion; the only new decision is when it runs. |
| SG44 | Run a dated snapshot collector before Week 12 | A. It is the single change that unblocks the promotion gate, the reward rule and the CLV claim at once. |
| SG45 | Keep the undated vintage as a first-class label everywhere | A. The label describes what we have; the other two describe what we wish we had. |
| SG46 | Publish cross-feed drift as a standing section, not a one-off | A. Option three is the failure mode this whole site was built to avoid. |
| SG47 | Consolidate the parallel decision-readiness and luck views into one canonical page each | A. The brief makes the owner the reviewer; consolidation is a decision, not a unilateral edit. |
| SG48 | Replace generator-only row citations with provenance-backed sources | A, with C for any row whose evidence cannot be found. Never infer a source from the value shape or neighboring rows. |
| SG49 | Keep every injury-hub read as a dated, hash-pinned immutable snapshot | Use the append-only snapshot ledger; preserve the 2026-11-14 and 2026-11-17 reads independently. |
| SG50 | Automate the dated injury-hub reads on the brief's cadence once Q42 clears | Do it immediately after Q42 clears; pin the raw captures outside the static site at the same time (SG's durable-store item, D-38). |
| SG51 | Promote finals into the verified feed under a frozen auto-rule (Q44) | Freeze the rule now, before Week 11 results arrive. |
| SG52 | Record each candidate's per-bet probability at registration so controls and candidates share one proper score | A. The probability field is required in the pre-registration template before the first candidate is registered. |

**How to review.** Approve/reject per row on `suggestions.html`.
Nothing in this section is implemented by this session; the brief
requires review before implementation, and the review has not happened.

## 5. Stale items found (logged as requests, not edited here)

These are contradictions between committed registers, found by recomputation.
Each is already logged in `COORDINATION.md` as RQ-J1…RQ-J5 for the
integration session; they are listed here so the reviewer sees them in one place.

1. **Readiness landing counts are stale** (`data/readiness.json`): R04 "42+
   flags" (now 72), R07 "34 suggestions" (now 51), R09 "34 questions" (now 46),
   R05 "28 requirements" (now 29), R22 "+13 Week 10 finals to capture (F61)"
   (now 14 captured in the closeout side-reads, P1–P8 PASS).
2. **Backlog statuses contradict the brief audit** (`data/requirements_backlog.json`
   vs `data/readiness.json` brief_audit): R87 not-started vs D-69 done;
   R37 not-started vs D-17 done; R44 not-started vs D-24 done; R83 not-started
   vs D-63 partial; R82 partial vs D-62 done; R47 not-started vs D-26/D-27
   done; R55 not-started vs D-35 done; R59 not-started vs D-39 done.
   One canonical status per requirement is needed (pairs Q29/SG47).
3. **F59/F61 actions are superseded**: F59 still names SG36 (F71 flags this);
   F61's action still says "Capture the 13 finals" — the closeout captured
   all 14. Q44's answer text still describes "13 finals plus the live Monday
   game" — superseded by the S98 closeout read (14 FINAL). Q44 stays open
   (the promotion decision), but its text needs the dated update.
4. **Q45 duplicates Q35 verbatim** (recorded as F70). Fold together under
   SG47's consolidation so the question is answered once.
5. **Two abbreviation conventions** (AZ/LA on NFL.com vs ARI/LAR in the repo
   corpus) must stay explicitly mapped. No action needed beyond the mapping
   this session's verifier already uses; flagged so future joins do not
   silently drop Arizona and the Rams.

None of these block a merge (per the brief, flagged items do not block).
None was silently fixed here, because the files are owned by other sessions
(PR #57) or are shared registers.

## 6. What would change our mind (per strategy, two-sided)

Every strategy entry in `data/strategies.json` carries a two-sided
`change_of_mind` field (upgrade / downgrade conditions), enforced by drift
pin DR-11. The standing verdicts that follow from it:

- **No strategy clears the removal-of-luck bar.** The best ROI entry
  (936 settled bets, 51.07% lower bound vs the 52.38% vig-adjusted hurdle)
  is rejected on exactly this. A strategy would need a lower bound above
  the hurdle after the multiplicity adjustment (α/16 = 0.00313) — that is
  the upgrade condition; anything less stays paper.
- **Injury features stay OUT of published models.** The ablation (5,657
  games, chronological holdout) gives margin MAE −0.11 pts [−0.24, +0.02]
  and total MAE −0.08 [−0.19, +0.03] — both intervals include zero. The
  fitted coefficients (home 2nd-string QB ≈ −3.5 pts [−4.6, −2.4]) are
  published with intervals; a fixed penalty would have guessed them.
- **Correlations publish only from official rows, with n.** Third-party
  measures stay in their own labelled registers and never enter a parlay
  without the joint-evidence gate (D-35).

## 7. Irregularities flagged for review (this session)

- **None new from the fresh reads.** Both standings routes agree; the
  closeout corpus reproduces the fresh standings 32/32; the Week 11 injury
  grammar parses cleanly; the schedule records match. The F72 route-lag
  did not recur.
- **Verifier bugs found and fixed during this session** (documented, not
  hidden): (a) games-played is 9 *or* 10 by bye timing, not always 9;
  (b) AZ/LA vs ARI/LAR aliasing; (c) schedule records omit a zero tie and
  carry parentheses. Each fix was verified by hand against the official
  pages before the script was changed. The pre-fix FAIL output is preserved
  in this session's commit history.
- **Transcription risk, stated plainly:** the 2026-11-19 raw captures were
  transcribed from page-reader chunks into the committed 6/17-column shapes
  by hand. The verifier checks internal consistency (arithmetic, route
  agreement, corpus reproduction, grammar), which catches systematic
  errors, but a single mis-typed player name would not be caught by it.
  The integration session should spot-check a sample of rows against the
  live URLs before promoting these captures into any headline register.
  Until then they are raw captures only, not published tables.

## 8. Reproduce

```bash
python3 scripts/verify_bc60d3ea.py   # V-J1..V-J6; exit 0 = all PASS
python3 -m unittest discover -s tests  # full suite (356 tests at session start)
python3 tools/checklinks.py          # internal links/anchors
python3 tools/checkrows.py           # every data row sourced
python3 tools/verify_drift.py        # 19/19 pins
python3 tools/verify_injuries.py     # 345/345 Week 10 rows vs raw capture
python3 tools/verify_results.py      # 137-game standings reconciliation
python3 tools/verify_brief.py        # 10/10 brief checks
```

No network is needed to re-run any of the above. No third-party packages.
