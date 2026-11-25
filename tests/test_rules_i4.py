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


def test_the_tent_of_the_bond_parameter_reaches_as_far_as_the_spacing_table_says():
    # a section wider than deep: the node's crack spacing is held to the depth, the table
    # the tent is built on is not [B 004fec60, 004ff450]
    su = run.setup(None, increment=(0.0, 1.0, 0.0))
    sec = su.section
    law = sec.segs[0][4]
    sec.segs = [(600.0, 0.0, 2000.0, 2000.0, law)]
    sec.stirrups = []
    sec._tables()
    bot = min(sec.layers, key=lambda l: l.z)
    reach = float(np.interp(bot.z, *sec.p_smx))
    assert reach > sec.h and float(sec.smx_at(bot.z)) == sec.h
    # the tent falls to nothing at the table's value from the bar, not at the depth: the
    # bottom bars' share at mid-depth is what a tent of that reach leaves
    sec.layers = [bot]
    sec._tables()
    mid = 0.5 * sec.h
    share = (reach - (mid - bot.z)) / (reach + 0.1)
    at_bar, at_mid = (3.6 / float(np.interp(z, sec.tz, sec.t_mlong)) for z in (bot.z, mid))
    assert at_mid / at_bar == pytest.approx(share, rel=0.02)


def test_the_transverse_spacing_takes_its_means_over_every_transverse_type():
    # a cross tie has no vertical leg and is no stirrup, but it counts as a type
    # [B 00440100; O: the Liping sample]
    su = run.setup(None, increment=(0.0, 1.0, 1.0))
    sec = su.section
    mid = 0.5 * (sec.stirrups[0].top + sec.stirrups[0].bot)
    one = sec._trans_spacing(mid, True)
    st = sec.stirrups[0]
    b = float(sec.width(np.array([mid]))[0])
    rho = st.area / st.space / b
    assert one == pytest.approx(np.hypot(b - 100.0, st.space) + 0.1 * st.db / rho)
    sec.n_trans = 3
    assert sec._trans_spacing(mid, True) == pytest.approx(
        np.hypot(b - 100.0, st.space / 3) + 0.1 * (st.db / 3) / rho)


def test_first_cracking_is_closed_in_on_until_two_per_cent_of_the_way_is_left():
    # every stage kept before the first cracked one is uncracked, each a fifth of what was
    # left further on, and what is left to the cracked stage from the last of them is under
    # 2 % of the way come from the first stage [B 00415e30, 00419ff0]
    su = run.setup(None, increment=(0.0, 1.0, 0.0))
    drv = su.driver()
    kept = drv.run(40)
    k = next(i for i, s in enumerate(kept) if drv._marks(s)[0])
    assert k > 3
    left = abs(kept[k].control - kept[k - 1].control)
    way = abs(kept[k - 1].control - kept[0].control)
    assert left < 0.02 * way
    # the try before it was still worth making: more than 2 % was left then
    before = abs(kept[k].control - kept[k - 2].control)
    assert before >= 0.02 * abs(kept[k - 2].control - kept[0].control)
