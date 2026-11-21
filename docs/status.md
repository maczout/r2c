# r2c: where it stands

The present state of r2c and the options for what comes next. History is in `docs/log/` and
in git. First written at the end of the 2026-11-15 build; kept in the repository since
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
  driver, shear by the longitudinal stiffness method with Response's own stiffness rules,
  stepping in curvature and then in the shear strain.
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
  (how each shear response ends in r2c and in Response), `scope.py` (which fixture has which
  input feature), `variants.py` (inputs derived from present ones by stated text edits),
  `probe.py` (what Response does with an input, through r2x), `check.py` (checks before
  pushing).
- 32 oracle fixtures in `tests/oracle`, each with the detail views of the feature stages of
  Response's curve (cracking, falls of load, peak, last stage); pytest tests (fast set;
  `-m slow` for seven shear cases; `R2C_RESPONSE_DIR` for Response's sample inputs,
  `R2C_DEFINE_DIR` for the Quick Define inputs, which are r2x's:
  `tests/reference/define`).
- Docs: `kernel.md` (each rule and its source), `verification.md` (what the results mean),
  `verification-results.md` (generated), `acceptance.md` (the owner's development targets),
  `scope.md` (every input an r2x solve can take, and r2c's status on each; the checklist for
  "scope complete"), `scope-probes.md` (generated: what Response does with each).

## 2. Against Response-2000 1.9.7

The numbers are in `docs/verification-results.md`, what they mean in `docs/verification.md`
("Against the acceptance targets"), and the pictures on the results page. Since 2026-11-21
each case is assessed against the owner's development targets in `docs/acceptance.md`: ±5 %
on every metric, the curve's shape the same, views at the features of the curve.

Third run of 2026-11-21, 32 cases (the 25, and 7 on Quick Define sections: T-beam, circular
column with hoops, I-girder with strands), cases outside by check: peak 0 of 32, rising 2,
post-peak 10, shape 10, views 30. On the 25, no check changed sides against the second run
(peak 0 of 25, rising 2, post-peak 6, shape 8, views 23). The seven new cases are all inside
on peak and rising branch; the five without shear are inside on shape too
(`docs/verification.md`, "Quick Define sections").

**Known deviation, shear cases (the last stage).** Response's response to moment and shear
often ends on a collapsed stage, at 4 to 66 % of the peak load (5 of the 12 shear cases:
both new ones, the column at M/V = 1 m and the I-girder at M/V = 2 m, and dm-n1n and the
Newbeam at M/V = 0.5 m and 1 m). r2c never finds such a state (`tools/ends.py`) and ends at
its last stage near the peak, so the shape check reads "ends falling" against "ends
standing still" on the two new cases; the rest of their shape is the same. This is
Response's acceptance of a stage (option A3).

Marshall and the Newbeam with N₀ = −2000 kN, both without shear, are inside on
every check. Principal tensile stress is outside at 28 stages in 18 cases (58 in 23
before); in seven cases without shear it is the only view outside, by one point at the
crack front (option F2).

**Known deviation, shear cases (cracking under compression).** Response lowers the cracking
strain and the principal tension of a node by the compression across it; r2c draws the
lowered line and does not apply it in its node (`docs/kernel.md`, "Cracking under
compression"; option F1).

Stance (owner, 2026-11-21): r2c clones Response's behaviour; where they differ, Response is
right, and no structural assessment of results is given. Once a case is inside target,
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

**Where the response ends is r2c's own guess, and now decides two results.**
- *M/V = 2 m:* Response's stages stand still at a curvature of 39 rad/km and its response
  ends; r2c goes on to 67 rad/km on closest iterates (profile error 1.8 to 2.7 %), 3.7 %
  more load.
- *M/V = 1 m:* with the new stiffness r2c found converged states up to 22 % beyond
  Response's failure, through its own rule of searching beyond a state it could not find.
  That rule is removed and r2c ends where Response does. Whether those states are real for
  the section is a structural question.
Response's own acceptance of a stage and its step control are in `00418af0` and `00424c60`,
read in passing and not taken over.

**dm-n1n.** The curves coincide to Response's peak. At the next step Response's shear strain
jumps and its load falls; r2c carries on to 3.2 % more. r2c's calculated shear stress in
Response's states agrees as Response's does, so it is not the stiffness.

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

Shear cases in the third run of 2026-11-19 (Response's stiffness rules; no search beyond a
state not found): 25 to 109 s, 12 at a time on 32 cores, against 56 to 126 s in the second
run (8 at a time). The breakdown below has not been measured again; the failing tail it
describes is shorter now, by how much was not measured.

Where the shear time goes (measured 2026-11-15): about 90 % after the last stage found,
retrying smaller steps and looking beyond a target, each attempt running to its iteration
limit (the same failure as stopping short); on the stages found, about 50 force evaluations
per stage at about 7 ms each, 80 % of it the transverse equilibrium solve, which starts from
scratch each time; and numpy call overhead on arrays of about 100 nodes.

## 4. Scope: what is not done

`docs/scope.md` is the inventory (2026-11-21): every input an r2x solve can take that
reaches the analysis, each with one status, measured with r2x's worker where it was not
known. Against it, the scope is **not complete**. What is left (increment S, the owner's
brief of 2026-11-21):

- **Missing** (r2x solves it, r2c refuses or ignores it): eleven named compression softening
  models and number 4; a segmental curve for reinforcing steel (read and ignored); draped
  tendons (ignored); shrinkage and thermal strains of the concrete (ignored).
- **Not compared** (implemented, no oracle case): the rest of the concrete model options
  (base curves 0 and 3, softening 0, 2, 6, 7, 10, 13 under shear, tension stiffening 1 to 4
  and 6, the tension stiffening factor); input files in US and kg-cm units; given crack
  spacings and moment axis; no stirrups with shear; interlocking hoops; prestrains on
  stirrups and bars; thermal strain of bars; factors in the file; a T-beam with shear; CSA
  factors and More Detail with shear; More Detail max; five load combinations.
- 53 new cases cover these: 41 that reach a kernel path no present case reaches (group A),
  12 that combine paths already reached (group B). `tools/scope_cases.py --list` names them.
- **Not solvable with r2x** (measured; nothing to compare with): curved outline rows in an
  input file (Response's reader rejects them; a circle is saved as 13 straight rows, so
  option C4 falls away); a shape without an outline; tension stiffening "None" (Response
  asks a question r2x does not answer) and 5; `units="roman"`; three load combinations on
  Newbeam. What r2c should do with each is proposed in `docs/scope.md` for the owner.
- **Out of scope by design** (owner): hollow sections, long-term effects, strain
  discontinuity, the old text input format.
- A section with tendons added by hand: dropped from the test set (owner, 2026-11-21).
- `tools/capture.py` has rebuilt the oracle archive against Response (2026-11-19): all 25
  captures match their fixtures. The seven of 2026-11-21 were captured once, with `--add`.
  r2x's clipboard helper can fail transiently (once in 25 captures); a rerun of that case
  on its own then matched.

**Where increment S stands** (2026-11-21): step 1, the inventory, is done. Next is step 2:
the 53 cases' fixtures and the baseline run on all cases before any kernel change; then
step 3 (build what is missing), step 4 (how a response ends: A3, G, C2).

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

Grouped, not ranked. Sizes are rough. Since 2026-11-21 the targets decide what is work: a
check outside target is work, a gap inside target is not. Options that waited on the owner's
word because they reach past Response's peak (A3, G) or into the detail views (F, H, I) no
longer do: post-peak and every view are in the targets, and where r2c and Response differ,
Response is right (owner, 2026-11-21). Reading, for the owner to confirm: that this puts A3
and G in scope for development sessions.

**A. Shear: where the response ends, and how a stage is accepted.** The stiffness is done
(section 2). What is left decides M/V = 2 m (+3.7 %) and bears on dm-n1n (B).
- A3. Read Response's acceptance of a stage and its step control (`00418af0`, `00424c60`,
  `00420f20`, `004276a0`; `0041e840` for the profile update) and take them over in place of
  r2c's own iteration, closest-iterate rule and change to shear strain control. Read in
  passing 2026-11-19: up to 16 passes a stage, converged under 1 %, a stage refused above
  3 % after 16 passes under a condition not yet understood. This overlaps option G.
  **Needs the owner's word**: G was out of scope for the 2026-11-19 step.
- A4. The differences left in Response's states (after a fall of load; Liping LB1 from
  stage 13): `tools/diagnose.py flow --profile` shows where over the depth.

