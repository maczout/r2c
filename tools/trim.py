#!/usr/bin/env python3
"""Cut a record down to a test fixture: its control charts and the detail views of a few stages.

    python tools/trim.py RECORD.r2x.txt OUT.r2x.txt [--stages peak,20]

A record of every stage runs to megabytes; the comparisons in tests/ need the control charts
and the peak. The header is kept, with detail-stages changed to the stages that remain.

Neighbouring stages (owner, 2026-11-23, D54; docs/measures.md, "Where Response is
unstable"): the test for an unstable view needs Response's views at the stage just before and
just after each compared stage. They are kept as sections neighbour/N/VIEW, not stage/N/VIEW,
so that the stages of a fixture (Record.stages, detail-stages) stay the compared stages and
nothing else reads the neighbours as stages to compare. Only what the test needs is kept: a
compared stage that is the first or last of the curve is not tested, so nothing is kept for
it, and a neighbour that is itself a compared stage is not kept twice. --near adds them.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from r2c import record, stages  # noqa: E402


NEAR = "neighbour/"


def near_stages(rec) -> list[int]:
    """The stages a cut record holds as neighbours (sections neighbour/N/VIEW), ascending."""
    return sorted({int(name.split("/")[1]) for name in rec.sections if name.startswith(NEAR)})


def near_needed(rec, keep) -> list[int]:
    """The neighbouring stages the test for an unstable view needs, for a full record cut to
    the stages keep: the stage before and the stage after each kept stage that has both,
    leaving out those that are kept stages themselves."""
    have = set(rec.stages())
    keep = set(keep) & have
    out = set()
    for n in keep:
        if n - 1 in have and n + 1 in have:
            out |= {n - 1, n + 1}
    return sorted(out - keep)


def trim(rec, keep: list[int], near: list[int] = ()) -> bytes:
    """The record cut to its control charts, the detail views of the stages keep, and the
    detail views of the stages near as neighbours (neighbour/N/VIEW)."""
    keep = sorted(set(n for n in keep if n in rec.stages()))
    near = set(near) - set(keep)
    header = dict(rec.header)
    header["detail-stages"] = stages.format_ranges(keep)
    sections, after = [], []
    for name, body in rec.sections.items():
        if name.startswith("control/"):
            sections.append((name, body))
        elif name.startswith("stage/") and int(name.split("/")[1]) in keep:
            sections.append((name, body))
        elif name.startswith("stage/") and int(name.split("/")[1]) in near:
            after.append((NEAR + name[len("stage/"):], body))
    return record.encode(header, sections + after)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("record")
    ap.add_argument("out")
    ap.add_argument("--stages", default="peak", help="stage numbers to keep, or peak")
    ap.add_argument("--near", action="store_true",
                    help="also keep the neighbouring stages the test for an unstable view needs")
    a = ap.parse_args(argv)
    rec = record.read(a.record)
    peak = int(rec.header.get("peak-stage", "0"))
    keep = [peak if s == "peak" else int(s) for s in a.stages.split(",")]
    Path(a.out).write_bytes(trim(rec, keep, near_needed(rec, keep) if a.near else ()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
