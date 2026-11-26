"""Response's own handling of the shear strain profile (docs/kernel.md, "The shear strain
profile between passes"): in use since step A-2 (D49). Its tests on every pass and its
solve of the global strains are written and off."""

import numpy as np

from r2c import run
from r2c.shear import Shear


def _driver():
    su = run.setup(None, increment=(0.0, 1.0, 1.0))
    return su, su.driver()


def test_response_s_own_solve_is_on_and_the_override_is_in_force():
    # owner, 2026-11-25 (docs/brief.md): Response's own solve of a stage is on, and the
    # "carry on" override is kept in force explicitly
    assert Shear.own_solve is True and Shear.parabolic_error is True
    assert Shear.carry_on is True and Shear.carried_from is None
    assert Shear.pass_code is False


def test_the_override_takes_over_once_and_only_while_the_load_holds():
    from types import SimpleNamespace as NS
    su, drv = _driver()
    drv.mode0 = "phi"
    drv.stages = [NS(lam=0.0), NS(lam=100.0), NS(lam=95.0)]
    assert drv._carry_on(NS(lam=70.0), 100.0) is False      # the load has fallen: an end
    assert drv.carried_from is None and drv.own_solve is True
    assert drv._carry_on(NS(lam=95.0), 100.0) is True
    assert drv.carried_from == 3
    assert drv.own_solve is False and drv.parabolic_error is False
    assert Shear.own_solve is True                          # this response alone
    assert drv._carry_on(NS(lam=95.0), 100.0) is False      # once in a response
    off = _driver()[1]
    off.carry_on = False
    off.stages = drv.stages
    assert off._carry_on(NS(lam=95.0), 100.0) is False      # off: ends as Response does


def test_the_fallback_wants_a_response_that_passes_the_stage_and_goes_on():
    from types import SimpleNamespace as NS
    from r2c import run
    d = NS(mode0="phi", control_of=lambda s, mode=None: s.phi)
    mine = [NS(phi=x, lam=y) for x, y in ((0, 0), (1, 80), (2, 100))]
    on = [NS(phi=x, lam=y) for x, y in ((0, 0), (1, 80), (2, 99), (3, 90))]
    assert run._carries_on(d, mine, d, on) is True
    ends = on[:3]
    assert run._carries_on(d, mine, d, ends) is False       # nothing beyond the stage
    elsewhere = [NS(phi=x, lam=y) for x, y in ((0, 0), (1, 60), (2, 75), (3, 80))]
    assert run._carries_on(d, mine, d, elsewhere) is False  # does not pass the stage


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
