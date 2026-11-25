"""tools/check.py holds the record to the brief (docs/brief.md, CLAUDE.md)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check  # noqa: E402


def test_the_record_passes():
    assert check.main([]) == 0


def test_the_brief_replaced_the_acceptance_file():
    assert (ROOT / "docs" / "brief.md").exists()
    assert not (ROOT / "docs" / "acceptance.md").exists()


def test_old_numbering_is_recognised():
    for text in ("accepted under D66", "the override (C2)", "D1 to D3"):
        assert check.OLD_NUMBER.search(text)
    for text in ("a 25M bar", "tools/D12.py", "M/V = 2 m", "ABCD12"):
        assert not check.OLD_NUMBER.search(text), text


def test_summary_items_are_counted():
    got = check.parts("# t\n\n## What changed\n\n- a\n- b\n  more\n\n## Next\n1. x\n")
    assert check.items(got["## What changed"]) == 2
    assert check.items(got["## Next"]) == 1


def test_the_summary_is_one_page():
    text = (ROOT / "docs" / "summary.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) <= check.SUMMARY_LINES
    got = check.parts(text)
    for h in check.SUMMARY_PARTS:
        assert h in got
    for h, most in check.SUMMARY_ITEMS.items():
        assert check.items(got[h]) <= most
