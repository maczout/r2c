#!/usr/bin/env python3
"""Gather the evidence behind each deviation outside target, one file per cause.

    python tools/evidence.py VERIFY_OUT --archive ARCHIVE --inputs DIR [DIR ...] --out FOLDER
                             [--repeats ARCHIVE ...] [--traces DIR ...] [--decompile]
                             [--only CAUSE ...] [--jobs N] [--no-measure]

Answers, for the end-of-phase review (docs/review.md): what is there to show for each
cause, apart from the developer's word? VERIFY_OUT is the run of record as tools/verify.py
wrote it (r2c's records are needed, so the combined JSON is not enough). Two things are
written.

1. **docs/review/measured.json** (committed; the page reads it). For every view check
   outside target at an assessed stage, on every case: r2c's difference on that view when
   it is put into Response's own state at that stage, with the history of Response's
   stages before it (tools/sources.py's measure, here also on cases without shear), and
   how flat Response's curve is there. A cause in docs/review/causes.toml may be told by
   it ("inside in Response's own state"). --no-measure keeps the file as it is.

2. **FOLDER/evidence-NN.md, outside the repository**, one for each cause of
   docs/review/causes.toml that has a deviation, and one for each case with deviations no
   cause matches; FOLDER/index.json says which is which. A file holds the evidence only,
   for an assessor who has not seen the development (docs/review.md, "The independent
   assessment"): the instances with their sizes, the two responses (the control curves
   point by point, their features), the two programs' views at the compared stages, the
   outputs of the diagnostics the cause names, each under the command that made it, and
   the rules claimed with their addresses (the text of docs/kernel.md, without any
   sentence that speaks of decisions or known deviations; with --decompile
   the routine as tools/decompile.py prints it, which is why these files stay outside
   the repository). It does **not** hold the cause's name, the developer's reason, the
   owner's decisions or anything from the logs, and its file name is a number.

--repeats names further full captures of the same cases (for tools/repeat.py), --traces
folders of tools/rtrace.py logs (CASE.log). A diagnostic whose capture, trace or input
is not found is listed as not run, with why.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
import dashboard  # noqa: E402
import report  # noqa: E402
import review  # noqa: E402
import sources  # noqa: E402
import verify  # noqa: E402
from r2c import record  # noqa: E402

LONG = 400          # lines of one diagnostic's output kept
CASES_FULL = 4      # cases whose curves are printed in full
VIEWS_FULL = 4      # instances whose views are printed point by point
TELLS = re.compile(r"\bD\d+[a-z]?\b|known deviation|docs/(summary|status|verification)\.md"
                   r"|\bowner\b|\b[Tt]he developer\b")


# ---------------------------------------------------------------- measuring


def find_input(header: dict, inputs) -> Path | None:
    src = header["input-name"]
    if src.lower() in verify.BUILT_IN:
        return None
    return verify.find_input(src, header.get("input-sha256"), inputs)


def measure_one(args):
    """r2c in Response's own state at the stages of one case's view misses."""
    name, res, stages, archive, inputs = args
    capture = Path(archive) / f"{name}.r2x.txt"
    if not capture.exists():
        return name, {}, "no capture in the archive"
    ref = record.read(capture)
    if ref.header.get("stage-count") != res["ref"]["stage-count"]:
        return name, {}, (f"the capture has {ref.header.get('stage-count')} stages, the "
                          f"fixture {res['ref']['stage-count']}")
    try:
        own = sources.in_own_states(capture, find_input(ref.header, inputs), sorted(stages))
    except Exception as e:  # a state r2c cannot evaluate: say so, measure nothing
        return name, {}, f"r2c in Response's states: {type(e).__name__}: {e}"
    return name, {s: {"views": own[s], "spread": sources.spread(ref, s)} for s in own}, None


def measure(results: dict, devs: list[dict], archive, inputs, jobs: int) -> dict:
    want: dict[str, set] = {}
    for d in devs:
        if d["check"] == "view" and not d.get("missing"):
            want.setdefault(d["case"], set()).add(d["stage"])
    work = [(n, results[n], want[n], archive, inputs) for n in sorted(want)]
    with ProcessPoolExecutor(max_workers=max(jobs, 1)) as ex:
        done = list(ex.map(measure_one, work))
    by = {n: got for n, got, _note in done}
    out = {"checks": {}, "skipped": {n: note for n, _g, note in done if note}}
    for d in devs:
        got = by.get(d["case"], {}).get(d.get("stage"))
        if d["check"] == "view" and got is not None:
            own = got["views"].get(d["view"])
            out["checks"][d["key"]] = {"own": None if own is None else round(own, 2),
                                       "spread": round(got["spread"], 2)}
    return out


# ---------------------------------------------------------------- the pieces of a file


def describe(name: str, res: dict) -> list[str]:
    ref, c = res["ref"], res["control"][-1]
    out = [f"### {name}: {dashboard.label(ref)}", "",
           f"- Input `{ref['input-name']}`, units {ref['units']}, material factors "
           f"{ref['factors']}; initial loads (N, M, V) {ref['initial']}, increments "
           f"{ref['increment']}.",
           f"- Stages: Response {ref['stage-count']} (peak at stage {ref['peak-stage']}), "
           f"r2c {res['sub']['stage-count']} (peak at stage {res['sub']['peak-stage']}).",
           f"- Control chart `{c['chart']}`: peak load Response {c['ref_peak_load']:g} at "
           f"{c['ref_peak_x']:g}, r2c {c['sub_peak_load']:g} at {c['sub_peak_x']:g} "
           f"(difference {c['peak_diff_pct']:+.2f} %); rising branch "
           f"{c.get('rising_pct', float('nan')):.2f} %, post-peak "
           f"{c.get('post_peak_pct', float('nan')):.2f} % (the measure's own figures).",
           f"- Features of the curve as the measure reads them: Response "
           f"{', '.join(c.get('shape_ref', []))}; r2c {', '.join(c.get('shape_sub', []))}.", ""]
    return out


def curves(name: str, fixture: Path, sub: Path) -> list[str]:
    out = [f"Control curves of `{name}`, every stage, as (control value, load), in the "
           "record's own units. The stage number is the point's place in the list, from 0.",
           "", "```"]
    for who, path in (("Response", fixture), ("r2c", sub)):
        rec = record.read(path)
        for key in cmp.control_keys(rec):
            c = cmp._curve(rec, key)
            out.append(f"{who}, {key} ({len(c)} points): "
                       + " ".join(f"({x:.4g},{y:.5g})" for x, y in c))
    return out + ["```", ""]


def view_lines(d: dict, fixture: Path, sub: Path) -> list[str]:
    ref, rec = record.read(fixture), record.read(sub)
    out = [f"`{d['case']}`, {d['view']}: Response's stage {d['stage']} ({d['feature']}) "
           f"against r2c's stage {d['sub_stage']} ({d['matched'] or 'matched by the feature'})."
           " Each line of the chart as (value, depth) points, in the order drawn.", "", "```"]
    for who, r, s in (("Response", ref, d["stage"]), ("r2c", rec, d["sub_stage"])):
        try:
            lines = cmp.parse_chart(r.stage(s, d["view"]))[3]
        except KeyError:
            out.append(f"{who}: no such chart at stage {s}")
            continue
        if not lines:
            out.append(f"{who}: the chart has no line")
        for i, ln in enumerate(lines):
            out.append(f"{who} line {i}: " + " ".join(f"({x:.5g},{y:.5g})" for x, y in ln))
    return out + ["```", ""]


def instance_table(ds: list[dict]) -> list[str]:
    out = ["| Case | Check | Tier | Response's stage (feature) | r2c's stage | Difference | "
           "× target | Chart's largest value | Largest difference | r2c in Response's own "
           "state | Spread of Response's load nearby |",
           "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for d in ds:
        own = d.get("own") or {}
        if d["check"] == "view":
            out.append(
                f"| {d['case']} | {d['view']} | {review.TIER_NAME[d['tier']]} | {d['stage']} "
                f"({d['feature']}) | {d['sub_stage']} ({d['matched'] or 'by feature'}) | "
                + ("missing | – | " if d.get("missing") else
                   f"{d['pct']:.1f} % | {d['size']:.1f} | ")
                + f"{d['ref_max']:g} | {d['diff']:.4g} | "
                + ("not measured" if own.get("own") is None else f"{own['own']:.1f} %")
                + " | " + ("–" if "spread" not in own else f"{own['spread']:.2f} % of peak")
                + " |")
        elif d["size"] is None:
            out.append(f"| {d['case']} | shape | {review.TIER_NAME[d['tier']]} | – | – | "
                       f"Response: {', '.join(d['ref'])}; r2c: {', '.join(d['sub'])} | – | – "
                       "| – | – | – |")
        else:
            out.append(f"| {d['case']} | {d['check']} | {review.TIER_NAME[d['tier']]} | – | – "
                       f"| {d['pct']:.1f} % | {d['size']:.1f} | – | – | – | – |")
    return out + [""]


def kernel_excerpt(phrase: str, cap: int = 90) -> list[str]:
    """The part of docs/kernel.md that starts at the heading or lead-in holding `phrase`,
    up to the next heading or bold lead-in."""
    lines = (ROOT / "docs" / "kernel.md").read_text(encoding="utf-8").splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if phrase in ln and (ln.startswith(("#", "**", "*")))), None)
    if start is None:
        return [f"(no part of docs/kernel.md starts with \"{phrase}\")", ""]
    out = [lines[start]]
    for ln in lines[start + 1:]:
        if ln.startswith("#") or (ln.startswith("**") and not lines[start].startswith("#")) \
                or (ln.startswith("*") and lines[start].startswith("*")
                    and not lines[start].startswith("**") and not ln.startswith("**")
                    and re.match(r"\*[A-Z]", ln)):
            break
        out.append(ln)
        if len(out) >= cap:
            out.append("[… cut here]")
            break
    # the rule only: a sentence that speaks of the decisions, of known deviations or of
    # the working record is the developer's account of a deviation, and is left out
    kept = []
    for para in "\n".join(out).split("\n\n"):
        parts = re.split(r"(?<=[.:])\s+(?=[A-Z*`(\[])", para)
        kept.append(" ".join("[a sentence that refers to the record of decisions is left "
                             "out here]" if TELLS.search(x) else x for x in parts))
    return "\n\n".join(kept).splitlines() + [""]


class Paths:
    def __init__(self, a):
        self.a = a

    def fill(self, template: str, results: dict) -> tuple[list[str] | None, str]:
        """The command of a diagnostic with its placeholders filled in, or (None, why)."""
        a = self.a
        out = []
        for word in template.split():
            m = re.fullmatch(r"\{(\w+)(?::([\w.-]+))?\}", word)
            if not m:
                out.append(word)
                continue
            what, case = m.groups()
            if what == "verify":
                out.append(a.verify_out)
            elif what == "archive":
                out.append(a.archive)
            elif what == "repeats":
                # only the archives that hold every case the command names
                named = template.split("--only", 1)[1].split() if "--only" in template else []
                have = [r for r in a.repeats
                        if all((Path(r) / f"{c}.r2x.txt").exists() for c in named)]
                if not have:
                    return None, "no further capture of these cases under --repeats"
                out += have
            elif what == "fixture":
                out.append(str(ROOT / "tests" / "oracle" / f"{case}.r2x.txt"))
            elif what in ("capture", "record"):
                p = Path(a.archive if what == "capture" else a.verify_out) / f"{case}.r2x.txt"
                if not p.exists():
                    return None, f"no {what} of {case}"
                out.append(str(p))
            elif what == "input":
                p = find_input(results[case]["ref"] | {"input-sha256": record.read(
                    ROOT / "tests" / "oracle" / f"{case}.r2x.txt").header.get("input-sha256")},
                    a.inputs)
                if p is not None:
                    out += ["--input", str(p)]
            elif what == "trace":
                hit = [p for t in a.traces for p in Path(t).rglob(f"{case}.log")]
                if not hit:
                    return None, f"no trace of {case} under --traces"
                out.append(str(sorted(hit, key=lambda p: len(p.parts))[0]))
            else:
                return None, f"unknown placeholder {word}"
        return out, ""


def run_diag(job):
    template, cmd, why = job
    if cmd is None:
        return template, None, why
    p = subprocess.run([sys.executable if cmd[0] == "python" else cmd[0], *cmd[1:]],
                       cwd=ROOT, capture_output=True, text=True, timeout=1800)
    text = (p.stdout + (("\n[stderr]\n" + p.stderr) if p.returncode and p.stderr.strip()
                        else "")).rstrip()
    lines = text.splitlines()
    if len(lines) > LONG:
        lines = lines[:LONG // 2] + [f"[… {len(lines) - LONG} lines cut …]"] + lines[-LONG // 2:]
    return template, "\n".join(lines), "" if p.returncode in (0, 1) else f"exit {p.returncode}"


def decompile(address: str) -> str:
    p = subprocess.run([sys.executable, "tools/decompile.py", address], cwd=ROOT,
                       capture_output=True, text=True, timeout=600)
    lines = (p.stdout or p.stderr).splitlines()
    if len(lines) > LONG:
        lines = lines[:LONG] + [f"[… {len(lines) - LONG} more lines cut]"]
    return "\n".join(lines)


HEAD = """# Evidence file {n}

