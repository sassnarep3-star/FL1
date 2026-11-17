"""
The availability graph: who was expected to start, and who actually did.

WHAT THE BRIEF ASKS FOR
    "Build the availability graph as a first-class dataset (who was expected to
    start, who actually did)."

    Until now this repository had two halves that had never been joined: the
    clubs' own published depth charts (what a club said its order would be) and
    the official NFL Game Book (what actually happened). Joining them is what
    turns "player X is out" into "player Y started, and the club's own chart
    puts him at string N".

THE JOIN, AND THE HONEST LIMITS OF IT
    * The club depth charts in this repository were captured for **Week 10 of
      2026**. They are therefore only a valid statement of expectation for
      Week 10 games. For an earlier game they are a *later* document, and using
      them to explain that game would be lookahead. The graph is built for
      Week 10 only, and says so on every row.
    * The club charts are the clubs' own documents. Some clubs print the word
      "unofficial" on them. That is recorded, not hidden.
    * Names are matched on surname plus first initial. "C.Kupp" in the game
      book and "Cooper Kupp" on the chart are the same person; the join is
      exact on that key, and a name that does not join is reported as
      unmatched rather than guessed at.

WHAT IT PRODUCES, PER (GAME, CLUB, PLAYER)
    expectation   what the club's own chart said
    reality       what the official game book says happened
    outcome       one of a small, fixed set of statements
    evidence      the official URL for the game, and the book's own status

THE OUTCOMES, AND WHAT EACH ONE MEANS
    STARTED_AS_CHARTED
        The club's chart named this player at the first string and the player
        started. No absence to explain.
    STARTED_FROM_DEEPER_ON_THE_CHART
        The player started but the club's chart puts them BELOW the first
        string. This is the depth-of-the-replacement case, measured on the
        club's own chart.
    STARTED_NOT_ON_THE_CHART
        The player started and the club's chart does not name them anywhere.
    OUT_INACTIVE
        The chart named this player at the first string and the official game
        book lists them on the "Not Active" list. This is the official inactive
        list, not an inference from the injury report.
    DID_NOT_PLAY
        The chart named this player at the first string and the game book lists
        them under "Did Not Play".
    NOT_ON_THE_GAME_DAY_ROSTER
        The chart named this player at the first string and the game book does
        not list them at all. Whether that means injured reserve, a trade, or a
        release is NOT decided here: the book does not say, so the row says so.
    DID_NOT_START
        The chart named this player at the first string, the book lists them in
        the game (as a substitution), and they did not start.
"""

from __future__ import annotations

import csv
import os
import re
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OUTCOMES = [
    "STARTED_AS_CHARTED",
    "STARTED_FROM_DEEPER_ON_THE_CHART",
    "STARTED_NOT_ON_THE_CHART",
    "OUT_INACTIVE",
    "DID_NOT_PLAY",
    "NOT_ON_THE_GAME_DAY_ROSTER",
    "DID_NOT_START",
]

GRAPH_FIELDS = [
    "game_slug", "game_date", "week", "away_team", "home_team", "club",
    "chart_slot_id", "chart_unit", "chart_slot", "chart_state",
    "chart_rank", "chart_string", "player", "expectation", "reality",
    "outcome", "depth_levels_lost", "gamebook_position", "gamebook_jersey",
    "official_url", "gamebook_url",
]

_NON_ALPHA = re.compile(r"[^a-z]")


def _surname_key(name: str) -> str:
    """Surname + first initial, from either the book's or the chart's form.

    "C.Kupp"            -> "kupp|c"
    "Cooper Kupp"       -> "kupp|c"
    "J.van den Berg"    -> "berg|j"
    "R.Jackson"         -> "jackson|r"
    """
    raw = " ".join((name or "").split())
    if not raw:
        return ""
    if "." in raw:
        parts = [p for p in raw.split(".") if p]
        if len(parts) >= 2:
            initial = parts[0].strip()[:1].lower()
            surname = parts[-1].strip()
            return "%s|%s" % (_NON_ALPHA.sub("", surname.lower()), initial)
        surname = parts[0]
        return _NON_ALPHA.sub("", surname.lower()) + "|"
    words = raw.split()
    if len(words) == 1:
        return _NON_ALPHA.sub("", words[0].lower()) + "|"
    initial = words[0][:1].lower()
    surname = words[-1]
    return "%s|%s" % (_NON_ALPHA.sub("", surname.lower()), initial)


def surname_only(name: str) -> str:
    """The surname alone, used as a secondary match when initials disagree."""
    key = _surname_key(name)
    return key.split("|")[0]


def load_depth_slots(path: str) -> list:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def load_game_players(path: str) -> list:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def load_games(path: str) -> list:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def charted_first_strings(depth_rows: list, team: str) -> list:
    """Every player the club's own chart names at the first string of a slot.

    A slot the club published with two names at the first string yields BOTH:
    the chart does not say which of them starts, so neither is treated as the
    one true starter.
    """
    out = []
    for r in depth_rows:
        if r["team"] != team:
            continue
        if r["state"] == "empty":
            continue
        for name in [n.strip() for n in r["first_string_names"].split(";") if n.strip()]:
            out.append({
                "slot_id": r["slot_id"], "unit": r["unit"], "slot": r["slot"],
                "state": r["state"], "player": name, "rank": "1",
                "string": r["strings_populated"],
                "source_url": r["source_url"], "chart_source": r["chart_source"],
            })
    return out


