# FL1 — Executive Summary (session `arena/bc60d3ea-fl1`, 2026-11-19)

**Site:** https://sassnarep3-star.github.io/FL1/
**Full audit:** `docs/DECISION-AUDIT-bc60d3ea.md` (this session's line-by-line record)
**Verification:** `scripts/verify_bc60d3ea.py` → `data/verification-bc60d3ea.tsv` (V-J1…V-J6, all PASS)

> This file is a new, session-scoped summary. It does not replace
> `EXECUTIVE_SUMMARY.md`; the integration session folds it in (RQ-J5).

---

## What this session did

Took fresh, clock-bracketed official reads dated 2026-11-19 (Week 11 injury
hub, both standings routes, Week 11 schedule), captured them verbatim to
`raw/`, and verified them with a new script (7 checks, all PASS). Audited
the whole brief line by line against repo evidence and published the
questions/informations/answers table (46 rows) and the suggestions review
table (51 rows). Edited no shared register and no canonical data file —
parallel PR #57 owns those — and logged every cross-scope change as a
request in `COORDINATION.md`.

## What is verified (with official sources)

- **Standings, post-Week-10, both routes agree.** 32 clubs × 17 columns,
  arithmetic exact (W+L+T ∈ {9,10} by bye timing; NET = PF−PA; PCT exact).
  The F72 route-lag did not recur.
- **The 150-row Week 10 closeout corpus is arithmetically complete.** It
  reproduces the fresh standings on W/L/T/PF/PA for 32/32 clubs. The
  frozen 137-row canonical feed is therefore known-stale by exactly the
  13 closeout finals; promotion remains Q44's owner decision.
- **Week 11 injury hub, first read:** 253 rows, 24 clubs. Only the
  Thursday game (IND at HOU) carries game designations (16 rows: 9 Out,
  7 Questionable). CIN/WAS report no injuries; six clubs are on bye.
- **Week 11 schedule:** 13 games, 26 clubs, 6 byes; every printed record
  matches the fresh standings.
- **Registers recomputed:** 46 questions (12 answered / 16 partial / 18
  open, all dated 2026-11-17), 51 suggestions (all with recommendations),
  72 flags, 91 sources (82 VERIFIED), 69 brief-audit rows (D-01…D-69, every
  named artefact exists).

## What is blocked, and the number that clears it

| Blocker | Gate | Number that clears it |
|---|---|---|
| No market price exists in any official source | Q21/Q22/Q30, G-1 | 1 licensed price source with capture timestamps, cadence and redistribution terms |
| No strategy has been run; no strategy clears luck | Q43, G-2 | Lower bound above the vig hurdle after multiplicity adjustment (α/16 = 0.00313); best candidate needs 4,315 bets vs 936 held |
| No official snap-count source | Q05, D-30/D-55 | 1 official snap source covering 32/32 clubs, or club-chart coverage 32/32 (now 30/32) |
| No league-wide official depth chart | Q04, D-51 | 1 verified depth route for all 32 clubs before the backup-deficiency feature |
| Injury designations uncalibrated | Q07, D-43/D-52 | Multi-season join of designations to official inactives: play rates with confidence intervals |
| Promotion policy undecided | Q44 | Owner ratifies the frozen auto-rule (SG51) or keeps dated reads |
| Capture cadence undecided | Q42/Q18 | Owner/counsel acceptable-use clearance, then Wed/Thu/Fri automation (SG50) |
| Legal/terms unanswered | Q14/Q18 | Jurisdiction + real-stakes answer from the owner; no counsel input exists |

## Decisions needed from the owner (in priority order)

1. **Price source (Q21/Q30).** Everything priced — ROI, difference columns,
   vig decomposition, residuals — waits on this. Until then every such cell
   stays blank by policy.
2. **Promotion rule (Q44/SG51).** The closeout corpus is verified complete;
   the only question is whether it rolls into the canonical feed under the
   frozen auto-rule.
3. **Third-party policy (Q23/Q32).** Whether labelled third-party values may
   back headline numbers, or every published value must resolve to an
   official source.
4. **Model admission (Q31) + luck bar (Q43).** Acceptance criteria for a
   fitted fair-line model, and whether the removal-of-luck numbers become
   the leaderboard qualification rule.
5. **Consolidation (Q29/SG47).** One canonical readiness page and one luck
   panel; retire the parallel builders. This session's audit found the
   backlog and readiness registers contradict each other on at least eight
   requirements — consolidation is the fix.
6. **Legal/terms (Q14/Q18).** Jurisdiction, real stakes, acceptable use.
   Nothing published here is legal advice.

## What would change our mind

- A strategy whose 95% lower bound clears the vig-adjusted hurdle after the
  multiplicity adjustment — nothing currently does; the best ROI entry is
  rejected on exactly this.
- An injury-feature ablation whose confidence interval excludes zero — the
  current ablation includes zero on both margin and total, so the features
  stay out of every published model.
- An official snap-count or depth source covering 32/32 clubs — until then
  starter/replacement logic rests on club charts plus dated announced-starter
  evidence only, and inferred replacements stay out of the tables.

## Irregularities flagged for review

- **Stale registers** (readiness counts, backlog statuses, F59/F61/Q44
  texts) — logged as RQ-J1…RQ-J5 in `COORDINATION.md`; not edited here
  because PR #57 owns those files.
- **Transcription risk** — the 2026-11-19 captures were transcribed from
  page-reader chunks by hand. Internal-consistency checks all pass, but a
  single mis-typed name would not be caught. Spot-check against the live
  URLs before promoting these captures into any headline register.
- **No new irregularities from the fresh reads themselves.** Both routes
  agree, the corpus reproduces the standings, the injury grammar parses,
  and the schedule records match.

## Not advice

Nothing here is a bet, an offer to wager, betting advice, or a statement
about the legality of any activity in any jurisdiction. No regulator or
tax source was verified.
