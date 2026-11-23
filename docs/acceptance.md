# Acceptance: what "agrees with Response-2000" means

**This file is the owner's.** It sits at the top of the instruction hierarchy in CLAUDE.md:
where it speaks, it governs. The developer may propose changes; only the owner makes them.

Status: **development targets, set by the owner 2026-11-21.** These hold while the scope of
the clone is being built. They will be reviewed when the focus moves from development to
testing.

## Stance

> "I have a structural engineer's definition of agreement which includes a tolerance. It
> [is] not mathematical equivalence." (owner, 2026-11-17)

> "The priority is cloning Response's behaviour in a naive way (software). I won't provide
> separate engineering assessment of results in this project." (owner, 2026-11-21)

> "My read of past runs is [the developer] is trying hard to get an unreasonably tight numeric
> match and it is distracting attention from building out the scope." (owner, 2026-11-21)

What this means for the work:

- **What exists is documented; how it calculates is the program's** (owner, 2026-11-22, D34).
  The manual (Appendix A of Bentz's thesis) decides which features are in scope. For those
  features, r2c reproduces what Response-2000 1.9.7 does, read from the binary: where the
  thesis and the binary differ, the binary is right. That includes how its solver behaves
  and how a response ends. The only exceptions are the owner's overrides below. (This
  replaces the rule of the same day that undocumented behaviour of the binary is not cloned
  and that each difference between the documents and the binary goes to the owner.)
- The aim is a really good sectional response calculator. Features beyond that are built
  outside r2c and r2x (owner, 2026-11-22).
- Agreement within the targets below is enough. Once a case is inside them, closing the gap
  further is not a goal: build out the scope instead.
- No structural assessment of results will be given. Questions of the form "is this state
  real for the section?" are answered by "follow Response".

## Phase A exit criteria (owner, 2026-11-22)

Development (phase A) is on a development set that widens step by step (owner, 2026-11-22,
D41): Newbeam varied in its loads, then one variable at a time (shape first). Cases not yet
in the set are parked. A case joins the set when it meets these criteria or its misses are
accepted by the owner as known deviations; phase A is done when, on the whole set:

- **Must:** peak, rising branch and shape inside target on every case; the detail views of
  the stress state under moment and axial load inside target.
- **Should:** the endings of responses without shear inside target; the detail views related
  to shear.
- **Could:** the detail views related to cracking.
- **Won't:** the endings of shear responses. They are recorded as known deviations in
  `docs/status.md`. For a shear case, "shape" leaves out how the response ends.

**Bounds** (owner, 2026-11-22: "in case I am wrong and we are spinning tires"). The Musts
may prove harder than they look. Each part of an increment aimed at a Must gets:

- **Two approaches, at most.** Each is grounded in a rule read from the binary (or, where
  the binary has not yet been read, the thesis). If neither brings the check inside
  target, stop that part. Don't try a third approach, and don't tune constants to fit.
- **No regression.** Peak, rising branch and shape must not go outside on any phase A case,
  and no Must view that is inside may go outside.
- **On stopping,** record what was tried and what it moved in the log. Add a decision to
  `docs/summary.md` with the options: accept the miss as a known deviation, move the view
  down a tier, or a named third approach with its grounds. Carry on with the next part.

The decisions behind these are D1 to D3 in `docs/summary.md`.

## Owner's overrides

Where Response's behaviour is not cloned although it is in scope. Only the owner adds to
this list; the developer may suggest an entry as a decision in `docs/summary.md`.

- **The circular column under axial load alone, after its peak** (C2): looks wrong in
  Response; r2c's uniform post-peak stands (D12).
- **The endings of shear responses** are a Won't for phase A (D1): not chased, recorded as
  known deviations. This is a tier, not a ruling that Response is wrong; it may be revisited
  in phase B.

## What matters (owner, 2026-11-21)

1. **Which results.** All of them: every branch of the control curves, including after the
   peak, and all detail views.
2. **Axial and moment cases** (no shear) match Response qualitatively, in the features of the
   curve's shape, and numerically within the targets below.
3. **Cases with shear** aim for the same. Matching them is accepted to be harder; minor
   deviations may be accepted, depending on how the project is progressing. A shear case
   outside target is recorded as a known deviation in `docs/status.md`, not left silent.
4. **Errs high vs low.** Treated the same. (Follows from the stance: no engineering
   assessment.)
5. **The test set.** The present 25 cases are right for proof of concept and for building the
   clone. Range and completeness are reviewed when the scope of development is complete.

## Targets (machine-read)

**±5 % on all metrics**, for current development. Where a value is small, close to the
numerical precision of the output, an absolute limit applies in place of the percentage.

`tools/report.py` reads the block below. A value left out means "not assessed". Percentages
are measured as `tools/compare.py` measures them:

- `peak_pct`: the difference of the largest load on the bottom control chart, relative to
  Response's.
- `curve_pct`: the rising branch. The largest distance between the two curves up to
  Response's peak, measured both ways (Response's points from r2c's curve and r2c's from
  Response's), load scaled by Response's peak, control value by its largest value over the
  whole curve.
- `post_peak_pct`: the same, after Response's peak. An r2c point counts as post-peak when its
  nearest point on Response's curve is at or after Response's peak, so a response that runs on
  past Response's end, or stops short of it, counts here.
- **Shape** (not a number): the curve's features in order (cracking, falls of load before
  the peak, the peak, and how the response ends: falling, standing still, or at the peak)
  must be the same. Always assessed.
- **Small values:** a difference within two units of the last digit Response prints is never
  a miss, for the curves and the views alike. The resolution is read from the data.
- `views_pct`: the largest difference in any detail view at the peak, relative to that
  chart's largest value. Views listed in `views_exempt` are reported but not assessed.

Cases without a shear increment are `flexure`; cases with one are `shear`.

```toml
[flexure]
peak_pct = 5.0
curve_pct = 5.0
post_peak_pct = 5.0

[shear]
peak_pct = 5.0
curve_pct = 5.0
post_peak_pct = 5.0

[views]
views_pct = 5.0
views_exempt = []
# owner, 2026-11-22 (D2): the tiers of the phase A exit criteria
must = ["longitudinal_strain", "longitudinal_concrete_stress", "principal_compressive_stress",
        "principal_tensile_stress", "principal_tensile_strain", "long_reinforcement_stress",
        "long_reinf_stress_at_crack", "shrinkage_thermal_strain"]
should = ["transverse_strain", "shear_strain", "shear_stress", "shear_on_crack",
          "average_angle", "stirrup_stress", "stirrup_stress_at_crack",
          "transverse_average_bond"]
could = ["crack_widths", "long_crack_spacing", "transverse_crack_spacing",
         "diagonal_spacing", "long_average_bond"]
```

**View tiers** (owner, 2026-11-22). *Must:* the views of the stress state (`must` above), on
cases without shear. *Should:* the views related to shear (`should`), and the stress-state
views on shear cases. *Could:* the views related to cracking (`could`), on every case. Each
tier is assessed against `views_pct` and counted separately. The longitudinal steel stress at
a crack and the principal tensile strain and stress are in the Must by the owner's choice.

### Not yet measured

- **Detail views away from the peak.** Today views are compared at the peak only.

## How this relates to the tests

The limits in `tests/test_oracle.py` are regression limits: "no worse than it was when last
compared", set just above the differences found. They protect against breaking what works.
The targets here say what is good enough for now. A case can pass its regression test and
miss its target, and the other way round.
