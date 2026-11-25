#!/usr/bin/env python3
"""Where is Response itself unstable, and how much do the readings of the rule move it?

    python tools/unstable.py VERIFY_OUT [--reference tests/oracle] [--only NAME ...]
                             [--list] [--tier must should could] [--readings]
    python tools/unstable.py --trace CAPTURE VIEW

The owner's rule (2026-11-23, D54, narrowed to spikes by D56; docs/measures.md, "Where
Response is unstable"): a view check is reported and not assessed where Response's views at
the two neighbouring stages agree with each other within the views target and its own view
at the stage lies farther than the target from the blend of the two. This tool answers four
questions:

* by default, of a verify run: for each tier, how many view checks are inside, outside and
  unassessed under the spike test, under no rule, and under the rule as first written
  (D54 before D56: the departure alone); how many checks were tested and how many could not
  be (no neighbours: first or last stage, or a fixture without them; or a line that cannot
  be blended); and, case by case, which tier results each rule changes;
* with --list, every unassessed check, with Response's departure, how far its neighbours
  are apart, and r2c's difference (--tier must for the list the owner reviews);
* with --readings, the same counts under the other readings of the choices the rule's
  wording leaves open (tools/compare.py, place, blend_lines and apart), and how many
  checks change state against the reading in use. The distances are measured again from
  the fixtures; r2c's differences are the run's own;
* with --trace, of one record of Response (a full capture, every stage with its views) and
  one view: stage by stage, the chart's largest value, its departure from the blend of its
  neighbours, how far the neighbours are apart, and what the two rules make of the stage.
  This is Response alone, at every stage and not only the compared ones: it shows what a
  view does along a whole response (the bond chart at the end of prestrained stirrups, the
  example D54 was written for).

Nothing is assessed here that tools/report.py does not assess: the states are its
stage_checks, the target is views_pct of docs/measures.md.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare  # noqa: E402
import report  # noqa: E402

from r2c import record  # noqa: E402

# (name, place, lines, apart): the reading in use first
READINGS = [
    ("in use: place by distance along the curve; a line one neighbour lacks blended with "
     "zero; each neighbour on its own largest value", "curve", "zero", "own"),
    ("place by control value alone", "control", "zero", "own"),
    ("place by load alone", "load", "zero", "own"),
    ("place half way", "middle", "zero", "own"),
    ("a line one neighbour lacks is left out of the blend", "curve", "both", "own"),
    ("the neighbours measured on the scale of the chart at the stage", "curve", "zero",
     "stage"),
]


def remeasure(res: dict, ref, how: str, lines: str, apart: str) -> dict:
    """The result with Response's two distances measured again under another reading."""
    out = copy.deepcopy(res)
    key = res["control"][-1]["chart"]
    a = compare._curve(ref, key)
    pk = float(np.max(np.abs(a[:, 1]))) or 1.0
    xs = float(np.max(np.abs(a[:, 0]))) or 1.0
    for st in out.get("views_stages", []):
        t = compare.place(a, st["ref_stage"], xs, pk, how)
        for row in st["views"]:
            for k in ("departure", "departure_pct", "apart_pct"):
                row.pop(k, None)
            if row.get("missing"):
                continue
            dep = compare.departure(ref, st["ref_stage"], row["view"], t, lines)
            if dep is not None:
                row["departure"] = dep
                row["departure_pct"] = 100.0 * dep / row["ref_max"] if row["ref_max"] > 1e-9 else 0.0
                row["apart_pct"] = compare.apart(ref, st["ref_stage"], row["view"], apart)
    return out


def states(results: dict, acc: dict) -> dict:
    return {(n, c["view"], c["ref_stage"]): c["state"]
            for n, r in results.items() for c in report.stage_checks(r, acc)}


def print_counts(results: dict, acc: dict) -> None:
    counts = report.tier_counts(results, acc)
    print(f"{'':<8}{'':>8}{'no rule':>16}{'as first written (D54)':>31}"
          f"{'the spike test (D56)':>31}")
    print(f"{'tier':<8}{'checks':>8}{'inside':>8}{'outside':>8}"
          + f"{'inside':>9}{'outside':>9}{'unassessed':>13}" * 2)
    for t, title in report.TIERS.items():
        n = counts[t]
        print(f"{title:<8}{n['checks']:>8}{n['plain_inside']:>8}{n['plain_outside']:>8}"
              f"{n['first_inside']:>9}{n['first_outside']:>9}{n['first_unstable']:>13}"
              f"{n['inside']:>9}{n['outside']:>9}{n['unstable']:>13}")


