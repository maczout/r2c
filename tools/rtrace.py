"""What did Response-2000's own load stage control do, try by try, on a case with shear?

    python tools/rtrace.py RECORD --input FILE --response-dir RESPONSE_FOLDER --out LOG
                           [--prefix WINE_PREFIX] [--steps]
    python tools/rtrace.py --show LOG [--passes] [--from N]

The counterpart of tools/trace.py for the program itself: every target Response tries,
the step multiplier and base step, whether the solve of the global strains came back,
the profile error and state code of every pass, and whether the try was kept, failed or
(a stage put in between) dropped. It answers "why is Response's stage here and r2c's
there" by observation, where reading the routines leaves it open (owner, 2026-11-24, D64:
what a stage starts from, and the tries Response makes).

How. Response is run as r2x runs it for a capture (r2x's worker, under Wine), but started
under tools/rtrace.c, a small debugger: it stops the program each time the stage control
finishes a pass [B `00418af0`, at the count of passes], accepts a stage, fails a try or
drops a stage put in between, reads the values from the program's memory and lets it go
on. Nothing in the program or its folder is changed, and the capture it makes is the
same as without (compare its stage count with the fixture's). With --steps every step of
the solve of the global strains [B `004276a0`, after `004267c0`] is logged too: whether
the step routine gave up, and the depth range with stiffness the step was taken on.

RECORD is the case's fixture or capture: its header gives the loading and settings, as
for tools/capture.py. Needs r2x importable (PYTHONPATH=R2X/src), Wine, Xvfb and
i686-w64-mingw32-gcc, which r2x's worker needs anyway. The log and rtrace.exe are kept
outside the repository (the log is Response's own numbers).

Columns of --show, as tools/trace.py prints r2c's: the index of the stage worked on; the
control variable and its target (rad/km, or mm/m); the step multiplier; the base step;
what came of the try; the load factor; the profile error (%) and passes of the last
pass; the state code; then the curvature, the centroid's strain and the section's shear
strain. A failed try is given its reason by the program's own tests on the last pass:
"no solve" (the solve of the global strains gave up; "at once" where it gave up on its
first step without moving), "code N" (state code with the multiplier at 0.5 or more),
"code 3 above" (web crushing with the load above the largest so far), "16 passes above"
(not converged after 16 passes with the load above the largest so far).

Signs and units are r2c's: Response holds the curvature with the other sign and in 1/m.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = """\
00418c19 P i:edi+85c i:edi+2bd i:edi+848 d:edi+854 d:edi+838 d:edi+84c i:edi+840 d:edi+4 d:edi+14 i:edi+10 r:ebx d:ebp-18 i:ebp-8 d:esi+8 d:esi+10 d:esi+18 d:esi+a8
00418d68 A i:edi+85c
00418e83 D i:edi+85c
00418eb2 F i:edi+85c
"""
STEPS = """\
00427aef S r:eax i:ebp-130 d:esi+14 d:[ebp-138]+148 d:[ebp-138]+150 d:edi d:edi+8 d:edi+10
"""
MODES = {0: "e0", 1: "phi", 2: "gam"}


def shim(argv) -> int:
    """r2x's worker, with Response started under rtrace.exe (the environment says where)."""
    from r2x.worker import runner, session
    import r2x.worker.__main__ as worker_main

    exe, spec, log = (os.environ[k] for k in ("RTRACE_EXE", "RTRACE_SPEC", "RTRACE_LOG"))
    plain = subprocess.Popen

    class Popen(plain):
        def __init__(self, cmd, *a, **k):
            if list(cmd[:2]) == ["wine", "r2k.exe"]:
                wp = session.wine_path
                cmd = ["wine", wp(Path(exe)), wp(Path(spec)), wp(Path(log)),
                       wp(Path(k["cwd"]) / "r2k.exe"), *cmd[2:]]
            super().__init__(cmd, *a, **k)

    class Cpu(session.Cpu):
        """Processor time of the process and of everything started under it: Response
        is now a child of the tracer."""

        def __init__(self, pid):
            self.pid = pid

        def seconds(self):
            procs = {}
            for p in Path("/proc").iterdir():
                if p.name.isdigit():
                    try:
                        f = (p / "stat").read_text().rsplit(")", 1)[1].split()
                        procs[int(p.name)] = (int(f[1]), int(f[11]) + int(f[12]))
                    except (OSError, IndexError):
                        pass
            if self.pid not in procs:
                return None
            want = {self.pid}
            grew = True
            while grew:
                grew = False
                for q, (parent, _t) in procs.items():
                    if parent in want and q not in want:
                        want.add(q)
                        grew = True
            return sum(procs[q][1] for q in want) / os.sysconf("SC_CLK_TCK")

    subprocess.Popen = Popen
    runner.Cpu = Cpu
    return worker_main.main(argv)


def build(cache: Path) -> Path:
    exe = cache / "rtrace.exe"
    src = HERE / "rtrace.c"
    if not exe.exists() or exe.stat().st_mtime < src.stat().st_mtime:
        cache.mkdir(parents=True, exist_ok=True)
        subprocess.run(["i686-w64-mingw32-gcc", "-O1", "-o", str(exe), str(src)], check=True)
    return exe


