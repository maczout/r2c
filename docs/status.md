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
- Tools: `compare.py` (any two records), `verify.py` (r2c on a set of oracle records),
  `report.py` (verification results from a verify run), `dashboard.py` (the same results as
  one HTML page of pictures, for the owner's review), `trim.py` (record to fixture),
  `diagnose.py` (r2c at Response's strain states, along its control values, its calculated
  shear stress in Response's states, and its own stages with their profile error),
  `decompile.py` (a routine of r2k.exe from a Ghidra project kept outside the repository),
  `capture.py` (rebuild the oracle archive with r2x), `check.py` (checks before pushing).
- 25 oracle fixtures in `tests/oracle`; pytest tests (fast set; `-m slow` for five shear cases;
  `R2C_RESPONSE_DIR` for Response's sample inputs).
- Docs: `kernel.md` (each rule and its source), `verification.md` (what the results mean),
  `verification-results.md` (generated), `acceptance.md` (the owner's tolerances; template).

## 2. Against Response-2000 1.9.7

The numbers are in `docs/verification-results.md` and what they mean is in
`docs/verification.md`. In short, for all 25 cases (run of 2026-11-19, third of that day):

| Group | Cases | Result |
|---|---|---|
| No shear | 15 | Peak within 0.3 %, curve within 0.5 % (unchanged) |
| Shear, failure at first stirrup yield | 5 | Peak within 1 % (Liping LB1 −0.4 %, was +1.8 %) |
| Shear alone (Newbeam, V only) | 1 | Peak 0.5 % low; r2c ends soon after the peak |
| Shear, section carries more after first stirrup yield | 3 | All reach Response's peak. M/V = 0.5 m: +0.5 % (was −5.2 %). US, M/V = 1 ft: +0.9 %. M/V = 2 m: on Response's curve to its end, then carries on where Response ends, +3.7 % |
| Shear: dm-n1n | 1 | r2c's peak 3.2 % **above** Response's; not explained |

No acceptance tolerances are set, so none of this is assessed. The owner's ruling for the
2026-11-19 step (not a tolerance): the three cases of the fourth row at 7 to 16 % below
Response's peak were outside acceptance. They are no longer below it; M/V = 2 m is now
3.7 % above, for a different reason (below).

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

## 4. Not done

- Quick Define variants (T, I, circular sections, added tendons): in the agreed test set, not
  captured or compared. Cm4 is the only prestressed and only non-rectangular section tested.
  Circular sections are untested, and curved outline segments are read as straight.
- Not compared: More Detail with shear, CSA factors with shear, US or kg-cm input files,
  stirrup patterns other than those in the samples, segmental steel curves, concrete models
  other than the defaults and those in the samples.
- Out of scope by design: hollow sections, long-term effects, strain discontinuity, the old text
  input format.
- `tools/capture.py` has rebuilt the oracle archive against Response (2026-11-19): all 25
  captures match their fixtures. r2x's clipboard helper can fail transiently (once in 25
  captures); a rerun of that case on its own then matched.

## 5. Decisions that are the owner's

1. **Tolerances (structural).** `docs/acceptance.md` holds the stance (owner, 2026-11-17:
   agreement within tolerance, not mathematical equivalence) and the template; the values are
   not set. Until they are, nothing is assessed.
2. **What matters (structural)**: which results, post-peak, which sections and loadings first,
   errs high vs low. Listed in `docs/acceptance.md`. Where it is silent, the developer decides
   and records the decision in the session log (owner, 2026-11-17).
3. **Reverse engineering.** The original brief allowed it "to answer questions but not as the
   primary development approach". The 2026-11-15 build used many rules read from the binary
   (each marked in `docs/kernel.md`). CLAUDE.md now ranks it below acceptance and the thesis,
   as the means of finding out why r2c misses acceptance (the developer's wording, 2026-11-17,
   for the owner to confirm).
4. **Dependencies.** numpy only. Compiling the node routine (option D4) would add one.

## 6. Options for next steps

Grouped, not ranked. Sizes are rough.

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

**C. Finish the agreed test set.** Capture and compare the Quick Define T, I and circular
sections and added tendons; implement curved outline segments (needed for circles).

**D. Performance** (software).
- D1. The failing tail: shorter since 2026-11-19 (section 3), not measured in detail.
- D2. Warm-start the transverse equilibrium solve from the previous evaluation.
- D3. Analytic tangents in place of finite differences.
- D4. Compile the node routine (numba or a small C extension). Adds a dependency.
- D5. Measure Response's solve time properly: peak-only r2x captures of the shear cases.

**E. Housekeeping.**
- E3. Compare the untested combinations in section 4.
- E5. `tools/capture.py` could retry a case once when r2x fails, since the one failure seen was
  transient. Not done: one failure is not yet a pattern.

**F. Detail views.** Reduced cracking-stress line in the compression zone; crack spacing on
multi-layer sections; signed shear on crack; transverse bond. Display-level, except that the
first may hint at a reduced cracking strength under biaxial compression that r2c does not
apply. No effect seen in the cases compared.

**H. Steel stress at a crack, found 2026-11-17.** At the Newbeam's peak with CSA factors
Response shows the bottom bar at 340 MPa at a crack and r2c shows 0; the Newbeam with N and M
differs the same way. Not investigated (see `docs/verification.md`, Detail views). Display or
kernel: unknown. The peak loads in these cases agree.

**I. Detail views of the sample-input cases, found 2026-11-19.** Not investigated. Marshall
under axial compression alone: Principal Tensile Stress 1900 % (Response's largest value
0.10 MPa), like the Newbeam's 371 %. With shear: se100 Longitudinal Concrete Stress 15 % and
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
`tests/reference/newbeam`.

**Routines in r2k.exe 1.9.7 already located** (addresses as the decompiler shows them).
Internal units in the binary: Pa and m; fc′ stored negative. `tools/decompile.py` shows any
of them (Ghidra 12, headless; the project with r2k.exe analysed is kept outside the
repository).

| Address | What |
|---|---|
| `004ad9c0`, `004ac960` | concrete stress, tangent |
| `004ac190`, `004af050`, `004aefa0` | concrete set-up, ε0, ft |
| `0046aaa0`, `0046a960` | MCFT node; crack strain |
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
