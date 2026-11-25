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



# -- where the reference is unstable (D54) -------------------------------------------------------

def test_place_is_by_distance_along_the_curve():
    a = np.array([[0, 0], [1, 50], [2, 100], [3, 50], [4, 0]], dtype=float)
    assert compare.place(a, 0, 4.0, 100.0) is None      # no stage before
    assert compare.place(a, 4, 4.0, 100.0) is None      # no stage after
    assert compare.place(a, 1, 4.0, 100.0) == pytest.approx(0.5)
    # at a peak the load turns back: distance along the curve still places the stage
    assert compare.place(a, 2, 4.0, 100.0) == pytest.approx(0.5)
    b = np.array([[0, 0], [1, 25], [4, 100]], dtype=float)
    assert compare.place(b, 1, 4.0, 100.0) == pytest.approx(0.25)


def test_blend_of_lines_with_the_same_points():
    p = np.array([[0, 10], [2, 0], [2, 5], [0, 5]], dtype=float)     # a box: depth turns back
    q = p * [2, 1]
    b = compare.blend_line(p, q, 0.25)
    assert b[:, 0] == pytest.approx([0, 2.5, 2.5, 0]) and b[:, 1] == pytest.approx(p[:, 1])


def test_blend_by_depth_keeps_a_step():
    p = np.array([[0, 10], [4, 10], [4, 0]], dtype=float)            # steps at the top
    q = np.array([[0, 10], [8, 10], [8, 5], [0, 0]], dtype=float)    # other points in depth
    b = compare.blend_line(p, q, 0.5)
    # top: 0 then (4 + 8) / 2; depth 5: (4 + 8) / 2; bottom: (4 + 0) / 2
    assert b.tolist() == [[0, 10], [6, 10], [6, 5], [2, 0]]
    # a line whose depth turns back cannot be blended by depth
    assert compare.blend_line(p, np.array([[0, 10], [1, 0], [1, 4], [0, 4], [0, 3]], float),
                              0.5) is None


def test_a_line_that_comes_or_goes_is_blended_with_zero():
    one = np.array([[4, 10], [4, 0]], dtype=float)
    lines = compare.blend_lines([one], [one, one], 0.25)
    assert lines[1][:, 0] == pytest.approx([1, 1])
    assert len(compare.blend_lines([one], [one, one], 0.25, lines="both")[1]) == 0


def _chart(points):
    return ("Title : v\r\nLine type : 0\r\n"
            + "".join(f"   {x:.3f}   \t   {y:.3f}\r\n" for x, y in points)).encode()


def _record(tops, near=True):
    """A reference with three stages on a straight control curve; its one view is a line
    from 0 at depth 0 to tops[i] at depth 10. The middle stage is the one compared."""
    from r2c import record
    sections = [("control/c", _chart([(0, 0), (1, 10), (2, 20)]))]
    for i, top in enumerate(tops):
        name = f"stage/{i}/v" if i == 1 or not near else f"neighbour/{i}/v"
        if i == 1 or near is not None:
            sections.append((name, _chart([(0, 0), (top, 10)])))
    return record.decode(record.encode({"peak-stage": "1"}, sections))


def test_departure_of_a_steady_change_and_of_a_spike():
    steady, spike = _record([1.0, 2.0, 3.0]), _record([1.0, 4.0, 3.0])
    assert compare.departure(steady, 1, "v", 0.5) == pytest.approx(0.0, abs=1e-9)
    assert compare.departure(spike, 1, "v", 0.5) == pytest.approx(2.0)
    # the neighbours may also be held as stages (a full capture)
    assert compare.departure(_record([1.0, 4.0, 3.0], near=False), 1, "v", 0.5) == \
        pytest.approx(2.0)
    # without them there is nothing to test
    assert compare.departure(_record([1.0, 4.0, 3.0], near=None), 1, "v", 0.5) is None


def test_views_carry_the_references_departure():
    ref = _record([1.0, 4.0, 3.0])
    row = compare.compare_views(ref, ref, 1, 1, 0.5)[0]
    assert row["max_diff"] == pytest.approx(0.0)
    assert row["departure"] == pytest.approx(2.0) and row["departure_pct"] == pytest.approx(50.0)
    assert row["apart_pct"] == pytest.approx(100.0 * 2.0 / 3.0)     # 1 and 3: a step
    assert "departure" not in compare.compare_views(ref, ref, 1, 1)[0]


