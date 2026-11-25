"""Chart data in the text layout of Response-2000's "Copy Chart Data", which is what a raw
record holds (docs/raw-format.md): the control charts and the detail views of a load stage.

r2c writes the same charts, titles, axis labels, line structure and number formats, so a reader
of r2x's records reads r2c's unchanged. The numbers are r2c's own.
"""

from __future__ import annotations

import math

import numpy as np

from r2c.solver import Stage
from r2c.units import Units

EOL = "\r\n"


def _num(x: float, dec: int) -> str:
    if x != x or abs(x) > 1e20:       # a ruptured bar, as Response prints it
        return "%.*f" % (dec, 31415926535897932384626433.0)
    return "%.*f" % (dec, x)


def chart(title: str, xt: str, yt: str, lines, dx: int, dy: int = 3) -> bytes:
    """One export. lines: list of (linetype or None, rows) with rows an iterable of (x, y);
    a line type of None is a line continuing the previous style ("New Line" alone)."""
    out = ["  Data from Graph", "  ==============", "", f"  Title\t\t: {title}", "",
           f"  X Axis Title\t: {xt}", f"  Y Axis Title\t: {yt}", "", f"   {xt}\t\t{yt}"]
    first = True
    for lt, rows in lines:
        if not first:
            out.append("New Line")
        if lt is not None:
            out.append(f"Line type : {lt}")
        for x, y in rows:
            out.append(f"   {_num(x, dx)}   \t   {_num(y, dy)}")
        first = False
    return (EOL.join(out) + EOL).encode("latin-1")


# -- control charts ---------------------------------------------------------------------------
def control_keys(incr) -> list[str]:
    """The control charts Response shows for a load increment (N, M, V), as r2x captures
    them: with shear, shear against shear strain and then moment against curvature (M
    increasing), axial load (N increasing, no M) or shear against axial strain; without
    shear, moment against axial strain and against curvature, the first of them replaced by
    axial load against axial strain when N increases with M; axial load alone otherwise."""
    n, m, v = incr
    if v != 0.0:
        if m != 0.0:
            return ["shear_gxy", "moment_phi"]
        if n != 0.0:
            return ["shear_gxy", "axial_ex"]
        return ["shear_gxy", "shear_ex"]
    if m != 0.0 and n != 0.0:
        return ["axial_ex", "moment_phi"]
    if m != 0.0 or n == 0.0:
        return ["moment_ex", "moment_phi"]
    return ["axial_ex"]


def _nz(x: float) -> float:
    """Response prints an exact zero moment or curvature as -0.000."""
    return -0.0 if x == 0.0 else x


def control(key: str, stages: list[Stage], u: Units, gam_avg=None, axis: float = 0.0) -> bytes:
    """A control chart. axis: the height of the moment axis above the centroid; Response's
    axial strain is the strain there (measured: newbeam-axialloc-nm)."""
    ex = [(s.e0 - s.phi * axis) * 1e3 for s in stages]
    if key == "moment_ex":
        return chart("Control : Moment - |e_x", f"Axial Strain ({u.l_strain})", f"Moment ({u.l_moment})",
                     [(0, [(x, _nz(s.m / u.moment)) for x, s in zip(ex, stages)])], 3)
    if key == "moment_phi":
        return chart("Control : Moment - |f", f"Curvature ({u.l_curv})", f"Moment ({u.l_moment})",
                     [(0, [(_nz(s.phi / u.curv), _nz(s.m / u.moment)) for s in stages])], 3)
    if key == "axial_ex":
        return chart("Control : Axial Load - |e_x", f"Axial Strain ({u.l_strain})",
                     f"Axial Load ({u.l_force})",
                     [(0, [(x, s.n / u.force) for x, s in zip(ex, stages)])], 3)
    if key == "shear_gxy":
        return chart("Control : Shear - |g_x_y", f"Shear Strain ({u.l_strain})", f"Shear ({u.l_force})",
                     [(0, [(g * 1e3, s.v / u.force) for g, s in zip(gam_avg, stages)])], 3)
    if key == "shear_ex":
        return chart("Control : Shear - |e_x", f"Axial Strain ({u.l_strain})", f"Shear ({u.l_force})",
                     [(0, [(x, s.v / u.force) for x, s in zip(ex, stages)])], 3)
    raise KeyError(key)


