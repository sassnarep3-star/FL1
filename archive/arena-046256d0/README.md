# archive/arena-046256d0 — Session `arena/046256d0-fl1` build (preserved)

This folder preserves, **verbatim and unmodified**, the complete site built by session
`arena/046256d0-fl1` on 2026-11-14. It was archived during final integration because the repo root
already carries the consolidated site merged from three earlier sessions (see `COORDINATION.md` for the
full reconciliation record). No work from this session was deleted; no file here was altered.

## What this is

A verification-first NFL decision dashboard for the 2026 season, Week 10 (games Nov 12–16, 2026):

| File | Contents |
|---|---|
| `index.html` | Dashboard landing page with verified findings summary |
| `executive-summary.html` | Executive summary of key details |
| `questions.html` | 12 decision-gate questions with required info, answers, sources |
| `suggestions.html` | 9 site/decision suggestions + 4 information-discovery suggestions (Proposed — Pending Review) |
| `strategies.html` | Single bet / parlay / player-prop framework, validation gates G1–G7, correlation methodology, luck removal, leaderboard rewards |
| `injury-report.html` | Complete official Week 10 injury report (~170 rows, every row linked) + starter-level deficiency watchlist |
| `standings.html` | Verified 32-team standings + computed PPG/PPA |
| `lines.html` | Week 10 slate; line values blank + flagged UNVERIFIED (no official book source reachable) |
| `flagged-review.html` | IR-1 irregularity + UNV-1/UNV-2 unverified items with source links |
| `sources.html` | All official sources used |
| `assets/site.css` | Stylesheet for this build |
| `data/*.md` | Verified source data files and the line-by-line verification log |

## How it maps to the live site

The live site at the repo root covers the same categories with its own (consolidated) pages:

- This `executive-summary.html` ↔ live `executive-summary.html`
- This `questions.html` ↔ live `questions.html`
- This `suggestions.html` ↔ live `suggestions.html`
- This `strategies.html` ↔ live `strategies.html` + `validation.html`
- This `injury-report.html` ↔ live `injuries.html` + `depth.html`
- This `standings.html` ↔ live `standings.html`
- This `lines.html` ↔ live `line-origination.html`
- This `flagged-review.html` ↔ live `flagged.html`
- This `sources.html` ↔ live `sources.html`

## Verification basis

All data verified line-by-line against official NFL.com sources on 2026-11-14 (standings, schedule,
injury report, game center). Values that could not be confirmed from an official source were left blank
and flagged, never inferred. See `data/verification-log.md`.

## Viewing

Open the files directly in a browser, or serve the folder:

```bash
cd archive/arena-046256d0 && python3 -m http.server 8000
```
