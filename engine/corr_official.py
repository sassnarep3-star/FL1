"""Correlations from officially sourced numbers only (requirement R27).

Rule: a correlation published in the official register must be computed from
values whose every input row is traced to an official league source, and every
published value must carry its n. Third-party datasets (nflverse captures,
prop-stat mirrors) may not enter this register at all — `CorrRecord.build`
takes an `official_sources` set and refuses any record whose source ids are not
all inside it. That is the requirement enforced as code, not as a promise.

Statistics are plain and hand-checkable: Pearson r, Fisher-z 95% CI, and n.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence, Set


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    n = len(xs)
    if n != len(ys) or n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r: float, n: int, conf: float = 0.95) -> tuple:
    """Fisher-z confidence interval for Pearson r. z_crit for 95% is 1.96."""
    if r is None or n < 4 or abs(r) >= 1.0:
        return (None, None)
    z_crit = 1.959964 if abs(conf - 0.95) < 1e-9 else None
    if z_crit is None:
        raise ValueError("only conf=0.95 is published")
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = z - z_crit * se, z + z_crit * se
    return (math.tanh(lo), math.tanh(hi))


@dataclass
class CorrRecord:
    corr_id: str
    label: str
    x_label: str
    y_label: str
    method: str = "Pearson r over game/team-level rows; Fisher-z 95% CI"
    n: int = 0
    r: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    source_ids: tuple = field(default_factory=tuple)
    inputs_note: str = ""
    tier: str = "COMPUTED-FROM-OFFICIAL"

    @classmethod
    def build(cls, corr_id, label, x_label, y_label, xs, ys,
              source_ids: Sequence[str], official_sources: Set[str],
              inputs_note: str = "") -> "CorrRecord":
        bad = [s for s in source_ids if s not in official_sources]
        if bad:
            raise ValueError(
                "%s: sources %r are not in the official set; requirement R27 "
                "forbids publishing this correlation in the official register"
                % (corr_id, bad))
        n = len(xs)
        r = pearson(xs, ys)
        lo, hi = fisher_ci(r, n) if r is not None else (None, None)
        return cls(corr_id=corr_id, label=label, x_label=x_label, y_label=y_label,
                   n=n, r=r, ci_low=lo, ci_high=hi,
                   source_ids=tuple(source_ids), inputs_note=inputs_note)

    def as_row(self) -> dict:
        return {
            "id": self.corr_id,
            "label": self.label,
            "x": self.x_label,
            "y": self.y_label,
            "n": self.n,
            "r": None if self.r is None else round(self.r, 4),
            "ci_low": None if self.ci_low is None else round(self.ci_low, 4),
            "ci_high": None if self.ci_high is None else round(self.ci_high, 4),
            "method": self.method,
            "sources": list(self.source_ids),
            "inputs": self.inputs_note,
            "tier": self.tier,
        }
