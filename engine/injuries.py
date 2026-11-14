"""Availability: the official report as an object, the diff as the signal, and the
Next-Man-Up deficiency index as a *range*, because a point estimate on top of an
unfitted P(play) model is theatre.

The module never invents a probability. `GAME_STATUSES` carries the league's
qualitative definitions verbatim and no number; anything that needs a number raises a
`NeedsEstimate` error rather than falling back to folklore, so a caller cannot quietly
ship the 50%-means-Questionable myth that this whole project exists to avoid.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

# --- verified vocabulary -----------------------------------------------------
# Practice participation values and their definitions come from the league's own
# injury-report policy revision (data/sources.json SRC-002). The game-status
# definitions are quoted there as qualitative on purpose: the league removed
# 'Probable' because ~95% of such players played, and attaches no percentage to
# 'Questionable' or 'Doubtful'.
PRACTICE_STATUSES = ("Full Participation in Practice",
                     "Limited Participation in Practice",
                     "Did Not Participate In Practice")

GAME_STATUSES = {
    "Questionable": "it is uncertain as to whether the player will play in the game",
    "Doubtful": "it is unlikely the player will participate",
    "Out": "the player will not play",
    None: "not listed in the Game Status Report, which under the policy means certain to play",
}

# Our classification, not the league's: which unit group a position feeds. Kept as a
# flat map so it is reviewable, and deliberately conservative (nothing is scored on an
# unmapped position).
POSITION_GROUPS = {
    "QB": ("offence", "qb"),
    "RB": ("offence", "backfield"),
    "FB": ("offence", "backfield"),
    "WR": ("offence", "receiver"),
    "TE": ("offence", "tight_end"),
    "T": ("offence", "offensive_line"),
    "G": ("offence", "offensive_line"),
    "C": ("offence", "offensive_line"),
    "OT": ("offence", "offensive_line"),
    "OG": ("offence", "offensive_line"),
    "OL": ("offence", "offensive_line"),
    "DE": ("defence", "edge_rush"),
    "DT": ("defence", "interior_rush"),
    "NT": ("defence", "interior_rush"),
    "DL": ("defence", "front_seven"),
    "LB": ("defence", "linebacker"),
    "OLB": ("defence", "edge_rush"),
    "ILB": ("defence", "linebacker"),
    "MLB": ("defence", "linebacker"),
    "CB": ("defence", "outside_cb"),
    "S": ("defence", "safety"),
    "FS": ("defence", "safety"),
    "SS": ("defence", "safety"),
    "DB": ("defence", "secondary"),
    "K": ("special_teams", "kicking"),
    "P": ("special_teams", "punting"),
    "LS": ("special_teams", "long_snap"),
}


class NeedsEstimate(RuntimeError):
    """Raised when a call demands a number that must be fitted from data we do not hold."""


# --- snapshot handling -------------------------------------------------------


def load_rows(snapshot: dict) -> list[dict]:
    """Normalise a captured snapshot into rows with unit classification applied."""
    out = []
    for r in snapshot.get("rows", []):
        pos = (r.get("pos") or "").strip().upper()
        side, group = POSITION_GROUPS.get(pos, (None, None))
        out.append({
            "game": r.get("game"),
            "club": r.get("team"),
            "player": r.get("player"),
            "pos": pos or None,
            "injury": r.get("injury") or None,          # blank in source -> None, never "healthy"
            "practice": r.get("practice") or None,
            "game_status": r.get("game_status") or None,
            "side": side,
            "group": group,
            "captured": snapshot.get("updated"),
            "source_url": snapshot.get("source_url"),
        })
    return out


def is_unavailable(row: dict) -> bool:
    """Confirmed absence: the official Out designation only.

    Doubtful is deliberately NOT treated as absent and Questionable is not treated as
    anything: converting a tag into an availability probability is the estimator's job,
    not this function's.
    """
    return (row.get("game_status") or "").strip().lower() == "out"


def at_risk(row: dict) -> bool:
    return (row.get("game_status") or "").strip().lower() in ("questionable", "doubtful")


def certain_to_play(row: dict) -> bool:
    """Absence from the Game Status Report after being reported in practice (SRC-002).

    Only meaningful when the capture is complete for that club: on a partial capture a
    missing designation cannot be distinguished from a row we never fetched, which is
    why `rows_for_club` requires an explicit completeness flag.
    """
    return row.get("game_status") in (None, "") and row.get("practice") not in (None, "")


def trajectory(rows: Sequence[dict]) -> dict[str, list[str]]:
    """Per-player ordered practice trail across whatever days we captured."""
    trail: dict[str, list] = defaultdict(list)
    for r in sorted(rows, key=lambda x: (x.get("captured") or "", x.get("game") or "")):
        if r.get("practice"):
            trail[f"{r.get('club')}::{r.get('player')}"].append(
                {"game": r.get("game"), "captured": r.get("captured"), "practice": r["practice"],
                 "game_status": r.get("game_status")})
    return dict(trail)


def diff_snapshots(old: dict, new: dict) -> list[dict]:
    """Every status change between two captures, including changes to 'not listed'.

    The diff, not the level, is the tradeable object: the market has already seen the
    Friday report, but it has not seen the move from Questionable to Out.
    """
    def key(r):
        return (r.get("game"), r.get("team"), r.get("player"))

    o = {key(r): r for r in load_rows(old)}
    n = {key(r): r for r in load_rows(new)}
    changes = []
    for k in sorted(set(o) | set(n), key=lambda t: tuple(str(x) for x in t)):
        a, b = o.get(k), n.get(k)
        if a is None:
            changes.append({"change": "ADDED", "key": k, "after": b})
            continue
        if b is None:
            changes.append({"change": "REMOVED", "key": k, "before": a})
            continue
        for field in ("practice", "game_status", "injury"):
            if (a.get(field) or None) != (b.get(field) or None):
                changes.append({"change": "STATUS", "key": k, "field": field,
                                "before": a.get(field), "after": b.get(field),
                                "direction": "worse" if _worsened(field, a.get(field), b.get(field))
                                             else "better"})
    return changes


_ORDER = {"Full Participation in Practice": 2, "Limited Participation in Practice": 1,
          "Did Not Participate In Practice": 0}
_GS_ORDER = {None: 3, "Questionable": 2, "Doubtful": 1, "Out": 0}


def _worsened(field: str, before, after) -> bool:
    if field == "practice":
        return _ORDER.get(after, 99) < _ORDER.get(before, 99)
    if field == "game_status":
        return _GS_ORDER.get(after if after else None, 99) < _GS_ORDER.get(before if before else None, 99)
    return False


# --- Next-Man-Up deficiency --------------------------------------------------


def deficiency_counts(rows: Sequence[dict]) -> dict:
    """Officially-grounded counts only: no estimation, therefore nothing to dispute."""
    per_club: dict = defaultdict(lambda: defaultdict(lambda: {"out": set(), "at_risk": set(),
                                                              "certain": set(), "all": set()}))
    for r in rows:
        if not r.get("club") or not r.get("group"):
            continue
        cell = per_club[r["club"]][f"{r['side']}::{r['group']}"]
        cell["all"].add(r["player"])
        if is_unavailable(r):
            cell["out"].add(r["player"])
        elif at_risk(r):
            cell["at_risk"].add(r["player"])
        elif certain_to_play(r):
            cell["certain"].add(r["player"])
    return {club: {grp: {"out": sorted(v["out"]), "at_risk": sorted(v["at_risk"]),
                             "certain_unlisted": sorted(v["certain"]), "reported": len(v["all"])}
                   for grp, v in groups.items()}
            for club, groups in per_club.items()}


def nmu_index(rows: Sequence[dict], snap_share: dict | None = None,
              quality_gap: dict | None = None) -> dict:
    """Next-Man-Up deficiency, in points-per-game-equivalent.

    deficiency(group) = sum over absent players of snap_share x quality_gap.

    Both arguments are fitted quantities. Passing None for either returns the count-only
    shadow of the index, clearly labelled, so the pipeline can run while the estimation
    gap (GAP-04, GAP-05) is open without pretending it has been closed. Passing an
    unlabelled guess is what this guard exists to stop.
    """
    counts = deficiency_counts(rows)
    if snap_share is None or quality_gap is None:
        return {"mode": "COUNT_ONLY_UNWEIGHTED", "counts": counts,
                "unavailable_value": "snap_share and quality_gap are not estimated yet "
                                      "(GAP-04/GAP-05); any points figure here would be invented",
                "index": None}
    index = {}
    for club, groups in counts.items():
        for grp, v in groups.items():
            score = 0.0
            for player in v["out"]:
                share = snap_share.get((club, player))
                gap = quality_gap.get((club, grp))
                if share is None or gap is None:
                    raise NeedsEstimate(
                        f"snap_share/quality_gap missing for {club} {player} ({grp}); "
                        "refusing to substitute a default")
                score += share * gap
            index.setdefault(club, {})[grp] = round(score, 4)
    return {"mode": "WEIGHTED", "counts": counts, "index": index}


def scenario_range(rows: Sequence[dict]) -> dict:
    """Best / expected / worst availability scenarios per club.

    The point estimate is reported as a range because the input uncertainty (designation
    semantics) is larger than the model's own precision on most weeks. A single number
    here would imply a calibration the injury report cannot support.
    """
    per_club: dict = defaultdict(lambda: {"out": 0, "risk": 0, "players": set()})
    for r in rows:
        if not r.get("club"):
            continue
        c = per_club[r["club"]]
        c["players"].add(r["player"])
        if is_unavailable(r):
            c["out"] += 1
        elif at_risk(r):
            c["risk"] += 1
    out = {}
    for club, v in per_club.items():
        has_risk = v["risk"] > 0
        out[club] = {
            "confirmed_out": v["out"],
            "at_risk": v["risk"],
            "reported_players": len(v["players"]),
            "best_case_out": v["out"],                      # every at-risk player plays
            "worst_case_out": v["out"] + v["risk"],         # every at-risk player sits
            "expected_case_out": v["out"] if not has_risk else None,
            "expected_case_note": (None if not has_risk else
                                   "requires the fitted P(play) table (Q-06 / GAP-02); "
                                   "refusing to assume a designation means a probability"),
        }
    return out
