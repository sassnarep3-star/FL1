#!/usr/bin/env python3
"""H4 — model output ledger: every model output as a probability + input vector.

Requirement R35: every model output must be stored as a probability together
with the input vector that produced it.

This builder reads the model line outputs already produced by the repo's line
origination engine (data/model_lines.tsv) and writes data/model_outputs.json.
Each entry stores:

  * output_type  — which market the model priced (side / total / moneyline);
  * game         — the game the output is for;
  * probability  — the implied win probability the model's fair line encodes,
                   computed from the fair moneyline (American odds -> probability);
  * fair_value   — the model's fair number (spread / total / ML) itself;
  * input_vector — the exact inputs the model used: home-field advantage,
                   fitted sigma, fit sample size, neutral-venue flag, and the
                   model version;
  * source       — the official Game Center URL the game is anchored to.

Nothing is invented: a cell the model did not publish stays blank, and the
implied probability is derived arithmetically from the model's own fair
moneyline (a conversion, not a new estimate). Market-derived cells are left
blank because no official NFL source publishes betting prices (flag F18).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
IN = os.path.join(DATA, "model_lines.tsv")
OUT = os.path.join(DATA, "model_outputs.json")


def american_to_prob(odds):
    """American odds -> implied probability (no vig adjustment)."""
    if odds == "":
        return None
    try:
        o = float(odds)
    except ValueError:
        return None
    if o > 0:
        return round(100.0 / (100.0 + o), 4)
    return round(-o / (100.0 - o), 4)


def main():
    with open(IN, encoding="utf-8") as fh:
        rows = [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]
    header, data = rows[0], rows[1:]
    idx = {h: i for i, h in enumerate(header)}

    outputs = []
    for r in data:
        game_id = r[idx["week"]] + "-" + r[idx["date"]] + "-" + \
            r[idx["away"]] + "@" + r[idx["home"]]
        kickoff = r[idx["kickoff_et"]]
        away = r[idx["away"]]
        home = r[idx["home"]]
        neutral = r[idx["neutral_venue"]]
        hfa = r[idx["hfa_used"]]
        sigma = r[idx["sigma"]]
        n_fit = r[idx["n_fit"]]
        src = r[idx["source_url"]]
        # implied probabilities from the fair moneylines
        p_home = american_to_prob(r[idx["ml_fair_home"]])
        p_away = american_to_prob(r[idx["ml_fair_away"]])
        entries = [
            {
                "output_type": "side",
                "game": game_id,
                "away": away, "home": home, "kickoff_et": kickoff,
                "neutral_venue": neutral,
                "probability_home": p_home,
                "probability_away": p_away,
                "fair_value": r[idx["side_fair_home_spread"]],
                "input_vector": {
                    "hfa_used": hfa, "sigma": sigma, "n_fit": n_fit,
                    "neutral_venue": neutral,
                    "model_version": "line-origination v1 (fair line only)",
                },
                "source": src,
            },
            {
                "output_type": "total",
                "game": game_id,
                "away": away, "home": home, "kickoff_et": kickoff,
                "neutral_venue": neutral,
                "probability": None,  # a total is not a win probability
                "fair_value": r[idx["total_fair"]],
                "input_vector": {
                    "sigma": sigma, "n_fit": n_fit,
                    "model_version": "line-origination v1 (fair line only)",
                },
                "source": src,
            },
            {
                "output_type": "moneyline",
                "game": game_id,
                "away": away, "home": home, "kickoff_et": kickoff,
                "neutral_venue": neutral,
                "probability_home": p_home,
                "probability_away": p_away,
                "fair_value_home": r[idx["ml_fair_home"]],
                "fair_value_away": r[idx["ml_fair_away"]],
                "input_vector": {
                    "hfa_used": hfa, "sigma": sigma, "n_fit": n_fit,
                    "neutral_venue": neutral,
                    "model_version": "line-origination v1 (fair line only)",
                },
                "source": src,
            },
        ]
        outputs.extend(entries)

    doc = {
        "id": "model_outputs",
        "title": "Model output ledger — every model output as a probability + input vector",
        "requirement": "R35",
        "updated": "2026-11-17",
        "note": ("Each entry stores the model's fair value, the implied win "
                 "probability derived arithmetically from the fair moneyline, "
                 "and the exact input vector (hfa, sigma, n_fit, neutral "
                 "venue, model version) that produced it. Market cells are "
                 "blank: no official NFL source publishes betting prices "
                 "(flag F18)."),
        "count": len(outputs),
        "outputs": outputs,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    n_prob = sum(1 for o in outputs if o.get("probability_home") is not None
                 or o.get("probability") is not None)
    print("model_outputs.json: %d outputs, %d with a derived probability"
          % (len(outputs), n_prob))


if __name__ == "__main__":
    main()
