#!/usr/bin/env python3
"""brief.py — session arena/685f958d-fl1 outputs.

Produces, from committed inputs only:
  data/model_lines.tsv         origination for the 13 pending Week 10 games (side -> total -> moneyline),
                               with FAIR, MARKET and DIFFERENCE as separate columns
  data/backtest_calibration.tsv walk-forward (strictly out-of-sample) error statistics by week
  data/price_snapshots.tsv     opening / closing store for every market we originate

and renders three pages through tools/site.py's shared layout:
  model-lines.html, results-feed.html, governance.html

Rules that this module enforces in code, not just in prose:
  * a MARKET or DIFFERENCE cell is written empty unless an official price source is registered
    for it (none is, so every such cell is empty and the reason is printed on the page);
  * no ROI is computed, because ROI needs prices;
  * every row carries the official URL it was checked against.

Run:  python3 tools/brief.py        (writes the data files; site.py renders the pages)
"""

import csv
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import originate as O  # noqa: E402

DATA = os.path.join(ROOT, "data")

NO_PRICE_SOURCE = ("no official NFL source publishes betting prices (GAP-01); "
                   "market cell left blank, see Flagged F18")


def _tsv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def _write_tsv(name, header, rows):
    path = os.path.join(DATA, name)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(["" if r.get(h) is None else r.get(h) for h in header])
    return path


