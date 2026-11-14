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
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build  # noqa: E402  (shares the loaders and derived analysis)

E = html.escape

SITE = "FL1 — NFL Line Lab"
TAGLINE = "Verified data, open questions, and a strategy leaderboard that refuses to guess."

NAV = [
    ("index.html", "Dashboard"),
    ("executive-summary.html", "Executive Summary"),
    ("requirements.html", "Requirements"),
    ("injuries.html", "Injuries"),
    ("depth.html", "Backup Depth"),
    ("standings.html", "Standings"),
    ("schedule.html", "Schedule 2026"),
    ("prop-correlations.html", "Prop Correlations"),

    ("line-origination.html", "Line Origination"),
    ("strategies.html", "Leaderboard"),
    ("validation.html", "Validation Gates"),
    ("questions.html", "Open Questions"),
    ("suggestions.html", "Suggestions"),
    ("sources.html", "Sources"),
    ("verification.html", "Verification"),
    ("flagged.html", "Flagged for Review"),
]


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


def table(headers, rows, cls="", caption=""):
    out = ['<div class="twrap">']
    if caption:
        out.append('<p class="caption">%s</p>' % caption)
    out.append('<table class="%s">' % cls)
    out.append("<thead><tr>")
    for h in headers:
        out.append("<th>%s</th>" % h)
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join(r) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def page(filename, title, body, extra_head="", wide=False):
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (href, ' class="on"' if href == filename else "", label)
        for href, label in NAV
    )
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
  <nav class="nav" aria-label="Sections">%s</nav>
</header>
<main id="main"%s>
%s
</main>
<footer class="foot">
  <p><strong>%s</strong> — %s</p>
  <p>Data captured 2026-11-14 (UTC) from official league and club sources. Every value links to its source.
  Values that could not be confirmed from an official source are left blank and listed on
  <a href="flagged.html">Flagged for Review</a>. Nothing on this site is a bet, an offer to wager, or advice.
  No price, edge or expected-value figure is displayed unless an official source supports it.</p>
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