This file is evidence for one group of deviations between two programs, gathered by a
tool (`tools/evidence.py`) from a run and from diagnostics. It gives no explanation of
its own. It was made for an assessor who has not seen how the work was done.

**The two programs.** Response-2000 (1.9.7) is a sectional analysis program for
reinforced concrete: it takes a cross-section and a loading (axial load N, moment M,
shear V, as initial loads and increments) and steps through load stages, giving control
curves (load against curvature or shear strain) and, at each stage, detail charts over
the depth of the section ("views"). r2c is a clone of it. "Response" below is
Response-2000's own result (the reference); "r2c" is the clone's.

**The checks** (the targets are in `docs/acceptance.md`, given with this file). Each
case is checked on its peak load, its rising branch, its post-peak branch, the shape of
its curve (the order of its features: cracking, falls of load before the peak, the
peak, how it ends), and on each detail view at the stages of Response's curve where a
feature is (cracking, a fall of load, the peak, the last stage). A view's difference is
the largest distance between the two charts as a share of the chart's largest value;
"× target" is that difference divided by the target (5 %), after the printed-precision
floor. For a view check, Response's stage is compared with r2c's stage "at the same
place" on the control curve where there is one within the target, otherwise with r2c's
stage at the same feature.

**"r2c in Response's own state"** is a diagnostic: the strain state of Response's
stage (longitudinal strain, curvature, and the shear strain over the depth) is read
from Response's own charts, r2c's rules are evaluated in that state (carrying the
history of Response's earlier stages), and the same view is compared again. A small
difference there means r2c's rules give Response's chart from Response's state; a large
one means they do not, or that the charts do not give the state closely enough.
"Spread of Response's load nearby" is how much Response's load changes over the stage
and its two neighbours on one side, as a share of the peak: a small spread is a flat
part of the curve.

**A trace** (`tools/rtrace.py`, `tools/tries.py`) lists the tries of Response's own
load stage control, read from the running program, beside r2c's: each target tried,
whether it was kept, refused or not solved. It is a diagnostic, not reference data:
running under the tracer can change Response's result.
"""


def write_file(n: int, ds: list[dict], cause: dict | None, results: dict, a, paths: Paths,
               pool) -> Path:
    ds = sorted(ds, key=review._rank)
    out = [HEAD.format(n=f"{n:02d}"), "## The instances", "",
           f"{len(ds)} checks outside target on "
           f"{len({d['case'] for d in ds})} case(s), worst first.", ""]
    out += instance_table(ds)
    cases = list(dict.fromkeys(d["case"] for d in ds))
    out += ["## The two responses", ""]
    for name in cases:
        out += describe(name, results[name])
        if cases.index(name) < CASES_FULL:
            out += curves(name, ROOT / "tests" / "oracle" / f"{name}.r2x.txt",
                          Path(a.verify_out) / f"{name}.r2x.txt")
    views = [d for d in ds if d["check"] == "view" and not d.get("missing")][:VIEWS_FULL]
    if views:
        out += ["## The views at the compared stages", "",
                "The worst view checks, both programs' charts point by point.", ""]
        for d in views:
            out += view_lines(d, ROOT / "tests" / "oracle" / f"{d['case']}.r2x.txt",
                              Path(a.verify_out) / f"{d['case']}.r2x.txt")
    diags = (cause or {}).get("diagnostic", [])
    if diags:
        out += ["## Diagnostics", "",
                "Each is a tool of the repository run on this case; the command is given "
                "with placeholders for the folders (the run, the archive of Response's "
                "full captures, the inputs).", ""]
        jobs = [(g["run"], *paths.fill(g["run"], results)) for g in diags]
        for template, text, note in pool.map(run_diag, jobs):
            out += [f"### `{template}`", ""]
            if text is None:
                out += [f"Not run: {note}.", ""]
            else:
                out += (["```", text, "```"] + ([f"({note})"] if note else []) + [""])
    rules = (cause or {}).get("rule", [])
    if rules:
        out += ["## Rules claimed", "",
                "Where a rule of Response-2000's binary is claimed to bear on these "
                "instances: its address, the description of it in r2c's record of rules "
                "(`docs/kernel.md`), and, where given, the routine as decompiled.", ""]
        for r in rules:
            out += [f"### Address `{r['address']}`", ""] + kernel_excerpt(r["kernel"])
            if a.decompile:
                out += ["Decompiled (Ghidra, via `tools/decompile.py`):", "", "```c",
                        decompile(r["address"]), "```", ""]
    out += ["## What this file does not hold", "",
            "No explanation by the developer of r2c, no record of decisions, no session "
            "logs. Diagnostics other than those above were not run for this file.", ""]
    path = Path(a.out) / f"evidence-{n:02d}.md"
    path.write_text("\n".join(out), encoding="utf-8")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verify_out")
    ap.add_argument("--archive", required=True)
    ap.add_argument("--inputs", nargs="+", default=[])
    ap.add_argument("--out", required=True, help="a folder outside the repository")
    ap.add_argument("--repeats", nargs="*", default=[])
    ap.add_argument("--traces", nargs="*", default=[])
    ap.add_argument("--decompile", action="store_true")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--no-measure", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out).resolve()
    if ROOT in out.parents or out == ROOT:
        raise SystemExit("--out must be outside the repository (CLAUDE.md: data stays out)")
    out.mkdir(parents=True, exist_ok=True)
    a.inputs = [Path(p) for p in a.inputs]
    run, results = review.load_results(Path(a.verify_out))
    acc = report.read_acceptance(ROOT / "docs" / "acceptance.md")
    devs = [d for d in review.all_checks(results, acc) if not d["ok"]]
    target = review.REVIEW / "measured.json"
    if a.no_measure:
        measured = review.load_measured(target)
    else:
        measured = {"made_by": "tools/evidence.py", "run": run.get("commit", "")[:12],
                    **measure(results, devs, a.archive, a.inputs, a.jobs)}
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(measured, indent=1, sort_keys=True) + "\n")
        print(f"wrote {target.relative_to(ROOT)}: {len(measured['checks'])} view checks "
              f"measured; skipped: {measured['skipped'] or 'none'}")
    causes = review.load_causes()
    review.classify(devs, causes, measured)
    ents = review.entries(devs, causes)
    order = [c["id"] for c in causes.get("cause", [])]
    number = {cid: i + 1 for i, cid in enumerate(order)}
    extra = len(order)
    index = {}
    paths = Paths(a)
    with ThreadPoolExecutor(max_workers=max(a.jobs, 1)) as pool:
        for e in sorted(ents, key=lambda e: number.get(e["id"], 10 ** 6)):
            if e["id"] not in number:
                extra += 1
                number[e["id"]] = extra
            if a.only and e["id"] not in a.only:
                continue
            cause = None if e["cause"].get("unclassified") else e["cause"]
            p = write_file(number[e["id"]], e["instances"], cause, results, a, paths, pool)
            index[e["id"]] = p.name
            print(f"{p.name}: {e['id']}: {len(e['instances'])} checks on "
                  f"{len(e['cases'])} case(s)")
    (out / "index.json").write_text(json.dumps(index, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
