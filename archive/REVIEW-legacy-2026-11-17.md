> **Historical snapshot — archived 2026-11-17.** Preserved from the pre-audit document. Its counts, status statements, source claims and workflow descriptions may be stale or contradicted by later dated captures. Do not use it as current guidance; see the root-level README.md, REVIEW.md and EXECUTIVE_SUMMARY.md.

---

# REVIEW — what to look at first

A short reading guide. The live site is https://sassnarep3-star.github.io/FL1/

---

## If you read one page

**[Executive Summary](executive-summary.html)** — what is verified, what is blocked, and the five
decisions that unblock the rest.

---

## If you have five minutes

1. **[Flagged for Review](flagged.html)** — the 15 items where something could not be confirmed or two
   official sources disagree. Nothing here is resolved silently; each item has its source link.
2. **[Open Questions](questions.html)** — 20 questions, 10 of them blocking. Each states what we know,
   what we do not know, what data is missing, and a recommended path.
3. **[Suggestions](suggestions.html)** — 15 proposals, each with options, trade-offs and one
   recommendation. This is the page to approve or reject paths on before anything is implemented.

---

## What to check, and how

| Question you might have | Where to look | How to check it yourself |
|---|---|---|
| Is the injury data real? | [Injuries](injuries.html) | Pick any row, follow `S01` to the source URL, and compare. Then run `python3 tools/verify_injuries.py` — it diffs all 345 rows against the raw capture and exits non-zero on any difference. |
| Why is no line published? | [Line Origination](line-origination.html) | The field-by-field table shows exactly which inputs exist and which are BLOCKED. A price requires a benchmark; the league publishes none. |
| Why is the leaderboard empty? | [Leaderboard](strategies.html) + [Validation Gates](validation.html) | No strategy has been run. The eight gates and the ranking rule are published *before* any result exists so they cannot be fitted to one. |
| Which backups are replacing starters? | [Backup Depth](depth.html) | Read the two halves separately: *observed absence* is official; *derived depth* is from a club chart the club itself calls "Unofficial". |
| What did you refuse to do? | [Flagged for Review](flagged.html) | F01–F03 are three official sources that 404'd. F08/F09 are the missing price feed and snap counts. F12 is the legal question, left open on purpose. |
| How was this verified? | [Verification](verification.html) + [Method](docs/METHOD.md) | Four scripts, all re-runnable, all exit non-zero on failure. |

---

## Things worth disagreeing with

These are judgement calls, not facts. Each is reversible and each is logged.

1. **Blanks over estimates.** Every missing value is left blank. If you would rather see a modelled
   estimate with an explicit error bar, that is a legitimate alternative — but it changes the site from
   a record of sources into a model, and the model then needs its own validation.
2. **Observed vs derived.** The depth layer is deliberately thin because depth is not available
   officially. A richer depth product is possible, but it would be inference wearing a table's clothes.
3. **Non-monetary rewards.** The leaderboard has no prize pool, because the legal question is open and
   no regulator source was verified. If you want prizes, that needs a review first (Q14, SG11).
4. **One season, one snapshot.** Nothing here supports a persistence claim. That is a limit of the
   data, not of the method.
5. **Consolidating one build at the repo root.** Two other sessions published their own sites to the
   same paths. Their work is preserved in `archive/v1/` and `archive/v2/` rather than deleted, and the
   reasoning is in `COORDINATION.md`. If you prefer a different consolidation, the archive makes it
   cheap to reverse.

---

## Where the parallel-session work went

| Session | Where it lives now |
|---|---|
| `arena/89c32e23-fl1` (PR #1) | `archive/v1/` — 6 HTML pages, stylesheet, script, with a mapping table |
| `arena/a7c0f9c5-fl1` (PR #2) | `archive/v2/` — 2 HTML pages, 5 CSVs, stylesheet, script, with a mapping table |
| `arena/ab4e9b05-fl1` (PRs #3, #5) | the published site at the repo root |

Session C's independent injury transcription of 161 rows was used as a genuine cross-check: 156 rows
matched this capture exactly. The 5 that differed were traced to a comma-splitting bug in their CSV, not
a disagreement about the data. Recorded as flag **F15**.

---

## Reproducing every check

```bash
python3 tools/verify_injuries.py   # 345 rows vs the raw page capture
python3 tools/build.py             # recompute every derived figure
python3 tools/site.py              # re-render all 14 pages
python3 tools/checklinks.py        # links, anchors, reachability, source IDs, escaped markup
```

No third-party packages. No network access needed.
