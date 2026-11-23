"""The Transverse Average Bond chart at the ends of the stirrups and at nodes with next to
no shear strain (docs/kernel.md, "The shear charts" and "A node with next to no shear
strain")."""

import types

import numpy as np

from r2c import export, run


def _setup():
    su = run.setup(None, increment=(0.0, 1.0, 1.0))
    return su.analysis, su.analysis.sec


def test_no_bond_from_the_step_of_stress_at_the_end_of_the_stirrups():
    an, sec = _setup()
    top = max(s.top for s in sec.stirrups)
    # three layers across the stirrups' top end, the middle one with its top node beyond it
    z = top + np.array([1.2, 0.8, 0.4, 0.2, -0.2, -0.6, -1.0])
    fs = np.where(z <= top, 200.0, 0.0)          # a prestress that stops at the end
    d = types.SimpleNamespace(z=z, fsy=fs, lone=None)
    _zt, vt = export.bond_table(sec, d)
    assert np.all(vt == 0.0)


def test_a_node_with_next_to_no_shear_strain_has_no_stirrups():
    an, sec = _setup()
    z = 300.0 + np.array([10.0, 5.0, 0.0, -5.0, -10.0])
    fs = np.array([300.0, 250.0, 200.0, 0.0, 100.0])
    lone = np.array([False, False, False, True, False])
    _zt, with_lone = export.bond_table(sec, types.SimpleNamespace(z=z, fsy=fs, lone=lone))
    _zt, without = export.bond_table(sec, types.SimpleNamespace(z=z, fsy=fs, lone=None))
    assert without[0] > 0 and without[2] > 0
    assert with_lone[0] == without[0] and with_lone[1] == without[1]
    assert with_lone[2] == 0.0 and with_lone[3] == 0.0   # the layer whose middle node it is


def test_which_nodes_count_as_having_no_shear_strain():
    an, sec = _setup()
    z = np.zeros(4)
    ex = np.full(4, 1e-3)
    ey = np.zeros(4)
    g = np.array([0.0, 1e-9, 3e-9, 1e-6])     # the limit here: 2e-9 + 1e-10
    assert list(an.lone_nodes(z, ex, ey, g)) == [True, True, False, False]
    flex = run.setup(None, increment=(0.0, 1.0, 0.0)).analysis
    assert not flex.lone_nodes(z, ex, ey, g).any()
