"""Where does each view miss of a shear case come from: the state reached, or a rule?

    python tools/sources.py VERIFY_OUT --archive ARCHIVE --inputs DIR [DIR ...]
                            [--only NAME ...] [--jobs N] [--flat PCT] [--by-case]

Answers the question step A-4 starts with (owner, 2026-11-24, D64): of the view checks
outside target on the cases with shear, how many trace to the state the two programs
reach (the shear profile iteration, or a state on a flat or slowly changing part of the
curve) and how many do not? For every view check outside target at an assessed stage
(tools/viewmisses.py's list: the last stage of a shear response and a check where
Response is unstable are left out) it puts r2c into Response's own state at that stage,
with the history of Response's stages before it (tools/diagnose.py states, on the full
capture in ARCHIVE), and compares the view again:

* **state**: inside target there. r2c's rules give Response's view from Response's
  state, so the miss is in the state r2c reached by its own stepping and iteration.
* **not the state**: outside there too. A rule, or a reading of the state from the
  charts that is too coarse for this view; not the path.
* **not computed**: a view that needs the driver (longitudinal bond).

Beside each: how the stage was matched (tools/compare.py: at the same place, or by the
feature), r2c's stage and its distance in load, and how flat Response's curve is there:
the spread of its load over the stage and the two before it, or the two after it,
whichever is smaller, as a share of its peak. "flat" is a spread under --flat (1 % if
not given: this tool's own threshold, for sorting only).

--by-case prints one line a case instead: how many of its misses are of each kind and of
each tier (the table of step A-6: which misses fall under the named limitation, D66).

Nothing is assessed and no target is read but the views target. The capture in ARCHIVE
must be the one the fixture was cut from (same number of stages); a case whose capture
differs is skipped and named.
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare as cmp  # noqa: E402
import diagnose  # noqa: E402
import report  # noqa: E402
import verify  # noqa: E402
from r2c import export, record  # noqa: E402
from viewmisses import has_shear  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def misses(res: dict, limit: float) -> dict[int, list]:
    """{Response's stage: [(view, difference %, the compared stage's entry)]} for the view
    checks outside target at the assessed stages of one case."""
    out: dict[int, list] = {}
    for vs in res.get("views_stages", []):
        if report.is_ending(vs):
            continue
        for v in vs["views"]:
            if v.get("missing") or v["max_diff"] <= v.get("floor", 0.0) \
                    or v["max_diff_pct"] <= limit or report.is_unstable(v, limit):
                continue
            out.setdefault(vs["ref_stage"], []).append((v["view"], v["max_diff_pct"], vs))
    return out


def in_own_states(capture: Path, input_path, stages) -> dict[int, dict[str, float]]:
    """r2c's difference on every view, in Response's own state at each of `stages`, with
    the history of the stages before carried (as tools/diagnose.py states does)."""
    ref = record.read(capture)
    su = diagnose._setup(ref, input_path)
    views = export.Views(su.section, su.units)
    out = {}
    for s in range(max(stages) + 1):
        e0, phi, prof, _resid = diagnose.strain_state(ref, su, s)
        st = diagnose.evaluate(su, e0, phi, prof)
        views.observe(st)
        if s > 0:
            su.analysis.commit(st.e0, st.phi)
            if prof is not None:
                su.analysis.commit_stirrups(st.detail)
        if s not in stages:
            continue
        made = views.charts(st, [k.split("/", 2)[2] for k in ref.sections
                                 if k.startswith(f"stage/{s}/")])
        sub = record.decode(record.encode(
            dict(ref.header), [(record.stage_section(s, k), b) for k, b in made.items()]))
        out[s] = {v["view"]: (None if v.get("missing") or v["view"] in diagnose.NOT_HERE
                              else 0.0 if v["max_diff"] <= v.get("floor", 0.0)
                              else v["max_diff_pct"])
                  for v in cmp.compare_views(ref, sub, s, s)}
    return out


def spread(ref, stage: int) -> float:
    """How flat Response's curve is at `stage`: the spread of its load over the stage and
    the two before it, or the stage and the two after it, whichever is smaller, in % of
    its peak, on the bottom control chart. One side is enough: a peak before a collapsed
    last stage is flat on the side it was reached from."""
    c = cmp._curve(ref, cmp.control_keys(ref)[-1])
    top = float(np.max(np.abs(c[:, 1])))
    if not top:
        return 0.0
    sides = []
    for lo, hi in ((stage - 2, stage), (stage, stage + 2)):
        lo, hi = max(lo, 0), min(hi, len(c) - 1)
        if hi > lo:
            y = np.abs(c[lo:hi + 1, 1])
            sides.append(100.0 * float(np.max(y) - np.min(y)) / top)
    return min(sides) if sides else 0.0


def one(args):
    name, res, archive, inputs, limit = args
    found = misses(res, limit)
    if not found:
        return name, [], None
    capture = Path(archive) / f"{name}.r2x.txt"
    if not capture.exists():
        return name, [], "no capture in the archive"
    ref = record.read(capture)
    if ref.header.get("stage-count") != res["ref"]["stage-count"]:
        return name, [], (f"the capture has {ref.header.get('stage-count')} stages, the "
                          f"fixture {res['ref']['stage-count']}")
    src = ref.header["input-name"]
    path = None
    if src.lower() not in verify.BUILT_IN:
        path = verify.find_input(src, ref.header.get("input-sha256"), inputs)
    try:
        own = in_own_states(capture, path, sorted(found))
    except Exception as e:  # a state r2c cannot evaluate: say so, classify nothing
        return name, [], f"r2c in Response's states: {type(e).__name__}: {e}"
    rows = []
    for s in sorted(found):
        for view, pct, vs in found[s]:
            rows.append(dict(
                stage=s, feature=vs["feature"], matched=vs.get("matched_by", ""),
                sub_stage=vs["sub_stage"], view=view, pct=pct, own=own[s].get(view),
                load_pct=100.0 * (vs["sub_y"] - vs["ref_y"]) / abs(vs["ref_y"])
                if vs["ref_y"] else 0.0,
                spread=spread(ref, s)))
    return name, rows, None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verify_out")
    ap.add_argument("--archive", required=True, help="folder of full captures")
    ap.add_argument("--inputs", nargs="+", default=[])
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--by-case", action="store_true",
                    help="one line a case: its misses by kind and by tier")
    ap.add_argument("--flat", type=float, default=1.0,
                    help="a spread of load under this (%% of the peak) is called flat")
    a = ap.parse_args(argv)
    results = json.loads((Path(a.verify_out) / "results.json").read_text())
    vacc = report.read_acceptance(ROOT / "docs" / "acceptance.md").get("views", {})
    limit = vacc.get("views_pct", 5.0)
    tier = {v: k for k in ("must", "should", "could") for v in vacc.get(k, [])}
    work = [(n, results[n], a.archive, a.inputs, limit) for n in sorted(results)
            if results[n].get("control") and has_shear(results[n])
            and (not a.only or n in a.only)]
    with ProcessPoolExecutor(max_workers=max(a.jobs, 1)) as ex:
        done = list(ex.map(one, work))
    count = {"state, flat": 0, "state, not flat": 0, "not the state": 0, "not computed": 0}
    skipped = []
    for name, rows, note in done:
        if note:
            skipped.append((name, note))
            continue
        last = None
        mine = {}
        for r in rows:
            if r["stage"] != last and not a.by_case:
                last = r["stage"]
                print(f"{name}: {r['feature']}, Response's stage {r['stage']} against r2c's "
                      f"{r['sub_stage']} ({r['matched'] or 'matched by feature'}; load "
                      f"{r['load_pct']:+.2f} %); spread of Response's load nearby "
                      f"{r['spread']:.2f} % of the peak")
            if r["own"] is None:
                what = "not computed"
            elif r["own"] <= limit:
                what = "state, flat" if r["spread"] < a.flat else "state, not flat"
            else:
                what = "not the state"
            count[what] += 1
            if a.by_case:
                last = r["stage"]
                for key in (what, tier.get(r["view"], "-")):
                    mine[key] = mine.get(key, 0) + 1
                continue
            own = "" if r["own"] is None else f"{r['own']:6.1f} % in Response's state"
            print(f"    {r['view']:30s} ({tier.get(r['view'], '-'):6s}) {r['pct']:6.1f} %  "
                  f"{own:32s} {what}")
        if a.by_case and mine:
            kinds = "; ".join(f"{mine[k]} {k}" for k in count if k in mine)
            tiers = ", ".join(f"{mine[k]} {k}" for k in ("must", "should", "could") if k in mine)
            print(f"{name}: {kinds} ({tiers})")
    for name, note in skipped:
        print(f"{name}: skipped ({note})")
    total = sum(count.values())
    print(f"{total} view checks outside at assessed stages of shear cases: "
          + "; ".join(f"{v} {k}" for k, v in count.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
