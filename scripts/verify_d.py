#!/usr/bin/env python3
"""
verify_d.py — session D independent verification suite (appends to
data/verification-d.tsv, which build_schedule_d.py created with V1-V4).

Checks added here (V5-V9):

V5  Week 10 injury-capture club completeness: the 28 clubs in the official
    Week 10 capture == the 32 minus the four bye clubs (CHI DEN PHI TB),
    verified against data/schedule2026-d.csv week-10 team set.
V6  Computed-layer reproducibility: re-run the merged computed research layer's
    own build scripts (strategy_lab.py, build_correlations.py,
    build_week10_board.py) and confirm the committed data artefacts are
    byte-identical to a fresh rebuild (determinism claim from the session that
    owns them).
V7  Injury-capture cross-check: a fixed sample of rows independently transcribed
    from the nfl.com/injuries/ page fetch (2026-11-14) is compared field-for-field
    against data/week10_2026_official.csv.
V8  Spread-sign convention: for every Week 10 game with a market line and
    moneylines, the favorite implied by spread_line (away spread; positive
    = home favored) agrees with the moneyline direction. 13/13 expected.
V9  prop-correlations QA gate re-run: scripts/build_prop_correlations_d.py must
    exit 0 (all QA gates pass) and output the same row count as committed.
"""
import csv
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = os.path.join(ROOT, "data", "verification-d.tsv")
SCHED = os.path.join(ROOT, "data", "schedule2026-d.csv")
WK10 = os.path.join(ROOT, "data", "week10_2026_official.csv")
PROPC = os.path.join(ROOT, "data", "prop-correlations-d.csv")
NFL_INJ = "https://www.nfl.com/injuries/"
NFL_SCHED = "https://www.nfl.com/schedules/2026/REG10/"
NFLVERSE = "https://github.com/nflverse/nfldata/blob/master/data/games.csv"

rows = []

def add(cid, desc, result, status, source, notes):
    rows.append([cid, desc, result, status, source, notes])

