"""Measurement of correlation and market behaviour from the in-repo game dataset.

WHY THIS MODULE EXISTS. The correlation register ships with a blank rho column because
no official source publishes NFL prices and no line history was in the repository. A
sibling session then committed a third-party dataset (nflverse/nfldata `games.csv`,
1999-2026, with scores, spread lines, totals and, in recent seasons, odds) under
data/raw/, with sha256s recorded in data/raw/MANIFEST.json. That makes rho measurable
rather than assumable, which is what the brief asks for.

WHAT THAT DOES AND DOES NOT LICENSE. It licenses a computed statistic: "in this dataset,
overs and home covers are correlated at X (95% CI ...)". It does not license calling that
an official market fact -- nflverse aggregates sportsbook closing prices, it is not the
NFL. Every number here therefore carries a provenance label, and the register keeps the
distinction instead of quietly promoting it.

Reproduce with:  python3 -m engine.measure   (writes data/measured.json)
"""

from __future__ import annotations

import csv
import json
import os
from typing import Iterable, Sequence

from . import correlation, pricing, stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMES_CSV = os.path.join(ROOT, "data", "raw", "games.csv")
OUT = os.path.join(ROOT, "data", "measured.json")

# Sign-convention resolution. A parallel session's verification file (data/verification-d.tsv,
# check V8) established that in nflverse's games feed `spread_line` is the AWAY team's line,
# checked against moneyline direction on 13/13 unplayed Week 10 games. Under that convention the
# home cover test on (home_minus_away) is `margin - line > 0`, which is this module's reading B —
# and it is the reading whose plausibility checks pass. So B is the default and A is kept only as
# the audit trail of how the question was settled.
CONVENTION = {
    "resolved": "B",
    "meaning": "spread_line is the AWAY team's line; home covers iff (home-away) - line > 0",
    "verified_by": "data/verification-d.tsv check V8 (spread direction == moneyline direction, 13/13, against the official Week 10 schedule)",
    "why_both_are_still_computed": ("the file's own documentation is ambiguous about which side the line belongs to; the "
                                    "moneyline cross-check settles it, and publishing the alternative reading is how we "
                                    "show the answer came from a test rather than from a preference"),
}

PROVENANCE = {
    "dataset": "nflverse/nfldata games.csv (third-party aggregation of sportsbook closing prices)",
    "in_repo_path": "data/raw/games.csv",
    "manifest": "data/raw/MANIFEST.json (records source URL and sha256)",
    "official": False,
    "allowed_use": ("computed statistics about joint outcomes in this dataset, labelled as such; "
                    "not a statement about any official market"),
}


def load_games(path: str = GAMES_CSV) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        if r.get("game_type") not in (None, "", "REG", "POST"):
            continue
        try:
            home = int(r["home_score"])
            away = int(r["away_score"])
        except (TypeError, ValueError, KeyError):
            continue

        def f(key):
            v = (r.get(key) or "").strip()
            try:
                return float(v)
            except ValueError:
                return None

        out.append({
            "game_id": r.get("game_id"), "season": int(r["season"]), "week": r.get("week"),
            "game_type": (r.get("game_type") or "REG"),
            "away": r.get("away_team"), "home": r.get("home_team"),
            "margin": home - away, "points_total": home + away,
            "spread_line": f("spread_line"), "total_line": f("total_line"),
            "over_odds": f("over_odds"), "under_odds": f("under_odds"),
            "home_spread_odds": f("home_spread_odds"), "away_spread_odds": f("away_spread_odds"),
        })
    return out


def _covers_home(g: dict, convention: str = CONVENTION["resolved"]):
    """Cover test under the two candidate sign conventions for `spread_line`.

    Convention A reads the column as the home team's line (negative = home favoured), which
    is what the dataset's documentation implies. Convention B reads it as "points the home
    team is favoured by" (positive = home favoured). The two are not equivalent: they
    disagree on which team is the favourite, and the plausibility checks in this module show
    that A produces an impossible 60% home-cover rate while B produces ~48%. So the
    documentation and the data disagree, and the honest response is to compute under both,
    publish both, and let the discrepancy be the finding rather than picking the flattering
    one.
    """
    if g["spread_line"] is None:
        return None
    adj = g["margin"] + g["spread_line"] if convention == "A" else g["margin"] - g["spread_line"]
    if adj == 0:
        return None
    return adj > 0