def read(log: Path):
    """The tries of a log: a list of dicts, each with its passes and how it ended."""
    tries, cur, steps = [], None, []
    for line in Path(log).read_text().splitlines():
        f = line.split()
        if not f or f[0].startswith("#"):
            continue
        if f[0] == "S":
            steps.append(dict(ret=int(f[1]), it=int(f[2]), share=float(f[3]),
                              zhi=float(f[4]), zlo=float(f[5])))
        elif f[0] == "P":
            n, done, mode = int(f[1]), int(f[2]), MODES[int(f[3])]
            k = -1e3 if mode == "phi" else 1e3
            p = dict(n=n, done=done, mode=mode, target=k * float(f[4]), mult=float(f[5]),
                     d0=abs(float(f[6])) * 1e3, retries=int(f[7]), peak=float(f[8]),
                     share=float(f[9]), flag=int(f[10]), r=int(f[11]), err=float(f[12]),
                     code=int(f[13]), e0=float(f[14]) * 1e3, phi=-float(f[15]) * 1e3,
                     gam=float(f[16]) * 1e3, lam=float(f[17]), steps=steps)
            steps = []
            if cur is None:
                cur = dict(passes=[], what=None)
                tries.append(cur)
            cur["passes"].append(p)
        elif f[0] in "ADF" and cur is not None:
            cur["what"] = {"A": "kept", "D": "dropped", "F": "failed"}[f[0]]
            cur = None
    return tries


def why(t) -> str:
    """The program's reason for failing a try, from its last pass [B 00418af0]."""
    p = t["passes"][-1]
    if p["r"] == 0:
        once = len(t["passes"]) == 1 and len(p["steps"]) == 1 and p["steps"][0]["ret"] != 0
        return "no solve, at once" if once else "no solve"
    if p["code"] != 0 and p["mult"] >= 0.5:
        return f"code {p['code']}"
    if p["code"] == 3 and p["lam"] > p["peak"]:
        return "code 3 above"
    if p["done"] + 1 > 15 and p["err"] > 0.03 and p["lam"] > p["peak"]:
        return "16 passes above"
    return "?"


def show(log: Path, passes: bool, first: int) -> int:
    tries = read(log)
    print(f"{'stg':>4} {'ctl':>3} {'target':>9} {'mult':>6} {'base':>7} {'what':<18} "
          f"{'load':>8} {'err %':>8} {'pass':>4} {'code':>4} {'phi':>8} {'e0':>8} {'gam':>8}")
    kept = 0
    for t in tries:
        p = t["passes"][-1]
        what = t["what"] or "(unfinished)"
        if what == "failed":
            what = why(t)
        elif what == "dropped":
            what = "dropped: " + why(t)
        if p["n"] >= first:
            err = f"{100 * p['err']:8.2f}" if p["err"] < 1e3 else f"{'big':>8}"
            print(f"{p['n']:4d} {p['mode']:>3} {p['target']:9.4f} {p['mult']:6.3f} "
                  f"{p['d0']:7.4f} {what:<18} {p['lam']:8.2f} {err} {len(t['passes']):4d} "
                  f"{p['code']:4d} {p['phi']:8.4f} {p['e0']:8.4f} {p['gam']:8.4f}")
            if passes:
                for q in t["passes"]:
                    e = f"{100 * q['err']:.2f}" if q["err"] < 1e3 else "big"
                    s = q["steps"]
                    note = ""
                    if s:
                        note = (f"  solve: {len(s)} steps, share {s[-1]['share']:g}, range "
                                f"{s[0]['zlo']:g} to {s[0]['zhi']:g} m"
                                + ("; step routine gave up" if any(x["ret"] for x in s) else ""))
                    print(f"       pass {q['done'] + 1:2d}: solve {q['r']:2d}, load {q['lam']:.2f}, "
                          f"error {e} %, code {q['code']}, phi {q['phi']:.4f}, e0 {q['e0']:.4f}, "
                          f"gam {q['gam']:.4f}{note}")
        kept += t["what"] == "kept"
    print(f"{kept} stages kept after the first, {len(tries)} tries")
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--shim"]:
        return shim(argv[1:])
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("record", nargs="?")
    ap.add_argument("--input")
    ap.add_argument("--response-dir")
    ap.add_argument("--prefix", help="Wine prefix (r2x's default if not given)")
    ap.add_argument("--out", help="where the log goes (outside the repository)")
    ap.add_argument("--steps", action="store_true", help="log every step of the solve too")
    ap.add_argument("--show", metavar="LOG")
    ap.add_argument("--passes", action="store_true", help="with --show: every pass")
    ap.add_argument("--from", dest="first", type=int, default=0, help="first stage to print")
    a = ap.parse_args(argv)
    if a.show:
        return show(Path(a.show), a.passes, a.first)
    if not (a.record and a.response_dir and a.out):
        ap.error("RECORD, --response-dir and --out are needed")
    sys.path.insert(0, str(HERE.parent / "src"))
    sys.path.insert(0, str(HERE))
    import capture
    from r2c import record
    h = record.read(a.record).header
    out = Path(a.out).resolve()
    cache = Path.home() / ".cache" / "r2c"
    exe = build(cache)
    spec = out.with_suffix(".spec")
    spec.write_text(SPEC + (STEPS if a.steps else ""))
    worker = [sys.executable, str(Path(__file__).resolve()), "--shim"]
    if a.prefix:
        worker += ["--prefix", a.prefix]
    inp = Path(a.input) if a.input else None
    cmd = capture.command(h, inp, out.with_suffix(".r2x.txt"), worker, a.response_dir)
    cmd[cmd.index("--stage") + 1] = "peak"          # the tries are what is wanted
    env = dict(os.environ, RTRACE_EXE=str(exe), RTRACE_SPEC=str(spec), RTRACE_LOG=str(out))
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-2000:])
        return proc.returncode
    made = record.read(out.with_suffix(".r2x.txt")).header.get("stage-count")
    print(f"{out}: Response made {made} stages (the record given has "
          f"{h.get('stage-count')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
