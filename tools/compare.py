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
  value by its largest value on that branch, as a percentage); and the two-way distance
  between the whole curves, split at the reference's peak into rising and post-peak (each
  curve's points against the other's curve, load scaled by the reference's peak, control value
  by its largest value over the whole curve). One-way misses a subject that runs on past the
  reference's end; two-way does not; and the curve's shape: its features in order (cracking,
  falls of load before the peak, the peak, and how the response ends);
* with --views, every detail view at each of the reference's detail stages (the features of
  its curve: cracking, falls of load, the peak, the last stage; see feature_stages): the
  subject's stage nearest the reference's in load and control value together, between the
  same features of the curves when both have them (D13, _segment_stage); for each
  chart the largest distance of the reference's points from the subject's curve, as a percentage of the chart's largest value (depth scaled by the section
  depth);
* with --views, where the reference holds the views of the stages just before and after a
  detail stage: how far the reference's own view at that stage lies from the blend of its
  two neighbours' views, and how far the two neighbours' views lie from each other, by the
  same measure (owner, 2026-11-23, D54 and D56; docs/acceptance.md, "Where Response is
  unstable"; see departure and apart).

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


def resolution(body: bytes) -> tuple[float, float]:
    """The printed resolution of a chart's x and y values: one unit in the last decimal
    place shown (Response prints a fixed number of decimals per chart)."""
    dx = dy = 0
    for ln in body.decode("latin1").splitlines():
        p = ln.split()
        if len(p) >= 2:
            try:
                float(p[0]), float(p[1])
            except ValueError:
                continue
            dx = max(dx, len(p[0].partition(".")[2]))
            dy = max(dy, len(p[1].partition(".")[2]))
    return 10.0 ** -dx, 10.0 ** -dy


# A difference within this many units of the last printed digit is never a miss (owner,
# 2026-11-21: absolute limits for small values close to the numerical precision).
FLOOR_DIGITS = 2


def control_keys(rec) -> list[str]:
    return [k.split("/", 1)[1] for k in rec.sections if k.startswith("control/")]


def _curve(rec, key):
    return parse_chart(rec.control(key))[3][0]


def project(a, b, xs, ys):
    """Each point of curve a against curve b (a polyline), with x scaled by xs and y by ys:
    its distance from b, and where on b its nearest point lies, as a position along b
    (segment index plus the fraction along that segment: 0 at b's first point, len(b) - 1
    at its last). Works for curves that double back or jump."""
    pa = np.column_stack([a[:, 0] / xs, a[:, 1] / ys])
    pb = np.column_stack([b[:, 0] / xs, b[:, 1] / ys])
    if len(pb) == 1:
        return np.hypot(*(pa - pb[0]).T), np.zeros(len(pa))
    p0, p1 = pb[:-1], pb[1:]
    seg = p1 - p0
    len2 = np.maximum(np.sum(seg * seg, axis=1), 1e-30)
    best = np.full(len(pa), np.inf)
    pos = np.zeros(len(pa))
    for i in range(len(p0)):
        t = np.clip(((pa - p0[i]) @ seg[i]) / len2[i], 0.0, 1.0)
        d = np.hypot(*(pa - (p0[i] + t[:, None] * seg[i])).T)
        closer = d < best
        best = np.where(closer, d, best)
        pos = np.where(closer, i + t, pos)
    return best, pos


def curve_distance(a, b, xs, ys):
    """How far each point of curve a lies from curve b (a polyline), with x scaled by xs and y
    by ys: the largest and the mean distance."""
    if len(a) == 0 or len(b) == 0:
        return float("nan"), float("nan")
    d, _ = project(a, b, xs, ys)
    return float(d.max()), float(d.mean())


def two_way(a, ia, b, xs, ys):
    """The two-way distance between the reference's curve a (peak at index ia) and the
    subject's curve b, split at the reference's peak: (rising, post-peak), each the largest
    distance in either direction, as a fraction, or None for a part with no points.

    Rising: the reference's points up to its peak against b, and the subject's points whose
    nearest point on a lies before a's peak, against a. Post-peak: the rest of both. A
    subject's point beyond the reference's end projects onto that end, so a response that runs
    on past the reference's, or stops short of it, counts as distance after the peak."""
    da, _ = project(a, b, xs, ys)
    db, pos = project(b, a, xs, ys)
    post_b = pos >= ia - 1e-9
    rise = np.concatenate([da[: ia + 1], db[~post_b]])
    post = np.concatenate([da[ia + 1:], db[post_b]])
    return (float(rise.max()) if len(rise) else None,
            float(post.max()) if len(post) else None)


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
    xw = float(np.max(np.abs(a[:, 0]))) if len(a) else 0.0
    sa, sb = shape(a, pk, xw), shape(b, pk, xw)
    if sa:
        out["shape_ref"] = [f for f, _ in sa]
        out["shape_sub"] = [f for f, _ in sb]
        out["shape_same"] = out["shape_ref"] == out["shape_sub"]
    if len(a) > 1 and len(b) > 0 and pk > 0 and xw > 0:
        # both curves, both ways; scaled by the reference's peak load and its largest control
        # value over the whole curve
        rise, post = two_way(a, ia, b, xw, pk)
        rx, ry = resolution(ref.control(key))
        out["floor_pct"] = 100.0 * FLOOR_DIGITS * float(np.hypot(rx / xw, ry / pk))
        if rise is not None:
            out["rising_pct"] = 100.0 * rise
        if post is not None:
            out["post_peak_pct"] = 100.0 * post
    return out


# Curve shape (owner, 2026-11-21: curves match qualitatively, in the features of their shape).
# Thresholds are the developer's, fitted on the 25 oracle cases; a second stiffness drop
# ("yield") was tried and dropped, because it also finds other softening.
CRACK_STIFFNESS = 0.4   # cracking: the first step whose stiffness is below this × the first's
FALL = 0.02             # a fall of load: below the largest so far by this × Response's peak


def shape(c, pk, xs):
    """The features of a control curve, in order along it: "cracking", "fall" (of load before
    the peak), "peak", and how the response ends: "ends falling", "ends standing still" (more
    stages at the peak load) or "ends at peak". Load is scaled by pk, control value by xs
    (both the reference's, so both curves are read alike). [(feature, index)]."""
    if len(c) == 0 or pk <= 0 or xs <= 0:
        return []
    ip = int(np.argmax(np.abs(c[:, 1])))
    sgn = np.sign(c[ip, 0]) or 1.0
    x = c[:, 0] * sgn / xs
    y = np.abs(c[:, 1]) / pk
    ev = []
    k0 = None
    for i in range(1, ip + 1):
        dx, dy = x[i] - x[i - 1], y[i] - y[i - 1]
        if dx <= 1e-9 or dy <= 0:
            continue
        k = dy / dx
        if k0 is None:
            k0 = k
        elif k < CRACK_STIFFNESS * k0:
            ev.append(("cracking", i))
            break
    falling = False
    for i in range(1, ip):
        below = y[i] < y[:i].max() - FALL
        if below and not falling:
            ev.append(("fall", i))
        falling = below
    ev.append(("peak", ip))
    if ip == len(c) - 1:
        ev.append(("ends at peak", ip))
    elif y[-1] < y[ip] - FALL:
        ev.append(("ends falling", len(c) - 1))
    else:
        ev.append(("ends standing still", len(c) - 1))
    order = ["cracking", "fall", "peak"]
    ev.sort(key=lambda e: (e[1], order.index(e[0]) if e[0] in order else 3))
    return ev


def _nearest_stage(sub, key, x, y, xs, ys):
    """The subject's detail stage nearest the point (x, y) of a control chart, with control
    value scaled by xs and load by ys (owner, 2026-11-21: views are matched to a state by load
    and control value together)."""
    c = _curve(sub, key)
    have = [n for n in sub.stages() if n < len(c)]
    if not have:
        return None
    return min(have, key=lambda n: np.hypot((c[n, 0] - x) / xs, (c[n, 1] - y) / ys))


def _segment_stage(sub, key, rs, a, b, x, y, xs, ys):
    """D13 (owner, 2026-11-22): the subject's stage matched to the reference's stage rs,
    respecting the features of the curves. Nearest by load and control value alone can jump
    across a fall of load: r2c's stage before the fall, still uncracked, can be nearer than
    its stage after it. So when the two curves have the same features before the end, a
    reference stage at a feature is matched to the subject's stage at that feature, and any
    other stage to the nearest subject stage between the same two features. Otherwise, or if
    there is no subject stage there, the nearest stage overall, as _nearest_stage."""
    fa = [(f, i) for f, i in shape(a, ys, xs) if not f.startswith("ends")]
    fb = [(f, i) for f, i in shape(b, ys, xs) if not f.startswith("ends")]
    have = [n for n in sub.stages() if n < len(b)]
    if not have:
        return None

    def nearest(ns):
        return min(ns, key=lambda n: np.hypot((b[n, 0] - x) / xs, (b[n, 1] - y) / ys))

    if [f for f, _ in fa] != [f for f, _ in fb]:
        return nearest(have)
    ia, ib = [i for _f, i in fa], [i for _f, i in fb]
    if rs in ia:
        t = ib[ia.index(rs)]
        if t in have:
            return t
    # the segment: between the features on either side of rs
    k = sum(1 for i in ia if i < rs)
    lo = ib[k - 1] if k > 0 else -1
    hi = ib[k] if k < len(ib) else len(b)
    cand = [n for n in have if lo < n < hi] or [n for n in have if lo <= n <= hi]
    return nearest(cand or have)


def same_place_limit(ref) -> float:
    """How near two stages must be to count as "at the same place" (D42): the target on the
    curves of docs/acceptance.md (curve_pct of the case's group), as a fraction. 0.05 where
    the file sets none."""
    import report
    try:
        acc = report.read_acceptance(Path(__file__).resolve().parents[1] / "docs" / "acceptance.md")
        pct = acc.get(report.group(ref.header), {}).get("curve_pct")
    except (OSError, SystemExit, KeyError, ValueError):
        pct = None
    return 0.05 if pct is None else pct / 100.0


def _same_place_stage(sub, rs, a, b, x, y, xs, ys, limit):
    """D42 (owner, 2026-11-22): the subject's stage at the same place as the reference's
    stage rs: the nearest in load and control value together (load scaled by ys, control
    value by xs, as the curves are measured), if it is within the target (limit, a
    fraction). None if there is none.

    D13's purpose is kept: no matching across a fall of load. Where the two curves have the
    same number of falls before the peak, only the subject's stages that have as many falls
    behind them as rs has are looked at, so r2c's stage before a fall is never taken for
    Response's stage after it, however near. A stage at a fall (the first one below) counts
    as after it."""
    fa = [i for f, i in shape(a, ys, xs) if f == "fall"]
    fb = [i for f, i in shape(b, ys, xs) if f == "fall"]
    have = [n for n in sub.stages() if n < len(b)]
    if len(fa) == len(fb):
        behind = sum(1 for i in fa if i <= rs)
        have = [n for n in have if sum(1 for i in fb if i <= n) == behind]
    if not have:
        return None

    def dist(n):
        return float(np.hypot((b[n, 0] - x) / xs, (b[n, 1] - y) / ys))

    n = min(have, key=dist)
    return n if dist(n) <= limit else None


def match_stage(sub, key, rs, a, b, xs, ys, limit):
    """The subject's stage whose views are compared with those of the reference's stage rs,
    and how it was found: (stage, "same place" or "feature"). Where the two curves have a
    stage at the same place, those are compared (D42); the stage matched by the features of
    the curves (D13) only where they do not. a, b: the two curves of control chart key."""
    x, y = float(a[rs, 0]), float(a[rs, 1])
    n = _same_place_stage(sub, rs, a, b, x, y, xs, ys, limit)
    if n is not None:
        return n, "same place"
    return _segment_stage(sub, key, rs, a, b, x, y, xs, ys), "feature"


def feature_stages(rec, key=None) -> dict[int, str]:
    """The stages at the features of a record's control curve (the bottom chart unless key is
    given), with the peak stage from its header: {stage: feature}. The stages whose detail
    views are compared (owner, 2026-11-21)."""
    key = key or control_keys(rec)[-1]
    c = _curve(rec, key)
    pk = float(np.max(np.abs(c[:, 1]))) if len(c) else 0.0
    xs = float(np.max(np.abs(c[:, 0]))) if len(c) else 0.0
    out: dict[int, str] = {}
    for f, i in shape(c, pk, xs):
        out.setdefault(i, f)
    hp = rec.header.get("peak-stage")
    if hp not in (None, ""):
        out.setdefault(int(hp), "peak")
    return out


def lines_distance(la, lb, scale=None):
    """The distance measure of the detail views: how far the lines la of a chart lie from
    the lines lb of another, line by line in the order they are drawn. (worst, scale): the
    largest distance of la's points from lb's curve, in the chart's units, and the chart's
    largest value in la. Values are scaled by that largest value and depth by the chart's
    span of depth; a line of la with no line in lb counts at its full size.

    With scale given, values are scaled by it and not by la's own largest value: two charts
    measured on the scale of a third (apart)."""
    worst = 0.0
    own = 0.0
    span = 0.0
    for a in la:
        if len(a):
            own = max(own, float(np.max(np.abs(a[:, 0]))))
            span = max(span, float(np.ptp(a[:, 1])))
    scale = own if scale is None else scale
    for i, a in enumerate(la):
        if len(a) == 0 or scale <= 1e-9:
            continue
        if i >= len(lb) or len(lb[i]) == 0:
            worst = max(worst, float(np.max(np.abs(a[:, 0]))))
            continue
        dmax, _ = curve_distance(a, lb[i], scale, max(span, 1e-9))
        worst = max(worst, dmax * scale)
    return worst, scale


# -- where the reference is unstable (owner, 2026-11-23, D54, narrowed to spikes by D56) --------
#
# docs/acceptance.md, "Where Response is unstable": a view at a stage is unstable when its
# two neighbours agree with each other within the views target AND Response's own view at
# the stage lies farther than the views target from the blend of its two neighbours' views,
# taken at that stage's place along the control curve, each with the same distance measure
# and printed-precision floor as the comparison. Here the two distances are measured
# (departure, apart); tools/report.py sets them against the target.
#
# The choices the wording leaves open. PLACE and LINES are the owner's (D55, readings
# confirmed 2026-11-23). APART is the developer's reading of "agree with each other", for
# the owner to confirm (docs/summary.md, D58); tools/unstable.py says how much each moves.
PLACE = "curve"    # the stage's place between its neighbours: see place
LINES = "zero"     # a line one neighbour does not have: see blend_lines
APART = "own"      # the chart the neighbours' difference is a percentage of: see apart


def place(a, rs, xs, ys, how=PLACE):
    """Where stage rs lies between the stage before and the stage after on the control curve
    a: 0 at the one before, 1 at the one after. None without both neighbours.

    "curve" (the reading in use): by distance along the curve, load scaled by ys and control
    value by xs as the curves are measured, so it holds on any branch, at a peak and across a
    fall of load. The other readings, for tools/unstable.py: "control" by control value
    alone, "load" by load alone (both fail where that value turns back, and are then taken
    as "middle"), "middle" half way."""
    if rs < 1 or rs + 1 >= len(a):
        return None
    p0, p1, p2 = (np.array([a[i, 0] / xs, a[i, 1] / ys]) for i in (rs - 1, rs, rs + 1))
    if how == "curve":
        d0, d1 = float(np.hypot(*(p1 - p0))), float(np.hypot(*(p2 - p1)))
        return d0 / (d0 + d1) if d0 + d1 > 1e-12 else 0.5
    if how in ("control", "load"):
        k = 0 if how == "control" else 1
        if abs(p2[k] - p0[k]) > 1e-12:
            t = float((p1[k] - p0[k]) / (p2[k] - p0[k]))
            if 0.0 <= t <= 1.0:
                return t
    return 0.5


def _by_depth(line):
    """A line as (u, x) with u = -depth not decreasing along it, or None if its depth turns
    back (the steel charts, drawn as boxes)."""
    if len(line) < 2:
        return -line[:, 1], line[:, 0]
    d = np.diff(line[:, 1])
    if np.all(d <= 1e-9):
        return -line[:, 1], line[:, 0]
    if np.all(d >= -1e-9):
        return -line[::-1, 1], line[::-1, 0]
    return None


def _sides(u, x, q):
    """The value of a line at each depth q, on the side it is approached from and on the
    side it is left: they differ where the line steps (two points at one depth). Beyond its
    ends a line keeps its end value."""
    lo = np.searchsorted(u, q, "left")
    hi = np.searchsorted(u, q, "right")
    before, after = np.empty(len(q)), np.empty(len(q))
    for j, (i0, i1, v) in enumerate(zip(lo, hi, q)):
        if i0 < i1:                       # a point of the line, or several at this depth
            before[j], after[j] = x[i0], x[i1 - 1]
        elif i0 == 0:
            before[j] = after[j] = x[0]
        elif i0 == len(u):
            before[j] = after[j] = x[-1]
        else:
            f = (v - u[i0 - 1]) / (u[i0] - u[i0 - 1])
            before[j] = after[j] = x[i0 - 1] + f * (x[i0] - x[i0 - 1])
    return before, after


def blend_line(p, q, t):
    """The line a fraction t of the way from line p to line q, or None if it cannot be
    formed. Lines with the same points in depth are blended point by point. Response layers
    the section afresh at each stage, so most lines are not; those are blended by depth:
    at every depth where either has a point, the two values there, a step in either kept as
    a step. That needs depth to run one way along both lines."""
    if len(p) == len(q) and len(p) and np.allclose(p[:, 1], q[:, 1], rtol=0.0, atol=1e-6):
        return np.column_stack([(1.0 - t) * p[:, 0] + t * q[:, 0], p[:, 1]])
    dp, dq = _by_depth(p), _by_depth(q)
    if dp is None or dq is None:
        return None
    u = np.union1d(dp[0], dq[0])
    pb, pa = _sides(*dp, u)
    qb, qa = _sides(*dq, u)
    out = []
    for j, v in enumerate(u):
        out.append(((1.0 - t) * pb[j] + t * qb[j], -v))
        if pa[j] != pb[j] or qa[j] != qb[j]:
            out.append(((1.0 - t) * pa[j] + t * qa[j], -v))
    return np.array(out, dtype=float).reshape(-1, 2)


def blend_lines(lp, lq, t, lines=LINES):
    """The chart a fraction t of the way from the chart with lines lp to the one with lines
    lq, line by line in the order they are drawn, or None if a line cannot be blended.

    A line that only one of the two has (Response draws some lines only once there is
    something to show, such as the shear on the crack): with "zero", the reading in use, it
    is blended with nothing, a line of zeros, so it comes in or goes out by degrees. With
    "both", the other reading (tools/unstable.py), the blend has only the lines both have,
    and a line of the stage's with none in the blend counts at its full size."""
    out = []
    for i in range(max(len(lp), len(lq))):
        p = lp[i] if i < len(lp) else np.zeros((0, 2))
        q = lq[i] if i < len(lq) else np.zeros((0, 2))
        if len(p) == 0 and len(q) == 0:
            out.append(np.zeros((0, 2)))
        elif len(p) == 0 or len(q) == 0:
            if lines == "both":
                out.append(np.zeros((0, 2)))
            else:
                w, one = (1.0 - t, p) if len(q) == 0 else (t, q)
                out.append(np.column_stack([w * one[:, 0], one[:, 1]]))
        else:
            b = blend_line(p, q, t)
            if b is None:
                return None
            out.append(b)
    return out


def view_body(rec, stage, key):
    """A detail view of a stage of a record, whether the record holds the stage as one to
    compare (stage/N/VIEW) or as a neighbour (neighbour/N/VIEW, tools/trim.py). None if it
    holds neither."""
    body = rec.sections.get(record.stage_section(stage, key))
    return body if body is not None else rec.sections.get(f"neighbour/{stage}/{key}")


def departure(ref, stage, key, t, lines=LINES):
    """How far the reference's own view at a stage lies from the blend of its views at the
    stage before and the stage after, t of the way from the one to the other: the largest
    distance of its points from the blend, in the chart's units, by the measure of the
    comparison (lines_distance). None where it cannot be tested: a neighbour's view is not
    in the record, or a line cannot be blended."""
    before, after = view_body(ref, stage - 1, key), view_body(ref, stage + 1, key)
    if t is None or before is None or after is None:
        return None
    blend = blend_lines(parse_chart(before)[3], parse_chart(after)[3], t, lines)
    if blend is None:
        return None
    return lines_distance(parse_chart(ref.stage(stage, key))[3], blend)[0]


def apart(ref, stage, key, how=APART):
    """How far the reference's views at the stage before and the stage after lie from each
    other, as a percentage, by the measure of the comparison (lines_distance) taken both
    ways, since neither neighbour is the reference: the larger of the two. A distance within
    the printed precision counts as none, as for the comparison. None where a neighbour's
    view is not in the record.

    The comparison's percentage is of the reference chart's largest value, and here there
    are three charts. "own" (the reading in use): each neighbour as the reference in turn,
    on its own largest value, as any two records are compared. "stage" (the other reading,
    tools/unstable.py): both on the scale of the chart at the stage itself, the one the
    departure is a percentage of; a chart with nothing in it at the stage is then taken on
    the larger neighbour's scale."""
    before, after = view_body(ref, stage - 1, key), view_body(ref, stage + 1, key)
    if before is None or after is None:
        return None
    lp, lq = parse_chart(before)[3], parse_chart(after)[3]
    scale = None
    if how == "stage":
        mine = parse_chart(ref.stage(stage, key))[3]
        scale = max((float(np.max(np.abs(a[:, 0]))) for a in mine if len(a)), default=0.0)
        if scale <= 1e-9:
            scale = max((float(np.max(np.abs(a[:, 0]))) for a in lp + lq if len(a)),
                        default=0.0)
    worst = 0.0
    for la, lb, body in ((lp, lq, before), (lq, lp, after)):
        d, s = lines_distance(la, lb, scale)
        if d > FLOOR_DIGITS * resolution(body)[0] and s > 1e-9:
            worst = max(worst, 100.0 * d / s)
    return float(worst)


def compare_views(ref, sub, ref_stage, sub_stage, t=None):
    """Every detail view of the reference's stage against the subject's. With t, the place
    of the reference's stage between its neighbours (place), each row also carries the
    reference's own departure from the blend of its neighbours' views there, where it can
    be tested (departure): "departure" in the chart's units, "departure_pct" relative to the
    chart's largest value, as "max_diff" and "max_diff_pct" are; and "apart_pct", how far
    the two neighbours' views lie from each other (apart)."""
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
        worst, scale = lines_distance(la, lb)
        rx, ry = resolution(ref.stage(ref_stage, key))
        rows.append({"view": key, "ref_max": scale, "max_diff": worst,
                     "floor": FLOOR_DIGITS * rx,
                     "max_diff_pct": float(100.0 * worst / scale) if scale > 1e-9 else 0.0,
                     "lines": [len(la), len(lb)]})
        dep = departure(ref, ref_stage, key, t)
        if dep is not None:
            rows[-1]["departure"] = dep
            rows[-1]["departure_pct"] = float(100.0 * dep / scale) if scale > 1e-9 else 0.0
            rows[-1]["apart_pct"] = apart(ref, ref_stage, key)
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
        key = keys[-1]
        a = _curve(ref, key)
        pk = float(np.max(np.abs(a[:, 1]))) if len(a) else 0.0
        xs = float(np.max(np.abs(a[:, 0]))) if len(a) else 0.0
        feats = feature_stages(ref, key)
        rp = int(ref.header.get("peak-stage", "0"))
        b = _curve(sub, key)
        limit = same_place_limit(ref)
        worst: dict[str, dict] = {}
        out["views_stages"] = []
        for rs in ref.stages():
            if rs >= len(a):
                continue
            x, y = float(a[rs, 0]), float(a[rs, 1])
            ss, how = match_stage(sub, key, rs, a, b, xs or 1.0, pk or 1.0, limit)
            if ss is None:
                continue
            at = {"ref_stage": rs, "sub_stage": ss, "matched_by": how,
                  "feature": feats.get(rs, ""),
                  "ref_x": x, "ref_y": y, "sub_x": float(b[ss, 0]), "sub_y": float(b[ss, 1])}
            # D54: the reference's own steadiness at this stage, where it has both neighbours
            t = place(a, rs, xs or 1.0, pk or 1.0)
            if t is not None:
                at["place"] = t
            rows = compare_views(ref, sub, rs, ss, t)
            at["views"] = rows
            out["views_stages"].append(at)
            if rs == rp:
                out["views_at"] = {k: at[k] for k in ("ref_stage", "sub_stage", "ref_x", "sub_x")}
            for row in rows:
                w = worst.get(row["view"])
                if (w is None or row.get("missing")
                        or (not w.get("missing") and row["max_diff_pct"] > w["max_diff_pct"])):
                    worst[row["view"]] = dict(row, ref_stage=rs)
        if worst:
            # each view's worst over the compared stages
            out["views"] = list(worst.values())
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
        f"{'ref x':>10}{'sub x':>10}{'curve max %':>13}{'mean %':>8}{'rising %':>10}"
        f"{'post %':>8}",
    ]
    for c in res["control"]:
        lines.append(
            f"{c['chart']:<14}{c['ref_peak_load']:>11.2f}{c['sub_peak_load']:>11.2f}"
            f"{c['peak_diff_pct']:>8.2f}{c['ref_peak_x']:>10.3f}{c['sub_peak_x']:>10.3f}"
            + (f"{c['curve_max_diff_pct']:>13.2f}{c['curve_mean_diff_pct']:>8.2f}"
               if "curve_max_diff_pct" in c else f"{'':>21}")
            + (f"{c['rising_pct']:>10.2f}" if "rising_pct" in c else f"{'':>10}")
            + (f"{c['post_peak_pct']:>8.2f}" if "post_peak_pct" in c else ""))
        if "shape_ref" in c:
            lines.append(f"{'':<14}shape {'same' if c['shape_same'] else 'DIFFERENT'}: "
                         f"reference {', '.join(c['shape_ref'])}; "
                         f"subject {', '.join(c['shape_sub'])}")
    for k in res["missing_control"]:
        lines.append(f"{k:<14} missing from the subject")
    for at in res.get("views_stages", []):
        lines += ["", f"detail views ({at['feature'] or 'stage'}): reference stage "
                      f"{at['ref_stage']} ({at['ref_x']:.3f}, {at['ref_y']:.1f}), subject stage "
                      f"{at['sub_stage']} ({at['sub_x']:.3f}, {at['sub_y']:.1f})",
                  f"{'view':<38}{'ref max':>12}{'max diff':>12}{'% of max':>10}"]
        for row in at["views"]:
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
