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


def test_shape():
    names = [f for f, _ in compare.shape(REF, 100.0, 4.0)]
    assert names == ["peak", "ends falling"]       # straight to the peak: no stiffness drop
    cracked = np.array([[0, 0], [0.1, 40], [1, 60], [2, 100], [3, 100]], dtype=float)
    assert [f for f, _ in compare.shape(cracked, 100.0, 4.0)] == [
        "cracking", "peak", "ends standing still"]
    assert [f for f, _ in compare.shape(REF[:3], 100.0, 4.0)] == ["peak", "ends at peak"]


# D13 (owner, 2026-11-22): stage matching respects the features of the curves.
class _Rec:
    def __init__(self, n):
        self._n = n

    def stages(self):
        return list(range(self._n))


def test_matching_does_not_jump_back_across_a_fall():
    # cracking at stage 3, a fall of load at stage 5; the reference's stage after the fall
    # (5) has a load close to the subject's uncracked stage 2, but must match the subject's
    # stage after its own fall (5)
    ref = np.array([[0, 0], [1, 40], [2, 80], [3, 90], [4, 100], [5, 82], [6, 105],
                    [7, 110]], dtype=float)
    sub = np.array([[0, 0], [1, 40], [2, 81], [3, 90], [4, 99], [5, 70], [6, 104],
                    [7, 110]], dtype=float)
    xs, ys = 7.0, 110.0
    assert compare._nearest_stage.__doc__  # the old rule is kept as the fallback
    ss = compare._segment_stage(_Rec(8), None, 5, ref, sub, 5.0, 82.0, xs, ys)
    assert ss == 5


def test_matching_falls_back_to_nearest_when_the_features_differ():
    ref = np.array([[0, 0], [1, 50], [2, 100], [3, 80]], dtype=float)
    sub = np.array([[0, 0], [1, 50], [2, 60], [3, 100]], dtype=float)  # no cracking
    ss = compare._segment_stage(_Rec(4), None, 1, ref, sub, 1.0, 50.0, 3.0, 100.0)
    assert ss == 1


# D42 (owner, 2026-11-22): a stage at the same place is compared before the feature's stage.
def test_matching_takes_the_stage_at_the_same_place_before_the_feature():
    # two curves that agree, with "cracking" read at stage 3 of one and stage 2 of the other
    ref = np.array([[0, 0], [1, 40], [2, 70], [3, 80], [4, 90], [5, 100]], dtype=float)
    sub = np.array([[0, 0], [1, 40], [2, 55], [3, 80], [4, 90], [5, 100]], dtype=float)
    assert dict(compare.shape(ref, 100.0, 5.0))["cracking"] == 3
    assert dict(compare.shape(sub, 100.0, 5.0))["cracking"] == 2
    assert compare._segment_stage(_Rec(6), None, 3, ref, sub, 3.0, 80.0, 5.0, 100.0) == 2
    assert compare.match_stage(_Rec(6), None, 3, ref, sub, 5.0, 100.0, 0.05) == (3, "same place")


def test_same_place_does_not_match_across_a_fall():
    # a shallow fall of load at stage 3 in both; the subject's stage before its fall (2) is
    # the nearest to the reference's stage after the fall (3), and within the target
    ref = np.array([[0, 0], [1, 50], [2, 60], [2.02, 57], [3, 80], [4, 100]], dtype=float)
    sub = np.array([[0, 0], [1, 50], [2.02, 58], [2.3, 55], [3, 80], [4, 100]], dtype=float)
    d = np.hypot((sub[:, 0] - 2.02) / 4.0, (sub[:, 1] - 57.0) / 100.0)
    assert int(np.argmin(d)) == 2 and d[2] < 0.05
    assert compare.match_stage(_Rec(6), None, 3, ref, sub, 4.0, 100.0, 0.05)[0] == 3


def test_far_stages_are_matched_by_feature():
    ref = np.array([[0, 0], [1, 40], [2, 80], [3, 90], [4, 100], [5, 82], [6, 105],
                    [7, 110]], dtype=float)
    sub = np.array([[0, 0], [1, 40], [2, 81], [3, 90], [4, 99], [5, 70], [6, 104],
                    [7, 110]], dtype=float)
    assert compare.match_stage(_Rec(8), None, 5, ref, sub, 7.0, 110.0, 0.05) == (5, "feature")

