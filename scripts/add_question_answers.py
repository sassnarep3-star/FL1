#!/usr/bin/env python3
"""Add the answer layer to data/questions.json (session arena/7ac4e12e-fl1, H4).

The brief demands "a clear list of questions, information and answers...
based upon the information that we already have and do not have". Every one of
the 45 register rows gains three fields:

  answer_state  answered | partial | open
      answered — settled by evidence already captured in this repo;
      partial  — the factual half is settled (and stated), a named gap remains;
      open     — an owner decision or a missing dataset dominates; the row says
                 exactly which and what would clear it.
  answer        the answer itself, citing register ids (D-*, F*, Q*, SG*, S*)
                and committed files. No new facts are introduced here: every
                number in these answers was checked against the file or the
                official source it names.
  answer_date   "2026-11-17".

Also appends (once) the register rows that this pass discovered:
  F70  Q45 duplicates Q35 verbatim (merge re-issue artefact).
  SG50 automate the dated injury-hub reads once Q42 clears.
  SG51 promote finals into the verified feed under a frozen auto-rule (Q44).

Idempotent: re-running leaves already-applied fields and register rows alone.

Run:  python3 scripts/add_question_answers.py
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QPATH = os.path.join(ROOT, "data", "questions.json")
FPATH = os.path.join(ROOT, "data", "flags.json")
SPATH = os.path.join(ROOT, "data", "suggestions.json")

DATE = "2026-11-17"

ANSWERS = {
    "Q01": ("answered",
            "Side first — the order is pre-registered: originate the side, then the "
            "total, then the moneyline (data/origination_order.json; brief audit D-03). "
            "model_lines.tsv prints the step order on every row ('1 side > 2 total > "
            "3 moneyline') and publishes fair, market and difference as separate "
            "columns per market (D-04). The side is the anchor quantity: both other "
            "markets are downstream of the same scoring decomposition."),
    "Q02": ("answered",
            "A repeatable pipeline. Every published line is regenerated from committed "
            "inputs on each rebuild (tools/build.py -> scripts/build_fair_lines_m.py -> "
            "data/model_lines.tsv and data/fair_lines.csv), and every row carries its "
            "model version and market provenance. One fair line per game per market at "
            "a time is the pipeline's scheduled output — not a hand-entry."),
    "Q03": ("partial",
            "No official league source publishes betting prices; the board records this "
            "as GAP-01 and leaves market cells blank with the reason (model_lines.tsv "
            "market_status; F18). Market values that do appear come from a third-party "
            "feed and are labelled per row (market_provenance in data/fair_lines.csv). "
            "The open half is approval of a market-price source for headline numbers "
            "(Q21, Q30, Q32; D-20)."),
    "Q04": ("answered",
            "No. https://www.nfl.com/depth-charts/ returns 404 (S13). Depth comes from "
            "the clubs' own published chart pages — 30 clubs plus the special-cased "
            "Chiefs capture are registered URL-per-club in data/depth-sources.tsv — and "
            "every derived rank is labelled derived, never official (D-42; club-chart "
            "caveat F10)."),
    "Q05": ("open",
            "Not established: no official snap-count file exists in this repo, which is "
            "exactly why the snap-count starter proxy is blocked (D-55, D-30). Until an "
            "official snap source covering all 32 clubs is verified (or club-chart "
            "coverage reaches 32/32 from 30/32 today), starter/replacement logic rests "
            "only on club charts and dated announced-starter evidence."),
    "Q06": ("partial",
            "Method settled: each read is captured verbatim under raw/ with a "
            "clock-bracketed window (three dated reads: 2026-11-14, 2026-11-16, "
            "2026-11-17), parsed by one shared grammar, its header row-claim asserted "
            "against the parser, and published as a delta — latest diff plus the earlier "
            "one under history in data/injury_hub_delta.json (D-21). Still open: which "
            "dated read a backtest may pin (Q40) and durable hash-pinned storage (D-28)."),
    "Q07": ("partial",
            "Official text supplies labels only — Out/Doubtful/Questionable and the "
            "three practice statuses map 1:1 in the capture grammar, and no official "
            "percentages exist. The empirical meaning (play rate per designation with "
            "confidence intervals, joined to official inactives over several seasons) "
            "has not been measured (D-43, D-52), so no outside percentage may be quoted "
            "as fact. Clears when a multi-season join of official designations to "
            "official inactives yields play rates with confidence intervals."),
    "Q08": ("answered",
            "Published, never suppressed: every cross-source irregularity becomes a row "
            "on flagged.html with detail, action and source links (70 flags today; F61 "
            "was corrected 2026-11-17 after re-reading the official pages; F53 records "
            "the row-count discrepancy). Per the brief, flagged items do not block a "
            "merge, and a cell that cannot be confirmed from an official source stays "
            "blank and flagged rather than filled (tools/checkrows.py rules 1-4)."),
    "Q09": ("partial",
            "Answered per strategy by the removal-of-luck panels: skill means the 95% "
            "lower bound of hit rate clears the vig-adjusted break-even hurdle after a "
            "multiplicity adjustment for every trial run (the register's best ROI entry "
            "is rejected on exactly this: 936 settled bets, 51.07% lower bound vs 52.38% "
            "hurdle — data/luck_panel_signal.json). The open half: which number becomes "
            "the leaderboard's standing qualification bar (Q43)."),
    "Q10": ("answered",
            "Operationally: benchmark-relative skill with uncertainty — the luck-removed "
            "edge (hit-rate lower bound minus hurdle), a game-cluster lower bound, a "
            "multiplicity adjustment, and control baselines, with PROVEN/NOT PROVEN "
            "verdicts published on removal-of-luck.html from data/luck_panel_signal.json "
            "and data/luck_panel.json. Win rate and ROI may be displayed but can never "
            "set a rank (D-37; season-long ROI ranking rejected, D-64)."),
    "Q11": ("answered",
            "From official rows only: data/correlations_official.json computes every "
            "value from rows transcribed from official league sources (S01/S03/S52) with "
            "n published per value (e.g. C-A1: n=32, r=0.8781), and engine/corr_official.py "
            "refuses non-official source ids — third-party measures stay in their own "
            "labelled registers (R27, D-07). A pair becomes usable for parlays/combos "
            "only through the joint-evidence gate (D-35)."),
    "Q12": ("answered",
            "Chronologically, frozen before scoring: the ablation corpus splits train "
            "1999-2019 / validation 2020-2021 / final holdout 2022-2025 (scored once, "
            "after freezing) with 2026 excluded as in-progress (data/ablations.json "
            "design.splits; D-69). Pre-registration (D-66, D-68) fixes rule text, sample "
            "window and gates in git before the evaluation window opens; a scored holdout "
            "is never reopened."),
    "Q13": ("partial",
            "What is ranked: luck-adjusted skill computed from a sealed, walk-forward "
            "bet log, gates first, with rewards conditional on passing them "
            "(data/leaderboard.json design; D-37). What is rewarded in value: nothing "
            "today — no payout, bankroll or currency mechanism exists anywhere in the "
            "repo (cf. economics OQ-02), so the reward design remains an owner decision."),
    "Q14": ("open",
            "Not answerable from data or official sources: the legal/regulator question "
            "(Q14, SG11) has had no counsel input. Before any decision: the owner's "
            "jurisdiction and whether any stake is real (OQ-02). Nothing published here "
            "is legal advice or evidence of compliance."),
    "Q15": ("answered",
            "None in the current captures: the canonical table holds 345 rows across "
            "all 28 clubs that played Week 10 — every one of the 14 games has both "
            "teams' rows (data/injuries.tsv, S01) — and each of the three dated hub "
            "reads prints a section for each of the 14 games. The gaps behind this "
            "question belonged to the stale 254-row pages, replaced by the re-capture "
            "(D-48; F53 keeps the count discrepancy on record)."),
    "Q16": ("answered",
            "Carried verbatim from the league's own text and explicitly marked: the "
            "per-team availability build publishes a nonInjury count per club and its "
            "net-injury rule excludes rows the league marks 'Not injury related' "
            "(scripts/build_availability_g.py, netInjuryRule). They never enter the "
            "injury count silently."),
    "Q17": ("partial",
            "Obtained official inputs are enumerated: 83 registered sources, 75 "
            "VERIFIED, each with URL and capture date (data/sources.tsv). Licensed "
            "vendors are not among them — money/contract items sit in the missing-data "
            "register as NOT-ATTEMPTED. Which to license (opening prices above all: "
            "Q21/Q30) is an owner decision."),
    "Q18": ("open",
            "No terms review exists, so no defensible yes/no. Practice so far: a handful "
            "of clock-bracketed dated reads per page with verbatim capture (raw/ headers), "
            "not continuous scraping. Before any cadence is automated (D-53) the owner "
            "must accept an acceptable-use position or name counsel to check (pairs Q14, "
            "OQ-02)."),
    "Q19": ("partial",
            "Measured against vig-adjusted break-even hurdles plus a market control: "
            "betting every home team at the close runs 5,067 settled bets at -5.19% ROI "
            "— pure house margin (data/luck_panel_signal.json control_baseline). The "
            "random-picks and favourites-only controls the brief names are not yet in "
            "every run (D-56) — the open half is the owner's adoption of those two "
            "controls into every leaderboard run; the addition itself is mechanical."),
    "Q20": ("answered",
            "Written in COORDINATION.md: read the board first; claim by pushing session "
            "id and file scope immediately; never start a claimed task; keep scopes "
            "non-overlapping on session branches; small frequent commits with "
            "pull --rebase; log cross-scope requests instead of editing; a claim idle "
            "over 60 minutes with no commits is open for takeover with a logged handoff; "
            "'done' requires sources, verification and irregularities recorded. This "
            "session pushed its claim before any other work."),
    "Q21": ("open",
            "No approved source. The price-snapshot store exists (D-01 store done) but "
            "opening values are blocked: no opening-price source has been chosen "
            "(D-01 'blocked (values)'; Q30), and the one captured opening line (2021 "
            "single-book) stays quarantined (Q37). Clearing: a named source, cadence and "
            "redistribution terms recorded in the register."),
    "Q22": ("open",
            "Same gap as Q21 — no approved source for moneyline open/close. The store "
            "keeps what the labelled feed provides (close, when provided) and leaves the "
            "rest blank; blocked on the Q30 decision (source, cadence, redistribution)."),
    "Q23": ("open",
            "Interim rule in force, ratification open: third-party-derived cells publish "
            "only with explicit labels/flags (market_provenance 'third-party ... "
            "flagged'; THIRD_PARTY badges on the boards). Promoting them to headline "
            "difference/staking numbers is the reserved owner call (Q32; D-20)."),
    "Q24": ("partial",
            "Numbers exist and are frozen, but they are not the brief's sketch: "
            "data/market/demotion_config.json (2026-11-14) fixes a 200-bet window (min "
            "60), D1 lower-bound fail < 0, D2 slope band 0.4-1.6, D3 caps 0.35/0.30/0.35, "
            "D4 price gap <= 5%, <= 2 demotions per season, reprobe >= 150 paper bets; "
            "G-16 demotes live -> paper automatically. Ratifying these instead of the "
            "100-bet / 25-unit / p<0.10 sketch is the open half (Q33, SG17)."),
    "Q25": ("partial",
            "Rank-side settled: staking can never affect a rank (signal/staking split, "
            "D-05), and each entry carries two-sided change-of-mind fields (D-17). The "
            "allowed plan list is not: Kelly-style sizing waits on bankroll, unit and "
            "jurisdiction (OQ-02), so paper entries run flat units by convention until "
            "the owner sets rules."),
    "Q26": ("partial",
            "Today no fitted coefficients populate published lines: output is the frozen "
            "pre-registered baseline fl1-elo-v1 (model_version column) with its "
            "calibration report (n=5,336 games; mean signed error -0.77 pts, MAE 2.89 "
            "pts vs close). Fitting starts only after acceptance criteria are frozen "
            "(Q31, open) and the switch itself is pre-registered (D-66, D-68)."),
    "Q27": ("partial",
            "Route (a) stands at 30/32 clubs: per-club chart pages registered URL-per-row "
            "(data/depth-sources.tsv) plus 11 dated, quoted announced-starter rows "
            "(data/announced_starters.csv) on a point-in-time ledger. Route (b), snap "
            "counts, is blocked — no official source (D-30, D-55). The gate (one "
            "verified route for all 32 clubs) is not cleared, so the backup-deficiency "
            "feature stays behind it (D-51)."),
    "Q28": ("answered",
            "The five published pairs in data/correlations_official.json (C-A1: season "
            "point differential vs win pct, n=32, r=0.8781; plus four more), each with "
            "its n, computed only from official rows (S01/S03/S52) by "
            "engine/corr_official.py; non-official rows are excluded by rule. The weekly "
            "capture cadence grows n on this same register."),
    "Q29": ("open",
            "Not decided: three sessions built overlapping readiness and luck views, all "
            "live and cross-linked (F66), with consolidation registered as SG47. The "
            "owner picks one readiness page and one luck panel (SG47 names "
            "recommendations), then the unused builders are retired."),
    "Q30": ("open",
            "No source chosen: Q21/Q22 are blocked on exactly three unknowns — source "
            "name, capture cadence, redistribution terms. Classified NOT-ATTEMPTED in "
            "the missing-data register (needs a decision or money)."),
    "Q31": ("open",
            "None frozen: the repo deliberately publishes the naive pre-registered "
            "baseline instead (Q26). Criteria for admitting a fitted model (calibration "
            "bounds, holdout behaviour, drift limits) must be written and committed "
            "before any fit is evaluated — owner/quant decision still to be made."),
    "Q32": ("open",
            "Open by default: today's enforced rule is third-party values publish only "
            "as labelled/flagged cells, never as unsourced headline numbers "
            "(tools/checkrows.py; market_provenance). Making them first-class is the "
            "decision the brief reserves (pairs Q23; D-20)."),
    "Q33": ("partial",
            "Frozen, with a divergence to ratify: demotion_config.json (2026-11-14) "
            "fixes window=200 (min 60), D1 LB-fail < 0, D2 slope band 0.4-1.6, D3 caps "
            "0.35/0.30/0.35, D4 price gap <= 5%, <= 2 demotions/season, reprobe >= 150 "
            "paper bets; G-16 defines live -> paper. The brief's sketch (100-bet window, "
            "25-unit drawdown, p<0.10, 300-bet re-promotion) was not adopted verbatim — "
            "confirming the implemented numbers is the open half (pairs SG17)."),
    "Q34": ("partial",
            "Labelled third-party history already powers the corpus: backtests span "
            "2011-2026 by season with provenance per row (data/market/backtest_by_season.tsv; "
            "13,310 graded trades), while the canonical feed stays official-only for 2026 "
            "(data/results.tsv). Extending the labelled backfill back to 1999 is the "
            "open policy half (owner; D-20)."),
    "Q35": ("open",
            "Open — whether the store's phase enum gains a value for prices whose "
            "vintage the publisher never stated is a schema/owner decision. Interim: "
            "such rows are labelled CLOSE_OR_UNDOCUMENTED in the backtest bench and the "
            "2021 opening line stays quarantined (Q37). NOTE: Q45 duplicates this "
            "question verbatim (merge re-issue) — see F70; folding them together belongs "
            "to SG47."),
    "Q36": ("partial",
            "Interim basis implemented: ROI publishes only where a posted price exists, "
            "with basis on the row (roi_basis=POSTED, price_basis=POSTED_IN_STORE in "
            "data/market/backtest_trades.tsv) and the benchmark labelled "
            "CLOSE_OR_UNDOCUMENTED; ROI is report-only and never ranks (D-64). The final "
            "headline basis waits on the price-source decisions (Q21, Q30)."),
    "Q37": ("open",
            "Open — it stays quarantined: a single 2021 single-book opening line cannot "
            "support a published movement table without a vintage/source policy (Q35) "
            "and an owner call on single-observation tables."),
    "Q38": ("answered",
            "Current published behaviour: show the fair number, leave the market cell "
            "blank, print the reason — model_lines.tsv carries market_status 'no official "
            "NFL source publishes betting prices (GAP-01); market cell left blank, see "
            "Flagged F18' on every unlined 2026 game. Nothing is inferred into the "
            "blank; ratifying this behaviour as the standing rule is a formality."),
    "Q39": ("open",
            "Open — D4 (price-integrity quarantine: price gap > 5% or quarantine share "
            "> 0.5%, data/market/demotion_config.json) currently gates promotion and "
            "demotion decisions inside the market spine. Whether a D4 breach should also "
            "hard-fail CI and block a merge (like the sourcing rules in checkrows) or "
            "only block promotion is undecided."),
    "Q40": ("open",
            "Open — three dated reads now exist (2026-11-14 canonical TSV, 2026-11-16, "
            "2026-11-17) precisely because no rule says which one a backtest may pin. "
            "The canonical injuries.tsv stays on read 1 while later reads publish as "
            "deltas. Choosing first-pre-kickoff vs latest-before-kickoff is an owner "
            "decision that sets backtest reproducibility."),
    "Q41": ("partial",
            "Implemented, awaiting ratification: later designations are never back-filled "
            "into the canonical table — injuries.tsv stays pinned to its dated capture "
            "and every subsequent change ships as a delta row with old/new values "
            "(data/injury_hub_delta.json, which also keeps the earlier delta under "
            "history). Ratify that, or switch to back-filling the latest read before "
            "kickoff — owner's call."),
    "Q42": ("open",
            "Open — three clock-bracketed reads exist (11-14, 11-16, 11-17), but the "
            "Wednesday/Thursday/Friday cadence has not started because capture cadence "
            "bumps into the terms question first (D-53; acceptable use Q18). Clearing: "
            "owner/counsel OK, then a scheduled workflow extends the repo's existing "
            "weekly refresh (SG50)."),
    "Q43": ("open",
            "Open — both luck panels publish exactly the numbers such a bar would use "
            "(edge lower bound vs hurdle, multiplicity-adjusted verdicts, control "
            "baselines). Adopting them as the leaderboard's standing qualification rule "
            "is an owner choice; if adopted, write it into the leaderboard register as a "
            "frozen gate (D-66, D-68)."),
    "Q44": ("open",
            "Open — today nobody promotes: the Week-10 close-out (13 finals plus the "
            "live Monday game) is published in data/week10_results_extension.json "
            "['completion'] with checks C1-C5 while data/results.tsv stays untouched "
            "pending this policy (F61, SG37/SG45 lineage). A workable rule to ratify: "
            "auto-promote only when a fresh official read prints every game FINAL and "
            "all V-checks pass — then it can run inside the weekly refresh (SG51)."),
    "Q45": ("open",
            "Duplicate of Q35 (verbatim — a merge re-issue collision, recorded as F70). "
            "Treat Q35 as the live question; Q45's disposition is pending SG47's "
            "consolidation so the two are answered once, not twice."),
    "Q46": ("partial",
            "Implemented, awaiting ratification: the 2026-11-17 capture is retained as an "
            "immutable dated snapshot (raw/ with its manifest) and published as a delta "
            "against the committed table — data/injuries.tsv is never rewritten in place "
            "(F69; the same never-back-fill rule as Q41, published through "
            "data/injury_hub_delta.json). The open half is the formal canonical-table "
            "policy — latest-state versus frozen-history — which is the same owner "
            "decision as Q40/Q41; SG51's append-only snapshot ledger is the recommended "
            "shape."),
}

NEW_FLAG = {
    "id": "F70",
    "kind": "Register duplication (merge re-issue artefact)",
    "item": "Q45 duplicates Q35 verbatim — the same open question is registered twice",
    "detail": "data/questions.json carries Q35 and Q45 with identical question text "
              "(both ask whether the snapshot store should accept a fourth phase value "
              "for prices whose vintage the publisher never stated). The duplication "
              "was created when a session re-issued its own Q35 at a merge where "
              "origin/main already held a Q35 — the re-issue landed as Q45 without "
              "noticing the content collision. Both rows are answered identically in "
              "the 2026-11-17 answer layer and cross-reference this flag; they must be "
              "folded into one during the SG47 consolidation so future answers cannot "
              "drift apart.",
    "sourceIds": [],
    "severity": "Low",
    "action": "Fold Q45 into Q35 during SG47 consolidation; until then treat Q35 as "
              "canonical (the answer layer marks both and cross-links here).",
}

NEW_SUGGESTIONS = [
    {
        "id": "SG50",
        "title": "Automate the dated injury-hub reads on the brief's cadence once Q42 clears",
        "category": "Data capture",
        "problem": "The brief asks for Wednesday/Thursday/Friday (daily-to-kickoff) "
                   "injury-report history, but reads have been hand-timed (2026-11-14, "
                   "11-16, 11-17 — S01/S80/S89). Cadence is the difference between a "
                   "series and three snapshots, and it is blocked only by the terms "
                   "question (Q42, Q18).",
        "proposal": "The moment Q42 clears, extend .github/workflows/refresh.yml with a "
                    "Wed/Thu/Fri (and game-day morning) job that fetches "
                    "https://www.nfl.com/injuries/, writes a clock-bracketed raw capture, "
                    "runs scripts/assemble-style seam checks, appends a sources.tsv row, "
                    "and rebuilds data/injury_hub_delta.json as read N vs read N-1. The "
                    "drift alarm (G-18) already fails loudly if row grammar changes.",
        "options": "A) cadence job in refresh.yml (recommended — same CI, same checks). "
                   "B) separate workflow with its own schedule. C) keep hand-timed reads "
                   "indefinitely (rejects the brief's requirement).",
        "impact": "Converts D-53/D-21 from partial to done and gives Questionable->Out "
                  "movement (and practice-designation trends DNP->LP->FP) a real series "
                  "to calibrate against (D-43, D-52).",
        "prerequisites": "Q42 owner/counsel clearance; no new data dependency.",
        "effort": "Small — the builders and grammar already exist; only scheduling is new.",
        "risk": "Terms exposure identical to the hand reads already taken, just more "
                "frequent — hence the prerequisite.",
        "reversibility": "High — delete the workflow step and history stays captured.",
        "recommendation": "Do it immediately after Q42 clears; pin the raw captures "
                          "outside the static site at the same time (SG's durable-store "
                          "item, D-38).",
        "evidence": "Three dated reads with asserted row counts and published deltas "
                    "(data/injury_hub_delta.json); clock windows recorded in every raw "
                    "capture header.",
    },
    {
        "id": "SG51",
        "title": "Promote finals into the verified feed under a frozen auto-rule (Q44)",
        "category": "Governance",
        "problem": "Week 10 now has 13 official finals (plus one live game) held only in "
                   "the extension register (data/week10_results_extension.json "
                   "['completion'], checks C1-C5) because nobody is authorised to move "
                   "them into canonical data/results.tsv — the promotion decision is "
                   "open (Q44) and F61 keeps flagging the staleness.",
        "proposal": "Ratify this rule text and commit it before the next full slate: "
                    "a refresh run may append a result row to data/results.tsv only if "
                    "(1) a fresh official schedule read prints that game FINAL with a "
                    "score, (2) the row's fixture exists in data/schedule.tsv, (3) the "
                    "record/point recomputation still reproduces the official standings "
                    "32/32 (the V3/V4/C3 checks), and (4) the game centre URL is stored "
                    "on the row. Partial scores are never rows. The rule's commit hash "
                    "is its registration (D-68 pattern).",
        "options": "A) frozen auto-rule as above (recommended). B) human approval per "
                   "week (violates 'no manual input'). C) leave the feed on weekly "
                   "snapshots forever (F61 never clears).",
        "impact": "Clears Q44, F61 and the stale-feed half of D-02's freshness; keeps "
                  "ROI/backtests on official, check-passing inputs.",
        "prerequisites": "Owner signs the rule text (Q44) — no new data source needed.",
        "effort": "Small — the checks already run inside scripts/build_week10_extension.py "
                  "and tools/verify_results.py.",
        "risk": "Low: every promoted row re-passes the same arithmetic that caught today's "
                "discrepancies; failures abort loudly.",
        "reversibility": "High — rows append with dates; a bad promotion is a revert.",
        "recommendation": "Freeze the rule now, before Week 11 results arrive.",
        "evidence": "C1-C5 all green on the 2026-11-17 close-out read (13 finals, "
                    "standings 32/32 W/L/T + PF/PA); F61/Q44/SG37 record the gap.",
    },
]


def main():
    with open(QPATH, encoding="utf-8") as fh:
        questions = json.load(fh)
    if isinstance(questions, dict):
        questions = questions.get("questions") or questions.get("rows")

    ids = {q["id"] for q in questions}
    missing = sorted(set(ANSWERS) - ids)
    extra = sorted(ids - set(ANSWERS))
    if missing or extra:
        raise SystemExit("FAIL: answer map does not match register (%s / %s)"
                         % (missing, extra))

    applied = 0
    for q in questions:
        state, text = ANSWERS[q["id"]]
        if q.get("answer_state") == state and q.get("answer") == text:
            continue
        if q.get("answer_state") and q.get("answer_state") != state:
            raise SystemExit("FAIL: %s already answered as %r, map says %r — refusing "
                             "to overwrite" % (q["id"], q["answer_state"], state))
        q["answer_state"] = state
        q["answer"] = text
        q["answer_date"] = DATE
        applied += 1

    from collections import Counter
    counts = Counter(q["answer_state"] for q in questions)
    if sum(counts.values()) != 46:
        raise SystemExit("FAIL: expected 46 answered rows, got %d" % sum(counts.values()))
    if set(counts) - {"answered", "partial", "open"}:
        raise SystemExit("FAIL: unexpected states %r" % set(counts))

    with open(QPATH, "w", encoding="utf-8") as fh:
        json.dump(questions, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    # ---- F70 (append once)
    with open(FPATH, encoding="utf-8") as fh:
        flags = json.load(fh)
    if isinstance(flags, dict):
        flags = flags.get("flags") or flags.get("rows")
    if not any(f["id"] == "F70" for f in flags):
        if any(f["id"] == NEW_FLAG["id"] for f in flags):
            raise SystemExit("FAIL: F70 already used by a different row")
        flags.append(NEW_FLAG)
        with open(FPATH, "w", encoding="utf-8") as fh:
            json.dump(flags, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("F70 appended")

    # ---- SG50/SG51 (append once)
    with open(SPATH, encoding="utf-8") as fh:
        suggs = json.load(fh)
    if isinstance(suggs, dict):
        suggs = suggs.get("suggestions") or suggs.get("rows")
    existing = {x["id"] for x in suggs}
    for s in NEW_SUGGESTIONS:
        if s["id"] in existing:
            continue
        suggs.append(s)
        existing.add(s["id"])
        print("%s appended" % s["id"])
    with open(SPATH, "w", encoding="utf-8") as fh:
        json.dump(suggs, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print("answers applied to %d rows; states: answered=%d partial=%d open=%d"
          % (applied, counts["answered"], counts["partial"], counts["open"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
