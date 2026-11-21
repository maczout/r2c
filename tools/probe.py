#!/usr/bin/env python3
"""Does Response-2000 accept an input, and does a feature reach its analysis? Measured with
r2x's worker, for docs/scope.md.

    python tools/probe.py OUT_DIR --response-dir DIR --inputs DIR [DIR ...]
                          [--only NAME ...] [--file INPUT --base BASE] [--no-save] [--report]

For each variant of tools/variants.py (built into OUT_DIR/inputs), or for one --file:

1. **Save As.** Response opens the file and saves it again (r2x's `define --screen`); the
   saved file, OUT_DIR/saved/NAME.r2t, is how Response read the input. The elements that
   differ from the input's are kept (an attribute Response dropped or rewrote shows here);
   the order of the elements is not compared, since Response writes the layers in its own.
2. **Solve.** r2x's worker solves it at the variant's loads, detail views at the peak only;
   the record goes to OUT_DIR/NAME.r2x.txt (with --report, the report with Response's input
   screen beside it). Kept: exit status, stage count, peak stage, and the largest load on
   each control chart.
3. **The base.** The variant's base input is solved the same way, once per set of loads, so
   that "the feature reaches the analysis" is measured: the ratio of the peaks, and how many
   of the charts differ from the base's by a byte.
4. **r2c.** Whether r2c reads the input and sets up its analysis, or refuses it and with
   what words. Nothing is solved here; tools/verify.py does that.

Results: OUT_DIR/probe.json (everything, merged with earlier runs) and a table on stdout.
Runs go one at a time in the default Wine prefix; about 15 s a variant.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402

import compare  # noqa: E402
import variants  # noqa: E402
from r2c import inputs, record, run  # noqa: E402
from r2c.materials import ConcreteLaw  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORKER = [sys.executable, "-m", "r2x.worker"]


def beam_elements(data: bytes) -> list[str]:
    """The elements of the first <r3g_beam>, each on one line without layout, sorted: what
    the section is, whatever order Response writes its layers in."""
    text = data.decode("latin1")
    a = text.find("<r3g_beam")
    b = text.find("</r3g_beam>")
    out, cur = [], []
    for ln in text[a:b].splitlines():
        s = " ".join(ln.split())
        if not s:
            continue
        if s.startswith("<") and not s.startswith("</") and cur:
            out.append(" ".join(cur))
            cur = []
        cur.append(s)
    if cur:
        out.append(" ".join(cur))
    return sorted(out)


def save_as(inp: Path, out: Path, response_dir: str) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    cmd = WORKER + ["define", "--screen", "probe", "--input", str(inp), "--out", str(out),
                    "--response-dir", response_dir]
    p = subprocess.run(cmd, capture_output=True, text=True)
    res = {"exit": p.returncode, "saved": out.exists()}
    if not out.exists():
        res["stderr"] = p.stderr[-600:]
        return res
    a, b = beam_elements(inp.read_bytes()), beam_elements(out.read_bytes())
    res["diff"] = [d for d in difflib.unified_diff(a, b, lineterm="", n=0)
                   if d[:1] in "+-" and d[:3] not in ("+++", "---")]
    return res


def solve(inp: Path, rec_path: Path, response_dir: str, initial: str | None,
          increment: str | None,
          report: Path | None = None) -> dict:
    if rec_path.exists():
        rec_path.unlink()
    cmd = WORKER + [str(inp), str(rec_path), "--stage", "peak", "--response-dir", response_dir]
    if initial is not None:
        cmd.append(f"--initial={initial}")
    if increment is not None:
        cmd.append(f"--increment={increment}")
    if report is not None:
        cmd += ["--report", str(report)]
    t = time.monotonic()
    p = subprocess.run(cmd, capture_output=True, text=True)
    res = {"exit": p.returncode, "seconds": round(time.monotonic() - t, 1),
           "initial": initial, "increment": increment}
    notes = [ln for ln in p.stderr.splitlines() if "note" in ln or "failed" in ln]
    if notes:
        res["notes"] = notes[-5:]
    if p.returncode != 0 or not rec_path.exists():
        res["stderr"] = p.stderr[-600:]
        return res
    rec = record.read(rec_path)
    res["stages"] = int(rec.header["stage-count"])
    res["peak-stage"] = int(rec.header["peak-stage"])
    res["units"] = rec.header["units"]
    res["factors"] = rec.header["factors"]
    res["loads"] = rec.header["initial"] + " + " + rec.header["increment"]
    peaks = {}
    for key in compare.control_keys(rec):
        c = compare._curve(rec, key)
        if len(c):
            i = int(np.argmax(np.abs(c[:, 1])))
            peaks[key] = [float(c[i, 0]), float(c[i, 1])]
    res["peaks"] = peaks
    return res


def charts_differ(rec_path: Path, base_path: Path) -> dict:
    """How many of the record's charts (control charts, and the detail views at the peak)
    differ from the base's by a single byte. None differing: the feature does not reach the
    analysis, as far as this loading shows."""
    a, b = record.read(rec_path), record.read(base_path)
    keys = sorted(set(a.sections) | set(b.sections))
    return {"total": len(keys),
            "differ": sum(1 for k in keys if a.sections.get(k) != b.sections.get(k)),
            "same-stages": a.header["stage-count"] == b.header["stage-count"]
            and a.header["peak-stage"] == b.header["peak-stage"]}


def r2c_reads(inp: Path, initial: str, increment: str) -> dict:
    try:
        su = run.setup(inp, initial=initial and tuple(float(x) for x in initial.split(",")),
                       increment=increment and tuple(float(x) for x in increment.split(",")))
        for c in inputs.read(inp).concretes:
            ConcreteLaw(c).soften(np.array([1e-3]))
        return {"reads": True, "units": su.units.name}
    except inputs.OutOfScope as e:
        return {"reads": False, "refused": str(e)}
    except Exception as e:  # noqa: BLE001  (the probe reports whatever r2c does)
        return {"reads": False, "error": f"{type(e).__name__}: {e}"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="folder for the probe's files (outside the repository)")
    ap.add_argument("--response-dir", default=os.environ.get("R2X_RESPONSE_DIR"))
    ap.add_argument("--inputs", nargs="*", default=[], help="folders with the base inputs")
    ap.add_argument("--only", nargs="*", help="variant names (default: all)")
    ap.add_argument("--file", help="probe this input instead of the variants")
    ap.add_argument("--base", help="with --file: the input to compare its solve with")
    ap.add_argument("--initial", default="0,0,0", help="with --file: N,M,V at the start")
    ap.add_argument("--increment", default="0,1,1", help="with --file: the N,M,V increment")
    ap.add_argument("--no-save", action="store_true", help="skip the Save As step")
    ap.add_argument("--report", action="store_true", help="keep r2x's report of each solve")
    ap.add_argument("--table", metavar="FILE",
                    help="write OUT_DIR/probe.json as a Markdown table to FILE and stop")
    a = ap.parse_args(argv)
    if a.table:
        results = json.loads((Path(a.out) / "probe.json").read_text())
        Path(a.table).write_text(table(results))
        return 0
    if not a.response_dir:
        ap.error("--response-dir or $R2X_RESPONSE_DIR is required")
    out = Path(a.out).resolve()
    if ROOT in out.parents or out == ROOT:
        ap.error("the probe's files belong outside the repository")
    (out / "inputs").mkdir(parents=True, exist_ok=True)
    jpath = out / "probe.json"
    results = json.loads(jpath.read_text()) if jpath.exists() else {}

    jobs = []   # (name, input path, base path or None, initial, increment, what)
    if a.file:
        p = Path(a.file)
        jobs.append((p.stem, p, Path(a.base) if a.base else None, a.initial, a.increment, ""))
    else:
        for name in a.only or list(variants.VARIANTS):
            v = variants.VARIANTS[name]
            p = out / "inputs" / f"{name}.r2t"
            p.write_bytes(variants.build(name, a.inputs))
            base = out / "inputs" / f"{v.base}.r2t"
            if not base.exists():
                base.write_bytes(variants.find_base(v.base, a.inputs).read_bytes())
            jobs.append((name, p, base, v.initial, v.increment, v.what))

    for name, p, base, initial, increment, what in jobs:
        entry = {"what": what, "input": p.name}
        if base is not None:
            bkey = f"base:{base.stem}:{initial}:{increment}"
            if bkey not in results or "record" not in results[bkey]:
                tag = f"{initial}+{increment}".replace(",", "_").replace("None", "file")
                results[bkey] = solve(base, out / f"base-{base.stem}-{tag}.r2x.txt",
                                      a.response_dir, initial, increment)
                results[bkey]["record"] = f"base-{base.stem}-{tag}.r2x.txt"
            entry["base"] = bkey
        if not a.no_save:
            entry["save"] = save_as(p, out / "saved" / p.name, a.response_dir)
        entry["solve"] = solve(p, out / f"{name}.r2x.txt", a.response_dir, initial, increment,
                               out / f"{name}.html" if a.report else None)
        if base is not None and entry["solve"]["exit"] == 0 and results[bkey]["exit"] == 0:
            entry["solve"]["charts"] = charts_differ(out / f"{name}.r2x.txt",
                                                     out / results[bkey]["record"])
        entry["r2c"] = r2c_reads(p, initial, increment)
        results[name] = entry
        jpath.write_text(json.dumps(results, indent=1))
        print(line(name, entry, results), flush=True)
    return 0


def table(results: dict) -> str:
    """probe.json as Markdown: one row per probe."""
    out = ["# Scope probes: what Response-2000 does with each input",
           "",
           "Generated by `python tools/probe.py OUT_DIR --table docs/scope-probes.md` from the "
           "probe's results; do not edit. Each row is one input of `tools/variants.py` put "
           "through r2x's worker: Response's own Save As of it, and a solve at the loads "
           "shown, compared with the same solve of the variant's base. What the rows mean for "
           "r2c's scope is in `docs/scope.md`.",
           "",
           "- **Save As**: how many elements of the section differ between the input and "
           "Response's own save of it (0: Response read every attribute as given; the order "
           "of the elements is not compared).",
           "- **Peak / base**: the largest load on the bottom control chart over the base's.",
           "- **Charts**: how many charts (control charts and the detail views at the peak) "
           "differ from the base's by a byte. `0 of n`: the feature does not reach the "
           "analysis at this loading. Where the stage count or the peak stage differs, every "
           "chart at the peak counts as different.",
           "- **r2c**: whether r2c reads the input and sets up its analysis (nothing is "
           "solved here).",
           "",
           "| Probe | Base | What | Loads (initial + increment) | Save As | r2x solve | "
           "Peak / base | Charts | r2c |",
           "|---|---|---|---|---|---|---|---|---|"]
    for name, e in results.items():
        if name.startswith("base:"):
            continue
        s = e["solve"]
        b = results.get(e.get("base", ""), {})
        base = e.get("base", "").split(":")[1] if e.get("base") else ""
        loads = f"{s.get('initial') or 'file'} + {s.get('increment') or 'file'}"
        sv = e.get("save")
        if not sv:
            save = ""
        elif not sv["saved"]:
            save = "refused: " + reason(sv.get("stderr", ""))
        else:
            save = f"{len(sv['diff'])} differ"
        ratio = charts = ""
        if s["exit"] != 0:
            solved = "**failed**: " + reason(s.get("stderr", ""))
        else:
            solved = f"{s['stages']} stages, peak {s['peak-stage']}"
            if s.get("units") not in (None, "si") or s.get("factors") != "1.00,1.00,1.00":
                solved += f" ({s['units']}; factors {s['factors']})"
            if b.get("peaks") and s.get("units") == b.get("units"):
                key = list(s["peaks"])[-1]
                by = b["peaks"].get(key, [0, 0])[1]
                if by:
                    ratio = f"{s['peaks'][key][1] / by:.4f}"
            if "charts" in s:
                charts = f"{s['charts']['differ']} of {s['charts']['total']}"
        c = e["r2c"]
        r2c = "reads" if c["reads"] else "**no**: " + c.get("refused", c.get("error", "?"))
        out.append(f"| {name} | {base} | {e.get('what', '')} | {loads} | {save} | {solved} | "
                   f"{ratio} | {charts} | {r2c} |")
    return "\n".join(out) + "\n"


def reason(stderr: str) -> str:
    """The last line of r2x's complaint, shortened."""
    lines = [ln for ln in stderr.strip().splitlines() if ln.strip()]
    text = lines[-1] if lines else "?"
    text = text.replace("r2x: failed: ", "").replace("|", "/")
    return text if len(text) <= 150 else text[:147] + "..."


