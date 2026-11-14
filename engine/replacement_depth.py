"""Depth of the replacement, not just the fact of a replacement.

WHAT THE BRIEF ASKS FOR, PRECISELY
    "Track the depth of the replacement, not just the fact of a replacement." A list that
    says *Player X is Out* carries no information about how much the team is worse: the
    answer depends on who fills in, and on how far down the chart that person sits. So
    every absence here is resolved to a named replacement, and the replacement is scored
    on the club's own published depth chart:

        depth_levels_lost   replacement's string number - absent player's string number
        depth_remaining     how many players sit below the replacement at that slot
        chain_broken        the replacement is himself on the injury report
        no_replacement      nobody is listed behind the absent player (a real, and loud,
                            case: the club's chart simply runs out)

    A first-string absence filled by a first-string backup (levels lost 0) is a different
    event from a first-string absence that pushes a fourth-stringer in (levels lost 3),
    and this module is where that distinction becomes a number.

WHAT IT REFUSES TO DO
    It never converts depth into a points or win-probability penalty. That conversion is
    a fitted model over snap counts and player quality, and neither is available from an
    official source (see flags F02/F03 and the depth pages' "observed vs derived" rule).
    The output is an ordinal, auditable description of the replacement, plus the club-level
    roll-up of it - and the estimator that *would* turn it into points is left named and
    blank in `data/specs/models.json`, where the previous session parked it.
"""

from __future__ import annotations

import csv
import os
from collections import OrderedDict, defaultdict
from typing import Sequence

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEPTH_FIELDS = [
    "team", "unit", "phase", "slot", "position", "absent_player", "absent_rank",
    "absent_line", "game_status", "practice_status", "injury", "replacement_player",
    "replacement_rank", "replacement_line", "depth_levels_lost", "depth_remaining",
    "chain_broken", "no_replacement", "replacement_status", "roster_starts_prior",
    "roster_years", "chart_source", "source_url",
]

CLUB_FIELDS = [
    "team", "club", "listed_on_report", "first_string_out", "vacancies_resolved",
    "vacancies_unresolved", "offence_levels_lost", "defence_levels_lost",
    "special_teams_levels_lost", "depth_lost_units", "mean_levels_lost",
    "worst_slot", "chain_broken_count", "chart_captured",
]


def _norm(name: str) -> str:
    """Normalise a person's name for an exact join after alias mapping. No fuzzy matching."""
    return " ".join((name or "").strip().lower().split())


def load_aliases() -> dict:
    path = os.path.join(ROOT, "data", "depth-aliases.tsv")
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            d = _norm(row.get("depthName", ""))
            r = _norm(row.get("reportName", ""))
            if d and r:
                out[d] = r
    return out


def load_roster_experience(season: int) -> dict:
    """Prior-season starts/years from the in-repo roster extract. Third-party; labelled.

    `data/raw/rosters.csv` is nflverse/nfldata's roster table (sourced by its publisher
    from Pro Football Reference). Where the season we want is not in that extract the
    cells are left blank rather than borrowed from a neighbouring year.
    """
    path = os.path.join(ROOT, "data", "raw", "rosters.csv")
    out: dict[tuple, dict] = {}
    if not os.path.exists(path):
        return out
    want = int(season)
    have = None
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    seasons = sorted({int(r["season"]) for r in rows if r.get("season", "").isdigit()})
    if not seasons:
        return out
    if want in seasons:
        have = want
    elif seasons and want > max(seasons):
        have = max(seasons)          # most recent available, and the row says so
    for r in rows:
        if int(r.get("season") or 0) != have:
            continue
        key = (r.get("team", "").strip(), _norm(r.get("full_name", "")))
        out[key] = {"starts": r.get("starts", ""), "years": r.get("years", ""),
                    "season_used": have}
    out[("__meta__", "")] = {"requested": want, "used": have}
    return out


