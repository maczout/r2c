#!/usr/bin/env python3
"""Interface parity with r2x (docs/brief.md): is r2c interchangeable with it?

    PYTHONPATH=R2X/src python tools/parity.py [--records VERIFY_OUT] [--inputs DIR ...] [--list]

Answers three questions and scores each as "N of M the same":

(a) **The command line.** Every subcommand, option, choice and default of r2x's parser set
    beside r2c's own, read from the two programs' parsers; and a list of command lines
    (ARGVS, good and bad values of every option) that each parser takes or refuses. Items
    r2x has for reaching Response itself are listed and not scored: `--image` (r2x's
    container) and `setup` (linking a Response-2000 folder). Nor are `define` and
    `--report`: they are not part of "the same command line" (owner, 2026-11-24,
    docs/brief.md); r2c refuses them.
(b) **The record** (--records). For every development fixture that has a record of r2c's in
    VERIFY_OUT: the header keys, their order and the form of their values; the control
    sections; the detail views at the peak; and each section's lines with every number
    reduced to its printed form. Values, stage counts and how many lines a chart has are
    the calculation's and are not compared here.
(c) **Refusals** (--inputs). Every input r2x is known to solve (each input a fixture was
    captured from) or to fail on (docs/scope-probes.md, measured through r2x), set beside
    whether r2c reads it and sets up its analysis. Nothing is solved, so an input on which
    Response fails part-way through its solve shows as a difference unless r2c refuses it.
    An input Response solves that its manual does not document is refused by r2c (owner,
    2026-11-24): it stays a difference in the score, and is counted on its own line as known.

--out FILE writes the result as a page (docs/parity.md, generated).

The headline says "complete except accepted refusals", with their count, when the only
differences left are those (owner, 2026-11-25), and "not complete" with the number of the
others otherwise. Exit status 0 when every part was run and parity is complete in that
sense, 1 otherwise. Needs r2x
importable; nothing is run against Response.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# r2x's own business: how it reaches Response-2000. Not part of being interchangeable.
NOT_SCORED = {"--image", "setup"}
# owner, 2026-11-24 (docs/brief.md, "Owner's decisions"): not part of "the same command
# line"; they stay refused by r2c and are left out of the score
LEFT_OUT = {"define", "--report"}


def describe(action: argparse.Action) -> dict:
    default = action.default
    return {
        "choices": sorted(map(str, action.choices)) if action.choices else None,
        "default": None if default in (None, argparse.SUPPRESS) else str(default),
        "nargs": action.nargs if action.nargs is not None else
        (0 if isinstance(action, (argparse._StoreTrueAction, argparse._StoreFalseAction,
                                  argparse._VersionAction, argparse._HelpAction)) else 1),
        "hidden": action.help == argparse.SUPPRESS,
    }


def surface(parser: argparse.ArgumentParser, prefix: str = "") -> dict[str, dict]:
    """{item: description} for a parser and its subcommands. An option is named by its
    longest flag; a positional by its dest."""
    out: dict[str, dict] = {}
    for a in parser._actions:
        if isinstance(a, argparse._SubParsersAction):
            for name, sub in a.choices.items():
                out[f"{prefix}{name}"] = {"subcommand": True}
                out.update(surface(sub, f"{prefix}{name} "))
        elif isinstance(a, (argparse._HelpAction, argparse._VersionAction)):
            out[prefix + max(a.option_strings, key=len)] = {"nargs": 0}
        else:
            name = max(a.option_strings, key=len) if a.option_strings else f"<{a.dest}>"
            out[prefix + name] = describe(a)
    return out


def compare(theirs: dict, ours: dict) -> tuple[list[str], list[tuple[str, str]], list[str]]:
    """(same, different with why, not scored) over r2x's items."""
    same, diff, skipped = [], [], []
    for item, d in theirs.items():
        if set(item.split()) & (NOT_SCORED | LEFT_OUT):
            skipped.append(item)
        elif item not in ours:
            diff.append((item, "r2c does not have it"))
        elif ours[item] != d:
            why = "; ".join(f"{k}: r2x {d.get(k)!r}, r2c {ours[item].get(k)!r}"
                            for k in sorted(set(d) | set(ours[item]))
                            if d.get(k) != ours[item].get(k))
            diff.append((item, why))
        else:
            same.append(item)
    return same, diff, skipped


