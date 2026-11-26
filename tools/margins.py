#!/usr/bin/env python3
"""Which development cases are nearest the target on priority 1, and on what?

    python tools/margins.py RESULTS [--area flexure|shear] [--top N]

Answers "where is the development set inside target only just?": a case that is inside by
a hair says a small difference is there, and a held-out case like it may be outside. For
each case of the area: its largest priority 1 difference among the views (stress-state
views, cases without shear), the peak and the rising branch, as a percentage, largest
first. RESULTS is a verify output on development fixtures or the committed
docs/verification-results.json; never anything of the held-out set.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import dashboard  # noqa: E402
import report  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("results")
    ap.add_argument("--area", choices=("flexure", "shear"), default="flexure")
    ap.add_argument("--top", type=int, default=25)
    a = ap.parse_args(argv)
    if "heldout" in str(Path(a.results).resolve()):
        ap.error("not on the held-out set (CLAUDE.md, the held-out rule)")
    _run, results = dashboard.load_results(Path(a.results))
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    rows = []
    for name, r in results.items():
        if "control" not in r or report.group(r["ref"]) != a.area:
            continue
        chk = report.assess(r, acc)
        worst = [(abs(chk[k][0]), k, "") for k in ("peak", "curve") if k in chk]
        views = [c for c in report.stage_checks(r, acc)
                 if c["tier"] == "views" and c["state"] != "unstable" and c["pct"] is not None]
        if views:
            w = max(views, key=lambda c: c["pct"])
            worst.append((w["pct"], w["view"], w["feature"] or "stage"))
        if worst:
            v, what, where = max(worst)
            rows.append((v, name, what, where))
    for v, name, what, where in sorted(rows, reverse=True)[: a.top]:
        print(f"{v:7.2f} %  {name}: {what}" + (f" at {where}" if where else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
