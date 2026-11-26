# The held-out set

What "good" is judged on (`docs/brief.md`): cases the developer has not tuned against.

- `manifest.json`: the frozen set. For each case its recipe (the input and how it was
  derived, the loads, units and factors) and the SHA-256 of its input and of its capture
  from Response-2000; one hash over all of them. Candidates that Response did not solve
  are listed under `not_captured` and are not cases.
- `totals.json`: the totals of each recorded scoring, by area and priority. Nothing per
  case.

- `finish-manifest.json`: the second set, for the finish (owner, 2026-11-25). The same
  form, frozen the same way, in an archive of its own. It is not scored in any way until
  the finishing steps: `tools/heldout.py score --set finish` refuses, and no total of it
  exists.

The recipe itself (the text edits that derive each input) is in `tools/heldout.py`. The
captures, the inputs and every per-case result are in an archive outside the repository.

**The rule** (`CLAUDE.md`, "The held-out rule"): score with `python tools/heldout.py score`
and read the totals; open nothing per case; diagnose on the development set; do not change
the set.

To rebuild the archive on another machine, the recipe and the hashes are enough: derive the
inputs, capture them through r2x with the settings in the manifest, cut each capture with
`tools/trim.py` as `tools/capture.py` does for a new case, and compare the hashes. A capture
that does not match its hash is not the frozen one (Response does not repeat every case run
to run), and the frozen archive should be copied instead.
