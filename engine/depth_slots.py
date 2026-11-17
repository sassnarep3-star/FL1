"""
Depth slots as GROUPS, not as a single "starter".

WHAT THE BRIEF ASKS FOR, PRECISELY
    "149 club/unit/position slots list more than one rank-1 player ... Treating
    column 1 as 'the starter' would fabricate a starter the club never named."

    A club's own depth chart does not always name one starter per slot. It
    sometimes names two players at the same string ("Jack Endries & Cam Grandy"),
    and it sometimes leaves a string with no name at all. Both are ordinary
    published facts, and both are invisible if the chart is read as a flat list of
    "starters and backups".

    This module therefore models a **slot group**:

        slot group = (club, unit, slot label, occurrence of that label)

    The occurrence matters because several clubs publish the same label more than
    once (two "DL" lines, two "CB" lines, two "S" lines). Those are different
    slots on the real chart, and merging them lets a second-string player on one
    line be mistaken for the backup to the starter on the other.

WHAT A SLOT GROUP KNOWS
    state              "single" | "shared" | "empty" | "unnamed-first-string"
    first_string       the names the club published AT THE FIRST STRING
    ladder             every published name, in the club's own order
    starter_named      "yes" | "no - the club published no name at the first string"
                                   | "ambiguous - the club published N names"

WHAT IT REFUSES TO DO
    It never picks one of several first-string names and calls it "the starter".
    For a shared slot it returns *all* of them and marks the slot ambiguous.
    For an empty first string it returns no name at all and says so, instead of
    promoting the second string into the first.

    It also never crosses a published line to find a replacement. The previous
    implementation grouped a club's chart by (club, unit, slot label) and walked
    the flattened list, so a name on the club's *second* "S" line could be
    offered as the replacement for an absence on its *first* "S" line. Those are
    different positions on a real roster. The walk here stays inside the group.

MEASURED, NOT ASSUMED
    The brief quotes "149" shared slots. That number is **not** reproduced by the
    committed official capture: `data/depth.tsv` (the Week 10 club depth-chart
    capture) contains a smaller number of shared first strings, and the raw
    capture behind it (`raw/depth-charts-week10-2026.tsv`) shows every shared
    cell holds exactly two names. The measured number is what this module
    publishes, and the discrepancy is recorded as a flag rather than smoothed
    over. See `docs/` and the Flagged for Review page.
"""

from __future__ import annotations

import csv
import os
from collections import OrderedDict
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEPTH_SCHEMA = ["team", "unit", "slot", "player", "rank", "line", "note"]
KC_SCHEMA = ["unit", "slot", "player", "rank"]

SLOT_FIELDS = [
    "slot_id", "team", "club", "unit", "slot", "line", "state",
    "n_at_first_string", "first_string_names", "first_string_blank",
    "starter_named_by_club",
    "strings_populated", "n_strings_populated", "ladder", "n_names",
    "note", "chart_source", "source_url", "chart_date",
]


def _norm(value: str) -> str:
    return " ".join((value or "").strip().split())


def load_depth_rows(root: str = ROOT) -> list:
    """Load the committed official depth capture: 30 clubs plus Kansas City."""
    rows = []
    path = os.path.join(root, "data", "depth.tsv")
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.reader(fh, delimiter="\t"):
            if len(r) < 6:
                continue
            rows.append({
                "team": _norm(r[0]), "unit": _norm(r[1]), "slot": _norm(r[2]),
                "player": _norm(r[3]), "rank": (r[4] or "").strip(),
                "line": (r[5] or "1").strip() or "1",
                "note": (r[6] if len(r) > 6 else "").strip(),
            })
    # Kansas City is captured in its own file (a flat chart with no line column
    # and slot labels that already carry their own occurrence, e.g. "WR1").
    kc_path = os.path.join(root, "data", "depth-kc.tsv")
    if os.path.exists(kc_path):
        with open(kc_path, encoding="utf-8", newline="") as fh:
            for r in csv.reader(fh, delimiter="\t"):
                if len(r) < 4:
                    continue
                rows.append({
                    "team": "KC", "unit": _norm(r[0]), "slot": _norm(r[1]),
                    "player": _norm(r[2]), "rank": (r[3] or "").strip(),
                    "line": "1", "note": "",
                })
    return rows


def load_depth_sources(root: str = ROOT) -> dict:
    out = {}
    path = os.path.join(root, "data", "depth-sources.tsv")
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.reader(fh, delimiter="\t"):
            if len(r) < 3:
                continue
            out[_norm(r[0])] = {
                "source": r[1].strip(),
                "url": r[2].strip(),
                "chart_date": (r[3].strip() if len(r) > 3 else ""),
                "note": (r[4].strip() if len(r) > 4 else ""),
            }
    return out


