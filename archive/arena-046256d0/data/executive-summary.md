# Executive Summary

**Project:** FL1 — NFL line origination, signal research, and decision-support site.
**Date:** 2026-11-14. **Current week:** NFL Week 10, 2026 season (games Nov 12-16, 2026).

## 1. What this site is
A verification-first decision-support dashboard for originating NFL lines and evaluating betting strategies.
Every published data row carries a link to an official source. Values that could not be confirmed from an
official source are left blank and flagged UNVERIFIED on the Flagged for Review page. No value has been
inferred or filled in.

## 2. Repo review result
The repository was empty at session start (single `README.md` containing "# FL1"). No existing code,
configuration, or data files required review. No irregularities in repo contents.

## 3. Verified data in hand (all from NFL.com, official)
- **Standings (32 teams):** Buffalo and San Francisco lead at 7-1 (.875). Jacksonville's defense allows
  15.1 PPG (121 points in 8 games) — the league's stingiest; Minnesota's offense scores 18.3 PPG (146 in 8)
  despite a 6-2 record. [source: NFL.com standings]
- **Week 10 schedule (16 games):** Full slate with times and networks, including the Munich international
  game (NE at DET) and the completed Thursday game (WAS 24, NYG 21). Bye: CHI, DEN, PHI, TB.
- **Week 10 injury report:** Complete official report for all 16 games. Key availability signals:
  - Vikings QB **Kyler Murray OUT** (hamstring) — Carson Wentz is the active starter.
  - Seahawks QB **Sam Darnold OUT** (ribs/quad) — Drew Lock started/expected to start.
  - Ravens QB **Lamar Jackson out 6-10 weeks** (thumb, IR) — major offense deficiency.
  - Packers RB **Josh Jacobs OUT** (finger, surgery scheduled); 49ers WR **Mike Evans OUT** (Achilles);
    Rams WR **Puka Nacua** DNP / likely IR (turf toe, MCL, PCL per NFL.com news).
  - Texans: WR **Marvin Harrison Jr. OUT**, two starting OTs questionable (Trent Brown, Keylan Rutledge out).
- **Irregularity flagged:** NFL.com standings do not yet reflect the completed Thursday WAS 24-21 NYG
  result (WAS shows 3-5-1, NYG 5-3-1). Flagged for review, not corrected.

## 4. Market status
No betting line value could be verified from an official sportsbook source through automated fetch
(DraftKings market is client-rendered; FanDuel returned HTTP 500). All spread/total/moneyline cells are
blank and flagged UNVERIFIED. This is the single largest information gap blocking line-origination
decisions.

## 5. Strategy framework (proposed, pending review)
A leaderboard-competition system for skills-based strategy selection:
- Strategy classes: **single bet**, **parlay**, **player-prop combos**.
- Every strategy must pass **validation gates** (sample size, edge threshold, significance, correlation
  check, regime check) before graduation.
- **Correlation values** computed between bet components before parlay assembly; correlated legs are
  rejected or flagged.
- **Luck removal:** performance is judged on expected value, closing-line value, and significance
  (z-score), not short-term ROI, with minimum-bet-count eligibility for the leaderboard.
- Reward tiers for top-performing verified strategies.

## 6. Open decisions
12 decision-gate questions are published on the Questions page; 8 are answered from official sources and
4 remain open (bankroll/risk tolerance, jurisdiction/legality, historical odds data source, and the
hand-verified current lines). The Suggestions page lists the actions proposed to close each gap.

## 7. Next steps
1. Review the Flagged for Review page.
2. Decide the bankroll, jurisdiction, and data-source answers on the Questions page.
3. Select which suggestion proposals to implement (Suggestions page).
4. Verify current lines on an official sportsbook, then populate the Lines page and launch the
   leaderboard competition.
