#!/usr/bin/env python3
"""Does the node store give the batch solve's numbers, bit for bit, on a development case?

    python tools/shadow.py NAME [NAME ...] --inputs DIR [DIR ...] [--calls N] [--jobs N]

Answers "is this speed-up exact?" directly, where tools/same.py answers it on the records.
It runs the case as tools/verify.py does, and at every transverse solve of the nodes
(Analysis.transverse, the node store) also solves the same call the plain way
(Analysis.transverse_batch) and compares every field of every node and its transverse
strain: equal bits, NaN where NaN. It stops at the first call that differs and says
which field. --calls N stops after N calls (the test in tests/test_speed.py uses that).
Twice as slow as a plain run and more. Development cases only.
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import verify  # noqa: E402
from r2c import record, run, solver  # noqa: E402


class Enough(Exception):
    pass


def shadow(name: str, inputs=(), calls: int | None = None) -> tuple[int, str]:
    """(calls compared, what differed or "")."""
    ref = record.read(ROOT / "tests" / "oracle" / f"{name}.r2x.txt")
    src = ref.header["input-name"]
    path = None
    if src.lower() not in verify.BUILT_IN:
        path = verify.find_input(src, ref.header.get("input-sha256"), list(inputs))
        if path is None:
            return 0, f"input {src} not found"
    fast = solver.Analysis.transverse
    count = [0]
    found = [""]

    def both(self, zf, z, ex, g, m, ft, smx, smt, cx, sh=None):
        out, ey = fast(self, zf, z, ex, g, m, ft, smx, smt, cx, sh)
        want, wey = self.transverse_batch(zf, z, ex, g, m, ft, smx, smt, cx, sh)
        count[0] += 1
        pairs = [("ey", ey, wey)] + [(k, getattr(out, k), v) for k, v in want.__dict__.items()]
        for field, a, b in pairs:
            if a.dtype != b.dtype or a.shape != b.shape or a.tobytes() != b.tobytes():
                if not (a.shape == b.shape and np.array_equal(a, b, equal_nan=True)
                        and np.array_equal(np.signbit(a), np.signbit(b))):
                    found[0] = f"call {count[0]}: {field} differs at {len(zf)} nodes"
                    raise Enough
        if calls is not None and count[0] >= calls:
            raise Enough
        return out, ey

    solver.Analysis.transverse = both
    try:
        run.solve(path, **verify.options(ref.header))
    except Enough:
        pass
    finally:
        solver.Analysis.transverse = fast
    return count[0], found[0]


def _one(args):
    return args[0], shadow(*args)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("names", nargs="+")
    ap.add_argument("--inputs", nargs="+", default=[])
    ap.add_argument("--calls", type=int)
    ap.add_argument("--jobs", type=int, default=1)
    a = ap.parse_args(argv)
    bad = 0
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        for name, (n, what) in ex.map(_one, [(nm, a.inputs, a.calls) for nm in a.names]):
            print(f"{name}: {n} calls compared, " + (what or "every one the same"), flush=True)
            bad += bool(what)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