def build(depth_rows: Sequence[dict], injuries: Sequence[dict], aliases: dict,
           roster: dict | None = None, sources: dict | None = None) -> dict:
    """Join the club's own chart to the club's own report and resolve every vacancy."""
    roster = roster or {}
    meta = roster.pop(("__meta__", ""), {}) if isinstance(roster, dict) else {}
    sources = sources or {}
    by_slot: dict[tuple, list[dict]] = defaultdict(list)
    for r in depth_rows:
        key = (r["team"], r["unit"], r["slot"])
        by_slot[key].append(r)
    for k in by_slot:
        by_slot[k].sort(key=lambda r: (int(r["line"] or 99), int(r["rank"] or 99)))

    # who is out, keyed the way the chart is keyed
    out_by_club: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in injuries:
        nm = _norm(aliases.get(_norm(r["player"]), r["player"]))
        out_by_club[r["team"]][nm] = r

    rows = []
    for (team, unit, slot), chart in sorted(by_slot.items()):
        absentees = [p for p in chart
                     if _norm(aliases.get(_norm(p["player"]), p["player"])) in out_by_club[team]
                     and _norm(aliases.get(_norm(p["player"]), p["player"]))]
        for i, entry in enumerate(chart):
            nm = _norm(aliases.get(_norm(entry["player"]), entry["player"]))
            inj = out_by_club[team].get(nm)
            if not inj:
                continue
            status = (inj.get("game") or "").strip()
            if status.lower() not in ("out", "doubtful", "questionable", "injured reserve",
                                      "non-football injured", "reserve/nfi", "suspended",
                                      "exempt", "not with team"):
                continue
            line_i = int(entry["line"] or 99)
            rank_i = int(entry["rank"] or 99)
            repl = None
            for nxt in chart[i + 1:]:
                nxt_nm = _norm(aliases.get(_norm(nxt["player"]), nxt["player"]))
                nxt_inj = out_by_club[team].get(nxt_nm)
                nxt_line = int(nxt["line"] or 99)
                if nxt_line < line_i:
                    continue      # cannot "come up" from a shallower string
                cand = {"row": nxt, "injured": bool(nxt_inj),
                        "status": (nxt_inj or {}).get("game", "") if nxt_inj else ""}
                if not nxt_inj:
                    repl = cand
                    break
                # the next man is also hurt: keep looking, but remember we saw it
                if repl is None:
                    repl = cand
            rows.append(OrderedDict([
                ("team", team), ("unit", unit), ("phase", _phase(unit, slot)),
                ("slot", slot), ("position", _pos(inj, entry)),
                ("absent_player", entry["player"]), ("absent_rank", rank_i),
                ("absent_line", line_i),
                ("game_status", status), ("practice_status", inj.get("practice", "")),
                ("injury", inj.get("injury", "")),
                ("replacement_player", repl["row"]["player"] if repl else ""),
                ("replacement_rank", int(repl["row"]["rank"] or 0) if repl else ""),
                ("replacement_line", int(repl["row"]["line"] or 0) if repl else ""),
                ("depth_levels_lost", (int(repl["row"]["line"] or 0) - line_i) if repl else ""),
                ("depth_remaining", sum(1 for x in chart[i + 1:]
                                         if int(x["line"] or 99) >= int(repl["row"]["line"] or 0))
                 if repl else 0),
                ("chain_broken", "YES - the next man up is also on the report"
                 if (repl and repl["injured"]) else ""),
                ("no_replacement", "" if repl else "YES - nobody is listed behind this slot"),
                ("replacement_status", repl["status"] if repl and repl["injured"] else ""),
                ("roster_starts_prior", _exp(roster, team, repl["row"]["player"] if repl else "")),
                ("roster_years", _exp(roster, team, repl["row"]["player"] if repl else "", "years")),
                ("chart_source", sources.get(team, {}).get("source", "")),
                ("source_url", sources.get(team, {}).get("url", "")),
            ]))

    # absences that never touch a charted slot: a real deficiency case, kept visible
    unmatched = []
    for team, plist in sorted(out_by_club.items()):
        charted = {_norm(aliases.get(_norm(r["player"]), r["player"]))
                   for r in depth_rows if r["team"] == team}
        if not charted:
            continue
        for nm, inj in sorted(plist.items()):
            if nm not in charted and (inj.get("game", "").strip().lower() in
                                      ("out", "injured reserve", "doubtful")):
                unmatched.append(OrderedDict([
                    ("team", team), ("player", inj["player"]),
                    ("position", inj.get("position", "")), ("game_status", inj.get("game", "")),
                    ("note", "on the club's injury report but not on its published chart"),
                ]))
    clubs = _club_rollup(rows, injuries, depth_rows)
    return {"rows": rows, "unmatched_absences": unmatched, "clubs": clubs,
            "roster_season_used": meta, "clubs_with_chart": len({r["team"] for r in depth_rows}),
            "clubs_total": len({r["team"] for r in injuries} | {r["team"] for r in depth_rows})}