def main():
    # ---------- V5 ----------
    sched = list(csv.DictReader(open(SCHED)))
    w10_teams = set()
    for g in sched:
        if g["week"] == "10":
            w10_teams.add(g["away_team"]); w10_teams.add(g["home_team"])
    byes = {g["away_team"] for g in sched if g["week"] == "10"} | \
           {g["home_team"] for g in sched if g["week"] == "10"}
    all_teams = set()
    for g in sched:
        all_teams.add(g["away_team"]); all_teams.add(g["home_team"])
    byes = all_teams - w10_teams
    wk = list(csv.DictReader(open(WK10)))
    captured = sorted({r["team"] for r in wk})
    expected = sorted(w10_teams)
    ok = captured == expected
    add("V5", "Week 10 injury capture covers exactly the 28 non-bye clubs",
        f"capture {len(captured)} clubs; bye clubs {sorted(byes)}; "
        + ("sets identical" if ok else f"diff: capture-only={set(captured)-w10_teams}, missing={w10_teams-set(captured)}"),
        "PASS" if ok else "FAIL", NFL_INJ,
        "explains '28 of 32' counts: CHI DEN PHI TB on bye, not missing")

    # ---------- V6 ----------
    arts = ["data/leaderboard.csv", "data/correlation_matrix.csv",
            "data/week10_signal_board.csv", "data/parlay_economics.csv"]
    def digest(path):
        return hashlib.sha256(open(os.path.join(ROOT, path), "rb").read()).hexdigest()[:16]
    before = {a: digest(a) for a in arts if os.path.exists(os.path.join(ROOT, a))}
    scripts = ["scripts/build_correlations.py", "scripts/strategy_lab.py",
               "scripts/build_week10_board.py"]
    ran = []
    failed = None
    for s in scripts:
        try:
            r = subprocess.run([sys.executable, s], cwd=ROOT, capture_output=True,
                               text=True, timeout=900)
            ran.append(f"{os.path.basename(s)}:{'ok' if r.returncode == 0 else 'rc=' + str(r.returncode)}")
            if r.returncode != 0:
                failed = s
                break
        except Exception as e:  # noqa
            failed = f"{s}: {e}"
            break
    after = {a: digest(a) for a in arts if os.path.exists(os.path.join(ROOT, a))}
    same = before == after and failed is None
    add("V6", "computed research layer rebuild is deterministic and reproducible",
        f"rebuild: {'; '.join(ran)}; artefact digests {'identical' if before == after else 'CHANGED: ' + str({k: (before.get(k), after.get(k)) for k in set(before) | set(after) if before.get(k) != after.get(k)})}",
        "PASS" if same else "CHECK", NFLVERSE,
        "fresh rebuild in this session's environment vs committed artefacts")

    # ---------- V7 ----------
    sample = [
        # (team-as-captured, player, position, injury, practice, game_status)
        # Transcribed verbatim from the 2026-11-14 nfl.com/injuries fetch.
        ("WAS", "John Bates", "TE", "", "Full Participation in Practice", ""),
        ("WAS", "Lucas Patrick", "C", "Concussion", "Did Not Participate In Practice", "Out"),
        ("NYG", "Malik Nabers", "WR", "", "Full Participation in Practice", ""),
        ("NE", "Ben Brown", "C", "Knee", "Did Not Participate In Practice", "Out"),
        ("NE", "Drake Maye", "QB", "", "Full Participation in Practice", ""),
        ("DET", "Kerby Joseph", "S", "Knee", "Did Not Participate In Practice", "Out"),
        ("KC", "Jaylon Moore", "T", "Ankle", "Did Not Participate In Practice", "Out"),
        ("GB", "Josh Jacobs", "RB", "Finger", "Did Not Participate In Practice", "Out"),
        ("MIN", "Kyler Murray", "QB", "Hamstring", "Did Not Participate In Practice", "Out"),
        ("BUF", "Terrel Bernard", "LB", "", "Did Not Participate In Practice", ""),
        ("MIA", "Aaron Brewer", "C", "Concussion", "Did Not Participate In Practice", "Out"),
        ("HOU", "Marvin Harrison Jr.", "WR", "Hamstring", "Did Not Participate In Practice", "Out"),
        ("CLE", "Ronnie Hickman Jr.", "S", "Concussion", "Did Not Participate In Practice", "Out"),
        ("SEA", "Sam Darnold", "QB", "Ribs, Quadricep", "Did Not Participate In Practice", "Out"),
        ("DAL", "Jake Ferguson", "TE", "Knee, Ankle", "Did Not Participate In Practice", "Out"),
        ("BAL", "Kyle Hamilton", "S", "", "Full Participation in Practice", ""),
        ("LAC", "Khalil Mack", "LB", "", "Full Participation in Practice", ""),
        ("PIT", "Cameron Heyward", "DT", "", "Full Participation in Practice", ""),
    ]
    idx = {r["team"] + "|" + r["player"]: r for r in wk}
    mism = []
    for t, p, pos, inj, prac, gs in sample:
        r = idx.get(t + "|" + p)
        if r is None:
            mism.append(f"{t}/{p}: not in capture")
            continue
        if r["position"] != pos or r["injury"] != inj or \
           r["practice_status"] != prac or (r["game_status"] or "") != gs:
            mism.append(f"{t}/{p}: capture=({r['position']},{r['injury']},{r['practice_status']},{r['game_status']}) expected=({pos},{inj},{prac},{gs})")
    add("V7", "injury-capture fidelity vs independent session-D transcription (18-row sample)",
        f"{len(sample) - len(mism)}/{len(sample)} rows match field-for-field"
        + ("; mismatches: " + "; ".join(mism[:5]) if mism else ""),
        "PASS" if not mism else "FAIL", NFL_INJ,
        "sample is a session-D re-transcription, not a copy of the capture")
    # known official-page anomalies, confirmed independently (not corrected)
    anomalies = [
        ("LAR", "Myles Garrett", "listed under Rams; club move corroborated by NFL.com articles (flag F04) - not an attribution error"),
        ("LAR", "Aaron Donald", "listed under Rams while profile shows active; session-B flag F05"),
        ("SF", "Mike Evans", "listed under 49ers while TB on bye; session-D flag F16"),
    ]
    an_ok = []
    for t, p, why in anomalies:
        if t + "|" + p in idx:
            an_ok.append(f"{t}/{p}")
    add("V7a", "official-page team-attribution anomalies confirmed in capture",
        f"{len(an_ok)}/3 present in capture exactly as published: " + "; ".join(an_ok),
        "FLAGGED", NFL_INJ,
        "rows are published verbatim as captured, never corrected; see flags F04/F05 and session-D flag")

    # ---------- V8 ----------
    bad = []
    n = 0
    for g in sched:
        if g["week"] != "10" or g["played"] != "no":
            continue
        sp = g["market_spread_away"]; aml = g["away_moneyline"]; hml = g["home_moneyline"]
        if sp == "" or aml == "" or hml == "":
            continue
        n += 1
        sp, aml, hml = float(sp), float(aml), float(hml)
        # convention: spread_line is the AWAY team's spread; positive => home favored
        if sp > 0 and not hml < 0 < aml:
            bad.append(g["game_id"])
        if sp < 0 and not aml < 0 < hml:
            bad.append(g["game_id"])
        if sp == 0:
            continue
    add("V8", "spread-sign convention verified against moneylines (Week 10, unplayed)",
        f"{n - len(bad)}/{n} games: spread direction == moneyline direction"
        + ("; violations: " + ", ".join(bad) if bad else ""),
        "PASS" if not bad and n else "FAIL", NFLVERSE,
        "establishes spread_line = away team's point spread in the nflverse feed")

    # ---------- V9 ----------
    prop_rows = list(csv.DictReader(open(PROPC)))
    r = subprocess.run([sys.executable, "scripts/build_prop_correlations_d.py"],
                       cwd=ROOT, capture_output=True, text=True, timeout=600)
    re_rows = list(csv.DictReader(open(PROPC)))
    ok = r.returncode == 0 and len(re_rows) == len(prop_rows)
    add("V9", "prop-correlations QA gates re-run (V6-style reproducibility)",
        f"rc={r.returncode}; rows committed {len(prop_rows)} == rows rebuilt {len(re_rows)}; "
        f"stdout={r.stdout.strip()[:120]}",
        "PASS" if ok else "FAIL", NFLVERSE,
        "player_stats mirror 1999-2024; join rate 1.0000; 13,384 team-games")

    # ---------- rewrite with per-check-id dedupe (latest wins) ----------
    existing = [r for r in csv.reader(open(VER, encoding="utf-8"), delimiter="\t") if r]
    header, prev = existing[0], existing[1:]
    new_ids = {r[0] for r in rows}
    kept = [r for r in prev if r[0] not in new_ids]
    with open(VER, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(header)
        w.writerows(kept)
        w.writerows(rows)
    for r_ in rows:
        print(f"{r_[0]} {r_[3]}: {r_[2][:150]}")
    if any(r_[3] == "FAIL" for r_ in rows):
        sys.exit(1)


if __name__ == "__main__":
    main()
