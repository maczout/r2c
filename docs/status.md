# r2c: where it stands

The present state of r2c in detail, and the options for what comes next. The owner reads
`docs/summary.md`; this page backs it, and questions for the owner live there, not here.
History is in `docs/log/` and in git. First written at the end of the 2026-11-15 build; kept in the repository since
2026-11-17.

r2c is the Python clone of Response-2000's sectional analysis; r2x (`maczout/r2x`, branch
`park`, 0.5.0) drives Response-2000 itself and is the oracle. Version 0.1.0.

Roles as in CLAUDE.md: structural engineering is the owner's, software engineering the
developer's. Items that need a structural judgement are marked **(structural)**.

---

## 1. What exists

- `r2c solve` with r2x's options, exit statuses and record format (r2x-raw 1, all views).
  Left out as agreed: `--report`, `define`/sessions, `setup`; `health` prints a version line.
- Kernel in Python (numpy only): MCFT node with crack check, dynamic layering, flexure and axial
  driver, shear by the longitudinal stiffness method with Response's own stiffness rules
  and, since 2026-11-21, Response's own load stage control.
- Tools: `compare.py` (any two records: peak, rising and post-peak measured both ways,
  curve shape, detail views at the features of Response's curve), `verify.py` (r2c on a set of oracle records),
  `report.py` (verification results from a verify run), `dashboard.py` (the same results as
  one HTML page of pictures, for the owner's review), `trim.py` (record to fixture),
  `diagnose.py` (r2c at Response's strain states, along its control values, its calculated
  shear stress in Response's states, and its own stages with their profile error),
  `decompile.py` (a routine of r2k.exe from a Ghidra project kept outside the repository;
  who uses a constant), `viewlines.py` (one view's lines from two records, side by side),
  `changes.py` (the checks that changed sides of their target between two verify runs),
  `retrim.py` (re-cut the fixtures from the archive to hold the feature stages),
  `capture.py` (rebuild the oracle archive with r2x; `--add` captures a new case and cuts
  its fixture), `curves.py` (the control curves of two records point by point), `ends.py`
  (how each shear response ends in Response and in r2c, from a verify run), `scope.py` (which fixture has which
  input feature), `variants.py` (inputs derived from present ones by stated text edits),
  `probe.py` (what Response does with an input, through r2x), `scope_cases.py` (the 53
  scope cases and their first capture), `targets.py` (which cases are inside on peak,
  rising branch and shape; `--counts`: cases inside, check by check, which is the progress
  table of the summary), `nodes.py` (the node depths of two records at a stage: are r2c's
  nodes where Response's are), `branch.py` (where the states before a fall of load end, for
  a case without shear), `offsets.py` (the strain states of two records, stage by stage),
  `viewmisses.py` (the views outside target, per case and feature stage), `matching.py`
  (is a view outside because of the stage it is compared at), `trace.py` (what the stage
  control did, try by try, with shear), `stagematch.py` (does r2c have its stages where
  Response has them), `spacing.py` (r2c's crack spacing tables against a record's charts),
  `earlyends.py` (which shear responses r2c ends early, and where: the diagnostic of the
  shear profile iteration on the parked I-girders), `bond.py` (does the bond rule give a
  record's bond chart from its own stirrup stress chart),
  `check.py` (checks before pushing). `diagnose.py states --out` writes r2c's views in
  Response's states as a record, for `viewlines.py`. `decompile.py` also lists
  a routine's instructions (`a:ADDRESS`).
- 85 oracle fixtures, each with the detail views of the feature stages of Response's curve
  (cracking, falls of load, peak, last stage). **The development set, 29 of them, is in
  `tests/oracle`**: Newbeam with only its loads varied (17), since step A-1 (2026-11-22,
  D41) the seven on the Quick Define sections, and since step A-2 (2026-11-23) five whose
  variable is the reinforcement (all listed in `docs/summary.md`).
  **The other 56 are parked in `tests/oracle/parked`** (D16, D19): kept, and not run by
  default. The folder is the set: verify, capture, retrim and scope read one folder and not
  the folders under it. The inputs of the five of step A-2 are variants of r2x's
  (`tools/variants.py`), so verify on the set needs that folder among its `--inputs`.
- pytest: by default the reader and material rules, the cases of the set without shear
  (the five on Quick Define sections need `R2C_DEFINE_DIR`, r2x's `tests/reference/define`,
  the two on reinforcement `R2C_SCOPE_DIR`, and are skipped without them); `-m "slow and
  not parked"` the fourteen with shear; `-m parked` the parked cases (`R2C_RESPONSE_DIR`
  for Response's sample inputs, `R2C_SCOPE_DIR` for the inputs of the scope cases). Eleven
  parked fixtures need something removed: five have no test, and the six on Response's
  sample inputs that hold several sections have a test that they are refused (D23).
  The parked tests were run at the end of step A-2 for the first time since increment
  A4: one fails, Newbeam in US units at M/V = 1 ft, whose peak is 1.41 and 1.57 % under
  Response's on its two charts against a regression limit of 1.3 % (1.31 and 1.47 % at
  the end of step A-1; the limit was left as it is).
- Docs: `kernel.md` (each rule and its source), `verification.md` (what the results mean),
  `verification-results.md` (generated), `acceptance.md` (the owner's development targets),
  `scope.md` (every input an r2x solve can take, whether the manual documents it, and
  r2c's status on each; the checklist for "scope complete"), `scope-probes.md` (generated:
  what Response does with each).

## 2. Against Response-2000 1.9.7

The numbers are in `docs/verification-results.md`, what they mean in `docs/verification.md`
("Against the acceptance targets"), and the pictures on the results page. Since 2026-11-21
each case is assessed against the owner's development targets in `docs/acceptance.md`: ±5 %
on every metric, the curve's shape the same, views at the features of the curve.

**The development set under the rule on unstable views** (run of record of 2026-11-23
after the measure change of D54, the 29 cases; measured, `python tools/targets.py
VERIFY_OUT --counts`; views compared at the stage at the same place since D42, the last
stage of a shear case left out since D40, a check where Response itself is unstable left
out since D54). Cases inside target: peak 29 of 29, rising branch 29, shape 26, post-peak
21 (14 of the 15 without shear), views of the stress state without shear (Must) 14 of 15,
views Should 24 of 29 (10 of the 14 with shear), views Could 26 of 29. Without the rule
(`--before-d54`), as at the end of step A-2: Should 21 of 29 (7 of 14), Could 23 of 29;
the kernel is the same and so is every difference r2c has from Response.

**The rule on unstable views** (owner, 2026-11-23, D54; `docs/acceptance.md`, "Where
Response is unstable"). How it is carried out:

- *Fixtures.* Each of the 29 fixtures holds, besides its compared stages, Response's
  views at the stage before and after each of them, as sections `neighbour/N/VIEW`
  (`tools/trim.py`). Nothing is kept for a compared stage that is first or last on its
  curve. `tools/retrim.py ARCHIVE` cuts them from the full captures; `tools/capture.py`
  checks a fresh capture against a fixture with its neighbours. The parked fixtures have
  none, so on them nothing is tested and everything stays assessed.
- *The measure.* `tools/compare.py` (`place`, `blend_lines`, `departure`) blends the two
  neighbours' views in proportion to where the stage lies between them along the bottom
  control chart, and measures Response's own view against the blend as r2c's view is
  measured against Response's. Each compared view carries that departure in the results.
- *The assessment.* `tools/report.py` (`is_unstable`, `stage_checks`): a departure over
  `views_pct`, and over the printed precision, makes the check unstable; it is left out of
  its tier and listed with Response's departure beside r2c's difference. The results page
  marks such a view with a ring and lists the checks.
- *The readings* of what the wording leaves open are the developer's and wait for the
  owner (D55); `python tools/unstable.py VERIFY_OUT --readings` measures the others.
- *What it does on the 29* (measured, `python tools/unstable.py VERIFY_OUT`): of 1,554
  view checks 1,216 are tested and 318 are unstable (Must 64, Should 193, Could 61); 286
  of those were inside and 32 outside. The figures and every unassessed Must are in
  `docs/summary.md`; D56 puts the reach of the rule to the owner.

**Response does not repeat itself on the I-girder with shear** (measured 2026-11-23,
five captures of `igirder-mv` in all: `python tools/capture.py NEW_ARCHIVE … --only
igirder-mv`). Two responses come back: 15 stages with the peak at stage 12 (the fixture,
and one run of four on 2026-11-23) or 25 stages with the peak at 22 (three runs of
four, one of them in the Wine prefix the fixture was captured in). The 25 are the 15
with ten more stages after stage 9, at shears of 385 to 451 kN between 366 and 463 kN;
every view of the 15 is the same byte for byte in both. So `tools/capture.py` may report
this case as differing from its fixture, and that is not a fault of r2x or the input.
The other 28 cases of the set matched their fixtures, neighbours included. Not looked
into: why, and whether any parked case does the same (D57).

Of the known deviations below, these are now unassessed under the rule and no longer
count as misses, though r2c's differences are what they were: the views of the column
with shear at its peak (D47, 9 Should and 2 Could); transverse bond at the peak of the
I-girder with shear (D46, item 1); M/V = 0.5 m at its fall of load (4 Should) and three
views at its peak (transverse bond, stirrup stress, principal tensile stress); V alone
at the stage of Response's fall of load (D32 and D49 item 2, 9 Should and 2 Could); the
diagonal crack spacing of tension at cracking; transverse bond at cracking of "N + M + V
increasing together". The seven views of M/V = 0.5 m at its peak listed under D49
item 1 are steady in Response and stay misses.

Three things changed in what r2c calculates
or reports in step A-2: Response's handling of the shear strain profile is in use (owner,
D49: 11 checks inside and 22 outside on the 24 cases, known deviations below); a node
with next to no shear strain is reported as Response reports it; and the bond chart
counts stirrups at a node by their own depth (the last two: two checks inside, none
outside, on the 29). What changed is in `docs/verification.md`, "Step A-2"; the rules are
in `docs/kernel.md` ("The shear strain profile between passes", "A node with next to no
shear strain", "The shear charts").

**The five cases on reinforcement** (step A-2): every Must and Should inside. On the
three with shear the response ends differently in the two programs (a Won't; known
deviation 3 of the shear cases below).

Outside on a Must (D1, D2):

- **Shape: tension** (one rising point fewer before the fall at cracking). A known
  deviation for phase A (owner, 2026-11-22, D36); the solve that has the point stays off.
- **Shape: V alone** (r2c's fall of load before the peak is 1.9 % of the peak, the measure
  counts from 2 %, Response's is 2.2 %). A known deviation for now (owner, 2026-11-22, D32).
- **Shape: the I-girder with shear.** Part of the known deviation "the shear profile
  iteration" (below).
- **Views of the stress state without shear: the column under N alone, at its last stage.**
  The owner's override (C2, D12): r2c's uniform state after the peak stands. Up to the
  peak every Must and Should view is inside.

The last-stage point of "constant N +200 kN, then M" (D35) is inside since the
longitudinal table went on (6.2 to 1.4 %).

**Known deviation: the shear profile iteration** (owner, 2026-11-23, D50: D47, D48 and
the early ends are recorded as one known deviation; taken up in step A-1c with the two
approaches the bound allows, and the one lead left was tested against the oracle in step
A-2 and dropped). Within a stage Response solves the global strains, updates the shear
strain profile from the calculated shear stress, and repeats up to 16 times. r2c does the
same, since step A-2 with the program's own update and hand-over of the profile (D49),
and with a solve of the global strains of its own. Where the iteration settles the two
agree. Where it does not, or where a state sits on a flat part of the curve, they
differ, and three things follow from it:

1. *The column with shear, views at its peak* (a Should; D47). Eleven views are 6 to 28 %
   off at the same curvature and a load 0.2 % apart (nine of the Must or Should tier):
   the top of the curve is flat within 0.2 % over three stages and the two programs sit
   in different states on it. In Response's own state there r2c agrees on every such view
   within 2 % but transverse bond (measured in step A-1b; since step A-2 the bond rule
   itself gives Response's chart of this column from its own stirrup stress within 0.8 %,
   `python tools/bond.py`, so the rule is not it; not looked at again in Response's state).
2. *The I-girder with shear, shape* (a Must; D43, D48). The girder's top is cracked under
   no load and the cracks close at a shear of about 34 kN. r2c closes in on that event
   and keeps the stages it puts in between, two of them with the top still cracked (49.5
   and 51.8 kN), from which the load falls to 32.5 kN: 2.9 % of the peak. Response has no
   stage there at M/V = 1 m (30.9, then 34.5 kN), and has exactly r2c's stages at
   M/V = 2 m. `python tools/trace.py tests/oracle/igirder-mv.r2x.txt --input INPUT`.
3. *Parked I-girders with shear that end early* (not set members; they come into the set
   with the material models). `python tools/earlyends.py VERIFY_OUT`; the count on the
   present kernel is in section 4, "The parked cases". On softening 12 the trace shows
   what an early end is: after the web cracks both programs have a stage that has not
   converged, and then one whose load is within 0.2 % of the largest so far; Response's
   is just under it and is kept, r2c's is just over it and is refused.

*What was read* (step A-1c, all in `docs/kernel.md`, "The shear strain profile between
passes"): the profile update and its cap; when the update reports a stage as not solved
(the 3 × 3 solve and its fall-backs); what the stage control tests on every pass; what a
stage leaves for the next and what is put back after a failure; the step factor of the
global solve. The update and the hand-over are in use (D49); the tests on every pass and
the program's solve are written and off. *What was not read:* the forces routine's
iteration mode against its final mode (`004a9d90`), the right-hand side of the shear
flow calculation (`004252c0`, `00422570`, taken as read on 2026-11-19), the start of the
global solve before its loop.

*The depth lead, tested with the oracle and dropped* (step A-2, owner 2026-11-23, D50;
measured). The I-girder is exactly 1 m deep, and the thought was that at M/V = 1 m a
comparison of M/V with the depth falls the other way by rounding. The girder was
captured from Response at M/V = 0.99 m and 1.01 m (diagnostics, not set members, no
fixture committed: `python tools/capture.py ARCHIVE --from A_FOLDER_OUTSIDE --add
igirder-mv099 igirder.r2t --increment=0,0.99,1`, and `0,1.01,1`).

- *At 1.01 m* Response's stages are those of 1 m, stage for stage up to the web cracking
  (30.9, then 34.5 kN): no stage where the top cracks close. So nothing hangs on the
  last digit of the depth.
- *At 0.99 m* Response's base step is half as long (its rule for M/V under the depth,
  which r2c has), so one of its regular stages falls where the top is still cracked
  (50.0 kN; r2c 49.9) and its curve has the fall of load there. But between that stage
  and the next it again has none of the stages r2c puts in while closing in on the event
  (r2c: one more at 51.8 kN, top still cracked).
- So Response puts in no stage at that event at 0.99, 1 and 1.01 m, and all of them at
  2 m. The difference is not rounding against the depth. What separates M/V near 1 m
  from 2 m was not found, and by the owner's decision it is not looked for further now.

**Known deviations that came with Response's handling of the shear strain profile**
(owner, 2026-11-23, D49: it is switched on and these are accepted). Measured on the 24
cases, the run of record of step A-1c against the "before" run of step A-2 (`python
tools/changes.py`): 11 checks came inside and 22 went outside. No Must went outside
(the Must views are counted on cases without shear).

1. *M/V = 0.5 m, views at its peak* (Should and Could): shear stress 2.1 to 15.5 %,
   shear strain 4.5 to 13.9 %, principal tensile strain 4.1 to 12.2 %, transverse strain
   4.0 to 11.9 %, crack widths 3.6 to 10.9 %, stirrup stress at a crack 1.1 to 10.0 %,
   longitudinal concrete stress 2.7 to 9.4 %; and at its fall of load by a point,
   principal tensile strain and transverse strain 4.7 to 5.2 %. With them that case's
   Could views go outside.
2. *V alone, the stage of Response's fall of load at cracking* (part of D32's known
   deviation): eleven views, up to 100 %, and that case's Could views. Not a difference
   of state. r2c's fall of load at cracking is now 1.2 % of the peak (1.9 % before;
   Response's 2.2 %; the measure counts a fall from 2 %), so Response's stage after
   cracking is compared with r2c's stage before cracking, which has the same load. The
   measure comparing stages across cracking is noted by the owner as a recurring pattern
   (D13, D25, D40, D42, D49), for a meta-development session later.

What came inside with it: the rising branch of M/V = 0.5 m (9.9 to 3.6 %, a Must, so the
known deviation of D46 on it is gone); the post-peak of V alone (6.9 to 3.6 %) and of
"N constant, then V"; the Should views of "N constant, then M + V" and of "V constant,
then M".

**Known deviations that came with the longitudinal crack spacing table** (owner,
2026-11-22, D46), as they stand since D49:

1. *Transverse bond at the peak of the I-girder with shear, 49.8 %*, which keeps that
   case's Should views outside, and *of M/V = 2 m, 8.1 %* (22.5 % before D49): a spike
   at the end of the stirrups in a stage r2c has not converged. With the program's own
   global solve, which is off, the I-girder's is gone (measured in step A-1c).
2. *M/V = 0.5 m by a point:* longitudinal strain at its fall of load (5.0 %) and shear
   on the crack at its peak (6.2 %).

Gone since D49: the rising branch of M/V = 0.5 m and the post-peak of V alone.

**The views related to shear** (Should). Inside on 7 of the 14 shear cases: Newbeam at
M/V = 1 m, V with constant compression, "N constant, then M + V", "V constant, then M",
and the three shear cases on reinforcement. Outside: M/V = 0.5 m (D49, D46), M/V = 2 m
(D46), V alone (D32, D49), the column with shear and the I-girder with shear (the lists
above), and "M constant, then M + V" and "N + M + V increasing together"
(`docs/verification.md`, "A4").
Under the rule on unstable views (D54) the column with shear, the I-girder with shear
and "N + M + V increasing together" are no longer outside, because their misses are at
checks where Response itself is unstable: inside on 10 of the 14.

Written and off: Response's tests on every pass of a stage (`Shear.pass_code`); its solve of the global
strains with shear, with its step factor since step A-1c (`Shear.own_solve`; r2c has
fewer of Response's stages with it); its history of the stirrups' plastic strain
(`Analysis.own_stirrup_history`, D39); its general solve under a stepped axial strain
(`Flexure.own_axial`, D36). Not taken over: the turn of an angle by 180° at nodes made
late.

**Crack spacing** (Could). Both spacings are Response's tables on every shape (within
0.001 mm of its charts but at one node of the I-girder and one of the T-beam). `python
tools/spacing.py RECORD` sets r2c's tables against a record's charts without solving
anything.

**Known to be not the program's, and left** (found in step A-1b while reading the solve):
with shear, r2c carries on from a solve of the global strains that has not closed when it
is out of balance by less than 2 % (`Shear._solve`, "soft"). The status that was read for
(−2) is returned by the program's solve only without shear; with shear a solve that has
not closed is a stage not solved. Not changed: nothing on the 24 cases says which way it
would move them, and it wants its own measured step. Also r2c's own in the profile
iteration: half of the update under shear alone in the second half of the passes, and
the re-layering between passes.

**What follows describes all 85 cases as they stood in the sixth run of 2026-11-21**, the
last run of record with the parked cases, on the kernel before A2. The parked cases were
run once on the kernel of A2 (2026-11-22, not a run of record): of the 57 that it still
solves, four I-girder cases with shear went outside on peak, rising branch or shape (the
softening models Vecchio-Collins 1982 and 1992-A, Kaufmann-Marti with its peak at −8 %,
Hsu-Zhang) and four came inside (softening 7, 11 and 15, and the I-girder at M/V = 2 m);
check by check 119 came inside and 80 went outside. Not looked into: parked.

**All 85 cases, after increment S** (sixth run of 2026-11-21: the 32, and the 53 scope
cases; Response's own stage control in place of r2c's for the cases with shear). No case
fails or is refused. **51 of 85 are inside on peak, rising branch and shape** (39 in the
baseline before the increment), 27 of the 53 scope cases. By check, cases outside: peak 5,
rising 6, shape 33, post-peak 42. On the 32 earlier cases peak and rising branch are as
before; two shape checks came inside (`docs/verification.md`, "How a response ends").

**Known deviations, shear cases** (owner's brief of 2026-11-21: a shear case outside target
is recorded here; how a shear response ends is a Won't of phase A, owner 2026-11-22, D1).
On the phase A set these are: M/V = 2 m in item 1, M/V = 0.5 m in item 2, and in item 3
M/V = 0.5 m and 2 m. All of them are about where and how a response ends; in Response's own
peak states r2c's forces agree within 1 to 3 % on every one.

1. *r2c goes on past Response's end; the peak is outside* (5 cases): softening 0 and 8
   (+19.0 %), 5 (+10.1 %) and 6 (+5.5 %) on the I-girder at M/V = 2 m; the T-beam at
   M/V = 2 m (+7.4 %). Response's response ends while its load is still rising: on the
   I-girder just after the web cracks (its next stages do not converge and are kept because
   their load is under the peak; the third has collapsed), on the T-beam with stages
   standing still. r2c's profile iteration converges at those states, and under Response's
   own rules a converged stage is accepted. Inside target but the same thing: Newbeam at
   M/V = 2 m (+3.3 %; Response's stages stand still at a curvature of 39 rad/km).
2. *The rising branch* (6 cases): softening 7, 9 and 11 on the I-girder (5.3, 14.2 and
   6.5 %); Newbeam at M/V = 0.5 m (6.1 %; 18.2 % before step 4); the two cases in US units
   at M/V = 1 ft (13.1 and 7.3 %: one fall of load fewer than Response's on the way up).
3. *The last stage; the shape alone is outside* (22 shear cases). Response's response ends on a
   collapsed stage in most (a stage that had not converged after sixteen passes, kept
   because its load was under the peak); r2c's ends with stages standing still at the same
   plateau, or the other way round. r2c follows the same rule since step 4; which stage
   fails to converge is not always the same. 23 of the 50 shear responses now end as
   Response's does (14 before; `python tools/ends.py VERIFY_OUT`).

**Known deviation, the column under axial load alone after its peak (C2). Not cloned**
(owner, 2026-11-22, D12: it looks wrong in Response; r2c's uniform post-peak stands). A
parked case. Response leaves the uniform state (a curved state with no moment, the load falling by a quarter in
one step); r2c stays on it. Not resolved in step 4: on the two rectangular sections under
axial load alone Response keeps the uniform state to the end, as r2c does, and its control
variable does not change; what makes the circular column different was not found.

Marshall and the Newbeam with N₀ = −2000 kN, both without shear, are inside on
every check. Principal tensile stress is outside at 28 stages in 18 cases (58 in 23
before); in seven cases without shear it is the only view outside, by one point at the
crack front (option F2).

Stance (owner, 2026-11-21 and 2026-11-22, D34): the manual decides which features exist; for
those, r2c reproduces what the 1.9.7 binary does, apart from the owner's overrides in
`docs/acceptance.md`; no structural assessment of results is given. Once a case is inside target,
closing the gap further is not a goal: build out the scope.

### What is known about shear

**The stiffness in the shear flow calculation was the cause of responses ending short**, and
is now Response's own, read from the binary (`docs/kernel.md`, "The stiffness in the shear
flow calculation"). `tools/diagnose.py flow` puts r2c in Response's own states and compares
its calculated shear stress profile with the state's; Response's own two lines agree within
1 %. r2c's now do too (within a point of Response's figure) on Marshall, se100, the Newbeam
at M/V = 1 m with and without axial load, shear alone, M/V = 2 m to stage 78 of 87 and
M/V = 0.5 m to stage 39.

*Still different in Response's states:* 3 to 7 % after a fall of load, on the recovery
(M/V = 0.5 m from stage 41, the US case from 31); 2 to 5 % on Liping LB1 from stage 13; up
to 2 % at the end of M/V = 2 m. Not explained. The peaks of these cases agree within 1 %
all the same.

**Where a response ends is Response's own rule since 2026-11-21** (step 4 of increment S;
`docs/kernel.md`, "Load stages" and "Response's own load stage control", read from the
binary: `00418af0`, `00418860`, `00415e30`, `0041a870`, `00422de0`, `00419250`, `004162d0`,
`00419990`, `00420f20`, `004204b0`). r2c steps as Response steps (control variable, base
step, a tenth of the control value, a fifth of the way to an event), works on a stage in up
to sixteen passes, keeps a stage that has not converged when its load is not above the
largest so far, refuses it otherwise and tries closer, changes the control variable when
the step has been cut five times, and ends by Response's tests. Two things of r2c's own
changed with it: the shear strain profile is kept at the nodes' own heights (on a fixed
grid the profile iteration could not converge below 1.6 to 3.8 % in Response's measure; now
under 0.1 %), and the profile update is Response's own form.

- *M/V = 1 m (Newbeam):* r2c's stages are Response's stage for stage to the peak, the
  control changes to the shear strain at the same stage, the plateau after the peak is the
  same (193 kN). Response then has two collapsed stages; r2c's step dies on the plateau.
- *M/V = 2 m:* Response's stages stand still at a curvature of 39 rad/km; r2c converges
  there and goes on (+3.3 %; known deviation 1).
- *Shear alone:* the whole response is Response's, falling branch included.

**dm-n1n** (option B; reported, not chased): inside on every one of peak (+0.10 %; it was
+3.2 %), rising branch, shape and post-peak since step 4. What governs that section's
failure was not looked at.

## 3. Performance

Measured (2026-11-15, one core): Newbeam moment only, 62 stages, 1.6 s; Cm4, 90 stages, 10 to
20 s; Newbeam M/V = 1 m, 12 s to near the peak and about 125 s for the whole response; other
shear cases 90 to 250 s. Times per case on the latest run are in
`docs/verification-results.md`.

Response's own solve: Newbeam moment only, peak-only capture, 4.3 s end to end including
Wine start-up (measured). For shear, no peak-only capture was made: roughly 2 to 12 s for
start-up plus solve (estimated by subtracting chart reading from all-stage captures).

So: without shear the two are in the same range. With shear r2c is several times slower on the
stages it finds and roughly 10 to 50 times slower overall (estimated).

Shear cases in the sixth run of 2026-11-21 (Response's own stage control; 50 cases, 22 at
a time on 32 cores): a median of 66 s each, 126 s at most (measured; 78 s median in the
fifth run, with r2c's own stage control). The breakdown below is of 2026-11-15 and has not
been measured again; the driver it describes is gone.

Where the shear time goes (measured 2026-11-15): about 90 % after the last stage found,
retrying smaller steps and looking beyond a target, each attempt running to its iteration
limit (the same failure as stopping short); on the stages found, about 50 force evaluations
per stage at about 7 ms each, 80 % of it the transverse equilibrium solve, which starts from
scratch each time; and numpy call overhead on arrays of about 100 nodes.

## 4. Scope

`docs/scope.md` is the inventory: every input an r2x solve can take that reaches the
analysis, each marked as documented or not with the manual's page (2026-11-22), and with
one status. Completion is judged against Response as documented (owner, 2026-11-22).

- **Nothing documented is missing**, apart from what is out of scope by the owner's
  decision: hollow sections, long-term effects, strain discontinuity, the old text format,
  draped tendons (D4), the Hsu softening models with Tamai tension stiffening (D5).
- **Removed on 2026-11-22 as beyond the documented scope** (D10, D18) and refused since:
  compression softening 4, 16 and 17; a segmental curve for reinforcing steel. A drape other
  than zero and a Hsu model with Tamai tension stiffening are refused too, where they were
  read and ignored. A shape with no outline is an input error (D6).
- **Kept by the owner's decision** (2026-11-22): the softening models the manual names
  without a rule in the documents (D21); the default softening of Response 1.9.7, later
  than the manual (D22).
- **Refused since 2026-11-22** (D23): several sections in one file, and the horizontal tie.
  Response's sample inputs but dm-n1n hold several sections, so six parked cases are
  refused for it.
- r2c refuses as out of scope what is out by design or removed. Inputs Response itself
  rejects are input errors (curved outline rows, tension stiffening 5, `units="roman"`, a
  shape with no outline).
- **Not solvable with r2x** (measured; nothing to compare with): tension stiffening "None"
  (Response asks a question r2x does not answer); three load combinations on Newbeam.
- No case: a shrinkage profile of more than three points.
- Response's program folder is not read (D9): the shipped bar list is built in.
- `tools/capture.py` has rebuilt the oracle archive against Response (2026-11-19): all 25
  captures match their fixtures. The seven of 2026-11-21 and the 53 scope cases were
  captured once, with `--add`. r2x's clipboard helper can fail transiently (once in 25
  captures); a rerun of that case on its own then matched.

**The parked cases.** The 56 were run once at the end of step A-2 (2026-11-23, not a
run of record; `docs/log/2026-11-23-01.md`); r2c solves 45 of them. Inside on peak,
rising branch and shape: 31 of the 45 (30 at the end of step A-1b, the last run of all of
them). Outside: eleven I-girders with shear (softening 0, 1, 2, 5, 6, 7, 8, 9, 11, 12,
14), the two cases in US units at M/V = 1 ft, the T-beam at M/V = 2 m. Since the end of
step A-1b, check by check, 107 came inside and 51 went outside (the longitudinal crack
spacing table and the shear profile handling; the rules of step A-2 part 3 moved none).
Of the 16 parked I-girders with shear, one ends early (softening 12: peak −10.7 %, at a
curvature of 0.58 rad/km where Response goes to 2.34); softening 9 at M/V = 1 m is on
the line (−5.0 %). `python tools/earlyends.py VERIFY_OUT`.

**Where a next session picks up**: the owner's answers to D55 and D56 in
`docs/summary.md` (the readings of the rule on unstable views, and its reach). Then
material models as the next variable (step A-3, D53), the cases on Newbeam first; the
parked cases that join the set need their neighbouring stages cut into their fixtures
first (`python tools/retrim.py ARCHIVE --oracle FOLDER`). If the shear profile iteration is taken up again, start from
what was not read (section 2) and from what the two captures at M/V = 0.99 m and 1.01 m
showed (section 2; D51); `python tools/trace.py RECORD --set own_solve=1 --set
pass_code=1` runs a case with either of the program's rules that are written and off,
and shows the state code by pass and why the program's solve gave up.

## 5. Decisions that are the owner's

1. **Targets: set** (owner, 2026-11-21) in `docs/acceptance.md`, for development; reviewed
   when the focus moves from development to testing. All results matter, post-peak and every
   detail view included; ±5 % on every metric with a floor at Response's printed precision;
   the curve's shape the same; shear cases may be accepted with minor deviations depending
   on progress, recorded as known deviations here.
2. **Test set** (owner, 2026-11-21): the 25 cases are right for proof of concept and
   for building the clone; seven on Quick Define sections were added the same day (T-beam
   M and −M; column N, N₀ + M, M + V; I-girder M, M + V) and "Newbeam with tendons added"
   dropped. Range and completeness are reviewed when the scope of development is complete.
3. **Reverse engineering.** The original brief allowed it "to answer questions but not as the
   primary development approach". Since 2026-11-22 (D34, owner) the binary is the spec for
   how a feature in scope calculates and is read directly to solve problems; the manual
   still decides which features exist. Rules are written fresh, not transliterated from
   decompiled code.
4. **Dependencies.** numpy only. Compiling the node routine (option D4) would add one.

## 6. Options for next steps

Grouped, not ranked; the ranking for the next increment is D26 in `docs/summary.md`. Options
C and the softening and section-specific items concern parked cases and wait for phase B.
Sizes are rough. Since 2026-11-21 the targets decide what is work: a
check outside target is work, a gap inside target is not. Options that waited on the owner's
word because they reach past Response's peak (A3, G) or into the detail views (F, H, I) no
longer do: post-peak and every view are in the targets, and where r2c and Response differ,
Response is right (owner, 2026-11-21). Reading, for the owner to confirm: that this puts A3
and G in scope for development sessions.

**A. Shear: where the response ends, and how a stage is accepted.**
- A3. **Done 2026-11-21** (step 4 of increment S): Response's acceptance of a stage, its
  step control and its end tests are r2c's (section 2). Left of it: Response's global solve
  (`004276a0`) was read on 2026-11-22 for the case without shear and has not been set
  against r2c's solve with shear; r2c's own solve converges at some
  states where Response's does not (known deviations 1 and 3).
- A4. The differences left in Response's states (after a fall of load; Liping LB1 from
  stage 13): `tools/diagnose.py flow --profile` shows where over the depth.

**B. dm-n1n.** Inside on peak, rising branch, shape and post-peak since step 4 (section 2).
A structural read of what governs that section's failure is still open.

**C. The Quick Define sections: done for peak, rising branch and shape** (2026-11-21), but
for the last stage of the two shear cases (A3). Left on these sections, all in the views or
after the peak (`docs/verification.md`, "Quick Define sections"):
- C1. Crack spacing tables: **read 2026-11-22** (step A-1b); both in use since step A-1c
  (D46).
- C2. The column under axial load alone after its peak: Response leaves the uniform state
  (a curved state with no moment, the load falling by a quarter in one step); r2c stays on
  it. Looked at in step 4 and not resolved (section 2, known deviation).
- C3. The I-girder with shear: a fall of load at V = 26 kN and another at a curvature of
  0.39 rad/km in Response, neither in r2c (1.7 % and 4.3 % of the peak; inside target).
- C4. Curved outline segments: fall away. An input file cannot carry one (measured
  2026-11-21, `docs/scope.md` section 1.4).
- C5. Views at a step in width: **done 2026-11-22** (step A-1): r2c has Response's three
  nodes at a step. The transverse crack spacing has a point on each side of a step since
  step A-1b; the bond parameter and the steel ratio at a crack are still read from 100
  stations across it.

**D. Performance** (software).
- D1. The failing tail: shorter since 2026-11-19 (section 3), not measured in detail.
- D2. Warm-start the transverse equilibrium solve from the previous evaluation.
- D3. Analytic tangents in place of finite differences.
- D4. Compile the node routine (numba or a small C extension). Adds a dependency.
- D5. Measure Response's solve time properly: peak-only r2x captures of the shear cases.

**E. Housekeeping.**
- E3. Compare the untested combinations: now increment S, by `docs/scope.md`.
- E5. `tools/capture.py` could retry a case once when r2x fails, since the one failure seen was
  transient. Not done: one failure is not yet a pattern.

**F. Detail views.** The cracking-stress line on the Principal Tensile Stress chart is drawn
as Response draws it since 2026-11-21. Left: crack spacing on multi-layer sections; and
- F1. Cracking under compression in the node: **done 2026-11-22** (A2 part 2).
- F2. Node spacing at the crack front: **done 2026-11-22** (A2 part 2): Response's own
  layering, read from the binary; the layer 0.1 mm thick across a step in width since step
  A-1. Left of it: Response's limit on the number of layers, not read.
- F3. The crack check where no bar crosses the tension zone: **done 2026-11-22** (A3
  part 1, D30): the program's rule.
- F4. The shear charts: envelopes, signed shear on crack, transverse bond: **done
  2026-11-22** (A4). Left: the angle turned by 180°.

**H. Steel stress at a crack: done 2026-11-22** (A2 part 3; `docs/kernel.md`, "Steel stress
at a crack"). The Newbeam with CSA factors, where it was first seen, is parked and was not
looked at again.

**I. Detail views of the sample-input cases, found 2026-11-19.** Not investigated, except
Principal Tensile Stress under axial compression alone (Marshall 1900 %, Newbeam 371 %):
that was the cracking-stress line, gone since 2026-11-21. With shear: se100 Longitudinal Concrete Stress 15 % and
Average Angle 14 %, Liping LB1 Long. Reinf Stress at Crack 18 %, Marshall Shear Stress 8 %,
strains 5 to 8 %. Part may come from comparing at slightly different states (peaks differ by
0.1 to 4.5 %). Details in `docs/verification.md`. Whether they matter depends on what
acceptance says about detail views **(structural)**.

**G. End-of-response rules.** With shear: Response's own since 2026-11-21 (A3). Without
shear: r2c's own, which come to the same as Response's tests on the cases compared, but
for bar rupture and the end after it, which are Response's since 2026-11-22
(`docs/kernel.md`, "Load stages").

## 7. Reference for a working session

**The oracle.** Clone `maczout/r2x` (branch `park`), unpack Response-2000 1.9.7 (r2k.exe
SHA-256 `bbf4bc59…4e74`). One capture:

    python -m r2x.worker INPUT OUT --stage all --response-dir RESPONSE_FOLDER [options]

Negative option values need the `=` form (`--initial=-2000,0,0`). An all-stage capture takes
25 to 75 s; captures run one at a time in the default Wine prefix. `tools/capture.py` does
this for every fixture. The Newbeam input (`input.r2t`) is in r2x's
`tests/reference/newbeam`; the Quick Define inputs are r2x's
`tests/reference/define/quick-{tbeam,column,ibeam-strands}/hand.r2t`, captured under the
names tbeam.r2t, column.r2t and igirder.r2t (r2x records the input's name). The inputs of
the 53 scope cases are derived from those: `python tools/variants.py SCOPE_INPUTS --inputs
R2X/tests/reference` writes them (`tools/scope_cases.py` does the same into the archive's
`scope-inputs`). Verify with all three folders: `--inputs RESPONSE_FOLDER
R2X/tests/reference SCOPE_INPUTS`. Several captures can run at once, each in a Wine prefix
of its own (`tools/scope_cases.py --jobs N`).

**The thesis** is at `~/references/bentz-thesis/` on the owner's machine (thesis.pdf and
appen_a, b, c.pdf from hadrianworks.com's "About the programs" page, each with a
`pdftotext -layout` copy), outside every repository (owner, 2026-11-21).

**Routines in r2k.exe 1.9.7 already located** (addresses as the decompiler shows them).
Internal units in the binary: Pa and m; fc′ stored negative. `tools/decompile.py` shows any
of them (Ghidra 12, headless; the project with r2k.exe analysed is kept outside the
repository).

| Address | What |
|---|---|
| `004ad9c0`, `004ac960` | concrete stress, tangent |
| `004ac190`, `004af050`, `004aefa0` | concrete set-up, ε0, ft |
| `0046aaa0`, `0046a960` | MCFT node; crack strain, with its lowering by compression |
| `004a7b60` | the node routine for a node with next to no shear strain (uniaxial, no stirrups); the test for it is at the head of `004a8b20` |
| `00569f58` | flag for the lowering by compression; set in `004992b0`, `004b2580` |
| `004aea40`, `004ae630` | steel stress, tangent |
| `004ab4e0` | derived steel properties (rupture strain, tendon yield) |
| `004ae520`, `004ac830` | steel capacity at a crack, concentrated strain |
| `004bc470`, `004bd930` | steel ratio for strain concentration: layers, table for stirrups |
| `004a79d0`, `004a80e0`, `004a8b20` | stirrups, transverse resultant, εy solve |
| `004a9d90`, `004a9be0`, `00434eb0` | section forces and the splitting of layers; the split itself; the base layers |
| `00442e50`, `00442cd0`, `00440c70`, `004409d0` | steel stress at a crack: the routine, its solve for the extra curvature, the bars' moment at an extra curvature, the most the bars can add |
| `00441d80`, `00440400` | flexural crack check: the zones and their capacity moments; the limit profile of a zone (zero where the capacity moment is zero) |
| `004fec60`, `004ff1a0` | bond parameter tables |
| `00424a90`, `00423e50` | cracking strength table |
| `0041e840`, `0041fe20` | shear distribution: calculated profile and profile update; the change of strain along the member |
| `00427cd0`, `0046b940` | condensed stiffness of the nodes; the node's analytic stiffness |
| `004201e0`, `004a8710` | stiffness of bars and of stirrups in that calculation |
| `00424da0`, `004252c0`, `00422570` | assembly of the 3 × 3 system and its right-hand side |
| `00440ea0` | the depth range with stiffness (in the flexural crack check) |
| `00418af0`, `00418860`, `00415e30`, `0041a870` | load stage control: a pass on a stage, its wrapper (step growth, the peak, the end), a new stage and the closing in on an event, the next target |
| `00422de0`, `00419250`, `004162d0` | the control variable, its base step, the change of control variable |
| `00419990`, `00420f20`, `004204b0` | the end of the response; the profile error; the stage's state code |
| `00424c60`, `004276a0`, `00425f10` | the single-state solve; the general solve (with shear, and without shear under a stepped axial strain; its step routine `004267c0` not read); the secant solve without shear under a stepped curvature |
| `0041e1e0`, `00425af0`, `00416730`, `00433c50` | the unbalanced force; the secant's fall-back by halving; the first estimate of a stage; a new stage as a copy of the last |
| `004aaf70`, `00434c80`, `00418fd0`, `004a9030` | a bar's stress in a state (nothing once it ruptures at a crack); the ruptured marks put back from a stage; a stage deleted; the sums over layers and bars |
| `00480590`, `004837e0` | the data of the detail charts (ids under 200; the titles are a table at `00563650`); its caller |
| `0041b1d0`, `0047fcd0`, `00485640`, `00484420` | the envelopes of a stage; transverse bond, its factor, its window |
| `0041e310`, `004b5470`, `004b6a30` | the stirrups' plastic strain table written at acceptance; a table over the depth: a point added, read linearly |
| `0040e9f0` | set-up of another analysis class that steps in the shear strain from the start (taken to be the one for shear alone) |
| `004ac190`, `004ab4e0`, `004fbf70` | concrete set-up (Kf, n), derived steel properties (segmental curve), the steel ratio η of the Hsu models |
| `004f96e0`, `00448d90` | the reader of shape.dat and the outline dialog's width field: the only users of UP and DOWN |
| `004181d0`, `004ff4e0`, `00419ff0` | "cracked" for an event between stages; the cracking strain before it is lowered by compression; whether an event is closed in on |
| `004267c0`, `004688b0`, `00467f20` | the step of the general solve; the 3 × 3 solve by elimination with pivoting, and the 2 × 2 one |
| `004b67e0`, `00426f10`, `0041c060`, `004357d0` | a table's integral by Simpson's rule; the concrete area within the depth that has stiffness; the profile rebuilt from a stage's node strains; the profile of the uncracked section |
| `0043fa20`, `0043f570`, `0043faf0`, `0043e8d0`, `00440100`, `0043f0d0` | crack spacing over the depth: both tables; a layer's term; the longitudinal spacing at a height and its table; the transverse spacing at a height and its table |
| `004440d0`, `00423110` | steel stress at a crack as left during iterations; the shear strain a stage reports |
| `00417290` | a secant stiffness of the section ("error in moment calculation"); not the shear driver it was taken for |
