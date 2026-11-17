# Official NFL Week 11 2026 schedule — capture

**Source:** https://www.nfl.com/schedules/2026/by-week/week-11 (official NFL schedule page)
**Captured:** 2026-11-17 (UTC), session `arena/3f12fa46-fl1`, by the page-fetch tool.
**Page title at capture:** "NFL Week 11 Schedule 2026: Games, Times, Matchups & Tickets"
**Chunks read:** 0, 1, 2 (of 3) — the whole page.

Each game below is transcribed from the official page. The stadium name in the last column is
**not** typed by hand: the official page's own "Hotel" link for the game carries the venue name in
its `destinationAddress.location` parameter, so the name below is the name nfl.com published for
that fixture. The per-game URL is the official Game Centre page, which also publishes the score,
the stadium and the link to the official Game Book PDF.

## Thursday, November 19th

| Game | Time (ET) | Network | Official Game Centre URL | Stadium (official, from the page's own link) |
|---|---|---|---|---|
| Colts at Texans | 8:15 PM | Prime | https://www.nfl.com/games/colts-at-texans-2026-reg-11 | NRG Stadium |

## Sunday, November 22nd — 1:00 PM window

| Game | Time (ET) | Network | Official Game Centre URL | Stadium (official) |
|---|---|---|---|---|
| Dolphins at Bills | 1:00 PM | CBS | https://www.nfl.com/games/dolphins-at-bills-2026-reg-11 | Highmark Stadium |
| Ravens at Panthers | 1:00 PM | FOX | https://www.nfl.com/games/ravens-at-panthers-2026-reg-11 | Bank of America Stadium |
| Saints at Bears | 1:00 PM | FOX | https://www.nfl.com/games/saints-at-bears-2026-reg-11 | Soldier Field |
| Titans at Cowboys | 1:00 PM | CBS | https://www.nfl.com/games/titans-at-cowboys-2026-reg-11 | AT&T Stadium |
| Buccaneers at Lions | 1:00 PM | FOX | https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11 | Ford Field |
| Cardinals at Chiefs | 1:00 PM | CBS | https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11 | GEHA Field at Arrowhead Stadium |
| Steelers at Eagles | 1:00 PM | CBS | https://www.nfl.com/games/steelers-at-eagles-2026-reg-11 | Lincoln Financial Field |

## Sunday, November 22nd — afternoon window

| Game | Time (ET) | Network | Official Game Centre URL | Stadium (official) |
|---|---|---|---|---|
| Jets at Chargers | 4:05 PM | FOX | https://www.nfl.com/games/jets-at-chargers-2026-reg-11 | SoFi Stadium |
| Jaguars at Giants | 4:25 PM | CBS | https://www.nfl.com/games/jaguars-at-giants-2026-reg-11 | MetLife Stadium |
| Raiders at Broncos | 4:25 PM | CBS | https://www.nfl.com/games/raiders-at-broncos-2026-reg-11 | Empower Field at Mile High |

## Sunday Night Football, November 22nd

| Game | Time (ET) | Network | Official Game Centre URL | Stadium (official) |
|---|---|---|---|---|
| Vikings at 49ers | 8:20 PM | NBC | https://www.nfl.com/games/vikings-at-49ers-2026-reg-11 | Mexico City (Mexico City Game — the official page marks this game with the "Mexico City 2026" logo; it is played at Estadio Azteca) |

The official page publishes this game with the Mexico City 2026 mark and a "+1" (one-game
international allocation) for both clubs.

## Monday Night Football, November 23rd

| Game | Time (ET) | Network | Official Game Centre URL | Stadium (official) |
|---|---|---|---|---|
| Bengals at Commanders | 8:15 PM | ESPN | https://www.nfl.com/games/bengals-at-commanders-2026-reg-11 | FedEx Field |

The official page also publishes a game-day weather line for this fixture: `Weather Clearnight`.

## Teams on bye (official page, "Teams on Bye")

| Club | Record printed on the page |
|---|---|
| ATL Atlanta Falcons | 3-7 |
| CLE Cleveland Browns | 6-4 |
| GB Green Bay Packers | 6-4 |
| LA Los Angeles Rams | 6-4 |
| NE New England Patriots | 5-5 |
| SEA Seattle Seahawks | 6-4 |

## Notes on abbreviations

nfl.com prints the Arizona club as `AZ` and the Rams as `LA`; this repository uses `ARI` and `LAR`
in `data/results.tsv` and `ARI`/`LA` in `data/depth.tsv`. The mapping used by the builders is
recorded in `data/schedule_week11.tsv` (`away_abbr` / `home_abbr` are repository abbreviations,
`away_official` / `home_official` are the strings nfl.com printed).
