"""tools/parity.py: the pieces of the interface parity check that need no r2x."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import parity  # noqa: E402
from r2c import cli, record  # noqa: E402


def parser(report_hidden=False, with_define=True):
    p = argparse.ArgumentParser(prog="x")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("solve")
    s.add_argument("inputs", nargs="*")
    s.add_argument("--units", choices=("si", "us"), default="si")
    s.add_argument("--notes", action="store_true",
                   help=argparse.SUPPRESS if report_hidden else "write a report")
    s.add_argument("--image", default="img")
    if with_define:
        sub.add_parser("make").add_argument("words", nargs="+")
    return p


def test_the_same_parser_is_the_same():
    same, diff, skipped = parity.compare(parity.surface(parser()), parity.surface(parser()))
    assert not diff and skipped == ["solve --image"]
    assert "solve --units" in same and "make <words>" in same


def test_a_hidden_option_and_a_missing_subcommand_are_differences():
    theirs, ours = parity.surface(parser()), parity.surface(parser(True, False))
    _same, diff, _skipped = parity.compare(theirs, ours)
    assert [d[0] for d in diff] == ["solve --notes", "make", "make --help", "make <words>"]


def test_r2c_s_own_parser_is_read():
    s = parity.surface(cli.build_parser())
    assert s["solve --units"]["choices"] == ["kgcm", "si", "us"]
    assert parity.parses(cli.build_parser, ["solve", "a.r2t", "--units", "metric"]) == "refuses (exit 2)"
    assert parity.parses(cli.build_parser, ["solve", "a.r2t", "--stage", "all"]) == "takes"


def test_a_skeleton_keeps_the_form_and_drops_the_values():
    a = b"  Title\t: Shear (kN)\r\n   1.250   \t   -12.5\r\nNew Line\r\n   2.000   \t   3.0\r\n"
    b = b"  Title\t: Shear (kN)\r\n   9.999   \t   0.1\r\n"
    assert parity.skeleton(a) == parity.skeleton(b)
    assert parity.skeleton(b"   1.25   \t   3.0\r\n") != parity.skeleton(b)
    assert parity.skeleton(b"  Title\t: Shear (tons)\r\n") != parity.skeleton(b"  Title\t: Shear (ton)\r\n")


def test_a_fixture_has_the_format_of_itself():
    fx = record.read(ROOT / "tests" / "oracle" / "newbeam-m.r2x.txt")
    assert parity.record_diffs(fx, fx) == []


def test_owner_left_define_and_report_out_of_the_score():
    # owner, 2026-11-24: not part of "the same command line"
    theirs = {"define": {"subcommand": True}, "define --help": {"nargs": 0},
              "solve --report": {"nargs": 0}, "solve --out": {"nargs": 1}}
    same, diff, skipped = parity.compare(theirs, {"solve --out": {"nargs": 1}})
    assert same == ["solve --out"] and not diff and len(skipped) == 3


def test_refusals_outside_the_manual_are_known_differences():
    assert parity.outside_manual("probe x: r2x solves, r2c refuses: draped tendons")
    assert not parity.outside_manual("probe x: r2x fails, r2c solves")