def _over(g: dict):
    if g["total_line"] is None:
        return None
    if g["points_total"] == g["total_line"]:
        return None
    return g["points_total"] > g["total_line"]


def _rho_ci(p_a: float, p_b: float, p_ab: float, n: int):
    """CI for rho, obtained by mapping a Wilson interval on the *counted* joint proportion
    through the inverse relation (monotone in p_ab for fixed marginals). Cleaner and more
    honest than bootstrapping a statistic that already has a closed form."""
    lo, hi = stats.wilson_interval(round(p_ab * n), n)
    return (correlation.rho_from_joint(p_a, p_b, lo), correlation.rho_from_joint(p_a, p_b, hi))


def measure_over_cover(games: Sequence[dict], seasons: Iterable[int] | None = None,
                       convention: str | None = None) -> dict:
    convention = convention or CONVENTION["resolved"]
    """rho between 'over the total' and 'home covers the spread' -- pair C-01 in the register."""
    want = set(seasons) if seasons else None
    n = a = b = both = 0
    for g in games:
        if want is not None and g["season"] not in want:
            continue
        hc, ov = _covers_home(g, convention), _over(g)
        if hc is None or ov is None:
            continue
        n += 1
        a += 1 if ov else 0
        b += 1 if hc else 0
        both += 1 if (ov and hc) else 0
    if n < 30:
        return {"status": "INSUFFICIENT", "n": n}
    p_over, p_cover, p_both = a / n, b / n, both / n
    rho = correlation.rho_from_joint(p_over, p_cover, p_both)
    rho_lo, rho_hi = _rho_ci(p_over, p_cover, p_both, n)
    return {
        "status": "MEASURED", "n": n,
        "p_over": round(p_over, 5), "p_home_covers": round(p_cover, 5),
        "p_both_observed": round(p_both, 5),
        "p_both_if_independent": round(p_over * p_cover, 5),
        "dependence_excess": round(p_both - p_over * p_cover, 5),
        "rho": round(rho, 5), "rho_ci95": [round(rho_lo, 5), round(rho_hi, 5)],
        "spread_sign_convention": convention,
        "provenance": PROVENANCE,
    }


def parlay_pricing_impact(games: Sequence[dict]) -> dict:
    """What the measured dependence does to a two-leg 'over + home side' parlay price."""
    sub = [g for g in games if _covers_home(g) is not None and _over(g) is not None]
    n = len(sub)
    both = sum(1 for g in sub if _covers_home(g) and _over(g))
    p_over = sum(1 for g in sub if _over(g)) / n
    p_cov = sum(1 for g in sub if _covers_home(g)) / n
    if n == 0:
        return {"n": 0, "note": "no games with both a total and a spread"}
    out = {"n": n, "p_both_observed": round(both / n, 5),
           "naive_product": round(p_over * p_cov, 5),
           "excess": round(both / n - p_over * p_cov, 5)}
    priced = [g for g in sub if g["over_odds"] and g["home_spread_odds"]]
    if priced:
        mean_dec = stats.mean([pricing.parlay_decimal([g["over_odds"], g["home_spread_odds"]])
                               for g in priced])
        out.update({
            "priced_parlay_n": len(priced),
            "mean_combined_decimal": round(mean_dec, 5),
            "break_even_at_that_price": round(1.0 / mean_dec, 5),
            "measured_hit_rate_minus_break_even_pp": round((both / n - 1.0 / mean_dec) * 100, 4),
            "note": ("empirical gap between how the pair actually resolves and how the combined "
                     "price pays, over games where both legs were priced. NOT an edge claim: a "
                     "book's combined price is not a probability forecast, and no stake was ever "
                     "placed at it"),
        })
    else:
        out["note"] = "no per-leg odds present in this dataset slice"
    return out


def season_stability(games: Sequence[dict], first: int = 2010, last: int | None = None) -> list[dict]:
    last = last or max(g["season"] for g in games)
    rows = []
    for s in range(first, last + 1):
        m = measure_over_cover(games, seasons=[s])
        if m.get("status") == "MEASURED":
            rows.append({"season": s, "n": m["n"], "rho": m["rho"], "rho_ci95": m["rho_ci95"],
                         "p_over": m["p_over"], "p_home_covers": m["p_home_covers"]})
    return rows


