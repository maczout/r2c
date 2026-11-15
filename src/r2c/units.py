"""Units. Inside r2c everything is mm, MPa, N, N mm and plain strains; these tables convert
input files to that, and results to the units in effect (Response's three sets).

    si     kN    kN·m    mm   MPa
    us     kip   kip·ft  in   psi (concrete), ksi (steel)
    kgcm   ton   ton·m   cm   kg/cm2 (concrete), t/cm2 (steel)
"""

from __future__ import annotations

from dataclasses import dataclass

G = 9.80665


@dataclass(frozen=True)
class Units:
    name: str
    length: float        # internal mm per unit
    area: float          # internal mm2 per unit
    conc_stress: float   # internal MPa per unit
    steel_stress: float  # internal MPa per unit
    force: float         # internal N per unit
    moment: float        # internal N mm per unit
    # labels as Response prints them
    l_len: str = "mm"
    l_conc: str = "MPa"
    l_steel: str = "MPa"
    l_force: str = "kN"
    l_moment: str = "kNm"
    l_curv: str = "mrad/m"       # curvature label
    curv: float = 1e-6           # internal (1/mm) per unit of curvature


SI = Units("si", 1.0, 1.0, 1.0, 1.0, 1000.0, 1e6)
US = Units("us", 25.4, 645.16, 0.00689475729, 6.89475729, 4448.2216, 4448.2216 * 304.8,
           "in", "psi", "ksi", "kips", "ft-kips", "rad/10^6 in", 1e-6 / 25.4)
KGCM = Units("kgcm", 10.0, 100.0, G / 100.0, G * 10.0, G * 1000.0, G * 1e6,
             "cm", "kg/cm^2", "t/cm^2", "tons", "ton-m", "rad/km", 1e-6)

FILE_UNITS = {"si": SI, "us": US, "kgcm": KGCM}
