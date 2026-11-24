# r2c against Response-2000

r2c 0.1.0 compared with Response-2000 1.9.7, run through r2x 0.5.0 (the oracle).

**What this file is.** An interpretation of r2c's results against Response-2000, written by
hand. The numbers are not here: they are in `docs/verification-results.md`, generated from a
run of `tools/verify.py` and headed by the commit, machine and date of that run. Unmarked
numbers below are those of that run; numbers marked "2026-11-15 run" are from the earlier
comparison.

**Since 2026-11-22 the generated results cover the development set alone**
(`tests/oracle`): at first the 17 cases on Newbeam that vary only the load ("Phase A
baseline" below), since step A-1 the seven on the Quick Define sections as well, since
step A-2 five on reinforcement, since step A-3 eight on material models: 37 cases. The
other 48 cases are parked until phase B (`tests/oracle/parked`; `docs/summary.md`, D16 and D19) and
are not run by default. The sections after the baseline describe them as they stood in the
runs of 2026-11-21; those numbers are no longer in the generated file (they are in its
history in git, and come back with
`python tools/verify.py tests/oracle/parked --inputs …`). Five parked cases need a feature
that was removed on 2026-11-22 and r2c now refuses them (`docs/scope.md`, section 3).

Until then the generated results covered all 85 cases, since the run of 2026-11-21 on the scope cases:
the 32 below and the 53 of increment S (see "The scope cases" below). The 32 are the 25 of the first test set, the 7 on Response's
sample inputs (Marshall, Cm4, Liping LB1, se100, dm-n1n) included, and since the third run
of 2026-11-21 the 7 on Quick Define sections (T-beam, circular column, I-girder with
strands; see "Quick Define sections" below). For the first 25 the kernel is that of the
third run of 2026-11-19, after the shear flow stiffness was changed to Response's rules: no
check of theirs changed sides in the third run of 2026-11-21 (`tools/changes.py`). The 15 cases without shear are unchanged from the first
run; the detail views of the 7 sample cases were first compared case by case on that day
(see Detail views).
Whether a difference is acceptable is decided against `docs/acceptance.md`, not here.

Reproduce with `python tools/verify.py tests/oracle --inputs R2X/tests/reference
SCOPE_INPUTS --out OUT` (the parked set needs RESPONSE_FOLDER among the inputs as well), then
`python tools/report.py OUT`; compare any two records with
`python tools/compare.py REF SUBJECT --views`.

**Since 2026-11-23 a view check where Response's own view spikes is reported and not
assessed** (owner, D54, narrowed by D56): see "The spike test" below. It applies to four
checks of the 29 cases (six of the 37 since step A-3), so the sections written before that date, which count every
check as inside or outside, read almost as they would today.

## Step A-3: material models on Newbeam; the softening cases captured again (2026-11-23)

The set went from 29 to 37 cases; the kernel did not change. The figures are in
`docs/verification-results.md` and, for the owner, in `docs/summary.md`.

**The eight new cases** (two concrete base curves under M; five tension stiffening
models and the factor 0.5 under M + V at M/V = 1 m). Peak within 0.16 % and rising
branch within 0.18 % on every one, shape the same. The two without shear agree at every
compared stage on every view (largest difference 4 %) and end as
Response's do (0.3 and 0.0 %). Read with the earlier check of the same models in
Response's own peak states (forces within 0.4 %, "The scope cases after step 3"), the
material rules themselves are Response's; what is left is where a shear response sits
at and after its peak.

**The five view checks outside** (all Should; `python tools/viewmisses.py VERIFY_OUT
--only …`). For each, r2c was put into Response's own state at that stage (`python
tools/diagnose.py states FIXTURE --input INPUT --stages N --views`):

| Case, stage | View | Driver | In Response's state |
|---|---|---:|---:|
| Factor 0.5, peak (36) | shear on crack | 106.3 % | 0.03 % |
| Factor 0.5, fall (11), cracking (12) | transverse bond | 5.2, 6.7 % | 0.38, 0.15 % |
| Tamai, peak (38) | shear on crack | 10.6 % | 18.4 % |
| Elasto-plastic, peak (30) | transverse bond | 7.0 % | 0.60 % |

- *Factor 0.5 at the peak.* Response's peak is stage 36 of 38 at a curvature of
  4.731 rad/km, r2c's nearest stage is at 4.741; the loads of the last six stages of
  both lie between 192.8 and 193.5 kN. Shear on the crack is small everywhere with half
  the tension stiffening (0.15 MPa at most). Response's values start at 186 mm above
  mid-depth, r2c's at 180 mm, so over 6 mm one has 0.15 MPa and the other nothing: that
  alone is the chart's largest value. On top of it Response's largest positive value is
  0.0020 MPa against a largest negative of 0.147 (under a fiftieth: no positive limit
  line), r2c's 0.0043 against 0.19 (over a fiftieth: the line is drawn), and a line
  one program draws is counted as 100 % (D38).
- *Factor 0.5 at the fall of load and at cracking.* The bond chart's largest value is
  0.05 and 0.10 MPa; the differences are 0.003 and 0.009 MPa. The curves agree there
  within 0.02 kN.
- *Tamai at the peak.* Response's peak is stage 38 of 40 and the load is 193.0 to
  193.1 kN over seven stages. The limit line of shear on the crack is nothing above the
  cracked zone and 3.4 MPa at its first node (a crack of 0.004 mm); r2c's cracked zone
  starts 1.3 mm lower. In Response's own state the 18.4 % is that first node alone:
  Response has it cracked by 0.004 mm and r2c, from the printed strains, not yet.
  Every other point of the chart agrees within 0.003 MPa.
- *Elasto-plastic at the peak.* Both programs have the stage at 4.254 rad/km (219.30
  and 219.64 kN). The bond chart differs by 1.9 to 2.7 MPa of 20 over the bottom 60 mm
  of the stirrups. `python tools/trace.py` shows r2c's stage accepted after eight
  passes with a profile error of 0.90 %, under the program's 1 %.

**The spike test on the new cases.** Two more checks are left unassessed, both inside:
shear stress at the peak with Collins-Mitchell 1987 (Response's departure 6.8 %, its
neighbours 4.2 % apart, r2c 0.1 % from Response) and longitudinal bond at the peak with
Izumo (6.8, 1.8, 0.0 %). On the 37 cases: 6 of 1,953 checks.

**How the responses end** (`python tools/ends.py VERIFY_OUT`). Izumo and the factor 0.5:
both programs end standing still, at 98 and 100 % of the peak, with the same number of
stages. Vecchio-Collins 1982 and Collins-Mitchell 1987: both end falling, Response's
last stage at 19 and 23 % of its peak, r2c's at 92 and 94 %. Tamai and elasto-plastic:
Response's ends falling (25, 97 %), r2c's stands still. A Won't (D1).

**The softening cases on the I-girder, captured three more times** (not set members).
`python tools/repeat.py ARCHIVE NEW1 NEW2 NEW3`: 16 of the 18 are the same record four
times. The two that are not, and the reading of the ten stages that come and go, are in
`docs/status.md`, "Where Response does not repeat itself". Against the long variant of
the I-girder with shear of the set (25 stages) r2c's stages from the web's cracking
on are Response's one for one; its peak, rising branch and shape checks come out as
against the fixture (peak +0.04 %; rising branch 0.04 % on the shear chart and 2.4 % on
the moment chart, where the two stages of D48 are; shape different by that fall).

## The spike test (D56), a change to the measure (2026-11-23)

No change to what r2c calculates: the run of record (`docs/verification-results.md`) has
the same differences from Response as the run before it, number for number (measured:
the two runs' results set side by side, the new field and the run's identity left out).
What changed is which view checks are left unassessed (owner, 2026-11-23, D56;
`docs/acceptance.md`, "Where Response is unstable"): only those where Response's views
at the two neighbouring stages agree within the views target and its view at the stage
departs from their blend by more than the target.

**What the generated file now shows.** "View checks by tier": for each tier the checks
inside, outside and unstable under the spike test, then the same checks with no rule,
and under the rule as first written. "Detail views where Response is unstable": each
unstable check with three numbers, Response's departure from the blend of its
neighbours, how far the neighbours are apart, and r2c's difference from Response.

**What it means.**

- *The spike test catches almost nothing.* Four checks of 1,554, against 318 under the
  rule as first written: principal tensile stress at cracking of the column under
  N₀ then M (departure 5.0 %, neighbours 4.1 % apart) and at the peak of Newbeam under
  −2000 kN then M (6.3 %, 3.8 %); shear on the crack at the peak of "V constant, then M"
  (8.9 %, 1.4 %); longitudinal bond at the peak of M/V = 1 m (7.3 %, 3.7 %). r2c is
  within 0.4 % of Response at each. All four are near both thresholds; none is a jump
  of the size the rule was written for.
- *Why so few.* Views are compared at cracking, falls of load and the peak. What
  Response's views do there is move to a new state (the 314 other checks of the first
  rule: neighbours more than 5 % apart). Response returning to where it was after one
  stage is rare at those stages.
- *No case's tier result changes* against no rule: Must 14 of 15, Should 21 of 29, Could
  23 of 29. The 32 misses that the first rule set aside are counted again.
- *The bond chart along the prestrained stirrups is not caught.* At its peak (stage 28)
  the chart's largest value is 9.5, 20.9 and 32.7 MPa at stages 27 to 29: departure
  18.0 %, neighbours 71 % apart, so a step by the test. At cracking (stage 9): 0.003,
  0.005 and 18.6 MPa, neighbours 100 % apart. Over the whole response
  (`tools/unstable.py --trace` on the full capture) the first rule would leave 19 of
  the 41 testable stages unassessed and the spike test one (stage 12: 18.6, 0.13,
  18.6 MPa). The chart moves between levels and seldom comes straight back. Put to the
  owner as D59 (`docs/summary.md`).
- *The one-way measure and a drop to nothing.* Stage 19 of the same chart (37.2, 1.4,
  37.3 MPa) has a departure of 4.9 %: the stage's own points, all small, lie near the
  foot of the blend, and the blend's peak has no point of the stage to be far from. The
  comparison measures r2c against Response the same one-way (Response's points from
  r2c's curve); nothing was changed.
- *The readings* move at most 3 checks (`docs/summary.md`, D55 and D58).

Reproduce: `python tools/unstable.py VERIFY_OUT [--list] [--readings]`;
`python tools/unstable.py --trace CAPTURE VIEW`;
`python tools/targets.py VERIFY_OUT --counts [--before-d54 | --d54-first]`.

The section below describes the rule as first written; its counts are the "as first
written" columns of today's tables.

## The rule on unstable views as first written (D54), a change to the measure (2026-11-23)

No change to what r2c calculates: the run of record
(`docs/verification-results.md`) has the same differences from Response as step A-2's,
number for number (measured: the two runs' results set side by side, the new fields
left out). What changed is which view checks are assessed (owner, 2026-11-23, D54;
`docs/acceptance.md`, "Where Response is unstable").

**What the generated file now shows.** "View checks by tier": one check is one view at
one compared stage of one case; for each tier the checks inside, outside and unstable
in Response, and what they were before the rule. "Detail views where Response is
unstable": each such check with Response's departure from the blend of its neighbouring
stages, then r2c's difference from Response, and "(outside)" where r2c's difference
would be a miss. A case's assessment says how many of its checks are unstable. The
"worst case per view" table and each case's worst view leave those checks out.

**What it means.**

- *Most of what the rule sets aside is agreement, not disagreement.* 286 of the 318
  unstable checks were inside. Response's principal tensile stress at the peak of
  Newbeam under M departs 35.5 % from the blend of its neighbours and r2c is 0.1 % from
  Response there: Response's view moves a great deal from stage to stage at a peak, and
  r2c moves with it. Whether such a match is luck is the owner's to judge (D56).
- *Where it is disagreement,* the 32 misses set aside are on six cases, and in most of
  them r2c's difference is about the size of Response's own departure (the column with
  shear at its peak: transverse bond 28.5 % against 32.1 %, stirrup stress 14.0 %
  against 14.0 %). Those are the cases the rule was written for. Two are not like
  that: transverse bond at the peak of the I-girder with shear (r2c 49.8 %, Response's
  departure 9.9 %) and at cracking of "N + M + V increasing together" (71.5 % against
  14.0 %); and the eleven views of V alone at Response's fall of load are up to 100 % off
  because the stage is compared across cracking (D32), with departures of 5.7 to 50 %.
  The rule asks only whether Response is unstable, not by how much r2c is off, so all of
  these are unassessed alike.
- *The features of the curve are where Response is unstable.* Of the checks tested, 155
  of the unstable ones are at cracking, 104 at a peak and 59 at a fall of load; those
  are the only stages compared, apart from the last, which has no stage after it and is
  not tested.
- *The readings* of the rule's wording move 48 to 78 checks of 1,554 at most
  (`docs/summary.md`, D55).

Reproduce: `python tools/unstable.py VERIFY_OUT [--list] [--readings]`;
`python tools/targets.py VERIFY_OUT --counts [--before-d54]`.

## Step A-2: the shear profile handling on; the depth lead; reinforcement (2026-11-23)

The run of record of step A-2 (`docs/verification-results.md`, 29 cases; all measured,
one machine, `python tools/changes.py` and `python tools/targets.py --counts`). The
development set since this step is 29 cases: the 24, and five whose variable is the
reinforcement (`docs/summary.md`, "The development set").

**Response's handling of the shear strain profile, switched on (owner, D49): 11 checks
came inside, 22 went outside**, on the 24 cases against the run of record of step A-1c;
it is the same result as the trial of step A-1c, check for check. Inside: the rising
branch of M/V = 0.5 m (9.9 to 3.6 %, a Must); the post-peak of V alone (6.9 to 3.6 %) and
of "N constant, then V" (15.4 to 3.5 %); shear stress at the peak of "N constant, then
M + V" (15.5 to 1.2 %) and of "V constant, then M" (33.0 to 0.1 %), with principal
tensile stress there (20.9 to 0.0 %); the angle at the peak of M/V = 2 m (71.8 to 2.9 %).
Outside, and known deviations by D49 (`docs/status.md`): seven views at the peak of
M/V = 0.5 m (up to 15.5 %) and two at its fall of load by a point; eleven views at one
stage of V alone, which is compared across cracking (D32). By case: rising branch 23 to
24, post-peak 16 to 18, Should views 14 to 16, Could views 20 to 18. This run is the
"before" of step A-2.

**The depth lead (owner, D50): tested with two captures from Response and dropped.** The
I-girder with shear at M/V = 0.99 m and 1.01 m (`python tools/curves.py CAPTURE
R2C_RECORD --chart moment_phi`). At 1.01 m Response's stages are those of 1 m up to the
web cracking. At 0.99 m its base step is half as long, a regular stage falls where the
top is still cracked (50.0 kN; r2c 49.9), and the curve has the fall of load there; but
it has none of the stages r2c puts in while closing in on the event (r2c: one more, at
51.8 kN). So Response puts in no stage at that event at 0.99, 1 and 1.01 m and all of
them at 2 m: not rounding against the depth. r2c on the two captures: peak +0.4 and
0.0 %, rising branch 2.2 and 2.4 %, shape different on both (as at 1 m).

**The five cases on reinforcement** (moved into the set as they were; before any kernel
change for them): every Must inside on all five. Bars with a prestrain and with a thermal
strain, under M: peak 0.00 %, rising branch 0.01 % and less, every view inside at
cracking, peak and last stage. No stirrups, M + V: peak −0.02 %, every view inside at
cracking and at the peak. Interlocking hoops on the column, M + V: peak −0.11 %, every
view inside at cracking and at the peak, where the column with a single hoop has eleven
views outside (D47). Prestrained stirrups, M + V: peak +0.04 %, one view outside,
transverse bond at the peak, 52.8 %.

**Transverse bond with prestrained stirrups: two rules from the binary, 52.8 to 2.7 %.**
(1) r2c took the stirrups to reach a little beyond their end (a table read between its
points), and so took the prestress that stops at the end for a change of stress along
the stirrup: 18.6 MPa of bond at the top end where Response has nothing. (2) Response
takes a node with next to no shear strain through a routine with no transverse strain
and no stirrups; with prestrained stirrups its Stirrup Stress chart then shows nothing
at such a node, and its bond chart at the bottom end of the stirrups jumps from stage to
stage with which nodes those are (`docs/kernel.md`, "A node with next to no shear
strain"). With both rules r2c's bond rule gives Response's bond chart from Response's own
stirrup stress chart within 0.4 % at every stage of that capture (`python tools/bond.py
CAPTURE`; 355 % at the peak before). On the 29 cases two checks came inside (that view,
and that case's Should views) and none went outside.

**By case, the 29:** peak 29, rising branch 29, shape 26 (the three of the 24), post-peak
21 (14 of the 15 without shear), Must views 14 of 15 (the column under N alone, C2),
Should views 21 (7 of the 14 with shear), Could views 23.

## Step A-1c: the longitudinal crack spacing table; the shear profile iteration (2026-11-22)

The run of record of step A-1c (`docs/verification-results.md`, 24 cases) against the run
of record of step A-1b (`python tools/changes.py`; all measured, one machine). One thing
changed in what r2c calculates: Response's longitudinal crack spacing table is in use
(owner, D46). The run the owner asked to be recorded as "before" in this step is that
kernel; the run of record is the same kernel with rules added that are switched off, and
the two agree check for check.

**The longitudinal table: 43 checks came inside, seven went outside**, as measured in step
A-1b before it was switched on. Inside: every check of longitudinal crack spacing (17),
with the crack widths and diagonal spacing that follow from it; shear stress at the peak
of the column with shear (7.7 to 2.6 %); the last-stage point of "constant N +200 kN,
then M" (6.2 to 1.4 %, the known deviation of D35, a Must); shear on the crack at
cracking of M/V = 2 m (100 to 0.0 %; inferred: the limit line of D38, which both programs now draw). Outside, and
known deviations by D46 (`docs/status.md`): the rising branch of M/V = 0.5 m (2.7 to
9.9 %, r2c's last stage counted with the rising branch); transverse bond at the peak of
the I-girder with shear (2.5 to 49.8 %) and of M/V = 2 m (3.7 to 22.5 %); longitudinal
strain at the fall of M/V = 0.5 m (2.4 to 5.2 %) and shear on the crack at its peak (4.7
to 5.7 %); the post-peak of V alone (3.7 to 6.9 %). By case: rising branch 24 to 23,
Must views 11 to 12 of 13, post-peak 17 to 16, Should views 15 to 14, Could views 15 to
20.

**The shear profile iteration: read, written, tried, and left off.** The rules are in
`docs/kernel.md`, "The shear strain profile between passes", with a table of what each
does when switched on by itself: on the 24 cases, and on the 16 parked I-girders with
shear, which are the diagnostic the owner set for this part (`python tools/earlyends.py`:
how many end early, and where). In short:

* nothing read changes the column with shear at its flat peak (D47) or the stage the
  I-girder with shear keeps at M/V = 1 m (D48);
* the program's handling of the profile brings the rising branch of M/V = 0.5 m back
  inside (9.9 to 3.6 %) and moves 22 checks outside, 11 of them one stage of V alone
  that is compared across cracking (D49);
* the program's own solve of a stage, corrected for its step factor, removes the
  transverse bond spike at the I-girder's peak (49.8 to 0.0 %) and leaves r2c with fewer
  of Response's stages (`python tools/stagematch.py`: M/V = 2 m 59 to 47 of 87);
* of the 16 parked I-girders, 3 end early on the kernel of record (softening 12, 7 and
  9), 2 with the profile handling, 1 with the profile handling and the solve together.
  Softening 12 ends early in every trial.

The parked I-girders are not set members and are not assessed; the figures above are
counts of the tool, not results against a target.

## Step A-1b: the measure, the stage control, crack spacing (2026-11-22)

The run of record of step A-1b (`docs/verification-results.md`, 24 cases) against the run
recorded as "before": the same 24 cases on the kernel of step A-1, measured with the
stage matching of D42 (`python tools/changes.py`; all measured, one machine). The rules
are in `docs/kernel.md`.

**The measure first (D42, owner).** Views are now compared at r2c's stage at the same
place as Response's feature stage, where there is one within the target and not across a
fall of load; at the stage of the same feature otherwise. On the kernel of step A-1 that
alone moved 44 assessed checks inside and 4 outside (the run of record of A-1 against
"before"): the column with shear at cracking (no longer compared four stages apart: every
Must and Should view inside, the worst 3.7 %) and at its peak (seven views), M/V = 2 m at its peak
(12 views), M/V = 0.5 m at its fall (7); outside, four views at the peak of M/V = 0.5 m
(principal tensile stress 3.6 to 11.6 %, stirrup stress 3.5 to 11.4 %, two by a point),
as foreseen in D42. By case the Could views went from 14 to 15 of 24; nothing else changed
in the counts. Six stages are still matched by feature, all of them last stages of shear
cases, which are not assessed.

| Change to the kernel | Came inside | Went outside |
|---|---|---|
| "Cracked" for an event tested before the lowering by compression; a stage put in between starts from the nearer neighbour and is dropped when refused | none | none |
| Response's transverse crack spacing table | 14: transverse crack spacing at every stage of the three column cases and the two T-beam cases (11.0 and 5.7 to 0.0 %); shear on the crack at the peak of the I-girder with shear, 7.3 to 1.0 %, which brings that case's Should views inside | shear stress at the peak of the column with shear, 2.9 to 7.7 % |

By case: views Should 14 to 15 of 24 (3 of the 11 with shear); nothing else changed in the
counts, and no figure of peak, rising branch or post-peak moved to the other side.

**What the stage control rules changed is where r2c's stages are**, which the checks do
not see (`python tools/stagematch.py tests/oracle BEFORE AFTER`). Under V with a constant
compression r2c had seven stages closing in on the first node to crack under compression,
which Response does not have; they are gone (stages up to the peak 30 to 24, Response's
25). On the I-girder with shear r2c has two stages more (26 up to its peak, Response 13).

**The I-girder with shear's shape (D43) is as it was.** Response puts no stage where the
top cracks close at M/V = 1 m, and it does on every case of the same girder at M/V = 2 m
(the parked ones), where r2c now has its three stages to within 0.1 kNm. Why the two
ratios differ was not found (`docs/kernel.md`, "Open: the same girder at M/V = 1 m").

**The two new shear cases on their views** (`python tools/viewmisses.py VERIFY_OUT --only
column-mv igirder-mv`; `python tools/diagnose.py states RECORD --views`):

- *The I-girder with shear:* every assessed view inside (the worst 2.5 %). In Response's
  own state at the peak shear stress, shear on the crack, stirrup stress and transverse
  bond are within 0.4 %.
- *The column with shear:* at cracking every Must and Should view is inside; three
  cracking views are 21 % off, which is the longitudinal crack spacing (D46). At the peak
  ten Must and Should views are 7.7 to 14 % off, at the same curvature and a load 0.2 %
  apart: the state differs on a flat top. In Response's own state at that stage every
  Must and Should view agrees within 2.0 % but shear on the crack (6.4 %; 1.5 % with the longitudinal
  table on) and transverse bond (12.5 %, not explained; the bond rule was not checked on
  a hoop).

**The longitudinal crack spacing table is written and off** (D46): what it moves is in
`docs/kernel.md`, "Crack spacing over the depth".

**The parked cases** were run once after it; what moved is in the Risks of
`docs/summary.md`.

## Step A-1: other shapes (2026-11-22)

The run of record of step A-1 (`docs/verification-results.md`, 24 cases), against the run
of the same 24 cases made when the seven Quick Define cases came into the set, on the
kernel of A4 (`python tools/changes.py`; all measured, one machine). Both are assessed with
the last stage of a shear case left out of the view checks (D40). The rules are in
`docs/kernel.md`.

| Change | Came inside | Went outside |
|---|---|---|
| Response's layer 0.1 mm thick across a step in width | T-beam under −M: steel stress at a crack at the last stage, 100 to 0.0 % | none |
| Steel stress at a crack: the step of its solve; the plastic strain of a bar that has unloaded | I-girder under M: steel stress at a crack at cracking, 5.2 to 0.0 %, and at the last stage, 47.6 to 0.0 % | none |
| The try after a refused stage goes half a step further (with the layer across a step) | I-girder with shear, at the peak: longitudinal strain 5.7 to 0.0 %, principal tensile strain 5.7 to 2.3 %, shear strain 5.8 to 2.4 %, transverse strain 5.6 to 2.3 %, transverse bond 98.9 to 2.5 % | none |

In all 8 checks came inside and none went outside. No check on a Newbeam case changed
side, and no Newbeam case's peak, rising branch or post-peak figure moved by more than
0.05 points. By case: Must views 9 to 11 of 13; nothing else changed in the counts. The
I-girder with shear's peak went from −1.65 to +0.05 % and its stages from 49 to 25
(Response: 15).

**The transverse bond on the I-girder** is worth a note, because the chart's values there
are not physical: at the web's edge the stirrup stress falls from yield to nothing across
the step, and the chart shows the bond that jump would need, 20 MPa at the top of the web
and 3249 MPa at the bottom at Response's peak. With one boundary on the step r2c spread the
jump over half a web layer; with Response's thin layer it has Response's figures (in
Response's own state at the stage before the peak, 99.8 to 0.0 %).

**What the seven new cases still miss** (`python tools/viewmisses.py VERIFY_OUT --only …`,
`python tools/matching.py`, `python tools/diagnose.py states RECORD --views`):

- *Shape, the I-girder with shear* (a Must): one fall of load in r2c's curve where the
  girder's top cracks close, which Response's curve does not have (`docs/status.md`;
  D43).
- *The column under N alone after its peak*: the owner's override (C2).
- *The column with shear, views at cracking*: the stage compared is not the same state
  (D42). *At the peak*: a flat top, the largest loads two stages apart.
- *Shear on the crack* in Response's own states: 6.4 to 6.7 % on the column, 8.5 % at one
  node on the I-girder. It follows the crack spacing, which r2c does not have right on
  these shapes (`docs/status.md`, "Crack spacing on the other shapes"; D45).
- *Crack spacing and what follows it* (Could): on six of the seven.

**The parked cases** were run once after it; what moved is in `docs/status.md` and in the
Risks of `docs/summary.md`.

## A4 (2026-11-22)

The run of record of increment A4 (`docs/verification-results.md`), against that of A3
(`python tools/changes.py`; all measured, one machine). The rules are in `docs/kernel.md`.

| Change | Came inside | Went outside |
|---|---|---|
| Response's solve under a stepped curvature, on (D35) | M, principal tensile stress at the last stage, 7.2 to 0.4 % | "constant N +200 kN, then M", the same view at its last stage, 1.1 to 6.2 % (known deviation, the owner's) |
| The longitudinal limit between the tension zones | 11 checks: nine at diagonal cracking on "N + M + V together" (5.9 to 13.2 % before, 1.5 to 4.4 % after), principal tensile stress and stirrup stress at the peak of M/V = 0.5 m (15.7 and 15.2 to 3.6 and 3.5 %) | none |
| The envelopes, shear on crack, transverse bond as the program draws them | shear strain at cracking on M/V = 1 m and 2 m (8.8 and 8.2 to 1.4 and 0.0 %); shear on crack at the last stage of "N constant, then M + V"; transverse bond at the fall of V alone | shear on crack at one stage each of "M constant, then M + V" and M/V = 2 m (a limit line one program draws and the other does not, at values under 0.002 MPa; D38); transverse bond at the peak of "M constant, then M + V", 2.6 to 7.7 % (the stirrup stress steps by 380 MPa in r2c's state, 428 in Response's) |

In all, 16 checks came inside and 4 went outside. By case nothing changed: peak and rising
branch 17 of 17, shape 15, post-peak 12, the view Must 7 of 8 (M in, "constant N +200 kN,
then M" out), views Should 8 of 17: the eight cases without shear. None of the nine cases
with shear is inside on its views.

**What keeps the nine shear cases outside on the views** (`python tools/viewmisses.py
VERIFY_OUT --shear --tier must should`; and `python tools/diagnose.py states RECORD
--views`, which puts r2c in Response's own states):

- *The last stage*, on eight of the nine (all but "M constant, then M + V"): r2c's response ends elsewhere than Response's (a
  Won't, D1), and the views are compared there all the same (D40). M/V = 1 m and V with
  constant compression are outside for this alone.
- *A state that differs although the curves agree.* The peak of "constant V, then M":
  shear stress 33 %, one node at the crack front, with the two states 0.00015 mm/m apart;
  in Response's own state r2c has Response's value. The peak of "N constant, then M + V":
  shear stress 15.5 %, also one node; this one is the stirrups' history (D39). The peak of
  "M constant, then M + V", which r2c reaches seven stages later.
- *Known deviations of the curve*: M/V = 0.5 m at its fall of load and M/V = 2 m at its
  peak are compared in different states (`docs/status.md`); V alone at its fall (D32).
- *A rule not taken over*: the angle of 180° at two nodes (M/V = 2 m at its peak).
- *Transverse bond at diagonal cracking* on "N + M + V together", 70 %: a step in stirrup
  stress at a slightly different place; the stage is one neither program has converged
  (profile error 1.3 % in Response's state, 1.9 % in r2c's).

In Response's own states, at the stages that are not a collapsed last stage, r2c's views of
shear are within target but for: shear stress at the fall of M/V = 0.5 m (5.9 %, the
calculated line; `docs/status.md`, option A4), stirrup stress at the last stages of V alone
and "constant V, then M" (7.2 and 6.4 %; the stirrups' history), and the angle above.

## A3 (2026-11-22)

Measured on the 17 phase A cases, each change against the run before it (`python
tools/verify.py tests/oracle ...`, `python tools/targets.py OUT --counts`, `python
tools/changes.py BEFORE AFTER`; this machine). The baseline is the run of record of A2.

| Check | A2 | Part 1 (D30) | Part 2 (−M's ending) |
|---|---:|---:|---:|
| Peak | 17 of 17 | 17 | 17 |
| Rising branch | 17 of 17 | 17 | 17 |
| Shape | 15 of 17 | 15 | 15 |
| Views, Must (stress state, without shear) | 5 of 8 | 6 | 7 |
| Post-peak | 11 of 17 | 11 | 12 |
| Views, Should | 8 of 17 | 8 | 8 |
| Views, Could | 7 of 17 | 7 | 8 |

* **Part 1.** A tension zone that no bar crosses is limited to zero, as in the program
  (D30). N + M, principal tensile stress at cracking: 51.5 to 0.3 %. No other check changes
  side.
* **Part 2.** A bar that ruptures at a crack is gone in the state where it ruptures;
  Response's stepping at a rupture and its end test (`docs/kernel.md`, "Flexural crack
  check" and "Load stages"). −M's last two stages are Response's: post-peak 20.3 to 0.0 %,
  longitudinal strain and principal tensile strain at the last stage 5.3 and 5.9 to 0.0 %,
  crack widths there 5.7 to 0.5 %. No check went outside. Every case without shear is now
  inside on post-peak.
* **Parts 3 and 4.** Response's two stage solves without shear were read and written
  (`docs/kernel.md`, "The stage solve without shear", with the table of what each moved).
  Neither is in use: each moves a Must view outside. The run of record is with r2c's own
  solve, so M's last stage (7.2 %) and tension's shape stand as they were.

What the reading explains, whether or not the solves are switched on: Response does not
balance a stage, it stops inside a tolerance. Under a stepped curvature the tolerance is
0.1 % of the loads and the last stages of M sit 0.005 mm/m from balance, which is the whole
of the 7.2 % next to a crack front. Under a stepped axial strain it is far wider and the
steps are half steps: that is the extra rising stage under tension.

## A2, parts 2 to 5 (2026-11-22)

Four kernel changes, each measured against the run before it on the 17 phase A cases
(`python tools/verify.py tests/oracle ...`, `python tools/targets.py OUT --counts`,
`python tools/changes.py BEFORE AFTER`; this machine, 17 cases at a time). The baseline was
run again on this machine first and gives the counts of the run of record of A2 part 1.

| Check | Baseline | Part 2, the node | Part 2, the layers | Part 3 |
|---|---:|---:|---:|---:|
| Peak | 17 of 17 | 17 | 17 | 17 |
| Rising branch | 16 of 17 | 17 | 17 | 17 |
| Shape | 15 of 17 | 15 | 15 | 15 |
| Views, Must (stress state, without shear) | 2 of 8 | 2 | 4 | 5 |
| Post-peak | 10 of 17 | 10 | 11 | 11 |
| Views, Should | 8 of 17 | 8 | 8 | 8 |
| Views, Could | 7 of 17 | 7 | 7 | 7 |

Parts 4 and 5 changed nothing in the kernel. The numbers of the last column are those of
`docs/verification-results.md`.

### A2, part 2: principal tensile stress at the crack front

*First, Response's cracking under compression in the node* (`docs/kernel.md`, "Cracking
under compression"; D14). Without shear nothing moves, as expected: there is no principal
tension across compression. With shear, 36 checks come inside and 3 go outside:

- the rising branch at M/V = 0.5 m, 6.1 to 2.7 % (the last rising-branch miss), and eleven
  views of that case at its fall of load and its peak;
- 14 views under N₀ then V at the peak and 10 under V alone at the fall of load at
  cracking, which now compare like states (principal tensile strain 90 to 0.4 %, crack
  widths 100 to 4 %);
- outside, all Should: shear on crack at M/V = 0.5 m at the peak (4.9 to 5.5 %), average
  angle under V alone at the last stage (3.7 to 5.1 %), transverse bond under N₀ then M + V
  at the last stage (2.6 to 22.5 %).

The stage that flipped in the trial of 2026-11-21 (V alone, stage 10) does not flip: with
the stage matching of D13 it is matched to r2c's stage after the fall, and its views come
inside.

*Then, how Response spaces its nodes* (`docs/kernel.md`, "Layers"). With Response's base
layers and splitting rule, r2c's nodes are Response's node for node at the stages looked at
(`python tools/nodes.py FIXTURE RECORD --feature peak`: M at the peak and at the end, −M at
the peak, N at the end; before, six of 65 nodes differed at M's peak, among them the four at
the crack front). Principal tensile stress, without shear:

| Case, stage | Before | After |
|---|---:|---:|
| M, peak | 18.2 % | 0.0 % |
| −M, peak | 23.9 % | 0.0 % |
| N, last stage | 10.0 % | 2.7 % |
| N + M, last stage | 6.7 % | 0.0 % |
| N₀ = +200 kN then M, last stage | 24.4 % | 1.1 % |
| **M, last stage** | **4.2 %** | **7.2 %** |
| N + M, cracking | 51.5 % | 51.5 % |

N and N₀ = +200 kN then M are now inside on every Must view. Two stages stay outside:

- *M at its last stage went outside* (4.2 to 7.2 %): the one Must check that was inside at
  a stage and is not now. r2c's nodes there are Response's, and its longitudinal strain
  differs from Response's by 0.005 mm/m over the whole depth (0.05 % of the strain at the
  top). Next to the crack front f1 rises by 1.4 MPa per millimetre, so that offset is
  0.135 MPa, 7 % of the chart. In Response's own strain state r2c's forces are Response's
  (N −0.01 kN, M +0.00 %: `python tools/diagnose.py states`). After the peak the axial
  force changes little with the axial strain: about 0.015 kN for 0.001 mm/m (estimated, from
  r2c's last stage solved again from the stages before it), so an unbalanced axial force of
  some 0.07 kN moves the strain that far. Response accepts a state without shear when the
  unbalanced force is under 0.1 % of the loads plus 1 N, here 0.3 kN [B `00425f10`, read in
  part 4]; r2c solves to 10⁻⁷ of the section's strength. So the offset is inside what
  Response's own solve leaves, and it is not a difference of rule. `docs/summary.md`, D29.
- *N + M at cracking* (51.5 %): not the nodes. Under N + M the tension zone at cracking is
  18 mm deep and below the bottom bars. r2c leaves the concrete tension there unreduced,
  as the thesis says it does where no bar crosses the crack [T 4-5, restriction 3]; in
  Response's chart the tension there is down at the floor after cracking, and in the binary
  the limit of a zone with no bar in it is zero [`00440400`]. Tried and not kept: with the
  binary's rule the stage comes to 0.3 % and nothing else changes sides (view Must would be
  6 of 8). The documents and the binary differ, so it is the owner's: D30.

With shear the layers put ten views of M/V = 0.5 m outside again (eight at its fall of
load, which the node had just brought inside, by one to five points) and one under V alone
(Should and Could), and bring inside five views of M/V = 2 m, two of V alone and V alone's
post-peak branch (8.4 to 3.7 %).

### A2, part 3: steel stress at a crack

The first approach brought both cases inside (`docs/kernel.md`, "Steel stress at a crack"):
N + M at the peak 100 to 0.0 % (the bottom bar at a crack: Response 46.1 MPa, r2c 0 before),
tension at the fall of load 78 to 0.0 % (Response 29.0 and 37.3 MPa on the two layers; r2c
0 and 210 before). The view also comes inside at five stages of four shear cases (M/V = 1 m
at the peak, N₀ then V at the peak, N + M + V at cracking, V alone at its fall and its peak)
and goes outside at one (M/V = 0.5 m at the fall of load, 0.0 to 5.6 %; Should). Tension is
now inside on every Must view.

### A2, part 4: tension, the order of cracking and the fall of load

Not resolved; one approach tried and dropped. Response's curve rises to 276.2 kN at a
strain of 0.0646 mm/m and falls to 235.8 at the next stage; r2c's rises to 274.5 at 0.0642
and has fallen to 239.1 at 0.0646. The measure reads Response's as "cracking, fall" and
r2c's as "fall, cracking".

- The kernel is not the difference: in Response's own state at 276.2 kN (the top of the
  section already cracked) r2c gives 276.19 kN.
- In r2c the states before the fall end at about 275.6 kN, at a strain of 0.06452 mm/m
  (`python tools/branch.py tests/oracle/newbeam-tension.r2x.txt --stage 11`): 0.2 % under
  Response's 276.2. At Response's control value, 0.06465, r2c has no state of equilibrium
  next to the last one: the least unbalanced moment is 0.055 kNm.
- *Tried:* Response's own tolerance for the solve without shear [B `00425f10`: the
  unbalanced force under 0.1 % of the sum of the loads plus 1 N, a tenth of that under
  axial strain control], which is 0.028 kNm here. The stage still falls; and the two last
  stages at a crack front swap sides (M 7.2 to 2.6 %, N₀ = +200 kN then M 1.1 to 5.0 %),
  which shows what those two are worth. Reverted.
- Response's solve goes on with the state it has after twenty iterations under axial
  strain control [B `00425f10`], which is how a stage can stand past r2c's limit point.
  That is the solver's behaviour, not a rule of the method, and is not cloned
  (`docs/acceptance.md`, Stance). No second approach with grounds was found. D31.

### A2, part 5: V alone, and M/V = 0.5 m (investigated; no kernel change)

*M/V = 0.5 m, the rising branch:* inside since part 2 (6.1 to 2.4 %), with the cracking
under compression in the node.

*V alone, the fall of load before the peak:* r2c has it since part 2. Response falls from
189.4 to 184.7 kN (4.7 kN), r2c from 189.5 to 185.4 (4.1 kN). The measure counts a fall when
the load is 2 % of Response's peak under the largest so far, 4.35 kN here: Response's is
2.2 %, r2c's 1.9 %, so r2c's is read as no fall. In Response's own states before and after
the fall r2c's shear is Response's (−0.00 %, `tools/diagnose.py states`), and its calculated
shear stress profile is as far from the state's as Response's own (0.7 %,
`tools/diagnose.py flow`). r2c's stage after the fall is its own: 185.42 kN at a shear
strain of 0.1170 mm/m against 184.69 at 0.116, with a profile error of 0.8 %, inside the
1 % at which a stage is accepted. Nothing was found to change within the bounds: every
check of that stage is inside target, and the 0.7 kN is under what the stage's own
convergence allows. D32.

## Phase A with the measures of A2 part 1 (2026-11-22)

r2c unchanged; three measures changed with the owner (log 2026-11-22-03): the views are
assessed in the tiers of `docs/acceptance.md` (D27), a shear case's shape leaves out its
ending (D25), and a stage is matched between the same features of the two curves (D13).
Measured: `python tools/targets.py VERIFY_OUT --counts`.

| Check | Inside |
|---|---:|
| Peak | 17 of 17 |
| Rising branch | 16 of 17 |
| Shape | 15 of 17 (M/V = 0.5 m and 2 m now inside) |
| Views, Must (stress state, without shear) | 2 of 8 |
| Post-peak | 10 of 17 |
| Views, Should | 8 of 17 |
| Views, Could | 7 of 17 |

The new stage matching re-matched eleven stages, ten of them on shear cases and mostly after
the peak, where nearest by load and control value had matched late stages to early ones (on
M/V = 0.5 m, Response's stage 55 to r2c's stage 1). Without shear only the no-load case's
first stage moved, and no check changed. With shear, M/V = 2 m's cracking views (Could) went
outside, as its last stages are now compared with r2c's last stages.

## Phase A baseline (run of 2026-11-22)

The 17 phase A cases, run after the parking of the other cases and the removal of what is
beyond the documented scope. **Nothing moved**: r2c's 17 records are byte for byte those of
a run made on the same machine before the removals (measured: `cmp` of the records of the
two runs; `python tools/changes.py` on the two reports no check that changed sides). So the
numbers are those of the sixth run of 2026-11-21 for these cases.

Cases inside target, check by check (measured: `python tools/targets.py VERIFY_OUT
--counts`; the limits are `docs/acceptance.md`'s):

| Check | Inside, of 17 | Outside |
|---|---:|---|
| Peak | 17 | none; largest +3.3 % (M/V = 2 m) and +2.6 % (N + M + V increasing) |
| Rising branch | 16 | M/V = 0.5 m (6.1 %) |
| Shape | 13 | M/V = 0.5 m and 2 m (how the response ends, and nothing else); V alone (Response has a fall of load before the peak, r2c none); tension (cracking and a fall of load at one step, read in the other order) |
| Post-peak | 10 | without shear: −M (20 %); with shear: constant V then M (5.9 %), M/V = 0.5, 1 and 2 m, V alone, constant N then V |
| Views | 1 | all but the Newbeam with N₀ = −2000 kN |

The shape check still counts how a shear response ends. Under the owner's reading D1a it
should not, and then M/V = 0.5 m and 2 m are inside on shape (their features up to the peak
are the same) and V alone and tension stay outside. The measure has not been changed: that
is a change to a measure, for the owner (`docs/summary.md`, D25).

**The views of the eight cases without shear** (the stress state under moment and axial
load, a Must of phase A). Outside, by view and the feature stage at which it is compared
(measured, from the run's results):

- Principal tensile stress in five cases (10 to 51 %): M and −M at the peak, constant
  tension then M and N alone at the last stage, N + M at cracking. One point at the crack
  front in most ("Principal tensile stress" below).
- Steel stress at a crack in two (N + M at the peak, 100 %; tension at the fall of load,
  78 %): finding H of `docs/status.md`, not investigated.
- At the last stage of −M: longitudinal strain, principal tensile strain and crack widths,
  5 to 6 %, where the post-peak branch is 20 % off.
- Diagonal crack spacing at cracking under tension (100 %), and longitudinal average bond
  under no load (100 %): one chart each, not investigated.

With shear, every view is outside in three to eight of the nine cases; most of it follows
from comparing unlike stages (D13).

## Against the acceptance targets (run of 2026-11-21)

`docs/acceptance.md` holds the owner's development targets since 2026-11-21: ±5 % on every
metric, the curve's shape the same, a floor at Response's printed precision, and the detail
views at the features of the curve, not only at the peak. The run of 2026-11-21 (on the
kernel of 2026-11-19, unchanged) is the first assessed against them. Every case is outside
on at least one check; the page shows which, one marker per check. Measured, from
`docs/verification-results.json`:

| Check | Cases outside | What it is, in short |
|---|---:|---|
| Peak | 0 of 25 | Largest +3.7 % (Newbeam M/V = 2 m) |
| Rising | 2 | M/V = 0.5 m (r2c drops back on the way up), US M/V = 1 ft |
| Post-peak | 6 | Cm4, Newbeam −M, M/V = 1 m and 2 m, M/V = 0.5 m, V alone: how and where the response ends |
| Shape | 8 | Four shear cases where Response ends with stages standing still at the peak load and r2c stops at it (Marshall, se100, Newbeam N₀ + M/V = 1 m, M/V = 2 m); M/V = 0.5 m and V alone end differently; US M/V = 1 ft has one fall of load fewer in r2c; tension (cracking and a fall of load at one step, read in a different order) |
| Views | 23 | See below. 25 before the Principal Tensile Stress line was drawn as Response draws it (second run of 2026-11-21): Marshall and the Newbeam with N₀ = −2000 kN, both without shear, are now inside on every check |

**The detail-view misses are not a matter of precision.** Every view comparison above 5 % was
checked against Response's printed precision (2026-11-21, on the views at the peak): none
lies within two units of the last printed digit, so the floor in acceptance.md changes none
of them. Do not look for a precision explanation.

**Principal tensile stress** missed at 58 of the stages compared, in 23 of the 25 cases, by
about 1.8 MPa: close to the cracking strength. The cause was looked for on 2026-11-21 and
is in "Principal tensile stress" below: Response lowers the cracking stress by the
compression across it, in its node routine. r2c now draws the line that way. It misses at 28
stages in 18 cases since (measured, second run of 2026-11-21), each explained there; no other
check changed sides.

**Where the views miss most** (measured, misses above 5 % over comparisons, by the feature of
Response's curve at which they are compared): at cracking 50 of 462, at a fall of load 33 of
126, at the peak 82 of 525, at the last stage 85 of 336 where the response ends falling and 29
of 126 where it ends standing still. The last stages are where the two responses differ most
(post-peak and shape above), so views there compare unlike states.

Views are matched by load and control value together since 2026-11-21 (owner's choice);
before, by control value alone. The numbers in the sections below that refer to views at the
peak are from the earlier matching.

## The scope cases: the baseline (fourth run of 2026-11-21)

53 cases were added on 2026-11-21 for increment S, one for each item of `docs/scope.md`
that no case had: 41 that reach a kernel path no earlier case reaches (group A) and 12 that
combine paths already reached (group B). The fourth run of 2026-11-21 is the baseline: all
85 cases on the kernel of the third run, before any change for the increment. Measured, from
that run with `tools/targets.py` (the checks and limits are the report's own):

- **The 32 earlier cases are unchanged**: no check changed sides against the third run
  (`tools/changes.py`); peak 0 outside, rising 2, shape 10, as before.
- **Of the 53 new cases, 17 are inside on peak, rising branch and shape** before anything
  is built: the two base curves (linear, elasto-plastic), the moment axis, the prestrain on
  bars, factors in the file with and without `--factors none`, the kg-cm file with shear,
  More Detail max and More Detail with shear, the negative elevations, constant tension
  with moment, a US file solved in SI, constant shear with moment, tension stiffening 2
  and 3, and the two shrinkage cases (r2c ignores the shrinkage; the peak hardly moves, the
  views are outside).
- **14 fail**: twelve softening models r2c refuses; the bar's thermal strain and the
  constant negative moment with shear both stop with "no equilibrium under the initial
  loads".
- **22 are outside on one of the three.** By what the difference looks like:
  - *r2c carries on past Response's failure* (a fall of load in r2c, then a higher peak, 12
    to 22 % above Response's, where Response's response ends falling): given crack
    spacings, the prestrain on stirrups, tension stiffening 1 and 6, softening 0 on the
    I-girder; the T-beam at M/V = 2 m (+8 %, Response's stages stand still). This is how a
    response ends (step 4 of the increment), unless a rule of the feature is behind it.
  - *The last stage only* (shape: Response ends falling or standing still, r2c ends at its
    peak or standing still; peak and rising branch inside): interlocking hoops, softening
    2, 10 and 13, the drape, the I-girder at M/V = 1 m, CSA factors with shear, no stirrups,
    the tension stiffening factor, tension stiffening 4. The known deviation of the shear
    cases (`docs/status.md`).
  - *The feature itself*: the segmental steel curve (−5.7 %; r2c ignores the curve);
    softening 6 and 7 (+5.6 % and +4.9 %, rising 5.3 %).
  - *The rising branch*: constant compression with shear alone (58 %), axial load with
    moment and shear together (8.7 %), the US file with shear (12.3 %, as the US case of the
    first set).

## The scope cases after step 3 (fifth run of 2026-11-21)

Step 3 of increment S built what the inventory listed as missing (`docs/kernel.md`:
"Compression softening", the segmental steel curve, shrinkage and thermal strain, the state
under the constant loads) and fixed two faults of r2c's own that the new cases showed (the
first step in shear strain under a constant axial load; strains and depths about a given
moment axis). Measured, fifth run of 2026-11-21, all 85 cases, with `tools/targets.py` and
`tools/changes.py` against the baseline:

- **No case fails or is refused.** The 14 that did in the baseline all run.
- **The 32 earlier cases: no check changed sides**, views included.
- **Of the 53 scope cases, 21 are inside on peak, rising branch and shape** (17 in the
  baseline): the segmental steel curve (−5.73 % to −0.00 %), the bar's thermal strain,
  compression with shear alone (rising 58 % to 4.7 %) and softening 1 came inside; the two
  shrinkage cases were inside on the three before and now have the feature in (thermal
  gradient: rising 1.30 % to 0.14 %).
- **32 are outside, every one of them on the shape, at the end of the response**; none is
  outside for its feature's rule. With the shape:
  - 11 also on the peak (+5 to +22 %): softening 0, 3, 4, 5, 6 and 8, given crack spacings,
    the prestrain on stirrups, tension stiffening 1 and 6, the T-beam. In each, r2c's curve
    lies on Response's up to where Response's response ends, and r2c carries on to a higher
    load; on the I-girder that is just after the web cracks.
  - 5 on the rising branch (5 to 16 %): softening 7, 9 and 12, the US file with shear, and
    axial load with moment and shear together (r2c stops short there: it steps in the axial
    strain, which turns back).
  - 16 on the shape alone: the last stage.

**The features' rules, apart from how the response ends.** r2c was put in Response's own
peak state of each feature case, with its history (`tools/diagnose.py states` on the
captures of every stage). Measured: moment within 0.4 % in every case; shear within 1 % for
softening 2, 6, 7, 9 to 15, tension stiffening 1, 2, 3, 4 and 6, the tension stiffening
factor, given crack spacings, the prestrain on stirrups, no stirrups, interlocking hoops,
the drape and the T-beam; within 3 % for softening 0, 1, 3, 5, whose peak in Response comes
at the web's cracking. So the 32 are a matter of where and how the response ends: step 4.

One view check went outside against the baseline, on a new case: Long. Average Bond at the
last stage of newbeam-ncomp-v (4.5 to 6.8 %). Its stages are different ones since the first
step was put right; the case came inside on the rising branch by the same change.

## How a response ends: Response's own stage control (sixth run of 2026-11-21)

Step 4 of increment S put Response's own load stage control in place of r2c's for every
case with shear (`docs/kernel.md`, "Load stages" and "Response's own load stage control"):
its control variable and steps, its closing in on an event, its passes on a stage and its
rule for keeping a stage that has not converged, what it does when a stage is refused, its
change of control variable and its end tests. Measured, sixth run of 2026-11-21, all 85
cases, against the fifth run (`tools/targets.py`, `tools/changes.py`, `tools/ends.py`):

| | Fifth run | Sixth run |
|---|---:|---:|
| Cases inside on peak, rising branch and shape | 43 of 85 | 51 of 85 |
| … of the 53 scope cases | 21 | 27 |
| Peak outside | 11 | 5 |
| Rising branch outside | 7 | 6 |
| Shape outside | 42 | 33 |
| Post-peak outside | 44 | 42 |
| Shear responses that end as Response's does (of 50) | 14 | 23 |

- **The 32 earlier cases: peak and rising branch as before** (none went outside). Two
  shape checks came inside (Marshall with shear; Newbeam with N₀ and M/V = 1 m: both now
  end standing still, as Response's). No post-peak or shape check went outside. View
  checks: 25 went outside and 55 came inside, on seven and eleven of the cases: the stages
  compared are other states now (r2c's stages sit at Response's control values, and the
  shear cases' last stages are different ones). Eleven of the 25 are at one stage of the
  shear-alone case, just past first cracking, where r2c's stage is on the other side of it.
- **dm-n1n** (option B, reported as the brief asks, not chased): the peak is +0.10 % (it
  was +3.2 %), the rising branch 0.08 %, the shape the same, post-peak 3.8 %: inside on all
  four. r2c no longer carries on past Response's peak there.
- **Peaks that came inside**: given crack spacings (+21.6 % to +0.04 %), the prestrain on
  stirrups (+21.8 % to +0.07 %), tension stiffening 1 and 6 (+18.2 % and +12.6 % to under
  3 %), softening 3 and 4 (+7 % and +6 % to about +1 %). In each r2c used to carry on past
  Response's failure; it now ends where Response does.
- **What Response's rules reproduce, stage for stage**: Newbeam at M/V = 1 m (the same
  curvatures to the peak, the change to shear strain control at the same stage, the plateau
  at 193 kN after it); shear alone, falling branch included (r2c's stages at shear strains
  of 4.34 and 4.44 mm/m carry 192.6 and 193.1 kN, Response's at 4.34 and 4.43 mm/m carry
  192.5 and 193.0); no stirrups (the stages to the peak: 120.4, 123.7, 125.2 kN against
  120.4, 123.6, 125.2; r2c then ends standing still at 126.8 kN where Response has a last
  stage at 74 % of its peak of 125.8).

**Still outside, and why** (known deviations, `docs/status.md`):

- *Five peaks*: softening 0 and 8 (+19.0 %), 5 (+10.1 %), 6 (+5.5 %) on the I-girder, and
  the T-beam at M/V = 2 m (+7.4 %). Response's response ends there while its load is still
  rising: just after the web cracks on the I-girder (its next stages do not converge, are
  kept because their load is under the peak, and the third has collapsed), with stages
  standing still on the T-beam. r2c's profile iteration converges at those states, and with
  Response's own rules a converged stage is accepted, so r2c goes on. In Response's own
  peak states r2c's forces agree (step 3).
- *Six rising branches*: softening 7, 9 and 11 on the I-girder (5 to 14 %), Newbeam at M/V =
  0.5 m (6.1 %, from 18.2 %), and the two US cases (13.1 % and 7.3 %: one fall of load
  fewer than Response's on the way up).
- *The shape alone, 22 shear cases*: the last stage. Response's ends falling in most of them (a
  collapsed last stage, kept because it had not converged and its load was under the peak);
  r2c's ends standing still, its step having died at the same plateau, or the other way
  round (Newbeam at M/V = 2 m). Which of the two happens turns on whether one stage's
  sixteen passes converge, in Response and in r2c alike; the rule is the same, the stage is
  not always.

Times: the 50 shear cases take a median of 66 s each (78 s in the fifth run), 126 s at most.

## Quick Define sections (third run of 2026-11-21)

Seven cases on three sections made with Response's Quick Define (the owner's test-set
decision, 2026-11-21): a T-beam, a circular column with hoops, an I-girder with 12 strands.
The target for this increment (the owner's brief): inside on peak, rising branch and shape;
views reported, not chased. Numbers are those of `docs/verification-results.md`.

| Case | Peak % | Rising % | Shape | Also outside |
|---|---:|---:|---|---|
| T-beam, M | −0.03 | 0.03 | same | views (7 %: crack spacing, tensile stress) |
| T-beam, −M | 0.00 | 0.92 | same | post-peak 20 %; views 8 % |
| Column, N | 0.00 | 0.00 | same | post-peak 161 %; views |
| Column, N₀ = −4000 kN, M | −0.02 | 0.02 | same | views (21 %: crack spacing) |
| Column, M/V = 1 m | −0.52 | 1.79 | different at the end | post-peak, views |
| I-girder, M | −0.03 | 0.18 | same | views (48 % at the last stage: steel stress at a crack) |
| I-girder, M/V = 2 m | −0.44 | 4.33 | different at the end | post-peak, views |

* **The five cases without shear were inside on peak, rising branch and shape before any
  kernel change** (the baseline run, kept outside the repository). The kernel changes of
  this increment do not touch them.
* **The two shear cases** were outside in the baseline: the I-girder found no stage after
  the first, the column's peak was 3.8 % low and its rising branch 5.1 % off. Three faults
  of r2c's own, none a missing rule of Response's (`docs/kernel.md`, "At a step in width"
  and "Hoops"): the shear strain profile could not jump at a flange; a web node on a flange
  junction took its stirrup ratio from the flange's width; a hoop's plastic strain was not
  kept in the hoop's own strain. Both are now inside on peak and rising branch.
* **Shape, both shear cases: Response's last stage is a collapsed one** (33 % of the peak
  on the column, 12 % on the I-girder) and r2c ends at its last stage near the peak. The
  rest of the shape is the same. Response ends this way in five of the twelve shear cases;
  r2c never finds such a state (`tools/ends.py`): its responses end where its iteration
  finds no state. This is Response's acceptance of a stage (option A3), out of scope for
  this increment; recorded as a known deviation in `docs/status.md`.
* **I-girder, M/V = 2 m, rising 4.3 %:** at a curvature of 0.39 to 0.47 rad/km Response's
  load falls from 1100 to 1083 kN·m and recovers; r2c's rises through. Before that, at
  V = 26 kN, Response has a fall of load (to 16 kN) that r2c does not: 1.7 % of the peak.
  Not investigated: inside target.
* **Column under axial load alone, after the peak:** Response's load falls from 16 191 to
  11 914 kN in one step and its concrete stress is no longer uniform over the depth (48 MPa
  near mid-depth, 7 MPa at both faces: a curved state with no moment). r2c stays on the
  uniform state and its load falls smoothly. Reported, not chased (post-peak).
* **T-beam under negative moment, after the peak:** as the Newbeam's (r2c takes one more
  stage before the bars rupture).
* **Views.** On the column the crack spacings differ at every stage: longitudinal 21 %
  (Response's is larger near the top and bottom faces, 490 against 387 mm), transverse 11 %
  and more away from mid-depth (1811 against 1139 mm at y = 215 mm; the same at mid-depth).
  The tables' rules for bars placed around a circle and for hoops have not been read from
  the binary. Crack widths and the diagonal spacing follow. On the T-beam and I-girder the
  crack spacing is 5 to 8 % off in places. With shear, views at the peak are 5 to 14 % off
  on the column and 5 to 12 % on the I-girder (transverse bond 97 %, r2c's numerical
  derivative), and the last stage is compared with whatever r2c stage is nearest to
  Response's collapsed one.
* **A circle is its polygon.** Quick Define writes the column's outline as 13 rows; r2c
  reads them straight and the peak under axial load agrees within 0.01 %. Curved outline
  segments were not needed and are not implemented.

## Principal tensile stress (2026-11-21)

The chart has two lines: f1, and the cracking stress it is held under. `tools/viewlines.py`
prints both programs' lines side by side.

**What the difference was** (measured on the fixtures, then read in the binary, routine
`0046a960`; the rule is in `docs/kernel.md`, "Cracking under compression"). Response's
cracking-stress line is the cracking stress times k = 1.05 − f2/f2max, between 0.05 and 1,
and 0.05 past the strain at peak stress: on the Newbeam at its peak moment the line is 5 %
of r2c's old one at the compression face. It is not only a drawn line: the same k scales the
cracking strain of the node and caps f1. Without shear that changes nothing, since there is
no principal tension where there is compression. With shear it does.

**What r2c does now.** It draws the line lowered and leaves its node alone. Measured
(`python tools/changes.py BEFORE AFTER` on the runs before and after): 30 of the 58 stages
come inside target, no check of any kind changes sides otherwise, and the control curves are
identical.

**Tried: the whole rule in the node** (cracking strain, f1 and the line). Measured on all 25
cases: the tensile stress stages outside fall to 27 and 16 other view checks come inside,
most on Liping LB1 at cracking and the US case at its peak; Marshall with shear ends
standing still as Response does (shape inside). But 15 checks that are inside go outside:
* 11 on the Newbeam under shear alone at stage 10 (the fall of load at cracking). r2c's load
  after the fall moves from 185.1 to 184.1 kN (Response 184.7), and the stage matched to
  Response's stage 10 flips from r2c's stage after the fall to its stage two before it
  (185.2 kN, uncracked), so every view there compares unlike states. The curves are within
  0.3 % either way.
* 4 by a point or two: shear stress on Marshall with shear at the last stage (3.9 to 6.0 %)
  and on the Newbeam with N₀ at the peak (3.9 to 5.4 %), shear on crack and transverse bond
  on shear alone at the peak (4.9 to 5.2 %, 4.2 to 5.4 %). On Marshall the difference is
  within a millimetre of the crack front, where the shear stress steps.
The increment's condition was that no check goes outside, so the node keeps its own cracking
and the rule is left as option F1 in `docs/status.md`. With the whole rule the peaks move by up
to 0.3 points, the US case by 2 (+0.9 to −1.1 %); all stay inside target.

**The 28 stages still outside**, by cause (measured, per stage, from the second run):
* *One point at the crack front* (10 stages; in the first 8 the only view outside at that
  stage): the peak
  of Marshall M (48 %), the Newbeam under M in its five variants (18 %) and −M (24 %), and
  the last stage of the Newbeam under N (10 %). f1 rises to the cracking stress and
  falls again within 2 mm of the crack front. Response has nodes every 0.34 mm there, r2c
  every 0.67 mm (Newbeam) or 1.1 mm (Marshall), so one of Response's points near the tip of
  that spike lies off r2c's line; both lines agree at the depths they share. Tried, not
  kept: layers down to h/1024 in place of h/512 bring six of these inside but leave Marshall
  at 8 % and put the Newbeam's last stage outside (4.2 to 5.8 %); the layering thresholds
  are r2c's own and Response's were not read. Option F2. The other 2: the last stages of Cm4 (35 %)
  and of the Newbeam with N and M (7 %).
* *The states compared differ* (16 stages; in the shear cases other views are outside at
  the same stage):
  the Newbeam with N and M at cracking, where Response's stage is just after cracking and
  the r2c stage nearest in load just before it (52 %); and the shear cases dm-n1n (last
  stage), Liping LB1 (3), M/V = 0.5 m (3), M/V = 2 m (2, at 5.7 %), M/V = 1 m (last stage),
  the US case (3), shear alone (2). These follow the differences in the curves and in where
  the response ends (status, A and B). Liping LB1 at cracking (9.7 %) is one the whole rule in the node brings inside (1.4 %).
* *f1 above Response's lowered cracking stress* (1 stage): M/V = 1 m at the peak, 7.6 % at
  three nodes near the crack front; 1.1 % with the whole rule in the node. Option F1.
* *The crack check after the steel has gone* (1 stage): the Newbeam with CSA factors at its
  last stage, 11 %. In the cracked zone Response's line is flat at 0.83 MPa and r2c's runs
  from 0.74 to 1.02. Goes with the steel stress at a crack in that case (status, option H);
  not investigated.

## Without shear

What this shows:

* Moment-curvature and axial responses agree to within 0.3 % at the peak and 0.5 % along the
  curve. In most cases the load stages are the same ones: same control values, loads within
  0.1 %.
* Stage counts differ where the two step through an event differently (two extra stages where
  the Newbeam's top fibre reaches its peak strain) and after the peak.
* Newbeam under axial compression alone: Response's own solution carries a small residual
  moment (about 2 kN·m) at its peak; r2c's does not, and its peak is 0.26 % lower.
* Newbeam in tension: Response stops when the section, bending under the unsymmetric steel,
  reaches zero strain at one face; r2c stops at the same place (no state exists there in
  either), two stages earlier.
* Cm4 (prestressed, ten steel layers, two concretes): stage for stage to the
  first strand rupture, peak within 0.04 %. Afterwards the sequence of ruptures is the same but the stages
  differ, and Response ran to its limit of 101 stages where r2c ends at 90.
* More Detail: same peak; 236 stages against 228 because the unrefined solves differ by two.

## With shear

What this shows:

* **Where shear governs and failure follows the first yielding of the stirrups** (Newbeam at
  M/V = 1 m, with and without axial load; Marshall; Liping LB1; se100): the peak is within
  about 1 %, the curve within 2 %, and up to the peak most
  stages coincide. For the Newbeam at
  M/V = 1 m, r2c's stresses at Response's own strain states agree within a few thousandths of
  a MPa at every node, up to the peak.
* **After the peak the two part company.** Response keeps taking small steps along a plateau
  (often its largest load is one of these, a fraction of a percent above the first), and its
  last one or two stages are states its own iteration did not converge on. r2c stops sooner.
  Stage counts and everything after the peak should not be compared.
* **Where the section can carry more after the stirrups first yield** (Newbeam at
  M/V = 2 m, at M/V = 0.5 m, and in US units at M/V = 1 ft), r2c stopped at the first plateau
  until 2026-11-19, 16 %, 7 % and 10 % below Response's peak. The cause was the stiffness in
  the shear flow calculation, not the profile iteration (as earlier versions of this file
  said). Two rules inferred from Response's output took two of the cases most of the way
  (session log 2026-11-19-03); reading Response's own rules from the binary did the rest
  (docs/kernel.md, session log 2026-11-19-04). All three now reach Response's peak:
  * *M/V = 0.5 m:* **0.5 % above** Response's peak (5.2 % below before). r2c follows the fall
    of load and the recovery (curve distance 3.4 % on moment-curvature, 1.3 % on the shear
    chart).
  * *US units, M/V = 1 ft:* **0.9 % above**. r2c steps over the lowest point of Response's
    fall of load (40.2; r2c's first stage after its first maximum is at 43.4), which is the
    13 % curve distance on the moment-curvature chart; on the shear chart it is 3 %.
    Response's peak here is on the recovery, after the fall: whether that is the result that
    matters is the owner's question (docs/acceptance.md, post-peak).
  * *M/V = 2 m:* r2c follows Response's curve to its end (curve distance 0.2 %; at
    Response's last curvature r2c carries 148.6 against 148.9) and then **carries on where
    Response ends**, to a largest load **3.7 % above** Response's. Response's last ten
    stages stand still at a curvature of 38.8 to 39.0 rad/km and its response ends there;
    why is not known (the stirrups are far from rupture at a crack, the top fibre is at 1.5
    times the strain at peak stress). r2c's stages beyond that point are closest iterates
    (profile error 1.8 to 2.7 %), not converged ones. This errs high, and is an
    end-of-response matter: an open question for the owner.
* **Newbeam at M/V = 1 m, a check on the same change.** With the new stiffness alone r2c
  found converged states (profile error about 1 %) far beyond Response's failure, up to
  22 % more load, reached by a rule of r2c's own that looked for a state beyond one it could
  not find. Response's last ten stages stand still at 193 and it then fails. The rule was
  removed and r2c ends as Response does (peak 0.15 % above). Whether the states beyond are
  real for the section is a structural question; r2c no longer reports them.
* **dm-n1n: r2c's peak is 3.2 % above Response's** (3.4 % before). The curves coincide up to
  Response's peak (curve distance 0.1 %). At the next step Response's shear strain jumps
  (0.89 to 1.19 mm/m, then 2.64) and its load falls; r2c carries on. In Response's own
  states r2c's calculated shear stress agrees as Response's own does, so this is not the
  stiffness. Not explained; errs high. What governs this section's failure is a structural
  question for the owner.
* **Liping LB1: 0.4 % below Response's peak** (1.8 % above before, with the stage found by
  the rule now removed). In Response's states r2c's calculated shear stress is 2 to 5 % off
  from stage 13 on, where Response's own lines agree within 1 %: a difference in the
  stiffness rules that this section shows and the Newbeam does not. Not investigated.
* Shear alone (Newbeam, V only): peak within 0.5 %; r2c ends shortly after the peak, Response
  carries on along a plateau 10 to 20 % lower.
* A shear solve took 1.5 to 4 minutes on one core (measured 2026-11-15); in the latest run
  (12 at a time on 32 cores) 25 to 109 s, against 56 to 126 s before the stiffness change
  (per-case times are in the generated results). Response's own solve of these cases takes a few seconds
  (estimated: no peak-only capture of a shear case was made), so r2c is roughly 10 to 50 times
  slower with shear. Most of r2c's time is spent at the end, on states it fails to find. An
  earlier version of this file compared r2c with "Response under Wine, 25 to 75 s"; those were
  r2x captures of every stage, nearly all of it chart reading, and the comparison was
  misleading.

## Detail views

At the peak (r2c's stage nearest Response's peak in control value). The 2026-11-15 version of
this section said the charts agree within a few percent of each chart's largest value apart
from the exceptions listed below. The generated results of 2026-11-17 show that this was
incomplete:

* **Long. Reinf Stress at Crack, Newbeam with CSA factors and Newbeam with N and M:** 100 %.
  At the CSA peak Response shows the bottom bar at 340 MPa at a crack (0.85 × 400 MPa); r2c
  shows 0 there. Inferred, not checked: r2c prints 0 for a bar it takes to have ruptured at a
  crack, so either its capacity at a crack is wrong here or its report of it is.
* **Principal Tensile Stress, Newbeam under axial compression alone:** 371 % (r2c's lines
  differed from Response's by up to 1.8 MPa where Response's largest value is 0.48 MPa). It was the
  cracking-stress line: 1.5 % at the peak since 2026-11-21 ("Principal tensile stress" above).
* **Shear cases that used to end before Response's peak** (M/V = 2 m, 0.5 m, US at 1 ft):
  they now reach it, but the views still show large differences (up to 80 % on some charts).
  For M/V = 2 m r2c's own peak is far beyond Response's last stage, so the stages compared
  are different states. The others have not been looked at beyond the generated numbers.

The sample-input cases, first compared view by view in the run of 2026-11-19, add these
(measured; none investigated):

* **Principal Tensile Stress, Marshall under axial compression alone:** 1900 % (Response's
  largest value 0.10 MPa, r2c's lines differed by up to 1.9 MPa). The same cause as the Newbeam
  under axial compression alone, above; no difference since 2026-11-21.
* **With shear, outside the exceptions known before:** se100, Longitudinal Concrete Stress 15 %
  and Average Angle 14 %; Liping LB1, Long. Reinf Stress at Crack 18 %; dm-n1n, Long. Reinf
  Stress at Crack 7 %; Marshall with shear, Shear Stress 8 % and Average Angle 6 %; transverse
  and shear strain 5 to 8 % on Liping LB1, se100 and Marshall. In these cases r2c's peak and
  Response's differ by 0.1 to 4.5 %, so the stages compared are not quite the same state;
  how much of this that accounts for is not known.

The exceptions known before:

* Principal Tensile Stress: Response draws the cracking-stress line reduced in the compression
  zone; r2c drew it unreduced (20 to 50 % of the chart's largest value there). Drawn as
  Response's since 2026-11-21; what is left is in "Principal tensile stress" above.
* Crack spacing and crack width charts for Cm4 and Liping LB1 (sections with many layers or
  ties): up to 44 % locally in spacing, 28 % in width; on Liping LB1 the diagonal spacing up to
  38 %. The Newbeam charts agree within 2 %; the Marshall charts within 2.5 % (the 2026-11-15
  version said 2 %).
* Transverse Average Bond: approximate in r2c (up to 36 %).
* Shear on Crack: r2c plots the magnitude; Response plots it signed.
* Node depths are not identical to Response's, so rows do not line up one for one; the number
  of rows often does.

Titles, axis labels, units, number formats and the line layout of every chart were checked
against Response's in SI, US and kg-cm units for the Newbeam (including Response's quirks:
"ms" for strains and "psi" on the steel stress at a crack in US units; g = 9.81 for concrete
stress and 9.8 otherwise in kg-cm units).

## Not compared

`docs/scope.md` is the inventory of what an r2x solve can take and whether a case has it.
Not compared after 2026-11-21: what r2x itself cannot solve (tension stiffening "None",
a shape without an outline, three load combinations on Newbeam) and what is out of scope
by design (hollow sections, long-term effects, strain discontinuity, the old text format).
A section with tendons added by hand was dropped from the test set by the owner
(2026-11-21: the I-girder covers strands, Cm4 covers prestress).

## Oracle captures

85 captures (25 of 2026-11-15 to 19, 7 of 2026-11-21 on the Quick Define sections, 53 of
2026-11-21 for increment S, whose inputs `tools/variants.py` derives from inputs already in
the set), each of every stage, made with `r2x` (worker, `--stage all`) from Response-2000
1.9.7 (r2k.exe SHA-256 bbf4bc59…4e74) under Wine 9.0. The fixtures in tests/oracle are those
records cut down to the control charts and the feature stages with tools/trim.py; nothing in
them is edited. Response's sample inputs are not in this repository. The archive of full captures
was rebuilt with `tools/capture.py` on 2026-11-19 and every capture matched its fixture.

## Step A-4 (2026-11-24): the flat peak

The run of record (`docs/verification-results.md`) is that of step A-3 check for check
(measured, `python tools/changes.py`: 0 in, 0 out on the 37 cases). One rule of the
stage control changed, when its base step grows (`docs/kernel.md`), and by itself it
moves no stage.

What the figures of the shear cases mean was measured in this step, and it bears on how
to read them. Of the view checks outside target on the shear cases, set and parked, 89 %
are inside when r2c is put into Response's own state at the stage (`python
tools/sources.py`): they measure the state the two programs reached, not a rule of r2c.
The states differ because the two make different tries where a stage does not settle
(`docs/status.md`, "Named limitation"; `python tools/rtrace.py`, `python tools/tries.py`),
and on a flat peak Response's own state is one of several it could have kept: with a
tension stiffening factor of 0.5 it solves one target three times and gets loads
0.14 % apart, the peak being the middle one. A view check at such a stage compares two
such samples.


## Step A-5 (2026-11-24): settings of the section, units and material factors

The run of record (`docs/verification-results.md`) is on 52 cases: the 37 of step A-4,
the I-girder with softening Vecchio-Collins 1992-A (D67) and 14 on Newbeam whose variable
is a setting of the section, the units, the material factors or More Detail. On the 38
that were in the set before the 14 joined, no check changed side against the "before" run
of the step (measured, `python tools/changes.py`). The tables are in `docs/summary.md`;
what they mean:

- **Units change nothing but the numbers read and printed.** Under M the US and kg-cm
  cases agree with Response to the same digits as the SI case does (peak 0.00 %), and
  Response's own US and kg-cm captures are its SI capture after conversion (`python
  tools/unitcheck.py`). A miss on a case in other units is therefore a miss of the
  section and load, not of the units. The two US-units cases with shear show it: their
  load is M/V = 1 ft, under the depth, with two falls of load before a flat peak, and
  Response's own SI capture at M/V = 0.3048 m differs from r2c in its own states by the
  same amounts as the US capture does.
- **More Detail** adds stages and changes none: 228, 327 and 130 stages, every check
  inside as on the plain cases. The case with shear is the first on Newbeam that Response
  does not repeat to the last digit (four captures; `python tools/repeat.py`).
- **The material factors** needed one rule (the crack check's two capacity moments without
  the concrete's factor, `docs/kernel.md`). It showed only after the peak, in the limit
  line of the Principal Tensile Stress chart: 11.3 to 0.0 %.
- **The figures of the shear cases are still read with the slopes rule off.** r2c's
  stiffness in the shear flow calculation is not the program's where the concrete softens
  (`docs/kernel.md`, "The slopes of the compressive stress"; measured with `python
  tools/flowset.py`: 309 stages of 2,007 more than a point off, 80 with the rule). On the
  set that is behind the view misses at the peak of the I-girder with softening, 10 of
  the 17 on M/V = 0.5 m, two on "M constant, then M + V", and the rising branch of the
  two US-units cases. With the rule on 45 checks come inside and 5 go outside on the 52;
  it is off because one of the five is a Must (`docs/summary.md`, D69).
- **The view misses of the new shear cases are mostly the state reached.** Of 44 view
  checks outside on the CSA shear case and the two US-units cases, 39 are inside with r2c
  in Response's own state at the stage (`python tools/sources.py`), 21 of them on a flat
  part of the curve. That is the named limitation of step A-4 again
  (`docs/status.md`).
