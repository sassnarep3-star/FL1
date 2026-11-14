"""The registers a human actually reads: suggestions, open questions, decision rules.

Single source of truth: `pipelines.build_site` renders these into the site, and
`--docs` writes them out as markdown, so the site and the repo docs can never disagree.

Every entry is written to be *actionable by one person with a decision to make*, and every
"what we know" line names an official page that was actually read this session.
"""

from __future__ import annotations

# --------------------------------------------------------------------------------------
# SUGGESTIONS — ranked so a reviewer can pick a path, not wade through a wishlist.
# --------------------------------------------------------------------------------------
SUGGESTIONS: list[dict] = [
    {"id": "S-01", "title": "Adopt one licensed closing-line source and make it a first-class dataset",
     "problem": "The NFL publishes no betting lines, so nothing in this repo can currently answer 'is our "
                "number better than the market's?' — which is the whole question a line-origination "
                "project exists to answer.",
     "proposal": "Pick a single provider (SportsDataIO / The Odds API / an exchange-grade feed), store "
                 "open and close per market with a fetch timestamp, and treat the file as immutable once "
                 "written. Record the licence and the retention terms next to the data.",
     "effort": "M", "depends_on": "budget decision",
     "unblocks": "edge (G2), closing-line value (G3), capacity (G9), and every reward tier above 3.",
     "risk_if_skipped": "Every strategy stays unfundable forever, and the leaderboard degrades into a "
                        "ranking of whoever got lucky on a small sample.",
     "priority": 1},
    {"id": "S-02", "title": "Wire the official transaction ledger (IR / PUP / active) into availability",
     "problem": "The weekly injury report only lists players a club submitted that week. A man on "
                "injured reserve never appears, so a report-only layer scores him as available. This "
                "session found Baltimore's Week 10 report contains zero quarterback rows while the "
                "league's own news feed has both of Baltimore's top two quarterbacks confirmed out.",
     "proposal": "Ingest the club transaction lists daily and maintain a season-long 'who is physically "
                  "unable to play' set, then join it to the weekly report. Delete the hand-maintained "
                  "correction file once the feed exists.",
     "effort": "S", "depends_on": "none",
     "unblocks": "an availability layer that is right for star players, not just for week-to-week "
                 "bumps; also removes the only hand-edited file in the pipeline.",
     "risk_if_skipped": "The largest single errors in the model are the absences it cannot see — i.e. "
                        "exactly the players who move lines most.",
     "priority": 1},
    {"id": "S-03", "title": "Build an effective-depth table from official participation data instead of a depth chart",
     "problem": "No official depth-chart page exists — the URL 404s and the obvious third-party "
                 "structured endpoint returns an empty object. 'Which string replaces the starter' is "
                 "therefore unanswered, and 159 of the 163 absence-weighted report rows sit in the shadow ledger because "
                 "starter status cannot be confirmed.",
     "proposal": "Derive depth from behaviour rather than from a coach's chart: take each club's "
                 "official game-level participation (who actually lined up, by snap share) across the "
                 "season and rank positions by snaps. That answers 'who would have started' and "
                 "'what is the drop-off' from data that is published, not requested.",
     "effort": "L", "depends_on": "a participation feed (see S-14)",
     "unblocks": "the 2nd/3rd/4th-string deficiency rating the brief asks for, and moves the "
                 "availability adjustment from shadow to applied for most clubs.",
     "risk_if_skipped": "The model keeps only the absences a headline happened to name, and the shadow "
                        "column keeps being much larger than the applied column — a visible, permanent "
                        "admission that most of the signal is unusable.",
     "priority": 1},
    {"id": "S-04", "title": "Snapshot the injury report on the league's own cadence, with a hash per snapshot",
     "problem": "The report page prints no 'as of' time, so a row cannot be tied to the designation "
                "deadline it reflects (Wednesday practice report, Thursday, or the final Friday "
                "designation) — and those are materially different documents.",
     "proposal": "Fetch three times a week, name each snapshot by (week, cadence), store a sha256, and "
                 "publish the diff between consecutive snapshots.",
     "effort": "S", "depends_on": "a scheduler",
     "unblocks": "line-movement-vs-report-timing studies, and any claim that a status 'was final'.",
     "risk_if_skipped": "Every historical backtest is contaminated: the 'pregame' status used might be "
                        "the post-announcement one.",
     "priority": 2},
    {"id": "S-05", "title": "Stamp every input with the kickoff it precedes, and refuse to score anything else",
     "problem": "Week 10 was mid-flight during this read: the Thursday game had already finished "
                "(24-21) while the report still printed its pregame designations. The model had to "
                "notice that and exclude the game by hand.",
     "proposal": "Make it structural: each snapshot carries `for_kickoff_before`, and the scorer raises "
                 "if a bet's inputs postdate its kickoff.",
     "effort": "S", "depends_on": "none",
     "unblocks": "trustworthy accuracy claims, and gate G10 automatically.",
     "risk_if_skipped": "Leakage. It is the cheapest way for a backtest to look brilliant and be worth "
                        "nothing.",
     "priority": 1},
    {"id": "S-06", "title": "Key every join on the official player id, never on a printed name",
     "problem": "The same official page prints 'Chig Okonkwo' but links /players/chigoziem-okonkwo/, "
                 "prints 'Jacob Hummel' linking /players/jake-hummel/, prints 'Kam Curl' linking "
                 "/players/kamren-curl/ and prints 'Chris Brooks' linking /players/christopher-brooks/. "
                 "Four name/id mismatches in one week's report.",
     "proposal": "Store the numeric/slug id as the key and the display name as an attribute; add a "
                 "validator that fails when a join is attempted on the display name.",
     "effort": "S", "depends_on": "none",
     "unblocks": "joining injuries to stats to lines to props without silently dropping rows.",
     "risk_if_skipped": "Missing rows that look like 'player was available', which is the worst "
                        "direction for an availability model to be wrong.",
     "priority": 2},
    {"id": "S-07", "title": "Stop scraping the rendered stat table; read the structured endpoint it is built from",
     "problem": "The rendered club stat pages concatenate values ('4814.4' for plays and yards, "
                 "'13722556.4' for completions/attempts/interceptions/average), and their total-offence "
                 "line does not equal rushing + passing for any of the 7 clubs read. That is 4 of the "
                 "most useful efficiency inputs unavailable, and 1 actively misleading.",
     "proposal": "Pull the JSON behind the same page (or the league's stats endpoint), store it raw, and "
                 "keep the rendered table only as a cross-check.",
     "effort": "M", "depends_on": "none",
     "unblocks": "yards-per-play, success rate and pressure-rate features; removes flag F-05/F-06.",
     "risk_if_skipped": "A model that keeps using a yards figure whose definition nobody has confirmed.",
     "priority": 2},
    {"id": "S-08", "title": "Publish home/road/division/conference splits from per-game pages",
     "problem": "The standings page prints 16 columns for 14 legend labels, so venue splits could not be "
                 "mapped without guessing and are absent from the repo — which is also why home-field "
                 "advantage is a guessed prior instead of a measured number.",
     "proposal": "Derive them from the official per-game schedule pages (each one names the venue and both "
                  "scores) and store a real home/road table.",
     "effort": "M", "depends_on": "none",
     "unblocks": "calibrating home_field (currently a prior) and venue/weather interaction.",
     "risk_if_skipped": "The single largest structural term in every total and spread stays uncalibrated.",
     "priority": 2},
    {"id": "S-09", "title": "Calibrate the three priors before any money, and treat today's G8 FAIL as a stop sign",
     "problem": "Perturbing one prior by 20% moves the published spread by up to 3.0 points on this "
                 "week's slate. The stability sweep fails gate G8, which is the honest statement that "
                 "v0's lines are still substantially a function of its assumptions.",
     "proposal": "Fit shrink_to_mean, home_field and sigma on 5+ seasons of official results plus "
                  "closing lines, then re-run the same sweep and require PASS.",
     "effort": "M", "depends_on": "S-01",
     "unblocks": "any use of these numbers for staking; converts model output into a decision input.",
     "risk_if_skipped": "Betting a number that a 20% change in a guess would rewrite by 3 points.",
     "priority": 1},
    {"id": "S-10", "title": "Make venue, weather and travel explicit inputs for totals",
     "problem": "Week 10 includes an outdoor 9:30 AM European kickoff (Patriots at Lions, Munich) "
                 "alongside three dome games and a 4:05 PM Las Vegas game. A scoring model that cannot "
                 "see the venue cannot see any of that, and this repo currently cannot see it.",
     "proposal": "Store stadium + roof + kickoff local time + a game-time weather forecast per game, "
                 "and add a documented venue adjustment for totals only.",
     "effort": "M", "depends_on": "a weather source decision",
     "unblocks": "a genuine totals edge, where availability and venue effects are largest.",
     "risk_if_skipped": "Totals stay a pure points-rate extrapolation — the most efficient market in "
                        "football betting, so the least likely to pay.",
     "priority": 3},
    {"id": "S-11", "title": "Create the bet ledger schema now, append-only, before the first real bet",
     "problem": "The leaderboard is only as trustworthy as the record. Backfilling a ledger invites "
                 "exactly the selection effects this project is built to remove.",
     "proposal": "One row per bet with: model probabilities, inputs hash, market price, stake rule, "
                 "kickoff, snapshot timestamps, settlement, close price. Append-only, signed by the "
                 "commit that placed it.",
     "effort": "S", "depends_on": "none",
     "unblocks": "G1, G4, G7 for real instead of on synthetic fixtures.",
     "risk_if_skipped": "Every future claim becomes unauditable, and 'we' cannot tell skill from a "
                        "remembered highlight.",
     "priority": 1},
    {"id": "S-12", "title": "Ship an explicit do-not-bet exclusion list, evaluated before signals",
     "problem": "Some information is in the line already or is unknowable pre-game; competing there is "
                 "where a decent model goes to die.",
     "proposal": "Encode exclusions as a first-class filter (already-decided games, markets without a "
                  "closing source, bets on teams whose availability ledger is >50% shadow, any prop "
                  "until participation data exists).",
     "effort": "S", "depends_on": "none",
     "unblocks": "a smaller, cleaner signal set whose edge is measurable.",
     "risk_if_skipped": "Dilution: the strategy looks bad in aggregate because half its bets were "
                        "structurally priced to lose.",
     "priority": 2},
    {"id": "S-13", "title": "Enforce the correlation cap at order time, not in the post-mortem",
     "problem": "Parlays get sold as multiplied legs; the correct price is a joint probability. The "
                 "bivariate integrator exists in model/correlation.py, and the cap is written as gate "
                 "G6, but nothing stops a ticket being built today.",
     "proposal": "Make the parlay builder refuse any leg pair whose rho is unknown, and price the rest "
                  "through the joint integral. Log the matrix used with each ticket.",
     "effort": "S", "depends_on": "S-01 for pricing, not for the cap",
     "unblocks": "safe multi-leg products; makes G6 an implementation rather than an aspiration.",
     "risk_if_skipped": "The strategy that looks best in a bull week is the one stacking two legs that "
                        "are the same bet twice.",
     "priority": 2},
    {"id": "S-14", "title": "Add a player-participation feed as the foundation of the prop layer",
     "problem": "Props need snap shares, routes, target share and red-zone share. Nothing in the repo "
                 "has any of them, so every prop row is definitionally unverified.",
     "proposal": "Source official/next-gen participation data, store per-game per-player, and build prop "
                  "projections as usage-weighted rates rather than season totals.",
     "effort": "L", "depends_on": "a data purchase",
     "unblocks": "the entire player-prop and prop-combo product, plus the same-player correlation term.",
     "risk_if_skipped": "The prop market — historically the softest — stays closed.",
     "priority": 3},
    {"id": "S-15", "title": "Record line history (open / interim / close) as its own dataset",
     "problem": "CLV is defined against the close, and 'did we beat the close' is the single best "
                 "early proxy for skill. Without history there is also no way to study how much of the "
                 "availability signal the market already absorbed.",
     "proposal": "Persist every quote with a timestamp per market; expose 'time since last move' as a "
                  "feature and as a diagnostic.",
     "effort": "M", "depends_on": "S-01",
     "unblocks": "G3, plus a direct read on whether injury news is over- or under-reacted.",
     "risk_if_skipped": "The project can never distinguish 'we are early' from 'we are wrong'.",
     "priority": 2},
    {"id": "S-16", "title": "Rank strategies within a market type, never across market types on one score",
     "problem": "On the fixture ledger the highest composite score belongs to a 3-leg prop parlay "
                 "strategy that fails five gates, while the sharpest single-bet strategy ranks second. "
                 "A z-score composite is not comparable across bet shapes.",
     "proposal": "Separate leaderboards per market family (side / total / prop / parlay) with a shared "
                  "gate requirement, and only compare tiers within a board.",
     "effort": "S", "depends_on": "S-11",
     "unblocks": "a reward system that cannot be won by bet-type mix alone.",
     "risk_if_skipped": "Rewards pay the strategy with the friendliest variance, not the best edge.",
     "priority": 2},
    {"id": "S-17", "title": "Size the portfolio, not the bet: correlation-aware Kelly with caps",
     "problem": "Half-Kelly per bet ignores that eleven Sunday legs share one slate, one weather "
                 "pattern and one market-maker. Independent sizing on dependent bets over-bets exactly "
                 "when it looks safest.",
     "proposal": "Optimise stake across the slate subject to a joint covariance matrix built from the "
                  "leg-pair rho table, a per-game exposure cap and a per-slate cap.",
     "effort": "M", "depends_on": "S-13",
     "unblocks": "G5 drawdown control becoming real rather than decorative.",
     "risk_if_skipped": "A genuine edge is ruined by a single correlated Sunday where every leg loses "
                        "for the same reason.",
     "priority": 2},
    {"id": "S-18", "title": "Publish a weekly one-page 'what changed' diff on the site itself",
     "problem": "This site is the review surface; a reviewer should be able to decide in five minutes "
                 "whether to act. Today that requires reading 345 rows of injury data.",
     "proposal": "Auto-generate a weekly diff: new Out/Doubtful rows, lines whose projection moved more "
                  "than a point, gates that changed state, flags that closed.",
     "effort": "S", "depends_on": "two consecutive snapshots",
     "unblocks": "a reviewable decision process, and turns the site into the audit log rather than a "
                 "display case.",
     "risk_if_skipped": "Nobody reads it, so the review step quietly disappears and the system ships "
                        "decisions with no human in the loop.",
     "priority": 3},
]

