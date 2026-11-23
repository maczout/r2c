"""r2c against records captured from Response-2000 with r2x (tests/oracle).

The development set (docs/summary.md, D16 and D41: Newbeam with only its loads varied, and
since step A-1 the seven cases on the Quick Define sections) is in tests/oracle and is what
runs by default. The Quick Define inputs are r2x's: without R2C_DEFINE_DIR those tests are
skipped. Every other case is parked (D19): its fixture is in tests/oracle/parked and its test
is marked "parked", run on request with `pytest -m parked` (`-m "parked and not slow"` to
leave out the parked shear cases).

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
from r2c import inputs, record, run, stages  # noqa: E402

# case: (limit on the peak load difference, limit on the curve distance), both in percent
# Phase A, without shear
PHASE_A = {
    "newbeam-m": (0.05, 0.1),
    "newbeam-negm": (0.1, 0.2),
    "newbeam-n2000-m": (0.05, 0.5),
    "newbeam-ntension-m": (0.05, 0.1),
    "newbeam-nonly": (0.5, 0.6),
    "newbeam-tension": (0.5, 1.0),
    "newbeam-nm": (0.2, 0.5),
}
# Parked: Newbeam with no input, material factors, other units, More Detail
BUILT_IN = {
    "newbeam-new": (0.05, 0.1),
    "newbeam-csa": (0.05, 0.1),
    "newbeam-us": (0.05, 0.1),
    "newbeam-kgcm": (0.1, 0.2),
    "newbeam-m-md2": (0.05, 0.1),
    "newbeam-m-mdmax": (0.05, 0.1),
}
# Response's sample inputs that hold several sections in one file, and Liping LB1 with its
# horizontal ties besides: refused since 2026-11-22 (D23). Their fixtures are kept (D19).
REFUSED_SAMPLES = ("marshall-m", "marshall-nonly", "marshall-asis", "cm4-asis", "liping-asis",
                   "se100-asis")
# Step A-1 of the development set (owner, 2026-11-22, D41): the Quick Define sections
# (T-beam, circular column, I-girder with strands). Their inputs are r2x's, found by SHA-256
# under R2C_DEFINE_DIR
DEFINE = {
    "tbeam-m": (0.1, 0.1),
    "tbeam-negm": (0.05, 1.2),
    "column-nonly": (0.05, 0.1),
    "column-n4000-m": (0.05, 0.4),
    "igirder-m": (0.1, 0.4),
}
DEFINE_SLOW = {
    "column-mv": (0.8, 3.0),
}
PARKED_DEFINE_SLOW = {
    # 4.3 % on the moment-curvature chart: Response's load falls and recovers at a curvature
    # of 0.4 rad/km, r2c's rises through it
    "igirder-m2v": (0.9, 5.0),
}
# The scope cases of increment S without shear (docs/scope.md). Their inputs are variants of
# r2x's (tools/variants.py), found by name or SHA-256 under R2C_SCOPE_DIR; the two on Newbeam
# itself need none.
SCOPE = {
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
# Phase A, with shear
SLOW = {
    "newbeam-mv": (0.6, 1.5),
    "newbeam-nmv": (0.6, 2.0),
    # r2c follows Response's curve to its end (0.2 %) and carries on where Response ends:
    # its largest load is 3.7 % above Response's
    "newbeam-m2v": (4.0, 1.0),
    "newbeam-m05v": (0.8, 4.0),
    # the other phase A cases with shear, at the baseline of 2026-11-22
    "newbeam-vonly": (0.2, 1.0),
    "newbeam-ncomp-v": (1.0, 3.2),
    # the largest load is 2.6 % above Response's
    "newbeam-nmv-incr": (3.0, 2.2),
    "newbeam-m0neg-mv": (0.1, 1.9),
    "newbeam-v0-m": (0.05, 0.1),
}
PARKED_SLOW = {
    # through Response's load drop and recovery, stepping in the shear strain. r2c steps
    # over the lowest point of the drop, which is the 13 % on the moment-curvature chart
    "newbeam-us-mv": (1.3, 14.0),
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


@pytest.mark.parametrize("case", sorted(PHASE_A))
def test_phase_a(case, oracle_dir):
    ref = record.read(oracle_dir / f"{case}.r2x.txt")
    _check(ref, _solve(ref), *PHASE_A[case])


@pytest.mark.parked
@pytest.mark.parametrize("case", sorted(BUILT_IN))
def test_built_in_section(case, parked_dir):
    ref = record.read(parked_dir / f"{case}.r2x.txt")
    _check(ref, _solve(ref), *BUILT_IN[case])


@pytest.mark.parked
@pytest.mark.parametrize("case", REFUSED_SAMPLES)
def test_response_samples_are_refused(case, parked_dir, response_dir):
    ref = record.read(parked_dir / f"{case}.r2x.txt")
    with pytest.raises(inputs.OutOfScope, match="several sections"):
        _solve(ref, response_dir / ref.header["input-name"])


@pytest.mark.slow
@pytest.mark.parametrize("case", sorted(SLOW))
def test_shear(case, oracle_dir):
    ref = record.read(oracle_dir / f"{case}.r2x.txt")
    _check(ref, _solve(ref), *SLOW[case])


@pytest.mark.parked
@pytest.mark.slow
@pytest.mark.parametrize("case", sorted(PARKED_SLOW))
def test_parked_shear(case, parked_dir):
    ref = record.read(parked_dir / f"{case}.r2x.txt")
    _check(ref, _solve(ref), *PARKED_SLOW[case])


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


@pytest.mark.parked
@pytest.mark.slow
@pytest.mark.parametrize("case", sorted(PARKED_DEFINE_SLOW))
def test_parked_quick_define_shear(case, parked_dir, define_dirs):
    _define(case, parked_dir, define_dirs, PARKED_DEFINE_SLOW[case])


@pytest.mark.parked
@pytest.mark.parametrize("case", sorted(SCOPE))
def test_scope_cases(case, parked_dir, scope_dirs):
    ref = record.read(parked_dir / f"{case}.r2x.txt")
    path = verify.find_input(ref.header["input-name"], ref.header["input-sha256"], scope_dirs)
    if path is None:
        pytest.skip(f"{ref.header['input-name']} is not under R2C_SCOPE_DIR")
    _check(ref, _solve(ref, path), *SCOPE[case])


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
