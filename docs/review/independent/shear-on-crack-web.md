# Independent assessment

One check: `igirder-csoft3-m2v`, `shear_on_crack`, Response's stage 27 (peak) against r2c's stage 27.

## What the evidence shows

- **The curves agree at this stage.** Peak 1123.18 against 1124.44 (+0.11 %), both at curvature 0.549, stage 27 ("The two responses").
- **The difference stays when r2c is put in Response's state.** 13.56 % there, against 13.5 % in the free run; every other view is 0.00 to 0.41 % (`diagnose.py states … --stages 27 --views`).
- **The two charts have different points.** Response draws 69 points per line, r2c 51 (`viewlines.py … --raw`). Response has depths r2c lacks (316.81, 292.45, eight between 284.33 and 272.14, 259.96, 243.72, and others in the lower web); r2c has four that Response lacks (40.61, -8.14, -24.39, -40.64).
- **Where both have a point in the web, values are close**: line 0 at 235.60 is 1.2901 against 1.2889; line 2 at the bottom is 4.2912 against 4.2909.
- **Top of the web.** Response's line 2 (the limit) is 0 down to 292.45 and 4.4677 from 284.33; its line 0 is 0 down to 281.28 and rises steeply to 0.9719 at 268.08. r2c's line 2 is already 4.4948 at 300.57, where Response has 0 at the same depth; r2c's line 0 goes straight from 0 at 300.57 to 1.0722 at 268.08.
- **Bottom of the web.** At -316.89 and -316.94 Response's line 0 is 0.0123 and 0.0214; r2c's is 0.8031 and 0.8073.

## The reason

- **measured**: it is not the solution state or the load stage control. `diagnose.py states` gives 13.56 % in Response's own state, with shear stress at 0.25 % and crack widths at 0.20 %. The cause is in how r2c forms or draws this one view.
- **measured**: the reported largest difference, 0.6029, equals r2c's line 0 read at depth 282.30 on its straight segment from (0, 300.57) to (1.0722, 268.08), where Response has 0 (my arithmetic on the `viewlines.py` points: 1.0722 × 18.27 / 32.49 = 0.6029). So the miss is at the top of the web, where Response starts the shear on crack about 20 mm lower than r2c and has closely spaced points that r2c does not.
- **measured**: at 300.57, a depth both have, the limit is 0 in Response and 4.4948 in r2c. So it is not only missing points: r2c gives a limit at a place where Response gives none.
- **inferred**: r2c decides differently from Response which depths carry a crack (or it lacks Response's finer layers there at this stage). Nothing in the file tests either.
- **read**: the rule at `00480590` (sign of the value; when the limit line is drawn) does not explain this. Both programs draw the same lines. The decompiled routine in the file is cut by 335 lines, and the part shown has no branch I can identify as this view and no 0.001 or one-fiftieth test. It neither bears out nor contradicts the description.

## What the evidence does not establish

- **Why r2c has a limit at 300.57 and Response does not.** Needed: both programs' crack state (principal tensile strain, crack width) point by point over depths 333 to 268 at stage 27.
- **Whether the layers differ or only the points drawn.** Needed: the same `viewlines.py --raw` for another view (say `shear_stress`) at stage 27.
- **The bottom of the web.** The difference there (about 0.79, 17.7 % of 4.4677) is larger than the reported 0.6029. The measure's rule is not given exactly enough to say why it is not the reported one, and nothing explains Response's near-zero values there. Needed: the measure's distance worked point by point for this check.
- **Whether Response's view is steady here.** The 0.68 % spread is of load, not of this view. Needed: Response's `shear_on_crack` at stages 26 and 28.

## Against the targets

`shear_on_crack` is in the `should` list and this is a shear case: tier **Should**. Difference 13.5 % against `views_pct` 5 %, 2.7 × target, on one check of one case. Peak and rising branch (0.11 %) are inside target. The post-peak figure (30.05 %) and the different endings are not part of this group.

## On the developer's reason

1. **Supports.** `diagnose.py states` gives 13.56 % in Response's own state against 13.5 % in the free run, so it is not the state reached. The mark "measured" is right, though the developer names `tools/sources.py` and my file holds the figure from `tools/diagnose.py`; I cannot check that they are the same measurement. Of the developer's two alternatives, the evidence leans to "a rule of this chart": every other view rebuilt from the same state is within 0.41 %, and at depth 300.57, which both programs have, the limit is 0 in Response and 4.4948 in r2c. It does not exclude the other alternative.
2. **Does not decide.** The part gives no cause; it says the cause is unknown, and "inferred (not tested)" is the right mark for that. Its supporting statements (one approach used in step A-5, the slopes rule settling the shear stress, the same miss on the parked softening cases) are history that my file does not hold, so I can neither confirm nor refute them. The shear stress being settled at this stage is consistent with the 0.25 % in the diagnostic. The evidence says more than the developer does on where the miss is: the top of the web, between depths 300 and 268, where r2c starts the limit and the shear on crack higher than Response and has fewer points; and a second, larger difference at the bottom of the web (-316.89) that the developer does not mention.

The developer's title ("where the web cracks") fits the top-of-web difference, but no diagnostic in my file shows the crack state there, and the material model named in the title is not in my file.

Verdict: supports
Suggestion: take up again - the developer's reason stops at "not the state" and names no cause, while the evidence already places the miss at two depths and one comparison of the crack state there would likely say which rule is wrong.
