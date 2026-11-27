#!/usr/bin/env python3
"""What would the totals be if no case were compared only up to Response's last stage?

    python tools/uncut.py REFS SUBS [--list]

Answers the independent assessor's question at the finish (docs/assessment.md, R5): how
much of each priority's total rests on the owner's override of 2026-11-25, by which a case
with shear where Response's solve gives up and r2c carries on is compared up to Response's
last stage (tools/compare.py, carried_on)? It compares every pair of records again (REFS:
Response's captures, NAME.r2x.txt, searched recursively; SUBS: the other program's) twice,
with the rule as it is and with the rule switched off, and prints both totals by area and
priority, by the tally the held-out scorer makes. --list names the cases whose verdict on
a priority turns, with the peak of the other program's whole curve against Response's.

Nothing is changed in the measure: this is a second reading beside it, for reporting. On
a held-out set it is for the finishing steps only (it prints case names with --list).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
import heldout  # noqa: E402
import report  # noqa: E402
from r2c import record  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("refs")
    ap.add_argument("subs")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    subs = {p.name: p for p in Path(a.subs).rglob("*.r2x.txt")}
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    rule = cmp.carried_on
    cases, both = [], ({}, {})
    for rp in sorted(Path(a.refs).rglob("*.r2x.txt"), key=lambda p: p.name):
        if rp.name not in subs or "parked" in rp.parts:
            continue
        name = rp.name[: -len(".r2x.txt")]
        ref, sub = record.read(rp), record.read(subs[rp.name])
        cases.append({"name": name, "area": heldout.AREAS[report.group(ref.header)]})
        for k, fn in enumerate((rule, lambda *_a: None)):
            cmp.carried_on = fn
            both[k][name] = cmp.compare(ref, sub, views=True)
    cmp.carried_on = rule
    with_, without = (heldout.tally(cases, r, acc)["totals"] for r in both)
    print("Cases inside target on every check of the priority: with the rule / with no case cut")
    for t, title in heldout.AREA_TITLES.items():
        for p in with_[t]:
            (n, of), (m, of2) = with_[t][p], without[t][p]
            print(f"  {title}, priority {p}: {n} of {of} / {m} of {of2}")
    if a.list:
        groups = {t: g for g, t in heldout.AREAS.items()}
        for c in cases:
            g, n = groups[c["area"]], c["name"]
            turned = []
            for p, names in heldout.PRIORITY[g].items():
                v = []
                for r in both:
                    chk = report.assess(r[n], acc)
                    oks = [chk[k][2] for k in names if k in chk and chk[k][2] is not None]
                    v.append(all(oks) if oks else None)
                if v[0] != v[1]:
                    turned.append(p)
            if turned:
                print(f"  {n}: priority {', '.join(turned)} turns; the whole curve's peak "
                      f"{both[1][n]['control'][-1]['peak_diff_pct']:+.1f} % against Response's")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
