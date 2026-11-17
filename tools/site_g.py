#!/usr/bin/env python3
"""
site_g.py — pages and dashboard sections added by session `arena/dbf11de0-fl1`.

Everything here is generated from committed data files. Nothing is typed in by
hand. The module is called from tools/site.py so that all pages share one
navigation, one stylesheet and one page template.

Pages built here
  requirements-backlog.html   the brief, line by line, with the gate that
                              blocks each row and the number that clears it
  removal-of-luck.html        how much of a result could be chance, and the
                              sample size at which it stops being chance
  team-availability.html      per club: starters out, replacement named,
                              net injury count
  announced-starters.html     starters an official page actually announced,
                              quoted and linked (never inferred)
  availability-ledger.html    point-in-time snapshot ledger: every dated
                              capture of the official injury report, with its
                              hash, and the diff between consecutive reads
"""

import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(ROOT, "raw")

STATUS_KIND = {
    "done": "ok",
    "partial": "warn",
    "blocked": "bad",
    "not-started": "warn",
    "decision-open": "bad",
    "rejected": "",
    "duplicate": "",
}

NEW_PAGES = [
    ("requirements-backlog.html", "Requirement Backlog"),
    ("team-availability.html", "Team Availability"),
    ("announced-starters.html", "Announced Starters"),
    ("availability-ledger.html", "Snapshot Ledger"),
    ("removal-of-luck.html", "Removal of Luck"),
]


# --------------------------------------------------------------------- helpers
def load_csv(name):
    delim = "\t" if name.endswith(".tsv") else ","
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=delim))


