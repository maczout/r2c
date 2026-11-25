"""tools/review.py groups the committed results' deviations by cause and builds the page."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import report  # noqa: E402
import review  # noqa: E402


def _data():
    run, results = review.load_results(ROOT / "docs" / "verification-results.json")
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    return review.build(run, results, acc, review.load_causes(), review.load_measured())


def test_sizes_are_multiples_of_the_target():
    acc = report.read_targets(ROOT / "docs" / "measures.md")
    _run, results = review.load_results(ROOT / "docs" / "verification-results.json")
    for d in review.all_checks(results, acc):
        if d["check"] == "shape":
            assert d["size"] is None
        elif d["check"] == "view" and not d.get("missing"):
            assert abs(d["size"] - d["pct"] / d["limit"]) < 1e-12
            # outside is tools/report.py's own verdict: more than one target
            assert d["ok"] == (d["size"] <= 1.0)


def test_every_deviation_is_in_one_entry_and_the_entries_are_ranked():
    data = _data()
    ents = data["entries"]
    listed = [d["key"] for e in ents for d in e["instances"]]
    assert len(listed) == len(set(listed))
    want = {d["key"] for d in data["devs"] if d["tier"] != "wont"}
    assert set(listed) == want
    tiers = [review.TIERS.index(e["tier"]) for e in ents]
    assert tiers == sorted(tiers)
    for a, b in zip(ents, ents[1:]):
        if a["tier"] == b["tier"] and not a["shape"] and not b["shape"]:
            assert a["size"] >= b["size"]
        if a["tier"] == b["tier"]:
            assert a["shape"] or not b["shape"]      # a shape comes first in its tier
    for e in ents:
        assert e["worst"] is e["instances"][0]
        assert e["tier"] == min((d["tier"] for d in e["instances"]), key=review.TIERS.index)


def test_a_check_without_a_cause_is_an_entry_of_its_own():
    data = _data()
    devs = [dict(d) for d in data["devs"]]
    review.classify(devs, {"cause": []}, {"checks": {}})
    ents = review.entries(devs, {"cause": []})
    assert ents and all(e["cause"].get("unclassified") for e in ents)
    assert all(len(e["cases"]) == 1 for e in ents)


def test_grid_counts_each_case_once_per_tier():
    data = _data()
    for (fam, tier), n in data["grid"].items():
        assert n["inside"] + n["accepted"] + n["open"] == n["cases"]
        assert n["verdict"] == ("not met" if n["open"] else
                                "met with accepted deviations" if n["accepted"] else "met")
    cases = {d["case"] for d in data["checks"]}
    assert sum(n["cases"] for (f, t), n in data["grid"].items() if t == "could") == len(cases)


def test_page_and_summary_block(tmp_path):
    out = tmp_path / "review.html"
    assert review.main(["--out", str(out)]) == 0
    page = out.read_text(encoding="utf-8")
    data = _data()
    for e in data["entries"][:review.CAP]:
        assert f'id="{e["id"]}"' in page
    assert "<script" not in page
    block = review.summary_block(data)
    assert block.startswith(review.BEGIN) and block.endswith(review.END)
    assert all(e["cause"]["name"] in block for e in data["entries"][:review.CAP])
