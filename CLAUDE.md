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
work, record the question under "Open questions for the owner" in the session log, and carry
on with something else.

## Starting a session

Read this file, `docs/status.md`, and the latest file in `docs/log/`. Read anything else only
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
  cites it. The results page (GitHub Pages) is rebuilt from the same JSON by CI on every push
  to `main`: nothing to do by hand.

## Ending a session

1. Write `docs/log/YYYY-MM-DD-NN.md` from `docs/log/TEMPLATE.md`. Keep it short. The sections
   that matter most: what was tried and dropped (so it is not tried again) and the decisions
   made, each with who made it and why.
2. Update `docs/status.md` to what is true now. It is a description of the present, not a
   history; the history is in the logs and in git.
3. If the kernel changed, rerun verify and report, or leave `tools/check.py` reporting the
   results as stale and say so in the log.
4. `pytest` and `python tools/check.py` pass. Push.

Not wanted: a changelog, a commit log, or recording commit IDs in files. Git keeps those.

## Where things are

| What | Where |
|---|---|
| Present state, open options | `docs/status.md` |
| What happened in each session | `docs/log/` |
| What agreement means (the owner's) | `docs/acceptance.md` |
| Each kernel rule and its source | `docs/kernel.md` |
| Results against Response (generated) | `docs/verification-results.md` |
| What the results mean | `docs/verification.md` |
| The results as pictures, for review | https://maczout.github.io/r2c/ (`tools/dashboard.py`) |
| Diagnostics: r2c in Response's states | `tools/diagnose.py` |
| Rebuild the oracle archive | `tools/capture.py` |
| Checks before pushing | `tools/check.py`, `pytest` |
