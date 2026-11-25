#!/usr/bin/env python3
"""Derive new input files from existing ones by stated text edits (the recipe for the inputs
of the scope cases; the inputs themselves stay out of the repository).

    python tools/variants.py OUT_DIR --inputs DIR [DIR ...] [--only NAME ...] [--list]

Each variant below names a base input (by SHA-256; found anywhere under --inputs, as
tools/verify.py finds inputs) and a list of edits. An edit replaces one piece of text by
another; the piece must occur exactly once in the base (or the stated number of times), or
the variant fails, so an edit can never silently miss. The result is written to OUT_DIR/NAME.r2t (CRLF line endings, as
Response writes them) and its SHA-256 printed; OUT_DIR must be outside the repository.

One feature per variant, on a section that is already in the test set, so that a difference
from Response points at that feature. What each variant is for is in its `what`; whether
Response accepts it is measured with tools/probe.py, not assumed.

The bases: r2x's tests/reference/newbeam/input.r2t (Newbeam, Response's File > New) and
tests/reference/define/quick-{tbeam,column,ibeam-strands}/hand.r2t.

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BASES = {
    "newbeam": "036440c79be86062dec63b0706c203efeb993961b9d2e40434e2fd44a64efcf6",
    "tbeam": "845cf02d122e",
    "column": "e9e813ddfdbe",
    "igirder": "62003de27673",
    # Response's own Save As of Newbeam in US units and with CSA factors (r2x's
    # tests/reference/newbeam-us/saved.r2t and newbeam-csa/saved.r2t): used as they are
    "newbeam-us-saved": "3397a57ebe57",
    "newbeam-csa-saved": "0e74ef3dd4dd",
}

T4 = "\r\n\t\t\t\t"   # a new attribute line inside an element, as Response lays it out


def attr(key: str, value: str) -> str:
    """An attribute as Response writes it: the key, one or two tabs, ="value"."""
    tabs = "\t\t" if len(key) < 6 else "\t"
    return f'{key}{tabs}="{value}"'


@dataclass
class Variant:
    base: str
    what: str
    edits: list[tuple] = field(default_factory=list)   # (old, new) or (old, new, count)
    # the loads the feature is probed and captured at (None: the file's own)
    initial: str | None = "0,0,0"
    increment: str | None = "0,1,1"


# pieces of the bases that the edits hang on (each occurs once in its base)
NB_CONC = attr("maxagg", "19.0") + "\t/>"                     # end of Newbeam's <concrete>
NB_BEAM = "<r3g_beam\t" + attr("date", "2026/10/24") + "\t>"  # Newbeam's <r3g_beam ...>
NB_STEEL1 = attr("eu", "100.0") + "\t/>\r\n\t\t<rebar\t\t"    # end of Newbeam's first <rebar>
NB_BOT = attr("A", "1500.0") + T4 + attr("bartitle", "25M") + "\t/>"
NB_STIRRUP = attr("pattern", "5")
NB_LOADING = "<sectloading\t\t/>"


def conc(key: str, value: str) -> list[tuple[str, str]]:
    """Add one attribute to Newbeam's concrete."""
    return [(NB_CONC, attr("maxagg", "19.0") + T4 + attr(key, value) + "\t/>")]


def rows(pairs, indent="\t\t\t\t\t") -> str:
    return "".join(f"\r\n{indent}{a} {b}" for a, b in pairs)


# A segmental concrete curve for 35 MPa: strain (mm/m), stress (MPa). Hognestad's parabola to
# the peak at 2.0 mm/m, then a straight fall to 20 MPa at 4.0 mm/m (the numbers are the
# developer's, chosen to differ visibly from the default curve).
SEG_CONCRETE = [("0.000", "0.00"), ("0.250", "8.20"), ("0.500", "15.31"), ("0.750", "21.33"),
                ("1.000", "26.25"), ("1.250", "30.08"), ("1.500", "32.81"), ("1.750", "34.45"),
                ("2.000", "35.00"), ("3.000", "27.50"), ("4.000", "20.00")]
