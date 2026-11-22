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

- r2c reproduces Response-2000's behaviour **as documented** (its manual and Bentz's thesis).
  Where r2c and documented Response differ, Response is right. Behaviour of the 1.9.7 binary
  that the documents do not describe, such as where its solver fails to converge, is not
  cloned; where the documents and the binary differ, the owner decides (owner, 2026-11-22).
- The aim is a really good sectional response calculator. Features beyond that are built
  outside r2c and r2x (owner, 2026-11-22).
- Agreement within the targets below is enough. Once a case is inside them, closing the gap
  further is not a goal: build out the scope instead.
- No structural assessment of results will be given. Questions of the form "is this state
  real for the section?" are answered by "follow Response".

## Phase A exit criteria (owner, 2026-11-22)

Development (phase A) is on Newbeam alone, varied in its loads; the other cases are parked
until phase B (validate and refine). Phase A is done when, on that set:

- **Must:** peak, rising branch and shape inside target on every case; the detail views of
  the stress state under moment and axial load inside target.
- **Should:** the endings of responses without shear inside target; the detail views related
  to shear.
- **Could:** the detail views related to cracking.
- **Won't:** the endings of shear responses. They are recorded as known deviations in
  `docs/status.md`. For a shear case, "shape" leaves out how the response ends.

The decisions behind these are D1 to D3 in `docs/summary.md`.

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
```

### Not yet measured

- **Detail views away from the peak.** Today views are compared at the peak only.

## How this relates to the tests

The limits in `tests/test_oracle.py` are regression limits: "no worse than it was when last
compared", set just above the differences found. They protect against breaking what works.
The targets here say what is good enough for now. A case can pass its regression test and
miss its target, and the other way round.
