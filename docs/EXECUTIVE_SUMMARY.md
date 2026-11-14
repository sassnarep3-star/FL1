# FL1 — Executive Summary

**As of:** 2026-11-14 (UTC)
**Live site:** https://sassnarep3-star.github.io/FL1/
**Scope:** verified data collection, open-questions register, suggestions register, line-origination
specification, strategy leaderboard specification and validation gates.

---

## 1. Bottom line

The repository began as a five-byte README. It now holds a verified data base, a decision register and a
published dashboard. Three things are true and should be stated plainly at the top:

1. **The injury data is real, complete for what it covers, and independently re-verifiable.**
   345 player rows over 28 clubs, each with practice status and game status, transcribed from the
   official Week 10 2026 report and diffed line by line against the raw capture (`tools/verify_injuries.py`).
2. **No line has been originated and no strategy has a result.** Not because the work stopped, but
   because a line requires a fitted model *and* a benchmark price, and only the first of those is
   possible in this repository. Publishing a number without a model would be an invention.
3. **The binding constraint is data, not method.** Ten of the twenty open questions are marked blocking,
   and the blocking ones concern inputs that do not exist here: a price feed, snap counts, an official
   league-wide depth chart, historical seasons. The methodology sections are complete; the inputs are not.

---

## 2. Source verification

| | Count |
|---|---|
| Sources assessed | 15 |
| Loaded and verified | 12 |
| Failed to load (HTTP 404) | 3 |

The three failures matter and are recorded honestly rather than worked around:

- The **2017 Personnel (Injury) Report Policy PDF** — cited by essentially every secondary source —
  returns 404 from `operations.nfl.com`. **No policy text is quoted anywhere on this site**, and the
  official meaning of "Questionable" or "Doubtful" is therefore *not* asserted. Only the categories
  observed on the live report are reproduced.
- **`nfl.com/depth-charts/`** returns 404. There is no league-wide official depth chart.
- The Football Operations injury-report landing page returns 404.

Verified sources: the official injury report, division standings, league standings, week-by-week
schedule, the league calendar, tiebreaking procedures, a club roster, a club depth chart, team
statistics, Next Gen Stats, a player profile, and the National Weather Service.

---

## 3. What the injury data shows

| Metric | Value |
|---|---|
| Player rows captured | 345 |
| Clubs present | 28 of 32 |
| Designated **Out** | 66 |
| Designated **Doubtful** | 10 |
| Designated **Questionable** | 84 |
| Rows with *no* game status | 185 |
| Did not participate in practice | 94 |
| Limited participation | 76 |
| Full participation | 175 |
| Explicitly **not injury related** | 2 |

Of the 66 players designated Out, the split is roughly even between offense and defense, with
defensive line and secondary the most exposed groups. That is the part of the brief about second- and
third-string defenders being forced in.

Two rows are explicitly *not injury related* (one resting player, one personal matter, plus a second
resting player). Counting those as injuries is the most likely way to inflate an injury rate, so they
are tagged rather than bucketed.

**Coverage caveat.** Chicago, Denver, Philadelphia and Tampa Bay are absent from the report. All 28
clubs that do appear also appear on the Week 10 schedule, so the likely explanation is a bye — but no
official bye table was verified, so that is *not* asserted. See flag F06.

**Timing caveat.** One Week 10 game (Commanders 24, Giants 21 on 2026-11-12) was already final at
capture. Those two clubs' rows are that completed game's report and must never be used as a
forward-looking signal. See flag F07.

---

## 4. Backup depth: what can and cannot be said

The brief asks which 2nd, 3rd and 4th string players are replacing starters. That question has two
halves and only one is answerable today.

- **Observable:** which players carry an official game status, and at which depth slot the club lists
  them. One club was worked end to end as a verified demonstration.
- **Not observable:** whether a specific backup actually took the snaps. That needs snap counts. No
  official snap-count source was verified, so the claim is not made.

There is also no league-wide official depth chart, and the club chart used is titled "Unofficial Depth
Chart" by the club itself. So every depth rank on the site is labelled **derived**, never official.

---

## 5. Why the leaderboard is empty

A strategy is only meaningful if three tests separate it from luck, and each needs data this
repository does not have:

| Control | Question | Status |
|---|---|---|
| Calibration | When we say 60%, does it happen 60% of the time? | gates defined, **not run** |
| Closing-line value | Did the market move toward our number? | **blocked** — no price feed |
| Persistence | Does the edge hold out of sample? | gates defined, **not run** |

A season is 18 weeks and Week 10 is in progress. Even a genuinely good model produces results well
inside noise over a few dozen bets. The gates are published *before* any strategy exists precisely so
they cannot be rewritten to fit a result.

The ranking rule is fixed in advance: rank on calibration error, break ties on sample size then model
simplicity, and **never rank on profit**, because over a single season profit is dominated by variance.

Rewards are position and a badge. No money, no entry fee, no wagering, no odds. The legal question is
recorded as open (Q14) rather than answered, because no regulator source was verified.

---

## 6. The five decisions that unblock everything else

| # | Decision | Question | Why it is first |
|---|---|---|---|
| 1 | Name **one market** to price first | Q01 | Pricing everything at once guarantees nothing reaches significance |
| 2 | Supply or accept a **benchmark price source** | Q03 | Without it there is no edge, EV or CLV — only calibration |
| 3 | Accept that **depth is derived, not official** | Q04 | Lets the depth product ship honestly |
| 4 | **Pre-register** the gates and thresholds | Q09, Q12, Q19 | Stops the target moving after the result is known |
| 5 | Keep rewards **non-monetary** | Q13, Q14 | Delivers the competition without the regulatory exposure |

---

## 7. Recommendations

Full reasoning, options and trade-offs are on the **Suggestions** page (15 entries). In priority order:

1. **Publish fair value only, never a fake market price** (SG01) — a blank labelled column costs nothing.
2. **Grade on calibration first, profit second** (SG02) — profit-first ranking surfaces luck in week one.
3. **Hash-seal every prediction before kickoff** (SG03) — nearly free, and it is what makes a record credible.
4. **Split observed absence from derived depth, visibly** (SG04, SG12).
5. **Require every strategy to beat a published naive baseline** (SG08) — otherwise it measures effort, not edge.
6. **Sequence the work**: team single market, then props, then combos, then correlations (SG07).
7. **Publish contradictions rather than resolving them silently** (SG14).
8. **Keep the site static with no build step** (SG10) so the published site cannot drift from the data.

---

## 8. Flagged for review

Fifteen items are published on the **Flagged for Review** page with their source links and nothing
resolved silently. The most consequential:

- **F04 / F05** — two places where official NFL.com pages contradict each other about Rams defenders.
  Both versions are shown verbatim.
- **F08** — no benchmark price source exists, so every price, edge and EV field is blank.
- **F09** — no snap counts, so replacement cannot be measured.
- **F11** — two different players named Marcus Harris. Any name-based join would merge them; joins must
  key on the player URL.
- **F12** — no legal or regulatory source verified; the site makes no legality claim in any jurisdiction.
- **F14** — single season, single snapshot; no persistence claim and no backtest is possible.

---

## 9. What this project deliberately does not do

- It does not quote an injury-policy definition, because the official document 404s.
- It does not claim any club is on a bye, because no official bye table was verified.
- It does not resolve cross-source contradictions by choosing a side.
- It does not print a single performance figure.
- It does not present a derived depth rank as official.
- It does not fill a blank to make a table look complete.

Each of those omissions is a deliberate choice, listed with links, so it can be reversed once the
missing source exists.
