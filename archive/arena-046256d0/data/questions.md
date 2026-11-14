# Decision Gate — Questions, Required Information, and Answers

Each decision that must be made before line-origination work can proceed is listed below with the
information required to answer it. Status: **Answered** (confirmed from an official source — link
provided) or **Open** (no official source exists; must be supplied by the operator or obtained first).

## Q1. What is the current league standing?
- Information needed: W-L-T, points for/against for all 32 teams.
- Answer: **Answered.** Full 32-team table published from NFL.com standings (official).
- Source: https://www.nfl.com/standings/league/2026/reg

## Q2. What games are being played this week and when?
- Information needed: Week 10 slate, kickoff times, networks.
- Answer: **Answered.** 16 games, Nov 12-16, 2026, including Munich game (NE at DET) and bye teams.
- Source: https://www.nfl.com/schedules/2026/by-week/week-10

## Q3. Which players are injured / out for Week 10, and who replaces them?
- Information needed: Per-player injury designation, practice status, game status.
- Answer: **Answered.** Complete official Week 10 injury report published (all 16 games).
- Source: https://www.nfl.com/injuries/

## Q4. Are team records current after the Thursday game?
- Information needed: Whether WAS-NYG (FINAL, WAS 24-21) is reflected in standings.
- Answer: **Open — irregularity flagged (IR-1).** NFL.com standings still show WAS 3-5-1 / NYG 5-3-1
  after the completed Thursday game. Published as-is and flagged.
- Sources: https://www.nfl.com/games/commanders-at-giants-2026-reg-10 ; https://www.nfl.com/standings/league/2026/reg

## Q5. What are the current betting lines (spread / total / moneyline)?
- Information needed: Live lines from an official sportsbook for Week 10.
- Answer: **Open — unverified (UNV-1).** NFL.com publishes no lines. Book markets could not be
  verified by automated fetch. Cells left blank and flagged until manually verified.
- Sources to check: https://sportsbook.draftkings.com/ ; https://sports.fanduel.com/ ; https://sports.betmgm.com/ ; https://sports.caesars.com/

## Q6. What are the player prop lines?
- Information needed: Player-specific props (yards, TDs, etc.) from an official sportsbook.
- Answer: **Open — unverified (UNV-2).** No official source reachable in this session.
- Sources to check: official sportsbook player-props markets.

## Q7. Which teams have offense/defense deficiencies from lineup absences?
- Information needed: Starter-level absences on offense and defense per team.
- Answer: **Answered (Week 10).** Injury report cross-referenced with team positional units. Notable
  offense deficiencies: Vikings (QB Kyler Murray out), Seahawks (QB Darnold out), Ravens (QB Lamar
  Jackson 6-10 weeks), Dolphins (QB Malik Willis on IR), Cardinals (QB Carson Beck starting). Notable
  defense deficiencies: Packers (LB Micah Parsons out), 49ers (WR Mike Evans out, offensive), Texans
  (DE Danielle Hunter out, OT Trent Brown questionable), Rams (WR Puka Nacua likely IR).
- Source: https://www.nfl.com/injuries/ plus NFL.com news links on the Injury page.

## Q8. How much bankroll is allocated, and what is the unit sizing policy?
- Information needed: Total bankroll, per-bet unit size, max exposure per game/league.
- Answer: **Open.** No official public source exists; must be defined by the operator.
- Related suggestion: S-01 (define bankroll policy) — see Suggestions page.

## Q9. Is betting on NFL lines legally permitted in the operator's jurisdiction?
- Information needed: Jurisdiction and local licensing/legal status.
- Answer: **Open.** No official source applicable; must be confirmed by the operator.
- Related suggestion: S-02 (confirm legality/licensing before any real-money step).

## Q10. Where will verified historical odds and results data come from?
- Information needed: A source for historical closing lines and results to backtest strategies.
- Answer: **Open.** No official league source for historical betting lines. Candidate sources listed on
  the Suggestions page (S-03) for manual evaluation.
- Related suggestion: S-03 (historical odds data source).

## Q11. What defines a "pass" through the validation gates?
- Information needed: Thresholds for sample size, edge, significance, correlation limits.
- Answer: **Answered (proposed).** Gate specification published on the Strategies page (proposed
  methodology, pending operator approval).
- Source: https://sassnarep3-star.github.io/FL1/strategies.html (this site)

## Q12. How is the leaderboard competition ranked and rewarded?
- Information needed: Ranking metric, eligibility rules, reward tiers.
- Answer: **Answered (proposed).** Ranking by verified ROI with minimum bet-count eligibility, z-score
  tie-breaker, reward tiers — published on the Strategies page (pending operator approval).
- Source: https://sassnarep3-star.github.io/FL1/strategies.html (this site)

## Summary
- Answered from official sources: Q1, Q2, Q3, Q7, Q11 (proposed), Q12 (proposed).
- Open (needs operator input or manual verification): Q4 (irregularity), Q5, Q6, Q8, Q9, Q10.
