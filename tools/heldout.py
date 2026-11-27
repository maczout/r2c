#!/usr/bin/env python3
"""The held-out set (docs/brief.md): its recipe, its capture, and its totals-only scorer.

    python tools/heldout.py list
    python tools/heldout.py build ARCHIVE --response-dir DIR --inputs DIR [DIR ...] [--jobs N]
    python tools/heldout.py score ARCHIVE --inputs DIR [DIR ...] [--jobs N] [--record LABEL]
                                          [--kinds]
    python tools/heldout.py repeat ARCHIVE --response-dir DIR [--jobs N] [--record]
    python tools/heldout.py summary
    python tools/heldout.py list --set finish
    python tools/heldout.py build ARCHIVE2 --set finish --response-dir DIR --inputs DIR [...]

Answers "how good is r2c on sections the developer has not tuned against?", in totals.

The set is the cases below: Response's sample files under loads of the developer's choosing,
and variations of the sections of the development set across the scope (shape,
reinforcement, material models, loads, units), none of them a case of the development set.
`build` derives each input by stated text edits (as tools/variants.py does), captures every
stage of it from Response-2000 through r2x, and cuts the capture to the stages the measure
compares, all into ARCHIVE, a folder outside the repository. It then writes
heldout/manifest.json: the recipe of each case and the SHA-256 of its input and capture, and
one hash over the lot. That freezes the set: `build` refuses to run once the manifest
exists, and tools/check.py and tests/test_heldout.py hold the manifest to the hash.
A candidate that Response does not solve is not a case; it is listed in the manifest under
"not_captured" (it belongs to the interface parity check: what r2x refuses).

`score` runs r2c on every case exactly as tools/verify.py does and assesses it exactly as
tools/report.py does (the same functions), and prints ONLY totals: for each area (moment and
axial; shear) and each priority of the brief (docs/measures.md, "Checks by priority"), how
many cases are inside target on every check of that priority. A case r2c does not solve
(refused, failed, over the time limit) counts as outside on every priority. With --record
LABEL the totals are appended to heldout/totals.json, the only held-out result that is
committed. Everything per case (r2c's records, the comparisons) is written under
ARCHIVE/results/ and nowhere else.

With --kinds `score` also prints the cases outside target by kind: for each area and
priority, how many cases of each section type and loading path are outside (owner,
2026-11-25: "with no curves, numbers or case names"; it is for choosing what to add to the
development set). The kinds are printed and not recorded.

THE HELD-OUT RULE (CLAUDE.md): the developer does not open anything under ARCHIVE/results,
does not run r2c on a held-out input to look at it, and does not diagnose with these cases.
This tool prints nothing per case in `score`, on purpose; do not add an option that does.

`repeat` answers "how often does Response agree with itself on these inputs?" (owner,
2026-11-25). It raises every concrete strength of each held-out input by 0.05 %, captures
the changed input from Response-2000 through r2x with the case's own options into
ARCHIVE/repeat/, compares that capture with the frozen one exactly as `score` compares
r2c's record, and prints ONLY the totals, by area and priority. Response against Response:
r2c is not run. A changed input that Response does not solve counts as outside. With
--record the totals are written to heldout/repeatability.json; the solution threshold for
priorities 1 to 3 is that score less 3 points (THRESHOLDS below reads the file). Its
per-case comparisons stay in ARCHIVE/repeat/ and fall under the held-out rule like the
rest: not opened.

`summary` rewrites the totals block of docs/summary.md from heldout/totals.json.

THE SECOND SET, FOR THE FINISH (owner, 2026-11-25; `--set finish`): about 20 more cases of
the same spread, with values of their own, built and frozen the same way into an archive of
its own and into heldout/finish-manifest.json. It was "not scored in any way until the
finishing steps", and `score --set finish` refused it until the owner started them
(2026-11-26). Since then `score ARCHIVE2 --set finish --record LABEL` writes its totals to
heldout/finish-totals.json and `repeat ARCHIVE2 --set finish --record` Response against
itself on its inputs to heldout/finish-repeatability.json; `summary` sets them beside the
first set's.

`build` needs r2x importable (PYTHONPATH=R2X/src) and one Wine prefix per job
(~/.cache/r2x/prefix-scope-K, as tools/scope_cases.py uses them).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import queue
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import variants  # noqa: E402
from variants import T4, Variant, attr, conc, rows  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "heldout" / "manifest.json"
FINISH_MANIFEST = ROOT / "heldout" / "finish-manifest.json"
TOTALS = ROOT / "heldout" / "totals.json"
REPEAT = ROOT / "heldout" / "repeatability.json"
FINISH_TOTALS = ROOT / "heldout" / "finish-totals.json"
FINISH_REPEAT = ROOT / "heldout" / "finish-repeatability.json"
REPEAT_BY = 0.05    # per cent added to every concrete strength (owner, 2026-11-25)
MARGIN = 3.0        # points under Response's own score: the threshold (owner, 2026-11-25)
SUMMARY = ROOT / "docs" / "summary.md"
BEGIN, END = "<!-- heldout:begin -->", "<!-- heldout:end -->"

AREAS = {"flexure": "moment-axial", "shear": "shear"}
AREA_TITLES = {"moment-axial": "Moment and axial", "shear": "Shear"}
# The brief's priorities as checks of tools/report.py's assess (docs/measures.md)
PRIORITY = {
    "flexure": {"1": ("peak", "curve", "shape", "views"), "2": ("post_peak", "views_should"),
                "3": ("views_could",)},
    "shear": {"1": ("peak", "curve", "shape", "views"), "2": ("views_should",),
              "3": ("views_could",), "4": ("post_peak",)},
}
# The solution threshold (owner, 2026-11-25; docs/brief.md, "Owner's decisions since"): for
# each area and priority 1 to 3, Response's own score against itself on the held-out inputs
# (heldout/repeatability.json, written by `repeat --record`) less MARGIN points, in per cent
# of cases inside. Priority 4 (endings with shear) is reported only, and since the owner's
# answer of 2026-11-26 so is priority 2 with shear (REPORTED): the live targets with shear
# are priorities 1 and 3. THRESHOLD is priority 1's.


# Kept by the owner (2026-11-26) whatever Response scores against itself: priority 1
# without shear stays at 99 %.
KEPT = {"moment-axial": {"1": 99.0}}
# Reported, not a target (owner, 2026-11-26): r2c's standing is set beside Response's own
# score (the brief, docs/summary.md, the results page), with no threshold.
REPORTED = {"shear": ("2",)}


def read_repeat(path: Path = REPEAT) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def thresholds(rep: dict | None) -> dict:
    if rep is None:
        return {t: {} for t in AREA_TITLES}
    made = {t: {p: round(100.0 * n / of - MARGIN, 1) for p, (n, of) in by.items()
                if p in "123" and of}
            for t, by in rep["totals"].items()}
    for t, by in KEPT.items():
        made.setdefault(t, {}).update(by)
    for t, ps in REPORTED.items():
        for p in ps:
            made.get(t, {}).pop(p, None)
    return made


THRESHOLDS = thresholds(read_repeat())
THRESHOLD = {t: by.get("1") for t, by in THRESHOLDS.items()}
TIME_LIMIT = 1800   # seconds for r2c on one case before it counts as not solved

# ---------------------------------------------------------------------------------------
# The recipe. Inputs: Response's sample files as they are (found by name in --inputs), and
# edits of the four sections of the development set (tools/variants.py, BASES).
# ---------------------------------------------------------------------------------------

SAMPLES = {"cm4": "Cm4.rsp", "liping": "Liping LB1.rsp", "marshall": "Marshall.rsp",
           "dmn1n": "dm-n1n.rsp", "se100": "se100am69.rsp"}

NB_OUTLINE = "600.0\t250.0\r\n\t\t\t\t\t0.0\t250.0"
NB_STIRRUPS = ("\t\t<transreinfz\t" + attr("A", "100.0") + T4 + attr("type", "Trans") + T4
               + attr("pattern", "5") + T4 + attr("space", "250.0") + T4
               + attr("disttop", "554.3") + T4 + attr("distbot", "45.7") + T4
               + attr("bartitle", "10M") + T4 + attr("name", "stirrup") + "\t/>\r\n")
NB_TOP_END = attr("bartitle", "20M") + T4 + attr("name", "top") + "\t/>\r\n"
NB_MID = ("\t\t<longreinfx\t" + attr("z", "300.00") + T4 + attr("type", "Steel 1") + T4
          + attr("num", "2") + T4 + attr("A", "600.0") + T4 + attr("bartitle", "20M") + T4
          + attr("name", "mid") + "\t/>\r\n")
NB_LOADING = "<sectloading\t\t/>"


def sub(key, old, new, count=None):
    e = (attr(key, old), attr(key, new))
    return e + (count,) if count else e


H: dict[str, Variant] = {}
# materials on Newbeam
H["h-fc25"] = Variant("newbeam", "Newbeam with 25 MPa concrete", [sub("fcp", "35.0", "25.0")])
H["h-fc70"] = Variant("newbeam", "Newbeam with 70 MPa concrete", [sub("fcp", "35.0", "70.0")])
H["h-fc90"] = Variant("newbeam", "Newbeam with 90 MPa concrete and 10 mm aggregate",
                      [sub("fcp", "35.0", "90.0"), sub("maxagg", "19.0", "10.0")])
H["h-fy500"] = Variant("newbeam", "Newbeam with 500 MPa steel, longitudinal and transverse",
                       [sub("fy", "400.0", "500.0", 2)])
H["h-csoft1"] = Variant("newbeam", "Newbeam, compression softening Vecchio-Collins 1982",
                        conc("c_soft", "1"))
H["h-csoft12"] = Variant("newbeam", "Newbeam, compression softening Kaufmann-Marti 1998",
                         conc("c_soft", "12"))
H["h-cmod1"] = Variant("newbeam", "Newbeam, parabolic concrete base curve", conc("c_mod", "1"))
H["h-ft"] = Variant("newbeam", "Newbeam, tensile strength given as 3.00 MPa",
                    [(attr("fcp", "35.0"), attr("fcp", "35.0") + T4 + attr("ft", "3.00"))])
H["h-e0"] = Variant("newbeam", "Newbeam, strain at peak stress given as 2.60 mm/m",
                    [(attr("fcp", "35.0"), attr("fcp", "35.0") + T4 + attr("e0", "2.60"))])
H["h-tstiff3"] = Variant("newbeam", "Newbeam with 50 MPa concrete, tension stiffening Izumo",
                         [(attr("fcp", "35.0") + "\r\n\t\t\t\t" + attr("maxagg", "19.0"),
                           attr("fcp", "50.0") + T4 + attr("maxagg", "19.0") + T4
                           + attr("t_stiff", "3"))])
# shapes: rectangles of other proportions
H["h-deep"] = Variant(
    "newbeam", "a deep beam, 300 x 1000 mm, 2500 mm2 bottom steel, stirrups at 200 mm",
    [(NB_OUTLINE, "1000.0\t300.0\r\n\t\t\t\t\t0.0\t300.0"), sub("par1", "250.0", "300.0"),
     sub("par2", "600.0", "1000.0"), sub("z", "538.95", "938.95"),
     sub("A", "1500.0", "2500.0"), sub("space", "250.0", "200.0"),
     sub("disttop", "554.3", "954.3")])
H["h-slab"] = Variant(
    "newbeam", "a slab strip, 1000 x 250 mm, no stirrups",
    [(NB_OUTLINE, "250.0\t1000.0\r\n\t\t\t\t\t0.0\t1000.0"), sub("par1", "250.0", "1000.0"),
     sub("par2", "600.0", "250.0"), sub("z", "538.95", "205.00"), sub("A", "300.0", "500.0"),
     sub("z", "63.90", "45.00"), (NB_STIRRUPS, "")])
# reinforcement on Newbeam
H["h-light"] = Variant("newbeam", "Newbeam with 600 mm2 bottom steel (lightly reinforced)",
                       [sub("A", "1500.0", "600.0")])
H["h-heavy"] = Variant("newbeam", "Newbeam with 3000 mm2 bottom and 1000 mm2 top steel",
                       [sub("A", "1500.0", "3000.0"), sub("A", "300.0", "1000.0")])
H["h-st100"] = Variant("newbeam", "Newbeam with stirrups at 100 mm",
                       [sub("space", "250.0", "100.0")])
H["h-stheavy"] = Variant("newbeam", "Newbeam with closed stirrups of 300 mm2 at 150 mm",
                         [sub("A", "100.0", "300.0"), sub("pattern", "5", "3"),
                          sub("space", "250.0", "150.0")])
H["h-mid"] = Variant("newbeam", "Newbeam with a third layer of steel at mid-depth",
                     [(NB_TOP_END, NB_TOP_END + NB_MID)])
H["h-shrink6"] = Variant(
    "newbeam", "Newbeam with shrinkage of -0.60 mm/m over the depth",
    [("\t\t" + NB_LOADING, "\t\t<shrinktherm\t\t>" + rows([("600.0", "-0.600"),
                                                           ("  0.0", "-0.600")])
      + "\r\n\t\t\t</shrinktherm>\r\n\t\t" + NB_LOADING)])
# the other sections of the development set, varied
H["h-tb-fc28"] = Variant("tbeam", "the T-beam with 28 MPa concrete and stirrups at 150 mm",
                         [sub("fcp", "40.0", "28.0"), sub("space", "300.0", "150.0")])
H["h-col-fc30"] = Variant("column", "the column with 30 MPa concrete and hoops at 100 mm",
                          [sub("fcp", "50.0", "30.0"), sub("space", "300.0", "100.0")])
H["h-ig-dep4"] = Variant("igirder", "the I-girder with its strands prestrained to 4.00 mm/m",
                         [sub("dep", "6.50", "4.00", 2)])
H["h-ig-fc40"] = Variant("igirder", "the I-girder with 40 MPa concrete",
                         [sub("fcp", "60.0", "40.0")])


# ---------------------------------------------------------------------------------------
# The second set, for the finish (owner, 2026-11-25): the same spread, values of its own.
# ---------------------------------------------------------------------------------------
F: dict[str, Variant] = {}
F["f-fc40"] = Variant("newbeam", "Newbeam with 40 MPa concrete", [sub("fcp", "35.0", "40.0")])
F["f-fc60"] = Variant("newbeam", "Newbeam with 60 MPa concrete", [sub("fcp", "35.0", "60.0")])
F["f-fy350"] = Variant("newbeam", "Newbeam with 350 MPa steel, longitudinal and transverse",
                       [sub("fy", "400.0", "350.0", 2)])
F["f-csoft8"] = Variant("newbeam", "Newbeam, compression softening model 8",
                        conc("c_soft", "8"))
F["f-deep800"] = Variant(
    "newbeam", "a deep beam, 300 x 800 mm, 1800 mm2 bottom steel, stirrups at 175 mm",
    [(NB_OUTLINE, "800.0\t300.0\r\n\t\t\t\t\t0.0\t300.0"), sub("par1", "250.0", "300.0"),
     sub("par2", "600.0", "800.0"), sub("z", "538.95", "738.95"),
     sub("A", "1500.0", "1800.0"), sub("space", "250.0", "175.0"),
     sub("disttop", "554.3", "754.3")])
F["f-slab220"] = Variant(
    "newbeam", "a slab strip, 1000 x 220 mm, no stirrups",
    [(NB_OUTLINE, "220.0\t1000.0\r\n\t\t\t\t\t0.0\t1000.0"), sub("par1", "250.0", "1000.0"),
     sub("par2", "600.0", "220.0"), sub("z", "538.95", "178.00"), sub("A", "300.0", "450.0"),
     sub("z", "63.90", "42.00"), (NB_STIRRUPS, "")])
F["f-heavy2000"] = Variant("newbeam", "Newbeam with 2000 mm2 bottom and 600 mm2 top steel",
                           [sub("A", "1500.0", "2000.0"), sub("A", "300.0", "600.0")])
F["f-st200"] = Variant("newbeam", "Newbeam with stirrups at 200 mm",
                       [sub("space", "250.0", "200.0")])
F["f-mid500"] = Variant(
    "newbeam", "Newbeam with a third layer of steel, 500 mm2 at 350 mm",
    [(NB_TOP_END, NB_TOP_END + "\t\t<longreinfx\t" + attr("z", "350.00") + T4
      + attr("type", "Steel 1") + T4 + attr("num", "2") + T4 + attr("A", "500.0") + T4
      + attr("bartitle", "15M") + T4 + attr("name", "mid") + "\t/>\r\n")])
F["f-tb-fc35"] = Variant("tbeam", "the T-beam with 35 MPa concrete and stirrups at 250 mm",
                         [sub("fcp", "40.0", "35.0"), sub("space", "300.0", "250.0")])
F["f-ig-dep55"] = Variant("igirder", "the I-girder with its strands prestrained to 5.50 mm/m",
                          [sub("dep", "6.50", "5.50", 2)])


def case(name, inp, increment, initial="0,0,0", units="si", factors="none", more_detail="0"):
    return dict(name=name, input=inp, initial=initial, increment=increment, units=units,
                factors=factors, more_detail=more_detail)


CASES = [
    # Response's sample files, under loads other than the files' own
    case("h-cm4-m", "cm4", "0,1,0"),
    case("h-cm4-m2v", "cm4", "0,2,1"),
    case("h-liping-m", "liping", "0,1,0"),
    case("h-liping-nmv", "liping", "0,1.5,1", initial="-400,0,0"),
    case("h-marshall-m2v", "marshall", "0,2,1"),
    case("h-marshall-nm", "marshall", "0,1,0", initial="-1000,0,0"),
    case("h-dmn1n-m", "dmn1n", "0,1,0"),
    case("h-dmn1n-m3v", "dmn1n", "0,3,1"),
    case("h-se100-m", "se100", "0,1,0"),
    case("h-se100-m25v", "se100", "0,2.5,1"),
    # materials
    case("h-fc25-m", "h-fc25", "0,1,0"),
    case("h-fc25-mv", "h-fc25", "0,1,1"),
    case("h-fc70-m", "h-fc70", "0,1,0"),
    case("h-fc70-m2v", "h-fc70", "0,2,1"),
    case("h-fc90-mv", "h-fc90", "0,1.5,1"),
    case("h-fy500-m", "h-fy500", "0,1,0"),
    case("h-csoft1-mv", "h-csoft1", "0,1,1"),
    case("h-csoft12-mv", "h-csoft12", "0,1,1"),
    case("h-cmod1-m", "h-cmod1", "0,1,0"),
    case("h-ft-mv", "h-ft", "0,1,1"),
    case("h-e0-nm", "h-e0", "0,1,0", initial="-1000,0,0"),
    case("h-tstiff3-m", "h-tstiff3", "0,1,0"),
    # shapes
    case("h-deep-m", "h-deep", "0,1,0"),
    case("h-deep-m2v", "h-deep", "0,2,1"),
    case("h-slab-m", "h-slab", "0,1,0"),
    case("h-slab-mv", "h-slab", "0,1,1"),
    # reinforcement
    case("h-light-m", "h-light", "0,1,0"),
    case("h-heavy-m", "h-heavy", "0,1,0"),
    case("h-heavy-negmv", "h-heavy", "0,-1,1"),
    case("h-st100-mv", "h-st100", "0,1,1"),
    case("h-st100-nv", "h-st100", "0,0,1", initial="-300,0,0"),
    case("h-stheavy-m3v", "h-stheavy", "0,3,1"),
    case("h-mid-nm", "h-mid", "0,1,0", initial="-1500,0,0"),
    case("h-mid-mv", "h-mid", "0,1,1"),
    # loads, on Newbeam and with shrinkage
    case("h-nb-m3v", "newbeam", "0,3,1"),
    case("h-nb-ncomp-mv", "newbeam", "0,1,1", initial="-1000,0,0"),
    case("h-nb-m100-v", "newbeam", "0,0,1", initial="0,100,0"),
    case("h-shrink6-mv", "h-shrink6", "0,1,1"),
    # the T-beam, the column and the I-girder: loads, materials, units and factors
    case("h-tb-m3v", "tbeam", "0,3,1"),
    case("h-tb-negm2v", "tbeam", "0,-2,1"),
    case("h-tb-nm", "tbeam", "0,1,0", initial="-2000,0,0"),
    case("h-tb-us-m", "tbeam", "0,1,0", units="us"),
    case("h-tb-csa-mv", "tbeam", "0,2.5,1", factors="csa"),
    case("h-tb-fc28-m", "h-tb-fc28", "0,1,0"),
    case("h-col-m", "column", "0,1,0"),
    case("h-col-n8000-m", "column", "0,1,0", initial="-8000,0,0"),
    case("h-col-ntens-m", "column", "0,1,0", initial="500,0,0"),
    case("h-col-n2000-mv", "column", "0,1,1", initial="-2000,0,0"),
    case("h-col-kgcm-m", "column", "0,1,0", units="kgcm"),
    case("h-col-fc30-nm", "h-col-fc30", "0,1,0", initial="-3000,0,0"),
    case("h-ig-negm", "igirder", "0,-1,0"),
    case("h-ig-m4v", "igirder", "0,4,1"),
    case("h-ig-nm", "igirder", "0,1,0", initial="-1000,0,0"),
    case("h-ig-dep4-m", "h-ig-dep4", "0,1,0"),
    case("h-ig-dep4-m3v", "h-ig-dep4", "0,3,1"),
    case("h-ig-fc40-m25v", "h-ig-fc40", "0,2.5,1"),
]
FINISH_CASES = [
    # Response's sample files
    case("f-cm4-n300-m25v", "cm4", "0,2.5,1", initial="-300,0,0"),
    case("f-liping-m3v", "liping", "0,3,1"),
    case("f-se100-n200-m", "se100", "0,1,0", initial="-200,0,0"),
    case("f-marshall-ntens300-m", "marshall", "0,1,0", initial="300,0,0"),
    # materials
    case("f-fc40-m", "f-fc40", "0,1,0"),
    case("f-fc60-m15v", "f-fc60", "0,1.5,1"),
    case("f-fy350-mv", "f-fy350", "0,1,1"),
    case("f-csoft8-m2v", "f-csoft8", "0,2,1"),
    # shapes
    case("f-deep800-m25v", "f-deep800", "0,2.5,1"),
    case("f-slab220-m", "f-slab220", "0,1,0"),
    # reinforcement
    case("f-heavy2000-n800-m", "f-heavy2000", "0,1,0", initial="-800,0,0"),
    case("f-st200-m2v", "f-st200", "0,2,1"),
    case("f-mid500-m15v", "f-mid500", "0,1.5,1"),
    # loads
    case("f-nb-m150-v", "newbeam", "0,0,1", initial="0,150,0"),
    # the T-beam, the column and the I-girder
    case("f-tb-m15v", "tbeam", "0,1.5,1"),
    case("f-tb-fc35-n500-m", "f-tb-fc35", "0,1,0", initial="-500,0,0"),
    case("f-tb-kgcm-negm", "tbeam", "0,-1,0", units="kgcm"),
    case("f-col-n4500-m", "column", "0,1,0", initial="-4500,0,0"),
    case("f-col-n1500-m15v", "column", "0,1.5,1", initial="-1500,0,0"),
    case("f-col-csa-m", "column", "0,1,0", factors="csa"),
    case("f-ig-m25v", "igirder", "0,2.5,1"),
    case("f-ig-dep55-m", "f-ig-dep55", "0,1,0"),
]
RECIPES = {**H, **F}
# the two sets: the cases of each and where each is frozen
SETS = {"heldout": (CASES, MANIFEST), "finish": (FINISH_CASES, FINISH_MANIFEST)}
# where each set's totals and its Response-against-itself totals are recorded
OUTPUTS = {"heldout": (TOTALS, REPEAT), "finish": (FINISH_TOTALS, FINISH_REPEAT)}
PRESENT = {"newbeam": "input.r2t", "tbeam": "tbeam.r2t", "column": "column.r2t",
           "igirder": "igirder.r2t"}


def what(c: dict) -> str:
    k = c["input"]
    if k in SAMPLES:
        return f"Response's sample file {SAMPLES[k]}, as it is"
    if k in PRESENT:
        return {"newbeam": "Newbeam", "tbeam": "the T-beam", "column": "the column",
                "igirder": "the I-girder"}[k] + ", as it is"
    return RECIPES[k].what


def input_bytes(c: dict, folders) -> tuple[str, bytes]:
    """The case's input: (the file name r2x is to record, its bytes)."""
    k = c["input"]
    if k in SAMPLES:
        for d in folders:
            p = Path(d) / SAMPLES[k]
            if p.is_file():
                return SAMPLES[k], p.read_bytes()
        raise SystemExit(f"{SAMPLES[k]} not found directly in a folder of --inputs")
    if k in PRESENT:
        return PRESENT[k], variants.find_base(k, folders).read_bytes()
    variants.VARIANTS[k] = RECIPES[k]
    return f"{k}.r2t", variants.build(k, folders)


