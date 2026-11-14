#!/usr/bin/env python3
"""Append R21-R28 requirement rows, Q21-Q28 questions, SG20-SG27 suggestions,
F23-F29 flags, source S52, and gate G-14 (requirements sprint, session
arena-360ca650-fl1). Run once; idempotent via id checks."""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def save(name, obj):
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def add_rows(path, rows, key="id"):
    d = load(path)
    existing = {r[key] for r in d}
    added = [r for r in rows if r[key] not in existing]
    d.extend(added)
    save(path, d)
    print("%s: +%d rows (%d total)" % (path, len(added), len(d)))


REQS = [
 {"id": "R21", "section": "Requirements sprint (2026-11-14)",
  "requirement": "Add a price-snapshot store that records opening and closing numbers for every market we originate",
  "status": "done",
  "evidence": "engine/snapshots.py + data/price_snapshots.json: 56 rows (14 games x SIDE/TOTAL/2x MONEYLINE) in mandated order. Closing spread/total sourced from the pinned capture (28/56 cells); every opening cell blank+flagged because no source exists; store validation (price requires provenance+source; OFFICIAL pricing claim rejected) enforced in tests.",
  "page": "price-snapshots.html"},
 {"id": "R22", "section": "Requirements sprint (2026-11-14)",
  "requirement": "Add a verified results feed so backtests and ROI can be computed at all",
  "status": "done",
  "evidence": "data/results_feed.json: 137 official rows (S52); recomputing all 32 clubs' W/L/T + PF/PA from the feed reproduces data/standings.tsv exactly (checked in the build). engine/backtest.py settles bets only against this feed and reports ROI with a provenance tier.",
  "page": "results-feed.html"},
 {"id": "R23", "section": "Requirements sprint (2026-11-14)",
  "requirement": "Originate the side first, then the total, then the moneyline",
  "status": "done",
  "evidence": "Order fixed in engine/fairline.py origination_order(), enforced in the snapshot-store sort and the line-board build; the earlier 'totals-first' design note is superseded and preserved in flag F27.",
  "page": "line-board.html"},
 {"id": "R24", "section": "Requirements sprint (2026-11-14)",
  "requirement": "Publish the model's fair line, the market line, and the difference as separate columns",
  "status": "done",
  "evidence": "data/line_board.json: 42 rows with model_fair_line / market_line / difference as separate columns. Fair computed from official standings+results (HFA -0.022 pts n=137, margin sd 13.225 n=137, published); market from the pinned capture (flag F23); difference = fair - market, blank when either side blank (never zero).",
  "page": "line-board.html"},
 {"id": "R25", "section": "Requirements sprint (2026-11-14)",
  "requirement": "Separate 'signal' from 'staking' in the leaderboard so a lucky staking run cannot mask a bad signal",
  "status": "done",
  "evidence": "engine/backtest.py split_signal_staking(): signal block is flat-stake only (hit rate vs break-even, Wilson CI, z/p); staking block carries ROI at actual stakes, profit, drawdown. Rank is computed from the signal block only; data/leaderboard_signal_staking.json applies the split to the 16 computed-layer strategies and re-ranks them on signal.",
  "page": "strategies.html"},
 {"id": "R26", "section": "Requirements sprint (2026-11-14)",
  "requirement": "Track the depth of the replacement, not just the fact of a replacement",
  "status": "done",
  "evidence": "data/replacement_depth.tsv: 52 affected slots; each row names the missing strings and the NEXT AVAILABLE player's string number (the depth of the replacement), plus contingent depth where the starter is healthy but deeper strings are out. Sources: club depth charts + official injury report S01; no snap-count claims.",
  "page": "replacement-depth.html"},
 {"id": "R27", "section": "Requirements sprint (2026-11-14)",
  "requirement": "Compute correlations only from officially sourced numbers and publish n with each value",
  "status": "done",
  "evidence": "data/correlations_official.json: 5 rows, every value computed from official captures (S01/S03/S52) and every value publishes n + Fisher-z 95% CI. engine/corr_official.py raises unless every source id is in the official set. Third-party correlation registers (measured.json, prop-correlations-d.csv, correlations.csv) explicitly excluded and listed as excluded.",
  "page": "correlation-register.html"},
 {"id": "R28", "section": "Requirements sprint (2026-11-14)",
  "requirement": "Define a demotion gate that sends a live strategy back to paper",
  "status": "done",
  "evidence": "engine/demotion.py: D1 signal decay (window hit rate below break-even, p<0.10), D2 drawdown (25 flat-stake units), D3 CLV rot; any one demotes LIVE->PAPER. Re-promotion needs 300 fresh settled bets passing the G-2b standard. Registered as G-14 in data/validation_gates.json; thresholds are proposed rules (flag F28).",
  "page": "validation.html"},
]

