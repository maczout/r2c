# The brief

**This file is the owner's.** It was approved by the owner on 2026-11-24 and governs the work
from the first increment on. It is the owner's text word for word; only headings and list
markers were added. The developer does not change it. It replaces `docs/acceptance.md`.

## Goal

As good a sectional response calculator as possible, interchangeable with r2x.

"Good" means this: on sections the developer has not tuned against, r2c gives
Response-2000's answers within an engineer's tolerance.

How r2c is made to agree is the developer's business. The owner judges the result, not the
method.

## How the work runs

The work runs as development increments. They continue until the solution threshold is
reached, or until the approach plateaus.

- **Solution threshold** (proposed; the owner sets it):
  - interface parity is complete;
  - on the held-out set, the priority 1 checks are inside target on at least 99 % of cases
    without shear and 90 % with shear.
- **Plateau:** two increments in a row with no gain in any area's held-out total.

The owner sets each increment's budget, and the developer plans to fit it.

## Before anything else: interface parity

r2c takes the same command line as r2x, writes the same output format, and refuses the same
inputs. This is checked against r2x and scored like the rest.

## Accuracy priorities, in order

The order guides where effort goes. It does not gate the work.

1. Peak, rising branch and shape of the control curves; the stress-state views under moment
   and axial load.
2. Endings of responses without shear; the shear-related views.
3. Cracking-related views.
4. Endings of shear responses.

## Fixed by the owner

- Tolerance: ±5 %, with the floor at the printed precision. Shape is matched by its
  features. The measures stay as they are unless the owner changes them.
- One override: for the circular column under axial load alone, r2c keeps its uniform
  post-peak response.
- The held-out rule (below).

## Rules that stay

These carry over unchanged from the earlier CLAUDE.md:

- Scope comes from the manual (Appendix A of Bentz's thesis, `docs/scope.md`).
- The calculation comes from the 1.9.7 binary. Each rule is written fresh in r2c's own
  code. Decompiled output is never committed. Response-2000 and its sample inputs are never
  committed. Each rule's source is recorded in `docs/kernel.md`.
- No result is brought inside target by changing a measure, a target or a fixture.
- Verification numbers are generated, never hand-written. Claims are marked measured,
  estimated or inferred.
- Commit small and push often.

## The developer owns

- Strategy: what to work on, in what order, how hard to push, and when to stop chasing
  something. This includes accepting a deviation and dropping an approach.
- The development set, and its fixtures.
- Tools, tests, docs and the results pages. All of them may be pruned freely.
- A short list of known deviations, in plain language. The owner does not approve entries
  one by one, and they are not numbered.

## The held-out set

- Built before any kernel work. It is drawn from Response's sample files, plus variations
  across the scope (shapes, reinforcement, material models, loads, units) that are not in
  the development set. About 30 to 50 cases, captured through r2x.
- Frozen once built. Its recipe and hashes are committed.
- Scored by a tool that prints only totals, by area (moment and axial; shear) and by
  priority. Its per-case results stay in the archive outside the repository. They are not
  committed, and they are not on the results pages; only the totals are. The developer does
  not open per-case results and does not diagnose with held-out cases. If a total drops, the
  developer finds the cause on the development set. This rests on instruction, so each log
  says whether it was kept.
- Floor: a fall in any area's total is reported to the owner, even if the overall total
  rises.

## Stop and ask the owner when

- an area's held-out total falls, and it cannot be recovered in the same increment;
- the developer wants a new override, or a change to a measure or the tolerance;
- the developer judges that the threshold is reached, or that the approach has plateaued.

Everything else the developer decides, and notes in the log.

## Reporting

`docs/summary.md` is one page at most, kept current each increment:

- held-out totals by area and priority, with their trend across increments;
- what changed, in three lines or fewer;
- what the developer needs from the owner: three items at most, often none;
- the top five known deviations.

Everything else is reference.

## Finishing

- The held-out results are opened case by case for the first time.
- An independent assessor, working from the evidence alone, explains the largest misses.
  Its explanation is shown beside the developer's.
- The owner signs off, or names what is still needed.

## First increment

This increment changes how the work is governed, with the owner's approval.

1. **Governance first, in its own commits.**
   - Add this brief as `docs/brief.md` and delete `docs/acceptance.md`.
   - Rewrite CLAUDE.md to match: roles; the hierarchy (the brief, then the rules that stay,
     then the developer's judgement); how an increment runs; the held-out rule; when to stop
     and ask. The meta-development/development split and the numbered decisions are dropped.
   - Update `tools/check.py` and the tests so they enforce the new record, not the old one.
2. **Close the earlier record.** The pending end-of-phase decisions are accepted as the
   developer suggested. That includes the correction to the US-units shapes: these are a
   fall of load just under what the measure counts, not the named limitation. Move the old
   decisions, the phases and the C/D numbering to `docs/history.md`. They are not referred
   to again.
3. **Prune.**
   - Rewrite `docs/summary.md` to the one-page form.
   - Archive the logs.
   - Cut `docs/status.md` to what the developer needs.
   - Remove the end-of-phase review machinery, or keep only what the finishing assessment
     will reuse.
   - Delete unused tools, or move them to `tools/attic/`.
4. **Build and freeze the held-out set, and its totals-only scorer.** Record the first
   totals as the baseline.
5. **Build the interface parity check, and close the gaps it finds.**
