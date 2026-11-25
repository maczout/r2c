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
THIN = 0.05          # mm: half the layer Response-2000 puts across a step [B 00434eb0]
THIN_WIDTH = 10.0    # mm: the change of width from which it does [B 00434eb0]


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
    lone: np.ndarray | None = None      # nodes with next to no shear strain (lone_nodes)
    # the concrete's shrinkage or thermal strain at the nodes, where the section has any: ex
    # and the principal strains of out are the concrete's own, less it; ey is the whole strain
    sh: np.ndarray | None = None


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


# Response's layer 0.1 mm thick across a step in width (docs/kernel.md, "Layers")
own_thin_layer = True


class Analysis:
    def __init__(self, sec: Section, const=(0.0, 0.0, 0.0), incr=(0.0, 1.0, 0.0)):
        self.sec = sec
        self.n0, self.m0, self.v0 = const
        self.dn, self.dm, self.dv = incr
        self.shear = (self.dv != 0.0) or (self.v0 != 0.0)
        self.t_ft = sec.cracking_table(self.n0, self.m0, self.dn, self.dm)
        # the steps in width, and those Response-2000 puts a thin layer across (docs/kernel.md,
        # "Layers"): a change of width of more than 10 mm, or a change of concrete
        jump = {z: abs(sec.width_side(z, True) - sec.width_side(z, False))
                for z in sec.breaks()[1:-1]}
        self.steps = np.array([z for z, d in jump.items() if d > 1e-6])
        self.thin = np.array([z for z, d in jump.items()
                              if own_thin_layer and (d > THIN_WIDTH or sec.law_at(z + STEP)
                                                     is not sec.law_at(z - STEP))])
        # which side of a thin layer its middle node belongs to: the wider one [O]
        self.thin_side = {float(z): (THIN if sec.width_side(z, True) >= sec.width_side(z, False)
                                     else -THIN) for z in self.thin}
        self.bounds = self._initial_bounds()
        # the shear strain profile's grid: the tables' heights, and a point just above and
        # just below every step in width, where the shear strain jumps (the two faces of the
        # thin layer, where there is one)
        self.shape_z = np.array(sorted(
            set(sec.tz.tolist())
            | {z + d * (THIN if float(z) in self.thin_side else STEP)
               for z in self.steps for d in (-1.0, 1.0)}))
        self.shape_z0 = self.shape_z.copy()      # the profile's base grid
        self.shape = self._elastic_shape()
        self.max_layers = 220
        # plastic strain of each layer, from which it unloads elastically
        self.ep0 = np.zeros(len(sec.layers))
        self.ep = self.ep0.copy()
        # plastic strain of the stirrups over the depth, as a table over height
        self.epy_z = np.array([sec.zbot, sec.ztop])
        self.epy = np.zeros(2)
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
        bd = set(round(z, 9) for z in bd) | set(sec.breaks())
        # across a step, a layer 0.1 mm thick in place of the boundary [B 00434eb0]
        for zs in self.thin:
            bd = {z for z in bd if abs(z - zs) > 1e-6} | {zs + THIN, zs - THIN}
        bd = sorted(bd, reverse=True)
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
            side = self.thin_side.get(float(zs))
            if side is not None:
                # the middle node of the thin layer across the step: on the wider side
                zp[np.abs(z[:, 1] - zs) < 1e-9, 1] = zs + side
                continue
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
        for zs, side in self.thin_side.items():
            b[np.abs(zm - zs) < 1e-9, 1] = sec.width_side(zs, upper=side > 0)
        return z, b

    # -- strain state ---------------------------------------------------------------------------
    def strain(self, e0, phi, z):
        return e0 - phi * (np.asarray(z) - self.sec.zc)

    def steel(self, e0, phi):
        """(strain incl. prestrain, average stress) of every longitudinal layer. The stress is
        Response-2000's (docs/kernel.md, "Bars"): never above what the bar can carry at a
        crack, and nan (no bar) once the bar has ruptured, in the state where its strain at a
        crack passes the end of its curve as much as in the states after it."""
        sec = self.sec
        es = np.array([float(self.strain(e0, phi, l.z)) + l.prestrain for l in sec.layers])
        fs = np.empty(len(es))
        for i, (l, e) in enumerate(zip(sec.layers, es)):
            if self.dead[i]:
                fs[i] = float("nan")
                continue
            # a bar that has yielded unloads along its elastic stiffness
            env = float(l.steel.unloaded(e, self.ep[i]))
            cap = float(l.steel.crack_capacity(e - l.prestrain, l.prestrain, l.rho, l.strand,
                                               self.ep[i]))
            f = env * l.steel.phi
            fs[i] = float("nan") if math.isnan(cap) or math.isnan(f) else min(f, cap)
        return es, fs

    # Response's own history of the stirrups' plastic strain (off: docs/summary.md, D39)
    own_stirrup_history = False

    def commit_stirrups(self, det):
        """Record the plastic strain of the stirrups over the depth at an accepted stage.
        Response-2000's rule [B 0041e310] is the stage's own, at its own nodes, in place of
        what was there; it is written and off (docs/kernel.md, "Shear": D39)."""
        sec = self.sec
        if not sec.stirrups:
            return
        st = sec.stirrups[0].steel
        z = np.asarray(det.z, dtype=float)
        # in the stirrup's own strain: a hoop is strained by less than the concrete (7-6)
        fac = self.stirrups_at(z, det.b)[0][2]
        ep = np.asarray(det.ey, dtype=float) * fac \
            - np.asarray(det.fsy, dtype=float) / (st.E * st.phi)
        zu, iu = np.unique(z, return_index=True)
        if self.own_stirrup_history:
            ep = np.where(np.asarray(det.rhov) > 0, ep, 0.0)
            self.epy_z, self.epy = zu, ep[iu]
            return
        # r2c's own: the largest so far, on the fixed heights of the tables
        ep = np.where((np.asarray(det.rhov) > 0) & (ep > 1e-9), ep, 0.0)
        old = np.interp(sec.tz, self.epy_z, self.epy)
        self.epy_z, self.epy = sec.tz, np.maximum(old, np.interp(sec.tz, zu, ep[iu]))

    def commit(self, e0, phi):
        """Record what an accepted load stage leaves behind: the bars that have ruptured, and
        the plastic strain of the others."""
        es, fs = self.steel(e0, phi)
        for i, l in enumerate(self.sec.layers):
            if math.isnan(fs[i]):
                self.dead[i] = True
                continue
            ep = es[i] - fs[i] / l.steel.phi / l.steel.E
            if es[i] > 0:
                self.ep[i] = max(self.ep[i], ep) if self.ep[i] >= 0 else ep
            elif es[i] < 0:
                self.ep[i] = min(self.ep[i], ep) if self.ep[i] <= 0 else ep

    def crack_check(self, e0, phi, es, fs):
        """The flexural crack check (thesis 4-5; details Response-2000's): the largest average concrete tension each
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
        if sec.shrink:
            z3, z4 = self._net_axes(e0, phi)
        else:
            if etop > 0:
                z3 = na if (na is not None and ebot < 0) else -FAR
            else:
                z3 = ztop
            if ebot > 0:
                z4 = na if (na is not None and etop <= 0) else FAR
            else:
                z4 = zbot
        mtop = mbot = 0.0
        for l, e, f, ep in zip(sec.layers, es, fs, self.ep):
            if not (l.z > z3 or l.z < z4):
                continue
            if math.isnan(f):
                continue
            cap = float(l.steel.crack_capacity(e - l.prestrain, l.prestrain, l.rho, l.strand,
                                               ep))
            df = 0.0 if math.isnan(cap) else max(cap - f, 0.0)
            near = min(min(abs(l.z - z4), abs(l.z - z3)) / (l.db + 0.1), 1.0)
            if l.z > z3:
                mtop += abs(z3 - l.z) * near * l.area * df + 100.0
            if l.z < z4:
                mbot += abs(z4 - l.z) * near * l.area * df + 100.0
        zones = []
        # a zone no bar crosses has no capacity moment and a limit of zero (docs/kernel.md)
        for zn, face, mcap in ((z3, ztop, mtop), (z4, zbot, mbot)):
            hh = abs(face - zn)
            if hh < 0.1:
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
                # the two capacity moments the zone's own is set against are summed without
                # the concrete's material factor; the limits at the face and at the axis
                # (below) carry it [B 00440400, 00441d80]
                ma += law.ft * a1 * 0.6
                mb += law.ft * a2 * (3.0 - 0.6)
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

        # between the two zones' axes (each the face itself where that face is not in
        # tension) the limit is three times the tensile strength of the concrete at each
        # axis, linear between them [B 00441d80, 004b5470]: it is what holds a node that
        # cracks diagonally above the flexural tension zone
        za, zb = min(max(z3, zbot), ztop), min(max(z4, zbot), ztop)
        la, lb = sec.law_at(za), sec.law_at(zb)
        pa, pb = 3.0 * la.ft * la.phi, 3.0 * lb.ft * lb.phi

        def f1cx(z):
            z = np.asarray(z, dtype=float)
            if za > zb:
                out = pb + (pa - pb) * np.clip((z - zb) / (za - zb), 0.0, 1.0)
            else:
                out = np.full(z.shape, BIG)     # all in tension: the zones cover the depth
            for zn, face, fna, fface in zones:
                inside = (z > zn) if face == ztop else (z < zn)
                tt = np.clip(np.abs(z - zn) / abs(face - zn), 0.0, 1.0)
                out = np.where(inside, fna + (fface - fna) * tt, out)
            return out
        # the zone the steel stress at a crack is worked out for: the deeper of the two, its
        # capacity moment and its neutral axis; a section all in tension counts as no depth
        # and gives the upper zone, with its axis far below
        dtop = ztop - z3 if abs(z3) < FAR else 0.0
        dbot = z4 - zbot if abs(z4) < FAR else 0.0
        f1cx.mcap, f1cx.zref = (mtop, z3) if dbot <= dtop else (mbot, z4)
        return f1cx

    def _net_axes(self, e0, phi):
        """The axes of the two flexural tension zones where the concrete has a shrinkage or
        thermal strain [B 00441d80, 004bb0d0, 004ff8f0]: a zone is where the concrete's own
        strain (the section's less the offset) is tension. From each face in tension the
        program walks over the heights at which the shrinkage profile is given (and those
        of a second table over the depth, taken here to be the outline's) and puts the axis
        where the concrete's own strain changes sign, on a straight line between the two
        heights. Returns (z3, z4) as crack_check uses them."""
        sec = self.sec
        ztop, zbot = sec.ztop, sec.zbot
        pts = {ztop, zbot} | {z for z, _ in sec.shrink}
        for z1, z2, *_ in sec.segs:
            pts |= {z1, z2}
        pts = sorted(z for z in pts if zbot <= z <= ztop)

        def net(z):
            return float(self.strain(e0, phi, z)) - float(sec.shrinkage(np.array([z]))[0])

        def walk(order, start_in_tension, none):
            prev, nprev = order[0], net(order[0])
            if not start_in_tension(nprev):
                return order[0]
            for z in order[1:]:
                n = net(z)
                if n < 0.0 and nprev > 0.0:
                    return prev - (prev - z) * nprev / (nprev - n)
                prev, nprev = z, n
            return none

        z3 = walk(pts[::-1], lambda n: n >= 0.0, -FAR)
        z4 = walk(pts, lambda n: n > 0.0, FAR)
        return z3, z4

    # -- nodes ----------------------------------------------------------------------------------
    def eval_nodes(self, e0, phi, gam, z, f1cx, ey=None):
        """Concrete stresses at heights z (any shape) for the global strain state."""
        sec = self.sec
        shp = z.shape
        zf = z.ravel()
        # the concrete's own strain: the section's, less what shrinkage or temperature
        # would give it unrestrained. The offset is the same along and across the member
        # [B 004a9d90, 004ff8f0]
        sh = sec.shrinkage(zf)
        ex = self.strain(e0, phi, zf) - sh
        m = sec.bond_m(zf)
        ft = np.interp(zf, sec.tz, self.t_ft)
        smx = sec.smx_at(zf)
        smt = sec.smt_at(zf)
        cx = f1cx(zf)
        g = gam * np.interp(self.profile_z(z).ravel(), self.shape_z, self.shape) \
            if gam != 0.0 else np.zeros_like(zf)
        if (self.shear or sec.shrink) and ey is None:
            # with shear, and at any node with shrinkage or thermal strain, the transverse
            # strain is solved for [B 004a8b20: its test for the node with no stirrups]
            out, eyv = self.transverse(zf, z, ex, g, m, ft, smx, smt, cx, sh)
            return out, ex, g, smx, smt, eyv
        eyv = np.zeros_like(zf) if ey is None else ey.ravel()
        cy = np.zeros_like(zf)
        if sec.shrink:
            eyc = eyv - sh          # a transverse strain given is the node's whole one
        else:
            eyc = eyv
        if len(sec.laws) == 1:
            out = nodelib.evaluate(sec.laws[0], ex, eyc, g, m, ft, smx, smt, cx, cy)
        else:
            # a node on the boundary of two concretes belongs to the layer it was made for
            idx = self.law_index(zf, z)
            fields = {}
            for j, law in enumerate(sec.laws):
                k = idx == j
                if not k.any():
                    continue
                o = nodelib.evaluate(law, ex[k], eyc[k], g[k], m[k], ft[k], smx[k], smt[k],
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
            a_n += np.where(inside, st.area / sec.n_trans, 0.0)
            a_s += np.where(inside, st.area / (st.space + 1e-4), 0.0)
        eff = np.clip(0.5 * (3.0 - a_n / (a_s + 1e-9) / sec.h), 0.0, 1.0)
        res = eff * (np.maximum(yld, capt) - tot)
        return tot, res, rho_t

    def transverse(self, zf, z, ex, g, m, ft, smx, smt, cx, sh=None):
        """The transverse strain of every node, from the condition that there is no total
        stress across the member: concrete fcy and the stirrups balance (thesis 7-2). sh is
        the concrete's shrinkage or thermal strain at each node: the concrete works on the
        transverse strain less it, the stirrups on the whole of it [B 004a8b20, 0046aaa0]."""
        sec = self.sec
        sts = self.stirrups_at(zf, self.node_width(z))
        rcrit = sec.tab(sec.t_rhocrit, zf)
        epy = np.interp(zf, self.epy_z, self.epy)
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
                o = nodelib.evaluate(law, rep(ex), eyl if sh is None else eyl - rep(sh),
                                     rep(g), rep(m), rep(ft), rep(smx), rep(smt), rep(cx),
                                     st_res)
                tot[sel] = (o.fcy + st_tot).reshape(-1, k)
                outs.append(o)
            return tot.reshape(shp), outs

        # scan a ladder of transverse strains for the first change of sign, then close in
        mag = 1e-6 * 1.7 ** np.arange(0, 21)
        ladder = np.concatenate([-mag[::-1][6:], [0.0], mag])
        if sh is not None and sh.any():
            # the ladder is laid about the strain at which the concrete is unstrained
            ladder = sh[:, None] + ladder[None, :]
        else:
            sh = None
            ladder = np.broadcast_to(ladder, (n, len(ladder))).copy()
        f, _ = run(ladder)
        pos = f > 0
        first = np.argmax(pos, axis=1)
        none = ~pos.any(axis=1)
        first = np.where(none, ladder.shape[1] - 1, first)
        first = np.maximum(first, 1)
        rows = np.arange(n)
        lo, hi = ladder[rows, first - 1], ladder[rows, first]
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
        fscr = self.steel_at_crack(e0, phi, es, fs, zz, o2, b.ravel()[sel], f1cx)
        rhov = sec.tab(sec.t_rhov, zz)
        ey = eyn[sel]
        fsy = np.zeros(len(sel))
        fsycr = np.zeros(len(sel))
        if (self.shear or sec.shrink) and sec.stirrups:
            tot, _res, rho_t = self.stirrup_stress(self.stirrups_at(zz, b.ravel()[sel]), ey,
                                                   sec.tab(sec.t_rhocrit, zz),
                                                   np.interp(zz, self.epy_z, self.epy))
            has = rho_t > 0
            fsy[has] = tot[has] / rho_t[has]
            # at a crack the stirrups also carry what the concrete carries between cracks
            law = sec.conc0
            fl = np.maximum(law.ft, np.interp(zz, sec.tz, self.t_ft)) / (1.0 + 250.0 * o2.w) \
                * law.phi
            extra = np.maximum(o2.f1 - fl, 0.0) - o2.vci * o2.tan
            on = has & (o2.w > 0)
            fsycr[on] = extra[on] / rho_t[on] + fsy[on]
        sh = sec.shrinkage(zz) if sec.shrink else None
        lone = self.lone_nodes(zz, ex[sel], ey if sh is None else ey - sh, g[sel])
        if lone.any():
            # (such a node's transverse strain is its offset: next to nothing)
            ey = np.where(lone, 0.0 if sh is None else sh, ey)
            fsy[lone] = 0.0
            fsycr[lone] = 0.0
        return Detail(z=zz, b=b.ravel()[sel], ex=ex[sel], ey=ey, gxy=g[sel],
                      out=o2, smx=smx[sel], smt=smt[sel], fsy=fsy,
                      fsycr=fsycr, rhov=rhov, fs=fs, fscr=fscr, es=es,
                      f1cx=f1cx(zz), lone=lone, sh=sh)

    def lone_nodes(self, z, ex, ey, g):
        """The nodes Response-2000 takes through its node routine for no shear strain
        [B 004a8b20, 004a7b60]: a node whose shear strain is under two millionths of the
        difference of its longitudinal and transverse strains (each less the shrinkage or
        thermal strain; ex and ey are given so), plus 1e-10, where the concrete has next to
        no shrinkage or thermal strain: the sizes of the node's four offsets (along, across
        and in the two principal directions, all the same strain here) come to under 1e-6.
        Such a node has no transverse strain but its offset and no stirrups: their stress
        and their ratio are nothing there. Applied to the state a stage reports; the forces
        are not evaluated differently (docs/kernel.md, "A node with next to no shear
        strain"). Without shear and without shrinkage every node is one, and r2c solves no
        transverse strain at all."""
        if not self.shear and not self.sec.shrink:
            return np.zeros(len(z), dtype=bool)
        lone = np.abs(g) < 2e-6 * np.abs(ex - ey) + 1e-10
        return lone & (4.0 * np.abs(self.sec.shrinkage(z)) < 1e-6)

    def steel_at_crack(self, e0, phi, es, fs, z, out, b, f1cx):
        """Stress of each longitudinal layer at a crack (thesis 4-5, last part; the details
        are Response-2000's, docs/kernel.md "Steel stress at a crack"): the moment about the
        neutral axis of the concrete tension the cracks do not carry is taken by an extra
        curvature about that axis, of every bar in tension. nan: no value (a bar ruptured, or
        the bars cannot take the moment)."""
        sec = self.sec
        res = np.zeros(len(sec.layers))
        if not len(sec.layers):
            return res
        zref, mcap = f1cx.zref, f1cx.mcap
        # the concrete's moment: the tension above the floor, and the shear on the crack,
        # over the halves of layers that are cracked at both ends, on the tension side
        law = sec.conc0
        ft = np.maximum(law.ft, np.interp(z, sec.tz, self.t_ft)) * law.phi
        fl = ft / (1.0 + 250.0 * out.w)
        g = np.maximum(out.f1 - fl, 0.0) + out.vci / out.tan
        cr = out.e1 > out.ecr
        side = (z >= zref) if phi <= 0 else (z <= zref)
        ok = cr & side
        d = np.abs(zref - z)
        k = ok[:-1] & ok[1:]
        g1, g2, b1, b2, d1, d2 = g[:-1], g[1:], b[:-1], b[1:], d[:-1], d[1:]
        mom = float(np.sum(((g1 + g2) * (b1 + b2) * (d1 + d2) * 0.5 + g1 * b1 * d1
                            + g2 * b2 * d2)[k] * (z[:-1] - z[1:])[k] / 6.0))
        # the bars in tension, and the extra curvature that uses up the first one's reserve
        bars = []
        dmin = 1e-3         # 1/mm
        lin = 0.0
        for i, l in enumerate(sec.layers):
            e = float(self.strain(e0, phi, l.z))
            if e - float(sec.shrinkage(np.array([l.z]))[0]) <= 0:
                continue
            arm = abs(zref - l.z)
            bars.append((i, l, e, arm))
            if math.isnan(fs[i]):
                continue
            cap = float(l.steel.crack_capacity(e, l.prestrain, l.rho, l.strand, self.ep[i]))
            room = 0.0 if math.isnan(cap) else max(cap - fs[i], 0.0)
            if arm > 0:
                dmin = min(dmin, room / (l.steel.E * l.steel.phi) / arm)
        for i, l, e, arm in bars:
            if e < l.steel.fy / l.steel.E:
                lin += l.steel.E * l.steel.phi * dmin * arm * arm * l.area

        def at(i, l, e, extra):
            """The bar's stress with an extra strain at the crack; nan when it ruptures."""
            if math.isnan(fs[i]):
                return float("nan")
            s = float(l.steel.unloaded(es[i] + extra, self.ep[i])) * l.steel.phi
            cap = float(l.steel.crack_capacity(e + extra, l.prestrain, l.rho, l.strand,
                                               self.ep[i]))
            if math.isnan(cap):
                return float("nan")
            return cap if math.isnan(s) else min(s, cap)

        def resist(dphi):
            tot = 0.0
            for i, l, e, arm in bars:
                s = at(i, l, e, dphi * arm)
                if not math.isnan(s):
                    tot += arm * (s - fs[i]) * l.area
            return tot

        dphi = None
        if lin < mom:
            # past what the bars take elastically: solved, if it is within the capacity
            # moment of the crack check (2 N m over)
            if mom < 1.001 * mcap + 2000.0:
                step = 1e-3 / sec.h if abs(zref) <= 20.0 * sec.h else 5e-10
                hi = step
                for _ in range(50):
                    hi += step
                    if resist(hi) >= mom:
                        break
                else:
                    best = 0.0
                    for i, l, e, arm in bars:
                        x = ((l.steel.rupture - l.prestrain) * 1.01 - e) / (arm + 0.1)
                        if resist(x) > best:
                            best, hi = resist(x), x
                    if best < mom:
                        hi = 0.0
                    step = hi
                lo = hi - step
                for _ in range(10):
                    mid = 0.5 * (lo + hi)
                    if resist(mid) > mom:
                        hi = mid
                    else:
                        lo = mid
                dphi = 0.5 * (lo + hi)
        elif lin <= 0:
            dphi = dmin
        else:
            dphi = mom / lin * dmin
        tension = {i for i, *_ in bars}
        if dphi is None:
            # no value: the bars in compression show their own stress
            for i in range(len(sec.layers)):
                res[i] = float("nan") if i in tension else fs[i]
            return res
        for i, l, e, arm in bars:
            ecr = max(float(np.interp(l.z, sec.tz, self.t_ft)) / law.Ec, law.ecr)
            if e + arm * dphi - float(sec.shrinkage(np.array([l.z]))[0]) >= ecr:
                res[i] = at(i, l, e, arm * dphi)
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
        self.slope = None     # of the unbalanced force, carried from solve to solve
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

    def _solve_balanced(self, c, prev: Stage | None) -> Stage:
        """The balanced state at control value c (curvature, or strain at the centroid):
        r2c's own solve, to a root of the unbalanced force."""
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

    # Response-2000's solve of a stage without shear [B 00425f10, 0041e1e0, 00425af0;
    # docs/kernel.md "The stage solve without shear"]. It works in N, N m and 1/m; so does
    # this, because its tolerance and its guard against a zero slope are not dimensionless.
    def _unbalanced(self, e0, phi):
        """(unbalanced force, tolerance, (N, M, V)) of a state, on the layers built for it:
        the axial force off the loading line when the curvature is stepped (N), the moment
        when the axial strain is (N m)."""
        an = self.an
        an.refine(e0, phi, 0.0)
        n, m, v = an.forces(e0, phi)
        tol = (abs(n) + abs(m) / 1e3 + abs(v)) * 1e-3 + 1.0
        if self.mode == "phi":
            lam = (m - an.m0) / an.dm
            return n - (an.n0 + lam * an.dn), tol, (n, m, v)
        lam = (n - an.n0) / an.dn if an.dn else 0.0
        return (m - (an.m0 + lam * an.dm)) / 1e3, tol / 10.0, (n, m, v)

    def _secant(self, c, x, fresh):
        """The unknown strain (the axial strain when the curvature c is given, the curvature
        in 1/m when the axial strain is) that brings the unbalanced force inside the
        tolerance, from the estimate x. The slope is carried from one stage to the next.
        Returns (x, found)."""
        phi_mode = self.mode == "phi"
        at = (lambda x: self._unbalanced(x, c)) if phi_mode \
            else (lambda x: self._unbalanced(c, x / 1e3))
        d = 1e-5 if phi_mode else 1e-6
        r1 = None
        if fresh or self.slope is None:
            self.slope = None
            r1 = at(x + d)[0]
        r, tol, _ = at(x)
        if self.slope is None and r1 != r:
            self.slope = (r - r1) / d
        if self.slope is None:
            self.slope = 0.0
        cap = self.sec.conc0.e0
        relax = 1.0
        count = 0
        while abs(r) >= tol:
            step = r / (self.slope + 1.0)
            if abs(step) > cap:
                step = math.copysign(0.5 * cap, step)
            x += relax * step
            rn, tol, _ = at(x)
            count += 1
            self.slope = (r - rn) / step
            if abs(x) > 1.0 or abs(c * (1e3 if phi_mode else 1.0)) > 1.0:
                count = 20
            r = rn
            if count == 20 or abs(r) < tol:
                break
            if count > 15:
                # the later tries: half steps, on the section's own stiffness
                relax = 0.5
                h = 1e-7
                e0, phi = (x, c) if phi_mode else (c, x / 1e3)
                fa = self.an.forces(e0 + h, phi) if phi_mode \
                    else self.an.forces(e0, phi + h / 1e3)
                fb = self.an.forces(e0 - h, phi) if phi_mode \
                    else self.an.forces(e0, phi - h / 1e3)
                self.slope = -(fa[0] - fb[0]) / (2 * h) if phi_mode \
                    else -(fa[1] - fb[1]) / 1e3 / (2 * h)
        if count == 20:
            self.slope = None
            return x, False
        return x, True

    def _bisect(self, c):
        """What Response falls back on when the secant gives up under a stepped curvature:
        the axial strain is bracketed in steps of the concrete's strain at peak stress and
        halved until the unbalanced force is inside the tolerance. Returns (e0, found)."""
        an, sec = self.an, self.sec
        step = sec.conc0.e0

        def at(e0):
            r, _tol, (n, m, _v) = self._unbalanced(e0, c)
            return -r, n, m
        target_n = lambda m: an.n0 + (m - an.m0) / an.dm * an.dn
        lo = -step - float(sec.shrinkage(np.array([sec.zc]))[0])
        hi = 0.0
        x = lo
        r0, n, m = at(lo)
        tn = target_n(m)
        found = abs(r0) < ((tn if tn > 1.0 else abs(m) / 1e3) * 1e-3 + 1.0)
        k = -1
        while r0 < 0.0:
            lo -= step
            hi -= step
            x = lo
            r0, n, m = at(lo)
            tn = target_n(m)
            found = found or abs(r0) < ((tn if tn > 1.0 else abs(m) / 1e3) * 1e-3 + 1.0)
            k -= 1
            if k < -12:
                return x, False
        nxt = 0.0
        while not found and -13 < k < 31:
            x = nxt
            r, n, m = at(x)
            if k < 0:
                if r / r0 < 0.0:
                    k = 1
                    nxt = 0.5 * (hi + lo)
                else:
                    k -= 1
                    lo = hi
                    nxt = hi = hi + step
            else:
                if r / r0 >= 0.0:
                    lo = x
                else:
                    hi = x
                k += 1
                nxt = 0.5 * (hi + lo)
            tn = target_n(m)
            found = abs(r) < ((tn if tn > 1.0 else abs(n)) * 1e-3 + 1.0)
        return x, found and -13 < k <= 30

    def _general_own(self, c, x):
        """Response-2000's solve when the axial strain c is stepped [B 004276a0, its step
        004267c0, its stiffness 00427cd0]: the one r2c has for the cases with shear
        (Shear._general), here with no shear strain and in half steps. x is the curvature
        (1/m) it starts from. Returns (x, found)."""
        from r2c.shear import Shear
        if self._helper is None:
            self._helper = Shear(self.an)
            self._helper.mode = self._helper.mode0 = "e0"
        sh = self._helper
        sh.half_steps, sh.step_share = True, 0.5
        _x, info, found = sh._general(c, np.array([x / 1e3, 0.0]))
        return info[1] * 1e3, found

    _helper = None

    # which of Response's own solves are in use (docs/kernel.md, "The stage solve without
    # shear"): under a stepped axial strain (on since 2026-11-25), and under a stepped
    # curvature
    own_axial = True
    own_curvature = True

    def response_solve(self) -> bool:
        return self.own_axial if self.mode == "e0" else self.own_curvature

    def solve(self, c, prev: Stage | None, aside: Stage | None = None,
              fresh: bool = True) -> Stage:
        """The state at control value c (curvature, or strain at the centroid). Where
        Response-2000's own solve is in use: started from the stage before (or from a stage
        set aside beyond c, if that one is nearer) and taken as soon as its unbalanced force
        is inside the tolerance. fresh: the secant's slope is found again and not taken
        from the last solve."""
        if not self.response_solve():
            return self._solve_balanced(c, prev)
        an = self.an
        if self.mode == "e0" and an.dm == 0.0 and an.m0 == 0.0 \
                and (prev is None or abs(prev.phi) * self.sec.h <= 0.02 * abs(prev.e0)):
            # axial load alone on a section that has stayed uniform (the strain differs over
            # the depth by under 2 % of the centroid's; r2c's own figure): r2c
            # stays with the balanced, uniform state. Past the peak Response's solve leaves
            # it; that r2c does not is the owner's override for the circular column
            # (docs/brief.md)
            return self._solve_balanced(c, prev)
        src = prev
        if aside is not None and prev is not None \
                and abs(aside.control - c) < abs(prev.control - c):
            src = aside
        if self.mode == "e0":
            x, ok = self._general_own(c, 0.0 if src is None else src.phi * 1e3)
            if not ok:
                # r2c's own: where that solve finds no state, the balanced state. This is
                # what keeps the uniform response of a column past its peak (the owner's
                # override, docs/brief.md)
                return self._solve_balanced(c, prev)
        else:
            x, ok = self._secant(c, 0.0 if src is None else src.e0, fresh)
            if not ok:
                x, ok = self._bisect(c)
        if not ok:
            raise SolveError(f"no equilibrium at control value {c:g}")
        e0, phi = (x, c) if self.mode == "phi" else (c, x / 1e3)
        an.refine(e0, phi, 0.0)
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
        # A moment above the cracking moment: from the unstrained section the residual
        # cannot be brought down across the fall of force at cracking. Start from cracked
        # planes instead: a strain difference over the depth of 0.25 to 8 mm/m, bending
        # either way, the centroid in a little tension [O: r2c's own; Response's first
        # stage under such a moment is a cracked state, e.g. Newbeam under 50 kNm]
        if self.an.m0 != 0.0:
            for k in (0.25e-3, 0.5e-3, 1e-3, 2e-3, 4e-3, 8e-3):
                for sgn in (1.0, -1.0):
                    yield np.array([0.15 * k, sgn * k / sec.h])

    # -- events ---------------------------------------------------------------------------------
    def _marks(self, st: Stage):
        d = st.detail
        cracked = bool(d.out.cracked.any())
        i = int(np.argmin(d.ex))
        crush = float(d.ex[i]) <= -self.sec.law_at(float(d.z[i])).e0
        # the layers that have ruptured, as the state itself has them
        gone = int(np.isnan(d.fs).sum())
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

    def advance(self, cur: Stage, target: float, depth: int,
                aside: Stage | None = None) -> Stage:
        """Accept a stage at the target, approaching it in geometric steps when something
        happens on the way (first cracking, the extreme fibre reaching its peak strain).
        aside: the stage beyond the target that was set aside for this one."""
        # only a plain next stage is solved on the slope left by the last one [B 00415e30]
        fresh = depth != 0 or aside is not None or len(self.stages) < 2
        trial = self.solve(target, cur, aside=aside, fresh=fresh)
        kind = self.has_event(cur, trial)
        if kind == "rupture" and depth == 0:
            # steel ruptures within the step [B 00415e30, 00419ff0]: the stage is set aside
            # and one a fifth of the way there is tried, and so on while the step is more
            # than 1 % of the way come from the first stage. A stage short of the rupture
            # is kept and the stepping goes on from it; so is the last one tried.
            first = self.stages[0].control
            step = target - cur.control
            while abs(step) >= 1e-10 and abs(step) > 0.01 * abs(trial.control - first):
                step *= 0.2
                try:
                    sub = self.solve(cur.control + step, cur)
                except SolveError:
                    continue
                trial = sub
                if self.has_event(cur, sub) != "rupture":
                    break
            self.accept(trial)
            return trial
        if kind == "crack" or (kind == "crush" and depth < 2):
            # cracking: the stage is set aside and one a fifth of the way to it is tried,
            # again and again, each one that shows the cracking set aside in its turn,
            # while what is left to the nearest stage set aside is more than 2 % of the
            # way come from the first stage [B 00415e30, 00419ff0; O: docs/kernel.md,
            # "Closing in on first cracking"]. The extreme fibre at its peak strain: as
            # before, 14 tries, 3 on a stage that was itself put in between [O]
            for _ in range(100 if kind == "crack" else 14 if depth == 0 else 3):
                t1 = cur.control + 0.2 * (target - cur.control)
                travel = abs(cur.control - self.stages[0].control)
                if kind == "crack" and abs(target - cur.control) < 0.02 * travel:
                    break
                try:
                    sub = self.advance(cur, t1, depth + 1, aside=trial)
                except SolveError:
                    if not self.response_solve():
                        raise
                    # a stage put in between that cannot be solved is dropped, and the
                    # event is closed in on no further [B 00418af0]
                    break
                passed = self.has_event(cur, sub)
                cur = sub
                if passed:
                    break
            if not self.response_solve():
                trial = self.solve(target, cur)
            # else the stage set aside is taken as it was found [B 00415e30]
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
        """Less than a fifth of the peak load is left at a stage, the eleventh or later, at
        which nothing new has happened since the one before [B 00419990]."""
        if len(self.stages) < 11 or not (peak > 0 and st.lam < 0.2 * peak):
            return False
        return self.has_event(self.stages[-2], st) == ""

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
        saved_y = (self.an.epy_z, self.an.epy)
        self.an.ep[:] = self.an.ep0
        self.an.epy = np.zeros(len(self.an.epy))
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
            self.an.epy_z, self.an.epy = saved_y
        newpeak = out.index(stages[peak])
        return out, newpeak
