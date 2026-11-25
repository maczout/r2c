"""Units. Inside r2c everything is mm, MPa, N, N mm and plain strains; these tables convert
input files to that, and results to the units in effect (Response's three sets).

    si     kN    kN·m    mm   MPa
    us     kip   kip·ft  in   psi (concrete), ksi (steel)
    kgcm   ton   ton·m   cm   kg/cm2 (concrete), t/cm2 (steel)
"""

from __future__ import annotations

from dataclasses import dataclass

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
    l_strain: str = "mm/m"
    l_deg: str = "deg."
    l_crack_steel: str = "MPa"   # the label of the steel stress at a crack


SI = Units("si", 1.0, 1.0, 1.0, 1.0, 1000.0, 1e6)
# Response's own labels and conversion constants, as its charts show them: in US units the
# strains are labelled "ms" and the steel stress at a crack carries the concrete's unit label;
# in kg-cm units g is 9.81 for concrete stresses and 9.8 for everything else, and a force is
# labelled "ton" on the control charts (axial load and shear alike).
US = Units("us", 25.4, 645.16, 0.00689475729, 6.89475729, 4448.2216, 4448.2216 * 304.8,
           "in", "psi", "ksi", "kips", "kip-ft", "rad/10^3inch", 1e-3 / 25.4,
           "ms", "deg", "psi")
KGCM = Units("kgcm", 10.0, 100.0, 9.81 / 100.0, 9.8 * 10.0, 9.8 * 1000.0, 9.8 * 1e6,
             "cm", "kg/cm^2", "t/cm^2", "ton", "ton-m", "mrad/m", 1e-6,
             "mm/m", "deg", "kg/cm^2")

FILE_UNITS = {"si": SI, "us": US, "kgcm": KGCM}