@dataclass
class SlotGroup:
    """One published slot on one club's own chart."""

    team: str
    unit: str
    slot: str
    line: int
    names: list = field(default_factory=list)   # [{"player","rank","note"}]

    @property
    def slot_id(self) -> str:
        return f"{self.team}-{self.unit}-{self.slot}-{self.line}"

    @property
    def first_string(self) -> list:
        """The NAMED players the club published at the first string.

        A blank first string is a published fact in its own right ("the club
        published this slot with no name in it"), so it is reported separately
        rather than being counted as a name.
        """
        return [n for n in self.names
                if str(n["rank"]) == "1" and n["player"]]

    @property
    def first_string_blank(self) -> bool:
        """True when the club published the slot but left the first string empty."""
        return any(str(n["rank"]) == "1" and not n["player"] for n in self.names)

    @property
    def state(self) -> str:
        first = self.first_string
        if len(first) == 1:
            return "single"
        if len(first) > 1:
            return "shared"
        return "empty"

    @property
    def starter_named(self) -> str:
        first = self.first_string
        if len(first) == 1:
            return "yes"
        if len(first) > 1:
            return (f"ambiguous - the club published {len(first)} names at the "
                    f"first string")
        return "no - the club published no name at the first string"

    @property
    def ladder(self) -> list:
        """Every published name in the club's own order."""
        return list(self.names)

    def strings_populated(self) -> list:
        out = []
        for n in self.names:
            r = str(n["rank"])
            if r not in out:
                out.append(r)
        return out

    def named_at(self, rank: str) -> list:
        return [n for n in self.names if str(n["rank"]) == str(rank)]


def build_groups(rows: list) -> "OrderedDict[tuple, SlotGroup]":
    """Group the flat capture into slot groups, preserving the club's order."""
    groups: "OrderedDict[tuple, SlotGroup]" = OrderedDict()
    for r in rows:
        key = (r["team"], r["unit"], r["slot"], r["line"])
        g = groups.get(key)
        if g is None:
            g = SlotGroup(team=r["team"], unit=r["unit"], slot=r["slot"],
                          line=int(r["line"] or 1))
            groups[key] = g
        g.names.append({"player": r["player"], "rank": r["rank"], "note": r["note"]})
    # The club's own order is the order the capture lists it in; the sort is
    # stable, so the published order inside a string is preserved.
    for g in groups.values():
        g.names.sort(key=lambda n: int(n["rank"] or 99))
    return groups


def publishable_rows(groups: "OrderedDict[tuple, SlotGroup]", teams: dict,
                     sources: dict) -> list:
    """One row per slot group, ready to be written to data/depth_slots.tsv."""
    out = []
    for key, g in groups.items():
        src = sources.get(g.team, {})
        first = g.first_string
        ladder = "; ".join(
            f"{n['rank']}: {n['player']}" + (" (co-starter)" if n.get("note") else "")
            for n in g.names if n["player"])
        out.append({
            "slot_id": g.slot_id,
            "team": g.team,
            "club": teams.get(g.team, g.team),
            "unit": g.unit,
            "slot": g.slot,
            "line": g.line,
            "state": g.state,
            "n_at_first_string": len(first),
            "first_string_names": "; ".join(n["player"] for n in first),
            "first_string_blank": "YES - the club published this slot with no name at the first string"
                                  if g.first_string_blank else "",
            "starter_named_by_club": g.starter_named,
            "strings_populated": ";".join(g.strings_populated()),
            "n_strings_populated": len(g.strings_populated()),
            "ladder": ladder,
            "n_names": len([n for n in g.names if n["player"]]),
            "note": "; ".join(sorted({n["note"] for n in g.names if n.get("note")})),
            "chart_source": src.get("source", ""),
            "source_url": src.get("url", ""),
            "chart_date": src.get("chart_date", ""),
        })
    return out


def write_tsv(path: str, fields: list, rows: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def resolve_replacement(group: SlotGroup, absent_player: str,
                        unavailable: set) -> dict:
    """Find the replacement for an absence, INSIDE the slot group.

    `unavailable` is a set of normalised names the club has ruled out. The walk
    starts at the absent player's position in the group's own ladder and returns
    the first name the club has not ruled out. It never leaves the group: a name
    published on a different line of the same slot label is a different position
    on a real roster and is not a backup.

    Returns a dict with the replacement's name and the number of strings lost.
    `strings_lost` is the difference in *published string*, not in list position:
    a co-starter who steps in has lost nothing (0), while a second string who
    steps in has lost one.
    """
    absent = _norm(absent_player)
    ladder = group.ladder
    idx = None
    for i, n in enumerate(ladder):
        if _norm(n["player"]) == absent:
            idx = i
            break
    if idx is None:
        return {"replacement": "", "strings_lost": "", "replacement_rank": "",
                "reason": "absent player is not in this slot group"}
    absent_rank = int(ladder[idx]["rank"] or 0)
    for n in ladder[idx + 1:]:
        if not n["player"]:
            continue
        if _norm(n["player"]) in unavailable:
            continue
        return {
            "replacement": n["player"],
            "replacement_rank": int(n["rank"] or 0),
            "strings_lost": max(0, int(n["rank"] or 0) - absent_rank),
            "reason": "same slot group, first name the club has not ruled out",
        }
    return {"replacement": "", "strings_lost": "", "replacement_rank": "",
            "reason": "no further name published in this slot group"}


def summarise(groups: "OrderedDict[tuple, SlotGroup]") -> dict:
    counts = {"single": 0, "shared": 0, "empty": 0}
    shared_names = {}
    for g in groups.values():
        counts[g.state] += 1
        if g.state == "shared":
            shared_names[g.slot_id] = [n["player"] for n in g.first_string]
    return {
        "slot_groups": len(groups),
        "single": counts["single"],
        "shared": counts["shared"],
        "empty": counts["empty"],
        "shared_slots": shared_names,
    }
