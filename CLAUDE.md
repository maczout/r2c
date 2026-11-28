# Working on r2c

r2c is a Python clone of Response-2000's sectional analysis. r2x (github.com/maczout/r2x)
drives Response-2000 itself and is r2c's oracle. This file is how work on r2c is done, by a
person or a coding agent. It is short on purpose: read it whole, then read selectively.

## Roles

- **The owner** is the structural engineer responsible for r2c. The owner wrote the brief
  (`docs/brief.md`), sets each increment's budget, and judges the result, not the method.
- **The developer** (a person or a coding agent) does everything else: strategy, the
  development set, the tools, the tests, the docs, the results pages.

"Engineering" in this repository means structural engineering unless it says otherwise.

## Hierarchy

When these pull against each other, the higher one wins.

1. **The brief, `docs/brief.md` (the owner's).** The goal, the priorities, what the owner
   has fixed (the tolerance, the measures, the one override, the held-out rule), and when to
   stop and ask. The developer does not edit it.
2. **The rules that stay** (below).
3. **The developer's judgement.** Everything else. A choice that a later increment would
   want to know about is noted in the log, with its reason.

## The rules that stay

- **Scope comes from the manual** (Appendix A of Bentz's thesis; `docs/scope.md`). The
  binary does not add features.
- **The calculation comes from Response-2000's binary** (1.9.7, the program the oracle
  runs): its method, constants, tables, layering, solver and how a solve ends. Read it
  directly; it is the primary route, not a last resort. Where the thesis and the binary
  differ, follow the binary. The thesis is the guide to reading it and the source of names.
  - Write each rule fresh, in r2c's own code and words. Do not transliterate decompiled
    code. **Decompiled output is never committed.**
  - Record every rule's source in `docs/kernel.md`: the binary's address, and the thesis'
    equation or section where there is one.
- **Response-2000, its sample inputs and any decompiler project of its binary are never
  committed.** Captures stay in an archive outside the repository, with the recipe in it.
- **No result is brought inside target by changing a measure, a target or a fixture.** The
  measures (`docs/measures.md`, `tools/compare.py`, `tools/report.py`) stay as they are
  unless the owner changes them. Fixing a bug in a measure goes in its own commit, with its
  reason, and is listed in the pull request under "Measurement changes".
- **Verification numbers are generated, never hand-written.** Claims in docs and logs are
  marked *measured* (and how: command, machine), *estimated* (and from what) or *inferred*.
- **Commit small and push often.** A working environment can disappear; only what is pushed
  survives.

## The held-out rule

The held-out set (`heldout/`) is what "good" is judged on: sections the developer has not
tuned against. It is frozen; its recipe and hashes are committed (`heldout/manifest.json`).

- **Score it only with `tools/heldout.py score`**, which prints totals by area and priority.
  It may also print the failing cases by kind (section type, loading path, area and
  priority), with no curves, numbers or case names (owner, 2026-11-25): that is for
  choosing what to add to the development set, and nothing else. Its per-case results go
  to the archive outside the repository.
- **Do not open per-case held-out results**, by any route: not the scorer's files in the
  archive, not r2c's own output for a held-out case, not a comparison of one. Do not run r2c
  on a held-out input to look at what it does.
- **Do not diagnose with held-out cases.** If a total drops, find the cause on the
  development set (`tests/oracle`), adding development cases if it has none like it.
- **Do not change the set.** No case is added, removed, recaptured or re-cut. A case that
  cannot be scored is counted as outside, not dropped.
- **Nothing per-case is committed or published**: only `heldout/totals.json` and what is
  made from it.
- **Response against itself** (owner, 2026-11-25): `tools/heldout.py repeat` captures
  Response on each held-out input with every concrete strength raised by 0.05 % and
  prints totals only (`heldout/repeatability.json`); the threshold is made from them. No
  r2c result is involved. Its captures and per-case comparisons stay in the archive and
  are not opened either.
- **The second set, for the finish** (`heldout/finish-manifest.json`; owner, 2026-11-25):
  about 20 more cases, frozen the same way in an archive of its own. It is not scored in
  any way until the finishing steps: `tools/heldout.py score` refuses it, r2c is not run
  on its inputs, its captures are not opened. Everything above holds for it too.
- **At the finish** (owner, 2026-11-26: "start the finishing steps"): the second set was
  scored once (`heldout/finish-totals.json`) and both sets were opened case by case, for
  the independent assessor (`tools/opened.py`, into files outside the repository;
  `docs/assessment.md`). Both sets are spent as held-out sets. Per-case tables are still
  not committed; the assessor's findings name cases and sizes, as written.
- **After the finish** (owner, 2026-11-27): both sets were scored once more after the
  override was narrowed and the record made to mark where Response stops. How a trace of
  Response shows each of their cases to have ended is per-case and stays in the archives
  (`trace-ends.json` there; `tools/traceend.py`).
- **Each log says whether the rule was kept**, since it rests on instruction.
- **Floor:** a fall in any area's total is reported to the owner in the summary, even if
  the overall total rises.

## How an increment runs

An increment is one budgeted piece of work, usually one session and one pull request.

**Start.** Read this file, `docs/brief.md`, `docs/summary.md`, `docs/status.md` and the
latest log in `docs/log/`. Read anything else when the work needs it (`docs/kernel.md`
before changing the kernel; `docs/measures.md` before judging a result). Run
`python tools/check.py`. Plan to fit the budget the owner set, by the brief's priorities.

**During.**

- **The budget is meant to be used** (owner, 2026-11-25). When a line of work ends, start
  the next. A question for the owner does not end the increment: record it with a
  suggested answer, act on that answer where it can be undone, and carry on. Stop only
  when the budget is spent or a stop-and-ask condition of the brief is met. Open-ended
  work on stages that do not settle is in bounds; measure it and log it.
- Work on the development set. The order of the priorities guides effort; it does not gate.
- Accepting a deviation or dropping an approach is the developer's call. Put it in
  `docs/deviations.md` in plain language (no numbers for the entries) and say why in the log.
- A script that answered a question goes in `tools/` in the same session, with a docstring
  saying what it answers. One that is no longer used is deleted or moved to `tools/attic/`.
- **A speed change changes no result** (owner, 2026-11-26): every development record is
  identical before and after it. `tests/oracle/records.json` holds each record's hash;
  after a speed change run the set and `python tools/same.py VERIFY_OUT`. A change of
  result rewrites the hashes in its own commit (`--write`).
- After a kernel change, regenerate the development results:
  `python tools/verify.py tests/oracle --inputs FOLDERS --out VERIFY_OUT --jobs N`, then
  `python tools/report.py VERIFY_OUT`. The results pages are rebuilt from the committed JSON
  by CI after every push (`main` at the root, a branch at `branches/<slug>/`, `/` as `-`).

**End.**

1. Score the held-out set once, at the end: `python tools/heldout.py score ARCHIVE --inputs
   FOLDERS --record LABEL`. It appends the totals to `heldout/totals.json`.
2. Write `docs/log/YYYY-MM-DD-NN.md` from `docs/log/TEMPLATE.md`. Short. What matters most:
   what was tried and dropped, and whether the held-out rule was kept.
3. Bring `docs/summary.md` up to date (`python tools/heldout.py summary` writes its totals block). It
   is one page at most: the held-out totals and their trend; what changed, in three lines
   or fewer; what is needed from the owner, three items at most; the top five known
   deviations.
4. Bring `docs/status.md` to what is true now. It describes the present; the history is in
   the logs and in git.
5. `pytest` and `python tools/check.py` pass. Push. Open the pull request; its description
   opens with what changed.

Not wanted: a changelog, commit IDs recorded in files, numbered decisions, or a growing
summary.

## Stop and ask the owner when

- an area's held-out total falls, and it cannot be recovered in the same increment;
- you want a new override, or a change to a measure or the tolerance;
- you judge that the solution threshold is reached, or that the approach has plateaued:
  an increment that gains nothing on a live target (owner, 2026-11-26). The threshold
  (owner, 2026-11-25), on the held-out set, for each area and priority 1 to 3: Response's
  own score there against itself after every concrete strength is raised by 0.05 %, less
  3 points (`heldout/repeatability.json`, the values in the brief); priority 1 without
  shear keeps 99 %. The live targets (owner, 2026-11-26) are the cells of it not yet
  met: priorities 1 and 3 with shear. Reported and not targets: priority 2 with shear,
  beside Response's own score; priority 4; and speed, r2c's run time beside r2x's on the
  same input and machine with r2x reading every stage (`tools/r2xtimes.py`,
  `tests/oracle/r2x-times.json`). No compiled routines. When the live targets are met
  or the plateau rule fires, ask before starting the finishing steps.

Asking means: say it under "Needed from the owner" in `docs/summary.md` and in the pull
request, with a suggested answer, stop that line of work, and carry on with something
else. Everything else, decide and note in the log.

## Where things are

| What | Where |
|---|---|
| **The owner's brief** | `docs/brief.md` |
| **The one page for the owner** | `docs/summary.md` |
| Present state, for the developer | `docs/status.md` |
| Known deviations, in plain language | `docs/deviations.md` |
| The measures and the targets | `docs/measures.md` |
| What is in scope | `docs/scope.md` |
| Each kernel rule and its source | `docs/kernel.md` |
| The held-out set and the second one for the finish: recipe, hashes, totals; Response against itself and the threshold | `heldout/`, `tools/heldout.py` |
| Interface parity with r2x | `tools/parity.py` |
| The record as r2c's public interface, what r2 builds on from 0.9.0: what a reader may rely on; whether it carries what r2x's does | `docs/output.md`, `tools/carries.py`, `docs/output-check.md` (generated) |
| Development results against Response (generated) | `docs/verification-results.md`, https://maczout.github.io/r2c/ |
| What happened in each increment | `docs/log/` |
| The earlier record (closed 2026-11-24; not referred to) | `docs/history.md`, `docs/history/` |
| Rebuild the oracle archive | `tools/capture.py` |
| Checks before pushing | `tools/check.py`, `pytest` |
