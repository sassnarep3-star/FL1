#!/usr/bin/env python3
"""
pdf_to_text.py — render captured official PDFs to text, for the parser to read.

WHY A SEPARATE SCRIPT
    The repository's runtime is standard-library only (see requirements.txt). PDF
    text extraction genuinely needs a third-party parser, and rather than smuggle
    a dependency into the runtime this step is isolated here and run **only in CI**,
    where the dependency is declared in `.github/workflows/capture-official.yml`.

    The output is plain text committed to the vault, so every downstream parser in
    this repository stays stdlib-only and byte-reproducible.

WHAT IT WRITES
    For every `*.pdf` under the given directory it writes a sibling `*.txt`
    alongside the PDF. The text is the PDF's text layer, extracted page by page,
    with a page marker so a parser can cite the page a fact came from.

Usage
    python3 scripts/pdf_to_text.py ../vault/pdf
"""

from __future__ import annotations

import os
import sys
import traceback


def extract(path: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:                                  # pragma: no cover
        try:
            from PyPDF2 import PdfReader                  # type: ignore
        except ImportError:
            raise SystemExit(
                "pdf_to_text.py needs a PDF parser. Run it in CI where the "
                "workflow installs one, or `pip install pypdf` locally.")
    reader = PdfReader(path)
    out = []
    for i, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            text = f"[page {i} extraction failed: {exc}]"
        out.append(f"\n===== PAGE {i} =====\n{text}")
    return "".join(out)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2
    root = argv[0]
    ok = fail = 0
    for dirpath, _dirs, files in os.walk(root):
        for name in sorted(files):
            if not name.lower().endswith(".pdf"):
                continue
            pdf = os.path.join(dirpath, name)
            txt = pdf[:-4] + ".txt"
            if os.path.exists(txt) and os.path.getsize(txt) > 0:
                continue
            try:
                text = extract(pdf)
            except Exception:
                traceback.print_exc()
                fail += 1
                continue
            if not text.strip():
                print(f"EMPTY  {pdf}")
                fail += 1
                continue
            with open(txt, "w", encoding="utf-8") as fh:
                fh.write(text)
            ok += 1
    print(f"pdf_to_text: {ok} written, {fail} failed")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
