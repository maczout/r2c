"""r2c command line: `r2c solve`, with the options, results and exit statuses of `r2x solve`.

    r2c solve beam.r2t --stage all
    r2c solve col.rsp --initial -2000,0,0 --increment 0,1,0
    r2c health

The record each solve writes is in r2x's raw format (docs/raw-format.md), named NAME.r2x.txt as
r2x names it, so whatever reads r2x's records reads r2c's. Standard library and numpy only.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from r2c import __version__, progress, run
from r2c.display import Display
from r2c.inputs import InputError, OutOfScope
from r2c.notice import DISCLAIMER
from r2c.progress import FAILED, OUT_OF_SCOPE, SOLVED, USAGE, Event
from r2c.settings import FACTORS, UNITS, parse_loads, parse_more_detail
from r2c.stages import StageError, StageSpec, parse_stages
from r2c.views import ViewError, parse_views

RECORD_SUFFIX = ".r2x.txt"     # the record format is r2x's, and so is its name
NEW_NAME = "newbeam"


class UsageError(Exception):
    """A problem with the command line, found before anything runs (exit status 2)."""


def expand_inputs(patterns: list[str]) -> list[Path]:
    """Expand globs here: PowerShell and cmd pass *.r2t through unexpanded."""
    out: list[Path] = []
    for pat in patterns:
        matches = sorted(glob.glob(pat)) if glob.has_magic(pat) else [pat]
        if not matches:
            raise UsageError(f"no files match {pat}")
        for m in matches:
            p = Path(m)
            if not p.is_file():
                raise UsageError(f"not a file: {m}")
            if p.resolve() not in [q.resolve() for q in out]:
                out.append(p)
    return out


def job_name(inp: Path | None) -> str:
    return inp.stem if inp is not None else NEW_NAME


def record_path(inp: Path | None, out: Path | None) -> Path:
    folder = out if out else (inp.parent if inp is not None else Path("."))
    return folder / f"{job_name(inp)}{RECORD_SUFFIX}"


def overall_status(statuses: list[int]) -> int:
    for s in (FAILED, USAGE, OUT_OF_SCOPE):
        if s in statuses:
            return s
    return SOLVED


def solve_one(inp: Path | None, a, display, job) -> tuple[int, str, bytes | None]:
    """Solve one input: (exit status, reason if not solved, record bytes if solved)."""
    display.start(job)

    def on_event(kind, value):
        if kind == "solving":
            display.event(job, Event("solving", count=value))
        elif kind == "refining":
            display.event(job, Event("refining", count=value[1], done=value[0]))

    try:
        result = run.solve(inp, units=a.units, factors=a.factors, initial=a.initial,
                           increment=a.increment, more_detail=a.more_detail, on_event=on_event)
        for note in result.notes:
            display.event(job, progress.note(note))
        display.event(job, Event("solved", count=len(result.stages), stage=result.peak))

        def staged(stage, done, total):
            display.event(job, Event("stage", stage=stage, done=done, total=total))
        data = result.record_bytes(a.stage, a.views, staged)
    except OutOfScope as e:
        return OUT_OF_SCOPE, str(e), None
    except (InputError, StageError) as e:
        return USAGE, str(e), None
    except run.Failed as e:
        return FAILED, str(e), None
    return SOLVED, "", data


def replace_ok(existing: list[Path]) -> bool:
    """Whether to replace results that exist: asked at a terminal; with no one to ask, r2c
    stops, and --overwrite says yes."""
    if len(existing) == 1:
        what = f"{existing[0]} exists: replace it"
    else:
        what = f"{existing[0]} and {len(existing) - 1} more exist: replace them"
    if not (sys.stdin.isatty() and sys.stderr.isatty()):
        raise UsageError(f"{what.split(':')[0]}; use --overwrite to replace")
    sys.stderr.write(f"  {what} [n]: ")
    sys.stderr.flush()
    answer = sys.stdin.readline().strip().lower()
    return answer in ("y", "yes")


def cmd_solve(a) -> int:
    if a.report:
        raise UsageError("--report is r2x's: its report is screenshots of Response-2000, "
                         "which r2c does not run")
    if a.stdout and a.out:
        raise UsageError("--stdout writes no files, so --out does not apply")
    inputs: list[Path | None] = expand_inputs(a.inputs) if a.inputs else [None]
    live = sys.stderr.isatty()
    if a.stdout:
        if len(inputs) != 1:
            raise UsageError(f"--stdout takes one input; {len(inputs)} given")
        with Display(sys.stderr, live, a.quiet) as display:
            job = display.add(job_name(inputs[0]))
            status, reason, data = solve_one(inputs[0], a, display, job)
            display.finish(job, status, reason, "stdout")
        if status == SOLVED:
            try:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
            except BrokenPipeError:
                os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
                return FAILED
        return status

    records = [record_path(i, a.out) for i in inputs]
    clash = sorted({str(r) for r in records if records.count(r) > 1})
    if clash:
        raise UsageError(f"several inputs would write {clash[0]}")
    existing = [p for p in records if p.exists()]
    if existing and not a.overwrite and not replace_ok(existing):
        print("r2c: nothing solved", file=sys.stderr)
        return SOLVED
    if a.out:
        a.out.mkdir(parents=True, exist_ok=True)
    for p in existing:
        p.unlink()

    with Display(sys.stderr, live, a.quiet) as display:
        jobs = [display.add(job_name(i)) for i in inputs]

        def solve(k: int) -> int:
            status, reason, data = solve_one(inputs[k], a, display, jobs[k])
            if status == SOLVED:
                # whole or nothing: write under a temporary name, then rename
                tmp = records[k].with_name(records[k].name + ".part")
                tmp.write_bytes(data)
                os.replace(tmp, records[k])
            display.finish(jobs[k], status, reason, str(records[k]))
            return status

        with ThreadPoolExecutor(max_workers=a.parallel) as pool:
            statuses = list(pool.map(solve, range(len(inputs))))
        display.summary()
    return overall_status(statuses)


def cmd_health(a) -> int:
    import numpy
    print(f"r2c {__version__}; Python {sys.version.split()[0]}; numpy {numpy.__version__}")
    print(textwrap.fill(DISCLAIMER, 78))
    t0 = time.monotonic()
    try:
        result = run.solve(None)
    except Exception as e:      # noqa: BLE001 - health reports whatever went wrong
        print(f"self-check failed: {e}", file=sys.stderr)
        return FAILED
    peak = result.stages[result.peak]
    print(f"self-check: default section solved, {len(result.stages)} stages, peak moment "
          f"{peak.m / 1e6:.1f} kNm ({time.monotonic() - t0:.1f} s)")
    return SOLVED


SOLVE_DESCRIPTION = """\
Run a full sectional response and write the data of its control charts and
detail views, as r2x captures them from Response-2000 1.9.7.