# A segmental steel curve: strain (mm/m), stress (MPa). Round-house curve without a yield
# plateau, 400 MPa at 2 mm/m rising to 600 MPa at 80 mm/m (the developer's numbers).
SEG_STEEL = [("0.000", "0.0"), ("2.000", "400.0"), ("10.000", "450.0"), ("30.000", "540.0"),
             ("80.000", "600.0"), ("100.000", "600.0")]

SOFTENING = {0: "None", 1: "Vecchio-Collins 1982", 2: "Vecchio-Collins 1986",
             3: "Vecchio-Collins 1992-A", 4: "(unsupported method)",
             5: "Vecchio-Collins 1992-B", 6: "Mehlhorn et al", 7: "Maekawa et al",
             8: "Noguchi et al", 9: "Belarbi-Hsu proportional", 10: "CAN CSA A23.3 M84",
             11: "Collins 1978 (CFT)", 12: "Kaufmann-Marti 1998", 13: "Porasz-Collins 1988",
             14: "Zhang-Hsu 1998 (with eta)", 15: "Hsu 1993", 16: "Zhu-Hsu-Lee 2001",
             17: "Zhang-Hsu 1998 (no eta)", 18: "Collins-Bentz 2011 (default)"}
STIFFENING = {0: "None", 1: "Vecchio-Collins 1982", 2: "Collins-Mitchell 1987",
              3: "Izumo et al", 4: "Tamai et al 1987", 5: "(Stuart Oliver: no longer supported)",
              6: "Elasto-Plastic", 7: "Bentz 1999 (default)"}
BASE_CURVE = {0: "Linear", 1: "Parabolic", 2: "Popovics/Thorenfeldt/Collins (default)",
              3: "Elasto-Plastic", 4: "Segmental (user-defined)"}

VARIANTS: dict[str, Variant] = {}

for n, title in BASE_CURVE.items():
    if n in (2, 4):
        continue
    VARIANTS[f"newbeam-cmod{n}"] = Variant("newbeam", f"concrete base curve {n}: {title}",
                                           conc("c_mod", str(n)))
VARIANTS["newbeam-cmod4"] = Variant(
    "newbeam", "concrete base curve 4: segmental, with a curve of 11 points",
    [(NB_CONC, attr("maxagg", "19.0") + T4 + attr("c_mod", "4") + "\t>"
      + rows(SEG_CONCRETE) + "\r\n\t\t\t</concrete>")])
for n, title in SOFTENING.items():
    if n == 18:
        continue
    VARIANTS[f"newbeam-csoft{n}"] = Variant("newbeam", f"compression softening {n}: {title}",
                                            conc("c_soft", str(n)))
for n, title in STIFFENING.items():
    if n == 7:
        continue
    VARIANTS[f"newbeam-tstiff{n}"] = Variant("newbeam", f"tension stiffening {n}: {title}",
                                             conc("t_stiff", str(n)))
VARIANTS["newbeam-tsfactor"] = Variant("newbeam", "tension stiffening factor 0.5",
                                       conc("tsfactor", "0.50"))
VARIANTS["newbeam-ft"] = Variant("newbeam", "tensile strength given: 3.00 MPa (auto 1.89)",
                                 [(attr("fcp", "35.0"), attr("fcp", "35.0") + T4
                                   + attr("ft", "3.00"))])
VARIANTS["newbeam-e0"] = Variant("newbeam", "strain at peak stress given: 2.60 mm/m (auto 2.03)",
                                 [(attr("fcp", "35.0"), attr("fcp", "35.0") + T4
                                   + attr("e0", "2.60"))])
VARIANTS["newbeam-segsteel"] = Variant(
    "newbeam", "segmental curve for the longitudinal steel (Steel 1), 6 points",
    [(NB_STEEL1, attr("eu", "100.0") + "\t>" + rows(SEG_STEEL)
      + "\r\n\t\t\t</rebar>\r\n\t\t<rebar\t\t")])
