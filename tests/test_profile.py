"""Response's own handling of the shear strain profile, written and off (docs/kernel.md,
"The shear strain profile between passes")."""

import numpy as np

from r2c import run
from r2c.shear import Shear


def _driver():
    su = run.setup(None, increment=(0.0, 1.0, 1.0))
    return su, su.driver()


def test_the_switches_are_off():
    assert Shear.own_profile is False
    assert Shear.own_solve is False
    assert Shear.pass_code is False


def test_update_leaves_a_converged_profile_as_it_is_but_for_its_scale():
    su, drv = _driver()
    an, sec = su.analysis, su.analysis.sec
    z, vstate, tau, t, _d = drv.shear_flow(-1e-5, 1e-6, 1e-4, 50e3)
    before = np.interp(an.profile_z(z), an.shape_z, an.shape)
    # the calculated stress equal to the state's: every node keeps its share
    drv.update_profile(z, vstate, vstate.copy(), t, 1e-4)
    after = np.interp(an.profile_z(z), an.shape_z, an.shape)
    inner = np.ones(z.shape, dtype=bool)
    inner[0, 0] = inner[-1, 2] = False
    ratio = after[inner] / before[inner]
    assert np.allclose(ratio, ratio[0], rtol=1e-6)
    # nothing at the two faces, and a mean of one over the depth by Simpson's rule
    assert after[0, 0] == 0.0 and after[-1, 2] == 0.0
    dz = z[:, 0] - z[:, 2]
    mean = float(np.sum(dz * (after[:, 0] + 4.0 * after[:, 1] + after[:, 2]) / 6.0)) / sec.h
    assert abs(mean - 1.0) < 1e-6


def test_update_moves_a_node_halfway_and_no_more_than_tenfold():
    su, drv = _driver()
    an = su.analysis
    z, vstate, tau, t, _d = drv.shear_flow(-1e-5, 1e-6, 1e-4, 50e3)
    before = np.interp(an.profile_z(z), an.shape_z, an.shape)
    k = z.shape[0] // 2
    calc = vstate.copy()
    calc[k, 1] = 3.0 * vstate[k, 1]          # the mean of one and three: twice
    calc[k + 1, 1] = 1e6 * vstate[k + 1, 1]  # held at ten
    drv.update_profile(z, vstate, calc, t, 1e-4)
    after = np.interp(an.profile_z(z), an.shape_z, an.shape)
    base = after[1, 1] / before[1, 1]
    assert abs(after[k, 1] / before[k, 1] / base - 2.0) < 1e-6
    assert abs(after[k + 1, 1] / before[k + 1, 1] / base - 10.0) < 1e-6


def test_no_shear_strain_yet_leaves_the_profile():
    su, drv = _driver()
    an = su.analysis
    z, vstate, tau, t, _d = drv.shear_flow(-1e-5, 1e-6, 1e-4, 50e3)
    before = np.interp(an.profile_z(z), an.shape_z, an.shape)
    drv.update_profile(z, vstate, 5.0 * vstate, t, 0.0)
    after = np.interp(an.profile_z(z), an.shape_z, an.shape)
    inner = np.ones(z.shape, dtype=bool)
    inner[0, 0] = inner[-1, 2] = False
    ratio = after[inner] / before[inner]
    assert np.allclose(ratio, ratio[0], rtol=1e-6)
