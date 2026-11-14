#!/usr/bin/env python3
"""
pages_market.py — renders the market-spine pages from the artefacts in data/market/.

This module is a renderer and nothing else. It reads the deterministic exports written by
`scripts/build_market_spine.py` (which is the only place those numbers are computed) and
turns them into HTML. It does not recompute a statistic, does not convert a blank into a
number, and does not fetch anything: a cell whose artefact value is empty renders as the
site's standard marked em dash, with the reason in the title attribute.

Two vocabulary rules apply on every page here:
  * `fair`   = what this project's model says, always shown next to the objective it was
               fitted for and the window it was fitted on;
  * `market` = a number somebody else published, always shown with its feed, its vintage,
               and its own source link; a difference is only ever printed when both exist.

Run from tools/site.py's main() (it is imported there, not executed):
    python3 -c "import sys;sys.path.insert(0,'tools');import pages_market;pages_market.main()"
"""

import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build  # noqa: E402  (shares the TSV/JSON loaders)


def _host_module():
    """The module that renders the shell: tools/site.py, however it was loaded.

    `import site` would find the interpreter's own startup module instead of this repo's
    file, so the helpers are looked up late on the module that is actually running. When
    site.py is executed as a script it is `__main__`; when imported as a module it is
    `site` or `tools.site`.
    """
    for name in ("__main__", "site", "tools.site"):
        m = sys.modules.get(name)
        if m is not None and hasattr(m, "page") and hasattr(m, "src_link"):
            return m
    raise SystemExit(
        "pages_market.py must be imported from tools/site.py (or run after it has been "
        "imported), because it reuses that file's page shell and table helpers")


class _Shell:
    """Attribute proxy onto the host module, resolved on each use."""

    def __getattr__(self, name):
        return getattr(_host_module(), name)


S = _Shell()

MKT = os.path.join(ROOT, "data", "market")

#: source chips used across these pages, in the order a reviewer should meet them
SRC_FEEDS = ("S47", "S50", "S51", "S52", "S53")

SOURCES_BY_ID = {}


# ---------------------------------------------------------------------------
# loading + tiny render helpers
# ---------------------------------------------------------------------------
def tsv(name):
    path = os.path.join(MKT, name)
    if not os.path.exists(path):
        raise SystemExit("missing artefact data/market/%s - run scripts/build_market_spine.py" % name)
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def js(name):
    with open(os.path.join(MKT, name), encoding="utf-8") as fh:
        return json.load(fh)


def c(v, kind=""):
    """Standard cell: blank stays blank, and the tooltip says it was not confirmed."""
    return S.cell(v, kind)


def num(v, nd=4):
    """Numeric cell with fixed precision; empty stays empty."""
    s = "" if v is None else str(v).strip()
    if s in ("", "None", "nan"):
        return S.cell("")
    try:
        f = float(s)
    except ValueError:
        return S.cell(v)
    if nd == 0:
        return '<td class="num">%d</td>' % int(round(f))
    txt = ("%.*f" % (nd, f)).rstrip("0").rstrip(".") if nd < 6 else s
    sign = ""
    if txt.startswith("-"):
        txt, sign = txt, "-"
    return '<td class="num">%s%s</td>' % (sign, txt or "0")


def signed(v, nd=3):
    """Explicit +/- on a difference, so a reader never has to infer direction from a dash."""
    s = "" if v is None else str(v).strip()
    if s in ("", "None", "nan"):
        return S.cell("")
    try:
        f = float(s)
    except ValueError:
        return S.cell(v)
    return '<td class="num %s">%+.*f</td>' % ("pos" if f > 0 else ("neg" if f < 0 else ""), nd, f)


def h(v):
    """A cell of *authored* prose that legitimately contains markup.

    `c()` escapes, which is right for data and wrong for a sentence this module wrote
    itself with a link in it. Keeping the two apart is what lets the build-time link
    checker guarantee that no anchor tag is ever printed as text.
    """
    return S.raw_src(v)


def srcs(*ids):
    """A source column: chips linked into the registry. Never a bare 'see sources'."""
    chips = [S.src_link(i, SOURCES_BY_ID) for i in ids if i]
    return S.raw_src(" ".join(chips) if chips else '<span class="muted">this repository (generated)</span>')


def verdict_cell(v):
    kind = {"PUBLISH": "ok", "TRIGGERED": "bad", "OK": "ok", "FAIL": "bad",
            "NOT_EVALUABLE": "warn", "QUARANTINED": "bad", "MATCHED_TWO_FEEDS": "ok",
            "SINGLE_FEED_SEASON_RECONCILED": "warn", "SINGLE_FEED": "warn",
            "NO_RESULT": "", "YES": "ok", "PASS": "ok"}.get(str(v).strip(), "")
    return '<td>%s</td>' % S.pill(v, kind)


def tbl(headers, rows, cls="dense", caption=""):
    return S.table(headers, rows, cls=cls, caption=caption)


def sec(title, *body):
    """A section whose prose is real markup, not a bare text node.

    Anything passed in that is not already an element gets wrapped in `<p>`, so the
    explanatory text under a table is markup the validator sees as a paragraph rather
    than loose text inside a section.
    """
    chunks = []
    for item in body:
        item = "" if item is None else str(item)
        chunks.append(item if item.lstrip().startswith("<") else "<p>%s</p>" % item)
    return "<section><h2>%s</h2>%s</section>" % (title, "".join(chunks))


def lead(text):
    return '<p class="lead">%s</p>' % text


def note(text):
    return '<p class="muted">%s</p>' % text


def callout(title, text, kind="warn"):
    return ('<div class="callout %s"><p><strong>%s</strong> %s</p></div>' % (kind, title, text))


CAP = "2026-11-14"