Scope: axial load, moment and shear. Not interaction diagrams or member
response.
r2c never edits the input file. Options override the input. Options you
leave out keep the input's value, or Response's start-up default if the
input has none."""

SOLVE_EPILOG = """\
Results (NAME is the input file name, or newbeam without one):
  NAME.r2x.txt          Raw record, in r2x's format: chart data in Response's
                        export layout, with the input SHA-256 and the
                        settings in effect.

Exit status: 0 solved · 1 failed · 2 usage error · 3 out of scope
With several inputs, the most serious: 1, then 2, then 3.

Examples:
  r2c solve
  r2c solve beam.r2t --stage all
  r2c solve beam.r2t --views cracking,no-shear
  r2c solve beam.r2t --increment 0,1,1 --more-detail 2
  r2c solve col.rsp --units si --initial -2000,0,0 --increment 0,1,0
  r2c solve cases\\*.r2t --out results --parallel 4
  r2c solve beam.r2t --stdout | py parse.py

""" + textwrap.fill(DISCLAIMER, 78)


class HelpFormatter(argparse.RawTextHelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=24, width=80)

    def _format_action_invocation(self, action):
        if not action.option_strings:
            return f"{action.metavar} ..." if action.nargs in ("*", "+") else action.metavar
        names = ", ".join(action.option_strings)
        if action.nargs == 0:
            return names
        return f"{names} {self._format_args(action, action.dest.upper())}"


def _typed(fn, error):
    def convert(text):
        try:
            return fn(text)
        except error as e:
            raise argparse.ArgumentTypeError(str(e))
    return convert


def positive_int(text: str) -> int:
    try:
        n = int(text)
    except ValueError:
        n = 0
    if n < 1:
        raise argparse.ArgumentTypeError(f"{text!r}: expected a whole number, 1 or more")
    return n


def join_pair_values(argv: list[str]) -> list[str]:
    """--initial -2000,0,0 -> --initial=-2000,0,0, so argparse does not take -2000,0,0 for an
    option."""
    out, it = [], iter(argv)
    for arg in it:
        if arg in ("--initial", "--increment"):
            value = next(it, None)
            out.append(arg if value is None else f"{arg}={value}")
        else:
            out.append(arg)
    return out


def add_solve_options(s: argparse.ArgumentParser):
    stage_spec = _typed(parse_stages, StageError)
    views_spec = _typed(parse_views, ViewError)
    loads = _typed(parse_loads, ValueError)
    g = s.add_argument_group("Analysis")
    g.add_argument("--units", choices=UNITS, type=str.lower,
                   help="Units for loads and results.\n"
                        "Default: input's, else si.\n"
                        "  si     kN    kN·m    mm   MPa\n"
                        "  us     kip   kip·ft  in   psi, ksi\n"
                        "  kgcm   ton   ton·m   cm   kg/cm2, t/cm2")
    g.add_argument("--factors", choices=FACTORS, type=str.lower,
                   help="Material reduction factors.\n"
                        "Default: input's, else none.")
    g.add_argument("--initial", type=loads, metavar="N,M,V",
                   help="Initial load, in the units in effect.\n"
                        "Default: input's, else 0,0,0.")
    g.add_argument("--increment", type=loads, metavar="N,M,V",
                   help="Load increment; only signs and ratio matter.\n"
                        "0,0,0 solves the initial load alone.\n"
                        "Default: input's, else 0,1,0.\n"
                        "N: tension positive. M: compression on top positive.")
    g.add_argument("--more-detail", type=_typed(parse_more_detail, ValueError), default=0,
                   metavar="N",
                   help="Refine the solve N times (more load stages), or\n"
                        "max: until it refines no further.\n"
                        "Default: 0.")
    g = s.add_argument_group("Output")
    g.add_argument("--stage", type=stage_spec, default=stage_spec("peak"), metavar="STAGES",
                   help="Stages for the detail views: peak, all, or numbers\n"
                        "and ranges (0,10,20-30 or peak,0-5). 0 is the\n"
                        "initial load. Control charts always cover every\n"
                        "stage. Default: peak.")
    g.add_argument("--views", type=views_spec, default=views_spec("all"), metavar="VIEWS",
                   help="Detail views: all, or any of general, cracking,\n"
                        "reinforcement, no-shear. Default: all.")
    g.add_argument("--report", action="store_true", help=argparse.SUPPRESS)
    g.add_argument("--out", type=Path, metavar="DIR",
                   help="Folder for results. Default: next to each input.")
    g.add_argument("--stdout", action="store_true",
                   help="Write the raw record to stdout and no files. One\n"
                        "input only.")
    g.add_argument("--overwrite", action="store_true",
                   help="Replace existing results without asking. Default:\n"
                        "ask at a terminal, else stop.")
    g = s.add_argument_group("Running")
    g.add_argument("-p", "--parallel", type=positive_int, default=1, metavar="N",
                   help="Solve up to N inputs at once. Default: 1.")
    g.add_argument("-q", "--quiet", action="store_true", help="Errors only. Default: off.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="r2c", description="Sectional response of reinforced concrete from the command "
                                "line: a clone of Response-2000's analysis.",
        epilog=textwrap.fill(DISCLAIMER, 78), formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--version", action="version", version=f"r2c {__version__}")
    sub = p.add_subparsers(dest="command", metavar="{solve,health}")
    s = sub.add_parser("solve", help="solve inputs and write their chart data",
                       usage="r2c solve [INPUT ...] [options]", description=SOLVE_DESCRIPTION,
                       epilog=SOLVE_EPILOG, formatter_class=HelpFormatter)
    g = s.add_argument_group("Input")
    g.add_argument("inputs", nargs="*", metavar="INPUT",
                   help=".rsp or .r2t files; globs allowed (cases\\*.r2t).\n"
                        "Default: a new section, Response's default (Newbeam).")
    add_solve_options(s)
    s.set_defaults(func=cmd_solve)
    h = sub.add_parser("health", help="show versions and solve the default section")
    h.set_defaults(func=cmd_health)
    return p


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    a = parser.parse_args(join_pair_values(argv))
    if a.command is None:
        parser.print_help(sys.stderr)
        return USAGE
    try:
        return a.func(a)
    except UsageError as e:
        print(f"r2c: {e}", file=sys.stderr)
        return USAGE
    except KeyboardInterrupt:
        print("\nr2c: stopped (Ctrl+C)", file=sys.stderr)
        return FAILED


if __name__ == "__main__":
    raise SystemExit(main())
