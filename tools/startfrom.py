"""Path or iteration: started from Response's own state at the stage before, does r2c
land on Response's state?

    python tools/startfrom.py CAPTURE [--input FILE] --stage N [N ...] [--from M] [--back K]
                              [--mode phi|gam|e0 ...] [--set NAME=VALUE ...] [--list]
                              [--passes] [--all-views]

Answers the question step A-4 asks before anything is read from the binary (owner,
2026-11-24, D64): where r2c and Response sit in different states at a stage, is that
because r2c's stage *started* from something else (the stage before, its profile, its
history), or because r2c's passes on a stage (the solve of the global strains, the
profile update, the tests) go another way from the same start?

CAPTURE is a capture of every stage (the archive, not a fixture). For Response's stage N:

1. r2c is put into Response's own states of stages 0 to M (M = N - 1 unless --from; with
   --back K, M = N - K), each committed as r2c commits an accepted stage, as
   tools/diagnose.py states does. That is Response's path, with r2c's rules.
2. r2c's driver then works on the next stage as it does in a run (Shear._solve: up to 16
   passes of solve and profile update), from Response's state M as the stage before, to
   Response's own control value at N. With --back K it goes on through Response's control
   values to N, each stage accepted, so that K stages of r2c's own iteration separate it
   from Response's path.
3. The state it lands on is set against Response's at N: the load, the three global
   strains, the shear strain profile, and every detail view, beside the same views with
   r2c put into Response's state at N itself (tools/diagnose.py states --views).

Two starts are tried, because the stage before hands over a profile and what Response
hands over was read but not seen: "state" starts from the profile of Response's state M
as its Shear Strain chart gives it; "updated" from that profile after one update from
the calculated shear stress at M, which is what the binary leaves for the next stage
(docs/kernel.md, "What a stage leaves behind"). And each control variable asked for with
--mode is tried (all that the loading can have, if none is given): which one Response
was stepping at N is not in the capture, and the state must satisfy all of them.

**Reading the result.** "lands" means: every view that is inside target with r2c in
Response's state at N is inside after r2c's own passes too, and the load is within the
target on a peak. If r2c lands from Response's state M but its own run does not reach
that state, the difference is in what a stage starts from (the path). If it does not
land, it is in the passes on a stage (the iteration). Nothing is assessed here.

--list prints Response's stages (load, the global strains read from the charts, and
Response's own profile error in its own measure, from the two lines of its Shear Stress
chart: 1 % or more is a stage the program kept without convergence) and stops. --set switches an attribute of the driver or the analysis, as tools/trace.py does.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
import diagnose  # noqa: E402
import report  # noqa: E402
from r2c import export, record  # noqa: E402
from r2c.solver import SolveError, Stage  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def mean_one(sec, prof):
    """Response's shear strain profile at a stage (heights, strains) as r2c holds one:
    (the section's shear strain, (heights, the profile with a mean of one over the
    depth)). The mean is over the depth with no width in it, as the program's is."""
    z, g = prof
    gam = float(np.trapezoid(g, z)) / (float(z[-1] - z[0]) or 1.0)
    if abs(gam) < 1e-12:
        return 0.0, None
    return gam, (z.copy(), g / gam)


def walk(ref, su, upto: int, views):
    """r2c in Response's states 0 to `upto`, each committed; returns the last twice: as a Stage
    whose strains are Response's (gam the section's shear strain, the analysis holding
    the profile of mean one), and as evaluated, for its views."""
    an = su.analysis
    st = None
    for s in range(upto + 1):
        e0, phi, prof, _r = diagnose.strain_state(ref, su, s)
        st = diagnose.evaluate(su, e0, phi, prof)
        views.observe(st)
        if s > 0:
            an.commit(st.e0, st.phi)
            if prof is not None:
                an.commit_stirrups(st.detail)
    gam, shape = (0.0, None) if prof is None else mean_one(su.section, prof)
    if shape is None:
        an.shape_z = an.shape_z0.copy()
        an.shape = an._elastic_shape()
    else:
        an.set_profile(shape)
    lam = load_factor(su, st)
    return Stage(st.e0, st.phi, gam, lam, st.n, st.m, st.v, st.detail), st


def load_factor(su, st) -> float:
    an = su.analysis
    for val, base, inc in ((st.m, an.m0, an.dm), (st.v, an.v0, an.dv), (st.n, an.n0, an.dn)):
        if inc != 0.0:
            return (val - base) / inc
    return 0.0


def response_control(ref, su, stage: int, mode: str) -> float:
    e0, phi, prof, _r = diagnose.strain_state(ref, su, stage)
    if mode == "phi":
        return phi
    if mode == "e0":
        return e0
    return mean_one(su.section, prof)[0] if prof is not None else 0.0


