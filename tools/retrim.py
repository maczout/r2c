#!/usr/bin/env python3
"""Re-cut the oracle fixtures from the full captures, keeping the detail views of every
feature stage of Response's curve.

    python tools/retrim.py ARCHIVE [--oracle tests/oracle] [--dry-run]

The owner's targets (docs/acceptance.md, 2026-11-21) ask for the detail views to agree away
from the peak too. Views are compared at the features of Response's control curve (cracking,
falls of load, the peak, the last stage: tools/compare.py, feature_stages), so each fixture
must hold those stages. The fixtures were cut to the peak only.

Since the owner's rule on unstable views (2026-11-23, D54; docs/acceptance.md, "Where
Response is unstable") each fixture also holds Response's views at the stage just before and
just after each compared stage, as neighbours (tools/trim.py says how, and which are
needed). This tool adds them.

ARCHIVE is the folder tools/capture.py wrote (ARCHIVE/NAME.r2x.txt, every stage). For each
fixture this tool first checks that the capture, cut the way the fixture was, matches it
byte for byte (tools/capture.py's check): a capture that does not is reported and that
fixture left alone. It then cuts the capture again, keeping the stages the fixture had plus
the feature stages, and their neighbours, and writes the fixture. tools/capture.py's check reads the stages to keep
from each fixture, so it carries on working with the new fixtures unchanged.

Needs no Response, only the archive. --dry-run prints the stages each fixture would keep.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from r2c import record  # noqa: E402

import capture  # noqa: E402
import compare  # noqa: E402
import trim  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("archive", help="the folder of full captures (tools/capture.py)")
    ap.add_argument("--oracle", default=str(ROOT / "tests" / "oracle"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    archive, oracle = Path(a.archive), Path(a.oracle)
    bad = 0
    for fx in sorted(oracle.glob("*.r2x.txt")):
        cap = archive / fx.name
        if not cap.exists():
            print(f"{fx.name}: no capture in {archive}")
            bad += 1
            continue
        chk = capture.check(cap, fx)
        if not chk["matches"]:
            print(f"{fx.name}: capture does not match the fixture, left alone: {chk}")
            bad += 1
            continue
        rec = record.read(cap)
        feats = compare.feature_stages(rec)
        keep = sorted(set(record.read(fx).stages()) | set(feats))
        near = trim.near_needed(rec, keep)
        desc = ", ".join(f"{n} ({feats.get(n, 'kept')})" for n in keep)
        desc += "; neighbours " + (", ".join(map(str, near)) or "none")
        if a.dry_run:
            print(f"{fx.name}: {desc}")
            continue
        data = trim.trim(rec, keep, near)
        fx.write_bytes(data)
        print(f"{fx.name}: {desc}; {len(data) / 1024:.0f} kB")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
