"""The slopes of the compressive stress as Response's node stiffness takes them
(docs/kernel.md, "The stiffness in the shear flow calculation"; B 004ac960): written in
step A-5, in use since step A-6 (docs/summary.md, D69)."""

import numpy as np
import pytest

from r2c.inputs import Concrete
from r2c.materials import ConcreteLaw
from r2c.shear import Shear

E2 = -np.array([1e-4, 5e-4, 1e-3, 1.5e-3, 1.9e-3])
E1 = np.array([0.0, 2e-4, 1e-3, 3e-3, 6e-3])
D = 1e-8


def _differences(law):
    f = lambda p, q: law._compression(p, q)[0]      # noqa: E731
    return (f(E2 + D, E1) - f(E2 - D, E1)) / (2 * D), (f(E2, E1 + D) - f(E2, E1)) / D


def test_the_switch_is_on():
    assert Shear.own_slopes is True


@pytest.mark.parametrize("c_mod", [0, 1, 2, 3])
def test_without_softening_they_are_the_slopes_of_the_curve(c_mod):
    law = ConcreteLaw(Concrete(fcp=40.0, c_mod=c_mod, c_soft=0))
    a, b = law.compression_slopes(E2, E1)
    an, _bn = _differences(law)
    assert np.allclose(a, an, rtol=1e-4, atol=1.0)
    assert not b.any()


@pytest.mark.parametrize("c_soft", [2, 10, 13, 18])
def test_softening_by_the_tension_alone_on_a_parabola_is_the_slope(c_soft):
    # a parabola has no exponent for the softening to change, so here the program's two
    # slopes are those of the stress relation
    law = ConcreteLaw(Concrete(fcp=40.0, c_mod=1, c_soft=c_soft))
    a, b = law.compression_slopes(E2, E1)
    an, bn = _differences(law)
    assert np.allclose(a, an, rtol=1e-4, atol=1.0)
    assert np.allclose(b, bn, rtol=1e-3, atol=1.0)


@pytest.mark.parametrize("c_soft", [1, 3, 8, 11])
def test_models_the_program_gives_no_softening_slope(c_soft):
    law = ConcreteLaw(Concrete(fcp=60.0, c_soft=c_soft))
    _a, b = law.compression_slopes(E2, E1)
    _an, bn = _differences(law)
    assert not b.any()
    if c_soft != 8:                        # (Noguchi is at its bound of 1 at these strains)
        assert np.abs(bn).max() > 100.0    # the relation itself does change with the tension


def test_the_default_model_leaves_out_the_change_of_the_exponent():
    law = ConcreteLaw(Concrete(fcp=60.0))
    a, b = law.compression_slopes(E2, E1)
    an, bn = _differences(law)
    assert np.allclose(a, an, rtol=1e-4)
    soft = bn > 1.0
    assert soft.any() and (b[soft] > bn[soft]).all()
    assert np.allclose(b[soft], bn[soft], rtol=0.2)
