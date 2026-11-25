"""Is a response in other units the SI response after conversion?

    python tools/unitcheck.py SI_RECORD OTHER_RECORD [--points]

Sets the control curves of two records of the same section and loads side by side, one in
SI units and one in US or kg-cm units, after converting the second to SI with the
conversion factors of r2c/units.py (which are Response's own, as its charts show them).
The loads must be the same physically: a US case at M/V = 1 ft against an SI case at
M/V = 0.3048 m. Printed per control chart: the number of stages, the peaks, the two-way
distance of the curves as tools/compare.py measures it, and the shape.

Used on two of Response's own captures it answers "do the units in effect change what
Response calculates, or only what it reads and prints?"; on two of r2c's records, the same
for r2c; on Response's SI capture and r2c's record of the other-units case, how much of a
miss on that case is units at all (step A-5).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
from r2c import record  # noqa: E402
from r2c.units import FILE_UNITS, SI  # noqa: E402

# what each control chart plots: (the control value, the load)
AXES = {"moment_phi": ("curv", "moment"), "shear_gxy": ("strain", "force"),
        "axial_ex": ("strain", "force"), "moment_ex": ("strain", "moment")}


def to_si(curve, key, u):
    kx, ky = AXES[key]
    fx = 1.0 if kx == "strain" else getattr(u, kx) / getattr(SI, kx)
    fy = getattr(u, ky) / getattr(SI, ky)
    return np.column_stack([curve[:, 0] * fx, curve[:, 1] * fy])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("si_record")
    ap.add_argument("other_record")
    ap.add_argument("--points", action="store_true", help="list the two curves' points")
    a = ap.parse_args(argv)
    ref, sub = record.read(a.si_record), record.read(a.other_record)
    ur, us = FILE_UNITS[ref.header["units"]], FILE_UNITS[sub.header["units"]]
    print(f"reference: units {ur.name}, {ref.header['stage-count']} stages; "
          f"other: units {us.name}, {sub.header['stage-count']} stages")
    for key in cmp.control_keys(ref):
        if key not in cmp.control_keys(sub) or key not in AXES:
            continue
        ca = to_si(cmp._curve(ref, key), key, ur)
        cb = to_si(cmp._curve(sub, key), key, us)
        ia = int(np.argmax(np.abs(ca[:, 1])))
        ib = int(np.argmax(np.abs(cb[:, 1])))
        pk = abs(ca[ia, 1])
        xw = float(np.max(np.abs(ca[:, 0])))
        rise, post = cmp.two_way(ca, ia, cb, xw, pk)
        sa = [f for f, _ in cmp.shape(ca, pk, xw)]
        sb = [f for f, _ in cmp.shape(cb, pk, xw)]
        print(f"{key}: peak {ca[ia, 1]:.3f} at {ca[ia, 0]:.4f} (stage {ia}) | "
              f"{cb[ib, 1]:.3f} at {cb[ib, 0]:.4f} (stage {ib}): "
              f"{100 * (abs(cb[ib, 1]) - pk) / pk:+.2f} %; rising "
              f"{'-' if rise is None else f'{100 * rise:.2f} %'}; post-peak "
              f"{'-' if post is None else f'{100 * post:.2f} %'}")
        print(f"    shape {'the same' if sa == sb else 'DIFFERENT'}: {', '.join(sa)} | "
              f"{', '.join(sb)}")
        if a.points:
            for i in range(max(len(ca), len(cb))):
                p = f"{ca[i, 0]:10.4f} {ca[i, 1]:10.3f}" if i < len(ca) else " " * 21
                q = f"{cb[i, 0]:10.4f} {cb[i, 1]:10.3f}" if i < len(cb) else ""
                print(f"    {i:4d} {p}    {q}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