VARIANTS["newbeam-nooutline"] = Variant(
    "newbeam", "shape RECT given without an outline (<sectionSOLID> removed)",
    [("\t\t<sectionSOLID\t\t>\r\n\t\t\t\t\t600.0\t250.0\r\n\t\t\t\t\t0.0\t250.0\t\"Concrete 1\""
      "\r\n\t\t\t</sectionSOLID>\r\n", "")])
VARIANTS["newbeam-negelev"] = Variant(
    "newbeam", "outline given from -100 to 500 mm (negative elevation), everything 100 lower",
    [("600.0\t250.0\r\n\t\t\t\t\t0.0\t250.0", "500.0\t250.0\r\n\t\t\t\t\t-100.0\t250.0"),
     (attr("z", "538.95"), attr("z", "438.95")), (attr("z", "63.90"), attr("z", "-36.10")),
     (attr("disttop", "554.3"), attr("disttop", "454.3")),
     (attr("distbot", "45.7"), attr("distbot", "-54.3"))])
VARIANTS["newbeam-nostirrups"] = Variant(
    "newbeam", "no transverse reinforcement (<transreinfz> removed)",
    [("\t\t<transreinfz\t" + attr("A", "100.0") + T4 + attr("type", "Trans") + T4
      + attr("pattern", "5") + T4 + attr("space", "250.0") + T4 + attr("disttop", "554.3")
      + T4 + attr("distbot", "45.7") + T4 + attr("bartitle", "10M") + T4
      + attr("name", "stirrup") + "\t/>\r\n", "")])
for n, title in ((1, "single leg"), (2, "open stirrup"), (3, "closed stirrup"), (4, "hoop"),
                 (6, "interlocking hoops"), (7, "horizontal tie")):
    VARIANTS[f"newbeam-pattern{n}"] = Variant(
        "newbeam", f"stirrup pattern {n} ({title}) in place of 5 (T-headed single leg), "
        "same area", [(NB_STIRRUP, attr("pattern", str(n)))])
VARIANTS["newbeam-stirrupdep"] = Variant(
    "newbeam", "prestrain of 1.0 mm/m on the stirrups (dep)",
    [(attr("bartitle", "10M"), attr("bartitle", "10M") + T4 + attr("dep", "1.00"))])
VARIANTS["newbeam-bardep"] = Variant(
    "newbeam", "prestrain of 1.0 mm/m on the bottom bars (dep on non-prestressed steel)",
    [(NB_BOT, attr("A", "1500.0") + T4 + attr("bartitle", "25M") + T4 + attr("dep", "1.00")
      + "\t/>")])
VARIANTS["newbeam-longpattern2"] = Variant(
    "newbeam", "bottom layer marked as part of a distributed pattern (pattern 2)",
    [(NB_BOT, attr("A", "1500.0") + T4 + attr("bartitle", "25M") + T4 + attr("pattern", "2")
      + T4 + attr("index", "1") + "\t/>")])
VARIANTS["newbeam-barspace"] = Variant(
    "newbeam", "bar spacing given on the bottom layer (space 60 mm)",
    [(NB_BOT, attr("A", "1500.0") + T4 + attr("space", "60.0") + T4 + attr("bartitle", "25M")
      + "\t/>")])
VARIANTS["newbeam-smx"] = Variant(
    "newbeam", "crack spacings given: longitudinal 300 mm, transverse 200 mm",
    [(NB_BEAM, "<r3g_beam\t" + attr("date", "2026/10/24") + "\r\n\t\t\t" + attr("smx", "300.0")
      + "\r\n\t\t\t" + attr("smt", "200.0") + "\t>")])
VARIANTS["newbeam-axialloc"] = Variant(
    "newbeam", "moment axis given at 200 mm above the bottom (centroid: 300 mm)",
    [(NB_BEAM, "<r3g_beam\t" + attr("date", "2026/10/24") + "\r\n\t\t\t"
      + attr("axialloc", "200.0") + "\t>")])
VARIANTS["newbeam-shrink"] = Variant(
    "newbeam", "shrinkage of -0.40 mm/m over the depth (<shrinktherm>)",
    [("\t\t" + NB_LOADING, "\t\t<shrinktherm\t\t>" + rows([("600.0", "-0.400"),
                                                           ("  0.0", "-0.400")])
      + "\r\n\t\t\t</shrinktherm>\r\n\t\t" + NB_LOADING)])
