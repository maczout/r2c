# r2c against Response-2000

r2c 0.1.0 compared with Response-2000 1.9.7, run through r2x 0.5.0 (the oracle). No pass or fail
is decided here: the differences are listed for an engineer to judge.

How to read the table. "Peak" is the largest load on the bottom control chart (kN·m, kN, or the
units named). "Curve" is how far Response's rising branch lies from r2c's curve, as a
percentage: the largest distance of its points from r2c's polyline, with load scaled by
Response's peak and the control value by its largest value on that branch. Stages are counted
over the whole response, Response's first. Time is r2c's, two cases at once on two cores;
Response under Wine took 25 to 75 s per case.

Reproduce with `python tools/verify.py tests/oracle --inputs RESPONSE_FOLDER` (the fixtures in
tests/oracle hold the control charts and the peak stage of each capture) or compare any two
records with `python tools/compare.py REF SUBJECT --views`.

## Without shear

| Input | Loads N,M,V (initial; increment) | Stages | Chart | Peak, Response | Peak, r2c | Diff % | Curve % | Time s |
|---|---|---|---|---:|---:|---:|---:|---:|
| File > New | 0,0,0; 0,1,0 | 60 / 62 | moment_phi | 336.8 | 336.8 | -0.00 | 0.01 | 3 |
| Newbeam | 0,0,0; 0,1,0 | 60 / 62 | moment_phi | 336.8 | 336.8 | -0.00 | 0.01 | 3 |
| Newbeam | 0,0,0; 0,-1,0 | 60 / 61 | moment_phi | -92.1 | -92.1 | -0.01 | 0.01 | 3 |
| Newbeam CSA | 0,0,0; 0,1,0 | 57 / 57 | moment_phi | 250.2 | 250.2 | +0.00 | 0.02 | 3 |
| Newbeam us | 0,0,0; 0,0.74,0 | 60 / 62 | moment_phi | 248.4 | 248.4 | +0.00 | 0.01 | 2 |
| Newbeam kgcm | 0,0,0; 0,0.1,0 | 60 / 62 | moment_phi | 34.4 | 34.4 | +0.00 | 0.01 | 3 |
| Newbeam MD×2 | 0,0,0; 0,1,0 | 228 / 236 | moment_phi | 336.8 | 336.8 | -0.00 | 0.02 | 11 |
| Newbeam | -2000,0,0; 0,1,0 | 46 / 46 | moment_phi | 477.1 | 477.1 | -0.00 | 0.01 | 2 |
| Newbeam | 0,0,0; -10,1,0 | 33 / 30 | moment_phi | 337.5 | 337.7 | +0.06 | 0.45 | 1 |
| Newbeam | 0,0,0; -1,0,0 | 35 / 36 | axial_ex | -5385.3 | -5371.5 | -0.26 | 0.27 | 1 |
| Newbeam | 0,0,0; 1,0,0 | 31 / 29 | axial_ex | 353.0 | 352.2 | -0.22 | 0.48 | 2 |
| Newbeam | 0,0,0; 0,0,0 | 2 / 2 | moment_phi | -0.0 | -0.0 | +0.00 | – | 0 |
| Marshall.rsp | 0,0,0; 0,1,0 | 59 / 59 | moment_phi | 839.7 | 839.7 | +0.00 | 0.02 | 2 |
| Marshall.rsp | 0,0,0; -1,0,0 | 38 / 38 | axial_ex | -10512.1 | -10512.1 | +0.00 | 0.00 | 0 |
| Cm4.rsp | 0,0,0; 0,-1100,0 | 101 / 90 | moment_phi | -2131.6 | -2130.7 | -0.04 | 0.43 | 21 |

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
* Cm4 (prestressed, ten steel layers, two concretes): stage for stage to the first strand
  rupture, peak within 0.04 %. Afterwards the sequence of ruptures is the same but the stages
  differ, and Response ran to its limit of 101 stages where r2c ends at 90.
* More Detail: same peak; 236 stages against 228 because the unrefined solves differ by two.

## With shear

