"""Shared helpers for reading this repo's pipe-delimited source snapshots.

Snapshots are deliberately not JSON: they are hand-checked transcriptions of rendered
official pages, and a line-oriented format lets a reviewer diff one row against the page it
came from. Blank means "the source printed nothing here" and is never filled in.
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
VERIFIED = ROOT / "data" / "verified"
MODEL = ROOT / "data" / "model"

OFFICIAL_HOSTS = ("nfl.com",)


def read_pipe_csv(path: Path) -> list[dict[str, str]]:
    """Parse a `|`-delimited file whose `#` lines are comments/provenance."""
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if not ln.startswith("#")]
    lines = [ln for ln in lines if ln.strip()]
    if not lines:
        return []
    reader = csv.DictReader(io.StringIO("\n".join(lines)), delimiter="|")
    rows = []
    for raw in reader:
        row = {}
        for key, value in raw.items():
            if key is None:
                raise ValueError(f"{path.name}: row has more fields than the header: {raw}")
            row[key.strip()] = (value or "").strip()
        rows.append(row)
    return rows


def is_official(url: str) -> bool:
    """True when the URL host is the league's or a club's own domain (T0/T1 source)."""
    host = re.sub(r"^https?://", "", url).split("/")[0]
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_HOSTS)


def fetch_stamp() -> str:
    """The timestamp of the fetch this snapshot came from (recorded, never `now()`)."""
    return (ROOT / "data" / "raw" / "sources.json").read_text(encoding="utf-8")


def chunk_rows(rows: list[dict], key: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for row in rows:
        out.setdefault(row[key], []).append(row)
    return out
