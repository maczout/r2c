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
  table of the summary), `check.py` (checks before pushing). `decompile.py` also lists
  a routine's instructions (`a:ADDRESS`).
- 85 oracle fixtures, each with the detail views of the feature stages of Response's curve
  (cracking, falls of load, peak, last stage). **The phase A set, 17 of them, is in
  `tests/oracle`**: Newbeam with only its loads varied (listed in `docs/summary.md`). **The
  other 68 are parked in `tests/oracle/parked`** until phase B (owner, 2026-11-22: D16,
  D19): kept, and not run by default. The folder is the set: verify, capture, retrim and
  scope read one folder and not the folders under it, so `tests/oracle` gives phase A and
  `tests/oracle/parked` the parked set, on request.
- pytest: by default the reader and material rules, and the eight phase A cases without
  shear; `-m "slow and not parked"` the nine with shear; `-m parked` the parked cases
  (`R2C_RESPONSE_DIR` for Response's sample inputs, `R2C_DEFINE_DIR` for the Quick Define
  inputs, which are r2x's `tests/reference/define`, `R2C_SCOPE_DIR` for the inputs of the
  scope cases). Five parked fixtures need a removed feature and have no test.
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

**The phase A baseline** (run of 2026-11-22, the 17 cases, after the parking and the
removals; measured, `python tools/targets.py VERIFY_OUT --counts`). Cases inside target:
peak 17 of 17, rising branch 16, shape 13, post-peak 10, views 1. r2c's 17 records are byte
for byte those of a run made before the removals on the same machine, so nothing moved.
What is outside, and the views of the cases without shear, are in `docs/verification.md`,
"Phase A baseline". The generated results now hold these 17 cases only.

Outside on a Must (D1, D2), on the phase A set:

- Rising branch: M/V = 0.5 m (6.1 %; known deviation 2 below).
- Shape: V alone (Response has a fall of load before the peak, r2c none) and tension
  (cracking and a fall of load at one step, read in a different order). A shear case's
  ending is no longer counted (D25).
- Views of the stress state without shear (the tiers of D27): 6 of the 8 cases are
  outside; principal tensile stress in five, steel stress at a crack in two, −M's strains by
  a point.

**What follows describes all 85 cases as they stood in the sixth run of 2026-11-21**, the
last that ran the parked cases. Peak and rising branch of the 17 have not moved since.

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

**Known deviation, shear cases (cracking under compression).** Response lowers the cracking
strain and the principal tension of a node by the compression across it; r2c draws the
lowered line and does not apply it in its node (`docs/kernel.md`, "Cracking under
compression"; option F1).

Stance (owner, 2026-11-21 and 2026-11-22): r2c reproduces Response's behaviour as
documented; where they differ, documented Response is right, undocumented behaviour of the
binary is not cloned, and no structural assessment of results is given. Once a case is inside target,
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
- **Kept, waiting for the owner**: the softening models the manual names without a rule in
  the documents (D21); the default softening of Response 1.9.7, later than the manual (D22);
  several sections in one file and the horizontal tie, read as the nearest documented thing
  (D23).
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

**Where a next session picks up**: A2 parts 2 to 5 in `docs/summary.md` (D26), within the
bounds in `docs/acceptance.md` (D28). Part 1, the measures, is done (D13, D25, D27; log
2026-11-22-03). Next: refuse what D23 names, then the views without shear (options F1, F2
and H below), then the two shape misses and the rising branch at M/V = 0.5 m.

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
   primary development approach". CLAUDE.md ranks it below acceptance and the thesis, as the
   means of finding out why r2c misses acceptance (the developer's wording, 2026-11-17, for
   the owner to confirm).
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
  (`004276a0`) and its relaxation factor were not read; r2c's own solve converges at some
  states where Response's does not (known deviations 1 and 3).
- A4. The differences left in Response's states (after a fall of load; Liping LB1 from
  stage 13): `tools/diagnose.py flow --profile` shows where over the depth.

**B. dm-n1n.** Inside on peak, rising branch, shape and post-peak since step 4 (section 2).
A structural read of what governs that section's failure is still open.

**C. The Quick Define sections: done for peak, rising branch and shape** (2026-11-21), but
for the last stage of the two shear cases (A3). Left on these sections, all in the views or
after the peak (`docs/verification.md`, "Quick Define sections"):
- C1. Crack spacing tables on the circular column: longitudinal 21 % and transverse 11 % or
  more off at every stage; crack widths and diagonal spacing follow. The rules for bars
  around a circle and for hoops are in the binary's tables (`004fec60`, `004ff1a0`,
  `004bc470` and what calls them) and have not been read.
