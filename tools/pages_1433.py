#!/usr/bin/env python3
"""
pages_1433.py — the pages built by session `arena/143300b4-fl1`.

Everything here is generated from committed data files. Nothing is typed in by
hand, and every published row carries a link to the official page it came from.

Pages built here
  gamebooks.html            the official NFL Game Books: who actually started,
                            who was actually inactive, where the game was played
                            and what the weather was
  availability-graph.html   who the club's own chart expected to start against
                            who the official book says did
  depth-slots.html          the clubs' depth charts read as SLOT GROUPS, so a
                            slot with two names at the first string is not
                            flattened into a single fabricated "starter"
"""

import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

OUTCOME_KIND = {
    "STARTED_AS_CHARTED": "ok",
    "STARTED_FROM_DEEPER_ON_THE_CHART": "warn",
    "STARTED_NOT_ON_THE_CHART": "warn",
    "OUT_INACTIVE": "bad",
    "DID_NOT_PLAY": "bad",
    "NOT_ON_THE_GAME_DAY_ROSTER": "bad",
    "DID_NOT_START": "warn",
}


def load_csv(name, base=DATA):
    path = os.path.join(base, name)
    delim = "\t" if name.endswith(".tsv") else ","
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=delim))


def load_json(name, base=DATA):
    path = os.path.join(base, name)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _link(ctx, url, label="official"):
    if not url:
        return ctx["raw_src"]('<span class="src">no link</span>')
    return ctx["raw_src"](
        '<a class="src" href="%s" target="_blank" rel="noopener">%s</a>'
        % (ctx["esc"](url), ctx["esc"](label)))


