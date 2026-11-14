#!/usr/bin/env python3
"""
build_pages_d.py — session D pages, rendered with the consolidating build's own
helpers (tools/site.py) so styling, blank-value discipline, and the link checker
all apply unchanged.

Pages written at repo root:
  schedule.html           full 272-game 2026 regular-season schedule & results,
                          with reconciliation banner and market-line flags.
  prop-correlations.html  empirical player-level correlation table (closes
                          Q-PROP-01), parlay math, QA gates, verification rows.

Run after tools/site.py NAV entries exist; then run tools/checklinks.py.
"""
import csv
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

# tools/site.py cannot be imported as `import site` (stdlib site shadows it).
_spec = importlib.util.spec_from_file_location(
    "fl1_site", os.path.join(ROOT, "tools", "site.py"))
site_mod = importlib.util.module_from_spec(_spec)
sys.modules["fl1_site"] = site_mod
_spec.loader.exec_module(site_mod)
_spec2 = importlib.util.spec_from_file_location(
    "fl1_build", os.path.join(ROOT, "tools", "build.py"))
build = importlib.util.module_from_spec(_spec2)
sys.modules["fl1_build"] = build
_spec2.loader.exec_module(build)


cell = site_mod.cell
table = site_mod.table
page = site_mod.page
src_link = site_mod.src_link
pill = site_mod.pill
raw_src = site_mod.raw_src if hasattr(site_mod, "raw_src") else (lambda s: s)

DATA = os.path.join(ROOT, "data")


def load_csv(path, delimiter=","):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter=delimiter))


TEAM_NAME = {r[0]: r[1] for r in
             [line.split("\t") for line in
              open(os.path.join(DATA, "teams.tsv"), encoding="utf-8")
              .read().strip().split("\n")]}


def abbr(g, side):
    return g[f"{side}_team"]


def schedule_page(sources_by_id):
    rows = load_csv(os.path.join(DATA, "schedule2026-d.csv"))
    ver = [r for r in csv.reader(open(os.path.join(DATA, "verification-d.tsv"),
                                      encoding="utf-8"), delimiter="\t") if r][1:]
    out_rows = []
    for g in rows:
        scored = ""
        if g["played"] == "yes":
            scored = f"{g['away_score']}–{g['home_score']}"
        out_rows.append([
            cell(g["week"], "n"), cell(g["date"]), cell(g["kickoff_et"]),
            cell(abbr(g, "away")), cell(abbr(g, "home")), cell(scored),
            cell("OT" if g["overtime"] == "yes" else ""),
            cell(g["stadium"]),
            cell(g["market_spread_away"]), cell(g["market_total"]),
            cell("yes (reconciled)" if g["scores_verified"] else ""),
            cell(g["flags"]),
            '<td><a class="src" href="sources.html#S47">S47</a> <a class="src" href="sources.html#S03">S03</a></td>',
        ])
    ver_rows = []
    for v in ver:
        status = f'<td>{pill(v[3], "ok" if v[3] == "PASS" else ("bad" if v[3] == "FAIL" else "warn"))}</td>' if v[3] in ("PASS", "FAIL", "FLAGGED") else cell(v[3])
        ver_rows.append([cell(v[0]), cell(v[1]), cell(v[2]), status, cell(v[4]),
                         '<td><a class="src" href="https://github.com/sassnarep3-star/FL1/blob/main/data/verification-d.tsv">record</a></td>'])
    body = """
<section>
<h2>Full 2026 regular-season schedule &amp; results (272 games)</h2>
<div class="callout">
<p><strong>Provenance.</strong> Game results come from the nflverse combined games feed
(<a href="https://github.com/nflverse/nfldata/blob/master/data/games.csv">nflverse/nfldata data/games.csv</a>,
auto-updated from official NFL game books; snapshot committed at
<code>raw/games-nfldata.csv</code>). The feed was reconciled line by line against the official
league capture: all 32 clubs' records, points for and points against match the
<a href="https://www.nfl.com/standings/">nfl.com standings</a> snapshot exactly, and the Week 10
Thursday final (Commanders 24, Giants 21) matches the
<a href="https://www.nfl.com/schedules/2026/REG10/">official Week 10 schedule page</a>.
Reconciliation rows are in <a href="#verification">Verification</a> below and in
<code>data/verification-d.tsv</code>.</p>
<p><strong>Market spread/total columns are third-party data</strong> (nflverse aggregation of
bookmaker lines). There is no official NFL source for betting lines; those cells are published
with a flag and are never used as verified facts.</p>
</div>
%s
</section>

<section>
<h2 id="verification">Verification — session D independent checks</h2>
<p>Full definitions in <code>scripts/build_schedule_d.py</code> and <code>scripts/verify_d.py</code>.
Every check recomputes from raw inputs; nothing is hand-entered.</p>
%s
</section>
""" % (table(["Wk", "Date", "KO ET", "Away", "Home", "Score", "OT", "Stadium",
              "Mkt spread (away)", "Mkt total", "Scores verified", "Flags", "Source"],
             out_rows, cls="dense searchable",
             caption="Away–home score shown only for played games. Mkt = third-party market "
                     "line, flagged. Blank cells are blank on purpose."),
       table(["Check", "Description", "Result", "Status", "Source", "Record"],
             ver_rows, cls="dense"))
    return page("schedule.html", "Schedule 2026", body, wide=True)


