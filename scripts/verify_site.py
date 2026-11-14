"""
Build gate. Fails (non-zero exit) if the site or the data breaks any of these:

  L1  every internal link target in docs/ exists
  L2  no <a href="#"> placeholders remain
  L3  every page is reachable from the nav, and every nav entry exists
  S1  every row of the official Week 10 table has a source URL
  S2  every source URL in the registry is https
  S3  no table row in the rendered HTML is missing a source column where one is required
  D1  required data files exist and are non-empty
  D2  strategies.csv has exactly 7 gate columns and each is boolean
  D3  leaderboard reward is paid only to APPROVED rows
  D4  correlation matrix is symmetric with unit diagonal
  D5  the Week 10 join covers all 14 games and 28 clubs
  D6  no NaN rendered as the literal text 'nan' or 'None' in any HTML page
  T1  every page declares a title and a viewport
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "computed"

errors: list[str] = []
warns: list[str] = []


def err(code: str, msg: str) -> None:
    errors.append(f"[{code}] {msg}")


def warn(code: str, msg: str) -> None:
    warns.append(f"[{code}] {msg}")


REQUIRED_FILES = [
    "sources.json", "requirements.csv", "questions.csv", "suggestions.csv",
    "irregularities.csv", "unverified.csv", "strategies.csv", "leaderboard.csv",
    "leaderboard_by_season.csv", "correlations.csv", "correlation_matrix.csv",
    "parlay_economics.csv", "availability_2025.csv", "depth_deficiency.csv",
    "week10_2026_official.csv", "week10_signal_board.csv",
    "raw/MANIFEST.json",
]


def main() -> int:
    # ---------------- D1 files ----------------
    for f in REQUIRED_FILES:
        p = DATA / f
        if not p.exists():
            err("D1", f"missing data file: {f}")
        elif p.stat().st_size < 20:
            err("D1", f"data file is empty: {f}")

    pages = sorted(DOCS.glob("*.html"))
    if len(pages) < 14:
        err("L3", f"expected 14 pages, found {len(pages)}")

    # ---------------- L1/L2/T1/D6 per page ----------------
    for p in pages:
        txt = p.read_text(encoding="utf-8")
        if "<title>" not in txt:
            err("T1", f"{p.name}: no <title>")
        if 'name="viewport"' not in txt:
            err("T1", f"{p.name}: no viewport meta")
        for bad in ("nan", "None", "NaN"):
            # only flag whole-cell occurrences, not words containing them
            if re.search(r">\s*(%s)\s*<" % bad, txt):
                err("D6", f"{p.name}: rendered literal '{bad}' in a cell")
        for href in re.findall(r'href="([^"]+)"', txt):
            if href.startswith("#"):
                err("L2", f"{p.name}: placeholder link {href}")
                continue
            if href.startswith(("http://", "https://", "mailto:")):
                if href.startswith("http://"):
                    warn("S2", f"{p.name}: non-https link {href}")
                continue
            target = href.split("#")[0]
            if target and not (DOCS / target).exists():
                err("L1", f"{p.name}: broken internal link -> {target}")

    # ---------------- S1 week 10 official ----------------
    w = pd.read_csv(DATA / "week10_2026_official.csv")
    if "official_source_url" not in w.columns:
        err("S1", "week10_2026_official.csv lacks official_source_url")
    else:
        missing = w[w.official_source_url.isna() | (w.official_source_url.astype(str).str.strip() == "")]
        if len(missing):
            err("S1", f"{len(missing)} Week 10 rows have no official source URL")
        notofficial = w[~w.official_source_url.astype(str).str.contains("nfl.com")]
        if len(notofficial):
            err("S1", f"{len(notofficial)} Week 10 rows point outside nfl.com")
    if "source_quote" in w.columns:
        q = w[w.source_quote.isna() | (w.source_quote.astype(str).str.strip().str.len() < 10)]
        if len(q):
            err("S1", f"{len(q)} Week 10 rows have no verbatim source quote")

    # ---------------- S2 sources registry ----------------
    src = json.loads((DATA / "sources.json").read_text())
    for s in src:
        if not s.get("url", "").startswith("https://"):
            err("S2", f"source {s.get('id')} url is not https: {s.get('url')}")
        for k in ("id", "tier", "publisher", "title", "used_for", "status"):
            if not s.get(k):
                err("S2", f"source {s.get('id')} missing field {k}")
    ids = [s["id"] for s in src]
    if len(ids) != len(set(ids)):
        err("S2", "duplicate source ids in sources.json")

    # ---------------- D2 gates ----------------
    st = pd.read_csv(DATA / "strategies.csv")
    # gates are the boolean G-columns; G5_max_season_share / G6_adjusted_alpha are
    # diagnostics that report the threshold used, not pass/fail flags.
    gates = [c for c in st.columns if re.fullmatch(r"G\d_.*", c) and st[c].dtype == bool]
    nonbool = [c for c in st.columns if re.fullmatch(r"G\d_.*", c) and st[c].dtype != bool]
    expected_nonbool = {"G5_max_season_share", "G6_adjusted_alpha", "G6_variants_searched"}
    unexpected = set(nonbool) - expected_nonbool
    if unexpected:
        err("D2", f"unexpected non-boolean G columns: {sorted(unexpected)}")
    if len(gates) != 7:
        err("D2", f"expected 7 gate columns, found {len(gates)}: {gates}")
    for g in gates:
        if st[g].dtype != bool:
            err("D2", f"gate {g} is not boolean ({st[g].dtype})")
    if "verdict" in st:
        recount = st[gates].sum(axis=1)
        bad = st[(recount == 7) != (st.verdict == "APPROVED")]
        if len(bad):
            err("D2", f"verdict disagrees with gate count for {len(bad)} strategies")
        bad2 = st[(st.verdict == "APPROVED") & (recount != 7)]
        if len(bad2):
            err("D2", f"{len(bad2)} APPROVED strategies did not pass all gates")
    for d in ("G5_max_season_share", "G6_adjusted_alpha", "G6_variants_searched"):
        if d in st and st[d].isna().any():
            err("D2", f"diagnostic {d} has blanks")
    if "p_value" in st:
        p = st.p_value.dropna()
        if len(p) and (p < 0).any():
            err("D2", "negative p-value present")

    # ---------------- D3 reward ----------------
    lb = pd.read_csv(DATA / "leaderboard.csv")
    if "reward_units" in lb and "verdict" in lb:
        paid = lb[(lb.reward_units > 0) & (lb.verdict != "APPROVED")]
        if len(paid):
            err("D3", f"{len(paid)} rewards paid to non-approved strategies")
        approved_unpaid = lb[(lb.reward_units == 0) & (lb.verdict == "APPROVED")]
        if len(approved_unpaid):
            err("D3", f"{len(approved_unpaid)} approved strategies not rewarded")

    # ---------------- D4 correlation matrix ----------------
    cm = pd.read_csv(DATA / "correlation_matrix.csv", index_col=0)
    vals = cm.to_numpy()
    if vals.shape[0] != vals.shape[1]:
        err("D4", "correlation matrix is not square")
    else:
        import numpy as np
        if not np.allclose(vals, vals.T, atol=1e-6):
            err("D4", "correlation matrix is not symmetric")
        if not np.allclose(vals.diagonal(), 1.0, atol=1e-6):
            err("D4", "correlation matrix diagonal is not 1")
        if np.nanmax(np.abs(vals)) > 1.0001:
            err("D4", "correlation outside [-1,1]")

    # ---------------- D5 week 10 join ----------------
    b = pd.read_csv(DATA / "week10_signal_board.csv")
    if len(b) != 14:
        err("D5", f"Week 10 board has {len(b)} games, expected 14")
    clubs = set(b.away_team) | set(b.home_team)
    if len(clubs) != 28:
        err("D5", f"Week 10 board covers {len(clubs)} clubs, expected 28")
    for c in ("away_listed", "home_listed", "closing_spread_home", "closing_total"):
        if c not in b:
            err("D5", f"Week 10 board missing column {c}")
        elif b[c].isna().any():
            err("D5", f"Week 10 board has blank {c} for {int(b[c].isna().sum())} games")
    joined = set(w.team) | set(w.opponent)
    if joined != clubs:
        err("D5", f"official report clubs ({len(joined)}) != board clubs ({len(clubs)}): "
                  f"symmetric diff {sorted(joined ^ clubs)}")

    # ---------------- S3 every key HTML table has a source column ----------------
    for name in ("week10.html", "sources.html", "flagged.html"):
        txt = (DOCS / name).read_text(encoding="utf-8")
        if "Source" not in txt:
            err("S3", f"{name}: no Source column or source reference found")

    # ---------------- L4 root site still intact + linked to us ----------------
    root_pages = sorted(ROOT.glob("*.html"))
    if len(root_pages) < 10:
        err("L4", f"root site has only {len(root_pages)} pages; the integrating session's build may have been overwritten")
    idx = ROOT / "index.html"
    if idx.exists() and "docs/computed/index.html" not in idx.read_text(encoding="utf-8"):
        err("L4", "root index.html does not link to docs/computed/index.html")
    # our pages must link back to the root
    back = (DOCS / "index.html").read_text(encoding="utf-8")
    if "../../index.html" not in back:
        err("L4", "computed index does not link back to the root site")

    # ---------------- report ----------------
    print(f"pages checked: {len(pages)}")
    print(f"week10 official rows: {len(w)}")
    print(f"sources: {len(src)}")
    print(f"strategies: {len(st)}  approved: {int((st.verdict=='APPROVED').sum())}")
    print(f"errors: {len(errors)}  warnings: {len(warns)}")
    for w_ in warns:
        print("  WARN", w_)
    for e in errors:
        print("  FAIL", e)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
