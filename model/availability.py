"""Availability -> points, with the applied/shadow split that keeps an unverified input out of
the published number.

Two ledgers per club per game:
  applied  officially confirmed absences only (news_week10.json) - moves the line
  shadow   every OUT/DOUBTFUL row on the official report - shows the size of the unverified
           signal so a human can see what is being left on the table, without the model
           pretending to know who starts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .config import PARAMS, POSITION_IMPACT, prob_for


def _prob(status: str | None) -> float:
    return prob_for(status)


@dataclass
class Ledger:
    """Points impact of one club's absences, split by side of the ball."""
    offence: float = 0.0
    defence: float = 0.0
    special_teams: float = 0.0
    players: list[dict] = field(default_factory=list)
    position_absence_counts: dict = field(default_factory=dict)

    @property
    def total(self) -> float:
        return self.offence + self.defence + self.special_teams

    def as_dict(self) -> dict:
        return {"offence_points": round(self.offence, 3), "defence_points": round(self.defence, 3),
                "special_teams_points": round(self.special_teams, 3), "total_points": round(self.total, 3),
                "position_absence_counts": dict(self.position_absence_counts),
                "players": self.players}


def _add(ledger: Ledger, row: dict, weight_scale: float = 1.0) -> None:
    prob = _prob(row.get("game_status"))
    if prob <= 0.0:
        return
    # Diminishing returns within a position group: 1.0 for the first absence, then the declared
    # factor for each further one. `seen` is carried on the ledger so the rule is stateless
    # across clubs and impossible to apply twice to the same player.
    seen = ledger.position_absence_counts
    grp = row["position_group"]
    nth = seen.get(grp, 0)
    seen[grp] = nth + 1
    impact = POSITION_IMPACT[grp].value * (1.0 if nth == 0 else PARAMS["subsequent_depth_factor"].value)
    target = {"offense": ledger.offence, "defense": ledger.defence,
              "special_teams": ledger.special_teams}[row["unit"]]
    amount = impact * prob * weight_scale
    if row["unit"] == "offense":
        ledger.offence += amount
    elif row["unit"] == "defense":
        ledger.defence += amount
    else:
        ledger.special_teams += amount
    ledger.players.append({
        "player": row["player"], "position": row["position"], "unit": row["unit"],
        "game_status": row.get("game_status"), "injury": row.get("injury"),
        "absence_probability": round(prob, 2),
        "points_impact": round(amount, 3),
        "starter_confirmation": row.get("starter_confirmation", "unverified"),
        "source_url": row.get("report_url"), "player_page_url": row.get("player_page_url"),
    })


def build_ledgers(injury_rows: list[dict], news_rows: list[dict],
                  extra_absences: list[dict] | None = None) -> dict[str, dict]:
    """Return {abbr: {"applied": Ledger, "shadow": Ledger, "unverified_player_count": n}}.

    `news_rows` is used only to decide who is *confirmed*; it never changes a magnitude, so a
    missing news item costs precision rather than injecting an invented one.
    """
    confirmed: list[dict] = []
    for item in news_rows:
        if item.get("confirms") in {"starter_replacement", "starter_absence"}:
            confirmed.append(item)

    # Name-level confirmation: the official headline text names the absent player, so match on
    # the surname token that appears in both strings. Deliberately conservative - if a name is
    # not in a headline, the row stays in the shadow ledger.
    def is_confirmed(club: str, player: str) -> dict | None:
        for item in confirmed:
            if item["club"].upper() != club:
                continue
            text = (item["headline_exactly_as_printed"] + " " + item["confirmed_fact"]).lower()
            surname = player.split()[-1].strip(".,").lower()
            if len(surname) >= 4 and surname in text:
                return item
        return None

    out: dict[str, dict] = {}
    for row in injury_rows:
        club = out.setdefault(row["team"], {"applied": Ledger(), "shadow": Ledger(),
                                            "unverified_player_count": 0,
                                            "game_slug": row["game_slug"]})
        shadow_row = dict(row)
        _add(club["shadow"], shadow_row)
        hit = is_confirmed(row["team"], row["player"])
        if hit:
            confirmed_row = dict(row)
            confirmed_row["starter_confirmation"] = f"official news: {hit['url']}"
            _add(club["applied"], confirmed_row)
        else:
            club["unverified_player_count"] += 1

    def already_counted(club_name: str, player: str) -> bool:
        """A player can appear on both sources (report + news). He may only be charged once."""
        ledgers = out.get(club_name)
        if not ledgers:
            return False
        for key in ("applied", "shadow"):
            for p in ledgers[key].players:
                if p["player"].lower() == player.lower():
                    return True
        return False

    for extra in (extra_absences or []):
        if already_counted(extra["club"], extra["player"]):
            continue
        row = {
            "player": extra["player"], "position": extra["pos"], "position_group": extra["position_group"],
            "unit": extra["unit"], "game_status": "OUT", "injury": extra["absence_as_stated"],
            "starter_confirmation": f"{extra['basis']} - {extra['news_url']}",
            "report_url": extra["news_url"], "player_page_url": "https://www.nfl.com/search/?query=" + extra["player"].replace(" ", "-"),
            "note": "not present on the weekly report; added from the official news item",
        }
        club = out.setdefault(extra["club"], {"applied": Ledger(), "shadow": Ledger(),
                                               "unverified_player_count": 0, "game_slug": ""})
        _add(club["applied"], row)
        _add(club["shadow"], row)
    return out


def net_availability(own: dict, opp: dict, *, applied: bool) -> float:
    """Points adjustment to ONE club's expected score.

        E_team += -own_offence_loss + opponent_defence_loss

    Own missing starters depress own scoring. Opponent's missing defenders inflate it. The
    opponent's missing *attackers* are handled when the opponent's own projection is built - they
    must NOT be credited to this team, and that is precisely what makes the two teams'
    adjustments asymmetric. An earlier symmetric version here could only ever move a spread and
    never a total, which is the wrong shape for the question being asked.
    """
    key = "applied" if applied else "shadow"
    mine, theirs = own[key], opp[key]
    return -mine.offence + theirs.defence


def presence_probability(points_of_deficit: float, sigma_game: float) -> float:
    """Small helper used by the gate runner: probability a unit is *not* materially degraded,
    treating the deficit as a normal shock. Kept here so no other module re-derives it."""
    return 0.5 * (1.0 + math.erf(-points_of_deficit / (sigma_game * math.sqrt(2.0))))
