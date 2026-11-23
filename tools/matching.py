#!/usr/bin/env python3
"""Is a view outside target because of the view, or because of the stage it is compared at?

    python tools/matching.py REFERENCE.r2x.txt SUBJECT.r2x.txt [--tier must should could]

Answers the question a case raises when its curves agree and its views do not. At each
feature stage of the reference's curve the views are compared with the subject's stage
matched by the features of the two curves (D13) and with the subject's stage nearest it in
load and control value alone, and the line marked "compared" is the one tools/compare.py
uses: since D42 (owner, 2026-11-22) the stage at the same place where there is one within
the target, not across a fall of load, and the feature's stage otherwise. Where the two
differ, the feature was read at different stages of two curves that may otherwise be the
same (the threshold on stiffness that reads "cracking", or which of two points of a plateau
is the largest), and the views would be compared in different states.

Nothing is assessed here and no measure is changed: the differences are tools/compare.py's
own (compare_views), the limit is views_pct of docs/acceptance.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
import report  # noqa: E402
from r2c import record  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def outside(ref, sub, rs, ss, limit, tier, tiers):
    rows = cmp.compare_views(ref, sub, rs, ss)
    return [(r["view"], r["max_diff_pct"]) for r in rows
            if not r.get("missing") and r["max_diff"] > r["floor"]
            and r["max_diff_pct"] > limit and (not tiers or tier.get(r["view"]) in tiers)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference")
    ap.add_argument("subject")
    ap.add_argument("--tier", nargs="*", choices=("must", "should", "could"))
    a = ap.parse_args(argv)
    ref, sub = record.read(a.reference), record.read(a.subject)
    vacc = report.read_acceptance(ROOT / "docs" / "acceptance.md").get("views", {})
    limit = vacc.get("views_pct", 5.0)
    tier = {v: k for k in ("must", "should", "could") for v in vacc.get(k, [])}
    key = [k for k in cmp.control_keys(ref) if k in cmp.control_keys(sub)][-1]
    ca, cb = cmp._curve(ref, key), cmp._curve(sub, key)
    pk = float(np.max(np.abs(ca[:, 1]))) or 1.0
    xs = float(np.max(np.abs(ca[:, 0]))) or 1.0
    feats = cmp.feature_stages(ref, key)
    for rs in ref.stages():
        if rs >= len(ca):
            continue
        x, y = float(ca[rs, 0]), float(ca[rs, 1])
        by_feature = cmp._segment_stage(sub, key, rs, ca, cb, x, y, xs, pk)
        nearest = cmp._nearest_stage(sub, key, x, y, xs, pk)
        used, how = cmp.match_stage(sub, key, rs, ca, cb, xs, pk, cmp.same_place_limit(ref))
        print(f"{feats.get(rs, 'stage')}: reference stage {rs} at ({x:g}, {y:g}); "
              f"compared with subject stage {used} ({how})")
        for how, ss in (("matched by feature", by_feature), ("nearest in state", nearest)):
            out = outside(ref, sub, rs, ss, limit, tier, a.tier)
            worst = max(out, key=lambda o: o[1]) if out else None
            print(f"  {how}: subject stage {ss} at ({cb[ss, 0]:g}, {cb[ss, 1]:g}): "
                  f"{len(out)} views outside"
                  + (f", worst {worst[0]} {worst[1]:.1f} %" if worst else ""))
            if how == "matched by feature" and by_feature == nearest:
                print("  nearest in state: the same stage")
                break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
