#!/usr/bin/env python3
"""Print the lines of one detail view at one stage, from two records side by side.

Answers: "where over the depth, and on which line of the chart, do the two programs' views
differ?" The comparison in tools/compare.py gives one number per view; this shows the values
behind it.

    python tools/viewlines.py REFERENCE.r2x.txt SUBJECT.r2x.txt principal_tensile_stress
        [--stage N | --feature peak] [--sub-stage M] [--raw]

The reference's stage is N, or the stage at the named feature of its curve (cracking, fall,
peak, ends ...; default: the peak). The subject's stage is the one tools/compare.py matches
to it (between the same features of the curves, D13) unless --sub-stage is given. Each line
of the reference's chart is printed at its own depths, with the subject's same-numbered line
interpolated to those depths and the difference. --raw prints each record's own points as
(value, depth) in the order they are drawn, which is what to read for a chart drawn as
boxes (the steel stresses) or with several points at one depth (a step in width).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
from r2c import record  # noqa: E402


def matched_stage(ref, sub, ref_stage: int) -> int:
    """The subject's stage that tools/compare.py compares with the reference's."""
    key = cmp.control_keys(ref)[-1]
    c = cmp._curve(ref, key)
    pk = float(np.max(np.abs(c[:, 1]))) or 1.0
    xs = float(np.max(np.abs(c[:, 0]))) or 1.0
    return cmp._segment_stage(sub, key, ref_stage, c, cmp._curve(sub, key), c[ref_stage, 0],
                              c[ref_stage, 1], xs, pk)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("reference")
    ap.add_argument("subject")
    ap.add_argument("view")
    ap.add_argument("--stage", type=int)
    ap.add_argument("--feature", default="peak")
    ap.add_argument("--sub-stage", type=int)
    ap.add_argument("--raw", action="store_true",
                    help="each record's own points in the order drawn, nothing interpolated")
    a = ap.parse_args(argv)
    ref, sub = record.read(a.reference), record.read(a.subject)
    feats = cmp.feature_stages(ref)
    if a.stage is None:
        hit = [n for n, f in feats.items() if f.startswith(a.feature)]
        if not hit:
            print(f"no feature {a.feature!r}; the reference has {feats}", file=sys.stderr)
            return 2
        a.stage = hit[0]
    ss = a.sub_stage if a.sub_stage is not None else matched_stage(ref, sub, a.stage)
    la = cmp.parse_chart(ref.stage(a.stage, a.view))[3]
    lb = cmp.parse_chart(sub.stage(ss, a.view))[3]
    print(f"{a.view}: reference stage {a.stage} ({feats.get(a.stage, '-')}), subject stage {ss}; "
          f"lines {len(la)} / {len(lb)}")
    if a.raw:
        for who, lines in (("reference", la), ("subject", lb)):
            for i, ln in enumerate(lines):
                print(f"{who} line {i}: " + " ".join(f"({x:.4f},{y:.2f})" for x, y in ln))
        return 0
    for i, ln in enumerate(la):
        print(f"line {i}: {len(ln)} points" + (f" / {len(lb[i])}" if i < len(lb) else " / none"))
        other = lb[i] if i < len(lb) and len(lb[i]) else None
        if other is not None:
            o = other[np.argsort(other[:, 1], kind="stable")]
        for x, y in ln:
            if other is None:
                print(f"  {y:10.3f} {x:12.4f}")
            else:
                v = float(np.interp(y, o[:, 1], o[:, 0]))
                print(f"  {y:10.3f} {x:12.4f} {v:12.4f} {v - x:+10.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
