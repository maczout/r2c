"""Where do r2c's tries first part from Response's own?

    python tools/tries.py RTRACE_LOG RECORD [--input FILE] [--set NAME=VALUE ...]
                          [--context N] [--all]

Answers "up to which try does r2c's load stage control do what Response's did, and what
is the first thing it does differently": the check a rule of the stage control is held
to before it goes in (owner, 2026-11-24, D64). RTRACE_LOG is a log of tools/rtrace.py
(Response's tries on the case, read from the running program); RECORD is the case's
fixture or capture, from which r2c is run as tools/trace.py runs it.

The two lists of tries are set side by side in order. Two tries agree when they are at
the same control variable and target (within a thousandth of the target, or 1e-4 in its
unit) and end the same way: kept, or not kept (a failed try and a dropped stage put in
between both count as not kept; why a try failed is printed and not compared). Printed:
how many tries agree before the first that does not, how many stages each program had
kept by then, and the tries around that place (--context, 4 if not given; --all for the
whole of both lists). Nothing is assessed: there is no target on tries.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import diagnose  # noqa: E402
import rtrace  # noqa: E402
from r2c import record  # noqa: E402


def response_tries(log):
    out = []
    for t in rtrace.read(log):
        p = t["passes"][-1]
        what = t["what"] or "unfinished"
        out.append(dict(n=p["n"], mode=p["mode"], target=p["target"], mult=p["mult"],
                        kept=what == "kept", lam=p["lam"], err=p["err"],
                        passes=len(t["passes"]),
                        what="kept" if what == "kept" else
                        ("dropped: " if what == "dropped" else "") + rtrace.why(t)))
    return out


def r2c_tries(rec, input_path, sets):
    ref = record.read(rec)
    su = diagnose._setup(ref, input_path)
    drv = su.driver()
    for item in sets:
        name, _, val = item.partition("=")
        obj = su.analysis if hasattr(type(su.analysis), name) else drv
        if not hasattr(obj, name):
            raise SystemExit(f"nothing called {name} on the analysis or the driver")
        setattr(obj, name, type(getattr(obj, name))(float(val)))
    drv.trace = []
    drv.run(400)
    out = []
    for t in drv.trace:
        k = 1e6 if t["mode"] == "phi" else 1e3
        what = t.get("what") or ("kept" if t["kept"] else "refused" if t["solved"]
                                 else "no state")
        out.append(dict(n=t["n"], mode=t["mode"], target=t["target"] * k, mult=t["mult"],
                        kept=bool(t["kept"]), lam=t["lam"], err=t["perr"],
                        passes=t["passes"] or 0, what=what))
    return out


def same(a, b) -> bool:
    return (a["mode"] == b["mode"] and a["kept"] == b["kept"]
            and abs(a["target"] - b["target"]) <= max(1e-3 * abs(b["target"]), 1e-4))


def cell(t) -> str:
    if t is None:
        return " " * 62
    lam = "" if t["lam"] is None else f"{t['lam']:8.2f}"
    err = "" if t["err"] is None else (f"{100 * t['err']:6.2f}" if t["err"] < 10 else "   big")
    return (f"{t['n']:3d} {t['mode']:>3} {t['target']:9.4f} {t['mult']:6.3f} "
            f"{t['what']:<18.18} {lam:>8} {err:>6} {t['passes']:2d}")


def first_difference(mine, theirs) -> int:
    i = 0
    while i < min(len(mine), len(theirs)) and same(mine[i], theirs[i]):
        i += 1
    return i


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log")
    ap.add_argument("record")
    ap.add_argument("--input")
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    ap.add_argument("--context", type=int, default=4)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    theirs = response_tries(a.log)
    mine = r2c_tries(a.record, a.input, a.set)
    i = first_difference(mine, theirs)
    whole = i == len(mine) == len(theirs)
    kept_r = sum(t["kept"] for t in theirs[:i])
    print(f"{Path(a.log).stem}: {i} tries agree"
          + (", all of them" if whole else
             f" of Response's {len(theirs)} and r2c's {len(mine)}; {kept_r} stages kept by "
             f"then, of Response's {sum(t['kept'] for t in theirs)} and r2c's "
             f"{sum(t['kept'] for t in mine)}"))
    lo, hi = (0, max(len(mine), len(theirs))) if a.all else \
        (max(i - a.context, 0), min(i + a.context + 1, max(len(mine), len(theirs))))
    head = f"{'stg':>3} {'ctl':>3} {'target':>9} {'mult':>6} {'what':<18} {'load':>8} {'err %':>6} {'ps':>2}"
    print(f"     Response: {head}   r2c: {head}")
    for j in range(lo, hi):
        t = theirs[j] if j < len(theirs) else None
        m = mine[j] if j < len(mine) else None
        mark = "  " if (t and m and same(m, t)) else "<>"
        print(f"{j:4d} {mark}       {cell(t)}        {cell(m)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
