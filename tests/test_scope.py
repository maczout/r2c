"""The reader and the material rules that increment S added (docs/scope.md): what r2c takes
from a file, what it rejects as Response-2000 does, and the rules read from Response's
binary, at values worked by hand from docs/kernel.md. No oracle and no input file needed."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r2c import inputs, run
from r2c.inputs import Concrete, InputError, OutOfScope
from r2c.materials import ConcreteLaw

BEAM = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<document><r3g_beam {beam}>
<concrete fcp="35.0" maxagg="19.0" {concrete}>{curve}</concrete>
<rebar fy="400.0" esh="7.0" eu="100.0">{steel}</rebar>
<rebar fy="400.0" esh="7.0" eu="100.0" name="Trans"/>
<prestress fu="1860.0"/>
{outline}
<shapesection name="{shape}" par1="{par1}" par2="600.0"/>
<longreinfx z="538.95" type="Steel 1" A="300.0" bartitle="20M" name="top"/>
<longreinfx z="63.90" type="Steel 1" num="3" A="1500.0" bartitle="25M"/>
<transreinfz A="100.0" type="Trans" pattern="5" space="250.0" disttop="554.3" distbot="45.7"
 bartitle="10M" name="stirrup"/>
{extra}
<sectloading/>
</r3g_beam></document>"""
RECT = '<sectionSOLID>\n600.0 250.0\n0.0 250.0 "Concrete 1"\n</sectionSOLID>'


def beam(**kw) -> bytes:
    d = dict(beam="", concrete="", curve="", steel="", outline=RECT, shape="RECT",
             par1="250.0", extra="")
    d.update(kw)
    return BEAM.format(**d).encode()


# -- what Response-2000 itself rejects is an input error -----------------------------------------
@pytest.mark.parametrize("outline", [
    '<sectionSOLID>\n600.0 0.0\nUP\n300.0 600.0 "Concrete 1"\nDOWN\n0.0 0.0\n</sectionSOLID>',
    '<sectionSOLID>\n600.0 0.0\n450.0 UP\n300.0 600.0 "Concrete 1"\n0.0 0.0\n</sectionSOLID>',
])
def test_curved_outline_rows_are_rejected(outline):
    with pytest.raises(InputError, match="curved outline rows"):
        inputs.parse(beam(outline=outline))


def test_tension_stiffening_5_is_rejected():
    with pytest.raises(InputError, match="Stuart Oliver"):
        inputs.parse(beam(concrete='t_stiff="5"'))


def test_roman_units_are_rejected():
    with pytest.raises(InputError, match="units"):
        inputs.parse(beam(beam='units="roman"'))


def test_a_model_number_response_does_not_have_is_rejected():
    with pytest.raises(InputError):
        inputs.parse(beam(concrete='c_soft="19"'))


def test_a_shape_without_an_outline_is_rejected():
    # Response-2000 opens such a file with no concrete and cannot solve it (D6)
    for shape in ("RECT", "CIRCLE"):
        with pytest.raises(InputError, match="no concrete outline"):
            inputs.parse(beam(outline="", shape=shape))


# -- beyond the documented scope: refused (docs/scope.md; docs/summary.md D4, D5, D10, D18, D23) ------
@pytest.mark.parametrize("model", [4, 16, 17])
def test_softening_models_that_are_not_in_the_manual_are_refused(model):
    with pytest.raises(OutOfScope, match="softening"):
        inputs.parse(beam(concrete=f'c_soft="{model}"'))


@pytest.mark.parametrize("model", [9, 14, 15])
def test_hsu_softening_with_tamai_tension_stiffening_is_refused(model):
    with pytest.raises(OutOfScope, match="Tamai"):
        inputs.parse(beam(concrete=f'c_soft="{model}" t_stiff="4"'))
    inputs.parse(beam(concrete=f'c_soft="{model}"'))
    inputs.parse(beam(concrete='c_soft="2" t_stiff="4"'))


def test_a_segmental_curve_for_reinforcing_steel_is_refused():
    with pytest.raises(OutOfScope, match="segmental"):
        inputs.parse(beam(steel="\n0.0 0.0\n2.0 400.0\n100.0 600.0\n"))


