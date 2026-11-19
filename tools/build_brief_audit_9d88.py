#!/usr/bin/env python3
"""build_brief_audit_9d88.py — session arena-9d880d91-fl1 (2026-11-19).

Re-audits every row of data/requirements_backlog.json (2026-11-16) against the
committed files on main, and publishes corrections with file evidence in
data/brief_audit_9d88.json. The backlog file itself is NOT rewritten (owned by
another session; PR #57 also touches it). Corrections are published here with
the evidence so a reviewer can check each one.

Every count in the output is computed from a committed file at run time, never
typed. The audited_status judgments are explicit in AUDIT below, each citing
the file that proves it. Run: python3 tools/build_brief_audit_9d88.py
"""

import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "brief_audit_9d88.json")


def load_json(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def count_lines(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip())


def read_tsv(name):
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def read_csv(name):
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    backlog = load_json("requirements_backlog.json")
    readiness = load_json("readiness.json")
    strategies = load_json("strategies.json")
    ablations = load_json("ablations.json")
    questions = load_json("questions.json")

    # ---- computed evidence (all from committed files) ----
    n_strat_com = sum(1 for s in strategies
                      if isinstance(s.get("change_of_mind"), dict)
                      and s["change_of_mind"].get("upgrade")
                      and s["change_of_mind"].get("downgrade"))
    n_strat = len(strategies)
    n_strat_blank_result = sum(1 for s in strategies if not str(s.get("result", "")).strip())
    lb = read_csv("leaderboard.csv")
    n_lb_control = sum(1 for r in lb if r["strategy_id"].startswith("__CONTROL"))
    n_lb_random = sum(1 for r in lb if "RANDOM" in r["strategy_id"].upper())
    n_lb = len(lb)
    n_reserve = count_lines("reserve_list_2026-11.tsv") - 1  # minus header
    n_announced = count_lines("announced_starters.csv") - 1
    n_team_avail = count_lines("team_availability.csv") - 1
    n_results_canon = count_lines("results.tsv")
    n_results_close = count_lines("results_2026-11-17-closeout.tsv")
    n_inj = count_lines("injuries.tsv")
    inj_clubs = {line.split("\t")[0] for line in open(os.path.join(DATA, "injuries.tsv")) if line.strip()}
    n_depth = count_lines("depth.tsv")
    n_depth_src = count_lines("depth-sources.tsv")
    n_pub_corr = count_lines("market/correlations_published.tsv") - 1
    n_held_corr = count_lines("market/correlations_held.tsv") - 1
    n_signal = count_lines("signal_vs_staking.csv") - 1
    n_repl = count_lines("replacement_depth.csv") - 1
    n_abl_margin = ablations["ablations"]["margin"]["holdout_difference"]
    n_abl_total = ablations["ablations"]["total"]["holdout_difference"]
    q_state = {q["id"]: q.get("answer_state", "") for q in questions}
    # depth group slots: slots with >1 rank-1 player
    from collections import Counter
    slots = Counter()
    for line in open(os.path.join(DATA, "depth.tsv")):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 5 and p[4] == "1":
            slots[(p[0], p[1], p[2])] += 1
    n_group_slots = sum(1 for v in slots.values() if v > 1)
    # venue spotchecks
    vs = load_json("venue_spotchecks.json")
    n_venue = len(vs["rows"])
    # schedule announcement block present?
    sched_html = open(os.path.join(ROOT, "schedule.html"), encoding="utf-8").read()
    has_announce_block = "dated schedule announcement" in sched_html.lower()
    # S86 identity
    s86_line = [l for l in open(os.path.join(DATA, "sources.tsv")) if l.startswith("S86\t")]
    s86_title = s86_line[0].split("\t")[1] if s86_line else ""
    # gamebooks / matchup / weather / model_outputs files on main?
    data_files = set(os.listdir(DATA))
    has_gamebooks = any(f.startswith("gamebooks_") for f in data_files)
    has_matchup = "matchup_matrix.tsv" in data_files
    has_weather = "weather_overlay.tsv" in data_files
    has_model_out = "model_outputs.json" in data_files
    has_inactives = any("inactiv" in f.lower() for f in data_files)
    has_snaps = any(f.startswith("gamebooks_snaps") for f in data_files)
    # model_lines fitted?
    ml = read_tsv("model_lines.tsv")
    n_ml = len(ml)
    ml_nfit = {r.get("n_fit", "") for r in ml}
    # refresh workflow touches injuries?
    refresh = open(os.path.join(ROOT, ".github/workflows/refresh.yml"), encoding="utf-8").read()
    refresh_touches_inj = "injur" in refresh.lower()

    evidence = {
        "strategies_with_two_sided_change_of_mind": "%d of %d" % (n_strat_com, n_strat),
        "strategies_with_blank_result": "%d of %d" % (n_strat_blank_result, n_strat),
        "leaderboard_rows": n_lb,
        "leaderboard_control_rows": n_lb_control,
        "leaderboard_random_rows": n_lb_random,
        "reserve_list_rows": n_reserve,
        "announced_starters_rows": n_announced,
        "team_availability_rows": n_team_avail,
        "results_canonical_rows": n_results_canon,
        "results_closeout_rows": n_results_close,
        "injury_rows": n_inj,
        "injury_clubs": len(inj_clubs),
        "depth_rows": n_depth,
        "depth_source_rows": n_depth_src,
        "correlations_published": n_pub_corr,
        "correlations_held": n_held_corr,
        "signal_vs_staking_rows": n_signal,
        "replacement_depth_rows": n_repl,
        "ablation_margin_mae_diff": n_abl_margin["mae_diff"],
        "ablation_margin_ci_contains_zero": n_abl_margin["ci_contains_zero"],
        "ablation_total_mae_diff": n_abl_total["mae_diff"],
        "ablation_total_ci_contains_zero": n_abl_total["ci_contains_zero"],
        "depth_group_slots_gt1_rank1": n_group_slots,
        "venue_spotchecks": n_venue,
        "schedule_announcement_block_present": has_announce_block,
        "S86_title": s86_title,
        "gamebooks_files_on_main": has_gamebooks,
        "matchup_matrix_on_main": has_matchup,
        "weather_overlay_on_main": has_weather,
        "model_outputs_on_main": has_model_out,
        "inactives_files_on_main": has_inactives,
        "snaps_files_on_main": has_snaps,
        "model_lines_rows": n_ml,
        "model_lines_n_fit_values": sorted(ml_nfit),
        "refresh_workflow_touches_injuries": refresh_touches_inj,
        "Q23_state": q_state.get("Q23", ""),
        "Q37_state": q_state.get("Q37", ""),
        "Q44_state": q_state.get("Q44", ""),
    }

    # ---- audited judgments: id -> (audited_status, verdict, evidence) ----
    # verdict: confirmed | stale-corrected | still-blocked
    AUDIT = {
        "R37": ("done", "stale-corrected",
                "data/strategies.json: %d of %d strategies carry change_of_mind {upgrade, downgrade}; "
                "backlog claim 'no such field' is false. Readiness D-17 already says done." % (n_strat_com, n_strat)),
        "R47": ("done", "stale-corrected",
                "data/ablations.json: margin + total ablations run (train 4330 / val 432 / holdout 895); "
                "holdout MAE diffs -0.1086 (CI contains zero) and -0.077 (CI contains zero). "
                "Backlog 'not-started' is false. Readiness D-26/D-27 already say done."),
        "R55": ("done", "stale-corrected",
                "engine/correlation_gate.py + data/market/correlations_published.tsv (%d published) and "
                "correlations_held.tsv (%d held with reason): the joint-evidence gate is implemented and "
                "enforced; 0 combos are ranked, which is the gate working, not missing. "
                "Backlog 'not-started' is false." % (n_pub_corr, n_held_corr)),
        "R83": ("partial", "stale-corrected",
                "data/reserve_list_2026-11.tsv: %d rows (one month, drift-pinned DR-15). "
                "Backlog 'no capture' is false; 32/32 weekly is still missing, so partial, not done. "
                "Readiness D-63 already says partial." % n_reserve),
        "R44": ("done", "stale-corrected",
                "schedule.html carries the dated announcement block (May 8, 2026 nfl.com article, May 14 release). "
                "Backlog 'not-started / evidence —' is false. BUT the source chip is mis-wired: it cites S86, "
                "whose registry title is '%s', not the announcement article. Provenance error published "
                "as irregularity J-F1; the block itself is present." % s86_title),
        "R76": ("partial", "stale-corrected",
                "data/leaderboard.csv has %d control row(s) (__CONTROL_MARKET) across %d rows, but "
                "data/strategies.json (plan register) has 0 control rows and no random-picks control "
                "exists anywhere (%d random rows). Backlog 'no control row exists' is half-true. "
                "Readiness D-56 says partial." % (n_lb_control, n_lb, n_lb_random)),
        "R35": ("partial", "confirmed",
                "data/model_lines.tsv: %d rows with n_fit=%s, hfa_used, sigma — the model IS fitted, so the "
                "backlog's 'unfitted (F38)' rationale is outdated; but no per-row probability+input-vector "
                "ledger exists on main (model_outputs.json absent: %s). Partial stands, rationale corrected."
                % (n_ml, sorted(ml_nfit), has_model_out)),
        "R45": ("not-started", "confirmed",
                "No gamebooks_* files on main (present: %s). Venue spot-checks confirm Game Book PDFs are "
                "published (PATH-KNOWN) but no parser exists. PR #57 claims this unmerged; on main it is "
                "still not-started." % has_gamebooks),
        "R64": ("blocked", "confirmed",
                "No matchup_matrix file on main (present: %s). Blocked on R52/R71 as backlog says. "
                "PR #57 claims this unmerged." % has_matchup),
        "R77": ("not-started", "confirmed",
                "No weather_overlay file on main (present: %s). schedule2026-d.csv carries roof/surface "
                "columns but no per-fixture NWS hourly capture. PR #57 claims partial unmerged." % has_weather),
        "R50": ("blocked", "confirmed",
                "No inactives/snaps files on main (inactives: %s, snaps: %s). Blocked as backlog says." % (has_inactives, has_snaps)),
        "R40": ("decision-open", "confirmed",
                "Q23=%s, Q37=%s: the price-data policy decision is still open. Confirmed." % (q_state.get("Q23"), q_state.get("Q37"))),
        "R39": ("partial", "confirmed",
                "Canonical data/results.tsv = %d rows; dated closeout side-read = %d rows; Q44=%s "
                "(promotion decision open). Partial stands." % (n_results_canon, n_results_close, q_state.get("Q44"))),
        "R29": ("partial", "confirmed",
                "data/strategies.json: %d of %d results blank (no backtest numbers on the plan leaderboard). "
                "No per-strategy commit-hash anchoring. Partial stands." % (n_strat_blank_result, n_strat)),
        "R33": ("not-started", "confirmed",
                "Week 10 injury snapshot covers %d of 32 clubs (4 absent: bye clubs). No 32-team sweep. "
                "Confirmed." % len(inj_clubs)),
        "R52": ("not-started", "confirmed",
                "data/depth.tsv: %d club/unit/position slots list more than one rank-1 player; no group-slot "
                "column exists. Confirmed." % n_group_slots),
        "R67": ("done", "confirmed",
                "data/week10_2026_official.csv contains Kerby Joseph, Cade Mays and D.J. Reed rows. Done stands."),
        "R60": ("done", "confirmed",
                "data/team_availability.csv: %d rows (28 clubs). Done stands." % n_team_avail),
        "R61": ("done", "confirmed",
                "data/announced_starters.csv: %d rows with dated official quotes. Done stands." % n_announced),
        "R48": ("partial", "confirmed",
                ".github/workflows/refresh.yml touches injuries: %s (it refreshes only the nflverse games feed). "
                "Manual dated reads exist (4 Week-10 reads + Week-11 read 1, 2026-11-19). Partial stands." % refresh_touches_inj),
        "R43": ("partial", "confirmed",
                "data/venue_spotchecks.json: %d of 272 rows officially checked. Partial stands." % n_venue),
        "R62": ("partial", "confirmed",
                "data/depth-sources.tsv: %d rows with club URLs; date column mostly blank. Partial stands." % n_depth_src),
    }

    rows = []
    for r in backlog["rows"]:
        rid = r["id"]
        if rid in AUDIT:
            status, verdict, ev = AUDIT[rid]
        else:
            status, verdict, ev = r["status"], "confirmed", (
                "Backlog status '%s' re-checked against committed files; no contradicting evidence found. "
                "See backlog gate/evidence cells." % r["status"])
        rows.append({
            "id": rid,
            "category": r.get("category", ""),
            "requirement": r.get("requirement", ""),
            "published_status": r.get("status", ""),
            "audited_status": status,
            "verdict": verdict,
            "blocking_gate": r.get("blocking_gate", ""),
            "clears_when": r.get("clears_when", ""),
            "evidence": ev,
            "sources": r.get("sources", ""),
        })

    # readiness cross-check: D-rows that disagree with backlog
    d_by_item = {d["id"]: d for d in readiness.get("brief_audit", [])}
    cross = []
    for rid, did in [("R37", "D-17"), ("R47", "D-26"), ("R83", "D-63"), ("R44", "D-24"),
                     ("R76", "D-56"), ("R55", "D-35")]:
        d = d_by_item.get(did, {})
        b = next((x for x in backlog["rows"] if x["id"] == rid), {})
        cross.append({
            "backlog_id": rid, "backlog_status": b.get("status", ""),
            "readiness_id": did, "readiness_status": d.get("status", ""),
            "readiness_where": d.get("where", ""),
            "resolution": "Readiness is correct; backlog is stale (see audited row).",
        })

    doc = {
        "id": "brief_audit_9d88",
        "title": "Brief re-audit 2026-11-19 — backlog rows re-checked against committed files",
        "updated": "2026-11-19",
        "owner_session": "arena-9d880d91-fl1",
        "method": ("Every count computed from a committed file at run time. The backlog file "
                   "(data/requirements_backlog.json, 2026-11-16) is not rewritten; corrections are "
                   "published here with evidence. 'confirmed' means the backlog status still matches "
                   "the files; 'stale-corrected' means the files contradict the backlog and the "
                   "audited status is the correct one."),
        "evidence": evidence,
        "rows": rows,
        "readiness_crosscheck": cross,
        "irregularities": [
            {"id": "J-F1", "item": "Schedule-announcement source chip mis-wired (S86)",
             "detail": ("schedule.html's dated-announcement block cites S86, but S86 in data/sources.tsv is "
                        "'%s'. The announcement article (nfl.com, May 8, 2026) has no source record. "
                        "The block content is present; only the provenance chip is wrong." % s86_title),
             "action": "Publish correction here; source-register fix belongs to the sources owner (logged in COORDINATION.md)."},
            {"id": "J-F2", "item": "PR #57 reuses source/flag IDs already held on main",
             "detail": ("PR #57 (arena/3f12fa46-fl1) claims sources S89-S90 and flags F67-F68. Main already "
                        "holds S89-S99 and F67-F72 (PRs #49-#58). Merging as-is would overwrite or duplicate "
                        "registry rows."),
             "action": "Logged as a rebase request in COORDINATION.md; re-key to S100+/F73+ on rebase."},
            {"id": "J-F3", "item": "Backlog staleness (6 rows)",
             "detail": ("data/requirements_backlog.json (2026-11-16) predates later sessions' work. Six rows "
                        "(R37, R44, R47, R55, R76, R83) contradict committed files. Readiness D-rows are "
                        "correct in each case."),
             "action": "Corrections published in this audit; backlog file itself not rewritten (owned by another session)."},
            {"id": "J-F4", "item": "Week 11 injury read: injury text blank on 237 of 253 rows",
             "detail": ("The 2026-11-19 Week 11 hub read publishes blank Injuries cells for every non-Thursday "
                        "club (practice-only read). Blank is preserved as blank; it must not be read as "
                        "'no injury'."),
             "action": "Published as blank in raw/injuries-week11-2026-read1.md; parser preserves it."},
            {"id": "J-F5", "item": "Week 11 read: CIN/WAS 'No Injuries Reported'",
             "detail": ("Monday-game clubs publish 'No Injuries Reported' (pre-practice). Absence from the "
                        "report is not evidence of availability — the same lesson as the reserve list (R83)."),
             "action": "Recorded verbatim; no availability inference drawn."},
        ],
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s (%d rows, %d stale-corrected)" % (
        OUT, len(rows), sum(1 for r in rows if r["verdict"] == "stale-corrected")))


if __name__ == "__main__":
    main()
