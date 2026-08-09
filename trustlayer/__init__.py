"""trustlayer: decide when a language model's output can be acted on.

    from trustlayer import Field, Policy, Verification, decide_all

    fields = [Field("total", "$2,225.00", 0.94, verification=Verification.VERIFIED)]
    policy = Policy(standard_bar=0.85, high_stakes={"total"})
    for d in decide_all(fields, policy):
        print(d.field.name, d.disposition.value, d.reason)
"""

from .core import Decision, Disposition, Field, Policy, Verification, decide, decide_all
from .calibrate import Point, at, sweep, worth_of_verification
from .report import render

__version__ = "0.1.0"
__all__ = ["Field", "Policy", "Verification", "Disposition", "Decision",
           "decide", "decide_all", "sweep", "at", "Point",
           "worth_of_verification", "render"]
