#!/usr/bin/env python3
"""Drift alarm (gate G-18): pin every register/scraper output to expected row counts
and required fields; FAIL loudly when a field goes missing or a dataset shrinks.

The brief: "Add a drift alarm to every scraper. Pin each parser to expected row counts
and required fields; fail the build loudly when a field goes missing rather than
publishing a blank."

Design
------
- A pin states: file, expected data-row count, required columns, and (optionally)
  columns that must be non-empty on every row.
- SHRUNK (fewer rows than pinned)  -> FAIL, exit 1.  Data going backwards is how a
  scraper dies quietly; this build refuses to publish it.
- GREW (more rows than pinned)     -> WARN, exit 0.  Growth is usually legitimate
  (a new week settled); the pin is meant to be re-committed with the growth, in the
  open, not bypassed.
- MISSING FIELD / NULLIFIED COLUMN -> FAIL, exit 1.  A column that silently turns
  empty is the exact failure mode the brief names.

Output: data/verification-drift.tsv (rewritten each run) + a loud table on stderr.
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "verification-drift.tsv"

# Every entry: id, path (relative to ROOT), kind (tsv|csv|json-list|json-doc),
# header (True if the file carries a header row), expected rows, required columns
# (column NAMES for headered files, 0-based INDEXES for headerless ones), and
# columns that must be non-empty per row (same rule).
PINS = [
    ("DR-01", "data/injuries.tsv", "tsv", False, 345,
     [0, 1, 2, 4, 5], [0, 1]),
    ("DR-02", "data/standings.tsv", "tsv", False, 32,
     [0, 1, 2], [0]),
    ("DR-03", "data/results.tsv", "tsv", False, 137,
     [0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5]),
    ("DR-04", "data/schedule2026-d.csv", "csv", True, 272,
     ["week", "away_team", "home_team", "stadium"], ["week", "away_team", "home_team", "stadium"]),
    ("DR-05", "data/results_feed.csv", "csv", True, 137,
     ["game_id", "away_score", "home_score"], ["game_id", "away_score", "home_score"]),
    ("DR-06", "data/price_snapshots.csv", "csv", True, 56,
     ["game_id", "market_type", "side"], ["game_id", "market_type", "side"]),
    ("DR-07", "data/settled_markets.csv", "csv", True, 548,
     ["game_id", "market", "outcome"], ["game_id", "market", "outcome"]),
    ("DR-08", "data/questions.json", "json-list", None, 45,
     ["id", "question"], ["id", "question"]),
    ("DR-09", "data/suggestions.json", "json-list", None, 48,
     ["id", "title"], ["id", "title"]),
    ("DR-10", "data/flags.json", "json-list", None, 68,  # F67 (results) + F68 (row citation audit)
     ["id", "item"], ["id", "item"]),
    ("DR-11", "data/strategies.json", "json-list", None, 6,
     ["id", "name", "change_of_mind"], ["id", "name", "change_of_mind"]),
    ("DR-12", "data/validation_gates.json", "json-doc", None, 15,
     ["g_id"], ["g_id"]),
    ("DR-13", "data/leaderboard_signal_staking.json", "json-doc", None, 16,
     ["strategy_id"], ["strategy_id"]),
    ("DR-14", "data/sources.tsv", "tsv", False, None,  # grows legitimately; pin columns only
     [0, 1, 3, 4], [0, 1, 3, 4]),
    ("DR-15", "data/reserve_list_2026-11.tsv", "tsv", True, 25,
     ["date", "player", "club", "transaction"], ["date", "player", "club", "transaction"]),
    ("DR-16", "data/announced_starters_g.json", "json-doc", None, 4,
     ["id", "player", "club"], ["id", "player", "club"]),
    ("DR-17", "data/venue_spotchecks.json", "json-doc", None, 2,
     ["id", "game_id"], ["id", "game_id"]),
    ("DR-18", "data/luck_panel_signals.json", "json-doc", None, 16,
     ["strategy_id"], ["strategy_id"]),
    ("DR-19", "data/ablations.json", "json-doc", None, 2,
     ["target"], None),
]


def load_rows(path: pathlib.Path, kind: str, has_header: bool):
    if kind in ("tsv", "csv"):
        delim = "\t" if kind == "tsv" else ","
        with open(path, encoding="utf-8", newline="") as fh:
            if has_header:
                return list(csv.DictReader(fh, delimiter=delim))
            return [dict(enumerate(row)) for row in csv.reader(fh, delimiter=delim) if row]
    if kind == "json-list":
        return json.load(open(path, encoding="utf-8"))
    if kind == "json-doc":
        doc = json.load(open(path, encoding="utf-8"))
        for key in ("rows", "ablations"):
            if key in doc:
                val = doc[key]
                if isinstance(val, list):
                    return val
                if isinstance(val, dict):
                    return list(val.values())
        raise ValueError("%s: no rows/ablations list found" % path.name)
    raise ValueError(kind)


def check() -> int:
    results = []
    failures = 0
    warnings = 0
    for pid, rel, kind, header, expected, required_cols, nonempty in PINS:
        path = ROOT / rel
        if not path.exists():
            results.append([pid, rel, "FAIL", "file missing", "0", expected or "-"])
            failures += 1
            continue
        try:
            rows = load_rows(path, kind, header)
        except Exception as exc:  # noqa: BLE001 - the alarm must never die silently
            results.append([pid, rel, "FAIL", "unreadable: %s" % exc, "-", expected or "-"])
            failures += 1
            continue
        n = len(rows)
        # column presence
        missing_cols = [c for c in required_cols if rows and c not in rows[0]]
        if missing_cols:
            results.append([pid, rel, "FAIL", "missing columns: %s" % ",".join(missing_cols),
                            n, expected or "-"])
            failures += 1
            continue
        # required non-empty fields
        nullified = []
        for c in (nonempty or []):
            blanks = sum(1 for r in rows if not str(r.get(c) or "").strip())
            if blanks == n and n > 0:
                nullified.append(c)
        if nullified:
            results.append([pid, rel, "FAIL",
                            "column(s) %s went fully empty" % ",".join(nullified), n, expected or "-"])
            failures += 1
            continue
        if expected is not None and n < expected:
            results.append([pid, rel, "FAIL", "row count SHRANK (scraper drift?)",
                            n, expected])
            failures += 1
            continue
        if expected is not None and n > expected:
            results.append([pid, rel, "WARN", "row count grew - re-commit the pin with the growth",
                            n, expected])
            warnings += 1
            continue
        results.append([pid, rel, "PASS", "pinned", n, expected if expected is not None else "-"])

    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["check_id", "file", "status", "note", "rows_now", "rows_pinned"])
        w.writerows(results)

    print("drift alarm (G-18): %d pins, %d PASS, %d WARN, %d FAIL"
          % (len(PINS), sum(1 for r in results if r[2] == "PASS"), warnings, failures))
    for r in results:
        if r[2] != "PASS":
            print("  %s %s -> %s (%s; rows %s vs pin %s)" % (r[2], r[1], r[3], r[0], r[4], r[5]),
                  file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(check())