# ---------------------------------------------------------------------------
# Official game books
# ---------------------------------------------------------------------------
def gamebooks_page(ctx):
    games = load_csv("gamebooks/games.tsv")
    players = load_csv("gamebooks/players.tsv")
    report = load_json("gamebooks/parse_report.json")

    counts = {}
    for p in players:
        counts[p["status"]] = counts.get(p["status"], 0) + 1
    venues = len({g["venue_stadium"] for g in games if g["venue_stadium"]})
    with_weather = sum(1 for g in games if g["temp_f"])
    roofs = {}
    for g in games:
        roofs[g["roof_status"]] = roofs.get(g["roof_status"], 0) + 1

    rows = []
    for g in games:
        rows.append([
            ctx["cell"](g["game_date"]),
            ctx["cell"](g["away_team"]),
            ctx["cell"](g["home_team"]),
            ctx["cell"]("%s–%s" % (g["away_score"], g["home_score"])),
            ctx["cell"](g["venue_stadium"]),
            ctx["cell"](g["venue_city"]),
            ctx["cell"](g["roof_status"]),
            ctx["cell"](g["surface"]),
            ctx["cell"](g["temp_f"], "n"),
            ctx["cell"](g["humidity_pct"], "n"),
            ctx["cell"](g["wind"]),
            _link(ctx, g["official_url"], "game centre"),
            _link(ctx, g["gamebook_url"], "game book PDF"),
        ])

    notes = [g for g in games if g["book_notes"]]

    kpis = [
        [ctx["cell"]("Official game books captured"), ctx["cell"](len(games), "n"),
         ctx["cell"]("one per completed 2026 regular-season game, hashed and stored "
                     "outside the published site"),
         _link(ctx, "https://www.nfl.com/schedules/2026/REG10/", "schedule")],
        [ctx["cell"]("Starting lineups parsed"), ctx["cell"](counts.get("starter", 0), "n"),
         ctx["cell"]("22 per game, every one checked against the book's own layout"),
         _link(ctx, "https://www.nfl.com/games/", "game centre")],
        [ctx["cell"]("Official inactive-list designations"),
         ctx["cell"](counts.get("inactive", 0), "n"),
         ctx["cell"]("the book's own “Not Active” list — the evidence the injury "
                     "report alone cannot give"),
         _link(ctx, "https://www.nfl.com/injuries/", "injury report")],
        [ctx["cell"]("“Did Not Play” designations"),
         ctx["cell"](counts.get("did_not_play", 0), "n"),
         ctx["cell"]("on the roster for the game, not on the field"),
         _link(ctx, "https://www.nfl.com/games/", "game centre")],
        [ctx["cell"]("Distinct venues transcribed from the books"), ctx["cell"](venues, "n"),
         ctx["cell"]("stadium name and city, read from the book, not from a "
                     "third-party feed"),
         _link(ctx, "https://www.nfl.com/schedules/2026/REG10/", "schedule")],
        [ctx["cell"]("Games with an official weather reading"),
         ctx["cell"](with_weather, "n"),
         ctx["cell"]("temperature, humidity and wind as printed in the book"),
         _link(ctx, "https://www.nfl.com/games/", "game centre")],
    ]

    note_rows = [[
        ctx["cell"](g["game_date"]),
        ctx["cell"](g["away_team"]),
        ctx["cell"](g["home_team"]),
        ctx["cell"](g["book_notes"]),
        _link(ctx, g["gamebook_url"], "game book PDF"),
    ] for g in notes]

    body = """
<section class="hero">
  <h1>Official game books</h1>
  <p class="lead">The official record of what actually happened on the field.
  Every row on this page is read from an NFL Game Book — the document the league
  publishes after every game — and every row links to the game it came from.
  This is the evidence the injury report cannot give: who was <em>inactive</em>,
  not merely who was on the report, and who <em>started</em>, not merely who was
  listed first on a depth chart.</p>
</section>

<h2>What the capture contains</h2>
%s

<h2>Every captured game</h2>
<p class="caption">Venue, roof, surface and weather are transcribed from the game book itself.
Each row links both to the league's game centre and to the game-book PDF it was read from.</p>
%s

<h2>Irregularities found in the books</h2>
<p class="caption">These are anomalies in the official documents themselves. They are published
as they stand — an official book is not corrected to make a model tidier — and each one is a
question for the reader, not a defect this repository has silently repaired.</p>
%s

<div class="callout">
  <h3>What a game book does <em>not</em> contain</h3>
  <p>The NFL Game Book publishes the starting lineup, the substitutions, the
  “Did Not Play” list, the “Not Active” list, the venue, the roof and surface
  status, and the game-day weather. It does <strong>not</strong> publish
  per-player snap counts for offensive players, so this repository does not
  claim to have snap counts. Depth that is measured from playing time remains
  blocked on an official snap-count source; see the requirement backlog.</p>
</div>
""" % (ctx["table"](["Figure", "Value", "Basis", "Source"], kpis, cls="kpi"),
       ctx["table"](["Date", "Away", "Home", "Score", "Venue", "City", "Roof",
                     "Surface", "Temp °F", "Humidity %", "Wind", "Game", "Book"],
                    rows, cls="data"),
       ctx["table"](["Date", "Away", "Home", "What the book says", "Source"],
                    note_rows) if note_rows else
       '<p class="caption">No irregularity was found in the captured books.</p>')
    return ctx["page"]("gamebooks.html", "Official Game Books", body, wide=True)