def area(c: dict) -> str:
    v = float(c["increment"].split(",")[2]), float(c["initial"].split(",")[2])
    return AREAS["shear" if any(v) else "flexure"]


def digest(cases: list[dict]) -> str:
    """One hash over the frozen cases: their recipe and their hashes."""
    return hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest()


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def outside_repo(ap, path: str) -> Path:
    p = Path(path).resolve()
    if ROOT in p.parents or p == ROOT:
        ap.error("the archive belongs outside the repository")
    return p


# ---------------------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------------------

def build(a, ap) -> int:
    import capture

    CASES, MANIFEST = SETS[a.set]
    if MANIFEST.exists():
        ap.error(f"heldout/{MANIFEST.name} exists: the set is frozen and is not rebuilt")
    if not a.response_dir:
        ap.error("--response-dir or $R2X_RESPONSE_DIR is required")
    archive = outside_repo(ap, a.archive)
    for d in ("inputs-src", "fixtures"):
        (archive / d).mkdir(parents=True, exist_ok=True)
    prefixes: queue.Queue = queue.Queue()
    for k in range(max(a.jobs, 1)):
        prefixes.put(Path.home() / ".cache" / "r2x" / f"prefix-scope-{k}")
    srcs = {}
    for c in CASES:   # written before the threads start: several cases share an input
        name, data = input_bytes(c, a.inputs)
        folder = archive / "inputs-src" / hashlib.sha256(data).hexdigest()[:16]
        folder.mkdir(exist_ok=True)
        (folder / name).write_bytes(data)
        srcs[c["name"]] = folder / name

    def one(c):
        prefix = prefixes.get()
        try:
            worker = [sys.executable, "-m", "r2x.worker", "--prefix", str(prefix)]
            # prints Response's stage count and the stages kept: Response's own, not a result
            return capture.add_case(archive, worker, a.response_dir, archive / "fixtures",
                                    c["name"], srcs[c["name"]], c["initial"], c["increment"],
                                    c["units"], c["factors"], c["more_detail"])
        finally:
            prefixes.put(prefix)

    todo = [c for c in CASES if not (archive / "fixtures" / f"{c['name']}.r2x.txt").exists()]
    with ThreadPoolExecutor(max_workers=max(a.jobs, 1)) as ex:
        list(ex.map(one, todo))
    capture.merge_manifest(archive)
    cases, missed = [], []
    for c in CASES:
        fx = archive / "fixtures" / f"{c['name']}.r2x.txt"
        entry = dict(c, area=area(c), what=what(c), input_name=srcs[c["name"]].name,
                     input_sha256=sha256(srcs[c["name"]]))
        if not fx.exists():
            missed.append(dict(entry, reason="Response gave no response through r2x "
                                             "(ARCHIVE/manifest.json has r2x's message)"))
            continue
        entry["capture_sha256"] = sha256(fx)
        entry["full_capture_sha256"] = sha256(archive / f"{c['name']}.r2x.txt")
        cases.append(entry)
    if a.dry_freeze:
        print(f"{len(cases)} captured, {len(missed)} not; manifest not written (--dry-freeze)")
        return 0
    MANIFEST.parent.mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps(
        {"frozen": dt.date.today().isoformat(), "frozen_sha256": digest(cases),
         "response": "Response-2000 1.9.7 through r2x; every stage, all views; the capture "
                     "hashed is the one cut to the compared stages (tools/trim.py)",
         "cases": cases, "not_captured": missed}, indent=1) + "\n")
    n = {t: sum(c["area"] == k for c in cases) for k, t in AREA_TITLES.items()}
    print(f"frozen: {len(cases)} cases ("
          + ", ".join(f"{t.lower()} {v}" for t, v in n.items())
          + f"); {len(missed)} candidates not captured")
    return 0


