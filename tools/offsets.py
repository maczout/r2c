#!/usr/bin/env python3
"""The strain states of two records, stage by stage, side by side.

Answers: "at which stages does r2c's state differ from Response's, and by how much strain?"
(asked in A3 for the stages where Response's solve stops inside its tolerance and not at
the balanced state). The state of a stage is read from its Longitudinal Strain view, so both
records must hold that view for the stage: the archive's captures do, and a verify run's
records hold it at the feature stages.

    python tools/offsets.py ARCHIVE/NAME.r2x.txt VERIFY_OUT/NAME.r2x.txt [--last N]

Strains in mm/m, curvature in rad/km. A stage is listed when both records have its view.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from r2c import record  # noqa: E402
import diagnose  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("reference")
    ap.add_argument("subject")
    ap.add_argument("--last", type=int, default=0, help="only the last N stages of each")
    a = ap.parse_args(argv)
    ref, sub = record.read(a.reference), record.read(a.subject)
    su = diagnose._setup(ref, None)

    def states(rec):
        n = int(rec.header["stage-count"])
        out = {}
        for i in range(n):
            if f"stage/{i}/longitudinal_strain" in rec.sections:
                out[i] = diagnose.strain_state(rec, su, i)[:2]
        return n, out

    (nr, sr), (ns, ss) = states(ref), states(sub)
    print(f"stages: reference {nr}, subject {ns}")
    print("from the end   reference: stage, e0, phi     subject: stage, e0, phi     "
          "difference: e0, phi")
    for back in range(max(nr, ns)):
        i, j = nr - 1 - back, ns - 1 - back
        if a.last and back >= a.last:
            break
        if i in sr and j in ss:
            (e1, p1), (e2, p2) = sr[i], ss[j]
            print(f"{-back:5d}   {i:4d} {e1*1e3:10.5f} {p1*1e6:11.5f}   {j:4d} {e2*1e3:10.5f} "
                  f"{p2*1e6:11.5f}   {(e2-e1)*1e3:+9.5f} {(p2-p1)*1e6:+10.5f}")


if __name__ == "__main__":
    main()