VARIANTS["newbeam-thermgrad"] = Variant(
    "newbeam", "thermal gradient: +0.30 mm/m at the top, 0 at mid-depth and below "
    "(<shrinktherm>)",
    [("\t\t" + NB_LOADING, "\t\t<shrinktherm\t\t>" + rows([("600.0", "0.300"),
                                                           ("300.0", "0.000"),
                                                           ("  0.0", "0.000")])
      + "\r\n\t\t\t</shrinktherm>\r\n\t\t" + NB_LOADING)])
VARIANTS["newbeam-bartherm"] = Variant(
    "newbeam", "thermal strain of 0.50 mm/m on the bottom bars (<rebarthermx>)",
    [("\t\t" + NB_LOADING, "\t\t" + NB_LOADING + "\r\n\t\t<rebarthermx\t\t>"
      + "\r\n\t\t\t\t\t\"bot\" 0.500\r\n\t\t\t</rebarthermx>")])
VARIANTS["newbeam-discont"] = Variant(
    "newbeam", "strain discontinuity of 0.20 mm/m above 400 mm (<straindiscont>; out of scope "
    "by design: probed to see what Response does)",
    [("\t\t" + NB_LOADING, "\t\t" + NB_LOADING + "\r\n\t\t<straindiscont\t\t>"
      + rows([("600.0", "0.200"), ("400.0", "0.200"), ("400.0", "0.000"), ("  0.0", "0.000")])
      + "\r\n\t\t\t</straindiscont>")])
VARIANTS["newbeam-fire"] = Variant(
    "newbeam", "<firedata> present (type 1, 1800 s)",
    [("\t\t" + NB_LOADING, "\t\t" + NB_LOADING + "\r\n\t\t<firedata\t" + attr("type", "1") + T4
      + attr("exposure", "7") + T4 + attr("time", "1800") + "\t/>")])
VARIANTS["newbeam-longterm"] = Variant(
    "newbeam", "time dependent effects switched on (<analysisoptions longterm>; out of scope "
    "by design: probed to see what Response does)",
    [("\t\t" + NB_LOADING, "\t\t" + NB_LOADING + "\r\n\t\t<analysisoptions\t"
      + attr("longterm", "1") + T4 + attr("sustainM", "100.0") + T4 + attr("age", "1000.0")
      + "\t/>")])
VARIANTS["newbeam-clamp"] = Variant(
    "newbeam", "<analysisoptions clamp=1> (meaning not documented)",
    [("\t\t" + NB_LOADING, "\t\t" + NB_LOADING + "\r\n\t\t<analysisoptions\t"
      + attr("clamp", "1") + "\t/>")])
VARIANTS["newbeam-roman"] = Variant(
    "newbeam", "units=roman (the schema lists it; not offered by r2x)",
    [(NB_BEAM, "<r3g_beam\t" + attr("date", "2026/10/24") + "\r\n\t\t\t"
      + attr("units", "roman") + "\t>")])
VARIANTS["newbeam-loads"] = Variant(
    "newbeam", "loads in the file: N -500 kN constant, increments M 1.5 : V 1",
    [(NB_LOADING, "<sectloading\t" + attr("BN", "-500.0") + T4 + attr("MM", "1.5") + T4
      + attr("MV", "1.0") + "\t/>")])

