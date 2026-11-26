#!/usr/bin/env python3
"""Where does r2c's time go on one development case?

    python tools/proftime.py NAME --inputs DIR [DIR ...] [--top N] [--callers FUNC]

Runs the case as tools/verify.py does, under cProfile, and prints the functions by their
own time and by cumulative time (the top N of each, default 25), then r2c's seconds
without the profiler's overhead are NOT given: time a case with tools/verify.py. With
--callers FUNC also who calls a function and how often. Development cases only.
"""
from __future__ import annotations

import argparse
import cProfile
import pstats
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import verify  # noqa: E402
from r2c import record, run  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("name")
    ap.add_argument("--inputs", nargs="+", default=[])
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--callers")
    ap.add_argument("--dump", help="also write the profile to this file (pstats)")
    a = ap.parse_args(argv)
    ref = record.read(ROOT / "tests" / "oracle" / f"{a.name}.r2x.txt")
    src = ref.header["input-name"]
    path = None
    if src.lower() not in verify.BUILT_IN:
        path = verify.find_input(src, ref.header.get("input-sha256"), a.inputs)
        if path is None:
            raise SystemExit(f"input {src} not found under --inputs")
    pr = cProfile.Profile()
    pr.enable()
    run.solve(path, **verify.options(ref.header))
    pr.disable()
    if a.dump:
        pr.dump_stats(a.dump)
    st = pstats.Stats(pr)
    st.strip_dirs()
    for key in ("tottime", "cumulative"):
        st.sort_stats(key).print_stats(a.top)
    if a.callers:
        st.print_callers(a.callers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
