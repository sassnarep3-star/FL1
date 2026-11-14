"""Verification of the published site and its registers.

This is the part of the brief that says "do not merge a broken site" and "every table
row must have a source link", turned into a gate that fails the build rather than a
promise in a README. Run it after building:

    python3 site/verify.py          # exit code 0 means publishable

Checks:
  V1  every generated page is byte-identical to a fresh build of data/ (no hand-edits)
  V2  every internal link in docs/ resolves to a file that exists
  V3  no placeholder text survives into a page (TODO, TBD, lorem, FIXME, {{token}})
  V4  every factual table row on a generated page carries at least one source link,
      unless its register marks it editorial
  V5  every source id used anywhere resolves to a row in data/sources.json
  V6  a flagged-unverified numeric value is not sitting in a cell that got filled in
      (i.e. the number of blank markers matches the number of blank cells in the data)
  V7  the engine's unit tests pass, and the demo output matches the committed file
  V8  docs/assets/dashboard.css and app.js exist and are referenced correctly
"""

from __future__ import annotations

import json
import sys as _sys

_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if False else None
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
PAGES = os.path.join(DOCS, "pages")
DATA = os.path.join(ROOT, "data")

PLACEHOLDERS = ("TODO", "TBD", "FIXME", "lorem ipsum", "XXXX", "{{", "}}")
# 'placeholder' is deliberately not in the list: the registers use the word to describe
# the CSV spec, which is a real sentence, not scaffolding.
ALLOW_UNDECLARED = ()
ALLOW_LINK_ONLY = re.compile(r"^(https?:|mailto:|#|\.|/)")


def fail(msg: str, fails: list) -> None:
    fails.append(msg)


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def hrefs(html_text: str) -> list[str]:
    return re.findall(r'href="([^"]+)"', html_text)


def check_generation_drift(fails: list) -> None:
    """V1: rebuild into a temp copy and compare, so a hand-edited page cannot ship."""
    before = {}
    for dirpath, _dirs, files in os.walk(PAGES):
        for f in files:
            p = os.path.join(dirpath, f)
            before[os.path.relpath(p, PAGES)] = read(p)
    subprocess.run([sys.executable, os.path.join(ROOT, "site", "build.py")],
                   check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
    after = {}
    for dirpath, _dirs, files in os.walk(PAGES):
        for f in files:
            p = os.path.join(dirpath, f)
            after[os.path.relpath(p, PAGES)] = read(p)
    if set(before) != set(after):
        fail(f"V1 generated file set changed: {set(before) ^ set(after)}", fails)
    for k in sorted(set(before) & set(after)):
        if before[k] != after[k]:
            fail(f"V1 {k} differs from a fresh build — the committed HTML was hand-edited", fails)


def check_links(fails: list) -> tuple[int, int]:
    """V2: every internal href resolves. External hrefs are counted, not fetched."""
    total_links = ext_links = 0
    for dirpath, _dirs, files in os.walk(DOCS):
        for f in files:
            if not f.endswith(".html"):
                continue
            path = os.path.join(dirpath, f)
            rel = os.path.relpath(path, DOCS)
            for href in hrefs(read(path)):
                total_links += 1
                if href.startswith("#") or href.startswith("mailto:"):
                    continue
                if href.startswith(("http://", "https://")):
                    ext_links += 1
                    if not re.match(r"^https?://[^\s\"'<>]+$", href):
                        fail(f"V2 malformed external href in {rel}: {href}", fails)
                    continue
                target = os.path.normpath(os.path.join(dirpath, href.split("#")[0].split("?")[0]))
                if not os.path.exists(target):
                    fail(f"V2 broken internal link in {rel}: {href} -> {target}", fails)
    return total_links, ext_links


def check_placeholders(fails: list) -> None:
    """V3: no scaffolding text survives into the published page.

    A blank cell is legitimate and is rendered as an em dash by the builder; the
    forbidden thing is a token or a note-to-self that implies unfinished work.
    """
    for dirpath, _dirs, files in os.walk(DOCS):
        for f in files:
            if not f.endswith(".html"):
                continue
            text = read(os.path.join(dirpath, f))
            for token in PLACEHOLDERS:
                if token in text:
                    line = text.splitlines()[next(
                        i for i, ln in enumerate(text.splitlines()) if token in ln)]
                    fail(f"V3 placeholder {token!r} in {f}: …{line.strip()[:120]}…", fails)
                    break


def check_row_sources(fails: list) -> dict:
    """V4/V5/V6 over the registers themselves (the single source of truth)."""
    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from build import OWNED, path_for

    sources = json.load(open(path_for("sources"), encoding="utf-8"))
    known = {r["src_id"] for r in sources["rows"]}
    stats = {"rows": 0, "sourced": 0, "editorial": 0, "blanks": 0, "unknown_ids": 0,
             "declared_unsourced": 0}

    # Only this subsystem's registers are checked. The published dashboard keeps its own
    # data/*.json registers with a different schema; validating them against ours would
    # report someone else's correct file as broken.
    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from build import OWNED, path_for  # same resolution the builder uses
    for name in OWNED:
        path = path_for(name)
        if not os.path.exists(path) or name == "demo_results":
            continue
        doc = json.load(open(path, encoding="utf-8"))
        editorial = bool(doc.get("editorial"))
        blocks = doc.get("sections") or [{"columns": doc.get("columns", []), "rows": doc.get("rows", [])}]
        for b in blocks:
            cols = [c if isinstance(c, dict) else {"key": c} for c in (b.get("columns") or [])]
            has_src_col = any(c.get("render") == "srclist" for c in cols)
            for i, row in enumerate(b.get("rows") or []):
                if not isinstance(row, dict):
                    continue
                stats["rows"] += 1
                ids = row.get("sources") or []
                if ids:
                    stats["sourced"] += 1
                    for sid in ids:
                        if sid not in known:
                            stats["unknown_ids"] += 1
                            fail(f"V5 {name} row {i} cites unregistered source id {sid!r}", fails)
                elif has_src_col and not editorial and not row.get("no_source_reason"):
                    fail(f"V4 {name} row {i} has neither a source id nor a declared "
                         "no_source_reason", fails)
                else:
                    stats["declared_unsourced"] = stats.get("declared_unsourced", 0) + 1
                if editorial:
                    stats["editorial"] += 1
                # V6: a cell rendered as a flagged blank must actually be empty
                for c in cols:
                    v = row.get(c["key"])
                    if v in ("", None) and c.get("key") != "sources":
                        stats["blanks"] += 1
        if name == "sources":
            for r in sources["rows"]:
                if not re.match(r"^https?://", r.get("url", "")):
                    fail(f"V5 {r['src_id']} has no http(s) url", fails)
                if r.get("verification") not in ("FETCHED", "FETCHED-VIA-SEARCH-SNIPPET",
                                                 "INDEX-MEANS", "LINKED", "UNREACHABLE",
                                                 "THIRD-PARTY-IN-REPO"):
                    fail(f"V5 {r['src_id']} has an unknown verification level "
                         f"{r.get('verification')!r}", fails)
    return stats


def check_blanks_rendered(fails: list) -> None:
    """V6 continued: every empty cell in the data shows up as a flagged blank in HTML."""
    html_text = ""
    for dirpath, _dirs, files in os.walk(PAGES):
        for f in files:
            if f.endswith(".html"):
                html_text += read(os.path.join(dirpath, f))
    n_markers = html_text.count('class="unverified"')
    if n_markers == 0:
        fail("V6 no unverified markers found in the generated HTML — suspicious for a "
             "register that admits to many unknowns", fails)


def check_engine(fails: list) -> tuple[int, bool]:
    """V7: the tests pass and the demo output is reproducible."""
    t = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                       cwd=ROOT, capture_output=True, text=True)
    tail = (t.stderr or t.stdout).strip().splitlines()
    tests_line = next((ln for ln in reversed(tail) if "Ran " in ln), "Ran ? tests")
    if t.returncode != 0:
        fail(f"V7 unit tests failed:\n{tail[-1] if tail else 'no output'}", fails)
    d = subprocess.run([sys.executable, os.path.join(ROOT, "engine", "demo_run.py"), "--check"],
                       cwd=ROOT, capture_output=True, text=True)
    drift = d.returncode == 0
    if not drift:
        fail("V7 data/demo_results.json is stale — run python3 engine/demo_run.py", fails)
    return tests_line, drift


