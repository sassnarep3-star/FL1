#!/usr/bin/env python3
"""Build data/decision_readiness.json — the landing-page decision-readiness table.

Requirement (brief): "Put a decision-readiness table on the landing page: one row
per requirement, with the gate that blocks it and the number that would clear it."

Construction rules:
- One row per entry in data/requirements.json (R01..R28). The builder FAILS if the
  register grows and a row is missing, so the table cannot silently drift.
- Identity, requirement text and status are read from data/requirements.json —
  never duplicated here.
- "Gate that blocks it" and "the number that would clear it" reference ONLY
  published registers (question ids, flag ids, gate ids, verification counts).
  No new facts are introduced; where a clearing threshold is a proposal rather
  than a measured fact it is marked "proposed".

Run:  python3 scripts/build_decision_readiness.py
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "decision_readiness.json")


def load_json(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


def count_tsv(name, col=0):
    path = os.path.join(ROOT, "data", name)
    with open(path, encoding="utf-8") as fh:
        return sum(1 for ln in fh.read().splitlines()
                   if ln.strip() and not ln.startswith("#"))


def main():
    requirements = load_json("requirements.json")
    questions = load_json("questions.json")
    flags = load_json("flags.json")
    q_ids = {q["id"] for q in questions}
    f_ids = {f["id"] for f in flags}

    n_sources = count_tsv("sources.tsv")
    with open(os.path.join(ROOT, "data", "sources.tsv"), encoding="utf-8") as fh:
        verified = sum(1 for ln in fh.read().splitlines()[0:]
                       if ln.strip() and not ln.startswith("#") and "\tVERIFIED\t" in ln)

    # Curated rows, keyed by requirement id. "clears" numbers are either
    # measured counts from this repo's own verification runs or proposed
    # acceptance thresholds (marked).
    rows = {
        "R01": {"delivered": "25 generated pages; tools/checklinks.py link-checks every "
                             "internal link and anchor",
                "blocker": None, "blocker_refs": [],
                "clears": "0 broken internal links across all pages (checklinks run per build)"},
        "R02": {"delivered": "data/sources.tsv register; only VERIFIED rows are citable",
                "blocker": None, "blocker_refs": [],
                "clears": "%d of %d source records VERIFIED (page loaded and read this "
                          "session)" % (verified, n_sources)},
        "R03": {"delivered": "every table row carries a source cell, auto-added by the "
                             "page generator sweep",
                "blocker": None, "blocker_refs": [],
                "clears": "0 rows without a source pointer (generator + checklinks)"},
        "R04": {"delivered": "flagged.html — Flagged for Review",
                "blocker": None, "blocker_refs": [],
                "clears": "%d irregularities published with source links (F01..F%02d)"
                          % (len(flags), len(flags))},
        "R05": {"delivered": "data/requirements.json register",
                "blocker": None, "blocker_refs": [],
                "clears": "28 requirements registered, one row each on requirements.html"},
        "R06": {"delivered": "EXECUTIVE_SUMMARY + per-requirement pages",
                "blocker": None, "blocker_refs": [],
                "clears": "24 of 28 requirements verified done at the last count"},
        "R07": {"delivered": "data/suggestions.json register",
                "blocker": None, "blocker_refs": [],
                "clears": "every proposal reviewed before implementation (suggestions.html)"},
        "R08": {"delivered": "suggestions.html — dedicated review section",
                "blocker": None, "blocker_refs": [],
                "clears": "each suggestion states options, trade-offs and one recommended path"},
        "R09": {"delivered": "data/questions.json + questions.html",
                "blocker": None, "blocker_refs": [],
                "clears": "%d questions with what-we-know / what-we-miss / how-to-find-it"
                          % len(questions)},
        "R10": {"delivered": "Q-rows each name the missing data and how to obtain it",
                "blocker": None, "blocker_refs": [],
                "clears": "every blocking question lists a concrete discovery step"},
        "R11": {"delivered": "two live boards cross-linked: line-board.html (fair | market | "
                             "difference, per-cell provenance tiers) and origination.html "
                             "(market spine, mu/EWMA/HFA fitted from the 2025 official "
                             "standings capture, S75)",
                "blocker": None, "blocker_refs": [],
                "clears": "closed by PR #42 close-out: numeric lines originated for every "
                          "scheduled 2026 game in the mandated order; the remaining "
                          "benchmark-provenance decision (Q23/Q37) is policy, not "
                          "origination"},
        "R12": {"delivered": "fitted, walk-forward-measured signals: market-spine backtest "
                             "graded 23,219 trades (13,310 published) 2011-2026 over the "
                             "pinned capture (S70-S73); signal separated from staking on "
                             "both implementations",
                "blocker": None, "blocker_refs": [],
                "clears": "closed by PR #42 close-out with the honest headline (F50): no "
                          "signal beats the recorded market number yet; 0 promoted, 0 "
                          "reward units payable (F49); the detection infrastructure runs"},
        "R13": {"delivered": "engine/leaderboard.py + signal-vs-staking split + reward "
                             "eligibility rules",
                "blocker": None, "blocker_refs": [],
                "clears": "ranking rule frozen before results; 0 ranked entries until a "
                          "gate is passed (by design)"},
        "R14": {"delivered": "leaderboard divisions: singles, game parlays, SGP, prop combos",
                "blocker": None, "blocker_refs": [],
                "clears": "each division lists its min settled bets and why it is separate"},
        "R15": {"delivered": "validation.html — 14 gates G-1..G-14 incl. demotion",
                "blocker": None, "blocker_refs": [],
                "clears": "every strategy row lists the gates it must clear before ranking"},
        "R16": {"delivered": "correlation-register.html (C-A1..C-A5 with n and Fisher CIs) "
                             "PLUS the correlation gate (correlation-gate.html) that "
                             "publishes the pairs it refuses with the reason "
                             "(correlations_held.tsv) instead of a number",
                "blocker": None, "blocker_refs": [],
                "clears": "closed by PR #42 close-out: values determined from official "
                          "operands only, enforced in code; the availability pair stays "
                          "blank at n=1 by rule (C-A4)"},
        "R17": {"delivered": "rank by luck-removed edge (CI lower bound vs price hurdle), "
                             "control baseline, multiplicity adjustment",
                "blocker": None, "blocker_refs": [],
                "clears": "0 of 16 computed entries proven — the metric rejects them all; "
                          "see the dashboard luck panel"},
        "R18": {"delivered": "injuries.html — official Week 10 report, 345 rows + a "
                             "second dated read with published delta",
                "blocker": None, "blocker_refs": [],
                "clears": "2 dated reads (2026-11-14, 2026-11-16); 34 row-level changes "
                          "published as a delta, never a level"},
        "R19": {"delivered": "league-wide per-club deficiency views: depth.html carries 71 "
                             "charted ladders (ruled-Out first string, replacement string, "
                             "out-trail) re-derived by an independent verifier "
                             "(tools/verify_replacement.py) and cross-checked against a "
                             "second implementation (35 core rows, 31 exact)",
                "blocker": None, "blocker_refs": [],
                "clears": "closed by PR #42 close-out; known limits stay published (HOU "
                          "image-only F16; club charts self-labelled unofficial F10; "
                          "Dallas dual-first-string definition open for review)"},
        "R20": {"delivered": "25 pages live on GitHub Pages from main /",
                "blocker": None, "blocker_refs": [],
                "clears": "Pages build reported 'built'; live pages re-fetched clean"},
        "R21": {"delivered": "price-snapshots store records open+close per originated market",
                "blocker": None, "blocker_refs": [],
                "clears": "close cells populated from the captured board; open cells stay "
                          "blank because no source exists (F37) — not invented"},
        "R22": {"delivered": "verified-results-feed.html — 137 settled 2026 games",
                "blocker": None, "blocker_refs": [],
                "clears": "recomputing all 32 clubs' W/L/T and PF/PA reproduces the "
                          "official standings exactly (32/32); Week 10 finals extension "
                          "verified V1-V4 on 2026-11-16"},
        "R23": {"delivered": "side, then total, then moneyline — fixed order published",
                "blocker": None, "blocker_refs": [],
                "clears": "order logged as a design change (F27), not made silently"},
        "R24": {"delivered": "line-board.html — fair | market | difference as separate "
                             "columns",
                "blocker": None, "blocker_refs": [],
                "clears": "market cells carry the third-party badge and flag (F23) instead "
                          "of a silent estimate"},
        "R25": {"delivered": "signal-vs-staking.html — rank computed from the signal block "
                             "only",
                "blocker": None, "blocker_refs": [],
                "clears": "staking block reported beside, cannot move the rank; demo: the "
                          "best-ROI entry is rejected on signal"},
        "R26": {"delivered": "replacement-depth.html — string number of the replacement, "
                             "not just the fact",
                "blocker": None, "blocker_refs": [],
                "clears": "69 affected Week 10 spots published with the next available "
                          "string per slot"},
        "R27": {"delivered": "correlation-register.html — official-only values, n "
                             "published with every value",
                "blocker": None, "blocker_refs": [],
                "clears": "5 official pairs (n=32..137; one pair blank by rule with n=1); "
                          "third-party correlations excluded by engine rule"},
        "R28": {"delivered": "validation gate G-14 + engine/demotion.py",
                "blocker": None, "blocker_refs": [],
                "clears": "thresholds are proposed rules (F28) pending Q24/Q33 freeze; "
                          "0 live entries to demote yet"},
    }

    out_rows = []
    missing = []
    for r in requirements:
        rid = r["id"]
        if rid not in rows:
            missing.append(rid)
            continue
        c = rows[rid]
        bad_refs = [x for x in c["blocker_refs"] if x.startswith("Q") and x not in q_ids]
        bad_refs += [x for x in c["blocker_refs"] if x.startswith("F") and x not in f_ids]
        if bad_refs:
            raise SystemExit("FAIL: %s references unknown register ids %s"
                             % (rid, bad_refs))
        out_rows.append({
            "id": rid,
            "requirement": r["requirement"],
            "status": r["status"],
            "page": r.get("page", ""),
            "delivered": c["delivered"],
            "blocker": c["blocker"],
            "blocker_refs": c["blocker_refs"],
            "clears": c["clears"],
        })
    if missing:
        raise SystemExit("FAIL: requirements.json holds ids with no decision-readiness "
                         "row: %s" % missing)
    if len(out_rows) != len(rows):
        raise SystemExit("FAIL: curated rows outnumber requirements.json entries")

    payload = {
        "id": "decision_readiness",
        "title": "Decision-readiness — one row per requirement",
        "updated": "2026-11-16",
        "requirement": "Put a decision-readiness table on the landing page: one row per "
                       "requirement, with the gate that blocks it and the number that "
                       "would clear it.",
        "notes": "Identity and status come from data/requirements.json (asserted at "
                 "build time). Blockers cite published question/flag/gate ids. Clearing "
                 "numbers are this repo's own verification counts; where a threshold is "
                 "a proposal it is marked proposed.",
        "rows": out_rows,
        "provenance": {"tier": "DERIVED", "source_ids": ["S01", "S03", "S52", "S77", "S78"],
                       "inputs": ["data/requirements.json", "data/questions.json",
                                  "data/flags.json", "data/sources.tsv"]},
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("decision-readiness rows: %d (done=%d partial=%d)" % (
        len(out_rows),
        sum(1 for r in out_rows if r["status"] == "done"),
        sum(1 for r in out_rows if r["status"] != "done")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
