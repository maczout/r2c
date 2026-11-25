#!/usr/bin/env python3
"""How does each shear response end, in Response-2000 and in r2c?

    python tools/ends.py VERIFY_OUT [--only NAME ...]

Answers: "Response's last stage is often a collapsed one, at a fraction of the peak load;
where does r2c's response end?" For every case with shear in a tools/verify.py run: how the
curve ends by the shape check's own words (tools/compare.py: ends falling, standing still,
at peak), the last stage's load as a share of the peak, and the number of stages, for
Response (the fixture) and for r2c (the run's record).

History. Until 2026-11-21 r2c ended a shear response by rules of its own and never found a
collapsed last stage (this tool then showed that its collapse rule discarded nothing). Since
step 4 of increment S r2c follows Response's own stage control (docs/kernel.md, "Response's
own load stage control"): a stage that does not converge is kept when its load is not above
the largest so far, and the response ends by Response's end tests.

Nothing is solved here.
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


def last_share(rec) -> float:
    """The last stage's load over the largest, on the bottom control chart."""
    c = compare._curve(rec, compare.control_keys(rec)[-1])
    y = abs(c[:, 1])
    return float(y[-1] / y.max()) if y.max() > 0 else 0.0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verify_out", help="folder of a tools/verify.py run")
    ap.add_argument("--only", nargs="*", help="case names")
    ap.add_argument("--fixtures", default=str(ROOT / "tests" / "oracle"))
    a = ap.parse_args(argv)
    out = Path(a.verify_out)
    results = json.loads((out / "results.json").read_text())
    same = total = 0
    for name in sorted(results):
        r = results[name]
        if a.only and name not in a.only:
            continue
        if "control" not in r or float(r["ref"]["increment"].split(",")[2]) == 0.0:
            continue
        c = r["control"][-1]
        fx = Path(a.fixtures) / f"{name}.r2x.txt"
        ref = record.read(fx if fx.exists() else fx.parent / "parked" / fx.name)
        sub = record.read(out / f"{name}.r2x.txt")
        e_ref, e_sub = c["shape_ref"][-1], c["shape_sub"][-1]
        total += 1
        same += e_ref == e_sub
        print(f"{name}: Response {e_ref}, last stage at {100 * last_share(ref):.0f} % of the "
              f"peak, {ref.header['stage-count']} stages; r2c {e_sub}, at "
              f"{100 * last_share(sub):.0f} %, {sub.header['stage-count']} stages"
              + ("" if e_ref == e_sub else "   <-- differs"))
    print(f"{same} of {total} shear responses end the same way")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