# -- detail views -----------------------------------------------------------------------------
def envelope(st: Stage, before: Stage | None):
    """The grey envelopes behind the transverse and shear strain charts, as Response-2000
    keeps them [B 0041b1d0]: each stage has its own, at its own nodes, made once from the
    envelope of the stage it follows (interpolated to the new heights) and its own profile.
    A stage put in between two others afterwards never enters the later one's envelope.
    Returns {name: (upper, lower)} at st.detail.z."""
    d = st.detail
    z = np.asarray(d.z, dtype=float)
    old = getattr(before, "envelope", None) if before is not None else None
    out = {"z": z}
    for name, own in (("gxy", d.gxy), ("ey", d.ey)):
        own = np.asarray(own, dtype=float)
        if old is None:
            # the first stage: what a node starts from at the two faces, straight between
            # them, and its own profile. A node starts from no shear strain and from its
            # shrinkage or thermal strain across the member [B 004a9d90: a new node's
            # transverse strain is its offset; O: Response's first envelope of
            # newbeam-thermgrad-m is the straight line between the profile's two ends]
            sh = getattr(d, "sh", None)
            if name == "ey" and sh is not None and len(z) > 1 and z[0] != z[-1]:
                base = sh[-1] + (sh[0] - sh[-1]) * (z - z[-1]) / (z[0] - z[-1])
            else:
                base = 0.0
            hi, lo = np.maximum(own, base), np.minimum(own, base)
        else:
            zo = old["z"]
            order = np.argsort(zo)
            inside = (z >= zo[order][0] - 1e-9) & (z <= zo[order][-1] + 1e-9)
            hi = np.where(inside, np.maximum(np.interp(z, zo[order], old[name][0][order]),
                                             own), own)
            lo = np.where(inside, np.minimum(np.interp(z, zo[order], old[name][1][order]),
                                             own), own)
        out[name] = (hi, lo)
    return out


def bond_table(sec, d):
    """Transverse bond over the depth as Response-2000 tabulates it [B 0047fcd0, 00485640]:
    for each half layer the change of the average stirrup stress between its two nodes over
    their distance, times the stirrups' area over their perimeter (taken at the layer's
    bottom node), put at the top of the half layer; nothing where the layer's top or middle
    node has no stirrups. A node has stirrups when it is within their depth [B 004a80e0]
    and is not one with next to no shear strain [B 004a7b60]. Returns (z descending,
    value)."""
    z = np.asarray(d.z, dtype=float)
    fs = np.asarray(d.fsy, dtype=float)

    def k_at(zz):
        num = den = 0.0
        for s in sec.stirrups:
            if s.space > 0 and s.bot - 1e-9 <= zz <= s.top + 1e-9:
                num += s.area
                den += math.pi * s.db * s.legs
        return num / den if den > 0 else 0.0

    lone = getattr(d, "lone", None)
    has = np.array([k_at(zz) > 0 for zz in z])
    if lone is not None:
        has &= ~np.asarray(lone, dtype=bool)
    zt, vt = [], []
    n = (len(z) - 1) // 2
    last = 0.0
    for i in range(n):
        t, m, b = 2 * i, 2 * i + 1, 2 * i + 2
        k = k_at(z[b])
        on = has[t] and has[m]
        up = abs(fs[t] - fs[m]) * k / (z[t] - z[m]) if on and z[t] > z[m] else 0.0
        dn = abs(fs[m] - fs[b]) * k / (z[m] - z[b]) if on and z[m] > z[b] else 0.0
        zt += [z[t], z[m]]
        vt += [up, dn]
        last = dn
    if n:
        zt.append(z[2 * n])
        vt.append(last if has[2 * n] else 0.0)
    return np.array(zt), np.array(vt)


def bond_chart(sec, d):
    """The Transverse Average Bond chart [B 0047fcd0]: the table of bond over the depth,
    averaged over a window at each of 41 evenly spaced heights. Returns (z from the top
    down, value in MPa)."""
    zz = np.linspace(sec.ztop, sec.zbot, 41)
    vals = np.zeros(41)
    # a horizontal tie (pattern 7) shows no bond: with ties alone the chart is zero
    if any(s.pattern != 7 for s in sec.stirrups) and len(d.z) >= 3:
        zt, vt = bond_table(sec, d)
        zt, vt = zt[::-1], vt[::-1]
        for j, zq in enumerate(zz):
            half = 0.5 * bond_window(sec, zq)
            lo_, hi_ = max(zq - half, sec.zbot), min(zq + half, sec.ztop)
            if hi_ - lo_ <= 0:
                continue
            inner = zt[(zt > lo_) & (zt < hi_)]
            zs = np.concatenate([[lo_], inner, [hi_]])
            vals[j] = np.trapezoid(np.interp(zs, zt, vt), zs) / (hi_ - lo_)
    return zz, vals