| Input | Loads N,M,V (initial; increment) | Stages | Chart | Peak, Response | Peak, r2c | Diff % | Curve % | Time s |
|---|---|---|---|---:|---:|---:|---:|---:|
| Newbeam | 0,0,0; 0,1,1 | 43 / 34 | moment_phi | 201.5 | 202.1 | +0.27 | 0.22 | 125 |
| Newbeam | -500,0,0; 0,1,1 | 45 / 33 | moment_phi | 253.5 | 253.1 | -0.16 | 0.28 | 128 |
| Newbeam | 0,0,0; 0,0,1 | 52 / 22 | shear_ex | 217.7 | 216.6 | -0.50 | 3.30 | 165 |
| Newbeam | 0,0,0; 0,0.5,1 | 56 / 28 | moment_phi | 128.5 | 119.7 | -6.87 | 7.42 | 98 |
| Newbeam | 0,0,0; 0,2,1 | 88 / 30 | moment_phi | 297.7 | 249.7 | -16.11 | 88.13 | 95 |
| Newbeam us | 0,0,0; 0,1,1 | 57 / 19 | moment_phi | 57.9 | 52.2 | -9.80 | 73.08 | 89 |
| Marshall.rsp | 0,0,0; 0,-1,1 | 40 / 28 | moment_phi | -476.5 | -475.9 | -0.13 | 0.58 | 154 |
| Liping LB1.rsp | -804,0,0; 0,0.7,1 | 36 / 35 | moment_phi | 246.5 | 248.7 | +0.91 | 1.40 | 248 |
| se100am69.rsp | 0,0,0; 0,1.3,1 | 36 / 29 | moment_phi | 685.3 | 692.5 | +1.05 | 1.87 | 135 |
| dm-n1n.rsp | 0,0,0; 0,1.5,1 | 30 / 26 | moment_phi | 555.4 | 580.5 | +4.53 | 0.62 | 180 |

What this shows:

* **Where shear governs and failure follows the first yielding of the stirrups** (Newbeam at
  M/V = 1 m, with and without axial load; Marshall; Liping LB1; se100): the peak is within
  about 1 %, the curve within 2 %, and up to the peak most stages coincide. For the Newbeam at
  M/V = 1 m, r2c's stresses at Response's own strain states agree within a few thousandths of
  a MPa at every node, up to the peak.
* **After the peak the two part company.** Response keeps taking small steps along a plateau
  (often its largest load is one of these, a fraction of a percent above the first), and its
  last one or two stages are states its own iteration did not converge on. r2c stops sooner.
  Stage counts and everything after the peak should not be compared.
* **Where the section can carry more after the stirrups first yield, r2c stops short** (Newbeam
  at M/V = 2 m, at M/V = 0.5 m, and in US units at M/V = 1 ft). Response redistributes: the
  stirrups unload, the shear strain profile changes shape and the load climbs on, to the
  flexural capacity at M/V = 2 m. r2c's shear profile iteration does not converge on those
  states and it ends the response at the first plateau: **16 %, 7 % and 10 % below Response's
  peak** in these three cases. This is the main shortfall. It errs low, but it is not a
  property to lean on.
* **dm-n1n: r2c's peak is 4.5 % above Response's.** The curves coincide up to Response's peak
  (curve distance 0.6 %); there Response's load starts to fall and r2c's keeps rising for
  three more stages. Not explained. This one errs high.
* Shear alone (Newbeam, V only): peak within 0.5 %; r2c ends shortly after the peak, Response
  carries on along a plateau 10 to 20 % lower.
* A shear solve takes 1.5 to 4 minutes, two to four times Response under Wine. Most of it is
  spent at the end, on states it fails to find.

## Detail views

At the peak (r2c's stage nearest Response's peak in control value) the charts agree within a
few percent of each chart's largest value, with these exceptions:

* Principal Tensile Stress: Response draws the cracking-stress line reduced in the compression
  zone; r2c draws it unreduced (20 to 50 % of the chart's largest value there). The stress line
  itself agrees.
* Crack spacing and crack width charts for Cm4 and Liping LB1 (sections with many layers or
  ties): up to 44 % locally in spacing, 28 % in width. The Newbeam and Marshall charts agree
  within 2 %.
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
is edited. Response's sample inputs are not in this repository.
