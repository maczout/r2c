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
  response is r2c's earlier solve's). **Narrowed, and marked in the record** (owner,
  2026-11-27; `docs/kernel.md`, "Where Response's response ends and r2c's goes on"): the
  stage control keeps why each try failed, r2c carries on only where every one of them
  failed numerically (`shear.stop_kind`, `Shear.stop`), and ends as Response does where
  one is a state refused for a crushing web or the two cannot be told apart. The record
  then has `response-last-stage`, `response-peak-stage`, `response-ending` and a section
  `response/last-stage` (r2c goes past), or `ending` (r2c ends as Response does, and
  why); `Result.response_last`, `Result.ending`. Switches for rules that are written and off are
  listed in `docs/kernel.md` (`Shear.pass_code`, `Analysis.own_stirrup_history`,
  `Shear.stale_marks`, `Shear.sliver`; each decided at the finish: kept, off; and
  `Shear.code_by_layers`, the state code read again in increment 10, off). A node's transverse strain is solved the way the
  program solves it (`Analysis.own_transverse`, since increment 8), where the answer
  depends on where the node starts; what was kept between evaluations for speed (the
  nodes' transverse solves by node, `NodeStore`) is therefore not used with shear. It
  is in `docs/kernel.md` too, and **every development record is held to its hash**
  (`tests/oracle/records.json`, `tools/same.py`; owner, 2026-11-26).
- **The development set**: 182 fixtures in `tests/oracle`, each a capture cut to the stages
  the measure compares: 55 on Newbeam under varied loads, materials, settings and units, the
  T-beam, the column and the I-girder; 52 wider cases since increment 2
  (`tools/scope_cases.py`, group W: Response's sample files under other loads; concrete and
  steel strengths, shapes, reinforcement and loads on the four sections); and 57 since
  increment 4 (group X), of the kinds the held-out scorer reports outside target
  (`tools/heldout.py score --kinds`), 53 of them without shear; all chosen to be like
  the held-out set and never the same; and 18 with shear since increment 8 (group Y): the
  kinds outside priorities 1 and 3 with shear at increment 7's score. 30 more in `tests/oracle/parked`, not run by
  default. Results: `docs/verification-results.md` (generated). Regression limits: the
  first 54 cases' in `tests/test_oracle.py`, the others' generated into
  `tests/oracle/limits.json` (`python tools/limits.py VERIFY_OUT --write`).
- **The held-out set**: `heldout/` (the frozen manifest and the totals), built and scored by
  `tools/heldout.py`. See "The held-out rule" in `CLAUDE.md` before touching anything.
  **The second set, for the finish** (`heldout/finish-manifest.json`, 22 cases, frozen
  2026-11-25) was built the same way with `--set finish` and scored at the
  finish, and once more after the owner's change of 2026-11-27 (`heldout/finish-totals.json`, `heldout/finish-repeatability.json`).
- **Known deviations**: `docs/deviations.md`.

## Next

**Without shear r2c is signed off (owner, 2026-11-27). With shear the work is stopped
for the owner's sign-off** (`docs/summary.md`; `docs/assessment.md` has the independent
assessor's findings with the developer's answers). Both held-out sets were opened case
by case at the finish, so **neither is held out any longer**: a further increment on
accuracy needs a new held-out set first (`tools/heldout.py build` with a new recipe),
and must not tune against the cases of the two spent sets as if they were unseen.

Standing after increment 10 (both sets scored once after the change): without shear 27
of 27 and 10 of 10 on each priority. With shear, priority 1 with no case cut 22 of 28
and 11 of 12, cut 26 of 28 and 12 of 12; priorities 2 and 3 at 16 and 25 of 28, 7 and
12 of 12; priority 4 at 18 of 27 and 8 of 12 cut. The cut totals fell from the finish
because the measure cuts fewer cases (a trace of Response must show the give-up); the
records of increment 8 under today's measure give the same totals.

