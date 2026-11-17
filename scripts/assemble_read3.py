#!/usr/bin/env python3
"""Assemble raw/injuries-week10-2026-read3.md from its chunk-seam staging markers.

The 2026-11-17 read of https://www.nfl.com/injuries/ was fetched in 8 content
chunks whose boundaries fall MID-LINE for 6 of the 7 seams. The staged capture
carries one @@SEAMnn@@ marker line per seam. This script:

  1. removes the marker lines and the staging newline they replaced so each
     split line re-joins character-exactly (seam 01 was a clean line boundary,
     so there only the marker line itself goes away);
  2. fails loudly if any marker remains, if a marker is duplicated, or if the
     assembled file no longer parses with the same line grammar
     scripts/build_injury_hub_delta.py uses (every practice/game value must
     map to a known designation — an unmapped value aborts);
  3. prints the parsed row count so the header claim ("Rows parsed: N") can be
     asserted against it.

Idempotent: running it on an already-assembled capture is a no-op parse.

Run:  python3 scripts/assemble_read3.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "raw", "injuries-week10-2026-read3.md")

# Mid-line seams: marker line plus the newline that staged it must both vanish.
MIDLINE = ["12", "23", "34", "45", "56", "67"]
# Line-boundary seam: only the marker line goes away (one newline stays).
LINE = "01"


def main():
    with open(PATH, encoding="utf-8") as fh:
        text = fh.read()

    n_mid = 0
    for nn in MIDLINE:
        marker = "\n@@SEAM%s@@\n" % nn
        c = text.count(marker)
        if c > 1:
            raise SystemExit("FAIL: seam marker %s appears %d times" % (nn, c))
        if c == 1:
            text = text.replace(marker, "")
            n_mid += 1

    marker01 = "@@SEAM%s@@\n" % LINE
    c01 = text.count(marker01)
    if c01 > 1:
        raise SystemExit("FAIL: seam marker %s appears %d times" % (LINE, c01))
    if c01 == 1:
        text = text.replace(marker01, "")

    leftover = re.findall(r"@@SEAM[0-9]{2}@@", text)
    if leftover:
        raise SystemExit("FAIL: unrecognised seam marker(s) remain: %s"
                         % sorted(set(leftover)))

    if n_mid not in (0, len(MIDLINE)):
        raise SystemExit("FAIL: partial assembly (%d of %d mid-line seams) — "
                         "refuse to write a half-joined capture"
                         % (n_mid, len(MIDLINE)))

    # Parse with the shared grammar (imported from the delta builder so the
    # two scripts can never drift apart).
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_injury_hub_delta as b
    rows = b.parse_capture_text(text, source="raw/injuries-week10-2026-read3.md")

    # The seam-crossing rows are the ones a bad join would break: assert each
    # of them parsed to its full, correct line.
    expect = {
        ("KC", "Patrick Mahomes", "QB"): ("", "FULL", ""),
        ("JAX", "Chris Rodriguez Jr.", "RB"): ("", "LIMITED", ""),
        ("IND", "Jonathan Taylor", "RB"): ("", "FULL", ""),
        ("SF", "Siran Neal", "S"): ("", "FULL", ""),
        ("LAC", "Brenen Thompson", "WR"): ("Hamstring", "DNP", "Doubtful"),
    }
    by = {(r["team"], r["player"], r["pos"]): r for r in rows}
    for k, v in expect.items():
        if k not in by:
            raise SystemExit("FAIL: seam-crossing row missing after assembly: %r" % (k,))
        r = by[k]
        got = (r["injury"], r["practice"], r["game"])
        if got != v:
            raise SystemExit("FAIL: seam-crossing row %r parsed as %r, expected %r"
                             % (k, got, v))

    # Header claim check (fill "Rows parsed: N" in the capture header).
    m = re.search(r"^[-\s]*Rows parsed: (\d+)", text, flags=re.M)
    if m:
        claimed = int(m.group(1))
        if claimed != len(rows):
            raise SystemExit("FAIL: header claims %d rows, parser produced %d"
                             % (claimed, len(rows)))
        claim = "header claim matches (%d)" % claimed
    else:
        claim = "header has no claim yet — parser produced %d rows" % len(rows)

    if n_mid:
        with open(PATH, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("assembled: %d mid-line seams + 1 line seam rejoined" % n_mid)
    else:
        print("already assembled (idempotent no-op)")
    print("rows parsed: %d — %s" % (len(rows), claim))
    return 0


if __name__ == "__main__":
    sys.exit(main())