# Newbeam in kg-cm units: the values Response's own Save As writes after its units are set to
# "kg/cm Metric" (measured with r2x: `python -m r2x.worker define units`, answer "kg/cm
# Metric"): cm, cm2, kg/cm2 for concrete, t/cm2 for steel, each rounded as Response rounds it
# (fy 4.1 t/cm2 is 402 MPa), so this is a slightly different section from Newbeam, as r2x's
# newbeam-us/saved.r2t is in US units.
VARIANTS["newbeam-kgcmfile"] = Variant(
    "newbeam", "the input file in kg-cm units (units=oldmetric), values as Response saves them",
    [(NB_BEAM, "<r3g_beam\t" + attr("date", "2026/10/24") + "\r\n\t\t\t"
      + attr("units", "oldmetric") + "\t>"),
     (attr("fcp", "35.0"), attr("fcp", "356.8")), (attr("maxagg", "19.0"), attr("maxagg", "1.9")),
     (attr("fy", "400.0") + T4 + attr("esh", "7.0"),
      attr("fy", "4.1") + T4 + attr("E", "2041") + T4 + attr("fu", "6.1") + T4
      + attr("esh", "7.0"), 2),
     (attr("fu", "1860.0") + "\t/>", attr("fu", "19.0") + T4 + attr("E", "2041") + "\t/>"),
     ("600.0\t250.0\r\n\t\t\t\t\t0.0\t250.0", "60.0\t25.0\r\n\t\t\t\t\t0.0\t25.0"),
     (attr("par1", "250.0"), attr("par1", "25.0")), (attr("par2", "600.0"), attr("par2", "60.0")),
     (attr("z", "538.95"), attr("z", "53.90")), (attr("A", "300.0"), attr("A", "3.0")),
     (attr("z", "63.90"), attr("z", "6.39")), (attr("A", "1500.0"), attr("A", "15.0")),
     (attr("A", "100.0"), attr("A", "1.0")), (attr("space", "250.0"), attr("space", "25.0")),
     (attr("disttop", "554.3"), attr("disttop", "55.4")),
     (attr("distbot", "45.7"), attr("distbot", "4.6")),
     (NB_LOADING, "<sectloading\t" + attr("MM", "0.102") + "\t/>")])

# the I-girder with strands (60 MPa, 150 mm web): where the web's compression matters
IG_CONC = attr("fcp", "60.0") + T4 + attr("maxagg", "19.0") + "\t/>"
for n, title in SOFTENING.items():
    if n == 18:
        continue
    VARIANTS[f"igirder-csoft{n}"] = Variant(
        "igirder", f"compression softening {n}: {title}",
        [(IG_CONC, attr("fcp", "60.0") + T4 + attr("maxagg", "19.0") + T4
          + attr("c_soft", str(n)) + "\t/>")], increment="0,2,1")
VARIANTS["igirder-drape"] = Variant(
    "igirder", "the lower tendon layer draped at 0.05 (rise over run)",
    [(attr("dep", "6.50") + T4 + attr("name", "pbot") + "\t/>",
      attr("drape", "0.05") + T4 + attr("dep", "6.50") + T4 + attr("name", "pbot") + "\t/>")],
    increment="0,2,1")
# A segmental curve for the strand: strain (mm/m), stress (MPa); the developer's numbers
SEG_STRAND = [("0.000", "0.0"), ("7.000", "1400.0"), ("9.000", "1650.0"), ("12.000", "1780.0"),
              ("20.000", "1830.0"), ("43.000", "1860.0")]
VARIANTS["igirder-segstrand"] = Variant(
    "igirder", "segmental curve for the prestressing steel (Low Relax), 6 points",
    [("<prestress\t" + attr("fu", "1860.0") + "\t/>", "<prestress\t" + attr("fu", "1860.0")
      + "\t>" + rows(SEG_STRAND) + "\r\n\t\t\t</prestress>")], increment="0,1,0")

# the circular column: the outline as a circle of two curved segments
COLUMN_ROWS = ("\t\t\t\t\t600.0\t0.1\r\n\t\t\t\t\t589.8\t155.3\t\"Concrete 1\"\r\n"
               "\t\t\t\t\t559.8\t300.0\t\"Concrete 1\"\r\n\t\t\t\t\t512.1\t424.3\t\"Concrete 1\"\r\n"
               "\t\t\t\t\t450.0\t519.6\t\"Concrete 1\"\r\n\t\t\t\t\t377.6\t579.6\t\"Concrete 1\"\r\n"
               "\t\t\t\t\t300.0\t600.0\t\"Concrete 1\"\r\n\t\t\t\t\t222.4\t579.6\t\"Concrete 1\"\r\n"
               "\t\t\t\t\t150.0\t519.6\t\"Concrete 1\"\r\n\t\t\t\t\t87.9\t424.3\t\"Concrete 1\"\r\n"
               "\t\t\t\t\t40.2\t300.0\t\"Concrete 1\"\r\n\t\t\t\t\t10.2\t155.3\t\"Concrete 1\"\r\n"
               "\t\t\t\t\t0.0\t0.1\t\"Concrete 1\"\r\n")