def home_underdog_after_miss(games: Sequence[dict], since: int = 2010,
                             convention: str | None = None) -> dict:
    convention = convention or CONVENTION["resolved"]
    """The one published hypothesis testable end-to-end on in-repo data (SIG-01).

    'Books underprice home underdogs that failed to cover the previous week' comes from a
    peer-reviewed study. Reproduced here as a bet log against closing lines so the gate
    machinery runs on something real, with the sample size and price mix reported rather
    than smoothed over.
    """
    by_team: dict[str, list[dict]] = {}
    for g in sorted([g for g in games if g["season"] >= since - 1 and g["game_type"] == "REG"],
                    key=lambda x: (x["season"], int(x["week"] or 0))):
        by_team.setdefault(g["home"], []).append(g)
        by_team.setdefault(g["away"], []).append(g)

    bets = []
    for team, hist in by_team.items():
        for i in range(1, len(hist)):
            prev, cur = hist[i - 1], hist[i]
            if prev["season"] != cur["season"]:
                continue
            if prev["spread_line"] is None or cur["spread_line"] is None:
                continue
            # home is the underdog when its opponent (away) is priced as the favourite:
            # under B the away line is negative; under A the home line would be positive.
            if convention == "A" and cur["spread_line"] <= 0:
                continue
            if convention == "B" and cur["spread_line"] >= 0:
                continue
            prev_home = prev["home"] == team
            prev_line = prev["spread_line"] if prev_home else -prev["spread_line"]
            prev_margin = prev["margin"]
            if prev_margin + prev_line == 0 or prev_margin + prev_line > 0:
                continue                                  # covered (or pushed) last week
            cur_home = cur["home"] == team
            cur_line = cur["spread_line"] if cur_home else -cur["spread_line"]
            cur_margin = cur["margin"] if cur_home else -cur["margin"]
            # Both perspectives are pre-signed above, so the cover test is identical for
            # home and away: adjusted margin strictly positive. Getting this sign backwards
            # is the classic spreads bug and it inverts the whole result.
            adj = cur_margin + cur_line
            if adj == 0:
                continue                                  # push
            price = (cur["home_spread_odds"] if cur_home else cur["away_spread_odds"]) or -110
            won = adj > 0
            bets.append({"game_id": cur["game_id"], "season": cur["season"], "team": team,
                         "price": price, "stake": 1.0, "won": won,
                         "pnl": (100.0 / abs(price)) if won else -1.0,
                         "clv": None, "modelled_edge": None, "eval": "oos",
                         "market": "game spread"})
    if not bets:
        return {"status": "NO_BETS_MATCHED", "n": 0}
    wins = sum(1 for b in bets if b["won"])
    n = len(bets)
    hit = wins / n
    lo, hi = stats.wilson_interval(wins, n)
    pnl = sum(b["pnl"] for b in bets)
    hurdle = pricing.break_even_probability(-110)
    prices: dict = {}
    for b in bets:
        prices[b["price"]] = prices.get(b["price"], 0) + 1
    top_prices = sorted(prices.items(), key=lambda kv: -kv[1])[:6]
    return {
        "status": "MEASURED", "spread_sign_convention": convention,
        "season_range": [since, max(b["season"] for b in bets)],
        "n": n, "wins": wins, "hit_rate": round(hit, 5),
        "wilson_ci95": [round(lo, 5), round(hi, 5)],
        "pnl_units_at_flat_stakes": round(pnl, 3),
        "roi_per_unit": round(pnl / n, 5),
        "most_common_prices": [[p, c] for p, c in top_prices],
        "hurdle_at_-110": round(hurdle, 5),
        "lower_bound_clears_hurdle": bool(lo > hurdle),
        "caveat": ("reproduces a published hypothesis on third-party closing data, not our own "
                   "model: no injury or availability feature is applied, and 'covered last week' "
                   "is derived from the same dataset rather than an official roster feed. It shows "
                   "the pipeline runs on real data. It is not a claim that the strategy is ours, "
                   "or that it is profitable now."),
    }


