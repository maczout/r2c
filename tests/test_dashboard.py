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
    run, results = dashboard.load_results(ROOT / "docs" / "verification-results.json")
    data = dashboard.build(run, results, {}, None, ROOT / "tests" / "oracle", [])
    assert len(data["cases"]) == len(results)
    assert all(c.get("curve", {}).get("ref") for c in data["cases"] if "problem" not in c)


def test_loading_labels():
    ref = {"initial": "-500.00,0.00,0.00", "increment": "0.00,1.00,1.00"}
    assert dashboard.loading(ref) == "N₀, then M + V"


def test_unstable_checks_are_shown_and_left_out_of_the_cells():
    # owner, 2026-11-23 (D54): shown with Response's departure beside r2c's difference
    import report
    run, results = dashboard.load_results(ROOT / "docs" / "verification-results.json")
    acc = report.read_acceptance(ROOT / "docs" / "acceptance.md")
    data = dashboard.build(run, results, acc, None, ROOT / "tests" / "oracle", [])
    lim = data["views_pct"]
    for t in data["tiers"]:
        assert t["inside"] + t["outside"] + t["unstable"] == t["checks"]
        assert t["plain_inside"] + t["plain_outside"] == t["checks"]
    for c in data["cases"]:
        shown = {(v["view"], v.get("stage")) for v in c.get("views", [])}
        for u in c.get("unstable", []):
            assert u["dep"] > lim and (u["view"], u["stage"]) not in shown
    page = dashboard.render(data)
    assert "Where Response itself is unstable" in page
