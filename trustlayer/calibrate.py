"""Threshold calibration.

Choosing a confidence bar is a business decision, not a default. Raising it
sends more work to people; lowering it lets more bad values through. sweep()
prints that tradeoff so the number gets chosen deliberately.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .core import Disposition, Field, Policy, decide_all


@dataclass(frozen=True)
class Point:
    bar: float
    posted: int
    review: int
    escaped: int

    @property
    def review_rate(self) -> float:
        total = self.posted + self.review + self.escaped
        return self.review / total if total else 0.0


def at(fields: list[Field], policy: Policy, *, verified: bool = True) -> Point:
    ds = decide_all(fields, policy, verified=verified)
    counts = {d.disposition: 0 for d in (
        *(d for d in ds),)}
    posted = sum(1 for d in ds if d.disposition is Disposition.POST)
    review = sum(1 for d in ds if d.disposition is Disposition.REVIEW)
    escaped = sum(1 for d in ds if d.disposition is Disposition.ESCAPED)
    return Point(policy.standard_bar, posted, review, escaped)


def sweep(fields: list[Field], policy: Policy, *,
          lo: float = 0.50, hi: float = 0.99, step: float = 0.05,
          verified: bool = True) -> list[Point]:
    """Walk the standard bar across a range, holding the high-stakes offset fixed."""
    offset = policy.high_stakes_bar - policy.standard_bar
    points, bar = [], lo
    while bar <= hi + 1e-9:
        p = replace(policy, standard_bar=round(bar, 4),
                    high_stakes_bar=round(min(0.99, bar + offset), 4))
        points.append(at(fields, p, verified=verified))
        bar += step
    return points


def worth_of_verification(fields: list[Field], policy: Policy) -> int:
    """How many wrong values the verification pass keeps out of the record."""
    return at(fields, policy, verified=False).escaped
