#!/usr/bin/env python3
"""Which development cases are outside target on a priority, and on which checks?

    python tools/priority.py RESULTS [--priority 1] [--views]

Answers "what stands between the development set and the threshold?": the same tally as
tools/heldout.py makes on the held-out set (its PRIORITY table, tools/report.py's assess),
but case by case, which is allowed here and only here: RESULTS is a verify output on
development fixtures (tests/oracle or tests/oracle/parked) or the committed
docs/verification-results.json. Never point it at anything of the held-out set.

Prints the total by area, then each case outside with the checks it misses and their values.
--views lists, for a missed view check, each view over the target with its worst stage.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import dashboard  # noqa: E402
import heldout  # noqa: E402
import report  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("results")
    ap.add_argument("--priority", default="1")
    ap.add_argument("--views", action="store_true")
    a = ap.parse_args(argv)
    if "heldout" in str(Path(a.results).resolve()):
        ap.error("not on the held-out set (CLAUDE.md, the held-out rule)")
    _run, results = dashboard.load_results(Path(a.results))
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    lim = report.views_limit(acc)
    for g, title in (("flexure", "Moment and axial"), ("shear", "Shear")):
        names = heldout.PRIORITY[g].get(a.priority, ())
        rows, n = [], 0
        for name in sorted(results):
            r = results[name]
            if "ref" not in r:
                if g == "flexure":
                    rows.append(f"  {name}: not run ({r.get('skipped') or r.get('failed')})")
                continue
            if report.group(r["ref"]) != g:
                continue
            checks = report.assess(r, acc)
            mine = {k: checks[k] for k in names if k in checks}
            if not mine:
                continue
            n += 1
            bad = {k: v for k, v in mine.items() if v[2] is False}
            if not bad:
                continue
            cells = []
            for k, (v, _l, _ok) in bad.items():
                if k == "shape":
                    c = r["control"][-1]
                    cells.append(f"shape [{', '.join(c['shape_ref'])}] / "
                                 f"[{', '.join(c['shape_sub'])}]")
                else:
                    cells.append(f"{k} {v:.1f}")
            rows.append(f"  {name}: " + "; ".join(cells))
            if a.views:
                for c in report.stage_checks(r, acc):
                    if c["tier"] in bad and c["state"] == "outside":
                        rows.append(f"      {c['view']} at stage {c['ref_stage']} "
                                    f"({c['feature'] or 'stage'}): "
                                    + ("missing" if c["pct"] is None else f"{c['pct']:.1f} %"))
        out = sum(1 for x in rows if "not run" not in x and not x.startswith("      "))
        print(f"{title}, priority {a.priority}: {n - out} of {n} inside (target {lim:g} %)")
        print("\n".join(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
