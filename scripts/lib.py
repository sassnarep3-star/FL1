"""Shared helpers for the FL1 NFL line-generation lab.

Design rules for this repo:
  * No number is invented. Every statistic is computed from a named source file.
  * Anything that cannot be computed from a source is returned as None / blank.
  * All money math is push-aware and vig-aware.
"""
from __future__ import annotations

import csv
import json
import math
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = ROOT / "data" / "raw"

# ----------------------------------------------------------------------------
# Provenance registry. ids are referenced by data/sources.json
# ----------------------------------------------------------------------------
SOURCES = {
    "NFD_GAMES": {
        "id": "NFD_GAMES",
        "title": "nflverse/nfldata — games.csv (schedules, scores, closing lines)",
        "url": "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
        "repo": "https://github.com/nflverse/nfldata",
        "publisher": "nflverse (open data, MIT)",
        "official": False,
        "used_for": "Margins, totals, closing spread/total/moneyline, rest days, roof, surface, QB ids",
    },
    "NFD_CLOSING": {
        "id": "NFD_CLOSING",
        "title": "nflverse/nfldata — closing_lines.csv (spread / total / moneyline, source: Sports Book Reviews)",
        "url": "https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv",
        "repo": "https://github.com/nflverse/nfldata",
        "publisher": "nflverse (open data, MIT)",
        "official": False,
        "used_for": "Cross-check of closing prices; push-free outcome flags (see irregularity #4)",
    },
    "NFD_SCLINES": {
        "id": "NFD_SCLINES",
        "title": "nflverse/nfldata — sc_lines.csv",
        "url": "https://github.com/nflverse/nfldata/blob/master/data/sc_lines.csv",
        "repo": "https://github.com/nflverse/nfldata",
        "publisher": "nflverse (open data, MIT)",
        "official": False,
        "used_for": "Second closing-spread series (2013+) for line-movement feasibility checks",
    },
    "NFD_ROSTERS": {
        "id": "NFD_ROSTERS",
        "title": "nflverse/nfldata — rosters.csv (season roster + Approximate Value)",
        "url": "https://github.com/nflverse/nfldata/blob/master/data/rosters.csv",
        "repo": "https://github.com/nflverse/nfldata",
        "publisher": "nflverse (open data, MIT)",
        "official": False,
        "used_for": "Starter/backup identification per team-season via games-started share",
    },
    "NFD_WINTOTALS": {
        "id": "NFD_WINTOTALS",
        "title": "nflverse/nfldata — win_totals.csv (season win total market)",
        "url": "https://github.com/nflverse/nfldata/blob/master/data/win_totals.csv",
        "repo": "https://github.com/nflverse/nfldata",
        "publisher": "nflverse (open data, MIT)",
        "official": False,
        "used_for": "Season-long market benchmark context only",
    },
    "NFL_INJURIES_2025": {
        "id": "NFL_INJURIES_2025",
        "title": "nflverse/nflverse-data release `injuries` — injuries_2025.csv",
        "url": "https://github.com/nflverse/nflverse-data/releases/tag/injuries",
        "repo": "https://github.com/nflverse/nflverse-data",
        "publisher": "nflverse, derived from NFL.com official weekly injury reports",
        "official": False,
        "used_for": "Weekly game-status designations (Out/Doubtful/Questionable) and IR for 2025",
    },
    "NFL_INJURIES_MIRROR": {
        "id": "NFL_INJURIES_MIRROR",
        "title": "Mirror copy of injuries_2025.csv — mgiancola9/nfl-predictions",
        "url": "https://github.com/mgiancola9/nfl-predictions/blob/main/data/raw/injuries_2025.csv",
        "publisher": "third-party mirror of nflverse data",
        "official": False,
        "used_for": "Fallback copy because the nflverse release CDN is blocked in this sandbox (irregularity #1)",
    },
    "NFL_COM_INJURIES": {
        "id": "NFL_COM_INJURIES",
        "title": "NFL.com official injury report (weekly, all 32 clubs)",
        "url": "https://www.nfl.com/injuries/",
        "publisher": "NFL",
        "official": True,
        "used_for": "Current-week availability snapshot, hand-read and cited row by row",
    },
    "NFL_PLAYING_RULES_2025": {
        "id": "NFL_PLAYING_RULES_2025",
        "title": "2025 Official Playing Rules of the National Football League (PDF)",
        "url": "https://media.nfl.com/content/dam/communications/Official%20Playing%20Rules/2025%20Official%20Playing%20Rules.pdf",
        "publisher": "NFL",
        "official": True,
        "used_for": "Injury timeout rules (Rule 5, Article 2-4); game rules affecting totals modelling",
    },
    "NFL_OPS_ATSPOTTER": {
        "id": "NFL_OPS_ATSPOTTER",
        "title": "NFL Football Operations — AT Spotters (injury video review)",
        "url": "https://operations.nfl.com/game-operations-logistics/game-day-assistants/at-spotters",
        "publisher": "NFL Football Operations",
        "official": True,
        "used_for": "Confirms an independent injury-detection channel exists in every game (a signal source)",
    },
    "ESPN_PROBABLE": {
        "id": "ESPN_PROBABLE",
        "title": "ESPN — NFL removes 'probable' designation from team injury reports (2016 policy change)",
        "url": "https://www.espn.com/nfl/story/_/id/17361111/nfl-streamlines-injured-players-game-status-removes-probable-designation",
        "publisher": "ESPN",
        "official": False,
        "used_for": "Documents that Out/Doubtful/Questionable are definitions, not probabilities (2016 onward)",
    },
    "NFD_PREDICTIONS": {
        "id": "NFD_PREDICTIONS",
        "title": "nflverse/nfldata — predictions.csv (published model predictions, benchmark only)",
        "url": "https://github.com/nflverse/nfldata/blob/master/data/predictions.csv",
        "publisher": "nflverse (open data, MIT)",
        "official": False,
        "used_for": "Independent benchmark probabilities for calibration comparison",
    },
}

TEAM_ALIASES = {
    "SD": "LAC", "LAC": "LAC", "STL": "LAR", "LA": "LAR", "LAR": "LAR",
    "OAK": "LV", "LV": "LV", "WAS": "WAS", "WSH": "WAS", "JAC": "JAX",
    "JAX": "JAX", "CLV": "CLE", "ARZ": "ARI", "BLT": "BAL", "HST": "HOU",
    "SL": "LAR",
}


def norm_team(t: str) -> str:
    if t is None:
        return ""
    t = str(t).strip().upper()
    return TEAM_ALIASES.get(t, t)


def money_to_prob(ml: float) -> float | None:
    """American odds -> implied probability (vig included)."""
    if ml is None or (isinstance(ml, float) and math.isnan(ml)):
        return None
    if ml == 0:
        return None
    return (-ml) / (-ml + 100.0) if ml < 0 else 100.0 / (ml + 100.0)


def payout_per_unit(ml: float) -> float:
    """Profit for a 1-unit win at American odds `ml`."""
    return (100.0 / -ml) if ml < 0 else (ml / 100.0)


def read_csv(path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, rows: list[dict], fields: list[str] | None = None) -> None:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        for r in rows:
            for k in r:
                if k not in fields:
                    fields.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})


def fnum(x):
    """Parse to float or None."""
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.upper() in {"NA", "NULL", "NAN"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None
