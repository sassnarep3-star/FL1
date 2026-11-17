#!/usr/bin/env python3
"""
build_d5.py — session arena/d50423eb-fl1's data spine.

Reads only committed inputs (raw/live/*.md|tsv, data/*.tsv, data/*.json, data/*.csv,
the pre-registration registry) and writes the derived layers the site renders:

  data/live_state_d5.json            what the official pages said, at what clock time
  data/org_health_d5.json            availability / depth / model-input / price coverage
  data/availability_d5.json          per-club, per-unit expected-starter -> replacement matrix
  data/scorecard_d5.json             the strategy competition: gates, controls, sample bars
  data/forecast_ledger_d5.csv|json   pre-registered shadow forecasts (in and out of sample)

Every published number is computed here from the inputs, never typed into a page.
Where an input is missing the field is None and the page prints an em dash.

Run:  python3 scripts/build_d5.py
"""

import csv
import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from engine import scoreboard_d5 as SB  # noqa: E402

DATA = os.path.join(ROOT, "data")
LIVE = os.path.join(ROOT, "raw", "live")

CAPTURES = {
    "standings": ("raw/live/2026-11-17-standings-league-reg.tsv",
                  "https://www.nfl.com/standings/league/2026/REG", "2026-11-17T02:36Z"),
    "week10": ("raw/live/2026-11-17-week10-finals.tsv",
               "https://www.nfl.com/schedules/2026/REG10/", "2026-11-17T02:36Z"),
    "week11": ("raw/live/2026-11-17-week11-slate.tsv",
               "https://www.nfl.com/schedules/2026/by-week/week-11", "2026-11-17T02:36Z"),
    "injuries": ("raw/live/2026-11-17-injury-report-week10.md",
                 "https://www.nfl.com/injuries/", "2026-11-17T02:39Z"),
}

PRACTICE = {"FULL": "Full Participation in Practice",
            "DNP": "Did Not Participate In Practice",
            "LIMITED": "Limited Participation in Practice"}

# Provider display positions that are spelled differently by different clubs.
POS_FAMILY = {
    "C": "OL", "LG": "OL", "RG": "OL", "LT": "OL", "RT": "OL", "G": "OL", "T": "OL",
    "LOT": "OL", "ROT": "OL", "OL": "OL",
    "DE": "EDGE", "EDGE": "EDGE", "LDE": "EDGE", "RDE": "EDGE", "RUSH": "EDGE",
    "DT": "IDL", "NT": "IDL", "LDT": "IDL", "RDT": "IDL", "DL": "IDL", "IDL": "IDL",
    "LB": "LB", "ILB": "LB", "MLB": "LB", "LILB": "LB", "RILB": "LB", "MIKE": "LB",
    "OLB": "LB", "LOLB": "LB", "ROLB": "LB", "SAM": "LB", "WILL": "LB", "SLB": "LB",
    "WLB": "LB",
    "CB": "CB", "LCB": "CB", "RCB": "CB", "NB": "CB", "NCB": "CB", "N": "CB", "DB": "DB",
    "S": "S", "FS": "S", "SS": "S",
    "QB": "QB", "RB": "RB", "HB": "RB", "FB": "FB", "WR": "WR", "TE": "TE",
    "K": "ST", "P": "ST", "LS": "ST",
}

UNIT_OF = {
    "QB": "Offense", "RB": "Offense", "FB": "Offense", "WR": "Offense", "TE": "Offense", "OL": "Offense",
    "EDGE": "Defense", "IDL": "Defense", "LB": "Defense", "CB": "Defense", "S": "Defense", "DB": "Defense",
    "ST": "Special Teams",
}

ALL32 = ["ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET",
         "GB", "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA", "MIN", "NE", "NO",
         "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS"]

# --------------------------------------------------------------------------- loaders


