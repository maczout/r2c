"""r2c against records captured from Response-2000 with r2x (tests/oracle).

The development set (docs/summary.md, D16 and D41: Newbeam with only its loads varied, and
since step A-1 the seven cases on the Quick Define sections, since step A-2 five cases whose
variable is the reinforcement, since step A-3 eight whose variable is a material model, since step
A-5 one compression softening model on the I-girder and 14 cases on the settings of the
section, units, material factors and More Detail, since step A-6 the three loads that were
not in it: shrinkage, a thermal gradient, where the axial load acts) is
in tests/oracle and is what runs by default. The Quick Define inputs are r2x's: without
R2C_DEFINE_DIR those tests are skipped; the inputs of the cases of steps A-2 and A-3 are
variants of r2x's (tools/variants.py): without R2C_SCOPE_DIR those tests are skipped. Every other case is parked (D19): its fixture is in tests/oracle/parked and its test
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
# Parked: Newbeam with no input
BUILT_IN = {
    "newbeam-new": (0.05, 0.1),
}
# Step A-5 of the development set (owner, 2026-11-24, D68): the settings of the section,
# units, material factors and More Detail, on Newbeam. Those on Newbeam's own input need no
# file; the others' inputs are variants of r2x's, as for SCOPE
SETTINGS = {
    "newbeam-csa": (0.05, 0.1),
    "newbeam-us": (0.05, 0.1),
    "newbeam-kgcm": (0.1, 0.2),
    "newbeam-m-md2": (0.05, 0.1),
    "newbeam-m-mdmax": (0.05, 0.1),
}
SETTINGS_FILE = {
    "newbeam-usfile-si-m": (0.05, 0.1),
    "newbeam-csafile-m": (0.05, 0.1),
    "newbeam-csafile-none-m": (0.05, 0.1),
}
SETTINGS_SLOW = {
    # through Response's load drop and recovery, stepping in the shear strain. r2c steps
    # over the lowest point of the drop, which is the 13 % on the moment-curvature chart.
    # The limit on the peak is as it was set before step A-1; r2c has been over it since
    # (1.4 and 1.6 % at step A-5) and the test fails. Left as it is: docs/summary.md, D69
    "newbeam-us-mv": (1.3, 14.0),
    # at the run of step A-5 when the cases joined (2026-11-24)
    "newbeam-csa-mv": (0.1, 0.3),
    "newbeam-mv-md2": (0.1, 0.2),
}
SETTINGS_FILE_SLOW = {
    "newbeam-smx-mv": (0.1, 0.2),
    "newbeam-usfile-mv": (1.4, 4.3),
    "newbeam-kgcmfile-mv": (0.1, 0.2),
}
# Response's sample inputs: each holds several sections, of which Response opens the first,
# and Liping LB1 has horizontal ties besides. r2c reads them as r2x does; no regression
# limit is set on them yet.
SAMPLES = ("marshall-m", "marshall-nonly", "marshall-asis", "cm4-asis", "liping-asis",
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
    # at the baseline of step A-1 (2026-11-22)
    "igirder-mv": (0.2, 0.3),
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
    "newbeam-negelev-m": (0.05, 0.1),
}
# Step A-6 of the development set (owner, 2026-11-24, D73): the loads that were not in it,
# on Newbeam under M: where the axial load acts, shrinkage, a thermal gradient. Inputs as
# for SCOPE; the limits are those the cases had while parked
LOADS = {
    "newbeam-axialloc-nm": (0.05, 0.1),
    "newbeam-shrink-m": (0.1, 0.8),
    "newbeam-thermgrad-m": (0.05, 0.3),
}
# Step A-2 of the development set (owner, 2026-11-23, D50): the reinforcement varied on
# shapes already in the set. Inputs as for SCOPE
REINF = {
    "newbeam-bardep-m": (0.05, 0.1),
    "newbeam-bartherm-m": (0.05, 0.1),
}
# at the "before" run of step A-2 (2026-11-23)
REINF_SLOW = {
    "newbeam-nostirrups-mv": (0.1, 0.5),
    "newbeam-stirrupdep-mv": (0.1, 0.3),
    "column-interlock-mv": (0.4, 1.0),
}
# Step A-3 of the development set (owner, 2026-11-23, D53): a material model varied on
# Newbeam: two concrete base curves under M, five tension stiffening models and the tension
# stiffening factor under M + V. Inputs as for SCOPE
MATERIAL = {
    "newbeam-cmod0-m": (0.05, 0.1),
    "newbeam-cmod3-m": (0.05, 0.1),
}
# at the run before step A-3 (2026-11-23)
MATERIAL_SLOW = {
    "newbeam-tstiff1-mv": (0.2, 0.3),
    "newbeam-tstiff2-mv": (0.1, 0.3),
    "newbeam-tstiff3-mv": (0.1, 0.2),
    "newbeam-tstiff4-mv": (0.1, 0.2),
    # reset at the "before" run of step A-6 (2026-11-24): with the slopes rule on (D69)
    # r2c carries on after Response's last stage and its peak is 1.6 % above Response's
    "newbeam-tstiff6-mv": (1.7, 0.4),
    "newbeam-tsfactor-mv": (0.3, 0.4),
}
# Step A-5 (owner, 2026-11-24, D67): the one softening case on the I-girder that joined the
# set, Vecchio-Collins 1992-A at M/V = 2 m. Limits at the "before" run of step A-5
SOFTENING_SLOW = {
    "igirder-csoft3-m2v": (3.2, 4.0),
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
@pytest.mark.parametrize("case", SAMPLES)
def test_response_samples_are_read(case, parked_dir, response_dir):
    ref = record.read(parked_dir / f"{case}.r2x.txt")
    opt = verify.options(ref.header)
    su = run.setup(response_dir / ref.header["input-name"], initial=opt["initial"],
                   increment=opt["increment"])
    assert su.units.name == "si"
    assert len(inputs.read(response_dir / ref.header["input-name"]).concretes) >= 1


@pytest.mark.slow
@pytest.mark.parametrize("case", sorted(SLOW))
def test_shear(case, oracle_dir):
    ref = record.read(oracle_dir / f"{case}.r2x.txt")
    _check(ref, _solve(ref), *SLOW[case])


@pytest.mark.parametrize("case", sorted(SETTINGS))
def test_settings(case, oracle_dir):
    ref = record.read(oracle_dir / f"{case}.r2x.txt")
    _check(ref, _solve(ref), *SETTINGS[case])


@pytest.mark.slow
@pytest.mark.parametrize("case", sorted(SETTINGS_SLOW))
def test_settings_shear(case, oracle_dir):
    ref = record.read(oracle_dir / f"{case}.r2x.txt")
    _check(ref, _solve(ref), *SETTINGS_SLOW[case])


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
    _scope(case, parked_dir, scope_dirs, SCOPE[case])


def _scope(case, folder, scope_dirs, limits):
    ref = record.read(folder / f"{case}.r2x.txt")
    path = verify.find_input(ref.header["input-name"], ref.header["input-sha256"], scope_dirs)
    if path is None:
        pytest.skip(f"{ref.header['input-name']} is not under R2C_SCOPE_DIR")
    _check(ref, _solve(ref, path), *limits)


@pytest.mark.parametrize("case", sorted(LOADS))
def test_loads(case, oracle_dir, scope_dirs):
    _scope(case, oracle_dir, scope_dirs, LOADS[case])


@pytest.mark.parametrize("case", sorted(REINF))
def test_reinforcement(case, oracle_dir, scope_dirs):
    _scope(case, oracle_dir, scope_dirs, REINF[case])


@pytest.mark.slow
@pytest.mark.parametrize("case", sorted(REINF_SLOW))
def test_reinforcement_shear(case, oracle_dir, scope_dirs):
    _scope(case, oracle_dir, scope_dirs, REINF_SLOW[case])


@pytest.mark.parametrize("case", sorted(MATERIAL))
def test_material_models(case, oracle_dir, scope_dirs):
    _scope(case, oracle_dir, scope_dirs, MATERIAL[case])


@pytest.mark.slow
@pytest.mark.parametrize("case", sorted(MATERIAL_SLOW))
def test_material_models_shear(case, oracle_dir, scope_dirs):
    _scope(case, oracle_dir, scope_dirs, MATERIAL_SLOW[case])


@pytest.mark.slow
@pytest.mark.parametrize("case", sorted(SOFTENING_SLOW))
def test_softening_shear(case, oracle_dir, scope_dirs):
    _scope(case, oracle_dir, scope_dirs, SOFTENING_SLOW[case])


@pytest.mark.parametrize("case", sorted(SETTINGS_FILE))
def test_settings_from_a_file(case, oracle_dir, scope_dirs):
    _scope(case, oracle_dir, scope_dirs, SETTINGS_FILE[case])


@pytest.mark.slow
@pytest.mark.parametrize("case", sorted(SETTINGS_FILE_SLOW))
def test_settings_from_a_file_shear(case, oracle_dir, scope_dirs):
    _scope(case, oracle_dir, scope_dirs, SETTINGS_FILE_SLOW[case])


# The wider development cases: their limits are generated from a verify run
# (python tools/limits.py VERIFY_OUT --write, tests/oracle/limits.json). All are marked
# slow, with shear or without: there are too many for the default run, and a verify run
# is held to the same limits without solving again (python tools/limits.py VERIFY_OUT).
def _generated():
    import json
    p = Path(__file__).parent / "oracle" / "limits.json"
    return json.loads(p.read_text()) if p.exists() else {}


GENERATED = _generated()


@pytest.mark.slow
@pytest.mark.parametrize("case", sorted(GENERATED))
def test_wider_cases(case, oracle_dir):
    import os
    ref = record.read(oracle_dir / f"{case}.r2x.txt")
    dirs = [Path(d) for d in (os.environ.get(k) for k in
                              ("R2C_RESPONSE_DIR", "R2C_DEFINE_DIR", "R2C_SCOPE_DIR")) if d]
    path = None
    if ref.header["input-name"].lower() not in verify.BUILT_IN:
        path = verify.find_input(ref.header["input-name"], ref.header.get("input-sha256"), dirs)
        if path is None:
            pytest.skip(f"{ref.header['input-name']} is not under the folders of inputs")
    _check(ref, _solve(ref, path), *GENERATED[case])


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
