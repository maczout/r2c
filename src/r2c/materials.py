"""Constitutive relations: concrete in principal directions, reinforcement, prestressing steel.

Units: MPa, mm, plain strains; compression negative. The relations are those of Bentz's thesis
(Sectional Analysis of Reinforced Concrete Members, University of Toronto, 2000), chapters 3 to
5 and the manual's Tables 2-1 to 2-3, in the form Response-2000 1.9.7 applies them
(docs/kernel.md says where that differs from the thesis). Everything is written for numpy
arrays, one entry per node.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from r2c.inputs import Concrete, OutOfScope, Rebar

# Tension stiffening models (t_stiff)
TS_NONE, TS_VC82, TS_CM87, TS_IZUMO, TS_TAMAI, TS_HALF, TS_PLASTIC, TS_BENTZ = range(8)
# Base curves (c_mod)
BC_LINEAR, BC_PARABOLA, BC_POPOVICS, BC_PLASTIC, BC_SEGMENTAL = range(5)

NOVAL = float("nan")   # a bar past rupture


def auto_ft(fcp: float) -> float:
    """Automatic cracking strength of a large volume of concrete (MPa)."""
    return min(0.15 * fcp, 1.4 * (1.0 + 0.01 * fcp))


def popovics_n(f: float) -> float:
    return 0.8 + f / 17.0


@dataclass
class ConcreteLaw:
    """One concrete type, with its derived properties and the material factor applied."""
    src: Concrete
    phi: float = 1.0

    def __post_init__(self):
        c = self.src
        self.fcp = max(c.fcp, 5.0)
        self.c_mod = c.c_mod if c.c_mod in (0, 1, 2, 3, 4) else 2
        if self.c_mod == BC_SEGMENTAL and len(c.segments) < 2:
            self.c_mod = BC_POPOVICS
        self.c_soft = c.c_soft
        self.t_stiff = c.t_stiff if 0 <= c.t_stiff <= 7 else 7
        if self.t_stiff == 5 and c.t_stiff == 5:
            self.t_stiff = 5
        self.tsfactor = min(max(c.tsfactor, 0.0), 1.0)
        self.auto_ft = c.ft is None or c.ft <= 0
        self.ft = auto_ft(self.fcp) if self.auto_ft else c.ft
        self.n = max(popovics_n(self.fcp), 1.01)
        self.k = max(0.67 + self.fcp / 62.0, 1.0)
        if self.c_mod == BC_SEGMENTAL:
            pts = sorted((abs(e), abs(s)) for e, s in c.segments)
            self.seg_e = np.array([p[0] for p in pts])
            self.seg_s = np.array([p[1] for p in pts])
            i = int(np.argmax(self.seg_s))
            self.fcp = float(self.seg_s[i])
            self.e0 = float(self.seg_e[i])
        elif c.e0 is not None and c.e0 > 0:
            self.e0 = c.e0
        else:
            ec = 3320.0 * math.sqrt(self.fcp) + 6900.0
            self.e0 = self.fcp / ec * self.n / (self.n - 1.0)
        # effective aggregate size for shear on the crack: reduced to zero from 60 to 70 MPa
        a = c.maxagg
        if self.fcp >= 60.0:
            a = (70.0 - self.fcp) * a / 10.0 if self.fcp <= 70.0 else 0.0
        self.agg = min(a, 25.0)
        # initial stiffness: the secant at 0.1 mm/m of compression, as Response takes it
        e = np.array([-1e-4])
        s, _ = self._compression(e, np.zeros(1))
        self.Ec = float(s[0] / e[0]) / self.phi      # unfactored; phi is applied to stresses
        self.ecr = self.ft / (self.Ec + 1e-6)
        self.coef = {TS_VC82: 200.0, TS_CM87: 500.0}.get(self.t_stiff, 0.0)

    # -- compression ----------------------------------------------------------------------------
    def soften(self, e1: np.ndarray) -> np.ndarray:
        """beta = f2max / f'c for a transverse tensile strain e1 (>= 0)."""
        m = self.c_soft
        f = self.fcp
        if m == 0:
            return np.ones_like(e1)
        if m in (2, 6):       # Vecchio-Collins 1982 form
            b = 1.0 / (0.8 + 0.34 * e1 / self.e0)
            return np.minimum(b, 1.0) if m == 2 else np.clip(b, 0.8, 1.0)
        if m == 10:           # Vecchio-Collins 1986
            return np.minimum(1.0 / (0.8 + 170.0 * e1), 1.0)
        if m == 13:           # Porasz-Collins 1988
            return np.minimum(1.0 / ((0.9 + 0.0045 * f) * (0.8 + 0.34 * e1 / self.e0)), 1.0)
        if m == 7:
            return np.minimum(np.maximum(1.15 - 125.0 * e1, 0.65), 1.0)
        if m == 18:           # Collins-Bentz 2011 (Response's default)
            return np.minimum(1.0 / (0.8 + max(170.0, 3.0 * f) * e1), 1.0)
        raise OutOfScope(f"compression softening model {m} is not implemented")

    def _compression(self, e2: np.ndarray, e1: np.ndarray):
        """(stress, f2max) for compressive strains e2 (< 0) and transverse tension e1."""
        beta = self.soften(np.maximum(e1, 0.0))
        fmax = self.fcp * beta
        e0 = self.e0
        x = -e2 / e0
        if self.c_mod == BC_POPOVICS:
            n = np.maximum(0.8 + fmax / 17.0, 1.1)
            k = np.where(x > 1.0, np.maximum(0.67 + fmax / 62.0, 1.0), 1.0)
            with np.errstate(over="ignore", invalid="ignore"):
                s = fmax * n * x / (n - 1.0 + np.power(x, n * k))
        elif self.c_mod == BC_PARABOLA:
            s = fmax * (2.0 * x - x * x)
        elif self.c_mod == BC_LINEAR:
            s = np.where(x <= 1.0, fmax * x, 0.0)
        elif self.c_mod == BC_PLASTIC:
            s = np.where(x <= 2.0, np.minimum(fmax * x, fmax), 0.0)
        else:
            s = np.interp(-e2, self.seg_e, self.seg_s, right=0.0) * beta
        s = np.maximum(s, 0.0)
        return -s * self.phi, -fmax * self.phi

    # -- tension --------------------------------------------------------------------------------
    def crack_strain(self, ft_eff: np.ndarray) -> np.ndarray:
        return np.maximum(ft_eff / self.Ec, self.ecr)

    def tension(self, e: np.ndarray, ft_eff: np.ndarray, m: np.ndarray) -> np.ndarray:
        """Average tensile stress before the crack check, for strains e >= 0."""
        ecr = self.crack_strain(ft_eff)
        ts = self.t_stiff
        ee = np.maximum(e, 1e-12)
        if ts == TS_NONE:
            post = np.zeros_like(e)
        elif ts == TS_IZUMO:
            post = np.where(ee >= 2 * ecr, self.ft * np.power(2 * ecr / ee, 0.4), self.ft)
        elif ts == TS_TAMAI:
            post = self.ft * np.power(ecr / ee, 0.4)
        elif ts == TS_HALF:
            post = np.full_like(e, 0.5 * self.ft)
        elif ts == TS_PLASTIC:
            post = np.full_like(e, self.ft)
        else:
            coef = m if ts == TS_BENTZ else self.coef
            post = self.ft / (1.0 + np.sqrt(coef * ee))
        return np.where(e <= ecr, e * self.Ec, post * self.tsfactor) * self.phi

    def stress(self, e: np.ndarray, eo: np.ndarray, ft_eff: np.ndarray, m: np.ndarray):
        """Principal stress for strain e with the other principal strain eo: (stress, f2max)."""
        tens = e >= -1e-9
        s = np.empty_like(e)
        fmax = np.full_like(e, -self.fcp * self.phi)
        if tens.any():
            s[tens] = self.tension(e[tens], ft_eff[tens], m[tens])
        comp = ~tens
        if comp.any():
            s[comp], fmax[comp] = self._compression(e[comp], eo[comp])
        return s, fmax


