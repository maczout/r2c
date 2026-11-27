# Known deviations

Where r2c is known to differ from Response-2000 beyond the target, on the development set,
in plain language. The developer keeps this list; the most important are first, and the top
five are copied to `docs/summary.md`. An entry leaves when the deviation is gone. Sizes are
measured on the development results (`docs/verification-results.md`) unless marked.

- **Inputs that r2x solves and r2c refuses** (`docs/parity.md`): three compression softening
  models the manual does not list, a segmental curve for reinforcing steel, long-term
  effects, draped tendons, and `units="roman"` in a file. The owner's decision (2026-11-24,
  `docs/brief.md`): refuse them; they may be revisited after the threshold. The other way
  round, four inputs on which Response gives up part-way through its solve are solved by
  r2c: on two Response puts up "No closure on shear distribution" and r2x stops at the
  message; on two r2x finds more stages on Response's control curves than in its list.
  r2c cannot know either before solving. Accepted by the owner as known differences
  (2026-11-25): parity is complete except accepted refusals.
- **r2c's record has lines that r2x's has not.** With shear, where they apply: the
  header lines `carried-on-stage`, `carried-on-peak-stage`, `carried-on` and
  `ending`, and a section `carried-on/stage`, on where r2c's own copy of Response's
  solve failed and what r2c did then (`docs/output.md`). Required by the owner
  (2026-11-27), and renamed the same day to what r2c can know: they do not say where
  Response itself stops; the parity check leaves them out of what it
  compares (`tools/parity.py`). A reader of r2x's records that looks sections up by
  name is not affected; one that takes every section for a chart is.
- **What r2x's record carries and r2c's does not** (`docs/output.md`,
  `docs/output-check.md`; `python tools/carries.py`): at the initial load Response's
  Shear Stress chart has a second line that r2c's has not (zero unless the initial load
  has a shear); under an initial shear with no shear in the increment Response keeps
  that line at later stages and r2c never writes it; and with no increment at all the
  second stage's Shear Strain and Transverse Strain charts have envelope lines in r2c
  and a single line in Response. Found at the handover by reading whole records, not
  fixtures; left as they are (no change to results in that increment).
- **`define` and `--report` of r2x are not in r2c.** Both work through Response's own
  windows. The owner's decision (2026-11-24): not part of the command line that is
  compared.
- **With shear, r2c goes past Response's last stage on some cases, and its record marks
  that stage only on some of them.** On sections that fail in flexure with some shear
  (M/V of 2 to 4 m: the T-beam, the Marshall sample, Newbeam with stronger concrete) the
  two curves are the same up to Response's last stage; r2c then finds further states and
  can reach a peak well above the one Response reports. Response's lower figure is its
  repeatable answer. What the owner decided (2026-11-25, narrowed 2026-11-27,
  `docs/brief.md`): r2c carries on only where Response's solve gives up numerically; where
  Response refuses a state whose web is crushing, or the two cannot be told apart, r2c
  ends there too and its record says why; and where r2c goes past, its record marks the
  stage. The mark is named for what r2c can know (owner, 2026-11-27, later that day):
  the stage after which its own copy of Response's solve failed and r2c carried on
  (`carried-on-stage` in the header, a section `carried-on/stage`). **Strength with
  shear past Response's last stage is not signed off.** What r2c
  does (`docs/kernel.md`, "Where Response's response ends and r2c's goes on"): its copy of
  Response's stage control keeps why each try failed, and when the tries run out it
  carries on only if every one of them failed numerically; the record then marks that
  stage. **What is still different, in three kinds** (`python tools/marks.py`):
  - r2c's copy gives up where Response's does, r2c's own solve takes over with a jump in
    load, and the record marks the stage: the override at work, as decided.
  - r2c's copy does not fail where Response's solve gave up: r2c goes on unknowing, and
    its record has no mark there, or marks a later stage where the copy did give up. The
    mark says what the copy did and is no guide to Response's last stage on these cases
    (the README's limitations say so). It is the
    difference on stages that do not settle (below), seen at the end of a response.
  - Response refuses a state whose web is crushing and r2c's state at the same curvature
    is not read as crushing, so r2c does not end there. The cause is found in part: the
    binary scans for web crushing layer by layer and a crushing node that carries no
    shear ends the flexural zone; written (`Shear.code_by_layers`) and off, because with
    r2c's uniaxial nodes it ends two cases exactly where Response does and six others
    well before (`docs/kernel.md`, "The state code, layer by layer").
  In the measure a case is now cut at Response's last stage only where a trace of
  Response shows the numerical give-up, and priority 1 with shear is reported with no
  case cut first (`docs/measures.md`, "The overrides"). The case where Response ended of
  its own accord (Newbeam under shear, then moment) is no longer cut.
- **With shear under axial compression, just after the web cracks, Response's response
  ends on a collapsed state and r2c's does not** (Newbeam with closed stirrups under
  axial compression and shear alone). Both programs hover at the cracking load for ten
  passes of the stage and then drop; Response's solve breaks down on the sixteenth pass,
  its next stage is kept far from converged at well under the peak with the stirrups past
  their rupture strain, and the response ends there. r2c finds the cracked states and
  climbs past Response's peak. It is the override's kind, but Response's last stage is
  the collapsed one, so the comparison up to Response's last stage does not apply. The
  owner's decision (2026-11-25): it stays outside and nothing is changed for it.
