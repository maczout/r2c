# r2c: the owner's summary

**Read this first.** The one page the owner reads each session: where r2c stands, what
"finished" means, and every decision that is open or has been made. The developer keeps it
current at the end of every session (CLAUDE.md, "Ending a session"). Everything else in
`docs/` is the developer's working record and backs this page; it does not replace it.

Last updated: 2026-11-23, by the developer, at the end of step A-3, the development set
widened by material models (log 2026-11-23-04).

**What changed.** The set is 37 cases: eight parked cases whose variable is a material
model on Newbeam have joined it (table under "The development set"). r2c calculates what
it did, number for number: nothing in the kernel was changed, because nothing on the new
cases called for it.

- **Each of the eight was captured three more times from Response before it joined (D57):
  all eight repeat exactly**, every stage and every view.
- **The Musts are met on all eight as they stood**: peak within 0.2 %, rising branch within
  0.2 %, shape the same, and on the two without shear every view of the stress state and
  the ending. No check on the 29 earlier cases moved.
- **Three of the six new shear cases are outside on the Should views, by five checks**
  (tension stiffening factor 0.5; Tamai; elasto-plastic). Put into Response's own state at
  those stages r2c agrees on every one of those views within 3 %, so no rule is wrong: the
  two programs sit in slightly different states on a flat peak, or within the tolerance of
  the shear profile iteration. They are the known deviations of D47, D38 and D46 recurring
  (table "Which known deviations recur"). Put to the owner as D61.
- **The softening models on the I-girder (part 2): three are proposed, as D62**, and all
  18 parked ones were captured three more times. 16 repeat exactly. Two do not, and what
  differs is telling: in one run Response keeps the stages it puts in while closing in on
  an event, in another it drops them. r2c has exactly the stages of the longer variant.
  That bears on the open item of the shear profile iteration (D48); put to the owner as
  D63.

**Four items wait for the owner: D60** (a reading: the given crack spacings are not a
material model, so that case stays parked), **D61** (accept the five Should misses as
known deviations), **D62** (which softening cases join) **and D63** (what Response's own
non-repeatability says about D48, and whether to follow it).

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
| **A. Develop the kernel** | On a development set that widens step by step (D41): Newbeam varied in its loads (the 17 cases below), then one variable at a time — shape (step A-1, the seven Quick Define cases), reinforcement (step A-2, five cases), then material models, units and material factors. What is not yet in the set stays parked. | **Now.** Steps A-1 (shape) and A-2 (reinforcement) are worked through, and of step A-3 (material models) the Newbeam part (2026-11-23). On the 37 cases peak and rising branch are met; shape on 34 and the Must views on 16 of 17. The four misses are known deviations or the owner's override (D32, D36, C2; the I-girder with shear, part of the shear profile iteration, D50). The Should on shear views is met on 10 of the 20 shear cases. The softening models on the I-girder wait for the owner's choice (D62) |
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