VARIANTS["column-curved"] = Variant(
    "column", "the circle as two curved segments: lone UP and DOWN lines between three rows "
    "(the form of shape.dat)",
    [(COLUMN_ROWS, "\t\t\t\t\t600.0\t0.0\r\n\t\t\t\t\tUP\r\n\t\t\t\t\t300.0\t600.0\t\"Concrete 1\""
      "\r\n\t\t\t\t\tDOWN\r\n\t\t\t\t\t0.0\t0.0\t\"Concrete 1\"\r\n")])
VARIANTS["column-curvedwidth"] = Variant(
    "column", "the circle as curved segments given as rows with a width of UP or DOWN (the "
    "form of the manual, section 2-4)",
    [(COLUMN_ROWS, "\t\t\t\t\t600.0\t0.0\r\n\t\t\t\t\t450.0\tUP\r\n\t\t\t\t\t300.0\t600.0\t"
      "\"Concrete 1\"\r\n\t\t\t\t\t150.0\tDOWN\r\n\t\t\t\t\t0.0\t0.0\t\"Concrete 1\"\r\n")])
VARIANTS["column-nooutline"] = Variant(
    "column", "shape CIRCLE given without an outline (<sectionSOLID> removed)",
    [("\t\t<sectionSOLID\t\t>\r\n" + COLUMN_ROWS + "\t\t\t</sectionSOLID>\r\n", "")])
VARIANTS["column-interlock"] = Variant(
    "column", "stirrup pattern 6 (interlocking hoops) in place of 4 (hoop)",
    [(attr("pattern", "4"), attr("pattern", "6"))])
VARIANTS["tbeam-nooutline"] = Variant(
    "tbeam", "shape TBEAM given without an outline (<sectionSOLID> removed)",
    [("\t\t<sectionSOLID\t\t>\r\n\t\t\t\t\t1200.0\t900.0\r\n\t\t\t\t\t1000.0\t900.0\t"
      "\"Concrete 1\"\r\n\t\t\t\t\t1000.0\t300.0\r\n\t\t\t\t\t0.0\t300.0\t\"Concrete 1\"\r\n"
      "\t\t\t</sectionSOLID>\r\n", "")])


# loads: flexure alone where the feature is a matter of flexure; the file's own for "loads"
for _n in ("newbeam-cmod0", "newbeam-cmod1", "newbeam-cmod3", "newbeam-cmod4", "newbeam-e0",
           "newbeam-segsteel", "newbeam-nooutline", "newbeam-negelev", "newbeam-bardep",
           "newbeam-bartherm", "newbeam-shrink", "newbeam-thermgrad", "newbeam-discont",
           "newbeam-longterm", "tbeam-nooutline"):
    VARIANTS[_n].increment = "0,1,0"
for _n in ("column-curved", "column-curvedwidth", "column-nooutline"):
    VARIANTS[_n].initial, VARIANTS[_n].increment = "-4000,0,0", "0,1,0"
VARIANTS["newbeam-axialloc"].initial, VARIANTS["newbeam-axialloc"].increment = \
    "-1000,0,0", "0,1,0"
VARIANTS["newbeam-loads"].initial = VARIANTS["newbeam-loads"].increment = None


for _n in ("igirder-csoft9", "igirder-csoft11"):
    # at M/V = 2 m r2x fails on these two ("Response has more than the N stages on its
    # control curves", measured 2026-11-21); at M/V = 1 m it solves them
    VARIANTS[_n].increment = "0,1,1"

# existing inputs used as they are (no edits): files in other units and with factors, and
# Newbeam under loads no case has yet
VARIANTS["newbeam-usfile"] = Variant(
    "newbeam-us-saved", "an input file in US units (Response's own Save As of Newbeam)")