# ---------------------------------------------------------------------------------------
# score: totals only
# ---------------------------------------------------------------------------------------

def verify_frozen(archive: Path, which: str = "heldout") -> list[dict]:
    manifest = SETS[which][1]
    man = json.loads(manifest.read_text())
    if man["frozen_sha256"] != digest(man["cases"]):
        raise SystemExit(f"heldout/{manifest.name} is not as frozen")
    for c in man["cases"]:
        fx = archive / "fixtures" / f"{c['name']}.r2x.txt"
        if not fx.exists() or sha256(fx) != c["capture_sha256"]:
            raise SystemExit("the archive's captures are not the frozen ones (one is missing "
                             "or changed); nothing scored")
    return man["cases"]


SECTIONS = {"newbeam": "rectangular beam", "tbeam": "T-beam", "column": "circular column",
            "igirder": "prestressed I-girder", "h-deep": "deep rectangular beam",
            "h-slab": "slab strip without stirrups", "f-deep800": "deep rectangular beam",
            "f-slab220": "slab strip without stirrups"}


def kind(c: dict) -> tuple[str, str]:
    """A case's kind, from its recipe alone: (section type, loading path)."""
    k = c["input"]
    if k in SAMPLES:
        section = "a sample file of Response's"
    else:
        section = SECTIONS.get(k) or SECTIONS[RECIPES[k].base if k in RECIPES else k]
    n0, m0, _v0 = (float(x) for x in c["initial"].split(","))
    _n, m, v = (float(x) for x in c["increment"].split(","))
    path = []
    if n0:
        path.append("axial compression, then" if n0 < 0 else "axial tension, then")
    if m0:
        path.append("a moment, then")
    if v and not m:
        path.append("shear alone")
    elif v:
        path.append(("negative " if m < 0 else "") + "moment and shear, M/V "
                    + ("under 2 m" if abs(m / v) < 2.0 else "2 m or more"))
    else:
        path.append(("negative " if m < 0 else "") + "moment")
    return section, " ".join(path)


