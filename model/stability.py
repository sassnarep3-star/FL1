"""Gate G8 evidence: how much does the published line move when a prior moves?

A model whose output swings more from its own assumptions than from the data is not a model,
it is a coin with extra steps. This re-runs the whole Week 10 origination with each prior moved
+/-20% and reports the largest line shift plus how stable the set of signalled sides is.

Run:  python3 -m model.stability
"""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

from . import config
from .originate import originate_game, load_verified

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "model" / "stability.json"

PERTURBED = ["shrink_to_mean", "home_field", "sigma_game_points"]
FACTOR = 0.20


def _run(standings, ledgers, games, lg) -> list[dict]:
    return [originate_game(g, standings, ledgers, lg, applied=True) for g in games]


def main() -> int:
    data = load_verified()
    standings = {c["abbr"]: c for c in data["standings_2026"]["clubs"]}
    from .availability import build_ledgers
    extras = json.loads((ROOT / "data" / "verified" / "unreported_absences.json")
                        .read_text(encoding="utf-8"))["rows"]
    ledgers = build_ledgers(data["injury_report_week10"]["rows"], data["news_week10"]["items"], extras)
    games = [g for g in data["schedule_week10"]["games"] if not g["result_as_printed"]]
    lg = data["standings_2026"]["league_check"]["league_avg_ppg"]

    original = _run(standings, ledgers, games, lg)
    base_spreads = {g["game_slug"]: g["published"]["spread_home"] for g in original}
    base_totals = {g["game_slug"]: g["published"]["total"] for g in original}
    base_fav = {g["game_slug"]: (g["home"] if g["published"]["spread_home"] < 0 else g["away"])
                for g in original}

    results, max_shift = [], 0.0
    saved = copy.deepcopy(config.PARAMS)
    for key in PERTURBED:
        base = config.PARAMS[key].value
        for delta in (-FACTOR, +FACTOR):
            value = round(base * (1 + delta), 6)
            config.PARAMS[key] = replace(config.PARAMS[key], value=value)
            try:
                run = _run(standings, ledgers, games, lg)
            finally:
                config.PARAMS[key] = saved[key]
            spread_shifts = [abs(r["published"]["spread_home"] - base_spreads[r["game_slug"]]) for r in run]
            total_shifts = [abs(r["published"]["total"] - base_totals[r["game_slug"]]) for r in run]
            fav_flip = sum(1 for r in run
                           if (r["home"] if r["published"]["spread_home"] < 0 else r["away"])
                           != base_fav[r["game_slug"]])
            overlap = round(1.0 - fav_flip / len(run), 4)
            results.append({
                "param": key, "perturbation_pct": delta * 100.0, "value_used": value,
                "max_spread_shift_pts": round(max(spread_shifts), 3),
                "max_total_shift_pts": round(max(total_shifts), 3),
                "mean_spread_shift_pts": round(sum(spread_shifts) / len(spread_shifts), 3),
                "signalled_side_flips": fav_flip, "games": len(run),
                "signal_set_overlap": overlap,
            })
            max_shift = max(max_shift, max(spread_shifts))

    worst_overlap = min(r["signal_set_overlap"] for r in results)
    verdict = {
        "gate": "G8",
        "threshold": "line shift <= 0.5 pts and signal overlap >= 0.80 under +/-20% of each prior",
        "observed": f"max spread shift {max_shift:.2f} pts; worst signal overlap {worst_overlap:.2f}",
        "result": "PASS" if max_shift <= 0.5 and worst_overlap >= 0.80 else
                  ("FAIL" if max_shift > 1.0 else "HOLD"),
        "interpretation": (
            "sigma_game_points moves probabilities but not the published line, so the spread "
            "shift comes from shrink_to_mean and home_field. A FAIL here would mean the slate's "
            "lines are a product of the priors rather than of the standings."),
    }
    payload = {"dataset": "Parameter-stability sweep (gate G8 evidence)",
               "method": f"re-run every eligible game with each prior moved {FACTOR * 100:.0f}%",
               "sweeps": results, "verdict": verdict}
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {OUT.relative_to(ROOT)}")
    print(f"  G8 -> {verdict['result']}: {verdict['observed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
