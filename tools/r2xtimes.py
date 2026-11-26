#!/usr/bin/env python3
"""How long does r2x take on each development case, and is r2c within it?

    python tools/r2xtimes.py measure SCRATCH --response-dir DIR --inputs DIR [DIR ...]
                             [--jobs N] [--only NAME ...] [--stage all|peak]
    python tools/r2xtimes.py compare VERIFY_OUT [--list] [--reading all|peak] [--archive DIR]

Answers the owner's speed threshold (2026-11-26): on every case, r2c's run time is no more
than r2x's on the same input, measured on the same machine.

measure runs r2x's worker on every fixture of tests/oracle the way the fixture was made
(tools/capture.py's command: the input, units, factors, loads and More Detail of its
header) and records the wall-clock seconds of the whole command, Wine's start and the
reading of the charts included, in tests/oracle/r2x-times.json. --stage all (the default)
reads the detail views of every stage, as the captures of the development set do and as
tools/verify.py has r2c write them; --stage peak is r2x's own default, the detail views of
the peak stage alone. Both are kept, side by side. --jobs N runs N at once, each in a Wine
prefix of its own (~/.cache/r2x/prefix-scope-K). The records r2x writes go to SCRATCH,
outside the repository, and are not used for anything else. Needs r2x importable.

compare sets r2c's seconds in a verify run (tools/verify.py's "seconds": the solve alone,
in a process that is already running) beside them: the number of cases where r2c takes no
longer than r2x, by area, for each of the two readings, and with --list the cases that
take longer, slowest first by ratio. --archive DIR adds a third reading: the seconds
tools/capture.py recorded in the development archive's manifest when each case was
captured, one at a time (the same command as "every stage"). Where r2x fails on a case at
a reading there is no time and the case is left out of that row. Development runs only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import queue
import shutil
import statistics as st
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import capture  # noqa: E402
import report  # noqa: E402
from r2c import record  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TIMES = ROOT / "tests" / "oracle" / "r2x-times.json"
READINGS = ("all", "peak")
NAMES = {"all": "every stage", "peak": "the peak", "capture": "every stage, as captured"}


def load() -> dict:
    return json.loads(TIMES.read_text()) if TIMES.exists() else {"cases": {}}


def measure(a) -> int:
    scratch = Path(a.scratch).resolve()
    if ROOT in scratch.parents or scratch == ROOT:
        raise SystemExit("SCRATCH belongs outside the repository")
    scratch.mkdir(parents=True, exist_ok=True)
    fixtures = sorted((ROOT / "tests" / "oracle").glob("*.r2x.txt"))
    if a.only:
        fixtures = [f for f in fixtures if f.name[: -len(".r2x.txt")] in a.only]
    inputs = capture.index_inputs(a.inputs)
    prefixes: queue.Queue = queue.Queue()
    for k in range(max(a.jobs, 1)):
        prefixes.put(Path.home() / ".cache" / "r2x" / f"prefix-scope-{k}")
    work = []
    for fx in fixtures:
        name = fx.name[: -len(".r2x.txt")]
        h = record.read(fx).header
        inp = None
        if h["input-name"] != "File > New":
            src = inputs.get(h.get("input-sha256", ""))
            if src is None:
                print(f"{name}: input {h['input-name']} not found under --inputs: skipped")
                continue
            inp = scratch / "inputs" / h["input-sha256"][:16] / h["input-name"]
            if not inp.exists():
                inp.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, inp)
        work.append((name, h, inp))

    def one(item):
        name, h, inp = item
        prefix = prefixes.get()
        try:
            worker = [sys.executable, "-m", "r2x.worker", "--prefix", str(prefix)]
            out = scratch / f"{name}.{a.stage}.r2x.txt"
            cmd = capture.command(h, inp, out, worker, a.response_dir)
            cmd[cmd.index("--stage") + 1] = a.stage
            t = time.monotonic()
            proc = subprocess.run(cmd, capture_output=True, text=True)
            took = round(time.monotonic() - t, 1)
            ok = proc.returncode == 0 and out.exists()
            print(f"{name}: {took} s" + ("" if ok else f" (r2x failed, exit {proc.returncode})"),
                  flush=True)
            return name, took if ok else None
        finally:
            prefixes.put(prefix)

    with ThreadPoolExecutor(max_workers=max(a.jobs, 1)) as ex:
        got = list(ex.map(one, work))
    data = load()
    for name, took in got:
        if took is not None:
            data["cases"].setdefault(name, {})[a.stage] = took
    data.setdefault("measured", {})[a.stage] = {
        "when": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "machine": f"{platform.system()} {platform.machine()}, {os.cpu_count()} cores",
        "jobs": a.jobs,
        "what": "wall-clock seconds of one r2x.worker command, start to exit",
    }
    data["cases"] = dict(sorted(data["cases"].items()))
    TIMES.write_text(json.dumps(data, indent=1) + "\n")
    failed = [n for n, t in got if t is None]
    print(f"{len(got) - len(failed)} timed, {len(failed)} failed"
          + (": " + ", ".join(failed) if failed else ""))
    return 1 if failed else 0


def compare(a) -> int:
    if "heldout" in a.run or "finish" in a.run:
        raise SystemExit("development runs only")
    results = json.loads((Path(a.run) / "results.json").read_text())
    cases = load()["cases"]
    readings = READINGS
    if a.archive:
        # the seconds tools/capture.py recorded when each case was captured (one at a time)
        man = json.loads((Path(a.archive) / "manifest.json").read_text())
        for n, c in cases.items():
            if "seconds" in man.get(n, {}):
                c["capture"] = man[n]["seconds"]
        readings = READINGS + ("capture",)
    print("Cases where r2c takes no longer than r2x (r2c: seconds of the solve in "
          "tools/verify.py; r2x: seconds of its worker's command)")
    print("| Cases | r2x reads | Within | r2c median | r2x median | Largest ratio |")
    print("|---|---|---:|---:|---:|---:|")
    over_all = []
    for g, title in (("flexure", "without shear"), ("shear", "with shear")):
        for reading in readings:
            rows = [(results[n]["seconds"], c[reading], n) for n, c in cases.items()
                    if reading in c and "seconds" in results.get(n, {})
                    and report.group(results[n]["ref"]) == g]
            if not rows:
                continue
            inside = sum(1 for r, x, _ in rows if r <= x)
            worst = max(r / x for r, x, _ in rows)
            print(f"| {len(rows)} {title} | {NAMES[reading]} | "
                  f"{inside} of {len(rows)} | {st.median(r for r, _, _ in rows):.1f} | "
                  f"{st.median(x for _, x, _ in rows):.1f} | {worst:.1f} |")
            if reading == a.reading:
                over_all += [(r / x, n, r, x) for r, x, n in rows if r > x]
    if a.list:
        print(f"longer than r2x reading {a.reading}:")
        for ratio, n, r, x in sorted(over_all, reverse=True):
            print(f"  {n}: {r:.1f} s against {x:.1f} s ({ratio:.1f} times)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure")
    m.add_argument("scratch")
    m.add_argument("--response-dir", default=os.environ.get("R2X_RESPONSE_DIR"), required=False)
    m.add_argument("--inputs", nargs="+", required=True)
    m.add_argument("--jobs", type=int, default=1)
    m.add_argument("--only", nargs="*")
    m.add_argument("--stage", choices=READINGS, default="all")
    c = sub.add_parser("compare")
    c.add_argument("run")
    c.add_argument("--list", action="store_true")
    c.add_argument("--reading", choices=READINGS, default="all")
    c.add_argument("--archive", help="also against the seconds in this archive's manifest")
    a = ap.parse_args(argv)
    return measure(a) if a.cmd == "measure" else compare(a)


if __name__ == "__main__":
    raise SystemExit(main())