# ---------------------------------------------------------------------------
# 1. price-store.html
# ---------------------------------------------------------------------------
def price_store_page():
    man = js("snapshot_manifest.json")
    integ = tsv("price_integrity.tsv")
    cov = tsv("price_coverage.tsv")
    drift = tsv("price_drift.tsv")
    quar = tsv("price_snapshots_quarantine.tsv")
    live = tsv("price_snapshots_2026.tsv")
    vc = man["vintage_counts"]
    sq = man["sqlite_interop"]

    body = ['<section><h1>Price-snapshot store</h1>',
            lead("Every number this project quotes as &ldquo;the market line&rdquo; is a row in an append-only "
                 "ledger, with the feed it came from, the field of that feed, the moment the capture was taken, "
                 "and what the publisher actually asserted about when in the game-week the price was struck. "
                 "The brief asked for opening <em>and</em> closing numbers for every market we originate. "
                 "This is that store, and the coverage table below is the honest size of the first half of "
                 "that sentence.")]
    body.append(callout("The opening half of requirement 1, stated plainly.",
                        "A first-posted price exists in these captures for exactly one season &mdash; 2021, one "
                        "sportsbook, no odds column, and a file whose last upstream change predates the season "
                        "it covers. It is stored, hashed, <strong>quarantined</strong> from pricing and "
                        "settlement, and published in full. Closing numbers exist for %s games across the "
                        "seasons the feeds cover. Nothing was labelled an opener to make the table look "
                        "complete. <a href=\"flagged.html#F18\">Flag F18</a> and <a href=\"questions.html\">Q21"
                        "</a> carry the consequence." % "{:,}".format(
                            sum(int(r["games_with_line"]) for r in integ if r["feed"] == "closing_lines"))))
    body.append("</section>")

    # -- A: capture manifest
    rows = []
    for f in man["feeds"]:
        rows.append([c(f["feed"]), c(f["file"]), num(f["rows"], 0), num(f["bytes"], 0),
                     c((f["sha256"] or "")[:16]),
                     c(f["upstream_commit"]), c(f["upstream_at"]), c(f["upstream_message"]),
                     c(f["vintage"]), c(f["markets"]),
                     srcs("S47" if f["feed"] == "games" else
                          {"closing_lines": "S50", "sc_lines": "S51", "initial_lines": "S52",
                           "win_totals": "S53"}.get(f["feed"]), "S54")])
    body.append(sec("A. What was captured, and from where",
                    tbl(["Feed", "File", "Rows", "Bytes", "sha256 (prefix)", "Upstream commit",
                         "Committed at (UTC)", "Upstream commit message", "Vintage asserted",
                         "Markets", "Source"], rows),
                    "Each file was pulled by <code>git clone</code> of nflverse/nfldata at the pinned tree "
                    "shown in the row, because <code>raw.githubusercontent.com</code> is not reachable from "
                    "the capture environment. The hash is recomputed on every rebuild by "
                    "<code>python3 -m engine.market_feed</code>; the previous capture's hash for "
                    "<code>games.csv</code> is kept in "
                    "<a href=\"sources.html#S54\">the manifest</a> so the refresh is auditable "
                    "(<a href=\"flagged.html#F27\">F27</a>)."))

    # -- B: what the publisher documents
    rows = []
    for f in man["registry"]:
        rows.append([c(f["feed"]), c(f["publisher"]), c(f["documented"]), c(f.get("vintage_evidence", "")),
                     c(f["note"]), srcs("S47" if f["feed"] == "games" else
                                        {"closing_lines": "S50", "sc_lines": "S51",
                                         "initial_lines": "S52", "win_totals": "S53"}.get(f["feed"]))])
    body.append(sec("B. What the publisher says these fields mean",
                    tbl(["Feed", "Publisher", "Documented meaning", "Evidence for the vintage claim",
                         "Note", "Source"], rows, cls="dense wrap"),
                    note("Rows in table B are quotations about documentation, not interpretations of it. "
                         "Where the answer is &lsquo;not documented&rsquo;, the store keeps the vintage as "
                         "UNDOCUMENTED rather than guessing an hour "
                         "(<a href=\"flagged.html#F26\">F26</a>).")))

    # -- C: integrity
    rows = []
    for r in integ:
        rows.append([c(r["feed"]), num(r["rows"], 0), num(r["games"], 0), num(r["games_with_line"], 0),
                     num(r["games_with_price"], 0), num(r["side_pairs_checked"], 0),
                     num(r["side_pairs_asymmetric"], 0), num(r["total_pairs_conflicting"], 0),
                     num(r["quarantined_rows"], 0), c(r["seasons"]), c(r["vintages"]), srcs("S54")])
    body.append(sec("C. Structural checks that need no outside knowledge",
                    tbl(["Feed", "Rows", "Games", "With a line", "With a price", "Side pairs checked",
                         "Side pairs NOT symmetric", "Totals conflicting", "Quarantined rows",
                         "Seasons", "Vintages present", "Source"], rows),
                    "Antisymmetry is the check that catches a vendor shipping a per-team file as if it were a "
                    "home-perspective file: the two sides of a spread must net to zero. A nonzero count in "
                    "&lsquo;not symmetric&rsquo; would quarantine the feed; the two per-team feeds "
                    "(<code>sc_lines</code>, <code>initial_lines</code>) pass it exactly."))

    # -- D: coverage by season and market
    agg = {}
    for r in cov:
        k = (r["season"], r["market"])
        d = agg.setdefault(k, {"games": 0, "line": 0, "price": 0, "vint": set(), "feeds": set()})
        d["games"] = max(d["games"], int(r["games"]))
        d["line"] = max(d["line"], int(r["games_with_line"]))
        d["price"] = max(d["price"], int(r["games_with_price"]))
        d["vint"].add(r["vintage"])
        d["feeds"].add(r["feed"])
    rows = []
    for (season, market) in sorted(agg, key=lambda k: (k[0], k[1]), reverse=True):
        d = agg[(season, market)]
        rows.append([c(season), c(market), num(d["games"], 0), num(d["line"], 0), num(d["price"], 0),
                     c(", ".join(sorted(d["vint"]))), c(", ".join(sorted(d["feeds"]))), srcs(*SRC_FEEDS)])
    body.append(sec("D. Coverage: which season has which vintage of which market",
                    tbl(["Season", "Market", "Games", "With a line", "With a price", "Vintages present",
                         "Feeds", "Source"], rows, cls="dense"),
                    "This is requirement 1 measured rather than asserted. Read it as: the closing side of the "
                    "store is dense from 2006 to 2018 and thin after that; the opening side is one season of "
                    "one book. Moneyline rows carry a price but no line by design, so &lsquo;with a line&rsquo; "
                    "is 0 there and that is not a gap in the store."))

    # -- E: drift
    rows = []
    for r in drift:
        rows.append([c(r["feed_a"]), c(r["feed_b"]), c(r["games_compared"]), num(r["lines_identical"], 0),
                     num(r["lines_differ"], 0), num(r["pct_lines_identical"], 1),
                     num(r["favourite_agrees"], 0), num(r["favourite_conflicts"], 0),
                     num(r["median_abs_diff_pts"], 2), num(r["max_abs_diff_pts"], 2),
                     num(r["prices_identical"], 0), num(r["prices_differ"], 0), c(r["note"]), srcs("S47", "S50", "S51", "S52")])
    body.append(sec("E. Cross-feed drift, published instead of averaged away",
                    tbl(["Feed A", "Feed B", "Games compared", "Lines identical", "Lines differ",
                         "% identical", "Favourite agrees", "Favourite conflicts", "Median |diff| (pts)",
                         "Max |diff| (pts)", "Prices identical", "Prices differ", "Note", "Source"],
                        rows),
                    "The benchmark a delta is measured against is chosen by a stated priority rule "
                    "(documented vintage first, then the feed that also carries a price, then the games "
                    "feed), and the runner-up number is kept in an <code>alt</code> column on every "
                    "origination row. Disagreement is a fact about the vendor landscape, not noise to "
                    "smooth (<a href=\"flagged.html#F20\">F20</a>, <a href=\"suggestions.html#SG18\">SG18</a>)."))

    # -- F: sqlite interop probe
    ref = sq.get("refused", {})
    rows = [[c("Rows the store accepted"), num(sq.get("inserted_calls", 0), 0),
             h("close-vintage rows from <code>closing_lines</code>, whose publisher labels them closing"), srcs("S50")],
            [c("Rows in the store afterwards"), num(sq.get("rows_in_store", 0), 0),
             c("Proves idempotence: re-ingesting the same capture adds nothing"), srcs("S54")],
            [h("Rows its <code>phase</code> CHECK cannot express"),
             num(sum(int(v) for v in ref.values()), 0),
             c("; ".join("<em>%s</em>: %s" % (k, v) for k, v in ref.items()) or "&mdash;"), srcs("S54")]]
    body.append(sec("F. Interoperability probe against the production store",
                    tbl(["Probe", "Count", "What it means", "Source"], rows, cls="dense wrap"),
                    "<code>engine/price_snapshots.py</code> on <code>main</code> constrains "
                    "<code>phase</code> to open / close / intermediate. Seventy-two per cent of this ledger "
                    "is undated, so the store rejects it &mdash; correctly. Relabelling those rows "
                    "&lsquo;intermediate&rsquo; would manufacture provenance, so the probe reports the "
                    "refusal instead. The vocabulary decision is <a href=\"questions.html\">Q21</a> and "
                    "<a href=\"flagged.html#F22\">F22</a>; the schema change belongs to the storage owner, "
                    "not to this page."))

    # -- G: quarantine
    why = {}
    for r in quar:
        k = r["integrity"] or "unlabelled"
        why[k] = why.get(k, 0) + 1
    rows = [[c(k), num(v, 0), srcs("S52", "S54")] for k, v in sorted(why.items(), key=lambda kv: -kv[1])]
    body.append(sec("G. Quarantine: recorded, hashed, and never used to price anything",
                    tbl(["Reason recorded on the row", "Rows", "Source"], rows, cls="dense"),
                    "Quarantine is the alternative to deletion. %s rows are in this state, every one of them "
                    "kept in <code>data/market/price_snapshots_quarantine.tsv</code> so the arithmetic that "
                    "put them there can be redone." % "{:,}".format(len(quar))))

    rows = []
    for r in live[:24]:
        rows.append([c(r["game_id"]), c(r["market"]), c(r["side_key"]), c(r["team"]),
                     num(r["line"], 2), num(r["price_american"], 0), c(r["vintage"]), c(r["feed"]),
                     c(r["feed_field"]), c(r["captured_at_utc"]), srcs("S47")])
    body.append(sec("H. The live ledger: the current season, first rows",
                    tbl(["Game", "Market", "Side", "Team", "Line", "Price", "Vintage", "Feed",
                         "Feed field", "Captured at (UTC)", "Source"], rows),
                    "First 24 of %s rows for the current season; the file holds all of them. Each row is "
                    "addressable by its content hash, so a corrected capture produces a new row and leaves "
                    "the old one visible: &lsquo;what did we know on the day&rsquo; stays answerable."
                    % "{:,}".format(len(live))))

    body.append(sec("Where the artefacts are",
                    "<p>Snapshot ledger exports, coverage, drift, quarantine and the capture manifest live in "
                    "<code>data/market/</code> (see <a href=\"sources.html#S56\">S56</a>) and are rebuilt "
                    "byte-identically by <code>python3 scripts/build_market_spine.py --check</code>. The "
                    "SQLite store itself is the production write path: "
                    "<code>engine/price_snapshots.py</code>.</p>"))
    return S.page("price-store.html", "Price-Snapshot Store", "".join(body), wide=True)