# ---------------------------------------------------------------------------------------
# (a2) option values: does each parser take the same command lines?
# ---------------------------------------------------------------------------------------

ARGVS = [
    "solve a.r2t", "solve a.r2t b.rsp", "solve", "solve --new", "solve a.r2t --units si",
    "solve a.r2t --units US", "solve a.r2t --units kgcm", "solve a.r2t --units metric",
    "solve a.r2t --factors csa", "solve a.r2t --factors aci", "solve a.r2t --initial 0,0,0",
    "solve a.r2t --initial=-2000,0,0", "solve a.r2t --initial 1,2", "solve a.r2t --initial a,b,c",
    "solve a.r2t --increment 0,1,1", "solve a.r2t --increment 0,0,0",
    "solve a.r2t --more-detail 2", "solve a.r2t --more-detail max",
    "solve a.r2t --more-detail -1", "solve a.r2t --more-detail x", "solve a.r2t --stage peak",
    "solve a.r2t --stage all", "solve a.r2t --stage 1,5-9", "solve a.r2t --stage 0",
    "solve a.r2t --stage 9-5", "solve a.r2t --stage last", "solve a.r2t --views all",
    "solve a.r2t --views general,cracking", "solve a.r2t --views no-shear",
    "solve a.r2t --views shear", "solve a.r2t --out d", "solve a.r2t --stdout",
    "solve a.r2t --overwrite", "solve a.r2t -p 4", "solve a.r2t -p 0", "solve a.r2t -q",
    "solve a.r2t --report", "solve a.r2t --bogus", "health", "health --json", "bogus", "",
    "--version", "define units", "setup",
]


def parses(parser_fn, argv: list[str]) -> str:
    """"takes", or "refuses (exit N)", for a command line given to a parser."""
    import contextlib
    import io

    try:
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            parser_fn().parse_args(argv)
        return "takes"
    except SystemExit as e:
        return "takes" if e.code in (0, None) else f"refuses (exit {e.code})"


def option_values(theirs, ours) -> tuple[int, list[str]]:
    same, diff = 0, []
    for line in ARGVS:
        if set(line.split()) & (NOT_SCORED | LEFT_OUT):
            continue
        x, c = parses(theirs.build_parser, line.split()), parses(ours.build_parser, line.split())
        if x == c:
            same += 1
        else:
            diff.append(f"`{line or '(nothing)'}`: r2x {x}, r2c {c}")
    return same, diff


# ---------------------------------------------------------------------------------------
# (b) the record
# ---------------------------------------------------------------------------------------

# header lines that say which program and machine made the record, on either side; and the
# input's hash, which tools/verify.py's records lack where r2c used its built-in Newbeam
MACHINE = {"r2x-version", "wine-version", "disclaimer", "response-exe-sha256",
           "response-files-sha256", "response-verified", "r2c-version", "kernel",
           "input-sha256"}
NUMBER = re.compile(r"-?\d+(\.\d+)?([eE][-+]?\d+)?")


def skeleton(body: bytes) -> set[str]:
    """The lines of a section with every number reduced to its printed form (#.k for k
    decimals): what a reader of the format depends on, whatever the values are."""
    out = set()
    for ln in body.decode("latin-1").split("\r\n"):
        if ln == "New Line":      # a chart of two lines or one: the state's, not the format's
            continue
        out.add(NUMBER.sub(lambda m: "#." + str(len((m.group(1) or ".")) - 1), ln))
    return out


def shape(value: str) -> str:
    return re.sub(r"\d+", "N", value)