QUESTIONS = [
 {"id": "Q21", "category": "Prices", "priority": "High",
  "question": "What approved source will supply OPENING prices for every market we originate?",
  "why_it_matters": "The price-snapshot store records the open field, but every open cell is blank: without a source there is no honest number, and without the number closing-line value cannot be computed from the open.",
  "what_we_know": "The store (data/price_snapshots.json) has the fields and the discipline. Closing prices come from the pinned nflverse capture (S47). No official league source prices NFL markets (F23).",
  "what_we_dont_know": "Whether a licensed line-history feed will be purchased or approved.",
  "missing_data": "Licensed opening + closing line history (GAP-01).",
  "source": "data/price_snapshots.json; flags F23/F25",
  "blocking": "Yes",
  "recommended_path": "Option A (SG21): buy licensed history. Interim (SG20): snapshot the market's open at the moment we publish our own line, prospectively from Week 11."},
 {"id": "Q22", "category": "Prices", "priority": "High",
  "question": "Where will moneyline opening and closing prices come from?",
  "why_it_matters": "Requirement R21 says every market we originate, and the moneyline is one of the three mandated markets. Its price cells are all blank today.",
  "what_we_know": "closing_lines.csv holds third-party moneyline prices for 2006-2025 only; the Week 10 2026 board captures spread and total but no moneyline.",
  "what_we_dont_know": "Any approved 2026 moneyline capture source.",
  "missing_data": "2026 moneyline prices (open and close).",
  "source": "data/price_snapshots.json; data/raw/MANIFEST.json",
  "blocking": "Yes",
  "recommended_path": "Extend the capture pipeline to record moneyline odds alongside spread/total, or approve a feed that carries them."},
 {"id": "Q23", "category": "Policy", "priority": "High",
  "question": "May third-party market prices back published difference and staking numbers, or must those cells stay blank?",
  "why_it_matters": "Requirement R24 demands a market-line column and a difference column; the standing verification rule says values without an official source are left blank. Both cannot hold unless the owner picks a policy. This is the open F-11 decision, now unavoidable.",
  "what_we_know": "The computed research layer already publishes third-party-derived values with labels; the root site's footer promised no price figures without official support, amended in this sprint to describe the THIRD_PARTY badge.",
  "what_we_dont_know": "The owner's preference among the three options below.",
  "missing_data": "None - this is a decision, not a data gap.",
  "source": "flags F23/F11; data/line_board.json",
  "blocking": "Yes",
  "recommended_path": "A: publish with THIRD_PARTY badge + flag until C is affordable; B switches every market cell to blank with one edit; C needs Q21's purchase."},
 {"id": "Q24", "category": "Competition rules", "priority": "Medium",
  "question": "Are the demotion-gate thresholds (100-bet window, 25-unit drawdown, p<0.10, 300-bet re-promotion) the rules to adopt?",
  "why_it_matters": "The gate defines when a live strategy goes back to paper. Wrong thresholds either strand dead strategies live or kill recovering ones.",
  "what_we_know": "Defaults are published as constructor arguments in engine/demotion.py and rendered verbatim as G-14.",
  "what_we_dont_know": "The owner's risk appetite for false demotions vs slow demotions.",
  "missing_data": "None - a rule choice.",
  "source": "engine/demotion.py; flag F28",
  "blocking": "No",
  "recommended_path": "Adopt as written for the first season (SG22) and revisit after 300 settled bets of live history."},
 {"id": "Q25", "category": "Competition rules", "priority": "Medium",
  "question": "What staking plans may entries use at all, now that rank counts signal only?",
  "why_it_matters": "Rewards must not pay on staking luck (R25), but staking still determines real-world results and drawdowns. The allowed plans need to be fixed before entries open.",
  "what_we_know": "The leaderboard reports a staking block separately; the engine computes both from one log.",
  "what_we_dont_know": "Whether flat-only, capped fractional Kelly, or author-defined stakes will be permitted.",
  "missing_data": "None - a rule choice.",
  "source": "engine/backtest.py; data/leaderboard_signal_staking.json",
  "blocking": "No",
  "recommended_path": "Flat 1 unit for the scored sample; optional separate staking report capped at 2 units (matches the exposure cap in GateConfig)."},
 {"id": "Q26", "category": "Model", "priority": "Medium",
  "question": "When do we fit the fair model's coefficients out-of-sample instead of publishing the naive baseline?",
  "why_it_matters": "The naive baseline (strength = (PF-PA)/G, /2 convention) is deliberately crude. Publishing a fitted model too early invites overfitting; too late leaves edge on the table.",
  "what_we_know": "models.json attaches the estimator (maximise out-of-sample log-loss, never tune PnL). Coefficients today are computed from 137 official 2026 games (F29).",
  "what_we_dont_know": "When enough official seasons will be captured to fit and validate honestly.",
  "missing_data": "Multi-season official results feed (today: 2026 weeks 1-10 only).",
  "source": "data/line_board.json; data/models.json",
  "blocking": "No",
  "recommended_path": "Keep the baseline published; schedule the first refit after two full official seasons are captured."},
 {"id": "Q27", "category": "Injuries and depth", "priority": "Medium",
  "question": "What verified source will confirm WHO actually replaces a starter on the field?",
  "why_it_matters": "Replacement depth today is chart-based: the club's own depth chart says who is next. Snap counts would confirm who actually took the snaps.",
  "what_we_know": "Club depth charts are self-published and labelled unofficial (S07/S08/S16-S46); the official report says who is Out. data/replacement_depth.tsv joins the two without asserting playing time.",
  "what_we_dont_know": "Any verified snap-count feed.",
  "missing_data": "Snap counts per game (GAP-05 family).",
  "source": "data/replacement_depth.tsv",
  "blocking": "No",
  "recommended_path": "Add a snap-count source once one is verified; until then label every replacement as chart-based."},
 {"id": "Q28", "category": "Correlations", "priority": "Low",
  "question": "Which officially sourced correlation pairs should be captured every week to grow n?",
  "why_it_matters": "The official correlation register publishes n with every value, and several decision-relevant pairs (e.g. availability vs margin, C-A4) sit at n=1 because only one week of injury captures exists.",
  "what_we_know": "Five pairs computed (C-A1..C-A5) from standings, results and the Week 10 report; every value carries n and a CI.",
  "what_we_dont_know": "Which pairs the owner cares about most.",
  "missing_data": "Weekly official injury + results captures (grows C-A4's n).",
  "source": "data/correlations_official.json",
  "blocking": "No",
  "recommended_path": "Pre-register the pairs now (SG23), capture weekly, publish n as it grows."},
]

