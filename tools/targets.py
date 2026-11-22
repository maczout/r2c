#!/usr/bin/env python3
"""Which cases are inside the increment's target: peak, rising branch and shape?

    python tools/targets.py VERIFY_OUT [--only NAME ...] [--new] [--outside] [--counts]

Answers the question a development increment asks of a verify run (the owner's briefs for
increments C and S): which cases are inside target on the peak, the rising branch and the
shape of the curve, the three checks that are chased, with the post-peak and the worst view
beside them, which are reported. The checks, their values and their limits are
tools/report.py's own (its assess function and docs/acceptance.md); nothing is measured
here. A case r2c failed on or refused is listed with r2c's words.

--new lists only the cases of increment S (tools/scope_cases.py); --outside only the cases
outside on one of the three, or failed.

--counts answers "how many cases are inside, check by check?": for each of tools/report.py's
checks (peak, rising branch, shape, post-peak, views) the number of cases not outside target
and the names of those outside. It is the progress table of docs/summary.md. A case on which
a check cannot be made (no curve after the peak, no load at all) counts as inside on it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import report  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CHASED = ("peak", "curve", "shape")


def row(name: str, res: dict, acc: dict) -> tuple[bool, str]:
    if "failed" in res or "skipped" in res:
        return False, f"{name}: r2c: {res.get('failed') or res.get('skipped')}"
    checks = report.assess(res, acc)
    ok = all(checks[k][2] is not False for k in CHASED if k in checks)
    c = res["control"][-1]
    parts = [f"peak {checks['peak'][0]:+.2f} %"]
    if "curve" in checks:
        parts.append(f"rising {checks['curve'][0]:.2f} %")
    if "shape" in checks:
        parts.append("shape same" if checks["shape"][0] else
                     "shape DIFFERENT (" + ", ".join(c["shape_ref"]) + " | "
                     + ", ".join(c["shape_sub"]) + ")")
    if "post_peak" in checks:
        parts.append(f"post-peak {checks['post_peak'][0]:.1f} %")
    if "views" in checks:
        parts.append(f"views {checks['views'][0]:.0f} %")
    out = [k for k in CHASED if k in checks and checks[k][2] is False]
    flag = "inside " if ok else "OUTSIDE (" + ", ".join(report.NAMES.get(k, k) for k in out) + ")"
    return ok, f"{name}: {flag}: " + "; ".join(parts)


def counts(names, results: dict, acc: dict) -> int:
    """Per check: how many of the cases are not outside target, and which are outside."""
    failed = [n for n in names if "control" not in results[n]]
    for n in failed:
        print(f"{n}: r2c: {results[n].get('failed') or results[n].get('skipped')}")
    ran = [n for n in names if n not in failed]
    checks = {n: report.assess(results[n], acc) for n in ran}
    for k in ("peak", "curve", "shape", "post_peak", "views"):
        out = [n for n in ran if k in checks[n] and checks[n][k][2] is False]
        print(f"{report.NAMES.get(k, k)}: {len(ran) - len(out)} of {len(names)} inside"
              + (f"; outside: {', '.join(out)}" if out else ""))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verify_out", help="folder of a tools/verify.py run")
    ap.add_argument("--only", nargs="*", help="case names")
    ap.add_argument("--new", action="store_true", help="only the cases of increment S")
    ap.add_argument("--outside", action="store_true", help="only cases outside, or failed")
    ap.add_argument("--counts", action="store_true", help="cases inside, check by check")
    a = ap.parse_args(argv)
    results = json.loads((Path(a.verify_out) / "results.json").read_text())
    acc = report.read_acceptance(ROOT / "docs" / "acceptance.md")
    names = sorted(results)
    if a.only:
        names = [n for n in names if n in a.only]
    if a.new:
        import scope_cases
        new = {c["name"] for c in scope_cases.CASES}
        names = [n for n in names if n in new]
    if a.counts:
        return counts(names, results, acc)
    inside = 0
    for n in names:
        ok, text = row(n, results[n], acc)
        inside += ok
        if not (a.outside and ok):
            print(text)
    print(f"{inside} of {len(names)} inside on peak, rising branch and shape")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
