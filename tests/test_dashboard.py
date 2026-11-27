"""tools/dashboard.py builds a page from the committed verification results."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import dashboard  # noqa: E402


def test_page_from_committed_results(tmp_path):
    out = tmp_path / "d.html"
    assert dashboard.main(["--out", str(out)]) == 0
    page = out.read_text(encoding="utf-8")
    assert page.startswith("<!DOCTYPE html>") and "__DATA__" not in page
    details = (tmp_path / "details.html").read_text(encoding="utf-8")
    assert 'KIND = "front"' in page and 'KIND = "details"' in details
    run, results = dashboard.load_results(ROOT / "docs" / "verification-results.json")
    data = dashboard.build(run, results, {}, None, ROOT / "tests" / "oracle", [])
    assert len(data["cases"]) == len(results)
    assert all(c.get("curve", {}).get("ref") for c in data["cases"] if "problem" not in c)


def test_loading_labels():
    ref = {"initial": "-500.00,0.00,0.00", "increment": "0.00,1.00,1.00"}
    assert dashboard.loading(ref) == "N₀, then M + V"


def test_unstable_checks_are_shown_and_left_out_of_the_cells():
    # owner, 2026-11-23 (D54, D56): shown with Response's departure beside r2c's difference
    import report
    run, results = dashboard.load_results(ROOT / "docs" / "verification-results.json")
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    data = dashboard.build(run, results, acc, None, ROOT / "tests" / "oracle", [])
    lim = data["views_pct"]
    for t in data["tiers"]:
        assert t["inside"] + t["outside"] + t["unstable"] == t["checks"]
        assert t["plain_inside"] + t["plain_outside"] == t["checks"]
        assert t["first_inside"] + t["first_outside"] + t["first_unstable"] == t["checks"]
        assert t["unstable"] <= t["first_unstable"]         # a spike also departs
    for c in data["cases"]:
        shown = {(v["view"], v.get("stage")) for v in c.get("views", [])}
        for u in c.get("unstable", []):
            assert u["dep"] > lim and u["apart"] <= lim
            assert (u["view"], u["stage"]) not in shown
    page = dashboard.render(data)
    assert "Where Response itself is unstable" in page


def test_front_page_lists_the_cases_outside_target_on_the_control_curve():
    # owner, 2026-11-24: the first screen answers "how accurate is r2c?"; then the control
    # curves of the development cases outside target
    import heldout
    import report
    run, results = dashboard.load_results(ROOT / "docs" / "verification-results.json")
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    data = dashboard.build(run, results, acc, None, ROOT / "tests" / "oracle", [])
    assert data["threshold"] == heldout.THRESHOLD and data["heldout"]
    for c in data["cases"]:
        if "problem" in c:
            continue
        missed = {k for k in dashboard.CURVE_CHECKS if c["checks"].get(k) is False}
        assert {o["check"] for o in c["curve_out"]} == missed
        assert all(o["over"] >= 1.0 for o in c["curve_out"])


def test_curve_misses_carry_the_priority():
    checks = {"peak": (7.0, 5.0, False), "curve": (1.0, 5.0, True), "shape": (False, True, False),
              "post_peak": (20.0, 5.0, False)}
    got = {o["check"]: o for o in dashboard.curve_misses(checks, "shear")}
    assert set(got) == {"peak", "shape", "post_peak"}
    assert got["peak"]["priority"] == 1 and got["post_peak"]["priority"] == 4
    assert got["post_peak"]["over"] == 4.0
    assert dashboard.curve_misses(checks, "flexure")[-1]["priority"] == 2


def test_the_front_page_sets_r2c_s_time_beside_r2x_s():
    # owner, 2026-11-26: speed is reported (not a target); the page shows it by area and by
    # what r2x reads, from the committed times
    import json
    from pathlib import Path

    root = Path(dashboard.__file__).resolve().parents[1]
    results = json.loads((root / "docs" / "verification-results.json").read_text())["results"]
    rows = dashboard.speed(results)
    assert {(r["area"], r["reads"]) for r in rows} == {
        (a, w) for a in ("Without shear", "With shear")
        for w in ("every stage", "the peak stage alone")}
    assert all(0 <= r["within"] <= r["of"] and r["worst"] > 0 for r in rows)
    run = json.loads((root / "docs" / "verification-results.json").read_text())["run"]
    data = dashboard.build(run, results, {}, None, ROOT / "tests" / "oracle", [])
    assert data["speed"] == rows
    assert "Speed: r2c against r2x" in dashboard.render(data, "front")

