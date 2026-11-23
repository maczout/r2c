#!/usr/bin/env python3
"""What did r2c's load stage control do, try by try, on a case with shear? Answers "why is
r2c's stage here and Response's there": every target tried, whether its solve closed, how far
the shear profile iteration got, the state code, and whether the stage was kept, refused,
set aside or dropped.

    python tools/trace.py RECORD [--input FILE] [--set NAME=VALUE ...] [--upto N]

RECORD is an r2x-raw record of the case (a fixture or a capture): its header gives the
loading; --input the section file where it is not Response's built-in one. --set switches
an attribute of the analysis or of the driver before the run (own_stirrup_history=1 on the
analysis; anything else on the driver), to see what a rule that is written and off does.

Columns: stages kept so far; the control variable and its target (rad/km or mm/m); the step
multiplier; what came of it; the load factor; the profile error in Response's measure (%);
passes; the state code; whether the state is cracked; then the curvature, the centroid's
strain and the mean shear strain of the state.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import diagnose  # noqa: E402
from r2c import record  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("record")
    ap.add_argument("--input")
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    ap.add_argument("--upto", type=int, default=400, help="stop after this many stages")
    a = ap.parse_args()
    ref = record.read(a.record)
    su = diagnose._setup(ref, a.input)
    drv = su.driver()
    for item in a.set:
        name, _, val = item.partition("=")
        obj = su.analysis if hasattr(type(su.analysis), name) else drv
        if not hasattr(obj, name):
            raise SystemExit(f"nothing called {name} on the analysis or the driver")
        setattr(obj, name, type(getattr(obj, name))(float(val)))
    drv.trace = []
    stages = drv.run(a.upto)
    print(f"{'kept':>4} {'ctl':>3} {'target':>9} {'mult':>6} {'what':<9} {'load':>8} "
          f"{'err %':>7} {'pass':>4} {'code':>4} {'crk':>3} {'phi':>8} {'e0':>8} {'gam':>8}")
    for t in drv.trace:
        k = 1e6 if t["mode"] == "phi" else 1e3
        st = t.get("stage")
        what = t.get("what") or ("kept" if t["kept"] else "refused" if t["solved"]
                                 else "no state")
        lam = "" if t["lam"] is None else f"{t['lam']:8.2f}"
        err = "" if t["perr"] is None else f"{100 * t['perr']:7.2f}"
        tail = ""
        if st is not None:
            crk = "y" if bool(st.detail.out.cracked.any()) else "n"
            tail = (f"{crk:>3} {st.phi * 1e6:8.4f} {st.e0 * 1e3:8.4f} "
                    f"{getattr(st, 'gam_avg', st.gam) * 1e3:8.4f}")
        print(f"{t['n']:4d} {t['mode']:>3} {t['target'] * k:9.4f} {t['mult']:6.3f} {what:<9} "
              f"{lam:>8} {err:>7} {t['passes'] or 0:4d} {t['code']:4d} {tail}")
    print(f"{len(stages)} stages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