**What the owner's requirements of 2026-11-27 still lack** (`python tools/marks.py REFS
SUBS`; `docs/deviations.md`): the record marks the stage where r2c's *copy* of
Response's stage control gives up. On the cases where r2c goes past Response's last
stage (25 development, 15 held-out) that is Response's last stage on 5 and 5, another
stage on 9 and 5, and there is no mark on 11 and 5; and of the 6 development cases where
a trace shows Response refusing a crushing web, r2c ends on a crushing web on 2, some
stages after Response, and goes on on 4; it also ends that way on 5 cases where the
trace shows something else. On the held-out sets 2 records end that way, and on 2 of
the 3 cases with such a trace r2c goes past. Where to start:

- **Which nodes are uniaxial** (`docs/kernel.md`, "The state code, layer by layer";
  `Shear.code_by_layers`, written, off). The binary's scan for web crushing goes layer
  by layer and a crushing node that carries no shear ends the flexural zone. With
  r2c's uniaxial nodes (`Detail.lone`) counted as carrying none, Newbeam at M/V = 4 m
  and Newbeam with two-leg stirrups at 200 mm at M/V = 3 m end exactly where Response
  refuses them, and six other cases end 6 to 16 stages early. Read what `004a7b60`
  stores as a node's shear stress and the whole test at the head of `004a8b20`, and
  hold `Detail.lone` to the Stirrup Stress chart of a section with prestrained
  stirrups.
- **Where r2c's copy does not fail where Response's solve gave up**: item 1 below.

How Response ended each traced case: `python tools/traceend.py read REFS TRACE_DIRS
--list` (the development set's endings are in `tests/oracle/trace-ends.json`, which the
measure reads; a held-out set's are in its archive, `trace-ends.json`, given to the
scorer's runs by `R2C_TRACE_ENDS`). A new development case with shear whose Response
capture ends at 0.8 of its peak or more needs a trace before it can be cut:
`python tools/traceend.py make tests/oracle OUT --inputs FOLDERS --response-dir DIR
--have TRACE_DIRS`, then `read ... --write tests/oracle/trace-ends.json`.

What the opened sets show (`python tools/sources.py` on the scorer's runs, outside the
repository): of 37 view checks outside target at assessed stages with shear, 28 are
inside when r2c is put into Response's own state (the path, not a rule), 7 are not
(five of them the Transverse Average Bond chart at the peak, on the Liping sample under
axial compression, Newbeam with heavy closed stirrups, Newbeam with stirrups at 200 mm,
the column under compression at M/V = 1.5 m and Newbeam under a moment then shear; the
T-beam's steel stress at a crack with material factors, item 8 below; the I-girder's
principal tensile stress at M/V = 4 m), and 2 need the driver.

Tools of the finish: `python tools/opened.py ARCHIVE --set heldout|finish --out FILE`
(a held-out set case by case, into a file outside the repository), `python
tools/gaveup.py REFS SUBS [--traces DIR]` (each condition of the rule that tells where
Response's solve gave up, on the records), `python tools/uncut.py REFS SUBS` (the
totals with no case cut), `python tools/marks.py REFS SUBS` (whether r2c's record marks
Response's last stage where it goes past it). Rules written and off: `docs/kernel.md`,
"Rules written and off: what was decided for each".

If work on accuracy goes on, in this order:

1. **Stages that do not settle, at a limit.** Newbeam at M/V = 0.5 m left priority 1
   on the development set with the node solve: 35 tries agree with Response's to the
   digits printed; at the 36th stage Response's profile error after 16 passes is 4.39 %
   (refused: the limit is 3 %) and r2c's 2.75 % (kept). Newbeam in US units at
   M/V = 1 ft: 32 tries agree; with `Shear.stale_marks=1` the first try in the shear
   strain fails at once as Response's does, and the next step turns on the gap between
   the last two stages against the base step (0.7 % apart in Response). On Newbeam
   under shear alone every try up to the peak is Response's; at the third step of the
   try after the stage kept unsettled r2c's unbalanced force is 2.6 % off, where
   Response's depth range with stiffness moves as the top fibre cracks in flexure:
   read the range of `00440ea0` at that state. Response's logs with every step's
   stiffness are beside the increment's runs, outside the repository.
2. **What the node solve leaves out** (`docs/kernel.md`, "The transverse solve of a
   node"): the uniaxial routine for a node with next to no shear strain is applied after
   the solve, not in place of it; the transverse clamping term of the step; a hoop's
   strain factor in the stirrups' secant. After the stirrups yield the secant steps
   jump about (the T-beam at M/V = 4 m): at the second step of its failing try r2c's
   unbalanced loads are not yet Response's.
3. **Read and not written** [B `004a80e0`]: Response multiplies the stirrups' average
   stress by the wide-spacing factor; r2c applies it to the reserve at a crack only. It
   matters only where the stirrups' spacing is more than the depth.
4. **Speed with shear** (reported, not a target; no compiled routines). With the node
   solve the solves kept by node are not used and a case takes about twice what it did.
   Exact and not done: keeping a node's solve by its inputs and its start (a kept node
   is solved again when it is asked for from another start); the nodes solved ahead
   (`warm`) would need the starts the splitting will give. `python tools/r2xtimes.py
   compare RUN --list` names the cases over; `python tools/proftime.py NAME` profiles
   one. **Do not edit `src/` while a verify run is going**: `shear.py` is imported by
   each worker when its first case starts, not when the run starts.
5. **The sliver of a depth range** (`Shear.sliver`, written, off): four development
   cases leave priority 1 with it. The origin of heights in `00440ea0`'s last block is
   inferred; read it, and what the step routine does on that range.
6. **The cracking views with shear outside on the development set** are the state, not
   a rule: in Response's state r2c's views are within 1 % (`tools/sources.py`); on two
   (Newbeam with two-leg stirrups at 200 mm and the T-beam, at 2 and 4 m) r2c has no
   stage at Response's last one, through the override.
7. **Steps in width, with shear: what is left after the stirrup ratio on the thin layer**
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
8. **Steel stress at a crack on the T-beam with CSA factors at M/V = 2 m** (the peak):
   Response gives its yielded bottom bars no value, r2c their average stress
   (`docs/kernel.md`, "Which bars show a stress at a crack": the routine leaves by
   `004440d0`, so the concrete's moment is over 1.001 times the capacity moment plus
   2 N m there and not in r2c). Put r2c into Response's state (`tools/diagnose.py`) and
   print the two moments.
9. **With shear: how many steps a solve takes before it stops.** `python tools/rtrace.py
   RECORD --steps --matrix`, then `python tools/stiff.py LOG RECORD`. The 1 % in the
   coupling terms of the stiffness is found (`docs/kernel.md`, "The concrete's stiffness"); what is left on the first
   stages with both rules on is a millionth at the very first step.
10. **Which cases to work on with shear**: `python tools/noise.py score OUT --list` names
   the development cases where Response does not hold to itself; `python
   tools/byprio.py RUN_A RUN_B` the cases a change moved, by priority.
11. **Without shear**, outside priority 2 on the development set: the Cm4 sample under
   axial compression (its ending: a second event between the stage kept after the fall
   and the stage set aside, `docs/kernel.md`, "Two more of those traces in full"), and the
   Transverse Average Bond chart at the last stage of Newbeam with shrinkage under
   moment, where Response's own values scatter (`docs/deviations.md`). Not written in the rupture rule: the change
   of control variable and the half step further on (both in `Shear.run`).
12. **Still to differ without shear in where the stages are** (`python tools/stagesat.py
   VERIFY_OUT --list`): three small first steps where the section is cracked from the
   start (the I-girder under axial tension); what More Detail at its most puts in at the
   start; the column under 600 kN of tension around first cracking; the I-girder under
   500 kN of compression at its 56th stage.
13. **The rules with shear that the state does not explain** (`python tools/sources.py`):
   the stirrups' stress at a crack at nodes that have only just cracked; shear on the
   crack with Tamai tension stiffening; the Transverse Bond chart where a half layer's
   top node has next to no shear strain.
14. **Not yet checked on parity:** the two programs run end to end on the same input.
15. **Newbeam under an axial tension of 300 kN** has no state under its initial load in
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
- Speed (owner, 2026-11-26): `python tools/r2xtimes.py measure SCRATCH --response-dir DIR
  --inputs FOLDERS --jobs 6 [--stage peak]` times r2x on every development case into
  `tests/oracle/r2x-times.json` (needs r2x importable; about half an hour for every
  stage); `python tools/r2xtimes.py compare RUN [--list]` sets a verify run's times
  beside it. After a speed change: a full verify run, then `python tools/same.py RUN`
  (every record identical to `tests/oracle/records.json`); `python tools/shadow.py NAMES
  --inputs FOLDERS` does every transverse solve of a case both ways and compares the
  bits; `python tools/proftime.py NAME` profiles one case. After a change of result:
  `python tools/same.py RUN --write`, in the same commit. Time r2c with the number of
  jobs r2x was timed with (6): with 16 or more at once each case takes up to twice as
  long on this kind of machine.
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
| `004a8b20`, `0046b690`, `004a7fa0`, `004a9d90` | the transverse solve of a node as the program does it: the steps and when they stop; the node's secant stiffness (its second form); the stirrups' part; where a node made by a split starts |
