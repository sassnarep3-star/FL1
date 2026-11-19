#!/usr/bin/env python3
"""pages_controls.py — renders controls.html (K1 / R76, session arena/9fccbb0e-fl1).

A renderer and nothing else. Every number is read from artefacts that scripts/strategy_lab.py
writes (data/controls.csv, data/controls.json, data/leaderboard.csv). Nothing is recomputed here,
and a cell whose artefact value is empty renders as the site's marked em dash, never as zero.

Called from tools/site.py's main(), which owns the page shell (page(), table(), cell(), src_link()).
"""

import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build  # noqa: E402  (shared loaders)

FILENAME = "controls.html"
NFLVERSE_URL = "https://github.com/nflverse/nfldata/blob/master/data/games.csv"
CODE_BASE = "https://github.com/sassnarep3-star/FL1/blob/main/"


def _host_module():
    """The module that renders the shell: tools/site.py however it was loaded (see pages_market)."""
    for name in ("__main__", "site", "tools.site"):
        m = sys.modules.get(name)
        if m is not None and hasattr(m, "page") and hasattr(m, "src_link"):
            return m
    raise SystemExit("pages_controls.py must be called from tools/site.py")


def _read_csv(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _fmt(v, nd=4):
    if v is None or str(v).strip() == "":
        return None
    try:
        return f"{float(v):.{nd}f}"
    except ValueError:
        return str(v)


def _pct(v):
    if v is None or str(v).strip() == "":
        return None
    return f"{float(v) * 100:+.2f}%"


def render_all():
    site = _host_module()
    sources = {s["id"]: s for s in build.load("sources.tsv")}
    with open(os.path.join(ROOT, "data", "controls.json"), encoding="utf-8") as fh:
        meta = json.load(fh)
    controls = _read_csv("controls.csv")
    lb = {r["strategy_id"]: r for r in _read_csv("leaderboard.csv")}

    feed_chip = site.src_link("S47", sources)
    feed_link = ('<a href="%s">nflverse games.csv (third-party, not official)</a>' % NFLVERSE_URL)
    src_cell = site.raw_src(feed_chip + " " + feed_link)

    # ----- table A: the controls that K1 scores
    rows = []
    for c in controls:
        br = c["brier_oos"]
        ci = ("—" if not br else "%s to %s" % (_fmt(c["brier_ci_low"], 4), _fmt(c["brier_ci_high"], 4)))
        rows.append([
            site.cell(c["control_id"]),
            site.cell(c["rule"]),
            site.cell(_fmt(c["forecast_p"], 4) or ""),
            site.cell(c["oos_settled"], "n"),
            site.cell(_fmt(c["oos_hit_rate"], 4) or ""),
            site.cell(_pct(c["oos_roi"]) or ""),
            site.cell(_fmt(br, 4) or ""),
            site.cell(ci),
            site.cell(_fmt(c["brier_minus_coinflip"], 6) or ""),
            src_cell,
        ])
    # reference row: the market control already on the leaderboard (not scored by Brier here)
    mk = lb.get("__CONTROL_MARKET")
    if mk:
        rows.append([
            site.cell("__CONTROL_MARKET (reference)"),
            site.cell(mk["description"]),
            site.cell(""),
            site.cell(mk["oos_settled"], "n"),
            site.cell(_fmt(mk["hit_rate"], 4) or ""),
            site.cell(_pct(mk["oos_roi"]) or ""),
            site.cell(""),
            site.cell(""),
            site.cell(""),
            src_cell,
        ])
    table_a = site.table(
        ["Control", "Rule", "Forecast p", "OOS settled (n)", "OOS hit rate", "OOS ROI",
         "Brier (OOS)", "95% interval", "Brier − 0.25", "Source"],
        rows, cls="",
        caption=("Out-of-sample seasons %s. Brier is the proper score of a probability forecast "
                 "(lower is better; 0.25 is the uninformed coin flip). Blank = not computed here, "
                 "shown as — and not as zero." % (controls[0]["oos_seasons"] if controls else "—")))

    # ----- table B: candidates (every strategy on the leaderboard)
    cand_rows = []
    for sid, r in lb.items():
        if sid.startswith("__CONTROL"):
            continue
        cand_rows.append([
            site.cell(sid),
            site.cell(r["family"]),
            site.cell(r["market"]),
            site.cell(r["oos_settled"], "n"),
            site.cell(_pct(r["oos_roi"]) or ""),
            site.cell(""),
            site.cell("NOT EVALUABLE — no per-bet probability is stored (R35)"),
            src_cell,
        ])
    table_b = site.table(
        ["Strategy", "Family", "Market", "OOS settled (n)", "OOS ROI", "Brier (OOS)",
         "Beats RANDOM and FAVOURITE on Brier?", "Source"],
        cand_rows, cls="",
        caption=("A candidate can only be ranked against the controls on the same proper score. "
                 "No candidate stores a per-bet probability, so no candidate has a Brier score and "
                 "none can yet pass the gate. The ROI column is shown for context only and is not a "
                 "ranking key (R84, R57)."))

    body = """
<section id="controls">
  <h1>Control baselines</h1>
  <p class="lede">Every leaderboard run now carries three yardsticks that need no insight:
  <strong>random picks</strong> (fixed seed %(seed)s), <strong>favourites only</strong>, and the
  original <strong>bet every home team</strong> control that measures the house margin.
  A strategy has to beat both the random and the favourites controls on the same proper score
  before it can be called skill. Right now that comparison cannot be made for any candidate.</p>
  <div class="note">
    <p><strong>Status:</strong> the two new controls are computed, scored and published in
    <code>data/controls.csv</code>. <strong>Candidates scored: %(scored)d of 15.</strong>
    Reason: candidate strategies store a bet and its result, not the probability they assigned to it
    (requirement R35). Until that exists, the statement &ldquo;beats both controls&rdquo; is
    NOT EVALUABLE, not passed.</p>
    <p><strong>Data:</strong> these controls use the third-party nflverse games feed (S47), which
    is not an official NFL source. They are flagged, and the values are not presented as official.
    <a href="flagged.html">See Flagged for Review</a>.</p>
  </div>
  <h2>1. Control rows</h2>
  %(table_a)s
  <h2>2. Candidate strategies against the controls</h2>
  %(table_b)s
  <h2>3. How the controls are defined</h2>
  <ul>
    <li><strong>Random:</strong> one side per game, drawn with Python&rsquo;s <code>random.Random(20261119)</code>
    (stable across Python releases). Forecast p = 0.5 for the side it picked, so its Brier score is
    0.25 by construction. Its hit rate and ROI are the realised check.</li>
    <li><strong>Favourites only:</strong> always the side the market favours. Forecast p = that
    favourite&rsquo;s cover rate on the training seasons %(train)s only (fixed before the out-of-sample
    games are scored, so the control never sees its own test data).</li>
    <li><strong>Sign convention (verified, not assumed):</strong> in this feed, <code>spread_line &gt; 0</code>
    means the <em>home</em> side is the favourite. The home team is the moneyline favourite in
    99.4%% of 5,198 regular-season games with both prices, and the home margin correlates +0.43 with
    the positive spread. The repository&rsquo;s line-board label &ldquo;negative = home favourite&rdquo;
    contradicts this and is logged as an irregularity (<a href="flagged.html#F73">F73</a>).</li>
    <li><strong>Brier interval:</strong> mean &plusmn; 1.96 standard errors, one bet per game, so the
    game is the unit. Pushes are excluded, as on every other row.</li>
  </ul>
  <p>Code: <a href="%(code)sengine/controls.py">engine/controls.py</a>,
  <a href="%(code)sscripts/strategy_lab.py">scripts/strategy_lab.py</a>,
  tests <a href="%(code)stests/test_controls_k1.py">tests/test_controls_k1.py</a>.
  Pre-registration: the seed, the favourite rule and the split are fixed in the code, the
  claim in COORDINATION.md (K1) and this page. Changing any of them creates a new control.</p>
</section>
""" % {
        "seed": "20261119",
        "scored": int(meta["candidates_scored"]),
        "train": (controls[1]["train_seasons"] if len(controls) > 1 else "2006–2019"),
        "table_a": table_a,
        "table_b": table_b,
        "code": CODE_BASE,
    }
    site.page(FILENAME, "Control Baselines", body)
    return [FILENAME]


def main():
    for name in render_all():
        print("  " + name)


if __name__ == "__main__":
    main()
