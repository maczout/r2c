"""Rules of the kernel read from the binary in increment 5 (docs/kernel.md)."""

import numpy as np
import pytest

from r2c import run


def test_the_profile_error_reads_each_layer_by_its_parabola():
    # [B 00420f20, 00427180, 004b6df0]: the calculated shear stress and the state's are
    # read at 50 points of the depth from the parabola through the three nodes of the
    # layer a point is in. A stress that is a parabola over a layer is then read exactly,
    # which straight lines between the nodes do not do
    su = run.setup(None, increment=(0.0, 1.0, 1.0))
    drv, sec = su.driver(), su.section
    edges = np.linspace(sec.ztop, sec.zbot, 5)
    z = np.stack([edges[:-1], 0.5 * (edges[:-1] + edges[1:]), edges[1:]], axis=1)
    x = (z - sec.zbot) / (sec.ztop - sec.zbot)
    calc = 4.0 * x * (1.0 - x)                  # one parabola over the whole depth
    state = np.ones_like(z) * 0.5
    pts = np.linspace(0.0, 1.0, 50)
    d = 4.0 * pts * (1.0 - pts) - 0.5
    exact = np.std(d, ddof=1) / np.mean(4.0 * pts * (1.0 - pts))
    assert drv.parabolic_error is False        # written and off (docs/kernel.md)
    assert drv.profile_error(z, state, calc, 1e6) != pytest.approx(exact, rel=1e-3)
    drv.parabolic_error = True
    assert drv.profile_error(z, state, calc, 1e6) == pytest.approx(exact, rel=1e-9)


def test_a_step_of_the_stress_between_two_layers_is_read_layer_by_layer():
    # each point is read from its own layer's three nodes, so a step of the stress where
    # two layers meet stays a step [B 00427180: the layer is found first]
    su = run.setup(None, increment=(0.0, 1.0, 1.0))
    drv, sec = su.driver(), su.section
    mid = 0.5 * (sec.ztop + sec.zbot)
    z = np.array([[sec.ztop, 0.5 * (sec.ztop + mid), mid], [mid, 0.5 * (mid + sec.zbot), sec.zbot]])
    calc = np.array([[2.0, 2.0, 2.0], [1.0, 1.0, 1.0]])
    state = np.zeros_like(z)
    # 50 points from the bottom up: 25 in each half, none on the boundary
    drv.parabolic_error = True
    got = drv.profile_error(z, state, calc, 1e6)
    d = np.array([1.0] * 25 + [2.0] * 25)
    assert got == pytest.approx(np.std(d, ddof=1) / np.mean(d), rel=1e-9)


def test_closing_in_on_a_rupture_when_the_try_fails_is_written_and_off(oracle_dir):
    # [B 00415e30, 00419ff0; O: Response's own tries on this case, tools/rtrace.py]: the
    # stage a fifth of the way to the rupture cannot be solved; Response halves its step
    # multiplier and tries half the last kept step on, and its last five stages follow.
    # Off, so that the kernel is the one the held-out set was scored on in increment 5
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import compare
    import verify
    from r2c import record, solver, stages
    assert solver.Flexure.rupture_halving is False
    ref = record.read(oracle_dir / "newbeam-light500-m.r2x.txt")
    path = verify.find_input(ref.header["input-name"], ref.header.get("input-sha256"),
                             [d for d in verify_inputs() if d])
    if path is None:
        pytest.skip("the input of newbeam-light500-m is not at hand")
    want = compare._curve(ref, "moment_phi")
    solver.Flexure.rupture_halving = True
    try:
        res = run.solve(path, **verify.options(ref.header))
    finally:
        solver.Flexure.rupture_halving = False
    got = compare._curve(record.decode(res.record_bytes(stages.ALL)), "moment_phi")
    assert len(got) == len(want) == 73
    assert np.allclose(got[-5:], want[-5:], atol=2e-3)


def verify_inputs():
    import os
    return [os.environ.get(k) for k in ("R2C_SCOPE_DIR", "R2C_RESPONSE_DIR", "R2C_DEFINE_DIR")]
