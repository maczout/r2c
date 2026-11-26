"""The held-out set stays frozen and its committed results stay totals (docs/brief.md)."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import heldout  # noqa: E402
import report  # noqa: E402

# The hash over the cases as frozen on 2026-11-24. It changes only if the set is changed,
# which the brief does not allow: do not update it to make this test pass.
FROZEN = "9b0ad8e27ef726e3bbd252c45250907542334869ecef15d5a64c348662d44e16"


def manifest():
    return json.loads(heldout.MANIFEST.read_text())


def test_the_set_is_the_frozen_one():
    man = manifest()
    assert man["frozen_sha256"] == FROZEN
    assert heldout.digest(man["cases"]) == FROZEN


def test_the_set_is_the_size_the_brief_asks_for_and_covers_both_areas():
    cases = manifest()["cases"]
    assert 30 <= len(cases) <= 56
    areas = [c["area"] for c in cases]
    assert areas.count("moment-axial") >= 10 and areas.count("shear") >= 10


def test_no_held_out_case_is_a_development_case():
    dev = {p.name for p in (ROOT / "tests" / "oracle").rglob("*.r2x.txt")}
    for c in manifest()["cases"]:
        assert f"{c['name']}.r2x.txt" not in dev


def test_every_case_follows_from_the_recipe():
    by = {c["name"]: c for c in heldout.CASES}
    for c in manifest()["cases"]:
        r = by[c["name"]]
        assert all(c[k] == r[k] for k in r)
        assert c["area"] == heldout.area(r)


def test_totals_hold_totals_only():
    heldout.check_totals(heldout.read_totals())
    bad = {"runs": [{"label": "x", "date": "d", "commit": "c", "cases": {}, "unsolved": {},
                     "totals": {}, "worst_case": "h-x"}]}
    with pytest.raises(ValueError):
        heldout.check_totals(bad)


def test_a_case_r2c_does_not_solve_counts_outside_on_every_priority():
    cases = [{"name": "a", "area": "shear"}, {"name": "b", "area": "moment-axial"}]
    t = heldout.tally(cases, {"a": {"failed": "x"}}, report.read_targets(ROOT / "docs" / "measures.md"))
    t.pop("kinds")
    assert t["unsolved"] == {"moment-axial": 1, "shear": 1}
    assert t["totals"]["shear"] == {p: [0, 1] for p in "1234"}
    assert t["totals"]["moment-axial"] == {p: [0, 1] for p in "123"}


def test_priorities_are_counted_from_the_report_s_own_assessment():
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    res = {"ref": {"initial": "0,0,0", "increment": "0,1,1"},
           "control": [{"chart": "c", "peak_diff_pct": 1.0, "rising_pct": 9.0,
                        "post_peak_pct": 1.0, "shape_same": True}]}
    t = heldout.tally([{"name": "a", "area": "shear"}], {"a": res}, acc)["totals"]["shear"]
    assert t["1"] == [0, 1]      # the rising branch is outside
    assert t["4"] == [1, 1]      # the ending is inside
    assert t["2"] == [0, 0] and t["3"] == [0, 0]   # no views compared: no such check


def test_the_kinds_name_no_case_and_carry_no_value():
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    cases = [dict(c, area=heldout.area(c)) for c in heldout.CASES]
    text = heldout.text_kinds(heldout.tally(cases, {}, acc)["kinds"])
    assert "outside" in text and "T-beam" in text and "shear alone" in text
    for c in heldout.CASES:
        assert c["name"] not in text
    assert "%" not in text and "h-" not in text
    # every case of the recipe has a kind
    assert len({heldout.kind(c) for c in heldout.CASES}) > 10