def text_kinds(kinds: dict) -> str:
    """The cases outside target by kind, as printed: no case names, no values."""
    out = ["Cases outside target by kind (section type; loading path): outside of that kind"]
    for t, title in AREA_TITLES.items():
        for p, by in kinds[t].items():
            bad = {k: v for k, v in by.items() if v[0]}
            out.append(f"  {title}, priority {p}:" + ("" if bad else " none outside"))
            for (section, path), (n, of) in sorted(bad.items()):
                out.append(f"    {section}; {path}: {n} of {of}")
    return "\n".join(out)


def tally(cases: list[dict], results: dict, acc: dict) -> dict:
    """{area: {priority: [inside, of]}} and the number of cases not solved, by area; and
    "kinds", {area: {priority: {kind: [outside, of]}}} for the cases that have a recipe
    (kind), which is printed on request and never recorded."""
    import report

    totals = {t: {p: [0, 0] for p in PRIORITY[g]} for g, t in AREAS.items()}
    kinds = {t: {p: {} for p in PRIORITY[g]} for g, t in AREAS.items()}

    def count(c, t, p, outside):
        if "input" in c:
            n = kinds[t][p].setdefault(kind(c), [0, 0])
            n[0] += outside
            n[1] += 1
    unsolved = {t: 0 for t in AREAS.values()}
    groups = {t: g for g, t in AREAS.items()}
    for c in cases:
        t = c["area"]
        g = groups[t]
        res = results.get(c["name"], {})
        if "control" not in res:
            unsolved[t] += 1
            for p in PRIORITY[g]:
                totals[t][p][1] += 1
                count(c, t, p, 1)
            continue
        chk = report.assess(res, acc)
        for p, names in PRIORITY[g].items():
            oks = [chk[n][2] for n in names if n in chk and chk[n][2] is not None]
            if not oks:
                continue
            totals[t][p][1] += 1
            totals[t][p][0] += all(oks)
            count(c, t, p, 0 if all(oks) else 1)
    return {"totals": totals, "unsolved": unsolved, "kinds": kinds}


