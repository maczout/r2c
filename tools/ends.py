#!/usr/bin/env python3
"""How each shear response ends in r2c, against how Response's ends.

Answers: "Response's last stage is often a collapsed one, at a fraction of the peak load;
does r2c find such a state and discard it, or never find one?" r2c's driver drops a stage
with less than half of the peak load left (Shear.collapsed) and otherwise ends when no state
is found. This runs every case with a shear increment and reports, for Response, its last
stage's load over its peak, and for r2c, the number of stages and each state its collapse
rule discarded.

    python tools/ends.py tests/oracle --inputs DIR [DIR ...] [--jobs N]

Found 2026-11-21: Response ends on a collapsed stage in five of twelve cases (12 to 66 % of
the peak); r2c discards none anywhere, so it never finds one. Its responses end where its
iteration finds no state.
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
import verify  # noqa: E402
from r2c import record, run  # noqa: E402
from r2c.shear import Shear  # noqa: E402


def one(args):
    path, inputs = args
    ref = record.read(path)
    if float(ref.header["increment"].split(",")[2]) == 0.0:
        return None
    name = Path(path).name[: -len(".r2x.txt")]
    c = cmp._curve(ref, cmp.control_keys(ref)[0])
    last = abs(c[-1, 1]) / max(abs(c[:, 1]).max(), 1e-12)
    src = ref.header["input-name"]
    inp = None
    if src.lower() not in verify.BUILT_IN:
        inp = verify.find_input(src, ref.header.get("input-sha256"), inputs)
        if inp is None:
            return name, last, None, [f"input {src} not found"]
    log = []
    orig = Shear.collapsed

    def collapsed(self, st, peak):
        r = orig(self, st, peak)
        if r:
            log.append(f"discarded: control {st.control:.4g}, {st.lam / peak:.2f} of the peak, "
                       f"control variable {self.mode}")
        return r
    Shear.collapsed = collapsed
    try:
        res = run.solve(inp, **verify.options(ref.header))
    finally:
        Shear.collapsed = orig
    return name, last, len(res.stages), log


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("reference_dir")
    ap.add_argument("--inputs", nargs="+", default=[])
    ap.add_argument("--jobs", type=int, default=1)
    a = ap.parse_args(argv)
    work = [(str(p), a.inputs) for p in sorted(Path(a.reference_dir).glob("*.r2x.txt"))]
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        for r in ex.map(one, work):
            if r is None:
                continue
            name, last, n, log = r
            print(f"{name}: Response's last stage at {last:.2f} of its peak; r2c "
                  f"{n} stages; " + ("; ".join(log) if log else "nothing discarded"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