def load_results():
    """Final 2026 results, reconciled in data/results.tsv. Neutral-site flag joins from the
    schedule feed (third-party attribute, recorded as such in the page)."""
    neutral = {}
    with open(os.path.join(DATA, "schedule2026-d.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["played"] == "yes":
                neutral[(int(r["week"]), r["away_team"], r["home_team"])] = r["neutral_site"] == "Neutral"
    games = []
    with open(os.path.join(DATA, "results.tsv"), encoding="utf-8") as fh:
        for row in csv.reader(fh, delimiter="\t"):
            w, date, away, ap, home, hp = row
            key = (int(w), away, home)
            games.append(O.Game(int(w), away, home, int(ap), int(hp), neutral.get(key, False)))
    return games


def load_slate():
    return _tsv(os.path.join(DATA, "slate-w10-2026.tsv"))


def compute():
    games = load_results()
    model = O.fit(games)
    bt = O.walk_forward(games, first_week=4)
    summary = O.summarise_backtest(bt)
    model.sigma = summary["rmse"]                    # moneyline sigma: out-of-sample RMSE
    slate = load_slate()
    records = []
    for s in slate:
        neutral = s["neutral_venue"] == "yes"
        rec = O.originate_game(model, s["away"], s["home"], neutral)
        rec.update({"week": s["week"], "date": s["date"], "kickoff_et": s["kickoff_et"],
                    "network": s["network"], "away": s["away"], "home": s["home"],
                    "neutral": neutral, "url": s["official_game_url"]})
        records.append(rec)
    return {"games": games, "model": model, "bt": bt, "summary": summary,
            "weekly": O.weekly_backtest(bt), "records": records}


def _line_text(team_fav, line):
    return "%s %+.1f" % (team_fav, line)


def write_data(c):
    model, recs = c["model"], c["records"]
    header = ["week", "date", "kickoff_et", "away", "home", "neutral_venue", "step_order",
              "side_fair_home_spread", "side_fair_raw", "side_market_home_spread", "side_difference",
              "total_fair", "total_fair_raw", "total_market", "total_difference",
              "ml_fair_home", "ml_fair_away", "ml_market_home", "ml_market_away", "ml_difference",
              "hfa_used", "sigma", "n_fit", "source_url", "market_status"]
    rows = []
    for r in recs:
        home_line = r["fair_home_spread"]
        rows.append({
            "week": r["week"], "date": r["date"], "kickoff_et": r["kickoff_et"],
            "away": r["away"], "home": r["home"],
            "neutral_venue": "yes" if r["neutral"] else "no",
            "step_order": "1 side > 2 total > 3 moneyline",
            "side_fair_home_spread": "%+.1f" % home_line if home_line else "0.0",
            "side_fair_raw": "%.2f" % r["fair_home_spread_raw"],
            "side_market_home_spread": "", "side_difference": "",
            "total_fair": "%.1f" % r["fair_total"], "total_fair_raw": "%.2f" % r["fair_total_raw"],
            "total_market": "", "total_difference": "",
            "ml_fair_home": "%+d" % r["fair_ml_home"], "ml_fair_away": "%+d" % r["fair_ml_away"],
            "ml_market_home": "", "ml_market_away": "", "ml_difference": "",
            "hfa_used": "0 (neutral)" if r["neutral"] else "%.2f" % model.hfa,
            "sigma": "%.2f" % model.sigma, "n_fit": model.n_fit,
            "source_url": r["url"], "market_status": NO_PRICE_SOURCE,
        })
    _write_tsv("model_lines.tsv", header, rows)

    bt_header = ["scope", "n_out_of_sample", "side_mae_model", "side_mae_constant", "side_bias",
                 "side_sign_n", "side_sign_hit_rate", "side_sign_ci95_low", "side_sign_ci95_high",
                 "total_mae_model", "total_mae_constant", "total_bias",
                 "ml_brier_model", "ml_brier_coinflip", "roi", "note"]
    bt_rows = []
    for w in c["weekly"]:
        bt_rows.append(_bt_row("week %d" % w["week"], w))
    bt_rows.append(_bt_row("all weeks 4-10", c["summary"]))
    for r in bt_rows:
        r["roi"] = ""
        r["note"] = ("ROI not computed: no official betting prices exist to price the bets"
                     if r["scope"].startswith("all") else "")
    _write_tsv("backtest_calibration.tsv", bt_header, bt_rows)

    ps_header = ["week", "date", "away", "home", "market", "open_line", "open_price", "open_time_utc",
                 "close_line", "close_price", "close_time_utc", "book", "source_url", "status"]
    ps_rows = []
    for r in recs:
        for market in ("SIDE", "TOTAL", "MONEYLINE"):
            ps_rows.append({"week": r["week"], "date": r["date"], "away": r["away"], "home": r["home"],
                            "market": market, "source_url": r["url"],
                            "status": "NOT CAPTURED — no official price source (GAP-01)"})
    _write_tsv("price_snapshots.tsv", ps_header, ps_rows)
    return len(rows), len(bt_rows), len(ps_rows)


def _bt_row(scope, s):
    def f(x, nd=2):
        return "" if x is None else ("%.*f" % (nd, x))
    lo, hi = s.get("sign_ci") or (None, None)
    return {"scope": scope, "n_out_of_sample": s.get("n", 0),
            "side_mae_model": f(s.get("mae")), "side_mae_constant": f(s.get("mae_benchmark")),
            "side_bias": f(s.get("bias")), "side_sign_n": s.get("sign_n", 0),
            "side_sign_hit_rate": f(s.get("sign_rate"), 3),
            "side_sign_ci95_low": f(lo, 3), "side_sign_ci95_high": f(hi, 3),
            "total_mae_model": f(s.get("total_mae")), "total_mae_constant": f(s.get("total_mae_benchmark")),
            "total_bias": f(s.get("total_bias")),
            "ml_brier_model": f(s.get("brier_model"), 4), "ml_brier_coinflip": f(s.get("brier_coinflip"), 4)}


def main():
    c = compute()
    a, b, d = write_data(c)
    s = c["summary"]
    print("model_lines rows=%d backtest rows=%d price-store rows=%d" % (a, b, d))
    print("fit on %d games; HFA %.2f; out-of-sample n=%d" % (c["model"].n_fit, c["model"].hfa, s["n"]))
    print("side MAE %.2f vs constant %.2f | sign %.3f CI %s | total MAE %.2f vs %.2f | Brier %.4f vs %.4f" % (
        s["mae"], s["mae_benchmark"], s["sign_rate"], tuple(round(x, 3) for x in s["sign_ci"]),
        s["total_mae"], s["total_mae_benchmark"], s["brier_model"], s["brier_coinflip"]))


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------------------
# Rendering. Uses tools/site.py's shared layout (page, table, cell) so the new pages look
# and navigate like the rest of the site. Called from site.main().
# ---------------------------------------------------------------------------------------

def _td(html, cls=""):
    return '<td%s>%s</td>' % (' class="%s"' % cls if cls else "", html)


def _link(url, label=None):
    label = label or url.replace("https://www.nfl.com/", "nfl.com/")
    return '<a href="%s" rel="noopener">%s</a>' % (url, _esc(label))


def _esc(s):
    import html as H
    return H.escape("" if s is None else str(s))


def _blank(title="No official source confirms this value — left blank on purpose"):
    return '<td class="blank" title="%s">—</td>' % _esc(title)


def _fav(away, home, home_line):
    x = float(home_line)
    if abs(x) < 1e-9:
        return "Pick'em"
    if x < 0:
        return "%s %.1f" % (home, x)
    return "%s -%.1f" % (away, x)


def render(site):
    """Write model-lines.html, results-feed.html and governance.html. Returns filenames."""
    from engine import gates as G, leaderboard as L

    c = compute()
    write_data(c)
    recs = c["records"]
    s = c["summary"]
    written = []

    # ---- model-lines.html -------------------------------------------------------------
    rows = []
    for r in recs:
        rows.append(
            "<tr>" + _td(_esc(r["week"])) + _td(_esc(r["date"])) + _td(_esc(r["kickoff_et"]))
            + _td("<strong>%s</strong> @ %s" % (_esc(r["away"]), _esc(r["home"])))
            + _td(_esc(_fav(r["away"], r["home"], r["fair_home_spread"])), "num")
            + _blank("Market side: no official price source (F18)")
            + _td(_esc("%.1f" % r["fair_total"]), "num")
            + _blank("Market total: no official price source (F18)")
            + _td(_esc("%+d" % r["fair_ml_home"]), "num") + _td(_esc("%+d" % r["fair_ml_away"]), "num")
            + _blank("Market moneyline: no official price source (F18)")
            + _td(_link(r["url"], "official game page"))
            + _td(_esc("F18, F20, F21" if r["neutral"] else "F18, F20"))
            + "</tr>")
    slate_tbl = site.table(
        ["Wk", "Date", "KO (ET)", "Game", "Step 1 · Fair side", "Market side", "Difference (side)",
         "Step 2 · Fair total", "Market total", "Difference (total)", "Step 3 · Fair ML home",
         "Step 3 · Fair ML away", "Market ML", "Difference (ML)", "Source (official)", "Flags"],
        rows, cls="dense searchable",
        caption="Pending Week 10 games in order: side, then total, then moneyline. Fair = this model. "
                "Market and difference columns are blank because no official NFL source publishes prices.")

    steps = """
<section>
<h2>Origination order</h2>
<div class="callout">
<ol>
<li><strong>Side first.</strong> Team ratings are fitted by least squares to the 137 reconciled 2026
results (home margin on team ratings plus a home-field term; neutral venues get no home-field term).
The fair home line is the negative of the predicted home margin, rounded to the nearest half point.</li>
<li><strong>Total second.</strong> Expected points for each side use season-to-date points for and
against: (home PF/g + away PA/g) / 2 for the home side, and the mirror for the away side. The step
does not read the side, but it runs after it by design.</li>
<li><strong>Moneyline third.</strong> The win probability is &Phi;(predicted home margin / &sigma;), where
&sigma; = %.2f is the out-of-sample RMSE of the side model. The price is the fair American price for
that probability, with no vig, so it is a fair price and not a market price.</li>
</ol>
<p><strong>Fair, market, difference.</strong> These are three separate columns for each market. The fair
value comes from this model. The market value would come from an official price source, and none exists,
so every market cell is blank (F18). The difference is computed only when both sides exist, so it is blank
too. <strong>The backtest does not show that the model beats a constant benchmark on margin or total</strong>
(F20), so no fair line on this page is a recommendation.</p>
</div>
</section>"""

    store_rows = []
    for ps in _tsv(os.path.join(DATA, "price_snapshots.tsv")):
        store_rows.append(
            "<tr>" + _td(_esc(ps["week"])) + _td(_esc(ps["away"] + " @ " + ps["home"]))
            + _td(_esc(ps["market"]))
            + _blank("Opening line: not captured (no official source)") + _blank("Opening price: not captured")
            + _blank("Closing line: not captured (no official source)") + _blank("Closing price: not captured")
            + _td(_link(ps["source_url"], "official game page"))
            + _td(_esc(ps["status"])) + "</tr>")
    store_tbl = site.table(
        ["Wk", "Game", "Market", "Opening line", "Opening price", "Closing line", "Closing price",
         "Source (official)", "Status"],
        store_rows, cls="dense searchable",
        caption="Price-snapshot store: one row for each market we originate. Every price cell is blank because "
                "the store has no official source to fill it from. The store is the place a feed would write to.")

    model_body = ("<h1>Line Origination &amp; Price Store</h1>"
                  "<p class=\"lede\">Our own fair lines for the 13 pending Week 10 games, the order they are built in, "
                  "and the price store that would hold opening and closing numbers. Model output only. Nothing here "
                  "is a bet or advice.</p>"
                  + steps + "<section><h2>Pending games: fair, market and difference</h2>" + slate_tbl + "</section>"
                  + "<section><h2>Price-snapshot store (every market we originate)</h2>"
                  "<p>Opening and closing numbers are stored per game and per market. No value can be filled "
                  "in from this repo, so every field is blank and listed as not captured.</p>"
                  + store_tbl + "</section>")
    written.append(site.page("model-lines.html", "Line Origination & Price Store", model_body, wide=True))

    # ---- results-feed.html ------------------------------------------------------------
    bt_rows = []
    for w in c["weekly"]:
        bt_rows.append(_bt_html(w["week"], w))
    bt_rows.append(_bt_html("All weeks 4–10 (out of sample)", s, total=True))
    bt_tbl = site.table(
        ["Scope", "n (out of sample)", "Side MAE (model)", "Side MAE (constant)", "Sign hit rate",
         "95% CI", "Total MAE (model)", "Total MAE (constant)", "ML Brier (model)", "ML Brier (50/50)", "ROI"],
        bt_rows, cls="dense",
        caption="Walk-forward backtest. Each week is predicted only from earlier weeks. n is shown on every row. "
                "ROI is blank: it needs official prices, and none exist (F18).")

    res_rows = []
    for g in c["games"]:
        res_rows.append(
            "<tr>" + _td(_esc(g.week)) + _td(_esc(g.away)) + _td(_esc(g.away_pts), "num")
            + _td(_esc(g.home)) + _td(_esc(g.home_pts), "num")
            + _td(_esc("%+d" % g.margin_home), "num")
            + _td(_link("https://www.nfl.com/schedules/2026/by-week/week-%d" % g.week, "week %d page" % g.week))
            + _td("aggregate reconciled (F22)" + ("; per game re-read" if g.week == 10 else "")) + "</tr>")
    res_tbl = site.table(
        ["Wk", "Away", "Away pts", "Home", "Home pts", "Home margin", "Source (official week page)", "Verification"],
        res_rows, cls="dense searchable",
        caption="All 137 final 2026 results used as model inputs. Per-game scores were re-read from the official "
                "page only for Week 10; Weeks 1–9 are reconciled to the official standings in aggregate (F22).")

    results_body = ("<h1>Verified Results Feed &amp; Backtest</h1>"
                    "<p class=\"lede\">The results that every model and backtest here is built on, and what a backtest "
                    "can and cannot show. Without official prices, calibration can be measured but ROI cannot.</p>"
                    "<section><h2>What can be computed right now</h2><div class=\"callout\"><ul>"
                    "<li><strong>Calibration and error</strong>: yes. Out-of-sample margin, total and win-probability "
                    "errors, each with n.</li>"
                    "<li><strong>ROI and closing-line value</strong>: no. Both need official opening and closing prices, "
                    "which are not available (F18).</li>"
                    "<li><strong>Correlations</strong>: no official joint sample yet (F19).</li></ul></div></section>"
                    "<section><h2>Backtest</h2>" + bt_tbl + "</section>"
                    "<section><h2>Results feed</h2>" + res_tbl + "</section>")
    written.append(site.page("results-feed.html", "Verified Results Feed & Backtest", results_body, wide=True))

    # ---- governance.html --------------------------------------------------------------
    # worked examples computed by the engine itself, so the page cannot drift from the code
    bets = [{"game_id": f"g{i}", "won": False, "pnl": -1.0, "stake": 1.0} for i in range(35)]
    bets += [{"game_id": f"w{i}", "won": True, "pnl": 9.1, "stake": 10.0} for i in range(5)]
    ent = L.Entry(entry_id="worked-example", author="docs", division="example", bets=bets)
    ss = L.split_scores(ent, n_boot=2000)
    lucky_row = [
        _td("Worked example: 35 one-unit losses and 5 ten-unit wins (price −110)"),
        _td(_esc("%d" % ss["signal_n"]), "num"),
        _td(_esc("%.4f" % ss["signal_mean"]), "num"),
        _td(_esc("%.4f" % ss["signal_lcb"]) if ss["signal_lcb"] is not None else "", "num"),
        _td(_esc("%.4f" % ss["staking_yield"]), "num"),
        _td(_esc("yes — staking is positive while the signal is not" if ss["masking_flag"] else "no")),
        _td(_esc("no — rank uses the signal lower bound only" if not ss["staking_reward_eligible"] else "yes")),
    ]
    split_tbl = site.table(
        ["Example", "Settled bets (n)", "Signal mean / unit", "Signal lower bound (95%)",
         "Staking yield", "Masking flag", "Staking reward"],
        ["<tr>" + "".join(lucky_row) + "</tr>"], cls="dense",
        caption="Signal is the equal-weight per-unit return (ranks the board). Staking is the dollar-weighted yield "
                "(reported, never ranks). Values are produced by engine/leaderboard.py.")

    def _gate_row(label, n, dec):
        return "<tr>" + _td(_esc(label)) + _td(_esc(str(n)), "num") + _td(_esc(dec)) + "</tr>"
    dem = [G.demotion_decision([{"game_id": f"g{i}", "won": False, "pnl": -1.0, "stake": 1.0} for i in range(100)]),
           G.demotion_decision([{"game_id": f"g{i}", "won": False, "pnl": -1.0, "stake": 1.0} for i in range(99)]),
           G.demotion_decision([{"game_id": f"g{i}", "won": (i % 10 < 7), "pnl": (0.91 if i % 10 < 7 else -1.0),
                                 "stake": 1.0} for i in range(100)])]
    dem_rows = [
        _gate_row("100 settled live bets, every one a 1-unit loss", 100, dem[0]["decision"] + " (" + dem[0]["state_after"] + ")"),
        _gate_row("99 settled live bets, every one a 1-unit loss", 99, dem[1]["decision"] + " (" + dem[1]["state_after"] + ")"),
        _gate_row("100 bets, 70% wins at +0.91 and 30% losses at −1", 100, dem[2]["decision"] + " (" + dem[2]["state_after"] + ")"),
    ]
    gate_tbl = site.table(["Example", "Settled live bets", "Decision (state after)"],
                          dem_rows, cls="dense",
                          caption="G-14 demotion gate, run by engine/gates.py. These are worked examples, not results.")

    rule_rows = [
        "<tr>" + _td("R1 Exposure") + _td("any live stake above the 2-unit cap") + _td("Demote to PAPER, immediately") + _td(_esc("internal rule (engine/gates.py); thresholds are proposals, see suggestions")) + "</tr>",
        "<tr>" + _td("R2 Sample") + _td("fewer than 100 settled live bets") + _td("No decision; stays LIVE and is reported as insufficient") + _td(_esc("internal rule")) + "</tr>",
        "<tr>" + _td("R3 Signal") + _td("95% lower bound of the per-unit return over the last 100 bets is below zero") + _td("Demote to PAPER") + _td(_esc("internal rule")) + "</tr>",
        "<tr>" + _td("R4 CLV") + _td("95% lower bound of closing-line value over the last 100 bets is below zero (not evaluated if CLV is absent)") + _td("Demote to PAPER") + _td(_esc("internal rule; CLV not available (F18)")) + "</tr>",
        "<tr>" + _td("Re-promotion") + _td("250 settled paper bets with a positive signal lower bound and no exposure breach") + _td("Return to LIVE") + _td(_esc("internal rule")) + "</tr>",
    ]
    rules_tbl = site.table(["Rule", "Trigger", "Action", "Source"], rule_rows, cls="dense")

    corr_rows = []
    import csv as _csv
    with open(os.path.join(DATA, "prop-correlations-d.csv"), encoding="utf-8") as fh:
        for r in _csv.DictReader(fh):
            corr_rows.append(
                "<tr>" + _td(_esc(r["pair_id"])) + _td(_esc(r["window"])) + _td(_esc(r["n"]), "num")
                + _blank("withheld: third-party source (F19)")
                + _td(_esc("official joint sample: 0 (F19)")) + "</tr>")
    corr_tbl = site.table(["Pair", "Window", "n (sample behind it)", "Value", "Official-source n"],
                          corr_rows, cls="dense searchable",
                          caption="Correlation values are withheld under brief B6. The sample size n is kept for every "
                                  "pair. The source of n is a third-party mirror (nflverse), so it is shown as a sample "
                                  "size only, not a verified fact.")

    gov_body = ("<h1>Signal, Staking &amp; Demotion</h1>"
                "<p class=\"lede\">How the leaderboard keeps a lucky staking run from hiding a bad signal, when a live "
                "strategy goes back to paper, and why no correlation value is published yet.</p>"
                "<section><h2>1. Signal versus staking</h2><div class=\"callout\"><p>The board ranks on the signal alone: "
                "the 95% lower bound of the equal-weight per-unit return of every settled bet. Staking is reported "
                "beside it as dollar-weighted yield and cannot change the rank. A staking reward needs both the signal "
                "and the staking bound to be above zero, so staking can add to a strong signal but cannot rescue a weak one.</p></div>"
                + split_tbl + "</section>"
                "<section><h2>2. Demotion gate G-14: live back to paper</h2>"
                "<div class=\"callout\"><p>A live strategy returns to paper when a trigger fires. Paper is not a penalty "
                "box: the strategy keeps accumulating paper bets, and only a full window of positive paper results "
                "returns it to live. Thresholds are proposals for owner decision (see the suggestions register).</p></div>"
                + rules_tbl + gate_tbl + "</section>"
                "<section><h2>3. Correlations: official sources only</h2>"
                "<div class=\"callout\"><p>Brief B6: correlations are computed only from officially sourced numbers, and n "
                "is published with each value. The 2026 official results and the official injury report do not contain "
                "enough joint observations for a correlation, and every priced pair needs official prices that do not exist. "
                "Nothing is published as a coefficient.</p></div>"
                + corr_tbl + "</section>")
    written.append(site.page("governance.html", "Signal, Staking & Demotion", gov_body, wide=True))
    return written


def _bt_html(label, s, total=False):
    def f(x, nd=2):
        return "" if x is None else ("%.*f" % (nd, x))
    lo, hi = s.get("sign_ci") or (None, None)
    cells = [
        _td(_esc(label) + (" <em>(total)</em>" if total else "")),
        _td(_esc(s.get("n", 0)), "num"),
        _td(_esc(f(s.get("mae"))), "num"),
        _td(_esc(f(s.get("mae_benchmark"))), "num"),
        _td(_esc(f(s.get("sign_rate"), 3)), "num"),
        _td(_esc("%s–%s" % (f(lo, 3), f(hi, 3))) if lo is not None else "", "num"),
        _td(_esc(f(s.get("total_mae"))), "num"),
        _td(_esc(f(s.get("total_mae_benchmark"))), "num"),
        _td(_esc(f(s.get("brier_model"), 4)), "num"),
        _td(_esc(f(s.get("brier_coinflip"), 4)), "num"),
        _blank("ROI needs official prices (F18)"),
    ]
    return "<tr>" + "".join(cells) + "</tr>"


if __name__ == "__main__" and "--pages" in sys.argv:
    import importlib.util
    spec = importlib.util.spec_from_file_location("fl1_site", os.path.join(ROOT, "tools", "site.py"))
    site_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(site_mod)
    print(render(site_mod))


def exec_banner():
    """Callout placed at the top of the executive summary. Every number is computed here."""
    c = compute()
    s = c["summary"]
    return (
        '<div class="callout"><p><strong>Update (session arena/685f958d-fl1, 2026-11-14).</strong> '
        'Own fair lines are now published for the 13 pending Week 10 games, in the order side, total, then '
        'moneyline, with fair, market and difference as separate columns. <strong>No market column is filled</strong>: '
        'no official NFL source publishes prices (F18). In a walk-forward backtest on %d out-of-sample games (weeks 4–10), '
        'the side model hits %.1f%% of winners (95%% CI %.1f%%–%.1f%%), but its margin error (%.2f points) does not beat a constant '
        'benchmark (%.2f). The total model does not beat its benchmark either (F20). Correlations are withheld (F19). '
        'The leaderboard ranks on signal and reports staking beside it, and the G-14 gate sends a live strategy back to paper. '
        'See <a href="model-lines.html">Model Lines</a>, <a href="results-feed.html">Results Feed</a> and '
        '<a href="governance.html">Signal &amp; Demotion</a>.</p></div>' % (
            s["n"], 100 * s["sign_rate"], 100 * s["sign_ci"][0], 100 * s["sign_ci"][1],
            s["mae"], s["mae_benchmark"]))
