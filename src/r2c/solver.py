"""The sectional analysis: forces from a strain state (with dynamic layering and the flexural
crack check), the solution for a load stage, and the stepping through a full response.

Follows chapter 7 of Bentz's thesis. The global strain state is (e0, phi, gam): the longitudinal
strain at the centroid of the gross concrete section, the curvature, and the average shear
strain. Plane sections: ex(y) = e0 - phi y, y measured up from that centroid, so a positive
curvature compresses the top, which is the sign of a positive moment.

Units: mm, MPa, N, N mm.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from r2c import node as nodelib
from r2c.section import Section

BIG = 1e9
FAR = 1e6            # stands for a neutral axis outside the section (whole section in tension)


STEP = 1e-6          # mm: how far from a step in width the shear strain profile is read


class SolveError(RuntimeError):
    """No equilibrium state was found for a load stage."""


@dataclass
class Detail:
    """Everything known at the nodes for one strain state (top node first)."""
    z: np.ndarray
    b: np.ndarray
    ex: np.ndarray
    ey: np.ndarray
    gxy: np.ndarray
    out: nodelib.NodeOut
    smx: np.ndarray
    smt: np.ndarray
    fsy: np.ndarray          # average stirrup stress
    fsycr: np.ndarray        # stirrup stress at a crack
    rhov: np.ndarray
    fs: np.ndarray           # average stress, one per longitudinal layer
    fscr: np.ndarray         # stress at a crack, one per layer
    es: np.ndarray           # strain of each layer (with prestrain)
    f1cx: np.ndarray
    vcalc: np.ndarray | None = None     # shear stress from the longitudinal stiffness method


@dataclass
class Stage:
    e0: float
    phi: float
    gam: float
    lam: float
    n: float
    m: float
    v: float
    detail: Detail
    control: float = 0.0
    event: bool = False
    cmode: str | None = None      # the control variable the stage was found in


class Analysis:
    def __init__(self, sec: Section, const=(0.0, 0.0, 0.0), incr=(0.0, 1.0, 0.0)):
        self.sec = sec
        self.n0, self.m0, self.v0 = const
        self.dn, self.dm, self.dv = incr
        self.shear = (self.dv != 0.0) or (self.v0 != 0.0)
        self.t_ft = sec.cracking_table(self.n0, self.m0, self.dn, self.dm)
        self.bounds = self._initial_bounds()
        # the shear strain profile's grid: the tables' heights, and a point just above and
        # just below every step in width, where the shear strain jumps
        self.steps = np.array([z for z in sec.breaks()[1:-1]
                               if abs(sec.width_side(z, True) - sec.width_side(z, False))
                               > 1e-6])
        self.shape_z = np.array(sorted(set(sec.tz.tolist())
                                       | {z + d for z in self.steps for d in (-STEP, STEP)}))
        self.shape_z0 = self.shape_z.copy()      # the profile's base grid
        self.shape = self._elastic_shape()
        self.max_layers = 220
        # plastic strain of each layer, from which it unloads elastically
        self.ep0 = np.zeros(len(sec.layers))
        self.ep = self.ep0.copy()
        self.epy = np.zeros(len(sec.tz))        # plastic strain of the stirrups, by depth
        self.dead = np.zeros(len(sec.layers), dtype=bool)   # ruptured at a crack
        self.last_ey = None

    # -- layers ---------------------------------------------------------------------------------
    def _initial_bounds(self) -> np.ndarray:
        """The layers every stage starts from, as Response-2000 builds them (docs/kernel.md,
        "Layers"): each stretch of the outline in equal layers, about seven to the depth of
        the section, then a boundary at the upper and at the lower edge of every bar."""
        sec = self.sec
        h = sec.h
        bd: list[float] = []
        for z1, z2, *_ in sec.segs:
            n = int((z1 - z2) * 8.0 / (h + 0.1) + 0.99)
            nl = max(n - 1, 1)
            bd.extend(z1 - (z1 - z2) * i / nl for i in range(nl))
        bd.append(sec.zbot)
        bd = sorted(set(round(z, 9) for z in bd) | set(sec.breaks()), reverse=True)
        sliver = h / 2048.0
        near = 0.2          # mm
        for l in sec.layers:
            for second in (False, True):
                for i in range(len(bd) - 1):
                    lt, lb = bd[i], bd[i + 1]
                    if not (abs(lt - l.z) < 1.0 or l.z <= lt):
                        continue
                    if second:
                        if not lb < l.z:
                            continue
                    elif not (l.z < lt and (lb < l.z or abs(lb - l.z) < 0.1)):
                        continue
                    top = min(l.z + l.db / 2.0, lt)
                    bot = max(l.z - l.db / 2.0, lb)
                    if abs(top - lt) >= near:
                        if top < lt and bot != lb and abs(lb - top) > sliver \
                                and abs(lt - top) > sliver:
                            bd.insert(i + 1, top)
                    elif abs(bot - lb) >= near and bot > lb and abs(lb - bot) > sliver \
                            and abs(lt - bot) > sliver:
                        bd.insert(i + 1, bot)
                    break
        return np.array(bd)

    def _elastic_shape(self) -> np.ndarray:
        """Shear strain profile of the uncracked section (VQ/Ib), scaled to a mean of one."""
        sec = self.sec
        z = self.shape_z
        b = np.maximum(sec.width(z), 1e-9)
        # first moment of the area above z about the centroid
        q = np.zeros_like(z)
        for i in range(len(z) - 2, -1, -1):
            zz = np.linspace(z[i], z[i + 1], 5)
            bb = sec.width(zz)
            q[i] = q[i + 1] + np.trapezoid(bb * (zz - sec.zc), zz)
        tau = q / b
        tau[0] = tau[-1] = 0.0
        mean = np.trapezoid(tau * b, z) / np.trapezoid(b, z)
        return tau / mean if mean > 0 else np.ones_like(z)

    def profile(self):
        """The shear strain profile as it is: (heights, values), to put back later."""
        return self.shape_z.copy(), self.shape.copy()

    def set_profile(self, p):
        self.shape_z, self.shape = p[0].copy(), p[1].copy()

    def profile_z(self, z):
        """Heights at which the shear strain profile is read for nodes z of shape (L, 3): a
        layer's top or bottom node on a step in width is read on the layer's own side."""
        if not len(self.steps) or z.ndim != 2 or z.shape[1] != 3:
            return z
        zp = z.copy()
        for zs in self.steps:
            zp[np.abs(z[:, 0] - zs) < 1e-9, 0] = zs - STEP
            zp[np.abs(z[:, 2] - zs) < 1e-9, 2] = zs + STEP
        return zp

    def layer_nodes(self, bounds=None):
        """(z, b) arrays of shape (L, 3): top, middle and bottom of every layer."""
        sec = self.sec
        bd = self.bounds if bounds is None else bounds
        zt, zb = bd[:-1], bd[1:]
        zm = 0.5 * (zt + zb)
        z = np.stack([zt, zm, zb], axis=1)
        b = np.empty_like(z)
        b[:, 1] = sec.width(zm)
        b[:, 0] = [sec.width_side(v, upper=False) for v in zt]
        b[:, 2] = [sec.width_side(v, upper=True) for v in zb]
        return z, b

    # -- strain state ---------------------------------------------------------------------------
    def strain(self, e0, phi, z):
        return e0 - phi * (np.asarray(z) - self.sec.zc)

    def steel(self, e0, phi):
        """(strain incl. prestrain, average stress) of every longitudinal layer."""
        sec = self.sec
        es = np.array([float(self.strain(e0, phi, l.z)) + l.prestrain for l in sec.layers])
        fs = np.empty(len(es))
        for i, (l, e) in enumerate(zip(sec.layers, es)):
            env = float(l.steel.raw(e))
            if not math.isnan(env):
                # a bar that has yielded unloads along its elastic stiffness
                lin = (e - self.ep[i]) * l.steel.E
                if env > 0:
                    if env - lin > 1e-6:
                        env = lin
                    env = max(env, -l.steel.fy)
                elif env < 0:
                    env = min(max(lin, env), l.steel.fy)
            fs[i] = float("nan") if self.dead[i] else env * l.steel.phi
        return es, fs

    def commit_stirrups(self, det):
        """Record the plastic strain of the stirrups over the depth at an accepted stage."""
        sec = self.sec
        if not sec.stirrups:
            return
        st = sec.stirrups[0].steel
        z = np.asarray(det.z, dtype=float)
        # in the stirrup's own strain: a hoop is strained by less than the concrete (7-6)
        fac = self.stirrups_at(z, det.b)[0][2]
        ep = np.asarray(det.ey, dtype=float) * fac \
            - np.asarray(det.fsy, dtype=float) / (st.E * st.phi)
        ep = np.where((np.asarray(det.rhov) > 0) & (ep > 1e-9), ep, 0.0)
        order = np.argsort(z)
        self.epy = np.maximum(self.epy, np.interp(sec.tz, z[order], ep[order]))

    def commit(self, e0, phi):
        """Record the plastic strain of each bar at an accepted load stage."""
        es, fs = self.steel(e0, phi)
        for i, l in enumerate(self.sec.layers):
            if not math.isnan(fs[i]) and es[i] > 0:
                cap = float(l.steel.crack_capacity(es[i] - l.prestrain, l.prestrain, l.rho,
                                                   l.strand))
                if math.isnan(cap):
                    self.dead[i] = True      # the bar has ruptured at a crack
            if math.isnan(fs[i]):
                continue
            ep = es[i] - fs[i] / l.steel.phi / l.steel.E
            if es[i] > 0:
                self.ep[i] = max(self.ep[i], ep) if self.ep[i] >= 0 else ep
            elif es[i] < 0:
                self.ep[i] = min(self.ep[i], ep) if self.ep[i] <= 0 else ep

    def crack_check(self, e0, phi, es, fs):
        """The flexural crack check (thesis 4-5): the largest average concrete tension each
        tension zone can carry without the bars crossing it exceeding their capacity at a
        crack. Returns a function f1cx(z)."""
        sec = self.sec
        ztop, zbot, zc = sec.ztop, sec.zbot, sec.zc
        etop = float(self.strain(e0, phi, ztop))
        ebot = float(self.strain(e0, phi, zbot))
        zna = zc + e0 / phi if abs(phi) > 1e-18 else None

        def crossing():
            if zna is not None and zbot < zna < ztop:
                return zna
            return None

        na = crossing()
        # tension zone reaching the top face: z in (z3, ztop]; the bottom face: [zbot, z4)
        if etop > 0:
            z3 = na if (na is not None and ebot < 0) else -FAR
        else:
            z3 = ztop
        if ebot > 0:
            z4 = na if (na is not None and etop <= 0) else FAR
        else:
            z4 = zbot
        mtop = mbot = 0.0
        ntop = nbot = 0
        for l, e, f in zip(sec.layers, es, fs):
            if not (l.z > z3 or l.z < z4):
                continue
            if math.isnan(f):
                continue
            cap = float(l.steel.crack_capacity(e - l.prestrain, l.prestrain, l.rho, l.strand))
            df = 0.0 if math.isnan(cap) else max(cap - f, 0.0)
            near = min(min(abs(l.z - z4), abs(l.z - z3)) / (l.db + 0.1), 1.0)
            if l.z > z3:
                mtop += abs(z3 - l.z) * near * l.area * df + 100.0
                ntop += 1
            if l.z < z4:
                mbot += abs(z4 - l.z) * near * l.area * df + 100.0
                nbot += 1
        zones = []
        for zn, face, mcap, count in ((z3, ztop, mtop, ntop), (z4, zbot, mbot, nbot)):
            hh = abs(face - zn)
            if hh < 0.1 or count == 0:
                continue
            lo, hi = (max(zn, zbot), ztop) if face == ztop else (zbot, min(zn, ztop))
            i1 = i2 = i3 = ma = mb = 0.0
            for z1, z2, b1, b2, law in sec.segs:
                u, d = min(z1, hi), max(z2, lo)
                if u <= d:
                    continue
                zz = np.linspace(d, u, 9)
                bb = b2 + (b1 - b2) * (zz - z2) / (z1 - z2)
                x = np.abs(zz - zn)
                a1 = np.trapezoid(bb * x, zz)
                a2 = np.trapezoid(bb * x * (hh - x) / hh, zz)
                a3 = np.trapezoid(bb * x * x / hh, zz)
                i1 += a1
                i2 += a2
                i3 += a3
                ma += law.ft * law.phi * a1 * 0.6
                mb += law.ft * law.phi * a2 * (3.0 - 0.6)
            lawf = sec.law_at(face)
            lawn = sec.law_at(min(max(zn, zbot), ztop))
            p4 = 0.6 * lawf.ft * lawf.phi
            p5 = 3.0 * lawn.ft * lawn.phi
            if mcap <= ma + mb:
                if mcap <= ma:
                    fna = fface = mcap / i1 if i1 > 0 else 0.0
                else:
                    fface = p4
                    fna = (mcap - ma) / i2 + p4 if i2 > 0 else p4
            else:
                fna = p5
                fface = (mcap - ma - mb) / i3 + p4 if i3 > 0 else p4
            zones.append((zn, face, fna, fface))

        def f1cx(z):
            z = np.asarray(z, dtype=float)
            out = np.full(z.shape, BIG)
            for zn, face, fna, fface in zones:
                inside = (z > zn) if face == ztop else (z < zn)
                tt = np.clip(np.abs(z - zn) / abs(face - zn), 0.0, 1.0)
                out = np.where(inside, np.minimum(out, fna + (fface - fna) * tt), out)
            return out
        return f1cx

    # -- nodes ----------------------------------------------------------------------------------
    def eval_nodes(self, e0, phi, gam, z, f1cx, ey=None):
        """Concrete stresses at heights z (any shape) for the global strain state."""
        sec = self.sec
        shp = z.shape
        zf = z.ravel()
        # the concrete's own strain: the section's, less what shrinkage or temperature
        # would give it unrestrained
        ex = self.strain(e0, phi, zf) - sec.shrinkage(zf)
        m = sec.tab(sec.t_m, zf)
        ft = np.interp(zf, sec.tz, self.t_ft)
        smx = sec.tab(sec.t_smx, zf)
        smt = sec.tab(sec.t_smt, zf)
        cx = f1cx(zf)
        g = gam * np.interp(self.profile_z(z).ravel(), self.shape_z, self.shape) \
            if gam != 0.0 else np.zeros_like(zf)
        if self.shear and ey is None:
            out, eyv = self.transverse(zf, z, ex, g, m, ft, smx, smt, cx)
            return out, ex, g, smx, smt, eyv
        eyv = np.zeros_like(zf) if ey is None else ey.ravel()
        cy = np.zeros_like(zf)
        if len(sec.laws) == 1:
            out = nodelib.evaluate(sec.laws[0], ex, eyv, g, m, ft, smx, smt, cx, cy)
        else:
            # a node on the boundary of two concretes belongs to the layer it was made for
            idx = self.law_index(zf, z)
            fields = {}
            for j, law in enumerate(sec.laws):
                k = idx == j
                if not k.any():
                    continue
                o = nodelib.evaluate(law, ex[k], eyv[k], g[k], m[k], ft[k], smx[k], smt[k],
                                     cx[k], cy[k])
                for name, val in o.__dict__.items():
                    fields.setdefault(name, np.zeros(len(zf), dtype=val.dtype))[k] = val
            out = nodelib.NodeOut(**fields)
        return out, ex, g, smx, smt, eyv

    # -- transverse equilibrium (shear) ---------------------------------------------------------
    def law_index(self, zf, z):
        sec = self.sec
        if len(sec.laws) == 1:
            return np.zeros(len(zf), dtype=int)
        zmid = np.repeat(z.reshape(-1, z.shape[-1])[:, z.shape[-1] // 2], z.shape[-1]) \
            if z.ndim == 2 else zf
        zl = zf + 1e-6 * np.sign(zmid - zf)
        idx = np.zeros(len(zf), dtype=int)
        for j, law in enumerate(sec.laws):
            for z1, z2, _, _, lw in sec.segs:
                if lw is law:
                    idx[(zl <= z1) & (zl >= z2)] = j
        return idx

    def node_width(self, z):
        """Width at nodes z of shape (L, 3), flattened: on a step in width, the width of the
        node's own layer."""
        return self.sec.width(self.profile_z(z).ravel())

    def stirrups_at(self, zf, bw=None):
        """For every stirrup type: (ratio by node, strain factor, force factor). bw is the
        width at each node where the caller knows which side of a step the node is on."""
        sec = self.sec
        bw = np.maximum(sec.width(zf) if bw is None else bw, 1e-6)
        out = []
        for st in sec.stirrups:
            inside = (zf >= st.bot - 1e-9) & (zf <= st.top + 1e-9)
            rho = np.where(inside, st.area / (bw * st.space), 0.0)
            if st.pattern == 4:
                # a hoop: only the part of it across the shear works (thesis 7-6)
                r = 0.5 * (st.top - st.bot)
                d = zf - 0.5 * (st.top + st.bot)
                sin2 = np.clip(1.0 - d * d / (r * r + 1e-4), 0.0, 1.0)
                sin2 = np.where(sin2 <= 0.0, 1.0, sin2)
                out.append((st, rho * np.sqrt(sin2), sin2))
            else:
                out.append((st, rho, np.ones_like(zf)))
        return out

    def stirrup_stress(self, sts, ey, rcrit, epy=None):
        """(total average stress rho fsy, crack reserve f1cy, total ratio). rcrit is the steel
        ratio that sets the strain concentration at a crack; epy the plastic strain the
        stirrups unload from."""
        tot = np.zeros_like(ey)
        yld = np.zeros_like(ey)
        capt = np.zeros_like(ey)
        rho_t = np.zeros_like(ey)
        a_n = np.zeros_like(ey)
        a_s = np.zeros_like(ey)
        sec = self.sec
        for st, rho, fac in sts:
            if not rho.any():
                continue
            inside = rho > 0
            e = ey * fac + st.prestrain
            fs = st.steel.stress(e)
            fs = np.where(np.isnan(fs), 0.0, fs)
            if epy is not None:
                lin = (e - epy) * st.steel.E * st.steel.phi
                fs = np.where((fs > 0) & (fs - lin > 1e-6),
                              np.maximum(lin, -st.steel.fy * st.steel.phi), fs)
            cap = st.steel.crack_capacity(ey * fac, st.prestrain, rcrit, st.strand)
            cap = np.where(np.isnan(cap), fs, cap)
            tot += rho * fs
            yld += rho * st.steel.fy * st.steel.phi
            capt += rho * cap
            rho_t += rho
            a_n += np.where(inside, st.area / len(sec.stirrups), 0.0)
            a_s += np.where(inside, st.area / (st.space + 1e-4), 0.0)
        eff = np.clip(0.5 * (3.0 - a_n / (a_s + 1e-9) / sec.h), 0.0, 1.0)
        res = eff * (np.maximum(yld, capt) - tot)
        return tot, res, rho_t

    def transverse(self, zf, z, ex, g, m, ft, smx, smt, cx):
        """The transverse strain of every node, from the condition that there is no total
        stress across the member: concrete fcy and the stirrups balance (thesis 7-2)."""
        sec = self.sec
        sts = self.stirrups_at(zf, self.node_width(z))
        rcrit = sec.tab(sec.t_rhocrit, zf)
        epy = np.interp(zf, sec.tz, self.epy)
        idx = self.law_index(zf, z)
        n = len(zf)

        def run(ey):
            """Total transverse stress for an array ey of shape (n,) or (n, k)."""
            shp = ey.shape
            k = 1 if ey.ndim == 1 else shp[1]
            eyf = ey.reshape(n, k)
            tot = np.empty((n, k))
            outs = []
            for j, law in enumerate(sec.laws):
                sel = idx == j
                if not sel.any():
                    outs.append(None)
                    continue
                rep = lambda a: np.repeat(a[sel], k)
                eyl = eyf[sel].ravel()
                subs = [(st, np.repeat(rho[sel], k), np.repeat(fac[sel], k))
                        for st, rho, fac in sts]
                st_tot, st_res, _ = self.stirrup_stress(subs, eyl, rep(rcrit), rep(epy))
                o = nodelib.evaluate(law, rep(ex), eyl, rep(g), rep(m), rep(ft), rep(smx),
                                     rep(smt), rep(cx), st_res)
                tot[sel] = (o.fcy + st_tot).reshape(-1, k)
                outs.append(o)
            return tot.reshape(shp), outs

        # scan a ladder of transverse strains for the first change of sign, then close in
        mag = 1e-6 * 1.7 ** np.arange(0, 21)
        ladder = np.concatenate([-mag[::-1][6:], [0.0], mag])
        f, _ = run(np.broadcast_to(ladder, (n, len(ladder))).copy())
        pos = f > 0
        first = np.argmax(pos, axis=1)
        none = ~pos.any(axis=1)
        first = np.where(none, len(ladder) - 1, first)
        first = np.maximum(first, 1)
        rows = np.arange(n)
        lo, hi = ladder[first - 1], ladder[first]
        flo, fhi = f[rows, first - 1], f[rows, first]
        ok = (flo <= 0) & (fhi > 0)
        ey = np.where(np.abs(flo) < np.abs(fhi), lo, hi)
        for it in range(40):
            with np.errstate(divide="ignore", invalid="ignore"):
                x = np.where(fhi != flo, lo - flo * (hi - lo) / (fhi - flo), 0.5 * (lo + hi))
            if it % 3 == 2:
                x = 0.5 * (lo + hi)
            x = np.clip(x, np.minimum(lo, hi), np.maximum(lo, hi))
            fx, _ = run(x)
            neg = fx <= 0
            lo = np.where(ok & neg, x, lo)
            flo = np.where(ok & neg, fx, flo)
            hi = np.where(ok & ~neg, x, hi)
            fhi = np.where(ok & ~neg, fx, fhi)
            ey = np.where(ok, x, ey)
            if np.max(np.where(ok, np.abs(fx), 0.0)) < 1e-7 or \
                    np.max(np.where(ok, np.abs(hi - lo), 0.0)) < 1e-12:
                break
        _, outs = run(ey)
        fields = {}
        for j, o in enumerate(outs):
            if o is None:
                continue
            sel = idx == j
            for name, val in o.__dict__.items():
                fields.setdefault(name, np.zeros(n, dtype=val.dtype))[sel] = val
        return nodelib.NodeOut(**fields), ey

    def forces(self, e0, phi, gam=0.0, bounds=None, want_detail=False):
        """(N, M, V) for a strain state on the current layers."""
        sec = self.sec
        z, b = self.layer_nodes(bounds)
        es, fs = self.steel(e0, phi)
        f1cx = self.crack_check(e0, phi, es, fs)
        out, ex, g, smx, smt, eyn = self.eval_nodes(e0, phi, gam, z, f1cx)
        fcx = out.fcx.reshape(z.shape)
        vv = out.v.reshape(z.shape)
        dz = z[:, 0] - z[:, 2]
        w = np.array([1.0, 4.0, 1.0]) / 6.0
        fb = fcx * b
        n = float(np.sum((fb @ w) * dz))
        m = float(-np.sum(((fb * (z - sec.zaxial)) @ w) * dz))
        v = float(np.sum(((vv * b) @ w) * dz))
        if sec.layers:
            # the concrete is net of the bars: each bar displaces its own area of concrete
            zb = np.array([l.z for l in sec.layers])
            ob, *_ = self.eval_nodes(e0, phi, gam, zb, f1cx)
            for l, f, fc in zip(sec.layers, fs, ob.fcx):
                net = (0.0 if math.isnan(f) else f) - fc
                n += net * l.area
                m -= net * l.area * (l.z - sec.zaxial)
        if not want_detail:
            return n, m, v
        return n, m, v, (z, b, out, ex, g, smx, smt, es, fs, f1cx, eyn)

    def refine(self, e0, phi, gam):
        """Dynamic layering, as Response-2000 does it (docs/kernel.md, "Layers"): each half of
        a layer is checked at its middle against the parabola through the layer's three nodes,
        and a layer with a half that fails is split in two; a half that passed is not looked
        at again. The layers are built from the base layers each time, for this strain state
        alone. Returns True if they are not the layers there were."""
        sec = self.sec
        before = self.bounds
        self.bounds = self._initial_bounds()
        es, fs = self.steel(e0, phi)
        f1cx = self.crack_check(e0, phi, es, fs)
        hmin = sec.h / 1024.0
        z, _b = self.layer_nodes()
        out, *_ = self.eval_nodes(e0, phi, gam, z, f1cx)
        tol1 = 0.002 * max(float(np.max(np.abs(out.f1))), 1e-6)
        tol2 = 0.002 * max(float(np.max(np.abs(out.f2))), 1e-6)
        done = np.zeros(len(z), dtype=bool)
        for _ in range(16):
            z, _b = self.layer_nodes()
            if len(z) >= self.max_layers - 2 or done.all():
                break
            out, *_ = self.eval_nodes(e0, phi, gam, z, f1cx)
            f1 = out.f1.reshape(z.shape)
            f2 = out.f2.reshape(z.shape)
            over = (out.e1 - out.ecr).reshape(z.shape)
            zq = np.stack([0.75 * z[:, 0] + 0.25 * z[:, 2], 0.25 * z[:, 0] + 0.75 * z[:, 2]],
                          axis=1)
            oq, *_ = self.eval_nodes(e0, phi, gam, zq, f1cx)
            q1 = oq.f1.reshape(zq.shape)
            q2 = oq.f2.reshape(zq.shape)

            def interp(f):
                # parabola through the three nodes at the quarter points
                a = 0.375 * f[:, 0] + 0.75 * f[:, 1] - 0.125 * f[:, 2]
                c = -0.125 * f[:, 0] + 0.75 * f[:, 1] + 0.375 * f[:, 2]
                return np.stack([a, c], axis=1)
            bad = np.abs(interp(f1) - q1) > tol1
            bad |= np.abs(interp(f2) - q2) > tol2
            # the crack front passes through the half
            a, m, c = over[:, 0], over[:, 1], over[:, 2]
            bad[:, 0] |= ((a < 0) & (m > 0)) | ((a > 0) & (m < 0))
            bad[:, 1] |= ((m < 0) & (c > 0)) | ((m > 0) & (c < 0))
            thick = 0.5 * (z[:, 0] - z[:, 2]) > hmin
            bad &= (thick & ~done)[:, None]
            split = bad.any(axis=1)
            done |= ~split
            if not split.any():
                break
            room = self.max_layers - 2 - len(z)
            idx = np.nonzero(split)[0][:room]
            keep = np.zeros(len(z), dtype=bool)
            keep[idx] = True
            bounds, flags = [], []
            for i in range(len(z)):
                bounds.append(z[i, 0])
                if keep[i]:
                    flags.append(not bad[i, 0])
                    bounds.append(z[i, 1])
                    flags.append(not bad[i, 1])
                else:
                    flags.append(bool(done[i]))
            bounds.append(z[-1, 2])
            self.bounds = np.array(bounds)
            done = np.array(flags)
        return len(before) != len(self.bounds) or not np.array_equal(before, self.bounds)

    def coarsen(self):
        """Start a stage from the base layers again (the crack front has moved on)."""
        self.bounds = self._initial_bounds()

    def detail(self, e0, phi, gam) -> Detail:
        sec = self.sec
        n, m, v, (z, b, out, ex, g, smx, smt, es, fs, f1cx, eyn) = self.forces(
            e0, phi, gam, want_detail=True)
        # unique nodes from the top down (shared layer boundaries once, unless the concrete or
        # the width changes there: then the upper layer's value is kept)
        zf = z.ravel()
        keep = np.ones(len(zf), dtype=bool)
        keep[3::3] = False
        sel = np.nonzero(keep)[0]
        o2 = nodelib.NodeOut(**{k: val[sel] for k, val in out.__dict__.items()})
        zz = zf[sel]
        fscr = self.steel_at_crack(e0, phi, es, fs, zz, o2, b.ravel()[sel])
        rhov = sec.tab(sec.t_rhov, zz)
        ey = eyn[sel]
        fsy = np.zeros(len(sel))
        fsycr = np.zeros(len(sel))
        if self.shear and sec.stirrups:
            tot, _res, rho_t = self.stirrup_stress(self.stirrups_at(zz, b.ravel()[sel]), ey,
                                                   sec.tab(sec.t_rhocrit, zz),
                                                   np.interp(zz, sec.tz, self.epy))
            has = rho_t > 0
            fsy[has] = tot[has] / rho_t[has]
            # at a crack the stirrups also carry what the concrete carries between cracks
            law = sec.conc0
            fl = np.maximum(law.ft, np.interp(zz, sec.tz, self.t_ft)) / (1.0 + 250.0 * o2.w) \
                * law.phi
            extra = np.maximum(o2.f1 - fl, 0.0) - o2.vci * o2.tan
            on = has & (o2.w > 0)
            fsycr[on] = extra[on] / rho_t[on] + fsy[on]
        return Detail(z=zz, b=b.ravel()[sel], ex=ex[sel], ey=ey, gxy=g[sel],
                      out=o2, smx=smx[sel], smt=smt[sel], fsy=fsy,
                      fsycr=fsycr, rhov=rhov, fs=fs, fscr=fscr, es=es,
                      f1cx=f1cx(zz))

    def steel_at_crack(self, e0, phi, es, fs, z, out, b):
        """Stress of each longitudinal layer at a crack (thesis 4-5, last part): the moment of
        the average concrete tension about the crack front is taken by an extra curvature of
        the bars crossing the cracked zone."""
        sec = self.sec
        res = np.zeros(len(sec.layers))
        if not len(sec.layers):
            return res
        cr = out.cracked
        if not cr.any():
            return res
        # cracked zones: contiguous runs of cracked nodes (nodes run from the top down)
        runs = []
        start = None
        for i, c in enumerate(cr):
            if c and start is None:
                start = i
            if (not c or i == len(cr) - 1) and start is not None:
                end = i if c else i - 1
                runs.append((start, end))
                start = None
        for a, e in runs:
            if e <= a:
                continue
            zt, zb = z[a], z[e]
            # the crack front is the end of the run nearer the neutral axis
            ext = self.strain(e0, phi, zt)
            exb = self.strain(e0, phi, zb)
            front = zt if abs(ext) < abs(exb) else zb
            zz = z[a:e + 1]
            ff = out.f1crack[a:e + 1] * np.abs(np.sin(out.theta[a:e + 1])) ** 2
            ff = np.maximum(out.f1[a:e + 1], 0.0)
            mom = abs(np.trapezoid(ff * b[a:e + 1] * np.abs(zz - front), zz))
            bars = [(i, l) for i, l in enumerate(sec.layers)
                    if min(zt, zb) - 1e-6 <= l.z <= max(zt, zb) + 1e-6 and not math.isnan(fs[i])]
            if not bars or mom <= 0:
                continue

            def resist(dphi):
                tot = 0.0
                for i, l in bars:
                    arm = abs(l.z - front)
                    s = float(l.steel.stress(es[i] + dphi * arm))
                    if math.isnan(s):
                        s = l.steel.fu * l.steel.phi
                    tot += (s - fs[i]) * l.area * arm
                return tot
            lo, hi = 0.0, 1e-9
            for _ in range(60):
                if resist(hi) >= mom:
                    break
                hi *= 2.0
            else:
                for i, l in bars:
                    res[i] = float("nan")
                continue
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                if resist(mid) >= mom:
                    hi = mid
                else:
                    lo = mid
            for i, l in bars:
                s = float(l.steel.stress(es[i] + hi * abs(l.z - front)))
                res[i] = s
        return res


