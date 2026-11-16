#!/usr/bin/env python3
"""
build_availability_g.py — session `arena-dbf11de0-fl1` (tasks G5 and G6).

G5  Per-team availability view: starters out, replacement named, net injury
    count — one row per club, every number computed from two official sources:
      * the club's own published (and self-described "unofficial") depth chart,
        which names the ORDER of players at each slot;
      * the league's official Week 10 injury report, which says who is Out.

G6  Announced-starter evidence. The brief asks for an announced-starter field
    that is NOT an inferred replacement. NFL.com publishes dated starter
    announcements in its daily news roundups ("DEPTH CHART NEWS") and in
    standalone articles. Each row here is a quotation from one of those pages
    with its URL and its publication date. Where no announcement was found the
    row is left blank and flagged — a blank is not an inference.

Every derived column states the rule that produced it, in the data and on the
page. Nothing is filled in from a guess.

Run:  python3 scripts/build_availability_g.py
Writes: data/team_availability.csv, data/starters_out_detail.csv,
        data/announced_starters.csv, data/announced_starters.json
No third-party packages.
"""

import csv
import json
import os
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INJ_URL = "https://www.nfl.com/injuries/"

# Announced-starter announcements, each QUOTED from the linked official page.
# quote is verbatim; date is the date the page states or implies for the remark.
ANNOUNCED = [
    dict(team="ARI", player="Carson Beck", pos="QB", slot="QB",
         status="Announced starter",
         quote='QB Carson Beck will start Sunday\'s game against the Rams, per head coach '
               'Mike LaFleur. This will be Beck\'s first career start in the NFL after he '
               'was selected in the third round of the 2026 draft.',
         date="2026-11-11", kind="DEPTH CHART NEWS",
         url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"),
    dict(team="CLE", player="Deshaun Watson", pos="QB", slot="QB",
         status="Announced starter",
         quote='QB Deshaun Watson will start Sunday against the Texans, the team announced '
               'Wednesday. Watson cleared concussion protocol before Cleveland\'s Week 9 game '
               'but was inactive as Shedeur Sanders got the start in the loss to New Orleans.',
         date="2026-11-11", kind="DEPTH CHART NEWS",
         url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"),
    dict(team="KC", player="Harrison Butker", pos="K", slot="K",
         status="Confirmed in role",
         quote='K Harrison Butker will continue to handle kicking duties for Kansas City for '
               'its Week 10 game against the Falcons, head coach Andy Reid said. Butker missed '
               'a 51-yard field goal in Week 9 and is 12 of 19 on field goal attempts this '
               'season.',
         date="2026-11-11", kind="DEPTH CHART NEWS",
         url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"),
    dict(team="MIN", player="Kirk Cousins", pos="QB", slot="QB",
         status="Not committed",
         quote='Head coach Kevin O\'Connell told reporters on Wednesday that it is "too early" '
               'to commit to Kirk Cousins as their starting quarterback for Sunday\'s game '
               'against the Packers. The Vikings traded a 2027 third-round draft pick to the '
               'Raiders on Tuesday for Cousins.',
         date="2026-11-11", kind="DEPTH CHART NEWS",
         url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"),
    dict(team="SEA", player="Drew Lock", pos="QB", slot="QB",
         status="Announced starter",
         quote='Drew Lock has no injury designation and will start Sunday for the Seahawks '
               'against the host Las Vegas Raiders, coach Mike Macdonald said Friday. Lock is '
               'filling in for the injured Sam Darnold and set to make his second straight '
               'start and his third overall this season.',
         date="2026-11-13", kind="Article",
         url="https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders"),
    dict(team="SEA", player="Jalen Milroe", pos="QB", slot="QB2",
         status="Announced backup",
         quote='Jalen Milroe will be Seattle\'s backup.',
         date="2026-11-13", kind="Article",
         url="https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders"),
    dict(team="SEA", player="Sam Darnold", pos="QB", slot="QB",
         status="Ruled out",
         quote='QB Sam Darnold (ribs/quadricep) did not practice on Wednesday. Darnold has '
               'been ruled out for Sunday\'s game against the Raiders. (Official Week 10 '
               'injury report game status: Out.)',
         date="2026-11-11", kind="DEPTH CHART NEWS + injury report",
         url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"),
    dict(team="MIA", player="Kyle McCord", pos="QB", slot="QB",
         status="Announced starter",
         quote='Willis was placed on injured reserve Tuesday due to a groin injury. With '
               'Willis shelved, second-year quarterback Kyle McCord will fill in, beginning '
               'Sunday on the road against the Indianapolis Colts.',
         date="2026-11-10", kind="Article",
         url="https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start"),
    dict(team="MIA", player="Malik Willis", pos="QB", slot="QB",
         status="On injured reserve (absent from the weekly report)",
         quote='Willis was placed on injured reserve Tuesday due to a groin injury. '
               '\u2026 Willis will miss games at the Colts, at the Buffalo Bills, versus the '
               'New York Jets and at the Denver Broncos from Weeks 10-13.',
         date="2026-11-10", kind="Article",
         url="https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start"),
    dict(team="NE", player="TreVeyon Henderson", pos="RB", slot="RB",
         status="On injured reserve (listed Out on the weekly report)",
         quote='NFL news roundup: Patriots place RB TreVeyon Henderson (illness) on injured '
               'reserve.',
         date="2026-11-14", kind="News roundup headline",
         url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-saturday-nov-14"),
    dict(team="BAL", player="Lamar Jackson", pos="QB", slot="QB",
         status="On injured reserve (absent from the weekly report)",
         quote='NFL news roundup: Ravens officially place Lamar Jackson on injured reserve. '
               '(NFL Network: Lamar Jackson, right thumb, out 6-9 weeks.)',
         date="2026-11-05", kind="News roundup headline",
         url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-thursday-nov-05"),
]

# Rows the brief asked about that this session could NOT evidence.
NOT_FOUND = [
    dict(team="ARI", player="Brissett", pos="QB", slot="QB",
         note="The brief names Brissett as an announced Arizona starter. No official page "
              "read in this session names Brissett: the dated NFL.com roundup of 2026-11-11 "
              "announces Carson Beck as Arizona's starter, and Brissett does not appear on "
              "the Week 10 injury report. Left blank rather than inferred.",
         url="https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"),
]


def load_tsv(path, fields):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split("\t")
            parts += [""] * (len(fields) - len(parts))
            out.append(OrderedDict(zip(fields, parts)))
    return out


def norm(s):
    return s.lower().replace(".", "").replace("'", "").strip()


def main():
    injuries = load_tsv(os.path.join(ROOT, "data", "injuries.tsv"),
                        ["team", "player", "pos", "injury", "practice", "game"])
    teams = load_tsv(os.path.join(ROOT, "data", "teams.tsv"),
                     ["abbr", "name", "conference", "division"])
    depth = load_tsv(os.path.join(ROOT, "data", "depth.tsv"),
                     ["team", "unit", "slot", "player", "rank", "line", "note"])
    aliases = load_tsv(os.path.join(ROOT, "data", "depth-aliases.tsv"),
                       ["depthName", "reportName", "evidence"])

    team_name = {t["abbr"]: t["name"] for t in teams}
    to_report = {norm(a["depthName"]): norm(a["reportName"]) for a in aliases}

    # official status per (team, normalised report name)
    status = {}
    for r in injuries:
        status[(r["team"], norm(r["player"]))] = r

    def is_noninjury(r):
        return r["injury"].strip().lower().startswith("not injury related")

    # ------------------------------------------------------------ G5 per club
    ladders = defaultdict(list)
    for d in depth:
        if d["player"].strip():
            ladders[(d["team"], d["unit"], d["slot"], d["line"])].append(d)

    clubs_on_report = sorted({r["team"] for r in injuries})
    clubs_with_chart = sorted({d["team"] for d in depth})

    rows = []
    detail = []
    for club in clubs_on_report:
        rep = [r for r in injuries if r["team"] == club]
        out = [r for r in rep if r["game"] == "Out"]
        out_inj = [r for r in out if not is_noninjury(r)]
        doub = [r for r in rep if r["game"] == "Doubtful"]
        doub_inj = [r for r in doub if not is_noninjury(r)]
        ques = [r for r in rep if r["game"] == "Questionable"]

        # Starters out: rank-1 names on the club's own chart whose official
        # game status is Out. Derived, and labelled as derived: the club calls
        # its chart unofficial (flag F10).
        starters_out, named = [], 0
        strings = []
        if club in clubs_with_chart:
            for key, group in sorted(ladders.items()):
                if key[0] != club:
                    continue
                first = sorted({int(r["rank"]) for r in group if r["rank"].isdigit()})
                if not first or first[0] != 1:
                    continue
                for r in group:
                    if r["rank"] != "1":
                        continue
                    rep_name = to_report.get(norm(r["player"]), norm(r["player"]))
                    st = status.get((club, rep_name))
                    if st and st["game"] == "Out":
                        starters_out.append((key[1], key[2], r["player"], st))
                        # walk the club's own string order for the next name
                        # the league has not ruled Out
                        nxt, nxt_rank = "", ""
                        for k in range(2, max(first) + 1):
                            level = [x for x in group if x["rank"] == str(k)]
                            if not level:
                                break
                            cand = level[0]
                            rn = to_report.get(norm(cand["player"]), norm(cand["player"]))
                            s2 = status.get((club, rn))
                            if not (s2 and s2["game"] == "Out"):
                                nxt, nxt_rank = cand["player"], str(k)
                                break
                        if nxt:
                            named += 1
                            strings.append(nxt_rank)
                            detail.append(OrderedDict([
                                ("team", club), ("club", team_name.get(club, club)),
                                ("unit", key[1]), ("slot", key[2]),
                                ("starterOut", r["player"]),
                                ("starterInjury", st["injury"]),
                                ("starterPractice", st["practice"]),
                                ("starterGameStatus", st["game"]),
                                ("replacement", nxt),
                                ("replacementString", nxt_rank),
                                ("replacementGameStatus",
                                 (status.get((club, to_report.get(norm(nxt), norm(nxt)))) or
                                  {"game": ""})["game"]),
                                ("replacementBasis",
                                 "next name at a deeper string on the club's own published "
                                 "chart (club calls it unofficial)"),
                                ("source", "S01"),
                            ]))
                        else:
                            detail.append(OrderedDict([
                                ("team", club), ("club", team_name.get(club, club)),
                                ("unit", key[1]), ("slot", key[2]),
                                ("starterOut", r["player"]),
                                ("starterInjury", st["injury"]),
                                ("starterPractice", st["practice"]),
                                ("starterGameStatus", st["game"]),
                                ("replacement", ""),
                                ("replacementString", ""),
                                ("replacementGameStatus", ""),
                                ("replacementBasis",
                                 "the club publishes no further name on this ladder"),
                                ("source", "S01"),
                            ]))

        rows.append(OrderedDict([
            ("team", club),
            ("club", team_name.get(club, club)),
            ("listed", str(len(rep))),
            ("out", str(len(out))),
            ("doubtful", str(len(doub))),
            ("questionable", str(len(ques))),
            ("dnp", str(sum(1 for r in rep if r["practice"] == "DNP"))),
            ("nonInjury", str(sum(1 for r in rep if is_noninjury(r)))),
            ("netInjuryCount", str(len(out_inj) + len(doub_inj))),
            ("netInjuryRule",
             "report rows whose game status is Out or Doubtful, excluding rows the league "
             "marks 'Not injury related'"),
            ("chartCaptured", "yes" if club in clubs_with_chart else "no"),
            ("startersOut", str(len(starters_out)) if club in clubs_with_chart else ""),
            ("replacementsNamed", str(named) if club in clubs_with_chart else ""),
            ("replacementStrings", ",".join(sorted(set(strings))) if strings else ""),
            ("startersOutBasis",
             "derived: rank 1 on the club's own published depth chart AND Out on the official "
             "report. The club labels its chart unofficial (flag F10)."
             if club in clubs_with_chart else
             "no club depth chart captured for this club — column left blank, not inferred"),
            ("source", "S01"),
        ]))

    def write_csv(name, rows_):
        with open(os.path.join(ROOT, "data", name), "w", encoding="utf-8",
                  newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows_[0].keys()))
            w.writeheader()
            for r in rows_:
                w.writerow(r)

    write_csv("team_availability.csv", rows)
    if detail:
        write_csv("starters_out_detail.csv", detail)

    # ------------------------------------------------------------- G6 starters
    with open(os.path.join(ROOT, "data", "announced_starters.csv"), "w",
              encoding="utf-8", newline="") as fh:
        fields = ["team", "player", "pos", "slot", "status", "quote", "date",
                  "kind", "url"]
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for a in ANNOUNCED:
            w.writerow({k: a.get(k, "") for k in fields})

    payload = {
        "id": "announced_starters",
        "title": "Announced starters — official evidence, not inferred replacements",
        "note": ("Each row quotes an official NFL.com page and links it. A replacement that "
                 "no official page names is left out of this table entirely; the depth-chart "
                 "walking on the Team Availability page is labelled as derived and is not "
                 "reproduced here."),
        "updated": "2026-11-16",
        "announced": ANNOUNCED,
        "notFound": NOT_FOUND,
    }
    with open(os.path.join(ROOT, "data", "announced_starters.json"), "w",
              encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")

    print("clubs on the official report   : %d" % len(clubs_on_report))
    print("clubs with a captured chart    : %d" % len(clubs_with_chart))
    print("starters-out rows (derived)    : %d" % len(detail))
    print("  with a replacement named     : %d"
          % sum(1 for d in detail if d["replacement"]))
    print("announced-starter rows         : %d" % len(ANNOUNCED))
    print("net injury count, league total : %d"
          % sum(int(r["netInjuryCount"]) for r in rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
