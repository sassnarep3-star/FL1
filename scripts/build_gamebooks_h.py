#!/usr/bin/env python3
"""H2 canonical builder: official NFL Game Book capture for Week 10, 2026.

Reads the transcribed capture module `_ingest_gamebooks_h.py` (tokens copied
verbatim from the official Game Book PDFs fetched 2026-11-17) and emits the
canonical data files the site generator reads:

  data/gamebooks_games.tsv    one row per game: identity, final score, official
                              stadium/roof/surface/weather/attendance + source URL
  data/gamebooks_rosters.tsv  one row per player per game: role (starter /
                              sub / dnp / inactive) and the Game Book's own
                              position/jersey/name
  data/gamebooks_snaps.tsv    one row per player per game per unit: the official
                              Game Book "Playtime Percentage" table (offense /
                              defense / special teams). Several Game Books label
                              this table "(Unofficial)"; that label is carried
                              onto every row of such games and is NOT silently
                              dropped (see flags F-GB-1).
  data/venue_official.csv     canonical stadium/roof/surface for the 13 venues
                              of this slate, from the Game Book itself.

Nothing is inferred: a cell the Game Book did not print stays blank, and the
builder refuses to emit a game whose PDF URL is missing.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _ingest_gamebooks_h as IN  # noqa: E402
import _ingest_gamebooks_snaps_h as SNAPS  # noqa: E402

DATA = os.path.join(ROOT, "data")
GAMES_TSV = os.path.join(DATA, "gamebooks_games.tsv")
ROSTERS_TSV = os.path.join(DATA, "gamebooks_rosters.tsv")
SNAPS_TSV = os.path.join(DATA, "gamebooks_snaps.tsv")
VENUE_CSV = os.path.join(DATA, "venue_official.csv")

GAME_HEADER = [
    "game_key", "date", "away_abbr", "home_abbr", "away_pts", "home_pts",
    "stadium", "city_state", "roof", "surface", "game_weather", "temp_f",
    "humidity_pct", "wind_dir", "wind_mph", "wind_chill_f", "attendance",
    "game_center_url", "game_book_url",
]
ROSTER_HEADER = [
    "game_key", "date", "team", "role", "unit", "position", "jersey", "name",
]
SNAP_HEADER = [
    "game_key", "date", "team", "position", "name",
    "offense_pct", "defense_pct", "special_teams_pct", "source_label",
]
VENUE_HEADER = [
    "game_key", "stadium", "city_state", "roof", "surface",
    "team_abbr", "game_book_url",
]

# Games whose Game Book labels its Playtime Percentage table "(Unofficial)".
# Carried verbatim onto the snap rows so the reader is not misled into treating
# the playtime percentages as an official snap count for those games.
UNOFFICIAL_SNAPS = {"HOUCL", "LARARI", "SEALV", "BUFNYJ"}


def _num(value):
    return value if value != "" else ""


def build_games():
    rows = []
    for key, g in IN.ROSTERS.items():
        info = g["info"]
        if not info.get("pdf"):
            raise SystemExit("missing Game Book URL for %s" % key)
        rows.append([
            key, info["date"], info["away"], info["home"],
            _num(info["ap"]), _num(info["hp"]),
            info["stadium"], info["city"], info["roof"], info["surface"],
            info["weather"], _num(info["temp"]), _num(info["hum"]),
            info["wind_dir"], _num(info["wind_mph"]), _num(info["chill"]),
            _num(info["att"]), info["gc"], info["pdf"],
        ])
    rows.sort(key=lambda r: (r[1], r[0]))
    _write_tsv(GAMES_TSV, GAME_HEADER, rows)
    return rows


def build_rosters(game_rows):
    rows = []
    for gr in game_rows:
        key = gr[0]
        g = IN.ROSTERS[key]
        info = g["info"]
        for team, blocks in g.items():
            if team == "info":
                continue
            for block, tokens in blocks.items():
                if not tokens:
                    continue
                if ":" not in block:
                    continue
                role, unit = block.split(":", 1)
                for tok in tokens.split(";"):
                    tok = tok.strip()
                    if not tok:
                        continue
                    part = tok.split()
                    if len(part) < 2:
                        raise SystemExit("bad roster token %r in %s" % (tok, key))
                    position, jersey = part[0], part[1]
                    name = " ".join(part[2:])
                    rows.append([key, info["date"], team, role, unit,
                                 position, jersey, name])
    rows.sort(key=lambda r: (r[1], r[0], r[2], r[3]))
    _write_tsv(ROSTERS_TSV, ROSTER_HEADER, rows)
    return rows


def build_snaps(game_rows):
    rows = []
    for gr in game_rows:
        key = gr[0]
        date = gr[1]
        if key not in SNAPS.SNAPS:
            continue
        unofficial = key in UNOFFICIAL_SNAPS
        for team, unit, name, off, defn, st in SNAPS.SNAPS[key]:
            rows.append([key, date, team, unit, name,
                         _num(off), _num(defn), _num(st),
                         "Unofficial" if unofficial else "Official"])
    rows.sort(key=lambda r: (r[1], r[0], r[2], r[4]))
    _write_tsv(SNAPS_TSV, SNAP_HEADER, rows)
    return rows


def build_venue(game_rows):
    rows = []
    for gr in game_rows:
        key, stadium, city, roof, surface, _, pdf = (
            gr[0], gr[6], gr[7], gr[8], gr[9], "", gr[18])
        for abbr in (gr[2], gr[3]):
            rows.append([key, stadium, city, roof, surface, abbr, pdf])
    _write_csv(VENUE_CSV, VENUE_HEADER, rows)
    return rows


def _write_tsv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(header) + "\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")


def _write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def main():
    os.makedirs(DATA, exist_ok=True)
    game_rows = build_games()
    roster_rows = build_rosters(game_rows)
    venue_rows = build_venue(game_rows)
    snap_rows = build_snaps(game_rows)
    print("games=%d rosters=%d venue_rows=%d snaps=%d"
          % (len(game_rows), len(roster_rows), len(venue_rows), len(snap_rows)))
    print("wrote", GAMES_TSV)
    print("wrote", ROSTERS_TSV)
    print("wrote", SNAPS_TSV)
    print("wrote", VENUE_CSV)


if __name__ == "__main__":
    main()
