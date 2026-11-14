"""All tunable constants in one place, each tagged with whether an official source backs it.

Nothing here is measured from data unless `verified=True`. That flag is not decoration: the
site renders it, `model.gates` refuses to let a strategy through a gate whose threshold is
uncalibrated, and `pipelines.build_site` publishes the whole table as the Assumptions
register. The point is that a model with hidden constants cannot be audited, and an audited
model is the only kind worth betting.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Param:
    key: str
    value: float
    unit: str
    verified: bool
    why: str
    calibrate_by: str

    @property
    def status(self) -> str:
        return "verified" if self.verified else "PRIOR - uncalibrated"


PARAMS: dict[str, Param] = {p.key: p for p in [
    Param("shrink_to_mean", 0.72, "fraction", False,
          "A club's 8-9 game scoring rate is a small sample; the additive model over-fits "
          "it at w=1.0 and under-weights real team quality at w=0.6.",
          "Fit the multiplier on 5+ seasons of closing lines (regress realised margin on "
          "pre-game PF/PA-derived rating), or on last-season-vs-this-season rate change."),
    Param("home_field", 1.4, "points", False,
          "Standard NFL home advantage magnitude. Cannot be measured from the data this repo "
          "holds because the standings page's home/road columns are unmappable (flag F-07).",
          "Derive from official per-game logs: mean(home_score - away_score) over >=500 games."),
    Param("sigma_game_points", 12.0, "points", False,
          "Std dev of one team's game points; sets win probability and every parlay "
          "correlation. Needs game-level scores, which are not in this snapshot.",
          "Estimate from 3-5 seasons of official box scores; check against realised margin sd."),
    Param("prob_out_is_absent", 1.00, "probability", True,
          "The official report publishes OUT as a game designation, so treating it as absent "
          "is what the source says, not an assumption.",
          "n/a - definition, not estimate"),
    Param("prob_doubtful_absent", 0.60, "probability", False,
          "Doubtful is a club statement of low probability of playing, not a rule-out.",
          "Realise from the official inactive lists for the same week (how often a Doubtful "
          "player in fact did not play)."),
    Param("prob_questionable_absent", 0.30, "probability", False,
          "Questionable players play roughly two thirds of the time; the exact figure moves "
          "with the day of the week and the sport's rules.",
          "Realise from the official inactive lists, split by Wed/Thu/Fri designation."),
    Param("subsequent_depth_factor", 0.25, "multiplier", False,
          "Only the FIRST absence at a position costs the full weight. The player replacing the "
          "replacement is closer in level to the replacement than the replacement was to the "
          "starter, so each further absence at the same position is charged at a fraction. "
          "Without this rule, losing a franchise QB and his backup costs twice the points that "
          "losing the franchise QB alone costs - which is obviously not how a roster works.",
          "Regress realised points on (n_absent_starters_at_position) for each position."),
    Param("key_number_cushion", 0.0, "points", True,
          "No adjustment applied. Key-number rounding is a market artefact and belongs to the "
          "line-comparison layer, which is empty until an odds feed exists (flag F-02).",
          "n/a - blocked on F-02"),
] }

POSITION_IMPACT: dict[str, Param] = {p.key: p for p in [
    Param("qb", 3.5, "pts/g", False,
          "Starting-QB quality is the largest single-player effect on team scoring.",
          "Regress team points on an indicator for 'named starter unavailable, next named "
          "replacement starts', 5+ seasons."),
    Param("backfield", 1.8, "pts/g", False, "Every-down lead back.", "same"),
    Param("skill_position", 1.2, "pts/g", False, "Top wide receiver / tight end.", "same"),
    Param("offensive_line", 0.9, "pts/g", False,
          "Per-olinelman; note it must be summed across the unit because line absences stack.",
          "same, with the unit total as the dependent variable"),
    Param("edge", 1.5, "pts/g", False, "Primary pass rusher, affects opponent scoring too.", "same"),
    Param("interior_dl", 0.8, "pts/g", False, "Run-defence anchor.", "same"),
    Param("linebacker", 1.0, "pts/g", False, "Middle-of-field defender.", "same"),
    Param("corner", 1.2, "pts/g", False, "Island defender; larger in coverage-man schemes.", "same"),
    Param("safety", 0.9, "pts/g", False, "Deep-half / centre-field error correction.", "same"),
    Param("secondary_other", 0.4, "pts/g", False, "Nickel/rookie-depth filler.", "same"),
    Param("special_teams", 0.1, "pts/g", False, "Near zero for spread/total purposes.", "same"),
] }

def prob_for(status: str | None) -> float:
    """Probability the player misses the game, per the declared priors above."""
    if status == "OUT":
        return PARAMS["prob_out_is_absent"].value
    if status == "DOUBTFUL":
        return PARAMS["prob_doubtful_absent"].value
    if status == "QUESTIONABLE":
        return PARAMS["prob_questionable_absent"].value
    return 0.0  # no designation published -> no absence may be assumed (flag F-13)


APPLY_POLICY = (
    "Availability adjustments are APPLIED only where an official NFL.com news item names the "
    "replacement or confirms the absence (data/verified/news_week10.json, confirms column). "
    "Every other row is reported as a SHADOW adjustment - computed, displayed, never applied - "
    "because with no depth chart (flag F-01) 'is this player a starter' is unverifiable."
)
