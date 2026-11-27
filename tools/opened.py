#!/usr/bin/env python3
"""What did each held-out case score? The held-out results, opened case by case.

    python tools/opened.py ARCHIVE --set heldout|finish --out FILE.md [--run FOLDER]
                           [--repeat]

FOR THE FINISHING STEPS ONLY (docs/brief.md, "Finishing"; started by the owner on
2026-11-26). Until then nothing per case of a held-out set was opened, and this tool is
the one place that does it. It does not run r2c: it reads the per-case comparisons the
scorer left in ARCHIVE/results/RUN/results.json (the latest run unless --run names one;
with --repeat, Response against itself, ARCHIVE/repeat/results.json) and writes one table
row per case and a list of every check outside target with its size, by the same tally the
scorer makes (tools/heldout.py's PRIORITY, tools/report.py's assess).

FILE.md must be outside the repository: per-case held-out results are not committed
(CLAUDE.md, "The held-out rule").
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import heldout  # noqa: E402
import report  # noqa: E402


def misses(r: dict, acc: dict, g: str) -> dict:
    """{priority: None (no such check) | [] (inside) | [text of each check outside]}."""
    checks = report.assess(r, acc)
    out = {}
    for p, names in heldout.PRIORITY[g].items():
        mine = {k: checks[k] for k in names if k in checks and checks[k][2] is not None}
        if not mine:
            out[p] = None
            continue
        cells = []
        for k, (v, _l, ok) in mine.items():
            if ok:
                continue
            if k == "shape":
                c = r["control"][-1]
                cells.append(f"shape: Response [{', '.join(c['shape_ref'])}], "
                             f"other [{', '.join(c['shape_sub'])}]")
            else:
                cells.append(f"{k} {v:.1f} %")
                for c in report.stage_checks(r, acc):
                    if c["tier"] == k and c["state"] == "outside":
                        cells.append(f"  - {c['view']} at Response's stage {c['ref_stage']} "
                                     f"({c['feature'] or 'stage'}): "
                                     + ("missing" if c["pct"] is None else f"{c['pct']:.1f} %"))
        out[p] = cells
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("archive")
    ap.add_argument("--set", choices=tuple(heldout.SETS), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--run")
    ap.add_argument("--repeat", action="store_true")
    a = ap.parse_args(argv)
    archive = heldout.outside_repo(ap, a.archive)
    dest = heldout.outside_repo(ap, a.out)
    cases = heldout.verify_frozen(archive, a.set)
    if a.repeat:
        src = archive / "repeat" / "results.json"
        who = "Response with every concrete strength raised by 0.05 %"
    else:
        runs = sorted(p for p in (archive / "results").iterdir() if (p / "results.json").exists())
        run = archive / "results" / a.run if a.run else runs[-1]
        src = run / "results.json"
        who = f"r2c (the scorer's run {run.name})"
    results = json.loads(src.read_text())
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    groups = {t: g for g, t in heldout.AREAS.items()}
    head = [f"# The {'second' if a.set == 'finish' else 'first'} held-out set, case by case: "
            f"{who} against Response", "",
            f"Target on every check: {report.views_limit(acc):g} % (docs/measures.md). "
            "\"in\": inside target on every check of the priority; \"OUT\": at least one "
            "check outside; \"-\": the case has no such check. \"cut\": compared up to "
            "Response's last stage (the override; the position along the other curve and "
            "its number of stages).", "",
            "| Case | Area | What | Stages (Response / other) | P1 | P2 | P3 | P4 | cut |",
            "|---|---|---|---|---|---|---|---|---|"]
    detail = []
    for c in cases:
        r = results.get(c["name"], {})
        g = groups[c["area"]]
        if "control" not in r:
            head.append(f"| {c['name']} | {c['area']} | {c['what']} | not solved: "
                        f"{r.get('failed') or r.get('skipped') or 'no result'} | OUT | OUT | "
                        "OUT | OUT | |")
            continue
        m = misses(r, acc, g)
        cell = lambda p: "-" if m.get(p) is None else ("in" if not m[p] else "OUT")  # noqa: E731
        up = r.get("upto")
        head.append(f"| {c['name']} | {c['area']} | {c['what']}; {c['initial']} + "
                    f"{c['increment']} | {r['ref'].get('stage-count')} / "
                    f"{r['sub'].get('stage-count')} | " + " | ".join(cell(p) for p in "1234")
                    + " | " + (f"{up['sub_position']:.1f} of {up['sub_stages']}" if up else "")
                    + " |")
        bad = {p: v for p, v in m.items() if v}
        if bad:
            ctl = r["control"][-1]
            detail += ["", f"## {c['name']}: {c['what']}; {c['initial']} + {c['increment']}", "",
                       f"Peak load: Response {ctl['ref_peak_load']:.4g} at "
                       f"{ctl['ref_peak_x']:.4g}, other {ctl['sub_peak_load']:.4g} at "
                       f"{ctl['sub_peak_x']:.4g} ({ctl['peak_diff_pct']:+.2f} %)", ""]
            for p, cells in bad.items():
                detail.append(f"- Priority {p}:")
                detail += [f"  - {x}" if not x.startswith("  ") else f"  {x}" for x in cells]
    dest.write_text("\n".join(head + detail) + "\n", encoding="utf-8")
    print(f"written: {dest.name} ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