def test_draped_tendons_are_refused():
    layer = '<longreinfx z="100.0" type="Low Relax" A="99.0" dep="6.5" {} name="strand"/>'
    with pytest.raises(OutOfScope, match="draped"):
        inputs.parse(beam(extra=layer.format('drape="0.05"')))
    inputs.parse(beam(extra=layer.format('drape="0.0"')))


def test_of_several_sections_in_one_file_the_first_is_read():
    # Response's sample inputs carry several sections; Response opens the first (r2x solves it)
    one = beam().decode()
    section = one[one.index("<r3g_beam"):one.index("</r3g_beam>") + len("</r3g_beam>")]
    other = section.replace('fcp="35.0"', 'fcp="80.0"')
    assert other != section
    two = one.replace(section, section + "\n" + other).encode()
    assert inputs.parse(two).concretes[0].fcp == inputs.parse(one.encode()).concretes[0].fcp == 35.0
    swapped = one.replace(section, other + "\n" + section).encode()
    assert inputs.parse(swapped).concretes[0].fcp == 80.0


def test_the_horizontal_tie_is_read_as_a_stirrup():
    # Response solves stirrup pattern 7 as it solves a stirrup, and draws no transverse bond
    one = beam()
    assert b'pattern="5"' in one
    for pattern in (1, 2, 3, 4, 6, 7):
        s = inputs.parse(one.replace(b'pattern="5"', f'pattern="{pattern}"'.encode()))
        assert s.trans[0].pattern == pattern


def test_out_of_scope_by_design_is_still_refused():
    with pytest.raises(OutOfScope):
        inputs.parse(beam(outline=RECT + '<sectionHOLLOW>\n400 100\n200 100\n</sectionHOLLOW>'))
    with pytest.raises(OutOfScope):
        inputs.parse(beam(extra='<analysisoptions longterm="1"/>'))
    with pytest.raises(OutOfScope):
        inputs.parse(beam(extra='<straindiscont>\n600 0.2\n0 0.0\n</straindiscont>'))


# -- what a file carries is taken from it --------------------------------------------------------
def test_factors_and_units_come_from_the_file_when_no_option_is_given(tmp_path):
    p = tmp_path / "f.r2t"
    p.write_bytes(beam(extra='<analysisoptions phic="0.65" phis="0.85" phip="0.90"/>'))
    assert run.setup(p).factors == (0.65, 0.85, 0.90)
    assert run.setup(p, factors="none").factors == (1.0, 1.0, 1.0)
    us = beam(beam='units="US"', par1="9.84",
              outline='<sectionSOLID>\n23.62 9.84\n0.0 9.84\n</sectionSOLID>').decode()
    for a, b in (('fcp="35.0" maxagg="19.0"', 'fcp="5076.3" maxagg="0.75"'),
                 ('fy="400.0"', 'fy="58.0" E="29008" fu="87.0"'), ('fu="1860.0"', 'fu="269.8"'),
                 ('z="538.95"', 'z="21.22"'), ('A="300.0"', 'A="0.465"'),
                 ('z="63.90"', 'z="2.52"'), ('A="1500.0"', 'A="2.325"'),
                 ('A="100.0"', 'A="0.155"'), ('space="250.0"', 'space="9.84"'),
                 ('disttop="554.3"', 'disttop="21.8"'), ('distbot="45.7"', 'distbot="1.8"'),
                 ('par2="600.0"', 'par2="23.62"')):
        assert a in us
        us = us.replace(a, b)
    us = us.encode()
    p.write_bytes(us)
    su = run.setup(p)
    assert su.units.name == "us"
    assert su.section.h == pytest.approx(23.62 * 25.4)
    assert su.section.laws[0].fcp == pytest.approx(35.0, abs=0.01)
    assert run.setup(p, units="si").units.name == "si"


def test_shrinkage_is_a_parabola_through_three_points():
    s = inputs.parse(beam(extra='<shrinktherm>\n600.0 0.300\n300.0 0.000\n0.0 0.000\n'
                                '</shrinktherm>'))
    from r2c.section import Section
    sec = Section(s, 1.0, 1.0, 1.0)
    # Response's own chart of this profile (newbeam-thermgrad-m): -0.037 mm/m at 162 mm
    assert sec.shrinkage(np.array([162.0]))[0] * 1e3 == pytest.approx(-0.037, abs=0.001)
    assert sec.shrinkage(np.array([0.0, 300.0, 600.0])) * 1e3 == pytest.approx([0, 0, 0.3])


