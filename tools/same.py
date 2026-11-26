#!/usr/bin/env python3
"""Is every development record the same as before?

    python tools/same.py RUN              hold a verify run's records to the committed hashes
    python tools/same.py BEFORE AFTER     compare two verify runs' records, byte for byte
    python tools/same.py RUN --write      record the run's hashes (after a change of result)

Answers the owner's rule for speed (2026-11-26): r2c is made faster without changing a
single result; every development record must be identical before and after a speed
change. tests/oracle/records.json holds the SHA-256 of r2c's whole record (every stage,
every view, as tools/verify.py writes it) for each development case. A speed commit
leaves that file alone and a full verify run after it must pass `same.py RUN`; a commit
that changes results on purpose rewrites it with --write, in the same commit, and says
so. tests/test_oracle.py holds every case it solves to the same hashes, so `pytest` (the
cases without shear) and `pytest -m slow` check it too.

The hashes are those of the machine that made them (numpy's version and the processor
are recorded with them): on another machine a last digit may print differently, and the
tests then skip the comparison rather than fail. Development runs only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "tests" / "oracle" / "records.json"


def made_on() -> dict:
    cpu = ""
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    return {"numpy": np.__version__, "python": platform.python_version(),
            "machine": platform.machine(), "processor": cpu}


def load() -> dict:
    return json.loads(RECORDS.read_text()) if RECORDS.exists() else {"made_on": {}, "sha256": {}}


def here() -> bool:
    """Whether the committed hashes were made on a machine like this one."""
    return load()["made_on"] == made_on()


def digest(data: bytes) -> str:
    """The hash of a record without the line that names the input file: the same input is
    found under one name by tools/verify.py and under another by the tests (the Quick
    Define sections are all called hand.r2t in r2x), and the name is no result."""
    head, sep, rest = data.partition(b"\ninput-name:")
    if sep:
        data = head + rest[rest.index(b"\n"):]
    return hashlib.sha256(data).hexdigest()


def expected(name: str) -> str | None:
    return load()["sha256"].get(name)


def of_run(run: Path) -> dict:
    return {p.name[: -len(".r2x.txt")]: digest(p.read_bytes())
            for p in sorted(run.glob("*.r2x.txt"))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", nargs="+")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if any("heldout" in r or "finish" in r for r in a.run) or len(a.run) > 2:
        raise SystemExit(__doc__)
    cases = {p.name[: -len(".r2x.txt")] for p in (ROOT / "tests" / "oracle").glob("*.r2x.txt")}
    got = of_run(Path(a.run[-1]))
    if a.write:
        missing = sorted(cases - set(got))
        if missing:
            raise SystemExit(f"{len(missing)} development cases have no record in the run: "
                             + ", ".join(missing[:8]))
        RECORDS.write_text(json.dumps(
            {"made_on": made_on(), "sha256": {n: got[n] for n in sorted(cases)}}, indent=1) + "\n")
        print(f"{RECORDS.relative_to(ROOT)}: {len(cases)} hashes written")
        return 0
    if len(a.run) == 2:
        want, what = of_run(Path(a.run[0])), "the first run"
    else:
        want, what = load()["sha256"], "the committed hashes"
    both = sorted(set(want) & set(got) & cases)
    differ = [n for n in both if want[n] != got[n]]
    absent = sorted((cases & set(want)) - set(got))
    print(f"{len(both)} development records compared with {what}: "
          f"{len(both) - len(differ)} identical, {len(differ)} differ"
          + (f"; {len(absent)} not in the run" if absent else ""))
    for n in differ:
        print(f"  differs: {n}")
    return 1 if differ else 0


if __name__ == "__main__":
    raise SystemExit(main())