# ---------------------------------------------------------------------------------------------
# Solving a load stage and stepping through the response (no shear)
# ---------------------------------------------------------------------------------------------
JUMP_TOL = 1e-4


def _root(f, x0, dx, tol, maxit=80):
    """A root of the scalar function f near x0. Secant steps first; if they find no change of
    sign, the neighbourhood of x0 is scanned outwards for one (the force of a cracking section
    is not monotonic in the strain), and the root is then closed in on inside the bracket.
    A jump across zero counts as the root. Returns (x, ok)."""
    fa = f(x0)
    if abs(fa) <= tol:
        return x0, True
    xa = x0
    xb, fb = x0 + dx, None
    lo = hi = None          # f(lo) < 0 < f(hi)
    flo = fhi = None
    for it in range(8):
        fb = f(xb)
        if math.isnan(fb):
            break
        if abs(fb) <= tol:
            return xb, True
        if fa * fb < 0:
            (lo, flo, hi, fhi) = (xa, fa, xb, fb) if fa < 0 else (xb, fb, xa, fa)
            break
        if fb == fa:
            break
        xn = xb - fb * (xb - xa) / (fb - fa)
        lim = 6.0 * max(abs(xb - xa), abs(dx))
        if abs(xn - xb) > lim:
            xn = xb + math.copysign(lim, xn - xb)
        xa, fa, xb = xb, fb, xn
    if lo is None:
        f0 = f(x0)
        prev = {1: (x0, f0), -1: (x0, f0)}
        step = abs(dx)
        for k in range(70):
            for sgn in (1, -1):
                x = x0 + sgn * step
                fx = f(x)
                if math.isnan(fx):
                    continue
                if abs(fx) <= tol:
                    return x, True
                px, pf = prev[sgn]
                if pf * fx < 0:
                    (lo, flo, hi, fhi) = (px, pf, x, fx) if pf < 0 else (x, fx, px, pf)
                    break
                prev[sgn] = (x, fx)
            if lo is not None:
                break
            step *= 1.5
        if lo is None:
            return x0, False
    for it in range(maxit):
        if it % 3 == 2 or flo == fhi:
            x = 0.5 * (lo + hi)
        else:
            x = lo - flo * (hi - lo) / (fhi - flo)
            w = abs(hi - lo)
            if abs(x - lo) < 0.01 * w or abs(x - hi) < 0.01 * w:
                x = 0.5 * (lo + hi)
        fx = f(x)
        if math.isnan(fx):
            return x, False
        if abs(fx) <= tol:
            return x, True
        if fx < 0:
            lo, flo = x, fx
        else:
            hi, fhi = x, fx
        if abs(hi - lo) <= 1e-13 * max(abs(dx) * 1e6, abs(lo), abs(hi)):
            break
    # the bracket has closed on a jump: a root only if the jump is small
    x, fx = (lo, flo) if abs(flo) < abs(fhi) else (hi, fhi)
    return x, abs(fx) <= JUMP_TOL