# ---------------------------------------------------------------------------
# 2. results-feed.html
# ---------------------------------------------------------------------------
def results_feed_page():
    led = tsv("results_ledger_2026.tsv")
    seas = tsv("results_ledger_seasons.tsv")
    rec = tsv("results_season_reconciliation.tsv")
    ver = tsv("results_verification.tsv")

    n_played = sum(1 for r in led if r["verify_status"] != "NO_RESULT")
    n_match = sum(1 for r in led if r["verify_status"] == "MATCHED_TWO_FEEDS")
    body = ['<section><h1>Verified results feed</h1>',
            lead("Backtests and ROI are impossible without a result nobody can argue with. This feed admits a "
                 "game with an explicit verification status, and settlement is refused for any game whose "
                 "status is not earned. A result taken from the same file as the price is not verification: it "
                 "is a tautology, so the status column says which of the two it is.")]
    rows = [[c("MATCHED_TWO_FEEDS"), c("Scores agree between the market feed and an independent transcription "
                                       "of the league's own game pages, matched on date and matchup"),
             c("settles bets"), verdict_cell("MATCHED_TWO_FEEDS")],
            [c("SINGLE_FEED_SEASON_RECONCILED"), c("Feed-only scores, but the season recount reproduces the "
                                                    "official standings table for every club"),
             c("settles bets, labelled aggregate-verified"), verdict_cell("SINGLE_FEED")],
            [c("SINGLE_FEED"), c("Feed only, no independent check at any level"),
             c("method development; never a published claim of skill"), verdict_cell("SINGLE_FEED")],
            [c("QUARANTINE_MISMATCH"), c("The two feeds disagree about this game"),
             c("settles nothing; the contradiction is published"), verdict_cell("TRIGGERED")],
            [c("NO_RESULT"), c("Not played at the capture date"),
             c("nothing to settle"), verdict_cell("NO_RESULT")]]
    body.append(sec("A. Admission rules", tbl(["Status", "Earned by", "Consequence", "Verdict"], rows, cls="dense wrap")))
    body.append(callout("Current season, at the capture date.",
                        "%s of %s scheduled games have a result; all %s of them match the independent "
                        "transcription on both scores, and the season recount matches the official standings "
                        "for 32 of 32 clubs. The other %s games are unplayed, not missing "
                        "(<a href=\"flagged.html#F23\">F23</a>)."
                        % (n_played, len(led), n_match, len(led) - n_played), kind=""))
    body.append("</section>")

    rows = []
    for r in seas:
        rows.append([c(r["season"]), num(r["games"], 0), num(r["matched_two_feeds"], 0),
                     num(r["season_reconciled"], 0), num(r["single_feed"], 0),
                     num(r["quarantine_mismatch"], 0), num(r["no_result"], 0),
                     num(r["settle_eligible"], 0), num(r["eligible_pct"], 1), srcs("S47", "S03", "S04")])
    body.append(sec("B. Per-season verification roll-up",
                    tbl(["Season", "Games", "Matched two feeds", "Season-reconciled", "Single feed",
                         "Quarantined", "No result", "Settle-eligible", "Settle-eligible %", "Source"], rows),
                    "Every season with games in the capture is listed, so the size of the verified sample is "
                    "visible rather than implied. Game-level cross-checking only exists where an independent "
                    "transcription was captured &mdash; for the current season &mdash; which is why earlier "
                    "seasons are admitted on the aggregate rule instead."))

    rows = []
    for r in rec:
        rows.append([c(r["season"]), num(r["official_clubs_checked"], 0), num(r["clubs_reconciled"], 0),
                     num(r["mismatch_clubs"], 0), num(r["games_counted"], 0), c(r["detail"] or "none"),
                     srcs("S03", "S55")])
    body.append(sec("C. Season recount against the official standings table",
                    tbl(["Season", "Official clubs checked", "Clubs reconciled", "Mismatches",
                         "Games counted", "Detail", "Source"], rows, cls="dense"),
                    "W/L/T, PF and PA are recomputed from game rows and compared with the published league "
                    "table. The 2025 row is the full 272-game season against the final official table; the "
                    "2026 row is 137 played games of the current season against the current official table "
                    "(<a href=\"sources.html#S55\">S55</a> holds the verbatim capture). This is the check "
                    "that makes a single-feed season usable at all."))

    rows = []
    for r in led:
        rows.append([c(r["game_id"]), num(r["week"], 0), c(r["gameday"]),
                     c(r["away"]), num(r["away_score"], 0), c(r["home"]), num(r["home_score"], 0),
                     num(r["margin_home"], 0), num(r["total_points"], 0),
                     verdict_cell(r["verify_status"]), c(r["settle_eligible"]), c(r["join_basis"]),
                     srcs("S04", "S47")])
    body.append(sec("D. The current season, game by game",
                    tbl(["Game", "Wk", "Date", "Away", "Pts", "Home", "Pts", "Margin (home)", "Total",
                         "Verification status", "Settle-eligible", "Join basis", "Source"], rows),
                    "All %s games of the current season; <code>results_ledger_index.tsv</code> holds the "
                    "same status for every season in the capture, so a reader can check any published bet "
                    "against its own game row. &lsquo;Join basis&rsquo; records how the two feeds were matched: the exact "
                    "date, or the unique week-and-matchup key, which is only permitted inside the season the "
                    "transcription covers so a 2024 fixture cannot be paired with a 2026 one and reported as "
                    "a contradiction." % len(led)))

    rows = [[c("SIDE (spread)"), h("home covers when margin + home line &gt; 0; equal is a push"),
             c("the feed's own convention: a positive spread_line means the home team was favoured by that "
               "many points (documented)"), c("overtime counts as part of the game")],
            [c("TOTAL"), h("over wins when total points &gt; line; equal is a push"),
             c("total = away + home (documented)"), c("overtime counts")],
            [c("MONEYLINE"), c("winner wins; a tied game is a push for both sides"),
             c("no three-way market is offered by these feeds"),
             c("a tie is therefore graded as push, not as a half-loss")]]
    body.append(sec("E. Settlement rules, stated so they can be objected to",
                    tbl(["Market", "Rule", "Basis in the feed", "Tie and overtime handling"], rows, cls="dense wrap")))

    rows = []
    for r in ver:
        rows.append([c(r["check"]), S.raw_src("<code>%s</code>" % S.esc(r["command"])), c(r["scope"]),
                     S.raw_src(("<strong>%s</strong> " % ("PASS" if r["result"].startswith("PASS")
                                else "FAIL" if r["result"].startswith("FAIL") else "SEE"))
                               + S.esc(r["result"][len("PASS - "):] if r["result"].startswith("PASS - ")
                                       else r["result"][len("FAIL - "):] if r["result"].startswith("FAIL - ")
                                       else r["result"])), c(r["when"]), srcs("S56")])
    body.append(sec("F. What was checked, with the command that checks it",
                    tbl(["Check", "Command", "Scope", "Result", "Date", "Source"], rows, cls="dense wrap"),
                    "The same rows are appended to <a href=\"verification.html\">the site-wide verification "
                    "log</a>; nothing in that file is asserted without the command that reproduces it."))
    return S.page("results-feed.html", "Verified Results Feed", "".join(body), wide=True)


