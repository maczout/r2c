#!/usr/bin/env python3
"""How many cases have their first stages at Response's own control values?

    python tools/stagesat.py VERIFY_OUT [--first 25 40] [--list] [--fixtures DIR]

Answers "does r2c's stepping put its stages where Response puts its own?", stage for
stage from the start: for each case of a verify run on development fixtures, the first N
points of the bottom control chart are set beside the fixture's, and the case counts when
every one of them is at the same control value (within a thousandth of it, and the printed
precision). A rule of the stage control is held to this before it goes in: the count
should rise and no case should fall out. --list prints, for each case that does not
count, the stage where the two part and the control values around it. Never anything of
the held-out set.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
from r2c import record  # noqa: E402


def parts_at(ref, sub, first: int):
    """The index of the first of the first `first` stages at which the two bottom control
    charts are at different control values, or None; and the two curves."""
    key = cmp.control_keys(ref)[-1]
    a, b = cmp._curve(ref, key), cmp._curve(sub, key)
    m = min(len(a), len(b), first)
    for i in range(m):
        if abs(a[i, 0] - b[i, 0]) > 2e-3 * max(1.0, abs(a[i, 0])) + 1.5e-3:
            return i, a, b
    return None, a, b


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("verify_out")
    ap.add_argument("--first", type=int, nargs="*", default=[25, 40])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--fixtures", default=str(ROOT / "tests" / "oracle"))
    a = ap.parse_args(argv)
    vo = Path(a.verify_out)
    if "heldout" in str(vo.resolve()):
        ap.error("not on the held-out set (CLAUDE.md, the held-out rule)")
    results = json.loads((vo / "results.json").read_text())
    names = [n for n, r in sorted(results.items())
             if "control" in r and (vo / f"{n}.r2x.txt").exists()]
    for first in a.first:
        count = 0
        for n in names:
            ref = record.read(Path(a.fixtures) / f"{n}.r2x.txt")
            i, x, y = parts_at(ref, record.read(vo / f"{n}.r2x.txt"), first)
            count += i is None
            if a.list and i is not None and first == a.first[-1]:
                print(f"  {n}: part at stage {i}: Response "
                      f"{[round(float(v), 4) for v in x[max(i - 1, 0): i + 3, 0]]}, r2c "
                      f"{[round(float(v), 4) for v in y[max(i - 1, 0): i + 3, 0]]}")
        print(f"first {first} stages at Response's control values: {count} of {len(names)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
