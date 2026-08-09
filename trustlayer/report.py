"""Terminal rendering. Kept separate so the decision logic stays free of I/O."""

from __future__ import annotations

import os
import sys

from .core import Decision, Disposition

_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _COLOR else s


def _meter(confidence: float, bar: float, width: int = 22, ok: bool = True) -> str:
    filled = round(confidence * width)
    tick = min(width - 1, round(bar * width))
    cells = []
    for i in range(width):
        ch = "#" if i < filled else "."
        if i == tick:
            ch = "|"
        cells.append(ch)
    return _c("32" if ok else "31", "".join(cells))


def render(decisions: list[Decision], *, title: str = "trustlayer") -> str:
    groups = {
        Disposition.ESCAPED: ("posted without verification", "31"),
        Disposition.REVIEW: ("held for review", "33"),
        Disposition.POST: ("posted to record", "32"),
    }
    posted = sum(1 for d in decisions if d.acted_on)
    review = sum(1 for d in decisions if d.disposition is Disposition.REVIEW)
    escaped = sum(1 for d in decisions if d.disposition is Disposition.ESCAPED)

    out = ["", f"  {_c('1', title)}", "  " + "-" * 66,
           f"  {posted} posted   {_c('33', str(review) + ' held')}   "
           + (_c("31", f"{escaped} escaped") if escaped else "0 escaped"),
           "  " + "-" * 66]

    for disp, (label, color) in groups.items():
        items = [d for d in decisions if d.disposition is disp]
        if not items:
            continue
        out.append(f"\n  {_c(color, label)} ({len(items)})")
        for d in items:
            val = d.field.value if d.field.value is not None else "-"
            val = val[:40] + "..." if len(val) > 43 else val
            out.append(f"    {d.field.name:<18}"
                       f"{_meter(d.field.confidence, d.bar, ok=disp is Disposition.POST)} "
                       f"{d.field.confidence:.2f}/{d.bar:.2f}  {val}")
            if disp is not Disposition.POST:
                out.append(f"      -> {d.reason}")
    out.append("")
    return "\n".join(out)
