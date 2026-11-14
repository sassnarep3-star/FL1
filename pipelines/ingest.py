"""Turn the hand-checked raw snapshots in data/raw/ into the JSON the site and model consume.

Run:  python3 -m pipelines.ingest

Design rules enforced here:
  * A blank in the source stays a blank here. Nothing is defaulted to 0 or "n/a".
  * Every row carries the official URL(s) it was read from, so the site can render a
    per-row source link without a reviewer re-deriving it.
  * Vocabulary is normalised against a closed set; an unexpected value raises instead of
    silently coercing, because silent coercion is how invented data enters a dataset.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .csvutil import RAW, VERIFIED, is_official, read_pipe_csv

PRACTICE_CODES = {
    "full": "Full Participation in Practice",
    "limited": "Limited Participation in Practice",
    "dnp": "Did Not Participate In Practice",
    "": None,
}
GAME_STATUSES = {"", "OUT", "DOUBTFUL", "QUESTIONABLE"}

OFFENSE = {"QB", "RB", "FB", "WR", "TE", "OT", "T", "G", "C"}
DEFENSE = {"DE", "DT", "DL", "LB", "CB", "S", "SAF", "DB"}
SPECIAL = {"K", "P", "LS"}
OL = {"T", "OT", "G", "C"}

POSITION_GROUPS = {
    "QB": "qb",
    "RB": "backfield",
    "FB": "backfield",
    "WR": "skill_position",
    "TE": "skill_position",
    "OT": "offensive_line",
    "T": "offensive_line",
    "G": "offensive_line",
    "C": "offensive_line",
    "DE": "edge",
    "DT": "interior_dl",
    "DL": "interior_dl",
    "LB": "linebacker",
    "CB": "corner",
    "S": "safety",
    "SAF": "safety",
    "DB": "secondary_other",
    "K": "special_teams",
    "P": "special_teams",
    "LS": "special_teams",
}

CLUB_SLUGS = {
    "ARI": "arizona-cardinals", "AZ": "arizona-cardinals", "ATL": "atlanta-falcons", "BAL": "baltimore-ravens",
    "BUF": "buffalo-bills", "CAR": "carolina-panthers", "CHI": "chicago-bears",
    "CIN": "cincinnati-bengals", "CLE": "cleveland-browns", "DAL": "dallas-cowboys",
    "DEN": "denver-broncos", "DET": "detroit-lions", "GB": "green-bay-packers",
    "HOU": "houston-texans", "IND": "indianapolis-colts", "JAX": "jacksonville-jaguars",
    "KC": "kansas-city-chiefs", "LA": "los-angeles-rams", "LAR": "los-angeles-rams",
    "LV": "las-vegas-raiders", "MIA": "miami-dolphins", "MIN": "minnesota-vikings",
    "NE": "new-england-patriots", "NO": "new-orleans-saints", "NYG": "new-york-giants",
    "NYJ": "new-york-jets", "PHI": "philadelphia-eagles", "PIT": "pittsburgh-steelers",
    "LAC": "los-angeles-chargers", "SF": "san-francisco-49ers", "SEA": "seattle-seahawks",
    "TB": "tampa-bay-buccaneers", "TEN": "tennessee-titans", "WAS": "washington-commanders",
}

REPORT_URL = "https://www.nfl.com/injuries/"


def unit_of(pos: str) -> str:
    if pos in OFFENSE:
        return "offense"
    if pos in DEFENSE:
        return "defense"
    if pos in SPECIAL:
        return "special_teams"
    raise ValueError(f"unknown position on the official report: {pos!r}")


def _dump(name: str, payload: dict) -> None:
    VERIFIED.mkdir(parents=True, exist_ok=True)
    path = VERIFIED / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {path.relative_to(RAW.parents[1])}")


def ingest_injuries() -> dict:
    rows = read_pipe_csv(RAW / "nflcom_injuries_week10.csv")
    out = []
    for i, r in enumerate(rows):
        practice = r["practice"].strip().lower()
        if practice not in PRACTICE_CODES:
            raise ValueError(f"injury row {i}: unknown practice status {practice!r}")
        status = r["status"].strip().upper()
        if status not in GAME_STATUSES:
            raise ValueError(f"injury row {i}: unknown game status {status!r}")
        player_url = "https://www.nfl.com" + r["player_path"]
        if not is_official(player_url):
            raise ValueError(f"injury row {i}: non-official player link {player_url}")
        out.append({
            "id": f"INJ-{i + 1:03d}",
            "game_slug": r["game_slug"],
            "team": r["team"],
            "player": r["player"],
            "position": r["pos"],
            "unit": unit_of(r["pos"]),
            "position_group": POSITION_GROUPS[r["pos"]],
            "on_offensive_line": r["pos"] in OL,
            "injury": r["injury"] or None,
            "injury_as_printed": r["injury"],
            "practice_status": PRACTICE_CODES[practice],
            "game_status": status or None,
            "designation_published": bool(status),
            "report_url": REPORT_URL,
            "player_page_url": player_url,
            "game_url": f"https://www.nfl.com/games/{r['game_slug']}",
        })
    payload = {
        "dataset": "Week 10 2026 official NFL injury report",
        "source_url": REPORT_URL,
        "source_tier": "T0 (official league source)",
        "fetched_at_utc": "2026-11-14T02:52:00Z",
        "row_count": len(out),
        "clubs": sorted({r["team"] for r in out}),
        "rows": out,
    }
    _dump("injury_report_week10.json", payload)
    return payload


def ingest_availability(injuries: dict, news: list[dict], extras: list[dict] | None = None) -> dict:
    """Club-level availability rollups + the 'who replaces them' question, answered only
    where an official news item names the replacement."""
    by_club: dict[str, dict] = {}
    for row in injuries["rows"]:
        club = by_club.setdefault(row["team"], {
            "club_abbr": row["team"], "game_slug": row["game_slug"], "rows": 0,
            "reported": 0, "out": 0, "doubtful": 0, "questionable": 0, "no_designation": 0,
            "out_offense": 0, "out_defense": 0, "out_special_teams": 0,
            "out_by_position_group": {}, "dnp_without_designation": 0,
            "confirmed_starter_absences": [], "confirmed_replacements": [],
            "source_url": "https://www.nfl.com/games/" + row["game_slug"],
            "report_url": REPORT_URL,
        })
        club["rows"] += 1
        club["reported"] += 1
        st = row["game_status"]
        if st == "OUT":
            club["out"] += 1
            key = {"offense": "out_offense", "defense": "out_defense",
                   "special_teams": "out_special_teams"}[row["unit"]]
            club[key] += 1
            grp = row["position_group"]
            club["out_by_position_group"][grp] = club["out_by_position_group"].get(grp, 0) + 1
        elif st == "DOUBTFUL":
            club["doubtful"] += 1
        elif st == "QUESTIONABLE":
            club["questionable"] += 1
        else:
            club["no_designation"] += 1
            if row["practice_status"] == "Did Not Participate In Practice":
                club["dnp_without_designation"] += 1

    for item in news:
        club = item["club"]
        if item.get("confirms") in {"starter_replacement", "starter_absence"} and club in by_club:
            by_club[club]["confirmed_replacements"].append({
                "headline": item["headline_exactly_as_printed"],
                "url": item["url"],
                "confirmed_fact": item["confirmed_fact"],
                "source_tier": "T0",
            })

    for club in by_club.values():
        club["absences_total"] = club["out"] + club["doubtful"]
        club["availability_note"] = (
            "No official depth chart exists, so 'which string starts in place of the absent "
            "player' is only answered where an official NFL.com news item names a replacement. "
            f"This club has {club['out'] + club['doubtful']} projected-absent players and "
            f"{len(club['confirmed_replacements'])} officially named replacement(s)."
        )

    for row in (extras or []):
        club = by_club.get(row["club"])
        if club is None:
            continue
        club["unreported_confirmed_absences"] = club.get("unreported_confirmed_absences", 0) + 1

    payload = {
        "dataset": "Week 10 2026 availability rollup (derived from the official injury report)",
        "derivation": "counts only; no projection, no depth assumption",
        "fetched_at_utc": injuries["fetched_at_utc"],
        "clubs": by_club,
    }
    _dump("availability_week10.json", payload)
    return payload


def ingest_standings() -> dict:
    rows = read_pipe_csv(RAW / "nflcom_standings_wk10.csv")
    out = []
    for r in rows:
        w, l, t = int(r["w"]), int(r["l"]), int(r["t"])
        games = w + l + t
        published_pct = float(r["pct"])
        derived = round((w + 0.5 * t) / games, 3)
        if abs(derived - published_pct) > 0.0015:
            raise ValueError(f"{r['abbr']}: published pct {published_pct} != (W+0.5T)/GP {derived}")
        if int(r["pf"]) - int(r["pa"]) != int(r["net"]):
            raise ValueError(f"{r['abbr']}: published net != PF - PA")
        out.append({
            "team": r["team"], "abbr": r["abbr"], "conference": r["conf"], "division": r["division"],
            "wins": w, "losses": l, "ties": t, "games_played": games,
            "win_pct_published": published_pct, "win_pct_derived": derived,
            "points_for": int(r["pf"]), "points_against": int(r["pa"]), "net_points": int(r["net"]),
            "streak_as_printed": r["strk"],
            "ppg": round(int(r["pf"]) / games, 4),
            "papg": round(int(r["pa"]) / games, 4),
            "net_ppg": round((int(r["pf"]) - int(r["pa"])) / games, 4),
            "source_url": "https://www.nfl.com/standings/?season=2026&week=10&sort=division",
            "team_page_url": f"https://www.nfl.com/teams/{CLUB_SLUGS[r['abbr']]}/",
            "unpublished_columns_note": (
                "div/home/road/conf records appear on the official page but the rendered "
                "column order could not be mapped to the Legend with certainty; not published."
            ),
        })
    total_pf = sum(r["points_for"] for r in out)
    total_pa = sum(r["points_against"] for r in out)
    total_gp = sum(r["games_played"] for r in out)
    payload = {
        "dataset": "2026 NFL standings, state through Week 9",
        "source_url": "https://www.nfl.com/standings/?season=2026&week=10&sort=division",
        "source_tier": "T0",
        "fetched_at_utc": "2026-11-14T02:53:00Z",
        "clubs": out,
        "league_check": {
            "sum_points_for": total_pf, "sum_points_against": total_pa,
            "sum_matches": total_pf == total_pa,
            "club_games_total": total_gp, "implied_games": total_gp / 2,
            "league_avg_ppg": round(total_pf / total_gp, 4),
            "league_avg_game_total_points": round(total_pf / (total_gp / 2), 4),
        },
    }
    _dump("standings_2026.json", payload)
    return payload


def ingest_schedule() -> dict:
    games = read_pipe_csv(RAW / "nflcom_schedule_wk10.csv")
    byes = read_pipe_csv(RAW / "nflcom_byes_wk10.csv")
    payload = {
        "dataset": "2026 Week 10 schedule",
        "source_url": "https://www.nfl.com/schedules",
        "source_tier": "T0",
        "fetched_at_utc": "2026-11-14T02:54:00Z",
        "games": [{
            "game_slug": g["game_slug"], "away": g["away"], "home": g["home"],
            "date": g["date"], "kickoff_et": g["kickoff_et"], "networks": g["networks"],
            "result_as_printed": g["result"] or None,
            "source_url": g["official_game_url"],
            "injury_report_url": REPORT_URL,
        } for g in games],
        "byes": [{"abbr": b["abbr"], "team": b["team"],
                  "record_as_printed": b["record_as_printed"], "source_url": b["source_url"]}
                 for b in byes],
    }
    _dump("schedule_week10.json", payload)
    return payload


def ingest_team_stats() -> dict:
    rows = read_pipe_csv(RAW / "nflcom_team_stats.csv")
    clubs: dict[str, dict] = {}
    for r in rows:
        club = clubs.setdefault(r["abbr"], {
            "abbr": r["abbr"], "club_slug": r["club"], "fields": {},
            "source_url": r["url"], "source_tier": "T0",
        })
        club["fields"][r["field"]] = {
            "club": r["col1_club"], "opponents": r["col2_opponents"],
            "note": r.get("note") or None,
        }
    payload = {
        "dataset": "Official club stat pages, VS-OPPONENTS block (partial coverage)",
        "fetched_at_utc": "2026-11-14T02:54:00Z",
        "coverage": {"clubs_published": sorted(clubs), "clubs_total": 32,
                     "clubs_unavailable": sorted(set(CLUB_SLUGS.values()) -
                                                  {c["club_slug"] for c in clubs.values()} &
                                                  set(CLUB_SLUGS.values()))},
        "clubs": clubs,
        "not_published": [
            "OFFENSE Plays / Average Yards", "RUSHING Plays / Average Yards",
            "PASSING Comp / Att / Int / Average", "TOUCHDOWNS Rushing / Passing / Returns / Defensive",
        ],
    }
    _dump("team_stats_snapshot.json", payload)
    return payload


def ingest_news() -> list[dict]:
    rows = read_pipe_csv(RAW / "nflcom_news_wk10.csv")
    out = []
    for r in rows:
        if not is_official(r["url"]):
            raise ValueError(f"news row not from an official source: {r['url']}")
        out.append({**r, "source_tier": "T0",
                    "fetched_at_utc": "2026-11-14T02:53:00Z"})
    _dump("news_week10.json", {"dataset": "Official NFL.com news items on the Week 10 report page",
                               "items": out, "row_count": len(out)})
    return out


def ingest_unreported_absences() -> list[dict]:
    """Absences real but absent from the weekly report (IR etc.), sourced to official news."""
    rows = read_pipe_csv(RAW / "nflcom_confirmed_absences_wk10.csv")
    out = []
    for r in rows:
        if not is_official(r["news_url"]):
            raise ValueError(f"absence row not sourced to an official page: {r['news_url']}")
        if r["pos"] not in POSITION_GROUPS:
            raise ValueError(f"absence row position {r['pos']!r} is not on the report vocabulary")
        out.append({**r, "source_tier": "T0",
                    "fetched_at_utc": "2026-11-14T02:53:00Z",
                    "position_group": POSITION_GROUPS[r["pos"]],
                    "unit": unit_of(r["pos"])})
    payload = {
        "dataset": "Confirmed absences missing from the weekly injury report",
        "why": "A player on IR is not submitted on the weekly report, so a report-only "
               "availability layer silently scores him as available. This file is the correction.",
        "rows": out,
        "affected_clubs": sorted({r["club"] for r in out}),
        "check": {
            "BAL_rows_on_report": 8,
            "BAL_qb_rows_on_report": 0,
            "note": "compared programmatically in pipelines.validate V13",
        },
    }
    _dump("unreported_absences.json", payload)
    return out


def ingest_roster_check() -> dict:
    rows = read_pipe_csv(RAW / "nflcom_roster_check.csv")
    payload = {
        "dataset": "Club-assignment cross-check against an official roster page",
        "fetched_at_utc": "2026-11-14T02:53:00Z",
        "checks": rows,
        "confirmed": sum(1 for r in rows if r["match"] == "YES"),
        "unconfirmed": sum(1 for r in rows if r["match"] == "UNCONFIRMED"),
    }
    _dump("roster_crosscheck.json", payload)
    return payload


def main() -> int:
    print("pipelines.ingest: data/raw -> data/verified")
    news = ingest_news()
    injuries = ingest_injuries()
    extras = ingest_unreported_absences()
    ingest_availability(injuries, news, extras)
    ingest_standings()
    ingest_schedule()
    ingest_team_stats()
    ingest_roster_check()
    return 0


if __name__ == "__main__":
    sys.exit(main())