- **With shear, where a load stage does not settle, the two programs try different
  states.** Near a flat peak Response and r2c each keep a state that the other does not
  reach, so the shear-related views there differ by up to several times the target while
  peak and rising branch agree. About eleven development cases. Put into Response's own
  state, r2c gives Response's views on most of them, so it is the path and not the rules.
  Response does not hold to these states itself: with every concrete strength raised by
  a twentieth of a per cent, Response compared with Response is outside on the
  shear-related views of about a quarter of the development cases with shear, and with a
  two-hundredth of a per cent on about one in seven (measured, `tools/noise.py`).
  Response's own solve of a stage is on since the owner's answer of 2026-11-25, and
  since increment 8 a node's transverse strain is solved the way the program solves it;
  r2c follows more of Response's tries with each. What is left turns on a limit at a
  stage that does not settle: a profile error after sixteen passes just over the limit
  in one program and just under it in the other, so one keeps the stage and the other
  halves the step (Newbeam at a small M/V, in SI and in US units).
- **With shear r2c is slower than r2x on most cases.** Response's own solve of a stage
  splits the layers anew at every evaluation, and r2c does the same in Python. In
  increment 7 what was already solved was kept between evaluations and a case with
  shear took about a fifth of what it had. Since increment 8 a node's transverse strain
  is solved as the program solves it, and that answer depends on where the node starts,
  so the solves kept by node are not used with shear and a case takes about twice what
  it did in increment 7 (measured, `tools/times.py`). Without shear r2c is within r2x's
  time on every case when r2x reads every stage (measured, six cases at a time for both
  programs, `tools/r2xtimes.py`). The owner's decision
  (2026-11-26): speed is a reported measure, not a target; the bar is r2x reading every
  stage; no compiled routines. r2c's standing is generated into the brief
  (`docs/brief.md`, "Owner's decisions since") and shown on the results page.
- **The shear-related views, on the held-out set, stand under Response's own score
  against itself** (priority 2 with shear). It is the path above, at stages that do not
  settle. The owner's decision (2026-11-26): reported, not a target; the standing is
  generated into the brief beside Response's own score.
- **The T-beam with material factors, steel stress at a crack at the peak:** Response
  gives its yielded bottom bars no value at the crack and r2c gives their average stress.
- **The Transverse Average Bond chart near the bottom of the stirrups, at the peak with
  shear**: r2c lower than Response over a few points. The most frequent single miss on
  the held-out sets; on about half of those cases it is there in Response's own state
  too, so a rule of that chart that r2c does not have, not looked for.
- **How a response with shear ends.** r2c's last stages and Response's differ on about two
  in five shear cases, now that a case where Response's solve gives up is compared up to
  Response's last stage. This is the lowest priority and has not been worked on.
- **How a response without shear ends when steel ruptures**, two places. On the
  prestressed I-girder under axial tension and moment Response's tries run out at the
  strands' rupture and its response ends at the peak; r2c finds the state after the
  rupture and goes on, so the shapes differ; its ending is inside since the rule for a
  failed try on the way to a rupture was turned on, and Newbeam with very light steel
  now ends where Response's does.
- **Where Response puts its stages without shear**, a few places where r2c does not
  follow it: three small first steps where the section is cracked from the start (the
  I-girder under axial tension); what More Detail at its most puts in at the start.
  The curves agree; the stages are not the same ones.
- **The I-girder with shear keeps a stage that Response drops.** At one stage the cracks at
  the top close; Response fails at that try every time and r2c does not, so the shapes
  differ at that point.
- **The horizontal tie with stirrups in the same section:** r2c draws the stirrups' bond as
  if the ties were not there. Inferred, not measured; with ties alone the chart is zero in
  both programs.
- **The circular column under axial load alone, after its peak.** r2c keeps its uniform
  post-peak response. This is the owner's override (`docs/brief.md`), not a defect; its
  checks are counted outside. The same holds for any section that stays uniform under
  axial load alone: r2c does not leave the uniform state there, and Response does.
- **Shear on the crack**, three places: a limit line that one program draws and the other
  does not on a flat peak; where the web of the I-girder cracks with one softening model;
  the top of the cracked zone with Tamai tension stiffening. The last two are outside in
  Response's own state too: a rule, not found.
- **Transverse bond**, two places: around cracking with a tension stiffening factor of
  0.5 (a chart of about 0.1 MPa); the last stage with shrinkage, where Response's own
  values scatter. Within the depth of the stirrups it differs with the state on most shear
  cases outside priority 2 (the path, above), not by its rule.
- **The stirrups' stress at a crack where the web has only just cracked** (the I-girder
  and the T-beam with shear, at cracking and at the peak): at nodes a few millionths of
  strain past cracking the two programs' transverse strains differ by as much again, the
  crack width with them, and the stress at the crack follows the crack width. (The
  nodes at a step in width, where Response showed no shear on the crack and r2c did,
  are Response's since the stirrup ratio there is taken by the narrower width.)
- **A spike one node wide at the tip of the cracked zone** (principal tensile stress,
  cases without shear): where it falls between two nodes its height as sampled hangs on a
  tenth of a millimetre in the neutral axis. Inside target on the development set, by
  less than elsewhere.
- **No load at all:** the longitudinal bond chart of the single stage differs.

## A finding for r2x, not a deviation of r2c

- **At its default setting (reading the detail views of the peak stage alone) r2x fails
  on eight of the sixty development cases with shear**: it stops with "Response has more
  than the N stages on its control curves". Reading every stage (`--stage all`) it
  captures all of them, and that is how every fixture here was made. Measured twice
  with `tools/r2xtimes.py measure --stage peak`; the cases are the ones with no "peak"
  time in `tests/oracle/r2x-times.json`. Noted for r2x at the owner's instruction
  (2026-11-26); nothing changes in r2c.
