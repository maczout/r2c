#!/usr/bin/env python3
"""Which development cases change side on a priority between verify runs?

    python tools/byprio.py RUN_A RUN_B [RUN_C ...] [--only NAME ...]

Answers "what did a kernel change do to each case, by the brief's priorities?": for every
case with shear whose inside/outside on any priority differs between the runs, one line
with a letter per priority and run (i inside, o outside, - no such check), whether the
case is compared up to Response's last stage (u, the owner's override) and where the
override took over (the stage count; 0: the whole response is r2c's own solve's). Then
the totals of each run. Development runs only (tools/verify.py output folders); never
anything of the held-out sets.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import heldout  # noqa: E402
import report  # noqa: E402


def flags(res, acc, g):
    chk = report.assess(res, acc)
    out = ""
    for p, names in heldout.PRIORITY[g].items():
        oks = [chk[n][2] for n in names if n in chk and chk[n][2] is not None]
        out += "-" if not oks else "i" if all(oks) else "o"
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args(argv)
    if any("heldout" in r or "finish" in r for r in a.runs):
        raise SystemExit("development runs only")
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    runs = [json.loads((Path(r) / "results.json").read_text()) for r in a.runs]
    tot = [{} for _ in runs]
    for name in sorted(runs[0]):
        if not all(name in r and "control" in r[name] for r in runs):
            continue
        g = report.group(runs[0][name]["ref"])
        fl = [flags(r[name], acc, g) for r in runs]
        for t, f in zip(tot, fl):
            for k, ch in enumerate(f):
                n = t.setdefault((g, k + 1), [0, 0])
                n[0] += ch == "i"
                n[1] += ch != "-"
        if (a.only and name in a.only) or (not a.only and len(set(fl)) > 1):
            cells = [f + ("u" if "upto" in r[name] else " ")
                     + (f"@{r[name]['carried_from']}" if "carried_from" in r[name] else "")
                     for f, r in zip(fl, runs)]
            print(f"{name:32s} " + "  ".join(f"{c:9s}" for c in cells))
    for (g, p) in sorted(tot[0]):
        print(f"{g} priority {p}: " + "  ".join(f"{t[(g, p)][0]} of {t[(g, p)][1]}" for t in tot))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