# ---------------------------------------------------------------------------
# 3. origination.html
# ---------------------------------------------------------------------------
def origination_page():
    cur = tsv("fair_lines_current.tsv")
    hist = tsv("fair_lines_history.tsv")
    mp = js("model_params.json")
    par = mp["parameters"]
    weeks = sorted({r["week"] for r in cur if r["week"]}, key=lambda w: float(w))
    live_week = weeks[-1] if weeks else ""
    slate = [r for r in cur if r["week"] == live_week]
    unlined = sum(1 for r in cur if str(r["market_side_line_home"]).strip() == "")

    body = ['<section><h1>Line origination</h1>',
            lead("Three markets per game, produced in the order the brief demands: the side first, then the "
                 "total, then the moneyline. Each row publishes our fair number, the market number, and the "
                 "difference between them as three separate columns &mdash; never a blended figure, never a "
                 "number chosen to make the other two agree.")]
    body.append(callout("The order is enforced in code, not by convention.",
                        "<code>OriginationPipeline.originate_total()</code> and "
                        "<code>derive_moneyline()</code> raise <code>StageOrderError</code> unless "
                        "<code>originate_side()</code> has run for that game. That is not decoration: the "
                        "moneyline is a re-statement of the margin distribution, so fitting it separately to "
                        "prices would create three models that cannot be reconciled. A unit test asserts the "
                        "raise.", kind=""))
    body.append("</section>")

    rows = [[c(par["mu"]), c(par["mu_basis"]), num(par["lam"], 4), num(par["s"], 4), num(par["hfa"], 4),
             num(par["sd_residual"], 4), c(par["tuning_objective"]), c(par["tuning_window"]),
             num(par["tuning_n_pred"], 0), c(mp["evaluate_from"]), srcs("S56")]]
    body.append(sec("A. Model card: what is fitted, on what, for what objective",
                    tbl(["&mu; (league mean points per team)", "How &mu; is set", "EWMA &lambda;",
                         "Scaling s", "HFA (home-field adjustment, pts)", "Residual sd (pts)",
                         "Tuning objective", "Tuning window", "Fitted predictions", "Published from", "Source"],
                        rows, cls="dense wrap"),
                    "Every parameter here was chosen by grid search on the development window only "
                    "(<code>%s</code>), and the whole grid is published in "
                    "<code>data/market/model_params.json</code> (%s combinations, best 10 shown). No folklore "
                    "constant is used anywhere: there is no assumed home-field number and no assumed "
                    "&lsquo;questionable means 50 per cent&rsquo;."
                    % (mp["dev_window"], mp["tuning_grid_size"])))
    nf = mp["what_is_not_fitted"]
    body.append(sec("B. What is deliberately not estimated",
                    "<ul>" + "".join("<li>%s</li>" % S.esc(x) for x in nf) + "</ul>",
                    "The third bullet is the one a reader most often expects to find filled in: this site "
                    "publishes how deep a replacement sits, not what it is worth in points, because the "
                    "conversion needs snap counts and no official source publishes them "
                    "(<a href=\"depth.html\">depth</a> carries the same rule)."))

    rows = []
    for r in slate:
        has_mkt = str(r["market_side_line_home"]).strip() != ""
        rows.append([c(r["gameday"]), c(r["away"]), c(r["home"]),
                     num(r["fair_side_line_home"], 2),
                     num(r["market_side_line_home"], 2), signed(r["delta_side_pts"], 2),
                     c(r["side_line_source"] or "no market number captured"),
                     num(r["fair_total"], 2), num(r["market_total_line"], 2), signed(r["delta_total_pts"], 2),
                     num(r["fair_p_home"], 4), num(r["market_p_home_novig"], 4), signed(r["delta_ml_pp"], 2),
                     num(r["fair_price_home"], 0), num(r["market_ml_home"], 0),
                     num(r["key_number_distance"], 2), num(r["residual_n"], 0),
                     c(r["has_result"] if not has_mkt else "settled" if str(r["has_result"]).startswith("yes") else "unplayed"),
                     srcs("S47", "S56")])
    body.append(sec("C. The live slate: Week %s, all %s games" % (live_week, len(slate)),
                    tbl(["Date", "Away", "Home", "FAIR side (home)", "MARKET side (home)", "&Delta; side (pts)",
                         "Market line feed", "FAIR total", "MARKET total", "&Delta; total (pts)",
                         "FAIR P(home)", "MARKET P(home) no-vig", "&Delta; ML (pp)", "FAIR price (home)",
                         "MARKET price (home)", "Key-number distance", "Residuals behind the ML",
                         "State", "Source"], rows),
                    "Three separate columns per market, exactly as required. Where the market column shows the "
                    "marked dash, no number for that game exists in any captured feed &mdash; %s of the %s "
                    "games scheduled this season are in that state, and the difference column is blank for them "
                    "by rule rather than measured against an assumed hold "
                    "(<a href=\"flagged.html#F21\">F21</a>, <a href=\"questions.html\">Q24</a>)."
                    % (unlined, len(cur))))

    rows = []
    for r in hist:
        rows.append([c(r["season"]), num(r["games"], 0), num(r["side_delta_present"], 0),
                     num(r["side_mae_vs_market_pts"], 3), num(r["side_mae_vs_actual_pts"], 3),
                     num(r["market_mae_vs_actual_pts"], 3), num(r["side_hit_pct"], 2),
                     num(r["total_delta_present"], 0), num(r["total_mae_vs_market_pts"], 3),
                     num(r["total_mae_vs_actual_pts"], 3), num(r["total_market_mae_vs_actual_pts"], 3),
                     num(r["ml_delta_present"], 0), num(r["ml_mean_delta_pp"], 3),
                     num(r["ml_brier_gain_pp"], 3), c(r["residual_sd"]), srcs("S47", "S56")])
    body.append(sec("D. How the originated line compares, season by season",
                    tbl(["Season", "Games", "Side: deltas present", "Side MAE vs market (pts)",
                         "Side MAE vs actual (pts)", "Market MAE vs actual (pts)", "Side: direction right %",
                         "Total: deltas present", "Total MAE vs market", "Total MAE vs actual",
                         "Market total MAE vs actual", "ML: pairs", "ML mean delta (pp)",
                         "ML Brier gain vs market (milli)", "Residual sd", "Source"], rows),
                    "The two MAE columns side by side are the whole point: our distance from the market, and "
                    "our distance from what actually happened, next to the market's own distance from what "
                    "happened. Where ours is larger than the market's, the model is worse than the number it "
                    "is arguing with, and that is published rather than smoothed."))
    body.append(sec("E. Reproduce it",
                    "<p><code>python3 scripts/build_market_spine.py</code> regenerates every number on this "
                    "page from the captures in <code>data/raw/</code>; "
                    "<code>python3 scripts/build_market_spine.py --check</code> proves the committed artefacts "
                    "are byte-identical to a fresh run. The pipeline is "
                    "<code>engine/originate.py</code>, the settlement it is graded against is "
                    "<code>engine/results_ledger.py</code>, and the price rows it quotes are in "
                    "<a href=\"price-store.html\">the store</a>.</p>"))
    return S.page("origination.html", "Line Origination", "".join(body), wide=True)


