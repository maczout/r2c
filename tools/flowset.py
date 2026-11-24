"""Is r2c's stiffness in the shear flow calculation Response's, over a set of captures?

    python tools/flowset.py ARCHIVE --inputs FOLDER ... [--only NAME ...] [--set NAME=VALUE ...]
                            [--out FOLDER] [--against FOLDER] [--jobs N]

For each full capture of a shear case this puts r2c into Response's own state at every
stage (tools/diagnose.py flow) and measures how far r2c's calculated shear stress is from
the state's, beside how far Response's own calculated line is from its own state. Where the
stiffness rules are the program's, the two figures are the same. A stage counts as "over"
when Response's own figure is within 2 % (it has converged there) and r2c's is more than a
point above it; the first stage, under next to no load, is left out.

--set switches a rule of the shear driver for the run (a class attribute of
r2c.shear.Shear, as tools/tries.py does it): `--set own_slopes=0` is the kernel with
differences of the stress relation in place of the program's compression slopes. --out
keeps each case's rows as JSON; --against sets a kept run beside this one. This is the
check a stiffness rule is held to before any verify run (step A-5: the program's slopes of
the compressive stress, docs/kernel.md "The stiffness in the shear flow calculation").
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import diagnose  # noqa: E402
import verify  # noqa: E402
from r2c import record  # noqa: E402

CONVERGED = 2.0   # Response's own figure, %, up to which a stage is counted
POINT = 1.0


def one(job):
    path, inp, sets, out = job
    from r2c.shear import Shear
    for item in sets:
        name, _, val = item.partition("=")
        if not hasattr(Shear, name):
            raise SystemExit(f"nothing called {name} on the shear driver")
        setattr(Shear, name, type(getattr(Shear, name))(float(val)))
    tmp = Path(out) / (Path(path).name.split(".")[0] + ".json")
    args = argparse.Namespace(record=str(path), input=inp, first=0, upto=None, fit_layer=None,
                              at=None, profile=None, json=str(tmp))
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            diagnose.cmd_flow(args)
        except (SystemExit, Exception) as e:    # noqa: BLE001 - a case that cannot be run
            return Path(path).name.split(".")[0], str(e)
    return Path(path).name.split(".")[0], None


def summary(rows):
    good = [r for r in rows if r["stage"] > 0 and r.get("oracle") is not None
            and 100 * r["oracle"] <= CONVERGED]
    over = [r for r in good if 100 * (r["r2c"] - r["oracle"]) > POINT]
    worst = max((100 * (r["r2c"] - r["oracle"]) for r in good), default=0.0)
    return len(good), len(over), worst


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("archive", help="folder of full captures")
    ap.add_argument("--inputs", nargs="*", default=[], help="folders with the input files")
    ap.add_argument("--only", nargs="*", help="case names (default: every shear capture)")
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    ap.add_argument("--out", help="folder for each case's rows (JSON)")
    ap.add_argument("--against", help="a folder written by --out, to set beside this run")
    ap.add_argument("--jobs", type=int, default=8)
    a = ap.parse_args(argv)
    import tempfile
    out = Path(a.out) if a.out else Path(tempfile.mkdtemp(prefix="flowset-"))
    out.mkdir(parents=True, exist_ok=True)
    jobs = []
    for p in sorted(Path(a.archive).glob("*.r2x.txt")):
        name = p.name.split(".")[0]
        if a.only and name not in a.only:
            continue
        ref = record.read(p)
        inc = [float(x) for x in ref.header.get("increment", "0,0,0").split(",")]
        ini = [float(x) for x in ref.header.get("initial", "0,0,0").split(",")]
        if inc[2] == 0.0 and ini[2] == 0.0:
            continue
        inp = verify.find_input(ref.header["input-name"], ref.header.get("input-sha256"),
                                a.inputs)
        if inp is None and not ref.header["input-name"].startswith("File"):
            print(f"{name}: input {ref.header['input-name']} not found, left out")
            continue
        jobs.append((p, str(inp) if inp else None, a.set, str(out)))
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        done = dict(ex.map(one, jobs))
    tot = [0, 0, 0]
    for name in sorted(done):
        if done[name]:
            print(f"{name:24s} not run: {done[name]}")
            continue
        rows = json.loads((out / f"{name}.json").read_text())
        n, over, worst = summary(rows)
        line = f"{name:24s} {n:3d} stages; over by a point: {over:3d}; worst {worst:5.1f}"
        tot[0] += n
        tot[1] += over
        prev = Path(a.against) / f"{name}.json" if a.against else None
        if prev is not None and prev.is_file():
            _n, o2, w2 = summary(json.loads(prev.read_text()))
            line += f"    against: {o2:3d}; worst {w2:5.1f}"
            tot[2] += o2
        print(line)
    print(f"{'together':24s} {tot[0]:3d} stages; over by a point: {tot[1]:3d}"
          + (f"    against: {tot[2]:3d}" if a.against else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
