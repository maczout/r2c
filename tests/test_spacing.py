"""The crack spacing tables over the depth (docs/kernel.md, "Crack spacing over the depth")."""

import math

import numpy as np

from r2c import inputs
from r2c.section import Section


def test_transverse_spacing_inside_and_outside_the_stirrups():
    sec = Section(inputs.default_section())
    st = sec.stirrups[0]
    b = float(sec.width(np.array([sec.zc]))[0])
    rho = st.area / st.space / b
    inside = math.hypot(b - 100.0, st.space) + 0.1 * st.db / rho
    assert abs(float(sec.smt_at(sec.zc)) - inside) < 1e-9
    # five times the depth beyond the stirrup's ends, reached over two bar diameters
    assert abs(float(sec.smt_at(sec.ztop)) - 5.0 * sec.h) < 1e-9
    mid = float(sec.smt_at(st.top))
    assert inside < mid < 5.0 * sec.h


def test_longitudinal_spacing_is_never_over_the_depth_and_has_a_point_at_each_layer():
    sec = Section(inputs.default_section())
    heights = set(np.round(sec.p_smx[0], 9))
    assert all(round(l.z, 9) in heights for l in sec.layers)
    z = np.linspace(sec.zbot, sec.ztop, 50)
    assert float(np.max(sec.smx_at(z))) <= sec.h + 1e-9


def test_a_layer_term_weights_other_layers_by_distance():
    sec = Section(inputs.default_section())
    terms = sec._bar_terms()
    assert len(terms) == len(sec.layers) and all(t > 0 for t in terms)
    l = sec.layers[0]
    # a layer far from every other one: its own steel alone
    far = all(abs(o.z - l.z) / o.db >= 15.0 for o in sec.layers if o is not l)
    if far:
        conc = sec.area_between(max(l.z - 7.5 * l.db, sec.zbot), min(l.z + 7.5 * l.db, sec.ztop))
        assert abs(terms[0] - 0.1 * l.db * conc / l.area) < 1e-9
