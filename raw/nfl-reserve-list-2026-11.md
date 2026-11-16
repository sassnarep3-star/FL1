# Official NFL reserve list — November 2026 (verbatim capture)

- **Source (official):** https://www.nfl.com/transactions/league/reserve-list/2026/11
- **Fetched:** 2026-11-16 (page-fetch tool, full page read in two chunks; both chunks returned the same table)
- **Capture session:** `arena-fc0ed6e8-fl1`
- **Why this capture exists:** the brief requires that "not listed" on a weekly injury report never
  means "available" — a player on the reserve list is absent from the weekly report for a roster
  reason, not a health one (the Malik Willis case: he is absent from the Week 10 report because he
  was placed on Reserve/Injured on 11/10, not because he is healthy). This is the first dated
  reserve-list capture in the repository; it is a snapshot of one month and is versioned as such.
- **Structure note:** the page's Position column was blank for every row shown on 2026-11-16;
  blank is recorded verbatim, not inferred. The From and To columns both carried the placing club
  for every row.

## Verbatim table (November 2026, Reserve List)

| From | To | Date | Name | Position | Transaction |
|---|---|---|---|---|---|
| Saints | Saints | 11/14 | Christen Miller | | Reserve/Injured |
| Patriots | Patriots | 11/14 | TreVeyon Henderson | | Reserve/Injured |
| Browns | Browns | 11/14 | Michael Burton | | Reserve/Injured |
| Colts | Colts | 11/14 | Mo Alie-Cox | | Reserve/Injured |
| Colts | Colts | 11/14 | Akeem Davis-Gaither | | Reserve/Injured |
| Titans | Titans | 11/14 | Peter Skoronski | | Reserve/Injured |
| Titans | Titans | 11/14 | Tommy Townsend | | Reserve/Injured |
| Cowboys | Cowboys | 11/14 | Tyler Goodson | | Reserve/Injured |
| Packers | Packers | 11/14 | Josh Whyle | | Reserve/Injured |
| Rams | Rams | 11/12 | Puka Nacua | | Reserve/Injured |
| Rams | Rams | 11/10 | Jordan Whittington | | Reserve/Injured |
| Dolphins | Dolphins | 11/10 | Zach Sieler | | Reserve/Injured |
| Dolphins | Dolphins | 11/10 | Malik Willis | | Reserve/Injured |
| 49ers | 49ers | 11/10 | Gracen Halton | | Reserve/Injured |
| Cardinals | Cardinals | 11/10 | Gardner Minshew | | Reserve/Injured |
| Cardinals | Cardinals | 11/10 | Michael Wilson | | Reserve/Injured |
| Titans | Titans | 11/09 | James Williams | | Reserve/Injured |
| Vikings | Vikings | 11/09 | Demond Claiborne | | Reserve/Injured |
| Bills | Bills | 11/09 | Josh Palmer | | Reserve/Injured |
| Falcons | Falcons | 11/07 | Brian Robinson | | Reserve/Injured |
| Rams | Rams | 11/07 | Jaylen Watson | | Reserve/Injured |
| Broncos | Broncos | 11/07 | Eyioma Uwazurike | | Reserve/Injured |
| Lions | Lions | 11/07 | Jack Campbell | | Reserve/Injured |
| Cowboys | Cowboys | 11/07 | Malachi Lawrence | | Reserve/Injured |
| Commanders | Commanders | 11/07 | Dyami Brown | | Reserve/Injured |

## Verification performed

- The page was fetched live (both chunks) on 2026-11-16 and the table transcribed verbatim.
- The Malik Willis row (Dolphins, 11/10, Reserve/Injured) is the row the brief cites; it is
  reproduced above exactly as published.
- Cross-check: the official Game Center for the same weekend shows Gardner Minshew (Cardinals,
  Reserve/Injured 11/10) — the nfl.com Brissett trade article of 2026-11-06 states Minshew had
  taken over as Cardinals starter and Carson Beck is the reserve, which is consistent with the
  Cardinals' quarterback sequence published there.
- Rows are dated to the day only, as published. No clock time is published by the page; the fetch
  time above is this capture's read time, not a source time.

## Irregularities noted during capture

- The November table contains 25 Reserve/Injured rows for 2026 at capture time. Week 10 games
  were played 11/12–11/15 and several placements (11/14) fall between the Week 10 Wednesday
  injury-report snapshot held in `data/injuries.tsv` and the following week — i.e. the weekly
  report snapshot and this reserve snapshot are **not** from the same moment, and must never be
  merged into one "availability level". The brief's rule (surprise, never level; delta, never
  level) applies.
