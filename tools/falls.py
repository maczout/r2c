#!/usr/bin/env python3
"""How deep is each fall of load before the peak, in Response's curve and in r2c's?

    python tools/falls.py VERIFY_OUT [--only NAME ...] [--all]

Answers the question the independent assessment of the end-of-phase review raised
(docs/review/independent/unsettled-tries.md): where the shape check says one curve has a
fall of load before its peak and the other has not, is the fall missing, or is it there
and just under what the measure counts? The shape check (tools/compare.py, shape) counts
a fall where the load drops below the largest so far by 2 % of Response's peak (FALL).
For each case of a tools/verify.py run this lists, for Response (the fixture) and for r2c
(the run's record), every drop below the running top before the peak that is deeper than
0.5 % of Response's peak: the stage where it starts and its depth in % of that peak, with
"counted" where the measure reads it as a fall. Without --all only the cases whose shapes
differ are listed. Nothing is assessed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
from r2c import record  # noqa: E402

LEAST = 0.005


def drops(c, pk: float) -> list[tuple[int, float]]:
    """(stage, depth as a share of pk) of each drop below the running top before the peak."""
    y = np.abs(c[:, 1]) / pk
    ip = int(np.argmax(y))
    out, i = [], 1
    while i < ip:
        top = y[:i].max()
        if top - y[i] > LEAST:
            j = i
            while j + 1 < ip and y[j + 1] < top:
                j += 1
            out.append((i, float(top - y[i:j + 1].min())))
            i = j + 1
        else:
            i += 1
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verify_out")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--fixtures", default=str(ROOT / "tests" / "oracle"))
    a = ap.parse_args(argv)
    results = json.loads((Path(a.verify_out) / "results.json").read_text())
    for name in sorted(results):
        res = results[name]
        if not res.get("control") or (a.only and name not in a.only):
            continue
        c = res["control"][-1]
        if not (a.all or a.only) and c.get("shape_ref") == c.get("shape_sub"):
            continue
        ref = record.read(Path(a.fixtures) / f"{name}.r2x.txt")
        sub = record.read(Path(a.verify_out) / f"{name}.r2x.txt")
        key = cmp.control_keys(ref)[-1]
        pk = float(np.max(np.abs(cmp._curve(ref, key)[:, 1]))) or 1.0
        print(f"{name}: shape Response {', '.join(c.get('shape_ref', []))} | r2c "
              f"{', '.join(c.get('shape_sub', []))}")
        for who, rec in (("Response", ref), ("r2c", sub)):
            ds = drops(cmp._curve(rec, key), pk)
            print(f"  {who:8s} " + ("; ".join(
                f"stage {i}: {100 * d:.2f} %" + (" (counted)" if d > cmp.FALL else "")
                for i, d in ds) or "no drop before the peak"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
