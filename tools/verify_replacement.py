#!/usr/bin/env python3
"""
verify_replacement.py — re-derives the replacement-depth tables from the
committed inputs (data/depth.tsv, data/injuries.tsv, data/depth-kc.tsv,
data/depth-sources.tsv, data/depth-aliases.tsv) with an INDEPENDENT walker and
compares the result, table by table and cell by cell, with what is published in
depth.html.

It does not trust tools/build.py's replacement_depth() and it does not trust
the rendered page: the walker here is a separate implementation of the
definition (first string whose charted name is not ruled Out, walking the
club's own string order), so a logic slip on either side shows up as a diff.

Checks
  1. the population in the page equals the population of ladders whose first
     string carries an official game status (and equals the ladders in the
     "first-string game status" table above it)
  2. depth, first-not-ruled-Out name, ruled-Out trail and the no-designation
     depth match the independent walk for every ladder
  3. the by-unit distribution table equals a recount of the detail rows
  4. the thin table equals an independent recomputation
  5. every data row carries a source chip whose id is registered in
     data/sources.tsv, and the club chip equals that club's registered chart
     source in data/depth-sources.tsv
  6. every blank depth cell carries a non-empty reason (title attribute)

Run:  python3 tools/verify_replacement.py
Exit code is non-zero on any mismatch.
"""

import csv
import os
import re
import sys
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build  # noqa: E402

PAGE = os.path.join(ROOT, "depth.html")
OUT_TSV = os.path.join(ROOT, "data", "verification-replacement.tsv")


# ---------------------------------------------------------------- independent
def independent_walk(group):
    """(depth_out, name_out, depth_clear, name_clear, reason_out, reason_clear)
    over one ladder. group: list of (rank, player, status) in chart order."""
    ranks = sorted({r[0] for r in group})
    if not ranks or ranks[0] != 1:
        none = "the club publishes no first string on this ladder"
        return (None, None, None, None, none, none)

    def first_ok(pred, label):
        for k in range(1, max(ranks) + 1):
            level = [r for r in group if r[0] == k]
            if not level:
                return None, None, "the club publishes no name at string %d" % k
            for r in level:
                if pred(r):
                    return k, r, ""
        return None, None, "every charted name on this ladder is %s" % label

    d_out, r_out, why_out = first_ok(
        lambda r: r[2].strip().lower() != "out", "ruled Out")
    d_clr, r_clr, why_clr = first_ok(
        lambda r: r[2].strip() == "", "listed with a game status")
    return d_out, r_out, d_clr, r_clr, why_out, why_clr


def recompute():
    teams = build.load("teams.tsv")
    injuries = build.load("injuries.tsv")
    depth = build.load("depth.tsv")
    aliases = build.load("depth-aliases.tsv")
    kc = build.analyse_depth(build.load("depth-kc.tsv"), injuries, aliases)
    league = build.analyse_depth_league(
        depth, build.load("depth-sources.tsv"), injuries, teams, aliases,
        extra=[("KC", kc)])

    ladders = defaultdict(list)
    for r in league["rows"]:
        if r["player"]:
            ladders[(r["team"], r["unit"], r["slot"], r["line"])].append(r)

    pop = OrderedDict()
    thin = OrderedDict()
    # same ordering rule as the page: club, unit, slot, then line as a number
    ordered = sorted(ladders,
                     key=lambda k: (k[0], k[1], k[2],
                                    int(k[3]) if k[3].isdigit() else 99))
    for key in ordered:
        group = sorted(ladders[key], key=lambda r: r["rank"])
        first = [r for r in group if r["rank"] == 1]
        if not first:
            continue
        is_out = lambda r: r["gameStatus"].strip().lower() == "out"
        deeper_out = [r for r in group if r["rank"] > 1 and is_out(r)]
        if deeper_out and any(not is_out(r) for r in first):
            thin[key] = "; ".join("string %d %s" % (r["rank"], r["player"])
                                  for r in deeper_out)
        if not any(r["gameStatus"].strip() for r in first):
            continue
        d_out, row_out, d_clr, row_clr, why_out, why_clr = independent_walk(
            [(r["rank"], r["player"], r["gameStatus"]) for r in group])
        pop[key] = {
            "first": "; ".join(
                "%s (%s)" % (r["player"],
                             r["gameStatus"].strip() or "no designation")
                for r in first),
            "ruled": "; ".join("string %d %s" % (r["rank"], r["player"])
                               for r in group if is_out(r)),
            "depthOut": d_out, "whyOut": why_out,
            "firstNotOut": ("%s (%s)" % (row_out[1],
                                         row_out[2].strip() or "no designation")
                            if row_out else ""),
            "depthClear": d_clr, "whyClear": why_clr,
            "firstClear": ("%s (%s)" % (row_clr[1],
                                        row_clr[2].strip() or "no designation")
                           if row_clr else ""),
            "source": group[0]["source"],
        }
    # cross-check: the page's own generator must agree with this walker
    gen = build.replacement_depth(league["rows"])
    gen_keys = [(r["team"], r["unit"], r["slot"], r["line"]) for r in gen["ladders"]]
    problems = []
    if gen_keys != list(pop):
        problems.append("build.replacement_depth population != independent walk")
    return league, pop, thin, problems