- C2. The column under axial load alone after its peak: Response leaves the uniform state
  (a curved state with no moment, the load falling by a quarter in one step); r2c stays on
  it. Looked at in step 4 and not resolved (section 2, known deviation).
- C3. The I-girder with shear: a fall of load at V = 26 kN and another at a curvature of
  0.39 rad/km in Response, neither in r2c (1.7 % and 4.3 % of the peak; inside target).
- C4. Curved outline segments: fall away. An input file cannot carry one (measured
  2026-11-21, `docs/scope.md` section 1.4).
- C5. Views at a step in width: Response's charts have a point on each side of the step;
  r2c's have the upper layer's only.

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
as Response draws it since 2026-11-21. Left: crack spacing on multi-layer sections; signed
shear on crack; transverse bond; and
- F1. **Cracking under compression in the node** (kernel; the owner's word is given, D14:
  yes, after the stage matching is fixed, D13). Response's rule
  (`docs/kernel.md`) also lowers the cracking strain and caps f1; r2c does not apply that.
  Tried 2026-11-21 (three lines in `node.evaluate`): against the present state 18 more
  checks come inside (17 views, among them tensile stress on Liping LB1 at cracking and
  M/V = 1 m at the peak; and the shape of Marshall with shear) and 15 go outside, 11 of them
  because one stage of the shear-alone case is matched to a different r2c stage, 4 by a
  point or two (`docs/verification.md`, "Principal tensile stress"). Peaks stay inside
  target.
- F2. **Node spacing at the crack front** (kernel, layering). Response has nodes every
  0.34 mm at the crack front, r2c every 0.67 to 1.1 mm; one point of Response's f1 there
  lies off r2c's line (10 stages; the only view outside in seven cases). Layers down to
  h/1024 were tried: six stages come inside, one goes outside, Marshall stays at 8 %.
  Response's own layering rule has not been read; that is the next step.

**H. Steel stress at a crack, found 2026-11-17.** At the Newbeam's peak with CSA factors
Response shows the bottom bar at 340 MPa at a crack and r2c shows 0; the Newbeam with N and M
differs the same way. Not investigated (see `docs/verification.md`, Detail views). Display or
kernel: unknown. The peak loads in these cases agree.

**I. Detail views of the sample-input cases, found 2026-11-19.** Not investigated, except
Principal Tensile Stress under axial compression alone (Marshall 1900 %, Newbeam 371 %):
that was the cracking-stress line, gone since 2026-11-21. With shear: se100 Longitudinal Concrete Stress 15 % and
Average Angle 14 %, Liping LB1 Long. Reinf Stress at Crack 18 %, Marshall Shear Stress 8 %,
strains 5 to 8 %. Part may come from comparing at slightly different states (peaks differ by
0.1 to 4.5 %). Details in `docs/verification.md`. Whether they matter depends on what
acceptance says about detail views **(structural)**.

**G. End-of-response rules.** With shear: Response's own since 2026-11-21 (A3). Without
shear: r2c's own, which come to the same as Response's tests on the cases compared
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
| `004a7b60` | a second node routine that calls the crack strain; not read |
| `00569f58` | flag for the lowering by compression; set in `004992b0`, `004b2580` |
| `004aea40`, `004ae630` | steel stress, tangent |
| `004ab4e0` | derived steel properties (rupture strain, tendon yield) |
| `004ae520`, `004ac830` | steel capacity at a crack, concentrated strain |
| `004bc470`, `004bd930` | steel ratio for strain concentration: layers, table for stirrups |
| `004a79d0`, `004a80e0`, `004a8b20` | stirrups, transverse resultant, εy solve |
| `004a9d90` | section forces and layering |
| `00441d80`, `00440400` | flexural crack check |
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
| `00424c60`, `004276a0`, `00425f10` | the single-state solve; the global solve with shear (not read); the stage solve without shear (read in part) |
| `0040e9f0` | set-up of another analysis class that steps in the shear strain from the start (taken to be the one for shear alone) |
| `004ac190`, `004ab4e0`, `004fbf70` | concrete set-up (Kf, n), derived steel properties (segmental curve), the steel ratio η of the Hsu models |
| `004f96e0`, `00448d90` | the reader of shape.dat and the outline dialog's width field: the only users of UP and DOWN |
| `00417290` | a secant stiffness of the section ("error in moment calculation"); not the shear driver it was taken for |
