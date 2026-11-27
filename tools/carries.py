#!/usr/bin/env python3
"""Does r2c's record carry the data of every chart that r2x's record of Response does?

    python tools/carries.py ARCHIVE VERIFY_OUT [--list] [--out docs/output-check.md]

Answers the handover question for r2 (owner, 2026-11-27): r2c's output must carry the
data for every one of Response's summary (control) and detail views that r2x's does, and
not only what the fixtures compare. The fixtures are captures cut to the stages the
measure compares, and tools/parity.py looks at the detail views at the peak only. Here
the two whole records of each development case are set side by side: r2x's full capture
(ARCHIVE/NAME.r2x.txt: every stage, every view) and r2c's full record of the same case
(VERIFY_OUT/NAME.r2x.txt, as tools/verify.py writes it). No value is compared: that is
the measure's business (docs/measures.md). What is compared is what a reader of the
record can find in it:

1. **Header keys**: every key of r2x's record that is not about r2x's own machinery
   (Response's and Wine's identification) is in r2c's.
2. **Control charts**: the same sections, in the same order.
3. **Detail views**: every stage of each record has every chart of the views named in
   its header, each once, in the order of the catalogue (src/r2c/views.json, which is
   r2x's own, and the check says if the two files differ when r2x is importable).
4. **Each chart's heading**: the title, the two axis titles with their units and the
   column heading, the same in both records of a case, at every stage.
5. **Each chart's lines**: a chart is a sequence of lines (a profile, an envelope, a
   limit), each with a line type and rows or none. Over all the stages of a case, the
   kinds of line r2x's record shows on a chart (line type, with rows or without, its
   place among the chart's lines) are set beside r2c's. A kind only r2x shows is data
   r2c's record does not carry on that case; a kind only r2c shows is the other way.
   Which stages show a kind is the calculation's, and is not compared.
6. **Each chart's numbers**: how many columns a row has and the decimals each is printed
   with, over all the stages of a case.
7. **Each chart's lines at stage 0**: the initial load is the one stage that is the same
   state in both records whatever the stages after it, so there the lines of each chart
   are compared one for one (how many, their line types, with rows or without).

Each of 1 to 7 is counted as "cases the same of cases compared", and the differences are
listed by kind with how many cases have them (--list names the cases). Development cases
only: it refuses a held-out archive. Standard library and r2c's record reader only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from r2c import record  # noqa: E402
from r2c import views as viewlib  # noqa: E402

# r2x's own machinery: which Response, which Wine, which r2x made the record
R2X_ONLY = {"r2x-version", "response-exe-sha256", "response-files-sha256",
            "response-verified", "wine-version", "template-sha256"}
NUMBER = re.compile(r"-?\d+(?:\.(\d+))?(?:[eE][-+]?\d+)?")
HEAD_LINES = 9          # "Data from Graph" down to the column heading


def chart(body: bytes):
    """(heading, kinds of line, forms of row) of one chart's export."""
    lines = body.decode("latin-1").split("\r\n")
    heading = tuple(ln.strip() for ln in lines[:HEAD_LINES])
    kinds, forms = [], set()
    place, cur, rows = 0, None, 0
    for ln in lines[HEAD_LINES:]:
        if ln.startswith("Line type"):
            if cur is not None:
                kinds.append((place, cur, rows > 0))
                place += 1
            cur, rows = ln.split(":")[1].strip(), 0
        elif ln == "New Line" or not ln.strip():
            continue
        else:
            rows += 1
            cells = [c.strip() for c in ln.split("\t") if c.strip()]
            forms.add(tuple(
                (lambda m: "text" if not m else f"{len(m.group(1) or '')} decimals")(
                    NUMBER.fullmatch(c)) for c in cells))
    if cur is not None:
        kinds.append((place, cur, rows > 0))
    return heading, kinds, forms


