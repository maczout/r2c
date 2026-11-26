#!/usr/bin/env python3
"""The results pages: a front page that answers "how accurate is r2c?", and a details page.

    python tools/dashboard.py [RESULTS] [--curves VERIFY_OUT] [--reference tests/oracle]
                              [--targets docs/measures.md] [--out index.html]

Writes two self-contained HTML files (no network): OUT, the front page, and details.html
beside it.

The front page (owner, 2026-11-24) is a snapshot of accuracy, in this order:

1. priority 1 on the held-out set for each area, against the solution threshold, with its
   trend across the recorded scorings (heldout/totals.json; totals only, nothing per case);
2. the latest held-out totals, priority by area;
3. the control curves of the development cases that are outside target on a check of the
   control curve (peak, rising branch, shape, ending), worst first: by the highest priority
   missed (docs/measures.md, "Checks by priority"), then by how many times over the target
   the largest miss is (a different shape counts as once over). These are development cases,
   and the page says so.

Everything else is on the details page: which sections and loadings the development set
covers, every case's peak, rising branch and ending, the detail views at the features of the
curve, where Response itself is unstable, every control curve, and the held-out totals of
every priority across the scorings.

RESULTS is a folder written by tools/verify.py (results.json and run.json) or the combined
JSON tools/report.py writes (default: docs/verification-results.json). r2c's curves come from
that JSON (report.py keeps them there) or, failing that, from r2c's records in a verify output
folder (NAME.r2x.txt): --curves names it, and defaults to RESULTS when RESULTS is a folder.
Response's curves come from the reference records (default: the oracle fixtures).

Every number on the pages is generated from a run or from the recorded totals; nothing is
typed in. The pages are output, not source: they are not committed. CI builds them from the
committed results after every push (tools/site.py, .github/workflows/pages.yml).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
import heldout  # noqa: E402
import report  # noqa: E402

from r2c import record  # noqa: E402

BUILT_IN = {"file > new", "input.r2t", "newbeam.r2t"}


# ---------------------------------------------------------------- reading


def load_results(path: Path) -> tuple[dict, dict]:
    """(run, results) from a verify output folder or a combined results JSON."""
    if path.is_dir():
        return (json.loads((path / "run.json").read_text()),
                json.loads((path / "results.json").read_text()))
    data = json.loads(path.read_text())
    return data["run"], data["results"]


def not_compared(path: Path) -> list[str]:
    """The bullets of the "Not compared" section of docs/verification.md, as plain text."""
    if not path.exists():
        return []
    m = re.search(r"^## Not compared\s*\n(.*?)(?=^## |\Z)", path.read_text(encoding="utf-8"),
                  re.S | re.M)
    if not m:
        return []
    items = re.split(r"^\* ", m.group(1), flags=re.M)
    return [" ".join(i.split()).replace("`", "") for i in items if i.strip()]


def curve(rec, key):
    """(x title, y title, [[x, y], ...]) of a control chart."""
    _t, xt, yt, lines = cmp.parse_chart(rec.control(key))
    pts = lines[0].tolist() if lines else []
    return xt or "", yt or "", [[round(x, 5), round(y, 4)] for x, y in pts]


# ---------------------------------------------------------------- describing a case


def nums(s: str) -> list[float]:
    return [float(x) for x in s.split(",")]


def section_name(ref: dict) -> str:
    src = ref["input-name"]
    if src.lower() in BUILT_IN:
        return "Newbeam"
    return Path(src).stem


def loading(ref: dict) -> str:
    """The loading path as a column label, from the signs of the initial and increment loads."""
    n0, m0, v0 = nums(ref["initial"])
    n, m, v = nums(ref["increment"])
    parts = []
    if n:
        parts.append("N comp." if n < 0 else "N tens.")
    if m:
        parts.append("M" if m > 0 else "−M")
    if v:
        parts.append("V")
    path = " + ".join(parts) if parts else "no load"
    pre = []
    if n0:
        pre.append("N₀")
    if m0:
        pre.append("M₀")
    if v0:
        pre.append("V₀")
    return (" + ".join(pre) + ", then " + path) if pre else path


def variants(ref: dict) -> list[str]:
    """What sets a case apart from the plain run of its section and loading."""
    out = []
    if ref["input-name"].lower() == "file > new":
        out.append("File > New")
    if ref["units"] != "si":
        out.append({"us": "US units", "kgcm": "kg-cm"}.get(ref["units"], ref["units"]))
    if nums(ref["factors"]) != [1.0, 1.0, 1.0]:
        out.append("CSA factors")
    md = int(ref.get("more-detail") or 0)
    if md:
        out.append(f"More Detail ×{md}")
    force, length = UNITS.get(ref["units"], ("", ""))
    n0 = nums(ref["initial"])[0]
    if n0:
        out.append(f"N₀ = {n0:g} {force}".rstrip())
    n, m, v = nums(ref["increment"])
    if v and m:
        out.append(f"M/V = {abs(m / v):g} {length}".rstrip())
    if n and m:
        out.append(f"N/M = {n / m:g}" + (f" /{length}" if length else ""))
    return out


# force and length of each unit system, for labels (Response's SI: kN and kN·m; US: kip and
# kip·ft). kg-cm is left without units: not checked.
UNITS = {"si": ("kN", "m"), "us": ("kip", "ft")}


def label(ref: dict) -> str:
    """A case in engineering terms, with units: section, loading path, what sets it apart."""
    return ", ".join([section_name(ref), loading(ref)] + variants(ref))


# ---------------------------------------------------------------- assembling


def stale(run: dict) -> str:
    """Why the results may not describe the kernel at HEAD; empty if they do or git can't tell."""
    commit = run.get("commit", "")
    if run.get("dirty"):
        return "the run was made with uncommitted changes"
    try:
        p = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-only", commit, "HEAD", "--",
                            "src/r2c"], capture_output=True, text=True)
    except OSError:
        return ""
    if p.returncode != 0 or not p.stdout.strip():
        return ""
    return "the kernel has changed since the run (" + ", ".join(p.stdout.split()) + ")"


def heldout_runs() -> list[dict]:
    """The recorded totals of the held-out set (heldout/totals.json): totals only, by area
    and priority, every scoring. Nothing per case exists in the repository."""
    p = ROOT / "heldout" / "totals.json"
    return json.loads(p.read_text())["runs"] if p.exists() else []


CURVE_CHECKS = ("peak", "curve", "shape", "post_peak")


def curve_misses(checks: dict, g: str) -> list[dict]:
    """The checks on the control curve that a case is outside target on: each with the
    brief's priority it is counted in (tools/heldout.py, PRIORITY), its value, and how many
    times over the target it is (a different shape: once)."""
    pr = {k: int(p) for p, ks in heldout.PRIORITY[g].items() for k in ks}
    out = []
    for k in CURVE_CHECKS:
        if k not in checks or checks[k][2] is not False:
            continue
        v, lim, _ok = checks[k]
        if k == "shape":
            out.append({"check": k, "priority": pr[k], "value": None, "over": 1.0})
        else:
            out.append({"check": k, "priority": pr[k], "value": round(v, 3), "limit": lim,
                        "over": round(abs(v) / lim, 3) if lim else None})
    return out