VARIANTS["newbeam-csafile"] = Variant(
    "newbeam-csa-saved", "material factors in the file (<analysisoptions>; Response's own "
    "Save As of Newbeam with CSA factors)")
for _n, _ini, _inc, _what in (
        ("v0-m", "0,0,50", "0,1,0", "constant shear, moment increasing"),
        ("m0neg-mv", "0,-50,0", "0,1,1", "constant negative moment, moment and shear increasing"),
        ("nmv", "0,0,0", "-5,1,1", "axial load, moment and shear increasing together"),
        ("ntension-m", "200,0,0", "0,1,0", "constant tension, moment increasing"),
        ("ncomp-v", "-500,0,0", "0,0,1", "constant compression, shear increasing alone"),
        ("ntension-mv", "200,0,0", "0,1,1", "constant tension, moment and shear increasing"),
        ("m0-v", "0,100,0", "0,0,1", "constant moment, shear increasing alone"),
        ("nv", "0,0,0", "-1,0,0.1", "axial load and shear increasing together")):
    VARIANTS[f"newbeam-loads-{_n}"] = Variant("newbeam", "loads: " + _what, [], _ini, _inc)


# ---------------------------------------------------------------------------------------
# Wider development cases (increment 2): the kinds of variation the held-out set draws on
# (materials, shapes, reinforcement), with numbers of their own. None is a held-out case:
# tools/heldout.py's recipes use other values.
# ---------------------------------------------------------------------------------------

def _sub(key, old, new, count=None):
    e = (attr(key, old), attr(key, new))
    return e + (count,) if count else e


_OUTLINE = "600.0\t250.0\r\n\t\t\t\t\t0.0\t250.0"
_STIRRUPS = ("\t\t<transreinfz\t" + attr("A", "100.0") + T4 + attr("type", "Trans") + T4
             + attr("pattern", "5") + T4 + attr("space", "250.0") + T4
             + attr("disttop", "554.3") + T4 + attr("distbot", "45.7") + T4
             + attr("bartitle", "10M") + T4 + attr("name", "stirrup") + "\t/>\r\n")
_TOP_END = attr("bartitle", "20M") + T4 + attr("name", "top") + "\t/>\r\n"

VARIANTS["newbeam-fc20"] = Variant("newbeam", "Newbeam with 20 MPa concrete",
                                   [_sub("fcp", "35.0", "20.0")])
VARIANTS["newbeam-fc50"] = Variant("newbeam", "Newbeam with 50 MPa concrete",
                                   [_sub("fcp", "35.0", "50.0")])
VARIANTS["newbeam-fc80"] = Variant("newbeam", "Newbeam with 80 MPa concrete, 10 mm aggregate",
                                   [_sub("fcp", "35.0", "80.0"), _sub("maxagg", "19.0", "10.0")])
VARIANTS["newbeam-fy600"] = Variant("newbeam", "Newbeam with 600 MPa steel throughout",
                                    [_sub("fy", "400.0", "600.0", 2)])
VARIANTS["newbeam-deep900"] = Variant(
    "newbeam", "a deep beam, 350 x 900 mm, 2000 mm2 bottom steel, stirrups at 150 mm",
    [(_OUTLINE, "900.0\t350.0\r\n\t\t\t\t\t0.0\t350.0"), _sub("par1", "250.0", "350.0"),
     _sub("par2", "600.0", "900.0"), _sub("z", "538.95", "838.95"),
     _sub("A", "1500.0", "2000.0"), _sub("space", "250.0", "150.0"),
     _sub("disttop", "554.3", "854.3")])
VARIANTS["newbeam-slab200"] = Variant(
    "newbeam", "a slab strip, 1000 x 200 mm, no stirrups",
    [(_OUTLINE, "200.0\t1000.0\r\n\t\t\t\t\t0.0\t1000.0"), _sub("par1", "250.0", "1000.0"),
     _sub("par2", "600.0", "200.0"), _sub("z", "538.95", "160.00"), _sub("A", "300.0", "400.0"),
     _sub("z", "63.90", "40.00"), (_STIRRUPS, "")])
