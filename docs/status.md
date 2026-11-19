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
  driver, shear by the longitudinal stiffness method.
- Tools: `compare.py` (any two records), `verify.py` (r2c on a set of oracle records),
  `report.py` (verification results from a verify run), `dashboard.py` (the same results as
  one HTML page of pictures, for the owner's review), `trim.py` (record to fixture),
  `diagnose.py` (r2c at Response's strain states, and along its control values),
  `capture.py` (rebuild the oracle archive with r2x), `check.py` (checks before pushing).
- 25 oracle fixtures in `tests/oracle`; pytest tests (fast set; `-m slow` for two shear cases;
  `R2C_RESPONSE_DIR` for Response's sample inputs).
- Docs: `kernel.md` (each rule and its source), `verification.md` (what the results mean),
  `verification-results.md` (generated), `acceptance.md` (the owner's tolerances; template).

## 2. Against Response-2000 1.9.7

The numbers are in `docs/verification-results.md` and what they mean is in
`docs/verification.md`. In short, for all 25 cases (run of 2026-11-19; the same as the 2026-11-15 comparison):

| Group | Cases | Result |
|---|---|---|
| No shear | 15 | Peak within 0.3 %, curve within 0.5 % |
| Shear, failure at first stirrup yield | 5 | Peak within about 1 % |
| Shear alone (Newbeam, V only) | 1 | Peak 0.5 % low; r2c ends soon after the peak |
| Shear, section carries more after first stirrup yield (Newbeam M/V = 2 m, 0.5 m, 1 ft US) | 3 | r2c stops at the first plateau: 16 %, 7 %, 10 % low |
| Shear: dm-n1n | 1 | r2c's peak 4.5 % **above** Response's; not explained |

The generated results (run of 2026-11-19) cover all 25 cases, the 7 on Response's sample
inputs included. The control-chart numbers of all 25 are the same as in the 2026-11-15
comparison. The detail views of the 7 sample cases, compared for the first time, show
differences not listed before (finding I in section 6).

### The two shear problems

**Stopping short (M/V = 2 m and similar).** In Response, after the stirrups first yield
mid-depth, the next stage has the stirrups unloaded elastically (plastic strain kept depth by
depth), the shear strain profile changes shape, and the load climbs on toward the flexural
capacity. r2c keeps that plastic strain, and when started from the state just before the dip it
reproduces Response's later stages closely (V within 0.2 % at five stages past the dip). What
fails is the profile iteration in between: with fixed damping it either diverges or settles on
a different state. The kernel can represent these states; the iteration cannot reach them
reliably.

**dm-n1n.** The curves coincide up to Response's peak. There Response's load starts to fall
while r2c's keeps rising for three more stages. Not investigated beyond that.

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

**A. Shear profile iteration (accuracy and speed together)**, the main shortfall.
- A1. Read how Response iterates: the shear distribution routine (`0041e840`) and the driver
  (`00417290`) were never read. Likely the quickest route to matching. Within CLAUDE.md's
  hierarchy if acceptance is not reached otherwise.
- A2. Develop r2c's own: adaptive damping, an accelerated fixed-point method, or solving for
  the profile and the strain state together. No guarantee of landing on Response's states.
- The test either way: the three stopping-short cases should continue; the five well-matched
  shear cases must not move. `tools/diagnose.py controls` separates the iteration from the
  stepping.

**B. dm-n1n** (errs high). `tools/diagnose.py states` on an all-stage capture past Response's
peak shows which quantity departs. Needs a structural read of what governs that section's
failure.

**C. Finish the agreed test set.** Capture and compare the Quick Define T, I and circular
sections and added tendons; implement curved outline segments (needed for circles).

**D. Performance** (software).
- D1. Remove the failing tail: follows from A; or cap it harder as a stopgap.
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
Internal units in the binary: Pa and m; fc′ stored negative.

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
| `0041e840`, `00417290` | shear distribution, driver: **not read** |