def build(run: dict, results: dict, acc: dict, curves_dir: Path | None, ref_dir: Path,
          gaps: list[str]) -> dict:
    cases = []
    for name in sorted(results):
        r = results[name]
        if "ref" not in r:
            cases.append({"name": name, "problem": r.get("skipped") or r.get("failed") or "?"})
            continue
        ref = r["ref"]
        c = r["control"][-1] if r.get("control") else None
        checks = report.assess(r, acc)
        case = {
            "name": name,
            "group": report.group(ref),
            "section": section_name(ref),
            "loading": loading(ref),
            "variants": variants(ref),
            "label": label(ref),
            "checks": {k: v[2] for k, v in checks.items()},
            "input": ref["input-name"],
            "initial": ref["initial"], "increment": ref["increment"],
            "stages": [int(ref["stage-count"]), int(r["sub"]["stage-count"])],
            "seconds": r.get("seconds"),
            "chart": c["chart"] if c else None,
            "peak": [c["ref_peak_load"], c["sub_peak_load"]] if c else None,
            "peak_pct": c["peak_diff_pct"] if c else None,
            "curve_pct": c.get("rising_pct", c.get("curve_max_diff_pct")) if c else None,
            "post_pct": c.get("post_peak_pct") if c else None,
            "shape": ([c["shape_ref"], c["shape_sub"]] if c and "shape_ref" in c else None),
            "verdict": report.verdict(checks),
            "limits": {k: v[1] for k, v in checks.items()},
            "curve_out": curve_misses(checks, report.group(ref)),
            "views": [],
            "run": r.get("run", ""),
        }
        va = r.get("views_at")
        if va:
            rx, sx = va["ref_x"], va["sub_x"]
            case["views_at"] = va
            # how far r2c's nearest stage is from Response's peak, in control value
            case["views_gap_pct"] = abs(sx - rx) / abs(rx) * 100 if rx else 0.0
        # the views that are assessed, and (D40) the last stage of a shear case on its own
        feat = {s["ref_stage"]: s["feature"] for s in r.get("views_stages", [])}
        # D54: the checks where Response itself is unstable, reported and not assessed
        case["unstable"] = [
            {"view": u["view"], "stage": u["ref_stage"], "feature": u["feature"],
             "tier": report.TIERS[u["tier"]], "dep": round(u["departure_pct"], 3),
             "apart": round(u["apart_pct"], 3),
             "pct": None if u["pct"] is None else round(u["pct"], 3),
             "outside": u["plain"] == "outside"}
            for u in report.unstable_checks(r, acc)]
        for key, endings in (("views", False), ("views_end", True)):
            for v in report.view_rows(r, endings, report.views_limit(acc)):
                if v.get("missing"):
                    case.setdefault(key, []).append({"view": v["view"], "missing": True})
                else:
                    case.setdefault(key, []).append(
                        {"view": v["view"], "pct": round(v["max_diff_pct"], 3),
                         "stage": v.get("ref_stage"),
                         "feature": feat.get(v.get("ref_stage"), ""),
                         "ref_max": v["ref_max"], "diff": v["max_diff"]})
        # curves
        # a parked case's fixture is under the folder (tests/oracle/parked)
        refp = ref_dir / f"{name}.r2x.txt"
        if not refp.exists():
            refp = ref_dir / "parked" / refp.name
        if c and refp.exists():
            xt, yt, rc = curve(record.read(refp), c["chart"])
            case["curve"] = {"x": xt, "y": yt, "ref": rc,
                             "ref_peak_stage": int(ref.get("peak-stage") or 0)}
            subp = curves_dir / f"{name}.r2x.txt" if curves_dir else None
            if r.get("sub_curve"):
                case["curve"]["sub"] = r["sub_curve"]
            elif subp and subp.exists():
                sub = record.read(subp)
                case["curve"]["sub"] = curve(sub, c["chart"])[2]
                case["curve"]["sub_peak_stage"] = int(sub.header.get("peak-stage") or 0)
                # was the record made at the run the metrics come from?
                other = curves_dir / "results.json"
                if other.exists():
                    o = json.loads(other.read_text()).get(name, {})
                    oc = (o.get("control") or [{}])[-1]
                    same = (abs(oc.get("peak_diff_pct", 1e9) - case["peak_pct"]) < 1e-6
                            and abs((oc.get("rising_pct", oc.get("curve_max_diff_pct")) or 0)
                                    - (case["curve_pct"] or 0)) < 1e-6)
                    if o.get("run") and case["run"] and o["run"] != case["run"] and not same:
                        case["curve"]["other_run"] = o["run"]
        cases.append(case)
    ran = {n: r for n, r in results.items() if "control" in r}
    return {"run": run, "cases": cases, "gaps": gaps, "stale": stale(run),
            "acceptance": {g: t for g, t in acc.items() if t},
            "views_pct": report.views_limit(acc),
            "heldout": heldout_runs(), "threshold": heldout.THRESHOLD, "thresholds": heldout.THRESHOLDS,
            "repeat": (heldout.read_repeat() or {}).get("totals", {}),
            "repeat_by": heldout.REPEAT_BY, "margin": heldout.MARGIN,
            "tiers": [dict(n, tier=report.TIERS[t])
                      for t, n in report.tier_counts(ran, acc).items() if n["checks"]]}


# ---------------------------------------------------------------- page

PAGE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>r2c against Response-2000</title>
<style>
.viz-root{color-scheme:light;
 --surface:#fcfcfb;--surface-2:#f2f1ee;--border:#dddcd6;--grid:#e8e7e2;
 --ink:#0b0b0b;--ink-2:#52514e;--ink-3:#8a8984;
 --ref:#52514e;--sub:#2a78d6;--low:#2a78d6;--high:#eb6834;
 --s1:#cde2fb;--s2:#9ec5f4;--s3:#6da7ec;--s4:#3987e5;--s5:#256abf;--s6:#184f95;--s7:#0d366b;
 --tol:#e34948;}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;
 --surface:#1a1a19;--surface-2:#242423;--border:#3a3a38;--grid:#2e2e2c;
 --ink:#f0efec;--ink-2:#c3c2b7;--ink-3:#8a8984;
 --ref:#c3c2b7;--sub:#3987e5;--low:#3987e5;--high:#d95926;
 --s1:#104281;--s2:#184f95;--s3:#1c5cab;--s4:#2a78d6;--s5:#5598e7;--s6:#86b6ef;--s7:#cde2fb;
 --tol:#e66767;}}
*{box-sizing:border-box}
body{margin:0;background:var(--surface)}
.viz-root{font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);
 background:var(--surface);max-width:1100px;margin:0 auto;padding:16px}
