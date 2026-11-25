"""The "Review" page of the results site, as HTML: what tools/review.py assembled, drawn.

Not run by itself: `python tools/review.py --out review.html` calls render(). The page is
one self-contained file (no network, no script), in the colours of tools/dashboard.py.
Layout by the owner's specification (docs/review.md): the verdict grid, the trend and
what changed side under it, then the entries, each with its worst instance, one chart
(r2c over Response on the control curve, the stage marked), the developer's reason by
what it rests on (an inferred part is drawn to stand out), the independent assessment
as written, and the decision asked for.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
import dashboard  # noqa: E402
import review  # noqa: E402
from r2c import record  # noqa: E402

esc = html.escape

CSS = """
.viz-root{color-scheme:light;
 --surface:#fcfcfb;--surface-2:#f2f1ee;--border:#dddcd6;--grid:#e8e7e2;
 --ink:#0b0b0b;--ink-2:#52514e;--ink-3:#8a8984;
 --ref:#52514e;--sub:#2a78d6;--high:#eb6834;--tol:#e34948;
 --ok:#1e8a5a;--ok-bg:#e3f3ea;--mid:#9a6a00;--mid-bg:#fbf0d2;--bad:#c03332;--bad-bg:#fbe4e3;
 --inf-bg:#fff1e8;--t1:#2a78d6;--t2:#eb6834;--t3:#6b6a66}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;
 --surface:#1a1a19;--surface-2:#242423;--border:#3a3a38;--grid:#2e2e2c;
 --ink:#f0efec;--ink-2:#c3c2b7;--ink-3:#8a8984;
 --ref:#c3c2b7;--sub:#3987e5;--high:#d95926;--tol:#e66767;
 --ok:#5cc596;--ok-bg:#173327;--mid:#e0b455;--mid-bg:#3a2f12;--bad:#ee8281;--bad-bg:#401c1c;
 --inf-bg:#3a2417;--t1:#5598e7;--t2:#e8804f;--t3:#b0afa6}}
*{box-sizing:border-box}
body{margin:0;background:var(--surface)}
.viz-root{font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);
 background:var(--surface);max-width:1000px;margin:0 auto;padding:16px}
h1{font-size:21px;margin:0 0 4px}
h2{font-size:17px;margin:34px 0 6px}
h3{font-size:15px;margin:0 0 6px;line-height:1.35}
h4{font-size:13px;margin:14px 0 4px;color:var(--ink-2);font-weight:600;text-transform:uppercase;letter-spacing:.03em}
p{margin:6px 0}
a{color:var(--sub)}
.sub{color:var(--ink-2);font-size:13px;margin:0 0 10px}
.note{color:var(--ink-2);font-size:12.5px}
.warn{border-left:3px solid var(--high);padding:6px 10px;background:var(--surface-2);margin:10px 0;font-size:13px}
.scroll{overflow-x:auto}
table{border-collapse:collapse;font-variant-numeric:tabular-nums}
th,td{padding:5px 9px;text-align:left;vertical-align:top}
th{font-weight:600;font-size:12.5px;color:var(--ink-2)}
td.num,th.num{text-align:right}
.grid td,.grid th{border:1px solid var(--border)}
.grid td{min-width:190px}
.grid th.row{background:var(--surface-2);color:var(--ink);font-size:13.5px;vertical-align:middle}
.cell{font-weight:600;font-size:15px;display:block;margin-bottom:2px}
.met{background:var(--ok-bg)}.met .cell{color:var(--ok)}
.acc{background:var(--mid-bg)}.acc .cell{color:var(--mid)}
.not{background:var(--bad-bg)}.not .cell{color:var(--bad)}
.chip{display:inline-block;border:1px solid var(--border);border-radius:10px;padding:0 8px;
 margin:0 4px 4px 0;font-size:12px;white-space:nowrap;background:var(--surface-2)}
