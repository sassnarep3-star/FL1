# archive/v1 — preserved from session `arena/89c32e23-fl1`

These files are **not part of the published site**. They are kept verbatim so that no work from the
parallel session is lost when the repo-root paths were taken over by the verification-first build.

- Origin: PR #1, branch `arena/89c32e23-fl1`, merged into `main` as commit `7c7ae6a` on 2026-11-14.
- Preserved: `index.html`, `executive-summary.html`, `suggestions.html`, `injuries.html`,
  `flagged-review.html`, `nfl-strategies.html`, `css/style.css`, `js/app.js`.
- Unmodified: byte-for-byte identical to what was on `main` before the merge in PR #3.

## Why they were superseded at the repo root

GitHub Pages serves exactly one site root and one `index.html`. Two sites cannot both publish from `/`.
The repo-root pages now carry the build that includes player-level verified data (345 injury rows over
28 clubs), the source registry with verification status, the eight validation gates and the verification
log. That build contains every section the v1 site had.

## Mapping from v1 to the live site

| v1 file | Live equivalent |
|---|---|
| `index.html` | `/index.html` |
| `executive-summary.html` | `/executive-summary.html` (expanded) |
| `suggestions.html` | `/suggestions.html` (15 entries with options and recommendations) |
| `nfl-strategies.html` | `/strategies.html` + `/validation.html` |
| `injuries.html` | `/injuries.html` (345 verified rows) + `/depth.html` |
| `flagged-review.html` | `/flagged.html` (14 items) |
| `css/style.css`, `js/app.js` | `/assets/css/site.css`, `/assets/js/site.js` |

## To view the v1 pages

They are static and self-contained apart from `css/style.css` and `js/app.js`, which sit alongside them
here, so opening `archive/v1/index.html` locally renders the original site with its original styling.

## If you want a v1 page restored at its old path

Open a PR, restore that one file plus the navigation entry, and confirm `tools/checklinks.py` still
passes. Do not delete this directory.
