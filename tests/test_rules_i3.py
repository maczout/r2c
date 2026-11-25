"""Three rules of the kernel read from the binary on 2026-11-25 (docs/kernel.md)."""

import numpy as np

from r2c import run


def test_a_response_with_shear_is_not_stopped_at_101_stages():
    # Response's own run to 148 stages with shear; only its count of solves ends them
    assert run.setup(None, increment=(0.0, 1.0, 0.0)).max_stages == 101
    assert run.setup(None, increment=(0.0, 1.0, 1.0)).max_stages == 330


def test_with_material_factors_the_stress_is_capped_at_yield_and_the_slope_is_not():
    plain = run.setup(None, increment=(0.0, 1.0, 1.0))
    csa = run.setup(None, increment=(0.0, 1.0, 1.0), factors="csa")
    for su, capped in ((plain, False), (csa, True)):
        st = next(l.steel for l in su.section.layers if not l.steel.prestress)
        e = 0.5 * (st.esh + st.eu)                 # on the hardening branch
        assert (float(st.raw(e)) <= st.fy * (1 + 1e-12)) == capped
        assert float(st.tangent(e)) > 0.0          # [B 004ae630]: no test of the factors
        assert float(st.tangent(0.5 * (st.fy / st.E + st.esh))) == 0.0   # the plateau


def test_axial_tension_is_solved_by_the_general_solve_and_a_uniform_column_is_not():
    su = run.setup(None, increment=(1.0, 0.0, 0.0))
    drv = su.driver()
    stages = drv.run(su.max_stages)
    assert drv._helper is not None                 # Shear._general was used
    loads = np.array([s.n for s in stages])
    k = int(np.argmax(np.diff(loads) < 0))         # the fall at cracking
    # Response has thirteen rising stages before the fall (fixture newbeam-tension);
    # the balanced solve found twelve
    assert k == 12
