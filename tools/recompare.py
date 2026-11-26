#!/usr/bin/env python3
"""Compare the records of a verify run again with the measure as it is now, without solving.

    python tools/recompare.py VERIFY_OUT [FIXTURES]

Answers "what does a change to the measure alone do to a run?": r2c's records in
VERIFY_OUT (a tools/verify.py output on development fixtures) are compared with the
fixtures again and VERIFY_OUT's results are rewritten, so that tools/changes.py can set the
run before the change beside it. Give it a copy of the run. Never anything of the held-out
set.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
from r2c import record  # noqa: E402


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or "heldout" in str(Path(argv[0]).resolve()):
        print(__doc__)
        return 2
    vo = Path(argv[0])
    fx = Path(argv[1]) if len(argv) > 1 else ROOT / "tests" / "oracle"
    res = json.loads((vo / "results.json").read_text())
    for name, r in res.items():
        sub = vo / f"{name}.r2x.txt"
        if "control" not in r or not sub.exists():
            continue
        new = cmp.compare(record.read(fx / f"{name}.r2x.txt"), record.read(sub), views=True)
        new["seconds"] = r.get("seconds")
        res[name] = new
        (vo / f"{name}.json").write_text(json.dumps(new, indent=1))
    (vo / "results.json").write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
