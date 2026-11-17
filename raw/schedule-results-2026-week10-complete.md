# RAW CAPTURE — NFL.com official 2026 Week 10 schedule — CLOSE-OUT READ (2026-11-17)
#
# URL: https://www.nfl.com/schedules/2026/by-week/week-10
# Read window (UTC): opened after 2026-11-17T02:45:45Z, completed before 2026-11-17T02:46:39Z
#   (page fetched in 2 content chunks by the session's page-fetch tool; window bracketed by two
#   sandbox clock readings taken immediately before the fetch sequence and immediately after it).
# Page title at capture: "NFL Week 10 Schedule 2026: Games, Times, Matchups & Tickets"
# Status at read: 13 of the 14 Week 10 games printed FINAL with scores. Monday Night Football
#   (LAC at BAL, Nov 16, 8:15 PM ESPN) was LIVE — the card printed "Q2" and a partial score
#   (Chargers 17, Ravens 7). A partial score is not a result: that game is NOT a final row here.
#   The Sunday Night Football game (PIT at CIN), in progress at the 2026-11-16 read, now prints
#   FINAL: Steelers 18, Bengals 38 — this is the one new final since raw/schedule-results-2026-week10-finals.tsv.
# Team keys are the repo's canonical abbreviations; the page prints full team names
#   ("Rams" with logo LA, "Cardinals" with logo AZ -> repo keys LAR, ARI).
#
# Verbatim bullet lines as the page printed them (scripts/build_week10_extension.py asserts each
# of these exact lines is present in this file, parses the scores from them, and cross-checks
# them against the TSV rows below and against data/week10_results_extension.json):
- [Commanders 24, Giants 21, FINAL, Thursday, November 12th](https://www.nfl.com/games/commanders-at-giants-2026-reg-10)
- [Patriots 10, Lions 35, FINAL, Sunday, November 15th](https://www.nfl.com/games/patriots-at-lions-2026-reg-10)
- [Chiefs 35, Falcons 13, FINAL, Sunday, November 15th](https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10)
- [Texans 24, Browns 27, FINAL, Sunday, November 15th](https://www.nfl.com/games/texans-at-browns-2026-reg-10)
- [Vikings 30, Packers 10, FINAL, Sunday, November 15th](https://www.nfl.com/games/vikings-at-packers-2026-reg-10)
- [Dolphins 22, Colts 24, FINAL, Sunday, November 15th](https://www.nfl.com/games/dolphins-at-colts-2026-reg-10)
- [Panthers 20, Saints 17, FINAL, Sunday, November 15th](https://www.nfl.com/games/panthers-at-saints-2026-reg-10)
- [Bills 31, Jets 12, FINAL, Sunday, November 15th](https://www.nfl.com/games/bills-at-jets-2026-reg-10)
- [Jaguars 40, Titans 23, FINAL, Sunday, November 15th](https://www.nfl.com/games/jaguars-at-titans-2026-reg-10)
- [Rams 34, Cardinals 6, FINAL, Sunday, November 15th](https://www.nfl.com/games/rams-at-cardinals-2026-reg-10)
- [Seahawks 21, Raiders 13, FINAL, Sunday, November 15th](https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10)
- [49ers 46, Cowboys 40, FINAL, Sunday, November 15th](https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10)
- [Steelers 18, Bengals 38, FINAL, Sunday, November 15th](https://www.nfl.com/games/steelers-at-bengals-2026-reg-10)
- [Chargers 17, Ravens 7, Q2, ESPN](https://www.nfl.com/games/chargers-at-ravens-2026-reg-10)
#
# Verbatim "Teams on Bye" lines as the page printed them (record under each club):
- CHIChicago Bears
7-27 wins, 2 losses, 0 ties
- DENDenver Broncos
7-27 wins, 2 losses, 0 ties
- PHIPhiladelphia Eagles
2-72 wins, 7 losses, 0 ties
- TBTampa Bay Buccaneers
3-63 wins, 6 losses, 0 ties
#
# TSV rows (only games the official page printed FINAL at this read):
# Format: week<TAB>date<TAB>away<TAB>away_pts<TAB>home<TAB>home_pts[<TAB>note]
10	2026-11-12	WAS	24	NYG	21	Thursday Night Football — already in data/results.tsv (captured 2026-11-14)
10	2026-11-15	NE	10	DET	35	International Game (Munich)
10	2026-11-15	KC	35	ATL	13	
10	2026-11-15	HOU	24	CLE	27	
10	2026-11-15	MIN	30	GB	10	
10	2026-11-15	MIA	22	IND	24	
10	2026-11-15	CAR	20	NO	17	
10	2026-11-15	BUF	31	NYJ	12	
10	2026-11-15	JAX	40	TEN	23	
10	2026-11-15	LAR	34	ARI	6	
10	2026-11-15	SEA	21	LV	13	
10	2026-11-15	SF	46	DAL	40	
10	2026-11-15	PIT	18	CIN	38	Sunday Night Football — NEW final since the 2026-11-16 read
# Not a row (live at read, partial score is not a result): LAC at BAL, Monday Night Football,
#   card printed "Chargers 17, Ravens 7, Q2, ESPN" and status "Live".
