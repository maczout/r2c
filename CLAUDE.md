# Working on r2c

r2c is a Python clone of Response-2000's sectional analysis. r2x (github.com/maczout/r2x)
drives Response-2000 itself and is r2c's oracle. This file is how work on r2c is done, by a
person or a coding agent. It is short on purpose: read it whole, then read selectively.

## Roles

- **The owner** is the structural engineer responsible for r2c. Structural engineering is the
  owner's side: what counts as agreement, which results matter, what a difference means.
- **The developer** (a person or a coding agent) does the software engineering.

"Engineering" in this repository means structural engineering unless it says otherwise. Mark
anything that needs a structural judgement as such and leave it to the owner.

## Development and meta-development

- **Development changes what r2c does:** the kernel, its interface, and the tests and docs
  that go with them. It is done in controlled increments, each measured against the targets.
- **Meta-development changes what "done" means or how it is seen:** the targets
  (`docs/acceptance.md`), the measures (`tools/compare.py`, `tools/report.py`), the results
  pages (`tools/dashboard.py`, `tools/site.py`), the fixtures and the test set. It is done
  with the owner, who decides each choice as it comes up.

In a development session, `docs/acceptance.md` is not changed. Fixing a bug in a measure counts
as development; any change to the measures, pages or fixtures goes in its own commit with its
reason, and is listed in the pull request under "Measurement changes" for the owner to review.
Never change a measure, a target or a fixture to bring a result inside target.

## Instruction hierarchy

When these pull against each other, the higher one wins.

1. **`docs/acceptance.md` (the owner's).** What "agrees with Response-2000" means: an
   engineer's agreement within tolerance, not mathematical equivalence. Where it sets a
   tolerance, that is the target. Where it is silent, the developer decides and records the
   decision (below).
2. **Bentz's thesis** is the basis of the kernel: its method, its relations, its notation.
3. **Response-2000's binary** may be read to find out why r2c does not reach acceptance where
   the thesis leaves the answer open: a constant, a table, a detail of a routine. Every rule
   taken from it is recorded in `docs/kernel.md` with its source. It is not the route to
   matching Response beyond what acceptance asks.
4. **The regression limits in `tests/`** guard what works. They are not acceptance.

When a goal and a constraint conflict and this list does not settle it, stop that line of
work, add the question to the decisions in `docs/summary.md` (below), and carry on with
something else.

## The owner's summary

`docs/summary.md` is the one page the owner reads: the aim, the phases, progress against the
exit criteria, the risks, and every decision, open or made. The decisions there sit just
under `docs/acceptance.md` in the hierarchy above.

- **Every question for the owner goes there**, numbered (D1, D2, …, never renumbered), with
  the developer's suggested answer. A session log refers to it by number; it does not hold
  questions of its own.
- **Answers are recorded there**, marked *decided*, with "owner" and the date. A developer's
  reading of an answer is a new item marked *suggested*.
- **Written for the owner.** Plain words, short, no tool names or addresses where a sentence
  will do. Detail stays in `docs/status.md`, `docs/kernel.md` and the logs, and the summary
  points to it.

## Starting a session

Read this file, `docs/summary.md`, `docs/status.md`, and the latest file in `docs/log/`. Read anything else only
when the work needs it (`docs/kernel.md` before changing the kernel; `docs/acceptance.md`
before judging a result). Run `python tools/check.py` to see the state of the record.

## During a session

- **Commit as you go.** Small commits, each with its reason in the message. Push the working
  branch at least at every natural stopping point: a working environment can disappear, and
  only what is pushed survives.
- **A script that answered a question goes in `tools/` in the same session**, with a
  docstring saying what it answers. Nothing useful stays in a scratch folder.
- **Data stays out of the repository**, with the recipe in it. Full oracle captures go to an
  archive outside the repository (`tools/capture.py`); the fixtures in `tests/oracle` are the
  recipe for rebuilding it. Response-2000, its sample inputs, and any decompiler project of
  its binary are never committed.
- **Mark where every claim comes from.** In docs and logs, numbers are *measured* (and how:
  command, machine), *estimated* (and from what), or *inferred*. Kernel rules carry their
  source in `docs/kernel.md` (thesis, binary, inferred from output). The owner's decisions are
  marked as the owner's, with the date; the developer's readings of them are marked "reading,
  for the owner to confirm".
- **Never hand-write verification numbers.** `docs/verification-results.md` is generated:
  `python tools/verify.py tests/oracle --inputs RESPONSE_FOLDER --out VERIFY_OUT --jobs N`,
  then `python tools/report.py VERIFY_OUT`. Prose in `docs/verification.md` interprets it and
  cites it. The results pages (GitHub Pages) are rebuilt from the same JSON by CI after every
  push: `main` at the root, each branch at `branches/<branch>/`. Nothing to do by hand; a pull
  request links its branch's page.

## Ending a session

1. Write `docs/log/YYYY-MM-DD-NN.md` from `docs/log/TEMPLATE.md`. Keep it short. The sections
   that matter most: what was tried and dropped (so it is not tried again) and the decisions
   made, each with who made it and why.
2. Update `docs/summary.md`: progress, the phase, the decisions (new questions added, answers
   recorded). The pull request's description opens with what changed on it.
3. Update `docs/status.md` to what is true now. It is a description of the present, not a
   history; the history is in the logs and in git.
4. If the kernel changed, rerun verify and report, or leave `tools/check.py` reporting the
   results as stale and say so in the log.
5. `pytest` and `python tools/check.py` pass. Push.

Not wanted: a changelog, a commit log, or recording commit IDs in files. Git keeps those.

## Where things are

| What | Where |
|---|---|
| **The owner's page: aim, phases, progress, decisions** | `docs/summary.md` |
| Present state in detail, open options | `docs/status.md` |
| What happened in each session | `docs/log/` |
| What agreement means (the owner's) | `docs/acceptance.md` |
| Each kernel rule and its source | `docs/kernel.md` |
| Results against Response (generated) | `docs/verification-results.md` |
| What the results mean | `docs/verification.md` |
| The results as pictures, for review | https://maczout.github.io/r2c/ (`tools/dashboard.py`); a branch's at `branches/<branch>/` (`tools/site.py`) |
| Diagnostics: r2c in Response's states | `tools/diagnose.py` |
| Rebuild the oracle archive | `tools/capture.py` |
| Checks before pushing | `tools/check.py`, `pytest` |