h1{font-size:20px;margin:0 0 4px}
h2{font-size:16px;margin:28px 0 4px}
.sub{color:var(--ink-2);margin:0 0 12px;font-size:13px}
.note{color:var(--ink-2);font-size:12.5px;margin:6px 0}
.warn{border-left:3px solid var(--high);padding:4px 10px;background:var(--surface-2);margin:10px 0;font-size:13px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}
.tile{background:var(--surface-2);border-radius:8px;padding:10px 12px}
.tile .k{font-size:12px;color:var(--ink-2)}
.tile .v{font-size:24px;font-weight:600;font-variant-numeric:tabular-nums}
.tile .d{font-size:12px;color:var(--ink-2)}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;font-variant-numeric:tabular-nums}
th,td{padding:3px 6px;text-align:left;vertical-align:middle;white-space:nowrap}
th{font-weight:600;font-size:12px;color:var(--ink-2)}
td.num{text-align:right}
tr.grp td{font-weight:600;padding-top:12px;color:var(--ink-2);font-size:12px}
.sticky{position:sticky;left:0;background:var(--surface);z-index:1}
.cov td,.cov th{border:1px solid var(--grid);vertical-align:top;white-space:normal}
.cov th{background:var(--surface-2)}
.chip{display:inline-block;background:var(--surface-2);border:1px solid var(--border);border-radius:10px;
 padding:0 7px;margin:2px;font-size:11.5px;white-space:nowrap;cursor:default}
.chip.empty{color:var(--ink-3)}
svg text{fill:var(--ink-2);font-size:10.5px}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:var(--ink-2);margin:6px 0}
.sw{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-2px;margin-right:4px}
.ln{display:inline-block;width:16px;height:0;border-top:2px solid;vertical-align:3px;margin-right:4px}
.multi{display:grid;grid-template-columns:repeat(auto-fill,minmax(165px,1fr));gap:12px}
.panel{border:1px solid var(--grid);border-radius:8px;padding:6px 8px 2px}
.panel h3{font-size:12.5px;margin:0;font-weight:600}
.panel .m{font-size:11.5px;color:var(--ink-2)}
#tip{position:fixed;pointer-events:none;background:var(--ink);color:var(--surface);font-size:12px;
 padding:6px 8px;border-radius:6px;max-width:300px;display:none;z-index:9;white-space:pre-line}