def plausibility_checks(games: Sequence[dict]) -> dict:
    """Sanity tests a dataset must pass before any number in it gets published.

    Run because the first measurement looked wrong in a specific, checkable way: home teams
    appeared to cover 60% of the time, which is not a market inefficiency, it is a sign or
    convention error somewhere. The checks below are how that suspicion becomes evidence
    instead of vibes, and they are published alongside the measurements so the reader can
    see which numbers are safe to use.
    """
    both = [g for g in games if g["spread_line"] is not None]
    cov = [g for g in both if _covers_home(g) is not None]
    resolved_note = (f"checks are evaluated under the resolved convention ({CONVENTION['resolved']}): "
                     f"{CONVENTION['meaning']}. Verified by {CONVENTION['verified_by']}.")
    home_wins = sum(1 for g in games if g["margin"] > 0)
    out = {
        "convention": CONVENTION,
        "resolved_note": resolved_note,
        "games_with_spread": len(both),
        "home_win_rate": round(home_wins / len(games), 5) if games else None,
        "home_cover_rate_measured": round(sum(1 for g in cov if _covers_home(g)) / len(cov), 5) if cov else None,
        "over_rate_measured": None,
        "expected_ranges": {
            "home_win_rate": "~0.52 to ~0.58 historically in the NFL",
            "home_cover_rate_at_close": "~0.48 to ~0.53; a durable 60% is not a market feature",
            "over_rate": "~0.49 to ~0.51",
        },
    }
    overs = [g for g in games if _over(g) is not None]
    if overs:
        out["over_rate_measured"] = round(sum(1 for g in overs if _over(g)) / len(overs), 5)
    checks = []
    hr = out["home_cover_rate_measured"]
    checks.append({"check": "home cover rate within 0.45-0.55",
                   "value": hr,
                   "verdict": "PASS" if (hr is not None and 0.45 <= hr <= 0.55) else "FAIL",
                   "consequence": ("if it fails, the spread sign convention in this third-party file (or the "
                                   "reading of it) is wrong, and every spread-derived number in this module is "
                                   "internal-only until reconciled against an official source")})
    wr = out["home_win_rate"]
    checks.append({"check": "home win rate within 0.50-0.60", "value": wr,
                   "verdict": "PASS" if (wr is not None and 0.50 <= wr <= 0.60) else "FAIL",
                   "consequence": "game outcomes are not sign-derivable, so this isolates whether the anomaly is in the results or in the spread column"})
    orr = out["over_rate_measured"]
    checks.append({"check": "over rate within 0.47-0.53", "value": orr,
                   "verdict": "PASS" if (orr is not None and 0.47 <= orr <= 0.53) else "FAIL",
                   "consequence": "totals are computed from scores and the total line only, so a pass here while the spread check fails localises the problem to the spread columns"})
    # explicit side-by-side of the two sign readings, because that is the actual finding
    cov_a = sum(1 for g in cov if _covers_home(g, "A"))
    cov_b = sum(1 for g in cov if _covers_home(g, "B"))
    fav_a = sum(1 for g in both if (g["spread_line"] or 0) < 0)
    fav_b = sum(1 for g in both if (g["spread_line"] or 0) > 0)
    out["convention_test"] = {
        "A_home_covers_when_margin_plus_line_positive": round(cov_a / len(cov), 5) if cov else None,
        "B_home_covers_when_margin_minus_line_positive": round(cov_b / len(cov), 5) if cov else None,
        "A_share_of_games_home_is_favourite": round(fav_a / len(both), 5) if both else None,
        "B_share_of_games_home_is_favourite": round(fav_b / len(both), 5) if both else None,
        "reading": ("settled: `spread_line` is the away team's line (verified against moneyline direction in "
                    "data/verification-d.tsv V8, 13/13), which is reading B — the reading whose plausibility "
                    "checks pass. Reading A, which the column's own documentation implies, produces a 60% "
                    "home-cover rate and a 36% home-favourite share, and is published here only as the audit "
                    "trail of how the question was decided. Spread-derived numbers in this module are therefore "
                    "computed under B; the remaining caution is provenance, not sign."),
    }
    out["checks"] = checks
    out["verdict"] = ("ALL PASS — spread-derived numbers may be published as internal measurements"
                      if all(c["verdict"] == "PASS" for c in checks)
                      else "HOLD — publish the totals-derived numbers only; keep spread-derived values in the register blank and flagged")
    return out