def charted_depth(depth_rows: list, team: str) -> dict:
    """surname key -> the charted row, with the depth string the player sits at."""
    out = {}
    for r in depth_rows:
        if r["team"] != team:
            continue
        for n in r["ladder"].split("; "):
            if not n.strip():
                continue
            rank, _, player = n.partition(": ")
            player = player.replace(" (co-starter)", "").strip()
            if not player:
                continue
            key = _surname_key(player)
            if key and key not in out:
                out[key] = {"rank": rank.strip(), "player": player,
                            "slot_id": r["slot_id"], "unit": r["unit"],
                            "slot": r["slot"], "state": r["state"],
                            "source_url": r["source_url"]}
    return out


def build(depth_rows: list, game_rows: list, games: list, week: str) -> list:
    """Build the availability graph for one week."""
    games_by_slug = {g["slug"]: g for g in games}
    by_game = defaultdict(lambda: defaultdict(list))
    for p in game_rows:
        by_game[p["slug"]][p["team"]].append(p)

    out = []
    for slug, clubs in sorted(by_game.items()):
        g = games_by_slug.get(slug)
        if not g or str(g.get("week")) != str(week):
            continue
        for club, people in sorted(clubs.items()):
            expected = charted_first_strings(depth_rows, club)
            depth = charted_depth(depth_rows, club)
            starters = [p for p in people if p["status"] == "starter"]
            inactive = {p["player"] for p in people if p["status"] == "inactive"}
            dnp = {p["player"] for p in people if p["status"] == "did_not_play"}
            subs = {p["player"] for p in people if p["status"] == "substitution"}

            expected_keys = OrderedDict()
            for e in expected:
                expected_keys.setdefault(_surname_key(e["player"]), e)

            matched_starters = set()
            rows = []

            # 1. the players the chart named at the first string
            for key, e in expected_keys.items():
                actual = next((s for s in starters
                               if _surname_key(s["player"]) == key), None)
                if actual:
                    matched_starters.add(_surname_key(actual["player"]))
                    outcome = "STARTED_AS_CHARTED"
                    reality = "the game book lists %s as a starter (%s %s)" % (
                        actual["player"], actual["unit"], actual["pos"])
                    levels = ""
                elif any(_surname_key(p) == key for p in inactive):
                    outcome = "OUT_INACTIVE"
                    reality = "the game book lists the player on the Not Active list"
                    levels = ""
                elif any(_surname_key(p) == key for p in dnp):
                    outcome = "DID_NOT_PLAY"
                    reality = "the game book lists the player under Did Not Play"
                    levels = ""
                elif any(_surname_key(p) == key for p in subs):
                    outcome = "DID_NOT_START"
                    reality = "the game book lists the player as a substitution"
                    levels = ""
                else:
                    outcome = "NOT_ON_THE_GAME_DAY_ROSTER"
                    reality = ("the game book does not list the player at all; "
                               "the book does not say why")
                    levels = ""
                rows.append({
                    "game_slug": slug, "game_date": g["game_date"],
                    "week": g["week"], "away_team": g["away_team"],
                    "home_team": g["home_team"], "club": club,
                    "chart_slot_id": e["slot_id"], "chart_unit": e["unit"],
                    "chart_slot": e["slot"], "chart_state": e["state"],
                    "chart_rank": e["rank"], "chart_string": e["string"],
                    "player": e["player"], "expectation":
                        "the club's own chart names this player at the first string",
                    "reality": reality, "outcome": outcome,
                    "depth_levels_lost": levels,
                    "gamebook_position": actual["pos"] if actual else "",
                    "gamebook_jersey": actual["jersey"] if actual else "",
                    "official_url": g["official_url"],
                    "gamebook_url": g["gamebook_url"],
                })

            # 2. the players who started without being the chart's first string
            for s in starters:
                key = _surname_key(s["player"])
                if key in matched_starters or key in expected_keys:
                    continue
                entry = depth.get(key)
                if entry:
                    outcome = "STARTED_FROM_DEEPER_ON_THE_CHART"
                    expectation = ("the club's own chart does not name this player "
                                   "at the first string")
                    reality = ("the game book lists %s as a starter (%s %s); the "
                               "club's chart puts them at string %s"
                               % (s["player"], s["unit"], s["pos"], entry["rank"]))
                    levels = max(0, int(entry["rank"] or 0) - 1)
                    slot_id, unit, slot, state = (entry["slot_id"], entry["unit"],
                                                  entry["slot"], entry["state"])
                else:
                    outcome = "STARTED_NOT_ON_THE_CHART"
                    expectation = "the club's own chart does not name this player"
                    reality = ("the game book lists %s as a starter (%s %s)"
                               % (s["player"], s["unit"], s["pos"]))
                    levels = ""
                    slot_id, unit, slot, state = "", "", "", ""
                rows.append({
                    "game_slug": slug, "game_date": g["game_date"],
                    "week": g["week"], "away_team": g["away_team"],
                    "home_team": g["home_team"], "club": club,
                    "chart_slot_id": slot_id, "chart_unit": unit,
                    "chart_slot": slot, "chart_state": state,
                    "chart_rank": entry["rank"] if entry else "",
                    "chart_string": "", "player": s["player"],
                    "expectation": expectation, "reality": reality,
                    "outcome": outcome, "depth_levels_lost": levels,
                    "gamebook_position": s["pos"], "gamebook_jersey": s["jersey"],
                    "official_url": g["official_url"],
                    "gamebook_url": g["gamebook_url"],
                })

            out.extend(rows)
    return out


def summarise(rows: list) -> dict:
    counts = {o: 0 for o in OUTCOMES}
    for r in rows:
        counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    return {"rows": len(rows), "by_outcome": counts}


def write_tsv(path: str, fields: list, rows: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
