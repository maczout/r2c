#!/usr/bin/env python3
"""Does Response repeat itself? Set several full captures of the same case side by side.

Answers the question of D57 (docs/summary.md): before a case joins the development set it
is captured more than once through r2x, and a case whose captures differ is noted. A
fixture is one capture; this tool reads the full captures (every stage, every view) that
tools/capture.py wrote into two or more archives and says, case by case, whether they are
the same record.

    python tools/repeat.py ARCHIVE ARCHIVE [ARCHIVE ...] [--only NAME ...] [--detail]

For each case found in the first archive (or named with --only) it prints one line: the
number of stages and the peak stage of each capture, and either "repeats" (every section
of every capture byte for byte the same; header lines that identify the machine are left
out) or what differs: the stage count, the control charts, or how many detail sections.
--detail lists the sections that differ, and where the stage counts differ it says whether
the shorter capture's stages are all found, view for view, among the longer one's (as on
the I-girder with shear, where Response gives 15 or 25 stages).

Exit status 1 if any case does not repeat or is missing from an archive.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from r2c import record  # noqa: E402

# header lines that depend on the machine or the run, not on the case
MACHINE_KEYS = {"r2x-version", "wine-version", "disclaimer"}


def stage_views(rec: record.Record) -> dict[int, dict[str, bytes]]:
    out: dict[int, dict[str, bytes]] = {}
    for name, body in rec.sections.items():
        if name.startswith("stage/"):
            _, n, key = name.split("/", 2)
            out.setdefault(int(n), {})[key] = body
    return out


def contained(short: record.Record, long: record.Record) -> bool:
    """Is every stage of the shorter capture, with all its views, a stage of the longer?"""
    pool = list(stage_views(long).values())
    return all(views in pool for views in stage_views(short).values())


def compare(recs: list[record.Record]) -> dict:
    first = recs[0]
    header = sorted({k for r in recs for k in r.header if k not in MACHINE_KEYS
                     and any(q.header.get(k) != first.header.get(k) for q in recs)})
    names = sorted({n for r in recs for n in r.sections})
    differ = [n for n in names
              if any(r.sections.get(n) != first.sections.get(n) for r in recs)]
    return {"header": header,
            "control": [n for n in differ if n.startswith("control/")],
            "stage": [n for n in differ if not n.startswith("control/")],
            "total": len(names)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("archives", nargs="+", help="two or more folders of full captures")
    ap.add_argument("--only", nargs="*", help="case names (default: those of the first archive)")
    ap.add_argument("--detail", action="store_true", help="list the sections that differ")
    a = ap.parse_args(argv)
    if len(a.archives) < 2:
        ap.error("give at least two archives")
    dirs = [Path(d) for d in a.archives]
    names = a.only or sorted(p.name[: -len(".r2x.txt")] for p in dirs[0].glob("*.r2x.txt"))
    bad = 0
    for name in names:
        paths = [d / f"{name}.r2x.txt" for d in dirs]
        missing = [str(p.parent) for p in paths if not p.exists()]
        if missing:
            print(f"{name}: no capture in {', '.join(missing)}")
            bad += 1
            continue
        recs = [record.read(p) for p in paths]
        shape = ", ".join(f"{r.header.get('stage-count')} stages (peak {r.header.get('peak-stage')})"
                          for r in recs)
        d = compare(recs)
        if not (d["header"] or d["control"] or d["stage"]):
            print(f"{name}: repeats. {len(recs)} captures, {shape}; {d['total']} sections the same")
            continue
        bad += 1
        what = []
        if d["header"]:
            what.append("header " + ", ".join(d["header"]))
        if d["control"]:
            what.append(f"{len(d['control'])} control charts")
        if d["stage"]:
            what.append(f"{len(d['stage'])} of {d['total']} detail sections")
        print(f"{name}: DOES NOT REPEAT. {shape}; differ: {'; '.join(what)}")
        if a.detail:
            counts = [len(stage_views(r)) for r in recs]
            if len(set(counts)) > 1:
                short = recs[counts.index(min(counts))]
                long = recs[counts.index(max(counts))]
                print(f"  the shortest capture's stages are "
                      f"{'all' if contained(short, long) else 'NOT all'} among the longest's")
            for n in d["control"] + d["stage"]:
                print(f"  {n}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