SUGGESTIONS = [
 {"id": "SG20", "title": "Record opening prices at origination from Week 11 onward",
  "category": "Prices",
  "problem": "Every open cell in the price-snapshot store is blank because no historical opening-price source exists, and nothing is being recorded prospectively either.",
  "proposal": "The moment we publish our own line for a market, snapshot the market's opening number into the store (the fields and the validation already exist). Over time this manufactures the missing history at zero cost.",
  "evidence": "data/price_snapshots.json coverage: 0/56 open cells filled.",
  "effort": "Low", "risk": "Low", "reversibility": "Fully reversible",
  "prerequisites": ["A captured market number at publication time (today: the pinned S47 feed)"],
  "options": ["Snapshot at publication. (Recommended)", "Buy history later only.", "Drop the open field."],
  "recommendation": "A. It starts closing GAP-01 prospectively at zero cost and cannot make anything worse.",
  "impact": "Opening cells fill from Week 11; open-to-close movement becomes measurable."},
 {"id": "SG21", "title": "Purchase a licensed opening + closing line history",
  "category": "Prices",
  "problem": "Closing-line value (gate G-3), honest difference columns and historical backtests all need prices with clean provenance. Today's prices are third-party and flagged.",
  "proposal": "Buy or license a historical line feed covering the seasons we backtest, with open and close per market. This is the single purchase that unblocks the most gates.",
  "evidence": "G-3 is BLOCKED in engine/gates.py for want of prices; flag F23; question Q21.",
  "effort": "Medium (cost unknown)", "risk": "Low", "reversibility": "Reversible (stop renewing)",
  "prerequisites": ["Budget approval"],
  "options": ["Buy licensed history. (Recommended)", "Continue third-party capture with badges.", "Blank all price cells."],
  "recommendation": "A if budget allows; B is the honest interim and is what runs now.",
  "impact": "G-3 becomes evaluable; difference columns stop carrying the third-party badge; backtests gain a defensible price basis."},
 {"id": "SG22", "title": "Adopt the signal/staking split and the demotion gate as written competition rules",
  "category": "Competition",
  "problem": "Without the split, a lucky staking run ranks above good signal; without demotion, a live badge outlives the edge that earned it.",
  "proposal": "Rank on the signal block only (engine/backtest.py), report staking separately, and demote live strategies to paper on any of D1/D2/D3 (engine/demotion.py, gate G-14).",
  "evidence": "data/leaderboard_signal_staking.json re-ranks the 16 computed-layer strategies on signal; flag F28 publishes the thresholds.",
  "effort": "Low", "risk": "Low", "reversibility": "Rules can be amended between seasons",
  "prerequisites": ["Q24/Q25 rule decisions"],
  "options": ["Adopt with published thresholds. (Recommended)", "Adopt with different thresholds.", "Rank on a blended signal+staking score."],
  "recommendation": "A. Blending re-opens the door the requirement exists to close.",
  "impact": "Lucky staking cannot mask bad signal; decaying strategies return to paper automatically."},
 {"id": "SG23", "title": "Capture official injury and depth snapshots weekly",
  "category": "Data",
  "problem": "One week of injury captures exists. Correlation C-A4 (availability vs margin) is stuck at n=1, and replacement depth only reflects Week 10.",
  "proposal": "Extend the weekly refresh workflow to capture the official injury report and club depth charts each week of the season, appending to the verified feed.",
  "evidence": "data/correlations_official.json C-A4 row (n=1, blank); .github/workflows/refresh.yml already runs weekly.",
  "effort": "Medium", "risk": "Low", "reversibility": "Fully reversible",
  "prerequisites": ["Stable capture tooling (exists)"],
  "options": ["Automate weekly capture. (Recommended)", "Manual capture", "Only at season milestones."],
  "recommendation": "A. The correlation register's n is the decision-quality bottleneck.",
  "impact": "C-A4 becomes computable; replacement depth tracks the whole season."},
 {"id": "SG24", "title": "Decide the market-price publication policy (F-18 / F-11)",
  "category": "Policy",
  "problem": "The brief both demands the market-line column and forbids unconfirmed values. The sprint resolved it provisionally with a THIRD_PARTY badge; the owner should ratify or overrule.",
  "proposal": "Pick one of three policies and record it: (A) publish third-party prices with badge + flag [current], (B) strict blank on every market cell, (C) licensed feed then publish as sourced.",
  "evidence": "flags F23/F11; question Q23; amended footer describing the badge.",
  "effort": "Low", "risk": "Low", "reversibility": "One edit per policy switch",
  "prerequisites": [],
  "options": ["A: badge + flag. (Recommended interim)", "B: strict blank.", "C: licensed feed."],
  "recommendation": "A until C is affordable, then C. B if the no-price promise must hold absolutely.",
  "impact": "Sets what the line board, snapshots and leaderboard are allowed to display."},
 {"id": "SG25", "title": "Unify the leaderboard wording across the two site layers (F-19)",
  "category": "Documentation",
  "problem": "The root Leaderboard page said no backtest existed anywhere in the repository while the computed layer publishes 16 backtested strategies over third-party data.",
  "proposal": "Point the root page at the computed layer explicitly: plan-level strategies (official data only) and computed-layer backtests (third-party, flagged) are two different registers and should say so.",
  "evidence": "flag F24; strategies.html; docs/pages/leaderboard.html.",
  "effort": "Low", "risk": "Low", "reversibility": "Fully reversible",
  "prerequisites": [],
  "options": ["Point root page at computed layer. (Recommended)", "Remove computed backtests.", "Keep both as-is."],
  "recommendation": "A. Both registers are useful; the error was the word 'anywhere'.",
  "impact": "A reader stops being told two contradictory things."},
 {"id": "SG26", "title": "Annotate, do not rename, the Week 10 board columns (F-21)",
  "category": "Data",
  "problem": "week10_signal_board.csv's 'closing_spread_home' column actually holds the AWAY team's spread (V8-verified), and 'market_implied_home_winprob' derives from an unvalidated formula.",
  "proposal": "Add a convention note and derived home-view column; leave original column names in place so existing consumers do not break. Exclude the implied-probability column from decision pages.",
  "evidence": "check V8 (data/verification-d.tsv); flag F26; the line board already negates per row and says so.",
  "effort": "Low", "risk": "Low", "reversibility": "Fully reversible",
  "prerequisites": [],
  "options": ["Annotate + derived column. (Recommended)", "Rename columns.", "Leave untouched."],
  "recommendation": "A. Renaming breaks consumers; leaving it silently keeps misleading readers.",
  "impact": "Nobody reads the away spread as the home spread again."},
 {"id": "SG27", "title": "Extend the verified results feed through the season in the weekly workflow",
  "category": "Operations",
  "problem": "The feed holds weeks 1-10. Backtests and ROI recompute as results land; nothing appends them automatically.",
  "proposal": "Wire scripts/build_results_feed.py and the standings cross-check into .github/workflows/refresh.yml so the feed extends weekly and fails loudly if the standings check breaks.",
  "evidence": "data/results_feed.json (137 rows); the build already proves 32/32 standings agreement.",
  "effort": "Low", "risk": "Low", "reversibility": "Fully reversible",
  "prerequisites": ["Weekly official results capture (SG23 shares the plumbing)"],
  "options": ["Wire into refresh.yml. (Recommended)", "Manual weekly build", "Snapshot only."],
  "recommendation": "A. The verification is already automated; it should simply run.",
  "impact": "ROI and backtests stay current all season with the same provenance bar."},
 {"id": "SG28", "title": "Fix the computed layer's break-even to use per-bet odds, then re-run its gates (F30)",
  "category": "Data",
  "problem": "The computed-layer leaderboard's breakeven_hit is 1/(1+realized ROI), a circular quantity, so its G4 'beats_vig' gate is unusable and every strategy is failed by construction.",
  "proposal": "In scripts/strategy_lab.py, compute the hurdle from the odds already in the bet ledger (mean of 1/decimal odds across settled bets, or per-bet break-even), regenerate leaderboard.csv, and re-run the gate columns. A one-line change to avg_dec semantics plus a rebuild.",
  "evidence": "flag F30; data/leaderboard_signal_staking.json transcribes the wrong value with a warning rather than silently fixing another session's dataset.",
  "effort": "Low", "risk": "Medium (changes computed-layer verdicts)", "reversibility": "Reversible (git history holds the old build)",
  "prerequisites": ["Owner acceptance that computed-layer verdicts may flip"],
  "options": ["Fix + rebuild + re-verify. (Recommended)", "Leave and read G4 as unusable.", "Drop G4 from the computed layer."],
  "recommendation": "A. The odds are already in the ledger; the correct number is one line away.",
  "impact": "The computed leaderboard's gate columns become meaningful; the signal split can then rank against true price hurdles."},
]

