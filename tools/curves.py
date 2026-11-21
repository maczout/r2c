#!/usr/bin/env python3
"""Print the control curves of two records point by point, one above the other.

Answers: "where along the curve do the two responses part, and how does each end?" The
comparison in tools/compare.py gives a few numbers per chart; this shows the points behind
them, as (control value, load) in the charts' own units.

    python tools/curves.py REFERENCE.r2x.txt SUBJECT.r2x.txt [--last N] [--chart KEY]

--last N prints only the last N points of each curve. --chart picks one control chart (for
example moment_phi); the default is every chart of the reference.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
from r2c import record  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("reference")
    ap.add_argument("subject")
    ap.add_argument("--last", type=int, default=0)
    ap.add_argument("--chart")
    a = ap.parse_args(argv)
    ref, sub = record.read(a.reference), record.read(a.subject)
    for key in cmp.control_keys(ref):
        if a.chart and key != a.chart:
            continue
        print(key)
        for label, rec in (("reference", ref), ("subject", sub)):
            try:
                c = cmp._curve(rec, key)
            except KeyError:
                print(f"  {label}: no such chart")
                continue
            pts = c[-a.last:] if a.last else c
            print(f"  {label} ({len(c)} points): "
                  + " ".join(f"({x:.3f},{y:.1f})" for x, y in pts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
