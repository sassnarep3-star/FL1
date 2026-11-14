"""Originate Week 10 lines from verified inputs only, and never invent a missing one.

Model (v0, "ADD-PTS"): an additive expected-points model on the official per-club scoring
rates, shrunk toward the league mean, adjusted for venue and for officially confirmed
availability losses, then expressed as a spread and a total.

    o_t = lg + s*(PPG_t - lg)          club's own scoring rate, shrunk
    d_t = lg + s*(PAPG_t - lg)         club's points allowed rate, shrunk
    E_t = o_t + d_opp - lg + venue_t + availability_t

Everything in that formula that is a *number from a page* comes from data/verified/, and
everything that is a *judgement* comes from model/config.py with verified=False. The two are
never mixed silently: the output carries `inputs` (page-backed) and `assumptions` (priors).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from .availability import build_ledgers, net_availability
from .config import APPLY_POLICY, PARAMS, POSITION_IMPACT

ROOT = Path(__file__).resolve().parents[1]
VERIFIED = ROOT / "data" / "verified"
MODEL_OUT = ROOT / "data" / "model"


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def round_half(x: float) -> float:
    return round(x * 2.0) / 2.0


def american_from_prob(p: float) -> str:
    """Fair price with no vig. This is a model output, NOT a market price - there is no
    official market source (flag F-02), so no line on any page may be read as a sportsbook quote."""
    p = min(max(p, 1e-6), 1 - 1e-6)
    dec = 1.0 / p
    return f"+{int(round((dec - 1) * 100))}" if dec >= 2.0 else f"-{int(round(100 / (dec - 1)))}"


def load_verified() -> dict:
    return {name: json.loads((VERIFIED / f"{name}.json").read_text(encoding="utf-8"))
            for name in ("standings_2026", "schedule_week10", "injury_report_week10", "news_week10")}


def originate_game(game: dict, standings: dict, ledgers: dict, lg: float, *, applied: bool) -> dict:
    away, home = standings[game["away"]], standings[game["home"]]
    s = PARAMS["shrink_to_mean"].value
    venue = PARAMS["home_field"].value
    key = "applied" if applied else "shadow"

    o = {c["abbr"]: lg + s * (c["ppg"] - lg) for c in standings.values()}
    d = {c["abbr"]: lg + s * (c["papg"] - lg) for c in standings.values()}

    adj_away = net_availability(ledgers[game["away"]], ledgers[game["home"]], applied=applied)
    adj_home = net_availability(ledgers[game["home"]], ledgers[game["away"]], applied=applied)
    ledger_away, ledger_home = ledgers[game["away"]][key], ledgers[game["home"]][key]

    e_away = o[game["away"]] + d[game["home"]] - lg + adj_away
    e_home = o[game["home"]] + d[game["away"]] - lg + venue + adj_home

    margin = e_home - e_away
    spread_home = round_half(-margin)
    total = round_half(e_home + e_away)

    sigma = PARAMS["sigma_game_points"].value
    sd_margin = math.sqrt(2.0) * sigma
    sd_total = math.sqrt(2.0) * sigma
    p_home_win = norm_cdf(margin / sd_margin)
    cover_line = -spread_home  # home points laid
    p_home_cover = norm_cdf((margin - cover_line) / sd_margin)
    p_over = norm_cdf((e_home + e_away - total) / sd_total)

    return {
        "game_slug": game["game_slug"],
        "away": game["away"], "home": game["home"],
        "date": game["date"], "kickoff_et": game["kickoff_et"],
        "networks": game["networks"], "source_url": game["source_url"],
        "projections": {
            "away": {"expected_points": round(e_away, 2), "scoring_rate_shrunk": round(o[game["away"]], 3),
                     "allowed_rate_shrunk": round(d[game["home"]], 3), "games_played": away["games_played"],
                     "raw_ppg": away["ppg"], "raw_papg": away["papg"],
                     "availability_applied_points": round(adj_away, 2),
                     "availability_source": key,
                     "injured_ledger": ledger_away.as_dict()},
            "home": {"expected_points": round(e_home, 2), "scoring_rate_shrunk": round(o[game["home"]], 3),
                     "allowed_rate_shrunk": round(d[game["away"]], 3), "games_played": home["games_played"],
                     "raw_ppg": home["ppg"], "raw_papg": home["papg"],
                     "availability_applied_points": round(adj_home, 2),
                     "availability_source": key,
                     "injured_ledger": ledger_home.as_dict()},
        },
        "published": {
            "spread_home": spread_home,
            "spread_home_text": f"{game['home']} {-spread_home:+.1f}" if spread_home else f"{game['home']} EVEN",
            "total": total,
            "projected_margin_home": round(margin, 2),
            "fair_prob_home_win": round(p_home_win, 4),
            "fair_prob_home_cover": round(p_home_cover, 4),
            "fair_prob_over": round(p_over, 4),
            "fair_american_home": american_from_prob(p_home_win),
            "fair_american_away": american_from_prob(1 - p_home_win),
            "price_note": "fair, no vig - derived from the model, NOT a sportsbook quote",
        },
        "market": {"spread": None, "total": None, "moneyline": None,
                   "edge_spread": None, "edge_total": None,
                   "reason": "No official source for market lines exists (flag F-02); "
                             "edge and CLV cannot be computed. Left blank, never filled in."},
        "status": "OK" if applied else "SHADOW",
        "inputs": {
            "scoring_rates": "data/verified/standings_2026.json <- https://www.nfl.com/standings/?season=2026&week=10&sort=division",
            "availability": "data/verified/injury_report_week10.json <- https://www.nfl.com/injuries/",
            "starter_confirmation": "data/verified/news_week10.json + data/verified/unreported_absences.json <- https://www.nfl.com/news/",
        },
        "assumptions": [
            {"key": k, "value": PARAMS[k].value, "unit": PARAMS[k].unit, "status": PARAMS[k].status}
            for k in ("shrink_to_mean", "home_field", "sigma_game_points")
        ],
    }


def main() -> int:
    data = load_verified()
    standings = {c["abbr"]: c for c in data["standings_2026"]["clubs"]}
    injuries = data["injury_report_week10"]["rows"]
    extras = json.loads((VERIFIED / "unreported_absences.json").read_text(encoding="utf-8"))["rows"]
    ledgers = build_ledgers(injuries, data["news_week10"]["items"], extras)

    # applied pass first, then attach the shadow pass for the same game
    games = data["schedule_week10"]["games"]
    done = [g for g in games if not g["result_as_printed"]]
    played = [g for g in games if g["result_as_printed"]]

    lg = data["standings_2026"]["league_check"]["league_avg_ppg"]
    out_games = []
    for game in done:
        applied = originate_game(game, standings, ledgers, lg, applied=True)
        shadow = originate_game(game, standings, ledgers, lg, applied=False)
        applied["shadow_scenario"] = {
            "spread_home": shadow["published"]["spread_home"],
            "total": shadow["published"]["total"],
            "note": "What the line would be if EVERY player the club listed as Out/Doubtful "
                    "were treated as a missing starter. Displayed to size the unverified "
                    "signal; not applied, because no depth chart confirms starter status.",
        }
        applied["availability_policy"] = APPLY_POLICY
        out_games.append(applied)

    for game in played:
        out_games.append({
            "game_slug": game["game_slug"], "away": game["away"], "home": game["home"],
            "date": game["date"], "kickoff_et": game["kickoff_et"], "networks": game["networks"],
            "source_url": game["source_url"], "status": "EXCLUDED_ALREADY_PLAYED",
            "reason": f"official page printed '{game['result_as_printed']}' before this "
                      f"pregame snapshot was taken (flag F-15)",
            "published": None, "market": {"spread": None, "total": None},
        })

    MODEL_OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset": "Week 10 2026 originated lines (model v0 ADD-PTS)",
        "generated_from": "data/verified/*.json snapshot 2026-11-14T02:52Z",
        "model_version": "v0-addpts",
        "eligibility": "research output; not a bet recommendation - no validation gate set "
                       "can pass until a market source and a multi-season corpus exist",
        "games": sorted(out_games, key=lambda g: (g["date"], g["kickoff_et"], g["game_slug"])),
        "position_impact_table": {k: {"value": p.value, "unit": p.unit, "status": p.status,
                                      "calibrate_by": p.calibrate_by}
                                  for k, p in POSITION_IMPACT.items()},
        "league_baseline": data["standings_2026"]["league_check"],
    }
    path = MODEL_OUT / "lines_2026_wk10.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}  ({len(out_games)} games, "
          f"{sum(1 for g in out_games if g.get('status') == 'OK')} originated, "
          f"{sum(1 for g in out_games if g.get('status') == 'EXCLUDED_ALREADY_PLAYED')} excluded)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
