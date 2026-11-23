#!/usr/bin/env python3
"""Where is Response itself unstable, and how much do the readings of the rule move it?

    python tools/unstable.py VERIFY_OUT [--reference tests/oracle] [--only NAME ...]
                             [--list] [--tier must should could] [--readings]

The owner's rule (2026-11-23, D54; docs/acceptance.md, "Where Response is unstable"): a view
check is reported and not assessed where Response's own view at the stage lies farther than
the views target from the blend of its two neighbouring stages' views. This tool answers
three questions of a verify run under that rule:

* by default, for each tier, how many view checks are inside, outside and unassessed, and
  how many were inside and outside before the rule; how many checks were tested and how many
  could not be (no neighbours: first or last stage, or a fixture without them; or a line
  that cannot be blended); and, case by case, which tier results the rule changes;
* with --list, every unassessed check, with Response's departure beside r2c's difference
  (--tier must for the list the owner reviews);
* with --readings, the same counts under the other readings of the two choices the rule's
  wording leaves open (tools/compare.py, place and blend_lines), and how many checks change
  state against the reading in use. The departures are measured again from the fixtures;
  r2c's differences are the run's own.

Nothing is assessed here that tools/report.py does not assess: the states are its
stage_checks, the target is views_pct of docs/acceptance.md.
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

# (name, place, lines): the reading in use first
READINGS = [
    ("in use: place by distance along the curve; a line one neighbour lacks blended with zero",
     "curve", "zero"),
    ("place by control value alone", "control", "zero"),
    ("place by load alone", "load", "zero"),
    ("place half way", "middle", "zero"),
    ("a line one neighbour lacks is left out of the blend", "curve", "both"),
]


def remeasure(res: dict, ref, how: str, lines: str) -> dict:
    """The result with Response's departures measured again under another reading."""
    out = copy.deepcopy(res)
    key = res["control"][-1]["chart"]
    a = compare._curve(ref, key)
    pk = float(np.max(np.abs(a[:, 1]))) or 1.0
    xs = float(np.max(np.abs(a[:, 0]))) or 1.0
    for st in out.get("views_stages", []):
        t = compare.place(a, st["ref_stage"], xs, pk, how)
        for row in st["views"]:
            row.pop("departure", None)
            row.pop("departure_pct", None)
            if row.get("missing"):
                continue
            dep = compare.departure(ref, st["ref_stage"], row["view"], t, lines)
            if dep is not None:
                row["departure"] = dep
                row["departure_pct"] = 100.0 * dep / row["ref_max"] if row["ref_max"] > 1e-9 else 0.0
    return out


def states(results: dict, acc: dict) -> dict:
    return {(n, c["view"], c["ref_stage"]): c["state"]
            for n, r in results.items() for c in report.stage_checks(r, acc)}


def print_counts(results: dict, acc: dict) -> None:
    counts = report.tier_counts(results, acc)
    print(f"{'tier':<8}{'checks':>8}{'inside':>8}{'outside':>9}{'unassessed':>12}"
          f"{'before: inside':>17}{'outside':>9}")
    for t, title in report.TIERS.items():
        n = counts[t]
        print(f"{title:<8}{n['checks']:>8}{n['inside']:>8}{n['outside']:>9}{n['unstable']:>12}"
              f"{n['plain_inside']:>17}{n['plain_outside']:>9}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verify_out", help="folder of a tools/verify.py run")
    ap.add_argument("--reference", default=str(ROOT / "tests" / "oracle"))
    ap.add_argument("--only", nargs="*", help="case names")
    ap.add_argument("--list", action="store_true", help="every unassessed check")
    ap.add_argument("--tier", nargs="*", choices=("must", "should", "could"))
    ap.add_argument("--readings", action="store_true",
                    help="the counts under the other readings of the rule")
    a = ap.parse_args(argv)
    results = json.loads((Path(a.verify_out) / "results.json").read_text())
    results = {n: r for n, r in results.items()
               if "control" in r and r["control"] and (not a.only or n in a.only)}
    acc = report.read_acceptance(ROOT / "docs" / "acceptance.md")
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
    changed = []
    for n in sorted(results):
        after, before = report.assess(results[n], acc), report.assess(results[n], acc, rule=False)
        for k in report.TIERS:
            b, f = before.get(k), after.get(k)
            if (b and b[2]) != (f and f[2]):
                word = {True: "inside", False: "outside", None: "nothing assessed"}
                changed.append(f"  {n}: {report.NAMES[k]}: {word[b[2] if b else None]} -> "
                               f"{word[f[2] if f else None]}")
    print(f"tier results of a case that the rule changes ({len(changed)}):", *changed, sep="\n")

    if a.list:
        print("\nunassessed checks: Response's departure %, r2c's difference %")
        for n in sorted(results):
            for c in report.unstable_checks(results[n], acc):
                if a.tier and tiers[c["tier"]] not in a.tier:
                    continue
                diff = "missing" if c["pct"] is None else f"{c['pct']:.1f}"
                print(f"  {report.TIERS[c['tier']]:<7}{n}: stage {c['ref_stage']} "
                      f"({c['feature'] or 'stage'}): {c['view']}: {c['departure_pct']:.1f}, "
                      f"{diff}{' (would be outside)' if c['plain'] == 'outside' else ''}")

    if a.readings:
        refs = {}
        for n in results:
            p = Path(a.reference) / f"{n}.r2x.txt"
            if not p.exists():
                p = Path(a.reference) / "parked" / p.name
            refs[n] = record.read(p)
        base = None
        for title, how, lines in READINGS:
            again = {n: remeasure(r, refs[n], how, lines) for n, r in results.items()}
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
