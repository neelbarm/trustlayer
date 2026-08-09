import pytest

from trustlayer import (Disposition, Field, Policy, Verification,
                        decide, decide_all, sweep, worth_of_verification)

POLICY = Policy(standard_bar=0.85, high_stakes_bar=0.95, high_stakes=frozenset({"permit_number"}))


def f(name="x", value="v", conf=0.99, ver=Verification.VERIFIED):
    return Field(name, value, conf, verification=ver)


def test_high_confidence_verified_posts():
    assert decide(f(), POLICY).disposition is Disposition.POST


def test_low_confidence_goes_to_review():
    d = decide(f(conf=0.40), POLICY)
    assert d.disposition is Disposition.REVIEW
    assert "below bar" in d.reason


def test_high_stakes_field_uses_the_stricter_bar():
    # 0.90 clears the standard bar but not the high-stakes one
    assert decide(f(name="other", conf=0.90), POLICY).disposition is Disposition.POST
    assert decide(f(name="permit_number", conf=0.90), POLICY).disposition is Disposition.REVIEW


def test_confident_but_unsupported_is_held_when_verification_runs():
    d = decide(f(conf=0.97, ver=Verification.MISMATCH), POLICY)
    assert d.disposition is Disposition.REVIEW
    assert "verification" in d.reason


def test_confident_but_unsupported_escapes_when_verification_is_skipped():
    """The whole reason the library exists: a threshold cannot catch this."""
    d = decide(f(conf=0.97, ver=Verification.MISMATCH), POLICY, verified=False)
    assert d.disposition is Disposition.ESCAPED
    assert d.acted_on is True


def test_missing_value_always_goes_to_review():
    assert decide(f(value=None, conf=0.0), POLICY).disposition is Disposition.REVIEW


def test_confidence_outside_range_is_rejected():
    with pytest.raises(ValueError):
        Field("x", "v", 1.4)


def test_raising_the_bar_never_reduces_review_load():
    fields = [f(name=f"n{i}", conf=c) for i, c in enumerate([0.55, 0.72, 0.88, 0.93, 0.99])]
    points = sweep(fields, POLICY, lo=0.5, hi=0.95, step=0.05)
    loads = [p.review for p in points]
    assert loads == sorted(loads), "review load must be monotonic in the threshold"


def test_worth_of_verification_counts_what_it_keeps_out():
    fields = [f(name="a", conf=0.99, ver=Verification.MISMATCH),
              f(name="b", conf=0.99, ver=Verification.VERIFIED)]
    assert worth_of_verification(fields, POLICY) == 1
    assert all(d.disposition is not Disposition.ESCAPED
               for d in decide_all(fields, POLICY, verified=True))
