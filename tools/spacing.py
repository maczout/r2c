#!/usr/bin/env python3
"""Are r2c's crack spacing tables Response's? Answers it without solving anything: the
spacing depends on the section alone, so r2c's tables are read at the heights of the nodes
of a reference record's Longitudinal and Transverse Crack Spacing charts and set against
the chart.

    python tools/spacing.py RECORD [--input FILE] [--stages N,N] [--response-smx] [-v]

RECORD is an r2x-raw record with those charts (a fixture or a capture); --input the
section file where it is not Response's built-in one; --stages the stages whose charts are
read (default: every stage of the record that has them). --response-smx switches on
Response's longitudinal table, which is written and off (docs/kernel.md, "Crack spacing
over the depth"). Per stage and chart: the number of nodes and the largest difference in
mm, with the height it is at; -v lists every node.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
from r2c import inputs, record  # noqa: E402
from r2c.section import Section  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("record")
    ap.add_argument("--input")
    ap.add_argument("--stages")
    ap.add_argument("--response-smx", action="store_true")
    ap.add_argument("-v", action="store_true")
    a = ap.parse_args(argv)
    rec = record.read(a.record)
    if a.response_smx:
        Section.response_smx = True
    sec = Section(inputs.read(a.input) if a.input else inputs.default_section())
    stages = [int(x) for x in a.stages.split(",")] if a.stages else rec.stages()
    for st in stages:
        for view, read in (("long_crack_spacing", sec.smx_at),
                           ("transverse_crack_spacing", sec.smt_at)):
            try:
                pts = np.asarray(cmp.parse_chart(rec.stage(st, view))[3][0])
            except KeyError:
                continue
            mine = read(pts[:, 1] + sec.zaxial)
            err = mine - pts[:, 0]
            k = int(np.argmax(np.abs(err)))
            print(f"stage {st} {view}: {len(pts)} nodes, largest difference {err[k]:+.3f} mm "
                  f"at {pts[k, 1]:.2f} (Response {pts[k, 0]:.3f}, r2c {mine[k]:.3f})")
            if a.v:
                for (r, y), m in zip(pts, mine):
                    print(f"    {y:9.2f} {r:10.3f} {m:10.3f} {m - r:+8.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
