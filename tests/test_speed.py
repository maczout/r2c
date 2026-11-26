"""A speed change changes no result (owner, 2026-11-26; docs/brief.md).

The whole check is on the records: tests/oracle/records.json holds the hash of r2c's record
for every development case, tests/test_oracle.py holds each case it solves to it, and a
full verify run is held to it with `python tools/same.py RUN`. Here: that file covers the
development set, and the node store (the transverse solve kept by node) gives the batch
solve's numbers bit for bit on the first calls of a case with shear.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import same  # noqa: E402
import shadow  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_every_development_case_has_its_record_s_hash():
    cases = {p.name[: -len(".r2x.txt")] for p in (ROOT / "tests" / "oracle").glob("*.r2x.txt")}
    data = same.load()
    assert set(data["sha256"]) == cases
    assert all(len(h) == 64 for h in data["sha256"].values())
    assert data["made_on"].get("numpy")


def test_the_node_store_gives_the_batch_solve_bit_for_bit():
    # Newbeam at M/V = 1 m, the first 400 transverse solves (the uncracked stages and the
    # first cracked ones): every field of every node, compared as bits
    n, differs = shadow.shadow("newbeam-mv", calls=400)
    assert n == 400 and not differs, differs