class Flexure:
    """Full response without shear: axial load and moment."""

    def __init__(self, an: Analysis, on_stage=None):
        self.an = an
        self.sec = an.sec
        self.stages: list[Stage] = []
        self.on_stage = on_stage
        sec = self.sec
        # scales for convergence
        self.nscale = max(sec.conc0.fcp * sec.area, 1.0)
        self.mscale = self.nscale * sec.h
        an_m, an_n = an.dm != 0.0, an.dn != 0.0
        if an_n:
            # an axial load increment: Response steps the strain at the centroid
            self.mode = "e0"
            self.step0 = sec.conc0.e0 / 20.0
            self.sign = 1.0 if an.dn > 0 else -1.0
        elif an_m:
            self.mode = "phi"
            base = 0.2e-3 / sec.h
            if an.n0 != 0.0:
                base *= 0.5
            self.step0 = base
            self.sign = 1.0 if an.dm > 0 else -1.0
        else:
            self.mode = "none"
            self.step0 = 0.0
            self.sign = 1.0

    # -- one state ------------------------------------------------------------------------------
    def _solve_fixed_layers(self, c, guess):
        an = self.an
        tol = 1e-7
        if self.mode == "phi":
            phi = c

            def res(e0):
                n, m, _ = an.forces(e0, phi)
                lam = (m - an.m0) / an.dm
                return (n - an.n0 - lam * an.dn) / self.nscale
            x, ok = _root(res, guess, 1e-6, tol)
            return x, phi, ok
        e0 = c

        def res(phi):
            n, m, _ = an.forces(e0, phi)
            lam = (n - an.n0) / an.dn
            return (m - an.m0 - lam * an.dm) / self.mscale
        x, ok = _root(res, guess, 1e-9, tol)
        return e0, x, ok

    def solve(self, c, prev: Stage | None) -> Stage:
        """The state at control value c (curvature, or strain at the centroid)."""
        an = self.an
        if prev is None:
            guess = 0.0
        else:
            guess = prev.e0 if self.mode == "phi" else prev.phi
        an.coarsen()
        ok = False
        e0 = phi = 0.0
        for _ in range(5):
            e0, phi, ok = self._solve_fixed_layers(c, guess)
            if not ok:
                break
            guess = e0 if self.mode == "phi" else phi
            if not an.refine(e0, phi, 0.0):
                break
        else:
            e0, phi, ok = self._solve_fixed_layers(c, guess)
        if not ok:
            raise SolveError(f"no equilibrium at control value {c:g}")
        n, m, v = an.forces(e0, phi)
        if self.mode == "phi":
            lam = (m - an.m0) / an.dm
        else:
            lam = (n - an.n0) / an.dn
        det = an.detail(e0, phi, 0.0)
        return Stage(e0, phi, 0.0, lam, n, m, v, det, control=c)

    def initial(self) -> Stage:
        """The state under the constant loads alone."""
        an = self.an
        if an.n0 == 0.0 and an.m0 == 0.0 and not self.sec.shrink \
                and not any(l.prestrain for l in self.sec.layers):
            e0, phi = 0.0, 0.0
        else:
            sc = np.array([1e-4, 1e-4 / self.sec.h])
            ok = False
            for x in self._initial_guesses():
                ok = False
                for _ in range(4):
                    for it in range(60):
                        n, m, _ = an.forces(x[0], x[1])
                        r = np.array([(n - an.n0) / self.nscale, (m - an.m0) / self.mscale])
                        if np.max(np.abs(r)) < 1e-8:
                            ok = True
                            break
                        jac = np.empty((2, 2))
                        for j in range(2):
                            xx = x.copy()
                            xx[j] += 1e-3 * sc[j]
                            n2, m2, _ = an.forces(xx[0], xx[1])
                            jac[:, j] = (np.array([(n2 - an.n0) / self.nscale,
                                                   (m2 - an.m0) / self.mscale]) - r) \
                                / (1e-3 * sc[j])
                        try:
                            dx = np.linalg.solve(jac, -r)
                        except np.linalg.LinAlgError:
                            break
                        # a section that cracks under its own prestrains or shrinkage has a
                        # kink in its forces: take the full step only if it brings the
                        # residual down, else as much of it as does
                        norm = float(np.max(np.abs(r)))
                        a = 1.0
                        for _ in range(12):
                            xt = x + a * dx
                            nt, mt, _ = an.forces(xt[0], xt[1])
                            if max(abs(nt - an.n0) / self.nscale,
                                   abs(mt - an.m0) / self.mscale) < norm:
                                break
                            a *= 0.5
                        x = x + a * dx
                    if not ok or not an.refine(x[0], x[1], 0.0):
                        break
                if ok:
                    break
            if not ok:
                raise SolveError("no equilibrium under the initial loads")
            e0, phi = float(x[0]), float(x[1])
        n, m, v = an.forces(e0, phi)
        det = an.detail(e0, phi, 0.0)
        # the control variable's value at the start: curvature, the strain at the centroid,
        # or, stepping in the shear strain, none yet
        c = {"phi": phi, "gam": 0.0}.get(self.mode, e0)
        return Stage(e0, phi, 0.0, 0.0, n, m, v, det, control=c)

    def _initial_guesses(self):
        """Where to start looking for the state under the constant loads: the unstrained
        section, and, for a section with strains of its own, the plane that fits them (the
        thesis, 7-3: with shrinkage the first estimate is "a linear fit to those profiles").
        A section cracked by a bar's thermal strain has no way from the unstrained state to
        its equilibrium that brings the residual down all the way; from the plane on which
        the bars carry nothing it has."""
        sec = self.sec
        yield np.zeros(2)
        fits = []
        if sec.shrink:
            z = np.linspace(sec.zbot, sec.ztop, 21)
            fits.append((z, sec.shrinkage(z), np.ones_like(z)))
        own = [l for l in sec.layers if l.prestrain != 0.0]
        if own:
            fits.append((np.array([l.z for l in own]), np.array([-l.prestrain for l in own]),
                         np.array([l.area for l in own])))
        for z, e, w in fits:
            if len(z) > 1 and np.ptp(z) > 1e-9:
                slope, at0 = np.polyfit(z - sec.zc, e, 1, w=np.sqrt(w))
            else:
                slope, at0 = 0.0, float(np.average(e, weights=w))
            # strain(z) = e0 - phi (z - zc)
            yield np.array([at0, -slope])

    # -- events ---------------------------------------------------------------------------------
    def _marks(self, st: Stage):
        d = st.detail
        cracked = bool(d.out.cracked.any())
        i = int(np.argmin(d.ex))
        crush = float(d.ex[i]) <= -self.sec.law_at(float(d.z[i])).e0
        # layers that have ruptured, or would at a crack in this state
        es, fs = self.an.steel(st.e0, st.phi)
        gone = 0
        for l, e, f in zip(self.sec.layers, es, fs):
            if math.isnan(f):
                gone += 1
            elif e > 0 and math.isnan(float(l.steel.crack_capacity(
                    e - l.prestrain, l.prestrain, l.rho, l.strand))):
                gone += 1
        return cracked, crush, gone

    def has_event(self, a: Stage, b: Stage) -> str:
        """What happens between two states: '' (nothing), 'crack', 'crush' or 'rupture'."""
        ca, ka, ga = self._marks(a)
        cb, kb, gb = self._marks(b)
        if cb and not ca:
            return "crack"
        if kb and not ka:
            return "crush"
        if gb > ga:
            return "rupture"
        return ""

    def accept(self, st: Stage):
        if self.stages:
            # Response starts to track unloading from the first stage after the initial one
            self.an.commit(st.e0, st.phi)
            if st.gam != 0.0:
                self.an.commit_stirrups(st.detail)
        self.stages.append(st)
        if self.on_stage:
            self.on_stage(len(self.stages))

    def advance(self, cur: Stage, target: float, depth: int) -> Stage:
        """Accept a stage at the target, approaching it in geometric steps when something
        happens on the way (first cracking, the extreme fibre reaching its peak strain)."""
        trial = self.solve(target, cur)
        kind = self.has_event(cur, trial)
        if kind == "rupture" and depth == 0:
            # steel ruptures within the step: take a fifth of it, or a twenty-fifth, if that
            # stops short of the rupture; otherwise the whole step, rupture included
            step = target - cur.control
            for frac in (0.2, 0.04):
                try:
                    sub = self.solve(cur.control + frac * step, cur)
                except SolveError:
                    continue
                if self.has_event(cur, sub) != "rupture":
                    self.accept(sub)
                    return sub
            self.accept(trial)
            return trial
        if depth < 2 and kind and kind != "rupture":
            for _ in range(14 if (depth == 0 or kind == "crack") else 3):
                t1 = cur.control + 0.2 * (target - cur.control)
                if kind == "crack" and abs(t1 - cur.control) < max(
                        0.004 * abs(cur.control), 0.0036 * self.step0):
                    break
                sub = self.advance(cur, t1, depth + 1)
                passed = self.has_event(cur, sub)
                cur = sub
                if passed:
                    break
            trial = self.solve(target, cur)
        self.accept(trial)
        return trial

    def run(self, max_stages=400) -> list[Stage]:
        st0 = self.initial()
        self.accept(st0)
        if self.mode == "none":
            self.accept(self.initial())
            return self.stages
        c0 = st0.control
        sgn = self.sign
        d0 = self.step0
        cur = st0
        try:
            cur = self.advance(cur, c0 + sgn * d0 / 6.0, 2)
            target = c0 + sgn * 7.0 * d0 / 6.0
            peak = 0.0
            spent = 0
            while len(self.stages) < max_stages:
                try:
                    cur = self.advance(cur, target, 0)
                except SolveError:
                    # try to get part of the way before giving up
                    done = False
                    t = target
                    cur = self.stages[-1]
                    for _ in range(3):
                        t = cur.control + 0.5 * (t - cur.control)
                        try:
                            cur = self.advance(cur, t, 2)
                            done = True
                            break
                        except SolveError:
                            continue
                    if not done and self.switch_control(self.stages[-1]):
                        # no state at a larger value of the control variable: carry on
                        # with another one
                        cur = self.stages[-1]
                        sgn, d0 = self.sign, self.step0
                        target = cur.control + sgn * max(d0, 0.1 * abs(cur.control))
                        continue
                    if not done:
                        break
                    target = cur.control
                lam = cur.lam
                peak = max(peak, lam)
                if peak > 0 and lam <= 0.01 * peak:
                    self.stages.pop()        # the load has run out: not a load stage
                    break
                if self.collapsed(cur, peak):
                    self.stages.pop()
                    break
                if self.crushed(cur):
                    break
                if self.spent(cur, peak):
                    spent += 1
                    if spent >= 2:
                        break
                # the next step is sized by the target just tried, from the stage reached
                target = cur.control + sgn * max(d0, 0.1 * abs(target))
        except SolveError:
            pass
        return self.stages[:max_stages]

    def collapsed(self, st: Stage, peak: float) -> bool:
        return False

    def switch_control(self, st: Stage) -> bool:
        """Change the control variable at the last stage found, if there is another to step
        in. True if it was changed."""
        return False

    def spent(self, st: Stage, peak: float) -> bool:
        """Steel has ruptured and less than a fifth of the peak load is left."""
        return bool(self.an.dead.any()) and peak > 0 and st.lam < 0.2 * peak

    def crushed(self, st: Stage) -> bool:
        """The response ends once the extreme fibre is strained to four times the strain at
        peak stress."""
        d = st.detail
        i = int(np.argmin(d.ex))
        return float(d.ex[i]) <= -4.0 * self.sec.law_at(float(d.z[i])).e0

    def more_detail(self, stages: list[Stage], peak: int, limit: int):
        """Response's More Detail: a new stage between every two up to the peak."""
        if peak < 1 or len(stages) >= limit:
            return stages, peak
        room = limit - len(stages)
        out = [stages[0]]
        added = 0
        saved = self.an.ep.copy()
        saved_y = self.an.epy.copy()
        self.an.ep[:] = self.an.ep0
        self.an.epy[:] = 0.0
        try:
            for i in range(1, len(stages)):
                a, b = stages[i - 1], stages[i]
                # not between stages found in another control variable
                same = (a.cmode or self.mode) == (b.cmode or self.mode) == self.mode
                if i <= peak and added < room and same:
                    try:
                        mid = self.solve(0.5 * (a.control + b.control), a)
                        out.append(mid)
                        added += 1
                    except SolveError:
                        pass
                out.append(stages[i])
        finally:
            self.an.ep[:] = saved
            self.an.epy[:] = saved_y
        newpeak = out.index(stages[peak])
        return out, newpeak