def bond_window(sec, z):
    """The length Response averages the bond over at a height [B 00484420]: five stirrup
    diameters, at most an eighth of the depth; a twentieth of the depth where there are no
    stirrups."""
    h = sec.ztop - sec.zbot
    num = den = 0.0
    for s in sec.stirrups:
        if s.space > 0 and s.bot - 1e-9 <= z <= s.top + 1e-9:
            num += s.db * s.area
            den += s.area
    if den <= 0:
        return h / 20.0
    return min(5.0 * num / den, h / 8.0)


class Views:
    """Builds the detail-view charts of a stage."""

    def __init__(self, sec, u: Units):
        self.sec = sec
        self.u = u
        self.last = None

    def observe(self, st: Stage):
        """Give the stage its envelope. Stages are observed in order; a stage that does not
        say which stage it followed is taken to follow the one observed before it."""
        if getattr(st, "envelope", None) is None:
            before = getattr(st, "parent", None)
            if before is None or getattr(before, "envelope", None) is None:
                before = self.last
            st.envelope = envelope(st, before)
        self.last = st

    def charts(self, st: Stage, keys) -> dict[str, bytes]:
        sec, u = self.sec, self.u
        d = st.detail
        o = d.out
        y = (d.z - sec.zaxial) / u.length
        ytop, ybot = (sec.ztop - sec.zaxial) / u.length, (sec.zbot - sec.zaxial) / u.length
        depth = f"Beam Depth ({u.l_len})"
        cs, ss, ln = u.conc_stress, u.steel_stress, u.length

        def rows(v):
            return list(zip(np.asarray(v, dtype=float), y))

        def steps(vals):
            out = [(0.0, ytop)]
            order = sorted(range(len(sec.layers)), key=lambda i: sec.layers[i].z)
            for i in order:
                l = sec.layers[i]
                lo = (l.z - l.db / 2 - sec.zaxial) / u.length
                hi = (l.z + l.db / 2 - sec.zaxial) / u.length
                v = vals[i]
                v = 0.0 if (isinstance(v, float) and math.isnan(v)) else v
                out += [(0.0, lo), (v, lo), (v, hi), (0.0, hi)]
            out.append((0.0, ybot))
            return out

        # the strain charts show a node's whole strain: the concrete's own and its shrinkage
        # or thermal strain [B 0046aaa0: the principal strains are stored with the offset]
        sh = getattr(d, "sh", None)
        sh = 0.0 if sh is None else sh
        made = {}
        for key in keys:
            if key == "longitudinal_strain":
                r = [(0.0, ytop)] + rows((d.ex + sh) * 1e3) + [(0.0, ybot)]
                made[key] = chart("Longitudinal Strain", f"|e_x Strain ({u.l_strain})", depth, [(0, r)], 4)
            elif key == "transverse_strain":
                hi, lo = st.envelope["ey"]
                made[key] = chart("Transverse Strain", f"|e_t Strain ({u.l_strain})", depth,
                                  [(4, rows(hi * 1e3)), (None, rows(lo * 1e3)),
                                   (0, rows(d.ey * 1e3))], 3)
            elif key == "shear_strain":
                hi, lo = st.envelope["gxy"]
                made[key] = chart("Shear Strain", f"|g_x_y Strain ({u.l_strain})", depth,
                                  [(4, rows(hi * 1e3)), (4, rows(lo * 1e3)),
                                   (0, rows(d.gxy * 1e3))], 4)
            elif key == "shear_stress":
                lines = [(0, rows(o.v / cs))]
                if d.vcalc is not None:
                    lines.append((2, rows(d.vcalc / cs)))     # from longitudinal equilibrium
                made[key] = chart("Shear Stress", f"Shear Stress ({u.l_conc})", depth, lines, 4)
            elif key == "principal_compressive_stress":
                made[key] = chart("Principal Compressive Stress", f"f_2 Stress ({u.l_conc})",
                                  depth, [(0, rows(o.f2 / cs)), (1, rows(o.f2max / cs))], 3)
            elif key == "shear_on_crack":
                # the value with its sign; its limit on the side of the larger extreme, and
                # on the other side too when that extreme is over a fiftieth of the larger
                # one; no limit while neither passes 0.001 MPa [B 00480590]
                lines = [(0, rows(o.vci / cs))]
                neg, pos = max(0.0, -float(np.min(o.vci))), max(0.0, float(np.max(o.vci)))
                if max(neg, pos) > 1e-3 and neg != pos:
                    if pos > neg or pos > neg / 50.0:
                        lines.append((1, rows(o.vcimax / cs)))
                    if neg > pos or neg > pos / 50.0:
                        lines.append((1, rows(-o.vcimax / cs)))
                made[key] = chart("Shear on Crack", f"|n_c_i shear ({u.l_conc})", depth,
                                  lines, 4)
            elif key == "principal_tensile_stress":
                made[key] = chart("Principal Tensile Stress", f"f_1 Stress ({u.l_conc})", depth,
                                  [(0, rows(o.f1 / cs)), (1, rows(o.f1draw / cs))], 4)
            elif key == "principal_tensile_strain":
                made[key] = chart("Principal Tensile Strain", f"|e_1 Strain ({u.l_strain})", depth,
                                  [(0, rows((o.e1 + sh) * 1e3))], 3)
            elif key == "crack_widths":
                made[key] = chart("Crack Widths", f"Crack Width ({u.l_len})", depth,
                                  [(0, rows(o.w / ln))], 4)
            elif key == "average_angle":
                made[key] = chart("Average Angle", f"|q Angle ({u.l_deg})", depth,
                                  [(0, rows(np.degrees(o.theta)))], 3)
            elif key == "long_crack_spacing":
                made[key] = chart("Long. Crack Spacing", f"Spacing ({u.l_len})", depth,
                                  [(0, rows(d.smx / ln))], 3)
            elif key == "transverse_crack_spacing":
                made[key] = chart("Transverse Crack Spacing", f"s_m_l Spacing ({u.l_len})",
                                  depth, [(0, rows(d.smt / ln))], 3)
            elif key == "diagonal_spacing":
                made[key] = chart("Diagonal Spacing", f"Spacing ({u.l_len})", depth,
                                  [(0, rows(o.sdiag / ln))], 3)
            elif key == "long_reinforcement_stress":
                made[key] = chart("Long. Reinforcement Stress", f"Stress ({u.l_steel})", depth,
                                  [(0, steps(d.fs / ss))], 3)
            elif key == "long_reinf_stress_at_crack":
                made[key] = chart("Long. Reinf Stress at Crack", f"f_s_c_r_a_c_k ({u.l_crack_steel})",
                                  depth, [(0, steps(d.fscr / ss))], 3)
            elif key == "long_average_bond":
                bond = getattr(d, "bond", None)
                vals = np.zeros(len(sec.layers)) if bond is None else bond / cs
                made[key] = chart("Long. Average Bond", f"Bond Stress ({u.l_conc})", depth,
                                  [(0, steps(vals))], 3)
            elif key == "stirrup_stress":
                made[key] = chart("Stirrup Stress", f"Stress ({u.l_steel})", depth,
                                  [(0, rows(d.fsy / ss))], 3)
            elif key == "stirrup_stress_at_crack":
                made[key] = chart("Stirrup Stress at Crack", f"Stress ({u.l_steel})", depth,
                                  [(0, rows(d.fsycr / ss))], 3)
            elif key == "transverse_average_bond":
                # the table of bond over the depth, averaged over a window at each of 41
                # heights [B 0047fcd0]
                zz, vals = bond_chart(sec, d)
                yy = (zz - sec.zaxial) / u.length
                vals = vals / cs
                made[key] = chart("Transverse Average Bond", f"Bond stress ({u.l_conc})", depth,
                                  [(0, list(zip(vals, yy)))], 4)
            elif key == "shrinkage_thermal_strain":
                yy = np.linspace(ybot, ytop, 101)
                sh = sec.shrinkage(yy * u.length + sec.zaxial) * 1e3
                r = [(0.0, ybot)] + list(zip(sh, yy)) + [(0.0, ytop)]
                made[key] = chart("Shrinkage & Thermal Strain", f"strain ({u.l_strain})", depth,
                                  [(0, r), (4, steps([l.thermal * 1e3 for l in sec.layers]))], 3)
            elif key == "longitudinal_concrete_stress":
                made[key] = chart("Longitudinal Concrete Stress", f"Stress ({u.l_conc})", depth,
                                  [(0, rows(o.fcx / cs))], 3)
            else:
                raise KeyError(key)
        return made
