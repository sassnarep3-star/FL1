#!/usr/bin/env python3
"""D5 strategy, live verification, and availability pages. Additive to site.py."""
import csv
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def _json(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def _e(x):
    return html.escape("" if x is None else str(x))


def _val(x, suffix=""):
    return "—" if x is None or x == "" else _e(x) + suffix


def _table(headers, rows):
    head = "".join("<th>%s</th>" % _e(h) for h in headers)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % (c if isinstance(c, str) and c.startswith("<") else _e(c)) for c in r) for r in rows)
    return '<div class="table-wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (head, body)


def _src(url, label="official source"):
    return '<a href="%s" rel="noopener">%s</a>' % (_e(url), _e(label))


def _section(title, text=""):
    return '<section class="card"><h2>%s</h2>%s' % (_e(title), text)


def build(ctx):
    page, esc, pill = ctx["page"], ctx["esc"], ctx["pill"]
    live = _json("live_state_d5.json")
    health = _json("org_health_d5.json")
    availability = _json("availability_d5.json")
    score = _json("scorecard_d5.json")
    forecast = _json("forecast_ledger_d5.json")
    pages = []
    sections = []

    # executive summary and immediate diligence
    inj = health["availability"]
    dep = health["depth"]
    model = health["model_inputs"]
    overview = _section("Executive summary", """
<p>As of the dated official NFL captures on 17 November 2026, the line lab has a
32-club standings snapshot, a 13-game Week 10 finals capture (the unfinished
LAC–BAL game is excluded), a 13-game Week 11 schedule, and a 347-player injury
report across 28 club sections. The frozen Elo point estimates are scored
retrospectively only: they were not prospectively pre-registered and do not
qualify for the competition. The leaderboard therefore has no eligible winner.
</p><ul>
<li>Injury rows changed against the committed earlier snapshot: %s new rows,
%s field changes; %s committed rows missing from the current capture.</li>
<li>Depth source covers %s of 32 clubs. The Houston image chart and Kansas City
source gap remain unresolved; replacement rows are not starters unless the
official chart names that rank.</li>
<li>The Elo model has %s scored games, Brier skill %s (game bootstrap 95%% interval
%s to %s) against a constant-0.5 baseline. This is ex-post and not an eligible
leaderboard result.</li>
<li>The 1,540-bet planning sample uses a 55%% alternative against 52.38%% break-even,
80%% power; it is a planning threshold, not a claim about expected performance.</li>
</ul><p>All missing or unresolved evidence remains blank. Method details and row-level
flags are in the pages below.</p>
""" % (inj["added_since_1114"], inj["moved_fields_since_1114"], inj["invented_rows"],
       dep["clubs_with_chart"], model["scored_forecasts"],
       _val(score["measured"].get("bss") if score.get("measured") else None),
       _val(score["measured"].get("lo") if score.get("measured") else None),
       _val(score["measured"].get("hi") if score.get("measured") else None)))
    sections.append(overview + "</section>")

    # captures / freshness and source hash ledger
    rows = []
    for name, c in live["captures"].items():
        rows.append([name, c["read_at"], c["sha256"], str(c["bytes"]), _src(c["url"])])
    caphtml = _section("Dated official capture ledger", "<p>Immutable, hash-pinned files in <code>raw/live/</code>. A new read must get a new dated path, never overwrite.</p>" + _table(["Capture", "Read at UTC", "SHA-256", "Bytes", "Official source"], rows))
    pages.append(page("live-captures.html", "Live Capture Ledger", caphtml + "</section>", wide=True))

    # live standings with stale rows called out
    rows = []
    for r in live["standings"]:
        x = r["live"]
        flag = "stale in published standings" if r["stale_vs_base"] else "current"
        rows.append([r["club"], "%s-%s-%s" % (x["w"], x["l"], x["t"]), x["pf"], x["pa"], x["net"], flag,
                     _src(live["captures"]["standings"]["url"])])
    standings = _section("2026 standings — official capture", _table(["Club", "W-L-T", "PF", "PA", "Net", "Compared with site data", "Source"], rows))
    pages.append(page("live-standings.html", "Live 2026 Standings", standings + "</section>", wide=True))

    # week 10 results / week 11 schedule
    rows = [[g["week"], g["date"], g["away"], g["away_pts"], g["home"], g["home_pts"], _src(g["url"])] for g in live["week10_finals"]]
    w10 = _section("Week 10 official finals", _table(["Week", "Date", "Away", "Pts", "Home", "Pts", "Game centre"], rows) + '<p>13 finished games. LAC–BAL was not final at capture time and is not scored or added.</p>')
    pages.append(page("live-finals.html", "Week 10 Official Finals", w10 + "</section>", wide=True))
    rows = [[g["date"], g["kickoff_et"], g["away"], g["home"], g["network"], _val(g["venue"]), _src(g["url"])] for g in live["week11_slate"]]
    w11 = _section("Week 11 official schedule", _table(["Date", "Kickoff ET", "Away", "Home", "Network", "Venue", "Game centre"], rows) + '<p>The source page does not provide a league schedule-announcement date. That value is deliberately blank; see Flagged for Review.</p>')
    pages.append(page("live-schedule.html", "Week 11 Official Schedule", w11 + "</section>", wide=True))

    # strategy competition
    rows = []
    for e in score["registry"]:
        signal = e.get("signal", {})
        rows.append([e["id"], e.get("name", e.get("label", "")), e.get("division", ""),
                     "YES" if e.get("qualified") else "NO",
                     "%s/%s" % (e.get("gates_passed", 0), e.get("gates_total", 0)),
                     _val(signal.get("n")), _val(signal.get("bss")), _val(signal.get("bss_lo")),
                     e.get("registration", {}).get("committed", False),
                     e.get("what_would_change_our_mind", "")])
    scorehtml = _section("Pre-registered strategy competition", """
<p>Registration is a frozen candidate registry; it is not a performance claim.
Backtests are excluded from eligibility and ranking. Rank is by benchmark-relative
proper score with a game-cluster lower bound, then multiplicity adjustment. Signal
and staking are separate. No current entry clears all gates. Combinations remain
blocked until directly validated joint probabilities and void/push rules are present.
</p><p>Measured historical Elo: n=%s; BSS=%s (95%% game-cluster interval %s to %s).
This measurement is retrospective, not pre-registered, and the lower bound is not
above zero; it is displayed for audit, not as a leaderboard rank.</p>""" % (
       score["measured"]["n"] if score.get("measured") else 0,
       _val(score["measured"].get("bss") if score.get("measured") else None),
       _val(score["measured"].get("lo") if score.get("measured") else None),
       _val(score["measured"].get("hi") if score.get("measured") else None)) +
       _table(["ID", "Strategy", "Division", "Qualified", "Gates", "Measured n", "BSS", "BSS lower bound", "Committed", "What changes our mind"], rows))
    pages.append(page("strategy-scorecard.html", "Strategy Scorecard", scorehtml + "</section>", wide=True))

    # readiness/health metrics, every row sourceable or explicitly repo-internal
    src_inj = _src(live["captures"]["injuries"]["url"])
    src_stand = _src(live["captures"]["standings"]["url"])
    health_rows = [
        ["Official injury rows", inj["report_rows"], "347 rows across 28 clubs", src_inj],
        ["Roster/IR sweep", "NOT VERIFIED", "official 32-club roster and reserve-list capture absent", ""],
        ["Depth charts", "%d/32" % dep["clubs_with_chart"], "HOU image and KC source gap; source register", ""],
        ["Point-in-time injury hashes", "4 captures", "all dated files hash-verified", src_inj],
        ["Verified standings", "32/32", "live official data; base site copy stale on %d clubs" % len(live["stale_vs_base"]), src_stand],
        ["Forecasts scored", model["scored_forecasts"], "retrospective; no prospective lock-before-kickoff evidence", ""],
        ["Season sample bar", score["sample_bars"]["singles"], "games/bets needed for configured 80% power", ""],
        ["Pre-registered eligible strategies", score["qualified_count"], "0 currently qualify", ""],
        ["Price-data policy", "OPEN", "third-party price series only; no first-party origin/open/close store", ""],
        ["Inactive lists + snap shares", "MISSING", "official evidence feed not ingested", ""],
    ]
    readiness = _section("Decision-readiness clearing numbers", _table(["Requirement", "Current", "Gate / clearing evidence", "Source"], health_rows))
    pages.append(page("readiness-d5.html", "Decision Readiness — D5", readiness + "</section>", wide=True))

    # availability matrix
    rows = []
    for r in availability["rows"]:
        source = _src(r.get("chart_url"), r.get("chart_source") or "depth chart") if r.get("chart_url") else "—"
        rows.append([r["club"], r["unit"], r["pos"], r["player"], r["depth_rank"], r["group_size_at_rank"],
                     r["status"], r["practice"], _val(r["replacement"]), _val(r["string_gap"]), source,
                     src_inj])
    avhtml = _section("Official report × captured depth rows", """
<p>Rows are exact-name joins only; no fuzzy matches. The chart lists order, not
proof of starter status, and the displaced person may not be the starter. “Replacement”
means next listed player in the same parsed position slot only; it is not a claim that
the player entered the game. Official Game Books, inactive lists and snap counts are
needed to confirm actual starters and replacements. Current chart source coverage is
%s/32 clubs; no rank is inferred where a chart was not captured.</p>""" % dep["clubs_with_chart"] +
       _table(["Club", "Unit", "Pos", "Report player", "Chart rank", "Players tied", "Game status", "Practice", "Next listed", "Depth gap", "Depth source", "Injury source"], rows))
    pages.append(page("availability-matrix-d5.html", "Availability & Replacement Matrix", avhtml + "</section>", wide=True))

    # Q&A and suggestions backlog to make decisions explicit
    questions = [
        ["Q-D5-01", "May third-party nflverse price data be used as a research benchmark?", "OPEN", "Need explicit policy on source terms, opening/closing definition, and whether prices are executable."],
        ["Q-D5-02", "What timestamp constitutes line open and line close?", "OPEN", "No originations currently have a first-party, timestamped price lifecycle."],
        ["Q-D5-03", "What official evidence establishes expected starters?", "OPEN", "Official Game Books confirm actual starters after games; pregame announced-starter evidence needed."],
        ["Q-D5-04", "Can player prop combos be ranked?", "NO", "Not until a directly validated joint probability and operator void/push rules are available."],
        ["Q-D5-05", "Can the roster/IR sweep be trusted?", "NO", "Capture the official 32-team rosters and reserve lists with hashes and point-in-time timestamps."],
        ["Q-D5-06", "Can injury labels enter model features?", "NO", "Need multi-season designation joins to official inactives and empirical play-rate confidence intervals."],
        ["Q-D5-07", "Can depth gaps quantify performance impact?", "NO", "Need official starters plus snap counts; chart position alone does not prove play or replacement."],
        ["Q-D5-08", "Can venue/context features be published?", "PARTIAL", "Official game-centre venue evidence only exists for captured games; schedule announcement date is missing."],
    ]
    qhtml = _section("Questions, known answers, and missing evidence", _table(["ID", "Decision question", "Answer now", "Information needed"], questions))
    pages.append(page("decision-questions-d5.html", "Decision Questions & Missing Evidence", qhtml + "</section>", wide=True))
    suggestions = [
        ["SG-D5-01", "Choose and document price-data terms/policy before publishing any backtest", "Blocking", "Legal/source terms, definition of open/close, executable price policy"],
        ["SG-D5-02", "Add scheduled immutable capture of official injury hub, club charts, reserve lists and inactives", "High", "Authorized persistence target, capture cadence, alert owner"],
        ["SG-D5-03", "Acquire official Game Books and snap counts; join exact names only", "High", "Structured official source and season coverage"],
        ["SG-D5-04", "Resolve HOU image and KC depth source, then verify all 32 clubs", "High", "Authorized structured source for Houston; current Kansas City depth page"],
        ["SG-D5-05", "Append pre-kickoff probabilistic forecasts to immutable ledger and independently hash each run", "High", "Operational schedule and timestamp authority"],
        ["SG-D5-06", "Run chronological availability ablations only after starter/inactive/snap joins exist", "After evidence", "Verified availability graph and multi-season snapshots"],
        ["SG-D5-07", "Do not rank parlays/prop combos until joint calibration and settlement rules pass", "Blocking", "Joint outcomes, void/push rules, dependence-aware sample"],
    ]
    sh = _section("Suggestions for better decisions — review before implementation", _table(["ID", "Suggestion", "Priority", "Evidence needed first"], suggestions))
    pages.append(page("suggestions-d5.html", "Suggestions & Evidence Pipeline", sh + "</section>", wide=True))

    # Full derived registers: preserve every existing question and suggestion, not only
    # the short D5 decision examples above.
    def load_rows(name):
        with open(os.path.join(DATA, name), encoding="utf-8") as f:
            return json.load(f)
    decision_rows = load_rows("decision_ledger_d5.json")
    rows = []
    for r in decision_rows:
        sid = r.get("source", "")
        ids = [x.strip() for x in sid.replace(" ", "").split(",") if x.strip().startswith("S")]
        source = ", ".join('<a href="sources.html#%s">%s</a>' % (_e(x), _e(x)) for x in ids) if ids else "—"
        rows.append([r["id"], r["category"], r["question"], r["known"], r["unknown"],
                     r["blocking_gate"], r["clearing_number"], r["owner_action"], source])
    dh = _section("Full decision ledger", "<p>Questions and flags carried from the existing registers; blank clearing criteria are intentionally not invented. Source IDs link to the source registry.</p>" +
        _table(["ID", "Category", "Question / issue", "Known", "Unknown", "Blocking gate", "Clearing number", "Owner action", "Source"], rows))
    pages.append(page("decision-ledger.html", "Decision Ledger", dh + "</section>", wide=True))

    pipe = load_rows("suggestion_pipeline_d5.json")
    rows = [[r["id"], r["title"], r["review_state"], r["impact"], r["effort"], r["reversibility"],
             r["prerequisites"], r["proposal"], r["evidence"]] for r in pipe]
    ph = _section("Suggestion pipeline", "<p>All suggestions are in proposed state until an explicit owner decision; nothing is auto-accepted or auto-implemented. Impact values are shown only when the source register supplies them.</p>" +
        _table(["ID", "Suggestion", "Review state", "Impact", "Cost", "Reversibility", "Prerequisites", "Proposal", "Evidence"], rows))
    pages.append(page("suggestions-pipeline.html", "Suggestion Review Pipeline", ph + "</section>", wide=True))

    qa_rows = load_rows("qa_register_d5.json")
    rows = [[r["id"], r["category"], r["priority"], r["question"], r["answer_now"], r["unknown"],
             r["missing_information"], r["how_to_find_out"], r["source"]] for r in qa_rows]
    qh = _section("Complete Q&A register", "<p>All existing questions are shown; a missing value stays blank rather than receiving an inferred answer.</p>" +
        _table(["ID", "Category", "Priority", "Question", "Known answer", "Unknown", "Missing information", "How to find out", "Source"], rows))
    pages.append(page("qa-d5.html", "Complete Questions & Answers", qh + "</section>", wide=True))

    # source-backed flags
    flags = [
        ["F-D5-01", "Committed standings are stale", "24/32 club records differ from the 17 Nov official capture; live values are shown separately.", src_stand],
        ["F-D5-02", "Injury snapshot differs from committed rows", "%d rows added, %d field changes; preserve the committed file, review differences before replacing it." % (inj["added_since_1114"], inj["moved_fields_since_1114"]), src_inj],
        ["F-D5-03", "Depth coverage incomplete", "%d clubs have parsed chart rows; HOU image chart and KC source gap unresolved." % dep["clubs_with_chart"], ""],
        ["F-D5-04", "No prospective strategy has cleared validation", "Current scorecard has %d qualified strategies. Historical Elo evaluation is retrospective and not eligible." % score["qualified_count"], ""],
        ["F-D5-05", "Price policy unresolved", "Market prices are third-party; no verified official operator open/close store.", ""],
        ["F-D5-06", "Unverified starter/replacement evidence", "Depth order alone is not an announced starter or proof a replacement played; official Game Books/inactives/snaps are missing.", ""],
    ]
    fh = _section("Flagged for Review", _table(["Flag", "Irregularity", "Evidence and implication", "Source"], flags))
    pages.append(page("flagged-d5.html", "Flagged for Review — D5", fh + "</section>", wide=True))

    return pages, sections