def of_record(rec) -> dict:
    """What a reader finds in a record, chart by chart, over all its stages."""
    out = {"control": [n for n in rec.sections if n.startswith("control/")],
           "heading": defaultdict(set), "kinds": defaultdict(set), "forms": defaultdict(set),
           "other": sorted(n for n in rec.sections if not n.startswith(("control/", "stage/"))),
           "stages_short": []}
    want = [c.key for c in viewlib.record_order(viewlib.parse_views(rec.header["views"]))]
    for n in out["control"]:
        h, k, f = chart(rec.sections[n])
        out["heading"][n].add(h)
        out["kinds"][n] |= {(p, t, r) for p, t, r in k}
        out["forms"][n] |= f
    for st in rec.stages():
        have = [n.split("/", 2)[2] for n in rec.sections if n.startswith(f"stage/{st}/")]
        if have != want:
            out["stages_short"].append(st)
        for key in have:
            h, k, f = chart(rec.sections[f"stage/{st}/{key}"])
            out["heading"][key].add(h)
            # a line with rows at some stage carries data; one without rows at every
            # stage does not. Keep the line's place and type with "ever has rows".
            out["kinds"][key] |= {(p, t, r) for p, t, r in k}
            out["forms"][key] |= f
    out["all_stages"] = rec.stages() == list(range(int(rec.header["stage-count"])))
    return out


def with_rows(kinds: set) -> set:
    return {(p, t) for p, t, r in kinds if r}


def compare(ref, sub) -> dict[str, list[str]]:
    """{part: [difference]} for one case; an empty list is 'the same'."""
    a, b = of_record(ref), of_record(sub)
    d: dict[str, list[str]] = {k: [] for k in
                               ("header", "control", "views", "heading", "lines", "numbers",
                                "first")}
    missing = [k for k in ref.header if k not in R2X_ONLY and k not in sub.header]
    if missing:
        d["header"].append(f"header keys of r2x's record not in r2c's: {', '.join(missing)}")
    if a["control"] != b["control"]:
        d["control"].append(f"control charts: r2x {a['control']}, r2c {b['control']}")
    if ref.header["views"] != sub.header["views"]:
        d["views"].append(f"views: r2x {ref.header['views']}, r2c {sub.header['views']}")
    if a["stages_short"]:
        d["views"].append("r2x's record lacks a chart of its views at some stage")
    if b["stages_short"]:
        d["views"].append("r2c's record lacks a chart of its views at some stage")
    if not b["all_stages"]:
        d["views"].append("r2c's record does not have every stage")
    for key in a["heading"]:
        name = key.split("/")[-1]
        if key not in b["heading"]:
            continue                      # counted under control or views
        if a["heading"][key] != b["heading"][key]:
            ha, hb = sorted(a["heading"][key] - b["heading"][key]), \
                sorted(b["heading"][key] - a["heading"][key])
            line = next((f"r2x {x!r}, r2c {y!r}" for x, y in zip((ha or [()])[0], (hb or [()])[0])
                         if x != y), "a heading only one of them shows")
            d["heading"].append(f"{name}: heading {line}")
        ka, kb = with_rows(a["kinds"][key]), with_rows(b["kinds"][key])
        for p, t in sorted(ka - kb):
            d["lines"].append(f"{name}: line {p + 1} (line type {t}) has rows in r2x's record "
                              "at some stage and in r2c's at none")
        for p, t in sorted(kb - ka):
            d["lines"].append(f"{name}: line {p + 1} (line type {t}) has rows in r2c's record "
                              "at some stage and in r2x's at none")
        fa, fb = a["forms"][key], b["forms"][key]
        for f in sorted(fa - fb):
            d["numbers"].append(f"{name}: rows of {' | '.join(f)} only in r2x's record")
        for f in sorted(fb - fa):
            d["numbers"].append(f"{name}: rows of {' | '.join(f)} only in r2c's record")
    for c in viewlib.record_order(viewlib.parse_views(ref.header["views"])):
        x, y = ref.sections.get(f"stage/0/{c.key}"), sub.sections.get(f"stage/0/{c.key}")
        if x is None or y is None:
            continue
        kx, ky = [k[1:] for k in chart(x)[1]], [k[1:] for k in chart(y)[1]]
        if kx != ky:
            def say(ks):
                return ", ".join(f"type {t}" + ("" if r else " (no rows)") for t, r in ks)
            d["first"].append(f"{c.key}: at stage 0 r2x's record has the lines {say(kx)}; "
                              f"r2c's {say(ky)}")
    return d, b["other"]


