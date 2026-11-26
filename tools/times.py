#!/usr/bin/env python3
"""How long does r2c take on a case, in one verify run and in another?

    python tools/times.py RUN_BEFORE RUN_AFTER

Answers "what did a kernel change do to r2c's run time per case?" (owner, 2026-11-25): for
the cases without shear and with it, the number of cases, the median, the mean and the
longest wall-clock time of r2c on one case in each run, and the sum; then the five cases
that take longest in the second run. The times are the ones tools/verify.py records
("seconds"): one process a case, on the machine and with the number of jobs of that run,
so two runs compare only if they were made the same way. Development runs only.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import report  # noqa: E402


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2 or any("heldout" in a or "finish" in a for a in args):
        raise SystemExit(__doc__)
    runs = [json.loads((Path(a) / "results.json").read_text()) for a in args]
    names = [n for n in runs[0] if all("seconds" in r.get(n, {}) for r in runs)]
    print(f"{len(names)} cases timed in both runs; seconds of r2c on one case")
    print("| Cases | Run | Median | Mean | Longest | Sum |\n|---|---|---:|---:|---:|---:|")
    for g, title in (("flexure", "without shear"), ("shear", "with shear")):
        mine = [n for n in names if report.group(runs[0][n]["ref"]) == g]
        for label, r in zip(("before", "after"), runs):
            t = [r[n]["seconds"] for n in mine]
            print(f"| {len(mine)} {title} | {label} | {st.median(t):.1f} | {st.mean(t):.1f} | "
                  f"{max(t):.0f} | {sum(t):.0f} |")
    slow = sorted(names, key=lambda n: -runs[1][n]["seconds"])[:5]
    print("longest in the second run: " + "; ".join(
        f"{n} {runs[0][n]['seconds']:.0f} -> {runs[1][n]['seconds']:.0f} s" for n in slow))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
