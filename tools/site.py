#!/usr/bin/env python3
"""Build the results site: main's page at the root, and a preview page for every branch.

    python tools/site.py OUT

Answers "what do a branch's results look like before it is merged?". Each page is built by
that branch's own tools/dashboard.py from that branch's committed results
(docs/verification-results.json), so a branch's page shows its own measures and targets.
Nothing is run against Response. Branch pages carry a banner naming the branch and commit;
OUT/branches/index.html lists them. A branch without a dashboard or committed results is
listed, not built.

Beside each page goes that branch's "Review" page (review.html: the end-of-phase review of
docs/review.md, built by the branch's tools/review.py from the same results) where the
branch has one, with the independent assessments it shows copied next to it as written
(review/independent/). The banner of each page links the two.

Branches are the remote-tracking ones (refs/remotes/origin/*), so the clone must have them
all (in CI: actions/checkout with fetch-depth 0). Each is checked out into a temporary git
worktree and removed afterwards.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = "main"


def git(*args, cwd=ROOT) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          check=True).stdout.strip()


def slug(branch: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", branch).strip("-") or "branch"


def branches() -> list[tuple[str, str, str, str]]:
    """(branch, commit, date, subject) for each remote branch, main first."""
    out = git("for-each-ref", "--format=%(refname:short)\t%(objectname:short)\t"
              "%(committerdate:short)\t%(subject)", "refs/remotes/origin")
    rows = []
    for ln in out.splitlines():
        ref, commit, date, subject = ln.split("\t", 3)
        name = ref.removeprefix("origin/")
        if name in ("HEAD", "origin") or ref == "origin":
            continue
        rows.append((name, commit, date, subject))
    return sorted(rows, key=lambda r: (r[0] != MAIN, r[0]))


def banner(text: str) -> str:
    return ('<div style="background:#fff4d6;color:#5a4300;border-bottom:1px solid #e0c97a;'
            'padding:8px 16px;font:14px system-ui,sans-serif">' + text + "</div>")


def inject(page: Path, html_text: str) -> None:
    s = page.read_text(encoding="utf-8")
    m = re.search(r"<body[^>]*>", s)
    s = s[: m.end()] + html_text + s[m.end():] if m else html_text + s
    page.write_text(s, encoding="utf-8")


def build_one(tree: Path, out: Path) -> str:
    """Build tree's page into out/index.html; '' on success, else why not."""
    if not (tree / "tools" / "dashboard.py").exists():
        return "no tools/dashboard.py"
    if not (tree / "docs" / "verification-results.json").exists():
        return "no committed results"
    out.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([sys.executable, "tools/dashboard.py", "--out", str(out / "index.html")],
                       cwd=tree, capture_output=True, text=True)
    if p.returncode != 0:
        return "dashboard failed: " + (p.stderr.strip().splitlines() or ["?"])[-1]
    return ""


def build_review(tree: Path, out: Path) -> bool:
    """Build tree's review page into out/review.html, with the independent assessments
    beside it; False where the branch has none or it does not build (said, not fatal)."""
    if not (tree / "tools" / "review.py").exists():
        return False
    p = subprocess.run([sys.executable, "tools/review.py", "--out", str(out / "review.html")],
                       cwd=tree, capture_output=True, text=True)
    if p.returncode != 0:
        print("  review not built: " + (p.stderr.strip().splitlines() or ["?"])[-1])
        return False
    src = tree / "docs" / "review" / "independent"
    if src.is_dir():
        shutil.copytree(src, out / "review" / "independent", dirs_exist_ok=True)
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out")
    a = ap.parse_args(argv)
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, commit, date, subject in branches():
            tree = Path(tmp) / slug(name)
            git("worktree", "add", "--detach", str(tree), f"origin/{name}")
            try:
                dest = out if name == MAIN else out / "branches" / slug(name)
                why = build_one(tree, dest)
                reviewed = not why and build_review(tree, dest)
            finally:
                git("worktree", "remove", "--force", str(tree))
            link = "./" if name == MAIN else f"branches/{slug(name)}/"
            rows.append((name, commit, date, subject, link, why))
            if why:
                print(f"{name}: not built ({why})")
                continue
            for page, other in ((dest / "index.html",
                                 '<a href="review.html"><b>The review</b></a> · '),
                                (dest / "review.html",
                                 '<a href="./">The results, check by check</a> · ')):
                if not reviewed and page.name == "review.html":
                    continue
                other = other if reviewed else ""
                if name == MAIN:
                    inject(page, banner('Results of <b>main</b>. ' + other +
                                        '<a href="branches/">Preview pages of other branches</a>'))
                else:
                    inject(page, banner(
                        f"Preview of branch <b>{html.escape(name)}</b> at {commit} ({date}), "
                        "not merged into main. " + other +
                        '<a href="../../">main</a> · <a href="../">all branches</a>'))
            print(f"{name}: built")
    idx = out / "branches" / "index.html"
    idx.parent.mkdir(parents=True, exist_ok=True)
    items = []
    for n, c, d, subj, link, why in rows:
        cell = html.escape(n) if why else f'<a href="../{link}">{html.escape(n)}</a>'
        items.append(f"<tr><td>{cell}</td><td>{c}</td><td>{d}</td><td>{html.escape(subj)}</td>"
                     f"<td>{html.escape(why)}</td></tr>")
    items = "".join(items)
    idx.write_text(
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>r2c: branch "
        "previews</title><style>body{font:15px system-ui,sans-serif;margin:24px;max-width:960px}"
        "td,th{padding:4px 10px;text-align:left;border-bottom:1px solid #ddd}</style></head>"
        "<body><h1>r2c: results by branch</h1><p>Each page is built from that branch's "
        "committed results by that branch's own tools. Rebuilt after every push.</p>"
        "<table><tr><th>Branch</th><th>Commit</th><th>Date</th><th>Last commit</th>"
        f"<th>Not built because</th></tr>{items}</table></body></html>", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