PARTS = {"header": "1. header keys of r2x's record present",
         "control": "2. control charts, the same sections in the same order",
         "views": "3. detail views, every chart of the views at every stage",
         "heading": "4. each chart's title, axes, units and column heading",
         "lines": "5. each chart's lines, over all stages",
         "numbers": "6. each chart's columns and decimals, over all stages",
         "first": "7. each chart's lines at stage 0, one for one"}


def catalogue() -> str:
    mine = json.loads((ROOT / "src" / "r2c" / "views.json").read_text())
    try:
        import r2x
        theirs = json.loads((Path(r2x.__file__).parent / "views.json").read_text())
    except Exception:  # noqa: BLE001 - r2x is not needed for the rest
        return "the catalogue of views was not set beside r2x's (r2x is not importable)"
    return ("the catalogue of views (views.json) is r2x's own, item for item" if mine == theirs
            else "THE CATALOGUE OF VIEWS DIFFERS FROM r2x's (views.json)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("archive")
    ap.add_argument("subs")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if any(w in str(Path(p).resolve()) for p in (a.archive, a.subs) for w in ("heldout", "finish")):
        raise SystemExit("development cases only")
    cases = sorted(p.name for p in (ROOT / "tests" / "oracle").glob("*.r2x.txt"))
    n = stages_x = stages_c = charts = 0
    same = {k: 0 for k in PARTS}
    by: dict[str, dict[str, list[str]]] = {k: {} for k in PARTS}
    others: dict[str, int] = defaultdict(int)
    absent = []
    for name in cases:
        rp, sp = Path(a.archive) / name, Path(a.subs) / name
        if not (rp.exists() and sp.exists()):
            absent.append(name[: -len(".r2x.txt")])
            continue
        ref, sub = record.read(rp), record.read(sp)
        n += 1
        stages_x += len(ref.stages())
        stages_c += len(sub.stages())
        charts += sum(1 for s in sub.sections if s.startswith(("stage/", "control/")))
        d, other = compare(ref, sub)
        for o in other:
            others[o] += 1
        for k in PARTS:
            same[k] += not d[k]
            for line in d[k]:
                by[k].setdefault(line, []).append(name[: -len(".r2x.txt")])
    out = [f"{n} development cases, each r2x's whole capture beside r2c's whole record: "
           f"{stages_x} stages of Response's and {stages_c} of r2c's, {charts} charts of "
           f"r2c's read; {catalogue()}.", ""]
    if absent:
        out += [f"Not compared, one of the two records missing: {len(absent)}"
                + (" (" + " ".join(absent) + ")" if a.list else ""), ""]
    for k, title in PARTS.items():
        out.append(f"- **{title}: {same[k]} of {n} cases the same**")
        for line, names in sorted(by[k].items(), key=lambda kv: (-len(kv[1]), kv[0])):
            out.append(f"  - {line}: {len(names)} cases"
                       + (" (" + " ".join(names) + ")" if a.list else ""))
    if others:
        out += ["", "Sections of r2c's record that r2x's has not: "
                + ", ".join(f"`{o}` ({c} cases)" for o, c in sorted(others.items())) + "."]
    text = "\n".join(out) + "\n"
    print(text, end="")
    if a.out:
        Path(a.out).write_text(
            "<!-- Generated by tools/carries.py --out. Do not edit: rerun it. -->\n\n"
            "# Does r2c's record carry what r2x's does?\n\n"
            "What `tools/carries.py` finds (its docstring says how each part is read). "
            "No value is compared here; `docs/verification-results.md` does that. "
            "`docs/output.md` says what each difference means for a reader.\n\n" + text,
            encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