def record_diffs(ref, sub) -> list[str]:
    """How two records of the same case differ as a format: header keys and the form of
    their values, the control sections and the detail views at the peak, and the lines of
    each as skeletons. Stage counts and values are the calculation's, not the format's."""
    out = []
    kr = [k for k in ref.header if k not in MACHINE]
    ks = [k for k in sub.header if k not in MACHINE]
    if kr != ks:
        out.append(f"header keys: only r2x {sorted(set(kr) - set(ks))}, only r2c "
                   f"{sorted(set(ks) - set(kr))}" if set(kr) != set(ks) else "header key order")
    for k in ("units", "factors", "initial", "increment", "more-detail", "views"):
        if k in ref.header and k in sub.header and ref.header[k] != sub.header[k]:
            out.append(f"header {k}: r2x {ref.header[k]!r}, r2c {sub.header[k]!r}")
    for k in ("stage-count", "peak-stage"):     # detail-stages: a fixture lists the kept ones
        if k in ref.header and k in sub.header and shape(ref.header[k]) != shape(sub.header[k]):
            out.append(f"header {k}: form r2x {ref.header[k]!r}, r2c {sub.header[k]!r}")
    cr = [n for n in ref.sections if n.startswith("control/")]
    cs = [n for n in sub.sections if n.startswith("control/")]
    if cr != cs:
        out.append(f"control sections: r2x {cr}, r2c {cs}")
    pr, ps = ref.header.get("peak-stage"), sub.header.get("peak-stage")
    vr = [n.split("/", 2)[2] for n in ref.sections if n.startswith(f"stage/{pr}/")]
    vs = [n.split("/", 2)[2] for n in sub.sections if n.startswith(f"stage/{ps}/")]
    if vr != vs:
        out.append(f"detail views at the peak: only r2x {sorted(set(vr) - set(vs))}, only r2c "
                   f"{sorted(set(vs) - set(vr))}" if set(vr) != set(vs) else "detail view order")
    pairs = [(n, n) for n in cr if n in cs] + \
            [(f"stage/{pr}/{v}", f"stage/{ps}/{v}") for v in vr if v in vs]
    for a, b in pairs:
        sa, sb = skeleton(ref.sections[a]), skeleton(sub.sections[b])
        if sa != sb:
            name = a if a.startswith("control/") else "view " + a.split("/", 2)[2]
            only_x = sorted(sa - sb)[:2]
            only_c = sorted(sb - sa)[:2]
            out.append(f"{name}: lines only r2x {only_x}, only r2c {only_c}")
    return out


def records(fixtures: Path, theirs_dir: Path) -> tuple[int, int, dict[str, list[str]]]:
    """(cases the same, cases compared, {difference: [cases]}) over the fixtures that have a
    record of r2c's in theirs_dir (a tools/verify.py output)."""
    from r2c import record

    same = n = 0
    by: dict[str, list[str]] = {}
    for fx in sorted(fixtures.glob("*.r2x.txt")):
        mine = theirs_dir / fx.name
        if not mine.exists():
            continue
        n += 1
        d = record_diffs(record.read(fx), record.read(mine))
        same += not d
        for line in d:
            by.setdefault(line, []).append(fx.name[: -len(".r2x.txt")])
    return same, n, by


# ---------------------------------------------------------------------------------------
# (c) refusals
# ---------------------------------------------------------------------------------------

