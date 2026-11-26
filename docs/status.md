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
  `docs/kernel.md`. With shear a stage is solved by Response's own solve
  (`Shear.own_solve`, with `Shear.parabolic_error`; owner, 2026-11-25), and the owner's
  "carry on" override is a step of its own (`Shear.carry_on`, `run._carries_on`;
  `docs/kernel.md`, "The global solve with shear"): `Result.carried_from` and the
  `carried_from` of a case's verify results say where it took over (0: the whole
  response is r2c's earlier solve's). Switches for rules that are written and off are
  listed in `docs/kernel.md` (`Shear.pass_code`, `Analysis.own_stirrup_history`).
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

The threshold (owner, 2026-11-25) is Response's own score against itself on the held-out
inputs, less 3 points (`heldout/repeatability.json`; the table in `docs/summary.md` has it
beside r2c's). Held-out now (increment 6): without shear
27 of 27 on priorities 1 to 3, every threshold met; with shear 26, 12, 22 of 28 against
thresholds of 93.4, 61.3, 86.3 % (27, 18 and 25 cases). **Priority 1 with shear fell by
one case in increment 6** (a rectangular beam under moment and shear, M/V under 2 m) and
is with the owner (`docs/summary.md`); item 1 below is what was seen of it on the
development set.

1. **The stage at the fall of load when the web cracks, with Response's solve on.** On
   newbeam-m50-v (rising branch 1.7 to 10.2 % since the solve went on) the first cracked
   stage does not settle and r2c keeps it at 152.7 kN, 2.35 mm/m where Response keeps
   176.3, 1.93; on newbeam-us-mv the fall comes one stage later in r2c (`python
   tools/byprio.py RUN_I5 RUN_I6`; the curves side by side from the records). Trace both
   (`python tools/rtrace.py RECORD --steps`, `python tools/trace.py RECORD --set debug=1`)
   and compare pass by pass at that stage (`tools/tries.py`).
   **Turn off r2c's own damping first** (`Shear.relax`: half the profile update in the
   second half of the passes under shear alone; r2c's own, from before Response's solve
   was on, and Response's update has none). Tried after the held-out score, so the
   kernel is as scored: `python tools/trial.py OUT --inputs FOLDERS --set Shear.relax=1
   --only` the eight development cases under shear alone, then `python tools/byprio.py
   RUN OUT`. Without it newbeam-m50-v is back inside priority 1 and 3 (rising branch
   11.0 to 0.9 %), newbeam-n300-v comes inside priority 2 and newbeam-st150-n200-v
   priority 4; none of the eight goes outside on a priority (two rising branches move
   by under 1 %, inside and outside as before). Make `relax` return 1 and run the set.
   It does not reach the held-out kind that fell (moment and shear together is not
   stepped in the shear strain): for that, add development cases of the kind (Newbeam
   variants at M/V of 0.5 to 1.5 m with a marked fall at cracking: `tools/scope_cases.py`,
   `tools/capture.py --add`) and look at the same stage on newbeam-us-mv.
2. **Speed with shear.** A case with shear takes about 3.7 times what it did
   (`python tools/times.py BEFORE AFTER`; median 86 to 318 s on the development set, the
   column under 3000 kN at M/V = 2 m 421 to 1109 s; the held-out scorer's limit is 1800 s
   a case). Profiled on Newbeam at M/V = 1 m: four fifths of the time is
   `Analysis.refine`, which Response's solve calls at every evaluation of the state
   (`Shear._general`, as the binary splits the layers anew each time), and in it the
   nodes' transverse solve. Each pass of `refine` evaluates every layer again though only
   the layers just split are looked at: evaluating those alone was the first thing tried.
   Tried on one case after the score, from a copy of the tree and not in the
   repository: 204 to 173 s on newbeam-mv, the record byte for byte the same; so most of
   the cost is the number of evaluations, not their size (27 853 calls of `eval_nodes`
   on that case, each a transverse solve of some 13 passes over every node). Fewer
   passes of the transverse solve, or a first estimate from the last evaluation, is the
   next thing to look at. The override's second run (r2c's earlier solve from the start,
   where the hand-over finds nothing) costs one earlier run more on about a third of
   the cases.
