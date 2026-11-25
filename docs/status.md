# r2c: where it stands

For the developer: what exists now and how to work on it. The owner reads
`docs/summary.md`. This page describes the present; what happened is in `docs/log/` and git.

## What exists

- **`r2c solve`** (`src/r2c/cli.py`): r2x's options, exit statuses and record format
  (r2x-raw 1, all views). Not there: `--report`, `define`, `setup`; `health` prints a
  version line. An input with tension stiffening turned off is refused, as r2x fails on it. Parity with
  r2x is complete except accepted refusals: `docs/parity.md`.
- **The kernel** (`src/r2c`, numpy only): the MCFT node with the crack check, Response's
  layering, the solves without shear, shear by the longitudinal stiffness method with
  Response's stiffness rules and its load stage control. Each rule and its source:
  `docs/kernel.md`. Switches for rules that are written and off are listed there.
- **The development set**: 164 fixtures in `tests/oracle`, each a capture cut to the stages
  the measure compares: 55 on Newbeam under varied loads, materials, settings and units, the
  T-beam, the column and the I-girder; 52 wider cases since increment 2
  (`tools/scope_cases.py`, group W: Response's sample files under other loads; concrete and
  steel strengths, shapes, reinforcement and loads on the four sections); and 57 since
  increment 4 (group X), of the kinds the held-out scorer reports outside target
  (`tools/heldout.py score --kinds`), 53 of them without shear. All are chosen to be like
  the held-out set and never the same. 30 more in `tests/oracle/parked`, not run by
  default. Results: `docs/verification-results.md` (generated). Regression limits: the
  first 54 cases' in `tests/test_oracle.py`, the others' generated into
  `tests/oracle/limits.json` (`python tools/limits.py VERIFY_OUT --write`).
- **The held-out set**: `heldout/` (the frozen manifest and the totals), built and scored by
  `tools/heldout.py`. See "The held-out rule" in `CLAUDE.md` before touching anything.
- **Known deviations**: `docs/deviations.md`.

## Next

1. **Priority 1 without shear** is the threshold still to be met (99 %). What is outside
   on the development set (`python tools/priority.py docs/verification-results.json`): the
   circular column (the override) and the prestressed I-girder under axial tension and
   moment, where Response's tries run out at the strands' rupture and r2c goes on. What
   brought cases inside in increment 4 was found by adding cases of new kinds and reading
   the first view that differed: do more of that (prestressed sections under axial load,
   sections with tapers, several transverse types, wide bar spacings, light steel).
   `python tools/margins.py` lists the cases nearest the target; `python tools/stagesat.py`
   the cases whose stages are not at Response's control values.
2. **Turn on `Flexure.crush_by_share`** (`docs/kernel.md`, "Closing in on first
   cracking"; `--set`-style: set the class attribute, run `python tools/verify.py`, then
   `python tools/stagesat.py`): the binary's share for closing in on the extreme fibre's
   peak strain. Measured with it on: first 60 stages at Response's control values on 96 of
   104 cases without shear, against 41. Written after the held-out score of increment 4
   and left off for that reason alone.
3. **Run the cases without shear on Response's own stage control.** Response has one
   stage control for both (`docs/kernel.md`, "Response's own load stage control"); r2c
   uses it with shear and keeps an earlier stepping of its own without
   (`Flexure.advance`, `Flexure.run`). What is left to differ without shear is what that
   control does and r2c's stepping does not: after a try that fails the multiplier is
   halved and, under 0.2, the control variable changes (the end on Newbeam with very light
   steel: Response's last steps are 0.787, 0.394 rad/km and then a step in the centroid's
   strain; the prestressed I-girder under axial tension, where its steps halve to the
   strands' rupture and the response ends); a stage is put in at 0.8 of the gap where the
   cracks close and at 0.2 where something starts (the I-girder under moment); how often
   it closes in on the extreme fibre's peak strain. Tried once, after the held-out score
   and not kept: `Shear(analysis).run()` on Newbeam with 500 mm² of bottom steel under
   moment runs, and ends as Response does (its last curvatures 88.11, 89.83, 90.68 rad/km
   against Response's 88.24, 90.62), but with the base steps of a case with shear, so its
   first stages are not Response's. The job is the base step and the first step of a case
   without shear on that control [B `00419250`, `0041a870`], then `python
   tools/stagesat.py` on every case without shear. Nine development cases around endings
   at rupture were added for it.
4. **Priority 2 with shear** (the shear-related views at the peak) is the lowest total.
   `python tools/sources.py` splits the misses: about four in five are the state the two
   programs reach on a stage that does not settle, one in five are rules. Of the rules:
   the stirrups' stress at a crack at nodes that have only just cracked (the transverse
   strain there differs by millionths and the crack width with it); the Transverse Bond
   chart at the stirrups' top end (a half layer whose top node has next to no shear strain
   keeps its bond in Response at Newbeam M/V = 0.5 m and loses it at mid-depth under a
   thermal gradient: the rule that tells the two apart was not found).
