# r2c against Response-2000

r2c 0.1.0 compared with Response-2000 1.9.7, run through r2x 0.5.0 (the oracle).

**What this file is.** An interpretation of r2c's results against Response-2000, written by
hand. The numbers are not here: they are in `docs/verification-results.md`, generated from a
run of `tools/verify.py` and headed by the commit, machine and date of that run. Unmarked
numbers below are those of that run; numbers marked "2026-11-15 run" are from the earlier
comparison.

The generated results cover all 25 cases, the 7 on Response's sample inputs (Marshall, Cm4,
Liping LB1, se100, dm-n1n) included (run of 2026-11-19). For those 7 the stage counts, peaks
and curve distances on the control charts are the same as in the 2026-11-15 comparison, to the
figure shown; their detail views had not been compared case by case before (see Detail views).
Whether a difference is acceptable is decided against `docs/acceptance.md`, not here.

Reproduce with `python tools/verify.py tests/oracle --inputs RESPONSE_FOLDER --out OUT`, then
`python tools/report.py OUT`; compare any two records with
`python tools/compare.py REF SUBJECT --views`.

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
  until 2026-11-19, 16 %, 7 % and 10 % below Response's peak. The cause was not the profile
  iteration, as earlier versions of this file said. Two things were found (docs/kernel.md,
  session log 2026-11-19-02):
  * *M/V = 2 m.* The bottom bars yield and the load climbs on to the flexural capacity. In
    Response's own states r2c's forces agreed within 0.2 %, but its calculated shear stress
    profile was 25 to 50 % off, because it gave a bar on its yield plateau no stiffness.
    With the stiffness Response's profiles imply, r2c follows Response's control values
    within 0.5 % to stage 56 of 88 and its peak is **1.8 % below** Response's. It still ends
    there: from stage 57 its calculated profile is 13 to 35 % off in Response's states, for
    a reason not found.
  * *US units, M/V = 1 ft.* Response's stages step in the shear strain once shear governs;
    its load falls 23 % (52.2 to 40.2), the curvature turns back through zero, and the load
    recovers to a peak above the first. Stepping in the shear strain, r2c follows that path
    (falls to 39.5, recovers) and its peak is **0.75 % above** Response's. Response's peak
    here is on the recovery, after the fall: whether that is the result that matters is the
    owner's question (docs/acceptance.md, post-peak).
  * *M/V = 0.5 m.* Response's load reaches 125.9, falls to 110.3 and recovers to its peak of
    128.5. r2c now reaches 121.9 (**5.2 % below** the peak; 6.9 % before) and loses the path
    at a shear strain of about 3.7 mm/m, where its calculated profile is 7 to 27 % off in
    Response's states (the same unexplained difference as at M/V = 2 m). Still short.
* **dm-n1n: r2c's peak is 3.4 % above Response's** (4.5 % before the closest-iterate limit
  was tightened). The curves coincide up to Response's peak (curve distance 0.6 %). At the
  next step Response's shear strain jumps (0.89 to 1.19 mm/m, then 2.64) and its load falls;
  at nearly the same curvature r2c finds a converged state with less shear strain (0.92 mm/m)
  and 1.2 % more load than Response's peak, and its last stage, 3.4 % above, is a closest
  iterate with a profile error of 2.7 %. Two states at one curvature, or a rule r2c lacks:
  not known. This one errs high. What governs this section's failure is a structural
  question for the owner.
* **Liping LB1 moved: 1.8 % above Response's peak** (0.9 % before). After the change to
  shear strain control r2c finds one more stage, higher than Response's plateau. Not
  investigated.
* Shear alone (Newbeam, V only): peak within 0.5 %; r2c ends shortly after the peak, Response
  carries on along a plateau 10 to 20 % lower.
* A shear solve takes 1.5 to 4 minutes (measured 2026-11-15; per-case times of the latest run
  are in the generated results). Response's own solve of these cases takes a few seconds
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
* **Shear cases where r2c ends before Response's peak** (M/V = 2 m, 0.5 m): the views compare
  r2c's last stage with Response's peak, which are different states. Not meaningful until
  r2c reaches that peak. The US case at M/V = 1 ft now reaches it; its views have not been
  looked at beyond the generated numbers.

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
