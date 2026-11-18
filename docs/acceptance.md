# Acceptance: what "agrees with Response-2000" means

**This file is Jamie's.** It sits at the top of the instruction hierarchy in CLAUDE.md: where
it speaks, it governs. Claude may propose changes; only Jamie makes them.

Status: **template, 2026-11-17.** The stance below is Jamie's own words, 2026-11-17. The
tolerances are not set yet. Until they are, `tools/report.py` reports every difference and
assesses none.

## Stance

> "I have a structural engineer's definition of agreement which includes a tolerance. It
> [is] not mathematical equivalence." (Jamie, 2026-11-17)

> "I don't mind the system making those decisions so long as the documentation is clear. I
> will specify what is important to me." (Jamie, 2026-11-17, on deciding what is done)

Claude's reading, for Jamie to confirm: r2c aims to agree with Response-2000 within the
tolerances below, not to reproduce it. Matching Response more closely than the tolerance is
not a goal in itself. Where r2c is inside tolerance by a route other than Response's, that is
acceptable, provided `docs/kernel.md` records the route.

## What matters (Jamie to complete)

These are the structural judgements that order the work. Claude decides anything not covered
here and records the decision in the session log.

1. **Which results matter.** For example: the peak load; the rising branch of the control
   curve; the state at service load; detail views at the peak; the post-peak response.
   *Not yet set.*
2. **Post-peak.** Whether the response after the peak needs to agree at all, and if so up
   to where. Response's own last stages are often unconverged. *Not yet set.*
3. **Which sections and loadings matter most**, to order the remaining test set (Quick
   Define T, I, circular, added tendons; shear variants). *Not yet set.*
4. **Errs high vs errs low.** Whether a difference on the unconservative side (r2c's peak
   above Response's) gets a tighter limit than one on the conservative side. *Not yet set.*

## Tolerances (machine-read)

`tools/report.py` reads the block below. A value left out means "not assessed". All values
are percentages, measured as `tools/compare.py` measures them:

- `peak_pct`: the difference of the largest load on the bottom control chart, relative to
  Response's. If `peak_pct_high` is given, it applies when r2c's peak is above Response's
  (unconservative) and `peak_pct` when it is below.
- `curve_pct`: the largest distance of Response's rising-branch points from r2c's curve,
  with load scaled by Response's peak and the control value by its largest value on that
  branch.
- `views_pct`: the largest difference in any detail view at the peak, relative to that
  chart's largest value. Views listed in `views_exempt` are reported but not assessed.

Cases without a shear increment are `flexure`; cases with one are `shear`.

```toml
[flexure]
# peak_pct = 
# peak_pct_high = 
# curve_pct = 

[shear]
# peak_pct = 
# peak_pct_high = 
# curve_pct = 

[views]
# views_pct = 
# views_exempt = []
```

## How this relates to the tests

The limits in `tests/test_oracle.py` are regression limits: "no worse than it was when last
compared", set just above the differences found. They protect against breaking what works.
The tolerances here say what is good enough. A case can pass its regression test and fail
acceptance, and the other way round.
