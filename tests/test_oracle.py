"""r2c against records captured from Response-2000 with r2x (tests/oracle).

These are regression tests. The limits are a little above the differences found when the cases
were last compared (docs/verification.md); they say "no worse than it was", not "close enough
to use". Shear cases take a minute or more each and are marked slow.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import compare  # noqa: E402
import verify  # noqa: E402
from r2c import record, run, stages  # noqa: E402

# case: (limit on the peak load difference, limit on the curve distance), both in percent
BUILT_IN = {
    "newbeam-m": (0.05, 0.1),
    "newbeam-new": (0.05, 0.1),
    "newbeam-negm": (0.1, 0.2),
    "newbeam-csa": (0.05, 0.1),
    "newbeam-n2000-m": (0.05, 0.5),
    "newbeam-nonly": (0.5, 0.6),
    "newbeam-tension": (0.5, 1.0),
    "newbeam-nm": (0.2, 0.5),
    "newbeam-us": (0.05, 0.1),
    "newbeam-kgcm": (0.1, 0.2),
    "newbeam-m-md2": (0.05, 0.1),
}
SAMPLES = {
    "marshall-m": (0.05, 0.1),
    "marshall-nonly": (0.05, 0.1),
    "cm4-asis": (0.2, 0.5),
}
# Quick Define sections (T-beam, circular column, I-girder with strands): their inputs are
# r2x's, found by SHA-256 under R2C_DEFINE_DIR
DEFINE = {
    "tbeam-m": (0.1, 0.1),
    "tbeam-negm": (0.05, 1.2),
    "column-nonly": (0.05, 0.1),
    "column-n4000-m": (0.05, 0.4),
    "igirder-m": (0.1, 0.4),
}
DEFINE_SLOW = {
    "column-mv": (0.8, 3.0),
    # 4.3 % on the moment-curvature chart: Response's load falls and recovers at a curvature
    # of 0.4 rad/km, r2c's rises through it
    "igirder-m2v": (0.9, 5.0),
}
# The scope cases of increment S without shear (docs/scope.md). Their inputs are variants of
# r2x's (tools/variants.py), found by name or SHA-256 under R2C_SCOPE_DIR; the two on Newbeam
# itself need none.
SCOPE = {
    "newbeam-segsteel-m": (0.05, 0.1),
    "newbeam-cmod0-m": (0.05, 0.1),
    "newbeam-cmod3-m": (0.05, 0.1),
    "newbeam-axialloc-nm": (0.05, 0.1),
    "newbeam-shrink-m": (0.1, 0.8),
    "newbeam-thermgrad-m": (0.05, 0.3),
    "newbeam-bartherm-m": (0.05, 0.1),
    "newbeam-usfile-si-m": (0.05, 0.1),
    "newbeam-negelev-m": (0.05, 0.1),
    "newbeam-bardep-m": (0.05, 0.1),
    "newbeam-csafile-m": (0.05, 0.1),
    "newbeam-csafile-none-m": (0.05, 0.1),
}
SCOPE_BUILT_IN = {
    "newbeam-ntension-m": (0.05, 0.1),
    "newbeam-m-mdmax": (0.05, 0.1),
}
SLOW = {
    "newbeam-mv": (0.6, 1.5),
    "newbeam-nmv": (0.6, 2.0),
    # r2c follows Response's curve to its end (0.2 %) and carries on where Response ends:
    # its largest load is 3.7 % above Response's
    "newbeam-m2v": (4.0, 1.0),
    # through Response's load drop and recovery, stepping in the shear strain. r2c steps
    # over the lowest point of the drop, which is the 13 % on the moment-curvature chart
    "newbeam-us-mv": (1.3, 14.0),
    "newbeam-m05v": (0.8, 4.0),
}


def _solve(ref, path=None):
    res = run.solve(path, **verify.options(ref.header))
    return record.decode(res.record_bytes(stages.ALL))


def _check(ref, sub, peak_limit, curve_limit):
    res = compare.compare(ref, sub)
    assert res["control"], "no control chart in common"
    for c in res["control"]:
        assert abs(c["peak_diff_pct"]) <= peak_limit, c
        if "curve_max_diff_pct" in c:
            assert c["curve_max_diff_pct"] <= curve_limit, c


@pytest.mark.parametrize("case", sorted(BUILT_IN))
def test_built_in_section(case, oracle_dir):
    ref = record.read(oracle_dir / f"{case}.r2x.txt")
    _check(ref, _solve(ref), *BUILT_IN[case])


@pytest.mark.parametrize("case", sorted(SAMPLES))
def test_response_samples(case, oracle_dir, response_dir):
    ref = record.read(oracle_dir / f"{case}.r2x.txt")
    _check(ref, _solve(ref, response_dir / ref.header["input-name"]), *SAMPLES[case])


@pytest.mark.slow
@pytest.mark.parametrize("case", sorted(SLOW))
def test_shear(case, oracle_dir):
    ref = record.read(oracle_dir / f"{case}.r2x.txt")
    _check(ref, _solve(ref), *SLOW[case])


def _define(case, oracle_dir, define_dirs, limits):
    ref = record.read(oracle_dir / f"{case}.r2x.txt")
    path = verify.find_input(ref.header["input-name"], ref.header["input-sha256"], define_dirs)
    if path is None:
        pytest.skip(f"{ref.header['input-name']} is not under R2C_DEFINE_DIR")
    _check(ref, _solve(ref, path), *limits)


@pytest.mark.parametrize("case", sorted(DEFINE))
def test_quick_define_sections(case, oracle_dir, define_dirs):
    _define(case, oracle_dir, define_dirs, DEFINE[case])


@pytest.mark.slow
@pytest.mark.parametrize("case", sorted(DEFINE_SLOW))
def test_quick_define_shear(case, oracle_dir, define_dirs):
    _define(case, oracle_dir, define_dirs, DEFINE_SLOW[case])


@pytest.mark.parametrize("case", sorted(SCOPE))
def test_scope_cases(case, oracle_dir, scope_dirs):
    ref = record.read(oracle_dir / f"{case}.r2x.txt")
    path = verify.find_input(ref.header["input-name"], ref.header["input-sha256"], scope_dirs)
    if path is None:
        pytest.skip(f"{ref.header['input-name']} is not under R2C_SCOPE_DIR")
    _check(ref, _solve(ref, path), *SCOPE[case])


@pytest.mark.parametrize("case", sorted(SCOPE_BUILT_IN))
def test_scope_cases_on_newbeam(case, oracle_dir):
    ref = record.read(oracle_dir / f"{case}.r2x.txt")
    _check(ref, _solve(ref), *SCOPE_BUILT_IN[case])


def test_same_charts_as_the_oracle(oracle_dir):
    """The record has the sections r2x's has: same control charts, same charts per stage."""
    ref = record.read(oracle_dir / "newbeam-m.r2x.txt")
    sub = _solve(ref)
    assert compare.control_keys(sub) == compare.control_keys(ref)
    rp = int(ref.header["peak-stage"])
    sp = int(sub.header["peak-stage"])
    ref_keys = [k.split("/", 2)[2] for k in ref.sections if k.startswith(f"stage/{rp}/")]
    sub_keys = [k.split("/", 2)[2] for k in sub.sections if k.startswith(f"stage/{sp}/")]
    assert sub_keys == ref_keys
    for k in ("units", "factors", "initial", "increment", "more-detail", "views"):
        assert sub.header[k] == ref.header[k], k


def test_zero_increment(oracle_dir):
    ref = record.read(oracle_dir / "newbeam-zero.r2x.txt")
    sub = _solve(ref)
    assert sub.header["stage-count"] == ref.header["stage-count"] == "2"
