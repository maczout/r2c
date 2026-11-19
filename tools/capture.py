#!/usr/bin/env python3
"""Rebuild the oracle archive: capture every stage of each case from Response-2000 with r2x.

    python tools/capture.py ARCHIVE --response-dir DIR --inputs DIR [DIR ...]
                            [--only NAME ...] [--from tests/oracle] [--dry-run]

The recipe is the fixtures themselves. Each fixture in tests/oracle is a capture cut down to
its control charts and peak, and its header records how it was made: the input (by name and
SHA-256), units, factors, initial load, increment, More Detail and views. For each fixture this
tool finds the input with that SHA-256 in the --inputs folders, copies it to ARCHIVE/inputs/
under the fixture's input name (r2x records the name), runs r2x's worker with the same settings
and every stage, and writes ARCHIVE/NAME.r2x.txt.

It then checks the capture against the fixture: the capture is cut down the way the fixture was
(tools/trim.py) and the two must match byte for byte, apart from header lines that identify the
machine (r2x and Wine versions). A mismatch means Response, r2x or the input is not what made
the fixture, and is reported; the capture is kept for inspection.

ARCHIVE/manifest.json records, for each capture: the command, when it was made, its SHA-256 and
size, and the check's result. Captures stay out of the repository (they run to tens of
megabytes); the recipe and the manifest's format are what the repository keeps.

Where the inputs are: Response's own folder for its samples (Marshall.rsp, Cm4.rsp, ...), and
r2x's tests/reference/newbeam for the Newbeam (input.r2t). "File > New" needs no input.

Captures must run one at a time in the default Wine prefix, which this tool does. Each takes
25 to 75 s, nearly all of it r2x reading the charts of every stage.

Not run in the session that wrote it (no Response there): check with --dry-run first.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import trim  # noqa: E402
from r2c import record  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# header lines that depend on the machine, not on the case
MACHINE_KEYS = {"r2x-version", "wine-version", "disclaimer"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index_inputs(dirs: list[str]) -> dict[str, Path]:
    """SHA-256 -> path of every .rsp and .r2t file under the folders."""
    found: dict[str, Path] = {}
    for d in dirs:
        for p in Path(d).rglob("*"):
            if p.is_file() and p.suffix.lower() in (".rsp", ".r2t"):
                found.setdefault(sha256(p), p)
    return found


def factors_option(h: dict) -> str:
    fac = [float(x) for x in h["factors"].split(",")]
    if fac == [1.0, 1.0, 1.0]:
        return "none"
    if fac == [0.65, 0.85, 0.90]:
        return "csa"
    raise ValueError(f"factors {h['factors']} are neither none nor CSA's: r2x cannot set them")


def command(h: dict, inp: Path | None, out: Path, worker: list[str], response_dir: str):
    cmd = list(worker)
    cmd += ["--new", str(out)] if inp is None else [str(inp), str(out)]
    cmd += ["--stage", "all", "--views", h["views"],
            "--units", h["units"], "--factors", factors_option(h),
            f"--initial={h['initial']}", f"--increment={h['increment']}",
            "--more-detail", h.get("more-detail", "0") or "0",
            "--response-dir", response_dir]
    return cmd


def check(capture: Path, fixture: Path) -> dict:
    """Cut the capture as the fixture was cut and compare."""
    fx = record.read(fixture)
    cap = record.read(capture)
    keep = [int(s) for s in fx.stages()]
    cut = record.decode(trim.trim(cap, keep))
    diff_header = sorted(k for k in set(fx.header) | set(cut.header)
                         if k not in MACHINE_KEYS and fx.header.get(k) != cut.header.get(k))
    diff_sections = sorted(k for k in set(fx.sections) | set(cut.sections)
                           if fx.sections.get(k) != cut.sections.get(k))
    return {"matches": not diff_header and not diff_sections,
            "header_differs": diff_header, "sections_differ": diff_sections}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("archive", help="folder for the captures (outside the repository)")
    ap.add_argument("--response-dir", default=os.environ.get("R2X_RESPONSE_DIR"),
                    help="Response-2000's folder (default: $R2X_RESPONSE_DIR)")
    ap.add_argument("--inputs", nargs="*", default=[],
                    help="folders to search for the inputs, by SHA-256")
    ap.add_argument("--from", dest="fixtures", default=str(ROOT / "tests" / "oracle"),
                    help="folder of fixtures to use as the recipe")
    ap.add_argument("--only", nargs="*", help="case names (default: every fixture)")
    ap.add_argument("--worker", default="python -m r2x.worker",
                    help="how to run r2x's worker (default: %(default)s)")
    ap.add_argument("--dry-run", action="store_true", help="print the commands only")
    a = ap.parse_args(argv)
    if not a.response_dir and not a.dry_run:
        ap.error("--response-dir or $R2X_RESPONSE_DIR is required")
    archive = Path(a.archive).resolve()
    if ROOT in archive.parents or archive == ROOT:
        ap.error("the archive belongs outside the repository")
    fixtures = sorted(Path(a.fixtures).glob("*.r2x.txt"))
    if a.only:
        fixtures = [f for f in fixtures if f.name[: -len(".r2x.txt")] in a.only]
    inputs = index_inputs(a.inputs)
    worker = shlex.split(a.worker)
    archive.mkdir(parents=True, exist_ok=True)
    mpath = archive / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {}
    failures = 0
    for fx in fixtures:
        name = fx.name[: -len(".r2x.txt")]
        h = record.read(fx).header
        if h["input-name"] == "File > New":
            inp = None
        else:
            inp = inputs.get(h.get("input-sha256", ""))
            if inp is None:
                print(f"{name}: input {h['input-name']} ({h.get('input-sha256', '?')[:12]}…) "
                      f"not found under --inputs: skipped")
                failures += 1
                continue
            # the same bytes can sit under another name (Response's Newbeam.r2t is r2x's
            # input.r2t), and r2x records the file's name: run it under the fixture's name
            named = archive / "inputs" / h["input-sha256"][:16] / h["input-name"]
            if not named.exists():
                named.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(inp, named)
            inp = named
        out = archive / f"{name}.r2x.txt"
        cmd = command(h, inp, out, worker, a.response_dir or "RESPONSE_DIR")
        if a.dry_run:
            print(shlex.join(cmd))
            continue
        print(f"{name}: capturing", flush=True)
        t = time.monotonic()
        proc = subprocess.run(cmd, capture_output=True, text=True)
        took = round(time.monotonic() - t, 1)
        entry = {"command": shlex.join(cmd), "made": dt.datetime.now().isoformat(timespec="seconds"),
                 "seconds": took, "exit": proc.returncode}
        if proc.returncode != 0 or not out.exists():
            entry["stderr"] = proc.stderr[-2000:]
            print(f"{name}: r2x failed (exit {proc.returncode})\n{proc.stderr[-500:]}")
            failures += 1
        else:
            entry["sha256"] = sha256(out)
            entry["bytes"] = out.stat().st_size
            entry["check"] = check(out, fx)
            ok = entry["check"]["matches"]
            failures += 0 if ok else 1
            print(f"{name}: {took} s, {'matches the fixture' if ok else 'DIFFERS from the fixture'}")
        manifest[name] = entry
        mpath.write_text(json.dumps(manifest, indent=1))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
