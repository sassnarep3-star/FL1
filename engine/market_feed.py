"""Market-feed loading, provenance and canonicalisation for the price/results spine.

WHY THIS MODULE EXISTS
    Every other part of the pipeline needs the same four facts about any number it
    touches: which feed it came from, which field of that feed, what the publisher
    documents that field to mean, and whether our copy still matches upstream. This
    module is the only place those facts are stated, so a provenance claim cannot be
    made anywhere else in the repository without going through here.

WHAT IT REFUSES TO DO
    It never merges two feeds into one column, and it never assigns a vintage
    (open / close / live) to a field the publisher has not labelled. Upstream
    `nflverse/nfldata` documents the line columns of `games.csv` in `DATASETS.md`
    without saying when in the game-week the price was taken, documents `spread_line`'s
    sign ("a positive number means the home team was favoured by that many points"),
    and does not document `closing_lines.csv`, `sc_lines.csv`, `initial_lines.csv` or
    `win_totals.csv` at all. Those statements are recorded per field below and each one
    cites the file it was read from.

Reproduce:  python3 -m engine.market_feed          (prints the registry it exposes)
"""

from __future__ import annotations

import csv
import hashlib
import os
from collections import OrderedDict
from typing import Iterable, Iterator, Sequence

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
MARKET = os.path.join(ROOT, "data", "market")

# ---------------------------------------------------------------------------
# capture facts, verified by this session on 2026-11-14 (see data/market/README.md)
# ---------------------------------------------------------------------------
#: upstream repository pin used for every hash and file-date below
UPSTREAM_REPO = "nflverse/nfldata"
UPSTREAM_TREE = "master"
UPSTREAM_HEAD = "69a1fa550eac8edfb6782cac4f92f2350ddd5b9a"
UPSTREAM_HEAD_AT = "2026-11-14T22:05:17Z"

#: per-feed provenance. `commit`/`at`/`message` are the most recent upstream commit
#: that touched the file, read from the GitHub commits API for the path on 2026-11-14.
FEEDS: "OrderedDict[str, dict]" = OrderedDict([
    ("games", {
        "file": "games.csv",
        "upstream_path": "data/games.csv",
        "commit": "69a1fa550e",
        "at": "2026-11-14T22:05:17Z",
        "message": "Automated data update",
        "publisher": "nflverse (community); derived from official NFL game books",
        "documented": ("upstream DATASETS.md documents these fields: result = home score - "
                       "away score; total = sum of both scores; spread_line positive = home "
                       "favoured by that many points; home_score/away_score are NA for games "
                       "not yet played. DATASETS.md does NOT state when the price behind "
                       "spread_line / total_line was taken."),
        "vintage": "UNDOCUMENTED",
        "markets": ("SIDE", "TOTAL", "MONEYLINE"),
        "note": ("upstream ships code/draft_kings.R, which scrapes live DraftKings prices "
                 "for games whose result is NA; that explains movement on unplayed games but "
                 "is not documented as the source of the historical columns."),
    }),
    ("closing_lines", {
        "file": "closing_lines.csv",
        "upstream_path": "data/closing_lines.csv",
        "commit": "46a1ceec90",
        "at": "2019-11-15T18:18:00Z",
        "message": "Removing wrong odds info",
        "publisher": "nflverse (community)",
        "documented": ("NOT documented in upstream DATASETS.md. Columns observed: game_id, "
                       "alt_game_id, type, side, line, odds, outcome."),
        "vintage": "CLOSE",
        "vintage_evidence": ("filename only ('closing_lines.csv'), and the last commit that "
                             "touched the file is titled 'Removing wrong odds info', which is "
                             "why SPREAD/TOTAL odds are present for 1,010 of 6,830 rows."),
        "markets": ("SIDE", "TOTAL", "MONEYLINE"),
        "note": "coverage ends with the 2018 season; no upstream update since 2019-11-15.",
    }),
    ("sc_lines", {
        "file": "sc_lines.csv",
        "upstream_path": "data/sc_lines.csv",
        "commit": "ecee8ed2b2",
        "at": "2021-06-26T17:02:14Z",
        "message": "Automated data update",
        "publisher": "nflverse (community)",
        "documented": "NOT documented in upstream DATASETS.md. Columns: season, week, away_team, home_team, game_id, side, line.",
        "vintage": "UNDOCUMENTED",
        "markets": ("SIDE",),
        "note": ("spread only, one line per side, no odds. Disagrees with games.csv on the "
                 "identity of the favoured team in 167 of 2,043 games; recorded as drift, "
                 "not resolved."),
    }),
    ("initial_lines", {
        "file": "initial_lines.csv",
        "upstream_path": "data/initial_lines.csv",
        "commit": "3beea2086c",
        "at": "2021-05-22T18:57:41Z",
        "message": "Automated data update",
        "publisher": "nflverse (community), single sportsbook WSGT",
        "documented": "NOT documented in upstream DATASETS.md. Columns: season, sportsbook, type, about, side, line.",
        "vintage": "OPEN",
        "vintage_evidence": ("filename only. The file covers the whole 2021 regular season but "
                             "its only upstream commit is dated 2021-05-22, i.e. before the "
                             "season was played, which is consistent with lines posted for the "
                             "full schedule shortly after it was released - and inconsistent "
                             "with per-week openers."),
        "markets": ("SIDE", "TOTAL"),
        "note": ("QUARANTINED as a price benchmark: no odds column, one book, and it names the "
                 "opposite favoured team from games.csv in 61 of 272 games."),
    }),
    ("win_totals", {
        "file": "win_totals.csv",
        "upstream_path": "data/win_totals.csv",
        "commit": "42d9f538bc",
        "at": "2021-07-29T03:30:10Z",
        "message": "Automated data update",
        "publisher": "nflverse (community)",
        "documented": "NOT documented in upstream DATASETS.md. Columns: season, team, line, over_odds, under_odds.",
        "vintage": "UNDOCUMENTED",
        "markets": ("WIN_TOTAL",),
        "note": "season win-total market; used to show the store is market-generic, not spread-only.",
    }),
    ("injuries_official", {
        "file": "injuries_2025.csv",
        "upstream_path": "(mirror of nflverse release assets)",
        "commit": "",
        "at": "",
        "message": "",
        "publisher": "nflverse via mirror (see data/raw/MANIFEST.json)",
        "documented": "third-party mirror; the release CDN was not reachable from the capture environment",
        "vintage": "N/A",
        "markets": (),
        "note": "not a price feed; listed so the registry covers everything under data/raw/.",
    }),
])