ul.gaps{margin:4px 0;padding-left:18px;color:var(--ink-2);font-size:13px}
ul.gaps li{margin:3px 0}
details summary{cursor:pointer;color:var(--ink-2);font-size:13px}
a{color:var(--sub)}
.heroes{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px;margin:12px 0}
.hero{background:var(--surface-2);border-radius:10px;padding:14px 16px 8px}
.hero .k{font-size:13px;color:var(--ink-2)}
.hero .v{font-size:44px;font-weight:650;line-height:1.1;font-variant-numeric:tabular-nums}
.hero .v small{font-size:15px;font-weight:400;color:var(--ink-2);margin-left:8px}
.hero .st{font-size:13px;margin:2px 0 6px}
.pa td,.pa th{padding:6px 14px 6px 0;white-space:normal}
.pa td.c{white-space:nowrap}
.pa .dl{color:var(--ink-2);font-size:12px;margin-left:6px}
.big{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.out{font-size:11.5px}
</style></head>
<body><div class="viz-root" id="root"></div><div id="tip"></div>
<script>
const D = __DATA__, KIND = "__KIND__";
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const f = (x, d=2) => x == null ? "–" : (+x).toFixed(d);
const sg = (x, d=2) => x == null ? "–" : (x > 0 ? "+" : x < 0 ? "−" : "±") + Math.abs(x).toFixed(d);
const cases = D.cases.filter(c => !c.problem), probs = D.cases.filter(c => c.problem);
const G = {flexure: "Without shear", shear: "With shear"};
let H = "";

// ---------- header
const run = D.run, when = (run.started||"").replace("T"," ").slice(0,16);
H += `<h1>${KIND === "front" ? "r2c against Response-2000: how accurate is it?" : "r2c against Response-2000: the development results in detail"}</h1>
<p class="sub">${KIND === "front" ? "" : `<a href="./">← The summary page</a> · `}r2c ${esc(run.r2c_version||"")} at <code>${esc((run.commit||"").slice(0,12))}</code>${run.dirty?" (uncommitted changes)":""}
 · run ${esc(when)} UTC on ${esc(run.host||"")} · reference: Response-2000 1.9.7 via r2x (the oracle fixtures)</p>`;
H += `<p class="note">r2c is an unofficial, work-in-progress clone of Response-2000's sectional analysis, not affiliated with Response-2000's authors. This page compares the two; it does not check designs.</p>`;
if (D.stale) H += `<div class="warn">These results may be stale: ${esc(D.stale)}.</div>`;
const accSet = Object.keys(D.acceptance).length;
if (KIND === "details") H += accSet ? `<p class="note">Tolerances from docs/measures.md are drawn in red where set.</p>`
 : `<div class="warn">No tolerances are set in docs/measures.md yet, so nothing here is assessed: the page shows differences, not verdicts.</div>`;
if (probs.length) H += `<div class="warn">${probs.length} development case(s) not run: ${probs.map(c=>esc(c.name)+" ("+esc(c.problem)+")").join("; ")}</div>`;

const by = g => cases.filter(c => c.group === g);
function sameShape(c) { return c.shape && c.shape[0].join() === c.shape[1].join(); }
function plot(c) {
 const k = c.curve, w = 250, h = 150, m = {l:40, r:6, t:6, b:22};
 const all = k.ref.concat(k.sub || []);
 const xs = all.map(p=>p[0]), ys = all.map(p=>p[1]);
 let x0 = Math.min(0,...xs), x1 = Math.max(0,...xs), y0 = Math.min(0,...ys), y1 = Math.max(0,...ys);
 if (x1 === x0) x1 = x0 + 1; if (y1 === y0) y1 = y0 + 1;
 const X = x => m.l + (x - x0)/(x1 - x0)*(w - m.l - m.r), Y = y => h - m.b - (y - y0)/(y1 - y0)*(h - m.t - m.b);
 const path = pts => pts.map((p,i)=>(i?"L":"M")+X(p[0]).toFixed(1)+","+Y(p[1]).toFixed(1)).join("");
 let s = `<svg viewBox="0 0 ${w} ${h}" width="100%" role="img" aria-label="${esc(k.y)} against ${esc(k.x)}">`;
 s += `<line x1="${m.l}" x2="${w-m.r}" y1="${Y(0)}" y2="${Y(0)}" stroke="var(--grid)"/><line x1="${X(0)}" x2="${X(0)}" y1="${m.t}" y2="${h-m.b}" stroke="var(--grid)"/>`;
 s += `<text x="${m.l-3}" y="${Y(y1)+8}" text-anchor="end">${f(y1,0)}</text><text x="${m.l-3}" y="${Y(y0)}" text-anchor="end">${f(y0,0)}</text>`;
 s += `<text x="${w-m.r}" y="${h-8}" text-anchor="end">${f(x1,1)}</text><text x="${m.l}" y="${h-8}">${f(x0,1)}</text>`;
 s += `<text x="${(m.l+w)/2}" y="${h-1}" text-anchor="middle">${esc(k.x)}</text>`;
 s += `<path d="${path(k.ref)}" fill="none" stroke="var(--ref)" stroke-width="2" stroke-linejoin="round"/>`;
 if (k.sub) s += `<path d="${path(k.sub)}" fill="none" stroke="var(--sub)" stroke-width="2" stroke-linejoin="round" opacity="0.9"/>`;
 const pk = (pts, col, who) => { if (!pts.length) return ""; let i = 0; pts.forEach((p,j)=>{ if (Math.abs(p[1]) > Math.abs(pts[i][1])) i = j; });
  return `<circle cx="${X(pts[i][0])}" cy="${Y(pts[i][1])}" r="4" fill="${col}" stroke="var(--surface)" stroke-width="2" data-tip="${esc(who)}: peak ${f(pts[i][1],1)} at ${f(pts[i][0],3)}"/>`; };
 s += pk(k.ref, "var(--ref)", "Response");
 if (k.sub) s += pk(k.sub, "var(--sub)", "r2c");
 return s + `</svg>`;
}

// ---------- the front page: how accurate is r2c?
const AREAS = {"moment-axial": ["Moment and axial", "cases without shear"], "shear": ["Shear", "cases with shear"]};
const PN = {1: "1: peak, rising branch and shape of the control curves; stress-state views under moment and axial load", 2: "2: endings without shear; shear-related views", 3: "3: cracking-related views", 4: "4: endings with shear"};
const pc = v => 100 * v[0] / v[1];
const need = (t, of) => Math.ceil(D.threshold[t] / 100 * of - 1e-9);
function trend(t) {
 const runs = D.heldout.filter(r => r.totals[t][1]), th = D.threshold[t];
 const w = 340, h = 132, m = {l: 30, r: 44, t: 16, b: 22};
 const X = i => runs.length === 1 ? m.l + 12 : m.l + 12 + i / (runs.length - 1) * (w - m.l - m.r - 24);
 const Y = p => h - m.b - p / 100 * (h - m.t - m.b);
 let s = `<svg viewBox="0 0 ${w} ${h}" width="100%" style="max-width:${w * 1.5}px" role="img" aria-label="Priority 1, ${AREAS[t][0]}: per cent of held-out cases inside target at each scoring, against the threshold of ${th} %">`;
 for (const g of [0, 50, 100]) s += `<line x1="${m.l}" x2="${w - m.r}" y1="${Y(g)}" y2="${Y(g)}" stroke="var(--grid)"/><text x="${m.l - 4}" y="${Y(g) + 3.5}" text-anchor="end">${g}</text>`;
 s += `<line x1="${m.l}" x2="${w - m.r}" y1="${Y(th)}" y2="${Y(th)}" stroke="var(--ink-2)" stroke-width="1.5" stroke-dasharray="5 3"/><text x="${w - m.r + 4}" y="${Y(th) + 3.5}">${th} %</text>`;
 const pts = runs.map((r, i) => [X(i), Y(pc(r.totals[t][1])), r]);
 if (pts.length > 1) s += `<path d="${pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + "," + p[1].toFixed(1)).join("")}" fill="none" stroke="var(--sub)" stroke-width="2" stroke-linejoin="round"/>`;
 const lab = new Set(runs.length <= 4 ? runs.map((_, i) => i) : [0, runs.length - 1]);
 pts.forEach(([x, y, r], i) => { const v = r.totals[t][1];
  s += `<circle cx="${x}" cy="${y}" r="4" fill="var(--sub)" stroke="var(--surface-2)" stroke-width="2"/>`;
  if (lab.has(i)) s += `<text x="${x}" y="${h - 6}" text-anchor="${i === 0 ? "start" : i === runs.length - 1 && runs.length > 1 ? "end" : "middle"}">${esc(r.label)}</text>`;
  s += `<circle cx="${x}" cy="${y}" r="13" fill="transparent" data-tip="${esc(`${r.label} (${r.date})\n${v[0]} of ${v[1]} cases inside target: ${f(pc(v), 0)} %\nthreshold ${th} %: ${need(t, v[1])} of ${v[1]}`)}"/>`; });
 return s + `</svg>`;
}
function front() {
 const runs = D.heldout || [];
 if (!runs.length) { H += `<div class="warn">No held-out totals are recorded yet.</div>`; }
 else {
  const L = runs[runs.length - 1], P = runs.length > 1 ? runs[runs.length - 2] : null;
  H += `<p class="sub">Judged on the held-out set: ${Object.values(L.cases).reduce((a, b) => a + b, 0)} sections and loadings the developer has not tuned against, frozen, compared with Response-2000 within ±5 %. Below: the cases inside target on every priority 1 check (peak, rising branch and shape of the control curve; the stress-state views without shear), against the threshold, at each scoring. The threshold (owner, 2026-11-25) is Response-2000's own score against itself on the same inputs, less ${D.margin} points: Response with every concrete strength raised by ${D.repeat_by} %, compared with Response as it is by the same measure; without shear the owner keeps 99 % (2026-11-26). Latest: ${esc(L.label)}, ${esc(L.date)}.</p><div class="heroes">`;
  for (const t in AREAS) { const v = L.totals[t][1], n = need(t, v[1]), met = pc(v) >= D.threshold[t];
   H += `<div class="hero"><div class="k"><b>${AREAS[t][0]}</b> · ${AREAS[t][1]} · priority 1, held-out</div>
<div class="v">${f(pc(v), 0)} %<small>${v[0]} of ${v[1]} cases inside target</small></div>
<div class="st">${met ? `✓ Threshold reached` : `✗ Below the threshold`}: ${D.threshold[t]} %, which is ${n} of ${v[1]}${met ? "" : `; ${n - v[0]} more case${n - v[0] === 1 ? "" : "s"} needed`}</div>
${trend(t)}</div>`; }
  H += `</div><div class="legend"><span><span class="ln" style="border-color:var(--sub)"></span>% of held-out cases inside target, by scoring</span><span><span class="ln" style="border-color:var(--ink-2);border-top-style:dashed"></span>threshold</span></div>`;
  // ----- priority by area
  H += `<h2>Held-out set: every priority, by area</h2>
<p class="sub">Cases inside target on every check of the priority, at the latest scoring${P ? `; the change is since ${esc(P.label)}` : ""}. Beside each: Response-2000 against itself on the same inputs (every concrete strength raised by ${D.repeat_by} %), and the threshold for priorities 1 to 3, which is that score less ${D.margin} points; priority 4 is reported only.</p>
<div class="scroll"><table class="pa"><tr><th>Priority</th>${Object.keys(AREAS).map(t => `<th>${AREAS[t][0]} (${L.cases[t]} cases)</th>`).join("")}</tr>`;
  const meter = (v, th) => { const w = 90; let s = `<svg width="${w}" height="12" style="vertical-align:-1px;margin-right:8px" aria-hidden="true"><rect x="0" y="3" width="${w}" height="6" rx="3" fill="var(--grid)"/><rect x="0" y="3" width="${Math.max(2, pc(v) / 100 * w)}" height="6" rx="3" fill="var(--s4)"/>`;
   if (th != null) s += `<line x1="${th / 100 * w - 0.75}" x2="${th / 100 * w - 0.75}" y1="0" y2="12" stroke="var(--ink)" stroke-width="1.5"/>`;
   return s + `</svg>`; };
  const own = (t, p, v) => { const r = (D.repeat[t] || {})[p], th = (D.thresholds[t] || {})[p];
   if (!r || !r[1]) return "";
   return `<div class="dl" style="display:block;white-space:normal;margin:2px 0 0 98px">Response against itself: <span style="white-space:nowrap">${r[0]} of ${r[1]} · ${f(pc(r), 0)} %</span><br>${th == null ? "no threshold: reported only" : `threshold ${f(th, 1)} %: ${pc(v) >= th ? "✓ reached" : "✗ not reached"}`}</div>`; };
  for (const p of [1, 2, 3, 4]) {
   H += `<tr><td style="min-width:16em">${PN[p]}</td>`;
   for (const t in AREAS) { const v = L.totals[t][p], q = P && P.totals[t][p];
    if (!v || !v[1]) { H += `<td class="c" style="color:var(--ink-3)">no such check</td>`; continue; }
    const d = q ? v[0] - q[0] : null;
    H += `<td class="c">${meter(v, (D.thresholds[t] || {})[p])}${v[0]} of ${v[1]} · ${f(pc(v), 0)} %${d == null ? "" : `<span class="dl">${d > 0 ? "▲ " + d : d < 0 ? "▼ " + (-d) : "no change"}</span>`}${own(t, p, v)}</td>`; }
   H += `</tr>`; }
  H += `</table></div><p class="note">${Object.keys(AREAS).map(t => `${AREAS[t][0]}: ${L.unsolved[t]} of ${L.cases[t]} not solved by r2c and counted outside`).join(" · ")}. The mark on a bar is the threshold of that priority. Held-out results are kept in totals only; no held-out case is shown anywhere.</p>`;
 }
 // ----- development cases outside target on the control curve
 const out = cases.filter(c => (c.curve_out || []).length && c.curve);
 const pr = c => Math.min(...c.curve_out.map(o => o.priority)), ov = c => Math.max(...c.curve_out.map(o => o.over ?? 1e9));
 out.sort((a, b) => pr(a) - pr(b) || ov(b) - ov(a) || a.name.localeCompare(b.name));
 const CK = {peak: o => `peak ${sg(o.value, 1)} %`, curve: o => `rising branch ${f(o.value, 1)} %`, post_peak: o => `ending ${f(o.value, 1)} %`, shape: () => `shape differs`};
 H += `<h2>Control curves outside target, worst first</h2>
<p class="sub"><b>These are development cases, which the developer works on, not held-out cases.</b> ${out.length} of the ${cases.length} development cases are outside target on a check of the control curve; ordered by the highest priority missed, then by the size of the miss. Dots: each one's peak.</p>
<div class="legend"><span><span class="ln" style="border-color:var(--ref)"></span>Response-2000</span><span><span class="ln" style="border-color:var(--sub)"></span>r2c</span></div>`;
 if (!out.length) H += `<p class="note">None: every development case is inside target on its control curve.</p>`;
 let cur = 0;
 for (const c of out) {
  if (pr(c) !== cur) { H += `${cur ? "</div>" : ""}<h3 style="font-size:13px;margin:14px 0 6px;color:var(--ink-2)">Highest priority missed: ${pr(c)} · ${out.filter(o => pr(o) === pr(c)).length} case(s)</h3><div class="big">`; cur = pr(c); }
  const k = c.curve;
  H += `<div class="panel"><h3>${esc(c.label)}</h3><div class="m">${esc(c.name)} · ${esc(k.y)}</div><div class="out">Outside: ${c.curve_out.map(o => `${CK[o.check](o)} (priority ${o.priority})`).join(" · ")}${c.shape && !sameShape(c) && c.curve_out.some(o => o.check === "shape") ? `<div class="m">Response: ${esc(c.shape[0].join(", "))}<br>r2c: ${esc(c.shape[1].join(", "))}</div>` : ""}</div>${plot(c)}</div>`;
 }
 if (cur) H += `</div>`;
 H += `<h2>Everything else</h2><p class="sub"><a href="details.html"><b>The development results in detail</b></a>: what the development set covers, every case's peak, rising branch and ending, the detail views, where Response itself is unstable, every control curve, and the held-out totals of every priority at every scoring.</p>
<p class="note">Generated by tools/dashboard.py from the recorded held-out totals and the development run named at the top.</p>`;
}
function details() {
// ---------- tiles
const worst = (a, k) => a.reduce((m, c) => c[k] != null && Math.abs(c[k]) > Math.abs(m[k] ?? 0) ? c : m, {});
const range = a => { const p = a.map(c=>c.peak_pct).filter(x=>x!=null); return [Math.min(...p), Math.max(...p)]; };
const sections = [...new Set(cases.map(c=>c.section))];
H += `<div class="tiles">
<div class="tile"><div class="k">Cases compared</div><div class="v">${cases.length}</div><div class="d">${by("flexure").length} without shear · ${by("shear").length} with</div></div>
<div class="tile"><div class="k">Sections</div><div class="v">${sections.length}</div><div class="d">${cases.filter(c=>c.section==="Newbeam").length} of the cases on the Newbeam</div></div>`;
for (const g of ["flexure","shear"]) { const a = by(g); if (!a.length) continue; const [lo, hi] = range(a);
 H += `<div class="tile"><div class="k">Peak, r2c vs Response · ${G[g].toLowerCase()}</div><div class="v">${sg(lo,1)} to ${sg(hi,1)} %</div><div class="d">lowest / highest across ${a.length} cases</div></div>`; }
H += `</div>`;

// ---------- the held-out totals
if ((D.heldout || []).length) {
 const runs = D.heldout, areas = {"moment-axial": "Moment and axial", "shear": "Shear"};
 const pn = {1: "1: peak, rising branch, shape; stress-state views", 2: "2: endings without shear; shear-related views", 3: "3: cracking-related views", 4: "4: endings with shear"};
 const cellT = v => v ? (v[1] ? `${v[0]} of ${v[1]} (${Math.round(100*v[0]/v[1])} %)` : "none") : "";
 H += `<h2>Held-out totals, every priority, every scoring</h2>
<p class="sub">What r2c is judged on: cases the developer has not tuned against, frozen, scored in totals only. Cases inside target on every check of the priority; one column per recorded scoring. Nothing per case is published. Everything else on this page is the development set.</p>
<div class="scroll"><table><tr><th>Area</th><th>Priority</th>${runs.map(r => `<th>${esc(r.label)} (${esc(r.date)})</th>`).join("")}</tr>`;
 for (const t in areas) for (const p of [1,2,3,4]) { if (!runs.some(r => r.totals[t][p])) continue;
  H += `<tr><td>${areas[t]}</td><td>${pn[p]}</td>${runs.map(r => `<td class="num">${cellT(r.totals[t][p])}</td>`).join("")}</tr>`; }
 const L = runs[runs.length-1];
 H += `</table></div><p class="note">${Object.keys(areas).map(t => `${areas[t]}: ${L.cases[t]} cases, ${L.unsolved[t]} not solved by r2c and counted outside`).join(" · ")}.</p>`;
}

// ---------- coverage
H += `<h2>What is tested</h2><p class="sub">Each chip is a case: section down, loading path across. Chip text is what sets it apart. Hover or tap for details.</p>`;
const cols = [...new Set(cases.map(c => c.group + "|" + c.loading))].sort((a,b) => (a.startsWith("shear") - b.startsWith("shear")) || a.localeCompare(b));
const nf = cols.filter(k => k.startsWith("flexure")).length, ns = cols.length - nf;
H += `<div class="scroll"><table class="cov"><tr><th class="sticky"></th>${nf?`<th colspan="${nf}">Without shear</th>`:""}${ns?`<th colspan="${ns}">With shear</th>`:""}</tr>
<tr><th class="sticky">Section</th>${cols.map(k=>`<th>${esc(k.split("|")[1])}</th>`).join("")}</tr>`;
for (const s of sections) {
 H += `<tr><th class="sticky">${esc(s)}</th>`;
 for (const k of cols) {
  const here = cases.filter(c => c.section === s && c.group + "|" + c.loading === k);
  H += `<td>${here.map(c => `<span class="chip" data-tip="${esc(tipCase(c))}">${esc(c.variants.join(", ") || "base")}</span>`).join("")}</td>`;
 }
 H += `</tr>`;
}
H += `</table></div>`;
if (D.gaps.length) H += `<details open><summary>Not in the test set (from docs/verification.md)</summary><ul class="gaps">${D.gaps.map(g=>`<li>${esc(g)}</li>`).join("")}</ul></details>`;

function tipCase(c) {
 return `${c.label}\n${c.name}\ninput ${c.input}\ninitial ${c.initial}; increment ${c.increment}\npeak ${sg(c.peak_pct)} %, rising ${f(c.curve_pct)} %, post-peak ${f(c.post_pct)} %${c.shape ? "\nshape Response: " + c.shape[0].join(", ") + "\nshape r2c: " + c.shape[1].join(", ") : ""}\nstages Response ${c.stages[0]} / r2c ${c.stages[1]}`;
}

// ---------- scorecard
const symlog = x => Math.sign(x) * Math.log10(1 + Math.abs(x) / 0.1);
const W = 170, PM = symlog(30);
const px = x => W/2 + symlog(Math.max(-30, Math.min(30, x))) / PM * (W/2 - 4);
const CW = 130, cl = x => 4 + (Math.log10(Math.max(0.01, Math.min(100, x))) + 2) / 4 * (CW - 8);
function peakBar(c) {
 const x = c.peak_pct, x0 = px(0), x1 = px(x), col = x > 0 ? "var(--high)" : "var(--low)";
 const lim = c.limits.peak;
 let s = `<svg width="${W}" height="16" role="img" aria-label="peak ${sg(x)} %">`;
 for (const t of [-10,-1,-0.1,0.1,1,10]) s += `<line x1="${px(t)}" x2="${px(t)}" y1="2" y2="14" stroke="var(--grid)"/>`;
 s += `<line x1="${x0}" x2="${x0}" y1="0" y2="16" stroke="var(--ink-3)"/>`;
 if (Math.abs(x) > 1e-9) s += `<rect x="${Math.min(x0,x1)}" y="4" width="${Math.max(2,Math.abs(x1-x0))}" height="8" rx="2" fill="${col}"/>`;
 if (lim != null) for (const t of [-lim, lim]) s += `<line x1="${px(t)}" x2="${px(t)}" y1="0" y2="16" stroke="var(--tol)" stroke-width="1.5"/>`;
 return s + `</svg>`;
}
const CHECKS = [["peak","peak"],["curve","rising"],["post_peak","post"],["shape","shape"],["views","views"]];
function checkChips(c) {
 return CHECKS.map(([k, l]) => {
  const ok = c.checks ? c.checks[k] : undefined;
  if (ok === undefined) return "";
  const col = ok === true ? "var(--ok, #2a7)" : ok === false ? "var(--high)" : "var(--ink-3)";
  const mark = ok === true ? "✓" : ok === false ? "✗" : "–";
  return `<span style="color:${col};margin-right:6px;white-space:nowrap">${mark} ${l}</span>`;
 }).join("");
}
function shapeCell(c) {
 if (!c.shape) return "";
 return sameShape(c) ? "same" : `<span style="color:var(--high)">different</span>`;
}
function curveBar(c, key = "curve_pct", lk = "curve") {
 const x = c[key]; if (x == null) return "";
 const lim = c.limits[lk];
 let s = `<svg width="${CW}" height="16" role="img" aria-label="${lk} ${f(x)} %">`;
 for (const t of [0.1,1,10]) s += `<line x1="${cl(t)}" x2="${cl(t)}" y1="2" y2="14" stroke="var(--grid)"/>`;
 s += `<rect x="4" y="4" width="${Math.max(2, cl(x)-4)}" height="8" rx="2" fill="var(--s4)"/>`;
 if (lim != null) s += `<line x1="${cl(lim)}" x2="${cl(lim)}" y1="0" y2="16" stroke="var(--tol)" stroke-width="1.5"/>`;
 return s + `</svg>`;
}
function axisRow() {
 let a = `<svg width="${W}" height="14">`;
 for (const [t,l] of [[-10,"−10"],[-1,"−1"],[0,"0"],[1,"1"],[10,"10"]]) a += `<text x="${px(t)}" y="11" text-anchor="middle">${l}</text>`;
 a += `</svg>`;
 let b = `<svg width="${CW}" height="14">`;
 for (const [t,l] of [[0.01,"0.01"],[0.1,"0.1"],[1,"1"],[10,"10"],[100,"100"]]) b += `<text x="${Math.min(CW-12,Math.max(10,cl(t)))}" y="11" text-anchor="middle">${l}</text>`;
 return [a, b + `</svg>`];
}
H += `<h2>How close: peak, rising branch and post-peak</h2>
<p class="sub">Peak: r2c's largest load on the control chart against Response's (log scale both sides of zero; <span style="color:var(--low)">■</span> r2c lower, <span style="color:var(--high)">■</span> r2c higher). Rising and post-peak: largest distance between the two curves, measured both ways and split at Response's peak, as % of Response's peak (log scale). A response that runs on past Response's end, or stops short of it, shows as post-peak distance.</p>`;
const [ax1, ax2] = axisRow();
H += `<div class="scroll"><table><tr><th class="sticky">Case</th><th>Peak diff %</th><th></th><th>Rising %</th><th></th><th>Post-peak %</th><th></th><th>Shape</th><th>Stages R / r2c</th><th>Verdict</th><th>r2c s</th></tr>
<tr><td class="sticky"></td><td>${ax1}</td><td></td><td>${ax2}</td><td></td><td>${ax2}</td><td colspan="5"></td></tr>`;
for (const g of ["flexure","shear"]) {
 const a = by(g); if (!a.length) continue;
 H += `<tr class="grp"><td class="sticky" colspan="11">${G[g]}</td></tr>`;
 for (const c of a) H += `<tr data-tip="${esc(tipCase(c))}"><td class="sticky">${esc(c.label)}<div class="m">${esc(c.name)}</div></td><td>${peakBar(c)}</td><td class="num">${sg(c.peak_pct)}</td><td>${curveBar(c)}</td><td class="num">${f(c.curve_pct)}</td><td>${curveBar(c, "post_pct", "post_peak")}</td><td class="num">${f(c.post_pct)}</td><td>${shapeCell(c)}</td><td class="num">${c.stages[0]} / ${c.stages[1]}</td><td>${checkChips(c)}</td><td class="num">${c.seconds ?? ""}</td></tr>`;
}
H += `</table></div><p class="note">Stage counts are not compared (see docs/verification.md).</p>`;

// ---------- heatmap
const views = [...new Set(cases.flatMap(c => c.views.map(v => v.view)))];
const bins = [[1,"<1"],[2,"1–2"],[5,"2–5"],[10,"5–10"],[25,"10–25"],[100,"25–100"],[Infinity,"≥100"]];
const binOf = p => bins.findIndex(b => p < b[0]);
const cs = 18, lw = 112, th = 150;
H += `<h2>Detail views at the features of the curve</h2>
<p class="sub">Largest difference in each chart, as % of that chart's largest value, over the stages compared: cracking, falls of load, the peak and the last stage of Response's curve, each against r2c's stage at the same place (within the target in load and control value together, and not across a fall of load), or, where there is none, r2c's stage at the same feature of its curve (the tooltip names the stage). For a case with shear the last stage is not assessed and is drawn on its own below. A ring marks a view where Response itself spikes at one of the stages: that check is left out of the cell's colour and listed in the next section. Hatched rows: at the peak, r2c's nearest stage is more than 5 % away in control value, so the two are different states.</p>
<div class="legend">${bins.map((b,i)=>`<span><span class="sw" style="background:var(--s${i+1})"></span>${b[1]} %</span>`).join("")}
<span><span class="sw" style="background:var(--surface);border:1px solid var(--border)"></span>chart all zero</span>
<span><svg width="12" height="12" style="vertical-align:-2px;margin-right:4px"><circle cx="6" cy="6" r="3.5" fill="none" stroke="var(--ink)" stroke-width="1.5"/></svg>Response spikes at a stage: not assessed there</span></div>`;
function heat(rows, key, hatch) {
 let hm = `<svg width="${lw + views.length*cs + 4}" height="${th + rows.length*cs + 4}" role="img" aria-label="heatmap of detail-view differences">
<defs><pattern id="hatch" width="5" height="5" patternTransform="rotate(45)" patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="0" y2="5" stroke="var(--surface)" stroke-width="2"/></pattern></defs>`;
 views.forEach((v, j) => { const x = lw + j*cs + cs/2; hm += `<text transform="translate(${x+3},${th-4}) rotate(-70)">${esc(v.replaceAll("_"," "))}</text>`; });
 rows.forEach((c, i) => {
  const y = th + i*cs;
  hm += `<text x="${lw-4}" y="${y+13}" text-anchor="end">${esc(c.name)}</text>`;
  const far = hatch && (c.views_gap_pct ?? 0) > 5;
  views.forEach((v, j) => {
   const x = lw + j*cs, r = c[key].find(w => w.view === v);
   const un = key === "views" ? (c.unstable || []).filter(u => u.view === v) : [];
   if (!r && !un.length) return;
   const unTip = un.map(u => `\nResponse unstable at its stage ${u.stage}${u.feature?" ("+u.feature+")":""}: departs ${f(u.dep,1)} % from the blend of its neighbours, which are ${f(u.apart,1)} % apart; r2c differs ${u.pct==null?"(missing)":f(u.pct,1)+" %"}; not assessed`).join("");
   const ring = un.length ? `<circle cx="${x+cs/2}" cy="${y+cs/2}" r="3.5" fill="none" stroke="var(--surface)" stroke-width="3.5" pointer-events="none"/><circle cx="${x+cs/2}" cy="${y+cs/2}" r="3.5" fill="none" stroke="var(--ink)" stroke-width="1.5" pointer-events="none"/>` : "";
   if (!r) { hm += `<rect x="${x+1}" y="${y+1}" width="${cs-2}" height="${cs-2}" rx="2" fill="var(--surface)" stroke="var(--border)" data-tip="${esc(`${c.name} · ${v}\nno stage assessed${unTip}`)}"/>${ring}`; return; }
   let fill, tip;
   if (r.missing) { fill = "var(--surface)"; tip = `${c.name} · ${v}\nmissing in r2c`; }
   else if (r.ref_max === 0) { fill = "var(--surface)"; tip = `${c.name} · ${v}\nchart all zero in Response`; }
   else { fill = `var(--s${binOf(r.pct)+1})`; tip = `${c.name} · ${v}\n${f(r.pct,1)} % (${f(r.diff,3)} of ${f(r.ref_max,3)})${r.stage!=null?`\nworst at Response's stage ${r.stage}${r.feature?" ("+r.feature+")":""}`:""}${far?`\nstages differ by ${f(c.views_gap_pct,0)} % in control value`:""}`; }
   hm += `<rect x="${x+1}" y="${y+1}" width="${cs-2}" height="${cs-2}" rx="2" fill="${fill}" stroke="${fill==="var(--surface)"?"var(--border)":"none"}" data-tip="${esc(tip + unTip)}"/>`;
   if (r.missing) hm += `<text x="${x+cs/2}" y="${y+11}" text-anchor="middle">×</text>`;
   if (far && !r.missing) hm += `<rect x="${x+1}" y="${y+1}" width="${cs-2}" height="${cs-2}" fill="url(#hatch)" opacity="0.6" pointer-events="none"/>`;
   hm += ring;
  });
 });
 return `<div class="scroll">${hm}</svg></div>`;
}
H += heat(cases, "views", true);

// ---------- where Response is unstable (D54)
const unst = cases.flatMap(c => (c.unstable || []).map(u => ({...u, name: c.name})));
if ((D.tiers || []).length) {
 const lim = D.views_pct;
 H += `<h2>Where Response itself is unstable</h2>
<p class="sub">A view check means something only where Response's own result is steady. At each compared stage, Response's view is set against the blend of its views at the stage before and the stage after, taken at the stage's place along the control curve and measured as r2c is measured against Response; the two neighbours' views are measured against each other the same way. Where the neighbours agree within the target (${f(lim,0)} %) and the stage departs from their blend by more than the target, Response's view spikes there: the check is shown here with Response's own departure beside r2c's difference, and counts neither inside nor outside. A step, where the neighbours differ, stays assessed. A check is one view at one stage of one case; the first and last stage of a curve have no two neighbours and are not tested. The last columns count the same checks with no such rule, and with the rule as first written, which left steps unassessed as well.</p>
<div class="scroll"><table><tr><th>Priority</th><th>Checks</th><th>Inside</th><th>Outside</th><th>Unstable in Response, not assessed</th><th>No rule: inside</th><th>outside</th><th>As first written: inside</th><th>outside</th><th>unassessed</th></tr>
${D.tiers.map(t => `<tr><td>${t.tier}</td><td class="num">${t.checks}</td><td class="num">${t.inside}</td><td class="num">${t.outside}</td><td class="num">${t.unstable}</td><td class="num">${t.plain_inside}</td><td class="num">${t.plain_outside}</td><td class="num">${t.first_inside}</td><td class="num">${t.first_outside}</td><td class="num">${t.first_unstable}</td></tr>`).join("")}</table></div>`;
 const pair = u => {
  let s = `<svg width="${CW}" height="18" role="img" aria-label="Response departs ${f(u.dep,1)} %, r2c differs ${u.pct==null?"missing":f(u.pct,1)+" %"}">`;
  for (const t of [0.1,1,10]) s += `<line x1="${cl(t)}" x2="${cl(t)}" y1="1" y2="17" stroke="var(--grid)"/>`;
  s += `<rect x="4" y="2" width="${Math.max(2, cl(u.dep)-4)}" height="6" rx="2" fill="var(--ref)"/>`;
  if (u.pct != null) s += `<rect x="4" y="10" width="${Math.max(2, cl(u.pct)-4)}" height="6" rx="2" fill="var(--sub)"/>`;
  if (lim != null) s += `<line x1="${cl(lim)}" x2="${cl(lim)}" y1="0" y2="18" stroke="var(--tol)" stroke-width="1.5"/>`;
  return s + `</svg>`; };
 const list = tier => { const a = unst.filter(u => u.tier === tier); if (!a.length) return "";
  a.sort((p, q) => p.name.localeCompare(q.name) || p.stage - q.stage || q.dep - p.dep);
  return `<details${tier.startsWith("1") ? " open" : ""}><summary>${tier}: ${a.length} check${a.length === 1 ? "" : "s"} not assessed${tier.startsWith("1") ? "" : ""}</summary>
<div class="scroll"><table><tr><th class="sticky">Case</th><th>Response's stage</th><th>View</th><th>Response's departure %</th><th>Its neighbours apart %</th><th>r2c's difference %</th><th></th><th></th></tr>
<tr><td class="sticky"></td><td colspan="5"></td><td>${ax2}</td><td></td></tr>
${a.map(u => `<tr><td class="sticky">${esc(u.name)}</td><td>${u.stage}${u.feature ? " (" + esc(u.feature) + ")" : ""}</td><td>${esc(u.view.replaceAll("_"," "))}</td><td class="num">${f(u.dep,1)}</td><td class="num">${f(u.apart,1)}</td><td class="num">${u.pct == null ? "missing" : f(u.pct,1)}</td><td>${pair(u)}</td><td>${u.outside ? `<span style="color:var(--ink-2)">would be outside</span>` : ""}</td></tr>`).join("")}</table></div></details>`; };
 H += `<div class="legend"><span><span class="sw" style="background:var(--ref)"></span>Response's departure from the blend of its neighbours</span><span><span class="sw" style="background:var(--sub)"></span>r2c's difference from Response</span><span><span class="ln" style="border-color:var(--tol)"></span>target</span></div>`;
 H += unst.length ? [...new Set(unst.map(u => u.tier))].sort().map(list).join("") : `<p class="note">No check is unstable in this run.</p>`;
}
const enders = cases.filter(c => (c.views_end || []).length);
if (enders.length) H += `<h2>Detail views at the last stage of the shear cases</h2>
<p class="sub">Reported, not assessed: how a shear response ends is not chased in this phase, so the two programs are often in different states at the last stage.</p>` + heat(enders, "views_end", false);

// ---------- curves
H += `<h2>Control curves</h2><p class="sub">The chart each case is compared on. Dots: each one's peak.</p>
<div class="legend"><span><span class="ln" style="border-color:var(--ref)"></span>Response-2000</span><span><span class="ln" style="border-color:var(--sub)"></span>r2c</span></div><div class="multi">`;
for (const g of ["flexure","shear"]) for (const c of by(g)) {
 if (!c.curve) continue;
 const k = c.curve;
 const note = !k.sub ? `<div class="m">No r2c record for this case in the curves folder: Response only.</div>`
  : k.other_run ? `<div class="m">r2c curve from run ${esc(k.other_run)}, metrics from ${esc(c.run)}.</div>` : "";
 H += `<div class="panel"><h3>${esc(c.label)}</h3><div class="m">${esc(c.name)} · ${esc(k.y)}<br>peak ${sg(c.peak_pct)} % · rising ${f(c.curve_pct)} % · post-peak ${f(c.post_pct)} %${c.shape && !sameShape(c) ? `<br>shape differs: Response ${esc(c.shape[0].join(", "))}; r2c ${esc(c.shape[1].join(", "))}` : ""}</div>${plot(c)}${note}</div>`;
}
H += `</div><p class="note">Generated by tools/dashboard.py. Every number comes from the run named at the top.</p>`;
}
KIND === "front" ? front() : details();
$("#root").innerHTML = H;

// ---------- tooltips (hover and tap)
const tip = $("#tip");
function show(e) { const t = e.target.closest("[data-tip]"); if (!t) { tip.style.display = "none"; return; }
 tip.textContent = t.getAttribute("data-tip"); tip.style.display = "block";
 const r = tip.getBoundingClientRect(), x = Math.min(e.clientX + 12, innerWidth - r.width - 6), y = e.clientY + 14 + r.height > innerHeight ? e.clientY - r.height - 10 : e.clientY + 14;
 tip.style.left = x + "px"; tip.style.top = y + "px"; }
document.addEventListener("mousemove", show);
document.addEventListener("click", show);
addEventListener("scroll", () => tip.style.display = "none", {passive: true});
</script></body></html>
"""


def render(data: dict, kind: str = "details") -> str:
    """The front page (kind "front") or the details page, as HTML."""
    if kind == "front":
        # the front page draws only the curves of the cases outside target
        data = dict(data, cases=[c if c.get("curve_out") or "problem" in c else
                                 {k: v for k, v in c.items()
                                  if k not in ("curve", "views", "views_end", "unstable")}
                                 for c in data["cases"]], gaps=[], tiers=[])
    blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    return PAGE.replace("__KIND__", kind).replace("__DATA__", blob)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("results", nargs="?", default=str(ROOT / "docs" / "verification-results.json"),
                    help="a verify output folder, or a combined results JSON")
    ap.add_argument("--curves", help="verify output folder holding r2c's records")
    ap.add_argument("--reference", default=str(ROOT / "tests" / "oracle"))
    ap.add_argument("--targets", default=str(ROOT / "docs" / "measures.md"))
    ap.add_argument("--notes", default=str(ROOT / "docs" / "verification.md"),
                    help="where the 'Not compared' list is read from")
    ap.add_argument("--out", default="index.html",
                    help="the front page; details.html is written beside it")
    a = ap.parse_args(argv)
    res = Path(a.results)
    run, results = load_results(res)
    curves = Path(a.curves) if a.curves else (res if res.is_dir() else None)
    acc = report.read_targets(Path(a.targets))
    data = build(run, results, acc, curves, Path(a.reference), not_compared(Path(a.notes)))
    out = Path(a.out)
    out.write_text(render(data, "front"), encoding="utf-8")
    det = out.with_name("details.html")
    det.write_text(render(data), encoding="utf-8")
    n = sum(1 for c in data["cases"] if c.get("curve", {}).get("sub"))
    k = sum(1 for c in data["cases"] if c.get("curve_out"))
    print(f"wrote {out} and {det}: {len(data['cases'])} development cases, r2c curves for "
          f"{n}, {k} outside target on the control curve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
