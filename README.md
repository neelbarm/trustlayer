<div align="center">

# trustlayer

**Decide when a language model's output can be acted on.**

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/tests-9%20passing-2F7D4F)
![Dependencies](https://img.shields.io/badge/dependencies-none-6E7078)
![License](https://img.shields.io/badge/license-MIT-6E7078)

</div>

---

A small Python library for the layer between an extraction and a system of record. Confidence scoring, independent verification, per-field risk policy, and threshold calibration.

```bash
pip install -e .
```

---

## The problem it solves

Most extraction pipelines gate on one signal, a confidence score, and inherit a failure they never see. Confidence catches the model being *unsure*. It cannot catch the model being *sure and wrong*, because nothing in a confidently wrong answer looks hesitant.

Two signals are needed, and they catch different things.

| Signal | Catches | Misses |
|---|---|---|
| Confidence threshold | the model was unsure | confident and wrong |
| Independent verification | the source does not support the value | nothing, but it costs a second pass |

## Usage

```python
from trustlayer import Field, Policy, Verification, decide_all, render

fields = [
    Field("permit_number", "BLD-2024-041877", 0.99, verification=Verification.VERIFIED),
    Field("permit_fee",     "$1,240.00",      0.94, verification=Verification.MISMATCH),
    Field("contractor",     "Meridian Tower", 0.38, verification=Verification.NOT_FOUND),
]

policy = Policy(
    standard_bar=0.85,
    high_stakes_bar=0.95,
    high_stakes=frozenset({"permit_number"}),
)

for d in decide_all(fields, policy):
    print(d.field.name, d.disposition.value, "|", d.reason)
```

```
permit_number post   | verified
permit_fee    review | verification mismatch
contractor    review | confidence 0.38 below bar 0.85
```

Every field lands in one of three dispositions.

- **`post`** — cleared its bar and verified, safe to write
- **`review`** — a person decides
- **`escaped`** — written despite being unsupported, because nothing checked it

`escaped` only appears when you pass `verified=False`, which is how you measure what the verification pass is actually worth.

## Measuring the verification pass

```python
from trustlayer import worth_of_verification

worth_of_verification(fields, policy)   # 1
```

One wrong value that a confidence threshold alone would have written to the record. In the worked example, a fee field extracts at 0.94 confidence and returns the plan-review line item instead of the total. It clears every threshold you could reasonably set.

```bash
python examples/permit.py
```

## Calibration

A confidence bar is a business decision, not a default. Raising it sends more work to people, lowering it lets more bad values through. `sweep` walks the range so the number gets chosen on purpose.

```python
from trustlayer import sweep

for p in sweep(fields, policy, lo=0.5, hi=0.99, step=0.05):
    print(f"{p.bar:.2f}  posted={p.posted}  review={p.review}  escaped={p.escaped}")
```

High-stakes fields keep their offset above the standard bar as it moves, so a permit number or a payment amount stays stricter than a description.

## Design notes

**No dependencies.** The decision logic is pure and synchronous, so it drops into any pipeline and is trivial to test. Rendering lives in its own module and does no work beyond formatting.

**Verification is a verdict, not a score.** `Verification.MISMATCH` and `NOT_FOUND` are treated identically because both mean the same thing operationally, which is that the source does not back the value. How that verdict gets produced is your business, whether that is a second model pass, a regex, a database lookup, or a human.

**Policy is data.** Thresholds and the high-stakes set are configuration rather than constants, because the right values differ per customer and per field and should be set against a labelled sample rather than guessed.

## Tests

```bash
python -m pytest tests -q
```

The suite includes a monotonicity property: raising the threshold can never reduce review load. That invariant is easy to break when refactoring the policy logic.

## License

## Related

- **[mcp-trustlayer](https://github.com/neelbarm/mcp-trustlayer)** — the same decision exposed as an MCP server, so an agent can ask before it acts
- **[plancheck](https://github.com/neelbarm/plancheck)** — the idea applied end to end to permit intake, with a [live demo](https://plancheck-neel.netlify.app/)

MIT. Built by [Neel Barmecha](https://neelbarmecha.netlify.app/).