def load_tsv(name):
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def load_json(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def live_rows(key):
    path = os.path.join(ROOT, CAPTURES[key][0])
    with open(path, encoding="utf-8") as fh:
        return [l.rstrip("\n").split("\t") for l in fh
                if l.strip() and not l.startswith("#")]


def capture_meta():
    out = {}
    with open(os.path.join(LIVE, "MANIFEST-2026-11-17.json"), encoding="utf-8") as fh:
        man = json.load(fh)
    for k, (rel, url, when) in CAPTURES.items():
        rec = next((f for f in man["files"] if f["path"] == rel), None)
        out[k] = {"url": url, "read_at": when, "path": rel,
                  "sha256": rec["sha256"] if rec else None,
                  "bytes": rec["bytes"] if rec else None}
    return out


def parse_injuries():
    rows, club = [], None
    with open(os.path.join(ROOT, CAPTURES["injuries"][0]), encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("## "):
                club = line[3:].strip()
                continue
            if not line.startswith("|") or not club:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) != 5 or cells[0] in ("Player", "---"):
                continue
            rows.append({"club": club, "player": cells[0], "pos": cells[1],
                         "injury": cells[2], "practice": cells[3], "status": cells[4]})
    return rows


def committed_injuries():
    out = []
    with open(os.path.join(DATA, "injuries.tsv"), encoding="utf-8", newline="") as fh:
        for r in csv.reader(fh, delimiter="\t"):
            if r:
                out.append({"club": r[0], "player": r[1], "pos": r[2], "injury": r[3],
                            "practice": r[4], "status": r[5]})
    return out


def depth_rows():
    with open(os.path.join(DATA, "depth.tsv"), encoding="utf-8", newline="") as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) < 5:
                continue
            yield {"club": f[0], "unit": f[1], "pos": f[2], "player": f[3],
                   "rank": int(f[4]) if f[4].isdigit() else None}


def results_rows():
    with open(os.path.join(DATA, "results.tsv"), encoding="utf-8", newline="") as fh:
        return [r for r in csv.reader(fh, delimiter="\t") if r]


