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
  `docs/kernel.md`. Switches for rules that are written and off are listed there
  (`Flexure.rupture_halving`, `Shear.own_solve`, `Shear.parabolic_error`,
  `Shear.pass_code`, `Analysis.own_stirrup_history`).
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
  **The second set, for the finish** (`heldout/finish-manifest.json`, 22 cases, frozen
  2026-11-25) is built the same way with `--set finish` and is not scored until the
  finishing steps: the scorer refuses it.
- **Known deviations**: `docs/deviations.md`.

## Next

The threshold (owner, 2026-11-25) on the held-out set, without shear / with: priority 1,
99 % / 99 %; priority 2, 95 % / 60 %; priority 3, 95 % / 85 %. Held-out now: 96 / 96,
96 / 39, 96 / 71. Increment 5 moved no total: one more such increment is the plateau of
the brief.

1. **Turn on `Flexure.rupture_halving`** (`docs/kernel.md`, "Bar rupture within a step":
   what Response does when the stage a fifth of the way to a rupture cannot be solved).
   Written after the held-out score of increment 5 and off for that reason alone. Set
   the class attribute to True, run `python tools/verify.py`, then `python
   tools/stagesat.py`. Measured on the 104 cases without shear: two checks come inside
   (the ending of Newbeam with 500 mm² of bottom steel; a view at the last stage of the
   I-girder under axial tension), none goes outside, and that Newbeam has Response's 73
   stages to the digit. Then look at the two Cm4 cases that part from Response at their
   66th stage (`python tools/stagesat.py VERIFY_OUT --first 100 --list`).
2. **If the owner says yes: turn on Response's own solve with the parabolic error**
   (`Shear.own_solve`, `Shear.parabolic_error`; `docs/kernel.md`, "The global solve with
   shear", "Measured again in increment 5"). Set both class attributes to True and run
   `python tools/verify.py`. Measured on the 60 development cases with shear: priority 2
   from 22 to 24 inside, priority 3 from 47 to 49, priority 1 the same, 2.4 times the
   time; 4 of the 15 cases under the override then end as Response does, which is why it
   waits for the owner. With it on, the passes agree with Response's to five or six
   digits where they were followed, and what is left to differ is in 3 below.
3. **With shear, with the solve on: how many steps a solve takes before it stops, and
   the 1 % in the coupling terms of the stiffness.** `python tools/rtrace.py RECORD
   --steps --matrix`, then `python tools/stiff.py LOG RECORD`, lists the tries in which a
   pass takes one step more or fewer than Response's, or a term of the stiffness is
   off. The terms that couple the shear strain with the axial load and the moment are
   1 % apart from the first uncracked stage (Newbeam at M/V = 1 m, the second pass):
   that is a state simple enough to work by hand, and it was not found. After it, the
   first place the two part on Newbeam is the stage at 0.5556 rad/km (loads 56.7793
   against 56.7789 kN after the first solve).
4. **Which cases to work on with shear**: `python tools/noise.py score OUT --list` names
   the development cases where Response does not hold to itself under a change of
   0.05 % in the concrete strength (16 for priority 2); the other 24 where r2c is outside
   priority 2 are the ones a rule or the solve can bring in. Most are I-girders and
   T-beams, the kinds the held-out scorer shows outside for priority 2 and 3.
5. **Priority 1 without shear** needs the one held-out case left (a rectangular beam
   under moment, outside on all three priorities). On the development set nothing of
   that kind is outside priority 1. Outside priority 2 was Newbeam with 500 mm² of bottom
   steel, which item 1 brings inside. Still outside there: the prestressed I-girder under
   axial tension (its shape and its ending: Response's steps halve to the strands'
   rupture and the response ends at the peak; with item 1 on, its last-stage view comes
   inside and the ending does not), and the Cm4 sample under axial compression (its
   ending). Response's own tries on both were traced with `python tools/rtrace.py`, which
   works without shear too, and are written out in `docs/kernel.md` ("Two more of
   Response's own tries without shear"): on the I-girder the fall-backs of the stage
   control with shear (the multiplier halved after a failed solve, the control variable
   changed under 0.2, the end under 0.01), which `Flexure.run` does not have; on Cm4 a
   second event between the stage kept after the fall and the stage set aside, which
   r2c's one flag for the extreme fibre's peak strain cannot show.
6. **Still to differ without shear in where the stages are** (`python tools/stagesat.py
   VERIFY_OUT --list`): three small first steps where the section is cracked from the
   start (the I-girder under axial tension); what More Detail at its most puts in at the
   start; the column under 600 kN of tension around first cracking; the I-girder under
   500 kN of compression at its 56th stage.
7. **The rules with shear that the state does not explain** (`python tools/sources.py`):
   the stirrups' stress at a crack at nodes that have only just cracked; shear on the
   crack with Tamai tension stiffening; the Transverse Bond chart where a half layer's
   top node has next to no shear strain (kept at Newbeam M/V = 0.5 m, dropped under a
   thermal gradient: the rule that tells the two apart was not found).
8. **Long shear responses are slow** (the column under 3000 kN at M/V = 2 m takes about
   ten minutes; with Response's own solve on, fifteen).
9. **Not yet checked on parity:** the two programs run end to end on the same input.
10. **Newbeam under an axial tension of 300 kN** has no state under its initial load in
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
  and `tools/rtrace.py` (Response's own tries, read from the running program; with
  `--steps --matrix` the 3 × 3 stiffness and unbalanced loads of every step of its solve).
  `tools/stiff.py LOG RECORD` sets r2c's stiffness beside that, try by try and pass by
  pass, and names the first term that differs.
- How far Response is from itself when an input changes by next to nothing:
  `python tools/noise.py capture OUT ...` then `python tools/noise.py score OUT [--list]`
  (every concrete strength raised by 0.05 %, or `--by PCT`; the development cases with
  shear, or `--flexure`). It says how much of a priority turns on states Response itself
  does not hold to.
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
