# The end-of-phase review: what the owner is shown

The owner's specification (2026-11-24, agreed in chat) of the review at the end of phase A,
and of the same review at later milestones. It is built as meta-development, with the owner,
after the last step of the phase. It replaces reading the dashboard check by check: progress
between steps is now a few per cent on a handful of checks, and the important things are
hard to see there.

The review is a generated page of the results site ("Review"), built from the run of record
like the rest of the site, so it stays current into phase B. A short copy of its top two
parts goes in `docs/summary.md`.

## 1. The verdict (one screen)

A grid: rows are the load families (moment and axial; shear), columns are the tiers (Must,
Should, Could). Each cell says *met*, *met with accepted deviations*, or *not met*, with the
number of cases. It answers "did the phase do what it set out to do?" before anything else.

Under it, two small things that show progress again:

- **The trend:** the tier counts at the run of record of each step of the phase (A-1, A-2,
  …), rebuilt from git, as one small chart.
- **What changed since the last review:** only the checks that changed side, not every
  number.

## 2. The deviations, worst first

A list of the deviations outside target, one entry per **cause**, ranked so that the list
starts with what matters most and works down.

**Ranking.** By tier first (Must, then Should, then Could), then by size. Size is the
deviation as a multiple of its target (7 % on a 5 % target is 1.4×), after the
printed-precision floor, so that a large percentage on a chart of next to nothing does not
outrank a real miss.

**One entry per cause.** Instances with the same cause (for example the flat peak, D66) are
one entry, shown through its worst instance, with "and N more like this" and their cases
and range. Without this one cause fills the list.

**The cap.** At most 20 entries. Below them, one line gives the counts by tier and cause of
everything not itemised, and of the Won't tier, so that nothing is hidden.

**Each entry:**

- **Heading:** a plain name for the cause, tier, size (× target), number of cases.
- **The worst instance:** case, view or check, stage, r2c's value and Response's, and the
  key features of the two responses that show the difference (peak load and curvature,
  cracking, a fall of load, where the response ends), as few as tell the story.
- **One chart:** r2c over Response for the worst instance, with the stage marked. The
  owner judges on charts; this is the one chart for this cause.
- **The reason**, marked by what it rests on:
  - *measured*: by a diagnostic, named, with its number (for example: in Response's own
    state r2c is within 0.3 %, so the path differs, not the rule; `tools/startfrom.py`,
    `tools/flowset.py`, `tools/sources.py`);
  - *read*: a rule taken from the binary, with its address;
  - *inferred*: a plausible explanation not tested. Shown so it stands out: these are the
    ones to question.
- **The independent assessment** (below), and whether it agrees.
- **Status and the decision asked for:** the D-numbers that accepted it, if any, and what
  the owner is asked now (keep it accepted, make it a named limitation, an owner's
  override, take it up again, or move the check to another tier).

Deviations already accepted stay in the list, marked: the point of the review is to decide
them again, together.

## 3. The independent assessment

The developer that built r2c also explains its deviations, and has a reason to explain
them away. So each entry's reason is assessed a second time by a separate agent that has
not seen the development:

- **What it gets:** for each entry, the evidence only: the worst instance and the others
  like it, the two responses, the outputs of the diagnostics, the rule and its address
  where one is claimed, and the targets in `docs/acceptance.md`. **Not** the logs,
  `docs/status.md`, the summary's decisions or the developer's reason.
- **What it writes:** its own reason, marked measured, read or inferred as above, and
  whether the evidence supports the developer's reason, contradicts it, or does not
  decide it.
- **Where the two disagree**, the entry says so in its heading, and it is raised in the
  review whatever its rank.

The independent assessment is generated with the page and kept beside it; the developer
does not edit it.

## What the review is not

It does not change a target, a measure or a decision by itself. The owner's answers are
recorded in `docs/summary.md` as for any decision.
