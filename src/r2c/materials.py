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

from r2c.inputs import Concrete, InputError, Rebar

# Tension stiffening models (t_stiff)
TS_NONE, TS_VC82, TS_CM87, TS_IZUMO, TS_TAMAI, TS_HALF, TS_PLASTIC, TS_BENTZ = range(8)
# Base curves (c_mod)
BC_LINEAR, BC_PARABOLA, BC_POPOVICS, BC_PLASTIC, BC_SEGMENTAL = range(5)

# Compression softening models (c_soft) that lower the strain at peak stress with the strength
SOFTEN_STRAIN = (1, 9, 11, 14, 15, 16, 17)
# ... and those that also put a plateau between the lowered and the unlowered strain
SOFTEN_PLATEAU = (3, 4)

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
        # Vecchio-Collins 1992: Kf, the strength term of the softening [B 004ac190]
        self.kf = max(0.1825 * math.sqrt(self.fcp), 1.0)
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
    def soften(self, e1: np.ndarray, e2: np.ndarray | None = None) -> np.ndarray:
        """beta = f2max / f'c for a transverse tensile strain e1 (>= 0) and, for the models
        that use it, the compressive strain e2 (< 0). Response's compression softening
        models by number [B 004ad9c0], docs/kernel.md "Compression softening"."""
        m = self.c_soft
        f = self.fcp
        e0 = self.e0
        one = np.ones_like(e1)
        ae = None if e2 is None else np.maximum(-np.asarray(e2, dtype=float), 1e-12)
        if m == 0:                      # none
            return one
        if m == 1:                      # Vecchio-Collins 1982
            return np.minimum(1.0 / (0.85 + 0.27 * e1 / ae), 1.0)
        if m == 2:                      # Vecchio-Collins 1986
            return np.minimum(1.0 / (0.8 + 0.34 * e1 / e0), 1.0)
        if m == 3:                      # Vecchio-Collins 1992-A
            kc = 0.35 * np.power(np.maximum(e1 / ae - 0.28, 0.0), 0.8)
            return np.minimum(1.0 / (1.0 + self.kf * kc), 1.0)
        if m == 4:                      # no name in Response's dialogs
            return np.minimum(1.0 / (1.0 + self.kf * 0.23 * e1 / ae), 1.0)
        if m == 5:                      # Vecchio-Collins 1992-B (Kf = 1)
            return np.minimum(1.0 / (1.0 + 0.27 * (e1 / e0 - 0.37)), 1.0)
        if m == 6:                      # Mehlhorn et al
            return np.clip(1.0 / (0.8 + 0.34 * e1 / e0), 0.8, 1.0)
        if m == 7:                      # Maekawa et al
            return np.clip(1.15 - 125.0 * e1, 0.65, 1.0)
        if m == 8:                      # Noguchi et al
            if f >= 60.0:
                d = 0.6 * np.power(e1 + 2e-4, 0.39) + 0.8
            else:
                d = 0.96 * np.power(e1 / e0, 0.167) + 0.27
            return np.minimum(1.0 / d, 1.0)
        if m == 9:                      # Belarbi-Hsu proportional
            return 0.9 / np.sqrt(1.0 + 400.0 * e1)
        if m == 10:                     # CAN CSA A23.3 M84
            return np.minimum(1.0 / (0.8 + 170.0 * e1), 1.0)
        if m == 11:                     # Collins 1978 (compression field theory)
            return np.minimum(3.6 / (1.0 + 2.0 * (e1 + ae) / e0), 1.0)
        if m == 12:                     # Kaufmann-Marti 1998
            return np.minimum(f ** 0.6667 / (0.4 + 30.0 * e1) / f, 1.0)
        if m == 13:                     # Porasz-Collins 1988
            return np.minimum(1.0 / ((0.9 + 0.0045 * f) * (0.8 + 0.34 * e1 / e0)), 1.0)
        if m in (14, 16, 17):           # Zhang-Hsu 1998, Zhu-Hsu-Lee 2001 (eta = 1, see kernel.md)
            return min(0.9, 5.8 / math.sqrt(f)) / np.sqrt(1.0 + 400.0 * e1)
        if m == 15:                     # Hsu 1993
            return 0.9 / np.sqrt(1.0 + 600.0 * e1)
        if m == 18:                     # Collins-Bentz 2011 (Response's default)
            return np.minimum(1.0 / (0.8 + max(170.0, 3.0 * f) * e1), 1.0)
        raise InputError(f"compression softening model {m} is not one of Response-2000's")

    def _base(self, x: np.ndarray, fmax: np.ndarray, n=None) -> np.ndarray:
        """The base curve: stress (positive) at x = strain / strain at peak, for a peak
        stress fmax."""
        if self.c_mod == BC_POPOVICS:
            if n is None:
                n = np.maximum(0.8 + fmax / 17.0, 1.1)
            k = np.where(x > 1.0, np.maximum(0.67 + fmax / 62.0, 1.0), 1.0)
            with np.errstate(over="ignore", invalid="ignore"):
                return fmax * n * x / (n - 1.0 + np.power(x, n * k))
        if self.c_mod == BC_PARABOLA:
            return fmax * (2.0 * x - x * x)
        if self.c_mod == BC_LINEAR:
            return np.where(x <= 1.0, fmax * x, 0.0)
        if self.c_mod == BC_PLASTIC:
            return np.where(x <= 2.0, np.minimum(fmax * x, fmax), 0.0)
        raise AssertionError(self.c_mod)

    def _compression(self, e2: np.ndarray, e1: np.ndarray):
        """(stress, f2max) for compressive strains e2 (< 0) and transverse tension e1
        [B 004ad9c0]."""
        m = self.c_soft
        beta = self.soften(np.maximum(e1, 0.0), e2)
        fmax = self.fcp * beta
        e0 = self.e0
        ae = -e2
        if self.c_mod == BC_SEGMENTAL:
            s = np.interp(ae, self.seg_e, self.seg_s, right=0.0) * beta
        elif m in SOFTEN_STRAIN:
            # the strain at peak stress is lowered with the strength
            ep = e0 * beta
            s = self._base(ae / ep, fmax)
            if self.c_mod == BC_PARABOLA:
                # past the peak the parabola runs out at twice (Zhu-Hsu-Lee: four times)
                # the unsoftened strain at peak stress
                end = (4.0 if m == 16 else 2.0) * e0
                s = np.where(ae > ep, fmax * (1.0 - ((ae - ep) / (end - ep)) ** 2), s)
        elif m in SOFTEN_PLATEAU:
            # strength and strain lowered; a plateau from the lowered strain at peak stress
            # to the unlowered one; past that the unlowered curve, scaled
            ep = e0 * beta
            n = self.n if self.c_mod == BC_POPOVICS else None
            s = np.where(ae < ep, self._base(ae / ep, fmax, n),
                         np.where(ae <= e0, fmax,
                                  beta * self._base(ae / e0, np.full_like(ae, self.fcp), n)))
        else:
            s = self._base(ae / e0, fmax)
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
        self.segmental = False
        if self.prestress:
            # Response derives the rest from the Ramberg-Osgood curve: the strength is no more
            # than the curve gives at the rupture strain, and "yield" is 0.9 of the strength
            with np.errstate(over="ignore"):
                top = self.E * self.eu * (r.A + (1.0 - r.A) / (1.0 + (r.B * self.eu) ** r.C)
                                          ** (1.0 / r.C))
            self.fu = min(self.fu, float(top))
            self.fy = 0.9 * self.fu
            self.esh = self.fy / self.E
            self.rupture = self.eu
            self.curv = 0.0
        elif len(r.segments) >= 2:
            self._segmental(r.segments)
        else:
            self.esh = max(self.esh, self.fy / self.E)
            self.eu = max(self.eu, self.esh + 1e-6)
            self.fu = max(self.fu, self.fy)
            # past the strain at peak stress the curve carries on down, until the bar ruptures
            # at one and a half times the length of the hardening branch
            self.rupture = self.esh + 1.5 * (self.eu - self.esh)
            self.curv = (self.fy - self.fu) / (self.esh - self.eu) ** 2

    def _segmental(self, segments):
        """A user-defined curve of (strain, stress) points, straight between them, and the
        properties Response derives from it [B 004ab4e0]: the stiffness from the stress at
        0.5 mm/m, the strength and its strain from the highest point, yield where the curve
        meets the line of that stiffness offset by 2 mm/m (the strength if it never does),
        the strain at which the curve passes 1.001 times yield in place of the strain at
        strain hardening, and rupture at the last point that carries more than 1 % of
        yield."""
        pts = sorted({(abs(e), abs(v)) for e, v in segments})
        if pts[0][0] > 0.0:
            pts.insert(0, (0.0, 0.0))
        self.seg_e = np.array([p[0] for p in pts])
        self.seg_s = np.array([p[1] for p in pts])
        at = lambda x: float(np.interp(x, self.seg_e, self.seg_s))
        self.E = max((at(5e-4) - at(0.0)) / 5e-4, 1e-3)
        i = int(np.argmax(self.seg_s))
        self.fu, self.eu = float(self.seg_s[i]), float(self.seg_e[i])
        hit = self._meets(self.E, -0.002 * self.E)
        self.fy = hit[1] if hit else self.fu
        hit = self._meets(0.0, 1.001 * self.fy)
        self.esh = hit[0] if hit else self.fy / self.E
        live = self.seg_e[self.seg_s > 0.01 * self.fy]
        self.rupture = float(live.max()) if len(live) else float(self.seg_e[-1])
        self.curv = 0.0
        self.segmental = True

    def _meets(self, slope: float, intercept: float):
        """The last point where the segmental curve crosses the line stress = slope x
        strain + intercept, or None."""
        found = None
        for x0, y0, x1, y1 in zip(self.seg_e[:-1], self.seg_s[:-1], self.seg_e[1:],
                                  self.seg_s[1:]):
            den = (y1 - y0) - slope * (x1 - x0)
            if den == 0.0:
                continue
            t = (slope * x0 + intercept - y0) / den
            if 0.0 <= t <= 1.0:
                found = (float(x0 + t * (x1 - x0)), float(y0 + t * (y1 - y0)))
        return found

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
        if self.segmental:
            # past the last point, or where the curve has come down to nothing: ruptured
            s = np.interp(a, self.seg_e, self.seg_s, right=NOVAL)
            s = np.where((s == 0.0) & (a > 0.0), NOVAL, s)
            if self.factored:
                s = np.minimum(s, self.fy)
            s = np.where(a > self.rupture, NOVAL, s)
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

    def tangent(self, e):
        """Slope of the loading curve at strain e, as Response's shear flow calculation takes
        it [B 004ae630]: no account of unloading; nothing on the yield plateau; on the
        hardening branch the slope's magnitude, also past the strain at peak stress; nothing
        once ruptured. Without the material factor."""
        e = np.asarray(e, dtype=float)
        a = np.abs(e)
        if self.prestress or self.segmental:
            d = 1e-7
            with np.errstate(invalid="ignore"):
                t = (np.abs(self.raw(a + d)) - np.abs(self.raw(a))) / d
            return np.where(np.isnan(t), 0.0, t)
        hard = 0.0 if self.factored else 1.0
        t = np.where(a < self.fy / self.E, self.E,
                     np.where(a < self.esh, 0.0,
                              np.where(a < self.rupture,
                                       hard * 2.0 * abs(self.curv) * np.abs(a - self.eu), 0.0)))
        return t

    def crack_strain(self, e, prestrain, rho, strand: bool):
        """The concentrated strain at a crack for an average strain e (see crack_capacity)."""
        base = 0.625 if strand else 1.0
        rho = np.asarray(rho, dtype=float)
        k = np.where(rho > 0, np.maximum(1.0, base * 0.014 / np.maximum(rho, 1e-12)), 2.0)
        return k * np.asarray(e, dtype=float) + prestrain + (self.esh - self.fy / self.E)

    def crack_capacity(self, e, prestrain, rho, strand: bool):
        """Largest stress the steel can reach at a crack, for an average strain e (thesis 4-5):
        the bare-bar stress at a concentrated strain, never less than yield. nan: the bar
        ruptures at the crack."""
        e = np.asarray(e, dtype=float)
        base = 0.625 if strand else 1.0
        rho = np.asarray(rho, dtype=float)
        k = np.where(rho > 0, np.maximum(1.0, base * 0.014 / np.maximum(rho, 1e-12)), 2.0)
        ec = k * e + prestrain + (self.esh - self.fy / self.E)
        s = self.raw(ec)
        avg = e + prestrain
        gone = np.isnan(s)
        inside = np.where(gone, self.fu, np.maximum(s, self.fy))
        # the concentrated strain is past the strain at peak stress: steel that has yielded on
        # average follows its curve down and ruptures at the crack where the curve ends
        beyond = np.where(avg >= self.fy / self.E, s, self.fu)
        cap = np.where(ec <= self.eu, inside, beyond)
        return np.where(np.isnan(self.raw(avg)), NOVAL, cap * self.phi)