# --------------------------------------------------------------------------------------
# OPEN QUESTIONS — the register the brief asks for: what we have, what we lack, and what
# a sufficient answer looks like.
# --------------------------------------------------------------------------------------
QUESTIONS: list[dict] = [
    {"id": "Q-01", "group": "Market & prices",
     "question": "Which provider is the source of truth for a line, and which price counts as the close?",
     "we_know": "nfl.com publishes no odds of any kind; the only lines reachable this session were "
                "third-party pages quoting a single sportsbook.",
     "missing": "a licence, a definition of 'close' (5:00 PM ET Friday? 90 minutes before kickoff? "
                "per-market?), and a decision on whether prop closes are recorded at all.",
     "answer_looks_like": "A named provider, a written close definition, and one recorded price per "
                          "market per game for the whole season.",
     "blocks": "edge, CLV, G2, G3, G9, and any reward above tier 3."},
    {"id": "Q-02", "group": "Market & prices",
     "question": "Do we originate against a vig-free fair number, or against a specific book's price?",
     "we_know": "The model publishes fair prices with no vig (american_from_prob), which is a "
                "reference, not a quote.",
     "missing": "the book or exchange to be beaten, and its typical hold.",
     "answer_looks_like": "A named benchmark market plus its hold, recorded per bet.",
     "blocks": "whether an edge of 2% is even reachable after vig."},
    {"id": "Q-03", "group": "Market & prices",
     "question": "Which markets are actually in scope: side, total, team totals, first half, live?",
     "we_know": "Week 10 offers 14 games; each market family has a different efficiency level.",
     "missing": "a scope decision plus the realisation that live betting needs a feed this project "
                "does not have.",
     "answer_looks_like": "A short list of market families with an explicit 'not yet' for the rest.",
     "blocks": "the whole data model — prop-shaped rows cannot be added retroactively."},
    {"id": "Q-04", "group": "Market & prices",
     "question": "How do we treat a market that moves between our snapshot and kickoff?",
     "we_know": "Nothing here records movement at all today.",
     "missing": "a policy: signal on last-known price, or require the price to still be available?",
     "answer_looks_like": "A rule expressed in seconds between signal and close, plus a re-quote step.",
     "blocks": "realised edge versus theoretical edge, and every 'we would have got it' argument."},
    {"id": "Q-05", "group": "Market & prices",
     "question": "Is a stale line worse than no line?",
     "we_know": "The Week 10 Thursday game already had a final score printed while its pregame "
                "designations were still on the report page.",
     "missing": "a timestamp discipline: which inputs are legal for which kickoff.",
     "answer_looks_like": "Every input row carrying the kickoff it precedes, enforced in code (S-05).",
     "blocks": "all accuracy claims and gate G10."},
    {"id": "Q-06", "group": "Market & prices",
     "question": "What is the minimum number of books whose price we need to trust our own?",
     "we_know": "One sportsbook's number is an anecdote; a consensus close across several is data.",
     "missing": "a decision on single-source vs aggregated close.",
     "answer_looks_like": "'Close = median of the no-vig probability across N>=3 books', implemented.",
     "blocks": "whether G3 is measuring skill or one trader's mood."},
    {"id": "Q-07", "group": "Availability & roster",
     "question": "Who starts when a starter is out — and can we say so from a source, not from a guess?",
     "we_know": "The report prints a status and nothing else. Only 4 of the 163 absence-weighted rows are backed by an official named "
                "replacement, at four clubs: Cleveland (Watson to start), Arizona (Beck to start), Seattle (Lock "
                "in place of the ruled-out Darnold) and Miami (McCord 'in line for' a first start).",
     "missing": "a depth source. The official depth-chart URL 404s and the third-party structured "
                "endpoint returns an empty body.",
     "answer_looks_like": "An effective-starter table per club per week, each cell traceable to "
                          "participation data or a named official report.",
     "blocks": "every '2nd/3rd/4th string' claim in the brief, and moving availability from shadow to "
               "applied."},
    {"id": "Q-08", "group": "Availability & roster",
     "question": "How big is the drop from starter to replacement, in points, per position?",
     "we_know": "The model uses declared priors (QB 3.5 pts, edge 1.5, interior line 0.8 …) all marked "
                "uncalibrated.",
     "missing": "a regression of realised points on officially-confirmed starter absences.",
     "answer_looks_like": "Per-position coefficients with confidence intervals, refit annually.",
     "blocks": "whether the availability adjustment adds value or noise."},
    {"id": "Q-09", "group": "Availability & roster",
     "question": "How much should a Questionable or Doubtful tag move a line?",
     "we_know": "The model uses priors of 30% and 60% absence probability; the report itself gives no "
                "probabilities. This week has 84 Questionable rows and 10 Doubtful rows across the 28 "
                "clubs.",
     "missing": "realised rates: how often a Doubtful player in fact did not play, split by the day the "
                "designation was set.",
     "answer_looks_like": "A table of P(absent | status, day, club) from official inactive lists.",
     "blocks": "the difference between a useful game-day update and a coin flip."},
    {"id": "Q-10", "group": "Availability & roster",
     "question": "Does a player listed as Out ever play?",
     "we_know": "The official vocabulary treats Out as a designation, not a guarantee; and rows with no "
                "designation at all (63 of 345 this week) are explicitly not 'available'.",
     "missing": "the ground truth: the official inactive list, published shortly before kickoff.",
     "answer_looks_like": "A count of mismatches between designation and inactives, over a season.",
     "blocks": "how much weight any designation can carry."},
    {"id": "Q-11", "group": "Availability & roster",
     "question": "Do we trust the club heading on the report, or the transaction ledger?",
     "we_know": "They disagreed this week: the league reported on Nov 10 that a Chargers linebacker had "
                "been traded to Denver, and the Week 10 report still lists him under the Chargers.",
     "missing": "a rule for which source wins, and a lag allowance for paperwork.",
     "answer_looks_like": "'transactions win; the report is joined by player id, and a row is dropped "
                          "if its club contradicts a transaction inside 48h'.",
     "blocks": "attributing availability to the right defence or offence."},
    {"id": "Q-12", "group": "Availability & roster",
     "question": "Which absences are already in the line by the time we see them?",
     "we_know": "Not measurable here — needs price history.",
     "missing": "the timing of each designation versus each market move.",
     "answer_looks_like": "A per-market estimate of 'information already absorbed', in points.",
     "blocks": "whether an injury signal is a signal at all rather than a news-delay artefact."},
    {"id": "Q-13", "group": "Availability & roster",
     "question": "How should multiple absences in one unit combine — additively or worse than additively?",
     "we_know": "This week Minnesota lists a quarterback, a tight end, a wide receiver, a defensive tackle and a linebacker as Out; "
                "Green Bay lists its lead running back, its premier pass rusher, a centre and a tight end as Out, "
                "plus a starting linebacker Doubtful. The "
                "model charges the first absence at full weight and each further one at 25% — a prior.",
     "missing": "an empirical stacking curve, per unit.",
     "answer_looks_like": "A curve fitted on 2+ seasons of 'n starters out at a unit' versus realised "
                          "points.",
     "blocks": "the difference between a plausible rating and a rating that blows up on bad teams."},
    {"id": "Q-14", "group": "Availability & roster",
     "question": "Is the reporting itself informative, separate from the injury?",
     "we_know": "Several rows print a practice status with no injury at all (e.g. a fully participating "
                "quarterback with a blank injury field), which suggests clubs report players for reasons "
                "other than an injury.",
     "missing": "a classification of 'reported for load management' versus 'reported for injury'.",
     "answer_looks_like": "A flag on each row distinguishing rest from injury, sourced from the injury "
                          "text or the news item.",
     "blocks": "cleaning a signal that currently mixes two different behaviours."},
    {"id": "Q-15", "group": "Data plumbing & definitions",
     "question": "Which endpoint replaces the rendered stat table, and does it expose a definition per field?",
     "we_know": "On the rendered pages, total offensive yards does not equal rushing + passing for any "
                "of the 7 clubs read (gaps of 48 to 151 yards, tracking each club's own sacks figure), "
                "and 'SACKS' is not labelled as taken or recorded.",
     "missing": "a documented field list.",
     "answer_looks_like": "A schema with one canonical name per field and a written definition.",
     "blocks": "every per-play efficiency feature."},
    {"id": "Q-16", "group": "Data plumbing & definitions",
     "question": "What denominator do 'per game' rates use while a week is in progress?",
     "we_know": "Club games summed to 274 (137 games) and the official standings' PF/PA are internally "
                "consistent at that, while a third-party weekly count implied 136 games.",
     "missing": "a rule (games completed before the snapshot, not 'week number').",
     "answer_looks_like": "games_played = count of completed official box scores before the snapshot time.",
     "blocks": "any rate that changes mid-week, and league-average baselines."},
    {"id": "Q-17", "group": "Data plumbing & definitions",
     "question": "How do we handle a club whose official pages contradict each other?",
     "we_know": "One league page gives a quarterback a 6-9 week absence, another a 6-10 week absence, "
                "and a third covers a different injury to the same player.",
     "missing": "a precedence rule: transaction ledger > team-confirmed > league roundup > report.",
     "answer_looks_like": "A written precedence order plus a 'contested' state that publishes both.",
     "blocks": "silently averaging two official numbers, which is fabrication with extra steps."},
    {"id": "Q-18", "group": "Data plumbing & definitions",
     "question": "Where does the raw snapshot live once it stops fitting in a CSV?",
     "we_know": "345 rows transcribe fine by hand; 32 clubs × 20 weeks × several pages does not.",
     "missing": "a storage decision (git-ignored parquet vs an object store) and a retention policy.",
     "answer_looks_like": "A documented layer: raw immutable snapshots, derived verified JSON, published "
                          "site data.",
     "blocks": "the point where the repo becomes too big to review — and review is the whole method."},
    {"id": "Q-19", "group": "Data plumbing & definitions",
     "question": "How is a value marked unverified, and does the site ever accidentally render it as fact?",
     "we_know": "The convention exists (blank cell + flag) and the builder can enforce it, but only for "
                "pages it generates.",
     "missing": "an editor-proof rule, not just a generator rule.",
     "answer_looks_like": "A build failure on any numeric cell whose row lacks a source link — already "
                          "started in build_site --check.",
     "blocks": "the credibility of every table on the site."},
    {"id": "Q-20", "group": "Data plumbing & definitions",
     "question": "Which sources may be cached, and for how long, before a decision is made on stale data?",
     "we_know": "Two sources this session were hours old in a week where a roster move and three "
                "quarterback changes happened inside 72 hours.",
     "missing": "a TTL per dataset, plus an 'expired' visual state.",
     "answer_looks_like": "Injuries 4h, odds 15m, standings 24h, weather 1h — each displayed on the page.",
     "blocks": "quietly betting on last week's roster."},
    {"id": "Q-21", "group": "Data plumbing & definitions",
     "question": "Can the whole site be rebuilt from scratch by one command, with no network?",
     "we_know": "Yes today: fetch → ingest → validate → model → build, all standard library, with the "
                "verified JSON committed so the site renders offline.",
     "missing": "a CI job that runs it on every push so it stays true.",
     "answer_looks_like": "A GitHub Action failing the PR when validate or --check fails.",
     "blocks": "the guarantee that 'published' and 'verified' still mean the same thing next month."},
    {"id": "Q-22", "group": "Model & validation",
     "question": "Is an additive points model the right shape at all, versus a win-probability model?",
     "we_know": "v0 is additive, which produces a spread and a total naturally but cannot respect "
                "scoring asymmetry (a 14-point lead changes behaviour).",
     "missing": "a comparison of both on the same history — which needs Q-01.",
     "answer_looks_like": "Two models, one backtest, log-loss and CLV compared.",
     "blocks": "the model's core architecture choice."},
    {"id": "Q-23", "group": "Model & validation",
     "question": "How do we know the injury adjustment helps, rather than just changes the answer?",
     "we_know": "On the verified 32-club data, absences are essentially uncorrelated with net points "
                "(rho = +0.06), which is good news: it means the adjustment adds information rather "
                "than duplicating the PPG term.",
     "missing": "the out-of-sample proof on realised games, and the same test on the shadow ledger.",
     "answer_looks_like": "CLV with the adjustment minus CLV without it, over >=300 bets.",
     "blocks": "whether availability stays in the model."},
    {"id": "Q-24", "group": "Model & validation",
     "question": "Which prior is load-bearing, and by how much?",
     "we_know": "The stability sweep says: a 20% change in shrink_to_mean moves spreads up to 3.0 "
                "points, and G8 fails as a result.",
     "missing": "fitted values, and a re-run of the same sweep expecting PASS.",
     "answer_looks_like": "Max shift <= 0.5 pts under the same sweep.",
     "blocks": "any staking decision built on today's lines."},
    {"id": "Q-25", "group": "Model & validation",
     "question": "What is our edge threshold before a bet is placed, and who sets it?",
     "we_know": "G2 currently demands 2.0% mean post-vig edge and 55% of bets with positive edge — a "
                "convention chosen for this repo, not a fitted value.",
     "missing": "a threshold calibrated on realised CLV distributions, plus a lower bound for high-"
                "capacity markets.",
     "answer_looks_like": "A threshold per market family with a written justification.",
     "blocks": "bet frequency, and therefore how fast the ledger can ever reach sample."},
    {"id": "Q-26", "group": "Model & validation",
     "question": "How do we remove luck without removing the sample that proves we are not lucky?",
     "we_know": "The board is CLV-weighted, uses a week-block bootstrap, and reports realised minus "
                "closing-implied units as 'luck' explicitly.",
     "missing": "an agreed stopping rule — nobody can keep betting until the CI clears zero, so the "
                "rule has to be prospective.",
     "answer_looks_like": "'minimum N bets before a tier promotion; no tier demotion before M bets', "
                          "with N and M set in advance.",
     "blocks": "the reward system's legitimacy."},
    {"id": "Q-27", "group": "Model & validation",
     "question": "Which gate is allowed to be waived, and by whom?",
     "we_know": "Today nothing is waivable, which is why every strategy sits at tier 3.",
     "missing": "an explicit waiver policy (probably: G0 and G10 never).",
     "answer_looks_like": "A two-line policy in COORDINATION.md.",
     "blocks": "the first real bet."},
    {"id": "Q-28", "group": "Model & validation",
     "question": "What is the null hypothesis for 'skill' here?",
     "we_know": "Implicitly: beating the closing line is not chance. That is testable, but only with prices.",
     "missing": "a written statistical definition of skill, plus the multiple-comparison correction for "
                "running many strategies on one ledger.",
     "answer_looks_like": "'p(clv<=0) < 0.05 after a Benjamini-Hochberg correction across all submitted "
                          "strategies'.",
     "blocks": "whether 20 strategies testing one noise signal can ever be separated from the winner."},
    {"id": "Q-29", "group": "Risk & operations",
     "question": "What bankroll, what stake rule, and what is the walk-away line?",
     "we_know": "Tier 1 allows 2.0% of roll per bet; G5 caps drawdown at 25%; half-Kelly is the sizing "
                "default in the ledger code.",
     "missing": "a declared roll and a losing-streak rule (e.g. pause at -20%).",
     "answer_looks_like": "Three numbers, written down before the first bet.",
     "blocks": "whether a bad month becomes a bad decision."},
    {"id": "Q-30", "group": "Risk & operations",
     "question": "How correlated is the slate, and what is the maximum correlated exposure?",
     "we_know": "Under the static model, margin and total in the same game are exactly uncorrelated "
                "(rho = 0) and a side plus that team's team-total is rho = 0.707; measured across the "
                "32 clubs, offence quality and defence quality correlate at -0.20.",
     "missing": "the game-flow term (a trailing team passes more), which requires play-by-play.",
     "answer_looks_like": "A per-slate exposure cap computed from the joint covariance matrix.",
     "blocks": "safe parlays and safe 11-leg Sundays."},
    {"id": "Q-31", "group": "Risk & operations",
     "question": "What is the legal and account-level constraint set, and where is the record of it?",
     "we_know": "Nothing in this repo touches jurisdiction, eligibility or account limits.",
     "missing": "a stated constraint list per venue of operation.",
     "answer_looks_like": "A short compliance file that the do-not-bet filter (S-12) consults.",
     "blocks": "operating at all, and it is not a technical problem."},
    {"id": "Q-32", "group": "Risk & operations",
     "question": "Who reviews the weekly output, and on what evidence?",
     "we_know": "This site is the review surface; the flag system is the escalation path; a flag blocks "
                "a decision but never blocks publication.",
     "missing": "a standing 20-minute review ritual with a written decision per signal.",
     "answer_looks_like": "A weekly checklist that produces a recorded decision, accept or reject.",
     "blocks": "the difference between a decision-support system and an autoplay button."},
    {"id": "Q-33", "group": "Risk & operations",
     "question": "What is the reward for a top strategy, and what stops gaming it?",
     "we_know": "Tiers 1-4 are defined with allocations, data priority and named slots; the score is "
                "CLV-weighted, and the tier depends on gates only — realised PnL cannot buy a tier.",
     "missing": "a rule against sandbagging (deliberately small stakes to farm a tier) and against "
                "bet-type arbitrage of the score (see S-16).",
     "answer_looks_like": "Minimum stake as a fraction of the market's table, and ranking only within a "
                          "market family.",
     "blocks": "the leaderboard becoming a contest to look good rather than to be right."},
    {"id": "Q-34", "group": "Risk & operations",
     "question": "What happens to the system when it stops working?",
     "we_know": "Nothing today watches for decay; a strategy can be flat for 300 bets and still sit on "
                "the board unchanged.",
     "missing": "a demotion rule and a kill switch based on CLV going negative.",
     "answer_looks_like": "'mean CLV < 0 over a rolling 100 bets -> tier 4, re-derive the thesis'.",
     "blocks": "long-term survival; models die quietly far more often than loudly."},
]

DECISION_RULE = (
    "A flag never blocks publication. It blocks a decision. A cell with no official source stays "
    "blank, and a blank cell is an answer: it says 'this is not knowable from what we hold' — which "
    "is the difference between a dashboard and a story."
)

TIER_NOTES = (
    "Today's verdict on this repo's own gates: one PASS (G0, data integrity — 13 checks clean) and "
    "nine HOLD. Nothing here is fundable yet, and the site says so in those words rather than "
    "showing a table of confident-looking numbers."
)
