#!/usr/bin/env python3
"""Where r2c goes past Response's last stage, does its record mark that stage?

    python tools/marks.py REFS SUBS [--list]

Answers the question the owner's requirement of 2026-11-27 raises ("r2c's record marks
the stage where Response would stop, whenever r2c goes past it"): r2c can mark only what
it knows, the stage at which its own copy of Response's stage control gives up; where its
copy does not fail where Response's did, it goes past unknowing. For every case with shear
whose Response capture is under REFS (NAME.r2x.txt, searched recursively) and whose r2c
record is under SUBS, it finds whether r2c goes past Response's last stage, by the
conditions of the measure without the trace (docs/measures.md, "The overrides": Response's
last stage at 0.8 of its peak or more, r2c's curve passing it at the same place, stages
beyond, the two ends apart), and prints, by how a trace of Response shows the case to have
ended (tools/traceend.py):

  marked there      r2c's record has carried-on-stage, and that stage is at the same
                    place as Response's last stage (within the target on the curves)
  marked elsewhere  it has the line, at another place: its copy gave up later or earlier
  not marked        it has no such line: r2c went past without its copy giving up

and how many records say that r2c ended where its copy of Response's stage control
stopped, by the reason given (the
header's "ending"). --list names the cases (on a held-out set: at the finish only).
Nothing is assessed: there is no target on the marks.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
import gaveup  # noqa: E402
from r2c import record  # noqa: E402


def mark(ref, sub) -> str | None:
    """None where r2c does not go past Response's last stage; else which of the three."""
    c = gaveup.conditions(ref, sub)
    if c is None or c["ratio"] < cmp.GAVE_UP_LOAD or c["off"] > c["limit"] \
            or c["beyond"] <= 1e-9 or c["apart"] <= c["limit"]:
        return None
    at = sub.header.get("carried-on-stage")
    if at is None:
        return "not marked"
    key = [k for k in cmp.control_keys(ref) if k in cmp.control_keys(sub)][-1]
    a, b = cmp._curve(ref, key), cmp._curve(sub, key)
    pk, xs = float(np.max(np.abs(a[:, 1]))), float(np.max(np.abs(a[:, 0])))
    d = float(np.hypot((b[int(at), 0] - a[-1, 0]) / xs, (b[int(at), 1] - a[-1, 1]) / pk))
    return "marked there" if d <= c["limit"] else "marked elsewhere"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("refs")
    ap.add_argument("subs")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    subs = {p.name: p for p in Path(a.subs).rglob("*.r2x.txt")}
    past, ends, shear = {}, {}, 0
    for rp in sorted(Path(a.refs).rglob("*.r2x.txt"), key=lambda p: p.name):
        if rp.name not in subs or "parked" in rp.parts:
            continue
        ref, sub = record.read(rp), record.read(subs[rp.name])
        if gaveup.conditions(ref, sub) is None:
            continue
        shear += 1
        name = rp.name[: -len(".r2x.txt")]
        m = mark(ref, sub)
        if m is not None:
            past[name] = (cmp.trace_end(ref) or "no trace", m)
        if "ending" in sub.header:
            ends[name] = sub.header["ending"].split(":", 1)[1].strip()
    print(f"{shear} cases with shear; r2c goes past Response's last stage on {len(past)}")
    for (trace, m), n in sorted(Counter(past.values()).items()):
        names = sorted(k for k, v in past.items() if v == (trace, m))
        print(f"  trace of Response: {trace}; {m}: {n}"
              + ("  " + " ".join(names) if a.list else ""))
    print(f"r2c's record says it ends where its copy of Response's stage control stops on "
          f"{len(ends)}")
    for why, n in sorted(Counter(ends.values()).items()):
        names = sorted(k for k, v in ends.items() if v == why)
        print(f"  {why}: {n}" + ("  " + " ".join(names) if a.list else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