def test_shrinkage_through_more_points_is_read_three_at_a_time_from_the_top():
    # the program's table read [B 004b6df0]: a parabola through the first three points from
    # the top, another through the third to the fifth; a point left over is joined straight
    from r2c.section import Section
    rows = '600.0 0.400\n500.0 0.100\n400.0 0.000\n200.0 0.200\n100.0 0.000\n0.0 0.300\n'
    sec = Section(inputs.parse(beam(extra=f'<shrinktherm>\n{rows}</shrinktherm>')), 1.0, 1.0, 1.0)
    sh = lambda z: float(sec.shrinkage(np.array([z]))[0]) * 1e3      # noqa: E731
    assert [sh(z) for z in (600, 500, 400, 200, 100, 0)] == pytest.approx(
        [0.4, 0.1, 0.0, 0.2, 0.0, 0.3])
    assert sh(550.0) == pytest.approx(0.4 * 0.375 + 0.1 * 0.75)         # through 600, 500, 400
    # through 400, 200, 100, where only the middle point has a strain
    assert sh(300.0) == pytest.approx(0.2 * (300 - 400) * (300 - 100) / ((200 - 400) * (200 - 100)))
    assert sh(50.0) == pytest.approx(0.15)                              # straight, 100 to 0


# -- compression softening: beta at a transverse strain of 2 mm/m, 60 MPa, e0 2.4 mm/m ------------
E1, E2, FC, E0 = 2e-3, -1.5e-3, 60.0, 2.4e-3
KF = 0.1825 * math.sqrt(FC)
BETA = {
    0: 1.0,
    1: 1 / (0.85 + 0.27 * E1 / 1.5e-3),
    2: 1 / (0.8 + 0.34 * E1 / E0),
    3: 1 / (1 + KF * 0.35 * (E1 / 1.5e-3 - 0.28) ** 0.8),
    5: 1 / (1 + 0.27 * (E1 / E0 - 0.37)),
    6: 1 / (0.8 + 0.34 * E1 / E0),
    7: 1.15 - 125 * E1,
    8: 1.0,                                        # 0.6 (e1 + 0.0002)^0.39 + 0.8 is below 1
    9: 0.9 / math.sqrt(1 + 400 * E1),
    10: 1 / (0.8 + 170 * E1),
    11: 3.6 / (1 + 2 * (E1 + 1.5e-3) / E0),
    12: FC ** 0.6667 / (0.4 + 30 * E1) / FC,
    13: 1 / ((0.9 + 0.0045 * FC) * (0.8 + 0.34 * E1 / E0)),
    14: (5.8 / math.sqrt(FC)) / math.sqrt(1 + 400 * E1),
    15: 0.9 / math.sqrt(1 + 600 * E1),
    18: 1 / (0.8 + 180 * E1),
}


@pytest.mark.parametrize("model", sorted(BETA))
def test_softening_models(model):
    law = ConcreteLaw(Concrete(fcp=FC, e0=E0, c_soft=model))
    beta = law.soften(np.array([E1]), np.array([E2]))[0]
    assert beta == pytest.approx(min(BETA[model], 1.0), rel=1e-9)
    stress, fmax = law._compression(np.array([E2]), np.array([E1]))
    assert fmax[0] == pytest.approx(-FC * beta)
    assert -FC * beta - 1e-9 <= stress[0] < 0.0


def test_softening_that_lowers_the_strain_at_peak_stress():
    # Belarbi-Hsu: the peak stress is reached at beta x e0, not at e0
    law = ConcreteLaw(Concrete(fcp=FC, e0=E0, c_soft=9))
    beta = law.soften(np.array([E1]))[0]
    at_peak, fmax = law._compression(np.array([-beta * E0]), np.array([E1]))
    assert at_peak[0] == pytest.approx(fmax[0])
    # Vecchio-Collins 1992-A: a plateau from beta x e0 to e0
    law = ConcreteLaw(Concrete(fcp=FC, e0=E0, c_soft=3))
    e2 = np.array([-0.9 * E0])
    beta = law.soften(np.array([E1]), e2)[0]
    assert 0.9 > beta
    stress, fmax = law._compression(e2, np.array([E1]))
    assert stress[0] == pytest.approx(fmax[0]) == pytest.approx(-FC * beta)