FLAGS = [
 {"id": "F23", "kind": "Data provenance",
  "item": "Market prices are third-party only - no official league source prices NFL lines",
  "detail": "Requirement R24 mandates publishing the market-line and difference columns; the standing verification rule says leave unconfirmed values blank. Provisional resolution applied in this sprint: market cells are transcribed from the sha256-pinned nflverse capture (S47) and badged THIRD_PARTY; difference cells inherit the badge. The strict-blank alternative is one edit away and is left open as question Q23 (the old F-11 decision, now unavoidable).",
  "source": "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
  "severity": "Medium", "sourceIds": ["S47"],
  "action": "Review Q23 / SG24. Option B switches every market cell to blank."},
 {"id": "F24", "kind": "Documentation inconsistency",
  "item": "Root Leaderboard page claimed no backtest existed anywhere in the repository while the computed layer publishes 16 backtested strategies",
  "detail": "strategies.html carried the sentence 'No backtest has been executed and no performance figure is claimed anywhere in this repository', but data/leaderboard.csv and docs/pages/ carry 16 strategies backtested over third-party data (2006-2026). The two registers answer different questions (official-data plan vs third-party research), but 'anywhere' was false. The sprint section on the Leaderboard page now states the split; the original sentence is preserved there as the plan-level register's statement about official data.",
  "source": "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
  "severity": "Low", "sourceIds": ["S47"],
  "action": "SG25: unify wording across the two layers."},
 {"id": "F25", "kind": "Missing capture",
  "item": "Moneyline opening and closing prices are not captured for the Week 10 slate",
  "detail": "The price-snapshot store holds MONEYLINE-HOME and MONEYLINE-AWAY rows for all 14 games with every price cell blank: the Week 10 board captures spread and total only, and closing_lines.csv carries moneyline prices only for 2006-2025 (third-party). Nothing was inferred to fill them.",
  "source": "https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv",
  "severity": "Medium", "sourceIds": ["S47"],
  "action": "Q22: approve a moneyline capture source."},
 {"id": "F26", "kind": "Data convention",
  "item": "week10_signal_board.csv 'closing_spread_home' holds the AWAY team's spread, and 'market_implied_home_winprob' comes from an unvalidated formula",
  "detail": "Check V8 (data/verification-d.tsv) verified across 13/13 games that nflverse spread_line is the away team's point spread, so the board's column name is wrong for its content. market_implied_home_winprob = logistic(0.28 * spread_line) has no cited basis and behaves like a probability of the away side's margin, not a home win probability; it is excluded from the line board and the price store. The line board negates the verbatim value into home view and says so per row; the store keeps the verbatim number as the AWAY quote.",
  "source": "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
  "severity": "Medium", "sourceIds": ["S47"],
  "action": "SG26: annotate columns and add a derived home-view column; do not rename."},
 {"id": "F27", "kind": "Design change",
  "item": "Origination order mandated: side first, then total, then moneyline - supersedes the earlier totals-first note",
  "detail": "data/models.json described the architecture as 'deliberately totals-first'. Requirement R23 fixes the order SIDE, then TOTAL, then MONEYLINE. The pipeline, the snapshot store and the line board now follow the mandated order. The old wording is preserved in this flag so the change is visible rather than silent.",
  "source": "https://www.nfl.com/schedules/2026/by-week/week-10",
  "severity": "Low", "sourceIds": [],
  "action": "None - recorded so the change is auditable."},
 {"id": "F28", "kind": "Proposed rule",
  "item": "Demotion-gate thresholds are proposed competition rules, not measured facts",
  "detail": "G-14 (engine/demotion.py) uses D1 window=100 settled bets with inferiority alpha 0.10, D2 max drawdown 25 flat-stake units, D3 trailing CLV rot, and re-promotion after 300 fresh settled bets at the G-2b standard. These are constructor arguments chosen as a design decision; a reviewer may change them. What cannot be changed by review is the verdict logic: DEMOTE cannot be reinterpreted as HOLD.",
  "source": "https://www.nfl.com/",
  "severity": "Low", "sourceIds": [],
  "action": "Q24: confirm or revise the thresholds."},
 {"id": "F29", "kind": "Model provenance",
  "item": "Fair-line coefficients are computed from the 2026 official feeds only (137 games)",
  "detail": "Home-field advantage -0.022 points per game and margin sd 13.225 points are computed by engine/fairline.py from data/results.tsv (S52) as of 2026-11-14; the strength convention (PF-PA)/G with a /2 meeting rule is a published bookkeeping choice, not a fitted coefficient. No coefficient is tuned on market prices. The 2026 home-field estimate being ~0 is a property of this season's 137 games, not a claim about the NFL.",
  "source": "https://www.nfl.com/standings/",
  "severity": "Low", "sourceIds": ["S52", "S03"],
  "action": "Q26: schedule out-of-sample refits after two official seasons."},
 {"id": "F30", "kind": "Data methodology",
  "item": "Computed-layer leaderboard's breakeven_hit is circular: 1/(1+realized ROI), not the price hurdle",
  "detail": "scripts/strategy_lab.py computes avg_dec as the mean of (realized profit/stake + 1) over settled bets - losers contribute 0 - so breakeven_hit = 1/(1+realized ROI) and gate G4 ('beats_vig') is tested against a quantity derived from the outcomes being tested. Every spread strategy at ordinary prices is then failed by construction (e.g. WIND15_UNDER: breakeven_hit 0.9326 = 1/1.0724 = 1/(1+ROI 0.0723)). The per-bet odds ARE present in that pipeline's bet ledger (home_spread_odds etc.), so the correct price-based hurdle is computable there with a one-line fix. Nothing in the computed layer was edited by this session; the value is transcribed as dataset_breakeven_hit_transcribed in data/leaderboard_signal_staking.json and NOT used for ranking - the signal split ranks against the standard -110 reference hurdle instead and labels it.",
  "source": "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
  "severity": "High", "sourceIds": ["S47"],
  "action": "SG28: recompute breakeven from per-bet odds in the computed layer and re-run its gates; until then treat its G4 column as unusable."},
]


