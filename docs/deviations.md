# Known deviations

Where r2c is known to differ from Response-2000 beyond the target, on the development set,
in plain language. The developer keeps this list; the most important are first, and the top
five are copied to `docs/summary.md`. An entry leaves when the deviation is gone. Sizes are
measured on the development results (`docs/verification-results.md`) unless marked.

- **Inputs that r2x solves and r2c refuses.** Files that hold several sections, which is
  how Response's own sample files come (Response opens the first), and the horizontal tie
  as a stirrup pattern. r2c stops with "out of scope". This is an interface gap, not an
  accuracy one, and it is the first thing the interface parity work has to close.
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
- **Elasto-plastic tension stiffening, with shear:** r2c keeps a stage that Response
  refuses and carries on past Response's last stage.
- **Axial tension:** r2c has one rising point fewer before the fall at cracking, and the
  diagonal crack spacing chart at cracking is compared across that fall.
- **The circular column under axial load alone, after its peak.** r2c keeps its uniform
  post-peak response. This is the owner's override (`docs/brief.md`), not a defect; its
  checks are counted outside.
- **Shear on the crack**, three places: a limit line that one program draws and the other
  does not on a flat peak; where the web of the I-girder cracks with one softening model;
  the top of the cracked zone with Tamai tension stiffening. The last two are outside in
  Response's own state too: a rule, not found.
- **Transverse bond**, three places: within the depth of the stirrups on four cases (cause
  not known); around cracking with a tension stiffening factor of 0.5 (a chart of about
  0.1 MPa); the last stage with shrinkage, where Response's own values scatter.
- **No load at all:** the longitudinal bond chart of the single stage differs.
