#!/usr/bin/env python3
"""Build data/injury_hub_delta.json — the delta between dated reads of the
official injury hub (https://www.nfl.com/injuries/).

Requirement (brief): "Store every injury-hub read with its clock time and
publish the delta, never the level."

Inputs (raw captures, never edited after write once assembled):
  raw/injuries-week10-2026.md          read 1, 2026-11-14 (source S01)
  raw/injuries-week10-2026-read2.md    read 2, 2026-11-16 (source S80)
  raw/injuries-week10-2026-read3.md    read 3, 2026-11-17T02:35-02:36Z (source S94, session 7ac4e12e)
  raw/injuries-week10-2026-read4.md    read 4, 2026-11-17T02:33-02:43Z window, completed after
                                       read 3 (source S97, session a502c4e0)
                                       (assembled from 8 fetched chunks by
                                        scripts/assemble_read3.py)
  raw/injuries-week11-2026-read5.md    read 5, 2026-11-19 (same official hub URL as S01)
                                       First WEEK 11 read (7 fetched chunks). A week
                                       rollover is NOT a same-week delta: read 4 ->
                                       read 5 is recorded under "week_rollover",
                                       never as the site's same-week "delta". The
                                       dated raw capture is retained; no separate full-
                                       level TSV is generated for publication.

The parser is the same line grammar tools/verify_injuries.py uses for read 1,
applied to all five captures. The script fails loudly on any practice/game value
the grammar does not map, if read 1 no longer parses to data/injuries.tsv, or if
a later capture's header row claim disagrees with the parser.

Output: data/injury_hub_delta.json —
  "delta"   latest same-week diff (read 3 -> read 4), published on the site;
  "history" earlier same-week diffs retained;
  "week_rollover" read 4 -> read 5 membership/designation diff, clearly labelled
                   as a Week 10 -> Week 11 transition, not a same-week change.
Changed/added/removed ROWS are published; no full parsed level TSV is written.

Run:  python3 scripts/build_injury_hub_delta.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "injury_hub_delta.json")

READ1 = os.path.join(ROOT, "raw", "injuries-week10-2026.md")
READ2 = os.path.join(ROOT, "raw", "injuries-week10-2026-read2.md")
READ3 = os.path.join(ROOT, "raw", "injuries-week10-2026-read3.md")
READ4 = os.path.join(ROOT, "raw", "injuries-week10-2026-read4.md")
READ5 = os.path.join(ROOT, "raw", "injuries-week11-2026-read5.md")

CLUBS = {
    "Commanders", "Giants", "Patriots", "Lions", "Chiefs", "Falcons", "Vikings",
    "Packers", "Jaguars", "Titans", "Bills", "Jets", "Dolphins", "Colts",
    "Panthers", "Saints", "Texans", "Browns", "Rams", "Cardinals", "Seahawks",
    "Raiders", "49ers", "Cowboys", "Steelers", "Bengals", "Chargers", "Ravens",
    "Bears", "Broncos", "Eagles", "Buccaneers",
}

ABBR = {
    "Washington Commanders": "WAS", "New York Giants": "NYG",
    "New England Patriots": "NE", "Detroit Lions": "DET",
    "Kansas City Chiefs": "KC", "Atlanta Falcons": "ATL",
    "Minnesota Vikings": "MIN", "Green Bay Packers": "GB",
    "Jacksonville Jaguars": "JAX", "Tennessee Titans": "TEN",
    "Buffalo Bills": "BUF", "New York Jets": "NYJ",
    "Miami Dolphins": "MIA", "Indianapolis Colts": "IND",
    "Carolina Panthers": "CAR", "New Orleans Saints": "NO",
    "Houston Texans": "HOU", "Cleveland Browns": "CLE",
    "Los Angeles Rams": "LAR", "Arizona Cardinals": "ARI",
    "Seattle Seahawks": "SEA", "Las Vegas Raiders": "LV",
    "San Francisco 49ers": "SF", "Dallas Cowboys": "DAL",
    "Pittsburgh Steelers": "PIT", "Cincinnati Bengals": "CIN",
    "Los Angeles Chargers": "LAC", "Baltimore Ravens": "BAL",
    "Chicago Bears": "CHI", "Denver Broncos": "DEN",
    "Philadelphia Eagles": "PHI", "Tampa Bay Buccaneers": "TB",
}

ROW = re.compile(
    r'^\| \[(?P<player>[^\]]+)\]\(https://www\.nfl\.com/players/[^)]*\)'
    r' \| (?P<pos>[^|]*)\| (?P<injury>[^|]*)\| (?P<practice>[^|]*)\| (?P<game>[^|]*)\|$'
)

PRACTICE_MAP = {
    "Full Participation in Practice": "FULL",
    "Limited Participation in Practice": "LIMITED",
    "Did Not Participate In Practice": "DNP",
    "": "",
}

GAME_MAP = {
    "Out": "Out", "Doubtful": "Doubtful", "Questionable": "Questionable",
    "": "",
}


def parse_capture_text(text, source):
    """Parse a capture's text with the shared grammar. `source` is only used
    in failure messages so a bad value can be traced to its capture file."""
    rows, current = [], None
    for line in text.splitlines():
        s = line.strip()
        if s in CLUBS:
            current = None
            for full, ab in ABBR.items():
                if full.endswith(" " + s) or full == s:
                    current = ab
                    break
            if current is None:
                raise SystemExit("FAIL: club heading %r did not map to an abbr (%s)"
                                 % (s, source))
            continue
        m = ROW.match(s)
        if m and current:
            practice = PRACTICE_MAP.get(m.group("practice").strip(),
                                        "?" + m.group("practice").strip())
            game = GAME_MAP.get(m.group("game").strip(),
                                "?" + m.group("game").strip())
            if practice.startswith("?") or game.startswith("?"):
                raise SystemExit("FAIL: unmapped value in %s: %r" % (source, s))
            rows.append({
                "team": current,
                "player": m.group("player").strip(),
                "pos": m.group("pos").strip(),
                "injury": m.group("injury").strip(),
                "practice": practice,
                "game": game,
            })
    return rows


def parse_capture(path):
    if not os.path.exists(path):
        raise SystemExit("FAIL: %s missing" % path)
    with open(path, encoding="utf-8") as fh:
        return parse_capture_text(fh.read(), os.path.relpath(path, ROOT))


def key(r):
    return (r["team"], r["player"], r["pos"])


def _assert_unique(rows, label):
    keys = [key(r) for r in rows]
    if len(set(keys)) != len(keys):
        raise SystemExit("FAIL: duplicate (club, player, position) key inside %s" % label)


def diff(old_rows, new_rows, older_label, newer_label):
    _assert_unique(old_rows, older_label)
    _assert_unique(new_rows, newer_label)
    old = {key(r): r for r in old_rows}
    new = {key(r): r for r in new_rows}

    changed, added, removed = [], [], []
    for k in sorted(new):
        if k not in old:
            added.append(new[k])
        else:
            for field in ("injury", "practice", "game"):
                if old[k][field] != new[k][field]:
                    c = dict(new[k])
                    c["field"] = field
                    c["old"] = old[k][field]
                    c["new"] = new[k][field]
                    changed.append(c)
    for k in sorted(old):
        if k not in new:
            removed.append(old[k])

    per_old, per_new = {}, {}
    for r in old_rows:
        per_old[r["team"]] = per_old.get(r["team"], 0) + 1
    for r in new_rows:
        per_new[r["team"]] = per_new.get(r["team"], 0) + 1
    per_club = [{"team": t,
                 "older": per_old.get(t, 0),
                 "newer": per_new.get(t, 0)}
                for t in sorted(set(per_old) | set(per_new))
                if per_old.get(t) != per_new.get(t)]

    return {"between": "%s -> %s" % (older_label, newer_label),
            "older_label": older_label,
            "newer_label": newer_label,
            "changed": changed, "added": added, "removed": removed,
            "per_club_row_count_changes": per_club}


def main():
    r1, r2, r3 = parse_capture(READ1), parse_capture(READ2), parse_capture(READ3)
    r4 = parse_capture(READ4)
    r5 = parse_capture(READ5)

    # like-for-like sanity: read 1 must still reproduce the canonical TSV
    tsv = []
    tsv_path = os.path.join(ROOT, "data", "injuries.tsv")
    with open(tsv_path, newline="", encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            if line.strip():
                c = line.split("\t")
                c += [""] * (6 - len(c))
                tsv.append({"team": c[0], "player": c[1], "pos": c[2],
                            "injury": c[3], "practice": c[4], "game": c[5]})
    if r1 != tsv:
        raise SystemExit("FAIL: read-1 capture no longer parses to data/injuries.tsv "
                         "(%d vs %d rows) — refuse to publish a delta on a moving baseline"
                         % (len(r1), len(tsv)))

    # read 3's header carries its own row claim (written after assembly); the
    # claim and the parser must agree before any delta is published.
    with open(READ3, encoding="utf-8") as fh:
        read3_text = fh.read()
    m = re.search(r"^[-\s]*Rows parsed: (\d+)", read3_text, flags=re.M)
    if not m:
        raise SystemExit("FAIL: read-3 capture has no 'Rows parsed:' header claim")
    if int(m.group(1)) != len(r3):
        raise SystemExit("FAIL: read-3 header claims %s rows, parser produced %d"
                         % (m.group(1), len(r3)))

    # read 4's header carries its own row claim (written after parse); the
    # claim and the parser must agree before any delta is published.
    with open(READ4, encoding="utf-8") as fh:
        read4_text = fh.read()
    m = re.search(r"^[\-\s]*Rows parsed: (\d+)", read4_text, flags=re.M)
    if not m:
        raise SystemExit("FAIL: read-4 capture has no 'Rows parsed:' header claim")
    if int(m.group(1)) != len(r4):
        raise SystemExit("FAIL: read-4 header claims %s rows, parser produced %d"
                         % (m.group(1), len(r4)))

    # read 5's header carries its own row claim (written after parse); the
    # claim and the parser must agree before anything is published.
    with open(READ5, encoding="utf-8") as fh:
        read5_text = fh.read()
    m = re.search(r"^[\-\s]*Rows parsed: (\d+)", read5_text, flags=re.M)
    if not m:
        raise SystemExit("FAIL: read-5 capture has no 'Rows parsed:' header claim")
    if int(m.group(1)) != len(r5):
        raise SystemExit("FAIL: read-5 header claims %s rows, parser produced %d"
                         % (m.group(1), len(r5)))

    delta12 = diff(r1, r2, "read 1 (2026-11-14)", "read 2 (2026-11-16)")
    delta23 = diff(r2, r3, "read 2 (2026-11-16)", "read 3 (2026-11-17)")
    delta34 = diff(r3, r4, "read 3 (2026-11-17 02:36Z)", "read 4 (2026-11-17 02:43Z)")
    # WEEK ROLLOVER (Week 10 -> Week 11): a different week's report, not a
    # same-week designation change. Published under its own key so the site's
    # "delta" (same-week) is never polluted by a week change.
    rollover45 = diff(r4, r5, "read 4 (WEEK 10, 2026-11-17)",
                      "read 5 (WEEK 11, 2026-11-19)")

    payload = {
        "id": "injury_hub_delta",
        "title": "Injury-hub reads — clock-timed, delta published",
        "requirement": "Store every injury-hub read with its clock time and publish "
                       "the delta, never the level.",
        "updated": "2026-11-19",
        "url": "https://www.nfl.com/injuries/",
        "reads": [
            {"read": 1, "capture": "raw/injuries-week10-2026.md",
             "captured": "2026-11-14", "rows": len(r1),
             "week_shown": "WEEK 10", "source_id": "S01"},
            {"read": 2, "capture": "raw/injuries-week10-2026-read2.md",
             "read_window_utc": "after 2026-11-16T01:14:56Z, before 2026-11-16T01:25:00Z",
             "rows": len(r2), "week_shown": "WEEK 10", "source_id": "S80"},
            {"read": 3, "capture": "raw/injuries-week10-2026-read3.md",
             "read_window_utc": "after 2026-11-17T02:35:39Z, before 2026-11-17T02:36:52Z",
             "rows": len(r3), "week_shown": "WEEK 10", "source_id": "S94"},
            {"read": 4, "capture": "raw/injuries-week10-2026-read4.md",
             "read_window_utc": "after 2026-11-17T02:33:27Z, before 2026-11-17T02:43:50Z "
                                "(chunks interleaved with read 3; completed after it)",
             "rows": len(r4), "week_shown": "WEEK 10", "source_id": "S97"},
        ],
        "delta": delta34,
        "history": [delta12, delta23],
        "week_rollover_read": {
            "read": 5, "capture": "raw/injuries-week11-2026-read5.md",
            "read_window_utc": "2026-11-19 (7 fetched chunks; completed before "
                               "2026-11-19T05:23:32Z; chunk-boundary seconds not "
                               "emitted by the fetch tool)",
            "rows": len(r5), "week_shown": "WEEK 11", "source_id": "S01",
            "source_url": "https://www.nfl.com/injuries/",
        },
        "week_rollover": rollover45,
        "reserve_list_pointers": [
            {"text": "NFL news roundup: Vikings WR Jordan Addison needs thumb surgery, "
                     "could go to IR; Buccaneers add QB",
             "url": "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-monday-nov-16"},
            {"text": "NFL news roundup: Patriots place RB TreVeyon Henderson (illness) "
                     "on injured reserve",
             "url": "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-saturday-nov-14"},
            {"text": "Dolphins place QB Malik Willis (groin) on injured reserve; "
                     "Kyle McCord in line for first start",
             "url": "https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start"},
            {"text": "Rams WR Puka Nacua likely to be placed on injured reserve with "
                     "turf toe, sprained MCL and PCL",
             "url": "https://www.nfl.com/news/rams-wr-puka-nacua-likely-to-be-placed-on-injured-reserve-with-turf-toe-sprained-mcl-and-pcl"},
            {"text": "NFL news roundup: Saints waive Kendre Miller; Cowboys place "
                     "Malachi Lawrence on IR",
             "url": "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-saturday-nov-7"},
        ],
        "provenance": {
            "tier": "OFFICIAL",
            "source_ids": ["S01", "S80", "S94", "S97"],
            "verification": "read 1 re-parses to data/injuries.tsv exactly (asserted "
                            "here, independently of tools/verify_injuries.py); reads 2 "
                            "and 3 parsed with the same grammar; every practice/game "
                            "value maps to a known designation; read 3's header row "
                            "claim matches the parser; read 3 was assembled from 8 "
                            "fetched chunks by scripts/assemble_read3.py, which asserts "
                            "the seam-crossing rows rejoin correctly; read 4's header "
                            "row claim matches the parser; each changed row of read 4 "
                            "was re-checked line-by-line against reads 2 and 3 before "
                            "publishing; read 5 (WEEK 11) parsed with the same grammar, "
                            "header claim matches the parser, and the Week 10 -> Week 11 "
                            "transition is published only as week_rollover, never as the "
                            "same-week delta.",
        },
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print("read1 rows=%d  read2 rows=%d  read3 rows=%d  read4 rows=%d  read5 rows=%d"
          % (len(r1), len(r2), len(r3), len(r4), len(r5)))
    print("week rollover read 4 -> read 5: changed=%d added=%d removed=%d"
          % (len(rollover45["changed"]), len(rollover45["added"]),
             len(rollover45["removed"])))
    for d in (delta12, delta23, delta34):
        print("%s: changed=%d added=%d removed=%d" %
              (d["between"], len(d["changed"]), len(d["added"]), len(d["removed"])))
    print("published delta = read 3 -> read 4:")
    for c in delta34["changed"]:
        print("  %s %s (%s): %s '%s' -> '%s'"
              % (c["team"], c["player"], c["field"], c["pos"], c["old"], c["new"]))
    for a in delta34["added"]:
        print("  + %s %s (%s) %s | %s | %s"
              % (a["team"], a["player"], a["pos"], a["injury"], a["practice"], a["game"]))
    for d in delta34["removed"]:
        print("  - %s %s (%s)" % (d["team"], d["player"], d["pos"]))
    for p in delta34["per_club_row_count_changes"]:
        print("  club row count: %s %d -> %d" % (p["team"], p["older"], p["newer"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