# --------------------------------------------------------------------------- 1. live state
def build_live_state():
    meta = capture_meta()
    live = {}
    for f in live_rows("standings"):
        live[f[0]] = {"w": int(f[1]), "l": int(f[2]), "t": int(f[3]), "pct": f[4],
                      "pf": int(f[5]), "pa": int(f[6]), "net": int(f[7]),
                      "home": f[8], "road": f[9], "div": f[10], "conf": f[11],
                      "nonconf": f[12], "strk": f[13], "last5": f[14]}

    def as_map(name):
        m = {}
        with open(os.path.join(DATA, name), encoding="utf-8") as fh:
            for line in fh:
                f = line.rstrip("\n").split("\t")
                if len(f) >= 7:
                    m[f[0]] = {"w": int(f[1]), "l": int(f[2]), "t": int(f[3]),
                               "pf": int(f[5]), "pa": int(f[6])}
        return m

    older = as_map("standings_2026-11-16.tsv")
    base = as_map("standings.tsv")

    rows = []
    for club in ALL32:
        lv = live.get(club, {})
        od = older.get(club, {})
        bs = base.get(club, {})
        moved_vs_older = (lv.get("w"), lv.get("l"), lv.get("t"), lv.get("pf"), lv.get("pa")) != \
                         (od.get("w"), od.get("l"), od.get("t"), od.get("pf"), od.get("pa"))
        moved_vs_base = (lv.get("w"), lv.get("l"), lv.get("t"), lv.get("pf"), lv.get("pa")) != \
                        (bs.get("w"), bs.get("l"), bs.get("t"), bs.get("pf"), bs.get("pa"))
        rows.append({"club": club, "live": lv, "at_2026_11_16": od, "committed_site": bs,
                     "stale_vs_older": moved_vs_older, "stale_vs_base": moved_vs_base})

    finals = []
    for f in live_rows("week10"):
        if len(f) >= 7 and f[6] == "FINAL":
            finals.append({"week": f[0], "date": f[1], "away": f[2], "away_pts": int(f[3]),
                           "home": f[4], "home_pts": int(f[5]), "url": f[7]})

    slate = []
    for f in live_rows("week11"):
        if len(f) < 7:
            continue
        slate.append({"date": f[0], "kickoff_et": f[1], "network": f[2],
                      "away": f[3], "home": f[4], "venue": f[5] or None, "url": f[6]})

    inj = parse_injuries()
    com = committed_injuries()
    com_keys = {(r["club"], r["player"]) for r in com}
    live_keys = {(r["club"], r["player"]) for r in inj}
    added = sorted(live_keys - com_keys)
    missing = sorted(com_keys - live_keys)

    pmap = {"FULL": "Full Participation in Practice",
            "DNP": "Did Not Participate In Practice",
            "LIMITED": "Limited Participation in Practice"}
    com_by_key = {(r["club"], r["player"]): r for r in com}
    field_moves = []
    for r in inj:
        c = com_by_key.get((r["club"], r["player"]))
        if not c:
            continue
        before = (c["pos"], c["injury"], pmap.get(c["practice"], c["practice"]), c["status"])
        after = (r["pos"], r["injury"], r["practice"], r["status"])
        if before != after:
            field_moves.append({"club": r["club"], "player": r["player"],
                                "field": "position/injury/practice/status",
                                "at_2026_11_14": " | ".join(before),
                                "at_2026_11_17": " | ".join(after)})

    by_club = defaultdict(int)
    for r in inj:
        by_club[r["club"]] += 1

    return {
        "captures": meta,
        "standings": rows,
        "stale_vs_older": [r["club"] for r in rows if r["stale_vs_older"]],
        "stale_vs_base": [r["club"] for r in rows if r["stale_vs_base"]],
        "week10_finals": finals,
        "week11_slate": slate,
        "week11_venue_published": sum(1 for g in slate if g["venue"]),
        "injuries": {
            "rows": len(inj),
            "clubs": len(by_club),
            "by_club": dict(sorted(by_club.items())),
            "added_vs_2026_11_14": [{"club": a[0], "player": a[1]} for a in added],
            "missing_vs_2026_11_14": [{"club": a[0], "player": a[1]} for a in missing],
            "field_moves": field_moves,
            "committed_rows": len(com),
        },
    }