def score(a, ap) -> int:
    import report

    # the second set: refused until the owner started the finishing steps (2026-11-26)
    CASES, totals_file = SETS[a.set][0], OUTPUTS[a.set][0]
    archive = outside_repo(ap, a.archive)
    cases = verify_frozen(archive, a.set)
    rc, commit = subprocess.getstatusoutput(f"git -C {ROOT} rev-parse --short=12 HEAD")
    dirty = bool(subprocess.getoutput(f"git -C {ROOT} status --porcelain -- src"))
    label = a.record or "unrecorded"
    out = archive / "results" / f"{dt.datetime.now():%Y%m%d-%H%M%S}-{re.sub(r'[^A-Za-z0-9._-]+', '-', label)}"
    out.mkdir(parents=True)

    def one(c):
        cmd = [sys.executable, str(ROOT / "tools" / "verify.py"), str(archive / "fixtures"),
               "--only", c["name"], "--out", str(out / c["name"]), "--inputs", *a.inputs,
               str(archive / "inputs-src")]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=TIME_LIMIT)
        except subprocess.TimeoutExpired:
            return c["name"], {"failed": "over the time limit"}
        p = out / c["name"] / "results.json"
        return c["name"], (json.loads(p.read_text()).get(c["name"], {}) if p.exists() else {})

    # how a trace of Response shows each case to have ended, for the cut (owner, 2026-11-27;
    # tools/traceend.py): per case, so it stays in the archive
    os.environ["R2C_TRACE_ENDS"] = str(archive / "trace-ends.json")
    with ThreadPoolExecutor(max_workers=max(a.jobs, 1)) as ex:
        results = dict(ex.map(one, cases))
    (out / "results.json").write_text(json.dumps(results, indent=1))
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    recipe = {c["name"]: c for c in CASES}
    counted = tally([dict(recipe[c["name"]], area=c["area"]) for c in cases], results, acc)
    kinds = counted.pop("kinds")
    # with no case cut (owner, 2026-11-27: reported first)
    import compare as cmp
    counted["uncut"] = tally([{"name": c["name"], "area": c["area"]} for c in cases],
                             {n: cmp.uncut(r) for n, r in results.items()}, acc)["totals"]
    run = dict(label=label, date=dt.date.today().isoformat(),
               commit=(commit if rc == 0 else "") + ("+dirty" if dirty else ""),
               cases={t: sum(c["area"] == t for c in cases) for t in AREAS.values()},
               **counted)
    print(text_totals(run))
    if a.kinds:
        print(text_kinds(kinds))
    if a.record:
        if dirty:
            raise SystemExit("not recorded: src/ has uncommitted changes")
        totals = read_totals(totals_file)
        totals["runs"].append(run)
        check_totals(totals)
        totals_file.write_text(json.dumps(totals, indent=1) + "\n")
        print(f"recorded as \"{label}\" in heldout/{totals_file.name}")
    return 0


