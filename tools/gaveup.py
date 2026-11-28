#!/usr/bin/env python3
"""On which cases with shear does the measure say Response's solve gave up, and why?

    python tools/gaveup.py REFS SUBS [--traces DIR ...] [--md]

Answers "does the rule that tells a case where Response's solve gives up (tools/compare.py,
carried_on; docs/measures.md, 'The overrides') fire where it should?", for the assessor at
the finish (owner, 2026-11-25: 'the first thing the independent assessor checks'). For
every case with shear whose Response capture is under REFS (NAME.r2x.txt, searched
recursively) and whose other record is under SUBS, it prints each condition of the rule
as measured on the two records, and the verdict:

  last/peak   Response's last stage's load over its peak load (the rule needs >= 0.8)
  off         how far the other curve passes from Response's last stage, as a fraction
              (the rule needs it within the target on the curves)
  beyond      the other record's stages after that point
  ends apart  whether the other record's last stage is somewhere else than Response's
  verdict     "cut at P of N" where all hold (the case is compared up to Response's
              last stage), else the first condition that fails; "not cut: trace ..."
              where the two records' conditions hold and a trace of Response does not
              show a numerical give-up (owner, 2026-11-27; tools/traceend.py)
  carried     where r2c itself says its copy of Response's solve gave up and its own
              carried on (the stage number, from the verify results beside the record;
              blank: it did not), which is r2c's word and not the measure's
  trace       with --traces: how Response's own stage control ended, read from the
              running program (tools/rtrace.py logs, NAME.log): the tries after its last
              kept stage, as letters (F a failed try, D a stage dropped), or "none"

Nothing is decided here: it sets the records side by side.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
import report  # noqa: E402
from r2c import record  # noqa: E402


def conditions(ref, sub) -> dict | None:
    """Each condition of compare.carried_on, as measured; None without shear."""
    if report.group(ref.header) != "shear":
        return None
    keys = [k for k in cmp.control_keys(ref) if k in cmp.control_keys(sub)]
    if not keys:
        return None
    key, limit = keys[-1], cmp.same_place_limit(ref)
    a, b = cmp._curve(ref, key), cmp._curve(sub, key)
    if len(a) < 2 or len(b) < 2:
        return None
    pk, xs = float(np.max(np.abs(a[:, 1]))), float(np.max(np.abs(a[:, 0])))
    d, pos = cmp.project(a[-1:], b, xs, pk)
    apart = float(np.hypot((b[-1, 0] - a[-1, 0]) / xs, (b[-1, 1] - a[-1, 1]) / pk))
    out = {"stages": (len(a), len(b)), "ratio": abs(a[-1, 1]) / pk, "off": float(d[0]),
           "beyond": len(b) - 1 - float(pos[0]), "apart": apart, "limit": limit,
           "upto": cmp.carried_on(ref, sub, key, limit)}
    if out["ratio"] < cmp.GAVE_UP_LOAD:
        out["why"] = "load has fallen"
    elif out["off"] > limit:
        out["why"] = "curves apart there"
    elif out["beyond"] <= 1e-9:
        out["why"] = "nothing beyond"
    elif out["apart"] <= max(limit, cmp.FLOOR_DIGITS * float(np.hypot(
            *(r / s for r, s in zip(cmp.resolution(ref.control(key)), (xs, pk)))))):
        out["why"] = "ends at the same place"
    elif out["upto"] is None:
        # all the conditions on the two records hold; the trace does not show a give-up
        out["why"] = f"not cut: trace {cmp.trace_end(ref) or 'none'}"
    else:
        out["why"] = f"cut at {out['upto']:.1f} of {len(b)}"
    return out


def trace_end(log: Path) -> str:
    """The tries after Response's last kept stage, from a tools/rtrace.py log."""
    marks = [ln[0] for ln in log.read_text().splitlines() if ln[:2] in ("A ", "F ", "D ")]
    tail = []
    for m in reversed(marks):
        if m == "A":
            break
        tail.append(m)
    return "".join(reversed(tail)) or "none"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("refs")
    ap.add_argument("subs")
    ap.add_argument("--traces", nargs="*", default=[])
    ap.add_argument("--md", action="store_true", help="a markdown table")
    a = ap.parse_args(argv)
    subs = {p.name: p for p in Path(a.subs).rglob("*.r2x.txt")}
    rows = []
    for rp in sorted(Path(a.refs).rglob("*.r2x.txt"), key=lambda p: p.name):
        if rp.name not in subs or "parked" in rp.parts:
            continue
        c = conditions(record.read(rp), record.read(subs[rp.name]))
        if c is None:
            continue
        name = rp.name[: -len(".r2x.txt")]
        carried = ""
        for j in (subs[rp.name].with_name(name + ".json"), subs[rp.name].parent / "results.json"):
            if j.exists():
                res = json.loads(j.read_text())
                res = res.get(name, res)
                if res.get("carried_from") is not None:
                    carried = str(res["carried_from"])
                break
        tr = ""
        for d in a.traces:
            if (Path(d) / f"{name}.log").exists():
                tr = trace_end(Path(d) / f"{name}.log")
        rows.append([name, f"{c['stages'][0]} / {c['stages'][1]}", f"{c['ratio']:.3f}",
                     f"{c['off']:.3f}", f"{c['beyond']:.1f}",
                     "yes" if c["apart"] > c["limit"] else "no", c["why"], carried, tr])
    head = ["case", "stages (Response / other)", "last/peak", "off", "beyond", "ends apart",
            "verdict", "carried", "trace"]
    if a.md:
        print("| " + " | ".join(head) + " |\n|" + "---|" * len(head))
        for r in rows:
            print("| " + " | ".join(r) + " |")
    else:
        w = [max(len(x[i]) for x in rows + [head]) for i in range(len(head))]
        for r in [head] + rows:
            print("  ".join(x.ljust(w[i]) for i, x in enumerate(r)))
    n = sum(r[6].startswith("cut") for r in rows)
    print(f"\n{len(rows)} cases with shear; the rule fires on {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
