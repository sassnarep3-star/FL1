#!/usr/bin/env python3
"""
build_pages_m.py — session M pages, rendered with the consolidating build's
own helpers (tools/site.py) so styling, blank-value discipline and the link
checker all apply unchanged.

Pages written at repo root:
  results-feed.html         the verified results feed (137 games, row-level
                            official) + the ROI/backtest contract.
  originations.html         origination order side -> total -> moneyline, and
                            fair line | market line | difference as three
                            separate columns for all 272 markets of 2026.
  signal-vs-staking.html    the leaderboard split (signal ranks and rewards;
                            staking is risk telemetry) + the demotion gate
                            G-14 (live -> paper) and G-15.
  replacement-depth.html    the depth of the replacement, not just the fact.
  official-correlations.html  correlations computed only from officially
                            sourced numbers, each published with its n.

Run after tools/site.py NAV entries exist; then run tools/checklinks.py.
"""
import csv
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

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
raw_src = site_mod.raw_src
esc = site_mod.esc

DATA = os.path.join(ROOT, "data")


def load_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_json(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def num(v, nd=None):
    if v is None or str(v).strip() == "":
        return None
    try:
        f = float(v)
    except ValueError:
        return v
    if nd is not None:
        f = round(f, nd)
    return ("%g" % f) if f == int(f) and abs(f) < 1e15 and nd is None else (
        str(round(f, nd)) if nd is not None else str(f))


def link(href, label):
    return '<a class="src" href="%s">%s</a>' % (esc(href), esc(label))


# ---------------------------------------------------------------------------
def backtest_table():
    """Walk-forward backtest table (values preserved from data/backtest_calibration.tsv,
    computed by tools/brief.py — session arena/685f958d-fl1; merged here at integration)."""
    with open(os.path.join(DATA, "backtest_calibration.tsv"), newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    trs = []
    for r in rows:
        roi_cell = ('<td class="blank" title="ROI needs official prices (F18)">&mdash;</td>'
                    if not r["roi"] else "<td>%s</td>" % esc(r["roi"]))
        total = "total" in r["scope"]
        label = "%s <em>(total)</em>" % esc(r["scope"]) if total else esc(r["scope"])
        trs.append("<tr><td>%s</td><td class=\"num\">%s</td><td class=\"num\">%s</td>"
                   "<td class=\"num\">%s</td><td class=\"num\">%s</td><td class=\"num\">%s&ndash;%s</td>"
                   "<td class=\"num\">%s</td><td class=\"num\">%s</td><td class=\"num\">%s</td>"
                   "<td class=\"num\">%s</td>%s</tr>"
                   % (label, r["n_out_of_sample"], r["side_mae_model"], r["side_mae_constant"],
                      r["side_sign_hit_rate"], r["side_sign_ci95_low"], r["side_sign_ci95_high"],
                      r["total_mae_model"], r["total_mae_constant"], r["ml_brier_model"],
                      r["ml_brier_coinflip"], roi_cell))
    return table(["Scope", "n (out of sample)", "Side MAE (model)", "Side MAE (constant)",
                  "Sign hit rate", "95% CI", "Total MAE (model)", "Total MAE (constant)",
                  "ML Brier (model)", "ML Brier (50/50)", "ROI"], trs,
                 caption="Walk-forward backtest. Each week is predicted only from earlier weeks. "
                         "n is shown on every row. ROI is blank: it needs official prices, and "
                         "none exist (F18).")


# ---------------------------------------------------------------------------
def results_feed_page(sources_by_id):
    rows = load_csv("results_feed.csv")
    week_src = {}
    body = []
    for r in rows:
        wk = int(r["week"])
        week_src.setdefault(wk, r["source_ids"])
        body.append([
            cell(r["week"], "n"), cell(r["game_date"]),
            cell(r["away_team"]), cell(r["away_score"], "n"),
            cell(r["home_team"]), cell(r["home_score"], "n"),
            cell("OT" if r["overtime"] == "yes" else ""),
            cell(r["stadium"]),
            raw_src(src_link(r["source_ids"], sources_by_id)),
            raw_src(link(r["official_game_url"], "game page")),
        ])
    head = ["Wk", "Date", "Away", "Away pts", "Home", "Home pts", "OT",
            "Venue", "Week source", "Official link"]

    by_week = []
    for wk in sorted(week_src):
        n = sum(1 for r in rows if int(r["week"]) == wk)
        by_week.append([cell(wk, "n"), cell(n, "n"),
                        raw_src(src_link(week_src[wk], sources_by_id))])

    html = """
<h1>Verified results feed</h1>
<p class="lead">Every played game of the 2026 regular season with its final score, verified
row by row against official NFL.com week pages &mdash; the settlement source of truth backtests
and ROI are computed against. 137 games, weeks 1&ndash;10.</p>

<div class="note ok"><strong>Verification (2026-11-14).</strong> Each of the 137 finals was
transcribed from the official week page&rsquo;s own &ldquo;FINAL&rdquo; line into
<code>raw/official-finals-2026.tsv</code>, then compared field for field against two independent
captures (<code>data/results.tsv</code>, <code>data/schedule2026-d.csv</code>).
<code>scripts/verify_feed_m.py</code> reports <strong>137/137 PASS, zero mismatches</strong>.
The same files were previously reconciled to the official standings (records + PF + PA, 32/32
clubs) &mdash; see <a href="verification.html">Verification</a> and
<a href="schedule.html">Schedule 2026</a>.</div>

<h2>What a backtest can and cannot show</h2>
<div class="note"><ul>
<li><strong>Calibration and error:</strong> yes &mdash; walk-forward, each week predicted only
from earlier weeks, n on every row (below).</li>
<li><strong>ROI against <em>official</em> prices:</strong> no &mdash; no official league source
prices betting lines (F18, F25). ROI columns against third-party snapshots are published on the
strategy pages, labelled third-party throughout.</li>
<li><strong>Own-line honesty (F20):</strong> the own-line fair model does <strong>not</strong>
beat a constant benchmark out of sample on side or total MAE. Published because negative results
are part of the record.</li>
</ul></div>
__BT_TABLE__
<h2>Why a feed, and what it makes computable</h2>
<ul>
<li><strong>Settlement.</strong> Side, total and moneyline bets settle against these scores only.
<code>engine/results_settlement.py</code> refuses to settle or compute ROI on a price whose provenance
is not declared &mdash; market prices are NOT in the feed; they arrive from the price-snapshot
store or a declared third-party snapshot with a source id.</li>
<li><strong>ROI and backtests.</strong> <code>roi()</code> computes stake-normalised profit with
pushes removed from both numerator and denominator, and fails closed before producing a single
number if any bet lacks price provenance. 17 unit tests (<code>tests/test_results_feed.py</code>).</li>
<li><strong>What the feed does not contain.</strong> No prices, no player statistics, no snap
counts. Blanks stay blank; nothing is inferred.</li>
</ul>

<h2>Coverage by week</h2>
""" + table(["Week", "Games", "Official week page"], by_week,
            caption="Every week&rsquo;s row-level source is a live official page.") + """
<h2>The feed &mdash; 137 games</h2>
""" + table(head, body, cls="wide",
            caption="Every row carries the official game page it was verified against. "
                    "Source chips resolve to the registry on "
                    '<a href="sources.html">Sources</a>.') + """
<h2>Reproduce</h2>
<pre>python3 scripts/verify_feed_m.py         # three-way line-by-line check
python3 scripts/build_results_feed_m.py  # rebuild the feed from the raw capture
python3 -m engine.results_settlement --check   # loader contract check
python3 -m unittest tests.test_results_feed</pre>
"""
    html = html.replace("__BT_TABLE__", backtest_table())
    page("results-feed.html", "Verified Results Feed &amp; Backtest", html)


# ---------------------------------------------------------------------------
def originations_page(sources_by_id):
    fl = load_csv("fair_lines.csv")
    cal = load_json("fair_lines_calibration.json")
    order = load_json("origination_order.json")

    def side_rows():
        out = []
        for r in fl:
            out.append([
                cell(r["week"], "n"), cell(r["gameday"]),
                cell(r["away_team"]), cell(r["home_team"]),
                cell("yes" if r["played"] == "yes" else "no"),
                cell(num(r["side_fair_spread_away"], 1), "n"),
                cell(num(r["side_market_spread_away"], 1), "n"),
                cell(num(r["side_difference"], 1), "n"),
                cell(r["fair_basis"]),
            ])
        return out

    def total_rows():
        out = []
        for r in fl:
            out.append([
                cell(r["week"], "n"), cell(r["away_team"]), cell(r["home_team"]),
                cell(None),                       # fair total: never invented
                cell(num(r["total_market"], 1), "n"),
                cell(None),
                cell("S2 parameters unfitted (F24)"),
            ])
        return out

    def ml_rows():
        out = []
        for r in fl:
            out.append([
                cell(r["week"], "n"), cell(r["away_team"]), cell(r["home_team"]),
                cell(num(r["ml_fair_home_american"]), "n"),
                cell(num(r["ml_market_home_american"]), "n"),
                cell(num(r["ml_diff_home_prob_pts"], 2), "n"),
                cell(num(r["ml_fair_away_american"]), "n"),
                cell(num(r["ml_market_away_american"]), "n"),
                cell(num(r["ml_diff_away_prob_pts"], 2), "n"),
            ])
        return out

    ref = cal["published_reference"]
    cal_rows = [
        [cell("Games priced"), cell(cal["n_games"], "n"), cell(ref["n_games"], "n")],
        [cell("Mean signed error (pts)"),
         cell(num(cal["mean_signed_error_points"], 3), "n"),
         cell(ref["mean_signed_error_points"], "n")],
        [cell("Mean absolute error (pts)"),
         cell(num(cal["mean_absolute_error_points"], 3), "n"),
         cell(ref["mean_absolute_error_points"], "n")],
        [cell("Correlation with the close"),
         cell(num(cal["corr_with_close"], 4), "n"),
         cell(ref["corr_with_close"], "n")],
    ]

    stage_html = ""
    for s in order["order"]:
        stage_html += (
            "<li><strong>Stage %s &mdash; %s.</strong> %s <em>(%s)</em></li>"
            % (esc(str(s["stage"])), esc(s["market"]), esc(s["why_first"] if "why_first" in s else s.get("why_second") or s.get("why_third") or ""),
               esc(s["status"])))

    html = """
<h1>Line origination</h1>
<p class="lead">We originate our own numbers. The order is mandated and fixed:
<strong>the side first, then the total, then the moneyline.</strong> Every market we originate
publishes three separate columns &mdash; the model&rsquo;s fair line, the market line, and the
difference &mdash; and no cell is ever inferred.</p>

<h2>Origination order</h2>
<ul>""" + stage_html + """</ul>
<p class="caption">A game is re-originated in this order at every release. The side is the anchor
quantity: total and moneyline are downstream of the same scoring decomposition, and committing the
margin first stops dependent markets from leaking information back into it.</p>

<h2>The three-column rule</h2>
<ul>
<li><strong>Fair line &mdash; MODEL OUTPUT.</strong> Causal pre-game Elo, versioned:
<code>""" + esc(cal["model_version"]) + """</code>.</li>
<li><strong>Market line &mdash; SOURCE.</strong> The pinned third-party snapshot
<code>data/raw/games.csv</code> (nflverse/nfldata, <a href="sources.html#S47">S47</a>), flagged
&mdash; no official NFL price source exists (flag F25).</li>
<li><strong>Difference &mdash; COMPUTED.</strong> Fair minus market. Spread columns use the
away-posted unit of the snapshot (positive = away underdog / home favoured):
<em>negative difference = the market gives the away side more points than the model says is fair
&mdash; value on the away side at the market number; positive = value on the home side.</em>
Moneyline differences are published in implied-probability percentage points against the
market&rsquo;s raw implied probability (vig included).</li>
</ul>

<div class="note"><strong>Worked example (2026 W1, NE @ SEA).</strong> The market number is
SEA&rsquo;s side &ldquo;NE +3&rdquo; (away-posted <code>+3</code>). The model&rsquo;s fair away
number is <code>+0.9</code> &mdash; it makes Seattle a smaller favourite than the market does, so
the difference is <code>&minus;2.1</code> and the value read is on the <strong>away</strong> side
(NE +3). The game finished SEA 13&ndash;10: NE +3 pushed, which is exactly what a
&plusmn;0-model-edge on a 3-point line looks like.</div>

<h2>Model card and calibration</h2>
<p>The fair-line engine is not invented here: it is the Computed Research Layer&rsquo;s documented
engine (<a href="docs/computed/lines.html">docs/computed/lines.html</a>), and this build proves
equivalence game by game &mdash; <strong>5,336 of 5,336 pre-game Elo values identical</strong>
(asserted in <code>scripts/build_fair_lines_m.py</code>) &mdash; then reproduces its published
calibration:</p>
""" + table(["Calibration stat", "This build", "Published reference"], cal_rows,
            caption="Computed over every 2006&ndash;2026 regular-season game with a closing "
                    "line in the pinned snapshot. Reproducible: "
                    "<code>python3 scripts/build_fair_lines_m.py</code>.") + """
<div class="note warn"><strong>What this model is not.</strong> By its own calibration it is a
slightly worse version of the market, not an independent one: mean absolute disagreement 2.89
points, sd of disagreement 3.56. It publishes a number &mdash; beating the close needs information
the market does not already have. Totals are deliberately blank (S2 parameters unfitted, flag
F24). Future games carry the fair basis &ldquo;Elo snapshot&rdquo; (re-originated weekly before
release).</div>

<h2>Stage 1 &mdash; Side (spread): fair | market | difference</h2>
""" + table(["Wk", "Date", "Away", "Home", "Played",
             "Fair (away pts)", "Market (away pts)", "Difference", "Fair basis"],
            side_rows(), cls="wide",
            caption="All 272 regular-season games of 2026. Fair = MODEL OUTPUT; market = "
                    "third-party (S47, flagged); difference = COMPUTED.") + """
<h2>Stage 2 &mdash; Total: fair | market | difference</h2>
""" + table(["Wk", "Away", "Home", "Fair total", "Market total", "Difference", "Note"],
            total_rows(), cls="wide",
            caption="The columns are published; the fair and difference cells stay BLANK "
                    "because the totals model has no fitted parameter. A number here would be "
                    "a fabrication (flag F24).") + """
<h2>Stage 3 &mdash; Moneyline: fair | market | difference</h2>
""" + table(["Wk", "Away", "Home",
             "Fair home (Am)", "Market home (Am)", "Home diff (prob pts)",
             "Fair away (Am)", "Market away (Am)", "Away diff (prob pts)"],
            ml_rows(), cls="wide",
            caption="Fair American odds converted from the same win probability as the side "
                    "(p clipped [0.02, 0.98]). Differences are implied-probability percentage "
                    "points vs the market&rsquo;s raw implied probability.") + """
<h2>Origination policy</h2>
<ul>""" + "".join("<li>%s</li>" % esc(p) for p in order["origination_policy"]) + """</ul>
<h2>Reproduce</h2>
<pre>python3 scripts/build_fair_lines_m.py   # equivalence assert + calibration + table</pre>
"""
    page("originations.html", "Line Origination", html, wide=True)


# ---------------------------------------------------------------------------
def signal_vs_staking_page(sources_by_id):
    ss = load_csv("signal_vs_staking.csv")
    gov = load_json("governance_gates.json")

    sig_rows = []
    for r in ss:
        sig_rows.append([
            cell(r["signal_rank"], "n"), cell(r["strategy_id"]),
            cell(r["family"]), cell(r["market"]),
            cell(r["n_settled"], "n"), cell(num(r["signal_hit_rate"], 4), "n"),
            cell(num(r["signal_hit_ci_low"], 4), "n"),
            cell(num(r["signal_breakeven_hit"], 4), "n"),
            cell(num(r["signal_flat_roi"], 4), "n"),
            cell(num(r["signal_p_value"], 5), "n"),
            cell(r["signal_gates_passed"], "n"),
            raw_src('<td>%s</td>' % pill(r["signal_verdict"],
                                         "ok" if r["signal_verdict"] == "APPROVED" else "bad")),
            cell(r["reward_eligible"]),
        ])

    st_rows = []
    for r in sorted(ss, key=lambda x: int(x["staking_rank"])):
        st_rows.append([
            cell(r["staking_rank"], "n"), cell(r["strategy_id"]),
            cell(r["staking_bets_staked"], "n"),
            cell(num(r["staking_staked_units"], 1), "n"),
            cell(num(r["staking_profit_units"], 2), "n"),
            cell(num(r["staking_roi"], 4), "n"),
            cell(num(r["staking_max_drawdown_units"], 2), "n"),
            raw_src('<td>%s</td>' % pill(r["staking_would_mask"],
                                         "warn" if r["staking_would_mask"] == "yes" else "")),
        ])

    masked = [r["strategy_id"] for r in ss if r["staking_would_mask"] == "yes"]

    g = gov["rows"][0]
    g15 = gov["rows"][1]

    html = """
<h1>Signal vs staking</h1>
<p class="lead">The leaderboard separates <strong>signal</strong> (what the picks are worth at flat
stakes) from <strong>staking</strong> (what a betting policy did to the bankroll), so a lucky
staking run cannot mask a bad signal. Only the signal ledger ranks, rewards and promotes.</p>

<div class="note ok"><strong>The rule (gate G-15, hard).</strong> Rank order, reward eligibility
and capital promotion read the SIGNAL columns exclusively. The staking ledger is published beside
it as risk telemetry: it can cap or remove exposure &mdash; and a staking risk breach triggers the
demotion gate &mdash; but it can never promote. %s</div>

<h2>Ledger 1 &mdash; SIGNAL (flat 1-unit stakes). The only ranking that counts</h2>
""" % (
        ("In the current candidate set, <strong>%d entrants show exactly that failure mode</strong>: "
         "positive staking profit over a non-positive signal &mdash; "
         "<strong>%s</strong>. They carry the MASKED flag below."
         % (len(masked), esc(", ".join(masked)))) if masked else
        "No current entrant is masked.") + table(
        ["Signal rank", "Strategy", "Family", "Market", "n", "Hit rate",
         "Wilson low", "Break-even", "Flat ROI", "p (1-sided)", "Gates",
         "Verdict", "Reward eligible"],
        sig_rows, cls="wide",
        caption="Settled at 1 unit per bet over the pinned snapshot (2006&ndash;2026, walk-forward "
                "with a sealed out-of-sample tail). Gates are the 7 lab gates "
                "(<a href=\"validation.html\">validation</a>); ranking uses gates passed then flat "
                "ROI. No staking column enters this sort.") + """
<h2>Ledger 2 &mdash; STAKING (risk telemetry only)</h2>
""" + table(["Staking rank", "Strategy", "Bets staked", "Staked units",
             "Profit units", "ROI", "Max drawdown", "MASKED"],
            st_rows,
            caption="Policy: %s. The MASKED flag marks a positive staking run over a "
                    "non-positive signal &mdash; the exact failure this split exists to prevent."
                    % esc(ss[0]["staking_policy"] if ss else "")) + """
<h2>Demotion gate G-14 &mdash; a live strategy goes back to paper</h2>
""" + table(["Field", "Rule"], [
        [cell("Gate"), cell(g["gate"] + " (" + g["kind"] + ")")],
        [cell("Trigger A — signal decay"), cell(g["trigger_a_signal_decay"])],
        [cell("Trigger B — risk breach"), cell(g["trigger_b_risk_breach"])],
        [cell("Trigger C — compliance"), cell(g["trigger_c_compliance"])],
        [cell("Destination"), cell(g["destination"])],
        [cell("Execution"), cell(g["execution"])],
        [cell("Re-entry"), cell(g["re_entry"])],
        [cell("Asymmetry"), cell(g["asymmetry_rule"])],
        [cell("Why"), cell(g["why"])],
    ], caption="Promotion is slow (two reviews); demotion is fast (one trigger) and automatic. "
               "Gate G-15 above is the ranking contract it enforces.") + """
<h2>Luck controls this design stands on</h2>
<ul>
<li>Break-even arithmetic: &minus;110 needs 52.38&#37;; separating a true 55&#37; from that at
80&#37; power needs <strong>2,243</strong> settled bets &mdash; see
<a href="validation.html">Validation Gates</a>.</li>
<li>Ranking on lower confidence bounds and deflated significance, not profit
(<a href="docs/pages/measured.html">measured layer</a>).</li>
<li>Sealed entries, overlap merging and abstention logging (anti-gaming rules in the
<a href="strategies.html">leaderboard design</a>).</li>
</ul>
<h2>Reproduce</h2>
<pre>python3 scripts/build_signal_staking_m.py   # both ledgers from the pinned snapshot</pre>
"""
    page("signal-vs-staking.html", "Signal vs Staking", html, wide=True)


# ---------------------------------------------------------------------------
def replacement_depth_page(sources_by_id):
    rows = load_csv("replacement_depth.csv")
    body = []
    for r in rows:
        body.append([
            cell(r["club"]), cell(r["unit"]),
            cell("%s / spot %s" % (r["slot"], r["line"] or "—")),
            cell(r["starter"]), cell(r["starter_status"]),
            cell(r["out_above"] or "0", "n"),
            cell(r["replacement"]),
            cell(r["replacement_depth"]),
            cell(r["replacement_own_status"]),
            raw_src(src_link(r["depth_source"], sources_by_id)
                    + " " + src_link(r["injury_source"], sources_by_id)),
            cell(r["flag"]),
        ])
    n_off = sum(1 for r in rows if r["unit"] == "Offense")
    n_def = sum(1 for r in rows if r["unit"] == "Defense")
    n_blank = sum(1 for r in rows if not r["replacement"])
    n_deep = sum(1 for r in rows if r["replacement_rank"] and int(r["replacement_rank"]) >= 3)

    html = """
<h1>Replacement depth</h1>
<p class="lead">Not just the fact of a replacement &mdash; the <strong>depth</strong> of it. When a
starter carries an official game status, this page names the player the club&rsquo;s own depth chart
lists next, his <strong>string</strong> (2nd, 3rd, 4th), and how many listed players are Out above
him. Week 10, 2026: <strong>%d</strong> affected lineup spots &mdash; %d on offense, %d on defense.</p>

<div class="note"><strong>Rule (derived, published with every row).</strong> Inputs are the official
Week 10 injury report (<a href="sources.html#S01">S01</a>) and the clubs&rsquo; own published depth
charts (per-club sources, chips in the table). Name joins use only the explicit alias table
&mdash; never fuzzy matching. Players whose official game status is &ldquo;Out&rdquo; are skipped;
the first listed player remaining is the replacement, and his published rank at that lineup spot is
his string. A player absent from the club&rsquo;s report is labelled &ldquo;not listed&rdquo; &mdash;
an official fact, and per league policy absence is <em>not</em> evidence of availability.</div>

<h2>Headline findings</h2>
<ul>
<li><strong>%d</strong> replacement(s) come from <strong>3rd string or deeper</strong> &mdash; the
brief&rsquo;s &ldquo;2nd/3rd/4th string backup&rdquo; case, carried with its cascade count.</li>
<li><strong>%d</strong> spots have <strong>no listed replacement remaining</strong> (every player
the club lists there is Out): those cells are BLANK and flagged, never filled in.</li>
<li>Coverage is 31 of 32 clubs &mdash; Houston publishes its chart as an image (flag F16), so no
Houston rows exist rather than invented ones.</li>
<li>League-wide historical depth-of-replacement tracking (starters-not-primary, max sequence rank,
1999&ndash;2026) is published on <a href="depth.html">Backup Depth</a> and in the
<a href="docs/computed/availability.html">computed availability model</a>.</li>
</ul>

<h2>The table &mdash; every affected spot</h2>
""" % (len(rows), n_off, n_def, n_deep, n_blank) + table(
        ["Club", "Unit", "Spot", "Starter", "Starter status", "Out above",
         "Replacement", "Replacement depth", "Replacement status",
         "Sources", "Flag"],
        body, cls="wide",
        caption="Week 10 official injury report (S01) joined to club depth charts. "
                "Derived columns carry the rule in data/replacement_depth.csv.") + """
<h2>Reproduce</h2>
<pre>python3 scripts/build_replacement_depth_m.py</pre>
"""
    page("replacement-depth.html", "Replacement Depth", html, wide=True)


# ---------------------------------------------------------------------------
def correlations_page(sources_by_id):
    rows = load_csv("correlations-official.csv")
    body = []
    for r in rows:
        body.append([
            cell(r["corr_id"]), cell(r["x"]), cell(r["y"]),
            cell(r["method"]), cell(r["n"], "n"), cell(r["r"], "n"),
            cell(r["se_r"], "n"), cell(r["window"]),
            cell(r["note"]),
        ])
    html = """
<h1>Official-source correlations</h1>
<p class="lead">Correlations computed <strong>only</strong> from officially sourced numbers, and
every value published <strong>with its n</strong>. Nothing from a third-party feed enters this
table.</p>

<div class="note"><strong>Policy.</strong> The inputs are the verified results feed
(<a href="results-feed.html">results-feed.html</a>) &mdash; 137 games whose finals are row-level
official (nfl.com week pages, S49&ndash;S58). The measurement register
(<code>data/correlations.json</code>, C-01&ndash;C-15) stays <em>blank</em> under the same rule
until each pair&rsquo;s inputs are officially sourced (flag F-11, open). Player-prop correlations
(<a href="prop-correlations.html">Prop Correlations</a>) are computed from a third-party archive
and are published separately with that label (flag F17) &mdash; they are not mixed in here.</div>

<h2>The values</h2>
""" + table(["ID", "X", "Y", "Method", "n", "r", "SE(r)", "Window", "Note"],
            body, cls="wide",
            caption="Pearson product-moment. Every row carries its n. Method of computation: "
                    "<code>scripts/build_correlations_m.py</code>, deterministic.") + """
<h2>What the numbers say (and do not say)</h2>
<ul>
<li>Same-game scoring co-movement (C-O1, <strong>r=+0.076, n=137</strong>) and week-to-week form
persistence (C-O2/C-O3, |r|&lt;0.09, n=242) are all <strong>near zero</strong> in this sample.
On officially sourced numbers alone, a bettor assuming hot-hand scoring persistence is leaning on
noise &mdash; and same-game parlay legs priced as if independent are close to the truth at the
<em>game total</em> level (player-level dependence is a different question &mdash; see the
third-party prop table).</li>
<li>These are <strong>small-sample</strong> values (one season&rsquo;s first ten weeks). n is
published precisely so the reader can discount them; the feed grows weekly and the script
recomputes deterministically.</li>
<li>Correlation is not causation and none of these edges a market: they calibrate assumptions
(parlay leg dependence, form reversion) that the origination and pricing layers consume.</li>
</ul>
<h2>Reproduce</h2>
<pre>python3 scripts/build_correlations_m.py</pre>
"""
    page("official-correlations.html", "Official Correlations", html)


# ---------------------------------------------------------------------------
def main():
    sources = build.load("sources.tsv")
    sources_by_id = {s["id"]: s for s in sources}
    results_feed_page(sources_by_id)
    originations_page(sources_by_id)
    signal_vs_staking_page(sources_by_id)
    replacement_depth_page(sources_by_id)
    correlations_page(sources_by_id)
    print("wrote results-feed.html, originations.html, signal-vs-staking.html, "
          "replacement-depth.html, official-correlations.html")


if __name__ == "__main__":
    main()
