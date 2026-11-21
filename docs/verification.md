# r2c against Response-2000

r2c 0.1.0 compared with Response-2000 1.9.7, run through r2x 0.5.0 (the oracle).

**What this file is.** An interpretation of r2c's results against Response-2000, written by
hand. The numbers are not here: they are in `docs/verification-results.md`, generated from a
run of `tools/verify.py` and headed by the commit, machine and date of that run. Unmarked
numbers below are those of that run; numbers marked "2026-11-15 run" are from the earlier
comparison.

The generated results cover all 25 cases, the 7 on Response's sample inputs (Marshall, Cm4,
Liping LB1, se100, dm-n1n) included (run of 2026-11-21; the kernel is that of the third run of
2026-11-19, after the shear flow stiffness was changed to Response's rules). The 15 cases without shear are unchanged from the first
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
| Views | 25 | See below |

**The detail-view misses are not a matter of precision.** Every view comparison above 5 % was
checked against Response's printed precision (2026-11-21, on the views at the peak): none
lies within two units of the last printed digit, so the floor in acceptance.md changes none
of them. Do not look for a precision explanation.

**Principal tensile stress** misses at 58 of the stages compared, in 23 of the 25 cases, by
about 1.8 MPa: close to the cracking strength. Inferred: one systematic difference, most
likely the cracking-stress line that Response reduces in the compression zone and r2c does
not (status, option F). It alone puts most cases outside on views.

**Where the views miss most** (measured, misses above 5 % over comparisons, by the feature of
Response's curve at which they are compared): at cracking 50 of 462, at a fall of load 33 of
126, at the peak 82 of 525, at the last stage 85 of 336 where the response ends falling and 29
of 126 where it ends standing still. The last stages are where the two responses differ most
(post-peak and shape above), so views there compare unlike states.

Views are matched by load and control value together since 2026-11-21 (owner's choice);
before, by control value alone. The numbers in the sections below that refer to views at the
peak are from the earlier matching.

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
  differ from Response's by up to 1.8 MPa where Response's largest value is 0.48 MPa). Probably the same
  cracking-stress line as below, scaled by a small chart; not checked.
* **Shear cases that used to end before Response's peak** (M/V = 2 m, 0.5 m, US at 1 ft):
  they now reach it, but the views still show large differences (up to 80 % on some charts).
  For M/V = 2 m r2c's own peak is far beyond Response's last stage, so the stages compared
  are different states. The others have not been looked at beyond the generated numbers.

The sample-input cases, first compared view by view in the run of 2026-11-19, add these
(measured; none investigated):

* **Principal Tensile Stress, Marshall under axial compression alone:** 1900 % (Response's
  largest value 0.10 MPa, r2c's lines differ by up to 1.9 MPa). Same pattern as the Newbeam
  under axial compression alone, above.
* **With shear, outside the exceptions known before:** se100, Longitudinal Concrete Stress 15 %
  and Average Angle 14 %; Liping LB1, Long. Reinf Stress at Crack 18 %; dm-n1n, Long. Reinf
  Stress at Crack 7 %; Marshall with shear, Shear Stress 8 % and Average Angle 6 %; transverse
  and shear strain 5 to 8 % on Liping LB1, se100 and Marshall. In these cases r2c's peak and
  Response's differ by 0.1 to 4.5 %, so the stages compared are not quite the same state;
  how much of this that accounts for is not known.

The exceptions known before:

* Principal Tensile Stress: Response draws the cracking-stress line reduced in the compression
  zone; r2c draws it unreduced (20 to 50 % of the chart's largest value there). The stress line
  itself agrees.
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

* Sections from Quick Define other than the Newbeam's rectangle: T, I and circular sections,
  and added tendons. These were in the plan and were not run. The only non-rectangular and the
  only prestressed section compared is Cm4. Circular sections in particular are untested, and
  curved outline segments are read as straight.
* `--more-detail` with shear, CSA factors with shear, US or kg-cm input files (as opposed to
  results in those units), stirrup patterns other than those in the samples (hoops, T-headed
  bars, interlocking), segmental steel curves, concrete models other than the defaults and
  those in the samples.
* Anything out of scope: hollow sections, long-term effects, strain discontinuity.

## Oracle captures

25 captures, each of every stage, made with `r2x` (worker, `--stage all`) from Response-2000
1.9.7 (r2k.exe SHA-256 bbf4bc59…4e74) under Wine 9.0. The fixtures in tests/oracle are those
records cut down to the control charts and the peak stage with tools/trim.py; nothing in them
is edited. Response's sample inputs are not in this repository. The archive of full captures
was rebuilt with `tools/capture.py` on 2026-11-19 and every capture matched its fixture.
