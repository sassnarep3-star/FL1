#!/usr/bin/env python3
"""pages_week11.py — renders week11-read.html from data/injuries_2026-11-19.tsv and
data/injury_hub_delta_w11.json. Renderer only: no value is computed or inferred here.
Every row links to the official NFL player page; the read links to the official hub.
Run: python3 tools/pages_week11.py
"""
import csv
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import importlib.util  # noqa: E402

# Load this repo's tools/site.py by path: a bare `import site` finds the stdlib module.
_spec = importlib.util.spec_from_file_location("repo_site", os.path.join(ROOT, "tools", "site.py"))
shell = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(shell)


def main():
    with open(os.path.join(ROOT, "data", "injuries_2026-11-19.tsv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    with open(os.path.join(ROOT, "data", "injury_hub_delta_w11.json"), encoding="utf-8") as f:
        doc = json.load(f)
    e = html.escape
    read = doc["reads"][0]
    flags = doc["flags"]
    body = []
    body.append('<h1>Week 11 injury-hub read (read 5)</h1>')
    body.append('<p class="lede">Official NFL injury report, Week 11 of the 2026 season, captured '
                f'{e(read["captured"])}. <a href="{e(doc["url"])}">Source: nfl.com/injuries</a> '
                f'({e(read["source_id"])}). Values are printed exactly as published; a blank cell is blank at source.</p>')
    body.append('<h2>Delta</h2>')
    body.append(f'<p>{e(doc["delta_reason"])} The level is stored in the capture; the delta page will '
                'render the change when a second Week 11 read lands.</p>')
    body.append('<h2>Summary</h2>')
    c = doc["counts"]
    body.append('<table><thead><tr><th>Measure</th><th>Count</th></tr></thead><tbody>'
                f'<tr><td>Player rows published</td><td>{read["rows"]}</td></tr>'
                f'<tr><td>Clubs with a table</td><td>{read["clubs_with_table"]}</td></tr>'
                f'<tr><td>Clubs showing "No Injuries Reported"</td><td>{e(", ".join(read["clubs_no_injuries_reported"]))}</td></tr>'
                f'<tr><td>Practice: Did Not Participate</td><td>{c["practice"].get("DNP",0)}</td></tr>'
                f'<tr><td>Practice: Limited</td><td>{c["practice"].get("LIMITED",0)}</td></tr>'
                f'<tr><td>Practice: Full</td><td>{c["practice"].get("FULL",0)}</td></tr>'
                f'<tr><td>Game status: Out</td><td>{c["game"].get("Out",0)}</td></tr>'
                f'<tr><td>Game status: Questionable</td><td>{c["game"].get("Questionable",0)}</td></tr>'
                f'<tr><td>Game status blank</td><td>{c["game"].get("blank",0)}</td></tr>'
                '</tbody></table>')
    body.append('<h2>Player rows</h2>')
    body.append('<p>Every row links to its official NFL player page. Club abbreviation is the one shown in the hub game header.</p>')
    body.append('<table><thead><tr><th>Club</th><th>Player</th><th>Pos</th><th>Injury (as published)</th>'
                '<th>Practice (as published)</th><th>Game status (as published)</th><th>Source</th></tr></thead><tbody>')
    for r in rows:
        body.append('<tr><td>%s</td><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
                    '<td><a href="%s">hub</a></td></tr>' % (
                        e(r["club_abbr"]), e(r["player_url"]), e(r["player"]), e(r["pos"]),
                        e(r["injury"]), e(r["practice_raw"]), e(r["game_raw"]) or '<span class="unv">—</span>',
                        e(r["source_url"])))
    body.append('</tbody></table>')
    body.append('<h2>Flagged for review</h2>')
    body.append('<p>Recorded, not corrected. Each item links to the official player page it concerns.</p>')
    body.append('<table><thead><tr><th>Club</th><th>Player</th><th>Issue</th><th>Link</th></tr></thead><tbody>')
    for f_ in flags:
        body.append('<tr><td>%s</td><td>%s</td><td>%s</td><td><a href="%s">player</a></td></tr>' % (
            e(f_["club"]), e(f_["player"]), e(f_["issue"]), e(f_["url"])))
    body.append('</tbody></table>')
    shell.page("week11-read.html", "Week 11 injury-hub read — NFL Line Origination",
               "\n".join(body), wide=True)
    print("wrote week11-read.html rows=%d flags=%d" % (len(rows), len(flags)))


if __name__ == "__main__":
    main()