def main():
    add_rows("requirements.json", REQS)
    add_rows("questions.json", QUESTIONS)
    add_rows("suggestions.json", SUGGESTIONS)
    add_rows("flags.json", FLAGS)

    # source S52
    path = os.path.join(DATA, "sources.tsv")
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not any(l.startswith("S52\t") for l in lines):
        lines.append("\t".join([
            "S52",
            "NFL.com 2026 schedules - official game results, weeks 1-10",
            "NFL.com (National Football League)",
            "https://www.nfl.com/schedules/2026/by-week/week-10",
            "Official (league)",
            "2026-11-14",
            "VERIFIED",
            "Transcribed in raw/schedule-results-2026-week1-10.tsv (137 games). "
            "Verification: recomputing W/L/T and PF/PA for all 32 clubs from the "
            "feed reproduces data/standings.tsv exactly (tools/verify_results.py).",
        ]))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print("sources.tsv: +S52")
    else:
        print("sources.tsv: S52 already present")

    # gate G-14
    g = load("validation_gates.json")
    if not any(r["g_id"] == "G-14" for r in g["rows"]):
        g["rows"].append({
            "g_id": "G-14",
            "gate": "Demotion gate - live strategies return to paper",
            "kind": "HARD",
            "metric": "trailing flat-stake hit rate vs break-even; max flat-stake drawdown; trailing mean CLV",
            "threshold": "DEMOTE when any of: (D1) window hit rate below break-even at the prices paid with one-sided p < 0.10; (D2) max drawdown > 25 flat-stake units; (D3) mean CLV and its bootstrap 95% upper bound both < 0. Re-promotion (PAPER->LIVE) requires 300 FRESH settled bets passing the G-2b standard.",
            "why": "A gate set decides who gets promoted; this decides who gets sent back. Without it a live badge outlives the edge that earned it, and a leaderboard decays into a graveyard of former winners. Old bets never re-qualify an entry: the burden of proof resets.",
            "impl": "engine/demotion.py demotion_status() / repromotion_status(); thresholds are constructor arguments (proposed rules, flag F28).",
            "sources": ["SRC-015"],
        })
        save("validation_gates.json", g)
        print("validation_gates.json: +G-14")
    else:
        print("validation_gates.json: G-14 already present")


if __name__ == "__main__":
    sys.exit(main())
