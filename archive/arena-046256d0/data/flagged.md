# Flagged for Review — Irregularities & Unverified Items

Generated: 2026-11-14. Every item below is published for manual review. None of these block the site or the merge.

## IR-1 — Standings do not include the completed Week 10 Thursday game
- Finding: The official NFL.com schedule shows Washington 24, New York 21, FINAL on Thursday Nov 12
  (Week 10). However, the NFL.com standings page (fetched 2026-11-14) still shows Washington 3-5-1 and
  New York 5-3-1, i.e. the result is not reflected in the records. The standings module embedded on the
  official game page (commanders-at-giants-2026-reg-10) shows the same records.
- Impact: Standings table on this site publishes the official values as shown; PPG/PPA computations use
  games played as displayed.
- Sources: https://www.nfl.com/games/commanders-at-giants-2026-reg-10 ; https://www.nfl.com/standings/league/2026/reg
- Status: NEEDS REVIEW.

## UNV-1 — All sportsbook line values (spread / total / moneyline) left blank
- Finding: No official source could be reached to verify Week 10 betting lines. NFL.com does not publish
  lines. DraftKings' NFL market is client-rendered (fetch returns the generic landing page) and FanDuel
  returned HTTP 500 on fetch.
- Impact: All lines cells are blank and marked UNVERIFIED on the Lines page.
- Sources (designated verification pages): https://sportsbook.draftkings.com/ ; https://sports.fanduel.com/ ;
  https://sports.betmgm.com/ ; https://sports.caesars.com/
- Status: NEEDS REVIEW (manual verification on a sportsbook site required before any line-based decision).

## UNV-2 — Player props (player prop lines) not verified
- Finding: Player prop lines are only published by sportsbooks; none could be verified from an official
  source through this session's fetch tools.
- Impact: No prop line values are published; the player-prop strategy framework requires manual verification.
- Status: NEEDS REVIEW.

## NOTE-1 — Injury report week label
- Finding: The NFL.com injury report page is titled "Week 10 of the 2026 Season" and displays the
  Week 10 slate (Nov 12-16). This is consistent with the official Week 10 schedule; no discrepancy found.
- Status: Closed (verified consistent).

## NOTE-2 — Resting-player designations
- Finding: Some listed "Out" players are designated "Not injury related - resting player" (e.g. JAX Jessie
  Bates, JAX Jordan Davis, LAR Myles Garrett). These are planned absences, not injuries, and are labeled
  exactly as the official report states.
- Status: Closed (presented as published).