#: official-abbreviation mapping for the historical franchise labels the feeds use.
#: Explicit table, no fuzzy matching - the same convention as data/depth-aliases.tsv.
TEAM_ALIASES: dict[str, str] = {
    "LA": "LAR",     # Los Angeles Rams, 2016-2026 in the feed
    "STL": "LAR",    # St. Louis Rams, 1999-2015
    "SD": "LAC",     # San Diego Chargers, 1999-2016
    "OAK": "LV",     # Oakland Raiders, 1999-2019
    "JAC": "JAX",
    "AZ": "ARI",     # label used on nfl.com standings tables
    "WAS": "WAS",
}


def canon_team(abbr: str) -> str:
    """Map a feed or official-page abbreviation onto the site's canonical one."""
    a = (abbr or "").strip().upper()
    return TEAM_ALIASES.get(a, a)


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv_rows(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(value) -> float | None:
    """Parse a numeric field. Blank / NA / nan all mean *no value*, never zero."""
    s = ("" if value is None else str(value)).strip()
    if s in ("", "NA", "nan", "None", "N/A"):
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    if f != f:  # NaN
        return None
    return f


def as_int(value) -> int | None:
    f = num(value)
    return None if f is None else int(round(f))


def iter_feeds() -> Iterator[tuple[str, dict]]:
    yield from FEEDS.items()


def feed_path(feed: str) -> str:
    meta = FEEDS[feed]
    return os.path.join(RAW, meta["file"])


def upstream_url(feed: str) -> str:
    meta = FEEDS[feed]
    if not meta["upstream_path"].startswith("data/"):
        return ""
    return "https://github.com/%s/blob/%s/%s" % (UPSTREAM_REPO, UPSTREAM_TREE, meta["upstream_path"])


def manifest() -> "OrderedDict[str, dict]":
    """Per-feed capture state: file, sha256, size, row count, and the manifest hash."""
    man_path = os.path.join(RAW, "MANIFEST.json")
    committed = {}
    if os.path.exists(man_path):
        import json
        with open(man_path, encoding="utf-8") as fh:
            committed = {f["file"]: f for f in json.load(fh).get("files", [])}
    out: "OrderedDict[str, dict]" = OrderedDict()
    for name, meta in FEEDS.items():
        path = feed_path(name)
        row = OrderedDict([
            ("feed", name),
            ("file", meta["file"]),
            ("exists", os.path.exists(path)),
            ("sha256", sha256_file(path) if os.path.exists(path) else ""),
            ("bytes", os.path.getsize(path) if os.path.exists(path) else 0),
            ("rows", 0),
            ("manifest_sha256", committed.get(meta["file"], {}).get("sha256", "")),
            ("upstream_commit", meta["commit"]),
            ("upstream_at", meta["at"]),
            ("upstream_message", meta["message"]),
            ("vintage", meta["vintage"]),
            ("markets", ",".join(meta["markets"])),
        ])
        if row["exists"]:
            row["rows"] = max(0, len(read_csv_rows(path)))
        row["hash_agrees_with_manifest"] = (
            "MATCH" if row["sha256"] and row["sha256"] == row["manifest_sha256"]
            else ("BLANK" if not row["manifest_sha256"] else "DIFFERS")
        )
        out[name] = row
    return out


# ---------------------------------------------------------------------------
# typed accessors used by the rest of the spine
# ---------------------------------------------------------------------------
def load_games(only_with_scores: bool = False) -> list[dict]:
    rows = []
    for r in read_csv_rows(feed_path("games")):
        rec = OrderedDict([
            ("game_id", r["game_id"].strip()),
            ("season", as_int(r["season"])),
            ("game_type", (r.get("game_type") or "").strip()),
            ("week", as_int(r["week"])),
            ("gameday", (r.get("gameday") or "").strip()),
            ("weekday", (r.get("weekday") or "").strip()),
            ("away", canon_team(r["away_team"])),
            ("home", canon_team(r["home_team"])),
            ("away_feed_team", r["away_team"].strip()),
            ("home_feed_team", r["home_team"].strip()),
            ("away_score", as_int(r["away_score"])),
            ("home_score", as_int(r["home_score"])),
            ("location", (r.get("location") or "").strip()),
            ("margin_home", num(r["result"])),
            ("total_points", num(r["total"])),
            ("spread_line", num(r["spread_line"])),
            ("total_line", num(r["total_line"])),
            ("away_ml", as_int(r["away_moneyline"])),
            ("home_ml", as_int(r["home_moneyline"])),
            ("away_spread_odds", as_int(r["away_spread_odds"])),
            ("home_spread_odds", as_int(r["home_spread_odds"])),
            ("over_odds", as_int(r["over_odds"])),
            ("under_odds", as_int(r["under_odds"])),
            ("temp", num(r.get("temp"))),
            ("wind", num(r.get("wind"))),
            ("roof", (r.get("roof") or "").strip()),
            ("surface", (r.get("surface") or "").strip()),
            ("referee", (r.get("referee") or "").strip()),
            ("stadium", (r.get("stadium") or "").strip()),
            ("away_rest", as_int(r.get("away_rest"))),
            ("home_rest", as_int(r.get("home_rest"))),
            ("old_game_id", (r.get("old_game_id") or "").strip()),
        ])
        if only_with_scores and (rec["away_score"] is None or rec["home_score"] is None):
            continue
        rows.append(rec)
    rows.sort(key=lambda r: (r["gameday"] or "9999", r["game_id"]))
    return rows


def load_closing_lines() -> list[dict]:
    out = []
    for r in read_csv_rows(feed_path("closing_lines")):
        out.append(OrderedDict([
            ("alt_game_id", r["alt_game_id"].strip()),
            ("market", {"SPREAD": "SIDE", "TOTAL": "TOTAL", "MONEYLINE": "MONEYLINE"}.get(
                r["type"].strip().upper(), r["type"].strip().upper())),
            ("side", r["side"].strip()),
            ("line", num(r["line"])),
            ("odds", as_int(r["odds"])),
            ("outcome_flag", num(r["outcome"])),
        ]))
    out.sort(key=lambda r: (r["alt_game_id"], r["market"], r["side"]))
    return out


def load_sc_lines() -> list[dict]:
    out = []
    for r in read_csv_rows(feed_path("sc_lines")):
        out.append(OrderedDict([
            ("game_id", r["game_id"].strip()),
            ("season", as_int(r["season"])),
            ("week", as_int(r["week"])),
            ("away", canon_team(r["away_team"])),
            ("home", canon_team(r["home_team"])),
            ("side", r["side"].strip()),
            ("line", num(r["line"])),
        ]))
    out.sort(key=lambda r: (r["game_id"], r["side"]))
    return out


def load_initial_lines() -> list[dict]:
    out = []
    for r in read_csv_rows(feed_path("initial_lines")):
        out.append(OrderedDict([
            ("game_id", r["about"].strip()),
            ("season", as_int(r["season"])),
            ("sportsbook", r["sportsbook"].strip()),
            ("market", {"SPREAD": "SIDE", "TOTAL": "TOTAL"}.get(r["type"].strip().upper(),
                                                                r["type"].strip().upper())),
            ("side", r["side"].strip()),
            ("line", num(r["line"])),
        ]))
    out.sort(key=lambda r: (r["game_id"], r["market"], r["side"]))
    return out


def load_win_totals() -> list[dict]:
    out = []
    for r in read_csv_rows(feed_path("win_totals")):
        out.append(OrderedDict([
            ("season", as_int(r["season"])),
            ("team", canon_team(r["team"])),
            ("line", num(r["line"])),
            ("over_odds", as_int(r["over_odds"])),
            ("under_odds", as_int(r["under_odds"])),
        ]))
    out.sort(key=lambda r: (r["season"], r["team"]))
    return out


def load_official_results() -> list[dict]:
    """The 2026 game-by-game transcription of the official NFL schedule pages.

    Source: data/results.tsv, produced from nfl.com /schedules/2026/by-week/week-N pages
    and reconciled against the official standings table by tools/verify_results.py.
    """
    out = []
    with open(os.path.join(ROOT, "data", "results.tsv"), newline="", encoding="utf-8") as fh:
        for i, raw in enumerate(csv.reader(fh, delimiter="\t")):
            if not raw or all(not c.strip() for c in raw):
                continue
            if i == 0 and raw[0].strip().lower() == "week":
                continue
            raw = raw + [""] * (6 - len(raw))
            out.append(OrderedDict([
                ("week", as_int(raw[0])),
                ("date", raw[1].strip()),
                ("away", canon_team(raw[2])),
                ("away_score", as_int(raw[3])),
                ("home", canon_team(raw[4])),
                ("home_score", as_int(raw[5])),
            ]))
    out.sort(key=lambda r: (r["date"], r["away"]))
    return out


def load_official_standings(path: str = "data/standings.tsv", season_label: str = "2026") -> list[dict]:
    """Official standings table (club -> W/L/T, PCT, PF, PA, ...)."""
    cols = ["abbr", "w", "l", "t", "pct", "pf", "pa", "net", "home", "road", "div",
            "div_pct", "conf", "conf_pct", "nonconf", "streak", "last5"]
    out = []
    with open(os.path.join(ROOT, path), newline="", encoding="utf-8") as fh:
        for i, raw in enumerate(csv.reader(fh, delimiter="\t")):
            if not raw or all(not c.strip() for c in raw):
                continue
            raw = raw + [""] * (len(cols) - len(raw))
            rec = OrderedDict(zip(cols, [c.strip() for c in raw[:len(cols)]]))
            rec["abbr"] = canon_team(rec["abbr"])
            rec["season"] = season_label
            rec["source_file"] = path
            out.append(rec)
    out.sort(key=lambda r: r["abbr"])
    return out


def tally_from_games(games: Iterable[dict], season: int | None = None) -> "OrderedDict[str, dict]":
    """Recount W/L/T/PF/PA per club from game rows, regular season only.

    This is the reconciliation primitive: it recomputes the standings table from the
    game-level feed instead of trusting either source.
    """
    tally: "OrderedDict[str, dict]" = OrderedDict()
    for g in games:
        if season is not None and g["season"] != season:
            continue
        if g["game_type"] != "REG":
            continue
        if g["away_score"] is None or g["home_score"] is None:
            continue
        for team, pts, opp in ((g["away"], g["away_score"], g["home_score"]),
                               (g["home"], g["home_score"], g["away_score"])):
            rec = tally.setdefault(team, {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0, "G": 0})
            rec["G"] += 1
            rec["PF"] += pts
            rec["PA"] += opp
            if pts > opp:
                rec["W"] += 1
            elif pts < opp:
                rec["L"] += 1
            else:
                rec["T"] += 1
    return OrderedDict(sorted(tally.items()))


if __name__ == "__main__":  # pragma: no cover - manual inspection helper
    for name, row in manifest().items():
        print("%-19s rows=%-6s bytes=%-9s sha256=%s  manifest=%s  vintage=%s" % (
            name, row["rows"], row["bytes"], row["sha256"][:12] or "-",
            row["hash_agrees_with_manifest"], row["vintage"]))
