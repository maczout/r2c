#!/usr/bin/env python3
"""Diagnostics that separate r2c's kernel from its stepping and its iteration, by putting
r2c in Response's own states. They did most of the work of the first build (2026-11-15) and
were lost with that session's workspace; these are rebuilt from the description in
docs/status.md.

    python tools/diagnose.py states   RECORD [--input FILE] [--stages 5,10,peak] [--views]
                                      [--out RECORD]
    python tools/diagnose.py controls RECORD [--input FILE] [--upto N]
    python tools/diagnose.py flow     RECORD [--input FILE] [--from N] [--upto N]
    python tools/diagnose.py own      RECORD [--input FILE] [--from N]
                                      [--fit-layer I --at Y]

RECORD is an r2x-raw record captured from Response-2000 (a fixture in tests/oracle, or a
capture of every stage from the archive). --input is the section file the record was made
from; it is not needed for Response's built-in Newbeam ("input.r2t", "File > New").

states    At each detail stage of RECORD: read Response's strain state from its charts (strain
          at the centroid and curvature from the Longitudinal Strain view, the shear strain
          profile from the Shear Strain view), evaluate r2c's section forces there, and compare
          them with Response's loads. With --views, also compare every detail view, as
          tools/compare.py does at the peak. This tests the kernel alone: no stepping, no
          equilibrium iteration, and no profile iteration.

          History: when RECORD holds every stage from 0 up to the one asked for, the stages
          before it are evaluated in turn and committed as r2c commits an accepted stage
          (plastic strain of bars and stirrups), so unloading is represented. With a fixture
          (control charts and the peak only) each stage is evaluated from a virgin state;
          that is exact only while nothing has unloaded, which is the case up to the peak in
          monotonic loading.

controls  Solve r2c at Response's own sequence of control values (curvature; strain at the
          centroid with an axial load increment; shear strain with shear alone), carrying the
          history forward stage by stage, and compare the loads. This tests the solve and the
          profile iteration, separated from r2c's choice of steps.

flow      At each stage of RECORD (a capture of every stage), in Response's own strain state
          with the history carried: how far r2c's calculated shear stress (the longitudinal
          stiffness method) is from the shear stress of the state, as a share of the shear
          force, next to the same measure for the two lines of Response's own Shear Stress
          chart. Where Response's is small and r2c's is not, r2c's stiffness rules differ
          from Response's at that state: the profile iteration cannot then settle on
          Response's state, however it iterates. This is what found the stiffness of a bar
          on its yield plateau (docs/kernel.md).

          With --fit-layer I --at Y: also the tangent stiffness of steel layer I (0 is the
          first in the section) that makes r2c's calculated shear stress at height Y (above
          the centroid, in the record's length unit; pick a point just inside the layer)
          equal Response's.

All print a table; --json writes the numbers. No pass or fail is decided here.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
import verify  # noqa: E402
from r2c import export, record, run  # noqa: E402
from r2c.solver import SolveError, Stage  # noqa: E402

LOADS = {"moment_phi": "m", "moment_ex": "m", "axial_ex": "n", "shear_gxy": "v",
         "shear_ex": "v"}
# bond stresses come from the change between stages in the shear driver: not at a lone state
NOT_HERE = {"long_average_bond", "transverse_average_bond"}


def _setup(ref, input_path):
    opt = verify.options(ref.header)
    opt.pop("more_detail")
    src = ref.header["input-name"]
    path = None
    if src.lower() not in verify.BUILT_IN:
        if input_path is None:
            raise SystemExit(f"--input is needed: the record was made from {src}")
        path = Path(input_path)
    return run.setup(path, **opt)


def _bottom_key(ref):
    keys = cmp.control_keys(ref)
    return keys[-1]


def oracle_loads(ref, su, stage: int) -> dict[str, float]:
    """Response's loads (N, M, V) at a stage, in the units in effect, from the control
    charts and the loading: the charts give the load that is stepped, the loading gives the
    rest."""
    n0, m0, v0 = su.initial
    dn, dm, dv = su.increment
    out = {}
    for key in cmp.control_keys(ref):
        c = cmp._curve(ref, key)
        if stage < len(c):
            out[LOADS[key]] = float(c[stage, 1])
    # the load factor from the stepped load, then the other two loads from it
    lam = None
    for comp, base, inc in (("m", m0, dm), ("v", v0, dv), ("n", n0, dn)):
        if inc != 0.0 and comp in out:
            lam = (out[comp] - base) / inc
            break
    if lam is not None:
        for comp, base, inc in (("n", n0, dn), ("m", m0, dm), ("v", v0, dv)):
            out.setdefault(comp, base + lam * inc)
    return out


def _depth_profile(ref, stage, key, line):
    """(z internal, value) of one line of a depth chart, top first, without the zero end
    points the strain chart adds."""
    _t, _x, _y, lines = cmp.parse_chart(ref.stage(stage, key))
    # "New Line" followed by "Line type" parses as an empty line between the two: skip those
    return [ln for ln in lines if len(ln)][line]


def strain_state(ref, su, stage: int):
    """Response's (e0, phi, gxy profile) at a stage, from its detail views. Internal units:
    plain strains, 1/mm, mm."""
    sec, u = su.section, su.units
    a = _depth_profile(ref, stage, "longitudinal_strain", 0)
    a = a[1:-1]                                 # drop the (0, top) and (0, bottom) ends
    ex = a[:, 0] * 1e-3
    y = a[:, 1] * u.length                      # height above the centroid
    phi, e0 = np.polyfit(-y, ex, 1)             # ex = e0 - phi * y
    resid = float(np.max(np.abs(ex - (e0 - phi * y)))) if len(ex) else 0.0
    prof = None
    if su.analysis.shear:
        try:
            g = _depth_profile(ref, stage, "shear_strain", -1)  # the stage's own line (last)
        except (KeyError, IndexError):
            g = None
        if g is not None and len(g):
            z = g[:, 1] * u.length + sec.zc
            order = np.argsort(z)
            zz, iu = np.unique(z[order], return_index=True)
            prof = (zz, (g[:, 0] * 1e-3)[order][iu])
    return float(e0), float(phi), prof, resid


def evaluate(su, e0, phi, prof):
    """r2c's forces and detail at a strain state, on r2c's own layering. With shear, the
    shear strain profile is set to the one given."""
    an = su.analysis
    gam = 0.0
    if prof is not None:
        an.shape_z, an.shape = prof[0].copy(), prof[1].copy()
        gam = 1.0                               # the profile carries the magnitude
    an.coarsen()
    for _ in range(6):
        if not an.refine(e0, phi, gam):
            break
    n, m, v = an.forces(e0, phi, gam)
    det = an.detail(e0, phi, gam)
    st = Stage(e0, phi, gam, 0.0, n, m, v, det)
    if prof is not None:
        from r2c.shear import Shear
        from r2c.solver import SolveError
        try:
            z, _vs, tau, _t, _d = Shear(an).shear_flow(e0, phi, gam, v)
        except SolveError:
            # no stiffness left in this state: no calculated profile
            det.vcalc = np.zeros(len(det.z))
        else:
            zf = z.ravel()[::-1]
            zz, ii = np.unique(zf, return_index=True)
            det.vcalc = np.interp(det.z, zz, tau.ravel()[::-1][ii])
    return st


def _pct(a, b, scale):
    return 100.0 * (a - b) / scale if scale else 0.0


def cmd_states(a) -> int:
    ref = record.read(a.record)
    su = _setup(ref, a.input)
    u = su.units
    have = ref.stages()
    peak = int(ref.header.get("peak-stage", "0"))
    if a.stages:
        want = [peak if s == "peak" else int(s) for s in a.stages.split(",")]
    else:
        want = list(have)
    missing = [s for s in want if s not in have]
    if missing:
        raise SystemExit(f"stages not in the record: {missing} (it has {have})")
    contiguous = have == list(range(len(have)))
    print(f"history: {'carried (every stage from 0)' if contiguous else 'none (virgin state at each stage)'}")
    # the scale for load differences: Response's largest load on each chart
    scale = {}
    for key in cmp.control_keys(ref):
        c = cmp._curve(ref, key)
        scale[LOADS[key]] = float(np.max(np.abs(c[:, 1]))) if len(c) else 0.0
    views = export.Views(su.section, u)
    order = sorted(set(want)) if not contiguous else list(range(max(want) + 1))
    rows = []
    kept = []                                   # r2c's views in Response's states (--out)
    for s in order:
        e0, phi, prof, resid = strain_state(ref, su, s)
        st = evaluate(su, e0, phi, prof)
        views.observe(st)
        if contiguous and s > 0:
            su.analysis.commit(st.e0, st.phi)
            if prof is not None:
                su.analysis.commit_stirrups(st.detail)
        if s not in want:
            continue
        ora = oracle_loads(ref, su, s)
        mine = {"n": st.n / u.force, "m": st.m / u.moment, "v": st.v / u.force}
        row = {"stage": s, "e0": e0, "phi": phi, "fit_resid": resid,
               "oracle": ora, "r2c": mine,
               # a load with a control chart: relative to Response's largest on it; a load
               # held constant (no chart): the plain difference, in the units in effect
               "diff_pct": {k: _pct(mine[k], ora[k], scale[k]) for k in ora if scale.get(k)},
               "diff_abs": {k: mine[k] - ora[k] for k in ora if not scale.get(k)}}
        if a.views:
            made = views.charts(st, [k.split("/", 2)[2] for k in ref.sections
                                     if k.startswith(f"stage/{s}/")])
            sub = record.decode(record.encode(
                dict(ref.header), [(record.stage_section(s, k), b) for k, b in made.items()]))
            row["views"] = cmp.compare_views(ref, sub, s, s)
            kept.extend((record.stage_section(s, k), b) for k, b in made.items())
            for v in row["views"]:
                if v["view"] in NOT_HERE:
                    v["not_computed"] = True
        rows.append(row)
    print(f"{'stage':>5} {'e0 (mm/m)':>10} {'phi (1/mm)':>11}   "
          + "   ".join(f"{k.upper():>2}: Response, r2c, diff   " for k in ("n", "m", "v")))
    for r in rows:
        cells = []
        for k in ("n", "m", "v"):
            if k in r["oracle"]:
                d = (f"{r['diff_pct'][k]:+7.2f}%" if k in r["diff_pct"]
                     else f"{r['diff_abs'][k]:+7.2f} ")
                cells.append(f"{r['oracle'][k]:10.2f} {r['r2c'][k]:10.2f} {d}")
            else:
                cells.append(" " * 29)
        print(f"{r['stage']:>5} {r['e0'] * 1e3:10.4f} {r['phi']:11.4e}   " + "   ".join(cells))
        if a.views:
            for v in r["views"]:
                if v.get("not_computed"):
                    print(f"        {v['view']:32s} not computed here (needs the driver)")
                elif v.get("missing"):
                    print(f"        {v['view']:32s} missing")
                else:
                    print(f"        {v['view']:32s} {v['max_diff_pct']:7.2f} %")
    print("diff: in % of Response's largest value on the load's control chart; for a load "
          "held constant (no chart), the plain difference in the units in effect.")
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=1))
    if a.out:
        # the control charts are Response's own, so that tools/viewlines.py finds the stages
        ctl = [(k, b) for k, b in ref.sections.items() if not k.startswith("stage/")]
        Path(a.out).write_bytes(record.encode(dict(ref.header), ctl + kept))
    return 0


def control_value(ref, su, driver, stage: int) -> float:
    """Response's control value at a stage, in r2c's internal form for the driver's mode."""
    u = su.units
    if driver.mode == "phi":
        return float(cmp._curve(ref, "moment_phi")[stage, 0]) * u.curv
    if driver.mode == "e0":
        key = "axial_ex" if "axial_ex" in cmp.control_keys(ref) else "moment_ex"
        return float(cmp._curve(ref, key)[stage, 0]) * 1e-3
    return float(cmp._curve(ref, "shear_gxy")[stage, 0]) * 1e-3