.chip.must{border-color:var(--ink);font-weight:600}
.chip.ok{color:var(--ok);border-color:var(--ok)}
.chip.mid{color:var(--mid);border-color:var(--mid)}
.chip.bad{color:var(--bad);border-color:var(--bad);font-weight:600}
.entry{border:1px solid var(--border);border-radius:8px;padding:12px 14px;margin:14px 0}
.entry.disagree{border-color:var(--bad);border-width:2px}
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:14px;align-items:start}
@media (max-width:760px){.two{grid-template-columns:1fr}}
dl{margin:0;display:grid;grid-template-columns:max-content 1fr;gap:2px 10px;font-size:13px}
dt{color:var(--ink-2)}dd{margin:0}
ul{margin:4px 0;padding-left:18px}
li{margin:3px 0}
.reason{list-style:none;padding:0;margin:0}
.reason li{padding:5px 8px;margin:4px 0;border-left:3px solid var(--border);font-size:13.5px}
.reason li.inferred{background:var(--inf-bg);border-left-color:var(--high)}
.basis{font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;margin-right:6px}
.inferred .basis{color:var(--high)}
.src{color:var(--ink-2);font-size:12px}
details{margin:6px 0}
summary{cursor:pointer;color:var(--ink-2);font-size:13px}
.md{font-size:13px;border-left:3px solid var(--border);padding:2px 10px;margin:6px 0;background:var(--surface-2)}
.md h5{font-size:13px;margin:10px 0 2px}
.md pre{white-space:pre-wrap;font-size:12px}
svg text{fill:var(--ink-2);font-size:11px}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:var(--ink-2);margin:4px 0}
.ln{display:inline-block;width:16px;height:0;border-top:2px solid;vertical-align:3px;margin-right:4px}
.ask{background:var(--surface-2);border-radius:6px;padding:8px 10px;margin-top:10px;font-size:13.5px}
code{font-size:12.5px}
"""


def md(text: str) -> str:
    """A plain rendering of the assessor's Markdown: headings, lists, paragraphs, bold,
    code. The words are not touched."""
    out, para, inlist, code = [], [], False, False

    def inline(s):
        s = esc(s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
        return re.sub(r"(?<![*\w])\*([^*\s][^*]*)\*(?!\w)", r"<i>\1</i>", s)

    def flush():
        nonlocal para, inlist
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para = []
        if inlist:
            out.append("</ul>")
            inlist = False

    for ln in text.splitlines():
        if ln.strip().startswith("```"):
            flush()
            out.append("</pre>" if code else "<pre>")
            code = not code
        elif code:
            out.append(esc(ln))
        elif not ln.strip():
            flush()
        elif ln.startswith("#"):
            flush()
            out.append("<h5>" + inline(ln.lstrip("#").strip()) + "</h5>")
        elif re.match(r"\s*([-*]|\d+\.)\s+", ln):
            if para:
                out.append("<p>" + inline(" ".join(para)) + "</p>")
                para = []
            if not inlist:
                out.append("<ul>")
                inlist = True
            out.append("<li>" + inline(re.sub(r"^\s*([-*]|\d+\.)\s+", "", ln)) + "</li>")
        elif inlist and ln.startswith(" "):
            out[-1] = out[-1][:-5] + " " + inline(ln.strip()) + "</li>"
        else:
            if inlist:
                out.append("</ul>")
                inlist = False
            para.append(ln.strip())
    flush()
    if code:
        out.append("</pre>")
    return "\n".join(out)


def fmt(x, d=1) -> str:
    return "–" if x is None else f"{x:.{d}f}"


# ---------------------------------------------------------------- the charts


def curve_chart(res: dict, fixture: Path, d: dict) -> str:
    """r2c over Response on the case's control chart, with the stage of the instance (a
    view check) or the features of both curves (a check on the curve) marked."""
    c = res["control"][-1]
    if not fixture.exists() or not res.get("sub_curve"):
        return '<p class="note">No curve to draw for this case.</p>'
    rec = record.read(fixture)
    xt, yt, ref = dashboard.curve(rec, c["chart"])
    sub = res["sub_curve"]
    w, h, m = 520, 300, {"l": 52, "r": 14, "t": 16, "b": 34}
    pts = ref + sub
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = min(0, *xs), max(0, *xs), min(0, *ys), max(0, *ys)
    x1 = x1 if x1 > x0 else x0 + 1
    y1 = y1 if y1 > y0 else y0 + 1
    pad = 0.08 * (y1 - y0)
    y1, y0 = y1 + pad, (y0 - pad if y0 < 0 else y0)

    def X(x):
        return m["l"] + (x - x0) / (x1 - x0) * (w - m["l"] - m["r"])

    def Y(y):
        return h - m["b"] - (y - y0) / (y1 - y0) * (h - m["t"] - m["b"])

    def path(p):
        return "".join(("L" if i else "M") + f"{X(a):.1f},{Y(b):.1f}" for i, (a, b) in enumerate(p))

    s = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="'
         f'{esc(yt)} against {esc(xt)}: r2c over Response-2000, {esc(d["case"])}">']
    s.append(f'<line x1="{m["l"]}" x2="{w - m["r"]}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="var(--grid)"/>'
             f'<line x1="{X(0):.1f}" x2="{X(0):.1f}" y1="{m["t"]}" y2="{h - m["b"]}" stroke="var(--grid)"/>')
    ends = [v for v in (max(ys), min(ys)) if abs(v) > 0.02 * (y1 - y0)]
    s.append("".join(f'<text x="{m["l"] - 5}" y="{Y(v) + 4:.1f}" text-anchor="end">{v:.4g}</text>'
                     for v in ends)
             + f'<text x="{m["l"] - 5}" y="{Y(0) + 4:.1f}" text-anchor="end">0</text>'
             f'<text x="{w - m["r"]}" y="{h - m["b"] + 14}" text-anchor="end">{x1:.4g}</text>'
             f'<text x="{m["l"]}" y="{h - m["b"] + 14}">{x0:.4g}</text>'
             f'<text x="{(m["l"] + w) / 2}" y="{h - 4}" text-anchor="middle">{esc(xt)}</text>'
             f'<text transform="translate(12,{(h - m["b"] + m["t"]) / 2}) rotate(-90)" '
             f'text-anchor="middle">{esc(yt)}</text>')
    s.append(f'<path d="{path(ref)}" fill="none" stroke="var(--ref)" stroke-width="2" stroke-linejoin="round"/>')
    s.append(f'<path d="{path(sub)}" fill="none" stroke="var(--sub)" stroke-width="2" '
             'stroke-linejoin="round" opacity="0.9"/>')

    def mark(x, y, col, text, up):
        dy = -12 if up else 20
        anchor = "end" if X(x) > w * 0.62 else "start"
        dx = -9 if anchor == "end" else 9
        return (f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="6" fill="none" stroke="{col}" '
                f'stroke-width="2"/><circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="1.8" fill="{col}"/>'
                f'<text x="{X(x) + dx:.1f}" y="{Y(y) + dy:.1f}" text-anchor="{anchor}" '
                f'style="fill:{col};font-weight:600">{esc(text)}</text>')

    if d["check"] == "view" and d["ref_xy"][0] is not None:
        (rx, ry), (sx, sy) = d["ref_xy"], d["sub_xy"]
        up = Y(ry) <= Y(sy)
        s.append(mark(rx, ry, "var(--ref)", f"Response's stage {d['stage']}", up))
        s.append(mark(sx, sy, "var(--sub)", f"r2c's stage {d['sub_stage']}", not up))
    else:
        a, b = np.array(ref, float), np.array(sub, float)
        pk = float(np.max(np.abs(a[:, 1]))) or 1.0
        sx = float(np.max(np.abs(a[:, 0]))) or 1.0
        for arr, col, up in ((a, "var(--ref)", True), (b, "var(--sub)", False)):
            for f, i in cmp.shape(arr, pk, sx):
                if f.startswith("ends") and i == int(np.argmax(np.abs(arr[:, 1]))):
                    continue
                x, y = arr[i]
                ty = Y(y) - 9 if up else Y(y) + 17
                s.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="3.5" fill="{col}" '
                         'stroke="var(--surface)" stroke-width="1.5"/>'
                         f'<text x="{X(x):.1f}" y="{ty:.1f}" text-anchor="middle" '
                         f'style="fill:{col}">{esc(f.replace("ends ", "ends: "))}</text>')
    s.append("</svg>")
    legend = ('<div class="legend"><span><span class="ln" style="border-color:var(--ref)">'
              '</span>Response-2000</span><span><span class="ln" style="border-color:var(--sub)">'
              "</span>r2c</span><span>"
              + ("rings: the two stages compared" if d["check"] == "view" else
                 "dots: the features of each curve as the measure reads them (Response's "
                 "above its curve, r2c's below)") + "</span></div>")
    return "".join(s) + legend


def trend_chart(rows: list[dict]) -> str:
    if len(rows) < 2:
        return '<p class="note">The trend needs the history of main (a full clone).</p>'
    w, h, m = 620, 230, {"l": 40, "r": 120, "t": 14, "b": 44}
    n = len(rows)

    def X(i):
        return m["l"] + i / (n - 1) * (w - m["l"] - m["r"])

    def Y(p):
        return h - m["b"] - (p - 40) / 60 * (h - m["t"] - m["b"])

    s = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px" role="img" '
         'aria-label="Cases inside each tier, as a share of the set, step by step">']
    for p in (40, 60, 80, 100):
        s.append(f'<line x1="{m["l"]}" x2="{w - m["r"]}" y1="{Y(p):.1f}" y2="{Y(p):.1f}" '
                 f'stroke="var(--grid)"/><text x="{m["l"] - 5}" y="{Y(p) + 4:.1f}" '
                 f'text-anchor="end">{p} %</text>')
    for i, r in enumerate(rows):
        s.append(f'<text x="{X(i):.1f}" y="{h - m["b"] + 15}" text-anchor="middle">{esc(r["step"])}</text>'
                 f'<text x="{X(i):.1f}" y="{h - m["b"] + 29}" text-anchor="middle">{r["cases"]} cases</text>')
    ends = []
    for t, col in (("must", "var(--t1)"), ("should", "var(--t2)"), ("could", "var(--t3)")):
        pts = [(X(i), Y(max(40, 100 * r["counts"][t][0] / max(r["counts"][t][1], 1))))
               for i, r in enumerate(rows)]
        s.append('<path d="' + "".join(("L" if i else "M") + f"{x:.1f},{y:.1f}"
                                         for i, (x, y) in enumerate(pts))
                 + f'" fill="none" stroke="{col}" stroke-width="2"/>')
        s += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{col}"/>' for x, y in pts]
        a, b = rows[-1]["counts"][t]
        ends.append([pts[-1][1], col, f"{review.TIER_NAME[t]} {a} of {b}"])
    ends.sort()
    for i in range(1, len(ends)):              # keep the end labels apart
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + 13)
    for y, col, text in ends:
        s.append(f'<text x="{w - m["r"] + 8}" y="{y + 4:.1f}" style="fill:{col};font-weight:600">'
                 f"{esc(text)}</text>")
    s.append("</svg>")
    head = "".join(f'<th class="num">{esc(r["step"])}</th>' for r in rows)
    body = "<tr><td>Cases in the set</td>" + "".join(
        f'<td class="num">{r["cases"]}</td>' for r in rows) + "</tr>"
    for t in review.TIERS[:3]:
        body += f"<tr><td>{review.TIER_NAME[t]}: cases inside</td>" + "".join(
            f'<td class="num">{r["counts"][t][0]} of {r["counts"][t][1]}</td>' for r in rows) + "</tr>"
    return ("".join(s) + '<details><summary>The same as a table</summary><div class="scroll">'
            f"<table><tr><th></th>{head}</tr>{body}</table></div></details>")


# ---------------------------------------------------------------- the parts


def grid_html(g: dict) -> str:
    cls = {"met": "met", "met with accepted deviations": "acc", "not met": "not"}
    out = ['<div class="scroll"><table class="grid"><tr><th></th>'
           + "".join(f"<th>{review.TIER_NAME[t]}</th>" for t in review.TIERS[:3]) + "</tr>"]
    for fam, title in review.FAMILY.items():
        out.append(f'<tr><th class="row">{title}</th>')
        for t in review.TIERS[:3]:
            n = g.get((fam, t))
            out.append("<td>–</td>" if not n else
                       f'<td class="{cls[n["verdict"]]}"><span class="cell">'
                       f'{n["verdict"].capitalize()}</span>{esc(review.cell_counts(n))}</td>')
        out.append("</tr>")
    return "".join(out) + "</table></div>"


def changes_html(data: dict) -> str:
    ch = data["changes"]
    if ch is None:
        return '<p class="note">No earlier run of record was found in this clone\'s history.</p>'

    def item(pair):
        a, b = pair
        d = b or a
        was = "–" if not a or a.get("pct") is None else f"{a['pct']:.1f} %"
        now = "gone" if not b else ("–" if b.get("pct") is None else f"{b['pct']:.1f} %")
        if d["check"] == "shape":
            was, now = ("same" if a and a["ok"] else "different"), ("same" if b and b["ok"] else "different")
        return (f"<li>{esc(d['case'])}: {esc(review.what(d))} "
                f"({review.TIER_NAME[d['tier']]}): {was} → {now}</li>")

    def by_case(pairs):
        n: dict[str, int] = {}
        for a, b in pairs:
            c = (b or a)["case"]
            n[c] = n.get(c, 0) + 1
        return ", ".join(f"{c} ({k})" for c, k in sorted(n.items(), key=lambda kv: -kv[1]))

    out = [f'<p class="sub">Counted from {esc(data["baseline"])}, with today\'s measure, on the '
           "cases in both runs. Only checks that changed side are listed.</p>"]
    out.append(f"<p><b>Went outside target: {len(ch['out'])}.</b></p>")
    if ch["out"]:
        out.append("<ul>" + "".join(item(p) for p in ch["out"]) + "</ul>")
    out.append(f"<p><b>Came inside target: {len(ch['in'])}</b>"
               + (f", on {esc(by_case(ch['in']))}." if ch["in"] else ".") + "</p>")
    if ch["in"]:
        out.append("<details><summary>Each of them</summary><ul>"
                   + "".join(item(p) for p in ch["in"]) + "</ul></details>")
    if ch["joined"]:
        devs = data["devs"]
        parts = []
        for c in ch["joined"]:
            k = sum(1 for d in devs if d["case"] == c and d["tier"] != "wont")
            parts.append(f"{esc(c)} ({k} check{'s' if k != 1 else ''} outside)" if k
                         else f"{esc(c)} (every check inside)")
        out.append(f"<p><b>Joined the set: {len(ch['joined'])}.</b> " + "; ".join(parts) + ".</p>")
    if ch["left"]:
        out.append("<p><b>Left the set:</b> " + esc(", ".join(ch["left"])) + ".</p>")
    return "".join(out)


def status_chips(e: dict) -> str:
    acc, pen = review.decided(e["instances"])
    st = review.status_of(e["instances"])
    out = []
    if acc:
        out.append(f'<span class="chip {"ok" if st == "accepted" else "mid"}">'
                   + ("accepted" if st == "accepted" else "accepted in part")
                   + f": {esc(', '.join(acc))}</span>")
    if pen:
        out.append(f'<span class="chip mid">no decision yet: {esc(", ".join(pen))}</span>')
    if not acc and not pen:
        out.append('<span class="chip bad">no decision</span>')
    return "".join(out)


def ind_chip(ind: dict) -> str:
    v = ind.get("verdict", "")
    if not ind:
        return '<span class="chip">independent assessment: not made</span>'
    cls = {"supports": "ok", "contradicts": "bad", "does not decide": "mid"}.get(v, "mid")
    words = {"supports": "supports the developer's reason",
             "contradicts": "contradicts the developer's reason",
             "does not decide": "the evidence does not decide it"}.get(v, "no verdict line found")
    return f'<span class="chip {cls}">independent assessment: {words}</span>'


def instance_facts(d: dict, res: dict) -> str:
    c = res["control"][-1]
    rows = [("Case", f"{esc(d['case'])}<br><span class='src'>{esc(dashboard.label(res['ref']))}</span>"),
            ("Check", f"{esc(review.what(d))} ({review.TIER_NAME[d['tier']]})"),
            ("Size", esc(review.size_text(d)))]
    if d["check"] == "view":
        own = d.get("own") or {}
        rows += [("Stages compared",
                  f"Response's {d['stage']} at ({d['ref_xy'][0]:g}, {d['ref_xy'][1]:g}); r2c's "
                  f"{d['sub_stage']} at ({d['sub_xy'][0]:g}, {d['sub_xy'][1]:g})"),
                 ("On the chart", "missing in r2c" if d.get("missing") else
                  f"largest difference {d['diff']:.3g}, where Response's chart reaches {d['ref_max']:g}")]
        if own.get("own") is not None:
            rows.append(("r2c in Response's own state", f"{own['own']:.1f} % (target {d['limit']:g} %)"))
        if "spread" in own:
            rows.append(("Response's load nearby", f"changes by {own['spread']:.2f} % of its peak"))
    elif d["check"] == "shape":
        rows += [("Response's curve", esc(", ".join(d["ref"]))),
                 ("r2c's curve", esc(", ".join(d["sub"])))]
    rows += [("Peak", f"Response {c['ref_peak_load']:g} at {c['ref_peak_x']:g}; r2c "
                      f"{c['sub_peak_load']:g} at {c['sub_peak_x']:g} ({c['peak_diff_pct']:+.2f} %)"),
             ("Stages", f"Response {res['ref']['stage-count']}, r2c {res['sub']['stage-count']}")]
    if d["check"] != "shape" and c.get("shape_ref"):
        rows.append(("How it ends", f"Response: {esc(c['shape_ref'][-1])}; r2c: {esc(c['shape_sub'][-1])}"))
    return "<dl>" + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows) + "</dl>"


def entry_html(e: dict, data: dict, ref_dir: Path) -> str:
    c, w, ind = e["cause"], e["worst"], e["independent"]
    res = data["results"][w["case"]]
    n, k = len(e["cases"]), len(e["instances"])
    disagree = ind.get("verdict") == "contradicts" or bool(c.get("disagreement"))
    out = [f'<section class="entry{" disagree" if disagree else ""}" id="{esc(e["id"])}">',
           f"<h3>{e['rank']}. {esc(c['name'])}</h3><div>",
           f'<span class="chip must">{review.TIER_NAME[e["tier"]]}</span>',
           f'<span class="chip">{esc(review.entry_size(e))}</span>',
           f'<span class="chip">{n} case{"s" if n != 1 else ""}, {k} check{"s" if k != 1 else ""}</span>',
           status_chips(e), ind_chip(ind), "</div>"]
    out.append('<div class="two"><div><h4>The worst instance</h4>' + instance_facts(w, res))
    more = review.others(e)
    if more:
        out.append(f"<h4>And {k - 1} more like this</h4><ul>"
                   + "".join(f"<li>{esc(x)}</li>" for x in more) + "</ul>")
    out.append("</div><div>" + curve_chart(res, ref_dir / f"{w['case']}.r2x.txt", w) + "</div></div>")
    out.append("<h4>The reason (the developer's)</h4>")
    if c.get("unclassified"):
        out.append('<p class="warn">No cause in docs/review/causes.toml matches these checks. '
                   "Not explained, not measured: run tools/evidence.py and add a cause.</p>")
    else:
        out.append('<ul class="reason">')
        for r in c.get("reason", []):
            src = (f"<span class='src'> · {esc(r['tool'])}</span>" if r.get("tool") else
                   f"<span class='src'> · the binary at <code>{esc(r['address'])}</code></span>"
                   if r.get("address") else
                   "<span class='src'> · not tested: question this one</span>"
                   if r["basis"] == "inferred" else "")
            out.append(f'<li class="{esc(r["basis"])}"><span class="basis">{esc(r["basis"])}</span>'
                       f"{esc(r['text'])}{src}</li>")
        out.append("</ul>")
    out.append("<h4>The independent assessment</h4>")
    if ind:
        out.append(f"<p>{ind_chip(ind)} Written by a separate agent that was given only this "
                   "entry's evidence file and docs/acceptance.md, and the developer's reason "
                   "only after it had written its own. Shown as written "
                   f'(<a href="{esc(ind["path"])}">the file</a>).</p>'
                   f'<details{" open" if ind.get("verdict") == "contradicts" else ""}><summary>Read it</summary>'
                   f'<div class="md">{md(ind["text"])}</div></details>')
    else:
        out.append('<p class="note">None has been made for this entry.</p>')
    if c.get("disagreement"):
        out.append('<ul class="reason"><li class="inferred"><span class="basis">Where it '
                   f"disagrees</span>{esc(c['disagreement'])}<span class='src'> · the "
                   "developer's account of the assessment above</span></li>"
                   + (f'<li><span class="basis">The developer, after it</span>{esc(c["after"])}</li>'
                      if c.get("after") else "") + "</ul>")
    acc, pen = review.decided(e["instances"])
    out.append('<div class="ask"><b>Status.</b> '
               + (f"Accepted by the owner: {esc(', '.join(acc))}. " if acc else
                  "No decision of the owner covers it yet. ")
               + (f"Put to the owner before and not answered: {esc(', '.join(pen))}. " if pen else ""))
    if c.get("ask"):
        out.append(f"<br><b>Asked now{' (' + esc(c['decision']) + ')' if c.get('decision') else ''}.</b> "
                   f"{esc(c['ask'])}<br><b>The developer suggests:</b> {esc(c.get('suggestion', '–'))}"
                   f"<br><b>The independent assessment suggests:</b> "
                   f"{esc(ind.get('suggestion') or '–')}")
    out.append("</div></section>")
    return "".join(out)


def render(data: dict, ref_dir: Path) -> str:
    run = data["run"]
    ents = data["entries"]
    when = (run.get("started") or "").replace("T", " ")[:16]
    H = ['<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width, initial-scale=1">'
         f"<title>r2c: end-of-phase review</title><style>{CSS}</style></head>"
         '<body><div class="viz-root">',
         "<h1>r2c against Response-2000: the review</h1>",
         f'<p class="sub">The run of record at <code>{esc(run.get("commit", "")[:12])}</code> '
         f"({esc(when)}), {sum(1 for r in data['results'].values() if r.get('control'))} cases · "
         'built to docs/review.md · <a href="./">the results, check by check</a></p>']
    if data["measured_run"] and data["measured_run"] != run.get("commit", "")[:12]:
        H.append('<div class="warn">The measurements in Response\'s own state '
                 f'(docs/review/measured.json) were made on run {esc(data["measured_run"])}, '
                 "not on this one: rerun tools/evidence.py. A check that cannot be placed by "
                 "them is listed as not classified.</div>")
    stale = dashboard.stale(run)
    if stale:
        H.append(f'<div class="warn">These results may be stale: {esc(stale)}.</div>')
    unc = [e for e in ents if e["cause"].get("unclassified")]
    if unc:
        H.append(f'<div class="warn">{len(unc)} entr{"y is" if len(unc) == 1 else "ies are"} '
                 "not classified by cause: " + esc(", ".join(e["worst"]["case"] for e in unc)) + ".</div>")

    H.append("<h2>1. The verdict</h2>"
             '<p class="sub">Did the phase do what it set out to do? Rows: the load families. '
             "Columns: the tiers of the exit criteria (docs/acceptance.md). A cell is <i>met</i> "
             "when every case is inside target on that tier; <i>met with accepted deviations</i> "
             "when every check outside has a decision of the owner that accepts it; <i>not "
             "met</i> when a check outside has none.</p>" + grid_html(data["grid"]))
    wo, wn = review.wont(data["checks"])
    H.append(f'<p class="note">Won\'t tier, not in the grid: how a shear response ends. {wo} of '
             f"{wn} shear cases are outside the post-peak target; reported, not chased.</p>")
    H.append("<h4>The trend over the steps of the phase</h4>"
             '<p class="sub">Cases inside each tier (every check of the tier inside target, '
             "nothing counted as accepted), as a share of the set at that step. Each point is "
             "the run of record a step left on main, counted with today's measure; the set grew "
             "from step to step, so a line can fall because harder cases joined.</p>"
             + trend_chart(data["trend"]))
    H.append("<h4>What changed side</h4>" + changes_html(data))

    dis = [e for e in ents if e["independent"].get("verdict") == "contradicts"
           or e["cause"].get("disagreement")]
    und = [e for e in ents if e["independent"].get("verdict") == "does not decide"
           and e not in dis]
    none = [e for e in ents if not e["independent"]]
    H.append("<h2>2. The deviations, worst first</h2>"
             f'<p class="sub">{len(data["devs"]) - wo} checks outside target in the Must, Should '
             f"and Could tiers, in {len(ents)} entries, one per cause. Ranked by tier, then by "
             "size (the deviation as a multiple of its target, after the printed-precision "
             "floor); a shape that differs has no size and comes first in its tier. Deviations "
             "the owner has accepted stay in the list: the review decides them again.</p>")
    if dis:
        H.append('<div class="warn"><b>Where the independent assessment contradicts the '
                 "developer's reason, in whole or in part</b> (raised whatever the rank):<ul>"
                 + "".join(f'<li><a href="#{esc(e["id"])}">{e["rank"]}. {esc(e["cause"]["name"])}</a>'
                           f': {esc(e["cause"].get("disagreement", ""))}</li>'
                           for e in dis) + "</ul></div>")
    if und or none:
        H.append('<p class="note">'
                 + (f"On {len(und)} more the assessment's verdict is that the evidence does "
                    "not decide the developer's reason: "
                    + ", ".join(f'<a href="#{esc(e["id"])}">{e["rank"]}</a>' for e in und) + ". "
                    if und else "")
                 + (f"No independent assessment yet on {len(none)}: "
                    + ", ".join(f'<a href="#{esc(e["id"])}">{e["rank"]}</a>' for e in none) + "."
                    if none else "") + "</p>")
    shown = ents[:review.CAP] + [e for e in ents[review.CAP:] if e in dis]
    for e in shown:
        H.append(entry_html(e, data, ref_dir))
    H.append(f'<p class="note"><b>Below the list.</b> {esc(review.below_cap(ents, data["checks"]))}</p>')
    H.append('<p class="note">Generated by tools/review.py from the run named at the top, '
             "docs/review/causes.toml (the developer's grouping and reasons), "
             "docs/review/measured.json (tools/evidence.py) and docs/review/independent/ (the "
             "assessments, as written). The review changes no target, measure or decision; the "
             "owner's answers are recorded in docs/summary.md.</p></div></body></html>")
    return "\n".join(H)
