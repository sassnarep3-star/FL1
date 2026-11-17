#!/usr/bin/env python3
"""
build_availability_graph.py — publish the expected-vs-actual availability graph.

WHAT IT DOES
    Joins the clubs' own published depth charts (captured for Week 10 of 2026)
    to the official NFL Game Books for the Week 10 games, and writes one row per
    (game, club, player) saying what the club's chart expected and what the
    official book recorded.

Run:  python3 scripts/build_availability_graph.py
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import availability_graph as ag  # noqa: E402

WEEK = "10"


def main() -> int:
    depth = ag.load_depth_slots(os.path.join(ROOT, "data", "depth_slots.tsv"))
    players = ag.load_game_players(os.path.join(ROOT, "data", "gamebooks", "players.tsv"))
    games = ag.load_games(os.path.join(ROOT, "data", "gamebooks", "games.tsv"))

    rows = ag.build(depth, players, games, WEEK)
    ag.write_tsv(os.path.join(ROOT, "data", "availability_graph.tsv"),
                 ag.GRAPH_FIELDS, rows)

    summary = ag.summarise(rows)
    summary["week"] = WEEK
    summary["games"] = len({r["game_slug"] for r in rows})
    summary["clubs"] = len({(r["game_slug"], r["club"]) for r in rows})
    summary["chart_capture"] = ("club depth charts captured for Week 10 of 2026; "
                                "the graph is therefore built for Week 10 games only")
    with open(os.path.join(ROOT, "data", "availability_graph_summary.json"), "w",
              encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)

    print("wrote data/availability_graph.tsv: %d rows across %d games, %d club-games"
          % (summary["rows"], summary["games"], summary["clubs"]))
    for k, v in sorted(summary["by_outcome"].items(), key=lambda kv: -kv[1]):
        print("  %-34s %d" % (k, v))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