# ---------------------------------------------------------------------------------------
# repeat: Response against itself, totals only
# ---------------------------------------------------------------------------------------

def repeat(a, ap) -> int:
    import capture as cap
    import compare as cmp
    import noise
    import report
    import verify
    from r2c import record

    archive = outside_repo(ap, a.archive)
    cases = verify_frozen(archive, a.set)
    out = archive / "repeat"
    (out / "inputs").mkdir(parents=True, exist_ok=True)
    prefixes: queue.Queue = queue.Queue()
    for k in range(max(a.jobs, 1)):
        prefixes.put(Path.home() / ".cache" / "r2x" / f"prefix-scope-{k}")

    def one(c):
        dest = out / f"{c['name']}.r2x.txt"
        if dest.exists():
            return
        if not a.response_dir:
            ap.error("--response-dir or $R2X_RESPONSE_DIR is required")
        h = record.read(archive / "fixtures" / dest.name).header
        src = verify.find_input(c["input_name"], c["input_sha256"], [archive / "inputs-src"])
        inp = out / "inputs" / c["name"] / src.name
        inp.parent.mkdir(exist_ok=True)
        inp.write_bytes(noise.stronger(src.read_bytes(), REPEAT_BY))
        prefix = prefixes.get()
        try:
            worker = [sys.executable, "-m", "r2x.worker", "--prefix", str(prefix)]
            subprocess.run(cap.command(h, inp, dest, worker, a.response_dir),
                           capture_output=True, text=True)
        finally:
            prefixes.put(prefix)

    with ThreadPoolExecutor(max_workers=max(a.jobs, 1)) as ex:
        list(ex.map(one, cases))
    results = {}
    for c in cases:
        p = out / f"{c['name']}.r2x.txt"
        if p.exists():
            ref = record.read(archive / "fixtures" / p.name)
            results[c["name"]] = cmp.compare(ref, record.read(p), views=True)
    (out / "results.json").write_text(json.dumps(results, indent=1))
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    counted = tally([{"name": c["name"], "area": c["area"]} for c in cases], results, acc)
    rep = {"what": f"Response-2000 with every concrete strength raised by {REPEAT_BY:g} %, "
                   "compared with Response as it is by the measure r2c is held to; cases "
                   "inside target on every check of the priority",
           "date": dt.date.today().isoformat(), "by_per_cent": REPEAT_BY,
           "cases": {t: sum(c["area"] == t for c in cases) for t in AREAS.values()},
           "totals": counted["totals"], "unsolved": counted["unsolved"]}
    print(text_repeat(rep))
    if a.record:
        OUTPUTS[a.set][1].write_text(json.dumps(rep, indent=1) + "\n")
        print(f"recorded in heldout/{OUTPUTS[a.set][1].name}")
    return 0


def text_repeat(rep: dict) -> str:
    out = [f"Response against itself on the held-out inputs ({rep['date']}; every concrete "
           f"strength raised by {rep['by_per_cent']:g} %): cases inside target on every check "
           "of the priority"]
    th = thresholds(rep)
    for t, title in AREA_TITLES.items():
        out.append(f"  {title} ({rep['cases'][t]} cases, {rep['unsolved'][t]} not solved by "
                   "Response after the change and counted outside):")
        for p, (n, of) in rep["totals"][t].items():
            out.append(f"    priority {p}: {pct(n, of)}"
                       + (f"; threshold {th[t][p]:g} %" if p in th[t] else "; reported only"))
    return "\n".join(out)


def check_repeat(rep: dict) -> None:
    """Totals only. Raises ValueError."""
    if set(rep) != {"what", "date", "by_per_cent", "cases", "totals", "unsolved"}:
        raise ValueError("fields other than the totals'")
    if set(rep["cases"]) != set(AREA_TITLES) or set(rep["unsolved"]) != set(AREA_TITLES):
        raise ValueError("areas other than the two")
    for t, by in rep["totals"].items():
        for p, v in by.items():
            if not (t in AREA_TITLES and p in "1234" and len(v) == 2
                    and all(isinstance(x, int) for x in v) and 0 <= v[0] <= v[1]):
                raise ValueError(f"{t} priority {p} is not a total")