def cmd_controls(a) -> int:
    ref = record.read(a.record)
    su = _setup(ref, a.input)
    u = su.units
    drv = su.driver()
    if drv.mode == "none":
        raise SystemExit("no load increment: nothing to step")
    count = int(ref.header["stage-count"])
    last = count - 1 if a.upto is None else min(a.upto, count - 1)
    key = _bottom_key(ref)
    comp = LOADS[key]
    ref_curve = cmp._curve(ref, key)
    scale = float(np.max(np.abs(ref_curve[:, 1])))
    unit = u.moment if comp == "m" else u.force
    cur = drv.initial()
    drv.accept(cur)
    rows = [{"stage": 0, "control": cur.control, "oracle": float(ref_curve[0, 1]),
             "r2c": getattr(cur, comp) / unit}]
    for s in range(1, last + 1):
        c = control_value(ref, su, drv, s)
        try:
            st = drv.solve(c, cur)
        except SolveError as e:
            rows.append({"stage": s, "control": c, "oracle": float(ref_curve[s, 1]),
                         "r2c": None, "note": str(e)})
            continue
        drv.accept(st)
        cur = st
        rows.append({"stage": s, "control": c, "oracle": float(ref_curve[s, 1]),
                     "r2c": getattr(st, comp) / unit,
                     "profile_err": getattr(st, "perr", None)})
    print(f"chart {key}: load {comp.upper()}, diff relative to Response's largest load "
          f"({scale:.2f})")
    print(f"{'stage':>5} {'control':>12} {'Response':>10} {'r2c':>10} {'diff %':>8}")
    for r in rows:
        if r["r2c"] is None:
            print(f"{r['stage']:>5} {r['control']:12.5e} {r['oracle']:10.2f} {'—':>10} "
                  f"{'':>8}  no state: {r['note']}")
            continue
        r["diff_pct"] = _pct(r["r2c"], r["oracle"], scale)
        print(f"{r['stage']:>5} {r['control']:12.5e} {r['oracle']:10.2f} {r['r2c']:10.2f} "
              f"{r['diff_pct']:+8.2f}")
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=1))
    return 0


