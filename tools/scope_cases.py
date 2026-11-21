#!/usr/bin/env python3
"""The oracle cases of increment S (docs/scope.md), and how each was first captured.

    python tools/scope_cases.py --list
    python tools/scope_cases.py ARCHIVE --response-dir DIR --inputs DIR [DIR ...]
                                [--only NAME ...] [--group A|B] [--jobs N]

Each case is one feature of docs/scope.md on a section that is already in the test set: an
input (one of the present inputs, or a variant of one from tools/variants.py) and the solve
options. This tool builds the inputs into ARCHIVE/scope-inputs, captures every case that has
no fixture yet with tools/capture.py's --add (every stage, all views) and cuts its fixture
into tests/oracle. Once a fixture exists it is the recipe, as for every other case
(tools/capture.py rebuilds the archive from the fixtures; give it ARCHIVE/scope-inputs, or
the folder tools/variants.py writes, among its --inputs).

--jobs N runs N captures at once, each in a Wine prefix of its own
(~/.cache/r2x/prefix-scope-K); r2x's worker runs one Response per prefix.

Group A: the case exercises a kernel path no earlier case reaches. Group B: a combination
of paths that are each reached already.
"""

from __future__ import annotations

import argparse
import os
import queue
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import capture  # noqa: E402
import variants  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# The inputs that are in the test set already, under the names their fixtures record
PRESENT = {"newbeam": "input.r2t", "tbeam": "tbeam.r2t", "column": "column.r2t",
           "igirder": "igirder.r2t"}


def case(group, name, inp, increment, initial="0,0,0", units="si", factors="none",
         more_detail="0"):
    return dict(group=group, name=name, input=inp, initial=initial, increment=increment,
                units=units, factors=factors, more_detail=more_detail)


CASES = [
    # the brief's list
    case("A", "tbeam-m2v", "tbeam", "0,2,1"),
    case("A", "newbeam-mv-md2", "newbeam", "0,1,1", more_detail="2"),
    case("A", "newbeam-csa-mv", "newbeam", "0,1,1", factors="csa"),
    case("A", "newbeam-usfile-mv", "newbeam-usfile", "0,1,1", units="us"),
    case("A", "newbeam-kgcmfile-mv", "newbeam-kgcmfile", "0,1,1", units="kgcm"),
    case("A", "column-interlock-mv", "column-interlock", "0,1,1"),
    case("A", "newbeam-segsteel-m", "newbeam-segsteel", "0,1,0"),
    # concrete models
    case("A", "newbeam-cmod0-m", "newbeam-cmod0", "0,1,0"),
    case("A", "newbeam-cmod3-m", "newbeam-cmod3", "0,1,0"),
    *[case("A", f"igirder-csoft{n}-m2v", f"igirder-csoft{n}", "0,2,1")
      for n in (0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 14, 15, 16, 17)],
    case("A", "igirder-csoft9-mv", "igirder-csoft9", "0,1,1"),
    case("A", "igirder-csoft11-mv", "igirder-csoft11", "0,1,1"),
    *[case("A", f"newbeam-tstiff{n}-mv", f"newbeam-tstiff{n}", "0,1,1") for n in (1, 2, 3, 4, 6)],
    case("A", "newbeam-tsfactor-mv", "newbeam-tsfactor", "0,1,1"),
    # reinforcement
    case("A", "newbeam-nostirrups-mv", "newbeam-nostirrups", "0,1,1"),
    case("A", "newbeam-stirrupdep-mv", "newbeam-stirrupdep", "0,1,1"),
    case("A", "igirder-drape-m2v", "igirder-drape", "0,2,1"),
    # General settings
    case("A", "newbeam-smx-mv", "newbeam-smx", "0,1,1"),
    case("A", "newbeam-axialloc-nm", "newbeam-axialloc", "0,1,0", initial="-1000,0,0"),
    # strains
    case("A", "newbeam-shrink-m", "newbeam-shrink", "0,1,0"),
    case("A", "newbeam-thermgrad-m", "newbeam-thermgrad", "0,1,0"),
    case("A", "newbeam-bartherm-m", "newbeam-bartherm", "0,1,0"),
    # group B: combinations
    case("B", "igirder-mv", "igirder", "0,1,1"),
    case("B", "newbeam-usfile-si-m", "newbeam-usfile", "0,1,0", units="si"),
    case("B", "newbeam-negelev-m", "newbeam-negelev", "0,1,0"),
    case("B", "newbeam-bardep-m", "newbeam-bardep", "0,1,0"),
    case("B", "newbeam-csafile-m", "newbeam-csafile", "0,1,0", factors="csa"),
    case("B", "newbeam-csafile-none-m", "newbeam-csafile", "0,1,0", factors="none"),
    case("B", "newbeam-ntension-m", "newbeam", "0,1,0", initial="200,0,0"),
    case("B", "newbeam-ncomp-v", "newbeam", "0,0,1", initial="-500,0,0"),
    case("B", "newbeam-v0-m", "newbeam", "0,1,0", initial="0,0,50"),
    case("B", "newbeam-m0neg-mv", "newbeam", "0,1,1", initial="0,-50,0"),
    case("B", "newbeam-nmv-incr", "newbeam", "-5,1,1"),
    case("B", "newbeam-m-mdmax", "newbeam", "0,1,0", more_detail="max"),
]