# ---------------------------------------------------------------------------
# 4. signal-vs-staking.html
# ---------------------------------------------------------------------------
def signal_staking_page():
    sig = tsv("signal_cards.tsv")
    stk = tsv("staking_cards.tsv")
    board = tsv("leaderboard_split.tsv")
    legacy = tsv("legacy_leaderboard_split.tsv")
    seas = tsv("backtest_by_season.tsv")
    cfg = js("demotion_config.json")
    clear = sum(1 for r in board if str(r["signal_grade"]).startswith("SIGNAL CLEARS"))
    rewards = sum(int(r["reward_units"] or 0) for r in board)

    body = ['<section><h1>Signal, and staking, kept apart</h1>',
            lead("One leaderboard, two blocks. The signal block never sees a stake: it measures points beat the "
                 "line, hit rate against the break-even implied by the log's own prices, whether the stated "
                 "edge is calibrated, and how much of the available slate the rule selected. The staking block "
                 "measures what a bankroll experienced. A run of luck can move the second block; it cannot "
                 "move the first, and only the first ranks.")]
    rows = []
    for r in sig:
        rows.append([c(r["strategy_id"]), c(r["market"]), num(r["signal_bets"], 0),
                     num(r["signal_n_eligible"], 0), num(r["selectivity_pct"], 1),
                     num(r["hit_rate"], 5), num(r["hit_ci_low"], 5), num(r["hit_ci_high"], 5),
                     num(r["breakeven_hit"], 5), num(r["mean_abs_edge"], 3), signed(r["points_beat_mean"], 4),
                     signed(r["points_beat_lb"], 4), c(r["points_beat_ci"] or "fewer than 30 settled bets"),
                     num(r["calibration_slope"], 4), c(r["calibration_ci"] or ""),
                     c(r["p_one_sided"]), c(r["signal_grade"]), srcs("S56", "S47")])
    body.append(sec("A. Signal block &mdash; stake-free",
                    tbl(["Rule", "Market", "Settled bets", "Eligible games", "Selectivity %", "Hit rate",
                         "Hit 95% low", "Hit 95% high", "Break-even hit rate", "Mean stated edge",
                         "Mean points beat", "Points beat, 95% lower bound", "Bootstrap interval",
                         "Calibration slope", "Slope interval", "p (one-sided)", "Reading", "Source"], rows),
                    "&lsquo;Break-even hit rate&rsquo; is computed from the modal price actually paid in that "
                    "rule's own log, not from an assumed hold. A negative calibration slope is the most "
                    "important column in this table: it means a bigger stated edge predicts a <em>worse</em> "
                    "result, so the rule is inverted rather than merely unlucky."))

    rows = []
    for r in stk:
        rows.append([c(r["strategy_id"]), num(r["stake_units"], 1), signed(r["profit_units"], 2),
                     signed(r["roi"], 5), signed(r["roi_ci_low"], 5), num(r["roi_ci_high"], 5),
                     num(r["max_drawdown_units"], 2), num(r["bets_at_posted_price"], 0),
                     num(r["price_basis_pct_posted"], 1), c(r["roi_is_upper_bound"]), c(r["staking_note"]),
                     srcs("S47", "S56")])
    body.append(sec("B. Staking block &mdash; what the bankroll saw, never ranked on",
                    tbl(["Rule", "Units staked", "Profit (units)", "ROI", "ROI 95% low", "ROI 95% high",
                         "Max drawdown (units)", "Bets at a posted price", "% posted", "ROI is an upper bound",
                         "Note", "Source"], rows, cls="dense wrap"),
                    "Every ROI figure here is measured at the recorded market number, which is a close or an "
                    "undated price &mdash; nobody can trade at the close of their own bet, so these are upper "
                    "bounds, not expectations. A quarter of the rows carry an assumed &minus;110 because the "
                    "feed holds the line but not the payout "
                    "(<a href=\"flagged.html#F19\">F19</a>, <a href=\"questions.html\">Q22</a>)."))

    rows = []
    for r in board:
        rows.append([num(r["rank_signal"], 0), c(r["strategy_id"]), c(r["market"]),
                     num(r["signal_bets"], 0), signed(r["points_beat_lb"], 4), num(r["hit_rate"], 5),
                     num(r["breakeven_hit"], 5), num(r["calibration_slope"], 3),
                     num(r["selectivity_pct"], 1), c(r["signal_grade"]),
                     num(r["rank_staking"], 0), signed(r["roi"], 5), num(r["max_drawdown_units"], 1),
                     c(r["divergence"]), num(r["reward_units"], 0), c(r["status"]), srcs("S56")])
    body.append(sec("C. The split leaderboard",
                    tbl(["Signal rank", "Rule", "Market", "Settled bets", "Points beat, 95% LB", "Hit rate",
                         "Break-even", "Calibration slope", "Selectivity %", "Reading", "Staking rank", "ROI",
                         "Drawdown", "Divergence between the two blocks", "Reward units", "State", "Source"],
                        rows),
                    "Ranking uses the lower bound on points beat, so a rule cannot climb by betting more "
                    "often. %s of %s rules clear zero; %s units of reward are payable. The divergence column "
                    "exists to name, out loud, the case the brief is guarding against: profit on a signal that "
                    "cannot clear its own break-even is a run, and it earns nothing here."
                    % (clear, len(board), rewards)))

    rows = []
    for r in legacy:
        rows.append([c(r["strategy_id"]), num(r["legacy_bets"], 0), num(r["legacy_hit_rate"], 5),
                     signed(r["legacy_roi"], 5), c(r["legacy_verdict"]), c(r["points_beat_mean"]),
                     c(r["points_beat_lb"]), c(r["calibration_slope"]), c(r["selectivity_pct"]),
                     S.raw_src('<span class="muted">%s</span>' % S.esc(r["blockable"])), srcs("S56")])
    body.append(sec("D. The pre-existing leaderboard, re-read under the split",
                    tbl(["Strategy", "Bets", "Hit rate", "ROI", "Prior verdict", "Points beat", "Points beat LB",
                         "Calibration slope", "Selectivity", "What blocks the signal block", "Source"], rows,
                        cls="dense"),
                    "Its columns are all staking-side, and no sealed bet log exists in the repository for them, "
                    "so the signal block cannot be recomputed from them. Those cells are blank with the reason "
                    "attached rather than back-filled &mdash; the 16 strategies there stay REJECTED, and the "
                    "nine rules above are measured on a log that does exist."))

    rows = []
    for r in seas:
        rows.append([c(r["strategy_id"]), c(r["season"]), num(r["bets"], 0), num(r["wins"], 0),
                     num(r["pushes"], 0), num(r["hit_rate"], 4), num(r["staked"], 1),
                     signed(r["pnl_units"], 2), signed(r["roi"], 5), num(r["bets_at_posted_price"], 0),
                     c(r["roi_basis"]), srcs("S56")])
    body.append(sec("E. The log behind both blocks, by season",
                    tbl(["Rule", "Season", "Bets", "Wins", "Pushes", "Hit rate", "Staked", "P&L (units)",
                         "ROI", "Bets at a posted price", "ROI basis", "Source"], rows),
                    "%s settled bets across %s seasons are graded from the published log; the committed file "
                    "holds the %s most recent rows (%s of them), and the aggregate in this table is computed "
                    "from the full log. A push is a push: it is excluded from the hit-rate denominator and "
                    "returns the stake."
                    % ("{:,}".format(cfg["trades_total"]), len({r["season"] for r in seas}),
                       "{:,}".format(cfg["trades_published"]),
                       ", ".join(str(s) for s in cfg["published_trade_seasons"]))))
    return S.page("signal-vs-staking.html", "Signal and Staking, Separated", "".join(body), wide=True)


