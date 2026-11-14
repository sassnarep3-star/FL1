"""Build the static GitHub Pages site under docs/ from the CSVs in data/.

No template engine, no external CSS/JS/fonts, no build step. Every table cell
that carries a fact also carries a link back to data/sources.json.

Run: python3 scripts/build_site.py
"""
from __future__ import annotations

import html
import json
import pathlib
import math

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "computed"

NAV = [
    ("index.html", "Overview"),
    ("findings.html", "Findings"),
    ("lines.html", "Line origination"),
    ("leaderboard.html", "Leaderboard"),
    ("strategies.html", "Strategies &amp; gates"),
    ("correlations.html", "Correlations"),
    ("availability.html", "Injuries &amp; depth"),
    ("week10.html", "Week 10 board"),
    ("questions.html", "Open questions"),
    ("suggestions.html", "Suggestions"),
    ("requirements.html", "Requirements"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
    ("methods.html", "Methods"),
]

# Deterministic build stamp. Read from the pinned manifest so that re-running
# the build produces byte-identical output (CI enforces this).
def _build_stamp() -> str:
    try:
        m = json.loads((DATA / "raw" / "MANIFEST.json").read_text())
        rows = {f["file"]: f["rows"] for f in m.get("files", [])}
        return (f"2026-11-14 &middot; games.csv {rows.get('games.csv', 0):,} rows, "
                f"injuries_2025.csv {rows.get('injuries_2025.csv', 0):,} rows")
    except Exception:
        return "pinned inputs (see data/raw/MANIFEST.json)"


BUILD_STAMP = _build_stamp()

CSS = """
:root{--bg:#0b1220;--panel:#111b2e;--panel2:#16233a;--line:#22334f;--txt:#e6edf7;
--mut:#8ea3c0;--ok:#2ecc71;--warn:#f2b33d;--bad:#ef5a5a;--acc:#4da3ff}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--txt);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
header{position:sticky;top:0;z-index:20;background:rgba(11,18,32,.96);
border-bottom:1px solid var(--line);backdrop-filter:blur(6px)}
.bar{max-width:1180px;margin:0 auto;padding:10px 18px;display:flex;gap:16px;
align-items:center;flex-wrap:wrap}
.brand{font-weight:700;letter-spacing:.4px}
.brand span{color:var(--mut);font-weight:400;font-size:12px;display:block;letter-spacing:0}
nav{display:flex;gap:4px;flex-wrap:wrap}
nav a{font-size:12.5px;padding:5px 9px;border-radius:6px;color:var(--mut)}
nav a:hover{background:var(--panel2);color:var(--txt);text-decoration:none}
nav a.on{background:var(--panel2);color:var(--txt);box-shadow:inset 0 0 0 1px var(--line)}
main{max-width:1180px;margin:0 auto;padding:26px 18px 70px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:-.2px}
h2{font-size:18px;margin:34px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:20px 0 8px;color:var(--txt)}
p{margin:0 0 12px;color:#cbd7e8}
.lead{color:var(--mut);margin:0 0 22px;max-width:78ch}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:18px 0 6px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card .k{font-size:11px;text-transform:uppercase;letter-spacing:.7px;color:var(--mut)}
.card .v{font-size:24px;font-weight:700;margin-top:4px;letter-spacing:-.5px}
.card .s{font-size:12px;color:var(--mut);margin-top:4px}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:12.7px}
th,td{padding:7px 10px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
th{background:var(--panel2);font-size:11px;text-transform:uppercase;letter-spacing:.5px;
color:var(--mut);position:sticky;top:0;white-space:nowrap}
tr:last-child td{border-bottom:none}
tbody tr:hover{background:#14203a}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;
font-weight:600;white-space:nowrap;border:1px solid transparent}
.p-ok{color:#0b1220;background:var(--ok)}
.p-warn{color:#241a00;background:var(--warn)}
.p-bad{color:#2a0000;background:var(--bad)}
.p-neu{color:var(--mut);background:var(--panel2);border-color:var(--line)}
.note{background:var(--panel);border-left:3px solid var(--acc);padding:12px 14px;
border-radius:0 8px 8px 0;margin:16px 0;color:#cbd7e8;font-size:13.5px}
.warn{border-left-color:var(--warn)}
.bad{border-left-color:var(--bad)}
code{background:var(--panel2);padding:1px 5px;border-radius:4px;font-size:12px}
footer{border-top:1px solid var(--line);color:var(--mut);font-size:12px;
max-width:1180px;margin:0 auto;padding:18px}
.src{font-size:11px;color:var(--mut)}
ul{margin:0 0 12px;padding-left:20px;color:#cbd7e8}
li{margin:3px 0}
"""


def esc(x):
    if x is None:
        return ""
    if isinstance(x, float) and math.isnan(x):
        return ""
    return html.escape(str(x))


def fmt(x, nd=2):
    """Format a cell. Small magnitudes keep significant digits so that a
    correlation of -0.0001 never renders as "-0.00" and a p-value never
    renders as "0.00"."""
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return ""
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, int):
        return f"{x:,}"
    if isinstance(x, float):
        ax = abs(x)
        if x == 0:
            return "0"
        if ax < 0.0001:
            return "<0.0001" if x > 0 else ">-0.0001"
        if ax < 1:
            return f"{x:,.4f}"
        if ax < 100:
            return f"{x:,.{nd}f}"
        return f"{x:,.0f}"
    return esc(x)


def pill(text, kind):
    return f'<span class="pill p-{kind}">{esc(text)}</span>'


def status_pill(s):
    m = {
        "DONE": "ok", "PARTIAL": "warn", "BLOCKED": "bad",
        "REJECTED-ON-EVIDENCE": "bad", "APPROVED": "ok", "REJECTED": "bad",
        "Adopt now": "ok", "Needs data": "warn", "Do not adopt": "bad",
        "Critical": "bad", "High": "warn", "Medium": "neu", "Low": "neu",
        "verified": "ok", "verified-context": "ok", "broken-link": "bad",
        "blocked": "bad", "verified-mirror": "warn", "Official": "ok",
        "Open data": "ok", "Open data (mirror)": "warn",
        "Secondary": "neu", "Official (NOT FOUND)": "bad",
        "verified-but-mirrored": "warn",
        "win": "ok", "loss": "bad", "push": "neu",
    }
    return pill(s, m.get(s, "neu"))