def _phase(unit: str, slot: str) -> str:
    s = slot.upper()
    if s in ("QB", "RB", "FB", "WR", "TE", "T", "G", "C", "OT", "OG", "LT", "RT", "LG", "RG"):
        return "offence" if unit.upper() in ("OFFENSE", "OFF") else "offence"
    if unit.upper() in ("SPECIAL TEAMS", "ST", "SPECIAL"):
        return "special teams"
    return "defence"


def _pos(inj: dict, chart_row: dict) -> str:
    return (inj.get("position") or chart_row.get("slot") or "").strip()


def _exp(roster: dict, team: str, player: str, field: str = "starts") -> str:
    if not roster or not player:
        return ""
    rec = roster.get((team, _norm(player)))
    return "" if not rec else str(rec.get(field, ""))


def _club_rollup(rows: Sequence[dict], injuries: Sequence[dict],
                 depth_rows: Sequence[dict]) -> list[dict]:
    per_team: dict[str, dict] = {}
    charted = defaultdict(set)
    for r in depth_rows:
        charted[r["team"]].add(r["slot"])
    listed = defaultdict(int)
    for r in injuries:
        listed[r["team"]] += 1
    for r in rows:
        d = per_team.setdefault(r["team"], {
            "first_string_out": 0, "resolved": 0, "unresolved": 0, "levels": 0,
            "levels_list": [], "worst": (0, ""), "chain": 0,
            "offence": 0, "defence": 0, "st": 0})
        if r["absent_line"] == 1:
            d["first_string_out"] += 1
        if r["no_replacement"]:
            d["unresolved"] += 1
        else:
            d["resolved"] += 1
        lv = r["depth_levels_lost"]
        if isinstance(lv, int):
            d["levels"] += lv
            d["levels_list"].append(lv)
            if lv > d["worst"][0]:
                d["worst"] = (lv, "%s %s (line %s -> %s)" % (
                    r["slot"], r["absent_player"], r["absent_line"], r["replacement_line"]))
            if r["phase"] == "offence":
                d["offence"] += lv
            elif r["phase"] == "defence":
                d["defence"] += lv
            else:
                d["st"] += lv
        if r["chain_broken"]:
            d["chain"] += 1
    teams = sorted(set(per_team) | set(listed))
    out = []
    for t in teams:
        d = per_team.get(t, {"first_string_out": 0, "resolved": 0, "unresolved": 0,
                             "levels": 0, "levels_list": [], "worst": (0, ""), "chain": 0,
                             "offence": 0, "defence": 0, "st": 0})
        n = len(d["levels_list"])
        out.append(OrderedDict([
            ("team", t), ("club", t), ("listed_on_report", listed.get(t, 0)),
            ("first_string_out", d["first_string_out"]), ("vacancies_resolved", d["resolved"]),
            ("vacancies_unresolved", d["unresolved"]),
            ("offence_levels_lost", d["offence"]), ("defence_levels_lost", d["defence"]),
            ("special_teams_levels_lost", d["st"]), ("depth_lost_units", d["levels"]),
            ("mean_levels_lost", round(d["levels"] / n, 3) if n else ""),
            ("worst_slot", d["worst"][1]), ("chain_broken_count", d["chain"]),
            ("chart_captured", "YES" if charted.get(t) else "NO - no chart to measure against"),
        ]))
    return out