def input_for(c: dict, folder: Path, sources) -> Path:
    """The case's input, written into the folder under the name its fixture records."""
    if c["input"] in PRESENT:
        p = folder / PRESENT[c["input"]]
        data = variants.find_base(c["input"], sources).read_bytes()
    else:
        p = folder / f"{c['input']}.r2t"
        data = variants.build(c["input"], sources)
    if not p.exists() or p.read_bytes() != data:
        p.write_bytes(data)
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("archive", nargs="?", help="folder for the captures (outside the repository)")
    ap.add_argument("--response-dir", default=os.environ.get("R2X_RESPONSE_DIR"))
    ap.add_argument("--inputs", nargs="*", default=[], help="folders with the present inputs")
    ap.add_argument("--fixtures", default=str(ROOT / "tests" / "oracle"))
    ap.add_argument("--only", nargs="*", help="case names (default: all without a fixture)")
    ap.add_argument("--group", choices=("A", "B"), help="only this group")
    ap.add_argument("--jobs", type=int, default=1, help="captures at once (default: 1)")
    ap.add_argument("--list", action="store_true", help="list the cases and stop")
    a = ap.parse_args(argv)
    cases = [c for c in CASES if (not a.only or c["name"] in a.only)
             and (not a.group or c["group"] == a.group)]
    if a.list:
        for c in cases:
            opts = " ".join(f"{k}={c[k]}" for k in ("units", "factors", "more_detail")
                            if c[k] not in ("si", "none", "0"))
            print(f"{c['group']} {c['name']}: {c['input']}, {c['initial']} + {c['increment']}"
                  + (f", {opts}" if opts else ""))
        return 0
    if not a.archive or not a.response_dir:
        ap.error("ARCHIVE and --response-dir are required")
    archive = Path(a.archive).resolve()
    if ROOT in archive.parents or archive == ROOT:
        ap.error("the archive belongs outside the repository")
    folder = archive / "scope-inputs"
    folder.mkdir(parents=True, exist_ok=True)
    fixtures = Path(a.fixtures)
    todo = [c for c in cases if not (fixtures / f"{c['name']}.r2x.txt").exists()]
    prefixes: queue.Queue = queue.Queue()
    for k in range(max(a.jobs, 1)):
        prefixes.put(Path.home() / ".cache" / "r2x" / f"prefix-scope-{k}")

    def one(c):
        src = input_for(c, folder, a.inputs)
        prefix = prefixes.get()
        try:
            worker = [sys.executable, "-m", "r2x.worker", "--prefix", str(prefix)]
            return capture.add_case(archive, worker, a.response_dir, fixtures, c["name"], src,
                                    c["initial"], c["increment"], c["units"], c["factors"],
                                    c["more_detail"])
        finally:
            prefixes.put(prefix)

    # the inputs are written before the threads start, so that two cases with the same input
    # do not write it at once
    for c in todo:
        input_for(c, folder, a.inputs)
    with ThreadPoolExecutor(max_workers=max(a.jobs, 1)) as ex:
        failed = sum(ex.map(one, todo))
    capture.merge_manifest(archive)
    print(f"{len(todo) - failed} captured, {failed} failed, "
          f"{len(cases) - len(todo)} had a fixture already")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
