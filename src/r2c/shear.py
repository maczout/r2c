"""Full response with shear: the longitudinal stiffness method for the shear stress profile
(thesis chapter 6) around the solution for the global strain state (chapter 7).

For a strain state the shear strain varies over the depth as gam0 times a profile of mean one.
The profile is not known in advance: it is whatever makes the shear stresses of the nodes
agree with the shear flow that longitudinal equilibrium requires. That shear flow comes from
the tangent stiffness of the nodes: a "virtual" change of the strain state that raises the
moment by V per unit length, at constant axial load and shear, gives the change of
longitudinal stress along the member at every depth, and integrating it from the top gives the
shear flow.
"""

from __future__ import annotations

import math

import numpy as np

from r2c import node as nodelib
from r2c.solver import Analysis, Flexure, SolveError, Stage, _root


class Shear(Flexure):

    def __init__(self, an: Analysis, on_stage=None):
        super().__init__(an, on_stage)
        sec = an.sec
        self.vscale = max(0.2 * math.sqrt(sec.conc0.fcp) * sec.area, 1.0)
        if an.dn != 0.0:
            self.mode = "e0"
            self.step0 = sec.conc0.e0 / 20.0
            self.sign = 1.0 if an.dn > 0 else -1.0
        elif an.dm != 0.0:
            self.mode = "phi"
            base = 0.08e-3 / sec.h
            if an.n0 != 0.0:
                base *= 0.5
            self.step0 = base
            self.sign = 1.0 if an.dm > 0 else -1.0
        else:
            self.mode = "gam"
            self.step0 = 0.024e-3
            self.sign = 1.0
        self.mode0 = self.mode
        # diagnostics only (tools/diagnose.py flow --fit-layer): a layer's tangent stiffness
        # in the shear flow, in place of its own
        self.bar_stiffness: dict[int, float] = {}
        # Response's acceptance of a stage [B 00418af0]: converged under 1 %; after 16 passes
        # kept unless above 3 % with the load above the largest so far
        self.profile_tol = 0.01
        self.profile_accept = 0.03
        self.passes = 16
        self.evals = 0
        self.budget = 600

    # -- tangent stiffness and the shear flow ---------------------------------------------------
    def bar_tangent(self, i, es):
        """Stiffness of longitudinal layer i in the shear flow calculation [B 004201e0]: the
        larger of the slope of its curve at the average strain and at the concentrated strain
        at a crack; nothing once it has ruptured."""
        l = self.sec.layers[i]
        if self.an.dead[i]:
            return 0.0
        st = l.steel
        ec = st.crack_strain(es - l.prestrain, l.prestrain, l.rho, l.strand)
        return float(max(st.tangent(es), st.tangent(ec))) * st.phi

    def zone(self, e0, phi, es, e2, zf, idx):
        """The depth range (zlo, zhi) outside which Response gives concrete and bars no
        stiffness in the shear flow calculation [B 00440ea0]. At a face cracked in flexure it
        ends at the outer edge of the outermost bar in the cracked zone that still has
        stiffness (the crack front if there is none); at a face compressed past the strain at
        peak stress, where that strain is reached."""
        an, sec = self.an, self.sec
        ztop, zbot = sec.ztop, sec.zbot
        kap = -phi                                  # strain = a + kap * z
        etop = float(an.strain(e0, phi, ztop))
        ebot = float(an.strain(e0, phi, zbot))
        live = [(l, self.bar_tangent(i, es[i])) for i, l in enumerate(sec.layers)]

        def front(target):
            # depth at which the longitudinal strain is `target`
            if abs(kap) * sec.h <= 1e-11:
                return None
            return sec.zc + (target - e0) / kap

        def law_at(z):
            for z1, z2, _b1, _b2, law in sec.segs:
                if z2 - 1e-9 <= z <= z1 + 1e-9:
                    return law
            return sec.conc0

        ltop, lbot = law_at(ztop), law_at(zbot)
        ecr_t = float(ltop.crack_strain(np.interp(ztop, sec.tz, an.t_ft)))
        ecr_b = float(lbot.crack_strain(np.interp(zbot, sec.tz, an.t_ft)))
        zhi = ztop
        if etop > ecr_t:
            zf_ = front(ecr_t)
            inz = [l.z + 0.5 * l.db for l, t in live
                   if t > 0 and (zf_ is None or (l.z > zf_ if kap > 0 else l.z < zf_))]
            zhi = max(inz) if inz else (zf_ if zf_ is not None else ztop)
        zlo = zbot
        if ebot > ecr_b:
            zf_ = front(ecr_b)
            inz = [l.z - 0.5 * l.db for l, t in live
                   if t > 0 and (zf_ is None or (l.z < zf_ if kap < 0 else l.z > zf_))]
            zlo = min(inz) if inz else (zf_ if zf_ is not None else zbot)
        if kap > 1e-8 / 1e3:
            zc_ = front(-lbot.e0)
            if zc_ is not None and zlo < zc_:
                zlo = zc_
        elif kap < -1e-8 / 1e3:
            zc_ = front(-ltop.e0)
            if zc_ is not None and zc_ < zhi:
                zhi = zc_
        if zhi - zlo == 0.0:
            zhi, zlo = zbot + 0.7 * sec.h, zbot + 0.3 * sec.h
        zhi = min(max(zhi, zbot), ztop)
        zlo = min(max(zlo, zbot), ztop)
        # concrete crushed inside the depth with both faces sound: nothing is left
        e0s = np.array([law.e0 for law in sec.laws])[idx]
        crushed = e2 < -e0s
        if not crushed[0] and not crushed[-1] and crushed.any():
            zlo, zhi = ztop, zbot
        return zlo, zhi

    # the slopes of the compressive stress in the node's stiffness: the program's analytic
    # ones [B 004ac960] in place of differences taken on the stress relation. With them
    # r2c's calculated shear stress in Response's states is Response's own
    # (tools/flowset.py). In use since step A-6 (owner 2026-11-24, D69; docs/kernel.md,
    # "The stiffness in the shear flow calculation")
    own_slopes = True

    def tangent(self, e0, phi, gam):
        """Per node: the condensed tangent stiffness (j, k, m, n) of thesis eq. 6-4, with the
        state it was taken at. The node's stiffness is Response's own [B 0046b940, 00427cd0]:
        analytic, in the principal directions, with the tension's stiffness set by what
        governs the tension at the node (docs/kernel.md)."""
        an, sec = self.an, self.sec
        z, b = an.layer_nodes()
        zf = z.ravel()
        es, fs = an.steel(e0, phi)
        f1cx = an.crack_check(e0, phi, es, fs)
        out, ex, g, smx, smt, ey = an.eval_nodes(e0, phi, gam, z, f1cx)
        m = sec.bond_m(zf)
        ft = np.interp(zf, sec.tz, an.t_ft)
        idx = an.law_index(zf, z)
        n_ = len(zf)

        th = out.theta
        co, si = np.cos(th), np.sin(th)
        s2, c2, sc = si * si, co * co, si * co
        cs = c2 - s2
        with np.errstate(divide="ignore", invalid="ignore"):
            t = si / co
        t = np.where(np.abs(t) > 1e6, np.sign(t) * 1e6, t)
        t = np.where(t == 0.0, 1e-6, t)
        t = np.where(np.abs(t) < 1e-6, np.sign(t) * 1e-6, t)
        t2 = t * t
        e1, e2 = out.e1, out.e2
        rad = np.maximum(np.sqrt(g * g + (ex - ey) ** 2), 1e-6)

        # the principal stresses' own slopes: tension along 1; compression along 2 and its
        # softening by the strain along 1
        d = 1e-8
        et1 = np.empty(n_)
        a2 = np.empty(n_)
        b2 = np.empty(n_)
        phic = np.empty(n_)
        dvci = np.zeros(n_)
        for j, law in enumerate(sec.laws):
            k = idx == j
            if not k.any():
                continue
            f = lambda p, q: law.stress(p, q, ft[k], m[k])[0]
            # (up to the cracking strain the slope is the concrete's stiffness: no difference
            # taken across the cracking strain)
            et1[k] = np.where(e1[k] <= law.crack_strain(ft[k]), law.Ec * law.phi,
                              (f(e1[k] + d, e2[k]) - f(e1[k], e2[k])) / d)
            a2[k] = (f(e2[k] + d, e1[k]) - f(e2[k] - d, e1[k])) / (2 * d)
            b2[k] = (f(e2[k], e1[k] + d) - f(e2[k], e1[k])) / d
            if self.own_slopes:
                # in compression the program's own two slopes, not the stress relation's
                cmp_ = e2[k] < -1e-9
                if cmp_.any():
                    sa, sb = law.compression_slopes(e2[k][cmp_], e1[k][cmp_])
                    ka = np.flatnonzero(k)[cmp_]
                    a2[ka], b2[ka] = sa, sb
            phic[k] = law.phi
            # slope of the limit of the shear on the crack against the principal strain
            aa = 24.0 * out.w[k] / (law.agg + 16.0)
            dvci[k] = -0.18 * math.sqrt(law.fcp) * (24.0 * out.sdiag[k] / (law.agg + 16.0)) \
                / (aa + 0.3) ** 2 * law.phi
        vci = out.vcimax
        gov = np.where(out.cracked, out.gov, nodelib.GOV_AVG)
        ok_s, ok_c, ok_t = s2 > 1e-6, c2 > 1e-6, np.abs(t) > 1e-6
        ok_sc = np.abs(sc) > 1e-6
        BIGE = 1.0      # 1e6 Pa
        with np.errstate(divide="ignore", invalid="ignore"):
            # limit 3: f1 = cx + vci,max / tan
            x3 = np.where(ok_s & ok_t, dvci / t - vci / s2 * sc / rad / s2, BIGE)
            y3 = np.where(ok_s & ok_c, vci / s2 * sc / rad / c2 + dvci / t, 0.0)
            g3 = np.where(ok_t & ok_sc, dvci / t - vci / s2 / sc * cs / (2 * rad), 0.0)
            # limit 4: f1 = cy + vci,max * tan
            y4 = np.where(ok_c, dvci * t - vci / c2 * sc / rad / c2, BIGE)
            x4 = np.where(ok_s, vci * t / s2 / rad + dvci * t, BIGE)
            g4 = np.where(ok_sc, vci / c2 / sc * cs / (2 * rad) + dvci * t, BIGE)
        is0, is3, is4 = gov == nodelib.GOV_AVG, gov == nodelib.GOV_VCI_X, gov == nodelib.GOV_VCI_Y
        e1x = np.where(is0, et1, np.where(is3, x3, np.where(is4, x4, 0.0)))
        e1y = np.where(is0, et1, np.where(is3, y3, np.where(is4, y4, 0.0)))
        e1g = np.where(is0, et1, np.where(is3, g3, np.where(is4, g4, 0.0)))
        # compression: softening counts with the strain along 1 the column brings; not for
        # the shear strain's column
        e2x = a2 + t2 * b2
        e2y = a2 + b2 / t2
        e2g = a2
        de = e1 - e2
        with np.errstate(divide="ignore", invalid="ignore"):
            gs = np.where(np.abs(de) > 1e-15, 0.5 * (out.f1 - out.f2) / de,
                          e2x * e1x / (e2x + e1x + 1e-6))
        p_, q_ = e1x * s2, e2x * c2
        hh = 4.0 * gs * c2 * s2
        u = 2.0 * gs * sc * cs
        A = p_ * s2 + q_ * c2 + hh
        B = e2y * c2 * s2 + e1y * s2 * c2 - hh
        C = -(e2g * c2 * sc - e1g * s2 * sc - u)
        D = p_ * c2 + q_ * s2 - hh
        E = e1y * c2 * c2 + e2y * s2 * s2 + hh
        F = -(e2g * s2 * sc - e1g * c2 * sc + u)
        G = -(q_ * sc - p_ * sc - u)
        H = -(e2y * s2 * sc - e1y * c2 * sc + u)
        I = e1g * c2 * s2 + e2g * c2 * s2 + gs * cs * cs
        tiny = 1e-12    # 1e-6 Pa
        A = np.where(np.abs(A) < tiny, 1e-6, A)
        E = np.where(np.abs(E) < tiny, 1e-6, E)
        I = np.where(np.abs(I) < tiny, 1e-6, I)

        # the stirrups' part of the transverse stiffness: the slope of their curve
        ks = np.zeros(n_)
        a_n = np.zeros(n_)
        a_s = np.zeros(n_)
        for st, rho, fac in an.stirrups_at(zf, an.node_width(z)):
            if not rho.any():
                continue
            ks += rho * fac * st.steel.tangent(ey * fac + st.prestrain) * st.steel.phi
            a_n += np.where(rho > 0, st.area / sec.n_trans, 0.0)
            a_s += np.where(rho > 0, st.area / (st.space + 1e-4), 0.0)
        eff = np.clip(0.5 * (3.0 - a_n / (a_s + 1e-9) / sec.h), 0.0, 1.0)
        Et = E + eff * ks
        with np.errstate(divide="ignore", invalid="ignore"):
            inv = np.where(Et != 0.0, 1.0 / Et, 0.0)
        jj = A - D * B * inv
        kk = C - F * B * inv
        mm = G - H * D * inv
        nn = I - H * F * inv

        zlo, zhi = self.zone(e0, phi, es, e2, zf, idx)
        e0s = np.array([law.e0 for law in sec.laws])[idx]
        off = (zf > zhi + 1e-9) | (zf < zlo - 1e-9) | (e2 < -e0s)
        jj, kk, mm, nn = (np.where(off, 0.0, q) for q in (jj, kk, mm, nn))
        shp = z.shape
        return dict(z=z, b=b, out=out, ex=ex, g=g, ey=ey, es=es, fs=fs, j=jj.reshape(shp),
                    k=kk.reshape(shp), m=mm.reshape(shp), n=nn.reshape(shp), zone=(zlo, zhi))

    def _stiffness(self, t, s):
        """The section's 3 x 3 tangent stiffness from the nodes' condensed stiffnesses t
        (rows N, M, V; columns the strain at the axis, the curvature, the shear strain
        parameter), with s the shear strain profile at the nodes [B 00427cd0], and the bars
        as (height, stiffness less the concrete displaced, lever arm, diameter, layer)."""
        sec = self.sec
        z, b = t["z"], t["b"]
        y = z - sec.zaxial
        dz = (z[:, 0] - z[:, 2])[:, None]
        w = np.array([1.0, 4.0, 1.0]) / 6.0

        def integ(f):
            return float(np.sum((f @ w) * dz[:, 0]))
        jb, kb, mb, nb = t["j"] * b, t["k"] * b, t["m"] * b, t["n"] * b
        jm = np.zeros((3, 3))
        jm[0] = [integ(jb), -integ(jb * y), integ(kb * s)]
        jm[1] = [-integ(jb * y), integ(jb * y * y), -integ(kb * s * y)]
        jm[2] = [integ(mb), -integ(mb * y), integ(nb * s)]
        # the bars: tangent stiffness of each layer, less the concrete it displaces
        bars = []
        for i, l in enumerate(sec.layers):
            if math.isnan(t["fs"][i]):
                continue
            zlo, zhi = t["zone"]
            et = 0.0 if (l.z < zlo or l.z > zhi) else self.bar_tangent(i, t["es"][i])
            et = self.bar_stiffness.get(i, et)
            jz = float(np.interp(l.z, z.ravel()[::-1], t["j"].ravel()[::-1]))
            ea = (et - jz) * l.area
            yb = l.z - sec.zaxial
            jm[0, 0] += ea
            jm[0, 1] -= ea * yb
            jm[1, 0] -= ea * yb
            jm[1, 1] += ea * yb * yb
            bars.append((l.z, ea, yb, l.db, i))
        return jm, bars

    def shear_flow(self, e0, phi, gam, v_total):
        """The shear stress profile longitudinal equilibrium requires: (z nodes from the top
        down, stress from the state, stress calculated, tangent shear stiffness, state)."""
        an, sec = self.an, self.sec
        t = self.tangent(e0, phi, gam)
        z, b = t["z"], t["b"]
        y = z - sec.zaxial
        s = np.interp(an.profile_z(z), an.shape_z, an.shape)
        dz = (z[:, 0] - z[:, 2])[:, None]
        w = np.array([1.0, 4.0, 1.0]) / 6.0

        def integ(f):
            return float(np.sum((f @ w) * dz[:, 0]))
        jm, bars = self._stiffness(t, s)
        rhs = np.array([0.0, v_total, 0.0])
        try:
            if abs(jm[2, 2]) < 1e-9:
                raise np.linalg.LinAlgError
            dv = np.linalg.solve(jm, rhs)
        except np.linalg.LinAlgError:
            # no shear stiffness yet (no shear strain): the flexural part alone
            try:
                d2 = np.linalg.solve(jm[:2, :2], rhs[:2])
            except np.linalg.LinAlgError:
                raise SolveError("the section has no stiffness left against moment") from None
            dv = np.array([d2[0], d2[1], 0.0])
        de0, dphi, dgam = dv
        dq = (t["j"] * (de0 - dphi * y) + t["k"] * s * dgam) * b      # per unit depth
        # integrate from the top: within each layer by the parabola through its three nodes
        full = (dq @ w) * dz[:, 0]
        half = dz[:, 0] / 24.0 * (5.0 * dq[:, 0] + 8.0 * dq[:, 1] - dq[:, 2])
        above = np.concatenate([[0.0], np.cumsum(full)[:-1]])
        q = np.stack([above, above + half, above + full], axis=1)
        t["bars"] = bars
        for zb, ea, yb, db, _i in bars:
            # a bar hands its force to the concrete over its own depth
            frac = np.clip((zb + db / 2.0 - z) / db, 0.0, 1.0)
            q += frac * ea * (de0 - dphi * yb)
        q = -q
        tau = q / np.maximum(b, 1e-9)
        tau[0, 0] = 0.0
        tau[-1, 2] = 0.0
        return z, t["out"].v.reshape(z.shape), tau, t, (de0, dphi, dgam)

    def update_profile(self, z, vstate, tau, t, gam, relax=1.0):
        """The shear strain profile for the next pass, as Response-2000 updates it
        [B 0041e840; in use since step A-2, owner 2026-11-23, D49]. At every node: the profile's value times the mean of one and
        (calculated stress over the state's stress), that factor within ten either way and
        the value within a hundred; unchanged where the node carries no shear or the
        section has no shear strain yet. Nothing at the two faces. Then divided by its mean
        over the depth (Simpson's rule over each layer's three nodes, no width in it; the
        divisor kept between 0.1 and 10), and no value above eight times the gross area
        over the concrete area within the depth that has stiffness."""
        an, sec = self.an, self.sec
        zp = an.profile_z(z)
        old = np.interp(zp, an.shape_z, an.shape)
        carries = np.abs(vstate) > 1e-14
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(carries, 0.5 * (tau + vstate) / np.where(carries, vstate, 1.0), 1.0)
        ratio = np.clip(ratio, -10.0, 10.0)
        new = np.clip(ratio * old, -100.0, 100.0)
        if abs(gam) < 1e-8:
            new = old.copy()
        new = np.where(carries, new, old + 1e-6)
        new[0, 0] = 0.0
        new[-1, 2] = 0.0
        dzl = z[:, 0] - z[:, 2]
        mean = float(np.sum(dzl * (new[:, 0] + 4.0 * new[:, 1] + new[:, 2]) / 6.0)) / sec.h
        if not math.isfinite(mean):
            return
        if mean == 0.0:
            an.shape_z = an.shape_z0.copy()
            an.shape = an._elastic_shape()
            return
        div = min(max(mean, 0.1), 10.0)
        zlo, zhi = t["zone"]
        inside = sec.area_between(min(zlo, zhi), max(zlo, zhi)) if zhi > zlo else 0.0
        cap = 8.0 * sec.area / max(inside, 1e-2)        # 1e-8 m2 at the least, in mm2
        new = np.minimum(new / div, cap)
        zf = zp.ravel()[::-1]
        zz, ii = np.unique(zf, return_index=True)
        grid = np.unique(np.concatenate([an.shape_z0, zz]))
        prof = np.interp(grid, zz, new.ravel()[::-1][ii])
        if relax != 1.0:
            prof = (1.0 - relax) * np.interp(grid, an.shape_z, an.shape) + relax * prof
        an.shape_z, an.shape = grid, prof

    def profile_error(self, z, vstate, tau, v) -> float:
        """Response's measure of how far the shear strain profile is from converged
        [B 00420f20]: the standard deviation, over 50 points of the depth, of the calculated
        shear stress less the state's, over the mean calculated shear stress. 0.9 % (which
        counts as converged) where the shear is negligible."""
        if abs(v) < 1e-3 * self.vscale:
            return 0.009
        sec = self.sec
        zf = self.an.profile_z(z).ravel()[::-1]
        zz, ii = np.unique(zf, return_index=True)
        calc = np.interp(np.linspace(sec.zbot, sec.ztop, 50), zz, tau.ravel()[::-1][ii])
        state = np.interp(np.linspace(sec.zbot, sec.ztop, 50), zz, vstate.ravel()[::-1][ii])
        d = calc - state
        mean = float(np.mean(calc))
        sd = math.sqrt(max(float(np.sum(d * d) * 50.0 - np.sum(d) ** 2) / 50.0 / 49.0, 0.0))
        return abs(sd / mean) if abs(mean) > 1e-12 else sd

    # -- one state ------------------------------------------------------------------------------
    def _residual(self, c, x):
        an = self.an
        if self.mode == "phi":
            e0, gam, phi = x[0], x[1], c
        elif self.mode == "e0":
            phi, gam, e0 = x[0], x[1], c
        else:
            e0, phi, gam = x[0], x[1], c
        self.evals += 1
        if self.evals > self.budget:
            raise SolveError("no equilibrium found within the iteration limit")
        n, m, v = an.forces(e0, phi, gam)
        rn = lambda lam: (n - an.n0 - lam * an.dn) / self.nscale
        rm = lambda lam: (m - an.m0 - lam * an.dm) / self.mscale
        rv = lambda lam: (v - an.v0 - lam * an.dv) / self.vscale
        # the load factor comes from one load that is being increased (by preference the one
        # that goes with the control variable), the other two are the equations
        order = {"phi": "mvn", "e0": "nvm", "gam": "vmn"}[self.mode]
        which = next(k for k in order if {"n": an.dn, "m": an.dm, "v": an.dv}[k] != 0.0)
        if which == "m":
            lam = (m - an.m0) / an.dm
            r = np.array([rn(lam), rv(lam)])
        elif which == "n":
            lam = (n - an.n0) / an.dn
            r = np.array([rm(lam), rv(lam)])
        else:
            lam = (v - an.v0) / an.dv
            r = np.array([rn(lam), rm(lam)])
        return r, (e0, phi, gam, lam, n, m, v)

    def _newton(self, c, x0):
        h = self.sec.h
        sc = {"phi": np.array([1e-6, 1e-6]), "e0": np.array([1e-6 / h, 1e-6]),
              "gam": np.array([1e-6, 1e-6 / h])}[self.mode]
        x = np.array(x0, dtype=float)
        r, info = self._residual(c, x)
        best = (float(np.max(np.abs(r))), x.copy(), info)
        for it in range(40):
            nr = float(np.max(np.abs(r)))
            if nr < 2e-7:
                self.unbalance = nr
                return x, info, True
            jac = np.empty((2, 2))
            for j in range(2):
                xx = x.copy()
                h = sc[j] * 0.05
                xx[j] += h
                r2, _ = self._residual(c, xx)
                jac[:, j] = (r2 - r) / h
            try:
                dx = np.linalg.solve(jac, -r)
            except np.linalg.LinAlgError:
                break
            step = 1.0
            ok = False
            for _ in range(8):
                xn = x + step * dx
                rn, infon = self._residual(c, xn)
                if np.all(np.isfinite(rn)) and float(np.max(np.abs(rn))) < nr * (1 - 0.1 * step):
                    ok = True
                    break
                step *= 0.5
            if not ok:
                break
            x, r, info = xn, rn, infon
            nr = float(np.max(np.abs(r)))
            if nr < best[0]:
                best = (nr, x.copy(), info)
        nr = float(np.max(np.abs(r)))
        if nr < best[0]:
            best = (nr, x.copy(), info)
        self.unbalance = best[0]
        return best[1], best[2], best[0] < 2e-5

    def _general(self, c, x0):
        """Response-2000's solve of the global strains at control value c [B 004276a0, its
        step 004267c0]: the load factor is read off the load that goes with the control
        variable, and the other strains are stepped by the section's own stiffness on what
        the other two loads are out of balance by, whole steps and no search along them. It
        stops once the unbalanced loads are inside its tolerance (at least one step is
        taken), and gives up after 50 steps, when the stiffness cannot be solved or when a
        step is larger than 0.5 in all (strains, and curvature per metre). The layers are
        split anew at each evaluation. Returns (x, info, found) as _newton does."""
        an, sec = self.an, self.sec
        ci = {"e0": 0, "phi": 1, "gam": 2}[self.mode]
        if self.mode == "phi":
            e = np.array([x0[0], c, x0[1]], dtype=float)
        elif self.mode == "e0":
            e = np.array([c, x0[0], x0[1]], dtype=float)
        else:
            e = np.array([x0[0], x0[1], c], dtype=float)
        inc = np.array([an.dn, an.dm, an.dv])
        con = np.array([an.n0, an.m0, an.v0])
        kl = ci
        if abs(inc[ci]) < 1e-3:
            kl = {"e0": 0, "phi": 1, "gam": 2}[self.mode0 if inc[
                {"e0": 0, "phi": 1, "gam": 2}[self.mode0]] != 0.0 else
                next(k for k, d in zip(("e0", "phi", "gam"), inc) if d != 0.0)]
        hm = sec.h / 1e3
        hh = (hm + 1e-4) ** 2
        floor = 1.0 + (1000.0 * sec.area / 1e6) ** 2
        si = np.array([1.0, 1e-3, 1.0])            # N, N mm, N to N, N m, N
        count = 0
        found = False

        def state():
            an.refine(e[0], e[1], e[2])
            self.evals += 1
            f = np.array(an.forces(e[0], e[1], e[2]))
            lam = (f[kl] - con[kl]) / inc[kl]
            return f, lam, (con + lam * inc - f)

        while True:
            f, lam, rhs = state()
            if not np.all(np.isfinite(f)):
                self.why = "forces not finite"
                break
            err = float(np.sum((rhs * si) ** 2)) / hh
            tol = (f[0] ** 2 + f[2] ** 2 + (f[1] / 1e3) ** 2 / hh) * 1e-6 + floor
            if err < tol and count:
                found = True
                break
            t = self.tangent(e[0], e[1], e[2])
            k, _bars = self._stiffness(t, np.interp(an.profile_z(t["z"]), an.shape_z, an.shape))
            # which strains have a stiffness to step on, against that of the control
            d = np.abs(np.array([k[0, 0], k[1, 1] / 1e6 / (hm * hm), k[2, 2]]))
            ref = d[ci] / 1e4
            on = d > ref
            on &= (d >= 1.0) | (np.arange(3) == ci)
            on[ci] = on[ci] or not on.any()
            k[ci, ci] *= 1e9                        # the control variable stays where it is
            step = np.zeros(3)
            idx = np.flatnonzero(on)
            try:
                step[idx] = np.linalg.solve(k[np.ix_(idx, idx)], rhs[idx])
            except np.linalg.LinAlgError:
                self.why = "singular stiffness"
                break
            if not np.all(np.isfinite(step)) or \
                    abs(step[0]) + abs(step[1] * 1e3) + abs(step[2]) > 0.5:
                self.why = "step too large"
                break
            e += self.step_share * step
            count += 1
            if self.debug:
                print(f"     step {count}: e0={e[0]*1e3:.4f} phi={e[1]*1e6:.4f} gam={e[2]*1e3:.4f} share={self.step_share}")
            if count > 10 and hm < 5.0:
                self.step_share = 0.5       # half steps from the eleventh on [B 004276a0]
            if count > 50:
                self.why = f"50 steps, out of balance by {math.sqrt(err / tol):.3g} of the tolerance"
                break
            if not tol < err:
                found = True
                break
        if found and count:
            f, lam, rhs = state()
        if self.mode != "gam" and not self.half_steps:
            self.step_share = 1.0           # whole steps again for the next solve
        self.unbalance = float(np.max(np.abs(rhs * si))) if np.all(np.isfinite(rhs)) else math.inf
        info = (float(e[0]), float(e[1]), float(e[2]), float(lam), float(f[0]), float(f[1]),
                float(f[2]))
        x = {"phi": [e[0], e[2]], "e0": [e[1], e[2]], "gam": [e[0], e[1]]}[self.mode]
        return np.array(x), info, found

    trace = None             # tools/trace.py: a list to which each try is added
    debug = False            # tools/trace.py --set debug=1: print each pass of a stage
    why = ""                 # why the program's solve gave up, for tools/trace.py
    # Response's own solve of the global strains [B 004276a0]: written and off
    # (docs/kernel.md, "The global solve with shear")
    own_solve = False
    step_share = 1.0         # the share of a step of that solve that is taken
    half_steps = False       # Response's flag that keeps that share at one half

    def _nested(self, c, x0):
        """Fallback for the Newton iteration: the two unknowns one inside the other, each by
        the bracketing search of the flexural solution."""
        state = {"inner": float(x0[0]), "info": None}

        def outer(x1):
            def inner(e0):
                r, info = self._residual(c, np.array([e0, x1]))
                state["info"] = info
                state["r"] = r
                return float(r[0])
            e0, ok = _root(inner, state["inner"],
                           1e-6 / self.sec.h if self.mode == "e0" else 1e-6, 1e-7)
            if ok:
                state["inner"] = e0
            r, info = self._residual(c, np.array([state["inner"], x1]))
            state["info"] = info
            state["r"] = r
            return float(r[1])
        dx = 2e-6 / self.sec.h if self.mode == "gam" else 2e-6
        x1, ok = _root(outer, float(x0[1]), dx, 1e-6)
        r1 = outer(x1)
        r = state["r"]
        good = ok and abs(float(r[0])) < 1e-4 and abs(r1) < 1e-3
        return np.array([state["inner"], x1]), state["info"], good

    def solve(self, c, prev: Stage | None, ctx=None) -> Stage:
        """The state at control value c: curvature, or the shear strain when there is no
        moment increment. prev: the stage whose strains are the first estimate. ctx: what
        the stage control knows when it asks (the step multiplier, the largest load so far,
        the load of the stage before), for the tests Response makes on every pass."""
        an = self.an
        keep = an.profile()
        try:
            return self._solve(c, prev, ctx)
        except SolveError:
            an.set_profile(keep)
            raise

    # Response's tests on every pass of a stage [B 00418af0]: written, off until verified
    pass_code = False
    # r2c's own: a solve of the global strains that has not closed is carried on from when
    # it is nearly balanced. Not the program's with shear (docs/kernel.md); on until
    # taking it out has been weighed
    soft_solve = True
    # when the base step grows to a tenth of the target: at every pass, as the program
    # does it [B 00418860], and not once before a stage's first try (docs/kernel.md,
    # "When the base step grows")
    late_growth = True

    def _solve(self, c, prev: Stage | None, ctx=None) -> Stage:
        """One load stage as Response works on it [B 00418af0]: up to 16 passes of solving the
        global strains with the shear strain profile as it is, then updating the profile from
        the calculated shear stress. The stage comes back converged (profile error under
        1 %) or as the last pass left it, with its error in `perr`; whether it is kept is the
        caller's decision. SolveError only where the global strains cannot be solved."""
        an = self.an
        if prev is None:
            x = [0.0, 0.0]
        elif self.mode == "phi":
            x = [prev.e0, prev.gam]
        elif self.mode == "e0":
            x = [prev.phi, prev.gam]
        else:
            x = [prev.e0, prev.phi]
        an.coarsen()
        saved_shape = an.profile()
        self.evals = 0
        self.tried = 0          # passes begun on this try, for the stage control
        info = None
        ok = False
        err = 1.0
        passes = refines = 0
        used = saved_shape
        codes = []
        failed = None
        while passes < self.passes:
            x0 = np.array(x, dtype=float)
            soft = False
            self.tried = passes + 1
            if self.own_solve:
                x, info, ok = self._general(c, x0)
                if not ok:
                    break
            else:
                x, info, ok = self._newton(c, x0)
            if not ok:
                near = (x, info, self.unbalance)
                x, info, ok = self._nested(c, x0)
                if not ok:
                    # Response carries on from a global solution that has not closed
                    # [B 00418af0, the solve's status -2]: here, the nearest state found,
                    # if it is out of balance by less than 2 % of the section's scale
                    x, info, res = near
                    if not self.soft_solve or info is None \
                            or not all(math.isfinite(q) for q in info) or res > 0.02:
                        ok = False
                        break
                    ok = soft = True
            e0, phi, gam, lam, n, m, v = info
            if not self.own_solve and refines < 3 and an.refine(e0, phi, gam):
                refines += 1
                continue
            z, vstate, tau, t, _d = self.shear_flow(e0, phi, gam, v)
            used = an.profile()
            self.update_profile(z, vstate, tau, t, gam, relax=self.relax(passes))
            err = self.profile_error(z, vstate, tau, v)
            passes += 1
            if err > 10.0 and passes > 3:
                # far off after three passes: the profile of the uncracked section again
                # [B 00418af0, 004357d0]
                an.shape_z = an.shape_z0.copy()
                an.shape = an._elastic_shape()
                self.half_steps, self.step_share = True, 0.5
            if getattr(self, "debug", False):
                print(f"   pass {passes}: lam={lam:.4f} profile err={err:.4f}")
            if self.pass_code and ctx is not None:
                # the state code of this pass's state, acted on at once [B 00418af0]
                code = self.state_code(Stage(e0, phi, gam, lam, n, m, v,
                                             an.detail(e0, phi, gam), control=c,
                                             cmode=self.mode))
                codes.append(code)
                if code != 0 and ctx["mult"] >= 0.5:
                    failed = f"state code {code} in pass {passes}"
                    break
                if code == 3 and lam > ctx["peak"]:
                    failed = f"state code 3 above the largest load in pass {passes}"
                    break
                if code != 0 and ctx["last"] is not None and lam < ctx["last"]:
                    break               # taken as it is: the load is under the stage before
            if soft:
                if err <= 0.05:
                    break               # kept as it is
                continue
            if err < self.profile_tol:
                break
        if ok and soft:
            err = max(err, self.profile_tol)
        if not ok or info is None:
            an.set_profile(saved_shape)
            raise SolveError(f"no equilibrium at control value {c:g}")
        left = an.profile()
        # the state is the last pass's, with the profile it was solved on
        an.set_profile(used)
        e0, phi, gam, lam, n, m, v = info
        if not all(math.isfinite(q) for q in info) or abs(gam) > 0.2 or abs(e0) > 0.2:
            an.set_profile(saved_shape)
            raise SolveError(f"no equilibrium at control value {c:g}")
        det = an.detail(e0, phi, gam)
        # the calculated profile at the detail's nodes
        z, vstate, tau, t, d = self.shear_flow(e0, phi, gam, v)
        zf = z.ravel()[::-1]
        zz, ii = np.unique(zf, return_index=True)
        det.vcalc = np.interp(det.z, zz, tau.ravel()[::-1][ii])
        # average bond: the change of bar force along the member over the bar surface
        de0, dphi, _dg = d
        bond = np.zeros(len(self.sec.layers))
        for i, l in enumerate(self.sec.layers):
            hit = [b for b in t["bars"] if b[4] == i]
            if hit:
                _zb, ea, yb, db, _i = hit[0]
                bond[i] = abs(ea * (de0 - dphi * yb)) / (l.num * math.pi * max(db, 1e-9))
        det.bond = bond
        st = Stage(e0, phi, gam, lam, n, m, v, det, control=c, cmode=self.mode)
        # the shear strain Response reports: weighted by the shear force over the depth
        num = np.trapezoid(det.out.v * det.gxy * det.b, det.z)
        den = np.trapezoid(det.out.v * det.b, det.z)
        st.gam_avg = float(num / den) if abs(den) > 1e-9 else 0.0
        st.perr = err
        st.passes = passes
        st.codes = codes
        st.failed = failed
        st.profile = an.profile()        # the profile the stage leaves for the next one
        # the stage keeps the profile of its own state, which is what is put back when
        # a later stage fails or is put in between [B 0041c060]; the next stage starts
        # from the last update, converged or not [B 00418af0]
        an.set_profile(left)
        return st

    def more_detail(self, stages, peak, limit):
        # between stages found in the first control variable
        mode, self.mode = self.mode, self.mode0
        try:
            return super().more_detail(stages, peak, limit)
        finally:
            self.mode = mode

    def relax(self, passes: int) -> float:
        """The share of the updated profile taken: all of it (the update is Response's, which
        is damped in itself). Under shear alone, half of it in the second half of the passes
        [O, r2c's own: without it the stage past the peak does not settle, where Response's
        does; with it everywhere, r2c settles where Response's stages stand still]."""
        if self.mode0 == "gam" and passes >= self.passes // 2:
            return 0.5
        return 1.0

    # -- Response's load stage control [B; docs/kernel.md "Response's own load stage control"] ---
    def control_of(self, st: Stage, mode: str | None = None) -> float:
        return {"phi": st.phi, "e0": st.e0, "gam": st.gam}[mode or self.mode]

    def _weights(self):
        """a, b, c of Response's choice of control variable: |dN|, 3|dM|/h, |dV|."""
        an = self.an
        return abs(an.dn), 3.0 * abs(an.dm) / self.sec.h, abs(an.dv)

    def first_control(self) -> str:
        """The curvature where the moment dominates, else the axial strain [B 00422de0];
        the shear strain for shear alone [O: Response's stages under shear alone are evenly
        spaced in the shear strain while the axial strain stays at nothing]."""
        a, b, c = self._weights()
        if a == 0.0 and b == 0.0:
            return "gam"
        return "phi" if (a <= b and c <= b) else "e0"

    def other_control(self) -> str:
        """The control variable Response changes to when the present one stalls."""
        a, b, c = self._weights()
        if c < b or c < a:
            if a <= b and c <= b:
                return "gam"                  # the moment dominates and there is shear
            return "gam" if b < c else "phi"
        return "e0" if (b < a or b <= 0.0) else "phi"

    def base_step(self, mode: str) -> float:
        """Response's base step of a control variable, signed towards loading [B 00419250]."""
        an, sec = self.an, self.sec
        sgn = lambda v: 1.0 if v > 0 else -1.0 if v < 0 else 0.0
        if mode == "phi":
            d = 0.004 / sec.h / 50.0          # rad/mm (0.004/h/50 with h in metres, per metre)
            if abs(an.dv) * 0.5 < abs(an.dn) and abs(an.dv) > 1e-3:
                d *= 0.5
            if abs(an.n0) > 0.1 * sec.area:   # a constant axial load above 0.1 MPa on the area
                d *= 0.5
            if abs(an.dv) > 1e-3 and abs(an.dm / an.dv) < sec.h:
                d *= 0.5
            return d * (sgn(an.dm) or 1.0)
        if mode == "e0":
            d = abs(sec.conc0.e0) / 20.0
            return d * (sgn(an.dn) or 1.0)
        # the shear strain: finer where the member has at least minimum stirrups
        deep = any(st.top - st.bot > 0.5 * sec.h for st in sec.stirrups)
        strong = False
        if sec.stirrups:
            bw = float(np.min(sec.width(np.linspace(sec.zbot, sec.ztop, 41)[1:-1])))
            strength = sum(st.area / (bw * st.space) * st.steel.fy for st in sec.stirrups)
            strong = strength >= 0.08 * math.sqrt(sec.conc0.fcp)
        d = 2e-5 if (deep and strong) or (an.dn == 0.0 and an.dm == 0.0) else 5e-5
        if an.dn == 0.0 and an.dm == 0.0 and an.n0 < 0.0:
            d *= 0.5      # [O] shear alone under a constant compression: half the step
        return d * (sgn(an.dv) or 1.0)

    def state_code(self, st: Stage) -> int:
        """Response's code for what has gone wrong in a state [B 004204b0]: 1 a crack
        slipping where there are no stirrups, 4 a stirrup past rupture, 3 the web crushing,
        2 an extreme fibre far past its peak strain; 0 nothing."""
        d, sec = st.detail, self.sec
        o = d.out
        # the shear on the crack at its limit (what then governs the tension at the node,
        # docs/kernel.md "The node") where no stirrup crosses
        slip = (o.gov == nodelib.GOV_VCI_X) | (o.gov == nodelib.GOV_VCI_Y)
        if d.rhov is not None:
            slip = slip & (np.asarray(d.rhov) <= 0.0)
        if slip.any():
            return 1
        if sec.stirrups:
            lim = max(0.01, max(s.steel.rupture for s in sec.stirrups))
            if float(np.max(d.ey)) > lim:
                return 4
        e0s = np.array([sec.law_at(float(z)).e0 for z in d.z])
        crush = (np.abs(o.f2 - o.f2max) < 0.015 * np.abs(o.f2max)) | (o.e2 < -e0s)
        shear = np.abs(o.v) > 0.0
        n = len(crush)
        if crush[0] or crush[-1]:
            # the crushing zone that starts at that face is flexure's; beyond it, any
            # crushing node that carries shear is the web's
            order = range(n) if crush[0] else range(n - 1, -1, -1)
            zone = True
            for i in order:
                if zone and not crush[i]:
                    zone = False
                elif not zone and crush[i] and shear[i]:
                    return 3
            if zone and st.v > 0.0:
                return 3
        elif (crush & shear).any():
            return 3
        far = min(-0.01, -5.0 * float(np.max(e0s)))
        if o.e2[0] >= far and o.e2[-1] >= far:
            return 3 if bool(np.all(o.e2 <= -e0s)) else 0
        return 2

    def _cracked(self, st: Stage) -> bool:
        """Is the stage cracked, for the events between stages? Response's test [B 004181d0,
        004ff4e0] is the principal tensile strain above the cracking strain at any node,
        with the cracking strain as it is before the node lowers it for the compression
        across it [B 0046a960]: a node that has cracked under compression, below that
        strain, does not make the stage a cracked one."""
        o = st.detail.out
        return bool(np.any(o.e1 > o.ecr))

    def _event(self, a: Stage, b: Stage) -> int:
        """What sets stage b apart from the one before [B 00415e30]: 1 newly cracked, 2
        cracked before and not now, 3 newly crushing, 5 a crack slipping, 4 a change in what
        has ruptured; 0 nothing."""
        ca, cb = self._cracked(a), self._cracked(b)
        if cb and not ca:
            return 1
        if ca and not cb:
            return 2

        def crushing(st):
            e0s = np.array([self.sec.law_at(float(z)).e0 for z in st.detail.z])
            return bool(np.any(st.detail.out.e2 < -e0s))

        if crushing(b) and not crushing(a):
            return 3
        if not self.sec.stirrups and self.state_code(b) == 1 and self.state_code(a) != 1:
            return 5
        if self._marks(a)[2] != self._marks(b)[2]:
            return 4
        return 0

    def _ends(self, last: Stage, prev: Stage, peak: float, count: int) -> bool:
        """Response's end of a response, tested after each accepted stage [B 00419990]."""
        an, sec = self.an, self.sec
        if self.state_code(last) != 0 and abs(last.lam) < 0.8 * abs(peak):
            return True
        if self._event(prev, last):
            return False
        if abs(last.lam) < 0.2 * abs(peak) and count >= 11:
            return True
        if an.n0 != 0.0 or an.m0 != 0.0 or an.v0 != 0.0:
            # a load that is being increased has all but gone
            top = [max(abs(getattr(s, k)) for s in self.stages) for k in "nmv"]
            big = max(top) / 1000.0
            for k, mx, inc, con in zip("nmv", top, (an.dn, an.dm, an.dv),
                                       (an.n0, an.m0, an.v0)):
                if mx < big or mx <= 1.0:
                    continue
                if abs(getattr(last, k)) < mx / 100.0 and (abs(inc) > 1e-3 or abs(con) > 1e-3) \
                        and (con + 0.01) * (inc + 0.01) > 0.0:
                    return True
        d = last.detail
        e0max = max(law.e0 for law in sec.laws)
        if float(-np.min(d.out.e2)) > 4.0 * e0max:
            return True
        if float(np.max(d.ey)) > 0.05:
            return True
        rup = max((l.steel.rupture for l in sec.layers), default=0.0)
        if rup > 0.0:
            net = np.asarray(d.ex)          # net of shrinkage
            if net[0] > 5.0 * rup or net[-1] > 5.0 * rup:
                return True
        return False

    def run(self, max_stages=400) -> list[Stage]:
        """The response, stage by stage, as Response-2000 finds it: its control variable and
        steps, its bracketing of events, its acceptance of a stage, what it does when a stage
        is refused, and its end tests (docs/kernel.md, "Response's own load stage control")."""
        an = self.an
        if an.dn == 0.0 and an.dm == 0.0 and an.dv == 0.0:
            self.mode = "none"
            return super().run(max_stages)
        self.mode = self.mode0 = self.first_control()
        # half steps in the program's solve throughout: under control of the axial strain,
        # and where M/V is between 0.15 and 0.75 of the depth [B 00419250]
        arm = abs(an.dm / an.dv) if an.dv != 0.0 else 0.0
        self.half_steps = self.mode0 == "e0" or 0.15 * self.sec.h < arm < 0.75 * self.sec.h
        self.step_share = 0.5 if self.half_steps else 1.0
        st0 = self.initial()
        st0.control, st0.cmode = self.control_of(st0), self.mode
        st0.profile = an.profile()
        self.accept(st0)
        unit = lambda: 1e-3 if self.mode == "phi" else 1.0     # Response's rad/m against rad/mm
        d0 = self.base_step(self.mode)
        mult = 1.0
        target = st0.control + d0 / 6.0
        pending: list[Stage] = []       # stages set aside while an event is closed in on
        start: Stage | None = None      # the stage a stage put in between starts from

        def next_target():
            """The next stage [B 00415e30]: close in on an event, take up a stage set
            aside, or step on."""
            nonlocal target, peak, start
            start = None
            while True:
                a, b = self.stages[-2], self.stages[-1]
                ev = self._event(a, b)
                travel = abs(self.control_of(b) - self.control_of(self.stages[0]))
                gap = self.control_of(b) - self.control_of(a)
                share = {1: 0.02, 2: 0.02, 3: 0.005, 4: 0.01, 5: 0.02}.get(ev, 0.0)
                if ev and abs(gap) >= 1e-10 and abs(gap) > share * travel \
                        and len(pending) < 60 and not getattr(b, "closed", False):
                    pending.append(self.stages.pop())
                    self._uncommit()
                    target = self.control_of(a) + (0.8 if ev == 2 else 0.2) * gap
                    # the first estimate: the strains of whichever of the two is nearer in
                    # the control variable [B 00416730]; the profile of the stage set aside
                    # where that one has un-cracked, else of the stage before [B 00415e30]
                    if abs(self.control_of(b) - target) < abs(self.control_of(a) - target):
                        start = b
                    src = b if ev == 2 else a
                    if getattr(src, "profile", None) is not None:
                        an.set_profile(src.profile)
                    return
                if pending:
                    nxt = pending.pop()
                    self.accept(nxt)
                    if getattr(nxt, "profile", None) is not None:
                        an.set_profile(nxt.profile)
                    peak = max(peak, nxt.lam)
                    target = nxt.control
                    continue
                target += d0 * mult
                return

        peak = 0.0
        retries = 0
        solves = 0
        def grow(at):
            """The base step grows to a tenth of the target [B 00418860]: tested before
            every pass on a stage, with the target as it is then."""
            nonlocal d0
            if len(self.stages) > 4 and mult <= 1.0 and abs(at) > 1e-4 * unit() \
                    and abs(d0) < abs(at) / 10.0:
                d0 = math.copysign(abs(at) / 10.0, d0)

        while len(self.stages) + len(pending) < max_stages and solves < 327:
            prev = self.stages[-1]
            n_st = len(self.stages)
            if not self.late_growth:
                grow(target)    # r2c's earlier reading: once, before a stage's first try
            elif retries:
                grow(target)    # a further try: its target was set when the last one failed
            solves += 1
            self.why = ""
            self.tried = 0
            try:
                st = self.solve(target, start or prev, dict(
                    mult=mult, peak=peak,
                    last=prev.lam if len(self.stages) > 1 else None))
                st.parent = prev        # the stage it follows, for its envelope (export)
                ok = st.failed is None
                if st.lam < 0.0 and len(self.stages) > 1:
                    # the loads reversed: not a state of this loading (Response's shear is
                    # never negative, the manual 3-5)
                    st, ok = None, False
            except SolveError:
                st, ok = None, False
            if self.late_growth and (st.passes if st is not None else self.tried) >= 2:
                grow(target)    # from the second pass on, against this try's own target
            code = 0
            if ok:
                st.cmode = self.mode
                code = self.state_code(st)
                if st.perr >= self.profile_tol and st.perr > self.profile_accept \
                        and st.lam > peak:
                    ok = False          # not converged after 16 passes, with the load above
                if code != 0 and mult >= 0.5:
                    ok = False
                if code == 3 and st.lam > peak:
                    ok = False
            if self.trace is not None:
                self.trace.append(dict(
                    n=len(self.stages), mode=self.mode, target=target, mult=mult, kept=ok,
                    solved=st is not None, code=code, peak=peak,
                    lam=None if st is None else st.lam, perr=None if st is None else st.perr,
                    passes=None if st is None else st.passes, stage=st,
                    codes=None if st is None else st.codes,
                    why=self.why if st is None else ""))
            if not ok:
                if pending:
                    # a stage put in between that is refused or not solved is dropped; the
                    # stage set aside is taken up as it was found and the event is closed
                    # in on no further; the step is as it was [B 00418af0]
                    pending[-1].closed = True
                    if self.trace is not None:
                        self.trace[-1]["what"] = "dropped"
                    if self.late_growth:
                        grow(target)
                    next_target()
                    continue
                retries += 1
                # back to the state of the stage before [B 004190a0]
                if getattr(prev, "profile", None) is not None:
                    an.set_profile(prev.profile)
                other = self.other_control() if self.mode0 != "gam" else self.mode
                if mult < (0.05 if self.mode == "e0" else 0.2) and other != self.mode:
                    # change the control variable [B 004162d0]
                    old = self.mode
                    self.mode = other
                    self.half_steps, self.step_share = True, 0.5    # [B 004162d0]
                    n_st = len(self.stages)
                    ref = self.stages[0] if n_st < 3 else \
                        self.stages[n_st - 3 if n_st - 2 <= 2 else n_st // 3]
                    here = self.control_of(prev)
                    move = here if n_st < 3 else here - self.control_of(ref)
                    d0 = abs(self.base_step(other)) * (1.0 if move >= 0 else -1.0)
                    if n_st > 4 and abs(here) > 1e-6 * unit() and abs(d0) < abs(here) / 10.0:
                        d0 = math.copysign(abs(here) / 10.0, d0)
                    mult = 1.0
                    target = here + d0 * mult
                    pending.clear()
                    if getattr(self, "debug", False):
                        print(f"  control {old} -> {other} at stage {n_st}")
                    continue
                # closer to the stage before [B 0041a870, 1]; the next solve starts on half
                # steps [B 00418af0]
                self.step_share = 0.5
                last_c = prev.control if prev.cmode == self.mode else self.control_of(prev)
                if pending:
                    gap = pending[-1].control - last_c
                elif n_st >= 2:
                    gap = last_c - self.control_of(self.stages[-2])
                else:
                    gap = d0 / 6.0
                if abs(gap) + 1e-6 * unit() < abs(mult * d0) and mult < 1.01:
                    target = last_c + 0.5 * gap
                    mult *= 0.5
                elif mult == 1.0:
                    # the first refusal of a whole step: half a step further on, not back
                    # (the multiplier's 1.5 is the step tried) [B 0041a870]
                    target += 0.5 * d0
                    mult = 1.5
                else:
                    mult *= 0.5
                    target = target * 0.5 if n_st == 1 else target - mult * d0
                if mult < 0.005:
                    break
                continue
            # accepted
            if mult == 1.5:
                mult = 1.0
            if retries == 0 and mult < 0.25:
                mult *= 2.0
            retries = 0
            self.accept(st)
            peak = max(peak, st.lam)
            if len(self.stages) >= 2 and self._ends(st, prev, peak, len(self.stages)):
                break
            if abs(st.lam) < 0.01 * abs(prev.lam) and len(self.stages) > 2:
                self.stages.pop()       # the load has run out: not a load stage
                break
            if self.late_growth:
                # a new stage's first pass is begun before its target is set: the step
                # is tested once more against the target of the stage just kept
                grow(target)
            next_target()
        return self.stages[:max_stages]

    def _uncommit(self):
        """Put the history (plastic strains, ruptured bars) back to that of the stages kept,
        after a stage has been set aside."""
        an = self.an
        an.ep[:] = an.ep0
        an.epy = np.zeros(len(an.epy))
        an.dead[:] = False
        for i, st in enumerate(self.stages):
            if i:
                an.commit(st.e0, st.phi)
                if st.gam != 0.0:
                    an.commit_stirrups(st.detail)
