# Independent assessment

## What the evidence shows

- One check is outside: `shear_on_crack` on `newbeam-tsfactor-mv`, Response's stage 36 (peak) against r2c's stage 35; 106.3 %, 21.3 × target ("The instances").
- The curve checks are inside: peak -0.12 %, rising 0.15 %, post-peak 0.32 %, same features ("The two responses").
- Response draws 3 lines, r2c 5 (`viewlines.py`: "lines 3 / 5"). r2c has a positive limit line (line 2) that Response does not have.
- Response's limit line is non-zero from depth 187.5 (-2.0742) and its shear on crack from 186.16 (-0.1472). r2c's both start at 179.8 (-2.9917 and -0.1875). Between 187.5 and 180.1 r2c is zero where Response is -1.4 to -2.07 (`viewlines.py`).
- Elsewhere the limit lines agree closely: 0.2967 against 0.3001 at depth 0; 1.8614 against 1.8627 at -248.7; 1.2836 against 1.3352 at 176.79.
- The value line's extremes: Response -0.1472 and +0.0020 (ratio 1.4 %); r2c -0.1937 and +0.0059 (ratio 3.0 %).
- In Response's own state the view differs by 0.7 % ("The instances"); started from Response's stage 35, r2c lands on stage 36 with 0 of 20 views outside (`startfrom.py`).
- The curve is flat here: spread 0.08 % of peak. The compared stages are at curvature 4.731 and shear strain 4.779 (Response), 4.740 and 4.747 (r2c) (`curves.py`).

## The reason

- **measured**: r2c's rules are not shown to be at fault. Given Response's state they give Response's chart (0.7 %, "r2c in Response's own state"; `startfrom.py`, 0 of 20 views outside, worst 3.4 %).
- **measured**: the two compared stages are in different states. The top edge of the zone that carries shear on a crack is 7.7 mm lower in r2c (179.8 against 187.5, `viewlines.py`), and the limit there is 2.99 against 2.07. The view's measure is the largest difference, so a shifted step alone gives about 100 % (2.0742 against 0 at depth 187.5).
- **measured**: r2c's stage 35 is not at Response's shear strain (4.747 against 4.779, `curves.py`), though it is "at the same place" on the curve. On a plateau (0.08 %) load does not fix the state.
- **read**: the rule at `00480590` (the other side's limit drawn when its extreme is over a fiftieth of the larger) fits both charts: 1.4 % gives one line, 3.0 % gives two. The decompiled text in the file does not bear it out: the part shown has no such test, and 335 lines are cut.
- **inferred**: the extra line follows from the state difference, not from a rule difference. Whether it adds to the 106.3 % is not shown.
- **inferred**: r2c's stage control takes a different path along the plateau (41 stages against 38), so no r2c stage matches Response's stage 36.

## What the evidence does not establish

- Why r2c's own state differs. No trace of the stage control is in the file. Best diagnostic: the `tools/tries.py` trace of both programs over stages 31 to 37.
- Whether another r2c stage (36 to 40, shear strain 4.762 to 4.784) would be inside. Best diagnostic: `viewlines.py` on each of them against Response's stage 36.
- How the measure pairs 5 lines with 3, and where 2.205 comes from; I could not reproduce it from the points. Best diagnostic: the measure's own point-by-point output.
- Whether Response's stage 36 is unstable (D54). Its load stands about 0.1 % above both neighbours; their views are not in the file. Best diagnostic: the instability test's output for this view.
- The 0.7 % and `startfrom.py` figures rest on a state read from charts; this is not independently checked.

## Against the targets

`shear_on_crack` is in the `should` list and the case has a shear increment: tier Should. One check, one case, 106.3 % against 5 % (21.3 × target). Peak, rising branch, post-peak and shape are inside. If the D54 test finds the stage unstable, the check would be unassessed; the file does not say.

## On the developer's reason

1. **Does not decide the reading; the output fits it.** The two charts fit a fiftieth rule (Response 1.4 %, one limit line; r2c 3.0 %, two). The decompiled text in my file does not show the test (335 lines cut), so "read" cannot be confirmed here; from this file the mark could only be "inferred from output". "r2c has the rule" is supported indirectly: in Response's own state the view differs by 0.7 %.
2. **Supported in part, incomplete in a way that matters.** Supported: the ratio falls on the other side of the fiftieth in r2c's state, r2c draws Response's chart in Response's state (0.7 %; `startfrom.py`, 0 of 20 views outside), and the top is flat (0.08 % of peak). Not supported: "the chart is 0.15 MPa at most" holds for the value line only; the chart's largest value is 2.0742, the limit line. "A missing line counts as 100 %" is not in my file, the figure is 106.3 %, and `tools/sources.py` is not in my file. The account leaves out a second difference that is enough by itself: the limit line both programs draw starts 7.7 mm lower in r2c (179.8 against 187.5), so it is 0 where Response's is -2.0742, about 100 % with no missing line. "Measured" is right for the supported items and wrong for the 100 % claim, which nothing in the file measures.
3. **Does not decide.** No trace of the stage control is in the file. `startfrom.py` landing from Response's stage 35 is consistent with it and no more. The mark "inferred" is right.

The developer's name for the group, and the question put to the owner ("take up the rule for drawing the line"), point at the drawing rule. The evidence points at the state: with the drawing rule made identical, the shifted step would still leave the check far outside.

Verdict: does not decide
Suggestion: named limitation - the rules give Response's chart in Response's state, so the miss comes from the difference of state on the flat peak (the shifted step as well as the extra line), which should be recorded as such and not as a line-drawing matter, with the stage-control trace still owed.