def _mismatch(z, v, tau, b=None) -> float:
    """The shear force that the difference of two shear stress profiles amounts to, relative
    to the shear force of the first."""
    order = np.argsort(z)
    z, v, tau = z[order], v[order], tau[order]
    b = np.ones_like(z) if b is None else b[order]
    tot = float(np.trapezoid(np.abs(v) * b, z))
    return float(np.trapezoid(np.abs(tau - v) * b, z)) / tot if tot > 1e-12 else 0.0


def _calculated(su, st):
    """r2c's calculated shear stress at the detail's nodes, for the state of st."""
    from r2c.shear import Shear
    drv = Shear(su.analysis)
    drv.bar_stiffness = dict(getattr(su, "bar_stiffness", {}))
    z, _vs, tau, _t, _d = drv.shear_flow(st.e0, st.phi, st.gam, st.v)
    zf = z.ravel()[::-1]
    zz, ii = np.unique(zf, return_index=True)
    return np.interp(st.detail.z, zz, tau.ravel()[::-1][ii])


def cmd_own(a) -> int:
    """r2c's own solve of the record's case, stage by stage: what it stepped in, the state,
    the loads, and how far the calculated shear stress was from the state's when the stage
    was accepted (1 % is converged; more is a closest iterate)."""
    ref = record.decode(Path(a.record).read_bytes())
    su = _setup(ref, a.input)
    u = su.units
    stages = su.driver().run(run.MAX_STAGES)
    print(f"{'stage':>5} {'by':>4} {'e0 mm/m':>9} {'phi rad/km':>11} {'gxy mm/m':>9} "
          f"{'N':>9} {'M':>9} {'V':>9} {'profile %':>9}")
    for i, st in enumerate(stages):
        if i < a.first:
            continue
        perr = getattr(st, "perr", None)
        print(f"{i:>5} {getattr(st, 'cmode', '') or '':>4} {st.e0 * 1e3:9.4f} "
              f"{st.phi * 1e6:11.3f} {getattr(st, 'gam_avg', st.gam) * 1e3:9.4f} "
              f"{st.n / u.force:9.2f} {st.m / u.moment:9.2f} {st.v / u.force:9.2f} "
              + (f"{100 * perr:9.2f}" if perr is not None else f"{'':>9}"))
    return 0


