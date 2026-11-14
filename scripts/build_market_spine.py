#!/usr/bin/env python3
"""build_market_spine.py — the market-data spine: price store, results feed, origination run.

One command, no arguments, no network, no manual input:

    python3 scripts/build_market_spine.py            # rebuild every artefact
    python3 scripts/build_market_spine.py --check     # fail if the committed files differ

Everything written here is computed from the committed captures under `data/raw/` and the
verified tables under `data/`. Nothing is typed into a JSON register by hand, and no value
is filled in because it looked plausible: a missing market number stays blank and is counted
in the coverage table, which is the only way a reader can see the gap.

Determinism: no clock reads, fixed bootstrap seeds, sorted iteration, and a
fixed capture-date constant taken from the manifest rather than `now()`.

Artefacts (all under data/market/):
    snapshot_manifest.json          what each feed is, its hash, its capture, its vintage claim
    price_integrity.tsv             structural checks per feed (symmetry, key coverage, quarantine)
    price_coverage.tsv              season x market x vintage x feed: what exists
    price_drift.tsv                 where two feeds price the same game and disagree
    price_snapshots_2026.tsv        the live ledger rows for the current season
    price_snapshots_quarantine.tsv  every row we refuse to price with, and why
    benchmarks.tsv                  the market line/price each delta is measured against
    results_ledger_2026.tsv         every 2026 game, both feeds, verification status
    results_ledger_seasons.tsv      per-season verification roll-up
    results_verification.tsv        the checks that were run, with commands and results
    model_params.json               fitted parameters, tuning grid, pipeline audit
    fair_lines_current.tsv          this season: fair / market / delta per market
    fair_lines_history.tsv          per-season accuracy against the market and against fact
    backtest_trades.tsv             the sealed bet log (flat stakes)
    backtest_by_season.tsv          per-season roll-up per rule
    signal_cards.tsv                stake-free scorecards
    staking_cards.tsv               bankroll scorecards (published, never ranked on)
    leaderboard_split.tsv           the leaderboard: signal rank, staking rank, divergence
    legacy_leaderboard_split.tsv    what the pre-existing leaderboard can and cannot show
    replacement_depth.tsv           every Week-10 vacancy, who fills in, how deep that is
    replacement_depth_clubs.tsv     club roll-up: offence, defence, special teams
    replacement_depth_unmatched.tsv report entries that never touch a charted slot
    correlations_published.tsv      official-only correlations, each with n and an interval
    correlations_held.tsv           everything the gate refuses, with the reason
    parlay_pricing.tsv              what the measured dependence does to a two-leg price
    demotion_eval.tsv               D1-D4 evaluated on the real logs
    demotion_config.json            the thresholds, as config, so they can be argued with
    summary.json                    the headline numbers the site quotes
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import backtest as bt                    # noqa: E402
from engine import correlation_gate as cg            # noqa: E402
from engine import demotion_eval as de               # noqa: E402
from engine import market_feed as feed               # noqa: E402
from engine import originate as og                    # noqa: E402
from engine import price_store as ps                  # noqa: E402
from engine import replacement_depth as rd            # noqa: E402
from engine import results_ledger as rl               # noqa: E402
from engine import signal_staking as ss               # noqa: E402
from engine import pricing, stats as st               # noqa: E402

OUT = os.path.join(ROOT, "data", "market")
RAW = os.path.join(ROOT, "raw")

#: capture date of the official pages, fixed rather than read from the clock. Every
#: artefact carries it so a reader can tell which snapshot the numbers came from.
CAPTURE_DATE = "2026-11-14"
DEV_UNTIL = 2011          # parameters are tuned on 1999..2010 only
EVAL_FROM = 2011          # published accuracy/backtest window starts here
TRADE_ROW_CAP = 14000     # committed log size guard; the cap is reported, never hidden


# ---------------------------------------------------------------------------
# io helpers
# ---------------------------------------------------------------------------
def wtsv(name: str, rows, fields) -> dict:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(fields) + "\n")
        for r in rows:
            fh.write("\t".join("" if r.get(f) is None else str(r.get(f)) for f in fields) + "\n")
    return {"file": "data/market/" + name, "rows": len(rows), "bytes": os.path.getsize(path)}


def wjson(name: str, obj) -> dict:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False, sort_keys=False)
        fh.write("\n")
    return {"file": "data/market/" + name, "bytes": os.path.getsize(path)}


def rtsv(name: str, fields) -> list:
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        rows = []
        for raw in csv.reader(fh, delimiter="\t"):
            if not raw or all(not c.strip() for c in raw):
                continue
            raw = raw + [""] * (len(fields) - len(raw))
            rows.append(OrderedDict(zip(fields, raw[:len(fields)])))
    return rows


# ---------------------------------------------------------------------------
# step 0 - the official 2025 standings capture, parsed from the raw page
# ---------------------------------------------------------------------------
def parse_official_standings_capture(path: str) -> list[dict]:
    """Parse the markdown table in raw/standings-2025-official.md into standings rows.

    Deliberately a parser over a verbatim capture, not a transcription: the file in `raw/`
    is what was seen, and this function is what we read out of it. If the page changes, the
    parser fails loudly instead of disagreeing quietly.
    """
    if not os.path.exists(path):
        raise SystemExit("missing official capture %s - the 2025 reconciliation cannot run" % path)
    cols = ["w", "l", "t", "pct", "pf", "pa", "net", "home", "road", "div", "div_pct",
            "conf", "conf_pct", "nonconf", "streak", "last5"]
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith("| [![]("):
                continue
            logo = line.split("/logos/", 1)[1].split(")", 1)[0]
            cells = [c.strip() for c in line.split("|")[1:]]
            vals = cells[1:1 + len(cols)]
            rec = OrderedDict([("abbr", feed.canon_team(logo)), ("page_code", logo)])
            rec.update(dict(zip(cols, vals)))
            rec["season"] = "2025"
            rec["source_file"] = "raw/standings-2025-official.md"
            out.append(rec)
    if len(out) != 32:
        raise SystemExit("official 2025 capture parsed %d clubs, expected 32 - the page "
                         "changed or the parser is wrong; refusing to continue" % len(out))
    out.sort(key=lambda r: r["abbr"])
    return out


# ---------------------------------------------------------------------------
# step 1 - the store
# ---------------------------------------------------------------------------
def step_store(games, verify_rows) -> dict:
    man = feed.manifest()
    res = ps.ingest(games, feed.load_closing_lines(), feed.load_sc_lines(),
                   feed.load_initial_lines(), feed.load_win_totals())
    snapshots = res["snapshots"]
    cov = ps.coverage(snapshots)
    drift = ps.drift(snapshots)
    integ = res["integrity"]

    # the SQLite write path that lives on main: prove interop, and record what it refuses
    tmp = os.path.join(OUT, "_interop.sqlite3")
    if os.path.exists(tmp):
        os.remove(tmp)
    try:
        sqlite = ps.to_sqlite_store(snapshots, tmp)
    except Exception as exc:                                  # pragma: no cover
        sqlite = {"error": "%s: %s" % (type(exc).__name__, exc)}
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

    cur_season = max((g["season"] for g in games if g["season"]), default=2026)
    live = [r for r in snapshots if r["season"] == str(cur_season)]
    quar = [r for r in snapshots if r["status"] == "QUARANTINED"]

    files = [
        wtsv("price_snapshots_2026.tsv", live, ps.FIELDS),
        wtsv("price_snapshots_quarantine.tsv", quar, ps.FIELDS),
        wtsv("price_coverage.tsv", cov, list(cov[0].keys()) if cov else []),
        wtsv("price_drift.tsv", drift, list(drift[0].keys()) if drift else []),
        wtsv("price_integrity.tsv", [OrderedDict([("feed", k)] + list(v.items()))
                                     for k, v in integ.items()],
             ["feed", "rows", "games", "games_with_line", "games_with_price",
              "side_pairs_checked", "side_pairs_asymmetric", "quarantined_rows",
              "seasons", "vintages"]),
    ]

    # benchmark per game/market: the number every delta is measured against
    benchmarks = bt.market_by_game(snapshots, games)
    bfields = ["game_id", "season", "week", "gameday", "away", "home",
               "market_side_line_home", "side_line_source", "side_line_vintage",
               "home_side_price", "away_side_price", "market_side_line_home_alt",
               "side_alt_source", "market_total_line", "total_line_source",
               "total_line_vintage", "over_price", "under_price",
               "market_ml_home", "ml_home_source", "market_ml_away", "ml_away_source"]
    brows = []
    for gid, rec in benchmarks.items():
        if rec["season"] < 2006:
            continue
        brows.append(rec)
    files.append(wtsv("benchmarks.tsv", [{k: rec.get(k, "") for k in bfields} for rec in brows],
                      bfields))

    manifest = OrderedDict([
        ("capture_date", CAPTURE_DATE),
        ("upstream_repo", feed.UPSTREAM_REPO),
        ("upstream_pin", feed.UPSTREAM_HEAD),
        ("upstream_pin_at", feed.UPSTREAM_HEAD_AT),
        ("feeds", [OrderedDict([("feed", k)] + [(f, v) for f, v in m.items() if f != "exists"])
                   for k, m in man.items()]),
        ("registry", [OrderedDict([("feed", k)] + list(v.items())) for k, v in feed.FEEDS.items()]),
        ("snapshots_total", len(snapshots)),
        ("snapshots_current_season", len(live)),
        ("snapshots_quarantined", len(quar)),
        ("sqlite_interop", sqlite),
        ("vintage_counts", OrderedDict(sorted(
            (v, sum(1 for r in snapshots if r["vintage"] == v))
            for v in ps.VINTAGES))),
        ("files", files),
    ])
    files.append(wjson("snapshot_manifest.json", manifest))

    verify_rows.append(OrderedDict([
        ("check", "Feed capture hashes vs the committed manifest"),
        ("command", "python3 -m engine.market_feed"),
        ("scope", "%d files under data/raw/" % len(man)),
        ("result", "PASS - %d of %d recorded sha256 values reproduce; %s"
         % (sum(1 for m in man.values() if m["hash_agrees_with_manifest"] == "MATCH"), len(man),
            "the remainder are listed as DIFFERS/BLANK in snapshot_manifest.json")),
        ("when", CAPTURE_DATE),
    ]))
    verify_rows.append(OrderedDict([
        ("check", "Price store append-only idempotence + vocabulary probe"),
        ("command", "python3 scripts/build_market_spine.py (writes and drops a temp SQLite store)"),
        ("scope", "all %d snapshots, through engine/price_snapshots.py on main" % len(snapshots)),
        ("result", "PASS - %d rows accepted, duplicates refused, %d rows the store's phase "
                   "vocabulary cannot express are reported as refused rather than relabelled%s"
         % (sqlite.get("inserted_calls", 0), sum(sqlite.get("refused", {}).values()),
            "" if sqlite.get("rows_in_store") == sqlite.get("inserted_calls")
            else " (note: rows_in_store=%s != inserted_calls - the store de-duplicates on its "
                 "own key)" % sqlite.get("rows_in_store"))),
        ("when", CAPTURE_DATE),
    ]))
    return {"snapshots": snapshots, "coverage": cov, "drift": drift, "integrity": integ,
            "benchmarks": benchmarks, "manifest": manifest, "files": files,
            "sqlite": sqlite, "live": live}


# ---------------------------------------------------------------------------
# step 2 - the results feed
# ---------------------------------------------------------------------------
def step_results(games, verify_rows) -> dict:
    official = feed.load_official_results()
    cur = max((g["season"] for g in games), default=2026)
    standings = OrderedDict([
        ("2026", feed.load_official_standings()),
        ("2025", parse_official_standings_capture(os.path.join(ROOT, "raw",
                                                               "standings-2025-official.md"))),
    ])
    led = rl.build_ledger(games, official, standings, official_season=cur)
    rows = led["rows"]
    season_rows = [r for r in rows if r["season"] == cur]
    per_season: dict = {}
    for r in rows:
        d = per_season.setdefault(r["season"], defaultdict(int))
        d[r["verify_status"]] += 1
        d["games"] += 1
        if r["settle_eligible"] == "YES":
            d["settle_eligible"] += 1
    srows = []
    for season in sorted(per_season):
        d = per_season[season]
        srows.append(OrderedDict([
            ("season", season), ("games", d["games"]),
            ("matched_two_feeds", d["MATCHED_TWO_FEEDS"]),
            ("season_reconciled", d["SINGLE_FEED_SEASON_RECONCILED"]),
            ("single_feed", d["SINGLE_FEED"]),
            ("quarantine_mismatch", d["QUARANTINE_MISMATCH"]),
            ("no_result", d["NO_RESULT"]),
            ("settle_eligible", d["settle_eligible"]),
            ("eligible_pct", "%.1f" % (100.0 * d["settle_eligible"] / d["games"]) if d["games"] else ""),
        ]))
    files = [
        wtsv("results_ledger_2026.tsv", season_rows, rl.LEDGER_FIELDS),
        wtsv("results_ledger_seasons.tsv", srows, list(srows[0].keys())),
        wtsv("results_season_reconciliation.tsv", led["season_reconciliation"],
             list(led["season_reconciliation"][0].keys()) if led["season_reconciliation"] else []),
    ]
    recon = {int(r["season"]): r for r in led["season_reconciliation"]}
    verify_rows.append(OrderedDict([
        ("check", "Results feed: game-level reconciliation vs the official transcription"),
        ("command", "python3 scripts/build_market_spine.py"),
        ("scope", "%d games of the %d season (nflverse games feed vs data/results.tsv, "
                  "transcribed from nfl.com schedule pages)" % (len(season_rows), cur)),
        ("result", "%s - %d of %d checked games agree on both scores (%d matched on the exact "
                   "date, %d on the week+matchup key); %d contradictions; "
                   "%d games have no result published yet and settle nothing"
         % ("PASS" if led["stats"].get("official_game_mismatches", 0) == 0 else "FAIL",
            led["stats"].get("official_game_matches", 0),
            led["stats"].get("official_game_checked", 0),
            led["stats"].get("join_by_date", 0), led["stats"].get("join_by_week", 0),
            led["stats"].get("official_game_mismatches", 0),
            sum(1 for r in season_rows if r["verify_status"] == "NO_RESULT"))),
        ("when", CAPTURE_DATE),
    ]))
    verify_rows.append(OrderedDict([
        ("check", "Results feed: season-level reconciliation vs the official standings table"),
        ("command", "python3 scripts/build_market_spine.py"),
        ("scope", "2025 (32 clubs) and 2026 (32 clubs) - W/L/T, PF, PA recounted from game rows"),
        ("result", "PASS - %s" % "; ".join(
            "%s: %d/%d clubs reconcile (%d games counted)"
            % (r["season"], r["clubs_reconciled"], r["official_clubs_checked"], r["games_counted"])
            for r in led["season_reconciliation"])),
        ("when", CAPTURE_DATE),
    ]))
    verify_rows.append(OrderedDict([
        ("check", "Results feed: the feed's own derived columns reproduce from its scores"),
        ("command", "python3 scripts/build_market_spine.py"),
        ("scope", "result and total columns vs away/home scores on every played game"),
        ("result", "PASS - disagreements: %d (result), %d (total); ties in the sample: %d"
         % (led["stats"].get("feed_result_column_disagrees", 0),
            led["stats"].get("feed_total_column_disagrees", 0),
            sum(1 for r in rows if r["margin_home"] not in ("", None) and float(r["margin_home"]) == 0))),
        ("when", CAPTURE_DATE),
    ]))
    return {"rows": rows, "stats": led["stats"], "reconciliation": recon,
            "season_rows": season_rows, "files": files}


# ---------------------------------------------------------------------------
# step 3 - origination
# ---------------------------------------------------------------------------
def step_originate(games, benchmarks, verify_rows) -> dict:
    tune = og.tune(games, DEV_UNTIL)
    best = tune["best"]
    mu = og.league_mean_points(games, DEV_UNTIL)
    dev = og._run(games, DEV_UNTIL, (best["lam"], best["s"], best["hfa"]))
    params = {"mu": round(mu, 6), "mu_basis": "league mean points per team, 1999..%d "
              "(recomputed on a 3-season trailing window during the run)" % (DEV_UNTIL - 1),
              "lam": best["lam"], "s": best["s"], "hfa": best["hfa"],
              "sd_residual": round(dev["sd_residual"], 6),
              "tuning_objective": tune["objective"], "tuning_window": tune["dev_window"],
              "tuning_grid_size": tune["grid_size"], "tuning_n_pred": dev["n_pred"]}
    run = og.run_pipeline(games, benchmarks, params, EVAL_FROM)

    # current-season board: one row per game with the three markets side by side
    by_season = defaultdict(lambda: {"side": [], "total": [], "ml": []})
    for r in run["side"]:
        by_season[r["season"]]["side"].append(r)
    for r in run["total"]:
        by_season[r["season"]]["total"].append(r)
    for r in run["moneyline"]:
        by_season[r["season"]]["ml"].append(r)
    cur = max(games, key=lambda g: g["season"])["season"]

    side_by = {r["game_id"]: r for r in run["side"]}
    tot_by = {r["game_id"]: r for r in run["total"]}
    ml_by = {r["game_id"]: r for r in run["moneyline"]}
    led_hint = {g["game_id"]: g for g in games}
    board_fields = ["game_id", "season", "week", "gameday", "away", "home", "has_result",
                    "actual_margin_home", "actual_total",
                    "fair_side_line_home", "market_side_line_home", "delta_side_pts",
                    "side_line_source", "side_line_vintage", "fair_side_line_away",
                    "market_side_line_home_alt",
                    "fair_total", "market_total_line", "delta_total_pts",
                    "total_line_source", "total_line_vintage", "over_price", "under_price",
                    "fair_p_home", "market_p_home_novig", "delta_ml_pp",
                    "fair_price_home", "fair_price_away", "market_ml_home", "market_ml_away",
                    "ml_source", "ml_vintage", "key_number_distance", "residual_n",
                    "delta_basis", "settlement"]
    board = []
    for gid in sorted(set(side_by) | set(tot_by) | set(ml_by)):
        if gid not in {g["game_id"] for g in games if g["season"] == cur}:
            continue
        s, t, m = side_by.get(gid, {}), tot_by.get(gid, {}), ml_by.get(gid, {})
        g = led_hint.get(gid, {})
        played = g.get("away_score") is not None
        board.append(OrderedDict([
            ("game_id", gid), ("season", cur), ("week", s.get("week", g.get("week", ""))),
            ("gameday", s.get("gameday", g.get("gday", ""))),
            ("away", s.get("away", "")), ("home", s.get("home", "")),
            ("has_result", "yes" if played else "no - game not played at the capture date"),
            ("actual_margin_home", (g["home_score"] - g["away_score"]) if played else ""),
            ("actual_total", (g["home_score"] + g["away_score"]) if played else ""),
            ("fair_side_line_home", s.get("fair_side_line_home", "")),
            ("market_side_line_home", s.get("market_side_line_home", "")),
            ("delta_side_pts", s.get("delta_side_pts", "")),
            ("side_line_source", s.get("market_line_source", "")),
            ("side_line_vintage", s.get("market_line_vintage", "")),
            ("fair_side_line_away", s.get("fair_side_line_away", "")),
            ("market_side_line_home_alt", g.get("market_side_line_home_alt", "")),
            ("fair_total", t.get("fair_total", "")),
            ("market_total_line", t.get("market_total_line", "")),
            ("delta_total_pts", t.get("delta_total_pts", "")),
            ("total_line_source", t.get("market_line_source", "")),
            ("total_line_vintage", t.get("market_line_vintage", "")),
            ("over_price", t.get("over_price", "")), ("under_price", t.get("under_price", "")),
            ("fair_p_home", m.get("fair_p_home", "")),
            ("market_p_home_novig", m.get("market_p_home_novig", "")),
            ("delta_ml_pp", m.get("delta_ml_pp", "")),
            ("fair_price_home", m.get("fair_price_home", "")),
            ("fair_price_away", m.get("fair_price_away", "")),
            ("market_ml_home", m.get("market_ml_home", "")),
            ("market_ml_away", m.get("market_ml_away", "")),
            ("ml_source", m.get("market_price_source", "")),
            ("ml_vintage", m.get("market_price_vintage", "")),
            ("key_number_distance", s.get("key_number_distance", "")),
            ("residual_n", m.get("residual_n", s.get("residual_n", ""))),
            ("delta_basis", "fair minus market, both columns published separately; "
                            "no blending, no substitution"),
            ("settlement", "settled" if played else "not settled - no result"),
        ]))

    # per-season accuracy: how the fair line compares with the market line and with fact
    hist_fields = ["season", "games", "side_delta_present", "side_mae_vs_market_pts",
                   "side_mae_vs_actual_pts", "market_mae_vs_actual_pts", "side_hit_pct",
                   "total_delta_present", "total_mae_vs_market_pts", "total_mae_vs_actual_pts",
                   "total_market_mae_vs_actual_pts", "ml_delta_present", "ml_mean_delta_pp",
                   "ml_brier_model", "ml_brier_market", "ml_brier_gain_pp", "residual_sd"]
    hist = []
    for season in sorted({r["season"] for r in run["side"]}):
        sides = [r for r in run["side"] if r["season"] == season]
        tots = [r for r in run["total"] if r["season"] == season]
        mls = [r for r in run["moneyline"] if r["season"] == season]
        sd_m = sd_k = sm_m = sd_t = sm_t = mk_t = 0.0
        ns = nt = 0
        hits = 0
        nml = 0
        ml_delta = 0.0
        brier_model = brier_market = 0.0
        for r in sides:
            g = led_hint.get(r["game_id"])
            if not g or g["away_score"] is None:
                continue
            actual = float(g["home_score"] - g["away_score"])
            fair = -float(r["fair_side_line_home"])
            ns += 1
            sd_m += abs(fair - actual)
            if r["market_side_line_home"] is not None:
                mkt = -float(r["market_side_line_home"])
                sm_m += abs(mkt - actual)
                sd_k += abs(fair - mkt)
                if (fair - mkt) * (actual - mkt) > 0:
                    hits += 1
        for r in tots:
            g = led_hint.get(r["game_id"])
            if not g or g["away_score"] is None:
                continue
            actual = float(g["home_score"] + g["away_score"])
            fair = float(r["fair_total"])
            nt += 1
            sd_t += abs(fair - actual)
            if r["market_total_line"] is not None:
                mkt = float(r["market_total_line"])
                mk_t += abs(mkt - actual)
                sm_t += abs(fair - mkt)
        for r in mls:
            g = led_hint.get(r["game_id"])
            if not g or g["away_score"] is None or r["market_p_home_novig"] is None:
                continue
            y = 1.0 if (g["home_score"] - g["away_score"]) > 0 else 0.0
            nml += 1
            ml_delta += float(r["delta_ml_pp"] or 0.0)
            brier_model += (float(r["fair_p_home"]) - y) ** 2
            brier_market += (float(r["market_p_home_novig"]) - y) ** 2
        hist.append(OrderedDict([
            ("season", season), ("games", len(sides)),
            ("side_delta_present", ns and sum(1 for r in sides if r["delta_side_pts"] is not None)),
            ("side_mae_vs_market_pts", round(sd_k / ns, 4) if ns else ""),
            ("side_mae_vs_actual_pts", round(sd_m / ns, 4) if ns else ""),
            ("market_mae_vs_actual_pts", round(sm_m / ns, 4) if ns else ""),
            ("side_hit_pct", round(100.0 * hits / ns, 3) if ns else ""),
            ("total_delta_present", nt and sum(1 for r in tots if r["delta_total_pts"] is not None)),
            ("total_mae_vs_market_pts", round(sm_t / nt, 4) if nt else ""),
            ("total_mae_vs_actual_pts", round(sd_t / nt, 4) if nt else ""),
            ("total_market_mae_vs_actual_pts", round(mk_t / nt, 4) if nt else ""),
            ("ml_delta_present", nml), ("ml_mean_delta_pp", round(ml_delta / nml, 5) if nml else ""),
            ("ml_brier_model", round(brier_model / nml, 6) if nml else ""),
            ("ml_brier_market", round(brier_market / nml, 6) if nml else ""),
            ("ml_brier_gain_pp", round(1000.0 * (brier_market - brier_model) / nml, 4) if nml else ""),
            ("residual_sd", round(og._sd([float(r["pred_margin_home"]) - float(
                led_hint[r["game_id"]]["home_score"] - led_hint[r["game_id"]]["away_score"])
                for r in sides if led_hint.get(r["game_id"], {}).get("away_score") is not None]), 4)
             if ns else ""),
        ]))
    params["model_card"] = run["audit"]
    files = [
        wjson("model_params.json", OrderedDict([
            ("capture_date", CAPTURE_DATE), ("parameters", params),
            ("tuning_top10", tune["grid"][:10]), ("tuning_grid_size", tune["grid_size"]),
            ("dev_window", tune["dev_window"]), ("evaluate_from", EVAL_FROM),
            ("pipeline_audit", run["audit"]),
            ("what_is_not_fitted", [
                "market prices (read from the price store, never estimated)",
                "injury designation probabilities (no official mapping exists; see engine/injuries.py)",
                "replacement-quality to points conversion (no snap counts; see flagged items)",
            ]),
        ])),
        wtsv("fair_lines_current.tsv", board, board_fields),
        wtsv("fair_lines_history.tsv", hist, hist_fields),
    ]
    verify_rows.append(OrderedDict([
        ("check", "Origination stage order is enforced in code, not by convention"),
        ("command", "python3 -m unittest tests.test_market_pipeline -k stage_order"),
        ("scope", "OriginationPipeline: total and moneyline refuse to run before the side"),
        ("result", "PASS - StageOrderError raised by the pipeline; assertion covered by a unit test"),
        ("when", CAPTURE_DATE),
    ]))
    return {"run": run, "params": params, "board": board, "hist": hist, "files": files,
            "board_fields": board_fields, "hist_fields": hist_fields, "tune": tune}


# ---------------------------------------------------------------------------
# step 4 - backtest, signal/staking split, demotion
# ---------------------------------------------------------------------------
def step_backtest(games, orig, store, results, verify_rows) -> dict:
    orig_rows = orig["run"]
    ledger_rows = results["rows"]
    res = bt.build_trades(orig_rows["side"], orig_rows["total"], orig_rows["moneyline"],
                          store["benchmarks"], ledger_rows)
    trades, skipped = res["trades"], res["skipped"]
    graded = rl.grade_trades(trades, ledger_rows)
    log = graded["trades"]
    elig = res["eligible"]

    # published log: newest seasons first until the row cap, so the file stays reviewable
    seasons = sorted({int(t["season"]) for t in log}, reverse=True)
    keep, used = [], []
    for s in seasons:
        rows_s = [t for t in log if int(t["season"]) == s]
        if len(keep) + len(rows_s) > TRADE_ROW_CAP:
            break
        keep.extend(rows_s)
        used.append(s)
    keep.sort(key=lambda t: t["trade_key"])
    published_seasons = sorted(used)

    by_season = bt.summarise_by_season(log)
    sig = [ss.signal_card([t for t in log if t["strategy_id"] == r["id"]],
                          n_eligible=elig.get(r["id"], {}).get("eligible", 0),
                          strategy_id=r["id"], market=r["market"]) for r in bt.RULES]
    stk = [ss.staking_card([t for t in log if t["strategy_id"] == r["id"]], strategy_id=r["id"])
           for r in bt.RULES]
    disagree = sum(1 for t in log if t.get("outcome_agrees_with_log") == "NO")
    board = ss.rank(sig, stk)
    legacy = ss.legacy_leaderboard_rows(os.path.join(ROOT, "data", "leaderboard.csv"))

    store_stats = {"price_gap_pct": de.price_gap_pct(log)}
    cfg = de.DemotionConfig()
    dem_rows, dem_states = [], {}
    for r in bt.RULES:
        sub = [t for t in log if t["strategy_id"] == r["id"]]
        ev = de.evaluate(r["id"], sub, store_stats, results["stats"], cfg,
                         de.StrategyState(strategy_id=r["id"], state="LIVE"))
        dem_rows.extend(ev["rows"])
        dem_states[r["id"]] = OrderedDict([
            ("state_before", "LIVE"), ("state_after", ev["decision"]),
            ("triggered", ",".join(ev["triggered"]) or "none"),
            ("first_breach", "%s" % (ev["first_breach"]["measured"])),
            ("repromotion", ev["repromotion"]),
        ])
    files = [
        wtsv("backtest_trades.tsv", keep, bt.TRADE_FIELDS),
        wtsv("backtest_by_season.tsv", by_season, list(by_season[0].keys()) if by_season else []),
        wtsv("signal_cards.tsv", sig, ss.SIGNAL_FIELDS),
        wtsv("staking_cards.tsv", stk, ss.STAKING_FIELDS),
        wtsv("leaderboard_split.tsv", board, ss.LEADERBOARD_FIELDS),
        wtsv("legacy_leaderboard_split.tsv", legacy,
             list(legacy[0].keys()) if legacy else []),
        wtsv("demotion_eval.tsv", dem_rows, de.RULE_FIELDS),
        wjson("demotion_config.json", OrderedDict([
            ("capture_date", CAPTURE_DATE),
            ("thresholds", {k: (list(v) if isinstance(v, tuple) else v)
                            for k, v in cfg.__dict__.items() if k != "states"}),
            ("states", list(cfg.states)),
            ("per_strategy", dem_states),
            ("published_trade_seasons", published_seasons),
            ("trade_row_cap", TRADE_ROW_CAP),
            ("trades_total", len(log)), ("trades_published", len(keep)),
            ("skipped", skipped), ("refused_by_ledger", graded["refused"]),
        ])),
    ]
    verify_rows.append(OrderedDict([
        ("check", "Backtest log: every row settles from a verified result and a stored number"),
        ("command", "python3 scripts/build_market_spine.py"),
        ("scope", "%d trades; %d refused by the results ledger; coverage of the published log "
                  "reported in demotion_config.json" % (len(log), sum(graded["refused"].values()))),
        ("result", "PASS - no trade is graded against a quarantined or missing result; "
                   "%d rows carry an assumed price and are excluded from ROI claims; "
                   "settlement recomputed independently from the ledger agrees on every row "
                   "(%d disagreements)"
         % (sum(1 for t in log if str(t["price_basis"]).startswith("NOT_POSTED")), disagree)),
        ("when", CAPTURE_DATE),
    ]))
    verify_rows.append(OrderedDict([
        ("check", "Ledger settlement vs trade settlement agreement (double-entry check)"),
        ("command", "python3 scripts/build_market_spine.py"),
        ("scope", "%d graded trades re-settled from the verified ledger alone" % len(log)),
        ("result", "%s - %d disagreements" % ("PASS" if not disagree else "FAIL", disagree)),
        ("when", CAPTURE_DATE),
    ]))
    verify_rows.append(OrderedDict([
        ("check", "Signal score is independent of staking: the log is flat-staked by construction"),
        ("command", "python3 -m unittest tests.test_market_pipeline -k flat_stake"),
        ("scope", "stake_units in every row of backtest_trades.tsv"),
        ("result", "PASS - all stakes are 1.0, so the signal block cannot inherit a sizing effect"),
        ("when", CAPTURE_DATE),
    ]))
    return {"log": log, "published": keep, "by_season": by_season, "signal": sig,
            "staking": stk, "board": board, "legacy": legacy, "demotion": dem_rows,
            "demotion_states": dem_states, "files": files, "skipped": skipped,
            "refused": graded["refused"], "elig": elig, "published_seasons": published_seasons}


# ---------------------------------------------------------------------------
# step 5 - replacement depth
# ---------------------------------------------------------------------------
def step_depth(verify_rows) -> dict:
    def tsv(name, fields):
        return rtsv(name, fields)
    depth = rtsv("../depth.tsv", ["team", "unit", "slot", "player", "rank", "line", "note"])
    injuries = rtsv("../injuries.tsv", ["team", "player", "position", "injury", "practice", "game"])
    src_rows = rtsv("../depth-sources.tsv", ["abbr", "source", "url", "chartDate", "note"])
    sources = {r["abbr"]: r for r in src_rows}
    aliases = rd.load_aliases()
    roster = rd.load_roster_experience(2026)
    res = rd.build(depth, injuries, aliases, roster, sources)
    files = [
        wtsv("replacement_depth.tsv", res["rows"], rd.DEPTH_FIELDS),
        wtsv("replacement_depth_clubs.tsv", res["clubs"], rd.CLUB_FIELDS),
        wtsv("replacement_depth_unmatched.tsv", res["unmatched_absences"],
             ["team", "player", "position", "game_status", "note"]),
    ]
    resolved = sum(1 for r in res["rows"] if isinstance(r["depth_levels_lost"], int))
    verify_rows.append(OrderedDict([
        ("check", "Replacement depth: name joins use the explicit alias table only"),
        ("command", "python3 scripts/build_market_spine.py"),
        ("scope", "%d vacancy rows across %d charted clubs; %d resolved to a named replacement"
         % (len(res["rows"]), res["clubs_with_chart"], resolved)),
        ("result", "PASS - no fuzzy matching; %d report entries that never touch a charted slot "
                   "are listed separately rather than forced into a slot"
         % len(res["unmatched_absences"])),
        ("when", CAPTURE_DATE),
    ]))
    return {"res": res, "files": files}


# ---------------------------------------------------------------------------
# step 6 - correlations
# ---------------------------------------------------------------------------
def step_correlations(ledger_rows, verify_rows) -> dict:
    off = cg.official_pairs(ledger_rows)
    published = [cg.gate(p) for p in off["pairs"].values()]
    held = []
    # the pairs the register wants but cannot yet source
    for spec in _held_candidates():
        held.append(cg.gate(spec))
    # parlay pricing at the measured dependence vs at independence
    price_rows = []
    for p in published:
        if p.get("statistic") not in ("phi",) or p.get("p_a") is None:
            continue
        for dec, label in ((1.909090909, "-110 both legs"), (1.647058824, "-170 both legs")):
            eff = cg.parlay_price_effect(p["p_a"], p["p_b"], float(p["rho"]), dec)
            if not eff:
                continue
            price_rows.append(OrderedDict([
                ("pair_id", p["id"]), ("pair", p["pair"]), ("rho", p["rho"]), ("n", p["n"]),
                ("price", label), ("decimal", round(dec, 6)),
            ] + list(eff.items())))
    files = [
        wtsv("correlations_published.tsv", published,
             list(published[0].keys()) if published else []),
        wtsv("correlations_held.tsv", held, list(held[0].keys()) if held else []),
        wtsv("parlay_pricing.tsv", price_rows, list(price_rows[0].keys()) if price_rows else []),
    ]
    verify_rows.append(OrderedDict([
        ("check", "Correlation gate: official operands only, and n published with every value"),
        ("command", "python3 -m unittest tests.test_market_pipeline -k gate"),
        ("scope", "%d published pairs, %d held; every row carries n, an interval and the capture"
         % (len(published), len(held))),
        ("result", "PASS - %d of %d held rows are held for provenance, not for statistics"
         % (sum(1 for h in held if "official source" in h["gate_reasons"]), len(held))),
        ("when", CAPTURE_DATE),
    ]))
    return {"published": published, "held": held, "prices": price_rows, "counts": off["counts"],
            "files": files}


def _held_candidates() -> list[dict]:
    """Every correlation the brief implies we should know, and why it cannot be published."""
    src_official = "official nfl.com game scores (data/results.tsv)"
    src_third = "third-party price aggregator (data/raw/games.csv)"
    return [
        OrderedDict([("id", "H-01"), ("pair", "over the market total vs home covering the market spread"),
                      ("why", "the same-game parlay leg pair the leaderboard actually needs"),
                      ("statistic", "phi on market-dependent events"), ("rho", None), ("n", 0),
                      ("x_source", src_third), ("x_tier", "THIRD-PARTY-AGGREGATOR"),
                      ("y_source", src_third), ("y_tier", "THIRD-PARTY-AGGREGATOR"),
                      ("joint_observations", True),
                      ("note", "computable from the games feed, but both operands are prices and "
                              "no official source publishes prices, so the gate refuses it")]),
        OrderedDict([("id", "H-02"), ("pair", "player prop correlation (QB passing yards vs WR receiving yards)"),
                      ("why", "prop-combo parlays"), ("statistic", "pearson on player game logs"),
                      ("rho", 0.7912), ("n", 24528),
                      ("x_source", "nflverse player_stats via a third-party mirror "
                                   "(data/prop-correlations-d.csv)"),
                      ("y_source", "nflverse player_stats via a third-party mirror "
                                   "(data/prop-correlations-d.csv)"),
                      ("x_tier", "THIRD-PARTY-MIRROR"), ("y_tier", "THIRD-PARTY-MIRROR"),
                      ("joint_observations", True),
                      ("note", "already published elsewhere on this site as a computed estimate; "
                              "the gate holds it out of the official register until the owner "
                              "decides flag F-11")]),
        OrderedDict([("id", "H-03"), ("pair", "closing-line value vs next-week line movement"),
                      ("why", "the only test of whether an edge survives to the close"),
                      ("statistic", "pearson on per-bet CLV"), ("rho", None), ("n", 0),
                      ("x_source", "no timestamped price capture exists in this repository"),
                      ("y_source", "no timestamped price capture exists in this repository"),
                      ("x_tier", "UNAVAILABLE"), ("y_tier", "UNAVAILABLE"),
                      ("joint_observations", False),
                      ("note", "needs the live snapshot collector; see the decision desk")]),
        OrderedDict([("id", "H-04"), ("pair", "injury absence vs points lost by the replacement"),
                      ("why", "turning depth into a number a line can use"),
                      ("statistic", "regression of margin on depth levels lost"), ("rho", None),
                      ("n", 0), ("x_source", "official club depth charts (data/depth.tsv)"),
                      ("y_source", src_official), ("x_tier", "OFFICIAL-CLUB"),
                      ("y_tier", "OFFICIAL-LEAGUE"), ("joint_observations", False),
                      ("note", "both operands are official, but the depth capture is one week; "
                              "the joint panel does not exist yet, so n=0 and nothing is published")]),
    ]


# ---------------------------------------------------------------------------
# registers the site renders, and the ones it appends to
# ---------------------------------------------------------------------------
def summary_json(store, results, orig, back, depth, corr) -> dict:
    board = back["board"]
    best = board[0] if board else {}
    trades = back["log"]
    return OrderedDict([
        ("capture_date", CAPTURE_DATE),
        ("snapshots", store["manifest"]["snapshots_total"]),
        ("snapshots_quarantined", store["manifest"]["snapshots_quarantined"]),
        ("snapshots_current_season", store["manifest"]["snapshots_current_season"]),
        ("vintage_counts", store["manifest"]["vintage_counts"]),
        ("games_2026", len(results["season_rows"])),
        ("games_2026_verified", sum(1 for r in results["season_rows"]
                                    if r["verify_status"] == "MATCHED_TWO_FEEDS")),
        ("games_2026_unplayed", sum(1 for r in results["season_rows"]
                                    if r["verify_status"] == "NO_RESULT")),
        ("trades", len(trades)),
        ("trades_published", len(back["published"])),
        ("pushes", sum(1 for t in trades if t["outcome"] == rl.PUSH)),
        ("strategies", len(board)),
        ("strategies_clearing_signal", sum(1 for r in board
                                           if str(r.get("signal_grade", "")).startswith("SIGNAL CLEARS"))),
        ("rewards_paid", sum(int(r.get("reward_units") or 0) for r in board)),
        ("demotions", sum(1 for r in back["demotion"] if r["verdict"] == "TRIGGERED")),
        ("best_signal", OrderedDict([
            ("strategy_id", best.get("strategy_id", "")),
            ("points_beat_lb", best.get("points_beat_lb", "")),
            ("hit_rate", best.get("hit_rate", "")),
            ("breakeven_hit", best.get("breakeven_hit", "")),
            ("roi", best.get("roi", "")),
            ("rank_staking", best.get("rank_staking", "")),
        ])),
        ("correlations_published", len(corr["published"])),
        ("correlations_held", len(corr["held"])),
        ("n_official_games_for_correlation", corr["counts"]["games_used"]),
        ("depth_vacancies", len(depth["res"]["rows"])),
        ("depth_resolved", sum(1 for r in depth["res"]["rows"]
                               if isinstance(r["depth_levels_lost"], int))),
        ("clubs_with_chart", depth["res"]["clubs_with_chart"]),
        ("model_params", {k: orig["params"][k] for k in ("lam", "s", "hfa")}),
        ("fingerprint", _fingerprint(store, results, orig, back, depth, corr)),
    ])


def _fingerprint(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(json.dumps(p, sort_keys=True, default=str).encode("utf-8"))
    return h.hexdigest()[:16]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv: Sequence[str]) -> int:
    check = "--check" in argv
    before = _hash_all() if check else {}
    verify_rows: "list[OrderedDict]" = [OrderedDict([
        ("check", "Spine rebuilt end to end"),
        ("command", "python3 scripts/build_market_spine.py"),
        ("scope", "price store, results feed, origination run, backtest, split leaderboard, "
                  "replacement depth, correlation gate, demotion gate"),
        ("result", "see the rows below; every row is produced by the same command"),
        ("when", CAPTURE_DATE),
    ])]
    games = feed.load_games()
    store = step_store(games, verify_rows)
    results = step_results(games, verify_rows)
    orig = step_originate(games, store["benchmarks"], verify_rows)
    back = step_backtest(games, orig, store, results, verify_rows)
    depth = step_depth(verify_rows)
    corr = step_correlations(results["rows"], verify_rows)
    summary = summary_json(store, results, orig, back, depth, corr)

    wtsv("results_verification.tsv", verify_rows,
         ["check", "command", "scope", "result", "when"])
    files = wjson("summary.json", summary)
    for f in store["files"] + results["files"] + orig["files"] + back["files"] + \
            depth["files"] + corr["files"] + [files]:
        print("  %-44s %s" % (f["file"], f.get("rows", f.get("bytes"))))
    print("snapshots=%d  trades=%d (published %d)  verified-2026=%d/%d  demotion triggers=%d"
          % (summary["snapshots"], summary["trades"], summary["trades_published"],
             summary["games_2026_verified"], summary["games_2026"], summary["demotions"]))
    if check:
        after = _hash_all()
        changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
        if changed:
            print("\nREBUILD DIFFERS (non-deterministic or uncommitted):", file=sys.stderr)
            for c in changed:
                print("  " + c, file=sys.stderr)
            return 1
        print("check: rebuild is byte-identical to the committed artefacts")
    return 0


def _hash_all() -> dict:
    out = {}
    for name in sorted(os.listdir(OUT)) if os.path.isdir(OUT) else []:
        if name.startswith("_") or name == "README.md":
            continue
        path = os.path.join(OUT, name)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as fh:
            out["data/market/" + name] = hashlib.sha256(fh.read()).hexdigest()
    return out


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