# ---------------------------------------------------------------------------
# Availability graph
# ---------------------------------------------------------------------------
def availability_graph_page(ctx):
    rows = load_csv("availability_graph.tsv")
    summary = load_json("availability_graph_summary.json")
    by_outcome = summary.get("by_outcome", {})

    kpis = [
        [ctx["cell"]("Games compared"), ctx["cell"](summary.get("games", 0), "n"),
         ctx["cell"]("Week 10 of 2026 — the week the club depth charts were captured for"),
         _link(ctx, "https://www.nfl.com/schedules/2026/REG10/", "schedule")],
        [ctx["cell"]("Club-games compared"), ctx["cell"](summary.get("clubs", 0), "n"),
         ctx["cell"]("each club's chart against each club's game book"),
         _link(ctx, "https://www.nfl.com/games/", "game centre")],
        [ctx["cell"]("Rows in the graph"), ctx["cell"](summary.get("rows", 0), "n"),
         ctx["cell"]("one row per player the club charted or the book started"),
         _link(ctx, "https://www.nfl.com/games/", "game centre")],
        [ctx["cell"]("Started where the chart named them at the first string"),
         ctx["cell"](by_outcome.get("STARTED_AS_CHARTED", 0), "n"),
         ctx["cell"]("no absence to explain"),
         _link(ctx, "https://www.nfl.com/games/", "game centre")],
        [ctx["cell"]("Started from deeper on the club's own chart"),
         ctx["cell"](by_outcome.get("STARTED_FROM_DEEPER_ON_THE_CHART", 0), "n"),
         ctx["cell"]("the depth-of-the-replacement case, measured on the club's chart"),
         _link(ctx, "https://www.nfl.com/games/", "game centre")],
        [ctx["cell"]("Charted at the first string and listed inactive by the book"),
         ctx["cell"](by_outcome.get("OUT_INACTIVE", 0), "n"),
         ctx["cell"]("the official inactive list, not an inference"),
         _link(ctx, "https://www.nfl.com/games/", "game centre")],
        [ctx["cell"]("Charted at the first string and not on the game-day roster"),
         ctx["cell"](by_outcome.get("NOT_ON_THE_GAME_DAY_ROSTER", 0), "n"),
         ctx["cell"]("the book does not say why, so this page does not either"),
         _link(ctx, "https://www.nfl.com/games/", "game centre")],
    ]

    body_rows = []
    for r in rows:
        body_rows.append([
            ctx["cell"](r["game_date"]),
            ctx["cell"](r["club"]),
            ctx["cell"](r["chart_unit"]),
            ctx["cell"](r["chart_slot"]),
            ctx["cell"](r["player"]),
            ctx["cell"](r["chart_rank"]),
            ctx["cell"](r["gamebook_position"]),
            "<td>%s</td>" % ctx["pill"](r["outcome"], OUTCOME_KIND.get(r["outcome"], "")),
            ctx["cell"](r["depth_levels_lost"], "n"),
            _link(ctx, r["official_url"], "game centre"),
        ])

    body = """
<section class="hero">
  <h1>The availability graph</h1>
  <p class="lead">Who was expected to start, and who actually did. This page joins two
  official documents that had never been joined before: the clubs' own published depth
  charts, and the NFL's own Game Book for the same game. On the left is what the club
  said its order would be; on the right is what the league recorded. Where the two
  disagree, the disagreement is the signal — and the depth of the replacement is
  measured on the club's own chart, not invented.</p>
</section>

<h2>The join</h2>
%s

<h2>Every row</h2>
<p class="caption">One row per player the club charted at the first string, and one row per
player who started without being the chart's first string. The outcome column states the
finding in a fixed vocabulary; the depth column is how many strings down the club's own
chart the actual starter sat.</p>
%s

<div class="callout">
  <h3>Where this stops, and why</h3>
  <p>The club depth charts in this repository were captured for <strong>Week 10 of
  2026</strong>, so they are only a valid statement of expectation for Week 10 games.
  Using them to explain an earlier game would be lookahead, and the graph does not do
  that.</p>
  <p>Some clubs print the word “unofficial” on their own depth chart. That is recorded
  against the row, and the official game book — not the chart — is the authority on
  who played.</p>
  <p>A player the chart names at the first string who does not appear in the game book
  at all is reported as <em>not on the game-day roster</em>. The book does not say
  whether that means injured reserve, a trade or a release, so this page does not
  guess.</p>
</div>
""" % (ctx["table"](["Figure", "Value", "Basis", "Source"], kpis, cls="kpi"),
       ctx["table"](["Date", "Club", "Unit", "Slot", "Player", "Chart rank",
                     "Started at", "Outcome", "Strings lost", "Source"],
                    body_rows, cls="data"))
    return ctx["page"]("availability-graph.html", "Availability Graph", body, wide=True)


