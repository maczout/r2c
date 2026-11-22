#!/usr/bin/env python3
"""How far does the branch of one of r2c's stages reach? (cases without shear)

Answers: "at the control values between two of r2c's stages, is there still a state of
equilibrium next to the earlier stage's, and at what load?" Where a response falls at
cracking, the states before the fall end at a limit point; whether a stage lands just short
of it or just past it decides whether the curve shows one more rising point, and with it the
order in which cracking and the fall are read (docs/verification.md, "A2, part 4").

    python tools/branch.py FIXTURE.r2x.txt --stage N [--points 10] [--span 0.08] [--input FILE]

r2c solves the fixture's case to its stage N, then, at control values evenly spaced from
stage N to stage N + 1, scans the unknown strain (the curvature under axial control, the
axial strain under curvature control) around stage N's value, within the given fraction of
it, with the layers rebuilt at every state. Prints, for each control value, the load at the
state with the least unbalanced force, and that force. A branch has ended where the least
unbalanced force stops being zero.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import verify  # noqa: E402
from r2c import record, run  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("fixture")
    ap.add_argument("--stage", type=int, required=True, help="r2c's own stage number")
    ap.add_argument("--points", type=int, default=10)
    ap.add_argument("--span", type=float, default=0.08)
    ap.add_argument("--input")
    a = ap.parse_args(argv)
    ref = record.read(a.fixture)
    opts = verify.options(ref.header)
    opts.pop("more_detail", None)
    if opts["increment"][2] != 0 or opts["initial"][2] != 0:
        print("a case with shear: not covered", file=sys.stderr)
        return 2
    res = run.solve(a.input, **opts)
    if a.stage + 1 >= len(res.stages):
        print(f"r2c has {len(res.stages)} stages", file=sys.stderr)
        return 2
    su = run.setup(a.input, **opts)
    drv = su.driver(on_stage=lambda count: None)
    an = su.analysis
    prev = None
    for st in res.stages[1:a.stage + 1]:
        prev = drv.solve(st.control, prev)
    nxt = res.stages[a.stage + 1]
    axial = drv.mode == "e0"
    x0 = prev.phi if axial else prev.e0
    print(f"stage {a.stage}: control {prev.control:.6g}, N {prev.n / 1e3:.2f} kN, "
          f"M {prev.m / 1e6:.2f} kNm; stage {a.stage + 1}: control {nxt.control:.6g}, "
          f"N {nxt.n / 1e3:.2f} kN, M {nxt.m / 1e6:.2f} kNm")
    print("control       N kN     M kNm   least unbalanced " + ("moment kNm" if axial else
                                                               "axial force kN"))
    for c in np.linspace(prev.control, nxt.control, a.points):
        best = None
        for x in np.linspace(x0 * (1 - a.span), x0 * (1 + a.span), 41):
            e0, phi = (c, x) if axial else (x, c)
            an.refine(e0, phi, 0.0)
            n, m, _ = an.forces(e0, phi)
            if axial:
                r = (m - an.m0 - (n - an.n0) / an.dn * an.dm) / 1e6
            else:
                r = (n - an.n0 - (m - an.m0) / an.dm * an.dn) / 1e3
            if best is None or abs(r) < abs(best[2]):
                best = (n, m, r)
        print(f"{c:<12.6g} {best[0] / 1e3:8.2f} {best[1] / 1e6:8.2f}   {best[2]:+.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
