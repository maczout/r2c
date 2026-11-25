#!/usr/bin/env python3
"""Which shear responses does r2c end early, and where?

    python tools/earlyends.py VERIFY_OUT [VERIFY_OUT ...] [--only NAME ...] [--fixtures DIR]

Answers "how many of these cases end early, and at what control value": the diagnostic of
the shear profile iteration (docs/summary.md, D48), run on the parked I-girders with shear
every time that part of the kernel changes. For every case with shear in a tools/verify.py
run, on the bottom control chart: the control value and load at Response's peak, the
control value r2c's response reaches and its largest load. A response **ends early** when
r2c's last stage is short of the control value at Response's peak (by more than 2 % of
it) and its largest load is under Response's peak by more than the tolerance of
docs/measures.md on a peak (5 %). With several runs, one column per run.

Nothing is solved and nothing is assessed here: the parked cases are not set members.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare  # noqa: E402
from r2c import record  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PEAK_PCT = 5.0


def curve(rec):
    return compare._curve(rec, compare.control_keys(rec)[-1])


def one(ref, sub):
    """(control at Response's peak, its peak load, r2c's furthest control value, r2c's
    largest load, ends early)."""
    cr, cs = curve(ref), curve(sub)
    k = int(abs(cr[:, 1]).argmax())
    x_peak, y_peak = float(cr[k, 0]), float(cr[k, 1])
    start = float(cr[0, 0])
    travel = abs(x_peak - start)
    reach = float(cs[int(abs(cs[:, 0] - start).argmax()), 0])
    top = float(cs[int(abs(cs[:, 1]).argmax()), 1])
    short = abs(reach - start) < 0.98 * travel
    low = abs(top) < (1.0 - PEAK_PCT / 100.0) * abs(y_peak)
    return x_peak, y_peak, reach, top, short and low


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verify_out", nargs="+", help="folders of tools/verify.py runs")
    ap.add_argument("--only", nargs="*", help="case names")
    ap.add_argument("--fixtures", default=str(ROOT / "tests" / "oracle"))
    a = ap.parse_args(argv)
    runs = [Path(p) for p in a.verify_out]
    names = sorted(set.intersection(*[
        {n for n, r in json.loads((p / "results.json").read_text()).items()
         if "control" in r and float(r["ref"]["increment"].split(",")[2]) != 0.0}
        for p in runs]))
    early = [0] * len(runs)
    total = 0
    for name in names:
        if a.only and name not in a.only:
            continue
        fx = Path(a.fixtures) / f"{name}.r2x.txt"
        ref = record.read(fx if fx.exists() else fx.parent / "parked" / fx.name)
        total += 1
        cells = []
        for i, p in enumerate(runs):
            x_peak, y_peak, reach, top, is_early = one(ref, record.read(p / f"{name}.r2x.txt"))
            early[i] += is_early
            cells.append(f"reaches {reach:.4g}, largest load {top:.4g} "
                         f"({100.0 * (top / y_peak - 1.0):+.1f} %)"
                         + (" EARLY" if is_early else ""))
        print(f"{name}: Response's peak {y_peak:.4g} at {x_peak:.4g}; r2c " + " | ".join(cells))
    print("end early: " + " | ".join(f"{e} of {total}" for e in early))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
