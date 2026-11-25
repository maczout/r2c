#!/usr/bin/env python3
"""List the checks that changed sides of their target between two verify runs.

Answers: "did this change put any check outside target that was inside, and which did it
bring inside?" The two folders are tools/verify.py outputs (before, after) on the same
fixtures. A check is a case's peak, rising branch, post-peak branch or shape, or one detail
view at one feature stage of Response's curve; inside and outside are decided as
tools/report.py decides them (docs/measures.md, the printed-precision floor included).
The views at the last stage of a shear case are not assessed (D40): those that changed
side are listed on their own and do not count as gone outside or come inside. Nor is a view
check where Response itself is unstable (D54, tools/report.py): it is named as such, counts
on neither side in either run, and a check that is unstable in one run only (the fixtures
or the rule changed between them) is listed on its own.

    python tools/changes.py VERIFY_BEFORE VERIFY_AFTER [--view principal_tensile_stress]

Prints the checks that went outside, those that came inside, and for each view the number of
stages outside before and after. With --view, also every stage of that view still outside.
Exit status 1 if any check went from inside to outside.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import report  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NOT_ASSESSED = ", not assessed"
UNSTABLE = "unstable in Response"


def checks(res: dict, acc: dict) -> dict:
    """{check name: (ok, text)} for one case of a verify run."""
    out = {}
    for k, (v, _lim, ok) in report.assess(res, acc).items():
        if k == "views" or ok is None:
            continue
        out[report.NAMES.get(k, k)] = (ok, f"{v:.2f}" if not isinstance(v, bool) else str(v))
    lim = acc.get("views", {}).get("views_pct")
    exempt = set(acc.get("views", {}).get("views_exempt", []))
    shear = report.group(res["ref"]) == "shear"
    for s in res.get("views_stages", []):
        for v in s["views"]:
            if v["view"] in exempt or lim is None:
                continue
            name = f"{v['view']} at stage {s['ref_stage']} ({s['feature']})"
            if shear and report.is_ending(s):
                # D40: the last stage of a shear case is reported, not assessed
                name += NOT_ASSESSED
            if v.get("missing"):
                out[name] = (False, "missing")
                continue
            d = 0.0 if v["max_diff"] <= v.get("floor", 0.0) else v["max_diff_pct"]
            if report.is_unstable(v, lim) and not name.endswith(NOT_ASSESSED):
                # D54: reported, not assessed
                out[name] = (None, f"{d:.1f} ({UNSTABLE}, departure {v['departure_pct']:.1f})")
                continue
            out[name] = (d <= lim, f"{d:.1f}")
    return out


def load(folder: Path) -> dict:
    return {p.stem: json.loads(p.read_text()) for p in sorted(folder.glob("*.json"))
            if p.stem not in ("results", "run")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--view", help="list every stage of this view still outside")
    ap.add_argument("--targets", default=str(ROOT / "docs" / "measures.md"))
    a = ap.parse_args(argv)
    acc = report.read_targets(Path(a.targets))
    before, after = load(Path(a.before)), load(Path(a.after))
    worse, better, still, ends, unst = [], [], [], [], []
    nb, na = Counter(), Counter()
    for case in sorted(set(before) & set(after)):
        if "control" not in before[case] or "control" not in after[case]:
            print(f"{case}: not compared ({list(before[case])[:1]} / {list(after[case])[:1]})")
            continue
        cb, ca = checks(before[case], acc), checks(after[case], acc)
        for k in sorted(set(cb) | set(ca)):
            ob, tb = cb.get(k, (None, "-"))
            oa, ta = ca.get(k, (None, "-"))
            view = k.split(" at stage ")[0]
            nb[view] += ob is False
            na[view] += oa is False
            line = f"  {case}: {k}: {tb} -> {ta}"
            if (UNSTABLE in tb) != (UNSTABLE in ta):
                unst.append(line)
            elif k.endswith(NOT_ASSESSED):
                if (ob is False) != (oa is False):
                    ends.append(line)
            elif ob is not False and oa is False:
                worse.append(line)
            elif ob is False and oa is not False:
                better.append(line)
            elif oa is False and view == a.view:
                still.append(line)
    only = sorted(set(before) ^ set(after))
    if only:
        print("in one run only:", ", ".join(only))
    print(f"went outside target ({len(worse)}):", *worse, sep="\n")
    print(f"came inside target ({len(better)}):", *better, sep="\n")
    print(f"last stage of a shear case, not assessed, changed side ({len(ends)}):", *ends,
          sep="\n")
    print(f"unstable in Response in one run only, not assessed there ({len(unst)}):", *unst,
          sep="\n")
    if a.view:
        print(f"{a.view} still outside ({len(still)}):", *still, sep="\n")
    print("checks outside, before -> after:")
    for k in sorted(nb, key=lambda k: (" at " in k, k)):
        if nb[k] or na[k]:
            print(f"  {k}: {nb[k]} -> {na[k]}")
    return 1 if worse else 0


if __name__ == "__main__":
    sys.exit(main())