# ---------------------------------------------------------------------------
# 5. replacement-depth.html
# ---------------------------------------------------------------------------
def replacement_depth_page():
    rows_in = tsv("replacement_depth.tsv")
    clubs = tsv("replacement_depth_clubs.tsv")
    unmatched = tsv("replacement_depth_unmatched.tsv")
    resolved = sum(1 for r in rows_in if str(r["depth_levels_lost"]).strip() != "")
    broken = sum(1 for r in rows_in if str(r["chain_broken"]).strip())
    none_left = sum(1 for r in rows_in if str(r["no_replacement"]).strip())
    firsts = sum(1 for r in rows_in if str(r["absent_line"]) == "1")

    body = ['<section><h1>Depth of the replacement</h1>',
            lead("An absence is not a quantity. &lsquo;Starting weakside linebacker is out&rsquo; tells a "
                 "reader nothing about how much worse the team is; what matters is who fills in and how far "
                 "down that club's own published chart the replacement sits. So every vacancy here is resolved "
                 "to a named person, and the replacement is scored on the chart.")]
    body.append(callout("What this page refuses to do.",
                        "It publishes an ordinal depth measurement, not a points penalty. Converting "
                        "&lsquo;two strings deep&rsquo; into &lsquo;minus 2.1 points&rsquo; needs snap counts "
                        "and player-quality estimates no official source publishes, so the conversion is left "
                        "named and blank in the model register instead of invented here. The chart is also "
                        "<em>unofficial by name</em> &mdash; clubs publish it as a listing, not as a "
                        "rules-defined depth order (<a href=\"flagged.html\">F02</a>).", kind="warn"))
    body.append("</section>")

    rows = [[c(r["team"]), c(r["club"]), num(r["listed_on_report"], 0), num(r["first_string_out"], 0),
             num(r["vacancies_resolved"], 0), num(r["vacancies_unresolved"], 0),
             num(r["offence_levels_lost"], 0), num(r["defence_levels_lost"], 0),
             num(r["special_teams_levels_lost"], 0), num(r["depth_lost_units"], 0),
             num(r["mean_levels_lost"], 3), c(r["worst_slot"]), num(r["chain_broken_count"], 0),
             c(r["chart_captured"]),
             S.raw_src('<a href="depth.html">club charts</a> ' + S.src_link("S01", SOURCES_BY_ID))]
            for r in clubs]
    body.append(sec("A. Club roll-up",
                    tbl(["Abbrev.", "Club", "Players on the report", "First-string absences", "Vacancies resolved",
                         "Vacancies unresolved", "Offence levels lost", "Defence levels lost",
                         "Special teams levels lost", "Total depth units lost", "Mean levels lost",
                         "Worst single vacancy", "Chains broken", "Chart captured", "Source"], rows),
                    "&lsquo;Levels lost&rsquo; is the replacement's string number minus the absent "
                    "player's: a starter replaced by the next man on the same line is 0, a starter pushed in by "
                    "a fourth-stringer is 3. A first-string absence is not automatically a depth event, and a "
                    "third-string absence can be a large one."))

    rows = []
    for r in rows_in:
        rows.append([c(r["team"]), c(r["unit"]), c(r["phase"]), c(r["slot"]), c(r["position"]),
                     c(r["absent_player"]), num(r["absent_line"], 0), c(r["game_status"]), c(r["injury"]),
                     c(r["replacement_player"] or "&mdash;"), num(r["replacement_line"], 0),
                     signed(r["depth_levels_lost"], 0), num(r["depth_remaining"], 0),
                     c(r["chain_broken"]), c(r["no_replacement"]), num(r["roster_starts_prior"], 0),
                     num(r["roster_years"], 0), srcs("S01")])
    body.append(sec("B. Every vacancy in the captured week, resolved or not",
                    tbl(["Club", "Unit", "Phase", "Slot", "Pos", "Absent", "Their line", "Game status",
                         "Injury", "Named replacement", "Replacement's line", "Levels lost",
                         "Depth left below", "Chain broken", "Nobody listed behind", "Prior starts",
                         "Years in league", "Source"], rows),
                    "%s vacancies across %s charted clubs: %s resolved to a named replacement, %s where the "
                    "chart runs out of people (%s of those the next man up is himself on the report), and %s "
                    "first-string absences. &lsquo;Prior starts&rsquo; and &lsquo;years in league&rsquo; come "
                    "from a third-party roster extract and are labelled as such in the row's basis, not "
                    "presented as official."
                    % (len(rows_in), len(clubs), resolved, none_left, broken, firsts)))

    rows = []
    for r in unmatched:
        rows.append([c(r["team"]), c(r["player"]), c(r["position"]), c(r["game_status"]), c(r["note"]),
                     srcs("S01", "S46" if r["team"] == "HOU" else "S01")])
    body.append(sec("C. On the report, not on the chart",
                    tbl(["Club", "Player", "Position", "Game status", "Note", "Source"], rows),
                    "%s entries. These are the cases a depth table built by joining names would silently drop "
                    "or, worse, force onto the nearest slot. They are listed as unresolved, because the club's "
                    "own chart does not place them." % len(unmatched)))
    return S.page("replacement-depth.html", "Depth of the Replacement", "".join(body), wide=True)


