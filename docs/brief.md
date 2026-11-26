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

## Owner's decisions since

Recorded here at the owner's instruction, in the owner's words. Where one of these differs
from the text above, it governs.

**2026-11-24**, in answer to the questions of the summary after increment 1:

1. define and --report are not part of "the same command line": they stay refused and are
   left out of the parity score.
2. Inputs Response solves but its manual does not document: refuse, listed as known
   differences. They may be revisited after the threshold.
3. Solution threshold on priority 1: 99 % without shear, 90 % with.

**2026-11-25**, in answer to the questions of the summary after increment 2:

1. Interface parity is complete when the only differences left are the inputs refused by
   the owner's decision. Report it that way: "complete except accepted refusals", with
   the count.
2. Budget: about three hours of work.
3. Where Response's solve gives up and ends a shear response early while r2c carries on:
   keep r2c carrying on, as an owner's override like the circular column. (The message
   left both choices standing, "clone Response's ending / keep r2c carrying on"; asked
   the same day, the owner chose this one.)

**2026-11-25**, in answer to the questions of the summary after increment 3:

1. For cases under the override where Response's solve gives up and r2c carries on,
   compare up to Response's last stage. Apply it to the development and held-out
   measures alike, in its own commit.
2. The four parity differences where Response gives up part-way are accepted as known
   differences: parity is complete except accepted refusals.
3. The held-out scorer may also report the failing cases by kind (section type, loading
   path, area and priority), with no curves, numbers or case names. Use it to choose
   what to add to the development set.
4. Budget: about three hours of work, and it is meant to be used. When a line of work
   ends, start the next. Questions for the owner do not end the increment: record them
   with a suggested answer, act on that answer where it can be undone, and carry on.
   Stop only when the budget is spent or a stop-and-ask condition in the brief is met.
   Open-ended work on stages that do not settle is in bounds; measure and log it.

**2026-11-25**, in answer to the questions of the summary after increment 4:

1. Keep the developer's rule for telling a case where Response's solve gives up. It will
   be the first thing the independent assessor checks at the finish.
2. The case under axial compression and shear where Response's solve breaks down after
   the web cracks stays outside; nothing is changed for it.
3. The bug fix in the measure (a difference of exactly two printed units) is confirmed.
4. The solution threshold is tightened. On the held-out set:
   - priority 1: 99 % without shear, 99 % with;
   - priority 2: 95 % without shear, 60 % with;
   - priority 3: 95 % without shear, 85 % with;
   - priority 4 (endings with shear): no target, reported only.
   The plateau rule is unchanged: two increments in a row with no gain in any area's
   held-out total.
5. Before any kernel work, build a second held-out set for the finish: about 20 cases
   of the same spread, captured through r2x, frozen with its recipe and hashes, and not
   scored in any way until the finishing steps. Its own commit.
6. Budget: about three hours of work, used as CLAUDE.md says.

If the threshold is reached, stop and ask before starting the finishing steps.

**2026-11-25**, in answer to the questions of the summary after increment 5:

1. The solution threshold is reframed around Response's own repeatability. Measure, on
   the held-out inputs, how often Response agrees with itself after every concrete
   strength is raised by 0.05 % (Response against Response only; no r2c results are
   involved, so the held-out rule is kept). The threshold for each area and priority 1
   to 3 is Response's own score there, less 3 points. Priority 4 stays reported only.
   Record the measured values in the brief, and show them beside r2c's on the results
   page and in the summary.
2. Turn on Response's own solve of a stage. Keep the owner's "carry on" override in
   force explicitly for the cases where it would otherwise end as Response does. Report
   r2c's run time per case before and after, in the summary.
3. Budget: about three hours of work, used as CLAUDE.md says.

If the threshold is reached or the plateau rule is met, stop and ask before starting the
finishing steps.

The measured values (recorded by the developer at the owner's instruction; measured,
`python tools/heldout.py repeat ARCHIVE --record`, the owner's machine, 2026-11-25;
`heldout/repeatability.json`): cases of the held-out set on which Response with every
concrete strength raised by 0.05 % is inside target against Response as it is, on every
check of the priority, and the threshold that follows (that score less 3 points).

<!-- repeat:begin -->
<!-- Generated by tools/heldout.py summary. Do not edit: rerun it. -->

| Area | Priority | Response against itself | Threshold |
|---|---|---:|---:|
| Moment and axial | 1 | 20 of 27 (74 %) | 99 % (kept by the owner, 2026-11-26) |
| Moment and axial | 2 | 27 of 27 (100 %) | 97 % |
| Moment and axial | 3 | 27 of 27 (100 %) | 97 % |
| Shear | 1 | 27 of 28 (96 %) | 93.4 % |
| Shear | 2 | 18 of 28 (64 %) | reported only |
| Shear | 3 | 25 of 28 (89 %) | 86.3 % |
| Shear | 4 | 25 of 27 (93 %) | reported only |

Measured 2026-11-25. Cases: moment and axial 27 (0 not solved by Response after the change, counted outside), shear 28 (0 not solved by Response after the change, counted outside).
<!-- repeat:end -->

**2026-11-26**, in answer to the questions of the summary after increment 6:

1. Response's own solve of a stage stays on. Work on the stage that does not settle at
   the fall of load when the web cracks (rectangular beams under moment and shear).
2. Priority 1 without shear keeps a threshold of 99 %; the threshold from Response
   against itself applies to the other cells.
3. Speed is now part of the threshold: on every case, r2c's run time is no more than
   r2x's on the same input, measured on the same machine. Measure r2x's time per case
   on the development set first and record it. Make r2c faster without changing a
   single result: every development record must be identical before and after a
   speed change, and the test that checks it goes in with the first speed commit.
4. Budget: about three hours of work, used as CLAUDE.md says. Split it between
   accuracy with shear and speed as you judge best.

If the threshold is reached or the plateau rule is met, stop and ask before starting the
finishing steps.

**2026-11-26**, in answer to the questions of the summary after increment 7:

1. Live targets: shear priority 1 and priority 3 against their thresholds. Shear
   priority 2 and speed become reported measures, not targets: record r2c's standing
   against Response's own score and against r2x's time in the brief and in the known
   limitations.
2. Plateau: stop when an increment gains nothing on a live target.
3. Speed: r2x reading every stage is the bar for the reported measure. No compiled
   routines.
4. r2x failing on 8 cases at its default setting is noted as a finding for r2x in
   docs/deviations.md; nothing changes in r2c.
5. Budget: about three hours of work, used as CLAUDE.md says.

If the live targets are met or the plateau rule fires, stop and ask before the finishing
steps.

r2c's standing on the two reported measures (recorded by the developer at the owner's
instruction; generated by `python tools/heldout.py summary` from `heldout/totals.json`,
`heldout/repeatability.json`, the development results and `tests/oracle/r2x-times.json`):

<!-- standing:begin -->
<!-- Generated by tools/heldout.py summary. Do not edit: rerun it. -->

- Shear, priority 2, held-out set (increment 7, 2026-11-26): r2c 12 of 28 (43 %); Response against itself 18 of 28 (64 %).
- Speed, development cases without shear, r2x reading every stage: r2c no slower on 104 of 104; medians 2.1 s (r2c) and 73.8 s (r2x); the slowest case 0.1 times r2x's.
- Speed, development cases with shear, r2x reading every stage: r2c no slower on 16 of 60; medians 67.8 s (r2c) and 50 s (r2x); the slowest case 6.4 times r2x's.

<!-- standing:end -->

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
