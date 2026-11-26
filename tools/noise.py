#!/usr/bin/env python3
"""How far is Response from itself when an input changes by next to nothing?

    python tools/noise.py capture OUT --response-dir DIR --inputs DIR [DIR ...] [--jobs N]
                                  [--only NAME ...] [--flexure] [--by PCT]
    python tools/noise.py score OUT [--list]

Answers "how much of a priority's checks can any other program reach?" on the development
set. `capture` takes each development case (tests/oracle; those with shear unless
--flexure), raises every concrete strength in its input by --by per cent (0.05 if not
given: 35.0 MPa becomes 35.018), and captures the changed input from Response-2000 through
r2x with the case's own options, into OUT (outside the repository). `score` then compares
each of those captures with the case's fixture exactly as tools/verify.py compares r2c's
record with it, assesses it as tools/report.py does, and prints how many cases are inside
target on every check of each priority (tools/heldout.py's tally): Response with a
concrete 0.05 % stronger, measured as if it were r2c.

Where that total is well under 100 %, the checks of that priority turn on states that
Response itself does not hold to under a change no engineer would call a change, and no
clone can be expected to do better than Response does against itself. Nothing here is a
target and nothing is assessed for r2c. Never anything of the held-out sets.

`capture` needs r2x importable (PYTHONPATH=R2X/src) and one Wine prefix per job.
"""

from __future__ import annotations

import argparse
import os
import queue
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import capture as cap  # noqa: E402
import compare as cmp  # noqa: E402
import heldout  # noqa: E402
import report  # noqa: E402
import verify  # noqa: E402
from r2c import record  # noqa: E402

FCP = re.compile(rb'(fcp\t+=")([0-9.]+)(")')


def has_shear(h: dict) -> bool:
    return any(float(h[k].split(",")[2]) for k in ("initial", "increment"))


def cases(only, flexure: bool):
    for p in sorted((ROOT / "tests" / "oracle").glob("*.r2x.txt")):
        name = p.name[: -len(".r2x.txt")]
        h = record.read(p).header
        if (only and name not in only) or (not only and has_shear(h) == flexure):
            continue
        yield name, p, h


def stronger(data: bytes, pct: float) -> bytes:
    out, n = FCP.subn(lambda m: m[1] + f"{float(m[2]) * (1 + pct / 100):.3f}".encode() + m[3],
                      data)
    if not n:
        raise ValueError("no concrete strength found in the input")
    return out


def capture(a) -> int:
    out = Path(a.out).resolve()
    if ROOT in out.parents or out == ROOT or "heldout" in str(out) or "finish" in str(out):
        raise SystemExit("OUT belongs outside the repository and outside the held-out archives")
    (out / "inputs").mkdir(parents=True, exist_ok=True)
    prefixes: queue.Queue = queue.Queue()
    for k in range(max(a.jobs, 1)):
        prefixes.put(Path.home() / ".cache" / "r2x" / f"prefix-scope-{k}")

    def one(item):
        name, _p, h = item
        dest = out / f"{name}.r2x.txt"
        if dest.exists():
            return
        src = h["input-name"]
        path = verify.find_input("input.r2t" if src.lower() in verify.BUILT_IN else src,
                                 h.get("input-sha256"), a.inputs)
        if path is None:
            print(f"{name}: input {src} not found", flush=True)
            return
        inp = out / "inputs" / name / path.name
        inp.parent.mkdir(exist_ok=True)
        inp.write_bytes(stronger(path.read_bytes(), a.by))
        prefix = prefixes.get()
        try:
            worker = [sys.executable, "-m", "r2x.worker", "--prefix", str(prefix)]
            proc = subprocess.run(cap.command(h, inp, dest, worker, a.response_dir),
                                  capture_output=True, text=True)
            print(f"{name}: " + ("captured" if proc.returncode == 0 and dest.exists()
                                 else f"r2x failed: {proc.stderr[-300:]}"), flush=True)
        finally:
            prefixes.put(prefix)

    with ThreadPoolExecutor(max_workers=max(a.jobs, 1)) as ex:
        list(ex.map(one, list(cases(a.only, a.flexure))))
    return 0


def score(a) -> int:
    out = Path(a.out)
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    todo, results = [], {}
    for p in sorted(out.glob("*.r2x.txt")):
        name = p.name[: -len(".r2x.txt")]
        fx = ROOT / "tests" / "oracle" / p.name
        if not fx.exists():
            continue
        ref = record.read(fx)
        results[name] = cmp.compare(ref, record.read(p), views=True)
        todo.append({"name": name,
                     "area": heldout.AREAS["shear" if has_shear(ref.header) else "flexure"]})
    counted = heldout.tally(todo, results, acc)
    print(f"Response with every concrete strength raised a little, against Response as it "
          f"is: {len(todo)} development cases, inside target on every check of the priority")
    for t, title in heldout.AREA_TITLES.items():
        if not any(c["area"] == t for c in todo):
            continue
        print(f"  {title}:")
        for p, (n, of) in counted["totals"][t].items():
            print(f"    priority {p}: {heldout.pct(n, of)}")
    if a.list:
        groups = {t: g for g, t in heldout.AREAS.items()}
        for c in todo:
            chk = report.assess(results[c["name"]], acc)
            bad = [p for p, names in heldout.PRIORITY[groups[c["area"]]].items()
                   if any(chk[n][2] is False for n in names if n in chk)]
            if bad:
                print(f"  {c['name']}: outside on priority " + ", ".join(bad))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=("capture", "score"))
    ap.add_argument("out")
    ap.add_argument("--response-dir", default=os.environ.get("R2X_RESPONSE_DIR"))
    ap.add_argument("--inputs", nargs="*", default=[])
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--flexure", action="store_true",
                    help="capture: the cases without shear in place of those with")
    ap.add_argument("--by", type=float, default=0.05, help="per cent added to each fc'")
    ap.add_argument("--list", action="store_true",
                    help="score: name the development cases outside, by priority")
    a = ap.parse_args(argv)
    return capture(a) if a.action == "capture" else score(a)


if __name__ == "__main__":
    raise SystemExit(main())
