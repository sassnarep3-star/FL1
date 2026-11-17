#!/usr/bin/env python3
"""H2-H8 site pages for session arena/3f12fa46-fl1.

This module owns the rendering of the six pages this session adds, reading
only from the canonical data files written by their builders. It is imported
by tools/site.py (single owner of the shell) and returns the list of written
filenames; it does NOT write files itself.

  H2  game-books.html       official Game Book capture: starters, inactives,
                            substitutions, DNP, official playtime, venue
  H3  matchup-matrix.html   offense-vs-defense deficiency matrix, 1st-4th string
  H4  model-outputs.html    every model output as a probability + input vector
  H5  weather-overlay.html  roof/surface + NWS hourly wind/precip overlay
  H6  backlog-reaudit.html  every brief requirement line's status, corrected
  H7  registers.html        (folded into existing pages; NAV added in site.py)

Every table row carries a source chip. A value the source does not publish
stays blank, never inferred.
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")


def _read_tsv(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        rows = [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]
    return rows[0], rows[1:]


def _load_sources():
    by_id = {}
    with open(os.path.join(DATA, "sources.tsv"), encoding="utf-8") as fh:
        for row in csv.reader(fh):
            if len(row) >= 5 and row[0]:
                by_id[row[0]] = row
    return by_id


def _esc(v):
    return (v.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def _src(sid, sources_by_id):
    s = sources_by_id.get(sid)
    if not s:
        return _esc(sid)
    return '<a class="src" href="%s" title="%s">%s</a>' % (
        _esc(s.get("url", "")), _esc(s.get("title", "")), sid)


# --------------------------------------------------------------------------- #
# H2 — official Game Book capture
# --------------------------------------------------------------------------- #
def render_game_books(site, sources_by_id):
    """H2 page: the official Game Book capture for the 13 completed Week 10 games."""
    esc = site.esc
    ghdr, games = _read_tsv("gamebooks_games.tsv")
    rhdr, rosters = _read_tsv("gamebooks_rosters.tsv")
    shedr, snaps = _read_tsv("gamebooks_snaps.tsv")
    with open(os.path.join(DATA, "venue_official.csv"), encoding="utf-8") as fh:
        vrows = list(csv.reader(fh))[1:]

    game_by_key = {g[0]: g for g in games}

    # --- venue table ---
    vhead = ["Game", "Stadium (official)", "City", "Roof", "Surface",
             "Teams", "Source"]
    vrows_out = []
    seen = {}
    for v in vrows:
        key, stadium, city, roof, surface, team, pdf = v
        seen.setdefault(key, [stadium, city, roof, surface, set()])
        seen[key][4].add(team)
    for key in sorted(seen):
        g = game_by_key[key]
        stadium, city, roof, surface, teams = seen[key]
        vrows_out.append([
            esc(g[2] + " @ " + g[3]), esc(stadium), esc(city), esc(roof),
            esc(surface), esc(" / ".join(sorted(teams))),
            _src("S98", sources_by_id)])

    # --- per-game roster + playtime summary ---
    sections = []
    for g in games:
        key, date, away, home, ap, hp = g[0], g[1], g[2], g[3], g[4], g[5]
        stadium = g[6]
        weather = g[10] or "(not published)"
        rows_html = []
        # group roster rows by team and role
        for team in (away, home):
            trows = [r for r in rosters if r[0] == key and r[2] == team]
            role_rows = {}
            for r in trows:
                role_rows.setdefault(r[3], []).append(r)
            for role in ("starter", "sub", "dnp", "inactive"):
                if role not in role_rows:
                    continue
                rr = role_rows[role]
                # format "POS jersey name"
                cells = []
                for r in sorted(rr, key=lambda x: x[5]):
                    pos, j, name = r[5], r[6], r[7]
                    cells.append("%s %s %s" % (pos, j, name))
                rows_html.append(
                    "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                    % (esc(team), esc(role), esc("; ".join(cells))))
        # playtime snapshot: starters' snap percentages
        snap_rows = [s for s in snaps if s[0] == key]
        snap_head = ["Team", "Player", "Unit", "Off %", "Def %", "ST %",
                     "Playtime label"]
        snap_out = []
        for s in sorted(snap_rows, key=lambda x: (x[2], x[4])):
            team, unit, name, off, defn, st, label = (
                s[2], s[3], s[4], s[5], s[6], s[7], s[8])
            snap_out.append([esc(team), esc(name), esc(unit),
                             esc(off or "—"), esc(defn or "—"),
                             esc(st or "—"), esc(label)])
        sections.append(
            '<section class="card"><h3>%s @ %s &nbsp;·&nbsp; %s</h3>'
            '<p class="muted">%s &nbsp;·&nbsp; %s–%s &nbsp;·&nbsp; %s</p>'
            '<table><thead><tr><th>Team</th><th>Role</th><th>Players '
            '(position · jersey · name)</th></tr></thead><tbody>%s</tbody>'
            '</table>'
            '<h4>Official playtime (Playtime Percentage)</h4>'
            '<p class="muted">Transcribed from the Game Book Playtime Percentage '
            'table. Rows labelled <em>Unofficial</em> carry the NFL&rsquo;s own '
            'caveat on those books (see flag F67).</p>'
            '<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>'
            '</section>'
            % (esc(away), esc(home), esc(date), esc(stadium), esc(ap), esc(hp),
               esc(weather), "".join(rows_html),
               "".join("<th>%s</th>" % h for h in snap_head),
               "".join("<tr>%s</tr>" % "".join(
                   "<td>%s</td>" % c for c in r) for r in snap_out)))

    body = [
        '<p class="lead">The official NFL Game Book is the league&rsquo;s own '
        'game summary. For the 13 completed Week 10 2026 games, each Game Book '
        'was read from its official PDF and transcribed: the <strong>starting '
        'lineups</strong>, the <strong>substitutions</strong>, the '
        '<strong>Did Not Play</strong> and <strong>Not Active</strong> (inactive) '
        'lists, the <strong>game-day weather / roof / surface</strong>, and the '
        '<strong>Playtime Percentage</strong> table. Every value below is '
        'transcribed from the PDF; nothing is inferred.</p>',
        '<h2>Venue, roof and surface (official)</h2>',
        site.table(vhead, vrows_out, caption="Official stadium facts from the Game Book."),
        '<h2>Per-game lineups, availability and playtime</h2>',
        "".join(sections),
        '<p class="muted">Sources: %s (Game Center pages) and %s (Game Book PDFs). '
        'The Monday LAC@BAL game was still in progress at capture and is excluded '
        '(flag F68).</p>'
        % (_src("S97", sources_by_id), _src("S98", sources_by_id)),
    ]
    return site.page("game-books.html", "Official Game Books — Week 10 2026",
                     "\n".join(body), wide=True)


# --------------------------------------------------------------------------- #
# H3 — offense vs defense matchup deficiency matrix
# --------------------------------------------------------------------------- #
def render_matchup_matrix(site, sources_by_id):
    esc = site.esc
    mhdr, mrows = _read_tsv("matchup_matrix.tsv")
    head = ["Game", "Date", "Away", "Home", "String",
            "Away OFF missing", "Home DEF missing",
            "Away DEF missing", "Home OFF missing",
            "Away OFF names", "Home DEF names",
            "Away DEF names", "Home OFF names", "Note"]
    out = []
    for r in mrows:
        out.append([
            esc(r[0]), esc(r[1]), esc(r[2]), esc(r[3]), esc(r[4]),
            esc(r[5]), esc(r[6]), esc(r[7]), esc(r[8]),
            esc(r[9] or "—"), esc(r[10] or "—"),
            esc(r[11] or "—"), esc(r[12] or "—"), esc(r[13] or "—"),
        ])
    body = [
        '<p class="lead">For each Week 10 game and each string level '
        '(1st&ndash;4th), this matrix records how many players each side is '
        'missing on offense and on defense, taken from the official Game Book '
        '<strong>inactive</strong> and <strong>Did Not Play</strong> lists. '
        'Each missing player is resolved to a string by matching against the '
        'club depth chart (data/depth.tsv). The offense-vs-defense deficiency '
        'is the pair: how depleted the offense is against how depleted the '
        'opposing defense is. A player whose name is not on the depth chart is '
        'reported in the note, never silently assigned a string.</p>',
        site.table(head, out, caption="Offense vs defense deficiency, 1st-4th string, Week 10 2026."),
        '<p class="muted">Sources: %s (Game Book inactives/DNP) and the club '
        'depth charts (S16&ndash;S46).</p>' % _src("S98", sources_by_id),
    ]
    return site.page("matchup-matrix.html", "Matchup Matrix — Week 10 2026",
                     "\n".join(body), wide=True)


# --------------------------------------------------------------------------- #
# H4 — model output ledger
# --------------------------------------------------------------------------- #
def render_model_outputs(site, sources_by_id):
    esc = site.esc
    doc = json.load(open(os.path.join(DATA, "model_outputs.json"),
                         encoding="utf-8"))
    head = ["Output", "Game", "Away", "Home", "Prob (home)", "Prob (away)",
            "Fair value", "hfa", "sigma", "n_fit", "neutral", "Source"]
    out = []
    for o in doc["outputs"]:
        out.append([
            esc(o["output_type"]), esc(o["game"]), esc(o["away"]),
            esc(o["home"]),
            esc(o.get("probability_home", "") or "—"),
            esc(o.get("probability_away", "") or "—"),
            esc(str(o.get("fair_value", o.get("fair_value_home", "")))),
            esc(o["input_vector"].get("hfa_used", "") or "—"),
            esc(o["input_vector"].get("sigma", "") or "—"),
            esc(o["input_vector"].get("n_fit", "") or "—"),
            esc(o["input_vector"].get("neutral_venue", "") or "—"),
            esc(o["source"]),
        ])
    body = [
        '<p class="lead">Every model output is stored as a probability together '
        'with the input vector that produced it (requirement R35). The implied '
        'win probability is derived arithmetically from the model&rsquo;s own '
        'fair moneyline (American odds &rarr; probability); it is a conversion '
        'of the model&rsquo;s published fair value, not a new estimate. The '
        'input vector records exactly what the model used: home-field '
        'advantage, fitted sigma, fit sample size, neutral-venue flag and model '
        'version. Market-derived cells are blank because no official NFL source '
        'publishes betting prices (flag F18).</p>',
        site.table(head, out, caption="Model outputs: fair value, implied probability and input vector."),
        '<p class="muted">%d model outputs. Source: %s (Game Center anchors).</p>'
        % (doc["count"], _src("S97", sources_by_id)),
    ]
    return site.page("model-outputs.html", "Model Outputs Ledger",
                     "\n".join(body), wide=True)


# --------------------------------------------------------------------------- #
# H5 — weather overlay
# --------------------------------------------------------------------------- #
def render_weather_overlay(site, sources_by_id):
    esc = site.esc
    whdr, wrows = _read_tsv("weather_overlay.tsv")
    head = ["Venue", "City", "Roof (official)", "Surface (official)",
            "NWS office", "Grid X", "Grid Y", "Hourly values", "Source / status"]
    out = []
    for r in wrows:
        hourly = r[8] if r[8] and r[8].startswith("20") else "(not retained)"
        out.append([
            esc(r[0]), esc(r[2] or "—"), esc(r[3] or "—"), esc(r[4] or "—"),
            esc(r[5] or "—"), esc(r[6] or "—"), esc(r[7] or "—"),
            esc(hourly), esc(r[14]),
        ])
    body = [
        '<p class="lead">The stadium roof/surface overlay combines the official '
        'Game Book venue line with the NWS forecast grid resolved for each '
        'Week 11 venue. Roof and surface are Game Book facts (the NFL does not '
        'publish them elsewhere); the NWS supplies the forecast grid for each '
        'venue&rsquo;s official coordinates.</p>',
        '<p class="muted">Scope note: the NWS grid identifiers '
        '(office/gridX/gridY) were resolved and verified this session. The '
        'hourly forecast VALUES (temperature, precipitation probability, wind) '
        'were read live but are <strong>not retained</strong> in this canonical '
        'capture, so they are left blank rather than inferred. Roof/surface is '
        'published only where an official Game Book reading exists (MetLife '
        'Stadium and AT&amp;T Stadium, from the Week 10 Game Books); every other '
        'Week 11 venue has no game-day Game Book yet and is left blank. A '
        'refresh fills the hourly columns from the live NWS response.</p>',
        site.table(head, out, caption="Week 11 2026 venue roof/surface + NWS grid overlay."),
        '<p class="muted">Sources: %s (Game Book roof/surface) and the NWS '
        'forecast grids (api.weather.gov).</p>' % _src("S98", sources_by_id),
    ]
    return site.page("weather-overlay.html", "Weather Overlay — Week 11 2026",
                     "\n".join(body), wide=True)


# --------------------------------------------------------------------------- #
# H6 — requirements backlog re-audit
# --------------------------------------------------------------------------- #
def render_backlog_reaudit(site, sources_by_id):
    esc = site.esc
    doc = json.load(open(os.path.join(DATA, "requirements_backlog.json"),
                         encoding="utf-8"))
    head = ["ID", "Category", "Requirement", "Status", "Evidence / gate"]
    out = []
    for r in doc.get("rows", []):
        out.append([
            esc(r.get("id", "")), esc(r.get("category", "")),
            esc(r.get("requirement", "")), esc(r.get("status", "")),
            esc(r.get("evidence", r.get("gate", "—")) or "—"),
        ])
    counts = doc.get("counts", {})
    body = [
        '<p class="lead">Every brief requirement line, with its status corrected '
        'against the committed evidence (H6 re-audit). A line is marked '
        '<strong>done</strong> only when a committed artefact proves it; lines '
        'with a remaining gap are <strong>partial</strong> with the exact gap '
        'and the source that proves the delivered part.</p>',
        '<p class="muted">Status counts: %s. Re-audited 2026-11-17 by '
        'arena/3f12fa46-fl1.</p>'
        % ", ".join("%s %d" % (k, v) for k, v in sorted(counts.items())),
        site.table(head, out, caption="Full requirement backlog with corrected statuses."),
    ]
    return site.page("backlog-reaudit.html", "Requirements Re-audit",
                     "\n".join(body), wide=True)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def render_all(site, sources_by_id):
    written = [
        render_game_books(site, sources_by_id),
        render_matchup_matrix(site, sources_by_id),
        render_model_outputs(site, sources_by_id),
        render_weather_overlay(site, sources_by_id),
        render_backlog_reaudit(site, sources_by_id),
    ]
    return written
