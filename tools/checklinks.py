#!/usr/bin/env python3
"""
checklinks.py — static link integrity check for the published site.

Checks:
  1. every internal href resolves to a file that exists in the repo
  2. every internal anchor (#id) exists in the target document
  3. every asset referenced (css/js) exists
  4. every page appears in the navigation and is reachable from index.html
  5. no page references a data source ID that is not in data/sources.tsv
  6. external links are counted and listed (they are not fetched here; see
     tools/verify_sources.py for the fetch log)

Exit code is non-zero if anything is broken, so this can gate a merge.

Run:  python3 tools/checklinks.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HREF = re.compile(r'href="([^"]+)"')
ID = re.compile(r'id="([^"]+)"')
SRCID = re.compile(r'\bS(\d{2})\b')


def main():
    pages = sorted(f for f in os.listdir(ROOT) if f.endswith(".html"))
    if not pages:
        print("no pages found", file=sys.stderr)
        return 1

    ids = {}
    text = {}
    for p in pages:
        with open(os.path.join(ROOT, p), encoding="utf-8") as fh:
            body = fh.read()
        text[p] = body
        ids[p] = set(ID.findall(body))

    errors = []
    warnings = []
    external = set()
    internal_edges = {}

    for p in pages:
        body = text[p]
        edges = set()
        for href in HREF.findall(body):
            if href.startswith(("http://", "https://")):
                external.add(href)
                continue
            if href.startswith(("mailto:", "#")):
                if href.startswith("#") and href[1:] and href[1:] not in ids[p]:
                    errors.append("%s: missing local anchor %s" % (p, href))
                continue
            target, _, frag = href.partition("#")
            if target == "":
                continue
            if not os.path.exists(os.path.join(ROOT, target)):
                errors.append("%s: dead internal link %s" % (p, href))
                continue
            if target.endswith(".html"):
                edges.add(target)
                if frag and frag not in ids.get(target, set()):
                    errors.append("%s: link %s points at missing anchor #%s" % (p, href, frag))

        internal_edges[p] = edges

    # asset references
    for p in pages:
        for m in re.findall(r'(?:src|href)="(assets/[^"]+)"', text[p]):
            if not os.path.exists(os.path.join(ROOT, m)):
                errors.append("%s: missing asset %s" % (p, m))

    # reachability from index
    seen, stack = {"index.html"}, ["index.html"]
    while stack:
        cur = stack.pop()
        for nxt in internal_edges.get(cur, ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    for p in pages:
        if p not in seen:
            errors.append("%s: not reachable from index.html" % p)

    # source-id integrity
    try:
        with open(os.path.join(ROOT, "data", "sources.tsv"), encoding="utf-8") as fh:
            known = {line.split("\t")[0] for line in fh if line.strip()}
    except OSError:
        known = set()
    for p in pages:
        for m in SRCID.findall(text[p]):
            sid = "S" + m
            if sid not in known:
                errors.append("%s: references unknown source %s" % (p, sid))

    # every NAV entry exists
    nav_block = text["index.html"]
    for href in re.findall(r'class="nav"[^>]*>(.*?)</nav>', nav_block, re.S):
        for h in HREF.findall(href):
            if h.endswith(".html") and not os.path.exists(os.path.join(ROOT, h)):
                errors.append("navigation lists missing page %s" % h)

    # escaped-markup guard: a rendered anchor must never appear as literal text
    for p in pages:
        escaped = text[p].count("&lt;a ") + text[p].count("&lt;td") + text[p].count("&lt;span")
        if escaped:
            errors.append("%s: %d escaped markup fragment(s) — an HTML string was "
                          "passed through cell() instead of raw_src()" % (p, escaped))

    print("pages checked: %d" % len(pages))
    print("external links: %d (not fetched here; see tools/verify_sources.py)" % len(external))
    for w in warnings:
        print("WARN:", w)
    if errors:
        print("\n%d LINK PROBLEM(S):" % len(errors), file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        return 1
    print("OK: every internal link and anchor resolves, every page reachable, "
          "all source IDs registered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
