#!/usr/bin/env python3
"""Checks to run before pushing (and in CI): is the record of the work consistent with the work?

    python tools/check.py [--strict]

1. The acceptance tolerances in docs/acceptance.md parse.
2. docs/verification-results.md is current: no file under src/r2c has changed since the
   commit its run was made at. If it is stale, it says so (an error with --strict).
3. docs/verification-results.md has not been edited by hand: it still carries the generated
   marker and matches what tools/report.py writes from its own JSON.
   Also warns when r2c's curves are missing from the JSON (the dashboard needs them).
4. Every session log in docs/log has the sections the template asks for.
5. The end-of-phase review (docs/review.md) follows the results: the verdict and headings
   copied into docs/summary.md are what tools/review.py writes now (an error if not:
   rerun `python tools/review.py --summary`); warns where the measurements in Response's
   own state were made on another run, or a deviation has no cause (rerun
   tools/evidence.py, add the cause to docs/review/causes.toml).

Exit status 0 when all pass; 1 when one fails (stale results only with --strict).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import report  # noqa: E402

# Each entry: a heading, or a tuple of headings any one of which will do. Logs from
# 2026-11-22 on have "Questions for the owner" (numbers in docs/summary.md); earlier logs
# have "Open questions for the owner".
LOG_SECTIONS = ("## Goal", "## Done", "## Tried and dropped", "## Decisions",
                ("## Questions for the owner", "## Open questions for the owner"))


def git(*args) -> tuple[int, str]:
    p = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--strict", action="store_true", help="stale results are an error")
    a = ap.parse_args(argv)
    bad = 0

    acc_path = ROOT / "docs" / "acceptance.md"
    try:
        acc = report.read_acceptance(acc_path)
        set_ = {g: {k: v for k, v in t.items()} for g, t in acc.items() if t}
        print(f"ok    acceptance: {'tolerances set for ' + ', '.join(set_) if set_ else 'no tolerances set yet'}")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL  acceptance: {e}")
        bad += 1
        acc = {}

    md = ROOT / "docs" / "verification-results.md"
    js = md.with_suffix(".json")
    if not md.exists() or not js.exists():
        print("FAIL  verification results: docs/verification-results.md or .json missing")
        bad += 1
    else:
        data = json.loads(js.read_text())
        run = data["run"]
        commit = run.get("commit", "")
        text = md.read_text(encoding="utf-8")
        if not text.startswith(report.GENERATED):
            print("FAIL  verification results: the generated marker is gone (edited by hand?)")
            bad += 1
        elif text != report.render(data["results"], run, acc, "docs/acceptance.md"):
            print("FAIL  verification results: differ from what tools/report.py writes from "
                  "their JSON (edited by hand, or acceptance.md changed: rerun tools/report.py)")
            bad += 1
        else:
            print("ok    verification results: as generated")
        bare = [n for n, r in data["results"].items() if r.get("control") and "sub_curve" not in r]
        if bare:
            print(f"warn  verification results: r2c's curves missing for {len(bare)} case(s), so "
                  f"the dashboard draws Response's alone (rerun tools/report.py on a verify output)")
        rc, changed = git("diff", "--name-only", commit, "HEAD", "--", "src/r2c")
        if rc != 0:
            print(f"warn  verification results: cannot tell whether current (commit "
                  f"{commit[:12]} is not in this clone's history)")
        elif changed or run.get("dirty"):
            files = ", ".join(changed.split()) or "uncommitted changes at the time of the run"
            msg = (f"verification results are stale: run at {commit[:12]}, kernel changed "
                   f"since ({files})")
            if a.strict:
                print(f"FAIL  {msg}")
                bad += 1
            else:
                print(f"warn  {msg}")
        else:
            print(f"ok    verification results: current (run at {commit[:12]})")

    logs = sorted((ROOT / "docs" / "log").glob("2*.md"))
    for p in logs:
        text = p.read_text(encoding="utf-8")
        missing = [s if isinstance(s, str) else s[0] for s in LOG_SECTIONS
                   if not any(h in text for h in ((s,) if isinstance(s, str) else s))]
        if missing:
            print(f"FAIL  {p.relative_to(ROOT)}: missing {', '.join(missing)}")
            bad += 1
    if logs:
        print(f"ok    session logs: {len(logs)} checked" if not bad else
              f"      session logs: {len(logs)} checked")

    summary = ROOT / "docs" / "summary.md"
    if (ROOT / "docs" / "review" / "causes.toml").exists() and js.exists() and acc:
        import review
        data = json.loads(js.read_text())
        measured = review.load_measured()
        built = review.build(data["run"], data["results"], acc, review.load_causes(), measured)
        text = summary.read_text(encoding="utf-8")
        if review.BEGIN not in text:
            print("warn  review: docs/summary.md has no review block yet "
                  "(python tools/review.py --summary)")
        elif review.summary_block(built) not in text:
            print("FAIL  review: the verdict and headings in docs/summary.md are not what "
                  "tools/review.py writes now (rerun python tools/review.py --summary)")
            bad += 1
        else:
            print("ok    review: the summary's verdict and headings are as generated")
        loose = [e for e in built["entries"] if e["cause"].get("unclassified")]
        if measured.get("run") and measured["run"] != data["run"].get("commit", "")[:12]:
            print(f"warn  review: docs/review/measured.json was made on run {measured['run']}, "
                  "the results on another (rerun tools/evidence.py)")
        if loose:
            print(f"warn  review: {len(loose)} deviation(s) with no cause in "
                  "docs/review/causes.toml: " + ", ".join(e["worst"]["case"] for e in loose))
        elif not measured.get("run") or measured["run"] == data["run"].get("commit", "")[:12]:
            print(f"ok    review: {len(built['entries'])} entries, every deviation has a cause")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