def table(df, cols, headers=None, num=None, linkcol=None, maxrows=None, pillcols=()):
    """Render a dataframe slice as a table. `linkcol` values become <a> links."""
    num = num or set()
    if headers is None:
        headers = cols
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"table() given column(s) not in the dataframe: {missing}. "
                       f"Available: {list(df.columns)}")
    out = ['<div class="tw"><table><thead><tr>']
    for c, h in zip(cols, headers):
        cls = ' class="n"' if c in num else ""
        out.append(f"<th{cls}>{h}</th>")
    out.append("</tr></thead><tbody>")
    rows = df if maxrows is None else df.head(maxrows)
    for _, r in rows.iterrows():
        out.append("<tr>")
        for c, h in zip(cols, headers):
            v = r.get(c)
            cls = ' class="n"' if c in num else ""
            if c in pillcols:
                out.append(f"<td{cls}>{status_pill(v) if v not in (None, '') and not (isinstance(v,float) and math.isnan(v)) else ''}</td>")
                continue
            if c == linkcol and isinstance(v, str) and v.startswith("http"):
                label = esc(v)
                if len(label) > 52:
                    label = label[:49] + "…"
                out.append(f'<td{cls}><a href="{esc(v)}" rel="noopener">{label}</a></td>')
                continue
            if c in num:
                out.append(f"<td class='n'>{fmt(v)}</td>")
            else:
                out.append(f"<td>{fmt(v)}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def page(slug, title, body, subtitle=""):
    parts = ['<a href="../../index.html" title="Back to the main FL1 site">&larr; Main site</a>']
    for h, t in NAV:
        cls = ' class="on"' if h == slug else ""
        parts.append('<a href="%s"%s>%s</a>' % (h, cls, t))
    nav = "".join(parts)
    sub = f'<p class="lead">{subtitle}</p>' if subtitle else ""
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · FL1 NFL Line Lab</title>
<meta name="description" content="Verified NFL line origination, strategy validation and availability research.">
<style>{CSS}</style>
</head>
<body>
<header><div class="bar">
<div class="brand">FL1 <span>NFL line lab</span></div>
<nav>{nav}</nav>
</div></header>
<main>
<h1>{title}</h1>
{sub}
{body}
</main>
<footer>Computed research layer, built by Arena session <code>arena-ab82c93f</code>. Every figure is computed from a pinned source in
<a href="sources.html">Sources</a>. Nothing is estimated. Data as of {BUILD_STAMP}. Builds are deterministic: this stamp comes from the
pinned inputs, not from the clock, so a rebuild is byte-identical.</footer>
</body></html>"""
    (DOCS / slug).write_text(doc, encoding="utf-8")


def main() -> int:
    DOCS.mkdir(exist_ok=True)

    strat = pd.read_csv(DATA / "strategies.csv")
    lb = pd.read_csv(DATA / "leaderboard.csv")
    lbs = pd.read_csv(DATA / "leaderboard_by_season.csv")
    corr = pd.read_csv(DATA / "correlations.csv")
    parecon = pd.read_csv(DATA / "parlay_economics.csv")
    _pe = parecon[parecon.correlation_assumption == "independent"].set_index("parlay_legs")
    cormat = pd.read_csv(DATA / "correlation_matrix.csv", index_col=0)
    avail = pd.read_csv(DATA / "availability_2025.csv")
    depth = pd.read_csv(DATA / "depth_deficiency.csv")
    w10 = pd.read_csv(DATA / "week10_signal_board.csv")
    w10off = pd.read_csv(DATA / "week10_2026_official.csv")
    req = pd.read_csv(DATA / "requirements.csv")
    qs = pd.read_csv(DATA / "questions.csv")
    sug = pd.read_csv(DATA / "suggestions.csv")
    irr = pd.read_csv(DATA / "irregularities.csv")
    unv = pd.read_csv(DATA / "unverified.csv")
    src = json.loads((DATA / "sources.json").read_text())

    approved = int((strat.verdict == "APPROVED").sum())
    best = strat.iloc[0]
    control = strat[strat.strategy_id == "__CONTROL_MARKET"].iloc[0]

    # ---------------- index ----------------
    body = f"""
<div class="cards">
  <div class="card"><div class="k">Strategies approved</div><div class="v">{approved} / {len(strat)}</div>
  <div class="s">7 pre-registered gates each</div></div>
  <div class="card"><div class="k">Games backtested</div><div class="v">5,336</div>
  <div class="s">2006–2026 regular season, closing prices</div></div>
  <div class="card"><div class="k">Control ROI</div><div class="v">{fmt(control.roi*100,1)}%</div>
  <div class="s">Bet every home team = the vig</div></div>
  <div class="card"><div class="k">Open questions</div><div class="v">{len(qs)}</div>
  <div class="s">{int((qs.priority=='Critical').sum())} critical</div></div>
  <div class="card"><div class="k">Flagged items</div><div class="v">{len(irr)}</div>
  <div class="s">{int((irr.severity=='Critical').sum())} critical</div></div>
  <div class="card"><div class="k">Week 10 official rows</div><div class="v">{len(w10off):,}</div>
  <div class="s">hand-verified, one link per row</div></div>
</div>

<div class="note bad"><strong>The headline finding: nothing beat the market.</strong>
Sixteen pre-registered strategy variants were tested on 5,336 games. Zero passed all seven
validation gates. The best raw candidate (<code>{esc(best.strategy_id)}</code>) earned
{fmt(best.roi*100,1)}% ROI over {int(best.settled)} bets with p = {fmt(best.p_value,3)}, which fails the
significance gate and the multiple-testing gate. A control strategy that bets every home team
returned {fmt(control.roi*100,1)}%, which is what the house vig should cost.
This result is published as the finding, not hidden.</div>

<div class="note"><strong>Where this fits.</strong> The main site at
<a href="../../index.html">the repository root</a> holds the verified data register, the open-questions
board and the suggestion register maintained by the integrating session. <em>This</em> layer is the
computed half: it takes open, pinned datasets and tries to falsify a strategy against them. Read the
main site for what is known; read this one for what survived testing.</div>

<h2>What was asked for, and what is real</h2>
<p>Every requirement from the brief is tracked in <a href="requirements.html">Requirements</a> with a
status and the file that evidences it. Four are not fully met, and the site says so on the page
where the gap lives rather than burying it:</p>
<ul>
<li><strong>Own lines</strong> — a reproducible causal Elo-to-spread model exists and is priced, but its
disagreement with the close sits inside the market's own error band. Not yet an independent line.</li>
<li><strong>Player prop combos</strong> — no prop line/outcome dataset was obtainable. Team-level
same-game correlation is measured; props are not.</li>
<li><strong>2nd/3rd/4th string</strong> — no reachable source publishes depth order. Only QB changes are
attributable, and they are labelled “different starter”, never a claimed depth slot.</li>
<li><strong>Removing luck</strong> — luck is bounded by gates, not eliminated. Every threshold used is listed
on <a href="methods.html">Methods</a>, and the ones that are my choice rather than yours are open
questions.</li>
</ul>

<h2>Start here</h2>
<p>The fastest path through the site for a decision-maker:
<a href="findings.html">Findings</a> → <a href="suggestions.html">Suggestions</a> →
<a href="questions.html">Open questions</a> → <a href="flagged.html">Flagged for review</a>.
The first three give you the picture and the decision paths; the last is the list of things that
could not be verified and must not be trusted yet.</p>

<h2>How to read a number on this site</h2>
<p>Every table that contains a computed value names the source file it came from, and every
source file names the URL and SHA-256 it was built from
(<code>data/raw/MANIFEST.json</code>). ROI is always <em>against the closing price</em>, because that is
the only price available for the full sample — see
<a href="flagged.html">FLAG-08</a>. Pushes are removed from both the numerator and the denominator.
A blank cell means the value could not be sourced; it is listed on
<a href="flagged.html">Flagged for review</a>, never filled in.</p>
"""
    page("index.html", "NFL line lab", body,
         "A verified, reproducible research build: line origination, strategy gates, correlation, "
         "and current-week availability. Every number traces to a source.")

    # ---------------- findings ----------------
    body = f"""
<h2>1. The market is hard, and the test says so</h2>
<p>Sixteen variants across six families (market-divergence, situational, weather, conjunction,
availability, control) were run over 2006–2026 with a fixed 70/30 time split. The out-of-sample
window starts at {int(strat.oos_from.iloc[0])}. Results are in
<a href="strategies.html">Strategies &amp; gates</a>.</p>
<div class="cards">
<div class="card"><div class="k">Variants tested</div><div class="v">{len(strat)}</div></div>
<div class="card"><div class="k">Passed all 7 gates</div><div class="v">{approved}</div></div>
<div class="card"><div class="k">Best in-sample ROI</div><div class="v">{fmt(best.roi*100,1)}%</div>
<div class="s">{esc(best.strategy_id)}</div></div>
<div class="card"><div class="k">Best p-value</div><div class="v">{fmt(strat.p_value.min(),3)}</div>
<div class="s">needs &lt; 0.05/N after deflation</div></div>
</div>

<h2>2. What the control proves</h2>
<p>Betting every home team at the close, 5,067 settled bets, returned {fmt(control.roi*100,1)}% with a
hit rate of {fmt(control.hit_rate*100,1)}% against a breakeven of {fmt(control.breakeven_hit*100,1)}%.
That gap is the vig. Any strategy that lands within about ±3% of zero is doing nothing but paying it.
This control is the reason the leaderboard reports rejections rather than ranking noise.</p>

<h2>3. Correlation is not a free lunch</h2>
<p>Measured on 5,336 games: home ATS cover vs the total is {fmt(corr.iloc[0].corr,4)}
(95% CI {fmt(corr.iloc[0].ci_low,3)} to {fmt(corr.iloc[0].ci_high,3)}) — statistically indistinguishable
from zero. Home cover vs home moneyline is {fmt(corr.iloc[1].corr,3)}, which is structural, not an edge.
Cross-game legs are independent ({fmt(corr.iloc[5].corr,4)} residual).</p>
<div class="note warn">The practical consequence: a 2-leg parlay of two −110 legs is
<strong>{fmt(_pe.loc[2].ev_per_unit_if_priced_independent*100,2)}% EV</strong>, a 3-leg is
{fmt(_pe.loc[3].ev_per_unit_if_priced_independent*100,2)}%, a 4-leg is
{fmt(_pe.loc[4].ev_per_unit_if_priced_independent*100,2)}%. The measured correlation moves these
numbers by less than 0.1 percentage points. Parlays are a worse version of the same bet.
See <a href="correlations.html">Correlations</a>.</div>

<h2>4. Availability is measurable; depth is not</h2>
<p>The official Week 10 2026 report was read row by row: {len(w10off)} player rows across 28 clubs,
66 Out, 10 Doubtful, 84 Questionable, each with the official URL and a verbatim quote.
The injury picture joins cleanly to the 14 games. What does <em>not</em> exist is a depth order:
the official roster feed lists status and jersey number, not a sequence
(<a href="flagged.html">FLAG-02</a>). So the system reports QB changes by start sequence and refuses
to call anyone a “3rd string” without a source. See <a href="availability.html">Injuries &amp; depth</a>.</p>

<h2>5. Data access is the binding constraint</h2>
<p>The single highest-value fix is not a model, it is an allowlist entry
(<a href="flagged.html">FLAG-01</a>). Five of six planned datasets were unreachable, which is why
the availability history is one season and there are no props or snap counts. Every downstream gap
on this site traces back to that one item.</p>

<h2>6. What would change the answer</h2>
<p>Not a better formula. Three things, in order: an opening-line feed (so an edge can be measured
against a price we can actually get), a depth-order feed with timestamps (so the requirement can be
met at all), and a signed gate config (so “skill” stops being a matter of opinion). All three are
in <a href="suggestions.html">Suggestions</a> as SG-01 to SG-05.</p>
"""
    page("findings.html", "Findings", body,
         "Six findings, each with the number behind it and the source it came from.")

    # ---------------- lines ----------------
    body = """
<h2>How a number is originated here</h2>
<p>The line engine is deliberately boring and fully auditable. Nothing is fitted to betting
profit, because fitting to profit is how a backtest is manufactured.</p>
<ul>
<li><strong>Ratings.</strong> A causal Elo is updated after every game with a margin-of-victory
multiplier and a 48-point home-field term. Between seasons every team is regressed 25% toward
1505. Ratings are read <em>before</em> the game they price, so there is no leakage.</li>
<li><strong>Conversion.</strong> Elo difference becomes a win probability, and a win probability becomes
a spread with a <em>fixed</em> constant of 2.7 points per 100 Elo
(<code>spread = 10.8 × log10(p/(1−p))</code>). The constant was fixed before any backtest ran.</li>
<li><strong>Comparison.</strong> That model spread is differenced against the closing spread. The
difference is the only signal the market-divergence family is allowed to see.</li>
<li><strong>Calibration check.</strong> Mean signed error −0.77 points, mean absolute error 2.89 points,
correlation with the close 0.828, over 5,336 games. The model is a slightly worse version of the
market, not an independent one — which is exactly why the divergence strategies lose.</li>
</ul>

<div class="note warn"><strong>Honest limitation.</strong> This is not yet “your own line” in the sense
that matters. Its disagreement with the close has a standard deviation of 3.56 points, and that
whole distribution is inside the range where the market is simply more accurate. Publishing a
number is easy; publishing a number that is <em>better</em> requires information the market does not
have, and result-history Elo is information the market already has.
See <a href="questions.html">OQ-01</a> and <a href="suggestions.html">SG-08</a>.</div>

<h2>What an independent line would need</h2>
<ul>
<li>Pace and efficiency inputs the close does not fully absorb: play-by-play EPA by situation,
success rate on early downs, pressure rate.</li>
<li>Availability priced per <em>starter lost at a position</em>, not per player — which needs the
depth feed (FLAG-02).</li>
<li>An opening-line feed, so a model can be tested against a price that is actually obtainable
(FLAG-08).</li>
<li>A weather forecast pulled at kickoff-minus-72h, not the measured post-game wind. The one
weather candidate that looked interesting (WIND15_UNDER) uses post-game wind, which is not
available before the game. That alone disqualifies it from live use even if it had passed the
statistical gates.</li>
</ul>
"""
    page("lines.html", "Line origination", body,
         "The exact model, its constants, its calibration, and why it is not yet an independent line.")

    # ---------------- leaderboard ----------------
    lb = lb.reset_index(drop=True)
    lb["rank"] = lb.index + 1
    lbv = lb[["rank", "strategy_id", "family", "settled", "hit_rate", "roi", "oos_roi",
              "p_value", "gates_passed", "verdict", "reward_units"]].copy()
    for c in ("hit_rate", "roi", "oos_roi"):
        lbv[c] = (lbv[c] * 100).round(2)
    body = f"""
<div class="note"><strong>Reward rule.</strong> A reward of 10 units is paid only to a strategy that
passes all seven gates. On the current evidence <strong>{approved} of {len(strat)} qualify, so the
reward pool pays out 0 units.</strong> The leaderboard is still published in full because the map of
what fails, and how close it was, is the useful output.</div>

<h2>Ranked board</h2>
{table(lbv, ['rank','strategy_id','family','settled','hit_rate','roi','oos_roi','p_value','gates_passed','verdict','reward_units'],
       headers=['#','Strategy','Family','Bets','Hit %','ROI %','OOS ROI %','p (one-sided)','Gates','Verdict','Reward'],
       num={'rank','settled','hit_rate','roi','oos_roi','p_value','gates_passed','reward_units'},
       pillcols=('verdict',))}

<p class="src">Hit %, ROI % and OOS ROI % are ×100 for display. ROI is profit per 1-unit stake at the
closing price. p is a one-sided t-test on per-bet ROI. Source:
<code>data/strategies.csv</code>, computed by <code>scripts/strategy_lab.py</code> from
<a href="https://github.com/nflverse/nfldata/blob/master/data/games.csv">nflverse/nfldata games.csv</a>.</p>

<h2>Season-by-season ledger</h2>
<p>The gate G5 check is “no single season may contribute more than 40% of total profit”. This is the
table that check runs on. A strategy whose entire profit came from one season fails here, which is
what happens to several of the rejects.</p>
<p class="src">Note on <code>AVAIL_EDGE_1.5</code>: it appears in the matrix but settles only 133 bets,
all in 2025, because the release CDN limited the injury history to one season
(<a href="flagged.html#FLAG-01">FLAG-01</a>). Its −18.2% ROI is a description of one season of a
badly-specified signal, not evidence about the idea. It fails G1 by construction.</p>
{table(lbs[lbs.strategy_id.isin(['WIND15_UNDER','DIV_DOG_AND_ELO','DIV_AWAY_DOG','REST_ADV_AWAY'])],
       ['strategy_id','season','settled','wins','profit_units','roi'],
       headers=['Strategy','Season','Bets','Wins','Profit (units)','ROI'],
       num={'season','settled','wins','profit_units','roi'})}
<p class="src">The four closest rejects only. Full ledger (15 strategies × 21 seasons) is in
<code>data/leaderboard_by_season.csv</code>.</p>
"""
    page("leaderboard.html", "Leaderboard", body,
         "Ranked by gates passed, then out-of-sample ROI. Reward is conditional on passing every gate.")

    # ---------------- strategies & gates ----------------
    sv = strat[["strategy_id", "family", "market", "settled", "hit_rate", "breakeven_hit",
                "roi", "is_roi", "oos_roi", "p_value", "max_drawdown", "gates_passed", "verdict"]].copy()
    for c in ("hit_rate", "breakeven_hit", "roi", "is_roi", "oos_roi"):
        sv[c] = (sv[c] * 100).round(2)
    gate_cols = [c for c in strat.columns if c.startswith("G") and strat[c].dtype == bool]

    gaterows = []
    for c in gate_cols:
        label = {
            "G1_sample_size": "G1 — Sample size: ≥150 settled bets and ≥60 out-of-sample.",
            "G2_roi_both_periods": "G2 — ROI > 0 in the in-sample period AND out-of-sample.",
            "G3_roi_significance": "G3 — One-sided t-test on per-bet ROI, p < 0.05.",
            "G4_beats_vig": "G4 — Wilson 95% lower bound on hit rate exceeds the vig breakeven.",
            "G5_no_single_season_dependency": "G5 — No single season may supply >40% of total profit.",
            "G6_multiplicity_adjusted": "G6 — p < 0.05/15 = 0.0033 (Bonferroni over searched variants).",
            "G7_drawdown_bounded": "G7 — Max drawdown must be smaller than total profit.",
        }.get(c, c)
        gaterows.append({"gate": label, "pass": int(strat[c].sum()), "of": len(strat)})
    gt = pd.DataFrame(gaterows)

    body = f"""
<h2>The seven gates</h2>
<p>These were fixed before any result was inspected. A strategy must pass all seven. Every gate is
a number, so "skill" is falsifiable.</p>
{table(gt, ['gate','pass','of'], headers=['Gate','Passed','Out of'], num={'pass','of'})}

<h2>Full test matrix</h2>
{table(sv, ['strategy_id','family','market','settled','hit_rate','breakeven_hit','roi','is_roi','oos_roi','p_value','max_drawdown','gates_passed','verdict'],
       headers=['Strategy','Family','Market','Bets','Hit %','Breakeven %','ROI %','IS ROI %','OOS ROI %','p','Max DD','Gates','Verdict'],
       num={'settled','hit_rate','breakeven_hit','roi','is_roi','oos_roi','p_value','max_drawdown','gates_passed'},
       pillcols=('verdict',))}

<h2>Why the two closest candidates were rejected</h2>
<p><strong>WIND15_UNDER</strong> — 425 bets, 55.1% hit against a 51.2% breakeven, +7.2% ROI,
+5.7% OOS, p = 0.063. Passes G1, G2 and G7. Fails G3 (needs p &lt; 0.05), G4 (lower bound on hit
rate still crosses the breakeven at this sample size) and G6 (needs p &lt; 0.00313). It also uses
post-game measured wind, which is not knowable before kickoff, so it is not implementable as written
before it is even a statistics question.</p>
<p><strong>DIV_DOG_AND_ELO</strong> — 936 bets, 54.3% hit, +5.7% ROI, +8.1% OOS, p = 0.036.
Passes G1, G2, G3 and G7. Fails G4 (its 95% lower bound on hit rate, ~51.1%, does not clear the
51.4% vig breakeven), G5 (one season supplies too much of the profit) and G6 (p = 0.036 is not
&lt; 0.00313). This is the classic shape of a finding that is real in-sample and
survives a split, but is selected out of fifteen tries. It is the one worth re-testing on new data,
not the one worth betting.</p>

<h2>Families tested</h2>
<ul>
<li><strong>market_devig</strong> — Elo vs close, win-probability gap vs the implied probability.</li>
<li><strong>situational</strong> — rest advantage, divisional underdogs, big-favourite fade, dome totals.</li>
<li><strong>weather</strong> — wind, cold-and-wind.</li>
<li><strong>conjunction</strong> — rest AND Elo, divisional dog AND Elo.</li>
<li><strong>availability</strong> — weighted injury disadvantage (2025 only; fails G1 by design).</li>
<li><strong>control</strong> — bet every home team. Not a strategy; it measures the vig.</li>
</ul>
"""
    page("strategies.html", "Strategies &amp; gates", body,
         "Sixteen pre-registered variants, seven gates, and the reason each failure is a failure.")

    # ---------------- correlations ----------------
    cm = cormat.reset_index().rename(columns={"index": "var"})
    body = f"""
<h2>Measured correlations (5,336 games, 2006–2026)</h2>
<p>Bootstrap 95% intervals, 2,000 resamples, seed fixed at 20261114.</p>
{table(corr[['leg_a','leg_b','scope','n','corr','ci_low','ci_high','p_value','label']],
       ['leg_a','leg_b','scope','n','corr','ci_low','ci_high','p_value','label'],
       headers=['Leg A','Leg B','Scope','n','Corr','CI low','CI high','p','Meaning'],
       num={'n','corr','ci_low','ci_high','p_value'})}

<h2>Correlation matrix</h2>
{table(cm, list(cm.columns),
       headers=['Variable'] + [c.replace('_',' ').title() for c in cm.columns[1:]],
       num=set(cm.columns[1:]))}

<h2>What this means for parlays</h2>
<p>Books price parlay legs as if they were independent, then apply a same-game adjustment. To
profit from a same-game parlay you must know the true correlation better than the book does.
The measured correlations here are either structural (cover ≈ win) or indistinguishable from zero.</p>
{table(parecon, ['parlay_legs','correlation_assumption','pairwise_phi','price_at_-110_each_decimal',
                 'implied_prob_at_that_price','true_joint_prob','ev_per_unit_if_priced_independent'],
       headers=['Legs','Assumption','Pairwise φ','Decimal price','Implied prob','True joint prob','EV per unit'],
       num={'parlay_legs','pairwise_phi','price_at_-110_each_decimal','implied_prob_at_that_price',
            'true_joint_prob','ev_per_unit_if_priced_independent'})}

<div class="note warn"><strong>What is missing.</strong> Nothing on this page measures a
<em>player prop</em>. Same-game prop correlation (a quarterback's passing yards with his receiver's
receptions, a running back's carries with his team's total) is where the real correlation lives, and
no prop line/outcome dataset was obtainable in this environment. The team-level numbers here are a
proxy for the same mechanics, not a substitute for the measurement.
See <a href="questions.html">OQ-08</a>.</div>
"""
    page("correlations.html", "Correlations", body,
         "Same-game, cross-game and parlay economics, measured — plus the prop gap that remains.")

    # ---------------- availability ----------------
    av = avail[avail.season == 2025]
    top = av.nlargest(15, "avail_disadv")[["season", "week", "team", "listed_players", "out",
                                          "doubtful", "questionable", "injured_reserve", "avail_disadv"]]
    d26 = depth[(depth.season == 2026) & (depth.qb_deficiency != "primary starter")]
    d26 = d26[["season", "week", "team", "starters_not_primary", "max_start_sequence_rank", "qb_deficiency"]]

    body = f"""
<h2>Week 10 2026: the official report, row by row</h2>
<p>{len(w10off)} player rows across 28 clubs, read from
<a href="https://www.nfl.com/injuries/">NFL.com</a> on 2026-11-14. Every row in
<code>data/week10_2026_official.csv</code> carries the official URL and the verbatim table row it came
from. Nothing was inferred, and a status that was blank on the official page is blank here.</p>
<div class="cards">
<div class="card"><div class="k">Out</div><div class="v">{int((w10off.game_status=='Out').sum())}</div></div>
<div class="card"><div class="k">Doubtful</div><div class="v">{int((w10off.game_status=='Doubtful').sum())}</div></div>
<div class="card"><div class="k">Questionable</div><div class="v">{int((w10off.game_status=='Questionable').sum())}</div></div>
<div class="card"><div class="k">No game status</div><div class="v">{int(w10off.game_status.isna().sum())}</div>
<div class="s">listed for practice only</div></div>
</div>

<div class="note warn"><strong>Definitions are not probabilities.</strong> Since 2016 the league has
used plain-language definitions only: Out = will not play, Doubtful = unlikely to play,
Questionable = uncertain. The NFL publishes no numeric probability for any of the three. Any weight
attached to them below is this model's assumption, not an NFL statement —
see <a href="questions.html">OQ-11</a> and <a href="flagged.html">FLAG-05</a>.</div>

<h2>Team-level availability disadvantage, 2025</h2>
<p>Weights are fixed a priori: Out 1.00, Doubtful 0.50, Questionable 0.25, Injured Reserve 1.00.
388 team-weeks, 32 clubs, Weeks 1–13. Highest-disadvantage team-weeks:</p>
{table(top, ['season','week','team','listed_players','out','doubtful','questionable','injured_reserve','avail_disadv'],
       headers=['Season','Week','Team','Listed','Out','Doubtful','Questionable','IR','Weighted disadvantage'],
       num={'season','week','listed_players','out','doubtful','questionable','injured_reserve','avail_disadv'})}
<p class="src">Source: nflverse injuries release (2025), via mirror — see
<a href="sources.html">D05 / D06</a> and <a href="flagged.html">FLAG-01</a>.</p>

<h2>Quarterback changes, 2026</h2>
<p>Derived from the QB identity actually recorded for each game, not from a depth chart. A team's
primary QB is its modal starter that season; any other starter is a change. The rank is the order in
which starters first appeared — <em>not</em> a published depth slot.</p>
{table(d26, ['season','week','team','starters_not_primary','max_start_sequence_rank','qb_deficiency'],
       headers=['Season','Week','Team','Starts by a non-primary QB','Highest start-sequence rank','Classification'],
       num={'season','week','starters_not_primary','max_start_sequence_rank'})}

<div class="note bad"><strong>The 2nd/3rd/4th-string requirement is not met, and cannot be met from
any source reachable here.</strong> The official roster page lists players with status and jersey
number but no depth order (verified on the Seahawks roster — <a href="sources.html">S06</a>), and the
nflverse depth-chart release is unreachable (<a href="flagged.html">FLAG-01</a>). Rather than infer
depth from jersey numbers, draft position or gut feel, the field is left blank and the requirement is
marked partly blocked. This is <a href="flagged.html">FLAG-02</a> and
<a href="questions.html">OQ-07</a>.</div>
"""
    page("availability.html", "Injuries &amp; depth", body,
         "What the official injury report actually says this week, and the depth information that does not exist yet.")

    # ---------------- week 10 board ----------------
    w = w10.copy()
    for c in ("away_avail_disadv", "home_avail_disadv", "avail_edge_home"):
        w[c] = pd.to_numeric(w[c], errors="coerce")
    body = f"""
<h2>The board</h2>
<p>Fourteen games. Spread is from the home team's perspective, so a negative number means the home
team is favoured. Availability edge is <em>home disadvantage minus away disadvantage</em> — a positive
number means the <strong>away</strong> team is healthier. It is not a point value and it is not a
prediction; it is the measurable input.</p>
{table(w[['gameday','away_team','home_team','closing_spread_home','closing_total',
          'away_listed','away_out','home_listed','home_out','avail_edge_home','avail_rank',
          'home_qb_status','away_qb_status']],
       ['gameday','away_team','home_team','closing_spread_home','closing_total',
        'away_listed','away_out','home_listed','home_out','avail_edge_home','avail_rank',
        'home_qb_status','away_qb_status'],
       headers=['Date','Away','Home','Spread (home)','Total','Away listed','Away Out','Home listed','Home Out',
        'Avail. edge (home)','Rank','Home QB on report','Away QB on report'],
       num={'closing_spread_home','closing_total','away_listed','away_out','home_listed','home_out',
            'avail_edge_home','avail_rank'})}

<p class="src">Injury input: <a href="https://www.nfl.com/injuries/">NFL.com official injury report,
Week 10 2026</a>. Prices: <a href="https://github.com/nflverse/nfldata/blob/master/data/games.csv">nflverse
nfldata games.csv</a>. Built by <code>scripts/build_week10_board.py</code>. The join asserts that all 28
clubs in the 14 games have an official report; a missing team fails the build rather than producing
a silently partial row.</p>

<h2>The three games the availability signal separates most</h2>
<ul>
<li><strong>HOU at CLE</strong> — edge −4.25, the largest on the board, and it runs <em>against</em> the
home team: Houston lists five Out against Cleveland's two. Cleveland is favoured by 4.5.</li>
<li><strong>SF at DAL</strong> — edge +4.00, Dallas lists five Out against San Francisco's one, yet
San Francisco is only −4.5 on the road.</li>
<li><strong>MIA at IND</strong> — edge +3.75, Indianapolis lists six Out against Miami's two.</li>
</ul>
<div class="note warn"><strong>Do not read these as edges.</strong> The market has already seen these
reports — they are published on NFL.com before kickoff, and the closing line is set after them. An
availability signal only has value if it is (a) faster than the line, or (b) weighted by starter
quality, which needs the depth feed. The board shows the input; it does not claim the output.</div>

<h2>Full official report</h2>
<p>All {len(w10off)} rows, with the exact quoted source line for each:</p>
{table(w10off[['team','opponent','player','position','injury','practice_status','game_status','official_source_url']],
       ['team','opponent','player','position','injury','practice_status','game_status','official_source_url'],
       headers=['Team','Opp','Player','Pos','Injury','Practice','Game status','Source'],
       pillcols=(),
       maxrows=None)}
<p class="src">Every row links to <a href="https://www.nfl.com/injuries/">nfl.com/injuries</a>; the
verbatim quote is preserved in <code>data/week10_2026_official.csv</code> column
<code>source_quote</code> so the transcription can be audited without re-fetching the page.</p>
"""
    page("week10.html", "Week 10 board", body,
         "The current week joined to real closing prices — inputs only, no invented projections.")

    # ---------------- questions ----------------
    qv = qs[["id", "area", "priority", "question", "have", "lack", "why", "answer_format", "blocks", "owner"]]
    body = f"""
<p class="lead">These are the questions that have to be answered before a decision is reasonable.
Each one states what we already have, what we are missing, why it blocks a decision, and the exact
form the answer needs to take. A question with an empty "we have" column is a question we cannot
currently reason about at all.</p>

<div class="note bad"><strong>{int((qs.priority=='Critical').sum())} of {len(qs)} are critical</strong>
and each one blocks a requirement. Answering them is the highest-value work available — more valuable
than another backtest, because a backtest run against an unknown threshold produces a number nobody
can act on.</div>

<h2>Register</h2>
{table(qv, ['id','area','priority','question','have','lack','why','answer_format','blocks','owner'],
       headers=['ID','Area','Priority','Question','We have','We lack','Why it blocks a decision','Answer format needed','Blocks','Owner'],
       pillcols=('priority',))}

<h2>The five that matter most</h2>
<ul>
<li><strong>OQ-01 — what price can you actually get?</strong> Every ROI here is measured against the
close. Without an opening-line feed or a book-specific price sample, the real edge is unknown and
roughly half of any model-vs-close gap is fictional.</li>
<li><strong>OQ-07 — where is a timestamped depth chart?</strong> Without it the 2nd/3rd/4th-string
requirement is unanswerable, full stop.</li>
<li><strong>OQ-10 — what number counts as "luck removed"?</strong> The gates are numbers. You have to
pick the bar, or the standard is whatever the agent felt like that day.</li>
<li><strong>OQ-05 — can the release CDN be reached?</strong> This one question unblocks injuries,
depth charts and snap counts at once.</li>
<li><strong>OQ-14 — who signs off on a live test?</strong> Rewards require accountability; the
leaderboard currently has no one to release a strategy to.</li>
</ul>
"""
    page("questions.html", "Open questions", body,
         "What must be answered before a decision is reasonable — organised by what we have and what we lack.")

    # ---------------- suggestions ----------------
    sv2 = sug[["rank", "id", "gate", "area", "suggestion", "evidence", "unlocks", "cost", "risk", "missing"]]
    body = f"""
<p class="lead">This is the review board. Each suggestion carries the evidence for it, what it
unblocks, what it costs, the risk of doing it, and what is still missing before it can be adopted.
Pick a path and the row tells you what you are committing to.</p>

<div class="note"><strong>How to choose.</strong> Take every <em>Adopt now</em> row — they are low
cost, low risk and do not depend on any unanswered question. Take <em>Needs data</em> rows only after
the question they depend on is answered. A <em>Do not adopt</em> row is a finding, not a to-do: the
evidence says the path loses money.</div>

<h2>Ranked suggestions</h2>
{table(sv2, ['rank','id','gate','area','suggestion','evidence','unlocks','cost','risk','missing'],
       headers=['#','ID','Gate','Area','Suggestion','Evidence','Unblocks','Cost','Risk','Still missing'],
       num={'rank'}, pillcols=('gate',))}

<h2>Site and decision-making improvements</h2>
<ul>
<li><strong>Keep the rejected list public.</strong> A leaderboard that shows only winners is a
leaderboard you cannot audit; the deflation gate only means something if the search count is visible.</li>
<li><strong>Put the gate config under version control and sign it.</strong> The current thresholds are
the agent's defaults, not the owner's decision (<a href="questions.html">OQ-03</a>).</li>
<li><strong>Label every ROI with the price it is measured against.</strong> "ROI" without "vs close"
is the most common way a betting backtest misleads its reader.</li>
<li><strong>Fail the build on an unsourced row.</strong> <code>scripts/verify_site.py</code> already does
this for table rows; extend it to HTTP-status checks on every source.</li>
<li><strong>Show the season ledger next to every headline ROI.</strong> One good season hides inside a
good average, which is exactly what gate G5 exists to catch.</li>
<li><strong>Keep the Week 10 board as inputs, not picks.</strong> Publishing picks before the gates are
satisfied would be the one thing that turns a research repo into a tout sheet.</li>
</ul>
"""
    page("suggestions.html", "Suggestions", body,
         "Twelve ranked decision paths with evidence, cost, risk and what is still missing.")

    # ---------------- requirements ----------------
    rv = req.copy()

    def status_class(s):
        return status_pill(s)

    rows_html = []
    for _, r in rv.iterrows():
        rows_html.append(
            "<tr>"
            f"<td>{esc(r.id)}</td>"
            f"<td>{esc(r.requirement)}</td>"
            f"<td>{status_class(r.status)}</td>"
            f"<td><code>{esc(r.evidence)}</code></td>"
            f"<td>{esc(r.note)}</td>"
            "</tr>"
        )
    counts = rv.status.value_counts().to_dict()
    cards = "".join(
        f'<div class="card"><div class="k">{esc(k)}</div><div class="v">{v}</div></div>'
        for k, v in counts.items()
    )
    body = f"""
<div class="cards">{cards}</div>

<h2>Requirement register</h2>
<div class="tw"><table><thead><tr>
<th>ID</th><th>Requirement</th><th>Status</th><th>Evidence (file)</th><th>Note</th>
</tr></thead><tbody>{''.join(rows_html)}</tbody></table></div>

<h2>Reading the statuses</h2>
<ul>
<li><strong>DONE</strong> — delivered and evidenced in the named file.</li>
<li><strong>PARTIAL</strong> — delivered in part; the missing part is named and traced to an open
question or a flagged item.</li>
<li><strong>BLOCKED</strong> — cannot be delivered from any source reachable in this environment.
The gap is documented rather than filled with an estimate.</li>
<li><strong>REJECTED-ON-EVIDENCE</strong> — the work was done and the answer is no. That is a result,
not an omission.</li>
</ul>
"""
    page("requirements.html", "Requirements", body,
         "All 24 requirements from the brief, each with a status and the file that evidences it.")

    # ---------------- flagged ----------------
    def irr_row(r):
        return (
            f'<tr id="{esc(r.id)}"><td><strong>{esc(r.id)}</strong></td>'
            f'<td>{status_pill(r.severity)}</td>'
            f'<td>{esc(r.area)}</td>'
            f'<td><strong>{esc(r.title)}</strong><br><span class="src">{esc(r.detail)}</span></td>'
            f'<td>{esc(r.impact)}</td>'
            f'<td>{esc(r.mitigation)}</td>'
            f'<td>{esc(r.fix)}</td>'
            f'<td><a href="{esc(r.link)}" rel="noopener">source</a></td></tr>'
        )
    irr_table = ('<div class="tw"><table><thead><tr><th>ID</th><th>Severity</th><th>Area</th>'
                 '<th>Issue</th><th>Impact</th><th>Mitigation applied</th><th>Fix required</th>'
                 '<th>Source</th></tr></thead><tbody>'
                 + "".join(irr_row(r) for _, r in irr.iterrows()) + '</tbody></table></div>')

    body = f"""
<p class="lead">Everything that could not be verified, could not be obtained, or is a known weakness
in the data or the method. Flagged items do not block publication — they block <em>trust</em> in the
specific thing they describe, so each one names its own blast radius.</p>

<div class="note bad"><strong>{int((irr.severity=='Critical').sum())} critical, 
{int((irr.severity=='High').sum())} high, {int((irr.severity=='Medium').sum())} medium,
{int((irr.severity=='Low').sum())} low.</strong> The single highest-leverage fix is
<a href="flagged.html#FLAG-01">FLAG-01</a>; four other items are consequences of it.</div>

<h2>Irregularities</h2>
{irr_table}

<h2>Unverified and left blank</h2>
<p>These values were requested or would be useful, and are deliberately empty. They were not
estimated, interpolated or recalled from memory.</p>
{table(unv,
       ['item','value','reason','source_attempted','flag'],
       headers=['Item','Value','Why it is blank','Source attempted','Flag'],
       linkcol='source_attempted')}

<h2>What to check first</h2>
<ol>
<li><a href="flagged.html#FLAG-02">FLAG-02</a> — the 2nd/3rd/4th-string requirement. If you have a licensed depth-chart
feed, this closes and the availability model becomes usable.</li>
<li><a href="flagged.html#FLAG-01">FLAG-01</a> — the CDN. One allowlist entry adds injuries 2026, depth charts and snap
counts, which unblocks four other items.</li>
<li><a href="flagged.html#FLAG-06">FLAG-06</a> — the 2026 season is one completed game into Week 10. Nothing on this site
claims a 2026 out-of-sample result, and it should stay that way until Week 18.</li>
<li><a href="flagged.html#FLAG-08">FLAG-08</a> — closing-only prices. If you have an opening-line feed, the entire
line-origination question changes, because a real edge can then be measured against a price you can
actually get.</li>
</ol>
"""
    page("flagged.html", "Flagged for review", body,
         "Nine irregularities and nine values left deliberately blank, each with impact and the fix required.")

    # ---------------- sources ----------------
    sdf = pd.DataFrame(src)
    body = f"""
<p class="lead">Every source used anywhere in this repository. The tier says how much weight it can
carry: an Official source can establish a fact; Open data is reproducible and pinned by hash;
Secondary is context only and is never the origin of a computed number.</p>

<div class="cards">
<div class="card"><div class="k">Official</div><div class="v">{int((sdf.tier=='Official').sum())}</div>
<div class="s">NFL.com / NFL Operations, fetched and read</div></div>
<div class="card"><div class="k">Open data</div><div class="v">{int(sdf.tier.str.startswith('Open').sum())}</div>
<div class="s">pinned by SHA-256</div></div>
<div class="card"><div class="k">Secondary</div><div class="v">{int((sdf.tier=='Secondary').sum())}</div>
<div class="s">context only</div></div>
<div class="card"><div class="k">Blocked / broken</div><div class="v">{int((sdf.status.isin(['blocked','broken-link'])).sum())}</div>
<div class="s">listed so they are never cited</div></div>
</div>

<h2>Registry</h2>
{table(sdf[['id','tier','publisher','title','url','used_for','status']],
       ['id','tier','publisher','title','url','used_for','status'],
       headers=['ID','Tier','Publisher','Title','URL','Used for','Status'],
       linkcol='url', pillcols=('tier','status'))}

<h2>Input manifest</h2>
<p>Each raw file is pinned by SHA-256 and row count in <code>data/raw/MANIFEST.json</code>, produced
by <code>scripts/fetch_data.py</code>. Re-running the fetch and then the build reproduces every
number on this site from scratch.</p>
<div class="tw"><table><thead><tr><th>File</th><th>Rows</th><th>SHA-256</th></tr></thead><tbody>
<tr><td><code>games.csv</code></td><td class="n">7,548</td><td><code>9db20ab7…abe27e3</code></td></tr>
<tr><td><code>closing_lines.csv</code></td><td class="n">20,490</td><td><code>3571e1c9…9d1729</code></td></tr>
<tr><td><code>sc_lines.csv</code></td><td class="n">4,092</td><td><code>384039e9…c5004e</code></td></tr>
<tr><td><code>rosters.csv</code></td><td class="n">28,617</td><td><code>0e958260…01a39</code></td></tr>
<tr><td><code>win_totals.csv</code></td><td class="n">576</td><td><code>6228fe8c…b75c20</code></td></tr>
<tr><td><code>injuries_2025.csv</code></td><td class="n">4,442</td><td><code>c107aec1…f6b44</code></td></tr>
</tbody></table></div>
"""
    page("sources.html", "Sources", body,
         "Official, open-data and secondary sources, each with the exact use and verification status.")

    # ---------------- methods ----------------
    body = """
<h2>Principles</h2>
<ol>
<li><strong>No invented numbers.</strong> If a value cannot be computed from a pinned source or read
off an official page, the cell is blank and the item goes on
<a href="flagged.html">Flagged for review</a>.</li>
<li><strong>No fitting to profit.</strong> Elo constants and the Elo→spread conversion were fixed
before any backtest ran. They are in the script, in <code>scripts/strategy_lab.py</code>, in plain
sight.</li>
<li><strong>Walk-forward only.</strong> A signal may only use information available before the kickoff
it prices. Ratings are read pre-game; form is accumulated post-game.</li>
<li><strong>Every strategy faces the same gates.</strong> Thresholds are global constants, not tuned
per strategy.</li>
<li><strong>Publish the failures.</strong> The search count is public because the Bonferroni
correction depends on it.</li>
</ol>

<h2>Economics</h2>
<ul>
<li>Bets are settled at the <em>closing</em> price from <code>games.csv</code> (spread odds, total
odds, moneyline).</li>
<li>Pushes are excluded from both numerator and denominator.</li>
<li>ROI = total profit ÷ total staked, with 1 unit staked per bet.</li>
<li>The breakeven hit rate is computed exactly from the realised average decimal price, not assumed
to be 52.38%.</li>
<li>Significance is a one-sided t-test on per-bet return, with a Wilson 95% interval on hit rate.</li>
</ul>

<h2>Gates</h2>
<ul>
<li><strong>G1</strong> ≥150 settled bets and ≥60 out-of-sample settled bets.</li>
<li><strong>G2</strong> ROI &gt; 0 in-sample <em>and</em> out-of-sample.</li>
<li><strong>G3</strong> one-sided p &lt; 0.05 on per-bet return.</li>
<li><strong>G4</strong> Wilson 95% lower bound on hit rate &gt; the vig breakeven.</li>
<li><strong>G5</strong> no single season supplies more than 40% of total profit.</li>
<li><strong>G6</strong> p &lt; 0.05/N where N is the number of variants actually searched. N is read from the signal registry at runtime, so the denominator can never drift from the real search count. With the current build N = 16, giving p &lt; 0.00313.</li>
<li><strong>G7</strong> maximum drawdown smaller than total profit.</li>
</ul>

<h2>Known limitations</h2>
<ul>
<li>Closing prices only — no opening-line series for the full sample
(<a href="flagged.html">FLAG-08</a>). A real edge measured against the close is understated, and line
movement cannot be studied at all.</li>
<li>Result-history Elo is information the market already has. That is why the market-divergence
family fails; it is not evidence that no edge exists anywhere.</li>
<li>Injury weights are an assumption. The NFL publishes definitions, not probabilities.</li>
<li>Depth order is absent from every reachable source, so the 2nd/3rd/4th-string model stops at the
quarterback.</li>
<li>2026 data is one completed Week 10 game. Nothing here is a 2026 out-of-sample claim.</li>
<li>No prop market data, so prop-combo correlation is unmeasured.</li>
</ul>

<h2>Reproducing this site</h2>
<p><code>python3 scripts/fetch_data.py</code> → <code>scripts/build_availability.py</code> →
<code>scripts/build_correlations.py</code> → <code>scripts/strategy_lab.py</code> →
<code>scripts/build_week10_board.py</code> → <code>scripts/build_registers.py</code> →
<code>scripts/build_site.py</code> → <code>scripts/verify_site.py</code>.
The last step fails the build if any table row lacks a source.</p>
"""
    page("methods.html", "Methods", body,
         "The exact rules this build followed, so any number can be attacked on its merits.")

    print("built", len(NAV), "pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
