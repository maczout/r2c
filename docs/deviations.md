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
  r2c cannot know either before solving.
- **`define` and `--report` of r2x are not in r2c.** Both work through Response's own
  windows. The owner's decision (2026-11-24): not part of the command line that is
  compared.
- **With shear, r2c carries on where Response's solve gives up and its response ends.**
  On sections that fail in flexure with some shear (M/V of 2 to 4 m: the T-beam, the
  Marshall sample, Newbeam with stronger concrete; several of the parked I-girder cases)
  the two curves are the same up to Response's last stage; r2c then finds further states
  and reaches a peak several per cent higher. This is the owner's override (2026-11-25,
  `docs/brief.md`): r2c keeps carrying on. It is not chased; its checks are outside target
  and are counted as such.
- **The Liping sample under axial compression and moment:** the principal tensile stress at
  the peak differs by more than twice the target. Not looked into.
- **With shear, where a load stage does not settle, the two programs try different
  states.** Near a flat peak Response and r2c each keep a state that the other does not
  reach, so the shear-related views there differ by up to several times the target while
  peak and rising branch agree. About eleven development cases. Put into Response's own
  state, r2c gives Response's views on most of them, so it is the path and not the rules.
- **How a response with shear ends.** r2c's last stages and Response's differ on about two
  in three shear cases. This is the lowest priority and has not been worked on.
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
- **Transverse bond**, three places: within the depth of the stirrups on four cases (cause
  not known); around cracking with a tension stiffening factor of 0.5 (a chart of about
  0.1 MPa); the last stage with shrinkage, where Response's own values scatter.
- **No load at all:** the longitudinal bond chart of the single stage differs.
