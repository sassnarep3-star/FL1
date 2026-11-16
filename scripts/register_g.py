#!/usr/bin/env python3
"""
register_g.py — session `arena/dbf11de0-fl1` (task G6).

Appends this session's registers: new official sources, new flags, new open
questions and new suggestions. Nothing already registered is modified or removed
— every earlier session's rows stay exactly as they were.

Every source added here was READ in this session. The note says what the page
said. A source that could not be loaded would be registered as NOT VERIFIED and
would never be cited as fact.

Run:  python3 scripts/register_g.py
No third-party packages.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# ------------------------------------------------------------------- sources
# (id, title, publisher, url, tier, checked, status, note)
SOURCES = [
    ("S70", "NFL.com news roundup, Wednesday Nov. 11 2026 (DEPTH CHART NEWS and Wednesday practice designations)",
     "NFL.com (National Football League)",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11",
     "Official (league)", "2026-11-16", "VERIFIED",
     "Loaded in full (4 chunks). Carries a per-club 'DEPTH CHART NEWS' section that names announced starters: Carson Beck (ARI) will start Sunday against the Rams per head coach Mike LaFleur; Deshaun Watson (CLE) will start Sunday against the Texans, the team announced Wednesday; Harrison Butker (KC) will continue to handle kicking duties per Andy Reid; Kevin O'Connell (MIN) said it is 'too early' to commit to Kirk Cousins. Also carries Wednesday practice designations for 28 clubs — a third dated read of the same week, earlier than either injury-report capture."),
    ("S71", "Drew Lock (elbow/oblique) has no injury designation, will start for Seahawks vs. Raiders",
     "NFL.com (National Football League)",
     "https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders",
     "Official (league)", "2026-11-16", "VERIFIED",
     "Loaded in full. Quoted: 'Drew Lock has no injury designation and will start Sunday for the Seahawks against the host Las Vegas Raiders, coach Mike Macdonald said Friday.' Also states 'Jalen Milroe will be Seattle's backup.' Dated by the surrounding rail to Friday Nov. 13."),
    ("S72", "Dolphins place QB Malik Willis (groin) on injured reserve; Kyle McCord in line for first start",
     "NFL.com (National Football League)",
     "https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start",
     "Official (league)", "2026-11-16", "VERIFIED",
     "Loaded in full. Quoted: 'Willis was placed on injured reserve Tuesday due to a groin injury. With Willis shelved, second-year quarterback Kyle McCord will fill in, beginning Sunday on the road against the Indianapolis Colts.' Confirms that Willis's absence from the weekly injury report means injured reserve, not health."),
]

FLAGS = [
    dict(id="F43", kind="Cross-source contradiction",
         item="Week 10 injury row count: the review says 254 rows published against 279 live; both of this session's official reads are larger",
         detail=("An earlier review recorded the published injury table as 254 rows and the live "
                 "page as 279 rows, with four 'no injuries reported' sections. This session read "
                 "the same official URL twice: the 2026-11-14 capture in the repository parses to "
                 "345 rows across 28 clubs, and a fresh 2026-11-16 re-capture parses to 347 rows "
                 "across the same 28 clubs, with no 'no injuries reported' section on the page in "
                 "either read. Both raw captures are committed with sha256 hashes so the "
                 "discrepancy can be re-checked line by line. No number was altered to make the "
                 "figures agree."),
         sourceIds=["S01"], severity="Medium",
         action="Both dated captures published on the Snapshot Ledger page with their hashes; the diff between them is published too. The 254/279 figures could not be reproduced and are left as recorded, not corrected."),
    dict(id="F44", kind="Not found in an official source",
         item="Announced-starter evidence for Brissett (Arizona) — named in the brief, not found on any official page read",
         detail=("The brief lists Brissett among the starters the NFL has announced. The dated "
                 "official roundup of 2026-11-11 announces Carson Beck as Arizona's Week 10 "
                 "starter, and Brissett appears on neither the Week 10 injury report nor any "
                 "article read this session. The cell is left blank on the Announced Starters "
                 "page with this reason, rather than filled from a depth chart or from memory."),
         sourceIds=["S70"], severity="Low",
         action="Row published blank with the reason and the source link. If an official page naming Brissett exists, the fix is to add the link."),
    dict(id="F45", kind="Source changed between two dated reads",
         item="The official Week 10 injury report is not a single fact: it moved between 2026-11-14 and 2026-11-16",
         detail=("Re-reading nfl.com/injuries two days later returned 347 rows where the earlier "
                 "read had 345. Two rows were added (BAL Calais Campbell, BAL Ronnie Stanley) and "
                 "32 fields moved. 22 of the 32 are Chargers rows: Los Angeles played on Monday "
                 "night, so its game-day designations were published after the earlier read. "
                 "Indianapolis's Arden Key moved the other way — Questionable with a hamstring "
                 "injury on 11-14, no designation at all on 11-16."),
         sourceIds=["S01"], severity="Medium",
         action="The 2026-11-14 read is kept as the pre-kickoff snapshot and is never overwritten; the later read is published beside it with a diff. Backtests must pin the capture they used."),
    dict(id="F46", kind="Coverage gap",
         item="The depth-chart register carries no capture date on 31 of 31 rows",
         detail=("data/depth-sources.tsv records club, source id and URL for 31 clubs, but its "
                 "chartDate column is empty on every row. Without a capture date, a depth chart "
                 "cannot be checked for staleness against the roster events the brief asks us to "
                 "track, and two captures of the same chart are indistinguishable."),
         sourceIds=["S08"], severity="Medium",
         action="Register left as-is with the gap stated; filling the column is requirement R62 on the backlog. No date was invented."),
    dict(id="F47", kind="Data provenance",
         item="Venue, roof and surface are captured only from a third-party feed; the official transcription covers 1 of 272 fixtures",
         detail=("data/schedule2026-d.csv carries stadium, roof and surface for all 272 games, "
                 "but every one of those rows is attributed to a third-party aggregation. The "
                 "official schedule transcription in data/schedule.tsv has a venue on 1 row of "
                 "272 (the Munich international game). The brief asks for the venue to be "
                 "transcribed from the official game centre."),
         sourceIds=["S04", "S47"], severity="Medium",
         action="Third-party venue fields are recorded in the store with their provenance label and are not presented as official. Official transcription is requirement R43 on the backlog."),
    dict(id="F48", kind="Model provenance",
         item="Published model outputs record a line, not a probability with its input vector",
         detail=("The brief asks that every model output be stored as a probability plus the "
                 "inputs that produced it. The current origination artefacts store a fair line "
                 "and a difference column, and the fair column is blank because the model is "
                 "unfitted (F38). Even when fitted, a line without its input vector cannot be "
                 "audited or reproduced after the fact."),
         sourceIds=["S02", "S03"], severity="Medium",
         action="Recorded as requirement R35 on the backlog with the schema change it needs. No output was retro-fitted to look complete."),
]

QUESTIONS = [
    dict(id="Q35", category="Data", priority="High",
         question="Which dated read of the injury report is the canonical pre-kickoff snapshot for backtests?",
         why_it_matters=("This session proved the report moves: two reads two days apart differ by "
                         "two rows and 32 fields. A backtest that trains on the Monday read has "
                         "seen designations that did not exist before kickoff, which is lookahead "
                         "leakage and will flatter any availability strategy."),
         what_we_know=("Two dated captures exist (2026-11-14, 345 rows; 2026-11-16, 347 rows), both "
                       "hash-pinned. The Chargers played Monday night, so their game-day "
                       "designations only exist in the later read."),
         what_we_dont_know=("Which read is closest to the information available before each game "
                            "kicked off, and therefore which one a backtest is allowed to use."),
         missing_data="A rule, written before the backtest runs, pinning the capture per game.",
         source="availability-ledger.html",
         blocking="Yes",
         recommended_path=("Pin the last read taken strictly before that game's kickoff, per game, "
                           "and record the capture hash on every backtest row. Never use a later "
                           "read for an earlier kickoff.")),
    dict(id="Q36", category="Data", priority="Medium",
         question="Should designations published after the earlier read be back-filled into the published table, or kept as a separate dated snapshot?",
         why_it_matters=("Back-filling makes one tidy table that no longer corresponds to anything "
                         "the league published at a single moment. Keeping separate snapshots is "
                         "less tidy but is the only version that can be audited."),
         what_we_know=("The 2026-11-14 read is the pre-kickoff snapshot for 13 of the 14 Week 10 "
                       "games and predates the Chargers' designations entirely."),
         what_we_dont_know="Whether the site's readers need one table or the series.",
         missing_data="A presentation decision, not data.",
         source="availability-ledger.html",
         blocking="No",
         recommended_path="Keep the snapshots separate and publish the diff, as the ledger page does now."),
    dict(id="Q37", category="Operations", priority="Medium",
         question="May the injury report be captured at the Wednesday/Thursday/Friday cadence the brief asks for, before the terms question is answered?",
         why_it_matters=("Three requirements (R32, R41, R73) depend on a multi-day series. None can "
                         "be met without automated repeated fetching, and the acceptable-use "
                         "question (Q18) is still open."),
         what_we_know=("The page publishes a season and week selector and returns the full report; "
                       "two manual reads were taken this session without incident."),
         what_we_dont_know="The terms of use for automated fetching, and the acceptable cadence.",
         missing_data="A read of the site's terms, or a licensed alternative.",
         source="availability-ledger.html",
         blocking="Yes",
         recommended_path=("Answer Q18 first. Until then, capture manually at a low cadence and "
                           "keep every read, rather than automating something whose permission is "
                           "unclear.")),
    dict(id="Q38", category="Competition", priority="High",
         question="Should the leaderboard adopt the removal-of-luck numbers as its qualification bar?",
         why_it_matters=("The leaderboard ranks strategies. Without a sample-size bar it will rank "
                         "whoever had the best short run. The panel shows that 785 independent "
                         "decisions are needed to detect a 5pp edge at all, and 1,211 once six "
                         "strategies are tried."),
         what_we_know=("137 official results exist. A single NFL season offers roughly 270 "
                       "team-game decisions, which is a third of the sample needed for a 5pp edge."),
         what_we_dont_know=("Whether the competition accepts that no strategy can qualify inside "
                            "one season, or wants a lower bar with an explicit warning."),
         missing_data="A decision on the bar, frozen before any result exists (SG37).",
         source="removal-of-luck.html",
         blocking="Yes",
         recommended_path=("Adopt the panel's numbers as the qualification bar, publish n on every "
                           "row, and let the leaderboard stay empty until something clears it.")),
]

SUGGESTIONS = [
    dict(id="SG35", title="Publish a weekly 'what changed' diff instead of a static snapshot",
         category="Site",
         problem=("The site publishes the injury report as one table. This session showed the "
                  "official page moves between reads: two days, two added rows, 32 moved fields. "
                  "A static table hides exactly the movement the availability signal depends on."),
         proposal=("Publish, every week, a diff between consecutive dated reads: rows added, rows "
                   "removed, and each field that moved, with both capture hashes on the page."),
         evidence=("availability-ledger.html; data/injury_diff_g.tsv (35 change records between "
                   "2026-11-14 and 2026-11-16)."),
         effort="Low", risk="Very low", reversibility="Fully reversible",
         prerequisites=["Q36"],
         options=["Diff published weekly for the whole league. (Recommended)",
                  "Diff published only for clubs with a moved designation.",
                  "Keep the static table and store the series privately."],
         recommendation="A. The diff is the product; the table is just the latest frame.",
         impact="Turns the injury layer from a snapshot into the series the brief asks for (R80, R74)."),
    dict(id="SG36", title="Promote the two dated captures into a scheduled, append-only ledger",
         category="Data",
         problem=("Two captures exist only because a session took them by hand. The brief asks for "
                  "Wednesday, Thursday and Friday reads with retained hashes; nothing in the "
                  "repository schedules that."),
         proposal=("Add a scheduled job that appends each read to an append-only store with its "
                   "sha256 and UTC timestamp, and alerts when a read does not arrive or when the "
                   "page's schema changes."),
         evidence="data/raw/MANIFEST-g.json; .github/workflows/refresh.yml (currently refreshes a third-party games feed only).",
         effort="Medium", risk="Low", reversibility="Fully reversible",
         prerequisites=["Q37"],
         options=["Scheduled append-only capture with hashes and an alert. (Recommended)",
                  "Manual capture each week, stored with hashes.",
                  "Wait for a licensed feed and skip official capture."],
         recommendation="A, once Q37 is answered. Until then, option B.",
         impact="Makes R41, R48, R49 and R73 achievable instead of aspirational."),
    dict(id="SG37", title="Adopt the removal-of-luck thresholds as the leaderboard's qualification bar",
         category="Competition",
         problem=("The leaderboard has a ranking rule but no sample-size bar, so a short lucky run "
                  "would top it. The luck panel publishes what the bar would have to be."),
         proposal=("Freeze a qualification rule now: a strategy is ranked only with n decisions at "
                   "or above the panel's requirement for the edge it claims, with the "
                   "multiplicity adjustment applied for the number of entries tried, and with n "
                   "published on every row."),
         evidence="removal-of-luck.html; engine/luck.py; data/luck_panel.json.",
         effort="Low", risk="Low", reversibility="Fully reversible until the first result lands",
         prerequisites=["Q38"],
         options=["Adopt 785 (5pp edge, unadjusted) and 1,211 (adjusted for six entries) as published. (Recommended)",
                  "Adopt a lower bar with a warning badge on every qualifying row.",
                  "Set no bar and rank whatever appears."],
         recommendation="A. Option C is how a lottery gets mistaken for a method.",
         impact="Converts 'remove luck' from a slogan into a gate that can be checked (R57, R78)."),
    dict(id="SG38", title="Add random-pick and favourites-only controls to every leaderboard run",
         category="Competition",
         problem=("Every registered strategy is a candidate and none is a control, so a candidate "
                  "can only be compared against other candidates. The brief asks for controls "
                  "explicitly."),
         proposal=("Add two control rows to the register — one that picks at random, one that "
                   "always takes the favourite — scored with the same proper score as the "
                   "candidates, and require a candidate to beat both."),
         evidence="data/strategies.json (six strategies, none is a control); removal-of-luck.html.",
         effort="Low", risk="Very low", reversibility="Fully reversible",
         prerequisites=[],
         options=["Both controls in every run, candidates must beat both. (Recommended)",
                  "Random control only.",
                  "No controls; rely on the fair-line baseline alone."],
         recommendation="A. A control costs nothing and is the cheapest lie detector available.",
         impact="Closes requirement R76 and gives every future result something to be compared against."),
]


def main():
    # ------------------------------------------------------------ sources.tsv
    spath = os.path.join(DATA, "sources.tsv")
    with open(spath, encoding="utf-8") as fh:
        existing = fh.read()
    with open(spath, "a", encoding="utf-8") as fh:
        if not existing.endswith("\n"):
            fh.write("\n")
        for s in SOURCES:
            fh.write("\t".join(s) + "\n")
    print("sources.tsv: appended %d rows (now S01-S%02d)" % (len(SOURCES), 69 + len(SOURCES)))

    # ---------------------------------------------------------- json registers
    for name, rows in (("flags", FLAGS), ("questions", QUESTIONS),
                       ("suggestions", SUGGESTIONS)):
        path = os.path.join(DATA, name + ".json")
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        have = {r["id"] for r in data}
        added = 0
        for r in rows:
            if r["id"] in have:
                print("  %s %s already present — skipped" % (name, r["id"]))
                continue
            data.append(r)
            added += 1
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        print("%s.json: %d -> %d rows (+%d)" % (name, len(data) - added, len(data), added))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
