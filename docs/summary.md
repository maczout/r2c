# r2c: the owner's summary

**Read this first.** The one page the owner reads each session: where r2c stands, what
"finished" means, and every decision that is open or has been made. The developer keeps it
current at the end of every session (CLAUDE.md, "Ending a session"). Everything else in
`docs/` is the developer's working record and backs this page; it does not replace it.

Last updated: 2026-11-23, by the developer, at the end of the session that carried out
the owner's rule on unstable views (D54; log 2026-11-23-02).

**What changed.** Only the measure; r2c calculates what it did. The rule of D54 is in
use: at each compared stage Response's own view is set against the blend of its views at
the stage before and the stage after, and where it departs by more than the 5 % target
the check is shown with Response's departure beside r2c's difference and counted neither
inside nor outside. For that, Response's views at the neighbouring stages of the 29 cases
were added to the fixtures (4.5 to 9.2 MB).

**What the rule does, on the 29 cases** (figures and the list of Musts in "The rule on
unstable views" below):

- **It leaves 318 of the 1,554 view checks unassessed, one in five.** 286 of them were
  inside before; 32 were outside.
- **Must: 64 checks unassessed, every one of them inside before** (r2c within 1.7 % of
  Response at each). The seven Must checks that are outside stay outside: they are the
  column under N alone at its last stage (the owner's override, C2), which has no stage
  after it and so is not tested.
- **Should: 27 misses are no longer counted,** on five cases; three more cases meet the
  Should (24 of 29, from 21). Could: five misses no longer counted (26 of 29, from 23).
  These include known deviations: the column with shear at its peak (D47) and the stage
  of V alone compared across cracking (D32) are now unassessed, not misses.
- **Why so many:** views are compared at the features of the curve (cracking, a fall of
  load, the peak), and those are the places where Response's views change most from one
  stage to the next. Put to the owner as D56.

**Found on the way: Response does not repeat itself on the I-girder with shear.** All 29
cases were captured again from Response to check the new fixtures. 28 came back byte
for byte. The I-girder with shear came back with 25 stages in three runs of four and
with the fixture's 15 in one. The 15 are all there in the 25, identical; ten more stages
sit on the rising branch between two of them. Nothing that is compared changes (D57).

**No decisions wait for the owner.** D55 to D57 answered 2026-11-23 (owner, after the
session): the rule is narrowed to spikes (D56), a measure change before step A-3; new cases
are captured three times (D57). Then material models (step A-3, D53).

## Aim

A really good sectional response calculator, interchangeable with r2x. **What exists** is
judged against Response-2000 as documented (the manual, Appendix A of Bentz's thesis).
**How it calculates** is the 1.9.7 program's, read from the binary: where the thesis and the
binary differ, the binary is followed without asking, apart from the owner's overrides in
`docs/acceptance.md` (D34). Bells and whistles are built outside r2c and r2x. (Owner,
2026-11-22.)

## Phases

| Phase | What | State |
|---|---|---|
| **A. Develop the kernel** | On a development set that widens step by step (D41): Newbeam varied in its loads (the 17 cases below), then one variable at a time — shape (step A-1, the seven Quick Define cases), reinforcement (step A-2, five cases), then material models, units and material factors. What is not yet in the set stays parked. | **Now.** Steps A-1 (shape) and A-2 (reinforcement) are worked through (2026-11-23). On the 29 cases peak and rising branch are met; shape on 26 and the Must views on 14 of 15. The four misses are known deviations or the owner's override (D32, D36, C2; the I-girder with shear, part of the shear profile iteration, D50). The Should on shear views is met on 7 of the 14 shear cases |
| **B. Validate and refine** | The parked cases come back; the test set and targets are reviewed; r2c is held to them. | Not started. Starts when the development set has widened to cover the scope and meets the exit criteria (D1, D2). Then the test set and targets are reviewed with the owner. |

### The development set

**Newbeam (17 cases).** Newbeam as Response defines it, in SI units, with no material factors; only the loads
differ. Confirmed against the fixtures on 2026-11-22: 17 cases.

| Without shear (8) | With shear (9) |
|---|---|
| M | M + V at M/V = 0.5 m |
| −M | M + V at M/V = 1 m |
| N (compression) | M + V at M/V = 2 m |
| N (tension) | V alone |
| N + M increasing together | constant N (−500 kN), then V |
| constant N (−2000 kN), then M | constant N (−500 kN), then M + V |
| constant N (+200 kN), then M | N + M + V increasing together |
| no load | constant M (−50 kNm), then M + V |
| | constant V (50 kN), then M |

**Step A-1, shape (7 cases, owner 2026-11-22, D41):** the Quick Define sections already among
the fixtures — T-beam under M and −M (`tbeam-m`, `tbeam-negm`); column under N, N₀ + M and
M + V (`column-nonly`, `column-n4000-m`, `column-mv`); I-girder under M and M + V
(`igirder-m`, `igirder-mv`). The column under N alone carries the owner's override after its
peak (C2, D12).

All seven have joined the set (owner, 2026-11-22, D44).

**Step A-2, reinforcement (5 cases, proposed by the developer 2026-11-23 to the owner's
brief; D52).** The parked fixtures whose variable is the reinforcement, on shapes already
in the set. Moved into the set in a commit of their own.

| Case | Shape and loads | The variable it tests |
|---|---|---|
| `newbeam-bardep-m` | Newbeam, M | a prestrain of 1 mm/m on the bottom bars (ordinary steel, not strand) |
| `newbeam-bartherm-m` | Newbeam, M | a thermal strain of 0.5 mm/m on the bottom bars |
| `newbeam-nostirrups-mv` | Newbeam, M + V at M/V = 1 m | no transverse reinforcement |
| `newbeam-stirrupdep-mv` | Newbeam, M + V at M/V = 1 m | a prestrain of 1 mm/m on the stirrups |
| `column-interlock-mv` | Column, M + V | interlocking hoops in place of a single hoop |

Not proposed, though they vary the reinforcement: the segmental steel curve and the
draped tendons. r2c refuses both by the owner's decisions (D18, D4), so there is nothing
to bring to the tiers. "Stirrup depth" in the brief: the parked fixture of that name is
the prestrain on the stirrups (its input field is called `dep`); no parked case has
stirrups over part of the depth.

Parked, kept and not run by default (56 cases): other materials, units,
material factors, More Detail, no input, the other cases on the T-beam, column and
I-girder, and Response's sample inputs. They sit in a folder of their own and can be run on
request. Eleven of them need something that has been removed, and r2c refuses them: five
since the removals of D18, six more (all on Response's sample inputs) since D23.

## Progress against the Phase A exit criteria

Cases inside target, counted by `tools/targets.py --counts` (measured). "Step A-1c" is
that step's run of record on the 24 cases. "Before" is the run after parts 1 and 2 of
step A-2, on the same 24: the only change to what r2c calculates is Response's handling
of the shear strain profile (D49). "Now" is the run of record of step A-2
(`docs/verification-results.md`) on the 29 cases.

| Check | Step A-1c (24) | Before (24) | Now (29) | Exit tier (D1, D2, D27) |
|---|---:|---:|---:|---|
| Peak | 24 | 24 | 29 of 29 | Must: met |
| Rising branch | 23 | 24 | 29 of 29 | Must: met. M/V = 0.5 m came back inside with D49 (9.9 to 3.6 %) |
| Shape | 21 | 21 | 26 of 29 | Must (a shear case's ending left out: D25). Two misses are known deviations (D32, D36); the third is the I-girder with shear (the shear profile iteration, D50) |
| Views of the stress state, without shear | 12 of 13 | 12 of 13 | 14 of 15 | Must. The miss is the column under N alone after its peak (the owner's override, C2) |
| Post-peak, without shear | 12 of 13 | 12 of 13 | 14 of 15 | Should. The miss is the column under N alone (C2) |
| Views related to shear, and stress-state views with shear | 14 of 24 (2 of the 11 with shear) | 16 of 24 (4 of 11) | 21 of 29 (7 of the 14 with shear); **24 of 29 (10 of 14) with the rule of D54** | Should, not met |
| Views related to cracking | 20 | 18 | 23 of 29; **26 of 29 with the rule of D54** | Could |

The 24 cases are held by the no-regression bound: between "before" and "now" no check
on them changed side.

### The rule on unstable views (D54), before and after

Carried out 2026-11-23 as a change to the measure (log 2026-11-23-02). "Before" and
"after" are the same run of r2c on the 29 cases, counted without and with the rule; r2c's
differences from Response are the same in both, number for number (measured: the run of
record against step A-2's). The generated figures are in `docs/verification-results.md`
("View checks by tier", "Detail views where Response is unstable"); the results page
shows the same.

**Checks, tier by tier** (measured, `python tools/unstable.py VERIFY_OUT`). A check is one
view at one compared stage of one case; the last stage of a shear case is left out (D40).

| Tier | Checks | Before: inside | Before: outside | After: inside | After: outside | After: unassessed |
|---|---:|---:|---:|---:|---:|---:|
| Must | 376 | 369 | 7 | 305 | 7 | 64 |
| Should | 808 | 764 | 44 | 598 | 17 | 193 |
| Could | 370 | 361 | 9 | 305 | 4 | 61 |

Of the 1,554 checks, 1,216 were tested. The other 338 have no stage on both sides (the
last stage of a case without shear, and the case with no load) or, twice, a view whose
lines could not be blended (the shrinkage and thermal strain at the peak of the two −M
cases, where r2c's difference is nothing); they stay assessed, as the rule says. Where the unassessed checks are:
155 at cracking, 104 at a peak, 59 at a fall of load.

**Cases, tier by tier** (measured, `python tools/targets.py VERIFY_OUT --counts`, and
with `--before-d54`).

| Tier | Before: cases inside | After: cases inside | Cases that changed |
|---|---:|---:|---|
| Must (views of the stress state, without shear) | 14 of 15 | 14 of 15 | None. The miss is the column under N alone (C2) |
| Should | 21 of 29 | 24 of 29 | Column with shear (its peak, D47), I-girder with shear (transverse bond at its peak, D46), N + M + V increasing together (transverse bond at cracking) |
| Could | 23 of 29 | 26 of 29 | Column with shear, tension (D36), V alone (D32) |

Peak, rising branch, shape and post-peak are not touched by the rule and stand as in the
table above.

**The misses that are no longer counted** (32 checks; r2c's difference and Response's
departure for each are in the generated report): the column with shear at its peak, 9
Should and 2 Could; M/V = 0.5 m at its fall of load, 4 Should, and at its peak, 3; V
alone at its fall of load, 9 Should and 2 Could; the I-girder with shear, transverse
bond at its peak; N + M + V increasing together, transverse bond at cracking; tension,
the diagonal crack spacing at cracking. They are still listed in `docs/status.md` as
known deviations, now marked as unassessed.

**Every Must check left unassessed** (64, on 12 of the 15 cases without shear; for the
owner's review, as the rule asks). Each entry: Response's departure from the blend of
its neighbouring stages, in % of the chart's largest value, then in brackets r2c's
difference from Response at that stage. Measured,
`python tools/unstable.py VERIFY_OUT --list --tier must`.

| Case | Response's stage | View: Response's departure % (r2c's difference %) |
|---|---|---|
| `column-n4000-m` | 28 (cracking) | principal tensile stress 5.0 (0.4) |
| `column-n4000-m` | 45 (peak) | principal tensile stress 20.3 (0.8); long reinf stress at crack 5.2 (0.0) |
| `igirder-m` | 32 (cracking) | principal tensile stress 37.7 (0.1) |
| `igirder-m` | 63 (peak) | principal tensile stress 30.1 (0.1); longitudinal concrete stress 6.0 (0.0); principal compressive stress 6.0 (0.0) |
| `newbeam-bardep-m` | 14 (cracking) | principal tensile stress 16.1 (1.2) |
| `newbeam-bardep-m` | 49 (peak) | principal tensile stress 34.7 (0.1); longitudinal concrete stress 5.1 (0.0); principal compressive stress 5.1 (0.0) |
| `newbeam-bartherm-m` | 17 (cracking) | principal tensile stress 36.4 (0.0) |
| `newbeam-bartherm-m` | 44 (peak) | principal tensile stress 28.9 (0.2); longitudinal concrete stress 10.4 (0.0); principal compressive stress 10.4 (0.0); long reinforcement stress 6.3 (0.0) |
| `newbeam-m` | 16 (cracking) | principal tensile stress 15.2 (0.0); longitudinal concrete stress 9.8 (0.0) |
| `newbeam-m` | 56 (peak) | principal tensile stress 35.5 (0.1); longitudinal concrete stress 7.7 (0.0); principal compressive stress 7.7 (0.0) |
| `newbeam-n2000-m` | 16 (cracking) | principal tensile stress 12.1 (1.0) |
| `newbeam-n2000-m` | 37 (peak) | principal tensile stress 6.3 (0.1) |
| `newbeam-negm` | 13 (fall) | longitudinal concrete stress 10.0 (0.0); principal tensile stress 9.1 (0.2); principal tensile strain 6.4 (0.0); longitudinal strain 5.6 (0.0) |
| `newbeam-negm` | 14 (cracking) | long reinf stress at crack 27.4 (0.0); longitudinal concrete stress 9.0 (0.0); principal tensile stress 8.9 (0.2); principal tensile strain 6.2 (0.0); longitudinal strain 5.5 (0.0) |
| `newbeam-nm` | 22 (peak) | long reinf stress at crack 46.9 (0.0); principal tensile stress 12.8 (1.7) |
| `newbeam-ntension-m` | 16 (fall) | longitudinal concrete stress 10.6 (0.0); principal tensile stress 7.9 (0.0) |
| `newbeam-ntension-m` | 17 (cracking) | long reinf stress at crack 25.3 (0.0); longitudinal concrete stress 21.6 (0.0); principal tensile stress 16.7 (0.1) |
| `newbeam-ntension-m` | 71 (peak) | principal tensile stress 43.0 (0.2); longitudinal concrete stress 31.0 (0.0); principal compressive stress 31.0 (0.0); long reinforcement stress 9.0 (0.0) |
| `newbeam-tension` | 13 (fall) | principal tensile strain 44.6 (0.0); longitudinal strain 29.6 (0.4); principal tensile stress 24.0 (0.5); longitudinal concrete stress 24.0 (0.5) |
| `newbeam-tension` | 25 (peak) | longitudinal concrete stress 10.1 (0.2); principal tensile stress 10.0 (0.2) |
| `tbeam-m` | 12 (cracking) | long reinf stress at crack 20.0 (0.0); longitudinal concrete stress 16.7 (0.3); principal tensile stress 16.3 (0.3) |
| `tbeam-m` | 61 (peak) | longitudinal concrete stress 32.2 (0.0); principal compressive stress 32.2 (0.0); principal tensile stress 30.0 (0.2) |
| `tbeam-negm` | 19 (fall) | principal tensile strain 22.2 (0.0); principal tensile stress 17.1 (0.2); longitudinal strain 16.7 (0.0); longitudinal concrete stress 13.2 (0.2) |
| `tbeam-negm` | 20 (cracking) | principal tensile stress 32.0 (0.1); longitudinal concrete stress 20.8 (0.0); long reinf stress at crack 13.0 (0.0); principal tensile strain 8.4 (0.0); longitudinal strain 7.2 (0.0) |

By view: the principal tensile stress 24, the longitudinal concrete stress 16, the steel
stress at a crack 6, the principal compressive stress 6, the principal tensile strain 5,
the longitudinal strain 5, the steel stress 2. Not on the list: the column under N alone
(its cracking stage and peak are steady; its last stage is not tested), N in compression
on Newbeam, and the case with no load.

**The readings** (D55). The rule's wording leaves three choices. What each moves
(measured, `python tools/unstable.py VERIFY_OUT --readings`):

| Choice | Reading in use | Other reading | What the other reading moves |
|---|---|---|---|
| The stage's place between its neighbours "along the control curve" | By distance along the curve, load and control value scaled as the curves are measured | By control value alone | 58 checks change (33 more unassessed, 25 assessed again); Must unassessed 79 |
| | | By load alone | 48 change (41 more, 7 again); Must unassessed 79 |
| | | Half way | 78 change (46 more, 32 again); Must unassessed 83 |
| A line that one neighbour draws and the other does not (the shear on the crack, 10 views) | Blended with nothing, so it comes in by degrees | Left out of the blend, so the stage's own line counts at full size | No check changes |
| How two views are blended when Response has re-layered the section between stages (most views) | By depth: at each depth where either has a point, the two values there | None measured: point by point is not possible when the points differ | — |

With every reading the seven Must misses stay and no Must miss becomes unassessed.

### Step A-2, part by part

| Part | What was done | Outcome |
|---|---|---|
| 1. Response's handling of the shear strain profile (D49) | Switched on; r2c's earlier update removed. Verify and report rerun | **Done.** 11 checks inside, 22 outside, as measured in the trial of step A-1c, check for check. No Must outside. The 22 are known deviations in `docs/status.md`: seven views at the peak of M/V = 0.5 m and two at its fall of load; eleven at one stage of V alone, compared across cracking (D32) |
| 2. The depth lead (D50), with the oracle | The I-girder with shear captured from Response at M/V = 0.99 m and 1.01 m; diagnostics, fixtures not committed | **Lead dropped.** At 1.01 m Response's stages are those of 1 m: no stage where the top cracks close. At 0.99 m a regular stage of its (shorter) step falls where the top is still cracked, but it puts in no stage there either (D51). "The shear profile iteration" is recorded as one known deviation, with what was read and what was not |
| 3. Reinforcement: five cases into the set | Moved in a commit of their own. Musts first | **Musts met on all five as they were.** One Should outside: transverse bond at the peak with prestrained stirrups, 52.8 %. Two rules read from the program brought it to 2.7 % (below). No check on the 24 moved |
| 4. Which known deviations recur | Table below | Only how a shear response ends |

**The two rules of part 3**, both about what a stage reports, not about the solve
(`docs/kernel.md`, "A node with next to no shear strain" and "The shear charts").

- r2c took the stirrups to reach a hair beyond their end when it drew the bond chart, so
  a prestress that stops at the end looked like a change of stress along the stirrup.
  Corrected to the program's test.
- Response treats a node that has next to no shear strain as having no stirrups at all.
  With ordinary stirrups that cannot be seen. With prestrained stirrups its Stirrup
  Stress chart shows nothing at such a node, and its bond chart follows. r2c now reports
  such nodes the same way. Which nodes these are near the bottom face changes from stage
  to stage in Response itself, so its own bond chart there jumps between stages (0.1 to
  38 MPa); agreement at one stage is partly luck, and is not promised at another.

With both, r2c's bond rule gives Response's bond chart from Response's own stirrup
stress within 0.4 % at every stage of that case (355 % off at the peak before).

### The five new cases

| Case | Musts | Should | What is left |
|---|---|---|---|
| Bars with a prestrain, M | met | met | Nothing |
| Bars with a thermal strain, M | met | met | Nothing |
| No stirrups, M + V | met (peak −0.02 %, rising branch 0.02 %) | met | How the response ends (a Won't) |
| Prestrained stirrups, M + V | met (peak +0.04 %, rising branch 0.03 %) | met since the two rules above | How the response ends (a Won't) |
| Interlocking hoops on the column, M + V | met (peak −0.11 %, rising branch 0.23 %) | **met, at the peak too** | How the response ends (a Won't) |

The seven cases of step A-1 stand as they did: five with nothing left, the column with
shear and the I-girder with shear under "the shear profile iteration" (D50).

### Which known deviations recur

The owner asked for this (D41): a deviation that recurs is likely Response's solver; one
that does not was a quirk of one case.

| Known deviation | On the seven shape cases (step A-1) | On the five reinforcement cases (step A-2) |
|---|---|---|
| How a shear response ends (a Won't, D1) | Recurs on both shear cases | **Recurs on all three shear cases.** Response's ends falling on a stage far down (25 to 74 % of the peak); r2c's ends just under its peak (95, 96 %) or stands still (the column) |
| The shear profile iteration: views on a flat peak (D47) | The column with shear | **Does not recur**, on the same column with interlocking hoops: every view at the peak is inside |
| The shear profile iteration: a stage Response does not put in (D48) | The I-girder with shear | Not tested: no new case is on the I-girder |
| D32: a fall of load just under the 2 % the measure counts from (V alone) | Does not recur | Not tested: no new case is under V alone |
| D35, D36, C2 | D35 does not recur; D36 not tested; C2 is that case | D35 does not recur (both cases without shear are inside at their last stage); D36 and C2 not tested |
| D38: a limit line of shear on the crack that one program draws and the other does not | Does not recur | Does not recur |
| D39: the stirrups' memory of yielding (off) | Does not recur | No miss on the new cases points to it; not measured switched on |
| D46: a spike of transverse bond at the end of the stirrups in a stage not converged | The I-girder with shear | Does not recur. The bond miss with prestrained stirrups had another cause and is resolved |
| D49: views at the peak of M/V = 0.5 m | (came with D49) | Does not recur |

Every rule taken over is in `docs/kernel.md` with its source.

Known deviations are in `docs/status.md`: how shear responses end (a Won't, D1), the
circular column under axial load alone, which is not cloned (D12), the fall of load
before the peak under V alone (D32, with the stage compared across cracking since D49),
tension's shape (D36), the views at the peak of M/V = 0.5 m (D49), what is left of the
checks that came with the longitudinal crack spacing table (D46), and the shear profile
iteration (D50), with three effects: the views of the column with shear at its peak
(D47), the shape of the I-girder with shear (D43, D48) and the parked I-girders with
shear that end early.

### What was removed (D18)

Each item of the scope inventory is now marked as documented or not, with the manual's page
(`docs/scope.md`). Removed, and now refused as out of scope: draped tendons (D4); the Hsu
softening models combined with Tamai tension stiffening (D5); compression softening 4 (D10),
16 and 17 (later than the manual); a segmental stress-strain curve for reinforcing steel. A
shape with no outline is an input error (D6). Response's program folder was never read, and
is not (D9). Three things were unclear and were put to the owner: the eleven softening models the manual names are kept (D21); 1.9.7's defaults are followed (D22); several sections in one file and the horizontal tie are refused (D23, done 2026-11-22).

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
| D1a | Reading of D1: "shape" for a shear case leaves out how the response ends, since the ending is a Won't | decided, owner 2026-11-22 (suggestion approved) | Yes |
| D2 | Detail views and post-peak: chase them? | decided, owner 2026-11-22 | *Must:* views of the stress state under moment and axial load. *Should:* views related to shear. *Could:* views related to cracking. |
| D3 | Shear endings: chase further or accept? | decided, owner 2026-11-22 | Accept: see D1 (Won't). |
| D20 | `docs/acceptance.md` still says "where r2c and Response differ, Response is right", with no qualifier | decided, owner 2026-11-22 (suggestion approved) | Reworded: "Response as documented is right; undocumented solver behaviour is not cloned"; the tiers of D1 and D2 added as the phase A exit criteria. Done 2026-11-22. The first half is superseded by D34. |

### Scope

| # | Question | Status | Answer |
|---|---|---|---|
| D4 | Draped tendons (rule not found; effect under 0.1 %) | decided, owner 2026-11-22 | Out of scope |
| D5 | Hsu softening models with Tamai tension stiffening | decided, owner 2026-11-22 (suggestion approved) | Out: a research feature, not the calculator |
| D6 | A shape with no outline (Response cannot solve it; r2c builds it) | decided, owner 2026-11-22 (suggestion approved) | Reject it, as Response does |
| D7 | Inputs Response rejects are input errors in r2c | decided, owner 2026-11-22 (suggestion approved) | Confirm |
| D8 | Two added scope statuses, "no effect" and "not solvable" | decided, owner 2026-11-22 (suggestion approved) | Confirm |
| D9 | Response's program folder (`rebar.dat`, `r2k.r2k`): should r2c read it? | decided, owner 2026-11-22 (suggestion approved) | No: outside the calculator |
| D10 | Compression softening 4 ("Unsupported Method") | decided, owner 2026-11-22 (suggestion approved) | Out: undocumented |
| D11 | Interlocking hoops analysed as stirrups (inferred, within 0.8 %) | decided, owner 2026-11-22 (suggestion approved) | Confirm |
| D12 | Circular column under axial load alone after its peak (C2) | decided, owner 2026-11-22 | Looks wrong in Response: not cloned; r2c's uniform post-peak stands. Pure N stays in Phase A on Newbeam. |
| D17 | Which document defines a complete feature | decided, owner 2026-11-22 (suggestion approved); amended by D34 | The manual (thesis Appendix A) for which features exist; ~~the thesis~~ the binary for how they calculate (D34) |
| D18 | Features built beyond the documented set (less common softening models, segmental steel, …) | decided, owner 2026-11-22 | Remove the code |
| D21 | Compression softening models that the manual names but that neither the manual nor the thesis gives a rule for (eleven of them: Vecchio-Collins 1982, 1992-A and 1992-B, Mehlhorn, Maekawa, Noguchi, Belarbi-Hsu, Collins 1978, Kaufmann-Marti, Hsu-Zhang 1998, Hsu 1993). Their rules in r2c were read from the binary. D18 names "less common softening models" for removal; the manual lists them, so they were kept | decided, owner 2026-11-22 | **Keep them.** Being named in the manual counts as documented; their rules from the binary stay. (The developer had suggested removing them.) |
| D22 | The default compression softening of Response 1.9.7 (Collins-Bentz 2011) is later than the manual and the thesis, so by D17 it is not documented. Every case uses it. For Newbeam's concrete it is the thesis' own equation; they differ above 57 MPa. The automatic tensile strength is another default where the program differs from the thesis | decided, owner 2026-11-22 (suggestion approved) | Keep. Where a default of Response 1.9.7 differs from the 2000 documents, r2c follows the program, because the oracle runs with its defaults |
| D23 | Two things an input file can carry that the manual does not have, and that r2c reads as the nearest documented thing with no code of their own: several sections in one file (the first is read), and the horizontal tie (read as a stirrup). Both occur only in Response's sample inputs, which are parked | decided, owner 2026-11-22 | **Refuse them now**, with a reason, as for the other removals (D24). (The developer had suggested leaving them until phase B.) **Done 2026-11-22:** the six parked cases on Response's sample files that hold several sections are refused and kept |
| D24 | Reading of "out of scope" and "remove" (D4, D5, D10, D18): r2c refuses such an input and says why, where before it read a drape and ignored it, or ran a Hsu model with Tamai tension stiffening as two independent models | decided, owner 2026-11-22 (reading confirmed) | Yes: refuse, do not ignore silently |

### Measurement and test set (meta-development)

| # | Question | Status | Answer |
|---|---|---|---|
| D13 | Stage matching: a 0.5 % change in r2c's load can switch the matched stage and flip 11 view checks | decided, owner 2026-11-22 (suggestion approved) | Fix the measure before any work on views. **Done 2026-11-22:** a stage is matched between the same features of the two curves. Without shear only the no-load case's first stage was re-matched, and no check changed; with shear ten stages, mostly after the peak, are now matched to like states (one had been matched to r2c's stage 1) |
| D14 | F1: Response's cracking-under-compression rule inside the node | decided, owner 2026-11-22 (suggestion approved) | Yes, after D13. **Done 2026-11-22** (A2 part 2) |
| D15 | The generated results JSON is committed on every run (~80,000 lines) | decided, owner 2026-11-22 (suggestion approved) | Build it in CI instead of storing it |
| D16 | The test set has grown to 85 cases | decided, owner 2026-11-22 | Develop on Newbeam; the rest is parked until Phase B. Amended by D41: the set widens step by step within phase A |
| D19 | Parked fixtures: delete, or keep and not run by default? | decided, owner 2026-11-22 (suggestion approved) | Keep them, not run by default |
| D25 | The shape check still counts how a shear response ends, against D1a. Two cases (M/V = 0.5 m and 2 m) are outside on shape for that reason alone | decided, owner 2026-11-22 (reading confirmed) | Change the measure so that shape leaves out the ending for shear cases. **Done 2026-11-22:** shape 13 → 15 of 17 |
| D27 | Which of the 21 detail views are Must, Should or Could | decided, owner 2026-11-22 | Must: the stress-state views on cases without shear, including steel stress at a crack and the principal tensile strain and stress (the owner's choice). Should: shear views, and stress-state views on shear cases. Could: cracking views. Lists in `docs/acceptance.md` |
| D28 | Bounds, in case a Must is harder than it looks | decided, owner 2026-11-22 | Two grounded approaches per part at most, no tuning to fit, no regression; on stopping, put it to the owner with options. In `docs/acceptance.md` |

### Left by increment A2 (answered 2026-11-22)

| # | Question | Status | Answer |
|---|---|---|---|
| D29 | Reading of the no-regression bound (D28: "no Must view that is inside may go outside"). With Response's layering, principal tensile stress on M went from 18.2 to 0.0 % at the peak and from 4.2 to 7.2 % at the last stage. The developer read the bound view by view on a case, as the report counts it: that view on M was outside before and is outside now, so the layering was kept. Stage by stage it is a regression | decided, owner 2026-11-22 | **Confirmed: the binary's layering stays.** Under D34 the stage left on M (7.2 %) is not a known deviation; it is work in increment A3. (The developer had suggested: Confirm, and accept that stage as a known deviation. At that stage r2c has Response's points, and gives Response's forces in Response's own state; the two states differ by 0.005 mm/m of strain, less than Response's own solve leaves unbalanced, and next to a crack front that is 7 % of the chart. Other options: take the layering out again (the four stages that came inside go back out), or measure this view differently at a crack front (meta-development, with the owner)) |
| D30 | Where no bar crosses the cracked zone (under N + M the zone is below the bottom bars), the thesis says the concrete tension is not reduced; Response 1.9.7 reduces it to the floor it keeps after cracking. r2c follows the thesis. This is the one principal-tension miss left that has a rule behind it: N + M at cracking, 51.5 % | decided by D34 (owner 2026-11-22) | **Follow the program** (D34: the binary is followed where it and the thesis differ), as for the defaults in D22: the oracle runs the program. Tried and not kept: 51.5 to 0.3 %, nothing else moves, the Must views go to 6 of 8. One line of code |
| D31 | Tension's shape (A2 part 4, stopped). Response's curve has one more rising point before the fall at cracking than r2c's (276.2 against 274.5 kN; r2c's own limit is about 275.6), and the measure reads the order of cracking and the fall from that point. Response's solve carries on with a state it has not balanced; r2c finds none there | decided, owner 2026-11-22 | **Clone it.** Under D34, cloning how Response's solve gives up at cracking under tension is allowed. It is work in increment A3, not a known deviation. (The developer had suggested: Accept as a known deviation. Other options: read cracking and a fall at the same step as one feature (a change to the measure, with the owner); or clone how Response's solve gives up (a third approach). Since D34 the stance no longer excludes this option: solver behaviour read from the binary is in) |
| D32 | V alone's shape (A2 part 5, no kernel change). r2c now has the fall of load before the peak, 1.9 % of the peak deep; Response's is 2.2 % and the measure counts a fall from 2 % | decided, owner 2026-11-22 | **Accept as a known deviation for now. No change to the measure.** (The developer had suggested: Accept as a known deviation, or count a fall in r2c's curve where Response has one at the same place and r2c's is within the 5 % target of it (a change to the measure, with the owner). No third approach is proposed: every check at that stage is inside target) |
| D33 | What comes after A2. With D29 to D32 answered as suggested and D30 carried out, the Musts left are −M's two views at its last stage, which follow from how −M ends (a Should, 20 %) | decided, owner 2026-11-22 | **Approved, extended: increment A3**, in this order: D30; the ending of −M with its two Must views; principal tensile stress on M at its last stage (D29); tension's shape (D31); if time allows, the views related to shear. The bounds of D28 apply to each part; an approach that reads the rule from the binary counts as one approach. The parked cases are run once before the end. (The developer had suggested: Next increment: the ending of −M, then the views related to shear (Should). Before phase B, look at the parked cases the changes of A2 moved (Risks)) |


### Left by increment A3 (new, 2026-11-22)

| # | Question | Status | Answer |
|---|---|---|---|
| D35 | M's last stage (A3 part 3). Response stops a stage's solve once the unbalanced force is within 0.1 % of the loads; r2c goes on to the balanced state. Next to a crack front that difference (0.005 mm/m of strain) is the 7.2 %. With Response's solve switched on, M comes inside (0.4 %) and r2c's last states sit 5 to 20 times closer to Response's; but which side of a crack front a point falls on is then decided by 0.005 mm/m in the other direction on "constant N +200 kN, then M", whose last stage goes from 1.1 to 6.2 %. Seven of eight cases are inside either way; the no-regression bound says the solve stays off | decided, owner 2026-11-22 (suggestion approved) | **Switch Response's solve on**, and accept the last-stage point on "constant N +200 kN, then M" as a known deviation |
| D36 | Tension's shape (A3 part 4). Under a stepped axial strain Response uses another solve: half steps and a wide tolerance, so its states before cracking are 40 to 130 N m out of balance, and that is why it finds one more rising point. With that solve switched on r2c has the point and the shape is inside, but at the peak of tension and of N + M two Must views go outside. In that solve the stiffness it steps on, and the step when moment grows with axial load, are still r2c's own | decided, owner 2026-11-22 | **Leave it off and accept tension's shape as a known deviation** for phase A: matching it is tightening, not scope. The half-built solve stays off; revisit in phase B. (The developer had suggested finishing the solve first.) |
| D37 | What comes next. A3 part 5 (the views related to shear) was not started. One parked case, the I-girder with strands under M, lost its ending to the rupture rule of A3 part 2 (Risks) | decided, owner 2026-11-22 | **Increment A4: the views related to shear first** (the last scope in phase A), with D35 carried out. D36's third step is not in A4. The I-girder's ending waits for phase B. (The developer had suggested D36's third step first.) |

### Left by increment A4 (new, 2026-11-22)

| # | Question | Status | Answer |
|---|---|---|---|
| D38 | Shear on crack: a line that one program draws and the other does not. Response draws the limit of the shear on a crack only once the largest value on the chart passes 0.001 MPa, and on the negative side only when the negative values are over a fiftieth of the positive. r2c now follows that rule. At two stages the values are so small (0.0015 against 0.0002 MPa; a ratio of exactly a fiftieth at the printed precision) that the two programs fall on either side of the rule, and the measure counts a line that is missing as a difference of 100 % | decided, owner 2026-11-22 (suggestion approved) | **Accept as known deviations** (two stages: M/V = 2 m at cracking, "M constant, then M + V" at its first fall) |
| D39 | How the stirrups remember yielding (A4 part 2c). Response keeps the stirrups' plastic strain at each stage's own points over the depth; r2c keeps it on a fixed grid about 6 mm apart, which is too coarse next to a crack front. With Response's rule switched on, the peak of "N constant, then M + V" comes inside (shear stress 15.5 to 1.3 %) and so do four checks on M/V = 0.5 m, but the rising branch of M/V = 0.5 m, a Must, goes outside (3.7 to 7.6 %): that case has a fall of load and a recovery on the way up, and where r2c takes the fall moves. The no-regression bound says it stays off | decided, owner 2026-11-22 (suggestion approved) | **Leave it off for now**; see whether the same miss appears on the other shapes before taking it up again |
| D40 | Views at the last stage of a shear response. How a shear response ends is a Won't (D1), and the shape check leaves the ending out for shear cases (D25). The views are still compared at the last stage, where the two programs are in different states (often Response's last stage is one it has not converged). Eight of the nine shear cases are outside on their views there, two of them for that alone; so the Should on shear views cannot be met in phase A as it is measured | decided, owner 2026-11-22 (suggestion approved) | **Leave the last stage out of the view checks for shear cases** (a change to the measure, the counterpart of D25), and report the last-stage views separately |
| D41 | What comes next. After A4 every Must miss is a known deviation by the owner's decision, and the Should without shear is met | decided, owner 2026-11-22 | **Neither more Newbeam nor phase B yet: widen the development set step by step**, one variable at a time, so the kernel is not fitted to Newbeam. Step A-1 is shape: the seven Quick Define cases. Each new case meets the same tiers (or its misses become known deviations by the owner's decision); the cases already in the set are held by the no-regression bound. Phase B becomes the review of the test set and targets at the end. Known deviations are watched as the set grows: one that recurs on other shapes is likely Response's solver; one that does not was a Newbeam quirk. (The developer had suggested calling phase A done on its Musts and starting phase B.) |

### Left by step A-1 (new, 2026-11-22)

| # | Question | Status | Answer |
|---|---|---|---|
| D40a | Reading of D40. Where a shear response ends at its peak, the last stage is the peak. The developer kept that stage in the view checks, as the peak; only a last stage after the peak is left out. (No case in the set ends at its peak in Response today.) | decided, owner 2026-11-22 (reading confirmed) | Yes: a last stage that is also the peak stays assessed |
| D42 | The column with shear is outside on its views at cracking for a reason that is not in the kernel. The two curves agree within 0.4 % up to the peak, stage for stage. The measure reads "cracking" as the first step whose stiffness is under 0.4 of the first; Response's load at one stage is 70.5 kN and r2c's 71.0, and that puts "cracking" at stage 15 of one curve and stage 11 of the other. Since D13 a feature stage is compared with the other curve's stage at the same feature, so the views of stage 15 are compared with those of stage 11: 15 Must and Should views outside, up to 100 %. Compared with r2c's stage 15, none is outside. The same happens at the peak, on a flat top: the largest loads are two stages apart | decided, owner 2026-11-22 (suggestion approved) | **Change the measure:** where the two curves have a stage at the same place (within the target, in load and control value together), compare those; use the feature only where they do not. First part of step A-1b. **Done 2026-11-22**, with D13's purpose kept explicitly: never across a fall of load |
| D43 | **The shape of the I-girder with shear, a Must.** This girder is cambered by its strands and its top is cracked under no load. As the load comes on the top cracks close, at a shear of about 34 kN in Response. Response's curve goes straight from 30.9 to 34.5 kN there. r2c sees the cracks closing as an event between two stages, as Response's rule says, and puts two more stages in between; they are states with the top still cracked, at 49.5 and 51.1 kN, and from them the load falls back to 34.4: a fall of 2.5 % of the peak, where the measure counts from 2 %. Before and after it the two curves agree (rising branch 2.4 %, peak +0.05 %). Why Response puts no stage there was not found: the helper that was reading it was stopped part-way. Its two trial rules (how the program tests "cracked" between stages; a stage put in between that fails is dropped) were not verified, did not remove the fall, and are not in the code | decided, owner 2026-11-22 (suggestion approved) | **Accept as a known deviation for now, and finish the reading** of Response's stage control in step A-1b. **Read 2026-11-22, not resolved:** D48 |
| D44 | Which of the seven have joined the set (`docs/acceptance.md`: a case joins when it meets the criteria or its misses are accepted by the owner) | decided, owner 2026-11-22 | **All seven join the set**, with D42 and D43 as answered |
| D45 | What comes next. Two things were started in step A-1 and not finished: the I-girder with shear's shape (D43), and how Response builds its crack spacing over the depth on other shapes: bars around a circle and hoops (21 and 11 % off on the column), the ends of a stirrup (6 to 8 % on the T-beam), a step in width. The spacing is a Could, but the shear on the crack follows it, and that is the one shear view still outside on the column and the I-girder in Response's own states | decided, owner 2026-11-22 (suggestion approved, reordered) | **Step A-1b before the next variable:** D42's measure change first (it changes what the results page shows), then D43's reading, then the crack spacing from the program. **Done 2026-11-22**; left by it: D46, D47, D48 |

### Left by step A-1b (new, 2026-11-22)

| # | Question | Status | Answer |
|---|---|---|---|
| D46 | **The longitudinal crack spacing table, read from the program, is switched off.** It reproduces Response's chart to 0.001 mm on every shape tried. Switched on, 43 checks come inside on the 24 cases (measured against the run of record): every longitudinal crack spacing check, crack widths and diagonal spacing with them, the Could views on 20 of 24 cases instead of 15, and the last-stage point of "constant N +200 kN, then M" (D35, a known deviation on a Must: 6.2 to 1.4 %; the Must views would stand at 12 of 13). In Response's own states the column with shear then agrees on every view but one. Seven checks go outside, and one of them is a Must: **the rising branch of M/V = 0.5 m, 2.7 to 9.9 %.** That figure is r2c's last stage. The response of that case ends differently in the two programs (a Won't), r2c's last stage now falls back further than before, and the point it falls to is nearest to Response's fall of load *before* its peak, so the measure counts it with the rising branch. Response's own rising points stay within 2.7 % of r2c's curve. The others that go outside: transverse bond at the peak of the I-girder with shear (2.5 to 49.8 %, which takes that case's Should views outside again) and of M/V = 2 m (3.7 to 22.5 %), both a spike at the end of the stirrups in a stage r2c has not converged (in Response's own state the I-girder's is 0.00 % off); two views of M/V = 0.5 m by a point; the post-peak of V alone (3.7 to 6.9 %). The no-regression bound says a rising branch may not go outside, so the table is off. (The same case was what kept D39 off.) | decided, owner 2026-11-22 | **Switch the longitudinal table on.** Accept the rising branch of M/V = 0.5 m as a known deviation: the point the measure counts is r2c's last stage, after its own peak, so it belongs to how the shear response ends (a Won't, D1). The other six checks that go outside are recorded with it; the transverse bond spikes are taken up in step A-1c if they come from the shear profile iteration. **Done 2026-11-22** (step A-1c): switched on, 43 in and 7 out as foreseen. The I-girder's spike goes with the program's own solve of a stage, which is off |
| D47 | The column with shear, views at its peak (a Should). Since D42 its views at cracking are inside. At the peak ten Must- and Should-tier views are 8 to 14 % off although curvature and load agree (417.8 against 417.2 kN): the top of this curve is flat within 0.2 % over three stages and the two programs sit in different states on it. Put into Response's own state at that stage, r2c agrees on every such view within 2 % but two: shear on the crack (6.4 %; 1.5 % with D46) and transverse bond (12.5 %, not explained; that rule was never checked on a hoop). This is the known deviation "a peak reached in a slightly different state" of three Newbeam shear cases, recurring | decided, owner 2026-11-22 | **Accept for now, but not as a separate deviation:** it is recorded as one of the effects of a single open item, the shear profile iteration (with D48 and the parked I-girders that end early), taken up in step A-1c. **Taken up 2026-11-22, unchanged:** D50 |
| D48 | **The shape of the I-girder with shear (D43) after the reading.** What is now known: at M/V = 2 m Response keeps the stages where the top cracks close (every parked case of this girder), and r2c has them exactly. At M/V = 1 m (this case and one parked one) Response has none of them, and also none where the web cracks later; a third parked case at M/V = 1 m does close in on the web. By every rule read, Response must have tried a stage in between at those places and had it fail; r2c solves the same stage without trouble, with the program's own solve written out as well as with its own. Two approaches were tried (the rules for a stage put in between; the program's solve), and the bound stops a third. What was not read is named in `docs/kernel.md` ("Open: the same girder at M/V = 1 m") | decided, owner 2026-11-22 | **Not on to reinforcement yet. Step A-1c: the shear profile iteration from the binary**, the part of the shear solve not yet set against the program and the likely common cause of D43/D48, D47 and the parked I-girders with shear that end early. The parked I-girders with shear are its diagnostic (not set members). Usual bounds: two approaches. If it does not break through, D47, D48 and the early ends are accepted together as one known deviation and reinforcement comes next. (The developer had suggested keeping D48 as a known deviation and going on to reinforcement.) **Done 2026-11-22, not resolved:** two approaches used; D49, D50 |

### Left by step A-1c (new, 2026-11-22)

| # | Question | Status | Answer |
|---|---|---|---|
| D49 | **Response's handling of the shear strain profile is written and switched off.** It is the program's own rule for updating the profile between the passes on a stage and for what one stage hands to the next. Switched on, on the 24 cases: the rising branch of M/V = 0.5 m comes back inside (9.9 to 3.6 %), so that Must stands at 24 of 24 again and the known deviation of D46 goes; post-peak 16 to 18 cases; Should views 14 to 16 cases. Against that, 22 checks go outside and 11 come inside, and the Could views go from 20 to 18 cases. Of the 22, nine are views at the peak of M/V = 0.5 m (up to 15.5 %, Should and Could). Eleven are one stage of V alone and are not a real difference: r2c's fall of load at cracking there becomes 1.2 % of the peak (1.9 % now, Response's 2.2 %, counted from 2 %: D32), and the measure then compares Response's stage after cracking with r2c's stage before cracking, which has the same load. No Must goes outside. On the parked I-girders with shear one fewer ends early. It was not switched on because the brief asked for a rule to be verified against Response's own stages first, and that check is neutral: r2c has about as many of Response's stages with it as without | decided, owner 2026-11-23 (suggestion approved) | **Switch it on.** The stage of V alone compared across cracking is accepted as part of D32's known deviation. The views at the peak of M/V = 0.5 m that go outside (Should and Could) are recorded as known deviations. The measure comparing stages across cracking is noted as a recurring pattern (D13, D25, D40, D42, D49), for a meta-development session with the owner later, not now. **Done 2026-11-23** (step A-2): 11 in and 22 out as foreseen |
| D50 | **What comes next.** The shear profile iteration did not break through in two approaches (above). What is left of it: the column with shear's views at its flat peak (D47), the shape of the I-girder with shear (D48), and the parked I-girders with shear that end early (3 of 16, or 2 with D49). What was not read is listed in `docs/status.md`. One lead was found and not followed, because the bound was reached: the I-girder is exactly 1 m deep, and M/V = 1 m is the one ratio at which Response drops the stage, so a comparison of M/V with the depth inside the program may fall the other way there by rounding | decided, owner 2026-11-23 | **Test the lead first, with the oracle, not the binary:** run the I-girder with shear through Response (r2x) at M/V = 0.99 m and 1.01 m. If Response keeps the stage at either, the M/V = 1 m case is rounding against the depth in the program: clone that, bounded to this one comparison. If not, drop the lead. **Either way, then record D47, D48 and the early ends as one known deviation, "the shear profile iteration", and go on to reinforcement (step A-2).** The two new captures are diagnostics, not set members. (The developer had suggested going on to reinforcement directly.) **Done 2026-11-23** (step A-2): no stage at either, lead dropped (D51 for the reading at 0.99 m); the one known deviation recorded; reinforcement done |

### Left by step A-2 (new, 2026-11-23)

| # | Question | Status | Answer |
|---|---|---|---|
| D51 | **Reading of D50's test, for the owner to confirm.** The owner's rule: "if Response keeps the stage at either [0.99 m or 1.01 m], … clone that; if not, drop the lead". At 1.01 m it is plain: Response's curve is that of 1 m. At 0.99 m Response's curve does have a point with the top still cracked (50.0 kN) and a fall of load after it, which r2c has too (49.9 kN). But that point is an ordinary stage of its step, which is half as long there because M/V is under the depth; r2c has that rule already. The stage in question in D48 is one put in *between* stages while closing in on the cracks closing, and Response has none of those at 0.99 m either (r2c has one, at 51.8 kN). The developer read this as "does not keep the stage" and dropped the lead | decided, owner 2026-11-23 (reading confirmed) | Confirmed: not rounding against the depth; the lead is dropped |
| D52 | **The set for reinforcement is five cases; the brief asked for about six to eight.** Only five parked fixtures vary the reinforcement and can be run. Two more vary it and are refused by earlier decisions: the segmental steel curve (D18) and draped tendons (D4). Reinforcement inputs that no fixture covers: stirrups given as a single leg, open or closed (Newbeam's are T-headed single legs; the column's hoops); two stirrup types in one section (Response keeps no stirrup history then, and the bond rule is not checked for it); stirrups over part of the depth; a bar spacing given on a layer; bars marked as a distributed pattern; a prestrain on bars under shear. Adding cases is a change to the test set, so it is the owner's | decided, owner 2026-11-23 (suggestion approved) | Five is enough; no new captures for reinforcement |
| D53 | **What comes next.** Steps A-1 and A-2 are worked through; every Must miss on the 29 cases is a known deviation or the owner's override. The next variable in D41's order is material models. Parked there: the tension stiffening models and factor on Newbeam with shear (6 cases), two concrete base curves on Newbeam under M (2), given crack spacings (1), and the compression softening models on the I-girder with shear (16 that run). The I-girder ones bring the shear profile iteration with them: on today's kernel 1 of the 16 ends early and 11 are outside on a Must | decided, owner 2026-11-23 (suggestion approved) | **Material models next (step A-3):** the Newbeam cases first, then the softening models on the I-girder. Before it, D54 is carried out |

### Where Response is unstable (2026-11-23, after A2)

| # | Question | Status | Answer |
|---|---|---|---|
| D54 | Matching the shear views needs a very tight clone, and some of Response's own views jump between neighbouring stages (the bond chart at the end of prestrained stirrups: 0.1 to 38 MPa from stage to stage, step A-2). Matching such a view at one stage is luck; the stage-by-stage measure makes it worse near cracking, the peak and the ending (D13, D25, D40, D42, D49) | decided, owner 2026-11-23 | **A view check where Response itself is unstable is reported, not assessed.** Unstable: Response's view at the stage lies farther than the views target from the blend of its neighbouring stages' views. Checks in steady stretches stay strict; the curves are not affected; every Must left unassessed is listed for the owner. The rule is in `docs/acceptance.md`, "Where Response is unstable". Carried out by the developer as a measure change before step A-3: views captured at the neighbouring stages, the test in the measure, the report showing Response's departure beside r2c's. **Done 2026-11-23** (log 2026-11-23-02): "The rule on unstable views" above; D55 and D56 came out of it |
| D55 | **Three readings of the rule's wording, for the owner to confirm.** (a) "At that stage's place along the control curve": the developer took the place by distance along the curve (load scaled by Response's peak, control value by its largest value, as the curves are measured), because it works on every branch, at a peak and across a fall of load, where load alone or control value alone turn back. (b) Response layers the section afresh at each stage, so the points of a view differ between neighbours: the blend is taken depth by depth. (c) A line that one neighbour draws and the other does not is blended with nothing. What each moves is in the table of readings above: (a) 48 to 78 of 1,554 checks with the other readings, none of them a Must miss; (c) nothing; (b) has no other reading that can be measured | decided, owner 2026-11-23 (readings confirmed) | **Confirm all three:** place by distance along the curve; blend depth by depth; a line one neighbour draws blended with nothing |
| D57 | **Response gives two different responses for the I-girder with shear (M/V = 1 m), run to run.** Same input, same loads, same program: 15 stages (the fixture, captured 2026-11-21, and one run of four on 2026-11-23) or 25 stages (three runs of four). The 25 hold the 15 with every view identical, and ten more stages between a shear of 366 and 463 kN, where the curve is the same straight rise. Peak, rising branch, post-peak, shape and every compared view of r2c come out the same against either. The other 28 cases repeated exactly. It is not the stage of D48 (that one is at 34 kN). Why Response does this was not looked into | decided, owner 2026-11-23 | **Keep the 15-stage fixture and note the case as not repeatable. From now on each new case is captured three times when the set is widened,** and any that does not repeat is noted before it joins; the direct evidence of Response's instability. Start with the cases of step A-3 |
| D56 | **The rule reaches further than its example: is that what was meant?** Views are compared at cracking, falls of load and the peak, which is where Response's views change most between stages; a steady stretch is not compared at all. So the rule leaves one check in five unassessed (318 of 1,554), nine in ten of them checks r2c was inside on. All 64 unassessed Musts were inside, r2c within 1.7 % of Response. It also takes 32 misses out of the count, among them known deviations (by case and stage: D47, and part of D32, D46 and D49). No Must miss is hidden by it. Whether a stage where Response jumps is one where a match "is luck" is a structural judgement and the owner's: r2c matches most of these jumps closely, which may not be luck | decided, owner 2026-11-23 | **No: the rule reached too far. Narrow it to spikes.** A check is unassessed only where Response's two neighbouring views agree with each other (within the views target) and its view at the stage departs from their blend by more than the target. A step, such as cracking, stays assessed: r2c follows most of them closely, which is behaviour to clone, not luck, and leaving them out would hide a regression at the stages that matter most. Wording in `docs/acceptance.md`. Carried out as a measure change before step A-3 (the neighbour captures are already in the fixtures). (The developer had suggested keeping the rule as written for step A-3.) |

### The source rule (2026-11-22, after A2)

| # | Question | Status | Answer |
|---|---|---|---|
| D34 | Which source decides how r2c calculates. Until now the thesis was the basis and the binary was read only to answer questions, so every difference between them came to the owner (D21, D22, D30 and others) | decided, owner 2026-11-22 | **The manual decides what exists; the binary decides how it calculates**, including the solver and how a response ends. Where they differ, follow the binary without asking. The thesis guides reading the binary and supplies names and explanation. Exceptions: the owner's overrides only (`docs/acceptance.md`: C2, D12; shear endings stay a Won't, D1). Each rule is written fresh from understanding the routine, not transliterated from decompiled code, and its source recorded in `docs/kernel.md`. In CLAUDE.md and `docs/acceptance.md` |

### The next increment

| # | Question | Status | Answer |
|---|---|---|---|
| D26 | What the first increment on the exit criteria should be | decided, owner 2026-11-22 (suggestion approved, as ranked) | **Increment A2: the Musts without shear, with the measures put right first.** Its parts are ranked below |

The parts of A2, ranked by how much of a Must each closes (the Musts: peak, rising branch,
shape, and the views of the stress state under moment and axial load). Peak is met.

1. **The measures, with the owner** (meta-development). **Done 2026-11-22** (D13, D25, D27,
   D28): shape 15 of 17; the view Must is counted on its own, 2 of 8 inside.
2. **Principal tensile stress at the crack front** (kernel). **Done 2026-11-22:** inside at
   four of five stages; D29 and D30 for the rest.
3. **Steel stress at a crack**, under N + M and under tension. **Done 2026-11-22:** inside.
4. **Tension: the order of cracking and the fall of load.** **Stopped 2026-11-22:** D31.
5. **V alone: the fall of load before the peak. M/V = 0.5 m: the recovery after a fall of
   load.** **2026-11-22:** M/V = 0.5 m inside; V alone investigated, D32.

Also in A2, before part 2: several sections in one file and the horizontal tie are refused
(D23). **Done 2026-11-22.**

Not in A2: the ending of −M (a Should), the views related to shear (Should) and to cracking
(Could), speed.

### Closed by the owner's stance

Settled by "no structural assessment of results" (owner, 2026-11-21) and need no answer: is a
peak after a fall of load the one that matters (Response's largest is used); dm-n1n's failure
mode; whether r2c's states beyond Response's failure are real; Liping LB1 at +1.8 %; findings
H and I (views are now covered by D2).

## Risks

- **Review load.** Development runs faster than the owner can review it. This page is the
  answer: one page per session, not one log per step.
- **Unattended runs** without a scoped GitHub token (setup, not yet done). Branch protection on
  `main` and auto-delete of merged branches are on (owner, 2026-11-22).
- **The set is still narrow.** Three more shapes and five reinforcement cases are in;
  material models, units and factors are parked. The parked cases are not run on every
  change, so a change that breaks one of them shows only when they are run again.
- **What moved on the parked cases** (the 56 run once at the end of step A-2, against
  the run at the end of step A-1b; measured; not runs of record). Two things changed in
  between: the longitudinal crack spacing table (D46) and the shear profile handling
  (D49). The rules of step A-2 part 3 moved no parked check. Check by check 107 came
  inside and 51 went outside. On the Musts, all of it on the I-girders with shear:
  softening 10 and 13 no longer end early and are inside on peak, rising branch and
  shape (peak −9 % to −0.7 %); softening 3 came inside; softening 7 came inside on peak
  and rising branch and went outside on shape; **softening 2 and 6 went outside**
  (softening 2 on shape; softening 6 on shape and on its peak, +4.1 to +5.4 %), and
  softening 5 on its rising branch by a hair (4.7 to 5.2 %). Cases inside on peak,
  rising branch and shape: 31 of the 45 that r2c solves (30 before).
- **The shear profile iteration is not resolved** (D50), and the parked I-girders with
  shear will be set members when the material models come in: an early end will be a
  Must there. One of 16 ends early now (softening 12; softening 9 is on the line at
  −5.0 %), three before D49. Which ones changes with any small change to the kernel.
- **A rule taken over in the reported state only.** A node with next to no shear strain
  is reported as Response reports it (no transverse strain, no stirrups), but its forces
  are still evaluated r2c's way. The difference in the forces is taken to be nothing
  (stirrups carry no axial load or moment); it was not measured by writing the other
  form. Which nodes these are near a face is not Response's node for node.
- **Four rules of the program are in the code and switched off** (`docs/status.md`).
  Each is one more thing to keep working while it is unused.
- **Part of the crack spacing routines was not read:** they branch on a setting of the
  section that could not be named. The branch taken over fits every chart compared. A
  parked case with another tension stiffening model or factor may take the other branch.
- **A stage control status that the program never returns with shear** is still acted on
  in r2c (it carries on from a solve that has not closed if it is nearly balanced). Found
  while reading the solve; left as it is, because taking it out is a change with no
  check to weigh it by. It is noted in `docs/status.md`.
- **One inferred detail in the new layering:** which side the middle node of the thin layer
  belongs to (the wider one) is taken from Response's charts on one section, not read.
- **One parked regression test fails:** Newbeam in US units at M/V = 1 ft, peak 1.4 to
  1.6 % under Response's against a guard of 1.3 %. It has been over the guard since
  step A-1 (the parked tests were not run in between) and moved 0.1 % further since.
  The guard was left as it is; the case is inside the 5 % target on its peak.
- **Still standing on the parked cases:** eleven I-girder cases with shear outside on peak,
  rising branch or shape; the two cases in US units at M/V = 1 ft outside on rising
  branch and shape; the T-beam at M/V = 2 m on its peak (+6.7 %).
- **Response is not repeatable on at least one case** (the I-girder with shear, D57):
  its number of stages differs from run to run. Each fixture is one capture. The 28
  other cases repeated exactly on 2026-11-23; the 56 parked cases were not captured
  again, and 16 of them are I-girders with shear.
- **Less is assessed at the features of the curve since D54.** One view check in five is
  now reported and not counted, most of them checks r2c meets (D56). A change to the
  kernel that spoils one of them will not show in the tier counts; it will show in the
  regression tests, which the rule does not touch, and in the report's list of unstable
  checks, which prints r2c's difference beside Response's departure and marks one that
  would be outside.
- **Speed.** Not worked on. The 29 cases take about two minutes on the owner's machine
  with all of them running at once (measured).