# --------------------------------------------------------------------------- 2. availability matrix
def build_availability(live_state):
    inj = parse_injuries()
    inj_by_player = {(r["club"], r["player"]): r for r in inj}
    published_seen = {k[1].lower(): k for k in inj_by_player}

    # depth slots: club/unit/pos -> ordered list of (rank, [players])
    slots = defaultdict(lambda: defaultdict(list))
    for d in depth_rows():
        slots[d["club"]][(d["unit"], d["pos"])].append((d["rank"], d["player"]))
    for club in slots:
        for k in slots[club]:
            slots[club][k].sort(key=lambda x: (x[0] if x[0] is not None else 99, x[1]))

    # A club whose chart is an image (HOU) or that publishes late (KC) has no rows here.
    chart_clubs = sorted(slots)

    matrix = []
    matched = 0
    unmatched_sample = []
    for r in inj:
        fam_pos = POS_FAMILY.get((r["pos"] or "").upper(), (r["pos"] or "").upper() or None)
        if fam_pos is None:
            continue
        # exact club slot whose position family matches
        candidates = [(k, v) for k, v in slots.get(r["club"], {}).items()
                      if POS_FAMILY.get((k[1] or "").upper(),
                                        (k[1] or "").upper() or None) == fam_pos]
        hit = None
        for k, v in candidates:
            for rank, player in v:
                if player == r["player"]:
                    hit = (k, rank, player, v)
                    break
            if hit:
                break
        if hit:
            matched += 1
            (unit, pos), rank, player, members = hit
            # the replacement is the *next* listed player at the same slot, and only
            # when the club itself lists one. Grouped slots may carry several at the
            # same rank; the whole group after `player` counts.
            order = [p for _r, p in members]
            idx = order.index(player)
            nxt = order[idx + 1] if idx + 1 < len(order) else None
            matrix.append({
                "club": r["club"], "unit": unit, "pos": pos, "player": player,
                "depth_rank": rank,
                "group_size_at_rank": sum(1 for rr, _p in members if rr == rank),
                "status": r["status"] or None,
                "practice": r["practice"] or None,
                "replacement": nxt,
                "replacement_status": (inj_by_player.get((r["club"], nxt), {}) or {}).get("status") or None,
                "string_gap": 1 if nxt else None,
                "chart_source": None,
            })
        else:
            if len(unmatched_sample) < 40:
                unmatched_sample.append({"club": r["club"], "player": r["player"], "pos": r["pos"]})

    # Chart source id per club, from the committed register.
    chart_src = {}
    with open(os.path.join(DATA, "depth-sources.tsv"), encoding="utf-8") as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) >= 3:
                chart_src[f[0]] = {"id": f[1], "url": f[2]}
    for m in matrix:
        cs = chart_src.get(m["club"], {})
        m["chart_source"] = cs.get("id")
        m["chart_url"] = cs.get("url")

    # ---- string of the *starter* who was displaced, per club/unit
    out = [m for m in matrix if m["status"] in ("Out", "Doubtful", "Questionable")]
    affected = [m for m in out if m["replacement"]]

    per_club = defaultdict(lambda: {"out": 0, "doubtful": 0, "questionable": 0,
                                    "named_replacement": 0, "units": defaultdict(int)})
    for m in out:
        rec = per_club[m["club"]]
        key = {"Out": "out", "Doubtful": "doubtful", "Questionable": "questionable"}[m["status"]]
        rec[key] += 1
        if m["replacement"]:
            rec["named_replacement"] += 1
            rec["units"][m["unit"]] += 1

    clubs = []
    for c in ALL32:
        rec = per_club.get(c, {"out": 0, "doubtful": 0, "questionable": 0,
                               "named_replacement": 0, "units": defaultdict(int)})
        clubs.append({
            "club": c,
            "chart_captured": c in slots,
            "injured_on_report": len([r for r in inj if r["club"] == c]),
            "starters_out": rec["out"],
            "starters_doubtful": rec["doubtful"],
            "starters_questionable": rec["questionable"],
            "named_replacement": rec["named_replacement"],
            "replacement_by_unit": dict(rec["units"]),
        })

    return {
        "rows": matrix,
        "slots": sum(len(v) for v in slots.values()),
        "clubs_with_chart": len(chart_clubs),
        "clubs_missing_chart": [c for c in ALL32 if c not in slots],
        "injured_matched_to_slot": matched,
        "injured_total_on_report": len(inj),
        "injured_not_on_any_slot": len(inj) - matched,
        "unmatched_sample": unmatched_sample,
        "designated": len(out),
        "designated_with_named_replacement": len(affected),
        "per_club": clubs,
    }


# --------------------------------------------------------------------------- 3. control baselines
def build_controls():
    n_games = len(live_rows("week11"))
    price = -110
    payout = SB.american_payout_per_unit(price)
    be = SB.american_to_prob(price)
    return {
        "price": price,
        "payout_per_unit": round(payout, 4),
        "breakeven_hit": round(be, 5),
        "random_side_expected_hit": 0.5,
        "random_side_expected_yield": round(0.5 * (1 + payout) - 1.0, 5),
        "random_side_expected_hit_ci_at_n": {
            "n": 100,
            "lo": round(SB.wilson(50, 100)[0], 4),
            "hi": round(SB.wilson(50, 100)[1], 4),
        },
        "favourite_note": "a favourites-only rule must clear %.4f to break even at %d; "
                          "it has no skill until it does" % (be, price),
        "slate_games": n_games,
        "power": {
            "edge_p1": SB.EDGE_FOR_POWER[0],
            "breakeven_p0": SB.EDGE_FOR_POWER[1],
            "power": SB.EDGE_FOR_POWER[2],
            "bets_for_55_vs_524": SB.sample_for_edge(*SB.EDGE_FOR_POWER),
        },
    }


