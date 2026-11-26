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
- **`define` and `--report` of r2x are not in r2c.** Both work through Response's own
  windows. The owner's decision (2026-11-24): not part of the command line that is
  compared.
- **With shear, r2c carries on where Response's solve gives up and its response ends.**
  On sections that fail in flexure with some shear (M/V of 2 to 4 m: the T-beam, the
  Marshall sample, Newbeam with stronger concrete; several of the parked I-girder cases)
  the two curves are the same up to Response's last stage; r2c then finds further states
  and reaches a peak several per cent higher. This is the owner's override (2026-11-25,
  `docs/brief.md`): r2c keeps carrying on, and such a case is compared up to Response's
  last stage (`docs/measures.md`, "The overrides").
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
  Response's own solve of a stage, which gives up where r2c's finds a state, is written
  in r2c and off; with it on r2c follows more of Response's tries and four of the cases
  under the override above end as Response's do. Whether to turn it on is put to the
  owner.
- **How a response with shear ends.** r2c's last stages and Response's differ on about two
  in five shear cases, now that a case where Response's solve gives up is compared up to
  Response's last stage. This is the lowest priority and has not been worked on.
- **How a response without shear ends when steel ruptures**, two places. On the
  prestressed I-girder under axial tension and moment Response's tries run out at the
  strands' rupture and its response ends at the peak; r2c finds the state after the
  rupture and goes on, so the shapes differ. On Newbeam with very light steel Response
  ends two stages after the rupture and r2c several stages later.
- **Where Response puts its stages without shear**, a few places where r2c does not
  follow it: three small first steps where the section is cracked from the start (the
  I-girder under axial tension); what More Detail at its most puts in at the start; the
  steps just before light steel ruptures, which Response halves. The curves agree; the
  stages are not the same ones.
- **A fall of load at cracking that sits on the edge of what the measure counts.** Under
  shear alone, and on Newbeam in US units, both programs show the fall; in one it is just
  under 2 % of the peak and in the other just over, so the shapes read as different (1.99
  and 1.97 % against 2.06 and 2.07 % on the US-units cases, measured).
- **The I-girder with shear keeps a stage that Response drops.** At one stage the cracks at
  the top close; Response fails at that try every time and r2c does not, so the shapes
  differ at that point.
- **The horizontal tie with stirrups in the same section:** r2c draws the stirrups' bond as
  if the ties were not there. Inferred, not measured; with ties alone the chart is zero in
  both programs.
- **Elasto-plastic tension stiffening, with shear:** r2c keeps a stage that Response
  refuses and carries on past Response's last stage.
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
  crack width with them, and the stress at the crack follows the crack width. At a step
  in width Response shows no shear on the crack at one node where r2c does.
- **A spike one node wide at the tip of the cracked zone** (principal tensile stress,
  cases without shear): where it falls between two nodes its height as sampled hangs on a
  tenth of a millimetre in the neutral axis. Inside target on the development set, by
  less than elsewhere.
- **No load at all:** the longitudinal bond chart of the single stage differs.
