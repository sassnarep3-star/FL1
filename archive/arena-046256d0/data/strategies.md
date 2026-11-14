# Lines-Origination Strategy Framework

Proposed methodology. Treat this as the design baseline for the leaderboard competition. Every strategy
must pass the validation gates before it is eligible for the leaderboard and rewards.

## 1. Objective
Originate NFL lines and generate useful betting signals that are selectively skill-based. Remove luck
from performance evaluation so the leaderboard rewards genuine edge, not variance.

## 2. Strategy classes

### 2.1 Single bet
- One wager per signal (spread, total, or moneyline).
- Signal sources: line movement vs. model, injury-driven availability gaps, situational factors
  (rest, travel, schedule density), and market inefficiency on one side.
- Minimum requirement: each single bet must state the signal, the model estimate, and the market price.

### 2.2 Parlay
- Multiple legs in one ticket. Legs are only combined after correlation checks (Section 5).
- Parlays are scored on the same ROI basis but require the per-leg edge to remain positive after
  correlation adjustment; correlated legs are rejected by the gate.

### 2.3 Player prop combos
- Player props (passing/rushing/receiving yards, TDs) combined into singles or parlays.
- Props require position-specific modeling (snap share, usage, opponent deficiency) and are validated
  with the same gates. Prop lines must be manually verified from an official sportsbook before use
  (currently unverified — UNV-2).

## 3. Validation gates (all must pass)
| Gate | Rule (proposed) | Purpose |
|---|---|---|
| G1 Sample size | Minimum number of independent bets/events before eligibility (proposed: 50+ bets or 1 season of data) | Avoid small-sample noise |
| G2 Edge threshold | Model-implied edge over the market price must exceed a minimum (proposed: 2% expected value) | Filter out no-edge signals |
| G3 Statistical significance | Edge is significant at a set confidence level using a z-score / binomial test on realized vs. expected | Remove luck |
| G4 Correlation check | Bet components within a parlay must be below the correlation limit (proposed: |r| < 0.6 between legs) | Avoid correlated-combo distortion |
| G5 Closing-line value | Strategy must show non-negative closing-line value over the evaluation window | Confirms the edge is real vs. the market |
| G6 Regime check | Strategy is re-tested across regimes (e.g. offense-leaning vs. defense-leaning weeks, home/road splits) | Confirms the signal is not regime-bound |
| G7 Discipline check | No look-ahead, no selective exclusion of results, fixed sizing rules | Prevents curve-fitting and survivorship bias |

A strategy that fails any gate stays in "in validation" and does not appear on the leaderboard.

## 4. Correlation methodology
- Compute pairwise correlation (Pearson; Spearman as a robustness check) between:
  - bet components (legs of a parlay),
  - strategy returns across market factors (e.g. totals vs. spreads),
  - signal inputs (injury score, team efficiency, situational factors).
- Use a rolling window (proposed: last 3 seasons where data permits) to keep correlations current.
- Reject or re-weight any parlay whose legs exceed the correlation limit (G4).
- Publish the correlation matrix per strategy so reviewers can inspect it.

## 5. Removing luck
- Evaluate on expected value and closing-line value, not short-term ROI.
- Require minimum bet count (G1) before any strategy is ranked.
- Use significance testing (G3) so a hot streak alone cannot qualify a strategy.
- Report variance bands alongside ROI; rank by ROI with a z-score tie-breaker.
- Track performance in-sample vs. out-of-sample to penalize overfitting.

## 6. Leaderboard competition design
- All strategies that pass all gates are ranked on the leaderboard.
- Ranking metric: verified ROI over the evaluation window, eligibility gated by G1-G7.
- Tie-breaker: z-score of edge (higher is better).
- Reward tiers (proposed):
  - Tier 1 (top strategy): primary reward.
  - Tier 2 (next tier): secondary reward.
  - Tier 3 (qualified): recognition only.
- Rewards are released only after the evaluation window closes and gates are re-verified.
- Strategies are re-entered each cycle; a strategy that fails a gate is removed until it re-passes.

## 7. Data dependencies (must be closed before live operation)
- Verified live lines (UNV-1) and verified player props (UNV-2) — see Questions page.
- Historical closing lines and results (Q10) for backtesting and closing-line value.
- Bankroll/unit policy (Q8) for sizing and reward normalization.
- Injury data continuity: the official injury report is the weekly baseline (already integrated).

## 8. Execution guardrails
- Fixed unit sizing from the approved bankroll policy.
- No manual overrides of gate results; overrides are logged and reviewed.
- Weekly refresh: re-run gates, update leaderboard, re-publish tables with source links.