# --------------------------------------------------------------------------- 4. forecast ledger
def build_forecasts():
    """Score the frozen Elo model's own recorded probabilities, honesty intact.

    Source: data/fair_lines.csv, written by an earlier session with the model version
    string stored per row. We take only rows the model had a number for AND that have
    a result in data/results.tsv. The benchmark is the market spread from the same
    file, which is THIRD-PARTY (nflverse). Both facts are printed on the page.
    """
    with open(os.path.join(DATA, "fair_lines.csv"), encoding="utf-8", newline="") as fh:
        fair = list(csv.DictReader(fh))

    res = {}
    for r in results_rows():
        if r[3] == "" or r[5] == "":
            continue
        res[(r[0], r[2], r[4])] = (int(r[3]), int(r[5]))

    rows = []
    for f in fair:
        if f["season"] != "2026" or f["played"] != "yes":
            continue
        key = (f["week"], f["away_team"], f["home_team"])
        if key not in res:
            continue
        ap, hp = res[key]
        margin = hp - ap  # home margin, positive = home won by
        fair_spread = f["side_fair_spread_away"]
        fair_ml = f["ml_fair_home_american"]
        if fair_spread == "" or fair_ml == "":
            continue
        # Score the stored model probability directly. Do not reconstruct a probability
        # from its point spread using an unvalidated margin distribution.
        p_home_win = SB.american_to_prob(int(float(fair_ml)))
        fair_home = -float(fair_spread)
        outcome_home_win = 1 if margin > 0 else 0
        bench = 0.5 if margin != 0 else 0.5
        market = f["side_market_spread_away"]
        rows.append({
            "game_id": f["game_id"], "week": int(f["week"]), "gameday": f["gameday"],
            "away": f["away_team"], "home": f["home_team"],
            "model_version": f["model_version"],
            "p_home_win_fair": round(p_home_win, 5),
            "outcome_home_win": outcome_home_win,
            "market_spread_away": (float(market) if market != "" else None),
            "market_provenance": f["market_provenance"],
            "fair_spread_home": round(fair_home, 2),
            "final_margin_home": margin,
        })
    rows.sort(key=lambda r: (r["week"], r["gameday"], r["away"]))
    return rows


