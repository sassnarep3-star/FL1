"""Fetch and pin the raw inputs used by every calculation in this repo.

Run:  python3 scripts/fetch_data.py
Pins each file with a SHA-256 + row count into data/raw/MANIFEST.json so that
any downstream number can be re-derived and audited.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
import urllib.error

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

NFD = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/"
NFD_FILES = ["games.csv", "closing_lines.csv", "sc_lines.csv", "rosters.csv", "win_totals.csv"]


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: pathlib.Path) -> str:
    """Return status string. Falls back to git clone of the repo when raw is blocked."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "fl1-research/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        dest.write_bytes(data)
        return "http"
    except Exception as exc:  # noqa: BLE001
        return f"FAILED: {type(exc).__name__}"


def main() -> int:
    manifest = {"generated_by": "scripts/fetch_data.py", "files": []}

    # 1. nflverse/nfldata --------------- raw.githubusercontent may be blocked; clone instead.
    clone_dir = pathlib.Path("/tmp/_nfldata_clone")
    need_clone = True
    for f in NFD_FILES:
        dest = RAW / f
        if dest.exists() and dest.stat().st_size > 0:
            continue
        need_clone = True
        break
    else:
        need_clone = False

    if need_clone:
        if clone_dir.exists():
            shutil.rmtree(clone_dir)
        subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/nflverse/nfldata", str(clone_dir)],
            check=True, capture_output=True,
        )
        for f in NFD_FILES:
            src = clone_dir / "data" / f
            if src.exists():
                shutil.copy(src, RAW / f)

    for f in NFD_FILES:
        p = RAW / f
        if p.exists():
            with open(p, encoding="utf-8") as fh:
                n = sum(1 for _ in fh) - 1
            manifest["files"].append({
                "file": f,
                "source_url": NFD + f,
                "source_repo": "https://github.com/nflverse/nfldata",
                "sha256": sha256(p),
                "rows": n,
                "bytes": p.stat().st_size,
                "transport": "git clone (raw.githubusercontent blocked)",
            })
        else:
            print(f"MISSING {f}", file=sys.stderr)

    # 2. injuries_2025 via third-party mirror (release CDN blocked, see COORDINATION.md)
    inj_dest = RAW / "injuries_2025.csv"
    if not inj_dest.exists() or inj_dest.stat().st_size == 0:
        url = "https://raw.githubusercontent.com/mgiancola9/nfl-predictions/main/data/raw/injuries_2025.csv"
        st = download(url, inj_dest)
        if st != "http":
            mirror = pathlib.Path("/tmp/_pred_clone")
            if mirror.exists():
                shutil.rmtree(mirror)
            subprocess.run(["git", "clone", "--depth", "1",
                            "https://github.com/mgiancola9/nfl-predictions", str(mirror)],
                           check=True, capture_output=True)
            shutil.copy(mirror / "data" / "raw" / "injuries_2025.csv", inj_dest)
    if inj_dest.exists():
        with open(inj_dest, encoding="utf-8") as fh:
            n = sum(1 for _ in fh) - 1
        manifest["files"].append({
            "file": "injuries_2025.csv",
            "source_url": "https://github.com/nflverse/nflverse-data/releases/tag/injuries",
            "mirror_url": "https://github.com/mgiancola9/nfl-predictions/blob/main/data/raw/injuries_2025.csv",
            "sha256": sha256(inj_dest),
            "rows": n,
            "bytes": inj_dest.stat().st_size,
            "note": "nflverse release CDN not reachable from sandbox; mirror used (irregularity #1)",
        })

    (RAW / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