@dataclass
class SteelLaw:
    """One reinforcement type (bars or strand), with material factors applied."""
    src: Rebar
    phi: float = 1.0          # this steel's material factor
    factored: bool = False    # any material factor in effect: no strain hardening above fy

    def __post_init__(self):
        r = self.src
        self.E, self.fy, self.fu, self.esh, self.eu = r.E, r.fy, r.fu, r.esh, r.eu
        self.prestress = r.prestress
        self.rupture = r.eu
        if not self.prestress and self.eu > self.esh:
            self.curv = (self.fy - self.fu) / (self.esh - self.eu) ** 2
        else:
            self.curv = 0.0

    def raw(self, e):
        """Stress without the material factor; nan once the bar has ruptured."""
        e = np.asarray(e, dtype=float)
        a = np.abs(e)
        sign = np.sign(e)
        if self.prestress:
            r = self.src
            with np.errstate(over="ignore"):
                s = self.E * a * (r.A + (1.0 - r.A) / np.power(1.0 + np.power(r.B * a, r.C),
                                                              1.0 / r.C))
            s = np.minimum(s, self.fu)
            s = np.where(a > self.eu, NOVAL, s)
            s = np.where(e < -0.006, NOVAL, s)
            return s * sign
        s = np.where(a <= self.fy / self.E, self.E * a,
                     np.where(a < self.esh, self.fy,
                              self.fu + self.curv * (a - self.eu) ** 2))
        if self.factored:
            s = np.minimum(s, self.fy)
        s = np.where(a >= self.rupture, NOVAL, s)
        return s * sign

    def stress(self, e):
        return self.raw(e) * self.phi

    def crack_capacity(self, e, prestrain, rho, strand: bool):
        """Largest stress the bar can reach at a crack, for an average strain e (thesis 4-5):
        the bare-bar stress at a concentrated strain, never less than yield."""
        e = np.asarray(e, dtype=float)
        base = 0.625 if strand else 1.0
        k = 2.0 if rho <= 0 else max(1.0, base * 0.014 / rho)
        ec = k * e + prestrain + (self.esh - self.fy / self.E if not self.prestress else 0.0)
        s = self.raw(ec)
        avg = e + prestrain
        inside = np.where(np.isnan(s), self.fu, np.maximum(s, self.fy))
        # the concentrated strain is past the strain at peak stress: once the bar has yielded
        # on average it has no reserve left at a crack
        beyond = np.where(avg >= self.fy / self.E, NOVAL, self.fu)
        cap = np.where(ec <= self.eu, inside, beyond)
        gone = np.isnan(self.raw(avg))
        return np.where(gone, NOVAL, cap * self.phi)