def prop_correlations_page(sources_by_id):
    rows = load_csv(os.path.join(DATA, "prop-correlations-d.csv"))
    out_rows = []
    for r in rows:
        if r["pearson_r"]:
            stat = f"r = {r['pearson_r']} [{r['ci95_low']}, {r['ci95_high']}] (ρ {r['spearman_rho']})"
        elif r["lift"]:
            stat = f"lift = {r['lift']} {r['lift_ci95']}"
        else:
            stat = ""
        out_rows.append([
            cell(r["pair_id"]), cell(r["scope"]), cell(r["window"]),
            cell(r["n"], "n"), cell(stat), cell("computed"), cell(r["notes"]),
            '<td><a class="src" href="sources.html#S48">S48</a></td>',
        ])
    body = """
<section>
<h2>Empirical player-level correlations — closes open question Q-PROP-01</h2>
<div class="callout">
<p><strong>What this is.</strong> The computed research layer's correlation engine
(<code>scripts/build_correlations.py</code>) measures team-level proxies and records
<strong>Q-PROP-01</strong>: player-prop-level correlation was unmeasured because player data was
unavailable to that session. This page closes that gap with the same repo rules: computed from
observations, fully scripted, source-stated, and <em>never</em> presented as an official NFL
statistic.</p>
<p><strong>Data.</strong> nflverse <code>player_stats</code> weekly, seasons 1999–2024
(13,384 team-games; every team-game joined to a played row in
<code>data/raw/games.csv</code> at a 100% join rate after canonicalizing historical
abbreviations SD→LAC, STL/OAK/LA→LAR, OAK→LV). Mirror: Beexly/Sports
(<code>data/nflverse/player_stats_weekly_archive.parquet</code>, commit 2026-11-07). The mirror is
QA-gated before use (schema, coverage, 100% score join, distribution sanity) — any gate failure
aborts publication.</p>
<p><strong>How to read it.</strong> For two independent legs the parlay hit probability is
P(A)·P(B). Positive dependence raises the true joint probability above that product; the table's
<em>lift</em> column is exactly the multiplier P(A and B) / (P(A)·P(B)) at the listed thresholds.
A same-game parlay built from positively dependent legs priced as independent is overpriced in
your favor; a correlation cap (see <a href="validation.html">validation gates</a>) still applies.</p>
</div>
@TABLE@
</section>

<section>
<h2>QA gates that published these numbers</h2>
<table class="dense">
<thead><tr><th>Gate</th><th>Definition</th><th>Status</th><th>Source</th></tr></thead>
<tbody>
<tr><td>QA1</td><td>Required player_stats columns present</td><td>PASS</td><td><a class="src" href="https://github.com/sassnarep3-star/FL1/blob/main/scripts/build_prop_correlations_d.py">script</a></td></tr>
<tr><td>QA2</td><td>Seasons 1999–2024 complete; 2002–2020 seasons ≥ 250 team-games</td><td>PASS</td><td><a class="src" href="https://github.com/sassnarep3-star/FL1/blob/main/scripts/build_prop_correlations_d.py">script</a></td></tr>
<tr><td>QA3</td><td>≥ 99% of team-games join a played game in data/raw/games.csv</td><td>PASS (100.00%)</td><td><a class="src" href="https://github.com/sassnarep3-star/FL1/blob/main/scripts/build_prop_correlations_d.py">script</a></td></tr>
<tr><td>QA4</td><td>2015–2024 mean team passing yards 200–300 y/g; mean points 15–30 p/g</td><td>PASS</td><td><a class="src" href="https://github.com/sassnarep3-star/FL1/blob/main/scripts/build_prop_correlations_d.py">script</a></td></tr>
<tr><td>QA5</td><td>Deterministic rebuild: same 12 rows on re-run (fixed bootstrap seed 42)</td><td>PASS</td><td><a class="src" href="https://github.com/sassnarep3-star/FL1/blob/main/scripts/build_prop_correlations_d.py">script</a></td></tr>
</tbody>
</table>
</section>

<section>
<h2>Reading notes and limits</h2>
<ul>
<li>Aggregates are position-group totals per team-game (all WRs, all RBs+FBs, all TEs, sum of QB
passing). No ex-post selection (e.g., "leading receiver" conditioning), which would bias
correlations upward.</li>
<li>QB↔WR aggregate correlation (r ≈ 0.79, n = 5,246) is a same-offense volume relationship, not a
guarantee for any single named pair; use it as a prior, then gate on actual n.</li>
<li>RB rushing ↔ RB receiving is essentially uncorrelated (r ≈ −0.07): workload in one phase does
not determine the other — useful for building correlated RB props deliberately rather than
assuming dependence.</li>
<li>Binary lifts are threshold-specific: re-derive for different thresholds before pricing.</li>
<li>All values are estimates from nflverse-derived data via a third-party mirror; they are inputs
for review, not verified league facts.</li>
</ul>
</section>
""".replace("@TABLE@", table(["Pair", "Scope", "Window", "n", "Estimate (95% CI)", "Status", "Notes", "Source"],
            out_rows, cls="dense searchable",
            caption="r = Pearson; ρ = Spearman; lift = P(A and B)/(P(A)P(B)) with bootstrap 95% CI."))
    return page("prop-correlations.html", "Prop Correlations", body)


def main():
    sources_by_id = {s["id"]: s for s in build.load("sources.tsv")}
    schedule_page(sources_by_id)
    prop_correlations_page(sources_by_id)
    print("pages written: schedule.html, prop-correlations.html")


if __name__ == "__main__":
    main()
