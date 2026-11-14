# FL1 — NFL Line Lab

A verified, auditable base for originating NFL lines: official injury data, a decision register,
and a strategy leaderboard that refuses to guess.

**Live site:** https://sassnarep3-star.github.io/FL1/

---

## What this is

The site is a static dashboard. It separates three things that are usually blurred together:

1. **What an official source actually says** — every value links to the live page it came from.
2. **What we do not know yet** — twenty open questions, each with the missing data named.
3. **What we propose to do about it** — fifteen suggestions with options, costs, risks and one
   recommended path, for review before anything is implemented.

Where a number could not be confirmed from an official source, the cell is left **blank** and listed
on the *Flagged for Review* page. Nothing is estimated to fill a gap.

**No line has been originated and no strategy has a result.** That is deliberate: a line needs a
fitted model *and* a benchmark price, and the second does not exist in this repository.

## Pages

| Page | Contents |
|---|---|
| `index.html` | Dashboard and headline figures |
| `executive-summary.html` | One-page brief |
| `requirements.html` | Full requirement decomposition with evidence |
| `injuries.html` | Official Week 10 2026 injury report, 345 rows |
| `depth.html` | Backup depth, observed vs derived, one club worked |
| `standings.html` | Official 2026 standings, schedule, tiebreakers |
| `line-origination.html` | How a line would be produced, and where it stops |
| `strategies.html` | Leaderboard and ranking rule |
| `validation.html` | The eight validation gates and luck controls |
| `questions.html` | Twenty open questions |
| `suggestions.html` | Fifteen suggestions with options and recommendations |
| `sources.html` | Source registry with verification status |
| `flagged.html` | Fourteen flagged items |

## Repository layout

```
index.html … flagged.html     the published site (generated, committed)
assets/css/site.css           one stylesheet, no framework, no CDN
assets/js/site.js             optional filter/highlight helpers
assets/js/data.js             generated data bundle
data/*.tsv                    normalised source data, one row per fact
data/*.json                   registers (questions, suggestions, requirements, strategies, flags)
raw/                          verbatim page captures used for verification
tools/build.py                data -> assets/js/data.js, and all derived arithmetic
tools/site.py                 data -> the HTML pages
tools/checklinks.py           internal link + anchor + reachability check
tools/verify_injuries.py      line-by-line diff of the TSV against the raw capture
docs/                         markdown copies of the executive summary and methodology
COORDINATION.md               shared task board for concurrent sessions
```

## Reproduce and verify

```bash
python3 tools/build.py           # regenerate data bundle + derived counts
python3 tools/site.py            # regenerate all HTML pages
python3 tools/checklinks.py      # fail if any internal link or anchor is broken
python3 tools/verify_injuries.py # diff every injury row against the raw capture
```

`checklinks.py` and `verify_injuries.py` both exit non-zero on failure, so they can gate a merge.
No third-party Python packages are required.

## Why there is no build step

`index.html` and its siblings are committed, fully rendered HTML. GitHub Pages serves the repository
root directly, so there is no pipeline that can fail and no possibility of the live site lagging the
committed data. Re-run the tools when the data changes and commit the output.

## Method notes

- **Blanks are load-bearing.** An em dash means no official source publishes that value. A cell reading
  *not listed* means the player does not appear on the club's injury report at all — also an official fact.
  These are visually distinct on purpose.
- **Provenance is per row.** Every fact carries the ID of the source record it came from.
- **Derived arithmetic is computed, never typed.** Every count on the site comes out of `tools/build.py`.
- **Name joins use an explicit alias table** (`data/depth-aliases.tsv`), never fuzzy matching, because two
  different players named Marcus Harris appear in this dataset (flag F11).

## Limitations

Single season, single snapshot, no price data, no snap counts, no official league-wide depth chart.
See `flagged.html` for all fourteen items, with links.

## Not advice

Nothing here is a bet, an offer to wager, betting advice, or a statement about the legality of any
activity in any jurisdiction. No regulator or tax source was verified.
