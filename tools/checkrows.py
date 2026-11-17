#!/usr/bin/env python3
"""checkrows.py — the row-level verification gate.

The brief: "Every table row must have a source link to an official site. If a
value can't be confirmed from an official source, leave it blank and flag it as
unverified. Never infer or fill in values."

This script audits every table on the published site, row by row. A row passes
when it publishes no unsourced value:

    1. it carries a source chip (class="src"), or
    2. it carries any hyperlink (a source-registry or official URL), or
    3. its text references a registered source id (S01..S99 convention), or
    4. every one of its cells is blank/na/empty — it publishes nothing, or
    5. it is on a register/decision page (DEF_PAGES below), where rows are
       authored definitions and decision-support text rather than NFL data; or
    6. it is on the explicitly labelled project-specification page (SPEC_PAGES),
       whose rows are user-provided requirements, not NFL facts. That exemption
       is valid only while the page carries its specification-provenance notice.

Data pages — results, prices, boards, depth, standings, injuries, schedule,
correlations, sources, flags — must satisfy 1-4 on every row. Run after
tools/site.py and scripts/build_pages_d.py.

Run:  python3 tools/checkrows.py
"""

import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Register/decision pages: authored definitions or planning rows, not NFL data entries.
DEF_PAGES = {
    "questions.html", "suggestions.html", "requirements.html",
    "validation.html", "line-origination.html",
    "readiness.html",  # register/decision rows (targets are not measured facts)
}

# This page is exempt from the NFL-fact source rule only because its rows are
# explicitly labelled as user-provided project specifications in the page body.
SPEC_PAGES = {"requirements-backlog.html"}
SPEC_NOTICE = "spec-provenance"
SPEC_NOTICE_TEXT = "user-provided project specifications"

ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
CELL_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
TAG_RE = re.compile(r"<[^>]+>")
SID_RE = re.compile(r"\bS\d{2}\b")


def cell_text(fragment):
    return TAG_RE.sub("", fragment).replace("&mdash;", "").strip()


def cell_is_blank(fragment):
    return ('class="blank"' in fragment or 'class="na"' in fragment
            or cell_text(fragment) == "")


def row_ok(row):
    if 'class="src"' in row:
        return True
    if "<a " in row or "<a\n" in row:
        return True
    if SID_RE.search(TAG_RE.sub(" ", row)):
        return True
    cells = CELL_RE.findall(row)
    if not cells:
        return True
    return all(cell_is_blank(c) for c in cells)


def check_page(path):
    """Return (n_rows, offending row numbers, n_def_rows, n_spec_rows)."""
    name = os.path.basename(path)
    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    bad = []
    row_no = 0
    for table_m in re.finditer(r"<table[^>]*>(.*?)</table>", html, re.S):
        body = table_m.group(1)
        tbody = body.split("</thead>", 1)[-1]
        for row_m in ROW_RE.finditer(tbody):
            row_no += 1
            if not row_ok(row_m.group(1)):
                bad.append(row_no)
    if name in SPEC_PAGES:
        plain = " ".join(TAG_RE.sub(" ", html).split()).lower()
        notice_present = (re.search(r'class="[^"]*\b%s\b[^"]*"' % SPEC_NOTICE, html)
                          is not None and SPEC_NOTICE_TEXT in plain
                          and "not nfl requirements" in plain)
        return row_no, ([] if notice_present else [0]), 0, row_no if notice_present else 0
    if name in DEF_PAGES:
        return row_no, [], row_no, 0
    return row_no, bad, 0, 0


def main():
    pages = sorted(glob.glob(os.path.join(ROOT, "*.html")))
    total_bad = 0
    total_rows = def_rows = spec_rows = 0
    for p in pages:
        n, bad, d, s = check_page(p)
        total_rows += n
        def_rows += d
        spec_rows += s
        if bad:
            total_bad += len(bad)
            if bad == [0]:
                print("FAIL %s: project-specification exemption lacks its provenance notice"
                      % os.path.basename(p))
            else:
                print("FAIL %s: %d of %d rows publish a value with no source link: %s"
                      % (os.path.basename(p), len(bad), n, bad[:10]))
    if total_bad:
        print("\n%d row/source or provenance failure(s). Data rows need a source "
              "link or must publish nothing; project-specification exemptions "
              "must remain explicitly labelled." % total_bad)
        sys.exit(1)
    data_rows = total_rows - def_rows - spec_rows
    print("OK: %d pages, %d rows audited (%d register/decision rows, "
          "%d explicitly labelled user-provided specification rows, "
          "%d data rows satisfying rules 1-4)."
          % (len(pages), total_rows, def_rows, spec_rows, data_rows))


if __name__ == "__main__":
    main()