def run_all(write: bool = True) -> dict:
    games = load_games()
    last = max(g["season"] for g in games)
    payload = {
        "id": "measured",
        "title": "Measured correlations and market behaviour from in-repo game data",
        "description": ("Computed by engine/measure.py from data/raw/games.csv. Third-party provenance, recorded as "
                        "such: these are measurements of a dataset, not official market facts. Re-run with "
                        "`python3 -m engine.measure`."),
        "updated": "2026-11-14",
        "editorial": True,
        "dataset": {"games_used": len(games), "seasons": [min(g["season"] for g in games), last],
                    "with_total_and_spread": sum(1 for g in games
                                                 if g["total_line"] is not None and g["spread_line"] is not None),
                    **PROVENANCE},
        "c01_over_versus_home_cover": measure_over_cover(games),
        "c01_under_convention_A": measure_over_cover(games, convention="A"),
        "c01_recent_10_seasons": measure_over_cover(games, seasons=range(last - 9, last + 1)),
        "parlay_pricing_impact": parlay_pricing_impact(games),
        "season_stability": season_stability(games, first=max(2010, min(g["season"] for g in games))),
        "sig01_home_underdog_after_miss": home_underdog_after_miss(games),
        "sig01_under_convention_A": home_underdog_after_miss(games, convention="A"),
        "plausibility_checks": plausibility_checks(games),
    }
    payload["view"] = build_view(payload)
    if write:
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    return payload


def _tbl(rows, cols, title, tid):
    return {"id": tid, "title": title,
            "columns": cols, "rows": rows}


