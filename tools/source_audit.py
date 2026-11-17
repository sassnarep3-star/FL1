#!/usr/bin/env python3
"""Audit citations on rendered tables without treating a repository link as evidence.

This is a provenance *classification* tool. It never fetches the web and does not
independently verify a claim. Its official-source label means only that a row points
to a source whose registry entry is marked Official and VERIFIED.
"""
from __future__ import annotations

import csv
import html
import os
import re
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "data", "source_row_audit.tsv")
SOURCE_RE = re.compile(r"\bS\d{2,3}\b")


def load_sources(path=None):
    path = path or os.path.join(ROOT, "data", "sources.tsv")
    out = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh, delimiter="\t"):
            if len(row) >= 7 and re.fullmatch(r"S\d{2,3}", row[0]):
                out[row[0]] = {
                    "title": row[1], "publisher": row[2], "url": row[3],
                    "tier": row[4], "date": row[5], "status": row[6],
                }
    return out


class TableRows(HTMLParser):
    """Collect body rows, their plain text, cell count and outgoing hyperlinks."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None
        self.in_thead = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            self.table = []
            self.tables.append(self.table)
        elif tag == "thead":
            self.in_thead = True
        elif tag == "tbody":
            self.in_thead = False
        elif tag == "tr" and self.table is not None and not self.in_thead:
            self.row = {"text": [], "cells": [], "links": [], "blank_cells": 0}
            self.table.append(self.row)
        elif tag in ("td", "th") and self.row is not None:
            if tag == "th":
                self.row["is_header"] = True
            self.cell = {"text": [], "classes": set()}
            if attrs.get("class"):
                self.cell["classes"].update(attrs["class"].split())
        elif tag == "a" and self.row is not None:
            href = attrs.get("href", "").strip()
            if href:
                self.row["links"].append(href)

    def handle_endtag(self, tag):
        if tag == "thead":
            self.in_thead = False
        elif tag in ("td", "th") and self.cell is not None:
            text = " ".join("".join(self.cell["text"]).split())
            self.cell["text"] = text
            self.row["cells"].append(self.cell)
            self.row["text"].append(text)
            self.cell = None
        elif tag == "tr":
            if self.row is not None and self.row.get("is_header") and self.table:
                self.table.pop()
            self.row = None
        elif tag == "table":
            self.table = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"].append(data)


def official_source(source):
    return (source.get("status", "").upper() == "VERIFIED"
            and source.get("tier", "").lower().startswith("official"))


def classify(row, sources):
    links = row["links"]
    source_ids = sorted(set(SOURCE_RE.findall(" ".join(row["text"] + links))))
    registered = [sources[sid] for sid in source_ids if sid in sources]
    direct_urls = [u for u in links if u.startswith(("http://", "https://"))]
    # A rendered direct link to a URL already present in the registry has the
    # same provenance as the registry chip. Match exact URLs only; do not infer
    # trust from a familiar-looking domain or a sibling page.
    known_by_url = {item.get("url"): (sid, item) for sid, item in sources.items() if item.get("url")}
    for url in direct_urls:
        match = known_by_url.get(url)
        if match and match[0] not in source_ids:
            source_ids.append(match[0])
            registered.append(match[1])
    source_ids.sort()

    visible = [c for c in row["cells"] if c["text"] and c["text"] not in {"—", "-", "–", "N/A", "na"}
               and "blank" not in c["classes"] and "na" not in c["classes"]]
    if not visible:
        status = "BLANK_NO_VALUE"
    elif registered:
        official = [official_source(s) for s in registered]
        if all(official) and len(registered) == len(source_ids):
            status = "OFFICIAL_REGISTERED"
        elif any(official):
            status = "MIXED_OR_UNRESOLVED_REGISTERED"
        elif any(s.get("status", "").upper() != "VERIFIED" for s in registered):
            status = "REGISTERED_NOT_VERIFIED"
        else:
            status = "NONOFFICIAL_REGISTERED"
    elif direct_urls:
        if any("github.com/sassnarep3-star/FL1/" in u for u in direct_urls):
            status = "REPOSITORY_LINK_ONLY"
        else:
            status = "DIRECT_LINK_UNREGISTERED"
    else:
        status = "NO_SOURCE_LINK"

    refs = []
    for sid in source_ids:
        if sid in sources:
            refs.append(sources[sid]["url"])
        else:
            refs.append("UNREGISTERED:" + sid)
    refs.extend(direct_urls)
    return status, source_ids, sorted(set(refs))


def audit_pages(root=None, sources=None):
    root = root or ROOT
    sources = sources if sources is not None else load_sources()
    results = []
    for filename in sorted(os.listdir(root)):
        if not filename.endswith(".html") or filename == "source-audit.html":
            continue
        parser = TableRows()
        with open(os.path.join(root, filename), encoding="utf-8") as fh:
            parser.feed(fh.read())
        for table_no, rows in enumerate(parser.tables, 1):
            for row_no, row in enumerate(rows, 1):
                status, source_ids, urls = classify(row, sources)
                results.append({
                    "page": filename,
                    "table": str(table_no),
                    "row": str(row_no),
                    "status": status,
                    "source_ids": ",".join(source_ids),
                    "source_urls": " | ".join(urls),
                    "row_text": " | ".join(row["text"]).strip()[:320].rstrip(),
                })
    return results


def write_tsv(rows, path=None):
    path = path or OUTPUT
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fields = ["page", "table", "row", "status", "source_ids", "source_urls", "row_text"]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def render(host_module):
    """Write the audit data and its dashboard page using the shared site shell."""
    sources = load_sources()
    rows = audit_pages(sources=sources)
    write_tsv(rows)
    counts = Counter(row["status"] for row in rows)

    def esc(value):
        return host_module.esc(value)

    summary_rows = []
    for key in ("OFFICIAL_REGISTERED", "MIXED_OR_UNRESOLVED_REGISTERED",
                "NONOFFICIAL_REGISTERED", "REGISTERED_NOT_VERIFIED",
                "REPOSITORY_LINK_ONLY", "DIRECT_LINK_UNREGISTERED",
                "NO_SOURCE_LINK", "BLANK_NO_VALUE"):
        summary_rows.append([host_module.cell(key), host_module.cell(counts.get(key, 0), "n")])

    findings = [r for r in rows if r["status"] in {
        "REPOSITORY_LINK_ONLY", "DIRECT_LINK_UNREGISTERED", "NO_SOURCE_LINK",
        "REGISTERED_NOT_VERIFIED", "MIXED_OR_UNRESOLVED_REGISTERED",
    }]
    # Show a balanced sample so a large generator-link class cannot crowd out
    # more severe missing/uncertain classes from the human-readable page.
    by_status = {}
    for r in findings:
        by_status.setdefault(r["status"], []).append(r)
    detail_sample = []
    for status in ("NO_SOURCE_LINK", "REGISTERED_NOT_VERIFIED", "DIRECT_LINK_UNREGISTERED",
                   "MIXED_OR_UNRESOLVED_REGISTERED", "REPOSITORY_LINK_ONLY"):
        detail_sample.extend(by_status.get(status, [])[:24])
    detail_rows = []
    for r in detail_sample:
        refs = []
        for sid in filter(None, r["source_ids"].split(",")):
            refs.append(host_module.src_link(sid, sources))
        for url in r["source_urls"].split(" | "):
            if url.startswith(("https://", "http://")):
                refs.append('<a href="%s" rel="noopener" target="_blank">link</a>' % esc(url))
        detail_rows.append([
            host_module.cell(r["page"] + " · table " + r["table"] + " · row " + r["row"]),
            host_module.cell(r["status"]),
            host_module.cell(r["row_text"]),
            host_module.raw_src(" ".join(refs) or '<span class="muted">none</span>'),
        ])

    lead = ("This page audits citation metadata in the currently rendered tables. It does not fetch or "
            "validate external pages. An official label means only that the row points to a registry "
            "entry marked Official and VERIFIED; it is not a fresh live-source verification.")
    body = [
        "<section><h1>Row-Level Source Audit</h1><p class=\"lead\">%s</p>" % esc(lead),
        "<div class=\"callout warn\"><p><strong>Important finding:</strong> a link to this repository's "
        "generator code is provenance for how a page was rendered, not an official source for the row's "
        "underlying facts. Such rows are explicitly classified <code>REPOSITORY_LINK_ONLY</code> and must "
        "not be treated as officially verified. This report does not silently upgrade any source.</p></div></section>",
        "<section><h2>Classification counts</h2>%s</section>" % host_module.table(
            ["Row classification", "Rows"], summary_rows, cls="dense"),
        "<section><h2>Review findings</h2><p class=\"caption\">The table below shows up to 24 entries per review class so small categories remain visible. "
        "The full deterministic row-by-row ledger is <a href=\"data/source_row_audit.tsv\">data/source_row_audit.tsv</a>. "
        "All table rows are classified there; none of the classifications claim a live fetch.</p>%s</section>" %
        host_module.table(["Location", "Classification", "Rendered row text", "Registered source links"],
                          detail_rows, cls="dense searchable"),
        "<section><h2>How to read this</h2><ul>"
        "<li><code>OFFICIAL_REGISTERED</code>: every extracted source ID resolves to a VERIFIED Official registry entry.</li>"
        "<li><code>NONOFFICIAL_REGISTERED</code>: citations resolve, but at least one is not classified Official.</li>"
        "<li><code>REGISTERED_NOT_VERIFIED</code>: a citation exists but registry status is not VERIFIED.</li>"
        "<li><code>REPOSITORY_LINK_ONLY</code>: the only detected source is a FL1 code/artifact URL.</li>"
        "<li><code>DIRECT_LINK_UNREGISTERED</code>: an external link exists, but it is not tied to a source registry entry.</li>"
        "<li><code>NO_SOURCE_LINK</code>: the populated row has no detected citation.</li>"
        "<li><code>BLANK_NO_VALUE</code>: no nonblank value is published on the row.</li>"
        "</ul><p>These checks are syntactic and registry-based. Official sites must still be opened and the underlying fact checked before any strategy or line is trusted.</p></section>"
    ]
    filename = host_module.page("source-audit.html", "Row-Level Source Audit", "".join(body), wide=True)
    return filename, counts, len(rows)


if __name__ == "__main__":
    audit = audit_pages()
    write_tsv(audit)
    print("audited %d table rows into %s" % (len(audit), OUTPUT))