# --------------------------------------------------------------------------- 5. scorecard
def build_scorecard(forecasts, avail):
    registry = load_json("strategy_registry_d5.json")
    bars = SB.sample_bars()
    n_hyp = len(registry)
    ctx = {"sample_bar": bars, "n_hypotheses": n_hyp}

    # ---- is the frozen Elo model's probability array skillful against the benchmark?
    skill = None
    if len(forecasts) >= 10:
        probs = [r["p_home_win_fair"] for r in forecasts]
        outcomes = [r["outcome_home_win"] for r in forecasts]
        bench = [0.5] * len(forecasts)
        clusters = [r["game_id"] for r in forecasts]
        skill = SB.cluster_bootstrap_skill(probs, outcomes, bench, clusters, reps=1000)
        skill["log_loss"] = round(SB.log_loss(probs, outcomes), 5)
        skill["brier"] = round(SB.brier(probs, outcomes), 5)
        skill["bench_brier"] = round(SB.brier(bench, outcomes), 5)
        skill["benchmark_note"] = "constant 0.5 outcome baseline only; spread prices cannot be converted to win probabilities without a validated margin distribution, so no market skill claim is made"

    # ---- multiplicity across the registered hypotheses (all currently untested)
    pvals = [1.0] * n_hyp
    bh = SB.benjamini_hochberg(pvals, q=0.05)

    entries = []
    for i, e in enumerate(registry):
        e = dict(e)
        e["multiplicity_pass"] = bool(bh[i])
        e["multiplicity_detail"] = ("not tested: n=0 forecasts, p=1.0 after BH across %d "
                                    "registered hypotheses" % n_hyp)
        # attach the one real measured signal we have, to the entry that owns it
        if e["id"] == "D5S04" and skill:
            e["signal"] = {"n": skill["n"], "bss": round(skill["bss"], 5),
                           "bss_lo": round(skill["lo"], 5) if skill.get("lo") is not None else None,
                           "bss_hi": round(skill["hi"], 5) if skill.get("hi") is not None else None}
            e["note"] = ("this entry's own recorded probabilities were scored ex post, not "
                         "pre-registered: the number shows the model exists and can be "
                         "evaluated, and it does NOT count as a prospective record")
        gates = SB.gates_for(e, ctx)
        e["gates"] = gates
        e["gates_passed"] = sum(1 for g in gates if g["passed"])
        e["gates_total"] = len(gates)
        e["qualified"] = SB.qualified(gates)
        entries.append(e)
    SB.rank(entries)

    return {
        "divisions": list(SB.DIVISIONS),
        "registry": entries,
        "sample_bars": bars,
        "power": {"edge": SB.EDGE_FOR_POWER[0], "breakeven": SB.EDGE_FOR_POWER[1],
                  "power": SB.EDGE_FOR_POWER[2], "n": SB.sample_for_edge(*SB.EDGE_FOR_POWER)},
        "controls": build_controls(),
        "n_hypotheses": n_hyp,
        "measured": skill,
        "qualified_count": sum(1 for e in entries if e["qualified"]),
        "reward_pool_basis": ("a reward is payable only when qualified; %d of %d entries "
                              "are qualified right now" % (sum(1 for e in entries if e["qualified"]), n_hyp)),
        "divisions_note": ("singles, game parlay, same-game parlay and prop combo are scored in "
                           "separate divisions because their variance and their dependence "
                           "structure differ; ranking them together would let a high-variance "
                           "division top a table on one good week"),
    }


# --------------------------------------------------------------------------- 6. org health
def build_health(live_state, avail, forecasts, scorecard):
    inj = live_state["injuries"]
    designations = defaultdict(int)
    for r in parse_injuries():
        designations[r["status"] or "(blank)"] += 1
    practice = defaultdict(int)
    for r in parse_injuries():
        practice[r["practice"] or "(blank)"] += 1

    with open(os.path.join(DATA, "fair_lines.csv"), encoding="utf-8", newline="") as fh:
        fair = list(csv.DictReader(fh))
    total_2026 = [f for f in fair if f["season"] == "2026"]
    with_fair = [f for f in total_2026 if f["side_fair_spread_away"] != ""]
    with_market = [f for f in total_2026 if f["side_market_spread_away"] != ""]
    with_total_fair = [f for f in total_2026 if f["total_fair"] != ""]

    n_inj = inj["rows"]
    designation_rows = n_inj - designations["(blank)"]
    return {
        "availability": {
            "report_rows": n_inj,
            "clubs_on_report": inj["clubs"],
            "clubs_total": 32,
            "blank_game_status": designations["(blank)"],
            "out": designations["Out"],
            "doubtful": designations["Doubtful"],
            "questionable": designations["Questionable"],
            "designated_coverage": round(designation_rows / n_inj, 4) if n_inj else None,
            "practice": dict(sorted(practice.items())),
            "added_since_1114": len(inj["added_vs_2026_11_14"]),
            "moved_fields_since_1114": len(inj["field_moves"]),
            "invented_rows": len(inj["missing_vs_2026_11_14"]),
        },
        "depth": {
            "clubs_with_chart": avail["clubs_with_chart"],
            "clubs_total": 32,
            "clubs_missing": avail["clubs_missing_chart"],
            "chart_slots": avail["slots"],
            "injured_matched": avail["injured_matched_to_slot"],
            "injured_total": avail["injured_total_on_report"],
            "match_rate": round(avail["injured_matched_to_slot"] / avail["injured_total_on_report"], 4)
                          if avail["injured_total_on_report"] else None,
            "designated": avail["designated"],
            "replacement_named": avail["designated_with_named_replacement"],
            "replacement_rate": round(avail["designated_with_named_replacement"] / avail["designated"], 4)
                                if avail["designated"] else None,
        },
        "model_inputs": {
            "games_2026": len(total_2026),
            "with_fair_side": len(with_fair),
            "with_market_side": len(with_market),
            "with_fair_total": len(with_total_fair),
            "market_coverage": round(len(with_market) / len(total_2026), 4) if total_2026 else None,
            "market_provenance": total_2026[0]["market_provenance"] if total_2026 else "",
            "scored_forecasts": len(forecasts),
            "weeks_scored": len({f["week"] for f in forecasts}),
        },
        "price": {
            "snapshots": len(load_tsv("price_snapshots.tsv")),
            "policy_decided": False,
            "policy_note": ("no official NFL price source exists; every market price in this "
                            "repository is third-party or absent"),
        },
        "leaderboard": {
            "entries": len(scorecard["registry"]),
            "qualified": scorecard["qualified_count"],
            "controls": 2,
        },
    }