def view_rows(ref, su, views, st, stage: int):
    made = views.charts(st, [k.split("/", 2)[2] for k in ref.sections
                             if k.startswith(f"stage/{stage}/")])
    sub = record.decode(record.encode(
        dict(ref.header), [(record.stage_section(stage, k), b) for k, b in made.items()]))
    out = {}
    for v in cmp.compare_views(ref, sub, stage, stage):
        if v.get("missing") or v["view"] in diagnose.NOT_HERE:
            continue
        out[v["view"]] = 0.0 if v["max_diff"] <= v.get("floor", 0.0) else v["max_diff_pct"]
    return out


def profile_gap(ref, su, stage: int, st) -> float:
    """The largest difference between r2c's shear strain over the depth and Response's at
    the stage, in % of Response's largest."""
    _e0, _phi, prof, _r = diagnose.strain_state(ref, su, stage)
    if prof is None:
        return 0.0
    z, g = prof
    d = st.detail
    mine = np.interp(z, np.asarray(d.z)[::-1] if d.z[0] > d.z[-1] else d.z,
                     np.asarray(d.gxy)[::-1] if d.z[0] > d.z[-1] else d.gxy)
    top = float(np.max(np.abs(g)))
    return 100.0 * float(np.max(np.abs(mine - g))) / top if top else 0.0


def response_error(ref, su, stage: int):
    """Response's own profile error at a stage, in its measure [docs/kernel.md,
    "Accepting a stage"], from the two lines of its Shear Stress chart (the state's and
    the calculated): the standard deviation of their difference over 50 points of the
    depth, over the mean calculated stress. None where the chart has not both lines. Under
    1 % the program takes a stage as converged; the chart is printed to three decimals,
    so a small error is read coarsely."""
    try:
        lines = [ln for ln in cmp.parse_chart(ref.stage(stage, "shear_stress"))[3] if len(ln)]
    except KeyError:
        return None
    if len(lines) < 2:
        return None
    sec, u = su.section, su.units
    y = np.linspace(sec.zbot - sec.zc, sec.ztop - sec.zc, 50) / u.length
    both = []
    for ln in lines[:2]:
        o = np.argsort(ln[:, 1], kind="stable")
        both.append(np.interp(y, ln[:, 1][o], ln[:, 0][o]))
    d = both[1] - both[0]
    mean = float(np.mean(both[1]))
    sd = float(np.sqrt(max(float(np.sum(d * d) * 50.0 - np.sum(d) ** 2) / 50.0 / 49.0, 0.0)))
    return abs(sd / mean) if abs(mean) > 1e-12 else None


def attempt(a, stage: int, mode: str, start: str, limit: float, peak_pct: float):
    """One try: Response's path to M, then r2c's passes to N. Returns a row."""
    ref = record.read(a.record)
    su = diagnose._setup(ref, a.input)
    an = su.analysis
    u = su.units
    drv = su.driver()
    for item in a.set:
        name, _, val = item.partition("=")
        obj = an if hasattr(type(an), name) else drv
        if not hasattr(obj, name):
            raise SystemExit(f"nothing called {name} on the analysis or the driver")
        setattr(obj, name, type(getattr(obj, name))(float(val)))
    drv.debug = a.passes
    first = a.origin if a.origin is not None else stage - a.back
    if first < 0 or first >= stage:
        raise SystemExit(f"stage {stage}: cannot start from stage {first}")
    views = export.Views(su.section, u)
    prev, _raw = walk(ref, su, first, views)
    drv.mode0 = drv.first_control()
    drv.mode = mode
    if start == "updated" and prev.gam != 0.0:
        # what a stage leaves for the next: the profile after one more update
        z, vstate, tau, t, _d = drv.shear_flow(prev.e0, prev.phi, prev.gam, prev.v)
        drv.update_profile(z, vstate, tau, t, prev.gam)
    key = cmp.control_keys(ref)[-1]
    curve = cmp._curve(ref, key)
    comp = diagnose.LOADS[key]
    unit = u.moment if comp == "m" else u.force
    top = float(np.max(np.abs(curve[:, 1])))
    lams = []
    st = prev
    passes, perr = [], []
    # the stages between first and N are those the capture lists, in its order
    for s in range(first + 1, stage + 1):
        c = response_control(ref, su, s, mode)
        try:
            nxt = drv._solve(c, st, dict(mult=1.0, peak=max(lams, default=prev.lam),
                                         last=st.lam))
        except SolveError as e:
            return dict(mode=mode, start=start, error=str(e), at=s)
        passes.append(nxt.passes)
        perr.append(nxt.perr)
        lams.append(nxt.lam)
        views.observe(nxt)
        if s < stage:
            an.commit(nxt.e0, nxt.phi)
            if nxt.gam != 0.0:
                an.commit_stirrups(nxt.detail)
        st = nxt
    e0, phi, prof, _r = diagnose.strain_state(ref, su, stage)
    gam = mean_one(su.section, prof)[0] if prof is not None else 0.0
    vr = view_rows(ref, su, views, st, stage)
    ora = float(curve[stage, 1])
    return dict(mode=mode, start=start, passes=passes, perr=perr,
                load=getattr(st, comp) / unit, load_ref=ora,
                load_pct=100.0 * (getattr(st, comp) / unit - ora) / top if top else 0.0,
                de0=(st.e0 - e0) * 1e3, dphi=(st.phi - phi) * 1e6, dgam=(st.gam - gam) * 1e3,
                gap=profile_gap(ref, su, stage, st), views=vr)