**B. dm-n1n** (errs high, +3.2 %). Not the stiffness (section 2). Next: Response's stage
acceptance (A3), then a structural read of what governs that section's failure.

**C. The Quick Define sections: done for peak, rising branch and shape** (2026-11-21), but
for the last stage of the two shear cases (A3). Left on these sections, all in the views or
after the peak (`docs/verification.md`, "Quick Define sections"):
- C1. Crack spacing tables on the circular column: longitudinal 21 % and transverse 11 % or
  more off at every stage; crack widths and diagonal spacing follow. The rules for bars
  around a circle and for hoops are in the binary's tables (`004fec60`, `004ff1a0`,
  `004bc470` and what calls them) and have not been read.
- C2. The column under axial load alone after its peak: Response leaves the uniform state
  (a curved state with no moment, the load falling by a quarter in one step); r2c stays on
  it.
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
- F1. **Cracking under compression in the node** (kernel). Response's rule
  (`docs/kernel.md`) also lowers the cracking strain and caps f1; r2c does not apply that.
  Tried 2026-11-21 (three lines in `node.evaluate`): against the present state 18 more
  checks come inside (17 views, among them tensile stress on Liping LB1 at cracking and
  M/V = 1 m at the peak; and the shape of Marshall with shear) and 15 go outside, 11 of them
  because one stage of the shear-alone case is matched to a different r2c stage, 4 by a
  point or two (`docs/verification.md`, "Principal tensile stress"). Peaks stay inside
  target. **Needs the owner's word**: it is Response's behaviour, and it puts checks outside
  that are inside (see the open question in the log of 2026-11-21-02).
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

**G. End-of-response rules.** r2c's rules after a shear failure and after rupture are its own
guesses. Depends on what acceptance says about post-peak.

## 7. Reference for a working session

**The oracle.** Clone `maczout/r2x` (branch `park`), unpack Response-2000 1.9.7 (r2k.exe
SHA-256 `bbf4bc59…4e74`). One capture:

    python -m r2x.worker INPUT OUT --stage all --response-dir RESPONSE_FOLDER [options]

Negative option values need the `=` form (`--initial=-2000,0,0`). An all-stage capture takes
25 to 75 s; captures run one at a time in the default Wine prefix. `tools/capture.py` does
this for every fixture. The Newbeam input (`input.r2t`) is in r2x's
`tests/reference/newbeam`; the Quick Define inputs are r2x's
`tests/reference/define/quick-{tbeam,column,ibeam-strands}/hand.r2t`, captured under the
names tbeam.r2t, column.r2t and igirder.r2t (r2x records the input's name). Verify with both
folders: `--inputs RESPONSE_FOLDER R2X/tests/reference`.

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
| `00418af0`, `00424c60`, `00420f20` | load stage control, profile iteration, profile error: read in passing |
| `00417290` | a secant stiffness of the section ("error in moment calculation"); not the shear driver it was taken for |