VARIANTS["newbeam-light800"] = Variant("newbeam", "Newbeam with 800 mm2 bottom steel",
                                       [_sub("A", "1500.0", "800.0")])
VARIANTS["newbeam-heavy2500"] = Variant("newbeam", "Newbeam with 2500 mm2 bottom, 800 mm2 top",
                                        [_sub("A", "1500.0", "2500.0"), _sub("A", "300.0", "800.0")])
VARIANTS["newbeam-st150"] = Variant("newbeam", "Newbeam with stirrups at 150 mm",
                                    [_sub("space", "250.0", "150.0")])
VARIANTS["newbeam-st2leg200"] = Variant(
    "newbeam", "Newbeam with closed stirrups of 200 mm2 at 200 mm",
    [_sub("A", "100.0", "200.0"), _sub("pattern", "5", "3"), _sub("space", "250.0", "200.0")])
VARIANTS["newbeam-mid400"] = Variant(
    "newbeam", "Newbeam with a third layer of steel, 400 mm2 at 250 mm",
    [(_TOP_END, _TOP_END + "\t\t<longreinfx\t" + attr("z", "250.00") + T4
      + attr("type", "Steel 1") + T4 + attr("num", "2") + T4 + attr("A", "400.0") + T4
      + attr("bartitle", "15M") + T4 + attr("name", "mid") + "\t/>\r\n")])
VARIANTS["tbeam-fc30"] = Variant("tbeam", "the T-beam with 30 MPa concrete, stirrups at 200 mm",
                                 [_sub("fcp", "40.0", "30.0"), _sub("space", "300.0", "200.0")])
VARIANTS["column-fc35"] = Variant("column", "the column with 35 MPa concrete, hoops at 150 mm",
                                  [_sub("fcp", "50.0", "35.0"), _sub("space", "300.0", "150.0")])
VARIANTS["igirder-dep5"] = Variant("igirder", "the I-girder, strands prestrained to 5.00 mm/m",
                                   [_sub("dep", "6.50", "5.00", 2)])
VARIANTS["igirder-fc45"] = Variant("igirder", "the I-girder with 45 MPa concrete",
                                   [_sub("fcp", "60.0", "45.0")])


def find_base(key: str, folders) -> Path:
    digest = BASES[key]
    for d in folders:
        for p in sorted(Path(d).rglob("*")):
            if p.is_file() and p.suffix.lower() in (".rsp", ".r2t") and \
                    hashlib.sha256(p.read_bytes()).hexdigest().startswith(digest):
                return p
    raise SystemExit(f"base {key} ({digest[:12]}…) not found under --inputs")


def build(name: str, folders) -> bytes:
    v = VARIANTS[name]
    text = find_base(v.base, folders).read_bytes().decode("ascii")
    for old, new, *count in v.edits:
        n = text.count(old)
        if n != (count[0] if count else 1):
            raise SystemExit(f"{name}: the text to replace occurs {n} times in the base, not "
                             f"{count[0] if count else 1}: {old!r}")
        text = text.replace(old, new)
    return text.encode("ascii")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", nargs="?", help="folder for the inputs (outside the repository)")
    ap.add_argument("--inputs", nargs="*", default=[], help="folders with the base inputs")
    ap.add_argument("--only", nargs="*", help="variant names (default: all)")
    ap.add_argument("--list", action="store_true", help="list the variants and stop")
    a = ap.parse_args(argv)
    names = a.only or list(VARIANTS)
    if a.list:
        for n in names:
            print(f"{n}: {VARIANTS[n].base}: {VARIANTS[n].what}")
        return 0
    if not a.out:
        ap.error("OUT_DIR is required")
    out = Path(a.out).resolve()
    if ROOT in out.parents or out == ROOT:
        ap.error("the inputs belong outside the repository")
    out.mkdir(parents=True, exist_ok=True)
    for n in names:
        data = build(n, a.inputs)
        (out / f"{n}.r2t").write_bytes(data)
        print(f"{hashlib.sha256(data).hexdigest()}  {n}.r2t")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
