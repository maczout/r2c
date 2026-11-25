#!/usr/bin/env python3
"""Does the subject have its load stages where the reference has them?

    python tools/stagematch.py REFERENCE_DIR RUN_DIR [RUN_DIR ...] [--only NAME ...]

Answers "did a change to the stage control move r2c's stages onto Response's, or off them":
for each case, how many of the reference's stages up to its peak have a stage of the
subject at the same control value (within 0.2 % of the largest control value on the bottom
control chart) and how many stages the subject has up to its own peak. The checks of
tools/compare.py measure the distance between two curves, which does not change when a
stage is added on the curve or left out; this counts the stages themselves. Nothing is
assessed: there is no target on stage counts (docs/measures.md).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
from r2c import record  # noqa: E402


def matched(ref, sub):
    key = [k for k in cmp.control_keys(ref) if k in cmp.control_keys(sub)][-1]
    a, b = cmp._curve(ref, key), cmp._curve(sub, key)
    ia, ib = int(np.argmax(np.abs(a[:, 1]))), int(np.argmax(np.abs(b[:, 1])))
    tol = 0.002 * float(np.max(np.abs(a[:, 0])))
    hit = sum(1 for x in a[: ia + 1, 0] if np.min(np.abs(b[:, 0] - x)) <= tol)
    return hit, ia + 1, ib + 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference_dir")
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args(argv)
    print("case: per run, reference stages up to the peak that the subject has / of how many "
          "(subject's stages up to its peak)")
    for ref_path in sorted(Path(a.reference_dir).glob("*.r2x.txt")):
        name = ref_path.name[: -len(".r2x.txt")]
        if a.only and name not in a.only:
            continue
        ref = record.read(ref_path)
        cells = []
        for run in a.runs:
            p = Path(run) / ref_path.name
            if not p.exists():
                cells.append("-")
                continue
            hit, n, m = matched(ref, record.read(p))
            cells.append(f"{hit}/{n} ({m})")
        print(f"{name}: " + "   ".join(cells))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
