#!/usr/bin/env python3
"""What would a switch do, on some development cases, without editing the source?

    python tools/trial.py OUT --inputs DIR [DIR ...] --set Class.name=VALUE [...]
                          --only NAME [NAME ...] [--jobs N]

Answers "is this worth turning on (or off)?" before a full run: it sets attributes of the
kernel's classes (Analysis, Flexure, Shear) for this process alone, runs the named
development cases as tools/verify.py does, and writes each case's record and comparison
into OUT (outside the repository), where tools/byprio.py and tools/changes.py read them
beside a full run's. A switch is given its value in the type it has (1 or 0 for a bool).
Where the name is a method, the method is replaced by one that returns VALUE whatever it
is asked: `Shear.relax=1` runs without r2c's own damping of the profile update under
shear alone. Development cases only.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import verify  # noqa: E402
from r2c import shear, solver  # noqa: E402

CLASSES = {"Analysis": solver.Analysis, "Flexure": solver.Flexure, "Shear": shear.Shear}


def apply(sets) -> None:
    for item in sets:
        where, _, value = item.partition("=")
        cls, _, name = where.partition(".")
        if cls not in CLASSES or not hasattr(CLASSES[cls], name):
            raise SystemExit(f"{where}: no such attribute (classes: {', '.join(CLASSES)})")
        cur = getattr(CLASSES[cls], name)
        if callable(cur):
            const = float(value)
            setattr(CLASSES[cls], name, lambda self, *a, _c=const, **k: _c)
        elif isinstance(cur, bool):
            setattr(CLASSES[cls], name, value not in ("0", "False", "false", ""))
        else:
            setattr(CLASSES[cls], name, type(cur)(value))


def one(args):
    sets, job = args
    apply(sets)
    return verify.one(job)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out")
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--set", nargs="+", default=[], dest="sets")
    ap.add_argument("--only", nargs="+", required=True)
    ap.add_argument("--jobs", type=int, default=1)
    a = ap.parse_args(argv)
    out = Path(a.out).resolve()
    if ROOT in out.parents or out == ROOT or "heldout" in str(out) or "finish" in str(out):
        raise SystemExit("OUT belongs outside the repository and outside the held-out archives")
    apply(a.sets)       # refuses a wrong name before anything runs
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(a.sets, (str(ROOT / "tests" / "oracle" / f"{n}.r2x.txt"), a.inputs, str(out)))
            for n in a.only]
    with ProcessPoolExecutor(max_workers=max(a.jobs, 1)) as ex:
        results = dict(ex.map(one, jobs))
    (out / "results.json").write_text(json.dumps(results, indent=1))
    for n, r in results.items():
        print(f"{n}: " + (r.get("failed") or r.get("skipped") or f"{r.get('seconds')} s"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
