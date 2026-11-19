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
    # with shear, r2c's profile iteration fails at some states where Response's does not:
    # look beyond such a state before ending the response (docs/verification.md)
    search_beyond = True

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
        self.profile_tol = 0.01
        # an iteration that does not converge is accepted at its closest iterate within this
        self.profile_accept = 0.03
        self.evals = 0
        self.budget = 600
        self.ratio = 1.2        # reported (force-weighted) shear strain over the plain mean

    # -- tangent stiffness and the shear flow ---------------------------------------------------
    def tangent(self, e0, phi, gam):
        """Per node: the condensed tangent stiffness (j, k, m, n) of thesis eq. 6-4, with the
        state it was taken at."""
        an, sec = self.an, self.sec
        z, b = an.layer_nodes()
        zf = z.ravel()
        es, fs = an.steel(e0, phi)
        f1cx = an.crack_check(e0, phi, es, fs)
        out, ex, g, smx, smt, ey = an.eval_nodes(e0, phi, gam, z, f1cx)
        m = sec.tab(sec.t_m, zf)
        ft = np.interp(zf, sec.tz, an.t_ft)
        cx = f1cx(zf)
        idx = an.law_index(zf, z)
        sts = an.stirrups_at(zf)
        rcrit = sec.tab(sec.t_rhocrit, zf)
        epy = np.interp(zf, sec.tz, an.epy)

        def fixed(exv, eyv, gv):
            fx = np.empty(len(zf))
            fy = np.empty(len(zf))
            vv = np.empty(len(zf))
            tot, res, _ = an.stirrup_stress(sts, eyv, rcrit, epy)
            for j, law in enumerate(sec.laws):
                k = idx == j
                if not k.any():
                    continue
                o = nodelib.evaluate(law, exv[k], eyv[k], gv[k], m[k], ft[k], smx[k], smt[k],
                                     cx[k], res[k])
                fx[k], fy[k], vv[k] = o.fcx, o.fcy + tot[k], o.v
            return fx, fy, vv

        d = 2e-7
        f0 = fixed(ex, ey, g)
        fa = fixed(ex + d, ey, g)
        fb = fixed(ex, ey + d, g)
        fc = fixed(ex, ey, g + d)
        a_, d_, g_ = ((fa[i] - f0[i]) / d for i in range(3))
        b_, e_, h_ = ((fb[i] - f0[i]) / d for i in range(3))
        c_, f_, i_ = ((fc[i] - f0[i]) / d for i in range(3))
        e_safe = np.where(np.abs(e_) > 1e-6, e_, np.inf)
        jj = a_ - b_ * d_ / e_safe
        kk = c_ - b_ * f_ / e_safe
        mm = g_ - h_ * d_ / e_safe
        nn = i_ - h_ * f_ / e_safe
        shp = z.shape
        return dict(z=z, b=b, out=out, ex=ex, g=g, ey=ey, es=es, fs=fs, j=jj.reshape(shp),
                    k=kk.reshape(shp), m=mm.reshape(shp), n=nn.reshape(shp))

    def shear_flow(self, e0, phi, gam, v_total):
        """The shear stress profile longitudinal equilibrium requires: (z nodes from the top
        down, stress from the state, stress calculated, tangent shear stiffness, state)."""
        an, sec = self.an, self.sec
        t = self.tangent(e0, phi, gam)
        z, b = t["z"], t["b"]
        y = z - sec.zaxial
        s = np.interp(z, an.shape_z, an.shape)
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
            de = 1e-7
            f1 = an.steel(e0 + de, phi)[1][i]
            et = (f1 - t["fs"][i]) / de
            if math.isnan(et):
                continue
            if abs(t["fs"][i]) >= l.steel.fy * l.steel.phi - 1e-6:
                # on its yield plateau (not unloading) a bar keeps the stiffness of the start
                # of strain hardening
                et = max(et, l.steel.plateau_stiffness(t["es"][i]))
            jz = float(np.interp(l.z, z.ravel()[::-1], t["j"].ravel()[::-1]))
            ea = (et - jz) * l.area
            yb = l.z - sec.zaxial
            jm[0, 0] += ea
            jm[0, 1] -= ea * yb
            jm[1, 0] -= ea * yb
            jm[1, 1] += ea * yb * yb
            bars.append((l.z, ea, yb, l.db, i))
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

    def update_shape(self, z, vstate, tau, t, relax=1.0):
        """A new shear strain profile from the calculated stresses: secant stiffness where the
        node carries shear, tangent stiffness where it does not yet. Returns the largest
        mismatch between the calculated and the state's shear stress, relative to the peak."""
        an, sec = self.an, self.sec
        g = t["g"].reshape(z.shape)
        nn = t["n"]
        with np.errstate(divide="ignore", invalid="ignore"):
            sec_g = np.where(np.abs(g) > 1e-12, vstate / g, 0.0)
        gc = sec.conc0.Ec / 2.0
        use_sec = (sec_g > 1e-4 * gc) & (np.abs(vstate) > 1e-6)
        stiff = np.where(use_sec, sec_g, np.maximum(nn, 1e-4 * gc))
        gnew = tau / stiff
        # keep the step of each node bounded: the same sign as the shear, and no more than
        # doubled or halved where the node already has a shear strain
        sgn = 1.0 if float(np.sum(vstate)) >= 0 else -1.0
        gnew = np.maximum(gnew * sgn, 0.0)
        gold = g * sgn
        big = gold > 0.02 * max(float(np.max(gold)), 1e-12)
        gnew = np.where(big, np.clip(gnew, 0.5 * gold, 2.0 * gold),
                        np.minimum(gnew, 2.0 * max(float(np.max(gold)), 1e-12))) * sgn
        gnew[0, 0] = 0.0
        gnew[-1, 2] = 0.0
        # how far the calculated stresses are from those of the state: the shear force that
        # the difference amounts to, relative to the shear force itself
        dzl = z[:, 0] - z[:, 2]
        wts = np.array([1.0, 4.0, 1.0]) / 6.0
        bb = t["b"]
        tot = float(np.sum((np.abs(vstate) * bb) @ wts * dzl))
        dif = float(np.sum((np.abs(tau - vstate) * bb) @ wts * dzl))
        err = dif / tot if tot > 1e-9 else 0.0
        # onto the profile's own grid, bottom up
        zf = z.ravel()[::-1]
        gf = gnew.ravel()[::-1]
        zz, ii = np.unique(zf, return_index=True)
        prof = np.interp(an.shape_z, zz, gf[ii])
        bw = sec.width(an.shape_z)
        mean = np.trapezoid(prof * bw, an.shape_z) / np.trapezoid(bw, an.shape_z)
        if not np.isfinite(mean) or abs(mean) < 1e-15:
            return err, None
        new = prof / mean
        an.shape = (1.0 - relax) * an.shape + relax * new
        return err, mean

    # -- one state ------------------------------------------------------------------------------
    def _residual(self, c, x):
        an = self.an
        if self.mode == "phi":
            e0, gam, phi = x[0], x[1], c
        elif self.mode == "e0":
            phi, gam, e0 = x[0], x[1], c
        else:
            e0, phi, gam = x[0], x[1], c / self.ratio
        self.evals += 1
        if self.evals > self.budget:
            raise SolveError("no equilibrium found within the iteration limit")
        n, m, v = an.forces(e0, phi, gam)
        rn = lambda lam: (n - an.n0 - lam * an.dn) / self.nscale
        rm = lambda lam: (m - an.m0 - lam * an.dm) / self.mscale
        rv = lambda lam: (v - an.v0 - lam * an.dv) / self.vscale
        if self.mode == "phi":
            lam = (m - an.m0) / an.dm
            r = np.array([rn(lam), rv(lam)])
        elif self.mode == "e0":
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
        return best[1], best[2], best[0] < 2e-5

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

    def solve(self, c, prev: Stage | None) -> Stage:
        """The state at control value c: curvature, or the shear strain when there is no
        moment increment."""
        an = self.an
        keep = (an.shape.copy(), self.ratio)
        try:
            return self._solve(c, prev)
        except SolveError:
            an.shape, self.ratio = keep
            raise

    def _solve(self, c, prev: Stage | None) -> Stage:
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
        saved_shape = an.shape.copy()
        saved_ratio = self.ratio
        self.evals = 0
        info = None
        ok = False
        best = None
        err = 1.0
        for outer in range(30):
            x0 = np.array(x, dtype=float)
            x, info, ok = self._newton(c, x0)
            if not ok:
                x, info, ok = self._nested(c, x0)
            if getattr(self, "debug", False):
                print(f"   outer {outer}: newton ok={ok} x={x} lam={info[3]:.4f}")
            if not ok:
                break
            e0, phi, gam, lam, n, m, v = info
            if outer < 3 and an.refine(e0, phi, gam):
                continue
            z, vstate, tau, t, _d = self.shear_flow(e0, phi, gam, v)
            prev_shape = an.shape.copy()
            err, mean = self.update_shape(z, vstate, tau, t, relax=self.relax(outer))
            if getattr(self, "debug", False):
                print(f"   outer {outer}: profile err={err:.4f} mean={mean}")
            if best is None or err < best[0]:
                best = (err, info, prev_shape, tau.copy(), np.array(x, dtype=float))
            if self.mode == "gam":
                # keep the reported shear strain at the control value
                zz_, b_ = t["z"].ravel(), t["b"].ravel()
                vv_, gg_ = t["out"].v, t["g"]
                den_ = np.trapezoid(vv_ * b_, zz_)
                bm_ = np.trapezoid(b_, zz_)
                if abs(den_) > 1e-9 and abs(gam) > 1e-15:
                    rep_ = np.trapezoid(vv_ * gg_ * b_, zz_) / den_
                    new_ratio = float(rep_ / gam)
                    if 0.2 < new_ratio < 5.0:
                        if abs(new_ratio - self.ratio) > 0.002 * self.ratio:
                            err = max(err, self.profile_tol * 1.01)
                        self.ratio = new_ratio
            if err < self.profile_tol:
                break
            if mean is not None and self.mode != "gam" and abs(gam) < 1e-12:
                x = [x[0], mean]
        if ok and best is not None and err > self.profile_tol and best[0] < err:
            # not converged: take the closest iterate
            err, an.shape = best[0], best[2].copy()
            x, info, ok = self._newton(c, best[4])
            if not ok:
                x, info, ok = self._nested(c, best[4])
        if not ok or info is None or err > self.profile_accept:
            an.shape = saved_shape
            self.ratio = saved_ratio
            raise SolveError(f"no equilibrium at control value {c:g}")
        e0, phi, gam, lam, n, m, v = info
        if not all(math.isfinite(q) for q in info) or abs(gam) > 0.2 or abs(e0) > 0.2:
            an.shape = saved_shape
            self.ratio = saved_ratio
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
        if self.sec.stirrups:
            zs = np.asarray(det.z, dtype=float)
            order = np.argsort(zs)
            zu, iu = np.unique(zs[order], return_index=True)
            fu = np.asarray(det.fsy, dtype=float)[order][iu]
            grid = np.linspace(zu[0], zu[-1], 161)
            fg = np.interp(grid, zu, fu)
            dg = np.abs(np.gradient(fg, grid))
            det.tbond = np.interp(zs, grid, dg) * self.sec.stirrups[0].db / 4.0
        st = Stage(e0, phi, gam, lam, n, m, v, det, control=c)
        # the shear strain Response reports: weighted by the shear force over the depth
        num = np.trapezoid(det.out.v * det.gxy * det.b, det.z)
        den = np.trapezoid(det.out.v * det.b, det.z)
        st.gam_avg = float(num / den) if abs(den) > 1e-9 else 0.0
        st.perr = err
        return st

    def relax(self, outer: int) -> float:
        return 1.0 if outer == 0 else 0.5

    def collapsed(self, st: Stage, peak: float) -> bool:
        """After a shear failure the load falls away: the response ends once less than half of
        the peak load is left."""
        return peak > 0 and st.lam < 0.5 * peak