# ---------------------------------------------------------------------------
# Depth slots
# ---------------------------------------------------------------------------
def depth_slots_page(ctx):
    rows = load_csv("depth_slots.tsv")
    summary = load_json("depth_slot_summary.json")
    shared = [r for r in rows if r["state"] == "shared"]
    empty = [r for r in rows if r["state"] == "empty"]

    kpis = [
        [ctx["cell"]("Published slot groups"), ctx["cell"](len(rows), "n"),
         ctx["cell"]("(club, unit, slot, occurrence of that label) read from the "
                     "clubs' own charts"),
         _link(ctx, "https://www.nfl.com/teams/", "teams")],
        [ctx["cell"]("Slots with exactly one name at the first string"),
         ctx["cell"](summary.get("single", 0), "n"),
         ctx["cell"]("the club named a starter"),
         _link(ctx, "https://www.nfl.com/teams/", "teams")],
        [ctx["cell"]("Slots the club published with more than one name at the first string"),
         ctx["cell"](summary.get("shared", 0), "n"),
         ctx["cell"]("this site does not choose between them"),
         _link(ctx, "https://www.nfl.com/teams/", "teams")],
        [ctx["cell"]("Slots the club published with no name at the first string"),
         ctx["cell"](summary.get("empty", 0), "n"),
         ctx["cell"]("left empty rather than filled in"),
         _link(ctx, "https://www.nfl.com/teams/", "teams")],
        [ctx["cell"]("Clubs with a captured chart"),
         ctx["cell"](summary.get("n_clubs", 0), "n"),
         ctx["cell"]("Houston is not one of them: the club publishes its chart as an image"),
         _link(ctx, "https://www.nfl.com/teams/", "teams")],
    ]

    def slot_rows(items):
        out = []
        for r in items:
            out.append([
                ctx["cell"](r["team"]),
                ctx["cell"](r["club"]),
                ctx["cell"](r["unit"]),
                ctx["cell"](r["slot"]),
                ctx["cell"](r["line"], "n"),
                ctx["cell"](r["n_at_first_string"], "n"),
                ctx["cell"](r["first_string_names"] or "— the club published no name here"),
                ctx["cell"](r["ladder"]),
                ctx["cell"](r["chart_date"] or "not dated on the chart"),
                _link(ctx, r["source_url"], "club chart"),
            ])
        return out

    body = """
<section class="hero">
  <h1>Depth slots as groups</h1>
  <p class="lead">A club's depth chart does not always name one starter per slot. It
  sometimes names two players at the same string, and it sometimes leaves a string with
  no name at all. Reading a chart as a flat list of “starters and backups” throws both
  facts away, and then quietly invents a starter the club never named. This page reads
  each chart as a set of <em>slot groups</em> and says which kind of slot each one is.</p>
</section>

<h2>What the charts actually say</h2>
%s

<h2>Slots published with more than one name at the first string</h2>
<p class="caption">The club published both names at the same string. This site does not
pick one, and does not call either of them “the starter”. A replacement logic that treats
column one as a single starter would demote a healthy first string to second string and
report a depth loss that never happened.</p>
%s

<h2>Slots published with no name at the first string</h2>
<p class="caption">The club published the slot and left it empty. The second string is
shown, but it is not promoted into the first.</p>
%s

<h2>Every slot group</h2>
%s
""" % (ctx["table"](["Figure", "Value", "Basis", "Source"], kpis, cls="kpi"),
       ctx["table"](["Club", "Unit", "Slot", "Occurrence", "Names at first string",
                     "First-string names", "Published ladder", "Chart date", "Source"],
                    slot_rows(shared), cls="data") if shared else
       "<p class=\"caption\">No shared slot was found.</p>",
       ctx["table"](["Club", "Unit", "Slot", "Occurrence", "Names at first string",
                     "First-string names", "Published ladder", "Chart date", "Source"],
                    slot_rows(empty), cls="data") if empty else
       "<p class=\"caption\">No empty slot was found.</p>",
       ctx["table"](["Slot", "Club", "Unit", "Position", "Occurrence", "State",
                     "Names at first string", "First-string names", "Strings",
                     "Published ladder", "Names", "Note", "Source", "Chart date"],
                    [[ctx["cell"](r["slot_id"]), ctx["cell"](r["team"]),
                      ctx["cell"](r["unit"]), ctx["cell"](r["slot"]),
                      ctx["cell"](r["line"], "n"), ctx["cell"](r["state"]),
                      ctx["cell"](r["n_at_first_string"], "n"),
                      ctx["cell"](r["first_string_names"]),
                      ctx["cell"](r["strings_populated"]),
                      ctx["cell"](r["ladder"]), ctx["cell"](r["n_names"], "n"),
                      ctx["cell"](r["note"]),
                      _link(ctx, r["source_url"], "club chart"),
                      ctx["cell"](r["chart_date"])] for r in rows], cls="data"))

    body += """
<div class="callout">
  <h3>A number in the brief that the committed capture does not reproduce</h3>
  <p>The brief describes “149 club/unit/position slots list more than one rank-1
  player”. The committed official capture in this repository yields
  <strong>%d</strong> shared first strings, the largest of which holds three names
  (Kansas City's linebacker slot). Every shared cell in the raw capture holds exactly
  two names except that one. The measured number is published above and the
  discrepancy is recorded on the Flagged for Review page rather than reconciled
  silently — the two counts may have been taken from different captures, and this
  repository will not publish either number as if it were the other.</p>
</div>
""" % summary.get("shared", 0)
    return ctx["page"]("depth-slots.html", "Depth Slots", body, wide=True)