def r2x_outcomes(folders) -> dict[str, tuple[str, object]]:
    """{name: ("solves" or "fails", how to get the input)} as measured through r2x: every
    input a fixture was captured from solves; the probes of docs/scope-probes.md solve or
    fail as its table says (measured 2026-11-21 with tools/probe.py)."""
    import variants
    from r2c import record

    out: dict[str, tuple[str, object]] = {}
    seen = set()
    for fx in sorted((ROOT / "tests" / "oracle").rglob("*.r2x.txt")):
        h = record.read(fx).header
        key = h.get("input-sha256", h["input-name"])
        if key in seen or h["input-name"] == "File > New":
            continue
        seen.add(key)
        out[f"input {h['input-name']} ({key[:8]})"] = ("solves", (h["input-name"], key))
    for ln in (ROOT / "docs" / "scope-probes.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in ln.split("|")]
        if len(cells) > 7 and cells[1] in variants.VARIANTS:
            ok = re.match(r"\d+ stages", cells[6]) is not None
            out[f"probe {cells[1]}"] = ("solves" if ok else "fails", cells[1])
    return out


def r2c_outcome(how, folders, tmp: Path) -> str:
    import numpy as np
    import variants
    import verify
    from r2c import inputs, run
    from r2c.materials import ConcreteLaw

    initial = increment = None
    if isinstance(how, tuple):
        path = verify.find_input(how[0], how[1], folders)
        if how[0].lower() in verify.BUILT_IN:
            return "solves"
        if path is None:
            return "input not found"
    else:
        v = variants.VARIANTS[how]
        path = tmp / f"{how}.r2t"
        path.write_bytes(variants.build(how, folders))
        initial, increment = v.initial, v.increment
    try:
        run.setup(path, initial=initial and tuple(float(x) for x in initial.split(",")),
                  increment=increment and tuple(float(x) for x in increment.split(",")))
        for c in inputs.read(path).concretes:
            ConcreteLaw(c).soften(np.array([1e-3]), np.array([-1e-3]))
        return "solves"
    except inputs.OutOfScope as e:
        return f"refuses: {e}"
    except Exception as e:  # noqa: BLE001 - reported as what r2c does
        return f"fails: {type(e).__name__}: {e}"


def refusals(folders) -> tuple[int, int, list[str]]:
    import tempfile

    same = n = 0
    diff = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, (theirs, how) in r2x_outcomes(folders).items():
            mine = r2c_outcome(how, folders, Path(tmp))
            if mine == "input not found":
                continue
            n += 1
            if (theirs == "solves") == (mine == "solves"):
                same += 1
            else:
                diff.append(f"{name}: r2x {theirs}, r2c {mine}")
    return same, n, diff


def outside_manual(difference: str) -> bool:
    """Is this difference of part (c) an input Response solves and r2c does not, because
    the manual does not document it (docs/scope.md)? Known differences by the owner's
    decision of 2026-11-24; r2c's refusals are scope's and nothing else's."""
    return ": r2x solves, r2c refuses: " in difference or "units='roman'" in difference


# The four inputs on which Response gives up part-way through its solve and r2x fails,
# while r2c solves them: accepted as known differences by the owner (2026-11-25,
# docs/brief.md). These four and no others: a new input of the kind is a difference.
GIVES_UP = {"newbeam-csoft1", "newbeam-loads-ntension-mv", "newbeam-loads-m0-v",
            "newbeam-loads-nv"}


def gives_up(difference: str) -> bool:
    """Is this difference of part (c) one of the four the owner accepted on 2026-11-25:
    Response gives up part-way, r2x fails, r2c solves?"""
    m = re.fullmatch(r"probe (\S+): r2x fails, r2c solves", difference)
    return bool(m) and m.group(1) in GIVES_UP


def verdict(same: int, n: int, accepted: int, every_part: bool = True,
            gave_up: int = 0) -> str:
    """The headline, in the form the owner asked for (2026-11-25, docs/brief.md): parity is
    complete when the only differences left are the inputs refused by the owner's decision
    (accepted) and the inputs Response gives up on part-way, accepted the same day
    (gave_up)."""
    head = f"{same} of {n} checks the same"
    if not every_part:
        return f"Interface parity: {head} (partial: not every part was run)"
    other = n - same - accepted - gave_up
    known = f"{accepted} accepted refusals" + (
        f" and the {gave_up} accepted inputs on which Response gives up part-way"
        if gave_up else "")
    if other:
        return (f"Interface parity: not complete: {other} difference(s) besides the "
                f"{known} ({head})")
    if gave_up:
        return (f"Interface parity: complete except accepted refusals ({accepted}, and "
                f"{gave_up} accepted inputs on which Response gives up part-way; {head})")
    if accepted:
        return f"Interface parity: complete except accepted refusals ({accepted}; {head})"
    return f"Interface parity: complete ({head})"


GENERATED = "<!-- Generated by tools/parity.py --out. Do not edit: rerun it. -->"


def render(head: str, lines: list[str]) -> str:
    out = [GENERATED, "", "# Interface parity with r2x", "",
           "What `tools/parity.py` finds when it sets r2c beside r2x (its docstring says how "
           "each part is measured). Nothing is run against Response. A difference is listed "
           "whether or not it is meant to be closed; `docs/deviations.md` says which are "
           "known and why. `define` and `--report` of r2x are not part of the command line "
           "that is compared and are left out of the score (owner, 2026-11-24).", "", f"**{head}.**", ""]
    for ln in lines:
        out.append(("  - `" + ln.strip().split(None, 1)[1].replace("`", "'") + "`") if ln.startswith("    ")
                   else f"- **{ln}**")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--list", action="store_true", help="print every command-line item")
    ap.add_argument("--records", metavar="VERIFY_OUT",
                    help="(b): a tools/verify.py output on tests/oracle, for r2c's records")
    ap.add_argument("--inputs", nargs="*", default=[],
                    help="(c): the folders inputs are found in (as for tools/verify.py)")
    ap.add_argument("--out", metavar="FILE", help="also write the result (docs/parity.md)")
    a = ap.parse_args(argv)
    try:
        from r2x import cli as theirs
    except ImportError:
        print("r2x is not importable: set PYTHONPATH to its src folder")
        return 2
    from r2c import cli as ours

    total = [0, 0]
    known: list[str] = []
    gave_up: list[str] = []

    lines: list[str] = []
    say = lines.append

    def scored(title, same, n):
        total[0] += same
        total[1] += n
        say(f"{title}: {same} of {n} the same")

    x, c = surface(theirs.build_parser()), surface(ours.build_parser())
    same, diff, skipped = compare(x, c)
    extra = sorted(set(c) - set(x))
    scored("(a) command line, the items of r2x's parser", len(same), len(same) + len(diff))
    for item, why in diff:
        say(f"    differs  {item}: {why}")
    for item in extra:
        say(f"    only r2c {item}")
    if a.list:
        for item in same:
            say(f"    same     {item}")
        for item in skipped:
            say(f"    skipped  {item} (r2x's own access to Response, or left out by the owner)")
    same, diff = option_values(theirs, ours)
    scored("(a) command line, command lines taken or refused alike", same, same + len(diff))
    for d in diff:
        say(f"    differs  {d}")
    if a.records:
        same, n, by = records(ROOT / "tests" / "oracle", Path(a.records))
        scored("(b) the record, development cases with the same format", same, n)
        for line, names in sorted(by.items(), key=lambda kv: -len(kv[1])):
            say(f"    differs  on {len(names)} case(s), e.g. {names[0]}: {line}")
    else:
        say("(b) the record: not run (give --records VERIFY_OUT)")
    if a.inputs:
        same, n, diff = refusals(a.inputs)
        scored("(c) refusals, inputs solved or refused alike", same, n)
        known = [d for d in diff if outside_manual(d)]
        gave_up = [d for d in diff if gives_up(d)]
        for d in diff:
            if d not in known and d not in gave_up:
                say(f"    differs  {d}")
        if gave_up:
            say(f"(c) of these differences, known: {len(gave_up)} are inputs on which "
                "Response gives up part-way through its solve and r2c solves, accepted by "
                "the owner (2026-11-25)")
            for d in gave_up:
                say(f"    known    {d}")
        if known:
            say(f"(c) of these differences, known: {len(known)} are inputs outside the manual "
                "that r2c refuses by the owner's decision (2026-11-24)")
            for d in known:
                say(f"    known    {d}")
    else:
        say("(c) refusals: not run (give --inputs FOLDERS)")
    complete = bool(a.records and a.inputs)
    head = verdict(total[0], total[1], len(known) if a.inputs else 0, complete,
                   len(gave_up))
    print("\n".join(lines + [head]))
    if a.out:
        if not complete:
            ap.error("--out needs every part: give --records and --inputs")
        Path(a.out).write_text(render(head, lines), encoding="utf-8")
    return 0 if complete and total[1] - total[0] == len(known) + len(gave_up) else 1

if __name__ == "__main__":
    raise SystemExit(main())