def cmd_flow(a) -> int:
    ref = record.read(a.record)
    su = _setup(ref, a.input)
    if not su.analysis.shear:
        raise SystemExit("no shear in this record")
    have = ref.stages()
    if have != list(range(len(have))):
        raise SystemExit("flow needs a capture of every stage (the archive, not a fixture)")
    u, sec, an = su.units, su.section, su.analysis
    last = len(have) - 1 if a.upto is None else min(a.upto, len(have) - 1)
    fit = a.fit_layer is not None
    if fit and a.at is None:
        raise SystemExit("--fit-layer needs --at")
    rows = []
    for s in range(last + 1):
        e0, phi, prof, _resid = strain_state(ref, su, s)
        st = evaluate(su, e0, phi, prof)
        d = st.detail
        if s >= a.first and prof is not None:
            z = np.asarray(d.z, dtype=float)
            row = {"stage": s, "v_oracle": oracle_loads(ref, su, s).get("v"),
                   "v_r2c": st.v / u.force,
                   "r2c": _mismatch(z, np.asarray(d.out.v), np.asarray(d.vcalc),
                                    np.asarray(d.b))}
            lines = [ln for ln in cmp.parse_chart(ref.stage(s, "shear_stress"))[3] if len(ln)]
            if a.profile == s and len(lines) >= 2:
                # over the depth: Response's two lines, r2c's calculated stress, and what
                # governs the principal tension at r2c's nodes
                yy = (z - sec.zc) / u.length
                o0, o1 = (np.argsort(ln[:, 1]) for ln in lines[:2])
                print(f"stage {s}: {'y':>8} {'Resp. state':>12} {'Resp. calc':>11} "
                      f"{'r2c calc':>9} {'gov':>4} {'fsy':>7}")
                for i in np.argsort(-yy):
                    print(f"          {yy[i]:8.1f} "
                          f"{np.interp(yy[i], lines[0][:, 1][o0], lines[0][:, 0][o0]):12.3f} "
                          f"{np.interp(yy[i], lines[1][:, 1][o1], lines[1][:, 0][o1]):11.3f} "
                          f"{d.vcalc[i] / u.conc_stress:9.3f} {int(d.out.gov[i]):4d} "
                          f"{float(np.asarray(d.fsy)[i]):7.1f}")
            if len(lines) >= 2:
                y = lines[0][:, 1]
                o = np.argsort(lines[1][:, 1])
                other = np.interp(y, lines[1][:, 1][o], lines[1][:, 0][o])
                row["oracle"] = _mismatch(y, lines[0][:, 0], other)
            if fit and lines:
                o = np.argsort(lines[0][:, 1])
                target = float(np.interp(a.at, lines[0][:, 1][o], lines[0][:, 0][o]))
                zq = a.at * u.length + sec.zc
                order = np.argsort(z)

                def at(k):
                    su.bar_stiffness = {a.fit_layer: k}
                    vc = _calculated(su, st)
                    su.bar_stiffness = {}
                    return float(np.interp(zq, z[order], vc[order])), vc
                lo_k, hi_k = 0.0, 2.0 * sec.layers[a.fit_layer].steel.E
                for _ in range(40):
                    mid = 0.5 * (lo_k + hi_k)
                    if abs(at(mid)[0]) < abs(target) * u.conc_stress:
                        lo_k = mid
                    else:
                        hi_k = mid
                _tq, vc = at(mid)
                lay = sec.layers[a.fit_layer]
                row["fit_k"] = mid
                row["fit_mismatch"] = _mismatch(z, np.asarray(d.out.v), vc, np.asarray(d.b))
                row["layer_strain"] = e0 - phi * (lay.z - sec.zc) + lay.prestrain
            rows.append(row)
        if s > 0:
            an.commit(st.e0, st.phi)
            if prof is not None:
                an.commit_stirrups(d)
    head = f"{'stage':>5} {'V Resp.':>9} {'V r2c':>9} {'r2c %':>7} {'Resp. %':>8}"
    if fit:
        head += f" {'strain mm/m':>12} {'fitted k MPa':>13} {'r2c % with k':>13}"
    print(head)
    for r in rows:
        line = (f"{r['stage']:>5} {r['v_oracle'] if r['v_oracle'] is not None else 0.0:9.2f} "
                f"{r['v_r2c']:9.2f} {100 * r['r2c']:7.1f} "
                + (f"{100 * r['oracle']:8.1f}" if "oracle" in r else f"{'':>8}"))
        if fit:
            line += (f" {r['layer_strain'] * 1e3:12.3f} {r['fit_k']:13.0f} "
                     f"{100 * r['fit_mismatch']:13.1f}")
        print(line)
    print("%: the shear force that the difference between the calculated shear stress and "
          "the state's amounts to, relative to the shear force.")
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=1))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("states", help="r2c's forces at Response's strain states")
    p.add_argument("record")
    p.add_argument("--input")
    p.add_argument("--stages", help="stage numbers or peak, comma separated (default: all "
                   "detail stages in the record)")
    p.add_argument("--views", action="store_true", help="also compare the detail views")
    p.add_argument("--json")
    p.add_argument("--out", help="with --views: write r2c's views in Response's states as "
                                 "a record (for tools/viewlines.py)")
    p.set_defaults(fn=cmd_states)
    p = sub.add_parser("controls", help="r2c solved at Response's control values")
    p.add_argument("record")
    p.add_argument("--input")
    p.add_argument("--upto", type=int, help="last stage to solve (default: all)")
    p.add_argument("--json")
    p.set_defaults(fn=cmd_controls)
    p = sub.add_parser("own", help="r2c's own stages for the record's case")
    p.add_argument("record")
    p.add_argument("--input")
    p.add_argument("--from", dest="first", type=int, default=0, help="first stage to print")
    p.set_defaults(fn=cmd_own)
    p = sub.add_parser("flow", help="r2c's calculated shear stress at Response's states")
    p.add_argument("record")
    p.add_argument("--input")
    p.add_argument("--from", dest="first", type=int, default=0, help="first stage to print")
    p.add_argument("--upto", type=int, help="last stage (default: all)")
    p.add_argument("--fit-layer", type=int, help="steel layer whose stiffness to fit")
    p.add_argument("--at", type=float, help="height above the centroid for the fit")
    p.add_argument("--profile", type=int, help="print the profiles over the depth at this stage")
    p.add_argument("--json")
    p.set_defaults(fn=cmd_flow)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