def pct(n: int, of: int) -> str:
    return f"{n} of {of} ({100.0 * n / of:.0f} %)" if of else "none"


def text_totals(run: dict) -> str:
    out = [f"Held-out totals, {run['label']}, {run['date']}, r2c at {run['commit']}: cases "
           "inside target on every check of the priority"]
    for t, title in AREA_TITLES.items():
        out.append(f"  {title} ({run['cases'][t]} cases, {run['unsolved'][t]} not solved by "
                   "r2c and counted outside):")
        for p, (n, of) in run["totals"][t].items():
            whole = run.get("uncut", {}).get(t, {}).get(p)
            out.append(f"    priority {p}: " + (f"{pct(*whole)} with no case cut; " if whole
                                                 and whole != [n, of] else "") + pct(n, of))
    return "\n".join(out)


# ---------------------------------------------------------------------------------------
# the committed totals
# ---------------------------------------------------------------------------------------

def read_totals(path: Path = TOTALS) -> dict:
    return json.loads(path.read_text()) if path.exists() else {"runs": []}


def check_totals(totals: dict) -> None:
    """Totals only: nothing but the fields a run's totals have. Raises ValueError."""
    if set(totals) != {"runs"}:
        raise ValueError("only \"runs\" is allowed at the top")
    for r in totals["runs"]:
        if set(r) - {"uncut"} != {"label", "date", "commit", "cases", "totals", "unsolved"}:
            raise ValueError(f"run {r.get('label')!r}: fields other than the totals'")
        if set(r["cases"]) != set(AREA_TITLES) or set(r["unsolved"]) != set(AREA_TITLES):
            raise ValueError(f"run {r['label']!r}: areas other than the two")
        for t, by in [*r["totals"].items(), *r.get("uncut", {}).items()]:
            for p, v in by.items():
                if not (t in AREA_TITLES and p in "1234" and len(v) == 2
                        and all(isinstance(x, int) for x in v) and 0 <= v[0] <= v[1]):
                    raise ValueError(f"run {r['label']!r}: {t} priority {p} is not a total")


def summary_block(totals: dict, rep: dict | None = None) -> str:
    """The totals of the last recorded runs, one column each (the trend), then Response's
    own score against itself and the threshold made from it, for docs/summary.md."""
    rep = read_repeat() if rep is None else rep
    th = thresholds(rep)
    runs = totals["runs"][-3:]
    out = [BEGIN, "<!-- Generated by tools/heldout.py summary. Do not edit: rerun it. -->", "",
           "Cases inside target on every check of the priority, of the cases that have such "
           "a check. One column per increment; then Response against itself (every concrete "
           f"strength raised by {REPEAT_BY:g} %) on the same inputs, and the threshold: that "
           f"score less {MARGIN:g} points (priority 1 without shear: 99 %, kept by the owner; "
           "priority 2 with shear is reported, not a target, since 2026-11-26).", "",
           "| Area | Priority | " + " | ".join(f"{r['label']} ({r['date']})" for r in runs)
           + " | Response against itself | Threshold |",
           "|---|---|" + "---:|" * (len(runs) + 2)]
    names = {"1": "1: peak, rising branch, shape; stress-state views",
             "2": "2: endings without shear; shear-related views",
             "3": "3: cracking-related views", "4": "4: endings with shear"}
    last = runs[-1]
    for t, title in AREA_TITLES.items():
        for p in ("1", "2", "3", "4"):
            if not any(p in r["totals"][t] for r in runs):
                continue
            cells = [pct(*r["totals"][t][p]) if p in r["totals"][t] else "" for r in runs]
            own = pct(*rep["totals"][t][p]) if rep and p in rep["totals"][t] else "not measured"
            if p in th[t]:
                n, of = last["totals"][t][p]
                met = "met" if of and 100.0 * n / of >= th[t][p] else "not met"
                goal = f"{th[t][p]:g} % ({met}{', kept by the owner' if p in KEPT.get(t, {}) else ''})"
            else:
                goal = ("reported only" if p == "4" or p in REPORTED.get(t, ()) or rep
                        else "not set")
            out.append(f"| {title} | {names[p]} | " + " | ".join(cells) + f" | {own} | {goal} |")
    out += ["", "Cases: " + ", ".join(
        f"{AREA_TITLES[t].lower()} {last['cases'][t]} ({last['unsolved'][t]} not solved by "
        "r2c, counted outside)" for t in AREA_TITLES) + ".", END]
    return "\n".join(out)


FBEGIN, FEND = "<!-- finish:begin -->", "<!-- finish:end -->"


def finish_block(first: dict, rep1: dict | None, finish: dict, rep2: dict | None) -> str:
    """The second set's totals beside the first set's (the finishing steps; owner,
    2026-11-26): for each area and priority, r2c on the first set at its last score, r2c
    on the second set at its only score, and Response against itself on each."""
    a, b = first["runs"][-1], finish["runs"][-1]
    names = {"1": "1: peak, rising branch, shape; stress-state views",
             "2": "2: endings without shear; shear-related views",
             "3": "3: cracking-related views", "4": "4: endings with shear"}
    th = thresholds(rep1)

    def own(rep, t, p):
        return pct(*rep["totals"][t][p]) if rep and p in rep["totals"][t] else "not measured"
    out = [FBEGIN, "<!-- Generated by tools/heldout.py summary. Do not edit: rerun it. -->", "",
           "Cases inside target on every check of the priority. The second set was scored "
           f"once, for the first time, at the finish ({b['date']}, r2c at {b['commit']}); "
           f"the first set's column is its last score ({a['label']}). Response against "
           f"itself: every concrete strength raised by {REPEAT_BY:g} %, on each set's own "
           "inputs. The threshold is the one made from the first set.", "",
           "| Area | Priority | First set: r2c | First set: Response against itself | "
           "Second set: r2c | Second set: Response against itself | Threshold |",
           "|---|---|---:|---:|---:|---:|---:|"]
    for t, title in AREA_TITLES.items():
        for p in ("1", "2", "3", "4"):
            if p not in a["totals"][t] and p not in b["totals"][t]:
                continue
            cell = lambda r: pct(*r["totals"][t][p]) if p in r["totals"][t] else ""
            goal = f"{th[t][p]:g} %" if p in th[t] else "reported only"
            out.append(f"| {title} | {names[p]} | {cell(a)} | {own(rep1, t, p)} | {cell(b)} | "
                       f"{own(rep2, t, p)} | {goal} |")
    out += ["", "Cases: first set " + ", ".join(
        f"{AREA_TITLES[t].lower()} {a['cases'][t]} ({a['unsolved'][t]} not solved by r2c)"
        for t in AREA_TITLES) + "; second set " + ", ".join(
        f"{AREA_TITLES[t].lower()} {b['cases'][t]} ({b['unsolved'][t]} not solved by r2c)"
        for t in AREA_TITLES) + ". A case not solved counts as outside.", FEND]
    return "\n".join(out)


