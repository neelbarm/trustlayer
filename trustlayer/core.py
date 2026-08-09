"""Core decision types.

The premise: a language model returning a value is not the same as a system
being allowed to act on it. Two independent signals decide that, and they catch
different failures.

  confidence   catches the model being unsure
  verification catches the model being sure and wrong

A confidence threshold on its own cannot catch the second case, because nothing
in a confidently wrong answer looks hesitant. Most extraction pipelines ship
with only the first signal and inherit the second failure silently.
"""

from __future__ import annotations

from dataclasses import dataclass, field as _field
from enum import Enum


class Verification(str, Enum):
    """Verdict from an independent pass that re-checks a value against its source."""

    VERIFIED = "verified"      # the source supports this value
    MISMATCH = "mismatch"      # the source says something different
    NOT_FOUND = "not_found"    # the source does not support this value
    UNCHECKED = "unchecked"    # no verification pass ran


class Disposition(str, Enum):
    POST = "post"        # safe to write to the system of record
    REVIEW = "review"    # a person decides
    ESCAPED = "escaped"  # written despite being unsupported, because nothing checked


@dataclass(frozen=True)
class Field:
    """One extracted value, plus everything needed to judge it."""

    name: str
    value: str | None
    confidence: float = 0.0
    evidence: str | None = None
    verification: Verification = Verification.UNCHECKED

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"{self.name}: confidence must be in [0,1], got {self.confidence}")


@dataclass
class Policy:
    """Per-customer risk configuration.

    high_stakes names the fields where a wrong value is expensive enough to
    justify more human review. They are held to a stricter bar than the rest.
    """

    standard_bar: float = 0.85
    high_stakes_bar: float = 0.95
    high_stakes: frozenset[str] = _field(default_factory=frozenset)

    def bar_for(self, name: str) -> float:
        return self.high_stakes_bar if name in self.high_stakes else self.standard_bar


@dataclass(frozen=True)
class Decision:
    field: Field
    disposition: Disposition
    bar: float
    reason: str

    @property
    def acted_on(self) -> bool:
        return self.disposition in (Disposition.POST, Disposition.ESCAPED)


def decide(field: Field, policy: Policy, *, verified: bool = True) -> Decision:
    """Judge a single field.

    `verified` describes whether a verification pass actually ran. Passing False
    is how you measure what that pass is worth, since unsupported values then
    surface as ESCAPED instead of being quietly held back.
    """
    bar = policy.bar_for(field.name)
    unsupported = field.verification in (Verification.MISMATCH, Verification.NOT_FOUND)

    if field.value is None:
        return Decision(field, Disposition.REVIEW, bar, "no value extracted")
    if verified and unsupported:
        return Decision(field, Disposition.REVIEW, bar, f"verification {field.verification.value}")
    if field.confidence < bar:
        tag = "high-stakes " if field.name in policy.high_stakes else ""
        return Decision(field, Disposition.REVIEW, bar,
                        f"{tag}confidence {field.confidence:.2f} below bar {bar:.2f}")
    if not verified and unsupported:
        return Decision(field, Disposition.ESCAPED, bar,
                        "posted unchecked, source does not support this value")
    return Decision(field, Disposition.POST, bar,
                    "verified" if verified else "above bar, unverified")


def decide_all(fields, policy: Policy, *, verified: bool = True) -> list[Decision]:
    return [decide(f, policy, verified=verified) for f in fields]
