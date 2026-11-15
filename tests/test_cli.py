"""The command line: exit statuses, record files, options."""

from __future__ import annotations

import pytest

from r2c import cli, inputs, record


def test_solve_writes_a_record(tmp_path, capsys):
    assert cli.main(["solve", "--out", str(tmp_path), "-q"]) == 0
    files = list(tmp_path.glob("*.r2x.txt"))
    assert len(files) == 1
    rec = record.read(files[0])
    assert rec.header["kernel"] == "r2c"
    assert rec.header["increment"] == "0.00,1.00,0.00"
    assert int(rec.header["stage-count"]) > 10
    assert rec.stages() == [int(rec.header["peak-stage"])]


def test_existing_record_is_kept(tmp_path):
    assert cli.main(["solve", "--out", str(tmp_path), "-q"]) == 0
    assert cli.main(["solve", "--out", str(tmp_path), "-q"]) != 0
    assert cli.main(["solve", "--out", str(tmp_path), "-q", "--overwrite"]) == 0


def test_usage_errors(tmp_path):
    with pytest.raises(SystemExit) as e:
        cli.main(["solve", "--units", "furlongs"])
    assert e.value.code == 2
    assert cli.main(["solve", "--report", "--out", str(tmp_path)]) == 2


def test_out_of_scope_input(tmp_path):
    old = tmp_path / "old.rsp"
    old.write_text("// Response-2000 data file\nVer_0.8\n")
    assert cli.main(["solve", str(old), "--out", str(tmp_path), "-q"]) == 3


def test_repeated_attribute_is_read():
    """Response writes a stirrup's area twice in one element."""
    sec = inputs.default_section()
    assert sec.longs and sec.trans
    xml = b"""<?xml version="1.0"?><r3g><r3g_beam>
      <concrete fcp="40" name="c"/><rebar fy="400" name="s"/>
      <sectionSOLID>
        300.0 400.0 "c"
        300.0 0.0
      </sectionSOLID>
      <longreinfx z="50" type="s" A="1000" name="bot"/>
      <transreinfz A="200" type="s" space="200" disttop="350" distbot="50" A="200" name="st"/>
    </r3g_beam></r3g>"""
    parsed = inputs.parse(xml)
    assert parsed.trans[0].area == 200.0


def test_health(capsys):
    assert cli.main(["health"]) == 0
    assert "r2c" in capsys.readouterr().out