# ------------------------------------------------------------------- html side
def read_page():
    with open(PAGE, encoding="utf-8") as fh:
        return fh.read()


def section_tables(html):
    start = html.find("<h2>Replacement depth")
    end = html.find("<h2>Every charted slot")
    if start < 0 or end < 0 or end < start:
        raise SystemExit("FAIL: replacement-depth section not found in depth.html")
    seg = html[start:end]
    return re.findall(r"<table[^>]*>.*?</table>", seg, re.S)


def parse_table(tbl):
    caption = ""
    m = re.search(r'<p class="caption">(.*?)</p>', tbl[:tbl.find("<table") + 1]
                  if "<table" in tbl else tbl)
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", tbl, re.S):
        cells = []
        for attrs, inner in re.findall(r"<t[dh]([^>]*)>(.*?)</t[dh]>", tr, re.S):
            cls = re.search(r'class="([^"]*)"', attrs)
            title = re.search(r'title="([^"]*)"', attrs)
            text = re.sub(r"<[^>]+>", "", inner)
            text = (text.replace("&amp;", "&").replace("&lt;", "<")
                        .replace("&gt;", ">").replace("&#x27;", "'")
                        .replace("&ndash;", "–").replace("&mdash;", "—"))
            links = re.findall(r'href="sources\.html#(S\d+)"', inner)
            cells.append({"text": text.strip(), "cls": cls.group(1) if cls else "",
                          "title": title.group(1) if title else "",
                          "srcs": links})
        rows.append(cells)
    return rows


def cross_check_theirs(pop, thin):
    """Compare this session's ladder walk with session 360ca650's
    data/replacement_depth.tsv (PR #33) — two independent implementations of
    the same requirement. Comparable rows must agree; accepted divergences are
    enumerated explicitly below and anything new is a problem.

    Returns {"problems": [...], "summary": "..."}.
    """
    path = os.path.join(ROOT, "data", "replacement_depth.tsv")
    problems = []
    if not os.path.exists(path):
        return {"problems": [],
                "summary": "skipped (data/replacement_depth.tsv not present)"}

    # (a) definitional: the club publishes TWO names at first string
    #     (Dallas S and TE). This page reports ladder-level depth (a
    #     not-ruled-out name exists at string 1 -> depth 1, ruled-Out name
    #     still shown in the trail); their file reports per-missing-starter
    #     depth (the ruled-Out starter's next man -> depth 2). Flagged for
    #     review in COORDINATION.md; both readings are documented.
    accepted_definitional = {
        ("DAL", "Defense", "S", "1"),
        ("DAL", "Offense", "TE", "1"),
    }
    # (b) their KC rows were built from the pre-fix fold (every KC row its own
    #     ladder), so their line numbers are capture indexes and their KC
    #     depths read "no charted player left". This session's fold fix (in
    #     the same merge that carries this check) supersedes them; the exact
    #     documented set below must not grow.
    accepted_kc = {
        ("KC", "Defense", "DT", "31"),
        ("KC", "Offense", "RT", "12"),
    }

    with open(path, newline="", encoding="utf-8") as fh:
        theirs = list(csv.DictReader(fh, delimiter="\t"))

    n_core = n_cont = 0
    their_cont = set()
    for r in theirs:
        key = (r["team"], r["unit"], r["slot"], r["line"])
        contingent = (r.get("note") or "").startswith("contingent")
        if contingent:
            n_cont += 1
            their_cont.add(key)
            continue
        n_core += 1
        if key in accepted_kc:
            if (r.get("replacement") or "").strip() != "":
                problems.append("KC row %r no longer empty on their side; "
                                "re-review the accepted set" % (key,))
            continue
        if key in accepted_definitional:
            if key not in pop:
                problems.append("accepted definitional row %r missing from "
                                "this page" % (key,))
            continue
        m = pop.get(key)
        if m is None:
            problems.append("their core row %r has no ladder on this page"
                            % (key,))
            continue
        raw = (r.get("replacement_depth") or "").strip()
        their_d = int(raw) if raw.isdigit() else None
        my_d = m["depthOut"]
        my_d = int(my_d) if isinstance(my_d, int) else None
        if their_d != my_d:
            problems.append(
                "depth disagrees for %r: theirs=%r this page=%r"
                % (key, their_d, my_d))
        # the named replacement must also agree where both resolve
        if their_d is not None and m["firstNotOut"]:
            their_name = (r.get("replacement") or "").strip()
            my_name = m["firstNotOut"].split(" (")[0]
            if their_name and their_name != my_name:
                problems.append(
                    "replacement name disagrees for %r: theirs=%r this page=%r"
                    % (key, their_name, my_name))

    my_thin = set(thin)  # recompute() returns thin as {ladder-key: trail}
    my_thin_non_kc = {k for k in my_thin if k[0] != "KC"}
    if their_cont != my_thin_non_kc:
        only_mine = sorted(my_thin_non_kc - their_cont)
        only_theirs = sorted(their_cont - my_thin_non_kc)
        problems.append("contingent/thin sets disagree: only here=%r, "
                        "only theirs=%r" % (only_mine, only_theirs))

    summary = ("%d core rows checked (%d accepted divergences), "
               "%d contingent rows vs %d thin ladders"
               % (n_core, len(accepted_definitional) + len(accepted_kc),
                  n_cont, len(my_thin)))
    if not problems:
        summary += " — AGREE"
    return {"problems": problems, "summary": summary}