5. **Stages that do not settle, with shear.** Up to the first difference r2c makes
   Response's tries one for one; after it the paths part. The new case of increment 4
   (Newbeam with closed stirrups under axial compression and shear alone): both programs
   hover at the web-cracking load for ten passes and then drop to a cracked profile,
   Response at its eleventh pass and r2c at its fifteenth; Response's solve then breaks
   down and its response ends on a collapsed state. The owner has been asked whether such
   a case is the override's kind.
6. **Long shear responses are slow** (the column under 3000 kN at M/V = 2 m takes about
   seven minutes).
7. **Not yet checked on parity:** the two programs run end to end on the same input.
8. **Newbeam under an axial tension of 300 kN** has no state under its initial load in
   r2c ("no equilibrium under the initial loads"). Seen in passing; what Response does
   was not looked at.

## How to run things

FOLDERS below is every folder inputs are found in: Response's own, r2x's `tests/reference`,
and the two folders of derived inputs in the development archive (`scope-inputs`,
`define-inputs`). The machine's actual paths are not recorded in the repository.

- Tests: `pytest` (fast; the cases without shear), `pytest -m "slow and not parked"` (with
  shear), `pytest -m parked`. Inputs come from `R2C_RESPONSE_DIR`, `R2C_DEFINE_DIR`,
  `R2C_SCOPE_DIR`; cases whose input is missing are skipped.
- Which development cases are outside a priority, and on what: `python tools/priority.py
  RESULTS [--priority N] [--views]`. The ones nearest the target: `python tools/margins.py
  RESULTS`. Whose stages are not at Response's control values: `python tools/stagesat.py
  VERIFY_OUT [--list]`.
- Development results: `python tools/verify.py tests/oracle --inputs FOLDERS --out OUT
  --jobs N`, then `python tools/report.py OUT`. `python tools/changes.py OLD NEW` lists the
  checks that changed side; `python tools/limits.py OUT` holds the regression limits to a
  run without solving again (`--write` adds generated limits for cases that have none);
  `python tools/recompare.py OUT_COPY` compares a run's records again under the measure
  as it is now.
- Held-out totals: `python tools/heldout.py score ARCHIVE --inputs FOLDERS --jobs N
  [--record LABEL] [--kinds]`, then `python tools/heldout.py summary`. `--kinds` also
  prints the cases outside by section type and loading path, for choosing development
  cases (owner, 2026-11-25).
- A new development case: `python tools/capture.py ARCHIVE --response-dir DIR --add NAME
  INPUT --initial=N,M,V --increment=N,M,V` (needs r2x importable). Derived inputs:
  `tools/variants.py`. What Response does with an input: `tools/probe.py`.
- Diagnosis on a development case: `tools/diagnose.py` (r2c in Response's states),
  `tools/viewlines.py`, `tools/viewmisses.py`, `tools/curves.py`, `tools/sources.py` (state
  or rule?), `tools/startfrom.py`, `tools/flowset.py`, `tools/trace.py`, `tools/tries.py`
  and `tools/rtrace.py` (Response's own tries, read from the running program).
- The binary: `tools/decompile.py` shows a routine from a Ghidra project kept outside the
  repository (needs `GHIDRA_HOME`; one call at a time). Its output is never committed.
- Results pages: `tools/dashboard.py` (the front page, "how accurate is r2c?", and
  `details.html`, from the committed JSON and `heldout/totals.json`), `tools/site.py`
  (every branch; run by CI).
- `tools/attic/`: scripts no longer in use.

## The oracle

r2x (`maczout/r2x`, branch `park`) drives Response-2000 1.9.7 under Wine. One capture:

    python -m r2x.worker INPUT OUT --stage all --response-dir RESPONSE_FOLDER [options]

Negative option values need the `=` form (`--initial=-2000,0,0`). An all-stage capture takes
25 to 75 s, and several minutes for a file with many stages. Captures run one at a time in
a Wine prefix; several prefixes run side by side (`--prefix DIR`). Response does not repeat
every case run to run: a few shear cases give another number of stages on another run, so a
capture is the reference, not Response in general.

## Routines of r2k.exe 1.9.7 already located

Addresses as the decompiler shows them. Internal units in the binary: Pa and m; fc′ stored
negative.

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
| `00417d50`, `004ac800` | stages moved up in the table of stages (330 places); a steel's material factor (the prestressing factor above a yield of 750 MPa) |
| `00417290` | a secant stiffness of the section ("error in moment calculation"); not the shear driver it was taken for |
| `004ac960` | the slopes of the compressive stress (and of the tension) that the node's stiffness `0046b940` is built from: closed forms, model by model |
| `004156b0`, `004190a0` | a test of the pass routine under control of the shear strain (an extreme fibre near its cracking strain, from the twelfth pass); a stage put back to the one before after a failed try (strains, the stored depth range, the profile, the ruptured marks) |
| `00418c19`, `00418d68`, `00418e83`, `00418eb2`, `00427aef` | places inside the pass routine and the solve where `tools/rtrace.py` reads the running program: after a pass's solve, update and error; a stage kept; a stage put in between dropped; a try failed; after a step of the solve |
