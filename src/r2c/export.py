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
    n, m, v = incr
    if v != 0.0:
        if m != 0.0:
            return ["shear_gxy", "moment_phi"]
        if n != 0.0:
            return ["shear_gxy", "axial_ex"]
        return ["shear_gxy", "shear_ex"]
    if m != 0.0 or n == 0.0:
        return ["moment_ex", "moment_phi"]
    return ["axial_ex"]


def _nz(x: float) -> float:
    """Response prints an exact zero moment or curvature as -0.000."""
    return -0.0 if x == 0.0 else x


def control(key: str, stages: list[Stage], u: Units, gam_avg=None) -> bytes:
    ex = [s.e0 * 1e3 for s in stages]
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
class Envelope:
    """Largest and smallest value of a depth profile over the stages so far (the grey
    envelopes Response draws behind the transverse and shear strain charts)."""

    def __init__(self, zlo: float, zhi: float, n: int = 401):
        self.z = np.linspace(zlo, zhi, n)
        self.hi = np.zeros(n)
        self.lo = np.zeros(n)

    def update(self, z, val):
        order = np.argsort(z)
        v = np.interp(self.z, np.asarray(z)[order], np.asarray(val)[order])
        self.hi = np.maximum(self.hi, v)
        self.lo = np.minimum(self.lo, v)

    def at(self, z, val):
        hi = np.maximum(np.interp(z, self.z, self.hi), val)
        lo = np.minimum(np.interp(z, self.z, self.lo), val)
        return hi, lo


class Views:
    """Builds the detail-view charts of a stage."""

    def __init__(self, sec, u: Units):
        self.sec = sec
        self.u = u
        self.env_t = Envelope(sec.zbot, sec.ztop)
        self.env_g = Envelope(sec.zbot, sec.ztop)

    def observe(self, st: Stage):
        d = st.detail
        self.env_t.update(d.z, d.ey)
        self.env_g.update(d.z, d.gxy)

    def charts(self, st: Stage, keys) -> dict[str, bytes]:
        sec, u = self.sec, self.u
        d = st.detail
        o = d.out
        y = (d.z - sec.zc) / u.length
        ytop, ybot = (sec.ztop - sec.zc) / u.length, (sec.zbot - sec.zc) / u.length
        depth = f"Beam Depth ({u.l_len})"
        cs, ss, ln = u.conc_stress, u.steel_stress, u.length

        def rows(v):
            return list(zip(np.asarray(v, dtype=float), y))

        def steps(vals):
            out = [(0.0, ytop)]
            order = sorted(range(len(sec.layers)), key=lambda i: sec.layers[i].z)
            for i in order:
                l = sec.layers[i]
                lo = (l.z - l.db / 2 - sec.zc) / u.length
                hi = (l.z + l.db / 2 - sec.zc) / u.length
                v = vals[i]
                v = 0.0 if (isinstance(v, float) and math.isnan(v)) else v
                out += [(0.0, lo), (v, lo), (v, hi), (0.0, hi)]
            out.append((0.0, ybot))
            return out

        made = {}
        for key in keys:
            if key == "longitudinal_strain":
                r = [(0.0, ytop)] + rows(d.ex * 1e3) + [(0.0, ybot)]
                made[key] = chart("Longitudinal Strain", f"|e_x Strain ({u.l_strain})", depth, [(0, r)], 4)
            elif key == "transverse_strain":
                hi, lo = self.env_t.at(d.z, d.ey)
                made[key] = chart("Transverse Strain", f"|e_t Strain ({u.l_strain})", depth,
                                  [(4, rows(hi * 1e3)), (None, rows(lo * 1e3)),
                                   (0, rows(d.ey * 1e3))], 3)
            elif key == "shear_strain":
                hi, lo = self.env_g.at(d.z, d.gxy)
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
                lines = [(0, rows(np.abs(o.vci) / cs))]
                if d.vcalc is not None:
                    # with shear Response adds the limit, on both sides of zero
                    lines += [(1, rows(o.vcimax / cs)), (1, rows(-o.vcimax / cs))]
                made[key] = chart("Shear on Crack", f"|n_c_i shear ({u.l_conc})", depth,
                                  lines, 4)
            elif key == "principal_tensile_stress":
                made[key] = chart("Principal Tensile Stress", f"f_1 Stress ({u.l_conc})", depth,
                                  [(0, rows(o.f1 / cs)), (1, rows(o.f1lim / cs))], 4)
            elif key == "principal_tensile_strain":
                made[key] = chart("Principal Tensile Strain", f"|e_1 Strain ({u.l_strain})", depth,
                                  [(0, rows(o.e1 * 1e3))], 3)
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
                yy = np.linspace(ytop, ybot, 41)
                tb = getattr(d, "tbond", None)
                vals = np.zeros(41) if tb is None else np.interp(
                    -yy, -y, np.asarray(tb, dtype=float)) / cs
                made[key] = chart("Transverse Average Bond", f"Bond stress ({u.l_conc})", depth,
                                  [(0, list(zip(vals, yy)))], 4)
            elif key == "shrinkage_thermal_strain":
                yy = np.linspace(ybot, ytop, 101)
                r = [(0.0, ybot)] + [(0.0, v) for v in yy] + [(0.0, ytop)]
                made[key] = chart("Shrinkage & Thermal Strain", f"strain ({u.l_strain})", depth,
                                  [(0, r), (4, steps(np.zeros(len(sec.layers))))], 3)
            elif key == "longitudinal_concrete_stress":
                made[key] = chart("Longitudinal Concrete Stress", f"Stress ({u.l_conc})", depth,
                                  [(0, rows(o.fcx / cs))], 3)
            else:
                raise KeyError(key)
        return made
