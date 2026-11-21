"""tools/compare.py's two-way curve measure, on made-up curves."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import compare  # noqa: E402

# a reference: rises to 100 at x = 2, falls to 80 at x = 4
REF = np.array([[0, 0], [1, 60], [2, 100], [3, 90], [4, 80]], dtype=float)
IA = 2


def measure(sub):
    return compare.two_way(REF, IA, np.array(sub, dtype=float), 4.0, 100.0)


def test_same_curve_is_zero():
    rise, post = measure(REF)
    assert rise == pytest.approx(0.0) and post == pytest.approx(0.0)


def test_running_on_past_the_end_is_post_peak():
    # on Response's curve to its end, then on to x = 8: invisible one-way
    rise, post = measure(np.vstack([REF, [[8, 80]]]))
    assert rise == pytest.approx(0.0)
    assert post == pytest.approx(1.0)          # 4 in x, scaled by 4
    one_way, _ = compare.curve_distance(REF, np.vstack([REF, [[8, 80]]]), 4.0, 100.0)
    assert one_way == pytest.approx(0.0)


def test_stopping_short_is_post_peak():
    rise, post = measure(REF[:3])
    assert rise == pytest.approx(0.0)
    assert post > 0.2


def test_a_detour_before_the_peak_is_rising():
    # r2c drops back to (0.9, 30) on the way up: Response's points all lie on r2c's curve,
    # r2c's detour does not lie on Response's
    sub = [[0, 0], [1, 60], [0.9, 30], [1, 60], [2, 100], [3, 90], [4, 80]]
    rise, post = measure(sub)
    assert rise > 0.05 and post == pytest.approx(0.0)
