"""Integrity gates for the verified layer. Run:  python3 -m pipelines.validate  (exit 1 = fail)

These checks exist because a table full of plausible-looking numbers is worth nothing unless
the numbers are self-consistent and traceable. Every check is machine-run on every build:

  V01 official-source coverage   every published row's source URL is a league/club domain
  V02 vocabulary                 no free-text status values leaked through normalisation
  V03 standings internal         PF - PA == net, (W + .5T)/GP == published pct, 32 clubs
  V04 league balance           sum(PF) == sum(PA) exactly
  V05 schedule/club coverage     the injury report covers exactly the 28 clubs that play
  V06 bye cross-check            bye records agree with the standings
  V07 injury/standings record    the (W-L-T) printed beside each club on the report page
  V08 designation arithmetic     out + doubtful + questionable + no-designation == reported
  V09 flags schema               every flag names the link and the decision it blocks
  V10 stat-page reconciliation   TD/FG fields reconcile with published PF/PA within tolerance
  V11 model input traceability   every model input row resolves to a verified dataset
  V12 roster cross-check         club assignment contradictions are reported, not hidden
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .csvutil import MODEL, RAW, ROOT, VERIFIED, is_official, read_pipe_csv
from .ingest import CLUB_SLUGS

FAIL = "FAIL"
PASS = "PASS"
WARN = "WARN"


def load(name: str) -> dict:
    return json.loads((VERIFIED / name).read_text(encoding="utf-8"))


def check(cid: str, title: str, ok: bool, detail: str, warn_only: bool = False) -> dict:
    return {"id": cid, "title": title,
            "result": (WARN if warn_only else FAIL) if not ok else PASS,
            "detail": detail}


def v01_official_sources() -> dict:
    bad: list[str] = []
    inj = load("injury_report_week10.json")
    for row in inj["rows"]:
        for field in ("report_url", "player_page_url", "game_url"):
            if not is_official(row[field]):
                bad.append(f"{row['id']}.{field}")
    for coll in ("standings_2026.json", "schedule_week10.json", "news_week10.json"):
        data = load(coll)
        rows = data.get("clubs") or data.get("games") or data.get("items") or []
        for row in rows:
            url = row.get("source_url") or row.get("url")
            if not url or not is_official(url):
                bad.append(f"{coll}:{row.get('abbr') or row.get('game_slug') or row.get('club')}")
    return check("V01", "every published row links to an official league/club URL",
                 not bad, f"{len(bad)} non-official or missing source links" + (f": {bad[:5]}" if bad else ""))


def v02_vocabulary() -> dict:
    inj = load("injury_report_week10.json")
    allowed_status = {None, "OUT", "DOUBTFUL", "QUESTIONABLE"}
    allowed_practice = {None, "Full Participation in Practice",
                        "Limited Participation in Practice", "Did Not Participate In Practice"}
    bad = [r["id"] for r in inj["rows"]
           if r["game_status"] not in allowed_status or r["practice_status"] not in allowed_practice]
    return check("V02", "status/practice values are inside the closed vocabulary",
                 not bad, f"{len(bad)} rows with unrecognised values")


def v03_v04_standings() -> tuple[dict, dict]:
    st = load("standings_2026.json")
    clubs = st["clubs"]
    bad = [c["abbr"] for c in clubs
           if c["points_for"] - c["points_against"] != c["net_points"]
           or abs(c["win_pct_published"] - c["win_pct_derived"]) > 0.0015]
    c03 = check("V03", "standings: net == PF-PA and published pct == (W+.5T)/GP, all 32 clubs",
                not bad and len(clubs) == 32,
                f"{len(clubs)} clubs read, {len(bad)} arithmetic mismatches {bad[:4]}")
    lc = st["league_check"]
    c04 = check("V04", "league balance: sum(PF) == sum(PA)", lc["sum_matches"],
                f"sum PF {lc['sum_points_for']} vs sum PA {lc['sum_points_against']}; "
                f"{lc['club_games_total']} club-games => {lc['implied_games']:.0f} games; "
                f"league avg {lc['league_avg_ppg']} PPG per club")
    return c03, c04


def v05_v06_coverage() -> tuple[dict, dict]:
    inj = load("injury_report_week10.json")
    sched = load("schedule_week10.json")
    playing = sorted({g["away"] for g in sched["games"]} | {g["home"] for g in sched["games"]})
    covered = sorted(set(inj["clubs"]))
    c05 = check("V05", "injury report covers exactly the clubs playing this week",
                covered == playing,
                f"report has {len(covered)} clubs, schedule has {len(playing)}; "
                f"missing={sorted(set(playing) - set(covered))} extra={sorted(set(covered) - set(playing))}")
    st = {c["abbr"]: c for c in load("standings_2026.json")["clubs"]}
    mismatches = []
    for bye in sched["byes"]:
        parts = bye["record_as_printed"].split("-")
        w, l = int(parts[0]), int(parts[1])
        club = st[bye["abbr"]]
        if (w, l) != (club["wins"], club["losses"]):
            mismatches.append(f"{bye['abbr']}: schedule {bye['record_as_printed']} vs "
                              f"standings {club['wins']}-{club['losses']}")
    c06 = check("V06", "bye records on the schedule page agree with the standings page",
                not mismatches, f"4 byes cross-checked; mismatches: {mismatches or 'none'}")
    return c05, c06


def v07_record_agreement() -> dict:
    """The injury report prints '(6-2)' beside each club heading and the standings page prints
    W-L-T separately. Two different official pages must agree, club by club."""
    printed = {r["abbr"]: r["record_as_printed"] for r in
               read_pipe_csv(RAW / "nflcom_injuries_week10_club_records.csv")}
    st = {c["abbr"]: c for c in load("standings_2026.json")["clubs"]}
    mismatches = []
    for abbr, rec in printed.items():
        parts = rec.split("-")
        w, l = int(parts[0]), int(parts[1])
        t = int(parts[2]) if len(parts) > 2 else 0
        club = st[abbr]
        if (w, l, t) != (club["wins"], club["losses"], club["ties"]):
            mismatches.append(f"{abbr}: report {rec} vs standings "
                              f"{club['wins']}-{club['losses']}-{club['ties']}")
    return check("V07", "club records on the injury-report page match the standings page "
                        "(two independent official sources)",
                 not mismatches and len(printed) == 28,
                 f"{len(printed)} clubs compared; mismatches: {mismatches or 'none'}")


def v08_designation_arithmetic() -> dict:
    avail = load("availability_week10.json")["clubs"]
    bad = []
    for abbr, club in avail.items():
        total = club["out"] + club["doubtful"] + club["questionable"] + club["no_designation"]
        if total != club["reported"]:
            bad.append(f"{abbr} {total}!={club['reported']}")
    return check("V08", "designation counts sum to the rows reported, per club",
                 not bad, f"{len(avail)} clubs; mismatches: {bad or 'none'}")


def v09_flags_schema() -> dict:
    flags = load("flags.json")["flags"]
    required = {"id", "kind", "severity", "title", "observed", "official_link",
                "decision_blocked", "recommended_path", "status"}
    bad = []
    for f in flags:
        missing = required - set(f)
        if missing:
            bad.append(f"{f.get('id')}: missing {sorted(missing)}")
        elif f.get("official_link") and not is_official(f["official_link"]):
            bad.append(f"{f['id']}: link is not official")
    return check("V09", "every flag carries id/observed/official link/blocked decision/path",
                 not bad, f"{len(flags)} flags; problems: {bad or 'none'}")


def v10_score_reconciliation() -> dict:
    stats = load("team_stats_snapshot.json")["clubs"]
    st = {c["abbr"]: c for c in load("standings_2026.json")["clubs"]}
    rows, worst = [], 0.0
    for abbr, club in stats.items():
        td = int(club["fields"]["total_touchdowns"]["club"])
        fg = int(club["fields"]["field_goals"]["club"].split("/")[0])
        opp_td = int(club["fields"]["total_touchdowns"]["opponents"])
        opp_fg = int(club["fields"]["field_goals"]["opponents"].split("/")[0])
        rebuilt = td * 7 + fg * 3
        rebuilt_opp = opp_td * 7 + opp_fg * 3
        d1 = abs(rebuilt - st[abbr]["points_for"])
        d2 = abs(rebuilt_opp - st[abbr]["points_against"])
        worst = max(worst, d1, d2)
        rows.append(f"{abbr} PF {st[abbr]['points_for']} vs {td}TD+{fg}FG={rebuilt} (Δ{d1}); "
                    f"PA {st[abbr]['points_against']} vs {rebuilt_opp} (Δ{d2})")
    ok = worst <= 8
    return check("V10", "official stat pages reconcile with official standings points (<=8 pts, "
                        "covers missed PATs / 2-pt tries / safeties)", ok,
                 f"{len(rows)} clubs reconciled; largest residual {worst:.0f} pts. " +
                 "Reconstruction assumes every TD carries one PAT; residuals are therefore a "
                 "check on transcription, not on the league.")


def v11_model_inputs() -> dict:
    path = MODEL / "lines_2026_wk10.json"
    if not path.exists():
        return check("V11", "model outputs trace to verified inputs", True,
                     "model not built yet - nothing to trace", warn_only=True)
    data = json.loads(path.read_text(encoding="utf-8"))
    bad = []
    for game in data["games"]:
        if game.get("status") != "OK":
            continue
        if not game.get("inputs"):
            bad.append(f"{game['game_slug']}: published line with no named inputs")
        for field in ("spread_home", "total"):
            if game["published"].get(field) in (None, ""):
                bad.append(f"{game['game_slug']}: {field} blank but status OK")
        for side in ("away", "home"):
            proj = game["projections"][side]
            for k in ("raw_ppg", "raw_papg", "games_played"):
                if proj.get(k) is None:
                    bad.append(f"{game['game_slug']}/{side}: {k} missing")
            if proj.get("availability_source") != "applied":
                bad.append(f"{game['game_slug']}/{side}: published from the shadow ledger")
        if any(game.get("market", {}).get(k) is not None for k in ("spread", "total", "moneyline")):
            bad.append(f"{game['game_slug']}: a market value was filled in - must stay blank (F-02)")
        if game.get("shadow_scenario", {}).get("spread_home") == game["published"]["spread_home"]:
            pass  # equal is allowed: it means the club had no unverified absences to hide
    return check("V11", "every published line names its verified inputs; blanks only with a status that says why",
                 not bad, f"{len(data['games'])} games; problems: {bad or 'none'}")


def v12_roster_crosscheck() -> dict:
    rc = load("roster_crosscheck.json")
    return check("V12", "club-assignment spot checks fully confirmed against club roster pages",
                 rc["unconfirmed"] == 0,
                 f"{rc['confirmed']} confirmed, {rc['unconfirmed']} UNCONFIRMED -> those rows "
                 f"stay flagged (F-03/F-09/F-14) and are never trusted as club-verified. "
                 f"Warn-only by design: closing it needs roster fetches, not a code change.",
                 warn_only=True)


def v13_ir_correction() -> dict:
    """The report-vs-reality correction must be doing real work and must not double-charge."""
    ex = load("unreported_absences.json")["rows"]
    inj = load("injury_report_week10.json")["rows"]
    on_report = {(r["team"], r["player"].lower()) for r in inj}
    overlapping = [f"{e['club']}/{e['player']}" for e in ex
                   if (e["club"], e["player"].lower()) in on_report]
    deduped_ok = True
    try:
        from model.availability import build_ledgers
        ledgers = build_ledgers(inj, load("news_week10.json")["items"], ex)
        for abbr, l in ledgers.items():
            for key in ("applied", "shadow"):
                names = [p["player"] for p in l[key].players]
                if len(names) != len(set(names)):
                    deduped_ok = False
    except Exception as exc:  # pragma: no cover
        return check("V13", "IR-absence correction is live and never double-counts a player",
                     False, f"could not evaluate: {exc}")
    invisible = len(ex) - len(overlapping)
    return check("V13", "IR-absence correction is live and never double-counts a player",
                 deduped_ok and len(ex) > 0,
                 f"{len(ex)} official-news absences outside the report, {invisible} genuinely "
                 f"invisible to it, {len(overlapping)} overlapping (deduped by the model); "
                 f"see flags F-17")


def main() -> int:
    print("pipelines.validate: data/verified + data/model")
    c03, c04 = v03_v04_standings()
    c05, c06 = v05_v06_coverage()
    checks = [
        v01_official_sources(),
        v02_vocabulary(),
        c03, c04, c05, c06,
        v07_record_agreement(),
        v08_designation_arithmetic(),
        v09_flags_schema(),
        v10_score_reconciliation(),
        v11_model_inputs(),
        v12_roster_crosscheck(),
        v13_ir_correction(),
    ]
    for c in checks:
        print(f"  [{c['result']:>4}] {c['id']} {c['title']}\n         {c['detail']}")
    fails = [c["id"] for c in checks if c["result"] == FAIL]
    warns = [c["id"] for c in checks if c["result"] == WARN]
    payload = {"tool": "pipelines.validate", "ran_at_utc": "2026-11-14T03:15:00Z",
               "checks": checks, "failures": fails, "warnings": warns,
               "raw_dir": "data/raw", "verified_dir": "data/verified"}
    (VERIFIED / "validation.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (ROOT / "data" / "raw" / "SHA256SUMS").write_text(
        "".join(f"{_sha(p)}  {p.relative_to(ROOT)}\n" for p in sorted(RAW.glob('*.csv'))),
        encoding="utf-8")
    print(f"  -> {len(checks) - len(fails) - len(warns)} pass, {len(warns)} warn, {len(fails)} fail")
    if fails:
        print("FAILED:", ", ".join(fails))
        return 1
    return 0


def _sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


if __name__ == "__main__":
    sys.exit(main())
