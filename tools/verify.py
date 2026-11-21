#!/usr/bin/env python3
"""Run r2c on every case of a set of reference records and compare.

    python tools/verify.py REFERENCE_DIR --inputs DIR [DIR ...] [--out DIR] [--only NAME ...]
                           [--jobs N]

REFERENCE_DIR holds r2x-raw records (NAME.r2x.txt), normally captured from Response-2000 with
r2x. Each record's header says how it was made (input, units, factors, loads, More Detail);
r2c is run the same way and the two records are compared with tools/compare.py.

--inputs is where the input files named in the headers are found: Response's own folder for
its sample files, and r2x's tests/reference for the Quick Define sections. A file is taken by
its name if it is directly in one of the folders, and otherwise by the SHA-256 the header
records, anywhere under them (the Quick Define inputs are all called hand.r2t in r2x and were
captured under other names). "File > New" and Newbeam's input.r2t need no file: r2c has that
section built in.

Results: OUT/NAME.r2x.txt (r2c's record), OUT/NAME.json (the comparison), OUT/summary.md,
OUT/results.json (every case) and OUT/run.json (what was run, where and when). tools/report.py
turns results.json and run.json into docs/verification-results.md.

Times are measured: wall-clock seconds per case on the machine named in run.json, with --jobs
cases at once. They are r2c's alone; nothing here times Response.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402

from r2c import __version__, record, run, stages  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
import compare as cmp  # noqa: E402

BUILT_IN = {"file > new", "input.r2t", "newbeam.r2t"}


def options(header: dict) -> dict:
    fac = [float(x) for x in header["factors"].split(",")]
    return dict(
        units=header["units"],
        factors="none" if fac == [1.0, 1.0, 1.0] else "csa",
        initial=tuple(float(x) for x in header["initial"].split(",")),
        increment=tuple(float(x) for x in header["increment"].split(",")),
        more_detail=int(header.get("more-detail", "0") or 0),
    )


def find_input(name: str, digest: str | None, folders) -> Path | None:
    """The input a record names: by name directly in a folder, else by SHA-256 under one."""
    for d in folders or []:
        p = Path(d) / name
        if p.is_file():
            return p
    if digest:
        for d in folders or []:
            for p in sorted(Path(d).rglob("*")):
                if p.is_file() and p.suffix.lower() in (".rsp", ".r2t") and \
                        hashlib.sha256(p.read_bytes()).hexdigest() == digest:
                    return p
    return None


def one(args):
    ref_path, inputs, out = args
    name = Path(ref_path).name[: -len(".r2x.txt")]
    ref = record.read(ref_path)
    opt = options(ref.header)
    src = ref.header["input-name"]
    path = None
    if src.lower() not in BUILT_IN:
        path = find_input(src, ref.header.get("input-sha256"), inputs)
        if path is None:
            return name, {"skipped": f"input {src} not found"}
    t = time.time()
    try:
        res = run.solve(path, **opt)
    except Exception as e:  # noqa: BLE001 - reported, not hidden
        return name, {"failed": f"{type(e).__name__}: {e}"}
    took = time.time() - t
    data = res.record_bytes(stages.ALL)
    out = Path(out)
    (out / f"{name}.r2x.txt").write_bytes(data)
    result = cmp.compare(ref, record.decode(data), views=True)
    result["seconds"] = round(took, 1)
    (out / f"{name}.json").write_text(json.dumps(result, indent=1))
    return name, result


def summary(results: dict) -> str:
    rows = ["| case | input | loads (initial; increment) | stages ref / r2c | chart | peak ref | "
            "peak r2c | diff % | curve max % | time s |",
            "|---|---|---|---|---|---:|---:|---:|---:|---:|"]
    for name in sorted(results):
        r = results[name]
        if "skipped" in r or "failed" in r:
            rows.append(f"| {name} | | {r.get('skipped') or r.get('failed')} | | | | | | | |")
            continue
        h = r["ref"]
        extra = ""
        if h["units"] != "si":
            extra += f" {h['units']}"
        if h["factors"] != "1.00,1.00,1.00":
            extra += " csa"
        if h["more-detail"] not in (None, "0"):
            extra += f" more-detail {h['more-detail']}"
        for i, c in enumerate(r["control"]):
            lead = (f"| {name} | {h['input-name']}{extra} | {h['initial']}; {h['increment']} | "
                    f"{h['stage-count']} / {r['sub']['stage-count']} |") if i == 0 else "| | | | |"
            cm = f"{c['curve_max_diff_pct']:.2f}" if "curve_max_diff_pct" in c else ""
            rows.append(f"{lead} {c['chart']} | {c['ref_peak_load']:.1f} | "
                        f"{c['sub_peak_load']:.1f} | {c['peak_diff_pct']:+.2f} | {cm} | "
                        f"{r['seconds'] if i == 0 else ''} |")
    return "\n".join(rows) + "\n"


def git(*args) -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def run_info(a, names) -> dict:
    """What was run, where and when: enough to tell whether the results are current."""
    return {
        "r2c_version": __version__,
        "commit": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain", "--", "src", "tools")),
        "started": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "host": platform.node(),
        "machine": f"{platform.system()} {platform.machine()}, {os.cpu_count()} cores",
        "python": platform.python_version(),
        "numpy": np.__version__,
        "jobs": a.jobs,
        "inputs_dir": bool(a.inputs),
        "reference_dir": str(a.reference_dir),
        "cases": sorted(names),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("reference_dir")
    ap.add_argument("--inputs", nargs="+",
                    help="folders with the input files named in the records")
    ap.add_argument("--out", default="verify-out")
    ap.add_argument("--only", nargs="*", help="case names to run (default: all)")
    ap.add_argument("--jobs", type=int, default=1)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    refs = sorted(Path(a.reference_dir).glob("*.r2x.txt"))
    if a.only:
        refs = [p for p in refs if p.name[: -len(".r2x.txt")] in a.only]
    work = [(str(p), a.inputs, str(out)) for p in refs]
    info = run_info(a, [p.name[: -len(".r2x.txt")] for p in refs])
    (out / "run.json").write_text(json.dumps(info, indent=1))
    results = {}
    old = out / "results.json"
    if old.exists():
        results = json.loads(old.read_text())
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        for name, res in ex.map(one, work):
            res["run"] = info["commit"][:12] + ("+dirty" if info["dirty"] else "")
            results[name] = res
            state = res.get("skipped") or res.get("failed") or f"{res['seconds']} s"
            print(f"{name}: {state}", flush=True)
            old.write_text(json.dumps(results, indent=1))
    (out / "summary.md").write_text(summary(results))
    print(f"wrote {out / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
