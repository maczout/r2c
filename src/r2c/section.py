"""The cross section as the analysis sees it: outline, reinforcement, and the depth-wise tables
(crack spacing, tension stiffening, cracking strength) that do not change during a solve.

Depths: z is measured up from the bottom of the section (as in the input); y = z - zc is
measured from the centroid of the gross concrete area, which is how results are reported.
Units: mm, MPa, N.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from r2c.inputs import SectionInput
from r2c.materials import ConcreteLaw, SteelLaw

NTAB = 100          # samples of every depth-wise table, as in Response


def _is_strand(title: str) -> bool:
    return title[:1] in ("S", "T", "s", "t")


@dataclass
class Layer:
    """One layer of longitudinal reinforcement."""
    name: str
    z: float
    area: float
    num: float
    db: float
    steel: SteelLaw
    prestrain: float        # dep less thermal strain
    strand: bool
    rho: float = 0.0        # ratio used for the strain concentration at a crack


@dataclass
class Stirrup:
    name: str
    area: float
    space: float
    top: float
    bot: float
    db: float
    steel: SteelLaw
    prestrain: float
    strand: bool
    pattern: int
    legs: int


class Section:
    def __init__(self, inp: SectionInput, phic=1.0, phis=1.0, phip=1.0):
        self.inp = inp
        self.phic, self.phis, self.phip = phic, phis, phip
        factored = (abs(phic) + 2 * abs(phis)) < 3.0
        self.concretes = {c.name.lower(): ConcreteLaw(c, phic) for c in inp.concretes}
        self.conc0 = ConcreteLaw(inp.concretes[0], phic)
        steels = {}
        for r in inp.rebars:
            steels[r.name.lower()] = SteelLaw(r, phip if r.prestress else phis, factored)
        # outline: rows from the top down; between consecutive rows the width is linear
        rows = sorted(inp.outline, key=lambda r: -r[0])
        self.rows = rows
        self.ztop = rows[0][0]
        self.zbot = rows[-1][0]
        self.h = self.ztop - self.zbot
        # segments: (z_hi, z_lo, b_hi, b_lo, concrete law)
        self.segs = []
        for (z1, b1, n1), (z2, b2, n2) in zip(rows[:-1], rows[1:]):
            if z1 - z2 > 1e-9:
                law = self.concretes.get((n2 or n1 or "").lower(), self.conc0)
                self.segs.append((z1, z2, b1, b2, law))
        self.laws = []
        for s in self.segs:
            if s[4] not in self.laws:
                self.laws.append(s[4])
        self.area = sum((b1 + b2) / 2 * (z1 - z2) for z1, z2, b1, b2, _ in self.segs)
        mom = sum(self._seg_moment(*s[:4]) for s in self.segs)
        self.zc = mom / self.area
        self.zaxial = inp.axialloc if inp.axialloc >= 0 else self.zc

        self.layers: list[Layer] = []
        for l in inp.longs:
            st = steels[l.type.lower()]
            self.layers.append(Layer(l.name, l.z, l.area, max(l.num, 1.0), l.db, st,
                                     l.dep - l.thermal, _is_strand(l.bartitle)))
        # steel ratio for the strain concentration at a crack: all the steel on the layer's
        # side of the centroid over 0.8 of the gross area
        above = sum(o.area for o in self.layers if o.z > self.zc) + \
            0.5 * sum(o.area for o in self.layers if o.z == self.zc)
        below = sum(o.area for o in self.layers if o.z < self.zc) + \
            0.5 * sum(o.area for o in self.layers if o.z == self.zc)
        for l in self.layers:
            ra, rb = above / (0.8 * self.area), below / (0.8 * self.area)
            l.rho = ra if l.z > self.zc else rb if l.z < self.zc else 0.5 * (ra + rb)
        self.stirrups: list[Stirrup] = []
        for t in inp.trans:
            if t.area <= 0 or t.space <= 0:
                continue
            if abs(t.disttop - t.distbot) < 1e-6:
                continue                  # a cross tie: no vertical leg
            # Response's stirrup types: 1 single leg, 2 open, 3 closed, 4 hoop,
            # 5 T-headed single leg, 6 interlocking hoops
            legs = 1 if t.pattern in (0, 1, 5) else 2
            self.stirrups.append(Stirrup(t.name, t.area, t.space, max(t.disttop, t.distbot),
                                         min(t.disttop, t.distbot), t.db,
                                         steels[t.type.lower()], t.dep,
                                         _is_strand(t.bartitle), t.pattern, legs))
        self.smx_user = inp.smx
        self.smt_user = inp.smt
        self._tables()

    # -- geometry -------------------------------------------------------------------------------
    @staticmethod
    def _seg_moment(z1, z2, b1, b2):
        """First moment about z = 0 of a trapezoid between z2 (width b2) and z1 (width b1)."""
        hh = z1 - z2
        return hh * (b2 * (2 * z2 + z1) + b1 * (z2 + 2 * z1)) / 6.0

    def width(self, z):
        """Width at height z (array); at a step, the value just below."""
        z = np.asarray(z, dtype=float)
        out = np.zeros_like(z)
        for z1, z2, b1, b2, _ in self.segs:
            m = (z <= z1 + 1e-9) & (z >= z2 - 1e-9)
            t = (z[m] - z2) / (z1 - z2)
            out[m] = b2 + (b1 - b2) * t
        return out

    def width_side(self, z: float, upper: bool) -> float:
        """Width just above (upper) or just below a height."""
        for z1, z2, b1, b2, _ in self.segs:
            if upper and abs(z - z2) < 1e-9:
                return b2
            if not upper and abs(z - z1) < 1e-9:
                return b1
        return float(self.width(np.array([z]))[0])

    def law_at(self, z: float) -> ConcreteLaw:
        for z1, z2, _, _, law in self.segs:
            if z2 - 1e-9 <= z <= z1 + 1e-9:
                return law
        return self.conc0

    def area_between(self, za: float, zb: float) -> float:
        lo, hi = min(za, zb), max(za, zb)
        a = 0.0
        for z1, z2, b1, b2, _ in self.segs:
            u, d = min(z1, hi), max(z2, lo)
            if u > d:
                bu = b2 + (b1 - b2) * (u - z2) / (z1 - z2)
                bd = b2 + (b1 - b2) * (d - z2) / (z1 - z2)
                a += (bu + bd) / 2 * (u - d)
        return a

    def breaks(self) -> list[float]:
        """Heights where the outline or the concrete type changes."""
        out = {self.ztop, self.zbot}
        for z1, z2, *_ in self.segs:
            out.add(z1)
            out.add(z2)
        return sorted(out)

    # -- transformed uncracked section ----------------------------------------------------------
    def transformed(self):
        """(area, inertia, distance to top, distance to bottom) of the uncracked transformed
        section, bars at (n - 1) times their area."""
        ec = self.conc0.Ec
        a = self.area
        m = self.area * self.zc
        for l in self.layers:
            n = l.steel.E / ec - 1.0
            a += n * l.area
            m += n * l.area * l.z
        zb = m / a
        i = 0.0
        for z1, z2, b1, b2, _ in self.segs:
            hh = z1 - z2
            # trapezoid inertia about its own centroid, then shifted
            aa = (b1 + b2) / 2 * hh
            if aa <= 0:
                continue
            zcg = self._seg_moment(z1, z2, b1, b2) / aa
            io = hh ** 3 * (b1 * b1 + 4 * b1 * b2 + b2 * b2) / (36.0 * (b1 + b2))
            i += io + aa * (zcg - zb) ** 2
        for l in self.layers:
            n = l.steel.E / ec - 1.0
            i += n * l.area * (l.z - zb) ** 2
        return a, i, self.ztop - zb, zb - self.zbot, zb

    # -- depth-wise tables ----------------------------------------------------------------------
    def _tables(self):
        self.tz = np.linspace(self.zbot, self.ztop, NTAB)
        bw = np.maximum(self.width(self.tz), 1e-6)
        # longitudinal crack spacing: 2c + 0.1 db / rho (CEB), c the diagonal distance to the
        # nearest bar, rho the steel within 7.5 db above and below the bar
        if self.layers:
            best = np.full(NTAB, np.inf)
            for l in self.layers:
                up = min(l.z + 7.5 * l.db, self.ztop)
                dn = max(l.z - 7.5 * l.db, self.zbot)
                ac = max(self.area_between(dn, up), 1e-6)
                steel = sum(o.area for o in self.layers if dn - 1e-9 <= o.z <= up + 1e-9)
                rho = steel / ac
                bz = float(self.width(np.array([l.z]))[0])
                dx = bz / (2.0 * l.num)
                c = np.sqrt((self.tz - l.z) ** 2 + dx * dx)
                best = np.minimum(best, 2.0 * c + 0.1 * l.db / rho)
            sx = best
        else:
            sx = np.full(NTAB, 5.0 * self.h)
        if self.smx_user > 0:
            sx = np.full(NTAB, self.smx_user)
        self.t_smx = np.minimum(sx, self.h)
        self.t_smx_raw = sx
        # transverse crack spacing: the same relation for the stirrups
        st = np.full(NTAB, 5.0 * self.h)
        for s in self.stirrups:
            inside = (self.tz >= s.bot - 1e-9) & (self.tz <= s.top + 1e-9)
            rho = s.area / (bw * s.space)
            c = np.sqrt((s.space / 2.0) ** 2 + np.maximum(bw / 2.0 - 50.0, 0.0) ** 2)
            val = 2.0 * c + 0.1 * s.db / rho
            st = np.where(inside, np.minimum(st, val), st)
        if self.smt_user > 0:
            st = np.full(NTAB, self.smt_user)
        self.t_smt = st
        # tension stiffening coefficient M (Bentz 1999): 3.6 / T, T the bonded bar perimeter
        # per area of concrete, a tent around each layer reaching zero one crack spacing away
        tl = np.zeros(NTAB)
        for l in self.layers:
            up = min(l.z + 7.5 * l.db, self.ztop)
            dn = max(l.z - 7.5 * l.db, self.zbot)
            ac = max(self.area_between(dn, up), 1e-6)
            perim = l.db * math.pi * l.num / ac
            sbar = float(np.interp(l.z, self.tz, self.t_smx))
            kk = perim * 2.5 / (sbar + 1e-4)
            tent = np.minimum((l.z + sbar - self.tz) * kk, (self.tz - (l.z - sbar)) * kk)
            tl += np.maximum(tent, 0.0)
        self.t_mlong = 3.6 / (tl + 1e-7)
        tt = np.zeros(NTAB)
        for s in self.stirrups:
            inside = (self.tz >= s.bot - 1e-9) & (self.tz <= s.top + 1e-9)
            tt += np.where(inside, s.db * math.pi * s.legs / (bw * s.space + 1e-4), 0.0)
        self.t_mtrans = 3.6 / (tt + 1e-7)
        self.t_m = np.minimum(self.t_mlong, self.t_mtrans)
        # stirrup ratio by depth
        rv = np.zeros(NTAB)
        for s in self.stirrups:
            inside = (self.tz >= s.bot - 1e-9) & (self.tz <= s.top + 1e-9)
            rv += np.where(inside, s.area / (bw * s.space), 0.0)
        self.t_rhov = rv
        # steel ratio for the strain concentration of the stirrups at a crack: the larger of
        # the stirrup ratio and a line between the ratios of the bottom and the top bars
        top = bot = 0.0
        for l in self.layers:
            if l.z > self.zc:
                top = l.rho
            elif l.z < self.zc:
                bot = l.rho
        rh = np.zeros(NTAB)
        for s in self.stirrups:
            inside = (self.tz >= s.bot - 1e-9) & (self.tz <= s.top + 1e-9)
            fac = 1.0
            if s.pattern == 4:
                d = self.tz - 0.5 * (s.top + s.bot)
                v = 1.0 - d * d / (0.25 * (s.top - s.bot) ** 2 + 1e-4)
                fac = np.where(v > 0, np.sqrt(np.maximum(v, 0.0)), 1.0)
            rh += np.where(inside, s.area / (bw * s.space) * fac, 0.0)
        self.t_rhocrit = np.maximum(bot + (self.tz - self.tz[0]) / self.h * (top - bot), rh)

    def tab(self, table: np.ndarray, z):
        return np.interp(z, self.tz, table)

    def cracking_table(self, n0, m0, dn, dm):
        """Cracking strength by depth. In flexure the extreme fibre cracks at a size-dependent
        flexural strength, 2.5 (1 + 1.75 f'c / D) MPa with D twice the depth of the tension
        zone at cracking; inside the section the strength follows the elastic stress profile
        at cracking down to the direct tensile strength ft. A concrete given an ft keeps it."""
        a, i, ct, cb, zb = self.transformed()
        if abs(dn) + abs(dm) < 1e-6:
            dm = 1.0
        # prestress acting on the uncracked section
        pf = sum(float(l.steel.stress(l.prestrain)) * l.area for l in self.layers
                 if l.prestrain != 0.0)
        pm = sum(float(l.steel.stress(l.prestrain)) * l.area * (l.z - zb) for l in self.layers
                 if l.prestrain != 0.0)
        out = []
        for face, c, law in ((0, ct, self.law_at(self.ztop)), (1, cb, self.law_at(self.zbot))):
            if not law.auto_ft:
                out.append((law.ft, self.h))
                continue
            ft = law.ft
            fr = 0.1 * ft
            d = self.h
            ok = False
            # the moment is taken to put this face in tension, whichever face it is
            mp = pm if face == 1 else -pm
            const = (abs(m0) + mp) * c / i + (n0 - pf) / a
            den = abs(dm) * c / i + dn / a
            for _ in range(50):
                lam = (fr - const) / den if abs(den) > 1e-30 else 0.0
                sig_n = (lam * dn + n0 - pf) / a
                bend = max(fr - sig_n, 1e-6)
                d = 2.0 * c * fr / bend
                new = min(0.15 * law.fcp, 2.5 * (1.0 + 1.75 * law.fcp / max(d, 1e-9)))
                mid = (d - c) / (d + 1e-7) * new
                if ft < mid:
                    new = new * (ft / mid)
                nxt = 0.5 * (fr + new)
                done = abs(nxt - new) < 0.001 * nxt + 0.001
                fr = nxt
                if done:
                    ok = True
                    break
            if not ok:
                fr, d = ft, self.h
            d = max(d, self.h / 20.0)
            out.append((fr, d))
        (ftop, dtop), (fbot, dbot) = out
        tab = np.empty(NTAB)
        for j, z in enumerate(self.tz):
            law = self.law_at(z)
            if not law.auto_ft:
                tab[j] = law.ft
                continue
            up = (z - (self.ztop - dtop / 2.0)) * ftop / (dtop / 2.0)
            dn_ = ((self.zbot + dbot / 2.0) - z) * fbot / (dbot / 2.0)
            tab[j] = max(law.ft, up, dn_)
        return tab