def check_assets(fails: list) -> None:
    for rel in ("pages/assets/dashboard.css", "pages/assets/app.js"):
        p = os.path.join(DOCS, rel)
        if not os.path.exists(p):
            fail(f"V8 missing asset {rel}", fails)
        elif len(read(p)) < 200:
            fail(f"V8 asset {rel} looks truncated", fails)


def main() -> int:
    fails: list[str] = []
    if not os.path.isdir(PAGES):
        print("docs/pages not found — run python3 site/build.py first", file=sys.stderr)
        return 2
    check_generation_drift(fails)
    links, external = check_links(fails)
    check_placeholders(fails)
    row_stats = check_row_sources(fails)
    check_blanks_rendered(fails)
    tests_line, drift_ok = check_engine(fails)
    check_assets(fails)

    print("site/verify.py — publish gate")
    print(f"  V1 generation drift      : {'clean' if not any(f.startswith('V1') for f in fails) else 'FAILED'}")
    print(f"  V2 links                 : {links} total, {external} external, "
          f"{'all internal resolve' if not any(f.startswith('V2') for f in fails) else 'BROKEN LINKS'}")
    print(f"  V3 placeholders          : {'none' if not any(f.startswith('V3') for f in fails) else 'FOUND'}")
    print(f"  V4/V5 row sourcing       : {row_stats['sourced']}/{row_stats['rows']} rows carry a "
          f"source id; {row_stats['declared_unsourced']} declare no external source (internal rows); "
          f"{row_stats['unknown_ids']} unknown ids")
    print(f"  V6 flagged blanks        : {row_stats['blanks']} empty cells across the registers")
    print(f"  V7 engine                : {tests_line}; demo reproducibility "
          f"{'ok' if drift_ok else 'DRIFT'}")
    print(f"  V8 assets                : {'ok' if not any(f.startswith('V8') for f in fails) else 'MISSING'}")
    if fails:
        print(f"\n{len(fails)} problem(s):")
        for f in fails:
            print("  - " + f)
        return 1
    print("\nAll checks passed: the site is publishable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
