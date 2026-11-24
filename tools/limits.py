"""Do the regression limits of tests/test_oracle.py hold on a verify run?

    python tools/limits.py VERIFY_OUT

The regression tests solve each case again and take minutes on the shear cases. A verify
run has already solved them and measured the same two figures (the peak's difference and
the curve's largest distance, per control chart, tools/compare.py). This reads the limits
from the test module and sets them against the run's results, so the slow tests need not
be run again to know which would fail. Cases of the run without a limit, and limits whose
case is not in the run (the parked ones, on a run of the set), are counted and not listed.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def limits():
    spec = importlib.util.spec_from_file_location("test_oracle", ROOT / "tests" / "test_oracle.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = {}
    for name in dir(mod):
        d = getattr(mod, name)
        if name.isupper() and isinstance(d, dict):
            for case, lim in d.items():
                if isinstance(lim, tuple) and len(lim) == 2:
                    out[case] = (name, lim)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("verify_out")
    a = ap.parse_args(argv)
    lim = limits()
    run = {p.stem: p for p in Path(a.verify_out).glob("*.json")}
    checked = over = 0
    for case in sorted(run):
        if case not in lim:
            continue
        group, (peak, curve) = lim[case]
        res = json.loads(run[case].read_text())
        if "control" not in res:
            continue
        checked += 1
        for c in res["control"]:
            p, d = abs(c["peak_diff_pct"]), c.get("curve_max_diff_pct", 0.0)
            if p > peak or d > curve:
                over += 1
                print(f"over: {case} ({group}), {c['chart']}: peak {c['peak_diff_pct']:+.2f} % "
                      f"against {peak}, curve {d:.2f} % against {curve}")
    print(f"{checked} cases of the run have a regression limit; {over} chart(s) over; "
          f"{len(run) - checked} without a limit; {len(set(lim) - set(run))} limits not in "
          f"this run")
    return 1 if over else 0


if __name__ == "__main__":
    raise SystemExit(main())
