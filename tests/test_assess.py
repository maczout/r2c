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