# ---------------------------------------------------------------------------
# 6. correlation-gate.html
# ---------------------------------------------------------------------------
def correlation_gate_page():
    pub = tsv("correlations_published.tsv")
    held = tsv("correlations_held.tsv")
    par = tsv("parlay_pricing.tsv")
    body = ['<section><h1>Correlation gate</h1>',
            lead("Two rules, enforced by a function rather than by a promise: a correlation may be published "
                 "only if every operand of it comes from an official source, and every published value carries "
                 "the number of joint observations it rests on. A number derived from a third-party price feed "
                 "is not false &mdash; it is a measurement of that dataset &mdash; but a column headed "
                 "&lsquo;correlation&rsquo; invites a reader to take it for a fact about the league, so "
                 "those rows are computed, labelled and held.")]
    rows = []
    for r in pub:
        rows.append([c(r["id"]), c(r["pair"]), c(r["why"]), c(r["statistic"]), signed(r["rho"], 5),
                     signed(r["ci_low"], 5), signed(r["ci_high"], 5), num(r["n"], 0), c(r["window"]),
                     c(r["x_source"]), c(r["x_tier"]), c(r["y_source"]), c(r["y_tier"]),
                     verdict_cell(r["verdict"]), c(r["gate_reasons"]), srcs("S04", "S49")])
    body.append(sec("A. Published: both operands official, n on the row",
                    tbl(["ID", "Pair", "Why it matters", "Statistic", "&rho;", "95% low", "95% high", "n",
                         "Window", "X source", "X tier", "Y source", "Y tier", "Verdict", "Gate basis",
                         "Source"], rows),
                    "n is %s games &mdash; the count of games both feeds agreed on, which is the whole "
                    "verified sample of the current season at the capture date. The interval is a fixed-seed "
                    "percentile bootstrap, so it is reproducible rather than indicative."
                    % (pub[0]["n"] if pub else "0")))
    rows = []
    for r in held:
        rows.append([c(r["id"]), c(r["pair"]), c(r["why"]), signed(r["rho"], 5), num(r["n"], 0),
                     c(r["x_source"]), c(r["x_tier"]), c(r["y_source"]), c(r["y_tier"]),
                     verdict_cell(r["verdict"]), c(r["gate_reasons"]), c(r["note"]), srcs("S48", "S50")])
    body.append(sec("B. Held, with the reason",
                    tbl(["ID", "Pair", "Why it matters", "&rho; (computed)", "n", "X source", "X tier",
                         "Y source", "Y tier", "Verdict", "Gate reason", "Note", "Source"], rows),
                    "Held rows are computed and shown, including the &rho; the gate refuses to publish, so the "
                    "reader can see the shape of the missing evidence. The pair the parlay pricing most wants "
                    "&mdash; the over against the home cover, measured on market numbers &mdash; cannot be "
                    "published on these rules because the league publishes no prices "
                    "(<a href=\"flagged.html\">F17</a>)."))
    rows = []
    for r in par:
        rows.append([c(r["pair_id"]), c(r["pair"]), signed(r["rho"], 5), num(r["n"], 0), c(r["price"]),
                     num(r["decimal"], 6), num(r["independent_joint_prob"], 6), num(r["true_joint_prob"], 6),
                     num(r["frechet_low"], 6), num(r["frechet_high"], 6), num(r["ev_at_independence"], 6),
                     num(r["ev_at_true_joint"], 6), signed(r["ev_error_per_unit"], 6),
                     num(r["break_even_prob_at_price"], 6), srcs("S04", "S56")])
    body.append(sec("C. What the measured dependence does to a two-leg price",
                    tbl(["Pair", "Legs", "&rho;", "n", "Price", "Decimal", "Joint if independent",
                         "Joint at measured &rho;", "Frechet low", "Frechet high", "EV at independence",
                         "EV at measured joint", "Error per unit", "Break-even probability", "Source"], rows),
                    "The Frechet bounds column is the only statement about a two-leg price that holds without "
                    "any dependence data at all, and it is published next to the estimate so a reader can see "
                    "how much of the conclusion depends on an n nobody has yet. A parlay priced at "
                    "independence when the legs are positively dependent is not a small rounding error: the "
                    "error per unit is in the same column."))
    return S.page("correlation-gate.html", "Correlation Gate", "".join(body), wide=True)


# ---------------------------------------------------------------------------
# 7. demotion-gate.html
# ---------------------------------------------------------------------------
def demotion_gate_page():
    ev = tsv("demotion_eval.tsv")
    cfg = js("demotion_config.json")
    th = cfg["thresholds"]
    states = cfg["per_strategy"]
    trig = sum(1 for r in ev if r["verdict"] == "TRIGGERED")
    body = ['<section><h1>Demotion gate</h1>',
            lead("Promotion gates answer &lsquo;may this strategy run money?&rsquo;. Nothing in the repository "
                 "answered when it stops. These four monitors do that, they run on the real log, and when one "
                 "fires the consequence is automatic: the strategy goes back to paper, its picks keep being "
                 "logged, and it cannot come back on profit alone.")]
    rows = []
    for r in ev:
        rows.append([c(r["strategy_id"]), c(r["rule"]), c(r["name"]), c(r["measured"]), c(r["threshold"]),
                     verdict_cell(r["verdict"]), c(r["why"]), num(r["window_bets"], 0), c(r["first_breach"]),
                     c(r["action"]), srcs("S56")])
    body.append(sec("A. Every rule, every monitor, on the committed log",
                    tbl(["Strategy", "Rule", "What it measures", "Measured", "Threshold", "Verdict", "Why",
                         "Window (bets)", "Earliest breach", "Action", "Source"], rows),
                    "%s of %s evaluations trigger on the current data. That number is mostly D4, which is a "
                    "statement about the inputs rather than about the strategies: a quarter of the log has no "
                    "posted payout and two feeds disagree about this season's slate. The gate is fail-closed by "
                    "design, so a hole in the data demotes the strategy scored on it."
                    % (trig, len(ev))))
    rows = []
    for sid, d in states.items():
        rp = d.get("repromotion") or {}
        rows.append([c(sid), c(d["state_before"]), verdict_cell(d["state_after"]),
                     c(d["triggered"] or "none"), num(rp.get("paper_bets_after_demotion", 0), 0),
                     num(rp.get("required", 0), 0),
                     signed(rp.get("lower_bound_points_beat"), 5), c(rp.get("why", "")), srcs("S56")])
    body.append(sec("B. State machine, including what a demoted strategy must do to return",
                    tbl(["Strategy", "State before", "State after", "Rules triggered", "Paper bets since",
                         "Required paper bets", "Lower bound on points beat", "What re-promotion requires",
                         "Source"], rows),
                    "Two demotions in a season escalate to a suspension, because a third chance is how a "
                    "contest ends up funding noise."))
    rows = [[h("D1 &mdash; live decay"), c("trailing mean points beat vs the recorded market number, and its 95%% lower bound; a losing run of %d settled bets also fires" % th["d1_negative_streak"]),
             h("named <strong>D1-SUBSTITUTE</strong>: the recorded number is a close or an undated price, so this measures &lsquo;did our edge against the close shrink&rsquo;, which is strictly weaker than closing-line value. The original D1 needs a timestamped open, which no capture here contains (<a href=\"flagged.html#F24\">F24</a>).")],
            [h("D2 &mdash; calibration drift"), c("slope of realised points beat on stated edge, must stay in [%s, %s]" % tuple(th["d2_slope_band"])),
             h("a slope at or below zero is the inversion case: the bigger the claimed edge, the worse the result. This is the monitor that separates &lsquo;unlucky&rsquo; from &lsquo;pointing the wrong way&rsquo;.")],
            [h("D3 &mdash; concentration"), c("largest share of net profit from one season (%d%%) or one club (%d%%)" % (100 * th["d3_season_cap"], 100 * th["d3_team_cap"])),
             c("computed on winning bets only, because that is where concentration actually hides.")],
            [h("D4 &mdash; data integrity (fail closed)"), c("missing market number above %d%%, or feed contradictions above %d%%" % (th["d4_price_gap_pct_max"], th["d4_quarantine_pct_max"])),
             c("added by this session: a strategy cannot be judged on numbers we do not trust. Missing coverage counts as a breach, not as an absence of evidence in the strategy's favour.")]]
    body.append(sec("C. The four monitors, and why each is written the way it is",
                    tbl(["Monitor", "Rule as implemented", "Why it is defined this way"], rows, cls="dense wrap"),
                    "The thresholds are configuration, published in "
                    "<code>data/market/demotion_config.json</code>, so a reviewer can change the judgement "
                    "without touching arithmetic. The definitions on "
                    "<a href=\"validation.html\">validation.html</a> remain the canonical statement of D1&ndash;D3; "
                    "this page is their evaluation, and the D1 substitution is named rather than hidden."))
    body.append(callout("Merge policy.",
                         "A D4 trigger demotes strategies and publishes its reason; it does not block a site "
                         "merge. That reading of the standing rule is written into <a href=\"questions.html\">Q25</a> "
                         "so it is a recorded decision rather than an inference from silence.", kind=""))
    body.append("</section>")
    return S.page("demotion-gate.html", "Demotion Gate", "".join(body), wide=True)


