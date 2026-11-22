"""Reading a section from a Response-2000 input file (.rsp or .r2t, the r3g XML schema).

The schema is Response's own (r3g.dtd, shipped with it). Everything is converted to one set of
internal units on the way in: mm, MPa, N, strains as plain numbers. `units.py` converts back for
the results.

Standard library only.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from r2c import bars
from r2c.units import FILE_UNITS, Units


class InputError(ValueError):
    """The input cannot be read as a Response-2000 section."""


class OutOfScope(ValueError):
    """The input asks for something r2c does not implement."""


# Compression softening numbers a file can carry that Response-2000's manual (Table 2-1) does
# not list: 4 has no name in Response's dialogs, 16 and 17 came after the manual
# (docs/scope.md 1.2; docs/summary.md D10, D18)
UNDOCUMENTED_SOFTENING = (4, 16, 17)
# The Hsu models, which Response runs in another mode with Tamai tension stiffening (D5)
HSU_SOFTENING = (9, 14, 15)
# A stirrup pattern a file can carry that the manual's list (A-27) does not have (D23)
HORIZONTAL_TIE = 7


@dataclass
class Concrete:
    name: str = "Concrete 1"
    fcp: float = 40.0            # MPa
    ft: float | None = None      # MPa, None = automatic
    e0: float | None = None      # strain at peak stress (plain), None = automatic
    tsfactor: float = 1.0
    maxagg: float = 19.0         # mm
    c_mod: int = 2               # base curve: 0 linear, 1 parabolic, 2 Popovics, 3 elastic-plastic, 4 segmental
    c_soft: int = 18             # compression softening model number
    t_stiff: int = 7             # tension stiffening model number
    segments: list[tuple[float, float]] = field(default_factory=list)   # (strain, MPa)


@dataclass
class Rebar:
    name: str = "Steel 1"
    fy: float = 400.0
    E: float = 200000.0
    fu: float = 600.0
    esh: float = 0.015
    eu: float = 0.080
    prestress: bool = False
    # Ramberg-Osgood (prestress only)
    A: float = 0.025
    B: float = 118.0
    C: float = 10.0


@dataclass
class LongLayer:
    name: str
    z: float                 # mm above the bottom of the section
    type: str                # material name
    area: float              # total area, mm2
    num: float               # number of bars
    db: float                # bar diameter, mm
    dep: float = 0.0         # prestrain (plain strain)
    space: float = 0.0
    bartitle: str = ""
    pattern: int = 0
    thermal: float = 0.0     # thermal strain of the bars (plain strain)


@dataclass
class TransLayer:
    name: str
    type: str
    area: float              # area of all legs per spacing, mm2
    space: float             # mm
    disttop: float           # mm above the bottom
    distbot: float           # mm above the bottom
    pattern: int = 0         # 0 single leg, 1 open, 2 closed, 3 hoop, 4 T-headed, ...
    db: float = 11.3
    dep: float = 0.0
    bartitle: str = ""


@dataclass
class Loading:
    constant: tuple[float, float, float] = (0.0, 0.0, 0.0)    # N (N), M (N mm), V (N)
    increment: tuple[float, float, float] = (0.0, 1.0, 0.0)   # ratios (N : M : V in file units)


@dataclass
class SectionInput:
    name: str = "New Cross Section"
    units: str = "si"
    smx: float = -1.0            # longitudinal crack spacing (mm), -1 = automatic
    smt: float = -1.0            # transverse crack spacing (mm), -1 = automatic
    axialloc: float = -1.0       # mm above the bottom where N acts; -1 = centroid
    concretes: list[Concrete] = field(default_factory=list)
    rebars: list[Rebar] = field(default_factory=list)
    # outline: (elevation mm, width mm, concrete name) from the top down, straight between rows
    outline: list[tuple[float, float, str]] = field(default_factory=list)
    hollow: list[tuple[float, float, str]] = field(default_factory=list)
    longs: list[LongLayer] = field(default_factory=list)
    trans: list[TransLayer] = field(default_factory=list)
    loading: Loading = field(default_factory=Loading)
    shrink: list[tuple[float, float]] = field(default_factory=list)       # (elev mm, strain)
    discont: list[tuple[float, float]] = field(default_factory=list)      # (elev mm, strain)
    phic: float = 1.0
    phis: float = 1.0
    phip: float = 1.0
    longterm: bool = False

    def material(self, name: str) -> Rebar:
        for r in self.rebars:
            if r.name.lower() == name.lower():
                return r
        raise InputError(f"reinforcement type {name!r} is not defined")

    def concrete(self, name: str | None) -> Concrete:
        if name:
            for c in self.concretes:
                if c.name.lower() == name.lower():
                    return c
        return self.concretes[0]


_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_TOKEN = re.compile(r'"[^"]*"|\S+')


def _f(el, key, default):
    v = el.get(key)
    if v is None:
        return default
    try:
        return float(v)
    except ValueError:
        raise InputError(f"<{el.tag}> {key}={v!r} is not a number") from None


def _units_of(text: str | None) -> str:
    known = {"metric": "si", "us": "us", "oldmetric": "kgcm"}
    if not text:
        return "si"
    if text.lower() not in known:
        # the schema also lists "roman"; Response reads such a file in a unit system its own
        # Preferences do not offer (docs/scope.md 1.1)
        raise InputError(f"units={text!r}: the units of an input are metric, US or oldmetric")
    return known[text.lower()]


def default_section() -> SectionInput:
    """The section File > New gives in Response-2000 (Quick Define's defaults, 'Newbeam')."""
    s = SectionInput()
    s.concretes = [Concrete(fcp=35.0, maxagg=19.0)]
    s.rebars = [Rebar("Steel 1", fy=400.0, esh=0.007, eu=0.100),
                Rebar("Trans", fy=400.0, esh=0.007, eu=0.100),
                Rebar("Low Relax", prestress=True, fu=1860.0, eu=0.043)]
    s.outline = [(600.0, 250.0, "Concrete 1"), (0.0, 250.0, "Concrete 1")]
    s.longs = [LongLayer("top", 538.95, "Steel 1", 300.0, 1, 19.5, bartitle="20M"),
               LongLayer("bot", 63.90, "Steel 1", 1500.0, 3, 25.2, bartitle="25M")]
    s.trans = [TransLayer("stirrup", "Trans", 100.0, 250.0, 554.3, 45.7, pattern=5, db=11.3,
                          bartitle="10M")]
    return s


def read(path: str | Path) -> SectionInput:
    data = Path(path).read_bytes()
    return parse(data)


_TAG = re.compile(r"<[A-Za-z_][^<>]*>")
_ATTR = re.compile(r"""\s+([A-Za-z_][\w.-]*)\s*=\s*("[^"]*"|'[^']*')""")


def _dedupe(text: str) -> str:
    """Response writes some attributes twice in one element (the area of a stirrup); XML does
    not allow that. Keep the first of each."""
    def fix(m):
        seen = set()

        def keep(a):
            if a.group(1) in seen:
                return ""
            seen.add(a.group(1))
            return a.group(0)
        return _ATTR.sub(keep, m.group(0))
    return _TAG.sub(fix, text)


def parse(data: bytes) -> SectionInput:
    text = data.decode("utf-8", errors="replace")
    # the DOCTYPE names r3g.dtd, which need not be beside the input: drop it and apply the
    # schema's defaults here
    text = re.sub(r"<!DOCTYPE[^>]*>", "", text)
    try:
        root = ET.fromstring(_dedupe(text).encode("utf-8"))
    except ET.ParseError as e:
        if text.lstrip().startswith("//"):
            raise OutOfScope("Response's older text format (Ver_0.8) is not read; save the "
                             "section from Response-2000 as .rsp or .r2t (XML)") from None
        raise InputError(f"not a Response-2000 XML input: {e}") from None
    beams = [root] if root.tag == "r3g_beam" else root.findall("r3g_beam")
    if not beams:
        raise InputError("no <r3g_beam> section in the input")
    if len(beams) > 1:
        # Response-2000's manual has one cross section to a file (A-7, A-28); its sample
        # inputs carry several (docs/scope.md 1.1; docs/summary.md D23)
        raise OutOfScope(f"the file holds {len(beams)} sections: several sections in one "
                         "file are not in Response-2000's manual and are not read; save the "
                         "one to analyse in a file of its own")
    beam = beams[0]

    s = SectionInput(name=beam.get("name", "New Cross Section"))
    s.units = _units_of(beam.get("units"))
    u: Units = FILE_UNITS[s.units]
    s.smx = _f(beam, "smx", -1.0)
    s.smt = _f(beam, "smt", -1.0)
    if s.smx > 0:
        s.smx *= u.length
    if s.smt > 0:
        s.smt *= u.length
    s.axialloc = _f(beam, "axialloc", -1.0)
    if s.axialloc >= 0:
        s.axialloc *= u.length

    for el in beam.findall("concrete"):
        c = Concrete(name=el.get("name", "Concrete 1"))
        c.fcp = _f(el, "fcp", 40.0) * u.conc_stress
        ft = _f(el, "ft", -1.0)
        c.ft = None if ft < 0 else ft * u.conc_stress
        e0 = _f(el, "e0", -1.0)
        c.e0 = None if e0 < 0 else e0 * 1e-3
        c.tsfactor = _f(el, "tsfactor", 1.0)
        c.maxagg = _f(el, "maxagg", 19.0 / u.length) * u.length
        c.c_mod = int(_f(el, "c_mod", 2))
        c.c_soft = int(_f(el, "c_soft", 18))
        c.t_stiff = int(_f(el, "t_stiff", 7))
        if c.t_stiff == 5:
            raise InputError("tension stiffening model 5 (Stuart Oliver) is not supported: "
                             "Response-2000 refuses the file too")
        if not 0 <= c.t_stiff <= 7 or not 0 <= c.c_soft <= 18 or not 0 <= c.c_mod <= 4:
            raise InputError(f"concrete {c.name!r}: c_mod={c.c_mod}, c_soft={c.c_soft}, "
                             f"t_stiff={c.t_stiff} are not all models of Response-2000")
        if c.c_soft in UNDOCUMENTED_SOFTENING:
            raise OutOfScope(f"concrete {c.name!r}: compression softening model {c.c_soft} is "
                             "not in Response-2000's manual and is not implemented")
        if c.c_soft in HSU_SOFTENING and c.t_stiff == 4:
            raise OutOfScope(f"concrete {c.name!r}: a Hsu softening model ({c.c_soft}) with "
                             "Tamai tension stiffening (Response-2000's RA-STM mode) is not "
                             "implemented")
        nums = [float(x) for x in _NUM.findall(el.text or "")]
        c.segments = [(nums[i] * 1e-3, nums[i + 1] * u.conc_stress)
                      for i in range(0, len(nums) - 1, 2)]
        s.concretes.append(c)
    if not s.concretes:
        raise InputError("no <concrete> in the section")

    for el in beam.findall("rebar"):
        r = Rebar(name=el.get("name", "Steel 1"))
        r.fy = _f(el, "fy", 400.0 / u.steel_stress) * u.steel_stress
        r.E = _f(el, "E", 200000.0 / u.steel_stress) * u.steel_stress
        r.fu = _f(el, "fu", 600.0 / u.steel_stress) * u.steel_stress
        r.esh = _f(el, "esh", 15.0) * 1e-3
        r.eu = _f(el, "eu", 80.0) * 1e-3
        if len(_NUM.findall(el.text or "")) >= 4:
            raise OutOfScope(f"reinforcement {r.name!r}: a segmental stress-strain curve for "
                             "reinforcing steel is not in Response-2000's manual and is not "
                             "implemented")
        s.rebars.append(r)
    for el in beam.findall("prestress"):
        r = Rebar(name=el.get("name", "Low Relax"), prestress=True)
        r.fu = _f(el, "fu", 1860.0 / u.steel_stress) * u.steel_stress
        r.E = _f(el, "E", 200000.0 / u.steel_stress) * u.steel_stress
        r.A = _f(el, "A", 0.025)
        r.B = _f(el, "B", 118.0)
        r.C = _f(el, "C", 10.0)
        r.eu = _f(el, "eu", 43.0) * 1e-3
        r.fy = r.fu
        s.rebars.append(r)

    solid = beam.find("sectionSOLID")
    if solid is not None and (solid.text or "").strip():
        s.outline = _outline(solid.text, u, s.concretes[0].name)
    else:
        # a shape given without its outline is no section to Response-2000 either: it opens
        # the file with no concrete and cannot solve it (docs/scope.md 1.4)
        raise InputError("the section has no concrete outline (<sectionSOLID>)")
    hollow = beam.find("sectionHOLLOW")
    if hollow is not None and (hollow.text or "").strip():
        raise OutOfScope("hollow sections (<sectionHOLLOW>) are not implemented")

    for i, el in enumerate(beam.findall("longreinfx")):
        title = el.get("bartitle", "")
        num = _f(el, "num", 1.0)
        area = _f(el, "A", 1.0) * u.area
        ai = _f(el, "Ai", 100.0 / u.area) * u.area
        db = _f(el, "db", 11.0 / u.length) * u.length
        known = bars.lookup(title) if title else None
        if known:
            db = known[0]
        elif el.get("db") is None:
            # no title and no diameter: take the diameter from the area of one bar
            one = area / max(num, 1.0) if el.get("Ai") is None else ai
            db = math.sqrt(4.0 * one / math.pi)
        if _f(el, "drape", 0.0) != 0.0:
            raise OutOfScope(f"layer {el.get('name', 'bot')!r}: draped tendons are not "
                             "implemented")
        lay = LongLayer(name=el.get("name", "bot"), z=_f(el, "z", 0.0) * u.length,
                        type=el.get("type", ""), area=area, num=num, db=db,
                        dep=_f(el, "dep", 0.0) * 1e-3,
                        space=_f(el, "space", 0.0) * u.length, bartitle=title,
                        pattern=int(_f(el, "pattern", 0)))
        s.material(lay.type)
        s.longs.append(lay)

    for el in beam.findall("transreinfz"):
        title = el.get("bartitle", "")
        db = _f(el, "db", 11.0 / u.length) * u.length
        known = bars.lookup(title) if title else None
        if known:
            db = known[0]
        t = TransLayer(name=el.get("name", "trans"), type=el.get("type", ""),
                       area=_f(el, "A", 0.0) * u.area,
                       space=_f(el, "space", 100.0 / u.length) * u.length,
                       disttop=_f(el, "disttop", 600.0 / u.length) * u.length,
                       distbot=_f(el, "distbot", 0.0) * u.length,
                       pattern=int(_f(el, "pattern", 0)), db=db,
                       dep=_f(el, "dep", 0.0) * 1e-3, bartitle=title)
        if t.pattern == HORIZONTAL_TIE:
            raise OutOfScope(f"transverse reinforcement {t.name!r}: the horizontal tie "
                             "(pattern 7) is not in Response-2000's manual and is not "
                             "implemented")
        s.material(t.type)
        s.trans.append(t)

    ld = beam.find("sectloading")
    if ld is not None:
        s.loading = Loading(
            constant=(_f(ld, "BN", 0.0) * u.force, _f(ld, "BM", 0.0) * u.moment,
                      _f(ld, "BV", 0.0) * u.force),
            increment=(_f(ld, "MN", 0.0), _f(ld, "MM", 1.0), _f(ld, "MV", 0.0)))

    sh = beam.find("shrinktherm")
    if sh is not None:
        nums = [float(x) for x in _NUM.findall(sh.text or "")]
        s.shrink = [(nums[i] * u.length, nums[i + 1] * 1e-3) for i in range(0, len(nums) - 1, 2)]
    sd = beam.find("straindiscont")
    if sd is not None:
        nums = [float(x) for x in _NUM.findall(sd.text or "")]
        s.discont = [(nums[i] * u.length, nums[i + 1] * 1e-3)
                     for i in range(0, len(nums) - 1, 2)]
    rt = beam.find("rebarthermx")
    if rt is not None:
        toks = [t.strip('"') for t in _TOKEN.findall(rt.text or "")]
        for i in range(0, len(toks) - 1, 2):
            for lay in s.longs:
                if lay.name.lower() == toks[i].lower():
                    try:
                        lay.thermal = float(toks[i + 1]) * 1e-3
                    except ValueError:
                        pass
    ao = beam.find("analysisoptions")
    if ao is not None:
        s.phic, s.phis, s.phip = _f(ao, "phic", 1.0), _f(ao, "phis", 1.0), _f(ao, "phip", 1.0)
        s.longterm = _f(ao, "longterm", 0.0) != 0.0
    if s.longterm:
        raise OutOfScope("time dependent effects (long term analysis) are not implemented")
    if any(v for _, v in s.discont):
        raise OutOfScope("strain discontinuities are not implemented")
    return s


CURVED = ("curved outline rows (UP, DOWN) cannot be in an input file: Response-2000's reader "
          "rejects them. Give the curve as straight rows, as Response saves a circle")


def _outline(text: str, u: Units, first: str):
    rows: list[tuple[float, float, str]] = []
    for line in text.splitlines():
        toks = [t for t in _TOKEN.findall(line)]
        if not toks:
            continue
        # UP and DOWN mark a curved segment in shape.dat and in Response's outline dialog,
        # which turn it into straight rows; a file has the rows (docs/scope.md 1.4)
        if any(t.upper() in ("UP", "DOWN") for t in toks[:2]):
            raise InputError(CURVED)
        try:
            elev, width = float(toks[0]), float(toks[1])
        except (ValueError, IndexError):
            raise InputError(f"section outline line {line.strip()!r}") from None
        name = toks[2].strip('"') if len(toks) > 2 else ""
        rows.append((elev * u.length, width * u.length, name))
    if len(rows) < 2:
        raise InputError("the section outline needs at least two rows")
    # Response lists rows from the top down; a row's concrete type applies upwards from it.
    rows.sort(key=lambda r: -r[0])
    return [(elev, width, name or first) for elev, width, name in rows]
