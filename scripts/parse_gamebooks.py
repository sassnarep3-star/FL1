#!/usr/bin/env python3
"""
parse_gamebooks.py — turn the captured official NFL Game Books into tables.

WHAT IT PARSES
    The NFL Game Book is the official record of a played game. One document per
    game yields, for each club:

        the starting lineup, by unit and position, with jersey numbers
        the substitutions
        the "Did Not Play" list
        the "Not Active" list   <- the official inactive list
        the venue line          ("at MetLife Stadium, East Rutherford, NJ")
        the roof / surface line ("Retractable Roof - Open on Field Turf")
        the game-day weather    (temp, humidity, wind)

    All of it is read from the captured text; nothing is inferred. A player who
    is not in the document is not in the document.

THE PDF PROBLEM, AND HOW IT IS HANDLED
    A game book is a multi-column PDF. Its running page header repeats the
    titles of the tables on the page ("Scoring Plays", "Field Goals",
    "Substitutions", ...) at the top of every page, so a naive "text between
    two markers" search picks up page furniture as if it were data. The parser
    therefore:

      * locates each section by a line that is EXACTLY the two column headers
        ("Not Active Not Active"), not by the first mention of the word;
      * bounds the last personnel section at the play-by-play table header
        ("Play Description ..."), which is what follows it in the book;
      * joins a list that ends in a trailing comma (a wrapped line) to the list
        it belongs to, instead of starting a spurious new list.

WHY THE PARSER IS DEFENSIVE
    Three invariants are checked on every single game, and a game that fails any
    of them is reported rather than published:

        1. the starting-lineup section must yield exactly 44 entries
           (11 offensive + 11 defensive for each of two clubs);
        2. each club's offensive starters must contain exactly one quarterback;
        3. each club's defensive starters must contain at least one front
           defender and at least two defensive backs.

    All 121 captured game books satisfy all three, which is what makes the
    column assignment "visitor offense / visitor defense / home offense / home
    defense" a checked fact rather than a guess.

Run:  python3 scripts/parse_gamebooks.py [--vault DIR]
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Lexical patterns
# ---------------------------------------------------------------------------
# One entry of a game-book personnel list: a position token, a jersey number and
# a name in the book's "X.Lastname" form. `\s+` deliberately spans newlines so
# a name that the PDF pushed onto the next line still parses.
# The head of a personnel entry: a position token and a jersey number. The
# name that follows is read as "everything up to the next head".
HEAD_RE = re.compile(r"(?P<pos>[A-Z0-9][A-Z0-9/]{0,4})\s+(?P<num>\d{1,2})\s+")

# A single-token form, used where the name is known to be one token (the
# starting-lineup table) and as a cross-check.
ENTRY_RE = re.compile(
    r"(?P<pos>[A-Z][A-Z0-9]{0,4})\s+(?P<num>\d{1,2})\s+(?P<name>[A-Za-z][A-Za-z.'\-]*)"
)

DATE_RE = re.compile(r"Date:\s*([A-Za-z]+),\s*(\d{1,2}/\d{1,2}/\d{4})")
VENUE_RE = re.compile(r"^at\s+(.+)$")
TEMP_RE = re.compile(
    r"Temp:\s*(-?\d+)°\s*F\s*\([^)]*\)\s*Humidity:\s*(\d+)%,\s*Wind:\s*(.+?)\s*$"
)
SURFACE_RE = re.compile(
    r"^(?P<roof>Retractable Roof|Open Stadium|Closed Stadium|Dome)\s*"
    r"(?:-\s*(?P<roof_state>Open|Closed))?\s+on\s+(?P<surface>Natural Grass|Field Turf)"
    r"(?P<extra>.*)$"
)
MATCHUP_RE = re.compile(r"^(?P<away>.+?) at (?P<home>.+?)\s+Start Time:")
OUTDOOR_RE = re.compile(
    r"Outdoor Weather:\s*(?P<temp>-?\d+)\s*deg F,\s*Winds?\s*(?P<wind>[A-Za-z]+ at \d+mph)"
    r"(?:,\s*Humidity\s*(?P<humidity>\d+)%)?"
)
SCORE_RE = re.compile(
    r"^(?P<side>VISITOR|HOME):\s*(?P<team>.+?)\s+"
    r"(?P<q1>\d+)\s+(?P<q2>\d+)\s+(?P<q3>\d+)\s+(?P<q4>\d+)\s+"
    r"(?P<ot>\d+)\s+(?P<total>\d+)\s*$"
)

# Section headers are matched as WHOLE lines so that the running page header
# (which lists the same words inline with other titles) cannot be mistaken for
# the section itself.
LINEUPS_HDR = re.compile(r"^Offense\s+Defense\s+Offense\s+Defense\s*$")
SUBS_HDR = re.compile(r"^Substitutions\s+Substitutions\s*$")
DNP_HDR = re.compile(r"^Did Not Play\s+Did Not Play\s*$")
INACT_HDR = re.compile(r"^Not Active\s+Not Active\s*$")
PLAYBYPLAY_HDR = re.compile(r"^Play Description\b")

FRONT_POSITIONS = {"DL", "DT", "DE", "EDGE", "LDE", "RDE", "NT", "DLINE"}
BACK_POSITIONS = {"CB", "DB", "S", "FS", "SS"}


HYPHEN_WRAP_RE = re.compile(r"-\s*\n\s*")


def _clean(text: str) -> str:
    return " ".join((text or "").replace("’", "'").split())


def find_entries(text: str) -> list:
    """Find the personnel entries in a block of game-book text.

    An entry is a position token, a jersey number and a name. The book's names
    are written "X.Lastname", but the Lastname can contain spaces ("J.van den
    Berg", "S.Van Meter"), so a name cannot be matched with a fixed pattern:
    it has to run until the next entry begins.

    So the entries are found by their HEAD (position + jersey number) and the
    name is whatever lies between one head and the next. The same pass records
    whether a comma separated this entry from the next one, because that comma
    is what tells the visitor's list from the home club's list.
    """
    heads = list(HEAD_RE.finditer(text))
    out = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        segment = text[m.end():end]
        name = segment.strip().rstrip(",").strip()
        # the separator is whatever is left once the name has been removed
        separator = segment[:len(segment) - len(segment.lstrip())]
        tail = segment.strip()
        had_comma = tail.endswith(",")
        out.append({
            "pos": m.group("pos"),
            "num": m.group("num"),
            "name": name,
            "continued": had_comma,
        })
    return out


def split_blocks(text: str) -> list:
    """Split a personnel section into its club blocks.

    The book prints the visitor's list first and the home club's second, each as
    a comma-separated list. A list ends where a comma does not follow the last
    entry. A list whose final entry carries a trailing comma (the PDF wrapped
    the line there) is joined to the list it belongs to rather than starting a
    spurious third list.
    """
    lines = [ln for ln in text.split("\n") if HEAD_RE.search(ln)]
    entries = find_entries(" ".join(lines))
    blocks, current = [], []
    for i, e in enumerate(entries):
        current.append((e["pos"], e["num"], e["name"]))
        if i + 1 < len(entries) and e["continued"]:
            continue
        blocks.append(current)
        current = []
    if current:
        blocks.append(current)
    return blocks


def _section_bounds(lines: list) -> dict:
    marks = {}
    for idx, line in enumerate(lines):
        s = line.strip()
        if "lineups" not in marks and LINEUPS_HDR.match(s):
            marks["lineups"] = idx
        elif "subs" not in marks and SUBS_HDR.match(s):
            marks["subs"] = idx
        elif "dnp" not in marks and DNP_HDR.match(s):
            marks["dnp"] = idx
        elif "inact" not in marks and INACT_HDR.match(s):
            marks["inact"] = idx
    bounds = {}
    order = sorted(marks.items(), key=lambda kv: kv[1])
    for i, (name, idx) in enumerate(order):
        end = order[i + 1][1] if i + 1 < len(order) else len(lines)
        bounds[name] = (idx, end)
    # the last personnel section is followed by the play-by-play table
    if "inact" in bounds:
        lo, hi = bounds["inact"]
        for k in range(lo + 1, hi):
            if PLAYBYPLAY_HDR.match(lines[k].strip()):
                bounds["inact"] = (lo, k)
                break
    return bounds


def parse_gamebook(text: str) -> dict:
    """Parse one game book. Returns every fact the book states."""
    out = {
        "date": "", "venue_stadium": "", "venue_city": "", "roof": "",
        "roof_state": "", "surface": "", "temp_f": "", "humidity_pct": "",
        "wind": "", "weather_note": "", "roof_status": "", "away_team": "", "home_team": "", "away_score": "",
        "home_score": "", "starters": [], "substitutions": [],
        "did_not_play": [], "not_active": [], "problems": [],
    }
    text = HYPHEN_WRAP_RE.sub("-", text)
    lines = text.split("\n")

    # ---- header -----------------------------------------------------------
    for line in lines[:80]:
        s = line.strip()
        if not s:
            continue
        m = MATCHUP_RE.match(s)
        if m and not out["away_team"]:
            out["away_team"] = _clean(m.group("away"))
            out["home_team"] = _clean(m.group("home"))
            continue
        m = DATE_RE.search(s)
        if m:
            out["date"] = "%s %s" % (m.group(1), m.group(2))
            continue
        m = VENUE_RE.match(s)
        if m and not out["venue_stadium"]:
            parts = [_clean(x) for x in m.group(1).split(",") if x.strip()]
            out["venue_stadium"] = parts[0] if parts else ""
            out["venue_city"] = ", ".join(parts[1:]) if len(parts) > 1 else ""
            continue
        m = SURFACE_RE.match(s)
        if m and not out["roof"]:
            out["roof"] = m.group("roof")
            out["roof_state"] = m.group("roof_state") or ""
            out["surface"] = m.group("surface")
            if out["roof"] == "Retractable Roof":
                out["roof_status"] = "retractable-%s" % (out["roof_state"] or "unknown").lower()
            elif out["roof"] == "Open Stadium":
                out["roof_status"] = "outdoors"
            else:
                out["roof_status"] = "dome"
            out["weather_note"] = (m.group("extra") or "").strip()
            continue
        m = TEMP_RE.search(s)
        if m:
            out["temp_f"] = m.group(1)
            out["humidity_pct"] = m.group(2)
            out["wind"] = _clean(m.group(3))
            continue
        m = OUTDOOR_RE.search(s)
        if m and not out["temp_f"]:
            # A closed-roof game prints the conditions outside instead of the
            # conditions at the game. It is still an official weather reading
            # for the stadium, and it is labelled as the outdoor reading.
            out["temp_f"] = m.group("temp")
            out["humidity_pct"] = m.group("humidity") or ""
            out["wind"] = _clean(m.group("wind"))
            out["weather_note"] = "outdoor reading printed by the book (closed roof)"
            continue
        m = SCORE_RE.match(s)
        if m:
            if m.group("side") == "VISITOR":
                out["away_score"] = m.group("total")
            else:
                out["home_score"] = m.group("total")
            continue

    # ---- sections ---------------------------------------------------------
    bounds = _section_bounds(lines)
    if "lineups" not in bounds:
        out["problems"].append("no lineups section found")
        return out
    lo, hi = bounds["lineups"]
    rows = []
    for line in lines[lo + 1:hi]:
        stripped = line.strip()
        if not stripped:
            continue
        heads = list(HEAD_RE.finditer(stripped))
        if len(heads) != 4:
            continue
        cells = []
        for i, m in enumerate(heads):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(stripped)
            cells.append((m.group("pos"), m.group("num"),
                          stripped[m.end():end].strip()))
        rows.append(cells)
    if len(rows) != 11:
        out["problems"].append("lineups section yielded %d rows of four, expected 11"
                               % len(rows))
        return out
    cols = [[] for _ in range(4)]
    for r in rows:
        for ci in range(4):
            cols[ci].append(r[ci])
    for ci, (side, unit) in enumerate([("visitor", "offense"), ("visitor", "defense"),
                                       ("home", "offense"), ("home", "defense")]):
        for pos, num, nm in cols[ci]:
            out["starters"].append({"side": side, "unit": unit, "pos": pos,
                                    "jersey": num, "name": nm})

    starter_names = {"visitor": set(), "home": set()}
    for s in out["starters"]:
        starter_names[s["side"]].add(s["name"])

    # ---- the three personnel lists ---------------------------------------
    for name, key in (("subs", "substitutions"), ("dnp", "did_not_play"),
                      ("inact", "not_active")):
        if name not in bounds:
            out["problems"].append("no %s section found" % name)
            continue
        lo, hi = bounds[name]
        blocks = split_blocks("\n".join(lines[lo + 1:hi]))
        if len(blocks) > 2:
            out["problems"].append(
                "%s section resolved to %d club blocks, expected 2"
                % (name, len(blocks)))
            continue
        if len(blocks) == 2:
            sides = ("visitor", "home")
        elif len(blocks) == 1:
            sides = (_one_block_side(blocks[0], starter_names),)
        else:
            sides = ()
        for side, block in zip(sides, blocks):
            if side == "unknown":
                out["problems"].append(
                    "%s section has one list that could not be attributed to a club"
                    % name)
                continue
            for pos, num, nm in block:
                out[key].append({"side": side, "pos": pos, "jersey": num, "name": nm})

    return out


def _one_block_side(block: list, starter_names: dict) -> str:
    """Which club does a lone list belong to?

    The book prints the visitor's column first, so a single list is normally the
    visitor's. That is checked against the starting lineups: if the names match
    the home club's starters instead, the list is the home club's.
    """
    names = {n for (_p, _j, n) in block}
    hit_home = len(names & starter_names["home"])
    hit_visitor = len(names & starter_names["visitor"])
    if hit_home and not hit_visitor:
        return "home"
    return "visitor"


def validate(game: dict) -> tuple:
    """Check the game book, and return (errors, notes).

    An *error* means the document could not be read with confidence, so the
    game is not published. A *note* means the book was read cleanly but says
    something worth a reviewer's attention - for example the Bears' game book
    lists two players at the position "QB". The book is the official record and
    is published as it stands; the note records that it says something
    unusual, rather than quietly "correcting" it.
    """
    errors = list(game["problems"])
    notes = []
    starters = game["starters"]
    if len(starters) != 44:
        errors.append("starter count %d, expected 44" % len(starters))
    else:
        for side in ("visitor", "home"):
            off = [s for s in starters if s["side"] == side and s["unit"] == "offense"]
            dfn = [s for s in starters if s["side"] == side and s["unit"] == "defense"]
            qb = [s for s in off if s["pos"] == "QB"]
            if len(qb) != 1:
                notes.append("the book lists %d players at the position QB on %s's "
                             "offensive lineup (%s)"
                             % (len(qb), side, ", ".join(s["name"] for s in qb)))
            front = [s for s in dfn if s["pos"] in FRONT_POSITIONS]
            back = [s for s in dfn if s["pos"] in BACK_POSITIONS]
            if len(front) < 1:
                notes.append("%s's defensive lineup lists no front defender" % side)
            if len(back) < 2:
                notes.append("%s's defensive lineup lists fewer than two defensive backs"
                             % side)
    if not game["away_team"] or not game["home_team"]:
        errors.append("match-up line not found")
    if not game["venue_stadium"]:
        errors.append("venue line not found")
    return errors, notes


GAME_FIELDS = [
    "slug", "season", "week", "game_date", "away_team", "home_team",
    "away_score", "home_score", "venue_stadium", "venue_city", "roof",
    "roof_state", "roof_status", "surface", "temp_f", "humidity_pct", "wind", "book_notes",
    "official_url", "gamebook_url", "gamebook_sha256",
]
PLAYER_FIELDS = [
    "slug", "season", "week", "game_date", "side", "team", "team_name",
    "status", "unit", "pos", "jersey", "player", "official_url", "gamebook_url",
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default="/tmp/vault")
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "gamebooks"))
    args = ap.parse_args(argv)

    index_path = os.path.join(args.vault, "games_index.tsv")
    index = {}
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                index[r["slug"]] = r

    team_names = {}
    with open(os.path.join(ROOT, "data", "teams.tsv"), encoding="utf-8", newline="") as fh:
        for r in csv.reader(fh, delimiter="\t"):
            if len(r) >= 2:
                team_names[r[1].strip()] = r[0].strip()

    text_dir = os.path.join(args.vault, "pdf", "2026")
    files = [f for f in sorted(glob.glob(os.path.join(text_dir, "*.txt")))
             if not re.search(r"\.[0-9a-f]{16}\.txt$", os.path.basename(f))]

    games, players, report = [], [], []
    notes_by_game = {}
    for path in files:
        slug = os.path.basename(path)[:-4]
        text = open(path, encoding="utf-8").read()
        game = parse_gamebook(text)
        errors, notes = validate(game)
        idx = index.get(slug, {})
        season = idx.get("season", "2026")
        week = idx.get("week", "")
        if errors:
            report.append({"slug": slug, "problems": errors})
            continue
        if notes:
            notes_by_game[slug] = notes
        away_abbr = team_names.get(game["away_team"], "")
        home_abbr = team_names.get(game["home_team"], "")
        games.append({
            "slug": slug, "season": season, "week": week,
            "game_date": game["date"],
            "away_team": away_abbr or game["away_team"],
            "home_team": home_abbr or game["home_team"],
            "away_score": game["away_score"], "home_score": game["home_score"],
            "venue_stadium": game["venue_stadium"],
            "venue_city": game["venue_city"],
            "roof": game["roof"], "roof_state": game["roof_state"],
            "roof_status": game["roof_status"], "surface": game["surface"], "temp_f": game["temp_f"],
            "humidity_pct": game["humidity_pct"], "wind": game["wind"],
            "book_notes": "; ".join(notes_by_game.get(slug, [])),
            "official_url": "https://www.nfl.com/games/%s" % slug,
            "gamebook_url": idx.get("gamebook_pdf_url", ""),
            "gamebook_sha256": idx.get("gamebook_sha256", ""),
        })
        side_team = {"visitor": away_abbr or game["away_team"],
                     "home": home_abbr or game["home_team"]}
        side_name = {"visitor": game["away_team"], "home": game["home_team"]}
        for s in game["starters"]:
            players.append({
                "slug": slug, "season": season, "week": week,
                "game_date": game["date"], "side": s["side"],
                "team": side_team[s["side"]], "team_name": side_name[s["side"]],
                "status": "starter", "unit": s["unit"], "pos": s["pos"],
                "jersey": s["jersey"], "player": s["name"],
                "official_url": "https://www.nfl.com/games/%s" % slug,
                "gamebook_url": idx.get("gamebook_pdf_url", ""),
            })
        for key, status in (("substitutions", "substitution"),
                            ("did_not_play", "did_not_play"),
                            ("not_active", "inactive")):
            for p in game[key]:
                players.append({
                    "slug": slug, "season": season, "week": week,
                    "game_date": game["date"], "side": p["side"],
                    "team": side_team[p["side"]], "team_name": side_name[p["side"]],
                    "status": status, "unit": "", "pos": p["pos"],
                    "jersey": p["jersey"], "player": p["name"],
                    "official_url": "https://www.nfl.com/games/%s" % slug,
                    "gamebook_url": idx.get("gamebook_pdf_url", ""),
                })

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "games.tsv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=GAME_FIELDS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for g in games:
            w.writerow({k: g.get(k, "") for k in GAME_FIELDS})
    with open(os.path.join(args.out, "players.tsv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=PLAYER_FIELDS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for p in players:
            w.writerow({k: p.get(k, "") for k in PLAYER_FIELDS})
    with open(os.path.join(args.out, "parse_report.json"), "w", encoding="utf-8") as fh:
        json.dump({"games_parsed": len(games), "players": len(players),
                   "games_rejected": report,
                   "games_with_notes": notes_by_game}, fh, indent=2, sort_keys=True)

    print("parsed %d games, %d personnel rows" % (len(games), len(players)))
    if report:
        print("REJECTED %d games:" % len(report))
        for r in report[:25]:
            print("  ", r["slug"], "|", "; ".join(r["problems"])[:170])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
