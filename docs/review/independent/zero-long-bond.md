# Independent assessment

## What the evidence shows

- One check is outside target: `long_average_bond` on `newbeam-zero`, Response's stage 1 (called the peak) against r2c's stage 0 ("The instances").
- The case has no load at all: initial loads and increments are all 0.00, and both control curves are two points at (0, -0) in both programs ("The two responses").
- Response's chart is not zero. It shows 1.803 over depths -248.7 to -223.5 and 1.557 over 229.2 to 248.7, and zero elsewhere. r2c's chart has the same depths and is zero everywhere ("The views at the compared stages"; `viewlines.py ... long_average_bond --stage 1 --raw`).
- The longitudinal reinforcement stress is zero at every point in both programs at the same stages (`viewlines.py ... long_reinforcement_stress --stage 1 --raw`).
- "r2c in Response's own state" is "not measured". The spread of Response's load nearby is 0.00 % of peak ("The instances").
- The file gives no rule of Response-2000's binary, no address and no decompiled routine.

## The reason

- **measured**: The whole difference is that Response draws a non-zero value in this view at the two bands and r2c draws zero. `viewlines.py long_average_bond`: 1.803 and 1.557 against 0 and 0; the largest difference, 1.803, equals the chart's largest value, hence 100 %.
- **measured**: The difference is not one of geometry or of stage matching on the curve. The depths of every point agree in the two charts, and the two control curves are identical (all zeros).
- **measured**: Response's non-zero value does not come with any steel stress. `viewlines.py long_reinforcement_stress`: zero everywhere in both programs. So in Response this view is non-zero in an unloaded, unstressed section.
- **inferred**: Response's view therefore plots something that does not depend on the load, most likely a property of each bar layer (the two bands have different values and different thicknesses, 25.2 and 19.5), while r2c computes a quantity that is zero when nothing is stressed. Nothing in the file tests this, and the file does not say what r2c computes.
- **read**: nothing. No rule of the binary is given, so the rule Response uses for this view is unknown from this file.

## What the evidence does not establish

- What Response's value is (a bond demand, a bond limit, or something else) and its unit. Best settled by: the binary's rule for this view, with its address and routine.
- Whether r2c's zero is specific to zero load or general. No loaded case is shown for this view. Best settled by: the same `viewlines.py` output on a loaded Newbeam case, at several stages, to see whether Response's 1.803 and 1.557 stay constant and what r2c gives.
- Whether the stage pairing matters. Response's stage 0 and r2c's stage 1 are not shown; Response may be zero at stage 0 and non-zero only at stage 1. Best settled by: `viewlines.py` at `--stage 0`.
- Whether r2c's rules give zero in Response's state: that diagnostic was not run. With all strains zero it would probably add little.
- Whether the tracer or capture affects this view: not addressed.
- The "peak" of a response with zero load everywhere is arbitrary; the check sits at a feature that has no physical meaning here. The evidence does not say whether the measure should assess such a case.

## Against the targets

- Tier: **Could** (`long_average_bond` is in the `could` list; cracking-related views, on every case).
- Size: 100.0 % of the chart's largest value against `views_pct` = 5 %, that is 20.0 × target. The absolute difference, 1.803, is far above the printed-precision floor (two units of the last digit, about 0.002), so the small-value rule does not excuse it.
- The instability rule (D54) does not apply: stage 1 is the last stage, has no two neighbours, and so stays assessed.
- Curve checks: peak difference +0.00 %; rising and post-peak are "nan" and the features lists are empty, so the file does not show whether those checks count as inside.
- One check, one case. It is a clear miss of a Could target; the cause is not established by this file.

## On the developer's reason

1. **Supported, with one detail contradicted.** The `viewlines.py` output bears out the facts: Response's stage 1 shows 1.803 and 1.557 over the two bands, its steel stress chart is zero, and r2c's bond chart is zero. But "r2c's one stage" is contradicted: the evidence gives r2c 2 stages and two control points, and the check uses r2c's stage 0. The unit "MPa" and the statement that the bands are "the two layers of bars" are not in the evidence. The mark **measured** is right for the chart values; it is a description of the difference, not a cause.
2. **Does not decide; nothing to decide.** The part makes no claim, and the evidence holds no rule of the binary and no test of why Response is non-zero here, so it agrees that the cause is unknown. The mark **inferred** is not the right one: nothing is inferred. It is an admission that the cause is not established, and should be labelled as such.

Taken together the developer's account is a correct description of the difference and gives no reason for it. The evidence supports what is claimed, apart from the stage count, on which nothing depends.

Verdict: supports
Suggestion: take up again - the cause is unknown, nothing has been read or tried, and the miss is 20 × target, so one bounded reading of Response's rule for this view is the least that would let it be accepted or closed on grounds.