def line(name: str, e: dict, results: dict) -> str:
    s = e["solve"]
    if s["exit"] != 0:
        r2x = f"r2x FAILED ({s.get('stderr', '').strip().splitlines()[-1][:90] if s.get('stderr') else s['exit']})"
    else:
        r2x = f"r2x solved, {s['stages']} stages, peak {s['peak-stage']}"
        b = results.get(e.get("base", ""), {})
        if b.get("peaks"):
            ratios = []
            for k, (_, y) in s["peaks"].items():
                by = b["peaks"].get(k, [0, 0])[1]
                if by:
                    ratios.append(f"{k} {y / by:.4f}")
            r2x += "; peak/base: " + ", ".join(ratios)
            if s["stages"] != b.get("stages"):
                r2x += f" (base {b.get('stages')} stages)"
            if "charts" in s:
                r2x += f"; {s['charts']['differ']} of {s['charts']['total']} charts differ"
    sv = e.get("save")
    save = ""
    if sv:
        save = ("; Save As: " + (f"{len(sv['diff'])} elements differ" if sv["saved"]
                                 else "FAILED"))
    c = e["r2c"]
    r2c = "r2c reads it" if c["reads"] else "r2c: " + c.get("refused", c.get("error", "?"))
    return f"{name}: {r2x}{save}; {r2c}"


if __name__ == "__main__":
    raise SystemExit(main())
