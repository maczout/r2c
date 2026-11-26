#!/usr/bin/env python3
"""Where does r2c's section stiffness first differ from the one Response's solve steps on?

    python tools/stiff.py RTRACE_LOG RECORD [--input FILE] [--tol 0.02] [--context N]
                          [--set NAME=VALUE ...]

Answers "at which step of which try does the 3 x 3 stiffness (or the unbalanced load) that
r2c's copy of Response's solve works with stop being Response's, and in which term": the
question the notes on Response's solve giving up leave open (docs/kernel.md, "What the
running program shows"). RTRACE_LOG is a log of `tools/rtrace.py --steps --matrix`
(Response's own stiffness and right-hand side at every step of its solve, read from the
running program); RECORD is the case's fixture, from which r2c is run with its copy of
Response's solve on (`Shear.own_solve`) and made to print the same at every step.

r2c's steps are dealt out to Response's tries by the control value they are at, and to
passes by r2c's own count; step is set beside step. A term differs when it is off by more than
--tol of the scale of its row and column (the root of the product of the two diagonal
terms); the right-hand side is printed and not tested (near balance it is all noise). Printed: the first tries
(--context of them) in which a step's stiffness differs or a pass has another number of
steps, with the terms that differ, and how many tries agree throughout. Nothing is assessed.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import diagnose  # noqa: E402
import rtrace  # noqa: E402
from r2c import record  # noqa: E402

NAMES = ("N", "M", "V")
BY = ("e0", "phi", "gam")


MODE = {"e0": 0, "phi": 1, "gam": 2}


def response_tries(log):
    """Response's tries: for each, where it is, its control variable and raw target, and
    its passes as lists of steps."""
    out = []
    for i, t in enumerate(rtrace.read(log)):
        passes = []
        for p in t["passes"]:
            steps = [dict(k=np.array(s["matrix"]["k"]).reshape(3, 3),
                          rhs=np.array(s["matrix"]["rhs"]), after=s["e"])
                     for s in p["steps"] if s.get("matrix")]
            passes.append(steps)
        p = t["passes"][-1]
        first = next((s for q in passes for s in q), None)
        out.append(dict(where=f"try {i}, stage {p['n']}, {p['mode']} {p['target']:.4f}",
                        ci=MODE[p["mode"]], raw=first["after"][MODE[p["mode"]]] if first else None,
                        passes=passes, what=t["what"]))
    return out


def r2c_steps(rec, inp, sets):
    """r2c's steps with its copy of Response's solve on, in order; each with the number of
    passes finished before it."""
    ref = record.read(rec)
    su = diagnose._setup(ref, inp)
    drv = su.driver()
    drv.own_solve, drv.debug = True, True
    for item in sets:
        name, _, val = item.partition("=")
        obj = su.analysis if hasattr(type(su.analysis), name) else drv
        setattr(obj, name, type(getattr(obj, name))(float(val)))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            drv.run(400)
        except Exception as e:  # noqa: BLE001 - the steps made so far are what is wanted
            print(f"stopped: {e}")
    out, done = [], 0
    for ln in buf.getvalue().splitlines():
        m = re.match(r"\s+K (.*) \| rhs (.*) \| at e0=(\S+) phi=(\S+) gam=(\S+)", ln)
        if m:
            out.append(dict(k=np.array(m[1].split(), dtype=float).reshape(3, 3),
                            rhs=np.array(m[2].split(), dtype=float),
                            at=[float(m[3]), float(m[4]), float(m[5])], done=done))
        elif re.match(r"\s+pass \d+:", ln):
            done += 1
    return out


def pair(rs, cs):
    """r2c's steps dealt out to Response's tries: a try takes the steps that follow at its
    own control value. Yields (try, [r2c's passes as lists of steps])."""
    j = 0
    for t in rs:
        mine = []
        if t["raw"] is not None:
            tol = 5e-4 * abs(t["raw"]) + 5e-7
            # skip r2c's tries Response did not make, a few steps at most
            k = j
            while k < len(cs) and k - j < 60 and abs(cs[k]["at"][t["ci"]] - t["raw"]) > tol:
                k += 1
            if k < len(cs) and k - j < 60:
                j = k
                while j < len(cs) and abs(cs[j]["at"][t["ci"]] - t["raw"]) <= tol:
                    mine.append(cs[j])
                    j += 1
        passes = []
        for s in mine:
            n = s["done"] - mine[0]["done"]
            while len(passes) <= n:
                passes.append([])
            passes[n].append(s)
        yield t, passes


def differs(a, b, tol):
    d = np.sqrt(np.abs(np.diag(a["k"])))
    scale = np.outer(d, d)
    bad = np.abs(a["k"] - b["k"]) > tol * scale
    return bad, np.zeros(3, dtype=bool)


def line(s):
    return (" ".join(f"{v:11.4g}" for v in s["k"].ravel()) + " | "
            + " ".join(f"{v:10.4g}" for v in s["rhs"]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log")
    ap.add_argument("record")
    ap.add_argument("--input")
    ap.add_argument("--tol", type=float, default=0.02)
    ap.add_argument("--context", type=int, default=2)
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    a = ap.parse_args(argv)
    rs, cs = response_tries(a.log), r2c_steps(a.record, a.input, a.set)
    print(f"{Path(a.record).name}: terms dN/de0 dN/dphi dN/dgam, dM/..., dV/... | unbalanced "
          "N M V (N, N m; per strain, per 1/m; Response's sign of curvature)")
    agree = shown = 0
    for t, passes in pair(rs, cs):
        note = []
        for n, (rp, cp) in enumerate(zip(t["passes"], passes)):
            for i, (r, c) in enumerate(zip(rp, cp)):
                bad, _ = differs(r, c, a.tol)
                if bad.any():
                    mark = [f"d{NAMES[x]}/d{BY[y]}" for x in range(3) for y in range(3)
                            if bad[x, y]]
                    note.append((n, i, r, c, mark))
                    break
            else:
                if len(rp) != len(cp):
                    note.append((n, None, len(rp), len(cp), None))
                continue
            break
        if not passes:
            note.append((0, None, sum(len(q) for q in t["passes"]), 0, None))
        if not note:
            agree += 1
            continue
        if shown >= a.context:
            continue
        shown += 1
        print(f"{t['where']} ({t['what']}; Response {len(t['passes'])} passes, r2c "
              f"{len(passes)}); {agree} tries before it agree throughout")
        for n, i, r, c, mark in note[:4]:
            if mark is None:
                print(f"  pass {n + 1}: Response {r} steps, r2c {c}")
            else:
                print(f"  pass {n + 1}, step {i + 1} DIFFERS: " + ", ".join(mark))
                print(f"    Response {line(r)}")
                print(f"    r2c      {line(c)}")
                print("    r2c at   " + " ".join(f"{v:.6g}" for v in c["at"]))
    print(f"{agree} of Response's {len(rs)} tries agree throughout (every step's stiffness "
          f"within {a.tol:g}, the same number of steps in every pass)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