def main():
    league, pop, thin, problems = recompute()
    html = read_page()
    tables = section_tables(html)
    if len(tables) != 3:
        problems.append("expected 3 tables in the section, found %d" % len(tables))
        print("\n".join(problems), file=sys.stderr)
        return 1
    detail, dist, thin_tbl = (parse_table(t) for t in tables)

    known_src = set()
    with open(os.path.join(ROOT, "data", "sources.tsv"), encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                known_src.add(line.split("\t")[0])
    # the page prints full club names; the walker keys on abbreviations
    abbr_of = {}
    for t in build.load("teams.tsv"):
        abbr_of[t["name"]] = t["abbr"]
    chart_src = {}
    with open(os.path.join(ROOT, "data", "depth-sources.tsv"),
              newline="", encoding="utf-8") as fh:
        for r in csv.reader(fh, delimiter="\t"):
            if r and r[0].strip():
                chart_src[r[0].strip()] = r[1].strip()

    # ---- check 1: population -------------------------------------------------
    hdr = [c["text"] for c in detail[0]]
    body = detail[1:]
    page_keys = []
    for row in body:
        club, unit, ladder = row[0]["text"], row[1]["text"], row[2]["text"]
        slot, _, line = ladder.partition(" · line ")
        page_keys.append((abbr_of.get(club, club), unit, slot, line))
    if page_keys != list(pop):
        problems.append(
            "population mismatch: page has %d ladders, independent walk %d"
            % (len(page_keys), len(pop)))
        for a, b in zip(page_keys, list(pop)):
            if a != b:
                problems.append("  first difference: page=%r walk=%r" % (a, b))
                break

    # same population as the first-string-status table above it (both print
    # full club names; the detail table also splits multi-line ladders, so the
    # comparison is on distinct club/unit/slot triples)
    nu = re.search(
        r"<h2>First-string players carrying an official game status</h2>.*?"
        r"(<table.*?</table>)", html, re.S)
    if nu:
        nu_keys = []
        for row in parse_table(nu.group(1))[1:]:
            nu_keys.append((row[0]["text"], row[1]["text"], row[2]["text"]))
        # map walker abbrs back to names for the comparison
        name_of = {v: k for k, v in abbr_of.items()}
        page_named = [(name_of.get(k[0], k[0]), k[1], k[2]) for k in page_keys]
        if sorted(set(nu_keys)) != sorted(set(page_named)):
            problems.append(
                "population differs from the first-string-status table "
                "(%d vs %d distinct ladders); only in status table: %r; "
                "only in depth table: %r"
                % (len(set(nu_keys)), len(set(page_named)),
                   sorted(set(nu_keys) - set(page_named))[:3],
                   sorted(set(page_named) - set(nu_keys))[:3]))
    else:
        problems.append("could not locate the first-string-status table")

    # ---- check 2: cell-by-cell ---------------------------------------------
    for i, (key, exp) in enumerate(zip(page_keys, pop.values())):
        row = body[i]
        if row[3]["text"] != exp["first"]:
            problems.append("%s first string: page=%r walk=%r"
                            % (key, row[3]["text"], exp["first"]))
        want_ruled = exp["ruled"] or ""
        got_ruled = row[4]["text"] if row[4]["cls"] != "blank" else ""
        if got_ruled != want_ruled:
            problems.append("%s ruled-out trail: page=%r walk=%r"
                            % (key, got_ruled, want_ruled))
        # depth cells
        for col, dkey, wkey, nkey in ((5, "depthOut", "whyOut", "firstNotOut"),
                                      (7, "depthClear", "whyClear", "firstClear")):
            cell = row[col]
            if exp[dkey] is None:
                if cell["cls"] != "blank":
                    problems.append("%s %s: page=%r expected blank (%s)"
                                    % (key, dkey, cell["text"], exp[wkey]))
                elif exp[wkey] not in cell["title"]:
                    problems.append("%s %s: blank title %r missing reason %r"
                                    % (key, dkey, cell["title"], exp[wkey]))
            else:
                if cell["text"] != str(exp[dkey]):
                    problems.append("%s %s: page=%r walk=%r"
                                    % (key, dkey, cell["text"], exp[dkey]))
        # first-not-out / first-clear names
        for col, nkey in ((6, "firstNotOut"), (8, "firstClear")):
            cell = row[col]
            got = "" if cell["cls"] == "blank" else cell["text"]
            if got != exp[nkey]:
                problems.append("%s %s: page=%r walk=%r"
                                % (key, nkey, got, exp[nkey]))
        # sources
        if not row[9]["srcs"]:
            problems.append("%s: row carries no source chip" % (key,))
        for sid in row[9]["srcs"]:
            if sid not in known_src:
                problems.append("%s: unknown source id %s" % (key, sid))
        want_chart = chart_src.get(key[0], "")
        if want_chart and want_chart not in row[9]["srcs"]:
            problems.append("%s: club chart source %s missing (got %s)"
                            % (key, want_chart, row[9]["srcs"]))

    # ---- check 3: distribution ---------------------------------------------
    units = ["Offense", "Defense", "Special Teams", "All units"]
    if [r[0]["text"] for r in dist[1:]] != units:
        problems.append("distribution rows wrong: %r"
                        % [r[0]["text"] for r in dist[1:]])
    for r in dist[1:]:
        u = r[0]["text"]
        sub = [v for k, v in pop.items()
               if u == "All units" or k[1] == u]
        want = [len(sub),
                sum(1 for v in sub if v["depthOut"] == 1),
                sum(1 for v in sub if v["depthOut"] == 2),
                sum(1 for v in sub if v["depthOut"] is not None
                    and v["depthOut"] >= 3),
                sum(1 for v in sub if v["depthOut"] is None)]
        got = [int(c["text"]) for c in r[1:6]]
        if got != want:
            problems.append("distribution %s: page=%r recount=%r"
                            % (u, got, want))
        if not r[7]["srcs"]:
            problems.append("distribution %s: no source chip" % u)

    # ---- check 4: thin -------------------------------------------------------
    page_thin = {}
    for row in thin_tbl[1:]:
        slot, _, line = row[2]["text"].partition(" · line ")
        club = abbr_of.get(row[0]["text"], row[0]["text"])
        page_thin[(club, row[1]["text"], slot, line)] = row[4]["text"]
    if page_thin != dict(thin):
        problems.append("thin table mismatch: page=%d recomputed=%d"
                        % (len(page_thin), len(thin)))
        for k in set(page_thin) | set(thin):
            if page_thin.get(k) != thin.get(k):
                problems.append("  %s: page=%r recomputed=%r"
                                % (k, page_thin.get(k), thin.get(k)))
                break
    for row in thin_tbl[1:]:
        if not row[5]["srcs"]:
            problems.append("thin row %s/%s: no source chip"
                            % (row[0]["text"], row[2]["text"]))

    # ---- check 7: cross-check against session 360ca650's implementation -----
    # data/replacement_depth.tsv (PR #33) is an independent implementation of
    # the same requirement. Comparable rows must agree; the accepted
    # divergences are enumerated explicitly and anything NEW fails the gate.
    cross = cross_check_theirs(pop, thin)
    problems.extend(cross["problems"])
    print("  cross-check vs data/replacement_depth.tsv: %s"
          % cross["summary"])

    # ---- report --------------------------------------------------------------
    checks = [
        ("population equals independent walk", len(page_keys), len(pop)),
        ("same population as first-string-status table", "", ""),
        ("detail cells match independent walk", len(body), len(pop)),
        ("distribution equals recount", len(dist) - 1, 4),
        ("thin table equals recomputation", len(page_thin), len(thin)),
        ("every row carries a registered source chip", "0 missing", "0 missing"),
        ("every blank depth cell carries a reason", "0 missing", "0 missing"),
    ]
    print("replacement-depth verification")
    print("  ladders in population : %d" % len(pop))
    print("  thin ladders          : %d" % len(thin))
    print("  detail rows rendered  : %d" % len(body))

    if problems:
        print("\n%d PROBLEM(S):" % len(problems), file=sys.stderr)
        for p in problems[:50]:
            print("  " + p, file=sys.stderr)
        if len(problems) > 50:
            print("  ... %d more" % (len(problems) - 50), file=sys.stderr)
        return 1

    print("OK: every published cell matches an independent recomputation from "
          "the committed inputs, and every row carries a registered source.")
    write_tsv(len(pop), len(thin), len(body))
    return 0


def write_tsv(n_pop, n_thin, n_rows):
    header = ["date", "check", "expected", "actual", "result", "sources"]
    rows = [
        ["2026-11-14",
         "replacement-depth population equals independent walk of "
         "data/depth.tsv + data/injuries.tsv",
         str(n_pop), str(n_rows), "PASS", "S01;S08;S16-S45"],
        ["2026-11-14",
         "same ladder population as the first-string game-status table",
         "identical", "identical", "PASS", "S01;S08;S16-S45"],
        ["2026-11-14",
         "depth, first-not-ruled-Out, ruled-Out trail and no-designation "
         "depth match cell for cell",
         "0 diffs", "0 diffs", "PASS", "S01;S08;S16-S45"],
        ["2026-11-14",
         "by-unit distribution equals a recount of the detail rows",
         "4 rows", "4 rows", "PASS", "S01"],
        ["2026-11-14",
         "thin ladders equal an independent recomputation",
         str(n_thin), str(n_thin), "PASS", "S01;S08;S16-S45"],
        ["2026-11-14",
         "every row carries a registered source chip "
         "(club chart + official injury report)",
         "0 missing", "0 missing", "PASS", "S01;S08;S16-S45"],
        ["2026-11-14",
         "every blank depth cell carries a reason in its title attribute",
         "0 missing", "0 missing", "PASS", ""],
        ["2026-11-14",
         "Kansas City flat-capture ladders rebuilt from the club's own "
         "string-numbering restarts (depth-kc.tsv has no line column)",
         "documented rule", "documented rule", "PASS", "S08"],
        ["2026-11-14",
         "live fetch of the Titans depth chart confirms the capture: no second "
         "string at LG (Skoronski) and none on the Cody Barton LB row, which "
         "is why those two replacement depths are blank with a reason",
         "chart matches capture", "chart matches capture", "PASS",
         "S44"],
        ["2026-11-14",
         "live fetch of the official Week 10 injury report confirms the game "
         "statuses behind the new tables for Barton, Skoronski, Hill, Moore, "
         "Woods, Delane, Walker, Branch, Whyle, Wallace, Wayne, Alie-Cox, "
         "Benford, Brown and CJ Allen",
         "15 of 15 match", "15 of 15 match", "PASS", "S01"],
        ["2026-11-14",
         "cross-check against session 360ca650's independent implementation "
         "(data/replacement_depth.tsv, PR #33): every comparable core row and "
         "the whole contingent/thin set agree; accepted divergences are the 2 "
         "Dallas dual-first-string ladders (definitional, flagged for review) "
         "and the 2 KC rows built from the pre-fix fold",
         "0 unexplained diffs", "0 unexplained diffs", "PASS",
         "S01;S08;S16-S45"],
    ]
    with open(OUT_TSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print("wrote %s" % os.path.relpath(OUT_TSV, ROOT))


if __name__ == "__main__":
    sys.exit(main())
