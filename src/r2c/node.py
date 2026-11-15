"""The biaxial node: concrete stresses at one depth from (ex, ey, gxy), by the Modified
Compression Field Theory with its crack check (thesis chapters 3 and 4, Tables 4-1).

Vectorised: every argument is an array with one entry per node, all of one concrete type.
Angles are measured as Response does: theta = 90 degrees when the principal tension is along
the member (flexural cracks), smaller as the cracks lean over in shear.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from r2c.materials import TS_BENTZ, ConcreteLaw

TMAX = 1e6
BIG = 1e9


@dataclass
class NodeOut:
    fcx: np.ndarray
    fcy: np.ndarray
    v: np.ndarray
    f1: np.ndarray
    f2: np.ndarray
    f2max: np.ndarray
    e1: np.ndarray
    e2: np.ndarray
    theta: np.ndarray
    w: np.ndarray
    sdiag: np.ndarray
    vci: np.ndarray
    vcimax: np.ndarray
    f1lim: np.ndarray
    cracked: np.ndarray
    f1crack: np.ndarray      # f1 + vci / tan(theta): the demand on the x steel at a crack
    tan: np.ndarray
    floor: np.ndarray


def evaluate(law: ConcreteLaw, ex, ey, gxy, m, ft_eff, smx, smy, f1cx, f1cy) -> NodeOut:
    ex = np.asarray(ex, dtype=float)
    ey = np.broadcast_to(np.asarray(ey, dtype=float), ex.shape)
    gxy = np.broadcast_to(np.asarray(gxy, dtype=float), ex.shape)
    phi = law.phi
    ang = np.arctan2(gxy, ex - ey)
    theta = np.pi / 2 - 0.5 * ang
    t = np.tan(theta)
    big = np.abs(t) > TMAX
    t = np.where(big, np.sign(t) * TMAX, t)
    small = np.abs(t) < 1e-6
    t = np.where(small, np.where(t < 0, -1e-6, 1e-6), t)
    s = np.sin(theta)
    c = np.cos(theta)
    s2 = s * s
    c2 = 1.0 - s2
    rad = np.sqrt((ex - ey) ** 2 + gxy ** 2)
    avg = 0.5 * (ex + ey)
    e1 = avg + 0.5 * rad
    e2 = avg - 0.5 * rad

    f1, _ = law.stress(e1, e2, ft_eff, m)
    f2, f2max = law.stress(e2, e1, ft_eff, m)

    ecr = law.crack_strain(ft_eff)
    f1lim = np.maximum(law.ft, ft_eff) * phi
    cracked = e1 > ecr
    w = np.zeros_like(ex)
    sdiag = np.zeros_like(ex)
    vcimax = np.zeros_like(ex)
    vci = np.zeros_like(ex)
    floor = np.zeros_like(ex)
    if cracked.any():
        k = cracked
        tk, sk, ck, s2k, c2k = t[k], s[k], c[k], s2[k], c2[k]
        sd = 1.0 / (np.abs(ck) / smy[k] + np.abs(sk) / smx[k])
        wk = (e1[k] - ecr[k]) * sd
        agg = 0.31 + 24.0 * wk / (law.agg + 16.0)
        vmax = 0.18 * np.sqrt(law.fcp) / agg * phi
        fl = law.Ec * ecr[k] / (1.0 + 250.0 * wk) * phi
        fk = f1[k].copy()
        cx, cy = f1cx[k], f1cy[k]
        lim = f1lim[k]
        if law.t_stiff == TS_BENTZ:
            # a lower bound on the average tension of cracked concrete far from bars, carried
            # by aggregate interlock
            q = 0.25 * law.ft / agg * phi
            a = np.minimum(np.abs(q / tk), lim) * law.tsfactor
            b = 0.85 * law.ft * phi * np.abs(tk) + cy + fl
            lb = np.minimum(0.5 * cx, np.minimum(b, a) * law.tsfactor)
            fk = np.maximum(fk, lb)
        f1b = cx * s2k + cy * c2k
        d = np.abs(cx - cy) * sk * ck
        sg = np.sign(d)
        vv = np.minimum(np.abs(d), vmax)
        f1c = sg * vv / tk + cx
        f1d = np.where(np.abs(tk) >= TMAX, 2.0 * fk, vv * sg * tk + cy)
        fk = np.minimum(np.minimum(fk, f1b), np.minimum(f1c, f1d))
        lim = np.minimum(lim, f1b)
        low = fk < fl
        fk = np.where(low, fl, fk)
        lim = np.where(low, np.maximum(lim, fl), lim)
        # shear on the crack, from equilibrium at the crack
        dem = fk - fl
        g = gxy[k]
        vx = (cx - dem) * tk
        vy = (dem - cy) / tk
        vk = np.where(cx <= cy, vx, vy)
        # keep only the sense that goes with the applied shear
        bad = np.where(cx <= cy, ((g > 0) & (vk > 0)) | ((g < 0) & (vk < 0)),
                       ((g > 0) & (vk < 0)) | ((g < 0) & (vk > 0)))
        vk = np.where(bad, 0.0, vk)
        edge = (np.abs(tk) <= 1e-6) | (np.abs(tk) >= TMAX)
        vk = np.where(edge, 0.0, vk)
        over = np.abs(d) > vmax
        lim = np.where(over, np.minimum(lim, np.minimum(f1c, np.where(np.abs(tk) >= TMAX, BIG,
                                                                       vv * sg * tk + cy))), lim)
        lim = np.maximum(lim, fl)
        f1[k] = fk
        f1lim[k] = lim
        w[k] = wk
        sdiag[k] = sd
        vcimax[k] = vmax
        vci[k] = vk
        floor[k] = fl
    v = (f1 - f2) / (1.0 / t + t)
    fcx = f1 - v / t
    fcy = f1 - v * t
    f1crack = np.abs(vci) / t + f1
    return NodeOut(fcx, fcy, v, f1, f2, f2max, e1, e2, theta, w, sdiag, vci, vcimax, f1lim,
                   cracked, f1crack, t, floor)
