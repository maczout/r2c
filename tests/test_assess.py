"""tools/report.py's assessment: the view tiers (D2) and the shape of shear cases (D25)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import report  # noqa: E402

ACC = {"flexure": {"peak_pct": 5.0}, "shear": {"peak_pct": 5.0},
       "views": {"views_pct": 5.0, "views_exempt": [], "must": ["a"], "should": ["b"],
                 "could": ["c"]}}


def res(shear, views, shape_ref=("peak", "ends falling"), shape_sub=("peak", "ends falling")):
    return {"ref": {"initial": "0,0,0", "increment": "0,1,1" if shear else "0,1,0"},
            "control": [{"peak_diff_pct": 0.0, "shape_same": list(shape_ref) == list(shape_sub),
                         "shape_ref": list(shape_ref), "shape_sub": list(shape_sub)}],
            "views": [{"view": v, "max_diff": p, "max_diff_pct": p, "floor": 0.0}
                      for v, p in views.items()]}


def test_must_views_assessed_without_shear_only():
    flex = report.assess(res(False, {"a": 9.0, "b": 1.0, "c": 1.0}), ACC)
    assert flex["views"][2] is False and flex["views_should"][2] is True
    shear = report.assess(res(True, {"a": 9.0, "b": 1.0, "c": 1.0}), ACC)
    assert "views" not in shear and shear["views_should"][2] is False


def test_could_views_counted_on_their_own():
    chk = report.assess(res(False, {"a": 1.0, "b": 1.0, "c": 9.0}), ACC)
    assert chk["views"][2] is True and chk["views_could"][2] is False


def test_shear_shape_leaves_out_the_ending():
    r = res(True, {}, ("peak", "ends falling"), ("peak", "ends standing still"))
    assert report.assess(r, ACC)["shape"][2] is True
    f = res(False, {}, ("peak", "ends falling"), ("peak", "ends standing still"))
    assert report.assess(f, ACC)["shape"][2] is False


def test_without_tiers_all_views_are_one_check():
    acc = {"flexure": {}, "views": {"views_pct": 5.0, "views_exempt": []}}
    chk = report.assess(res(False, {"a": 1.0, "c": 9.0}), acc)
    assert chk["views"][2] is False and "views_could" not in chk


def staged(shear, stages):
    """A result with its views stage by stage: stages is [(feature, {view: pct})]."""
    r = res(shear, {})
    r["views_stages"] = [
        {"ref_stage": i, "feature": f,
         "views": [{"view": v, "max_diff": p, "max_diff_pct": p, "floor": 0.0}
                   for v, p in views.items()]}
        for i, (f, views) in enumerate(stages)]
    return r


def test_shear_views_leave_out_the_last_stage():
    # owner, 2026-11-22 (D40): the counterpart of D25 for the views
    stages = [("peak", {"b": 1.0}), ("ends falling", {"b": 9.0})]
    assert report.assess(staged(True, stages), ACC)["views_should"][2] is True
    assert [v["max_diff_pct"] for v in report.view_rows(staged(True, stages), True)] == [9.0]
    # without shear the last stage is assessed, and nothing is set aside
    flex = staged(False, stages)
    assert report.assess(flex, ACC)["views_should"][2] is False
    assert report.view_rows(flex, True) == []


def test_a_last_stage_that_is_the_peak_is_assessed():
    r = staged(True, [("cracking", {"b": 1.0}), ("peak", {"b": 9.0})])
    assert report.assess(r, ACC)["views_should"][2] is False


# -- where Response is unstable (owner, 2026-11-23, D54; the spike test, D56) --------------------

def unstable_case(shear=False):
    """Two stages. View a at stage 0: r2c 9 % off where Response itself spikes, departing
    20 % from the blend of its neighbours, which agree. Everything else steady or not
    tested."""
    r = staged(shear, [("cracking", {"a": 9.0, "b": 1.0}), ("peak", {"a": 1.0, "c": 9.0}),
                       ("ends falling", {})])
    rows = {(i, v["view"]): v for i, st in enumerate(r["views_stages"]) for v in st["views"]}
    rows[0, "a"].update(departure=20.0, departure_pct=20.0, apart_pct=1.0)
    rows[0, "b"].update(departure=2.0, departure_pct=2.0, apart_pct=4.0)   # steady: assessed
    return r, rows


def test_an_unstable_check_counts_neither_inside_nor_outside():
    r, _rows = unstable_case()
    chk = report.assess(r, ACC)
    assert chk["views"] == (1.0, 5.0, True)                 # a's 9 % at stage 0 is left out
    assert report.assess(r, ACC, rule=False)["views"][2] is False
    states = {(c["view"], c["ref_stage"]): (c["state"], c["plain"])
              for c in report.stage_checks(r, ACC)}
    assert states["a", 0] == ("unstable", "outside")
    assert states["b", 0] == ("inside", "inside")
    n = report.tier_counts({"x": r}, ACC)["views"]
    assert (n["checks"], n["inside"], n["outside"], n["unstable"]) == (2, 1, 0, 1)
    assert (n["plain_inside"], n["plain_outside"]) == (1, 1)
    assert (n["first_inside"], n["first_outside"], n["first_unstable"]) == (1, 0, 1)


def test_a_step_stays_assessed():
    # owner, 2026-11-23 (D56): the neighbours differ, so Response moved and stayed: a step
    r, rows = unstable_case()
    rows[0, "a"].update(apart_pct=30.0)
    assert report.assess(r, ACC)["views"][2] is False
    assert report.assess(r, ACC, rule="departure")["views"] == (1.0, 5.0, True)
    c = next(c for c in report.stage_checks(r, ACC) if (c["view"], c["ref_stage"]) == ("a", 0))
    assert (c["state"], c["first"], c["plain"]) == ("outside", "unstable", "outside")
    n = report.tier_counts({"x": r}, ACC)["views"]
    assert (n["outside"], n["unstable"], n["first_unstable"]) == (1, 0, 1)
    # neighbours exactly at the target agree
    rows[0, "a"].update(apart_pct=5.0)
    assert report.assess(r, ACC)["views"][2] is True
    # a result from before the neighbours were measured against each other: not tested
    del rows[0, "a"]["apart_pct"]
    assert report.assess(r, ACC)["views"][2] is False


def test_a_check_that_is_not_tested_stays_assessed():
    r, _rows = unstable_case()
    # c at stage 1 has no departure (no neighbours): 9 % is outside, as before
    assert report.assess(r, ACC)["views_could"][2] is False


def test_a_departure_within_the_printed_precision_is_not_unstable():
    r, rows = unstable_case()
    rows[0, "a"].update(departure=0.01, departure_pct=20.0, floor=0.02)
    assert report.assess(r, ACC)["views"][2] is False
    # and one at the target is not beyond it
    rows[0, "a"].update(departure=5.0, departure_pct=5.0, floor=0.0)
    assert report.assess(r, ACC)["views"][2] is False


def test_the_report_shows_response_departure_beside_r2c_difference():
    r, _rows = unstable_case()
    text = "\n".join(report.unstable_sections({"x": r}, ACC))
    assert "| Must | x | 0 (cracking) | a: 20.0 / 1.0 / 9.0 (outside) |" in text
    assert "| Must | 2 | 1 | 0 | 1 | 1 | 1 | 1 | 0 | 1 |" in text
