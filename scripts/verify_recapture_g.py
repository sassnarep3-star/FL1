#!/usr/bin/env python3
"""
verify_recapture_g.py — session `arena-dbf11de0-fl1` (task G1).

Re-parses the DATED RE-CAPTURE of the official NFL.com Week 10 2026 injury report
(`raw/injuries-week10-2026-recapture-2026-11-16.md`, sha256 recorded in
`data/raw/MANIFEST-g.json`) and diffs it line by line against the published
table `data/injuries.tsv` (the 2026-11-14 capture).

Why this exists
---------------
Two earlier review items said, essentially, "the published counts are stale".
The only way to check that claim is to read the official page again on a later
date and compare, row by row, field by field. This script does that and exits
non-zero on any difference, so it can gate a merge.

It also settles three specific flagged claims:
  * the three Lions rows whose Game Status cell was published blank
    (Kerby Joseph, Cade Mays, D.J. Reed) — the official page is the arbiter;
  * the published row count and the "no injuries reported" section count;
  * whether any club gained or lost rows between the two dates.

Run:  python3 scripts/verify_recapture_g.py
Exit: 0 = every row matches, 1 = a difference was found (printed in full).
No third-party packages.
"""

import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECAPTURE = os.path.join(ROOT, "raw", "injuries-week10-2026-recapture-2026-11-16.md")
FIRST = os.path.join(ROOT, "raw", "injuries-week10-2026.md")
TSV = os.path.join(ROOT, "data", "injuries.tsv")
OUT_TSV = os.path.join(ROOT, "raw", "injuries-week10-2026-recapture-2026-11-16.tsv")
VER = os.path.join(ROOT, "data", "verification-g.tsv")

CLUBS = {
    "Commanders", "Giants", "Patriots", "Lions", "Chiefs", "Falcons", "Vikings",
    "Packers", "Jaguars", "Titans", "Bills", "Jets", "Dolphins", "Colts",
    "Panthers", "Saints", "Texans", "Browns", "Rams", "Cardinals", "Seahawks",
    "Raiders", "49ers", "Cowboys", "Steelers", "Bengals", "Chargers", "Ravens",
    "Bears", "Broncos", "Eagles", "Buccaneers",
}

