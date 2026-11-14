# Method — how every fact on this site is verified

This document exists so the verification is reproducible rather than asserted.

## The one rule

**A value appears on this site only if an official source publishes it, and that source is linked.**

If a value cannot be confirmed, the cell is left blank and the item is listed on *Flagged for Review*
with the source that was attempted. There is no middle state where a value is "probably right".

## Source tiers

| Tier | Meaning | Example |
|---|---|---|
| Official (league) | Published by the NFL | `nfl.com/injuries/`, `nfl.com/standings/` |
| Official (club) | Published by a club, speaks only for that club | `chiefs.com/team/depth-chart` |
| Official (government) | Published by a US federal agency | `weather.gov` |

A club source is never used to make a league-wide claim. A government source is used only for the
thing it actually publishes (weather), never as a proxy for a sports fact.

## Verification protocol

1. **One request per URL.** No batching, no scraping loops, no scheduled crawling.
2. **Read the content that supports the claim.** A source is verified only when the specific value
   appeared in the returned content — not when the domain is reputable.
3. **Record the outcome, including failure.** An HTTP 404 is a finding. Three official addresses
   failed on 2026-11-14 and all three are recorded as `NOT VERIFIED` and never cited as fact.
4. **Capture verbatim.** The injury report was transcribed into `raw/injuries-week10-2026.md` exactly
   as rendered, field by field, in page order.
5. **Diff mechanically.** `tools/verify_injuries.py` parses the raw capture independently, rebuilds the
   table, and compares it to `data/injuries.tsv` row by row and field by field. If a single character
   differs, it exits non-zero.
6. **Recount independently.** The headline figures (rows, clubs, Out/Doubtful/Questionable, DNP,
   non-injury) are recomputed from the raw capture by the verifier, separately from the code path that
   renders them on the site. The two must agree.

## Why blanks are load-bearing

There are three visually distinct states in a data table, and conflating them is the most common way a
dataset becomes untrustworthy:

| Appearance | Meaning |
|---|---|
| `— ` (grey, centred) | No official source publishes a value for this field |
| `not listed` (italic) | The player does not appear on the club's report at all — an official fact |
| A value | Published by the linked source |

An empty injury field on the league's report does **not** mean "no injury". It means the club listed the
player without naming a body part. The site reproduces that distinction instead of smoothing it over.

## Derived values

Anything computed rather than read is produced by `tools/build.py`, never typed. Per-club counts, league
totals, unit splits and depth matches all come out of that one script, so re-running it reproduces every
number on the site exactly.

The one exception is deliberate: unit classification (offense / defense / special teams) is a mapping
table in `tools/build.py`, not a computation, and it is visible there for anyone to disagree with.

## Name matching

`Marcus Harris` appears twice in this dataset — a Tennessee cornerback and a Kansas City defensive
tackle — and NFL player URLs disambiguate them with numeric suffixes. A fuzzy name join would merge two
different people.

Therefore depth-chart names are mapped to report names through an explicit, evidence-bearing alias table
(`data/depth-aliases.tsv`) where each row states why the two spellings are the same person. There is no
fuzzy matching anywhere in the pipeline. Keys in any future join must be player URLs.

## Cross-source contradictions

When two official pages disagree, the site does not pick a winner. Both values are published as captured,
both sources are linked, and the contradiction is listed on *Flagged for Review* with a note that no
resolution was applied. Two such cases exist in this dataset (F04, F05).

The reason is not neutrality for its own sake: choosing silently would be an unlogged inference, and an
unlogged inference is indistinguishable from a guess once it is downstream of a model.

## What verification does not cover

- **Market prices.** The league does not publish betting prices. No feed was licensed or supplied, so no
  price, edge or expected-value figure exists on this site.
- **Snap counts.** No official feed was verified, so no claim is made that a specific backup played.
- **Historical seasons.** Only one season is captured, so nothing here supports a persistence claim.
- **Legal and regulatory position.** No regulator, tax or gaming-commission source was verified, so no
  statement is made about legality in any jurisdiction.

## Reproducing the whole verification

```bash
python3 tools/verify_injuries.py   # every injury row vs the raw capture; non-zero on any difference
python3 tools/build.py             # recompute every derived figure
python3 tools/site.py              # re-render every page
python3 tools/checklinks.py        # every internal link, anchor and reachability; non-zero on failure
```

A reader who runs those four commands has re-done the verification.