def own_state(a, stage: int):
    """The views with r2c in Response's own state at N (history carried)."""
    ref = record.read(a.record)
    su = diagnose._setup(ref, a.input)
    views = export.Views(su.section, su.units)
    _st, raw = walk(ref, su, stage, views)
    return view_rows(ref, su, views, raw, stage)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("record")
    ap.add_argument("--input")
    ap.add_argument("--stage", type=int, nargs="+")
    ap.add_argument("--from", dest="origin", type=int,
                    help="Response's stage to start from (the stage before, if not given)")
    ap.add_argument("--back", type=int, default=1,
                    help="start this many stages back and walk Response's control values")
    ap.add_argument("--mode", nargs="*", choices=("phi", "gam", "e0"))
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--passes", action="store_true",
                    help="print the load factor and profile error of every pass")
    ap.add_argument("--all-views", action="store_true", help="print every view, not the worst")
    a = ap.parse_args(argv)
    ref = record.read(a.record)
    have = ref.stages()
    if have != list(range(len(have))):
        raise SystemExit("a capture of every stage is needed (the archive, not a fixture)")
    su = diagnose._setup(ref, a.input)
    key = cmp.control_keys(ref)[-1]
    curve = cmp._curve(ref, key)
    if a.list or not a.stage:
        print(f"{'stage':>5} {'load':>9} {'e0 mm/m':>9} {'phi rad/km':>11} {'gam mm/m':>9} "
              f"{'profile error %':>15}")
        for s in have:
            e0, phi, prof, _r = diagnose.strain_state(ref, su, s)
            gam = mean_one(su.section, prof)[0] if prof is not None else 0.0
            err = response_error(ref, su, s)
            print(f"{s:5d} {curve[s, 1]:9.2f} {e0 * 1e3:9.4f} {phi * 1e6:11.4f} "
                  f"{gam * 1e3:9.4f} " + ("" if err is None else f"{100 * err:15.2f}"))
        return 0
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    limit = acc.get("views", {}).get("views_pct", 5.0)
    peak_pct = 5.0
    an = su.analysis
    modes = a.mode or [m for m, inc in (("phi", an.dm), ("gam", an.dv), ("e0", an.dn))
                       if inc != 0.0 or m == "gam"]
    for stage in a.stage:
        own = own_state(a, stage)
        inside = {k for k, v in own.items() if v <= limit}
        first = a.origin if a.origin is not None else stage - a.back
        print(f"Response's stage {stage} (load {curve[stage, 1]:g}), r2c started from "
              f"Response's stage {first} (load {curve[first, 1]:g})")
        worst = max(own.items(), key=lambda kv: kv[1], default=("", 0.0))
        print(f"  in Response's own state at {stage}: {len(own) - len(inside)} of {len(own)} "
              f"views outside; worst {worst[0]} {worst[1]:.1f} %")
        for mode in modes:
            for start in ("state", "updated"):
                r = attempt(a, stage, mode, start, limit, peak_pct)
                head = f"  control {mode:>3}, profile {start:<7}: "
                if "error" in r:
                    print(head + f"no state at Response's stage {r['at']} ({r['error']})")
                    continue
                out = {k: v for k, v in r["views"].items() if v > limit and k in inside}
                lands = not out and abs(r["load_pct"]) <= peak_pct
                wv = max(r["views"].items(), key=lambda kv: kv[1], default=("", 0.0))
                print(head + f"load {r['load']:.2f} against {r['load_ref']:.2f} "
                      f"({r['load_pct']:+.2f} % of the peak); e0 {r['de0']:+.4f} mm/m, phi "
                      f"{r['dphi']:+.4f} rad/km, gam {r['dgam']:+.4f} mm/m; profile "
                      f"{r['gap']:.1f} %; passes {r['passes']}, profile error "
                      + ", ".join(f"{100 * e:.2f}" for e in r["perr"]) + " %")
                print(f"      views outside that are inside in Response's state: {len(out)}"
                      + (f" (worst {wv[0]} {wv[1]:.1f} %)" if r["views"] else "")
                      + ("  -> lands" if lands else "  -> does not land"))
                if a.all_views or out:
                    for k in sorted(r["views"], key=lambda k: -r["views"][k]):
                        if a.all_views or k in out:
                            print(f"        {k:32s} {r['views'][k]:7.1f} %   "
                                  f"(in Response's state {own.get(k, float('nan')):.1f} %)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
