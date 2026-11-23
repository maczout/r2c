#!/usr/bin/env python3
"""Does r2c's rule for the Transverse Average Bond chart give a record's own chart?

Answers it without solving anything: the rule (docs/kernel.md, "The shear charts") makes
the bond chart from the stirrup stress over the depth, so it is applied to a record's own
Stirrup Stress chart, at that chart's nodes, and set against the record's Transverse
Average Bond chart. On a capture from Response this checks the rule; on r2c's own record
it only checks the export.

    python tools/bond.py RECORD [--input FILE] [--stages N,N] [-v] [--nodes]

RECORD is an r2x-raw record with both charts; --input the section file where it is not
Response's built-in one; --stages the stages (default: every stage that has both charts).
Per stage: the largest difference over the 41 heights of the chart, as a share of the
chart's largest value, and where; -v lists every height. Stages whose chart is under
0.01 MPa throughout are listed and left out of the largest.

--nodes answers another question, for prestrained stirrups: at which nodes within the
stirrups' depth does the Stirrup Stress chart show nothing (in Response, the nodes with
next to no shear strain, docs/kernel.md), and what is the bond chart's largest value in
the bottom and the top quarter of the depth at that stage? One line per stage.
"""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
from r2c import export, inputs, record  # noqa: E402
from r2c.section import Section  # noqa: E402


def chart_from_stress(sec, y, fs):
    """The bond chart r2c's rule makes of a stirrup stress chart: y the nodes' heights from
    the axis, top first, fs the stress in MPa. Returns (heights, values in MPa)."""
    z = np.asarray(y, dtype=float) + sec.zaxial
    fs = np.asarray(fs, dtype=float)
    # a node with next to no shear strain shows no stirrup stress [B 004a7b60]. With
    # prestrained stirrups such a node can be read off the chart: no stress within the
    # stirrups' depth. Without a prestrain it cannot (and makes no difference to speak of)
    lone = fs == 0.0 if any(s.prestrain != 0.0 for s in sec.stirrups) else None
    d = types.SimpleNamespace(z=z, fsy=fs, lone=lone)
    return export.bond_chart(sec, d)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("record")
    ap.add_argument("--input")
    ap.add_argument("--stages")
    ap.add_argument("-v", action="store_true")
    ap.add_argument("--nodes", action="store_true")
    a = ap.parse_args(argv)
    rec = record.read(a.record)
    sec = Section(inputs.read(a.input) if a.input else inputs.default_section())
    stages = [int(x) for x in a.stages.split(",")] if a.stages else rec.stages()
    worst = 0.0
    for st in stages:
        try:
            fs = np.asarray(cmp.parse_chart(rec.stage(st, "stirrup_stress"))[3][0])
            bond = np.asarray(cmp.parse_chart(rec.stage(st, "transverse_average_bond"))[3][0])
        except KeyError:
            continue
        if a.nodes:
            z = fs[:, 1] + sec.zaxial
            within = np.array([any(t.bot <= q <= t.top for t in sec.stirrups) for q in z])
            none = within & (fs[:, 0] == 0.0)
            h = sec.ztop - sec.zbot
            zb = bond[:, 1] + sec.zaxial
            low = bond[zb < sec.zbot + 0.25 * h, 0]
            high = bond[zb > sec.ztop - 0.25 * h, 0]
            print(f"stage {st}: {int(none.sum())} of {int(within.sum())} nodes within the "
                  f"stirrups show no stress"
                  + (f", at {', '.join(f'{q:.1f}' for q in fs[none, 1][:12])}"
                     if 0 < none.sum() < within.sum() else "")
                  + f"; bond at most {low.max():.2f} MPa in the bottom quarter, "
                  f"{high.max():.2f} in the top")
            continue
        zz, mine = chart_from_stress(sec, fs[:, 1], fs[:, 0])
        err = mine - bond[:, 0]
        top = max(float(np.max(np.abs(bond[:, 0]))), 1e-9)
        k = int(np.argmax(np.abs(err)))
        if top >= 0.01:
            worst = max(worst, abs(err[k]) / top * 100.0)
        print(f"stage {st}: largest difference {abs(err[k]) / top * 100.0:.1f} % of the "
              f"chart's {top:.3f} MPa, at {bond[k, 1]:.1f} (record {bond[k, 0]:.4f}, "
              f"rule {mine[k]:.4f})")
        if a.v:
            for (r, y), m in zip(bond, mine):
                print(f"    {y:9.2f} {r:10.4f} {m:10.4f} {m - r:+9.4f}")
    if not a.nodes:
        print(f"largest over {len(stages)} stages: {worst:.1f} %")
    return 0


if __name__ == "__main__":
    sys.exit(main())
