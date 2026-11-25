"""Rules of the kernel read from the binary in increment 4 (docs/kernel.md)."""

import numpy as np
import pytest

from r2c import run


def _tapered():
    """Newbeam's section with its outline changed to a web that widens downward into a
    flange: 250 mm from 600 down to 200, a taper to 500 mm at 100, 500 mm to the bottom."""
    su = run.setup(None, increment=(0.0, 1.0, 0.0))
    sec = su.section
    law = sec.segs[0][4]
    sec.segs = [(600.0, 200.0, 250.0, 250.0, law), (200.0, 100.0, 250.0, 500.0, law),
                (100.0, 0.0, 500.0, 500.0, law)]
    return sec


def test_the_bond_parameters_concrete_area_takes_a_taper_at_its_upper_width():
    sec = _tapered()
    # the taper wholly inside the range: its upper width, not its trapezoid [B 004fd7c0]
    assert sec.bond_area(0.0, 300.0) == pytest.approx(100 * 500 + 100 * 250 + 100 * 250)
    assert sec.area_between(0.0, 300.0) == pytest.approx(100 * 500 + 100 * 375 + 100 * 250)
    # the range ends inside the taper from below: the cut's width with the upper width
    assert sec.bond_area(0.0, 150.0) == pytest.approx(100 * 500 + 50 * 0.5 * (375 + 250))
    # the range starts inside the taper: a true trapezoid
    assert sec.bond_area(150.0, 300.0) == pytest.approx(50 * 0.5 * (375 + 250) + 100 * 250)
    # a range within the taper: as it is
    assert sec.bond_area(120.0, 180.0) == pytest.approx(sec.area_between(120.0, 180.0))


def test_on_prismatic_parts_the_bond_area_is_the_area():
    sec = run.setup(None, increment=(0.0, 1.0, 0.0)).section
    for lo, hi in ((0.0, 600.0), (37.0, 211.5), (300.0, 300.0)):
        assert sec.bond_area(lo, hi) == pytest.approx(sec.area_between(lo, hi))


def test_the_bond_parameter_is_the_lesser_of_the_two_tables_each_read_at_the_height():
    sec = run.setup(None, increment=(0.0, 1.0, 1.0)).section
    z = np.linspace(sec.zbot, sec.ztop, 37)
    want = np.minimum(np.interp(z, sec.tz, sec.t_mlong), np.interp(z, sec.tz, sec.t_mtrans))
    assert np.allclose(sec.bond_m(z), want)
    # the stirrups' term: bar perimeter over width times spacing plus 1e-4 m2 [B 004ff1a0]
    s = sec.stirrups[0]
    mid = 0.5 * (s.top + s.bot)
    b = float(sec.width(np.array([mid]))[0])
    t = s.db * np.pi * s.legs / (b * s.space + 100.0)
    assert float(np.interp(mid, sec.tz, sec.t_mtrans)) == pytest.approx(3.6 / (t + 1e-7))
