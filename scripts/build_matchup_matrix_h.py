#!/usr/bin/env python3
"""H3 — Offense vs Defense matchup deficiency matrix (1st-4th string).

Requirement R64: an offense-vs-defense matchup deficiency matrix at the
1st-4th string level.

Method (all inputs are official or already-verified in the repo):

  * The official inactive (Not Active) and Did Not Play lists come from the
    Game Book capture (data/gamebooks_rosters.tsv, role inactive/dnp). These
    are the players each club cannot field on game day.
  * Each missing player is mapped to a string (1st/2nd/3rd/4th) by matching
    the player's name against the club depth chart (data/depth.tsv), which
    records the string number for every charted player at each unit. The
    string level is a property of the depth chart, not inferred from the
    injury report.
  * For each game and each string level 1..4, the matrix records how many
    players each side is missing on offense and on defense. The
    offense-vs-defense deficiency is the pair: how depleted the offense is
    (missing offensive players at that string) against how depleted the
    opposing defense is (missing defensive players at that string).

A missing player whose name is not found on the club's depth chart is counted
in an "unmatched" bucket and reported in the note rather than silently
assigned a string. Nothing is inferred.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, HERE)

OUT = os.path.join(DATA, "matchup_matrix.tsv")
HEADER = [
    "game_key", "date", "away_team", "home_team", "string_level",
    "away_offense_missing", "home_defense_missing",
    "away_defense_missing", "home_offense_missing",
    "away_offense_names", "home_defense_names",
    "away_defense_names", "home_offense_names", "note",
]


def read_tsv(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        rows = [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]
    return rows[1:]


def load_depth():
    """abbr -> {name: (unit, string)} and abbr -> {lastname: [(first, unit, string)]}.

    The Game Book prints abbreviated names ("M.Mariota"); the depth chart
    prints full names ("Matthew Mariota"). Both an exact-name map and a
    last-name + first-initial index are built so an inactive can be resolved
    to a string. Ambiguous matches are left unmatched (never guessed).
    """
    depth = {}
    by_last = {}
    with open(os.path.join(DATA, "depth.tsv"), encoding="utf-8") as fh:
        for ln in fh:
            p = ln.rstrip("\n").split("\t")
            if len(p) < 5:
                continue
            abbr, unit, pos, name, string = p[0], p[1], p[2], p[3], p[4]
            depth.setdefault(abbr, {})[name] = (unit, string)
            parts = name.split()
            if parts:
                last = parts[-1]
                first = parts[0]
                by_last.setdefault((abbr, last), []).append((first, unit, string))
    return depth, by_last


def resolve(name, team, by_last):
    """Resolve a Game Book name to (unit, string) or (None, None).

    The Game Book prints abbreviated names either as "M.Mariota" (initial dot,
    no space) or "A.Williams" (initial + space + lastname). Split on both the
    dot and whitespace. Matches by last name + first initial against the depth
    chart. Returns (unit, string, matched_bool). Ambiguous matches return False.
    """
    # Normalise "M.Mariota" -> "M Mariota"
    norm = name.replace(".", " ").strip()
    parts = norm.split()
    if len(parts) != 2:
        return None, None, False
    initial, last = parts
    initial = initial.rstrip(".")
    if len(initial) != 1:
        return None, None, False
    cands = by_last.get((team, last), [])
    hits = [(u, s) for (f, u, s) in cands if f and f[0].lower() == initial.lower()]
    if len(hits) == 1:
        return hits[0][0], hits[0][1], True
    return None, None, False


def main():
    games = read_tsv("gamebooks_games.tsv")
    rosters = read_tsv("gamebooks_rosters.tsv")
    depth, by_last = load_depth()

    # For each (game, team, unit), collect missing players (inactive + dnp)
    # and map them to string levels via the depth chart.
    missing = {}  # (game, team, unit) -> list of (name, string_or_None)
    for r in rosters:
        key, date, team, role, unit, pos, j, name = r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]
        if role not in ("inactive", "dnp"):
            continue
        # Resolve unit + string via the depth chart.
        dunit, dstring, matched = resolve(name, team, by_last)
        if not matched:
            dunit, dstring = unit, None
        missing.setdefault((key, team, dunit), []).append((name, dstring))

    rows = []
    for g in games:
        key, date, away, home = g[0], g[1], g[2], g[3]
        for level in range(1, 5):
            def cnt(team, unit):
                return [n for (n, s) in missing.get((key, team, unit), [])
                        if s == str(level)]
            ao = cnt(away, "Offense")
            hd = cnt(home, "Defense")
            ad = cnt(away, "Defense")
            ho = cnt(home, "Offense")
            note_parts = []
            for team in (away, home):
                for unit in ("Offense", "Defense"):
                    all_missing = missing.get((key, team, unit), [])
                    unmatched = [n for (n, s) in all_missing if s is None]
                    if unmatched:
                        note_parts.append(
                            "%s %s unmatched-to-depth: %s"
                            % (team, unit, ", ".join(sorted(unmatched))))
            rows.append([
                key, date, away, home, str(level),
                str(len(ao)), str(len(hd)), str(len(ad)), str(len(ho)),
                "; ".join(sorted(ao)), "; ".join(sorted(hd)),
                "; ".join(sorted(ad)), "; ".join(sorted(ho)),
                " ".join(note_parts),
            ])
    rows.sort(key=lambda r: (r[1], r[0], int(r[4])))
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(HEADER) + "\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    # summary
    total_missing = sum(len(v) for v in missing.values())
    unmatched = sum(1 for v in missing.values() for (n, s) in v if s is None)
    print("matchup_matrix.tsv: %d rows, %d missing-player records, %d unmatched"
          % (len(rows), total_missing, unmatched))


if __name__ == "__main__":
    main()
