#!/usr/bin/env python3
"""How did Response's own stage control end each response with shear: a give-up of its
solve, a refusal of a state whose web is crushing, or an end of its own accord?

    python tools/traceend.py make REFS OUT --inputs FOLDERS --response-dir DIR
                             [--only NAMES] [--have DIRS] [--jobs 6]
    python tools/traceend.py read REFS TRACE_DIRS... [--write FILE] [--list]

Answers the question the owner's override turns on since 2026-11-27 (docs/brief.md: "r2c
carries on only where a trace of Response confirms a numerical give-up"; docs/measures.md,
"The overrides"). A trace is a log of tools/rtrace.py: Response's tries, read from the
running program.

make traces every case with shear under REFS (NAME.r2x.txt) whose last stage carries at
least 0.8 of its peak load and that has no log yet in OUT or in the --have folders, several
at a time, one Wine prefix each. OUT is outside the repository: the logs are Response's own
numbers.

read gives each traced case its ending, from the tries after the last stage Response kept:

  gave up          the tries ran out (down to the smallest step) and every one of them
                   failed numerically: the solve of the global strains gave up ("no
                   solve"), or the stage had not settled after 16 passes
  refused          the tries ran out and one of them at least was a solved state refused
                   on its state code 3, the web crushing
  not told apart   the tries ran out with a solved state refused for another reason (a
                   stirrup past rupture, or one the trace does not name): neither of
                   the two above for certain
  own accord       no try failed after the last stage kept, and the trace has as many
                   stages as the capture (the first stage is not a try): Response ended
                   by its own tests
  not shown        the trace stops before the capture's last stage, or has another ending

--write puts {case: ending} into FILE (tests/oracle/trace-ends.json for the development
set; a file in the archive for a held-out set, whose cases are not named in the
repository). --list prints the cases; without it only the counts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
import report  # noqa: E402
import rtrace  # noqa: E402
import verify  # noqa: E402
from r2c import record  # noqa: E402

GAVE_UP, REFUSED, UNTOLD, OWN, NOT_SHOWN = ("gave up", "refused", "not told apart",
                                             "own accord", "not shown")
RAN_OUT = 0.01      # the step multiplier of the last try when the tries have run out


def ending(log: Path, stage_count: int) -> str:
    """The ending a trace shows (the module's docstring)."""
    tries = rtrace.read(log)
    if not tries or tries[-1]["what"] is None:
        return NOT_SHOWN
    tail = []
    for t in reversed(tries):
        if t["what"] == "kept":
            break
        tail.append(t)
    kept = sum(t["what"] == "kept" for t in tries)
    if not tail:
        return OWN if kept + 1 == stage_count else NOT_SHOWN
    failed = [t for t in tail if t["what"] == "failed"]
    if kept + 1 != stage_count or not failed or tail[0]["what"] != "failed" \
            or tail[0]["passes"][-1]["mult"] >= RAN_OUT:
        return NOT_SHOWN
    whys = [rtrace.why(t) for t in tail]
    if all(w.startswith("no solve") or w == "16 passes above" for w in whys):
        return GAVE_UP
    if any(w.startswith("code 3") for w in whys):
        return REFUSED
    return UNTOLD


def shear_cases(refs: Path):
    """(name, path, header, last stage's load over the peak) of each case with shear."""
    for p in sorted(Path(refs).rglob("*.r2x.txt"), key=lambda q: q.name):
        if "parked" in p.parts:
            continue
        r = record.read(p)
        if report.group(r.header) != "shear":
            continue
        a = cmp._curve(r, cmp.control_keys(r)[-1])
        pk = float(np.max(np.abs(a[:, 1]))) if len(a) else 0.0
        yield p.name[: -len(".r2x.txt")], p, r.header, (abs(a[-1, 1]) / pk if pk > 0 else 0.0)


def make(a) -> int:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    have = {p.stem for d in [out, *a.have] for p in Path(d).glob("*.log")}
    todo = []
    for name, p, h, ratio in shear_cases(a.refs):
        if a.only and name not in a.only or name in have or ratio < cmp.GAVE_UP_LOAD:
            continue
        inp = verify.find_input(h["input-name"], h.get("input-sha256"), a.inputs)
        if inp is None:
            print(f"{name}: input not found")
            continue
        todo.append((name, p, inp))
    slots = list(range(a.jobs))

    def one(job):
        name, p, inp = job
        k = slots.pop()
        try:
            cmd = [sys.executable, str(Path(__file__).with_name("rtrace.py")), str(p),
                   "--input", str(inp), "--response-dir", a.response_dir,
                   "--out", str(out / f"{name}.log"),
                   "--prefix", str(Path.home() / ".cache" / "r2x" / f"prefix-scope-{k}")]
            pr = subprocess.run(cmd, capture_output=True, text=True)
            return name, pr.returncode, (pr.stdout or pr.stderr).strip().splitlines()[-1:]
        finally:
            slots.append(k)

    with ThreadPoolExecutor(a.jobs) as ex:
        for name, rc, last in ex.map(one, todo):
            print(name, rc, *last, flush=True)
    print("done")
    return 0


def read(a) -> int:
    ends = {}
    for name, _p, h, _ratio in shear_cases(a.refs):
        for d in a.traces:
            log = Path(d) / f"{name}.log"
            if log.exists():
                e = ending(log, int(h.get("stage-count", "0")))
                if name not in ends or ends[name] == NOT_SHOWN:
                    ends[name] = e
    for kind in (GAVE_UP, REFUSED, UNTOLD, OWN, NOT_SHOWN):
        names = sorted(n for n, e in ends.items() if e == kind)
        print(f"{kind}: {len(names)}" + (("  " + " ".join(names)) if a.list and names else ""))
    if a.write:
        Path(a.write).write_text(json.dumps(dict(sorted(ends.items())), indent=1) + "\n")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("refs")
    m.add_argument("out")
    m.add_argument("--inputs", nargs="+", required=True)
    m.add_argument("--response-dir", required=True)
    m.add_argument("--only", nargs="*", default=[])
    m.add_argument("--have", nargs="*", default=[])
    m.add_argument("--jobs", type=int, default=6)
    r = sub.add_parser("read")
    r.add_argument("refs")
    r.add_argument("traces", nargs="+")
    r.add_argument("--write")
    r.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    return make(a) if a.cmd == "make" else read(a)


if __name__ == "__main__":
    raise SystemExit(main())