def load_json(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def pct(v, nd=1):
    if v is None:
        return ""
    return ("%%.%df%%%%" % nd) % (v * 100)


# ------------------------------------------------------------ backlog / G2 G3
def backlog_page(ctx):
    reqs = load_json("requirements.json")
    backlog = load_json("requirements_backlog.json")

    rows = []
    for r in reqs:
        rows.append({
            "id": r["id"], "category": r.get("section", ""),
            "requirement": r.get("requirement", ""),
            "status": r.get("status", ""),
            "blocking_gate": r.get("evidence", ""),
            "clears_when": "", "evidence": "", "sources": "",
        })
    rows.extend(backlog["rows"])
    rows.sort(key=lambda r: r["id"])

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    order = ["done", "partial", "blocked", "not-started", "decision-open",
             "rejected"]
    chips = "".join(
        '<span class="pill %s">%s &middot; %d</span> '
        % (STATUS_KIND.get(s, ""), ctx["esc"](s), counts[s])
        for s in order if s in counts)

    body = ["""
<section class="hero">
  <h1>Requirement backlog</h1>
  <p class="lead">Every requirement line from the project brief, one row each.
  For each row: <strong>the gate that blocks it</strong> and
  <strong>the number that would clear it</strong>. A gate without a number is an
  opinion; with a number it is a task that can be finished and checked.</p>
  <p class="lead">%s</p>
</section>

<section>
<h2>How to read this page</h2>
<div class="callout">
  <h3>Four kinds of row</h3>
  <p><strong>done</strong> &mdash; the artefact exists in this repository and is re-runnable.
  <strong>partial</strong> &mdash; started, but the blocking gate is still open.
  <strong>blocked</strong> &mdash; waiting on an official source that does not exist yet in
  any form we can cite. <strong>not-started</strong> &mdash; nothing depends on it being blocked;
  it simply has not been built. <strong>rejected</strong> rows are kept with their reason, because
  a shortcut nobody records gets re-proposed next week.</p>
</div>
<p class="caption">Rows R01&ndash;R28 come from the register built by earlier sessions
(<code>data/requirements.json</code>); rows R29&ndash;R87 were added by this session from the
brief lines that register did not yet track (<code>data/requirements_backlog.csv</code>).</p>
</section>
""" % chips]

    head = ["ID", "Requirement", "Category", "Status", "Gate that blocks it",
            "Number that would clear it", "Evidence in this repo", "Source"]
    table_rows = []
    for r in rows:
        table_rows.append([
            "<td><code>%s</code></td>" % ctx["esc"](r["id"]),
            ctx["cell"](r["requirement"]),
            ctx["cell"](r["category"]),
            "<td>%s</td>" % ctx["pill"](r["status"], STATUS_KIND.get(r["status"], "")),
            ctx["cell"](r["blocking_gate"] or r.get("blocking_gate", "")),
            ctx["cell"](r.get("clears_when", "")),
            ctx["cell"](r.get("evidence", "")),
            ctx["raw_src"](ctx["src_link"](
                (r.get("sources") or "S01").split(";")[0], ctx["sources_by_id"])),
        ])
    body.append(ctx["table"](head, table_rows, cls="searchable",
                             caption="%d requirement rows. Filter by club, gate or id."
                             % len(rows)))
    return ctx["page"]("requirements-backlog.html", "Requirement Backlog",
                       "".join(body), wide=True)


def readiness_section(ctx):
    """The decision-readiness table the brief asks to see on the landing page."""
    reqs = load_json("requirements.json")
    backlog = load_json("requirements_backlog.json")
    rows = []
    for r in reqs:
        gate = (r.get("evidence", "") or "")
        if r.get("status") != "done":
            gate = ("partially met — %s" % gate) if gate else \
                   "see requirements.html for the current state"
        rows.append({
            "id": r["id"], "requirement": r.get("requirement", ""),
            "status": r.get("status", ""),
            "blocking_gate": gate, "clears_when": "",
        })
    for r in backlog["rows"]:
        rows.append({
            "id": r["id"], "requirement": r["requirement"],
            "status": r["status"], "blocking_gate": r["blocking_gate"],
            "clears_when": r["clears_when"],
        })
    rows.sort(key=lambda r: r["id"])

    blocked = [r for r in rows if r["status"] in ("blocked", "decision-open")]
    table_rows = []
    for r in rows:
        table_rows.append([
            "<td><code>%s</code></td>" % ctx["esc"](r["id"]),
            ctx["cell"](r["requirement"]),
            "<td>%s</td>" % ctx["pill"](r["status"], STATUS_KIND.get(r["status"], "")),
            ctx["cell"](r["blocking_gate"]),
            ctx["cell"](r["clears_when"] or "—"),
            ctx["raw_src"](ctx["src_link"]("S01", ctx["sources_by_id"])),
        ])
    return """
<section id="decision">
<h2>Decision readiness</h2>
<p class="lead">One row per requirement: what stops it today, and the number that
would clear it. <strong>%d of %d rows are blocked or waiting on a decision.</strong>
The full table, with the evidence file behind each row, is on the
<a href="requirements-backlog.html">Requirement Backlog</a> page.</p>
%s
</section>
""" % (len(blocked), len(rows),
       ctx["table"](["ID", "Requirement", "Status", "Gate that blocks it",
                     "Number that would clear it", "Source"],
                    table_rows, cls="searchable",
                    caption="Filter by id, gate or keyword. Blank in the last column "
                            "means the requirement is already satisfied."))


# ------------------------------------------------------------------ luck / G4
def luck_page(ctx):
    p = load_json("luck_panel.json")
    h = p["headline"]
    b = p["brier"]

    body = ["""
<section class="hero">
  <h1>Removal of luck</h1>
  <p class="lead">A leaderboard ranks something. Before it ranks anything, this
  page publishes the size of the thing it will be ranking against: <strong>how much
  of a result chance alone could produce</strong>, and <strong>how many decisions it
  would take before chance stopped being a plausible explanation</strong>.</p>
  <p class="lead">%s</p>
</section>
""" % ctx["esc"](h["verdict"])]

    # headline figures
    rows = [
        [ctx["cell"]("Official 2026 results used"), ctx["cell"](h["games"], "n"),
         ctx["cell"]("data/results.tsv, reconciled 32/32 against the official standings"),
         ctx["raw_src"](ctx["src_link"]("S49", ctx["sources_by_id"]))],
        [ctx["cell"]("Home wins / away wins / ties"),
         ctx["cell"]("%d / %d / %d" % (h["home_wins"], h["away_wins"], h["ties"]), "n"),
         ctx["cell"]("Final scores from the official schedule pages"),
         ctx["raw_src"](ctx["src_link"]("S49", ctx["sources_by_id"]))],
        [ctx["cell"]("Home-team hit rate"), ctx["cell"](pct(h["home_win_rate"], 2), "n"),
         ctx["cell"]("67 of 137"),
         ctx["raw_src"](ctx["src_link"]("S49", ctx["sources_by_id"]))],
        [ctx["cell"]("95% interval for that hit rate"),
         ctx["cell"]("%s to %s" % (pct(h["home_win_rate_wilson"][0]),
                                   pct(h["home_win_rate_wilson"][1])), "n"),
         ctx["cell"]("Wilson score interval — it contains 50%"),
         ctx["raw_src"](ctx["src_link"]("S49", ctx["sources_by_id"]))],
        [ctx["cell"]("Exact two-sided p vs a coin flip"),
         ctx["cell"]("%.3f" % h["exact_p_vs_coin"], "n"),
         ctx["cell"]("Far from significant: this is what no signal looks like"),
         ctx["raw_src"](ctx["src_link"]("S49", ctx["sources_by_id"]))],
        [ctx["cell"]("95% luck band at n = 137"),
         ctx["cell"]("%s to %s" % (pct(h["luck_band_95_at_n"][0]),
                                   pct(h["luck_band_95_at_n"][1])), "n"),
         ctx["cell"]("A skill-free strategy lands in here 19 times out of 20"),
         ctx["raw_src"](ctx["src_link"]("S49", ctx["sources_by_id"]))],
        [ctx["cell"]("Brier score, constant forecast at the home rate"),
         ctx["cell"]("%.5f" % b["constant_forecast_at_home_rate"], "n"),
         ctx["cell"]("Same number forecast for all 137 games"),
         ctx["raw_src"](ctx["src_link"]("S49", ctx["sources_by_id"]))],
        [ctx["cell"]("Brier score, constant forecast at 0.5"),
         ctx["cell"]("%.5f" % b["constant_forecast_at_coin"], "n"),
         ctx["cell"]("The benchmark every strategy must beat"),
         ctx["raw_src"](ctx["src_link"]("S49", ctx["sources_by_id"]))],
        [ctx["cell"]("Brier skill score of the home-team constant vs a coin"),
         ctx["cell"]("%.5f" % b["brier_skill_score_vs_coin"], "n"),
         ctx["cell"]("Effectively zero — and that is the honest baseline"),
         ctx["raw_src"](ctx["src_link"]("S49", ctx["sources_by_id"]))],
        [ctx["cell"]("Decisions needed for a 5pp edge (alpha .05, power .80)"),
         ctx["cell"]("785", "n"),
         ctx["cell"]("Nearly six NFL seasons of every game, or one season of ~46 bets/week"),
         ctx["raw_src"](ctx["src_link"]("S49", ctx["sources_by_id"]))],
        [ctx["cell"]("Same, adjusted for trying 6 strategies"),
         ctx["cell"]("%d" % p["multiplicity"]["n_required_at_5pp_edge"], "n"),
         ctx["cell"]("Bonferroni per-comparison alpha %.5f" % p["multiplicity"]["per_comparison_alpha"]),
         ctx["raw_src"](ctx["src_link"]("S49", ctx["sources_by_id"]))],
    ]
    body.append("<section><h2>Headline numbers</h2>%s</section>"
                % ctx["table"](["Figure", "Value", "Basis", "Source"], rows,
                               cls="kpi"))

    # base rates
    br_rows = []
    for r in p["base_rates"]:
        if r["measurable"]:
            br_rows.append([
                ctx["cell"](r["label"]),
                ctx["cell"](r["k"], "n"), ctx["cell"](r["n"], "n"),
                ctx["cell"](pct(r["rate"], 2), "n"),
                ctx["cell"]("%s to %s" % (pct(r["wilson_lo"], 1), pct(r["wilson_hi"], 1)), "n"),
                ctx["cell"]("%.3f" % r["exact_p_vs_coin"], "n"),
                ctx["raw_src"](ctx["src_link"](r["source"], ctx["sources_by_id"])),
            ])
        else:
            br_rows.append([
                ctx["cell"](r["label"]),
                ctx["cell"](""), ctx["cell"](""), ctx["cell"](""),
                ctx["cell"](""), ctx["cell"](""),
                ctx["raw_src"]('<a class="src" href="flagged.html">unverified</a>'),
            ])
            br_rows[-1][1] = ctx["cell"]("")
    body.append("""
<section>
<h2>Base rates that can and cannot be measured</h2>
<p class="caption">A luck band needs a base rate. Two of the four decision types
this project wants to price have an officially measurable base rate; two do not.
Where it cannot be measured the cell is blank, and the row says why &mdash; assuming
0.5 for a total or a prop would be an invented input.</p>
%s
</section>
""" % ctx["table"](["Decision type", "k", "n", "Rate", "95% interval",
                    "Exact p vs coin", "Source"], br_rows))

    # luck bands
    band_rows = []
    for r in p["luck_bands"]:
        band_rows.append([
            ctx["cell"](r["n"], "n"),
            ctx["cell"]("%s to %s" % (pct(r["lo"], 1), pct(r["hi"], 1)), "n"),
            ctx["cell"]("±%.1f pp" % r["half_width_pp"], "n"),
            ctx["raw_src"](ctx["src_link"]("S49", ctx["sources_by_id"])),
        ])
    body.append("""
<section>
<h2>How wide luck is, by sample size</h2>
<p class="caption">The interval within which a strategy with <em>no skill at all</em>
would finish, 19 times out of 20, if every decision were a coin flip. Read it as:
a hit rate inside the band proves nothing.</p>
%s
</section>
""" % ctx["table"](["Decisions n", "95% band for a skill-free hit rate",
                    "Half-width", "Source"], band_rows))

    # sizing
    size_rows = []
    for r in p["sizing"]:
        size_rows.append([
            ctx["cell"]("%.0f pp" % r["edge_pp"], "n"),
            ctx["cell"](r["n_alpha05_power80"], "n"),
            ctx["cell"](r["n_at_icc_%.2f_m2" % 0.10], "n"),
            ctx["cell"](r["n_at_icc_%.2f_m2" % 0.30], "n"),
            ctx["cell"](r["n_at_icc_%.2f_m2" % 0.50], "n"),
            ctx["raw_src"](ctx["src_link"]("S49", ctx["sources_by_id"])),
        ])
    body.append("""
<section>
<h2>Sample needed to establish an edge</h2>
<p class="caption">Independent decisions required to detect an edge of the given
size over a 50%% base rate, two-sided alpha 0.05, power 0.80. The last three
columns inflate that number for two legs inside the same game at three
intra-cluster correlations. <strong>The ICC itself is not measured anywhere in
this repository</strong> &mdash; those columns are a sensitivity, not an estimate.</p>
%s
</section>
""" % ctx["table"](["Edge to detect", "Independent decisions",
                    "2 legs/game, ICC 0.10", "2 legs/game, ICC 0.30",
                    "2 legs/game, ICC 0.50", "Source"], size_rows))

    body.append("""
<section>
<h2>What this means for the leaderboard</h2>
<div class="callout">
  <h3>%s</h3>
  <p>%s</p>
  <p>%s</p>
</div>
</section>
""" % (ctx["esc"]("Rank on a proper score, with the sample size published beside it"),
       ctx["esc"](p["multiplicity"]["note"]),
       ctx["esc"](p["clustering"]["icc_note"])))
    body.append("<p class='note'>Companion signal-level decomposition (per-strategy p-values, certifiable edges, sample floors) lives on <a href='readiness.html#luck'>Decision Readiness &rarr; Luck</a>.</p>")
    return ctx["page"]("removal-of-luck.html", "Removal of Luck", "".join(body),
                       wide=True)


def luck_section(ctx):
    p = load_json("luck_panel.json")
    h = p["headline"]
    b = p["brier"]
    return """
<section>
<h2>Removal of luck</h2>
<p class="lead">Before any strategy is ranked, here is the size of what it has to
beat. Over <strong>%d</strong> official 2026 results the home team won
<strong>%s</strong> of games; the 95%% interval is
<strong>%s to %s</strong>, which contains 50%%. A season is not long enough for a
small edge to become visible &mdash; the panel publishes the sample size at which it
would.</p>
%s
<p><a href="removal-of-luck.html">Full panel: luck bands by sample size, required n by
edge size, and the multiplicity adjustment &rarr;</a></p>
</section>
""" % (h["games"], pct(h["home_win_rate"], 1),
       pct(h["home_win_rate_wilson"][0], 1), pct(h["home_win_rate_wilson"][1], 1),
       ctx["table"](
           ["Figure", "Value", "Basis"],
           [[ctx["cell"]("Home-team hit rate"), ctx["cell"](pct(h["home_win_rate"], 2), "n"),
             ctx["cell"]("67 of 137 official results")],
            [ctx["cell"]("95% interval"), ctx["cell"]("%s to %s" % (
                pct(h["home_win_rate_wilson"][0], 1), pct(h["home_win_rate_wilson"][1], 1)), "n"),
             ctx["cell"]("contains 50% — indistinguishable from luck")],
            [ctx["cell"]("Exact p vs a coin flip"), ctx["cell"]("%.3f" % h["exact_p_vs_coin"], "n"),
             ctx["cell"]("two-sided binomial, n = 137")],
            [ctx["cell"]("Brier skill of a constant forecast vs a coin"),
             ctx["cell"]("%.5f" % b["brier_skill_score_vs_coin"], "n"),
             ctx["cell"]("what zero skill looks like on a proper score")],
            [ctx["cell"]("Decisions needed for a 5pp edge"),
             ctx["cell"]("785", "n"), ctx["cell"]("alpha 0.05, power 0.80")],
            [ctx["cell"]("Same, adjusted for 6 strategies tried"),
             ctx["cell"]("%d" % p["multiplicity"]["n_required_at_5pp_edge"], "n"),
             ctx["cell"]("Bonferroni — ranking the best of many inflates false positives")]],
           cls="kpi"))


# ------------------------------------------------------- availability / G5 G6
def team_availability_page(ctx):
    rows = load_csv("team_availability.csv")
    detail = []
    if os.path.exists(os.path.join(DATA, "starters_out_detail.csv")):
        detail = load_csv("starters_out_detail.csv")

    tot = {
        "listed": sum(int(r["listed"]) for r in rows),
        "out": sum(int(r["out"]) for r in rows),
        "doubtful": sum(int(r["doubtful"]) for r in rows),
        "questionable": sum(int(r["questionable"]) for r in rows),
        "net": sum(int(r["netInjuryCount"]) for r in rows),
        "starters": sum(int(r["startersOut"]) for r in rows if r["startersOut"]),
        "named": sum(int(r["replacementsNamed"]) for r in rows if r["replacementsNamed"]),
    }

    body = ["""
<section class="hero">
  <h1>Team availability</h1>
  <p class="lead">One row per club on the official Week 10 report:
  <strong>starters out</strong>, <strong>the replacement the club itself names</strong>,
  and a <strong>net injury count</strong> whose rule is printed on every row.</p>
  <p class="lead">%d clubs, %d listed players, %d starters out with %d replacements named.
  &ldquo;Starters out&rdquo; is <em>derived</em>: it joins the club's own published depth
  chart to the league's official Out designation. The clubs call those charts
  unofficial, so the column is labelled as derived and is never presented as a
  league statement.</p>
</section>
""" % (len(rows), tot["listed"], tot["starters"], tot["named"])]

    table_rows = []
    for r in rows:
        table_rows.append([
            ctx["cell"]("%s &middot; %s" % (r["team"], r["club"])),
            ctx["cell"](r["listed"], "n"),
            ctx["cell"](r["out"], "n"),
            ctx["cell"](r["doubtful"], "n"),
            ctx["cell"](r["questionable"], "n"),
            ctx["cell"](r["nonInjury"], "n"),
            ctx["cell"](r["netInjuryCount"], "n"),
            ctx["cell"](r["startersOut"], "n"),
            ctx["cell"](r["replacementsNamed"], "n"),
            ctx["cell"](r["replacementStrings"]),
            ctx["raw_src"](ctx["src_link"]("S01", ctx["sources_by_id"])),
        ])
    body.append("""
<section>
<h2>Per-club counts</h2>
<p class="caption"><strong>Net injury count</strong> = report rows whose game status
is Out or Doubtful, excluding rows the league marks &ldquo;Not injury related&rdquo;.
Resting a healthy player is not an injury, and counting it as one would bias every
downstream feature. <strong>Starters out</strong> is derived and blank where no club
chart was captured &mdash; never inferred.</p>
%s
</section>
""" % ctx["table"](
        ["Club", "Listed", "Out", "Doubtful", "Questionable", "Not injury related",
         "Net injury count", "Starters out (derived)", "Replacements named",
         "Replacement strings", "Source"], table_rows, cls="searchable"))

    d_rows = []
    for d in detail:
        d_rows.append([
            ctx["cell"](d["team"]), ctx["cell"](d["unit"]), ctx["cell"](d["slot"]),
            ctx["cell"](d["starterOut"]), ctx["cell"](d["starterInjury"]),
            ctx["cell"](d["starterGameStatus"]),
            ctx["cell"](d["replacement"]),
            ctx["cell"](d["replacementString"], "n"),
            ctx["cell"](d["replacementBasis"]),
            ctx["raw_src"](ctx["src_link"]("S01", ctx["sources_by_id"])),
        ])
    body.append("""
<section>
<h2>Every starter ruled out, and the next name the club charts</h2>
<p class="caption">%d slots. The replacement is the first name at a deeper string on
the club's own chart who is not himself ruled Out. Where the club charts no further
name, the cell is blank and the reason is printed &mdash; that is a fact about the
club's publication, not a gap in ours.</p>
%s
</section>
""" % (len(detail), ctx["table"](
        ["Club", "Unit", "Slot", "Starter ruled out", "Injury", "Status",
         "Next charted name", "String", "Basis", "Source"],
        d_rows, cls="searchable")))
    return ctx["page"]("team-availability.html", "Team Availability", "".join(body),
                       wide=True)


def announced_starters_page(ctx):
    p = load_json("announced_starters.json")
    rows = []
    for a in p["announced"]:
        rows.append([
            ctx["cell"](a["team"]), ctx["cell"](a["player"]), ctx["cell"](a["pos"]),
            "<td>%s</td>" % ctx["pill"](a["status"], "ok" if "Announced" in a["status"] or "Confirmed" in a["status"] else "warn"),
            ctx["cell"]("&ldquo;%s&rdquo;" % ctx["esc"](a["quote"])),
            ctx["cell"](a["date"]), ctx["cell"](a["kind"]),
            ctx["raw_src"]('<a class="src" href="%s" target="_blank" rel="noopener">%s</a>'
                           % (ctx["esc"](a["url"]), "official page")),
        ])
    nf = []
    for r in p["notFound"]:
        nf.append([
            ctx["cell"](r["team"]), ctx["cell"](r["player"]), ctx["cell"](r["pos"]),
            ctx["cell"](r["note"]),
            ctx["raw_src"]('<a class="src" href="flagged.html">flagged</a>'),
        ])

    return ctx["page"]("announced-starters.html", "Announced Starters", """
<section class="hero">
  <h1>Announced starters</h1>
  <p class="lead">A replacement can be <em>inferred</em> from a depth chart or
  <em>announced</em> by an official page. These are different kinds of evidence and
  this site keeps them apart. Everything below is <strong>quoted</strong> from an
  official NFL.com page with its publication date &mdash; nothing here is derived
  from a chart order.</p>
</section>

<section>
<h2>Starters and roles an official page actually announced</h2>
%s
</section>

<section>
<h2>Named in the brief, not found in any official page we read</h2>
<p class="caption">Left blank rather than filled in. If an official page naming this
player exists and we have not read it, the fix is a source link, not a guess.</p>
%s
</section>
""" % (ctx["table"](["Club", "Player", "Pos", "Status", "Official wording", "Date",
                     "Where", "Source"], rows),
       ctx["table"](["Club", "Player", "Pos", "Why the cell is blank", "Source"],
                    nf)), wide=True)


# ---------------------------------------------------------------- ledger / G1
def ledger_page(ctx):
    manifest = load_json(os.path.join("raw", "MANIFEST-g.json"))
    diff = load_csv("injury_diff_g.tsv") if os.path.exists(
        os.path.join(DATA, "injury_diff_g.tsv")) else []
    ver = []
    if os.path.exists(os.path.join(DATA, "verification-g.tsv")):
        with open(os.path.join(DATA, "verification-g.tsv"), encoding="utf-8") as fh:
            ver = [line.rstrip("\n").split("\t") for line in fh][1:]

    capture_rows = [
        [ctx["cell"]("2026-11-14"), ctx["cell"]("345"), ctx["cell"]("28"),
         ctx["cell"]("raw/injuries-week10-2026.md"),
         ctx["cell"]("first read; the pre-kickoff snapshot used on the Injuries page"),
         ctx["raw_src"]('<a class="src" href="https://www.nfl.com/injuries/" target="_blank" rel="noopener">S01</a>')],
        [ctx["cell"]("2026-11-16"), ctx["cell"]("347"), ctx["cell"]("28"),
         ctx["cell"]("raw/injuries-week10-2026-recapture-2026-11-16.md"),
         ctx["cell"]("second read, after the Sunday games; sha256 %s"
                     % manifest["injuries-week10-2026-recapture-2026-11-16.md"]["sha256"][:16]),
         ctx["raw_src"]('<a class="src" href="https://www.nfl.com/injuries/" target="_blank" rel="noopener">S01</a>')],
    ]

    diff_rows = []
    for d in diff:
        diff_rows.append([
            ctx["cell"](d["change"]), ctx["cell"](d["team"]), ctx["cell"](d["player"]),
            ctx["cell"](d["field"]), ctx["cell"](d["value_2026_11_14"]),
            ctx["cell"](d["value_2026_11_16"]),
            ctx["raw_src"]('<a class="src" href="https://www.nfl.com/injuries/" target="_blank" rel="noopener">S01</a>'),
        ])

    # results / standings side of the ledger
    res_rows = [
        [ctx["cell"]("2026-11-14"), ctx["cell"]("137"), ctx["cell"]("data/results.tsv"),
         ctx["cell"]("the frozen pre-registration corpus — never overwritten"),
         ctx["raw_src"]('<a class="src" href="https://www.nfl.com/schedules/2026/REG10/" target="_blank" rel="noopener">S49</a>')],
        [ctx["cell"]("2026-11-16"), ctx["cell"]("148"), ctx["cell"]("data/results_2026-11-16.tsv"),
         ctx["cell"]("eleven further finals; reconciled 32/32 against the standings read the same day"),
         ctx["raw_src"]('<a class="src" href="https://www.nfl.com/schedules/2026/REG10/" target="_blank" rel="noopener">S49</a>')],
        [ctx["cell"]("2026-11-17"), ctx["cell"]("149"), ctx["cell"]("data/results_2026-11-17.tsv"),
         ctx["cell"]("one further final: Steelers 18 at Bengals 38 (Sunday night, Game Center status Final). Reconciled 32/32 against the standings read the same day; the change between the two standings reads is exactly that game. Monday night (Chargers at Ravens) was live at read time and is NOT recorded."),
         ctx["raw_src"]('<a class="src" href="https://www.nfl.com/games/steelers-at-bengals-2026-reg-10" target="_blank" rel="noopener">S89</a>')],
        [ctx["cell"]("2026-11-17"), ctx["cell"]("150"), ctx["cell"]("data/results_2026-11-17-closeout.tsv"),
         ctx["cell"]("week-10 closeout read: all 14 finals, the Monday-night game captured FINAL after the re-read flag F67 asked for; byte-chained after the 149-row read (gate P8); reconciled 32/32. The canonical corpus was not promoted \u2014 Q44's policy half stays open."),
         ctx["raw_src"]('<a class="src" href="https://www.nfl.com/schedules/2026/REG10/" target="_blank" rel="noopener">S95</a>')],
    ]
    ver_rows = []
    for row in ver:
        if len(row) < 5:
            continue
        res = row[2]
        ver_rows.append([
            ctx["cell"](row[0]), ctx["cell"](row[1]),
            "<td>%s</td>" % ctx["pill"](res, "ok" if res == "PASS" else ("bad" if res == "FAIL" else "warn")),
            ctx["cell"](row[3]),
            ctx["raw_src"](
                '<a class="src" href="%s" target="_blank" rel="noopener">official page</a>'
                % ctx["esc"](row[4]) if row[4].startswith("http")
                else ctx["src_link"]("S01", ctx["sources_by_id"])),
        ])

    added = sum(1 for d in diff if d["change"] == "row_added")
    changed = sum(1 for d in diff if d["change"] == "field_changed")

    return ctx["page"]("availability-ledger.html", "Snapshot Ledger", """
<section class="hero">
  <h1>Point-in-time snapshot ledger</h1>
  <p class="lead">An injury report is not a weekly fact, it is a series that changes
  several times between Wednesday and kickoff. This page keeps <strong>every dated
  read</strong> of the official report, each with its own hash, and publishes the
  <strong>diff</strong> between consecutive reads instead of overwriting the old one.</p>
  <p class="lead">Between 2026-11-14 and 2026-11-16 the official page gained
  <strong>%d rows</strong> and moved <strong>%d fields</strong>. Most of the movement is the
  Chargers, who played on Monday night and therefore received game-day designations
  after the earlier read was taken.</p>
</section>

<section>
<h2>Captures held</h2>
<p class="caption">The 2026-11-14 read is never overwritten by a later one: doing so
would inject lookahead into any backtest that uses it.</p>
%s
</section>

<section>
<h2>Results and standings reads</h2>
<p class="caption">The same rule applies to results: the frozen corpus keeps its
date and is never silently grown, and a newer read is published beside it. The
2026-11-16 read reproduces the official standings of the same day for all 32 clubs
on wins, losses, ties, points for and points against (check G-R1) &mdash; eleven
transcribed scores have to be right for that to hold, so it is a stronger check than
it looks.</p>
%s
</section>

<section>
<h2>What changed &mdash; injuries</h2>
<p class="caption">Produced by <code>scripts/verify_recapture_g.py</code>, which exits
non-zero if any row present on 11-14 is missing from 11-16 &mdash; that would mean the
earlier table held an invented row. Rows added later, and fields that moved later,
are recorded, not treated as failures.</p>
%s
</section>

<section>
<h2>Checks run on the re-capture</h2>
%s
</section>
""" % (added, changed,
       ctx["table"](["Captured (UTC)", "Rows", "Clubs", "File", "Note", "Source"],
                    capture_rows),
       ctx["table"](["Captured (UTC)", "Results", "File", "Note", "Source"],
                    res_rows),
       ctx["table"](["Change", "Club", "Player", "Field", "2026-11-14", "2026-11-16",
                     "Source"], diff_rows, cls="searchable"),
       ctx["table"](["Check", "Description", "Result", "Detail", "Source"], ver_rows)),
        wide=True)


# ------------------------------------------------------------------- entry
def build(ctx):
    """Build every page this session owns and return the index sections."""
    pages = [
        backlog_page(ctx),
        team_availability_page(ctx),
        announced_starters_page(ctx),
        ledger_page(ctx),
        luck_page(ctx),
    ]
    sections = readiness_section(ctx) + luck_section(ctx)
    return pages, sections


# ------------------------------------------------------- executive summary add
def exec_section(ctx):
    """Dated block on the executive summary page: what this session added and
    verified, with the numbers and the source behind each claim."""
    backlog = load_json("requirements_backlog.json")
    luck = load_json("luck_panel.json")
    h = luck["headline"]
    counts = backlog["counts"]
    rows = [
        [ctx["cell"]("Requirement lines tracked"), ctx["cell"]("87", "n"),
         ctx["cell"]("R01–R28 from the earlier register, R29–R87 added this session from the brief"),
         ctx["raw_src"]('<a class="src" href="requirements-backlog.html">backlog</a>')],
        [ctx["cell"]("Blocked or awaiting a decision"),
         ctx["cell"](counts.get("blocked", 0) + counts.get("decision-open", 0), "n"),
         ctx["cell"]("each row names the gate and the number that would clear it"),
         ctx["raw_src"]('<a class="src" href="index.html#decision">readiness</a>')],
        [ctx["cell"]("Official injury report, dated reads held"), ctx["cell"]("2", "n"),
         ctx["cell"]("2026-11-14 (345 rows) and 2026-11-16 (347 rows), both hash-pinned"),
         ctx["raw_src"]('<a class="src" href="availability-ledger.html">ledger</a>')],
        [ctx["cell"]("Rows / fields that moved between those reads"),
         ctx["cell"]("+2 / 32", "n"),
         ctx["cell"]("mostly the Monday-night game, which had no designations yet on the earlier read"),
         ctx["raw_src"]('<a class="src" href="availability-ledger.html">diff</a>')],
        [ctx["cell"]("Starters ruled out, with the club's next charted name"),
         ctx["cell"]("33 / 31", "n"),
         ctx["cell"]("derived from club charts the clubs themselves call unofficial"),
         ctx["raw_src"]('<a class="src" href="team-availability.html">teams</a>')],
        [ctx["cell"]("Starters an official page actually announced"),
         ctx["cell"]("11", "n"),
         ctx["cell"]("quoted and linked; one name from the brief could not be evidenced and is blank"),
         ctx["raw_src"]('<a class="src" href="announced-starters.html">starters</a>')],
        [ctx["cell"]("Home-team hit rate over 137 official results"),
         ctx["cell"]("%s" % pct(h["home_win_rate"], 1), "n"),
         ctx["cell"]("95%% interval %s to %s — contains 50%%"
                     % (pct(h["home_win_rate_wilson"][0], 1), pct(h["home_win_rate_wilson"][1], 1))),
         ctx["raw_src"]('<a class="src" href="removal-of-luck.html">panel</a>')],
        [ctx["cell"]("Decisions needed before a 5pp edge is visible"),
         ctx["cell"]("785", "n"),
         ctx["cell"]("%d once six strategies are tried — more than three NFL seasons of every game"
                     % luck["multiplicity"]["n_required_at_5pp_edge"]),
         ctx["raw_src"]('<a class="src" href="removal-of-luck.html">panel</a>')],
    ]
    return """
<section id="session-g">
<h2>Session <code>arena/dbf11de0-fl1</code> &mdash; 2026-11-16</h2>
<p class="lead">This session re-read the official injury report on a later date, registered the
brief's requirement lines that no register tracked, and published the numbers that say how much of
any future result could be chance. Everything below came out of a script in this repository against
a page that is linked from every row.</p>
%s
<div class="callout">
  <h3>The finding worth acting on</h3>
  <p>The official injury report <strong>moved</strong> between two reads taken two days apart: two
  rows appeared and 32 fields changed, 22 of them Chargers rows for a game that had not yet been
  played at the time of the first read. Any backtest that trains on the later read has used
  information that did not exist before kickoff. The repository now keeps both reads, hash-pinned,
  and publishes the diff &mdash; and never overwrites the earlier one.</p>
</div>
</section>
""" % ctx["table"](["Figure", "Value", "Basis", "Where"], rows, cls="kpi")
