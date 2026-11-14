# NFL Lines / Market Snapshot — Verification Status

Rule applied: every value must be confirmed from an official source (the sportsbook itself is the
only authoritative source for odds). Values that cannot be confirmed are left blank and flagged UNVERIFIED.

## Official-source attempts (2026-11-14)
- DraftKings Sportsbook (https://sportsbook.draftkings.com/) — official book. The NFL market page
  redirects to the generic sportsbook landing; odds are rendered client-side and could NOT be
  extracted/verified via fetch. No line values recorded.
- FanDuel Sportsbook (https://sports.fanduel.com/football/nfl) — HTTP 500 on fetch. No line values recorded.

## Result
All Week 10 spread / total / moneyline cells are left blank and flagged UNVERIFIED on the
lines page. NFL.com does not publish betting lines, so no official league source exists for odds.

## Designated verification sources (for manual review)
- DraftKings Sportsbook: https://sportsbook.draftkings.com/ (navigate to NFL → Week 10)
- FanDuel Sportsbook: https://sports.fanduel.com/
- BetMGM Sportsbook: https://sports.betmgm.com/
- Caesars Sportsbook: https://sports.caesars.com/

Note: media outlets (e.g. Bleacher Nation, Fantasy Alarm) publish line references that attribute
numbers to books, but they are not official sources and are not used as verification here.