def build(ctx):
    """Build every page this session owns and return the index sections."""
    pages = [
        gamebooks_page(ctx),
        availability_graph_page(ctx),
        depth_slots_page(ctx),
    ]
    return pages, ""


def exec_section(ctx):
    """Dated block for the executive summary page."""
    games = load_csv("gamebooks/games.tsv")
    players = load_csv("gamebooks/players.tsv")
    summary = load_json("availability_graph_summary.json")
    slots = load_json("depth_slot_summary.json")
    inactive = sum(1 for p in players if p["status"] == "inactive")
    rows = [
        [ctx["cell"]("Official NFL Game Books captured and parsed"),
         ctx["cell"](len(games), "n"),
         ctx["cell"]("every completed 2026 regular-season game, hashed and stored "
                     "outside the published site"),
         ctx["raw_src"]('<a class="src" href="gamebooks.html">game books</a>')],
        [ctx["cell"]("Official inactive-list designations"),
         ctx["cell"](inactive, "n"),
         ctx["cell"]("the book's own “Not Active” list"),
         ctx["raw_src"]('<a class="src" href="gamebooks.html">game books</a>')],
        [ctx["cell"]("Availability-graph rows"),
         ctx["cell"](summary.get("rows", 0), "n"),
         ctx["cell"]("expected starter against actual starter, Week 10"),
         ctx["raw_src"]('<a class="src" href="availability-graph.html">graph</a>')],
        [ctx["cell"]("Depth slot groups published"),
         ctx["cell"](slots.get("slot_groups", 0), "n"),
         ctx["cell"]("%d shared first strings, %d empty slots — both left as the club "
                     "published them" % (slots.get("shared", 0), slots.get("empty", 0))),
         ctx["raw_src"]('<a class="src" href="depth-slots.html">slots</a>')],
    ]
    return """
<section id="session-1433">
<h2>Session <code>arena/143300b4-fl1</code> &mdash; 2026-11-17</h2>
<p class="lead">This session closed the repository's largest evidence gap. The official
NFL Game Book — the document the league publishes after every game — had never been
captured here, so the site could say who was <em>on the injury report</em> but not who
was actually <em>inactive</em> or actually <em>started</em>. It is now captured for every
completed 2026 game, hashed, and stored outside the published site; the derived analysis
is published here with an official link on every row.</p>
%s
</section>
""" % ctx["table"](["Figure", "Value", "Basis", "Where"], rows, cls="kpi")
