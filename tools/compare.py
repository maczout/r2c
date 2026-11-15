#!/usr/bin/env python3
"""Compare two r2x-raw records: a reference and a subject.

    python tools/compare.py REFERENCE.r2x.txt SUBJECT.r2x.txt [--views] [--json]

Either record may come from r2x (Response-2000 itself) or from r2c: the format is the same, so
the two programs are interchangeable on both sides of the comparison.

What is compared:

* the number of load stages and the stage shown as the peak;
* every control chart: the peak load, the control value there, and how far the reference's
  rising branch lies from the subject's curve (the largest and the mean distance of its points
  from the subject's polyline, with the load scaled by the reference's peak load and the control
  value by its largest value on that branch, as a percentage);
* with --views, every detail view at the peak: the subject's stage nearest the reference's peak
  in control value; for each chart the largest distance of the reference's points from the
  subject's curve, as a percentage of the chart's largest value (depth scaled by the section
  depth).

No pass or fail is decided here: the numbers are for an engineer to judge.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from r2c import record  # noqa: E402


def parse_chart(body: bytes):
    """A chart's text as (title, x title, y title, [array of (x, y) per line])."""
    title = xt = yt = None
    lines: list[list[tuple[float, float]]] = []
    cur = None
    for ln in body.decode("latin1").splitlines():
        s = ln.strip()
        if s.startswith("Title"):
            title = s.split(":", 1)[1].strip() if ":" in s else s
        elif s.startswith("X Axis Title"):
            xt = s.split(":", 1)[1].strip()
        elif s.startswith("Y Axis Title"):
            yt = s.split(":", 1)[1].strip()
        elif s.startswith("Line type") or s == "New Line":
            cur = []
            lines.append(cur)
        elif cur is not None and s:
            p = s.split()
            try:
                cur.append((float(p[0]), float(p[1])))
            except (ValueError, IndexError):
                pass
    return title, xt, yt, [np.array(c, dtype=float).reshape(-1, 2) for c in lines]


def control_keys(rec) -> list[str]:
    return [k.split("/", 1)[1] for k in rec.sections if k.startswith("control/")]


def _curve(rec, key):
    return parse_chart(rec.control(key))[3][0]


def curve_distance(a, b, xs, ys):
    """How far each point of curve a lies from curve b (a polyline), with x scaled by xs and y
    by ys: the largest and the mean distance. Works for curves that double back or jump."""
    if len(a) == 0 or len(b) == 0:
        return float("nan"), float("nan")
    pa = np.column_stack([a[:, 0] / xs, a[:, 1] / ys])
    pb = np.column_stack([b[:, 0] / xs, b[:, 1] / ys])
    if len(pb) == 1:
        d = np.hypot(*(pa - pb[0]).T)
        return float(d.max()), float(d.mean())
    p0, p1 = pb[:-1], pb[1:]
    seg = p1 - p0
    len2 = np.maximum(np.sum(seg * seg, axis=1), 1e-30)
    best = np.full(len(pa), np.inf)
    for i in range(len(p0)):
        t = np.clip(((pa - p0[i]) @ seg[i]) / len2[i], 0.0, 1.0)
        d = np.hypot(*(pa - (p0[i] + t[:, None] * seg[i])).T)
        best = np.minimum(best, d)
    return float(best.max()), float(best.mean())


def _rising(c):
    """The curve up to its largest load."""
    if len(c) == 0:
        return c, 0
    ip = int(np.argmax(np.abs(c[:, 1])))
    return c[: ip + 1], ip


def compare_control(ref, sub, key):
    a, b = _curve(ref, key), _curve(sub, key)
    ra, ia = _rising(a)
    rb, ib = _rising(b)
    out = {
        "chart": key,
        "ref_peak_load": float(a[ia, 1]), "sub_peak_load": float(b[ib, 1]),
        "ref_peak_x": float(a[ia, 0]), "sub_peak_x": float(b[ib, 0]),
    }
    pk = abs(a[ia, 1])
    out["peak_diff_pct"] = float(100.0 * (abs(b[ib, 1]) - pk) / pk) if pk > 0 else 0.0
    xs = float(np.max(np.abs(ra[:, 0]))) if len(ra) else 0.0
    if len(ra) > 1 and len(rb) > 1 and pk > 0 and xs > 0:
        # the reference's rising branch against the subject's whole curve
        dmax, dmean = curve_distance(ra, b, xs, pk)
        out["curve_max_diff_pct"] = 100.0 * dmax
        out["curve_mean_diff_pct"] = 100.0 * dmean
    return out


def _nearest_stage(sub, key, x):
    c = _curve(sub, key)
    have = sub.stages()
    if not have:
        return None
    best = min(have, key=lambda n: abs(c[n, 0] - x) if n < len(c) else float("inf"))
    return best


