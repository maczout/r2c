#!/usr/bin/env python3
"""Compare the node depths of two records at one stage.

Answers: "does r2c put its nodes where Response-2000 puts its own?" A detail view lists its
values node by node, so the depths of a view are the nodes of the stage. Where one program
has a node and the other has none, a point of the first can lie off the second's line: at a
crack front that was the whole difference in the Principal Tensile Stress view before r2c
took over Response's layering (docs/kernel.md, "Layers").

    python tools/nodes.py REFERENCE.r2x.txt SUBJECT.r2x.txt [--stage N | --feature peak]
        [--sub-stage M] [--view principal_tensile_stress]

The stages are chosen as tools/viewlines.py chooses them. Prints the number of nodes of each
and the depths only one of them has.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
import viewlines  # noqa: E402
from r2c import record  # noqa: E402


def depths(rec, stage: int, view: str) -> list[float]:
    """Depths of the first line of a view at a stage, as the chart lists them."""
    return [float(y) for _x, y in cmp.parse_chart(rec.stage(stage, view))[3][0]]


def only(a: list[float], b: list[float], tol: float) -> list[float]:
    return [x for x in a if not any(abs(x - y) < tol for y in b)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("reference")
    ap.add_argument("subject")
    ap.add_argument("--stage", type=int)
    ap.add_argument("--feature", default="peak")
    ap.add_argument("--sub-stage", type=int)
    ap.add_argument("--view", default="principal_tensile_stress")
    ap.add_argument("--tol", type=float, default=0.01, help="depths closer than this are one")
    a = ap.parse_args(argv)
    ref, sub = record.read(a.reference), record.read(a.subject)
    stage = a.stage
    if stage is None:
        feats = cmp.feature_stages(ref)
        hit = [n for n, f in feats.items() if f.startswith(a.feature)]
        if not hit:
            print(f"no feature {a.feature!r}; the reference has {feats}", file=sys.stderr)
            return 2
        stage = hit[0]
    sub_stage = a.sub_stage if a.sub_stage is not None else \
        viewlines.matched_stage(ref, sub, stage)
    r, s = depths(ref, stage, a.view), depths(sub, sub_stage, a.view)
    print(f"reference stage {stage}: {len(r)} nodes; subject stage {sub_stage}: {len(s)}")
    print("only in the reference:", only(r, s, a.tol))
    print("only in the subject:", only(s, r, a.tol))
    return 0


if __name__ == "__main__":
    sys.exit(main())
