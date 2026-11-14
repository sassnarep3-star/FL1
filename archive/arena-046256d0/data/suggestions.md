# Suggestions — For Review Before Implementing Any Change

This section is dedicated to review. Nothing here is implemented automatically. Each suggestion has a
status of **Proposed — Pending Review**. Reviewers should choose the best path per item, then mark it
Approved / Rejected / Amended. Information-discovery suggestions (IDS) close specific gaps identified on
the Questions page.

## A. Site & decision-making improvements

### S-01 — Define the bankroll and unit-sizing policy
- What: Define total bankroll, unit size (e.g. % of bankroll per bet), max exposure per game and per
  slate, and a stop-loss/cool-off rule for drawdowns.
- Why: Without it, no strategy's size can be sized, and the leaderboard cannot normalize results.
- Priority: Critical. Status: Proposed — Pending Review.

### S-02 — Confirm legality and licensing before any real-money step
- What: Confirm jurisdiction rules, sportsbook licensing, and any compliance constraints before
  funding an account or placing bets.
- Why: Legal/compliance gating item (Question Q9).
- Priority: Critical. Status: Proposed — Pending Review.

### S-03 — Source verified historical closing lines and results
- What: Secure a data source for historical closing lines, results, and settlement data (official sportsbook
  APIs where available, or licensed third-party historical providers). Verify each candidate's data lineage
  before trusting it.
- Why: Required to backtest strategies and compute closing-line value (Question Q10). No official league
  source exists for historical betting lines.
- Priority: Critical. Status: Proposed — Pending Review.

### S-04 — Add a live "lines snapshot" with timestamps
- What: After manual verification on a sportsbook, record spread/total/moneyline per game with an exact
  timestamp and the book name in every row, so values are auditable and comparable week to week.
- Why: Fixes UNV-1 and makes every line decision auditable.
- Priority: High. Status: Proposed — Pending Review.

### S-05 — Add a strategy leaderboard page with eligibility rules
- What: Publish a leaderboard ranking strategies by verified ROI, with minimum bet-count eligibility,
  z-score tie-breakers, and reward tiers (see Strategies page for the proposed design).
- Why: The user wants a leaderboard competition with rewards for top-performing strategies.
- Priority: High. Status: Proposed — Pending Review.

### S-06 — Add automated injury-to-impact scoring
- What: Convert the injury report into a per-team availability score (e.g. starters out/questionable by
  position unit) and surface the biggest Week 10 deficiencies automatically.
- Why: Injuries are the core signal source for line origination; scoring makes the signal comparable.
- Priority: High. Status: Proposed — Pending Review.

### S-07 — Add correlation heatmap output
- What: Render the correlation matrix of strategy legs as a visual heatmap on the strategies page so
  correlated combos are obvious before validation.
- Why: Supports the "determine correlation values" requirement visually.
- Priority: Medium. Status: Proposed — Pending Review.

### S-08 — Add a review workflow for flagged items
- What: Add status controls (Open / Resolved / Accepted-as-published) to items on the Flagged for Review
  page, with a note field for each resolution.
- Why: Makes the review loop explicit; irregularities and unverified items currently are static.
- Priority: Medium. Status: Proposed — Pending Review.

### S-09 — Add a weekly refresh schedule
- What: Schedule a repeatable weekly process: refresh standings, schedule, injury report, and verified
  lines; re-run validation gates; update the leaderboard.
- Why: Data is weekly by nature; the site should stay current without manual rework.
- Priority: Medium. Status: Proposed — Pending Review.

## B. Information-discovery suggestions (to find the missing information)

### IDS-1 — Manually verify current Week 10 lines on an official sportsbook
- What: Open DraftKings / FanDuel / BetMGM / Caesars, capture spread, total, and moneyline for all 16
  Week 10 games with timestamps, then fill the blank cells on the Lines page and un-flag UNV-1.
- Closes: Q5 / UNV-1. Status: Proposed — Pending Review.

### IDS-2 — Manually verify player prop lines
- What: Capture player props (passing yards, rushing yards, receiving yards, TDs) for key Week 10 players
  from an official sportsbook.
- Closes: Q6 / UNV-2. Status: Proposed — Pending Review.

### IDS-3 — Confirm the standings freshness question (IR-1)
- What: Check the official NFL.com standings after the Thursday game settles and confirm whether WAS/NYG
  records update to include the 24-21 result.
- Closes: Q4. Status: Proposed — Pending Review.

### IDS-4 — Evaluate historical-data vendors
- What: Request sample data and lineage documentation from candidate historical odds providers; verify a
  sample of closing lines against official books before committing.
- Closes: Q10. Status: Proposed — Pending Review.