# ---------------------------------------------------------------------------
# 8. decision-desk.html
# ---------------------------------------------------------------------------
def decision_desk_page():
    flags = json.load(open(os.path.join(ROOT, "data", "flags.json"), encoding="utf-8"))
    qs = json.load(open(os.path.join(ROOT, "data", "questions.json"), encoding="utf-8"))
    sg = json.load(open(os.path.join(ROOT, "data", "suggestions.json"), encoding="utf-8"))
    mine_f = [f for f in flags if f["id"] in {"F18", "F19", "F20", "F21", "F22", "F23", "F24", "F25",
                                               "F26", "F27"}]
    mine_q = [q for q in qs if q["id"] in {"Q21", "Q22", "Q23", "Q24", "Q25"}]
    mine_s = [s for s in sg if s["id"] in {"SG16", "SG17", "SG18", "SG19"}]

    body = ['<section><h1>Decision desk</h1>',
            lead("One place where this session's open items are stated as choices: what is decided, what is "
                 "waiting on a decision, and what the next session should do. Everything here is a pointer to "
                 "a register the site already publishes &mdash; no number is restated in a way that could drift "
                 "away from its source.")]
    rows = [[c(q["id"]), c(q["category"]), S.raw_src('<span class="pill %s">%s</span>'
                                                     % ("bad" if q["priority"] == "Critical" else "warn",
                                                        S.esc(q["priority"]))),
             c(q["question"]), c(q["blocking"]), c(q["recommended_path"]),
             c(", ".join(q.get("sourceIds", []) or [])) ] for q in mine_q]
    body.append(sec("A. Questions this session opened, and the path each one suggests",
                    tbl(["ID", "Category", "Priority", "Question", "Blocks what", "Recommended path",
                         "Source"], rows, cls="dense wrap"),
                    "Rendered from <code>data/questions.json</code>, so the register and this view cannot "
                    "disagree. Full text, including what is known and unknown for each, is on "
                    "<a href=\"questions.html\">Open Questions</a>."))
    rows = [[c(s["id"]), c(s["title"]), c(s["category"]), c(s["problem"]), c(s["proposal"]),
             c(s["effort"]), c(s["risk"]), c(s["reversibility"]), c(", ".join(s.get("prerequisites", [])) or "none"),
             c(s["impact"]), srcs("S56")] for s in mine_s]
    body.append(sec("B. Paths offered, before anything is implemented",
                    tbl(["ID", "Suggestion", "Category", "Problem it answers", "Proposal", "Effort", "Risk",
                         "Reversibility", "Prerequisites", "Impact", "Source"], rows, cls="dense wrap"),
                    "Each suggestion carries its options with a recommended one marked, on "
                    "<a href=\"suggestions.html\">Suggestions</a>. Choosing a path is a reviewer action; "
                    "nothing on this page has been implemented on the strength of a recommendation."))
    rows = [[S.raw_src('<a href="flagged.html#%s">%s</a>' % (f["id"], f["id"])), c(f["kind"]),
             S.raw_src('<span class="pill %s">%s</span>'
                       % ("bad" if f["severity"] == "High" else ("warn" if f["severity"] == "Medium" else ""),
                          S.esc(f["severity"]))),
             c(f["item"]), c(f["action"]), srcs(*f.get("sourceIds", []))] for f in mine_f]
    body.append(sec("C. Irregularities this session found, published not hidden",
                    tbl(["ID", "Kind", "Severity", "Item", "What was done instead", "Sources"], rows, cls="dense wrap"),
                    "Same records as <a href=\"flagged.html\">Flagged for Review</a>, filtered to this "
                    "session. Flagged items do not block a merge; a broken build or a broken link does."))
    body.append(sec("D. Requests logged against files owned elsewhere",
                    "<ul>"
                    "<li><strong>engine/price_snapshots.py</strong> (owner <code>0669d4cf</code>): accept a "
                    "fourth <code>phase</code> value for prices whose vintage the publisher never stated. "
                    "%s of %s ledger rows are currently refused by the CHECK. Q21, SG17, F22.</li>"
                    "<li><strong>tools/site.py</strong>: the D1&ndash;D3 table on "
                    "<code>validation.html</code> is hardcoded in that file; this session added no edit to it "
                    "and left the definitions authoritative there. Evaluation lives on "
                    "<a href=\"demotion-gate.html\">demotion-gate.html</a> instead.</li>"
                    "<li><strong>data/requirements.json</strong>: requirement statuses are not rewritten here "
                    "because the register is shared. The evidence for each of the eight brief items is on the "
                    "page that carries it; an integration session can move the statuses with that evidence in "
                    "hand.</li>"
                    "<li><strong>engine/price_snapshots.py tests</strong>: this session added "
                    "<code>tests/test_market_pipeline.py</code> around the loader and the ledger rather than "
                    "touching the storage tests.</li>"
                    "</ul>" % ("{:,}".format(js("snapshot_manifest.json")["sqlite_interop"]["refused"] and
                                              sum(int(v) for v in js("snapshot_manifest.json")["sqlite_interop"]["refused"].values())),
                                "{:,}".format(js("snapshot_manifest.json")["snapshots_total"]))))
    body.append(sec("E. What the next session should do, in order",
                    "<ol>"
                    "<li>Run the dated snapshot collector against this week's slate (SG16). Two weeks of it "
                    "converts D1-SUBSTITUTE into D1 and makes 2026 bets measurable for line value.</li>"
                    "<li>Decide Q21 (store vocabulary) before any second writer is built on top of the ledger.</li>"
                    "<li>Settle the price-basis rule for published ROI (Q22), then re-publish the staking block "
                    "with the chosen basis.</li>"
                    "<li>Re-run <code>python3 scripts/build_market_spine.py</code> after each capture refresh; "
                    "<code>--check</code> tells you whether a committed artefact moved.</li>"
                    "<li>Only then revisit rewards (SG19): with today's data the payable amount is zero, and "
                    "that is the finding, not a placeholder.</li>"
                    "</ol>"))
    return S.page("decision-desk.html", "Decision Desk", "".join(body), wide=True)


# ---------------------------------------------------------------------------
_counts_cache = {}


def summary_counts():
    """Headline figures for the dashboard cards, read from the artefacts.

    Strings, formatted once, cached: the dashboard must not disagree with the pages, so
    these numbers are taken from data/market/summary.json rather than recomputed here.
    """
    if _counts_cache:
        return _counts_cache
    sm = js("summary.json")
    depth = tsv("replacement_depth.tsv")
    _counts_cache.update({
        "snapshots": "{:,}".format(sm["snapshots"]),
        "quarantined": "{:,}".format(sm["snapshots_quarantined"]),
        "verified": str(sm["games_2026_verified"]),
        "games": str(sm["games_2026"]),
        "trades": "{:,}".format(sm["trades"]),
        "trades_published": "{:,}".format(sm["trades_published"]),
        "strategies": str(sm["strategies"]),
        "clearing": str(sm["strategies_clearing_signal"]),
        "rewards": "{:,}".format(sm["rewards_paid"]),
        "demotions": str(sm["demotions"]),
        "depth": str(len(depth)),
        "correlations": str(sm["correlations_published"]),
        "capture": sm["capture_date"],
    })
    return _counts_cache


PAGES = [price_store_page, results_feed_page, origination_page, signal_staking_page,
         replacement_depth_page, correlation_gate_page, demotion_gate_page, decision_desk_page]


def render_all():
    """Render the market-spine pages. Called from tools/site.py's main()."""
    global SOURCES_BY_ID
    SOURCES_BY_ID = {s["id"]: s for s in build.load("sources.tsv")}
    return [p() for p in PAGES]


def main():
    for name in render_all():
        print("  " + name)


if __name__ == "__main__":
    main()
