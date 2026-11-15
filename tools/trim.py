#!/usr/bin/env python3
"""Cut a record down to a test fixture: its control charts and the detail views of a few stages.

    python tools/trim.py RECORD.r2x.txt OUT.r2x.txt [--stages peak,20]

A record of every stage runs to megabytes; the comparisons in tests/ need the control charts
and the peak. The header is kept, with detail-stages changed to the stages that remain.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from r2c import record, stages  # noqa: E402


def trim(rec, keep: list[int]) -> bytes:
    keep = sorted(set(n for n in keep if n in rec.stages()))
    header = dict(rec.header)
    header["detail-stages"] = stages.format_ranges(keep)
    sections = []
    for name, body in rec.sections.items():
        if name.startswith("control/"):
            sections.append((name, body))
        elif name.startswith("stage/") and int(name.split("/")[1]) in keep:
            sections.append((name, body))
    return record.encode(header, sections)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("record")
    ap.add_argument("out")
    ap.add_argument("--stages", default="peak", help="stage numbers to keep, or peak")
    a = ap.parse_args(argv)
    rec = record.read(a.record)
    peak = int(rec.header.get("peak-stage", "0"))
    keep = [peak if s == "peak" else int(s) for s in a.stages.split(",")]
    Path(a.out).write_bytes(trim(rec, keep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
