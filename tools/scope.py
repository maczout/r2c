#!/usr/bin/env python3
"""Which input features does each oracle case exercise?

    python tools/scope.py tests/oracle --inputs DIR [DIR ...] [--by-case]

Answers the question behind docs/scope.md's "implemented and compared (name the fixture)":
for every feature an input file or a solve option can carry, which fixtures have it. Each
fixture's header names its input (by name and SHA-256) and its solve options; the input is
found under --inputs as tools/verify.py finds it and read as XML (the section Response opens
at: the first <r3g_beam>). Nothing is solved.

A feature is a short label: an attribute with a non-default value ("concrete c_soft=0"), an
element present ("shrinktherm"), a property of the outline ("outline: step in width"), or a
solve option ("units us", "increment N-,M+,V0"). The default output lists each feature with
the cases that have it; --by-case lists each case with its features.

Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from r2c import inputs, record  # noqa: E402
import verify  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# Newbeam (File > New), as r2c's inputs.default_section has it and r2x's input.r2t writes it
NEWBEAM_FEATURES = [
    "concretes: 1", "concrete c_mod=2 (default)", "concrete c_soft=18 (default)",
    "concrete t_stiff=7 (default)", "concrete ft auto", "concrete e0 auto",
    "outline: explicit rows", "outline: rectangle", "shapesection RECT (with an outline)",
    "long: bars", "long: bars by title", "trans pattern=5 (T-headed single leg)",
    "trans: by title", "rebar types: 2",
    "prestress types: 1 (unused)", "units metric (file)",
]

PATTERN = {0: "none", 1: "single leg", 2: "open stirrup", 3: "closed stirrup", 4: "hoop",
           5: "T-headed single leg", 6: "interlocking hoops", 7: "horizontal tie"}


def sign(v: float) -> str:
    return "0" if v == 0 else ("+" if v > 0 else "-")


def option_features(h: dict) -> list[str]:
    out = [f"units {h['units']} (solve)"]
    fac = [float(x) for x in h["factors"].split(",")]
    out.append("factors none" if fac == [1.0, 1.0, 1.0] else "factors csa")
    ini = [float(x) for x in h["initial"].split(",")]
    inc = [float(x) for x in h["increment"].split(",")]
    out.append("initial " + ",".join(f"{n}{sign(v)}" for n, v in zip("NMV", ini)))
    out.append("increment " + ",".join(f"{n}{sign(v)}" for n, v in zip("NMV", inc)))
    md = h.get("more-detail", "0") or "0"
    out.append(f"more-detail {md}")
    if h["input-name"] == "File > New":
        out.append("no input (File > New)")
    return out


def file_features(data: bytes) -> list[str]:
    text = data.decode("utf-8", errors="replace")
    text = re.sub(r"<!DOCTYPE[^>]*>", "", text)
    root = ET.fromstring(inputs._dedupe(text).encode("utf-8"))
    beams = [root] if root.tag == "r3g_beam" else root.findall("r3g_beam")
    beam = beams[0]
    f: list[str] = []
    if len(beams) > 1:
        f.append("several sections in the file (catalogue)")
    f.append(f"units {beam.get('units', 'metric')} (file)")
    for key in ("smx", "smt", "axialloc"):
        if float(beam.get(key, "-1")) >= 0:
            f.append(f"general {key} given")
    cons = beam.findall("concrete")
    f.append(f"concretes: {len(cons)}")
    for c in cons:
        for key, default in (("c_mod", "2"), ("c_soft", "18"), ("t_stiff", "7")):
            v = c.get(key, default)
            f.append(f"concrete {key}={v}" + (" (default)" if v == default else ""))
        f.append("concrete ft given" if float(c.get("ft", "-1")) >= 0 else "concrete ft auto")
        f.append("concrete e0 given" if float(c.get("e0", "-1")) >= 0 else "concrete e0 auto")
        if float(c.get("tsfactor", "1")) != 1.0:
            f.append("concrete tsfactor given")
        if (c.text or "").strip():
            f.append("concrete segmental data")
    used = {el.get("type", "").lower() for el in beam.findall("longreinfx")} | \
           {el.get("type", "").lower() for el in beam.findall("transreinfz")}
    rebars = beam.findall("rebar")
    f.append(f"rebar types: {len(rebars)}")
    for r in rebars:
        if (r.text or "").strip():
            f.append("rebar segmental data" + ("" if r.get("name", "Steel 1").lower() in used
                                               else " (type unused)"))
    pres = beam.findall("prestress")
    pnames = {p.get("name", "Low Relax").lower() for p in pres}
    f.append(f"prestress types: {len(pres)}" + ("" if pnames & used else " (unused)"))
    for p in pres:
        if (p.text or "").strip():
            f.append("prestress segmental data")
        if p.get("name", "Low Relax").lower() in used and \
                (p.get("A"), p.get("B"), p.get("C")) != (None, None, None):
            f.append("prestress Ramberg-Osgood A, B, C given")
    solid = beam.find("sectionSOLID")
    shape = beam.find("shapesection")
    if solid is not None and (solid.text or "").strip():
        f.append("outline: explicit rows")
        rows, names, codes = [], set(), 0
        for line in solid.text.splitlines():
            t = inputs._TOKEN.findall(line)
            if not t:
                continue
            if t[0].upper() in ("UP", "DOWN"):
                codes += 1
                continue
            if len(t) > 1 and t[1].upper() in ("UP", "DOWN"):
                f.append("outline: width of UP or DOWN")
                continue
            rows.append((float(t[0]), float(t[1])))
            if len(t) > 2:
                names.add(t[2].strip('"').lower())
        if codes:
            f.append("outline: lone UP or DOWN line")
        widths = {w for _, w in rows}
        elevs = [e for e, _ in rows]
        if len(set(elevs)) < len(elevs):
            f.append("outline: step in width")
        if len(widths) == 1:
            f.append("outline: rectangle")
        elif any(a[0] != b[0] and a[1] != b[1] for a, b in zip(rows, rows[1:])):
            f.append("outline: tapering width")
        if min(elevs) < 0:
            f.append("outline: negative elevation")
        if len(names) > 1:
            f.append("outline: several concrete types")
        if shape is not None:
            f.append(f"shapesection {shape.get('name', '').upper()} (with an outline)")
    elif shape is not None:
        f.append(f"shapesection {shape.get('name', '').upper()} (no outline)")
    hollow = beam.find("sectionHOLLOW")
    if hollow is not None and (hollow.text or "").strip():
        f.append("sectionHOLLOW")
    for el in beam.findall("longreinfx"):
        strand = el.get("type", "").lower() in pnames
        f.append("long: tendons" if strand else "long: bars")
        f.append(("long: tendon " if strand else "long: bars ")
                 + ("by title" if el.get("bartitle") else "by area"))
        if float(el.get("dep", "0")) != 0:
            f.append("long: prestrain (dep)" + ("" if strand else " on bars"))
        if float(el.get("drape", "0")) != 0:
            f.append("long: drape")
        if int(float(el.get("pattern", "0"))) != 0:
            f.append(f"long pattern={el.get('pattern')}")
        if float(el.get("space", "0")) != 0:
            f.append("long: space given")
    if not beam.findall("transreinfz"):
        f.append("trans: none")
    for el in beam.findall("transreinfz"):
        p = int(float(el.get("pattern", "0")))
        f.append(f"trans pattern={p} ({PATTERN.get(p, '?')})")
        f.append("trans: by title" if el.get("bartitle") else "trans: by area")
        if float(el.get("dep", "0")) != 0:
            f.append("trans: prestrain (dep)")
        if el.get("type", "").lower() in pnames:
            f.append("trans: prestressing steel")
    if len(beam.findall("transreinfz")) > 1:
        f.append("trans: several")
    for tag in ("shrinktherm", "rebarthermx", "straindiscont"):
        el = beam.find(tag)
        if el is not None and (el.text or "").strip():
            vals = [float(x) for x in inputs._NUM.findall(el.text)]
            f.append(tag + ("" if any(vals[1::2]) or tag == "rebarthermx" else " (all zero)"))
    ld = beam.find("sectloading")
    if ld is not None and any(ld.get(k) for k in ("BN", "BM", "BV", "MN", "MM", "MV")):
        f.append("sectloading given")
    ao = beam.find("analysisoptions")
    if ao is not None:
        if any(float(ao.get(k, "1")) != 1.0 for k in ("phic", "phis", "phip")):
            f.append("analysisoptions: material factors in the file")
        if float(ao.get("longterm", "0")) != 0:
            f.append("analysisoptions: longterm")
        if ao.get("clamp", "0") != "0":
            f.append("analysisoptions: clamp")
    if beam.find("firedata") is not None:
        f.append("firedata")
    return f


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fixtures", help="folder of fixtures (tests/oracle)")
    ap.add_argument("--inputs", nargs="*", default=[], help="folders with the input files")
    ap.add_argument("--by-case", action="store_true", help="list each case with its features")
    a = ap.parse_args(argv)
    by_feature: dict[str, list[str]] = defaultdict(list)
    by_case: dict[str, list[str]] = {}
    missing = []
    for fx in sorted(Path(a.fixtures).glob("*.r2x.txt")):
        name = fx.name[: -len(".r2x.txt")]
        h = record.read(fx).header
        feats = option_features(h)
        if h["input-name"].lower() in verify.BUILT_IN:
            feats += NEWBEAM_FEATURES
        else:
            p = verify.find_input(h["input-name"], h.get("input-sha256"), a.inputs)
            if p is None:
                missing.append(name)
                continue
            feats += file_features(p.read_bytes())
        feats = sorted(set(feats))
        by_case[name] = feats
        for f in feats:
            by_feature[f].append(name)
    if a.by_case:
        for name, feats in by_case.items():
            print(f"{name}:\n  " + "\n  ".join(feats))
    else:
        for f in sorted(by_feature):
            cases = by_feature[f]
            print(f"{f}: {len(cases)}: " + ", ".join(cases))
    for name in missing:
        print(f"{name}: input not found under --inputs", file=sys.stderr)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