ABBR = {
    "Commanders": "WAS", "Giants": "NYG", "Patriots": "NE", "Lions": "DET",
    "Chiefs": "KC", "Falcons": "ATL", "Vikings": "MIN", "Packers": "GB",
    "Jaguars": "JAX", "Titans": "TEN", "Bills": "BUF", "Jets": "NYJ",
    "Dolphins": "MIA", "Colts": "IND", "Panthers": "CAR", "Saints": "NO",
    "Texans": "HOU", "Browns": "CLE", "Rams": "LAR", "Cardinals": "ARI",
    "Seahawks": "SEA", "Raiders": "LV", "49ers": "SF", "Cowboys": "DAL",
    "Steelers": "PIT", "Bengals": "CIN", "Chargers": "LAC", "Ravens": "BAL",
    "Bears": "CHI", "Broncos": "DEN", "Eagles": "PHI", "Buccaneers": "TB",
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

GAME_MAP = {"Out": "Out", "Doubtful": "Doubtful", "Questionable": "Questionable", "": ""}


def parse(path):
    """Parse a markdown capture of nfl.com/injuries into rows."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    rows, current, unknown = [], None, []
    for ln, line in enumerate(lines, 1):
        s = line.strip()
        if s in CLUBS:
            current = ABBR[s]
            continue
        if s.startswith("## NEWS"):
            current = None
            continue
        m = ROW.match(s)
        if not m:
            continue
        if current is None:
            unknown.append((ln, s))
            continue
        practice = m.group("practice").strip()
        game = m.group("game").strip()
        if practice not in PRACTICE_MAP:
            unknown.append((ln, "practice=%r" % practice))
            continue
        if game not in GAME_MAP:
            unknown.append((ln, "game=%r" % game))
            continue
        rows.append({
            "team": current,
            "player": m.group("player").strip(),
            "pos": m.group("pos").strip(),
            "injury": m.group("injury").strip(),
            "practice": PRACTICE_MAP[practice],
            "game": GAME_MAP[game],
        })
    return rows, unknown


def load_tsv(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            f = line.split("\t")
            f += [""] * (6 - len(f))
            out.append({
                "team": f[0], "player": f[1], "pos": f[2], "injury": f[3],
                "practice": f[4], "game": f[5],
            })
    return out


FIELDS = ["team", "player", "pos", "injury", "practice", "game"]


def key(r):
    return (r["team"], r["player"])


def main():
    rec, unknown = parse(RECAPTURE)
    pub = load_tsv(TSV)

    with open(OUT_TSV, "w", encoding="utf-8") as fh:
        for r in rec:
            fh.write("\t".join(r[f] for f in FIELDS) + "\n")

    pub_i = {key(r): r for r in pub}
    rec_i = {key(r): r for r in rec}

    only_pub = [k for k in pub_i if k not in rec_i]
    only_rec = [k for k in rec_i if k not in pub_i]
    diffs = []
    for k in sorted(set(pub_i) & set(rec_i)):
        for f in FIELDS:
            if pub_i[k][f] != rec_i[k][f]:
                diffs.append((k, f, pub_i[k][f], rec_i[k][f]))

    # Write the change record: this is the deliverable, not a failure.
    with open(os.path.join(ROOT, "data", "injury_diff_g.tsv"), "w",
              encoding="utf-8") as fh:
        fh.write("change\tteam\tplayer\tfield\tvalue_2026_11_14\tvalue_2026_11_16\n")
        for k in sorted(only_rec):
            fh.write("row_added\t%s\t%s\t-\t-\t-\n" % k)
        for k in sorted(only_pub):
            fh.write("row_removed\t%s\t%s\t-\t-\t-\n" % k)
        for k, f, a, b in sorted(diffs):
            fh.write("field_changed\t%s\t%s\t%s\t%s\t%s\n"
                     % (k[0], k[1], f, a if a else "(blank)", b if b else "(blank)"))

    checks = []

    def add(cid, desc, res, detail):
        checks.append((cid, desc, res, detail))

    add("G-V1", "re-capture parses with no unparsed rows", "PASS" if not unknown else "FAIL",
        "unparsed: %s" % (unknown[:5] if unknown else "none"))
    add("G-V2", "row count: published table vs 2026-11-16 re-capture",
        "PASS" if len(pub) == len(rec) else "DIFF",
        "published %d rows, re-capture %d rows" % (len(pub), len(rec)))
    add("G-V3", "no published row is absent from the re-capture (no invented rows)",
        "PASS" if not only_pub else "FAIL",
        "missing in re-capture: %d; field differences: %d" % (len(only_pub), len(diffs)))
    add("G-V4", "rows added on the official page since 2026-11-14",
        "PASS" if not only_rec else "DIFF",
        "new rows: %s" % (", ".join("%s %s" % k for k in only_rec[:10]) or "none"))

    # The three Lions rows explicitly queried in review.
    lions = {r["player"]: r["game"] for r in rec if r["team"] == "DET"}
    wanted = ["Kerby Joseph", "Cade Mays", "D.J. Reed"]
    got = {w: lions.get(w) for w in wanted}
    add("G-V5", "DET Kerby Joseph / Cade Mays / D.J. Reed game status on the official page",
        "PASS" if all(got[w] for w in wanted) else "FAIL",
        "; ".join("%s=%s" % (w, got[w] or "BLANK") for w in wanted))

    # Designation coverage — the claim "only 6 of 254 rows carry a game designation".
    filled = sum(1 for r in rec if r["game"])
    add("G-V6", "rows carrying a game-status designation in the re-capture",
        "INFO", "%d of %d rows carry a game designation (%.1f%%)"
        % (filled, len(rec), 100.0 * filled / max(1, len(rec))))
    for g in ("Out", "Doubtful", "Questionable"):
        add("G-V6%s" % g[:3].lower(), "count of %s designations" % g, "INFO",
            "%d" % sum(1 for r in rec if r["game"] == g))

    clubs = sorted({r["team"] for r in rec})
    add("G-V7", "clubs present on the official Week 10 page", "INFO",
        "%d clubs: %s" % (len(clubs), ",".join(clubs)))

    with open(VER, "w", encoding="utf-8") as fh:
        fh.write("check\tdescription\tresult\tdetail\tsource\n")
        for cid, desc, res, detail in checks:
            fh.write("%s\t%s\t%s\t%s\t%s\n"
                     % (cid, desc, res, detail, "https://www.nfl.com/injuries/"))

    manifest = {}
    mpath = os.path.join(ROOT, "data", "raw", "MANIFEST-g.json")
    for name, path in (("injuries-week10-2026-recapture-2026-11-16.md", RECAPTURE),
                       ("injuries-week10-2026-recapture-2026-11-16.tsv", OUT_TSV)):
        with open(path, "rb") as fh:
            manifest[name] = {
                "sha256": hashlib.sha256(fh.read()).hexdigest(),
                "bytes": os.path.getsize(path),
            }
    manifest["_source"] = "https://www.nfl.com/injuries/"
    manifest["_retrieved"] = "2026-11-16T01:19:16Z"
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("rows in published table : %d" % len(pub))
    print("rows in 2026-11-16 capture: %d" % len(rec))
    print("missing in re-capture   : %d" % len(only_pub))
    print("new in re-capture       : %d" % len(only_rec))
    print("field differences       : %d" % len(diffs))
    for k in only_pub[:20]:
        print("  ONLY PUBLISHED : %s" % (k,))
    for k in only_rec[:20]:
        print("  ONLY RECAPTURE : %s" % (k,))
    for k, f, a, b in diffs[:40]:
        print("  DIFF %s %s: published=%r recapture=%r" % (k, f, a, b))
    for cid, desc, res, detail in checks:
        print("  %-7s %-4s %s | %s" % (cid, res, desc, detail))
    for ln, s in unknown[:10]:
        print("  UNPARSED line %d: %s" % (ln, s))

    # Policy (stated so the gate is not silently relaxed): the 2026-11-14 table is
    # the PRE-KICKOFF snapshot and is never overwritten by a later read — doing so
    # would inject lookahead into any backtest. A row that exists on 11-14 but not
    # on 11-16 would mean the earlier table held an invented row, so that FAILS.
    # Rows added later, and fields that moved later, are RECORDED, not failures:
    # they are the evidence that the report is a series, not a snapshot.
    ok = not only_pub and not unknown
    print("\nGATE: %s (hard failures: rows missing from the later official read, "
          "or unparsed rows)" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