def compare_views(ref, sub, ref_stage, sub_stage):
    rows = []
    prefix = f"stage/{ref_stage}/"
    for name in ref.sections:
        if not name.startswith(prefix):
            continue
        key = name[len(prefix):]
        try:
            sb = sub.stage(sub_stage, key)
        except KeyError:
            rows.append({"view": key, "missing": True})
            continue
        la = parse_chart(ref.stage(ref_stage, key))[3]
        lb = parse_chart(sb)[3]
        worst = 0.0
        scale = 0.0
        span = 0.0
        for a in la:
            if len(a):
                scale = max(scale, float(np.max(np.abs(a[:, 0]))))
                span = max(span, float(np.ptp(a[:, 1])))
        for i, a in enumerate(la):
            if len(a) == 0 or scale <= 1e-9:
                continue
            if i >= len(lb) or len(lb[i]) == 0:
                worst = max(worst, float(np.max(np.abs(a[:, 0]))))
                continue
            dmax, _ = curve_distance(a, lb[i], scale, max(span, 1e-9))
            worst = max(worst, dmax * scale)
        rows.append({"view": key, "ref_max": scale, "max_diff": worst,
                     "max_diff_pct": float(100.0 * worst / scale) if scale > 1e-9 else 0.0,
                     "lines": [len(la), len(lb)]})
    return rows


def compare(ref, sub, views=False):
    keys = [k for k in control_keys(ref) if k in control_keys(sub)]
    out = {
        "ref": {k: ref.header.get(k) for k in ("input-name", "units", "factors", "initial",
                                                "increment", "more-detail", "stage-count",
                                                "peak-stage")},
        "sub": {k: sub.header.get(k) for k in ("stage-count", "peak-stage")},
        "control": [compare_control(ref, sub, k) for k in keys],
        "missing_control": [k for k in control_keys(ref) if k not in keys],
    }
    if views and keys:
        rp = int(ref.header.get("peak-stage", "0"))
        if rp in ref.stages():
            x = _curve(ref, keys[-1])[rp, 0]
            sp = _nearest_stage(sub, keys[-1], x)
            if sp is not None:
                out["views_at"] = {"ref_stage": rp, "sub_stage": sp, "ref_x": float(x),
                                   "sub_x": float(_curve(sub, keys[-1])[sp, 0])}
                out["views"] = compare_views(ref, sub, rp, sp)
    return out


def render(res) -> str:
    r, s = res["ref"], res["sub"]
    lines = [
        f"input {r['input-name']}  units {r['units']}  factors {r['factors']}  "
        f"initial {r['initial']}  increment {r['increment']}  more-detail {r['more-detail']}",
        f"stages: reference {r['stage-count']} (peak at {r['peak-stage']}), "
        f"subject {s['stage-count']} (peak at {s['peak-stage']})",
        "",
        f"{'control chart':<14}{'ref peak':>11}{'sub peak':>11}{'diff %':>8}"
        f"{'ref x':>10}{'sub x':>10}{'curve max %':>13}{'mean %':>8}",
    ]
    for c in res["control"]:
        lines.append(
            f"{c['chart']:<14}{c['ref_peak_load']:>11.2f}{c['sub_peak_load']:>11.2f}"
            f"{c['peak_diff_pct']:>8.2f}{c['ref_peak_x']:>10.3f}{c['sub_peak_x']:>10.3f}"
            + (f"{c['curve_max_diff_pct']:>13.2f}{c['curve_mean_diff_pct']:>8.2f}"
               if "curve_max_diff_pct" in c else ""))
    for k in res["missing_control"]:
        lines.append(f"{k:<14} missing from the subject")
    if "views" in res:
        v = res["views_at"]
        lines += ["", f"detail views: reference stage {v['ref_stage']} (control value "
                      f"{v['ref_x']:.3f}), subject stage {v['sub_stage']} ({v['sub_x']:.3f})",
                  f"{'view':<38}{'ref max':>12}{'max diff':>12}{'% of max':>10}"]
        for row in res["views"]:
            if row.get("missing"):
                lines.append(f"{row['view']:<38} missing from the subject")
            else:
                lines.append(f"{row['view']:<38}{row['ref_max']:>12.4f}{row['max_diff']:>12.4f}"
                             f"{row['max_diff_pct']:>10.1f}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("reference")
    ap.add_argument("subject")
    ap.add_argument("--views", action="store_true", help="also compare the detail views at the peak")
    ap.add_argument("--json", action="store_true", help="print the comparison as JSON")
    a = ap.parse_args(argv)
    res = compare(record.read(a.reference), record.read(a.subject), views=a.views)
    print(json.dumps(res, indent=1) if a.json else render(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