**Step A-3, material models on Newbeam (8 cases, proposed by the developer 2026-11-23 to
the owner's brief; D53, D60).** The parked fixtures whose variable is a material model of
the concrete, on Newbeam. Each was captured three more times through Response first (D57):
all eight repeat exactly. Moved into the set in a commit of their own.

| Case | Loads | The model it tests |
|---|---|---|
| `newbeam-cmod0-m` | M | concrete base curve: linear |
| `newbeam-cmod3-m` | M | concrete base curve: elasto-plastic |
| `newbeam-tstiff1-mv` | M + V at M/V = 1 m | tension stiffening: Vecchio-Collins 1982 |
| `newbeam-tstiff2-mv` | M + V at M/V = 1 m | tension stiffening: Collins-Mitchell 1987 |
| `newbeam-tstiff3-mv` | M + V at M/V = 1 m | tension stiffening: Izumo et al |
| `newbeam-tstiff4-mv` | M + V at M/V = 1 m | tension stiffening: Tamai et al 1987 |
| `newbeam-tstiff6-mv` | M + V at M/V = 1 m | tension stiffening: elasto-plastic |
| `newbeam-tsfactor-mv` | M + V at M/V = 1 m | the tension stiffening factor, 0.5 in place of 1 (with the default model, Bentz 1999) |

The default models (base curve Popovics/Thorenfeldt/Collins, tension stiffening Bentz
1999, softening Collins-Bentz 2011) are what every other case in the set uses. Not
proposed: the given crack spacings (`newbeam-smx-mv`), which Response holds as a setting of
the section and not of a material (D60); the parabolic and segmental base curves and
tension stiffening "none", for which there is no fixture (the last cannot be captured:
Response asks a question first). The softening models are on the I-girder: part 2, D62.

Parked, kept and not run by default (48 cases): the softening models on the I-girder,
given crack spacings, units, material factors, More Detail, no input, the other cases on
the T-beam and I-girder, and Response's sample inputs. They sit in a folder of their own and can be run on
request. Eleven of them need something that has been removed, and r2c refuses them: five
since the removals of D18, six more (all on Response's sample inputs) since D23.

## Progress against the Phase A exit criteria

Cases inside target, counted by `tools/targets.py --counts` (measured). "Step A-2" is that
step's run of record on the 29 cases, under the spike test. "Now" is the run of record of
step A-3 (`docs/verification-results.md`) on the 37 cases. The kernel is the same in
both; only the set differs.

| Check | Step A-2 (29) | Now (37) | Exit tier (D1, D2, D27) |
|---|---:|---:|---|
| Peak | 29 | 37 of 37 | Must: met |
| Rising branch | 29 | 37 of 37 | Must: met |
| Shape | 26 | 34 of 37 | Must (a shear case's ending left out: D25). Two misses are known deviations (D32, D36); the third is the I-girder with shear (the shear profile iteration, D50). None is a new case |
| Views of the stress state, without shear | 14 of 15 | 16 of 17 | Must. The miss is the column under N alone after its peak (the owner's override, C2) |
| Post-peak, without shear | 14 of 15 | 16 of 17 | Should. The miss is the column under N alone (C2) |
| Views related to shear, and stress-state views with shear | 21 of 29 (7 of the 14 with shear) | 26 of 37 (10 of the 20 with shear) | Should, not met. Three of the six new shear cases are outside (D61) |
| Views related to cracking | 23 of 29 | 31 of 37 | Could. All eight new cases are inside |

The 29 cases are held by the no-regression bound: against the last run of record no
check on them changed side (measured, `python tools/changes.py`).

### The rule on unstable views (D54, D56): no rule, the rule as first written, the spike test

The spike test was carried out 2026-11-23 as a change to the measure (log 2026-11-23-03).
The three columns are the same run of r2c on the 29 cases, counted three ways; r2c's
differences from Response are the same in all three, and the same as in the run of record
before it (measured: the two runs' results set side by side). The generated figures are in
`docs/verification-results.md` ("View checks by tier", "Detail views where Response is
unstable"); the results page shows the same.

**Checks, tier by tier** (measured, `python tools/unstable.py VERIFY_OUT`). A check is one
view at one compared stage of one case; the last stage of a shear case is left out (D40).

| Tier | Checks | No rule: inside | outside | As first written (D54): inside | outside | unassessed | Spike test (D56): inside | outside | unassessed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Must | 376 | 369 | 7 | 305 | 7 | 64 | 367 | 7 | 2 |
| Should | 808 | 764 | 44 | 598 | 17 | 193 | 763 | 44 | 1 |
| Could | 370 | 361 | 9 | 305 | 4 | 61 | 360 | 9 | 1 |

Of the 1,554 checks, 1,216 were tested. The other 338 have no stage on both sides (the
last stage of a case without shear, and the case with no load) or, twice, a view whose
lines could not be blended; they stay assessed, as the rule says.

**Cases, tier by tier** (measured, `python tools/targets.py VERIFY_OUT --counts`, with
`--before-d54` and `--d54-first`).

| Tier | No rule | As first written | Spike test |
|---|---:|---:|---:|
| Must (views of the stress state, without shear) | 14 of 15 | 14 of 15 | 14 of 15. The miss is the column under N alone (C2) |
| Should | 21 of 29 | 24 of 29 | 21 of 29 |
| Could | 23 of 29 | 26 of 29 | 23 of 29 |

Peak, rising branch, shape and post-peak are not touched by the rule.

**Every check the spike test leaves unassessed** (4; Musts first, for the owner's review
as the rule asks). Measured, `python tools/unstable.py VERIFY_OUT --list`. Percentages
are of a chart's largest value.

| Tier | Case | Response's stage | View | Response's departure from the blend of its neighbours | Its two neighbours apart | r2c's difference from Response |
|---|---|---|---|---:|---:|---:|
| Must | Column, N₀ = −4000 kN then M (`column-n4000-m`) | 28 (cracking) | principal tensile stress | 5.0 % | 4.1 % | 0.4 % |
| Must | Newbeam, N₀ = −2000 kN then M (`newbeam-n2000-m`) | 37 (peak) | principal tensile stress | 6.3 % | 3.8 % | 0.1 % |
| Should | Newbeam, V₀ = 50 kN then M (`newbeam-v0-m`) | 61 (peak) | shear on the crack | 8.9 % | 1.4 % | 0.1 % |
| Could | Newbeam, M + V at M/V = 1 m (`newbeam-mv`) | 30 (peak) | longitudinal bond | 7.3 % | 3.7 % | 0.0 % |

All four were inside before any rule. All four sit close to the two thresholds (the first row's
5.0 % is 5.006 % against "more than 5 %"), so a small change
in a reading or in the target would move them in or out.

**The bond chart as a test of the rule: not caught.** The case is Newbeam at M/V = 1 m
with a prestrain on the stirrups (`newbeam-stirrupdep-mv`); the view is the bond stress
along the stirrups, whose largest value is at the stirrups' end. It is compared at
cracking (stage 9) and at the peak (stage 28).

| Compared stage | Chart's largest value at the stage before, at the stage, at the stage after (MPa) | Response's departure | Its neighbours apart | As first written | Spike test | r2c's difference |
|---|---|---:|---:|---|---|---:|
| 9 (cracking) | 0.003, 0.005, 18.6 | 9.9 % | 100 % | unassessed | **assessed** (a step) | 3.5 % (0.0002 MPa of 0.005) |
| 28 (peak) | 9.5, 20.9, 32.7 | 18.0 % | 71 % | unassessed | **assessed** (a step) | 2.7 % |

The chart along the whole response, from Response's full capture (measured,
`python tools/unstable.py --trace CAPTURE transverse_average_bond`; Response alone, every
stage, though only stages 9 and 28 are compared):

| Stages | Largest value of the chart, stage by stage (MPa) |
|---|---|
| 1 to 9 | nothing (cracking at 9) |
| 10 to 17 | 18.6, 18.6, **0.13**, 18.6, 18.6, 18.6, 18.6, 18.6 |
| 18 to 27 | 37.2, **1.4**, 37.3, 37.4, 19.0, 19.2, 37.9, 38.1, 38.5, 9.5 |
| 28 to 34 | 20.9 (peak), 32.7, 34.4, 16.7, 36.0, 36.2, 17.8 |
| 35 to 41 | 17.9, 18.0, 18.0, 17.7, 36.6, 36.7, 45.0 |

What this shows:

- **The chart flickers between levels (about 0, 19 and 37 MPa, and others near the
  peak); it does not spike and return.** Of its 41 stages that can be tested, the rule
  as first written would leave 19 unassessed. The spike test would leave one: stage 12,
  where the chart drops to 0.13 MPa between two stages at 18.6. At every other jump the
  stage after is at a different level from the stage before, which the test reads as a
  step: behaviour to clone.
- **At the peak it is a different chart at each of three stages running.** That is the
  situation D54 described ("matching it at one stage is luck"), and the spike test does
  not cover it.
- **A drop to nothing is seen less well than a rise.** Stage 19 drops from 37 to 1.4 MPa
  and back, and its departure measures 4.9 %, under the target, so it is not a spike by
  the test. The measure is the comparison's own: how far the points of the stage's chart
  lie from the other curve, as a share of the stage's largest value. Where the stage's
  chart is nearly empty, its points lie close to the foot of the other curve, and the
  peak it lacks is not counted. This is the measure every view check uses (r2c's points
  are not measured against Response's curve either); it is noted here, not changed.

**The readings.** The owner confirmed three (D55): the stage's place by distance along
the curve; the blend taken depth by depth; a line one neighbour draws blended with
nothing. The spike test adds one, the developer's, confirmed by the owner (D58): "agree with each other" is
measured as any two records are compared, each neighbour in turn as the reference and on
its own largest value, the larger of the two taken. What the other readings would move
under the spike test (measured, `python tools/unstable.py VERIFY_OUT --readings`):

| Choice | Reading in use | Other reading | What the other reading moves |
|---|---|---|---|
| The stage's place between its neighbours (D55, decided) | By distance along the curve | By control value alone | 3 checks (2 more unassessed, 1 assessed again); Must unassessed 3 |
| | | By load alone | 2 more unassessed; Must unassessed 4 |
| | | Half way | 2 more unassessed; Must unassessed 4 |
| A line that one neighbour draws and the other does not (D55, decided) | Blended with nothing | Left out of the blend | No check changes |
| What the neighbours' difference is a percentage of (D58, decided) | Each neighbour's own largest value, both ways | The largest value of the chart at the stage, as the departure is | No check changes |

**The spike test on the 37 cases** (measured, `python tools/unstable.py VERIFY_OUT
--list`; the tables above are the 29 cases as they stood when the test was made). Of
1,953 view checks 1,573 are tested and 6 are left unassessed: the four above and two on
the new cases, both checks r2c is inside on. No new Must is unassessed. No case's result
in any tier changes against no rule.

| Tier | Case | Response's stage | View | Response's departure | Its two neighbours apart | r2c's difference |
|---|---|---|---|---:|---:|---:|
| Should | Tension stiffening Collins-Mitchell 1987 (`newbeam-tstiff2-mv`) | 30 (peak) | shear stress | 6.8 % | 4.2 % | 0.1 % |
| Could | Tension stiffening Izumo (`newbeam-tstiff3-mv`) | 30 (peak) | longitudinal bond | 6.8 % | 1.8 % | 0.0 % |

By tier, inside, outside and unassessed under the spike test: Must 415, 7, 2 of 424;
Should 1,013, 49, 2 of 1,064; Could 454, 9, 2 of 465.

### Step A-3, part by part

| Part | What was done | Outcome |
|---|---|---|
| 1. Material models on Newbeam | Eight cases proposed; each captured three more times (D57); moved into the set in a commit of their own; verify and report rerun | **All eight repeat. Musts met on all eight as they stood; no kernel change.** Five Should checks outside on three of the six shear cases, none of them a rule (below; D61). All Could views inside |
| 2. Softening models on the I-girder | Three proposed with reasons (D62). All 18 parked ones captured three more times; none moved in | **16 of 18 repeat exactly; two do not** (below; D63). The three proposed all repeat |
| 3. Which known deviations recur | Table below | How a shear response ends, on four of six; the flat-peak views (D47), the limit line (D38) and the bond at the stirrups' end (D46), once each or twice. The stage Response does not put in (D48) is not on Newbeam; on the I-girder it turns out to be tied to Response's own non-repeatability |
| The parked cases, run once | The 48 that remain | **Nothing moved** against the run at the end of step A-2: the kernel is the same (Risks) |

### The eight new cases

| Case | Musts | Should | What is left |
|---|---|---|---|
| Base curve linear, M | met (peak 0.00 %, every stress-state view inside, ending 0.3 %) | met | Nothing |
| Base curve elasto-plastic, M | met (peak 0.00 %, ending 0.0 %) | met | Nothing |
| Tension stiffening Vecchio-Collins 1982, M + V | met (peak +0.07 %, rising branch 0.05 %) | met | How the response ends (a Won't) |
| Collins-Mitchell 1987, M + V | met (+0.04 %, 0.03 %) | met | How the response ends (a Won't) |
| Izumo, M + V | met (+0.01 %, 0.02 %) | met | Nothing: it ends as Response's does |
| Tamai, M + V | met (−0.02 %, 0.06 %) | **one check outside:** shear on the crack at the peak, 10.6 % | That check (D61); how the response ends |
| Elasto-plastic, M + V | met (+0.16 %, 0.09 %) | **one check outside:** transverse bond at the peak, 7.0 % | That check (D61); how the response ends |
| Tension stiffening factor 0.5, M + V | met (−0.14 %, 0.18 %) | **three checks outside:** shear on the crack at the peak, 106 %; transverse bond at the fall of load and at cracking, 5.2 and 6.7 % | Those checks (D61). It ends as Response's does |

**The five Should checks outside: none is a rule** (measured: r2c put into Response's own
state at each of those stages, `python tools/diagnose.py states RECORD --stages N
--views`; and the two charts side by side, `python tools/viewlines.py`).

| Case and stage | View | As r2c solves it | In Response's own state | What it is |
|---|---|---:|---:|---|
| Factor 0.5, peak | shear on the crack | 106 % | 0.03 % | The top of this curve is flat (193.1 to 193.5 kN over the last six stages) and the two programs stop at different stages on it; the top of the cracked zone is 6 mm lower in r2c's. The chart's values are small (0.15 MPa at most), and r2c's then fall just on the other side of the rule for drawing the limit line on the positive side (a fiftieth: 0.022 against Response's 0.014), which is the 106 %. D47 and D38 recurring |
| Factor 0.5, fall of load and cracking | transverse bond | 5.2, 6.7 % | 0.4, 0.2 % | The stirrups have barely started to work: the whole chart is 0.05 to 0.10 MPa, and the difference 0.003 to 0.009 MPa |
| Tamai, peak | shear on the crack | 10.6 % | 18.4 % | A flat top again (193.0 to 193.1 kN over seven stages). The limit line starts with a jump at the top of the cracked zone (0 to 3.4 MPa), and that zone ends one node (1 mm) lower in r2c's state. In Response's own state r2c differs at that one node alone: Response has it just cracked (a width of 0.004 mm), r2c just not. D47 recurring |
| Elasto-plastic, peak | transverse bond | 7.0 % | 0.6 % | At the bottom end of the stirrups (2.7 of 20 MPa), at the same curvature and a load 0.16 % apart. r2c's stage there has converged (profile error 0.9 % against the program's limit of 1 %). The bond at the stirrups' end is that sensitive to the state. D46's kind, in a converged stage |

Also checked, because the risk was on record: with another tension stiffening model or
factor r2c's crack spacing tables are still Response's charts (within 0.05 mm on the four
captures tried, `python tools/spacing.py`). The branch of those routines that was not
read is not taken on these cases.

### The softening models on the I-girder (part 2)

**Proposed: three of the 18 parked cases** (D62; the reasons are there). None was moved in.

| Proposed | Model | The kind it stands for | Where it stands today (parked run, not of record) |
|---|---|---|---|
| `igirder-csoft2-m2v` | Vecchio-Collins 1986 | Strength lowered by the tensile strain alone; the strain at peak stress kept. The commonest kind: nine of the models, the default among them | peak −0.6 %, rising branch 2.0 %, **shape outside** |
| `igirder-csoft14-m2v` | Hsu-Zhang 1998 | Strength and the strain at peak stress both lowered, by a square-root rule, with a cap for high strength concrete that acts on this 60 MPa girder. The Hsu family (three models) | peak −0.8 %, **rising branch 6.9 %, shape outside** |
| `igirder-csoft3-m2v` | Vecchio-Collins 1992-A | Lowered by the ratio of tensile to compressive strain, with a curve of its own (a plateau). The ratio kind (three models) | peak −3.0 %, rising branch 3.7 %, shape the same: inside |

**How the 18 repeat** (measured, `python tools/repeat.py`: the capture the fixture was cut
from and three new ones, every stage and view byte for byte).

- **16 repeat exactly**, the three proposed among them, and softening 9 at M/V = 1 m.
- **Collins 1978 at M/V = 1 m (`igirder-csoft11-mv`) does not:** 22 stages in the capture
  of the fixture, 32 in all three new ones. The 32 are the 22 with ten more stages
  between a shear of 366 and 463 kN: the same ten, at the same loads, as on the I-girder
  with shear of the set (D57: 15 or 25 stages).
- **Zhu-Hsu-Lee 2001 at M/V = 2 m (`igirder-csoft16-m2v`, a model r2c refuses, D18) does
  not:** 62 stages three times, 61 once. The stage missing is one of those put in where
  the top cracks close (a moment of 37 kNm, between 53 and 38).

**What the difference is** (measured on the captures; that it is one cause is inferred).
Those ten stages are Response closing in on the web cracking: each a fifth of the way
from the last to the stage at 463 kN, which is the rule r2c has from the program. In its
short variant Response goes there in one step. **r2c has exactly the ten** (385.2 to
451.1 kN against Response's 385.3 to 450.7), and on softening 9, which repeats, exactly
the six Response has there. So at the web cracking r2c does what Response does in most
runs, and Response's short variant is Response not repeating itself. The stage missing on
softening 16 is the same thing at the other event, the closing of the top cracks, which
is where D48 is. D63.

### Which known deviations recur

The owner asked for this (D41): a deviation that recurs is likely Response's solver; one
that does not was a quirk of one case.

| Known deviation | On the seven shape cases (step A-1) | On the five reinforcement cases (step A-2) | On the eight material cases (step A-3) |
|---|---|---|---|
| How a shear response ends (a Won't, D1) | Recurs on both shear cases | Recurs on all three shear cases | **Recurs on four of the six shear cases.** With Vecchio-Collins 1982 and Collins-Mitchell 1987 both end falling, Response's on a stage far down (19, 23 % of the peak), r2c's just under its peak (92, 94 %). With Tamai and elasto-plastic Response's ends falling (25, 97 %) and r2c's stands still. With Izumo and with the factor 0.5 both stand still at the same place: the same ending |
| The shear profile iteration: views on a flat peak (D47) | The column with shear | Does not recur | **Recurs on two:** shear on the crack at the peak with the factor 0.5 and with Tamai. Both curves are flat at the top within 0.2 % over six or seven stages. One check each, where the column had ten |
| The shear profile iteration: a stage Response does not put in (D48) | The I-girder with shear | Not tested | **Not on Newbeam** (no new case has an event Response steps over). On the parked I-girders it is seen again at M/V = 1 m, and now with a cause in sight: Response itself keeps or drops such stages from run to run (D63) |
| D32: a fall of load just under the 2 % the measure counts from (V alone) | Does not recur | Not tested | Not tested: no new case is under V alone. The factor 0.5 has a fall of load before cracking, 3.6 % of the peak in Response and 3.5 % in r2c, well clear of the 2 % |
| D35, D36, C2 | D35 does not recur; D36 not tested; C2 is that case | D35 does not recur; D36 and C2 not tested | D35 does not recur (both base curves are inside at their last stage, 0.3 and 0.0 %); D36 and C2 not tested |
| D38: a limit line of shear on the crack that one program draws and the other does not | Does not recur | Does not recur | **Recurs once:** the factor 0.5 at its peak, as a consequence of the flat peak (above) |
| D39: the stirrups' memory of yielding (off) | Does not recur | No miss points to it | No miss points to it; not measured switched on |
| D46: a spike of transverse bond at the end of the stirrups | The I-girder with shear, in a stage not converged | Does not recur | **Recurs once, smaller:** elasto-plastic at its peak, 7.0 %, in a stage that has converged |
| D49: views at the peak of M/V = 0.5 m | (came with D49) | Does not recur | Does not recur |

What the pattern says (the developer's reading): the deviations that recur on the new
cases are all of one family, the state a shear case is in at or after a flat peak. None
is a material rule: in Response's own states every new case agrees. The models
themselves (base curves, tension stiffening, the factor) are Response's.

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

### Left by step A-3 (new, 2026-11-23)

| # | Question | Status | Answer |
|---|---|---|---|
| D60 | **Reading of the brief, for the owner to confirm: the given crack spacings are not a material model.** D53 counted the case with crack spacings given (`newbeam-smx-mv`) among the material models. In Response it is a setting of the whole section (beside the moment axis), not of a concrete, and the brief for this step names concrete models, tension stiffening and its factor. The developer left it parked. It is inside on peak, rising branch and shape today (peak +0.07 %) | suggested (reading) | **Confirm, and take it with the next variable** (settings of the section and units), or say that it joins now: it would need its three captures first |
| D61 | **Five Should checks outside on three of the new shear cases: accept as known deviations?** (table "The five Should checks outside"). Shear on the crack at the peak with the tension stiffening factor 0.5 (106 %) and with Tamai (10.6 %); transverse bond at the peak with elasto-plastic tension stiffening (7.0 %) and, on a chart of 0.1 MPa, at the fall of load and at cracking with the factor 0.5 (5.2, 6.7 %). In Response's own state at each of those stages r2c agrees within 3 % on every one of these views, but for one node at the top of the cracked zone with Tamai. So no rule is behind them and there was nothing to read from the program: they are the state at a flat peak (D47), the limit line that follows from it (D38), and the bond at the stirrups' end (D46). The Musts are met on all eight | suggested | **Accept as known deviations, as effects of the shear profile iteration (D50), and let the eight stand in the set.** Other options: (a) hold the three cases out of the set until the shear profile iteration is taken up again; (b) take up the flat peak now as work of its own, which is the item the owner closed for now in D50 |
| D62 | **Which softening cases on the I-girder join the set** (the owner asked for two or three that cover the kinds of model, not all 18). The 15 models r2c has besides the default fall into kinds by what the rule does (`docs/kernel.md`, "Compression softening"): (1) strength lowered by the tensile strain alone, the strain at peak stress kept (nine models, the default among them); (2) lowered by the ratio of tensile to compressive strain (Vecchio-Collins 1982 and 1992-A; Collins 1978 uses their sum); (3) the Hsu family, strength and peak strain both lowered by a square-root rule (three); and "none". All but two are at M/V = 2 m | suggested | **Three: `igirder-csoft2-m2v`, `igirder-csoft14-m2v`, `igirder-csoft3-m2v`.** *Vecchio-Collins 1986* for kind 1: the classic rule, in ε1/ε0, and far enough from the default that it is not the default again (the CSA rule nearly is, on this girder); its peak comes after softening has set in. *Hsu-Zhang 1998* for kind 3: of the three Hsu models it alone also uses its cap for high strength, which acts at 60 MPa; the other at M/V = 2 m, Hsu 1993, is the same form without the cap. *Vecchio-Collins 1992-A* for kind 2: it has the most rule of its own (the ratio, a factor for strength, a plateau in the curve); against it, its response in Response ends soon after the web cracks (a curvature of 0.55 rad/km, where the other two reach 2.3 and 2.6), so it tests the rule over a short range. All three repeat exactly in four captures. Two of the three are outside on a Must today (table above), so this is not a choice of easy cases. **Not suggested:** Collins 1978 (the one model of kind 2 whose peak clearly comes after softening) because its fixture is at M/V = 1 m and does not repeat (D63); "none" and Noguchi, whose responses in Response end just after the web cracks, where r2c goes on (+20.8 %): that is how a response ends, not a softening rule, and it would bring the largest known miss into the set; Kaufmann-Marti, the one that ends early in r2c (−10.7 %), which is a good diagnostic of the shear profile iteration but would be a fourth. If the owner wants only two: the first two |
| D63 | **Response's non-repeatability is in the stages it puts in while closing in on an event, and r2c has the stages of its longer variant. What follows for D48 and for the fixtures?** Measured (above, and `docs/status.md`): on the I-girder at M/V = 1 m Response closes in on the web cracking with ten stages in most runs (3 of 5 on the case in the set, 3 of 4 on Collins 1978) and with none in the others; r2c has exactly the ten. Softening 9 at M/V = 1 m repeats, with six such stages, and r2c has exactly the six. Softening 16 at M/V = 2 m lost one such stage in one run of four, at the closing of the top cracks. D48 is the same thing seen from the other side: at the closing of the top cracks at M/V = 1 m Response has no stage put in, in every capture so far (13 captures of three cases), where the rules as read say it should, and r2c has them. So the dropping of a stage put in between is something Response does not do the same way twice. Inferred, not read: the program takes such a stage from something that is not set by the input alone (memory left by an earlier stage or try, for one) | suggested | **(a) Leave the fixtures as they are** (D57 stands: the short capture of the I-girder with shear; the parked fixture of Collins 1978 likewise): every check comes out the same against either variant, so a change would move nothing. **(b) Record D48's stage as "Response does not repeat itself here", still a known deviation.** **(c) If the owner wants D48 taken up again, this is the named third approach the bounds ask for:** read what a stage put in between starts from that the input does not fix (`docs/kernel.md`, "A stage put in between": its first estimate and what is put back after a try is dropped), with the two variants of one capture as the test. Bounded to that reading. The developer suggests not now: the Must it would close is one shape check, and the softening cases come first |

### Where Response is unstable (2026-11-23, after A2)

| # | Question | Status | Answer |
|---|---|---|---|
| D54 | Matching the shear views needs a very tight clone, and some of Response's own views jump between neighbouring stages (the bond chart at the end of prestrained stirrups: 0.1 to 38 MPa from stage to stage, step A-2). Matching such a view at one stage is luck; the stage-by-stage measure makes it worse near cracking, the peak and the ending (D13, D25, D40, D42, D49) | decided, owner 2026-11-23 | **A view check where Response itself is unstable is reported, not assessed.** Unstable: Response's view at the stage lies farther than the views target from the blend of its neighbouring stages' views. Checks in steady stretches stay strict; the curves are not affected; every Must left unassessed is listed for the owner. The rule is in `docs/acceptance.md`, "Where Response is unstable". Carried out by the developer as a measure change before step A-3: views captured at the neighbouring stages, the test in the measure, the report showing Response's departure beside r2c's. **Done 2026-11-23** (log 2026-11-23-02): "The rule on unstable views" above; D55 and D56 came out of it |
| D55 | **Three readings of the rule's wording, for the owner to confirm.** (a) "At that stage's place along the control curve": the developer took the place by distance along the curve (load scaled by Response's peak, control value by its largest value, as the curves are measured), because it works on every branch, at a peak and across a fall of load, where load alone or control value alone turn back. (b) Response layers the section afresh at each stage, so the points of a view differ between neighbours: the blend is taken depth by depth. (c) A line that one neighbour draws and the other does not is blended with nothing. What each moves is in the table of readings above: (a) 48 to 78 of 1,554 checks with the other readings, none of them a Must miss; (c) nothing; (b) has no other reading that can be measured | decided, owner 2026-11-23 (readings confirmed) | **Confirm all three:** place by distance along the curve; blend depth by depth; a line one neighbour draws blended with nothing |
| D57 | **Response gives two different responses for the I-girder with shear (M/V = 1 m), run to run.** Same input, same loads, same program: 15 stages (the fixture, captured 2026-11-21, and one run of four on 2026-11-23) or 25 stages (three runs of four). The 25 hold the 15 with every view identical, and ten more stages between a shear of 366 and 463 kN, where the curve is the same straight rise. Peak, rising branch, post-peak, shape and every compared view of r2c come out the same against either. The other 28 cases repeated exactly. It is not the stage of D48 (that one is at 34 kN). Why Response does this was not looked into | decided, owner 2026-11-23 | **Keep the 15-stage fixture and note the case as not repeatable. From now on each new case is captured three times when the set is widened,** and any that does not repeat is noted before it joins; the direct evidence of Response's instability. Start with the cases of step A-3 |
| D56 | **The rule reaches further than its example: is that what was meant?** Views are compared at cracking, falls of load and the peak, which is where Response's views change most between stages; a steady stretch is not compared at all. So the rule leaves one check in five unassessed (318 of 1,554), nine in ten of them checks r2c was inside on. All 64 unassessed Musts were inside, r2c within 1.7 % of Response. It also takes 32 misses out of the count, among them known deviations (by case and stage: D47, and part of D32, D46 and D49). No Must miss is hidden by it. Whether a stage where Response jumps is one where a match "is luck" is a structural judgement and the owner's: r2c matches most of these jumps closely, which may not be luck | decided, owner 2026-11-23 | **No: the rule reached too far. Narrow it to spikes.** A check is unassessed only where Response's two neighbouring views agree with each other (within the views target) and its view at the stage departs from their blend by more than the target. A step, such as cracking, stays assessed: r2c follows most of them closely, which is behaviour to clone, not luck, and leaving them out would hide a regression at the stages that matter most. Wording in `docs/acceptance.md`. Carried out as a measure change before step A-3 (the neighbour captures are already in the fixtures). (The developer had suggested keeping the rule as written for step A-3.). **Done 2026-11-23** (log 2026-11-23-03): the spike test leaves 4 checks unassessed where the first rule left 318, and does not catch the bond chart; D58 and D59 came out of it |
| D58 | **One reading of the spike test's wording, for the owner to confirm.** "Its two neighbours agree with each other, within the views target": the comparison measures one chart's points against another's curve, as a share of the first chart's largest value, and here neither neighbour is the reference. The developer measured it both ways, each neighbour on its own largest value, and took the larger. The other reading puts both neighbours on the scale of the chart at the stage, as the departure is. On the 29 cases the two give the same four checks | decided, owner 2026-11-23 (reading confirmed) | Confirmed: both ways, each neighbour on its own largest value |
| D59 | **The spike test does not catch the bond chart at the end of the prestrained stirrups, the example D54 was written for. Is that acceptable?** (structural) At the peak Response's chart is 9.5, 20.9 and 32.7 MPa at three stages running; along the whole response it changes level at about half its stages and comes straight back only once. By the test these are steps, and the check stays assessed. r2c is 2.7 % from Response at the peak today, so nothing is outside because of it; but D54's point stands for this view, that a match at one stage is not promised at another. More widely the spike test leaves 4 checks of 1,554 unassessed, all marginal, so as carried out it has almost no effect: the tiers stand as they did with no rule ("The rule on unstable views" above) | decided, owner 2026-11-23 (suggestion approved) | **Leave the spike test as it is, and keep the bond chart at the end of the prestrained stirrups on record as a view where agreement is not promised.** It is inside today (2.7 % at the peak). If it goes outside, the owner may exempt it by name (option a) rather than build a test around one chart. The spike test is kept: it is built, and it can only leave out a real spike. What the result shows: Response is steady almost everywhere, so the sensitivity of the shear views is mostly r2c's rules, not Response's noise, and the measure stays strict |

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
- **The set is still narrow.** Three more shapes, five reinforcement cases and eight
  material cases on Newbeam are in; the softening models, units and factors are parked.
  The parked cases are not run on every change, so a change that breaks one of them
  shows only when they are run again.
- **What moved on the parked cases: nothing** (the 48 that remain, run once in step A-3
  against the run at the end of step A-2; measured, `python tools/changes.py`; not a run
  of record). The kernel is the same, so this is as expected: no check changed side. Of
  the 37 that r2c solves, 23 are inside on peak, rising branch and shape. Outside, as
  before: eleven I-girders with shear (softening 0, 1, 2, 5, 6, 7, 8, 9, 11, 12, 14), the
  two cases in US units at M/V = 1 ft, the T-beam at M/V = 2 m. One I-girder ends early
  (softening 12).
- **The Should on shear views is getting no nearer as the set widens.** 10 of the 20
  shear cases are inside. Every miss on the new cases is a state on or after a flat
  peak, and the measure reads one stage there (D61).
- **The shear profile iteration is not resolved** (D50), and the parked I-girders with
  shear will be set members when the softening models come in (D62): an early end will
  be a Must there. Of the three proposed, two are outside on a Must today. One of 16 ends early now (softening 12; softening 9 is on the line at
  −5.0 %), three before D49. Which ones changes with any small change to the kernel.
- **A rule taken over in the reported state only.** A node with next to no shear strain
  is reported as Response reports it (no transverse strain, no stirrups), but its forces
  are still evaluated r2c's way. The difference in the forces is taken to be nothing
  (stirrups carry no axial load or moment); it was not measured by writing the other
  form. Which nodes these are near a face is not Response's node for node.
- **Four rules of the program are in the code and switched off** (`docs/status.md`).
  Each is one more thing to keep working while it is unused.
- **Part of the crack spacing routines was not read:** they branch on a setting of the
  section that could not be named. The branch taken over fits every chart compared,
  since step A-3 also with the other tension stiffening models and the factor 0.5. A
  case with crack spacings given, or in other units, may take the other branch.
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
- **Response is not repeatable on three cases found so far**, all on the I-girder with
  shear (D57, D63): the one in the set and softening 11, both at M/V = 1 m, and
  softening 16 at M/V = 2 m. Each time the difference is whether stages put in while
  closing in on an event are kept. A fixture is one capture, so on such a case it holds
  one of the variants. The eight new cases and 16 of the 18 parked softening cases
  repeated exactly in four captures each; the other 30 parked cases have one capture.
- **The rule on unstable views now does almost nothing** (D56 carried out, D59). Every
  check at cracking, a fall of load and the peak is assessed again but four. Views that
  Response itself changes from stage to stage without returning (the bond chart with
  prestrained stirrups) are assessed as they stand: inside today, not promised to stay
  so when the kernel or a case changes.
- **Speed.** Not worked on. The 29 cases take about two minutes on the owner's machine
  with all of them running at once (measured).
