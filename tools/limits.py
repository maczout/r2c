"""Do the regression limits of tests/test_oracle.py hold on a verify run?

    python tools/limits.py VERIFY_OUT [--write]

The regression tests solve each case again and take minutes on the shear cases. A verify
run has already solved them and measured the same two figures (the peak's difference and
the curve's largest distance, per control chart, tools/compare.py). This reads the limits
from the test module and sets them against the run's results, so the slow tests need not
be run again to know which would fail. Cases of the run without a limit, and limits whose
case is not in the run (the parked ones, on a run of the set), are counted and not listed.

The limits of the first development cases are written in the test module. Those of the
wider cases are generated: --write puts a limit for every case of the run that has none
into tests/oracle/limits.json, a little above what the run measured (the larger of the
figure times 1.5 and the figure plus 0.05 % on the peak, 0.1 % on the curve; times 2 plus
0.5 % for a case with shear, whose stages do not all settle). A case that has a generated
limit keeps it: --write adds, it does not loosen. tests/test_oracle.py reads the file too.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "tests" / "oracle" / "limits.json"


def generated() -> dict:
    """{case: [peak limit, curve limit]} of tests/oracle/limits.json."""
    return json.loads(GENERATED.read_text()) if GENERATED.exists() else {}


def write(verify_out: Path, have: dict) -> int:
    """Add a generated limit for every case of the run that has none."""
    import math
    gen = generated()
    added = 0
    for p in sorted(verify_out.glob("*.json")):
        case = p.stem
        if case in have or case in gen or case in ("results", "run"):
            continue
        res = json.loads(p.read_text())
        if not res.get("control"):
            continue
        inc = [float(x) for x in res["ref"]["increment"].split(",")]
        ini = [float(x) for x in res["ref"]["initial"].split(",")]
        shear = inc[2] != 0.0 or ini[2] != 0.0
        peak = max(abs(c["peak_diff_pct"]) for c in res["control"])
        curve = max(c.get("curve_max_diff_pct", 0.0) for c in res["control"])

        def above(v, least):
            v = max(2.0 * v + 0.5, least) if shear else max(1.5 * v, v + least)
            return math.ceil(v * 100.0) / 100.0

        gen[case] = [above(peak, 0.05), above(curve, 0.1)]
        added += 1
    GENERATED.write_text(json.dumps(dict(sorted(gen.items())), indent=1) + "\n")
    return added


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
    for case, lim in generated().items():
        out.setdefault(case, ("generated", tuple(lim)))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("verify_out")
    ap.add_argument("--write", action="store_true",
                    help="add a generated limit for every case of the run that has none")
    a = ap.parse_args(argv)
    if a.write:
        hand = {c for c, (g, _l) in limits().items() if g != "generated"}
        print(f"{write(Path(a.verify_out), hand)} limits added to {GENERATED.name}")
    lim = limits()
    run = {p.stem: p for p in Path(a.verify_out).glob("*.json")
           if p.stem not in ("results", "run")}
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
