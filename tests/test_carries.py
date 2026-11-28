"""tools/carries.py: what a reader finds in a chart, and that a missing line is seen."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import carries  # noqa: E402
from r2c import record, run, stages  # noqa: E402


def test_a_chart_is_read_as_heading_lines_and_row_forms():
    rec = record.decode(run.solve().record_bytes(stages.ALL))
    heading, kinds, forms = carries.chart(rec.stage(0, "shear_stress"))
    assert heading[3].startswith("Title") and "Shear Stress" in heading[3]
    assert kinds == [(0, "0", True)]
    assert forms == {("4 decimals", "3 decimals")}


def test_a_line_only_one_record_has_is_listed():
    data = run.solve().record_bytes(stages.ALL)
    ref, sub = record.decode(data), record.decode(data)
    d, other = carries.compare(ref, sub)
    assert not any(d.values()) and other == []
    body = ref.sections["stage/0/shear_stress"]
    rows = body.split(b"\r\n")[10:12]
    ref.sections["stage/0/shear_stress"] = body.rstrip(b"\r\n") + b"\r\n" + b"\r\n".join(
        [b"New Line", b"Line type : 2", *rows, b""])
    d, _ = carries.compare(ref, sub)
    assert any("line 2 (line type 2)" in x for x in d["lines"])
    assert any("at stage 0" in x for x in d["first"])
    assert not d["heading"] and not d["numbers"] and not d["control"]
