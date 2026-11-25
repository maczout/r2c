#!/usr/bin/env python3
"""Which detail views are outside target, at which feature stage of which case?

    python tools/viewmisses.py VERIFY_OUT [--only NAME ...] [--shear] [--tier must should could]
                               [--no-endings]

Answers the question an increment on the views asks of a verify run: for each case, at each
feature of Response's curve (cracking, a fall of load, the peak, the last stage), which views
differ by more than the target, and by how much; with the stages matched and their loads, so
that a difference in the state reached can be told from a difference in a view's rule
(tools/diagnose.py states --views puts r2c in Response's own state to settle it).

Nothing is measured here: the differences are tools/compare.py's, as tools/verify.py stored
them, the limit is views_pct of docs/measures.md, and a difference within the printed
precision counts as none, as in tools/report.py. --shear lists only cases with shear;
--tier only views of those tiers of docs/measures.md. The last stage of a shear case is
listed as "not assessed" and left out of the total (owner, 2026-11-22, D40); --no-endings
leaves the last stage out of the listing altogether, for cases without shear too. A view
where Response itself is unstable at the stage (owner, 2026-11-23, D54) is listed with
Response's departure and left out of the total, as tools/report.py leaves it unassessed.
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


def has_shear(res: dict) -> bool:
    return any(float(res["ref"][k].split(",")[2]) != 0.0 for k in ("initial", "increment"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verify_out", help="folder of a tools/verify.py run")
    ap.add_argument("--only", nargs="*", help="case names")
    ap.add_argument("--shear", action="store_true", help="only cases with shear")
    ap.add_argument("--tier", nargs="*", choices=("must", "should", "could"))
    ap.add_argument("--no-endings", action="store_true", help="leave out the last stage")
    a = ap.parse_args(argv)
    results = json.loads((Path(a.verify_out) / "results.json").read_text())
    vacc = report.read_targets(ROOT / "docs" / "measures.md").get("views", {})
    limit = vacc.get("views_pct", 5.0)
    tier = {v: k for k in ("must", "should", "could") for v in vacc.get(k, [])}
    total = 0
    for name in sorted(results):
        res = results[name]
        if "control" not in res or not res["control"] or (a.only and name not in a.only):
            continue
        if a.shear and not has_shear(res):
            continue
        print(f"{name}: stages {res['ref']['stage-count']} (Response), "
              f"{res['sub']['stage-count']} (r2c)")
        for vs in res.get("views_stages", []):
            ending = report.is_ending(vs)
            if a.no_endings and ending:
                continue
            # D40: the last stage of a shear case is reported, not assessed
            aside = ending and has_shear(res)
            out = [(v["view"], v["max_diff_pct"],
                    v["departure_pct"] if report.is_unstable(v, limit) else None)
                   for v in vs["views"]
                   if not v.get("missing") and v["max_diff"] > v.get("floor", 0.0)
                   and v["max_diff_pct"] > limit
                   and (not a.tier or tier.get(v["view"]) in a.tier)]
            total += 0 if aside else sum(1 for o in out if o[2] is None)
            print(f"  {vs['feature']}{' (not assessed)' if aside else ''}: stage {vs['ref_stage']} at ({vs['ref_x']:g}, "
                  f"{vs['ref_y']:g}), r2c's {vs['sub_stage']} at ({vs['sub_x']:g}, "
                  f"{vs['sub_y']:g})" + ("" if out else ": all inside"))
            for view, pct, dep in out:
                print(f"      {view} ({tier.get(view, '-')}): {pct:.1f} %"
                      + ("" if dep is None else
                         f" (not assessed: Response unstable, departure {dep:.1f} %)"))
    print(f"{total} views outside at the stages assessed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