3. **Steps in width, with shear: what is left after the stirrup ratio on the thin layer**
   (`docs/kernel.md`, "The stirrups' ratio on the thin layer across a step"; found by
   setting the two programs' shear strain side by side down the flange, node by node and
   stage by stage, on igirder-m3v and tbeam-m4v: the flange agreed to a thousandth and
   the two nodes of the thin layer did not). Not checked: a step where the stirrups end;
   whether the binary takes the narrower width or the web's (the two are one on every
   development section); the routine itself was not read (look at what `004a80e0` sums
   over for a node on a layer whose top and bottom widths differ). `python
   tools/sources.py` still lists 12 Transverse Average Bond checks as "not the state":
   its reading of Response's state from the charts may be too coarse at the thin layer;
   look at that before taking them for a rule.
4. **Steel stress at a crack on the T-beam with CSA factors at M/V = 2 m** (the peak):
   Response gives its yielded bottom bars no value, r2c their average stress
   (`docs/kernel.md`, "Which bars show a stress at a crack": the routine leaves by
   `004440d0`, so the concrete's moment is over 1.001 times the capacity moment plus
   2 N m there and not in r2c). Put r2c into Response's state (`tools/diagnose.py`) and
   print the two moments.
5. **With shear: how many steps a solve takes before it stops, and the 1 % in the
   coupling terms of the stiffness.** `python tools/rtrace.py RECORD --steps --matrix`,
   then `python tools/stiff.py LOG RECORD`. The terms that couple the shear strain with
   the axial load and the moment are 1 % apart from the first uncracked stage (Newbeam
   at M/V = 1 m, the second pass); not found in increment 5.
6. **Which cases to work on with shear**: `python tools/noise.py score OUT --list` names
   the development cases where Response does not hold to itself; `python
   tools/byprio.py RUN_A RUN_B` the cases a change moved, by priority.
7. **Without shear**, outside priority 2 on the development set: the Cm4 sample under
   axial compression (its ending: a second event between the stage kept after the fall
   and the stage set aside, `docs/kernel.md`, "Two more of those traces in full"), and the
   Transverse Average Bond chart at the last stage of Newbeam with shrinkage under
   moment, where Response's own values scatter (`docs/deviations.md`). Not written in the rupture rule: the change
   of control variable and the half step further on (both in `Shear.run`).
8. **Still to differ without shear in where the stages are** (`python tools/stagesat.py
   VERIFY_OUT --list`): three small first steps where the section is cracked from the
   start (the I-girder under axial tension); what More Detail at its most puts in at the
   start; the column under 600 kN of tension around first cracking; the I-girder under
   500 kN of compression at its 56th stage.
9. **The rules with shear that the state does not explain** (`python tools/sources.py`):
   the stirrups' stress at a crack at nodes that have only just cracked; shear on the
   crack with Tamai tension stiffening; the Transverse Bond chart where a half layer's
   top node has next to no shear strain.
10. **Not yet checked on parity:** the two programs run end to end on the same input.
11. **Newbeam under an axial tension of 300 kN** has no state under its initial load in
   r2c ("no equilibrium under the initial loads"). What Response does was not looked at.

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
  as it is now. `python tools/trial.py OUT --set Class.name=VALUE --only NAMES` runs some
  cases with a switch set differently, without editing the source. `python tools/byprio.py RUN_A RUN_B [...]` lists the cases that change
  side on a priority between runs; `python tools/times.py BEFORE AFTER` r2c's run time
  per case in two runs.
- Response against itself on the held-out inputs, which the threshold is made from:
  `python tools/heldout.py repeat ARCHIVE --response-dir DIR --jobs N [--record]` (needs
  r2x importable; totals only; its captures stay in ARCHIVE/repeat and are not opened).
- Held-out totals: `python tools/heldout.py score ARCHIVE --inputs FOLDERS --jobs N
  [--record LABEL] [--kinds]`, then `python tools/heldout.py summary` (which also writes
  the measured values into the brief). `--kinds` also
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