def trace(capture: str, view: str, lim: float) -> int:
    """One view of one record of Response at every stage that has two neighbours."""
    ref = record.read(capture)
    a = compare._curve(ref, compare.control_keys(ref)[-1])
    pk = float(np.max(np.abs(a[:, 1]))) or 1.0
    xs = float(np.max(np.abs(a[:, 0]))) or 1.0
    feats = compare.feature_stages(ref)
    print(f"{view} in {Path(capture).name}: Response alone; target {lim:g} %")
    print(f"{'stage':>5}{'control':>10}{'load':>9}{'largest':>10}{'departs %':>11}"
          f"{'apart %':>9}  as first written; spike test")
    for s in ref.stages():
        if s >= len(a) or compare.view_body(ref, s, view) is None:
            continue
        body = ref.stage(s, view)
        lines = compare.parse_chart(body)[3]
        top = max((float(np.max(np.abs(ln[:, 0]))) for ln in lines if len(ln)), default=0.0)
        t = compare.place(a, s, xs, pk)
        dep = compare.departure(ref, s, view, t)
        text = f"{s:>5}{a[s, 0]:>10.3f}{a[s, 1]:>9.1f}{top:>10.3f}"
        if dep is None:
            print(text + f"{'':>20}  not tested" + (f"  [{feats[s]}]" if s in feats else ""))
            continue
        row = {"departure": dep, "departure_pct": 100.0 * dep / top if top > 1e-9 else 0.0,
               "apart_pct": compare.apart(ref, s, view),
               "floor": compare.FLOOR_DIGITS * compare.resolution(body)[0]}
        first = "unassessed" if report.is_unstable(row, lim, "departure") else "assessed"
        spike = "unassessed (a spike)" if report.is_unstable(row, lim) else "assessed"
        print(text + f"{row['departure_pct']:>11.1f}{row['apart_pct']:>9.1f}  {first}; {spike}"
              + (f"  [{feats[s]}]" if s in feats else ""))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verify_out", nargs="?", help="folder of a tools/verify.py run")
    ap.add_argument("--trace", nargs=2, metavar=("CAPTURE", "VIEW"),
                    help="one view of a record of Response, stage by stage")
    ap.add_argument("--reference", default=str(ROOT / "tests" / "oracle"))
    ap.add_argument("--only", nargs="*", help="case names")
    ap.add_argument("--list", action="store_true", help="every unassessed check")
    ap.add_argument("--tier", nargs="*", choices=("must", "should", "could"))
    ap.add_argument("--readings", action="store_true",
                    help="the counts under the other readings of the rule")
    a = ap.parse_args(argv)
    if a.trace:
        return trace(a.trace[0], a.trace[1],
                     report.views_limit(report.read_targets(ROOT / "docs" / "measures.md")))
    if not a.verify_out:
        ap.error("VERIFY_OUT or --trace")
    results = json.loads((Path(a.verify_out) / "results.json").read_text())
    results = {n: r for n, r in results.items()
               if "control" in r and r["control"] and (not a.only or n in a.only)}
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    lim = report.views_limit(acc)
    tiers = {"views": "must", "views_should": "should", "views_could": "could"}

    print_counts(results, acc)
    tested = untested = 0
    for r in results.values():
        shear = report.group(r["ref"]) == "shear"
        for st in r.get("views_stages", []):
            if shear and report.is_ending(st):
                continue
            for row in st["views"]:
                if not row.get("missing"):
                    tested += "departure" in row
                    untested += "departure" not in row
    print(f"checks tested: {tested}; not tested, so assessed: {untested}")
    word = {True: "inside", False: "outside", None: "nothing assessed"}
    for rule, title in (("departure", "the rule as first written"), (True, "the spike test")):
        changed = []
        for n in sorted(results):
            before, after = report.assess(results[n], acc, False), report.assess(results[n], acc, rule)
            for k in report.TIERS:
                b, f = before.get(k), after.get(k)
                if (b and b[2]) != (f and f[2]):
                    changed.append(f"  {n}: {report.NAMES[k]}: {word[b[2] if b else None]} -> "
                                   f"{word[f[2] if f else None]}")
        print(f"tier results of a case that {title} changes against no rule ({len(changed)}):",
              *changed, sep="\n")

    if a.list:
        print("\nunassessed checks: Response's departure %, its neighbours apart %, "
              "r2c's difference %")
        for n in sorted(results):
            for c in report.unstable_checks(results[n], acc):
                if a.tier and tiers[c["tier"]] not in a.tier:
                    continue
                diff = "missing" if c["pct"] is None else f"{c['pct']:.1f}"
                print(f"  {report.TIERS[c['tier']]:<7}{n}: stage {c['ref_stage']} "
                      f"({c['feature'] or 'stage'}): {c['view']}: {c['departure_pct']:.1f}, "
                      f"{c['apart_pct']:.1f}, "
                      f"{diff}{' (would be outside)' if c['plain'] == 'outside' else ''}")

    if a.readings:
        refs = {}
        for n in results:
            p = Path(a.reference) / f"{n}.r2x.txt"
            if not p.exists():
                p = Path(a.reference) / "parked" / p.name
            refs[n] = record.read(p)
        base = None
        for title, how, lines, apart in READINGS:
            again = {n: remeasure(r, refs[n], how, lines, apart)
                     for n, r in results.items()}
            st = states(again, acc)
            print(f"\n{title} (target {lim:g} %)")
            print_counts(again, acc)
            if base is None:
                base = st
                same = all(states({n: results[n]}, acc) == states({n: again[n]}, acc)
                           for n in results)
                print("measured again from the fixtures: "
                      + ("the same states as the run's" if same else "DIFFERS from the run"))
            else:
                diff = [k for k in st if st[k] != base[k]]
                gone = sum(1 for k in diff if st[k] == "unstable")
                back = sum(1 for k in diff if base[k] == "unstable")
                print(f"checks that change state against the reading in use: {len(diff)} "
                      f"({gone} more unassessed, {back} assessed again)")
                for k in sorted(diff):
                    if a.list:
                        print(f"  {k[0]}: stage {k[2]}: {k[1]}: {base[k]} -> {st[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