# --------------------------------------------------------------------------- main
def write(name, obj):
    p = os.path.join(DATA, name)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print("wrote %-34s %7d bytes" % (name, os.path.getsize(p)))


def main():
    live_state = build_live_state()
    avail = build_availability(live_state)
    forecasts = build_forecasts()
    scorecard = build_scorecard(forecasts, avail)
    health = build_health(live_state, avail, forecasts, scorecard)

    write("live_state_d5.json", live_state)
    write("availability_d5.json", avail)
    write("scorecard_d5.json", scorecard)
    write("org_health_d5.json", health)

    # forecast ledger as csv + json
    p = os.path.join(DATA, "forecast_ledger_d5.csv")
    cols = list(forecasts[0].keys()) if forecasts else []
    with open(p, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in forecasts:
            w.writerow(r)
    print("wrote forecast_ledger_d5.csv              %7d bytes" % os.path.getsize(p))
    write("forecast_ledger_d5.json", {
        "rows": forecasts,
        "n": len(forecasts),
        "note": ("model probabilities were recorded by an earlier session as model output, "
                 "not as a pre-registered forecast; they are scored here ex post and are "
                 "labelled IN-SAMPLE-CAPABLE, not prospective"),
    })

    print()
    print("live: %d standings rows, %d stale vs the 2026-11-16 read, %d stale vs the rendered site"
          % (len(live_state["standings"]), len(live_state["stale_vs_older"]),
             len(live_state["stale_vs_base"])))
    print("injuries: %d rows / %d clubs, +%d added, %d fields moved, %d invented"
          % (live_state["injuries"]["rows"], live_state["injuries"]["clubs"],
             len(live_state["injuries"]["added_vs_2026_11_14"]),
             len(live_state["injuries"]["field_moves"]),
             len(live_state["injuries"]["missing_vs_2026_11_14"])))
    print("availability: %d designated, %d with a named replacement, %d/%d clubs charted"
          % (avail["designated"], avail["designated_with_named_replacement"],
             avail["clubs_with_chart"], 32))
    print("scorecard: %d entries, %d qualified, sample bar %d"
          % (len(scorecard["registry"]), scorecard["qualified_count"],
             scorecard["sample_bars"]["singles"]))
    if scorecard["measured"]:
        m = scorecard["measured"]
        print("measured Elo: n=%d BSS=%.4f lo=%s hi=%s"
              % (m["n"], m["bss"], m.get("lo"), m.get("hi")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
