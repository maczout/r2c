#!/usr/bin/env python3
"""The end-of-phase review: the verdict, and the deviations outside target by cause.

    python tools/review.py [RESULTS] [--out review.html] [--summary [docs/summary.md]]
                           [--list]

Answers the question the owner's specification asks (docs/review.md): did the phase do what
it set out to do, and what is outside target, worst first, one entry per cause? Built from
the run of record (RESULTS: the combined JSON tools/report.py writes, or a verify output
folder; default docs/verification-results.json), docs/acceptance.md and:

* docs/review/causes.toml: the developer's grouping of the deviations by cause, with the
  reason for each marked measured, read or inferred, the owner's decisions that accepted
  it, and what is asked now;
* docs/review/measured.json: r2c's difference on each view outside target when it is put
  into Response's own state (written by tools/evidence.py; a cause may be told by it);
* docs/review/independent/ID.md: the independent assessment of each cause, as the
  assessing agent wrote it. Read, shown and linked; never edited here.

The page has the verdict grid (load families by tiers), the trend of the tier counts over
the steps of the phase (each step's run of record, read from git at the merge of its
branch and counted with today's measure), the checks that changed side since the last
review, and the entries, ranked and capped at 20, with one line below for what is not
itemised and for the Won't tier.

Ranking (docs/review.md): by tier, then by size, the deviation as a multiple of its target
after the printed-precision floor. A shape that differs has no size: within its tier such
an entry comes first, the entry with more cases before the one with fewer (the developer's
choice; docs/summary.md, D92).

--list prints the entries as text. --summary writes the verdict and the list of headings
into docs/summary.md between its two "review" markers (tools/check.py holds it current).
Nothing is assessed here that tools/report.py does not assess: inside and outside are its
own, and no target, measure or decision is changed.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import report  # noqa: E402

REVIEW = ROOT / "docs" / "review"
TIERS = ("must", "should", "could", "wont")
TIER_NAME = {"must": "Must", "should": "Should", "could": "Could", "wont": "Won't"}
FAMILY = {"flexure": "Moment and axial load", "shear": "Shear"}
CAP = 20
BEGIN, END = "<!-- review:begin -->", "<!-- review:end -->"
STEP = re.compile(r"Merge pull request #\d+ from [^/\s]+/dev/a-(\d+[a-z]?)\b")
VERDICTS = ("supports", "contradicts", "does not decide")


# ---------------------------------------------------------------- the deviations


def load_results(path: Path) -> tuple[dict, dict]:
    if path.is_dir():
        return (json.loads((path / "run.json").read_text()),
                json.loads((path / "results.json").read_text()))
    data = json.loads(path.read_text())
    return data["run"], data["results"]


def key_of(d: dict) -> str:
    return "|".join(str(d.get(k) if d.get(k) is not None else "")
                    for k in ("case", "check", "view", "stage"))


def case_checks(name: str, res: dict, acc: dict) -> list[dict]:
    """Every assessed check of one case, inside or outside: check ("peak", "rising",
    "post-peak", "shape", "view"), tier, ok, and for a number its size as a multiple of its
    target (after the printed-precision floor; a shape has none)."""
    g = report.group(res["ref"])
    out = []
    c = res["control"][-1]
    fl = c.get("floor_pct", 0.0)
    for k, (v, lim, ok) in report.assess(res, acc).items():
        if k.startswith("views") or ok is None:
            continue
        check = {"curve": "rising", "post_peak": "post-peak"}.get(k, k)
        tier = "must" if k != "post_peak" else ("should" if g == "flexure" else "wont")
        d = {"case": name, "group": g, "check": check, "tier": tier, "ok": bool(ok)}
        if k == "shape":
            d.update(size=None, ref=c.get("shape_ref"), sub=c.get("shape_sub"))
        elif k == "peak":
            d.update(pct=v, limit=lim, size=abs(v) / lim,
                     ref=c["ref_peak_load"], sub=c["sub_peak_load"])
        else:
            d.update(pct=v, limit=lim, size=v / max(lim, fl))
        out.append(d)
    lim = report.views_limit(acc)
    stages = {s["ref_stage"]: s for s in res.get("views_stages", [])}
    for ch in report.stage_checks(res, acc):
        if ch["state"] == "unstable":
            continue
        st = stages[ch["ref_stage"]]
        row = next(r for r in st["views"] if r["view"] == ch["view"])
        tier = {"views": "must", "views_should": "should", "views_could": "could"}[ch["tier"]]
        out.append({"case": name, "group": g, "check": "view", "view": ch["view"],
                    "stage": ch["ref_stage"], "feature": ch["feature"], "tier": tier,
                    "ok": ch["state"] == "inside", "pct": ch["pct"], "limit": lim,
                    "size": None if ch["pct"] is None else ch["pct"] / lim,
                    "missing": ch["pct"] is None,
                    "ref_max": row.get("ref_max"), "diff": row.get("max_diff"),
                    "sub_stage": st.get("sub_stage"), "matched": st.get("matched_by", ""),
                    "ref_xy": [st.get("ref_x"), st.get("ref_y")],
                    "sub_xy": [st.get("sub_x"), st.get("sub_y")]})
    for d in out:
        d["key"] = key_of(d)
    return out


def all_checks(results: dict, acc: dict) -> list[dict]:
    return [d for n in sorted(results) if results[n].get("control")
            for d in case_checks(n, results[n], acc)]


# ---------------------------------------------------------------- the causes


def load_causes(path: Path = REVIEW / "causes.toml") -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8")) if path.exists() else {"cause": []}


def load_measured(path: Path = REVIEW / "measured.json") -> dict:
    return json.loads(path.read_text()) if path.exists() else {"checks": {}}


def _matches(m: dict, d: dict, measured: dict) -> bool:
    if d["case"] not in m.get("cases", []) or d["check"] not in m.get("checks", []):
        return False
    if d["check"] == "view":
        if "views" in m and d["view"] not in m["views"]:
            return False
        if "features" in m and not any(d["feature"].startswith(f) for f in m["features"]):
            return False
        if "own_state" in m:
            own = (measured.get("checks", {}).get(d["key"]) or {}).get("own")
            if own is None or (own <= d["limit"]) != (m["own_state"] == "inside"):
                return False
    return True


def classify(devs: list[dict], causes: dict, measured: dict) -> None:
    """Give each deviation its cause (the first match in the causes file) with the owner's
    decisions that accepted it or are pending on it; none where no cause matches."""
    for d in devs:
        d["cause"], d["accepted"], d["pending"] = None, [], []
        d["own"] = (measured.get("checks", {}).get(d["key"]) or {})
        for c in causes.get("cause", []):
            hit = next((m for m in c.get("match", []) if _matches(m, d, measured)), None)
            if hit:
                d["cause"] = c["id"]
                d["accepted"], d["pending"] = hit.get("accepted", []), hit.get("pending", [])
                break


def _rank(d: dict):
    """Worst first within a tier: a shape (no size), then by size."""
    return (TIERS.index(d["tier"]), 0 if d["size"] is None and not d.get("missing") else 1,
            -(d["size"] if d["size"] is not None else 1e9))


def entries(devs: list[dict], causes: dict) -> list[dict]:
    """One entry per cause, ranked: by tier, a shape first (more cases first), then by
    size. A deviation with no cause is an entry of its own case. The Won't tier is not
    itemised."""
    by: dict[str, list] = {}
    for d in devs:
        if d["tier"] == "wont" and not d["cause"]:
            continue
        by.setdefault(d["cause"] or f"unclassified:{d['case']}", []).append(d)
    known = {c["id"]: c for c in causes.get("cause", [])}
    out = []
    for cid, ds in by.items():
        ds.sort(key=_rank)
        w = ds[0]
        sizes = [d["size"] for d in ds if d["tier"] == w["tier"] and d["size"] is not None]
        nums = [d["size"] for d in ds if d["size"] is not None]
        c = known.get(cid, {"id": cid, "name": f"Not classified: {w['case']}",
                            "reason": [], "unclassified": True})
        out.append({"id": cid, "cause": c, "tier": w["tier"], "worst": w, "instances": ds,
                    "shape": w["size"] is None and not w.get("missing"),
                    "size": max(sizes) if sizes else None,
                    "largest": max(nums) if nums else None,
                    "cases": sorted({d["case"] for d in ds})})
    out.sort(key=lambda e: (TIERS.index(e["tier"]), 0 if e["shape"] else 1,
                            -len(e["cases"]) if e["shape"] else 0,
                            -(e["size"] or e["largest"] or 0.0), e["id"]))
    for i, e in enumerate(out, 1):
        e["rank"] = i
    return out


def status_of(ds: list[dict]) -> str:
    """"accepted" (every check has the owner's decision), "part" or "open"."""
    acc = [bool(d["accepted"]) for d in ds]
    return "accepted" if all(acc) else "part" if any(acc) else "open"


# ---------------------------------------------------------------- the verdict


def grid(checks: list[dict]) -> dict:
    """{(family, tier): {"cases", "inside", "accepted", "open", "verdict"}}: a case is
    inside a tier when none of its checks of that tier is outside; outside with every
    such check accepted by the owner it counts as an accepted deviation."""
    cell: dict[tuple, dict] = {}
    per: dict[tuple, list] = {}
    for d in checks:
        if d["tier"] != "wont":
            per.setdefault((d["group"], d["tier"], d["case"]), []).append(d)
    for (g, t, _case), ds in per.items():
        n = cell.setdefault((g, t), {"cases": 0, "inside": 0, "accepted": 0, "open": 0})
        n["cases"] += 1
        out = [d for d in ds if not d["ok"]]
        if not out:
            n["inside"] += 1
        elif all(d.get("accepted") for d in out):
            n["accepted"] += 1
        else:
            n["open"] += 1
    for n in cell.values():
        n["verdict"] = ("not met" if n["open"] else
                        "met with accepted deviations" if n["accepted"] else "met")
    return cell


def tier_counts(checks: list[dict]) -> dict:
    """{tier: (cases inside, cases)} over both families, nothing accepted counted in."""
    per: dict[tuple, bool] = {}
    for d in checks:
        if d["tier"] != "wont":
            k = (d["tier"], d["case"])
            per[k] = per.get(k, True) and d["ok"]
    return {t: (sum(v for (tt, _c), v in per.items() if tt == t),
                sum(1 for (tt, _c) in per if tt == t)) for t in TIERS[:3]}


def wont(checks: list[dict]) -> tuple[int, int]:
    ds = [d for d in checks if d["tier"] == "wont"]
    return sum(1 for d in ds if not d["ok"]), len(ds)


# ---------------------------------------------------------------- the history, from git


def git(*args) -> str:
    p = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else ""


def results_at(ref: str):
    text = git("show", f"{ref}:docs/verification-results.json")
    try:
        data = json.loads(text)
        return data["run"], data["results"]
    except (ValueError, KeyError):
        return None


def steps() -> list[tuple[str, dict, dict]]:
    """(step, run, results) at the merge of each step's branch into this history, oldest
    first: the run of record the step left. A step merged more than once counts at its last
    merge."""
    seen: dict[str, str] = {}
    for ln in git("log", "--merges", "--first-parent", "--format=%H\t%s", "HEAD").splitlines():
        commit, _, subject = ln.partition("\t")
        m = STEP.search(subject)
        if m and "A-" + m.group(1) not in seen:
            seen["A-" + m.group(1)] = commit
    out = []
    for label, commit in reversed(seen.items()):
        got = results_at(commit)
        if got:
            out.append((label, *got))
    return out


def trend(now_run: dict, now: dict, acc: dict) -> list[dict]:
    rows = []
    hist = steps()
    for label, run, res in hist:
        rows.append({"step": label, "commit": run.get("commit", ""),
                     "counts": tier_counts(all_checks(res, acc)),
                     "cases": sum(1 for r in res.values() if r.get("control"))})
    if not rows or rows[-1]["commit"] != now_run.get("commit", ""):
        rows.append({"step": "now", "commit": now_run.get("commit", ""),
                     "counts": tier_counts(all_checks(now, acc)),
                     "cases": sum(1 for r in now.values() if r.get("control"))})
    return rows


def baseline(now_run: dict, causes: dict):
    """(what it is, results) of the run "what changed" is counted from: the run of record
    at the last review held (the ref named in the causes file), or, before any review, the
    run of record of the step before the last."""
    ref = causes.get("last_review", "")
    if ref:
        got = results_at(ref)
        if got:
            return f"the last review ({ref})", got[1]
    older = [(s, res) for s, run, res in steps() if run.get("commit") != now_run.get("commit")]
    if older:
        return f"step {older[-1][0]} (no review has been held before this one)", older[-1][1]
    return "", None


def changes(before: dict, now: dict, acc: dict) -> dict:
    """Checks that changed side on the cases in both runs, and the cases that joined."""
    old = {d["key"]: d for d in all_checks(before, acc)}
    new = {d["key"]: d for d in all_checks(now, acc)}
    both = set(before) & set(now)
    out = {"in": [], "out": [], "joined": sorted(set(now) - set(before)),
           "left": sorted(set(before) - set(now))}
    for k in sorted(set(old) | set(new)):
        a, b = old.get(k), new.get(k)
        d = b or a
        if d["case"] not in both or d["tier"] == "wont":
            continue
        was = a["ok"] if a else True
        isnow = b["ok"] if b else True
        if was and not isnow:
            out["out"].append((a, b))
        elif isnow and not was:
            out["in"].append((a, b))
    return out


# ---------------------------------------------------------------- the independent assessment


def independent(cid: str) -> dict:
    """The assessing agent's file for a cause: its text as written, and the two lines it
    was asked to end with ("Verdict: ..." on the developer's reason, "Suggestion: ...")."""
    p = REVIEW / "independent" / f"{cid}.md"
    if not p.exists():
        return {}
    text = p.read_text(encoding="utf-8")
    v = re.findall(r"^\**Verdict:?\**:?\s*\**\s*(supports|contradicts|does not decide)",
                   text, re.M | re.I)
    s = re.findall(r"^\**Suggestion:?\**:?\s*(.+)$", text, re.M)
    return {"text": text, "verdict": v[-1].lower() if v else "",
            "suggestion": s[-1].strip().strip("*").strip() if s else "",
            "path": f"review/independent/{cid}.md"}


# ---------------------------------------------------------------- words


def plain(view: str) -> str:
    return view.replace("_", " ")


def what(d: dict) -> str:
    if d["check"] == "view":
        return f"{plain(d['view'])} at Response's stage {d['stage']} ({d['feature']})"
    return {"rising": "rising branch", "post-peak": "post-peak"}.get(d["check"], d["check"])


def size_text(d: dict) -> str:
    if d.get("missing"):
        return "chart missing"
    if d["size"] is None:
        return "shape differs"
    return f"{d['size']:.1f}× target ({d['pct']:.1f} % on {d['limit']:g} %)"


def entry_size(e: dict) -> str:
    if e["shape"]:
        extra = f"; views up to {e['largest']:.1f}× target" if e["largest"] else ""
        return "shape differs" + extra
    return f"{e['size']:.1f}× target" if e["size"] is not None else "chart missing"


def heading(e: dict, ind: dict | None = None) -> str:
    n, k = len(e["cases"]), len(e["instances"])
    s = (f"{e['cause']['name']} · {TIER_NAME[e['tier']]} · {entry_size(e)} · "
         f"{n} case{'s' if n != 1 else ''}, {k} check{'s' if k != 1 else ''}")
    if ind and ind.get("verdict") == "contradicts":
        s += " · the independent assessment disagrees"
    elif e["cause"].get("disagreement"):
        s += " · the independent assessment disagrees in part"
    return s


def decided(ds: list[dict]) -> tuple[list[str], list[str]]:
    acc = sorted({x for d in ds for x in d["accepted"]}, key=_dnum)
    pen = sorted({x for d in ds for x in d["pending"]}, key=_dnum)
    return acc, pen


def _dnum(s: str):
    m = re.search(r"\d+", s)
    return (s[0], int(m.group()) if m else 0)


def others(e: dict) -> list[str]:
    """"And N more like this": the other instances by tier, with cases and range."""
    out = []
    rest = e["instances"][1:]
    for t in TIERS:
        ds = [d for d in rest if d["tier"] == t]
        if not ds:
            continue
        nums = [d["size"] for d in ds if d["size"] is not None]
        cases = sorted({d["case"] for d in ds})
        rng = (f", {min(nums):.1f}× to {max(nums):.1f}× target" if len(nums) > 1 else
               f", {nums[0]:.1f}× target" if nums else "")
        shapes = sum(1 for d in ds if d["size"] is None and not d.get("missing"))
        out.append(f"{TIER_NAME[t]}: {len(ds)} check{'s' if len(ds) != 1 else ''}"
                   + (f" ({shapes} of them a shape)" if shapes else "") + rng
                   + f", on {len(cases)} case{'s' if len(cases) != 1 else ''}: "
                   + ", ".join(cases))
    return out


def below_cap(ents: list[dict], checks: list[dict]) -> str:
    rest = ents[CAP:]
    parts = []
    for t in TIERS[:3]:
        es = [e for e in rest if e["tier"] == t]
        if es:
            parts.append(f"{TIER_NAME[t]}: " + "; ".join(
                f"{e['cause']['name']} ({len(e['instances'])})" for e in es))
    wo, wn = wont(checks)
    line = ("Not itemised above: " + (" · ".join(parts) if parts else "nothing; every "
            "deviation in the Must, Should and Could tiers is in an entry") + ". ")
    return line + (f"Won't tier (how a shear response ends): {wo} of {wn} shear cases are "
                   "outside the post-peak target; not chased, not itemised.")


# ---------------------------------------------------------------- assembling


def build(run: dict, results: dict, acc: dict, causes: dict, measured: dict) -> dict:
    checks = all_checks(results, acc)
    devs = [d for d in checks if not d["ok"]]
    classify(devs, causes, measured)
    ents = entries(devs, causes)
    for e in ents:
        e["independent"] = independent(e["id"])
    what_base, before = baseline(run, causes)
    return {"run": run, "results": results, "checks": checks, "devs": devs, "entries": ents,
            "grid": grid(checks), "trend": trend(run, results, acc),
            "baseline": what_base,
            "changes": changes(before, results, acc) if before else None,
            "measured_run": measured.get("run", ""), "acc": acc}


# ---------------------------------------------------------------- text outputs


def grid_markdown(g: dict) -> list[str]:
    out = ["| | Must | Should | Could |", "|---|---|---|---|"]
    for fam, title in FAMILY.items():
        cells = []
        for t in TIERS[:3]:
            n = g.get((fam, t))
            cells.append("–" if not n else f"**{n['verdict']}**: {cell_counts(n)}")
        out.append(f"| {title} | " + " | ".join(cells) + " |")
    return out


def cell_counts(n: dict) -> str:
    s = f"{n['inside']} of {n['cases']} cases inside"
    if n["accepted"]:
        s += f", {n['accepted']} with accepted deviations"
    if n["open"]:
        s += f", {n['open']} with a deviation not yet decided"
    return s


def summary_block(data: dict) -> str:
    run = data["run"]
    out = [BEGIN,
           "<!-- Generated by tools/review.py --summary. Do not edit: rerun it. -->", "",
           f"Run of record at `{run.get('commit', '')[:12]}`; the page is \"Review\" on the "
           "results site. A cell is *met* when every case is inside target on the tier, *met "
           "with accepted deviations* when every check outside has the owner's decision, "
           "*not met* otherwise.", ""]
    out += grid_markdown(data["grid"])
    out += ["", below_cap(data["entries"], data["checks"]), "",
            "The entries, worst first (one per cause; the decision asked for each is in the "
            "table \"The end-of-phase review\" under Decisions):", ""]
    for e in data["entries"][:CAP]:
        acc, pen = decided(e["instances"])
        st = ("accepted: " + ", ".join(acc) if acc else "no decision yet")
        if pen:
            st += "; pending: " + ", ".join(pen)
        ask = e["cause"].get("decision", "")
        out.append(f"{e['rank']}. {heading(e, e['independent'])} ({st}"
                   + (f"; asked now: {ask}" if ask else "") + ")")
    out += ["", END]
    return "\n".join(out)


def write_summary(path: Path, block: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit(f"{path}: no review markers ({BEGIN} … {END})")
    new = text[: text.index(BEGIN)] + block + text[text.index(END) + len(END):]
    if new != text:
        path.write_text(new, encoding="utf-8")
    return new != text


def listing(data: dict) -> str:
    out = []
    for fam, title in FAMILY.items():
        for t in TIERS[:3]:
            n = data["grid"].get((fam, t))
            if n:
                out.append(f"{title}, {TIER_NAME[t]}: {n['verdict']} ({cell_counts(n)})")
    out.append("")
    for e in data["entries"]:
        ind = e["independent"]
        out.append(f"{e['rank']:2d}. [{e['id']}] {heading(e, ind)}")
        w = e["worst"]
        out.append(f"      worst: {w['case']}, {what(w)}: {size_text(w)}")
        for ln in others(e):
            out.append(f"      more: {ln}")
        acc, pen = decided(e["instances"])
        out.append(f"      accepted by: {', '.join(acc) or '-'}; pending: "
                   f"{', '.join(pen) or '-'}; independent: {ind.get('verdict') or '-'}")
    out += ["", below_cap(data["entries"], data["checks"])]
    return "\n".join(out)


# ---------------------------------------------------------------- the page


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results", nargs="?",
                    default=str(ROOT / "docs" / "verification-results.json"))
    ap.add_argument("--reference", default=str(ROOT / "tests" / "oracle"))
    ap.add_argument("--acceptance", default=str(ROOT / "docs" / "acceptance.md"))
    ap.add_argument("--out", default="review.html")
    ap.add_argument("--list", action="store_true", help="print the entries, write no page")
    ap.add_argument("--summary", nargs="?", const=str(ROOT / "docs" / "summary.md"),
                    help="write the verdict and headings into the owner's summary")
    a = ap.parse_args(argv)
    run, results = load_results(Path(a.results))
    acc = report.read_acceptance(Path(a.acceptance))
    data = build(run, results, acc, load_causes(), load_measured())
    if a.list:
        print(listing(data))
        return 0
    if a.summary:
        changed = write_summary(Path(a.summary), summary_block(data))
        print(f"{a.summary}: review block " + ("written" if changed else "already current"))
        return 0
    import review_page
    Path(a.out).write_text(review_page.render(data, Path(a.reference)), encoding="utf-8")
    n = sum(1 for e in data["entries"] if e["cause"].get("unclassified"))
    print(f"wrote {a.out}: {len(data['entries'])} entries from {len(data['devs'])} "
          f"deviations" + (f"; {n} not classified" if n else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