RBEGIN, REND = "<!-- repeat:begin -->", "<!-- repeat:end -->"
SBEGIN, SEND = "<!-- standing:begin -->", "<!-- standing:end -->"


def standing_block(totals: dict, rep: dict | None) -> str:
    """r2c's standing on the measures that are reported and not targets (owner,
    2026-11-26): priority 2 with shear on the held-out set beside Response's own score, and
    r2c's time beside r2x's reading every stage, on the development cases (the committed
    results and tests/oracle/r2x-times.json; the held-out set keeps nothing per case)."""
    import dashboard   # here: dashboard imports this module
    last = totals["runs"][-1]
    out = [SBEGIN, "<!-- Generated by tools/heldout.py summary. Do not edit: rerun it. -->", ""]
    for t, ps in REPORTED.items():
        for p in ps:
            n, of = last["totals"][t][p]
            own = pct(*rep["totals"][t][p]) if rep and p in rep["totals"][t] else "not measured"
            out.append(f"- {AREA_TITLES[t]}, priority {p}, held-out set ({last['label']}, "
                       f"{last['date']}): r2c {pct(n, of)}; Response against itself {own}.")
    res = ROOT / "docs" / "verification-results.json"
    rows = [r for r in (dashboard.speed(dashboard.load_results(res)[1]) if res.exists() else [])
            if r["reads"] == "every stage"]
    for r in rows:
        out.append(f"- Speed, development cases {r['area'].lower()}, r2x reading every stage: "
                   f"r2c no slower on {r['within']} of {r['of']}; medians {r['r2c']:g} s "
                   f"(r2c) and {r['r2x']:g} s (r2x); the slowest case {r['worst']:g} times "
                   "r2x's.")
    if not rows:
        out.append("- Speed: not measured.")
    out += ["", SEND]
    return "\n".join(out)


def brief_block(rep: dict) -> str:
    """The measured values the owner asked to have in the brief, generated."""
    th = thresholds(rep)
    out = [RBEGIN, "<!-- Generated by tools/heldout.py summary. Do not edit: rerun it. -->", "",
           "| Area | Priority | Response against itself | Threshold |", "|---|---|---:|---:|"]
    for t, title in AREA_TITLES.items():
        for p, (n, of) in rep["totals"][t].items():
            out.append(f"| {title} | {p} | {pct(n, of)} | "
                       + ((f"{th[t][p]:g} %" + (" (kept by the owner, 2026-11-26)"
                                                  if p in KEPT.get(t, {}) else ""))
                          if p in th[t] else "reported only") + " |")
    out += ["", f"Measured {rep['date']}. Cases: " + ", ".join(
        f"{AREA_TITLES[t].lower()} {rep['cases'][t]} ({rep['unsolved'][t]} not solved by "
        "Response after the change, counted outside)" for t in AREA_TITLES) + ".", REND]
    return "\n".join(out)


def write_summary() -> int:
    totals = read_totals()
    if not totals["runs"]:
        raise SystemExit("heldout/totals.json has no run yet")
    text = SUMMARY.read_text(encoding="utf-8")
    block = summary_block(totals)
    finish = read_totals(FINISH_TOTALS)
    if BEGIN in text:
        text = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _m: block, text,
                      flags=re.S)
    elif not (finish["runs"] and FBEGIN in text):
        # the sign-off page has the two sets side by side in place of the trend
        raise SystemExit(f"docs/summary.md has no {BEGIN} ... {END} block to fill")
    if finish["runs"] and FBEGIN in text:
        fb = finish_block(totals, read_repeat(), finish, read_repeat(FINISH_REPEAT))
        text = re.sub(re.escape(FBEGIN) + r".*?" + re.escape(FEND), lambda _m: fb, text,
                      flags=re.S)
    SUMMARY.write_text(text, encoding="utf-8")
    print("docs/summary.md: totals block rewritten")
    rep = read_repeat()
    if rep is not None:
        brief = ROOT / "docs" / "brief.md"
        text = brief.read_text(encoding="utf-8")
        if RBEGIN not in text:
            raise SystemExit(f"docs/brief.md has no {RBEGIN} ... {REND} block to fill")
        text = re.sub(re.escape(RBEGIN) + r".*?" + re.escape(REND),
                      lambda _m: brief_block(rep), text, flags=re.S)
        if SBEGIN in text:
            text = re.sub(re.escape(SBEGIN) + r".*?" + re.escape(SEND),
                          lambda _m: standing_block(totals, rep), text, flags=re.S)
        brief.write_text(text, encoding="utf-8")
        print("docs/brief.md: the measured values of Response against itself and r2c's "
              "standing on the reported measures rewritten")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=("list", "build", "score", "repeat", "summary"))
    ap.add_argument("archive", nargs="?", help="the held-out archive (outside the repository)")
    ap.add_argument("--response-dir", default=os.environ.get("R2X_RESPONSE_DIR"))
    ap.add_argument("--inputs", nargs="*", default=[],
                    help="Response's folder and the folders with the development inputs")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--record", metavar="LABEL", nargs="?", const="repeat",
                    help="score: append the totals to heldout/totals.json under this label; "
                         "repeat: write the totals to heldout/repeatability.json")
    ap.add_argument("--kinds", action="store_true",
                    help="score: also print the cases outside target by kind (section type "
                         "and loading path), with no names or values")
    ap.add_argument("--set", choices=tuple(SETS), default="heldout",
                    help="the held-out set (the default) or the second one, for the "
                         "finish (scored since the owner started the finishing steps)")
    ap.add_argument("--dry-freeze", action="store_true",
                    help="build: capture, but do not write the manifest")
    a = ap.parse_args(argv)
    if a.action == "list":
        for c in SETS[a.set][0]:
            opts = " ".join(f"{k}={c[k]}" for k in ("units", "factors", "more_detail")
                            if c[k] not in ("si", "none", "0"))
            print(f"{c['name']}: {area(c)}: {what(c)}; {c['initial']} + {c['increment']}"
                  + (f"; {opts}" if opts else ""))
        return 0
    if a.action == "summary":
        return write_summary()
    if not a.archive:
        ap.error("ARCHIVE is required")
    return {"build": build, "score": score, "repeat": repeat}[a.action](a, ap)


if __name__ == "__main__":
    raise SystemExit(main())
