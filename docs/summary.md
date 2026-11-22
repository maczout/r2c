# r2c: the owner's summary

**Read this first.** The one page the owner reads each session: where r2c stands, what
"finished" means, and every decision that is open or has been made. The developer keeps it
current at the end of every session (CLAUDE.md, "Ending a session"). Everything else in
`docs/` is the developer's working record and backs this page; it does not replace it.

Last updated: 2026-11-22, by the owner and the developer together (meta-development).

## Aim

A really good sectional response calculator, interchangeable with r2x. Completion is judged
against Response-2000 **as documented** (its manual and Bentz's thesis), not against
everything the 1.9.7 binary does. Where the documents and the binary differ, that is put to
the owner (a decision below), not settled by reading the binary. Bells and whistles are built
outside r2c and r2x. (Owner, 2026-11-22.)

## Phases

| Phase | What | State |
|---|---|---|
| **A. Develop the kernel** | Newbeam only, varied in its loads (M, −M, N, tension, N + M, M/V, V alone, constant loads first). Other sections, reinforcement, material models and units are parked. | **Now.** Next: reset the working set (D16, D18, D19) |
| **B. Validate and refine** | The parked cases come back; the test set and targets are reviewed; r2c is held to them. | Not started. Starts when Phase A meets its exit criteria (D1, D2). |

## Progress against the Phase A exit criteria

On the 17 Newbeam cases that vary only the load, cases inside target. Counted by hand from
the generated `docs/verification-results.md` (sixth verify run of 2026-11-21). The next
change to `tools/report.py` should write this table itself, so that it can't drift.

| Check | Inside, of 17 | Exit tier (D1, D2) |
|---|---:|---|
| Peak | 17 | Must |
| Rising branch | 16 | Must |
| Shape | 13 | Must |
| Post-peak | 10 | Should, without shear |
| Detail views | 1 | Must for stress state under moment and axial load |

What keeps the misses outside: one rising branch (M/V = 0.5 m) and four shapes (tension,
M/V = 0.5 m and 2 m, V alone), all at falls of load or at the end of a response; views mostly
by one point of the principal tensile stress chart (D13 first).

## Decisions

Numbered once and never renumbered. The developer adds a question here, with a suggested
answer, instead of leaving it only in a session log; a log refers to it by number. The owner
answers here (or in conversation, and the developer records it here with the date).

**Status:** *decided* (owner, with date) · *suggested* (the developer's answer, awaiting the
owner) · *open* (no suggestion yet).

### Steering

| # | Question | Status | Answer |
|---|---|---|---|
| D1 | What "finished" means for Phase A | decided, owner 2026-11-22 | *Must:* peak, rising branch and shape inside on every case. *Should:* the endings of moment (and axial) responses inside on every case. *Won't:* shear endings; recorded as known deviations. |
| D1a | Reading of D1: "shape" for a shear case leaves out how the response ends, since the ending is a Won't | suggested | Yes |
| D2 | Detail views and post-peak: chase them? | decided, owner 2026-11-22 | *Must:* views of the stress state under moment and axial load. *Should:* views related to shear. *Could:* views related to cracking. |
| D3 | Shear endings: chase further or accept? | decided, owner 2026-11-22 | Accept: see D1 (Won't). |
| D20 | `docs/acceptance.md` still says "where r2c and Response differ, Response is right", with no qualifier | suggested | Reword to "Response as documented is right; undocumented solver behaviour is not cloned", and add the tiers of D1 and D2. The owner's file: the owner makes the change. |

### Scope

| # | Question | Status | Answer |
|---|---|---|---|
| D4 | Draped tendons (rule not found; effect under 0.1 %) | decided, owner 2026-11-22 | Out of scope |
| D5 | Hsu softening models with Tamai tension stiffening | suggested | Out: a research feature, not the calculator |
| D6 | A shape with no outline (Response cannot solve it; r2c builds it) | suggested | Reject it, as Response does |
| D7 | Inputs Response rejects are input errors in r2c | suggested | Confirm |
| D8 | Two added scope statuses, "no effect" and "not solvable" | suggested | Confirm |
| D9 | Response's program folder (`rebar.dat`, `r2k.r2k`): should r2c read it? | suggested | No: outside the calculator |
| D10 | Compression softening 4 ("Unsupported Method") | suggested | Out: undocumented |
| D11 | Interlocking hoops analysed as stirrups (inferred, within 0.8 %) | suggested | Confirm |
| D12 | Circular column under axial load alone after its peak (C2) | decided, owner 2026-11-22 | Looks wrong in Response: not cloned; r2c's uniform post-peak stands. Pure N stays in Phase A on Newbeam. |
| D17 | Which document defines a complete feature | suggested | The manual (thesis Appendix A) for which features exist; the thesis for how they calculate |
| D18 | Features built beyond the documented set (less common softening models, segmental steel, …) | decided, owner 2026-11-22 | Remove the code |

### Measurement and test set (meta-development)

| # | Question | Status | Answer |
|---|---|---|---|
| D13 | Stage matching: a 0.5 % change in r2c's load can switch the matched stage and flip 11 view checks | suggested | Fix the measure before any work on views |
| D14 | F1: Response's cracking-under-compression rule inside the node | suggested | Yes, after D13 |
| D15 | The generated results JSON is committed on every run (~80,000 lines) | suggested | Build it in CI instead of storing it |
| D16 | The test set has grown to 85 cases | decided, owner 2026-11-22 | Develop on Newbeam; the rest is parked until Phase B |
| D19 | Parked fixtures: delete, or keep and not run by default? | suggested | Keep them, not run by default |

### Closed by the owner's stance

Settled by "no structural assessment of results" (owner, 2026-11-21) and need no answer: is a
peak after a fall of load the one that matters (Response's largest is used); dm-n1n's failure
mode; whether r2c's states beyond Response's failure are real; Liping LB1 at +1.8 %; findings
H and I (views are now covered by D2).

## Risks

- **Review load.** Development runs faster than the owner can review it. This page is the
  answer: one page per session, not one log per step.
- **Unattended runs** without a scoped GitHub token or branch protection on `main` (setup,
  not yet done).
- **Newbeam only** leaves the paths built for steps in width, strands and hoops unexercised
  until Phase B.
