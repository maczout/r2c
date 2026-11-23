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
    thermal: float = 0.0    # the layer's thermal strain (already taken off the prestrain)


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
                                     l.dep - l.thermal, _is_strand(l.bartitle),
                                     thermal=l.thermal))
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
        # shrinkage and thermal strain of the concrete: (elevation, strain) from the bottom up
        self.shrink = sorted({(float(z), float(e)) for z, e in inp.shrink})
        if not any(e for _, e in self.shrink):
            self.shrink = []
        self._tables()

    def shrinkage(self, z):
        """The shrinkage or thermal strain of the concrete at heights z: the strain the
        concrete would take up unrestrained, which carries no stress. A parabola through
        the points given (the manual, 3-5: "Response-2000 parabolically interpolates between
        these points"; Response's own Shrinkage & Thermal Strain chart shows it for three
        points, measured); constant beyond the end points; straight between two points."""
        z = np.asarray(z, dtype=float)
        pts = self.shrink
        if not pts:
            return np.zeros_like(z)
        zs = np.array([p[0] for p in pts])
        es = np.array([p[1] for p in pts])
        if len(pts) < 3:
            return np.interp(z, zs, es)
        zc = np.clip(z, zs[0], zs[-1])
        # the three points nearest each height (all three when there are only three)
        i = np.clip(np.searchsorted(zs, zc) - 1, 0, len(zs) - 3)
        i = np.where((i + 3 <= len(zs) - 1) & (zc - zs[i + 1] > zs[np.minimum(i + 2, len(zs) - 1)] - zc),
                     i + 1, i)
        z0, z1, z2 = zs[i], zs[i + 1], zs[i + 2]
        e0, e1, e2 = es[i], es[i + 1], es[i + 2]
        return (e0 * (zc - z1) * (zc - z2) / ((z0 - z1) * (z0 - z2))
                + e1 * (zc - z0) * (zc - z2) / ((z1 - z0) * (z1 - z2))
                + e2 * (zc - z0) * (zc - z1) / ((z2 - z0) * (z2 - z1)))

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
        self._spacing_tables()
        # tension stiffening coefficient M (Bentz 1999): 3.6 / T, T the bonded bar perimeter
        # per area of concrete, a tent around each layer reaching zero one crack spacing away
        tl = np.zeros(NTAB)
        for l in self.layers:
            up = min(l.z + 7.5 * l.db, self.ztop)
            dn = max(l.z - 7.5 * l.db, self.zbot)
            ac = max(self.area_between(dn, up), 1e-6)
            perim = l.db * math.pi * l.num / ac
            sbar = float(self.smx_at(l.z))
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

    # -- crack spacing over the depth [B 0043f570, 0043faf0, 0043e8d0, 00440100, 0043f0d0] -----
    def _bar_terms(self) -> list[float]:
        """The second term of each layer's crack spacing, 0.1 db / rho, as Response-2000
        takes it: the bar diameter is the mean over the layers weighted by their areas, a
        layer counting in full at the layer's own height and less with distance, to nothing
        at 15 of its own diameters; rho is that weighted area over the concrete within 7.5
        of the mean diameter above and below the layer. 0.1 mm for a layer outside the
        section."""
        out = []
        for l in self.layers:
            if not self.zbot <= l.z <= self.ztop:
                out.append(0.1)
                continue
            steel = dsum = 0.0
            for o in self.layers:
                w = (15.0 - min(abs(o.z - l.z) / o.db, 15.0)) / 15.0 * o.area
                steel += w
                dsum += o.db * w
            db = dsum / steel
            conc = self.area_between(max(l.z - 7.5 * db, self.zbot), min(l.z + 7.5 * db, self.ztop))
            out.append(0.1 * db * conc / steel)
        return out

    def _aggregate_floor(self, z: float) -> float:
        """No crack spacing is under the aggregate size, taken between 2 and 25 mm."""
        return min(25.0, max(self.law_at(z).agg, 2.0))

    def _long_spacing(self, z: float, terms: list[float]) -> float:
        """The longitudinal crack spacing at a height: from the nearest layer above and the
        nearest below, twice the diagonal distance to its bars (the height apart, and half
        the spacing of the bars across the width, with the bars of layers that overlap it in
        height counted in) plus the layer's term; the lesser of the two, no more than five
        times the depth, which is also the value where there is no layer."""
        z = min(max(z, self.zbot), self.ztop)
        best = math.inf
        near = [math.inf, math.inf]
        for i, l in enumerate(self.layers):
            bars = l.num + sum(o.num for o in self.layers if o is not l and
                               (abs(o.z - l.z) < l.db or abs(o.z - l.z) < o.db))
            d = abs(l.z - z)
            for k, (side, inside) in enumerate(((l.z >= z, l.z < self.ztop),
                                                (l.z <= z, l.z > self.zbot))):
                if side and inside and d < near[k]:
                    near[k] = d
                    # the width on the side of the layer that faces the height
                    width = self.width_side(l.z, k == 1)
                    val = math.hypot(2.0 * d, width / bars) + terms[i] if width > 0 else math.inf
                    if k == 0:
                        above = val
                    else:
                        below = val
        if near[0] < math.inf:
            best = min(best, above)
        if near[1] < math.inf:
            best = min(best, below)
        return max(min(best, 5.0 * self.h), self._aggregate_floor(z))

    def _trans_spacing(self, z: float, upper: bool) -> float:
        """The transverse crack spacing at a height (on a step in width: on its upper or
        lower side): the diagonal of the stirrup spacing and the width less 100 mm, plus
        0.1 db / rho of the stirrups that reach the height; a hoop's steel counts by the
        cosine of where the height lies on its circle. Five times the depth where no
        stirrup reaches."""
        big = 5.0 * self.h
        b = self.width_side(z, upper)
        if not (b > 0 and z > self.zbot and self.stirrups):
            return big
        n = len(self.stirrups)
        rho = db = space = 0.0
        for st in self.stirrups:
            if not (st.bot <= z <= st.top and st.space > 0):
                continue
            r = st.area / st.space / b
            if st.pattern == 4:
                x = (z - 0.5 * (st.top + st.bot)) / (0.5 * (st.top - st.bot) + 0.1)
                r *= math.cos(math.asin(max(-1.0, min(1.0, x))))
            rho += r
            db += st.db / n
            space += st.space / n
        if rho <= 0.0:
            return big
        return max(math.hypot(b - 100.0, space) + 0.1 * db / rho, self._aggregate_floor(z))

    # Response's longitudinal crack spacing table: written and off (docs/kernel.md, "Crack
    # spacing over the depth"; docs/summary.md, D46)
    response_smx = False

    def _long_spacing_before(self):
        """r2c's longitudinal crack spacing before Response's table was read, at 100 evenly
        spaced heights: least over the layers of 2 c + 0.1 db / rho, c the diagonal distance
        to the nearest bar, rho the steel within 7.5 db of the layer over the concrete
        there. In use while Response's table is off."""
        if not self.layers:
            return np.full(NTAB, 5.0 * self.h)
        best = np.full(NTAB, np.inf)
        for l in self.layers:
            up = min(l.z + 7.5 * l.db, self.ztop)
            dn = max(l.z - 7.5 * l.db, self.zbot)
            ac = max(self.area_between(dn, up), 1e-6)
            steel = sum(o.area for o in self.layers if dn - 1e-9 <= o.z <= up + 1e-9)
            dx = float(self.width(np.array([l.z]))[0]) / (2.0 * l.num)
            c = np.sqrt((self.tz - l.z) ** 2 + dx * dx)
            best = np.minimum(best, 2.0 * c + 0.1 * l.db / (steel / ac))
        return best

    def _spacing_tables(self):
        """Both crack spacings as tables of points over the depth, read linearly between
        them, as Response-2000 builds them (docs/kernel.md, "Crack spacing over the depth").
        Longitudinal: at every layer and every corner of the outline, and at 0.1, 0.25,
        0.5, 0.75 and 0.9 of the way from each of those heights to the next. Transverse: at
        the top and bottom of every part of the outline (the two sides of a step in width
        0.1 mm apart) and one stirrup diameter above and below each end of a stirrup."""
        if self.smx_user > 0:
            pts = [(self.zbot, self.smx_user), (self.ztop, self.smx_user)]
        elif not self.response_smx:
            pts = list(zip(self.tz, self._long_spacing_before()))
        else:
            terms = self._bar_terms()
            keys = sorted({l.z for l in self.layers} | {self.segs[0][0]}
                          | {sg[1] for sg in self.segs}, reverse=True)
            pts = []
            for hi, lo in zip(keys[:-1], keys[1:]):
                for f in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9):
                    z = hi + f * (lo - hi)
                    pts.append((z, self._long_spacing(z, terms)))
            pts.append((self.zbot, self._long_spacing(self.zbot, terms)))
        self.p_smx = self._points(pts)
        if self.smt_user > 0:
            pts = [(self.zbot, self.smt_user), (self.ztop, self.smt_user)]
        else:
            pts = []
            last = len(self.segs) - 1
            for k, (zt, zb, wt, wb, _law) in enumerate(self.segs):
                if k == 0:
                    pts.append((zt, self._trans_spacing(zt, False)))
                elif wt != self.segs[k - 1][3]:
                    # a step: its lower side, just under the step where the section widens
                    z = zt - 0.1 if self.segs[k - 1][3] <= wt else zt
                    pts.append((z, self._trans_spacing(z, False)))
                for st in self.stirrups:
                    if zb < st.top < zt:
                        for z in (min(st.top + st.db, zt), min(st.top - st.db, zt)):
                            pts.append((z, self._trans_spacing(z, True)))
                    if zb < st.bot < zt:
                        for z in (max(st.bot + st.db, zb), max(st.bot - st.db, zb)):
                            pts.append((z, self._trans_spacing(z, True)))
                z = zb
                if k < last:
                    nxt = self.segs[k + 1][2]
                    if abs(wb - nxt) > 10.0 and wb > nxt:
                        z = zb + 0.1      # the upper side, just over a step to a narrower part
                pts.append((z, self._trans_spacing(z, True)))
        self.p_smt = self._points(pts)

    @staticmethod
    def _points(pts):
        """Points (height, value) as arrays for reading, from the bottom up; points at one
        height keep the order they were made in from the top down."""
        pts = sorted(enumerate(pts), key=lambda p: (p[1][0], -p[0]))
        return (np.array([p[1][0] for p in pts]), np.array([p[1][1] for p in pts]))

    def smx_at(self, z):
        """Longitudinal crack spacing at heights z: never more than the depth."""
        return np.minimum(np.interp(z, *self.p_smx), self.h)

    def smt_at(self, z):
        """Transverse crack spacing at heights z."""
        return np.interp(z, *self.p_smt)

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