def main():
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

    written = []

    # ------------------------------------------------------------------ index
    n_sugg = len(suggestions)
    n_q = len(questions)
    n_block = sum(1 for q in questions if str(q.get("blocking", "")).lower().startswith("yes"))
    n_verified = sum(1 for s in sources if s["status"] == "VERIFIED")
    n_404 = sum(1 for s in sources if s["status"] != "VERIFIED")
    n_req_done = sum(1 for r in requirements if r["status"] == "done")

    cards = """
<section class="hero">
  <h1>What this site is</h1>
  <p class="lead">A verified, auditable base for originating NFL lines. It separates three things that are
  usually blurred together: <strong>what an official source actually says</strong>,
  <strong>what we do not know yet</strong>, and <strong>what we propose to do about it</strong>.
  Nothing here has been estimated to fill a gap. Where a number could not be confirmed, the cell is blank.</p>
  <p class="lead">No strategy on this site has a performance figure, because no strategy has been run.
  A blank leaderboard is the honest starting state.</p>
</section>

<section class="grid">
  <a class="card" href="executive-summary.html"><h3>Executive Summary</h3>
    <p>One page: what is verified, what is blocked, and the five decisions that unblock the rest.</p></a>
  <a class="card" href="injuries.html"><h3>Injury Report</h3>
    <p><strong>%(inj_rows)d</strong> player rows across <strong>%(inj_clubs)d of %(inj_clubs_total)d</strong> clubs, straight from the official
    Week 10 report. Practice status and game status preserved exactly.</p></a>
  <a class="card" href="depth.html"><h3>Backup Depth</h3>
    <p><strong>%(depth_covered)d of %(depth_total)d</strong> club charts captured — <strong>%(depth_rows)d</strong> charted slots.
    <strong>%(depth_starters_status)d</strong> first-string players carry an official Out / Doubtful / Questionable status,
    each with the next player the club itself lists at that slot. No inferred ranking.</p></a>
  <a class="card" href="questions.html"><h3>Open Questions</h3>
    <p><strong>%(n_questions)d</strong> questions, <strong>%(n_blocking)d</strong> of them blocking, each stating what we know,
    what we do not, and what data is missing.</p></a>
  <a class="card" href="suggestions.html"><h3>Suggestions</h3>
    <p><strong>%(n_suggestions)d</strong> proposals with options, trade-offs and one recommended path. Review before
    anything is implemented.</p></a>
  <a class="card" href="strategies.html"><h3>Leaderboard</h3>
    <p>Strategies, the gates each must clear, and a ranking that stays empty until a gate is actually passed.</p></a>
  <a class="card" href="schedule.html"><h3>Schedule &amp; Results 2026</h3>
    <p>All 272 regular-season games, %(n_results)d results in so far, reconciled 32/32 against the official standings; market lines flagged third-party.</p></a>
  <a class="card" href="prop-correlations.html"><h3>Prop Correlations</h3>
    <p>Empirical player-level correlations from 1999&ndash;2024 (closes Q-PROP-01); parlay lift math, QA gates, reproducible.</p></a>
  <a class="card" href="docs/computed/index.html"><h3>Computed Research Layer</h3>
    <p>Elo line engine, 16 strategies &times; 7 gates, availability model &mdash; built by the strategy-lab session at <code>docs/computed/</code>.</p></a></section>
""" % {
       "inj_rows": lg["rows"],
       "inj_clubs": lg["clubs"],
       "inj_clubs_total": lg["clubsTotal"],
       "depth_covered": depth_cov["covered"],
       "depth_total": depth_cov["total"],
       "depth_rows": depth_tot["rows"],
       "depth_starters_status": depth_tot["startersWithStatus"],
       "n_questions": n_q,
       "n_blocking": n_block,
       "n_suggestions": n_sugg,
       "n_results": len(results),
   }

    kpis = table(
        ["Metric", "Value", "Basis", "Source"],
        [
            [cell("Injury rows captured"), cell(lg["rows"], "n"),
             cell("Official Week 10 2026 report, one snapshot"), raw_src(src_link("S01", sources_by_id))],
            [cell("Clubs present in that report"), cell("%d of %d" % (lg["clubs"], lg["clubsTotal"]), "n"),
             cell("Four clubs absent — see Flagged F06"), raw_src(src_link("S01", sources_by_id))],
            [cell("Players designated Out"), cell(lg["out"], "n"),
             cell("Game status column reads Out"), raw_src(src_link("S01", sources_by_id))],
            [cell("Players designated Doubtful"), cell(lg["doubtful"], "n"),
             cell("Game status column reads Doubtful"), raw_src(src_link("S01", sources_by_id))],
            [cell("Players designated Questionable"), cell(lg["questionable"], "n"),
             cell("Game status column reads Questionable"), raw_src(src_link("S01", sources_by_id))],
            [cell("Did-not-participate practice rows"), cell(lg["dnp"], "n"),
             cell("Practice status column reads Did Not Participate"), raw_src(src_link("S01", sources_by_id))],
            [cell("Rows marked not injury related"), cell(lg["nonInjury"], "n"),
             cell("Injury text begins 'Not injury related'"), raw_src(src_link("S01", sources_by_id))],
            [cell("Sources verified"), cell("%d of %d" % (n_verified, len(sources)), "n"),
             cell("Page loaded successfully in this session"), raw_src('<a href="sources.html">registry</a>')],
            [cell("Sources that failed to load"), cell(n_404, "n"),
             cell("Recorded as NOT VERIFIED, never cited as fact"), raw_src('<a href="flagged.html">flagged</a>')],
            [cell("Strategies with a result"), cell("0 of %d" % len(strategies), "n"),
             cell("No backtest executed; no numeric result claimed"), raw_src('<a href="strategies.html">board</a>')],
        ],
        cls="kpi",
        caption="Headline figures. Each is computed by <code>tools/build.py</code> from the data files, not typed in by hand.",
    )

    written.append(page("index.html", "Dashboard", cards + kpis))

    # ------------------------------------------------------- executive summary
    total_out_def = sum(t["defOut"] for t in by_team)
    total_out_off = sum(t["offOut"] for t in by_team)
    es = """
<section>
<h1>Executive Summary</h1>
<p class="lead">Status as of 2026-11-14. This page states only what can be traced to an official source,
and marks everything else as open.</p>
</section>

<section>
<h2>1. What has been verified</h2>
<p>The repository was empty apart from a five-byte README, so the entire base is new. Fifteen sources were
attempted; <strong>%d loaded successfully</strong> and <strong>%d did not</strong>. The failed ones are
recorded as unverified and are never used to support a claim.</p>
<p>The most substantial verified artefact is the <strong>official Week 10, 2026 season injury report</strong>:
%d player rows over %d clubs, with each player's practice status and game status reproduced exactly as published.
Of those rows, %d carry a game status (Out, Doubtful or Questionable) and %d are recorded as did-not-participate
in practice. Two rows are explicitly <em>not injury related</em>, which matters: counting them as injuries would
inflate any injury rate.</p>
<p>Alongside the injury data the site holds the official 2026 division and league standings for all 32 clubs,
the Week 10 schedule with kickoff times and broadcasters, the league's tiebreaking procedures, and the official
league calendar through Super Bowl LXI on 2027-02-14.</p>
</section>

<section>
<h2>2. What is blocked, and why</h2>
<p>Three blockers stop the analytical work, and none of them can be solved by effort inside this repository.</p>
<ol class="tight">
<li><strong>No benchmark price.</strong> The league publishes results, statistics and schedules, not betting
prices. Without a price there is no edge, no expected value and no closing-line value. Every such field on this
site is blank. This is blocker #1 and it gates the entire leaderboard.</li>
<li><strong>No official snap counts and no league-wide official depth chart.</strong>
<code>nfl.com/depth-charts/</code> returns 404. Depth therefore has to be captured club by club, and each club
titles its own chart <em>Unofficial Depth Chart</em>. %d of the 32 clubs publish one as a readable table; Houston
publishes its as an image (<a href="flagged.html#F16">F16</a>). So &ldquo;which backup replaced which
starter&rdquo; cannot be measured, only alleged. The site shows official absence and the club&rsquo;s own
published ordering instead, and labels the depth layer as derived.</li>
<li><strong>One snapshot, one season.</strong> Everything here is a single capture on a single day. No backtest,
no persistence claim and no multi-season holdout is possible from this data.</li>
</ol>
</section>

<section>
<h2>3. What the injury data already shows</h2>
<p>Among the clubs captured, %d players are designated Out, split <strong>%d on offense, %d on defense and %d on
special teams</strong>. Defensive line and secondary depth is the most exposed area, which is the part of the
brief about 2nd and 3rd string defenders being forced in.</p>
<p>The pattern is concrete and checkable across the league: of the %d first-string slots charted, <strong>%d
carry an official Out / Doubtful / Questionable status</strong> this week, and for each one the club&rsquo;s own
chart names the next player at that same slot. Kansas City is worked end to end on
<a href="depth.html">Backup Depth</a> — starting right tackle Out (ankle), starting running back Questionable
after not practising (groin), second-string defensive tackle Out (neck). Those are observed facts with a source
link. The claim that a specific backup took the snaps is <em>not</em> made, because no snap-count source was
verified.</p>
</section>

<section>
<h2>4. The five decisions that unblock the rest</h2>
<ol class="tight">
<li><strong>Name one market to price first</strong> (Q01). Trying to price everything at once guarantees nothing
reaches significance in an 18-week season.</li>
<li><strong>Supply or accept a benchmark price source</strong> (Q03), or accept that the site publishes fair
value only and grades on calibration instead of profit.</li>
<li><strong>Accept that depth is derived, not official</strong> (Q04), and let the depth layer ship labelled as
such.</li>
<li><strong>Pre-register the validation gates</strong> (Q09, Q12, Q19) before any strategy is scored, so the
target cannot be moved after the result is known.</li>
<li><strong>Keep rewards non-monetary</strong> (Q13, Q14) and leave the legal question open rather than
answering it.</li>
</ol>
</section>

<section>
<h2>5. Recommendations, in order</h2>
<p>Full reasoning and alternatives are on the <a href="suggestions.html">Suggestions</a> page. In short:</p>
<ul class="tight">
<li>Publish <em>fair value with an uncertainty band</em>, never an invented market price (SG01).</li>
<li>Rank strategies on <em>calibration first</em>, profit second (SG02).</li>
<li>Seal every prediction with a hash before kickoff (SG03) — it is almost free and it is what makes a record credible.</li>
<li>Split the injury product into <em>observed absence</em> and <em>derived depth</em>, visibly (SG04, SG12).</li>
<li>Require every strategy to beat a published naive baseline, or it does not get ranked (SG08).</li>
<li>Sequence the work: team-level single market, then props, then combos, then correlations (SG07).</li>
</ul>
</section>

<section>
<h2>6. What this site deliberately does not do</h2>
<p>It does not quote an injury-policy definition, because the official PDF returns 404. It does not claim any
club has a bye, because no official bye table was verified. It does not resolve two places where official NFL.com
pages contradict each other. It does not print a single performance number. Each of those is listed with links on
<a href="flagged.html">Flagged for Review</a>.</p>
</section>
""" % (n_verified, n_404, lg["rows"], lg["clubs"], lg["withGameStatus"], lg["dnp"],
       depth_cov["covered"],
       lg["out"], total_out_off, total_out_def, sum(t["stOut"] for t in by_team),
       depth_tot["starters"], depth_tot["startersWithStatus"])
    written.append(page("executive-summary.html", "Executive Summary", es))

    # ------------------------------------------------------------ requirements
    by_section = {}
    for r in requirements:
        by_section.setdefault(r["section"], []).append(r)
    req_html = ['<section><h1>Requirements</h1>',
                '<p class="lead">Every line of the brief, decomposed, with the evidence that satisfies it and '
                'the page where it can be checked. A requirement is only marked done when there is a link.</p>',
                '<p class="note">%d of %d requirements are complete. The rest are marked '
                '<span class="pill warn">partial</span> on purpose — a partial status means the method is '
                'specified and the number is withheld because no source supports it.</p></section>'
                % (n_req_done, len(requirements))]
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
    written.append(page("injuries.html", "Injury Report", inj_html, wide=True))

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
    written.append(page("line-origination.html", "Line Origination", lo))

    # -------------------------------------------------------------- strategies
    srows = []
    for s in strategies:
        srows.append([
            cell(s["id"]),
            cell(s["name"]),
            cell(s["role"]),
            cell(s["market"]),
            '<td>%s</td>' % pill(s["data_status"], STATUS_KIND.get(s["data_status"], "")),
            cell(s["data_note"]),
            cell(", ".join(s["gates"])),
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
  <p><strong>0 of %d entries carry a result.</strong> No backtest has been executed and no performance figure is
  claimed anywhere in this repository. The leaderboard will stay empty until a strategy clears the gates with a
  price source supplied. That is the design, not a delay.</p>
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
              "Gates", "Result", "Result note", "Source"],
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
    written.append(page("strategies.html", "Leaderboard", strat, wide=True))

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
    written.append(page("validation.html", "Validation Gates", val, wide=True))

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
                cell(q["id"]),
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

    print("wrote %d pages:" % len(written))
    for w in written:
        print("  " + w)


if __name__ == "__main__":
    main()
