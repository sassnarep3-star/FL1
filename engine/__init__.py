"""FL1 engine — line origination support, validation gates and leaderboard scoring.

Design constraints, in order of importance:

1. No number in this package may be a disguised opinion. Every coefficient that
   would have to be *estimated from data we do not yet hold* is either an explicit
   function argument with a documented default, or absent. There are no hidden
   priors in here.
2. Standard library only. The pipeline has to run on a small unattended host and be
   reviewable line by line; a dependency is a liability we would have to audit.
3. Everything that ranks money is a confidence bound, not a point estimate, because
   the brief's central requirement is to remove luck from the equation.

Modules:
    pricing      odds arithmetic, break-even, no-vig probabilities, Kelly, parlay EV
    stats        interval estimation, power analysis, bootstrap, multiple-testing
    correlation  joint simulation and correlation-corrected parlay pricing
    injuries     official injury-report parsing/diffing and the Next-Man-Up index
    compliance   the league's prohibited-wager classes as an executable gate
    gates        G-1..G-13 evaluation of a bet log
    leaderboard  sealed-entry scoring and ranking
"""

__all__ = ["pricing", "stats", "correlation", "injuries", "compliance", "gates", "leaderboard"]
__version__ = "0.1.0"
