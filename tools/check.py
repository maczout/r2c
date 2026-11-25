#!/usr/bin/env python3
"""Checks to run before pushing (and in CI): does the record follow the brief?

    python tools/check.py [--strict]

1. The brief is in place (docs/brief.md) and the targets in docs/measures.md parse.
2. docs/verification-results.md is as generated (it matches what tools/report.py writes
   from its own JSON) and current: no file under src/r2c has changed since the commit its
   run was made at. Stale results are a warning (an error with --strict).
3. docs/summary.md is the one page of the brief: its four parts, within the limits on
   length and on the number of items, and its totals block is what tools/heldout.py writes
   from heldout/totals.json.
4. The held-out set is frozen and nothing of it per case is committed: the manifest parses
   and is the one that was frozen, heldout/totals.json holds totals only, and no tracked
   file is a capture, a result or a fixture of a held-out case.
5. Each log in docs/log has the template's sections, among them whether the held-out rule
   was kept.
6. The living record does not use the numbered decisions of the earlier record, and the
   known deviations are not numbered.
7. Nothing that must stay out is tracked: Response's own files, sample inputs, decompiler
   output.

Exit status 0 when all pass; 1 when one fails (stale results only with --strict).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import report  # noqa: E402

LOG_SECTIONS = ("## Goal", "## Done", "## Tried and dropped", "## Held-out rule",
                "## Evidence")
SUMMARY_PARTS = ("## Held-out totals", "## What changed", "## Needed from the owner",
                 "## Top known deviations")
# one page: lines and characters at most (the totals tables are in the count)
SUMMARY_LINES, SUMMARY_CHARS = 70, 6000
# at most this many list items under a part of the summary
SUMMARY_ITEMS = {"## What changed": 3, "## Needed from the owner": 3,
                 "## Top known deviations": 5}
# the numbering of the earlier record (C2, D12, ...), in the files that are kept current
OLD_NUMBER = re.compile(r"(?<![\w/-])[CD]\d{1,3}(?![\w.])")
LIVING = ("CLAUDE.md", "README.md", "docs/summary.md", "docs/status.md",
          "docs/deviations.md", "docs/measures.md", "heldout/README.md")
KEPT_OUT = re.compile(r"(\.rsp|\.exe|\.dll|/shape\.dat|/rebar\.dat|\.gpr|\.rep)$", re.I)
DECOMPILED = re.compile(r"FUN_00[0-9a-f]{6}|\bundefined[1248]\b")


def git(*args) -> tuple[int, str]:
    p = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def parts(text: str) -> dict[str, list[str]]:
    """The lines under each "## " heading."""
    out: dict[str, list[str]] = {}
    cur = None
    for ln in text.splitlines():
        if ln.startswith("## "):
            cur = ln.strip()
            out[cur] = []
        elif cur:
            out[cur].append(ln)
    return out


def items(lines: list[str]) -> int:
    return sum(1 for ln in lines if re.match(r"(- |\* |\d+\. )", ln))


def check_summary(say) -> None:
    try:
        import heldout
    except ImportError:
        say("FAIL", "tools/heldout.py is missing (the held-out set's builder and scorer)")
        return
    p = ROOT / "docs" / "summary.md"
    text = p.read_text(encoding="utf-8")
    n = len(text.splitlines())
    if n > SUMMARY_LINES or len(text) > SUMMARY_CHARS:
        say("FAIL", f"summary: {n} lines, {len(text)} characters; one page is at most "
                    f"{SUMMARY_LINES} lines and {SUMMARY_CHARS} characters")
    got = parts(text)
    missing = [h for h in SUMMARY_PARTS if h not in got]
    if missing:
        say("FAIL", "summary: missing " + ", ".join(missing))
    for h, most in SUMMARY_ITEMS.items():
        if h in got and items(got[h]) > most:
            say("FAIL", f"summary: {items(got[h])} items under \"{h[3:]}\", at most {most}")
    totals = heldout.read_totals()
    if totals["runs"] and heldout.summary_block(totals) not in text:
        say("FAIL", "summary: the held-out totals are not what tools/heldout.py writes from "
                    "heldout/totals.json (rerun python tools/heldout.py summary)")
    elif not missing:
        say("ok", f"summary: one page ({n} lines), its four parts, totals as generated")


def check_heldout(say, tracked: list[str]) -> None:
    try:
        import heldout
    except ImportError:
        return
    mp = ROOT / "heldout" / "manifest.json"
    if not mp.exists():
        say("FAIL", "held-out: heldout/manifest.json is missing (the set is built before "
                    "any kernel work: python tools/heldout.py build)")
        return
    man = json.loads(mp.read_text())
    cases = man["cases"]
    bad = [c["name"] for c in cases
           if not (re.fullmatch(r"[0-9a-f]{64}", c.get("input_sha256", "") or "0" * 64)
                   and re.fullmatch(r"[0-9a-f]{64}", c.get("capture_sha256", "")))]
    if bad:
        say("FAIL", "held-out: no hash recorded for " + ", ".join(bad))
    if man.get("frozen_sha256") != heldout.digest(cases):
        say("FAIL", "held-out: the cases in heldout/manifest.json are not the ones that "
                    "were frozen (the set is not changed once built)")
    names = {c["name"] for c in cases}
    leaked = [f for f in tracked
              if Path(f).name.split(".")[0] in names and not f.startswith("heldout/manifest")]
    if leaked:
        say("FAIL", "held-out: per-case files are tracked: " + ", ".join(leaked[:5]))
    tp = ROOT / "heldout" / "totals.json"
    text = tp.read_text() if tp.exists() else ""
    named = sorted(n for n in names if re.search(rf"(?<![\w-]){re.escape(n)}(?![\w-])", text))
    for f in ("docs/verification-results.json", "docs/summary.md", "docs/status.md",
              "docs/deviations.md"):
        q = ROOT / f
        t = q.read_text(encoding="utf-8") if q.exists() else ""
        named += [f"{n} in {f}" for n in sorted(names)
                  if re.search(rf"(?<![\w-]){re.escape(n)}(?![\w-])", t)]
    if named:
        say("FAIL", "held-out: cases are named outside the manifest (totals only): "
                    + ", ".join(named[:5]))
    try:
        heldout.check_totals(heldout.read_totals())
    except ValueError as e:
        say("FAIL", f"held-out: heldout/totals.json: {e}")
        return
    if not (bad or leaked or named):
        say("ok", f"held-out: {len(cases)} cases, frozen {man.get('frozen')}, as frozen; "
                  f"totals only ({len(heldout.read_totals()['runs'])} run(s) recorded)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--strict", action="store_true", help="stale results are an error")
    a = ap.parse_args(argv)
    bad = 0

    def say(kind: str, msg: str) -> None:
        nonlocal bad
        bad += kind == "FAIL"
        print(f"{kind:<5} {msg}")

    _rc, out = git("ls-files")
    tracked = out.splitlines()

    # 1. the brief and the targets
    if not (ROOT / "docs" / "brief.md").exists() or (ROOT / "docs" / "acceptance.md").exists():
        say("FAIL", "brief: docs/brief.md must exist and docs/acceptance.md must not")
    acc = {}
    try:
        acc = report.read_targets(ROOT / "docs" / "measures.md")
        say("ok", "brief in place; targets set for " + ", ".join(g for g, t in acc.items() if t))
    except (Exception, SystemExit) as e:  # noqa: BLE001
        say("FAIL", f"targets: {e}")

    # 2. the development results
    md = ROOT / "docs" / "verification-results.md"
    js = md.with_suffix(".json")
    if not md.exists() or not js.exists():
        say("FAIL", "verification results: docs/verification-results.md or .json missing")
    else:
        data = json.loads(js.read_text())
        run = data["run"]
        commit = run.get("commit", "")
        text = md.read_text(encoding="utf-8")
        if not text.startswith(report.GENERATED):
            say("FAIL", "verification results: the generated marker is gone (edited by hand?)")
        elif text != report.render(data["results"], run, acc, "docs/measures.md"):
            say("FAIL", "verification results: differ from what tools/report.py writes from "
                        "their JSON (edited by hand, or the report changed: rerun it)")
        else:
            say("ok", "verification results: as generated")
        rc, changed = git("diff", "--name-only", commit, "HEAD", "--", "src/r2c")
        if rc != 0:
            say("warn", f"verification results: cannot tell whether current (commit "
                        f"{commit[:12]} is not in this clone's history)")
        elif changed or run.get("dirty"):
            files = ", ".join(changed.split()) or "uncommitted changes at the time of the run"
            say("FAIL" if a.strict else "warn",
                f"verification results are stale: run at {commit[:12]}, kernel changed "
                f"since ({files})")
        else:
            say("ok", f"verification results: current (run at {commit[:12]})")

    # 3. the summary, 4. the held-out set
    check_summary(say)
    check_heldout(say, tracked)

    # 5. the logs
    logs = sorted((ROOT / "docs" / "log").glob("2*.md"))
    before = bad
    for p in logs:
        text = p.read_text(encoding="utf-8")
        missing = [s for s in LOG_SECTIONS if s not in text]
        if missing:
            say("FAIL", f"{p.relative_to(ROOT)}: missing {', '.join(missing)}")
        elif not re.search(r"## Held-out rule\s+\**(Kept|Not kept)\b", text):
            say("FAIL", f"{p.relative_to(ROOT)}: \"Held-out rule\" must open with Kept or "
                        "Not kept")
        if OLD_NUMBER.search(text):
            say("FAIL", f"{p.relative_to(ROOT)}: uses the earlier record's numbering "
                        f"({OLD_NUMBER.search(text).group()})")
    if bad == before:
        say("ok", f"logs: {len(logs)} checked")

    # 6. the earlier record is not referred to; deviations are not numbered
    before = bad
    for f in LIVING:
        p = ROOT / f
        if not p.exists():
            if f in ("docs/summary.md", "docs/status.md", "docs/deviations.md"):
                say("FAIL", f"{f} is missing")
            continue
        text = p.read_text(encoding="utf-8")
        m = OLD_NUMBER.search(text)
        if m:
            say("FAIL", f"{f}: uses the earlier record's numbering ({m.group()})")
        if f != "CLAUDE.md" and re.search(r"\bphase [AB]\b|\bstep A-\d", text):
            say("FAIL", f"{f}: refers to the earlier record's phases")
    dev = ROOT / "docs" / "deviations.md"
    if dev.exists() and re.search(r"^(\d+\.|#+ *\d)", dev.read_text(encoding="utf-8"), re.M):
        say("FAIL", "docs/deviations.md: the entries are not numbered")
    if bad == before:
        say("ok", "the living record: no numbered decisions, deviations unnumbered")

    # 7. what stays out of the repository
    out_ = [f for f in tracked if KEPT_OUT.search("/" + f)]
    dec = []
    for f in tracked:
        p = ROOT / f
        if (p.suffix in (".py", ".md", ".c", ".txt", ".toml", ".json") and p.exists()
                and p.stat().st_size < 4_000_000 and f != "tools/check.py"
                and DECOMPILED.search(p.read_text(encoding="utf-8", errors="replace"))):
            dec.append(f)
    if out_:
        say("FAIL", "tracked but never committed by rule: " + ", ".join(out_[:5]))
    if dec:
        say("FAIL", "looks like decompiler output: " + ", ".join(dec[:5]))
    if not out_ and not dec:
        say("ok", f"nothing of Response or a decompiler among {len(tracked)} tracked files")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
