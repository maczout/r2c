# r2c against Response-2000

r2c 0.1.0 compared with Response-2000 1.9.7, run through r2x 0.5.0 (the oracle).

**What this file is.** An interpretation of r2c's results against Response-2000, written by
hand. The numbers are not here: they are in `docs/verification-results.md`, generated from a
run of `tools/verify.py` and headed by the commit, machine and date of that run. Unmarked
numbers below are those of that run; numbers marked "2026-11-15 run" are from the earlier
comparison.

The generated results cover all 32 cases: the 25 of the first test set, the 7 on Response's
sample inputs (Marshall, Cm4, Liping LB1, se100, dm-n1n) included, and since the third run
of 2026-11-21 the 7 on Quick Define sections (T-beam, circular column, I-girder with
strands; see "Quick Define sections" below). For the first 25 the kernel is that of the
third run of 2026-11-19, after the shear flow stiffness was changed to Response's rules: no
check of theirs changed sides in the third run of 2026-11-21 (`tools/changes.py`). The 15 cases without shear are unchanged from the first
run; the detail views of the 7 sample cases were first compared case by case on that day
(see Detail views).
Whether a difference is acceptable is decided against `docs/acceptance.md`, not here.

Reproduce with `python tools/verify.py tests/oracle --inputs RESPONSE_FOLDER --out OUT`, then
`python tools/report.py OUT`; compare any two records with
`python tools/compare.py REF SUBJECT --views`.

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

* A section with tendons added to it by hand (dropped from the test set by the owner,
  2026-11-21: the I-girder covers strands, Cm4 covers prestress). A T-beam with shear.
  Curved outline segments (a width of UP or DOWN): not implemented, and no input has one.
* `--more-detail` with shear, CSA factors with shear, US or kg-cm input files (as opposed to
  results in those units), stirrup patterns other than those compared (single leg, open,
  closed, hoop: T-headed bars and interlocking hoops are not), segmental steel curves, concrete models other than the defaults and
  those in the samples.
* Anything out of scope: hollow sections, long-term effects, strain discontinuity.

## Oracle captures

32 captures (25 of 2026-11-15 to 19, 7 of 2026-11-21 on the Quick Define sections), each of every stage, made with `r2x` (worker, `--stage all`) from Response-2000
1.9.7 (r2k.exe SHA-256 bbf4bc59…4e74) under Wine 9.0. The fixtures in tests/oracle are those
records cut down to the control charts and the peak stage with tools/trim.py; nothing in them
is edited. Response's sample inputs are not in this repository. The archive of full captures
was rebuilt with `tools/capture.py` on 2026-11-19 and every capture matched its fixture.
