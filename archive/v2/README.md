# archive/v2 — preserved from session `arena/a7c0f9c5-fl1`

These files are **not part of the published site**. They are kept verbatim so no work from the third
parallel session is lost when the repo-root paths were consolidated.

- Origin: PR #2, branch `arena/a7c0f9c5-fl1`, merged into `main` as commit `42b06f5` on 2026-11-14.
- Preserved: `depth-charts.html`, `leaderboard.html`, `style.css`, `main.js`, and the five CSVs under `data/`.

## What was valuable here

This session independently transcribed the **same** official Week 10 injury report. That made a genuine
cross-check possible, which is recorded as flag **F15** and as a row in `data/verification.tsv`:

| | Result |
|---|---|
| Rows in their `data/injuries.csv` | 161 |
| Rows also present in this repo's 345-row capture | 161 (none only in theirs) |
| Rows matching field-for-field | **156 of 161** |
| Rows differing | 5 — all players with two listed body parts |

**Why the 5 differ.** Their CSV was comma-delimited with the injury field unquoted, so a value like
`Ankle, Knee` split across columns and pushed practice status and game status one field to the right.
Example: A.J. Brown should read `Ankle, Knee / Limited Participation / Questionable`; their row shows
`Ankle / Limited Participation In Practice / Knee`. The raw page capture in
`raw/injuries-week10-2026.md` confirms the correct value.

So the agreement on 156 rows is independent confirmation of the capture, and the 5 disagreements are a
formatting bug rather than a data dispute.

## Why the repo-root pages are not these files

GitHub Pages serves one root and one `index.html`. This site's build is a superset: 345 verified rows
over 28 clubs (vs 161 over 14), plus the source registry, validation gates, open-questions register,
suggestions register and verification log.

## Mapping from v2 to the live site

| v2 file | Live equivalent |
|---|---|
| `depth-charts.html` | `/depth.html` |
| `leaderboard.html` | `/strategies.html` |
| `data/injuries.csv` | `data/injuries.tsv` (345 rows, comma-safe) |
| `data/standings.csv` | `data/standings.tsv` |
| `data/strategies.csv` | `data/strategies.json` |
| `data/correlations.csv` | `/validation.html` (correlation method, values left blank where unscoreable) |
| `data/rosters.csv` | `data/depth-kc.tsv` + `sources.tsv` S07 |
| `style.css`, `main.js` | `assets/css/site.css`, `assets/js/site.js` |

## Note on `data/correlations.csv`

It carried numeric correlation estimates (e.g. `0.55 - 0.75` for "same-team QB passing yards + WR1
receiving yards") with its own column reading **"Unverified — not from an official source"** and
"Analytical estimate". They are preserved here as that session left them, but they are **not** published
on the live site: this site's rule is that a correlation value is computed from joint observations or
left blank. See `/validation.html` and flag F08.

## If you want a v2 page restored

Open a PR, restore that file plus its navigation entry, and confirm `tools/checklinks.py` still passes.
Do not delete this directory.
