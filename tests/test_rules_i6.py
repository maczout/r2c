"""Rules of increment 6 (docs/kernel.md): which bars show a stress at a crack; the
stirrups' ratio on the thin layer across a step in width."""

import numpy as np
import pytest

from r2c import run
from r2c.solver import THIN, Analysis


def _tbeam(scope_dirs):
    for d in scope_dirs:
        p = d / "tbeam.r2t"
        if p.exists():
            return p
    pytest.skip("the T-beam input is not at hand")


def test_the_thin_layer_s_stirrup_ratio_is_by_the_narrower_width(scope_dirs):
    # [O: Response's charts at a web's edge, docs/kernel.md]: on the thin layer across a
    # step, its two ends included, the stirrup ratio is worked out with the narrower
    # width; a node's own width stays what it was, and nodes elsewhere are not touched
    assert Analysis.thin_rho_narrow is True
    su = run.setup(_tbeam(scope_dirs), increment=(0.0, 4.0, 1.0))
    an, sec = su.analysis, su.section
    assert an.thin_side, "the T-beam has a step in width with a thin layer across it"
    zs = next(iter(an.thin_side))
    narrow = min(sec.width_side(zs, True), sec.width_side(zs, False))
    wide = max(sec.width_side(zs, True), sec.width_side(zs, False))
    assert wide > 2.0 * narrow
    z, b = an.layer_nodes()
    zf = z.ravel()
    own = an.node_width(z)
    got = an.rho_width(zf, own)
    on = np.abs(zf - zs) <= THIN + 1e-9
    assert on.sum() >= 4                       # the layer's three nodes and its neighbours' ends
    assert np.all(got[on] == narrow)
    assert np.any(own[on] == wide)             # some of them are on the flange's side
    assert np.array_equal(got[~on], own[~on])
    an.thin_rho_narrow = False
    assert np.array_equal(an.rho_width(zf, own), own)


def test_a_bar_shows_a_stress_at_a_crack_by_the_node_s_principal_strain():
    # [B 00442e50]: the strain tested against the cracking strain is the nodes' principal
    # tensile strain at the bar's height, plus the extra strain at the crack. With shear,
    # a bar with next to no strain of its own in concrete cracked diagonally shows a stress
    su = run.setup(None, initial=(-300.0, 0.0, 0.0), increment=(0.0, 0.0, 1.0))
    an = su.analysis
    e0, phi, gam = -2e-5, 1e-7, 6e-4
    d = an.detail(e0, phi, gam)
    low = int(np.argmin([l.z for l in an.sec.layers]))
    e_bar = float(an.strain(e0, phi, an.sec.layers[low].z))
    if not 0.0 < e_bar < an.sec.conc0.ecr:
        pytest.skip("the state is not the one the test is about")
    assert float(np.max(d.out.e1)) > an.sec.conc0.ecr      # cracked diagonally
    assert d.fscr[low] >= d.fs[low] > 0.0                  # a stress at the crack is shown
