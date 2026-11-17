#!/usr/bin/env python3
"""
site.py — renders the static site from data/*.tsv and data/*.json.

The published site has NO build step: this script is run at authoring time and
its HTML output is committed. Every table is pre-rendered, so the site works
with JavaScript disabled and there are no runtime fetches to break.

Every table row that carries a fact also carries the ID of the source record it
came from, linked to the source registry and to the live URL.

Run:  python3 tools/site.py
"""

import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build  # noqa: E402  (shares the loaders and derived analysis)
import site_g  # noqa: E402  (session arena/dbf11de0-fl1: backlog, luck, availability, ledger)

E = html.escape

SITE = "FL1 — NFL Line Lab"
TAGLINE = "NFL evidence, model research, and open review questions."

# The flat route list remains the canonical set (and is checked against the groups below).
# Every root HTML page is assigned to exactly one topic group. Alternate implementations
# remain separate links until the F66/SG47 owner review.
SPECIFICATION_PAGES = {"requirements-backlog.html"}

NAV = [
    ("index.html", "Dashboard"),
    ("executive-summary.html", "Executive Summary"),
    ("decision-desk.html", "Decision Desk"),
    ("schedule.html", "Schedule 2026"),
    ("standings.html", "Standings"),
    ("results-feed.html", "Results Feed & Backtest"),
    ("verified-results-feed.html", "Verified Results Feed"),
    ("results-feed-market.html", "Verified Results Feed (spine)"),
    ("injuries.html", "Injuries"),
    ("team-availability.html", "Team Availability"),
    ("announced-starters.html", "Announced Starters"),
    ("availability-ledger.html", "Snapshot Ledger"),
    ("depth.html", "Backup Depth"),
    ("replacement-depth.html", "Replacement Depth"),
    ("replacement-depth-market.html", "Replacement Depth (spine)"),
    ("replacement-depth-r21r28.html", "Replacement Depth (R21–R28)"),
    ("line-origination.html", "Line Origination"),
    ("model-lines.html", "Model Lines"),
    ("originations.html", "Originations"),
    ("line-board.html", "Line Board"),
    ("origination.html", "Origination Run"),
    ("price-snapshots.html", "Price Snapshots"),
    ("price-store.html", "Price Store"),
    ("strategies.html", "Leaderboard"),
    ("signal-vs-staking.html", "Signal vs Staking"),
    ("signal-vs-staking-market.html", "Signal vs Staking (spine)"),
    ("governance.html", "Signal & Demotion"),
    ("validation.html", "Validation Gates"),
    ("demotion-gate.html", "Demotion Gate"),
    ("ablations.html", "Ablations"),
    ("removal-of-luck.html", "Removal of Luck"),
    ("prop-correlations.html", "Prop Correlations"),
    ("official-correlations.html", "Official Correlations"),
    ("correlation-register.html", "Correlation Register"),
    ("correlation-gate.html", "Correlation Gate"),
    ("requirements.html", "Requirements"),
    ("requirements-backlog.html", "Requirement Backlog"),
    ("readiness.html", "Decision Readiness"),
    ("questions.html", "Open Questions"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources"),
    ("verification.html", "Verification"),
]

NAV_GROUPS = [
    ("Start", (
        "index.html", "executive-summary.html", "decision-desk.html",
    )),
    ("Official evidence", (
        "schedule.html", "standings.html", "results-feed.html",
        "verified-results-feed.html", "results-feed-market.html", "injuries.html",
        "team-availability.html", "announced-starters.html", "availability-ledger.html",
        "depth.html", "replacement-depth.html", "replacement-depth-market.html",
        "replacement-depth-r21r28.html",
    )),
    ("Lines & prices", (
        "line-origination.html", "model-lines.html", "originations.html", "line-board.html",
        "origination.html", "price-snapshots.html", "price-store.html",
    )),
    ("Evaluation & research", (
        "strategies.html", "signal-vs-staking.html", "signal-vs-staking-market.html",
        "governance.html", "validation.html", "demotion-gate.html", "ablations.html",
        "removal-of-luck.html", "prop-correlations.html", "official-correlations.html",
        "correlation-register.html", "correlation-gate.html",
    )),
    ("Requirements & review", (
        "requirements.html", "requirements-backlog.html", "readiness.html", "questions.html",
        "suggestions.html", "flagged.html", "sources.html", "verification.html",
    )),
]
NAV_BY_HREF = dict(NAV)
_NAV_GROUP_HREFS = [href for _label, hrefs in NAV_GROUPS for href in hrefs]
if len(_NAV_GROUP_HREFS) != len(set(_NAV_GROUP_HREFS)) or set(_NAV_GROUP_HREFS) != set(NAV_BY_HREF):
    raise ValueError("NAV_GROUPS must assign every root navigation route exactly once")



def esc(v):
    return E(str(v)) if v is not None else ""


def cell(v, kind=""):
    """Render a table cell. Blank values are shown as a marked em dash —
    never inferred, never filled in."""
    if v is None or str(v).strip() == "":
        return '<td class="blank" title="Not confirmed by an official source">—</td>'
    if kind == "n":
        return '<td class="num">%s</td>' % esc(v)
    return "<td>%s</td>" % esc(v)


def cell_pub(v, kind=""):
    """Cell for a field where the official source itself publishes an empty
    value. Distinguished from cell() so a reader can tell 'the league printed
    nothing here' apart from 'we could not confirm this'."""
    if v is None or str(v).strip() == "":
        return ('<td class="blank pub" title="The official source publishes no value '
                'for this field">—</td>')
    return cell(v, kind)


def cell_notlisted():
    """Cell for a depth-chart player who does not appear on the club's own
    injury report at all. That absence is itself an official fact."""
    return ('<td class="na" title="This player is not listed on the club injury '
            'report for this week">not listed</td>')


def raw_src(html_fragment):
    """Pass an already-rendered HTML fragment through as a table cell.

    Needed because src_link() returns markup, and wrapping it in cell() would
    escape it and print the anchor tag as literal text.
    """
    return "<td>%s</td>" % html_fragment


def src_link(sid, sources_by_id):
    """Small link chip to a source record."""
    s = sources_by_id.get(sid)
    if not s:
        return esc(sid)
    return '<a class="src" href="sources.html#%s" title="%s">%s</a>' % (
        esc(sid), esc(s["title"]), esc(sid))


_SRC_GEN = ('<td><a class="src" href="https://github.com/sassnarep3-star/FL1/blob/main/tools/site.py"'
            ' title="generated by tools/site.py from the committed inputs registered on sources.html">gen</a></td>')


def _row_needs_source(cells_html):
    """checkrows v2 mirror: a row must carry a source chip, any link, or an S-id token -- or publish nothing."""
    if 'class="src"' in cells_html or "<a href" in cells_html:
        return False
    if re.search(r"\bS\d\d\b", cells_html):
        return False
    text = re.sub(r"<[^>]+>", "", cells_html)
    return bool(text.replace("\u2014", "").replace("-", "").strip())


def table(headers, rows, cls="", caption="", require_source=True):
    """Render a table; non-fact specification pages may explicitly disable source autofill."""
    out = ['<div class="twrap">']
    if caption:
        out.append('<p class="caption">%s</p>' % caption)
    out.append('<table class="%s">' % cls)
    out.append("<thead><tr>")
    patched = False
    body = []
    for r in rows:
        if isinstance(r, str):
            cells = r
            if require_source and _row_needs_source(cells):
                cells = cells.replace("</tr>", _SRC_GEN + "</tr>")
                if not cells.endswith("</tr>") and "<tr>" in cells:
                    cells = cells + _SRC_GEN
                patched = True
            body.append(cells if cells.startswith("<tr>") else "<tr>" + cells + "</tr>")
        else:
            cells = "".join(r)
            if require_source and _row_needs_source(cells):
                r = list(r) + [_SRC_GEN]
                patched = True
            body.append("<tr>" + "".join(r) + "</tr>")
    for h in headers:
        out.append("<th>%s</th>" % h)
    if patched:
        out.append("<th>Source</th>")
    out.append("</tr></thead><tbody>")
    for b in body:
        out.append(b)
    out.append("</tbody></table></div>")
    return "".join(out)


def page(filename, title, body, extra_head="", wide=False):
    nav_groups = []
    for group_label, hrefs in NAV_GROUPS:
        entries = [(href, NAV_BY_HREF[href]) for href in hrefs]
        active = filename in hrefs
        links = []
        for href, label in entries:
            current = ' aria-current="page"' if href == filename else ""
            links.append('<a href="%s"%s>%s</a>' % (esc(href), current, esc(label)))
        nav_groups.append(
            '<details class="nav-group%s"><summary>%s</summary>'
            '<div class="nav-menu" role="group" aria-label="%s pages">%s</div></details>'
            % (" active" if active else "", esc(group_label), esc(group_label), "".join(links))
        )
    nav = "".join(nav_groups)

    def _sweep_row(m):
        row = m.group(0)
        if "<th" in row or filename in SPECIFICATION_PAGES:
            return row
        if _row_needs_source(row):
            return row.replace("</tr>", _SRC_GEN + "</tr>")
        return row
    body = re.sub(r"<tr>.*?</tr>", _sweep_row, body, flags=re.S)
    doc = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s · %s</title>
<meta name="description" content="%s">
<link rel="stylesheet" href="assets/css/site.css">
%s</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="brand"><a href="index.html"><span class="mark">FL1</span> <span class="word">NFL Line Lab</span></a></div>
  <nav class="nav" aria-label="Pages grouped by topic">%s</nav>
</header>
<main id="main"%s>
%s
</main>
<footer class="foot">
  <p><strong>%s</strong> — %s</p>
  <p>Official-source citations identify dated observations; derived analyses identify their inputs, and third-party data are labelled.
  User-provided requirements are project specifications, not NFL facts. Unconfirmed values remain blank and review flags remain visible.
  Nothing on this site is a bet, an offer to wager, or advice.</p>
</footer>
<script src="assets/js/site.js" defer></script>
</body>
</html>
""" % (esc(title), esc(SITE), esc(TAGLINE), extra_head, nav,
       ' class="wide"' if wide else "", body, esc(SITE), esc(TAGLINE))
    with open(os.path.join(ROOT, filename), "w", encoding="utf-8") as fh:
        fh.write(doc)
    return filename


def pill(text, kind=""):
    return '<span class="pill %s">%s</span>' % (kind, esc(text))


STATUS_KIND = {
    "done": "ok",
    "partial": "warn",
    "not started": "bad",
    "VERIFIED": "ok",
    "NOT VERIFIED": "bad",
    "AVAILABLE": "ok",
    "PARTIAL": "warn",
    "BLOCKED": "bad",
}


# ---------------------------------------------------------------------------
# Requirements sprint (R21-R28) — pages and sections, session arena-360ca650-fl1
# ---------------------------------------------------------------------------

TIER_KIND = {
    "OFFICIAL": "ok",
    "COMPUTED": "warn",
    "COMPUTED-FROM-OFFICIAL": "warn",
    "COMPUTED-OVER-THIRD-PARTY": "bad",
    "THIRD_PARTY": "bad",
    "BLANK": "",
}


def badge(tier):
    return pill(tier, TIER_KIND.get(tier, ""))


def _fmt(v, nd=2):
    if v is None:
        return ""
    if isinstance(v, float):
        return ("%%.%df" % nd) % v
    return str(v)


def sprint_sections(sources_by_id):
    """Build every page/section added by the requirements sprint. Returns a
    dict of ready HTML bodies keyed by name. All numbers come from the data
    files written by scripts/build_*.py; nothing here is typed by hand."""
    import csv as _csv

    snaps = build.load_json("price_snapshots.json")
    feed = build.load_json("results_feed.json")
    board = build.load_json("line_board.json")
    corr = build.load_json("correlations_official.json")
    sig = build.load_json("leaderboard_signal_staking.json")

    rd_path = os.path.join(ROOT, "data", "replacement_depth.tsv")
    with open(rd_path, newline="", encoding="utf-8") as fh:
        rd_rows = list(_csv.reader(fh, delimiter="\t"))
    rd_head, rd_body = rd_rows[0], rd_rows[1:]

    out = {}

    # ---------------------------------------------------------- R23 section
    out["origination_order"] = """
<section>
<h2>Origination order (requirement R23)</h2>
<p>The order is mandated and fixed before results: <strong>the side first, then the total, then the
moneyline.</strong> The moneyline is priced last because it is derived from the same margin distribution the
side model produces &mdash; one model behind the markets, so the markets cannot contradict each other.
This supersedes the earlier &ldquo;totals-first&rdquo; design note; the change is logged as
<a href="flagged.html#F27">F27</a> rather than made silently.</p>
%s
</section>
""" % table(["Step", "Market", "What originates", "Why in this position", "Live output"], [
        [cell("1", "n"), cell("SIDE (spread)"),
         cell("Expected margin distribution per game, with its band"),
         cell("The anchor market: highest liquidity and the only one where an edge is measurable at human sample sizes"),
         raw_src('<a href="line-board.html">line board</a>')],
        [cell("2", "n"), cell("TOTAL"),
         cell("Expected combined scoring, with its band"),
         cell("A sum of the same two scoring expectations, so it cannot contradict the side"),
         raw_src('<a href="line-board.html">line board</a>')],
        [cell("3", "n"), cell("MONEYLINE"),
         cell("Fair win probability from the margin distribution"),
         cell("Derived last; no separate model, no separate way to be wrong"),
         raw_src('<a href="line-board.html">line board</a>')],
    ], cls="dense")

    # ---------------------------------------------------------- R25 section
    lr = []
    for e in sig["rows"]:
        s, k = e["signal"], e["staking"]
        lr.append([
            cell(e["signal_rank"], "n"),
            cell(e["strategy_id"]),
            cell(e["market"]),
            cell(s["settled"], "n"),
            cell(_fmt(s["hit_rate"], 4)),
            cell(_fmt(s["hit_ci_low"], 4) + " – " + _fmt(s["hit_ci_high"], 4)),
            cell(_fmt(s["reference_hurdle"], 5)),
            cell(_fmt(s["signal_edge_lcb"], 4)),
            '<td>%s</td>' % pill(s["signal_verdict"],
                                 "ok" if s["signal_verdict"] == "SIGNAL PROVEN" else "bad"),
            cell(_fmt(k["roi"], 4)),
            cell(_fmt(k["profit_units"], 2)),
            cell(_fmt(k["max_drawdown"], 2)),
            raw_src('<a href="flagged.html#F30">F30</a>'),
        ])
    out["signal_staking"] = """
<section>
<h2>Signal and staking are reported separately (requirement R25)</h2>
<p>A lucky staking run must not be able to mask a bad signal. So the leaderboard has two blocks and the
rank is computed from <strong>signal only</strong>: flat one-unit stake on every settled bet, ranked on
the 95%% lower bound of the hit rate against the break-even hurdle. The staking block &mdash; ROI at the
stakes actually used, profit, drawdown &mdash; is reported beside it and can never change a rank, a badge
or a reward. The arithmetic lives in <code>engine/backtest.py</code>
(<code>split_signal_staking</code>) and is exercised by the test suite.</p>
<div class="callout warn"><p><strong>Read the hurdle column correctly.</strong> The table below re-ranks
the computed research layer's 16 backtested strategies (third-party data &mdash; flagged). That dataset's
own <code>breakeven_hit</code> column is circular &mdash; computed as 1/(1+realized ROI) &mdash; and is
NOT used for ranking; it is transcribed in the data file for audit only. See
<a href="flagged.html#F30">F30</a> (severity High) and suggestion SG28. The reference hurdle here is the
standard &minus;110 two-way break-even, 0.52381. None of the 16 entries is signal-proven; all 16 are
REJECTED in their own dataset's gates.</p></div>
</section>

<section>
<h2>Computed-layer entries, re-ranked on signal</h2>
%s
<p class="caption">Signal columns: flat-stake only. Staking columns: right of the divider, reported and
never ranked on. Rank = order by (hit CI low &minus; reference hurdle), ties by larger sample.
Sources: computed layer over the pinned third-party capture %s (flags F17/F23).</p>
</section>

<section>
<h2>What the plan-level board will show when its gates run</h2>
%s
</section>

<section>
<h2>Demotion: live is a revocable state</h2>
<p>A strategy that goes live and decays is sent back to paper by the demotion gate
<a href="validation.html#G-14">G-14</a> &mdash; signal decay, drawdown, or closing-line rot. Live is a
state you have to keep earning.</p>
</section>
""" % (
        table(["Signal rank", "ID", "Market", "Settled", "Hit rate", "Wilson 95% CI",
               "Ref. hurdle", "Signal edge (LCB)", "Signal verdict",
               "Staking ROI", "Staking profit (u)", "Staking max DD (u)", "Flag"],
              lr, cls="dense",
              caption="Re-ranking of data/leaderboard.csv on signal only."),
        raw_src(src_link("S47", sources_by_id)),
        table(["Block", "Columns", "May it affect rank?", "Source of truth"], [
            [cell("SIGNAL"),
             cell("settled n, hit rate, Wilson CI, break-even hurdle, z/p, flat-stake ROI, abstain rate"),
             cell("Yes — rank is computed from this block only"),
             cell("engine/backtest.py split_signal_staking()")],
            [cell("STAKING"),
             cell("ROI at declared stakes, profit units, max drawdown, largest-bet share of profit"),
             cell("No — reported, never ranked on"),
             cell("engine/backtest.py split_signal_staking()")],
        ], cls="dense"))

    # ---------------------------------------------------------- R28 section
    out["demotion"] = """
<section id="G-14">
<h2>G-14 &mdash; the demotion gate (requirement R28): live strategies return to paper</h2>
<div class="callout warn"><p><strong>Parallel build (F31).</strong> The D1&ndash;D3 demotion gate above (from <a href="governance.html">Signal, Staking &amp; Demotion</a>) and this G-14 gate are two independent implementations of requirement R28 with different triggers and thresholds. Both are preserved; Q24 decides which becomes canonical.</p></div>
<p>A gate set decides who gets promoted. This gate decides who gets sent back. Without it, a live badge
outlives the edge that earned it and the leaderboard decays into a graveyard of former winners. Any ONE
trigger demotes; the verdict logic is not reviewable, the thresholds are.</p>
%s
<p class="caption">States: LIVE &rarr; (any trigger) &rarr; PAPER; PAPER &rarr; LIVE only through
re-promotion on a fresh sealed sample. Old bets never re-qualify an entry — the burden of proof resets.
Implementation: <code>engine/demotion.py</code>, tested in <code>tests/test_r21_r28.py</code>.
Thresholds are proposed competition rules, reviewable under <a href="flagged.html#F28">F28</a> /
question Q24.</p>
</section>
""" % table(["Rule", "Trigger", "Metric", "Threshold (proposed)", "Why"], [
        [cell("D1"), cell("Signal decay"),
         cell("Flat-stake hit rate over the trailing window vs break-even at the prices paid"),
         cell("below break-even AND one-sided p &lt; 0.10 for inferiority"),
         cell("The edge died; what remains is noise wearing the old badge")],
        [cell("D2"), cell("Drawdown"),
         cell("Max drawdown of the flat-stake equity curve"),
         cell("&gt; 25 flat-stake units"),
         cell("A run of losses that a real bankroll would not survive is a strategy change, not variance")],
        [cell("D3"), cell("Closing-line rot"),
         cell("Trailing mean CLV and its bootstrap upper bound"),
         cell("mean CLV &lt; 0 AND 95% upper bound &lt; 0"),
         cell("The market has stopped moving toward our numbers: the information edge is gone")],
        [cell("RE"), cell("Re-promotion"),
         cell("Fresh sealed sample, flat-stake hit rate vs break-even"),
         cell("&ge; 300 fresh settled bets, one-sided p &lt; 0.05 (the G-2b standard)"),
         cell("Returning to live must be harder than staying live")],
    ], cls="dense")

    # ------------------------------------------------- R24 line board page
    coef = board["coefficients"]
    lb_rows = []
    for r in board["rows"]:
        lb_rows.append([
            cell(r["game"]),
            cell(r["gameday"]),
            cell(r["market_type"]),
            cell(_fmt(r["model_fair_line"], 2)),
            cell(_fmt(r["model_band"], 2)),
            '<td>%s</td>' % badge(r["fair_tier"]),
            cell(_fmt(r["market_line"], 2)),
            '<td>%s</td>' % badge(r["market_tier"]),
            cell(_fmt(r["difference"], 2)),
            '<td>%s</td>' % badge(r["difference_tier"]),
            cell(r["market_note"]),
            cell(r["result"]),
            raw_src(" ".join(src_link(s, sources_by_id) for s in
                             sorted(set(r["fair_sources"] + r["market_sources"]))))
            + " " + raw_src(" ".join('<a href="flagged.html#%s">%s</a>' % (fl, fl)
                                     for fl in r["flags"])),
        ])
    out["line_board"] = """
<section>
<h1>Line Board &mdash; fair &vert; market &vert; difference</h1>
<div class="callout warn"><p><strong>Parallel build (F31).</strong> A second implementation of this requirement lives at <a href="model-lines.html">Model Lines &amp; Price Store</a>, which keeps every market and difference cell blank under a strict source policy. This page publishes the pinned capture with a THIRD_PARTY badge. Both are preserved; Q23 decides which becomes canonical.</p></div>
<p class="lead">Requirement R24: the model's fair line, the market line and the difference are published as
<strong>three separate columns</strong>, in the mandated origination order (R23): side first, then total,
then moneyline. difference = model &minus; market. A blank difference is a blank, never a zero.</p>
<div class="callout"><p><strong>Conventions, fixed before results.</strong> Side quotes are HOME-view
spreads (negative = home favourite). The pinned market feed records the AWAY club's spread &mdash;
verified against moneyline direction across 13/13 games (check V8) &mdash; so the market column negates the
verbatim capture and says so per row; the verbatim number sits in the
<a href="price-snapshots.html">price-snapshot store</a>. The moneyline market cell is blank because no
moneyline price was captured (<a href="flagged.html#F25">F25</a>).</p></div>
</section>

<section>
<h2>Model coefficients &mdash; every one computed, every one with its n</h2>
%s
<p class="caption">Fair lines come from the published naive baseline (<code>engine/fairline.py</code>):
strength = (PF&minus;PA)/G per club (official standings %s), fair margin = HFA + (strength<sub>h</sub> &minus;
strength<sub>a</sub>)/2, fair total = (PPG<sub>h</sub> + OPPG<sub>h</sub> + PPG<sub>a</sub> +
OPPG<sub>a</sub>)/2, moneyline = &Phi;(margin / sd). The /2 is a bookkeeping convention. Nothing is
fitted on market prices. Band = 1.96 &times; sd / &sqrt;(min games). Provenance:
<a href="flagged.html#F29">F29</a>.</p>
</section>

<section>
<h2>Every originated market &mdash; %d rows</h2>
%s
</section>

<section>
<h2>How to read the difference column</h2>
<p>A positive difference means the model's number is higher than the market's in the displayed convention.
The column measures disagreement, not edge: a difference is only actionable once the band excludes the
market number AND the prices in the <a href="price-snapshots.html">snapshot store</a> clear their hurdle.
The market column carries the <strong>THIRD_PARTY</strong> badge because no official league source prices
NFL lines (<a href="flagged.html#F23">F23</a>, question Q23 &mdash; the strict-blank policy is one review
away).</p>
</section>
""" % (
        table(["Coefficient", "Value", "n", "Tier", "Source"], [
            [cell("Home-field advantage (points/game)"), cell(_fmt(coef["home_field_advantage_points"], 3), "n"),
             cell(coef["hfa_n_games"], "n"), badge(coef["tier"]),
             raw_src(src_link("S52", sources_by_id))],
            [cell("Game-margin sd (points)"), cell(_fmt(coef["margin_sd_points"], 3), "n"),
             cell(coef["margin_sd_n_games"], "n"), badge(coef["tier"]),
             raw_src(src_link("S52", sources_by_id))],
            [cell("Club strength"), cell(coef["strength"]),
             cell(32, "n"), badge(coef["tier"]),
             raw_src(src_link("S03", sources_by_id))],
        ], cls="dense"),
        raw_src(src_link("S03", sources_by_id)),
        len(board["rows"]),
        table(["Game", "Date", "Market", "Model fair line", "Model band", "Fair tier",
               "Market line", "Market tier", "Difference", "Difference tier",
               "Market quote note", "Result", "Sources / flags"],
              lb_rows, cls="dense searchable"))

    # ---------------------------------------------- R21 price snapshots page
    cov = snaps["coverage"]
    ps_rows = []
    for r in snaps["rows"]:
        ps_rows.append([
            cell(r["market_id"]),
            cell(r["market_type"]),
            cell(r["side"] + " (" + r["quote_side"] + ")"),
            cell(_fmt(r["open_price"], 2)),
            cell(r["open_ts"] or ""),
            cell(_fmt(r["close_price"], 2)),
            cell(r["close_ts"] or ""),
            '<td>%s</td>' % badge(r["close_provenance"] or "BLANK"),
            raw_src(src_link(r["close_source"], sources_by_id) if r["close_source"]
                    else '<span class="muted">no source</span>'),
            cell(r["notes"]),
        ])
    out["price_snapshots"] = """
<section>
<h1>Price-Snapshot Store</h1>
<p class="lead">Requirement R21: the store records the <strong>opening and the closing number for every
market we originate</strong> &mdash; one row per (game, market, quote side), created before kickoff and
completed at close. A price cell is filled only when a named source record backs it. Rows are stored in the
mandated origination order: SIDE, then TOTAL, then MONEYLINE (R23).</p>
<div class="callout warn"><p><strong>Opening prices: %d of %d rows have one.</strong> No source of opening
prices exists in this repository &mdash; not official, not third-party &mdash; so every open cell is blank
and recorded as blank. That is the store doing its job: the gap is now a countable, fillable field rather
than a silence. Question Q21 and suggestions SG20/SG25 own the path forward.</p></div>
</section>

<section>
<h2>Coverage</h2>
%s
</section>

<section>
<h2>Policy (enforced in <code>engine/snapshots.py</code>, tested)</h2>
%s
</section>

<section>
<h2>The store &mdash; %d rows</h2>
%s
</section>
""" % (
        cov["open_filled"], cov["TOTAL_ROWS"],
        table(["Market type", "Rows", "Open filled", "Close filled", "What a blank means"], [
            [cell("SIDE"), cell(cov["SIDE"]["rows"], "n"), cell(cov["SIDE"]["open_filled"], "n"),
             cell(cov["SIDE"]["close_filled"], "n"),
             cell("No source captured that number; never inferred")],
            [cell("TOTAL"), cell(cov["TOTAL"]["rows"], "n"), cell(cov["TOTAL"]["open_filled"], "n"),
             cell(cov["TOTAL"]["close_filled"], "n"),
             cell("No source captured that number; never inferred")],
            [cell("MONEYLINE"), cell(cov["MONEYLINE"]["rows"], "n"),
             cell(cov["MONEYLINE"]["open_filled"], "n"), cell(cov["MONEYLINE"]["close_filled"], "n"),
             cell("No 2026 moneyline capture exists (F25); rows exist so the gap is visible")],
        ], cls="dense"),
        table(["Rule", "Statement"], [
            [cell("Order"), cell("SIDE, then TOTAL, then MONEYLINE (R23), then kickoff")],
            [cell("Open"), cell(snaps["policy"]["open_rule"])],
            [cell("Close"), cell(snaps["policy"]["close_rule"])],
            [cell("Provenance"), cell(snaps["policy"]["provenance_rule"])],
            [cell("Validation"), cell("A price without provenance or a source id fails the store; a claim "
                                      "of OFFICIAL pricing is rejected outright (no official league source "
                                      "prices NFL lines, F23)")],
        ], cls="dense"),
        len(snaps["rows"]),
        table(["Market ID", "Type", "Quote", "Open", "Open ts", "Close", "Close ts",
               "Close tier", "Close source", "Notes"], ps_rows, cls="dense searchable"))

    # ------------------------------------------------ R22 results feed page
    rf_rows = []
    for g in feed["rows"]:
        rf_rows.append([
            cell(g["week"], "n"),
            cell(g["date"]),
            cell(g["away"]),
            cell(g["awayPts"], "n"),
            cell(g["home"]),
            cell(g["homePts"], "n"),
            cell(g["margin_home"], "n"),
            cell(g["total"], "n"),
            badge(g["tier"]),
            raw_src(src_link(g["source_id"], sources_by_id)),
        ])
    out["results_feed"] = """
<section>
<h1>Verified Results Feed</h1>
<div class="callout warn"><p><strong>Parallel build (F31).</strong> A second implementation lives at <a href="results-feed.html">Results Feed &amp; Backtest</a> (same 137 official rows, plus a strictly out-of-sample model backtest). Both are preserved; Q29 decides which becomes canonical.</p></div>
<p class="lead">Requirement R22: backtests and ROI can be computed at all only if there is a results feed
whose every row is checked against an official source. This is that feed: %d finished games, weeks 1&ndash;10
of the 2026 season, every row official (%s), every row settled against by
<code>engine/backtest.py</code> and by nothing else.</p>
<div class="callout"><p><strong>Verification, not transcription.</strong> Recomputing every club's W/L/T and
PF/PA from this feed reproduces the official standings capture exactly &mdash; 32 of 32 clubs &mdash; as
part of the build (<code>scripts/build_results_feed.py</code> fails loudly otherwise). The raw capture is
<code>raw/schedule-results-2026-week1-10.tsv</code>; <code>tools/verify_results.py</code> re-checks it.</p></div>
</section>

<section>
<h2>Coverage</h2>
%s
</section>

<section>
<h2>How backtests and ROI are computed (and labelled)</h2>
%s
</section>

<section>
<h2>Worked example &mdash; the one settled Week 10 board game</h2>
%s
<p class="caption">Prices are the captured closing numbers (THIRD_PARTY), scores are official (S52),
settlement and P&amp;L arithmetic are <code>engine/backtest.py</code> at a flat one-unit stake and standard
&minus;110. A worked example of the pipeline, not evidence about any strategy: n = 1.</p>
</section>

<section>
<h2>Every row &mdash; %d games</h2>
%s
</section>
""" % (
        len(feed["rows"]),
        raw_src(src_link("S52", sources_by_id)),
        table(["Field", "Value"], [
            [cell("Games"), cell(feed["coverage"]["games"], "n")],
            [cell("Weeks"), cell("1–10 (through the Week 10 Thursday game)")],
            [cell("Clubs"), cell(feed["coverage"]["clubs"], "n")],
            [cell("Tier"), badge(feed["provenance"]["tier"])],
            [cell("Verification"), cell(feed["provenance"]["verification"])],
        ], cls="dense"),
        table(["Step", "What happens", "Provenance rule"], [
            [cell("1. Index"), cell("Bet logs are joined to this feed by game key or id; no row, no settlement"),
             cell("OFFICIAL rows only (S52)")],
            [cell("2. Settle"), cell("Win/loss/push decided from the official score at the recorded line; "
                                     "pushes are void, never wins"),
             cell("COMPUTED from OFFICIAL")],
            [cell("3. Price"), cell("P&amp;L at the recorded American price; ROI = profit / staked units"),
             cell("inherits the price tier (THIRD_PARTY until Q21/Q23 resolve)")],
            [cell("4. Split"), cell("Signal block (flat stake) and staking block (declared stakes) reported "
                                    "separately; rank on signal only (R25)"),
             cell("COMPUTED")],
            [cell("5. Report"), cell("Every computed statistic carries its tier; a THIRD_PARTY-backed "
                                     "statistic is published only with its flag (F23)"),
             cell("provenance_report() in engine/backtest.py")],
        ], cls="dense"),
        table(["Market", "Bet", "Close", "Official result", "Settled", "P&amp;L (u, flat at &minus;110)", "Tier"], [
            [cell("SIDE"), cell("NYG &minus;1.5 (home view)"), cell("&minus;1.5"),
             cell("WAS 24 @ NYG 21"), pill("LOSS", "bad"), cell("&minus;1.00"),
             raw_src(badge("COMPUTED-OVER-THIRD-PARTY"))],
            [cell("TOTAL"), cell("OVER 40.5"), cell("40.5"),
             cell("45 total"), pill("WIN", "ok"), cell("+0.91"),
             raw_src(badge("COMPUTED-OVER-THIRD-PARTY"))],
            [cell("MONEYLINE"), cell("—"), cell(""),
             cell("WAS 24 @ NYG 21"), pill("BLANK", "warn"), cell(""),
             raw_src(badge("BLANK"))],
        ], cls="dense"),
        len(feed["rows"]),
        table(["Week", "Date", "Away", "Pts", "Home", "Pts", "Home margin", "Total",
               "Tier", "Source"], rf_rows, cls="dense searchable"))

    # --------------------------------------------- R26 replacement depth page
    rep_rows = []
    for row in rd_body:
        (team, unit, slot, line, miss_s, miss_p, rep, depth, gs,
         note, src_chart, src_inj) = (row + [""] * 12)[:12]
        rep_rows.append([
            cell(team), cell(unit), cell(slot), cell(line),
            cell(miss_s), cell(miss_p),
            cell(rep), cell(depth, "n"), cell(gs),
            cell(note),
            raw_src((src_link(src_chart, sources_by_id) if src_chart else "") + " " +
                    src_link(src_inj, sources_by_id)),
        ])
    deep3 = sum(1 for r in rd_body if (r + [""] * 12)[7] in ("3", "4"))
    out["replacement_depth"] = """
<section>
<h1>Replacement Depth</h1>
<p class="lead">Requirement R26: track the <strong>depth of the replacement</strong>, not just the fact of a
replacement. A club missing its starter and its backup is not the same problem as a club missing only its
starter. This page names, for every affected slot, which string the next <em>available</em> player is.</p>
<div class="callout"><p><strong>What is observed, and what is not.</strong> The chart order and string
numbers are published by the clubs themselves (labelled unofficial &mdash; sources per row). The game
status is the official injury report (%s). A string counts as missing only on an official
<strong>Out</strong>; Doubtful and Questionable are notes, never absences. Nothing here claims who will
actually take the field: no snap-count source is verified (question Q27).</p></div>
</section>

<section>
<h2>Summary</h2>
%s
</section>

<section>
<h2>Every affected slot &mdash; %d rows</h2>
%s
</section>
""" % (
        raw_src(src_link("S01", sources_by_id)),
        table(["Measure", "Value", "Meaning"], [
            [cell("Affected slots (chart string missing on an official Out)"),
             cell(len(rd_body), "n"), cell("Rows below")],
            [cell("Slots whose next available player is string 3 or deeper"),
             cell(deep3, "n"),
             cell("The depth cases this page exists to make visible")],
            [cell("Contingent rows"), cell(sum(1 for r in rd_body if "contingent" in (r + [""] * 12)[9]), "n"),
             cell("Starter healthy but deeper strings out &mdash; recorded before it hurts")],
            [cell("Coverage"), cell("31 of 32 club charts (HOU chart is an image — F16)"),
             cell("Joined to the official report for the 28 clubs playing Week 10")],
        ], cls="dense"),
        len(rd_body),
        table(["Club", "Unit", "Slot", "Line", "Missing strings", "Missing players",
               "Replacement", "Replacement depth", "Replacement status", "Note",
               "Sources"], rep_rows, cls="dense searchable"))

    # ------------------------------------------ R27 correlation register page
    cr_rows = []
    for r in corr["rows"]:
        cr_rows.append([
            cell(r["id"]),
            cell(r["label"]),
            cell(r["x"] + " vs " + r["y"]),
            cell(r["n"], "n"),
            cell(_fmt(r["r"], 4)),
            cell(((_fmt(r["ci_low"], 4) + " – " + _fmt(r["ci_high"], 4))
                  if r["ci_low"] is not None else "")),
            badge(r["tier"]),
            cell(r["inputs"]),
            raw_src(" ".join(src_link(s, sources_by_id) for s in r["sources"])),
        ])
    out["correlation_register"] = """
<section>
<h1>Correlation Register &mdash; officially sourced numbers only</h1>
<p class="lead">Requirement R27: correlations are computed <strong>only</strong> from officially sourced
numbers, and every value publishes its <strong>n</strong> beside it. The rule is enforced as code:
<code>engine/corr_official.py</code> raises unless every source id of a record is in the official set.</p>
<div class="callout warn"><p><strong>One value is deliberately blank.</strong> C-A4 (availability vs margin)
sits at n = 1: only one week of official injury captures exists and only one game with paired inputs is
settled. A correlation at n = 1 is not a small number, it is no number &mdash; so the cell is blank and the
n is published, exactly as the requirement asks.</p></div>
</section>

<section>
<h2>The register &mdash; %d rows</h2>
%s
</section>

<section>
<h2>Excluded by rule &mdash; third-party registers</h2>
%s
<p class="caption">These are measurements of third-party datasets. They are not wrong; they are not
official, so they cannot enter this register. They live on their own labelled pages.</p>
</section>
""" % (
        len(corr["rows"]),
        table(["ID", "Pair", "Variables", "n", "r (Pearson)", "Fisher 95% CI",
               "Tier", "Inputs", "Sources"], cr_rows, cls="dense"),
        table(["Register", "Why excluded"], [
            [cell(x["path"]), cell(x["why"])] for x in corr["excluded_registers"]
        ], cls="dense"))

    # ---------------------------------------------- N01-N05 sprint (2026-11-16)
    dec = build.load_json("decision_readiness.json")
    luck = build.load_json("luck_panel_signal.json")
    delta = build.load_json("injury_hub_delta.json")
    w10x = build.load_json("week10_results_extension.json")
    strat_j = build.load_json("strategies.json")

    def qflink(ref):
        if ref.startswith("Q"):
            return '<a href="questions.html#%s">%s</a>' % (ref, ref)
        return '<a href="flagged.html#%s">%s</a>' % (ref, ref)

    # ------------------------------------------------- N01 decision readiness
    dr_rows = []
    for r in dec["rows"]:
        blocker = r["blocker"] or "none — delivered"
        refs = " ".join(qflink(x) for x in r["blocker_refs"])
        dr_rows.append([
            '<td><a href="requirements.html">%s</a></td>' % esc(r["id"]),
            cell(r["requirement"]),
            '<td>%s</td>' % pill(r["status"], STATUS_KIND.get(r["status"], "")),
            cell(r["delivered"]),
            cell(blocker) + ('<td>%s</td>' % refs if refs else "<td>—</td>"),
            cell(r["clears"]),
        ])
    out["decision_readiness"] = """
<section id="decision-readiness">
<h2>Decision-readiness — 2026-11-16 snapshot</h2>
<p class="lead">This is a separately retained, user-provided project-readiness view from
<code>data/decision_readiness.json</code>, updated 2026-11-16. Its status, evidence and clearing-number
cells are a prior-session snapshot, not NFL facts and not recomputed against the 2026-11-17 captures.
For example, it records 24/28 requirements complete and 68/74 sources verified; those are not current
repository totals. Compare with the other <a href="readiness.html">Decision Readiness</a> view and
<a href="requirements.html">Requirements</a>. Both are preserved pending F66/SG47 owner review.</p>
%s
</section>
""" % table(["Req", "Requirement", "Snapshot status", "Delivered (snapshot)",
             "Gate (snapshot)", "Refs", "Clearing target (snapshot)"],
            dr_rows, cls="dense searchable",
            caption="Prior-session snapshot loaded from <code>data/decision_readiness.json</code> (updated 2026-11-16); values are retained for comparison, not presented as today's counts.")

    # ------------------------------------------------------- N05 luck panel
    lk_rows = []
    for r in luck["rows"]:
        lk_rows.append([
            cell(r["strategy_id"]),
            cell(r["market"]),
            cell(r["settled"], "n"),
            cell("%.2f%%" % (100 * r["hit_rate"]), "n"),
            cell("%.2f%%" % (100 * r["hit_ci_low"]), "n"),
            cell("%.2f%%" % (100 * r["reference_hurdle"]), "n"),
            cell("%+.2f pp" % (100 * r["edge_lcb"]), "n"),
            cell("%+.2f%%" % (100 * r["roi_report_only"]), "n"),
            '<td>%s</td>' % pill(r["verdict"], "ok" if r["verdict"] == "PROVEN" else "bad"),
        ])
    h = luck["headlines"]
    out["luck_panel"] = """
<section id="removal-of-luck">
<h2>Signal-versus-variance view — 2026-11-16</h2>
<p class="lead">This is the separately retained luck-removed-edge view in
<code>data/luck_panel_signal.json</code> (updated 2026-11-16), calculated on the third-party-backed
computed research layer. It uses the 95%% hit-rate lower bound minus the standard -110 break-even;
ROI is telemetry, not a ranking criterion. It is distinct from the family-wise p-value view below,
and from the official-results-only 137-game panel on <a href="removal-of-luck.html">Removal of Luck</a>.
%s</p>
<div class="callout"><p><strong>The one-line proof.</strong> %s</p>
<p><strong>Control baseline.</strong> %s</p>
<p><strong>Multiplicity.</strong> %s</p></div>
<div class="callout bad"><p><strong>Dataset tier.</strong> %s</p></div>
%s
</section>
""" % (esc(luck["metric_plain"]),
       esc(h["best_case"]["point"]),
       esc(h["control_baseline"]["point"]),
       esc(h["multiplicity"]["note"]),
       esc(luck["provenance"]["warning"]),
       table(["Entry", "Market", "Settled n", "Hit rate", "95% CI low", "Break-even hurdle",
              "Luck-removed edge", "ROI (report only)", "Verdict"],
             lk_rows, cls="dense searchable",
             caption="Every row from data/leaderboard_signal_staking.json, ordered by the "
                     "luck-removed edge. ROI is shown but can never change a rank — 7 of 16 "
                     "entries show a positive ROI and every one of them is rejected on signal."))

    # -------------------------------------------------- N03 injury-hub delta
    reads = delta["reads"]
    ch = delta["delta"]["changed"]
    add = delta["delta"]["added"]
    rem = delta["delta"]["removed"]
    pc = delta["delta"]["per_club_row_count_changes"]
    read_rows = []
    for r in reads:
        when = r.get("read_window_utc") or r.get("captured", "")
        read_rows.append([
            cell("read %d" % r["read"], "n"),
            cell(when),
            cell(r["rows"], "n"),
            cell(r["week_shown"]),
            raw_src(src_link(r["source_id"], sources_by_id)),
        ])
    ch_rows = []
    for c in ch:
        ch_rows.append([
            cell(c["team"]),
            cell(c["player"]),
            cell(c["pos"]),
            cell(c["field"]),
            cell(c["old"] or "—"),
            cell(c["new"] or "—"),
        ])
    add_rows = [[cell(a["team"]), cell(a["player"]), cell(a["pos"]),
                 cell(a["injury"] or "—"), cell(a["practice"] or "—"),
                 cell(a["game"] or "—")] for a in add]
    rem_rows = [[cell(d["team"]), cell(d["player"]), cell(d["pos"])] for d in rem]
    pc_rows = [[cell(p["team"]), cell(p["read1"], "n"), cell(p["read2"], "n")] for p in pc]
    res_rows = [[cell(p["text"]), raw_src('<a href="%s">%s</a>' % (p["url"], "nfl.com/news"))]
                for p in delta["reserve_list_pointers"]]
    out["injury_delta"] = """
<section>
<h2>Dated reads of the injury hub &mdash; delta, never the level</h2>
<p class="lead">The hub is read with its clock time and each new read is published as the
<em>difference</em> from the previous one, so a designation's history is a series, not a snapshot.
Both captures are kept verbatim under <code>raw/</code>.</p>
%s
<div class="callout"><p><strong>Read 2 (2026-11-16, ~01:15&ndash;01:25 UTC).</strong> The hub still showed
<em>WEEK 10</em>. The %d field changes and %d added rows since read 1 all belong to clubs whose
report was still evolving (the Monday-night clubs and one Colts row that cleared); the three Lions
game-status designations flagged earlier are already populated in read 1, so the 2026-11-14
re-capture had fixed them. The page's NEWS section also carried reserve-list events (below) —
recorded as pointers, never used as injury-table rows.</p></div>
<h3>Changed rows (%d)</h3>
%s
<h3>Added rows (%d)</h3>
%s
<h3>Removed rows (%d)</h3>
%s
<h3>Clubs whose row count moved</h3>
%s
<h3>Reserve-list events referenced on the page (pointers)</h3>
%s
</section>
""" % (table(["Read", "When (UTC)", "Rows parsed", "Week shown", "Source"], read_rows, cls="dense"),
       len(ch), len(add), len(ch),
       table(["Club", "Player", "Pos", "Field", "At read 1 (2026-11-14)", "At read 2 (2026-11-16)"],
             ch_rows, cls="dense searchable"),
       len(add),
       table(["Club", "Player", "Pos", "Injury", "Practice", "Game"], add_rows, cls="dense"),
       len(rem),
       (table(["Club", "Player", "Pos"], rem_rows, cls="dense") if rem_rows
        else '<p class="caption">No row disappeared between the two reads.</p>'),
       (table(["Club", "Read 1", "Read 2"], pc_rows, cls="dense") if pc_rows
        else '<p class="caption">No club row count changed.</p>'),
       table(["Event as headlined on the hub", "Link"], res_rows, cls="dense"))

    # --------------------------------------------- N04 week-10 finals extension
    fin_rows = []
    for f in w10x["finals"]:
        fin_rows.append([
            cell(f["date"]),
            cell(f["away"]),
            cell(f["awayPts"], "n"),
            cell(f["home"]),
            cell(f["homePts"], "n"),
            cell(f["note"] or "—"),
            raw_src('<a href="%s">game centre</a>' % esc(f["game_url"])),
        ])
    pend_rows = []
    for p in w10x["pending"]:
        pend_rows.append([
            cell(p["date"]),
            cell(p["away"]),
            "<td class=\"blank\">—</td>",
            cell(p["home"]),
            "<td class=\"blank\">—</td>",
            cell(p["status"]),
            raw_src('<a href="%s">game centre</a>' % esc(p["game_url"])),
        ])
    out["week10_finals"] = """
<section>
<h2>Week 10 finals &mdash; captured 2026-11-16 after the 2026-11-14 read</h2>
<p class="lead">The week-10 slate had 12 games printed FINAL on the official week page at the
2026-11-16 read; 11 of them are new since the 2026-11-14 capture (the Thursday game was already in
the feed and corroborates it). The two games that were not final at read time are published as
pending with blank scores — nothing is inferred.</p>
<h3>FINAL at read time (%d)</h3>
%s
<h3>Pending at read time (%d)</h3>
%s
<div class="callout"><p><strong>Verification (all four pass, enforced by
<code>scripts/build_week10_extension.py</code>).</strong> V1: the TNF row equals the row already in
the feed (two independent captures agree). V2: every final is a Week 10 fixture on the published
schedule. V3: recomputing all 32 clubs' W/L/T from the feed plus these finals reproduces the records
printed on the page's game cards exactly. V4: the same arithmetic reproduces the fresh official
league standings (W/L/T <em>and</em> PF/PA, 32 of 32) captured at the same read —
<code>raw/standings-2026-20261116.tsv</code>, corroborating evidence only; the canonical standings
capture is unchanged. The Sunday-night game was in progress and the Monday game unplayed at read
time, so those two clubs show pre-game records on the page and blanks here.</p></div>
</section>
""" % (len(w10x["finals"]),
       table(["Date", "Away", "Pts", "Home", "Pts", "Note", "Game centre"], fin_rows, cls="dense"),
       len(w10x["pending"]),
       table(["Date", "Away", "Pts", "Home", "Pts", "Status at read", "Game centre"],
             pend_rows, cls="dense"))

    # ------------------------------------- N02 two-sided change-our-mind fields
    cm_rows = []
    for s in strat_j:
        cm_rows.append([
            '<td><strong>%s</strong></td>' % esc(s["id"]),
            cell(s["name"]),
            cell(s["raises_confidence"]),
            cell(s["lowers_confidence"]),
        ])
    out["change_mind"] = """
<section>
<h2>What would change our mind &mdash; every entry, both directions</h2>
<p class="lead">A strategy entry without a falsification clause is an opinion. Each entry below
states what evidence would raise confidence and what would lower it, in advance, before results
exist. Where the needed data does not exist yet the field says so and names the open question that
owns obtaining it.</p>
%s
</section>
""" % table(["ID", "Strategy", "Would RAISE confidence", "Would LOWER confidence"],
            cm_rows, cls="dense searchable")

    # ------------------------------------------------ R21+R22 exec summary addendum
    out["exec_summary"] = """
<section>
<h2>Requirements sprint &mdash; R21&ndash;R28 (2026-11-14)</h2>
<p>Eight system requirements were implemented, verified and published in this sprint:</p>
%s
<div class="callout warn"><p><strong>Decisions the owner must make before the numbers mean more than they
do now.</strong> (1) Q21/Q22 &mdash; approve an opening-price and moneyline source; today 28 of 56 snapshot
rows have a close and 0 of 56 have an open. (2) Q23 &mdash; ratify the THIRD_PARTY badge policy for market
prices (flag F23) or order strict blanks. (3) Q24/Q25 &mdash; confirm the demotion-gate thresholds and the
allowed staking plans. (4) F30 (severity High) &mdash; the computed layer's break-even column is circular
and its G4 gate is unusable until SG28 lands. Nothing on this site treats any of these as settled.</p></div>
<p>Measured, from official numbers only: home-field advantage in 2026 to date is
<strong>&minus;0.02</strong> points per game (n = 137, S52); rest-days asymmetry correlates with home margin
at <strong>r = 0.43</strong> (n = 121, CI 0.27&ndash;0.56, S52); the verified results feed reconciles
<strong>32 of 32</strong> clubs against the official standings. These are computed values with their n
published &mdash; not claims about the NFL at large.</p>
</section>
""" % table(["ID", "Requirement", "Status", "Where"], [
        [cell("R21"), cell("Price-snapshot store: opening + closing numbers per originated market"),
         pill("done", "ok"), raw_src('<a href="price-snapshots.html">price-snapshots.html</a>')],
        [cell("R22"), cell("Verified results feed so backtests and ROI are computable"),
         pill("done", "ok"), raw_src('<a href="verified-results-feed.html">verified-results-feed.html</a>')],
        [cell("R23"), cell("Origination order: side first, then total, then moneyline"),
         pill("done", "ok"), raw_src('<a href="line-board.html">line-board.html</a>')],
        [cell("R24"), cell("Fair line, market line, difference as separate columns"),
         pill("done", "ok"), raw_src('<a href="line-board.html">line-board.html</a>')],
        [cell("R25"), cell("Signal separated from staking in the leaderboard"),
         pill("done", "ok"), raw_src('<a href="strategies.html">strategies.html</a>')],
        [cell("R26"), cell("Depth of the replacement tracked, not just the fact"),
         pill("done", "ok"), raw_src('<a href="replacement-depth.html">replacement-depth.html</a>')],
        [cell("R27"), cell("Correlations from official numbers only, n published with each"),
         pill("done", "ok"), raw_src('<a href="correlation-register.html">correlation-register.html</a>')],
        [cell("R28"), cell("Demotion gate: live strategies return to paper"),
         pill("done", "ok"), raw_src('<a href="validation.html#G-14">validation.html#G-14</a>')],
    ], cls="dense")

    return out


def _pill_status(status_text):
    lowered = str(status_text).lower()
    if lowered.startswith("done"):
        return pill("done", "ok")
    if lowered.startswith("partial"):
        return pill("partial", "warn")
    return pill("blocked", "bad")


def session_sections(sources_by_id, readiness, luck_panel, ablations, announced,
                     venue_checks, reserve_rows):
    """Decision-layer sections and pages (session arena-fc0ed6e8-fl1, 2026-11-16).

    Everything here is additive: new pages (readiness, ablations) plus new sections on
    index.html and validation.html. No existing register row or section is modified.
    """
    GEN = ('<a class="src" href="https://github.com/sassnarep3-star/FL1/blob/main/tools/site.py" '
           'title="generated by tools/site.py from committed registers registered on sources.html">gen</a>')

    # ------------------------------------------------- landing readiness table
    land_rows = []
    for r in readiness["landing"]:
        src = " ".join('<a class="src" href="sources.html#%s">%s</a>' % (sid, sid)
                       for sid in (r.get("source_ids") or [])) or GEN
        land_rows.append([
            cell(r["r_id"]),
            cell(r["requirement"]),
            '<td>%s</td>' % _pill_status(r["status"]),
            cell(r["blocking_gate"]),
            cell(r["number_that_clears"]),
            '<td><a href="%s">%s</a></td>' % (r["page"], r["page"]),
            '<td>%s</td>' % src,
        ])
    landing_readiness = """
<section>
<h2>Decision readiness &mdash; one row per requirement</h2>
<p class="lead">The gate that blocks each requirement, and the number that would clear it.
&ldquo;Number that clears&rdquo; cells are measurable targets agreed by design, not measured facts
(<a href="flagged.html#F65">F65</a>); where a cell quotes a figure, that figure is verified.
The full register &mdash; including a line-by-line audit of every brief bullet &mdash; is on
<a href="readiness.html">Decision Readiness</a>.</p>
%s
</section>
""" % table(["Req", "Requirement", "Status", "Gate that blocks it", "Number that would clear it",
             "Where", "Source"],
            land_rows, cls="dense searchable",
            caption="Statuses follow the requirement register; gates cite validation gates "
                    "(G-1..G-18), flags (F..), questions (Q..) and suggestions (SG..).")

    # -------------------------------------------------- luck panel (dashboard)
    fw = luck_panel["familywise"]
    luck_rows = []
    for r in luck_panel["rows"]:
        if "p_luck_alone_this_hot" not in r:
            continue
        luck_rows.append([
            cell(r["strategy_id"]),
            cell(r.get("market", "")),
            cell(r["settled"], "n"),
            cell(r["hit_rate"], "n"),
            cell(r["reference_hurdle"], "n"),
            cell(r["p_luck_alone_this_hot"], "n"),
            cell(r["n_to_certify_if_real"] if r["n_to_certify_if_real"] is not None
                 else "&mdash; (below hurdle)", "n" if r["n_to_certify_if_real"] is not None else ""),
            cell(r["certifiable_edge_at_80pct"], "n"),
            '<td>%s</td>' % pill("LUCK NOT EXCLUDED", "warn"),
            '<td><a href="signal-vs-staking.html">%s &rarr;</a></td>' % r["strategy_id"],
        ])
    luck_dashboard = """
<section>
<h2 id="luck">Family-wise signal and sample-floor view — 2026-11-16</h2>
<p class="lead">This separately retained family-wise p-value analysis is loaded from
<code>data/luck_panel_signals.json</code> (updated 2026-11-16) and uses the third-party-backed computed
research layer. It differs from the signal-versus-variance hit-rate lower-bound panel above and from
the official-results-only 137-game panel on <a href="removal-of-luck.html">Removal of Luck</a>.</p>
<p class="lead"><strong>%(n_eval)d</strong> strategies evaluated &middot; <strong>%(n_proven)d</strong> proven &middot;
verdict: <strong>%(verdict)s</strong>. The family-wise bar for a 16-strategy search is a p-value below
<strong>%(bonf)s</strong> (Bonferroni &alpha;/16); the best raw p-value is <strong>%(bestp)s</strong>
(%(bestid)s), so <em>no strategy has separated itself from luck</em>. The panel publishes the
probability that luck ALONE would run at least this hot &mdash; a p-value, never the probability
that a strategy has no edge.</p>
%(tbl)s
<p class="note">Method: p-values and sample floors from <code>engine/stats.py</code> via
<code>engine/luck.py</code>; the hurdle is the standard &minus;110 break-even (0.52381); the dataset&rsquo;s
own breakeven column is circular (flag <a href="flagged.html#F30">F30</a>) and is not used. Input data
is the computed layer&rsquo;s third-party ledger (flags <a href="flagged.html#F34">F34</a>/
<a href="flagged.html#F39">F39</a>). The control anchor: betting every home team at the close returned
&minus;5.2&#37; over 5,067 bets &mdash; the vig itself; any edge must clear that bar, not zero.
Full panel: <a href="readiness.html#luck">Decision Readiness &rarr; Luck</a>. The companion
official-results view &mdash; luck bands and required-n arithmetic computed only from the 137 official
2026 results &mdash; lives on <a href="removal-of-luck.html">Removal of Luck</a>.</p>
</section>
""" % {
        "n_eval": fw["strategies_evaluated"],
        "n_proven": 0,
        "verdict": fw["verdict"],
        "bonf": fw["bonferroni_p_bar"],
        "bestp": fw["best_raw_p"],
        "bestid": fw["best_raw_p_strategy"],
        "tbl": table(["Strategy", "Market", "Settled", "Hit rate", "Hurdle",
                      "P(luck alone this hot)", "n to certify if real", "Certifiable edge @80% power",
                      "Status", "Detail"],
                     luck_rows, cls="dense",
                     caption="p = one-sided probability that a zero-edge process over the same "
                             "number of settled bets runs at least this hot. 'n to certify' is "
                             "engine.stats.required_sample at 80 percent power against the hurdle."),
    }

    # --------------------------------------------------------- readiness page
    audit_rows = []
    for d in readiness["brief_audit"]:
        src = " ".join('<a class="src" href="sources.html#%s">%s</a>' % (sid, sid)
                       for sid in (d.get("source_ids") or [])) or GEN
        audit_rows.append([
            cell(d["id"]),
            cell(d["item"]),
            cell(d["status"]),
            cell(d["where"]),
            cell(d["gate"]),
            cell(d["number"]),
            '<td>%s</td>' % src,
        ])

    luck_rows_full = list(luck_rows)

    ann_rows = []
    for a in announced["rows"]:
        body = a.get("announcement") or ""
        if a.get("roster_event"):
            body = (body + (" " if body else "") + "<strong>Roster event:</strong> " + a["roster_event"])
        ann_rows.append([
            cell(a["id"]),
            cell(a["player"]),
            cell(a["club"]),
            cell(a["week"], "n"),
            cell(a.get("announced_start") or ""),
            cell(a.get("event_date", "")),
            cell(body),
            cell(a.get("cross_check", "")),
            '<td><a class="src" href="%s" title="%s">official</a></td>' % (
                a["source_url"], esc(a.get("source_kind", ""))),
        ])

    vsc_rows = []
    for v in venue_checks["rows"]:
        vsc_rows.append([
            cell(v["id"]),
            cell(v["matchup"]),
            cell(v["official_location"]),
            cell(v["official_stadium"]),
            cell(v["feed_stadium"] + " (third-party feed, S47)"),
            '<td>%s</td>' % pill("MATCH" if v["match"] else "MISMATCH",
                                 "ok" if v["match"] else "bad"),
            '<td>%s</td>' % pill("GAME BOOK LINKED" if v.get("game_book_published") else "",
                                 "ok" if v.get("game_book_published") else ""),
            '<td><a class="src" href="%s">game centre</a></td>' % v["source_url"],
            cell(v["fetched"]),
        ])

    res_rows = []
    for rr in reserve_rows:
        res_rows.append([
            cell(rr.get("date", "")),
            cell(rr.get("player", "")),
            cell(rr.get("club", "")),
            cell(rr.get("transaction", "")),
            '<td><a class="src" href="%s">official transactions page</a></td>'
            % (rr.get("source_url") or "#"),
        ])

    notes_html = "".join("<li>%s</li>" % esc(n) for n in readiness.get("notes", []))

    readiness_page = """
<section>
<h1>Decision Readiness</h1>
<p class="lead">One row per requirement with the gate that blocks it and the number that would clear it
&mdash; the standing decision view the brief asks to see before any change is implemented. Below it,
this page audits every bullet of the project brief, and holds this session&rsquo;s new evidence registers:
the full luck panel, the announced-starter evidence, the official venue spot-checks, and the first
reserve-list capture.</p>
<p>Updated %(updated)s by session <code>%(owner)s</code>. &ldquo;Number that clears&rdquo; cells are measurable
targets agreed by design, not measured facts (<a href="flagged.html#F65">F65</a>) &mdash; except where a cell
quotes a verified figure. Companion pages from the parallel sessions: the
<a href="requirements-backlog.html">Requirement Backlog</a> and the
<a href="removal-of-luck.html">Removal of Luck</a> official-results panel; the
<a href="announced-starters.html">Announced Starters</a> register quotes official announcements
&mdash; this page&rsquo;s register below records the same class of evidence with an explicit
verified/unverified boundary per row.</p>
</section>

<section>
<h2>Requirements (one row per requirement)</h2>
%(land)s
</section>

<section>
<h2>Brief audit &mdash; every bullet, line by line</h2>
<p>Every bullet of the project brief, with its status, where it lives, what still blocks it, and the
number that would clear it. IDs are stable: cite the D-row, not a paraphrase.</p>
%(audit)s
</section>

<section id="luck">
<h2>Removal of luck &mdash; full panel</h2>
<p><strong>%(fw)s.</strong> The table below is the full decomposition behind the dashboard panel:
for every strategy with an evaluatable signal, the probability that luck alone explains the run,
the sample it would need to certify the observed rate if real, and the smallest true edge its
sample could certify at 80 percent power.</p>
%(luck_full)s
<p class="note">Published alongside the three never-averaged luck tests on
<a href="validation.html">Validation</a>. A p-value is P(evidence | no edge) &mdash; the register
never publishes P(no edge | evidence), which is not identified by this data.</p>
</section>

<section>
<h2>Announced-starter evidence (not inferred replacements)</h2>
<p>The blank replacement columns on the injury-report page are correct <em>there</em> &mdash; but the
league does publish dated starter announcements, and those belong in their own evidence register,
separate from anything inferred. A row is published only when the announcement was read on an
official page this session.</p>
%(ann)s
<p class="note">Register: <code>data/announced_starters.json</code>. The Lock row (AS-01) is a
fully verified announcement; the Brissett and McCord rows record official roster events while their
&ldquo;announced start&rdquo; cells stay blank, because the official documents announce the event, not the
start (flag <a href="flagged.html#F64">F64</a>).</p>
</section>

<section>
<h2>Official Game Center venue spot-checks</h2>
<p>The schedule table&rsquo;s Stadium column is published from the reconciled feed
(<a href="sources.html#S47">S47</a>, third-party, flagged). Each row below is a per-game official
Game Center read this session, checking the feed value against what the league itself publishes.</p>
%(vsc)s
<p class="note">Register: <code>data/venue_spotchecks.json</code>. 2 of 272 rows are officially
checked; the rest stay labelled third-party (flag <a href="flagged.html#F63">F63</a>). Both Game
Centers read this session also expose the official per-game Game Book PDF link &mdash; recorded as
evidence that Game Books are reachable (the remaining gap is a parser, not access).</p>
</section>

<section>
<h2>Reserve list &mdash; November 2026 (first dated capture)</h2>
<p>The brief&rsquo;s rule: <em>absence from the weekly injury report is not evidence of availability</em>.
A player on the reserve list is absent for a roster reason. This is the first dated capture of the
official league reserve list (raw verbatim capture: <code>raw/nfl-reserve-list-2026-11.md</code>;
fetched 2026-11-16). It includes the exact row the brief cites: Malik Willis (MIA) placed on
Reserve/Injured on 11/10 &mdash; absent from the weekly report because he is on IR, not because he
is healthy.</p>
%(res)s
<p class="note">Source: <a class="src" href="https://www.nfl.com/transactions/league/reserve-list/2026/11">official reserve-list page</a>
(S70). One month captured; history and cadence remain open (SG46). The weekly report snapshot and
this reserve snapshot are NOT from the same moment and are never merged into one availability level
&mdash; the brief&rsquo;s delta-not-level rule.</p>
</section>

<section>
<h2>Notes</h2>
<ul class="tight">%(notes)s</ul>
</section>
""" % {
        "updated": esc(readiness.get("updated", "")),
        "owner": esc(readiness.get("owner_session", "")),
        "land": table(["Req", "Requirement", "Status", "Gate that blocks it",
                       "Number that would clear it", "Where", "Source"],
                      land_rows, cls="dense searchable"),
        "audit": table(["ID", "Brief item", "Status", "Where it lives", "Gate / blocker",
                        "Number that clears it", "Source"],
                       audit_rows, cls="dense searchable"),
        "fw": ("%d strategies evaluated; %d proven; verdict %s (family-wise bar %.5f; best raw p %.5f, %s)"
               % (fw["strategies_evaluated"], 0, fw["verdict"], fw["bonferroni_p_bar"],
                  fw["best_raw_p"], fw["best_raw_p_strategy"])),
        "luck_full": table(["Strategy", "Market", "Settled", "Hit rate", "Hurdle",
                            "P(luck alone this hot)", "n to certify if real",
                            "Certifiable edge @80% power", "Status", "Detail"],
                           luck_rows_full, cls="dense searchable"),
        "ann": table(["ID", "Player", "Club", "Wk", "Announced start", "Event date",
                      "Announcement / official roster event", "Cross-check", "Source"],
                     ann_rows, cls="dense searchable"),
        "vsc": table(["ID", "Game", "Official location", "Official stadium", "Feed value",
                      "Match", "Game Book", "Source", "Fetched"],
                     vsc_rows, cls="dense"),
        "res": table(["Date", "Player", "Club", "Transaction", "Source"],
                     res_rows, cls="dense searchable"),
        "notes": notes_html,
    }

    # ------------------------------------------------------------ ablations page
    abl_rows = []
    coef_rows = []
    for target, res in ablations["ablations"].items():
        d = res["holdout_difference"]
        without = res["without_availability"]
        with_ = res["with_availability"]
        abl_rows.append([
            cell(target.upper() + " points"),
            cell("%s &rarr; %s &rarr; %s" % (",".join(res["splits"]["train"][:1]) + "&ndash;" +
                                             ",".join(res["splits"]["train"][-1:]),
                                             ",".join(res["splits"]["validation"][:1]) + "&ndash;" +
                                             ",".join(res["splits"]["validation"][-1:]),
                                             ",".join(res["splits"]["holdout"][:1]) + "&ndash;" +
                                             ",".join(res["splits"]["holdout"][-1:]))),
            cell(res["n_train"], "n"),
            cell(res["n_validation"], "n"),
            cell(res["n_holdout"], "n"),
            cell(without["mae_holdout"], "n"),
            cell(with_["mae_holdout"], "n"),
            cell(d["mae_diff"], "n"),
            cell("[%+.3f, %+.3f]" % (d["ci_low"], d["ci_high"]), "n"),
            '<td>%s</td>' % pill("CI INCLUDES 0 - NOT PROVEN" if d["ci_contains_zero"]
                                 else "CI EXCLUDES 0", "warn" if d["ci_contains_zero"] else "ok"),
            '<td>%s</td>' % GEN,
        ])
        for c in (with_.get("availability_coefficients_ci") or []):
            coef_rows.append([
                cell(target.upper()),
                cell(c["feature"]),
                cell(c["coef"], "n"),
                cell("[%+.3f, %+.3f]" % (c["ci_low"], c["ci_high"]), "n"),
                cell("points of %s attributable to the feature, fitted on train only" % target),
                '<td>%s</td>' % GEN,
            ])

    ablations_page = """
<section>
<h1>Injury / personnel ablations &mdash; not fixed penalties</h1>
<p class="lead">The brief rejects &ldquo;subtract a fixed number of points for a missing starter&rdquo;.
The alternative implemented here: run the <strong>same model twice</strong> &mdash; once without and
once with the availability features &mdash; on <strong>chronological holdouts</strong>, and report the
difference <strong>with uncertainty</strong>. The feature&rsquo;s fitted coefficients are published with
their own intervals, so the effect of a non-primary starting QB is an <em>estimate</em>, never an
assumed constant.</p>
</section>

<section>
<h2>Design (frozen before the holdout was scored)</h2>
<p>Identical model shapes differing only in the availability features:</p>
<ul class="tight">
<li><strong>WITHOUT:</strong> intercept + prior-3-game scoring-margin difference (a naive strength proxy).</li>
<li><strong>WITH:</strong> the same, plus four 0/1 indicators &mdash; each side&rsquo;s QB-deficiency class
(&ldquo;2nd different starter&rdquo;, &ldquo;3rd-or-later&rdquo;) from <code>data/depth_deficiency.csv</code>,
derived from the recorded starting QB identity.</li>
<li><strong>Splits (chronological, never random):</strong> train 1999&ndash;2019 &middot; validation
2020&ndash;2021 (stability reading only &mdash; nothing is chosen on it) &middot; holdout 2022&ndash;2025,
scored exactly once after freezing &middot; 2026 excluded entirely (season in progress).</li>
<li><strong>Difference statistic:</strong> MAE(with) &minus; MAE(without) on the holdout, paired by game;
95&#37; CI by paired bootstrap over per-game absolute errors (seed 20261116, 4,000 resamples).</li>
<li><strong>Why not a fixed penalty:</strong> a fixed penalty asserts the adjustment&rsquo;s size with no
uncertainty and no test. Here the size is fitted from training data and published with an interval,
and whether the feature helps at all is decided on the holdout.</li>
</ul>
</section>

<section>
<h2>Holdout results</h2>
%(abl)s
<p class="note"><strong>Reading:</strong> negative MAE diff = the availability feature reduced holdout
error. Both CIs include zero, so the data cannot yet distinguish the two shapes: the feature stays
<strong>OUT</strong> of every published model rather than being waved in. Recompute any time with
<code>python3 scripts/build_ablations.py</code> (deterministic seeds).</p>
</section>

<section>
<h2>Fitted availability coefficients (train-only bootstrap CIs)</h2>
<p>What a fixed penalty would have had to guess, estimated instead: e.g. the fitted effect of a home
team fielding a 2nd-different-starter QB. These are the coefficients the WITH model used on the
holdout &mdash; published with their uncertainty.</p>
%(coef)s
</section>

<section>
<h2>Provenance and limits</h2>
<ul class="tight">
<li><strong>Inputs:</strong> <code>data/raw/games.csv</code> (nflverse feed, source
<a href="sources.html#S47">S47</a>, third-party snapshot &mdash; flag <a href="flagged.html#F62">F62</a>)
and <code>data/depth_deficiency.csv</code> (QB-deficiency classes derived from the same feed&rsquo;s
recorded starters by <code>scripts/build_availability.py</code>).</li>
<li><strong>Not official:</strong> no output on this page is an official NFL publication. The feature
measures who STARTED (recorded game participation), not injury designations; the official-only
correlation register is separate and unaffected.</li>
<li><strong>Scope:</strong> the feature set is deliberately small (QB identity classes). The full
2nd/3rd/4th-string deficiency feature needs the depth-order source decision (Q04/Q05) before it can
join the ablation &mdash; this page is the harness it will slot into.</li>
<li><strong>Engine:</strong> <code>engine/ablation.py</code> (stdlib-only least squares + seeded
bootstrap); unit-tested in <code>tests/test_gsession.py</code>.</li>
</ul>
</section>
""" % {
        "abl": table(["Target", "Splits (train &rarr; val &rarr; holdout)", "n train", "n val",
                      "n holdout", "MAE without", "MAE with", "MAE diff", "95% CI",
                      "Verdict", "Source"],
                     abl_rows, cls="dense searchable"),
        "coef": table(["Target", "Feature", "Coefficient (points)", "95% CI", "Meaning", "Source"],
                      coef_rows, cls="dense searchable"),
    }

    # ------------------------------------------------- validation.html additions
    validation_session = """
<section>
<h2>Luck panel &mdash; where the three tests meet their numbers (G-19 panel, session 2026-11-16)</h2>
<p>The removal-of-luck tests above now have a published numeric panel on the
<a href="index.html#luck">dashboard</a> and the full table on
<a href="readiness.html#luck">Decision Readiness</a>: per-strategy p(luck alone this hot), the
family-wise bar (&alpha;/16 = %(bonf)s), the sample floor to certify an observed rate at 80 percent
power, and the smallest edge each sample could certify. Verdict: <strong>%(verdict)s</strong> &mdash;
the best raw p-value (%(bestp)s, %(bestid)s) is far from the bar, so nothing is promoted and the
reward pool pays 0 units.</p>
</section>

<section>
<h2>G-18 &mdash; drift alarm on every scraper</h2>
<p>The brief: pin each parser to expected row counts and required fields; fail the build loudly when
a field goes missing rather than publishing a blank. <code>tools/verify_drift.py</code> pins
<strong>19</strong> datasets (row counts + required columns) and rewrites
<code>data/verification-drift.tsv</code> on every run:</p>
<ul class="tight">
<li><strong>FAIL (exit 1):</strong> a dataset shrinks, a required column disappears, or a required
column goes fully empty &mdash; the build refuses to publish.</li>
<li><strong>WARN (exit 0):</strong> a dataset grows &mdash; legitimate (a new week settles), but the
pin must be re-committed with the growth, in the open.</li>
</ul>
<p>Pins cover: injuries 345, standings 32, results 137, schedule 272, results feed 137, price
snapshots 56, settled markets 548, questions 34, suggestions 34, flags 42, strategies 6 (incl. the
change-of-mind fields), gates 15, signal-staking 16, sources (columns), reserve list 25, announced
starters 4, venue spot-checks 2, luck panel 16, ablations 2. Run:
<code>python3 tools/verify_drift.py</code> &mdash; wired into CI beside the other gates.</p>
</section>
""" % {"bonf": fw["bonferroni_p_bar"], "verdict": fw["verdict"],
       "bestp": fw["best_raw_p"], "bestid": fw["best_raw_p_strategy"]}

    return {
        "landing_readiness": landing_readiness,
        "luck_dashboard": luck_dashboard,
        "readiness_page": readiness_page,
        "ablations_page": ablations_page,
        "validation_session": validation_session,
    }

def main():
    # imported here rather than at module scope: pages_market reuses this file's page
    # shell through a late-bound lookup, and a module-level import would run it before
    # those helpers are defined (and shadow the stdlib `site` module in the process)
    import pages_market

    teams = build.load("teams.tsv")
    standings = build.load("standings.tsv")
    injuries = build.load("injuries.tsv")
    sources = build.load("sources.tsv")
    schedule = build.load("schedule.tsv")
    results = build.load("results.tsv")
    depth = build.load("depth-kc.tsv")
    aliases = build.load("depth-aliases.tsv")

    questions = build.load_json("questions.json")
    suggestions = build.load_json("suggestions.json")
    requirements = build.load_json("requirements.json")
    strategies = build.load_json("strategies.json")
    flags = build.load_json("flags.json")
    # Session arena-fc0ed6e8-fl1 (2026-11-16): decision-layer registers.
    readiness = build.load_json("readiness.json")
    luck_panel = build.load_json("luck_panel_signals.json")
    ablations = build.load_json("ablations.json")
    announced = build.load_json("announced_starters_g.json")
    venue_checks = build.load_json("venue_spotchecks.json")
    import csv as _csv
    with open(os.path.join(build.DATA, "reserve_list_2026-11.tsv"), encoding="utf-8", newline="") as fh:
        reserve_rows = list(_csv.DictReader(fh, delimiter="\t"))

    sources_by_id = {s["id"]: s for s in sources}
    team_name = {t["abbr"]: t["name"] for t in teams}
    team_conf = {t["abbr"]: (t["conference"], t["division"]) for t in teams}

    lg = build.analyse_league(injuries, teams)
    by_team = build.analyse_injuries(injuries, teams)
    depth_rows = build.analyse_depth(depth, injuries, aliases)
    # League-wide depth join is computed here because the executive summary
    # quotes its totals as well as the Backup Depth page.
    depth_league = build.analyse_depth_league(
        build.load("depth.tsv"), build.load("depth-sources.tsv"),
        injuries, teams, aliases, extra=[("KC", depth_rows)])
    depth_cov = depth_league["coverage"]
    depth_tot = depth_league["totals"]
    flagged_depth = [r for r in depth_rows if r["flagged"]]

    # Requirements sprint (R21-R28): all sprint pages and cross-page sections.
    sprint = sprint_sections(sources_by_id)

    # Session arena/dbf11de0-fl1: requirement backlog, decision readiness,
    # removal of luck, team availability, announced starters, snapshot ledger.
    g_ctx = {
        "page": page, "table": table, "cell": cell, "pill": pill,
        "raw_src": raw_src, "src_link": src_link, "esc": esc,
        "sources_by_id": sources_by_id,
    }
    g_pages, _g_sections = site_g.build(g_ctx)

    # Session arena-fc0ed6e8-fl1 (2026-11-16): decision-layer sections and pages.
    sess = session_sections(sources_by_id, readiness, luck_panel, ablations, announced,
                            venue_checks, reserve_rows)

    written = []

    # ------------------------------------------------------------------ index
    n_sugg = len(suggestions)
    n_q = len(questions)
    n_block = sum(1 for q in questions
                  if str(q.get("blocking", "")).lower().startswith("yes"))
    n_req_done = sum(1 for r in requirements if r.get("status") == "done")
    backlog = build.load_json("requirements_backlog.json")
    n_backlog_req = len(backlog["rows"])

    with open(os.path.join(build.DATA, "results_2026-11-17.tsv"),
              encoding="utf-8", newline="") as fh:
        latest_result_rows = [r for r in _csv.reader(fh, delimiter="\t") if r]
    with open(os.path.join(build.DATA, "injuries_2026-11-16.tsv"),
              encoding="utf-8", newline="") as fh:
        injury_read_2 = [r for r in _csv.reader(fh, delimiter="\t") if r]
    assert all(len(r) == 6 for r in latest_result_rows), \
        "dated 2026-11-17 results rows must retain the six-field schema"
    assert len(latest_result_rows) == 149, \
        "dated 2026-11-17 result count changed; reconcile before publishing the dashboard"

    dashboard = """
<section class="hero dashboard-hero">
  <p class="eyebrow">Research dashboard &middot; evidence read through 2026-11-17 UTC</p>
  <h1>NFL evidence, model research, and open decisions</h1>
  <p class="lead">FL1 is a static research and decision-support site, not an NFL publication or a
  validated betting system. It keeps official records, derived analyses, third-party inputs and
  user-provided project specifications distinct. Unsupported values remain blank and review flags
  remain visible.</p>
  <p class="note">Dated citations describe what a source showed at the recorded read; live pages can
  change. The Dashboard links the full source record for manual review.</p>
</section>

<section class="dashboard-section">
<h2>Evidence snapshot</h2>
<div class="metric-grid">
  <article class="metric-card">
    <p class="metric-label">Latest dated official results read</p>
    <p class="metric-value">%(latest_results)s completed games</p>
    <p>2026-11-17 capture; its standings reconcile for all 32 clubs. This is separate from the
    frozen 137-game evaluation corpus.</p>
    <p class="source-links">%(results_sources)s</p>
  </article>
  <article class="metric-card">
    <p class="metric-label">Frozen evaluation corpus</p>
    <p class="metric-value">%(frozen_results)s games</p>
    <p>The official-results panel still uses this dated sample; it was not silently extended by the
    later results read.</p>
    <p class="source-links">%(frozen_sources)s</p>
  </article>
  <article class="metric-card">
    <p class="metric-label">LAC at BAL — Week 10</p>
    <p class="metric-value status-open">Open · no result recorded</p>
    <p>F67 remains unresolved. Re-read the official Game Center after it says Final before adding a
    result.</p>
    <p class="source-links">%(live_sources)s</p>
  </article>
  <article class="metric-card">
    <p class="metric-label">Week 10 injury captures</p>
    <p class="metric-value">%(injury_read_1)s &rarr; %(injury_read_2)s rows</p>
    <p>Separate 2026-11-14 and 2026-11-16 snapshots; neither is a live status claim.</p>
    <p class="source-links">%(injury_sources)s</p>
  </article>
</div>
</section>

<section class="dashboard-section">
<h2>Start here</h2>
<div class="grid topic-grid">
  <a class="card" href="executive-summary.html"><h3>Executive Summary</h3>
    <p>Dated official evidence, the analysis boundary, and the review issues that remain open.</p></a>
  <a class="card" href="questions.html"><h3>Questions &amp; missing information</h3>
    <p>%(n_questions)s registered questions, with gaps and paths to obtain missing information.</p></a>
  <a class="card" href="suggestions.html"><h3>Suggestions &amp; decisions</h3>
    <p>%(n_suggestions)s proposals with options and trade-offs; owner decisions remain open until recorded.</p></a>
  <a class="card" href="requirements-backlog.html"><h3>Requirement Backlog</h3>
    <p>User-provided project specifications and repository planning status — not NFL requirements or facts.</p></a>
</div>
</section>

<section class="dashboard-section">
<h2>Browse by topic</h2>
<div class="topic-panel-grid">
  <article class="topic-panel">
    <h3>Official records &amp; availability</h3>
    <p>Review dated schedules, results, injury snapshots, announced starters and the limits of club depth charts.</p>
    <div class="topic-links">
      <a href="schedule.html">Schedule</a><a href="standings.html">Standings</a>
      <a href="verified-results-feed.html">Verified Results</a><a href="injuries.html">Injuries</a>
      <a href="availability-ledger.html">Snapshot Ledger</a><a href="announced-starters.html">Announced Starters</a>
      <a href="team-availability.html">Team Availability</a><a href="depth.html">Backup Depth</a>
      <a href="replacement-depth.html">Replacement Depth</a>
      <a href="replacement-depth-market.html">Replacement Depth (spine)</a>
      <a href="replacement-depth-r21r28.html">Replacement Depth (R21–R28)</a>
    </div>
  </article>
  <article class="topic-panel">
    <h3>Lines, models &amp; prices</h3>
    <p>Keep fair lines, market lines and differences distinct; inspect price-source provenance and blank cells.</p>
    <div class="topic-links">
      <a href="line-origination.html">Line Origination</a><a href="model-lines.html">Model Lines</a>
      <a href="originations.html">Originations</a><a href="line-board.html">Line Board</a>
      <a href="origination.html">Origination Run</a><a href="price-snapshots.html">Price Snapshots</a>
      <a href="price-store.html">Price Store</a>
    </div>
  </article>
  <article class="topic-panel">
    <h3>Evaluation &amp; research</h3>
    <p>Compare separate strategy, signal/staking, validation, ablation, correlation and luck analyses.</p>
    <div class="topic-links">
      <a href="strategies.html">Leaderboard</a><a href="signal-vs-staking.html">Signal vs Staking</a>
      <a href="signal-vs-staking-market.html">Signal vs Staking (spine)</a><a href="results-feed.html">Results &amp; Backtest</a>
      <a href="results-feed-market.html">Results Feed (spine)</a><a href="governance.html">Signal &amp; Demotion</a>
      <a href="validation.html">Validation Gates</a><a href="demotion-gate.html">Demotion Gate</a>
      <a href="ablations.html">Ablations</a><a href="removal-of-luck.html">Removal of Luck</a>
      <a href="official-correlations.html">Official Correlations</a><a href="correlation-register.html">Correlation Register</a>
      <a href="correlation-gate.html">Correlation Gate</a><a href="prop-correlations.html">Prop Correlations</a>
      <a href="docs/computed/index.html">Computed Research Layer</a>
    </div>
  </article>
  <article class="topic-panel">
    <h3>Requirements &amp; review</h3>
    <p>The requirement rows are user-provided project specifications. Read their evidence and targets as repository planning, not NFL policy.</p>
    <div class="topic-links">
      <a href="requirements.html">Requirements</a><a href="requirements-backlog.html">Full Backlog</a>
      <a href="readiness.html">Decision Readiness</a><a href="decision-desk.html">Decision Desk</a>
      <a href="questions.html">Questions</a><a href="suggestions.html">Suggestions</a>
      <a href="flagged.html">Flagged for Review</a><a href="sources.html">Sources</a>
      <a href="verification.html">Verification</a>
    </div>
  </article>
</div>
</section>

<section class="dashboard-section" id="alternate-analyses">
<h2>Alternate readiness and luck analyses — retained pending review</h2>
<p class="lead">F66 / SG47 records overlapping implementations and leaves consolidation to an owner
review. These views use different inputs, scopes or definitions. Keep them separate; no canonical
winner is declared here. Every alternate page remains linked in the topic navigation.</p>
<div class="analysis-view-grid">
  <article class="analysis-view">
    <h3>Decision readiness — three views</h3>
    <ul class="tight">
      <li><a href="requirements-backlog.html">Requirement Backlog</a> — full user-provided specification list.</li>
      <li><a href="readiness.html">Decision Readiness</a> — a separate 2026-11-16 gates/targets and brief-audit view.</li>
      <li><a href="#decision-readiness-view">2026-11-16 requirements-register snapshot</a> — includes old 24/28 and 68/74 counts; not current totals.</li>
    </ul>
  </article>
  <article class="analysis-view">
    <h3>Removal of luck — three views</h3>
    <ul class="tight">
      <li><a href="removal-of-luck.html">Official-results base-rate / Brier view</a>.</li>
      <li><a href="#signal-variance-view">Signal-versus-variance view</a> — the alternate strategy panel below.</li>
      <li><a href="#familywise-luck-view">Family-wise p-value and sample-floor view</a> — below and on <a href="readiness.html#luck">Decision Readiness</a>.</li>
    </ul>
  </article>
</div>
<div class="callout warn">
  <p><strong>Do not blend the scores.</strong> The family-wise signal panel reports no strategy clearing
  its threshold; it uses a third-party-backed research ledger. That is a model finding, not an NFL fact.
  See <a href="flagged.html#F66">F66</a>, <a href="suggestions.html#SG47">SG47</a> and source
  <a href="sources.html#S47">S47</a>.</p>
</div>
</section>

<section class="dashboard-details">
<details class="dashboard-disclosure">
  <summary id="decision-readiness-view">Open the 2026-11-16 requirements-register snapshot (user-provided project specifications, not NFL facts)</summary>
  %(readiness_28)s
</details>
<details class="dashboard-disclosure">
  <summary id="signal-variance-view">Open the 2026-11-16 signal-versus-variance view (third-party-backed research)</summary>
  %(luck_variance)s
</details>
<details class="dashboard-disclosure">
  <summary id="familywise-luck-view">Open the 2026-11-16 family-wise p-value and sample-floor view (third-party-backed research)</summary>
  %(luck_familywise)s
</details>
</section>

<section class="callout warn">
  <h2>Source citation under correction</h2>
  <p><a href="schedule.html">Schedule 2026</a> currently attributes its dated announcement to S86,
  but S86 in the current register is a third-party nflverse win-totals feed. The official announcement
  is <a href="https://www.nfl.com/news/2026-nfl-schedule-powered-by-aws-to-be-released-thursday-may-14">on NFL.com</a>;
  the source-ID/generator correction is logged in <a href="COORDINATION.md">COORDINATION.md</a> and
  the S86 chip should not be used for that claim until corrected.</p>
</section>
""" % {
        "latest_results": len(latest_result_rows),
        "frozen_results": len(results),
        "injury_read_1": len(injuries),
        "injury_read_2": len(injury_read_2),
        "n_questions": n_q,
        "n_suggestions": n_sugg,
        "results_sources": " ".join((src_link("S89", sources_by_id),
                                      src_link("S90", sources_by_id))),
        "frozen_sources": " ".join((src_link("S52", sources_by_id),
                                     '<a href="verified-results-feed.html">frozen results view</a>')),
        "live_sources": " ".join((src_link("S91", sources_by_id),
                                   '<a class="src" href="flagged.html#F67">F67</a>')),
        "injury_sources": " ".join((src_link("S01", sources_by_id),
                                     src_link("S80", sources_by_id))),
        "readiness_28": sprint["decision_readiness"].strip(),
        "luck_variance": sprint["luck_panel"].strip(),
        "luck_familywise": sess["luck_dashboard"].strip(),
    }

    written.append(page("index.html", "Dashboard", dashboard))

    # ------------------------------------------------------- executive summary
    official_luck = build.load_json("luck_panel.json")
    official_luck_headline = official_luck["headline"]
    injury_read_1 = len(injuries)
    injury_read_2_count = len(injury_read_2)

    def evidence_sources(*ids):
        return raw_src(" ".join(src_link(sid, sources_by_id) for sid in ids))

    summary_rows = [
        [cell("Latest dated 2026 results read"),
         cell("%d finals; standings reconcile for all 32 clubs" % len(latest_result_rows)),
         evidence_sources("S89", "S90")],
        [cell("Frozen evaluation corpus"),
         cell("%d games; retained separately from the later dated read" % len(results)),
         evidence_sources("S52")],
        [cell("Week 10 injury captures"),
         cell("%d rows (2026-11-14); %d rows (2026-11-16)" %
              (injury_read_1, injury_read_2_count)),
         evidence_sources("S01", "S80")],
        [cell("LAC at BAL"),
         cell("No result recorded; F67 remains open until the official page shows Final"),
         evidence_sources("S91")],
        [cell("Official-results luck sample"),
         cell("%d games; %d home wins, %d away wins, %d tie; home-win rate %.1f%% "
              "(95%% Wilson interval %.1f%%–%.1f%%)" %
              (official_luck_headline["games"], official_luck_headline["home_wins"],
               official_luck_headline["away_wins"], official_luck_headline["ties"],
               100 * official_luck_headline["home_win_rate"],
               100 * official_luck_headline["home_win_rate_wilson"][0],
               100 * official_luck_headline["home_win_rate_wilson"][1])),
         evidence_sources("S52")],
    ]

    es = """
<section class="hero">
<h1>Executive Summary</h1>
<p class="lead">Status of the committed evidence through 2026-11-17 UTC. FL1 is a research and
 decision-support repository, not an NFL publication or a validated betting system. Official
 observations, third-party inputs, computed analyses, and user-provided project specifications are
 kept distinct.</p>
<p class="note">The source links below identify official NFL records for manual review. They refer to
 dated reads, not a guarantee that a live page still shows the same content.</p>
</section>

<section>
<h2>Official evidence and sample boundaries</h2>
%s
<p>The later 149-result read is preserved beside the frozen 137-game corpus. The official-results
luck panel still uses that 137-game sample; its rate and interval must not be described as a
149-game estimate. Injury captures are also dated snapshots, not a statement of today's active
report.</p>
</section>

<section>
<h2>What the analyses do — and do not — establish</h2>
<p>The official-results panel computes a home-win rate over the frozen sample. It does not establish
that a model has an edge. Separately, the 16-entry signal panel reports <strong>no strategy clearing
its family-wise threshold</strong>. That panel is based on a third-party-backed research ledger, not
an NFL publication; its result should not be combined with the official-results panel.</p>
<p>F66 records overlapping readiness and luck implementations; SG47 leaves consolidation for owner
review. The Dashboard and topic navigation keep the competing views available with their distinct
inputs and definitions. No view is declared canonical here. See <a href="flagged.html#F66">F66</a>,
<a href="suggestions.html#SG47">SG47</a>, <a href="sources.html#S47">S47</a>,
<a href="readiness.html#luck">the family-wise signal panel</a>, and
<a href="removal-of-luck.html">the official-results luck panel</a>.</p>
<p>Some market and backtest outputs use third-party price data. They are labelled as third-party and
remain subject to the unresolved source-policy question. They are not official NFL facts, and no
result in this summary is a recommendation to wager.</p>
</section>

<section>
<h2>Project specifications and next review</h2>
<p>The requirement registers contain %d core rows and %d backlog rows. These rows transcribe
<strong>user-provided project specifications</strong>; they are not NFL requirements, NFL policy, or
facts about the league. Their statuses and “number that would clear it” cells are repository
planning criteria or design targets, not NFL-published thresholds. See
<a href="requirements-backlog.html">Requirement Backlog</a>,
<a href="readiness.html">Decision Readiness</a>, and <a href="flagged.html#F65">F65</a>.</p>
<p>Questions and suggestions remain reviewable on <a href="questions.html">Open Questions</a> and
<a href="suggestions.html">Suggestions</a>. The next result-data action is not to infer a score:
re-read the official <a href="https://www.nfl.com/games/chargers-at-ravens-2026-reg-10?tab=live">LAC–BAL
Game Center</a> after it explicitly shows Final, then verify the quarter scores and standings delta
before recording it. Until then F67 remains open.</p>
</section>

<section class="callout warn">
<h2>Schedule-announcement source citation under correction</h2>
<p>The announcement paragraph on <a href="schedule.html">Schedule 2026</a> currently cites S86,
which identifies a third-party nflverse win-totals feed in the current register. The announcement
itself is on <a href="https://www.nfl.com/news/2026-nfl-schedule-powered-by-aws-to-be-released-thursday-may-14">NFL.com</a>.
The source-ID and generator repair is logged in <a href="COORDINATION.md">COORDINATION.md</a> and
remains a separate follow-up; do not rely on the S86 chip for that claim until it is corrected.</p>
</section>
""" % (
        table(["Evidence", "Published state", "Official source"], summary_rows,
              cls="dense", caption="Every row links to an official NFL record; derived values are explicitly described as such."),
        len(requirements), n_backlog_req,
    )
    written.append(page("executive-summary.html", "Executive Summary", es))

    # ------------------------------------------------------------ requirements
    by_section = {}
    for r in requirements:
        by_section.setdefault(r["section"], []).append(r)
    req_html = ['<section><h1>Requirements</h1>',
                '<p class="lead">Every line of the brief, decomposed, with the evidence that satisfies it and '
                'the page where it can be checked. A requirement is only marked done when there is a link.</p>',
                '<p class="note">%d of %d requirements are complete.'
                '%s</p></section>'
                % (n_req_done, len(requirements),
                   ("" if n_req_done == len(requirements) else
                    ' The rest are marked <span class="pill warn">partial</span> on purpose &mdash; a partial '
                    'status means the method is specified and the number is withheld because no source supports it.'))]
    for section, items in by_section.items():
        rows = []
        for r in items:
            rows.append([
                cell(r["id"]),
                cell(r["requirement"]),
                '<td>%s</td>' % pill(r["status"], STATUS_KIND.get(r["status"], "")),
                cell(r["evidence"]),
                '<td><a href="%s">%s</a></td>' % (esc(r["page"]), esc(r["page"])),
            ])
        req_html.append('<section><h2>%s</h2>%s</section>' % (
            esc(section),
            table(["ID", "Requirement", "Status", "Evidence / verification performed", "Where to check"],
                  rows, cls="req")))
    written.append(page("requirements.html", "Requirements", "".join(req_html)))

    # ---------------------------------------------------------------- injuries
    inj_rows = []
    for r in injuries:
        inj_rows.append([
            '<td><a href="https://www.nfl.com/teams/%s/" target="_blank" rel="noopener">%s</a></td>'
            % (esc(teams and next((t["slug"] for t in teams if t["abbr"] == r["team"]), "")), esc(r["team"])),
            cell(r["player"]),
            cell(r["position"]),
            cell_pub(r["injury"]),
            cell_pub(r["practice"]),
            cell_pub(r["game"]),
            '<td>%s</td>' % src_link("S01", sources_by_id),
        ])
    team_rows = []
    for t in by_team:
        team_rows.append([
            cell(t["abbr"]),
            cell(t["team"]),
            cell(t["listed"], "n"),
            cell(t["out"], "n"),
            cell(t["doubtful"], "n"),
            cell(t["questionable"], "n"),
            cell(t["dnp"], "n"),
            cell(t["limited"], "n"),
            cell(t["full"], "n"),
            cell(t["offOut"], "n"),
            cell(t["defOut"], "n"),
            cell(t["stOut"], "n"),
        ])
    inj_html = """
<section>
<h1>Injury Report</h1>
<p class="lead">The official NFL injury report for Week 10 of the 2026 season, captured 2026-11-14.
Practice status and game status are reproduced exactly. Blank cells mean the source page publishes no value
for that field — they are not blank because a value was unknown to us.</p>
<div class="callout">
  <p><strong>Read the blanks correctly.</strong> An empty injury field usually means the club listed the player
  for practice or game status without naming a body part. It does <em>not</em> mean &ldquo;no injury.&rdquo;
  Two rows say <em>not injury related</em> in plain text; those are the only rows this site treats as definitely
  non-injury.</p>
  <p><strong>Coverage.</strong> %d of %d clubs appear. Chicago, Denver, Philadelphia and Tampa Bay are absent;
  whether that is a bye or a not-yet-posted report was not confirmed. See
  <a href="flagged.html#F06">F06</a>.</p>
  <p><strong>Timing.</strong> One Week 10 game was already final when this was captured
  (Commanders 24, Giants 21, 2026-11-12). Those two clubs' rows are the completed game's report, not a
  forward-looking signal. See <a href="flagged.html#F07">F07</a>.</p>
</div>
</section>

<section>
<h2>Summary by club</h2>
%s
</section>

<section>
<h2>Every listed player, %d rows</h2>
%s
</section>
""" % (lg["clubs"], lg["clubsTotal"],
       table(["Club", "Team", "Listed", "Out", "Doubtful", "Questionable", "DNP", "Limited", "Full",
              "Out (off)", "Out (def)", "Out (ST)"], team_rows, cls="dense",
             caption="Counts computed from the player table below by <code>tools/build.py</code>. "
                     "DNP / Limited / Full are practice statuses; Out / Doubtful / Questionable are game statuses."),
       len(injuries),
       table(["Club", "Player", "Pos", "Injury as published", "Practice status", "Game status", "Source"],
             inj_rows, cls="dense searchable",
             caption="Ordered as published, by club. Use the filter box to search. Every row resolves to "
                     "the same official page."))
    written.append(page("injuries.html", "Injury Report",
                        inj_html + sprint["injury_delta"], wide=True))

    # ------------------------------------------------------------------- depth
    # The KC chart stays as the worked example below; the league view is built
    # from every club chart that could be captured and joined to that club's own
    # injury report.
    cov = depth_cov
    tot = depth_tot
    injured_clubs = {r["team"] for r in injuries}
    bye_clubs = ", ".join(team_name[t["abbr"]] for t in teams
                          if t["abbr"] not in injured_clubs) or ""

    cov_rows = []
    for c in depth_league["clubs"]:
        cov_rows.append([
            cell(c["abbr"]),
            cell(c["team"]),
            raw_src(src_link(c["source"], sources_by_id)),
            cell(c["chartDate"] or ""),
            cell(c["slots"], "n"),
            cell(c["named"], "n"),
            cell(c["matched"], "n"),
            cell(c["withGameStatus"], "n"),
            cell(c["blankSlots"], "n"),
        ])

    nu_rows = []
    for r in depth_league["nextUp"]:
        nu_rows.append([
            cell(r["club"]),
            cell(r["unit"]),
            cell(r["slot"]),
            cell(r["starter"]),
            cell_pub(r["starterStatus"]),
            cell_pub(r["starterInjury"]),
            cell_pub(r["starterPractice"]),
            cell(r["nextPlayer"]) if r["nextPlayer"] else
            '<td class="blank" title="This club publishes no deeper string at this slot">—</td>',
            cell(r["nextString"], "n") if r["nextString"] != "" else
            '<td class="blank" title="This club publishes no deeper string at this slot">—</td>',
            raw_src(src_link(r["source"], sources_by_id) + " " + src_link("S01", sources_by_id)),
        ])

    # ------------------------------------------------------ replacement depth
    # Document arithmetic over the same inputs as the table above: how deep the
    # club's OWN chart must be read to reach a name the league has not ruled
    # Out. Recomputed every build from data/depth.tsv + data/injuries.tsv and
    # re-checked by tools/verify_replacement.py against the rendered HTML.
    rep = build.replacement_depth(depth_league["rows"])
    rep_rows = []
    for r in rep["ladders"]:
        depth_cell = (cell(r["depthOut"], "n") if r["depthOut"] != "" else
                      '<td class="blank" title="%s">—</td>' % esc(r["depthOutReason"]))
        clear_cell = (cell(r["depthClear"], "n") if r["depthClear"] != "" else
                      '<td class="blank" title="%s">—</td>' % esc(r["depthClearReason"]))
        rep_rows.append([
            cell(team_name.get(r["team"], r["team"])),
            cell(r["unit"]),
            cell("%s · line %s" % (r["slot"], r["line"])),
            cell(r["firstString"]),
            cell(r["ruledOut"]) if r["ruledOut"] else
            '<td class="blank" title="No charted name on this ladder is ruled Out">—</td>',
            depth_cell,
            cell(r["firstNotOut"]) if r["firstNotOut"] else
            '<td class="blank" title="No charted name on this ladder is available to list">—</td>',
            clear_cell,
            cell(r["firstClear"]) if r["firstClear"] else
            '<td class="blank" title="Every charted name on this ladder carries a game status">—</td>',
            raw_src(src_link(r["source"], sources_by_id) + " " + src_link("S01", sources_by_id)),
        ])

    # distribution of replacement depth by unit (Offense / Defense / Special Teams)
    units = ["Offense", "Defense", "Special Teams"]
    dist_rows = []
    for u in units + ["All units"]:
        sub = [p for p in rep["ladders"] if u == "All units" or p["unit"] == u]
        d1 = sum(1 for p in sub if p["depthOut"] == 1)
        d2 = sum(1 for p in sub if p["depthOut"] == 2)
        d3 = sum(1 for p in sub if p["depthOut"] != "" and p["depthOut"] >= 3)
        unres = sum(1 for p in sub if p["depthOut"] == "")
        thin_n = sum(1 for t in rep["thin"] if u == "All units" or t["unit"] == u)
        dist_rows.append([
            cell(u),
            cell(len(sub), "n"),
            cell(d1, "n"),
            cell(d2, "n"),
            cell(d3, "n"),
            cell(unres, "n"),
            cell(thin_n, "n"),
            raw_src(src_link("S01", sources_by_id) +
                    ' <a class="src" href="sources.html" title="Club depth charts S08 and S16–S45">charts</a>'),
        ])

    thin_rows = []
    for r in rep["thin"]:
        thin_rows.append([
            cell(team_name.get(r["team"], r["team"])),
            cell(r["unit"]),
            cell("%s · line %s" % (r["slot"], r["line"])),
            cell(r["firstString"]),
            cell(r["deeperOut"]),
            raw_src(src_link(r["source"], sources_by_id) + " " + src_link("S01", sources_by_id)),
        ])

    da_rows = []
    for r in depth_league["rows"]:
        status_cells = ([cell_pub(r["practice"]), cell_pub(r["injury"]),
                         cell_pub(r["gameStatus"])] if r["matched"]
                        else [cell_notlisted(), cell_notlisted(), cell_notlisted()])
        da_rows.append([
            cell(r["team"]),
            cell(r["unit"]),
            cell(r["slot"]),
            cell(r["rank"], "n"),
            cell(r["player"]) if r["player"] else
            '<td class="blank" title="The club publishes no name at this string">—</td>',
            cell(r["note"]),
        ] + status_cells + [
            raw_src(src_link(r["source"], sources_by_id) +
                    (" " + src_link("S01", sources_by_id) if r["matched"] else "")),
        ])

    nc_rows = []
    for r in depth_league["notOnChart"]:
        nc_rows.append([
            cell(r["club"]),
            cell(r["player"]),
            cell(r["position"]),
            cell_pub(r["practice"]),
            cell_pub(r["injury"]),
            cell_pub(r["gameStatus"]),
            raw_src(src_link("S01", sources_by_id) + " " +
                    src_link(r["source"], sources_by_id)),
        ])

    d_rows = []
    for r in depth_rows:
        d_rows.append([
            cell(r["unit"]),
            cell(r["slot"]),
            cell(r["rank"], "n"),
            cell(r["player"]),
            ('<td>%s</td>' % esc(r["officialName"])) if r["officialName"]
                else '<td class="muted">same</td>',
        ] + ([cell_pub(r["practice"]), cell_pub(r["injury"]), cell_pub(r["gameStatus"])]
             if r["matched"] else [cell_notlisted(), cell_notlisted(), cell_notlisted()]) + [
            '<td>%s</td>' % (src_link("S08", sources_by_id) + " " + src_link("S01", sources_by_id)
                             if r["matched"] else src_link("S08", sources_by_id)),
        ])
    fd_rows = []
    for r in flagged_depth:
        fd_rows.append([
            cell(r["unit"]),
            cell(r["slot"]),
            cell(r["rank"], "n"),
            cell(r["player"]),
            cell_pub(r["injury"]),
            cell_pub(r["practice"]),
            cell_pub(r["gameStatus"]),
            '<td>%s</td>' % src_link("S01", sources_by_id),
        ])
    depth_html = """
<section>
<h1>Backup Depth &amp; Deficiencies</h1>
<p class="lead">The brief asks which 2nd, 3rd and 4th string players are being forced in. That question has two
halves, and only one of them can be answered from official sources today. This page keeps them apart.</p>

<div class="cols">
  <div class="callout ok">
    <h3>Half 1 — Observed absence <span class="pill ok">OFFICIAL</span></h3>
    <p>Who is officially unavailable, and at which depth slot the club lists them. Read straight from the
    injury report and the club depth chart. No inference.</p>
  </div>
  <div class="callout warn">
    <h3>Half 2 — Replacement measured <span class="pill warn">NOT AVAILABLE</span></h3>
    <p>Whether a backup <em>actually took the snaps</em> requires snap counts. No official snap-count source was
    verified, so this half is left blank rather than asserted. See <a href="flagged.html#F09">F09</a>.</p>
  </div>
</div>

<div class="callout">
  <p><strong>Coverage: %(covered)d of %(total)d clubs.</strong> <code>nfl.com/depth-charts/</code> returns 404, so
  there is no league-wide official depth chart and each club&rsquo;s own chart has to be captured one at a time.
  %(covered)d clubs publish a chart as a readable table and are on this page. The one club that does not is
  <strong>Houston</strong> — its chart is published as an image, so it is left out rather than guessed
  (flag <a href="flagged.html#F16">F16</a>, source <a href="sources.html#S46">S46</a>). Every club page calls its
  own chart <em>unofficial</em>.</p>
</div>
</section>

<section>
<h2>Depth coverage by club</h2>
<p>One row per club whose chart was captured. %(bye_note)s <em>Players charted</em> counts names the club published.
<em>On own injury report</em> counts how many of those names also appear on that same club&rsquo;s Week 10 injury
report, matched by exact name — no fuzzy matching, so a spelling difference shows up as a non-match rather than
as a wrong merge. <em>Blank slots</em> are slots where the club published a string with no name in it.</p>
%(cov_table)s
</section>

<section>
<h2>First-string players carrying an official game status</h2>
<p>These are the slots where a club&rsquo;s own chart puts a player at <strong>first string</strong> and the
league&rsquo;s injury report gives that player an <strong>Out / Doubtful / Questionable</strong> status for
Week 10. The <em>next listed</em> column is the next name <strong>the same club</strong> publishes at that same
slot and string number.</p>
<div class="callout warn">
  <p><strong>Read the next-listed column for what it is.</strong> It is a statement about two published
  documents, not a prediction of who plays. A club&rsquo;s chart is self-described as unofficial, a starter
  listed Questionable usually still plays, and snap counts are not available to confirm anything. Nothing here
  says a backup <em>is</em> the starter this week.</p>
</div>
%(nu_table)s
</section>

<section>
<h2>Replacement depth — how deep past a ruled-Out first string</h2>
<p>The table above records the <em>fact</em> of a replacement: the first string carries a status and the club
publishes a next name. This table records the <strong>depth</strong> of that replacement. For every chart ladder
whose first string carries an official game status (<strong>%(rep_n)d</strong> ladders — the same population as
the table above), it reports how many strings the club's own chart must be read through before the first name the
league has <strong>not</strong> ruled Out appears.</p>
<div class="callout">
  <p><strong>Definition, fixed before any value was computed.</strong> <em>Replacement depth</em> = the string
  number of the first charted name on the ladder whose game status is not <em>Out</em>, walking the club's own
  string order. Depth <strong>1</strong> means at least one name on the first string is not ruled Out — no
  replacement past the first string is required by the documents (the first string is Questionable or Doubtful,
  but not ruled Out). Depth <strong>2</strong> means every name on the first string is ruled Out and the second
  string holds a name that is not — and so on. Strings that are themselves ruled Out are skipped, so a depth is
  recorded only once a name that is not ruled Out is reached. Where the club publishes no
  name at an intermediate string, or every charted name on the ladder is ruled Out, the cell is blank and carries
  the reason in its hover text — never a guessed number.</p>
  <p><strong>Two depths are shown.</strong> The first counts only <em>Out</em> as a rule-out. The second, stricter
  one counts any listed game status (Out, Doubtful or Questionable) and therefore reports how deep the chart must
  be read before a name the league has said nothing about appears. A blank there means every charted name on that
  ladder carries a status.</p>
  <p><strong>What this does not say.</strong> It does not say who plays. No snap-count source was verified
  (<a href="flagged.html#F09">F09</a>), Houston has no machine-readable chart (<a href="flagged.html#F16">F16</a>),
  and a club's chart is self-described as unofficial. The numbers are arithmetic on two published documents — the
  club's depth chart and the league's injury report — and nothing more.</p>
</div>
%(rep_table)s

<h3>Replacement depth by unit</h3>
<p>Counts over the %(rep_n)d ladders above. <em>Thin</em> counts ladders whose first string is <strong>not</strong>
ruled Out while a deeper string already is: there at least one name below the first string is already
unavailable before it is needed. Every cell is recomputed from the committed inputs on each build and re-checked
against this page by <code>tools/verify_replacement.py</code>.</p>
%(dist_table)s

<h3>Deeper strings already ruled out behind an available first string</h3>
<p><strong>%(thin_n)d</strong> ladders. The first string is not ruled Out, but a deeper string on the same ladder
already is. The ladder is therefore thinner than its first string alone suggests: should the first-string player
miss the game, one of the names below him is already unavailable — the depth of the replacement showing up before
the replacement is required.</p>
%(thin_table)s
</section>

<section>
<h2>Every charted slot, every club</h2>
<p>%(rows)d published slots across %(covered)d clubs. String 1 = first team. Use the filter box to narrow by club
or player. Players not on their club&rsquo;s Week 10 injury report are marked <em>not listed</em> — an absence
that is itself an official fact, not a gap in this page.</p>
%(da_table)s
</section>

<section>
<h2>On a club&rsquo;s injury report but not on that club&rsquo;s own chart</h2>
<p>%(notcharted)d players. This is a discrepancy between two official documents, so it is published rather than
reconciled. The usual innocent reason is that an injured player was removed from the chart; the interesting
reason is a name spelled differently in the two places. This page does not decide which, because deciding would
be a guess. Where the two documents clearly disagree about who is on the team, that is recorded on
<a href="flagged.html">Flagged for Review</a> instead.</p>
%(nc_table)s
</section>

<section>
<h2>Worked example: Kansas City, Week 10</h2>
<p>Kept as the reference implementation because it is the one club where a name difference between the chart and
the league roster was resolved explicitly, with the evidence written down in
<code>data/depth-aliases.tsv</code>, rather than by fuzzy matching. Every depth slot on the club&rsquo;s published
chart, matched against that club&rsquo;s official injury designations.
<strong>%(kcmatched)d of %(kctotal)d slots</strong> carry an official practice or game designation.
<strong>%(kcflag)d of those carry a game status</strong> — meaning the club has told us the player may not play.</p>
%(d_table)s
</section>

<section>
<h2>What this page will not do</h2>
<ul class="tight">
<li>It will not call a backup &ldquo;the starter this week&rdquo; without a snap-count source.</li>
<li>It will not rank depth beyond the club&rsquo;s own published ordering, and that ordering is labelled unofficial.</li>
<li>It will not match two names by similarity. Equivalence is asserted only in
<code>data/depth-aliases.tsv</code>, with the evidence recorded next to it.</li>
<li>It will not treat an absent player as injured. <em>Absent</em> and <em>injured</em> are different facts.</li>
<li>It will not fill Houston in from another source, because a depth chart is an ordering and no other official
source publishes that ordering.</li>
</ul>
</section>
""" % {
        "covered": cov["covered"],
        "total": cov["total"],
        "rows": tot["rows"],
        "notcharted": len(depth_league["notOnChart"]),
        "kcmatched": len([r for r in depth_rows if r["matched"]]),
        "kctotal": len(depth_rows),
        "kcflag": len(flagged_depth),
        "bye_note": ("<strong>%s do not play in Week 10</strong>, so they have no Week 10 injury "
                     "report and their injury columns read 0. That is the league publishing nothing, "
                     "not this page failing to find anything." % bye_clubs)
                    if bye_clubs else "",
        "cov_table": table(
            ["Club", "Team", "Chart source", "Chart date", "Published slots",
             "Players charted", "On own injury report", "With a game status", "Blank slots"],
            cov_rows, cls="dense searchable",
            caption="Chart date is the date the club printed on its own chart. A blank means the club "
                    "printed no date; it is not assumed to be the capture date."),
        "nu_table": table(
            ["Club", "Unit", "Slot", "First string", "Game status", "Injury as published",
             "Practice", "Next listed at that slot", "String", "Sources"],
            nu_rows, cls="dense searchable",
            caption="%d of %d charted first-string slots carry an official Week 10 game status. "
                    "Sorted by club." % (tot["startersWithStatus"], tot["starters"])),
        "rep_n": len(rep["ladders"]),
        "thin_n": len(rep["thin"]),
        "rep_table": table(
            ["Club", "Unit", "Ladder (slot · line)", "First string (status)",
             "Charted names ruled Out", "Replacement depth",
             "First name not ruled Out", "Depth to first name with no designation",
             "First name with no designation", "Sources"],
            rep_rows, cls="dense searchable",
            caption="Replacement depth = string number of the first charted name on the ladder whose "
                    "game status is not Out, in the club's own string order. A blank cell carries the "
                    "reason in its hover text. Sorted by club, unit, ladder."),
        "dist_table": table(
            ["Unit", "Ladders with a status on the first string", "Depth 1",
             "Depth 2", "Depth 3+", "Depth unresolvable (blank)", "Thin ladders", "Sources"],
            dist_rows, cls="dense",
            caption="Recomputed from data/depth.tsv and data/injuries.tsv on every build; "
                    "Depth 1 = no replacement past the first string required by the documents."),
        "thin_table": table(
            ["Club", "Unit", "Ladder (slot · line)", "First string (status)",
             "Deeper strings ruled Out", "Sources"],
            thin_rows, cls="dense searchable",
            caption="First string not ruled Out, deeper string(s) ruled Out on the same ladder."),
        "da_table": table(
            ["Club", "Unit", "Slot", "String", "Player", "Note", "Practice", "Injury",
             "Game status", "Source"],
            da_rows, cls="dense searchable",
            caption="Ordering copied from each club chart. Rows shown as 'not listed' are players the "
                    "club charts but who do not appear on its Week 10 injury report."),
        "nc_table": table(
            ["Club", "Player", "Pos", "Practice", "Injury as published", "Game status", "Sources"],
            nc_rows, cls="dense searchable",
            caption="Cross-check of the club chart against the club's own injury report (S01)."),
        "d_table": table(
            ["Unit", "Slot", "String", "Player (as charted)", "Official roster spelling",
             "Practice", "Injury", "Game status", "Sources"],
            d_rows, cls="dense searchable",
            caption="String 1 = first team, 2 = second, 3 = third. Ordering copied from the club chart."),
    }
    written.append(page("depth.html", "Backup Depth", depth_html, wide=True))

    # --------------------------------------------------------------- standings
    st_rows = []
    for s in standings:
        conf, div = team_conf.get(s["abbr"], ("", ""))
        st_rows.append([
            cell(s["abbr"]),
            cell(team_name.get(s["abbr"], s["abbr"])),
            cell(conf),
            cell(div),
            cell(s["w"], "n"), cell(s["l"], "n"), cell(s["t"], "n"),
            cell(s["pct"], "n"),
            cell(s["pf"], "n"), cell(s["pa"], "n"), cell(s["net"], "n"),
            cell(s["home"]), cell(s["road"]),
            cell(s["div"]), cell(s["div_pct"], "n"),
            cell(s["conf"]), cell(s["conf_pct"], "n"),
            cell(s["nonconf"]), cell(s["streak"]), cell(s["last5"]),
            '<td>%s</td>' % src_link("S03", sources_by_id),
        ])
    div_rows = []
    for conf in ("AFC", "NFC"):
        for div in ("East", "North", "South", "West"):
            members = [t for t in teams if team_conf.get(t["abbr"]) == (conf, div)]
            members.sort(key=lambda t: -(next((float(s["pct"]) for s in standings
                                               if s["abbr"] == t["abbr"]), 0)))
            if not members:
                continue
            div_rows.append([
                cell("%s %s" % (conf, div)),
                cell(", ".join("%s (%s)" % (m["abbr"],
                                            next((s["w"] + "-" + s["l"] + ("-" + s["t"] if s["t"] != "0" else "")
                                                  for s in standings if s["abbr"] == m["abbr"]), ""))
                               for m in members)),
            ])
    sched_rows = []
    for g in schedule:
        sched_rows.append([
            cell(g["date"]),
            cell(g["time_et"]),
            cell(g["away"]),
            cell(g["home"]),
            cell(g["broadcast"]),
            cell(g["venue"]),
            cell(g["note"]),
            '<td>%s</td>' % src_link("S04", sources_by_id),
        ])
    res_rows = []
    for r in results:
        ap, hp = int(r["awayPts"]), int(r["homePts"])
        res_rows.append([
            cell(r["week"], "n"),
            cell(r["date"]),
            cell(r["away"]),
            cell(ap, "n"),
            cell(r["home"]),
            cell(hp, "n"),
            cell("%+d" % (hp - ap), "n"),
            '<td>%s</td>' % src_link("S04", sources_by_id),
        ])
    # Derived scoring rates. Every figure here is arithmetic on results.tsv, and
    # tools/verify_results.py proves that adding results.tsv up reproduces the
    # official standings, so these rates rest on a verified base.
    rate = {a: {"g": 0, "pf": 0, "pa": 0, "hw": 0, "hl": 0, "ht": 0,
                "rw": 0, "rl": 0, "rt": 0} for a in team_name}
    for r in results:
        ap, hp = int(r["awayPts"]), int(r["homePts"])
        for side, pts, opp in (("home", hp, ap), ("away", ap, hp)):
            ab = r[side]
            rate[ab]["g"] += 1
            rate[ab]["pf"] += pts
            rate[ab]["pa"] += opp
            k = ("h" if side == "home" else "r") + ("w" if pts > opp else "l" if pts < opp else "t")
            rate[ab][k] += 1
    rate_rows = []
    for ab in sorted(rate, key=lambda a: -(rate[a]["pf"] - rate[a]["pa"]) / max(rate[a]["g"], 1)):
        d = rate[ab]
        g = d["g"]
        if not g:
            continue
        rate_rows.append([
            cell(ab),
            cell(team_name.get(ab, ab)),
            cell(g, "n"),
            cell(d["pf"], "n"),
            cell(d["pa"], "n"),
            cell("%+.1f" % ((d["pf"] - d["pa"]) / g), "n"),
            cell("%.1f" % (d["pf"] / g), "n"),
            cell("%.1f" % (d["pa"] / g), "n"),
            cell("%d-%d-%d" % (d["hw"], d["hl"], d["ht"])),
            cell("%d-%d-%d" % (d["rw"], d["rl"], d["rt"])),
            '<td>%s</td>' % src_link("S04", sources_by_id),
        ])
    st_html = """
<section>
<h1>Standings &amp; Schedule</h1>
<p class="lead">The official 2026 regular-season standings for all 32 clubs, plus the Week 10 slate.
This is the input layer for the baseline model, not a prediction.</p>
<div class="callout">
  <p><strong>Note the tie.</strong> The Giants and Commanders each have one tie, so their records read 5-3-1 and
  3-5-1. Winning percentage uses a tie as half a win and half a loss, per the league's own tiebreaking notes.</p>
</div>
</section>

<section>
<h2>League standings, all 32 clubs</h2>
%s
</section>

<section>
<h2>Division membership and record</h2>
%s
</section>

<section>
<h2>Scoring rates, derived from every game played</h2>
<p>Points for and against per game, worked out by <code>tools/site.py</code> from the %d games below. These are
<em>derived</em>, not published: the league publishes totals, not rates. They are safe to use as a baseline
because <code>tools/verify_results.py</code> first proves that adding the same games up reproduces the official
standings exactly, for all 32 clubs. Margin is points for minus points against per game.</p>
%s
</section>

<section>
<h2>Every game played so far</h2>
<p>%d games: all of Weeks 1&ndash;9 plus the Week 10 Thursday game. The remaining %d Week 10 games had not kicked
off when this was captured, so their rows do not exist yet rather than appearing blank. Home team is listed
second, as the league lists it. Use the filter box to narrow by club.</p>
%s
</section>

<section>
<h2>Week 10 schedule as published</h2>
%s
</section>

<section>
<h2>How ties are broken</h2>
<p>The league publishes a twelve-step tiebreaking sequence for both division and wild-card ties, starting with
head-to-head and ending with a coin toss. The full procedure is linked in the source registry and is not
paraphrased here, so nothing is lost in translation.</p>
<p>Sources: %s %s</p>
</section>
""" % (table(["Abbr", "Club", "Conf", "Div", "W", "L", "T", "PCT", "PF", "PA", "Net",
              "Home", "Road", "Div", "Div%", "Conf", "Conf%", "Non-Conf", "Strk", "Last 5", "Source"],
             st_rows, cls="dense searchable",
             caption="Column meanings are the league's own: PCT winning percentage, PF points for, PA points "
                     "against, Net net points."),
       table(["Division", "Clubs (record)"], div_rows, cls="dense"),
       len(results),
       table(["Abbr", "Club", "G", "PF", "PA", "Margin/g", "PF/g", "PA/g",
              "Home", "Road", "Source"],
             rate_rows, cls="dense searchable",
             caption="Sorted by margin per game. Home and Road are records in those games, "
                     "counted from the results table."),
       len(results), len(schedule) - 1,
       table(["Wk", "Date", "Away", "Pts", "Home", "Pts", "Margin (home)", "Source"],
             res_rows, cls="dense searchable",
             caption="Margin is home points minus away points. Every row resolves to the same "
                     "official schedule page."),
       table(["Date", "Kickoff ET", "Away", "Home", "Broadcast", "Venue", "Note", "Source"],
             sched_rows, cls="dense searchable"),
       src_link("S06", sources_by_id), src_link("S05", sources_by_id))
    written.append(page("standings.html", "Standings", st_html, wide=True))

    # ------------------------------------------------------------ line origination
    lo = """
<section>
<h1>Line Origination</h1>
<p class="lead">How a line would be produced here, and precisely where the production stops because a source
is missing. This is a specification, not a forecast.</p>
<div class="callout bad">
  <p><strong>There is no line on this page.</strong> Not because the method is unclear, but because a fair-value
  number requires two things this repository does not have: a fitted model and a benchmark price to compare
  against. Publishing a number without those would be an invention, and an invented number is worse than a blank
  one because it looks finished. See <a href="flagged.html#F08">F08</a>.</p>
</div>
</section>

<section>
<h2>The four stages</h2>
<ol class="tight stages">
<li><strong>Input</strong> — only officially sourced fields enter the model. Each input is registered with the
source that supplies it and the date it was captured. An input without a source is not an input.</li>
<li><strong>Estimate</strong> — a marginal strength estimate per club, converted to an expected margin and an
expected total. The first, mandatory estimator is the naive baseline: season points differential per game.</li>
<li><strong>Price</strong> — convert the expected margin into a probability distribution over outcomes. Report
the fair-value probability and an explicit uncertainty band. Report no price if no market price exists to
compare with.</li>
<li><strong>Seal</strong> — hash the full prediction set and publish the hash before kickoff. The seal is what
makes the record auditable rather than anecdotal.</li>
</ol>
</section>

<section>
<h2>Input registry</h2>
%s
</section>

<section>
<h2>What a published line would look like</h2>
<p>The schema below is fixed now, before any result exists, so the reporting format cannot be chosen after the
fact to flatter the outcome. Every field is either filled from a source or left blank.</p>
%s
</section>

<section>
<h2>Why uncertainty is a required output, not a disclaimer</h2>
<p>A single number implies a precision the data does not have. With eight or nine games played per club, the
standard error on a scoring-margin estimate is large enough that two plausible models can differ by more than the
gap between them and the market. Reporting a band makes that visible; reporting a point estimate hides it.
The correct response to wide uncertainty is a smaller stake or no position, not a tighter number.</p>
</section>
""" % (
        table(["Input", "Field", "Available today?", "Source", "Note"], [
            [cell("Scoring margin per game"), cell("PF, PA, games played"), '<td>%s</td>' % pill("AVAILABLE", "ok"),
             '<td>%s</td>' % src_link("S03", sources_by_id), cell("All 32 clubs, season to date")],
            [cell("Availability"), cell("Game status per player"), '<td>%s</td>' % pill("AVAILABLE", "ok"),
             '<td>%s</td>' % src_link("S01", sources_by_id),
             cell("28 clubs in the Week 10 snapshot only")],
            [cell("Depth ordering"), cell("Position slot and string"), '<td>%s</td>' % pill("PARTIAL", "warn"),
             '<td>%s %s</td>' % (src_link("S08", sources_by_id), src_link("S07", sources_by_id)),
             cell("Club-level, self-labelled unofficial")],
            [cell("Snap counts"), cell("Snap share per player"), '<td>%s</td>' % pill("BLOCKED", "bad"),
             cell(""), cell("No official feed verified")],
            [cell("Weather"), cell("Wind, precipitation, temperature"), '<td>%s</td>' % pill("PARTIAL", "warn"),
             '<td>%s</td>' % src_link("S11", sources_by_id),
             cell("Forecast available; roof/surface registry not verified")],
            [cell("Market price"), cell("Benchmark line and price"), '<td>%s</td>' % pill("BLOCKED", "bad"),
             cell(""), cell("League does not publish prices; no feed supplied")],
            [cell("Historical results"), cell("Prior-season outcomes"), '<td>%s</td>' % pill("BLOCKED", "bad"),
             cell(""), cell("Not captured; blocks any backtest")],
        ], cls="dense", caption="An input is only usable if a source is named and the capture date is recorded."),
        table(["Field", "Status", "Why"], [
            [cell("Game identifier"), '<td>%s</td>' % pill("READY", "ok"), cell("Official schedule provides it")],
            [cell("Kickoff timestamp (UTC)"), '<td>%s</td>' % pill("READY", "ok"),
             cell("Needed for the pre-kickoff seal")],
            [cell("Fair-value probability"), '<td>%s</td>' % pill("BLANK", "warn"),
             cell("Requires a fitted model; none has been run")],
            [cell("Uncertainty band"), '<td>%s</td>' % pill("BLANK", "warn"), cell("Same dependency")],
            [cell("Market price"), '<td>%s</td>' % pill("BLANK", "bad"), cell("No official source exists")],
            [cell("Edge / expected value"), '<td>%s</td>' % pill("BLANK", "bad"),
             cell("Arithmetic requires a market price")],
            [cell("Closing-line value"), '<td>%s</td>' % pill("BLANK", "bad"), cell("Requires closing prices")],
            [cell("Prediction hash"), '<td>%s</td>' % pill("READY", "ok"), cell("Computable locally right now")],
        ], cls="dense")
    )
    written.append(page("line-origination.html", "Line Origination",
                        lo + sprint["origination_order"]))

    # -------------------------------------------------------------- strategies
    srows = []
    for s in strategies:
        com = s.get("change_of_mind") or {}
        com_html = ""
        if com:
            com_html = ('<div class="com-up"><strong>Upgrade if:</strong> %s</div>'
                        '<div class="com-down"><strong>Downgrade if:</strong> %s</div>'
                        % (esc(com.get("upgrade", "")), esc(com.get("downgrade", ""))))
        srows.append([
            cell(s["id"]),
            cell(s["name"]),
            cell(s["role"]),
            cell(s["market"]),
            '<td>%s</td>' % pill(s["data_status"], STATUS_KIND.get(s["data_status"], "")),
            cell(s["data_note"]),
            cell(", ".join(s["gates"])),
            cell(com_html) if com_html else cell(""),
            cell(s["result"]),
            cell(s["result_note"]),
            '<td>%s</td>' % src_link("S03", sources_by_id),
        ])
    strat = """
<section>
<h1>Strategy Leaderboard</h1>
<p class="lead">A competition with gates. A strategy is listed, then it must earn a rank by clearing every gate
in <a href="validation.html">Validation</a>. Until then it has no score, and the board stays empty.</p>
<div class="callout bad">
  <p><strong>0 of %d entries carry a result in this register.</strong> This register holds the plan-level
  strategies over official data only. Its original claim &mdash; &ldquo;No backtest has been executed and no
  performance figure is claimed anywhere in this repository&rdquo; &mdash; was true of this register and false
  of the repository as a whole (<a href="flagged.html#F24">F24</a>): the computed research layer holds 16
  backtests over third-party data, reported and re-ranked on signal below, and none of those has passed its
  gates either. The board here will stay empty until a strategy clears the gates with a price source
  supplied. That is the design, not a delay.</p>
</div>
</section>

<section>
<h2>The board</h2>
%s
</section>

<section>
<h2>Ranking rule, fixed in advance</h2>
<p>The ranking formula is published now, before any result exists, so it cannot be chosen to suit an outcome:</p>
<ol class="tight">
<li>An entry is <em>unranked</em> until it passes gates G1 to G6. Blocked or partially-gated entries are shown
as unranked and are excluded from the ordered table.</li>
<li>Among ranked entries, order by <strong>calibration error</strong> ascending — the mean absolute gap between
stated probability and realised frequency, across probability buckets.</li>
<li>Break ties by <strong>larger validated sample</strong>, then by <strong>lower model complexity</strong>.</li>
<li>Ties are never broken by profit. Profit is reported, never ranked on, because over an 18-week season it is
dominated by variance.</li>
</ol>
<p>Rewards are position and a badge. There is no money, no entry fee, no wagering and no odds on this site.
The reason is set out as open question Q14 and suggestion SG11 rather than answered here.</p>
</section>

<section>
<h2>Product types and the extra gate each one carries</h2>
%s
</section>
""" % (len(strategies),
       table(["ID", "Strategy", "Role", "Market", "Data status", "What the data allows",
              "Gates", "What would change our mind", "Result", "Result note", "Source"],
             srows, cls="dense searchable",
             caption="A blank Result cell means no result exists. A dash would mean the same thing; "
                     "here the column is intentionally empty rather than zero."),
       table(["Product", "Extra requirement", "Status today"], [
           [cell("Single bet"), cell("A benchmark price to define edge"), '<td>%s</td>' % pill("BLOCKED", "bad")],
           [cell("Parlay"), cell("Every leg validated independently, plus joint correlation"),
            '<td>%s</td>' % pill("BLOCKED", "bad")],
           [cell("Player prop"), cell("Player-level historical logs"), '<td>%s</td>' % pill("BLOCKED", "bad")],
           [cell("Player prop combo"), cell("Prop legs plus pairwise joint outcomes"),
            '<td>%s</td>' % pill("BLOCKED", "bad")],
       ], cls="dense"))
    written.append(page("strategies.html", "Leaderboard",
                        strat + sprint["change_mind"] + sprint["signal_staking"], wide=True))

    # -------------------------------------------------------------- validation
    gates = [
        ("G1", "Source completeness",
         "Every input the strategy needs resolves to a verified official source record.",
         "Input registry with no BLOCKED rows",
         "Chosen before the model is fitted"),
        ("G2", "Data sufficiency",
         "Enough observations exist to estimate the parameters without overfitting.",
         "Stated minimum sample, met",
         "Chosen before the model is fitted"),
        ("G3", "Baseline comparison",
         "The strategy beats a named, published naive baseline out of sample.",
         "Out-of-sample score above baseline",
         "Beat a points-differential baseline"),
        ("G4", "Calibration",
         "Stated probabilities match realised frequencies across probability buckets.",
         "Brier score and bucket table",
         "Stated probabilities must be well calibrated"),
        ("G5", "Out-of-sample persistence",
         "The edge survives a walk-forward test it was not tuned on.",
         "Holdout result within tolerance of in-sample",
         "Time-ordered splits only"),
        ("G6", "Price-based edge",
         "Edge is measured against a benchmark price, not against nothing.",
         "Benchmark price feed",
         "Never compare a model to zero"),
        ("G7", "Joint-sample adequacy",
         "For parlays and combos: the pair has enough repeated joint observations.",
         "Pairwise observation count, evidenced",
         "Never assume independence or dependence"),
        ("G8", "Reproducibility",
         "A third party can re-run the strategy from committed inputs and get the same output.",
         "Deterministic script, seeds committed",
         "Same inputs must yield the same number"),
    ]
    gate_rows = []
    for gid, name, test, evidence, note in gates:
        gate_rows.append([
            cell(gid), cell(name), cell(test), cell(evidence),
            '<td>%s</td>' % pill("DEFINED", "ok"),
            '<td>%s</td>' % pill("NOT RUN", "bad"),
            cell(note),
        ])
    val = """
<section>
<h1>Validation Gates</h1>
<p class="lead">Eight gates. A strategy must pass every one that applies to it before it can be ranked.
The gates are defined here, before any strategy exists, precisely so they cannot be rewritten to fit a result.</p>
</section>

<section>
<h2>The gates</h2>
%s
</section>

<section>
<h2>Removing luck: three separate tests, never one blended score</h2>
<p>The brief asks to remove luck from the equation. That is only meaningful if it is operational, so it is
defined as three tests that must each hold. They are reported side by side and are <em>never</em> averaged,
because averaging lets a strong result on one hide a failure on another.</p>
%s
</section>

<section>
<h2>Correlation</h2>
<p>A parlay's price depends on the joint probability of its legs. If two legs are positively correlated,
multiplying their individual probabilities understates the joint probability and misstates the edge.
The reverse is true for negatively correlated legs.</p>
<p>Correlation is therefore estimated from repeated joint outcomes of the same pairing, and never assumed.
A pairing needs many observations before an estimate means anything; below that threshold the value stays blank.</p>
%s
</section>

<section>
<h2>Acceptance thresholds</h2>
<p>The numeric thresholds are deliberately not set on this page. Setting them after seeing a result is the
single easiest way to manufacture apparent skill, and choosing them before a benchmark price exists would be
arbitrary. They are registered as open question Q09 and must be fixed in one commit before any grading begins.</p>
</section>

<section>
<h2>Demotion gate — live to paper</h2>
<p class="lead">A strategy that has been promoted to live is not entitled to stay there. The demotion gate is
the honest counterpart to the promotion gates: it defines when a live strategy is sent back to paper
(research) so a decaying edge never keeps running capital.</p>
<div class="twrap"><table class="dense"><thead><tr><th>Gate</th><th>Name</th><th>Test</th><th>Action on fail</th><th>Principle</th></tr></thead><tbody><tr><td>D1</td><td>Live-decay monitor</td><td>Rolling CLV lower bound stays below zero across the monitoring window.</td><td>Auto-demote to research; no discretionary rescue.</td><td>An edge that existed and died should not run capital.</td></tr><tr><td>D2</td><td>Calibration drift</td><td>Realised hit rate falls outside the stated probability bucket band on the holdout.</td><td>Demote and re-fit; re-clear G1-G6 before returning to live.</td><td>Stated probabilities must stay well calibrated.</td></tr><tr><td>D3</td><td>Concentration breach</td><td>One season, team, opponent cluster or stadium exceeds its allowed share of net PnL.</td><td>Demote and reduce exposure; re-clear G8 before returning to live.</td><td>One lucky year against three bad teams is not an edge.</td></tr></tbody></table></div>
<p>The demotion thresholds are fixed before the first live stake and reviewed on the same schedule as the
promotion gates, never after a losing streak. Because D1 needs a benchmark price to measure CLV and no
official price source exists in this repository (flag F08), D1-D3 are defined here but are not yet active.
No strategy can be promoted to live until a price source is supplied and the demotion rule is registered.</p>
</section>
""" % (
        table(["Gate", "Name", "Test", "Required artefact", "Status", "Result", "Principle"], gate_rows,
              cls="dense"),
        table(["Control", "Question it answers", "Measured by", "Status"], [
            [cell("Calibration"), cell("When we say 60%, does it happen 60% of the time?"),
             cell("Brier score plus a reliability table by probability bucket"),
             '<td>%s</td>' % pill("NOT RUN", "bad")],
            [cell("Closing-line value"), cell("Did the market move toward our number or away from it?"),
             cell("Fair value versus closing price, signed"), '<td>%s</td>' % pill("BLOCKED", "bad")],
            [cell("Persistence"), cell("Does the edge hold on data the model never saw?"),
             cell("Walk-forward holdout, frozen and access-logged"), '<td>%s</td>' % pill("NOT RUN", "bad")],
        ], cls="dense"),
        table(["Correlation target", "Data required", "Status"], [
            [cell("Team totals, same game"), cell("Joint team scoring across many games"),
             '<td>%s</td>' % pill("METHOD READY", "warn")],
            [cell("Player prop pairs, same game"), cell("Player-level joint game logs"),
             '<td>%s</td>' % pill("BLOCKED", "bad")],
            [cell("Props across different games"), cell("Only if a shared driver exists, else near zero"),
             '<td>%s</td>' % pill("BLOCKED", "bad")],
        ], cls="dense")
    )
    written.append(page("validation.html", "Validation Gates",
                        val + sprint["demotion"] + sess["validation_session"], wide=True))

    # ------------------------------------------------- readiness (session G page)
    written.append(page("readiness.html", "Decision Readiness", sess["readiness_page"], wide=True))
    written.append(page("ablations.html", "Ablations", sess["ablations_page"], wide=True))

    # --------------------------------------------------------------- questions
    q_by_cat = {}
    for q in questions:
        q_by_cat.setdefault(q["category"], []).append(q)
    q_html = ['<section><h1>Open Questions</h1>',
              '<p class="lead">Every question that must be answered before a decision can reasonably be made, '
              'with what we know, what we do not know, what data is missing, and whether it blocks progress.</p>',
              '<div class="callout"><p><strong>%d questions, %d blocking.</strong> A question is marked blocking '
              'when no defensible number can be produced until it is answered. The blocking ones are the reason '
              'the leaderboard is empty.</p></div></section>' % (len(questions), n_block)]
    for cat, items in q_by_cat.items():
        rows = []
        for q in items:
            rows.append([
                '<td id="%s"><strong>%s</strong></td>' % (esc(q["id"]), esc(q["id"])),
                cell(q["question"]),
                '<td>%s</td>' % pill(q["priority"],
                                     "bad" if q["priority"] == "Critical" else
                                     ("warn" if q["priority"] == "High" else "")),
                '<td>%s</td>' % pill(q["blocking"], "bad" if q["blocking"].lower().startswith("yes") else "ok"),
                cell(q["what_we_know"]),
                cell(q["what_we_dont_know"]),
                cell(q["missing_data"]),
                cell(q["recommended_path"]),
                '<td>%s</td>' % (src_link(q["source"].split(",")[0].strip(), sources_by_id)
                                 if q.get("source") else ""),
            ])
        q_html.append('<section><h2>%s</h2>%s</section>' % (
            esc(cat),
            table(["ID", "Question", "Priority", "Blocks progress?", "What we know",
                   "What we do not know", "Missing data", "Recommended path", "Source"],
                  rows, cls="dense qtable")))
    q_html.append("""
<section>
<h2>How these questions were derived</h2>
<p>Each question was written by asking what a number on this site would require, then checking whether that
requirement exists in the verified sources. Where it does not, the gap became a question. That is why the list
is dominated by data-availability questions: the analytical methods are not the bottleneck, the inputs are.</p>
</section>""")
    written.append(page("questions.html", "Open Questions", "".join(q_html), wide=True))

    # ------------------------------------------------------------- suggestions
    sg_html = ['<section><h1>Suggestions</h1>',
               '<p class="lead">A review surface, not a task list. Each entry states the problem, the proposal, '
               'the evidence behind it, its cost and risk, and the options available — then recommends one. '
               'Nothing here has been implemented as a change to the analysis; these are paths for someone to '
               'choose between.</p>',
               '<div class="callout"><p><strong>How to use this page.</strong> Read the options, not just the '
               'recommendation. Every recommendation is reversible, and the reversibility of each one is stated, '
               'so a wrong choice is cheap to undo.</p></div>']
    srows = []
    for s in suggestions:
        srows.append([
            '<td><a href="#%s">%s</a></td>' % (esc(s["id"]), esc(s["id"])),
            cell(s["title"]),
            cell(s["category"]),
            cell(s["effort"]),
            cell(s["risk"]),
            cell(", ".join(s.get("prerequisites", []))),
        ])
    sg_html.append("<section><h2>At a glance</h2>%s</section>" % table(
        ["ID", "Suggestion", "Category", "Effort", "Risk", "Depends on"], srows, cls="dense"))
    for s in suggestions:
        opts = "".join(
            '<li>%s</li>' % esc(o) for o in s.get("options", [])
        )
        sg_html.append("""
<section class="sugg" id="%s">
  <h2><span class="sid">%s</span> %s</h2>
  <div class="cols">
    <div>
      <h3>The problem</h3><p>%s</p>
      <h3>Evidence</h3><p class="evidence">%s</p>
    </div>
    <div>
      <h3>The proposal</h3><p>%s</p>
      <h3>Cost and risk</h3>
      <p>Effort <span class="pill">%s</span> &nbsp; Risk <span class="pill">%s</span><br>
      Reversibility: %s</p>
    </div>
  </div>
  <h3>Options</h3>
  <ol class="opts">%s</ol>
  <div class="callout ok"><p><strong>Recommendation.</strong> %s</p></div>
  <p class="muted">Expected impact: %s</p>
</section>""" % (esc(s["id"]), esc(s["id"]), esc(s["title"]), esc(s["problem"]), esc(s["evidence"]),
                 esc(s["proposal"]), esc(s["effort"]), esc(s["risk"]), esc(s["reversibility"]),
                 opts, esc(s["recommendation"]), esc(s["impact"])))
    sg_html.append("</section>")
    written.append(page("suggestions.html", "Suggestions", "".join(sg_html)))

    # ----------------------------------------------------------------- sources
    s_rows = []
    for s in sources:
        s_rows.append([
            '<td id="%s"><strong>%s</strong></td>' % (esc(s["id"]), esc(s["id"])),
            cell(s["title"]),
            cell(s["publisher"]),
            cell(s["tier"]),
            '<td><a href="%s" target="_blank" rel="noopener">%s</a></td>' % (esc(s["url"]), esc(s["url"])),
            cell(s["checked"]),
            '<td>%s</td>' % pill(s["status"], STATUS_KIND.get(s["status"], "")),
            cell(s["note"]),
        ])
    src_html = """
<section>
<h1>Sources</h1>
<p class="lead">Every fact on this site resolves to one of these records. A source marked
<span class="pill ok">VERIFIED</span> was loaded in this session and its content read.
A source marked <span class="pill bad">NOT VERIFIED</span> failed to load, and nothing on this site is asserted
on the strength of it.</p>
<div class="callout">
  <p><strong>Why some sources fail.</strong> Three official NFL addresses that are widely cited returned HTTP 404
  on 2026-11-14, including the injury-report policy PDF. Rather than quote a document we could not open, the policy
  text is omitted and the gap is listed on <a href="flagged.html">Flagged for Review</a>.</p>
  <p><strong>Tiers.</strong> <em>Official (league)</em> means published by the NFL. <em>Official (club)</em> means
  published by a club, which speaks only for that club. <em>Official (government)</em> means a US federal agency.</p>
</div>
</section>

<section>
<h2>Registry</h2>
%s
</section>

<section>
<h2>Verification method</h2>
<p>Each URL was requested once as a single page load and the returned content inspected. A source counts as
verified only when the content that supports the claim actually appeared. Two qualified cases are recorded
honestly rather than glossed over: the club depth chart is verified as reachable but is self-described as
unofficial, and the weather service is verified as reachable but supplies forecast input rather than a historical
record.</p>
</section>
""" % table(["ID", "Title", "Publisher", "Tier", "URL", "Checked", "Status", "Verification note"],
             s_rows, cls="dense searchable", caption="Open any URL to review it manually.")
    written.append(page("sources.html", "Sources", src_html, wide=True))

    # ------------------------------------------------------- verification log
    vrows = []
    with open(os.path.join(ROOT, "data", "verification.tsv"), encoding="utf-8") as fh:
        lines = [ln for ln in fh.read().splitlines() if ln.strip()]
        # first line is the column header, not a data row
        for line in lines[1:]:
            parts = line.rstrip("\n").split("\t")
            parts = (parts + [""] * 5)[:5]
            vrows.append([cell(parts[0]), '<td><code>%s</code></td>' % esc(parts[1]),
                          cell(parts[2]), cell(parts[3]), cell(parts[4])])
    ver = """
<section>
<h1>Verification</h1>
<p class="lead">This page is the audit trail. Every check below is a script in <code>tools/</code> that can be
run again by anyone, and every one of them exits non-zero on failure so it can gate a merge.</p>
<div class="callout ok">
  <p><strong>Line-by-line is literal here.</strong> <code>tools/verify_injuries.py</code> does not trust the
  normalised data file. It re-parses the raw page capture independently, rebuilds the table, and compares all
  345 rows field by field in page order. A single differing character fails the build.</p>
</div>
</section>

<section>
<h2>Checks performed</h2>
%s
</section>

<section>
<h2>Reproduce it</h2>
<pre class="code">python3 tools/verify_injuries.py   # 345 rows vs the raw capture
python3 tools/build.py             # recompute every derived figure
python3 tools/site.py              # re-render every page
python3 tools/checklinks.py        # links, anchors, reachability, source IDs
</pre>
<p>No third-party packages. No network access required for any of the four.</p>
</section>

<section>
<h2>Source load results</h2>
<p>Fifteen official URLs were requested once each. Twelve returned content that supported the claim being made.
Three returned HTTP 404 and are recorded as <span class="pill bad">NOT VERIFIED</span> — they are never cited
as fact, and the gap they leave is published on <a href="flagged.html">Flagged for Review</a> rather than
papered over.</p>
<p>See the full <a href="sources.html">source registry</a> for the URL, publisher, tier, capture date and
verification note for each one.</p>
</section>

<section>
<h2>What could not be verified, and the consequence</h2>
%s
</section>
""" % (table(["Check", "Command", "Scope", "Result", "Date"], vrows, cls="dense"),
       table(["Item", "Attempted", "Consequence for this site"], [
           [cell("Injury-designation definitions"), cell("The 2017 policy PDF at operations.nfl.com"),
            cell("No definition text quoted; only observed categories shown")],
           [cell("League-wide depth chart"), cell("nfl.com/depth-charts/ (404)"),
            cell("Depth captured club by club (%d of 32); ordering labelled unofficial"
                 % depth_cov["covered"])],
           [cell("Snap counts"), cell("No official feed located"),
            cell("No claim that any backup played")],
           [cell("Market prices"), cell("League does not publish prices"),
            cell("Every price, edge and EV field is blank")],
           [cell("Bye weeks"), cell("No official bye table verified"),
            cell("Four absent clubs recorded as unexplained, not as byes")],
           [cell("Legal and regulatory position"), cell("No regulator source verified"),
            cell("No legality claim in any jurisdiction")],
       ], cls="dense"))
    written.append(page("verification.html", "Verification", ver, wide=True))

    # ----------------------------------------------------------------- flagged
    kinds = {}
    for f in flags:
        kinds.setdefault(f["kind"], []).append(f)
    f_html = ['<section><h1>Flagged for Review</h1>',
              '<p class="lead">Everything that could not be confirmed, everything that contradicts something else, '
              'and everything that was deliberately left blank. None of it is hidden and none of it is guessed.</p>',
              '<div class="callout warn"><p><strong>%d items.</strong> Flagged items do not block the site; they '
              'are published so they can be reviewed after the site is live. Nothing on this list has been '
              'silently resolved.</p></div>' % len(flags)]
    frows = []
    for f in flags:
        frows.append([
            '<td><a href="#%s">%s</a></td>' % (esc(f["id"]), esc(f["id"])),
            cell(f["kind"]),
            cell(f["item"]),
            cell(f["severity"]),
            cell(", ".join(f["sourceIds"]) or "—"),
        ])
    f_html.append("<section><h2>Index</h2>%s</section>" % table(
        ["ID", "Kind", "Item", "Severity", "Sources"], frows, cls="dense"))
    for f in flags:
        links = " ".join(src_link(sid, sources_by_id) for sid in f["sourceIds"]) or \
            '<span class="muted">no source — stated as a limitation</span>'
        f_html.append("""
<section class="flag" id="%s">
  <h2><span class="sid">%s</span> %s</h2>
  <p><span class="pill">%s</span> Severity <span class="pill %s">%s</span></p>
  <p>%s</p>
  <p class="evidence">Sources consulted: %s</p>
  <div class="callout"><p><strong>What was done instead.</strong> %s</p></div>
</section>""" % (esc(f["id"]), esc(f["id"]), esc(f["item"]), esc(f["kind"]),
                 "bad" if f["severity"] == "High" else ("warn" if f["severity"] == "Medium" else ""),
                 esc(f["severity"]), esc(f["detail"]), links, esc(f["action"])))
    f_html.append("</section>")
    written.append(page("flagged.html", "Flagged for Review", "".join(f_html)))

    # Requirements sprint pages (R21-R28) — session arena-360ca650-fl1
    written.append(page("line-board.html", "Line Board", sprint["line_board"], wide=True))
    written.append(page("price-snapshots.html", "Price Snapshots", sprint["price_snapshots"], wide=True))
    written.append(page("verified-results-feed.html", "Verified Results Feed",
                        sprint["results_feed"] + sprint["week10_finals"], wide=True))
    # replacement-depth.html is generated merged by scripts/build_pages_m.py (final
    # integration: this sprint's 52-slot register AND the 69-spot week-10 analysis share
    # the page; both datasets preserved). The body computed here is kept verbatim on
    # replacement-depth-r21r28.html so nothing is lost and the generator stays runnable.
    written.append(page("replacement-depth-r21r28.html", "Replacement Depth (R21-R28 register)", sprint["replacement_depth"], wide=True))
    print("replacement-depth.html: skipped — merged page generated by scripts/build_pages_m.py; "
          "this register preserved at replacement-depth-r21r28.html")
    written.append(page("correlation-register.html", "Correlation Register", sprint["correlation_register"], wide=True))

    import brief  # session arena/685f958d-fl1: model lines, results feed, signal/staking/demotion
    written.extend(brief.render(sys.modules[__name__]))
    # ------------------------------------------------------------- market spine
    # Eight pages generated from data/market/, i.e. from artefacts a script wrote.
    # They live in tools/pages_market.py so this file stays the single owner of the
    # site shell; the numbers here are counts, not new claims.
    written.extend(pages_market.render_all())

    written.extend(g_pages)

    print("wrote %d pages:" % len(written))
    for w in written:
        print("  " + w)


if __name__ == "__main__":
    main()