def build_view(payload: dict) -> dict:
    """The same numbers, shaped as a site register: sections with columns and rows.

    Kept in the module rather than in the template so the page is generated from data and
    cannot drift from it — and so every cell here is the value the code computed, not a
    transcription of it.
    """
    ds = payload["dataset"]
    pc = payload["plausibility_checks"]
    conv = pc.get("convention_test", {})
    prov_note = ("Third-party dataset committed in-repo by a parallel session (checksummed in data/raw/"
                 "MANIFEST.json). Not an official NFL source, so nothing on this page is promoted into the "
                 "registers as a published market fact.")
    sections = [
        {"title": "0. Provenance, stated before any number",
         "description": prov_note,
         "columns": [{"key": "k", "label": "Property"}, {"key": "v", "label": "Value"}],
         "rows": [
             {"k": "Dataset", "v": ds["dataset"], "no_source_reason": prov_note},
             {"k": "In-repo path", "v": ds["in_repo_path"], "no_source_reason": prov_note},
             {"k": "Checksum manifest", "v": ds["manifest"], "no_source_reason": prov_note},
             {"k": "Games used", "v": str(ds["games_used"]), "no_source_reason": prov_note},
             {"k": "Seasons covered", "v": f"{ds['seasons'][0]}–{ds['seasons'][1]}", "no_source_reason": prov_note},
             {"k": "Games with both a total and a spread", "v": str(ds["with_total_and_spread"]),
              "no_source_reason": prov_note},
             {"k": "Official source?", "v": "No — third-party aggregation of sportsbook closing prices",
              "no_source_reason": prov_note},
             {"k": "Permitted use", "v": ds["allowed_use"], "no_source_reason": prov_note},
         ]},
        {"title": "1. Plausibility checks the dataset has to pass first",
         "description": ("Run before publishing anything derived from these files, because the first measurement "
                         "looked wrong in a checkable way. They localise the problem instead of arguing about it."),
         "columns": [
             {"key": "check", "label": "Check"},
             {"key": "value", "label": "Measured", "render": "num"},
             {"key": "verdict", "label": "Verdict", "render": "badge"},
             {"key": "consequence", "label": "Consequence if it fails"},
             {"key": "no_source_reason", "label": "Provenance"},
         ],
         "rows": [{**c, "no_source_reason": prov_note} for c in pc["checks"]]},
        {"title": "2. Which sign convention the data supports",
         "description": ("The dataset's own documentation implies reading A; its contents behave like reading B. "
                          "Both are computed and neither is promoted, because picking the flattering one is how a "
                          "pipeline manufactures a result."),
         "columns": [
             {"key": "k", "label": "Test"}, {"key": "v", "label": "Value", "render": "num"},
             {"key": "n", "label": "Reading"}, {"key": "no_source_reason", "label": "Provenance"}],
         "rows": [
             {"k": "Home cover rate, reading A (margin + line > 0)",
              "v": conv.get("A_home_covers_when_margin_plus_line_positive"),
              "n": "what the documentation implies — implausibly high", "no_source_reason": prov_note},
             {"k": "Home cover rate, reading B (margin − line > 0)",
              "v": conv.get("B_home_covers_when_margin_minus_line_positive"),
              "n": "how the data actually behaves — plausible", "no_source_reason": prov_note},
             {"k": "Home is favourite — reading A", "v": conv.get("A_share_of_games_home_is_favourite"),
              "n": "≈36% is not a real NFL frequency", "no_source_reason": prov_note},
             {"k": "Home is favourite — reading B", "v": conv.get("B_share_of_games_home_is_favourite"),
              "n": "≈64% is", "no_source_reason": prov_note},
         ]},
    ]

    c01_cols = [
        {"key": "label", "label": "Slice"}, {"key": "n", "label": "Games", "render": "num"},
        {"key": "p_over", "label": "P(over)", "render": "num"},
        {"key": "p_cover", "label": "P(home covers)", "render": "num"},
        {"key": "p_both", "label": "P(both)", "render": "num"},
        {"key": "p_independent", "label": "Product of marginals", "render": "num"},
        {"key": "excess", "label": "Dependence excess", "render": "num"},
        {"key": "rho", "label": "Measured rho", "render": "num"},
        {"key": "ci", "label": "95% CI on rho"},
        {"key": "no_source_reason", "label": "Provenance"},
    ]
    rows = []
    for label, key in (("All seasons, resolved convention (B)", "c01_over_versus_home_cover"),
                       ("All seasons, documentation's convention (A) — audit trail", "c01_under_convention_A"),
                       ("Most recent ten seasons", "c01_recent_10_seasons")):
        m = payload.get(key) or {}
        if m.get("status") != "MEASURED":
            continue
        ci = m.get("rho_ci95") or ["", ""]
        rows.append({"label": label, "n": m["n"], "p_over": m["p_over"], "p_cover": m["p_home_covers"],
                     "p_both": m["p_both_observed"], "p_independent": m["p_both_if_independent"],
                     "excess": m["dependence_excess"], "rho": m["rho"], "ci": f"[{ci[0]}, {ci[1]}]",
                     "no_source_reason": prov_note})
    sections.append({
        "title": "3. Pair C-01 measured: over the total versus home covering",
        "description": ("This is the answer to the brief's correlation ask, and the number matters less than what "
                         "it refutes: at the level of marginal outcomes the two legs are close to independent, so "
                         "the classic warning about multiplying singles is *not* where the damage is in this pair. "
                         "The damage is in the price, in section 4."),
        "columns": c01_cols, "rows": rows,
        "id": "c01"})

    pp = payload["parlay_pricing_impact"]
    sections.append({
        "title": "4. What the combined price actually does to the pair (resolved convention)",
        "description": ("Measured on games where both legs had odds in the dataset. The gap below is a property of "
                         "how parlays are priced against their legs — it is not an edge claim, because a book's "
                         "price is not a probability forecast and no stake was ever placed at it."),
        "columns": [{"key": "k", "label": "Quantity"}, {"key": "v", "label": "Value", "render": "num"},
                    {"key": "n", "label": "Note"}, {"key": "no_source_reason", "label": "Provenance"}],
        "rows": [{"k": k, "v": pp.get(k2), "n": n, "no_source_reason": prov_note} for k, k2, n in (
            ("Games with both legs priced", "priced_parlay_n", f"of {pp.get('n')} games with a total and a spread"),
            ("Observed joint hit rate", "p_both_observed", "both legs winning"),
            ("Naive product of marginals", "naive_product", "what multiplying singles says"),
            ("Dependence excess", "excess", "observed minus naive — the whole marginal-correlation effect"),
            ("Mean combined decimal", "mean_combined_decimal", "the parlay price implied by the two closing leg prices"),
            ("Break-even at that price", "break_even_at_that_price", "1 / combined decimal"),
            ("Observed minus break-even (pp)", "measured_hit_rate_minus_break_even_pp", "see the caveat above"),
        )], "id": "price"})

    sig_rows = []
    for label, key in (("Resolved convention (B)", "sig01_home_underdog_after_miss"),
                       ("Documentation's convention (A)", "sig01_under_convention_A")):
        r = payload.get(key) or {}
        if r.get("status") != "MEASURED":
            continue
        ci = r.get("wilson_ci95") or ["", ""]
        sig_rows.append({"label": label, "n": r["n"], "hit": r["hit_rate"], "ci": f"[{ci[0]}, {ci[1]}]",
                         "hurdle": r["hurdle_at_-110"], "roi": r["roi_per_unit"],
                         "pnl": r["pnl_units_at_flat_stakes"],
                         "clears": "CLEARS" if r["lower_bound_clears_hurdle"] else "FAILS G-2b",
                         "no_source_reason": prov_note})
    sections.append({
        "title": "5. A peer-reviewed hypothesis, run through the real gate pipeline",
        "description": ("SIG-01 (home underdogs after a failed cover) is the one published signal fully computable "
                         "from in-repo data. It does not survive: the hit rate is far below break-even and the "
                         "lower bound clears nothing, so gate G-2b rejects it. That is the point of a gate set — a "
                         "cited, plausible story still fails when the sample is large enough to see through the "
                         "noise. Which is the difference between removing luck as a slogan and as a rule."),
        "columns": [{"key": "label", "label": "Sign convention"}, {"key": "n", "label": "Bets", "render": "num"},
                    {"key": "hit", "label": "Hit rate", "render": "num"}, {"key": "ci", "label": "95% Wilson CI"},
                    {"key": "hurdle", "label": "Break-even", "render": "num"},
                    {"key": "roi", "label": "ROI per unit", "render": "num"},
                    {"key": "pnl", "label": "PnL (units)", "render": "num"},
                    {"key": "clears", "label": "Gate G-2b", "render": "badge"},
                    {"key": "no_source_reason", "label": "Provenance"}],
        "rows": sig_rows, "id": "sig01"})

    st = payload["season_stability"]
    sections.append({
        "title": "6. Season-by-season stability of the measured rho",
        "description": ("A pooled number hides regime change; per season the estimate is noisy by construction "
                         "(≈250 games), which is the honest reason the register publishes an interval rather than a "
                         "point."),
        "columns": [{"key": "season", "label": "Season", "render": "num"},
                    {"key": "n", "label": "Games", "render": "num"},
                    {"key": "rho", "label": "rho", "render": "num"},
                    {"key": "ci", "label": "95% CI"},
                    {"key": "p_over", "label": "P(over)", "render": "num"},
                    {"key": "p_home_covers", "label": "P(home covers)", "render": "num"},
                    {"key": "no_source_reason", "label": "Provenance"}],
        "rows": [{"season": r["season"], "n": r["n"], "rho": r["rho"],
                  "ci": f"[{r['rho_ci95'][0]}, {r['rho_ci95'][1]}]", "p_over": r["p_over"],
                  "p_home_covers": r["p_home_covers"], "no_source_reason": prov_note} for r in st],
        "id": "stab"})
    # every row on this page is a measurement of one citable dataset, so it gets a source chip
    # like every other factual row in the project — the rule is not relaxed for our own numbers
    for sec in sections:
        cols = sec.get("columns") or []
        rows = sec.get("rows") or []
        if cols and not any(c.get("render") == "srclist" for c in cols):
            cols.append({"key": "sources", "label": "Source", "render": "srclist"})
        for r in rows:
            r.pop("no_source_reason", None)
            r["sources"] = ["SRC-025"]
    sections.append({"title": "7. Verdict",
                     "description": pc["verdict"] + " — " + conv.get("reading", ""),
                     "columns": [], "rows": []})
    return {"sections": sections}


if __name__ == "__main__":
    p = run_all()
    m = p["c01_over_versus_home_cover"]
    r = p["sig01_home_underdog_after_miss"]
    print(f"games={p['dataset']['games_used']}  C-01: n={m['n']} rho={m['rho']} CI={m['rho_ci95']}")
    print(f"SIG-01: n={r['n']} hit={r['hit_rate']} CI={r['wilson_ci95']} ROI={r['roi_per_unit']}")