def test_neighbours_apart_is_measured_both_ways_and_floored():
    # owner, 2026-11-23 (D56): a spike has neighbours that agree; a step does not
    assert compare.apart(_record([3.0, 9.0, 3.0]), 1, "v") == pytest.approx(0.0)
    # 2 and 4 at the top: the end of the larger line lies 2 from the smaller, 50 % of its
    # own largest value (the smaller line's end is nearer the larger line than that)
    assert compare.apart(_record([2.0, 9.0, 4.0]), 1, "v") == pytest.approx(50.0)
    # the other reading: both on the scale of the chart at the stage (2 of 9)
    assert compare.apart(_record([2.0, 9.0, 4.0]), 1, "v", "stage") == \
        pytest.approx(100.0 * 2.0 / 9.0)
    # within two units of the last printed digit the neighbours do not differ
    assert compare.apart(_record([3.0, 9.0, 3.002]), 1, "v") == 0.0
    assert compare.apart(_record([3.0, 9.0, 3.01]), 1, "v") > 0.0
    assert compare.apart(_record([3.0, 9.0, 3.0], near=None), 1, "v") is None


# -- compared up to the reference's last stage (owner, 2026-11-25) ------------------------------

def _curve_record(points, shear=True):
    from r2c import record
    head = {"peak-stage": "0", "initial": "0,0,0", "increment": "0,1,1" if shear else "0,1,0"}
    return record.decode(record.encode(head, [("control/c", _chart(points))]))


RISE = [(0, 0), (1, 50), (2, 80), (3, 100)]


def test_a_subject_that_carries_on_is_compared_up_to_the_references_last_stage():
    ref = _curve_record(RISE)
    sub = _curve_record(RISE[:3] + [(4, 120), (5, 130), (6, 131)])
    res = compare.compare(ref, sub)
    assert res["upto"]["sub_position"] == pytest.approx(2.5)
    c = res["control"][0]
    assert c["peak_diff_pct"] == pytest.approx(0.0)
    assert c["post_peak_pct"] == 0.0 and c["rising_pct"] < 0.01
    assert c["shape_same"]


def test_no_cut_without_shear_nor_after_a_fall_of_load_nor_when_both_end_together():
    carried = RISE[:3] + [(4, 120), (5, 130)]
    # without shear: the override is about shear responses
    assert "upto" not in compare.compare(_curve_record(RISE, False), _curve_record(carried, False))
    # the reference ended on a load that had fallen under 0.8 of its peak
    fell = RISE + [(4, 70)]
    assert "upto" not in compare.compare(_curve_record(fell), _curve_record(fell + [(5, 60)]))
    # the subject ends at the same place as the reference
    near = RISE + [(3.05, 100.5)]
    assert "upto" not in compare.compare(_curve_record(RISE), _curve_record(near))
    # the subject never passes the reference's last stage
    off = [(0, 0), (1, 30), (2, 50), (3, 60), (6, 90)]
    assert "upto" not in compare.compare(_curve_record(RISE), _curve_record(off))


def test_a_difference_of_exactly_two_printed_units_is_within_the_floor():
    # 0.0026 - 0.0024 is 0.00020000000000000017 in floating point: still two units
    def rec(top):
        from r2c import record
        chart = ("Title : v\r\nLine type : 0\r\n   0.0000   \t   0.000\r\n"
                 f"   {top:.4f}   \t   10.000\r\n").encode()
        return record.decode(record.encode({"peak-stage": "1"}, [
            ("control/c", _chart([(0, 0), (1, 10), (2, 20)])), ("stage/1/v", chart)]))
    row = compare.compare_views(rec(0.0026), rec(0.0024), 1, 1)[0]
    assert row["max_diff"] <= row["floor"]
    row = compare.compare_views(rec(0.0026), rec(0.0023), 1, 1)[0]
    assert row["max_diff"] > row["floor"]
